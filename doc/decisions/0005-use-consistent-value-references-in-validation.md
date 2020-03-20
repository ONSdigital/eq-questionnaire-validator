# 5. Use consistent value references in validation

## Context

We reference dynamic values (metadata, answers) in placeholders, validation, and routing. The agreed structure for referencing dynamic values is:

```json
{
    "source": "",
    "identifier": ""
}
```

This structure is used by placeholders and is part of the agreed [changes to routing](https://github.com/ONSdigital/eq-schema-validator/blob/v3/doc/decisions/0004-extend-and-improve-routing-rules.md). Validation is inconsistent with these.

## Proposal

Update validation so that it uses the same consistent way of referencing dynamic values as placeholders and routing. This will be changed for minimum and maximum validation on numbers and dates (all current validation we support). 

### Numbers 

Current:

- Validation properties: `min_value`, `max_value`
- Value reference properties: `answer_id` 
- Also `exclusive` property

```json
{
    "max_value": {
        "answer_id": "set-maximum",
        "exclusive": true
    }
}
```

Proposed:

- Validation properties: `minimum` and `maximum` (consistent with date answers)
- Value reference replaced with source and identifier

```json
{
    "maximum": {
        "value": {
            "source": "answers",
            "identifier": "set-maximum"
        },
        "exclusive": true
    }
}
```

### Dates

Current:

- Validation properties: `minimum` and `maximum` 
- Value references properties: `answer_id` and `meta`
- Also `offset_by` property

```json
{
    "maximum": {
        "meta": "ref_p_end_date",
        "offset_by": {
            "days": 20
        }
    }
}
```

Proposed:

- Value reference replaced with source and identifier

```json
{
    "maximum": {
        "value": {
            "source": "metadata",
            "identifier": "ref_p_end_date"
        },
        "offset_by": {
            "days": 20
        }
    }
}
```

## Consequences

- We will be more consistent in how we reference dynamic values. This will simplify the development of services that are consumers of the schema (runner, author).
- All dynamic values will be available to all validations e.g. the number of items in a list.
