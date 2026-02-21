# Strava Activity Description

Generate short Strava activity descriptions from run polylines, weather, traffic, and prior history. The core Python entry points live in `scripts/` (see `scripts/merge.py`, `scripts/context.py`, and `scripts/describe.py`).

## Steps

Add GPX and TCX to `data/raw`

Run `make analyze` to merge GPX/TCX, to get context and weather / traffic data.

`make describe` to generate the descriptions.
