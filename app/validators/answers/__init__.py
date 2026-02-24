from app.validators.answers.answer_validator import AnswerValidator
from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.answers.number_answer_validator import NumberAnswerValidator
from app.validators.answers.option_answer_validator import OptionAnswerValidator
from app.validators.answers.text_field_answer_validator import TextFieldAnswerValidator


def get_answer_validator(answer, questionnaire_schema):
    """Factory function called by section validator to return the appropriate answer validator based on
    the answer type. If answer type doesn't match keys in validators dict, it returns a default `AnswerValidator`.

    Args:
        answer (dict): The answer to be validated.
        questionnaire_schema (QuestionnaireSchema): The entire questionnaire schema, which may be needed for certain
        validators.

    Returns:
        An instance of an answer validator class that corresponds to the type of the answer.
    """
    validators = {
        "TextField": TextFieldAnswerValidator,
        "Date": DateAnswerValidator,
        "Number": NumberAnswerValidator,
        "Currency": NumberAnswerValidator,
        "Percentage": NumberAnswerValidator,
        "Dropdown": OptionAnswerValidator,
        "Radio": OptionAnswerValidator,
        "Checkbox": OptionAnswerValidator,
    }
    validator_type = validators.get(answer["type"], AnswerValidator)

    return validator_type(answer, questionnaire_schema)
