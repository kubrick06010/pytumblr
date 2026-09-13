from unittest.mock import Mock

import pytest

from pytumblr.modern import ModernTumblrRestClient


def _client():
    client = ModernTumblrRestClient(
        "consumer", "secret", "token", "token_secret"
    )
    client.request = Mock()
    return client


def test_create_post_uses_modern_npf_endpoint():
    client = _client()
    client.request.post_json.return_value = {"id": "123"}
    content = [{"type": "text", "text": "Hello from Python"}]

    result = client.create_post(
        "example.tumblr.com",
        content=content,
        tags=["python", "tumblr"],
    )

    assert result == {"id": "123"}
    client.request.post_json.assert_called_once_with(
        "/v2/blog/example.tumblr.com/posts",
        {"content": content, "tags": ["python", "tumblr"]},
    )


def test_create_post_requires_non_empty_content():
    client = _client()
    with pytest.raises(ValueError):
        client.create_post("example.tumblr.com", content=[])


def test_edit_post_uses_put_and_preserves_tags_as_list():
    client = _client()
    client.request.put_json.return_value = {"id": "123"}
    content = [{"type": "text", "text": "Edited"}]

    result = client.edit_post(
        "example.tumblr.com",
        123,
        content=content,
        tags=["python", "api"],
    )

    assert result == {"id": "123"}
    client.request.put_json.assert_called_once_with(
        "/v2/blog/example.tumblr.com/posts/123",
        {"content": content, "tags": ["python", "api"]},
    )


def test_edit_post_requires_a_change():
    client = _client()
    with pytest.raises(ValueError):
        client.edit_post("example.tumblr.com", 123)


def test_unknown_npf_options_are_rejected():
    client = _client()
    with pytest.raises(ValueError):
        client.create_post(
            "example.tumblr.com",
            content=[{"type": "text", "text": "Hi"}],
            imaginary_option=True,
        )
