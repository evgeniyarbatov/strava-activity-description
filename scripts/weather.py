from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from scripts.utils import load_json, parse_iso, write_json


DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
WEATHER_PATH = DATA_DIR / "weather.json"


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


def main() -> None:
    weather_items = load_json(WEATHER_PATH)
    for activity_path in sorted(ACTIVITIES_DIR.glob("*.json")):
        payload = load_json(activity_path)
        if "weather" in payload:
            continue
        activity = payload["activity"]
        start_time = parse_iso(activity["start_date"])
        end_time = start_time + timedelta(seconds=activity["moving_time"])

        # Keep only weather items that fall within the activity window.
        weather_during_activity = filter_weather(weather_items, start_time, end_time)
        payload["weather"] = build_weather_entries(weather_during_activity)

        write_json(activity_path, payload)


if __name__ == "__main__":
    main()
