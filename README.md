# Strava Activity Description

Generate activity description based on weather data and geometric properties of the run polyline. Use past descriptions and history of my runs to generate unique and short description with help of LLMs/

## Steps

Add GPX and TCX to `data/raw`

Run `make analyze` to merge GPX/TCX, to get context and weather / traffic data.

`make describe` to generate the descriptions.