import pytest

import api


# pylint: disable=duplicate-code
@pytest.mark.usefixtures("mock_ajv_valid")
def test_validate_no_json_data(client):

    response = client.post("/validate")
    assert response.status_code == 400
    assert "No JSON data provided for validation" in response.text


@pytest.mark.usefixtures("mock_ajv_valid")
def test_validate_post_wrong_type(client):

    response = client.post("/validate", json=[7, 8, 9])
    assert response.status_code == 400
    assert "Invalid data type received for validation" in response.text


@pytest.mark.usefixtures("mock_ajv_down")
def test_validate_post_ajv_unavailable_returns_503(client, valid_schema):

    response = client.post("/validate", json=valid_schema)
    assert response.status_code == 503
    assert "AJV Schema Validator service unavailable" in response.text


@pytest.mark.usefixtures("mock_ajv_valid")
def test_validate_post_questionnaire_validator_errors(client, valid_schema, monkeypatch):

    class MockValidator:
        def __init__(self, _json_data):
            self.errors = [{"message": "questionnaire invalid"}]

        def validate(self):
            return None

    monkeypatch.setattr(api, "QuestionnaireValidator", MockValidator)

    response = client.post("/validate", json=valid_schema)
    assert response.status_code == 400
    assert "errors" in response.text
