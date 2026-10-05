"""Mod discovery, dependency resolution and content merging.

A mod is a folder containing a ``mod.json`` manifest plus any number of other
``.json`` content files.  Each content file is an object whose top-level keys
are *sections* (``features``, ``rooms``, ``areas``, ``regions``, ``beats`` ...).
Everything from every selected mod is merged, in load order, into a single
:class:`Registry` that the world generator works from.
"""

import copy
import fnmatch
import json
import os

# Sections whose entries are keyed by id.  Later mods replace earlier entries
# with the same id, or deep-merge into them when the entry has "_patch": true.
ID_SECTIONS = (
    "features", "rooms", "areas", "regions", "beats", "premises",
    "verbs", "rules", "directions", "macros",
)
# Sections that are plain key -> value maps merged key by key.
MAP_SECTIONS = ("strings", "settings")
# Grammar: lists are concatenated so mods extend each other's vocabulary.
LIST_MAP_SECTIONS = ("grammar",)

KNOWN_SECTIONS = set(ID_SECTIONS) | set(MAP_SECTIONS) | set(LIST_MAP_SECTIONS)


class ModError(Exception):
    pass


def _strip_comments(obj):
    """Remove keys starting with '//' so authors can annotate JSON."""
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items() if not k.startswith("//")}
    if isinstance(obj, list):
        return [_strip_comments(v) for v in obj]
    return obj


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        try:
            return _strip_comments(json.load(fh))
        except json.JSONDecodeError as exc:
            raise ModError("%s: invalid JSON (line %d col %d): %s"
                           % (path, exc.lineno, exc.colno, exc.msg))


def deep_patch(base, patch):
    """Deep-merge *patch* into a copy of *base*.

    * dict values merge recursively
    * a key written as "+key" appends its list to the existing list
    * a key written as "-key" removes the listed values from the existing list
    * anything else replaces
    """
    result = copy.deepcopy(base) if isinstance(base, dict) else {}
    for key, val in patch.items():
        if key == "_patch":
            continue
        if key.startswith("+"):
            real = key[1:]
            cur = result.get(real) or []
            if not isinstance(cur, list):
                cur = [cur]
            result[real] = cur + (copy.deepcopy(val) if isinstance(val, list) else [copy.deepcopy(val)])
        elif key.startswith("-") and len(key) > 1:
            real = key[1:]
            remove = val if isinstance(val, list) else [val]
            result[real] = [v for v in result.get(real) or [] if v not in remove]
        elif isinstance(val, dict) and isinstance(result.get(key), dict):
            result[key] = deep_patch(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


class ModInfo:
    def __init__(self, path, manifest):
        self.path = path
        self.id = manifest.get("id") or os.path.basename(path.rstrip(os.sep))
        self.name = manifest.get("name", self.id)
        self.version = str(manifest.get("version", "0"))
        self.author = manifest.get("author", "")
        self.description = manifest.get("description", "")
        self.requires = list(manifest.get("requires", []))
        self.load_after = list(manifest.get("load_after", []))
        self.recommends = list(manifest.get("recommends", []))
        self.conflicts = list(manifest.get("conflicts", []))
        self.tags = list(manifest.get("tags", []))
        self.priority = manifest.get("priority", 50)
        self.default = bool(manifest.get("default", False))
        self.content = manifest.get("content", ["*.json"])
        self.manifest = manifest

    def content_files(self):
        files = []
        for root, _dirs, names in os.walk(self.path):
            for name in sorted(names):
                full = os.path.join(root, name)
                rel = os.path.relpath(full, self.path)
                if rel == "mod.json" or not name.endswith(".json"):
                    continue
                if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(name, pat) for pat in self.content):
                    files.append(full)
        return sorted(files)

    def __repr__(self):
        return "<Mod %s %s>" % (self.id, self.version)


def default_mod_dirs():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dirs = [os.path.join(here, "mods")]
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    dirs.append(os.path.join(data_home, "patchwork", "mods"))
    for extra in os.environ.get("PATCHWORK_MODS", "").split(os.pathsep):
        if extra:
            dirs.append(extra)
    return dirs


def discover(mod_dirs):
    """Find every mod folder.  Returns (mods_by_id, errors)."""
    mods, errors = {}, []
    for base in mod_dirs:
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            manifest_path = os.path.join(path, "mod.json")
            if not os.path.isfile(manifest_path):
                continue
            try:
                info = ModInfo(path, read_json(manifest_path))
            except (ModError, OSError) as exc:
                errors.append(str(exc))
                continue
            if info.id in mods:
                errors.append("Duplicate mod id '%s' in %s (keeping %s)"
                              % (info.id, path, mods[info.id].path))
                continue
            mods[info.id] = info
    return mods, errors


def resolve_order(selected, available):
    """Expand *selected* with required dependencies and sort into load order.

    Returns (ordered_mod_infos, added_dependency_ids, problems).  *problems* are
    fatal (missing dependency, dependency cycle); conflicts are reported as
    problems too so the caller can decide.
    """
    problems, added = [], []
    chosen = []
    seen = set()

    def add(mid, chain):
        if mid in seen:
            return
        if mid not in available:
            problems.append("Missing mod '%s' (required by %s)" % (mid, " -> ".join(chain) or "selection"))
            return
        seen.add(mid)
        chosen.append(mid)
        for dep in available[mid].requires:
            if dep not in seen and dep not in selected and dep not in added:
                added.append(dep)
            add(dep, chain + [mid])

    for mid in selected:
        add(mid, [])

    for mid in chosen:
        for other in available[mid].conflicts:
            if other in seen:
                problems.append("Mod '%s' conflicts with '%s'" % (mid, other))

    # Topological sort: requires and load_after edges, priority as tie-break.
    remaining = set(chosen)
    order = []
    while remaining:
        ready = [m for m in remaining
                 if not any(d in remaining for d in available[m].requires + available[m].load_after)]
        if not ready:
            problems.append("Dependency cycle between: %s" % ", ".join(sorted(remaining)))
            ready = list(remaining)
        ready.sort(key=lambda m: (available[m].priority, m))
        first = ready[0]
        order.append(first)
        remaining.discard(first)
    return [available[m] for m in order], added, problems


class Registry:
    """All merged content from the selected mods."""

    def __init__(self):
        self.sections = {s: {} for s in KNOWN_SECTIONS}
        self.sources = {}  # (section, id) -> mod id
        self.mods = []     # [{id, name, version}]
        self.warnings = []

    def __getitem__(self, section):
        return self.sections.setdefault(section, {})

    def get(self, section, key, default=None):
        return self.sections.get(section, {}).get(key, default)

    # ------------------------------------------------------------------
    def merge_file(self, mod, path, data):
        if not isinstance(data, dict):
            raise ModError("%s: top level must be an object of sections" % path)
        for section, entries in data.items():
            if section not in KNOWN_SECTIONS:
                self.warnings.append("%s: unknown section '%s' (ignored)" % (os.path.relpath(path), section))
                continue
            if not isinstance(entries, dict):
                raise ModError("%s: section '%s' must be an object" % (path, section))
            if section in ID_SECTIONS:
                for key, entry in entries.items():
                    self._merge_entry(mod, section, key, entry, path)
            elif section in MAP_SECTIONS:
                target = self.sections[section]
                for key, val in entries.items():
                    if isinstance(val, dict) and isinstance(target.get(key), dict):
                        target[key] = deep_patch(target[key], val)
                    else:
                        target[key] = copy.deepcopy(val)
            else:  # grammar
                target = self.sections[section]
                for key, val in entries.items():
                    vals = val if isinstance(val, list) else [val]
                    if key.startswith("!"):
                        target[key[1:]] = list(vals)
                    else:
                        target.setdefault(key, []).extend(vals)

    def _merge_entry(self, mod, section, key, entry, path):
        target = self.sections[section]
        if entry is None or (isinstance(entry, dict) and entry.get("_delete")):
            target.pop(key, None)
            return
        if not isinstance(entry, dict):
            raise ModError("%s: %s.%s must be an object" % (path, section, key))
        if entry.get("_patch"):
            if key not in target:
                self.warnings.append("%s: patch for missing %s '%s' (skipped)" % (mod.id, section, key))
                return
            target[key] = deep_patch(target[key], entry)
        else:
            new = copy.deepcopy(entry)
            new["_mod"] = mod.id
            target[key] = new
        self.sources[(section, key)] = mod.id
        if section == "areas" and isinstance(target[key].get("rooms"), dict):
            # Inline room definitions become global rooms named "area/room".
            for rid, rdef in target[key]["rooms"].items():
                rdef = copy.deepcopy(rdef)
                rdef.setdefault("_mod", mod.id)
                rdef["_area"] = key
                self.sections["rooms"]["%s/%s" % (key, rid)] = rdef

    def to_dict(self):
        return {"sections": self.sections, "mods": self.mods}

    @classmethod
    def from_dict(cls, data):
        reg = cls()
        reg.sections.update(data["sections"])
        reg.mods = data.get("mods", [])
        return reg


def build_registry(ordered_mods):
    reg = Registry()
    for mod in ordered_mods:
        reg.mods.append({"id": mod.id, "name": mod.name, "version": mod.version})
        for path in mod.content_files():
            reg.merge_file(mod, path, read_json(path))
    return reg
