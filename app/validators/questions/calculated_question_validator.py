from app.validators.questions.question_validator import QuestionValidator
from app.validators.routing.types import ANSWER_TYPE_TO_JSON_TYPE, TYPE_NUMBER


class CalculatedQuestionValidator(QuestionValidator):
    ANSWER_NOT_IN_QUESTION = "Answer does not exist within this question"
    ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID = "Expected the answer type for calculation to be type 'number' but got type '{answer_type}'"

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
            for answer_id in calculation["answers_to_calculate"]:
                if answer_id not in answer_ids:
                    self.add_error(self.ANSWER_NOT_IN_QUESTION, answer_id=answer_id)

    def _validate_answer_is_numeric(self, *, question_id, answer_id):
        answer_type = self.schema.get_answer_type(answer_id)

        if ANSWER_TYPE_TO_JSON_TYPE[answer_type.value] != TYPE_NUMBER:
            self.add_error(
                self.ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID.format(
                    answer_type=ANSWER_TYPE_TO_JSON_TYPE[answer_type.value],
                ),
                referenced_question_id=question_id,
                identifier=answer_id,
            )

    def validate_calculations_value_source_is_numeric(self):
        """
        Validates that source answer is of number type
        """
        for calculation in self.question.get("calculations"):
            value = calculation.get("value")

            if answer_id := calculation.get("answer_id"):
                question_id = self.schema.get_block_by_answer_id(answer_id)["question"][
                    "id"
                ]
                self._validate_answer_is_numeric(
                    question_id=question_id, answer_id=answer_id
                )

            elif value and value.get("source"):
                answer_id = value.get("identifier")
                # Calculated summary value source is validated elsewhere and must be of a number type

                if value.get("source") == "answers":
                    question_id = self.schema.get_block_by_answer_id(answer_id)[
                        "question"
                    ]["id"]
                    self._validate_answer_is_numeric(
                        question_id=question_id, answer_id=answer_id
                    )
