# Modern PyTumblr

This branch is an isolated modernization layer built on top of `agent/oauth2-support`.
The historical `TumblrRestClient` remains available unchanged; modern behavior is opt-in with:

```python
from pytumblr.modern import ModernTumblrRestClient
```

## Modern post API

- NPF-first reads (`npf=true` by default, toggleable with `npf_consumption_on/off`).
- `create_post()` via `POST /v2/blog/{blog}/posts`.
- `edit_post()` via `PUT /v2/blog/{blog}/posts/{id}`.
- NPF reblogs with automatic parent UUID/reblog-key lookup and caching.
- JSON and multipart NPF requests under both OAuth1 and OAuth2.
- `media_sources={identifier: path_or_file}` compatible with Tumblr's multipart JSON+media shape.

Example media upload:

```python
client.create_post(
    "example.tumblr.com",
    content=[
        {"type": "text", "text": "hello"},
        {"type": "image", "media": [{"type": "image/jpeg", "identifier": "photo"}]},
    ],
    media_sources={"photo": "/path/to/photo.jpg"},
)
```

## Convenience API

- `get_single_post()`
- `notifications()`
- `notes()`
- `iter_posts()`, `iter_queue()`, `iter_likes()`
- `get_root_post()`
- NPF traversal helpers in `pytumblr.npf`: `iter_blocks`, `iter_media`, `iter_images`, `iter_text`
- block constructors for text, link, image, audio and video

The modern client also exposes legacy-shaped creation helpers (`create_text`, `create_photo`, `create_quote`, `create_link`, `create_chat`, `create_audio`, `create_video`) implemented through modern NPF endpoints. The classic client retains the original legacy endpoint behavior.

## Async

`pytumblr.async_client.AsyncModernTumblrRestClient` returns asyncio Futures while reusing the same synchronous OAuth/signing and multipart implementation. On Python 3 the results can be awaited directly.

## Typing

The package ships PEP 561 metadata (`py.typed`) and `.pyi` stubs. `pytumblr.types` keeps dict semantics at runtime while exposing `TypedDict` definitions to static type checkers.

## Regression coverage

The branch covers:

- modern create/edit endpoint selection
- list-valued tags on edits
- OAuth1/OAuth2 multipart NPF payloads
- bearer-token preservation during multipart uploads
- Tumblr `/tagged` top-level array responses
- pagination iterators
- reblog metadata caching
- trail/media traversal
- local photo legacy→NPF adaptation

CI now runs pytest, rather than only building distributions, across Python 3.7, 3.8, 3.9, 3.11 and 3.12 before building the package.
