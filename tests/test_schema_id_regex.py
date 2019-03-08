import json

from app.validation.validator import Validator

validator = Validator()


def create_schema_with_id(schema_id='answer'):
    """
    Utility method that loads a JSON schema file and swaps out an answer Id.
    :param schema_id: The Id to use for the answer.
    :return: The JSON file with the Id swapped for schema_id
    """
    schema_path = 'tests/schemas/valid/test_schema_id_regex.json'

    with open(schema_path, encoding='utf8') as json_data:
        json_content = json.load(json_data)

        json_content['sections'][0]['groups'][0]['blocks'][0]['question']['answers'][0]['id'] = schema_id
        return json_content


def validate_schema(json_to_validate):
    errors = validator.validate_schema(json_to_validate)
    validation_errors = errors['validation_errors']
    schema_errors = errors['schema_errors']

    return validation_errors, schema_errors


def assert_schema_is_valid(json_to_validate):
    validation_errors, schema_errors = validate_schema(json_to_validate)

    assert validation_errors == []
    assert schema_errors == {}


def test_default_id_should_pass_validation():
    json_to_validate = create_schema_with_id()

    assert_schema_is_valid(json_to_validate)


def test_guid_should_pass_validation():
    json_to_validate = create_schema_with_id('star-wars')

    assert_schema_is_valid(json_to_validate)


def test_id_with_hyphenated_names_should_pass_validation():
    json_to_validate = create_schema_with_id('name-with-hyphens')

    assert_schema_is_valid(json_to_validate)


def test_id_with_numeric_should_pass_validation():
    json_to_validate = create_schema_with_id('this-is-a-valid-id-0')

    assert_schema_is_valid(json_to_validate)


def test_id_with_numeric_at_start_should_pass_validation():
    json_to_validate = create_schema_with_id('0-this-is-a-valid-id-0')

    assert_schema_is_valid(json_to_validate)


def test_id_with_punctuation_should_fail_validation():
    json_to_validate = create_schema_with_id('!n0t-@-valid-id')

    validation_errors, schema_errors = validate_schema(json_to_validate)

    assert 'is not valid under any of the given schemas' in schema_errors.get('message')
    assert validation_errors == []


def test_id_with_spaces_should_fail_validation():
    json_to_validate = create_schema_with_id('not a valid id')

    validation_errors, schema_errors = validate_schema(json_to_validate)

    assert 'is not valid under any of the given schemas' in schema_errors.get('message')
    assert validation_errors == []


def test_id_with_capital_letters_should_fail_validation():
    json_to_validate = create_schema_with_id('NOT-A-VALID-ID')

    validation_errors, schema_errors = validate_schema(json_to_validate)

    assert 'is not valid under any of the given schemas' in schema_errors.get('message')
    assert validation_errors == []


def test_id_with_underscores_should_pass_validation():
    json_to_validate = create_schema_with_id('not_a_valid_id')

    validation_errors, schema_errors = validate_schema(json_to_validate)

    assert 'is not valid under any of the given schemas' in schema_errors.get('message')

    assert validation_errors == []
