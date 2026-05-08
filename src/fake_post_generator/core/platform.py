"""Base ``Platform`` class — one per social-media plugin.

A ``Platform`` ties together:

- a registry key (``name``)
- the supported themes (``themes`` + ``default_theme``)
- a directory of Jinja2 templates (auto-discovered next to the subclass)
- a set of named :class:`Variant` instances (``variants()``)
- a renderer (defaults to Playwright)

Concrete platforms live under ``fake_post_generator/platforms/<name>/`` and
register themselves with the global registry via the ``@register`` decorator.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Optional

from .layout import LayoutConfig
from .renderer import Renderer, default_renderer
from .templates import make_env
from .variant import Variant


class Platform(ABC):
    """Base class for a social-media platform plugin.

    Subclasses must define the class-level ``name``, ``themes``, and
    ``default_theme`` attributes, and implement :meth:`variants`.

    The constructor accepts an optional :class:`Renderer` (handy for tests
    or for swapping in a non-Playwright engine). Templates are auto-loaded
    from ``<module_dir>/templates`` by default — override
    :meth:`_template_dir` to change that.

    Class attributes:
        name: Registry key for the platform (e.g. ``"twitter"``).
        themes: Tuple of accepted theme names. ``LayoutConfig.theme`` is
            validated against this list.
        default_theme: Theme used when ``LayoutConfig.theme`` isn't set.
    """

    name: ClassVar[str]
    themes: ClassVar[tuple[str, ...]]
    default_theme: ClassVar[str]

    def __init__(self, renderer: Optional[Renderer] = None):
        """Construct the platform with an optional custom renderer."""
        self.renderer = renderer or default_renderer()
        self.env = make_env(self._template_dir())

    @classmethod
    def _template_dir(cls) -> Path:
        """Default templates directory: ``<file holding subclass>/templates``."""
        return Path(inspect.getfile(cls)).parent / "templates"

    @abstractmethod
    def variants(self) -> dict[str, Variant]:
        """Return ``{variant_name: Variant}`` for every variant the platform
        supports. Called once per render — return new instances or memoize
        as you prefer.
        """
        ...

    def render(
        self,
        post: Any,
        variant: str = "full",
        layout: Optional[LayoutConfig] = None,
    ) -> bytes:
        """Render `post` with the named variant and return PNG bytes.

        Validates the requested theme and variant up front so misuse fails
        loudly. Delegates HTML production to :meth:`Variant.render_html`
        and bytes production to ``self.renderer.render_element``.

        Args:
            post: A platform-specific content model (e.g. ``TwitterPost``).
            variant: Variant name. Must be a key of :meth:`variants`.
            layout: Optional :class:`LayoutConfig`. Defaults to a fresh
                instance with this platform's ``default_theme``.

        Raises:
            ValueError: If the theme or variant is unknown.
        """
        layout = layout or LayoutConfig(theme=self.default_theme)
        if layout.theme not in self.themes:
            raise ValueError(
                f"{self.name} supports themes {self.themes}, got {layout.theme!r}"
            )
        variants = self.variants()
        if variant not in variants:
            raise ValueError(
                f"{self.name} has no variant {variant!r}; "
                f"available: {sorted(variants)}"
            )
        v = variants[variant]
        html = v.render_html(post, layout, self.env)
        return self.renderer.render_element(
            html=html,
            selector=v.selector,
            scale=layout.scale,
            transparent=(layout.background == "transparent"),
        )
