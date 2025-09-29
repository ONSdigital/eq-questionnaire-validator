import itertools
from json import load
from pathlib import Path

from jsonschema import Draft202012Validator as DraftValidator
from jsonschema import ValidationError
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource

from app.validators.validator import Validator


class SchemaValidator(Validator):
    def __init__(self, schema_element, schema="schemas/questionnaire_v1.json"):
        super().__init__(schema_element)

        with open(schema, encoding="utf8") as schema_data:
            self.schema = load(schema_data)

        registry = (
            Registry().with_resources(pairs=self.lookup_ref_store().items()).crawl()
        )

        self.schema_validator = DraftValidator(self.schema, registry=registry)

    @staticmethod
    def lookup_ref_store():
        store = {}

        for filename in Path("schemas").rglob("*.json"):
            with open(filename, encoding="utf8") as schema_file:
                json_data = load(schema_file)
                resource = Resource.from_contents(json_data)
                store[json_data["$id"]] = resource
        return store

    def validate(self):
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

# Utility functions adapted from jsonschema (MIT License)

WEAK_MATCHES: frozenset[str] = frozenset(["anyOf", "oneOf"])
STRONG_MATCHES: frozenset[str] = frozenset()

def by_relevance(weak=WEAK_MATCHES, strong=STRONG_MATCHES):
    def relevance(error):
        validator = error.validator
        return -len(error.path), validator not in weak, validator in strong
    return relevance

def best_match(errors, key=by_relevance()):
    errors = iter(errors)
    best = next(errors, None)
    if best is None:
        return
    best = max(itertools.chain([best], errors), key=key)

    while best.context:
        best = min(best.context, key=key)
    return best






