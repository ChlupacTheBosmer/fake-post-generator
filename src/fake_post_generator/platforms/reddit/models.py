from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Optional

from ...core.account import AccountProfile
from ...core.layout import LayoutConfig


@dataclass
class RedditPost:
    """A unified Reddit content node — represents both posts and comments.

    For top-level posts, supply `title` and `subreddit`. For comments
    (used as items in another post's `replies`), leave `title=None`.

    `replies` enables threading: each reply is itself a `RedditPost` and
    may have its own replies (nested).

    Variants validate which fields they need:
      - full / compact / thread / thread_nested / thread_flat → require `title`
      - badge → requires only `account`
      - comment / comment_compact → requires no `title` (must be None or empty)
    """

    account: AccountProfile
    body: str = ""

    # Post-only fields (None when this node represents a comment)
    title: Optional[str] = None
    subreddit: Optional[str] = None
    subreddit_icon: Optional[str] = None
    subreddit_members: Optional[str] = None
    subreddit_description: Optional[str] = None
    flair: Optional[str] = None
    image_url: Optional[str] = None
    comments: int = 0  # comment-count (the integer shown in the UI)

    # Common engagement fields
    upvotes: int = 0
    timestamp: Optional[str] = None
    awards: list[str] = field(default_factory=list)

    # Comment-only fields (ignored on top-level posts)
    op: bool = False
    edited: bool = False

    # Threading
    replies: list["RedditPost"] = field(default_factory=list)

    platform: ClassVar[str] = "reddit"

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
