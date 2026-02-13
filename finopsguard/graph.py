from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from finopsguard.models import Anomaly, Recommendation, ReportPayload
from finopsguard.tools.notify_teams import TeamsNotifier


class FinOpsGraph:
    """Pipeline skeleton following the FinOps Guard one-page design."""

    def __init__(self, config_path: str) -> None:
        with Path(config_path).open("r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def run_weekly(self) -> ReportPayload:
        raw = self.ingest_node()
        normalized = self.normalize_node(raw)
        anomalies = self.anomaly_node(normalized)
        insights = self.insight_node(anomalies)
        recommendations = self.action_node(insights)
        report = self.report_node(anomalies, recommendations)
        self.notify_node(report)
        return report

    def ingest_node(self) -> list[dict[str, Any]]:
        # Placeholder for AWS Cost Explorer and CloudWatch ingestion.
        return [
            {"service": "AmazonEC2", "account": "prod", "tag": "platform", "cost_usd": 4100.0},
            {"service": "AmazonS3", "account": "prod", "tag": "platform", "cost_usd": 900.0},
        ]

    def normalize_node(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for row in raw:
            row.setdefault("day", date.today().isoformat())
        return raw

    def anomaly_node(self, rows: list[dict[str, Any]]) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for row in rows:
            if row["cost_usd"] > 3000:
                anomalies.append(
                    Anomaly(
                        day=date.today(),
                        dimension=f"{row['account']}:{row['service']}",
                        delta_abs=550.0,
                        delta_pct=15.5,
                        score=2.9,
                        severity="high",
                    )
                )
        return anomalies

    def insight_node(self, anomalies: list[Anomaly]) -> list[dict[str, Any]]:
        # Placeholder for LLM inference using prompts/insight.txt.
        return [
            {
                "anomaly": a,
                "hypothesis": "Sustained EC2 growth likely due to oversized instances in non-optimized autoscaling group.",
                "confidence": 0.78,
            }
            for a in anomalies
        ]

    def action_node(self, insights: list[dict[str, Any]]) -> list[Recommendation]:
        # Placeholder for LLM + policy rules using prompts/action.txt.
        recs: list[Recommendation] = []
        for item in insights:
            anomaly: Anomaly = item["anomaly"]
            recs.append(
                Recommendation(
                    action="Rightsize EC2 instances and enforce scale-in policy",
                    target=anomaly.dimension,
                    estimated_monthly_savings_usd=620.0,
                    effort="medium",
                    risk="low",
                )
            )
        return recs

    def report_node(self, anomalies: list[Anomaly], recommendations: list[Recommendation]) -> ReportPayload:
        return ReportPayload(
            title="FinOps Guard Weekly Report",
            summary="Weekly cloud cost review with anomalies and prioritized recommendations.",
            metrics={
                "anomaly_count": float(len(anomalies)),
                "estimated_monthly_savings_usd": float(
                    sum(r.estimated_monthly_savings_usd for r in recommendations)
                ),
            },
            anomalies=anomalies,
            recommendations=recommendations,
        )

    def notify_node(self, report: ReportPayload) -> None:
        notifier = TeamsNotifier.from_env()
        notifier.send_report(
            title=report.title,
            summary=report.summary,
            metrics=report.metrics,
            anomalies=[asdict(a) for a in report.anomalies],
            recommendations=[asdict(r) for r in report.recommendations],
        )
