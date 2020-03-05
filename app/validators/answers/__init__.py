from app.validators.answers.answer_validator import AnswerValidator
from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.answers.number_answer_validator import NumberAnswerValidator
from app.validators.answers.text_field_answer_validator import TextFieldAnswerValidator


def get_answer_validator(answer, list_names, block_ids):
    validators = {
        "TextField": TextFieldAnswerValidator,
        "Date": DateAnswerValidator,
        "Number": NumberAnswerValidator,
        "Currency": NumberAnswerValidator,
        "Percentage": NumberAnswerValidator,
    }
    return validators.get(answer["type"], AnswerValidator)(
        answer, list_names, block_ids
    )
