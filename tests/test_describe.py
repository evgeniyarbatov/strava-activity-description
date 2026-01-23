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
    dawn = {
        "crack of dawn",
        "first light",
        "sunrise",
        "early morning",
        "daybreak",
        "dawn's glow",
        "the rooster hour",
        "pre-sunrise",
        "the breaking dawn",
        "morning's birth",
        "twilight's end",
        "the awakening",
        "eastern light",
        "fresh dawn",
        "new day's start",
        "cockcrow",
        "aurora",
        "the blue hour fades",
        "sun's arrival",
        "morning star time",
        "the yawning world",
        "dew-kissed morning",
        "the eastern glow",
        "dawn patrol",
        "sunrise symphony",
        "the world stirring",
        "birds' chorus",
        "misty morning",
    }
    midday = {
        "midday",
        "high noon",
        "lunch hour",
        "noon's peak",
        "the sun's zenith",
        "bright afternoon",
        "noontime",
        "meridian",
        "the height of day",
        "solar maximum",
        "lunch break",
        "noon sharp",
        "the blazing hour",
        "peak daylight",
        "the overhead sun",
        "full brightness",
        "day's climax",
        "the scorching hour",
        "lunch o'clock",
        "the brilliant hour",
        "zenith time",
        "sun directly above",
        "the hottest hour",
        "maximal light",
    }
    early_evening = {
        "early evening",
        "dusk",
        "twilight",
        "the golden hour",
        "sunset",
        "sundown",
        "day's end",
        "the gloaming",
        "eventide",
        "the magic hour",
        "sunset glow",
        "the dimming",
        "twilight zone",
        "the orange hour",
        "day's farewell",
        "vespers",
        "the transition hour",
        "dusky time",
        "purple hour",
        "sun's goodbye",
        "the softening light",
        "evening's arrival",
        "the mellowing",
        "sundown spectacle",
        "the photographer's hour",
        "crimson sky time",
        "fading daylight",
        "dusk's embrace",
    }
    late_night = {
        "late night",
        "near midnight",
        "the late hours",
        "bedtime",
        "the night deepens",
        "approaching midnight",
        "night owl time",
        "the waning day",
        "late evening",
        "the final hours",
        "closing time",
        "the day's last breath",
        "pre-midnight",
        "the sleepy hours",
        "the winding down",
        "late shift",
        "the settling night",
        "last call",
        "the drowsy hours",
        "evening's end",
        "the dark hours",
        "night's depth",
        "the calm before midnight",
        "the quiet night",
    }

    assert time_of_day_description(datetime(2024, 1, 1, 6, 0, 0)) in dawn
    assert time_of_day_description(datetime(2024, 1, 1, 12, 0, 0)) in midday
    assert time_of_day_description(datetime(2024, 1, 1, 18, 0, 0)) in early_evening
    assert time_of_day_description(datetime(2024, 1, 1, 23, 0, 0)) in late_night


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
    dawn = {
        "crack of dawn",
        "first light",
        "sunrise",
        "early morning",
        "daybreak",
        "dawn's glow",
        "the rooster hour",
        "pre-sunrise",
        "the breaking dawn",
        "morning's birth",
        "twilight's end",
        "the awakening",
        "eastern light",
        "fresh dawn",
        "new day's start",
        "cockcrow",
        "aurora",
        "the blue hour fades",
        "sun's arrival",
        "morning star time",
        "the yawning world",
        "dew-kissed morning",
        "the eastern glow",
        "dawn patrol",
        "sunrise symphony",
        "the world stirring",
        "birds' chorus",
        "misty morning",
    }
    assert summary["time_of_day_description"] in dawn
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


def test_render_prompt_includes_activity_context(tmp_path) -> None:
    template_path = tmp_path / "template.txt"
    template_path.write_text("Report:\n{activity_context}", encoding="utf-8")
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

    rendered = render_prompt(template_path, inputs)

    assert "ACTIVITY CONTEXT" in rendered
