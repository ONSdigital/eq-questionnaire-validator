import os
from json import load

from structlog import configure
from structlog import getLogger
from structlog.stdlib import LoggerFactory

from app.validation.validator import Validator

logger = getLogger()

configure(logger_factory=LoggerFactory())

validator = Validator()


def validate_schema(json_to_validate):
    errors = validator.validate_schema(json_to_validate)
    validation_errors = errors['validation_errors']
    schema_errors = errors['schema_errors']

    return validation_errors, schema_errors


def _open_and_load_schema_file(file):
    json_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), file), encoding='utf8')
    json_to_validate = load(json_file)

    return json_to_validate


def check_validation_errors(filename, expected_validation_error_messages):
    """
    Helper function to automate tests which are just checking validation errors against a known list.
    """

    json_to_validate = _open_and_load_schema_file(filename)

    validation_errors, schema_errors = validate_schema(json_to_validate)

    print(f'validation errors: {validation_errors}')
    print(f'schema errors: {schema_errors}')

    assert schema_errors == {}

    error_messages = list(error['message'] for error in validation_errors)

    for expected_error_message in expected_validation_error_messages:
        assert expected_error_message in error_messages

    assert len(validation_errors) == len(expected_validation_error_messages)


def test_param_valid_schemas(valid_schema_filename):
    """
    Uses py.test generated tests to validate all schemas contained in the 'valid' folder.
    """
    with open(valid_schema_filename, encoding='utf8') as json_file:
        json_to_validate = load(json_file)

        errors = validator.validate_schema(json_to_validate)
        assert not errors['validation_errors']
        assert not errors['schema_errors']


def test_invalid_schema_block():
    filename = 'schemas/invalid/test_invalid_routing_block.json'

    expected_error_messages = [
        'Schema Integrity Error. The routing rules for group or block: '
        'conditional-routing-block must contain a default routing rule '
        'without a when rule',

        'Schema Integrity Error. Routing rule routes to invalid block '
        '[invalid-location]',

        'Schema Integrity Error. The answer id - fake-answer in the id key of the '
        '"when" clause for conditional-routing-block does not exist',

        'Schema Integrity Error. Routing rule not defined for all answers or '
        'default not defined for answer [conditional-routing-answer] '
        "missing options ['no']",

        'Schema Integrity Error. The answer id - AnAnswerThatDoesNotExist in the id '
        'key of the "when" clause for response-yes does not exist',
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_numeric_answers():
    filename = 'schemas/invalid/test_invalid_numeric_answers.json'

    expected_error_messages = [
        'Schema Integrity Error. Invalid range of min = 0 and max = -1.0 is possible for answer "answer-2".',
        'Schema Integrity Error. The referenced answer "answer-1" has a greater number of decimal places than '
        'answer "answer-2"',
        'Schema Integrity Error. The referenced answer "answer-4" can not be used to set the minimum of answer '
        '"answer-3"',
        'Schema Integrity Error. The referenced answer "answer-5" can not be used to set the maximum of answer '
        '"answer-3"',
        'Schema Integrity Error. Minimum value -99999999999 for answer "answer-4" is less than system limit of '
        '-999999999',
        'Schema Integrity Error. Maximum value 99999999999 for answer "answer-4" is greater than system limit of '
        '9999999999',
        'Schema Integrity Error. Number of decimal places 10 for answer "answer-5" is greater than system limit '
        'of 6',
        'Schema Integrity Error. The referenced answer "answer-1" has a greater number of decimal places than '
        'answer "answer-6"',
        'Schema Integrity Error. Default is being used with a mandatory answer: answer-7'
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_id_in_answers_to_calculate():
    filename = 'schemas/invalid/test_invalid_id_in_grouped_answers_to_calculate.json'

    expected_error_messages = [
        'Schema Integrity Error. Answer id - breakdown-3 does not exist within this question - breakdown-question',
        'Schema Integrity Error. Answer id - breakdown-4 does not exist within this question - breakdown-question'
    ]
    check_validation_errors(filename, expected_error_messages)


def test_invalid_date_range_period():
    filename = 'schemas/invalid/test_invalid_date_range_period.json'

    expected_error_messages = [
        'Schema Integrity Error. The minimum period is greater than the maximum period for date-range-question'
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_mm_yyyy_date_range_period():
    filename = 'schemas/invalid/test_invalid_mm_yyyy_date_range_period.json'

    expected_error_messages = [
        'Schema Integrity Error. Days can not be used in period_limit for yyyy-mm date range for date-range-question'
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_yyyy_date_range_period():
    filename = 'schemas/invalid/test_invalid_yyyy_date_range_period.json'

    expected_error_messages = [
        'Schema Integrity Error. '
        'Days/Months can not be used in period_limit for yyyy date range for date-range-question'
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_single_date_period():
    filename = 'schemas/invalid/test_invalid_single_date_min_max_period.json'

    expected_error_messages = [
        'Schema Integrity Error. The minimum offset date is greater than the maximum offset date'
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_metadata():
    filename = 'schemas/invalid/test_invalid_metadata.json'

    expected_error_messages = [
        'Schema Integrity Error. Metadata - ru_name not specified in metadata field',
        'Schema Integrity Error. Metadata - invalid not specified in metadata field'
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_survey_id_whitespace():
    file = 'schemas/invalid/test_invalid_survey_id_whitespace.json'
    json_to_validate = _open_and_load_schema_file(file)

    validation_errors, schema_errors = validate_schema(json_to_validate)

    assert validation_errors == []

    assert "'lms ' does not match '^[0-9a-z]+$'" in schema_errors.get('message')


def test_invalid_calculated_summary():
    """Asserts invalid `when` types, currencies or units are not of the same type for CalculatedSummary"""
    filename = 'schemas/invalid/test_invalid_calculated_summary.json'
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        "Schema Integrity Error. All answers in block total-playback-type-error's answers_to_calculate must be of the same type",
        "Schema Integrity Error. All answers in block total-playback-currency-error's answers_to_calculate must be of the same currency",
        "Schema Integrity Error. All answers in block total-playback-unit-error's answers_to_calculate must be of the same unit",
        "Schema Integrity Error. Invalid answer id 'seventh-number-answer' in block total-playback-answer-error's answers_to_calculate",
    ]

    expected_fuzzy_error_messages = [
        'Schema Integrity Error. Duplicate answers',
    ]

    validation_errors, schema_errors = validate_schema(json_to_validate)

    assert schema_errors == {}
    assert len(validation_errors) == len(expected_error_messages) + len(expected_fuzzy_error_messages)

    validation_error_messages = [error['message'] for error in validation_errors]

    for expected_error in expected_error_messages:
        assert expected_error in validation_error_messages

    for fuzzy_error in expected_fuzzy_error_messages:
        assert any(fuzzy_error in validation_error_message for validation_error_message in validation_error_messages)


def test_answer_comparisons_different_types():
    """ Ensures that when answer comparison is used, the type of the variables must be the same """
    filename = 'schemas/invalid/test_invalid_answer_comparison_types.json'

    expected_error_messages = [
        'Schema Integrity Error. The answers used as comparison_id `route-comparison-1-answer` and answer_id `route-comparison-2-answer` '
        'in the `when` clause for `route-comparison-2` have different types',

        'Schema Integrity Error. The comparison_id `route-comparison-2-answer` is not of answer type `Checkbox`. '
        'The condition `equals any` can only reference `Checkbox` answers when using `comparison id`',

        'Schema Integrity Error. The answers used as comparison_id `comparison-2-answer` and answer_id `comparison-1-answer` in the `when` '
        'clause for `equals-answers` have different types',

        'Schema Integrity Error. The answers used as comparison_id `comparison-2-answer` and answer_id `comparison-1-answer` in the `when` '
        'clause for `less-than-answers` have different types',

        'Schema Integrity Error. The answers used as comparison_id `comparison-2-answer` and answer_id `comparison-1-answer` in the `when` '
        'clause for `less-than-answers` have different types',
    ]

    check_validation_errors(filename, expected_error_messages)


def test_answer_comparisons_invalid_comparison_id():
    """ Ensures that when answer comparison is used, the comparison_id is a valid answer id"""
    filename = 'schemas/invalid/test_invalid_answer_comparison_id.json'

    expected_error_messages = [
        'Schema Integrity Error. The answer id - bad-answer-id-2 in the comparison_id key of the "when" '
        'clause for route-comparison-2 does not exist',
        'Schema Integrity Error. The answer id - bad-answer-id-3 in the comparison_id key of the "when" '
        'clause for equals-answers does not exist',
        'Schema Integrity Error. The answer id - bad-answer-id-4 in the comparison_id key of the "when" '
        'clause for less-than-answers does not exist',
        'Schema Integrity Error. The answer id - bad-answer-id-5 in the comparison_id key of the "when" '
        'clause for less-than-answers does not exist',
        'Schema Integrity Error. The answer id - bad-answer-id-6 in the comparison_id key of the "when" '
        'clause for greater-than-answers does not exist',
        'Schema Integrity Error. The answer id - bad-answer-id-7 in the id key of the "when" '
        'clause for greater-than-answers does not exist',
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_mutually_exclusive_conditions():
    filename = 'schemas/invalid/test_invalid_mutually_exclusive_conditions.json'

    expected_error_messages = [
        'Schema Integrity Error. MutuallyExclusive question type cannot contain mandatory answers.',
        'Schema Integrity Error. mutually-exclusive-date-answer-2 is not of type Checkbox.'
    ]

    check_validation_errors(filename, expected_error_messages)


def test_decimal_places_must_be_defined_when_using_totaliser():
    filename = 'schemas/invalid/test_invalid_decimal_places_must_be_defined_when_using_totaliser.json'
    expected_error_messages = [
        "Schema Integrity Error. 'decimal_places' must be defined and set to 2 for the answer_id - total-percentage",
        "Schema Integrity Error. 'decimal_places' must be defined and set to 2 for the answer_id - total-percentage-2"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_string_transforms():
    filename = 'schemas/invalid/test_invalid_string_transforms.json'

    expected_error_messages = [
        "Schema Integrity Error. Placeholders in 'text' doesn't match 'placeholders' definition for block id 'block1'",
        "Schema Integrity Error. Placeholders in 'text' doesn't match 'placeholders' definition for block id 'block2'",
        "Schema Integrity Error. Placeholders in 'text' doesn't match 'placeholders' definition for block id 'block3'",
        "Schema Integrity Error. Can't reference `previous_transform` in a first transform in block id 'block4'",
        "Schema Integrity Error. `previous_transform` not referenced in chained transform in block id 'block5'"
    ]

    check_validation_errors(filename, expected_error_messages)


def test_invalid_placeholder_answer_ids():
    filename = 'schemas/invalid/test_invalid_placeholder_source_ids.json'

    expected_error_messages = [
        'Schema Integrity Error. Invalid answer id reference `answer4` for placeholder `simple_answer` (self-reference)',
        'Schema Integrity Error. Invalid answer id reference `invalid-answer0` for placeholder `simple_answer`',
        'Schema Integrity Error. Invalid answer id reference `invalid-answer1` for placeholder `answer1`',
        'Schema Integrity Error. Invalid metadata reference `invalid-metadata-ref` for placeholder `simple_metadata`'
    ]

    check_validation_errors(filename, expected_error_messages)


def test_single_variant_invalid():
    file_name = 'schemas/invalid/test_invalid_single_variant.json'
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors, schema_errors = validate_schema(json_to_validate)

    assert 'is not valid under any of the given schemas' in schema_errors['message']

    assert len(validation_errors) == 1

    assert 'contains fewer than two variants' in validation_errors[0]['message']


def test_duplicate_answer_ids():
    file_name = 'schemas/invalid/test_invalid_duplicate_ids.json'
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors, schema_errors = validate_schema(json_to_validate)
    error_messages = [error['message'] for error in validation_errors]

    assert 'Schema Integrity Error. Duplicate id found: block-1' in error_messages
    assert 'Schema Integrity Error. Duplicate id found: answer-2' in error_messages
    assert 'Schema Integrity Error. Duplicate id found: question-1' in error_messages
    assert 'Schema Integrity Error. Duplicate id found: block-2' in error_messages

    assert schema_errors == {}


def test_invalid_list_collector_non_radio():
    file_name = 'schemas/invalid/test_invalid_list_collector_non_radio.json'
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors, schema_errors = validate_schema(json_to_validate)
    error_messages = [error['message'] for error in validation_errors]

    assert 'Schema Integrity Error. The list collector block list-collector does not contain a Radio answer type' \
           in error_messages

    assert schema_errors == {}


def test_invalid_list_collector_with_routing():
    file_name = 'schemas/invalid/test_invalid_list_collector_with_routing.json'
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors, schema_errors = validate_schema(json_to_validate)
    error_messages = [error['message'] for error in validation_errors]

    assert 'Schema Integrity Error. The list collector block list-collector contains routing rule on the "remove_block"' in error_messages

    assert schema_errors == {}


def test_invalid_list_collector_with_no_add_option():
    file_name = 'schemas/invalid/test_invalid_list_collector_with_no_add_option.json'
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors, schema_errors = validate_schema(json_to_validate)
    error_messages = [error['message'] for error in validation_errors]

    assert 'Schema Integrity Error. The list collector block list-collector has an add_answer_value that is not present ' \
           'in the answer values' in error_messages

    assert schema_errors == {}


def test_inconsistent_ids_in_variants():
    file_name = 'schemas/invalid/test_invalid_inconsistent_ids_in_variants.json'
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors, schema_errors = validate_schema(json_to_validate)
    error_messages = [error['message'] for error in validation_errors]

    fuzzy_error_messages = ['Schema Integrity Error. Variants contain more than one question_id for block: block-2. Found ids',
                            'question-2',
                            'question-2-variant',
                            'Schema Integrity Error. Variants have mismatched answer_ids for block: block-2.']

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert 'Schema Integrity Error. Variants in block: block-2 contain different numbers of answers' in error_messages

    assert len(validation_errors) == 3

    assert schema_errors == {}


def test_inconsistent_types_in_variants():
    file_name = 'schemas/invalid/test_invalid_inconsistent_types_in_variants.json'
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors, _ = validate_schema(json_to_validate)
    error_messages = [error['message'] for error in validation_errors]

    fuzzy_error_messages = (
        'Schema Integrity Error. Variants have more than one question type for block: block-2',
        'Schema Integrity Error. Variants have mismatched answer types for block: block-2. Found types:',
    )

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert len(validation_errors) == 2


def test_invalid_when_condition_property():
    file_name = 'schemas/invalid/test_invalid_when_condition_property.json'
    json_to_validate = _open_and_load_schema_file(file_name)

    validation_errors, schema_errors = validate_schema(json_to_validate)
    error_messages = [error['message'] for error in validation_errors]

    fuzzy_error_messages = [
        'Schema Integrity Error. The comparison_id `country-checkbox-answer2` is not of answer type `Checkbox`. '
        'The condition `contains any` can only reference `Checkbox` answers when using `comparison id`',

        'Schema Integrity Error. The condition `equals any` cannot be used with `Checkbox` answer type.'
    ]

    for fuzzy_error in fuzzy_error_messages:
        assert any(fuzzy_error in error_message for error_message in error_messages)

    assert len(validation_errors) == 2

    assert schema_errors != {}
