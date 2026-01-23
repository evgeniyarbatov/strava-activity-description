from __future__ import annotations

import os
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
import random

import boto3
from boto3.dynamodb.conditions import Key

from scripts.utils import load_json, parse_iso, write_json


DATA_DIR = Path("data")
ACTIVITIES_DIR = DATA_DIR / "activities"
DYNAMODB_TABLE = "strava-activity-context"


def filter_items_by_hour(
    items: list[dict], start_hour: int, end_hour: int
) -> list[dict]:
    items = [
        item
        for item in items
        if start_hour <= int(item["hour"]) <= end_hour
    ]
    items.sort(key=lambda item: int(item["hour"]))
    return items


def to_number(value: object) -> object:
    if isinstance(value, Decimal):
        return float(value)
    return value


import random

def feels_like_description(feels_like_c: float) -> str:
    if feels_like_c < 5:
        return random.choice([
            "bone-chilling, rare Hanoi frost",
            "shockingly frigid for Vietnam",
            "once-in-a-decade freezing",
            "arctic winds invading the tropics",
            "glacial morning paralyzing the city",
            "perishingly cold, unprecedented chill",
            "numbing frost gripping the capital",
            "mercilessly frozen, almost Siberian",
            "devastatingly icy, historic low"
        ])
    if feels_like_c < 10:
        return random.choice([
            "icy northern winds sweeping through",
            "teeth-chattering winter morning",
            "frosty like the highlands descended",
            "biting cold gripping the streets",
            "piercing chill cutting through layers",
            "razor-sharp winds slicing the air",
            "brutally frigid, exceptionally harsh",
            "savagely cold morning commute",
            "wickedly icy, unforgiving winter"
        ])
    if feels_like_c < 14:
        return random.choice([
            "proper Hanoi winter chill",
            "thick fog and bitter cold",
            "time for phở and winter coats",
            "brisk winds off the Red River",
            "crisp northern snap in the air",
            "penetrating dampness seeping everywhere",
            "raw, unrelenting winter bite",
            "dank coldness clinging stubbornly",
            "unforgivingly chilly, layers required",
            "blustery gusts whipping through",
            "austere winter conditions prevailing"
        ])
    if feels_like_c < 18:
        return random.choice([
            "crisp Old Quarter morning",
            "motorbike riders bundled up",
            "cool mist over Hoàn Kiếm Lake",
            "nippy breeze through the alleyways",
            "fresh winter air invigorating",
            "bracing coolness awakening the senses",
            "zippy chill energizing the morning",
            "tangy coolness nipping at exposed skin",
            "keen air sharpening your focus",
            "perky coldness requiring a scarf"
        ])
    if feels_like_c < 20:
        return random.choice([
            "refreshing dry season breeze",
            "light jacket weather around West Lake",
            "perfectly cool for a cà phê sữa đá",
            "agreeably mild morning commute",
            "comfortable chill tickling your skin",
            "snappy coolness, delightfully tolerable",
            "pleasingly crisp, neither hot nor cold",
            "mellowly cool, just right for exploring",
            "moderately fresh, ideal strolling weather",
            "gently brisk, satisfyingly temperate"
        ])
    if feels_like_c < 23:
        return random.choice([
            "delightfully comfortable Hanoi day",
            "ideal for strolling the French Quarter",
            "gentle sunshine, pleasant breeze",
            "splendidly temperate afternoon",
            "gloriously balanced climate",
            "wonderfully moderate and inviting",
            "blissfully agreeable conditions",
            "exquisitely mild, picture-perfect",
            "harmoniously pleasant atmosphere",
            "superbly comfortable, goldilocks zone",
            "serenely balanced, neither extreme",
            "divinely temperate, absolutely ideal"
        ])
    if feels_like_c < 26:
        return random.choice([
            "warm but lovely with the fan on",
            "perfect bánh mì on the sidewalk weather",
            "golden afternoon glow over the city",
            "summery warmth beginning to radiate",
            "toasty sunshine bathing the boulevards",
            "agreeably heated, bordering on balmy",
            "sun-kissed streets buzzing with life",
            "gently warming, approaching tropical",
            "pleasantly heated, comfortably sunny",
            "mellowly warm, invitingly bright",
            "benignly hot, still quite bearable"
        ])
    if feels_like_c < 29:
        return random.choice([
            "warming up, seek the shade",
            "balmy streets calling for iced tea",
            "typical tropical Hanoi heat building",
            "sultry air wrapping around you",
            "steamy atmosphere thickening",
            "languid heat settling in",
            "torrid conditions intensifying gradually",
            "increasingly heated, sweat appearing",
            "mounting warmth becoming noticeable",
            "escalating heat demanding attention",
            "progressively muggy, fans spinning"
        ])
    if feels_like_c < 32:
        return random.choice([
            "seriously hot, summer has arrived",
            "sidewalk vendors' parasols essential",
            "sweating through the afternoon heat",
            "blistering sun beating down relentlessly",
            "fierce tropical heat radiating upward",
            "searing warmth testing your endurance",
            "baking pavement shimmering with heat",
            "roasting temperatures cooking the streets",
            "flaming hot, shade desperately needed",
            "grilling sunshine pounding mercilessly",
            "incandescent heat waves rising visibly",
            "red-hot conditions draining energy"
        ])
    if feels_like_c < 35:
        return random.choice([
            "oppressively humid, clothes sticking",
            "thick summer air you can almost drink",
            "everyone seeking air conditioning",
            "suffocating moisture saturating everything",
            "stifling humidity smothering the city",
            "cloying wetness hanging heavy",
            "drenching mugginess enveloping all",
            "claustrophobic heat wrapping tightly",
            "asphyxiating humidity choking the air",
            "viscous atmosphere clinging relentlessly",
            "strangling moisture overwhelming senses"
        ])
    return random.choice([
        "scorching monsoon intensity",
        "blazing tropical furnace",
        "absolutely sweltering, stay hydrated!",
        "infernal heat radiating mercilessly",
        "punishing sauna-like conditions",
        "broiling temperatures roasting everything",
        "withering heat wave crushing the city",
        "apocalyptic temperatures melting resolve",
        "volcanic heat overwhelming the capital",
        "tyrannical sun dominating without mercy",
        "excruciating furnace-like atmosphere",
        "incinerating conditions, survival mode",
        "molten air, dangerously extreme heat"
    ])


def traffic_description(speed_ratio: float) -> str:
    if speed_ratio <= 0.25:
        return random.choice([
            "complete standstill, motorbikes frozen",
            "absolute gridlock paralysis",
            "total traffic apocalypse",
            "utterly immobilized chaos",
            "hopelessly jammed, zero movement",
            "catastrophically stuck everywhere",
            "nightmarish parking lot situation",
            "exhaustingly stationary madness",
            "frustratingly cemented in place",
            "monumentally congested hell",
            "suffocatingly trapped, going nowhere",
            "desperately stagnant gridlock"
        ])
    if speed_ratio <= 0.4:
        return random.choice([
            "severe gridlock choking the streets",
            "brutal congestion everywhere",
            "mercilessly jammed citywide",
            "agonizingly slow gridlock",
            "punishingly dense traffic",
            "oppressively packed roads",
            "claustrophobic sea of vehicles",
            "stifling wall-to-wall congestion",
            "crushingly heavy gridlock",
            "exasperatingly clogged arteries",
            "suffocating mass of motorbikes",
            "relentlessly packed streets"
        ])
    if speed_ratio <= 0.55:
        return random.choice([
            "crawling at snail's pace",
            "inching forward painfully",
            "barely moving, extreme patience required",
            "creeping along grudgingly",
            "sluggishly advancing inch by inch",
            "tediously slow-motion traffic",
            "maddeningly gradual progress",
            "torturously crawling forward",
            "glacially slow movement",
            "laboriously inching through chaos",
            "ploddingly slow, testing patience",
            "excruciatingly sluggish flow"
        ])
    if speed_ratio <= 0.7:
        return random.choice([
            "slow but steady movement",
            "heavily congested, stop-and-go",
            "frustratingly sluggish pace",
            "annoyingly slow progress",
            "moderately jammed, patience needed",
            "tiringly slow downtown crawl",
            "wearisome stop-start rhythm",
            "dragging along reluctantly",
            "laboriously progressing forward",
            "vexingly slow city navigation",
            "unhurried but congested flow"
        ])
    if speed_ratio <= 0.85:
        return random.choice([
            "busy but moving steadily",
            "typical Hanoi hustle and bustle",
            "active flow with minor delays",
            "moderately crowded streets",
            "brisk traffic with occasional slowdowns",
            "energetically bustling roads",
            "dynamically flowing chaos",
            "vibrantly packed but progressing",
            "lively stream of vehicles",
            "spiritedly moving crowds",
            "animated traffic dance",
            "pulsating urban flow"
        ])
    if speed_ratio <= 0.95:
        return random.choice([
            "steady predictable flow",
            "consistent comfortable pace",
            "reliable smooth movement",
            "dependably even traffic",
            "rhythmically flowing well",
            "harmoniously balanced flow",
            "pleasantly uninterrupted progress",
            "satisfyingly regular pace",
            "agreeably smooth navigation",
            "calmly flowing traffic",
            "reassuringly steady movement"
        ])
    if speed_ratio <= 1.05:
        return random.choice([
            "smooth sailing through streets",
            "effortlessly flowing traffic",
            "gloriously clear roads",
            "delightfully open conditions",
            "wonderfully smooth cruising",
            "blissfully unimpeded flow",
            "serenely easy navigation",
            "peacefully flowing streets",
            "tranquilly smooth movement",
            "gracefully gliding through",
            "splendidly clear passage",
            "beautifully fluid traffic"
        ])
    return random.choice([
        "wide open roads, rare sight!",
        "completely clear, speed freely",
        "gloriously empty streets",
        "astonishingly open highways",
        "miraculously clear Hanoi roads",
        "unbelievably vacant, enjoy it!",
        "extraordinarily empty, perfect conditions",
        "stunningly clear, once-in-a-lifetime",
        "magically deserted streets",
        "phenomenally open, no obstacles",
        "impossibly clear for Hanoi",
        "spectacularly vacant roadways",
        "breathtakingly empty, savor this!"
    ])


def build_weather_entries(items: list[dict]) -> list[dict]:
    return [
        {
            "description": item["data"]["weather_description"],
            "feels_like": feels_like_description(
                float(to_number(item["data"]["feels_like"]))
            ),
        }
        for item in items
    ]


def build_traffic_entries(items: list[dict]) -> list[dict]:
    return [
        {
            "description": traffic_description(
                float(to_number(item["data"]["currentSpeed"]))
                / float(to_number(item["data"]["freeFlowSpeed"]))
            ),
        }
        for item in items
    ]


def query_context_items(table, context: str, date: str) -> list[dict]:
    response = table.query(
        KeyConditionExpression=Key("context").eq(context) & Key("date").eq(date)
    )
    return response.get("Items", [])


def main() -> None:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(DYNAMODB_TABLE)
    for activity_path in sorted(ACTIVITIES_DIR.glob("*.json")):
        payload = load_json(activity_path)
        if "weather" in payload and "traffic" in payload:
            continue
        activity = payload["activity"]
        start_time = parse_iso(activity["start_date_local"])
        end_time = (
            start_time
            + timedelta(seconds=activity["moving_time"])
            + timedelta(hours=1)
        )
        date = start_time.date().isoformat()
        start_hour = start_time.hour
        end_hour = end_time.hour

        if "weather" not in payload:
            weather_items = query_context_items(table, "weather", date)
            weather_during_activity = filter_items_by_hour(
                weather_items, start_hour, end_hour
            )
            payload["weather"] = build_weather_entries(weather_during_activity)

        if "traffic" not in payload:
            traffic_items = query_context_items(table, "traffic", date)
            traffic_during_activity = filter_items_by_hour(
                traffic_items, start_hour, end_hour
            )
            payload["traffic"] = build_traffic_entries(traffic_during_activity)

        write_json(activity_path, payload)


if __name__ == "__main__":
    main()
