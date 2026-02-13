import os

from finopsguard.tools.notify_teams import TeamsNotifier


def test_bullets_empty() -> None:
    assert TeamsNotifier._to_bullets([], key="k") == "- none"


def test_from_env_optional_returns_none_without_webhook(monkeypatch) -> None:
    monkeypatch.delenv("TEAMS_WEBHOOK_URL", raising=False)
    assert TeamsNotifier.from_env_optional() is None


def test_from_env_optional_returns_notifier_with_webhook(monkeypatch) -> None:
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://example.com/webhook")
    notifier = TeamsNotifier.from_env_optional()
    assert notifier is not None
    assert notifier.webhook_url == "https://example.com/webhook"
