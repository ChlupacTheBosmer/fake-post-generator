"""Reddit `Variant` subclasses + the shared context-building helpers.

All variants share :func:`_post_context`, which auto-loads
``subreddits.yaml`` and exposes the resolved palette, avatar URIs, flair
colors, and the recursive ``avatar_for`` helper used by the comment macro.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from ...core.avatar import to_data_uri
from ...core.layout import LayoutConfig
from ...core.subreddit import load_subreddits
from ...core.variant import Variant
from .icons import icon_svg
from .themes import FLAIR_COLORS, THEMES

DEFAULT_AVATAR = Path(__file__).parent / "assets" / "default_avatar.png"
DEFAULT_SUBREDDIT_ICON = DEFAULT_AVATAR  # the snoo doubles as subreddit fallback


# ----- helpers --------------------------------------------------------------

def _resolve_background(layout: LayoutConfig, card_bg: str) -> str:
    """Map ``layout.background`` to a concrete CSS color string.

    ``"theme"`` echoes the card's bg color (no halo). ``"transparent"``
    stays literal. Anything else is passed through verbatim.
    """
    if layout.background == "theme":
        return card_bg
    if layout.background == "transparent":
        return "transparent"
    return layout.background


def _resolve_border(layout: LayoutConfig) -> bool:
    """Decide whether the card should draw a 1-px border.

    Explicit ``layout.border`` wins; otherwise the border is on by default
    and turned off when the page background is ``"transparent"``.
    """
    if layout.border is not None:
        return layout.border
    return layout.background != "transparent"


def _flair_colors(flair: str | None, palette) -> tuple[str, str]:
    """Look up ``(bg, text)`` for a flair label.

    Case-insensitive lookup against :data:`FLAIR_COLORS`. Unknown flairs
    fall back to the theme's neutral flair palette.
    """
    if not flair:
        return palette.flair_bg, palette.flair_text
    return FLAIR_COLORS.get(flair.strip().lower(), (palette.flair_bg, palette.flair_text))


def _avatar_uri(account):
    """Return the data-URI for an account's avatar (bundled fallback if None)."""
    src = account.avatar or str(DEFAULT_AVATAR)
    return to_data_uri(src, size=200)


def _resolved_subreddit(post):
    """Merge the post's per-instance fields with any matching entry in the
    auto-loaded subreddits.yaml. Per-post fields always win; the YAML only
    fills in what's missing.
    """
    if not post.subreddit:
        return None
    cfg = load_subreddits().get(post.subreddit)
    if cfg is None:
        return None
    return cfg


def _sub_icon_uri(post, sub_cfg):
    """Resolve the subreddit-icon source: per-post → YAML config → bundled snoo."""
    src = post.subreddit_icon or (sub_cfg.icon if sub_cfg else None) or str(
        DEFAULT_SUBREDDIT_ICON
    )
    return to_data_uri(src, size=200)


def _post_context(post: Any, layout: LayoutConfig) -> dict[str, Any]:
    """Build the full Jinja context dict shared by all Reddit variants.

    Auto-resolves the subreddit config, flair colors, avatars (post + each
    nested commenter), background, and border. Variant-specific extras
    (e.g. ``flat_comments``) are added by individual variants on top.
    """
    palette = THEMES[layout.theme]
    flair_bg, flair_text = _flair_colors(post.flair, palette)
    sub_cfg = _resolved_subreddit(post)
    members = post.subreddit_members or (sub_cfg.members if sub_cfg else None)
    description = post.subreddit_description or (
        sub_cfg.description if sub_cfg else None
    )
    return {
        "post": post,
        "palette": palette,
        "avatar_uri": _avatar_uri(post.account),
        "sub_icon_uri": _sub_icon_uri(post, sub_cfg),
        "sub_members": members,
        "sub_description": description,
        "page_bg": _resolve_background(layout, palette.bg),
        "show_border": _resolve_border(layout),
        "flair_bg": flair_bg,
        "flair_text": flair_text,
        "icon": icon_svg,
        "layout": layout,
        "avatar_for": _avatar_uri,
    }


def _require_title(post, variant_name):
    """Raise ``ValueError`` if a post-style variant got a comment-shaped post."""
    if not post.title:
        raise ValueError(
            f"reddit variant {variant_name!r} requires a title; got "
            f"title={post.title!r}. Use the 'comment' / 'comment_compact' "
            f"variants for comments."
        )


def _require_no_title(post, variant_name):
    """Raise ``ValueError`` if a comment variant got a title-bearing post."""
    if post.title:
        raise ValueError(
            f"reddit variant {variant_name!r} expects a comment (title=None); "
            f"got title={post.title!r}. Use 'full' / 'thread' for posts."
        )


# ----- variants -------------------------------------------------------------

class FullVariant(Variant):
    """Feed-card view — how a post appears in a subreddit feed.

    Subreddit name + author + title + (optional flair / body / image) +
    action bar. Requires ``post.title``; raises ``ValueError`` otherwise.
    """

    name = "full"
    template = "full.html.j2"

    def context(self, post, layout):
        _require_title(post, self.name)
        return _post_context(post, layout)


class CompactVariant(Variant):
    """Minimal feed card — subreddit + author + title + body. No flair,
    no action bar. Requires ``post.title``."""

    name = "compact"
    template = "compact.html.j2"

    def context(self, post, layout):
        _require_title(post, self.name)
        return _post_context(post, layout)


class BadgeVariant(Variant):
    """Circular avatar + display name + ``u/handle``. No subreddit chrome.
    Defaults to a transparent background for compositing."""

    name = "badge"
    template = "badge.html.j2"

    def context(self, post, layout):
        ctx = _post_context(post, layout)
        if layout.background == "theme":
            ctx["page_bg"] = "transparent"
        return ctx


class ThreadVariant(Variant):
    """Single-post detail page — the view you see when you click a post.

    Wider layout, larger title, separate subreddit row + author row, plus
    Join pill and members/description from the auto-loaded
    :mod:`...core.subreddit` config. No comments. Requires ``post.title``.
    """

    name = "thread"
    template = "thread.html.j2"

    def context(self, post, layout):
        _require_title(post, self.name)
        return _post_context(post, layout)


class CommentVariant(Variant):
    """A single standalone comment — no surrounding post.

    Useful when you want to extract one reply on its own (for a quote /
    callout). No vertical thread line, no indent. Requires ``title=None``
    (raises ``ValueError`` if a title is supplied)."""

    name = "comment"
    template = "comment.html.j2"

    def context(self, post, layout):
        _require_no_title(post, self.name)
        return _post_context(post, layout)


class CommentCompactVariant(Variant):
    """Smallest possible comment — avatar + author + body + score, no action
    bar. Requires ``title=None``."""

    name = "comment_compact"
    template = "comment_compact.html.j2"

    def context(self, post, layout):
        _require_no_title(post, self.name)
        return _post_context(post, layout)


class ThreadNestedVariant(Variant):
    """Thread detail page + recursive nested comment tree.

    Each comment renders its replies underneath, indented with a colored
    vertical thread line. Cuts off at ``LayoutConfig.max_nesting_depth``
    with a "Continue this thread →" link. Requires ``post.title``.
    """

    name = "thread_nested"
    template = "thread_nested.html.j2"

    def context(self, post, layout):
        _require_title(post, self.name)
        return _post_context(post, layout)


class ThreadFlatVariant(Variant):
    """Thread detail page + flat list of all comments (descendants
    flattened in pre-order). Requires ``post.title``."""

    name = "thread_flat"
    template = "thread_flat.html.j2"

    def context(self, post, layout):
        _require_title(post, self.name)
        ctx = _post_context(post, layout)
        # Pre-flatten the reply tree for the template.
        ctx["flat_comments"] = list(_walk(post.replies))
        return ctx


def _walk(replies):
    """Pre-order walk yielding shallow copies (with ``replies=[]``) so the
    recursive macro renders each one once and doesn't re-nest a flat list."""
    for r in replies or ():
        yield dataclasses.replace(r, replies=[])
        yield from _walk(r.replies)
