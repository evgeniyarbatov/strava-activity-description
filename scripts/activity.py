from __future__ import annotations

import json
from pathlib import Path


data_dir = Path("data")
activities_path = data_dir / "strava_activities.json"

with activities_path.open("r", encoding="utf-8") as handle:
    activities = json.load(handle)

last_activity = sorted(
    activities, key=lambda item: item["activity"]["start_date"]
)[-1]["activity"]

output_dir = data_dir / "activities"
output_dir.mkdir(parents=True, exist_ok=True)

activity_id = str(last_activity["id"])
output_path = output_dir / f"{activity_id}.json"

payload = {
    "activity": {
        "start_date": last_activity["start_date"],
        "distance": last_activity["distance"],
        "moving_time": last_activity["moving_time"],
        "start_date_local": last_activity["start_date_local"],
        "map": {"polyline": last_activity["map"]["polyline"]},
    }
}

with output_path.open("w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=True, indent=2)
