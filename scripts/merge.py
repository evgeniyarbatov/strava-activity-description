"""Merge TCX cadence/HR with GPX location data into new GPX files."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/gpx")

GPX_NS = "http://www.topografix.com/GPX/1/1"
GPXTPX_NS = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"


@dataclass
class GpxPoint:
    lat: str
    lon: str
    ele: str | None
    time: str
    time_key: str


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def time_key(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def list_files(directory: Path, suffix: str) -> list[Path]:
    return sorted(p for p in directory.iterdir() if p.suffix.lower() == suffix)


def parse_tcx(path: Path) -> dict[str, tuple[int | None, int | None]]:
    tree = ET.parse(path)
    root = tree.getroot()
    data: dict[str, tuple[int | None, int | None]] = {}
    for tp in root.findall(".//{*}Trackpoint"):
        time_el = tp.find("{*}Time")
        dt = parse_time(time_el.text if time_el is not None else None)
        if not dt:
            continue
        hr_el = tp.find(".//{*}HeartRateBpm/{*}Value")
        cad_el = tp.find("{*}Cadence")
        hr = int(hr_el.text) if hr_el is not None and hr_el.text else None
        cad = int(cad_el.text) if cad_el is not None and cad_el.text else None
        data[time_key(dt)] = (hr, cad)
    return data


def parse_gpx(path: Path) -> list[GpxPoint]:
    tree = ET.parse(path)
    root = tree.getroot()
    points: list[GpxPoint] = []
    for trkpt in root.findall(".//{*}trkpt"):
        time_el = trkpt.find("{*}time")
        dt = parse_time(time_el.text if time_el is not None else None)
        if not dt:
            continue
        tk = time_key(dt)
        points.append(
            GpxPoint(
                lat=trkpt.attrib.get("lat", ""),
                lon=trkpt.attrib.get("lon", ""),
                ele=(trkpt.find("{*}ele").text if trkpt.find("{*}ele") is not None else None),
                time=tk,
                time_key=tk,
            )
        )
    return points


def load_gpx(path: Path) -> tuple[list[GpxPoint], set[str]]:
    points = parse_gpx(path)
    return points, {point.time_key for point in points}


def write_gpx(points: list[GpxPoint], tcx_data: dict[str, tuple[int | None, int | None]], output: Path) -> None:
    ET.register_namespace("", GPX_NS)
    ET.register_namespace("gpxtpx", GPXTPX_NS)

    gpx = ET.Element(
        "{http://www.topografix.com/GPX/1/1}gpx",
        {
            "version": "1.1",
            "creator": "merge_tcx_gpx",
        },
    )
    trk = ET.SubElement(gpx, "{http://www.topografix.com/GPX/1/1}trk")
    seg = ET.SubElement(trk, "{http://www.topografix.com/GPX/1/1}trkseg")

    for point in points:
        trkpt = ET.SubElement(
            seg,
            "{http://www.topografix.com/GPX/1/1}trkpt",
            {"lat": point.lat, "lon": point.lon},
        )
        if point.ele is not None:
            ET.SubElement(trkpt, "{http://www.topografix.com/GPX/1/1}ele").text = point.ele
        ET.SubElement(trkpt, "{http://www.topografix.com/GPX/1/1}time").text = point.time

        hr, cad = tcx_data.get(point.time_key, (None, None))
        if hr is not None or cad is not None:
            ext = ET.SubElement(trkpt, "{http://www.topografix.com/GPX/1/1}extensions")
            tpe = ET.SubElement(ext, f"{{{GPXTPX_NS}}}TrackPointExtension")
            if hr is not None:
                ET.SubElement(tpe, f"{{{GPXTPX_NS}}}hr").text = str(hr)
            if cad is not None:
                ET.SubElement(tpe, f"{{{GPXTPX_NS}}}cad").text = str(cad)

    tree = ET.ElementTree(gpx)
    ET.indent(tree, space="  ")
    tree.write(output, encoding="utf-8", xml_declaration=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tcx_files = list_files(RAW_DIR, ".tcx")
    gpx_files = list_files(RAW_DIR, ".gpx")
    gpx_cache: dict[Path, tuple[list[GpxPoint], set[str]]] = {}
    for tcx_file in tcx_files:
        output_id = uuid.uuid5(uuid.NAMESPACE_URL, tcx_file.name)
        output_path = OUT_DIR / f"{output_id}.gpx"
        if output_path.exists():
            continue
        tcx_data = parse_tcx(tcx_file)
        tcx_keys = set(tcx_data)
        match_file: Path | None = None
        match_points: list[GpxPoint] = []
        for gpx_file in gpx_files:
            if gpx_file not in gpx_cache:
                points, keys = load_gpx(gpx_file)
                gpx_cache[gpx_file] = (points, keys)
            else:
                points, keys = gpx_cache[gpx_file]
            if tcx_keys & keys:
                match_file = gpx_file
                match_points = points
                break
        if match_file is None:
            continue
        gpx_files.remove(match_file)
        gpx_points = [pt for pt in match_points if pt.time_key in tcx_data]
        if not gpx_points:
            continue
        write_gpx(gpx_points, tcx_data, output_path)


if __name__ == "__main__":
    main()
