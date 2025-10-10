from json import load

import pytest
from structlog import configure, getLogger
from structlog.stdlib import LoggerFactory

from app import error_messages
from app.validators.placeholders.placeholder_validator import PlaceholderValidator
from app.validators.questionnaire_validator import QuestionnaireValidator
from app.validators.questions import MutuallyExclusiveQuestionValidator
from tests.helpers.schema_validator import SchemaFileValidator
from app.validators.value_source_validator import ValueSourceValidator
from tests.conftest import find_all_json_files
from tests.utils import _open_and_load_schema_file

logger = getLogger()

configure(logger_factory=LoggerFactory())


@pytest.mark.parametrize(
    "valid_schema_filename", find_all_json_files("tests/schemas/valid")
)
def test_param_valid_schemas(valid_schema_filename):
    """
    Uses py.test generated tests to validate all schemas contained in the 'valid' folder.
    """
    with open(valid_schema_filename, encoding="utf8") as json_file:
        json_to_validate = load(json_file)

        validator = QuestionnaireValidator(json_to_validate)
        schema_validator = SchemaFileValidator(json_to_validate)

        schema_validator.validate()
        validator.validate()

        assert not validator.errors
        assert not schema_validator.errors


def test_invalid_mutually_exclusive_conditions():
    filename = "schemas/invalid/test_invalid_mutually_exclusive_conditions.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate()

    expected_errors = [
        {
            "message": MutuallyExclusiveQuestionValidator.MUTUALLY_EXCLUSIVE_CONTAINS_MANDATORY,
            "question_id": "mutually-exclusive-date-question",
        },
        {
            "message": MutuallyExclusiveQuestionValidator.INVALID_EXCLUSIVE_ANSWER,
            "answer_id": "mutually-exclusive-date-answer-2",
            "question_id": "mutually-exclusive-date-question",
        },
        {
            "message": MutuallyExclusiveQuestionValidator.NON_EXCLUSIVE_RADIO_ANSWER,
            "question_id": "mutually-exclusive-radio-question",
        },
    ]

    assert expected_errors == validator.errors


def test_invalid_string_transforms():
    filename = "schemas/invalid/test_invalid_string_transforms.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate()

    expected_errors = [
        {
            "message": PlaceholderValidator.PLACEHOLDERS_DONT_MATCH_DEFINITIONS,
            "text": "test {answer1}",
            "differences": {"answer1"},
        },
        {
            "message": PlaceholderValidator.PLACEHOLDERS_DONT_MATCH_DEFINITIONS,
            "text": "test {answer1} and {answer2}",
            "differences": {"answer2"},
        },
        {
            "message": PlaceholderValidator.FIRST_TRANSFORM_CONTAINS_PREVIOUS_TRANSFORM_REF
        },
        {"message": PlaceholderValidator.NO_PREVIOUS_TRANSFORM_REF_IN_CHAIN},
    ]

    assert validator.errors == expected_errors


def test_invalid_placeholder_answer_ids():
    filename = "schemas/invalid/test_invalid_placeholder_source_ids.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate()

    expected_errors = [
        {
            "identifier": "invalid-answer0",
            "message": ValueSourceValidator.ANSWER_SOURCE_REFERENCE_INVALID,
        },
        {
            "message": ValueSourceValidator.ANSWER_SOURCE_REFERENCE_INVALID,
            "identifier": "invalid-answer0",
            "json_path": "groups.[0].blocks.[0].question.answers.[1].description.placeholders.[0].value.identifier",
        },
        {
            "message": ValueSourceValidator.ANSWER_SOURCE_REFERENCE_INVALID,
            "identifier": "invalid-answer1",
            "json_path": "groups.[0].blocks.[1].question.answers.[1].description.placeholders.[0].transforms.[0].arguments.number.identifier",
        },
        {
            "message": ValueSourceValidator.SOURCE_REFERENCE_INVALID.format("metadata"),
            "identifier": "invalid-metadata-ref",
            "json_path": "groups.[0].blocks.[3].question.answers.[0].description.placeholders.[0].value.identifier",
        },
    ]
    assert validator.errors == expected_errors


def test_single_variant_invalid():
    file_name = "schemas/invalid/test_invalid_single_variant.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(file_name))
    validator.validate()

    assert {
        "message": error_messages.VARIANTS_HAS_ONE_VARIANT,
        "section_id": "section",
        "block_id": "block-2",
    } in validator.errors


def test_duplicate_answer_ids():
    filename = "schemas/invalid/test_invalid_duplicate_ids.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate_duplicates()

    expected_errors = [
        {"message": error_messages.DUPLICATE_ID_FOUND, "id": "block-1"},
        {"message": error_messages.DUPLICATE_ID_FOUND, "id": "answer-2"},
        {"message": error_messages.DUPLICATE_ID_FOUND, "id": "question-1"},
        {"message": error_messages.DUPLICATE_ID_FOUND, "id": "block-2"},
        {"message": error_messages.DUPLICATE_ID_FOUND, "id": "block-and-question"},
    ]

    assert all(
        {expected_error in validator.errors for expected_error in expected_errors}
    )


def test_inconsistent_ids_in_variants():
    file_name = "schemas/invalid/test_invalid_inconsistent_ids_in_variants.json"
    json_to_validate = _open_and_load_schema_file(file_name)

    validator = QuestionnaireValidator(json_to_validate)
    validator.validate()

    assert [
        {
            "message": error_messages.VARIANTS_HAVE_DIFFERENT_ANSWER_LIST_LENGTHS,
            "block_id": "block-2",
            "section_id": "section",
        },
        {
            "message": error_messages.VARIANTS_HAVE_DIFFERENT_QUESTION_IDS,
            "block_id": "block-2",
            "section_id": "section",
            "question_ids": {"question-2", "question-2-variant"},
        },
        {
            "message": error_messages.VARIANTS_HAVE_MISMATCHED_ANSWER_IDS,
            "block_id": "block-2",
            "section_id": "section",
            "answer_ids": {"answer-2", "answer-2-variant", "answer-3"},
        },
    ] == validator.errors

    assert len(validator.errors) == 3


def test_inconsistent_default_answers_in_variants():
    file_name = (
        "schemas/invalid/test_invalid_inconsistent_default_answers_in_variants.json"
    )
    json_to_validate = _open_and_load_schema_file(file_name)

    validator = QuestionnaireValidator(json_to_validate)
    validator.validate()

    assert [
        {
            "message": error_messages.VARIANTS_HAVE_DIFFERENT_DEFAULT_ANSWERS,
            "block_id": "block-2",
            "section_id": "section",
            "question_ids": {"question-2"},
        }
    ] == validator.errors


def test_invalid_list_collector_duplicate_ids_between_list_collectors():
    filename = "schemas/invalid/test_invalid_list_collector_duplicate_ids_multiple_collectors.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate_duplicates()

    expected_errors = [
        {"message": error_messages.DUPLICATE_ID_FOUND, "id": "add-person"},
        {"message": error_messages.DUPLICATE_ID_FOUND, "id": "remove-person"},
        {"message": error_messages.DUPLICATE_ID_FOUND, "id": "edit-person"},
    ]

    assert all(
        {expected_error in validator.errors for expected_error in expected_errors}
    )


def test_inconsistent_types_in_variants():
    file_name = "schemas/invalid/test_invalid_inconsistent_types_in_variants.json"
    json_to_validate = _open_and_load_schema_file(file_name)

    validator = QuestionnaireValidator(json_to_validate)
    validator.validate()

    expected_errors = [
        {
            "message": error_messages.VARIANTS_HAVE_MULTIPLE_QUESTION_TYPES,
            "block_id": "block-2",
            "section_id": "section",
            "question_types": {"NotGeneral", "General"},
        },
        {
            "message": error_messages.VARIANTS_HAVE_MISMATCHED_ANSWER_TYPES,
            "block_id": "block-2",
            "answer_id": "answer-2",
            "section_id": "section",
            "answer_types": {"TextField", "Number"},
        },
    ]

    assert expected_errors == validator.errors


def test_non_existent_list_name_in_relationship():
    filename = "schemas/invalid/test_invalid_relationship_list_doesnt_exist.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate()

    expected_for_list_error = {
        "message": error_messages.FOR_LIST_NEVER_POPULATED,
        "list_name": "not-a-list",
        "block_id": "relationships",
    }

    assert validator.errors[0] == expected_for_list_error


def test_invalid_repeating_section_list_name():
    filename = "schemas/invalid/test_invalid_repeating_section_list_name.json"
    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_errors = [
        {
            "message": error_messages.FOR_LIST_NEVER_POPULATED,
            "list_name": "non-existent-list",
            "section_id": "personal-details-section",
        },
    ]

    validator.validate()

    assert validator.errors == expected_errors


def test_invalid_hub_section_non_existent():
    validator = QuestionnaireValidator()
    section_ids = ["employment-section", "accommodation-section"]
    required_section_ids = ["invalid-section-id"]
    expected_error_message = {
        "message": error_messages.REQUIRED_HUB_SECTION_UNDEFINED,
        "required_section_id": "invalid-section-id",
    }

    validator.validate_required_section_ids(section_ids, required_section_ids)

    assert expected_error_message == validator.errors[0]


def test_invalid_quotes_in_schema():
    filename = "schemas/invalid/test_invalid_quotes_in_schema_text.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_error_messages = [
        {"message": error_messages.DUMB_QUOTES_FOUND, "pointer": pointer}
        for pointer in [
            "/sections/0/groups/0/blocks/1/question_variants/0/question/title",
            "/sections/0/groups/0/blocks/0/question/description/0",
            "/sections/0/groups/0/blocks/0/question/answers/0/label",
            "/sections/0/groups/0/blocks/0/question/answers/0/guidance/contents/0/list/0",
        ]
    ]
    validator.validate_smart_quotes()

    assert validator.errors == expected_error_messages


def test_invalid_whitespaces_in_schema():
    filename = "schemas/invalid/test_invalid_whitespaces_in_schema_text.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_error_messages = [
        {
            "message": error_messages.INVALID_WHITESPACE_FOUND,
            "pointer": pointer,
            "text": text,
        }
        for text, pointer in [
            (
                "What is this persons  age?",
                "/sections/0/groups/0/blocks/1/question_variants/0/question/title",
            ),
            (
                " The persons age",
                "/sections/0/groups/0/blocks/0/question/description/0",
            ),
            ("Your age? ", "/sections/0/groups/0/blocks/0/question/answers/0/label"),
            (
                " Guidance Line 1",
                "/sections/0/groups/0/blocks/0/question/answers/0/guidance/contents/0/list/0",
            ),
        ]
    ]
    validator.validate_white_spaces()

    assert validator.errors == expected_error_messages


def test_invalid_answer_type_for_question_summary_concatenation():
    filename = "schemas/invalid/test_invalid_answer_type_for_question_summary.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_error_messages = [
        {
            "message": error_messages.UNSUPPORTED_QUESTION_SUMMARY_ANSWER_TYPE,
            "answer_id": "radio-answer",
            "section_id": "default-section",
        }
    ]

    validator.validate()

    assert validator.errors == expected_error_messages


def test_multiple_list_collectors_and_lists_in_single_section():
    filename = "schemas/invalid/test_invalid_multiple_list_collectors_and_lists.json"
    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_errors = [
        {
            "message": error_messages.MULTIPLE_LIST_COLLECTORS,
            "section_id": "section",
        },
    ]

    validator.validate()

    assert validator.errors == expected_errors


def test_introduction_block_not_in_schema():
    filename = "schemas/invalid/test_invalid_introduction_block.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_errors = [
        {
            "message": error_messages.PREVIEW_WITHOUT_INTRODUCTION_BLOCK,
        },
    ]
    validator.validate_introduction_block()

    assert validator.errors == expected_errors


def test_invalid_calculated_or_grand_calculated_summary_id_in_value_source():
    """Asserts `invalid` when a value source references an invalid calculated or grand calculated summary id"""
    filename = "schemas/invalid/test_invalid_value_source_calculated_and_grand_calculated_summary.json"
    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_errors = [
        {
            "identifier": "first-number-block",
            "json_path": "groups.[0].blocks.[3].content.contents.[0].list.[0].placeholders.[0].transforms.[0].arguments.number.identifier",
            "message": "Invalid calculated_summary source reference",
        },
        {
            "identifier": "currency-total-playback",
            "json_path": "groups.[0].blocks.[3].content.contents.[0].list.[1].placeholders.[0].transforms.[0].arguments.number.identifier",
            "message": "Invalid grand_calculated_summary source reference",
        },
    ]

    validator.validate()

    assert validator.errors == expected_errors


def test_answer_as_source_referenced_before_created():
    """
    The schema being validated contains blocks where an invalid answer source being referenced multiple times within that block,
    resulting in duplicated expected errors.
    """
    filename = "schemas/invalid/test_invalid_answer_source_reference.json"
    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_errors = [
        {
            "block_id": "confirm-dob",
            "message": "Answer 'date-of-birth-answer' referenced as source before it has "
            "been added.",
        },
        {
            "block_id": "confirm-sex",
            "message": "Answer 'sex-answer' referenced as source before it has been "
            "added.",
        },
        {
            "group_id": "confirmation-group",
            "message": "Answer 'number-of-employees-total' referenced as source before "
            "it has been added.",
        },
        {
            "block_id": "number-of-employees-split-block",
            "message": "Answer 'number-of-employees-total' referenced as source before "
            "it has been added.",
        },
        {
            "block_id": "number-of-employees-split-block",
            "message": "Answer 'number-of-employees-total' referenced as source before "
            "it has been added.",
        },
        {
            "block_id": "confirm-zero-employees-block",
            "message": "Answer 'number-of-employees-total' referenced as source before "
            "it has been added.",
        },
        {
            "block_id": "any-other-companies-or-branches",
            "message": "Answer 'any-companies-or-branches-answer' referenced as source "
            "before it has been added.",
        },
        {
            "message": "Answer 'number-of-employees-total' referenced as source before "
            "it has been added.",
            "section_id": "confirmation-section",
        },
    ]
    validator.validate()
    assert validator.errors == expected_errors


def test_list_as_source_referenced_before_created():
    filename = "schemas/invalid/test_invalid_list_source_reference.json"
    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_errors = [
        {
            "list_id": "household",
            "message": error_messages.LIST_REFERENCED_BEFORE_CREATED,
            "block_id": "individual-interstitial",
            "section_id": "individuals-section",
        },
        {
            "list_id": "household",
            "message": error_messages.LIST_REFERENCED_BEFORE_CREATED,
            "block_id": "individual-interstitial",
            "section_id": "individuals-section",
        },
        {
            "list_id": "household",
            "message": error_messages.LIST_REFERENCED_BEFORE_CREATED,
            "block_id": "list-status-2",
            "section_id": "individuals-section",
        },
        {
            "list_id": "household",
            "message": error_messages.LIST_REFERENCED_BEFORE_CREATED,
            "block_id": "list-status-2",
            "section_id": "individuals-section",
        },
        {
            "list_id": "household",
            "message": error_messages.LIST_REFERENCED_BEFORE_CREATED,
            "block_id": "list-status-2",
            "section_id": "individuals-section",
        },
        {
            "list_name": "household",
            "message": error_messages.LIST_REFERENCED_BEFORE_CREATED,
            "section_id": "individuals-section",
        },
        {
            "list_id": "utility-bills",
            "message": error_messages.LIST_REFERENCED_BEFORE_CREATED,
            "block_id": "dynamic-answer",
            "section_id": "utility-bills-section",
        },
        {
            "list_id": "utility-bills",
            "message": error_messages.LIST_REFERENCED_BEFORE_CREATED,
            "block_id": "dynamic-answer",
            "section_id": "utility-bills-section",
        },
    ]

    validator.validate()
    assert validator.errors == expected_errors


def test_list_and_answer_source_referenced_before_created_repeating_blocks():
    filename = (
        "schemas/invalid/test_invalid_list_source_reference_repeating_blocks.json"
    )
    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_errors = [
        {
            "block_id": "any-other-companies-or-branches",
            "message": "Answer 'company-or-branch-name' referenced as source before it "
            "has been added.",
        },
        {
            "block_id": "any-other-companies-or-branches",
            "list_id": "companies",
            "message": error_messages.LIST_REFERENCED_BEFORE_CREATED,
            "section_id": "section-companies",
        },
    ]

    validator.validate()
    assert validator.errors == expected_errors
