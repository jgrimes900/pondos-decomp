"""Build prose for rooms and features out of the features nested inside them.

A room's description is its own text followed by the "appearance" line of
every visible feature in it.  Features that hold other features (a table with
things on it, an open chest) add a "contents" sentence via their
``contents_text`` template, recursively.  Examining a feature shows its own
description plus the appearance of everything nested in it.
"""

from . import consumables, textutil


class Describer:
    def __init__(self, world, interp):
        self.w = world
        self.i = interp

    def text(self, ent, key, ctx=None):
        """Render an entity text which may be a string or a list of conditional variants."""
        val = ent.texts.get(key)
        if val is None:
            val = self.w.def_of(ent).get(key)
        if val is None or val is False:
            return None
        ctx = ctx or self.i.ctx(self_ent=ent)
        if isinstance(val, list):
            for variant in val:
                if isinstance(variant, dict):
                    if self.i.check(variant.get("if"), ctx):
                        return self.i.render(variant.get("text", ""), ctx)
                else:
                    return self.i.render(variant, ctx)
            return None
        return self.i.render(val, ctx)

    def has_text(self, ent, key):
        if key in ent.texts:
            return ent.texts[key] is not None and ent.texts[key] is not False
        val = self.w.def_of(ent).get(key)
        return val is not None and val is not False

    # ------------------------------------------------------------------
    def contents_sentence(self, ent, depth):
        """'On the table you see a cup and a knife.' for features that show contents."""
        if depth > 3 or not self.has_text(ent, "contents_text"):
            return []
        kids = self.w.visible_children(ent)
        if not kids:
            empty = self.text(ent, "empty_text")
            return [empty] if empty else []
        listed = [k for k in kids if self.text(k, "appearance") is None]
        lines = []
        if listed:
            ctx = self.i.ctx(self_ent=ent, local={"contents": textutil.join_list(textutil.group_names(listed))})
            line = self.text(ent, "contents_text", ctx)
            if line:
                lines.append(line)
        for k in kids:
            if k in listed:
                lines.extend(self.contents_sentence(k, depth + 1))
            else:
                lines.extend(self.appearance_lines(k, depth + 1))
        return lines

    def appearance_lines(self, ent, depth=0):
        lines = []
        app = self.text(ent, "appearance")
        if app:
            lines.append(app)
        lines.extend(self.contents_sentence(ent, depth))
        return lines

    def _paragraph(self, lines):
        lines = [textutil.cap(l.strip()) for l in lines if l and l.strip()]
        return textutil.tidy(" ".join(lines))

    # ------------------------------------------------------------------
    def room(self, room, brief=False):
        """Return a list of (text, style) pieces describing *room*."""
        out = [(room.name, "room")]
        body = []
        if brief and self.has_text(room, "brief"):
            body.append(self.text(room, "brief"))
        else:
            desc = self.text(room, "description")
            if desc:
                body.append(desc)
        loose = []
        for child in self.w.visible_children(room):
            app = self.text(child, "appearance")
            if self.w.def_of(child).get("appearance") is False or child.texts.get("appearance") is False:
                body.extend(self.contents_sentence(child, 1))
                continue
            if app:
                body.append(app)
                body.extend(self.contents_sentence(child, 1))
            else:
                loose.append(child)
                body.extend(self.contents_sentence(child, 1))
        if loose:
            ctx = self.i.ctx(self_ent=room, local={"contents": textutil.join_list(textutil.group_names(loose))})
            body.append(self.i.render(self.w.string("also_here", "You also see {contents}."), ctx))
        para = self._paragraph(body)
        if para:
            out.append((para, None))
        exits = self.exits_line(room)
        if exits:
            out.append((exits, "exit"))
        return out

    def exit_label(self, room, ex):
        dest = self.w.get(ex["to"])
        dirdef = self.w.registry["directions"].get(ex.get("dir") or "", {})
        label = ex.get("name") or dirdef.get("name") or ex.get("dir")
        known = dest is not None and (dest.visited or ex.get("show_dest"))
        dest_name = dest.name if known else None
        if ex.get("via") and label:
            # Following a path: "north along the Old Fox Way".
            label = self.i.render(self.w.string("exit_via", "{dir} along {via}"),
                                  self.i.ctx(local={"dir": label, "via": ex["via"]}))
        ctx = self.i.ctx(self_ent=room, local={
            "dir": label or (dest.name if dest else "?"),
            "dest": dest_name or self.w.string("unknown_dest", "unexplored"),
            "distance": ex.get("distance", 1),
        })
        if label:
            key = "exit_format" if known else "exit_format_unknown"
            return self.i.render(self.w.string(key, "{dir} ({dest}, {distance})"), ctx)
        return self.i.render(self.w.string("exit_format_named", "to {dest} ({distance})"),
                             ctx.derive(local={"dest": dest.name if dest else "?"}))

    def visible_exits(self, room):
        ctx = self.i.ctx(self_ent=room)
        return [ex for ex in room.exits
                if not ex.get("hidden") and self.i.check(ex.get("visible_if"), ctx)]

    def exits_line(self, room):
        exits = self.visible_exits(room)
        if not exits:
            return self.w.string("no_exits", "There is no obvious way out.")
        labels = [self.exit_label(room, ex) for ex in exits]
        ctx = self.i.ctx(self_ent=room, local={"exits": textutil.join_list(labels, "and")})
        text = self.i.render(self.w.string("exits_line", "Exits: {exits}."), ctx)
        notes = []
        for ex in exits:
            if ex.get("description"):
                notes.append(self.i.render(ex["description"], self.i.ctx(self_ent=room)))
        if notes:
            text = self._paragraph(notes) + "\n" + text
        return text

    # ------------------------------------------------------------------
    def entity(self, ent):
        """Examine text for a feature."""
        lines = []
        desc = self.text(ent, "description")
        if desc is None:
            desc = self.i.render(self.w.string("nothing_special", "You see nothing special about {self}."),
                                 self.i.ctx(self_ent=ent))
        lines.append(desc)
        gauge = self.gauge(ent)
        if gauge:
            lines.append(self.i.render(self.w.string("consumer_examine", "({gauge})"),
                                       self.i.ctx(self_ent=ent, local={"gauge": gauge})))
        kids = self.w.visible_children(ent)
        if self.has_text(ent, "contents_text"):
            lines.extend(self.contents_sentence(ent, 0))
        elif kids:
            for k in kids:
                lines.extend(self.appearance_lines(k, 1) or [
                    self.i.render(self.w.string("part_of", "There is {self.a} on {parent}."),
                                  self.i.ctx(self_ent=k, local={"parent": ent.uid}))])
        return self._paragraph(lines)

    def gauge(self, ent):
        """How much a consumer has left ("12/17 rounds"), or a supply holds ("34 9mm ammo")."""
        p = ent.props
        if consumables.is_consumer(ent):
            if consumables.capacity(ent):
                return "%s/%s %s" % (consumables.stored(ent), consumables.capacity(ent), consumables.label(ent))
            return "%s %s to draw on" % (consumables.available(self.w, ent), consumables.label(ent)) if ent.uid in \
                {e.uid for e in self.w.descendants(self.w.player)} else ""
        if "supply" in ent.tags:
            skip = {"default_max_health", "value", "weight", "armor", "damage", "heal", "health", "max_health"}
            for k, v in sorted(p.items()):
                if k not in skip and isinstance(v, (int, float)) and not isinstance(v, bool):
                    kind = p.get(k + "_type")
                    return "%s %s%s" % (v, kind + " " if kind else "", k)
        return ""

    def inventory(self, holder):
        items = self.w.visible_children(holder)
        if not items:
            return self.i.render(self.w.string("inventory_empty", "You are carrying nothing."),
                                 self.i.ctx(self_ent=holder))
        parts = []
        for it in items:
            label = it.a()
            inner = self.w.visible_children(it)
            gauge = self.gauge(it)
            if gauge:
                label += " (" + gauge + ")"
            if inner:
                label += " (" + self.i.render(self.w.string("inventory_holding", "holding {contents}"),
                                              self.i.ctx(local={"contents": textutil.join_list(textutil.group_names(inner))})) + ")"
            parts.append(label)
        ctx = self.i.ctx(self_ent=holder, local={"contents": textutil.join_list(parts)})
        return self.i.render(self.w.string("inventory", "You are carrying {contents}."), ctx)
