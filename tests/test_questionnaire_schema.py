"""Tests for the QuestionnaireSchema class and its methods."""

from jsonpath_rw import parse

from app.validators.questionnaire_schema import (
    QuestionnaireSchema,
    get_context_from_match,
)
from tests.utils import _open_and_load_schema_file


def test_get_blocks():
    """Test getting blocks by type and list name."""
    filename = "schemas/valid/test_list_collector_driving_question.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    driving_question_blocks = questionnaire_schema.get_blocks(
        type="ListCollectorDrivingQuestion",
        for_list="people",
    )

    assert len(driving_question_blocks) == 1
    assert driving_question_blocks[0]["id"] == "anyone-usually-live-at"


def test_get_other_blocks():
    """Test getting other blocks by type and list name."""
    filename = "schemas/valid/test_list_collector.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    other_list_collectors = questionnaire_schema.get_other_blocks(
        block_id_to_filter="list-collector",
        type="ListCollector",
        for_list="people",
    )

    assert len(other_list_collectors) == 1
    assert other_list_collectors[0]["id"] == "another-list-collector"


def test_get_context_from_match():
    """Test getting context from a JSONPath match."""
    filename = "schemas/valid/test_question_variants.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    matches = parse("$..blocks[*]").find(questionnaire_schema.schema)
    context = get_context_from_match(matches[0])

    assert context == {"section": "section", "group_id": "group", "block": "block-1"}


def test_questions_with_context():
    """Test getting questions with context."""
    filename = "schemas/valid/test_question_variants.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    assert list(questionnaire_schema.questions_with_context) == [
        (
            {
                "id": "question-1",
                "type": "General",
                "title": "Are you answering for yourself",
                "answers": [
                    {
                        "type": "Radio",
                        "id": "answer-1",
                        "mandatory": True,
                        "options": [
                            {"label": "Yes", "value": "Yes"},
                            {"label": "No", "value": "No"},
                        ],
                    },
                ],
            },
            {"section": "section", "block": "block-1", "group_id": "group"},
        ),
        (
            {
                "id": "question-2",
                "type": "General",
                "title": "Are you in full time education?",
                "answers": [
                    {
                        "type": "Radio",
                        "id": "answer-2",
                        "mandatory": False,
                        "options": [
                            {"label": "Yes", "value": "Yes"},
                            {"label": "No", "value": "No"},
                        ],
                    },
                ],
            },
            {"section": "section", "block": "block-2", "group_id": "group"},
        ),
        (
            {
                "id": "question-2",
                "type": "General",
                "title": "Is the person your are answering for in full time education?",
                "answers": [
                    {
                        "type": "Radio",
                        "id": "answer-2",
                        "mandatory": False,
                        "options": [
                            {"label": "Yes", "value": "Yes"},
                            {"label": "No", "value": "No"},
                        ],
                    },
                ],
            },
            {"section": "section", "block": "block-2", "group_id": "group"},
        ),
    ]


def test_get_sub_block_context():
    """Test getting sub-block context."""
    filename = "schemas/valid/test_list_collector_driving_question.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    assert [
        (question["id"], context)
        for question, context in questionnaire_schema.questions_with_context
    ] == [
        (
            "anyone-usually-live-at-question",
            {
                "group_id": "group",
                "section": "section",
                "block": "anyone-usually-live-at",
            },
        ),
        (
            "confirmation-question",
            {"group_id": "group", "section": "section", "block": "anyone-else-live-at"},
        ),
        (
            "add-question",
            {"group_id": "group", "section": "section", "block": "add-person"},
        ),
        (
            "edit-question",
            {"group_id": "group", "section": "section", "block": "edit-person"},
        ),
        (
            "remove-question",
            {"group_id": "group", "section": "section", "block": "remove-person"},
        ),
    ]


def test_id_paths():
    """Test getting ID paths from the questionnaire schema."""
    filename = "schemas/valid/test_list_collector_variants.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    found_paths = list(questionnaire_schema.id_paths)

    assert found_paths == [
        ("sections.[0]", "section"),
        ("sections.[0].groups.[0]", "group"),
        ("sections.[0].groups.[0].blocks.[0]", "you-live-here-block"),
        ("sections.[0].groups.[0].blocks.[0].question", "you-live-here-question"),
        (
            "sections.[0].groups.[0].blocks.[0].question.answers.[0]",
            "you-live-here-answer",
        ),
        ("sections.[0].groups.[0].blocks.[1]", "list-collector"),
        (
            "sections.[0].groups.[0].blocks.[1].question_variants.[0].question",
            "confirmation-question",
        ),
        (
            "sections.[0].groups.[0].blocks.[1].question_variants.[0].question.answers.[0]",
            "anyone-else",
        ),
        (
            "sections.[0].groups.[0].blocks.[1].question_variants.[1].question",
            "confirmation-question",
        ),
        (
            "sections.[0].groups.[0].blocks.[1].question_variants.[1].question.answers.[0]",
            "anyone-else",
        ),
        ("sections.[0].groups.[0].blocks.[1].add_block", "add-person"),
        (
            "sections.[0].groups.[0].blocks.[1].add_block.question_variants.[0].question",
            "add-question",
        ),
        (
            "sections.[0].groups.[0].blocks.[1].add_block.question_variants.[1].question",
            "add-question",
        ),
        ("sections.[0].groups.[0].blocks.[1].edit_block", "edit-person"),
        (
            "sections.[0].groups.[0].blocks.[1].edit_block.question_variants.[0].question",
            "edit-question",
        ),
        (
            "sections.[0].groups.[0].blocks.[1].edit_block.question_variants.[1].question",
            "edit-question",
        ),
        ("sections.[0].groups.[0].blocks.[1].remove_block", "remove-person"),
        (
            "sections.[0].groups.[0].blocks.[1].remove_block.question_variants.[0].question",
            "remove-question",
        ),
        (
            "sections.[0].groups.[0].blocks.[1].remove_block.question_variants.[1].question",
            "remove-question",
        ),
    ]


def test_get_block_id_by_answer_id():
    """Test getting block ID by answer ID."""
    filename = "schemas/valid/test_q_codes.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    answer_id = "confirmation-1-answer"

    block_id = questionnaire_schema.get_block_id_by_answer_id(answer_id)

    assert block_id == "confirmation-1"


def test_answers_with_context():
    """Test getting answers with context from the questionnaire schema."""
    filename = "schemas/valid/test_dynamic_answers_list_source.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    assert questionnaire_schema.answers_with_context == {
        "any-supermarket-answer": {
            "answer": {
                "id": "any-supermarket-answer",
                "mandatory": True,
                "options": [
                    {
                        "action": {
                            "params": {
                                "block_id": "add-supermarket",
                                "list_name": "supermarkets",
                            },
                            "type": "RedirectToListAddBlock",
                        },
                        "label": "Yes",
                        "value": "Yes",
                    },
                    {"label": "No", "value": "No"},
                ],
                "type": "Radio",
            },
            "block": "any-supermarket",
            "group_id": "group",
            "section": "section",
        },
        "days-a-week": {
            "answer": {
                "decimal_places": 0,
                "id": "days-a-week",
                "label": {
                    "placeholders": [
                        {
                            "placeholder": "transformed_value",
                            "value": {
                                "identifier": "supermarket-name",
                                "source": "answers",
                            },
                        },
                    ],
                    "text": "How many days a week you shop at {transformed_value}",
                },
                "mandatory": True,
                "maximum": {"value": 7},
                "minimum": {"value": 1},
                "type": "Number",
            },
            "block": "dynamic-answer",
            "group_id": "group",
            "section": "section",
        },
        "list-collector-answer": {
            "answer": {
                "id": "list-collector-answer",
                "mandatory": True,
                "options": [
                    {
                        "action": {"type": "RedirectToListAddBlock"},
                        "label": "Yes",
                        "value": "Yes",
                    },
                    {"label": "No", "value": "No"},
                ],
                "type": "Radio",
            },
            "block": "list-collector",
            "group_id": "group",
            "section": "section",
        },
        "percentage-of-shopping": {
            "answer": {
                "decimal_places": 0,
                "id": "percentage-of-shopping",
                "label": {
                    "placeholders": [
                        {
                            "placeholder": "transformed_value",
                            "value": {
                                "identifier": "supermarket-name",
                                "source": "answers",
                            },
                        },
                    ],
                    "text": "Percentage of shopping at {transformed_value}",
                },
                "mandatory": False,
                "maximum": {"value": 100},
                "type": "Percentage",
            },
            "block": "dynamic-answer",
            "group_id": "group",
            "section": "section",
        },
        "remove-confirmation": {
            "answer": {
                "id": "remove-confirmation",
                "mandatory": True,
                "options": [
                    {
                        "action": {"type": "RemoveListItemAndAnswers"},
                        "label": "Yes",
                        "value": "Yes",
                    },
                    {"label": "No", "value": "No"},
                ],
                "type": "Radio",
            },
            "block": "remove-supermarket",
            "group_id": "group",
            "section": "section",
        },
        "set-maximum": {
            "answer": {
                "decimal_places": 2,
                "description": "Maximum amount of spending at this supermarket",
                "id": "set-maximum",
                "label": "Maximum amount of spending",
                "mandatory": True,
                "maximum": {"value": 10000},
                "minimum": {"value": 1001},
                "type": "Number",
            },
            "block": "edit-supermarket",
            "group_id": "group",
            "section": "section",
        },
        "supermarket-name": {
            "answer": {
                "id": "supermarket-name",
                "label": "Supermarket",
                "mandatory": True,
                "type": "TextField",
            },
            "block": "edit-supermarket",
            "group_id": "group",
            "section": "section",
        },
    }


def test_answers_method():
    """Test getting answers from the questionnaire schema."""
    filename = "schemas/valid/test_dynamic_answers_list_source.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    answers = list(questionnaire_schema.answers)

    assert answers == [
        {
            "id": "any-supermarket-answer",
            "mandatory": True,
            "options": [
                {
                    "action": {
                        "params": {
                            "block_id": "add-supermarket",
                            "list_name": "supermarkets",
                        },
                        "type": "RedirectToListAddBlock",
                    },
                    "label": "Yes",
                    "value": "Yes",
                },
                {"label": "No", "value": "No"},
            ],
            "type": "Radio",
        },
        {
            "id": "list-collector-answer",
            "mandatory": True,
            "options": [
                {
                    "action": {"type": "RedirectToListAddBlock"},
                    "label": "Yes",
                    "value": "Yes",
                },
                {"label": "No", "value": "No"},
            ],
            "type": "Radio",
        },
        {
            "id": "supermarket-name",
            "label": "Supermarket",
            "mandatory": True,
            "type": "TextField",
        },
        {
            "decimal_places": 2,
            "description": "Maximum amount of spending at this supermarket, should be "
            "between 1001 and 10000",
            "id": "set-maximum",
            "label": "Maximum Spending",
            "mandatory": True,
            "maximum": {"value": 10000},
            "minimum": {"value": 1001},
            "type": "Number",
        },
        {
            "id": "supermarket-name",
            "label": "Supermarket",
            "mandatory": True,
            "type": "TextField",
        },
        {
            "decimal_places": 2,
            "description": "Maximum amount of spending at this supermarket",
            "id": "set-maximum",
            "label": "Maximum amount of spending",
            "mandatory": True,
            "maximum": {"value": 10000},
            "minimum": {"value": 1001},
            "type": "Number",
        },
        {
            "id": "remove-confirmation",
            "mandatory": True,
            "options": [
                {
                    "action": {"type": "RemoveListItemAndAnswers"},
                    "label": "Yes",
                    "value": "Yes",
                },
                {"label": "No", "value": "No"},
            ],
            "type": "Radio",
        },
        {
            "decimal_places": 0,
            "id": "percentage-of-shopping",
            "label": {
                "placeholders": [
                    {
                        "placeholder": "transformed_value",
                        "value": {
                            "identifier": "supermarket-name",
                            "source": "answers",
                        },
                    },
                ],
                "text": "Percentage of shopping at {transformed_value}",
            },
            "mandatory": False,
            "maximum": {"value": 100},
            "type": "Percentage",
        },
        {
            "decimal_places": 0,
            "id": "days-a-week",
            "label": {
                "placeholders": [
                    {
                        "placeholder": "transformed_value",
                        "value": {
                            "identifier": "supermarket-name",
                            "source": "answers",
                        },
                    },
                ],
                "text": "How many days a week you shop at {transformed_value}",
            },
            "mandatory": True,
            "maximum": {"value": 7},
            "minimum": {"value": 1},
            "type": "Number",
        },
    ]


def test_get_all_answer_ids_dynamic_answers():
    """Test getting all answer IDs for a dynamic answer block."""
    filename = "schemas/valid/test_dynamic_answers_list_source.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    assert questionnaire_schema.get_all_answer_ids("dynamic-answer") == {
        "days-a-week",
        "percentage-of-shopping",
    }


def test_get_first_answer_in_block_dynamic_answers():
    """Test getting the first answer in a dynamic answer block."""
    filename = "schemas/valid/test_dynamic_answers_list_source.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    assert questionnaire_schema.get_first_answer_in_block("dynamic-answer") == {
        "label": {
            "text": "Percentage of shopping at {transformed_value}",
            "placeholders": [
                {
                    "placeholder": "transformed_value",
                    "value": {"source": "answers", "identifier": "supermarket-name"},
                },
            ],
        },
        "id": "percentage-of-shopping",
        "mandatory": False,
        "type": "Percentage",
        "maximum": {"value": 100},
        "decimal_places": 0,
    }


def test_get_block_id_by_answer_id_dynamic_answers():
    """Test getting block ID by answer ID for dynamic answers."""
    filename = "schemas/valid/test_dynamic_answers_list_source.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    assert (
        questionnaire_schema.get_block_id_by_answer_id("percentage-of-shopping")
        == "dynamic-answer"
    )
