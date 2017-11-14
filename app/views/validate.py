import urllib

import json
from json import JSONDecodeError

from flask import Blueprint, request, jsonify, Response

from app.validation.validator import Validator

validate_blueprint = Blueprint('validate', __name__)

validator = Validator()


@validate_blueprint.route('/validate', methods=['POST'])
def validate_schema_request_body():
    return validate_schema(request.data.decode())


@validate_blueprint.route('/validate', methods=['GET'])
def validate_schema_from_url():
    values = request.args
    if 'url' in values:
        try:
            with urllib.request.urlopen(values['url']) as url:
                return validate_schema(url.read().decode())
        except urllib.error.URLError:
            return Response(status=404, response='Could not load schema at URL [{}]'.format(values['url']))


def validate_schema(data):
    try:
        json_to_validate = json.loads(data)
    except JSONDecodeError:
        return Response(status=400, response='Could not parse JSON')

    response = {}

    errors = validator.validate_schema(json_to_validate)

    if errors:
        response['errors'] = errors

    return jsonify(response), 200
