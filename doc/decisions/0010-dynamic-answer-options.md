# 10. Dynamic Answer Options

## Context

We need the ability to generate answer options for Checkbox and Radio answers dynamically.

We need to support dynamic options that are driven by:

- Checkbox answers
- List collectors
- Arbitrary functions that return a sequence of values.

Additional requirements:

- Ability for the label and value to be different
    - When driven by list collectors, the option's `value` is the `list_item_id` and the `label` is some transformed value on answers stored against the list item id, e.g. `FirstName LastName`.
        - When driven by answers, the option's `value` should be the answer value, and the `label` should be resolved to the schema label based on the answer id, list item id, and option value.
        - Supports translated schemas since we are resolving to the label.
        - Allows for value to be different to the label.
- Values to resolve correctly when inside and outside of repeats.

## Proposal

Introduce a new `dynamic_options` object that will handle the generation of any dynamic options.
Existing `options` property to stay as is to provide the ability to define additional options. The additional options will always be appended to the bottom.

Properties and uses:

- `dynamic_options.values`
    - Used to define the literal values used for [`options.*.value`](https://github.com/ONSdigital/eq-questionnaire-validator/blob/master/schemas/answers/definitions.json#L17-L19).
    - Structure to allow either a Value Source that returns a sequence or the new Rules structure.
- `dynamic_options.transform`
    - Used to apply some transform on each value provided to `dynamic_options.values` which will be used for [`options.*.label`](https://github.com/ONSdigital/eq-questionnaire-validator/blob/master/schemas/answers/definitions.json#L14-L16).
    - Structure to follow the new Rules structure allowing for the chaining of operators. All transforms are new [value operators](https://github.com/ONSdigital/eq-questionnaire-validator/tree/master/schemas/rules/operators/value).
    - The reference to `self` within a transform refers to the value of the current iteration.
      Some mechanism is needed to identify the value of the current iteration and pass it to transforms. For example, in the JSON Logic lib, this is done using `var.""` however, the meaning is not strictly clear, hence `self` was chosen.
      References to `self` will be resolved before passing the transform in the Rules evaluator. This means the rules can operate as is without any coupling with `dynamic_options`.

### Dynamic answer options with arbitrary sequence (Full week date range)

```json
{
  "id": "answer-id",
  "mandatory": true,
  "type": "Checkbox",
  "dynamic_options": {
    "values": {
      "map": [
        {
          "date-range": [
            {
              "date": [
                {
                  "source": "response_metadata",
                  "identifier": "started_at"
                },
                {
                  "days": -7,
                  "day_of_week": "MONDAY"
                }
              ]
            },
            7
          ]
        },
        {
          "format_date": [
            "self",
            "%Y-%m-%d"
          ]
        }
      ]
    },
    "transform": {
      "format_date": [
        "self",
        "%A %d %B %Y",
        "%Y-%m-%d"
      ]
    }
  },
  "options": [
    {
      "label": "None of the above",
      "value": "None of the above"
    }
  ]
}
```

- The `date` operator takes an offset object; this currently only supports `days`, `months`, and `years`.
  This has been extended to support a `day_of_week` property, allowing a date to be set to a specific day for the given week. This can be combined with the numerical offsets to achieve behaviours such as "last Monday", "next Monday" etc. To achieve this, **the day_of_week offset needs to be applied after any numerical offsets.**.
- The `date-range` operation returns a list of `datetime` objects for a specified range from a given date. It takes a `datetime` object, the range in days (+/-), to return.
- The `format_date` is used to return a formatted string date. It takes three arguments, the datetime object, or a string date, the format to return and an input format (Used with string inputs).
    - This could be broken down into two explicit operations, `format_string_date` and `formate_datetime`, so each has a single responsibility.
- The `map` operator has been introduced to apply operations on each value of a sequence. It takes two-argument, first, a sequence, and second the operation to apply to each item in the sequence.
  The reference to `self` within the `map` operator refers to the current iteration's value.

### Dynamic answer options with non-repeating answer source (Checkbox)

```json
{
  "id": "answer-id",
  "mandatory": true,
  "type": "Checkbox",
  "dynamic_options": {
    "values": {
      "source": "answers",
      "identifier": "checkbox-answer-id"
    },
    "transform": {
      "option_label_from_value": [
        "self",
        "checkbox-answer-id"
      ]
    }
  },
  "options": [
    {
      "label": "None of the above",
      "value": "None of the above"
    }
  ]
}
```

- Given an answer id, list item id and, an option's value, `option_label_from_value` is responsible for resolving the label for that option's value.

### Dynamic answer options with repeating answer source within a repeat (Checkbox)

```json
{
  "id": "answer-id",
  "mandatory": true,
  "type": "Checkbox",
  "dynamic_options": {
    "values": {
      "source": "answers",
      "identifier": "checkbox-answer-id",
      "list_item_selector": {
        "source": "location",
        "id": "list_item_id"
      }
    },
    "transform": {
      "answer_label_from_value": [
        "self",
        "checkbox-answer-id",
        {
          "source": "location",
          "identifier": "list_item_id"
        }
      ]
    }
  },
  "options": [
    {
      "label": "None of the above",
      "value": "None of the above"
    }
  ]
}
```

- `values.list_item_selector` is not strictly needed. Dynamic options code could always pass the current list item id, and there is already logic in our value source resolver to use that list item id if the answer id is in a repeating section or a list collector block.

### Dynamic answer options with repeating answer source outside a repeat (Checkbox)

```json
{
  "id": "answer-id",
  "mandatory": true,
  "type": "Checkbox",
  "dynamic_options": {
    "values": {
      "source": "answers",
      "identifier": "checkbox-answer-id",
      "list_item_selector": {
        "source": "list",
        "id": "people",
        "id_selector": "first"
      }
    },
    "transform": {
      "answer_label_from_value": [
        "self",
        "checkbox-answer-id",
        {
          "source": "list",
          "id": "people",
          "id_selector": "first"
        }
      ]
    }
  },
  "options": [
    {
      "label": "None of the above",
      "value": "None of the above"
    }
  ]
}
```

### Dynamic answer options with list source

```json
{
  "id": "answer-id",
  "mandatory": true,
  "type": "Checkbox",
  "dynamic_options": {
    "values": {
      "source": "list",
      "identifier": "people",
      "id_selector": "items"
    },
    "transform": {
      "concat": [
        [
          {
            "source": "answers",
            "identifier": "first-name"
          },
          {
            "source": "answers",
            "identifier": "last-name"
          }
        ],
        " "
      ]
    }
  },
  "options": [
    {
      "label": "None of the above",
      "value": "None of the above"
    }
  ]
}
```

- The `concat` operator is responsible for concatenating a sequence of values using a delimiter.
  This example demonstrates formatting the answer values for each list item.
- When dynamic options are used with a `list` source, the `list_item_id` is not passed explicitly as `self` as the call is responsible for using the rule evaluator in the context of the current list item id. 
  Alternatively, we could introduce a new property such as `list_item_id` to answer value source to support passing in explicit values.

## Consequences

- Dynamic answer options can be driven by any value source or value operators that return a sequence of values.
- Consistent with new rules structure.
- Although we resolve an answer value to its label when using Checkbox answers to drive the dynamic options, support for translations are out of scope, and no guarantees are provided.
- `answer.*.options` can be optional when `dynamic_options` are defined. The necessary guards will need to be in place to ensure the answer always have a minimum of 2 options.
- Answer option action (`options.*.action`) will not be supported for dynamic options.
- Support for the nested use of dynamic options, i.e. dynamically generated options, populating other dynamic options, is out of scope.
