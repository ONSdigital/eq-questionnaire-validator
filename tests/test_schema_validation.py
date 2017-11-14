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

        json_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), file), encoding='utf8')
        json_to_validate = load(json_file)

        error = self.validator.validate_schema(json_to_validate)

        self.assertTrue('message' in error, 'This schema should fail with an invalid block')

    def test_invalid_schema_group(self):

        file = 'schemas/test_invalid_routing_group.json'

        json_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), file), encoding='utf8')
        json_to_validate = load(json_file)

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
