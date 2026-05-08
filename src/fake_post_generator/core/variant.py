"""Per-render variant abstraction.

A `Variant` is a single way of presenting a post: ``full`` (everything),
``compact`` (text + author), ``badge`` (avatar + name only), ``thread``
(post detail page), etc. Each platform owns its own concrete subclasses
and templates.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from jinja2 import Environment

from .layout import LayoutConfig


class Variant(ABC):
    """Base class for one named rendering variant.

    Concrete subclasses set:

    - ``name``      : the variant's lookup key (e.g. ``"full"``).
    - ``template``  : the Jinja2 template filename within the platform's
                      ``templates/`` directory.
    - ``selector``  : optional CSS selector for the element to screenshot
                      (defaults to ``.post-card``).

    They must implement :meth:`context`, which maps a platform-specific post
    object plus a :class:`LayoutConfig` to the dict consumed by the template.
    """

    name: ClassVar[str]
    template: ClassVar[str]
    selector: ClassVar[str] = ".post-card"

    @abstractmethod
    def context(self, post: Any, layout: LayoutConfig) -> dict[str, Any]:
        """Build the Jinja context dict for ``post`` rendered with ``layout``.

        Implementations should also do upfront validation here — e.g. raise
        ``ValueError`` if a required field on ``post`` is missing for this
        variant — so failures show up before the renderer is touched.
        """
        ...

    def render_html(
        self, post: Any, layout: LayoutConfig, env: Environment
    ) -> str:
        """Render the variant's template to an HTML string.

        Adds ``layout`` to the context as a fallback if the variant's
        :meth:`context` didn't include it explicitly.
        """
        ctx = self.context(post, layout)
        ctx.setdefault("layout", layout)
        return env.get_template(self.template).render(**ctx)
