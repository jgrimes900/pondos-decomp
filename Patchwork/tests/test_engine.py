"""Unit and integration tests for the engine, mod loader and generator."""

import itertools
import json
import os
import tempfile
import unittest

from helpers import MOD_DIR, Player, available, registry

from patchwork.engine import Engine
from patchwork.generator import GenerationError, generate
from patchwork.mods import Registry, deep_patch, resolve_order
from patchwork.ui import ScriptIO
from patchwork.validate import check_registry, check_world
from patchwork.world import World

ALL = sorted(m for m in available() if m != "lighthouse")


class ModLoading(unittest.TestCase):
    def test_every_mod_is_discovered(self):
        for mid in ("core", "wilds", "hamlet", "combat", "barrow", "spire", "saga_waning_light", "derelict"):
            self.assertIn(mid, ALL)

    def test_dependencies_are_added_and_ordered(self):
        ordered, added, problems = resolve_order(["barrow"], available())
        self.assertEqual(problems, [])
        self.assertIn("core", added)
        self.assertEqual([m.id for m in ordered][0], "core")

    def test_load_after_is_respected(self):
        ordered, _a, _p = resolve_order(["combat", "wilds", "core"], available())
        ids = [m.id for m in ordered]
        self.assertLess(ids.index("wilds"), ids.index("combat"))

    def test_missing_dependency_is_reported(self):
        _o, _a, problems = resolve_order(["nonexistent"], available())
        self.assertTrue(problems)

    def test_patches_and_grammar_merge(self):
        reg = registry(["core", "wilds", "hamlet", "combat"])
        # combat patches the core player and edible trait
        self.assertEqual(reg["features"]["player"]["props"]["health"], 20)
        self.assertEqual(reg["features"]["edible"]["props"]["heal"], 2)
        # both wilds and hamlet contribute names to the shared "given" grammar
        given = reg["grammar"]["given"]
        self.assertIn("Bram", given)   # from wilds
        self.assertIn("Maud", given)   # from hamlet

    def test_deep_patch_list_operators(self):
        base = {"tags": ["a", "b"], "props": {"x": 1, "y": 2}}
        out = deep_patch(base, {"+tags": ["c"], "-tags": ["a"], "props": {"y": 5}})
        self.assertEqual(out["tags"], ["b", "c"])
        self.assertEqual(out["props"], {"x": 1, "y": 5})

    def test_all_mods_validate_cleanly(self):
        problems = [p for p in check_registry(registry(ALL)) if not p.startswith("note:")]
        self.assertEqual(problems, [])

    def test_core_alone_cannot_build_a_world(self):
        with self.assertRaises(GenerationError):
            generate(registry(["core"]), seed=1)


class Generation(unittest.TestCase):
    COMBOS = [
        ["core", "wilds"],
        ["core", "hamlet"],
        ["core", "barrow"],
        ["core", "spire"],
        ["core", "derelict"],
        ["core", "wilds", "hamlet"],
        ["core", "wilds", "barrow", "combat"],
        ["core", "wilds", "hamlet", "barrow", "spire", "saga_waning_light", "combat"],
        ["core", "derelict", "combat"],
        ALL,
    ]

    def test_worlds_are_sound_for_many_combinations(self):
        for combo in self.COMBOS:
            reg = registry(combo)
            for seed in range(1, 16):
                with self.subTest(combo=combo, seed=seed):
                    world, log = generate(reg, seed=seed)
                    self.assertEqual(check_world(world), [], log)

    def test_same_seed_same_world(self):
        reg = registry(ALL)
        a, _ = generate(reg, seed=99)
        b, _ = generate(reg, seed=99)
        self.assertEqual(sorted(r.name for r in a.rooms()), sorted(r.name for r in b.rooms()))

    def test_gates_hold_until_beat_reached(self):
        p = Player(["core", "wilds", "hamlet", "barrow", "spire", "saga_waning_light"], seed=3)
        top = p.room_by_def("spire/foot")
        self.assertIsNone(p.path_to(top), "the spire should be gated at the start")

    def test_story_elements_come_from_several_mods(self):
        p = Player(["core", "wilds", "hamlet", "barrow", "spire", "saga_waning_light"], seed=5)
        mods = {p.reg.sources[("beats", b["id"])] for b in p.world.story["beats"]}
        self.assertEqual(mods, {"hamlet", "barrow", "spire"})
        # The spire's "bane" role re-uses the relic placed by the barrow mod.
        beats = {b["id"]: b for b in p.world.story["beats"]}
        self.assertEqual(beats["spire_confrontation"]["roles"]["bane"], beats["barrow_relic"]["roles"]["relic"])

    def test_sandbox_without_story(self):
        world, _ = generate(registry(["core", "wilds"]), seed=2)
        self.assertEqual(world.story["beats"], [])
        self.assertGreaterEqual(len(world.rooms()), 10)

    def test_ship_directions_stay_on_the_ship(self):
        reg = registry(ALL)
        for seed in range(1, 10):
            world, _ = generate(reg, seed=seed, premise="dead_signal")
            for r in world.rooms():
                for ex in r.exits:
                    dest = world.get(ex["to"])
                    if r.region and r.region.startswith("station") and dest.region and dest.region.startswith("station"):
                        self.assertIn(ex["dir"], (None, "fore", "aft", "port", "starboard"))
                    if r.region in ("forest", "road", "hills"):
                        self.assertNotIn(ex["dir"], ("fore", "aft", "port", "starboard"))


class Parser(unittest.TestCase):
    def setUp(self):
        self.p = Player(["core", "wilds", "hamlet"], seed=7)

    def test_take_and_drop_all(self):
        p = self.p
        p.do("search bed")
        out = p.do("take all")
        self.assertIn("travel pack", out)
        self.assertNotIn("hearth", out)  # scenery is skipped
        out = p.do("drop all")
        self.assertIn("travel pack", out)

    def test_nested_containers_and_it(self):
        p = self.p
        p.do("search bed")
        p.do("take pack")
        out = p.do("examine it")
        self.assertIn("tinderbox", out)
        out = p.do("i")
        self.assertIn("holding", out)

    def test_unknown_things(self):
        self.assertIn("no \"zebra\"", self.p.do("take zebra"))
        self.assertIn("don't know", self.p.do("frobnicate"))
        self.assertIn("can't go", self.p.do("north"))

    def test_dialogue_choice(self):
        out = self.p.do("talk to innkeeper", answers=["2"])
        self.assertIn("On the house", out)
        out = self.p.do("eat bread")
        self.assertIn("You eat", out)

    def test_bare_direction_and_go_to(self):
        p = self.p
        p.do("s")
        self.assertEqual(p.room.def_id, "room:hamlet/green")
        p.do("e")
        out = p.do("go to inn")
        self.assertIn("set out", out)
        self.assertEqual(p.room.def_id, "room:hamlet/inn")

    def test_put_in_container(self):
        p = self.p
        p.do("search bed")
        p.do("take pack")
        p.do("take candle")
        out = p.do("put candle in pack")
        self.assertIn("You put", out)
        candle = [e for e in p.world.entities.values() if e.name == "candle stub"][0]
        self.assertEqual(p.world.get(candle.parent).name, "travel pack")


class SeamExits(unittest.TestCase):
    """Exits with no direction (where two settings' maps meet) must be usable by
    the destination's name even before the destination has been visited."""

    def test_seam_exit_usable_by_partial_name(self):
        checked = 0
        for seed in range(1, 30):
            p = Player(["core", "wilds", "hamlet", "derelict"], seed)
            w = p.world
            for room in w.rooms():
                for ex in room.exits:
                    if ex.get("dir") or ex.get("name") or ex.get("hidden") or ex.get("if"):
                        continue
                    dest = w.get(ex["to"])
                    for r in w.rooms():
                        r.visited = False
                    word = max(dest.name.lower().split(), key=len)  # e.g. "hydroponics"
                    for cmd in (word, "go " + word, "go to " + word):
                        w.place(w.player, room)
                        p.do(cmd)
                        self.assertEqual(w.room.uid, dest.uid,
                                         "seed %d: '%s' from %s" % (seed, cmd, room.name))
                    checked += 1
        self.assertGreater(checked, 0, "no seam exits generated; test needs other seeds")


class SaveLoad(unittest.TestCase):
    def test_round_trip(self):
        p = Player(["core", "wilds", "hamlet", "barrow", "spire", "saga_waning_light", "combat"], seed=12)
        p.walk_to(p.room_by_def("hamlet/cottage"))
        p.do("talk to elder")
        data = json.loads(json.dumps(p.world.to_dict()))
        w2 = World.from_dict(data)
        self.assertEqual(w2.room.uid, p.world.room.uid)
        self.assertEqual(w2.story["current"], p.world.story["current"])
        io = ScriptIO([], echo=False)
        eng = Engine(w2, io)
        eng.handle("look")
        self.assertIn(p.world.room.name, io.text())
        # RNG state survives too: both worlds now make the same random choices.
        self.assertEqual(w2.rng.random(), p.world.rng.random())

    def test_save_command_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PATCHWORK_SAVES"] = tmp
            try:
                p = Player(["core", "wilds"], seed=1)
                p.do("save testslot")
                self.assertTrue(os.path.exists(os.path.join(tmp, "testslot.json")))
            finally:
                del os.environ["PATCHWORK_SAVES"]


class Combat(unittest.TestCase):
    def test_player_can_die(self):
        p = Player(["core", "wilds", "combat"], seed=4)
        w = p.world
        wolf_room = p.room
        p.world.spawn_spec("grey_wolf", wolf_room)
        w.player.props["health"] = 1
        for _ in range(10):
            p.do("wait")
            if w.game_over:
                break
        self.assertIsNotNone(w.game_over)
        self.assertFalse(w.game_over["win"])

    def test_killing_drops_loot(self):
        p = Player(["core", "wilds", "combat"], seed=4)
        w = p.world
        bandit = w.spawn_spec("bandit", p.room)[0]
        bandit.props["health"] = 1
        p.do("attack bandit")
        self.assertNotIn(bandit.uid, w.entities)
        self.assertTrue(any(e.name == "knotted cudgel" for e in w.visible_children(p.room)))


if __name__ == "__main__":
    unittest.main()
