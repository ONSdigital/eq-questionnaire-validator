"""This module provides the `QuestionValidator` class, which is responsible for validating questions
in a questionnaire schema. It checks for the presence of answer labels when there are multiple answers,
ensuring that the schema adheres to the expected structure and requirements for questions with multiple answers.

Classes:
    QuestionValidator
"""

from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.validator import Validator


class QuestionValidator(Validator):
    """Validator for questions in a questionnaire schema. It checks that if a question has multiple answers,
    and is not of type "MutuallyExclusive", then each answer must have a label.

    Methods:
        validate
        _validate_answer_labels
    """
    ANSWER_LABEL_MISSING_MULTIPLE_ANSWERS = "Answer label must be provided for questions with multiple answers"
    question: dict = {}

    def __init__(self, schema_element, schema=None):
        super().__init__(schema_element)
        self.question = schema_element
        self.answers = QuestionnaireSchema.get_answers_from_question(self.question)
        self.context["question_id"] = schema_element["id"]
        self.schema = schema

    def validate(self):
        """Validates the question by checking if it has multiple answers and is not of type "MutuallyExclusive".

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        if self.question["type"] != "MutuallyExclusive":
            self._validate_answer_labels()

        return self.errors

    def _validate_answer_labels(self):
        """Validates that each answer in the question has a label if the question contains multiple answers and
        other conditions are not met (e.g. if the question has only one answer, or if the last answer is a Checkbox
        with only one option, then labels are not required).
        """
        if len(self.answers) < 2 or (
            len(self.answers) == 2 and self.answers[-1]["type"] == "Checkbox" and len(self.answers[-1]["options"]) == 1
        ):
            return

        for answer in self.answers:
            if not answer.get("label"):
                self.add_error(
                    self.ANSWER_LABEL_MISSING_MULTIPLE_ANSWERS,
                    answer_id=answer["id"],
                )
