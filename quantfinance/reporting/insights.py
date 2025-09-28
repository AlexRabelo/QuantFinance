"""Geração de insights textuais a partir dos dados de mercado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from quantfinance.analysis import (
    BreakoutSignal,
    DivergenceSignal,
    PriceLevels,
    TrendSnapshot,
    breakout_signals,
    consolidate_levels,
    compute_retracements,
    detect_rsi_divergences,
    trend_strength,
)
from quantfinance.indicators import bollinger_bands, ema, macd, rsi, sma


@dataclass
class MarketSnapshot:
    """Snapshot consolidado com níveis, indicadores e sinais."""

    levels: PriceLevels
    fibonacci: Dict[str, float]
    trend: TrendSnapshot
    breakout: Dict[str, BreakoutSignal | None]
    divergences: List[DivergenceSignal]
    indicators: pd.DataFrame


REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}


def _validate_input(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e ordena o DataFrame antes de calcular os indicadores."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame sem as colunas obrigatórias: {missing}")
    data = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(data["Date"]):
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date"]).sort_values("Date").set_index("Date")
    return data


def build_market_snapshot(
    df: pd.DataFrame,
    round_step: float = 5.0,
    round_width: int = 5,
) -> MarketSnapshot:
    """Calcula o snapshot analítico utilizado nos relatórios."""
    data = _validate_input(df)

    indicators = pd.DataFrame(index=data.index)
    indicators["SMA_21"] = sma(data["Close"], 21)
    indicators["EMA_21"] = ema(data["Close"], 21)
    indicators["RSI_14"] = rsi(data["Close"], 14)
    indicators = indicators.join(macd(data["Close"]))
    indicators = indicators.join(bollinger_bands(data["Close"], window=21))

    levels = consolidate_levels(
        data[["Close"]],
        column="Close",
        order=5,
        round_step=round_step,
        round_width=round_width,
    )

    fibonacci = compute_retracements(data, column="Close").levels
    trend = trend_strength(data["Close"])
    breakout = breakout_signals(
        data["Close"],
        tuple(levels.supports),
        tuple(levels.resistances),
    )
    divergences = detect_rsi_divergences(data["Close"], indicators["RSI_14"])

    return MarketSnapshot(
        levels=levels,
        fibonacci=fibonacci,
        trend=trend,
        breakout=breakout,
        divergences=divergences,
        indicators=indicators,
    )


def summarise_snapshot(snapshot: MarketSnapshot) -> str:
    """Gera um resumo textual amigável para o snapshot."""
    lines: List[str] = []
    lines.append("Resumo de Mercado")
    trend = snapshot.trend
    lines.append(f"- Tendência: {trend.direction} (curto={trend.slope_short:.4f}, médio={trend.slope_medium:.4f}, longo={trend.slope_long:.4f})")
    lines.append(f"- Empilhamento de médias: {trend.crossover}")

    breakouts = [sig for sig in snapshot.breakout.values() if sig]
    if breakouts:
        for sig in breakouts:
            lines.append(
                f"- {sig.kind.replace('_', ' ').title()} perto de {sig.reference_level:.2f} (preço {sig.price:.2f})"
            )
    else:
        lines.append("- Nenhum sinal de rompimento relevante no momento")

    lines.append(
        f"- Suportes próximos: {[round(level, 2) for level in snapshot.levels.supports[:3]]}"
    )
    lines.append(
        f"- Resistências próximas: {[round(level, 2) for level in snapshot.levels.resistances[:3]]}"
    )

    fib_levels = {k: round(v, 2) for k, v in snapshot.fibonacci.items()}
    lines.append(f"- Níveis de Fibonacci: {fib_levels}")

    if snapshot.divergences:
        for div in snapshot.divergences[-3:]:
            lines.append(
                f"- Divergência {div.kind} detectada em {div.price_index.date()} (preço {div.price_level:.2f}, indicador {div.indicator_level:.2f})"
            )
    else:
        lines.append("- Sem divergências relevantes entre preço e RSI")

    return "\n".join(lines)
