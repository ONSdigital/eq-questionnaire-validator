import os
from json import load

from structlog import configure
from structlog import getLogger
from structlog.stdlib import LoggerFactory

from app.validation.validator import Validator

logger = getLogger()

configure(logger_factory=LoggerFactory())

validator = Validator()


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

    schema_errors = validator.validate_json_schema(json_to_validate)
    validation_errors = validator.validate_questionnaire(json_to_validate)

    print(f"validation errors: {validation_errors}")
    print(f"schema errors: {schema_errors}")

    assert schema_errors == {}
    error_messages = [error["message"] for error in validation_errors if error]

    for expected_error_message in expected_validation_error_messages:
        assert expected_error_message in error_messages

    if not expected_number_validation_errors:
        expected_number_validation_errors = len(expected_validation_error_messages)

    assert len(validation_errors) == expected_number_validation_errors

    return validation_errors, schema_errors


def test_param_valid_schemas(valid_schema_filename):
    """
    Uses py.test generated tests to validate all schemas contained in the 'valid' folder.
    """
    with open(valid_schema_filename, encoding="utf8") as json_file:
        json_to_validate = load(json_file)

        schema_errors = validator.validate_json_schema(json_to_validate)
        validation_errors = validator.validate_questionnaire(json_to_validate)

        assert not validation_errors
        assert not schema_errors


def test_invalid_schema_block():
    filename = "schemas/invalid/test_invalid_routing_block.json"

    expected_error_messages = [
        "The routing rules for group or block: "
        "conditional-routing-block must contain a default routing rule "
        "without a when rule",
        "Routing rule routes to invalid block [invalid-location]",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_numeric_answers():
    filename = "schemas/invalid/test_invalid_numeric_answers.json"

    expected_error_messages = [
        'Invalid range of min = 0 and max = -1.0 is possible for answer "answer-2".',
        'The referenced answer "answer-1" has a greater number of decimal places than '
        'answer "answer-2"',
        'The referenced answer "answer-4" can not be used to set the minimum of answer '
        '"answer-3"',
        'The referenced answer "answer-5" can not be used to set the maximum of answer '
        '"answer-3"',
        'Minimum value -99999999999 for answer "answer-4" is less than system limit of '
        "-999999999",
        'Maximum value 99999999999 for answer "answer-4" is greater than system limit of '
        "9999999999",
        'Number of decimal places 10 for answer "answer-5" is greater than system limit '
        "of 6",
        'The referenced answer "answer-1" has a greater number of decimal places than '
        'answer "answer-6"',
        "Default is being used with a mandatory answer: answer-7",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_id_in_answers_to_calculate():
    filename = "schemas/invalid/test_invalid_id_in_grouped_answers_to_calculate.json"

    expected_error_messages = [
        "Answer id - breakdown-3 does not exist within this question - breakdown-question",
        "Answer id - breakdown-4 does not exist within this question - breakdown-question",
    ]
    check_validation_errors(filename, expected_error_messages)


def test_invalid_date_range_period():
    filename = "schemas/invalid/test_invalid_date_range_period.json"

    expected_error_messages = [
        "The minimum period is greater than the maximum period for date-range-question"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_mm_yyyy_date_range_period():
    filename = "schemas/invalid/test_invalid_mm_yyyy_date_range_period.json"

    expected_error_messages = [
        "Days can not be used in period_limit for yyyy-mm date range for date-range-question"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_yyyy_date_range_period():
    filename = "schemas/invalid/test_invalid_yyyy_date_range_period.json"

    expected_error_messages = [
        ""
        "Days/Months can not be used in period_limit for yyyy date range for date-range-question"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_single_date_period():
    filename = "schemas/invalid/test_invalid_single_date_min_max_period.json"

    expected_error_messages = [
        "The minimum offset date is greater than the maximum offset date"
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

    schema_errors = validator.validate_json_schema(json_to_validate)
    validation_errors = validator.validate_questionnaire(json_to_validate)

    assert validation_errors == []

    assert "'lms ' does not match '^[0-9a-z]+$'" in schema_errors.get("message")


def test_invalid_calculated_summary():
    """Asserts invalid `when` types, currencies or units are not of the same type for CalculatedSummary"""
    filename = "schemas/invalid/test_invalid_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        "All answers in block total-playback-type-error's answers_to_calculate must be of the same type",
        "All answers in block total-playback-currency-error's answers_to_calculate must be of the same currency",
        "All answers in block total-playback-unit-error's answers_to_calculate must be of the same unit",
        "Invalid answer id 'seventh-number-answer' in block total-playback-answer-error's answers_to_calculate",
    ]

    expected_fuzzy_error_messages = ["Duplicate answers"]

    schema_errors = validator.validate_json_schema(json_to_validate)
    validation_errors = validator.validate_questionnaire(json_to_validate)

    assert schema_errors == {}
    assert len(validation_errors) == len(expected_error_messages) + len(
        expected_fuzzy_error_messages
    )

    validation_error_messages = [error["message"] for error in validation_errors]

    for expected_error in expected_error_messages:
        assert expected_error in validation_error_messages

    for fuzzy_error in expected_fuzzy_error_messages:
        assert any(
            fuzzy_error in validation_error_message
            for validation_error_message in validation_error_messages
        )


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
        'The answer id - bad-answer-id-2 in the comparison.id key of the "when" '
        "clause for route-comparison-2 does not exist",
        'The answer id - bad-answer-id-3 in the comparison.id key of the "when" '
        "clause for equals-answers does not exist",
        'The answer id - bad-answer-id-4 in the comparison.id key of the "when" '
        "clause for less-than-answers does not exist",
        'The answer id - bad-answer-id-5 in the comparison.id key of the "when" '
        "clause for less-than-answers does not exist",
        'The answer id - bad-answer-id-6 in the comparison.id key of the "when" '
        "clause for greater-than-answers does not exist",
        'The answer id - bad-answer-id-7 in the id key of the "when" '
        "clause for greater-than-answers does not exist",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_mutually_exclusive_conditions():
    filename = "schemas/invalid/test_invalid_mutually_exclusive_conditions.json"

    expected_error_messages = [
        "MutuallyExclusive question type cannot contain mandatory answers.",
        "mutually-exclusive-date-answer-2 is not of type Checkbox.",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_decimal_places_must_be_defined_when_using_totaliser():
    filename = "schemas/invalid/test_invalid_decimal_places_must_be_defined_when_using_totaliser.json"
    expected_error_messages = [
        "'decimal_places' must be defined and set to 2 for the answer_id - total-percentage",
        "'decimal_places' must be defined and set to 2 for the answer_id - total-percentage-2",
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
    json_to_validate = _open_and_load_schema_file(file_name)

    schema_errors = validator.validate_json_schema(json_to_validate)
    validation_errors = validator.validate_questionnaire(json_to_validate)

    assert "'when' is a required property" in schema_errors["predicted_cause"]

    assert len(validation_errors) == 1

    assert "contains fewer than two variants" in validation_errors[0]["message"]


def test_duplicate_answer_ids():
    filename = "schemas/invalid/test_invalid_duplicate_ids.json"

    expected_error_messages = [
        "Duplicate id found: block-1",
        "Duplicate id found: answer-2",
        "Duplicate id found: question-1",
        "Duplicate id found: block-2",
    ]

    check_validation_errors(
        filename, expected_error_messages, expected_number_validation_errors=5
    )


def test_invalid_list_collector_non_radio():
    filename = "schemas/invalid/test_invalid_list_collector_non_radio.json"

    expected_error_messages = [
        "The list collector block list-collector does not contain a Radio answer type"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_primary_person_invalid_list_collector_non_radio():
    filename = (
        "schemas/invalid/test_invalid_primary_person_list_collector_no_radio.json"
    )

    expected_error_messages = [
        "The primary person list collector block primary-person-list-collector does not contain a Radio answer type"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_list_collector_with_routing():
    filename = (
        "schemas/invalid/test_invalid_list_collector_with_routing_in_sub_block.json"
    )

    expected_error_messages = [
        "The list collector block list-collector contains routing rules on the remove-person sub block"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_primary_person_list_collector_with_routing():
    filename = "schemas/invalid/test_invalid_primary_person_list_collector_routing.json"

    expected_error_messages = [
        "The primary person list collector block primary-person-list-collector contains routing rules on the "
        "add-primary-person sub block"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_list_collector_with_no_add_option():
    filename = "schemas/invalid/test_invalid_list_collector_with_no_add_option.json"

    expected_error_messages = [
        "The list collector block list-collector has an add_answer_value that is not present in the answer values"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_primary_person_list_collector_with_no_add_option():
    filename = "schemas/invalid/test_invalid_primary_person_list_collector_bad_answer_value.json"

    expected_error_messages = [
        "The primary person list collector block primary-person-list-collector has an add_or_edit_answer value that is not "
        "present in the answer values"
    ]

    check_validation_errors(filename, expected_error_messages)


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


def test_inconsistent_ids_in_variants():
    file_name = "schemas/invalid/test_invalid_inconsistent_ids_in_variants.json"
    json_to_validate = _open_and_load_schema_file(file_name)

    schema_errors = validator.validate_json_schema(json_to_validate)
    validation_errors = validator.validate_questionnaire(json_to_validate)

    error_messages = [error["message"] for error in validation_errors]

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

    assert len(validation_errors) == 3

    assert schema_errors == {}


def test_inconsistent_default_answers_in_variants():
    file_name = (
        "schemas/invalid/test_invalid_inconsistent_default_answers_in_variants.json"
    )
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors = validator.validate_questionnaire(json_to_validate)
    error_messages = [error["message"] for error in validation_errors]

    fuzzy_error_messages = [
        "Variants contain different default answers for block: block-2. Found ids",
        "question-2",
    ]

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert len(validation_errors) == 1


def test_invalid_list_collector_duplicate_ids_between_list_collectors():
    filename = "schemas/invalid/test_invalid_list_collector_duplicate_ids_multiple_collectors.json"
    expected_error_messages = [
        "Duplicate id found: add-person",
        "Duplicate id found: remove-person",
        "Duplicate id found: edit-person",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_inconsistent_types_in_variants():
    file_name = "schemas/invalid/test_invalid_inconsistent_types_in_variants.json"
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors = validator.validate_questionnaire(json_to_validate)
    error_messages = [error["message"] for error in validation_errors]
    fuzzy_error_messages = (
        "Variants have more than one question type for block: block-2",
        "Variants have mismatched answer types for block: block-2. Found types:",
    )

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert len(validation_errors) == 2


def test_invalid_when_condition_property():
    file_name = "schemas/invalid/test_invalid_when_condition_property.json"
    json_to_validate = _open_and_load_schema_file(file_name)

    schema_errors = validator.validate_json_schema(json_to_validate)
    validation_errors = validator.validate_questionnaire(json_to_validate)

    error_messages = [error["message"] for error in validation_errors]

    fuzzy_error_messages = [
        "The comparison id `country-checkbox-answer2` is not of answer type `Checkbox`. "
        "The condition `contains any` can only reference `Checkbox` answers when using `comparison id`",
        "The condition `equals any` cannot be used with `Checkbox` answer type.",
    ]

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert len(validation_errors) == 2

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
    expected_error_messages = [
        'Required hub completed section "invalid-section-id" '
        "defined in hub does not appear in schema"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_answer_action():
    filename = (
        "schemas/invalid/test_invalid_answer_action_redirect_to_list_add_question.json"
    )
    expected_error_messages = [
        "List name `non-existent-list-name` defined in action params for "
        "answer `anyone-else-live-here-answer` does not exist",
        "The block_id `non-existent-block-id` defined in action params for "
        "answer `anyone-else-live-here-answer` does not exist",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_driving_question_multiple_collectors():
    filename = "schemas/invalid/test_invalid_list_collector_driving_question_multiple_collectors.json"
    expected_error_messages = [
        "ListCollectorDrivingQuestion `anyone-usually-live-at` for list `people` cannot be "
        "used with multiple ListCollectors"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_driving_question_multiple_driving_questions():
    filename = "schemas/invalid/test_invalid_list_collector_driving_question_multiple_driving_questions.json"
    expected_error_messages = [
        "The block_id `anyone-usually-live-at-preceding` should be the only "
        "ListCollectorDrivingQuestion for list `people`",
        "The block_id `anyone-usually-live-at` should be the only "
        "ListCollectorDrivingQuestion for list `people`",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_mismatching_answer_label_and_value():
    filename = "schemas/invalid/test_invalid_mismatching_answer_label_and_value.json"
    expected_error_messages = [
        "Found mismatching answer value for label: Yes it is {name} in answer id: correct-answer",
        "Found mismatching answer value for label: Nope in answer id: correct-answer",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_answer_value_in_when_rule():
    filename = "schemas/invalid/test_invalid_answer_value_in_when_rule.json"
    expected_error_messages = [
        "Answer value in when rule with answer id `country-checkbox-answer` has an invalid value of `France`",
        "Answer value in when rule with answer id `country-checkbox-answer` has an invalid value of `France`",
        "Answer value in when rule with answer id `country-checkbox-answer` has an invalid value of `France`",
        "Answer value in when rule with answer id `country-checkbox-answer` has an invalid value of `Austria`",
        "Answer value in when rule with answer id `country-checkbox-answer` has an invalid value of `7`",
        "Answer value in when rule with answer id `country-checkbox-answer` has an invalid value of `French`",
        "Answer value in when rule with answer id `country-checkbox-answer` has an invalid value of `Italian`",
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_quotes_in_schema():
    filename = "schemas/invalid/test_invalid_quotes_in_schema_text.json"

    expected_error_messages = [
        "Found dumb quotes(s) in schema text at /sections/0/groups/0/blocks/0/question/description",
        "Found dumb quotes(s) in schema text at /sections/0/groups/0/blocks/1/question_variants/0/question/title",
        "Found dumb quotes(s) in schema text at "
        "/sections/0/groups/0/blocks/0/question/answers/0/guidance/contents/0/list/0",
        "Found dumb quotes(s) in schema text at /sections/0/groups/0/blocks/0/question/answers/0/label",
    ]

    check_validation_errors(filename, expected_error_messages)
