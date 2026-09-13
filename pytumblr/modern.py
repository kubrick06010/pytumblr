"""Modern Tumblr API helpers built on top of the backwards-compatible client."""

import mimetypes

from . import TumblrRestClient
from .helpers import validate_blogname
from . import npf


class ModernTumblrRestClient(TumblrRestClient):
    """PyTumblr client with first-class Neue Post Format helpers."""

    _NPF_OPTIONS = {
        "content", "layout", "state", "tags", "date", "publish_on",
        "slug", "source_url", "send_to_twitter", "is_private",
        "interactability_reblog", "parent_tumblelog_uuid", "parent_post_id",
        "reblog_key", "hide_trail", "exclude_trail_items", "media_sources"
    }

    def __init__(self, *args, **kwargs):
        self.consume_in_npf_by_default = kwargs.pop("consume_in_npf_by_default", True)
        super(ModernTumblrRestClient, self).__init__(*args, **kwargs)
        self._reblog_requirements_cache = {}

    def npf_consumption_on(self):
        self.consume_in_npf_by_default = True

    def npf_consumption_off(self):
        self.consume_in_npf_by_default = False

    @staticmethod
    def _validate_npf_payload(payload, require_content=False):
        unknown = set(payload) - ModernTumblrRestClient._NPF_OPTIONS
        if unknown:
            raise ValueError("Unknown NPF option(s): {}".format(", ".join(sorted(unknown))))
        content = payload.get("content")
        if require_content and (not isinstance(content, list) or not content):
            raise ValueError("content must be a non-empty list of NPF blocks")
        if content is not None and not isinstance(content, list):
            raise ValueError("content must be a list when provided")
        layout = payload.get("layout")
        if layout is not None and not isinstance(layout, list):
            raise ValueError("layout must be a list when provided")
        tags = payload.get("tags")
        if tags is not None and not isinstance(tags, (list, str)):
            raise ValueError("tags must be a list or comma-separated string")
        media_sources = payload.get("media_sources")
        if media_sources is not None and not isinstance(media_sources, dict):
            raise ValueError("media_sources must be a dict of identifier -> path/file")

    @staticmethod
    def _legacy_common(kwargs):
        result = dict(kwargs)
        result.pop("tweet", None)
        result.pop("format", None)
        result.pop("photoset_layout", None)
        return result

    @validate_blogname
    def posts(self, blogname, type=None, **kwargs):
        kwargs.setdefault("npf", self.consume_in_npf_by_default)
        return super(ModernTumblrRestClient, self).posts(blogname, type=type, **kwargs)

    @validate_blogname
    def queue(self, blogname, **kwargs):
        kwargs.setdefault("npf", self.consume_in_npf_by_default)
        return super(ModernTumblrRestClient, self).queue(blogname, **kwargs)

    @validate_blogname
    def drafts(self, blogname, **kwargs):
        kwargs.setdefault("npf", self.consume_in_npf_by_default)
        return super(ModernTumblrRestClient, self).drafts(blogname, **kwargs)

    @validate_blogname
    def submission(self, blogname, **kwargs):
        kwargs.setdefault("npf", self.consume_in_npf_by_default)
        return super(ModernTumblrRestClient, self).submission(blogname, **kwargs)

    @validate_blogname
    def create_post(self, blogname, **kwargs):
        kwargs.setdefault("state", "published")
        self._validate_npf_payload(kwargs, require_content=True)
        payload = dict(kwargs)
        if isinstance(payload.get("tags"), list):
            payload["tags"] = ",".join(payload["tags"])
        media_sources = payload.pop("media_sources", None)
        return self.request.post_npf(
            "/v2/blog/{}/posts".format(blogname), payload, media_sources
        )

    @validate_blogname
    def edit_post(self, blogname, id, **kwargs):
        self._validate_npf_payload(kwargs)
        if not kwargs:
            raise ValueError("at least one NPF field must be provided")
        payload = dict(kwargs)
        if isinstance(payload.get("tags"), list):
            payload["tags"] = ",".join(payload["tags"])
        media_sources = payload.pop("media_sources", None)
        return self.request.put_npf(
            "/v2/blog/{}/posts/{}".format(blogname, id), payload, media_sources
        )

    @validate_blogname
    def notifications(self, blogname, **kwargs):
        return self.send_api_request(
            "get", "/v2/blog/{}/notifications".format(blogname), kwargs,
            ["before", "types", "type"]
        )

    @validate_blogname
    def notes(self, blogname, id, **kwargs):
        params = dict(kwargs)
        params["id"] = id
        return self.send_api_request(
            "get", "/v2/blog/{}/notes".format(blogname), params,
            ["id", "mode", "before_timestamp"]
        )

    @validate_blogname
    def get_single_post(self, blogname, id, **kwargs):
        params = dict(kwargs)
        params["id"] = id
        params.setdefault("npf", self.consume_in_npf_by_default)
        response = self.posts(blogname, **params)
        posts = response.get("posts", []) if isinstance(response, dict) else []
        return posts[0] if posts else None

    @validate_blogname
    def reblog_post(self, blogname, parent_blogname, id,
                    parent_blog_uuid=None, reblog_key=None, **kwargs):
        cache_key = (parent_blogname, str(id))
        if parent_blog_uuid is None or reblog_key is None:
            cached = self._reblog_requirements_cache.get(cache_key)
            if cached is None:
                parent = self.get_single_post(parent_blogname, id)
                if not parent:
                    raise ValueError("parent post could not be resolved")
                blog = parent.get("blog", {}) if isinstance(parent, dict) else {}
                parent_blog_uuid = parent_blog_uuid or blog.get("uuid") or parent.get("blog_uuid")
                reblog_key = reblog_key or parent.get("reblog_key")
                if not parent_blog_uuid or not reblog_key:
                    raise ValueError("parent post lacks UUID or reblog_key")
                cached = (parent_blog_uuid, reblog_key)
                self._reblog_requirements_cache[cache_key] = cached
            parent_blog_uuid = parent_blog_uuid or cached[0]
            reblog_key = reblog_key or cached[1]
        kwargs.setdefault("content", [])
        kwargs.update({
            "parent_tumblelog_uuid": parent_blog_uuid,
            "parent_post_id": str(id),
            "reblog_key": reblog_key,
        })
        self._validate_npf_payload(kwargs, require_content=False)
        payload = dict(kwargs)
        media_sources = payload.pop("media_sources", None)
        return self.request.post_npf(
            "/v2/blog/{}/posts".format(blogname), payload, media_sources
        )

    def _iter_collection(self, fetch, response_key, page_size=20, max_items=None, **kwargs):
        offset = int(kwargs.pop("offset", 0))
        yielded = 0
        while True:
            params = dict(kwargs)
            params["limit"] = min(page_size, 20)
            params["offset"] = offset
            response = fetch(**params)
            items = response.get(response_key, []) if isinstance(response, dict) else []
            if not items:
                return
            for item in items:
                yield item
                yielded += 1
                if max_items is not None and yielded >= max_items:
                    return
            if len(items) < params["limit"]:
                return
            offset += len(items)

    @validate_blogname
    def iter_posts(self, blogname, max_items=None, **kwargs):
        for item in self._iter_collection(
                lambda **params: self.posts(blogname, **params),
                "posts", max_items=max_items, **kwargs):
            yield item

    @validate_blogname
    def iter_queue(self, blogname, max_items=None, **kwargs):
        for item in self._iter_collection(
                lambda **params: self.queue(blogname, **params),
                "posts", max_items=max_items, **kwargs):
            yield item

    def iter_likes(self, max_items=None, **kwargs):
        for item in self._iter_collection(
                self.likes, "liked_posts", max_items=max_items, **kwargs):
            yield item

    def get_root_post(self, post):
        reference = npf.root_post_reference(post)
        if reference is None:
            return post
        blogname, post_id = reference
        resolved = self.get_single_post(blogname, post_id)
        return resolved or post

    @validate_blogname
    def create_text(self, blogname, **kwargs):
        kwargs = self._legacy_common(kwargs)
        title = kwargs.pop("title", None)
        body = kwargs.pop("body", "")
        content = []
        if title:
            content.append(npf.text_block(title, subtype="heading1"))
        content.append(npf.text_block(body))
        kwargs["content"] = content
        return self.create_post(blogname, **kwargs)

    @validate_blogname
    def create_link(self, blogname, **kwargs):
        kwargs = self._legacy_common(kwargs)
        url = kwargs.pop("url")
        title = kwargs.pop("title", None)
        description = kwargs.pop("description", None)
        kwargs.pop("thumbnail", None)
        kwargs["content"] = [npf.link_block(url, title=title, description=description)]
        return self.create_post(blogname, **kwargs)

    @validate_blogname
    def create_quote(self, blogname, **kwargs):
        kwargs = self._legacy_common(kwargs)
        quote = kwargs.pop("quote")
        source = kwargs.pop("source", None)
        content = [npf.text_block(quote, subtype="quote")]
        if source:
            content.append(npf.text_block(source))
        kwargs["content"] = content
        return self.create_post(blogname, **kwargs)

    @validate_blogname
    def create_chat(self, blogname, **kwargs):
        kwargs = self._legacy_common(kwargs)
        title = kwargs.pop("title", None)
        conversation = kwargs.pop("conversation", "")
        content = []
        if title:
            content.append(npf.text_block(title, subtype="heading1"))
        content.append(npf.text_block(conversation, subtype="chat"))
        kwargs["content"] = content
        return self.create_post(blogname, **kwargs)

    @validate_blogname
    def create_photo(self, blogname, **kwargs):
        kwargs = self._legacy_common(kwargs)
        source = kwargs.pop("source", None)
        data = kwargs.pop("data", None)
        caption = kwargs.pop("caption", None)
        kwargs.pop("link", None)
        content = []
        media_sources = {}
        if source:
            content.append(npf.image_block(url=source))
        elif data:
            paths = data if isinstance(data, list) else [data]
            for index, path in enumerate(paths):
                identifier = "media{}".format(index)
                media_type = mimetypes.guess_type(str(path))[0]
                content.append(npf.image_upload_block(identifier, media_type=media_type))
                media_sources[identifier] = path
        else:
            raise ValueError("create_photo requires source or data")
        if caption:
            content.append(npf.text_block(caption))
        kwargs["content"] = content
        if media_sources:
            kwargs["media_sources"] = media_sources
        return self.create_post(blogname, **kwargs)

    @validate_blogname
    def create_audio(self, blogname, **kwargs):
        kwargs = self._legacy_common(kwargs)
        external_url = kwargs.pop("external_url", None)
        data = kwargs.pop("data", None)
        caption = kwargs.pop("caption", None)
        provider = kwargs.pop("provider", None)
        content = []
        if external_url:
            content.append(npf.audio_block(external_url, provider=provider))
        elif data:
            media_type = mimetypes.guess_type(str(data))[0]
            content.append(npf.audio_upload_block("media0", media_type=media_type))
            kwargs["media_sources"] = {"media0": data}
        else:
            raise ValueError("create_audio requires external_url or data")
        if caption:
            content.append(npf.text_block(caption))
        kwargs["content"] = content
        return self.create_post(blogname, **kwargs)

    @validate_blogname
    def create_video(self, blogname, **kwargs):
        kwargs = self._legacy_common(kwargs)
        data = kwargs.pop("data", None)
        embed = kwargs.pop("embed", None)
        caption = kwargs.pop("caption", None)
        content = []
        if data:
            content.append(npf.video_upload_block("media0"))
            kwargs["media_sources"] = {"media0": data}
        elif embed:
            content.append(npf.text_block(embed))
        else:
            raise ValueError("create_video requires data or embed")
        if caption:
            content.append(npf.text_block(caption))
        kwargs["content"] = content
        return self.create_post(blogname, **kwargs)
