"""Fluxos para carregar e processar carteiras de ativos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import yaml

from quantfinance.workflows.features.indicators import enrich_dataframe
from quantfinance.utils.diagnostics import coalesce_ohlcv, has_duplicate_columns
from quantfinance.workflows.snapshot import snapshot_from_dataframe

SUPPORTED_PROVIDERS = {"yahoo"}


@dataclass
class AssetConfig:
    """Representa um ativo configurado no arquivo de carteira."""

    name: str
    provider: str
    ticker: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    interval: Optional[str] = None
    raw: Dict[str, object] = None


@dataclass
class PortfolioConfig:
    """Descrição padronizada da carteira."""

    name: str
    assets: List[AssetConfig]
    defaults: Dict[str, object]


class UnsupportedProviderError(NotImplementedError):
    """Erro disparado quando um provider ainda não foi implementado."""


def load_portfolio_config(path: str | Path) -> PortfolioConfig:
    """Lê o arquivo YAML de configuração e retorna a estrutura tipada."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de carteira não encontrado: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    portfolio_data = data.get("portfolio") or {}
    name = portfolio_data.get("name", path.stem)
    defaults = portfolio_data.get("defaults", {})

    assets: List[AssetConfig] = []
    for entry in portfolio_data.get("assets", []):
        provider = entry.get("provider", defaults.get("provider", "yahoo"))
        asset = AssetConfig(
            name=entry.get("name", entry.get("ticker")),
            provider=provider,
            ticker=entry.get("ticker"),
            start=entry.get("start", defaults.get("start")),
            end=entry.get("end", defaults.get("end")),
            interval=entry.get("interval", defaults.get("interval", "1d")),
            raw=entry,
        )
        assets.append(asset)

    return PortfolioConfig(name=name, assets=assets, defaults=defaults)


def _download_asset(
    asset: AssetConfig,
    *,
    start_override: Optional[str] = None,
) -> pd.DataFrame:
    """Baixa os dados para um ativo conforme o provider configurado."""
    if asset.provider not in SUPPORTED_PROVIDERS:
        raise UnsupportedProviderError(
            f"Provider '{asset.provider}' ainda não suportado para o ativo '{asset.name}'."
        )

    if asset.provider == "yahoo":
        if not asset.ticker:
            raise ValueError(f"Ticker ausente para o ativo '{asset.name}'.")
        start = start_override or asset.start
        # Importa de forma tardia para evitar falhas de import em ambientes mínimos de teste
        from quantfinance.data.yahoo import download_history  # type: ignore

        return download_history(
            asset.ticker,
            start=start,
            end=asset.end,
            interval=asset.interval or "1d",
            auto_adjust=True,  # usa preços ajustados (splits/dividendos) para evitar distorções
        )

    raise UnsupportedProviderError(
        f"Provider '{asset.provider}' possui entrada mas não foi totalmente implementado."
    )


def download_portfolio_data(
    config: PortfolioConfig,
    *,
    existing_dir: Optional[Path] = None,
    max_workers: int = 4,
) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    """Baixa os dados de todos os ativos suportados.

    Quando ``existing_dir`` é informado, realiza merge incremental com os
    Parquets já persistidos (ignorando datas duplicadas).

    Retorna um dicionário nome -> DataFrame e lista de ativos ignorados.
    """
    data_map: Dict[str, pd.DataFrame] = {}
    skipped: List[str] = []

    existing_dir = Path(existing_dir) if existing_dir else None

    def _load_existing(name: str) -> Optional[pd.DataFrame]:
        if not existing_dir:
            return None
        file_path = existing_dir / f"{name}_raw.parquet"
        if not file_path.exists():
            return None
        try:
            existing = pd.read_parquet(file_path)
            if "Date" in existing.columns:
                existing["Date"] = pd.to_datetime(existing["Date"], errors="coerce")
            return existing.dropna(subset=["Date"]) if "Date" in existing.columns else existing
        except Exception:
            return None

    def _merge_frames(existing: Optional[pd.DataFrame], new: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
        if existing is None or existing.empty:
            combined = new
        elif new is None or new.empty:
            combined = existing
        else:
            combined = pd.concat([existing, new], ignore_index=True)
        # Saneia colunas duplicadas (OHLCV) e flatten, se necessário
        if combined is not None:
            try:
                fixed, _ = coalesce_ohlcv(combined)
                combined = fixed
            except Exception:
                pass
        if combined is None or combined.empty:
            return combined
        if "Date" in combined.columns:
            # Evita SettingWithCopyWarning garantindo cópia própria
            combined = combined.copy()
            combined.loc[:, "Date"] = pd.to_datetime(combined["Date"], errors="coerce")
            combined = (
                combined.dropna(subset=["Date"])
                .drop_duplicates(subset=["Date"], keep="last")
                .sort_values("Date")
                .reset_index(drop=True)
            )
        return combined

    def _task(asset: AssetConfig) -> Tuple[str, pd.DataFrame]:
        existing_frame = _load_existing(asset.name)
        start_override = None
        if existing_frame is not None and not existing_frame.empty and "Date" in existing_frame.columns:
            last_date = pd.to_datetime(existing_frame["Date"].max())
            if pd.notna(last_date):
                start_override = (last_date + pd.Timedelta(days=1)).date().isoformat()

        try:
            frame = _download_asset(asset, start_override=start_override)
        except UnsupportedProviderError as exc:
            raise exc
        except ValueError:
            # Nenhum dado novo disponível; manter o existente
            frame = None
        combined = _merge_frames(existing_frame, frame)
        if combined is None or combined.empty:
            raise ValueError("Nenhum dado disponível para o ativo")
        return asset.name, combined

    with ThreadPoolExecutor(max_workers=max_workers or 1) as executor:
        future_map = {executor.submit(_task, asset): asset for asset in config.assets}
        for future in as_completed(future_map):
            asset = future_map[future]
            try:
                name, frame = future.result()
                data_map[name] = frame
            except UnsupportedProviderError:
                skipped.append(asset.name)
            except Exception as exc:  # pragma: no cover - log simples para debug manual
                skipped.append(f"{asset.name} (erro: {exc})")
    return data_map, skipped


def enrich_portfolio_data(data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Aplica o enriquecimento de indicadores em cada ativo."""
    enriched: Dict[str, pd.DataFrame] = {}
    for name, frame in data_map.items():
        enriched[name] = enrich_dataframe(frame)
    return enriched


def save_portfolio_parquet(
    data_map: Dict[str, pd.DataFrame],
    output_dir: str | Path,
    suffix: str = "",
) -> None:
    """Salva cada ativo em Parquet dentro da pasta informada."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in data_map.items():
        # Saneia possíveis duplicatas de colunas antes de salvar
        try:
            fixed, _ = coalesce_ohlcv(frame)
            frame = fixed
        except Exception:
            # fallback: remove colunas duplicadas mantendo a primeira
            try:
                frame = frame.loc[:, ~frame.columns.duplicated()]
            except Exception:
                pass
        suffix_part = f"_{suffix}" if suffix else ""
        file_path = output_dir / f"{name}{suffix_part}.parquet"
        frame.to_parquet(file_path, index=False)


def save_portfolio_excel_combined(
    data_map: Dict[str, pd.DataFrame],
    output_path: str | Path,
) -> None:
    """Salva todos os ativos em um único arquivo Excel (uma aba por ativo)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for name, frame in data_map.items():
            sheet_name = name[:31] if name else "Ativo"
            frame.to_excel(writer, sheet_name=sheet_name, index=False)


def generate_portfolio_snapshots(
    data_map: Dict[str, pd.DataFrame],
) -> Dict[str, object]:
    """Gera snapshots para cada ativo já baixado."""
    snapshots = {}
    for name, frame in data_map.items():
        snapshots[name] = snapshot_from_dataframe(frame)
    return snapshots
