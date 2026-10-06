"""End-to-end: generated stories must be completable, through the text parser, on many seeds.

Every story step records a machine-checkable solution (go here, talk to them, use
this on that).  The test player follows those solutions with ordinary typed
commands, so a pass means a human could finish the same story the same way.
"""

import unittest

from helpers import Player, available
from patchwork.validate import check_world

ALL = sorted(m for m in available() if m != "lighthouse")
COMBOS = [
    ["core", "derelict"],
    ["core", "tales", "derelict"],
    ["core", "hamlet"],
    ["core", "tales", "wilds", "hamlet"],
    ["core", "tales", "wilds", "hamlet", "barrow", "spire"],
    ["core", "barrow"],
    ["core", "spire"],
    ALL,
]
SEEDS = range(1, 16)


class GeneratedStoriesAreCompletable(unittest.TestCase):
    def check(self, mods, seeds, fight=False):
        for seed in seeds:
            with self.subTest(mods=",".join(mods), seed=seed):
                p = Player(mods, seed)
                w = p.world
                self.assertEqual(check_world(w), [], p.log)
                self.assertTrue(p.solve(fight=fight), "story did not complete")
                self.assertTrue(w.story["complete"])
                self.assertIsNone(w.game_over)

    def test_mod_combinations(self):
        for mods in COMBOS:
            self.check([m for m in mods if m != "combat"], SEEDS)

    def test_with_combat(self):
        self.check(["core", "tales", "wilds", "hamlet", "barrow", "spire", "combat"], SEEDS, fight=True)
        self.check(["core", "derelict", "combat"], SEEDS, fight=True)
        self.check(ALL, range(1, 8), fight=True)

    def test_example_mod(self):
        self.check(["core", "tales", "wilds", "lighthouse"], range(1, 10))
        self.check(["core", "lighthouse"], range(1, 6))


class StoriesAreGenerated(unittest.TestCase):
    def test_no_mod_contains_a_preset_story(self):
        p = Player(ALL, 1)
        for section in ("beats", "premises"):
            self.assertFalse(p.reg.sections.get(section), section)

    def test_same_mods_different_story(self):
        """Playing Derelict on its own twice should not be the same experience."""
        plots = set()
        events = set()
        for seed in range(1, 13):
            w = Player(["core", "derelict"], seed).world
            events.add(w.story["event"])
            plots.add(tuple((st["kind"], tuple(sorted(w.get(u).def_id for u in st["refs"].values())))
                            for st in w.story["steps"]))
        self.assertGreaterEqual(len(events), 2)
        self.assertEqual(len(plots), 12, "two seeds produced the same quest chain")

    def test_characters_take_different_roles(self):
        roles = set()
        for seed in range(1, 25):
            w = Player(["core", "tales", "wilds", "hamlet", "barrow", "spire"], seed).world
            for name, uid in w.story["cast"].items():
                roles.add((name, w.get(uid).def_id if w.get(uid) else None))
        villains = {d for n, d in roles if n == "villain"}
        self.assertGreaterEqual(len(villains), 3, villains)

    def test_every_important_feature_is_in_the_main_quest(self):
        for seed in range(1, 11):
            w = Player(ALL, seed).world
            involved = {u for st in w.story["steps"] for u in st["refs"].values()}
            places = {st.get("place") for st in w.story["steps"]}
            for e in w.entities.values():
                if w.def_of(e).get("important") and not e.is_room:
                    self.assertIn(e.uid, involved, "seed %d: %s left out" % (seed, e.name))
            for aid in w.areas:
                if w.registry["areas"].get(aid, {}).get("important"):
                    self.assertIn(aid, places, "seed %d: place %s left out" % (seed, aid))

    def test_lore_mixes_mod_snippets_and_story_specific_lore(self):
        w = Player(["core", "derelict"], 2).world
        lore = w.story["lore"]
        self.assertTrue(any(k.startswith("kestrel_") for k in lore))
        self.assertTrue(any(k.startswith(w.story["event"]) for k in lore))


if __name__ == "__main__":
    unittest.main()
