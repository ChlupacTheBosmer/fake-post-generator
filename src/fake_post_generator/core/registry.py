"""Global registry of installed Platform plugins.

When a platform module is imported, its `Platform` subclass calls
:func:`register` (typically via the `@register` decorator) which adds it to
this module-level dict. The `fake_post_generator/__init__.py` package eagerly
imports the bundled platforms (twitter, reddit) so they are available without
the caller having to import them explicitly.
"""

from __future__ import annotations

from typing import Optional

from .platform import Platform
from .renderer import Renderer

_REGISTRY: dict[str, type[Platform]] = {}


def register(platform_cls: type[Platform]) -> type[Platform]:
    """Decorator that adds a `Platform` subclass to the global registry.

    Use as `@register` above the platform class definition. Registration is
    keyed on `platform_cls.name` (e.g. ``"twitter"``) and is idempotent —
    re-registering a platform with the same name overwrites the previous one.

    Returns the class unchanged so it works as a decorator.
    """
    _REGISTRY[platform_cls.name] = platform_cls
    return platform_cls


def get_platform(name: str, renderer: Optional[Renderer] = None) -> Platform:
    """Instantiate the registered platform with the given name.

    Args:
        name: The platform key (e.g. ``"twitter"``, ``"reddit"``).
        renderer: Optional custom `Renderer`. Defaults to a `PlaywrightRenderer`.

    Raises:
        KeyError: If no platform with `name` is registered.
    """
    if name not in _REGISTRY:
        raise KeyError(
            f"no platform registered with name {name!r}; "
            f"available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[name](renderer=renderer)


def available_platforms() -> list[str]:
    """Return the sorted list of platform names that have been registered."""
    return sorted(_REGISTRY)
