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

    def validate_placeholder_answer_id(self, answer_id):
        """
        Validate answer_id exists in Answer Context
        Args:
          answer_id: Answer id of placeholder
        Returns:
            True  : if exists
            False : if not exists
        """

        answers = self.questionnaire_schema.answers_with_context
        if answer_id not in answers:
            self.add_error(
                ValueSourceValidator.ANSWER_SOURCE_REFERENCE_INVALID,
                identifier=answer_id,
            )
            return False
        return True

    def validate_option_label_from_value_placeholder(self, answer_id):
        """
        validate answer_id exists and answer_id for option label from value is of type ['Radio','Checkbox','Dropdown']
        Args:
         answer_id: answer_id passed to transform

        """
        answers = self.questionnaire_schema.answers_with_context
        answer_id_exists = self.validate_placeholder_answer_id(answer_id)

        # if answer id doesn't exist, no further validation is done
        if not answer_id_exists:
            return None

        if not any(
            x.value == answers[answer_id]["answer"]["type"] for x in AnswerOptionType
        ):
            self.add_error(
                error_messages.ANSWER_TYPE_FOR_OPTION_LABEL_FROM_VALUE_INVALID,
                identifier=answer_id,
            )

    def validate_answer_type_for_transform(
        self, argument, argument_name, transform_type
    ):
        if not (
            transform_type in ["format_unit", "format_percentage"]
            and argument_name == "value"
            and argument.get("value", {}).get("source") == "answers"
        ):
            return None

        answer_id = argument["value"]["identifier"]
        answer_type = self.questionnaire_schema.answers_with_context[answer_id][
            "answer"
        ]["type"]

        if answer_type.lower() in transform_type:
            return None

        expected_type = transform_type.split("_")[1].title()
        self.add_error(
            error_messages.ANSWER_TYPE_FOR_TRANSFORM_TYPE_INVALID.format(
                transform=transform_type,
                expected_type=expected_type,
                answer_type=answer_type,
            ),
            identifier=answer_id,
        )

    def validate_answer_and_transform_unit_match(self, *, arguments, transform_type):
        if transform_type != "format_unit":
            return None

        value = arguments["value"]
        answer_id = value.get("identifier")
        unit = arguments["unit"]

        if self.errors or (
            unit
            == self.questionnaire_schema.answers_with_context[answer_id]["answer"][
                "unit"
            ]
        ):
            return None

        self.add_error(
            error_messages.ANSWER_UNIT_AND_TRANSFORM_UNIT_MISMATCH.format(
                answer_unit=self.questionnaire_schema.answers_with_context[answer_id][
                    "answer"
                ]["unit"],
                transform_unit=unit,
            ),
            identifier=answer_id,
        )

    def _validate_placeholder_previous_transforms(self, transforms):
        # First transform can't reference a previous transform
        first_transform = transforms[0]
        for argument_name in first_transform.get("arguments"):
            argument = first_transform["arguments"][argument_name]
            if (
                isinstance(argument, dict)
                and argument.get("source") == "previous_transform"
            ):
                self.add_error(self.FIRST_TRANSFORM_CONTAINS_PREVIOUS_TRANSFORM_REF)

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
                self.add_error(self.NO_PREVIOUS_TRANSFORM_REF_IN_CHAIN)

    def validate_placeholder_transforms(self, transforms):
        self._validate_placeholder_previous_transforms(transforms)

        for transform in transforms:
            for argument_name in transform.get("arguments"):
                argument = transform["arguments"][argument_name]
                if (
                    transform["transform"] == "option_label_from_value"
                    and argument_name == "answer_id"
                ):
                    self.validate_option_label_from_value_placeholder(argument)

                self.validate_answer_type_for_transform(
                    transform.get("arguments"), argument_name, transform["transform"]
                )

            self.validate_answer_and_transform_unit_match(
                arguments=transform.get("arguments"),
                transform_type=transform["transform"],
            )
