from mock import Mock, patch
import pytest

import pytumblr


TOKEN = {
    "access_token": "access-token",
    "refresh_token": "refresh-token",
    "token_type": "bearer",
    "expires_in": 2520,
    "scope": "basic write offline_access",
}


def response(status, payload):
    result = Mock()
    result.status_code = status
    result.ok = status < 400
    result.json.return_value = payload
    return result


@patch("pytumblr.request2.requests.get")
def test_oauth2_client_uses_bearer_header(get):
    get.return_value = response(200, {"meta": {"status": 200}, "response": {"user": {}}})
    client = pytumblr.TumblrRestClient2("client-id", TOKEN)
    assert client.info() == {"user": {}}
    assert get.call_args[1]["headers"]["Authorization"] == "Bearer access-token"
    assert get.call_args[1]["allow_redirects"] is False
    assert get.call_args[1]["timeout"] == 30


@patch("pytumblr.request2.requests.get")
def test_oauth2_public_endpoint_uses_client_id_as_api_key(get):
    get.return_value = response(200, {"meta": {"status": 200}, "response": {}})
    pytumblr.TumblrRestClient2("client-id", TOKEN).blog_info("example.tumblr.com")
    assert "api_key=client-id" in get.call_args[0][0]


@patch("pytumblr.request2.requests.post")
def test_oauth2_refresh_replaces_tokens_and_notifies_updater(post):
    replacement = dict(TOKEN, access_token="new-access", refresh_token="new-refresh")
    post.return_value = response(200, replacement)
    updater = Mock()
    client = pytumblr.TumblrRestClient2(
        "client-id", TOKEN, client_secret="client-secret", token_updater=updater
    )
    assert client.refresh_token() == replacement
    assert client.request.headers["Authorization"] == "Bearer new-access"
    body = post.call_args[1]["data"]
    assert body["grant_type"] == "refresh_token"
    assert body["refresh_token"] == "refresh-token"
    assert post.call_args[0][0] == "https://api.tumblr.com/v2/oauth2/token"
    assert post.call_args[1]["allow_redirects"] is False
    updater.assert_called_once_with(replacement)


@patch("pytumblr.request2.requests.post")
def test_refresh_preserves_refresh_token_and_rejects_bad_replacement_atomically(post):
    post.return_value = response(200, {"access_token": "new-access", "token_type": "bearer"})
    client = pytumblr.TumblrRestClient2("client-id", TOKEN, client_secret="client-secret")
    assert client.refresh_token()["refresh_token"] == "refresh-token"
    post.return_value = response(200, {"access_token": "bad\nvalue"})
    with pytest.raises(ValueError):
        client.refresh_token()
    assert client.request.token["access_token"] == "new-access"


@patch("pytumblr.request2.requests.post")
def test_refresh_error_does_not_expose_response_secrets(post):
    post.return_value = response(400, {"error": "invalid_grant", "access_token": "server-secret"})
    client = pytumblr.TumblrRestClient2("client-id", TOKEN, client_secret="client-secret")
    with pytest.raises(RuntimeError) as error:
        client.refresh_token()
    assert "invalid_grant" in str(error.value)
    assert "server-secret" not in str(error.value)


@pytest.mark.parametrize("token", [
    {"access_token": "bad\nheader", "token_type": "bearer"},
    {"access_token": "token", "token_type": "mac"},
])
def test_oauth2_rejects_unsafe_tokens(token):
    with pytest.raises(ValueError):
        pytumblr.TumblrRestClient2("client-id", token)


def test_oauth_clients_reject_insecure_or_unapproved_hosts():
    with pytest.raises(ValueError):
        pytumblr.TumblrRestClient2("client-id", TOKEN, host="http://api.tumblr.com")
    with pytest.raises(ValueError):
        pytumblr.TumblrRestClient2("client-id", TOKEN, host="https://example.com")
    client = pytumblr.TumblrRestClient2(
        "client-id", TOKEN, host="https://example.com", allow_custom_host=True
    )
    assert client.request.host == "https://example.com"
