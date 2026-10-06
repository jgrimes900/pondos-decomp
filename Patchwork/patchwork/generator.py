"""World generation.

The generator owns no content.  It takes the merged registry of the selected
mods and:

1. asks the story planner (story.py) to invent a plot from the mods' events,
   characters, important features and obstacles; the plan decides which areas
   the story needs and in what order they open up;
2. builds those areas (hand-made, or generated from a layout and furnished by
   biomes) and lays them out along a "spine" in story order;
3. joins them: with paths across a biome map when mods define paths (see
   atlas.py), otherwise with filler rooms generated from region definitions;
   then adds side areas, generated places, branches and loops;
4. scatters wandering features and encounters, then lets the story binder
   place the plot's characters, items, obstacles, dialogue and lore, and plants
   travellers who pass on rumours about what to do next.
"""

import copy
import fnmatch

from .atlas import Atlas
from .logic import Interpreter
from .story import StoryBinder, StoryPlanner
from .world import World



class GenerationError(Exception):
    pass


def expand_room_list(rooms, all_rooms):
    """An area's room list may use glob patterns: "hl/c1a0*" or "hl/*"."""
    out = []
    for r in _as_list(rooms):
        if any(ch in r for ch in "*?["):
            out.extend(k for k in sorted(all_rooms) if fnmatch.fnmatchcase(k, r) and k not in out)
        elif r not in out:
            out.append(r)
    return out


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _weighted(rng, items, weight_fn):
    if not items:
        return None
    weights = [max(0.0, float(weight_fn(i))) for i in items]
    if sum(weights) <= 0:
        return rng.choice(items)
    return rng.choices(items, weights=weights)[0]


SIZES = {"small": 0.7, "medium": 1.4, "large": 2.2, "huge": 3.2}


class Generator:
    def __init__(self, registry, seed=None, player_name=None, size="medium", start=None):
        self.size = SIZES.get(size, size if isinstance(size, (int, float)) else 1.0)
        self.reg = registry
        self.w = World(registry, seed)
        self.i = Interpreter(self.w)
        self.rng = self.w.rng
        self.entries = {}         # area id -> (room uid, exit) of the way into it along the spine
        self.forced_start = start
        self.player_name = player_name
        self.log = []
        self.region_use = {}
        self.filler = []          # uids of generated filler rooms
        self.expansion = []       # uids of rooms grown from expansion points (behind doors etc.)
        self.placed_areas = []    # area ids in placement order
        self.atlas = Atlas(self)

    # ------------------------------------------------------------------
    def note(self, msg):
        self.log.append(msg)

    def setting(self, key, default):
        return self.reg["settings"].get(key, default)

    def rng_range(self, val, default):
        val = val if val is not None else default
        if isinstance(val, list):
            return self.rng.randint(int(val[0]), int(val[1]))
        return int(val)

    # ------------------------------------------------------------------
    # Directions & linking
    # ------------------------------------------------------------------
    def opposite(self, d):
        if not d:
            return None
        return self.reg["directions"].get(d, {}).get("opposite")

    def allowed_dirs(self, room):
        """Directions the generator may use for a room's new exits.

        A region or area can list its own "directions" (a space station might use
        fore/aft/port/starboard).  Otherwise every automatic direction that isn't
        marked "default": false is allowed.
        """
        dirs = self.reg["directions"]
        listed = None
        if room is not None and room.region:
            listed = self.reg["regions"].get(room.region, {}).get("directions")
        if listed is None and room is not None and room.area:
            listed = self.area_def(room.area).get("directions")
        if listed is None and room is not None and room.props.get("path"):
            listed = self.reg["paths"].get(room.props["path"], {}).get("directions")
        if listed is None:
            listed = self.reg["settings"].get("directions")
        if listed is None:
            return [d for d, dd in dirs.items() if dd.get("auto", True) and dd.get("default", True)]
        return [d for d in listed if d in dirs]

    def link(self, a, b, dist, prefer=None, out_extra=None, back_extra=None, oneway=False):
        dirs = self.reg["directions"]
        used_a, used_b = self.w.used_dirs(a), self.w.used_dirs(b)
        allowed_a, allowed_b = self.allowed_dirs(a), self.allowed_dirs(b)

        def ok(d, both):
            if d in used_a:
                return False
            if oneway:
                return True
            opp = self.opposite(d)
            return bool(opp) and opp not in used_b and (not both or opp in allowed_b)
        cands = [d for d in allowed_a if ok(d, True)]
        if not cands:
            cands = [d for d in allowed_a if ok(d, False)]
        # With no sensible direction left the exit is simply named after where it leads.
        chosen = None
        if prefer in cands and self.rng.random() < 0.65:
            chosen = prefer
        elif cands:
            chosen = _weighted(self.rng, cands, lambda d: dirs[d].get("weight", 1))
        self.w.add_exit(a, b, chosen, dist, **(out_extra or {}))
        if not oneway:
            back = self.opposite(chosen)
            if back not in allowed_b or back in self.w.used_dirs(b):
                # A seam between two direction systems (say a forest and a space
                # station): the far side gets an exit named after its destination.
                back = None
            self.w.add_exit(b, a, back, dist, **(back_extra or {}))
        return chosen

    def free_dirs(self, room):
        if "story_skip" in room.tags:
            return []   # a scripted scene (an opening, an ending) never grows new exits
        return [d for d in self.allowed_dirs(room) if d not in self.w.used_dirs(room)]

    # ------------------------------------------------------------------
    # Areas
    # ------------------------------------------------------------------
    def area_def(self, area_id):
        """An area's definition; generated copies ("village~2") share their template's."""
        if not area_id:
            return {}
        adef = self.reg["areas"].get(area_id)
        if adef is None and "~" in area_id:
            adef = self.reg["areas"].get(area_id.split("~")[0])
        return adef or {}

    def area_room_ids(self, area_id):
        adef = self.area_def(area_id)
        if adef.get("layout"):
            return []
        rooms = adef.get("rooms") or {}
        if isinstance(rooms, dict):
            return ["%s/%s" % (area_id, rid) for rid in rooms]
        return expand_room_list(rooms, self.reg["rooms"])

    def resolve_room_ref(self, area_id, ref):
        local = "%s/%s" % (area_id, ref)
        if local in self.reg["rooms"]:
            return local
        if ref in self.reg["rooms"]:
            return ref
        return None

    def build_area(self, area_id, stage):
        adef = self.area_def(area_id)
        if adef.get("layout"):
            return self.build_layout_area(area_id, stage)
        uids = {}
        for rid in self.area_room_ids(area_id):
            if rid not in self.reg["rooms"]:
                self.note("area '%s': unknown room '%s'" % (area_id, rid))
                continue
            ent = self.w.instantiate("room:" + rid, uid=rid)
            ent.is_room = True
            ent.area = area_id
            ent.stage = stage
            for t in _as_list(adef.get("room_tags")):
                if t not in ent.tags:
                    ent.tags.append(t)
            uids[rid] = ent
        # Internal exits.
        for rid, ent in list(uids.items()):
            rdef = self.reg["rooms"][rid]
            for ex in rdef.get("exits") or []:
                target = self.resolve_room_ref(area_id, ex.get("to", ""))
                if target is None:
                    self.note("room '%s': exit to unknown room '%s'" % (rid, ex.get("to")))
                    continue
                if target not in uids:
                    # A shared standalone room pulled into this area.
                    if target in self.w.entities:
                        dest = self.w.entities[target]
                    else:
                        dest = self.w.instantiate("room:" + target, uid=target)
                        dest.is_room, dest.area, dest.stage = True, area_id, stage
                        uids[target] = dest
                else:
                    dest = uids[target]
                if any(x["to"] == dest.uid and x.get("dir") == ex.get("dir") for x in ent.exits):
                    continue
                extra = {k: ex[k] for k in ("name", "aliases", "description", "if", "blocked", "hidden",
                                            "visible_if", "show_dest", "on_use", "solve") if k in ex}
                self.w.add_exit(ent, dest, ex.get("dir"), ex.get("distance", 1), **extra)
                if not ex.get("oneway") and ex.get("back") is not False:
                    back = ex.get("back") or self.opposite(ex.get("dir"))
                    if not any(x["to"] == ent.uid for x in dest.exits):
                        bextra = {k[5:]: ex[k] for k in ex if k.startswith("back_")}
                        self.w.add_exit(dest, ent, back, ex.get("distance", 1), **bextra)
        entrances = [uids[self.resolve_room_ref(area_id, e)] for e in _as_list(adef.get("entrances"))
                     if self.resolve_room_ref(area_id, e) in uids]
        if not entrances:
            entrances = list(uids.values())
        name = self.w.grammar.expand(adef.get("name") or area_id)
        self.w.areas[area_id] = {
            "name": name,
            "rooms": [e.uid for e in uids.values()],
            "entrances": [e.uid for e in entrances],
            "stage": stage,
            "tags": _as_list(adef.get("tags")),
        }
        self.placed_areas.append(area_id)
        self.note("area '%s' (%s) placed at stage %d with %d rooms" % (area_id, name, stage, len(uids)))
        return self.w.areas[area_id]

    def build_layout_area(self, area_id, stage):
        """A generated area: its layout builds the rooms, its biomes furnish them."""
        adef = self.area_def(area_id)
        atlas = self.atlas
        biomes = atlas.area_biomes(area_id)
        pos = atlas.positions.get(area_id)
        rooms, entrances = atlas.build_layout(adef["layout"], biomes, stage, area_id, pos)
        for ent in rooms:
            for t in _as_list(adef.get("room_tags")) + _as_list(adef.get("tags")):
                if t not in ent.tags and t != "start":
                    ent.tags.append(t)
        with self.w.grammar.scoped(atlas.overlay(biomes)):
            name = self.w.grammar.expand(adef.get("name") or area_id.split("~")[0].replace("_", " "))
        self.w.areas[area_id] = {
            "name": name,
            "rooms": [e.uid for e in rooms],
            "entrances": [e.uid for e in entrances],
            "stage": stage,
            "tags": _as_list(adef.get("tags")),
            "biomes": atlas.flat(biomes),
            "generated": True,
        }
        self.placed_areas.append(area_id)
        self.note("area '%s' (%s) generated at stage %d with %d rooms, biomes %s"
                  % (area_id, name, stage, len(rooms), ", ".join(atlas.flat(biomes)) or "none"))
        return self.w.areas[area_id]

    def themes(self, room):
        if room is None:
            return set()
        tags = set(room.tags)
        if room.area:
            adef = self.area_def(room.area)
            tags |= set(_as_list(adef.get("tags"))) | set(_as_list(adef.get("theme")))
        if room.region:
            tags |= set(_as_list(self.reg["regions"].get(room.region, {}).get("tags")))
        return tags

    def pick_entrance(self, area_id, want_free=True):
        info = self.w.areas[area_id]
        rooms = [self.w.get(u) for u in info["entrances"]]
        free = [r for r in rooms if len(self.free_dirs(r)) >= 1] if want_free else rooms
        return self.rng.choice(free or rooms)

    # ------------------------------------------------------------------
    # Regions & filler
    # ------------------------------------------------------------------
    def regions(self):
        return {k: v for k, v in self.reg["regions"].items() if not v.get("abstract") and v.get("rooms")}

    # -- settings: fantasy next to science fiction needs a seam between them ----
    def settings_of(self, tags):
        return set(tags) & set(_as_list(self.setting("setting_tags", ["fantasy", "scifi"])))

    def clash(self, ta, tb):
        sa, sb = self.settings_of(ta), self.settings_of(tb)
        return bool(sa and sb and not (sa & sb))

    def def_setting(self, def_key):
        """A feature's setting: its own "setting" field, else the setting its mod is tagged with."""
        d = self.w.resolve_def(def_key) or {}
        if d.get("setting"):
            return self.settings_of(_as_list(d["setting"]))
        src = getattr(self.reg, "sources", {}).get(("features", def_key))
        for m in getattr(self.reg, "mods", []):
            if m["id"] == src:
                return self.settings_of(m.get("tags") or [])
        return set()

    def region_tags(self, rid):
        return set(_as_list(self.reg["regions"].get(rid, {}).get("tags")))

    def plain_regions(self):
        """Regions for ordinary country: everything but the seams between settings."""
        return sorted(r for r in self.regions() if not self.is_seam(r))

    def is_seam(self, rid):
        return "seam" in self.region_tags(rid)

    def choose_seam(self, ta, tb):
        seams = [r for r in sorted(self.regions()) if self.is_seam(r)]
        if not seams:
            return None
        return _weighted(self.rng, seams, lambda r: (1 + self.region_score(r, ta | tb)) * self.reg["regions"][r].get("weight", 1)
                         / (1 + 0.5 * self.region_use.get(r, 0)))

    def region_score(self, rid, themes):
        r = self.reg["regions"][rid]
        return len((set(_as_list(r.get("tags"))) | set(_as_list(r.get("connects")))) & themes)

    def choose_region(self, themes, exclude=(), context=None):
        plain = self.plain_regions()
        regs = [r for r in plain if r not in exclude] or plain
        if not regs:
            return None
        # Never wander from a fantasy place into science-fiction filler (or back) without a seam.
        ctx = themes | set(context or ())
        regs = [r for r in regs if not self.clash(ctx, self.region_tags(r))] or regs
        scores = {r: self.region_score(r, themes) for r in regs}
        top = max(scores.values())
        if top == 0:
            return _weighted(self.rng, regs, lambda r: self.reg["regions"][r].get("weight", 1))
        best = [r for r in regs if scores[r] >= max(1, top - 1)]
        return _weighted(self.rng, best, lambda r: (scores[r] + 1) ** 2 * self.reg["regions"][r].get("weight", 1)
                         / (1 + 0.5 * self.region_use.get(r, 0)))

    def make_filler(self, region_id, stage, expansion=False):
        region = self.reg["regions"][region_id]
        templates = region.get("rooms") or []
        use = self.region_use.setdefault(("tpl", region_id), {})

        def weight(i):
            t = templates[i]
            base = t.get("weight", 1) if isinstance(t, dict) else 1
            name = (t.get("name") if isinstance(t, dict) else self.reg["rooms"].get(t, {}).get("name")) or ""
            if use.get(i) and "#" not in name:
                return base * 0.02  # a fixed-name place should rarely appear twice
            return base / (1 + use.get(i, 0) * 1.5)
        idx = _weighted(self.rng, list(range(len(templates))), weight)
        use[idx] = use.get(idx, 0) + 1
        tpl = templates[idx]
        if isinstance(tpl, str):
            key = "room:" + tpl
        else:
            spec = copy.deepcopy(tpl)
            spec["room"] = True
            spec.pop("weight", None)
            key = self.w.register_inline_def(spec)
        ent = self.w.instantiate(key, uid=self.w.new_uid("f"))
        ent.is_room = True
        ent.region = region_id
        ent.stage = stage
        for t in _as_list(region.get("tags")):
            if t not in ent.tags:
                ent.tags.append(t)
        # Avoid two identical place names.
        names = {r.name for r in self.w.rooms() if r.uid != ent.uid}
        d = self.w.def_of(ent)
        tries = 0
        while ent.name in names and tries < 6 and "#" in (d.get("name") or ""):
            ent.name = self.w.grammar.expand(d["name"])
            tries += 1
        self.w.refresh_aliases(ent)
        for spec in region.get("features") or []:
            self.w.spawn_spec(spec, ent)
        self.region_use[region_id] = self.region_use.get(region_id, 0) + 1
        (self.expansion if expansion else self.filler).append(ent.uid)
        return ent

    def region_distance(self, region_id):
        region = self.reg["regions"].get(region_id, {})
        return self.rng_range(region.get("distance"), self.setting("filler_distance", [1, 3]))

    def connect(self, a, b, stage, short=False):
        """Join room a to room b with a generated path of filler rooms."""
        ta, tb = self.themes(a), self.themes(b)
        if self.clash(ta, tb):
            return self.connect_across(a, b, stage, ta, tb)
        regions = []
        # Both ends share a setting (or one has none): the whole path keeps to it.
        both = self.settings_of(ta | tb)
        ra = self.choose_region(ta | (tb if self.rng.random() < 0.3 else set()), context=both)
        if ra:
            regions.append(ra)
            rb = self.choose_region(tb, context=both)
            if rb and rb != ra and self.region_score(rb, tb) > self.region_score(ra, tb):
                regions.append(rb)
        chain = [a]
        if regions:
            for idx, rid in enumerate(regions):
                region = self.reg["regions"][rid]
                default_len = self.setting("path_length", [1, 3])
                n = max(1, int(round(self.rng_range(region.get("length"), default_len) * self.size)))
                if short:
                    n = min(n, self.rng.randint(1, 2))
                if len(regions) > 1:
                    n = max(1, (n * 2) // 3)
                for _ in range(max(1, n)):
                    chain.append(self.make_filler(rid, stage))
        chain.append(b)
        heading = None
        for idx in range(len(chain) - 1):
            x, y = chain[idx], chain[idx + 1]
            region = y.region or x.region
            dist = self.region_distance(region) if region else self.rng_range(
                self.setting("direct_distance", [3, 6]), [3, 6])
            out_extra = {}
            heading = self.link(x, y, dist, prefer=heading, out_extra=out_extra)
        if b.area:
            self.entries.setdefault(b.area, (chain[-2].uid, chain[-2].exits[-1]))
        return chain

    def connect_across(self, a, b, stage, ta, tb):
        """Two settings meet: each side's own country, and a seam region between them if any mod has one."""
        legs = [(self.choose_region(ta), 1), (self.choose_seam(ta, tb), self.rng.randint(1, 2)), (self.choose_region(tb), 1)]
        chain = [a]
        for rid, n in legs:
            if rid is None:
                continue
            for _ in range(max(1, int(round(n * min(self.size, 1.5))))):
                chain.append(self.make_filler(rid, stage))
        chain.append(b)
        heading = None
        for x, y in zip(chain, chain[1:]):
            region = y.region or x.region
            dist = self.region_distance(region) if region else self.rng_range(
                self.setting("direct_distance", [3, 6]), [3, 6])
            heading = self.link(x, y, dist, prefer=heading, out_extra={})
        if b.area:
            self.entries.setdefault(b.area, (chain[-2].uid, chain[-2].exits[-1]))
        return chain

    # ------------------------------------------------------------------
    # Placement helpers
    # ------------------------------------------------------------------
    def rooms_with_stage(self, max_stage, filler_only=False):
        out = []
        for r in self.w.rooms():
            if r.stage <= max_stage and (not filler_only or r.uid in self.filler):
                out.append(r)
        return sorted(out, key=lambda r: r.uid)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def generate(self):
        w = self.w
        planner = StoryPlanner(self)
        planner.plan()
        spine = list(planner.accessible)
        start_area = planner.start_area

        if self.atlas.paths():
            # Areas on a biome map, joined by paths.
            self.atlas.build(spine, start_area)
            if not spine and not self.atlas.nodes:
                self.build_sandbox()
            self.build_expansions()
            self.create_player(start_area)
            self.populate()
            StoryBinder(self, planner).bind()
            self.plant_rumours()
            self.finish()
            return w

        prev_room = None
        if spine and start_area is None and self.plain_regions():
            # No mod offers a starting place: begin out in the wilds, on the way in.
            first = self.make_filler(self.choose_region(set(_as_list(self.reg["areas"][spine[0]].get("theme")))), 0)
            self.sandbox_start = first
            prev_room = first
        for idx, area_id in enumerate(spine):
            self.build_area(area_id, idx)
            if prev_room is not None:
                entrance = self.pick_entrance(area_id)
                self.connect(prev_room, entrance, max(0, idx - 1))
            # The next leg leaves from a different entrance where possible.
            prev_room = self.pick_entrance(area_id)

        if not spine:
            self.build_sandbox()

        self.place_side_areas(len(spine))
        self.add_branches_and_loops()
        self.build_expansions()
        self.create_player(start_area)
        self.populate()
        StoryBinder(self, planner).bind()
        self.plant_rumours()
        self.finish()
        return w

    def build_sandbox(self):
        regs = self.plain_regions()
        if not regs:
            raise GenerationError(
                "The selected mods define no areas and no regions, so there is no world to build. "
                "Select at least one mod that adds places.")
        size = int(self.rng_range(self.setting("sandbox_size", [10, 16]), [10, 16]) * self.size)
        first = self.make_filler(self.rng.choice(regs), 0)
        rooms = [first]
        while len(rooms) < size:
            anchor = self.rng.choice([r for r in rooms if self.free_dirs(r)] or rooms)
            if self.rng.random() < 0.7:
                rid = anchor.region
            else:
                rid = self.choose_region(self.themes(anchor), exclude=(anchor.region,))
            new = self.make_filler(rid, 0)
            self.link(anchor, new, self.region_distance(rid))
            rooms.append(new)
        self.sandbox_start = first

    def side_area_ids(self, spine):
        """Every other area the mods offer (not generated copies), in a random order, up to the cap."""
        areas = self.reg["areas"]
        side = [a for a in sorted(areas) if a not in self.w.areas and a not in spine and not areas[a].get("abstract")
                and areas[a].get("include", True) and not areas[a].get("only_if_used") and not areas[a].get("start_only")
                and not areas[a].get("copies")]
        self.rng.shuffle(side)
        return side[:self.setting("max_side_areas", 12)]

    def place_side_areas(self, spine_len):
        w = self.w
        areas = self.reg["areas"]
        side = self.side_area_ids([])
        for area_id in side:
            adef = areas[area_id]
            max_stage = max(0, spine_len - 1)
            want = adef.get("stage")
            pool = [w.get(u) for u in self.filler] or [r for r in w.rooms() if "story_skip" not in r.tags]
            if want is not None:
                pool = [r for r in pool if r.stage <= int(want)] or pool
            pool = [r for r in pool if r.stage <= max_stage and self.free_dirs(r)] or pool
            # Prefer anchors whose surroundings suit the area.
            tags = set(_as_list(adef.get("tags"))) | set(_as_list(adef.get("theme")))
            anchor = _weighted(self.rng, sorted(pool, key=lambda r: r.uid),
                               lambda r: (1 + 3 * len(self.themes(r) & tags)) * (0.15 if self.clash(self.themes(r), tags) else 1))
            if anchor is None:
                continue
            info = self.build_area(area_id, anchor.stage)
            entrance = self.pick_entrance(area_id)
            if self.plain_regions() and (self.rng.random() < 0.75 or self.clash(self.themes(anchor), self.themes(entrance))):
                self.connect(anchor, entrance, anchor.stage, short=True)
            else:
                self.link(anchor, entrance, self.region_distance(anchor.region) if anchor.region else 2)
            info["side"] = True

    def grow_region(self, tag, stage):
        """Generate a short spur of rooms from a region with *tag* when a story
        element asks to be placed somewhere the world doesn't have yet."""
        regs = [r for r in self.plain_regions()
                if tag == r or tag in _as_list(self.reg["regions"][r].get("tags"))]
        if not regs:
            return None
        rid = self.rng.choice(regs)
        rtags = set(_as_list(self.reg["regions"][rid].get("tags"))) | set(_as_list(self.reg["regions"][rid].get("connects")))
        # Grow from generated rooms when possible: hand-built rooms may sit behind
        # locked doors that the story hasn't opened yet.
        anchors = [r for r in self.rooms_with_stage(stage, filler_only=True) if self.free_dirs(r)]
        anchors = anchors or [r for r in self.rooms_with_stage(stage) if self.free_dirs(r)
                              and r.uid in self.w.areas.get(r.area, {}).get("entrances", [])]
        anchors = [r for r in anchors if not self.clash(self.themes(r), rtags)] or anchors
        if not anchors:
            return None
        anchor = _weighted(self.rng, anchors, lambda r: 1 + 3 * len(self.themes(r) & rtags) + (2 if r.uid in self.filler else 0))
        prev, last = anchor, None
        if self.clash(self.themes(anchor), rtags):
            seam = self.choose_seam(self.themes(anchor), rtags)
            if seam:
                for _ in range(self.rng.randint(1, 2)):
                    last = self.make_filler(seam, anchor.stage)
                    self.link(prev, last, self.region_distance(seam))
                    prev = last
        for _ in range(self.rng_range(self.reg["regions"][rid].get("length"), [1, 2])):
            last = self.make_filler(rid, anchor.stage)
            self.link(prev, last, self.region_distance(rid))
            prev = last
        self.note("grew region '%s' off %s for a story element" % (rid, anchor.name))
        return last

    # ------------------------------------------------------------------
    # Expansion points: generated sections behind locked doors, off open ground...
    # ------------------------------------------------------------------
    def build_expansions(self):
        w = self.w
        for room in sorted(w.rooms(), key=lambda r: r.uid):
            if room.uid in self.filler or room.uid in self.expansion:
                continue
            for spec in _as_list(w.def_of(room).get("expansions")):
                if self.rng.random() < float(spec.get("chance", 1)):
                    self.expand_from(room, spec)

    def expand_from(self, room, spec):
        tags = set(_as_list(spec.get("tags")))
        regs = [r for r in sorted(self.regions())
                if tags & (set(_as_list(self.reg["regions"][r].get("tags"))) | set(_as_list(self.reg["regions"][r].get("connects"))))
                and not self.is_seam(r)]
        regs = [r for r in regs if not self.clash(self.themes(room), self.region_tags(r))] or regs
        if not regs:
            return None
        score = lambda r: 1 + len(tags & set(_as_list(self.reg["regions"][r].get("tags"))))
        rid = _weighted(self.rng, regs, lambda r: score(r) ** 2 * self.reg["regions"][r].get("weight", 1))
        n = max(1, int(round(self.rng_range(spec.get("length"), [2, 4]) * self.size)))
        first = self.make_filler(rid, room.stage, expansion=True)
        out_extra = {k: spec[k] for k in ("name", "aliases", "description") if k in spec}
        self.link(room, first, self.rng_range(spec.get("distance"), [1, 2]), prefer=spec.get("dir"), out_extra=out_extra)
        exit_ = next(ex for ex in reversed(room.exits) if ex["to"] == first.uid)
        if spec.get("door"):
            self.make_door(room, exit_, spec["door"])
        nodes = [first]
        for _ in range(n - 1):
            anchors = [x for x in nodes if self.free_dirs(x)] or nodes
            anchor = self.rng.choice(anchors)
            rid2 = rid if self.rng.random() < 0.75 else _weighted(self.rng, regs, score)
            new = self.make_filler(rid2, room.stage, expansion=True)
            self.link(anchor, new, self.region_distance(rid2))
            nodes.append(new)
        if len(nodes) > 3 and self.rng.random() < 0.5:
            a, b = self.rng.sample(nodes, 2)
            if not any(x["to"] == b.uid for x in a.exits) and self.free_dirs(a) and self.free_dirs(b):
                self.link(a, b, self.region_distance(b.region))
        return nodes

    def make_door(self, room, exit_, door):
        """A door on an expansion exit, opened by anything that affords what it needs."""
        w = self.w
        if isinstance(door, str):
            od = self.reg["obstacles"].get(door) or {}
        else:
            od = door
        spec = copy.deepcopy(od.get("feature") or {"name": "door"})
        spec["extends"] = _as_list(spec.get("extends")) + ["scenery"]
        spec["tags"] = _as_list(spec.get("tags")) + ["expansion_door"]
        spec["props"] = dict(spec.get("props") or {}, open=False, locked=True)
        e = w.spawn_spec(spec, room)[0]
        needs = _as_list(od.get("needs"))
        # Obstacle texts written for the story name the key; a generated door opens to whatever fits.
        ctx = self.i.ctx(self_ent=e, local={"key": w.string("door_any_key", "the right tool")})
        opened = [{"set": {"open": True, "locked": False}},
                  self.i.render(od.get("open_text") or "{self.The} opens.", ctx)]
        locked = self.i.render(od.get("locked_text") or "{self.The} won't open.", ctx)
        already = {"if": {"prop": "open"}, "do": [self.i.render(od.get("open_already") or "{self.The} is already open.", ctx)]}
        if needs:
            holds = {"has": {"affords": needs}}
            for verb in ["open", "unlock", "use", "push"] + _as_list(od.get("verbs")):
                w.add_action(e, verb, already, first=False)
                w.add_action(e, verb, {"if": holds, "do": opened}, first=False)
                w.add_action(e, verb, {"do": [locked]}, first=False)
            for verb in ["use", "put"] + _as_list(od.get("verbs")):
                w.add_action(e, verb + "_with", {"if": {"is": {"affords": needs}, "of": "target"}, "do": opened}, first=False)
        else:
            for verb in ["open", "use", "push"]:
                w.add_action(e, verb, already, first=False)
                w.add_action(e, verb, {"do": opened}, first=False)
        exit_["if"] = {"prop": "open", "of": "uid:" + e.uid}
        exit_["blocked"] = self.i.render(od.get("blocked") or "{self.The} is shut.", ctx)
        return e

    def add_branches_and_loops(self):
        w = self.w
        chance = min(0.9, self.setting("branch_chance", 0.25) * self.size)
        for uid in list(self.filler):
            room = w.get(uid)
            if room is None or not room.region or not self.free_dirs(room):
                continue
            if self.rng.random() < chance:
                rid = room.region
                if self.rng.random() < 0.3:
                    rid = self.choose_region(self.themes(room), exclude=(room.region,)) or rid
                nook = self.make_filler(rid, room.stage)
                self.link(room, nook, self.region_distance(room.region))
        loops = int(round(self.rng_range(self.setting("loops", [1, 3]), [1, 3]) * self.size))
        for _ in range(loops * 4):
            if loops <= 0:
                break
            cands = [w.get(u) for u in self.filler if self.free_dirs(w.get(u))]
            if len(cands) < 2:
                break
            a = self.rng.choice(cands)
            same = [r for r in cands if r.uid != a.uid and r.stage == a.stage
                    and not any(x["to"] == r.uid for x in a.exits)
                    and not self.clash(self.themes(a), self.themes(r))
                    and (r.region == a.region or self.rng.random() < 0.3)]
            if not same:
                continue
            b = self.rng.choice(same)
            if not any(self.opposite(d) in self.free_dirs(b) for d in self.free_dirs(a)):
                continue
            self.link(a, b, self.region_distance(a.region))
            loops -= 1

    def create_player(self, start_area):
        w = self.w
        base = "player" if w.resolve_def("player") else None
        spec = {}
        if base is None:
            spec["name"] = w.string("player_name", "yourself")
        key = w.register_inline_def(spec, base)
        player = w.instantiate(key, uid="player")
        w.player_uid = player.uid
        if self.player_name:
            w.vars["player_name"] = self.player_name
        elif w.grammar.has("hero_name"):
            w.vars["player_name"] = w.grammar.expand("#hero_name#")
        else:
            w.vars["player_name"] = w.string("default_hero_name", "the wanderer")
        start = None
        if start_area:
            rid = self.reg["areas"][start_area].get("start")
            if rid:
                start = w.get(self.resolve_room_ref(start_area, rid))
            if start is None:
                start = w.get(self.w.areas[start_area]["entrances"][0])
        if start is None:
            start = getattr(self, "sandbox_start", None) or self.rooms_with_stage(0)[0]
        w.place(player, start)
        # A starting area can say who you are and what you carry (one game, several protagonists).
        adef = self.reg["areas"].get(start_area, {}) if start_area else {}
        if adef.get("player"):
            pd = adef["player"]
            if pd.get("name"):
                player.name = w.grammar.expand(pd["name"])
                player.article = "" if pd.get("proper", True) else None
                w.refresh_aliases(player, {"aliases": ["me", "myself", "self"] + _as_list(pd.get("aliases"))})
            for key in ("description",):
                if pd.get(key):
                    player.texts[key] = pd[key]
            player.props.update({k: w._rand_value(v) for k, v in (pd.get("props") or {}).items()})
            for t in _as_list(pd.get("tags")):
                if t not in player.tags:
                    player.tags.append(t)
            if pd.get("player_name") and not self.player_name:
                w.vars["player_name"] = pd["player_name"]
        for spec in _as_list(adef.get("kit")):
            w.spawn_spec(spec, player)

    def populate(self):
        """Scatter wandering features and encounters into generated rooms."""
        w = self.w
        scatter = [d for d in w.defs_with_tags("scatter")]
        encounters = [d for d in w.defs_with_tags("encounter")]
        sc, ec = self.setting("scatter_chance", 0.4), self.setting("encounter_chance", 0.2)
        start = w.room_of(w.player)

        def suits(def_key, room):
            if self.clash(self.def_setting(def_key), self.themes(room)):
                return False   # no headcrabs in the hay meadow, no wolves in the server room
            hab = _as_list(w.resolve_def(def_key).get("habitat"))
            return not hab or bool(set(hab) & set(room.tags))
        targets = [w.get(u) for u in self.filler + self.expansion]
        for area_id, info in w.areas.items():
            if self.area_def(area_id).get("allow_scatter"):
                targets.extend(w.get(u) for u in info["rooms"])
        for room in targets:
            if room is None:
                continue
            if scatter and self.rng.random() < sc:
                opts = [d for d in scatter if suits(d, room)]
                if opts:
                    pick = _weighted(self.rng, opts, lambda d: w.resolve_def(d).get("weight", 1))
                    w.spawn_spec(pick, room)
            if encounters and room is not start and self.rng.random() < ec:
                opts = [d for d in encounters if suits(d, room)
                        and int(w.resolve_def(d).get("min_stage", 0)) <= room.stage]
                if opts:
                    pick = _weighted(self.rng, opts, lambda d: w.resolve_def(d).get("weight", 1))
                    w.spawn_spec(pick, room)

    def plant_rumours(self):
        """Put travellers on the roads who point toward what the story needs next."""
        w = self.w
        wanderers = w.defs_with_tags("wanderer")
        steps = w.story.get("steps", [])
        chance = self.setting("rumour_chance", 0.5)
        fillers = [w.get(u) for u in self.filler if w.get(u)]
        if not fillers or not steps:
            return
        for j, step in enumerate(steps):
            if not step.get("hint") or self.rng.random() > chance:
                continue
            room = self.rng.choice(fillers)
            ctx = self.i.ctx(beat=j, local={"hint": step["hint"]})
            text = self.i.render(w.string("rumour_frame", "{hint}") if not w.grammar.has("rumour_frame")
                                 else "#rumour_frame#", ctx)
            fits = [d for d in wanderers
                    if not w.resolve_def(d).get("habitat")
                    or set(_as_list(w.resolve_def(d).get("habitat"))) & set(room.tags)]
            if fits:
                made = w.spawn_spec(self.rng.choice(fits), room)
                if made:
                    made[0].props["rumor"] = text
            else:
                w.spawn_spec({"name": w.string("rumour_object", "scrawled message"),
                              "extends": ["readable"], "tags": ["rumour"], "description": text,
                              "props": {"text": text},
                              "appearance": w.string("rumour_appearance", "Someone has left a message here.")}, room)

    def tell_doors_apart(self):
        """Two doors with one name in a room (a story's locked door beside a generated one) can't be
        told apart by the parser: name the generated ones by where they lead."""
        w = self.w
        for room in w.rooms():
            kids = [w.get(c) for c in room.children if w.get(c) is not None]
            names = [k.name for k in kids]
            for k in kids:
                if "expansion_door" not in k.tags or names.count(k.name) < 2:
                    continue
                ex = next((x for x in room.exits if (x.get("if") or {}).get("of") == "uid:" + k.uid), None)
                if ex and ex.get("dir"):
                    label = self.reg["directions"].get(ex["dir"], {}).get("name") or ex["dir"]
                    names.remove(k.name)
                    k.name = "%s to the %s" % (k.name, label)
                    names.append(k.name)

    def finish(self):
        w = self.w
        self.tell_doors_apart()
        missing = sorted(w.grammar.missing)
        if missing:
            self.note("grammar symbols with no rules: %s" % ", ".join(missing))
        self.note("world: %d rooms (%d generated), %d areas, %d features" % (
            len(w.rooms()), len(self.filler), len(w.areas),
            len([e for e in w.entities.values() if not e.is_room])))


def generate(registry, seed=None, player_name=None, size="medium", start=None):
    gen = Generator(registry, seed, player_name, size, start)
    world = gen.generate()
    return world, gen.log
