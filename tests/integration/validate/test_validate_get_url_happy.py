from urllib.parse import urlencode

def test_validate_get_url_happy_path(client, mock_urlopen_valid, mock_ajv_valid):

    url = "https://raw.githubusercontent.com/ONSdigital/eq-questionnaire-runner/main/schemas/test/en/test_checkbox.json"
    response = client.get("/validate", params={"url": url})

    assert response.status_code == 200
    assert response.json() == {}
    assert "errors" not in response.json()
    