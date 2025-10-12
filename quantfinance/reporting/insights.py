"""Geração de insights textuais a partir dos dados de mercado."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
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
    detect_obv_divergences,
    detect_macd_histogram_divergences,
    trend_strength,
    trend_by_timeframe,
)
from quantfinance.indicators import (
    average_true_range,
    bollinger_bands,
    ema,
    macd,
    on_balance_volume,
    rsi,
    sma,
)

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

DIVERGENCE_KIND_LABELS: Dict[str, str] = {
    "bullish": "alta (bullish)",
    "bearish": "baixa (bearish)",
}

INDICATOR_LABELS: Dict[str, str] = {
    "RSI": "RSI (Relative Strength Index)",
    "OBV": "OBV (On-Balance Volume)",
    "MACD": "MACD (Moving Average Convergence Divergence)",
}

BREAKOUT_LABELS: Dict[str, str] = {
    "breakout_up": "Rompimento de alta (breakout up)",
    "false_breakout_up": "Falso rompimento de alta (false breakout up)",
    "breakout_down": "Rompimento de baixa (breakout down)",
    "false_breakout_down": "Falso rompimento de baixa (false breakout down)",
}

MACRO_LABELS: Dict[str, str] = {
    "USD_BRL_SPOT": "Dólar à vista (USD/BRL)",
    "USDB11": "Fundo cambial USDB11",
    "IVVB11": "ETF S&P 500 (IVVB11)",
    "BRENT_OIL": "Brent (BZ=F)",
}


@dataclass
class MarketSnapshot:
    """Snapshot consolidado com níveis, indicadores e sinais."""

    levels: PriceLevels
    fibonacci: FibonacciLevels
    trend: TrendSnapshot
    trend_multi: Dict[str, TrendSnapshot]
    breakout: Dict[str, BreakoutSignal | None]
    divergences: List[DivergenceSignal]
    indicators: pd.DataFrame
    latest_price: float
    latest_date: pd.Timestamp
    macro_context: Dict[str, float] = field(default_factory=dict)


REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}


def _validate_input(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame sem as colunas obrigatórias: {missing}")
    data = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(data["Date"]):
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    return data.dropna(subset=["Date"]).sort_values("Date").set_index("Date")


def _ensure_series(df: pd.DataFrame, name: str) -> pd.Series:
    """Garante que uma coluna possivelmente duplicada vire uma única Série numérica.

    Em alguns cenários (ex.: DataFrames vindos de fontes que geram MultiIndex
    ou salvam colunas repetidas), ``df[name]`` pode retornar um DataFrame.
    Este helper reduz para a primeira coluna e converte para numérico.
    """
    col = df[name]
    if isinstance(col, pd.DataFrame):
        # Converte todas as colunas para numérico e toma o maior valor por linha
        # para evitar escolher séries subescaladas quando houver duplicatas.
        numeric = col.apply(pd.to_numeric, errors="coerce")
        return numeric.max(axis=1)
    return pd.to_numeric(col, errors="coerce")


def build_market_snapshot(
    df: pd.DataFrame,
    round_step: float = 5.0,
    round_width: int = 5,
) -> MarketSnapshot:
    data = _validate_input(df)

    # Normaliza colunas de preço/volume para garantir Series únicas
    close = _ensure_series(data, "Close")
    high = _ensure_series(data, "High") if "High" in data.columns else close
    low = _ensure_series(data, "Low") if "Low" in data.columns else close

    indicators = pd.DataFrame(index=data.index)
    indicators["SMA_9"] = sma(close, 9)
    indicators["SMA_21"] = sma(close, 21)
    indicators["SMA_72"] = sma(close, 72)
    indicators["SMA_200"] = sma(close, 200)
    indicators["EMA_9"] = ema(close, 9)
    indicators["EMA_21"] = ema(close, 21)
    indicators["EMA_72"] = ema(close, 72)
    indicators["EMA_200"] = ema(close, 200)
    indicators["RSI_14"] = rsi(close, 14)
    macd_df = macd(close)
    indicators = indicators.join(macd_df)
    indicators = indicators.join(bollinger_bands(close, window=21))
    if "Volume" in data.columns:
        vol_series = data["Volume"]
        if isinstance(vol_series, pd.DataFrame):
            vol_series = vol_series.iloc[:, 0]
        indicators["Volume"] = pd.to_numeric(vol_series, errors="coerce").astype(float)
        vol_ma20 = indicators["Volume"].rolling(window=20, min_periods=1).mean()
        indicators["Volume_MA20"] = vol_ma20
        volume_ratio = indicators["Volume"] / vol_ma20
        volume_ratio = volume_ratio.replace([np.inf, -np.inf], np.nan)
        indicators["Volume_Ratio"] = volume_ratio
        indicators["OBV"] = on_balance_volume(data["Close"], data["Volume"].astype(float))
    if {"High", "Low", "Close"}.issubset(data.columns):
        atr = average_true_range(data["High"], data["Low"], data["Close"], window=14)
        indicators["ATR_14"] = atr
        atr_pct = (atr / data["Close"]) * 100.0
        atr_pct = atr_pct.replace([np.inf, -np.inf], np.nan)
        indicators["ATR_Pct_14"] = atr_pct

    if {"High", "Low"}.issubset(data.columns):
        level_df = data[["Close", "High", "Low"]]
    else:
        level_df = data[["Close"]]

    levels = consolidate_levels(level_df)
    fibonacci = compute_retracements(level_df)
    trend_map = trend_by_timeframe(data["Close"])
    trend = trend_map.get("daily") or trend_strength(data["Close"])
    breakout = breakout_signals(
        data["Close"],
        tuple(levels.supports),
        tuple(levels.resistances),
    )
    divergences = detect_rsi_divergences(data["Close"], indicators["RSI_14"])
    if "OBV" in indicators.columns:
        divergences += detect_obv_divergences(data["Close"], indicators["OBV"])
    if "Histogram" in macd_df.columns:
        divergences += detect_macd_histogram_divergences(data["Close"], macd_df["Histogram"])

    latest_price = float(data["Close"].iloc[-1])
    latest_date = data.index[-1]

    return MarketSnapshot(
        levels=levels,
        fibonacci=fibonacci,
        trend=trend,
        trend_multi=trend_map,
        breakout=breakout,
        divergences=divergences,
        indicators=indicators,
        latest_price=latest_price,
        latest_date=latest_date,
        macro_context={},
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


def _classify_trend_strength(
    trend: TrendSnapshot,
    *,
    price_above_ma200: Optional[bool] = None,
) -> str:
    if trend.direction == "uptrend":
        if trend.crossover == "bullish_stack" and (price_above_ma200 is None or price_above_ma200):
            return "alta forte"
        return "alta moderada"
    if trend.direction == "downtrend":
        if trend.crossover == "bearish_stack" and (price_above_ma200 is None or price_above_ma200 is False):
            return "baixa forte"
        return "baixa moderada"
    return "lateral"


def _describe_trend_regimes(snapshot: MarketSnapshot) -> tuple[List[str], str, Optional[str]]:
    lines: List[str] = []
    price_above_ma200: Optional[bool] = None
    if not snapshot.indicators.empty and "SMA_200" in snapshot.indicators.columns:
        sma200 = snapshot.indicators["SMA_200"].iloc[-1]
        if pd.notna(sma200) and sma200 != 0:
            price_above_ma200 = snapshot.latest_price >= float(sma200)

    daily_label = _classify_trend_strength(snapshot.trend, price_above_ma200=price_above_ma200)
    t = snapshot.trend
    if t.direction == "sideways":
        if t.slope_short < 0 and (t.slope_medium > 0 or t.slope_long > 0) and (
            t.crossover == "bullish_stack" or (price_above_ma200 is True)
        ):
            daily_label = "correção em tendência de alta"
        elif t.slope_short > 0 and (t.slope_medium < 0 or t.slope_long < 0) and (
            t.crossover == "bearish_stack" or (price_above_ma200 is False)
        ):
            daily_label = "repique em tendência de baixa"
    lines.append(f"- Tendência diária: {daily_label}")

    weekly = snapshot.trend_multi.get("weekly") if snapshot.trend_multi else None
    weekly_label = None
    if weekly:
        weekly_label = _classify_trend_strength(weekly)
        lines.append(f"- Tendência semanal: {weekly_label}")
    return lines, daily_label, weekly_label


def _describe_moving_averages(
    snapshot: MarketSnapshot,
    columns: Optional[List[tuple[str, str]]] = None,
) -> List[str]:
    if snapshot.indicators.empty:
        return []
    latest = snapshot.indicators.iloc[-1]
    price = snapshot.latest_price
    columns = columns or [
        ("EMA 9", "EMA_9"),
        ("EMA 21", "EMA_21"),
        ("EMA 72", "EMA_72"),
        ("EMA 200", "EMA_200"),
        ("SMA 200", "SMA_200"),
    ]
    details: List[str] = []
    for label, col in columns:
        value = latest.get(col)
        if value is None or pd.isna(value):
            continue
        value = float(value)
        if value == 0:
            continue
        status = "acima" if price >= value else "abaixo"
        diff_pct = (price / value - 1.0) * 100.0
        details.append(f"{label}: {status} ({value:.2f}, Δ {diff_pct:+.2f}%)")
    if not details:
        return []
    return ["- Preço vs. médias: " + "; ".join(details)]


def _volume_info(snapshot: MarketSnapshot) -> Optional[tuple[float, float, float, str]]:
    if snapshot.indicators.empty:
        return None
    volume_series = snapshot.indicators.get("Volume")
    vol_ma20_series = snapshot.indicators.get("Volume_MA20")
    vol_ratio_series = snapshot.indicators.get("Volume_Ratio")
    if volume_series is None or vol_ma20_series is None or vol_ratio_series is None:
        return None
    volume = volume_series.iloc[-1]
    ma20 = vol_ma20_series.iloc[-1]
    ratio = vol_ratio_series.iloc[-1]
    if pd.isna(volume) or pd.isna(ma20) or pd.isna(ratio):
        return None
    if ratio >= 1.5:
        qual = "acima da média (pressão forte)"
    elif ratio >= 1.0:
        qual = "ligeiramente acima da média"
    elif ratio >= 0.7:
        qual = "abaixo da média"
    else:
        qual = "bem abaixo da média (movimento fraco)"
    return float(volume), float(ma20), float(ratio), qual


def _describe_volume(snapshot: MarketSnapshot) -> List[str]:
    info = _volume_info(snapshot)
    if not info:
        return []
    volume_value, ma20_value, ratio_value, qual = info
    return [
        "- Volume: "
        f"{volume_value:,.0f} vs média 20d {ma20_value:,.0f} (ratio {ratio_value:.2f}, {qual})"
    ]


def _describe_volatility(snapshot: MarketSnapshot) -> List[str]:
    if snapshot.indicators.empty or "ATR_Pct_14" not in snapshot.indicators.columns:
        return []
    atr_pct = snapshot.indicators["ATR_Pct_14"].iloc[-1]
    if pd.isna(atr_pct):
        return []
    if atr_pct >= 4.0:
        label = "volatilidade elevada"
    elif atr_pct >= 2.0:
        label = "volatilidade moderada"
    else:
        label = "volatilidade baixa"
    return [f"- ATR(14) normalizado: {atr_pct:.2f}% ({label})"]


def _describe_bollinger(snapshot: MarketSnapshot) -> tuple[List[str], Optional[str]]:
    if snapshot.indicators.empty:
        return [], None
    cols = [
        "BB_Middle_2_0",
        "BB_Upper_2_0",
        "BB_Lower_2_0",
    ]
    if not all(col in snapshot.indicators.columns for col in cols):
        return [], None

    latest = snapshot.indicators.iloc[-1]
    middle = latest["BB_Middle_2_0"]
    upper = latest["BB_Upper_2_0"]
    lower = latest["BB_Lower_2_0"]
    price = snapshot.latest_price
    if any(pd.isna(x) for x in (middle, upper, lower)):
        return [], None

    bandwidth = (upper - lower) / middle * 100 if middle else np.nan
    lines: List[str] = []
    hint: Optional[str] = None

    if not pd.isna(bandwidth):
        if bandwidth <= 4:
            lines.append(f"- Bandas de Bollinger (21, 2σ): squeeze (largura {bandwidth:.2f}% do preço)")
            hint = "Bandas Bollinger em squeeze (possível rompimento)"
        elif bandwidth >= 12:
            lines.append(f"- Bandas de Bollinger (21, 2σ): abertas (largura {bandwidth:.2f}%)")
        else:
            lines.append(f"- Bandas de Bollinger (21, 2σ): largura {bandwidth:.2f}%")

    if price >= upper:
        lines.append("- Preço tocando/rompendo a banda superior (movimento forte)" )
        hint = ("Preço encostando na banda superior, movimento forte" if not hint else hint)
    elif price <= lower:
        lines.append("- Preço tocando/rompendo a banda inferior (pressão vendedora)")
        hint = ("Preço encostando na banda inferior (pressão vendedora)" if not hint else hint)

    return lines, hint


def _describe_rsi(snapshot: MarketSnapshot) -> tuple[List[str], Optional[str]]:
    if snapshot.indicators.empty or "RSI_14" not in snapshot.indicators.columns:
        return [], None
    rsi_value = snapshot.indicators["RSI_14"].iloc[-1]
    if pd.isna(rsi_value):
        return [], None
    lines: List[str] = []
    hint: Optional[str] = None
    lines.append(f"- RSI(14): {rsi_value:.1f}")
    if rsi_value >= 70:
        hint = "RSI em sobrecompra"
    elif rsi_value <= 30:
        hint = "RSI em sobrevenda"
    elif rsi_value >= 55:
        hint = "RSI em terreno positivo"
    elif rsi_value <= 45:
        hint = "RSI em terreno fraco"
    return lines, hint


def _describe_macd(snapshot: MarketSnapshot) -> tuple[List[str], Optional[str]]:
    required = {"MACD", "Signal", "Histogram"}
    if snapshot.indicators.empty or not required.issubset(snapshot.indicators.columns):
        return [], None
    macd_line = snapshot.indicators["MACD"].iloc[-1]
    signal_line = snapshot.indicators["Signal"].iloc[-1]
    hist = snapshot.indicators["Histogram"].iloc[-1]
    if any(pd.isna(val) for val in (macd_line, signal_line, hist)):
        return [], None
    prev_hist = snapshot.indicators["Histogram"].iloc[-2] if len(snapshot.indicators) > 1 else np.nan
    lines: List[str] = []
    hint: Optional[str] = None
    lines.append(f"- MACD: {macd_line:.4f} | Signal: {signal_line:.4f} | Hist: {hist:.4f}")
    if macd_line > signal_line and hist > 0:
        hint = "MACD acima da linha de sinal, momentum comprador"
    elif macd_line < signal_line and hist < 0:
        hint = "MACD abaixo da linha de sinal, momentum vendedor"
    if not pd.isna(prev_hist):
        if hist > prev_hist:
            lines.append("  • Histograma crescente")
        elif hist < prev_hist:
            lines.append("  • Histograma decrescente")
    return lines, hint


def _describe_52w(snapshot: MarketSnapshot) -> tuple[List[str], Optional[str]]:
    required = {"Within_5pct_Max52w", "Within_5pct_Min52w", "Max_52w", "Min_52w"}
    if snapshot.indicators.empty or not required.issubset(snapshot.indicators.columns):
        return [], None
    latest = snapshot.indicators.iloc[-1]
    lines: List[str] = []
    hint: Optional[str] = None
    if bool(latest.get("Within_5pct_Max52w")):
        max_val = latest.get("Max_52w")
        lines.append(f"- Próximo do topo 52s ({max_val:.2f})")
        hint = "Preço perto do topo de 52 semanas"
    if bool(latest.get("Within_5pct_Min52w")):
        min_val = latest.get("Min_52w")
        lines.append(f"- Próximo do fundo 52s ({min_val:.2f})")
        if hint:
            hint += " e do fundo 52s"
        else:
            hint = "Preço perto do fundo de 52 semanas"
    return lines, hint


def _describe_stochastic(snapshot: MarketSnapshot) -> tuple[List[str], Optional[str]]:
    required = {"Stoch_%K_14", "Stoch_%D_14"}
    if snapshot.indicators.empty or not required.issubset(snapshot.indicators.columns):
        return [], None
    latest = snapshot.indicators.iloc[-1]
    k = latest.get("Stoch_%K_14")
    d = latest.get("Stoch_%D_14")
    if pd.isna(k) or pd.isna(d):
        return [], None
    lines = [f"- Estocástico (14): %K {k:.1f} | %D {d:.1f}"]
    hint = None
    if k >= 80 and d >= 80:
        hint = "Estocástico em sobrecompra"
    elif k <= 20 and d <= 20:
        hint = "Estocástico em sobrevenda"
    elif k > d:
        hint = "Estocástico cruzado para cima"
    elif k < d:
        hint = "Estocástico cruzado para baixo"
    return lines, hint


def _describe_macro(snapshot: MarketSnapshot) -> tuple[List[str], Optional[str]]:
    if not snapshot.macro_context:
        return [], None
    items = sorted(snapshot.macro_context.items(), key=lambda kv: abs(kv[1]), reverse=True)
    lines: List[str] = []
    human_hint: Optional[str] = None
    readable = []
    for name, corr in items:
        label = MACRO_LABELS.get(name, name)
        qual = "forte" if abs(corr) >= 0.6 else "moderada" if abs(corr) >= 0.3 else "fraca"
        direction = "positiva" if corr >= 0 else "negativa"
        readable.append(f"{label}: {corr:+.2f} ({qual} {direction})")
    if readable:
        lines.append("- Correlação 60d com ativos macro: " + "; ".join(readable))
        top_name, top_corr = items[0]
        direction = "positiva" if top_corr >= 0 else "negativa"
        human_hint = f"Correlação {direction} {top_corr:+.2f} com {MACRO_LABELS.get(top_name, top_name)}"
    return lines, human_hint


def _build_human_summary(
    snapshot: MarketSnapshot,
    daily_label: str,
    weekly_label: Optional[str],
    ema9_diff_pct: Optional[float],
    volume_ratio: Optional[float],
    volume_class: Optional[str],
    support_hint: Optional[str],
    resistance_hint: Optional[str],
    divergence_hint: Optional[str],
    bollinger_hint: Optional[str],
    rsi_hint: Optional[str],
    macd_hint: Optional[str],
    stoch_hint: Optional[str],
    fiftytwo_hint: Optional[str],
    macro_hint: Optional[str],
) -> Optional[str]:
    pieces: List[str] = []

    if weekly_label:
        pieces.append(f"Tendência diária em {daily_label} e semanal em {weekly_label}.")
    else:
        pieces.append(f"Tendência diária em {daily_label}.")

    if ema9_diff_pct is not None:
        if ema9_diff_pct >= 0:
            pieces.append(f"Preço trabalha {ema9_diff_pct:+.2f}% acima da EMA9.")
        else:
            pieces.append(f"Preço respira {ema9_diff_pct:+.2f}% em relação à EMA9.")

    if volume_ratio is not None and volume_class:
        pieces.append(f"Volume {volume_class.lower()} (ratio {volume_ratio:.2f}).")

    if support_hint:
        pieces.append(f"Suporte relevante próximo de {support_hint}.")
    if resistance_hint:
        pieces.append(f"Resistência marcante em {resistance_hint}.")

    if divergence_hint:
        pieces.append(f"Alerta: {divergence_hint}.")

    if bollinger_hint:
        pieces.append(bollinger_hint.rstrip(".") + ".")

    if rsi_hint:
        pieces.append(rsi_hint.rstrip(".") + ".")

    if macd_hint:
        pieces.append(macd_hint.rstrip(".") + ".")

    if stoch_hint:
        pieces.append(stoch_hint.rstrip(".") + ".")

    if fiftytwo_hint:
        pieces.append(fiftytwo_hint.rstrip(".") + ".")

    if macro_hint:
        pieces.append(macro_hint.rstrip(".") + ".")

    if not pieces:
        return None

    return "Resumo: " + " ".join(pieces)


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
    max_days: int = 15,
) -> List[DivergenceSignal]:
    if not divergences:
        return []
    return [div for div in divergences if (latest_date - div.price_index).days <= max_days]


def summarise_snapshot(snapshot: MarketSnapshot) -> str:
    lines: List[str] = []
    lines.append("Resumo")
    lines.append(
        f"- Preço atual: {snapshot.latest_price:.2f} em {_format_date(snapshot.latest_date)}"
    )
    lines.extend(_describe_trend(snapshot.trend))
    regime_lines, daily_label, weekly_label = _describe_trend_regimes(snapshot)
    lines.extend(regime_lines)
    lines.extend(_describe_moving_averages(snapshot))
    volume_info = _volume_info(snapshot)
    lines.extend(_describe_volume(snapshot))
    lines.extend(_describe_volatility(snapshot))
    bollinger_lines, bollinger_hint = _describe_bollinger(snapshot)
    lines.extend(bollinger_lines)
    rsi_lines, rsi_hint = _describe_rsi(snapshot)
    lines.extend(rsi_lines)
    macd_lines, macd_hint = _describe_macd(snapshot)
    lines.extend(macd_lines)
    stoch_lines, stoch_hint = _describe_stochastic(snapshot)
    lines.extend(stoch_lines)
    fiftytwo_lines, fiftytwo_hint = _describe_52w(snapshot)
    lines.extend(fiftytwo_lines)
    macro_lines, macro_hint = _describe_macro(snapshot)
    lines.extend(macro_lines)

    breakouts = [sig for sig in snapshot.breakout.values() if sig]
    if breakouts:
        for sig in breakouts:
            label = BREAKOUT_LABELS.get(sig.kind, sig.kind.replace('_', ' '))
            lines.append(
                f"- {label} perto de {sig.reference_level:.2f} (preço {sig.price:.2f})"
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
            kind_label = DIVERGENCE_KIND_LABELS.get(div.kind, div.kind)
            indicator_label = INDICATOR_LABELS.get(div.indicator, div.indicator)
            lines.append(
                f"- Divergência {indicator_label} {kind_label} detectada em {_format_date(div.price_index)} "
                f"(preço {div.price_level:.2f}, indicador {div.indicator_level:.2f})"
            )
    else:
        lines.append("- Sem divergências relevantes (RSI/OBV/MACD) nos últimos 15 dias")

    ema9_diff_pct: Optional[float] = None
    if not snapshot.indicators.empty and "EMA_9" in snapshot.indicators.columns:
        ema9 = snapshot.indicators["EMA_9"].iloc[-1]
        if pd.notna(ema9) and ema9 != 0:
            ema9_diff_pct = (snapshot.latest_price / float(ema9) - 1.0) * 100.0

    support_hint = supports_weekly[0] if supports_weekly else (supports_daily[0] if supports_daily else None)
    resistance_hint = resistances_weekly[0] if resistances_weekly else (resistances_daily[0] if resistances_daily else None)

    def _shorten(level_desc: Optional[str]) -> Optional[str]:
        if not level_desc:
            return None
        return level_desc.split("(")[0].strip()

    support_hint_short = _shorten(support_hint)
    resistance_hint_short = _shorten(resistance_hint)

    volume_ratio = volume_info[2] if volume_info else None
    volume_class = volume_info[3] if volume_info else None

    divergence_hint = None
    if recent_divs:
        latest_div = max(recent_divs, key=lambda div: div.price_index)
        kind_label = DIVERGENCE_KIND_LABELS.get(latest_div.kind, latest_div.kind)
        divergence_hint = (
            f"divergência {INDICATOR_LABELS.get(latest_div.indicator, latest_div.indicator)} {kind_label} observada em "
            f"{_format_date(latest_div.price_index)}"
        )

    human_summary = _build_human_summary(
        snapshot,
        daily_label=daily_label,
        weekly_label=weekly_label,
        ema9_diff_pct=ema9_diff_pct,
        volume_ratio=volume_ratio,
        volume_class=volume_class,
        support_hint=support_hint_short,
        resistance_hint=resistance_hint_short,
        divergence_hint=divergence_hint,
        bollinger_hint=bollinger_hint,
        rsi_hint=rsi_hint,
        macd_hint=macd_hint,
        stoch_hint=stoch_hint,
        fiftytwo_hint=fiftytwo_hint,
        macro_hint=macro_hint,
    )
    if human_summary:
        lines.append("")
        lines.append(human_summary)

    return "\n".join(lines)
