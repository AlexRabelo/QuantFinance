"""Gera um ranking simples de momentum usando os dados já baixados."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from quantfinance.analysis import compute_momentum_scores, MomentumConfig

PROCESSED_DIR = Path("data/processed/carteira_base")


def load_latest_raw() -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for path in PROCESSED_DIR.glob("*_raw.parquet"):
        ticker = path.stem.replace("_raw", "")
        df = pd.read_parquet(path)
        data[ticker] = df
    return data


def main() -> None:
    data_map = load_latest_raw()
    if not data_map:
        print("Nenhum parquet encontrado em data/processed/carteira_base. Execute o pipeline primeiro.")
        return

    ranking = compute_momentum_scores(data_map, MomentumConfig(windows=(21, 63, 126)))
    print("Top 10 momentum:")
    print(ranking.head(10).to_string(index=False))

    export_path = PROCESSED_DIR / "momentum_ranking.csv"
    ranking.to_csv(export_path, index=False)
    print(f"Ranking completo exportado para {export_path}")


if __name__ == "__main__":
    main()
