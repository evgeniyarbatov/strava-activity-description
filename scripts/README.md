## Scripts

`scripts/merge.py` merges TCX cadence/heart-rate samples into GPX tracks from `data/raw` and writes merged GPX files to `data/gpx`.

`scripts/activity.py` parses merged GPX tracks into activity JSON with distance, moving time, and an encoded polyline in `data/activities`.

`scripts/weather_traffic.py` enriches activity JSON by pulling weather and traffic samples from DynamoDB and writing them into each activity payload.

`scripts/uniqueness.py` compares routes using z-scored raw lat/lon samples plus distance and stores a uniqueness description on the activity.

`scripts/context.py` derives activity context (distance/moving-time adjectives and time-of-day wording) using `goals.json`.

`scripts/poi.py` loads OSM data from `osm/hanoi.osm` and adds nearby points-of-interest categories to the activity payload.

`scripts/describe.py` runs a CrewAI pipeline per prompt (config in `prompts/<prompt>/agents.yaml` and `prompts/<prompt>/tasks.yaml` with shared context in `prompts/activity-context.txt`) to draft and then revise descriptions with a personal-voice pass, writing markdown to `data/descriptions`, using Ollama and Gemini output.

`scripts/utils.py` provides shared JSON and ISO timestamp helpers used by the pipeline.
