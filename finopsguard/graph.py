from __future__ import annotations

import logging
import os
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import boto3
import yaml
from botocore.exceptions import BotoCoreError, ClientError

from finopsguard.models import Anomaly, Recommendation, ReportPayload
from finopsguard.tools.notify_teams import TeamsNotifier

logger = logging.getLogger(__name__)


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
        lookback_days = int(self.config.get("aws", {}).get("lookback_days", 90))
        end_day = date.today()
        start_day = end_day - timedelta(days=lookback_days)

        try:
            ce = boto3.client("ce", region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = ce.get_cost_and_usage(
                TimePeriod={"Start": start_day.isoformat(), "End": end_day.isoformat()},
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                GroupBy=[
                    {"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"},
                    {"Type": "DIMENSION", "Key": "SERVICE"},
                ],
            )
        except (BotoCoreError, ClientError) as exc:
            if os.getenv("FINOPSGUARD_USE_MOCK_DATA", "false").lower() == "true":
                logger.warning("AWS ingest failed; using mock data because FINOPSGUARD_USE_MOCK_DATA=true: %s", exc)
                return self._mock_ingest_data()
            logger.warning("AWS ingest failed; continuing with empty dataset: %s", exc)
            return []

        rows: list[dict[str, Any]] = []
        for day_entry in response.get("ResultsByTime", []):
            day = day_entry.get("TimePeriod", {}).get("Start")
            for group in day_entry.get("Groups", []):
                keys = group.get("Keys", ["unknown", "unknown"])
                account = keys[0] if len(keys) > 0 else "unknown"
                service = keys[1] if len(keys) > 1 else "unknown"
                amount = float(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0.0))
                rows.append(
                    {
                        "day": day,
                        "account": account,
                        "service": service,
                        "tag": "unallocated",
                        "cost_usd": amount,
                    }
                )
        return rows

    def normalize_node(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for row in raw:
            row.setdefault("day", date.today().isoformat())
            row.setdefault("account", "unknown")
            row.setdefault("service", "unknown")
            row.setdefault("tag", "unallocated")
        return raw

    def anomaly_node(self, rows: list[dict[str, Any]]) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        threshold_usd = float(self.config.get("thresholds", {}).get("min_absolute_delta_usd", 100.0))
        for row in rows:
            if row["cost_usd"] > threshold_usd:
                anomalies.append(
                    Anomaly(
                        day=date.fromisoformat(str(row["day"])),
                        dimension=f"{row['account']}:{row['service']}",
                        delta_abs=float(row["cost_usd"]),
                        delta_pct=100.0,
                        score=2.9,
                        severity="high" if row["cost_usd"] > (threshold_usd * 3) else "medium",
                    )
                )
        return anomalies

    def insight_node(self, anomalies: list[Anomaly]) -> list[dict[str, Any]]:
        # Placeholder for LLM inference using prompts/insight.txt.
        return [
            {
                "anomaly": a,
                "hypothesis": "Cost spike likely due to increased compute and missing rightsizing policy.",
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
                    action="Rightsize compute and enforce scale-in policy",
                    target=anomaly.dimension,
                    estimated_monthly_savings_usd=round(anomaly.delta_abs * 0.2, 2),
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
        notifier = TeamsNotifier.from_env_optional()
        if notifier is None:
            logger.info("TEAMS_WEBHOOK_URL is not set; skipping Teams notification")
            return
        notifier.send_report(
            title=report.title,
            summary=report.summary,
            metrics=report.metrics,
            anomalies=[asdict(a) for a in report.anomalies],
            recommendations=[asdict(r) for r in report.recommendations],
        )

    @staticmethod
    def _mock_ingest_data() -> list[dict[str, Any]]:
        return [
            {
                "day": date.today().isoformat(),
                "service": "AmazonEC2",
                "account": "prod",
                "tag": "platform",
                "cost_usd": 4100.0,
            },
            {
                "day": date.today().isoformat(),
                "service": "AmazonS3",
                "account": "prod",
                "tag": "platform",
                "cost_usd": 900.0,
            },
        ]
