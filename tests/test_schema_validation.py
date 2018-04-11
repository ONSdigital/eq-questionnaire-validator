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

        errors = self.validator.validate_schema(json_to_validate)

        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0]['message'],
            'Schema Integrity Error. Routing rule routes to invalid block [invalid-location]')

    def test_invalid_schema_group(self):

        file = 'schemas/test_invalid_routing_group.json'
        json_to_validate = self.open_and_load_schema_file(file)

        errors = self.validator.validate_schema(json_to_validate)

        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0]['message'],
            'Schema Integrity Error. Routing rule routes to invalid group [invalid-group]')

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

        errors = self.validator.validate_schema(json_to_validate)
        self.assertEqual(len(errors), 9)
        self.assertEqual(
            errors[0]['message'],
            'Schema Integrity Error. Invalid range of min = 0 and max = -1.0 is possible for answer "answer-2".')
        self.assertEqual(
            errors[1]['message'],
            'Schema Integrity Error. The referenced answer "answer-1" has a greater number of decimal places than '
            'answer "answer-2"')
        self.assertEqual(
            errors[2]['message'],
            'Schema Integrity Error. The referenced answer "answer-4" can not be used to set the minimum of answer '
            '"answer-3"')
        self.assertEqual(
            errors[3]['message'],
            'Schema Integrity Error. The referenced answer "answer-5" can not be used to set the maximum of answer '
            '"answer-3"')
        self.assertEqual(
            errors[4]['message'],
            'Schema Integrity Error. Minimum value -99999999999 for answer "answer-4" is less than system limit of '
            '-999999999')
        self.assertEqual(
            errors[5]['message'],
            'Schema Integrity Error. Maximum value 99999999999 for answer "answer-4" is greater than system limit of '
            '9999999999')
        self.assertEqual(
            errors[6]['message'],
            'Schema Integrity Error. Number of decimal places 10 for answer "answer-5" is greater than system limit '
            'of 6')
        self.assertEqual(
            errors[7]['message'],
            'Schema Integrity Error. The referenced answer "answer-1" has a greater number of decimal places than '
            'answer "answer-6"')

        self.assertEqual(
            errors[8]['message'],
            'Schema Integrity Error. Default is being used with a mandatory answer: answer-7')

    def test_numeric_default_with_routing(self):

        file = 'schemas/test_numeric_default_with_routing.json'
        json_to_validate = self.open_and_load_schema_file(file)

        errors = self.validator.validate_schema(json_to_validate)

        self.assertEqual(len(errors), 0)

    def test_invalid_id_in_answers_to_calculate(self):

        file = 'schemas/test_invalid_id_in_grouped_answers_to_calculate.json'
        json_to_validate = self.open_and_load_schema_file(file)

        question = json_to_validate['sections'][0]['groups'][0]['blocks'][1]['questions'][0]

        errors = self.validator.validate_calculated_ids_in_answers_to_calculate_exists(question)
        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0]['message'], 'Schema Integrity Error. Answer id - breakdown-3 does not exist '
                                               'within this question - breakdown-question')
        self.assertEqual(errors[1]['message'], 'Schema Integrity Error. Answer id - breakdown-4 does not exist within '
                                               'this question - breakdown-question')

    def test_invalid_date_range_period(self):

        file = 'schemas/test_invalid_date_range_period.json'
        json_to_validate = self.open_and_load_schema_file(file)

        errors = self.validator.validate_schema(json_to_validate)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['message'], 'Schema Integrity Error. The minimum period is greater than the maximum '
                                               'period for date-range-question')

    def test_invalid_mm_yyyy_date_range_period(self):

        file = 'schemas/test_invalid_mm_yyyy_date_range_period.json'
        json_to_validate = self.open_and_load_schema_file(file)

        errors = self.validator.validate_schema(json_to_validate)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['message'], 'Schema Integrity Error. Days can not be used in period_limit '
                                               'for yyyy-mm date range for date-range-question')

    def test_invalid_single_date_period(self):

        file = 'schemas/test_invalid_single_date_min_max_period.json'
        json_to_validate = self.open_and_load_schema_file(file)

        errors = self.validator.validate_schema(json_to_validate)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['message'], 'Schema Integrity Error. The minimum offset date is greater than the '
                                               'maximum offset date')

    def test_invalid_metadata(self):
        self.skipTest('Will enable once runner PR is merged.')
        file = 'schemas/test_invalid_metadata.json'
        json_to_validate = self.open_and_load_schema_file(file)

        errors = self.validator.validate_schema(json_to_validate)

        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0]['message'], 'Schema Integrity Error. Metadata - invalid not specified in metadata field')
        self.assertEqual(errors[1]['message'], 'Schema Integrity Error. Unused metadata defined in metadata field - invalid_metadata')

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
