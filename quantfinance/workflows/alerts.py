"""Rotinas de alerta e sinalização a partir das auditorias."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from quantfinance.workflows.audit import AuditSummary


@dataclass
class Alert:
    title: str
    message: str


@dataclass
class AlertReport:
    alerts: List[Alert]
    ok: bool


def build_alerts_from_summary(title: str, summary: AuditSummary) -> List[Alert]:
    alerts: List[Alert] = []
    if summary.missing:
        alerts.append(
            Alert(
                title=f"{title}: ativos ausentes",
                message=", ".join(sorted(summary.missing)),
            )
        )
    for issue in summary.gaps:
        alerts.append(
            Alert(
                title=f"{title}: gap elevado",
                message=(
                    f"{issue.ticker} – maior gap {issue.max_gap}d, "
                    f"gap atual {issue.last_gap}d (última data {issue.last_date.date()}, arquivo {issue.path})"
                ),
            )
        )
    for failure in summary.failures:
        alerts.append(Alert(title=f"{title}: falha de leitura", message=failure))
    return alerts


def build_alert_report(summaries: Iterable[tuple[str, AuditSummary]]) -> AlertReport:
    alerts: List[Alert] = []
    for title, summary in summaries:
        alerts.extend(build_alerts_from_summary(title, summary))
    return AlertReport(alerts=alerts, ok=not alerts)
