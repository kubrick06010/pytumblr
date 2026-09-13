# Modern Posts development notes

The user-facing documentation for the modern client now lives in
[`docs/modern.rst`](docs/modern.rst).

This file is intentionally kept as a development/milestone note for the
`modern-posts` branch rather than as the canonical user manual.

## Architecture

The modern layer is opt-in via `pytumblr.modern.ModernTumblrRestClient` and is
stacked on top of `agent/oauth2-support`, keeping the classic
`TumblrRestClient` behavior isolated.

The branch currently includes:

- NPF-first reads with legacy opt-out.
- Modern create/edit/reblog endpoints.
- Shared OAuth1/OAuth2 modern transport behavior for JSON, PUT and multipart NPF.
- Multipart media uploads.
- Reblog metadata lookup and caching.
- Pagination iterators, notes, notifications and trail/media helpers.
- Legacy-shaped creation adapters backed by NPF.
- Async Future-based facade.
- PEP 561 metadata, stubs and TypedDict definitions.
- Regression tests for transport, media, pagination, tags and Tumblr response edge cases.

## Documentation contract

`tests/test_docs_contract.py` is the maintenance guardrail for the public modern
surface. It checks that the declared modern API:

1. exists at runtime,
2. exists in `pytumblr/modern.pyi`,
3. is mentioned in `docs/modern.rst`, and
4. can execute a representative NPF create flow without network access.

CI runs that contract explicitly before the complete pytest suite. A public API
change should therefore update runtime code, stubs, tests and the public guide
in the same pull request.

## Validation

GitHub Actions were explicitly enabled on the fork. CI covers Python 3.7, 3.8,
3.9, 3.11 and 3.12; Python 3.7 runs on Ubuntu 22.04 because the Ubuntu 24.04
runner no longer provides that interpreter through `setup-python`.
