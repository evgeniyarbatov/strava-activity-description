from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path

import polyline
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from google import genai

from scripts.utils import load_json, parse_iso


DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
PROMPTS_DIR = Path("prompts")
PROMPT_FILES = [
    (path.stem, path) for path in sorted(PROMPTS_DIR.glob("*.txt"), key=lambda path: path.name)
]
ACTIVITY_CONTEXT_PATH = PROMPTS_DIR / "common" / "activity-context.txt"
GEMINI_MODEL = "gemini-2.5-flash"
PROMPT_INPUT_KEYS = [
    "distance_context",
    "moving_time_context",
    "average_cadence_context",
    "average_hr_context",
    "max_hr_context",
    "start_time_local",
    "time_of_day_description",
    "feels_like",
    "weather_description",
    "city_name",
    "country",
    "uniqueness_description",
]

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


def payload_start_time(path: Path) -> datetime:
    payload = load_json(path)
    return parse_iso(payload["activity"]["start_date"])


def latest_payload(activities_dir: Path) -> dict:
    latest_path = max(activities_dir.glob("*.json"), key=payload_start_time)
    return load_json(latest_path)


def activity_summary(activity: dict, weather_entries: list[dict]) -> dict:
    start_time_local = parse_iso(activity["start_date_local"])
    start_time_local_str = start_time_local.strftime("%Y-%m-%d %H:%M")
    time_of_day = time_of_day_description(start_time_local)

    feels_like_values = [float(entry["main_feels_like"]) for entry in weather_entries]
    feels_like = sum(feels_like_values) / len(feels_like_values)
    weather_description = ", ".join(
        str(entry["weather_0_description"]) for entry in weather_entries
    )

    return {
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
    activity_context = payload["activity_context"]

    # Reverse geocode the midpoint of the route for location context.
    geolocator = Nominatim(user_agent="strava-activity-description")
    city, country = location_from_polyline(activity["map"]["polyline"], geolocator)

    uniqueness_description = payload["uniqueness"]["description"]
    summary.update(
        {
            "distance_context": activity_context["distance"],
            "moving_time_context": activity_context["moving_time"],
            "average_cadence_context": activity_context["average_cadence"],
            "average_hr_context": activity_context["average_hr"],
            "max_hr_context": activity_context["max_hr"],
            "city_name": city,
            "country": country,
            "uniqueness_description": uniqueness_description,
        }
    )
    return summary


def render_prompt(template_path: Path, inputs: dict) -> str:
    prompt_template = template_path.read_text(encoding="utf-8")
    activity_context_template = ACTIVITY_CONTEXT_PATH.read_text(encoding="utf-8")
    activity_context = activity_context_template.format(**inputs)
    return prompt_template.format(**inputs, activity_context=activity_context)


def run_model(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", "mistral-nemo"],
        input=prompt,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def run_gemini(prompt: str, client: genai.Client) -> str:
    result = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return result.text.strip()


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--gemini", action="store_true")
    args = parser.parse_args()

    payload = latest_payload(ACTIVITIES_DIR)
    inputs = prompt_inputs(payload)
    gemini_client = genai.Client() if args.gemini else None

    for label, path in PROMPT_FILES:
        prompt = render_prompt(path, inputs)
        print(f"=== {label} prompt ===")
        print(prompt)
        print(f"=== {label} description (ollama) ===")
        print(run_model(prompt))
        if gemini_client:
            print(f"=== {label} description (gemini) ===")
            try:
                print(run_gemini(prompt, gemini_client))
            except Exception as exc:
                print(f"gemini error: {exc}")


if __name__ == "__main__":
    main()
