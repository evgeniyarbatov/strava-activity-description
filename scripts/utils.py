from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def env_path(name: str, default: str) -> Path:
    """Resolve a directory path from an env var, falling back to a repo-relative default."""
    return Path(os.environ.get(name, default))


def parse_iso(value: str) -> datetime:
    """Parse ISO 8601 timestamps, accepting trailing Zulu suffix."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON payloads with UTF-8 encoding."""
    with path.open("r", encoding="utf-8") as handle:
        result: dict[str, Any] = json.load(handle)
        return result


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON payloads with stable indentation for diffs."""
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)


def load_env(path: Path) -> None:
    """Load dotenv-style API keys for scripts."""
    load_dotenv(path, override=True)
