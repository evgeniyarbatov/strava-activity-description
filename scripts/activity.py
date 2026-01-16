from __future__ import annotations

from pathlib import Path

from utils import load_json, write_json

DATA_DIR = Path("data")
ACTIVITIES_PATH = DATA_DIR / "strava_activities.json"
OUTPUT_DIR = DATA_DIR / "activities"


def load_activities(path: Path) -> list[dict]:
    return load_json(path)


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
    write_json(path, payload)


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
