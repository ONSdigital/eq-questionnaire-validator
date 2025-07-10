"""This module provides utility functions for testing the questionnaire schema."""

import os

from app.validators.questionnaire_schema import QuestionnaireSchema


def find_all_json_files(folder_name):
    """Find all JSON files in the specified folder and its subfolders."""
    return [
        os.path.join(folder, filename)
        for folder, _, files in os.walk(folder_name)
        for filename in files
        if filename.endswith(".json")
    ]


def get_mock_schema(questionnaire_schema=None, answers_with_context=None):
    """Return a mock questionnaire schema with optional answers with context."""
    if not questionnaire_schema:
        questionnaire_schema = QuestionnaireSchema({})

    if answers_with_context:
        questionnaire_schema.answers_with_context = answers_with_context

    return questionnaire_schema


def get_mock_schema_with_data_version(data_version):
    """Return a mock questionnaire schema with a specific data version."""
    return QuestionnaireSchema({"data_version": data_version})
