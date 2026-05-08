"""Render every possible variant × theme × background for the `tophet` account.

Run from anywhere — the script chdirs to the repo root so that the relative
avatar path `./examples/profile_pic.png` in accounts.yaml resolves.

    python examples/render_all_tophet.py
"""

from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)  # so ./examples/profile_pic.png in yaml resolves

from fake_post_generator import (  # noqa: E402  (after chdir)
    LayoutConfig,
    RedditPost,
    TwitterPost,
    load_accounts,
)

OUT = REPO / "examples" / "out"
OUT.mkdir(parents=True, exist_ok=True)

# Wipe any previous run so the directory only shows the current outputs.
for stale in OUT.glob("tophet-*.png"):
    stale.unlink()

accounts = load_accounts(REPO / "examples" / "accounts.yaml")
tophet = accounts["tophet"]
tophet_reddit = accounts["tophet_reddit"]

# --- Twitter ---------------------------------------------------------------
tweet = TwitterPost(
    text=(
        "Testing the fake-post-generator package with my own avatar.\n\n"
        "All variants × all themes × theme/transparent backgrounds."
    ),
    account=tophet,
    replies_count=128,
    retweets=412,
    likes=3_842,
    bookmarks=57,
    views=100_000,
    time="14:32",
    date="May 8, 2026",
)

twitter_themes = ("light", "dim", "dark")
backgrounds = ("theme", "transparent")
variants = ("full", "compact", "badge")

twitter_count = 0
for variant in variants:
    for theme in twitter_themes:
        for bg in backgrounds:
            layout = LayoutConfig(
                width=600, theme=theme, background=bg, scale=2.0
            )
            png = tweet.render(variant=variant, layout=layout)
            (OUT / f"tophet-twitter-{variant}-{theme}-{bg}.png").write_bytes(png)
            twitter_count += 1

# --- Reddit ----------------------------------------------------------------
rpost = RedditPost(
    title="I built a python package that generates fake social media posts",
    body=(
        "Pure-python, headless rendering via Playwright, modular per-platform.\n\n"
        "Works with Twitter/X and Reddit out of the box."
    ),
    account=tophet_reddit,
    subreddit="r/Python",
    upvotes=2_400,
    comments=312,
    flair="Showcase",
    timestamp="3h ago",
)

reddit_themes = ("light", "dark")

reddit_count = 0
for variant in variants:
    for theme in reddit_themes:
        for bg in backgrounds:
            layout = LayoutConfig(
                width=640, theme=theme, background=bg, scale=2.0
            )
            png = rpost.render(variant=variant, layout=layout)
            (OUT / f"tophet-reddit-{variant}-{theme}-{bg}.png").write_bytes(png)
            reddit_count += 1

print(f"wrote {twitter_count} twitter + {reddit_count} reddit pngs to {OUT}")
