"""The data-driven logic layer: conditions, effects, templates and expressions.

Mods never contain code.  Instead they describe behaviour with small JSON
structures that this module interprets.  See MODDING.md for the reference.
"""

import ast
import operator
import re

from . import textutil
from .world import normalize_handlers


def _is_handler_list(v):
    return isinstance(v, list) and all(isinstance(x, dict) and "do" in x for x in v)


class StopAction(Exception):
    """Raised by the ``stop`` effect to cancel the rest of the current command."""


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class Ctx:
    def __init__(self, world, self_ent=None, target=None, second=None,
                 beat=None, local=None, args=""):
        self.world = world
        self.self_ent = self_ent
        self.target = target
        self.second = second
        self.beat = beat          # index into world.story["beats"] or None
        self.local = dict(local or {})
        self.args = args

    def derive(self, **kw):
        c = Ctx(self.world, self.self_ent, self.target, self.second, self.beat, self.local, self.args)
        for k, v in kw.items():
            setattr(c, k, v)
        if "local" in kw:
            c.local = dict(self.local)
            c.local.update(kw["local"] or {})
        return c


_CMP = {
    "eq": operator.eq, "ne": operator.ne, "gt": operator.gt, "gte": operator.ge,
    "lt": operator.lt, "lte": operator.le,
    "in": lambda a, b: a in (b or []),
}


def _compare(value, spec):
    """Apply any comparison keys present in *spec* to *value*."""
    used = False
    for key, fn in _CMP.items():
        if key in spec:
            used = True
            other = spec[key]
            try:
                if not fn(value, other):
                    return False
            except TypeError:
                return False
    return True if used else bool(value)


class Interpreter:
    def cmp_spec(self, spec, ctx):
        """Render templated comparison values: {"eq": "{self.lock}"}."""
        if not any(isinstance(spec.get(k), str) and "{" in spec.get(k) for k in _CMP):
            return spec
        out = dict(spec)
        for k in _CMP:
            if isinstance(out.get(k), str) and "{" in out[k]:
                out[k] = self.render(out[k], ctx)
        return out

    def __init__(self, world, engine=None):
        self.world = world
        self.engine = engine
        world.logic = self

    def ctx(self, **kw):
        return Ctx(self.world, **kw)

    # ------------------------------------------------------------------
    # References and matchers
    # ------------------------------------------------------------------
    def role(self, name, ctx):
        story = self.world.story
        beats = story.get("beats", [])
        if "." in name:
            bid, rname = name.split(".", 1)
            for b in beats:
                if b["id"] == bid:
                    return self.world.get(b["roles"].get(rname))
            return None
        order = []
        if ctx is not None and ctx.beat is not None and ctx.beat < len(beats):
            order.append(beats[ctx.beat])
        cur = story.get("current", 0)
        if cur < len(beats):
            order.append(beats[cur])
        order.extend(beats)
        for b in order:
            uid = b["roles"].get(name)
            if uid:
                return self.world.get(uid)
        return None

    def ref(self, ref, ctx):
        """Resolve a reference string to an Entity (or None)."""
        w = self.world
        if ref is None or ref == "self":
            return ctx.self_ent
        if not isinstance(ref, str):
            return None
        if ref == "target":
            return ctx.target
        if ref == "second":
            return ctx.second
        if ref == "player":
            return w.player
        if ref == "room":
            return w.room
        if ref == "parent":
            return w.get(ctx.self_ent.parent) if ctx.self_ent else None
        if ref == "holder":
            ent = ctx.self_ent
            return w.room_of(ent) if ent else None
        if ref in ("it",) or ref.startswith("local:"):
            name = ref.split(":", 1)[1] if ":" in ref else ref
            val = ctx.local.get(name)
            return w.get(val) if isinstance(val, str) else None
        if ref.startswith("role:"):
            return self.role(ref[5:], ctx)
        if ref.startswith("uid:"):
            return w.get(ref[4:])
        if ref.startswith("here:"):
            room = w.room_of(ctx.self_ent) if ctx.self_ent is not None else w.room
            for e in w.visible_tree(room) if room else []:
                if self.match(e, ref[5:], ctx):
                    return e
            return None
        if ref.startswith("carried:"):
            for e in w.visible_tree(w.player):
                if self.match(e, ref[8:], ctx):
                    return e
            return None
        if ref.startswith("near:"):
            for e in w.scope():
                if self.match(e, ref[5:], ctx):
                    return e
            return None
        if ref.startswith("room:"):
            for e in w.rooms():
                if e.def_id == ref or e.uid == ref[5:]:
                    return e
            return None
        if ref.startswith("any:"):
            for e in w.entities.values():
                if self.match(e, ref[4:], ctx):
                    return e
            return None
        if ref in ctx.local and isinstance(ctx.local[ref], str):
            return w.get(ctx.local[ref])
        return w.get(ref)

    def match(self, ent, m, ctx=None):
        """Does entity *ent* match matcher *m*?"""
        if ent is None:
            return False
        if isinstance(m, list):
            return any(self.match(ent, x, ctx) for x in m)
        if isinstance(m, dict):
            if "tag" in m:
                tags = m["tag"] if isinstance(m["tag"], list) else [m["tag"]]
                if not all(t in ent.tags for t in tags):
                    return False
            if "def" in m and ent.def_id != m["def"] and ent.def_id != "room:" + str(m["def"]):
                return False
            if "role" in m:
                r = self.role(m["role"], ctx)
                if r is None or r.uid != ent.uid:
                    return False
            if "name" in m and m["name"].lower() not in ent.aliases:
                return False
            if "prop" in m:
                if not _compare(ent.props.get(m["prop"]), self.cmp_spec(m, ctx) if ctx else m):
                    return False
            if "not" in m and self.match(ent, m["not"], ctx):
                return False
            return True
        if not isinstance(m, str):
            return False
        if ":" in m:
            kind, val = m.split(":", 1)
            if kind == "tag":
                return val in ent.tags
            if kind == "def":
                return ent.def_id in (val, "room:" + val)
            if kind == "role":
                r = self.role(val, ctx)
                return r is not None and r.uid == ent.uid
            if kind == "uid":
                return ent.uid == val
            if kind == "name":
                return val.lower() in ent.aliases
            if kind == "area":
                return ent.area == val or (self.world.room_of(ent) or ent).area == val
            if kind == "room":
                return ent.def_id == m
        return ent.def_id == m or ent.def_id == "room:" + m or m in ent.tags

    def find_in(self, container, m, ctx, visible=True):
        if container is None:
            return []
        pool = self.world.visible_tree(container) if visible else self.world.descendants(container)
        return [e for e in pool if self.match(e, m, ctx)]

    # ------------------------------------------------------------------
    # Values and expressions
    # ------------------------------------------------------------------
    def value(self, v, ctx):
        if isinstance(v, str):
            if v.startswith("="):
                return self.expr(v[1:], ctx)
            return self.render(v, ctx)
        if isinstance(v, dict) and set(v) == {"rand"}:
            lo, hi = v["rand"]
            return self.world.rng.randint(int(lo), int(hi))
        return v

    def expr(self, src, ctx):
        try:
            tree = ast.parse(src.strip(), mode="eval")
        except SyntaxError:
            self.world.say("[mod error] bad expression: %s" % src, "error")
            return 0
        try:
            return _Eval(self, ctx).visit(tree.body)
        except Exception as exc:  # mods must never crash the game
            self.world.say("[mod error] %s in expression: %s" % (exc, src), "error")
            return 0

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------
    _PLACEHOLDER = re.compile(r"\{([^{}]+)\}")

    def render(self, text, ctx):
        if text is None:
            return ""
        if not isinstance(text, str):
            return str(text)
        if "#" in text or "[" in text:
            text = self.world.grammar.expand(text)
        for _ in range(3):  # a substituted value (e.g. a prop) may itself contain placeholders
            if "{" not in text:
                break
            new = self._PLACEHOLDER.sub(lambda m: self._placeholder(m.group(1), ctx, m.group(0)), text)
            if new == text:
                break
            text = new
        return text

    def _entity_attr(self, ent, attr):
        if attr is None:
            return ent.the()
        table = {
            "name": ent.name, "Name": textutil.cap(ent.name),
            "a": ent.a(), "A": textutil.cap(ent.a()),
            "the": ent.the(), "The": textutil.cap(ent.the()),
        }
        if attr in table:
            return table[attr]
        if attr == "area" and self.world.room_of(ent):
            area = self.world.areas.get(self.world.room_of(ent).area or "")
            return area["name"] if area else self.world.room_of(ent).name
        if attr == "room":
            r = self.world.room_of(ent)
            return r.name if r else ""
        if attr == "contents":
            kids = self.world.visible_children(ent)
            return textutil.join_list(textutil.group_names(kids)) if kids else self.world.string("nothing", "nothing")
        val = ent.props.get(attr)
        return "" if val is None else val

    def _placeholder(self, body, ctx, original):
        body = body.strip()
        if body.startswith("="):
            val = self.expr(body[1:], ctx)
            if isinstance(val, float) and val.is_integer():
                val = int(val)
            return str(val)
        if body.startswith("#"):
            return original
        parts = body.split(".")
        root = parts[0]
        w = self.world
        if root in ("self", "target", "second", "player", "room", "it", "parent") or root in ctx.local and isinstance(ctx.local.get(root), str) and w.get(ctx.local.get(root)):
            ent = self.ref(root, ctx) if root not in ctx.local else w.get(ctx.local[root])
            if ent is None:
                return original if root in ("target", "second") else ""
            return str(self._entity_attr(ent, parts[1] if len(parts) > 1 else None))
        if root == "role" and len(parts) >= 2:
            ent = self.role(parts[1], ctx)
            if ent is None:
                return "someone"
            return str(self._entity_attr(ent, parts[2] if len(parts) > 2 else None))
        if root in ("beat", "next", "prev"):
            return str(self._beat_attr(root, parts[1:], ctx))
        if root == "var" and len(parts) == 2:
            return str(w.vars.get(parts[1], 0))
        if root == "clock":
            return str(w.clock)
        if root == "args":
            return ctx.args
        if root == "story":
            return w.story.get("title", "")
        if root == "string" and len(parts) == 2:
            return self.render(w.string(parts[1]), ctx)
        if root in ctx.local:
            return str(ctx.local[root])
        return original

    def beat_index(self, which, ctx):
        cur = ctx.beat if ctx.beat is not None else self.world.story.get("current", 0)
        if which == "next":
            cur += 1
        elif which == "prev":
            cur -= 1
        return cur

    def _beat_attr(self, which, parts, ctx):
        beats = self.world.story.get("beats", [])
        idx = self.beat_index(which, ctx)
        if idx < 0 or idx >= len(beats):
            return ""
        b = beats[idx]
        attr = parts[0] if parts else "title"
        if attr == "title":
            return b.get("title", "")
        if attr == "area":
            area = self.world.areas.get(b.get("area") or "")
            return area["name"] if area else "parts unknown"
        if attr in b["roles"]:
            ent = self.world.get(b["roles"][attr])
            if ent is None:
                return "something"
            return self._entity_attr(ent, parts[1] if len(parts) > 1 else None)
        if attr == "id":
            return b["id"]
        bdef = self.world.registry["beats"].get(b["id"], {})
        val = bdef.get(attr)
        if isinstance(val, list) and val:
            val = val[0]
        if val is None:
            val = self.world.string("default_" + attr) or None
        if isinstance(val, str):
            return self.render(val, ctx.derive(beat=idx))
        return ""

    # ------------------------------------------------------------------
    # Conditions
    # ------------------------------------------------------------------
    def check(self, cond, ctx):
        if cond is None:
            return True
        if isinstance(cond, bool):
            return cond
        if isinstance(cond, str):
            return bool(self.expr(cond, ctx))
        if isinstance(cond, list):
            return all(self.check(c, ctx) for c in cond)
        if not isinstance(cond, dict):
            return bool(cond)
        w = self.world
        for key, val in cond.items():
            if key in _CMP or key in ("of", "who", "in"):
                continue
            ok = self._check_one(key, val, cond, ctx, w)
            if not ok:
                return False
        return True

    def _check_one(self, key, val, cond, ctx, w):
        if key == "all":
            return all(self.check(c, ctx) for c in val)
        if key == "any":
            return any(self.check(c, ctx) for c in val)
        if key == "not":
            return not self.check(val, ctx)
        if key == "flag":
            flags = val if isinstance(val, list) else [val]
            return all(self.render(f, ctx) in w.flags for f in flags)
        if key == "var":
            return _compare(w.vars.get(val, 0), self.cmp_spec(cond, ctx))
        if key == "prop":
            ent = self.ref(cond.get("of", "self"), ctx)
            return ent is not None and _compare(ent.props.get(val), self.cmp_spec(cond, ctx))
        if key == "has":
            who = self.ref(cond.get("who", "player"), ctx)
            return bool(self.find_in(who, val, ctx, visible=False))
        if key == "here":
            room = w.room
            return bool(room and self.find_in(room, val, ctx))
        if key == "near":
            return any(self.match(e, val, ctx) for e in w.scope())
        if key == "in_room":
            ent = self.ref(cond.get("of", "player"), ctx)
            return self.match(w.room_of(ent), val, ctx)
        if key == "inside":
            ent = self.ref(cond.get("of", "self"), ctx)
            return ent is not None and any(self.match(a, val, ctx) for a in w.ancestors(ent))
        if key == "held":
            ent = self.ref(val, ctx)
            return ent is not None and w.is_inside(ent, w.player)
        if key == "tag":
            ent = self.ref(cond.get("of", "self"), ctx)
            tags = val if isinstance(val, list) else [val]
            return ent is not None and all(t in ent.tags for t in tags)
        if key == "is":
            ent = self.ref(cond.get("of", "target"), ctx)
            return self.match(ent, val, ctx)
        if key == "same":
            a = self.ref(val[0], ctx)
            b = self.ref(val[1], ctx)
            return a is not None and b is not None and a.uid == b.uid
        if key == "exists":
            return self.ref(val, ctx) is not None
        if key == "chance":
            return w.rng.random() < float(val)
        if key == "clock":
            return _compare(w.clock, val if isinstance(val, dict) else {"gte": val})
        if key == "turns":
            return _compare(w.turns, val if isinstance(val, dict) else {"gte": val})
        if key == "visited":
            return any(r.visited and self.match(r, val, ctx) for r in w.rooms())
        if key == "mod":
            ids = {m["id"] for m in w.registry.mods}
            vals = val if isinstance(val, list) else [val]
            return all(v in ids for v in vals)
        if key in ("beat_done", "beat_active", "beat_reached"):
            beats = w.story.get("beats", [])
            cur = w.story.get("current", 0)
            idx = None
            for i, b in enumerate(beats):
                if b["id"] == val or i == val:
                    idx = i
            if idx is None:
                return key == "beat_reached"  # unknown/unused beat: treat as open
            if key == "beat_done":
                return beats[idx].get("state") == "done"
            if key == "beat_active":
                return idx == cur and beats[idx].get("state") == "active"
            return cur >= idx or w.story.get("complete")
        if key == "next_beat":
            beats = w.story.get("beats", [])
            nxt = (ctx.beat if ctx.beat is not None else w.story.get("current", 0)) + 1
            return (nxt < len(beats)) == bool(val)
        if key == "story_complete":
            return bool(w.story.get("complete")) == bool(val)
        if key == "expr":
            return bool(self.expr(val, ctx))
        if key == "local":
            return _compare(ctx.local.get(val), cond)
        if key == "args":
            return _compare(ctx.args, cond) if any(k in cond for k in _CMP) else ctx.args == val
        if key == "target":
            return self.match(ctx.target, val, ctx)
        if key == "second":
            if val is None:
                return ctx.second is None
            return self.match(ctx.second, val, ctx)
        w.say("[mod error] unknown condition '%s'" % key, "error")
        return False

    # ------------------------------------------------------------------
    # Effects
    # ------------------------------------------------------------------
    def run(self, effects, ctx):
        if effects is None:
            return
        if not isinstance(effects, list):
            effects = [effects]
        for eff in effects:
            if self.world.game_over and not (isinstance(eff, dict) and "end_game" in eff):
                return
            self.run_one(eff, ctx)

    def run_handlers(self, handlers, ctx):
        """Run the first handler whose condition passes.  Returns True if one ran."""
        for h in normalize_handlers(handlers) if not _is_handler_list(handlers) else handlers:
            if self.check(h.get("if"), ctx):
                self.run(h.get("do"), ctx)
                return True
            if "else" in h:
                self.run(h["else"], ctx)
                return True
        return False

    def run_one(self, eff, ctx):
        w = self.world
        if isinstance(eff, str):
            w.say(self.render(eff, ctx))
            return
        if isinstance(eff, list):
            self.run(eff, ctx)
            return
        if not isinstance(eff, dict):
            return
        on = eff.get("on")

        if "say" in eff:
            w.say(self.render(eff["say"], ctx), eff.get("style"))
        elif "if" in eff and ("then" in eff or "else" in eff or "do" in eff):
            if self.check(eff["if"], ctx):
                self.run(eff.get("then", eff.get("do")), ctx)
            else:
                self.run(eff.get("else"), ctx)
        elif "random" in eff:
            options = eff["random"]
            weights = []
            for o in options:
                weights.append(o.get("weight", 1) if isinstance(o, dict) else 1)
            pick = w.rng.choices(options, weights=weights)[0]
            self.run(pick.get("do") if isinstance(pick, dict) and "do" in pick else pick, ctx)
        elif "set" in eff:
            ent = self.ref(on or "self", ctx)
            if ent is not None:
                for k, v in eff["set"].items():
                    ent.props[k] = self.value(v, ctx)
        elif "add" in eff:
            ent = self.ref(on or "self", ctx)
            if ent is not None:
                for k, v in eff["add"].items():
                    ent.props[k] = (ent.props.get(k) or 0) + self.value(v, ctx)
        elif "toggle" in eff:
            ent = self.ref(on or "self", ctx)
            if ent is not None:
                ent.props[eff["toggle"]] = not ent.props.get(eff["toggle"])
        elif "set_var" in eff:
            for k, v in eff["set_var"].items():
                w.vars[k] = self.value(v, ctx)
        elif "add_var" in eff:
            for k, v in eff["add_var"].items():
                w.vars[k] = (w.vars.get(k) or 0) + self.value(v, ctx)
        elif "flag" in eff:
            for f in eff["flag"] if isinstance(eff["flag"], list) else [eff["flag"]]:
                w.flags.add(self.render(f, ctx))
        elif "unflag" in eff:
            for f in eff["unflag"] if isinstance(eff["unflag"], list) else [eff["unflag"]]:
                w.flags.discard(self.render(f, ctx))
        elif "let" in eff:
            for k, v in eff["let"].items():
                ctx.local[k] = self.value(v, ctx)
        elif "move" in eff:
            ent = self.ref(eff["move"], ctx)
            dest = self.ref(eff.get("to", "room"), ctx)
            if ent is not None and dest is not None and ent.uid != dest.uid and not w.is_inside(dest, ent):
                w.place(ent, dest)
        elif "spawn" in eff:
            dest = self.ref(eff.get("in", "room"), ctx)
            if dest is not None:
                made = w.spawn_spec(eff["spawn"], dest, ctx)
                if made and eff.get("as"):
                    ctx.local[eff["as"]] = made[0].uid
        elif "destroy" in eff:
            ent = self.ref(eff["destroy"], ctx)
            if ent is not None and ent.uid != w.player_uid and not ent.is_room:
                if ctx.target is not None and ctx.target.uid == ent.uid:
                    ctx.local["_destroyed_target"] = ent.name
                w.destroy(ent)
        elif "reveal" in eff:
            ent = self.ref(eff["reveal"], ctx)
            if ent is not None:
                if eff.get("children"):
                    found = [w.get(c) for c in ent.children if w.get(c) and w.get(c).hidden]
                    for c in found:
                        c.hidden = False
                    ctx.local["revealed"] = len(found)
                    ctx.local["revealed_list"] = textutil.join_list([c.a() for c in found])
                else:
                    ent.hidden = False
        elif "hide" in eff:
            ent = self.ref(eff["hide"], ctx)
            if ent is not None:
                ent.hidden = True
        elif "rename" in eff:
            ent = self.ref(on or "self", ctx)
            if ent is not None:
                ent.name = self.render(eff["rename"], ctx)
                w.refresh_aliases(ent)
        elif "set_text" in eff:
            ent = self.ref(on or "self", ctx)
            if ent is not None:
                for k, v in eff["set_text"].items():
                    ent.texts[k] = v
        elif "tag" in eff:
            ent = self.ref(on or "self", ctx)
            if ent is not None:
                for t in eff["tag"] if isinstance(eff["tag"], list) else [eff["tag"]]:
                    if t not in ent.tags:
                        ent.tags.append(t)
        elif "untag" in eff:
            ent = self.ref(on or "self", ctx)
            if ent is not None:
                for t in eff["untag"] if isinstance(eff["untag"], list) else [eff["untag"]]:
                    if t in ent.tags:
                        ent.tags.remove(t)
        elif "teleport" in eff:
            dest = self.ref(eff["teleport"], ctx)
            if dest is None:
                for r in w.rooms():
                    if self.match(r, eff["teleport"], ctx):
                        dest = r
                        break
            if dest is not None:
                dest = dest if dest.is_room else w.room_of(dest)
                self.engine.enter_room(dest, describe=eff.get("describe", True))
        elif "travel" in eff:
            self.engine.travel(self.render(eff["travel"], ctx))
        elif "exit" in eff:
            self._modify_exit(eff["exit"], ctx)
        elif "connect" in eff:
            spec = eff["connect"]
            a = self.ref(spec.get("from", "room"), ctx)
            b = self.ref(spec["to"], ctx)
            if b is None:
                b = next((r for r in w.rooms() if self.match(r, spec["to"], ctx)), None)
            if a is not None and b is not None:
                if not any(x["to"] == b.uid and x.get("dir") == spec.get("dir") for x in a.exits):
                    w.add_exit(a, b, spec.get("dir"), spec.get("distance", 1),
                               name=spec.get("name"), description=spec.get("description"))
                if spec.get("back") is not False and not spec.get("oneway"):
                    back = spec.get("back") or self.engine.opposite(spec.get("dir"))
                    if not any(x["to"] == a.uid for x in b.exits):
                        w.add_exit(b, a, back, spec.get("distance", 1))
        elif "journal" in eff:
            text = self.render(eff["journal"], ctx)
            w.journal.append({"time": w.clock, "text": text})
            if eff.get("quiet") is not True:
                w.say(self.render(w.string("journal_updated", "(Your journal has been updated.)"), ctx), "dim")
        elif "show" in eff:
            self.engine.show(eff["show"], self.ref(eff.get("of", "target"), ctx), ctx)
        elif "describe" in eff:
            ent = self.ref(eff["describe"], ctx)
            if ent is not None:
                self.engine.show("room" if ent.is_room else "entity", ent, ctx)
        elif "choice" in eff:
            self._choice(eff["choice"], ctx)
        elif "end_game" in eff:
            w.game_over = {"text": self.render(eff["end_game"], ctx), "win": bool(eff.get("win"))}
        elif "advance" in eff:
            w.clock += int(self.value(eff["advance"], ctx) or 0)
        elif "macro" in eff:
            macro = w.registry["macros"].get(eff["macro"])
            if macro is None:
                w.say("[mod error] unknown macro '%s'" % eff["macro"], "error")
            else:
                sub = ctx.derive(local={k: self.value(v, ctx) for k, v in (eff.get("with") or {}).items()})
                body = macro.get("do") if isinstance(macro, dict) else macro
                self.run(body, sub)
                ctx.local.update({k: v for k, v in sub.local.items() if k.startswith("out_")})
        elif "emit" in eff:
            self.fire(eff["emit"], ctx)
        elif "hook" in eff:
            ent = self.ref(on or "self", ctx)
            if ent is not None:
                sub = ctx.derive(self_ent=ent, target=ctx.self_ent if on else ctx.target)
                self.run(w.hook(ent, eff["hook"]), sub)
        elif "find" in eff:
            container = self.ref(eff.get("in", "player"), ctx)
            found = self.find_in(container, eff["find"], ctx, visible=not eff.get("hidden_too"))
            if found:
                ctx.local[eff.get("as", "found")] = found[0].uid
            else:
                ctx.local.pop(eff.get("as", "found"), None)
        elif "for_each" in eff:
            container = self.ref(eff.get("in", "room"), ctx)
            items = self.find_in(container, eff["for_each"], ctx, visible=not eff.get("hidden_too"))
            if eff.get("direct"):
                items = [i for i in items if i.parent == container.uid]
            for item in items:
                if item.uid in w.entities:
                    self.run(eff.get("do"), ctx.derive(local={"it": item.uid}))
        elif "complete_beat" in eff:
            self.engine.complete_beat(eff["complete_beat"])
        elif "lead" in eff:
            self.engine.show_lead(ctx)
        elif "interrupt" in eff:
            w.interrupt = bool(eff["interrupt"])
        elif "stop" in eff:
            raise StopAction()
        elif "nothing" in eff:
            pass
        else:
            w.say("[mod error] unknown effect: %s" % ", ".join(eff.keys()), "error")

    def _modify_exit(self, spec, ctx):
        room = self.ref(spec.get("room", "room"), ctx)
        if room is None:
            return
        for ex in room.exits:
            if "dir" in spec and ex.get("dir") != spec["dir"]:
                continue
            if "to" in spec:
                dest = self.world.get(ex["to"])
                if not self.match(dest, spec["to"], ctx):
                    continue
            if "name" in spec and ex.get("name") != spec["name"]:
                continue
            for k, v in (spec.get("set") or {}).items():
                if v is None:
                    ex.pop(k, None)
                else:
                    ex[k] = v

    def _choice(self, spec, ctx):
        options = [o for o in spec.get("options", []) if self.check(o.get("if"), ctx)]
        if not options:
            return
        prompt = self.render(spec.get("prompt", ""), ctx)
        labels = [self.render(o.get("text", "..."), ctx) for o in options]
        idx = self.world.io.choose(prompt, labels)
        if idx is None or idx < 0 or idx >= len(options):
            if spec.get("cancel"):
                self.world.say(self.render(spec["cancel"], ctx))
            return
        self.run(options[idx].get("do"), ctx)

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------
    def fire(self, event, ctx):
        """Run every rule listening for *event*."""
        rules = self.world.registry["rules"]
        ordered = sorted(rules.items(), key=lambda kv: (kv[1].get("priority", 50), kv[0]))
        for rid, rule in ordered:
            on = rule.get("on")
            events = on if isinstance(on, list) else [on]
            if event not in events:
                continue
            if rule.get("once") and rid in self.world.fired:
                continue
            if not self.check(rule.get("if"), ctx):
                continue
            if rule.get("once"):
                self.world.fired.add(rid)
            self.run(rule.get("do"), ctx.derive())
            if self.world.game_over:
                return


# ---------------------------------------------------------------------------
# Safe expression evaluator
# ---------------------------------------------------------------------------

class _EntityView:
    def __init__(self, interp, ent):
        self._i = interp
        self._e = ent

    def get(self, name):
        if name == "name":
            return self._e.name
        if name == "uid":
            return self._e.uid
        val = self._e.props.get(name)
        return 0 if val is None else val


class _VarsView:
    def __init__(self, world):
        self._w = world

    def get(self, name):
        return self._w.vars.get(name, 0)


class _RoleView:
    def __init__(self, interp, ctx):
        self._i = interp
        self._c = ctx

    def get(self, name):
        ent = self._i.role(name, self._c)
        return _EntityView(self._i, ent) if ent else None


_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
}
_CMPOPS = {
    ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le,
    ast.Gt: operator.gt, ast.GtE: operator.ge,
}


class _Eval(ast.NodeVisitor):
    def __init__(self, interp, ctx):
        self.i = interp
        self.c = ctx

    def generic_visit(self, node):
        raise ValueError("unsupported syntax '%s'" % type(node).__name__)

    def visit_Constant(self, node):
        return node.value

    def visit_Name(self, node):
        n = node.id
        if n in ("true", "True"):
            return True
        if n in ("false", "False"):
            return False
        if n in ("none", "None"):
            return None
        if n in ("self", "target", "second", "player", "room", "it", "parent"):
            ent = self.i.ref(n, self.c)
            return _EntityView(self.i, ent) if ent else None
        if n == "var":
            return _VarsView(self.i.world)
        if n == "role":
            return _RoleView(self.i, self.c)
        if n == "clock":
            return self.i.world.clock
        if n == "turns":
            return self.i.world.turns
        if n in self.c.local:
            val = self.c.local[n]
            if isinstance(val, str) and self.i.world.get(val):
                return _EntityView(self.i, self.i.world.get(val))
            return val
        return 0

    def visit_Attribute(self, node):
        base = self.visit(node.value)
        if base is None:
            return 0
        if hasattr(base, "get"):
            return base.get(node.attr)
        raise ValueError("cannot read '%s'" % node.attr)

    def visit_BinOp(self, node):
        op = _BINOPS.get(type(node.op))
        if op is None:
            raise ValueError("unsupported operator")
        return op(self.visit(node.left), self.visit(node.right))

    def visit_UnaryOp(self, node):
        val = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -val
        if isinstance(node.op, ast.UAdd):
            return +val
        if isinstance(node.op, ast.Not):
            return not val
        raise ValueError("unsupported unary operator")

    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            result = True
            for v in node.values:
                result = self.visit(v)
                if not result:
                    return result
            return result
        result = False
        for v in node.values:
            result = self.visit(v)
            if result:
                return result
        return result

    def visit_Compare(self, node):
        left = self.visit(node.left)
        for op, comp in zip(node.ops, node.comparators):
            right = self.visit(comp)
            fn = _CMPOPS.get(type(op))
            if fn is None:
                raise ValueError("unsupported comparison")
            if not fn(left, right):
                return False
            left = right
        return True

    def visit_IfExp(self, node):
        return self.visit(node.body) if self.visit(node.test) else self.visit(node.orelse)

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ValueError("only simple function calls are allowed")
        name = node.func.id
        args = [self.visit(a) for a in node.args]
        w = self.i.world
        if name == "min":
            return min(args)
        if name == "max":
            return max(args)
        if name == "abs":
            return abs(args[0])
        if name == "int":
            return int(args[0])
        if name == "round":
            return round(*args)
        if name == "rand":
            return w.rng.randint(int(args[0]), int(args[1]))
        if name == "chance":
            return w.rng.random() < float(args[0])
        if name in ("best", "total", "count", "has"):
            view = args[0]
            if not isinstance(view, _EntityView):
                return 0
            items = [e for e in w.descendants(view._e)]
            if name == "best":
                vals = [e.props.get(args[1]) for e in items if isinstance(e.props.get(args[1]), (int, float))]
                return max(vals) if vals else 0
            if name == "total":
                return sum(e.props.get(args[1]) or 0 for e in items
                           if isinstance(e.props.get(args[1]), (int, float)))
            found = [e for e in items if self.i.match(e, args[1], self.c)]
            return len(found) if name == "count" else bool(found)
        raise ValueError("unknown function '%s'" % name)
