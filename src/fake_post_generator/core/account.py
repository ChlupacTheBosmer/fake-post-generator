"""Reusable per-account profile loaded from YAML.

An ``AccountProfile`` packages everything the renderer needs to know about
*who* is posting: display name, handle, avatar (path or URL), verification
state, and optional platform-specific defaults. Profiles are typically loaded
from a YAML file so the same persona can be reused across many renders.

Default lookup order when no path is supplied to :func:`load_accounts`:

1. ``~/.fake_post_generator/accounts.yaml``  (global, machine-wide)
2. ``./accounts.yaml``                       (project-local — overrides global)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


DEFAULT_GLOBAL = Path.home() / ".fake_post_generator" / "accounts.yaml"
DEFAULT_LOCAL = Path("accounts.yaml")


@dataclass
class AccountProfile:
    """A single account that can post on any registered platform.

    Attributes:
        id: Stable account key (e.g. the YAML map key). Used as a handle in
            error messages and for cross-referencing.
        name: Display name shown in the rendered post header.
        handle: The ``@handle`` (Twitter) or ``u/handle`` (Reddit) shown
            below the display name. Stored without prefix.
        avatar: Path or URL to a profile image. ``None`` falls back to the
            platform's bundled default avatar.
        verified: ``"blue"`` / ``"gold"`` / ``None``. Twitter only — Reddit
            ignores this field.
        platform_defaults: Optional per-platform defaults that callers can
            merge into their post construction (e.g. a default subreddit on
            Reddit). Not applied automatically — see USAGE for patterns.
    """

    id: str
    name: str
    handle: str
    avatar: Optional[str] = None
    verified: Optional[str] = None
    platform_defaults: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, account_id: str, data: dict[str, Any]) -> "AccountProfile":
        """Construct an ``AccountProfile`` from one YAML map entry.

        Args:
            account_id: The top-level YAML key (used as ``id``).
            data: The mapping value containing ``name`` / ``handle`` /
                optional ``avatar`` / ``verified`` / ``platform_defaults``.
        """
        return cls(
            id=account_id,
            name=data["name"],
            handle=data["handle"],
            avatar=data.get("avatar"),
            verified=data.get("verified"),
            platform_defaults=data.get("platform_defaults", {}),
        )

    @classmethod
    def load(cls, account_id: str, *paths: Path) -> "AccountProfile":
        """Look up one account by id from the merged YAML files.

        Equivalent to ``load_accounts(*paths)[account_id]`` with a clearer
        error message when the account is missing.

        Raises:
            KeyError: If `account_id` doesn't exist in any of the searched
                files.
        """
        accounts = load_accounts(*paths)
        if account_id not in accounts:
            searched = paths or (DEFAULT_GLOBAL, DEFAULT_LOCAL)
            raise KeyError(
                f"account {account_id!r} not found in: "
                + ", ".join(str(p) for p in searched)
            )
        return accounts[account_id]


def load_accounts(*paths: Path) -> dict[str, AccountProfile]:
    """Load and merge YAML account files into ``{id: AccountProfile}``.

    Files are read in order — later files **override** earlier entries with
    the same key (project-local YAML wins over the global default).

    With no args, reads the global file then a project-local file (see module
    docstring). Pass explicit `paths` to load from non-default locations:

        accounts = load_accounts(Path("examples/accounts.yaml"))
    """
    sources = paths or (DEFAULT_GLOBAL, DEFAULT_LOCAL)
    out: dict[str, AccountProfile] = {}
    for path in sources:
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text()) or {}
        for account_id, raw in data.items():
            out[account_id] = AccountProfile.from_dict(account_id, raw)
    return out
