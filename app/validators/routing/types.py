"""This module contains functions to resolve the JSON type of various sources in a questionnaire schema.

Functions:
    resolve_answer_source_json_type
    resolve_calculated_summary_source_json_type
    resolve_grand_calculated_summary_source_json_type
    resolve_metadata_source_json_type
    resolve_list_source_json_type
    resolve_value_source_json_type
    python_type_to_json_type
"""

from typing import Mapping

from app.validators.questionnaire_schema import QuestionnaireSchema

TYPE_STRING = "string"
TYPE_NUMBER = "number"
TYPE_ARRAY = "array"
TYPE_OBJECT = "object"
TYPE_DATE = "date"
TYPE_BOOLEAN = "boolean"
TYPE_NULL = "null"

ANSWER_TYPE_TO_JSON_TYPE = {
    "Address": TYPE_OBJECT,
    "Duration": TYPE_OBJECT,
    "Relationship": TYPE_OBJECT,
    "Checkbox": TYPE_ARRAY,
    "Date": TYPE_STRING,
    "MonthYearDate": TYPE_STRING,
    "YearDate": TYPE_STRING,
    "Dropdown": TYPE_STRING,
    "MobileNumber": TYPE_STRING,
    "Radio": TYPE_STRING,
    "TextArea": TYPE_STRING,
    "TextField": TYPE_STRING,
    "Currency": TYPE_NUMBER,
    "Number": TYPE_NUMBER,
    "Percentage": TYPE_NUMBER,
    "Unit": TYPE_NUMBER,
}

LIST_SELECTOR_TO_JSON_TYPE = {
    "count": TYPE_NUMBER,
    "first": TYPE_STRING,
    "primary_person": TYPE_STRING,
    "same_name_items": TYPE_ARRAY,
}

PYTHON_TYPE_TO_JSON_TYPE = {
    "dict": TYPE_OBJECT,
    "list": TYPE_ARRAY,
    "str": TYPE_STRING,
    "int": TYPE_NUMBER,
    "float": TYPE_NUMBER,
    "bool": TYPE_BOOLEAN,
    "NoneType": TYPE_NULL,
}

METADATA_TYPE_TO_JSON_TYPE = {
    "string": TYPE_STRING,
    "date": TYPE_STRING,
    "boolean": TYPE_BOOLEAN,
    "uuid": TYPE_STRING,
    "url": TYPE_STRING,
}


def resolve_answer_source_json_type(answer_id: str, schema: QuestionnaireSchema) -> str:
    """Resolve the JSON type of answer source by looking up the answer type in the questionnaire schema and mapping
    it to the corresponding JSON type.

    Args:
        answer_id: The identifier of the answer source to resolve the JSON type for.
        schema: The questionnaire schema to use for resolving the JSON type.

    Returns:
        The JSON type of the answer source as a string.
    """
    answer_type = schema.answers_with_context[answer_id]["answer"]["type"]
    return ANSWER_TYPE_TO_JSON_TYPE[answer_type]


def resolve_calculated_summary_source_json_type(
    block: Mapping,
    schema: QuestionnaireSchema,
) -> str:
    """Resolves the JSON type of calculated summary source by looking at the first answer to calculate or value source
    in its calculation operation.

    Args:
        block: The block containing the grand calculated summary source to resolve the JSON type for.
        schema: The questionnaire schema to use for resolving the JSON type.

    Returns:
        The JSON type of the calculated summary source as a string.
    """
    if block["calculation"].get("answers_to_calculate"):
        answer_id = block["calculation"]["answers_to_calculate"][0]
    else:
        answer_value_source = block["calculation"]["operation"]["+"][0]
        answer_id = answer_value_source["identifier"]
    answer_type = schema.answers_with_context[answer_id]["answer"]["type"]
    return ANSWER_TYPE_TO_JSON_TYPE[answer_type]


def resolve_grand_calculated_summary_source_json_type(
    block: Mapping,
    schema: QuestionnaireSchema,
) -> str:
    """Resolves the JSON type of grand calculated summary source by looking at the first value source in its calculation
    operation.

    Args:
        block: The block containing the grand calculated summary source to resolve the JSON type for.
        schema: The questionnaire schema to use for resolving the JSON type.

    Returns:
        The JSON type of the grand calculated summary source as a string.
    """
    first_calculated_summary_source = block["calculation"]["operation"]["+"][0]
    return resolve_value_source_json_type(first_calculated_summary_source, schema)


def resolve_metadata_source_json_type(
    identifier: str | None,
    schema: QuestionnaireSchema,
) -> str:
    """Resolves the JSON type of metadata source based on its identifier and the questionnaire schema.

    Args:
        identifier: The identifier of the metadata source to resolve the JSON type for.
        schema: The questionnaire schema to use for resolving the JSON type.

    Returns:
        The JSON type of the metadata source as a string, or "string" if the identifier is None or not found in the
        schema metadata.
    """
    if identifier:
        for values in schema.schema.get("metadata", []):
            if values.get("name") == identifier:
                return METADATA_TYPE_TO_JSON_TYPE[values.get("type")]
    return TYPE_STRING


def resolve_list_source_json_type(selector: str | None) -> str:
    """Resolves the list selector to JSON type, if selector is None, defaults to array type else returns the
    corresponding JSON type for the selector.

    Args:
        selector: The list selector to resolve to a JSON type.

    Returns:
        The JSON type corresponding to the list selector, or "array" if the selector is None.
    """
    return LIST_SELECTOR_TO_JSON_TYPE[selector] if selector else TYPE_ARRAY


def resolve_value_source_json_type(
    value_source: dict[str, str],
    schema: QuestionnaireSchema,
) -> str:
    """Resolves the JSON type of value source based on its source, identifier, and selector.

    Args:
        value_source: A dictionary containing the source, identifier, and selector of the value source.
        schema: The questionnaire schema to use for resolving the JSON type.

    Returns:
        The JSON type of the value source as a string.
    """
    source = value_source["source"]
    identifier = value_source.get("identifier")
    selector = value_source.get("selector")
    if identifier:
        if source == "answers":
            return resolve_answer_source_json_type(identifier, schema)

        if block := schema.get_block(identifier):
            if source == "calculated_summary" and "calculation" in block:
                return resolve_calculated_summary_source_json_type(block, schema)

            if source == "grand_calculated_summary":
                return resolve_grand_calculated_summary_source_json_type(block, schema)

        if source == "metadata":
            return resolve_metadata_source_json_type(identifier, schema)

    if source == "list":
        return resolve_list_source_json_type(selector)

    return TYPE_STRING


def python_type_to_json_type(python_type: str) -> str:
    """Converts a Python type to its corresponding JSON type.

    Args:
        python_type: The name of the Python type to convert.

    Returns:
        The corresponding JSON type as a string.
    """
    return PYTHON_TYPE_TO_JSON_TYPE[python_type]
