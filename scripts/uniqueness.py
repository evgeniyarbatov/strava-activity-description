from __future__ import annotations

import json
from pathlib import Path
from statistics import median

import polyline
from fastdtw import fastdtw


UNIQUENESS_MIN = 1
UNIQUENESS_MAX = 100

DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
STRAVA_ACTIVITIES_PATH = DATA_DIR / "strava_activities.json"


def decode_points(activity: dict) -> list[tuple[float, float]] | None:
    map_data = activity.get("map") or {}
    encoded = map_data.get("summary_polyline") or map_data.get("polyline")
    if not encoded:
        return None
    return polyline.decode(encoded)


def point_distance(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    return ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5


def load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_reference_runs(strava_activities: list[dict]) -> list[dict]:
    runs: list[dict] = []
    for item in strava_activities:
        activity = item["activity"]
        points = decode_points(activity)
        if not points:
            continue
        runs.append(
            {
                "id": str(activity.get("id")),
                "points": points,
            }
        )
    return runs


def calculate_uniqueness_score(distances: list[float]) -> float | None:
    if not distances:
        return None
    ordered = sorted(distances)
    nearest_distance = ordered[0]
    median_distance = median(ordered)
    if median_distance == 0:
        return UNIQUENESS_MAX
    # Score rises as the nearest run becomes smaller relative to the median distance.
    ratio = min(1.0, nearest_distance / median_distance)
    return UNIQUENESS_MIN + (UNIQUENESS_MAX - UNIQUENESS_MIN) * (1 - ratio)


def uniqueness_for_activity(
    activity: dict, reference_runs: list[dict]
) -> float | None:
    points = decode_points(activity)
    if not points or not reference_runs:
        return None

    activity_id = str(activity.get("id"))
    distances: list[float] = []
    for reference in reference_runs:
        if reference["id"] == activity_id:
            continue
        distance, _ = fastdtw(points, reference["points"], dist=point_distance)
        distances.append(float(distance))
    return calculate_uniqueness_score(distances)


def write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)


def main() -> None:
    strava_activities = load_json(STRAVA_ACTIVITIES_PATH)
    reference_runs = build_reference_runs(strava_activities)

    for path in ACTIVITIES_DIR.glob("*.json"):
        payload = load_json(path)
        activity = payload["activity"]
        score = uniqueness_for_activity(activity, reference_runs)
        payload["uniqueness"] = {"score": score}
        write_json(path, payload)


if __name__ == "__main__":
    main()
