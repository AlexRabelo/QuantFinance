"""Rotinas de auditoria para validar cobertura e qualidade das séries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from quantfinance.workflows.b3 import load_tickers_from_config
from quantfinance.workflows.portfolio import load_portfolio_config


@dataclass
class GapIssue:
    ticker: str
    max_gap: int
    last_gap: int
    last_date: pd.Timestamp
    path: Path


@dataclass
class AuditSummary:
    missing: list[str]
    gaps: list[GapIssue]
    failures: list[str]


def _collect_dates(path: Path) -> Optional[pd.Series]:
    df = pd.read_parquet(path, columns=["Date"])
    if df.empty:
        return None
    dates = pd.to_datetime(df["Date"], errors="coerce").dropna().sort_values()
    return dates if not dates.empty else None


def _evaluate_series(dates: pd.Series, max_gap_days: int) -> tuple[int, int, pd.Timestamp]:
    if dates.shape[0] <= 1:
        max_gap = 0
    else:
        gaps = dates.diff().dt.days.dropna()
        max_gap = int(gaps.max()) if not gaps.empty else 0
    today = pd.Timestamp.today().normalize()
    last_date = pd.to_datetime(dates.iloc[-1])
    last_gap = int((today - last_date).days)
    return max_gap, last_gap, last_date


def _audit_directory(
    expected: Iterable[str],
    data_dir: Path,
    *,
    suffix: str,
    max_gap_days: int,
) -> AuditSummary:
    missing: list[str] = []
    gaps: list[GapIssue] = []
    failures: list[str] = []

    for ticker in expected:
        file_path = data_dir / f"{ticker}{suffix}"
        if not file_path.exists():
            missing.append(ticker)
            continue
        try:
            dates = _collect_dates(file_path)
        except Exception as exc:  # pragma: no cover - leitura defensiva
            failures.append(f"{ticker}: erro ao ler {file_path} ({exc})")
            continue
        if dates is None:
            failures.append(f"{ticker}: arquivo vazio em {file_path}")
            continue
        max_gap, last_gap, last_date = _evaluate_series(dates, max_gap_days)
        if max_gap > max_gap_days or last_gap > max_gap_days:
            gaps.append(
                GapIssue(
                    ticker=ticker,
                    max_gap=max_gap,
                    last_gap=last_gap,
                    last_date=last_date,
                    path=file_path,
                )
            )

    return AuditSummary(missing=missing, gaps=gaps, failures=failures)


def audit_yahoo_assets(
    config_path: Path,
    data_dir: Path,
    *,
    max_gap_days: int = 7,
) -> AuditSummary:
    config = load_portfolio_config(config_path)
    expected = [asset.name for asset in config.assets]
    return _audit_directory(expected, data_dir, suffix="_raw.parquet", max_gap_days=max_gap_days)


def audit_b3_tickers(
    config_path: Path,
    data_dir: Path,
    *,
    max_gap_days: int = 10,
) -> AuditSummary:
    expected = load_tickers_from_config(config_path)
    return _audit_directory(expected, data_dir, suffix="_raw.parquet", max_gap_days=max_gap_days)
