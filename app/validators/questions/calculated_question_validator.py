from app.validators.questions.question_validator import QuestionValidator
from app.validators.routing.types import ANSWER_TYPE_TO_JSON_TYPE, TYPE_NUMBER


class CalculatedQuestionValidator(QuestionValidator):
    ANSWER_NOT_IN_QUESTION = "Answer does not exist within this question"
    ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID = "Expected the answer type for calculation to be type 'number' but got type '{answer_type}'"
    ANSWERS_TO_CALCULATE_TOO_SHORT = "Answers to calculate list is too short {list}"

    def validate(self):
        super().validate()
        self.validate_calculations()
        self.validate_calculations_value_source_is_numeric()
        return self.errors

    def validate_calculations(self):
        """
        Validates that any answer ids within the 'answer_to_group'
        list are existing answers within the question
        """
        answer_ids = [answer["id"] for answer in self.answers]
        for calculation in self.question.get("calculations"):
            answer_ids_list = calculation["answers_to_calculate"]
            if len(answer_ids_list) == 1 and answer_ids_list[
                0
            ] not in self.schema.get_all_dynamic_answer_ids(
                self.schema.get_block_by_answer_id(answer_ids_list[0])["id"]
            ):
                self.add_error(
                    self.ANSWERS_TO_CALCULATE_TOO_SHORT.format(
                        list=answer_ids_list,
                    )
                )
            for answer_id in answer_ids_list:
                if answer_id not in answer_ids:
                    self.add_error(self.ANSWER_NOT_IN_QUESTION, answer_id=answer_id)

    def _validate_answer_is_numeric(self, answer_id):
        answer_type = self.schema.get_answer_type(answer_id)

        if ANSWER_TYPE_TO_JSON_TYPE[answer_type.value] != TYPE_NUMBER:
            self.add_error(
                self.ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID.format(
                    answer_type=ANSWER_TYPE_TO_JSON_TYPE[answer_type.value],
                ),
                referenced_answer=answer_id,
            )

    def validate_calculations_value_source_is_numeric(self):
        """
        Validates that source answer is of number type
        """
        for calculation in self.question.get("calculations"):
            value = calculation.get("value")

            if answer_id := calculation.get("answer_id"):
                self._validate_answer_is_numeric(answer_id)

            elif isinstance(value, dict) and value.get("source"):
                answer_id = value.get("identifier")
                # Calculated summary value source is validated elsewhere and must be of a number type

                if value.get("source") == "answers":
                    self._validate_answer_is_numeric(answer_id)
