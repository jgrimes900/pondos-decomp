"""Mods from different settings sharing a world: starting points, seams, and crossover stories."""

import unittest

from helpers import Player, available
from patchwork.cli import start_choices

ALL = sorted(m for m in available() if m != "lighthouse")
SETTINGS = {"fantasy", "scifi"}


def setting(p, room):
    reg = p.reg
    tags = set(room.tags)
    if room.area:
        tags |= set(reg["areas"][room.area].get("tags") or []) | set(reg["areas"][room.area].get("theme") or [])
    if room.region:
        tags |= set(reg["regions"][room.region].get("tags") or [])
    return tags & SETTINGS


class Starts(unittest.TestCase):
    def test_every_bundled_place_mod_offers_a_start(self):
        starts = dict(start_choices(Player(ALL, 1).reg))
        for aid in ("hamlet", "docking_ring", "barrow", "spire", "crossroads",
                    "hl_blackmesa", "of_blackmesa", "bs_blackmesa"):
            self.assertIn(aid, starts)

    def test_each_start_begins_there_and_is_completable(self):
        for start in ("hamlet", "docking_ring", "barrow", "spire", "crossroads"):
            for seed in (1, 2, 3):
                with self.subTest(start=start, seed=seed):
                    p = Player(ALL, seed, start=start)
                    self.assertEqual(p.world.room.area, start)
                    self.assertTrue(p.solve(fight=True), "story did not complete")
                    self.assertIsNone(p.world.game_over)

    def test_start_only_area_exists_only_when_chosen(self):
        for seed in range(1, 6):
            w = Player(["core", "tales", "wilds", "hamlet"], seed).world
            self.assertNotIn("crossroads", w.areas)
        w = Player(["core", "wilds"], 1, start="crossroads").world
        self.assertEqual(w.room.name, "Wayfarers' Camp")

    def test_openings_fit_the_start(self):
        """An event whose opening is the shuttle docking never starts you in a village, and so on."""
        for seed in range(1, 8):
            w = Player(ALL, seed, start="hamlet").world
            self.assertFalse(w.story["event"].startswith(("derelict_", "hl_cascade", "of_", "bs_")), w.story["event"])


class Seams(unittest.TestCase):
    def test_fantasy_and_scifi_never_touch_directly(self):
        for start in (None, "hamlet", "docking_ring", "hl_blackmesa"):
            for seed in range(1, 5):
                p = Player(ALL, seed, start=start)
                w = p.world
                for room in w.rooms():
                    for ex in room.exits:
                        a, b = setting(p, room), setting(p, w.get(ex["to"]))
                        self.assertFalse(a and b and not (a & b), "%s -> %s" % (room.name, w.get(ex["to"]).name))

    def test_seam_regions_join_the_settings(self):
        regions = set()
        for seed in range(1, 6):
            w = Player(ALL, seed, start="hamlet").world
            regions |= {r.region for r in w.rooms() if r.region}
        self.assertTrue(regions & {"border_rift", "strange_mile"})

    def test_creatures_keep_to_their_setting(self):
        for seed in range(1, 5):
            p = Player(ALL, seed, start="hamlet")
            w = p.world
            for e in w.entities.values():
                room = w.room_of(e) if not e.is_room else None
                if room is not None and room.area is None and "hl_creature" in e.tags:
                    self.assertNotIn("fantasy", setting(p, room), "%s in %s" % (e.name, room.name))


class Crossover(unittest.TestCase):
    def test_black_mesa_story_reaches_other_starts(self):
        events = set()
        for seed in range(1, 13):
            events.add(Player(ALL, seed, start="hamlet").world.story["event"])
        self.assertIn("hl_incursion", events)

    def test_incursion_never_opens_in_black_mesa(self):
        for seed in range(1, 10):
            for start in ("hl_blackmesa", "of_blackmesa"):
                self.assertNotEqual(Player(ALL, seed, start=start).world.story["event"], "hl_incursion")

    def test_incursion_is_completable(self):
        done = 0
        for seed in range(1, 30):
            p = Player(ALL, seed, start="hamlet")
            if p.world.story["event"] != "hl_incursion":
                continue
            self.assertTrue(p.solve(fight=True))
            done += 1
            if done == 3:
                break
        self.assertGreater(done, 0)


if __name__ == "__main__":
    unittest.main()
