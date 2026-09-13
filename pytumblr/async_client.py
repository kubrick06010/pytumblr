"""Async facade for ModernTumblrRestClient.

Methods return asyncio Futures, so on Python 3 they can be awaited directly:
``await client.create_post(...)``. The module keeps Python-2-compatible syntax
so adding it does not make the historical package unparseable on old runtimes.
"""

import functools

from .modern import ModernTumblrRestClient


class AsyncModernTumblrRestClient(object):
    def __init__(self, *args, **kwargs):
        self._client = ModernTumblrRestClient(*args, **kwargs)

    @property
    def sync_client(self):
        return self._client

    def _call(self, method_name, *args, **kwargs):
        try:
            import asyncio
        except ImportError:
            raise RuntimeError("async client requires Python 3 with asyncio")
        try:
            loop = asyncio.get_running_loop()
        except AttributeError:
            loop = asyncio.get_event_loop()
        func = functools.partial(getattr(self._client, method_name), *args, **kwargs)
        return loop.run_in_executor(None, func)

    def info(self):
        return self._call("info")

    def posts(self, blogname, **kwargs):
        return self._call("posts", blogname, **kwargs)

    def create_post(self, blogname, **kwargs):
        return self._call("create_post", blogname, **kwargs)

    def edit_post(self, blogname, id, **kwargs):
        return self._call("edit_post", blogname, id, **kwargs)

    def reblog_post(self, blogname, parent_blogname, id, **kwargs):
        return self._call("reblog_post", blogname, parent_blogname, id, **kwargs)

    def notifications(self, blogname, **kwargs):
        return self._call("notifications", blogname, **kwargs)

    def notes(self, blogname, id, **kwargs):
        return self._call("notes", blogname, id, **kwargs)

    def get_single_post(self, blogname, id, **kwargs):
        return self._call("get_single_post", blogname, id, **kwargs)

    def get_root_post(self, post):
        return self._call("get_root_post", post)

    def refresh_token(self):
        return self._call("refresh_token")
