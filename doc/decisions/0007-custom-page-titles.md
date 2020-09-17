# 7. Custom page titles

## Context

Page titles are currently defined in question or content block using the block title property. There is a requirement to override the default page title with a custom title. The format of the custom page title will always be one of the following:

1. String with no interpolation: `"This is a page title"`
1. String with a list item index: `"Person {index}"`
1. String with multiple list item indices: `"Person {index} and person {index}"` (RelationshipCollector blocks only)

This could be achieved with the introduction of a new transform object, one that takes a list item id and returns it's index position in a list; this approach would require significant changes to almost all Census schema block definitions. Instead, we can rely on Python's string formatting to render the index value for the list item ids.

## Proposal

We will add an optional `page_title` property to page definitions (both block and non-block pages). This property, when provided, will override any question or content page title definitions for that page. If it is ommitted, the page title will still be determined from a question or content definition depending on the definition type. For ListCollectorAction blocks, the `page_title` property can also be defined on the ListCollectorAction

Python's string formatting will be used to resolve the `list_item_index` and `to_list_item_index` parameters. Note that the `to_list_item_index` will only be available for Relationship block types. If either `list_item_index` (or `to_list_item_index` where applicable) cannot be resolved, the question or content title will be used.

### Examples:

```json
{
  "blocks": [
    {
      "type": "Question",
      "id": "",
      "page_title": "Question or Content block: Person {list_item_index}"
    }
  ]
}
```

```json
{
  "blocks": {
    "type": "RelationshipCollector",
    "id": "relationships",
    "page_title": "How Person {list_item_index} is related to Person {to_list_item_index}",
    "for_list": "household"
  }
}
```

```json
{
  "content": {
    "title": "Content"
  },
  "page_title": "Question or Content block: Person {list_item_index}"
}
```

```json
{
  "sections": [
    {
      "id": "section",
      "title": "Household",
      "summary": {
        "page_title": "Custom section summary page title"
      }
    }
  ]
}
```

```json
{
  "add_block": {
    "id": "add-person",
    "type": "ListAddQuestion",
    "page_title": "Custom page title"
  }
}
```

## Consequences

- Page title rendering will be implicit in the schema.
- There will be two methods for rendering strings, placeholder definitions and implicit string formatting (though this is already the case due to min and max definitions).
