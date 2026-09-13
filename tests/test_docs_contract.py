import ast
from pathlib import Path

from pytumblr.modern import ModernTumblrRestClient


PUBLIC_MODERN_METHODS = (
    "npf_consumption_on",
    "npf_consumption_off",
    "posts",
    "queue",
    "drafts",
    "submission",
    "create_post",
    "edit_post",
    "notifications",
    "notes",
    "get_single_post",
    "reblog_post",
    "iter_posts",
    "iter_queue",
    "iter_likes",
    "get_root_post",
    "create_text",
    "create_photo",
    "create_quote",
    "create_link",
    "create_chat",
    "create_audio",
    "create_video",
)


class DummyRequest(object):
    def __init__(self):
        self.calls = []

    def post_npf(self, url, payload, media_sources=None):
        self.calls.append(("post", url, payload, media_sources))
        return {"id": "123", "content": payload.get("content", [])}


def _stub_methods():
    source = Path("pytumblr/modern.pyi").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ModernTumblrRestClient":
            return {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    raise AssertionError("ModernTumblrRestClient is missing from pytumblr/modern.pyi")


def test_modern_public_api_exists_at_runtime():
    missing = [
        name for name in PUBLIC_MODERN_METHODS
        if not callable(getattr(ModernTumblrRestClient, name, None))
    ]
    assert not missing, "runtime is missing documented methods: {}".format(missing)


def test_modern_public_api_is_declared_in_stub():
    stub_methods = _stub_methods()
    missing = [name for name in PUBLIC_MODERN_METHODS if name not in stub_methods]
    assert not missing, "modern.pyi is missing public methods: {}".format(missing)


def test_modern_public_api_is_mentioned_in_public_guide():
    guide = Path("docs/modern.rst").read_text(encoding="utf-8")
    missing = [
        name for name in PUBLIC_MODERN_METHODS
        if "``{}()``".format(name) not in guide
    ]
    assert not missing, "docs/modern.rst is missing public methods: {}".format(missing)


def test_documented_create_post_flow_without_network():
    client = ModernTumblrRestClient("consumer", "secret", "token", "token_secret")
    client.request = DummyRequest()

    result = client.create_post(
        "example.tumblr.com",
        content=[{"type": "text", "text": "Hello from modern PyTumblr"}],
        tags=["python", "tumblr"],
    )

    assert result["id"] == "123"
    assert client.request.calls == [
        (
            "post",
            "/v2/blog/example.tumblr.com/posts",
            {
                "content": [
                    {"type": "text", "text": "Hello from modern PyTumblr"}
                ],
                "tags": ["python", "tumblr"],
            },
            None,
        )
    ]
