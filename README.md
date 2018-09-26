# eq-schema-validator
An API for validating survey schemas.

## Setup

```
brew install pyenv
pip install --upgrade pip setuptools pipenv
pipenv install --dev
```

## Running

To run the app:

```
pipenv run ./scripts/run_app.sh
```

## Testing

To run the app's unit tests:

```
pipenv run ./scripts/run_tests_unit.sh
```

To test the apps functionality:
```
pipenv run ./scripts/run_app.sh
```

Then, in another terminal window/tab, navigate to a checked out copy of eq-survey-runner:
```
pipenv run ./scripts/test_schemas.sh --local
```
