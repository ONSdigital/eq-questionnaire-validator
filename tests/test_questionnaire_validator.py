import os
from json import load

from structlog import configure
from structlog import getLogger
from structlog.stdlib import LoggerFactory

from app.validation.questionnaire_validator import QuestionnaireValidator

logger = getLogger()

configure(logger_factory=LoggerFactory())


def _open_and_load_schema_file(file):
    json_file = open(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), file), encoding="utf8"
    )
    json_to_validate = load(json_file)

    return json_to_validate


def check_validation_errors(
    filename, expected_validation_error_messages, expected_number_validation_errors=None
):
    """
    Helper function to automate tests which are just checking validation errors against a known list.
    """
    json_to_validate = _open_and_load_schema_file(filename)

    validator = QuestionnaireValidator(json_to_validate)

    schema_errors = validator.validate_json_schema()
    validator.validate_questionnaire()

    print(f"validation errors: {validator.errors}")
    print(f"schema errors: {schema_errors}")

    assert schema_errors == {}

    error_messages = [error["message"] for error in validator.errors if error]

    for expected_error_message in expected_validation_error_messages:
        assert expected_error_message in error_messages

    if not expected_number_validation_errors:
        expected_number_validation_errors = len(expected_validation_error_messages)

    assert len(validator.errors) == expected_number_validation_errors

    return validator.errors, schema_errors


def test_param_valid_schemas(valid_schema_filename):
    """
    Uses py.test generated tests to validate all schemas contained in the 'valid' folder.
    """
    with open(valid_schema_filename, encoding="utf8") as json_file:
        json_to_validate = load(json_file)

        validator = QuestionnaireValidator(json_to_validate)

        schema_errors = validator.validate_json_schema()
        validator.validate_questionnaire()

        assert not validator.errors
        assert not schema_errors


def test_invalid_routing_default_block():
    rules = [
        {
            "goto": {
                "block": "response-yes",
                "when": [
                    {
                        "condition": "equals",
                        "id": "conditional-routing-answer",
                        "value": "Yes",
                    }
                ],
            }
        },
        {
            "goto": {
                "block": "invalid-location",
                "when": [
                    {
                        "condition": "equals",
                        "id": "conditional-routing-answer",
                        "value": "No, I prefer tea",
                    }
                ],
            }
        },
    ]
    questionnaire_validator = QuestionnaireValidator({"id": "test-questionnaire"})

    questionnaire_validator.validate_routing_rules_have_default(
        rules, "conditional-routing-block"
    )

    expected_error = {
        "message": "The routing rules for group or block: conditional-routing-block must contain a default routing "
        "rule without a when rule",
        "id": "test-questionnaire",
    }

    assert questionnaire_validator.errors[0] == expected_error


def test_invalid_routing_block_id():

    rule = {
        "goto": {
            "block": "invalid-location",
            "when": [
                {
                    "condition": "equals",
                    "id": "conditional-routing-answer",
                    "value": "No, I prefer tea",
                }
            ],
        }
    }
    questionnaire_validator = QuestionnaireValidator({"id": "test-questionnaire"})

    expected_error = {
        "message": "Routing rule routes to invalid block [invalid-location]",
        "id": "test-questionnaire",
    }

    questionnaire_validator.validate_routing_rule_target(
        [{"id": "a-valid-location"}], "block", rule
    )

    assert questionnaire_validator.errors[0] == expected_error


def test_invalid_numeric_answers():
    filename = "schemas/invalid/test_invalid_numeric_answers.json"

    expected_error_messages = [
        'The referenced answer "answer-1" has a greater number of decimal places than '
        'answer "answer-2"',
        'The referenced answer "answer-4" can not be used to set the minimum of answer '
        '"answer-3"',
        "Invalid answer reference 'answer-4' in block 'block-3'",
        "Invalid answer reference 'answer-5' in block 'block-3'",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_metadata():
    filename = "schemas/invalid/test_invalid_metadata.json"

    expected_error_messages = [
        "Metadata - ru_name not specified in metadata field",
        "Metadata - invalid not specified in metadata field",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_survey_id_whitespace():
    file = "schemas/invalid/test_invalid_survey_id_whitespace.json"
    json_to_validate = _open_and_load_schema_file(file)

    validator = QuestionnaireValidator(json_to_validate)

    schema_errors = validator.validate_json_schema()
    validator.validate_questionnaire()

    assert validator.errors == []

    assert "'lms ' does not match '^[0-9a-z]+$'" in schema_errors.get("message")


def test_invalid_calculated_summary():
    """Asserts invalid `when` types, currencies or units are not of the same type for CalculatedSummary"""
    filename = "schemas/invalid/test_invalid_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "message": "All answers in block's answers_to_calculate must be of the same type",
            "block_id": "total-playback-type-error",
        },
        {
            "message": "All answers in block's answers_to_calculate must be of the same currency",
            "block_id": "total-playback-currency-error",
        },
        {
            "message": "All answers in block's answers_to_calculate must be of the same unit",
            "block_id": "total-playback-unit-error",
        },
        {
            "message": "Invalid answer id in block's answers_to_calculate",
            "answer_id": "seventh-number-answer",
            "block_id": "total-playback-answer-error",
        },
        {
            "message": "Duplicate answers in block's answers_to_calculate",
            "block_id": "total-playback-duplicate-error",
            "duplicate_answers": {"sixth-number-answer", "fourth-number-answer"},
        },
    ]

    validator = QuestionnaireValidator(json_to_validate)
    validator.validate_questionnaire()

    assert validator.errors == expected_error_messages


def test_answer_comparisons_different_types():
    """ Ensures that when answer comparison is used, the type of the variables must be the same """
    filename = "schemas/invalid/test_invalid_answer_comparison_types.json"

    expected_error_messages = [
        "The answers used as comparison id `route-comparison-1-answer` and answer_id `route-comparison-2-answer` "
        "in the `when` clause for `route-comparison-2` have different types",
        "The comparison id `route-comparison-2-answer` is not of answer type `Checkbox`. "
        "The condition `equals any` can only reference `Checkbox` answers when using `comparison id`",
        "The answers used as comparison id `comparison-2-answer` and answer_id `comparison-1-answer` in the `when` "
        "clause for `equals-answers` have different types",
        "The answers used as comparison id `comparison-2-answer` and answer_id `comparison-1-answer` in the `when` "
        "clause for `less-than-answers` have different types",
        "The answers used as comparison id `comparison-2-answer` and answer_id `comparison-1-answer` in the `when` "
        "clause for `less-than-answers` have different types",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_answer_comparisons_invalid_comparison_id():
    """ Ensures that when answer comparison is used, the comparison_id is a valid answer id"""
    filename = "schemas/invalid/test_invalid_answer_comparison_id.json"

    expected_error_messages = [
        {
            "message": QuestionnaireValidator.NON_EXISTENT_WHEN_KEY,
            "answer_id": "bad-answer-id-2",
            "key": "comparison.id",
            "referenced_id": "route-comparison-2",
        },
        {
            "message": QuestionnaireValidator.NON_EXISTENT_WHEN_KEY,
            "answer_id": "bad-answer-id-3",
            "key": "comparison.id",
            "referenced_id": "equals-answers",
        },
        {
            "message": QuestionnaireValidator.NON_EXISTENT_WHEN_KEY,
            "answer_id": "bad-answer-id-4",
            "key": "comparison.id",
            "referenced_id": "less-than-answers",
        },
        {
            "message": QuestionnaireValidator.NON_EXISTENT_WHEN_KEY,
            "answer_id": "bad-answer-id-5",
            "key": "comparison.id",
            "referenced_id": "less-than-answers",
        },
        {
            "message": QuestionnaireValidator.NON_EXISTENT_WHEN_KEY,
            "answer_id": "bad-answer-id-6",
            "key": "comparison.id",
            "referenced_id": "greater-than-answers",
        },
        {
            "message": QuestionnaireValidator.NON_EXISTENT_WHEN_KEY,
            "answer_id": "bad-answer-id-7",
            "key": "id",
            "referenced_id": "greater-than-answers",
        },
    ]

    json_to_validate = _open_and_load_schema_file(filename)
    questionnaire_validator = QuestionnaireValidator(json_to_validate)
    questionnaire_validator.validate_questionnaire()

    assert expected_error_messages == questionnaire_validator.errors


def test_invalid_mutually_exclusive_conditions():
    filename = "schemas/invalid/test_invalid_mutually_exclusive_conditions.json"

    expected_error_messages = [
        "MutuallyExclusive question type cannot contain mandatory answers.",
        "mutually-exclusive-date-answer-2 is not of type Checkbox.",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_string_transforms():
    filename = "schemas/invalid/test_invalid_string_transforms.json"

    expected_error_messages = [
        "Placeholders in 'test {answer1}' don't match definitions. Missing '{'answer1'}'",
        "Placeholders in 'test {answer1} and {answer2}' don't match definitions. Missing '{'answer2'}'",
        "Can't reference `previous_transform` in a first transform in block id 'block4'",
        "`previous_transform` not referenced in chained transform in block id 'block5'",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_placeholder_answer_ids():
    filename = "schemas/invalid/test_invalid_placeholder_source_ids.json"

    expected_error_messages = [
        "Invalid answer reference 'answer4' in block 'block3' (self-reference)",
        "Invalid answer reference 'invalid-answer0' in block 'block1'",
        "Invalid answer reference 'invalid-answer1' in block 'block2'",
        "Invalid metadata reference 'invalid-metadata-ref' in block 'block4'",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_placeholder_list_reference():
    filename = "schemas/invalid/test_invalid_placeholder_plurals.json"

    expected_error_messages = [
        "Invalid list reference 'people' in block 'block1'",
        "Invalid list reference 'people' in block 'block1'",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_single_variant_invalid():
    file_name = "schemas/invalid/test_invalid_single_variant.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(file_name))
    schema_errors = validator.validate_json_schema()
    validator.validate_questionnaire()

    assert "'when' is a required property" in schema_errors["predicted_cause"]

    assert len(validator.errors) == 1

    assert "contains fewer than two variants" in validator.errors[0]["message"]


def test_duplicate_answer_ids():
    filename = "schemas/invalid/test_invalid_duplicate_ids.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate_questionnaire()

    expected_errors = [
        {"message": QuestionnaireValidator.DUPLICATE_ID_FOUND, "id": "block-1"},
        {"message": QuestionnaireValidator.DUPLICATE_ID_FOUND, "id": "answer-2"},
        {"message": QuestionnaireValidator.DUPLICATE_ID_FOUND, "id": "question-1"},
        {"message": QuestionnaireValidator.DUPLICATE_ID_FOUND, "id": "block-2"},
    ]

    assert all(
        [expected_error in validator.errors for expected_error in expected_errors]
    )


def test_invalid_list_collector_non_radio():
    filename = "schemas/invalid/test_invalid_list_collector_non_radio.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate_questionnaire()

    expected_error_messages = [
        {
            "message": QuestionnaireValidator.NO_RADIO_FOR_LIST_COLLECTOR,
            "block_id": "list-collector",
        }
    ]

    assert expected_error_messages == validator.errors


def test_primary_person_invalid_list_collector_non_radio():
    filename = (
        "schemas/invalid/test_invalid_primary_person_list_collector_no_radio.json"
    )

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate_questionnaire()

    expected_errors = [
        {
            "message": QuestionnaireValidator.NO_RADIO_FOR_PRIMARY_PERSON_LIST_COLLECTOR,
            "block_id": "primary-person-list-collector",
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_list_collector_with_no_add_option():
    filename = "schemas/invalid/test_invalid_list_collector_with_no_add_option.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate_questionnaire()

    expected_errors = [
        {
            "message": QuestionnaireValidator.NON_EXISTENT_LIST_COLLECTOR_ADD_ANSWER_VALUE,
            "block_id": "list-collector",
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_primary_person_list_collector_with_no_add_option():
    filename = "schemas/invalid/test_invalid_primary_person_list_collector_bad_answer_value.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate_questionnaire()

    expected_errors = [
        {
            "message": QuestionnaireValidator.NON_EXISTENT_PRIMARY_PERSON_LIST_COLLECTOR_ANSWER_VALUE,
            "block_id": "primary-person-list-collector",
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_list_collector_with_different_add_block_answer_ids():
    filename = "schemas/invalid/test_invalid_list_collector_with_different_add_block_answer_ids.json"

    expected_error_messages = [
        "Multiple list collectors populate the list: people using different answer_ids in the add block"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_primary_person_list_collector_with_different_add_block_answer_ids():
    filename = "schemas/invalid/test_invalid_primary_person_list_collector_different_answer_ids_multi_collectors.json"

    expected_error_messages = [
        "Multiple primary person list collectors populate the list: people using different answer ids in the add_or_edit "
        "block"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_list_collector_with_different_answer_ids_in_add_and_edit():
    filename = "schemas/invalid/test_invalid_list_collector_with_different_answer_ids_in_add_and_edit.json"

    expected_error_messages = [
        "The list collector block list-collector contains an add block and edit block with different answer ids"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_list_reference_in_custom_summary():
    filename = "schemas/invalid/test_invalid_custom_list_summary.json"

    expected_error_messages = [
        "for_list 'household' is not populated by any ListCollector blocks"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_inconsistent_ids_in_variants():
    file_name = "schemas/invalid/test_invalid_inconsistent_ids_in_variants.json"
    json_to_validate = _open_and_load_schema_file(file_name)

    validator = QuestionnaireValidator(json_to_validate)
    schema_errors = validator.validate_json_schema()
    validator.validate_questionnaire()

    error_messages = [error["message"] for error in validator.errors]

    fuzzy_error_messages = [
        "Variants contain more than one question_id for block: block-2. Found ids",
        "question-2",
        "question-2-variant",
        "Variants have mismatched answer_ids for block: block-2.",
    ]

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert (
        "Variants in block: block-2 contain different numbers of answers"
        in error_messages
    )

    assert len(validator.errors) == 3

    assert schema_errors == {}


def test_inconsistent_default_answers_in_variants():
    file_name = (
        "schemas/invalid/test_invalid_inconsistent_default_answers_in_variants.json"
    )
    json_to_validate = _open_and_load_schema_file(file_name)

    validator = QuestionnaireValidator(json_to_validate)
    validator.validate_questionnaire()
    error_messages = [error["message"] for error in validator.errors]

    fuzzy_error_messages = [
        "Variants contain different default answers for block: block-2. Found ids",
        "question-2",
    ]

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert len(validator.errors) == 1


def test_invalid_list_collector_duplicate_ids_between_list_collectors():
    filename = "schemas/invalid/test_invalid_list_collector_duplicate_ids_multiple_collectors.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))
    validator.validate_questionnaire()

    expected_errors = [
        {"message": QuestionnaireValidator.DUPLICATE_ID_FOUND, "id": "add-person"},
        {"message": QuestionnaireValidator.DUPLICATE_ID_FOUND, "id": "remove-person"},
        {"message": QuestionnaireValidator.DUPLICATE_ID_FOUND, "id": "edit-person"},
    ]

    assert all(
        [expected_error in validator.errors for expected_error in expected_errors]
    )


def test_inconsistent_types_in_variants():
    file_name = "schemas/invalid/test_invalid_inconsistent_types_in_variants.json"
    json_to_validate = _open_and_load_schema_file(file_name)

    validator = QuestionnaireValidator(json_to_validate)
    validator.validate_questionnaire()
    error_messages = [error["message"] for error in validator.errors]
    fuzzy_error_messages = (
        "Variants have more than one question type for block: block-2",
        "Variants have mismatched answer types for block: block-2. Found types:",
    )

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert len(validator.errors) == 2


def test_invalid_when_condition_property():
    file_name = "schemas/invalid/test_invalid_when_condition_property.json"
    json_to_validate = _open_and_load_schema_file(file_name)

    validator = QuestionnaireValidator(json_to_validate)
    schema_errors = validator.validate_json_schema()
    validator.validate_questionnaire()

    error_messages = [error["message"] for error in validator.errors]

    fuzzy_error_messages = [
        "The comparison id `country-checkbox-answer2` is not of answer type `Checkbox`. "
        "The condition `contains any` can only reference `Checkbox` answers when using `comparison id`",
        "The condition `equals any` cannot be used with `Checkbox` answer type (country-checkbox-answer).",
    ]

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert len(validator.errors) == 2

    assert schema_errors != {}


def test_invalid_list_collector_bad_answer_reference_ids():
    filename = (
        "schemas/invalid/test_invalid_list_collector_bad_answer_reference_ids.json"
    )
    expected_error_messages = [
        "add_answer reference uses id not found in main block question: someone-else",
        "remove_answer reference uses id not found in remove_block: delete-confirmation",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_primary_person_list_collector_bad_answer_reference_ids():
    filename = (
        "schemas/invalid/test_invalid_primary_person_list_collector_bad_answer_id.json"
    )
    expected_error_messages = [
        "add_or_edit_answer reference uses id not found in main block question: fake-answer-id"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_list_name_in_when_rule():
    filename = "schemas/invalid/test_invalid_when_condition_list_property.json"
    expected_error_messages = [
        "The list `non-existent-list-name` is not defined in the schema"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_relationship_no_list_specified():
    filename = "schemas/invalid/test_invalid_relationship_list_doesnt_exist.json"
    for_list_error = [
        "for_list 'not-a-list' is not populated by any ListCollector blocks"
    ]
    expected_error_message = [
        "Invalid answer reference 'first-name' in block 'relationships'",
        "Invalid answer reference 'last-name' in block 'relationships'",
        "Invalid answer reference 'first-name' in block 'relationships'",
        "Invalid answer reference 'last-name' in block 'relationships'",
    ] * 6
    expected_error_message = for_list_error + expected_error_message

    check_validation_errors(filename, expected_error_message)


def test_invalid_relationship_multiple_answers():
    filename = "schemas/invalid/test_invalid_relationship_multiple_answers.json"
    expected_error_message = ["RelationshipCollector contains more than one answer."]

    check_validation_errors(filename, expected_error_message)


def test_invalid_relationship_wrong_answer_type():
    filename = "schemas/invalid/test_invalid_relationship_wrong_answer_type.json"
    expected_error_message = [
        "Only answers of type Relationship are valid in RelationshipCollector blocks."
    ]

    check_validation_errors(filename, expected_error_message)


def test_invalid_hub_and_spoke_with_summary_confirmation():
    filename = (
        "schemas/invalid/test_invalid_hub_and_spoke_with_summary_confirmation.json"
    )
    expected_error_messages = [
        "Schema can only contain one of [Confirmation page, Summary page, Hub page]"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_hub_and_spoke_and_summary_confirmation_non_existent():
    filename = "schemas/invalid/test_invalid_hub_and_spoke_and_summary_confirmation_non_existent.json"
    expected_error_messages = [
        "Schema must contain one of [Confirmation page, Summary page, Hub page]"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_repeating_section_list_name():
    filename = "schemas/invalid/test_invalid_repeating_section_list_name.json"
    expected_error_messages = [
        "for_list 'non-existent-list' is not populated by any ListCollector blocks"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_repeating_section_title_placeholders():
    filename = "schemas/invalid/test_invalid_repeating_section_title_placeholders.json"
    expected_error_messages = [
        "Placeholders in '{person}' don't match definitions. Missing '{'person'}'"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_hub_section_non_existent():
    filename = "schemas/invalid/test_invalid_hub_section_definition.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_error_message = {
        "message": 'Required hub completed section "invalid-section-id" defined in hub does not appear in schema'
    }

    validator.validate_questionnaire()

    assert expected_error_message == validator.errors[0]


def test_invalid_answer_action():
    filename = (
        "schemas/invalid/test_invalid_answer_action_redirect_to_list_add_question.json"
    )
    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_error_messages = [
        {
            "message": "List name defined in action params does not exist",
            "id": "anyone-else-live-here-answer",
            "list_name": "non-existent-list-name",
        },
        {
            "message": "Block id defined in action params does not exist",
            "block_id": "non-existent-block-id",
            "id": "anyone-else-live-here-answer",
        },
    ]

    validator.validate_questionnaire()

    assert expected_error_messages == validator.errors


def test_invalid_driving_question_multiple_collectors():
    filename = "schemas/invalid/test_invalid_list_collector_driving_question_multiple_collectors.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_error_message = (
        "ListCollectorDrivingQuestion `anyone-usually-live-at` for list "
        "`people` cannot be used with multiple ListCollectors"
    )

    validator.validate_questionnaire()

    assert expected_error_message == validator.errors[0]["message"]


def test_invalid_driving_question_multiple_driving_questions():
    filename = "schemas/invalid/test_invalid_list_collector_driving_question_multiple_driving_questions.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_error_messages = [
        {
            "message": "The block_id should be the only ListCollectorDrivingQuestion for list",
            "block_id": "anyone-usually-live-at-preceding",
            "for_list": "people",
        },
        {
            "message": "The block_id should be the only ListCollectorDrivingQuestion for list",
            "block_id": "anyone-usually-live-at",
            "for_list": "people",
        },
    ]

    validator.validate_questionnaire()

    assert expected_error_messages == validator.errors


def test_invalid_answer_value_in_when_rule():
    filename = "schemas/invalid/test_invalid_answer_value_in_when_rule.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_error_messages = [
        {
            "message": QuestionnaireValidator.INVALID_WHEN_RULE_ANSWER_VALUE,
            "answer_id": "country-checkbox-answer",
            "value": value,
        }
        for value in ["France", "France", "France", "Austria", 7, "French", "Italian"]
    ]

    validator.validate_questionnaire()

    assert validator.errors == expected_error_messages


def test_invalid_quotes_in_schema():
    filename = "schemas/invalid/test_invalid_quotes_in_schema_text.json"

    validator = QuestionnaireValidator(_open_and_load_schema_file(filename))

    expected_error_messages = [
        {"message": QuestionnaireValidator.DUMB_QUOTES_FOUND, "pointer": pointer}
        for pointer in [
            "/sections/0/groups/0/blocks/0/question/description",
            "/sections/0/groups/0/blocks/1/question_variants/0/question/title",
            "/sections/0/groups/0/blocks/0/question/answers/0/guidance/contents/0/list/0",
            "/sections/0/groups/0/blocks/0/question/answers/0/label",
        ]
    ]
    validator.validate_questionnaire()

    assert validator.errors == expected_error_messages


def test_invalid_non_textfield_question_concatenation():
    filename = "schemas/invalid/test_invalid_question_concatenation_non_textfield.json"

    expected_error_messages = [
        "Summary concatenation can only be used for TextFields, `checkbox-answer` is invalid"
    ]

    check_validation_errors(filename, expected_error_messages)
