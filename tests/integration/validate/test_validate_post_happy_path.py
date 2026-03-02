import pytest


@pytest.mark.usefixtures("mock_ajv_valid")
def test_post_valid_schema(client, load_valid_schema):
    """Test the /validate endpoint with a valid JSON schema."""
    response = client.post("/validate", json=load_valid_schema)
    assert response.status_code == 200
    assert response.json() == {}
