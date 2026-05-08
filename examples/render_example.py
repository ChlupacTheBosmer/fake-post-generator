"""Render one example for each platform & variant.

    pip install -e .
    playwright install chromium
    python examples/render_example.py
"""

from pathlib import Path

from fake_post_generator import (
    AccountProfile,
    LayoutConfig,
    RedditPost,
    TwitterPost,
    load_accounts,
)

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)


def main() -> None:
    accounts = load_accounts(Path(__file__).parent / "accounts.yaml")
    elon = accounts["elon"]
    throwaway = accounts["throwaway42"]

    tweet = TwitterPost(
        text=(
            "the fake post generator package is working\n\n"
            "9:16 vertical, transparent background, dim theme."
        ),
        account=elon,
        replies_count=1234,
        retweets=5678,
        likes=98765,
        views=1_200_000,
        time="11:25 AM",
        date="May 8, 2026",
    )

    # All three Twitter variants × three themes × transparent vs theme bg.
    for variant in ("full", "compact", "badge"):
        for theme in ("light", "dim", "dark"):
            for bg in ("theme", "transparent"):
                layout = LayoutConfig(
                    width=600, theme=theme, background=bg, scale=2.0
                )
                png = tweet.render(variant=variant, layout=layout)
                (OUT / f"twitter-{variant}-{theme}-{bg}.png").write_bytes(png)

    # Granular custom layout: 9:16-friendly badge, larger fonts.
    custom = LayoutConfig(
        width=720, theme="dim", background="transparent", font_scale=1.4, scale=2.0
    )
    (OUT / "twitter-badge-9x16.png").write_bytes(
        tweet.render(variant="badge", layout=custom)
    )

    # Reddit
    rpost = RedditPost(
        title="Anyone else generating fake posts in pure python?",
        body=(
            "Built a small package that mocks tweets and reddit posts as PNG. "
            "Works headless via playwright. AMA."
        ),
        account=throwaway,
        subreddit="r/Python",
        upvotes=2400,
        comments=312,
        flair="Showcase",
        timestamp="3h ago",
    )
    for variant in ("full", "compact", "badge"):
        for theme in ("light", "dark"):
            layout = LayoutConfig(width=640, theme=theme, background="theme")
            (OUT / f"reddit-{variant}-{theme}.png").write_bytes(
                rpost.render(variant=variant, layout=layout)
            )

    # Inline-defined account (no yaml).
    adhoc = AccountProfile(id="anon", name="Anonymous", handle="anon")
    (OUT / "twitter-adhoc-badge.png").write_bytes(
        TwitterPost(text="hi", account=adhoc).render(variant="badge")
    )

    print(f"wrote {len(list(OUT.glob('*.png')))} pngs to {OUT}")


if __name__ == "__main__":
    main()
