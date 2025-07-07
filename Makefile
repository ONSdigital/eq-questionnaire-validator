.PHONY: build run lint test
ifneq (,$(wildcard .env))
  include .env
  export
endif


build:
	poetry run ./scripts/build.sh

stop-ajv:
	@AJV_VALIDATOR_PORT=$(AJV_VALIDATOR_PORT) npm run stop

start-ajv:
	npm run start

run: start-ajv
	poetry run python api.py

.PHONY: clean
clean: ## Clean the temporary files.
	rm -rf .ruff_cache

lint: lint-python
	npm run lint
	poetry run ruff check .

.PHONY: ruff
ruff: ## Run ruff linter.
	poetry run ruff check .

.PHONY: black
black: ## Run black code formatter.
	poetry run black --check .

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
