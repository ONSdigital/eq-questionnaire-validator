from app.validation.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_get_driving_question_blocks():
    filename = "schemas/valid/test_list_collector_driving_question.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    driving_question_blocks = questionnaire_schema.get_driving_question_blocks("people")

    assert questionnaire_schema.list_names == ["people"]
    assert len(driving_question_blocks) == 1
    assert driving_question_blocks[0]["id"] == "anyone-usually-live-at"


def test_get_context_from_path():
    filename = "schemas/valid/test_question_variants.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    context = questionnaire_schema.get_context_from_path(
        "sections.[0].groups.[0].blocks.[1]"
    )

    assert context == {"section": "section", "group_id": "group", "block": "block-2"}


def test_questions_with_context():
    filename = "schemas/valid/test_question_variants.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    assert questionnaire_schema.questions_with_context == [
        (
            {
                "id": "question-1",
                "type": "General",
                "title": "What is your age?",
                "answers": [
                    {
                        "id": "answer-1",
                        "label": "Your age?",
                        "mandatory": False,
                        "type": "Number",
                    }
                ],
            },
            {"group_id": "group", "section": "section", "block": "block-1"},
        ),
        (
            {
                "id": "question-2",
                "type": "General",
                "title": "What is your age?",
                "answers": [
                    {
                        "id": "answer-2",
                        "label": "Your age?",
                        "mandatory": False,
                        "type": "Number",
                    }
                ],
            },
            {"group_id": "group", "section": "section", "block": "block-2"},
        ),
        (
            {
                "id": "question-2",
                "type": "General",
                "title": "What is your age?",
                "answers": [
                    {
                        "id": "answer-2",
                        "label": "Your age?",
                        "mandatory": False,
                        "type": "Number",
                    }
                ],
            },
            {"group_id": "group", "section": "section", "block": "block-2"},
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
