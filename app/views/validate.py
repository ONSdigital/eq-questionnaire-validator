import json
import os
import urllib
from json import JSONDecodeError

import requests
from flask import Blueprint, Response, jsonify, request
from requests import RequestException
from structlog import get_logger

from app.validators.questionnaire_validator import QuestionnaireValidator

logger = get_logger()

validate_blueprint = Blueprint("validate", __name__)

AJV_HOST = os.getenv("AJV_HOST", "localhost")

AJV_VALIDATOR_URL = f"http://{AJV_HOST}:5002/validate"


@validate_blueprint.route("/validate", methods=["POST"])
def validate_schema_request_body():
    logger.info("Validating schema")
    return validate_schema(request.data.decode())


@validate_blueprint.route("/validate", methods=["GET"])
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


def validate_schema(data):
    try:
        json_to_validate = json.loads(data)
    except JSONDecodeError:
        logger.info("Could not parse JSON", status=400)
        return Response(status=400, response="Could not parse JSON")

    response = {}
    try:
        ajv_response = requests.post(
            AJV_VALIDATOR_URL, json=json_to_validate, timeout=10
        )
        ajv_response_dict = ajv_response.json()

        if ajv_response_dict:
            response["errors"] = ajv_response_dict["errors"]
            logger.info("Schema validator returned errors", status=400)
            return jsonify(response), 400

    except RequestException:
        logger.info("AJV Schema validator service unavailable")
        return jsonify(error="AJV Schema validator service unavailable")

    validator = QuestionnaireValidator(json_to_validate)
    validator.validate()

    if len(validator.errors) > 0:
        response["errors"] = validator.errors
        logger.info("Questionnaire validator returned errors", status=400)
        return jsonify(response), 400

    logger.info("Schema validation passed", status=200)

    return jsonify(response), 200
