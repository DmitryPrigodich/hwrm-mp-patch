"""Detect the specific prose glue found in review; allow IDs, HW2 and Lua4."""

from tool_safety import ensure_normal_python

ensure_normal_python()
import re

PROTECTED = re.compile(r"```[\s\S]*?```|`[^`]*`|https?://\S+|\]\([^)]*\)")
GLUE = re.compile(r"\b(?:build\d+|(?:Hiigaran|Vaygr)\d|multiplier\d|old\d|Current\d+)")


def glued_prose(text):
    text = PROTECTED.sub("", text)
    return [match.group() for match in GLUE.finditer(text)]
