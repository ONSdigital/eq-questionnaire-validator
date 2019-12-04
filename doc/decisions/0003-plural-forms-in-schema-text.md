# 3. Plural forms in schema text

## Context

We need to be able to support:
- variations of text based on the number of items in a list
- word forms of numbers 1 to 9

For example:

```
Yes, one person lives here
Yes, two people live here
Yes, three people live here
Yes, ... people live here
Yes, 10 people live here
Yes, 11 people live here
Yes, .. people live here
```

## Proposal

- Use a placeholder transform to transform a number into words.
- New `text_plural` element to support the plural forms of the text.
- Use the CLDR plural categories to define the plural forms (http://www.unicode.org/reports/tr35/tr35-33/tr35-numbers.html#Language_Plural_Rules):
  - zero
  - one
  - two
  - few
  - many
  - other
- Choose the plural form based on a numeric answer, metadata or number of items in a list.

Example schema:

```json
{
    "summary_text": {
        "placeholders": [
            {
                "placeholder": "number_of_people",
                "transforms": [
                    {
                        "arguments": {
                            "number": {
                                "source": "list",
                                "identifier": "household"
                            }
                        },
                        "transform": "number_to_words"
                    }
                ]
            }
        ],
        "text_plural": {
            "forms": {
                "one": "Yes, {number_of_people} person lives here",
                "other": "Yes, {number_of_people} people live here"
            },
            "count": {
                "source": "list",
                "identifier": "household"
            }
        }
    }
}
```

Translated schemas can contain more forms than an English source schema, for example:

```json
{
    "text_plural": {
        "forms": {
            "zero": "Ydy, nid oes unrhyw bobl yn byw yma",
            "one": "Ydy, mae {number_of_people} person yn byw yma",
            "two": "Ydy, mae {number_of_people} berson yn byw yma",
            "few": "Ydy, mae {number_of_people} o bobl yn byw yma",
            "many": "Ydy, mae {number_of_people} o bobl yn byw yma",
            "other": "Ydy, mae {number_of_people} o bobl yn byw yma"
        }
    }
}
```

Additional placeholders can also be defined:

```json
{
    "summary_text": {
        "placeholders": [
            {
                "placeholder": "number_of_people",
                "transforms": [
                    {
                        "arguments": {
                            "number": {
                                "source": "list",
                                "identifier": "household"
                            }
                        },
                        "transform": "number_to_words"
                    }
                ]
            },
            {
                "placeholder": "address",
                "value": {
                    "source": "metadata",
                    "identifier": "display_address"
                }
            }
        ],
        "text_plural": {
            "forms": {
                "one": "Yes, {number_of_people} person live at {address}",
                "other": "Yes, {number_of_people} people live at {address}"
            },
            "count": {
                "source": "list",
                "identifier": "household"
            }
        }
    }
}
```

### Mapping the count to the CLDR plural forms

We will use the gettext plural forms mapping. For example, the Welsh gettext plural forms are:

```
"Plural-Forms: nplurals=6; plural=(n == 0) ? 0 : ((n == 1) ? 1 : ((n == 2) ? 2 : ((n == 3) ? 3 : ((n == 6) ? 4 : 5))));\n"
```

Which would map to:

```
zero - msgstr[0]
one - msgstr[1]
two - msgstr[2]
few - msgstr[3]
many - msgstr[4]
other - msgstr[5]
```

## Consequences

- Plural forms can be used in schema text.
- Translators need to be aware of how to populate the plural forms in the translation tool.
- Need to review the rule that enforces answer labels and values are the same.

## Useful references

- http://babel.pocoo.org/en/latest/api/plural.html
- http://cldr.unicode.org/index/cldr-spec/plural-rules#TOC-Determining-Plural-Categories
- http://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html#cy
- https://www.omniglot.com/language/numbers/welsh.htm