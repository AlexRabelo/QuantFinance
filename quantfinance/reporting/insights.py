"""Geração de insights textuais a partir dos dados de mercado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from quantfinance.analysis import (
    BreakoutSignal,
    DivergenceSignal,
    LevelDetail,
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
    latest_price: float
    latest_date: pd.Timestamp


REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}


def _validate_input(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame sem as colunas obrigatórias: {missing}")
    data = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(data["Date"]):
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    return data.dropna(subset=["Date"]).sort_values("Date").set_index("Date")


def build_market_snapshot(
    df: pd.DataFrame,
    round_step: float = 5.0,
    round_width: int = 5,
) -> MarketSnapshot:
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
        order=3,
        round_step=round_step,
        round_width=round_width,
    )

    fibonacci = compute_retracements(data, column="Close").levels
    trend = trend_strength(data["Close"])
    breakout = breakout_signals(
        data["Close"],
        tuple(level for level in levels.supports),
        tuple(level for level in levels.resistances),
    )
    divergences = detect_rsi_divergences(data["Close"], indicators["RSI_14"])

    latest_price = float(data["Close"].iloc[-1])
    latest_date = data.index[-1]

    return MarketSnapshot(
        levels=levels,
        fibonacci=fibonacci,
        trend=trend,
        breakout=breakout,
        divergences=divergences,
        indicators=indicators,
        latest_price=latest_price,
        latest_date=latest_date,
    )


def _format_date(date: pd.Timestamp) -> str:
    return date.strftime("%d-%b-%y")


def _describe_trend(trend: TrendSnapshot) -> List[str]:
    direction_map = {
        "uptrend": "alta",
        "downtrend": "baixa",
        "sideways": "lateral",
    }
    crossover_map = {
        "bullish_stack": "Médias alinhadas em alta (EMA 9 > 21 > 72)",
        "bearish_stack": "Médias alinhadas em baixa (EMA 9 < 21 < 72)",
        "mixed": "Médias cruzadas entre si",
    }
    direction = direction_map.get(trend.direction, trend.direction)
    crossover = crossover_map.get(trend.crossover, trend.crossover)
    return [
        f"- Direção: mercado em {direction}",
        f"  • Inclinação curta (EMA 9 ~ 2 semanas): {trend.slope_short:.4f}",
        f"  • Inclinação média (EMA 21 ~ 1 mês): {trend.slope_medium:.4f}",
        f"  • Inclinação longa (EMA 72 ~ 3 meses): {trend.slope_long:.4f}",
        f"  • Estrutura das médias: {crossover}",
    ]


def _level_score(detail: LevelDetail, price: float, side: str) -> Optional[Tuple[float, float, LevelDetail]]:
    if detail.value <= 0 or price <= 0:
        return None
    if side == "support" and detail.value >= price:
        return None
    if side == "resistance" and detail.value <= price:
        return None
    distance_pct = abs(detail.value - price) / price * 100
    base = detail.weight if detail.weight > 0 else 1.0
    if "historical" in detail.tags:
        base += 2.0
    if "rolling_52w" in detail.tags:
        base += 1.5
    if "swing" in detail.tags:
        base += 1.0
    if "round" in detail.tags:
        base += 0.3
    score = base / (1 + distance_pct)
    return score, detail.value, detail


def _select_levels(
    details: List[LevelDetail],
    round_numbers: List[float],
    price: float,
    side: str,
    limit: int = 3,
) -> List[str]:
    candidates: List[Tuple[float, float, LevelDetail]] = []
    for detail in details:
        scored = _level_score(detail, price, side)
        if scored:
            candidates.append(scored)

    # adicionar round numbers como candidatos fracos
    for value in round_numbers:
        detail = LevelDetail(value=float(value), weight=0.3, count=1, tags=["round"])
        scored = _level_score(detail, price, side)
        if scored:
            candidates.append(scored)

    candidates.sort(key=lambda item: item[0], reverse=True)

    selected: List[str] = []
    seen = set()
    for _, value, detail in candidates:
        rounded = round(value, 2)
        if rounded in seen:
            continue
        seen.add(rounded)
        tag_suffix = ""
        if detail.tags:
            tag_suffix = " (" + ", ".join(detail.tags) + ")"
        selected.append(f"{rounded}{tag_suffix}")
        if len(selected) == limit:
            break
    return selected


def _filter_recent_divergences(
    divergences: List[DivergenceSignal],
    latest_date: pd.Timestamp,
    max_days: int = 60,
) -> List[DivergenceSignal]:
    if not divergences:
        return []
    return [div for div in divergences if (latest_date - div.price_index).days <= max_days]


def summarise_snapshot(snapshot: MarketSnapshot) -> str:
    lines: List[str] = []
    lines.append("Resumo de Mercado")
    lines.append(
        f"- Preço atual: {snapshot.latest_price:.2f} em {_format_date(snapshot.latest_date)}"
    )
    lines.extend(_describe_trend(snapshot.trend))

    breakouts = [sig for sig in snapshot.breakout.values() if sig]
    if breakouts:
        for sig in breakouts:
            lines.append(
                f"- {sig.kind.replace('_', ' ').title()} perto de {sig.reference_level:.2f} (preço {sig.price:.2f})"
            )
    else:
        lines.append("- Nenhum sinal de rompimento relevante no momento")

    price = snapshot.latest_price
    supports = _select_levels(
        snapshot.levels.support_details,
        snapshot.levels.round_numbers,
        price,
        side="support",
    )
    resistances = _select_levels(
        snapshot.levels.resistance_details,
        snapshot.levels.round_numbers,
        price,
        side="resistance",
    )

    if supports:
        lines.append(f"- Suportes próximos: {supports}")
    else:
        lines.append("- Suportes próximos: não identificados na janela analisada")

    if resistances:
        lines.append(f"- Resistências próximas: {resistances}")
    else:
        lines.append("- Resistências próximas: não identificadas na janela analisada")

    fib_levels = {k: round(v, 2) for k, v in snapshot.fibonacci.items()}
    lines.append(f"- Níveis de Fibonacci: {fib_levels}")

    recent_divs = _filter_recent_divergences(snapshot.divergences, snapshot.latest_date)
    if recent_divs:
        for div in recent_divs:
            lines.append(
                f"- Divergência {div.kind} detectada em {_format_date(div.price_index)} (preço {div.price_level:.2f}, indicador {div.indicator_level:.2f})"
            )
    else:
        lines.append("- Sem divergências relevantes entre preço e RSI nos últimos 60 dias")

    return "\n".join(lines)
