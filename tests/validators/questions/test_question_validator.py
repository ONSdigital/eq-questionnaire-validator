from app.validators.questions import get_question_validator
from tests.conftest import get_mock_schema


def test_no_answer_label_single_answer():
    question = {
        "id": "some-question",
        "title": "Some title",
        "type": "General",
        "answers": [{"id": "number-1", "mandatory": False, "type": "Number"}],
    }

    validator = get_question_validator(question, schema=get_mock_schema())
    validator.validate()

    assert not validator.errors


def test_no_answer_label_multiple_answers():
    question = {
        "id": "some-question",
        "title": "Some title",
        "type": "General",
        "answers": [
            {
                "id": "number-1",
                "label": "Enter the first number",
                "mandatory": False,
                "type": "Number",
            },
            {"id": "number-2", "mandatory": False, "type": "Number"},
        ],
    }

    validator = get_question_validator(question, schema=get_mock_schema())
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.ANSWER_LABEL_MISSING_MULTIPLE_ANSWERS,
            "answer_id": "number-2",
            "question_id": "some-question",
        }
    ]

    assert expected_error_messages == validator.errors


def test_no_answer_label_mutually_exclusive():
    question = {
        "id": "some-question",
        "title": "Some title",
        "type": "MutuallyExclusive",
        "answers": [
            {
                "type": "Checkbox",
                "id": "answer",
                "mandatory": False,
                "options": [
                    {"label": "Option 1", "value": "Option 1"},
                    {"label": "Option 2", "value": "Option 2"},
                ],
            },
            {
                "id": "answer-exclusive",
                "mandatory": False,
                "options": [
                    {
                        "label": "None of the these apply",
                        "value": "None of the these apply",
                    }
                ],
                "type": "Checkbox",
            },
        ],
    }

    validator = get_question_validator(question, schema=get_mock_schema())
    validator.validate()

    assert not validator.errors


def test_no_answer_label_two_answers_last_answer_single_checkbox():
    question = {
        "id": "some-question",
        "title": "Some title",
        "type": "General",
        "answers": [
            {
                "id": "cost",
                "mandatory": False,
                "type": "Radio",
                "options": [
                    {"label": "100", "value": "100"},
                    {"label": "1000", "value": "1000"},
                ],
            },
            {
                "id": "age-estimate",
                "mandatory": False,
                "options": [
                    {"label": "This is an estimate", "value": "This is an estimate"}
                ],
                "type": "Checkbox",
            },
        ],
    }

    validator = get_question_validator(question, schema=get_mock_schema())
    validator.validate()

    assert not validator.errors
