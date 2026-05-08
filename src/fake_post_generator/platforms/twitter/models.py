from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Optional

from ...core.account import AccountProfile
from ...core.layout import LayoutConfig


@dataclass
class TwitterPost:
    """A unified tweet node — top-level tweets and replies use the same class.

    All metric fields are ignored by the `compact` and `badge` variants —
    fill what you have, leave the rest at 0/None. The `replies_count` field
    is the integer shown next to the reply icon; the `replies` list contains
    nested reply tweets used by the `thread_*` variants.
    """

    text: str
    account: AccountProfile

    replies_count: int = 0
    retweets: int = 0
    quotes: int = 0
    likes: int = 0
    bookmarks: int = 0
    views: int = 0

    time: Optional[str] = None
    date: Optional[str] = None
    image_url: Optional[str] = None

    replies: list["TwitterPost"] = field(default_factory=list)

    platform: ClassVar[str] = "twitter"

    def render(
        self,
        variant: str = "full",
        layout: Optional[LayoutConfig] = None,
        renderer=None,
    ) -> bytes:
        from ...core.registry import get_platform

        return get_platform(self.platform, renderer=renderer).render(
            self, variant=variant, layout=layout
        )
