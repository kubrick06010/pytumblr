import json
from unittest.mock import Mock, patch

from pytumblr.request import TumblrRequest
from pytumblr.request2 import TumblrRequest2


def _response(payload, status=200):
    response = Mock()
    response.json.return_value = payload
    response.status_code = status
    response.headers = {}
    response.reason = "OK"
    return response


def test_oauth1_json_parse_accepts_top_level_array():
    request = TumblrRequest("key")
    assert request.json_parse(_response([{"id": 1}])) == [{"id": 1}]


def test_oauth2_json_parse_accepts_top_level_array():
    request = TumblrRequest2("client", {"access_token": "token"})
    assert request.json_parse(_response([{"id": 1}])) == [{"id": 1}]


def test_oauth1_npf_multipart_has_json_part_identifier_and_mime(tmp_path):
    media = tmp_path / "photo.jpg"
    media.write_bytes(b"jpg")
    request = TumblrRequest("key")
    with patch("pytumblr.transport.requests.post") as post:
        post.return_value = _response({"meta": {"status": 201}, "response": {"id": "1"}}, 201)
        request.post_npf(
            "/v2/blog/example/posts",
            {"content": [{"type": "image", "media": {"identifier": "photo"}}]},
            {"photo": str(media)},
        )
        files = post.call_args[1]["files"]
        assert files[0][0] == "json"
        payload = json.loads(files[0][1][1])
        assert payload["content"][0]["media"] == {"identifier": "photo"}
        assert files[1][0] == "photo"
        assert files[1][1][2] == "image/jpeg"


def test_oauth2_npf_multipart_keeps_bearer_header(tmp_path):
    media = tmp_path / "photo.jpg"
    media.write_bytes(b"jpg")
    request = TumblrRequest2("client", {"access_token": "token"})
    with patch("pytumblr.transport.requests.post") as post:
        post.return_value = _response({"meta": {"status": 201}, "response": {"id": "1"}}, 201)
        request.post_npf(
            "/v2/blog/example/posts",
            {"content": [{"type": "image", "media": {"identifier": "photo"}}]},
            {"photo": str(media)},
        )
        assert post.call_args[1]["headers"]["Authorization"] == "Bearer token"
        assert post.call_args[1]["files"][1][1][2] == "image/jpeg"
