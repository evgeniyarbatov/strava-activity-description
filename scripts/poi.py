from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import polyline
import pyproj
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import transform

from scripts.utils import load_json, write_json

DATA_DIR = Path("data/activities")
OSM_PATH = Path("osm/hanoi.osm")

POI_TAGS = [
    ("leisure", {"park", "garden", "nature_reserve"}),
    ("natural", {"tree", "wood", "water", "wetland", "grassland"}),
    ("water", {"pond", "lake", "reservoir", "river"}),
    ("waterway", {"river", "stream", "canal"}),
    ("landuse", {"park", "forest", "recreation_ground", "village_green"}),
]


def parse_tags(element: ET.Element) -> dict:
    tags = {}
    for tag in element.findall("tag"):
        key = tag.get("k")
        value = tag.get("v")
        if key and value:
            tags[key] = value
    return tags


def match_poi(tags: dict) -> str | None:
    water_value = tags.get("water")
    if water_value in {"pond", "lake", "reservoir", "river"}:
        return water_value
    waterway_value = tags.get("waterway")
    if waterway_value in {"river", "stream", "canal"}:
        return waterway_value
    natural_value = tags.get("natural")
    if natural_value in {"tree", "wood", "water", "wetland", "grassland"}:
        return natural_value
    leisure_value = tags.get("leisure")
    if leisure_value in {"park", "garden", "nature_reserve"}:
        return leisure_value
    landuse_value = tags.get("landuse")
    if landuse_value in {"park", "forest", "recreation_ground", "village_green"}:
        return landuse_value
    return None


def load_pois(osm_path: Path) -> list[dict]:
    nodes: dict[str, tuple[float, float]] = {}
    pois: list[dict] = []
    context = ET.iterparse(osm_path, events=("end",))
    for _, element in context:
        if element.tag == "node":
            node_id = element.get("id")
            lat = element.get("lat")
            lon = element.get("lon")
            if node_id and lat and lon:
                nodes[node_id] = (float(lat), float(lon))
                tags = parse_tags(element)
                category = match_poi(tags)
                if category:
                    pois.append({"category": category, "lat": float(lat), "lon": float(lon)})
            element.clear()
        elif element.tag == "way":
            tags = parse_tags(element)
            category = match_poi(tags)
            if category:
                coords = []
                for node_ref in element.findall("nd"):
                    ref = node_ref.get("ref")
                    if ref and ref in nodes:
                        node_lat, node_lon = nodes[ref]
                        coords.append((node_lon, node_lat))
                if len(coords) >= 2:
                    if coords[0] == coords[-1] and len(coords) >= 4:
                        geom = Polygon(coords)
                    else:
                        geom = LineString(coords)
                    centroid = geom.centroid
                    pois.append({"category": category, "lat": centroid.y, "lon": centroid.x})
            element.clear()
    return pois


def buffer_in_meters(geom, meters: float):
    if geom.is_empty:
        return geom
    lon0 = geom.centroid.x
    lat0 = geom.centroid.y
    zone = int((lon0 + 180) / 6) + 1
    epsg = 32600 + zone if lat0 >= 0 else 32700 + zone
    crs_src = pyproj.CRS.from_epsg(4326)
    crs_dst = pyproj.CRS.from_epsg(epsg)
    forward = pyproj.Transformer.from_crs(crs_src, crs_dst, always_xy=True).transform
    backward = pyproj.Transformer.from_crs(crs_dst, crs_src, always_xy=True).transform
    projected = transform(forward, geom)
    buffered = projected.buffer(meters)
    return transform(backward, buffered)


def hull_from_polyline(encoded: str):
    points = polyline.decode(encoded)
    coords = [(lon, lat) for lat, lon in points]
    return LineString(coords).convex_hull


def enrich_activity(path: Path, pois: list[dict]) -> None:
    activity = load_json(path)
    geo = activity.get("geo")
    if not isinstance(geo, dict):
        geo = {}
    activity["geo"] = geo

    polyline_value = None
    if isinstance(activity.get("activity"), dict):
        activity_map = activity["activity"].get("map")
        if isinstance(activity_map, dict):
            polyline_value = activity_map.get("polyline")

    if not polyline_value:
        geo["points_of_interest"] = []
        write_json(path, activity)
        return

    hull = hull_from_polyline(polyline_value)
    buffered = buffer_in_meters(hull, 20)
    categories = set()
    for poi in pois:
        point = Point(poi["lon"], poi["lat"])
        if buffered.contains(point):
            categories.add(poi["category"])
    geo["points_of_interest"] = sorted(categories)
    write_json(path, activity)


def main() -> None:
    pois = load_pois(OSM_PATH)
    for path in sorted(DATA_DIR.glob("*.json")):
        enrich_activity(path, pois)


if __name__ == "__main__":
    main()
