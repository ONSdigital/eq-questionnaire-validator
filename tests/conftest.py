import os

from app.validators.questionnaire_schema import QuestionnaireSchema


def find_all_json_files(folder_name):
    return [
        os.path.join(folder, filename)
        for folder, _, files in os.walk(folder_name)
        for filename in files
        if filename.endswith(".json")
    ]


def get_mock_schema(questionnaire_schema, answers_with_context):
    if not questionnaire_schema:
        questionnaire_schema = QuestionnaireSchema({})

    if answers_with_context:
        questionnaire_schema.answers_with_context = answers_with_context

    return questionnaire_schema
