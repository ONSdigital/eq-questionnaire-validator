from app.validators.placeholders.placeholder_validator import PlaceholderValidator
from app.validators.questionnaire_schema import get_object_containing_key


class BlockPlaceholderValidator(PlaceholderValidator):
    def validate(self):
        strings_with_placeholders = get_object_containing_key(
            self.schema_element, "placeholders"
        )
        for placeholder_object in strings_with_placeholders:
            self.validate_placeholder_object(
                placeholder_object, self.schema_element["id"]
            )

        return self.errors
