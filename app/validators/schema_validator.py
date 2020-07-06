import glob
from json import load

from jsonschema import Draft7Validator, ValidationError, RefResolver
from jsonschema.exceptions import best_match, SchemaError

from app.validators.validator import Validator


class SchemaValidator(Validator):
    def __init__(self, schema_element=None):
        super().__init__(schema_element)

        with open("schemas/questionnaire_v1.json", encoding="utf8") as schema_data:
            self.schema = load(schema_data)

        resolver = RefResolver(
            base_uri="https://eq.ons.gov.uk/",
            referrer=self.schema,
            store=self.lookup_ref_store(),
        )
        self.schema_validator = Draft7Validator(self.schema, resolver=resolver)

    @staticmethod
    def lookup_ref_store():
        store = {}
        for glob_path in [
            "schemas/**/**/*.json",
            "schemas/**/*.json",
            "schemas/*.json",
        ]:
            for filename in glob.glob(glob_path):
                with open(filename) as schema_file:
                    json_data = load(schema_file)
                    store[json_data["$id"]] = json_data
        return store

    def validate(self):
        try:
            self.schema_validator.validate(self.schema_element)
            return {}
        except ValidationError as e:
            match = best_match([e])
            path = "/".join([str(path_element) for path_element in e.path])
            self.add_error(match.message, verbose=e.message, pointer=f"/{path}")
        except SchemaError as e:
            self.add_error(e)
        return self.errors
