from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class TeamsNotifier:
    webhook_url: str
    timeout_seconds: int = 10

    @classmethod
    def from_env(cls) -> "TeamsNotifier":
        webhook = os.getenv("TEAMS_WEBHOOK_URL", "")
        if not webhook:
            raise RuntimeError("TEAMS_WEBHOOK_URL is not set")
        return cls(webhook_url=webhook)

    def send_report(
        self,
        title: str,
        summary: str,
        metrics: dict[str, float],
        anomalies: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
    ) -> None:
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": title,
            "themeColor": "0078D7",
            "title": title,
            "sections": [
                {
                    "text": summary,
                    "facts": [
                        {"name": "Anomaly count", "value": str(int(metrics.get("anomaly_count", 0)))},
                        {
                            "name": "Estimated monthly savings",
                            "value": f"${metrics.get('estimated_monthly_savings_usd', 0):,.2f}",
                        },
                    ],
                },
                {
                    "title": "Top anomalies",
                    "text": self._to_bullets(anomalies, key="dimension"),
                },
                {
                    "title": "Recommended actions",
                    "text": self._to_bullets(recommendations, key="action"),
                },
            ],
        }

        response = requests.post(
            self.webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

    @staticmethod
    def _to_bullets(rows: list[dict[str, Any]], key: str) -> str:
        if not rows:
            return "- none"
        return "\n".join(f"- {row.get(key, 'n/a')}" for row in rows[:5])
