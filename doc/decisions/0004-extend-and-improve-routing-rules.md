# 4. Extend and improve routing rules

## Context

There are some issues with the current structure of routing rules:

- They only support limited `AND` and `OR` logic - `OR` is only supported outside of a `when` block leading to duplicate routing targets 
- Logic can't be nested for more nuanced rules
- Dynamic values (answers, metadata, lists) are referenced inconsistently

Routing rules in Author don't suffer from the first issue (see https://github.com/ONSdigital/eq-author-app/wiki/Routing,-MK2); they were used as a starting point for this proposal, combined with ideas from http://jsonlogic.com.

## Proposal

We will define a rule as an operation and it's arguments:

```
{ 
    "operation": [
        "argument1", "argument2"
    ]
}
```

An argument can be an operation:

```
{
    "operation": [
        {
            "operation2": [
                "argument1"
            ],
        }
        "argument2"
    ]
}
```

- Operations can be boolean (and, or, equal etc.), numeric (more than, less than etc.) or array (contains etc.)
- An operation can take any number of arguments
- References to dynamic values - answers, metadata, lists and location - can be used in place of any argument

### Worked example

Using the example:

```
(answer1 = "No" OR unanswered) AND answer2 != 8 AND answer4 > answer3
```

The rule definition is:

```json
{
    "and": [
        {
            "or": [
                {
                    "equal": [
                        {
                            "source": "answers",
                            "identifier": "answer1"
                        },
                        "No"
                    ]
                },
                {
                    "not-answered": [
                        {
                            "source": "answers",
                            "identifier": "answer1"
                        }
                    ]
                }
            ]
        },
        {
            "not-equal": [
                {
                    "source": "answers",
                    "identifier": "answer2"
                },
                8
            ]
        },
        {
            "greater-than": [
                {
                    "source": "answers",
                    "identifier": "answer4"
                },
                {
                    "source": "answers",
                    "identifier": "answer3"
                }
            ]
        }
	]
}
```

## Consequences

- This is a breaking change. All places where rules are used will need to be migrated
- Rules are more consistent
- More advanced logic is possible
- Author conversion process is less complicated


## Other information

### Converting current rules

#### equals

Current:
```json
{
    "condition": "equals",
    "id": "you-live-here-answer",
    "value": "No"
}
```

Proposed:
```json
{
    "equal": [
        {
            "source": "answers",
            "identifier": "you-live-here-answer"
        },
        "No"
    ]
}
```

All of the other simple boolean operators would work in the same way:
- `not-equal`
- `greater-than`
- `greather-than-or-equal-to`
- `less-than`
- `less-than-or-equal-to`

We should consider using the short form of expressing these rules (`==`, `!=`, `>`, `>=`, `<`, `<=`).

#### equals any

Current:
```json
{
    "condition": "equals any",
    "id": "confirm-date-of-birth-answer",
    "values": [
        "No, I need to change their date of birth",
        "No, I need to change my date of birth"
    ]
}
```

Proposed:
```json
{
    "in": [
        {
            "source": "answers",
            "identifier": "confirm-date-of-birth-answer"
        },
        [
            "No, I need to change their date of birth",
            "No, I need to change my date of birth"
        ]
    ]
}
```

#### not equals any

Current:
```json
{
    "condition": "not equals any",
    "id": "confirm-date-of-birth-answer",
    "values": [
        "No, I need to change their date of birth",
        "No, I need to change my date of birth"
    ]
}
```

Proposed:
```json
{
    "not": [
        {
            "in": [
                {
                    "source": "answers",
                    "identifier": "confirm-date-of-birth-answer"
                },
                [
                    "No, I need to change their date of birth",
                    "No, I need to change my date of birth"
                ]
            ]
        }
    ]
}
```

#### contains

Current:
```json
{
    "condition": "contains",
    "id": "understand-irish-answer",
    "value": "Speak Irish"
}
```

Proposed:
```json
{
    "in": [
        "Speak Irish",
        {
            "source": "answers",
            "identifier": "understand-irish-answer"
        }
    ]
}
```

Note that this uses the `in` operation with the arguments reversed (rather than defining another operation).

#### greater than date with offset

Current:
```json
{
    "condition": "greater than",
    "date_comparison": {
        "offset_by": {
            "years": -16
        },
        "value": "now"
    },
    "id": "date-of-birth-answer"
}
```

Proposed:
```json
{
    "greater-than": [
        {
            "source": "answers",
            "identifier": "date-of-birth-answer"
        },
        {
            "date-offset": [
                {
                    "source": "date",
                    "value": "now"
                },
                { "years": -16 }
            ]
        }
    ]
}
```

This example demonstrates the extensibility of this approach as new operations can be easily added.

#### list

Current:
```json
{
    "condition": "greater than",
    "list": "household",
    "value": 0
}
```

Proposed:
```json
{
    "greater-than": [
        {
            "source": "list",
            "identifier": "household"
        },
        0
    ]
}
```

#### location

Current:
```json
{
    "comparison": {
        "id": "list_item_id",
        "source": "location"
    },
    "condition": "equals",
    "id_selector": "primary_person",
    "list": "household"
}
```

Proposed:
```json
{
    "equal": [
        {
            "source": "list",
            "identifier": "household",
            "id_selector": "primary_person",
        },
        {
            "source": "location",
            "identifier": "list_item_id"
        }
    ]
}
```

#### combined not equals and greater than date

Current:
```json
[
    {
        "condition": "not equals",
        "id": "past-usual-address-household-answer",
        "value": "An address outside the UK"
    },
    {
        "condition": "greater than",
        "date_comparison": {
            "offset_by": {
                "years": -16
            },
            "value": "now"
        },
        "id": "date-of-birth-answer"
    }
]
```

Proposed:
```json
{
    "and": [
        {
            "not-equal": [
                {
                    "source": "answers",
                    "identifier": "past-usual-address-household-answer"
                },
                "An address outside the UK"
            ]
        },
        {
            "greater-than": [
                {
                    "source": "answers",
                    "identifier": "date-of-birth-answer"
                },
                {
                    "date-offset": [
                        {
                            "source": "date",
                            "value": "now"
                        },
                        { "years": -16 }
                    ]
                }
            ]
        }
    ]
}
```
