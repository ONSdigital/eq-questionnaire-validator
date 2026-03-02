import pytest


@pytest.mark.usefixtures("mock_ajv_valid")
def test_validate_get_url_happy_path(client):
    """Test the /validate endpoint with a valid URL."""
    valid_url = (
        "https://raw.githubusercontent.com/ONSdigital/"
        "eq-questionnaire-validator/refs/heads/main/tests/schemas/valid/test_list_collector.json"
    )
    response = client.get("/validate", params={"url": valid_url})

    assert response.status_code == 200
    assert response.json() == {}
    assert "errors" not in response.json()
