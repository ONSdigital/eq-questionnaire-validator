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


def test_invalid_hub_and_spoke_with_summary_confirmation():
    filename = (
        "schemas/invalid/test_invalid_hub_and_spoke_with_summary_confirmation.json"
    )
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    section = questionnaire_schema.get_section("accommodation-section")
    validator = SectionValidator(section, questionnaire_schema)

    expected_errors = [
        {
            "message": SectionValidator.QUESTIONNAIRE_ONLY_ONE_PAGE,
            "section_id": "accommodation-section",
        }
    ]

    validator.validate()

    assert validator.errors == expected_errors


def test_invalid_hub_and_spoke_and_summary_confirmation_non_existent():
    filename = "schemas/invalid/test_invalid_hub_and_spoke_and_summary_confirmation_non_existent.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    section = questionnaire_schema.get_section("accommodation-section")
    validator = SectionValidator(section, questionnaire_schema)

    expected_errors = [
        {
            "section_id": "accommodation-section",
            "message": SectionValidator.QUESTIONNAIRE_MUST_CONTAIN_PAGE,
        }
    ]

    validator.validate()

    assert validator.errors == expected_errors
