"""Valida leitura unificada de tickers B3 na configuração principal."""

from __future__ import annotations

from pathlib import Path

import yaml

from quantfinance.workflows.b3 import load_tickers_from_config


def test_load_tickers_from_unified_config(tmp_path: Path) -> None:
    config = {
        "portfolio": {
            "name": "Test",
            "defaults": {"provider": "yahoo"},
            "assets": [
                {"name": "PETR4", "ticker": "PETR4.SA"},
            ],
        },
        "b3": {
            "tickers": ["PETR4", "VALE3", "PETR4"],
        },
    }
    config_path = tmp_path / "carteira.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")

    tickers = load_tickers_from_config(config_path)

    assert tickers == ["PETR4", "VALE3"]


def test_load_tickers_from_legacy_config(tmp_path: Path) -> None:
    config = {
        "carteira": {
            "tickers": ["BOVA11", "PETR4"],
        }
    }
    config_path = tmp_path / "legacy.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")

    tickers = load_tickers_from_config(config_path)

    assert tickers == ["BOVA11", "PETR4"]
