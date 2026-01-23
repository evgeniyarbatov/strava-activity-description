from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path

from scripts.utils import load_json, parse_iso, write_json

DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
GOALS_PATH = Path("goals.json")

DISTANCE_WORDS = [
    "minuscule",
    "tiny",
    "petite",
    "brief",
    "short",
    "compact",
    "modest",
    "fair",
    "moderate",
    "respectable",
    "substantial",
    "solid",
    "lengthy",
    "considerable",
    "extensive",
    "ambitious",
    "massive",
    "monumental",
    "colossal",
    "epic",
    "gargantuan",
    "heroic",
    "legendary",
    "ultra",
]

MOVING_TIME_WORDS = [
    "fleeting",
    "swift",
    "quick",
    "nippy",
    "brisk",
    "expeditious",
    "efficient",
    "moderate",
    "steady",
    "sustained",
    "prolonged",
    "extended",
    "lengthy",
    "protracted",
    "arduous",
    "drawn-out",
    "grueling",
    "grinding",
    "marathon",
    "exhausting",
    "punishing",
    "epic",
    "all-consuming",
    "never-ending",
]

GOAL_FIELDS = [
    ("distance", DISTANCE_WORDS),
    ("moving_time", MOVING_TIME_WORDS),
]

DEEP_NIGHT = [
    "the witching hour", "deep night", "the small hours", "darkest night",
    "midnight's embrace", "the dead of night", "moonlit silence", "owl hours",
    "star-watching time", "the velvet darkness", "sleeping world", "lunar hours",
    "shadow time", "the silent deep", "night's heart", "moon's domain",
    "the hushed hours", "cosmic silence", "dreamtime", "the void hours",
    "midnight oil time", "the quietest hours", "pitch black", "nocturnal realm",
]

DAWN = [
    "crack of dawn", "first light", "sunrise", "early morning",
    "daybreak", "dawn's glow", "the rooster hour", "pre-sunrise",
    "the breaking dawn", "morning's birth", "twilight's end", "the awakening",
    "eastern light", "fresh dawn", "new day's start", "cockcrow",
    "aurora", "the blue hour fades", "sun's arrival", "morning star time",
    "the yawning world", "dew-kissed morning", "the eastern glow", "dawn patrol",
    "sunrise symphony", "the world stirring", "birds' chorus", "misty morning",
]

MORNING = [
    "morning", "mid-morning", "late morning", "the bright morning",
    "forenoon", "morning sunshine", "coffee time", "the productive hours",
    "sun-bright morning", "rush hour aftermath", "morning hustle", "AM prime",
    "breakfast aftermath", "the working morning", "morning bloom", "daylight's climb",
    "fresh hours", "morning vigor", "the energetic hours", "morning momentum",
    "sun's ascent", "the bustling morning", "clear morning", "morning activity",
    "the crisp hours", "vibrant morning", "morning peak", "sun-drenched hours",
]

MIDDAY = [
    "midday", "high noon", "lunch hour", "noon's peak",
    "the sun's zenith", "bright afternoon", "noontime", "meridian",
    "the height of day", "solar maximum", "lunch break", "noon sharp",
    "the blazing hour", "peak daylight", "the overhead sun", "full brightness",
    "day's climax", "the scorching hour", "lunch o'clock", "the brilliant hour",
    "zenith time", "sun directly above", "the hottest hour", "maximal light",
]

AFTERNOON = [
    "afternoon", "mid-afternoon", "late afternoon", "the golden hours",
    "post-lunch", "siesta time", "the lazy afternoon", "afternoon warmth",
    "the drowsy hours", "PM hours", "the slow afternoon", "lengthening shadows",
    "tea time", "the waning sun", "afternoon lull", "the mellow hours",
    "coffee break time", "slanting light", "the amber hours", "warm afternoon",
    "the peaceful hours", "afternoon glow", "the quiet productivity", "sun's descent begins",
    "the contemplative hours", "afternoon drift", "the golden light", "easygoing hours",
]

EARLY_EVENING = [
    "early evening", "dusk", "twilight", "the golden hour",
    "sunset", "sundown", "day's end", "the gloaming",
    "eventide", "the magic hour", "sunset glow", "the dimming",
    "twilight zone", "the orange hour", "day's farewell", "vespers",
    "the transition hour", "dusky time", "purple hour", "sun's goodbye",
    "the softening light", "evening's arrival", "the mellowing", "sundown spectacle",
    "the photographer's hour", "crimson sky time", "fading daylight", "dusk's embrace",
]

EVENING = [
    "evening", "nightfall", "early night", "the blue hour",
    "prime time", "dinner hour", "settling darkness", "the quiet evening",
    "after dark", "lamplight hour", "the cooling hours", "evening calm",
    "night's descent", "the peaceful evening", "TV hour", "the winding down",
    "stars emerging", "the relaxing hours", "evening chill", "the cozy hours",
    "night's beginning", "the restful time", "moon's rise", "evening repose",
    "the gathering dark", "dinner time", "family hour", "the settling in",
]

LATE_NIGHT = [
    "late night", "near midnight", "the late hours", "bedtime",
    "the night deepens", "approaching midnight", "night owl time", "the waning day",
    "late evening", "the final hours", "closing time", "the day's last breath",
    "pre-midnight", "the sleepy hours", "the winding down", "late shift",
    "the settling night", "last call", "the drowsy hours", "evening's end",
    "the dark hours", "night's depth", "the calm before midnight", "the quiet night",
]


def time_of_day_description(start_time: datetime) -> str:
    """
    Returns a random creative description of the time of day.
    Each call may return a different description for the same time.
    """
    hour = start_time.hour

    # 12 AM - 4 AM: Deep night
    if 0 <= hour < 5:
        return random.choice(DEEP_NIGHT)

    # 5 AM - 7 AM: Dawn
    if 5 <= hour < 8:
        return random.choice(DAWN)

    # 8 AM - 11 AM: Morning
    if 8 <= hour < 12:
        return random.choice(MORNING)

    # 12 PM - 2 PM: Midday
    if 12 <= hour < 14:
        return random.choice(MIDDAY)

    # 2 PM - 5 PM: Afternoon
    if 14 <= hour < 17:
        return random.choice(AFTERNOON)

    # 5 PM - 7 PM: Early evening
    if 17 <= hour < 19:
        return random.choice(EARLY_EVENING)

    # 7 PM - 10 PM: Evening
    if 19 <= hour < 22:
        return random.choice(EVENING)

    # 10 PM - 12 AM: Late night
    return random.choice(LATE_NIGHT)


def describe_goal(value: float, goal: float, words: list[str]) -> str:
    ratio = value / goal
    index = min(len(words) - 1, int(ratio * (len(words) - 1)))
    return words[index]


def build_context(activity: dict, goals: dict[str, float]) -> dict:
    context: dict[str, str] = {}
    for field, words in GOAL_FIELDS:
        value = activity.get(field)
        goal = goals.get(field)
        if not isinstance(value, (int, float)) or not isinstance(goal, (int, float)):
            continue
        context[field] = describe_goal(float(value), float(goal), words)
    start_time = activity.get("start_date_local")
    if isinstance(start_time, str):
        context["time_of_day_description"] = time_of_day_description(parse_iso(start_time))
    return context


def main() -> None:
    goals = load_json(GOALS_PATH)
    activity_paths = sorted(ACTIVITIES_DIR.glob("*.json"))
    for path in activity_paths:
        payload = load_json(path)
        activity = payload.get("activity") or {}
        payload["activity_context"] = build_context(activity, goals)
        write_json(path, payload)


if __name__ == "__main__":
    main()
