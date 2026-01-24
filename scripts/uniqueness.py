from __future__ import annotations

from pathlib import Path
from statistics import mean

import polyline
from shapely.geometry import LineString

from scripts.utils import load_json, write_json

UNIQUENESS_MIN = 1
UNIQUENESS_MAX = 100
RESAMPLE_POINTS = 50
UNIQUENESS_WORDS = [
    "mundane",
    "repetitive",
    "routine",
    "familiar",
    "commonplace",
    "standard",
    "ordinary",
    "typical",
    "distinct",
    "notable",
    "uncommon",
    "rare",
    "fresh",
    "original",
    "innovative",
    "novel",
]

DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"


def decode_points(activity: dict) -> list[tuple[float, float]] | None:
    map_data = activity.get("map") or {}
    encoded = map_data.get("summary_polyline") or map_data.get("polyline")
    if not encoded:
        return None
    return polyline.decode(encoded)


def point_distance(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    return ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5


def resample_points(
    points: list[tuple[float, float]], count: int
) -> list[tuple[float, float]]:
    line = LineString([(lon, lat) for lat, lon in points])
    if count <= 1:
        return [points[0]]
    length = line.length
    if length == 0:
        return [points[0]] * count
    step = length / (count - 1)
    resampled = []
    for i in range(count):
        point = line.interpolate(step * i)
        resampled.append((point.y, point.x))
    return resampled


def build_reference_runs() -> list[dict]:
    runs: list[dict] = []
    for path in ACTIVITIES_DIR.glob("*.json"):
        payload = load_json(path)
        activity = payload["activity"]
        points = decode_points(activity)
        if not points:
            continue
        activity_id = str(activity.get("id") or path.stem)
        runs.append(
            {
                "id": activity_id,
                "resampled": resample_points(points, RESAMPLE_POINTS),
            }
        )
    return runs


def mean_distance(distances: list[float]) -> float | None:
    if not distances:
        return None
    return mean(distances)


def uniqueness_for_activity(
    activity: dict, reference_runs: list[dict], activity_id: str
) -> float | None:
    points = decode_points(activity)
    if not points or not reference_runs:
        return None
    resampled = resample_points(points, RESAMPLE_POINTS)
    distances: list[float] = []
    for reference in reference_runs:
        if reference["id"] == activity_id:
            continue
        distance = mean(
            point_distance(a, b) for a, b in zip(resampled, reference["resampled"])
        )
        distances.append(float(distance))
    return mean_distance(distances)


def uniqueness_description(score: float | None) -> str | None:
    if score is None:
        return None
    normalized = (score - UNIQUENESS_MIN) / (UNIQUENESS_MAX - UNIQUENESS_MIN)
    index = int(normalized * (len(UNIQUENESS_WORDS) - 1))
    return UNIQUENESS_WORDS[index]


def main() -> None:
    reference_runs = build_reference_runs()

    raw_scores: dict[Path, float | None] = {}
    for path in ACTIVITIES_DIR.glob("*.json"):
        payload = load_json(path)
        activity = payload["activity"]
        activity_id = str(activity.get("id") or path.stem)
        raw_scores[path] = uniqueness_for_activity(
            activity, reference_runs, activity_id
        )

    valid_scores = [score for score in raw_scores.values() if score is not None]
    if not valid_scores:
        return

    min_score = min(valid_scores)
    max_score = max(valid_scores)

    for path, raw_score in raw_scores.items():
        payload = load_json(path)
        if raw_score is None:
            payload["uniqueness"] = {"description": None}
            write_json(path, payload)
            continue
        if min_score == max_score:
            score = UNIQUENESS_MAX
        else:
            normalized = (raw_score - min_score) / (max_score - min_score)
            score = UNIQUENESS_MIN + (UNIQUENESS_MAX - UNIQUENESS_MIN) * normalized
        payload["uniqueness"] = {"description": uniqueness_description(score)}
        write_json(path, payload)


if __name__ == "__main__":
    main()
