# eq-questionnaire-validator

An API for validating survey schemas.

## Setup

In order to run locally you'll need Node.js, Poetry and Python installed.
It's recommended that Python is installed via pyenv but pyenv is optional.

### Install NVM and pyenv

NVM and pyenv will manage your versions of Node and Python and these commands will install the
required versions of them which will be read from `.nvmrc` and `.python-version`.

```shell
brew install nvm pyenv
nvm use
pyenv install
```

If you get a message in the command line after running `nvm use` that the version of Node specified
in the `.nvmrc` file isn't installed, just follow the commands to install it.

e.g.

```shell
nvm install v22.15.0
```

### Install JS dependencies

```shell
npm install
```

### Install Poetry and Python dependencies

```shell
curl -sSL https://install.python-poetry.org | python3 - --version 2.2.1
poetry install
```

## Running locally

To run the app:

```shell
make run
```

Validator runs on two ports, `5001` is the main validator app and `5002` is Ajv validator.

### Validator

Validator runs on `http://localhost:5001/validate` and accepts GET and POST requests.

If you need to change the port you can change the port variable in the Uvicorn settings in api.py:

```python
uvicorn.run("api:app", workers=20, port=5001, reload=True)
```

The reload flag here will allow the service to restart if you make a change to the code,
if you want to run the app locally using multiple server workers you need to set reload to "False".

### Ajv validator

Ajv validator defaults to running on `http://localhost:5002`.

You can override this by setting the `AJV_VALIDATOR_SCHEME`, `AJV_VALIDATOR_HOST`, and `AJV_VALIDATOR_PORT` environment variables.
These values are set by the `.development.env` file in the route of the repo file structure.
This is linked to `.env` by the `link-development-env` command in the make file, which is triggered automatically on run.
The linking of the `.env` files ensures that changes in one are reflected in the other.
The defaults for these are:

- `AJV_VALIDATOR_SCHEME` = http
- `AJV_VALIDATOR_HOST` = localhost
- `AJV_VALIDATOR_PORT` = 5002

Alternatively, you can override the entire URL by setting the `AJV_VALIDATOR_URL` environment variable directly.
(**Note**: These values are also defined in the Dockerfiles, so if you choose to run
[Validator through Docker](#running-with-docker) these may need to be updated)

### Running against a URL

Once Validator is running, it can be called directly in the browser using the "/validate" endpoint
and the "url" parameter for the address where the schema is located (e.g. GitHub Gist raw json).

As Validator runs on `localhost:5001` by default, here is an
example of a command you can use to validate a schema via a URL:

```shell
http://localhost:5001/validate?url=https://raw.githubusercontent.com/ONSdigital/eq-questionnaire-runner/refs/heads/main/schemas/test/en/test_address.json
```

Only the following URLs and domains are accepted:

- `https://gist.githubusercontent.com/`
- `https://raw.githubusercontent.com/`
- `onsdigital.uk`
- `localhost`

Also when using a URL from GitHub you can only validate schemas from the ONSdigital organisation and
only against repos with the owner "ONSdigital".

### Running against eQ Runner

Also once you have Validator running it can be used to run against eQ Runner (`https://github.com/ONSdigital/eq-questionnaire-runner`).
If you have eQ Runner spun up you can from within the root of eQ Runner run:

```shell
make validate-test-schemas
```

This script will run Validator on the test eQ Runner schemas.

### Running the Ajv (server) version of Validator

Running `make run` will start up the both of services required for validation (Ajv validator
and the Validator app itself). However, if you want to start Ajv individually, run:

```shell
make start-ajv
```

This defaults to running on port `5002`, set `AJV_VALIDATOR_PORT` in your .env file if you need to change this.

Running the Ajv server returns either an empty json response when the questionnaire is valid,
or a response containing an "errors" key.
The errors are ordered by their path length and with first error message being the deepest path
into the schema and should represent the best match for the questionnaire which has been posted.

To stop the Ajv server:

```shell
make stop-ajv
```

### Testing and running against local schemas

By default, all schemas in the `tests/schemas/valid` and `tests/schemas/invalid` directories will be
evaluated as part of the unit tests. Any errors in these schemas will cause a failure.

To run the app's unit tests:

```shell
make test-unit
```

Make sure you don't already have Ajv running on localhost:5002 by running `lsof -i tcp:5002` if you
do make a note of the PID (process identifier) and then run `kill -9 <PID>`, replacing `<PID>` with
the process id from the previous command.

To run the app's integration tests:

```shell
make test-integration
```

Run the Ajv validator tests:

```shell
make test-ajv
```

To run the app's unit tests and Ajv validator tests:

```shell
make test
```

#### Test the local Validator app against eQ Runner schemas

Spin Validator up with:

```shell
make run
```

Then, in another terminal, navigate to a checked out copy
of `https://github.com/ONSdigital/eq-questionnaire-runner` and run:

```shell
make validate-test-schemas
```

This will run Validator against all eQ Runner test schemas.

Or you can run it against a specific eQ Runner schema, to do this:

- set the following vars passing them into the following command:
    - `SCHEMA_PATH` to the path of the schema file (if not specified defaults to `./schemas/test/en/`)
    - `SCHEMA` to the schema file name without the `.json`
- then run (for example):

```shell
make validate-test-schema SCHEMA=test_checkbox SCHEMA_PATH=./schemas/
```

## Formatting/linting json

Run the following to format the JS files in the Ajv folder, the json files in the schemas and test schemas folders
and the Python files in the repository:

```shell
make format
```

Run the following to lint the JS files in the Ajv folder, the json files in the schemas and test schemas folders
and the Python files in the repository:

```shell
make lint
```

## MegaLinter (Lint/Format non-python files)

[MegaLinter](https://github.com/oxsecurity/megalinter) is utilised to lint the non-python files in the project.
It offers a single interface to execute a suite of linters for multiple languages and formats, ensuring adherence to
best practices and maintaining consistency across the repository without the need to install each linter individually.

MegaLinter examines various file types and tools, including GitHub Actions, Shell scripts, Dockerfile, etc. It is
configured using the `.mega-linter.yml` file.

To run MegaLinter, ensure you have **Docker** installed on your system.

> Note: The initial run may take some time to download the Docker image. However, subsequent executions will be
> considerably faster due to Docker caching.

To start the linter and automatically rectify fixable issues, run:

```bash
make megalint
```

## Running with Docker

To install Docker run:

```shell
brew install docker
```

On MacOS install container runtimes, e.g. Colima:

```shell
brew install colima
```

Make sure Colima is started every time you want to use Docker images:

```shell
colima start
```

When PRs are merged in this repo there is a GitHub workflow that builds 2 Docker images one for Validator
and one for the Ajv validator and then pushes them to our GAR in GCP.
These images can then be pulled down and run locally with Docker.
These images are pulled down and run from eQ Runner when `make run validator` is run which uses
the `docker-compose-schema-validator.yml` script.

You can do this using these commands:

You will need to be authenticated with GCP to run these, to do this run `gcloud auth login` first

- Validator:

```shell
docker run -it -p 5001:5001 europe-west2-docker.pkg.dev/ons-eq-ci/docker-images/eq-questionnaire-validator
```

- Ajv validator:

```shell
docker run -it -p 5002:5002 europe-west2-docker.pkg.dev/ons-eq-ci/docker-images/eq-questionnaire-validator-ajv
```

To stop these containers you may need to use the `docker kill` command:

First run:

```shell
docker ps
```

Then make a note of the container id of the container you want to stop and then
run (replacing "<CONTAINER_ID>" with the id):

```shell
docker kill <CONTAINER_ID>
```

## Environment variables

| Environment variable   | Description                                                              | Default value                                                                 |
|------------------------|--------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `LOG_LEVEL`            | Sets the minimum log level, can be set to `DEBUG` to increase this level | `INFO`                                                                        |
| `AJV_VALIDATOR_SCHEME` | Sets the scheme for the URL that Ajv validator will run on               | `http`                                                                        |
| `AJV_VALIDATOR_HOST`   | Sets the host for the URL that Ajv validator will run on                 | `localhost`                                                                   |
| `AJV_VALIDATOR_PORT`   | Sets the port for the URL that Ajv validator will run on                 | `5002`                                                                        |
| `AJV_VALIDATOR_URL`    | Sets complete URL that Ajv validator will run on                         | `<AJV_VALIDATOR_SCHEME>://<AJV_VALIDATOR_HOST>:<AJV_VALIDATOR_PORT>/validate` |
