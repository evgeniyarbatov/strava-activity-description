import polyline
import pytest

from scripts.uniqueness import (
    UNIQUENESS_MIN,
    UNIQUENESS_MAX,
    UNIQUENESS_WORDS,
    calculate_uniqueness_score,
    decode_points,
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
