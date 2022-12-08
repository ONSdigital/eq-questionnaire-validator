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


def test_section_summary_items_fields_missing():
    filename = "schemas/invalid/test_invalid_list_collector_section_summary_fields_missing.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    section = questionnaire_schema.get_section("section")
    validator = SectionValidator(section, questionnaire_schema)

    expected_errors = [
        {"message": "Items field not present for summary", "section_id": "section"}
    ]

    validator.validate()

    assert validator.errors == expected_errors


def test_invalid_section_summary_items():
    filename = "schemas/invalid/test_invalid_list_collector_section_summary_items.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    section = questionnaire_schema.get_section("section-companies")
    validator = SectionValidator(section, questionnaire_schema)

    expected_errors = [
        {"message": "Section has multiple lists", "section_id": "section-companies"},
        {
            "message": "Section has multiple ListCollector blocks",
            "section_id": "section-companies",
        },
        {
            "id": "any-companies-or-branches-answer",
            "message": "Related_answers id not present in any list collector",
            "section_id": "section-companies",
        },
        {
            "id": "any-companies-or-branches-answer",
            "message": "Item anchor answer id not present in any list collector",
            "section_id": "section-companies",
        },
        {
            "id": "any-companies-or-branches-answer",
            "message": "No label found for any-companies-or-branches-answer, only "
            "answers that support labels can be used as related answers",
            "section_id": "section-companies",
        },
    ]

    validator.validate()

    assert validator.errors == expected_errors
