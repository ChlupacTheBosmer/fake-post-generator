"""Avatar utilities: load, center-crop to a circle, encode as data URI.

Templates embed avatars as base64 data URIs so the renderer doesn't need to
hit the network or filesystem at screenshot time. The two public helpers are
:func:`to_circular_avatar` (returns PNG bytes) and :func:`to_data_uri` (the
same PNG inline-encoded for direct use in a CSS / ``<img src="...">``).
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw

ImageSource = Union[str, Path, bytes, Image.Image]
"""Anything :func:`_load` can read: a path/URL string, a `Path`, raw bytes,
or an in-memory PIL Image."""


def _load(source: ImageSource) -> Image.Image:
    """Resolve an arbitrary image source to a fresh PIL ``Image`` in RGBA.

    URL strings (``http://`` / ``https://``) are fetched with ``requests``;
    everything else is treated as a local path or in-memory data.
    """
    if isinstance(source, Image.Image):
        return source.convert("RGBA")
    if isinstance(source, bytes):
        return Image.open(BytesIO(source)).convert("RGBA")
    s = str(source)
    if s.startswith(("http://", "https://")):
        import requests

        resp = requests.get(s, timeout=10)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    return Image.open(s).convert("RGBA")


def to_circular_avatar(source: ImageSource, size: int = 400) -> bytes:
    """Return PNG bytes of `source` center-cropped to a square and circle-masked.

    Workflow: load → take the largest centered square → resize to ``size×size``
    → apply a circular alpha mask → return PNG bytes (RGBA, transparent corners).

    Args:
        source: Path, URL, bytes, or PIL ``Image``.
        size: Output edge length in pixels. Default 400 is a good balance for
            templates rendered at 1×–3× pixel ratios.
    """
    img = _load(source)
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize(
        (size, size), Image.LANCZOS
    )

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask=mask)

    buf = BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()


def to_data_uri(source: ImageSource, size: int = 400) -> str:
    """Convenience wrapper: return a ``data:image/png;base64,...`` URI.

    Suitable for embedding directly in template HTML/CSS. Saves a network
    round-trip during rendering and keeps the output self-contained.
    """
    return "data:image/png;base64," + base64.b64encode(
        to_circular_avatar(source, size)
    ).decode()
