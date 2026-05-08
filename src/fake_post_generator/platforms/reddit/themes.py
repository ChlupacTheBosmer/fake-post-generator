"""Reddit color palettes (light / dark)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemePalette:
    """Colors for one Reddit theme. All fields are CSS color strings."""

    bg: str
    """Card and page background color."""
    text: str
    """Primary text color (titles, post body)."""
    subtext: str
    """Secondary text color (timestamps, action labels)."""
    border: str
    """1-px separator and threading-line color."""
    flair_bg: str
    """Background of neutral flair pills, vote pills, and action pills."""
    flair_text: str
    """Foreground of neutral flair pills."""
    upvote: str
    """Brand orange for the active upvote arrow."""
    downvote: str
    """Brand blue for the active downvote arrow (currently unused — we
    only render the outline icon)."""
    icon: str
    """Default fill color for inactive action icons."""


# Flair colors (bg, text). Lookup is case-insensitive on the flair label.
# Anything not listed falls back to the theme's neutral flair_bg/flair_text.
FLAIR_COLORS: dict[str, tuple[str, str]] = {
    "showcase": ("#46d160", "#ffffff"),
    "discussion": ("#0079d3", "#ffffff"),
    "help": ("#ff4500", "#ffffff"),
    "tutorial": ("#7193ff", "#ffffff"),
    "news": ("#ff66ac", "#ffffff"),
    "resource": ("#24a0ed", "#ffffff"),
    "meta": ("#646d73", "#ffffff"),
    "question": ("#ffb000", "#1a1a1b"),
}


THEMES: dict[str, ThemePalette] = {
    "light": ThemePalette(
        bg="#ffffff",
        text="#1a1a1b",
        subtext="#7c7c7c",
        border="#ccc",
        flair_bg="#edeff1",
        flair_text="#1a1a1b",
        upvote="#ff4500",
        downvote="#7193ff",
        icon="#878a8c",
    ),
    "dark": ThemePalette(
        bg="#0b1416",
        text="#d7dadc",
        subtext="#818384",
        border="#343536",
        flair_bg="#272729",
        flair_text="#d7dadc",
        upvote="#ff4500",
        downvote="#7193ff",
        icon="#818384",
    ),
}
