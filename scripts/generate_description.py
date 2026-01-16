from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path


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


data_dir = Path("data")
activities_dir = data_dir / "activities"

payloads: list[tuple[datetime, dict]] = []
for path in activities_dir.glob("*.json"):
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    start_date = payload["activity"]["start_date"]
    payloads.append((parse_iso(start_date), payload))

latest_payload = max(payloads, key=lambda item: item[0])[1]

activity = latest_payload["activity"]["activity"]
weather = latest_payload["weather"][0]

distance_m = int(activity["distance"])
distance_km = distance_m / 1000
elapsed_time = int(activity["elapsed_time"])
moving_time = int(activity.get("moving_time", elapsed_time))

avg_pace = format_pace(moving_time / distance_km)
avg_hr = float(activity["average_heartrate"])

start_time_local = parse_iso(activity["start_date_local"])
start_time_local_str = start_time_local.strftime("%Y-%m-%d %H:%M")
time_of_day = time_of_day_description(start_time_local)

feels_like = float(weather["main_feels_like"])
weather_description = str(weather["weather_0_description"])

prompt_inputs = {
    "distance_m": distance_m,
    "distance_km": distance_km,
    "elapsed_time_formatted": format_duration(elapsed_time),
    "avg_pace_min_km": avg_pace,
    "avg_hr": avg_hr,
    "start_time_local": start_time_local_str,
    "time_of_day_description": time_of_day,
    "feels_like": feels_like,
    "weather_description": weather_description,
}

prompt_files = [
    ("story", Path("prompts/story_prompt.txt")),
    ("minimalist", Path("prompts/minimalist_prompt.txt")),
    ("scientific", Path("prompts/prompt_scientific.txt")),
    ("artist", Path("prompts/prompt_artist.txt")),
    ("athlete", Path("prompts/prompt_athlete.txt")),
]

for label, path in prompt_files:
    prompt_template = path.read_text(encoding="utf-8")
    prompt = prompt_template.format(**prompt_inputs)
    print(f"=== {label} prompt ===")
    print(prompt)
    print(f"=== {label} description ===")
    result = subprocess.run(
        ["ollama", "run", "mistral-nemo"],
        input=prompt,
        text=True,
        capture_output=True,
        check=True,
    )
    print(result.stdout.strip())
