from __future__ import annotations

import json
from pathlib import Path


data_dir = Path("data")
activities_path = data_dir / "strava_activities.json"

with activities_path.open("r", encoding="utf-8") as handle:
    activities = json.load(handle)

last_activity = sorted(
    activities, key=lambda item: item["activity"]["start_date"]
)[-1]

output_dir = data_dir / "activities"
output_dir.mkdir(parents=True, exist_ok=True)

activity_id = str(last_activity["activity"]["id"])
output_path = output_dir / f"{activity_id}.json"

payload = {"activity": last_activity}

with output_path.open("w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=True, indent=2)
