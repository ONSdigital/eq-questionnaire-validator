# 9. Telephone and email placeholder transforms

## Context

When rendering telephone numbers and email addresses, we need to be able to wrap them with specific markup. This markup should not be included in schema text as it:
- binds the schema to the output format 
- creates translation issues

## Proposal

Introduce two new placeholder transforms that abstract the markup from the text.  

### Telephone number link transform

The `telephone_number_link` transform will allow runner to wrap the number with a `tel` href.

```json
{
  "text": "Ring us on {telephone_number}",
  "placeholders": [
    {
      "placeholder": "telephone_number",
      "transforms": [
        {
          "transform": "telephone_number_link",
          "arguments": {
            "telephone_number": "0300 1234 931"
          }
        }
      ]
    }
  ]
}
```

### Email link transform

The `email_link` transform will allow runner to wrap the email address with a `mailto` href and a customisable email subject. 

The `email_subject` and `email_subject_append` variables are optional, if provided they will be used to set the email subject line.

```json
{
  "text": "Email us at {email_address}",
  "placeholders": [
    {
      "placeholder": "email_address",
      "transforms": [
        {
          "transform": "email_link",
          "arguments": {
            "email_address": "surveys@ons.gov.uk",
            "email_subject": "Change of details reference ",
            "email_subject_append": {
              "identifier": "ru_ref",
              "source": "metadata"
            }
          }
        }
      ]
    }
  ]
}
```

We should use `placeholders` for the email subject, but recursive placeholders are not currently supported.

## Consequences

- We can have telephone numbers and email addresses in schema text that render as links
- No additional markup is used in schema text
- We are using string concatenation for something that should be done with placeholders. We should revisit our placeholders implementation to allow recursive placeholders
- The transforms are specific to telephone number and email address links. We should explore a more generic `format_link` transform