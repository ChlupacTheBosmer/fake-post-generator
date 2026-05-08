"""Bundled name pools used as fallbacks when generating random commenter accounts.

The user's text content is never randomized — only metadata (display name,
handle, avatar) and numeric stats. The pools are intentionally small/generic.
"""

from __future__ import annotations

# Reddit/X-style handles (lowercase, sometimes a numeric or word suffix).
HANDLES = [
    "alex_99", "northern_lights", "bobby_tables", "throwawayacc",
    "mr_pickles", "celery_man", "polar_bear", "yellowjacket42",
    "lazysunday", "grumpybear", "cosmiccrab", "phantompenguin",
    "rusty_bolt", "midnight_owl", "wandering_oak", "the_real_dave",
    "captainquack", "nimbus3000", "echo_chamber", "binary_dust",
    "stardust_88", "hopeful_potato", "ironpenguin", "sundownkid",
    "blue_october", "silent_lemon", "redditor7777", "throwaway_99",
    "moonshot22", "verdant_fern",
]

# Display names (real-name-ish; mix of casual and formal).
NAMES = [
    "Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Drew",
    "Riley", "Quinn", "Avery", "Jamie", "Robin", "Skyler",
    "Emma Stone", "James Reid", "Maya Patel", "Liam Foster",
    "Olivia Park", "Ben Carter", "Aisha Khan", "Daniel Kim",
    "Sofia Reyes", "Isaac Wong", "Nina Ortiz", "Marcus Hill",
    "Zoe Hayes", "Felix Tran", "Lila Stone", "Noah Webb",
]
