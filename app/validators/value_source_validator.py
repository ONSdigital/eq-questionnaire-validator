from app.validators.validator import Validator


class ValueSourceValidator(Validator):
    COMPOSITE_ANSWER_INVALID = "Invalid composite answer"
    COMPOSITE_ANSWER_FIELD_INVALID = "Invalid field for composite answer"
    SOURCE_REFERENCE_INVALID = "Invalid {} source reference"
    ANSWER_SOURCE_REFERENCE_INVALID = SOURCE_REFERENCE_INVALID.format("answers")

    COMPOSITE_ANSWERS_TO_SELECTORS_MAP = {
        "Address": ["line1", "line2", "town", "postcode"]
    }
    RESPONSE_METADATA_IDENTIFIERS = ["started_at"]

    def __init__(self, value_source, json_path, questionnaire_schema):
        super().__init__(value_source)
        self.value_source = value_source
        self.questionnaire_schema = questionnaire_schema
        self.context["json_path"] = json_path

        self._valid_source_identifiers_map = {
            "answers": self.questionnaire_schema.answers_with_context,
            "metadata": self.questionnaire_schema.metadata_ids,
            "response_metadata": self.RESPONSE_METADATA_IDENTIFIERS,
            "list": self.questionnaire_schema.list_names,
            "calculated_summary": self.questionnaire_schema.calculated_summary_block_ids,
        }

    def validate(self):
        self.validate_source_reference()
        return self.errors

    def validate_source_reference(self):
        source = self.value_source["source"]
        identifiers = self.value_source["identifier"]
        if isinstance(identifiers, str):
            identifiers = [identifiers]

        self._validate_source_reference(identifiers, source)

    def _validate_source_reference(self, identifiers, source):
        valid_identifiers = self._valid_source_identifiers_map.get(source)
        if not valid_identifiers:
            return None

        for identifier in identifiers:
            self._validate_source_identifier(
                source, identifier=identifier, valid_identifiers=valid_identifiers
            )

    def _validate_source_identifier(self, source, *, identifier, valid_identifiers):
        if identifier not in valid_identifiers:
            self.add_error(
                self.SOURCE_REFERENCE_INVALID.format(source),
                identifier=identifier,
            )

        elif source == "answers" and (selector := self.value_source.get("selector")):
            self._validate_answer_source_selector_reference(identifier, selector)

    def _validate_answer_source_selector_reference(self, identifier, selector):
        answers_with_context = self.questionnaire_schema.answers_with_context
        answer_type = answers_with_context[identifier]["answer"]["type"]

        if answer_type not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP:
            self.add_error(self.COMPOSITE_ANSWER_INVALID, identifier=identifier)

        elif selector not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP[answer_type]:
            self.add_error(self.COMPOSITE_ANSWER_FIELD_INVALID, identifier=identifier)
