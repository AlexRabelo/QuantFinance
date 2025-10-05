from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from quantfinance.workflows.audit import audit_b3_tickers, audit_yahoo_assets


def _write_config(path: Path) -> None:
    config = {
        "portfolio": {
            "name": "Test",
            "defaults": {"provider": "yahoo"},
            "assets": [
                {"name": "AAA", "ticker": "AAA.SA"},
                {"name": "BBB", "ticker": "BBB.SA"},
            ],
        },
        "b3": {"tickers": ["AAA", "BBB"]},
    }
    path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_parquet(path: Path, start: str, freq: str = "D", periods: int = 5) -> None:
    df = pd.DataFrame(
        {
            "Date": pd.date_range(start=start, periods=periods, freq=freq),
            "Close": range(periods),
        }
    )
    df.to_parquet(path, index=False)


def test_audit_yahoo_flags_missing_and_gaps(tmp_path: Path) -> None:
    config_path = tmp_path / "tickets.yaml"
    _write_config(config_path)

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # AAA com lacuna longa
    _write_parquet(data_dir / "AAA_raw.parquet", start="2024-01-01", freq="15D", periods=4)
    summary = audit_yahoo_assets(config_path, data_dir, max_gap_days=7)

    assert "BBB" in summary.missing
    assert summary.gaps, "Deveria sinalizar lacuna para AAA"
    assert summary.gaps[0].ticker == "AAA"


def test_audit_b3_detects_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "tickets.yaml"
    _write_config(config_path)

    data_dir = tmp_path / "b3"
    data_dir.mkdir()

    _write_parquet(data_dir / "AAA_raw.parquet", start="2024-01-01")

    summary = audit_b3_tickers(config_path, data_dir, max_gap_days=5)
    assert summary.missing == ["BBB"]
