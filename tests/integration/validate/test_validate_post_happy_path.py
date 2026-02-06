import pytest


@pytest.mark.usefixtures("mock_ajv_valid")
def test_valid_schema_post(client, valid_schema):

    response = client.post("/validate", json=valid_schema)
    assert response.status_code == 200
    assert response.json() == {}
