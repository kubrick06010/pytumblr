from unittest.mock import Mock

import pytest

from pytumblr.modern import ModernTumblrRestClient
from pytumblr import npf


def _client():
    client = ModernTumblrRestClient(
        "consumer", "secret", "token", "token_secret"
    )
    client.request = Mock()
    return client


def test_create_post_uses_modern_npf_endpoint():
    client = _client()
    client.request.post_npf.return_value = {"id": "123"}
    content = [{"type": "text", "text": "Hello from Python"}]

    result = client.create_post(
        "example.tumblr.com", content=content, tags=["python", "tumblr"]
    )

    assert result == {"id": "123"}
    client.request.post_npf.assert_called_once_with(
        "/v2/blog/example.tumblr.com/posts",
        {"content": content, "tags": ["python", "tumblr"], "state": "published"},
        None,
    )


def test_create_post_preserves_explicit_state():
    client = _client()
    content = [{"type": "text", "text": "Draft"}]
    client.create_post("example.tumblr.com", content=content, state="draft")
    assert client.request.post_npf.call_args[0][1]["state"] == "draft"


def test_create_post_passes_media_sources_outside_json():
    client = _client()
    media_sources = {"photo": "/tmp/photo.jpg"}
    content = [npf.image_upload_block("photo")]
    client.create_post(
        "example.tumblr.com", content=content, media_sources=media_sources
    )
    client.request.post_npf.assert_called_once_with(
        "/v2/blog/example.tumblr.com/posts",
        {"content": content, "state": "published"},
        media_sources,
    )


def test_create_post_requires_non_empty_content():
    client = _client()
    with pytest.raises(ValueError):
        client.create_post("example.tumblr.com", content=[])


def test_edit_post_uses_put_and_preserves_tags_as_list():
    client = _client()
    client.request.put_npf.return_value = {"id": "123"}
    content = [{"type": "text", "text": "Edited"}]

    result = client.edit_post(
        "example.tumblr.com", 123, content=content, tags=["python", "api"]
    )

    assert result == {"id": "123"}
    client.request.put_npf.assert_called_once_with(
        "/v2/blog/example.tumblr.com/posts/123",
        {"content": content, "tags": ["python", "api"]},
        None,
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


def test_iter_posts_paginates_until_short_page():
    client = _client()
    client.posts = Mock(side_effect=[
        {"posts": [{"id": i} for i in range(20)]},
        {"posts": [{"id": 20}, {"id": 21}]},
    ])
    assert [p["id"] for p in client.iter_posts("example.tumblr.com")] == list(range(22))


def test_reblog_resolves_and_caches_requirements():
    client = _client()
    client.get_single_post = Mock(return_value={
        "reblog_key": "rk",
        "blog": {"uuid": "t:uuid"},
    })
    client.request.post_npf.return_value = {"id": "new"}

    client.reblog_post("dest.tumblr.com", "source.tumblr.com", 42)
    client.reblog_post("dest.tumblr.com", "source.tumblr.com", 42)

    assert client.get_single_post.call_count == 1
    payload = client.request.post_npf.call_args[0][1]
    assert payload["parent_tumblelog_uuid"] == "t:uuid"
    assert payload["parent_post_id"] == "42"
    assert payload["reblog_key"] == "rk"


def test_image_upload_block_uses_creation_identifier_object():
    block = npf.image_upload_block("media0")
    assert block == {"type": "image", "media": {"identifier": "media0"}}


def test_audio_upload_block_is_native_tumblr_media_object():
    block = npf.audio_upload_block("media0")
    assert block == {
        "type": "audio",
        "provider": "tumblr",
        "media": {"identifier": "media0"},
    }


def test_video_upload_block_is_native_tumblr_media_object():
    block = npf.video_upload_block("media0")
    assert block == {
        "type": "video",
        "provider": "tumblr",
        "media": {"identifier": "media0"},
    }


def test_create_photo_local_file_builds_npf_media_reference():
    client = _client()
    client.create_post = Mock(return_value={"id": "x"})
    client.create_photo("example.tumblr.com", data="/tmp/photo.jpg", caption="hi")
    kwargs = client.create_post.call_args[1]
    assert kwargs["content"][0]["media"]["identifier"] == "media0"
    assert kwargs["media_sources"] == {"media0": "/tmp/photo.jpg"}


def test_create_audio_local_file_builds_native_media_reference():
    client = _client()
    client.create_post = Mock(return_value={"id": "x"})
    client.create_audio("example.tumblr.com", data="/tmp/audio.wav")
    kwargs = client.create_post.call_args[1]
    assert kwargs["content"][0] == {
        "type": "audio",
        "provider": "tumblr",
        "media": {"identifier": "media0"},
    }


def test_npf_helpers_traverse_trail_media():
    post = {
        "content": [{"type": "image", "media": [{"url": "a"}]}],
        "trail": [{"content": [{"type": "image", "media": [{"url": "b"}]}]}],
    }
    assert [item["url"] for item in npf.iter_images(post)] == ["a", "b"]
