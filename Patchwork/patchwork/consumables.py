"""Things that spend a resource when used: guns and ammunition, grenades, spells and mana,
blades that wear down and whetstones that restore them.

Everything is driven by props on the item (a mod gives them through the core `consumer` trait):

    resource       the prop its supplies carry: "ammo", "mana", "repair", "oil"...
    resource_type  optional; a supply must have <resource>_type equal to it ("9mm")
    cost           how much one use takes (default 1)
    capacity       internal storage (a magazine, charges, durability); 0 = none
    stored         how much is in it now (starts full)
    feed           "internal": only what is stored; reload by hand
                   "auto":     stored, and refills itself from carried supplies when it runs dry
                   "direct":   no storage; every use draws straight from supplies (a spell from mana)
    reloadable     false: what it holds is all it will ever have (a grenade, a scroll)
    on_empty       "keep" (default), "consume" (gone when used up) or "transmute" (becomes empty_into)
    empty_into     the feature it turns into ("broken sword")
    spend_on       the verbs that spend it (default ["attack"])
    draw_from      "carried" (default) or "nearby": where supplies are looked for
    label          what to call the resource in messages ("rounds", "mana", "durability")
    empty_text, reload_text, depleted_text    message overrides

A supply is anything with a positive <resource> prop (and matching type): an ammo box, a mana
potion, the player's own mana pool, a whetstone. Portable supplies are used up and vanish when
drained, unless they have keep_when_empty.
"""

DEFAULT_TEXTS = {
    "empty_text": "{self.The} is out of {label}.",
    "reload_text": "You load {self} from {source}. ({stored}/{capacity} {label})",
    "full_text": "{self.The} is already full.",
    "no_supply_text": "You have nothing to load {self} with.",
    "not_reloadable_text": "{self.The} can't be reloaded.",
    "no_storage_text": "{self.The} draws straight from your {label}; there is nothing to load.",
    "wrong_supply_text": "{source.The} won't fit {self}.",
    "consumed_text": "{self.The} is used up.",
    "transmuted_text": "{self.The} is spent.",
}


def is_consumer(ent):
    return ent is not None and bool(ent.props.get("resource") or ent.props.get("capacity"))


def _num(v, default=0):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else default


def cost(ent):
    return _num(ent.props.get("cost"), 1)


def capacity(ent):
    return _num(ent.props.get("capacity"), 0)


def stored(ent):
    if "stored" not in ent.props:
        ent.props["stored"] = capacity(ent)   # things come loaded
    return _num(ent.props.get("stored"), 0)


def feed(ent):
    f = ent.props.get("feed")
    if f in ("internal", "auto", "direct"):
        return f
    return "internal" if capacity(ent) else "direct"


def reloadable(ent):
    return ent.props.get("reloadable", True) is not False


def label(ent):
    return ent.props.get("label") or ent.props.get("resource") or "charge"


def feeds(world, source, item):
    """Can *source* supply *item*?"""
    res = item.props.get("resource")
    if not res or source is None or source.uid == item.uid:
        return False
    if _num(source.props.get(res), 0) <= 0:
        return False
    want = item.props.get("resource_type")
    return not want or source.props.get(res + "_type") == want


def sources(world, item):
    """Supplies for *item*, nearest first: the player, what they carry, then (if allowed) nearby things."""
    pool = [world.player] + [e for e in world.descendants(world.player)]
    if item.props.get("draw_from") == "nearby" and world.room is not None:
        pool += [e for e in world.visible_tree(world.room) if e not in pool]
    return [e for e in pool if feeds(world, e, item)]


def available(world, item):
    res = item.props.get("resource")
    return sum(_num(s.props.get(res)) for s in sources(world, item)) if res else 0


def ready(world, item):
    """Has *item* enough for one more use (counting supplies it can draw on automatically)?"""
    if not is_consumer(item):
        return True
    need = cost(item)
    f = feed(item)
    if f == "direct":
        return available(world, item) >= need
    if stored(item) >= need:
        return True
    return f == "auto" and reloadable(item) and stored(item) + available(world, item) >= need


def _take(world, item, srcs, amount):
    """Drain up to *amount* from *srcs*; returns (taken, names of supplies drawn on)."""
    res = item.props["resource"]
    got, used = 0, []
    for s in srcs:
        if got >= amount:
            break
        have = _num(s.props.get(res))
        n = min(have, amount - got)
        if n <= 0:
            continue
        s.props[res] = have - n
        got += n
        used.append(s)
        if s.props[res] <= 0 and "portable" in s.tags and not s.props.get("keep_when_empty") \
                and s.uid != world.player_uid:
            world.destroy(s)
    return got, used


class Consumables:
    def __init__(self, interp):
        self.i = interp
        self.w = interp.world

    def say(self, item, key, ctx, style=None, **extra):
        text = item.props.get(key) or self.w.string("consumer_" + key, DEFAULT_TEXTS.get(key, ""))
        if not text:
            return
        sub = ctx.derive(self_ent=item)
        sub.local.update(label=label(item), stored=stored(item) if capacity(item) else available(self.w, item),
                         capacity=capacity(item))
        sub.local.update(extra)
        self.w.say(self.i.render(text, sub), style)

    def reload(self, item, ctx, source=None, quiet=False):
        """Fill *item* from a given supply, or from everything carried. Returns how much went in.
        *quiet* hides the reasons it couldn't (already full, nothing to load it with)."""
        w = self.w
        if not is_consumer(item):
            if not quiet:
                w.say(self.i.render("{self.The} doesn't take anything.", ctx.derive(self_ent=item)))
            return 0
        if not capacity(item):
            if not quiet:
                self.say(item, "no_storage_text", ctx)
            return 0
        if not reloadable(item):
            if not quiet:
                self.say(item, "not_reloadable_text", ctx)
            return 0
        need = capacity(item) - stored(item)
        if need <= 0:
            if not quiet:
                self.say(item, "full_text", ctx)
            return 0
        if source is not None and not feeds(w, source, item):
            if not quiet:
                self.say(item, "wrong_supply_text", ctx, source=source.uid)
            return 0
        srcs = [source] if source is not None else sources(w, item)
        if not srcs:
            if not quiet:
                self.say(item, "no_supply_text", ctx)
            return 0
        # Name the supply before drawing on it: an emptied box is thrown away.
        first = self.i.render("{x}", ctx.derive(local={"x": srcs[0].uid}))
        got, used = _take(w, item, srcs, need)
        item.props["stored"] = stored(item) + got
        if got:
            self.say(item, "reload_text", ctx, source=first)
        return got

    def carried_consumers(self):
        w = self.w
        return [e for e in w.descendants(w.player) if is_consumer(e)]

    def reload_all(self, ctx):
        """Top up everything carried that can be reloaded. Returns how much went in."""
        total = 0
        for item in self.carried_consumers():
            if capacity(item) and reloadable(item) and stored(item) < capacity(item):
                total += self.reload(item, ctx, quiet=True)
        if not total:
            self.w.say(self.w.string("consumer_nothing_to_reload",
                                     "You have nothing that needs reloading, or nothing to reload it with."))
        return total

    def supply(self, source, ctx):
        """Use a supply by itself: it goes into whatever carried things it fits."""
        total = 0
        for item in self.carried_consumers():
            if source.uid not in self.w.entities:
                break
            if feeds(self.w, source, item) and capacity(item) and reloadable(item) and stored(item) < capacity(item):
                total += self.reload(item, ctx, source=source, quiet=True)
        if not total:
            self.w.say(self.i.render(self.w.string("consumer_nothing_takes", "Nothing you carry takes {self}."),
                                     ctx.derive(self_ent=source)))
        return total

    def spend(self, item, ctx):
        """Pay for one use. Returns False (with a message) if *item* can't be used right now.
        Running out of a consumable or transmuting item is settled afterwards by deplete()."""
        w = self.w
        if not is_consumer(item):
            return True
        need = cost(item)
        f = feed(item)
        if f == "direct":
            srcs = sources(w, item)
            if sum(_num(s.props.get(item.props["resource"])) for s in srcs) < need:
                self.say(item, "empty_text", ctx, style="warn")
                return False
            _take(w, item, srcs, need)
            return True
        if stored(item) < need and f == "auto" and reloadable(item):
            self.reload(item, ctx, quiet=True)
        if stored(item) < need:
            self.say(item, "empty_text", ctx, style="warn")
            return False
        item.props["stored"] = stored(item) - need
        if stored(item) < need and item.props.get("on_empty") in ("consume", "transmute"):
            if not (f == "auto" and reloadable(item) and available(w, item) >= need):
                item.props["_depleted"] = True
        return True

    def deplete(self, item, ctx):
        """Used up: vanish, or turn into something else (a broken blade, an empty bottle)."""
        w = self.w
        if item is None or not item.props.get("_depleted") or item.uid not in w.entities:
            return
        item.props.pop("_depleted", None)
        how = item.props.get("on_empty")
        parent = w.get(item.parent)
        if how == "consume":
            self.say(item, "depleted_text" if item.props.get("depleted_text") else "consumed_text", ctx)
            w.destroy(item)
        elif how == "transmute":
            self.say(item, "depleted_text" if item.props.get("depleted_text") else "transmuted_text", ctx)
            into = item.props.get("empty_into")
            w.destroy(item)
            if into and parent is not None:
                w.spawn_spec({"id": into} if isinstance(into, str) else into, parent)


def best_weapon(world, holder):
    """The hardest-hitting weapon *holder* carries that can be used right now (uid, or "")."""
    best, best_dmg = "", 0
    for e in world.descendants(holder):
        dmg = _num(e.props.get("damage"))
        if dmg <= best_dmg or "portable" not in e.tags:
            continue
        if is_consumer(e) and "attack" in (e.props.get("spend_on") or ["attack"]) and not ready(world, e):
            continue
        best, best_dmg = e.uid, dmg
    return best
