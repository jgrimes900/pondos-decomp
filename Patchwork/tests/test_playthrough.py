"""End-to-end playthroughs: every bundled story must be completable on many seeds."""

import unittest

from helpers import Player

FANTASY = ["core", "wilds", "hamlet", "barrow", "spire", "saga_waning_light"]
SCIFI = ["core", "derelict"]
SEEDS = range(1, 13)


def relic_word(p):
    beat = next(b for b in p.world.story["beats"] if b["id"] == "barrow_relic")
    return p.world.get(beat["roles"]["relic"]).name


class FantasyPlaythrough(unittest.TestCase):
    def play(self, mods, seed, fight=False):
        p = Player(mods, seed, premise="waning_light")
        w = p.world
        ids = [b["id"] for b in w.story["beats"]]
        self.assertEqual(ids, ["hamlet_call", "barrow_relic", "spire_confrontation"], p.log)

        # Opening: speak with the elder.
        p.walk_to(p.room_by_def("hamlet/cottage"), fight)
        p.do("talk to elder")
        self.assertEqual(w.story["beats"][0]["state"], "done")

        # Middle: get into the barrow sanctum.
        p.walk_to(p.room_by_def("barrow/ossuary"), fight)
        p.do("search bones")
        out = p.do("take key")
        self.assertIn("key", out)
        p.walk_to(p.room_by_def("barrow/antechamber"), fight)
        p.do("unlock door")
        p.do("open door")
        p.walk_to(p.room_by_def("barrow/sanctum"), fight)
        p.do("open sarcophagus")
        relic = relic_word(p)
        p.do("take " + relic)
        self.assertEqual(w.story["beats"][1]["state"], "done", "relic not taken: " + relic)

        # Climax: the spire, gated until now, then the ward that needs the relic.
        top = p.room_by_def("spire/top")
        self.assertTrue(p.walk_to(top, fight), "could not reach the top of the spire")
        villain = w.get(w.story["beats"][2]["roles"]["villain"])
        if villain is not None:
            p.do("use %s on %s" % (relic, villain.name))
        # (With combat loaded the sorcerer may already have fallen in the fight.)
        self.assertTrue(w.story["complete"], "story not complete")
        self.assertIsNone(w.game_over)

    def test_story_without_combat(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                self.play(FANTASY, seed)

    def test_story_with_combat(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                self.play(FANTASY + ["combat"], seed, fight=True)

    def test_spire_fallback_relic_without_barrow(self):
        """With no barrow mod the spire hides its own relic so the story stays winnable."""
        for seed in range(1, 6):
            with self.subTest(seed=seed):
                p = Player(["core", "wilds", "hamlet", "spire", "saga_waning_light"], seed)
                w = p.world
                beat = w.story["beats"][-1]
                self.assertEqual(beat["id"], "spire_confrontation")
                bane = w.get(beat["roles"]["bane"])
                self.assertEqual(bane.def_id, "spire_bane")
                p.do("talk to innkeeper", answers=["4"])
                p.walk_to(p.room_by_def("hamlet/cottage"))
                p.do("talk to elder")
                p.walk_to(p.world.room_of(bane))
                p.do("take shard")
                p.walk_to(p.room_by_def("spire/top"))
                p.do("use shard on " + w.get(beat["roles"]["villain"]).name)
                self.assertTrue(w.story["complete"])


class ExampleModPlaythrough(unittest.TestCase):
    def test_lighthouse_slots_into_the_saga(self):
        for seed in range(1, 8):
            with self.subTest(seed=seed):
                p = Player(FANTASY + ["lighthouse"], seed, premise="waning_light")
                ids = [b["id"] for b in p.world.story["beats"]]
                self.assertIn("lighthouse_relight", ids)
                self.assertEqual(ids[-1], "spire_confrontation")
                # Skip ahead: complete the chapters before the lighthouse.
                for bid in ids[:ids.index("lighthouse_relight")]:
                    p.engine.complete_beat(bid)
                self.assertEqual(p.world.story["beats"][ids.index("lighthouse_relight")]["state"], "active")
                p.walk_to(p.room_by_def("lighthouse/base"))
                p.do("take can")
                p.do("up")
                out = p.do("light lamp")
                self.assertIn("roars into life", out)
                self.assertEqual(p.world.story["beats"][ids.index("lighthouse_relight")]["state"], "done")


class SciFiPlaythrough(unittest.TestCase):
    def play(self, mods, seed, fight=False):
        p = Player(mods, seed, premise="dead_signal")
        w = p.world
        self.assertEqual([b["id"] for b in w.story["beats"]],
                         ["derelict_signal", "derelict_doctor", "derelict_reactor"], p.log)
        p.walk_to(p.room_by_def("docking_ring/bay"), fight)
        p.do("read terminal")
        p.walk_to(p.room_by_def("medbay/ward"), fight)
        p.do("talk to doctor")
        self.assertEqual(w.story["beats"][1]["state"], "done")
        coupling = w.get(w.story["beats"][2]["roles"]["coupling"])
        p.walk_to(w.room_of(coupling), fight)
        p.do("take coupling")
        self.assertTrue(w.is_inside(coupling, w.player))
        p.walk_to(p.room_by_def("reactor_deck/access"), fight)
        p.do("use keycard on reader")
        p.walk_to(p.room_by_def("reactor_deck/core"), fight)
        p.do("put coupling in socket")
        self.assertTrue(w.story["complete"])

    def test_story(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                self.play(SCIFI, seed)

    def test_story_with_combat(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                self.play(SCIFI + ["combat"], seed, fight=True)


if __name__ == "__main__":
    unittest.main()
