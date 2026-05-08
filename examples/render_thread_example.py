"""Demo: render thread + comments for both Reddit and Twitter, plus standalone
comment / reply renders.

    python examples/render_thread_example.py
"""

from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)

from fake_post_generator import (  # noqa: E402
    AccountProfile,
    LayoutConfig,
    RedditPost,
    TwitterPost,
    account_bank,
    build_replies,
    load_accounts,
)

OUT = REPO / "examples" / "out"
OUT.mkdir(parents=True, exist_ok=True)
for stale in OUT.glob("thread-*.png"):
    stale.unlink()

accounts = load_accounts(REPO / "examples" / "accounts.yaml")
tophet_reddit = accounts["tophet_reddit"]
tophet_twitter = accounts["tophet"]
bank = account_bank(REPO / "examples" / "comment_bank.yaml", seed=7)


# ---------------------------------------------------------------------------
# REDDIT — post detail + comments
# ---------------------------------------------------------------------------

# User-controlled comment texts. The bank fills in random accounts/upvotes.
top_replies = build_replies(
    [
        {"text": "This is exactly what I needed for my project!", "op": False},
        {"text": "Cool, but how does it handle non-ASCII text?", "upvotes": 245},
        "How does this compare to Pillow's text rendering?",
        "Is there a docker image?",
    ],
    model_cls=RedditPost,
    bank=bank,
    upvotes_range=(5, 600),
    timestamps=["1h ago", "2h ago", "3h ago", "5h ago"],
    seed=11,
)

# Add nested replies to the second comment to demonstrate threading.
top_replies[1].replies = build_replies(
    [
        "Great question! It uses Playwright's headless Chromium so anything Chrome can render works.",
        {"text": "Including emoji!", "upvotes": 32},
    ],
    model_cls=RedditPost,
    bank=bank,
    upvotes_range=(2, 100),
    seed=13,
)

# OP replies in their own thread.
top_replies[0].replies = build_replies(
    [{"text": "Glad it helps! Lmk if you run into any rough edges.", "op": True, "upvotes": 88}],
    model_cls=RedditPost,
    bank=account_bank(seed=99),  # OP override happens via override below
    seed=21,
)
# Force OP avatar/name on that reply (since we want OP, not random).
top_replies[0].replies[0].account = tophet_reddit
top_replies[0].replies[0].op = True


reddit_thread = RedditPost(
    title="I built a python package that generates fake social media posts",
    body=(
        "Pure-python, headless rendering via Playwright, modular per-platform.\n"
        "Works with Twitter/X and Reddit out of the box. AMA."
    ),
    subreddit="r/Python",  # auto-resolves members + description from subreddits.yaml
    account=tophet_reddit,
    upvotes=2_412,
    comments=312,
    flair="Showcase",
    timestamp="3h ago",
    replies=top_replies,
)

for theme in ("light", "dark"):
    layout = LayoutConfig(width=720, theme=theme)
    (OUT / f"thread-reddit-thread-{theme}.png").write_bytes(
        reddit_thread.render(variant="thread", layout=layout)
    )
    (OUT / f"thread-reddit-thread_nested-{theme}.png").write_bytes(
        reddit_thread.render(variant="thread_nested", layout=layout)
    )
    (OUT / f"thread-reddit-thread_flat-{theme}.png").write_bytes(
        reddit_thread.render(variant="thread_flat", layout=layout)
    )

# Standalone comment (no surrounding post)
single_comment = RedditPost(
    body="This is one of the best things I've seen on r/Python lately.",
    account=tophet_reddit,
    upvotes=420,
    timestamp="2h ago",
    op=False,
)
(OUT / "thread-reddit-comment-light.png").write_bytes(
    single_comment.render(variant="comment", layout=LayoutConfig(width=560, theme="light"))
)
(OUT / "thread-reddit-comment_compact-light.png").write_bytes(
    single_comment.render(variant="comment_compact", layout=LayoutConfig(width=560, theme="light"))
)


# ---------------------------------------------------------------------------
# TWITTER — tweet + replies
# ---------------------------------------------------------------------------

tweet_replies = build_replies(
    [
        "Wait this is incredible",
        {"text": "How long did this take?", "upvotes": 142},
        "Open source?",
    ],
    model_cls=TwitterPost,
    bank=bank,
    upvotes_range=(20, 5000),
    timestamps=["2h", "1h", "30m"],
    seed=17,
)

tweet_replies[1].replies = build_replies(
    [
        {"text": "About a week of evenings — most of it was getting the visuals right", "op": True, "upvotes": 88},
    ],
    model_cls=TwitterPost,
    bank=account_bank(seed=42),
    seed=23,
)
tweet_replies[1].replies[0].account = tophet_twitter

tweet = TwitterPost(
    text=(
        "shipped a python package that generates pixel-accurate fake posts.\n\n"
        "twitter, reddit, threads, replies — all in one shot."
    ),
    account=tophet_twitter,
    replies_count=120,
    retweets=412,
    likes=3_842,
    bookmarks=57,
    views=210_000,
    time="14:32",
    date="May 8, 2026",
    replies=tweet_replies,
)

for theme in ("light", "dim", "dark"):
    layout = LayoutConfig(width=600, theme=theme)
    (OUT / f"thread-twitter-thread_nested-{theme}.png").write_bytes(
        tweet.render(variant="thread_nested", layout=layout)
    )
    (OUT / f"thread-twitter-thread_flat-{theme}.png").write_bytes(
        tweet.render(variant="thread_flat", layout=layout)
    )

# Compact reply variant override
compact_layout = LayoutConfig(width=600, theme="light", reply_variant="compact")
(OUT / "thread-twitter-thread_nested-compact-replies.png").write_bytes(
    tweet.render(variant="thread_nested", layout=compact_layout)
)


print(f"wrote {len(list(OUT.glob('thread-*.png')))} thread pngs to {OUT}")
