VENV_PATH := .venv

PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
REQUIREMENTS := requirements.txt

DATA_DIR = data
STRAVA_ACTIVITIES = $(DATA_DIR)/strava_activities.json
DESCRIPTIONS = $(DATA_DIR)/descriptions.txt

venv:
	@python3 -m venv $(VENV_PATH)

install: venv
	@$(PIP) install --disable-pip-version-check -q --upgrade pip
	@$(PIP) install --disable-pip-version-check -q -r $(REQUIREMENTS)

data:
	@mkdir -p $(dir $(STRAVA_ACTIVITIES))
	@aws dynamodb scan \
	--table-name strava_activities_v2 \
	--output json \
	| unmarshal > $(STRAVA_ACTIVITIES)

descriptions:
	@jq -r '.[].activity.description | select(. != null and . != "")' \
	$(STRAVA_ACTIVITIES) > $(DESCRIPTIONS)

script:
	@$(PYTHON) $(SCRIPTS_DIR)/script.py

.PHONY: data