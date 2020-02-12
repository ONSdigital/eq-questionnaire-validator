# 1. Define piping (string interpolation) in a structured way

## Context

The current way we define piping (string interpolation) in a schema is to include jinja filters directly in the source strings. This has a number of issues:

- It's hard to read for translators.
- It's possible that the jinja filters could become corrupted during translation.
- If the way that we resolve the piped information changes, then the translations would all need to be updated.
- We can't easily parse the schema to understand what is being piped, for example to find all places where a specific answer is piped.

## Proposal

To define an appropriate schema to resolve placeholders in a source string. When resolving placeholder values we need to cater for:

- Previous answers or metadata
- Previous answers or metadata transformed in some way e.g. formatting a number with a currency symbol
- Using multiple answers, metadata or fixed values in a transform e.g. formatting a date answer with a specific format
- Chaining transforms e.g. concatenate a name and then add a 's

### Previous answers or metadata

Current:

```json
{
    "description": "What was the <em>total gross weekly pay</em> paid to employees in the last week of {{metadata['period_str']}}?"
}
```

Proposed:

```json
{
    "description": {
        "text": "What was the <em>total gross weekly pay</em> paid to employees in the last week of {period}?",
        "placeholders": [
            {
                "placeholder": "period",
                "value": {
                    "source": "metadata",
                    "identifier": "period_str"
                }
            }
        ]
    }
}
```

## Previous answers or metadata transformed in some way

Current:

```json
{
    "description": "Of the <em>{{format_currency(answers['total-retail-turnover-answer'])}}</em> total retail turnover, what was the value of internet sales?"
}
```

Proposed:

```json
{
    "description": {
        "text": "Of the <em>{total_turnover}</em> total retail turnover, what was the value of internet sales?",
        "placeholders": [
            {
                "placeholder": "total_turnover",
                "transforms": [
                    {
                        "transform": "format_currency",
                        "arguments": {
                            "number": {
                                "source": "answers",
                                "identifier": "total-retail-turnover-answer"
                            }
                        }
                    }
                ]
            }
        ]
    }
}
```

## Using multiple answers, metadata or fixed values in a transform

```json
{
    "description": "Are you able to report for the period starting on {{format_date_custom(metadata['ref_p_start_date'], 'EEEE d MMMM yyyy')}}?"
}
```

Proposed:

```json
{

    "description": {
        "text": "Are you able to report for the period starting on {start_date}?",
        "placeholders": [
            {
                "placeholder": "start_date",
                "transforms": [
                    {
                        "transform": "format_date",
                        "arguments": {
                            "date": {
                                "source": "metadata",
                                "identifier": "ref_p_start_date"
                            },
                            "format": "EEEE d MMMM yyyy"
                        }
                    }
                ]
            }
        ]
    }
}
```

## Chaining transforms

Current:

```json
{
    "description": "What is <em>{{[answers['first-name'][group_instance], answers['last-name'][group_instance]] | format_household_name_possessive }}</em> date of birth?""
}
```

Proposed:

```json
{
    "description": {
        "text": "What is <em>{persons_name}</em> date of birth?",
        "placeholders": [
            {
                "placeholder": "persons_name",
                "transforms": [
                    {
                        "transform": "concatenate_list",
                        "arguments": {
                            "list": {
                                "source": "answers",
                                "identifier": ["first-name","last-name"]
                            },
                            "delimiter": " "
                        }
                    },
                    {
                        "transform": "format_possessive",
                        "arguments": {
                            "string": {
                                "source": "previous_transform"
                            }
                        }
                    }
                ]
            }
        ]
    }
}
```

## Full worked example (with surrounding schema)

Original:

```json
{
    "type": "ConfirmationQuestion",
    "id": "confirm-dob-proxy",
    "questions": [{
        "id": "confirm-date-of-birth-proxy",
        "title": "{{[answers['first-name'][group_instance], answers['last-name'][group_instance]] | format_household_name}} is {{ calculate_years_difference (answers['date-of-birth-answer'][group_instance], 'now') }} old. Is this correct?",
        "type": "General",
        "answers": [{
            "id": "confirm-date-of-birth-answer-proxy",
            "mandatory": true,
            "options": [{
                    "label": "Yes, {{[answers['first-name'][group_instance], answers['last-name'][group_instance]] | format_household_name}} is {{ calculate_years_difference (answers['date-of-birth-answer'][group_instance], 'now') }} old",
                    "value": "Yes"
                },
                {
                    "label": "No, I need to change their date of birth",
                    "value": "No"
                }
            ],
            "type": "Radio"
        }]
    }]
}
```

Proposed:

```json
{
    "type": "ConfirmationQuestion",
    "id": "confirm-dob-proxy",
    "questions": [{
        "id": "confirm-date-of-birth-proxy",
        "title": {
            "text": "{person_name} is {age_in_years} old. Is this correct?",
            "placeholders": [
                {
                    "placeholder": "person_name",
                    "transforms": [
                        {
                            "transform": "concatenate_list",
                            "arguments": {
                                "list": {
                                    "source": "answers",
                                    "identifier": ["first-name","last-name"]
                                },
                                "delimiter": " "
                            }
                        }
                    ]
                },
                {
                    "placeholder": "age_in_years",
                    "transforms": [
                        {
                            "transform": "calculate_years_difference",
                            "arguments": {
                                "first_date": {
                                    "source": "answers",
                                    "identifier": "date-of-birth-answer"
                                },
                                "second_date": {
                                    "value": "now"
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "type": "General",
        "answers": [{
            "id": "confirm-date-of-birth-answer-proxy",
            "mandatory": true,
            "options": [{
                    "label": {
                        "text": "{person_name} is {age_in_years} old. Is this correct?",
                        "placeholders": [
                            {
                                "placeholder": "person_name",
                                "transforms": [
                                    {
                                        "transform": "concatenate_list",
                                        "arguments": {
                                            "list": {
                                                "source": "answers",
                                                "identifier": ["first-name","last-name"]
                                            },
                                            "delimiter": " "
                                        }
                                    }
                                ]
                            },
                            {
                                "placeholder": "age_in_years",
                                "transforms": [
                                    {
                                        "transform": "calculate_years_difference",
                                        "arguments": {
                                            "first_date": {
                                                "source": "answers",
                                                "identifier": "date-of-birth-answer"
                                            },
                                            "second_date": {
                                                "value": "now"
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    "value": "Yes"
                },
                {
                    "label": {
                        "text": "No, I need to change their date of birth"
                    },
                    "value": "No"
                }
            ],
            "type": "Radio"
        }]
    }]
}
```

Note: The repetition of placeholder resolution in the same block is rare

---


## Other notes

- No provision has been made in the schema design for group instances. It is assumed that:
  - When a placeholder is used in a non-repeating group that any reference to answers resolves to all answers that match the answer id.
  - When a placeholder is used in a repeating group that any reference to answers resolves to the answer that matches within the current repeat.
- `format_date_range` and `format_datetime` should be done via two separate placeholders rather than a transform, so that the 'to' and 'at' are in the sentence to be translated.
- Jinja filters are used to resolve values in the variables schema e.g. `period` in 1_0005. This will no longer work and will require some further design outside of the scope of this proposal.
