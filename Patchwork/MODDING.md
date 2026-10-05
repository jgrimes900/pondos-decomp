# Patchwork Modding Guide

Everything a player sees in Patchwork comes from mods: places, characters, items, verbs, rules,
story, even the words "You can't go that way." A mod is a folder of JSON files. There is no code to
write: behaviour is described with small JSON conditions and effects that the engine interprets.

* [1. Quick start](#1-quick-start)
* [2. How a world is woven](#2-how-a-world-is-woven)
* [3. Mod folders and mod.json](#3-mod-folders-and-modjson)
* [4. Merging, overriding and patching](#4-merging-overriding-and-patching)
* [5. Features: the nested building block](#5-features-the-nested-building-block)
* [6. Rooms and exits](#6-rooms-and-exits)
* [7. Areas: hand-made places](#7-areas-hand-made-places)
* [8. Regions: generated in-between places](#8-regions-generated-in-between-places)
* [9. Story: beats and premises](#9-story-beats-and-premises)
* [10. Verbs and actions](#10-verbs-and-actions)
* [11. Rules, events and hooks](#11-rules-events-and-hooks)
* [12. The logic language](#12-the-logic-language) (references, matchers, conditions, effects, expressions, templates)
* [13. Grammar: generating novel text](#13-grammar-generating-novel-text)
* [14. Directions, strings and settings](#14-directions-strings-and-settings)
* [15. Working with other mods](#15-working-with-other-mods)
* [16. Testing your mod](#16-testing-your-mod)
* [17. Worked example: The Drowned Lighthouse](#17-worked-example-the-drowned-lighthouse)

---

## 1. Quick start

```
~/.local/share/patchwork/mods/      (or Patchwork/mods/)
  my_mod/
    mod.json        manifest
    anything.json   content (any number of files, any names, subfolders allowed)
```

`mod.json`:

```json
{
  "id": "my_mod",
  "name": "My First Mod",
  "version": "1.0.0",
  "description": "A tiny shrine in the woods.",
  "requires": ["core"]
}
```

`shrine.json`:

```json
{
  "areas": {
    "shrine": {
      "name": "the Mossy Shrine",
      "tags": ["fantasy", "holy"],
      "theme": ["forest"],
      "rooms": {
        "clearing": {
          "name": "Shrine Clearing",
          "description": "A ring of stones surrounds a tiny shrine, half swallowed by moss.",
          "features": ["offering_dish"]
        }
      }
    }
  },
  "features": {
    "offering_dish": {
      "extends": ["scenery", "surface"],
      "name": "offering dish",
      "aliases": ["dish"],
      "appearance": "A stone dish sits before the shrine.",
      "features": [{"id": "copper_coins", "chance": 0.5}]
    }
  }
}
```

Check it with `./patchwork.sh --validate --mods my_mod,wilds`, see where it lands with
`./patchwork.sh --map --mods my_mod,wilds --seed 1`, then play it.

Any key starting with `//` is a comment and is ignored, at any depth.

---

## 2. How a world is woven

When a new game starts:

1. **Load.** The selected mods (plus their requirements) are sorted into load order and merged into
   one *registry* (section 4).
2. **Choose a premise.** If any mod defines `premises`, the player picks one or gets a random one.
   The premise sets the intro, the ending, the player's starting kit and the story *structure*,
   for example `["opening", "middle*", "climax"]`.
3. **Plan the story.** For each slot of the structure a **beat** is picked from *any* loaded mod
   whose `stage` matches (`middle*` means as many middle beats as are available, up to a limit).
   Beats prefer the premise's tags, and a beat that `needs` something prefers to come after a beat
   that `provides` it.
4. **Lay out the spine.** The start area comes first, then the area of each beat in story order.
   Each area gets a *stage* number: 0 for the start, increasing along the spine.
5. **Stitch.** Consecutive spine areas are joined by generated **filler rooms** from **regions**.
   Regions are chosen by how well their tags match the two areas' themes, and the path may change
   region halfway to make a transition (road becoming forest becoming marsh). If a beat has a
   `gate`, the last step into its area is locked until the story reaches that beat.
6. **Side content.** Every other area from the selected mods is attached as an optional side area.
   Filler rooms sprout dead-end branches and a few loops, scaled by world size.
7. **Populate.** Features tagged `scatter` (forage, trinkets) and `encounter` (creatures) are placed
   in generated rooms whose tags match their `habitat`.
8. **Bind the story.** Each beat's **roles** are filled, either by *finding* an existing entity (for
   example "any relic placed earlier in the world") or by *spawning* one, often with a generated name.
   If a role asks for a place the world lacks, the generator grows a spur of that region on demand.
9. **Rumours.** Travellers (features tagged `wanderer`) are placed on the roads leading to each
   beat, carrying that beat's `rumor` text.

During play, the active beat's `objective` is checked after every command. When it is met, the beat
completes, the next one starts, and the player is told where the story leads next.

---

## 3. Mod folders and mod.json

Mods are discovered in `Patchwork/mods/`, `~/.local/share/patchwork/mods/`, any folder listed in
the `PATCHWORK_MODS` environment variable (colon-separated), and any `--mod-dir`.

| Field | Meaning |
| --- | --- |
| `id` | Unique id (defaults to the folder name). |
| `name`, `version`, `author`, `description` | Shown in the mod menu. The first sentence of the description is the one-line summary. |
| `requires` | Mod ids that must be loaded. They are enabled automatically and load first. |
| `load_after` | Load after these mods *if* they are selected (no hard dependency). Use this when you patch another mod's content. |
| `recommends` | Suggested to the player when your mod is chosen. |
| `conflicts` | Mods that cannot be combined with this one. |
| `tags` | Informational. |
| `priority` | Tie-break for load order (lower loads first; default 50; core is 0). |
| `default` | `true` to pre-select in the menu on first run. |
| `content` | Glob patterns for content files (default `["*.json"]`). |

Every other `.json` file in the folder is a content file. Its top-level keys are **sections**:

`features`, `rooms`, `areas`, `regions`, `beats`, `premises`, `verbs`, `rules`, `macros`,
`directions`, `grammar`, `strings`, `settings`.

---

## 4. Merging, overriding and patching

All selected mods are merged in load order.

* **Id sections** (`features`, `rooms`, `areas`, `regions`, `beats`, `premises`, `verbs`, `rules`,
  `macros`, `directions`): an entry with the same id as an earlier one **replaces** it.
* **Patching:** add `"_patch": true` to deep-merge into the existing entry instead:

  ```json
  {"features": {"player": {"_patch": true, "props": {"health": 20}}}}
  ```

  Inside a patch, `"+key": [...]` appends to a list, `"-key": [...]` removes values from a list,
  nested objects merge, and anything else replaces.
* **Removing:** `"some_id": null` or `{"_delete": true}`.
* **strings / settings:** merged key by key; later mods win.
* **grammar:** lists are **concatenated**, so several mods can add words to the same symbol.
  Write `"!symbol"` to replace a symbol's list instead.

---

## 5. Features: the nested building block

Everything in the world is a **feature**: items, furniture, characters, the player, even rooms
(section 6). Features nest without limit: a room holds a desk, the desk holds a drawer, the drawer
holds a letter. Descriptions are assembled from that nesting (section 5.3).

### 5.1 Fields

| Field | Meaning |
| --- | --- |
| `name` | Display name. May use grammar (`"#tree# tree"`), expanded once when the feature is created. |
| `article` | `null` (automatic a/an), `""` (proper noun), `"the"`, `"some"` and so on. |
| `proper` | `true` is shorthand for `article: ""`. |
| `aliases` | Extra words the player can use. Every word of the name is added automatically. |
| `tags` | Free-form labels used by matchers, generation and story roles. |
| `props` | Arbitrary state: numbers, strings, booleans. `{"rand": [2, 6]}` rolls a number at creation, `{"choose": [...]}` picks one, and strings may use grammar. |
| `description` | Shown by `examine`. A string, or conditional variants (section 5.3). |
| `appearance` | The sentence used when this feature is listed inside its parent. `false` means never listed: the parent's own text already mentions it. If omitted, the feature appears in a "You also see ..." list. |
| `contents_text` | Template listing this feature's visible children, with `{contents}`: `"On the table you see {contents}."` |
| `empty_text` | Shown instead of `contents_text` when there are no visible children. |
| `contents_visible` | Condition deciding whether children can be seen (closed chests use it). |
| `hidden` | Not visible or usable until revealed (for example by `search`). |
| `features` | Nested feature specs (section 5.2). |
| `actions` | Verb handlers (section 10). |
| `extends` | Inherit from other features (traits). |
| `abstract` | `true` for a trait: inherited from, never placed. |
| `on_enter`, `on_turn`, `on_tick`, `on_<anything>` | Hooks (section 11.3). |
| `habitat` | For `scatter` and `encounter` features: room tags they can be placed in. |
| `weight`, `min_stage` | Placement weight; earliest story stage an encounter may appear at. |

**Inheritance (`extends`)**: parents merge in order, then the feature itself. `tags` and
`aliases` are unioned, `props` merged, `features` concatenated, `actions` per verb are *stacked*
(the child's handlers are tried first, then the parent's), `on_*` hooks accumulate, and everything
else is replaced. Extending a feature from a mod that isn't loaded is allowed and contributes
nothing (a *soft* dependency).

Core traits you can extend: `scenery`, `portable`, `surface`, `container`, `openable`, `lockable`,
`key`, `door`, `person`, `wanderer`, `edible`, `drinkable`, `readable`, `light_source`,
`valuable`. With Steel & Peril loaded you also get `creature` and `hostile`.

### 5.2 Feature specs (placing features)

Anywhere a list of features appears (`features`, `spawn`, region rooms...), each entry is a
**spec**:

```json
"features": [
  "lantern",                                        // a feature id
  {"id": "copper_coins", "chance": 0.5},            // maybe
  {"id": "candle", "count": [1, 3]},                // 1-3 of them
  {"pick": ["apple", "stale_bread", "tinderbox"]},  // one of these
  {"pick_tag": "trinket", "count": 2},              // two random features from ANY mod tagged "trinket"
  {"pick_tag": "relic", "unique": true},            // ...that hasn't been placed anywhere yet
  {"id": "tree", "hidden": true},                   // an id plus overrides (any feature field)
  {"id": "rogue_drone", "if": {"mod": "combat"}},   // only if a condition holds
  {"name": "rusty nail", "extends": ["portable"],   // a brand-new inline feature
   "description": "Bent."}
]
```

Unknown ids are skipped silently. That's intentional: it lets you reference features from optional
mods (`{"id": "tree"}` uses The Wilds' tree when that mod is loaded).

### 5.3 How descriptions are built

`look` shows the room's name, its `description`, then for each visible child either its
`appearance` sentence or a place in the "You also see ..." list. A child with a `contents_text`
then lists its own children, and so on down the tree. `examine X` shows X's description plus its
children the same way.

Any text field may be a list of **variants**, the first whose condition passes is used:

```json
"description": [
  {"if": {"prop": "open"}, "text": "The chest gapes open."},
  {"text": "A heavy oak chest, firmly shut."}
]
```

Rooms may also have a `brief` text, used when revisiting (unless the player typed `verbose`).

---

## 6. Rooms and exits

A room is a feature with exits. Rooms are defined inside areas (section 7), as region templates
(section 8), or in a `rooms` section to be shared.

```json
"exits": [
  {"to": "hall", "dir": "north", "distance": 2},
  {"to": "cellar", "dir": "down", "name": "trapdoor", "aliases": ["hatch"],
   "description": "A trapdoor is set into the floor.",
   "if": {"prop": "open", "of": "here:trapdoor"},
   "blocked": "The trapdoor is closed."},
  {"to": "ledge", "dir": "east", "oneway": true, "hidden": true}
]
```

| Field | Meaning |
| --- | --- |
| `to` | Room id (local to the area first, then global). |
| `dir` | A direction id (section 14). The return exit uses the opposite direction automatically. |
| `distance` | Travel cost. Shown to the player; advances the clock. |
| `name`, `aliases` | Lets the player say `go trapdoor`; shown instead of the direction. |
| `description` | Sentence added to the room description. |
| `if`, `blocked` | Condition to pass and the message when it fails. |
| `hidden`, `visible_if` | Hide the exit entirely (reveal later with the `exit` effect). |
| `oneway`, `back` | No return exit, or an explicit return direction (`back: false` for none). |
| `back_<field>` | Fields for the return exit only, for example `back_blocked`. |
| `on_use` | Effects run when the exit is taken. |
| `show_dest` | Show the destination name before it has been visited. |

Players move with `north`, `n`, `go north`, `go trapdoor`, `go to <room name>` (travel by
pathfinding through visited rooms, stopping if interrupted), or by typing the destination name.
An exit with neither `dir` nor `name` is labelled by its destination ("to Hydroponics Bay"), and
any word of that name works for it, even before the destination has been visited.

---

## 7. Areas: hand-made places

```json
"areas": {
  "hamlet": {
    "name": "#village_name#",
    "tags": ["settlement", "start", "fantasy"],
    "theme": ["road", "pastoral"],
    "start": "inn",
    "entrances": ["gate"],
    "rooms": { "inn": { ... }, "gate": { ... } }
  }
}
```

| Field | Meaning |
| --- | --- |
| `name` | Grammar allowed; available to text as `{beat.area}` and `{self.area}`. |
| `tags` | `start` marks a possible starting area. Tags are also used by beats that ask for an area by tag and by region matching. |
| `theme` | Extra tags that steer which regions connect to this area. |
| `rooms` | Object of inline room definitions (ids are local, registered as `area/room`), or a list of global room ids. |
| `entrances` | Rooms that may be connected to the outside world (default: all rooms). |
| `start` | Starting room when this is the start area. |
| `room_tags` | Tags added to every room in the area. |
| `directions` | Directions the generator may use when connecting this area (section 14). |
| `only_with_beat` | Only build this area if a story beat uses it. |
| `include: false` | Never add it as side content. |
| `allow_scatter` | Let scatter/encounter features appear in its rooms. |
| `stage` | Upper bound for how deep into the story a side area may be attached. |

---

## 8. Regions: generated in-between places

Regions generate the novel country that joins areas together.

```json
"regions": {
  "forest": {
    "tags": ["forest", "wild", "outdoor", "fantasy"],
    "connects": ["road", "pastoral", "dungeon", "hills"],
    "length": [2, 4],
    "distance": [1, 3],
    "weight": 3,
    "rooms": [
      {"name": "#forest_name#", "description": "#forest_desc#", "weight": 3,
       "features": [{"chance": 0.6, "id": "tree"}, {"chance": 0.3, "id": "berry_bush"}]},
      {"name": "Woodcutter's Clearing", "description": "Stumps dot this clearing."}
    ],
    "features": [{"chance": 0.2, "id": "wildflowers"}]
  }
}
```

* `tags` + `connects` are scored against the themes of the two areas being joined.
* `length` is how many rooms a path through this region has (scaled by world size). `distance` is the distance of each step.
* `rooms` are room templates: inline room definitions with an optional `weight`, or room ids. Names
  and descriptions use grammar, so every generated room is different. Templates with a fixed name
  rarely repeat.
* `features` are added to every room made from the region.
* `directions` limits exit directions (a space station uses fore/aft/port/starboard).

Only regions are needed for a playable world. With no areas at all, the generator builds a
sandbox wilderness.

---

## 9. Story: beats and premises

### 9.1 Beats

A beat is one chapter. Beats from different mods are chained into a single story.

```json
"beats": {
  "barrow_relic": {
    "title": "The Barrow's Heart",
    "stage": "middle",
    "tags": ["fantasy", "relic"],
    "area": "barrow",
    "provides": ["relic"],
    "roles": {
      "relic": {"spawn": "barrow_relic", "in": {"feature": "def:barrow_sarcophagus"}, "name": "#relic_name#"}
    },
    "intro": "Somewhere ahead lies {beat.area}...",
    "hint": "Find a way into the sanctum and claim {beat.relic.name}.",
    "hook": "The old barrow, {beat.area}, has been broken open.",
    "rumor": ["They say {beat.area} stands open now."],
    "objective": {"has": "role:relic"},
    "complete_text": "As your fingers close around {beat.relic.name}..."
  }
}
```

| Field | Meaning |
| --- | --- |
| `title` | Chapter title (grammar allowed). |
| `stage` | `opening`, `middle`, `climax` (or any custom stage a premise uses). May be a list. Default `middle`. |
| `tags`, `weight` | Used to prefer beats that suit the premise. |
| `area` | Area id, `{"tags": [...]}` to use any matching area, or omitted (the beat happens wherever the story has reached). A beat whose area isn't loaded is skipped. |
| `roles` | Named entities the beat is about (below). |
| `spawn` | Extra specs to place; each may have an `in` (placement). |
| `intro` | Printed when the beat starts. |
| `journal` / `hint` | Journal entry when the beat starts; `hint` is also shown by `journal`. |
| `hook` | One sentence describing this beat's trouble. **Other** mods' characters use it via `{next.hook}`; that is how a village elder from one mod can send you to a dungeon from another. |
| `lead` | Printed after the previous beat completes. Defaults to the `default_lead` string ("Your path now leads toward {beat.area}"). |
| `rumor` | Lines given to wandering travellers on the roads leading to this beat. |
| `objective` | Condition; the beat completes when it is true (checked every command). Omit it to complete only via the `complete_beat` effect. |
| `on_start`, `on_complete` | Effects. |
| `complete_text` | Printed on completion. |
| `gate` | `true` or a message: the path into this beat's area is blocked until the beat is reached. |
| `needs`, `provides` | Ordering hints: beats that need `X` prefer to follow a beat that provides `X`. |
| `premises` | Restrict the beat to these premise ids. |

**Roles.** Each role is filled when the world is generated:

```json
"roles": {
  "giver":   {"find": {"tag": "quest_giver"}, "where": "area"},
  "villain": {"spawn": "sorcerer", "in": {"room": "top"}, "name": "#villain_name#"},
  "bane":    {"find": {"tag": "relic"}, "spawn": "spire_bane", "in": {"feature": "def:spire_shelves"}},
  "loot":    "gold_crown"
}
```

* `find`: a matcher. An existing entity is used. `where` is `area` (in this beat's area), `start`, or
  `reachable` (default: anywhere already reachable at this point in the story). Entities may fill
  roles in several beats; add `"exclusive": true` to prevent that.
* `spawn`: a spec, used if `find` is absent or found nothing. `in` is the **placement**:
  * `"area"` (default): a random room of the beat's area
  * `{"room": "local_room_id"}`, `{"room_tags": [...]}`, `{"area": "area_id"}`
  * `{"feature": matcher}`: *inside* a matching feature in the area (in a chest, on an altar)
  * `{"role": "giver"}`: carried by another role (set `"hidden": true` and hand it over in dialogue)
  * `{"region": "maintenance"}`: a generated room with that tag. If the world doesn't have one yet, a spur of a matching region is **grown** to hold it.
  * `"before"` (a generated room reachable before this beat's gate), `"anywhere"`, `"start"`, `"player"`
* `name` renames the entity with grammar (proper noun unless `"proper": false`). `props`, `tags`
  and `hidden` adjust it. `"optional": true` lets the beat proceed if the role can't be filled;
  otherwise the beat is dropped (and its gate removed).
* A string is shorthand for `{"spawn": "<id>"}`.

Text can refer to roles as `{beat.villain}` / `{beat.villain.name}` (this beat) or `{role.villain}`
(the current beat first, then any beat). Conditions use `"role:villain"`.

### 9.2 Premises

```json
"premises": {
  "waning_light": {
    "title": "The Waning Light",
    "menu_name": "The Waning Light (fantasy)",
    "tags": ["fantasy"],
    "beat_tags": ["fantasy"],
    "strict": true,
    "structure": ["opening", "middle*", "climax"],
    "start_area": {"tags": ["start", "fantasy"]},
    "intro": "Each evening the sun sets a little earlier... You are {var.player_name}...",
    "ending": "And so the light returned...",
    "inventory": [{"name": "worn cloak", "extends": ["portable"]}],
    "player": {"props": {"courage": 3}}
  }
}
```

| Field | Meaning |
| --- | --- |
| `structure` | Stage slots. `stage*` means as many beats of that stage as available (up to `max_middle_beats`). |
| `beats` | An explicit list of beat ids instead of a structure. |
| `beat_tags` | Preferred beat tags. With `"strict": true`, beats must share one of them (keeps a sci-fi story free of fantasy chapters when both kinds of mod are loaded). |
| `start_area`, `start_room` | Area id or `{"tags": [...]}`; optional room override. |
| `intro`, `ending` | Printed at the start and when the last beat completes. |
| `end_on_complete` | End the game when the story completes (default: keep exploring). |
| `player`, `inventory` | Fields merged onto the player; starting item specs. |
| `vars`, `flags` | Initial global variables and flags. |
| `weight` | Chance of being picked at random. |

With no premise, beats are still chained using the default structure, and a world with no beats is
free exploration.

---

## 10. Verbs and actions

### 10.1 Verbs

Verbs are defined by mods. Core defines the usual set; Steel & Peril adds `attack`, `rest`
and `status`; Turning Days adds `time`.

```json
"verbs": {
  "unlock": {
    "aliases": ["open lock"],
    "target": "entity",
    "prepositions": ["with", "using"],
    "help": "unlock <thing> [with <key>]",
    "default": ["{target.The} has no lock."]
  }
}
```

| Field | Meaning |
| --- | --- |
| `aliases` | Other words or phrases (multi-word aliases match first: `pick up` before `pick`). |
| `target` | `optional` (default), `entity` (required), `none` (no object), `text` (raw words in `{args}`). |
| `scope` | `any` (default), `held`, `room`: where to look for the object. `second_scope` does the same for the second object. |
| `prepositions` | Split off a second object: `put X in Y`, `unlock X with Y`. |
| `second` | `"required"` to demand the second object. |
| `all` | Allow `take all`; `"direct"` for only direct children. `all_if` filters candidates. |
| `default` | Handlers used when nothing more specific handled the command. |
| `no_target` | Handlers for the verb with no object (`search`, `listen`). |
| `time` | Turns the action takes (default 1; 0 for free actions like `look`). |
| `bare_exit` | This verb handles a bare exit name typed alone (`north`). Core's `go` has it. |
| `help`, `hidden` | Help text, or hide from `help`. |

**Dispatch order** for `verb target [prep second]`:

1. rules `before:<verb>` and `before:*` (a `stop` cancels the command)
2. the target's `actions.<verb>` handlers
3. the second object's `actions.<verb>_with` handlers (so `use key on door` can be handled by the door)
4. for a verb with no object: the room's `actions.<verb>`, then the verb's `no_target`
5. the verb's `default`
6. rules `after:<verb>` and `after:*`
7. the turn passes (if `time` > 0): `turn` rules and `on_turn` hooks

### 10.2 Action handlers

An action value can be:

* one effect or a list of effects: `"talk": ["\"Hello,\" says {self.name}."]`
* a list of **handlers**, the first whose `if` passes runs (and `else` runs if present):

```json
"open": [
  {"if": {"prop": "open"}, "do": ["{self.The} is already open."]},
  {"if": {"prop": "locked"}, "do": ["{self.The} is locked."]},
  {"do": [{"set": {"open": true}}, "You open {self}."]}
]
```

In handlers, `self` is the feature that owns the action, `target` is the command's object and
`second` the second object.

---

## 11. Rules, events and hooks

### 11.1 Rules

```json
"rules": {
  "wilds_ambience": {
    "on": "travel",
    "if": {"all": [{"chance": 0.18}, {"in_room": "tag:outdoor"}]},
    "do": [{"say": "#outdoor_ambience#", "style": "dim"}],
    "once": false,
    "priority": 50
  }
}
```

### 11.2 Events

| Event | When | Context |
| --- | --- | --- |
| `start` | New game begins | |
| `turn` | After any action that takes time | |
| `leave` | About to take an exit | `self` = room, `target` = destination |
| `travel` | Moving along an exit (before arriving) | `self` = origin, `target` = destination, `{distance}` |
| `enter` | Arrived in a room | `self` = room, `{first}` true on first visit |
| `before:<verb>`, `before:*`, `after:<verb>`, `after:*` | Around every command | `target`, `second`, `{verb}` |
| `story_complete` | The last beat completed | |
| anything | `{"emit": "name"}` from any effect | the emitter's context |

Bundled mods emit `ate`, `drank`, `read` and `killed`, so your rules can react to them.

### 11.3 Hooks on features

* `on_enter`: when the player arrives in the room containing the feature
* `on_turn`: each turn for every feature in the player's room (not what they carry)
* `on_tick`: each turn for every feature anywhere in the world (use sparingly)
* `on_<anything>`: run by the `hook` effect, for example Steel & Peril runs `on_death`

`style` on `say` can be `story`, `dim`, `warn`, `good`, `title`, `bold`, `error`.

---

## 12. The logic language

### 12.1 References (which entity?)

| Reference | Entity |
| --- | --- |
| `self`, `target`, `second`, `player`, `room` | as named (`room` is the player's room) |
| `parent`, `holder` | parent of self; room containing self |
| `it`, `local:name` | an entity stored in a local variable (`for_each`, `spawn ... as`, `find ... as`) |
| `role:name`, `role:beat_id.name` | a story role |
| `here:<matcher>` | first matching visible entity in self's room |
| `carried:<matcher>` | first matching thing the player carries |
| `near:<matcher>` | first matching thing the player can see or carry |
| `any:<matcher>` | first matching entity anywhere |
| `room:<id>`, `uid:<uid>` | by id |

### 12.2 Matchers (does an entity fit?)

* `"tag:key"`, `"def:barrow_key"`, `"role:relic"`, `"name:lantern"`, `"area:hamlet"`
* a bare word: a feature id **or** a tag
* an object combining tests: `{"tag": ["weapon"], "prop": "damage", "gte": 3, "not": "tag:cursed"}`
* a list: any of them

### 12.3 Conditions

A condition is an object; all keys must hold. `true`/`false` are allowed, a list means "all",
and a plain string is an expression (12.5).

| Condition | True when |
| --- | --- |
| `{"all": [...]}`, `{"any": [...]}`, `{"not": c}` | logic |
| `{"flag": "name"}` (or list) | global flag set |
| `{"var": "gold", "gte": 10}` | global variable comparison |
| `{"prop": "lit", "of": "target", "eq": true}` | property comparison (`of` defaults to self) |
| `{"has": matcher, "who": "player"}` | the entity holds a match anywhere inside it |
| `{"held": ref}` | the referenced entity is carried by the player |
| `{"here": matcher}` | a matching visible thing is in the player's room |
| `{"near": matcher}` | ...in the room or carried |
| `{"in_room": matcher, "of": "player"}` | the entity's room matches |
| `{"inside": matcher, "of": ref}` | the entity is nested inside a match |
| `{"tag": "x", "of": ref}`, `{"is": matcher, "of": "target"}` | tests on one entity |
| `{"target": matcher}`, `{"second": matcher}` (`null` = absent) | tests on the command's objects |
| `{"same": [ref, ref]}`, `{"exists": ref}` | identity / existence |
| `{"chance": 0.25}` | random |
| `{"clock": {"gte": 100}}`, `{"turns": 10}` | time |
| `{"visited": matcher}` | the player has been to a matching room |
| `{"mod": "combat"}` | a mod is loaded (great for optional cross-mod content) |
| `{"beat_active": id}`, `{"beat_done": id}`, `{"beat_reached": id}`, `{"next_beat": true}`, `{"story_complete": true}` | story state |
| `{"local": "name", "gt": 0}`, `{"args": "text"}` | local variables / raw command text |
| `{"expr": "player.health < 5"}` | expression |

Comparisons: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`. With none, the value is tested for
truth. A string comparison value may be a template: `{"prop": "opens", "eq": "{self.lock}"}`.

### 12.4 Effects

A string effect is shorthand for `say`. Effects run in order.

| Effect | Does |
| --- | --- |
| `{"say": text, "style": s}` | print a templated line |
| `{"if": cond, "then": [...], "else": [...]}` | branch (`do` works as `then`) |
| `{"random": [{"weight": 2, "do": [...]}, ...]}` | weighted random branch |
| `{"choice": {"prompt": t, "options": [{"text": t, "if": c, "do": [...]}], "cancel": t}}` | numbered menu: dialogue trees, shops, decisions |
| `{"set": {"open": true}, "on": ref}`, `{"add": {"health": -2}, "on": ref}`, `{"toggle": "lit"}` | properties (values may be expressions) |
| `{"set_var": {...}}`, `{"add_var": {...}}`, `{"flag": f}`, `{"unflag": f}` | global state |
| `{"let": {"dmg": "=rand(1,4)"}}` | local variable for this action |
| `{"move": ref, "to": ref}` | move an entity (`to: "player"` = into inventory) |
| `{"spawn": spec, "in": ref, "as": "name"}` | create features |
| `{"destroy": ref}`, `{"reveal": ref}`, `{"reveal": ref, "children": true}`, `{"hide": ref}` | existence and visibility (`reveal ... children` sets `{revealed}` and `{revealed_list}`) |
| `{"find": matcher, "in": ref, "as": "name"}` | store the first match in a local |
| `{"for_each": matcher, "in": ref, "do": [...], "direct": true, "hidden_too": true}` | loop; the item is `it` |
| `{"rename": text, "on": ref}`, `{"set_text": {"description": ...}, "on": ref}`, `{"tag": t}`, `{"untag": t}` | change an entity |
| `{"teleport": room_matcher}`, `{"travel": "north"}` | move the player |
| `{"exit": {"room": ref, "dir": d, "set": {"hidden": false, "if": null}}}` | change an exit |
| `{"connect": {"from": ref, "to": ref, "dir": d, "distance": n}}` | create a new exit (secret passages) |
| `{"show": "room"/"examine"/"inventory"/"journal"/"exits"/"map", "of": ref}`, `{"describe": ref}` | display |
| `{"journal": text, "quiet": true}` | add a journal entry |
| `{"complete_beat": id_or_true}`, `{"lead": true}` | story control |
| `{"emit": event}`, `{"hook": "on_death", "on": ref}`, `{"macro": id, "with": {...}}` | call other logic |
| `{"advance": n}` | pass time |
| `{"interrupt": true}` | stop a multi-leg journey |
| `{"end_game": text, "win": bool}` | end the game |
| `{"stop": true}` | cancel the rest of the command (in `before:` rules: cancel the action) |

**Macros** are reusable effect lists in the `macros` section: `{"do": [...]}`. Call them with
`{"macro": "id", "with": {"x": 1}}`; locals named `out_*` are passed back to the caller.

### 12.5 Expressions

Any value written as a string starting with `=` is an expression:
`"=max(1, player.attack + best(player, 'damage') - self.armor)"`.

* Entities: `self`, `target`, `second`, `player`, `room`, `it`, `parent`; `x.prop` reads a property
  (missing = 0), `x.name` the name; `role.villain.health`
* `var.gold`, `clock`, `turns`, local variables, `true`/`false`/`none`, numbers, strings
* `+ - * / // %`, comparisons, `and`/`or`/`not`, `a if cond else b`
* `min`, `max`, `abs`, `int`, `round`, `rand(lo, hi)`, `chance(p)`,
  `best(entity, 'prop')` (highest value among carried things), `total(entity, 'prop')`,
  `count(entity, 'tag:coin')`, `has(entity, 'tag:key')`

### 12.6 Text templates

Every text runs through grammar (`#symbol#`, section 13) and then placeholders:

| Placeholder | Gives |
| --- | --- |
| `{self}`, `{target}` ... | "the lantern" (proper nouns without "the") |
| `{x.name}`, `{x.a}`, `{x.the}`, `{x.Name}`, `{x.A}`, `{x.The}` | name forms |
| `{x.<prop>}`, `{x.contents}`, `{x.area}`, `{x.room}` | property, list of visible contents, area name, room name |
| `{beat.title}`, `{beat.area}`, `{beat.<role>}`, `{beat.<role>.name}`, `{beat.hint}`, `{beat.hook}` | the current beat (or the beat being described) |
| `{next.*}`, `{prev.*}` | the next / previous beat |
| `{role.<name>}` | a role entity |
| `{var.x}`, `{clock}`, `{args}`, `{story}`, `{string.key}` | globals |
| `{name}` | a local variable (an entity stored in a local renders as "the <name>"; use `{name.name}` for the bare name) |
| `{=expression}` | computed value |

---

## 13. Grammar: generating novel text

The `grammar` section defines symbols. Text containing `#symbol#` picks a random expansion,
recursively:

```json
"grammar": {
  "forest_name": ["#forest_adj.title# #forest_place.title#", "The #forest_adj.title# Wood"],
  "forest_adj": ["mossy", "shadowed", "silent"],
  "forest_place": ["glade", "thicket", "hollow"]
}
```

Modifiers: `.cap`, `.title`, `.upper`, `.lower`, `.a` ("an owl"), `.s` (plural), `.the`.
`[name:#symbol#]` picks once and remembers it, so `#name#` repeats the same choice within the same
feature. Names, descriptions and props are expanded **once** when a feature is created, so each
instance is fixed but unique. Runtime text (`say`) is expanded every time it is shown.

Mods share grammar: if two mods both define `given`, names from both are used. Add words to another
mod's vocabulary just by defining the same symbol.

---

## 14. Directions, strings and settings

**Directions** are data too:

```json
"directions": {
  "north": {"aliases": ["n"], "opposite": "south", "weight": 2},
  "up":    {"aliases": ["u"], "opposite": "down", "auto": false},
  "fore":  {"aliases": ["f"], "opposite": "aft", "default": false}
}
```

`auto: false` means the generator never assigns it (authored exits only). `default: false` means
it is only used where a region/area lists it in `directions`. Where two direction systems meet,
each side keeps its own and the far side gets an exit named after its destination.

**Strings** are every piece of interface text. Override any of them in your own `strings` section.
See `mods/core/strings.json` for the full list (for example `exits_line`, `not_here`, `inventory`,
`default_lead`, `gate_blocked`, `default_hook`, `ignore_words`).

**Settings** tune generation:

| Setting | Default | Meaning |
| --- | --- | --- |
| `default_structure` | `["opening","middle*","climax"]` | story structure without a premise |
| `max_middle_beats` | 4 | cap for `middle*` |
| `path_length` | `[2,4]` | filler rooms between areas (before size scaling), if a region gives none |
| `filler_distance`, `direct_distance` | `[1,3]`, `[3,6]` | exit distances |
| `branch_chance`, `loops` | 0.35, `[1,3]` | dead-end branches and extra loops |
| `scatter_chance`, `encounter_chance` | 0.45, 0.25 | per generated room |
| `rumour_chance` | 0.5 | chance of a second rumour-carrier per beat |
| `max_side_areas` | 12 | optional areas to attach |
| `sandbox_size` | `[10,16]` | rooms in a story-less, area-less world |
| `time_per_distance` | 1 | clock units per unit of distance |
| `auto_lead` | true | print the next beat's lead when one completes |
| `directions` | all default | directions available to the generator everywhere |

---

## 15. Working with other mods

* **Soft references.** Spec ids, `extends` and actions for verbs that aren't loaded are silently
  skipped, so you can enrich your content when another mod is present without requiring it.
  Example: The Barrow's wight `extends: ["scenery", "hostile"]`, so it fights only if Steel & Peril
  is loaded.
* **`{"mod": "id"}` conditions** branch on what's loaded (the hamlet priest's blessing raises max
  health only with Steel & Peril).
* **Tags, not ids.** Ask for `pick_tag`, `find: {"tag": ...}`, `area: {"tags": [...]}`, `habitat`.
  Then any mod can supply the thing. The Spire's victory needs *any* `relic`: it finds the Barrow's
  if present, and otherwise hides its own.
* **Hooks between chapters.** Use `{next.hook}` and `{"lead": true}` in your characters' dialogue so
  they point at whatever chapter comes next, from whichever mod.
* **Patching.** `load_after` the mod you patch and use `"_patch": true`. Steel & Peril gives the
  core player health and makes core `edible` things heal.

---

## 16. Testing your mod

```bash
./patchwork.sh --validate --mods my_mod,wilds         # static checks plus 20 generated worlds
./patchwork.sh --map --mods my_mod,wilds --seed 3     # full layout, roles, hidden items
./patchwork.sh --script walkthrough.txt --mods my_mod,wilds --seed 3
```

`--validate` prints *notes* for soft references (usually fine) and *warnings* for real problems:
unknown rooms in exits, unreachable rooms, missing grammar symbols, roles that spawn unknown
features, and so on. Lines starting with `#` in a script are ignored, and numbers answer `choice`
menus.

---

## 17. Worked example: The Drowned Lighthouse

`examples/lighthouse/` is a complete mod you can copy. It adds:

* an **area** (`lighthouse`) of three rooms joined by authored exits (`north`, `up`), with one
  room whose description changes once the lamp is lit;
* a **region** (`coast`) of generated shore rooms, which the generator picks to approach it
  because the area's `theme` includes `coast`;
* a **beat** (`lighthouse_relight`, stage `middle`) whose role `keeper` is *found* in the area,
  whose `hook` lets the village elder from Hearthside Hamlet send you there, whose `rumor` is given
  to travellers on the way, and whose `objective` is a flag;
* **features**: a keeper with conditional dialogue, an oil cask (container) holding a can of oil,
  and a great lamp with two ways to light it (`light lamp` while carrying oil, or
  `put oil in lamp` via `put_with`).

Try it:

```bash
./patchwork.sh --mod-dir examples --mods lighthouse,wilds,hamlet,barrow,spire,saga_waning_light --map --seed 8
```

The saga premise's `middle*` slot now holds two chapters, the barrow and the lighthouse, in an order
chosen per world, with the spire still the finale. That is the whole idea of Patchwork: you write a
self-contained piece, and the generator finds it a place in everyone else's story.
