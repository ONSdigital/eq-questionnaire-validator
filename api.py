import json
import logging
import os
import sys
from json import JSONDecodeError
from urllib import error, request
from urllib.parse import urlparse

import requests
import structlog
import uvicorn
from fastapi import Body, FastAPI, Response
from requests import RequestException

from app.validators.questionnaire_validator import QuestionnaireValidator

ALLOWED_FULL_DOMAINS = {
    "https://gist.githubusercontent.com/",
    "https://raw.githubusercontent.com/",
}

ALLOWED_BASE_DOMAINS = {"onsdigital.uk", "localhost"}

ALLOWED_REPO_OWNERS = {"ONSdigital"}

AJV_VALIDATOR_SCHEME = os.getenv("AJV_VALIDATOR_SCHEME", "http")

AJV_VALIDATOR_HOST = os.getenv("AJV_VALIDATOR_HOST", "localhost")

AJV_VALIDATOR_PORT = os.getenv("AJV_VALIDATOR_PORT", "5002")

AJV_VALIDATOR_URL = os.getenv(
    "AJV_VALIDATOR_URL",
    f"{AJV_VALIDATOR_SCHEME}://{AJV_VALIDATOR_HOST}:{AJV_VALIDATOR_PORT}/validate",
)


def configure_logging():
    LOG_LEVEL = logging.DEBUG if os.getenv("LOG_LEVEL") == "DEBUG" else logging.INFO

    error_log_handler = logging.StreamHandler(sys.stderr)
    error_log_handler.setLevel(logging.ERROR)

    renderer_processor = (
        structlog.dev.ConsoleRenderer()
        if LOG_LEVEL == logging.DEBUG
        else structlog.processors.JSONRenderer()
    )

    logging.basicConfig(level=LOG_LEVEL, format="%(message)s", stream=sys.stdout)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            renderer_processor,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


app = FastAPI()

configure_logging()
logger = structlog.get_logger()


@app.get("/status")
async def status():
    return Response(status_code=200)


@app.post("/validate")
async def validate_schema_request_body(payload=Body(None)):
    logger.info("Schema validation request received")
    return await validate_schema(payload)


@app.get("/validate")
async def validate_schema_from_url(url=None):
    logger.debug("Attempting to validate schema from URL...", url=url)
    if url:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if not is_url_allowed(parsed_url, domain):
            return Response(
                status_code=400,
                content=f"URL domain [{parsed_url.hostname}] is not allowed",
            )
        logger.info("Schema validation request accepted - URL allowed", url=url)
        try:
            # Opens the URL and validates the schema
            with request.urlopen(parsed_url.geturl()) as opened_url:
                return await validate_schema(data=opened_url.read().decode())
        except error.URLError:
            logger.warning(
                "Could not load schema from allowed domain - URL not found", url=url
            )
            return Response(
                status_code=404,
                content=f"Could not load schema from allowed domain - URL not found [{url}]",
            )


async def validate_schema(data):
    logger.debug("Attempting to validate schema from JSON data...")
    if data:
        # Sets `json_to_validate` to the data received if it is a dictionary as data does not require parsing
        if isinstance(data, dict):
            logger.info("JSON data received as dictionary - parsing not required")
            json_to_validate = data
        # Sets `json_to_validate` to the parsed data if it is a string
        elif isinstance(data, str):
            json_to_validate = parse_json(data)
        # Returns an error response if the data received is not a string or dictionary
        else:
            logger.error(
                "Invalid data type received for validation (expected string or dictionary)",
                data_type=type(data),
                status=400,
            )
            return Response(
                status_code=400, content="Invalid data type received for validation"
            )
    else:
        logger.error("No JSON data provided for validation", status=400)
        return Response(status_code=400, content="No JSON data provided for validation")

    response = {}
    try:
        logger.debug(
            "Sending JSON data to AJV Schema Validator service...",
            url=AJV_VALIDATOR_URL,
        )
        # Posts JSON data to AJV Validator service and returns a response containing any errors
        ajv_response = requests.post(
            AJV_VALIDATOR_URL, json=json_to_validate, timeout=10
        )
        # Returns errors in the response if AJV Validator service returned any errors
        if ajv_response_dict := ajv_response.json():
            response["errors"] = ajv_response_dict["errors"]
            logger.warning(
                "AJV Schema Validator service returned errors",
                status=400,
                errors=response["errors"],
            )
            return response, 400

    except RequestException:
        logger.error("AJV Schema Validator service unavailable")
        return json.dumps(obj={}, error="AJV Schema Validator service unavailable")

    logger.info("AJV Schema Validator service returned no errors", status=200)

    validator = QuestionnaireValidator(json_to_validate)
    logger.debug(
        "Attempting to validate questionnaire schema contents with Questionnaire Validator...",
        questionnaire_title=json_to_validate.get("title"),
    )
    # Validates questionnaire schema contents using the QuestionnaireValidator
    validator.validate()

    # Adds errors from validation to the response if there are any
    if validator.errors:
        response["errors"] = validator.errors
        logger.warning(
            "Questionnaire Validator returned errors",
            status=400,
            errors=response["errors"],
        )
        response = Response(content=json.dumps(response), status_code=400)

        return response

    logger.info("Schema validation successfully completed with no errors", status=200)

    response = Response(content=json.dumps(response), status_code=200)

    return response


def is_url_allowed(parsed_url, domain):
    logger.debug("Checking if domain is allowed...", domain=domain)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    repo_owner = (
        parsed_url.path.split("/")[1] if len(parsed_url.path.split("/")) > 1 else ""
    )
    logger.debug("Parsed URL components", base_url=base_url, repo_owner=repo_owner)

    # Allows URLs from verified full domains with trusted repo owners
    full_url_allowed = (
        base_url in ALLOWED_FULL_DOMAINS and repo_owner in ALLOWED_REPO_OWNERS
    )
    # Allows URLs from trusted base domains
    base_domain_allowed = domain in ALLOWED_BASE_DOMAINS

    logger.debug(
        "URL allowance checks",
        full_url_allowed=full_url_allowed,
        base_domain_allowed=base_domain_allowed,
    )

    url_allowed = full_url_allowed or base_domain_allowed

    # If the URL is not allowed, outputs warnings reflecting which parts of the URL are not allowed
    if not url_allowed:
        logger.warning("URL is not allowed", url=parsed_url.geturl())
        if base_url not in ALLOWED_FULL_DOMAINS:
            logger.warning(
                "Base URL is not in ALLOWED_FULL_DOMAINS (resolve by using allowed base URL or domain)",
                base_url=base_url,
            )
        if repo_owner not in ALLOWED_REPO_OWNERS:
            logger.warning(
                "Repo owner is not in ALLOWED_REPO_OWNERS (resolve by using allowed repo owner or domain)",
                repo_owner=repo_owner,
            )
        if not base_domain_allowed:
            logger.warning(
                "Domain is not in ALLOWED_BASE_DOMAINS (resolve by using allowed domain or full URL)",
                domain=domain,
            )

    return url_allowed


def parse_json(data):
    processed_data = data
    # Parses `data` if it is in string format
    if isinstance(data, str):
        logger.info("JSON data received as string - parsing required")
        logger.debug("Attempting to parse JSON data...")
        try:
            processed_data = json.loads(data)
            logger.info("JSON data parsed successfully")
        except JSONDecodeError:
            logger.error("Failed to parse JSON data", status=400)
            return Response(status_code=400, content="Failed to parse JSON")
    return processed_data


if __name__ == "__main__":
    uvicorn.run("api:app", workers=20, port=5001, reload=True)
