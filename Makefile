# Uses uv (https://docs.astral.sh/uv) for dependency management — uv sync creates/updates .venv; run commands via uv run, no manual activation.
DATA_DIR = data

BOUNDARY_POLY = osm/ho-chi-minh-city.poly
OSM_URL = https://download.geofabrik.de/asia/vietnam-latest.osm.pbf

DOTFILES_MK := $(HOME)/gitRepo/dotfiles/make/osm-country.mk

.PHONY: country osm-country-fetch

ifneq ($(wildcard $(DOTFILES_MK)),)
include $(DOTFILES_MK)
else
COUNTRY_OSM_FILE ?= $(notdir $(OSM_URL))

country osm-country-fetch:
	@echo "error: '$@' needs evgeniyarbatov/dotfiles (private helper); not found at $(DOTFILES_MK)." >&2
	@echo "Fetch manually: download $(OSM_URL) into $(OSM_DIR)/$(COUNTRY_OSM_FILE), then retry." >&2
	@exit 1
endif

OSM_DIR = osm
TERRAFORM_DIR = terraform

.DEFAULT_GOAL := all

install:
	@uv sync --dev

city:
	@osmconvert $(OSM_DIR)/$(COUNTRY_OSM_FILE) -B=$(BOUNDARY_POLY) -o=$(OSM_DIR)/city.osm.pbf
	@osmium cat --overwrite $(OSM_DIR)/city.osm.pbf -o $(OSM_DIR)/city.osm

# Enrichment only (GPX → data/activities). Idempotent; scripts skip existing fields.
analyze: install
	@uv run python -m scripts.activity
	@uv run python -m scripts.weather_traffic
	@uv run python -m scripts.uniqueness
	@uv run python -m scripts.context
	@uv run python -m scripts.poi

# Full daily path: drop GPX in data/raw, then `make`.
reflect: analyze
	@uv run python -m scripts.describe

all: reflect

test: install
	@uv run python -m pytest

deploy: test
	@cd $(TERRAFORM_DIR) && terraform apply -auto-approve

lock:
	@uv lock

# Drop generated .gpx/.json/.md not tracked by git; keep committed samples and docs.
clean:
	@find . -type f \( -name '*.gpx' -o -name '*.json' -o -name '*.md' \) \
		! -path './.git/*' ! -path './.venv/*' \
		! -path './.mypy_cache/*' ! -path './.pytest_cache/*' ! -path './.ruff_cache/*' \
		| sed 's|^\./||' \
		| while IFS= read -r f; do \
			git ls-files --error-unmatch "$$f" >/dev/null 2>&1 || rm -f "$$f"; \
		done
	rm -rf .venv

help:
	@echo "make         - drop GPX in data/raw, then this (analyze + reflect → journal/)"
	@echo "analyze      - enrichment pipeline only"
	@echo "reflect      - analyze + journal reflection"
	@echo "install      - uv sync --dev"
	@echo "city         - build city OSM extract from country extract"
	@echo "test         - run pytest"
	@echo "deploy       - test + terraform apply"
	@echo "lock         - refresh uv.lock"
	@echo "clean        - remove untracked .gpx/.json/.md and .venv"

.PHONY: all install city analyze reflect test deploy lock clean help
