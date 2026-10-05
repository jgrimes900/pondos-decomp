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

    def __init__(self, ids, seed, name="Tester", answers=None, size="medium", start=None):
        self.reg = registry(ids)
        self.world, self.log = generate(self.reg, seed=seed, player_name=name, size=size, start=start)
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

    def path_to(self, dest, strict=True):
        start = self.room
        prev = {start.uid: None}
        q = collections.deque([start])
        while q:
            r = q.popleft()
            if r.uid == dest.uid:
                break
            for ex in r.exits:
                if ex.get("hidden") or (strict and not self.passable(r, ex)):
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
        for _ in range(500):
            if self.room.uid == dest.uid or self.world.game_over:
                return True
            path = self.path_to(dest)
            if path is None:
                # Blocked by a scripted gate: open it the way its mod says (exit "solve" hints).
                path = self.path_to(dest, strict=False)
                assert path is not None, "no path from %s to %s" % (self.room.name, dest.name)
                gate = next(((r, ex) for r, ex in path if not self.passable(r, ex)), None)
                assert gate is not None and gate[1].get("solve") and gate[1]["to"] not in self.solving, \
                    "no way through to %s from %s" % (dest.name, self.room.name)
                self.open_gate(gate[1], fight)
                continue
            _r, ex = path[0]
            self.patch_up()
            self.do(self.exit_command(ex))
            if fight:
                self.clear_hostiles()
        return self.room.uid == dest.uid

    solving = ()

    def open_gate(self, ex, fight):
        self.solving = tuple(self.solving) + (ex["to"],)
        try:
            for op in ex["solve"]:
                if op[0] == "goto":
                    self.walk_to(self.room_by_def(op[1]), fight)
                else:
                    self.patch_up()
                    self.do(op[1])
        finally:
            self.solving = self.solving[:-1]

    def ensure_held(self, uid, fight, then=None):
        """Fetch an item the next command needs if it isn't in hand (taken away by a scripted scene)."""
        w = self.world
        ent = w.get(uid)
        if ent is None or "portable" not in ent.tags or w.is_inside(ent, w.player):
            return
        self.walk_to(w.room_of(ent), fight)
        self.do("take " + self.name_of(uid))
        back = w.get(then) if then else None
        if back is not None:
            self.walk_to(back if back.is_room else w.room_of(back), fight)

    def recover_lost(self, before, op, fight):
        """Things a scripted scene took off the player (not given or used by this op) are fetched back."""
        w = self.world
        for uid in before:
            ent = w.get(uid)
            if ent is None or uid in op or w.is_inside(ent, w.player):
                continue
            holder = w.get(ent.parent)
            if holder is not None and ("person" in holder.tags or "creature" in holder.tags):
                continue
            here = self.room
            self.ensure_held(uid, fight, then=here.uid)

    def hostiles(self):
        return [e for e in self.world.visible_tree(self.room) if e.props.get("hostile") and e.props.get("health", 0) > 0]

    def clear_hostiles(self, max_rounds=40):
        for _ in range(max_rounds):
            foes = self.hostiles()
            if not foes or self.world.game_over:
                return
            foe = foes[0]
            self.patch_up()
            self.do("attack " + foe.name)

    # -- solving generated stories ---------------------------------------
    def name_of(self, uid):
        return self.world.get(uid).name.lower()

    def patch_up(self):
        # Stands in for the medkits and chargers a human player would use between fights.
        w = self.world
        if w.player.props.get("health", 99) < 40:
            w.player.props["health"] = w.player.props.get("max_health", 20)

    def run_op(self, op, fight):
        w = self.world
        self.patch_up()
        kind = op[0]
        if any(isinstance(x, str) and x.startswith(("e", "f", "r")) and w.get(x) is None
               and x not in w.entities for x in op[1:] if x) and kind != "cmd":
            self.engine.check_story()   # something it needed was killed; the step settles itself
            return ""
        if kind == "goto":
            ent = w.get(op[1])
            assert ent is not None, "solution refers to a missing entity"
            room = ent if ent.is_room else w.room_of(ent)
            assert self.walk_to(room, fight), "could not reach %s" % room.name
            return ""
        if kind == "reveal":
            ent = w.get(op[1])
            if ent is None or not ent.hidden:
                return ""
            parent = w.get(ent.parent)
            return self.do("search" if parent.is_room else "search " + parent.name.lower())
        if kind in ("open", "take", "talk", "read", "examine"):
            verb = {"talk": "talk to"}.get(kind, kind)
            if kind == "open" and w.get(op[1]).props.get("open"):
                return ""
            return self.do("%s %s" % (verb, self.name_of(op[1])))
        if kind in ("give", "use"):
            self.ensure_held(op[1], fight, then=op[2])
        if kind == "cmd" and op[2]:
            self.ensure_held(op[2], fight, then=op[3])
        if kind == "give":
            return self.do("give %s to %s" % (self.name_of(op[1]), self.name_of(op[2])))
        if kind == "use":
            return self.do("use %s on %s" % (self.name_of(op[1]), self.name_of(op[2])))
        if kind == "cmd":
            verb, means, target = op[1], op[2], op[3]
            if verb == "attack":
                out = ""
                foe = w.get(target)
                for command in (w.resolve_def(foe.def_id) or {}).get("solve") or [] if foe else []:
                    self.patch_up()
                    out += self.do(command)   # a boss's mod says how to soften it up first
                for _ in range(60):
                    if w.get(target) is None or w.game_over:
                        break
                    self.patch_up()
                    out += self.do("attack " + self.name_of(target))
                return out
            prep = {"put": "in", "use": "on", "give": "to"}.get(verb)
            if w.get(target) is None:
                self.engine.check_story()
                return ""
            if means and prep:
                return self.do("%s %s %s %s" % (verb, self.name_of(means), prep, self.name_of(target)))
            return self.do("%s %s" % (verb, self.name_of(target)))
        raise AssertionError("unknown solution op %r" % (op,))

    def solve(self, fight=False):
        """Play the generated main quest to the end using each step's recorded solution."""
        w = self.world
        for _ in range(len(w.story["steps"]) + 2):
            if w.story.get("complete") or w.game_over:
                break
            st = w.story["steps"][w.story["current"]]
            transcript = []
            for op in st["solution"]:
                transcript.append(">> %r" % (op,))
                before = [e.uid for e in w.descendants(w.player) if "portable" in e.tags]
                transcript.append(self.run_op(tuple(op), fight))
                self.recover_lost(before, op, fight)
                if st.get("state") == "done":
                    break
            assert st.get("state") == "done", "step %s (%s: %s) not completed:\n%s" % (
                st["id"], st["kind"], st["title"], "\n".join(t for t in transcript if t)[-3000:])
        return w.story.get("complete")
