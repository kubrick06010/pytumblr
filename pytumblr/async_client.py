"""Async facade for ModernTumblrRestClient.

The facade deliberately reuses the battle-tested synchronous transport in an
executor so OAuth1/OAuth2 signing, token refresh, multipart encoding and error
handling stay single-sourced.
"""

import asyncio
import functools

from .modern import ModernTumblrRestClient


class AsyncModernTumblrRestClient(object):
    def __init__(self, *args, **kwargs):
        self._client = ModernTumblrRestClient(*args, **kwargs)

    @property
    def sync_client(self):
        return self._client

    async def _call(self, method_name, *args, **kwargs):
        loop = asyncio.get_running_loop()
        func = functools.partial(getattr(self._client, method_name), *args, **kwargs)
        return await loop.run_in_executor(None, func)

    async def info(self):
        return await self._call("info")

    async def posts(self, blogname, **kwargs):
        return await self._call("posts", blogname, **kwargs)

    async def create_post(self, blogname, **kwargs):
        return await self._call("create_post", blogname, **kwargs)

    async def edit_post(self, blogname, id, **kwargs):
        return await self._call("edit_post", blogname, id, **kwargs)

    async def reblog_post(self, blogname, parent_blogname, id, **kwargs):
        return await self._call("reblog_post", blogname, parent_blogname, id, **kwargs)

    async def notifications(self, blogname, **kwargs):
        return await self._call("notifications", blogname, **kwargs)

    async def notes(self, blogname, id, **kwargs):
        return await self._call("notes", blogname, id, **kwargs)

    async def get_single_post(self, blogname, id, **kwargs):
        return await self._call("get_single_post", blogname, id, **kwargs)

    async def get_root_post(self, post):
        return await self._call("get_root_post", post)

    async def refresh_token(self):
        return await self._call("refresh_token")
