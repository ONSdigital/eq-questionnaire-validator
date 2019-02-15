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

To allow proxy versions of interstitials, a top-level `content_variants` object has been introduced. The variant to display will be chosen based on the `when` conditions for each object in the variants block. 

```json
{
    "type": "Interstitial",
    "id": "past-main-employment-block",
    "content_variants": [
        {
            "content": {
                "id": "past-main-employment-content",
                "type": "Content",
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
            "when": [{
                "id": "proxy-answer",
                "condition": "equals",
                "value": "no"
            }]
        },
        {
            "content": {
                "id": "past-main-employment-content",
                "type": "Content",
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
            },
            "when": [{
                "id": "proxy-answer",
                "condition": "equals",
                "value": "proxy"
            }],
        }
    ],
    "routing_rules": [{
        "goto": {
            "block": "main-job-type-past"
        }
    }]
}
```

Each variant object can contain a content object and a when rule which governs whether the content should be displayed.

Variants will be evaluated in order.

Variants with a length of one should be disallowed since they can be moved out of the `content_variants` object.

### Question

For questions, the basic premise is to use the multiple question scheme that is currently possible with some changes to keep them aligned with interstitials:

 ```json
{
    "id": "example",
    "type": "Question",
    "question_variants": [{
        "question": {
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
        "when": [{
            "id": "proxy-answer",
            "condition": "equals",
            "value": "no"
        }]
    },
    {
        "question": {
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
        },
        "when": [{
            "id": "proxy-answer",
            "condition": "equals",
            "value": "proxy"
        }]
    }]
}
```

Each variant should have the same structure as questions currently do. 

The `questions` key should be removed from the block and replaced with `question` and `question_variant`.

Single variants should be disallowed (i.e. length of variants == 1) since a variants object should be converted to a question at this point.

### Additional Changes
- The current `titles` key should be removed and replaced with `title` which is a string.
- `questions` should be removed and relpaced with `question` object which only allows a single question.
- The schema validator should ensure that question_variants and content_variants has a length of greater than one.
- Answer IDs within variants should allow duplicates. This means routing becomes simpler for proxy etc.

