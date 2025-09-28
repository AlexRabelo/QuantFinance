"""Utilitários de plotagem para relatórios."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quantfinance.indicators import bollinger_bands, ema, macd, rsi, sma


def plot_full_analysis(df: pd.DataFrame, output_path: str | Path = "reports/analysis.html") -> Path:
    """Gera um relatório interativo em HTML com indicadores principais."""
    data = df.copy()
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        data = data.dropna(subset=["Date"]).sort_values("Date")

    data["SMA_9"] = sma(data["Close"], 9)
    data["SMA_21"] = sma(data["Close"], 21)
    data["SMA_72"] = sma(data["Close"], 72)

    data["EMA_9"] = ema(data["Close"], 9)
    data["EMA_21"] = ema(data["Close"], 21)
    data["EMA_72"] = ema(data["Close"], 72)

    data["RSI_14"] = rsi(data["Close"], 14)
    macd_df = macd(data["Close"])
    bb_df = bollinger_bands(data["Close"], window=21)
    data = data.join(macd_df).join(bb_df)

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.4, 0.1, 0.25, 0.25],
        subplot_titles=("Preço com Médias e Bollinger", "Volume", "MACD", "RSI"),
    )

    fig.add_trace(
        go.Candlestick(
            x=data["Date"],
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Preço",
        ),
        row=1,
        col=1,
    )

    for ma in ["SMA_9", "SMA_21", "SMA_72"]:
        fig.add_trace(
            go.Scatter(x=data["Date"], y=data[ma], mode="lines", name=ma),
            row=1,
            col=1,
        )

    for ma in ["EMA_9", "EMA_21", "EMA_72"]:
        fig.add_trace(
            go.Scatter(
                x=data["Date"],
                y=data[ma],
                mode="lines",
                name=ma,
                line=dict(dash="dash"),
            ),
            row=1,
            col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=data["Date"],
            y=data["UpperBand"],
            mode="lines",
            name="BB Upper",
            line=dict(color="rgba(255,0,0,0.2)"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data["Date"],
            y=data["MiddleBand"],
            mode="lines",
            name="BB Middle",
            line=dict(color="rgba(0,0,0,0.2)"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data["Date"],
            y=data["LowerBand"],
            mode="lines",
            name="BB Lower",
            line=dict(color="rgba(0,0,255,0.2)"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(go.Bar(x=data["Date"], y=data["Volume"], name="Volume"), row=2, col=1)

    fig.add_trace(go.Scatter(x=data["Date"], y=data["MACD"], mode="lines", name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=data["Date"], y=data["Signal"], mode="lines", name="Signal"), row=3, col=1)
    fig.add_trace(go.Bar(x=data["Date"], y=data["Histogram"], name="Histogram"), row=3, col=1)

    fig.add_trace(go.Scatter(x=data["Date"], y=data["RSI_14"], mode="lines", name="RSI"), row=4, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1)

    fig.update_layout(
        height=900,
        title_text="Análise Técnica Completa",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_yaxes(title_text="Preço", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_yaxes(title_text="RSI", row=4, col=1, range=[0, 100])

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path))
    return output_path
