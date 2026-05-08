# Usage Guide

Comprehensive reference for everything the package can do. For a 30-second
intro see the [README](../README.md); for the CLI see [CLI.md](CLI.md).

## Contents

1. [Install](#install)
2. [Core concepts](#core-concepts)
3. [Accounts](#accounts)
4. [Subreddit config](#subreddit-config)
5. [Twitter / X](#twitter--x)
6. [Reddit](#reddit)
7. [Layout & themes](#layout--themes)
8. [Threads & comments](#threads--comments)
9. [Random "banks" for commenters](#random-banks-for-commenters)
10. [Custom rendering & transparency](#custom-rendering--transparency)
11. [Saving output](#saving-output)
12. [Troubleshooting](#troubleshooting)

---

## Install

```bash
pip install -e .
playwright install chromium     # one-time, ~150 MB
```

Requires Python 3.10+. The first render takes ~2 seconds (Chromium boot);
subsequent renders within the same process are also ~2 s each (one browser
per call — see [ARCHITECTURE](ARCHITECTURE.md) for why).

## Core concepts

The package has five public concepts you'll touch:

| Concept | Class | What it represents |
|---|---|---|
| **Account** | `AccountProfile` | Who is posting (name, handle, avatar, verification) |
| **Post** | `TwitterPost`, `RedditPost` | The content node — also represents replies / comments via the `replies` field |
| **Layout** | `LayoutConfig` | Dimensions, theme, background, font scale, threading depth |
| **Variant** | (string) | One named visual form: `"full"`, `"badge"`, `"thread_nested"`, etc. |
| **Bank** | `AccountBank` | Random pool of personas for filling reply authors |

You almost always interact with the package via:

```python
post.render(variant="...", layout=LayoutConfig(...)) -> bytes
```

Both `TwitterPost` and `RedditPost` expose `.render()` that returns PNG bytes.

## Accounts

### Inline

```python
from fake_post_generator import AccountProfile

acc = AccountProfile(
    id="me",                 # any string; used in error messages
    name="Sample User",      # display name
    handle="sampleuser",     # the @ / u/ handle (no prefix)
    avatar="path/to/pic.png" # optional path or URL
    verified="blue",         # None | "blue" | "gold" — Twitter only
)
```

### From YAML

```yaml
# ./accounts.yaml
elon:
  name: Elon Musk
  handle: elonmusk
  avatar: https://example.com/elon.jpg
  verified: blue
  platform_defaults:
    twitter:
      views: 1200000          # used as a default if you reuse this account a lot

throwaway42:
  name: throwaway42
  handle: throwaway42
  avatar: null
  verified: null
```

```python
from fake_post_generator import AccountProfile, load_accounts

# Single account by id (auto-loads the YAML files)
acc = AccountProfile.load("elon")

# Or load all accounts as a dict and index manually
accounts = load_accounts()           # default global + project-local
accounts = load_accounts(Path("./examples/accounts.yaml"))  # explicit path
acc = accounts["elon"]
```

**Default lookup order:** later files override earlier entries with the same key.

1. `~/.fake_post_generator/accounts.yaml`  (global)
2. `./accounts.yaml`                       (project-local)

### Avatars

Anything `PIL.Image.open` can read — local paths, URLs (HTTP/HTTPS), or raw
bytes — works as an avatar. The package automatically:

1. Loads the source.
2. Center-crops to the largest inscribed square.
3. Resizes to 200×200.
4. Applies a circular alpha mask.
5. Embeds as a base64 data URI in the rendered HTML.

If `avatar` is `None`, the platform's bundled default avatar is used (a head-
and-shoulders silhouette for Twitter, the Reddit snoo for Reddit).

## Subreddit config

Visual chrome for known subreddits — auto-loaded on every Reddit render:

```yaml
# ./subreddits.yaml
r/Python:
  icon: ./assets/python.png
  members: "1.3M"
  description: News about the Python programming language
  color: "#4584b6"
```

Once defined, any `RedditPost(subreddit="r/Python", ...)` automatically gets
the icon, members count, and description applied to the `thread` /
`thread_nested` / `thread_flat` variants. Per-post fields always win:

```python
RedditPost(
    subreddit="r/Python",
    subreddit_icon="./different.png",  # overrides YAML icon
    ...
)
```

Default lookup order is the same as accounts: `~/.fake_post_generator/subreddits.yaml`
then `./subreddits.yaml`.

## Twitter / X

```python
from fake_post_generator import TwitterPost

post = TwitterPost(
    text="...",
    account=acc,
    replies_count=42,         # NOTE: integer count is `replies_count`
    retweets=234,
    quotes=12,
    likes=12345,
    bookmarks=57,
    views=1_200_000,
    time="11:25 AM",
    date="May 8, 2026",
    image_url=None,           # optional — embeds an image in the tweet
    replies=[],               # list of TwitterPost — used by thread variants
)
```

### Variants

| Variant | What it shows |
|---|---|
| `full` | Avatar, name, handle, verified, text, image, time/date/views, full action bar |
| `compact` | Avatar, name/handle, text. No metrics |
| `badge` | Circular avatar + display name + handle. Transparent by default |
| `thread_nested` | Top tweet + recursive nested replies (each reply rendered as `LayoutConfig.reply_variant`) |
| `thread_flat` | Top tweet + flat list of all reply descendants |

```python
png = post.render(variant="full",   layout=LayoutConfig(theme="dim"))
png = post.render(variant="badge",  layout=LayoutConfig(scale=3))
png = post.render(variant="thread_nested", layout=LayoutConfig(reply_variant="compact"))
```

### Themes

`light` (white) · `dim` (navy / X's mid-dark mode) · `dark` (true black)

## Reddit

```python
from fake_post_generator import RedditPost

post = RedditPost(
    title="My post title",
    body="The body text.",
    subreddit="r/Python",
    subreddit_icon=None,           # optional override; otherwise YAML or snoo
    subreddit_members=None,        # ditto
    subreddit_description=None,    # ditto
    flair="Showcase",
    image_url=None,
    account=acc,
    upvotes=2412,
    comments=312,                  # the comment-count integer (different from `replies`)
    timestamp="3h ago",
    awards=[],
    replies=[],                    # list of RedditPost — used by thread variants
    op=False,                      # only meaningful when this RedditPost is itself a comment
    edited=False,                  # ditto
)
```

`RedditPost` is unified — it represents both **posts** (with `title`) and
**comments** (with `title=None`). Variants validate which mode they expect:

| Variant | Requires title? | Renders |
|---|---|---|
| `full` | yes | Feed-card view |
| `compact` | yes | Minimal feed card |
| `badge` | no | Avatar + name + `u/handle` |
| `thread` | yes | Single-post detail page (no comments) |
| `comment` | no (must be None) | Standalone comment, no thread line |
| `comment_compact` | no | Avatar + author + body + score |
| `thread_nested` | yes | Detail page + nested comment tree |
| `thread_flat` | yes | Detail page + flat comment list |

Pass a `title` to a comment variant or omit it from a post variant and the
package raises `ValueError` with a helpful message.

### Flair colors

Known flair labels get tinted backgrounds. Add to
`platforms/reddit/themes.py::FLAIR_COLORS` to extend:

| Label (case-insensitive) | Color |
|---|---|
| `Showcase` | green |
| `Discussion` | blue |
| `Help` | orange |
| `Tutorial` | purple |
| `News` | pink |
| `Resource` | sky blue |
| `Meta` | gray |
| `Question` | yellow |

Anything else falls back to the theme's neutral flair palette.

## Layout & themes

`LayoutConfig` is shared across all platforms:

```python
from fake_post_generator import LayoutConfig

LayoutConfig(
    width=600,                # CSS pixels
    aspect_ratio=None,        # reserved for future; not yet wired
    scale=2.0,                # device pixel ratio — final image is width*scale wide
    font_scale=1.0,           # multiplier on every font-size in the templates
    padding=None,             # None = each variant's tuned default
    theme="light",            # platform-specific: see below
    background="theme",       # "theme" | "transparent" | any CSS color
    border=None,              # None = auto: border off when transparent
    max_nesting_depth=8,      # Reddit-consistent comment nesting cutoff
    reply_variant="full",     # Twitter only: "full" | "compact" — for thread variants
)
```

| Platform | Themes |
|---|---|
| Twitter | `light` · `dim` · `dark` |
| Reddit  | `light` · `dark` |

Pass an unsupported theme and `Platform.render()` raises `ValueError`.

## Threads & comments

The same `RedditPost` / `TwitterPost` class represents both top-level content
and nested replies. To render a thread, populate `.replies` with more posts:

```python
top_post = RedditPost(
    title="AMA",
    account=op,
    subreddit="r/Python",
    upvotes=2400,
    comments=300,
    replies=[
        RedditPost(body="great!", account=other),                           # comment
        RedditPost(body="thanks", account=op, op=True,                      # OP reply
                   replies=[
                       RedditPost(body="agreed", account=third),            # nested reply
                   ]),
    ],
)
top_post.render(variant="thread_nested")
```

Every nested level adds an indent + a vertical thread line. Past
`LayoutConfig.max_nesting_depth` (default 8), the macro emits a "Continue
this thread →" link instead of recursing further.

## Random "banks" for commenters

When you have a real post but want plausible-looking commenters, use a bank.

### Bundled defaults (no setup)

```python
from fake_post_generator import RedditPost, build_replies

replies = build_replies(
    ["agree!", "no way", "underrated"],
    model_cls=RedditPost,
    upvotes_range=(1, 500),
    timestamps=["1h ago", "2h ago"],
    seed=42,
)
```

With no `bank=` argument, picks random handles + names from the bundled pools
in `core/banks/default_names.py` and assigns each one a different cartoon
avatar from `core/banks/avatars/`. With `unique_per_thread=True` (the
default), no two replies in one call share an account.

### Curated bank (recommended)

```yaml
# ./comment_bank.yaml — same schema as accounts.yaml
red_octopus:
  name: Red Octopus
  handle: red_octopus
  avatar: null               # null = bundled-pool fallback

stack_overflow:
  name: Stack Overflow
  handle: stack_overflow
  avatar: null
```

```python
from fake_post_generator import account_bank, build_replies

bank = account_bank("./comment_bank.yaml", seed=42)
replies = build_replies(["agree", "lol"], model_cls=RedditPost, bank=bank)
```

### Reply spec format

`build_replies` accepts a mixed iterable of:

- **`str`** — just the body. Everything else randomized.
- **`dict`** — `{"text": "...", "upvotes": 42, "account": acc, "op": True, ...}`.
  All keys optional except `text`. Anything not consumed becomes constructor kwargs.
- **`ReplyTemplate`** — pre-built spec.

User text is **always** under your control — the bank only randomizes account
and metadata.

### Pin specific replies (e.g. the OP)

```python
from fake_post_generator import ReplyTemplate

replies = build_replies(
    [
        "first comment",
        ReplyTemplate(text="OP here, glad it helps", account=op, op=True, upvotes=88),
        "third",
    ],
    model_cls=RedditPost,
    bank=bank,
)
```

## Custom rendering & transparency

Every variant supports two visual axes you'll use a lot:

### Theme

What the **card** looks like. Stays at platform-defined values
(`light/dim/dark` for Twitter, `light/dark` for Reddit).

### Background

What's **behind** the card. Independent from theme:

| `background` | Result |
|---|---|
| `"theme"` (default) | Page bg matches the card — no halo |
| `"transparent"` | Alpha 0 — composite over your own background |
| `"#hex"` / `"rgb(...)"` | Solid color of your choice |

When `background="transparent"`, the border around the card auto-hides (so
you don't get a visible edge floating on your composite background). Override
with `LayoutConfig(border=True)` if you want to keep the edge.

### Aspect-ratio framing

`aspect_ratio` is reserved for a future iteration — current renders are
element-fit (the screenshot equals the card's natural size). To get a 9:16
image today, render the card transparent and composite it onto a 9:16 canvas
yourself with PIL.

## Saving output

`render()` always returns PNG bytes. Trivial to write to disk:

```python
from pathlib import Path
Path("out.png").write_bytes(post.render(variant="full"))
```

To get a PIL Image:

```python
from io import BytesIO
from PIL import Image
img = Image.open(BytesIO(post.render(variant="full")))
```

To embed in HTML:

```python
import base64
"data:image/png;base64," + base64.b64encode(post.render(variant="full")).decode()
```

## Troubleshooting

**`RenderError: playwright is required`** — Playwright is installed but the
browser isn't. Run `playwright install chromium` once.

**`ValueError: reddit variant 'full' requires a title`** — you tried to use
a post variant on a `RedditPost` with `title=None` (which is shaped like a
comment). Either set the title or use the `comment` / `comment_compact` /
`badge` variant.

**`KeyError: account 'foo' not found`** — the account isn't in any of the
loaded YAML files. Check the path you passed to `load_accounts()` or
`AccountProfile.load(...)`, or that the global file at
`~/.fake_post_generator/accounts.yaml` exists.

**Renders look fine but text is rendering with a system font instead of
Twitter's Chirp** — Chirp is proprietary; the package falls back to
`-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica` per the
real X site's CSS. The result is very close but not identical. Bundle Chirp
locally if you have a license for it.

**Text overflows the card** — increase `LayoutConfig.width` or set
`LayoutConfig.font_scale=0.9`.

**Image is too small / pixelated** — bump `LayoutConfig.scale=3` (3× DPR).
