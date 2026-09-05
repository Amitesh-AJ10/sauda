"""Deterministic guardrail checks and pricing math.

Per PRD §6: the LLM never states SLAs or warranties, and never computes the
final price — everything here is plain Python, testable without an LLM.
"""

import re

# Tiered bulk discount off list price, keyed by minimum qty. Larger orders
# get a better rate. This *is* the "approved price band" the LLM is told
# about — it never chooses the number itself.
DISCOUNT_TIERS: list[tuple[int, float]] = [
    (500, 0.10),
    (100, 0.06),
    (20, 0.03),
    (0, 0.0),
]

# The floor of what a human merchant could plausibly approve, regardless of
# tier math — used to clamp any LLM-proposed figure back into range.
MAX_DISCOUNT = 0.10

FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"deliver(?:ed|y)?\s+in\s+\d+", re.IGNORECASE),
    re.compile(r"\bguarantee[sd]?\b", re.IGNORECASE),
    re.compile(r"\bwarrant(?:y|ies)\b", re.IGNORECASE),
    re.compile(r"\bSLA\b", re.IGNORECASE),
    re.compile(r"\bpromise[sd]?\b", re.IGNORECASE),
]

# Deterministic pre-LLM filter: catches a buyer message trying to override
# Sauda's role/instructions rather than the LLM's own phrasing. A hit here
# is decided by Python before the message ever reaches the LLM — see
# `nodes.guard_input`, which short-circuits the whole graph on a match.
INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+|any\s+|previous\s+|prior\s+)*instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"\byou are now\b", re.IGNORECASE),
    re.compile(r"disregard (your|all)\s+(rules|guardrails|instructions)", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    re.compile(r"reveal (your|the)\s+(prompt|instructions)", re.IGNORECASE),
    re.compile(r"pretend (you('re| are)|to be)", re.IGNORECASE),
    re.compile(r"\bDAN\b"),  # common "Do Anything Now" jailbreak handle
    re.compile(r"\bfor free\b", re.IGNORECASE),
]


def price_band(base_price: float) -> tuple[float, float]:
    """The (min, max) unit price a deal may legally settle at."""
    return round(base_price * (1 - MAX_DISCOUNT), 2), base_price


def compute_unit_price(base_price: float, qty: int) -> float:
    """The deterministic, tiered-discount unit price for a given quantity."""
    discount = next(rate for threshold, rate in DISCOUNT_TIERS if qty >= threshold)
    return round(base_price * (1 - discount), 2)


def clamp_price(price: float, base_price: float) -> float:
    """Clamp a (possibly LLM-proposed) price into the approved band."""
    min_price, max_price = price_band(base_price)
    return min(max(price, min_price), max_price)


def check_text_guardrails(text: str) -> list[str]:
    """Return the forbidden phrases found in `text` (empty if clean)."""
    return [pattern.pattern for pattern in FORBIDDEN_PATTERNS if pattern.search(text)]


def check_prompt_injection(text: str) -> list[str]:
    """Return the jailbreak/prompt-injection patterns found in a buyer's raw message."""
    return [pattern.pattern for pattern in INJECTION_PATTERNS if pattern.search(text)]
