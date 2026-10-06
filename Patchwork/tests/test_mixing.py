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
        adef = reg["areas"].get(room.area) or reg["areas"][room.area.split("~")[0]]
        tags |= set(adef.get("tags") or []) | set(adef.get("theme") or [])
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


class StatScaling(unittest.TestCase):
    """Stats are written for a player of some base max health (default_max_health) and converted to the
    world's player, so mixing a 20-health fantasy mod with 100-health Half-Life keeps both fair."""

    def spawn(self, w, fid):
        return w.spawn_spec({"id": fid}, w.room)[0]

    def test_fantasy_creatures_scale_up_beside_half_life(self):
        plain = Player(["core", "combat", "wilds"], 1).world
        mixed = Player(["core", "wilds", "hl_core"], 1).world
        self.assertEqual(plain.player.props["max_health"], 20)
        self.assertEqual(mixed.player.props["max_health"], 100)
        for fid in ("grey_wolf", "bandit", "bog_lurker", "rusty_sword", "healing_salve", "leather_jerkin"):
            a, b = self.spawn(plain, fid), self.spawn(mixed, fid)
            for k in ("health", "max_health", "damage", "armor", "heal"):
                if a.props.get(k):
                    self.assertEqual(b.props[k], a.props[k] * 5, "%s %s" % (fid, k))
            # The same share of the player's health either way.
            if a.props.get("damage") and "creature" in a.tags:
                self.assertAlmostEqual(a.props["damage"] / plain.player.props["max_health"],
                                       b.props["damage"] / mixed.player.props["max_health"])

    def test_half_life_stats_stay_put(self):
        w = Player(["core", "wilds", "hl_core"], 1).world
        self.assertEqual(self.spawn(w, "headcrab").props["damage"], 6)
        self.assertEqual(self.spawn(w, "crowbar").props["damage"], 10)
        self.assertEqual(self.spawn(w, "medkit").props["heal"], 15)

    def test_scaled_expression(self):
        p = Player(["core", "wilds", "hl_core"], 1)
        w = p.world
        i = p.engine.i
        self.assertEqual(i.value("=scaled(1)", i.ctx()), 5)
        self.assertEqual(i.value("=scaled(12, 100)", i.ctx()), 12)
        w2 = Player(["core", "combat", "wilds"], 1).world
        self.assertEqual(w2.player.props["default_max_health"], 20)

    def test_wolf_fight_is_a_fight_in_black_mesa_worlds(self):
        p = Player(["core", "wilds", "hl_core"], 2)
        w = p.world
        wolf = self.spawn(w, "grey_wolf")
        start = w.player.props["health"]
        for _ in range(3):
            p.do("attack grey wolf")
        self.assertIn(wolf.uid, w.entities, "an unarmed player should not flatten a wolf in three blows")
        self.assertLess(w.player.props["health"], start)

    def test_validator_notes_undeclared_stats(self):
        from patchwork.validate import check_registry
        reg = Player(["core", "combat", "wilds"], 1).reg
        reg["features"]["test_beast"] = {"extends": ["thing"], "props": {"health": 9}}
        notes = [n for n in check_registry(reg) if "test_beast" in n]
        self.assertTrue(notes and "default_max_health" in notes[0], notes)


if __name__ == "__main__":
    unittest.main()
