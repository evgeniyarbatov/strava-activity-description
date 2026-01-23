from scripts.weather_traffic import (
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

    freezing = {
        "bone-chilling, rare Hanoi frost",
        "shockingly frigid for Vietnam",
        "once-in-a-decade freezing",
        "arctic winds invading the tropics",
        "glacial morning paralyzing the city",
        "perishingly cold, unprecedented chill",
        "numbing frost gripping the capital",
        "mercilessly frozen, almost Siberian",
        "devastatingly icy, historic low",
    }
    assert entries[0]["description"] == "rain"
    assert entries[1]["description"] == "clear"
    assert entries[0]["feels_like"] in freezing
    assert entries[1]["feels_like"] in freezing


def test_build_traffic_entries_keeps_expected_fields() -> None:
    entries = build_traffic_entries(
        [
            {"data": {"currentSpeed": 10, "freeFlowSpeed": 20, "extra": 5}},
            {"data": {"currentSpeed": 12, "freeFlowSpeed": 22}},
        ]
    )

    crawling = {
        "crawling along roads at snail's pace",
        "inching forward on streets painfully",
        "barely moving on roads, extreme patience required",
        "creeping along roadways grudgingly",
        "sluggishly advancing inch by inch",
        "tediously slow-motion traffic",
        "maddeningly gradual progress",
        "torturously crawling forward",
        "glacially slow movement",
        "laboriously inching through chaos",
        "ploddingly slow, testing patience",
        "excruciatingly sluggish flow",
    }
    assert entries[0]["description"] in crawling
    assert entries[1]["description"] in crawling
