# 7. Custom page titles

## Context

Page titles are currently defined in question or content blocks. There is a requirement to override the default page title with a custom title. The format of the custom title will always be one of the following:

1. String with no interpolation: `"This is a page title"`
1. String with a list item index: `"Person {index}"`
1. String with multiple list item indices: `"Person {index} and person {index}"`

This could be achieved with the introduction of a new transform object, one that takes a list item id and returns it's index position in a list; this approach would require significant changes to almost all Census schema block definitions. Instead, we can rely on Python's string formatting to render the index value for the list item id.

## Proposal

We will add an optional `title` property to block definitions. This property, when provided, will override any question or content page title definitions for that block. If it is ommitted, the page title will still be determined from a question or content definition depending on the block type.

Python's [string formatting](https://docs.python.org/3/library/string.html#string.Formatter.format) will be used to resolve any formatting parameters. The only formatting parameters that will be resolved are `list_item_index` and `to_list_item_index`. Note that the `to_list_item_index` will only be available for Relationship block types. If either `list_item_index` (or `to_list_item_index` where applicable) cannot be resolved, the question or content title will be used.

### Example:

```json
{
  "blocks": [
    {
      "type": "Question",
      "id": "",
      "title": "Question or Content block: Person {list_item_index}"
    }
  ]
}
```

```json
{
  "blocks": [
    {
      "type": "Question",
      "id": "",
      "title": "Relationship block: Person {list_item_index} and Person {to_list_item_index}"
    }
  ]
}
```

## Consequences

- Page title rendering will be implicit in the schema.
- There will be two methods for rendering strings, placeholder definitions and implicit string formatting (though this is already the case due to min and max definitions).
