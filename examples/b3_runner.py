"""Executa o pipeline da B3 usando os arquivos COTAHIST presentes em data/raw/b3."""

from __future__ import annotations

from quantfinance.workflows import run_b3_pipeline


def main() -> None:
    run_b3_pipeline()


if __name__ == "__main__":
    main()
