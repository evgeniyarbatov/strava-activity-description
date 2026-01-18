from pathlib import Path

from scripts.utils import load_json, write_json


def test_load_json_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "payload.json"
    payload = {"alpha": 1, "beta": [2, 3]}

    write_json(path, payload)

    assert load_json(path) == payload
