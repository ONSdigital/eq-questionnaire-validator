from structlog import configure, getLogger  # pyright: ignore
from structlog.stdlib import LoggerFactory  # pyright: ignore

from app.validators.questionnaire_validator import QuestionnaireValidator
from tests.utils import _open_and_load_schema_file

logger = getLogger()

configure(logger_factory=LoggerFactory())


def test_invalid_non_linear_progress_references():
    """Tests a progress value source cannot refer to a section or block located later in the questionnaire."""
    schema_path = "schemas/invalid/test_invalid_progress_value_source_non_linear.json"
    questionnaire_validator = QuestionnaireValidator(
        _open_and_load_schema_file(schema_path),
    )
    questionnaire_validator.validate()

    expected_error_messages = [
        {
            "msg": "Invalid progress source reference: the identifier being referenced in the progress source "
            "must come before the current block",
            "identifier": "s1-b3",
        },
        {
            "msg": "Invalid progress source reference: the identifier being referenced in the progress source "
            "must come before the current block",
            "identifier": "s2-b1",
        },
        {
            "msg": "Invalid progress source reference: the identifier being referenced in the progress source "
            "must come before the current section",
            "identifier": "second-section",
        },
    ]

    error_messages = [
        {"msg": error["message"], "identifier": error["identifier"]} for error in questionnaire_validator.errors
    ]

    for expected_error in expected_error_messages:
        assert expected_error in error_messages


def test_invalid_current_location_progress():
    """Tests a progress value source cannot refer to the current section or the current block."""
    schema_path = "schemas/invalid/test_invalid_progress_value_source_current_location.json"
    questionnaire_validator = QuestionnaireValidator(
        _open_and_load_schema_file(schema_path),
    )
    questionnaire_validator.validate()

    expected_error_messages = [
        {
            "msg": "Invalid progress source reference: the identifier being referenced in the progress source cannot "
            "be the current block",
            "identifier": "s1-b1",
        },
        {
            "msg": "Invalid progress source reference: the identifier being referenced in the progress source cannot "
            "be the current section",
            "identifier": "first-section",
        },
    ]

    error_messages = [
        {"msg": error["message"], "identifier": error["identifier"]} for error in questionnaire_validator.errors
    ]

    for expected_error in expected_error_messages:
        assert expected_error in error_messages


def test_invalid_block_in_repeating_section():
    """Test for invalid block in repeating section.

    Tests a progress value source cannot refer to a block in a repeating section
    except if it is the parent section of the value source. Nor to a repeating section.
    """
    schema_path = "schemas/invalid/test_invalid_progress_value_source_block_in_past_repeating_section.json"
    questionnaire_validator = QuestionnaireValidator(
        _open_and_load_schema_file(schema_path),
    )
    questionnaire_validator.validate()

    expected_error_messages = [
        {
            "msg": (
                "Invalid progress source reference: the identifier being referenced in the progress source cannot "
                "be a block in a repeating section except for current section"
            ),
            "identifier": "dob-block",
        },
        {
            "msg": (
                "Invalid progress source reference: the identifier being referenced in the progress source cannot "
                "be a repeating section"
            ),
            "identifier": "section-2",
        },
    ]

    error_messages = [
        {"msg": error["message"], "identifier": error["identifier"]} for error in questionnaire_validator.errors
    ]

    for expected_error in expected_error_messages:
        assert expected_error in error_messages
