# Strava Activity Description

Generate short Strava activity descriptions from run polylines, weather, traffic, and prior history. Sample data lives in `data/activities` with the corresponding description in `data/descriptions`.

## Steps

Add GPX and TCX to `data/raw`

Run `make analyze` to merge GPX/TCX, to get context and weather / traffic data.

`make describe` to generate the descriptions.

## Update

`make test` to run tests

`make deploy` to update Lambda
