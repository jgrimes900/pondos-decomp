"""Static checks for mod content, used by ``--validate`` and the test-suite."""

import re

from .generator import GenerationError, generate
from .world import normalize_handlers

_SYMBOL = re.compile(r"(?<!\\)#([A-Za-z0-9_\-]+)(?:\.[A-Za-z0-9_]+)*#")
_ACTION = re.compile(r"\[([A-Za-z0-9_\-]+):")


def _walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def _spec_ids(spec):
    """Yield every feature id referenced by a feature spec."""
    if isinstance(spec, str):
        yield spec
    elif isinstance(spec, list):
        for s in spec:
            yield from _spec_ids(s)
    elif isinstance(spec, dict):
        for key in ("id", "def"):
            if isinstance(spec.get(key), str):
                yield spec[key]
        for p in spec.get("pick") or []:
            yield from _spec_ids(p)
        for s in spec.get("features") or []:
            yield from _spec_ids(s)


def check_registry(reg):
    """Return a list of warning strings for suspicious content."""
    problems = list(reg.warnings)
    feats, rooms = reg["features"], reg["rooms"]
    verbs = set(reg["verbs"])
    loaded = {m["id"] for m in reg.mods}

    def where(section, key):
        return "%s '%s' (%s)" % (section[:-1], key, reg.sources.get((section, key)) or
                                 reg[section].get(key, {}).get("_mod", "?"))

    def check_feature_specs(label, specs, soft):
        for fid in _spec_ids(specs or []):
            if fid not in feats and not soft:
                problems.append("note: %s: feature '%s' is not loaded (skipped unless its mod is selected)" % (label, fid))

    for section in ("features", "rooms"):
        for key, d in reg[section].items():
            label = where(section, key)
            ext = d.get("extends") or []
            for parent in ext if isinstance(ext, list) else [ext]:
                if parent not in feats and parent not in rooms and not d.get("soft_extends"):
                    problems.append("note: %s: extends '%s', which is not loaded (fine if it comes from an optional mod)"
                                    % (label, parent))
            check_feature_specs(label, d.get("features"), d.get("soft"))
            for verb in (d.get("actions") or {}):
                base = verb[:-5] if verb.endswith("_with") else verb
                if base not in verbs:
                    problems.append("note: %s: action for verb '%s', which no loaded mod defines" % (label, base))
                if not normalize_handlers(d["actions"][verb]):
                    problems.append("%s: empty action '%s'" % (label, verb))
    for key, d in reg["areas"].items():
        r = d.get("rooms")
        if not r:
            problems.append("%s: has no rooms" % where("areas", key))
        ids = ["%s/%s" % (key, x) for x in r] if isinstance(r, dict) else list(r or [])
        for rid in ids:
            rdef = rooms.get(rid)
            if rdef is None:
                problems.append("%s: unknown room '%s'" % (where("areas", key), rid))
                continue
            for ex in rdef.get("exits") or []:
                to = ex.get("to")
                if "%s/%s" % (key, to) not in rooms and to not in rooms:
                    problems.append("room '%s': exit to unknown room '%s'" % (rid, to))
                if ex.get("dir") and ex["dir"] not in reg["directions"]:
                    problems.append("room '%s': unknown direction '%s'" % (rid, ex["dir"]))
    for key, d in reg["events"].items():
        label = where("events", key)
        roles = d.get("roles") or {}
        for rname, spec in roles.items():
            if spec.get("type", "character") not in ("character", "item", "place", "feature"):
                problems.append("%s: role '%s' has unknown type '%s'" % (label, rname, spec.get("type")))
            if spec.get("spawn") and spec["spawn"] not in feats:
                problems.append("note: %s: role '%s' spawns '%s', which is not loaded" % (label, rname, spec["spawn"]))
            if spec.get("in") and spec["in"] not in roles:
                problems.append("%s: role '%s' is 'in' unknown role '%s'" % (label, rname, spec["in"]))
        if not d.get("resolutions"):
            problems.append("%s: has no resolutions" % label)
        for r in d.get("resolutions") or []:
            for k in ("target", "means"):
                if r.get(k) and r[k] not in roles:
                    problems.append("%s: resolution %s '%s' is not a role" % (label, k, r[k]))
    for key, d in reg["obstacles"].items():
        if not d.get("needs"):
            problems.append("%s: has no 'needs'" % where("obstacles", key))
        if d.get("kind", "barrier") not in ("barrier", "container"):
            problems.append("%s: kind must be barrier or container" % where("obstacles", key))
        if d.get("key") and d["key"] not in feats:
            problems.append("note: %s: key '%s' is not loaded" % (where("obstacles", key), d["key"]))
    for key, d in feats.items():
        if d.get("profile") and not isinstance(d["profile"], dict):
            problems.append("%s: profile must be an object" % where("features", key))
    for section in ("beats", "premises"):
        if section in reg.sections and reg[section]:
            problems.append("section '%s' is no longer supported: stories are generated (see events)" % section)
    for key, d in reg["regions"].items():
        if not d.get("rooms") and not d.get("abstract"):
            problems.append("%s: has no room templates" % where("regions", key))
    # Grammar symbols referenced anywhere but defined nowhere.
    grammar = reg["grammar"]
    used = set()
    saved = set()
    for section, entries in reg.sections.items():
        for s in _walk_strings(entries):
            used.update(_SYMBOL.findall(s))
            saved.update(_ACTION.findall(s))
    for sym in sorted(used - set(grammar) - saved):
        problems.append("grammar symbol '#%s#' is used but never defined" % sym)
    for rule_id, rule in reg["rules"].items():
        if "on" not in rule:
            problems.append("rule '%s' has no 'on' event" % rule_id)
    if not loaded:
        problems.append("no mods loaded")
    return problems


def smoke_generate(reg, seeds=range(1, 21)):
    """Generate several worlds and check basic invariants. Returns problems."""
    problems = []
    for seed in seeds:
        try:
            world, _log = generate(reg, seed=seed)
        except GenerationError as exc:
            problems.append("generation failed: %s" % exc)
            break
        except Exception as exc:  # report, don't crash
            problems.append("seed %s: generation failed: %r" % (seed, exc))
            continue
        problems.extend("seed %s: %s" % (seed, p) for p in check_world(world))
    return problems


def check_world(world):
    """Invariants every generated world must satisfy."""
    problems = []
    rooms = world.rooms()
    if world.player is None or world.room is None:
        return ["player was not placed in a room"]
    # Every room must be reachable from the start (ignoring conditions).
    seen = {world.room.uid}
    stack = [world.room]
    while stack:
        r = stack.pop()
        for ex in r.exits:
            nxt = world.get(ex["to"])
            if nxt is None:
                problems.append("room %s has an exit to missing %s" % (r.uid, ex["to"]))
                continue
            if nxt.uid not in seen:
                seen.add(nxt.uid)
                stack.append(nxt)
    unreachable = [r.name for r in rooms if r.uid not in seen]
    if unreachable:
        problems.append("unreachable rooms: %s" % ", ".join(sorted(unreachable)[:6]))
    for r in rooms:
        dirs = [ex.get("dir") for ex in r.exits if ex.get("dir")]
        if len(dirs) != len(set(dirs)):
            problems.append("room '%s' has duplicate exit directions %s" % (r.name, dirs))
    involved = set()
    for st in world.story.get("steps", []):
        for rname, uid in st.get("refs", {}).items():
            if uid not in world.entities:
                problems.append("step %s ref %s is missing" % (st["id"], rname))
            involved.add(uid)
            ent = world.get(uid)
            if ent is not None:
                involved.add(world.room_of(ent).uid if world.room_of(ent) else uid)
    # Every important feature that exists must be part of the main quest.
    if world.story.get("steps"):
        involved_areas = {world.get(u).area for u in involved if world.get(u) is not None and world.get(u).is_room}
        involved_areas |= {st.get("place") for st in world.story["steps"]}
        for e in world.entities.values():
            d = world.def_of(e)
            if d.get("important") and not e.is_room and e.uid not in involved:
                problems.append("important '%s' is not part of the main quest" % e.name)
        for aid, adef in world.registry["areas"].items():
            if adef.get("important") and aid in world.areas and aid not in involved_areas:
                problems.append("important place '%s' is not part of the main quest" % aid)
    return problems
