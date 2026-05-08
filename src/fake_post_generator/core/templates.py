"""Jinja2 environment factory + custom number-formatting filters.

Each `Platform` constructs its own `Environment` rooted at its template
directory. Custom filters added here are available in every template:

    {{ 1234567 | humannum }}   # "1.2M"
    {{ 1234567 | thousands }}  # "1,234,567"
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def make_env(*template_dirs: Path) -> Environment:
    """Build a Jinja2 `Environment` rooted at the given template directories.

    Multiple paths can be provided; templates are looked up in order. Adds the
    custom ``humannum`` and ``thousands`` filters to the returned environment.
    """
    env = Environment(
        loader=FileSystemLoader([str(p) for p in template_dirs]),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["humannum"] = _humannum
    env.filters["thousands"] = lambda n: f"{int(n):,}"
    return env


def _humannum(n: int | float | None) -> str:
    """Format an integer like social-media stats: ``1234`` → ``"1.2K"``.

    Returns ``""`` for None. Sub-thousand values are rendered as plain ints
    (no comma). 1K-10K shows one decimal (``"1.2K"``); 10K-1M is rounded to
    integer K; 1M-10M is one-decimal M; above that, integer M.
    """
    if n is None:
        return ""
    n = int(n)
    if n < 1_000:
        return str(n)
    if n < 10_000:
        return f"{n / 1000:.1f}K".replace(".0K", "K")
    if n < 1_000_000:
        return f"{n // 1000}K"
    if n < 10_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    return f"{n // 1_000_000}M"
