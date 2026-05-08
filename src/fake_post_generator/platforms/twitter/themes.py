"""Color palettes for the three X themes (light / dim / dark)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemePalette:
    """Colors for one theme. All fields are CSS color strings (hex / rgb)."""

    bg: str
    """Card and page background color."""
    text: str
    """Primary text color (display name, post body)."""
    subtext: str
    """Secondary text color (handle, timestamps, counts)."""
    border: str
    """1-px separator color used between sections and around the card."""
    hover: str
    """Hover background color (currently unused — reserved for future variants)."""
    icon: str
    """Default fill color for action-bar icons."""


THEMES: dict[str, ThemePalette] = {
    "light": ThemePalette(
        bg="#ffffff",
        text="#0f1419",
        subtext="#536471",
        border="#eff3f4",
        hover="#f7f9f9",
        icon="#536471",
    ),
    "dim": ThemePalette(
        bg="#15202b",
        text="#f7f9f9",
        subtext="#8b98a5",
        border="#38444d",
        hover="#1e2732",
        icon="#8b98a5",
    ),
    "dark": ThemePalette(
        bg="#000000",
        text="#e7e9ea",
        subtext="#71767b",
        border="#2f3336",
        hover="#16181c",
        icon="#71767b",
    ),
}
