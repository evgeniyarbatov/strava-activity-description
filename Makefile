VENV_PATH := .venv

PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
REQUIREMENTS := requirements.txt

DATA_DIR = data
STRAVA_ACTIVITIES = $(DATA_DIR)/strava_activities.json
WEATHER_DATA = $(DATA_DIR)/weather.json
DESCRIPTIONS = $(DATA_DIR)/descriptions.txt

venv:
	@python3 -m venv $(VENV_PATH)

install: venv
	@$(PIP) install --disable-pip-version-check -q --upgrade pip
	@$(PIP) install --disable-pip-version-check -q -r $(REQUIREMENTS)

strava:
	@aws dynamodb scan \
	--table-name strava_activities_v2 \
	--output json \
	| unmarshal > $(STRAVA_ACTIVITIES)

weather:
	@aws dynamodb scan \
	--table-name weather-data \
	--output json \
	| unmarshal > $(WEATHER_DATA)

activity:
	@$(PYTHON) scripts/last_activity.py

activity-weather:
	@$(PYTHON) scripts/last_activity_weather.py

uniqueness:
	@$(PYTHON) scripts/activity_uniqueness.py

description:
	@$(PYTHON) scripts/generate_description.py
