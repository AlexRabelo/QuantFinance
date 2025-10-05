"""Interface de linha de comando para o QuantFinance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import typer

import pandas as pd

from quantfinance.reporting import summarise_snapshot
from quantfinance.workflows import (
    download_portfolio_data,
    enrich_portfolio_data,
    load_portfolio_config,
    run_b3_pipeline,
    save_portfolio_excel_combined,
    save_portfolio_parquet,
    snapshot_from_dataframe,
    audit_yahoo_assets,
    audit_b3_tickers,
)
from quantfinance.workflows.alerts import build_alert_report
from quantfinance.setups import evaluate_setups

DEFAULT_YAHOO_CONFIG = Path("config/tickets.yaml")
YAHOO_PROCESSED_DIR = Path("data/processed/carteira_base")
B3_PROCESSED_DIR = Path("data/processed/b3")
ENRICHED_SUFFIX = "_enriched"
MACRO_SERIES = ["USD_BRL_SPOT", "USDB11", "IVVB11", "BRENT_OIL"]

app = typer.Typer(help="Gerenciador de rotinas QuantFinance.")


@app.callback()
def main() -> None:
    """Menu principal."""
    typer.echo("QuantFinance CLI")


def _normalize_tokens(values: Optional[Iterable[str]]) -> List[str]:
    if not values:
        return []
    normalized: List[str] = []
    for raw in values:
        if not raw:
            continue
        for token in raw.replace(",", " ").split():
            token_clean = token.strip()
            if token_clean:
                normalized.append(token_clean)
    return normalized


def _available_tickers(processed_dir: Path) -> Dict[str, tuple[str, Path]]:
    if not processed_dir.exists():
        return {}
    mapping: Dict[str, tuple[str, Path]] = {}
    suffix_marker = ENRICHED_SUFFIX
    for file_path in processed_dir.glob("*" + ENRICHED_SUFFIX + ".parquet"):
        stem = file_path.stem
        name = stem[: -len(ENRICHED_SUFFIX)] if stem.endswith(suffix_marker) else stem
        mapping[name.upper()] = (name, file_path)
    return mapping


def _resolve_requested(
    requested: List[str],
    available: Dict[str, tuple[str, Path]],
) -> Dict[str, tuple[str, Path]]:
    if not requested:
        return available

    resolved: Dict[str, tuple[str, Path]] = {}
    for token in requested:
        key = token.upper()
        candidates = [key]
        if key.endswith(".SA"):
            candidates.append(key[:-3])
        matched_entry: Optional[tuple[str, Path]] = None
        for candidate in candidates:
            if candidate in available:
                matched_entry = available[candidate]
                break
        if matched_entry is None:
            raise typer.BadParameter(
                f"Ticker '{token}' não encontrado nos dados processados. Disponíveis: "
                f"{', '.join(sorted(name for name, _ in available.values())) or 'nenhum'}"
            )
        name_key = matched_entry[0].upper()
        resolved[name_key] = matched_entry
    return resolved


def _compute_returns(df: pd.DataFrame) -> pd.Series:
    if "Date" not in df.columns or "Close" not in df.columns:
        return pd.Series(dtype=float)
    data = df.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date", "Close"]).sort_values("Date")
    returns = data["Close"].astype(float).pct_change()
    returns.index = data["Date"].values
    return returns.dropna()


def _compute_macro_context(asset_df: pd.DataFrame) -> Dict[str, float]:
    asset_returns = _compute_returns(asset_df)
    if asset_returns.empty:
        return {}
    context: Dict[str, float] = {}
    for macro in MACRO_SERIES:
        macro_path = YAHOO_PROCESSED_DIR / f"{macro}_raw.parquet"
        if not macro_path.exists():
            continue
        macro_df = pd.read_parquet(macro_path)
        macro_returns = _compute_returns(macro_df)
        if macro_returns.empty:
            continue
        combined = pd.concat([asset_returns, macro_returns], axis=1, join="inner").dropna()
        if combined.empty:
            continue
        window = combined.tail(60)
        if window.empty:
            continue
        corr = window.iloc[:, 0].corr(window.iloc[:, 1])
        if pd.notna(corr):
            context[macro] = float(corr)
    return context


@app.command()
def yahoo(
    config_path: Path = DEFAULT_YAHOO_CONFIG,
    max_workers: int = typer.Option(8, "--workers", help="Número máximo de downloads concorrentes."),
) -> None:
    """Atualiza a carteira definida em config/tickets.yaml via Yahoo Finance."""
    config = load_portfolio_config(config_path)
    data_map, skipped = download_portfolio_data(
        config,
        existing_dir=YAHOO_PROCESSED_DIR,
        max_workers=max_workers,
    )

    if not data_map:
        typer.echo("Nenhum ativo foi baixado. Verifique sua conexão e configuração.")
        raise typer.Exit(code=1)

    if skipped:
        typer.echo("Ativos pendentes: " + ", ".join(skipped))

    enriched_map = enrich_portfolio_data(data_map)
    output_dir = YAHOO_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    save_portfolio_parquet(data_map, output_dir, suffix="raw")
    save_portfolio_parquet(enriched_map, output_dir, suffix="enriched")
    save_portfolio_excel_combined(enriched_map, output_dir / "carteira_base.xlsx")

    typer.echo(
        "Carteira Yahoo atualizada. Utilize 'python manage.py snapshot --source yahoo' para ver os resumos."
    )


@app.command()
def b3() -> None:
    """Processa os arquivos COTAHIST em data/raw/b3 conforme tickets.yaml."""
    run_b3_pipeline(show_summary=False)
    typer.echo(
        "Pipeline da B3 concluído. Utilize 'python manage.py snapshot --source b3' para ver os resumos."
    )


@app.command()
def profit() -> None:
    """Placeholder para leitura de planilhas exportadas do Profit Pro."""
    typer.echo("Integração com planilhas do Profit Pro está em desenvolvimento.")


@app.command()
def snapshot(
    source: str = typer.Option(..., "--source", "-s", help="Fonte dos dados processados"),
    tickers: Optional[List[str]] = typer.Option(
        None,
        "--tickers",
        "-t",
        help="Lista de tickers (separados por espaço ou vírgula). Caso omita, mostra todos.",
    ),
    directory: Optional[Path] = typer.Option(
        None,
        "--dir",
        help="Diretório alternativo com os Parquets enriquecidos.",
    ),
    tickers_args: Optional[List[str]] = typer.Argument(
        None,
        help="Tickers informados diretamente após o comando (separados por espaço ou vírgula).",
    ),
) -> None:
    """Exibe o snapshot técnico de ativos previamente processados."""

    normalized_source = source.lower()
    default_dirs = {
        "yahoo": YAHOO_PROCESSED_DIR,
        "b3": B3_PROCESSED_DIR,
    }
    if normalized_source not in default_dirs:
        raise typer.BadParameter("Fonte deve ser 'yahoo' ou 'b3'.")

    base_dir = directory or default_dirs[normalized_source]
    available = _available_tickers(base_dir)
    if not available:
        typer.echo(
            f"Nenhum dado enriquecido encontrado em {base_dir}. Execute primeiro 'python manage.py {normalized_source}'."
        )
        raise typer.Exit(code=1)

    requested = _normalize_tokens(tickers)
    requested.extend(_normalize_tokens(tickers_args))
    resolved = _resolve_requested(requested, available)

    for display_name, file_path in sorted(resolved.values(), key=lambda item: item[0]):
        try:
            df = pd.read_parquet(file_path)
        except FileNotFoundError as exc:
            typer.echo(f"Arquivo não encontrado: {file_path}")
            raise typer.Exit(code=1) from exc
        macro_context = _compute_macro_context(df)
        snapshot_obj = snapshot_from_dataframe(df, macro_context=macro_context)
        typer.echo(f"\n{display_name}:")
        typer.echo(summarise_snapshot(snapshot_obj))

        setups = evaluate_setups(snapshot_obj, df)
        active_setups = [setup for setup in setups if setup.active]
        if active_setups:
            typer.echo("\nSetups sugeridos:")
            for setup in active_setups:
                typer.echo(f"  • {setup.name}: {setup.details}")
        else:
            typer.echo("\nSem setups sugeridos com as condições atuais.")


@app.command()
def audit(
    source: str = typer.Option("both", "--source", "-s", help="Fonte a auditar: yahoo, b3 ou both."),
    max_gap_yahoo: int = typer.Option(7, "--max-gap-yahoo", help="Dias de tolerância sem negociação (Yahoo)."),
    max_gap_b3: int = typer.Option(10, "--max-gap-b3", help="Dias de tolerância sem negociação (B3)."),
    config_path: Path = DEFAULT_YAHOO_CONFIG,
    export_json: Optional[Path] = typer.Option(
        None,
        "--json",
        help="Caso informado, salva o relatório de alertas em formato JSON nesse caminho.",
    ),
) -> None:
    """Valida cobertura dos dados processados e identifica séries estagnadas."""

    normalized_source = source.lower()
    allowed = {"yahoo", "b3", "both"}
    if normalized_source not in allowed:
        raise typer.BadParameter("Fonte deve ser 'yahoo', 'b3' ou 'both'.")

    def _print_summary(title: str, summary) -> None:
        typer.echo(f"\n{title}")
        if summary.missing:
            typer.echo("  - Ausentes: " + ", ".join(sorted(summary.missing)))
        if summary.gaps:
            typer.echo("  - Séries com gaps acima do limite:")
            for issue in summary.gaps:
                typer.echo(
                    f"    • {issue.ticker}: maior gap = {issue.max_gap}d, gap atual = {issue.last_gap}d (última data {issue.last_date.date()}, arquivo {issue.path})"
                )
        if summary.failures:
            typer.echo("  - Falhas de leitura:")
            for failure in summary.failures:
                typer.echo(f"    • {failure}")
        if (
            not summary.missing
            and not summary.gaps
            and not summary.failures
        ):
            typer.echo("  ✓ Nenhum problema encontrado.")

    summaries = []

    if normalized_source in {"yahoo", "both"}:
        yahoo_summary = audit_yahoo_assets(
            config_path,
            YAHOO_PROCESSED_DIR,
            max_gap_days=max_gap_yahoo,
        )
        summaries.append(("Yahoo Finance", yahoo_summary))
        _print_summary("Yahoo Finance", yahoo_summary)

    if normalized_source in {"b3", "both"}:
        b3_summary = audit_b3_tickers(
            config_path,
            B3_PROCESSED_DIR,
            max_gap_days=max_gap_b3,
        )
        summaries.append(("B3 (COTAHIST)", b3_summary))
        _print_summary("B3 (COTAHIST)", b3_summary)

    if export_json:
        report = build_alert_report(summaries)
        payload = {
            "ok": report.ok,
            "alerts": [
                {
                    "title": alert.title,
                    "message": alert.message,
                }
                for alert in report.alerts
            ],
        }
        export_json.parent.mkdir(parents=True, exist_ok=True)
        export_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        typer.echo(f"Relatório salvo em {export_json}")
