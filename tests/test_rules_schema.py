from json import load

from structlog import configure
from structlog import getLogger
from structlog.stdlib import LoggerFactory

from app.validators.schema_validator import SchemaValidator

logger = getLogger()

configure(logger_factory=LoggerFactory())


def test_param_valid_schemas(rule_schema_filename):
    """
    Uses py.test generated tests to validate all schemas contained in the 'rules' folder.
    """
    with open(rule_schema_filename, encoding="utf8") as json_file:
        for json_fixture in load(json_file):
            schema_validator = SchemaValidator(
                json_fixture["rule"], schema="schemas/rules/rule.json"
            )
            schema_validator.validate()

            assert not schema_validator.errors
