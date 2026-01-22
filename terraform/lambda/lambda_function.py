import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import boto3
import urllib3

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
TTL_DAYS = int(os.environ["TTL_DAYS"])

LAT = os.environ["LATITUDE"]
LON = os.environ["LONGITUDE"]

OPENWEATHER_API_KEY = os.environ["OPENWEATHER_API_KEY"]
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

dynamodb = boto3.resource("dynamodb")

def call_weather_api(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    http = urllib3.PoolManager()
    query_params = urlencode(params)
    try:
        response = http.request("GET", f"{WEATHER_BASE_URL}?{query_params}")
        if response.status != 200:
            print(f"API call failed with status {response.status}")
            return None
        return response.data.decode("utf-8")
    except Exception as exc:
        print(f"Error calling API: {exc}")
        return None

def lambda_handler(event, context):
    table = dynamodb.Table(DYNAMODB_TABLE)

    try:
        lat = float(LAT)
        lon = float(LON)

        api_response = call_weather_api(lat, lon)
        if api_response is None:
            raise Exception("Failed to get weather data from API")

        weather_json = json.loads(api_response)

        current_time = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        date = current_time.date().isoformat()
        ttl = int((current_time + timedelta(days=TTL_DAYS)).timestamp())

        feels_like = Decimal(str(weather_json["main"]["feels_like"]))
        weather_description = weather_json["weather"][0]["description"]

        item = {
            "ttl": ttl,
            "context": "weather",
            "date": date,
            "feels_like": feels_like,
            "weather_description": weather_description,
        }

        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Weather data stored successfully",
                }
            ),
        }

    except Exception as exc:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(exc)}),
        }
