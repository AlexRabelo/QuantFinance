"""Extensões de CLI separadas para manter o arquivo principal estável.

Adiciona comandos:
  - b3-participants: processa fluxo de investidores (B3)
  - features: exporta features a partir de Parquets enriquecidos
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import typer

from quantfinance.workflows.participants import run_participants_pipeline
from quantfinance.ml import export_features
from quantfinance.utils.diagnostics import scan_and_fix


def register(app: typer.Typer) -> None:
    @app.command()
    def b3_participants(
        raw_dir: Path = typer.Option(
            Path("data/raw/b3/participants"),
            "--raw-dir",
            help="Diretório com CSVs de fluxo por investidor (B3)",
        ),
        output_dir: Path = typer.Option(
            Path("data/processed/b3"),
            "--out",
            help="Diretório para salvar Parquet/Excel consolidados",
        ),
    ) -> None:
        """Processa fluxo de investidores (estrangeiro/institucional) da B3."""
        run_participants_pipeline(raw_dir=raw_dir, output_dir=output_dir, show_summary=True)
        typer.echo("Fluxo de investidores processado.")

    @app.command()
    def features(
        source: str = typer.Option(
            "yahoo", "--source", "-s", help="Fonte dos dados processados (yahoo|b3)"
        ),
        ticker: str = typer.Option(
            ..., "--ticker", "-t", help="Ticker/ativo já processado (usar nome do arquivo)"
        ),
        directory: Path = typer.Option(
            Path("data/processed/carteira_base"),
            "--dir",
            help="Diretório base com Parquets enriquecidos",
        ),
        output: Optional[Path] = typer.Option(
            None,
            "--out",
            help=(
                "Caminho de saída (parquet/csv). "
                "Padrão: data/processed/features/<ticker>.parquet"
            ),
        ),
        fmt: str = typer.Option("parquet", "--format", help="Formato de saída: parquet ou csv"),
    ) -> None:
        """Exporta features a partir do Parquet enriquecido do ativo."""
        normalized_source = source.lower()
        base_dir_map = {
            "yahoo": Path("data/processed/carteira_base"),
            "b3": Path("data/processed/b3"),
        }
        if normalized_source not in base_dir_map:
            raise typer.BadParameter("Fonte deve ser 'yahoo' ou 'b3'.")
        base_dir = directory or base_dir_map[normalized_source]

        enriched = base_dir / f"{ticker}_enriched.parquet"
        if not enriched.exists():
            raise typer.BadParameter(f"Arquivo não encontrado: {enriched}")

        df = pd.read_parquet(enriched)
        default_out_dir = Path("data/processed/features")
        target = output or (default_out_dir / f"{ticker}.{fmt.lower()}")
        path = export_features(df, target, format=fmt)
        typer.echo(f"Features exportadas em {path}")

    @app.command()
    def diagnostics(
        source: str = typer.Option(
            "yahoo", "--source", "-s", help="Fonte dos dados processados (yahoo|b3)"
        ),
        directory: Path = typer.Option(
            None,
            "--dir",
            help="Diretório base com Parquets (padrão por fonte)",
        ),
        fix: bool = typer.Option(
            False, "--fix", help="Aplicar correção (coalesce de OHLCV e regravação do Parquet)"
        ),
        backup: bool = typer.Option(
            True, "--backup/--no-backup", help="Criar .bak ao corrigir Parquets"
        ),
    ) -> None:
        """Diagnostica (e opcionalmente corrige) Parquets com colunas duplicadas.

        A correção faz coalesce de colunas duplicadas de OHLCV tomando o maior
        valor numérico por linha e regrava o arquivo (com .bak se habilitado).
        """
        base_dir_map = {
            "yahoo": Path("data/processed/carteira_base"),
            "b3": Path("data/processed/b3"),
        }
        normalized_source = source.lower()
        if directory is None:
            if normalized_source not in base_dir_map:
                raise typer.BadParameter("Fonte deve ser 'yahoo' ou 'b3'.")
            directory = base_dir_map[normalized_source]
        if not directory.exists():
            raise typer.BadParameter(f"Diretório não existe: {directory}")

        results = scan_and_fix(directory, patterns=("*_raw.parquet", "*_enriched.parquet"), fix=fix, backup=backup)
        issues = 0
        fixes = 0
        for p, changed, actions in results:
            if actions or changed:
                issues += 1
            if changed:
                fixes += 1
            act = ", ".join(actions) if actions else "ok"
            typer.echo(f"- {p.name}: {act}{' (corrigido)' if changed else ''}")
        typer.echo(f"Resumo: arquivos com avisos={issues}, corrigidos={fixes}, total={len(results)}")
