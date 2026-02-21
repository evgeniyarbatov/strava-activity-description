from __future__ import annotations

from pathlib import Path
from statistics import median

import polyline
from fastdtw import fastdtw

from scripts.utils import load_json, write_json

UNIQUENESS_MIN = 1
UNIQUENESS_MAX = 100
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


def build_reference_runs(activities: list[dict] | None = None) -> list[dict]:
    runs: list[dict] = []
    if activities is None:
        for path in ACTIVITIES_DIR.glob("*.json"):
            payload = load_json(path)
            activity = payload["activity"]
            points = decode_points(activity)
            if not points:
                continue
            activity_id = str(activity.get("id") or path.stem)
            runs.append({"id": activity_id, "points": points})
        return runs

    for payload in activities:
        activity = payload["activity"]
        points = decode_points(activity)
        if not points:
            continue
        activity_id = str(activity.get("id"))
        runs.append({"id": activity_id, "points": points})
    return runs


def calculate_uniqueness_score(distances: list[float]) -> float | None:
    if not distances:
        return None
    median_distance = median(distances)
    if median_distance == 0:
        return UNIQUENESS_MAX
    ratio = min(distances) / median_distance
    return UNIQUENESS_MAX - ratio * (UNIQUENESS_MAX - UNIQUENESS_MIN)


def uniqueness_for_activity(activity: dict, reference_runs: list[dict]) -> float | None:
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


def uniqueness_description(score: float | None) -> str | None:
    if score is None:
        return None
    normalized = (score - UNIQUENESS_MIN) / (UNIQUENESS_MAX - UNIQUENESS_MIN)
    index = int((1 - normalized) * (len(UNIQUENESS_WORDS) - 1))
    return UNIQUENESS_WORDS[index]


def main() -> None:
    reference_runs = build_reference_runs()

    raw_scores: dict[Path, float | None] = {}
    for path in ACTIVITIES_DIR.glob("*.json"):
        payload = load_json(path)
        activity = payload["activity"]
        raw_scores[path] = uniqueness_for_activity(activity, reference_runs)

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
