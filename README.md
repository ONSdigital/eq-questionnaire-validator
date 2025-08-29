# eq-questionnaire-validator

An API for validating survey schemas.

## Setup

In order to run locally you'll need Node.js, poetry and pyenv installed.

### Install NVM and pyenv

NVM and pyenv will manage your versions of Node and Python.
``` shell
brew install nvm pyenv
nvm use
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

Validator defaults to running on `http://localhost:5002/validate`.

You can override this by setting the `AJV_VALIDATOR_SCHEME` , `AJV_VALIDATOR_HOST`, and `AJV_VALIDATOR_PORT` environment variables.
The defaults for these are:
- `AJV_VALIDATOR_SCHEME` = "http"
- `AJV_VALIDATOR_HOST` = "localhost"
- `AJV_VALIDATOR_PORT` = "5002"

Alternatively, you can override the entire URL by setting the `AJV_VALIDATOR_URL` environment variable directly.

If you want to run the app locally using multiple server workers set reload to "False" in the Uvicorn settings in api.py:
``` python
uvicorn.run("api:app", workers=20, port=5001, reload=False)
```

### Running against a URL

Once validator is running, it can be called directly in the browser using the "/validate" endpoint and the "url" parameter for the address where the schema is located (eg. GitHub Gist raw json).

Only the following ur URLs and domains are accepted:
- "https://gist.githubusercontent.com/"
- "https://raw.githubusercontent.com/"
- "onsdigital.uk"
- "localhost"

Also when using a URL from GitHub you can only validate schemas from the ONSdigital organisation.

Here is an example of a command you can use to validate a schema via a URL:
```
http://localhost:5001/validate?url=https://raw.githubusercontent.com/ONSdigital/eq-questionnaire-runner/refs/heads/main/schemas/test/en/test_address.json
```

### Running against eQ Runner

Also once you have validator running it can be used to run against eQ runner (`https://github.com/ONSdigital/eq-questionnaire-runner`). If you have runner spun up you can run the `make validate-test-schemas` script from within the root of runner which will run validator on the test runner schemas.

### Running the Ajv (server) version of validator

Included is a node based version of the json schema validation which may be used during development to assist with debugging errors. This returns more errors than we'd currently like due to the way polymorphism works for each of our blocks.

To run this you will need to add the `AJV_VALIDATOR_PORT` number to your .env file.

Then run the Ajv server:
``` shell
make start-ajv
```

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

To run the Ajv validator tests:
``` shell
make test-ajv
```

To run the app's unit tests and Ajv validator tests:
``` shell
make test
```

#### Test the apps functionality against runner

Spin it up with:
``` shell
make run
```

Then, in another terminal, navigate to a checked out copy of `https://github.com/ONSdigital/eq-questionnaire-runner` and run:
``` shell
make test
```

## Formatting json

Run the following to format all json files in the schemas directory:

``` shell
make format
```
