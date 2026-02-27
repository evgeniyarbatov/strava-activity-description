from __future__ import annotations

import os
import random
import subprocess
from pathlib import Path

import ollama
import polyline
from geopy.geocoders import Nominatim

from scripts.utils import load_env, load_json, parse_iso

load_env(Path("api-keys/ollama.env"))

OLLAMA_CLOUD_MODELS = [
    "gemini-3-flash-preview"
]
OLLAMA_CLOUD_HOST = "https://api.ollama.com"
OLLAMA_MODELS = [
    *OLLAMA_CLOUD_MODELS,
    "mistral-nemo",
    "gemma3",
    "qwen2.5",
]

DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
DESCRIPTIONS_DIR = DATA_DIR / "descriptions"
PROMPTS_DIR = Path("prompts")
PROMPT_FILES = [
    (path.stem, path) for path in sorted(PROMPTS_DIR.glob("*.txt"), key=lambda path: path.name)
]
ACTIVITY_CONTEXT_PATH = PROMPTS_DIR / "common" / "activity-context.txt"
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
    return f"{prompt}\n\nVARIATION\n\n{variation}"


def run_ollama_local(prompt: str, model: str) -> str:
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()

def run_ollama_cloud(prompt: str, model: str) -> str:
    api_key = os.getenv("OLLAMA_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        raise ValueError("Missing Ollama API key in api-keys/ollama.env.")
    client = ollama.Client(
        host=OLLAMA_CLOUD_HOST,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    result = client.generate(model=model, prompt=prompt)
    return result.response.strip()


def run_model(prompt: str, model: str) -> str:
    if model in OLLAMA_CLOUD_MODELS:
        return run_ollama_cloud(prompt, model)
    return run_ollama_local(prompt, model)


def build_markdown(activity_id: str, inputs: dict) -> str:
    lines = [f"# {activity_id}", ""]
    for label, path in PROMPT_FILES:
        prompt = render_prompt(path, inputs)
        # print(prompt)
        lines.append(f"## {label}")
        for model in OLLAMA_MODELS:
            ollama_output = run_model(prompt, model)
            print(f"{label} - {model}")
            print(ollama_output)
            lines.append(f"### {model}")
            lines.append(ollama_output)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    for activity_path in sorted(ACTIVITIES_DIR.glob("*.json")):
        activity_id = activity_path.stem
        output_path = DESCRIPTIONS_DIR / f"{activity_id}.md"
        if output_path.exists():
            continue
        payload = load_json(activity_path)
        inputs = prompt_inputs(payload)
        output_path.write_text(
            build_markdown(activity_id, inputs),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
