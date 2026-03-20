import polyline
import pytest

from scripts.uniqueness import (
    UNIQUENESS_MIN,
    UNIQUENESS_MAX,
    UNIQUENESS_WORDS,
    build_reference_runs,
    calculate_uniqueness_score,
    decode_points,
    uniqueness_for_activity,
    uniqueness_description,
)


def test_decode_points_prefers_summary_polyline() -> None:
    points = [(1.0, 2.0), (3.0, 4.0)]
    encoded = polyline.encode(points)
    activity = {"map": {"polyline": encoded}}
    assert decode_points(activity) == points


def test_calculate_uniqueness_score_empty() -> None:
    assert calculate_uniqueness_score([]) is None


def test_calculate_uniqueness_score_median_zero() -> None:
    assert calculate_uniqueness_score([0.0, 0.0]) == UNIQUENESS_MAX


def test_calculate_uniqueness_score_ratio() -> None:
    score = calculate_uniqueness_score([10.0, 20.0, 30.0])
    assert score == pytest.approx(50.5)


def test_uniqueness_description_mapping() -> None:
    assert uniqueness_description(UNIQUENESS_MAX) == UNIQUENESS_WORDS[0]
    assert uniqueness_description(UNIQUENESS_MIN) == UNIQUENESS_WORDS[-1]


def test_build_reference_runs_skips_missing_polyline() -> None:
    encoded = polyline.encode([(1.0, 2.0), (3.0, 4.0)])
    payloads = [
        {"activity": {"id": 1, "map": {"polyline": encoded}}},
        {"activity": {"id": 2, "map": {}}},
    ]

    runs = build_reference_runs(payloads)

    assert runs == [
        {"id": "1", "route_text": encoded},
    ]


def test_uniqueness_for_activity_ignores_same_id() -> None:
    encoded = polyline.encode([(0.0, 0.0), (1.0, 1.0)])
    activity_payload = {
        "activity": {"id": 1, "map": {"polyline": encoded}},
    }
    reference_payloads = [
        activity_payload,
        {
            "activity": {
                "id": 2,
                "map": {
                    "polyline": polyline.encode([(0.0, 0.0), (2.0, 2.0)])
                },
            },
        },
    ]
    reference_runs = build_reference_runs(reference_payloads)

    score = uniqueness_for_activity(activity_payload, reference_runs)

    assert score == UNIQUENESS_MIN


def test_uniqueness_for_activity_uses_fallback_id() -> None:
    encoded = polyline.encode([(0.0, 0.0), (1.0, 1.0)])
    activity_payload = {
        "activity": {"map": {"polyline": encoded}},
    }
    reference_payloads = [
        activity_payload,
        {
            "activity": {
                "id": 2,
                "map": {
                    "polyline": polyline.encode([(0.0, 0.0), (2.0, 2.0)])
                },
            },
        },
    ]
    reference_runs = build_reference_runs(reference_payloads)

    score = uniqueness_for_activity(
        activity_payload, reference_runs, activity_id="run-1"
    )

    assert score == UNIQUENESS_MIN
