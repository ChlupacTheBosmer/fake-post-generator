# Agent Guide

Context dump for AI coding agents asked to *use* or *extend* this package.
Optimised for being pasted into context wholesale — read top-to-bottom and
you should know enough to make non-trivial changes safely.

## TL;DR

- Python package that renders accurate Twitter/X and Reddit posts as PNGs.
- One content class per platform (`TwitterPost`, `RedditPost`); `replies:
  list[Self]` represents threading.
- One `Variant` subclass per visual form. Twitter: `full`, `compact`,
  `badge`, `reply`, `thread_nested`, `thread_flat`. Reddit: `full`,
  `compact`, `badge`, `thread`, `comment`, `comment_compact`,
  `thread_nested`, `thread_flat`.
- Render = Jinja2 → HTML → Playwright headless Chromium → PNG bytes.
- Avatars are circle-cropped + base64-embedded as data URIs.
- Validation lives in `Variant.context()` — fails fast before Playwright runs.
- Single `LayoutConfig` controls all dimensions/themes/backgrounds.
- Per-platform theme palettes in `themes.py`; SVG icon paths in `icons.py`.
- Random commenter "banks" via `account_bank()` + `build_replies()`.
- Subreddit visual config auto-loads from `subreddits.yaml` on every Reddit render.

## Map of the codebase

```
src/fake_post_generator/
├── __init__.py                    public API surface — re-exports everything
├── cli.py                         `fake-post` console script
├── core/                          platform-agnostic infra (read this first)
│   ├── account.py                 AccountProfile + load_accounts
│   ├── avatar.py                  load → center-crop → circle-mask → data URI
│   ├── bank.py                    AccountBank, ReplyTemplate, build_replies
│   ├── layout.py                  LayoutConfig dataclass — all dimensional knobs
│   ├── platform.py                Platform ABC with .render(post, variant, layout)
│   ├── registry.py                @register / get_platform / available_platforms
│   ├── renderer.py                Renderer ABC + PlaywrightRenderer
│   ├── subreddit.py               SubredditConfig + load_subreddits
│   ├── templates.py               Jinja2 env factory + humannum/thousands filters
│   ├── variant.py                 Variant ABC: name, template, selector, .context()
│   └── banks/
│       ├── default_names.py       30 handles + 30 names for random pool
│       └── avatars/avatar_*.png   12 cartoon-portrait avatars
└── platforms/
    ├── __init__.py                imports both platforms → triggers @register
    ├── twitter/                   themes light/dim/dark; 5 variants
    └── reddit/                    themes light/dark; 8 variants
```

When you read a platform folder, read in this order:

1. `models.py` — the data shape
2. `themes.py` — the color knobs
3. `icons.py` — the SVG paths
4. `variants.py` — the Python logic per variant
5. `templates/*.html.j2` — the actual visual output
6. `platform.py` — the registration + variant lookup

## How a render works (read this once, then trust it)

```
post.render(variant, layout)
  → registry.get_platform(post.platform)
    → Platform.render(post, variant, layout)
      → validates layout.theme ∈ self.themes
      → looks up Variant by name (else ValueError)
      → variant.render_html(post, layout, env)
        → variant.context(post, layout)         ← per-variant python
        → env.get_template(variant.template).render(**ctx)
      → renderer.render_element(html, selector, scale, transparent)
        → playwright.chromium.launch(headless=True)
        → page.set_content(html, wait_until="networkidle")
        → page.locator(selector).screenshot(omit_background=transparent)
      → bytes
```

Two facts that matter for debugging:

1. **Avatars are eagerly resolved into data URIs in `_post_context()` /
   `_common_context()`**. By the time HTML reaches Playwright, every avatar
   is inline. If avatar loads ever fail, they fail synchronously in Python,
   not silently in the headless browser.
2. **The screenshot is element-fit, not viewport-fit**. `Renderer.render_element`
   calls `element.screenshot()`, which captures the bounding box of the
   element matched by the variant's `selector` (default `.post-card`). The
   viewport just needs to be tall enough to fully lay out the element.

## The single-class-per-platform pattern

`RedditPost` and `TwitterPost` are unified — one class for both top-level
content and nested replies/comments. **Don't introduce separate `RedditComment`
classes; the user explicitly rejected that design.** The contract:

- `replies: list[Self]` represents nesting (Reddit comments, Twitter replies).
- For Reddit, `title=None` means "this is a comment". Variants validate via
  `_require_title` / `_require_no_title` and raise `ValueError` if mismatched.
- Adding fields specific to one mode (e.g. `op: bool` for comments) is fine
  — they're just dataclass fields; variants ignore them when not relevant.

## Adding a new platform plugin

Read [ARCHITECTURE.md § Adding a new platform](ARCHITECTURE.md#adding-a-new-platform)
for the full recipe. Quick checklist:

- [ ] New folder `src/fake_post_generator/platforms/<name>/`.
- [ ] `models.py` with one dataclass that has `platform: ClassVar[str] = "<name>"`
  and a `.render()` shim that calls `get_platform(self.platform).render(...)`.
- [ ] `themes.py` with palettes, `icons.py` with SVG path data,
  `assets/default_avatar.png`, and `templates/*.html.j2`.
- [ ] `variants.py` with one `Variant` subclass per visual form. Each declares
  `name`, `template`, optional `selector`, and implements `context()`.
- [ ] `platform.py` with `Platform` subclass decorated with `@register`,
  declaring `name`, `themes`, `default_theme`, and `variants()`.
- [ ] One-line import in `platforms/__init__.py` to trigger registration.
- [ ] Re-export the new model class in `src/fake_post_generator/__init__.py`.

The smallest working variant is `badge` — copy it as a scaffold for new
platforms.

## Adding a new variant to an existing platform

1. Add a `Variant` subclass in `<platform>/variants.py`.
2. Add the corresponding `<name>.html.j2` in `<platform>/templates/`.
3. Register it in `<platform>/platform.py::variants()`.
4. Add a smoke test that asserts the rendered HTML contains expected strings.

If the variant needs a recursive piece (like comments / replies), put a
`_macro.html.j2` partial alongside it and import with
`{% from "_thing_macro.html.j2" import render_thing with context %}`. The
`with context` matters — without it the macro can't see the calling
template's variables (`palette`, `layout`, `icon`, `avatar_for`, etc.).

## Recurring patterns

### Theme + background resolution

Every variant calls `_resolve_background()` and `_resolve_border()`. Don't
duplicate that logic — call the helpers in your context builder. Templates
read `page_bg` (a CSS color string) and `show_border` (a bool), not
`layout.background` directly.

### Avatar resolution

Templates expect `avatar_uri` (the post author's avatar) and an `avatar_for`
callable that takes an `AccountProfile` and returns a data URI. The callable
is needed because the recursive comment/reply macro renders many distinct
authors at different depths.

### Icons

Each platform has an `icons.py` with raw SVG path data and an `icon_svg(name,
size, color)` factory function exposed in the template context as `icon`.
Templates call `{{ icon('reply', 18, palette.icon) | safe }}`.

### Recursive macros

Both `_comment_macro.html.j2` (Reddit) and `_reply_macro.html.j2` (Twitter)
follow the same pattern:

```jinja
{% macro render_X(item, depth=0) %}
<div ...>
  {# render the item #}
  {% if item.replies %}
    {% if depth + 1 >= layout.max_nesting_depth %}
      <div class="continue-thread">Continue this thread →</div>
    {% else %}
      {% for child in item.replies %}{{ render_X(child, depth + 1) }}{% endfor %}
    {% endif %}
  {% endif %}
</div>
{% endmacro %}
```

For flat variants, `variants.py::_walk()` pre-flattens the tree using
`dataclasses.replace(r, replies=[])` so the macro renders each comment once.

## Tests and verification

`tests/test_smoke.py` runs in <0.2 s with no browser. It uses a
`_FakeRenderer` that returns HTML bytes so assertions can `b"u/u" in out`-style
check the structure. **Run `pytest tests/` after every code change.**

Visual fidelity isn't covered by automated tests — it's manual via
`examples/render_thread_example.py` and `examples/render_all_tophet.py`.
The committed PNGs in `examples/out/` are the regression baseline; eyeball
them after meaningful changes.

## Known constraints / gotchas

- **Twitter renamed field**: the integer reply count is `replies_count: int`
  (because `replies: list[TwitterPost]` is the threading list). Old callers
  using `replies=42` need updating.
- **Reddit's `replies` vs `comments`**: `comments: int` is the *count* shown
  in the action bar; `replies: list[RedditPost]` is the nested tree.
- **Subreddit auto-resolution loads YAML on every render**. Cheap but worth
  knowing if you're rendering thousands.
- **Playwright spawns a fresh browser per render**. ~2 s per call from cold.
  Batch rendering would benefit from a persistent browser context — not
  implemented yet.
- **Chirp font isn't bundled**. Twitter templates fall back to system sans.
- **Element screenshots may clip box-shadows**. The `.post-card` element
  doesn't include surrounding shadow-room. Cosmetic; live with it for now.
- **`aspect_ratio` in `LayoutConfig` is reserved but not yet wired**. Setting
  it has no effect on the current renderer.

## Where things have moved during development

In case you see references to old names in old PRs or commits:

- `RedditComment` / `RedditThread` were considered and rejected — Reddit
  unified into `RedditPost` per the user's request.
- The Twitter integer reply field was once `replies: int`, renamed to
  `replies_count: int` when threading was added.
- Procedural avatars (initials-in-circle, runtime-generated) were considered
  and rejected — bundled cartoon PNGs in `core/banks/avatars/` are the
  canonical default.
- Subreddit config caching was considered but explicitly skipped — every
  render reloads the YAML so edits take effect immediately.

## What to do before claiming a task is done

1. `pytest tests/ -q` should pass.
2. `python examples/render_thread_example.py` should produce a non-zero PNG
   in `examples/out/thread-reddit-thread_nested-light.png` and the file
   should open without errors.
3. Eyeball the produced PNG against the screenshot baseline in your editor.
4. Update relevant docs:
   - New variant → mention in [USAGE.md](USAGE.md#variants) and [README](../README.md#features).
   - New layout knob → document in [USAGE.md § Layout & themes](USAGE.md#layout--themes).
   - New design choice → log it in [DECISIONS.md](DECISIONS.md).
5. Update docstrings on changed functions/classes.

If a step fails or the diff is large enough to be risky, **don't claim it's
done**. Either fix it or report the blocker.

## What you should not do

- Don't introduce a new content class per platform when a `replies:
  list[Self]` field on the existing class would do.
- Don't add caching to `load_subreddits()` / `load_accounts()` without
  explicit user request — the user values "edit YAML, see effect immediately."
- Don't bundle proprietary fonts (Twitter Chirp, Reddit Sans) without
  licensing context — fall back to system sans.
- Don't make `Variant.context()` silently fix bad input. Validate, raise
  `ValueError` with a helpful message. The user's words: "fail loudly."
- Don't break the YAML schema in a way that requires existing user files
  to migrate. If a field changes meaning, add the new one alongside the
  old.
- Don't write multi-paragraph docstrings or planning docs unless asked.
