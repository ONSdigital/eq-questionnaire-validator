from app.validators.questions.question_validator import QuestionValidator
from app.validators.routing.types import ANSWER_TYPE_TO_JSON_TYPE, TYPE_NUMBER


class CalculatedQuestionValidator(QuestionValidator):
    ANSWER_NOT_IN_QUESTION = "Answer does not exist within this question"
    ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID = "Expected the answer type for calculation to be type 'number' but got type '{answer_type}'"
    ANSWER_TYPES_FOR_CALCULATION_MISMATCH = "Expected the answer types for calculation to be same type but got {answer_types}'"
    ANSWERS_TO_CALCULATE_TOO_SHORT = "Answers to calculate list is too short {list}"

    def validate(self):
        super().validate()
        self.validate_calculations()
        if self.errors:
            # If there are missing answers/not enough, exit to prevent errors in validation of the types
            return self.errors
        self.validate_calculations_numeric_matching_answer_types()
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

    def validate_calculations_numeric_matching_answer_types(self):
        """
        Validates that source answer is of number type, and that the answers_to_calculate match that type
        """
        for calculation in self.question.get("calculations"):
            if not (answer_id := calculation.get("answer_id")):
                value = calculation.get("value")
                # Calculated summary value source is validated elsewhere and must be of a number type
                if isinstance(value, dict) and value.get("source") == "answers":
                    answer_id = value.get("identifier")

            if answer_id:
                self._validate_answer_is_numeric(answer_id)
                self._validate_answers_are_same_numeric_type(
                    calculation.get("answers_to_calculate"), answer_id
                )

    def _validate_answers_are_same_numeric_type(self, answers_to_calculate, answer_id):
        """
        Checks that the answers to calculate and the answer_id are all the same type
        """
        types = {
            self.schema.get_answer_type(answer).value
            for answer in [answer_id, *answers_to_calculate]
        }
        if len(types) > 1:
            self.add_error(
                self.ANSWER_TYPES_FOR_CALCULATION_MISMATCH.format(
                    answer_types=sorted(types),
                ),
                referenced_answer=answer_id,
            )
