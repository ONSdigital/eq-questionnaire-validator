from jsonpath_rw import parse

from app.validators.questionnaire_schema import (
    QuestionnaireSchema,
    get_context_from_match,
)
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_get_blocks():
    filename = "schemas/valid/test_list_collector_driving_question.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    driving_question_blocks = questionnaire_schema.get_blocks(
        type="ListCollectorDrivingQuestion", for_list="people"
    )

    assert len(driving_question_blocks) == 1
    assert driving_question_blocks[0]["id"] == "anyone-usually-live-at"


def test_get_other_blocks():
    filename = "schemas/valid/test_list_collector.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    other_list_collectors = questionnaire_schema.get_other_blocks(
        block_id_to_filter="list-collector", type="ListCollector", for_list="people"
    )

    assert len(other_list_collectors) == 1
    assert other_list_collectors[0]["id"] == "another-list-collector"


def test_get_context_from_match():
    filename = "schemas/valid/test_question_variants.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    matches = parse("$..blocks[*]").find(questionnaire_schema.schema)
    context = get_context_from_match(matches[0])

    assert context == {"section": "section", "group_id": "group", "block": "block-1"}


def test_questions_with_context():
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
                    }
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
                    }
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
                    }
                ],
            },
            {"section": "section", "block": "block-2", "group_id": "group"},
        ),
    ]


def test_get_sub_block_context():
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
    filename = "schemas/valid/test_q_codes.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    answer_id = "confirmation-1-answer"

    block_id = questionnaire_schema.get_block_id_by_answer_id(answer_id)

    assert block_id == "confirmation-1"
