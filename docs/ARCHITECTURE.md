# Architecture

This document describes how the package is laid out, how a render flows
through it, and how to add a new platform plugin.

## Package layout

```
fake_post_generator/
├── pyproject.toml
├── README.md
├── docs/                                # this folder
├── examples/
│   ├── accounts.yaml                    # sample account configs
│   ├── subreddits.yaml                  # sample subreddit configs
│   ├── comment_bank.yaml                # sample bank for random commenters
│   ├── render_all_tophet.py             # renders every variant × theme × bg
│   ├── render_thread_example.py         # threads + comments demo
│   ├── render_example.py                # generic kitchen-sink demo
│   ├── profile_pic.png                  # sample avatar used by the demos
│   └── out/                             # generated PNGs (committed)
├── tests/
│   └── test_smoke.py                    # 10 wiring/validation tests, no browser
└── src/fake_post_generator/
    ├── __init__.py                      # public API surface (re-exports)
    ├── cli.py                           # `fake-post` console script
    ├── core/                            # platform-agnostic infrastructure
    │   ├── account.py                   # AccountProfile + YAML loader
    │   ├── avatar.py                    # PIL helpers (load, circle-crop, data URI)
    │   ├── bank.py                      # AccountBank, ReplyTemplate, build_replies
    │   ├── layout.py                    # LayoutConfig dataclass
    │   ├── platform.py                  # Platform ABC
    │   ├── registry.py                  # @register / get_platform / available_platforms
    │   ├── renderer.py                  # Renderer ABC + PlaywrightRenderer
    │   ├── subreddit.py                 # SubredditConfig + YAML loader
    │   ├── templates.py                 # Jinja2 env factory + filters
    │   ├── variant.py                   # Variant ABC
    │   └── banks/                       # bundled random-commenter assets
    │       ├── default_names.py         # 30 handles + 30 names
    │       └── avatars/                 # 12 cartoon-portrait PNGs
    └── platforms/                       # one folder per platform plugin
        ├── __init__.py                  # importing this triggers all @register
        ├── twitter/
        │   ├── __init__.py
        │   ├── platform.py              # TwitterPlatform
        │   ├── models.py                # TwitterPost dataclass
        │   ├── variants.py              # 5 variant classes + helpers
        │   ├── icons.py                 # X icon SVG path data + verified badges
        │   ├── themes.py                # ThemePalette + 3 palettes
        │   ├── assets/default_avatar.png
        │   └── templates/               # Jinja2 templates
        │       ├── full.html.j2
        │       ├── compact.html.j2
        │       ├── badge.html.j2
        │       ├── thread_nested.html.j2
        │       ├── thread_flat.html.j2
        │       ├── _reply_macro.html.j2
        │       └── _reply_styles.html.j2
        └── reddit/                      # same shape as twitter/
            ├── ...
            ├── icons.py                 # RPL (Reddit Product Language) SVG paths
            ├── themes.py                # palettes + FLAIR_COLORS map
            ├── variants.py              # 8 variant classes
            └── templates/               # 8 .html.j2 + 2 partials (_comment_*)
```

## The render pipeline

End-to-end, one `post.render(variant=..., layout=...)` call does this:

```
TwitterPost / RedditPost           (data)
        │
        ▼
post.render(variant, layout)       (model.py — convenience method)
        │
        ▼
get_platform("twitter")            (registry.py — looks up plugin class)
        │
        ▼
TwitterPlatform.render(post, ...)  (core/platform.py)
        │
        ├─ validates theme ∈ self.themes
        ├─ looks up Variant by name
        │
        ▼
variant.render_html(post, layout, env)
        │
        ├─ variant.context(post, layout)        ← per-variant Python logic
        │   (raises ValueError on bad input)
        │
        ▼
Jinja2 Environment.get_template(...).render(**ctx)
        │
        ▼
HTML string                          (with avatars as base64 data URIs)
        │
        ▼
PlaywrightRenderer.render_element(html, selector, scale, transparent)
        │
        ├─ chromium.launch(headless=True)
        ├─ context.new_page()
        ├─ page.set_content(html, wait_until="networkidle")
        ├─ page.locator(selector).wait_for(state="visible")
        ├─ element.screenshot(omit_background=transparent)
        │
        ▼
PNG bytes                             (returned all the way up)
```

Key invariants:

- **Validation happens in `Variant.context()`** so misuse fails before
  Playwright is touched. Example: `RedditPost(title=None)` rendered with
  `full` raises `ValueError`.
- **The Jinja env is per-platform, scoped to that platform's templates
  directory.** Cross-platform partials live alongside the variant that
  needs them (e.g. `_comment_macro.html.j2` lives in `reddit/templates/`).
- **Avatar resolution is eager.** Each `_post_context()` immediately turns
  every avatar source (path/URL) into a base64 data URI. By the time the
  HTML reaches Playwright, no further loads are needed.
- **The screenshot is element-fit.** `Renderer.render_element` calls
  `element.screenshot()`, which captures the element's bounding box, not
  the viewport. The `viewport_height` only needs to be tall enough to
  fully lay out the element.

## Single-class-per-platform model

Both `TwitterPost` and `RedditPost` are unified content nodes — one class
represents both top-level content and replies/comments. `replies: list[Self]`
provides nesting; variants decide how to traverse it.

| Why | Rationale |
|---|---|
| Modular | Every platform plugin owns exactly one model. Adding Instagram → one new class, no other changes. |
| Symmetric | A reply *is* a tweet; a comment is structurally a post-without-title. Forcing two classes adds boilerplate without expressing real differences. |
| Validation localized | The `Variant.context()` method is the single place that knows which fields it needs. `_require_title` / `_require_no_title` make the contract explicit. |

## Adding a new platform

To add e.g. Instagram:

1. **Create the package:**
   ```
   src/fake_post_generator/platforms/instagram/
   ├── __init__.py
   ├── platform.py         # InstagramPlatform(Platform), @register
   ├── models.py           # InstagramPost dataclass with platform="instagram"
   ├── variants.py         # one class per visual variant
   ├── icons.py            # SVG paths
   ├── themes.py           # ThemePalette + dict of palettes
   ├── assets/default_avatar.png
   └── templates/          # one .html.j2 per variant + any partials
   ```

2. **Wire registration**: in `src/fake_post_generator/platforms/__init__.py`,
   add `from . import instagram  # noqa: F401`. Importing the platform's
   `platform.py` triggers the `@register` decorator on the class.

3. **Export the model**: in `src/fake_post_generator/__init__.py`, add
   `from .platforms.instagram import InstagramPost` and add it to
   `__all__`.

4. **Done.** Nothing in `core/` or in other platforms needs to change.
   The new platform's `name` ("instagram") is the registry key; users call
   `InstagramPost(...).render(variant=..., layout=...)`.

### Concrete starter for `models.py`

```python
from dataclasses import dataclass, field
from typing import ClassVar, Optional

from ...core.account import AccountProfile
from ...core.layout import LayoutConfig


@dataclass
class InstagramPost:
    """One Instagram post node — also represents comments via `replies`."""
    caption: str
    account: AccountProfile
    image_url: Optional[str] = None
    likes: int = 0
    timestamp: Optional[str] = None
    replies: list["InstagramPost"] = field(default_factory=list)

    platform: ClassVar[str] = "instagram"

    def render(self, variant="full", layout=None, renderer=None):
        from ...core.registry import get_platform
        return get_platform(self.platform, renderer=renderer).render(
            self, variant=variant, layout=layout
        )
```

### Concrete starter for `platform.py`

```python
from ...core.platform import Platform
from ...core.registry import register
from .variants import FullVariant, BadgeVariant


@register
class InstagramPlatform(Platform):
    name = "instagram"
    themes = ("light", "dark")
    default_theme = "light"

    def variants(self):
        return {
            "full": FullVariant(),
            "badge": BadgeVariant(),
        }
```

### Concrete starter for one variant

```python
from ...core.variant import Variant
from .themes import THEMES


class FullVariant(Variant):
    name = "full"
    template = "full.html.j2"

    def context(self, post, layout):
        return {
            "post": post,
            "palette": THEMES[layout.theme],
            "layout": layout,
            # ... avatar URIs, page bg, etc.
        }
```

The smallest end-to-end variant is the `badge` for either existing platform
— ~30 lines of template, no metrics or interactions. Copy it as a starting
point.

## Renderer contract

Anything that implements `Renderer.render_element(html, selector, ...) -> bytes`
plugs into a `Platform`. Pass a custom one via the constructor:

```python
plat = TwitterPlatform(renderer=MyRenderer())
```

For tests, `tests/test_smoke.py` uses a `_FakeRenderer` that just returns the
HTML bytes — useful for asserting the rendered HTML contains expected strings
without spinning up Chromium.

## Asset bundling

Asset files (PNG / SVG / WOFF / Jinja templates) are declared in
`pyproject.toml` under `[tool.setuptools.package-data]`:

```toml
"fake_post_generator" = ["**/*.j2", "**/*.html", "**/*.svg", "**/*.css", "**/*.png"]
```

Drop a new file into any subpackage and it'll ship with `pip install`. No
manifest file or extra config needed.

## Testing

Tests in `tests/test_smoke.py` deliberately don't touch Playwright. They
verify:

- Platform registration (both bundled platforms appear in `available_platforms()`).
- HTML rendering (using a fake renderer that returns the HTML bytes).
- Validation paths (`reddit.full` rejects `title=None`; `reddit.comment` rejects a title).
- Bank wiring (`build_replies` honors user-supplied text; the bundled pool produces complete accounts).

End-to-end pixel checks are manual via `examples/render_*.py`. The
deliverables in `examples/out/` are the de-facto regression suite: visual
diff before/after a change.
