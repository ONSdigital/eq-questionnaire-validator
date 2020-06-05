from app.validators.placeholders.placeholder_validator import PlaceholderValidator


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
