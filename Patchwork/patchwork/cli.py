"""Command-line entry point: main menu, mod selection and the game loop."""

import argparse
import json
import os
import sys
import zlib

from . import __version__, textutil
from .engine import Engine, LoadRequest, QuitRequest, list_saves, load_world
from .generator import GenerationError, generate
from .mods import ModError, build_registry, default_mod_dirs, discover, resolve_order
from .ui import ScriptIO, TerminalIO
from .validate import check_registry, smoke_generate

BANNER = r"""
  ___       _      _                   _
 | _ \__ _ | |_ __| |_ __ __ _____ _ _| |__
 |  _/ _` ||  _/ _| ' \\ V  V / _ \ '_| / /
 |_| \__,_| \__\__|_||_|\_/\_/\___/_| |_\_\
"""


def config_path():
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(data_home, "patchwork", "last_mods.json")


def remember_selection(ids):
    try:
        os.makedirs(os.path.dirname(config_path()), exist_ok=True)
        with open(config_path(), "w", encoding="utf-8") as fh:
            json.dump(list(ids), fh)
    except OSError:
        pass


def last_selection():
    try:
        with open(config_path(), "r", encoding="utf-8") as fh:
            return list(json.load(fh))
    except (OSError, ValueError):
        return None


class App:
    def __init__(self, args):
        self.args = args
        self.io = TerminalIO(color=False if args.no_color else None)
        dirs = list(args.mod_dir or []) + default_mod_dirs()
        self.available, errors = discover(dirs)
        for e in errors:
            self.io.write(e, "warn")

    # ------------------------------------------------------------------
    def run(self):
        self.io.write(BANNER, "title")
        self.io.write("A text RPG woven entirely from mods.  v%s" % __version__, "dim")
        while True:
            self.io.write("")
            self.io.write("1) New game   2) Load game   3) Browse mods   4) Quit", "bold")
            try:
                ans = self.io.ask("menu> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                self.io.write("")
                return 0
            if ans in ("1", "n", "new"):
                world = self.new_game()
                if world is not None:
                    self.play(world, fresh=True)
            elif ans in ("2", "l", "load"):
                world = self.pick_save()
                if world is not None:
                    self.play(world, fresh=False)
            elif ans in ("3", "b", "browse", "mods"):
                self.browse()
            elif ans in ("4", "q", "quit", "exit"):
                return 0

    # ------------------------------------------------------------------
    def sorted_mods(self):
        return sorted(self.available.values(), key=lambda m: (m.priority, m.name.lower()))

    def browse(self):
        for m in self.sorted_mods():
            self.io.write("%s (%s) v%s%s" % (m.name, m.id, m.version, " by " + m.author if m.author else ""), "bold")
            if m.description:
                self.io.write("    " + m.description)
            extra = []
            if m.requires:
                extra.append("requires: " + ", ".join(m.requires))
            if m.recommends:
                extra.append("works well with: " + ", ".join(m.recommends))
            if m.conflicts:
                extra.append("conflicts: " + ", ".join(m.conflicts))
            if extra:
                self.io.write("    " + "; ".join(extra), "dim")

    def select_mods(self):
        mods = self.sorted_mods()
        if not mods:
            self.io.write("No mods found. Put mods in one of: %s" % ", ".join(default_mod_dirs()), "error")
            return None
        prev = last_selection()
        chosen = set(prev) if prev else {m.id for m in mods if m.default}
        chosen &= set(self.available)
        while True:
            self.io.write("")
            self.io.write("Choose the mods to weave your world from:", "title")
            width = max(len(m.name) for m in mods)
            room = max(10, textutil.term_width() - width - 12)
            for idx, m in enumerate(mods, 1):
                mark = "x" if m.id in chosen else " "
                desc = m.description.split(". ")[0]
                if len(desc) > room:
                    desc = desc[:room - 3].rstrip(" .,;(") + "..."
                self.io.write(" [%s] %2d  %-*s  %s" % (mark, idx, width, m.name, desc), raw=True)
            self.io.write("Toggle with numbers (\"2 5 6\"), 'a' all, 'n' none, 'i 3' for details, "
                          "Enter to continue, 'b' to go back.", "dim")
            try:
                ans = self.io.ask("mods> ").strip().lower()
            except EOFError:
                return None
            if ans == "":
                if not chosen:
                    self.io.write("Select at least one mod.", "warn")
                    continue
                ordered, added, problems = resolve_order(sorted(chosen), self.available)
                if problems:
                    for p in problems:
                        self.io.write(p, "error")
                    continue
                if added:
                    self.io.write("Also enabling required mods: %s" % ", ".join(added), "warn")
                recommended = sorted({r for m in ordered for r in m.recommends
                                      if r in self.available and r not in {o.id for o in ordered}})
                if recommended:
                    self.io.write("Tip: these mods work well with your selection: %s" % ", ".join(recommended), "dim")
                remember_selection([m.id for m in ordered])
                return ordered
            if ans == "b":
                return None
            if ans == "a":
                chosen = {m.id for m in mods}
                continue
            if ans == "n":
                chosen = set()
                continue
            if ans.startswith("i"):
                num = ans[1:].strip()
                if num.isdigit() and 1 <= int(num) <= len(mods):
                    m = mods[int(num) - 1]
                    self.io.write("%s (%s) v%s" % (m.name, m.id, m.version), "bold")
                    self.io.write(m.description or "(no description)")
                    for label, vals in (("Requires", m.requires), ("Works well with", m.recommends),
                                        ("Conflicts with", m.conflicts), ("Tags", m.tags)):
                        if vals:
                            self.io.write("%s: %s" % (label, ", ".join(vals)), "dim")
                continue
            for tok in ans.replace(",", " ").split():
                if tok.isdigit() and 1 <= int(tok) <= len(mods):
                    mid = mods[int(tok) - 1].id
                    chosen ^= {mid}
                elif tok in self.available:
                    chosen ^= {tok}

    def new_game(self):
        ordered = self.select_mods()
        if not ordered:
            return None
        try:
            reg = build_registry(ordered)
        except ModError as exc:
            self.io.write(str(exc), "error")
            return None
        if reg.warnings:
            self.io.write("%d mod warning(s); run with --validate to see them." % len(reg.warnings), "dim")
        start = None
        starts = start_choices(reg)
        if len(starts) > 1:
            idx = self.io.choose("Where do you begin? (Enter to let the story decide)",
                                 [label for _aid, label in starts])
            if idx is not None:
                start = starts[idx][0]
        sizes = ["small", "medium", "large", "huge"]
        idx = self.io.choose("How big a world? (Enter for medium)", [
            "Small - quick to cross", "Medium", "Large - more wilderness between places",
            "Huge - a long journey"])
        size = sizes[idx] if idx is not None else "medium"
        try:
            seed_text = self.io.ask("World seed (Enter for random): ").strip()
            fixed = start and (reg["areas"][start].get("player") or {}).get("player_name")
            name = "" if fixed else self.io.ask("Your character's name (Enter for a generated one): ").strip()
        except EOFError:
            return None
        seed = None
        if seed_text:
            # Words make seeds too; crc32 is stable across runs (hash() is not).
            seed = int(seed_text) if seed_text.isdigit() else zlib.crc32(seed_text.encode("utf-8")) % (2 ** 31)
        self.io.write("Weaving your world from %d mod(s)..." % len(ordered), "dim")
        try:
            world, log = generate(reg, seed=seed, player_name=name or None, size=size, start=start)
        except GenerationError as exc:
            self.io.write(str(exc), "error")
            return None
        self.io.write(log[-1] if log else "", "dim")
        return world

    def pick_save(self):
        saves = list_saves()
        if not saves:
            self.io.write("There are no saved games yet.")
            return None
        idx = self.io.choose("Load which game?", saves)
        if idx is None:
            return None
        try:
            return load_world(saves[idx])
        except (OSError, ValueError, KeyError) as exc:
            self.io.write("Could not load: %s" % exc, "error")
            return None

    # ------------------------------------------------------------------
    def play(self, world, fresh):
        io = self.io
        while True:
            engine = Engine(world, io)
            if fresh:
                io.write("")
                engine.start()
                io.write(engine.s("help_hint", "(Type 'help' for a list of commands.)"), "dim")
            else:
                io.write("Game loaded.", "good")
                engine.show("room", world.room, None)
            try:
                while not world.game_over:
                    try:
                        line = io.ask("\n> ")
                    except KeyboardInterrupt:
                        io.write("")
                        io.write("(Type 'quit' to leave the game.)", "dim")
                        continue
                    engine.handle(line)
            except LoadRequest as req:
                world, fresh = req.world, False
                continue
            except (QuitRequest, EOFError):
                io.write("")
                ans = "n"
                try:
                    ans = io.ask("Save before quitting? (y/N) ").strip().lower()
                except EOFError:
                    pass
                if ans.startswith("y"):
                    engine.save("quicksave")
                return
            # Game over
            io.write("")
            go = world.game_over
            io.write(go["text"], "good" if go.get("win") else "error")
            io.write("*** %s ***" % ("THE END" if go.get("win") else "GAME OVER"), "title")
            return


def start_choices(reg):
    """Starting areas that offer themselves as a choice (they have a start_label)."""
    out = []
    for aid, adef in sorted(reg["areas"].items()):
        if adef.get("abstract"):
            continue
        if adef.get("start_label"):
            out.append((aid, adef["start_label"]))
    return out


def run_script(args, ordered, reg):
    with open(args.script, "r", encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if not l.startswith("#")]
    io = ScriptIO(lines)
    world, _log = generate(reg, seed=args.seed, player_name=args.name, size=args.size, start=args.start)
    engine = Engine(world, io)
    engine.start()
    try:
        while not world.game_over:
            engine.handle(io.ask("\n> "))
    except (EOFError, QuitRequest):
        pass
    if world.game_over:
        io.write(world.game_over["text"])
    return 0


def print_map(world, log, out=sys.stdout):
    for line in log:
        print("# " + line, file=out)
    story = world.story
    print("Story: %s  [event: %s]" % (story.get("title"), story.get("event")), file=out)
    for role, uid in sorted(story.get("cast", {}).items()):
        e = world.get(uid)
        print("  cast %-10s %s" % (role, e.name if e else "?"), file=out)
    for st in story.get("steps", []):
        refs = ", ".join("%s=%s" % (k, world.get(v).name if world.get(v) else "?") for k, v in st.get("refs", {}).items())
        print("  step %-4s %-12s %-40s %s" % (st["id"], st["kind"], st["title"][:40], refs), file=out)
    print("  lore: %d entries" % len(story.get("lore", {})), file=out)
    for r in sorted(world.rooms(), key=lambda r: (r.stage, r.area or "~", r.uid)):
        where = r.area or ("~" + (r.region or r.props.get("path") or "?"))
        biomes = " {%s}" % ", ".join(r.props["biomes"]) if r.props.get("biomes") else ""
        print("[%d] %-22s %-30s%s" % (r.stage, where, r.name, biomes), file=out)
        for ex in r.exits:
            dest = world.get(ex["to"])
            gate = " (gated)" if ex.get("if") else ""
            via = " along %s" % ex["via"] if ex.get("via") else ""
            print("      %-10s -> %s [%s]%s%s" % (ex.get("dir") or ex.get("name") or "-", dest.name if dest else "?",
                                                  ex.get("distance", 1), via, gate), file=out)
        for e in world.descendants(r):
            depth = len(world.ancestors(e)) - len(world.ancestors(r))
            print("      %s%s%s" % ("  " * depth, e.name, " (hidden)" if e.hidden else ""), file=out)


def main(argv=None):
    p = argparse.ArgumentParser(prog="patchwork", description="A text RPG woven entirely from mods.")
    p.add_argument("--mods", help="comma separated mod ids: skip the menus and start a new game with these")
    p.add_argument("--seed", type=int, help="world seed")
    p.add_argument("--name", help="your character's name")
    p.add_argument("--start", help="starting area id (see --list-starts)")
    p.add_argument("--list-starts", action="store_true", help="list the starting points the selected mods offer, then exit")
    p.add_argument("--size", default="medium", choices=["small", "medium", "large", "huge"], help="world size")
    p.add_argument("--mod-dir", action="append", help="extra folder to look for mods in (repeatable)")
    p.add_argument("--list-mods", action="store_true", help="list available mods and exit")
    p.add_argument("--validate", action="store_true", help="check the selected mods (or all) for problems and exit")
    p.add_argument("--map", action="store_true", help="generate a world and print its layout, then exit")
    p.add_argument("--script", help="run commands from a file (non-interactive) and exit")
    p.add_argument("--no-color", action="store_true", help="disable coloured output")
    p.add_argument("--version", action="version", version="patchwork " + __version__)
    args = p.parse_args(argv)

    dirs = list(args.mod_dir or []) + default_mod_dirs()
    available, errors = discover(dirs)
    for e in errors:
        print("warning: " + e, file=sys.stderr)

    if args.list_mods:
        for m in sorted(available.values(), key=lambda m: (m.priority, m.id)):
            print("%-14s %-34s %s" % (m.id, m.name, m.description.split(". ")[0]))
        return 0

    if args.mods or args.validate or args.map or args.script or args.list_starts:
        ids = [m.strip() for m in (args.mods or "").split(",") if m.strip()] or sorted(available)
        ordered, added, problems = resolve_order(ids, available)
        if problems:
            for prob in problems:
                print("error: " + prob, file=sys.stderr)
            return 2
        if added:
            print("note: also loading required mods: %s" % ", ".join(added), file=sys.stderr)
        try:
            reg = build_registry(ordered)
        except ModError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        if args.list_starts:
            for aid, label in start_choices(reg):
                print("%-24s %s" % (aid, label))
            return 0
        if args.validate:
            problems = check_registry(reg) + smoke_generate(reg)
            notes = [p for p in problems if p.startswith("note: ")]
            warnings = [p for p in problems if not p.startswith("note: ")]
            for prob in notes:
                print(prob)
            for prob in warnings:
                print("warning: " + prob)
            print("%d mod(s) checked: %d warning(s), %d note(s)." % (len(ordered), len(warnings), len(notes)))
            return 1 if warnings else 0
        try:
            if args.map:
                world, log = generate(reg, seed=args.seed, player_name=args.name, size=args.size, start=args.start)
                print_map(world, log)
                return 0
            if args.script:
                return run_script(args, ordered, reg)
        except GenerationError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        app = App(args)
        try:
            world, _log = generate(reg, seed=args.seed, player_name=args.name, size=args.size, start=args.start)
        except GenerationError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        app.play(world, fresh=True)
        return 0

    return App(args).run()
