"""Story generation: the plot, its cast, the quest chain and the lore.

No mod contains a story.  Mods contribute building blocks:

* characters with a *profile* (personality, motives, goals, wants, what they
  know, which story roles suit them);
* *events* - situations that can befall a world ("the station AI goes rogue"),
  each with roles to cast from whatever characters, places and items are
  loaded, and one or more ways the situation can be resolved;
* *obstacles* - locks, wards, card readers... that the generator can put in
  the player's way, opened by items that *afford* the right thing;
* *lore* snippets, and anything marked *important* (items, characters, places,
  features), which the generator must weave into the main quest.

Generation happens in two halves.  The :class:`StoryPlanner` works on mod
definitions before the map exists: it picks and casts an event, chooses how it
will be resolved, then chains backwards from the resolution - every means must
be obtained somehow (found somewhere, held by a character who wants a favour,
locked in a container whose key must be found first, behind a barrier...) -
using up the important features as keys, favours, holders, informants and
locations.  Its output decides the order in which areas are laid out.  After
the map is built, the :class:`StoryBinder` places everything, creates the
obstacles, writes every character's quest dialogue and conversation menu,
distributes the lore and records a machine-checkable solution for each step.
"""

import copy

from . import textutil


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _weighted(rng, items, weight_fn):
    items = list(items)
    if not items:
        return None
    weights = [max(0.0, float(weight_fn(i))) for i in items]
    if sum(weights) <= 0:
        return rng.choice(items)
    return rng.choices(items, weights=weights)[0]


DEFAULT_CHAR_ROLES = ["ally", "informant", "holder", "victim", "giver"]


class Thing:
    """Something the story can use: a character, item, or fixed feature."""

    def __init__(self, key, def_id, kind, d):
        self.key = key
        self.def_id = def_id
        self.kind = kind            # "character" | "item" | "feature"
        self.d = d
        self.area = None            # area the mod authored it into, if any
        self.loc = None             # planned location for things the generator places
        self.important = bool(d.get("important"))
        self.obtained = False
        self.uid = None
        self.spawned = False        # created by the generator rather than authored
        self.relocate = False       # the story moves it away from where its mod put it
        self.keep = bool(d.get("story_keep"))   # the player must never be asked to give it away

    @property
    def profile(self):
        return self.d.get("profile") or {}

    @property
    def affords(self):
        return set(_as_list(self.d.get("affords")))

    @property
    def tags(self):
        return set(_as_list(self.d.get("tags")))

    @property
    def home(self):
        return set(_as_list(self.d.get("home")))

    def roles(self):
        return set(_as_list(self.profile.get("roles")) or DEFAULT_CHAR_ROLES)

    def __repr__(self):
        return "<Thing %s %s>" % (self.kind, self.key)


class StoryPlanner:
    def __init__(self, gen):
        self.gen = gen
        self.reg = gen.reg
        self.w = gen.w
        self.rng = gen.rng
        self.things = {}
        self.areas = {}
        self.tasks = []
        self.obstacles = {}
        self.accessible = []        # areas in the order the story opens them up (the spine)
        self.accessing = set()
        self.inprogress = set()
        self.pool = set()           # important thing keys not yet given a story function
        self.pool_places = set()
        self.used = set()
        self.cast = {}
        self.event_id = None
        self.event = {}
        self.resolution = None
        self.start_area = None
        self.reserved = set()       # things kept for a later purpose (never given away)
        self.future = set()         # areas the finale will need, which leftovers may gate
        self.pre_gated = set()
        self.generic_keys = 0
        self._n = 0

    def note(self, msg):
        self.gen.note(msg)

    def new_key(self, prefix):
        self._n += 1
        return "%s#%d" % (prefix, self._n)

    # ------------------------------------------------------------------
    # Inventory of what the mods offer
    # ------------------------------------------------------------------
    def collect(self):
        reg, w = self.reg, self.w
        forced = getattr(self.gen, "forced_start", None)
        # A start_only area (a crossroads to set out from) exists only when the player chooses to begin there.
        self.areas = {a: d for a, d in reg["areas"].items() if not d.get("abstract")
                      and (not d.get("start_only") or a == forced)}
        authored = {}
        offstage = {}
        for aid in sorted(self.areas):
            for rid in self.gen.area_room_ids(aid):
                rdef = w.resolve_def("room:" + rid) or {}
                # A story_skip room is a scripted scene; whatever waits there is not the planner's to use.
                skip = "story_skip" in _as_list(rdef.get("tags"))
                self._walk(rdef.get("features") or [], aid, offstage if skip else authored, 0)
        for fid in sorted(reg["features"]):
            d = w.resolve_def(fid)
            if not d or d.get("abstract") or fid == "player":
                continue
            if fid in offstage and fid not in authored:
                continue
            if d.get("profile"):
                kind = "character"
            elif "portable" in (d.get("tags") or []):
                if not d.get("important") and not d.get("affords"):
                    continue
                kind = "item"
            elif d.get("important"):
                kind = "feature"
            else:
                continue
            t = Thing(fid, fid, kind, d)
            t.area = authored.get(fid)
            if kind == "feature" and t.area is None and not d.get("story_spawn"):
                continue  # important scenery only counts where a mod actually built it
            self.things[fid] = t
        self.pool = {k for k, t in self.things.items() if t.important}
        self.pool_places = {a for a, d in self.areas.items() if d.get("important")}

    def _walk(self, specs, aid, authored, depth):
        if depth > 4:
            return
        for spec in _as_list(specs):
            if isinstance(spec, str):
                did, inline = spec, None
            elif isinstance(spec, dict):
                if "chance" in spec or "if" in spec or "pick" in spec or "pick_tag" in spec:
                    continue
                did, inline = spec.get("id") or spec.get("def"), spec
            else:
                continue
            if did:
                d = self.w.resolve_def(did)
                if d is None:
                    continue
                authored.setdefault(did, aid)
                self._walk(d.get("features") or [], aid, authored, depth + 1)
            if inline:
                self._walk(inline.get("features") or [], aid, authored, depth + 1)

    def spawn_thing(self, def_id, kind=None):
        d = self.w.resolve_def(def_id)
        if d is None:
            return None
        if kind is None:
            kind = "character" if d.get("profile") else ("item" if "portable" in (d.get("tags") or []) else "feature")
        t = Thing(self.new_key(def_id), def_id, kind, d)
        t.spawned = True
        self.things[t.key] = t
        return t

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------
    def area_tags(self, aid):
        ad = self.areas.get(aid, {})
        return set(_as_list(ad.get("tags"))) | set(_as_list(ad.get("theme")))

    def matches(self, t, m):
        m = m or {}
        if "def" in m and t.def_id not in _as_list(m["def"]):
            return False
        if "tags" in m and not set(_as_list(m["tags"])) <= t.tags:
            return False
        if "tag" in m and not set(_as_list(m["tag"])) <= t.tags:
            return False
        if "any_tags" in m and not set(_as_list(m["any_tags"])) & t.tags:
            return False
        if "affords" in m and not set(_as_list(m["affords"])) & t.affords:
            return False
        prof = t.profile
        if "motive" in m and not set(_as_list(m["motive"])) & set(_as_list(prof.get("motives"))):
            return False
        if "personality" in m and not set(_as_list(m["personality"])) & set(_as_list(prof.get("personality"))):
            return False
        if "role" in m and not set(_as_list(m["role"])) & t.roles():
            return False
        return True

    def place_matches(self, aid, m):
        tags = self.area_tags(aid)
        m = m or {}
        if "id" in m and aid not in _as_list(m["id"]):
            return False
        if "tags" in m and not set(_as_list(m["tags"])) <= tags:
            return False
        if "any_tags" in m and not set(_as_list(m["any_tags"])) & tags:
            return False
        if "none_tags" in m and set(_as_list(m["none_tags"])) & tags:
            return False
        return True

    # ------------------------------------------------------------------
    # Event choice and casting
    # ------------------------------------------------------------------
    def mods_loaded(self, ids):
        loaded = {m["id"] for m in self.reg.mods}
        return set(_as_list(ids)) <= loaded

    def try_cast(self, ev):
        cast = {}
        taken = set()
        order = {"place": 0, "character": 1, "feature": 2, "item": 3}
        roles = sorted((ev.get("roles") or {}).items(), key=lambda kv: (order.get(kv[1].get("type"), 9), kv[0]))
        for name, spec in roles:
            typ = spec.get("type", "character")
            m = spec.get("match") or {}
            chosen = None
            if typ == "place":
                cands = [a for a in sorted(self.areas) if a not in taken and self.place_matches(a, m)]
                chosen = _weighted(self.rng, cands, lambda a: 3 if a in self.pool_places else 1)
                if chosen:
                    taken.add(chosen)
                    cast[name] = ("place", chosen)
            else:
                kind = {"character": "character", "item": "item", "feature": "feature"}[typ]
                within = cast.get(spec.get("in"), (None, None))[1] if spec.get("in") else None
                cands = [t for k, t in sorted(self.things.items())
                         if t.kind == kind and k not in taken and not t.spawned and self.matches(t, m)
                         and (within is None or t.area == within)]
                chosen = _weighted(self.rng, cands, lambda t: 4 if t.important else 1)
                if chosen is None and spec.get("spawn"):
                    if self.w.resolve_def(spec["spawn"]) is not None:
                        chosen = ("spawn", spec["spawn"], kind, within)
                if chosen is not None:
                    if isinstance(chosen, Thing):
                        taken.add(chosen.key)
                    cast[name] = ("thing", chosen)
            if chosen is None and not spec.get("optional"):
                return None
        return cast

    def choose_event(self):
        options = []
        loaded_tags = set()
        for aid in self.areas:
            loaded_tags |= self.area_tags(aid)
        for eid, ev in sorted(self.reg["events"].items()):
            if ev.get("abstract") or not self.mods_loaded(ev.get("requires_mods")):
                continue
            starts = [a for a in _as_list(ev.get("start_areas")) if a in self.areas]
            if self.start_area and _as_list(ev.get("start_areas")) and self.start_area not in starts:
                continue  # this event belongs to another starting point
            if _as_list(ev.get("start_areas")) and not starts:
                continue
            if self.start_area and self.area_tags(self.start_area) & set(_as_list(ev.get("exclude_start_tags"))):
                continue  # its opening makes no sense from here
            cast = self.try_cast(ev)
            if cast is None:
                continue
            def target_ok(r):
                kind, val = cast.get(r.get("target"), (None, None))
                if r.get("verb") == "attack":
                    # Only something that can actually be fought can be defeated in a fight.
                    d = val.d if isinstance(val, Thing) else (self.w.resolve_def(val[1]) if isinstance(val, tuple) else {})
                    return "creature" in _as_list((d or {}).get("tags"))
                return True
            res = [r for r in _as_list(ev.get("resolutions"))
                   if self.mods_loaded(r.get("requires_mods")) and r.get("target") in cast
                   and (not r.get("means") or r["means"] in cast) and target_ok(r)]
            if not res:
                continue
            imp = sum(1 for kind, v in cast.values() if kind == "thing" and isinstance(v, Thing) and v.important)
            imp += sum(1 for kind, v in cast.values() if kind == "place" and v in self.pool_places)
            weight = float(ev.get("weight", 1)) * (1 + imp)
            if self.start_area and self.start_area in starts:
                weight *= 6
            elif self.start_area and set(_as_list(ev.get("tags"))) & self.area_tags(self.start_area):
                weight *= 2
            if set(_as_list(ev.get("tags"))) & loaded_tags:
                weight *= 2
            options.append((eid, ev, cast, res, weight))
        if not options:
            return False
        eid, ev, cast, res, _w = _weighted(self.rng, options, lambda o: o[4])
        self.event_id, self.event = eid, ev
        for name, (kind, val) in cast.items():
            if kind == "thing" and isinstance(val, Thing) and (ev.get("roles") or {}).get(name, {}).get("relocate"):
                val.relocate = True
            if kind == "thing" and isinstance(val, tuple):
                _, def_id, tkind, within = val
                t = self.spawn_thing(def_id, tkind)
                if within:
                    t.loc = ("area", within)
                val = t
            self.cast[name] = (kind, val)
        self.resolution = self.rng.choice(res)
        self.alt_resolutions = [r for r in res if r is not self.resolution]
        return True

    def cast_thing(self, name):
        kind, val = self.cast.get(name, (None, None))
        return val if kind == "thing" else None

    def cast_place(self, name):
        kind, val = self.cast.get(name, (None, None))
        return val if kind == "place" else None

    def villain(self):
        v = self.cast_thing("villain") or self.cast_thing("antagonist")
        return v

    # ------------------------------------------------------------------
    # Planning primitives
    # ------------------------------------------------------------------
    def task(self, kind, **refs):
        t = {"id": "s%d" % (len(self.tasks) + 1), "kind": kind}
        t.update(refs)
        self.tasks.append(t)
        for v in refs.values():
            if isinstance(v, str) and v in self.things:
                self.use(self.things[v])
        return t

    def use(self, thing):
        self.pool.discard(thing.key)
        self.used.add(thing.key)

    def frontier(self):
        return max(0, len(self.accessible) - 1)

    def has_regions(self):
        return any(not r.get("abstract") and r.get("rooms") for r in self.reg["regions"].values())

    def choose_area(self, thing, extra_forbid=()):
        forbid = set(self.accessing) | set(extra_forbid)
        home = thing.home if thing is not None else set()
        ttags = thing.tags if thing is not None else set()
        cands = []
        for aid, ad in sorted(self.areas.items()):
            if aid in forbid or ad.get("no_story"):
                continue
            w = 1.0
            if aid in self.pool_places:
                w += 6
            atags = self.area_tags(aid)
            if home & atags:
                w += 5
            if ttags & atags:
                w += 1.5
            if aid in self.accessible:
                w += 1
            cands.append((aid, w))
        if self.has_regions():
            wild = 2.0 + (4 if home and any(home & set(_as_list(r.get("tags")))
                                             for r in self.reg["regions"].values()) else 0)
            cands.append((None, wild))
        if not cands:
            return None
        return _weighted(self.rng, cands, lambda c: c[1])[0]

    def access(self, aid):
        """Make sure the story opens up area *aid*, possibly behind an obstacle."""
        if aid is None or aid in self.accessible or aid in self.accessing:
            return
        self.accessing.add(aid)
        if aid in self.pre_gated:
            pass
        elif self.accessible and len([o for o in self.obstacles.values() if o["kind"] == "barrier"]) < 4:
            choice = self.choose_obstacle("barrier", aid)
            if choice is not None:
                oid, key = choice
                if self.rng.random() < (0.85 if key.important else 0.3):
                    self.obtain(key, 1)
                    o = self.add_obstacle(oid, "barrier", aid, key)
                    self.task("open", obstacle=o["key"], key=key.key, place=aid)
        self.accessing.discard(aid)
        self.accessible.append(aid)
        self.pool_places.discard(aid)

    def choose_obstacle(self, kind, aid):
        tags = self.area_tags(aid) if aid else set()
        options = []
        important_keys = len([k for k in self.pool if self.things[k].affords])
        cap = int(self.reg["settings"].get("story_max_locks", 3)) + important_keys
        if len(self.obstacles) >= cap:
            return None
        generic_ok = self.generic_keys < int(self.reg["settings"].get("story_generic_locks", 2))
        for oid, od in sorted(self.reg["obstacles"].items()):
            if od.get("abstract") or od.get("kind", "barrier") != kind:
                continue
            otags = set(_as_list(od.get("tags")))
            if otags and tags and not otags & tags:
                continue
            needs = set(_as_list(od.get("needs")))
            for k in sorted(self.pool):
                t = self.things[k]
                if t.kind == "item" and t.affords & needs and self.can_obtain(t) and t.area != aid:
                    options.append((oid, t, 6.0 + (2 if otags & tags else 0)))
            if generic_ok and od.get("key") and self.w.resolve_def(od["key"]) is not None:
                options.append((oid, od["key"], 1.0 + (1 if otags & tags else 0)))
        if not options:
            return None
        oid, key, _w = _weighted(self.rng, options, lambda o: o[2])
        if isinstance(key, str):
            key = self.spawn_thing(key, "item")
            self.generic_keys += 1
        return oid, key

    def obstacle_for(self, t, aid):
        tags = self.area_tags(aid)
        opts = []
        for oid, od in sorted(self.reg["obstacles"].items()):
            if od.get("abstract") or od.get("kind", "barrier") != "barrier":
                continue
            otags = set(_as_list(od.get("tags")))
            if otags and tags and not otags & tags:
                continue
            if t.affords & set(_as_list(od.get("needs"))):
                opts.append(oid)
        return self.rng.choice(opts) if opts else None

    def arm(self):
        """Before a fight the story depends on, make sure the player has picked up a weapon."""
        weapons = [t for k, t in sorted(self.things.items())
                   if t.kind == "item" and "weapon" in t.tags and not t.spawned]
        if not weapons or any(t.obtained and t.keep for t in weapons):   # one the story will not take back
            return
        weapons = [t for t in weapons if self.can_obtain(t) and (t.area or t.loc)]
        if weapons:
            dmg = lambda t: (t.d.get("props") or {}).get("damage", 1) or 1
            self.obtain(_weighted(self.rng, weapons, lambda t: dmg(t) * (3 if t.key in self.pool else 1)))

    def can_obtain(self, t):
        return (not t.obtained and t.key not in self.inprogress
                and (t.area is None or t.area not in self.accessing))

    def add_obstacle(self, oid, kind, aid, key):
        okey = "o%d" % (len(self.obstacles) + 1)
        o = {"key": okey, "def": oid, "kind": kind, "area": aid, "needs": key.key, "frontier": self.frontier()}
        self.obstacles[okey] = o
        return o

    def place_character(self, c, forbid=()):
        if c.relocate and c.loc is None:
            away = {c.area, self.start_area} | set(forbid)
            aid = self.choose_area(c, away)
            c.loc = ("area", aid) if aid else ("wild", self.frontier())
            if aid:
                self.access(aid)
            return
        if c.relocate:
            if c.loc[0] == "area":
                self.access(c.loc[1])
            return
        if c.area:
            self.access(c.area)
        elif c.loc is None:
            aid = self.choose_area(c, forbid)
            if aid:
                c.loc = ("area", aid)     # commit before recursing, so nested plans see it
                self.access(aid)
            else:
                c.loc = ("wild", self.frontier())
        elif c.loc[0] == "area":
            self.access(c.loc[1])

    def character_area(self, c):
        if c.relocate:
            return c.loc[1] if c.loc and c.loc[0] == "area" else None
        if c.area:
            return c.area
        if c.loc and c.loc[0] == "area":
            return c.loc[1]
        return None

    def helpers(self, role, exclude=()):
        villain = self.villain()
        out = []
        for k, t in sorted(self.things.items()):
            if t.kind != "character" or k in exclude or (villain and k == villain.key):
                continue
            if role not in t.roles() or k in self.inprogress:
                continue
            if "hostile" in t.tags:
                continue  # creatures that attack on sight make poor go-betweens
            if self.resolution and self.cast.get(self.resolution.get("target"), (None, None))[1] is t:
                continue  # whoever the finale is about can't run errands before it
            if t.spawned and k not in [v.key for kind, v in self.cast.values() if kind == "thing"]:
                continue
            area = self.character_area(t)
            if area and area in self.accessing:
                continue
            out.append(t)
        return out

    def favour_item(self, c, thing):
        wants = set(_as_list(c.profile.get("wants")))
        if not wants:
            return None
        cands = [t for k, t in sorted(self.things.items())
                 if t.kind == "item" and t is not thing and self.can_obtain(t) and not t.spawned
                 and k not in self.reserved and not t.keep
                 and (t.affords & wants or t.tags & wants)]
        if not cands:
            return None
        return _weighted(self.rng, cands, lambda t: 5 if t.key in self.pool else 1)

    def maybe_informant(self, about, place):
        cands = [c for c in self.helpers("informant") if c.key in self.pool]
        if not cands or self.rng.random() > 0.65:
            return
        c = self.rng.choice(cands)
        self.place_character(c)
        self.task("talk_info", char=c.key, about=about.key, place=self.character_area(c), about_place=place)

    def obtain(self, thing, depth=0):
        """Plan how the player comes to hold *thing*."""
        if thing.obtained or thing.key in self.inprogress:
            return
        self.inprogress.add(thing.key)
        self.use(thing)
        if thing.area or (thing.loc and thing.loc[0] == "area"):
            aid = thing.area or thing.loc[1]
            self.access(aid)
            self.maybe_informant(thing, aid)
            self.task("find", item=thing.key, place=aid)
        else:
            holders = self.helpers("holder")
            pool_holders = [c for c in holders if c.key in self.pool]
            p_holder = 0.6 if pool_holders else 0.3
            if holders and depth < 4 and self.rng.random() < p_holder:
                c = _weighted(self.rng, holders, lambda c: 4 if c.key in self.pool else 1)
                self.inprogress.add(c.key)
                self.place_character(c)
                thing.loc = ("carried", c.key)
                want = self.favour_item(c, thing) if depth < 3 else None
                if want is not None and self.rng.random() < 0.75:
                    self.obtain(want, depth + 1)
                    self.task("deliver", item=want.key, char=c.key, gives=thing.key, place=self.character_area(c))
                else:
                    self.task("talk_get", char=c.key, item=thing.key, place=self.character_area(c))
                self.inprogress.discard(c.key)
            else:
                aid = self.choose_area(thing)
                if aid:
                    thing.loc = ("area", aid)
                    self.access(aid)
                else:
                    thing.loc = ("wild", self.frontier())
                if depth < 3 and self.rng.random() < 0.45:
                    choice = self.choose_obstacle("container", aid)
                    if choice is not None:
                        oid, key = choice
                        self.obtain(key, depth + 1)
                        o = self.add_obstacle(oid, "container", aid, key)
                        o["loc"] = thing.loc if thing.loc[0] == "area" else ("wild", self.frontier())
                        thing.loc = ("inside", o["key"])
                        self.task("open", obstacle=o["key"], key=key.key, place=aid)
                self.maybe_informant(thing, aid)
                self.task("find", item=thing.key, place=aid)
        thing.obtained = True
        self.inprogress.discard(thing.key)

    # ------------------------------------------------------------------
    def plan(self):
        self.collect()
        forced = getattr(self.gen, "forced_start", None)
        if forced and forced in self.areas:
            self.start_area = forced
        has_event = self.choose_event()
        self.note("event: %s" % (self.event_id or "(none - the story is built from important features alone)"))
        if not (forced and forced in self.areas):
            self.choose_start()
        if self.start_area:
            self.accessible.append(self.start_area)
            self.pool_places.discard(self.start_area)
        # Story-cast places count as important for this world.
        for name, (kind, val) in self.cast.items():
            if kind == "place":
                self.pool_places.add(val)
            elif isinstance(val, Thing) and name not in ("means",):
                pass

        villain = self.villain()
        if villain is not None:
            self.use(villain)
            if villain.area is None and villain.loc is None:
                lair = self.cast_place("lair")
                villain.loc = ("area", lair) if lair else None

        # Opening: someone at the start sets the player on their way.
        giver = None
        if self.start_area:
            final_target = self.cast_thing(self.resolution["target"]) if self.resolution else None
            givers = [c for c in self.helpers("giver") if self.character_area(c) == self.start_area
                      and c is not final_target and not c.relocate]
            if givers:
                giver = _weighted(self.rng, givers, lambda c: 4 if c.important else 1)
                self.task("meet", char=giver.key, place=self.start_area)

        means = self.cast_thing(self.resolution["means"]) if self.resolution and self.resolution.get("means") else None
        target = self.cast_thing(self.resolution["target"]) if self.resolution else None
        if means is not None:
            self.reserved.add(means.key)
            self.pool.discard(means.key)
        # The finale already involves its target and the place it stands in.
        self.final_area = None
        if target is not None:
            self.pool.discard(target.key)
            self.final_area = target.area or (target.loc[1] if target.loc and target.loc[0] == "area" else None) \
                or (self.character_area(target) if target.kind == "character" else None)
            if self.final_area:
                self.pool_places.discard(self.final_area)
                self.future.add(self.final_area)
        if villain is not None and self.character_area(villain):
            self.future.add(self.character_area(villain))
        goals = sorted(self.pool | self.pool_places, key=str)
        self.rng.shuffle(goals)
        if means is not None:
            goals.insert(self.rng.randint(0, len(goals)), "@means")
        for goal in goals:
            if goal == "@means":
                self.obtain(means)
            elif goal in self.things and goal in self.pool:
                self.weave_leftover(self.things[goal])
            elif goal in self.pool_places:
                self.access(goal)
                self.task("investigate", place=goal)
                self.pool_places.discard(goal)
        # Anything that slipped through (e.g. added during the loop).
        for k in sorted(self.pool):
            self.weave_leftover(self.things[k])
        for aid in sorted(self.pool_places):
            self.access(aid)
            self.task("investigate", place=aid)

        if self.resolution:
            target = self.cast_thing(self.resolution["target"])
            if target is not None and self.resolution.get("verb") == "attack":
                self.arm()
            if target is not None:
                if target.kind == "character":
                    self.place_character(target)
                elif target.area:
                    self.access(target.area)
                elif target.loc and target.loc[0] == "area":
                    self.access(target.loc[1])
                if villain is not None and (villain is not target or self.rng.random() < 0.5):
                    self.place_character(villain)
                    self.task("confront", char=villain.key, place=self.character_area(villain))
                self.task("resolve", target=target.key, means=means.key if means else None,
                          place=target.area or (target.loc[1] if target.loc and target.loc[0] == "area" else None))
        self.note("story plan: " + ", ".join("%s(%s)" % (t["kind"], t.get("item") or t.get("char") or t.get("place") or t.get("target") or "")
                                             for t in self.tasks))
        return has_event

    def weave_leftover(self, t):
        if t.key not in self.pool:
            return
        if t.kind == "item":
            # Best use: make it the key to somewhere the story is going to need.
            home = t.area if not t.relocate else None
            gates = [a for a in sorted(self.future) if a not in self.accessible and a not in self.pre_gated
                     and a not in self.accessing and a != home]
            self.rng.shuffle(gates)
            for aid in gates:
                oid = self.obstacle_for(t, aid)
                if oid:
                    self.accessing.add(aid)      # the key must not end up behind its own lock
                    self.obtain(t)
                    self.accessing.discard(aid)
                    o = self.add_obstacle(oid, "barrier", aid, t)
                    self.pre_gated.add(aid)
                    self.task("open", obstacle=o["key"], key=t.key, place=aid)
                    self.access(aid)   # the area joins the spine right behind its gate
                    self.pool.discard(t.key)
                    return
            self.obtain(t)
            if t.keep:
                self.pool.discard(t.key)
                return
            recipients = [c for c in self.helpers("ally") + self.helpers("informant") if c is not t]
            if recipients:
                wants = lambda c: (5 if (t.affords | t.tags) & set(_as_list(c.profile.get("wants"))) else 1) + (2 if c.key in self.pool else 0)
                r = _weighted(self.rng, recipients, wants)
                self.place_character(r)
                self.task("deliver", item=t.key, char=r.key, gives=None, place=self.character_area(r))
        elif t.kind == "character" and "hostile" in t.tags:
            # A monster with a story of its own: the quest goes through it, not around it.
            self.place_character(t)
            self.arm()
            self.task("defeat", char=t.key, place=self.character_area(t))
        elif t.kind == "character":
            self.place_character(t)
            about = self.villain()
            if about is None and self.resolution and self.resolution.get("means"):
                about = self.cast_thing(self.resolution["means"])
            self.task("talk_info", char=t.key, about=about.key if about else None, place=self.character_area(t),
                      about_place=None)
        elif t.kind == "feature":
            self.access(t.area)
            self.task("inspect", feature=t.key, place=t.area)
        self.pool.discard(t.key)

    def choose_start(self):
        own = [a for a in _as_list(self.event.get("start_areas")) if a in self.areas]
        if own:
            # Prefer the event's real starting points over the optional ones (training courses).
            main = [a for a in own if "start" in _as_list(self.areas[a].get("tags"))]
            self.start_area = self.rng.choice(main or own)
            return
        tags = set(_as_list(self.event.get("tags")))
        for kind, val in self.cast.values():
            if kind == "place":
                tags |= self.area_tags(val)
        avoid = set(_as_list(self.event.get("exclude_start_tags")))
        starts = [a for a, d in sorted(self.areas.items()) if "start" in _as_list(d.get("tags"))
                  and not (self.area_tags(a) & avoid)]
        if not starts:
            self.start_area = None
            return
        lair = self.cast_place("lair")

        def weight(a):
            w = 1 + 3 * len(self.area_tags(a) & tags)
            if a == lair:
                w *= 0.2
            if any(t.kind == "character" and t.area == a for t in self.things.values()):
                w += 2
            return w
        self.start_area = _weighted(self.rng, starts, weight)


# ---------------------------------------------------------------------------
# Binding the plan into the built world
# ---------------------------------------------------------------------------

class StoryBinder:
    def __init__(self, gen, planner):
        self.gen = gen
        self.p = planner
        self.w = gen.w
        self.i = gen.i
        self.rng = gen.rng
        self.reg = gen.reg
        self.claimed = set()
        self.obst_ent = {}
        self.lore = {}
        self.knows = {}       # char uid -> [lore ids]

    def note(self, msg):
        self.gen.note(msg)

    # -- helpers -------------------------------------------------------
    def area_rooms(self, aid):
        rooms = [self.w.get(u) for u in self.w.areas.get(aid, {}).get("rooms", []) if self.w.get(u)]
        # Rooms a mod marks story_skip (reached only by a one-off scene, or past the ending) never hold quest things.
        return [r for r in rooms if "story_skip" not in r.tags] or rooms

    def room_for(self, thing, loc):
        kind = loc[0] if loc else "wild"
        home = thing.home if thing else set()
        if kind == "area" and loc[1] in self.w.areas:
            rooms = self.area_rooms(loc[1])
            return _weighted(self.rng, rooms, lambda r: 1 + 4 * len(home & set(r.tags)))
        frontier = loc[1] if loc and kind == "wild" else 0
        stage = frontier
        fillers = [self.w.get(u) for u in self.gen.filler if self.w.get(u) and self.w.get(u).stage <= stage]
        if thing is not None:
            # A sword waits in the woods, a keycard in an office: keep things to country of their own setting.
            own = self.gen.def_setting(thing.def_id)
            fillers = [r for r in fillers if not self.gen.clash(own, self.gen.themes(r))] or fillers
        if home:
            homed = [r for r in fillers if home & set(r.tags)]
            if not homed:
                for tag in sorted(home):
                    grown = self.gen.grow_region(tag, stage)
                    if grown is not None:
                        return grown
            fillers = homed or fillers
        if fillers:
            return self.rng.choice(fillers)
        spine = self.p.accessible
        if spine:
            aid = spine[min(frontier, len(spine) - 1)]
            if aid in self.w.areas:
                return self.rng.choice(self.area_rooms(aid))
        return self.w.room_of(self.w.player)

    def find_authored(self, thing):
        for r in self.area_rooms(thing.area):
            for e in [r] + self.w.descendants(r):
                if e.def_id == thing.def_id and e.uid not in self.claimed:
                    return e
        return None

    def instantiate(self, thing, container):
        made = self.w.spawn_spec({"id": thing.def_id}, container)
        return made[0] if made else None

    def ent(self, key):
        if key is None:
            return None
        t = self.p.things.get(key)
        if t is not None:
            return self.w.get(t.uid)
        o = self.obst_ent.get(key)
        return self.w.get(o) if o else None

    # -- placing -------------------------------------------------------
    def place_all(self):
        p = self.p
        things = [t for t in p.things.values() if t.key in p.used or any(
            v is t for kind, v in p.cast.values())]
        # 1. authored things and freestanding things
        later = []
        for t in sorted(things, key=lambda t: t.key):
            if t.area:
                e = self.find_authored(t)
                if e is None and t.area in self.w.areas:
                    e = self.instantiate(t, self.rng.choice(self.area_rooms(t.area)))
                if e is not None:
                    t.uid = e.uid
                    self.claimed.add(e.uid)
                    if t.relocate and t.loc:
                        self.w.place(e, self.room_for(t, t.loc))
            elif t.loc and t.loc[0] in ("carried", "inside"):
                later.append(t)
            else:
                room = self.room_for(t, t.loc)
                container = room
                if t.kind == "item" and self.rng.random() < 0.35:
                    holders = [e for e in self.w.visible_children(room)
                               if e.has_tag("surface") or (e.has_tag("container") and e.props.get("open") is not False
                                                           and not e.has_tag("obstacle"))]
                    if holders:
                        container = self.rng.choice(holders)
                e = self.instantiate(t, container)
                if e is not None:
                    t.uid = e.uid
                    e.hidden = False
        # 2. obstacle features (wired up once their keys exist)
        for okey, o in sorted(self.p.obstacles.items()):
            self.make_obstacle(o)
        # 3. things inside obstacles or carried by characters
        for t in sorted(later, key=lambda t: t.loc[0] != "carried"):
            kind, ref = t.loc
            if kind == "inside":
                holder = self.w.get(self.obst_ent.get(ref))
            else:
                holder = self.w.get(self.p.things[ref].uid)
            if holder is None:
                holder = self.room_for(t, ("wild", 0))
            e = self.instantiate(t, holder)
            if e is not None:
                t.uid = e.uid
                e.hidden = kind == "carried"
        for t in things:
            if t.uid is None:
                self.note("could not place %s" % t.key)
        self.dedupe_names([self.w.get(t.uid) for t in things if t.uid] +
                          [self.w.get(u) for u in self.obst_ent.values()])
        for okey, o in sorted(self.p.obstacles.items()):
            self.wire_obstacle(o)

    def dedupe_names(self, ents):
        """Two story things with the same name would be impossible to tell apart."""
        seen = {}
        for e in ents:
            if e is None:
                continue
            if e.name in seen:
                for _ in range(8):
                    new = "%s %s" % (self.w.grammar.expand("#dup_adj#"), e.name)
                    if new not in seen:
                        e.name = new
                        break
                self.w.refresh_aliases(e)
            seen[e.name] = e

    def make_obstacle(self, o):
        od = self.reg["obstacles"].get(o["def"], {})
        spec = copy.deepcopy(od.get("feature") or {"name": o["def"].replace("_", " ")})
        spec.setdefault("extends", [])
        spec["extends"] = _as_list(spec["extends"])
        tags = _as_list(spec.get("tags")) + ["obstacle"]
        spec["tags"] = tags
        props = dict(spec.get("props") or {})
        props.update({"open": False, "locked": True})
        spec["props"] = props
        if o["kind"] == "container":
            if "scenery" not in spec["extends"]:
                spec["extends"].append("scenery")
            if "container" not in spec["extends"]:
                spec["extends"].append("container")
            spec["contents_visible"] = {"prop": "open"}
            room = self.room_for(None, o.get("loc") or ("area", o["area"]) if o["area"] else ("wild", o["frontier"]))
        else:
            if "scenery" not in spec["extends"]:
                spec["extends"].append("scenery")
            entry = self.gen.entries.get(o["area"])
            if entry is None:
                self.note("obstacle %s: no way into %s to block" % (o["def"], o["area"]))
                room = self.room_for(None, ("area", o["area"]))
            else:
                room = self.w.get(entry[0])
        e = self.w.spawn_spec(spec, room)[0]
        self.obst_ent[o["key"]] = e.uid

    def wire_obstacle(self, o):
        od = self.reg["obstacles"].get(o["def"], {})
        e = self.w.get(self.obst_ent[o["key"]])
        key = self.p.things[o["needs"]]
        loc = {"obstacle": e.uid, "key": key.uid}
        ctx = self.i.ctx(self_ent=e, local=loc)
        open_text = self.i.render(od.get("open_text") or "#obstacle_open#", ctx)
        locked_text = self.i.render(od.get("locked_text") or "#obstacle_locked#", ctx)
        consume = [{"destroy": "uid:" + key.uid}] if od.get("consume") else []
        opened = [{"set": {"open": True, "locked": False}}, open_text] + consume
        if o["kind"] == "barrier" and self.gen.entries.get(o["area"]):
            room_uid, ex = self.gen.entries[o["area"]]
            ex["if"] = {"prop": "open", "of": "uid:" + e.uid}
            ex["blocked"] = self.i.render(od.get("blocked") or "#obstacle_blocked#", ctx)
        already = {"if": {"prop": "open"}, "do": [self.i.render(od.get("open_already") or "#obstacle_already_open#", ctx)]}
        for verb in ["use", "put", "give"] + _as_list(od.get("verbs")):
            self.w.add_action(e, verb + "_with", {"if": {"is": "uid:" + key.uid, "of": "target"}, "do": opened}, first=False)
        for verb in ["open", "unlock"] + _as_list(od.get("verbs")):
            self.w.add_action(e, verb, already, first=False)
            self.w.add_action(e, verb, {"if": {"held": "uid:" + key.uid}, "do": opened}, first=False)
            self.w.add_action(e, verb, {"do": [locked_text]}, first=False)
        self.w.add_action(e, "use", already, first=False)
        self.w.add_action(e, "use", {"if": {"held": "uid:" + key.uid}, "do": opened}, first=False)
        self.w.add_action(e, "use", {"do": [locked_text]}, first=False)
        # The key works from the other direction too: "use key on door".
        self.w.add_action(self.w.get(key.uid), "use", {"if": {"same": ["second", "uid:" + e.uid]},
                                                         "do": [{"if": {"prop": "open", "of": "second"},
                                                                 "then": [already["do"][0]],
                                                                 "else": [{"set": {"open": True, "locked": False}, "on": "second"},
                                                                          open_text] + consume}]})

    # -- text ----------------------------------------------------------
    def voice(self, char_uid, kind, **local):
        """A line of dialogue shaped by the speaker's personality."""
        ent = self.w.get(char_uid)
        g = self.w.grammar
        lines = _as_list((ent.profile or {}).get(kind)) if ent is not None else []
        if lines:
            src = self.rng.choice(lines)
        else:
            src = "#say_%s#" % kind
            for p in _as_list((ent.profile or {}).get("personality")) if ent is not None else []:
                if g.has("say_%s_%s" % (kind, p)):
                    src = "#say_%s_%s#" % (kind, p)
                    break
        return self.text(src, speaker=char_uid, **local)

    def text(self, src, beat=None, **local):
        if isinstance(src, list):
            src = self.rng.choice(src) if src else ""
        ctx = self.i.ctx(local={k: v for k, v in local.items() if v is not None}, beat=beat)
        return textutil.cap(self.i.render(src, ctx).strip())

    def place_name(self, aid, ent=None):
        room = self.w.room_of(ent) if ent is not None else None
        if aid and aid in self.w.areas:
            area = self.w.areas[aid]
            if room is not None and room.area == aid and len(area.get("rooms", [])) > 12:
                # In a sprawling place the area's name alone is no help: name the room too.
                return "%s (%s)" % (room.name, area["name"])
            return area["name"]
        if room is not None:
            return room.name
        return self.w.string("somewhere", "somewhere")

    # -- the steps -----------------------------------------------------
    def solution_for_find(self, ent):
        sol = [("goto", ent.uid)]
        chain = [a for a in reversed(self.w.ancestors(ent)) if not a.is_room]
        for anc in chain:
            if anc.hidden:
                sol.append(("reveal", anc.uid))
            if anc.props.get("open") is False and not anc.has_tag("obstacle") and not anc.has_tag("person"):
                sol.append(("open", anc.uid))
        if ent.hidden:
            sol.append(("reveal", ent.uid))
        sol.append(("take", ent.uid))
        return sol

    def build_steps(self):
        steps = []
        p = self.p
        for idx, task in enumerate(p.tasks):
            step = self.build_step(idx, task)
            if step is not None:
                steps.append(step)
        return steps

    def build_step(self, idx, task):
        kind = task["kind"]
        e = self.ent
        flag = "story_%s" % task["id"]
        refs = {}
        place = task.get("place")
        step = {"id": task["id"], "kind": kind, "state": "pending", "place": place}
        villain = self.p.villain()
        vuid = villain.uid if villain else None
        common = {"villain": vuid}

        if kind == "meet":
            c = e(task["char"])
            if c is None:
                return None
            refs = {"char": c.uid}
            lines = [self.voice(c.uid, "greet", **common), self.voice(c.uid, "meet", hook=self.story_hook(), goal=self.story_goal(), **common)]
            lore = self.pick_lore(prefer=("event",), holder=c.uid)
            if lore:
                lines.append(self.voice(c.uid, "lore_intro", **common) + " " + self.lore[lore]["text"])
            self.w.add_action(c, "talk", {"if": {"not": {"flag": flag}}, "do": lines + ([{"learn": lore}] if lore else []) + [{"flag": flag}]}, first=False)
            step.update(objective={"flag": flag}, solution=[("goto", c.uid), ("talk", c.uid)])
            title_sym, hint_sym = "#step_meet_title#", "#step_meet_hint#"
        elif kind == "find":
            it = e(task["item"])
            if it is None:
                return None
            refs = {"item": it.uid}
            step.update(objective={"held": "uid:" + it.uid}, solution=self.solution_for_find(it))
            title_sym, hint_sym = "#step_find_title#", "#step_find_hint#"
        elif kind == "talk_get":
            c, it = e(task["char"]), e(task["item"])
            if c is None or it is None:
                return None
            refs = {"char": c.uid, "item": it.uid}
            self.w.add_action(c, "talk", {"if": {"not": {"flag": flag}}, "do": [
                self.voice(c.uid, "give", item=it.uid, **common),
                {"reveal": "uid:" + it.uid}, {"move": "uid:" + it.uid, "to": "player"},
                self.text("#receive_item#", char=c.uid, item=it.uid), {"flag": flag}]}, first=False)
            step.update(objective={"held": "uid:" + it.uid}, solution=[("goto", c.uid), ("talk", c.uid)])
            title_sym, hint_sym = "#step_talkget_title#", "#step_talkget_hint#"
        elif kind == "deliver":
            c, it = e(task["char"]), e(task["item"])
            gives = e(task.get("gives"))
            if c is None or it is None:
                return None
            refs = {"char": c.uid, "item": it.uid}
            reward = []
            if gives is not None:
                refs["reward"] = gives.uid
                reward = [{"reveal": "uid:" + gives.uid}, {"move": "uid:" + gives.uid, "to": "player"},
                          self.text("#receive_item#", char=c.uid, item=gives.uid)]
            lore = self.pick_lore(prefer=("cast", "event"), holder=c.uid)
            thanks = [self.voice(c.uid, "thanks", item=it.uid, **common)]
            if lore:
                thanks.append(self.voice(c.uid, "lore_intro", **common) + " " + self.lore[lore]["text"])
                reward.append({"learn": lore})
            handler = {"if": {"all": [{"is": "uid:" + it.uid, "of": "target"}, {"not": {"flag": flag}}]},
                       "do": [{"move": "uid:" + it.uid, "to": "uid:" + c.uid}, {"hide": "uid:" + it.uid}] + thanks + reward + [{"flag": flag}]}
            for verb in ("give_with", "use_with", "put_with"):
                self.w.add_action(c, verb, handler)
            asked = flag + "_asked"
            self.w.add_action(c, "talk", {"if": {"all": [{"not": {"flag": asked}}, {"not": {"flag": flag}}]}, "do": [
                self.voice(c.uid, "ask", item=it.uid, reward=refs.get("reward"), **common),
                {"flag": asked}]}, first=False)
            step.update(objective={"flag": flag}, solution=[("goto", c.uid), ("give", it.uid, c.uid)])
            wanted = set(_as_list(c.profile.get("wants"))) & (set(_as_list(self.w.def_of(it).get("affords"))) | set(it.tags))
            title_sym = "#step_deliver_title#" if (gives is not None or wanted) else "#step_show_title#"
            hint_sym = "#step_deliver_hint_reward#" if gives is not None else "#step_deliver_hint#"
        elif kind == "talk_info":
            c = e(task["char"])
            if c is None:
                return None
            about = e(task.get("about"))
            refs = {"char": c.uid}
            if about is not None:
                refs["about"] = about.uid
            where = self.place_name(task.get("about_place"), about)
            lore = self.pick_lore(prefer=("cast", "event", "place"), holder=c.uid)
            lines = [self.voice(c.uid, "info", about=about.uid if about else None, where=where, **common)]
            if lore:
                lines.append(self.voice(c.uid, "lore_intro", **common) + " " + self.lore[lore]["text"])
            self.w.add_action(c, "talk", {"if": {"not": {"flag": flag}}, "do": lines + ([{"learn": lore}] if lore else []) + [{"flag": flag}]}, first=False)
            step.update(objective={"flag": flag}, solution=[("goto", c.uid), ("talk", c.uid)])
            title_sym, hint_sym = "#step_info_title#", "#step_info_hint#"
        elif kind == "open":
            o = self.w.get(self.obst_ent.get(task["obstacle"]))
            k = e(task["key"])
            if o is None or k is None:
                return None
            refs = {"obstacle": o.uid, "key": k.uid}
            step.update(objective={"prop": "open", "of": "uid:" + o.uid}, solution=[("goto", o.uid), ("use", k.uid, o.uid)])
            title_sym, hint_sym = "#step_open_title#", "#step_open_hint#"
        elif kind == "investigate":
            rooms = self.area_rooms(place)
            if not rooms:
                return None
            room = self.rng.choice(rooms)
            lore = self.pick_lore(prefer=("place", "event", "cast"), holder=None, place=place)
            doc = self.make_document(room, lore, extra=[{"flag": flag}])
            refs = {"clue": doc.uid}
            step.update(objective={"flag": flag}, solution=[("goto", doc.uid), ("read", doc.uid)])
            title_sym, hint_sym = "#step_investigate_title#", "#step_investigate_hint#"
        elif kind == "inspect":
            f = e(task["feature"])
            if f is None:
                return None
            refs = {"feature": f.uid}
            lore = self.pick_lore(prefer=("cast", "place"), holder=None, about_uid=f.uid, place=(self.w.room_of(f).area if self.w.room_of(f) else None), strict=True)
            effects = [{"show": "examine", "of": "self"}]
            if lore:
                effects += [self.lore[lore]["text"], {"learn": lore}]
            self.w.add_action(f, "examine", {"if": {"not": {"flag": flag}}, "do": effects + [{"flag": flag}]})
            step.update(objective={"flag": flag}, solution=[("goto", f.uid), ("examine", f.uid)])
            title_sym, hint_sym = "#step_inspect_title#", "#step_inspect_hint#"
        elif kind == "confront":
            c = e(task["char"])
            if c is None:
                return None
            refs = {"char": c.uid}
            lines = [self.voice(c.uid, "confront", **common)]
            motive = (c.profile or {}).get("motive_text")
            if motive:
                lines.append(self.voice(c.uid, "motive", motive=motive, **common))
            self.w.add_action(c, "talk", {"if": {"not": {"flag": flag}}, "do": lines + [{"flag": flag}]}, first=False)
            step.update(objective={"flag": flag}, solution=[("goto", c.uid), ("talk", c.uid)])
            title_sym, hint_sym = "#step_confront_title#", "#step_confront_hint#"
        elif kind == "defeat":
            c = e(task["char"])
            if c is None:
                return None
            refs = {"char": c.uid}
            self.w.dynamic_rules.append({"on": "killed", "if": {"same": ["self", "uid:" + c.uid]}, "do": [{"flag": flag}]})
            step.update(objective={"flag": flag}, solution=[("goto", c.uid), ("cmd", "attack", None, c.uid)])
            title_sym, hint_sym = "#step_defeat_title#", "#step_defeat_hint#"
        elif kind == "resolve":
            target = e(task["target"])
            means = e(task.get("means"))
            if target is None:
                return None
            refs = {"target": target.uid}
            if means is not None:
                refs["means"] = means.uid
            res = self.p.resolution
            self.wire_resolution(res, target, means, primary=True)
            for alt in getattr(self.p, "alt_resolutions", []):
                t2 = self.ent_for_role(alt.get("target"))
                m2 = self.ent_for_role(alt.get("means"))
                if t2 is not None and (m2 is not None or not alt.get("means")):
                    self.wire_resolution(alt, t2, m2, primary=False)
            verb = res.get("verb", "use")
            if means is not None:
                sol = [("goto", target.uid), ("cmd", verb, means.uid, target.uid)]
            else:
                sol = [("goto", target.uid), ("cmd", verb, None, target.uid)]
            step.update(objective={"flag": "story_resolved"}, solution=sol)
            title_sym = self.text(res.get("title") or "#step_resolve_title#", target=target.uid, means=means.uid if means else None, villain=vuid)
            hint_sym = res.get("hint") or ("#step_resolve_hint_means#" if means is not None else "#step_resolve_hint#")
        else:
            return None

        local = dict(refs)
        local.update(place=self.place_name(place, self.w.get(next(iter(refs.values()))) if refs else None),
                     villain=vuid)
        step["refs"] = refs
        step["title"] = self.text(title_sym, **local)
        step["hint"] = self.text(hint_sym, **local)
        step["involves"] = sorted(set(refs.values()))
        return step

    def ent_for_role(self, role):
        if not role:
            return None
        t = self.p.cast_thing(role)
        return self.w.get(t.uid) if t is not None and t.uid else None

    def wire_resolution(self, res, target, means, primary):
        flag = [{"flag": "story_resolved"}]
        text = self.text(res.get("text") or "#resolution_text#", target=target.uid,
                         means=means.uid if means else None)
        effects = [{"say": text, "style": "story"}] + _as_list(res.get("effects")) + flag
        guard = {"not": {"flag": "story_resolved"}}
        verb = res.get("verb", "use")
        if verb == "attack":
            self.w.dynamic_rules.append({"on": "killed", "if": {"all": [guard, {"same": ["self", "uid:" + target.uid]}]},
                                         "do": effects})
            return
        if means is not None:
            for v in {verb, "use", "put", "give"}:
                self.w.add_action(target, v + "_with", {"if": {"all": [guard, {"is": "uid:" + means.uid, "of": "target"}]},
                                                        "do": effects})
            self.w.add_action(target, verb, {"if": {"all": [guard, {"held": "uid:" + means.uid}]}, "do": effects})
            self.w.add_action(means, "use", {"if": {"all": [guard, {"same": ["second", "uid:" + target.uid]}]},
                                             "do": effects})
        else:
            # After any quest dialogue still pending, before the conversation menu.
            self.w.add_action(target, verb, {"if": guard, "do": effects}, first=False)

    def story_hook(self):
        ev = self.p.event
        return self.text(ev.get("hook") or "#default_story_hook#", **self.cast_locals())

    def story_goal(self):
        ev = self.p.event
        return self.text(ev.get("goal") or "#default_story_goal#", **self.cast_locals())

    def cast_locals(self):
        out = {}
        for name, (kind, val) in self.p.cast.items():
            if kind == "thing" and val.uid:
                out[name] = val.uid
            elif kind == "place":
                out[name] = self.place_name(val)
        return out

    # -- lore ----------------------------------------------------------
    def gather_lore(self):
        w = self.w
        present_defs = {e.def_id for e in w.entities.values()}
        cast_roles = {n for n, (k, v) in self.p.cast.items() if (k == "place") or (k == "thing" and v.uid)}
        all_tags = set()
        for a in w.areas.values():
            all_tags |= set(a.get("tags") or [])
        for e in w.entities.values():
            all_tags |= set(e.tags)
        loc = self.cast_locals()

        def ok(about):
            for a in _as_list(about):
                kind, _, val = a.partition(":")
                if kind == "def" and val not in present_defs:
                    return False
                if kind == "area" and val not in w.areas:
                    return False
                if kind == "event" and val != self.p.event_id:
                    return False
                if kind == "cast" and val not in cast_roles:
                    return False
                if kind == "tag" and val not in all_tags:
                    return False
                if kind == "mod" and not self.p.mods_loaded(val):
                    return False
            return True

        entries = []
        for lid, ld in sorted(self.reg["lore"].items()):
            if ld.get("abstract") or not ok(ld.get("about")):
                continue
            if self.rng.random() > float(ld.get("chance", 1)):
                continue
            entries.append((lid, ld))
        for n, ld in enumerate(_as_list(self.p.event.get("lore"))):
            entries.append(("%s.%d" % (self.p.event_id, n), dict(ld, about=_as_list(ld.get("about")) + ["event:" + str(self.p.event_id)])))
        for lid, ld in entries:
            text = self.text(ld.get("text", ""), **loc)
            if not text:
                continue
            about = _as_list(ld.get("about"))
            kinds = {a.partition(":")[0] for a in about}
            self.lore[lid] = {"title": self.text(ld.get("title") or "#lore_title#", **loc),
                              "text": text, "tags": _as_list(ld.get("tags")),
                              "about": about, "kinds": sorted(kinds), "told": False}
        self.w.story["lore"] = {k: {"title": v["title"], "text": v["text"]} for k, v in self.lore.items()}

    def pick_lore(self, prefer=(), holder=None, place=None, about_uid=None, strict=False):
        """Choose an untold lore entry, preferring certain kinds (event, cast, place)."""
        free = [k for k, v in sorted(self.lore.items()) if not v["told"]]
        if not free:
            return None
        holder_ent = self.w.get(holder) if holder else None
        knows = set(_as_list((holder_ent.profile or {}).get("knows"))) if holder_ent is not None else set()

        def weight(k):
            v = self.lore[k]
            wt = 1.0
            for idx, kind in enumerate(prefer):
                if kind in v["kinds"]:
                    wt += 4 - idx
            if knows & set(v["tags"]):
                wt += 4
            if holder_ent is not None and ("def:" + holder_ent.def_id) in v["about"]:
                wt += 6
            if place and ("area:" + place) in v["about"]:
                wt += 6
            if about_uid and self.w.get(about_uid) is not None and ("def:" + self.w.get(about_uid).def_id) in v["about"]:
                wt += 6
            return wt
        if strict:
            # Only lore that is actually about this thing or where it stands.
            about_def = ("def:" + self.w.get(about_uid).def_id) if about_uid and self.w.get(about_uid) else None
            free = [k for k in free if about_def in self.lore[k]["about"]
                    or (place and ("area:" + place) in self.lore[k]["about"])]
            if not free:
                return None
        k = _weighted(self.rng, free, weight)
        self.lore[k]["told"] = True
        return k

    def make_document(self, room, lore_id, extra=()):
        carriers = self.w.defs_with_tags("lore_carrier")
        rtags = set(room.tags)
        fit = [c for c in carriers if not self.w.resolve_def(c).get("habitat")
               or set(_as_list(self.w.resolve_def(c).get("habitat"))) & rtags]
        # A second glyph beside the room's own would be impossible to tell apart when reading.
        present = {e.def_id for e in self.w.descendants(room)}
        names = {e.name.lower() for e in self.w.descendants(room)}
        fit = [c for c in fit if c not in present]
        if fit:
            spec = {"id": _weighted(self.rng, fit, lambda c: 1 + 3 * bool(self.w.resolve_def(c).get("habitat")))}
        else:
            spec = {"name": self.w.string("lore_note_name", "scrap of writing"), "extends": ["portable", "readable"],
                    "description": self.w.string("lore_note_description", "A few lines of writing.")}
        doc = self.w.spawn_spec(spec, room)[0]
        doc.hidden = False
        if doc.name.lower() in names:
            doc.name = self.w.string("lore_note_name", "scrap of writing")
        if lore_id:
            doc.props["text"] = self.lore[lore_id]["text"]
            self.w.add_action(doc, "read", {"do": [self.lore[lore_id]["title"] + ": \"" + self.lore[lore_id]["text"] + "\"",
                                                   {"learn": lore_id}] + list(extra)})
        elif extra:
            self.w.add_action(doc, "read", {"do": ["{self.text}"] + list(extra)})
        return doc

    def scatter_lore(self):
        """Put remaining lore into documents around the world and into people's heads."""
        chars = [e for e in self.w.entities.values() if e.profile]
        for c in chars:
            self.knows[c.uid] = []
        for k, v in sorted(self.lore.items()):
            for c in chars:
                knows = set(_as_list(c.profile.get("knows")))
                if knows & set(v["tags"]) or ("def:" + c.def_id) in v["about"]:
                    self.knows[c.uid].append(k)
        n = int(self.gen.setting("lore_documents", 5) * max(0.6, self.gen.size))
        rooms = [r for r in self.w.rooms() if r.uid != self.w.room.uid]
        for _ in range(n):
            free = [k for k, v in self.lore.items() if not v["told"]]
            if not free or not rooms:
                break
            lid = self.rng.choice(sorted(free))
            about_areas = [a.partition(":")[2] for a in self.lore[lid]["about"] if a.startswith("area:")]
            pool = [r for r in rooms if r.area in about_areas] or rooms
            self.lore[lid]["told"] = True
            self.make_document(self.rng.choice(pool), lid)

    # -- conversation menus ---------------------------------------------
    def build_menus(self):
        for c in sorted([e for e in self.w.entities.values() if e.profile], key=lambda e: e.uid):
            if c.profile.get("menu") is False or "hostile" in c.tags:
                continue   # scripted speakers and monsters keep their own lines
            opts = [{"text": self.text("#ask_who#"), "do": [self.voice(c.uid, "who", **self.cast_locals())]}]
            goals = c.profile.get("goals")
            if goals:
                opts.append({"text": self.text("#ask_want#"),
                             "do": [self.voice(c.uid, "goal", goal=self.rng.choice(_as_list(goals)))]})
            for lid in self.knows.get(c.uid, [])[:4]:
                opts.append({"text": self.text("#ask_about#", topic=self.lore[lid]["title"]),
                             "do": [self.voice(c.uid, "lore_intro") + " " + self.lore[lid]["text"], {"learn": lid}]})
            opts.append({"text": self.text("#ask_advice#"), "if": {"story_complete": False}, "do": [{"lead": True}]})
            if self.w.handlers(c, "talk", "def"):
                opts.append({"text": self.text("#ask_chat#"), "do": [{"inherit": "talk"}]})
            opts.append({"text": self.text("#ask_bye#"), "do": [self.voice(c.uid, "bye")]})
            self.w.add_action(c, "talk", {"do": [{"choice": {"prompt": self.voice(c.uid, "greet"),
                                                             "options": opts, "cancel": self.voice(c.uid, "bye")}}]},
                              first=False)

    # -- main ----------------------------------------------------------
    def bind(self):
        w = self.w
        self.place_all()
        for name, (kind, val) in self.p.cast.items():
            if kind == "thing" and val.uid:
                w.story["cast"][name] = val.uid
        self.gather_lore()
        steps = self.build_steps()
        self.scatter_lore()
        self.build_menus()
        ev = self.p.event
        loc = self.cast_locals()
        w.story.update({
            "event": self.p.event_id,
            "title": self.text(ev.get("title") or "#default_story_title#", **loc),
            "intro": self.story_hook(),
            "goal": self.story_goal(),
            "steps": steps,
            "current": 0,
            "complete": not steps,
            "on_start": _as_list(ev.get("consequences")),
        })
        w.story["ending"] = self.ending()
        self.note("story: %s (%d steps, %d lore)" % (w.story["title"], len(steps), len(self.lore)))
        return w.story

    def ending(self):
        parts = []
        ev = self.p.event
        if ev.get("ending"):
            parts.append(self.text(ev["ending"], **self.cast_locals()))
        helped = []
        for st in self.w.story["steps"]:
            c = st.get("refs", {}).get("char")
            ent = self.w.get(c)
            if ent is not None and ent.profile.get("epilogue") and c not in helped:
                villain = self.p.villain()
                if villain is None or villain.uid != c:
                    helped.append(c)
        for c in helped[:3]:
            ent = self.w.get(c)
            parts.append(self.text(ent.profile["epilogue"], speaker=c))
        if not parts:
            parts.append(self.text("#default_story_ending#"))
        return "\n\n".join(parts)
