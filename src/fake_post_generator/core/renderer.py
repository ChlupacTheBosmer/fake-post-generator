"""HTML → PNG bytes renderer abstraction.

A `Renderer` takes a fully-rendered HTML string and a CSS selector for the
element to capture, and returns PNG bytes. The default implementation uses
Playwright's headless Chromium for high-fidelity rendering — same engine that
real browsers use, so CSS / fonts / SVG behave exactly as on the web.
"""

from __future__ import annotations

from typing import Optional


class RenderError(RuntimeError):
    """Raised when the renderer fails to produce an image.

    The most common cause is a missing Playwright install. Catch this if you
    want to fall back to a different renderer at runtime.
    """


class Renderer:
    """Abstract base class for HTML → PNG renderers.

    Subclass and implement :meth:`render_element`. The class is intentionally
    thin so tests and alternate engines (e.g. wkhtmltoimage) can plug in.
    """

    def render_element(
        self,
        html: str,
        selector: str,
        *,
        scale: float = 2.0,
        transparent: bool = False,
        viewport_width: int = 1200,
        viewport_height: int = 2400,
        clip: Optional[dict] = None,
    ) -> bytes:
        """Render `html` and screenshot the first element matching `selector`.

        Args:
            html: A fully-formed HTML document.
            selector: CSS selector for the element to capture (e.g. ``.post-card``).
            scale: Device pixel ratio for the screenshot. ``2.0`` doubles the
                pixel dimensions for retina-quality output.
            transparent: If True, omit the page background so transparent
                regions of the captured element stay transparent in the PNG.
            viewport_width: Page viewport width in CSS pixels. Mainly affects
                layout (the screenshot is element-sized, not viewport-sized).
            viewport_height: Page viewport height in CSS pixels — must be tall
                enough to fully lay out the captured element.
            clip: Optional ``{x, y, width, height}`` dict to override the
                screenshot region. When provided, captures the page (not the
                element) at the clip rectangle.

        Returns:
            PNG-encoded image bytes.
        """
        raise NotImplementedError


class PlaywrightRenderer(Renderer):
    """Default renderer. Spins up a headless Chromium instance per call.

    The browser is launched and torn down on every render — fine for one-off
    work and the simplest API surface. For batch rendering, future work could
    expose a long-lived browser via a context manager.
    """

    def render_element(
        self,
        html,
        selector,
        *,
        scale=2.0,
        transparent=False,
        viewport_width=1200,
        viewport_height=2400,
        clip=None,
    ):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise RenderError(
                "playwright is required. install with: "
                "pip install playwright && playwright install chromium"
            ) from e

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    viewport={"width": viewport_width, "height": viewport_height},
                    device_scale_factor=scale,
                )
                page = context.new_page()
                page.set_content(html, wait_until="networkidle")
                element = page.locator(selector).first
                element.wait_for(state="visible", timeout=5000)
                if clip is not None:
                    return page.screenshot(
                        omit_background=transparent, type="png", clip=clip
                    )
                return element.screenshot(omit_background=transparent, type="png")
            finally:
                browser.close()


def default_renderer() -> Renderer:
    """Return a freshly-constructed `PlaywrightRenderer`.

    Use this when you want the package's default rendering behavior; pass a
    custom `Renderer` to a `Platform` constructor to override.
    """
    return PlaywrightRenderer()
