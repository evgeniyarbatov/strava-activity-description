import importlib.util
import json
from pathlib import Path


class FakeTable:
    def __init__(self) -> None:
        self.items = []

    def put_item(self, Item):
        self.items.append(Item)


class FakeDynamo:
    def __init__(self, table: FakeTable) -> None:
        self.table = table
        self.table_name = None

    def Table(self, name: str):
        self.table_name = name
        return self.table


def load_lambda_module(monkeypatch, dynamo):
    monkeypatch.setenv("DYNAMODB_TABLE", "test-table")
    monkeypatch.setenv("TTL_DAYS", "1")
    monkeypatch.setenv("LATITUDE", "10")
    monkeypatch.setenv("LONGITUDE", "20")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "weather-key")
    monkeypatch.setenv("TOMTOM_API_KEY", "traffic-key")
    monkeypatch.setattr("boto3.resource", lambda *_args, **_kwargs: dynamo)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "terraform"
        / "lambda"
        / "lambda_function.py"
    )
    spec = importlib.util.spec_from_file_location("lambda_function_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_call_weather_api_returns_body(monkeypatch) -> None:
    table = FakeTable()
    dynamo = FakeDynamo(table)
    module = load_lambda_module(monkeypatch, dynamo)

    class FakeHTTP:
        def request(self, method, url):
            assert method == "GET"
            assert "lat=10" in url
            assert "lon=20" in url
            assert "appid=weather-key" in url
            return type("Resp", (), {"status": 200, "data": b"ok"})()

    monkeypatch.setattr(module.urllib3, "PoolManager", lambda: FakeHTTP())

    assert module.call_weather_api(10, 20) == "ok"


def test_call_traffic_api_encodes_point(monkeypatch) -> None:
    table = FakeTable()
    dynamo = FakeDynamo(table)
    module = load_lambda_module(monkeypatch, dynamo)

    captured = {}

    class FakeHTTP:
        def request(self, method, url):
            captured["url"] = url
            return type(
                "Resp",
                (),
                {
                    "status": 200,
                    "data": b"{\"flowSegmentData\": {\"currentSpeed\": 5}}",
                },
            )()

    monkeypatch.setattr(module.urllib3, "PoolManager", lambda: FakeHTTP())

    result = module.call_traffic_api("1, 2")

    assert "point=1%2C2" in captured["url"]
    assert "key=traffic-key" in captured["url"]
    assert result["flowSegmentData"]["currentSpeed"] == 5


def test_query_traffic_returns_none_when_missing_data(monkeypatch) -> None:
    table = FakeTable()
    dynamo = FakeDynamo(table)
    module = load_lambda_module(monkeypatch, dynamo)

    monkeypatch.setattr(module, "call_traffic_api", lambda _point: {})

    assert module.query_traffic("1,2") is None


def test_lambda_handler_stores_weather_and_traffic(monkeypatch) -> None:
    table = FakeTable()
    dynamo = FakeDynamo(table)
    module = load_lambda_module(monkeypatch, dynamo)

    monkeypatch.setattr(
        module,
        "call_weather_api",
        lambda _lat, _lon: json.dumps(
            {"main": {"feels_like": 12.3}, "weather": [{"description": "clear"}]}
        ),
    )
    monkeypatch.setattr(
        module,
        "query_traffic",
        lambda _point: {"currentSpeed": 10, "freeFlowSpeed": 20},
    )

    response = module.lambda_handler({}, None)

    assert response["statusCode"] == 200
    assert dynamo.table_name == "test-table"
    assert len(table.items) == 2
    assert {item["context"] for item in table.items} == {"weather", "traffic"}
