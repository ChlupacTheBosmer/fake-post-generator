# fake_post_generator

Pixel-faithful fake social-media post images, in Python. Twitter / X and Reddit
out of the box; modular plugin architecture for adding more.

```python
from fake_post_generator import AccountProfile, LayoutConfig, TwitterPost

png = TwitterPost(
    text="hello world",
    account=AccountProfile(id="elon", name="Elon Musk", handle="elonmusk", verified="blue"),
    likes=12345, retweets=234, replies_count=42, views=1_200_000,
).render(
    variant="full",
    layout=LayoutConfig(theme="dim", background="transparent", scale=2),
)
open("tweet.png", "wb").write(png)
```

## Why

I needed accurate-looking fake post images for video/marketing/research work
and didn't want to keep screenshotting real posts. Existing web tools work but
aren't scriptable. This package gives you the same fidelity, programmatic
control, and the ability to render hundreds of variants in a batch.

## Install

```bash
pip install -e .                  # editable install
playwright install chromium       # one-time, ~150 MB
```

Python 3.10+. Playwright is the default renderer; runs headless Chromium so
fonts/CSS/SVG behave exactly as on the web.

## Features

| Capability | Twitter / X | Reddit |
|---|---|---|
| Themes | light / dim / dark | light / dark |
| Variants | full · compact · badge · thread_nested · thread_flat | full · compact · badge · thread · comment · comment_compact · thread_nested · thread_flat |
| Verified badges | blue · gold | n/a |
| Custom subreddit icons / members / description | n/a | yes (via `subreddits.yaml`) |
| Threading (replies / comments) | nested + flat | nested + flat |
| Random-account "bank" for filling commenters | yes | yes |
| Transparent backgrounds for compositing | yes | yes |
| Granular layout (width, scale, font_scale, padding, border) | yes | yes |

## Quick start

### Inline construction

```python
from fake_post_generator import AccountProfile, LayoutConfig, RedditPost

acc = AccountProfile(id="me", name="Sample User", handle="sampleuser")
png = RedditPost(
    title="I built a fake post generator",
    body="Pure-python, headless Chromium rendering. AMA.",
    subreddit="r/Python",
    account=acc,
    upvotes=2412, comments=312,
    flair="Showcase",
    timestamp="3h ago",
).render(
    variant="full",
    layout=LayoutConfig(theme="dark", scale=2),
)
```

### Reusable accounts via YAML

```yaml
# ./accounts.yaml
elon:
  name: Elon Musk
  handle: elonmusk
  avatar: https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Elon_Musk_Royal_Society_%28crop2%29.jpg/256px-Elon_Musk_Royal_Society_%28crop2%29.jpg
  verified: blue
```

```python
from fake_post_generator import AccountProfile, TwitterPost

acc = AccountProfile.load("elon")  # auto-loads from ./accounts.yaml
TwitterPost(text="hi", account=acc).render(variant="badge")
```

### Threads with random commenters

```python
from fake_post_generator import RedditPost, account_bank, build_replies

bank = account_bank("./examples/comment_bank.yaml", seed=7)

post = RedditPost(
    title="...",
    body="...",
    subreddit="r/Python",
    account=acc,
    replies=build_replies(
        ["agree!", {"text": "lol", "upvotes": 999}, "underrated"],
        model_cls=RedditPost,
        bank=bank,
    ),
)
post.render(variant="thread_nested")
```

User text is always under your control; only metadata (random account, vote
counts, timestamps) is filled from the bank.

## Documentation

- **[docs/USAGE.md](docs/USAGE.md)** — comprehensive user guide: every variant,
  every option, accounts, subreddit configs, banks, threads, transparent
  composites.
- **[docs/CLI.md](docs/CLI.md)** — `fake-post` command-line reference.
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — how the package is laid
  out, the render pipeline, and how to add a new platform plugin.
- **[docs/AGENTS.md](docs/AGENTS.md)** — context dump for AI agents asked to
  work with or extend this package.
- **[docs/DECISIONS.md](docs/DECISIONS.md)** — every meaningful design
  decision and why we chose it.

## Examples

- [`examples/render_all_tophet.py`](examples/render_all_tophet.py) — every
  variant × theme × background for one account (30 PNGs).
- [`examples/render_thread_example.py`](examples/render_thread_example.py) —
  thread + nested comments with random commenters from a bank.
- [`examples/accounts.yaml`](examples/accounts.yaml),
  [`examples/subreddits.yaml`](examples/subreddits.yaml),
  [`examples/comment_bank.yaml`](examples/comment_bank.yaml) — sample configs.

## License

Open-source. The package vendors official platform iconography (Twitter/X
SVG path data, Reddit RPL icons) for visual fidelity. Twitter's "Chirp" font
is **not** bundled — templates fall back to system sans-serif.
