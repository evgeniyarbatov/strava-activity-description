import xml.etree.ElementTree as ET

from scripts.merge import GpxPoint, write_gpx


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
