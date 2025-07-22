from app.validators.answers.answer_validator import AnswerValidator
from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.answers.number_answer_validator import NumberAnswerValidator
from app.validators.answers.option_answer_validator import OptionAnswerValidator
from app.validators.answers.text_field_answer_validator import TextFieldAnswerValidator


def get_answer_validator(answer, questionnaire_schema):
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
