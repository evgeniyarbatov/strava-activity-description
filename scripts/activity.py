from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import timezone
from pathlib import Path

import polyline
from shapely.geometry import LineString
from geopy.distance import distance as geo_distance

from scripts.utils import parse_iso, write_json

DATA_DIR = Path("data")
GPX_DIR = DATA_DIR / "gpx"
OUTPUT_DIR = DATA_DIR / "activities"
SIMPLIFY_DISTANCE_M = 10


def parse_points(path: Path) -> list[dict]:
    tree = ET.parse(path)
    root = tree.getroot()
    points: list[dict] = []
    for trkpt in root.findall(".//{*}trkpt"):
        time_text = trkpt.findtext("{*}time")
        if not time_text:
            continue
        point = {
            "lat": float(trkpt.attrib["lat"]),
            "lon": float(trkpt.attrib["lon"]),
            "time": parse_iso(time_text),
        }
        ele = trkpt.findtext("{*}ele")
        if ele is not None:
            point["ele"] = ele
        hr = trkpt.findtext(".//{*}hr")
        if hr is not None:
            point["hr"] = hr
        cad = trkpt.findtext(".//{*}cad")
        if cad is not None:
            point["cad"] = cad
        points.append(point)
    return points


def to_zulu(dt) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def to_local_zulu(dt) -> str:
    local_dt = dt.astimezone().replace(tzinfo=timezone.utc)
    return local_dt.isoformat().replace("+00:00", "Z")


def simplify_points(points: list[dict], min_distance_m: float) -> list[dict]:
    if len(points) < 2:
        return points
    tolerance = min_distance_m / 111_320
    line = LineString([(point["lon"], point["lat"]) for point in points])
    simplified = line.simplify(tolerance, preserve_topology=False)
    coord_map = {(point["lon"], point["lat"]): point for point in points}
    return [coord_map[(lon, lat)] for lon, lat in simplified.coords]


def activity_payload(points: list[dict]) -> dict:
    start_time = points[0]["time"]
    end_time = points[-1]["time"]
    moving_time = int(round((end_time - start_time).total_seconds()))

    distance_m = 0.0
    for prev, curr in zip(points, points[1:]):
        distance_m += geo_distance((prev["lat"], prev["lon"]), (curr["lat"], curr["lon"])).meters

    simplified_points = simplify_points(points, SIMPLIFY_DISTANCE_M)
    encoded = polyline.encode([(pt["lat"], pt["lon"]) for pt in simplified_points])

    return {
        "activity": {
            "start_date": to_zulu(start_time),
            "start_date_local": to_local_zulu(start_time),
            "distance": int(round(distance_m)),
            "moving_time": moving_time,
            "map": {"polyline": encoded},
        }
    }


def write_payload(path: Path, payload: dict) -> None:
    write_json(path, payload)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for gpx_path in sorted(GPX_DIR.glob("*.gpx")):
        output_path = OUTPUT_DIR / f"{gpx_path.stem}.json"
        if output_path.exists():
            continue
        points = parse_points(gpx_path)
        payload = activity_payload(points)
        write_payload(output_path, payload)


if __name__ == "__main__":
    main()
