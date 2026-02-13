from __future__ import annotations

import logging
import os
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import yaml

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
        if os.getenv("FINOPSGUARD_USE_MOCK_DATA", "false").lower() == "true":
            logger.info("FINOPSGUARD_USE_MOCK_DATA=true; using mock ingest dataset")
            return self._mock_ingest_data()

        lookback_days = int(self.config.get("aws", {}).get("lookback_days", 90))
        end_day = date.today()
        start_day = end_day - timedelta(days=lookback_days)

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError

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
        except (ImportError, BotoCoreError, ClientError) as exc:
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
        thresholds = self.config.get("thresholds", {})
        min_abs_delta = float(thresholds.get("min_absolute_delta_usd", 5.0))
        zscore_threshold = float(thresholds.get("anomaly_zscore", 2.5))
        min_history_points = int(thresholds.get("min_history_points", 7))
        baseline_days = int(thresholds.get("baseline_days", 14))

        grouped: dict[str, list[tuple[date, float]]] = {}
        for row in rows:
            day_str = str(row.get("day", date.today().isoformat()))
            day = date.fromisoformat(day_str)
            dimension = f"{row['account']}:{row['service']}"
            grouped.setdefault(dimension, []).append((day, float(row["cost_usd"])))

        for dimension, series in grouped.items():
            ordered = sorted(series, key=lambda x: x[0])
            if len(ordered) <= min_history_points:
                continue

            window = ordered[-(baseline_days + 1) :]
            current_day, current_cost = window[-1]
            baseline = [cost for _, cost in window[:-1]]

            if len(baseline) < min_history_points:
                continue

            base_mean = mean(baseline)
            base_std = pstdev(baseline)
            delta_abs = current_cost - base_mean
            if delta_abs < min_abs_delta:
                continue

            if base_std == 0:
                score = 10.0
            else:
                score = delta_abs / base_std

            if score < zscore_threshold:
                continue

            delta_pct = (delta_abs / base_mean * 100.0) if base_mean > 0 else 100.0
            severity = "high" if score >= (zscore_threshold + 1.0) else "medium"
            anomalies.append(
                Anomaly(
                    day=current_day,
                    dimension=dimension,
                    delta_abs=round(delta_abs, 2),
                    delta_pct=round(delta_pct, 2),
                    score=round(score, 2),
                    severity=severity,
                )
            )

        return sorted(anomalies, key=lambda a: a.score, reverse=True)

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
