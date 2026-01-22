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
TOMTOM_API_KEY = os.environ["TOMTOM_API_KEY"]

dynamodb = boto3.resource("dynamodb")

def call_weather_api(lat, lon):
    http = urllib3.PoolManager()

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    query_params = urlencode(params)

    response = http.request("GET", f"{url}?{query_params}")
    if response.status != 200:
        return None

    return response.data.decode("utf-8")


def call_traffic_api(point):
    http = urllib3.PoolManager()

    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/22/json"
    params = {
        "key": TOMTOM_API_KEY,
        "point": point.replace(" ", ""),
    }
    query_params = urllib3.request.urlencode(params)

    response = http.request("GET", f"{url}?{query_params}")
    if response.status != 200:
        return None

    return json.loads(response.data.decode("utf-8"))

def query_traffic(point):
    result = call_traffic_api(point)
    if result is None or "flowSegmentData" not in result:
        return None

    flow_data = result["flowSegmentData"]

    return {
        "currentSpeed": flow_data.get("currentSpeed", None),
        "freeFlowSpeed": flow_data.get("freeFlowSpeed", None),
    }

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

        weather_item = {
            "ttl": ttl,
            "context": "weather",
            "date": date,
            "data": {
                "feels_like": feels_like,
                "weather_description": weather_description,
            }
        }
        table.put_item(Item=weather_item)

        traffic = query_traffic(f"{lat},{lon}")
        if traffic is None:
            raise Exception("Failed to get traffic data from API")

        traffic_item = {
            "ttl": ttl,
            "context": "traffic",
            "date": date,
            "data": {
                "currentSpeed": Decimal(str(traffic["currentSpeed"])),
                "freeFlowSpeed": Decimal(str(traffic["freeFlowSpeed"])),
            }
        }
        table.put_item(Item=traffic_item)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Weather and traffic data stored successfully",
                }
            ),
        }

    except Exception as exc:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(exc)}),
        }
