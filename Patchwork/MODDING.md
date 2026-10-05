# Patchwork Modding Guide

Everything a player sees in Patchwork comes from mods: places, characters, items, verbs, rules,
the raw material of stories, even the words "You can't go that way." A mod is a folder of JSON files. There is no code to
write: behaviour is described with small JSON conditions and effects that the engine interprets.

* [1. Quick start](#1-quick-start)
* [2. How a world is woven](#2-how-a-world-is-woven)
* [3. Mod folders and mod.json](#3-mod-folders-and-modjson)
* [4. Merging, overriding and patching](#4-merging-overriding-and-patching)
* [5. Features: the nested building block](#5-features-the-nested-building-block)
* [6. Rooms and exits](#6-rooms-and-exits)
* [7. Areas: hand-made places](#7-areas-hand-made-places)
* [8. Regions: generated in-between places](#8-regions-generated-in-between-places)
* [9. Story building blocks](#9-story-building-blocks) (important features, character profiles, events, obstacles, lore)
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

No mod contains a story. Mods contribute *building blocks*, and every new game the generator
invents a plot, a cast, a quest chain and the lore to go with them:

1. **Load.** The selected mods (plus their requirements) are sorted into load order and merged into
   one *registry* (section 4).
2. **Take inventory.** The story planner lists every character (a feature with a `profile`), every
   item that `affords` something, everything marked `important` (items, characters, fixed features
   and areas), every `obstacle` and every `event` the loaded mods offer.
3. **Choose and cast an event.** An event is a situation, such as "the station AI goes rogue" or
   "something precious was stolen", with *roles* to fill: a character whose motives fit, a place
   with certain tags, an item that affords something. Events are weighted towards the ones that can
   use the most important features, and each role is cast from whatever matches in *any* mod.
   One of the event's *resolutions* becomes the finale.
4. **Plan backwards from the finale.** The finale needs its means (say, a power coupling). The
   planner decides how the player gets it, and each answer can need something else in turn:
   * it lies somewhere: in an important place, or out in the wilds where it would naturally be;
   * a character holds it, and hands it over when asked, or in return for a favour, an item they
     `want`;
   * it is locked in a container, or the area it is in sits behind a barrier: an **obstacle** whose
     key is an item that affords what the obstacle `needs`;
   * a character who knows where it is can be asked first.
   The planner keeps choosing **important** features to fill these jobs, and afterwards weaves any
   important feature still unused into the chain: as the key to a place the story needs, a gift for
   a character, an informant, a place to investigate, or a feature to examine. Every important
   feature ends up in the main quest.
5. **Lay out the spine.** The order in which the plan opens up areas becomes the map's spine: the
   start area first, then each area in story order, each with a *stage* number.
6. **Stitch.** Consecutive spine areas are joined by generated **filler rooms** from **regions**.
   Regions are chosen by how well their tags match the two areas' themes, and a path may change
   region halfway (road into forest into marsh).
7. **Side content.** Every other area is attached as a side area, and filler rooms sprout branches
   and loops, scaled by world size.
8. **Populate.** Features tagged `scatter` and `encounter` are placed in generated rooms whose
   tags match their `habitat`.
9. **Bind the story.** Everything is placed. Obstacles are built and their keys wired up. Every
   character's quest dialogue is written in the voice of their personality, and they get a
   conversation menu: who they are, what they want, the lore they know, advice, small talk. Lore
   from the mods is mixed with event-specific lore and spread through dialogue and documents.
   Travellers on the roads pass on hints.

During play the current step's objective is checked after every command. Steps complete in any
order the player manages: if you already hold the thing a step asks for, it completes at once.
If a character a step needs is killed, the step settles itself rather than becoming impossible.

The same mods with a different seed give a different story: another event, another cast, another
chain of keys, favours and hiding places, other lore.

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

`features`, `rooms`, `areas`, `regions`, `events`, `obstacles`, `lore`, `verbs`, `rules`,
`macros`, `directions`, `grammar`, `strings`, `settings`.

---

## 4. Merging, overriding and patching

All selected mods are merged in load order.

* **Id sections** (`features`, `rooms`, `areas`, `regions`, `events`, `obstacles`, `lore`, `verbs`,
  `rules`, `macros`, `directions`): an entry with the same id as an earlier one **replaces** it.
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
| `important`, `affords`, `home`, `profile` | Story building blocks: see section 9. |

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
| `solve` | Ignored by the engine. For a scripted gate (an `if` that a set piece opens), the steps an automated player takes to open it: `[["goto", "room id"], ["do", "push button"], ...]`. The test suite's player uses it. |

### 6.1 Expansions: the map generator off hand-built rooms

A hand-built room can grow generated sections of its own: a corridor of offices behind a locked
door, a canyon trail off a desert road. Each entry in a room's `expansions` list may (by `chance`)
add a spur of rooms from regions whose `tags` or `connects` match:

```json
"expansions": [
  {"tags": ["office", "lab"], "length": [2, 4], "chance": 0.8,
   "door": "bm_locked_door", "name": "locked door", "aliases": ["door"]},
  {"tags": ["surface"], "length": [2, 3], "name": "canyon trail"}
]
```

| Field | Meaning |
| --- | --- |
| `tags` | Region tags to grow from (section 8). |
| `length`, `distance` | How many rooms, and the distance of the first exit. Scaled by world size. |
| `chance` | Probability the expansion is built (default 1). |
| `dir`, `name`, `aliases`, `description` | The new exit. |
| `door` | An obstacle id (section 9.4) or an inline obstacle. Its `feature` is placed in the room and the exit stays shut until it opens. If the obstacle has `needs`, it opens for anyone carrying (or using on it) an item that `affords` one of them, so any crowbar opens any jammed hatch; without `needs` it just opens. |

Expansion rooms are side content: the story never puts quest steps behind these doors.

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
| `name` | Grammar allowed; available to text as `{area.<id>}` and `{self.area}`. |
| `tags` | `start` marks a possible starting area. Tags are also matched by event place roles, obstacles and items' `home`, and by region matching. |
| `theme` | Extra tags that steer which regions connect to this area. |
| `rooms` | Object of inline room definitions (ids are local, registered as `area/room`), or a list of global room ids. The list may use globs: `["hl/*"]` takes every room in the `rooms` section whose id starts with `hl/`. |
| `entrances` | Rooms that may be connected to the outside world (default: all rooms). |
| `start` | Starting room when this is the start area. |
| `room_tags` | Tags added to every room in the area. |
| `directions` | Directions the generator may use when connecting this area (section 14). |
| `important` | The main quest must take the player here (section 9.1). |
| `only_if_used` | Only build this area if the story uses it. |
| `no_story` | The planner never places story things here. |
| `include: false` | Never add it as side content. |
| `allow_scatter` | Let scatter/encounter features appear in its rooms. |
| `stage` | Upper bound for how deep into the story a side area may be attached. |
| `start_label` | Offers this area as a starting point. New games ask "Where do you begin?" and list every area with a label (Enter lets the story decide); `--start <area>` picks one and `--list-starts` lists them. |
| `player` | Who you are when you start here: `name`, `player_name` (skips the name prompt), `aliases`, `description`, `props`, `tags`. |
| `kit` | Feature specs given to the player when starting here. |

Rooms tagged `story_skip` are scripted scenes (a crash you wake up from, a void before the
credits). The planner never places quest things in them, never uses characters authored in them,
the generator never attaches new exits to them, and the validator doesn't flag them as
unreachable.

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

## 9. Story building blocks

### 9.1 Important features

Add `"important": true` to any feature (item, character, scenery) or area. The generator guarantees
the player must interact with every important thing that exists in the world as part of the main
quest. When all mods are enabled, all their important content is part of one story.

* **Items** become keys, favours, things to find, or the finale's means.
* **Characters** become quest-givers, holders, informants, people to help, victims or villains.
* **Places** become locations of story steps, or are investigated for clues.
* **Fixed features** (an orb, a well, a reactor socket) become a finale target or something to examine.

Mark only what matters. Everything else is still in the world, but optional.

Useful item fields for the planner:

| Field | Meaning |
| --- | --- |
| `affords` | What the item can be used for: `unlock`, `access`, `code`, `power`, `light`, `tool`, `medicine`, `cure`, `holy`, `relic`, `evidence`, `fuel`... Free-form; obstacles and characters' `wants` use the same words. |
| `home` | Tags of places where it would naturally be found (`["maintenance", "engineering"]`). The generator places it there, growing a region spur if needed. |
| `story_keep` | The player keeps it: the planner never asks you to give it away as a favour (weapons, suits). |

Important **monsters** (a character with a profile that is also `hostile`, from Steel & Peril)
are not questioned: unless they are the finale they become "defeat" steps, and before any fight
the story depends on, the planner makes sure you have picked up a weapon (an item tagged `weapon`).
A monster's `solve` list (commands such as `"attack healing crystal"`) tells automated players how
to soften it up first. Characters whose profile has `"menu": false` (and all hostile ones) get no
conversation menu; their own `talk` handlers speak for them.

### 9.2 Character profiles

Any feature with a `profile` is a character the story can use.

```json
"warden_core": {
  "name": "WARDEN", "proper": true, "important": true, "tags": ["ai"],
  "profile": {
    "personality": ["cold"],
    "motives": ["preserve", "control", "order"],
    "motive_text": "preserve the reactor, whatever happens to the crew",
    "goals": ["keep the reactor safe", "keep everyone exactly where they are"],
    "backstory": "\"I am WARDEN. I manage Kestrel's life support, power and personnel.\"",
    "roles": ["antagonist", "informant"],
    "knows": ["station", "reactor", "crew"],
    "wants": [],
    "greet": ["On every screen, WARDEN's blue eye turns to you. \"Hello. Please remain where you are.\""],
    "epilogue": ""
  }
}
```

| Field | Used for |
| --- | --- |
| `personality` | Chooses the voice of generated dialogue: `say_<kind>_<personality>` grammar (core has gruff, kind, nervous, cheerful, cold, cunning, weary, wise, stern). |
| `motives`, `motive_text` | Matched by event roles (`"match": {"motive": [...]}`); `{x.motive}` in text. Villains explain themselves with it. |
| `goals` | "What do you want?" in conversation; `{x.goal}`. |
| `backstory` | "Who are you?"; `{x.backstory}`. |
| `roles` | Which story jobs suit them: `antagonist`, `giver`, `informant`, `holder`, `ally`, `victim`, `authority` (default: everything except antagonist). |
| `knows` | Lore tags they can talk about. |
| `wants` | Affordances or tags of items they'd trade a favour for. |
| `greet`, `give`, `ask`, `thanks`, `info`, `meet`, `confront`, `motive`, `who`, `goal`, `bye`, `lore_intro` | Optional lines of their own, used instead of the generic voice. |
| `epilogue` | A line about their fate in the ending, if they helped. |

Characters you author into an area stay there (unless an event says `"relocate": true`); others
are placed by the generator, using `home` if given.

### 9.3 Events

An event is a situation that can befall the world, written with roles instead of fixed
characters, so it plays out differently with every cast.

```json
"events": {
  "derelict_rogue_ai": {
    "title": ["Dead Signal", "The Quiet Machine"],
    "tags": ["scifi", "station"],
    "roles": {
      "lair":    {"type": "place", "match": {"tags": ["engineering"]}},
      "villain": {"type": "character", "match": {"motive": ["preserve", "control"], "role": ["antagonist"]}},
      "heart":   {"type": "feature", "match": {"tag": ["reactor_heart"]}, "in": "lair", "spawn": "reactor_socket"},
      "power":   {"type": "item", "match": {"affords": ["power"]}, "spawn": "fusion_coupling"}
    },
    "hook": "... the station's AI, {villain}, greets you politely and asks you to remain exactly where you are.",
    "goal": "Restart the reactor in {lair} by fitting {power} into {heart}.",
    "resolutions": [
      {"verb": "put", "target": "heart", "means": "power", "title": "Restart the reactor",
       "text": "{means.The} locks home in {target} ..."}
    ],
    "consequences": [{"flag": "station_dark"}],
    "lore": [{"title": "Why the lights went out", "text": "{villain.The} shut the reactor down ..."}],
    "ending": "Your shuttle pulls away with the survivors ..."
  }
}
```

| Field | Meaning |
| --- | --- |
| `roles` | `type` is `character`, `item`, `place` or `feature`. `match` keys: `tags` (all), `any_tags`, `tag`, `affords`, `motive`, `personality`, `role`, `def`, `id`. `in` limits a feature to another role's place. `spawn` is the fallback if nothing in any mod matches. `optional` roles may stay empty. `relocate` moves an authored character away from home (a missing person). |
| `resolutions` | Ways to end it. `verb` (`use`, `put`, `give`, `light`, `talk`, `attack`...), `target` role, optional `means` role, `title`, `text`, `effects`, `requires_mods`. One is the planned finale; all valid ones work. `attack` needs the target to be a creature (Steel & Peril). |
| `hook`, `goal` | The opening text and the overall objective shown in the journal. |
| `title` | Story title (a list picks one). |
| `consequences` | Effects run when the game starts. |
| `lore` | Story-specific lore entries (section 9.5). |
| `ending` | Shown when the story completes, followed by epilogues of characters who helped. |
| `tags`, `weight`, `requires_mods` | Selection. Events whose tags match the loaded areas are preferred. |
| `start_areas` | The event belongs to these starting areas: it is only chosen when the game starts in one of them (and is strongly preferred there), and a story-decided start picks one of them. This is how one mod set offers several protagonists, each with their own stories. |

In text, role names are placeholders: `{villain}` renders "WARDEN" or "the barrow wight" (with the
right article), `{villain.The}` at the start of a sentence, `{villain.motive}` the profile's motive.
Place roles render as the area's name.

The **Storyteller's Almanac** mod provides setting-neutral events (a theft, a blight, a
disappearance) so any combination of places and characters can produce a story. With no events at
all, the generator still builds a quest out of the important features.

### 9.4 Obstacles

Obstacles are locks the planner puts in the player's way. A `barrier` blocks the way into an area
(it is placed in the room just before, and the exit is closed until it opens); a `container` holds
something the story needs.

```json
"obstacles": {
  "card_reader_door": {
    "kind": "barrier",
    "needs": ["access"],
    "tags": ["station", "scifi"],
    "key": "maintenance_keycard",
    "feature": {"name": "blast door", "aliases": ["door", "reader"],
                "appearance": [{"if": {"prop": "open"}, "text": "A blast door stands open."},
                               {"text": "A blast door seals the way on. The card reader blinks red."}]},
    "open_text": "You swipe {key}. The blast door grinds open.",
    "locked_text": "ACCESS DENIED, says the card reader.",
    "blocked": "The blast door is sealed."
  }
}
```

`needs` lists affordances; any item that `affords` one of them opens it (`use <key> on <obstacle>`,
or `open`/`unlock` while carrying it). The planner prefers important items as keys. `key` is a
fallback item to generate when no important item fits (limited to a couple per story). `tags`
restrict which places it suits; an obstacle with no tags suits anywhere. `consume: true` uses the
key up, and `verbs` adds extra verbs that open it.

### 9.5 Lore

```json
"lore": {
  "kestrel_warden": {"title": "WARDEN", "about": ["def:warden_core"], "tags": ["station", "reactor"],
                     "text": "WARDEN was installed to manage life support and the reactor..."}
}
```

`about` lists what must be in this world for the entry to exist: `def:<feature>`, `area:<area>`,
`tag:<tag>`, `event:<event>`, `cast:<role>` (and its placeholders become usable), `mod:<id>`.
`chance` makes it occasional. Grammar in the text makes each telling different.

Each game, the eligible lore is mixed with the chosen event's own lore. Characters share lore whose
tags match their profile's `knows` (in quest dialogue and as "Tell me about..." options), story
steps reveal it, and the rest is written into **lore carriers** (features tagged `lore_carrier`,
with a `habitat` such as data pads on a station or waystones in the wilds) scattered around the
world. Reading or hearing lore records it; the `lore` command reviews it.

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
| `story_complete` | The story's last step completed | |
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
| `role:name` | a member of the generated story's cast (`role:villain`) |
| `here:<matcher>` | first matching visible entity in self's room |
| `carried:<matcher>` | first matching thing the player carries |
| `near:<matcher>` | first matching thing the player can see or carry |
| `any:<matcher>` | first matching entity anywhere |
| `room:<id>`, `uid:<uid>` | by id |

### 12.2 Matchers (does an entity fit?)

* `"tag:key"`, `"def:barrow_key"`, `"role:relic"`, `"name:lantern"`, `"area:hamlet"`
* a bare word: a feature id **or** a tag
* `"affords:pry"`: an item that affords something
* an object combining tests: `{"tag": ["weapon"], "affords": ["pry"], "prop": "damage", "gte": 3, "not": "tag:cursed"}`
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
| `{"step_active": id}`, `{"step_done": id}`, `{"step_reached": id}`, `{"next_step": true}`, `{"story_complete": true}`, `{"flag": "story_resolved"}`, `{"lore_known": id}` | story state |
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
| `{"complete_step": id_or_true}`, `{"lead": true}` (show the current step's hint), `{"learn": lore_id}` | story control |
| `{"inherit": verb, "on": ref}` | run the definition's own handlers for a verb (the generated conversation menu uses it for "small talk") |
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
| `{step.title}`, `{step.hint}`, `{step.place}`, `{step.<ref>}` | the current story step |
| `{next.*}`, `{prev.*}` | the next / previous step |
| `{cast.<role>}`, `{role.<role>}` | a member of the story's cast |
| `{x.motive}`, `{x.goal}`, `{x.backstory}`, `{x.personality}` | from a character's profile |
| `{area.<id>}` | an area's generated name |
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
| `path_length` | `[2,4]` | filler rooms between areas (before size scaling), if a region gives none |
| `filler_distance`, `direct_distance` | `[1,3]`, `[3,6]` | exit distances |
| `branch_chance`, `loops` | 0.35, `[1,3]` | dead-end branches and extra loops |
| `scatter_chance`, `encounter_chance` | 0.45, 0.25 | per generated room |
| `rumour_chance` | 0.5 | chance of a traveller carrying each step's hint |
| `story_max_locks` | 3 | obstacles per story, plus one per important item that could be a key |
| `story_generic_locks` | 2 | obstacles whose key the generator invents |
| `lore_documents` | 5 | lore carriers to scatter (scaled by world size) |
| `max_side_areas` | 12 | optional areas to attach |
| `sandbox_size` | `[10,16]` | rooms in a story-less, area-less world |
| `time_per_distance` | 1 | clock units per unit of distance |
| `directions` | all default | directions available to the generator everywhere |

---

## 15. Working with other mods

* **Soft references.** Spec ids, `extends` and actions for verbs that aren't loaded are silently
  skipped, so you can enrich your content when another mod is present without requiring it.
  Example: The Barrow's wight `extends: ["scenery", "hostile"]`, so it fights only if Steel & Peril
  is loaded.
* **`{"mod": "id"}` conditions** branch on what's loaded (the hamlet priest's blessing raises max
  health only with Steel & Peril).
* **Describe, don't name.** Event roles match by motive, tags and affordances, never by id, so
  other mods' content can fill them. The Spire's eclipse can be broken by *anything* that affords
  `light`: its own star-glass shard, the Barrow's relic, the Hamlet's saint's bell, a flashlight
  from Derelict. A greedy innkeeper from one mod can be the thief in another mod's event.
* **Give characters full profiles.** The more motives, roles, wants and knowledge a character has,
  the more stories they can be cast in.
* **Use `{"lead": true}`** in authored dialogue to have a character point at whatever the current
  story needs.
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

`examples/lighthouse/` is a complete mod you can copy. It contains no story; just the pieces for one:

* an **important area** (`lighthouse`) of three rooms, one whose description changes once the
  story is resolved;
* a **region** (`coast`) of generated shore rooms, which the generator picks to approach it
  because the area's `theme` includes `coast`;
* a **character** (the keeper) with a profile: gruff and weary, motivated by duty, wants `fuel` or
  `food`, knows about the sea; usable as a quest-giver, informant, holder or victim in *any* event;
* **important features**: the great lamp (tagged `lamp_heart`) and a can of lamp oil that
  `affords` `fuel` and `light`, with `home` tags so it turns up somewhere sensible;
* an **event** (`dark_lamp`) whose roles are "a place tagged lighthouse", "a lamp feature in it" and
  "something that affords fuel", resolved by `light`ing the lamp while carrying the means;
* **lore** about the lighthouse.

Try it on its own, then mixed with everything else:

```bash
./patchwork.sh --mod-dir examples --mods core,lighthouse --map --seed 3
./patchwork.sh --mod-dir examples --mods core,tales,wilds,hamlet,barrow,spire,lighthouse --map --seed 8
```

Alone, it makes a short story about relighting the lamp. Mixed in, the lighthouse and its keeper
become part of someone else's story. The keeper might hold the key to the barrow, or the lamp oil
might be the light that breaks the sorcerer's ward, and when its own event is chosen, the other
mods' characters and places become part of the lighthouse's story. You write self-contained pieces;
the generator writes the story.
