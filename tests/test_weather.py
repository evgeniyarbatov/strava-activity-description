from datetime import datetime, timezone
from scripts.weather import build_weather_entries, filter_weather


def test_filter_weather_orders_and_filters() -> None:
    items = [
        {"timestamp": "2026-01-01T00:10:00Z", "weather_0_description": "rain", "main_feels_like": 1},
        {"timestamp": "2026-01-01T00:05:00Z", "weather_0_description": "cloudy", "main_feels_like": 2},
        {"timestamp": "2026-01-01T00:20:00Z", "weather_0_description": "sunny", "main_feels_like": 3},
    ]
    start_time = datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc)
    end_time = datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc)

    filtered = filter_weather(items, start_time, end_time)

    assert [item["timestamp"] for item in filtered] == [
        "2026-01-01T00:05:00Z",
        "2026-01-01T00:10:00Z",
    ]


def test_build_weather_entries_keeps_expected_fields() -> None:
    entries = build_weather_entries(
        [
            {"weather_0_description": "rain", "main_feels_like": 1, "extra": 5},
            {"weather_0_description": "clear", "main_feels_like": 3},
        ]
    )

    assert entries == [
        {"weather_0_description": "rain", "main_feels_like": 1},
        {"weather_0_description": "clear", "main_feels_like": 3},
    ]

