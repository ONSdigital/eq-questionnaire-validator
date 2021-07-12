# 8. Remove final summary and confirmation blocks

## Context

Linear non-hub questionnaires must either end with a `Summary` or `Confirmation` block. This block determines what a user sees after completing and before submitting a questionnaire. As the block must be included as the last block in the questionnaire, the block is either included in:
- the last group
- an extra group added for the summary block
- an extra section (with one group) added for the summary block

This is not ideal for two reasons:
- The block is related to the whole questionnaire, not any given group or section
- Any time we condsider completeness for a given section, we need to consider if a `Summary` or `Confirmation` block exists.

The `SectionSummary` block type was [removed](https://github.com/ONSdigital/eq-questionnaire-validator/pull/29) for similar reasons. 

## Proposal

- Remove the `Summary` and `Confirmation` block types
- Introduce a new `questionnaire_flow` top-level schema object with:
  - a `type` property to differentiate between `Linear` and `Hub` questionnaires
  - an `options` object to hold options related to the given questionnaire flow:
    - For `Linear` questionnaires, an `include_summary` boolean option
    - For `Hub` questionnaires, the existing `required_completed_sections` option
- Remove the top-level `hub` property

### Examples:

Current:

```json
{
  "hub": {
    "enabled": true,
    "required_completed_sections": ["section-id"]
  }
}
```

Proposed:

```json
{
  "questionnaire_flow": {
    "type": "Linear",
    "options": {
      "include_summary": true
    }
  }
}
```

```json
{
  "questionnaire_flow": {
    "type": "Hub",
    "options": {
      "required_completed_sections": ["section-id"]
    }
  }
}
```

## Consequences

- The type of questionnaire (linear or hub) will be clearer
- Final summaries will be consistent with section summaries
- Calculation of completeness will be simpler