from datetime import datetime

import polyline

from scripts.context import DAWN, EARLY_EVENING, LATE_NIGHT, MIDDAY, time_of_day_description
from scripts.describe import (
    activity_summary,
    build_reflection,
    format_duration,
    format_pace,
    journal_path_from_activity,
    location_from_polyline,
    render_activity_context,
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
    assert time_of_day_description(datetime(2024, 1, 1, 6, 0, 0)) in set(DAWN)
    assert time_of_day_description(datetime(2024, 1, 1, 12, 0, 0)) in set(MIDDAY)
    assert time_of_day_description(datetime(2024, 1, 1, 18, 0, 0)) in set(EARLY_EVENING)
    assert time_of_day_description(datetime(2024, 1, 1, 23, 0, 0)) in set(LATE_NIGHT)


def test_activity_summary_builds_fields() -> None:
    activity = {"start_date_local": "2026-01-01T06:30:00Z"}
    weather_entries = [
        {"feels_like": "cool", "description": "rain"},
        {"feels_like": "cool", "description": "cloudy"},
    ]
    traffic_entries = [
        {"description": "heavy"},
        {"description": "gridlock"},
    ]

    summary = activity_summary(activity, weather_entries, traffic_entries)

    assert summary["start_time_local"] == "2026-01-01 06:30"
    assert summary["feels_like"] == "cool"
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


def test_render_activity_context_includes_header() -> None:
    inputs = {
        "distance_context": "medium",
        "moving_time_context": "solid",
        "start_time_local": "2026-01-01 06:30",
        "time_of_day_description": "morning",
        "feels_like": "cool",
        "weather_description": "cloudy",
        "traffic_description": "gridlock",
        "city_name": "Paris",
        "country": "France",
        "uniqueness_description": "distinct",
        "points_of_interest": "park, river",
    }

    rendered = render_activity_context(inputs)

    assert "ACTIVITY CONTEXT" in rendered


def test_journal_path_from_activity_uses_local_date() -> None:
    activity = {"start_date_local": "2026-03-15T06:23:39Z"}
    path = journal_path_from_activity(activity)
    assert path.name == "2026-03-15.md"
    assert path.parent.name == "journal"


def test_build_reflection_includes_perspective_headers() -> None:
    perspectives = {
        "artist": "Silver light on the lake.",
        "buddhist-monk": "Each step passes.",
        "memory": "The reservoir stays flat.",
        "scientist": "Overcast, lengthy, notable route.",
        "cartographer": "A loop with a late detour.",
        "physiologist": "Effort arrived in the second half.",
        "archivist": "Notable against your usual shapes.",
        "dreamer": "The lake holds what the sky will not.",
        "contrarian": "You will call this easy.",
    }
    reflection = build_reflection(
        run_date="2026-03-15",
        perspectives=perspectives,
    )

    assert reflection.startswith("# 2026-03-15\n\n")
    assert "## Artist\n\nSilver light on the lake." in reflection
    assert "## Monk\n\nEach step passes." in reflection
    assert "## Cartographer\n\nA loop with a late detour." in reflection
    assert "── Afterglow" not in reflection
    assert "── Tensions" not in reflection
    assert "── Residue" not in reflection
