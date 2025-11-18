RUNNER_ENV_FILE ?= .development.env

.PHONY: build run lint test
ifneq (,$(wildcard $(RUNNER_ENV_FILE)))
  include $(RUNNER_ENV_FILE)
  export $(shell sed 's/=.*//' $(RUNNER_ENV_FILE))
endif


link-development-env:
	@ln -sf $(RUNNER_ENV_FILE) .env

build:
	poetry run ./scripts/build.sh

stop-ajv:
	@echo "Stopping AJV on port $(AJV_VALIDATOR_PORT)..."
	@AJV_VALIDATOR_PORT=$(AJV_VALIDATOR_PORT) npm run stop

start-ajv: link-development-env
	npm run start

run: start-ajv
	poetry run python api.py

lint: lint-python
	npm run lint

lint-python:
	poetry run ./scripts/run_lint_python.sh

test-unit:
	poetry run ./scripts/run_tests_unit.sh

test-ajv:
	npm run test

test: test-unit test-ajv

format: format-python
	npm run format

format-python:
	poetry run isort .
	poetry run black .
