# eq-questionnaire-validator

An API for validating survey schemas.

## Setup

In order to run locally you'll need Node.js, poetry and pyenv installed.

### Install NVM and pyenv

NVM and pyenv will manage your versions of Node and Python and these commands will install the required versions of them which will be read from `.nvmrc` and `.python-version`.

``` shell
brew install nvm pyenv
nvm use
pyenv install
```

If you get a message in the command line after running `nvm use` that the version of node specified in the `.nvmrc` file isn't installed, just follow the commands to install it.

e.g.
``` shell
nvm install v22.15.0
```

### Install JS dependencies

``` shell
npm install
```

### Install Poetry and Python dependencies

``` shell
curl -sSL https://install.python-poetry.org | python3 - --version 2.1.2
poetry install
```

## Running locally

To run the app:
``` shell
make run
```

Validator runs on two ports, `5001` is the main validator app and `5002` is the Ajv validator.

### Validator

Validator runs on `http://localhost:5001/validate`.

If you need to change the port you can change the port variable in the Uvicorn settings in api.py:
``` python
uvicorn.run("api:app", workers=20, port=5001, reload=False)
```
If you want to run the app locally using multiple server workers you can also set reload to "False" here too.

### Ajv Validator

The Ajv validator defaults to running on `http://localhost:5002`.

You can override this by setting the `AJV_VALIDATOR_SCHEME` , `AJV_VALIDATOR_HOST`, and `AJV_VALIDATOR_PORT` environment variables.
The defaults for these are:
- `AJV_VALIDATOR_SCHEME` = "http"
- `AJV_VALIDATOR_HOST` = "localhost"
- `AJV_VALIDATOR_PORT` = "5002"

Alternatively, you can override the entire URL by setting the `AJV_VALIDATOR_URL` environment variable directly.

### Running against a URL

Once validator is running, it can be called directly in the browser using the "/validate" endpoint and the "url" parameter for the address where the schema is located (eg. GitHub Gist raw json).

As Validator runs on `localhost:5001` by default, here is an example of a command you can use to validate a schema via a URL:
``` shell
http://localhost:5001/validate?url=https://raw.githubusercontent.com/ONSdigital/eq-questionnaire-runner/refs/heads/main/schemas/test/en/test_address.json
```

Only the following URLs and domains are accepted:
- "https://gist.githubusercontent.com/"
- "https://raw.githubusercontent.com/"
- "onsdigital.uk"
- "localhost"

Also when using a URL from GitHub you can only validate schemas from the ONSdigital organisation and only against repos with the owner "ONSdigital".

### Running against eQ Runner

Also once you have validator running it can be used to run against eQ runner (`https://github.com/ONSdigital/eq-questionnaire-runner`). If you have runner spun up you can run the `make validate-test-schemas` script from within the root of runner which will run validator on the test runner schemas.

### Running the Ajv (server) version of validator

Then run the Ajv server:
``` shell
make start-ajv
```

This defaults to running on port `5002` set `AJV_VALIDATOR_PORT` in your .env file if you need to change this.

To stop the Ajv server:
``` shell
make stop-ajv
```

Running this returns either an empty json response when the questionnaire is valid, or a response containing an "errors" key. The errors are ordered by their path length and with first error message being the deepest path into the schema and should represent the best match for the questionnaire which has been posted.

### Testing and running against local schemas

By default, all schemas in the `tests/schemas/valid` directory will be evaluated as part of the unit tests. Any errors in these schemas will cause a failure. You can use this to run against local schemas by adding any schemas to this folder.

To run the app's unit tests:
``` shell
make test-unit
```

Make sure you don't already have Ajv running on localhost:5002 by running `lsof -i tcp:5002` if you do make a note of the PID and then run `kill -9 PID`, replacing "PID" with the process id from the previous command.

Run the Ajv validator tests:
``` shell
make test-ajv
```

To run the app's unit tests and Ajv validator tests:
``` shell
make test
```

#### Test the local validator app against runner schemas

Spin validator up with:
``` shell
make run
```

Then, in another terminal, navigate to a checked out copy of `https://github.com/ONSdigital/eq-questionnaire-runner` and run:
``` shell
make validate-test-schemas
```
This will run the validator against all runner test schemas.

Or you can run it against a specific runner schema, to do this:
- set the runner vars:
    - `SCHEMA_PATH` to the path of the schema file (defaults to `./schemas/test/en/`)
    - `SCHEMA` to the schema file name without the `.json`
- then run:
``` shell
make validate-test-schema
```

## Formatting/linting json

Run the following to format all json files in the schemas directory:

``` shell
make format
```

Run the following to lint all schemas, test schemas and Ajv files in the repo:

``` shell
make lint
```

## Docker

When PRs are merged in this repo there is a GitHub workflow that builds a Docker image of validator and then pushes to our GAR in GCP. This image can then be pulled down and run locally with Docker.
