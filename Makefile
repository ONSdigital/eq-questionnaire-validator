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

.PHONY: clean
clean: ## Clean the temporary files.
	rm -rf .ruff_cache
	rm -rf megalinter-reports

lint: lint-python
	npm run lint

.PHONY: ruff
ruff: ## Run ruff linter code check.
	poetry run ruff check .

.PHONY: black
black: ## Run black linter code check.
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

.PHONY: megalint
megalint:  clean ## Run the MegaLinter.
	docker run --platform linux/amd64 --rm \
		-v /var/run/docker.sock:/var/run/docker.sock:rw \
		-v $(shell pwd):/tmp/lint:rw \
		ghcr.io/oxsecurity/megalinter-python:v9.1.0

run-validator:
	./scripts/run_validator.sh $(TAG)
