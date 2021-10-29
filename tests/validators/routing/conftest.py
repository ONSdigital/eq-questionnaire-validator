import pytest

from app.validators.routing.new_when_rule_validator import NewWhenRuleValidator


@pytest.fixture(scope="function")
def mock_is_source_id_valid(monkeypatch):
    def mock_return(*args):  # pylint: disable=unused-argument
        # return true to skip id name validations within schema
        return True

    monkeypatch.setattr(NewWhenRuleValidator, "is_source_identifier_valid", mock_return)
