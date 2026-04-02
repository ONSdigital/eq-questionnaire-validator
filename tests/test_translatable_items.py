from app.validators.translatable_items import TranslatableItem, get_translatable_items

schema = {
    "question": {
        "id": "term-time-location-question",
        "type": "General",
        "title": {
            "placeholders": [
                {
                    "placeholder": "person_name",
                    "transforms": [
                        {
                            "arguments": {
                                "delimiter": " ",
                                "list_to_concatenate": {
                                    "identifier": [
                                        "first-name",
                                        "last-name",
                                    ],
                                    "source": "answers",
                                },
                            },
                            "transform": "concatenate_list",
                        }
                    ],
                }
            ],
            "text": "During term time, where does <strong>{person_name}</strong> usually live?",
        },
        "answers": [
            {
                "id": "term-time-location-answer",
                "mandatory": True,
                "options": [
                    {
                        "label": {
                            "placeholders": [
                                {
                                    "placeholder": "address",
                                    "value": {
                                        "identifier": "display_address",
                                        "source": "metadata",
                                    },
                                }
                            ],
                            "text": "{address}",
                        },
                        "value": "household-address",
                    },
                    {
                        "label": {
                            "placeholders": [
                                {
                                    "placeholder": "country",
                                    "value": {
                                        "identifier": "another-address-answer-other-country",
                                        "source": "answers",
                                    },
                                }
                            ],
                            "text": "The address in {country}",
                        },
                        "value": "30-day-address",
                    },
                ],
                "type": "Radio",
            }
        ],
    }
}


def test_get_placeholder_pointers():
    translatable_items = list(get_translatable_items(schema))

    assert (
        TranslatableItem(
            pointer="/question/answers/0/options/0/label/text",
            description="Answer option",
            value="{address}",
            context="During term time, where does <strong>{person_name}</strong> usually live?",
        )
        in translatable_items
    )

    assert (
        TranslatableItem(
            pointer="/question/answers/0/options/1/label/text",
            description="Answer option",
            value="The address in {country}",
            context="During term time, where does <strong>{person_name}</strong> usually live?",
        )
        in translatable_items
    )

    assert (
        TranslatableItem(
            pointer="/question/title/text",
            description="Question text",
            value="During term time, where does <strong>{person_name}</strong> usually live?",
        )
        in translatable_items
    )
