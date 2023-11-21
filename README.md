# eq-questionnaire-validator

An API for validating survey schemas.

## Setup

It is recommended that you use [Pyenv](https://github.com/pyenv/pyenv) to manage your Python installations.

### Install Poetry
```
curl -sSL https://install.python-poetry.org | python3 - 
poetry install
```

## Running

To run the app:

```
make run
```

## Testing

By default, all schemas in the `tests/schemas/valid` directory will be evaluated as part of the unit tests.
Any errors in these schemas will cause a failure.

To run the app's unit tests:

```
make test-unit
```

To run the app's unit tests and ajv validator tests:

```
make test
```

To test the apps functionality:
```
make run
```

Then, in another terminal window/tab, navigate to a checked out copy of eq-survey-runner:
```
make test
```

# Installing node dependencies

In the eq-schema-validator directory, install node version manager (nvm) and node using the following commands:

```
brew install nvm
nvm install
```

Install node dependencies:

```
npm install
```

To install additional dependencies use:
```
npm install [dev dependency] --save-dev 
```
or
```
npm install [dev dependency]
```

To run the ajv validator tests:

```
make test-ajv
```

## Formatting json

Run the following to format all json files in the schemas directory:

```
make format
````

## Validating with ajv

Also included is a node based version of the json schema validation which may be used during development to assist with
debugging errors. This returns more errors than we'd currently like due to the way polymorphism works for each of our
blocks.

Run the ajv (server) based version of validator.

```
make start-ajv
```
To stop the ajv (server) based version of validator.

```
make stop-ajv
```

This returns either an empty json response when the questionnaire is valid, or a response containing an "errors" key.
The errors are ordered by their path length and with first error message being the deepest path into the schema and
should represent the best match for the questionnaire which has been posted.
