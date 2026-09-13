"""Small, dependency-free helpers for working with Tumblr's NPF dictionaries."""


def _compact(mapping):
    return dict((key, value) for key, value in mapping.items() if value is not None)


def text_block(text, subtype=None, formatting=None):
    block = {"type": "text", "text": text}
    if subtype is not None:
        block["subtype"] = subtype
    if formatting is not None:
        block["formatting"] = formatting
    return block


def link_block(url, title=None, description=None, author=None, site_name=None):
    return _compact({
        "type": "link", "url": url, "title": title,
        "description": description, "author": author, "site_name": site_name,
    })


def _media_block(block_type, url=None, identifier=None, media_type=None,
                 width=None, height=None, alt_text=None):
    media = _compact({
        "url": url,
        "identifier": str(identifier) if identifier is not None else None,
        "type": media_type,
        "width": width,
        "height": height,
    })
    block = {"type": block_type, "media": [media]}
    if alt_text is not None:
        block["alt_text"] = alt_text
    return block


def image_block(url, media_type=None, width=None, height=None, alt_text=None):
    return _media_block("image", url=url, media_type=media_type,
                        width=width, height=height, alt_text=alt_text)


def image_upload_block(identifier, media_type="image/jpeg", alt_text=None):
    return _media_block("image", identifier=identifier, media_type=media_type,
                        alt_text=alt_text)


def audio_block(url, media_type=None):
    return _media_block("audio", url=url, media_type=media_type)


def audio_upload_block(identifier, media_type="audio/mpeg"):
    return _media_block("audio", identifier=identifier, media_type=media_type)


def video_block(url, media_type=None, width=None, height=None):
    return _media_block("video", url=url, media_type=media_type,
                        width=width, height=height)


def video_upload_block(identifier, media_type="video/mp4"):
    return _media_block("video", identifier=identifier, media_type=media_type)


def iter_blocks(post, include_trail=True):
    """Yield NPF content blocks from a post and, optionally, each trail item."""
    if not isinstance(post, dict):
        return
    for block in post.get("content", []) or []:
        if isinstance(block, dict):
            yield block
    if include_trail:
        for trail_item in post.get("trail", []) or []:
            if not isinstance(trail_item, dict):
                continue
            for block in trail_item.get("content", []) or []:
                if isinstance(block, dict):
                    yield block


def iter_media(post, media_types=None, include_trail=True):
    """Yield media objects from image/audio/video NPF blocks."""
    allowed = set(media_types) if media_types else None
    for block in iter_blocks(post, include_trail=include_trail):
        if block.get("type") not in ("image", "audio", "video"):
            continue
        media = block.get("media") or []
        if isinstance(media, dict):
            media = [media]
        for item in media:
            if not isinstance(item, dict):
                continue
            if allowed is None or block.get("type") in allowed:
                yield item


def iter_images(post, include_trail=True):
    for media in iter_media(post, media_types=("image",), include_trail=include_trail):
        yield media


def iter_text(post, include_trail=True):
    for block in iter_blocks(post, include_trail=include_trail):
        if block.get("type") == "text":
            yield block.get("text", "")


def root_post_reference(post):
    """Return ``(blog_name, post_id)`` for the root trail item, if available."""
    if not isinstance(post, dict):
        return None
    trail = post.get("trail") or []
    if not trail:
        return None
    root = trail[0]
    if not isinstance(root, dict):
        return None
    blog = root.get("blog") or {}
    post_ref = root.get("post") or {}
    blog_name = blog.get("name") if isinstance(blog, dict) else None
    if isinstance(post_ref, dict):
        post_id = post_ref.get("id") or post_ref.get("id_string")
    else:
        post_id = post_ref
    if blog_name and post_id:
        return blog_name, post_id
    return None
