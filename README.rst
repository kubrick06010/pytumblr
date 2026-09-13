PyTumblr
========
|Build Status|

PyTumblr is a Python client for Tumblr's API v2. The historical
``TumblrRestClient`` remains available for backwards compatibility, while the
``modern-posts`` branch also provides an opt-in NPF-first client for current
Tumblr post workflows.

Installation
============

Install via pip:

.. code-block:: bash

    $ pip install pytumblr

Install from source:

.. code-block:: bash

    $ git clone https://github.com/tumblr/pytumblr.git
    $ cd pytumblr
    $ python -m build

Classic client
==============

OAuth 1
-------

.. code:: python

    import pytumblr

    client = pytumblr.TumblrRestClient(
        '<consumer_key>',
        '<consumer_secret>',
        '<oauth_token>',
        '<oauth_secret>',
    )

    client.info()

The classic surface retains the established PyTumblr methods for user, blog,
post, queue, draft, submission, likes, followers, tagged-post and legacy post
creation workflows.

OAuth 2
-------

OAuth 2 bearer tokens are supported through ``TumblrRestClient2``:

.. code:: python

    client = pytumblr.TumblrRestClient2(
        '<client_id>',
        {
            'access_token': '<access_token>',
            'refresh_token': '<refresh_token>',
            'token_type': 'bearer',
            'expires_in': 2520,
            'scope': 'basic write offline_access',
        },
        client_secret='<client_secret>',
    )

    client.info()

When an access token expires, call ``client.refresh_token()`` and persist the
complete returned token response. Tumblr may rotate refresh tokens.

For interactive OAuth 2 setup, install ``pytumblr[console]`` and run
``python interactive_console2.py``. Credential files are written atomically
and use owner-only permissions where POSIX file modes are supported. Do not
commit them to source control.

OAuth 2 requests are restricted to ``https://api.tumblr.com`` by default.
Custom OAuth 2 hosts must use HTTPS and require the explicit
``allow_custom_host=True`` opt-in.

Modern NPF client
=================

The modern client is opt-in and keeps the classic client unchanged:

.. code:: python

    from pytumblr.modern import ModernTumblrRestClient

    client = ModernTumblrRestClient(
        '<consumer_key>',
        '<consumer_secret>',
        '<oauth_token>',
        '<oauth_secret>',
    )

    post = client.create_post(
        'example.tumblr.com',
        content=[{'type': 'text', 'text': 'Hello from modern PyTumblr'}],
        tags=['python', 'tumblr'],
    )

The modern surface provides:

- NPF-first ``posts()``, ``queue()``, ``drafts()`` and ``submission()`` reads.
- Raw-NPF ``create_post()`` and ``edit_post()``.
- NPF ``reblog_post()`` with parent metadata lookup and caching.
- OAuth 1 and OAuth 2 JSON and multipart NPF media transport.
- ``get_single_post()``, ``notes()`` and ``notifications()``.
- ``iter_posts()``, ``iter_queue()`` and ``iter_likes()`` pagination helpers.
- NPF block/media/trail helpers in ``pytumblr.npf``.
- Legacy-shaped creation adapters backed by NPF.
- PEP 561 typing metadata and an async Future-based facade.

See `Modern PyTumblr documentation <docs/modern.rst>`_ for the public modern
API guide, media examples, migration helpers, typing and async usage.

Common classic methods
======================

User methods
------------

.. code:: python

    client.info()
    client.dashboard()
    client.likes()
    client.following()
    client.follow('codingjester.tumblr.com')
    client.unfollow('codingjester.tumblr.com')
    client.like(id, reblogkey)
    client.unlike(id, reblogkey)

Blog methods
------------

.. code:: python

    client.blog_info(blogName)
    client.posts(blogName, **params)
    client.avatar(blogName)
    client.blog_likes(blogName)
    client.followers(blogName)
    client.blog_following(blogName)
    client.queue(blogName)
    client.drafts(blogName)
    client.submission(blogName)

Legacy post creation
--------------------

The classic client preserves the familiar typed creation helpers:

.. code:: python

    client.create_text(
        blogName,
        state='published',
        title='Testing',
        body='testing 1 2 3 4',
        tags=['testing'],
    )

    client.create_photo(
        blogName,
        state='queue',
        data='/path/to/image.jpg',
        caption='A photo',
    )

    client.create_quote(blogName, quote='I am the Walrus', source='Ringo')
    client.create_link(blogName, title='Search', url='https://duckduckgo.com')

Editing, reblogging and deleting
--------------------------------

.. code:: python

    client.edit_post(blogName, id=post_id, type='text', title='Updated')
    client.reblog(blogName, id=125356, reblog_key='reblog_key')
    client.delete_post(blogName, 123456)

Tagged posts
------------

.. code:: python

    client.tagged(tag, **params)

Interactive console
===================

For OAuth 1 setup, install the console dependencies and run:

.. code:: bash

    $ python interactive_console.py

For OAuth 2 use ``interactive_console2.py``.

Development and tests
=====================

The test suite uses pytest:

.. code-block:: bash

    $ python -m pip install -e . mock pytest
    $ python -m pytest -q

The modern public API also has an explicit documentation contract:

.. code-block:: bash

    $ python -m pytest -q tests/test_docs_contract.py

That contract checks runtime methods, type stubs, the public modern guide and a
no-network documented NPF creation flow. CI runs it before the full suite.

Copyright and license
=====================

Copyright 2013 Tumblr, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this work except in compliance with the License. You may obtain a copy of the
License file in this repository or at https://www.apache.org/licenses/LICENSE-2.0.

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.

.. |Build Status| image:: https://github.com/tumblr/pytumblr/actions/workflows/ci.yaml/badge.svg
   :target: https://github.com/tumblr/pytumblr/actions/workflows/ci.yaml
