from app.validators.questions.question_validator import QuestionValidator
from app.validators.routing.types import ANSWER_TYPE_TO_JSON_TYPE, TYPE_NUMBER


class CalculatedQuestionValidator(QuestionValidator):
    ANSWER_NOT_IN_QUESTION = "Answer does not exist within this question"
    ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID = "Expected the answer type for calculation to be type 'number' but got type '{answer_type}'"

    def validate(self):
        super().validate()
        self.validate_calculations()
        self.validate_value_source()
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

    def check_answer_type(self, answer_type, answer_id):
        if ANSWER_TYPE_TO_JSON_TYPE[answer_type.value] != TYPE_NUMBER:
            self.add_error(
                self.ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID.format(
                    answer_type=ANSWER_TYPE_TO_JSON_TYPE[answer_type.value],
                ),
                identifier=answer_id,
            )

    def validate_value_source(self):
        """
        Validates that source answer is of number type
        """
        for calculation in self.question.get("calculations"):
            if answer_id := calculation.get("answer_id"):
                self.check_answer_type(
                    self.schema[0][0].get_answer_type(answer_id), answer_id
                )

            elif calculation.get("value") and calculation.get("value").get("source"):
                answer_id = calculation.get("value").get("identifier")
                self.check_answer_type(
                    self.schema[0][0].get_answer_type(answer_id), answer_id
                )
