from app.validators.validator import Validator


class ValueSourceValidator(Validator):
    ANSWER_REFERENCE_INVALID = "Invalid answer reference"
    COMPOSITE_ANSWER_INVALID = "Invalid composite answer"
    COMPOSITE_ANSWER_FIELD_INVALID = "Invalid field for composite answer"
    LIST_REFERENCE_INVALID = "Invalid list reference"
    METADATA_REFERENCE_INVALID = "Invalid metadata reference"
    RESPONSE_METADATA_REFERENCE_INVALID = "Invalid response metadata reference"

    COMPOSITE_ANSWERS_TO_SELECTORS_MAP = {
        "Address": ["line1", "line2", "town", "postcode"]
    }

    def __init__(self, value_source, json_path, questionnaire_schema):
        super().__init__(value_source)
        self.value_source = value_source
        self.questionnaire_schema = questionnaire_schema
        self.context["json_path"] = json_path

    def validate(self):
        self.validate_source_reference()
        return self.errors

    def validate_source_reference(self):
        source = self.value_source["source"]
        if isinstance(self.value_source["identifier"], str):
            identifiers = [self.value_source["identifier"]]
        else:
            identifiers = self.value_source["identifier"]

        if source == "answers":
            selector = self.value_source.get("selector")
            self._validate_answer_source_reference(identifiers, selector)

        elif source == "metadata":
            self._validate_metadata_source_reference(identifiers)

        elif source == "list":
            self._validate_list_source_reference(identifiers)

        elif source == "response_metadata":
            self._validate_response_metadata_source_reference(identifiers)

    def _validate_metadata_source_reference(self, identifiers):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.metadata_ids:
                self.add_error(self.METADATA_REFERENCE_INVALID, identifier=identifier)

    def _validate_list_source_reference(self, identifiers):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.list_names:
                self.add_error(self.LIST_REFERENCE_INVALID, identifier=identifier)

    def _validate_response_metadata_source_reference(self, identifiers):
        for identifier in identifiers:
            if identifier not in ["started_at"]:
                self.add_error(
                    self.RESPONSE_METADATA_REFERENCE_INVALID, identifier=identifier
                )

    def _validate_answer_source_reference(self, identifiers, selector=None):
        answers_with_context = self.questionnaire_schema.answers_with_context

        for identifier in identifiers:
            if identifier not in answers_with_context:
                self.add_error(self.ANSWER_REFERENCE_INVALID, identifier=identifier)

            if selector:
                answer_type = answers_with_context[identifier]["answer"]["type"]

                if answer_type not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP:
                    self.add_error(self.COMPOSITE_ANSWER_INVALID, identifier=identifier)
                elif (
                    selector not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP[answer_type]
                ):
                    self.add_error(
                        self.COMPOSITE_ANSWER_FIELD_INVALID, identifier=identifier
                    )
