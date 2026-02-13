from __future__ import annotations

from dotenv import find_dotenv, load_dotenv


def load_runtime_env() -> None:
    """Load environment variables from a local .env file if present."""
    dotenv_path = find_dotenv(filename=".env", usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path, override=False)
