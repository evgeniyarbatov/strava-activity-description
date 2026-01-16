from __future__ import annotations

import json
from pathlib import Path
from statistics import median

import polyline
from fastdtw import fastdtw


def decode_points(activity: dict) -> list[tuple[float, float]] | None:
    map_data = activity.get("map") or {}
    encoded = map_data.get("summary_polyline") or map_data.get("polyline")
    if not encoded:
        return None
    return polyline.decode(encoded)


def point_distance(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    return ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5


data_dir = Path("data")
activities_dir = data_dir / "activities"
strava_activities_path = data_dir / "strava_activities.json"

with strava_activities_path.open("r", encoding="utf-8") as handle:
    strava_activities = json.load(handle)

reference_runs: list[dict] = []
for item in strava_activities:
    activity = item["activity"]
    points = decode_points(activity)
    if not points:
        continue
    reference_runs.append(
        {
            "id": str(activity.get("id")),
            "date": activity.get("start_date_local") or activity.get("start_date"),
            "points": points,
        }
    )

for path in activities_dir.glob("*.json"):
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    activity = payload["activity"]["activity"]
    activity_id = str(activity.get("id"))
    points = decode_points(activity)

    if not points or not reference_runs:
        payload["uniqueness"] = {
            "score": None,
            "similar_dates": [],
        }
    else:
        distances: list[tuple[float, dict]] = []
        for reference in reference_runs:
            if reference["id"] == activity_id:
                continue
            distance, _ = fastdtw(points, reference["points"], dist=point_distance)
            distances.append((float(distance), reference))

        if not distances:
            payload["uniqueness"] = {
                "score": None,
                "similar_dates": [],
            }
        else:
            distances.sort(key=lambda item: item[0])
            nearest_distance = distances[0][0]
            median_distance = median(item[0] for item in distances)
            if median_distance == 0:
                score = 10
            else:
                ratio = min(1.0, nearest_distance / median_distance)
                score = 1 + 9 * (1 - ratio)

            similar = distances[:5]
            payload["uniqueness"] = {
                "score": score,
                "similar_dates": [item[1]["date"] for item in similar],
            }

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)
