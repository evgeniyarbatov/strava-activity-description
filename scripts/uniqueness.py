from __future__ import annotations

from pathlib import Path
from statistics import median

import polyline
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
ROUTE_NGRAM_RANGE = (2, 4)
ROUTE_MAX_FEATURES = 512


def decode_points(activity: dict) -> list[tuple[float, float]] | None:
    map_data = activity.get("map") or {}
    encoded = map_data.get("polyline")
    if not encoded:
        return None
    return polyline.decode(encoded)


def build_route_text(activity: dict) -> str | None:
    map_data = activity.get("map") or {}
    return map_data.get("polyline")


def build_run_item(payload: dict, activity_id: str | None = None) -> dict | None:
    activity = payload.get("activity") or payload
    activity_id = activity.get("id") or activity_id
    if activity_id is None:
        return None
    route_text = build_route_text(activity)
    if not route_text:
        return None
    return {
        "id": str(activity_id),
        "route_text": route_text,
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
    combined_runs = [run_item, *filtered_runs]
    route_texts = [run["route_text"] for run in combined_runs]

    route_matrix = build_route_matrix(route_texts)
    if route_matrix.shape[1] == 0:
        return None
    similarities = cosine_similarity(route_matrix[0], route_matrix[1:])[0]
    distances = [1 - float(score) for score in similarities]
    return calculate_uniqueness_score(distances)


def build_route_matrix(route_texts: list[str]) -> csr_matrix:
    if not any(text.strip() for text in route_texts):
        return csr_matrix((len(route_texts), 0))
    vectorizer = TfidfVectorizer(
        analyzer="char",
        lowercase=False,
        ngram_range=ROUTE_NGRAM_RANGE,
        max_features=ROUTE_MAX_FEATURES,
    )
    try:
        return vectorizer.fit_transform(route_texts)
    except ValueError:
        return csr_matrix((len(route_texts), 0))


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
