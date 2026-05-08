"""Per-render layout configuration.

A :class:`LayoutConfig` controls every dimensional / theming knob that's
shared across platforms: width, scale (DPR), font scale, padding, theme,
background, border, and threading depth. Platform-specific behavior lives
in the variants/templates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LayoutConfig:
    """Granular knobs for resizing/repositioning a post variant.

    Most fields have sane defaults — pass only what you want to override.

    Attributes:
        width: Card width in CSS pixels. Final image width is
            ``width * scale`` (because of the device pixel ratio).
        aspect_ratio: width / height (e.g. ``9 / 16 == 0.5625``). When set,
            the rendered image is padded to that ratio. ``None`` keeps the
            variant's natural height.
            *(Note: aspect-ratio padding is reserved for a future iteration —
            current renders are element-fit.)*
        scale: Device pixel ratio for the screenshot. ``2.0`` doubles pixel
            density (retina-quality output).
        font_scale: Multiplier applied to every CSS font-size in the
            templates. ``1.5`` makes everything 50% larger; ``0.8`` shrinks.
        padding: Override the default card padding in CSS pixels. ``None``
            uses each variant's tuned default.
        theme: Visual theme. Twitter supports ``"light" / "dim" / "dark"``;
            Reddit supports ``"light" / "dark"``. Validation happens in
            :meth:`Platform.render`.
        background: What shows behind the card.

            * ``"theme"`` (default) — same color as the card body (no halo).
            * ``"transparent"`` — alpha 0 (uses Playwright's omit_background).
            * any CSS color — ``"#000000"``, ``"rgb(...)"``, etc.

        border: Force the card border on/off. ``None`` (default) means auto:
            border off when ``background="transparent"``, on otherwise.
        max_nesting_depth: Reddit-consistent threading cutoff. After this
            depth, the comment macro emits a "Continue this thread →" link
            instead of recursing further. Default ``8``.
        reply_variant: Twitter only — the visual style for nested replies
            in ``thread_nested`` / ``thread_flat``. ``"full"`` (default,
            with metrics) or ``"compact"`` (text + author only).
    """

    width: int = 600
    aspect_ratio: Optional[float] = None
    scale: float = 2.0
    font_scale: float = 1.0
    padding: Optional[int] = None
    theme: str = "light"
    background: str = "theme"
    border: Optional[bool] = None
    max_nesting_depth: int = 8
    reply_variant: str = "full"
