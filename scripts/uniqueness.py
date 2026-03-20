from __future__ import annotations

from pathlib import Path
from statistics import median

import numpy as np
import polyline
from shapely.geometry import LineString

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
COARSE_SIMPLIFY_M = 35
ROUTE_MAX_POINTS = 48
DISTANCE_WEIGHT = 0.35
CENTROID_WEIGHT = 0.2


def decode_points(activity: dict) -> list[tuple[float, float]] | None:
    map_data = activity.get("map") or {}
    encoded = map_data.get("polyline")
    if not encoded:
        return None
    return polyline.decode(encoded)


def simplify_points(
    points: list[tuple[float, float]], tolerance_m: float
) -> list[tuple[float, float]]:
    if len(points) <= 2:
        return points
    tolerance = tolerance_m / 111_320
    line = LineString([(lon, lat) for lat, lon in points])
    simplified = line.simplify(tolerance, preserve_topology=False)
    return [(lat, lon) for lon, lat in simplified.coords]


def build_route_vector(points: list[tuple[float, float]]) -> np.ndarray:
    simplified = simplify_points(points, COARSE_SIMPLIFY_M)
    if not simplified:
        return np.array([], dtype=float)
    lats = np.array([point[0] for point in simplified], dtype=float)
    lons = np.array([point[1] for point in simplified], dtype=float)
    lats = zscore_array(lats)
    lons = zscore_array(lons)
    vector = pad_or_trim_vector(lats, lons, ROUTE_MAX_POINTS)
    return vector


def zscore_array(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    mean = float(values.mean())
    std = float(values.std())
    if std == 0:
        return np.zeros_like(values)
    return (values - mean) / std


def pad_or_trim_vector(
    lats: np.ndarray, lons: np.ndarray, target_points: int
) -> np.ndarray:
    if target_points <= 0:
        return np.array([], dtype=float)
    count = min(len(lats), len(lons))
    lats = lats[:count]
    lons = lons[:count]
    if count == 0:
        return np.array([], dtype=float)
    if count < target_points:
        pad_count = target_points - count
        lats = np.pad(lats, (0, pad_count), mode="edge")
        lons = np.pad(lons, (0, pad_count), mode="edge")
    elif count > target_points:
        indices = np.linspace(0, count - 1, target_points).round().astype(int)
        lats = lats[indices]
        lons = lons[indices]
    vector = np.empty(target_points * 2, dtype=float)
    vector[0::2] = lats
    vector[1::2] = lons
    return vector


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
    centroid = (float(np.mean([pt[0] for pt in points])), float(np.mean([pt[1] for pt in points])))
    distance_m = activity.get("distance")
    return {
        "id": str(activity_id),
        "vector": route_vector,
        "centroid": centroid,
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
    centroid_lats = [run_item["centroid"][0]] + [
        reference["centroid"][0] for reference in filtered_runs
    ]
    centroid_lons = [run_item["centroid"][1]] + [
        reference["centroid"][1] for reference in filtered_runs
    ]
    centroid_lat_z = zscore_values(centroid_lats)
    centroid_lon_z = zscore_values(centroid_lons)
    centroid_distances = [
        float(
            ((centroid_lat_z[0] - centroid_lat_z[i]) ** 2 + (centroid_lon_z[0] - centroid_lon_z[i]) ** 2)
            ** 0.5
        )
        for i in range(1, len(centroid_lat_z))
    ]
    if all(value is not None for value in distance_values):
        zscores = zscore_values([float(value) for value in distance_values])
        activity_distance = zscores[0]
        reference_distances = zscores[1:]
        for route_distance, distance_score, centroid_distance in zip(
            route_distances, reference_distances, centroid_distances
        ):
            distances.append(
                route_distance
                + DISTANCE_WEIGHT * abs(activity_distance - distance_score)
                + CENTROID_WEIGHT * centroid_distance
            )
    else:
        for route_distance, centroid_distance in zip(route_distances, centroid_distances):
            distances.append(route_distance + CENTROID_WEIGHT * centroid_distance)

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
