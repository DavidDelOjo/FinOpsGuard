from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict


@dataclass
class CostPoint:
    day: date
    account: str
    service: str
    tag: str
    cost_usd: float


@dataclass
class Anomaly:
    day: date
    dimension: str
    delta_abs: float
    delta_pct: float
    score: float
    severity: str


@dataclass
class Recommendation:
    action: str
    target: str
    estimated_monthly_savings_usd: float
    effort: str
    risk: str


@dataclass
class ReportPayload:
    title: str
    summary: str
    metrics: Dict[str, float]
    anomalies: list[Anomaly]
    recommendations: list[Recommendation]
