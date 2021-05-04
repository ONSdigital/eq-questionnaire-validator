from app import error_messages
from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.sections.section_validator import SectionValidator
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_list_reference_in_custom_summary():
    filename = "schemas/invalid/test_invalid_custom_list_summary.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    section = questionnaire_schema.get_section("section")
    validator = SectionValidator(section, questionnaire_schema)

    expected_errors = [
        {
            "message": error_messages.FOR_LIST_NEVER_POPULATED,
            "list_name": "household",
            "section_id": "section",
        }
    ]

    validator.validate()

    assert validator.errors == expected_errors
