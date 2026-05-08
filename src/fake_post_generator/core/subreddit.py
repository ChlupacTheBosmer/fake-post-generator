"""Reusable per-subreddit visual config loaded from YAML.

A ``SubredditConfig`` provides the icon, member count, description, and
optional accent color for a named subreddit. The Reddit platform calls
:func:`load_subreddits` on every render and merges any matching entry into
the post's context — so once a config exists, ``RedditPost(subreddit="r/X")``
auto-fills the visual chrome.

Default lookup order (same pattern as accounts):

1. ``~/.fake_post_generator/subreddits.yaml``
2. ``./subreddits.yaml``
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml


DEFAULT_GLOBAL = Path.home() / ".fake_post_generator" / "subreddits.yaml"
DEFAULT_LOCAL = Path("subreddits.yaml")


@dataclass
class SubredditConfig:
    """Visual config for one subreddit.

    Attributes:
        name: The full ``r/Foo`` name (used as the YAML map key).
        icon: Path or URL to the subreddit's circular avatar. ``None`` falls
            back to the bundled snoo placeholder.
        color: Optional accent color (hex string). Reserved for future use —
            current templates don't apply it.
        members: Free-form member count (e.g. ``"1.3M"``). Shown in the
            thread variant header next to the description.
        description: Short subreddit tagline shown in the thread header.
    """

    name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    members: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "SubredditConfig":
        """Build a `SubredditConfig` from one YAML map entry."""
        return cls(
            name=name,
            icon=data.get("icon"),
            color=data.get("color"),
            members=data.get("members"),
            description=data.get("description"),
        )


def load_subreddits(*paths: Path) -> dict[str, SubredditConfig]:
    """Load and merge subreddit YAMLs.

    With no args, reads the global file then a project-local file. Later
    files override earlier entries with the same name. Returns a mapping
    from full subreddit name (``"r/Python"``) to `SubredditConfig`.

    The Reddit platform calls this on every render, so adding/removing
    entries in the YAML is reflected immediately — there's no cache.
    """
    sources = paths or (DEFAULT_GLOBAL, DEFAULT_LOCAL)
    out: dict[str, SubredditConfig] = {}
    for path in sources:
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text()) or {}
        for name, raw in data.items():
            out[name] = SubredditConfig.from_dict(name, raw or {})
    return out
