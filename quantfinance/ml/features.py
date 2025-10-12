"""Engenharia de features a partir de dados enriquecidos.

Requer um DataFrame com colunas padrão (Date, Open, High, Low, Close, Volume)
e colunas de indicadores geradas pelo workflow de enriquecimento
(`quantfinance.workflows.features.indicators.enrich_dataframe`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


def _weekly_rsi(df: pd.DataFrame) -> pd.Series:
    """RSI semanal aproximado a partir do RSI diário com fechamento semanal."""
    if "RSI_14" not in df.columns:
        return pd.Series(index=df.index, dtype=float)
    weekly = df.set_index("Date")["RSI_14"].resample("W").last()
    return weekly.reindex(df["Date"]).ffill().astype(float)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cria um conjunto de features a partir de um DataFrame enriquecido.

    Features iniciais:
      - distancia_preco_MM200 (% diferença Close vs SMA_200)
      - largura_banda_bollinger (BB Upper 2.0 - Lower 2.0 normalizada por Close)
      - IFR_semanal (RSI semanal via fechamento semanal)
      - retornos de 1, 5, 21 dias (Close)
    """
    data = df.copy()
    if "Date" not in data.columns:
        raise ValueError("DataFrame precisa conter coluna 'Date'.")
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    close = data["Close"].astype(float)

    # Distância do preço para SMA200
    sma200 = data.get("SMA_200")
    if sma200 is not None:
        with np.errstate(divide="ignore", invalid="ignore"):
            data["distancia_preco_MM200"] = np.where(sma200 != 0, (close / sma200 - 1.0) * 100.0, np.nan)
    else:
        data["distancia_preco_MM200"] = np.nan

    # Largura da banda de Bollinger 2.0
    upper = data.get("BB_Upper_2_0")
    lower = data.get("BB_Lower_2_0")
    if upper is not None and lower is not None:
        width = (upper - lower).astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            data["largura_banda_bollinger"] = np.where(close != 0, width / close, np.nan)
    else:
        data["largura_banda_bollinger"] = np.nan

    # RSI semanal (aproximação pelo último RSI diário da semana)
    data["IFR_semanal"] = _weekly_rsi(data)

    # Retornos
    data["ret_1"] = close.pct_change(1)
    data["ret_5"] = close.pct_change(5)
    data["ret_21"] = close.pct_change(21)

    # Seleção de colunas de saída
    feature_cols = [
        "Date",
        "Close",
        "distancia_preco_MM200",
        "largura_banda_bollinger",
        "IFR_semanal",
        "ret_1",
        "ret_5",
        "ret_21",
    ]

    # Mantém apenas as que existem
    feature_cols = [c for c in feature_cols if c in data.columns]
    return data[feature_cols].dropna(subset=["Date"]).reset_index(drop=True)


def export_features(
    df: pd.DataFrame,
    output_path: str | Path,
    *,
    format: str = "parquet",
) -> Path:
    """Gera features e salva em Parquet/CSV."""
    features = build_features(df)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fmt = format.lower()
    if fmt == "parquet":
        features.to_parquet(output, index=False)
    elif fmt == "csv":
        features.to_csv(output, index=False)
    else:
        raise ValueError("format deve ser 'parquet' ou 'csv'")
    return output

