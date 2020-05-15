from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_get_blocks():
    filename = "schemas/valid/test_list_collector_driving_question.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    driving_question_blocks = questionnaire_schema.get_blocks(
        type="ListCollectorDrivingQuestion", for_list="people"
    )

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

    assert list(questionnaire_schema.questions_with_context) == [
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


def test_id_paths():
    filename = "schemas/valid/test_list_collector.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    found_paths = list(questionnaire_schema.id_paths)

    assert found_paths == [
        ("sections.[0]", "section"),
        ("sections.[0].groups.[0]", "group"),
        ("sections.[0].groups.[0].blocks.[0]", "list-collector"),
        ("sections.[0].groups.[0].blocks.[0].add_answer", "anyone-else"),
        ("sections.[0].groups.[0].blocks.[0].remove_answer", "remove-confirmation"),
        ("sections.[0].groups.[0].blocks.[0].question", "confirmation-question"),
        ("sections.[0].groups.[0].blocks.[0].question.answers.[0]", "anyone-else"),
        ("sections.[0].groups.[0].blocks.[0].add_block", "add-person"),
        ("sections.[0].groups.[0].blocks.[0].add_block.question", "add-question"),
        ("sections.[0].groups.[0].blocks.[0].edit_block", "edit-person"),
        ("sections.[0].groups.[0].blocks.[0].edit_block.question", "edit-question"),
        ("sections.[0].groups.[0].blocks.[0].remove_block", "remove-person"),
        ("sections.[0].groups.[0].blocks.[0].remove_block.question", "remove-question"),
        ("sections.[0].groups.[0].blocks.[1]", "another-list-collector"),
        ("sections.[0].groups.[0].blocks.[1].add_answer", "another-anyone-else"),
        (
            "sections.[0].groups.[0].blocks.[1].remove_answer",
            "another-remove-confirmation",
        ),
        (
            "sections.[0].groups.[0].blocks.[1].question",
            "another-confirmation-question",
        ),
        (
            "sections.[0].groups.[0].blocks.[1].question.answers.[0]",
            "another-anyone-else",
        ),
        ("sections.[0].groups.[0].blocks.[1].add_block", "another-add-person"),
        (
            "sections.[0].groups.[0].blocks.[1].add_block.question",
            "another-add-question",
        ),
        ("sections.[0].groups.[0].blocks.[1].edit_block", "another-edit-person"),
        (
            "sections.[0].groups.[0].blocks.[1].edit_block.question",
            "another-edit-question",
        ),
        ("sections.[0].groups.[0].blocks.[1].remove_block", "another-remove-person"),
        (
            "sections.[0].groups.[0].blocks.[1].remove_block.question",
            "another-remove-question",
        ),
        ("sections.[0].groups.[0].blocks.[2]", "summary"),
    ]
