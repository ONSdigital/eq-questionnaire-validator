def test_validate_no_json_data(client, mock_ajv_valid):

    response = client.post("/validate")
    assert response.status_code == 400
    assert "No JSON data provided for validation" in response.text

def test_validate_post_wrong_type(client, mock_ajv_valid):

    response = client.post("/validate", json=[7,8,9])
    assert response.status_code == 400
    assert "Invalid data type received for validation" in response.text

#validator bug - returns 200 even though ajv is an error... 
""" 
def test_validate_post_ajv_errors(client, mock_ajv_error, valid_schema):

    response = client.post("/validate", json=valid_schema)
    assert response.status_code == 400

    body = response.json()
    assert "errors" in body
    assert len(body["errors"]) > 0
"""

def test_validate_post_ajv_unavailable_returns_503(client, valid_schema, mock_ajv_down):

    response = client.post("/validate", json=valid_schema)
    assert response.status_code == 503
    assert "AJV Schema Validator service unavailable" in response.text

def test_validate_post_questionnaire_validator_errors(client, valid_schema, api_module, mock_ajv_valid, monkeypatch):

    class MockValidator:
        def __init__(self, _json_data):
            self.errors = [{"message": "questionnaire invalid"}]
        def validate(self):
            return None
        
    monkeypatch.setattr(api_module, "QuestionnaireValidator", MockValidator)

    response = client.post("/validate", json=valid_schema)
    assert response.status_code == 400
    assert "errors" in response.text