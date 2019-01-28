# 2. Define a more flexible approach to proxy questions

## Context
Currently, the solution for proxy question titles has some limitations:

- Unable to modify any part of a question except the title
- Current solution difficult to integrate with structured string interpolation.
- Does not support interstitials

Since only titles are currently changeable, routing and duplicated blocks have been used to resolve this, but this can cause issues when routing becomes complicated or changes need to be made later on.

### Example of current question schema

Currently, proxy titles are defined through the question `titles` object:

 ```json
{
    "id": "example",
    "type": "Question",
    "questions": [{
        "id": "example-question",
        "titles": [{
                "value": "Did they work today?",
                "when": [{
                    "id": "proxy-check-answer",
                    "condition": "equals",
                    "value": "proxy"
                }]
            },
            {
                "value": "Did you do any work today?"
            }
        ],
        "type": "General",
        "answers": [{
            "id": "example-answer",
            "mandatory": true,
            "type": "Radio",
            "options": [{
                    "label": "Yes",
                    "value": "Yes"
                },
                {
                    "label": "No",
                    "value": "No"
                }
            ]
        }]
    }]
}
```

### Current multiple questions with skip conditions

Currently, it is possible to create a proxy variant of questions within a block. This takes advantage of the capability for multiple questions within a block where each question includes a skip condition.

Example:

```json
{
    "id": "example",
    "type": "Question",
    "questions": [{
        "id": "example-question",
        "title": "Did you do any work today?",
        "type": "General",
        "answers": [{
            "id": "example-answer",
            "mandatory": true,
            "type": "Radio",
            "options": [{
                    "label": "Yes",
                    "value": "Yes"
                },
                {
                    "label": "No",
                    "value": "No"
                }
            ]
        }],
        "skip_conditions": [{
            "when": [{
                "id": "proxy-check-answer",
                "condition": "equals",
                "value": "no"
            }],
        }]
    },
    {
        "id": "example-question-proxy",
        "title": "Did they do any work today?",
        "type": "General",
        "answers": [{
            "id": "example-answer-proxy",
            "mandatory": true,
            "type": "Radio",
            "options": [{
                    "label": "Yes",
                    "value": "Yes"
                },
                {
                    "label": "No",
                    "value": "No"
                }
            ]
        }],
        "skip_conditions": [{
            "when": [{
                "id": "proxy-check-answer",
                "condition": "equals",
                "value": "proxy"
            }],
        }]
    }]
}
```

### Example of current interstitial schema

Interstitials do not currently support proxy titles, so the current method to use them in schemas which require proxy is to create multiple interstitials and route between them according to a proxy question.

Example (assumes a previous question routes to one of these depending on a proxy question):

```json
{
    "type": "Interstitial",
    "id": "past-main-employment-block",
    "title": "Answer the remaining questions for your last main job",
    "description": "Your main job is the job in which you usually worked the most hours",
    "content": [
        {
            "title": "Some extra information",
            "list": [
                "A list of thing",
                "Some of these things are needed"
            ]
        },
        {
            "description": "Some more extra information"
        }
    ],
    "routing_rules": [{
        "goto": {
            "block": "main-job-type-past"
        }
    }]
},
{
    "type": "Interstitial",
    "id": "past-main-employment-block-proxy",
    "title": "Answer the remaining questions for {{[answers['first-name'][group_instance], answers['last-name'][group_instance]] | format_household_name_possessive}} last main job",
    "description": "Their main job is the job in which they usually worked the most hours",
    "content": [
        {
            "title": "Some extra information",
            "list": [
                "A list of thing",
                "Some of these things are needed"
            ]
        },
        {
            "description": "Some more extra information"
        }
    ],
    "routing_rules": [{
        "goto": {
            "block": "main-job-type-past"
        }
    }]
}
```

## Requirements of future solution

Must support proxy versions for the following features:

- Answer guidance
    - You / They
        - `How you define your ethnic group is up to you`
        - `How they define their ethnic group is up to them`
    - You / Name
        - `If you are self-employed in your own business, give the business name`
        - `If {proxy_person_name} is self-employed in their own business, give the business name.`
- Detail Answer
    - Label may change between proxy versions:
        - `Please describe your national identity`
        - `Please describe their national identity`
- Interstitial
    - Past / Present and by proxy
        - Past: `Answer the next set of questions for your last main job`
        - Past Proxy: `Answer the next set of questions for {proxy_name_posessive} last main job`
        - Current: `Answer the next set of questions for your main job`
        - Current Proxy: `Answer the next set of questions for {proxy_name_posessive} main job`
- Response Options
    - Confirmation
        - `Yes, I am {age_years} old`
        - `Yes, {proxy_name} is {age_years} old`
        - `No, I need to change my date of birth`
        - `No, I need to change {proxy_name_posessive} date of birth`
        
        
## Proposal

### Interstitial

To allow proxy versions of interstitials, a top-level `variants` object has been introduced. The variant to display will be chosen based on the `when` conditions listed in the `variant_choice` list. `routing_rules` and block `id` are kept at the top-level, so these cannot be changed as part of the proxy variant.

```json
{
    "type": "Interstitial",
    "id": "past-main-employment-block",
    "variants": {
        "past-main-employment": {
            "title": "Answer the remaining questions for your last main job",
            "description": "Your main job is the job in which you usually worked the most hours",
            "content": [
                {
                    "title": "Some extra information",
                    "list": [
                        "A list of thing",
                        "Some of these things are needed"
                    ]
                },
                {
                    "description": "Some more extra information"
                }
            ]
        },
        "past-main-employment-proxy": {
            "title": "Answer the remaining questions for {{[answers['first-name'][group_instance], answers['last-name'][group_instance]] | format_household_name_possessive}} last main job",
            "description": "Their main job is the job in which they usually worked the most hours",
            "content": [
                {
                    "title": "Some extra information",
                    "list": [
                        "A list of thing",
                        "Some of these things are needed"
                    ]
                },
                {
                    "description": "Some more extra information"
                }
            ]
        }
    },
    "variant_choice": [
        {
            "variant": "past-main-employment-proxy",
            "when": [{
                "id": "proxy-answer",
                "condition": "equals",
                "value": "proxy"
            }]
        },
        {
            "variant": "past-main-employment",
        }
    ],
    "routing_rules": [{
        "goto": {
            "block": "main-job-type-past"
        }
    }]
}
```

Variant choice is composed of a list of objects, these will be evaluated in the order of the list and the first matching variant will be chosen for display.

A default variant may be enforced, e.g. one of the variants does not include a when condition and will be used if no previous variants match.

An object has been used for the variants key to allow the id of each variant to be looked up efficiently.

Variants with a length of one should be disallowed since they can be moved out of the `variants` object.

### Question

For questions, the basic premise is to use the multiple question scheme that is currently possible with some changes to keep them aligned with interstitials:

 ```json
{
    "id": "example",
    "type": "Question",
    "variants": {
        "example-question": {
            "id": "example-question",
            "title": "Did you do any work today?",
            "type": "General",
            "answers": [{
                "id": "example-answer",
                "mandatory": true,
                "type": "Radio",
                "options": [{
                        "label": "Yes",
                        "value": "Yes"
                    },
                    {
                        "label": "No",
                        "value": "No"
                    }
                ]
            }]
        },
        "example-question-proxy": {
            "id": "example-question-proxy",
            "title": "Did they do any work today?",
            "type": "General",
            "answers": [{
                "id": "example-answer-proxy",
                "mandatory": true,
                "type": "Radio",
                "options": [
                    {
                        "label": "Yes",
                        "value": "Yes"
                    },
                    {
                        "label": "No",
                        "value": "No"
                    }
                ]
            }]
        }
    },
    "variant_choice": [
        {
            "variant": "example-question-proxy",
            "when": [{
                "id": "proxy-answer",
                "condition": "equals",
                "value": "proxy"
            }]
        },
        {
            "variant": "example-question"
        }
    ]
}
```

Each variant should have the same structure as questions currently do, including the `id`. The key of each object in `variants` is a label for that variant and does not necessarily correspond to the question id.

Skip conditions on questions have been moved to the top level of the block and into `variant_choice`. This enforces a seperation between the questions themselves and the logic around whether or not they should be displayed.

The schema should intitially still allow `question` to be used for questions which don't require a variant form. The question should still use the same object schema as currently found within `questions`.

Single variants should be disallowed (i.e. length of variants == 1) since a variants object should be converted to a question at this point.

### Additional Changes
- The current `titles` key should be removed and replaced with `title` which is a string.
- `questions` should be removed and relpaced with `question` object which only allows a single question.
- The schema validator should ensure that variants has a length of greater than one.
- The schema validator should enforce at least one variant_choice without a `when` condition as a default choice.
