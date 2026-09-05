"""Deterministic catalog knowledge derived from item names — never the LLM's job.

Per PRD §6, anything that decides what's sellable, at what price, or in
what quantity is plain Python. This currently covers one rule: an item
named "... (Box of N)" is sold in packs of N, worth surfacing to the
buyer when quoting so a bare number like "10" is never silently ambiguous
between 10 units and 10 boxes.
"""

import re

_BOX_PATTERN = re.compile(r"box of (\d+)", re.IGNORECASE)


def pack_size(item_name: str) -> int | None:
    """The pack size for a '... (Box of N)' item, or None for a loose/unpacked one."""
    match = _BOX_PATTERN.search(item_name)
    return int(match.group(1)) if match else None
