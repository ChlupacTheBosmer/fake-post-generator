"""Twitter / X platform plugin."""

from __future__ import annotations

from ...core.platform import Platform
from ...core.registry import register
from ...core.variant import Variant
from .variants import (
    BadgeVariant,
    CompactVariant,
    FullVariant,
    ThreadFlatVariant,
    ThreadNestedVariant,
)


@register
class TwitterPlatform(Platform):
    """Twitter / X renderer.

    Themes: ``light`` (white), ``dim`` (navy), ``dark`` (true-black). Variants:
    ``full``, ``compact``, ``badge``, ``thread_nested``, ``thread_flat``.
    """

    name = "twitter"
    themes = ("light", "dim", "dark")
    default_theme = "light"

    def variants(self) -> dict[str, Variant]:
        """Return the five Twitter variants keyed by name."""
        return {
            "full": FullVariant(),
            "compact": CompactVariant(),
            "badge": BadgeVariant(),
            "thread_nested": ThreadNestedVariant(),
            "thread_flat": ThreadFlatVariant(),
        }
