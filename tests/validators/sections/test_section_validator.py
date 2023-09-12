from app import error_messages
from app.validators.blocks import BlockValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.sections.section_validator import SectionValidator
from tests.utils import _open_and_load_schema_file


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


def test_invalid_section_summary_items():
    filename = "schemas/invalid/test_invalid_list_collector_section_summary_items.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    section = questionnaire_schema.get_section("section-companies")
    validator = SectionValidator(section, questionnaire_schema)

    expected_errors = [
        {
            "message": "Section cannot contain multiple ListCollector blocks with a "
            "summary showing non-item answers",
            "section_id": "section-companies",
        },
        {
            "id": "any-companies-or-branches-answer",
            "message": "Item anchor answer id 'any-companies-or-branches-answer' not "
            "present in any list collector for list name 'companies'",
            "section_id": "section-companies",
        },
        {
            "id": "any-companies-or-branches-answer",
            "message": "Related_answers id not present in any list collector",
            "section_id": "section-companies",
        },
        {
            "id": "any-companies-or-branches-answer",
            "message": "No label found for answer 'any-companies-or-branches-answer', "
            "only answers that support labels can be used as related answers",
            "section_id": "section-companies",
        },
    ]

    validator.validate()

    assert validator.errors == expected_errors


def test_invalid_list_collector_repeating_blocks_validated_from_section_validator():
    filename = "schemas/invalid/test_invalid_list_collector_repeating_blocks_placeholder_references_same_block.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    section = questionnaire_schema.get_section("section-companies")
    validator = SectionValidator(section, questionnaire_schema)
    validator.validate()

    expected_errors = [
        {
            "block_id": "companies-repeating-block-1",
            "identifier": "registration-number",
            "message": BlockValidator.PLACEHOLDER_ANSWER_SELF_REFERENCE,
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_multiple_list_collectors_when_summary_with_items_enabled():
    filename = (
        "schemas/invalid/test_invalid_multiple_list_collectors_with_summary_items.json"
    )

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    section = questionnaire_schema.get_section("section-companies")
    validator = SectionValidator(section, questionnaire_schema)
    validator.validate()

    expected_errors = [
        {
            "for_list": "companies",
            "section_id": "section-companies",
            "message": error_messages.MULTIPLE_LIST_COLLECTORS_WITH_SUMMARY_ENABLED,
        }
    ]
    assert expected_errors == validator.errors


def test_invalid_repeating_section_for_non_existent_list():
    """
    Tests that you cannot have a repeating section with a for_list that is not from either:
    1) a standard list collector
    2) the supplementary lists property for the schema
    """
    filename = "schemas/invalid/test_invalid_supplementary_data_list_collector.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = SectionValidator(
        questionnaire_schema.get_section("section-4"),
        questionnaire_schema,
    )
    validator.validate()

    expected_errors = [
        {
            "message": error_messages.FOR_LIST_NEVER_POPULATED,
            "section_id": "section-4",
            "list_name": "employees",
        }
    ]

    assert expected_errors == validator.errors
