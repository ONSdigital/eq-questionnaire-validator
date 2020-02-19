# 6. Custom section summaries

## Context

Section summaries don't provide a way to define what should be summarised. To summarise a section that contains list collectors, we use information from the first list collector for each list. This forces section summary properties into the first list collector (`add_link_text`, `empty_list_text`) and causes un-necessary complexity when a section summary needs to be rendered.

## Proposal

We will add an optional `summary` property to sections. This property, when provided, will provide properties defining what to summarise and will override the default i.e. summarisation of all questions.

```json
{ 
    "sections": [
        {
            "id": "",
            "summary": [
                {
                    "type": "List",
                    "for_list": "<list_name>",
                    "title": "",
                    "add_link_text": "",
                    "empty_list_text": "",
                    "item_title": {}
                }
            ]
        }
    ]
}
```

- `item_title` is a string with placeholders and will work the same as the equivalent list collector property. Duplicating the property in the summary allows for a different representation and will simplify implementations (by not having to search for a definition)
- The initial implementation will only support a `List` type, but this can be extended in the future for other summary types

### Example

```json
{ 
    "sections": [
        {
            "id": "household-section",
            "summary": [
                {
                    "type": "List",
                    "for_list": "householders",
                    "title": "Householders",
                    "add_link_text": "Add a person",
                    "empty_list_text": "No householders",
                    "item_title": {}
                },
                {
                    "type": "List",
                    "for_list": "visitors",
                    "title": "Visitors",
                    "add_link_text": "Add a visitor",
                    "empty_list_text": "No visitors",
                    "item_title": {}
                }
            ]
        }
    ]
}
```

## Consequences

- Section summaries for lists are explicit rather than implicit; services that interperet the schema will be simpler. 
- Properties related to summaries are not present on non-summary blocks.
- The `ListCollectorSummary` block can be removed as it's no longer needed.
- Other custom summary types are possible.
