from json import load

import pytest
from structlog import configure, getLogger
from structlog.stdlib import LoggerFactory

from app.validators.schema_validator import SchemaValidator
from tests.conftest import find_all_json_files

logger = getLogger()

configure(logger_factory=LoggerFactory())


def _assert_schema_is_valid(valid_schema_filename, *, json_schema_definition_filepath):
    with open(valid_schema_filename, encoding="utf8") as json_file:
        for json_fixture in load(json_file):
            schema_validator = SchemaValidator(
                json_fixture["rule"], schema=json_schema_definition_filepath
            )
            schema_validator.validate()

            if schema_validator.errors:
                schema_validator.validate()

            assert not schema_validator.errors


@pytest.mark.parametrize(
    "valid_schema_filename", find_all_json_files("tests/schemas/rules/boolean")
)
def test_param_valid_schemas_boolean_operators(valid_schema_filename):
    """
    Uses py.test generated tests to validate all schemas contained in the 'rules/boolean' folder.
    """
    _assert_schema_is_valid(
        valid_schema_filename,
        json_schema_definition_filepath="schemas/rules/boolean_rule.json",
    )


@pytest.mark.parametrize(
    "valid_schema_filename", find_all_json_files("tests/schemas/rules/value")
)
def test_param_valid_schemas_value_operators(valid_schema_filename):
    """
    Uses py.test generated tests to validate all schemas contained in the 'rules/value' folder.
    """
    _assert_schema_is_valid(
        valid_schema_filename,
        json_schema_definition_filepath="schemas/rules/value_rule.json",
    )
