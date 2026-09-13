Modern PyTumblr
================

The modern client is an opt-in, New Post Format (NPF)-first layer built on top
of PyTumblr's backwards-compatible client. Existing ``TumblrRestClient`` code
continues to use the historical API surface.

Quick start
-----------

.. code-block:: python

    from pytumblr.modern import ModernTumblrRestClient

    client = ModernTumblrRestClient(
        "consumer_key",
        "consumer_secret",
        "oauth_token",
        "oauth_secret",
    )

    post = client.create_post(
        "example.tumblr.com",
        content=[{"type": "text", "text": "Hello from modern PyTumblr"}],
        tags=["python", "tumblr"],
    )

OAuth 2 uses the same modern surface through ``TumblrRestClient2`` credentials
accepted by the inherited client constructor.

NPF-first reads
---------------

The modern client requests NPF responses by default for ``posts()``,
``queue()``, ``drafts()`` and ``submission()``. Use
``npf_consumption_off()`` to request legacy responses and
``npf_consumption_on()`` to switch NPF-first reads back on.

Creating, editing and reblogging
--------------------------------

``create_post()`` sends raw NPF to ``POST /v2/blog/{blog}/posts``.
``edit_post()`` sends raw NPF to ``PUT /v2/blog/{blog}/posts/{id}``.
``reblog_post()`` resolves and caches the parent UUID and reblog key when they
are not supplied explicitly.

A single post can be fetched with ``get_single_post()`` and its root trail post
can be resolved with ``get_root_post()``.

Media uploads
-------------

OAuth 1 and OAuth 2 both support Tumblr's multipart NPF shape: one JSON part
plus named media parts. Reference an identifier from an NPF media block and map
that identifier to a path or file object with ``media_sources``.

.. code-block:: python

    client.create_post(
        "example.tumblr.com",
        content=[
            {"type": "text", "text": "hello"},
            {
                "type": "image",
                "media": [{"type": "image/jpeg", "identifier": "photo"}],
            },
        ],
        media_sources={"photo": "/path/to/photo.jpg"},
    )

Pagination and activity
-----------------------

``iter_posts()``, ``iter_queue()`` and ``iter_likes()`` paginate automatically.
``notes()`` exposes post notes and ``notifications()`` exposes blog activity.

NPF helpers
-----------

``pytumblr.npf`` contains block constructors and traversal helpers. In
particular, ``iter_blocks``, ``iter_media``, ``iter_images`` and ``iter_text``
walk post content and reblog trails without replacing the normal dictionary
response model.

Legacy-shaped creation helpers
------------------------------

For migration convenience, the modern client also provides ``create_text()``,
``create_photo()``, ``create_quote()``, ``create_link()``, ``create_chat()``,
``create_audio()`` and ``create_video()``. These helpers translate the familiar
legacy-shaped arguments into modern NPF requests; the classic client keeps the
original legacy endpoint behavior.

Typing
------

PyTumblr ships PEP 561 metadata, ``.pyi`` stubs and dictionary-oriented
``TypedDict`` definitions in ``pytumblr.types``. The runtime response model
remains normal Python dictionaries.

Async facade
------------

``pytumblr.async_client.AsyncModernTumblrRestClient`` exposes awaitable
``asyncio.Future`` results while reusing the synchronous OAuth, refresh,
serialization and multipart implementation. This keeps authentication behavior
single-sourced.

Documentation contract
----------------------

The modern public surface is guarded by ``tests/test_docs_contract.py``. CI
checks that documented methods exist at runtime, are represented in
``pytumblr/modern.pyi``, remain mentioned in this guide, and that a documented
NPF creation flow works against a no-network test transport. API changes should
therefore update runtime code, stubs, tests and this guide in the same pull
request.
