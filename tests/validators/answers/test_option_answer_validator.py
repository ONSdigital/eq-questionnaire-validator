from app.validators.answers import OptionAnswerValidator
from app.validators.rules.rule_validator import RulesValidator
from app.validators.value_source_validator import ValueSourceValidator
from tests.conftest import get_mock_schema, get_mock_schema_with_data_version


def test_unique_answer_options():
    answer = {
        "id": "duplicate-country-answer",
        "label": "Label",
        "type": "Checkbox",
        "options": [
            {"label": "India", "value": "India"},
            {"label": "Azerbaijan", "value": "Azerbaijan"},
            {"label": "India", "value": "India"},
            {"label": "Malta", "value": "Malta"},
        ],
    }

    validator = OptionAnswerValidator(
        answer, get_mock_schema_with_data_version("0.0.3")
    )
    validator.validate_duplicate_options()

    assert validator.errors == [
        {
            "message": validator.DUPLICATE_LABEL,
            "answer_id": "duplicate-country-answer",
            "label": "India",
        },
        {
            "message": validator.DUPLICATE_VALUE,
            "answer_id": "duplicate-country-answer",
            "value": "India",
        },
    ]


def test_validate_default_exists_in_options():
    answer = {
        "type": "Radio",
        "id": "correct-answer",
        "mandatory": False,
        "default": "Yes",
        "options": [
            {"label": "Yes it is", "value": "Yes it is"},
            {"label": "No", "value": "No"},
        ],
    }

    validator = OptionAnswerValidator(
        answer, get_mock_schema_with_data_version("0.0.3")
    )

    expected_errors = [
        {
            "message": validator.ANSWER_DEFAULT_MISSING,
            "default_value": "Yes",
            "answer_id": "correct-answer",
        }
    ]

    validator.validate_default_exists_in_options()

    assert expected_errors == validator.errors


def test_min_answer_options_without_dynamic_options():
    answer_type = "Checkbox"
    answer = {"id": "answer", "label": "Label", "type": answer_type, "options": []}

    validator = OptionAnswerValidator(
        answer, get_mock_schema_with_data_version("0.0.3")
    )
    validator.validate_min_options()

    assert validator.errors == [
        {
            "message": validator.NOT_ENOUGH_ANSWER_OPTIONS.format(
                answer_type=answer_type, required_num_options=1, actual_num_options=0
            ),
            "answer_id": "answer",
        }
    ]


def test_min_answer_options_with_dynamic_options():
    answer_type = "Checkbox"
    answer = {
        "id": "answer",
        "label": "Label",
        "type": answer_type,
        "options": [],
        "dynamic_options": {"values": {}, "transform": {}},
    }

    validator = OptionAnswerValidator(
        answer, get_mock_schema_with_data_version("0.0.3")
    )
    validator.validate_min_options()

    assert validator.errors == [
        {"message": validator.OPTIONS_DEFINED_BUT_EMPTY, "answer_id": "answer"}
    ]


def test_dynamic_options_transform_allows_non_map_self_reference():
    answer = {
        "id": "answer",
        "label": "Label",
        "type": "Checkbox",
        "dynamic_options": {
            "values": {"source": "answers", "identifier": "checkbox-answer"},
            "transform": {"option-label-from-value": ["self", "checkbox-answer"]},
        },
    }

    validator = OptionAnswerValidator(
        answer,
        questionnaire_schema=get_mock_schema(
            answers_with_context={
                "checkbox-answer": {
                    "answer": {"id": "checkbox-answer", "type": "Checkbox"}
                }
            }
        ),
    )
    validator.validate_dynamic_options()

    assert not validator.errors


def test_dynamic_options_values_with_invalid_value_rule():
    answer = {
        "id": "answer",
        "label": "Label",
        "type": "Checkbox",
        "dynamic_options": {
            "values": {
                "map": [
                    {"format-date": [{"date": ["now"]}, "yyyy-MM-dd"]},
                    {
                        "date-range": [
                            {
                                "date": [
                                    {
                                        "source": "response_metadata",
                                        "identifier": "started_at",
                                    }
                                ]
                            },
                            7,
                        ]
                    },
                ]
            },
            "transform": {"format-date": [{"date": ["self"]}, "EEEE d MMMM yyyy"]},
        },
    }

    validator = OptionAnswerValidator(
        answer,
        questionnaire_schema=get_mock_schema(
            answers_with_context={
                "checkbox-answer": {
                    "answer": {"id": "checkbox-answer", "type": "Checkbox"}
                }
            }
        ),
    )
    validator.validate_dynamic_options()

    expected_error = {
        "message": RulesValidator.MAP_OPERATOR_WITHOUT_SELF_REFERENCE,
        "origin_id": "answer",
        "rule": {"format-date": [{"date": ["now"]}, "yyyy-MM-dd"]},
    }

    assert validator.errors == [expected_error]


def test_dynamic_options_source_identifier_and_option_label_from_value_mismatch():
    answer = {
        "id": "answer",
        "label": "Label",
        "type": "Radio",
        "dynamic_options": {
            "values": {"source": "answers", "identifier": "checkbox-answer"},
            "transform": {
                "option-label-from-value": ["self", "mismatch-checkbox-answer"]
            },
        },
    }

    validator = OptionAnswerValidator(
        answer,
        questionnaire_schema=get_mock_schema(
            answers_with_context={
                "checkbox-answer": {
                    "answer": {"id": "checkbox-answer", "type": "Checkbox"}
                },
                "mismatch-checkbox-answer": {
                    "answer": {"id": "mismatch-checkbox-answer", "type": "Checkbox"}
                },
            }
        ),
    )
    validator.validate_dynamic_options()

    expected_error = {
        "message": validator.DYNAMIC_OPTIONS_SOURCE_IDENTIFIER_AND_OPTION_LABEL_FROM_VALUE_MISMATCH,
        "source_identifier": "checkbox-answer",
        "transform_identifier": "mismatch-checkbox-answer",
        "answer_id": "answer",
    }

    assert validator.errors == [expected_error]


def test_dynamic_options_transform_with_invalid_answer_id_reference():
    answer = {
        "id": "answer",
        "label": "Label",
        "type": "Checkbox",
        "dynamic_options": {
            "values": {"source": "answers", "identifier": "checkbox-answer"},
            "transform": {"option-label-from-value": ["self", "non-existing-answer"]},
        },
    }

    validator = OptionAnswerValidator(
        answer,
        questionnaire_schema=get_mock_schema(
            answers_with_context={
                "checkbox-answer": {
                    "answer": {"id": "checkbox-answer", "type": "Checkbox"}
                }
            }
        ),
    )
    validator.validate_dynamic_options()

    option_label_from_value_do_not_match_error = {
        "message": validator.DYNAMIC_OPTIONS_SOURCE_IDENTIFIER_AND_OPTION_LABEL_FROM_VALUE_MISMATCH,
        "source_identifier": "checkbox-answer",
        "transform_identifier": "non-existing-answer",
        "answer_id": "answer",
    }

    answer_reference_invalid_error = {
        "message": ValueSourceValidator.ANSWER_SOURCE_REFERENCE_INVALID,
        "identifier": "non-existing-answer",
        "origin_id": "answer",
    }

    assert validator.errors == [
        option_label_from_value_do_not_match_error,
        answer_reference_invalid_error,
    ]


def test_dynamic_options_values_with_non_checkbox_answer_source():
    answer = {
        "id": "answer",
        "label": "Label",
        "type": "Checkbox",
        "dynamic_options": {
            "values": {"source": "answers", "identifier": "non-checkbox-answer"},
            "transform": {"option-label-from-value": ["self", "non-checkbox-answer"]},
        },
    }

    validator = OptionAnswerValidator(
        answer,
        questionnaire_schema=get_mock_schema(
            answers_with_context={
                "non-checkbox-answer": {
                    "answer": {"id": "non-checkbox-answer", "type": "Radio"}
                }
            }
        ),
    )
    validator.validate_dynamic_options()

    expected_error = {
        "message": validator.DYNAMIC_OPTIONS_REFERENCES_NON_CHECKBOX_ANSWER,
        "value_source": {"source": "answers", "identifier": "non-checkbox-answer"},
        "answer_id": "answer",
    }

    assert validator.errors == [expected_error]
