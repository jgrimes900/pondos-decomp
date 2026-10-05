"""The game engine: parsing, verb dispatch, movement, turns and story progress.

The engine knows *how* to run a turn but not *what* any verb does: every
in-world verb (look, take, open, attack...) is defined by mods as data.  The
only commands built into the engine are out-of-world ones such as save, load,
help and quit.
"""

import heapq
import json
import os
import re

from . import textutil
from .describe import Describer
from .logic import Interpreter, StopAction
from .world import World, normalize_handlers

META_COMMANDS = {
    "help": "list commands",
    "save": "save [name] - save the game",
    "load": "load [name] - load a saved game",
    "map": "show the places you have visited",
    "story": "recap the story so far",
    "mods": "list the mods this world was woven from",
    "verbose": "always show full room descriptions",
    "brief": "show short descriptions of rooms you have seen",
    "again": "repeat the last command (also 'g')",
    "quit": "leave the game (also 'exit')",
}


class LoadRequest(Exception):
    def __init__(self, world):
        super().__init__()
        self.world = world


class QuitRequest(Exception):
    pass


def saves_dir():
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    path = os.environ.get("PATCHWORK_SAVES") or os.path.join(data_home, "patchwork", "saves")
    return path


def list_saves():
    d = saves_dir()
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if name.endswith(".json"):
            out.append((name[:-5], os.path.getmtime(os.path.join(d, name))))
    out.sort(key=lambda x: -x[1])
    return [n for n, _ in out]


def load_world(name):
    path = os.path.join(saves_dir(), name + ".json")
    with open(path, "r", encoding="utf-8") as fh:
        return World.from_dict(json.load(fh))


_PUNCT = re.compile(r"[^\w\s'\-]")


class Engine:
    def __init__(self, world, io):
        self.w = world
        self.io = io
        world.io = io
        self.i = Interpreter(world, self)
        self.d = Describer(world, self.i)
        self.reg = world.registry
        self.last_command = None
        self._build_verb_table()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _build_verb_table(self):
        self.aliases = []  # (tuple(words), verb_id)
        for vid, vdef in self.reg["verbs"].items():
            if vdef.get("abstract"):
                continue
            names = [vid] + list(vdef.get("aliases") or [])
            for n in names:
                self.aliases.append((tuple(n.lower().split()), vid))
        self.aliases.sort(key=lambda a: -len(a[0]))
        self.ignore = set(self.reg["strings"].get("ignore_words", ["the", "a", "an"]))

    def opposite(self, d):
        if not d:
            return None
        return self.reg["directions"].get(d, {}).get("opposite")

    def s(self, key, default="", ctx=None, **local):
        ctx = (ctx or self.i.ctx()).derive(local=local) if local else (ctx or self.i.ctx())
        return self.i.render(self.w.string(key, default), ctx)

    # ------------------------------------------------------------------
    # Game start
    # ------------------------------------------------------------------
    def start(self):
        w = self.w
        story = w.story
        title = story.get("title")
        if title:
            self.io.write(title.upper(), "title")
            self.io.write("")
        if story.get("intro"):
            self.io.write(self.i.render(story["intro"], self.i.ctx(beat=0)), "story")
            self.io.write("")
        self.i.fire("start", self.i.ctx())
        if story["beats"]:
            self.activate_beat(0, announce=False)
        room = w.room
        self.enter_room(room, describe=True, travelled=False)
        self.check_story()

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------
    def normalize(self, line):
        line = _PUNCT.sub(" ", line.lower())
        return [t for t in line.split() if t]

    def handle(self, line):
        """Process one line of input."""
        w = self.w
        words = self.normalize(line)
        if not words:
            return
        if words[0] in ("again", "g") and len(words) == 1:
            if not self.last_command:
                self.io.write(self.s("nothing_to_repeat", "There is nothing to repeat."))
                return
            words = self.normalize(self.last_command)
            line = self.last_command
        else:
            self.last_command = line
        if self.meta(words):
            return
        w.interrupt = False
        self.command(words)
        self.check_story()

    def meta(self, words):
        cmd, rest = words[0], words[1:]
        if cmd in ("quit", "exit") and not rest:
            raise QuitRequest()
        if cmd == "help" and not rest:
            self.show_help()
            return True
        if cmd == "save" and len(rest) <= 1:
            self.save(rest[0] if rest else "quicksave")
            return True
        if cmd in ("load", "restore") and len(rest) <= 1:
            name = rest[0] if rest else "quicksave"
            try:
                world = load_world(name)
            except (OSError, ValueError, KeyError) as exc:
                self.io.write("Could not load '%s': %s" % (name, exc), "error")
                return True
            raise LoadRequest(world)
        if cmd == "map" and not rest:
            self.show_map()
            return True
        if cmd == "story" and not rest:
            self.show_story()
            return True
        if cmd == "mods" and not rest:
            for m in self.reg.mods:
                self.io.write("  %s (%s) v%s" % (m["name"], m["id"], m["version"]))
            self.io.write("  seed: %s" % self.w.seed, "dim")
            return True
        if cmd in ("verbose", "brief") and not rest:
            self.w.verbose = cmd == "verbose"
            self.io.write("Room descriptions: %s." % cmd)
            return True
        return False

    def save(self, name):
        name = re.sub(r"[^\w\-]", "_", name)
        d = saves_dir()
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, name + ".json")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.w.to_dict(), fh)
        os.replace(tmp, path)
        self.io.write(self.s("saved", "Game saved as '{name}'.", name=name))

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    def match_verb(self, words):
        for alias, vid in self.aliases:
            n = len(alias)
            if tuple(words[:n]) == alias:
                return vid, words[n:]
        return None, words

    def command(self, words):
        w = self.w
        room = w.room
        # A bare exit name ("north", "n", "ladder") means "go" for verbs that allow it.
        phrase = " ".join(words)
        bare = next((vid for vid, v in self.reg["verbs"].items() if v.get("bare_exit")), None)
        vid, rest = self.match_verb(words)
        if bare and (vid is None or not rest) and (self.find_exit(room, phrase) or self.is_direction(phrase)):
            vid, rest = bare, words
        if vid is None:
            self.io.write(self.s("unknown_verb", "I don't know how to \"{verb}\".", verb=words[0]))
            return
        vdef = self.reg["verbs"][vid]
        rest = [r for r in rest if r not in self.ignore]
        kind = vdef.get("target", "optional")
        if kind == "text" or kind == "none":
            if kind == "none" and rest:
                pass  # ignore stray words ("look around")
            self.dispatch(vid, vdef, None, None, " ".join(rest))
            return
        # Split off a second object: "put coin in box", "unlock door with key".
        tphrase, sphrase = rest, []
        for idx, word in enumerate(rest):
            if word in (vdef.get("prepositions") or []) and idx > 0:
                tphrase, sphrase = rest[:idx], rest[idx + 1:]
                break
        if not tphrase:
            if kind == "entity":
                self.dispatch(vid, vdef, None, None, "", missing=True)
            else:
                self.dispatch(vid, vdef, None, None, "")
            return
        text = " ".join(tphrase)
        if text in ("all", "everything") and vdef.get("all"):
            self.do_all(vid, vdef)
            return
        target = self.resolve(text, vdef.get("scope", "any"))
        if target is None:
            return
        second = None
        if sphrase:
            second = self.resolve(" ".join(sphrase), vdef.get("second_scope", "any"))
            if second is None:
                return
        elif vdef.get("second") == "required":
            self.io.write(self.s("need_second", "{Verb} {target} {prep} what?",
                                 Verb=textutil.cap(vid), target=target.the(),
                                 prep=(vdef.get("prepositions") or ["with"])[0]))
            return
        w.last_target = target.uid
        self.dispatch(vid, vdef, target, second, text)

    def _candidates(self, scope_kind):
        w = self.w
        ents = w.scope()
        if scope_kind == "held":
            ents = [e for e in ents if w.is_inside(e, w.player)]
        elif scope_kind == "room":
            ents = [e for e in ents if not w.is_inside(e, w.player)]
        return ents

    def resolve(self, phrase, scope_kind="any", quiet=False):
        w = self.w
        words = phrase.split()
        if phrase in ("me", "myself", "self", "yourself"):
            return w.player
        if phrase in ("it", "them", "him", "her") and w.last_target:
            ent = w.get(w.last_target)
            if ent is not None and (ent in w.scope() or ent.uid == w.player_uid):
                return ent
        if phrase in ("here", "around", "room"):
            return w.room
        scored = []
        for e in self._candidates(scope_kind):
            name = e.name.lower()
            name_words = name.split()
            explicit = [a.lower() for a in w.def_of(e).get("aliases") or []]
            # The head noun: "lamp" in "great lamp", "can" in "can of lamp oil".
            head = name_words[name_words.index("of") - 1] if "of" in name_words[1:] else name_words[-1]
            if phrase == name:
                score = 100
            elif phrase in explicit:
                score = 90
            elif phrase == head:
                score = 85
            elif phrase in e.aliases:
                score = 70
            elif all(x in name_words or x in e.aliases for x in words):
                score = 50 + (10 if words[-1] == head else 0)
            else:
                continue
            if w.is_inside(e, w.player):
                score += 1  # prefer what you're holding on a tie
            scored.append((score, e))
        if not scored:
            # Is it something you could see only elsewhere?
            if not quiet:
                key = "not_held" if scope_kind == "held" and any(
                    phrase in e.aliases for e in w.scope()) else "not_here"
                default = "You don't have that." if key == "not_held" else "You see no {thing} here."
                self.io.write(self.s(key, default, thing=phrase))
            return None
        scored.sort(key=lambda x: -x[0])
        best = scored[0][0]
        tied = [e for s, e in scored if s >= best - 1 and s // 10 == best // 10]
        names = []
        for e in tied:
            if e.name not in names:
                names.append(e.name)
        if len(names) > 1:
            if not quiet:
                self.io.write(self.s("ambiguous", "Which do you mean: {options}?",
                                     options=textutil.join_list([n for n in names], "or")))
            return None
        return scored[0][1]

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    def do_all(self, vid, vdef):
        w = self.w
        cands = self._candidates(vdef.get("scope", "any"))
        if vdef.get("all") == "direct":
            room = w.room
            holder = w.player if vdef.get("scope") == "held" else room
            cands = [e for e in cands if e.parent == holder.uid]
        cands = [e for e in cands if w.handlers(e, vid) and not e.has_tag("player")]
        if vdef.get("all_if") is not None:
            cands = [e for e in cands if self.i.check(vdef["all_if"], self.i.ctx(self_ent=e, target=e))]
        if not cands:
            self.io.write(self.s("nothing_for_all", "There is nothing to {verb}.", verb=vid))
            return
        for e in cands:
            if e.uid not in w.entities:
                continue
            self.io.write("%s:" % textutil.cap(e.name), "dim")
            self.dispatch(vid, vdef, e, None, e.name, end_turn=False)
            if w.game_over:
                break
        self.end_turn(vdef.get("time", 1))

    def dispatch(self, vid, vdef, target, second, args, missing=False, end_turn=True):
        w = self.w
        ctx = self.i.ctx(self_ent=target, target=target, second=second, args=args, local={"verb": vid})
        try:
            self.i.fire("before:" + vid, ctx)
            self.i.fire("before:*", ctx)
            handled = False
            if missing:
                handled = self.i.run_handlers(_listify(vdef.get("no_target")), ctx)
                if not handled:
                    self.io.write(self.s("what", "What do you want to {verb}?", verb=vid))
                    return
            elif target is not None:
                handled = self.i.run_handlers(w.handlers(target, vid), ctx)
                if not handled and second is not None:
                    handled = self.i.run_handlers(w.handlers(second, vid + "_with"),
                                                  ctx.derive(self_ent=second))
            else:
                room = w.room
                handled = self.i.run_handlers(w.handlers(room, vid), ctx.derive(self_ent=room))
                if not handled:
                    handled = self.i.run_handlers(_listify(vdef.get("no_target")), ctx)
            if not handled:
                handled = self.i.run_handlers(_listify(vdef.get("default")), ctx)
            if not handled:
                self.io.write(self.s("cant", "You can't do that."))
            self.i.fire("after:" + vid, ctx)
            self.i.fire("after:*", ctx)
        except StopAction:
            pass
        if end_turn:
            self.end_turn(vdef.get("time", 1))

    def end_turn(self, time):
        w = self.w
        if not time or w.game_over:
            return
        w.turns += 1
        w.clock += int(time)
        self.tick()

    def tick(self):
        """Run per-turn rules and the on_turn hooks of everything near the player."""
        w = self.w
        try:
            self.i.fire("turn", self.i.ctx())
            room = w.room
            if room is not None:
                for ent in [room] + [e for e in w.descendants(room) if not w.is_inside(e, w.player)]:
                    if w.game_over:
                        break
                    if ent.uid not in w.entities:
                        continue
                    hooks = w.hook(ent, "on_turn")
                    if hooks:
                        self.i.run(hooks, self.i.ctx(self_ent=ent))
            for ent in list(w.entities.values()):
                if w.game_over:
                    break
                if ent.uid in w.entities:
                    hooks = w.hook(ent, "on_tick")
                    if hooks:
                        self.i.run(hooks, self.i.ctx(self_ent=ent))
        except StopAction:
            pass

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def exit_words(self, ex):
        words = []
        if ex.get("dir"):
            words.append(ex["dir"])
            dd = self.reg["directions"].get(ex["dir"], {})
            words.extend(a.lower() for a in dd.get("aliases") or [])
            if dd.get("name"):
                words.append(dd["name"].lower())
        if ex.get("name"):
            words.append(ex["name"].lower())
        words.extend(a.lower() for a in ex.get("aliases") or [])
        return words

    def is_direction(self, phrase):
        for did, dd in self.reg["directions"].items():
            if phrase == did or phrase in [a.lower() for a in dd.get("aliases") or []]:
                return True
        return False

    def find_exit(self, room, phrase):
        if room is None:
            return None
        phrase = " ".join(t for t in phrase.split() if t not in self.ignore)
        visible = self.d.visible_exits(room)
        for ex in visible:
            if phrase in self.exit_words(ex):
                return ex
        for ex in visible:
            dest = self.w.get(ex["to"])
            if dest is None:
                continue
            if phrase == dest.name.lower():
                return ex
            # The destination's other names work whenever the player can see them: once
            # visited, or when the exit is labelled by its destination because it has no
            # direction or name of its own (for example where two settings' maps meet).
            shown = dest.visited or ex.get("show_dest") or not (ex.get("dir") or ex.get("name"))
            if shown and phrase in dest.aliases:
                return ex
        return None

    def travel(self, text):
        w = self.w
        words = [t for t in text.lower().split() if t not in self.ignore]
        if not words:
            self.io.write(self.s("go_where", "Where do you want to go?"))
            return
        if words[0] == "to" and len(words) > 1:
            words = words[1:]
        phrase = " ".join(words)
        room = w.room
        ex = self.find_exit(room, phrase)
        if ex is not None:
            self.take_exit(room, ex)
            return
        dest = self.find_known_room(phrase)
        if dest is None:
            self.io.write(self.s("no_exit", "You can't go that way."))
            return
        if dest.uid == room.uid:
            self.io.write(self.s("already_here", "You are already there."))
            return
        path = self.route(room, dest)
        if path is None:
            self.io.write(self.s("no_route", "You don't know a way to get there from here."))
            return
        total = sum(ex.get("distance", 1) for _, ex in path)
        self.io.write(self.s("journey", "You set out for {dest} ({hops} legs, distance {distance}).",
                             dest=dest.name, hops=len(path), distance=total), "dim")
        for idx, (frm, ex) in enumerate(path):
            last = idx == len(path) - 1
            if not self.take_exit(frm, ex, describe=last):
                return
            if w.game_over or w.interrupt:
                if not last:
                    self.io.write(self.s("journey_interrupted", "Your journey is interrupted."), "warn")
                    self.show("room", w.room, None)
                return

    def find_known_room(self, phrase):
        best = None
        for r in self.w.rooms():
            if not r.visited:
                continue
            if phrase == r.name.lower():
                return r
            if best is None and (phrase in r.aliases or all(x in r.name.lower().split() for x in phrase.split())):
                best = r
        return best

    def route(self, src, dst):
        """Dijkstra over visited rooms and currently passable exits."""
        w = self.w
        dist = {src.uid: 0}
        prev = {}
        heap = [(0, src.uid)]
        while heap:
            d, uid = heapq.heappop(heap)
            if uid == dst.uid:
                break
            if d > dist.get(uid, 1e18):
                continue
            room = w.get(uid)
            for ex in self.d.visible_exits(room):
                nxt = w.get(ex["to"])
                if nxt is None or (not nxt.visited and nxt.uid != dst.uid):
                    continue
                if ex.get("if") is not None and not self.i.check(ex["if"], self.i.ctx(self_ent=room)):
                    continue
                nd = d + ex.get("distance", 1)
                if nd < dist.get(nxt.uid, 1e18):
                    dist[nxt.uid] = nd
                    prev[nxt.uid] = (uid, ex)
                    heapq.heappush(heap, (nd, nxt.uid))
        if dst.uid not in prev:
            return None
        path = []
        cur = dst.uid
        while cur != src.uid:
            p, ex = prev[cur]
            path.append((w.get(p), ex))
            cur = p
        path.reverse()
        return path

    def take_exit(self, room, ex, describe=True):
        w = self.w
        dest = w.get(ex["to"])
        ctx = self.i.ctx(self_ent=room, local={"distance": ex.get("distance", 1), "dir": ex.get("dir") or ""})
        if dest is None:
            self.io.write(self.s("no_exit", "You can't go that way."))
            return False
        if ex.get("if") is not None and not self.i.check(ex["if"], ctx):
            self.io.write(self.i.render(ex.get("blocked") or w.string("blocked", "You can't go that way right now."), ctx))
            return False
        try:
            self.i.fire("leave", ctx.derive(target=dest))
            if ex.get("on_use"):
                self.i.run(ex["on_use"], ctx)
        except StopAction:
            return False
        dist = int(ex.get("distance", 1))
        w.clock += dist * int(w.setting("time_per_distance", 1))
        w.turns += 1
        try:
            self.i.fire("travel", ctx.derive(target=dest))
        except StopAction:
            return False
        if w.game_over:
            return False
        # Arriving does not give the room's occupants a free turn: the player acts first.
        self.enter_room(dest, describe=describe)
        return not w.game_over

    def enter_room(self, dest, describe=True, travelled=True):
        w = self.w
        first = not dest.visited
        w.place(w.player, dest)
        dest.visited = True
        if describe:
            self.show("room", dest, None, brief=not first and not w.verbose)
        ctx = self.i.ctx(self_ent=dest, local={"first": first})
        try:
            for ent in [dest] + [e for e in w.descendants(dest) if not w.is_inside(e, w.player)]:
                if ent.uid not in w.entities or w.game_over:
                    continue
                hooks = w.hook(ent, "on_enter")
                if hooks:
                    self.i.run(hooks, ctx.derive(self_ent=ent))
            self.i.fire("enter", ctx)
        except StopAction:
            pass

    # ------------------------------------------------------------------
    # Output helpers (also reachable from mods through the "show" effect)
    # ------------------------------------------------------------------
    def show(self, what, ent, ctx, brief=False):
        w = self.w
        if what in ("room", "look"):
            room = ent if ent is not None and ent.is_room else w.room
            self.io.write("")
            for text, kind in self.d.room(room, brief=brief):
                self.io.write(text, kind)
        elif what in ("entity", "examine"):
            if ent is None:
                return
            if ent.is_room:
                self.show("room", ent, ctx)
            else:
                self.io.write(self.d.entity(ent))
        elif what == "inventory":
            self.io.write(self.d.inventory(ent if ent is not None and not ent.is_room else w.player))
        elif what == "exits":
            self.io.write(self.d.exits_line(w.room), "exit")
        elif what == "journal":
            self.show_journal()
        elif what == "help":
            self.show_help()
        elif what == "map":
            self.show_map()
        elif what == "story":
            self.show_story()
        else:
            w.say("[mod error] cannot show '%s'" % what, "error")

    def show_help(self):
        self.io.write(self.s("help_header", "Commands:"), "bold")
        rows = []
        for vid, vdef in sorted(self.reg["verbs"].items()):
            if vdef.get("abstract") or vdef.get("hidden"):
                continue
            usage = vdef.get("help") or vid
            aliases = [a for a in vdef.get("aliases") or [] if a != vid]
            if aliases:
                usage += "  (" + ", ".join(aliases[:4]) + ")"
            rows.append("  " + usage)
        self.io.write("\n".join(rows))
        self.io.write(self.s("help_meta", "Game:"), "bold")
        self.io.write("\n".join("  %-8s %s" % (k, v) for k, v in META_COMMANDS.items()))
        dirs = self.reg["directions"]
        if dirs:
            self.io.write(self.s("help_dirs", "You can type an exit's name on its own to go that way, "
                                              "or 'go to <place>' to travel to somewhere you have been."), "dim")

    def show_journal(self):
        w = self.w
        story = w.story
        if story.get("title"):
            self.io.write(story["title"], "title")
        cur = story.get("current", 0)
        beats = story.get("beats", [])
        if cur < len(beats):
            self.io.write(self.s("journal_current", "Current goal: {title}", title=beats[cur]["title"]), "story")
            bdef = self.reg["beats"].get(beats[cur]["id"], {})
            if bdef.get("hint"):
                self.io.write("  " + self.i.render(bdef["hint"], self.i.ctx(beat=cur)), "dim")
        elif beats:
            self.io.write(self.s("journal_done", "Your tale is told, but the world remains to explore."), "story")
        if not w.journal:
            self.io.write(self.s("journal_empty", "Your journal is empty."))
            return
        for entry in w.journal[-15:]:
            self.io.write("- " + entry["text"])

    def show_story(self):
        beats = self.w.story.get("beats", [])
        if not beats:
            self.io.write(self.s("no_story", "This world has no story; it is yours to explore."))
            return
        for idx, b in enumerate(beats):
            mark = {"done": "x", "active": ">", "pending": " "}.get(b.get("state"), " ")
            label = b["title"] if b.get("state") != "pending" else self.s("unknown_chapter", "???")
            self.io.write("[%s] %s" % (mark, label))

    def show_map(self):
        w = self.w
        visited = [r for r in w.rooms() if r.visited]
        if not visited:
            return
        here = w.room
        groups = {}
        for r in visited:
            key = w.areas.get(r.area, {}).get("name") if r.area else self.s("map_wilds", "Along the way")
            groups.setdefault(key, []).append(r)
        for gname, rooms in groups.items():
            self.io.write(gname, "bold")
            for r in sorted(rooms, key=lambda r: r.name):
                links = []
                for ex in self.d.visible_exits(r):
                    dest = w.get(ex["to"])
                    label = ex.get("dir") or ex.get("name") or "path"
                    links.append("%s->%s(%s)" % (label, dest.name if dest and dest.visited else "?",
                                                 ex.get("distance", 1)))
                marker = "*" if r is here else " "
                self.io.write(" %s %s: %s" % (marker, r.name, ", ".join(links)))

    # ------------------------------------------------------------------
    # Story progression
    # ------------------------------------------------------------------
    def activate_beat(self, idx, announce=True):
        w = self.w
        beats = w.story["beats"]
        if idx >= len(beats):
            return
        beat = beats[idx]
        beat["state"] = "active"
        w.story["current"] = idx
        bdef = self.reg["beats"].get(beat["id"], {})
        ctx = self.i.ctx(beat=idx)
        if announce:
            self.io.write("")
            self.io.write(self.s("chapter", "~ {title} ~", ctx=ctx, title=beat["title"]), "title")
        if bdef.get("intro"):
            self.io.write(self.i.render(bdef["intro"], ctx), "story")
        journal = bdef.get("journal") or bdef.get("hint")
        if journal:
            w.journal.append({"time": w.clock, "text": self.i.render(journal, ctx)})
        try:
            self.i.run(bdef.get("on_start"), ctx)
        except StopAction:
            pass

    def beat_index(self, which):
        beats = self.w.story["beats"]
        if which in (True, "self", "current", None):
            return self.w.story.get("current", 0)
        for idx, b in enumerate(beats):
            if b["id"] == which:
                return idx
        return None

    def complete_beat(self, which):
        w = self.w
        idx = self.beat_index(which)
        beats = w.story["beats"]
        if idx is None or idx >= len(beats) or beats[idx].get("state") == "done":
            return
        beat = beats[idx]
        bdef = self.reg["beats"].get(beat["id"], {})
        beat["state"] = "done"
        ctx = self.i.ctx(beat=idx)
        try:
            self.i.run(bdef.get("on_complete"), ctx)
        except StopAction:
            pass
        if bdef.get("complete_text"):
            self.io.write(self.i.render(bdef["complete_text"], ctx), "story")
        w.journal.append({"time": w.clock, "text": self.s("journal_done_entry", "Done: {title}.", title=beat["title"])})
        if idx == w.story.get("current", 0):
            nxt = idx + 1
            while nxt < len(beats) and beats[nxt].get("state") == "done":
                nxt += 1
            if nxt < len(beats):
                self.activate_beat(nxt)
                if self.reg["settings"].get("auto_lead", True):
                    self.show_lead(self.i.ctx(beat=nxt))
            else:
                w.story["current"] = len(beats)
                self.finish_story()

    def show_lead(self, ctx):
        beats = self.w.story["beats"]
        idx = ctx.beat if ctx is not None and ctx.beat is not None else self.w.story.get("current", 0)
        if idx >= len(beats):
            return
        bdef = self.reg["beats"].get(beats[idx]["id"], {})
        lead = bdef.get("lead")
        area = beats[idx].get("area")
        here = self.w.room.area if self.w.room is not None else None
        if lead is None and area and area in self.w.areas and area != here:
            lead = self.w.string("default_lead", "")
        if lead:
            self.io.write(self.i.render(lead, self.i.ctx(beat=idx)), "story")

    def finish_story(self):
        w = self.w
        if w.story.get("complete"):
            return
        w.story["complete"] = True
        ending = w.story.get("ending")
        self.io.write("")
        if ending:
            self.io.write(self.i.render(ending, self.i.ctx()), "story")
        if w.story.get("end_on_complete"):
            w.game_over = {"text": self.s("the_end", "THE END"), "win": True}
        else:
            self.io.write(self.s("story_complete", "Your story is complete, but the world remains. "
                                                   "You may keep exploring."), "good")
        try:
            self.i.fire("story_complete", self.i.ctx())
        except StopAction:
            pass

    def check_story(self):
        w = self.w
        for _ in range(len(w.story.get("beats", [])) + 1):
            if w.game_over or w.story.get("complete"):
                return
            idx = w.story.get("current", 0)
            beats = w.story["beats"]
            if idx >= len(beats):
                return
            bdef = self.reg["beats"].get(beats[idx]["id"], {})
            obj = bdef.get("objective")
            if obj is None or not self.i.check(obj, self.i.ctx(beat=idx)):
                return
            self.complete_beat(beats[idx]["id"])


def _listify(v):
    return normalize_handlers(v)
