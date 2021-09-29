.PHONY: build run lint test

build:
	pipenv run ./scripts/build.sh

run:
	pipenv run ./scripts/run_app.sh

lint: lint-python
	yarn lint

lint-python:
	pipenv run ./scripts/run_lint_python.sh

test:
	pipenv run ./scripts/run_tests_unit.sh

format: format-python
	yarn format

format-python:
	pipenv run isort .
	pipenv run black .
