# 12. Dynamically creating answers based on a list

## Context

We need the ability to dynamically generate answers based on a list item.

We need to support dynamic answers that are driven by:

- List collectors
- Arbitrary functions that return a sequence of values
- Checkbox answers

Additional requirements:

- Dynamic answers need to be identifiable for downstream processing
- Dynamic answers need to be able to support user defined answer codes

## Proposal

Introduce a new `dynamic_answers` object that will handle the generation of any repeating answers based on a list of items.

## Properties and uses:

### `dynamic_answers`

- A new property within the `question` block that supports answers based on a list of items, answers, or arbitrary functions 
  that return a sequence of values.
- `dynamic_answers` will contain two top level properties, `values` and `answers`.
- `dynamic_answers` can be used alongside the existing static `answers` property, allowing for static and dynamic answers 
  on the same page.
- `dynamic_answers` must have at least one answer block but can contain multiple `answers` to be iterated over for each literal list item.
- `dynamic_answers` will be limited to a single block i.e. they will only be displayed on one page.

#### `dynamic_answers.values`

- This field will contain the `source` for the list of literal values to be repeated over.
- The `values` property will follow existing patterns and allow either a `Value Source` or a `Value Operator` as per the schema examples below.
- There must be at least one item in the list being used to generate dynamic answers unless static answers are provided.

#### `dynamic_answers.answers`
- This property allows a list of answer blocks, as there can be more than one dynamic answer for each literal list item.
- The `answers` property should be able to support any of the properties that would be supported in a normal/static `answer` block.
- All the properties within the `dynamic_answers.answers` block that can contain text displayed to the user will need to support placeholder transforms. For example, answer labels which currently do not allow placeholders will need to be extended to support this.
- `dynamic_options` cannot be used inside `dynamic_answers`.
- The structure should be consistent with a regular static answer block.
- For `dynamic_answers.answers` blocks, the answer `id` will simply be a prefix, and a unique identifier will need to be added to the prefix at runtime. This is required in order for us to be able to render the id in other parts of the questionnaire. This id made of the prefix and unique identifier will only be used for front end rendering purposes. We will still use just the `list_item_id` for storage even if it isn't a list collector.

### Dynamic answers based on a list source

```json
{
  "question": {
    "id": "percentage-of-research",
    "title": "Some title",
    "type": "Question",
    "answers": [...],
    "dynamic_answers": {
      "values": {
        "source": "list",
        "identifier": "postcodes",
        "selector": "items"
      },
      "answers": [
        {
          "description": {
            "text": "Percentage of shopping at {transformed_value}",
            "placeholders": [
              {
                "placeholder": "transformed_value",
                "value": {
                  "source": "answers",
                  "identifier": "postcode"
                }
              }
            ]
          },
          "id": "percentage-of-shopping",
          "mandatory": false,
          "type": "Percentage",
          "maximum": {
            "value": 100
          },
          "decimal_places": 2
        }
      ]
    }
  }
}
```
- For dynamic answers driven by list collectors, for front end purposes each list item, at runtime the `list-item-id` will be appended to the `id` used in the `dynamic_answers.answer` block, so that all answers have unique ids e.g. `"id": "percentage-of-shopping-{list_item_id}`. For storage we will just use the combination of `answer_id` and `list_item_id`.
- Answer sources within a loop must be resolved using the `list_item_id` to resolve the current iterations value.

### Dynamic answers based on a list of answers

```json
{
  "question": {
    "id": "percentage-of-research",
    "title": "Some title",
    "type": "Question",
    "answers": [...],
    "dynamic_answers": {
      "values": {
        "source": "answers",
        "identifier": "checkbox-answer"
      },
      "answers": [
        {
          "description": {
            "text": "Percentage of shopping at {transformed_value}",
            "placeholders": [
              {
                "placeholder": "transformed_value",
                "transforms": [
                  {
                    "transform": "option_label_from_value",
                    "arguments": {
                      "value": "self",
                      "answer_id": "checkbox-answer"
                    }
                  }
                ]
              }
            ]
          },
          "id": "percentage-of-shopping",
          "mandatory": false,
          "type": "Percentage",
          "maximum": {
            "value": 100
          },
          "decimal_places": 2
        }
      ]
    }
  }
}
```

- `list_item_id` can now be an answer value or the output of a function, not just list collector ids. To make sure it is a valid id for storage we will replace any spaces with hyphens.
- Dynamic answers can only be generated if there is at least one value.
- In order to support examples like the schema above, Placeholders will need to be extended to support the new value `self`, which will allow the placeholder resolve the answer value for the current literal list item being processed. This is similar to the concept [`self` added in order to support
dynamic answer options](https://github.com/ONSdigital/eq-questionnaire-validator/blob/master/doc/decisions/0010-dynamic-answer-options.md#resolving-the-value-for-self). This is required so that we can pipe the value of the literal item being processed into any user displayed text field.

#### Dynamic Answers based on an arbitrary function

```json
{
  "question": {
    "id": "percentage-of-research",
    "title": "Some title",
    "type": "Question",
    "answers": [...],
    "dynamic_answers": {
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
      "answers": [
        {
          "description": {
            "text": "Percentage of shopping on {date}",
            "placeholders": [
              {
                "placeholder": "date",
                "transforms": [
                  {
                    "transform": "format_date",
                    "format-date": [
                      "self",
                      "%A %d %B %Y",
                      "%Y-%m-%d"
                    ]
                  }
                ]
              }
            ]
          },
          "id": "percentage-of-shopping",
          "mandatory": false,
          "type": "Percentage",
          "maximum": {
            "value": 100
          },
          "decimal_places": 2
        }
      ]
    }
  }
}
```

- The example above shows a dynamic answer that is based on a list of dates generated by a function, this extends the usage of the [map operator 
that was implemented in order to support dynamic answer options](https://github.com/ONSdigital/eq-questionnaire-validator/blob/master/doc/decisions/0010-dynamic-answer-options.md#resolving-the-value-for-self).
- Similarly to the example based on an answer value source, a unique identifier such as the answer value for the item being processed would need to be appended to the answer `id` prefix at runtime in order to generate a unique answer `id`.

## Downstream Processing

We need to be able to identify which dynamic answers have been answered when sending the payload downstream to SDC. 

For Dynamic Answers driven by list collector sources, we would need to include the `list_item_id` for the answered item. As a result, the answer payload sent downstream would only contain the prefixed `answer_id` and not the one that is dynamically generated at run time with the appended `list_item_id` outlined above e.g.
```json
{
  "answer_id": "percentage-of-shopping",
  "value": 70,
  "list_item_id": "afghjf"
},
{
  "answer_id": "percentage-of-shopping",
  "value": 30,
  "list_item_id": "fdhjfl"
}

For other sources, we would set the `list_item_id` and use it the same way it is used for list collector sources but instead of it being set to an automatically generated value we would set it to to the option value with any spaces replaced with hyphens as per the checkbox example below:
```json
{
  "answer_id": "percentage-of-shopping",
  "value": 20,
  "list_item_id": "Tesco"
},
{
  "answer_id": "percentage-of-shopping",
  "value": 50,
  "list_item_id": "Asda"
},
{
  "answer_id": "percentage-of-shopping",
  "value": 30,
  "list_item_id": "Aldi"
}
```

This is something we will need to discuss with downstream teams as they will need to know we are using it in this way. We will also need to discuss it with Author because they will need to know that they need to be set but must be unique within the `dynamic_answers` object. These will be then concatenated with the `answer_id` and any spaces will be replaced with dashes in order to be valid ids when set in the HTML.

## Answer Codes

As answer ids used for dynamic answers will only be prefixed values in the schema, only one answer code would be able to be set against each dynamic answer (using the id prefix) e.g.
```json
{
  "answer-id": "some-id-prefix",
  "code": 1
}
```

## Consequences

- Dynamic answer options can be driven by a list sources, answer sources or functions.
- All the new properties make use of or extend existing patterns.
- Consistent with existing answer structure.
- Extends the use of `self` and `map` that were introduced in order to support dynamic answer options.
- Should be extensible for future features new types of list sources i.e. prepop.
