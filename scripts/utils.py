from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


def parse_iso(value: str) -> datetime:
    """Parse ISO 8601 timestamps, accepting trailing Zulu suffix."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def load_json(path: Path) -> dict | list:
    """Load JSON payloads with UTF-8 encoding."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    """Write JSON payloads with stable indentation for diffs."""
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)


def load_env(path: Path) -> None:
    """Load dotenv-style API keys for scripts."""
    load_dotenv(path, override=True)
