"""Exemplo para baixar dados da carteira configurada."""

from __future__ import annotations

from pathlib import Path

from quantfinance.reporting import summarise_snapshot
from quantfinance.workflows import (
    download_portfolio_data,
    enrich_portfolio_data,
    generate_portfolio_snapshots,
    load_portfolio_config,
    save_portfolio_excel_combined,
    save_portfolio_parquet,
)

CONFIG_PATH = Path("config/carteira_base.yaml")
OUTPUT_DIR = Path("data/processed/carteira_base")
COMBINED_EXCEL = OUTPUT_DIR / "carteira_base.xlsx"


def main() -> None:
    config = load_portfolio_config(CONFIG_PATH)
    data_map, skipped = download_portfolio_data(config)

    if not data_map:
        print("Nenhum ativo foi baixado. Verifique sua conexão e configuração.")
        return

    print("Ativos baixados:", ", ".join(data_map.keys()))
    if skipped:
        print("Ativos pendentes:", ", ".join(skipped))

    enriched_map = enrich_portfolio_data(data_map)

    save_portfolio_parquet(data_map, OUTPUT_DIR, suffix="raw")
    save_portfolio_parquet(enriched_map, OUTPUT_DIR, suffix="enriched")
    save_portfolio_excel_combined(enriched_map, COMBINED_EXCEL)
    print(
        "Dados salvos em "
        f"{OUTPUT_DIR.resolve()} (arquivos *_raw.parquet e *_enriched.parquet)"
        f" e {COMBINED_EXCEL.resolve()} (.xlsx consolidado)"
    )

    snapshots = generate_portfolio_snapshots(data_map)
    for name, snapshot in snapshots.items():
        print(f"\nResumo para {name}:")
        print(summarise_snapshot(snapshot))


if __name__ == "__main__":
    main()
