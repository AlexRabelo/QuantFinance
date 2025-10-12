#!/usr/bin/env python3
"""
Menu inicial simples para acionar as principais rotinas do QuantFinance.

Este script oferece um menu textual para:
- Baixar e enriquecer dados via Yahoo (conforme config/tickets.yaml)
- Processar arquivos COTAHIST da B3 e gerar saídas
- Auditar cobertura e lacunas das séries processadas
- Visualizar snapshot técnico de ativos já enriquecidos
- Exportar features para ML a partir de dados enriquecidos
- Rodar o pipeline de fluxo de investidores (B3), se disponível

Requisitos: dependências do projeto instaladas (requirements.txt).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from quantfinance.reporting import summarise_snapshot
from quantfinance.workflows.snapshot import snapshot_from_dataframe
from quantfinance.workflows.portfolio import (
    load_portfolio_config,
    download_portfolio_data,
    enrich_portfolio_data,
    save_portfolio_parquet,
    save_portfolio_excel_combined,
)
from quantfinance.workflows.audit import audit_b3_tickers, audit_yahoo_assets
from quantfinance.workflows.b3 import run_b3_pipeline
from quantfinance.ml.features import export_features


DEFAULT_YAHOO_CONFIG = Path("config/tickets.yaml")
YAHOO_PROCESSED_DIR = Path("data/processed/carteira_base")
B3_PROCESSED_DIR = Path("data/processed/b3")
FEATURES_DIR = Path("data/features")
ENRICHED_SUFFIX = "_enriched"


def _available_enriched(processed_dir: Path) -> Dict[str, Path]:
    if not processed_dir.exists():
        return {}
    mapping: Dict[str, Path] = {}
    for file_path in processed_dir.glob(f"*{ENRICHED_SUFFIX}.parquet"):
        name = file_path.stem[: -len(ENRICHED_SUFFIX)]
        mapping[name.upper()] = file_path
    return mapping


def _purge_parquet_files(base_dir: Path, patterns: Optional[list[str]] = None) -> int:
    """Remove arquivos .parquet no diretório informado.

    Por padrão, limpa apenas os arquivos gerados pelo pipeline do Yahoo
    ("*_raw.parquet" e "*_enriched.parquet"). Retorna a contagem removida.
    """
    patterns = patterns or ["*_raw.parquet", "*_enriched.parquet"]
    if not base_dir.exists():
        return 0
    removed = 0
    for pattern in patterns:
        for file_path in base_dir.glob(pattern):
            try:
                file_path.unlink()
                removed += 1
            except Exception:
                pass
    return removed


def action_yahoo_pipeline() -> None:
    try:
        config = load_portfolio_config(DEFAULT_YAHOO_CONFIG)
    except Exception as exc:
        print(f"Erro ao ler configuração {DEFAULT_YAHOO_CONFIG}: {exc}")
        return

    rebuild = input("Reconstruir do zero (rebaixar tudo com preços ajustados)? [S/n]: ").strip().lower()
    full_rebuild = (rebuild != "n")
    try:
        workers_raw = input("Paralelismo (nº de workers) [8]: ").strip()
        max_workers = int(workers_raw) if workers_raw else 8
        if max_workers <= 0:
            max_workers = 8
    except Exception:
        max_workers = 8

    print("Baixando dados do Yahoo e mesclando com os existentes (se houver)...")
    data_map, skipped = download_portfolio_data(
        config,
        existing_dir=None if full_rebuild else YAHOO_PROCESSED_DIR,
        max_workers=max_workers,
    )
    if skipped:
        print("Ignorados:")
        for item in skipped:
            print(f"  - {item}")

    if full_rebuild:
        removed = _purge_parquet_files(YAHOO_PROCESSED_DIR)
        if removed:
            print(f"Limpando diretório: {removed} arquivos .parquet removidos de {YAHOO_PROCESSED_DIR}.")

    print(f"Salvando Parquets (raw) em {YAHOO_PROCESSED_DIR}...")
    save_portfolio_parquet(data_map, YAHOO_PROCESSED_DIR, suffix="raw")

    print("Enriquecendo ativos com indicadores...")
    enriched = enrich_portfolio_data(data_map)

    print(f"Salvando Parquets (enriched) em {YAHOO_PROCESSED_DIR}...")
    save_portfolio_parquet(enriched, YAHOO_PROCESSED_DIR, suffix="enriched")

    excel_path = YAHOO_PROCESSED_DIR / "carteira_enriched.xlsx"
    print(f"Gerando Excel combinado em {excel_path}...")
    save_portfolio_excel_combined(enriched, excel_path)

    print("Concluído.")


def action_b3_pipeline() -> None:
    try:
        run_b3_pipeline(show_summary=True)
    except ImportError as exc:
        print("Pipeline B3 indisponível neste ambiente:")
        print(f"  {exc}")
    except Exception as exc:  # pragma: no cover - defensivo
        print(f"Falha ao executar pipeline B3: {exc}")


def action_audit() -> None:
    print("Auditando Yahoo Finance...")
    yahoo_summary = audit_yahoo_assets(
        DEFAULT_YAHOO_CONFIG,
        YAHOO_PROCESSED_DIR,
        max_gap_days=7,
    )
    _print_audit_summary("Yahoo Finance", yahoo_summary)

    print("\nAuditando B3 (COTAHIST)...")
    b3_summary = audit_b3_tickers(
        DEFAULT_YAHOO_CONFIG,
        B3_PROCESSED_DIR,
        max_gap_days=10,
    )
    _print_audit_summary("B3 (COTAHIST)", b3_summary)


def _print_audit_summary(title: str, summary) -> None:
    print(f"\n{title}")
    if summary.missing:
        print("  - Ausentes: " + ", ".join(sorted(summary.missing)))
    if summary.gaps:
        print("  - Séries com gaps acima do limite:")
        for issue in summary.gaps:
            print(
                f"    • {issue.ticker}: maior gap = {issue.max_gap}d, gap atual = {issue.last_gap}d (última data {issue.last_date.date()}, arquivo {issue.path})"
            )
    if summary.failures:
        print("  - Falhas de leitura:")
        for failure in summary.failures:
            print(f"    • {failure}")
    if not summary.missing and not summary.gaps and not summary.failures:
        print("  ✓ Nenhum problema encontrado.")


def action_snapshot() -> None:
    source = input("Fonte (yahoo/b3) [yahoo]: ").strip().lower() or "yahoo"
    if source not in {"yahoo", "b3"}:
        print("Fonte inválida. Use 'yahoo' ou 'b3'.")
        return
    base_dir = YAHOO_PROCESSED_DIR if source == "yahoo" else B3_PROCESSED_DIR
    available = _available_enriched(base_dir)
    if not available:
        print(f"Nenhum dado enriquecido encontrado em {base_dir}. Execute o pipeline primeiro.")
        return
    print("Ativos disponíveis:")
    print(", ".join(sorted(name for name in (n for n in (k for k in available.keys())))))
    tokens = input("Informe tickers separados por vírgula (vazio = todos): ").strip()
    requested = [t.strip().upper() for t in tokens.replace(";", ",").split(",") if t.strip()] if tokens else []

    def _want(name: str) -> bool:
        if not requested:
            return True
        key = name.upper()
        return key in requested or (key + ".SA") in requested

    for name, file_path in sorted(available.items()):
        if not _want(name):
            continue
        try:
            df = pd.read_parquet(file_path)
        except Exception as exc:
            print(f"Falha ao ler {file_path}: {exc}")
            continue
        snapshot = snapshot_from_dataframe(df)
        last_row = df.tail(1)
        try:
            last_price = float(last_row.iloc[0]["Close"]) if "Close" in last_row.columns else None
            last_date = str(last_row.iloc[0]["Date"]) if "Date" in last_row.columns else "?"
        except Exception:
            last_price, last_date = None, "?"
        print(f"\n{name} (arquivo: {file_path} | último: {last_date} Close={last_price}):")
        print(summarise_snapshot(snapshot))


def action_export_features() -> None:
    ticker = input("Ticker (como salvo no enriched, ex.: BOVA11): ").strip()
    if not ticker:
        print("Ticker não informado.")
        return
    enriched_path = YAHOO_PROCESSED_DIR / f"{ticker}_enriched.parquet"
    if not enriched_path.exists():
        print(f"Arquivo não encontrado: {enriched_path}")
        return
    out_dir = FEATURES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"{ticker}_features.parquet"
    try:
        df = pd.read_parquet(enriched_path)
        export_features(df, output, format="parquet")
    except Exception as exc:
        print(f"Falha ao exportar features: {exc}")
        return
    print(f"Features salvas em {output}")


def action_participants() -> None:
    try:
        from quantfinance.workflows.participants import run_participants_pipeline  # type: ignore
    except Exception as exc:
        print("Pipeline de participantes (B3) indisponível neste ambiente:")
        print(f"  {exc}")
        return
    try:
        run_participants_pipeline(show_summary=True)
    except Exception as exc:  # pragma: no cover - defensivo
        print(f"Falha ao processar participantes: {exc}")


def action_fix_single_ticker() -> None:
    """Força rebaixar e regravar apenas um ticker do Yahoo, limpando arquivos antigos."""
    target = input("Ticker (nome do ativo na carteira, ex.: BOVA11): ").strip()
    if not target:
        print("Ticker não informado.")
        return
    try:
        config = load_portfolio_config(DEFAULT_YAHOO_CONFIG)
    except Exception as exc:
        print(f"Erro ao ler configuração {DEFAULT_YAHOO_CONFIG}: {exc}")
        return
    assets = [a for a in config.assets if a.name.upper() == target.upper()]
    if not assets:
        print(f"Ativo '{target}' não encontrado na carteira.")
        return
    asset = assets[0]
    # Limpa arquivos antigos desse ativo
    removed = 0
    for pattern in [f"{asset.name}_*.parquet", f"{asset.name}.parquet"]:
        for p in YAHOO_PROCESSED_DIR.glob(pattern):
            try:
                p.unlink()
                removed += 1
            except Exception:
                pass
    if removed:
        print(f"Removidos {removed} arquivos antigos de {asset.name} em {YAHOO_PROCESSED_DIR}.")
    # Cria uma carteira temporária só com esse ativo
    from dataclasses import dataclass
    @dataclass
    class _TmpConfig:
        name: str
        assets: list
        defaults: dict
    tmp = _TmpConfig(name=f"single:{asset.name}", assets=[asset], defaults=config.defaults)
    try:
        data_map, skipped = download_portfolio_data(tmp, existing_dir=None, max_workers=1)
        if skipped:
            print("Ignorados:", skipped)
        save_portfolio_parquet(data_map, YAHOO_PROCESSED_DIR, suffix="raw")
        enriched = enrich_portfolio_data(data_map)
        save_portfolio_parquet(enriched, YAHOO_PROCESSED_DIR, suffix="enriched")
        file_path = YAHOO_PROCESSED_DIR / f"{asset.name}_enriched.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            print(df.tail(1)[["Date", "Close"]])
            print(f"Recriado: {file_path}")
        else:
            print("Arquivo enriched não encontrado após recriação.")
    except Exception as exc:
        print(f"Falha no re-download de {asset.name}: {exc}")


def main() -> None:
    options = {
        "1": ("Yahoo: baixar + enriquecer carteira", action_yahoo_pipeline),
        "2": ("B3: processar COTAHIST (raw + enriched)", action_b3_pipeline),
        "3": ("Auditar dados processados (Yahoo/B3)", action_audit),
        "4": ("Snapshot: visualizar resumo técnico", action_snapshot),
        "5": ("Exportar features para ML (Yahoo)", action_export_features),
        "6": ("B3: fluxo de investidores (participantes)", action_participants),
        "7": ("Yahoo: forçar rebaixar um único ticker", action_fix_single_ticker),
        "0": ("Sair", None),
    }

    while True:
        print("\n=== QuantFinance - Menu Inicial ===")
        for key in sorted(options.keys(), key=lambda k: int(k) if k.isdigit() else 99):
            label, _ = options[key]
            print(f" {key}) {label}")
        choice = input("Escolha uma opção: ").strip()
        if choice == "0":
            print("Até logo!")
            break
        _, handler = options.get(choice, (None, None))
        if handler is None:
            print("Opção inválida. Tente novamente.")
            continue
        handler()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
        sys.exit(1)
