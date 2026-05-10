"""Twitter `Variant` subclasses + the shared context-building helpers.

All variants share :func:`_common_context`, which exposes the resolved
palette, avatar URIs, verified-badge HTML, and the ``avatar_for`` /
``verified_for`` helpers used by the recursive reply macro.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from ...core.avatar import to_data_uri
from ...core.layout import LayoutConfig
from ...core.variant import Variant
from .icons import icon_svg, verified_svg
from .themes import THEMES

DEFAULT_AVATAR = Path(__file__).parent / "assets" / "default_avatar.png"


def _resolve_background(layout: LayoutConfig, card_bg: str) -> str:
    """Map ``layout.background`` to a concrete CSS color string."""
    if layout.background == "theme":
        return card_bg
    if layout.background == "transparent":
        return "transparent"
    return layout.background


def _resolve_border(layout: LayoutConfig) -> bool:
    """Decide whether the card should draw a 1-px border (auto-off when transparent)."""
    if layout.border is not None:
        return layout.border
    return layout.background != "transparent"


def _avatar_uri(account):
    """Return the data-URI for an account's avatar (bundled fallback if None)."""
    src = account.avatar or str(DEFAULT_AVATAR)
    return to_data_uri(src, size=200)


def _common_context(post: Any, layout: LayoutConfig) -> dict[str, Any]:
    """Build the Jinja context dict shared by all Twitter variants.

    Includes palette, avatar URI, verified-badge HTML, page background,
    border decision, the ``icon()`` SVG factory, and ``avatar_for`` /
    ``verified_for`` callables for the recursive reply macro.
    """
    palette = THEMES[layout.theme]
    return {
        "post": post,
        "palette": palette,
        "avatar_uri": _avatar_uri(post.account),
        "page_bg": _resolve_background(layout, palette.bg),
        "show_border": _resolve_border(layout),
        "verified_html": verified_svg(post.account.verified),
        "icon": icon_svg,
        "layout": layout,
        "avatar_for": _avatar_uri,
        "verified_for": lambda acc: verified_svg(acc.verified),
    }


class FullVariant(Variant):
    """Full single-tweet card with avatar, name, verified, text, time/date,
    view count, and the six-icon action bar (reply / retweet / like / view /
    bookmark / share). Mirrors the live X card."""

    name = "full"
    template = "full.html.j2"

    def context(self, post, layout):
        return _common_context(post, layout)


class CompactVariant(Variant):
    """Avatar + name/handle + tweet text. No metrics, no action bar — for
    use in tight space (mobile cards, video overlays)."""

    name = "compact"
    template = "compact.html.j2"

    def context(self, post, layout):
        return _common_context(post, layout)


class BadgeVariant(Variant):
    """Circular avatar + display name + ``@handle``. Defaults to a
    transparent background so it can be composited over video / images."""

    name = "badge"
    template = "badge.html.j2"

    def context(self, post, layout):
        ctx = _common_context(post, layout)
        if layout.background == "theme":
            ctx["page_bg"] = "transparent"
        return ctx


class ReplyVariant(Variant):
    """A single tweet styled with the in-thread *reply card* chrome.

    Same data as ``full`` but with the more compact reply look (smaller
    avatar, name + handle inline, slimmer action bar) — matches how a
    reply renders inside ``thread_nested`` / ``thread_flat``, but with
    nothing above or below it. Useful when you want to extract one reply
    from a thread to use standalone.

    Honors ``LayoutConfig.reply_variant`` — pass ``"compact"`` to drop
    the action bar and keep only avatar + name + text.
    """

    name = "reply"
    template = "reply.html.j2"

    def context(self, post, layout):
        return _common_context(post, layout)


class ThreadNestedVariant(Variant):
    """Top tweet + recursive nested replies. Each reply is rendered with the
    style controlled by ``LayoutConfig.reply_variant`` (``"full"`` by
    default). Nesting respects ``LayoutConfig.max_nesting_depth``."""

    name = "thread_nested"
    template = "thread_nested.html.j2"

    def context(self, post, layout):
        return _common_context(post, layout)


class ThreadFlatVariant(Variant):
    """Top tweet + flat list of all replies (descendants flattened in
    pre-order). No indentation — useful when you only care about the
    chronological list of responses."""

    name = "thread_flat"
    template = "thread_flat.html.j2"

    def context(self, post, layout):
        ctx = _common_context(post, layout)
        ctx["flat_replies"] = list(_walk(post.replies))
        return ctx


def _walk(replies):
    """Pre-order walk yielding shallow copies (with ``replies=[]``) so the
    recursive macro renders each reply once and doesn't re-nest a flat list."""
    for r in replies or ():
        yield dataclasses.replace(r, replies=[])
        yield from _walk(r.replies)
