"""Random "bank" of commenter accounts for populating replies.

User-supplied text always wins; this module only randomizes metadata
(display name, handle, avatar, upvote counts, timestamps).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from .account import AccountProfile, load_accounts
from .banks import AVATARS_DIR
from .banks.default_names import HANDLES, NAMES


def _list_default_avatars() -> list[Path]:
    """Return the sorted list of bundled avatar PNGs (one per persona slot)."""
    return sorted(AVATARS_DIR.glob("*.png"))


@dataclass
class AccountBank:
    """Random pool of accounts used to populate fake replies/comments.

    The bank either holds a list of curated entries (loaded from a YAML via
    :func:`account_bank`) or, when ``entries`` is empty, falls back to the
    bundled default name + avatar pool. Use ``rng=Random(seed)`` for
    reproducible picks.

    Attributes:
        entries: Optional curated `AccountProfile` list to pick from.
        rng: A `random.Random` instance — pass a seeded one for determinism.
    """

    entries: list[AccountProfile] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)

    def pick(self) -> AccountProfile:
        """Return one random account (with replacement)."""
        if self.entries:
            return self.rng.choice(self.entries)
        return self._pick_default()

    def pick_many(self, count: int, unique: bool = True) -> list[AccountProfile]:
        """Return ``count`` random accounts.

        Args:
            count: How many accounts to return.
            unique: If True (default), sample without replacement when the
                pool is large enough. If the pool is too small, falls back
                to allowing repeats silently.
        """
        if not self.entries:
            return self._pick_default_many(count, unique=unique)
        if unique and count <= len(self.entries):
            return self.rng.sample(self.entries, count)
        return [self.rng.choice(self.entries) for _ in range(count)]

    def _pick_default_many(self, count: int, *, unique: bool) -> list[AccountProfile]:
        """Generate `count` random accounts from the bundled default pool.

        When `unique` is True and the bundled pools are large enough, samples
        each axis (handle / name / avatar) without replacement so all `count`
        accounts are visually distinct.
        """
        avatars = _list_default_avatars()
        if unique and count <= min(len(HANDLES), len(NAMES), len(avatars) or 1):
            handles = self.rng.sample(HANDLES, count)
            names = self.rng.sample(NAMES, count)
            avs = self.rng.sample(avatars, count) if avatars else [None] * count
            return [
                AccountProfile(
                    id=f"random:{h}", name=n, handle=h,
                    avatar=str(a) if a else None, verified=None,
                )
                for h, n, a in zip(handles, names, avs)
            ]
        return [self._pick_default() for _ in range(count)]

    def _pick_default(self) -> AccountProfile:
        """Generate one random account from the bundled default pool.

        Independent draws on each axis — does not dedupe across calls.
        """
        handle = self.rng.choice(HANDLES)
        name = self.rng.choice(NAMES)
        avatars = _list_default_avatars()
        avatar = str(self.rng.choice(avatars)) if avatars else None
        return AccountProfile(
            id=f"random:{handle}",
            name=name,
            handle=handle,
            avatar=avatar,
            verified=None,
        )


def account_bank(
    path: Optional[Path] = None,
    seed: Optional[int] = None,
) -> AccountBank:
    """Build an :class:`AccountBank` from bundled defaults or a YAML file.

    Args:
        path: When ``None`` (the default), the returned bank picks from the
            bundled name + avatar pools. When given a path, loads accounts
            from a YAML in the same schema as ``accounts.yaml``; entries with
            no ``avatar`` field get a random bundled avatar so renders never
            fail to find an image.
        seed: Optional integer to seed the bank's RNG. Same seed → same picks.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    if path is None:
        return AccountBank(entries=[], rng=rng)

    accounts_dict = load_accounts(path)
    entries = list(accounts_dict.values())

    # Fill missing avatars from the bundled pool so renders never break.
    avatars = _list_default_avatars()
    for acc in entries:
        if not acc.avatar and avatars:
            acc.avatar = str(rng.choice(avatars))

    return AccountBank(entries=entries, rng=rng)


@dataclass
class ReplyTemplate:
    """User-controlled spec for a single reply / comment.

    Only ``text`` is required — everything else is optional and gets filled
    from the bank / randomization controls passed to :func:`build_replies`.
    Pass an explicit ``account`` to pin a specific persona (e.g. the OP).

    Attributes:
        text: Body text for Reddit, tweet text for Twitter. Always honored.
        account: Override the random account pick.
        upvotes: Override the random upvote count.
        timestamp: Override the random timestamp.
        op: Mark this comment as authored by the post's OP (Reddit only).
        edited: Show the "edited" marker (Reddit only).
        extras: Free-form passthrough kwargs that get forwarded to the
            model class constructor — useful for fields not covered above.
    """

    text: str
    account: Optional[AccountProfile] = None
    upvotes: Optional[int] = None
    timestamp: Optional[str] = None
    op: bool = False
    edited: bool = False
    extras: dict[str, Any] = field(default_factory=dict)


def _coerce_template(item: Any) -> ReplyTemplate:
    """Normalize a reply spec to a :class:`ReplyTemplate`.

    Accepts ``str`` (just the text), ``dict`` (matching the dataclass fields,
    plus extras), or an existing :class:`ReplyTemplate`. Anything else raises
    `TypeError`.
    """
    if isinstance(item, ReplyTemplate):
        return item
    if isinstance(item, str):
        return ReplyTemplate(text=item)
    if isinstance(item, dict):
        return ReplyTemplate(
            text=item.pop("text"),
            account=item.pop("account", None),
            upvotes=item.pop("upvotes", None),
            timestamp=item.pop("timestamp", None),
            op=item.pop("op", False),
            edited=item.pop("edited", False),
            extras=item,
        )
    raise TypeError(f"reply must be str | dict | ReplyTemplate, got {type(item).__name__}")


def build_replies(
    items: Iterable[Any],
    *,
    model_cls,
    bank: Optional[AccountBank] = None,
    upvotes_range: tuple[int, int] = (1, 500),
    timestamps: Optional[list[str]] = None,
    seed: Optional[int] = None,
    unique_per_thread: bool = True,
) -> list[Any]:
    """Convert a list of reply specs into a list of ``model_cls`` instances.

    ``model_cls`` is the platform's content class — :class:`RedditPost` or
    :class:`TwitterPost`. Each item in ``items`` may be:

    - ``str``           — just the body text; everything else is randomized.
    - ``dict``          — keys ``text`` (required), ``account``, ``upvotes``,
      ``timestamp``, ``op``, ``edited``; any other keys are forwarded to the
      model constructor as-is (``extras``).
    - :class:`ReplyTemplate` — pre-constructed spec.

    User-supplied fields always win. Anything missing is filled from the
    bank (account) and from the ``upvotes_range`` / ``timestamps`` controls.

    Args:
        items: Iterable of reply specs.
        model_cls: ``RedditPost`` or ``TwitterPost``. Determines the keyword
            mapping (``body=`` vs ``text=``, etc.).
        bank: Optional :class:`AccountBank`. Defaults to the bundled pool.
        upvotes_range: Inclusive ``(low, high)`` range for random vote
            counts. Used for both Reddit upvotes and Twitter likes.
        timestamps: Optional list of timestamp strings to choose from.
        seed: Optional RNG seed for the local generator (numbers and any
            time-stamp choice). Note: a separate seed lives on the bank.
        unique_per_thread: When True (default), pre-allocates a unique
            account pool large enough to fill all auto-assigned replies in
            this call so accounts don't repeat. Falls back silently to
            allowing repeats if the pool is too small.

    Returns:
        A new list of ``model_cls`` instances, in input order.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    bank = bank or AccountBank(rng=rng)
    coerced = [_coerce_template(raw) for raw in items]

    # Pre-allocate a unique account pool when requested, so two replies in
    # the same call never share an account (unless the bank is too small).
    n_needed = sum(1 for tpl in coerced if tpl.account is None)
    auto_accounts = (
        bank.pick_many(n_needed, unique=True) if unique_per_thread and n_needed else []
    )
    auto_iter = iter(auto_accounts)
    out = []
    for tpl in coerced:
        if tpl.account is not None:
            account = tpl.account
        elif unique_per_thread:
            account = next(auto_iter)
        else:
            account = bank.pick()
        upvotes = tpl.upvotes if tpl.upvotes is not None else rng.randint(*upvotes_range)
        timestamp = tpl.timestamp
        if timestamp is None and timestamps:
            timestamp = rng.choice(timestamps)

        # `model_cls` may be RedditPost (body=...) or TwitterPost (text=...).
        kwargs = dict(tpl.extras)
        kwargs["account"] = account
        if "RedditPost" in model_cls.__name__:
            kwargs["body"] = tpl.text
            kwargs["upvotes"] = upvotes
            if timestamp is not None:
                kwargs["timestamp"] = timestamp
            kwargs["op"] = tpl.op
            kwargs["edited"] = tpl.edited
        else:  # TwitterPost
            kwargs["text"] = tpl.text
            kwargs["likes"] = upvotes  # reuse the range for likes on twitter
            if timestamp is not None:
                kwargs["time"] = timestamp
        out.append(model_cls(**kwargs))
    return out
