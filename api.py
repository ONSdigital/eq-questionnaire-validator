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

app = FastAPI()


@app.get("/status")
async def status():
    return Response(status_code=200)


logger = get_logger()

AJV_VALIDATOR_SCHEME = os.getenv("AJV_VALIDATOR_SCHEME", "http")
AJV_VALIDATOR_HOST = os.getenv("AJV_VALIDATOR_HOST", "localhost")
AJV_VALIDATOR_PORT = os.getenv("AJV_VALIDATOR_PORT", "5002")
AJV_VALIDATOR_URL = os.getenv(
    "AJV_VALIDATOR_URL",
    f"{AJV_VALIDATOR_SCHEME}://{AJV_VALIDATOR_HOST}:{AJV_VALIDATOR_PORT}/validate",
)


@app.post("/validate")
async def validate_schema_request_body(payload=Body(None)):
    logger.info("Validating schema")
    return await validate_schema(payload)


@app.get("/validate")
async def validate_schema_from_url(url=None):
    if url:
        logger.info("Validating schema from URL", url=url)
        parsed_url = urlparse(url)
        if not is_hostname_allowed(parsed_url.hostname):
            return Response(
                status_code=400,
                content=f"URL domain [{parsed_url.hostname}] is not allowed",
            )

        try:
            with request.urlopen(url) as opened_url:
                return await validate_schema(data=opened_url.read().decode())
        except error.URLError:
            return Response(
                status_code=404, content=f"Could not load schema at URL [{url}]"
            )


async def validate_schema(data):
    json_to_validate = None
    if data:
        if isinstance(data, str):
            try:
                json_to_validate = json.loads(data)
            except JSONDecodeError:
                logger.info("Could not parse JSON", status=400)
                return Response(status_code=400, content="Could not parse JSON")
        elif isinstance(data, dict):
            json_to_validate = data

    response = {}
    try:
        ajv_response = requests.post(
            AJV_VALIDATOR_URL, json=json_to_validate, timeout=10
        )
        if ajv_response_dict := ajv_response.json():
            response["errors"] = ajv_response_dict["errors"]
            logger.info("Schema validator returned errors", status=400)
            return response, 400

    except RequestException:
        logger.info("AJV Schema validator service unavailable")
        return json.dumps(obj={}, error="AJV Schema validator service unavailable")

    validator = QuestionnaireValidator(json_to_validate)
    validator.validate()

    if validator.errors:
        response["errors"] = validator.errors
        logger.info("Questionnaire validator returned errors", status=400)
        response = Response(content=json.dumps(response), status_code=400)

        return response

    logger.info("Schema validation passed", status=200)

    response = Response(content=json.dumps(response), status_code=200)

    return response


def is_hostname_allowed(hostname):
    allowed_full_domains = {
        "gist.githubusercontent.com",
        "raw.githubusercontent.com",
    }
    allowed_base_domains = {"onsdigital.uk"}

    return hostname in allowed_full_domains or any(
        hostname.endswith(f".{base}") for base in allowed_base_domains
    )


if __name__ == "__main__":
    uvicorn.run("api:app", workers=20, port=5001, reload=True)
