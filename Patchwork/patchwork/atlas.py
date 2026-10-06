"""The world map: biomes, generated areas (layouts) and paths.

Three building blocks, all defined by mods:

* **Biomes** (section ``biomes``) are sets of tags, words and features that furnish
  a tile (a room).  Each has a *kind*: ``terrain`` (forest, plains, mesa...),
  ``style`` (medieval, modern, scifi...), ``region`` (uk, mexico, china...),
  ``quality`` (luxurious, humble...) or anything a mod invents.  A tile carries
  a combination of them, and their grammar decides what ``#floor#`` or ``#tree#``
  means there.  Kinds marked as gradients spread across the map in large patches;
  where two patches of one kind meet, tiles carry both and their text blends.

* **Layouts** (section ``layouts``) are generators of clusters of rooms: a
  hotel, a town, a lost wood, a dungeon.  An area with ``"layout"`` instead of
  ``"rooms"`` is built by one, furnished by its biomes, so a single hotel layout
  makes a tropical resort, a Soviet apartment block or a medieval inn.

* **Paths** (section ``paths``) are what the player follows from area to area: a
  road, a river, a canyon, a tram line.  A path is condensed to its notable
  places and its forks; the stretches between them are just long exits.

The generator lays areas out on a plane, samples biomes from the map wherever a
tile is made, and joins the areas with a network of paths (``Atlas.build``).
"""

import copy
import math


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


DEFAULT_KINDS = {
    "terrain": {"gradient": True, "cell": 14, "blend": 0.3},
    "style": {"gradient": True, "cell": 30, "blend": 0.2},
    "region": {"gradient": True, "cell": 40, "blend": 0.15},
}


class Atlas:
    def __init__(self, gen):
        self.gen = gen
        self.w = gen.w
        self.reg = gen.reg
        self.rng = gen.rng
        self.biomes = {k: v for k, v in self.reg["biomes"].items() if isinstance(v, dict) and not v.get("abstract")}
        kinds = dict(DEFAULT_KINDS)
        for k, v in (self.reg["settings"].get("biome_kinds") or {}).items():
            kinds[k] = dict(kinds.get(k, {}), **(v or {}))
        self.kinds = kinds
        self.seeds = {}          # kind -> [(x, y, biome id)]
        self.positions = {}      # area instance id -> (x, y)
        self.nodes = []          # path network nodes: (room uid, x, y)
        self.path_use = {}
        self.area_count = {}

    # ==================================================================
    # Biomes
    # ==================================================================
    def kind_of(self, bid):
        return self.biomes.get(bid, {}).get("kind", "terrain")

    def world_settings(self, extra=()):
        """The settings (fantasy, scifi...) present among the world's places."""
        tags = set(extra)
        for aid, adef in self.reg["areas"].items():
            if not adef.get("abstract"):
                tags |= set(_as_list(adef.get("tags")))
        return self.gen.settings_of(tags)

    def biome_fits(self, bid, settings):
        need = set(_as_list(self.biomes.get(bid, {}).get("setting")))
        return not need or not settings or bool(need & settings)

    def pins_for(self, tags):
        """Biomes an area's tags call for (a biome's pin_tags): Black Mesa pins mesa, modern, New Mexico."""
        out = []
        for bid, b in sorted(self.biomes.items()):
            if set(_as_list(b.get("pin_tags"))) & set(tags):
                out.append(bid)
        return out

    def plan_map(self, extent, pins):
        """Scatter gradient seeds over the map; *pins* are (x, y, biome) an area insists on."""
        (x0, y0), (x1, y1) = extent
        settings = self.world_settings()
        for kind, kd in sorted(self.kinds.items()):
            if not kd.get("gradient"):
                continue
            cands = [b for b, d in sorted(self.biomes.items())
                     if self.kind_of(b) == kind and d.get("gradient", 1) and self.biome_fits(b, settings)]
            pinned = [(x, y, b) for x, y, b in pins if self.kind_of(b) == kind]
            if not cands and not pinned:
                continue
            cell = float(kd.get("cell", 14)) * max(0.6, self.gen.size ** 0.5)
            area = max(1.0, (x1 - x0 + 2 * cell) * (y1 - y0 + 2 * cell))
            n = max(int(kd.get("min_patches", 4)), int(round(area / (cell * cell))))
            seeds = list(pinned)
            for _ in range(n if cands else 0):
                b = _weighted(self.rng, cands, lambda c: self.biomes[c].get("gradient", 1) if not isinstance(
                    self.biomes[c].get("gradient"), bool) else 1)
                seeds.append((self.rng.uniform(x0 - cell, x1 + cell), self.rng.uniform(y0 - cell, y1 + cell), b))
            self.seeds[kind] = seeds

    def sample(self, x, y):
        """Biomes at a point: for each gradient kind the nearest patch, plus any close enough to blend."""
        out = {}
        for kind, seeds in self.seeds.items():
            if not seeds:
                continue
            kd = self.kinds.get(kind, {})
            cell = float(kd.get("cell", 14)) * max(0.6, self.gen.size ** 0.5)
            blend = float(kd.get("blend", 0.25)) * cell
            dists = sorted(((math.hypot(sx - x, sy - y), b) for sx, sy, b in seeds), key=lambda t: t[0])
            found = []
            for d, b in dists:
                if d - dists[0][0] > blend or len(found) >= 3:
                    break
                if b not in found:
                    found.append(b)
            out[kind] = found
        return out

    def combine(self, *layers):
        """Merge biome choices: a later layer replaces earlier ones kind by kind."""
        out = {}
        for layer in layers:
            for kind, ids in (layer or {}).items():
                ids = [b for b in _as_list(ids) if b in self.biomes]
                if ids:
                    out[kind] = ids
        return out

    def by_kind(self, ids):
        out = {}
        for b in _as_list(ids):
            if b in self.biomes:
                out.setdefault(self.kind_of(b), []).append(b)
        return out

    def choose(self, spec, settings=None):
        """An area's biome spec -> {kind: [ids]}. Values may be an id, a list to pick one from,
        or {"any": [...], "blend": true} to keep all."""
        out = {}
        for kind, val in (spec or {}).items():
            if isinstance(val, dict):
                opts = [b for b in _as_list(val.get("any")) if b in self.biomes]
                if val.get("blend"):
                    out[kind] = opts
                elif opts:
                    out[kind] = [self.rng.choice(opts)]
                continue
            opts = [b for b in _as_list(val) if b in self.biomes and self.biome_fits(b, settings or set())] \
                or [b for b in _as_list(val) if b in self.biomes]
            if opts:
                out[kind] = [self.rng.choice(opts)]
        return out

    def keep_setting(self, biomes, settings):
        """Drop biomes that clash with a setting (a medieval patch beside a space station); if a kind is
        left empty, borrow a fitting biome of that kind so the tile still has one."""
        if not settings:
            return biomes
        out = {}
        for kind, ids in biomes.items():
            ok = [b for b in ids if self.biome_fits(b, settings)]
            if not ok:
                cands = [b for b, d in sorted(self.biomes.items()) if self.kind_of(b) == kind
                         and set(_as_list(d.get("setting"))) & settings and d.get("gradient", 1)]
                ok = [self.rng.choice(cands)] if cands else []
            if ok:
                out[kind] = ok
        return out

    def flat(self, biomes):
        return [b for ids in biomes.values() for b in ids]

    def overlay(self, biomes):
        """The grammar a tile speaks: every biome's words, blended. A kind's "grammar_weight" makes its
        words more likely (a quality says more about a hotel than its region does); a symbol written
        "!name" replaces what other biomes say (a derelict hotel's front has no lit sign)."""
        rules, overrides = {}, {}
        for b in self.flat(biomes):
            weight = int(self.kinds.get(self.kind_of(b), {}).get("grammar_weight", 1))
            for sym, opts in (self.biomes[b].get("grammar") or {}).items():
                if sym.startswith("!"):
                    overrides.setdefault(sym[1:], []).extend(_as_list(opts))
                else:
                    rules.setdefault(sym, []).extend(_as_list(opts) * max(1, weight))
        rules.update(overrides)
        return rules

    def biome_tags(self, biomes):
        tags = []
        for b in self.flat(biomes):
            for t in [b] + _as_list(self.biomes[b].get("tags")):
                if t not in tags:
                    tags.append(t)
        return tags

    def fits(self, template, biomes):
        """Does a room template's "requires" ({kind: [ids or tags]}) match the tile?"""
        req = template.get("requires") if isinstance(template, dict) else None
        if not req:
            return True
        tags = set(self.biome_tags(biomes))
        for kind, want in req.items():
            want = set(_as_list(want))
            have = set(biomes.get(kind, [])) if kind != "tags" else tags
            if kind != "tags":
                have |= {t for b in biomes.get(kind, []) for t in _as_list(self.biomes[b].get("tags"))}
            if not (want & have):
                return False
        return True

    # ==================================================================
    # Furnishing: making a room on a tile
    # ==================================================================
    def make_room(self, template, biomes, role=None, pos=None, uid_prefix="f", indoor=False):
        """Instantiate a room template on a tile with these biomes, furnished by them.
        Whether the tile is outdoors comes from the template's tags (else *indoor*), never from its
        biomes: a hotel parlour in a forest is still indoors."""
        w = self.w
        with w.grammar.scoped(self.overlay(biomes)):
            if isinstance(template, str):
                key = "room:" + template
            else:
                spec = copy.deepcopy(template)
                spec["room"] = True
                for k in ("weight", "requires", "role"):
                    spec.pop(k, None)
                key = w.register_inline_def(spec)
            ent = w.instantiate(key, uid=w.new_uid(uid_prefix))
            ent.is_room = True
            if "indoor" not in ent.tags and "outdoor" not in ent.tags:
                ent.tags.append("indoor" if indoor else "outdoor")
            for t in self.biome_tags(biomes):
                if t not in ent.tags and t not in ("indoor", "outdoor"):
                    ent.tags.append(t)
            ent.props["biomes"] = self.flat(biomes)
            if role:
                ent.props["role"] = role
            if pos is not None:
                ent.props["pos"] = [round(pos[0], 1), round(pos[1], 1)]
            self.dedupe_name(ent)
            self.furnish(ent, biomes, role)
            desc = ent.texts.get("description")
            if isinstance(desc, str):
                ent.texts["description"] = " ".join(desc.split())   # biomes with nothing to say leave gaps
            w.refresh_aliases(ent)
        return ent

    def dedupe_name(self, ent):
        w = self.w
        names = {r.name for r in w.rooms() if r.uid != ent.uid}
        d = w.def_of(ent)
        tries = 0
        while ent.name in names and tries < 6 and "#" in (d.get("name") or ""):
            ent.name = w.grammar.expand(d["name"])
            tries += 1
        if ent.name in names:
            # Two rooms with one name can't be told apart by "go to": number the later ones.
            base, n = ent.name, 2
            while ent.name in names:
                ent.name = "%s %s" % (base, ["II", "III", "IV", "V", "VI", "VII", "VIII"][min(n - 2, 6)] if n < 9 else n)
                n += 1

    def furnish(self, ent, biomes, role):
        """Each biome adds its features (and those for this role); a blended tile shares the space."""
        w = self.w
        outdoor = "outdoor" in ent.tags
        for kind, ids in biomes.items():
            share = 1.0 / max(1, len(ids)) ** 0.5
            for b in ids:
                bd = self.biomes[b]
                # A biome's own features are the land's (trees, boulders): outdoors only.
                specs = list(_as_list(bd.get("features"))) if outdoor else []
                furnish = bd.get("furnish") or {}
                if role and role in furnish:
                    specs += _as_list(furnish[role])
                specs += _as_list(furnish.get("outdoor" if outdoor else "indoor"))
                for spec in specs:
                    if self.rng.random() <= share:
                        w.spawn_spec(spec, ent)
                details = _as_list(bd.get("details"))
                if details and outdoor and self.rng.random() < 0.6 * share:
                    line = w.grammar.expand(self.rng.choice(details))
                    desc = ent.texts.get("description")
                    if isinstance(desc, str):
                        ent.texts["description"] = (desc + " " + line).strip()

    # ==================================================================
    # Layouts: generated areas
    # ==================================================================
    def layout_def(self, ref):
        if isinstance(ref, dict):
            return ref
        return self.reg["layouts"].get(ref) or {}

    def pick_template(self, layout, role, biomes):
        tpls = [t for t in _as_list((layout.get("rooms") or {}).get(role)) if self.fits(t, biomes)] \
            or _as_list((layout.get("rooms") or {}).get(role))
        if not tpls:
            return {"name": role.replace("_", " ").title(), "description": "#%s_desc#" % role}
        use = self.path_use.setdefault(("tpl", id(layout), role), {})

        def weight(i):
            t = tpls[i]
            base = t.get("weight", 1) if isinstance(t, dict) else 1
            return base / (1 + use.get(i, 0) * 1.5)
        i = _weighted(self.rng, list(range(len(tpls))), weight)
        use[i] = use.get(i, 0) + 1
        return tpls[i]

    def build_layout(self, layout, biomes, stage, area_id, pos=None, depth=0):
        """Generate a layout's rooms on a tile. Returns (rooms, entrances)."""
        layout = self.layout_def(layout)
        biomes = self.combine(biomes, self.choose(layout.get("biomes")) if layout.get("biomes") else None) \
            if layout.get("biomes") and not depth else biomes
        kind = layout.get("type", "plan")
        if kind == "grid":
            rooms, entrances = self._build_grid(layout, biomes, stage, area_id, pos)
        else:
            rooms, entrances = self._build_plan(layout, biomes, stage, area_id, pos, depth)
        for r in rooms:
            for t in _as_list(layout.get("tags")):
                if t not in r.tags:
                    r.tags.append(t)
        return rooms, entrances

    def _new(self, layout, role, biomes, stage, area_id, pos):
        tpl = self.pick_template(layout, role, biomes)
        ent = self.make_room(tpl, biomes, role=role, pos=pos, uid_prefix="g", indoor=bool(layout.get("indoor")))
        ent.area = area_id
        ent.stage = stage
        return ent

    def _build_plan(self, layout, biomes, stage, area_id, pos, depth):
        g = self.gen
        rooms, by_role, entrances = [], {}, []
        steps = _as_list(layout.get("plan")) or [{"role": r} for r in (layout.get("rooms") or {})]
        for idx, step in enumerate(steps):
            if self.rng.random() > float(step.get("chance", 1)):
                continue
            anchors = [r for r in by_role.get(step.get("from"), [])] if step.get("from") else []
            if step.get("from") and not anchors:
                continue
            per = anchors if step.get("per") else [None]
            for anchor_for in per:
                n = g.rng_range(step.get("count"), 1)
                prev = None
                for _ in range(n):
                    sub = None
                    if step.get("layout") and depth < 3 and self.layout_def(step["layout"]):
                        # A building inside a town, a cellar under an inn: another layout, its own biome tweaks.
                        sub_biomes = self.combine(biomes, self.choose(step.get("biomes")))
                        sub, sub_in = self.build_layout(step["layout"], sub_biomes, stage, area_id, pos, depth + 1)
                    if sub:
                        new_rooms, link_to = sub, (sub_in[0] if sub_in else sub[0])
                    elif step.get("layout") and not step.get("role"):
                        continue   # the layout's mod isn't loaded and there's nothing to stand in for it
                    else:
                        tpl_biomes = self.combine(biomes, self.choose(step.get("biomes"))) if step.get("biomes") else biomes
                        link_to = self._new(layout, step.get("role", "room"), tpl_biomes, stage, area_id, pos)
                        new_rooms = [link_to]
                    anchor = anchor_for or (prev if step.get("chain") and prev is not None else
                                            (self.rng.choice(anchors) if anchors else None))
                    if anchor is not None:
                        extra = {k: step[k] for k in ("name", "aliases", "description") if k in step}
                        g.link(anchor, link_to, g.rng_range(step.get("distance"), 1), prefer=step.get("dir"),
                               out_extra=extra or None)
                    rooms.extend(new_rooms)
                    role = step.get("role", "room")
                    by_role.setdefault(role, []).append(link_to)
                    if step.get("entrance") or (idx == 0 and not any(s.get("entrance") for s in steps)):
                        entrances.append(link_to)
                    prev = link_to
        # A few extra connections make a building or town less tree-like.
        loops = g.rng_range(layout.get("loops"), 0)
        for _ in range(loops):
            cands = [r for r in rooms if g.free_dirs(r)]
            if len(cands) < 2:
                break
            a, b = self.rng.sample(cands, 2)
            if not any(x["to"] == b.uid for x in a.exits):
                g.link(a, b, 1)
        return rooms, entrances or rooms[:1]

    def _build_grid(self, layout, biomes, stage, area_id, pos):
        """A grid of cells joined as a maze: woods, caves, catacombs.
        "lost": a share of extra one-way exits that lead somewhere other than where they point."""
        g = self.gen
        width = g.rng_range(layout.get("width") or layout.get("size"), 3)
        height = g.rng_range(layout.get("height") or layout.get("size"), 3)
        role = layout.get("role", "cell")
        cells = {}
        for x in range(width):
            for y in range(height):
                cells[(x, y)] = self._new(layout, role, biomes, stage, area_id, pos)
        steps = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}
        seen, stack = {(0, 0)}, [(0, 0)]
        while stack:
            cx, cy = stack[-1]
            opts = [((cx + dx, cy + dy), d) for (dx, dy), d in steps.items()
                    if (cx + dx, cy + dy) in cells and (cx + dx, cy + dy) not in seen]
            if not opts:
                stack.pop()
                continue
            nxt, d = self.rng.choice(opts)
            g.link(cells[(cx, cy)], cells[nxt], 1, prefer=d)
            seen.add(nxt)
            stack.append(nxt)
        for _ in range(g.rng_range(layout.get("loops"), max(1, (width * height) // 5))):
            (cx, cy) = self.rng.choice(list(cells))
            (dx, dy), d = self.rng.choice(list(steps.items()))
            other = cells.get((cx + dx, cy + dy))
            if other and not any(x["to"] == other.uid for x in cells[(cx, cy)].exits):
                g.link(cells[(cx, cy)], other, 1, prefer=d)
        lost = float(layout.get("lost", 0))
        if lost:
            for cell in list(cells.values()):
                if self.rng.random() < lost and g.free_dirs(cell):
                    dest = self.rng.choice(list(cells.values()))
                    if dest is not cell:
                        g.link(cell, dest, 1, oneway=True)
                        cell.props["lost"] = True
        edge = [c for (x, y), c in cells.items() if x in (0, width - 1) or y in (0, height - 1)]
        if layout.get("goal"):
            far = cells[(width - 1, height - 1)]
            goal = self._new(layout, layout["goal"], biomes, stage, area_id, pos)
            g.link(far, goal, 1)
            return list(cells.values()) + [goal], [cells[(0, 0)]]
        return list(cells.values()), [cells[(0, 0)]] + [c for c in edge if c is not cells[(0, 0)]][:2]

    # ==================================================================
    # Paths
    # ==================================================================
    def paths(self):
        return {k: v for k, v in self.reg["paths"].items() if isinstance(v, dict) and not v.get("abstract")}

    def path_fits(self, pid, ta, tb, biomes):
        p = self.reg["paths"][pid]
        tags = set(_as_list(p.get("tags")))
        if self.gen.clash(tags, ta) or self.gen.clash(tags, tb):
            return 0
        for kind, want in (p.get("biomes") or {}).items():
            if want != "*" and not (set(_as_list(want)) & set(biomes.get(kind, []))):
                return 0
        score = 1 + len((tags | set(_as_list(p.get("connects")))) & (ta | tb))
        return score * score * float(p.get("weight", 1)) / (1 + 0.5 * self.path_use.get(pid, 0))

    def choose_path(self, ta, tb, biomes):
        cands = sorted(self.paths())
        scored = [(p, self.path_fits(p, ta, tb, biomes)) for p in cands]
        ok = [p for p, s in scored if s > 0]
        if not ok:
            return None
        pid = _weighted(self.rng, ok, lambda p: dict(scored)[p])
        self.path_use[pid] = self.path_use.get(pid, 0) + 1
        return pid

    def waypoint(self, pid, role, biomes, stage, pos):
        p = self.reg["paths"][pid]
        pool = _as_list(p.get(role)) if role in ("fork", "end") else []
        pool = [t for t in pool if self.fits(t, biomes)] or pool
        if not pool:
            pool = [t for t in _as_list(p.get("waypoints")) if self.fits(t, biomes)] or _as_list(p.get("waypoints"))
        if not pool:
            pool = [{"name": "#%s_name#" % pid, "description": "#%s_desc#" % pid}]
        use = self.path_use.setdefault(("wp", pid), {})
        def wt(k):
            t = pool[k]
            base = t.get("weight", 1) if isinstance(t, dict) else 1
            if use.get(k) and "#" not in ((t.get("name") if isinstance(t, dict) else "") or ""):
                return base * 0.05   # a place with a fixed name should rarely appear twice
            return base / (1 + use.get(k, 0) * 2)
        i = _weighted(self.rng, list(range(len(pool))), wt)
        use[i] = use.get(i, 0) + 1
        ent = self.make_room(pool[i], biomes, role=role, pos=pos)
        ent.stage = stage
        ent.region = None
        ent.props["path"] = pid
        for t in _as_list(p.get("tags")):
            if t not in ent.tags:
                ent.tags.append(t)
        for spec in _as_list(p.get("features")):
            self.w.spawn_spec(spec, ent)
        self.gen.filler.append(ent.uid)
        return ent

    def lay_path(self, a, b, pa, pb, stage, ta=None, tb=None):
        """Join room a (at pa) to room b (at pb) along a path: its notable places, with stretches between."""
        g = self.gen
        ta = ta if ta is not None else g.themes(a)
        tb = tb if tb is not None else g.themes(b)
        mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
        pid = self.choose_path(ta, tb, self.sample(*mid))
        if pid is None:
            g.link(a, b, max(1, int(round(math.hypot(pb[0] - pa[0], pb[1] - pa[1]) / 3))))
            return [a, b], None
        p = self.reg["paths"][pid]
        name = self.w.grammar.expand(p.get("name") or pid.replace("_", " "))
        if name.startswith("The "):
            name = "the " + name[4:]   # it's read mid-sentence: "north along the Old Fox Way"
        dist = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
        spacing = float(p.get("spacing", 9))
        k = max(1, min(int(p.get("max_waypoints", 6)), int(round(dist / spacing))))
        chain, points = [a], [pa]
        # Two settings that clash meet in a seam (portal storms, a misty strange mile).
        seam_at = k // 2 if g.clash(ta, tb) and g.choose_seam(ta, tb) else None
        for j in range(1, k + 1):
            t = j / float(k + 1)
            jitter = spacing * 0.35
            pos = (pa[0] + (pb[0] - pa[0]) * t + self.rng.uniform(-jitter, jitter),
                   pa[1] + (pb[1] - pa[1]) * t + self.rng.uniform(-jitter, jitter))
            if seam_at is not None and j - 1 == seam_at:
                seam = g.make_filler(g.choose_seam(ta, tb), stage)
                seam.props["pos"] = [round(pos[0], 1), round(pos[1], 1)]
                chain.append(seam)
            else:
                # Each half of a path keeps to the setting of the end it's nearer: the change happens midway.
                near = ta if (seam_at is None and t < 0.5) or (seam_at is not None and j - 1 < seam_at) else tb
                biomes = self.keep_setting(self.sample(*pos), g.settings_of(near))
                chain.append(self.waypoint(pid, "landmark", biomes, stage, pos))
            points.append(pos)
        chain.append(b)
        points.append(pb)
        stretch = p.get("stretch")
        heading = None
        for (x, y), (px, py) in zip(zip(chain, chain[1:]), zip(points, points[1:])):
            span = math.hypot(py[0] - px[0], py[1] - px[1])
            legd = max(1, int(round(span / float(p.get("scale", 2.5)) * self.rng.uniform(0.7, 1.3))))
            if stretch:
                lo, hi = _as_list(stretch)[0], _as_list(stretch)[-1]
                legd = max(int(lo), min(int(hi), legd))
            extra = {"via": name}
            heading = g.link(x, y, legd, prefer=heading, out_extra=extra, back_extra=dict(extra))
        for r in chain[1:-1]:
            r.props.setdefault("path_name", name)
        if b.area:
            # The way into an area along its path: where the story can put a gate.
            way_in = next((x for x in chain[-2].exits if x["to"] == b.uid), None)
            if way_in is not None:
                g.entries.setdefault(b.area, (chain[-2].uid, way_in))
        for r, pos in zip(chain, points):
            self.nodes.append((r.uid, pos[0], pos[1]))
        return chain, pid

    def make_fork(self, room, branch_name, toward):
        """A notable place where another path branches off."""
        if "fork" not in room.tags:
            room.tags.append("fork")
        pid = room.props.get("path")
        p = self.reg["paths"].get(pid or "", {})
        text = self.w.grammar.expand(p.get("fork_text") or self.w.string(
            "fork_text", "The way forks here: {branch} leads off toward {toward}."))
        line = text.replace("{branch}", branch_name).replace("{toward}", toward)
        desc = room.texts.get("description")
        if isinstance(desc, str) and line not in desc:
            room.texts["description"] = (desc + " " + line).strip()

    # ==================================================================
    # The whole map
    # ==================================================================
    def build(self, spine, start_area):
        """Place areas on a plane, sample biomes, build them and join them with paths."""
        g, w = self.gen, self.w
        size = g.size
        # -- where everything goes ------------------------------------------------
        leg = [float(x) for x in _as_list(g.setting("area_spacing", [16, 26]))]
        heading = self.rng.uniform(0, 2 * math.pi)
        x = y = 0.0
        for idx, aid in enumerate(spine):
            if idx:
                heading += self.rng.uniform(-0.8, 0.8)
                d = self.rng.uniform(leg[0], leg[-1]) * size ** 0.5
                x, y = x + math.cos(heading) * d, y + math.sin(heading) * d
            self.positions[aid] = (x, y)
        side = g.side_area_ids(spine)
        generated = self.generated_area_plan(spine, side)
        anchor_pts = list(self.positions.values()) or [(0.0, 0.0)]
        for aid in side + generated:
            ax, ay = self.rng.choice(anchor_pts)
            ang = self.rng.uniform(0, 2 * math.pi)
            d = self.rng.uniform(leg[0] * 0.6, leg[-1]) * size ** 0.5
            self.positions[aid] = (ax + math.cos(ang) * d, ay + math.sin(ang) * d)
            anchor_pts.append(self.positions[aid])
        if not self.positions:
            self.positions["~wilds"] = (0.0, 0.0)
        xs = [p[0] for p in self.positions.values()]
        ys = [p[1] for p in self.positions.values()]
        pins = []
        for aid, (px, py) in self.positions.items():
            adef = g.area_def(aid)
            for b in self.flat(self.area_biome_spec(aid, adef)) + self.pins_for(_as_list(adef.get("tags"))):
                pins.append((px, py, b))
        self.plan_map(((min(xs), min(ys)), (max(xs), max(ys))), pins)

        # -- the spine -------------------------------------------------------------
        prev, prev_pos = None, None
        for idx, aid in enumerate(spine):
            g.build_area(aid, idx)
            entrance = g.pick_entrance(aid)
            pos = self.positions[aid]
            if prev is not None:
                self.lay_path(prev, entrance, prev_pos, pos, max(0, idx - 1))
            else:
                self.nodes.append((entrance.uid, pos[0], pos[1]))
            prev, prev_pos = g.pick_entrance(aid), pos
            self.nodes.append((prev.uid, pos[0], pos[1]))
        if not spine and start_area is None:
            # No story places: the world is made of generated places and the paths between them.
            pass
        # -- side and generated areas branch off the network at forks --------------
        max_stage = max(0, len(spine) - 1)
        for aid in side + generated:
            pos = self.positions[aid]
            stage = min(max_stage, g.area_def(aid).get("stage", max_stage) if isinstance(
                g.area_def(aid).get("stage"), int) else max_stage)
            if not self.nodes:
                info = g.build_area(aid, 0)
                entrance = g.pick_entrance(aid)
                self.nodes.append((entrance.uid, pos[0], pos[1]))
                g.sandbox_start = getattr(g, "sandbox_start", None) or entrance
                continue
            near = self.nearest_node(pos, max_stage=stage)
            anchor = w.get(near[0])
            stage = min(stage, anchor.stage)
            info = g.build_area(aid, stage)
            info["side"] = True
            entrance = g.pick_entrance(aid)
            chain, pid = self.lay_path(anchor, entrance, (near[1], near[2]), pos, stage)
            if anchor.props.get("path") and pid:
                self.make_fork(anchor, chain[1].props.get("path_name") or "a path", info["name"])
            self.nodes.append((entrance.uid, pos[0], pos[1]))
        # -- shortcuts between parts of the network that are close on the map -----
        loops = int(round(g.rng_range(g.setting("path_loops", [1, 2]), 1) * size))
        for _ in range(loops * 4):
            if loops <= 0 or len(self.nodes) < 4:
                break
            a = self.rng.choice(self.nodes)
            ra = w.get(a[0])
            close = [n for n in self.nodes if n[0] != a[0] and w.get(n[0]).stage == ra.stage
                     and 6 < math.hypot(n[1] - a[1], n[2] - a[2]) < 22 * size ** 0.5
                     and not any(x["to"] == n[0] for x in ra.exits)
                     and g.free_dirs(w.get(n[0])) and g.free_dirs(ra)]
            if not close:
                continue
            b = self.rng.choice(close)
            chain, pid = self.lay_path(ra, w.get(b[0]), (a[1], a[2]), (b[1], b[2]), ra.stage)
            for end in (ra, w.get(b[0])):
                if end.props.get("path") and pid and len(chain) > 2:
                    self.make_fork(end, chain[1].props.get("path_name") or "a path",
                                   chain[-1].name if end is ra else chain[0].name)
            loops -= 1
        if not spine:
            # No story places: set out from a settlement if the world made one.
            towns = [a for a in generated if "settlement" in _as_list(g.area_def(a).get("tags")) and a in w.areas]
            if towns:
                g.sandbox_start = w.get(w.areas[towns[0]]["entrances"][0])
            elif not getattr(g, "sandbox_start", None) and self.nodes:
                g.sandbox_start = w.get(self.nodes[0][0])

    def nearest_node(self, pos, max_stage=None):
        w = self.w
        pool = [n for n in self.nodes if w.get(n[0]) is not None and g_free(self.gen, w.get(n[0]))
                and (max_stage is None or w.get(n[0]).stage <= max_stage)] or \
            [n for n in self.nodes if w.get(n[0]) is not None]
        return min(pool, key=lambda n: math.hypot(n[1] - pos[0], n[2] - pos[1]))

    def area_biome_spec(self, aid, adef):
        return self.choose(adef.get("biomes"), self.world_settings())

    def area_biomes(self, aid):
        """An area's biomes: what it asks for, what its tags pin, and the map where it stands."""
        adef = self.gen.area_def(aid)
        pos = self.positions.get(aid)
        sampled = self.sample(*pos) if pos else {}
        if adef.get("indoor") or adef.get("layout") and self.layout_def(adef["layout"]).get("indoor"):
            sampled = {k: v[:1] for k, v in sampled.items()}   # a building is one place, not a blend
        pinned = self.by_kind(self.pins_for(_as_list(adef.get("tags"))))
        cached = getattr(self, "_area_spec", {})
        if aid not in cached:
            cached[aid] = self.area_biome_spec(aid, adef)
            self._area_spec = cached
        return self.combine(sampled, pinned, cached[aid])

    def generated_area_plan(self, spine, side):
        """Generated places (villages, lost woods, roadside inns) the world sprinkles in: area
        templates with "copies"."""
        g = self.gen
        out = []
        budget = int(round(g.rng_range(g.setting("generated_areas", [2, 4]), 2) * g.size))
        templates = [a for a, d in sorted(self.reg["areas"].items())
                     if not d.get("abstract") and d.get("layout") and d.get("copies")]
        settings = self.world_settings()
        templates = [a for a in templates
                     if not settings or not g.settings_of(_as_list(self.reg["areas"][a].get("tags")))
                     or g.settings_of(_as_list(self.reg["areas"][a].get("tags"))) & settings]
        for _ in range(budget):
            if not templates:
                break
            tpl = _weighted(self.rng, templates, lambda a: self.reg["areas"][a].get("weight", 1))
            limit = _as_list(self.reg["areas"][tpl].get("copies"))[-1]
            n = self.area_count.get(tpl, 0)
            if n >= int(limit):
                templates.remove(tpl)
                continue
            self.area_count[tpl] = n + 1
            out.append("%s~%d" % (tpl, n + 1))
        return out


def g_free(gen, room):
    return bool(gen.free_dirs(room))
