import polyline
import pytest

from scripts.uniqueness import (
    UNIQUENESS_MIN,
    UNIQUENESS_MAX,
    UNIQUENESS_WORDS,
    build_reference_runs,
    calculate_uniqueness_score,
    decode_points,
    point_distance,
    uniqueness_for_activity,
    uniqueness_description,
)


def test_decode_points_prefers_summary_polyline() -> None:
    points = [(1.0, 2.0), (3.0, 4.0)]
    encoded = polyline.encode(points)
    activity = {"map": {"summary_polyline": encoded}}
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
    activities = [
        {"activity": {"id": 1, "map": {"summary_polyline": encoded}}},
        {"activity": {"id": 2, "map": {}}},
    ]

    runs = build_reference_runs(activities)

    assert runs == [{"id": "1", "points": [(1.0, 2.0), (3.0, 4.0)]}]


def test_point_distance_calculates_euclidean() -> None:
    assert point_distance((0.0, 0.0), (3.0, 4.0)) == 5.0


def test_uniqueness_for_activity_ignores_same_id(monkeypatch) -> None:
    encoded = polyline.encode([(0.0, 0.0), (1.0, 1.0)])
    activity = {"id": 1, "map": {"summary_polyline": encoded}}
    reference_runs = [
        {"id": "1", "points": [(0.0, 0.0), (1.0, 1.0)]},
        {"id": "2", "points": [(0.0, 0.0), (2.0, 2.0)]},
    ]

    def fake_fastdtw(*_args, **_kwargs):
        return 10.0, []

    monkeypatch.setattr("scripts.uniqueness.fastdtw", fake_fastdtw)

    score = uniqueness_for_activity(activity, reference_runs)

    assert score == UNIQUENESS_MIN
