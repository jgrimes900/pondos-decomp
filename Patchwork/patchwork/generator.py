"""World and story generation.

The generator owns no content.  It takes the merged registry of the selected
mods and:

1. picks a premise (if any mod supplies one) and plans a chain of story beats
   pulled from every mod, ordered by stage (opening -> middle -> climax);
2. builds the hand-authored areas those beats take place in, plus the start
   area, and lays them out along a "spine";
3. stitches the areas together with novel filler rooms generated from region
   definitions (with themed transitions when two areas differ), adds side
   branches, loops and every other optional area the mods provide;
4. scatters wandering features and encounters, binds story roles (finding
   existing characters/items or spawning new ones with generated names), gates
   later areas behind earlier beats, and plants rumours that point the player
   toward the next beat.
"""

import copy

from .logic import Interpreter
from .world import World

DEFAULT_STRUCTURE = ["opening", "middle*", "climax"]


class GenerationError(Exception):
    pass


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
    def __init__(self, registry, seed=None, premise=None, player_name=None, size="medium"):
        self.size = SIZES.get(size, size if isinstance(size, (int, float)) else 1.0)
        self.reg = registry
        self.w = World(registry, seed)
        self.i = Interpreter(self.w)
        self.rng = self.w.rng
        self.premise_choice = premise
        self.player_name = player_name
        self.log = []
        self.region_use = {}
        self.filler = []          # uids of generated filler rooms
        self.placed_areas = []    # area ids in placement order

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
            listed = self.reg["areas"].get(room.area, {}).get("directions")
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
        return [d for d in self.allowed_dirs(room) if d not in self.w.used_dirs(room)]

    # ------------------------------------------------------------------
    # Premise and story planning
    # ------------------------------------------------------------------
    def choose_premise(self):
        premises = {k: v for k, v in self.reg["premises"].items() if not v.get("abstract")}
        if self.premise_choice and self.premise_choice in premises:
            return self.premise_choice, premises[self.premise_choice]
        if self.premise_choice == "none" or not premises:
            return None, {}
        pid = _weighted(self.rng, sorted(premises), lambda k: premises[k].get("weight", 1))
        return pid, premises[pid]

    def resolve_area_ref(self, ref, used):
        areas = self.reg["areas"]
        if ref is None:
            return None
        if isinstance(ref, str):
            return ref if ref in areas else False
        tags = _as_list(ref.get("tags"))
        cands = [a for a, ad in areas.items()
                 if not ad.get("abstract") and all(t in _as_list(ad.get("tags")) for t in tags)]
        if not cands:
            return False
        fresh = [a for a in cands if a not in used]
        return self.rng.choice(sorted(fresh or cands))

    def plan_story(self, premise):
        beats = {k: v for k, v in self.reg["beats"].items() if not v.get("abstract")}
        ptags = set(_as_list(premise.get("beat_tags")) + _as_list(premise.get("tags")))
        plan, used_areas, provided = [], [], set()

        def usable(bid):
            b = beats[bid]
            allowed = _as_list(b.get("premises"))
            if allowed and premise.get("_id") not in allowed:
                return False
            # A strict premise only accepts beats sharing one of its beat_tags.
            if premise.get("strict") and ptags and not ptags & set(_as_list(b.get("tags"))):
                return False
            return True

        def add(bid):
            b = beats[bid]
            area = self.resolve_area_ref(b.get("area"), used_areas)
            if area is False:
                self.note("beat '%s' skipped: its area is not available" % bid)
                return False
            if area:
                used_areas.append(area)
            plan.append({"id": bid, "def": b, "area": area})
            provided.update(_as_list(b.get("provides")))
            return True

        if premise.get("beats"):
            for bid in premise["beats"]:
                if bid in beats:
                    add(bid)
            return plan

        structure = list(premise.get("structure") or self.setting("default_structure", DEFAULT_STRUCTURE))
        max_mid = self.setting("max_middle_beats", 4)
        taken = set()

        def stages_of(b):
            return _as_list(b.get("stage") or "middle")

        def pick(stage):
            cands = [bid for bid in sorted(beats) if bid not in taken and usable(bid) and stage in stages_of(beats[bid])]

            def weight(bid):
                b = beats[bid]
                w = float(b.get("weight", 1))
                if ptags and ptags & set(_as_list(b.get("tags"))):
                    w *= 4
                needs = set(_as_list(b.get("needs")))
                if needs and not needs <= provided:
                    w *= 0.15
                return w
            while cands:
                bid = _weighted(self.rng, cands, weight)
                cands.remove(bid)
                taken.add(bid)
                if add(bid):
                    return True
            return False

        for slot in structure:
            if slot.endswith("*"):
                stage = slot[:-1]
                n = 0
                while n < max_mid and pick(stage):
                    n += 1
            else:
                pick(slot)
        # Order beats so that anything providing what another needs comes first.
        return plan

    # ------------------------------------------------------------------
    # Areas
    # ------------------------------------------------------------------
    def area_room_ids(self, area_id):
        adef = self.reg["areas"][area_id]
        rooms = adef.get("rooms") or {}
        if isinstance(rooms, dict):
            return ["%s/%s" % (area_id, rid) for rid in rooms]
        return list(rooms)

    def resolve_room_ref(self, area_id, ref):
        local = "%s/%s" % (area_id, ref)
        if local in self.reg["rooms"]:
            return local
        if ref in self.reg["rooms"]:
            return ref
        return None

    def build_area(self, area_id, stage):
        adef = self.reg["areas"][area_id]
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
                                            "visible_if", "show_dest", "on_use") if k in ex}
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

    def themes(self, room):
        if room is None:
            return set()
        tags = set(room.tags)
        if room.area:
            adef = self.reg["areas"].get(room.area, {})
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

    def region_score(self, rid, themes):
        r = self.reg["regions"][rid]
        return len((set(_as_list(r.get("tags"))) | set(_as_list(r.get("connects")))) & themes)

    def choose_region(self, themes, exclude=()):
        regs = [r for r in sorted(self.regions()) if r not in exclude] or sorted(self.regions())
        if not regs:
            return None
        scores = {r: self.region_score(r, themes) for r in regs}
        top = max(scores.values())
        if top == 0:
            return _weighted(self.rng, regs, lambda r: self.reg["regions"][r].get("weight", 1))
        best = [r for r in regs if scores[r] >= max(1, top - 1)]
        return _weighted(self.rng, best, lambda r: (scores[r] + 1) ** 2 * self.reg["regions"][r].get("weight", 1)
                         / (1 + 0.5 * self.region_use.get(r, 0)))

    def make_filler(self, region_id, stage):
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
        self.filler.append(ent.uid)
        return ent

    def region_distance(self, region_id):
        region = self.reg["regions"].get(region_id, {})
        return self.rng_range(region.get("distance"), self.setting("filler_distance", [1, 3]))

    def connect(self, a, b, stage, gate=None, short=False):
        """Join room a to room b with a generated path of filler rooms."""
        ta, tb = self.themes(a), self.themes(b)
        regions = []
        ra = self.choose_region(ta | (tb if self.rng.random() < 0.3 else set()))
        if ra:
            regions.append(ra)
            rb = self.choose_region(tb)
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
            if gate and y is b:
                out_extra = {"if": {"beat_reached": gate["beat"]}, "blocked": gate["text"]}
            heading = self.link(x, y, dist, prefer=heading, out_extra=out_extra)
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

    def location(self, spec, beat, roles):
        """Resolve a beat/role placement spec to a container entity."""
        w = self.w
        area = beat.get("area")
        stage = beat.get("stage", 0)
        area_rooms = [w.get(u) for u in w.areas.get(area, {}).get("rooms", [])] if area else []
        if spec is None or spec == "area":
            pool = area_rooms or self.rooms_with_stage(stage)
            return self.rng.choice(pool) if pool else w.room_of(w.player)
        if spec == "start":
            return w.room_of(w.player)
        if spec == "player":
            return w.player
        if spec == "before":
            pool = self.rooms_with_stage(max(0, stage - 1), filler_only=True) or self.rooms_with_stage(max(0, stage - 1))
            return self.rng.choice(pool) if pool else w.room_of(w.player)
        if spec == "anywhere":
            pool = self.rooms_with_stage(stage)
            return self.rng.choice(pool)
        if isinstance(spec, str):
            spec = {"room": spec}
        if "role" in spec and spec["role"] in roles:
            return w.get(roles[spec["role"]])
        if "room" in spec and area:
            rid = self.resolve_room_ref(area, spec["room"])
            if rid and rid in w.entities:
                return w.entities[rid]
        if "area" in spec and spec["area"] in w.areas:
            return w.get(self.rng.choice(w.areas[spec["area"]]["rooms"]))
        if "room_tags" in spec:
            tags = _as_list(spec["room_tags"])
            pool = [r for r in (area_rooms or self.rooms_with_stage(stage)) if all(t in r.tags for t in tags)]
            if pool:
                return self.rng.choice(pool)
        if "region" in spec:
            pool = [r for r in self.rooms_with_stage(stage, True) if spec["region"] in r.tags]
            if pool:
                return self.rng.choice(pool)
            grown = self.grow_region(spec["region"], max(0, stage - 1))
            if grown is not None:
                return grown
        if "feature" in spec:
            scope = area_rooms or self.rooms_with_stage(stage)
            pool = []
            for r in scope:
                pool.extend(e for e in w.descendants(r) if self.i.match(e, spec["feature"]))
            if pool:
                return self.rng.choice(sorted(pool, key=lambda e: e.uid))
        pool = area_rooms or self.rooms_with_stage(stage)
        return self.rng.choice(pool) if pool else w.room_of(w.player)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def generate(self):
        w = self.w
        pid, premise = self.choose_premise()
        premise = dict(premise)
        premise["_id"] = pid
        plan = self.plan_story(premise)
        self.note("premise: %s" % (pid or "(none)"))
        self.note("story plan: %s" % (", ".join(b["id"] for b in plan) or "(free exploration)"))

        start_area = self.choose_start_area(premise, plan)
        spine = []
        if start_area:
            spine.append(start_area)
        for b in plan:
            if b["area"] and b["area"] not in spine:
                spine.append(b["area"])

        # Build spine areas and connect them in order.
        prev_room = None
        for idx, area_id in enumerate(spine):
            first_beat = next((j for j, b in enumerate(plan) if b["area"] == area_id), None)
            gate = None
            if first_beat is not None and first_beat > 0:
                gtext = plan[first_beat]["def"].get("gate")
                if gtext:
                    gate = {"beat": plan[first_beat]["id"],
                            "text": gtext if isinstance(gtext, str) else w.string(
                                "gate_blocked", "Something tells you it is not yet time to go that way.")}
            self.build_area(area_id, idx)
            if prev_room is not None:
                entrance = self.pick_entrance(area_id)
                self.connect(prev_room, entrance, idx - 1, gate=gate)
            # The next leg leaves from a different entrance where possible.
            prev_room = self.pick_entrance(area_id)

        if not spine:
            self.build_sandbox()

        stage = 0
        for b in plan:
            # A beat without an area of its own happens wherever the story has reached.
            stage = w.areas[b["area"]]["stage"] if b["area"] in w.areas else stage
            b["stage"] = stage

        self.place_side_areas(len(spine))
        self.add_branches_and_loops()
        self.create_player(premise, start_area)
        self.populate()
        self.bind_story(premise, pid, plan)
        self.plant_rumours()
        self.finish(premise)
        return w

    def choose_start_area(self, premise, plan):
        areas = self.reg["areas"]
        ref = premise.get("start_area")
        if ref:
            got = self.resolve_area_ref(ref, [])
            if got:
                return got
        if plan and plan[0]["area"] and "start" in _as_list(areas[plan[0]["area"]].get("tags")):
            return plan[0]["area"]
        ptags = set(_as_list(premise.get("tags")))
        used = {b["area"] for b in plan}
        starts = [a for a, ad in sorted(areas.items())
                  if "start" in _as_list(ad.get("tags")) and not ad.get("abstract")
                  and (a not in used or (plan and plan[0]["area"] == a))]
        if starts:
            return _weighted(self.rng, starts,
                             lambda a: 1 + 4 * len(ptags & set(_as_list(areas[a].get("tags")))))
        if plan and plan[0]["area"]:
            return plan[0]["area"]
        return None

    def build_sandbox(self):
        regs = sorted(self.regions())
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

    def place_side_areas(self, spine_len):
        w = self.w
        areas = self.reg["areas"]
        side = [a for a in sorted(areas) if a not in w.areas and not areas[a].get("abstract")
                and areas[a].get("include", True) and not areas[a].get("only_with_beat")]
        self.rng.shuffle(side)
        side = side[:self.setting("max_side_areas", 12)]
        for area_id in side:
            adef = areas[area_id]
            max_stage = max(0, spine_len - 1)
            want = adef.get("stage")
            pool = [w.get(u) for u in self.filler] or [r for r in w.rooms()]
            if want is not None:
                pool = [r for r in pool if r.stage <= int(want)] or pool
            pool = [r for r in pool if r.stage <= max_stage and self.free_dirs(r)] or pool
            # Prefer anchors whose surroundings suit the area.
            tags = set(_as_list(adef.get("tags"))) | set(_as_list(adef.get("theme")))
            anchor = _weighted(self.rng, sorted(pool, key=lambda r: r.uid),
                               lambda r: 1 + 3 * len(self.themes(r) & tags))
            if anchor is None:
                continue
            info = self.build_area(area_id, anchor.stage)
            entrance = self.pick_entrance(area_id)
            if self.regions() and self.rng.random() < 0.75:
                self.connect(anchor, entrance, anchor.stage, short=True)
            else:
                self.link(anchor, entrance, self.region_distance(anchor.region) if anchor.region else 2)
            info["side"] = True

    def grow_region(self, tag, stage):
        """Generate a short spur of rooms from a region with *tag* when a story
        element asks to be placed somewhere the world doesn't have yet."""
        regs = [r for r in sorted(self.regions())
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
        if not anchors:
            return None
        anchor = _weighted(self.rng, anchors, lambda r: 1 + 3 * len(self.themes(r) & rtags) + (2 if r.uid in self.filler else 0))
        prev, last = anchor, None
        for _ in range(self.rng_range(self.reg["regions"][rid].get("length"), [1, 2])):
            last = self.make_filler(rid, anchor.stage)
            self.link(prev, last, self.region_distance(rid))
            prev = last
        self.note("grew region '%s' off %s for a story element" % (rid, anchor.name))
        return last

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
                    and (r.region == a.region or self.rng.random() < 0.3)]
            if not same:
                continue
            b = self.rng.choice(same)
            if not any(self.opposite(d) in self.free_dirs(b) for d in self.free_dirs(a)):
                continue
            self.link(a, b, self.region_distance(a.region))
            loops -= 1

    def create_player(self, premise, start_area):
        w = self.w
        base = "player" if w.resolve_def("player") else None
        spec = copy.deepcopy(premise.get("player") or {})
        spec.setdefault("name", w.string("player_name", "yourself") if base is None else
                        w.resolve_def("player").get("name", "yourself"))
        key = w.register_inline_def(spec, base)
        player = w.instantiate(key, uid="player")
        w.player_uid = player.uid
        if self.player_name:
            w.vars["player_name"] = self.player_name
        elif w.grammar.has("hero_name"):
            w.vars["player_name"] = w.grammar.expand("#hero_name#")
        else:
            w.vars["player_name"] = w.string("default_hero_name", "the wanderer")
        # Starting room
        start = None
        if start_area:
            adef = self.reg["areas"][start_area]
            rid = adef.get("start")
            if premise.get("start_room"):
                rid = premise["start_room"]
            if rid:
                start = w.get(self.resolve_room_ref(start_area, rid))
            if start is None:
                start = w.get(self.w.areas[start_area]["entrances"][0])
        if start is None:
            start = getattr(self, "sandbox_start", None) or self.rooms_with_stage(0)[0]
        w.place(player, start)
        for spec in premise.get("inventory") or []:
            w.spawn_spec(spec, player)

    def populate(self):
        """Scatter wandering features and encounters into generated rooms."""
        w = self.w
        scatter = [d for d in w.defs_with_tags("scatter")]
        encounters = [d for d in w.defs_with_tags("encounter")]
        sc, ec = self.setting("scatter_chance", 0.4), self.setting("encounter_chance", 0.2)
        start = w.room_of(w.player)

        def suits(def_key, room):
            hab = _as_list(w.resolve_def(def_key).get("habitat"))
            return not hab or bool(set(hab) & set(room.tags))
        targets = [w.get(u) for u in self.filler]
        for area_id, info in w.areas.items():
            if self.reg["areas"].get(area_id, {}).get("allow_scatter"):
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

    def bind_story(self, premise, pid, plan):
        w = self.w
        story_beats = []
        for b in plan:
            bdef = b["def"]
            beat = {"id": b["id"], "title": w.grammar.expand(bdef.get("title", b["id"])),
                    "area": b["area"], "stage": b.get("stage", 0), "roles": {}, "state": "pending"}
            spawned = []
            ok = True
            for rname, rspec in (bdef.get("roles") or {}).items():
                if isinstance(rspec, str):
                    rspec = {"spawn": rspec}
                ent = None
                if "find" in rspec:
                    ent = self.find_role(rspec, beat, story_beats)
                if ent is None and "spawn" in rspec:
                    container = self.location(rspec.get("in"), beat, beat["roles"])
                    made = w.spawn_spec(rspec["spawn"], container)
                    if made:
                        ent = made[0]
                        spawned.append(ent)
                if ent is None:
                    if rspec.get("optional"):
                        continue
                    self.note("beat '%s' dropped: could not fill role '%s'" % (b["id"], rname))
                    ok = False
                    break
                if rspec.get("name"):
                    ent.name = w.grammar.expand(rspec["name"])
                    if rspec.get("proper", True):
                        ent.article = ""
                    w.refresh_aliases(ent)
                for k, v in (rspec.get("props") or {}).items():
                    ent.props[k] = w._rand_value(v)
                for t in _as_list(rspec.get("tags")):
                    if t not in ent.tags:
                        ent.tags.append(t)
                if rspec.get("hidden") is not None:
                    ent.hidden = bool(rspec["hidden"])
                beat["roles"][rname] = ent.uid
            if not ok:
                for e in spawned:
                    if e.uid in w.entities:
                        w.destroy(e)
                # Remove the gate so the area stays reachable as side content.
                self.ungate(b["id"])
                continue
            for spec in bdef.get("spawn") or []:
                container = self.location(spec.get("in") if isinstance(spec, dict) else None, beat, beat["roles"])
                w.spawn_spec({k: v for k, v in spec.items() if k != "in"} if isinstance(spec, dict) else spec,
                             container)
            story_beats.append(beat)
        title = premise.get("title") or (w.grammar.expand("#story_title#") if w.grammar.has("story_title")
                                         else w.string("untitled_story", "An Untold Tale"))
        w.story = {
            "premise": pid,
            "title": w.grammar.expand(title),
            "beats": story_beats,
            "current": 0,
            "complete": not story_beats,
            "end_on_complete": bool(premise.get("end_on_complete")),
        }

    def ungate(self, beat_id):
        for r in self.w.rooms():
            for ex in r.exits:
                cond = ex.get("if")
                if isinstance(cond, dict) and cond.get("beat_reached") == beat_id:
                    ex.pop("if", None)
                    ex.pop("blocked", None)

    def find_role(self, rspec, beat, earlier):
        w = self.w
        # Entities may fill roles in several beats (that is how a relic found in one
        # beat becomes the weapon of another) unless the role asks to be exclusive.
        bound = set(beat["roles"].values())
        if rspec.get("exclusive"):
            bound |= {u for b in earlier for u in b["roles"].values()}
        where = rspec.get("where", "reachable")
        area_rooms = set(w.areas.get(beat.get("area"), {}).get("rooms", []))
        cands = []
        for e in w.entities.values():
            if e.is_room or e.uid in bound or e.uid == w.player_uid:
                continue
            if not self.i.match(e, rspec["find"]):
                continue
            room = w.room_of(e)
            if room is None:
                continue
            if where == "area" and room.uid not in area_rooms:
                continue
            if where == "start" and room.stage != 0:
                continue
            if where in ("reachable", "before") and room.stage > beat.get("stage", 0):
                continue
            cands.append(e)
        if not cands:
            return None
        cands.sort(key=lambda e: e.uid)
        in_area = [e for e in cands if w.room_of(e).uid in area_rooms]
        return self.rng.choice(in_area or cands)

    def plant_rumours(self):
        """Put wanderers on the roads who point toward the next story beat."""
        w = self.w
        wanderers = w.defs_with_tags("wanderer")
        beats = w.story["beats"]
        chance = self.setting("rumour_chance", 0.5)
        for j, beat in enumerate(beats):
            bdef = self.reg["beats"].get(beat["id"], {})
            rumours = _as_list(bdef.get("rumor") or bdef.get("rumour"))
            if not rumours:
                continue
            stage = beat.get("stage", 0)
            pool = [w.get(u) for u in self.filler if w.get(u) and w.get(u).stage == max(0, stage - 1)]
            pool = pool or [w.get(u) for u in self.filler if w.get(u) and w.get(u).stage <= stage]
            if not pool:
                continue
            n = 1 + (1 if self.rng.random() < chance else 0)
            for room in self.rng.sample(pool, min(n, len(pool))):
                ctx = self.i.ctx(beat=j)
                text = self.i.render(self.rng.choice(rumours), ctx)
                fits = [d for d in wanderers
                        if not w.resolve_def(d).get("habitat")
                        or set(_as_list(w.resolve_def(d).get("habitat"))) & set(room.tags)]
                if fits:
                    made = w.spawn_spec(self.rng.choice(fits), room)
                    if made:
                        made[0].props["rumor"] = text
                else:
                    # No wanderer characters available: leave the rumour as a sign of the times.
                    w.spawn_spec({"name": w.string("rumour_object", "scrawled message"),
                                  "tags": ["rumour"], "description": text,
                                  "appearance": w.string("rumour_appearance",
                                                         "Someone has left a message here.")}, room)

    def finish(self, premise):
        w = self.w
        w.story["intro"] = premise.get("intro")
        w.story["ending"] = premise.get("ending")
        for k, v in (premise.get("vars") or {}).items():
            w.vars[k] = w._rand_value(v)
        for f in _as_list(premise.get("flags")):
            w.flags.add(f)
        missing = sorted(w.grammar.missing)
        if missing:
            self.note("grammar symbols with no rules: %s" % ", ".join(missing))
        self.note("world: %d rooms (%d generated), %d areas, %d features" % (
            len(w.rooms()), len(self.filler), len(w.areas),
            len([e for e in w.entities.values() if not e.is_room])))


def generate(registry, seed=None, premise=None, player_name=None, size="medium"):
    gen = Generator(registry, seed, premise, player_name, size)
    world = gen.generate()
    return world, gen.log
