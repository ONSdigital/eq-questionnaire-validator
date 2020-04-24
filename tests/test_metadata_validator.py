from app.validation import error_messages
from app.validation.metadata_validator import MetadataValidator


def test_mandatory_metadata():
    metadata = [
        {"name": "period_id", "type": "string"},
        {"name": "user_id", "type": "string"},
    ]
    validator = MetadataValidator(metadata, "default")
    validator.validate_mandatory()

    expected_errors = [
        {"message": error_messages.FOUND_MISSING_METADATA, "metadata": "ru_name"}
    ]

    assert validator.errors == expected_errors


def test_mandatory_metadata_non_default_theme():
    metadata = [
        {"name": "period_id", "type": "string"},
        {"name": "user_id", "type": "string"},
    ]
    validator = MetadataValidator(metadata, "another_theme")
    validator.validate_mandatory()

    assert validator.errors == []


def test_duplicate_metadata():
    metadata = [
        {"name": "period_id", "type": "string"},
        {"name": "user_id", "type": "string"},
        {"name": "period_id", "type": "string"},
    ]
    validator = MetadataValidator(metadata, "default")
    validator.validate_duplicates()

    expected_errors = [
        {
            "message": error_messages.FOUND_DUPLICATE_METADATA,
            "duplicates": ["period_id"],
        }
    ]

    assert validator.errors == expected_errors
