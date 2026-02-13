from datetime import date, timedelta

from finopsguard.graph import FinOpsGraph


def test_anomaly_node_detects_spike(tmp_path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
thresholds:
  anomaly_zscore: 2.0
  min_absolute_delta_usd: 2
  min_history_points: 5
  baseline_days: 10
aws:
  lookback_days: 90
""".strip()
    )

    graph = FinOpsGraph(str(cfg))

    start = date(2026, 1, 1)
    rows = []
    for i in range(10):
        rows.append(
            {
                "day": (start + timedelta(days=i)).isoformat(),
                "account": "prod",
                "service": "AmazonEC2",
                "tag": "platform",
                "cost_usd": 10.0,
            }
        )

    rows.append(
        {
            "day": (start + timedelta(days=10)).isoformat(),
            "account": "prod",
            "service": "AmazonEC2",
            "tag": "platform",
            "cost_usd": 30.0,
        }
    )

    anomalies = graph.anomaly_node(rows)
    assert len(anomalies) == 1
    assert anomalies[0].dimension == "prod:AmazonEC2"
    assert anomalies[0].delta_abs > 0
