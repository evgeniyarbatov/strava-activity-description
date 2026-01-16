from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path


def parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


data_dir = Path("data")
activities_dir = data_dir / "activities"
weather_path = data_dir / "weather.json"

def activity_start_date(path: Path) -> datetime:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return parse_iso(payload["activity"]["start_date"])


activity_path = max(
    activities_dir.glob("*.json"), key=activity_start_date
)

with activity_path.open("r", encoding="utf-8") as handle:
    payload = json.load(handle)

last_activity = payload["activity"]

start_time = parse_iso(last_activity["start_date"])
moving_time = last_activity["moving_time"]
end_time = start_time + timedelta(seconds=moving_time)

with weather_path.open("r", encoding="utf-8") as handle:
    weather_items = json.load(handle)

weather_during_activity = [
    item
    for item in weather_items
    if start_time <= parse_iso(item["timestamp"]) <= end_time
]
weather_during_activity.sort(key=lambda item: item["timestamp"])

payload["weather"] = [
    {
        "weather_0_description": item["weather_0_description"],
        "main_feels_like": item["main_feels_like"],
    }
    for item in weather_during_activity
]

with activity_path.open("w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=True, indent=2)
