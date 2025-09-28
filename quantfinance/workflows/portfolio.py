"""Fluxos para carregar e processar carteiras de ativos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
import yaml

from quantfinance.data.yahoo import download_history
from quantfinance.workflows.features.indicators import enrich_dataframe
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


def _download_asset(asset: AssetConfig) -> pd.DataFrame:
    """Baixa os dados para um ativo conforme o provider configurado."""
    if asset.provider not in SUPPORTED_PROVIDERS:
        raise UnsupportedProviderError(
            f"Provider '{asset.provider}' ainda não suportado para o ativo '{asset.name}'."
        )

    if asset.provider == "yahoo":
        if not asset.ticker:
            raise ValueError(f"Ticker ausente para o ativo '{asset.name}'.")
        return download_history(
            asset.ticker,
            start=asset.start,
            end=asset.end,
            interval=asset.interval or "1d",
        )

    raise UnsupportedProviderError(
        f"Provider '{asset.provider}' possui entrada mas não foi totalmente implementado."
    )


def download_portfolio_data(config: PortfolioConfig) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    """Baixa os dados de todos os ativos suportados.

    Retorna um dicionário nome -> DataFrame e lista de ativos ignorados.
    """
    data_map: Dict[str, pd.DataFrame] = {}
    skipped: List[str] = []
    for asset in config.assets:
        try:
            frame = _download_asset(asset)
            data_map[asset.name] = frame
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
