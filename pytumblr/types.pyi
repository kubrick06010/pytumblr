from typing import Any, Dict, List, Optional, TypedDict

class MediaObject(TypedDict, total=False):
    url: str
    type: str
    width: int
    height: int
    identifier: str

class ContentBlock(TypedDict, total=False):
    type: str
    text: str
    subtype: str
    media: List[MediaObject]
    url: str
    title: str
    description: str

class LayoutBlock(TypedDict, total=False):
    type: str
    blocks: List[int]
    display: List[Dict[str, Any]]

class Blog(TypedDict, total=False):
    name: str
    uuid: str
    title: str
    url: str
    description: str
    posts: int

class TrailItem(TypedDict, total=False):
    blog: Blog
    post: Dict[str, Any]
    content: List[ContentBlock]
    is_root_item: bool

class Post(TypedDict, total=False):
    id: int
    id_string: str
    blog_name: str
    blog: Blog
    post_url: str
    short_url: str
    timestamp: int
    date: str
    state: str
    tags: List[str]
    note_count: int
    reblog_key: str
    content: List[ContentBlock]
    layout: List[LayoutBlock]
    trail: List[TrailItem]
