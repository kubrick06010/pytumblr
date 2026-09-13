"""Modern Tumblr API helpers built on top of the backwards-compatible client."""

from . import TumblrRestClient
from .helpers import validate_blogname


class ModernTumblrRestClient(TumblrRestClient):
    """PyTumblr client with first-class Neue Post Format helpers.

    This class intentionally starts with raw NPF dictionaries. Typed block
    helpers can be layered on later without constraining the wire format.
    """

    _NPF_OPTIONS = {
        "content", "layout", "state", "tags", "date", "publish_on",
        "slug", "source_url", "send_to_twitter"
    }

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

    @validate_blogname
    def create_post(self, blogname, **kwargs):
        """Create a post through Tumblr's modern NPF endpoint."""
        self._validate_npf_payload(kwargs, require_content=True)
        return self.request.post_json(
            "/v2/blog/{}/posts".format(blogname), kwargs
        )

    @validate_blogname
    def edit_post(self, blogname, id, **kwargs):
        """Edit a post through Tumblr's modern NPF endpoint."""
        self._validate_npf_payload(kwargs)
        if not kwargs:
            raise ValueError("at least one NPF field must be provided")
        return self.request.put_json(
            "/v2/blog/{}/posts/{}".format(blogname, id), kwargs
        )
