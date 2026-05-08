# Design Decisions

The non-obvious choices we made during development, with rationale. Read
this if you're confused why something is shaped the way it is — chances are
we considered the alternative.

## Architecture

### Modular plugin architecture, one folder per platform

**Decision:** Every platform lives in its own folder under
`platforms/<name>/` with the same internal shape (`models.py`, `variants.py`,
`platform.py`, `themes.py`, `icons.py`, `templates/`, `assets/`).

**Why:** Adding Instagram/Facebook later should mean *one new folder*, no
edits to core or other platforms. The symmetry across folders makes the
contract obvious to anyone (human or agent) reading the code.

**Alternatives considered:** A flat module with switch-on-platform-name
logic. Rejected — wouldn't scale past 3-4 platforms without becoming
unreadable.

### One content class per platform, unified for top-level + replies

**Decision:** `RedditPost` represents both posts and comments;
`TwitterPost` represents both tweets and replies. Threading is a
`replies: list[Self]` field.

**Why:** The user explicitly chose this over a separate `RedditComment`
class. Modularity (one class per platform) is more important than the slight
field-list bloat of a unified shape. Validation in `Variant.context()`
disambiguates which mode each variant expects.

**Alternatives considered:** Separate `RedditComment` and `RedditThread`
wrapper. Rejected by user during pass 3 planning: *"I would prefer to also
keep one class for reddit, this seems more compact and better modular
considering that there might be more platforms added."*

### Validation in `Variant.context()`, not on the model

**Decision:** Each variant validates its own requirements at context-build
time. e.g. `_require_title(post, "full")` raises `ValueError` if a Reddit
post variant gets a comment-shaped post.

**Why:** A given post object can be valid input to one variant and invalid
to another. Putting validation on the model would force pre-knowing which
variant will render it. Variant-time validation also runs cheaply before
Playwright spins up.

**User asked for:** "fail loudly." We do — clear `ValueError` with the
expected and actual fields.

## Rendering pipeline

### Playwright headless Chromium as the default renderer

**Decision:** HTML rendered to PNG via Playwright's chromium-headless-shell.

**Why:** Maximum CSS / SVG / font fidelity — same engine the live sites use.
The other practical options (`html2image`, `imgkit`/wkhtmltoimage) are
lighter but render with subtly different defaults that show up in shadows,
font weights, SVG anti-aliasing.

**Cost:** ~150 MB Chromium download on first install, ~2 s per render
(browser boot per call). Acceptable for the use case (image generation
isn't latency-critical) and fixable later with a persistent browser context.

### Element-fit screenshots, not viewport-fit

**Decision:** `Renderer.render_element` uses
`page.locator(selector).screenshot()`, capturing the bounding box of the
target element rather than a fixed viewport region.

**Why:** The card is what the user wants. The viewport is incidental layout
infrastructure. Using `element.screenshot()` means the user doesn't have
to compute viewport dimensions.

**Trade-off:** Box shadows that extend past the element border get clipped.
Cosmetic; documented in [USAGE § Troubleshooting](USAGE.md#troubleshooting).

### Avatars resolved eagerly into base64 data URIs

**Decision:** `_post_context()` / `_common_context()` immediately converts
every avatar source (path / URL / bytes / PIL.Image) into a circular PNG
encoded as `data:image/png;base64,...`.

**Why:** Self-contained HTML — no network/filesystem reads at screenshot
time. Failures (e.g. broken URL) raise synchronously in Python, with a
clear stack trace. Also avoids cross-origin / CORS / file:// permission
issues inside headless Chromium.

**Trade-off:** Renders are slower if many distinct avatars need fetching;
in practice the number per post is small and the network calls happen up
front.

## Configuration

### YAML for accounts and subreddits, with merged global → local order

**Decision:** Per-user global config at `~/.fake_post_generator/<name>.yaml`
plus per-project file at `./<name>.yaml`. Same schema; later files override
earlier entries with the same key.

**Why:** Same UX as `.env` / `pyproject` / `npmrc`. Users can keep one
"my accounts" file globally and override per project.

**Alternatives considered:** TOML (rejected as less concise for this kind
of nested data); JSON (rejected as comment-unfriendly).

### Subreddit configs auto-load on every render, no caching

**Decision:** `load_subreddits()` is called inside `_resolved_subreddit()`
on every Reddit render.

**Why:** User explicitly asked for this — "no caching now." The cost is
a tiny YAML parse per render; the benefit is that editing the YAML and
re-running the script *just works*. No invalidation footguns.

**If perf matters later:** add a cache keyed on file mtime. Document the
clearing API. Don't silently cache without a user-facing way to invalidate.

### Account `platform_defaults` schema present but not auto-applied

**Decision:** `AccountProfile` has a `platform_defaults: dict[str, dict]`
field, but the package doesn't auto-merge those defaults into post
construction.

**Why:** Pinning down the merge semantics (deep merge? per-field?) needs
a real use case. The field is there so users can read it and merge
manually for now.

**Status:** Open — flagged as next-pass work in conversation.

## Layout & visuals

### Single `LayoutConfig` shared across platforms

**Decision:** All dimensional/theme knobs live on one `LayoutConfig` dataclass.

**Why:** Most knobs (width, scale, font_scale, padding, theme, background,
border, max_nesting_depth, reply_variant) are platform-agnostic. The few
platform-specific ones (e.g. `reply_variant` is Twitter-only) live on
`LayoutConfig` too rather than per-platform — at the cost of a few unused
fields, you get one small class instead of three.

### Theme vs. background as independent axes

**Decision:** `theme` controls *card* colors. `background` controls what
shows *behind* the card. They're independent.

**Why:** Common requirement: dim-themed card on a transparent canvas (so
you can composite it onto your own dark video). Coupling them would force
either ugly two-step API or dropping the use case.

**Default:** `background="theme"` — page bg matches the card, no halo.

### Border auto-disables on transparent backgrounds

**Decision:** When `background == "transparent"`, `_resolve_border()`
returns `False` unless `LayoutConfig.border` is explicitly set.

**Why:** A 1-px border on a transparent card looks like a floating box
edge when composited. The auto-off behavior matches what users want 95%
of the time. The explicit override (`border=True`) is there for the 5%.

### Reddit-consistent threading depth (default 8)

**Decision:** `LayoutConfig.max_nesting_depth=8`. Beyond that, the
recursive macro emits a "Continue this thread →" link instead of rendering
deeper.

**Why:** User asked for "Reddit-consistent" cutoff. New Reddit collapses
threads at roughly that depth. Configurable per render.

### Aspect-ratio padding reserved but not wired

**Decision:** `LayoutConfig.aspect_ratio` is in the dataclass but currently
no-op; renders are element-fit.

**Why:** Wiring it correctly means deciding whether to letterbox/pillarbox
on the page background, on a separate transparent canvas, or both. Out of
scope for the initial release. Documented as TODO in [USAGE](USAGE.md#aspect-ratio-framing).

## Random commenter banks

### Bundled defaults via PIL-generated cartoon avatars (not real photos)

**Decision:** `core/banks/avatars/` ships 12 cartoon-portrait PNGs
generated by PIL with diverse skin tones, hair styles, hair colors, shirts,
and gradient backgrounds.

**Why:**
- **Procedural runtime generation** (initials-in-colored-circle) was
  considered and rejected: user said *"that wouldn't look real."*
- **Real photos / stock portraits** were rejected for licensing and
  ethical reasons (impersonation risk in a fake-post tool).
- **AI-generated faces** (ThisPersonDoesNotExist) were rejected for the
  same ethical reasons — too close to real-looking impersonation.
- **Wikimedia Commons** was the user's explicit suggestion, but the
  available "User_avatars" / "Default_avatars" categories don't have a
  curated CC0 set.

The compromise: bundle PIL-generated cartoon characters that are clearly
*illustrations*, look "designed" rather than "code-generated", and ship
as actual asset files (not generated at runtime). Users can swap them out
by dropping different PNGs into the same folder.

### `unique_per_thread=True` by default in `build_replies`

**Decision:** When a single `build_replies()` call needs N random accounts,
it pre-allocates a unique pool of size N from the bank.

**Why:** During development we noticed that `bank.pick()` per-item could
pick the same account twice in one thread, which looked unrealistic. User
asked: *"yes dedup in one call."*

**Fallback:** When the bank is too small to dedupe, allows repeats silently.

### User text always wins; only metadata is randomized

**Decision:** `build_replies` only randomizes account, upvotes, and
timestamp. The body text always comes from the user's spec.

**Why:** User control over content is the whole point. Random text would
defeat the use case.

## Naming

### `replies_count` (Twitter) vs `comments` (Reddit)

**Decision:** On `TwitterPost` the integer reply count is `replies_count`
(because `replies: list[TwitterPost]` is the threading list). On
`RedditPost` it's `comments: int` (because `replies: list[RedditPost]` is
the threading list, and Reddit calls them "comments").

**Why:** Matches each platform's vernacular and avoids the name clash with
the threading field.

**Cost:** It's slightly inconsistent across platforms. We chose
platform-native naming over forced uniformity.

## Things we deliberately didn't build

- **html2image / imgkit fallback renderer.** Documented as an option, not
  implemented. Playwright is the only path today.
- **Persistent browser context for batch rendering.** Each render currently
  spawns and tears down Chromium. Optimization for a later iteration.
- **Twitter Chirp / Reddit Sans bundled fonts.** Proprietary licensing.
  We use the platform-native fallback chains instead.
- **Real-photo random avatars.** Ethical / licensing risk. Cartoon PNGs
  ship instead.
- **Old-Reddit / new-Reddit toggle.** Templates target new Reddit only.
  Old Reddit is a separate variant that hasn't been requested.
- **Quote tweets / embedded link cards on Twitter.** Data model supports
  `image_url` only; URL preview cards are out of scope.
- **Reddit gallery posts, polls, video.** Single image only.
- **Programmatic comment-text generation.** User must supply every reply's
  text; we never invent content.
