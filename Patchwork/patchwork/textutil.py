"""Small text helpers: articles, list joining, wrapping and terminal styling."""

import os
import re
import shutil
import sys
import textwrap

_VOWEL_SOUND_EXCEPTIONS_AN = ("hour", "honest", "honor", "honour", "heir")
_VOWEL_SOUND_EXCEPTIONS_A = ("uni", "use", "usu", "eu", "one", "once", "ure", "uti")


def a_an(word):
    """Return 'a' or 'an' for *word* (best-effort English heuristic)."""
    w = word.strip().lower()
    if not w:
        return "a"
    if w.startswith(_VOWEL_SOUND_EXCEPTIONS_AN):
        return "an"
    if w.startswith(_VOWEL_SOUND_EXCEPTIONS_A):
        return "a"
    return "an" if w[0] in "aeiou" else "a"


def cap(text):
    """Capitalise the first visible letter, leaving the rest alone."""
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i + 1:]
        if ch.isdigit():
            return text
    return text


def join_list(items, conj="and"):
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return "%s %s %s" % (items[0], conj, items[1])
    return "%s, %s %s" % (", ".join(items[:-1]), conj, items[-1])


def group_names(entities):
    """['a coin', 'a coin', 'a key'] style listing with duplicates folded: 'a coin (x2)'."""
    order, counts = [], {}
    for e in entities:
        label = e.a()
        if label not in counts:
            order.append(label)
            counts[label] = 0
        counts[label] += 1
    return [l if counts[l] == 1 else "%s (x%d)" % (l, counts[l]) for l in order]


def pluralize(word):
    if not word:
        return word
    lower = word.lower()
    if lower.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    if lower.endswith("y") and len(lower) > 1 and lower[-2] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


_WS = re.compile(r"[ \t]+")


def tidy(text):
    """Collapse runs of spaces and fix spacing before punctuation."""
    text = _WS.sub(" ", text)
    text = re.sub(r" +([,.;:!?])", r"\1", text)
    return text.strip()


# --------------------------------------------------------------------------
# Terminal styling
# --------------------------------------------------------------------------

_STYLES = {
    "title": "\033[1;36m",
    "room": "\033[1;37m",
    "exit": "\033[32m",
    "dim": "\033[2m",
    "warn": "\033[33m",
    "error": "\033[31m",
    "story": "\033[35m",
    "prompt": "\033[1;33m",
    "bold": "\033[1m",
    "good": "\033[1;32m",
}
_RESET = "\033[0m"


def color_enabled(stream=None):
    stream = stream or sys.stdout
    if os.environ.get("NO_COLOR") or os.environ.get("PATCHWORK_NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def style(text, kind, enabled=True):
    if not enabled or kind not in _STYLES:
        return text
    return _STYLES[kind] + text + _RESET


def term_width(default=80):
    try:
        width = shutil.get_terminal_size((default, 24)).columns
    except OSError:
        width = default
    return max(40, min(width, 100))


def wrap(text, width=None):
    """Wrap text paragraph-by-paragraph, keeping explicit newlines."""
    width = width or term_width()
    out = []
    for para in text.split("\n"):
        if not para.strip():
            out.append("")
            continue
        indent = len(para) - len(para.lstrip(" "))
        out.append(textwrap.fill(para.strip(), width=width,
                                 initial_indent=" " * indent,
                                 subsequent_indent=" " * indent))
    return "\n".join(out)
