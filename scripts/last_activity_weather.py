from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path


def parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


data_dir = Path("data")
activities_path = data_dir / "strava_activities.json"
weather_path = data_dir / "weather.json"

with activities_path.open("r", encoding="utf-8") as handle:
    activities = json.load(handle)

last_activity = sorted(
    activities, key=lambda item: item["activity"]["start_date"]
)[-1]

start_time = parse_iso(last_activity["activity"]["start_date"])
elapsed_seconds = last_activity["activity"]["elapsed_time"]
end_time = start_time + timedelta(seconds=elapsed_seconds)

with weather_path.open("r", encoding="utf-8") as handle:
    weather_items = json.load(handle)

weather_during_activity = [
    item
    for item in weather_items
    if start_time <= parse_iso(item["timestamp"]) <= end_time
]
weather_during_activity.sort(key=lambda item: item["timestamp"])

output_dir = data_dir / "activities"
output_dir.mkdir(parents=True, exist_ok=True)

activity_id = str(last_activity["activity"]["id"])
output_path = output_dir / f"{activity_id}.json"

payload = {"activity": last_activity, "weather": weather_during_activity}

with output_path.open("w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=True, indent=2)
