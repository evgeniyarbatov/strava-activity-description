from __future__ import annotations

import random
import runpy
import subprocess
from pathlib import Path

import polyline
from geopy.geocoders import Nominatim
from google import genai

from scripts.utils import load_json, parse_iso

api_secrets = Path.home() / "gitRepo" / "api-secrets"
env_loader = api_secrets / "scripts" / "env_loader.py"
load_env = runpy.run_path(env_loader)["load_env"]

load_env(api_secrets / "gemini.env")

DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
DESCRIPTIONS_DIR = DATA_DIR / "descriptions"
PROMPTS_DIR = Path("prompts")
PROMPT_FILES = [
    (path.stem, path) for path in sorted(PROMPTS_DIR.glob("*.txt"), key=lambda path: path.name)
]
ACTIVITY_CONTEXT_PATH = PROMPTS_DIR / "common" / "activity-context.txt"
GEMINI_MODEL = "gemini-2.5-flash"
PROMPT_INPUT_KEYS = [
    "distance_context",
    "moving_time_context",
    "start_time_local",
    "time_of_day_description",
    "feels_like",
    "weather_description",
    "city_name",
    "country",
    "uniqueness_description",
    "traffic_description",
    "points_of_interest",
]
VARIATION_PROMPTS = [
    # Sensory & Perceptual
    "Lean on a single vivid sensory detail (sound, smell, or texture).",
    "Name one color or quality of light.",
    "Use one unusual verb to describe movement or air.",
    "Let a single sound anchor the whole scene.",
    "Name one smell that defines the moment.",
    "Notice one texture underfoot or against skin.",
    "Let temperature be the dominant sensation.",
    "Focus on breath — its rhythm, weight, or quality.",

    # Compositional & Structural
    "Frame the moment as a snapshot rather than a sequence.",
    "Include one brief, unexpected metaphor rooted in the surroundings.",
    "Let a small contrast shape the sentence (calm body, busy street).",
    "Build the sentence around a single object noticed in passing.",
    "Open with the environment, close with the body.",
    "Open with the body, close with the environment.",
    "Use juxtaposition between effort and stillness.",
    "Let the sentence turn on a single conjunction — but, yet, while.",

    # Temporal & Mood
    "Capture the feeling of a specific moment mid-run, not the whole.",
    "Suggest time of day without naming it directly.",
    "Evoke the mood of transition — beginning settling into rhythm.",
    "Let the city feel like it's waking up, winding down, or indifferent.",
    "Imply weather through its effect on the body, not its name.",
    "Convey effort as something almost forgotten rather than felt.",
    "Suggest the run is already over before it fully began.",

    # Voice & Distance
    "Write as if observing yourself from just outside your body.",
    "Be the last person noticing you as you pass.",
    "Let the surroundings be indifferent to the run entirely.",
    "Write as if describing a photograph taken mid-stride.",
    "Adopt the distance of a painter noting a small figure in a landscape.",
    "Make the city a character with no awareness of you.",

    # Constraint-based
    "Use no adjectives — carry everything with verbs and nouns.",
    "Use exactly one adjective. Make it count.",
    "Avoid any word that could appear in a fitness app.",
    "Say nothing about speed, distance, or time — only sensation.",
    "Let silence or absence be the defining quality.",
    "End on an image, not a feeling.",
]
GEMINI_TEMPERATURE_RANGE = (0.9, 1.3)
GEMINI_TOP_P_RANGE = (0.85, 0.98)

def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def format_pace(seconds_per_km: float) -> str:
    total_seconds = int(round(seconds_per_km))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes}:{secs:02d}"


def activity_summary(
    activity: dict,
    weather_entries: list[dict],
    traffic_entries: list[dict],
) -> dict:
    start_time_local = parse_iso(activity["start_date_local"])
    start_time_local_str = start_time_local.strftime("%Y-%m-%d %H:%M")

    feels_like_values = [str(entry["feels_like"]) for entry in weather_entries]
    feels_like = ""
    if feels_like_values:
        feels_like = max(feels_like_values, key=feels_like_values.count)
    weather_description = ", ".join(
        dict.fromkeys(str(entry["description"]) for entry in weather_entries)
    )

    traffic_description = ", ".join(
        dict.fromkeys(str(entry["description"]) for entry in traffic_entries)
    )

    return {
        "start_time_local": start_time_local_str,
        "feels_like": feels_like,
        "weather_description": weather_description,
        "traffic_description": traffic_description,
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
    traffic_entries = payload["traffic"]
    summary = activity_summary(activity, weather_entries, traffic_entries)
    activity_context = payload["activity_context"]
    points_of_interest = ", ".join(payload["geo"]["points_of_interest"])

    # Reverse geocode the midpoint of the route for location context.
    geolocator = Nominatim(user_agent="strava-activity-description")
    city, country = location_from_polyline(activity["map"]["polyline"], geolocator)

    uniqueness_description = payload["uniqueness"]["description"]
    time_of_day = activity_context["time_of_day_description"]
    summary.update(
        {
            "distance_context": activity_context["distance"],
            "moving_time_context": activity_context["moving_time"],
            "city_name": city,
            "country": country,
            "uniqueness_description": uniqueness_description,
            "time_of_day_description": time_of_day,
            "points_of_interest": points_of_interest,
        }
    )
    return summary


def render_prompt(template_path: Path, inputs: dict) -> str:
    prompt_template = template_path.read_text(encoding="utf-8")
    activity_context_template = ACTIVITY_CONTEXT_PATH.read_text(encoding="utf-8")
    activity_context = activity_context_template.format(**inputs)
    prompt = prompt_template.format(**inputs, activity_context=activity_context)
    variation = random.choice(VARIATION_PROMPTS)
    return f"{prompt}\n\nVARIATION\n{variation}"


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
    config = genai.types.GenerateContentConfig(
        temperature=random.uniform(*GEMINI_TEMPERATURE_RANGE),
        top_p=random.uniform(*GEMINI_TOP_P_RANGE),
    )
    result = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=config)
    return result.text.strip()


def build_markdown(activity_id: str, inputs: dict, gemini_client: genai.Client) -> str:
    lines = [f"# {activity_id}", ""]
    for label, path in PROMPT_FILES:
        prompt = render_prompt(path, inputs)
        # print(prompt)
        ollama_output = run_model(prompt)
        print(label)
        print(ollama_output)
        lines.append(f"## {label}")
        lines.append("### ollama")
        lines.append(ollama_output)
        result = run_gemini(prompt, gemini_client)
        lines.append("### gemini")
        print(result)
        lines.append(result)

        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    gemini_client = genai.Client()
    for activity_path in sorted(ACTIVITIES_DIR.glob("*.json")):
        activity_id = activity_path.stem
        output_path = DESCRIPTIONS_DIR / f"{activity_id}.md"
        if output_path.exists():
            continue
        payload = load_json(activity_path)
        inputs = prompt_inputs(payload)
        output_path.write_text(
            build_markdown(activity_id, inputs, gemini_client),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
