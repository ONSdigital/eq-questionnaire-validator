import pytest


# pylint: disable=duplicate-code
@pytest.mark.usefixtures("mock_urlopen_not_found")
def test_validate_get_url_not_found(client):

    url = "https://raw.githubusercontent.com/ONSdigital/does_not_exist.json"
    response = client.get("/validate", params={"url": url})

    assert response.status_code == 404
    assert "Could not load schema from allowed domain - URL not found" in response.text


def test_validate_get_url_domain_not_allowed(client):

    url = "ftp://does_not_exist.com/"
    response = client.get("/validate", params={"url": url})

    assert response.status_code == 400
    assert "URL domain [does_not_exist.com] is not allowed" in response.text
