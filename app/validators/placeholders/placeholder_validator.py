import re

from app import error_messages
from app.validators.validator import Validator


class PlaceholderValidator(Validator):
    PLACEHOLDERS_DONT_MATCH_DEFINITIONS = "Placeholders don't match definitions."
    FIRST_TRANSFORM_CONTAINS_PREVIOUS_TRANSFORM_REF = (
        "Can't reference `previous_transform` in a first transform"
    )
    NO_PREVIOUS_TRANSFORM_REF_IN_CHAIN = (
        "`previous_transform` not referenced in chained transform"
    )

    def __init__(self, element, questionnaire_schema):
        super().__init__(element)
        self.questionnaire_schema = questionnaire_schema

    def validate_placeholder_object(self, placeholder_object, current_block_id):
        """ Current block id may be None if called outside of a block
        """
        placeholders_in_string = set()
        placeholder_regex = re.compile("{(.*?)}")

        if "text" in placeholder_object:
            placeholders_in_string.update(
                placeholder_regex.findall(placeholder_object.get("text"))
            )
        elif "text_plural" in placeholder_object:
            for text in placeholder_object["text_plural"]["forms"].values():
                placeholders_in_string.update(placeholder_regex.findall(text))

        placeholder_definition_names = set()

        for placeholder_definition in placeholder_object.get("placeholders"):
            placeholder_definition_names.add(placeholder_definition["placeholder"])

            transforms = placeholder_definition.get("transforms")
            if transforms:
                self.validate_placeholder_transforms(transforms, current_block_id)

        placeholder_differences = placeholders_in_string - placeholder_definition_names

        if placeholder_differences:
            try:
                text = placeholder_object["text"]
            except KeyError:
                text = placeholder_object["text_plural"]["forms"]["other"]

            self.add_error(
                self.PLACEHOLDERS_DONT_MATCH_DEFINITIONS,
                text=text,
                differences=placeholder_differences,
            )

    def validate_placeholder_transforms(self, transforms, block_id):
        # First transform can't reference a previous transform
        first_transform = transforms[0]
        for argument_name in first_transform.get("arguments"):
            argument = first_transform["arguments"][argument_name]
            if (
                isinstance(argument, dict)
                and argument.get("source") == "previous_transform"
            ):
                self.add_error(
                    self.FIRST_TRANSFORM_CONTAINS_PREVIOUS_TRANSFORM_REF,
                    block_id=block_id,
                )

        # Previous transform must be referenced in all subsequent transforms
        for transform in transforms[1:]:
            previous_transform_used = False
            for argument_name in transform.get("arguments"):
                argument = transform["arguments"][argument_name]
                if (
                    isinstance(argument, dict)
                    and argument.get("source") == "previous_transform"
                ):
                    previous_transform_used = True

            if not previous_transform_used:
                self.add_error(
                    self.NO_PREVIOUS_TRANSFORM_REF_IN_CHAIN, block_id=block_id
                )
