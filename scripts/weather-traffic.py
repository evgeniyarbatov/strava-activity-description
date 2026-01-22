from __future__ import annotations

import os
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

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


def build_weather_entries(items: list[dict]) -> list[dict]:
    return [
        {
            "weather_description": item["data"]["weather_description"],
            "main_feels_like": to_number(item["data"]["feels_like"]),
        }
        for item in items
    ]


def build_traffic_entries(items: list[dict]) -> list[dict]:
    return [
        {
            "currentSpeed": to_number(item["data"]["currentSpeed"]),
            "freeFlowSpeed": to_number(item["data"]["freeFlowSpeed"]),
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
        end_time = start_time + timedelta(seconds=activity["moving_time"])
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
