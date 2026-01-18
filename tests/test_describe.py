from datetime import datetime

import polyline

from scripts.describe import (
    activity_summary,
    format_duration,
    format_pace,
    location_from_polyline,
    render_prompt,
    time_of_day_description,
)
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


def test_activity_summary_builds_fields() -> None:
    activity = {"start_date_local": "2026-01-01T06:30:00Z"}
    weather_entries = [
        {"main_feels_like": 10, "weather_0_description": "rain"},
        {"main_feels_like": 12, "weather_0_description": "cloudy"},
    ]

    summary = activity_summary(activity, weather_entries)

    assert summary["start_time_local"] == "2026-01-01 06:30"
    assert summary["time_of_day_description"] == "morning"
    assert summary["feels_like"] == 11
    assert summary["weather_description"] == "rain, cloudy"


def test_location_from_polyline_uses_midpoint() -> None:
    class StubLocation:
        raw = {"address": {"city": "Paris", "country": "France"}}

    class StubGeolocator:
        def __init__(self) -> None:
            self.seen = None

        def reverse(self, coords, language, addressdetails):
            self.seen = coords
            return StubLocation()

    geolocator = StubGeolocator()
    encoded = polyline.encode([(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)])

    city, country = location_from_polyline(encoded, geolocator)

    assert geolocator.seen == (3.0, 4.0)
    assert (city, country) == ("Paris", "France")


def test_render_prompt_includes_activity_context(tmp_path) -> None:
    template_path = tmp_path / "template.txt"
    template_path.write_text("Report:\n{activity_context}", encoding="utf-8")
    inputs = {
        "distance_context": "medium",
        "moving_time_context": "solid",
        "average_cadence_context": "steady",
        "average_hr_context": "hard",
        "max_hr_context": "fierce",
        "start_time_local": "2026-01-01 06:30",
        "time_of_day_description": "morning",
        "feels_like": 11.2,
        "weather_description": "cloudy",
        "city_name": "Paris",
        "country": "France",
        "uniqueness_description": "distinct",
    }

    rendered = render_prompt(template_path, inputs)

    assert "ACTIVITY CONTEXT" in rendered
