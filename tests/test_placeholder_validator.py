import json
import os

import pytest

from app.validators.placeholders.placeholder_validator import PlaceholderValidator
from app.validators.questionnaire_schema import QuestionnaireSchema


def test_invalid_repeating_section_title_placeholders():
    placeholder_container = {
        "text": "{person}",
        "placeholders": [
            {
                "placeholder": "person_name",
                "transforms": [
                    {
                        "transform": "concatenate_list",
                        "arguments": {
                            "list_to_concatenate": [
                                {"source": "answers", "identifier": "first-name"},
                                {"source": "answers", "identifier": "last-name"},
                            ],
                            "delimiter": " ",
                        },
                    }
                ],
            }
        ],
    }

    validator = PlaceholderValidator({})
    validator.validate_placeholder_object(placeholder_container)

    expected_errors = [
        {
            "message": validator.PLACEHOLDERS_DONT_MATCH_DEFINITIONS,
            "text": "{person}",
            "differences": {"person"},
        }
    ]

    assert validator.errors == expected_errors


def test_placeholder_plurals():
    placeholder_container = {
        "text_plural": {
            "forms": {
                "one": "You’ve said one person lives here. Is that correct?",
                "other": "You’ve said {number_of_people} people live here. Is that correct?",
            },
            "count": {"source": "answers", "identifier": "answer1"},
        },
        "placeholders": [
            {
                "placeholder": "number_of_persons",
                "transforms": [
                    {
                        "transform": "number_to_words",
                        "arguments": {
                            "number": {"source": "answers", "identifier": "answer1"}
                        },
                    }
                ],
            }
        ],
    }

    validator = PlaceholderValidator({})
    validator.validate_placeholder_object(placeholder_container)

    expected_errors = [
        {
            "message": validator.PLACEHOLDERS_DONT_MATCH_DEFINITIONS,
            "text": "You’ve said {number_of_people} people live here. Is that correct?",
            "differences": {"number_of_people"},
        }
    ]

    assert validator.errors == expected_errors


def _open_and_load_schema_file(file):
    with open(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), file), encoding="utf8"
    ) as json_file:
        return json.load(json_file)


@pytest.mark.parametrize(
    "answer_id,expected_error",
    [
        ("test", [{"message": "Invalid answer reference", "identifier": "test"}]),
        (
            "body-part-name",
            [
                {
                    "identifier": "body-part-name",
                    "message": "The referenced answer_id type is not of type ['Radio','Checkbox','Dropdown']",
                }
            ],
        ),
    ],
)
def test_validation_option_label_from_value(answer_id, expected_error):
    filename = "schemas/invalid/test_invalid_placeholder_option_label_from_value.json"
    schema_file = _open_and_load_schema_file(filename)
    schema = QuestionnaireSchema(schema_file)
    validator = PlaceholderValidator({})
    validator.questionnaire_schema = schema
    validator.validate_option_label_value_placeholder(answer_id)
    assert validator.errors == expected_error
