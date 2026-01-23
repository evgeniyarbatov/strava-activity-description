from __future__ import annotations

import random
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

import polyline
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from google import genai

from scripts.utils import load_json, parse_iso
from datetime import datetime


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
    "traffic_description"
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
    """
    Returns a random creative description of the time of day.
    Each call may return a different description for the same time.
    """
    hour = start_time.hour

    # 12 AM - 4 AM: Deep night
    if 0 <= hour < 5:
        return random.choice([
            "the witching hour", "deep night", "the small hours", "darkest night",
            "midnight's embrace", "the dead of night", "moonlit silence", "owl hours",
            "star-watching time", "the velvet darkness", "sleeping world", "lunar hours",
            "shadow time", "the silent deep", "night's heart", "moon's domain",
            "the hushed hours", "cosmic silence", "dreamtime", "the void hours",
            "midnight oil time", "the quietest hours", "pitch black", "nocturnal realm"
        ])

    # 5 AM - 7 AM: Dawn
    elif 5 <= hour < 8:
        return random.choice([
            "crack of dawn", "first light", "sunrise", "early morning",
            "daybreak", "dawn's glow", "the rooster hour", "pre-sunrise",
            "the breaking dawn", "morning's birth", "twilight's end", "the awakening",
            "eastern light", "fresh dawn", "new day's start", "cockcrow",
            "aurora", "the blue hour fades", "sun's arrival", "morning star time",
            "the yawning world", "dew-kissed morning", "the eastern glow", "dawn patrol",
            "sunrise symphony", "the world stirring", "birds' chorus", "misty morning"
        ])

    # 8 AM - 11 AM: Morning
    elif 8 <= hour < 12:
        return random.choice([
            "morning", "mid-morning", "late morning", "the bright morning",
            "forenoon", "morning sunshine", "coffee time", "the productive hours",
            "sun-bright morning", "rush hour aftermath", "morning hustle", "AM prime",
            "breakfast aftermath", "the working morning", "morning bloom", "daylight's climb",
            "fresh hours", "morning vigor", "the energetic hours", "morning momentum",
            "sun's ascent", "the bustling morning", "clear morning", "morning activity",
            "the crisp hours", "vibrant morning", "morning peak", "sun-drenched hours"
        ])

    # 12 PM - 2 PM: Midday
    elif 12 <= hour < 14:
        return random.choice([
            "midday", "high noon", "lunch hour", "noon's peak",
            "the sun's zenith", "bright afternoon", "noontime", "meridian",
            "the height of day", "solar maximum", "lunch break", "noon sharp",
            "the blazing hour", "peak daylight", "the overhead sun", "full brightness",
            "day's climax", "the scorching hour", "lunch o'clock", "the brilliant hour",
            "zenith time", "sun directly above", "the hottest hour", "maximal light"
        ])

    # 2 PM - 5 PM: Afternoon
    elif 14 <= hour < 17:
        return random.choice([
            "afternoon", "mid-afternoon", "late afternoon", "the golden hours",
            "post-lunch", "siesta time", "the lazy afternoon", "afternoon warmth",
            "the drowsy hours", "PM hours", "the slow afternoon", "lengthening shadows",
            "tea time", "the waning sun", "afternoon lull", "the mellow hours",
            "coffee break time", "slanting light", "the amber hours", "warm afternoon",
            "the peaceful hours", "afternoon glow", "the quiet productivity", "sun's descent begins",
            "the contemplative hours", "afternoon drift", "the golden light", "easygoing hours"
        ])

    # 5 PM - 7 PM: Early evening
    elif 17 <= hour < 19:
        return random.choice([
            "early evening", "dusk", "twilight", "the golden hour",
            "sunset", "sundown", "day's end", "the gloaming",
            "eventide", "the magic hour", "sunset glow", "the dimming",
            "twilight zone", "the orange hour", "day's farewell", "vespers",
            "the transition hour", "dusky time", "purple hour", "sun's goodbye",
            "the softening light", "evening's arrival", "the mellowing", "sundown spectacle",
            "the photographer's hour", "crimson sky time", "fading daylight", "dusk's embrace"
        ])

    # 7 PM - 10 PM: Evening
    elif 19 <= hour < 22:
        return random.choice([
            "evening", "nightfall", "early night", "the blue hour",
            "prime time", "dinner hour", "settling darkness", "the quiet evening",
            "after dark", "lamplight hour", "the cooling hours", "evening calm",
            "night's descent", "the peaceful evening", "TV hour", "the winding down",
            "stars emerging", "the relaxing hours", "evening chill", "the cozy hours",
            "night's beginning", "the restful time", "moon's rise", "evening repose",
            "the gathering dark", "dinner time", "family hour", "the settling in"
        ])

    # 10 PM - 12 AM: Late night
    else:
        return random.choice([
            "late night", "near midnight", "the late hours", "bedtime",
            "the night deepens", "approaching midnight", "night owl time", "the waning day",
            "late evening", "the final hours", "closing time", "the day's last breath",
            "pre-midnight", "the sleepy hours", "the winding down", "late shift",
            "the settling night", "last call", "the drowsy hours", "evening's end",
            "the dark hours", "night's depth", "the calm before midnight", "the quiet night"
        ])


def activity_summary(
    activity: dict,
    weather_entries: list[dict],
    traffic_entries: list[dict],
) -> dict:
    start_time_local = parse_iso(activity["start_date_local"])
    start_time_local_str = start_time_local.strftime("%Y-%m-%d %H:%M")
    time_of_day = time_of_day_description(start_time_local)

    feels_like_values = [str(entry["feels_like"]) for entry in weather_entries]
    feels_like = max(feels_like_values, key=feels_like_values.count)
    weather_description = ", ".join(
        str(entry["description"]) for entry in weather_entries
    )

    traffic_description = ", ".join(
        str(entry["description"]) for entry in traffic_entries
    )

    return {
        "start_time_local": start_time_local_str,
        "time_of_day_description": time_of_day,
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


def build_markdown(
    activity_id: str,
    inputs: dict,
    gemini_client: genai.Client | None,
) -> str:
    lines = [f"# {activity_id}", ""]
    for label, path in PROMPT_FILES:
        prompt = render_prompt(path, inputs)
        ollama_output = run_model(prompt)
        print(label)
        print(ollama_output)
        lines.append(f"## {label}")
        lines.append("### ollama")
        lines.append(ollama_output)
        if gemini_client:
            try:
                result = run_gemini(prompt, gemini_client)
                lines.append("### gemini")
                print(result)
                lines.append(result)
            except Exception as exc:
                continue

        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--gemini", action="store_true")
    args = parser.parse_args()

    gemini_client = genai.Client() if args.gemini else None
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
