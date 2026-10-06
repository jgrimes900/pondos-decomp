"""World generation: biomes, layouts (generated areas) and paths."""

import collections
import math
import unittest

from helpers import Player, registry
from patchwork.generator import Generator

FANTASY = ["core", "tales", "wilds", "hamlet", "atlas"]


def biomes_of(room, atlas, kind):
    return [b for b in room.props.get("biomes", []) if atlas.kind_of(b) == kind]


class Biomes(unittest.TestCase):
    def test_terrain_spreads_in_patches_and_blends_at_edges(self):
        blended = shared = pairs = 0
        for seed in range(1, 6):
            p = Player(FANTASY, seed)
            w, atlas = p.world, None
            gen_atlas = Generator(p.reg, seed=seed).atlas
            tiles = [r for r in w.rooms() if r.props.get("path")]
            for r in tiles:
                terr = biomes_of(r, gen_atlas, "terrain")
                if len(terr) > 1:
                    blended += 1
                for ex in r.exits:
                    d = w.get(ex["to"])
                    if d is not None and d.props.get("path"):
                        pairs += 1
                        if set(terr) & set(biomes_of(d, gen_atlas, "terrain")):
                            shared += 1
        self.assertGreater(blended, 0, "no tile sits on the edge of two terrains")
        # Neighbours along a path mostly share some terrain: patches, not noise.
        self.assertGreater(shared / float(pairs), 0.6)

    def test_sampling_blends_two_patches_of_one_kind(self):
        g = Generator(registry(FANTASY), seed=3)
        a = g.atlas
        a.seeds = {"terrain": [(0, 0, "forest"), (20, 0, "plains")]}
        self.assertEqual(a.sample(-5, 0)["terrain"], ["forest"])
        self.assertEqual(a.sample(25, 0)["terrain"], ["plains"])
        self.assertEqual(set(a.sample(10, 0)["terrain"]), {"forest", "plains"})

    def test_blended_tile_speaks_both_biomes(self):
        g = Generator(registry(FANTASY), seed=3)
        rules = g.atlas.overlay({"terrain": ["forest", "plains"]})
        self.assertTrue(set(g.reg["biomes"]["forest"]["grammar"]["landmark"]) <= set(rules["landmark"]))
        self.assertTrue(set(g.reg["biomes"]["plains"]["grammar"]["landmark"]) <= set(rules["landmark"]))


class Layouts(unittest.TestCase):
    COMBOS = {
        "inn": {"style": ["medieval"], "region": ["uk"], "quality": ["humble"]},
        "resort": {"style": ["modern"], "region": ["tropics"], "quality": ["luxurious"]},
        "block": {"style": ["soviet"], "quality": ["humble"]},
        "ruin": {"style": ["modern"], "region": ["new_mexico"], "quality": ["derelict"]},
    }

    def build(self, biomes, seed=7):
        g = Generator(registry(FANTASY), seed=seed)
        rooms, entrances = g.atlas.build_layout("hotel", biomes, 0, "demo")
        return g, rooms, entrances

    def test_one_hotel_layout_many_buildings(self):
        texts = {}
        for name, biomes in self.COMBOS.items():
            g, rooms, entrances = self.build(biomes)
            roles = collections.Counter(r.props.get("role") for r in rooms)
            for role in ("entrance", "lobby", "stairs", "corridor", "guest_room"):
                self.assertIn(role, roles, name)
            texts[name] = " ".join(r.texts.get("description", "") for r in rooms)
            # Every room is reachable from the entrance.
            seen, todo = {entrances[0].uid}, [entrances[0]]
            while todo:
                r = todo.pop()
                for ex in r.exits:
                    if ex["to"] not in seen:
                        seen.add(ex["to"])
                        todo.append(g.w.get(ex["to"]))
            self.assertTrue({r.uid for r in rooms} <= seen, name)
        self.assertIn("timbered inn", texts["inn"])
        self.assertIn("concrete", texts["block"])
        self.assertTrue("palms" in texts["resort"] or "lagoon" in texts["resort"] or "Rattan" in texts["resort"]
                        or "louvres" in texts["resort"])
        self.assertTrue("boarded-up" in texts["ruin"] or "What is left" in texts["ruin"], texts["ruin"])
        self.assertNotIn("lit sign", texts["ruin"])   # the derelict quality overrides the modern frontage

    def test_lost_woods_twist_but_reach_their_heart(self):
        twists = 0
        for seed in range(1, 5):
            g = Generator(registry(FANTASY), seed=seed)
            rooms, entrances = g.atlas.build_layout("lost_woods", {"terrain": ["forest"]}, 0, "woods")
            heart = [r for r in rooms if r.props.get("role") == "heart"]
            self.assertEqual(len(heart), 1)
            twists += len([ex for r in rooms for ex in r.exits
                           if not any(x["to"] == r.uid for x in g.w.get(ex["to"]).exits)])
            seen, todo = {entrances[0].uid}, [entrances[0]]
            while todo:
                r = todo.pop()
                for ex in r.exits:
                    if ex["to"] not in seen:
                        seen.add(ex["to"])
                        todo.append(g.w.get(ex["to"]))
            self.assertIn(heart[0].uid, seen)
        self.assertGreater(twists, 0, "the woods never turn you round")

    def test_nested_layout_falls_back_when_its_mod_is_missing(self):
        g = Generator(registry(["core", "wilds"]), seed=2)
        rooms, _ = g.atlas.build_layout("village", {"terrain": ["plains"]}, 0, "v")
        roles = {r.props.get("role") for r in rooms}
        self.assertIn("tavern", roles)
        g2 = Generator(registry(["core", "wilds", "atlas"]), seed=2)
        rooms2, _ = g2.atlas.build_layout("village", {"terrain": ["plains"], "style": ["medieval"]}, 0, "v")
        self.assertIn("lobby", {r.props.get("role") for r in rooms2})   # the full inn


class Paths(unittest.TestCase):
    def test_areas_are_joined_by_named_paths_with_long_stretches(self):
        p = Player(FANTASY, 2, start="hamlet")
        w = p.world
        waypoints = [r for r in w.rooms() if r.props.get("path")]
        self.assertTrue(waypoints)
        vias = [ex for r in waypoints for ex in r.exits if ex.get("via")]
        self.assertTrue(vias)
        self.assertGreater(max(ex["distance"] for ex in vias), 2)
        self.assertGreater(len({ex["distance"] for ex in vias}), 1)
        w.place(w.player, waypoints[0])
        self.assertIn("along", p.do("look"))

    def test_side_places_branch_off_at_forks(self):
        forks = 0
        for seed in range(1, 6):
            w = Player(FANTASY, seed, start="hamlet").world
            forks += sum(1 for r in w.rooms() if "fork" in r.tags)
        self.assertGreater(forks, 0)

    def test_generated_places_appear(self):
        kinds = collections.Counter()
        for seed in range(1, 8):
            w = Player(FANTASY, seed).world
            for aid in w.areas:
                if "~" in aid:
                    kinds[aid.split("~")[0]] += 1
        self.assertGreaterEqual(len(kinds), 3, kinds)

    def test_story_less_world_starts_in_a_settlement(self):
        for seed in range(1, 6):
            w = Player(["core", "wilds"], seed).world
            area = w.room.area
            if area and "village" in area:
                return
        self.fail("never started in a village")

    def test_without_paths_the_old_regions_still_join_areas(self):
        w = Player(["core", "hl_halflife"], 1).world
        self.assertFalse(any(r.props.get("path") for r in w.rooms()))

    def test_worlds_save_and_load_with_biomes(self):
        from patchwork.world import World
        w = Player(FANTASY, 4).world
        w2 = World.from_dict(w.to_dict())
        tiles = [r for r in w2.rooms() if r.props.get("biomes")]
        self.assertTrue(tiles)


if __name__ == "__main__":
    unittest.main()
