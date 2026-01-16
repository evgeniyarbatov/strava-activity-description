from __future__ import annotations

import json
from pathlib import Path


DATA_DIR = Path("data")
ACTIVITIES_PATH = DATA_DIR / "strava_activities.json"
OUTPUT_DIR = DATA_DIR / "activities"


def load_activities(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def latest_activity(activities: list[dict]) -> dict:
    return max(activities, key=lambda item: item["activity"]["start_date"])["activity"]


def build_payload(activity: dict) -> dict:
    return {
        "activity": {
            "start_date": activity["start_date"],
            "distance": activity["distance"],
            "moving_time": activity["moving_time"],
            "start_date_local": activity["start_date_local"],
            "map": {"polyline": activity["map"]["polyline"]},
        }
    }


def write_payload(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)


def main() -> None:
    activities = load_activities(ACTIVITIES_PATH)
    activity = latest_activity(activities)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{activity['id']}.json"

    # Normalize the latest activity into a compact payload for downstream scripts.
    payload = build_payload(activity)
    write_payload(output_path, payload)


if __name__ == "__main__":
    main()
