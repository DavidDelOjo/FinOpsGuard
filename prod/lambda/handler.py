from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict
from typing import Any

import boto3

from finopsguard.graph import FinOpsGraph

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _resolve_teams_webhook_from_secret() -> None:
    """Load TEAMS_WEBHOOK_URL from Secrets Manager when running in production."""
    if os.getenv("TEAMS_WEBHOOK_URL"):
        return

    secret_arn = os.getenv("TEAMS_WEBHOOK_SECRET_ARN", "")
    if not secret_arn:
        logger.info("TEAMS_WEBHOOK_SECRET_ARN not set; Teams notification may be skipped")
        return

    sm = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))
    response = sm.get_secret_value(SecretId=secret_arn)
    secret_str = response.get("SecretString", "")

    if not secret_str:
        raise RuntimeError("Teams secret exists but SecretString is empty")

    secret_str = secret_str.strip()
    if secret_str.startswith("{"):
        payload = json.loads(secret_str)
        for key in ("TEAMS_WEBHOOK_URL", "webhook_url", "url"):
            value = payload.get(key)
            if value:
                os.environ["TEAMS_WEBHOOK_URL"] = value
                return
        raise RuntimeError("Teams secret JSON does not contain a webhook URL key")

    os.environ["TEAMS_WEBHOOK_URL"] = secret_str


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    _resolve_teams_webhook_from_secret()

    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    graph = FinOpsGraph(config_path=config_path)
    report = graph.run_weekly()

    return {
        "statusCode": 200,
        "anomaly_count": int(report.metrics.get("anomaly_count", 0)),
        "estimated_monthly_savings_usd": float(report.metrics.get("estimated_monthly_savings_usd", 0.0)),
        "anomalies": [asdict(item) for item in report.anomalies],
    }
