"""Shared helpers for the test-suite: build worlds and drive the engine like a player."""

import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from patchwork.engine import Engine  # noqa: E402
from patchwork.generator import generate  # noqa: E402
from patchwork.mods import build_registry, discover, resolve_order  # noqa: E402
from patchwork.ui import ScriptIO  # noqa: E402

MOD_DIR = os.path.join(ROOT, "mods")
EXAMPLES_DIR = os.path.join(ROOT, "examples")


def available():
    mods, errors = discover([MOD_DIR, EXAMPLES_DIR])
    assert not errors, errors
    return mods


def registry(ids):
    ordered, _added, problems = resolve_order(ids, available())
    assert not problems, problems
    return build_registry(ordered)


class Player:
    """Drives an Engine through ordinary text commands."""

    def __init__(self, ids, seed, premise=None, name="Tester", answers=None):
        self.reg = registry(ids)
        self.world, self.log = generate(self.reg, seed=seed, premise=premise, player_name=name)
        self.io = ScriptIO(answers or [], echo=False)
        self.engine = Engine(self.world, self.io)
        self.engine.start()

    # -- basic interaction -------------------------------------------
    def do(self, command, answers=()):
        self.io.lines.extend(answers)
        start = len(self.io.log)
        self.engine.handle(command)
        return "\n".join(self.io.log[start:])

    @property
    def room(self):
        return self.world.room

    def find(self, pred):
        return [e for e in self.world.entities.values() if pred(e)]

    def entity_by_def(self, def_id):
        found = self.find(lambda e: e.def_id == def_id)
        return found[0] if found else None

    def room_by_def(self, room_id):
        return self.world.get(room_id) or self.entity_by_def("room:" + room_id)

    # -- navigation ----------------------------------------------------
    def passable(self, room, ex):
        cond = ex.get("if")
        if cond is None:
            return True
        return self.engine.i.check(cond, self.engine.i.ctx(self_ent=room))

    def path_to(self, dest):
        start = self.room
        prev = {start.uid: None}
        q = collections.deque([start])
        while q:
            r = q.popleft()
            if r.uid == dest.uid:
                break
            for ex in r.exits:
                if ex.get("hidden") or not self.passable(r, ex):
                    continue
                nxt = self.world.get(ex["to"])
                if nxt is not None and nxt.uid not in prev:
                    prev[nxt.uid] = (r, ex)
                    q.append(nxt)
        if dest.uid not in prev:
            return None
        hops = []
        cur = dest.uid
        while prev[cur] is not None:
            r, ex = prev[cur]
            hops.append((r, ex))
            cur = r.uid
        return list(reversed(hops))

    def exit_command(self, ex):
        if ex.get("dir"):
            return ex["dir"]
        if ex.get("name"):
            return "go " + ex["name"]
        return "go " + self.world.get(ex["to"]).name

    def walk_to(self, dest, fight=False):
        if dest.is_room is False:
            dest = self.world.room_of(dest)
        for _ in range(60):
            if self.room.uid == dest.uid or self.world.game_over:
                return True
            path = self.path_to(dest)
            assert path is not None, "no path from %s to %s" % (self.room.name, dest.name)
            _r, ex = path[0]
            self.do(self.exit_command(ex))
            if fight:
                self.clear_hostiles()
        return self.room.uid == dest.uid

    def hostiles(self):
        return [e for e in self.world.visible_tree(self.room) if e.props.get("hostile") and e.props.get("health", 0) > 0]

    def clear_hostiles(self, max_rounds=40):
        for _ in range(max_rounds):
            foes = self.hostiles()
            if not foes or self.world.game_over:
                return
            foe = foes[0]
            if self.world.player.props.get("health", 99) < 8:
                self.world.player.props["health"] = self.world.player.props.get("max_health", 20)
            self.do("attack " + foe.name)
