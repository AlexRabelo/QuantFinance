"""Engine para avaliação de setups baseados nos indicadores atuais."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List

import pandas as pd

from quantfinance.analysis import TrendSnapshot
from quantfinance.reporting import MarketSnapshot


@dataclass
class SetupResult:
    name: str
    description: str
    active: bool
    details: str


def _trend_label(trend: TrendSnapshot, *, price_above_ma200: bool | None = None) -> str:
    if trend.direction == "uptrend":
        if trend.crossover == "bullish_stack" and (price_above_ma200 is None or price_above_ma200):
            return "alta forte"
        return "alta moderada"
    if trend.direction == "downtrend":
        if trend.crossover == "bearish_stack" and (price_above_ma200 is None or price_above_ma200 is False):
            return "baixa forte"
        return "baixa moderada"
    return "lateral"


def _float(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None
    value = df[column].iloc[-1]
    return float(value) if pd.notna(value) else None


def _lagged_values(df: pd.DataFrame, column: str, n: int = 2) -> List[float]:
    if column not in df.columns:
        return []
    series = df[column].dropna().astype(float)
    if series.empty:
        return []
    return series.tail(n).tolist()


def _setup_trend_following(snapshot: MarketSnapshot, df: pd.DataFrame) -> SetupResult:
    ema21 = _float(df, "EMA_21")
    volume_ratio = _float(df, "Volume_Ratio")
    price = snapshot.latest_price

    price_above_ma200 = None
    sma200 = _float(df, "SMA_200")
    if sma200 is not None:
        price_above_ma200 = price >= sma200

    daily_label = _trend_label(snapshot.trend, price_above_ma200=price_above_ma200)
    weekly_trend = snapshot.trend_multi.get("weekly")
    weekly_label = None
    if weekly_trend:
        weekly_label = _trend_label(weekly_trend, price_above_ma200=price_above_ma200)

    conditions = [
        daily_label == "alta forte",
        weekly_label in {"alta moderada", "alta forte"} if weekly_label else True,
        ema21 is not None and price >= ema21,
        volume_ratio is not None and volume_ratio >= 1.0,
    ]

    active = all(conditions)
    details = (
        "Tendência diária/semana favorável, preço acima da EMA21 e volume >= média 20d."
        if active
        else "Requer tendência forte, preço acima da EMA21 e volume em linha com a média."
    )

    return SetupResult(
        name="Trend Following",
        description="Seguir tendência em alta com pullback raso.",
        active=active,
        details=details,
    )


def _setup_rsi_rebound(snapshot: MarketSnapshot, df: pd.DataFrame) -> SetupResult:
    rsi_values = _lagged_values(df, "RSI_14", n=3)
    if len(rsi_values) < 2:
        return SetupResult(
            name="RSI Rebound",
            description="Retomada a partir de sobrevenda (RSI 30).",
            active=False,
            details="RSI insuficiente para avaliar cruzamento.",
        )
    rsi_prev, rsi_now = rsi_values[-2], rsi_values[-1]

    weekly_trend = snapshot.trend_multi.get("weekly")
    weekly_label = _trend_label(weekly_trend) if weekly_trend else "lateral"

    crossed_up = rsi_prev <= 30 and 30 < rsi_now <= 45
    conditions = [
        crossed_up,
        weekly_label in {"alta moderada", "alta forte", "lateral"},
    ]

    active = all(conditions)
    details = (
        "RSI saiu da zona de sobrevenda e semanal não está em baixa forte."
        if active
        else "Aguardando RSI cruzar 30 ou melhorar tendência semanal."
    )

    return SetupResult(
        name="RSI Rebound",
        description="Compra quando RSI reacelera acima da faixa 30.",
        active=active,
        details=details,
    )


def _ema_cross(
    snapshot: MarketSnapshot,
    df: pd.DataFrame,
    short_col: str,
    long_col: str,
) -> List[SetupResult]:
    if not {short_col, long_col}.issubset(df.columns):
        return []

    short = df[short_col].astype(float)
    long = df[long_col].astype(float)
    diff = short - long
    if diff.dropna().shape[0] < 2:
        return []

    latest_diff = diff.iloc[-1]
    prev_diff = diff.iloc[-2]
    daily_label = _trend_label(snapshot.trend)

    results: List[SetupResult] = []

    crossed_up = prev_diff <= 0 < latest_diff
    crossed_down = prev_diff >= 0 > latest_diff

    pair_name = f"EMA Cross ({short_col[-2:]} x {long_col[-2:]})"

    if crossed_up:
        active = daily_label in {"alta moderada", "alta forte"}
        details = (
            "Cruzamento de compra confirmado pela tendência diária."
            if active
            else "Cruzamento de compra, mas tendência diária não favorece."
        )
        results.append(
            SetupResult(
                name=f"{pair_name} compra",
                description=f"EMA {short_col[-2:]} cruzando acima da EMA {long_col[-2:]}.",
                active=active,
                details=details,
            )
        )

    if crossed_down:
        active = daily_label in {"baixa moderada", "baixa forte"}
        details = (
            "Cruzamento de venda alinhado à tendência diária."
            if active
            else "Cruzamento de venda, porém tendência diária não está em baixa."
        )
        results.append(
            SetupResult(
                name=f"{pair_name} venda",
                description=f"EMA {short_col[-2:]} cruzando abaixo da EMA {long_col[-2:]}.",
                active=active,
                details=details,
            )
        )

    return results


def evaluate_setups(snapshot: MarketSnapshot, df: pd.DataFrame) -> List[SetupResult]:
    setup_functions: Iterable[Callable[[MarketSnapshot, pd.DataFrame], Iterable[SetupResult]]] = (
        lambda s, data: [_setup_trend_following(s, data)],
        lambda s, data: [_setup_rsi_rebound(s, data)],
        lambda s, data: _ema_cross(s, data, "EMA_9", "EMA_21"),
        lambda s, data: _ema_cross(s, data, "EMA_21", "EMA_72"),
    )

    results: List[SetupResult] = []
    for func in setup_functions:
        try:
            evaluations = list(func(snapshot, df))
        except Exception as exc:  # pragma: no cover - proteção extra
            evaluations = [
                SetupResult(
                    name=getattr(func, "__name__", "setup"),
                    description="Erro ao avaliar setup.",
                    active=False,
                    details=str(exc),
                )
            ]
        results.extend(evaluations)
    return results
