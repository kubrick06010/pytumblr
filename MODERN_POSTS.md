# Modern Posts milestone

This branch is the first isolated step toward a modern, NPF-first PyTumblr client.

## Included

- OAuth1 and OAuth2 JSON request helpers for modern Tumblr endpoints.
- HTTP PUT support in both transports.
- `pytumblr.modern.ModernTumblrRestClient`.
- Raw-NPF `create_post()` using `POST /v2/blog/{blog}/posts`.
- Raw-NPF `edit_post()` using `PUT /v2/blog/{blog}/posts/{id}`.
- Focused tests for endpoint selection, payload preservation, tags, and validation.

## Deliberately deferred

- Multipart NPF media uploads.
- Typed NPF content/layout helpers.
- Automatic legacy-to-NPF conversion.
- Pagination iterators and response `TypedDict`s.
- Notifications/trail convenience helpers.

The legacy `TumblrRestClient` surface remains unchanged in this milestone; users opt in with `from pytumblr.modern import ModernTumblrRestClient` while the modern API matures.
