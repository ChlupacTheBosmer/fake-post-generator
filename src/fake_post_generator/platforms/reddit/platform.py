"""Reddit platform plugin."""

from __future__ import annotations

from ...core.platform import Platform
from ...core.registry import register
from ...core.variant import Variant
from .variants import (
    BadgeVariant,
    CommentCompactVariant,
    CommentVariant,
    CompactVariant,
    FullVariant,
    ThreadFlatVariant,
    ThreadNestedVariant,
    ThreadVariant,
)


@register
class RedditPlatform(Platform):
    """Reddit renderer.

    Themes: ``light``, ``dark``. Variants:

    - ``full``           — feed-card view (the post as it appears in a list)
    - ``compact``        — minimal feed card (no actions/flair)
    - ``badge``          — circular avatar + display name + ``u/handle``
    - ``thread``         — single-post detail page (no comments)
    - ``comment``        — standalone single comment (no thread line)
    - ``comment_compact``— minimal comment (avatar + author + body + score)
    - ``thread_nested``  — thread page + nested comment tree
    - ``thread_flat``    — thread page + flat comment list (no indentation)

    Subreddit visual config (icon / members / description) is auto-loaded
    from a ``subreddits.yaml`` next to the project (see :mod:`...core.subreddit`).
    """

    name = "reddit"
    themes = ("light", "dark")
    default_theme = "light"

    def variants(self) -> dict[str, Variant]:
        """Return the eight Reddit variants keyed by name."""
        return {
            "full": FullVariant(),
            "compact": CompactVariant(),
            "badge": BadgeVariant(),
            "thread": ThreadVariant(),
            "comment": CommentVariant(),
            "comment_compact": CommentCompactVariant(),
            "thread_nested": ThreadNestedVariant(),
            "thread_flat": ThreadFlatVariant(),
        }
