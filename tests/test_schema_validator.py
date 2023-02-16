import json

from jsonschema import RefResolver, validators

from app.validators.schema_validator import SchemaValidator
from tests.test_questionnaire_validator import _open_and_load_schema_file


def create_schema_with_answer_id(answer_id):
    """
    Utility method that loads a JSON schema file and swaps out an answer Id.
    :param answer_id: The Id to use for the answer.
    :return: The JSON file with the Id swapped for schema_id
    """
    schema_path = "tests/schemas/valid/test_schema_id_regex.json"

    with open(schema_path, encoding="utf8") as json_data:
        json_content = json.load(json_data)

        json_content["sections"][0]["groups"][0]["blocks"][0]["question"]["answers"][0][
            "id"
        ] = answer_id
        return json_content


def test_valid_answer_ids():
    answer_ids = ["star-wars", "name-with-hyphens", "this-is-a-valid-id-0", "answer"]

    for answer_id in answer_ids:
        json_to_validate = create_schema_with_answer_id(answer_id)
        validator = SchemaValidator(json_to_validate)
        validator.validate()

        assert len(validator.errors) == 0


def test_invalid_answer_ids():
    answer_ids = [
        "!n0t-@-valid-id",
        "NOT-A-VALID-ID",
        "not_a_valid_id",
        "not a valid id",
    ]

    for answer_id in answer_ids:
        json_to_validate = create_schema_with_answer_id(answer_id)
        validator = SchemaValidator(json_to_validate)
        validator.validate()

        expected_message = f"'{answer_id}' does not match"

        assert expected_message in validator.errors[0]["message"]


def test_schema():
    with open("schemas/questionnaire_v1.json", encoding="utf8") as schema_data:
        schema = json.load(schema_data)
        resolver = RefResolver(
            base_uri="https://eq.ons.gov.uk/",
            referrer=schema,
            store=SchemaValidator.lookup_ref_store(),
        )

        validator = validators.validator_for(schema)
        validator.resolver = resolver
        validator.check_schema(schema)


def test_single_variant_invalid():
    file_name = "schemas/invalid/test_invalid_single_variant.json"

    validator = SchemaValidator(_open_and_load_schema_file(file_name))
    validator.validate()

    assert validator.errors[0]["message"] == "'when' is a required property"

    assert len(validator.errors) == 1


def test_invalid_survey_id_whitespace():
    file = "schemas/invalid/test_invalid_survey_id_whitespace.json"
    json_to_validate = _open_and_load_schema_file(file)

    validator = SchemaValidator(json_to_validate)

    validator.validate()

    assert validator.errors[0]["message"] == "'lms ' does not match '^[0-9a-z]+$'"


def test_returns_pointer():
    file = "schemas/invalid/test_invalid_survey_id_whitespace.json"
    json_to_validate = _open_and_load_schema_file(file)

    validator = SchemaValidator(json_to_validate)

    validator.validate()

    assert validator.errors[0]["pointer"] == "/survey_id"


def test_invalid_q_code_regex_pattern():
    file = "schemas/invalid/test_invalid_q_code_regex_pattern.json"
    json_to_validate = _open_and_load_schema_file(file)

    validator = SchemaValidator(json_to_validate)

    validator.validate()

    assert (
        validator.errors[0]["message"]
        == "'&*fgh er*R' does not match '^[a-zA-Z0-9._-]+$'"
    )
