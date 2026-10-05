"""Throw thousands of random commands at worlds built from every mod: nothing may crash."""

import random
import unittest

from helpers import Player, available

ALL = sorted(available())
VERBS = ["look", "x", "take", "drop", "open", "close", "unlock", "search", "use", "talk to", "give",
         "eat", "drink", "read", "light", "extinguish", "push", "pull", "touch", "listen", "smell",
         "attack", "put", "wait", "rest", "status", "time", "journal", "inventory", "map", "story",
         "take all", "drop all", "go to", "again", "help", "exits", "brief", "verbose"]


class Fuzz(unittest.TestCase):
    def test_random_commands_never_crash(self):
        for seed in range(1, 9):
            rng = random.Random(seed)
            premise = rng.choice(["waning_light", "dead_signal", "none", None])
            p = Player(ALL, seed, premise=premise)
            p.io.lines = [str(rng.randint(0, 5)) for _ in range(5000)]  # answers to choice menus
            w = p.world
            for step in range(400):
                if w.game_over:
                    break
                room = w.room
                names = [e.name for e in w.scope()] + ["me", "it", "zebra", ""]
                exits = [ex.get("dir") or ex.get("name") or "" for ex in room.exits]
                roll = rng.random()
                if roll < 0.35 and exits:
                    cmd = rng.choice(exits)
                elif roll < 0.45:
                    cmd = "go to " + rng.choice([r.name for r in w.rooms()])
                else:
                    verb = rng.choice(VERBS)
                    cmd = verb + " " + rng.choice(names)
                    if rng.random() < 0.25:
                        cmd += " " + rng.choice(["in", "on", "with", "to"]) + " " + rng.choice(names)
                with self.subTest(seed=seed, step=step, cmd=cmd):
                    p.do(cmd)
                    errors = [l for l in p.io.log if "[mod error]" in l]
                    self.assertEqual(errors, [], cmd)


if __name__ == "__main__":
    unittest.main()
