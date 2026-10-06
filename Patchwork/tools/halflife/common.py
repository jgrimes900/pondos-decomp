"""Helpers for building the Half-Life mods' JSON from compact Python specs.

Run tools/halflife/build.py to regenerate mods/hl_*/.  The generated JSON is the
mod; these scripts just keep ~200 hand-written rooms consistent.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east",
            "northeast": "southwest", "southwest": "northeast", "northwest": "southeast",
            "southeast": "northwest", "up": "down", "down": "up", "in": "out", "out": "in"}


STATS = ("health", "max_health", "damage", "armor", "heal", "charge")
HL_SCALE = 100   # every Half-Life number is written for a player with 100 health


def declare_scale(obj, base=HL_SCALE):
    """Stamp default_max_health on every stat block, so Steel & Peril can convert Half-Life's
    numbers when the world's player has a different base max health (and convert other mods'
    numbers to Half-Life's)."""
    if isinstance(obj, dict):
        props = obj.get("props")
        if isinstance(props, dict) and any(k in props for k in STATS) and "default_max_health" not in props:
            obj["props"] = dict({"default_max_health": base}, **props)
        for v in obj.values():
            declare_scale(v, base)
    elif isinstance(obj, list):
        for v in obj:
            declare_scale(v, base)
    return obj


class ModBuilder:
    def __init__(self, mod_id, prefix):
        self.mod_id = mod_id
        self.prefix = prefix
        self.rooms = {}
        self.sections = {}
        self.chapter = None
        self.chapter_seen = set()

    def section(self, name):
        return self.sections.setdefault(name, {})

    # -- rooms ---------------------------------------------------------
    def rid(self, short):
        return short if "/" in short else self.prefix + short

    def set_chapter(self, title):
        self.chapter = title

    def room(self, short, name, desc, *, after=None, feats=(), tags=(), map=None, brief=None,
             expand=None, enter=None, props=None, aliases=(), flag="hl_cascade", actions=None):
        rid = self.rid(short)
        assert rid not in self.rooms, "duplicate room " + rid
        d = {"name": name, "tags": list(tags), "exits": [], "features": list(feats)}
        if after:
            d["description"] = [{"if": {"flag": flag}, "text": after}, {"text": desc}]
        else:
            d["description"] = desc
        if brief:
            d["brief"] = brief
        if aliases:
            d["aliases"] = list(aliases)
        p = {"map": map or "", "chapter": self.chapter or ""}
        p.update(props or {})
        d["props"] = p
        hooks = []
        if self.chapter and self.chapter not in self.chapter_seen:
            self.chapter_seen.add(self.chapter)
            hooks.append({"if": {"local": "first"}, "then": [{"say": self.chapter.upper(), "style": "title"}]})
        if enter:
            hooks.extend(enter)
        if hooks:
            d["on_enter"] = hooks
        if expand:
            d["expansions"] = expand if isinstance(expand, list) else [expand]
        if actions:
            d["actions"] = actions
        self.rooms[rid] = d
        return rid

    def link(self, a, b, d, dist=1, back=None, name=None, aliases=None, desc=None, back_desc=None,
             oneway=False, cond=None, blocked=None, back_name=None, solve=None):
        a, b = self.rid(a), self.rid(b)
        ex = {"to": b, "dir": d, "distance": dist}
        if name:
            ex["name"] = name
        if aliases:
            ex["aliases"] = aliases
        if desc:
            ex["description"] = desc
        if cond:
            ex["if"] = cond
        if blocked:
            ex["blocked"] = blocked
        if solve:
            # Not used by the engine: tells automated players (tests) how to open a scripted gate.
            ex["solve"] = solve
        ex["back"] = False   # the reverse exit is written explicitly below
        self.rooms[a]["exits"].append(ex)
        if not oneway:
            bd = back if back is not None else OPPOSITE.get(d)
            bex = {"to": a, "dir": bd, "distance": dist, "back": False}
            if back_name:
                bex["name"] = back_name
            if back_desc:
                bex["description"] = back_desc
            self.rooms[b]["exits"].append(bex)

    def chain(self, shorts, d, dist=1):
        for x, y in zip(shorts, shorts[1:]):
            self.link(x, y, d, dist)

    # -- output --------------------------------------------------------
    def check(self):
        problems = []
        for rid, r in self.rooms.items():
            dirs = [e["dir"] for e in r["exits"] if e.get("dir")]
            dup = {x for x in dirs if dirs.count(x) > 1}
            if dup:
                problems.append("%s: duplicate exits %s" % (rid, sorted(dup)))
            for e in r["exits"]:
                if e["to"] not in self.rooms:
                    problems.append("%s: exit to unknown %s" % (rid, e["to"]))
        return problems

    def write(self, manifest, files):
        out = os.path.join(ROOT, "mods", self.mod_id)
        os.makedirs(out, exist_ok=True)
        for name in os.listdir(out):
            if name.endswith(".json"):
                os.remove(os.path.join(out, name))
        with open(os.path.join(out, "mod.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        for fname, content in files.items():
            declare_scale(content)
            with open(os.path.join(out, fname), "w", encoding="utf-8") as fh:
                json.dump(content, fh, indent=1, ensure_ascii=False)
                fh.write("\n")


def weapon(name, aliases, damage, desc, tags=(), affords=(), extra=None, ammo=None):
    """ammo: consumer props (core's consumer trait), e.g. gun("9mm", 17) or throwable("grenades")."""
    d = {"extends": ["portable"], "name": name, "aliases": aliases, "tags": ["weapon", "hl_weapon"] + list(tags),
         "props": {"damage": damage}, "description": desc, "story_keep": True}
    if ammo:
        d["extends"] = ["portable", "consumer"]
        d["props"].update(ammo)
    d["affords"] = list(affords) + ["fight"]   # so the story planner can arm you before a boss
    if extra:
        d.update(extra)
    return d


def gun(kind, capacity, label="rounds"):
    """A magazine of `capacity`, reloaded (automatically when it runs dry) from carried ammo of `kind`."""
    return {"resource": "ammo", "resource_type": kind, "capacity": capacity, "feed": "auto", "label": label}


def direct(kind, cost, label):
    """No magazine: every shot draws `cost` straight from the carried ammo of `kind`."""
    return {"resource": "ammo", "resource_type": kind, "cost": cost, "feed": "direct", "label": label}


def throwable(label, capacity=1, empty="{self.The} is gone."):
    """Thrown or planted: used up when the last one goes."""
    return {"resource": "ammo", "resource_type": "none", "capacity": capacity, "reloadable": False,
            "on_empty": "consume", "label": label, "depleted_text": empty}


def creature(name, aliases, health, damage, attack, desc, appearance, *, habitat=(), encounter=True,
             tags=(), death=None, extends=("hostile",), extra=None, weight=1, min_stage=0, armor=0):
    d = {"extends": list(extends), "name": name, "aliases": aliases,
         "tags": (["encounter"] if encounter else []) + ["hl_creature"] + list(tags),
         "props": {"health": health, "max_health": health, "damage": damage, "armor": armor,
                   "attack_text": attack},
         "description": desc, "appearance": appearance}
    if death:
        d["props"]["death_text"] = death
    if habitat:
        d["habitat"] = list(habitat)
    if weight != 1:
        d["weight"] = weight
    if min_stage:
        d["min_stage"] = min_stage
    if extra:
        d.update(extra)
    return d
