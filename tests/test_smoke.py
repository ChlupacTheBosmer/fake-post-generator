"""Smoke tests that don't actually run a browser.

These verify wiring (registry, templates, context, validation) without
rendering pixels. End-to-end pixel checks live in examples/.
"""

from __future__ import annotations

import pytest

from fake_post_generator import (
    AccountProfile,
    LayoutConfig,
    RedditPost,
    TwitterPost,
    account_bank,
    available_platforms,
    build_replies,
    get_platform,
)


def _acc(handle="x", name=None):
    return AccountProfile(id=handle, name=name or handle, handle=handle)


def test_platforms_registered():
    assert "twitter" in available_platforms()
    assert "reddit" in available_platforms()


def test_twitter_full_html_renders():
    plat = get_platform("twitter", renderer=_FakeRenderer())
    out = plat.render(
        TwitterPost(text="hello", account=_acc(), likes=10),
        variant="full",
        layout=LayoutConfig(theme="dim"),
    )
    assert b"hello" in out


def test_twitter_reply_renders_standalone():
    plat = get_platform("twitter", renderer=_FakeRenderer())
    out = plat.render(
        TwitterPost(text="standalone reply", account=_acc("alice"), likes=99),
        variant="reply",
    )
    assert b"standalone reply" in out
    assert b"@alice" in out


def test_twitter_thread_nested_renders():
    plat = get_platform("twitter", renderer=_FakeRenderer())
    post = TwitterPost(
        text="parent",
        account=_acc("alice"),
        replies=[TwitterPost(text="child", account=_acc("bob"))],
    )
    out = plat.render(post, variant="thread_nested")
    assert b"parent" in out and b"child" in out


def test_reddit_full_renders():
    plat = get_platform("reddit", renderer=_FakeRenderer())
    out = plat.render(
        RedditPost(title="t", body="b", subreddit="r/x", account=_acc("u")),
        variant="full",
    )
    assert b"u/u" in out


def test_reddit_full_requires_title():
    plat = get_platform("reddit", renderer=_FakeRenderer())
    with pytest.raises(ValueError, match="requires a title"):
        plat.render(RedditPost(body="just a comment", account=_acc()), variant="full")


def test_reddit_comment_rejects_title():
    plat = get_platform("reddit", renderer=_FakeRenderer())
    with pytest.raises(ValueError, match="title=None"):
        plat.render(
            RedditPost(title="not a comment", body="b", account=_acc()),
            variant="comment",
        )


def test_reddit_thread_nested_renders_comments():
    plat = get_platform("reddit", renderer=_FakeRenderer())
    post = RedditPost(
        title="ask me anything",
        body="post body",
        subreddit="r/x",
        account=_acc("op"),
        replies=[
            RedditPost(body="top reply", account=_acc("alice"), op=True),
            RedditPost(
                body="other reply",
                account=_acc("bob"),
                replies=[RedditPost(body="nested", account=_acc("carol"))],
            ),
        ],
    )
    out = plat.render(post, variant="thread_nested")
    for needle in (b"ask me anything", b"top reply", b"other reply", b"nested"):
        assert needle in out


def test_unknown_variant_raises():
    plat = get_platform("twitter", renderer=_FakeRenderer())
    with pytest.raises(ValueError, match="nope"):
        plat.render(TwitterPost(text="hi", account=_acc()), variant="nope")


def test_account_bank_default_pool_picks():
    bank = account_bank(seed=42)
    a = bank.pick()
    assert a.handle and a.name and a.avatar  # bundled fallback fills all three


def test_build_replies_for_reddit_uses_user_text():
    bank = account_bank(seed=42)
    replies = build_replies(
        ["one", {"text": "two", "upvotes": 99}],
        model_cls=RedditPost,
        bank=bank,
        seed=42,
    )
    assert [r.body for r in replies] == ["one", "two"]
    assert replies[1].upvotes == 99


class _FakeRenderer:
    def render_element(self, html, selector, **_):
        return html.encode()
