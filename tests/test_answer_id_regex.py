import json

from app.validation.validator import Validator

validator = Validator()


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
        schema_errors = validator.validate_json_schema(json_to_validate)

        assert schema_errors == {}


def test_invalid_answer_ids():
    answer_ids = [
        "!n0t-@-valid-id",
        "NOT-A-VALID-ID",
        "not_a_valid_id",
        "not a valid id",
    ]

    for answer_id in answer_ids:
        json_to_validate = create_schema_with_answer_id(answer_id)
        schema_errors = validator.validate_json_schema(json_to_validate)

        expected_message = f"'{answer_id}' does not match"

        assert expected_message in schema_errors.get("predicted_cause")
