import json
import unittest

from app.validation.validator import Validator


def create_schema_with_id(schema_id='answer'):
    """
    Utility method that loads a JSON schema file and swaps out an answer Id.
    :param schema_id: The Id to use for the answer.
    :return: The JSON file with the Id swapped for schema_id
    """
    schema_path = 'tests/schemas/test_schema_id_regex.json'

    with open(schema_path, encoding='utf8') as json_data:
        json_content = json.load(json_data)

        json_content['sections'][0]['groups'][0]['blocks'][0]['questions'][0]['answers'][0]['id'] = schema_id
        return json_content


class TestSchemaIdRegEx(unittest.TestCase):

    def setUp(self):
        self.validator = Validator()
        self.errors = []

    def test_default_id_should_pass_validation(self):
        # Given
        json_to_validate = create_schema_with_id()

        # When
        errors = self.validator.validate_schema(json_to_validate)

        # Then
        self.assertEqual(len(errors), 0, errors)

    def test_guid_should_pass_validation(self):
        # Given
        json_to_validate = create_schema_with_id('star-wars')

        # When
        errors = self.validator.validate_schema(json_to_validate)

        # Then
        self.assertEqual(len(errors), 0, errors)

    def test_id_with_hyphenated_names_should_pass_validation(self):
        # Given
        json_to_validate = create_schema_with_id('name-with-hyphens')

        # When
        errors = self.validator.validate_schema(json_to_validate)

        # Then
        self.assertEqual(len(errors), 0, errors)

    def test_id_with_numeric_should_pass_validation(self):
        # Given
        json_to_validate = create_schema_with_id('this-is-a-valid-id-0')

        # When
        errors = self.validator.validate_schema(json_to_validate)

        # Then
        self.assertEqual(len(errors), 0, errors)

    def test_id_with_numeric_at_start_should_pass_validation(self):
        # Given
        json_to_validate = create_schema_with_id('0-this-is-a-valid-id-0')

        # When
        errors = self.validator.validate_schema(json_to_validate)

        # Then
        self.assertEqual(len(errors), 0, errors)

    def test_id_with_punctuation_should_fail_validation(self):
        # Given
        json_to_validate = create_schema_with_id('!n0t-@-valid-id')

        # When
        error = self.validator.validate_schema(json_to_validate)

        # Then
        self.assertTrue(isinstance(error, dict))
        self.assertTrue('is not valid under any of the given schemas' in error['message'])

    def test_id_with_spaces_should_fail_validation(self):
        # Given
        json_to_validate = create_schema_with_id('not a valid id')

        # When
        error = self.validator.validate_schema(json_to_validate)

        # Then
        self.assertTrue(isinstance(error, dict))
        self.assertTrue('is not valid under any of the given schemas' in error['message'])

    def test_id_with_capital_letters_should_fail_validation(self):
        # Given
        json_to_validate = create_schema_with_id('NOT-A-VALID-ID')

        # When
        error = self.validator.validate_schema(json_to_validate)

        # Then
        self.assertTrue(isinstance(error, dict))
        self.assertTrue('is not valid under any of the given schemas' in error['message'])

    def test_id_with_underscores_should_pass_validation(self):
        # Given
        json_to_validate = create_schema_with_id('not_a_valid_id')

        # When
        error = self.validator.validate_schema(json_to_validate)

        # Then
        self.assertTrue(isinstance(error, dict))
        self.assertTrue('is not valid under any of the given schemas' in error['message'])
