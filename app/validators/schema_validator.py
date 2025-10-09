import itertools
from json import load
from pathlib import Path
from typing import Callable, Mapping, Any

from jsonschema import Draft202012Validator as DraftValidator
from jsonschema import ValidationError
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource

from app.validators.validator import Validator

WEAK_MATCHES: frozenset[str] = frozenset(["anyOf", "oneOf"])
STRONG_MATCHES: frozenset[str] = frozenset()


class SchemaFileValidator(Validator):
    """
    Validates JSON data against a schema, resolving $ref references.

    Args:
        schema (str): The path to the schema file.
        schema_element (dict): The JSON schema to validate.

    Notes:
        This class loads in a schema file, builds a reference registry
        for resolving $ref links. And Validates schema using Draft202012
        validator rules.
    """
    def __init__(self, schema_element: dict, schema: str ="schemas/questionnaire_v1.json"):
        super().__init__(schema_element)

        with open(schema, encoding="utf8") as schema_data:
            self.schema: Mapping[str, Any] = load(schema_data)

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


# Override: function (by_relevance, best_match) from jsonschema.exceptions v4.25.1
# Reason: Default best_match() did not handle anyOf/oneOf errors needed for our schema
# custom by_relevance + best_match() ensured nested and weak/strong matches are correctly
# prioritised to give the most relevant validation error.

def by_relevance(
    weak: frozenset[str] = WEAK_MATCHES, strong: frozenset[str] = STRONG_MATCHES
) -> Callable[[ValidationError], tuple[int, bool, bool]]:
    """
    Return a function that orders validation errors by relevance.

    Args:
        weak (frozenset[str]): A set of validator names that are considered weak matches.
        strong (frozenset[str]): A set of validator names that are considered strong matches.

    Returns:
        relevance (function): A function that can be used as a key for sorting validation errors.

    Notes:
        Errors that occur deeper in the schema are considered more relevant.
        Errors from weaker keywords like 'anyOf' or 'oneOf' are given lower priority.
    """

    def relevance(error: ValidationError) -> tuple[int, bool, bool]:
        validator = error.validator
        return -len(error.path), validator not in weak, validator in strong

    return relevance


def best_match(errors: list[ValidationError]) -> None | ValidationError:
    """
    Return the most relevant validation error from a list of errors.

    Args:
        errors (list<ValidationError>): A list of validation errors.

    Returns:
        None: If there are no errors.
        best (ValidationError): The most relevant ValidationError.

    Notes:
        Uses the given key function by_relevance() to choose the most specific error.
        If the error has nested context errors (anyOf, oneOf), it will pick the deepest errors,
        based on the same key function.
    """
    errors = iter(errors)
    best = next(errors, None)
    if best is None:
        return None

    key = by_relevance()
    best = max(itertools.chain([best], errors), key=key)

    while best.context:
        best = min(best.context, key=key)
    return best
