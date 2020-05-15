from app.validators.placeholders.placeholder_validator import PlaceholderValidator


class BlockPlaceholderValidator(PlaceholderValidator):
    def validate(self):
        strings_with_placeholders = self.questionnaire_schema.get_block_key_context(
            self.schema_element["id"], "placeholders"
        )
        for placeholder_object in strings_with_placeholders:
            self.validate_placeholder_object(
                placeholder_object, self.schema_element["id"]
            )
