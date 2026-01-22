from scripts.weather import (
    build_traffic_entries,
    build_weather_entries,
    filter_items_by_hour,
)


def test_filter_items_by_hour_orders_and_filters() -> None:
    items = [
        {"hour": 10, "data": {}},
        {"hour": 5, "data": {}},
        {"hour": 20, "data": {}},
    ]

    filtered = filter_items_by_hour(items, 5, 15)

    assert [item["hour"] for item in filtered] == [
        5,
        10,
    ]


def test_build_weather_entries_keeps_expected_fields() -> None:
    entries = build_weather_entries(
        [
            {"data": {"weather_description": "rain", "feels_like": 1, "extra": 5}},
            {"data": {"weather_description": "clear", "feels_like": 3}},
        ]
    )

    assert entries == [
        {"weather_description": "rain", "main_feels_like": 1},
        {"weather_description": "clear", "main_feels_like": 3},
    ]


def test_build_traffic_entries_keeps_expected_fields() -> None:
    entries = build_traffic_entries(
        [
            {"data": {"currentSpeed": 10, "freeFlowSpeed": 20, "extra": 5}},
            {"data": {"currentSpeed": 12, "freeFlowSpeed": 22}},
        ]
    )

    assert entries == [
        {"currentSpeed": 10, "freeFlowSpeed": 20},
        {"currentSpeed": 12, "freeFlowSpeed": 22},
    ]
