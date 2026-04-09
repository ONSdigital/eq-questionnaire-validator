#!/bin/bash
#
# Run project through linting
#
# NOTE: This script expects to be run from the project root with
# ./scripts/run_lint.sh

function display_result {
    RESULT=$1
    EXIT_STATUS=$2
    TEST=$3

    if [ $RESULT -ne 0 ]; then
        echo -e "\033[31m$TEST failed\033[0m"
        exit $EXIT_STATUS
    else
        echo -e "\033[32m$TEST passed\033[0m"
    fi
}

COMMON_EXCLUDES=".venv,.tox,node_modules,htmlcov,megalinter-reports"
BLACK_EXCLUDES='/(\.venv|\.tox|node_modules|htmlcov|megalinter-reports)/'

flake8 --max-complexity 10 --count --exclude "$COMMON_EXCLUDES"
display_result $? 1 "Flake 8 code style check"

find . \
    \( -path "./.venv" -o \
    -path "./.tox" -o \
    -path "./node_modules" -o \
    -path "./htmlcov" -o \
    -path "./megalinter-reports" \) -prune \
    -o -type f -name "*.py" -print | xargs pylint --reports=n --output-format=colorized --rcfile=.pylintrc -j 0
# pylint bit encodes the exit code to allow you to figure out which category has failed.
# https://docs.pylint.org/en/1.6.0/run.html#exit-codes
# We want to fail on all errors so don't check for specific bits in the output; but if we did in future, see:
# http://stackoverflow.com/questions/6626351/how-to-extract-bits-from-return-code-number-in-bash
display_result $? 2 "Pylint linting check"

isort --check --skip .venv --skip .tox --skip node_modules --skip htmlcov --skip megalinter-reports .
display_result $? 1 "isort linting check"

black --check . --exclude "$BLACK_EXCLUDES"

display_result $? 1 "Python code formatting check"

ruff check . --exclude .venv --exclude .tox --exclude node_modules --exclude htmlcov --exclude megalinter-reports
display_result $? 1 "Ruff linting check"
