import urllib

import json
from json import JSONDecodeError

from flask import Blueprint, request, jsonify, Response
from structlog import get_logger

from app.validation.validator import Validator

logger = get_logger()

validate_blueprint = Blueprint('validate', __name__)

validator = Validator()


@validate_blueprint.route('/validate', methods=['POST'])
def validate_schema_request_body():
    logger.info('Validating schema')
    return validate_schema(request.data.decode())


@validate_blueprint.route('/validate', methods=['GET'])
def validate_schema_from_url():
    values = request.args
    if 'url' in values:
        logger.info('Validating schema from URL', url=values['url'])
        try:
            with urllib.request.urlopen(values['url']) as url:
                return validate_schema(url.read().decode())
        except urllib.error.URLError:
            return Response(status=404, response='Could not load schema at URL [{}]'.format(values['url']))


def validate_schema(data):
    try:
        json_to_validate = json.loads(data)
    except JSONDecodeError:
        logger.info('Could not parse JSON', status=400)
        return Response(status=400, response='Could not parse JSON')

    response = {}

    errors = validator.validate_schema(json_to_validate)

    if errors:
        response['errors'] = errors
        logger.info('Schema validator returned errors', status=400)
        return jsonify(response), 400

    logger.info('Schema validation passed', status=200)
    return jsonify(response), 200
