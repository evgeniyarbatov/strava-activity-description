# Uses uv (https://docs.astral.sh/uv) for dependency management — uv sync creates/updates .venv; run commands via uv run, no manual activation.
DATA_ROOT ?= $(HOME)/data
REPO_NAME := $(notdir $(CURDIR))
DATA_DIR  ?= $(DATA_ROOT)/$(REPO_NAME)
JOURNAL_DIR ?= $(DATA_DIR)/journal

export DATA_DIR
export JOURNAL_DIR

BOUNDARY_POLY = osm/ho-chi-minh-city.poly
OSM_URL = https://download.geofabrik.de/asia/vietnam-latest.osm.pbf

DOTFILES_MK := $(HOME)/gitRepo/dotfiles/make/osm-country.mk

OSM_DIR := $(DATA_DIR)/osm
export OSM_DIR

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

TERRAFORM_DIR = terraform

.DEFAULT_GOAL := all

install:
	@mkdir -p $(DATA_DIR)/raw $(DATA_DIR)/activities $(JOURNAL_DIR)
	@uv sync --dev

city:
	@osmconvert $(OSM_DIR)/$(COUNTRY_OSM_FILE) -B=$(BOUNDARY_POLY) -o=$(OSM_DIR)/city.osm.pbf
	@osmium cat --overwrite $(OSM_DIR)/city.osm.pbf -o $(OSM_DIR)/city.osm

# Enrichment only (GPX → DATA_DIR/activities). Idempotent; scripts skip existing fields.
analyze: install
	@uv run python -m scripts.activity
	@uv run python -m scripts.weather_traffic
	@uv run python -m scripts.uniqueness
	@uv run python -m scripts.context
	@uv run python -m scripts.poi

# Full daily path: drop GPX in DATA_DIR/raw, then `make`.
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
	@echo "make         - drop GPX in $(DATA_DIR)/raw, then this (analyze + reflect → $(JOURNAL_DIR))"
	@echo "analyze      - enrichment pipeline only"
	@echo "reflect      - analyze + journal reflection"
	@echo "install      - uv sync --dev"
	@echo "city         - build city OSM extract from country extract"
	@echo "test         - run pytest"
	@echo "deploy       - test + terraform apply"
	@echo "lock         - refresh uv.lock"
	@echo "clean        - remove untracked .gpx/.json/.md and .venv"

.PHONY: all install city analyze reflect test deploy lock clean help
