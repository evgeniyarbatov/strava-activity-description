from datetime import datetime, timedelta, timezone

from pathlib import Path

from scripts.activity import activity_payload, parse_points, simplify_points


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


def test_parse_points_reads_track_data(tmp_path: Path) -> None:
    gpx_path = tmp_path / "sample.gpx"
    gpx_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
      <trkpt lat="1.0" lon="2.0">
        <ele>3</ele>
        <time>2026-01-01T00:00:00Z</time>
        <extensions>
          <gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
            <gpxtpx:hr>100</gpxtpx:hr>
            <gpxtpx:cad>80</gpxtpx:cad>
          </gpxtpx:TrackPointExtension>
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
""",
        encoding="utf-8",
    )

    points = parse_points(gpx_path)

    assert points == [
        {
            "lat": 1.0,
            "lon": 2.0,
            "ele": "3",
            "time": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "hr": "100",
            "cad": "80",
        }
    ]


def test_simplify_points_with_zero_distance() -> None:
    start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    points = [
        make_point(1.0, 2.0, "0", start),
        make_point(1.0, 2.00001, "0", start + timedelta(seconds=1)),
        make_point(1.0, 2.00002, "0", start + timedelta(seconds=2)),
    ]

    simplified = simplify_points(points, 0)

    assert simplified[0] == points[0]
    assert simplified[-1] == points[-1]
    assert all(point in points for point in simplified)
