import json
import urllib
from json import JSONDecodeError

from flask import Blueprint, Response, jsonify, request
from structlog import get_logger

from app.validators.questionnaire_validator import QuestionnaireValidator
from app.validators.schema_validator import SchemaValidator

logger = get_logger()

validate_blueprint = Blueprint("validate", __name__)


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
            return Response(
                status=404,
                response="Could not load schema at URL [{}]".format(values["url"]),
            )


def validate_schema(data):
    try:
        json_to_validate = json.loads(data)
    except JSONDecodeError:
        logger.info("Could not parse JSON", status=400)
        return Response(status=400, response="Could not parse JSON")

    response = {}

    schema_validator = SchemaValidator(json_to_validate)
    schema_validator.validate()

    if len(schema_validator.errors) > 0:
        response["errors"] = schema_validator.errors
        logger.info("Schema validator returned errors", status=400)
        return jsonify(response), 400

    validator = QuestionnaireValidator(json_to_validate)
    validator.validate()

    if len(validator.errors) > 0:
        response["errors"] = validator.errors
        logger.info("Questionnaire validator returned errors", status=400)
        return jsonify(response), 400

    logger.info("Schema validation passed", status=200)

    return jsonify(response), 200
