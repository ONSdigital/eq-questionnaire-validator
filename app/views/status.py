from flask import Blueprint, Response

status_blueprint = Blueprint("status", __name__)


@status_blueprint.route("/status", methods=["GET"])
def validate_schema():
    return Response(status=200)
