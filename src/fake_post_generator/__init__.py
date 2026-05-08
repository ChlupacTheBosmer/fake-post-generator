"""fake_post_generator — accurate fake social-media post images.

A modular, plugin-based Python package that renders pixel-faithful Twitter/X
and Reddit post images from structured data, with deep customization of
themes, layouts, accounts, comments, and threading.

Quick example
=============

    from fake_post_generator import (
        AccountProfile, LayoutConfig, TwitterPost,
    )

    acc = AccountProfile(
        id="elon", name="Elon Musk", handle="elonmusk", verified="blue",
    )
    png = TwitterPost(
        text="hello world",
        account=acc,
        likes=12345, retweets=234, replies_count=42, views=1_200_000,
    ).render(
        variant="full",
        layout=LayoutConfig(theme="dim", background="transparent", scale=2),
    )
    open("tweet.png", "wb").write(png)

See ``docs/`` for full guides:
- ``docs/USAGE.md``      — comprehensive user guide
- ``docs/CLI.md``        — CLI reference
- ``docs/ARCHITECTURE.md`` — package layout + render pipeline
- ``docs/AGENTS.md``     — context dump for AI agents working with this code
- ``docs/DECISIONS.md``  — design rationale
"""

from .core import (
    AccountProfile,
    LayoutConfig,
    Platform,
    PlaywrightRenderer,
    Renderer,
    Variant,
    available_platforms,
    get_platform,
    load_accounts,
    register,
    to_circular_avatar,
    to_data_uri,
)
from .core.bank import AccountBank, ReplyTemplate, account_bank, build_replies
from .core.subreddit import SubredditConfig, load_subreddits
from .platforms.reddit import RedditPost
from .platforms.twitter import TwitterPost

__all__ = [
    "AccountBank",
    "AccountProfile",
    "LayoutConfig",
    "Platform",
    "PlaywrightRenderer",
    "RedditPost",
    "Renderer",
    "ReplyTemplate",
    "SubredditConfig",
    "TwitterPost",
    "Variant",
    "account_bank",
    "available_platforms",
    "build_replies",
    "get_platform",
    "load_accounts",
    "load_subreddits",
    "register",
    "to_circular_avatar",
    "to_data_uri",
]
