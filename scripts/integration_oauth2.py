#!/usr/bin/env python3
"""Opt-in OAuth2 integration smoke test for the modern PyTumblr client.

The test performs read-only checks and a reversible transaction against a
Tumblr blog. It creates temporary drafts, edits one, exercises follow/like
and creates a draft reblog. Every successful mutation is registered before
the next assertion and is reverted in ``finally``.

Required environment variables::

    TUMBLR_CONSUMER_KEY
    TUMBLR_CONSUMER_SECRET
    TUMBLR_ACCESS_TOKEN
    TUMBLR_REFRESH_TOKEN       (optional, needed only for refresh)
    TUMBLR_BLOG                (default: example.tumblr.com)

Run explicitly from the repository root; this script is not part of the
default test suite::

    python scripts/integration_oauth2.py

The OAuth2 token is read from the environment and is never printed.
"""

from __future__ import print_function

import json
import os
import random
import secrets
import sys


REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, REPOSITORY_ROOT)

from pytumblr import npf  # noqa: E402
from pytumblr.modern import ModernTumblrRestClient  # noqa: E402


def _required(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError("missing required environment variable: {}".format(name))
    return value


def _client():
    access_token = _required("TUMBLR_ACCESS_TOKEN")
    token = {
        "access_token": access_token,
        "token_type": os.environ.get("TUMBLR_TOKEN_TYPE", "bearer"),
    }
    refresh_token = os.environ.get("TUMBLR_REFRESH_TOKEN")
    if refresh_token:
        token["refresh_token"] = refresh_token

    return ModernTumblrRestClient(
        _required("TUMBLR_CONSUMER_KEY"),
        _required("TUMBLR_CONSUMER_SECRET"),
        client_id=_required("TUMBLR_CONSUMER_KEY"),
        oauth2_token=token,
    )


def _blog_name(post):
    return post.get("blog_name") or (post.get("blog") or {}).get("name")


def _post_id(response):
    post_id = response.get("id") if isinstance(response, dict) else None
    if not post_id:
        raise AssertionError("Tumblr response did not contain a post id")
    return post_id


def _all_following_names(client):
    names = set()
    offset = 0
    while True:
        blogs = client.following(limit=20, offset=offset).get("blogs", [])
        names.update(item.get("name") for item in blogs if item.get("name"))
        if len(blogs) < 20:
            return names
        offset += len(blogs)


def _all_liked_ids(client):
    return {str(post.get("id")) for post in client.iter_likes() if post.get("id")}


def _draft_snapshot(client, blog):
    drafts = client.drafts(blog).get("posts", [])
    return {
        str(post["id"]): json.dumps(post, ensure_ascii=False, sort_keys=True)
        for post in drafts
        if post.get("id")
    }


def _assert_drafts_restored(client, blog, initial_drafts, temporary_ids):
    current_drafts = _draft_snapshot(client, blog)
    assert set(current_drafts) == set(initial_drafts), (
        "draft IDs changed during integration test: expected {}, got {}".format(
            sorted(initial_drafts), sorted(current_drafts)
        )
    )
    for post_id, initial_json in initial_drafts.items():
        assert current_drafts[post_id] == initial_json, (
            "pre-existing draft {} was modified".format(post_id)
        )
    assert not set(temporary_ids) & set(current_drafts), "temporary draft still exists"

    for post_id in temporary_ids:
        assert client.get_single_post(blog, post_id) is None, (
            "temporary post {} still exists".format(post_id)
        )


def _choose_candidates(client, blog):
    following_names = _all_following_names(client)

    tagged_posts = client.tagged("music", limit=30)
    follow_candidates = []
    for post in tagged_posts:
        name = _blog_name(post)
        if name and name not in following_names and name != blog:
            if name not in follow_candidates:
                follow_candidates.append(name)

    dashboard_posts = client.dashboard(limit=30).get("posts", [])
    like_candidates = [
        post
        for post in dashboard_posts
        if post.get("id")
        and post.get("reblog_key")
        and post.get("liked") is False
        and post.get("can_like", True)
    ]
    reblog_candidates = [
        post
        for post in dashboard_posts
        if post.get("id")
        and post.get("reblog_key")
        and post.get("can_reblog", True)
    ]

    assert follow_candidates, "could not find an un-followed blog candidate"
    assert like_candidates, "could not find an un-liked dashboard post"
    assert reblog_candidates, "could not find a rebloggable dashboard post"

    chooser = random.SystemRandom()
    return (
        chooser.choice(follow_candidates),
        chooser.choice(like_candidates),
        chooser.choice(reblog_candidates),
    )


def run():
    blog = os.environ.get("TUMBLR_BLOG", "example.tumblr.com")
    client = _client()

    # Read-only smoke assertions.
    assert client.info().get("user") is not None
    assert client.blog_info(blog).get("blog", {}).get("name")
    assert isinstance(client.posts(blog, limit=1).get("posts"), list)
    assert isinstance(client.dashboard(limit=1).get("posts"), list)
    assert isinstance(client.likes(limit=1).get("liked_posts"), list)
    assert isinstance(client.following(limit=1).get("blogs"), list)
    assert isinstance(client.followers(blog, limit=1).get("users"), list)
    assert isinstance(client.queue(blog).get("posts"), list)
    assert isinstance(client.drafts(blog).get("posts"), list)
    assert isinstance(client.submission(blog).get("posts"), list)
    assert isinstance(client.notifications(blog).get("notifications"), list)

    initial_drafts = _draft_snapshot(client, blog)
    follow_target, like_target, reblog_target = _choose_candidates(client, blog)
    marker = "modern-pytumblr-oauth2-{}".format(secrets.token_hex(6))

    temporary_ids = []
    follow_applied = False
    like_applied = False
    reblog_id = None
    cleanup_errors = []
    results = []

    try:
        for name, create in (
            ("text", lambda: client.create_text(blog, body=marker + " text", state="draft")),
            (
                "link",
                lambda: client.create_link(
                    blog, url="https://example.com/", title=marker + " link", state="draft"
                ),
            ),
            (
                "quote",
                lambda: client.create_quote(
                    blog, quote=marker + " quote", source="integration", state="draft"
                ),
            ),
            (
                "chat",
                lambda: client.create_chat(
                    blog, title=marker + " chat", conversation="integration", state="draft"
                ),
            ),
        ):
            post_id = _post_id(create())
            temporary_ids.append(post_id)
            results.append("create_{}".format(name))

        edited_id = temporary_ids[0]
        edited = client.edit_post(
            blog,
            id=edited_id,
            content=[npf.text_block(marker + " edited")],
            state="draft",
        )
        assert edited is not None
        results.append("edit_post")

        client.follow(follow_target)
        follow_applied = True
        assert follow_target in _all_following_names(client)
        results.append("follow")

        client.like(like_target["id"], like_target["reblog_key"])
        like_applied = True
        liked_post = client.get_single_post(_blog_name(like_target), like_target["id"])
        assert liked_post is not None and liked_post.get("liked") is True
        results.append("like")

        parent_blog = _blog_name(reblog_target)
        reblog_response = client.reblog_post(
            blog,
            parent_blog,
            reblog_target["id"],
            reblog_key=reblog_target["reblog_key"],
            content=[],
            state="draft",
        )
        reblog_id = _post_id(reblog_response)
        temporary_ids.append(reblog_id)
        results.append("reblog_draft")
    finally:
        for post_id in reversed(temporary_ids):
            try:
                client.delete_post(blog, post_id)
            except Exception as error:  # pragma: no cover - production cleanup
                cleanup_errors.append("delete {}: {}".format(post_id, error))

        if like_applied:
            try:
                client.unlike(like_target["id"], like_target["reblog_key"])
            except Exception as error:  # pragma: no cover - production cleanup
                cleanup_errors.append("unlike: {}".format(error))

        if follow_applied:
            try:
                client.unfollow(follow_target)
            except Exception as error:  # pragma: no cover - production cleanup
                cleanup_errors.append("unfollow: {}".format(error))

        try:
            assert follow_target not in _all_following_names(client), (
                "follow target remains followed after cleanup"
            )
            assert str(like_target["id"]) not in _all_liked_ids(client), (
                "like target remains liked after cleanup"
            )
            _assert_drafts_restored(client, blog, initial_drafts, temporary_ids)
        except Exception as error:  # pragma: no cover - production cleanup
            cleanup_errors.append("verify restored state: {}".format(error))

    if cleanup_errors:
        raise RuntimeError("cleanup failed: {}".format("; ".join(cleanup_errors)))

    print(json.dumps({"blog": blog, "passed": results, "cleanup": "complete"}, sort_keys=True))


if __name__ == "__main__":
    run()
