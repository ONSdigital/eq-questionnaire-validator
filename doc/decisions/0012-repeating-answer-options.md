# 12. Dynamically creating answers based on a list

## Context

We need the ability to dynamically generate answers based on a list item.

We need to support dynamic options that are driven by:

- List collectors
- Arbitrary functions that return a sequence of values.

Additional requirements:

- Ability for the label and value to be different
- When driven by list collectors, the option's `value` is the `list_item_id` and the `label` is some transformed value on answers stored against the list item id, e.g. `FirstName LastName`.
- When driven by answers, the option's `value` should be the answer value, and the `label` should be resolved to the schema label based on the answer id, list item id, and option value.
- Supports translated schemas since we are resolving to the label.
- Values to resolve correctly when inside and outside of repeats.

## Proposal

Introduce a new `repeating_answers` object that will handle the generation of any dynamic options.

Properties and uses:

- `dynamic_options`
    - Used to define the an array of questions that will be asked for each answer in the list.
    - Structure to follow the structure for regular question answers.

### Dynamic answer options

```json
{
    "question": {
        "id": "percentage-of-research",
        "title": {
            "text": "Which percentage of R&D carried out by {company_name} was at each postcode",
            "placeholders": [
                {
                    "placeholder": "company_name",
                    "value": {
                        "source": "metadata",
                        "identifier": "ru_name"
                    }
                }
            ]
        },
        "type": "Question",
        "repeating_answers": [
            {
                "description": "Percentage of R&D carried out at {transformed_value}",
                "id": "percentage-of-research-{transformed_value}",
                "mandatory": false,
                "type": "Percentage",
                "maximum": {
                    "value": 100
                },
                "decimal_places": 2
            },
            {
                "transform": {
                    "values": {
                        "source": "list",
                        "identifier": "post_codes",
                        "id_selector": "items"
                    }
                }
            }
        ]
    }
}
```

## Consequences

- Dynamic answer options can be driven a list or a sequence of values.
- Consistent with other answer structure.
- Consistent with new rules structure.
- Although we resolve an answer value to its label when using Checkbox answers to drive the dynamic options, support for translations are out of scope, and no guarantees are provided.
