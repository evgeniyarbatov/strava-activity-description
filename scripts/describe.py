from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import polyline
from geopy.geocoders import Nominatim


def parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def format_pace(seconds_per_km: float) -> str:
    total_seconds = int(round(seconds_per_km))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes}:{secs:02d}"


def time_of_day_description(start_time: datetime) -> str:
    hour = start_time.hour
    if 5 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 16:
        return "afternoon"
    if 17 <= hour <= 20:
        return "evening"
    return "night"


DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
PROMPT_FILES = [
    ("minimalist", Path("prompts/minimalist.txt")),
    ("scientific", Path("prompts/scientist.txt")),
    ("artist", Path("prompts/artist.txt")),
    ("athlete", Path("prompts/athlete.txt")),
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def payload_start_time(path: Path) -> datetime:
    payload = load_json(path)
    return parse_iso(payload["activity"]["start_date"])


def latest_payload(activities_dir: Path) -> dict:
    latest_path = max(activities_dir.glob("*.json"), key=payload_start_time)
    return load_json(latest_path)


def activity_summary(activity: dict, weather_entries: list[dict]) -> dict:
    distance_km = int(activity["distance"]) / 1000.0
    moving_time = int(activity["moving_time"])
    avg_pace = format_pace(moving_time / distance_km)

    start_time_local = parse_iso(activity["start_date_local"])
    start_time_local_str = start_time_local.strftime("%Y-%m-%d %H:%M")
    time_of_day = time_of_day_description(start_time_local)

    feels_like_values = [float(entry["main_feels_like"]) for entry in weather_entries]
    feels_like = sum(feels_like_values) / len(feels_like_values)
    weather_description = ", ".join(
        str(entry["weather_0_description"]) for entry in weather_entries
    )

    return {
        "distance_km": distance_km,
        "moving_time": format_duration(moving_time),
        "avg_pace_min_km": avg_pace,
        "start_time_local": start_time_local_str,
        "time_of_day_description": time_of_day,
        "feels_like": feels_like,
        "weather_description": weather_description,
    }


def location_from_polyline(map_polyline: str, geolocator: Nominatim) -> tuple[str | None, str | None]:
    coordinates = polyline.decode(map_polyline)
    median_lat, median_lng = coordinates[len(coordinates) // 2]
    location = geolocator.reverse(
        (median_lat, median_lng), language="en", addressdetails=True
    )
    address = location.raw.get("address", {}) if location else {}
    return address.get("city"), address.get("country")


def prompt_inputs(payload: dict) -> dict:
    activity = payload["activity"]
    weather_entries = payload["weather"]
    summary = activity_summary(activity, weather_entries)

    # Reverse geocode the midpoint of the route for location context.
    geolocator = Nominatim(user_agent="strava-activity-description")
    city, country = location_from_polyline(activity["map"]["polyline"], geolocator)

    uniqueness_score = float(payload["uniqueness"]["score"])
    summary.update(
        {
            "city_name": city,
            "country": country,
            "uniqueness_score": uniqueness_score,
        }
    )
    return summary


def render_prompt(template_path: Path, inputs: dict) -> str:
    prompt_template = template_path.read_text(encoding="utf-8")
    return prompt_template.format(**inputs)


def run_model(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", "mistral-nemo"],
        input=prompt,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> None:
    payload = latest_payload(ACTIVITIES_DIR)
    inputs = prompt_inputs(payload)

    for label, path in PROMPT_FILES:
        prompt = render_prompt(path, inputs)
        print(f"=== {label} prompt ===")
        print(prompt)
        print(f"=== {label} description ===")
        print(run_model(prompt))


if __name__ == "__main__":
    main()
