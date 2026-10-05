"""The Half-Life mods: three spawns, scripted set pieces, and generated sections behind doors."""

import unittest

from helpers import Player
from patchwork.validate import check_world

HL = ["core", "tales", "hl_halflife", "hl_opfor", "hl_blueshift"]
SPAWNS = {
    "hl_blackmesa": ("Gordon Freeman", "hl/c0a0_tram", {"hl_cascade_war", "hl_military_cleanup"}),
    "of_blackmesa": ("Adrian Shephard", "of/of0a0_osprey", {"of_worlds_collide", "of_the_package"}),
    "bs_blackmesa": ("Barney Calhoun", "bs/ba_tram1", {"bs_leap_of_faith"}),
}


class Spawns(unittest.TestCase):
    def test_each_spawn_is_its_own_game(self):
        for start, (name, room, events) in SPAWNS.items():
            for seed in range(1, 6):
                with self.subTest(start=start, seed=seed):
                    p = Player(HL, seed, start=start)
                    w = p.world
                    self.assertEqual(w.player.name, name)
                    self.assertEqual(w.room.def_id, "room:" + room)
                    self.assertIn(w.story["event"], events)
                    self.assertEqual(check_world(w), [], p.log)

    def test_each_campaign_alone_is_completable(self):
        for mods, start in ((["core", "hl_halflife"], "hl_blackmesa"), (["core", "hl_opfor"], "of_blackmesa"),
                            (["core", "hl_blueshift"], "bs_blackmesa")):
            for seed in range(1, 6):
                with self.subTest(mods=mods, seed=seed):
                    p = Player(mods, seed, start=start)
                    self.assertTrue(p.solve(fight=True), "story did not complete")
                    self.assertIsNone(p.world.game_over)

    def test_all_three_campaigns_from_each_spawn(self):
        for start in SPAWNS:
            for seed in range(1, 5):
                with self.subTest(start=start, seed=seed):
                    p = Player(HL, seed, start=start)
                    self.assertTrue(p.solve(fight=True), "story did not complete")
                    self.assertIsNone(p.world.game_over)

    def test_quest_never_uses_scripted_scene_rooms(self):
        for start in SPAWNS:
            for seed in range(1, 6):
                w = Player(HL, seed, start=start).world
                for st in w.story["steps"]:
                    for uid in st["refs"].values():
                        ent = w.get(uid)
                        room = ent if ent is not None and ent.is_room else (w.room_of(ent) if ent else None)
                        self.assertFalse(room is not None and "story_skip" in room.tags,
                                         "%s step %s uses %s" % (start, st["id"], room.name if room else uid))


class Maps(unittest.TestCase):
    def test_rooms_carry_their_map_and_chapter(self):
        w = Player(HL, 1, start="hl_blackmesa").world
        authored = [r for r in w.entities.values() if r.is_room and r.def_id and r.def_id.startswith(("room:hl/", "room:of/", "room:bs/"))]
        self.assertGreater(len(authored), 150)
        for r in authored:
            self.assertTrue(r.props.get("map"), r.def_id)
            self.assertTrue(r.props.get("chapter"), r.def_id)
        p = Player(HL, 1, start="hl_blackmesa")
        self.assertIn("map c0a0", p.do("where"))

    def test_generator_extends_locked_doors_and_outdoors(self):
        for seed in range(1, 4):
            p = Player(["core", "hl_halflife"], seed, start="hl_blackmesa")
            w = p.world
            doors = [e for e in w.entities.values() if "expansion_door" in e.tags]
            self.assertGreaterEqual(len(doors), 5)
            outdoor = [r for r in w.entities.values() if r.is_room and r.area is None and "outdoor" in r.tags]
            self.assertTrue(outdoor, "no generated outdoor sections")
            # A crowbar opens a locked door or jammed hatch, and the way beyond is then open.
            door = next(d for d in doors if d.name.endswith(("door", "hatch")))
            room = w.room_of(door)
            ex = next(x for x in room.exits if x.get("if", {}).get("of") == "uid:" + door.uid)
            w.place(w.player, room)
            self.assertIn("is shut", p.do("go " + w.get(ex["to"]).name.lower()) + " is shut")
            w.spawn_spec({"id": "crowbar"}, w.player)
            p.do("open " + door.name.lower())
            self.assertTrue(door.props.get("open"), p.do("look"))
            self.assertTrue(p.passable(room, ex))


class SetPieces(unittest.TestCase):
    def go(self, p, room):
        p.world.place(p.world.player, p.room_by_def(room))

    def test_resonance_cascade_and_blast_pit(self):
        p = Player(["core", "hl_halflife"], 2, start="hl_blackmesa")
        w = p.world
        self.go(p, "hl/c1a0e_chamber")
        out = p.do("push sample cart")
        self.assertIn("hl_cascade", w.flags, out)
        self.assertIn("RESONANCE", out.upper())
        self.assertIsNone(w.game_over)
        # The tentacles block the exhaust shaft until the engine has been fired.
        self.go(p, "hl/c1a4i_control")
        self.assertIn("NOT READY", p.do("push button"))
        for room, cmd in (("hl/c1a4b_power", "use power switch"), ("hl/c1a4d_oxygen", "turn valve"),
                          ("hl/c1a4f_fuel", "use fuel pump controls")):
            self.go(p, room)
            p.do(cmd)
        self.go(p, "hl/c1a4i_control")
        p.do("push button")
        self.assertIn("hl_tentacles_dead", w.flags)

    def test_apprehension_takes_your_weapons(self):
        p = Player(["core", "hl_halflife"], 3, start="hl_blackmesa")
        w = p.world
        w.flags.add("hl_cascade")
        crowbar = w.spawn_spec({"id": "crowbar"}, w.player)[0]
        self.go(p, "hl/c2a3b_labs")
        p.do("east")
        self.assertEqual(w.room.def_id, "room:hl/c2a4_compactor")
        self.assertFalse(w.is_inside(crowbar, w.player))
        p.do("take crowbar")
        self.assertTrue(w.is_inside(crowbar, w.player))

    def test_gman_offers_the_job_only_at_the_end(self):
        p = Player(["core", "hl_halflife"], 1, start="hl_blackmesa")
        w = p.world
        self.go(p, "hl/c5a1_gman")
        self.assertIn("Not yet", p.do("talk to g-man"))
        self.assertIsNone(w.game_over)
        w.flags.update({"hl_nihilanth_dead", "story_resolved"})
        p.do("talk to g-man", answers=["1"])
        self.assertIsNotNone(w.game_over)


if __name__ == "__main__":
    unittest.main()
