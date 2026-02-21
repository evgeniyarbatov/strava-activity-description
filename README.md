# Strava Activity Description

Generate short Strava activity descriptions from run polylines, weather, traffic, and prior history. The core Python entry points live in `scripts/` (see `scripts/merge.py`, `scripts/context.py`, and `scripts/describe.py`).

## Steps

Add GPX and TCX to `data/raw`

Run `make analyze` to merge GPX/TCX, to get context and weather / traffic data.

`make describe` to generate the descriptions.

## Update

`make test` to run tests

`make deploy` to update Lambda

## Scripts

`scripts/merge.py` merges TCX cadence/heart-rate samples into GPX tracks from `data/raw` and writes merged GPX files to `data/gpx`.

`scripts/activity.py` parses merged GPX tracks into activity JSON with distance, moving time, and an encoded polyline in `data/activities`.

`scripts/weather_traffic.py` enriches activity JSON by pulling weather and traffic samples from DynamoDB and writing them into each activity payload.

`scripts/uniqueness.py` compares each route to other activities with DTW and stores a uniqueness description on the activity.

`scripts/context.py` derives activity context (distance/moving-time adjectives and time-of-day wording) using `goals.json`.

`scripts/poi.py` loads OSM data from `osm/hanoi.osm` and adds nearby points-of-interest categories to the activity payload.

`scripts/describe.py` renders prompt templates in `prompts/` and writes description markdown to `data/descriptions`, using Ollama and Gemini output.

`scripts/utils.py` provides shared JSON and ISO timestamp helpers used by the pipeline.
