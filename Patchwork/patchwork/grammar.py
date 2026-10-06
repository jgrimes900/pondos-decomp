"""A small Tracery-style text grammar used to generate novel names and prose.

Syntax inside any text:

    #symbol#                expand a random rule for *symbol*
    #symbol.cap#            ...and apply modifiers (cap, a, s, upper, lower, title, the)
    [name:#symbol#]         expand once and remember it as *name* for this expansion,
                            later #name# repeats the same value
    \\#                      a literal '#'

Rules from every loaded mod are merged, so one mod can add words to another
mod's vocabulary simply by defining the same symbol.

A scope (see Grammar.scoped) lays extra rules over the global ones for a while:
the world generator uses it so a tile's biomes decide what #floor# or #tree#
means there.  A blended tile (the edge of a forest and a plain) gets the rules of
both, so its descriptions mix them.
"""

import contextlib
import re

from . import textutil

_SYMBOL = re.compile(r"(?<!\\)#([A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_]+)*)#")
_ACTION = re.compile(r"\[([A-Za-z0-9_\-]+):([^\[\]]*)\]")

MAX_DEPTH = 24


def _apply_modifier(value, mod):
    if mod in ("cap", "capitalize"):
        return textutil.cap(value)
    if mod == "a":
        return "%s %s" % (textutil.a_an(value), value) if value else value
    if mod == "s":
        return textutil.pluralize(value)
    if mod == "upper":
        return value.upper()
    if mod == "lower":
        return value.lower()
    if mod == "title":
        return " ".join(textutil.cap(w) for w in value.split(" "))
    if mod == "the":
        return "the " + value if value else value
    return value


class Grammar:
    def __init__(self, rules, rng):
        self.rules = {}
        for key, val in (rules or {}).items():
            if isinstance(val, str):
                val = [val]
            self.rules[key] = list(val)
        self.rng = rng
        self.missing = set()
        self.overlay = {}

    @contextlib.contextmanager
    def scoped(self, rules):
        """Lay *rules* ({symbol: [options]}) over the global grammar inside a with-block."""
        saved = self.overlay
        merged = dict(saved)
        for key, val in (rules or {}).items():
            merged[key] = list(val) if isinstance(val, list) else [val]
        self.overlay = merged
        try:
            yield self
        finally:
            self.overlay = saved

    def options(self, symbol):
        return self.overlay.get(symbol) or self.rules.get(symbol)

    def has(self, symbol):
        return bool(self.options(symbol))

    def expand(self, text, saved=None, depth=0):
        if not isinstance(text, str) or ("#" not in text and "[" not in text):
            return text
        if saved is None:
            saved = {}
        if depth > MAX_DEPTH:
            return text

        def do_action(m):
            saved[m.group(1)] = self.expand(m.group(2), saved, depth + 1)
            return ""

        text = _ACTION.sub(do_action, text)

        def do_symbol(m):
            parts = m.group(1).split(".")
            name, mods = parts[0], parts[1:]
            if name in saved:
                value = saved[name]
            else:
                options = self.options(name)
                if not options:
                    self.missing.add(name)
                    value = name.replace("_", " ")
                else:
                    value = self.expand(self.rng.choice(options), saved, depth + 1)
            for mod in mods:
                value = _apply_modifier(value, mod)
            return value

        text = _SYMBOL.sub(do_symbol, text)
        return text.replace("\\#", "#") if depth == 0 else text
