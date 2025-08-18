import json
import os
from json import JSONDecodeError
from urllib import error, request
from urllib.parse import urlparse

import requests
import uvicorn
from fastapi import Body, FastAPI, Response
from requests import RequestException
from structlog import get_logger

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

app = FastAPI()

logger = get_logger()


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
        if not is_domain_allowed(parsed_url, domain):
            logger.warning(
                "Schema validation request rejected - URL not allowed (this could be related to domain, base_url or repo_owner - see debug logs for values)",
                url=url,
            )
            return Response(
                status_code=400,
                content=f"URL domain [{parsed_url.hostname}] is not allowed",
            )
        logger.info("Schema validation request accepted - URL allowed", url=url)
        try:
            # Opens the URL and validates the schema
            with request.urlopen(parsed_url.geturl()) as opened_url:
                return await validate_schema(data=opened_url.read().decode())
            logger.info("Schema successfully validated from URL", url=url)
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
        # Sets `json_to_validate` to the data received if it is a dictionary as data does not require processing
        if isinstance(data, dict):
            logger.info("JSON data received as dictionary - processing not required")
            json_to_validate = data
        # Sets `json_to_validate` to the decoded and parsed data if it is not in dictionary format
        else:
            json_to_validate = decode_and_parse_json(data)
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


def is_domain_allowed(parsed_url, domain):
    logger.debug("Checking if domain is allowed...", domain=domain)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    repo_owner = (
        parsed_url.path.split("/")[1] if len(parsed_url.path.split("/")) > 1 else ""
    )
    logger.debug("Parsed URL components", base_url=base_url, repo_owner=repo_owner)
    return (
        base_url in ALLOWED_FULL_DOMAINS and repo_owner in ALLOWED_REPO_OWNERS
    ) or domain in ALLOWED_BASE_DOMAINS


def decode_and_parse_json(data):
    processed_data = data
    # Decodes `data` to string if it is in bytes format
    if isinstance(data, bytes):
        logger.info("JSON data received as bytes - decoding required")
        logger.debug("Attempting to decode JSON data...")
        try:
            data = data.decode("utf-8")
            logger.info("JSON data decoded as UTF-8 successfully")
        except UnicodeDecodeError:
            logger.error("Failed to decode JSON data as UTF-8", status=400)
            return Response(
                status_code=400, content="Failed to decode JSON data as UTF-8"
            )
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
