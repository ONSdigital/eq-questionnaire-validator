"""This code defines a SchemaValidator class that validates a schema element against a JSON schema."""

import glob
from json import load

from jsonschema import Draft202012Validator as DraftValidator
from jsonschema import RefResolver, ValidationError
from jsonschema.exceptions import SchemaError, best_match

from app.validators.validator import Validator


class SchemaValidator(Validator):
    """Validates a schema element against a JSON schema."""

    def __init__(self, schema_element, schema="schemas/questionnaire_v1.json"):
        """Initializes the SchemaValidator with a schema element and a JSON schema."""
        super().__init__(schema_element)

        with open(schema, encoding="utf8") as schema_data:
            self.schema = load(schema_data)

        resolver = RefResolver(
            base_uri="",
            referrer=self.schema,
            store=self.lookup_ref_store(),
        )
        self.schema_validator = DraftValidator(self.schema, resolver=resolver)

    @staticmethod
    def lookup_ref_store():
        """Looks up the reference store for JSON schema."""
        store = {}
        for glob_path in [
            "schemas/**/**/**/*.json",
            "schemas/**/**/*.json",
            "schemas/**/*.json",
            "schemas/*.json",
        ]:
            for filename in glob.glob(glob_path):
                with open(filename, encoding="utf8") as schema_file:
                    json_data = load(schema_file)
                    store[json_data["$id"]] = json_data
        return store

    def validate(self):
        """Validates the schema element against the JSON schema."""
        try:
            self.schema_validator.validate(self.schema_element)
            return {}
        except ValidationError as e:
            match = best_match([e])
            path = "/".join(str(path_element) for path_element in e.path)
            error = {
                "reason": e.message.replace(str(e.instance), "").strip(),
                "json": e.instance,
            }
            self.add_error(match.message, verbose=error, pointer=f"/{path}")
        except SchemaError as e:
            self.add_error(e)
        return self.errors
