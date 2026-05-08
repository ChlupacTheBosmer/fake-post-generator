"""Console-script entry point — renders one post per invocation.

Installed as the ``fake-post`` command via ``pyproject.toml``. See
``docs/CLI.md`` for the full reference. Quick usage::

    fake-post twitter --account elon --variant full --theme dim \\
              --background transparent --text "hello" --likes 100 \\
              --views 50000 --out tweet.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import LayoutConfig, available_platforms, load_accounts
from .platforms.reddit import RedditPost
from .platforms.twitter import TwitterPost


def main(argv: list[str] | None = None) -> int:
    """Parse args, build a post object, render it, write the PNG.

    Returns ``0`` on success, ``2`` if the named account isn't found in
    any of the searched YAML files.
    """
    p = argparse.ArgumentParser(prog="fake-post")
    p.add_argument("platform", choices=available_platforms())
    p.add_argument("--account", required=True, help="account id from accounts.yaml")
    p.add_argument("--variant", default="full", choices=["full", "compact", "badge"])
    p.add_argument("--theme", default=None)
    p.add_argument("--background", default="theme")
    p.add_argument("--width", type=int, default=600)
    p.add_argument("--scale", type=float, default=2.0)
    p.add_argument("--font-scale", type=float, default=1.0)
    p.add_argument("--out", required=True, help="output PNG path")
    p.add_argument(
        "--text", default=None, help="post text (twitter) or post body (reddit)"
    )
    p.add_argument("--title", default=None, help="reddit post title")
    p.add_argument("--accounts-file", type=Path, default=None)

    # twitter metrics
    p.add_argument("--likes", type=int, default=0)
    p.add_argument("--retweets", type=int, default=0)
    p.add_argument("--replies", type=int, default=0)
    p.add_argument("--views", type=int, default=0)
    p.add_argument("--bookmarks", type=int, default=0)
    p.add_argument("--date", default=None)
    p.add_argument("--time", default=None)

    # reddit
    p.add_argument("--subreddit", default="r/AskReddit")
    p.add_argument("--upvotes", type=int, default=0)
    p.add_argument("--comments", type=int, default=0)
    p.add_argument("--flair", default=None)
    p.add_argument("--timestamp", default=None)

    args = p.parse_args(argv)

    accounts = (
        load_accounts(args.accounts_file) if args.accounts_file else load_accounts()
    )
    if args.account not in accounts:
        print(
            f"account {args.account!r} not found. known: {sorted(accounts)}",
            file=sys.stderr,
        )
        return 2
    account = accounts[args.account]

    layout = LayoutConfig(
        width=args.width,
        scale=args.scale,
        font_scale=args.font_scale,
        theme=args.theme or _default_theme(args.platform),
        background=args.background,
    )

    if args.platform == "twitter":
        post = TwitterPost(
            text=args.text or "",
            account=account,
            likes=args.likes,
            retweets=args.retweets,
            replies_count=args.replies,
            views=args.views,
            bookmarks=args.bookmarks,
            date=args.date,
            time=args.time,
        )
    else:
        post = RedditPost(
            title=args.title or "",
            body=args.text or "",
            account=account,
            subreddit=args.subreddit,
            upvotes=args.upvotes,
            comments=args.comments,
            flair=args.flair,
            timestamp=args.timestamp,
        )

    png = post.render(variant=args.variant, layout=layout)
    Path(args.out).write_bytes(png)
    print(f"wrote {args.out} ({len(png)} bytes)")
    return 0


def _default_theme(platform: str) -> str:
    """Return the CLI's default theme for a platform.

    Currently both Twitter and Reddit default to ``"light"``. Lives as its
    own function so future platform-specific defaults are easy to add.
    """
    return "light" if platform == "reddit" else "light"


if __name__ == "__main__":
    raise SystemExit(main())
