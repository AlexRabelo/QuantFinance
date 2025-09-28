"""Interface de linha de comando para o QuantFinance."""

from __future__ import annotations

from pathlib import Path

import typer

from quantfinance.reporting import summarise_snapshot
from quantfinance.workflows import (
    download_portfolio_data,
    enrich_portfolio_data,
    generate_portfolio_snapshots,
    load_portfolio_config,
    run_b3_pipeline,
    save_portfolio_excel_combined,
    save_portfolio_parquet,
)

DEFAULT_YAHOO_CONFIG = Path("config/carteira_base.yaml")

app = typer.Typer(help="Gerenciador de rotinas QuantFinance.")


@app.callback()
def main() -> None:
    """Menu principal."""
    typer.echo("QuantFinance CLI")


@app.command()
def yahoo(config_path: Path = DEFAULT_YAHOO_CONFIG) -> None:
    """Atualiza a carteira definida em config/carteira_base.yaml via Yahoo Finance."""
    config = load_portfolio_config(config_path)
    data_map, skipped = download_portfolio_data(config)

    if not data_map:
        typer.echo("Nenhum ativo foi baixado. Verifique sua conexão e configuração.")
        raise typer.Exit(code=1)

    if skipped:
        typer.echo("Ativos pendentes: " + ", ".join(skipped))

    enriched_map = enrich_portfolio_data(data_map)
    output_dir = Path("data/processed/carteira_base")
    output_dir.mkdir(parents=True, exist_ok=True)

    save_portfolio_parquet(data_map, output_dir, suffix="raw")
    save_portfolio_parquet(enriched_map, output_dir, suffix="enriched")
    save_portfolio_excel_combined(enriched_map, output_dir / "carteira_base.xlsx")

    typer.echo("Resumo dos ativos:")
    snapshots = generate_portfolio_snapshots(data_map)
    for name, snapshot in snapshots.items():
        typer.echo(f"\n{name}:\n{summarise_snapshot(snapshot)}")


@app.command()
def b3() -> None:
    """Processa os arquivos COTAHIST em data/raw/b3 conforme carteira_b3.yaml."""
    run_b3_pipeline()
    typer.echo("Pipeline da B3 concluído. Conferir data/processed/b3.")


@app.command()
def profit() -> None:
    """Placeholder para leitura de planilhas exportadas do Profit Pro."""
    typer.echo("Integração com planilhas do Profit Pro está em desenvolvimento.")
