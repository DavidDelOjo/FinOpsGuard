from finopsguard.tools.notify_teams import TeamsNotifier


def test_bullets_empty() -> None:
    assert TeamsNotifier._to_bullets([], key="k") == "- none"
