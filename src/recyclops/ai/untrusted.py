"""User-typed text (member names, questions) is data, never instructions.

It reaches prompts with markup and control characters removed, so it can't close a tag, break the
JSON around it, or pass for part of the instructions.
"""

import re

_MARKUP = re.compile(r"[<>{}\[\]`\\]|[\x00-\x1f\x7f]")


def sanitize(text: str) -> str:
    """Remove markup and control characters, and collapse whitespace."""
    return " ".join(_MARKUP.sub(" ", text).split())


def fence(tag: str, text: str, empty: str) -> str:
    """`<tag>clean text</tag>`, or the `empty` placeholder inside the tags."""
    return f"<{tag}>{sanitize(text) or empty}</{tag}>"
