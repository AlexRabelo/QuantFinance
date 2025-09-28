"""Geração de insights textuais a partir dos dados de mercado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from quantfinance.analysis import (
    BreakoutSignal,
    DivergenceSignal,
    FibonacciLevels,
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

TAG_LABELS: Dict[str, str] = {
    "swing_curto": "swing curto",
    "swing_medio": "swing médio",
    "swing_longo": "swing longo",
    "swing_semanal": "swing semanal",
    "numero_redondo": "número redondo",
    "minimo_52s": "mínimo 52s",
    "maximo_52s": "máximo 52s",
    "minimo_historico": "mínimo histórico",
    "maximo_historico": "máximo histórico",
    "topo_rompido": "antigo topo semanal",
    "generico": "genérico",
}


@dataclass
class MarketSnapshot:
    """Snapshot consolidado com níveis, indicadores e sinais."""

    levels: PriceLevels
    fibonacci: FibonacciLevels
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

    if {"High", "Low"}.issubset(data.columns):
        level_df = data[["Close", "High", "Low"]]
    else:
        level_df = data[["Close"]]

    levels = consolidate_levels(level_df)
    fibonacci = compute_retracements(level_df)
    trend = trend_strength(data["Close"])
    breakout = breakout_signals(
        data["Close"],
        tuple(levels.supports),
        tuple(levels.resistances),
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


def _level_score(
    detail: LevelDetail,
    price: float,
    side: str,
    max_pct: float = 5.0,
) -> Optional[tuple[float, float, LevelDetail]]:
    if detail.value <= 0 or price <= 0:
        return None
    if side == "support" and detail.value >= price:
        return None
    if side == "resistance" and detail.value <= price:
        return None
    distance_pct = abs(detail.value - price) / price * 100
    if distance_pct > max_pct:
        return None
    base = detail.weight if detail.weight > 0 else 1.0
    score = base / (1 + distance_pct)
    return score, detail.value, detail


def _format_tags(tags: List[str]) -> str:
    readable = [TAG_LABELS.get(tag, tag) for tag in tags]
    return ", ".join(readable)


def _select_levels(
    details: List[LevelDetail],
    round_numbers: List[float],
    price: float,
    side: str,
    *,
    limit: int = 3,
    max_pct: float = 5.0,
    required_tag: Optional[str] = None,
    exclude_tag: Optional[str] = None,
) -> List[str]:
    candidates: List[tuple[float, float, LevelDetail]] = []
    for detail in details:
        if required_tag and required_tag not in detail.tags:
            continue
        if exclude_tag and exclude_tag in detail.tags:
            continue
        scored = _level_score(detail, price, side, max_pct=max_pct)
        if scored:
            candidates.append(scored)

    if required_tag is None:
        for value in round_numbers:
            detail = LevelDetail(value=float(value), weight=0.3, count=1, tags=["numero_redondo"])
            if exclude_tag and exclude_tag in detail.tags:
                continue
            scored = _level_score(detail, price, side, max_pct=max_pct)
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
        label = _format_tags(detail.tags)
        tag_suffix = f" ({label})" if label else ""
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

    supports_daily = _select_levels(
        snapshot.levels.support_details,
        snapshot.levels.round_numbers,
        price,
        side="support",
        exclude_tag="swing_semanal",
    )
    supports_weekly = _select_levels(
        snapshot.levels.support_details,
        snapshot.levels.round_numbers,
        price,
        side="support",
        required_tag="swing_semanal",
    )

    resistances_daily = _select_levels(
        snapshot.levels.resistance_details,
        snapshot.levels.round_numbers,
        price,
        side="resistance",
        exclude_tag="swing_semanal",
    )
    resistances_weekly = _select_levels(
        snapshot.levels.resistance_details,
        snapshot.levels.round_numbers,
        price,
        side="resistance",
        required_tag="swing_semanal",
    )

    if supports_daily:
        lines.append(f"- Suportes (diário): {supports_daily}")
    else:
        lines.append("- Suportes (diário): não identificados na janela analisada")

    if supports_weekly:
        lines.append(f"- Suportes (semanal): {supports_weekly}")
    else:
        lines.append("- Suportes (semanal): não identificados na janela analisada")

    if resistances_daily:
        lines.append(f"- Resistências (diário): {resistances_daily}")
    else:
        lines.append("- Resistências (diário): não identificadas na janela analisada")

    if resistances_weekly:
        lines.append(f"- Resistências (semanal): {resistances_weekly}")
    else:
        lines.append("- Resistências (semanal): não identificadas na janela analisada")

    fib_levels = {k: round(v, 2) for k, v in snapshot.fibonacci.levels.items()}
    lines.append(
        "- Níveis de Fibonacci: "
        f"{fib_levels} (swing: low {_format_date(snapshot.fibonacci.low_date)} ->"
        f" high {_format_date(snapshot.fibonacci.high_date)})"
    )

    recent_divs = _filter_recent_divergences(snapshot.divergences, snapshot.latest_date)
    if recent_divs:
        for div in recent_divs:
            lines.append(
                f"- Divergência {div.kind} detectada em {_format_date(div.price_index)} "
                f"(preço {div.price_level:.2f}, indicador {div.indicator_level:.2f})"
            )
    else:
        lines.append("- Sem divergências relevantes entre preço e RSI nos últimos 60 dias")

    return "\n".join(lines)
