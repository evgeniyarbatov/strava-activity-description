# Uses uv (https://docs.astral.sh/uv) for dependency management — uv sync creates/updates .venv; run commands via uv run, no manual activation.
DATA_DIR = data
WEATHER_DATA = $(DATA_DIR)/weather.json

BOUNDARY_POLY = osm/ho-chi-minh-city.poly
OSM_URL = https://download.geofabrik.de/asia/vietnam-latest.osm.pbf
include $(HOME)/gitRepo/dotfiles/make/osm-country.mk

OSM_DIR = osm
TERRAFORM_DIR = terraform

install:
	@uv sync --dev

city:
	@osmconvert $(OSM_DIR)/$(COUNTRY_OSM_FILE) -B=$(BOUNDARY_POLY) -o=$(OSM_DIR)/city.osm.pbf
	@osmium cat --overwrite $(OSM_DIR)/city.osm.pbf -o $(OSM_DIR)/city.osm

analyze: install
	@uv run python -m scripts.activity
	@uv run python -m scripts.weather_traffic
	@uv run python -m scripts.uniqueness
	@uv run python -m scripts.context
	@uv run python -m scripts.poi

reflect: install
	@uv run python -m scripts.describe

describe: reflect

test: install
	@uv run python -m pytest

deploy: test
	@cd $(TERRAFORM_DIR) && terraform apply -auto-approve

lock:
	@uv lock

clean:
	rm -rf .venv

help:
	@echo "install - uv sync --dev"
	@echo "city    - build city OSM extract from country extract"
	@echo "analyze - run activity/weather/uniqueness/context/poi pipeline"
	@echo "reflect - run CrewAI multi-lens reflection"
	@echo "describe - alias for reflect"
	@echo "test    - run pytest"
	@echo "deploy  - test + terraform apply"
	@echo "lock    - refresh uv.lock"
	@echo "clean   - remove .venv"

.PHONY: data test install city analyze reflect describe deploy lock clean help
