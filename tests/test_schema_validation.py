import os
import unittest
from json import load

from structlog import configure
from structlog import getLogger
from structlog.stdlib import LoggerFactory

from app.validation.validator import Validator

logger = getLogger()

configure(logger_factory=LoggerFactory())


class TestSchemaValidation(unittest.TestCase):

    def setUp(self):
        self.validator = Validator()

    def test_invalid_schema_block(self):
        file = 'schemas/test_invalid_routing_block.json'
        json_to_validate = self.open_and_load_schema_file(file)

        error = self.validator.validate_schema(json_to_validate)

        self.assertTrue('message' in error, 'This schema should fail with an invalid block')

    def test_invalid_schema_group(self):

        file = 'schemas/test_invalid_routing_group.json'
        json_to_validate = self.open_and_load_schema_file(file)

        error = self.validator.validate_schema(json_to_validate)

        self.assertTrue('message' in error, 'This schema should fail with an invalid block')

    def test_schemas(self):

        errors = []

        files = self.all_schema_files()

        for file in files:
            with open(file, encoding='utf8') as json_file:
                json_to_validate = load(json_file)

                errors.extend(self.validator.validate_schema(json_to_validate))

        if errors:
            for error in errors:
                logger.error(error)

    def test_invalid_numeric_answers(self):

        file = 'schemas/test_invalid_numeric_answers.json'
        json_to_validate = self.open_and_load_schema_file(file)

        errors = self.validator.validate_numeric_answer_types(json_to_validate)
        self.assertEqual(len(errors), 8)
        self.assertEqual(errors[0]['message'], 'Schema Integrity Error. Invalid range of min = 0 and max = -1.0 is possible for answer "answer-2".')
        self.assertEqual(errors[1]['message'], 'Schema Integrity Error. The referenced answer "answer-1" has a greater number of decimal places than answer "answer-2"')
        self.assertEqual(errors[2]['message'], 'Schema Integrity Error. The referenced answer "answer-4" can not be used to set the minimum of answer "answer-3"')
        self.assertEqual(errors[3]['message'], 'Schema Integrity Error. The referenced answer "answer-5" can not be used to set the maximum of answer "answer-3"')
        self.assertEqual(errors[4]['message'], 'Schema Integrity Error. Minimum value -99999999999 for answer "answer-4" is less than system limit of -999999999')
        self.assertEqual(errors[5]['message'], 'Schema Integrity Error. Maximum value 99999999999 for answer "answer-4" is greater than system limit of 9999999999')
        self.assertEqual(errors[6]['message'], 'Schema Integrity Error. Number of decimal places 10 for answer "answer-5" is greater than system limit of 6')
        self.assertEqual(errors[7]['message'], 'Schema Integrity Error. The referenced answer "answer-1" has a greater number of decimal places than answer "answer-6"')


    @staticmethod
    def open_and_load_schema_file(file):
        json_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), file), encoding='utf8')
        json_to_validate = load(json_file)

        return json_to_validate

    @staticmethod
    def all_schema_files():
        schema_files = []
        for folder, _, files in os.walk('schemas'):
            for filename in files:
                if filename.endswith('.json'):
                    schema_files.append(os.path.join(folder, filename))
        return schema_files


if __name__ == '__main__':
    unittest.main()
