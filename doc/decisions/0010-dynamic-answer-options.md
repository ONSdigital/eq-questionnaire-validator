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
    - Used to define the literal values used for [`options.*.value`](https://github.com/ONSdigital/eq-questionnaire-validator/blob/main/schemas/answers/definitions.json#L17-L19).
    - Structure to allow either a Value Source that returns a sequence or the any of the [new value operators](https://github.com/ONSdigital/eq-questionnaire-validator/tree/main/schemas/rules/operators/value) that returns a sequence.
- `dynamic_options.transform`
    - An optional property used to apply some transform on each value provided to `dynamic_options.values` which will be used for [`options.*.label`](https://github.com/ONSdigital/eq-questionnaire-validator/blob/main/schemas/answers/definitions.json#L14-L16). If omitted, labels will use `dynamic_options.values` as the source.
    - Structure to follow the new Rules structure allowing for the chaining of operators. All transforms are new [value operators](https://github.com/ONSdigital/eq-questionnaire-validator/tree/main/schemas/rules/operators/value).
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
          "format-date": [
            "self",
            "%Y-%m-%d"
          ]
        },
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
        }
      ]
    },
    "transform": {
      "format-date": [
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
- The `format-date` is used to return a formatted string date. It takes three arguments, the datetime object, or a string date, the format to return and an input format (Used with string inputs).
    - This could be broken down into two explicit operations, `format_string_date` and `format-datetime`, so each has a single responsibility.
- The `map` operator has been introduced to apply operations on each value of a sequence. It takes two-argument, first, the operation to apply to each item, second, the sequence of values on which the operation is applied.
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
  This is required as the label and value does not necessarily always match. We store the option's value, but the user sees the label; hence when rerendering an answer option, we need to use the label for the given value.

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
      "option_label_from_value": [
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
      "option_label_from_value": [
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

### Resolving the value for `self`

As already outlined, the use of `self` denotes the value of the current iteration. To make things more straightforward, the outputs below shows the rough representation when using `self` with `map`; the concept is the same when used within `dynamic_options.transform`.

Given the following schema for a `map` operation:
```json
{
    "map": [
        {
            "format-date": [
                "self",
                "%Y-%m-%d"
            ]
        },
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
                2
            ]
        }
    ]
}
```

Steps involved:
1. Resolve the `iterables`, which is the second argument to the `map` operator. In this example, the `date` operator would be resolved first, then the `date-range` operator. Once resolved, the definition under the hood would look like this:
    ```json    
    {
        "map": [
            {
                "format-datetime": [
                    "self",
                    "%Y-%m-%d"
                ]
            },
            [datetime(2021, 1, 1), datetime(2021, 1, 2)]
        ]
    }
    ```
1. Resolve the string `self` on each iteration. So the first iteration would look like this:
    ```json    
    {
        "format-datetime": [
            datetime(2021, 1, 1),
            "%Y-%m-%d"
        ]
    }
    ```
1. Once the operation is applied to each item in the list; the output should look like this:
   ```json
   ["2021-01-01", "2021-01-02"]
   ``` 


## Consequences

- Dynamic answer options can be driven by any value source or value operators that return a sequence of values.
- Consistent with new rules structure.
- Although we resolve an answer value to its label when using Checkbox answers to drive the dynamic options, support for translations are out of scope, and no guarantees are provided.
- `answer.*.options` can be optional when `dynamic_options` are defined. The necessary guards will need to be in place to ensure the answer always have a minimum of 2 options.
- Answer option action (`options.*.action`) will not be supported for dynamic options.
- Support for the nested use of dynamic options, i.e. dynamically generated options, populating other dynamic options, is out of scope.
