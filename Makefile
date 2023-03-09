.PHONY: build run lint test

build:
	poetry run ./scripts/build.sh

stop-ajv:
	yarn stop

start-ajv:
	yarn start

run: start-ajv
	poetry run ./scripts/run_app.sh

lint: lint-python
	yarn lint

lint-python:
	poetry run ./scripts/run_lint_python.sh

test-unit:
	poetry run ./scripts/run_tests_unit.sh

test-yarn:
	yarn test

test: test-unit test-yarn

format: format-python
	yarn format

format-python:
	poetry run isort .
	poetry run black .
