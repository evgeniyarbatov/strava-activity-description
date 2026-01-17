from datetime import datetime, timedelta, timezone

from scripts.activity import activity_payload


def make_point(lat: float, lon: float, ele: str, time: datetime) -> dict:
    return {
        "lat": lat,
        "lon": lon,
        "ele": ele,
        "time": time,
        "hr": "100",
        "cad": "80",
    }


def test_activity_payload() -> None:
    start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    points = [
        make_point(0.0, 0.0, "0", start),
        make_point(0.0, 0.00001, "10", start + timedelta(seconds=1)),
        make_point(0.0, 0.00002, "0", start + timedelta(seconds=2)),
    ]

    payload = activity_payload(points)

    assert payload["activity"]["start_date"] == "2026-01-01T00:00:00Z"
