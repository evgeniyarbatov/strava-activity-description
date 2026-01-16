from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path


def parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
WEATHER_PATH = DATA_DIR / "weather.json"


def load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def activity_start_date(path: Path) -> datetime:
    payload = load_json(path)
    return parse_iso(payload["activity"]["start_date"])


def latest_activity_path(activities_dir: Path) -> Path:
    return max(activities_dir.glob("*.json"), key=activity_start_date)


def filter_weather(
    weather_items: list[dict], start_time: datetime, end_time: datetime
) -> list[dict]:
    items = [
        item
        for item in weather_items
        if start_time <= parse_iso(item["timestamp"]) <= end_time
    ]
    items.sort(key=lambda item: item["timestamp"])
    return items


def build_weather_entries(weather_items: list[dict]) -> list[dict]:
    return [
        {
            "weather_0_description": item["weather_0_description"],
            "main_feels_like": item["main_feels_like"],
        }
        for item in weather_items
    ]


def write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)


def main() -> None:
    activity_path = latest_activity_path(ACTIVITIES_DIR)
    payload = load_json(activity_path)

    activity = payload["activity"]
    start_time = parse_iso(activity["start_date"])
    end_time = start_time + timedelta(seconds=activity["moving_time"])

    # Keep only weather items that fall within the activity window.
    weather_items = load_json(WEATHER_PATH)
    weather_during_activity = filter_weather(weather_items, start_time, end_time)
    payload["weather"] = build_weather_entries(weather_during_activity)

    write_json(activity_path, payload)


if __name__ == "__main__":
    main()
