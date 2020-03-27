import json

from jsonschema import RefResolver, validators

from app.validation.questionnaire_validator import QuestionnaireValidator


def test_schema():
    with open("schemas/questionnaire_v1.json", encoding="utf8") as schema_data:
        schema = json.load(schema_data)
        resolver = RefResolver(
            base_uri="https://eq.ons.gov.uk/",
            referrer=schema,
            store=QuestionnaireValidator.lookup_ref_store(),
        )

        validator = validators.validator_for(schema)
        validator.resolver = resolver
        validator.check_schema(schema)
