import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from scripts.merge import (
    GpxPoint,
    list_files,
    parse_gpx,
    parse_tcx,
    parse_time,
    time_key,
    write_gpx,
)


def test_write_gpx_includes_hr_and_cadence(tmp_path) -> None:
    points = [
        GpxPoint(
            lat="1.0",
            lon="2.0",
            ele="3",
            time="2026-01-01T00:00:00Z",
            time_key="2026-01-01T00:00:00Z",
        )
    ]
    tcx_data = {"2026-01-01T00:00:00Z": (120, 80)}
    output = tmp_path / "activity.gpx"

    write_gpx(points, tcx_data, output)

    tree = ET.parse(output)
    root = tree.getroot()
    assert root.find(".//{*}hr").text == "120"
    assert root.find(".//{*}cad").text == "80"


def test_parse_time_and_key() -> None:
    parsed = parse_time("2026-01-01T00:00:00Z")

    assert parsed == datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert time_key(parsed) == "2026-01-01T00:00:00Z"


def test_list_files_filters_by_suffix(tmp_path) -> None:
    (tmp_path / "a.gpx").write_text("a", encoding="utf-8")
    (tmp_path / "b.gpx").write_text("b", encoding="utf-8")
    (tmp_path / "c.tcx").write_text("c", encoding="utf-8")

    files = list_files(tmp_path, ".gpx")

    assert [path.name for path in files] == ["a.gpx", "b.gpx"]


def test_parse_tcx_reads_metrics(tmp_path) -> None:
    tcx_path = tmp_path / "sample.tcx"
    tcx_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase>
  <Activities>
    <Activity>
      <Lap>
        <Track>
          <Trackpoint>
            <Time>2026-01-01T00:00:00Z</Time>
            <HeartRateBpm><Value>150</Value></HeartRateBpm>
            <Cadence>80</Cadence>
          </Trackpoint>
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>
""",
        encoding="utf-8",
    )

    data = parse_tcx(tcx_path)

    assert data == {"2026-01-01T00:00:00Z": (150, 80)}


def test_parse_gpx_reads_points(tmp_path) -> None:
    gpx_path = tmp_path / "sample.gpx"
    gpx_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
      <trkpt lat="1.0" lon="2.0">
        <ele>3</ele>
        <time>2026-01-01T00:00:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
""",
        encoding="utf-8",
    )

    points = parse_gpx(gpx_path)

    assert points == [
        GpxPoint(
            lat="1.0",
            lon="2.0",
            ele="3",
            time="2026-01-01T00:00:00Z",
            time_key="2026-01-01T00:00:00Z",
        )
    ]
