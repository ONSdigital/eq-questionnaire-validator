import pytest

import api


@pytest.mark.usefixtures("mock_ajv_valid")
def test_validate_no_json_data(client):
    """Test the /validate endpoint with no JSON data."""
    response = client.post("/validate")
    assert response.status_code == 400
    assert "No JSON data provided for validation" in response.text


@pytest.mark.usefixtures("mock_ajv_valid")
def test_validate_post_wrong_data_type(client):
    """Test the /validate endpoint with a wrong data type."""
    response = client.post("/validate", json=[7, 8, 9])
    assert response.status_code == 400
    assert "Invalid data type received for validation" in response.text


@pytest.mark.usefixtures("mock_ajv_down")
def test_validate_post_ajv_unavailable_returns_503(client, load_valid_schema):
    """Test the /validate endpoint when the AJV service is unavailable."""
    response = client.post("/validate", json=load_valid_schema)
    assert response.status_code == 503
    assert "AJV Schema Validator service unavailable" in response.text


@pytest.mark.usefixtures("mock_ajv_valid")
def test_validate_post_questionnaire_validator_errors(client, load_valid_schema, monkeypatch):
    """Test the /validate endpoint with questionnaire validator errors."""

    class MockValidator:
        """Mock validator for testing."""

        def __init__(self, _json_data):
            self.errors = [{"message": "questionnaire invalid"}]

        def validate(self):
            return None

    monkeypatch.setattr(api, "QuestionnaireValidator", MockValidator)

    response = client.post("/validate", json=load_valid_schema)
    assert response.status_code == 400
    assert "errors" in response.text
