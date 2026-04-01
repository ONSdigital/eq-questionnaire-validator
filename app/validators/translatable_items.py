"""This module defines the TranslatableItem class and functions to extract translatable items from a schema element.

Classes:
    TranslatableItem
"""

from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

from jsonpath_ng import parse
from jsonpointer import resolve_pointer

EXTRACTABLE_STRINGS = [
    {"json_path": "$.title", "description": "Questionnaire title"},
    {"json_path": "$.legal_basis", "description": "Questionnaire legal basis"},
    {"json_path": "$.messages.*", "description": "Global answer error message"},
    {"json_path": "$.submission.button", "description": "Submission button"},
    {
        "json_path": "$.submission.guidance",
        "description": "Submission guidance",
    },
    {"json_path": "$.submission.title", "description": "Submission title"},
    {"json_path": "$.submission.warning", "description": "Submission warning"},
    {
        "json_path": "$.post_submission.guidance.contents[*].title",
        "description": "Post submission guidance heading",
    },
    {
        "json_path": "$.post_submission.guidance.contents[*].description",
        "description": "Post submission guidance description",
    },
    {
        "json_path": "$.post_submission.guidance.contents[*].list[*]",
        "description": "Post submission guidance list item",
        "additional_context": ["ListHeading", "ListDescription"],
    },
    {"json_path": "$.sections[*].title", "description": "Section title"},
    {"json_path": "$..page_title", "description": "Page title"},
    {
        "json_path": "$.sections[*].repeat.title",
        "description": "Section title (repeating section)",
    },
    {
        "json_path": "$.sections[*].repeat.page_title",
        "description": "Section page title suffix (repeating section)",
    },
    {
        "json_path": "$.sections[*].summary.items[*].title",
        "description": "Section summary item title",
    },
    {
        "json_path": "$.sections[*].summary.items[*].add_link_text",
        "description": "Section summary list add link",
    },
    {
        "json_path": "$.sections[*].summary.items[*].empty_list_text",
        "description": "Section summary empty list text",
    },
    {
        "json_path": "$.sections[*].summary.items[*].item_label",
        "description": "Label for the item title on a section summary",
    },
    {"json_path": "$..groups[*].title", "description": "Group title"},
    {"json_path": "$..blocks[*].title", "description": "Block title"},
    {"json_path": "$..summary.title", "description": "List collector summary heading"},
    {
        "json_path": "$..summary.item_title",
        "description": "List collector summary item",
    },
    {
        "json_path": "$..summary.empty_list_text",
        "description": "List collector empty list text",
    },
    {
        "json_path": "$..summary.add_link_text",
        "description": "List collector add link text",
    },
    {
        "json_path": "$..summary.item_label",
        "description": "List collector item label",
    },
    {
        "json_path": "$..add_block.cancel_text",
        "description": "List collector add block cancel link",
    },
    {
        "json_path": "$..repeating_blocks[*].question.title.text",
        "description": "Repeating block question",
    },
    {"json_path": "$..content.title", "description": "Content page main heading"},
    {"json_path": "$..content.instruction[*]", "description": "Content instruction"},
    {
        "json_path": "$..content.contents[*].title",
        "description": "Content page heading",
        "context": "Content",
    },
    {
        "json_path": "$..content.contents[*].description",
        "description": "Content page description",
        "context": "Content",
    },
    {
        "json_path": "$..content.contents[*].list[*]",
        "description": "Content page list item",
        "context": "Content",
        "additional_context": ["ListHeading", "ListDescription"],
    },
    {
        "json_path": "$..content.contents[*].definition.title",
        "description": "Definition title",
        "context": "Content",
    },
    {
        "json_path": "$..content.contents[*].definition.contents[*].description",
        "description": "Definition description",
        "context": "Content",
    },
    {
        "json_path": "$..content_variants[*].content.title",
        "description": "Content page heading",
        "context": "Content",
    },
    {
        "json_path": "$..content_variants[*].content.contents[*].description",
        "description": "Content page description",
        "context": "Content",
    },
    {"json_path": "$..question.title", "description": "Question text"},
    {
        "json_path": "$..question.description[*]",
        "description": "Question description",
        "context": "Question",
    },
    {
        "json_path": "$..question.instruction[*]",
        "description": "Question instruction",
        "context": "Question",
    },
    {
        "json_path": "$..question.warning",
        "description": "Question warning",
        "context": "Question",
    },
    {
        "json_path": "$..question.definitions[*].title",
        "description": "Question definition link",
        "context": "Question",
    },
    {
        "json_path": "$..question.definitions[*].contents[*].title",
        "description": "Question definition heading",
        "context": "Question",
    },
    {
        "json_path": "$..question.definitions[*].contents[*].description",
        "description": "Question definition description",
        "context": "Question",
    },
    {
        "json_path": "$..question.definitions[*].contents[*].list[*]",
        "description": "Question definition list item",
        "context": "Question",
        "additional_context": ["ListHeading", "ListDescription"],
    },
    {
        "json_path": "$..question.definition.title",
        "description": "Question definition heading",
        "context": "Question",
    },
    {
        "json_path": "$..question.definition.contents[*].title",
        "description": "Question definition heading",
        "context": "Question",
    },
    {
        "json_path": "$..question.definition.contents[*].description",
        "description": "Question definition description",
        "context": "Question",
    },
    {
        "json_path": "$..question.definition.contents[*].list[*]",
        "description": "Question definition list item",
        "context": "Question",
        "additional_context": ["ListHeading", "ListDescription"],
    },
    {
        "json_path": "$..question.guidance.contents[*].title",
        "description": "Question guidance heading",
        "context": "Question",
    },
    {
        "json_path": "$..question.guidance.contents[*].description",
        "description": "Question guidance description",
        "context": "Question",
    },
    {
        "json_path": "$..question.guidance.contents[*].list[*]",
        "description": "Question guidance list item",
        "context": "Question",
        "additional_context": ["ListHeading", "ListDescription"],
    },
    {
        "json_path": "$..question.calculation.title",
        "description": "Question calculation title",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].validation.messages.*",
        "description": "Answer error message",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].label",
        "description": "Answer",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].instruction",
        "description": "Checkbox answer instruction",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].placeholder",
        "description": "Dropdown field placeholder text",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].description",
        "description": "Answer description",
        "context": "Question",
        "additional_context": ["Answer"],
    },
    {
        "json_path": "$..answers[*].playback",
        "description": "Relationships playback template",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].options[*].label",
        "description": "Answer option",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].options[*].description",
        "description": "Answer option description",
        "context": "Question",
        "additional_context": ["AnswerOption"],
    },
    {
        "json_path": "$..answers[*].options[*].detail_answer.label",
        "description": "Detail answer label",
        "context": "Question",
        "additional_context": ["AnswerOption"],
    },
    {
        "json_path": "$..answers[*].options[*].detail_answer.description",
        "description": "Detail answer description",
        "context": "Question",
        "additional_context": ["AnswerOption"],
    },
    {
        "json_path": "$..answers[*].options[*].title",
        "description": "Relationships answer option question text",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].options[*].playback",
        "description": "Relationships answer option playback text",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].guidance.show_guidance",
        "description": "Answer guidance show link",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].guidance.hide_guidance",
        "description": "Answer guidance hide link",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].guidance.contents[*].title",
        "description": "Answer guidance heading",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].guidance.contents[*].description",
        "description": "Answer guidance description",
        "context": "Question",
    },
    {
        "json_path": "$..answers[*].guidance.contents[*].list[*]",
        "description": "Answer guidance list item",
        "context": "Question",
        "additional_context": ["ListHeading", "ListDescription"],
    },
    {
        "json_path": "$..primary_content[*].title",
        "description": "Introduction main title",
    },
    {
        "json_path": "$..primary_content[*].contents[*].list[*]",
        "description": "Introduction main list item",
        "context": "PrimaryContent",
        "additional_context": ["ListHeading", "ListDescription"],
    },
    {
        "json_path": "$..primary_content[*].contents[*].description",
        "description": "Introduction main description",
        "context": "PrimaryContent",
    },
    {
        "json_path": "$..primary_content[*].contents[*].guidance.contents[*].title",
        "description": "Introduction main guidance title",
        "context": "PrimaryContent",
    },
    {
        "json_path": "$..primary_content[*].contents[*].guidance.contents[*].description",
        "description": "Introduction main guidance description",
        "context": "PrimaryContent",
        "additional_context": ["ListHeading"],
    },
    {
        "json_path": "$..primary_content[*].contents[*].guidance.contents[*].list[*]",
        "description": "Introduction main guidance list",
        "context": "PrimaryContent",
        "additional_context": ["ListHeading"],
    },
    {
        "json_path": "$..preview_content.title",
        "description": "Introduction preview title",
    },
    {
        "json_path": "$..preview_content.contents[*].description",
        "description": "Introduction preview description",
        "context": "PreviewContent",
    },
    {
        "json_path": "$..preview_content.questions[*].question",
        "description": "Introduction preview question title",
        "context": "PreviewContent",
    },
    {
        "json_path": "$..preview_content.questions[*].contents[*].description",
        "description": "Introduction preview question description",
        "context": "PreviewContent",
        "additional_context": ["PreviewQuestionListHeading"],
    },
    {
        "json_path": "$..preview_content.questions[*].contents[*].list[*]",
        "description": "Introduction preview question list item",
        "context": "PreviewContent",
        "additional_context": ["PreviewQuestionListHeading"],
    },
    {
        "json_path": "$..secondary_content[*].contents[*].title",
        "description": "Introduction additional title",
    },
    {
        "json_path": "$..secondary_content[*].contents[*].list[*]",
        "description": "Introduction additional list item",
        "context": "ListHeading",
        "additional_context": ["ListDescription"],
    },
    {
        "json_path": "$..secondary_content[*].contents[*].description",
        "description": "Introduction additional description",
        "context": "ListHeading",
    },
]

CONTEXT_DEFINITIONS = {
    "Question": {
        "parent_schema_property": "question",
        "property": "title",
        "text": "{context}",
    },
    "Content": {
        "parent_schema_property": "content",
        "property": "title",
        "text": "{context}",
    },
    "Answer": {
        "parent_schema_property": "answers",
        "property": "label",
        "text": "For answer: {context}",
    },
    "AnswerOption": {
        "parent_schema_property": "options",
        "property": "label",
        "text": "For answer option: {context}",
    },
    "ListHeading": {
        "parent_schema_property": "contents",
        "property": "title",
        "text": "For heading: {context}",
    },
    "ListDescription": {
        "parent_schema_property": "contents",
        "property": "description",
        "text": "For description: {context}",
    },
    "PrimaryContent": {
        "parent_schema_property": "primary_content",
        "property": "title",
        "text": "{context}",
    },
    "PreviewContent": {
        "parent_schema_property": "preview_content",
        "property": "title",
        "text": "{context}",
    },
    "PreviewQuestionListHeading": {
        "parent_schema_property": "questions",
        "property": "question",
        "text": "For question: {context}",
    },
}


# pylint: disable=unsubscriptable-object
@dataclass
class TranslatableItem:
    """Represents a translatable item within the schema.

    Attributes:
        pointer (str): JSON pointer for this item within the schema.
        description (str): Description of the translatable item.
        value (str | dict): The resolved value of the pointer. This is a dict for plural forms, and a string for all
        other elements.
        context (str | None): The context to use when translating the item.
        additional_context (list[str] | None): Additional context for the item, if any.
    """

    pointer: str
    description: str
    value: str | dict
    context: str | None = None
    additional_context: list[str] | None = None


def get_translatable_items(schema_element: dict) -> Generator[TranslatableItem]:
    """Yields all translatable items found in the given schema element.

    Args:
        schema_element: The schema element to search for translatable items.

    Yields:
        TranslatableItem: An item representing a translatable string in the schema.
    """
    for extractable_string in EXTRACTABLE_STRINGS:
        json_path = parse(extractable_string["json_path"])  # type: ignore
        # The type ignore is necessary because jsonpath-ng's parse method does not have type hints

        for match in json_path.find(schema_element):
            # The type ignore is necessary because jsonpath-ng's find doesn't have type hints, match is an "object" type
            json_pointer, string_value = _get_json_pointer_and_string_value(str(match.full_path), match.value)
            additional_context = []
            for context_type in extractable_string.get("additional_context", []):  # type: ignore
                context = _get_context_for_pointer(schema_element, json_pointer, context_type)
                if context:
                    additional_context.append(context)

            yield TranslatableItem(
                pointer=json_pointer,
                description=extractable_string["description"],  # type: ignore
                value=string_value,
                context=_get_context_for_pointer(schema_element, json_pointer, extractable_string.get("context")),  # type: ignore
                additional_context=additional_context or None,
            )


def _get_parent_schema_object(input_data: dict, json_pointer: str, parent_property: str) -> Any:
    """Get the parent schema object identified by `parent_property` in the JSON pointer.

    If the parent schema object is a list, the matching array item is returned.

    Args:
        input_data: The input data to search.
        json_pointer: The pointer being searched.
        parent_property: The parent property to search for.

    Returns:
        The schema object identified by `parent_property`.
    """
    json_pointer = json_pointer.replace("(", "").replace(")", "")
    pointer_parts = json_pointer.split("/")
    pointer_index = pointer_parts.index(parent_property)
    parent_pointer = "/".join(pointer_parts[: pointer_index + 1])
    schema_object = resolve_pointer(input_data, parent_pointer)
    if isinstance(schema_object, list):
        return schema_object[int(pointer_parts[pointer_index + 1])]
    return schema_object


def _get_context_for_pointer(schema: dict, pointer: str, context_type: str) -> str | None:
    """Returns the context string for a given pointer and context type.

    Args:
        schema: The schema to search.
        pointer: The JSON pointer to the item.
        context_type: The type of context to retrieve.

    Returns:
        str: The formatted context string, or None if not found.
    """
    context_definition = CONTEXT_DEFINITIONS.get(context_type)
    if context_definition:
        parent_schema_object = _get_parent_schema_object(schema, pointer, context_definition["parent_schema_property"])
        if context_definition["property"] in parent_schema_object:
            context_string = _get_single_string_value(parent_schema_object[context_definition["property"]])
            return context_definition["text"].format(context=context_string)
    return None


def _get_json_pointer_and_string_value(json_path: str, schema_object: dict) -> tuple[str, str | dict]:
    """Resolves the given schema_object to a json pointer and value.

    Args:
        json_path: the json path to convert to a pointer
        schema_object: the object at the json path to resolve to a string value
    Returns:
        json pointer: the json pointer for the schema object
        string value: the string value of the schema object. This is a Tuple for plural forms
    """
    json_pointer = _json_path_to_json_pointer(json_path).replace("(", "").replace(")", "")
    if isinstance(schema_object, dict):
        plural_forms = schema_object.get("text_plural", {}).get("forms")
        if plural_forms:
            return f"{json_pointer}/text_plural/forms", plural_forms
        return f"{json_pointer}/text", schema_object["text"]

    return json_pointer, schema_object


def _json_path_to_json_pointer(json_path: str) -> str:
    """Convert a JSONPath string into a JSON Pointer string.

    Args:
        json_path: The JSONPath to convert.

    Returns:
        str: The equivalent JSON Pointer.
    """
    json_pointer = json_path.replace("[", "").replace("]", "").replace(".", "/")
    return f"/{json_pointer}"


def _get_single_string_value(schema_object: dict) -> dict:
    """Return a string value identifying the schema_object. If plural, returns the `other` form.

    Args:
        schema_object: the object to resolve to a string value
    Returns:
        string value: the string value of the schema object. If plural, returns the `other` form
    """
    if isinstance(schema_object, dict):
        if "text_plural" in schema_object:
            return schema_object["text_plural"]["forms"]["other"]
        return schema_object["text"]
    return schema_object
