from app import error_messages
from app.validators.placeholders.placeholder_validator import PlaceholderValidator
from app.validators.questionnaire_schema import QuestionnaireSchema


def test_invalid_repeating_section_title_placeholders():
    questionnaire_schema = QuestionnaireSchema({})

    placeholder_container = {
        "text": "{person}",
        "placeholders": [
            {
                "placeholder": "person_name",
                "transforms": [
                    {
                        "transform": "concatenate_list",
                        "arguments": {
                            "list_to_concatenate": {
                                "source": "answers",
                                "identifier": ["first-name", "last-name"],
                            },
                            "delimiter": " ",
                        },
                    }
                ],
            }
        ],
    }

    validator = PlaceholderValidator({}, questionnaire_schema)
    validator.validate_placeholder_object(placeholder_container, None)

    expected_errors = [
        {
            "message": error_messages.PLACEHOLDERS_DONT_MATCH_DEFINITIONS,
            "text": "{person}",
            "differences": {"person"},
        }
    ]

    assert validator.errors == expected_errors
