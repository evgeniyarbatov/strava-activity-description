from scripts.poi import extract_polyline, match_poi


def test_match_poi_respects_priority() -> None:
    tags = {"natural": "wood", "water": "lake"}
    assert match_poi(tags) == "lake"


def test_extract_polyline_handles_missing() -> None:
    assert extract_polyline({}) is None
    assert extract_polyline({"activity": {"map": {}}}) is None


def test_extract_polyline_reads_activity_map() -> None:
    activity = {"activity": {"map": {"polyline": "abc"}}}
    assert extract_polyline(activity) == "abc"
