import re

from app import error_messages
from app.answer_type import AnswerOptionType
from app.validators.questionnaire_schema import (
    QuestionnaireSchema,
    get_object_containing_key,
)
from app.validators.validator import Validator
from app.validators.value_source_validator import ValueSourceValidator


class PlaceholderValidator(Validator):
    PLACEHOLDERS_DONT_MATCH_DEFINITIONS = "Placeholders don't match definitions."
    FIRST_TRANSFORM_CONTAINS_PREVIOUS_TRANSFORM_REF = (
        "Can't reference `previous_transform` in a first transform"
    )
    NO_PREVIOUS_TRANSFORM_REF_IN_CHAIN = (
        "`previous_transform` not referenced in chained transform"
    )

    def __init__(self, element):
        super().__init__(element)
        self.questionnaire_schema = QuestionnaireSchema(element)

    def validate(self):
        strings_with_placeholders = get_object_containing_key(
            self.schema_element, "placeholders"
        )
        for _, placeholder_object in strings_with_placeholders:
            self.validate_placeholder_object(placeholder_object)

        return self.errors

    def validate_placeholder_object(self, placeholder_object):
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
                self.validate_placeholder_transforms(transforms)

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

    def validate_placeholder_answer_id(self, argument):
        """
        Validate answer_id exists in Answer Context
        Args:
         argument: answer id
        Returns:
            True  : if exists
            False : if not exists
        """

        answers = self.questionnaire_schema.answers_with_context
        if argument not in answers:
            self.add_error(
                ValueSourceValidator.ANSWER_REFERENCE_INVALID, identifier=argument
            )
            return False
        return True

    def validate_option_label_value_placeholder(self, argument):
        """
        validate answer_id exists and answer_id for transform 'option_label_from_value' is of type of ['Checkbox','Radio','Dropdown']
        Args:
         argument: answer id argument passed to transform

        """
        answers = self.questionnaire_schema.answers_with_context
        answer_id_exists = self.validate_placeholder_answer_id(argument)

        # if answer id doesn't exist, no further validation is done
        if not answer_id_exists:
            return

        if not any(
            x.value == answers[argument]["answer"]["type"] for x in AnswerOptionType
        ):
            self.add_error(
                error_messages.ANSWER_OPTION_LABEL_VALUE_TYPE_INVALID,
                identifier=argument,
            )

    def validate_placeholder_transforms(self, transforms):
        # First transform can't reference a previous transform
        first_transform = transforms[0]
        for argument_name in first_transform.get("arguments"):
            argument = first_transform["arguments"][argument_name]
            if (
                isinstance(argument, dict)
                and argument.get("source") == "previous_transform"
            ):
                self.add_error(self.FIRST_TRANSFORM_CONTAINS_PREVIOUS_TRANSFORM_REF)
            if (
                first_transform["transform"] == "option_label_from_value"
                and argument_name == "answer_id"
            ):
                self.validate_option_label_value_placeholder(argument)

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

                if (
                    transform["transform"] == "option_label_from_value"
                    and argument_name == "answer_id"
                ):
                    self.validate_option_label_value_placeholder(argument)

            if not previous_transform_used:
                self.add_error(self.NO_PREVIOUS_TRANSFORM_REF_IN_CHAIN)
