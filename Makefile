.PHONY: build run lint test

build:
	poetry run ./scripts/build.sh

stop-ajv:
	npm run stop

start-ajv:
	npm run start

run: start-ajv
	poetry run ./scripts/run_app.sh

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
