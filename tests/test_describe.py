from datetime import datetime

from scripts.describe import format_duration, format_pace, time_of_day_description
from scripts.utils import parse_iso


def test_parse_iso_supports_zulu_suffix() -> None:
    value = "2024-01-01T10:00:00Z"
    parsed = parse_iso(value)
    assert parsed == datetime.fromisoformat("2024-01-01T10:00:00+00:00")


def test_format_duration() -> None:
    assert format_duration(3661) == "1:01:01"


def test_format_pace_rounds_seconds() -> None:
    assert format_pace(302.7) == "5:03"


def test_time_of_day_description() -> None:
    assert time_of_day_description(datetime(2024, 1, 1, 6, 0, 0)) == "morning"
    assert time_of_day_description(datetime(2024, 1, 1, 12, 0, 0)) == "afternoon"
    assert time_of_day_description(datetime(2024, 1, 1, 18, 0, 0)) == "evening"
    assert time_of_day_description(datetime(2024, 1, 1, 23, 0, 0)) == "night"
