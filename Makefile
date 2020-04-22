lint:
	pipenv run ./scripts/run_lint_python.sh

format:
	pipenv run black .

test-unit:
	pipenv run ./scripts/run_tests_unit.sh