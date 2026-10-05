"""Runtime world model.

Everything in the world is an :class:`Entity`.  A room is simply an entity
with exits and no parent; everything inside a room (furniture, items,
characters, the player) is an entity nested under it, and entities can nest
arbitrarily deep (a room contains a desk, which contains a drawer, which
contains a letter...).
"""

import copy
import random

from . import textutil
from .grammar import Grammar
from .mods import Registry

# Keys in a feature spec that control *how* it is spawned rather than *what*.
SPEC_CONTROL_KEYS = {"chance", "count", "pick", "pick_tag", "id", "def", "unique", "as", "if"}

# Keys whose values are combined (rather than replaced) through "extends".
_UNION_LIST_KEYS = ("tags", "aliases")
_CONCAT_LIST_KEYS = ("features",)
_DICT_KEYS = ("props",)


def normalize_handlers(v):
    """Turn any action value into a list of handler dicts {"if", "do", "else"}.

    An action may be written as a single effect, a list of effects, a single
    handler ({"if": ..., "do": ...}) or a list of handlers (every element a dict
    with a "do" key).
    """
    if v is None:
        return []
    if isinstance(v, dict):
        return [v] if "do" in v else [{"do": [v]}]
    if isinstance(v, str):
        return [{"do": [v]}]
    if isinstance(v, list):
        if v and all(isinstance(x, dict) and "do" in x for x in v):
            return list(v)
        return [{"do": v}]
    return []


def merge_def(parent, child):
    """Combine a parent definition with a child that extends it."""
    out = copy.deepcopy(parent)
    out.pop("abstract", None)
    for key, val in child.items():
        if key in _UNION_LIST_KEYS:
            cur = list(out.get(key) or [])
            for v in val or []:
                if v not in cur:
                    cur.append(v)
            out[key] = cur
        elif key in _CONCAT_LIST_KEYS:
            out[key] = list(out.get(key) or []) + list(copy.deepcopy(val) or [])
        elif key in _DICT_KEYS:
            cur = dict(out.get(key) or {})
            cur.update(copy.deepcopy(val) or {})
            out[key] = cur
        elif key == "actions":
            acts = dict(out.get("actions") or {})
            for verb, handlers in (val or {}).items():
                mine = normalize_handlers(handlers)
                theirs = normalize_handlers(acts.get(verb))
                # The child's handlers are tried first, then the parent's.
                acts[verb] = copy.deepcopy(mine) + theirs
            out["actions"] = acts
        elif key.startswith("on_") and isinstance(val, list):
            # Event hooks accumulate: parent hooks run, then the child's.
            out[key] = list(out.get(key) or []) + copy.deepcopy(val)
        else:
            out[key] = copy.deepcopy(val)
    return out


class Entity:
    __slots__ = ("uid", "def_id", "name", "article", "aliases", "tags", "props",
                 "parent", "children", "hidden", "is_room", "exits", "texts",
                 "area", "region", "stage", "visited", "actions", "profile")

    def __init__(self, uid, def_id):
        self.uid = uid
        self.def_id = def_id
        self.name = "thing"
        self.article = None   # None=auto a/an, ""=proper noun, "the", "some"...
        self.aliases = []
        self.tags = []
        self.props = {}
        self.parent = None
        self.children = []
        self.hidden = False
        self.is_room = False
        self.exits = []
        self.texts = {}
        self.area = None
        self.region = None
        self.stage = 0
        self.visited = False
        self.actions = {}     # handlers attached to this one instance by the story generator
        self.profile = {}     # rendered character profile (personality, motives...)

    # -- naming --------------------------------------------------------
    def a(self):
        if self.article == "":
            return self.name
        art = self.article if self.article is not None else textutil.a_an(self.name)
        return "%s %s" % (art, self.name)

    def the(self):
        if self.article == "":
            return self.name
        return "the " + self.name

    def has_tag(self, tag):
        return tag in self.tags

    def to_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}

    @classmethod
    def from_dict(cls, data):
        e = cls(data["uid"], data["def_id"])
        for k in cls.__slots__:
            if k in data:
                setattr(e, k, data[k])
        return e

    def __repr__(self):
        return "<%s %s '%s'>" % (self.uid, self.def_id, self.name)


class NullIO:
    """Output sink used when no terminal is attached (tests, generation)."""

    def __init__(self):
        self.lines = []

    def write(self, text, kind=None):
        self.lines.append(text)

    def choose(self, prompt, options):
        return 0


class World:
    def __init__(self, registry, seed=None):
        self.registry = registry
        self.seed = seed if seed is not None else random.randrange(1, 2 ** 31)
        self.rng = random.Random(self.seed)
        self.grammar = Grammar(registry["grammar"], self.rng)
        self.entities = {}
        self.defs = {}
        self.player_uid = None
        self.clock = 0
        self.turns = 0
        self.flags = set()
        self.vars = {}
        self.fired = set()           # ids of once-only rules that have fired
        self.journal = []
        self.story = {"title": "", "steps": [], "current": 0, "complete": False,
                      "cast": {}, "lore": {}, "lore_known": []}
        self.dynamic_rules = []      # rules created by the story generator
        self.areas = {}              # area id -> {"name":..., "rooms":[uids], "stage": n}
        self.spawn_counts = {}
        self.game_over = None        # None or {"text":..., "win": bool}
        self.verbose = False
        self._next = 0
        self.io = NullIO()
        self.logic = None            # set by logic.Interpreter
        self.interrupt = False
        self.last_target = None

    # -- helpers -------------------------------------------------------
    def setting(self, key, default=None):
        return self.registry["settings"].get(key, default)

    def string(self, key, default=""):
        return self.registry["strings"].get(key, default)

    def say(self, text, kind=None):
        if text is None:
            return
        self.io.write(text, kind)

    def new_uid(self, prefix="e"):
        self._next += 1
        return "%s%d" % (prefix, self._next)

    def get(self, uid):
        return self.entities.get(uid) if uid else None

    @property
    def player(self):
        return self.entities.get(self.player_uid)

    def room_of(self, ent):
        while ent is not None and not ent.is_room:
            ent = self.entities.get(ent.parent)
        return ent

    @property
    def room(self):
        return self.room_of(self.player)

    def rooms(self):
        return [e for e in self.entities.values() if e.is_room]

    def descendants(self, ent):
        out = []
        stack = list(reversed(ent.children))
        while stack:
            uid = stack.pop()
            child = self.entities.get(uid)
            if child is None:
                continue
            out.append(child)
            stack.extend(reversed(child.children))
        return out

    def ancestors(self, ent):
        out = []
        cur = self.entities.get(ent.parent)
        while cur is not None:
            out.append(cur)
            cur = self.entities.get(cur.parent)
        return out

    def is_inside(self, ent, container):
        return any(a.uid == container.uid for a in self.ancestors(ent))

    # -- definitions ---------------------------------------------------
    def def_key_for_room(self, room_id):
        return "room:" + room_id

    def resolve_def(self, key, _chain=()):
        """Return the fully merged definition for *key* (cached)."""
        if key in self.defs:
            return self.defs[key]
        if key in _chain:
            raise ValueError("circular 'extends' through %s" % " -> ".join(_chain + (key,)))
        if key.startswith("room:"):
            raw = self.registry["rooms"].get(key[5:])
        else:
            raw = self.registry["features"].get(key)
        if raw is None:
            return None
        parents = raw.get("extends") or []
        if isinstance(parents, str):
            parents = [parents]
        merged = {}
        for parent in parents:
            pkey = parent
            pdef = None
            if key.startswith("room:") and ("room:" + parent) not in _chain:
                pdef = self.resolve_def("room:" + parent, _chain + (key,))
                pkey = "room:" + parent
            if pdef is None:
                pdef = self.resolve_def(parent, _chain + (key,))
            if pdef is None:
                # Soft dependency: extending something from a mod that is not
                # loaded simply contributes nothing.
                continue
            merged = merge_def(merged, pdef)
        child = {k: v for k, v in raw.items() if k != "extends"}
        merged = merge_def(merged, child)
        merged["abstract"] = bool(raw.get("abstract"))
        merged["_id"] = key
        self.defs[key] = merged
        return merged

    def register_inline_def(self, spec, base=None):
        key = "~%d" % (len([k for k in self.defs if k.startswith("~")]) + 1)
        while key in self.defs:
            key += "x"
        merged = {}
        bases = base if isinstance(base, list) else ([base] if base else [])
        ext = spec.get("extends") or []
        bases += ext if isinstance(ext, list) else [ext]
        for b in bases:
            bdef = self.resolve_def(b)
            if bdef is not None:
                merged = merge_def(merged, bdef)
        child = {k: v for k, v in spec.items() if k not in SPEC_CONTROL_KEYS and k != "extends"}
        merged = merge_def(merged, child)
        merged["abstract"] = False
        merged["_id"] = key
        self.defs[key] = merged
        return key

    def def_of(self, ent):
        if ent is None:
            return {}
        return self.defs.get(ent.def_id) or self.resolve_def(ent.def_id) or {}

    def defs_with_tags(self, tags):
        tags = [tags] if isinstance(tags, str) else list(tags)
        out = []
        for fid in self.registry["features"]:
            d = self.resolve_def(fid)
            if d and not d.get("abstract") and all(t in (d.get("tags") or []) for t in tags):
                out.append(fid)
        return out

    def handlers(self, ent, verb, which="all"):
        """Handlers for *verb* on *ent*: instance (story) handlers first, then the definition's."""
        out = []
        if which in ("all", "instance"):
            out.extend(normalize_handlers((ent.actions or {}).get(verb)))
        if which in ("all", "def"):
            out.extend(normalize_handlers((self.def_of(ent).get("actions") or {}).get(verb)))
        return out

    def add_action(self, ent, verb, handler, first=True):
        """Attach a handler to one entity instance (used by the story generator)."""
        cur = ent.actions.setdefault(verb, [])
        if first:
            cur.insert(0, handler)
        else:
            cur.append(handler)

    def hook(self, ent, name):
        val = self.def_of(ent).get(name)
        if val is None:
            return []
        return val if isinstance(val, list) else [val]

    # -- instantiation -------------------------------------------------
    def _rand_value(self, val):
        if isinstance(val, dict) and set(val) == {"rand"}:
            lo, hi = val["rand"]
            if isinstance(lo, int) and isinstance(hi, int):
                return self.rng.randint(lo, hi)
            return round(self.rng.uniform(lo, hi), 2)
        if isinstance(val, dict) and set(val) == {"choose"}:
            return self.grammar.expand(self.rng.choice(val["choose"]))
        if isinstance(val, str):
            return self.grammar.expand(val)
        return copy.deepcopy(val)

    def _expand_text(self, val, saved):
        if isinstance(val, str):
            return self.grammar.expand(val, saved)
        if isinstance(val, list):
            out = []
            for v in val:
                if isinstance(v, dict):
                    v = dict(v)
                    if "text" in v:
                        v["text"] = self.grammar.expand(v["text"], saved)
                    out.append(v)
                else:
                    out.append(self.grammar.expand(v, saved))
            return out
        return val

    TEXT_KEYS = ("description", "appearance", "contents_text", "brief")

    def instantiate(self, def_key, parent=None, overrides=None, uid=None):
        d = self.resolve_def(def_key)
        if d is None:
            raise KeyError("unknown feature '%s'" % def_key)
        if d.get("abstract"):
            raise KeyError("'%s' is abstract (a trait) and cannot be placed" % def_key)
        if overrides:
            d = merge_def(d, overrides)
        is_room = def_key.startswith("room:") or bool(d.get("room"))
        ent = Entity(uid or self.new_uid("r" if is_room else "e"), def_key)
        saved = {}
        template = d.get("name") or def_key.split(":")[-1].replace("_", " ")
        ent.name = self.grammar.expand(template, saved)
        if d.get("profile") and "#" in template:
            # Two generated people with the same name would be impossible to tell apart.
            taken = {e.name for e in self.entities.values() if e.profile}
            for _ in range(12):
                if ent.name not in taken:
                    break
                saved = {}
                ent.name = self.grammar.expand(template, saved)
        ent.article = d.get("article")
        if d.get("proper"):
            ent.article = ""
        ent.tags = list(d.get("tags") or [])
        ent.props = {k: self._rand_value(v) for k, v in (d.get("props") or {}).items()}
        ent.hidden = bool(d.get("hidden"))
        ent.is_room = is_room
        for key in self.TEXT_KEYS:
            if key in d:
                ent.texts[key] = self._expand_text(d[key], saved)
        self.refresh_aliases(ent, d)
        if d.get("profile"):
            ent.profile = {k: self._expand_text(v, saved) for k, v in d["profile"].items()}
        self.entities[ent.uid] = ent
        self.spawn_counts[def_key] = self.spawn_counts.get(def_key, 0) + 1
        if parent is not None:
            self.place(ent, parent)
        for spec in d.get("features") or []:
            self.spawn_spec(spec, ent)
        return ent

    def refresh_aliases(self, ent, d=None):
        d = d if d is not None else self.def_of(ent)
        aliases = [a.lower() for a in d.get("aliases") or []]
        base = ent.name.lower()
        for word in [base] + base.split():
            if word not in aliases and word not in ("of", "the", "a", "an", "and", "in", "on"):
                aliases.append(word)
        ent.aliases = aliases

    def spawn_spec(self, spec, parent, ctx=None):
        """Instantiate a feature spec (see MODDING.md) inside *parent*."""
        out = []
        if spec is None:
            return out
        if isinstance(spec, list):
            for s in spec:
                out.extend(self.spawn_spec(s, parent, ctx))
            return out
        if isinstance(spec, str):
            spec = {"id": spec}
        if "if" in spec and self.logic is not None:
            if not self.logic.check(spec["if"], ctx or self.logic.ctx(self_ent=parent)):
                return out
        if "chance" in spec and self.rng.random() >= float(spec["chance"]):
            return out
        count = spec.get("count", 1)
        if isinstance(count, list):
            count = self.rng.randint(int(count[0]), int(count[1]))
        pool = None
        if "pick" in spec:
            pool = list(spec["pick"])
        elif "pick_tag" in spec:
            pool = self.defs_with_tags(spec["pick_tag"])
            if spec.get("unique"):
                pool = [p for p in pool if not self.spawn_counts.get(p)]
        for _ in range(int(count)):
            if pool is not None:
                if not pool:
                    break
                choice = self.rng.choice(pool)
                if spec.get("unique"):
                    pool.remove(choice)
                sub = choice if isinstance(choice, dict) else {"id": choice}
                extra = {k: v for k, v in spec.items()
                         if k not in SPEC_CONTROL_KEYS and k not in ("pick", "pick_tag")}
                if extra:
                    sub = dict(sub)
                    sub.update(extra)
                out.extend(self.spawn_spec(sub, parent, ctx))
                continue
            base = spec.get("id") or spec.get("def")
            if base and spec.get("unique") and self.spawn_counts.get(base):
                continue
            inline = {k: v for k, v in spec.items() if k not in SPEC_CONTROL_KEYS}
            if base and self.resolve_def(base) is None:
                if not inline.get("name"):
                    # Soft reference to a feature from a mod that isn't loaded.
                    continue
                base = None
            if inline:
                key = self.register_inline_def(inline, base)
            else:
                key = base
            if key is None:
                continue
            ent = self.instantiate(key, parent)
            out.append(ent)
        return out

    # -- tree manipulation --------------------------------------------
    def place(self, ent, parent):
        if ent.parent:
            old = self.entities.get(ent.parent)
            if old and ent.uid in old.children:
                old.children.remove(ent.uid)
        ent.parent = parent.uid if parent is not None else None
        if parent is not None:
            parent.children.append(ent.uid)

    def destroy(self, ent):
        for child in list(self.descendants(ent)):
            self.entities.pop(child.uid, None)
        if ent.parent:
            parent = self.entities.get(ent.parent)
            if parent and ent.uid in parent.children:
                parent.children.remove(ent.uid)
        self.entities.pop(ent.uid, None)

    # -- visibility ----------------------------------------------------
    def contents_visible(self, ent):
        cond = self.def_of(ent).get("contents_visible")
        if cond is None or self.logic is None:
            return True
        return self.logic.check(cond, self.logic.ctx(self_ent=ent))

    def visible_children(self, ent):
        if not ent.is_room and not self.contents_visible(ent):
            return []
        out = []
        for uid in ent.children:
            child = self.entities.get(uid)
            if child is None or child.hidden or child.uid == self.player_uid:
                continue
            out.append(child)
        return out

    def visible_tree(self, ent):
        out = []
        stack = list(reversed(self.visible_children(ent)))
        while stack:
            cur = stack.pop()
            out.append(cur)
            stack.extend(reversed(self.visible_children(cur)))
        return out

    def scope(self):
        """Every entity the player can currently see or hold."""
        room = self.room
        seen = []
        if self.player is not None:
            seen.extend(self.visible_tree(self.player))
        if room is not None:
            seen.extend(e for e in self.visible_tree(room) if e not in seen)
        return seen

    # -- exits ---------------------------------------------------------
    def add_exit(self, room, dest, direction=None, distance=1, **extra):
        ex = {"to": dest.uid, "dir": direction, "distance": distance}
        ex.update({k: v for k, v in extra.items() if v is not None})
        room.exits.append(ex)
        return ex

    def used_dirs(self, room):
        return {e.get("dir") for e in room.exits if e.get("dir")}

    # -- serialisation -------------------------------------------------
    def to_dict(self):
        return {
            "format": 1,
            "seed": self.seed,
            "registry": self.registry.to_dict(),
            "defs": self.defs,
            "entities": [e.to_dict() for e in self.entities.values()],
            "player": self.player_uid,
            "clock": self.clock,
            "turns": self.turns,
            "flags": sorted(self.flags),
            "vars": self.vars,
            "fired": sorted(self.fired),
            "journal": self.journal,
            "story": self.story,
            "areas": self.areas,
            "spawn_counts": self.spawn_counts,
            "dynamic_rules": self.dynamic_rules,
            "game_over": self.game_over,
            "next": self._next,
            "verbose": self.verbose,
            "rng": _rng_state_to_json(self.rng.getstate()),
        }

    @classmethod
    def from_dict(cls, data):
        reg = Registry.from_dict(data["registry"])
        w = cls(reg, data["seed"])
        w.defs = data["defs"]
        for ed in data["entities"]:
            e = Entity.from_dict(ed)
            w.entities[e.uid] = e
        w.player_uid = data["player"]
        w.clock = data["clock"]
        w.turns = data.get("turns", 0)
        w.flags = set(data["flags"])
        w.vars = data["vars"]
        w.fired = set(data["fired"])
        w.journal = data["journal"]
        w.story = data["story"]
        if "steps" not in w.story:
            # A save from before stories were generated: keep the world, retire the old plot.
            w.story = {"title": w.story.get("title", ""), "steps": [], "current": 0, "complete": True,
                       "cast": {}, "lore": {}, "lore_known": []}
        w.areas = data["areas"]
        w.spawn_counts = data.get("spawn_counts", {})
        w.dynamic_rules = data.get("dynamic_rules", [])
        w.game_over = data.get("game_over")
        w._next = data["next"]
        w.verbose = data.get("verbose", False)
        w.rng.setstate(_rng_state_from_json(data["rng"]))
        return w


def _rng_state_to_json(state):
    version, internal, gauss = state
    return [version, list(internal), gauss]


def _rng_state_from_json(data):
    version, internal, gauss = data
    return (version, tuple(internal), gauss)
