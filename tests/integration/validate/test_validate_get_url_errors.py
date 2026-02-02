from urllib.parse import urlencode

def test_validate_get_url_not_found(client, mock_urlopen_not_found):

    url = "https://raw.githubusercontent.com/ONSdigital/does_not_exist.json"
    response = client.get("/validate", params={"url": url})

    assert response.status_code == 404
    assert "Could not load schema from allowed domain - URL not found" in response.text
