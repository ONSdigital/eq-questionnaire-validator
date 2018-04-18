#!/usr/bin/env bash

pyenv install
pip install pip==9.0.3 pipenv==11.10.0
pipenv install --dev --deploy
pipenv check
pipenv run ./scripts/run_lint.sh
pipenv run py.test