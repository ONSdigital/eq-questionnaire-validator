# 11. User-defined Answer Codes

## Context

We need to allow users to define their own set of uniquely identifiable codes for answers that can be used in downstream processing.
Although `q_code` partially supports this, it is misnamed and is not extensible to data version 0.0.3, which supports more complex features such as repeating answers.

**Requirements for answer codes:**

1. Need to identify an answer uniquely
2. For answers with options (Radio/Dropdown/Relationship/Checkbox), it needs to identify the answer and the selected value.

## Proposal

Introduce a new optional `answer_codes` top-level property to the schema JSON, which maps the answers to a user-defined code.

  - `answer_codes` is an array of objects representing the answer ID and, optionally, the answer value to a user-defined code relationship.
  - Top-level to prevent duplicate mappings, as answers can be duplicated in variants. Additionally, it avoids the need for Runner to map it when Author needs to anyway.
  - This mapping will be filtered to cover only the relevant answers for the submission and then sent in the downstream payload.
  - For answers with options, an optional `answer_value` must be provided to allow mapping to a single option value. The validation that enforces the label must match the value will be removed to prevent downstream mappings from changing when the label changes.
  - If `answer_codes` are defined, then there must be a code for every answer.

**Example:**

```js
  ...
  "answer_codes": [
    {
      "answer_id": "textfield-answer",
      "code": "1"
    },
    {
      "answer_id": "number-answer",
      "code": "2"
    },
    {
      "answer_id": "radio-dropdown-checkbox-relationship-answer",
      "code": "3" // This should only exist and be used for dynamic answers or when codes for each option aren't given.
    },
    {
      "answer_id": "radio-dropdown-checkbox-relationship-answer",
      "answer_value": "RAD1",  // This is the value of the Dropdown/Radio/Checkbox/Relationship, not the label.
      "code": "3a"
    },
    {
      "answer_id": "radio-dropdown-checkbox-relationship-answer",
      "answer_value": "RAD2",  // This is the value of the Dropdown/Radio/Checkbox/Relationship, not the label.
      "code": "3b"
    }
  ],
  ...
```

### Answer Options with User Defined Codes

- Answer options are supported by Checkbox, Radio, Dropdown, and Relationship answer types.
- When a user-defined code is assigned to each answer option, the downstream payload will expose both the `answer_id` and the `answer_value` for a given code.
- The user-defined code is not defined as the `option. value` because:
    - We need to allow the label's value to have a different meaning to the user-defined code. For example, when talking about Standard industrial classification of economic activities (SIC) codes, the label might be `Growing of rice`, and the value might be the literal `SIC` code, i.e. `01120`. However, the user-defined code might mean something else entirely, i.e. get `1` to mean it was the first in the list. We should keep the two meanings separate.
    - Not all surveys need a mapping to the individual options.
    - It makes option answers mapping inconsistent with other answers.
    - We need to support dynamic answer options, which are only available at runtime.

Example option answer with a user-defined code:

```js
{
  "answer_id": "option-answer", 
  "answer_value": "Value 1",
  "code": "8a"
}
```

This means the user-defined code for answer id `option-answer` with a value of `Value 1` is `8a`.

#### Dynamic Option Values / Single Code for All Options

- It is possible to have dynamic Checkbox options at run time. All dynamic options for a given answer ID will be represented against a single user-defined code.
- If each option does not need its own code, then the code can be defined at the answer level instead of the option level.

```js
{
  "answer_id": "option-answer",
  "code": "8"
}
```

This means one of two things:
1. the user-defined code suffix/prefix for any generated dynamic option with the id `option-answer` is `8`.
2. the user-defined code suffix/prefix for all answer options with the id `option-answer` is `8`.

The user-defined code for an answer that supports `options` must be against the following:
- the entire answer (1 for all options)
- each answer option level (1 for each option)
- the entire option and answer level if dynamic options are involved. (1 for each static one, and 1 prefix/suffix for the dynamic option)

##### Radio Example (Answer level code)

This mapping implies that regardless of the value selected by the respondent, the user-defined code for the answer `radio-answer` will be `1`.

```js
{
  "answer_id": "radio-answer",
  "code": "1"
}
```

##### Radio Example (Option level codes)

This mapping implies that option value `2022-01-01` has a code for `1a` whereas `2022-02-01` will be mapped using the code `1b`.

```js
{
  "answer_id": "radio-answer",
  "answer_value": "2022-01-01",
  "code": "1a"
},
{
  "answer_id": "radio-answer",
  "answer_value": "2022-02-01",
  "code": "1b"
}
```

##### Radio with Dynamic Options Example (Answer + Option level codes)

This mapping implies:
- The option value `None` has a code of `1a`
- Any dynamically generated answers will have a code of `1`. Downstream will use this as a suffix/prefix, as you may have various dynamic answers.

_**JSON Schema:**_

```js
{
  "id": "radio-answer",
  "mandatory": false,
  "type": "Radio",
  "dynamic_options": {
    "values": {...}
  },
  "transform": {...}
  },
  "options": [
    {
      "label": "None of the above",
      "value": "None"
    }
  ]
}
```

_**Answer codes:**_

```js
{
  "answer_id": "radio-answer",
  "code": "1"  // Used for any dynamic options
},
{
  "answer_id": "radio-answer",
  "answer_value": "None",
  "code": "1a"
}
```

## Consequences

- User-defined codes can be supplied for data version 0.0.3.
- In addition to Checkbox answers, Radio, Dropdown & Relationship answers can now specify a code for each option.
- Allows downstream to identify answers even with repeating functionality.
- Support defining a suffix/prefix code for dynamic answer options. In the future, this will also support dynamic answers.
