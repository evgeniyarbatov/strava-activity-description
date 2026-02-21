VENV_PATH := .venv
PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
REQUIREMENTS := requirements.txt

DATA_DIR = data
STRAVA_ACTIVITIES = $(DATA_DIR)/strava_activities.json
WEATHER_DATA = $(DATA_DIR)/weather.json
DESCRIPTIONS = $(DATA_DIR)/descriptions.txt

BOUNDARY_POLY = osm/hanoi.poly
OSM_URL = https://download.geofabrik.de/asia/vietnam-latest.osm.pbf
COUNTRY_OSM_FILE = $$(basename $(OSM_URL))

OSM_DIR = osm
TERRAFORM_DIR = terraform

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

country:
	if [ ! -f $(OSM_DIR)/$(COUNTRY_OSM_FILE) ]; then \
		wget $(OSM_URL) -P $(OSM_DIR); \
	fi

city:
	@osmconvert $(OSM_DIR)/$(COUNTRY_OSM_FILE) -B=$(BOUNDARY_POLY) -o=$(OSM_DIR)/hanoi.osm.pbf
	@osmium cat --overwrite $(OSM_DIR)/hanoi.osm.pbf -o $(OSM_DIR)/hanoi.osm

analyze:
	@$(PYTHON) -m scripts.merge
	@$(PYTHON) -m scripts.activity
	@$(PYTHON) -m scripts.weather_traffic
	@$(PYTHON) -m scripts.uniqueness
	@$(PYTHON) -m scripts.context
	@$(PYTHON) -m scripts.poi

describe:
	@$(PYTHON) -m scripts.describe --gemini

test:
	@$(PYTHON) -m pytest

deploy:
	@cd $(TERRAFORM_DIR) && terraform apply -auto-approve

.PHONY: data test
