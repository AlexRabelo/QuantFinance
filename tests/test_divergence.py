from __future__ import annotations

import pandas as pd

from quantfinance.analysis.divergence import (
    detect_obv_divergences,
    detect_macd_histogram_divergences,
)


def test_detect_obv_divergence_bullish() -> None:
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    prices = pd.Series([10, 9, 11, 8, 10, 9], index=dates)
    obv = pd.Series([100, 110, 120, 150, 140, 130], index=dates)

    signals = detect_obv_divergences(prices, obv, order=1, min_distance=1)

    assert any(sig.indicator == "OBV" and sig.kind == "bullish" for sig in signals)


def test_detect_macd_histogram_divergence_bearish() -> None:
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    prices = pd.Series([9, 11, 10, 12, 11, 10], index=dates)
    histogram = pd.Series([0.3, 0.6, 0.4, 0.2, 0.1, 0.05], index=dates)

    signals = detect_macd_histogram_divergences(prices, histogram, order=1, min_distance=1)

    assert any(sig.indicator == "MACD" and sig.kind == "bearish" for sig in signals)


