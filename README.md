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

By default, all schemas in the `tests/schemas/valid` directory will be evaluated as part of the unit tests.
Any errors in these schemas will cause a failure.

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


## Formatting json

In the eq-schema-validator directory, ensure you are using a recent version of node (>10):

```
npm install 
npm i -g gulp-cli
```

Run the following to format all json files in the schemas directory:

```
gulp format
````
