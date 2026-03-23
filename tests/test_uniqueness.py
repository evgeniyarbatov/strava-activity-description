import json

import polyline

from scripts import uniqueness


def test_main_skips_existing_uniqueness(tmp_path, monkeypatch) -> None:
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()

    existing_payload = {
        "id": "1",
        "map": {
            "polyline": polyline.encode([(0.0, 0.0), (0.0, 0.01), (0.01, 0.01)]),
        },
        "distance": 1000,
        "uniqueness": {"description": "existing"},
    }
    new_payload = {
        "id": "2",
        "map": {
            "polyline": polyline.encode([(0.0, 0.0), (0.0, 0.02), (0.02, 0.02)]),
        },
        "distance": 1200,
    }

    existing_path = activities_dir / "1.json"
    new_path = activities_dir / "2.json"
    existing_path.write_text(json.dumps(existing_payload), encoding="utf-8")
    new_path.write_text(json.dumps(new_payload), encoding="utf-8")

    monkeypatch.setattr(uniqueness, "ACTIVITIES_DIR", activities_dir)

    original_text = existing_path.read_text(encoding="utf-8")

    uniqueness.main()

    assert existing_path.read_text(encoding="utf-8") == original_text
    updated_new = json.loads(new_path.read_text(encoding="utf-8"))
    assert "uniqueness" in updated_new
    assert "description" in updated_new["uniqueness"]
