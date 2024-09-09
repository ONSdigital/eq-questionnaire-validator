import json
import os
import urllib
from json import JSONDecodeError

import requests

from requests import RequestException
from structlog import get_logger

from app.validators.questionnaire_validator import QuestionnaireValidator

from fastapi import FastAPI, Response, Body

from requests import request

import uvicorn

app = FastAPI()


@app.get("/status")
async def validate_schema():
    return Response(status_code=200)



logger = get_logger()

AJV_HOST = os.getenv("AJV_HOST", "localhost")

AJV_VALIDATOR_URL = f"http://{AJV_HOST}:5002/validate"


@app.post("/validate")
async def validate_schema_request_body(payload=Body(None)):
    logger.info("Validating schema")
    return await validate_schema(payload)


@app.get("/validate")
def validate_schema_from_url():
    values = request.args
    if "url" in values:
        logger.info("Validating schema from URL", url=values["url"])
        try:
            with urllib.request.urlopen(values["url"]) as url:
                return validate_schema(url.read().decode())
        except urllib.error.URLError:
            return (
                Response(
                    status=404,
                    response=f'Could not load schema at URL [{values["url"]}]',
                ),
            )


async def validate_schema(data):
    # try:
    #     json_to_validate = json.loads(data)
    # except JSONDecodeError:
    #     logger.info("Could not parse JSON", status=400)
    #     return Response(status=400, response="Could not parse JSON")

    response = {}
    try:
        ajv_response = requests.post(
            AJV_VALIDATOR_URL, json=data, timeout=10
        )
        ajv_response_dict = ajv_response.json()

        if ajv_response_dict:
            response["errors"] = ajv_response_dict["errors"]
            logger.info("Schema validator returned errors", status=400)
            return response, 400

    except RequestException:
        logger.info("AJV Schema validator service unavailable")
        return json.dumps(error="AJV Schema validator service unavailable")

    validator = QuestionnaireValidator(data)
    validator.validate()

    if len(validator.errors) > 0:
        response["errors"] = validator.errors
        logger.info("Questionnaire validator returned errors", status=400)
        response = Response(
            content=json.dumps(response),
            status_code=400
        )

        return response

    logger.info("Schema validation passed", status=200)

    response = Response(
        content=json.dumps(response),
        status_code=200
    )

    return response


if __name__ == "__main__":
    uvicorn.run(app, port=5001)
