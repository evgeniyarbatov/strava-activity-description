# Strava Activity Description

Generate short Strava activity descriptions from run polylines, weather, traffic, and prior history. The core Python entry points live in `scripts/` (see `scripts/merge.py`, `scripts/context.py`, and `scripts/describe.py`).

Sample data lives in `data/activities/7068952d-1b91-5eb2-8181-05a612370031.json` with the corresponding description in `data/descriptions/7068952d-1b91-5eb2-8181-05a612370031.md`.

## Steps

Add GPX and TCX to `data/raw`

Run `make analyze` to merge GPX/TCX, to get context and weather / traffic data.

`make describe` to generate the descriptions.

## Update

`make test` to run tests

`make deploy` to update Lambda
