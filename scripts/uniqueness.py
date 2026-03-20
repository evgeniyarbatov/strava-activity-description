from __future__ import annotations

from pathlib import Path
from statistics import median

import numpy as np
import polyline

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
ROUTE_SAMPLE_POINTS = 64
DISTANCE_WEIGHT = 0.35


def decode_points(activity: dict) -> list[tuple[float, float]] | None:
    map_data = activity.get("map") or {}
    encoded = map_data.get("polyline")
    if not encoded:
        return None
    return polyline.decode(encoded)


def resample_points(
    points: list[tuple[float, float]], target_count: int
) -> list[tuple[float, float]]:
    if not points:
        return []
    if target_count <= 1:
        return [points[0]]
    if len(points) == 1:
        return [points[0]] * target_count

    distances = [0.0]
    total = 0.0
    for (lat_a, lon_a), (lat_b, lon_b) in zip(points, points[1:]):
        segment = ((lat_b - lat_a) ** 2 + (lon_b - lon_a) ** 2) ** 0.5
        total += segment
        distances.append(total)

    if total == 0:
        return [points[0]] * target_count

    resampled: list[tuple[float, float]] = []
    segment_index = 1
    for i in range(target_count):
        target_distance = (total * i) / (target_count - 1)
        while segment_index < len(distances) - 1 and distances[segment_index] < target_distance:
            segment_index += 1
        prev_distance = distances[segment_index - 1]
        next_distance = distances[segment_index]
        if next_distance == prev_distance:
            ratio = 0.0
        else:
            ratio = (target_distance - prev_distance) / (next_distance - prev_distance)
        (lat_a, lon_a) = points[segment_index - 1]
        (lat_b, lon_b) = points[segment_index]
        lat = lat_a + (lat_b - lat_a) * ratio
        lon = lon_a + (lon_b - lon_a) * ratio
        resampled.append((lat, lon))
    return resampled


def build_route_vector(points: list[tuple[float, float]]) -> np.ndarray:
    resampled = resample_points(points, ROUTE_SAMPLE_POINTS)
    if not resampled:
        return np.array([], dtype=float)
    lats = np.array([point[0] for point in resampled], dtype=float)
    lons = np.array([point[1] for point in resampled], dtype=float)
    lats = zscore_array(lats)
    lons = zscore_array(lons)
    vector = np.empty(lats.size + lons.size, dtype=float)
    vector[0::2] = lats
    vector[1::2] = lons
    return vector


def zscore_array(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    mean = float(values.mean())
    std = float(values.std())
    if std == 0:
        return np.zeros_like(values)
    return (values - mean) / std


def zscore_values(values: list[float]) -> list[float]:
    if not values:
        return []
    array = np.array(values, dtype=float)
    mean = float(array.mean())
    std = float(array.std())
    if std == 0:
        return [0.0 for _ in values]
    return [float((value - mean) / std) for value in values]


def build_run_item(payload: dict, activity_id: str | None = None) -> dict | None:
    activity = payload.get("activity") or payload
    activity_id = activity.get("id") or activity_id
    if activity_id is None:
        return None
    points = decode_points(activity)
    if not points:
        return None
    route_vector = build_route_vector(points)
    if route_vector.size == 0:
        return None
    distance_m = activity.get("distance")
    return {
        "id": str(activity_id),
        "vector": route_vector,
        "distance_m": float(distance_m) if distance_m is not None else None,
    }


def build_reference_runs(payloads: list[dict] | None = None) -> list[dict]:
    runs: list[dict] = []
    if payloads is None:
        for path in ACTIVITIES_DIR.glob("*.json"):
            payload = load_json(path)
            run_item = build_run_item(payload, activity_id=path.stem)
            if not run_item:
                continue
            runs.append(run_item)
        return runs

    for payload in payloads:
        run_item = build_run_item(payload)
        if not run_item:
            continue
        runs.append(run_item)
    return runs


def calculate_uniqueness_score(distances: list[float]) -> float | None:
    """Calculate a raw uniqueness score from cosine distances."""
    if not distances:
        return None
    median_distance = median(distances)
    if median_distance == 0:
        return UNIQUENESS_MAX
    ratio = min(distances) / median_distance
    return UNIQUENESS_MAX - ratio * (UNIQUENESS_MAX - UNIQUENESS_MIN)


def uniqueness_for_activity(
    payload: dict, reference_runs: list[dict], activity_id: str | None = None
) -> float | None:
    run_item = build_run_item(payload, activity_id=activity_id)
    if not run_item or not reference_runs:
        return None
    filtered_runs = [run for run in reference_runs if run["id"] != run_item["id"]]
    if not filtered_runs:
        return None
    distances = []
    route_distances = [
        float(np.linalg.norm(run_item["vector"] - reference["vector"]))
        for reference in filtered_runs
    ]

    distance_values = [run_item.get("distance_m")] + [
        reference.get("distance_m") for reference in filtered_runs
    ]
    if all(value is not None for value in distance_values):
        zscores = zscore_values([float(value) for value in distance_values])
        activity_distance = zscores[0]
        reference_distances = zscores[1:]
        for route_distance, distance_score in zip(route_distances, reference_distances):
            distances.append(route_distance + DISTANCE_WEIGHT * abs(activity_distance - distance_score))
    else:
        distances = route_distances

    return calculate_uniqueness_score(distances)


def uniqueness_description(score: float | None) -> str | None:
    if score is None:
        return None
    normalized = (score - UNIQUENESS_MIN) / (UNIQUENESS_MAX - UNIQUENESS_MIN)
    normalized = max(0.0, min(1.0, normalized))
    index = int((1 - normalized) * (len(UNIQUENESS_WORDS) - 1))
    return UNIQUENESS_WORDS[index]


def main() -> None:
    reference_runs = build_reference_runs()

    raw_scores: dict[Path, float | None] = {}
    for path in ACTIVITIES_DIR.glob("*.json"):
        payload = load_json(path)
        raw_scores[path] = uniqueness_for_activity(
            payload, reference_runs, activity_id=path.stem
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
