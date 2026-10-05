# Patchwork

A mod-oriented text RPG for the terminal. **The game has no world and no story of its own.**
When you start a new game you pick a collection of mods, and Patchwork weaves a world and a story
out of everything in them. Hand-made places, characters and plot from different mods are stitched
together, and novel generated content fills the gaps: wilderness between towns, travellers on the
road, generated names, scattered items, random encounters and events.

```
~ The Barrow's Heart ~
Somewhere ahead lies the Barrow of Eadgar the Grey. Whatever is calling from it,
the answer lies in its deepest chamber.

> search bones
Searching the pile of bones, you discover a key of carved bone.
```

## Requirements

* Linux (developed for Linux Mint, x86-64; any OS with Python works)
* Python 3.8 or newer. Linux Mint already ships with it, so nothing to install.
* No third-party packages.

## Running it

```bash
cd Patchwork
./patchwork.sh            # or: python3 -m patchwork
```

From the main menu choose **New game**, then:

1. **Pick your mods.** Toggle them by number. Required dependencies are added for you, and mods
   that work well with your choice are suggested.
2. **Pick a tale**, if more than one of your mods offers a story premise. You can also pick
   "No story - just explore".
3. **Pick a world size.** Bigger worlds have more generated country between places.
4. Optionally give a **seed**: the same mods and seed always weave the same world.
5. Optionally name your **character**. Leave it blank to get a generated name.

Useful command-line options:

| Option | Effect |
| --- | --- |
| `--mods core,wilds,hamlet` | skip the menus and start a new game with these mods |
| `--seed 42` / `--size large` / `--premise waning_light` / `--name Wren` | generation options |
| `--list-mods` | list every mod found |
| `--validate [--mods ...]` | check mods for mistakes and generate 20 test worlds |
| `--map --mods ... --seed N` | print a generated world's full layout (a spoiler map for mod authors) |
| `--script commands.txt` | play a list of commands non-interactively |
| `--mod-dir PATH` | look for mods in another folder too (repeatable) |
| `--no-color` | plain output |

## Playing

Type commands in plain English. Everything below comes from the **Core Rules** mod (other mods add
more), so type `help` in game to see the real list.

* `look`, `examine lantern` (`x lantern`), `search`, `search the log`
* `north` / `n`, `go ladder`, `go to village green` (multi-leg travel to anywhere you've been)
* `take all`, `drop knife`, `put coin in box`, `inventory` (`i`)
* `open chest`, `unlock door with key` (or just `unlock door` if you carry the key), `light torch`
* `talk to innkeeper` (choose numbered replies), `give apple to pilgrim`, `use horn on sorcerer`
* `read`, `eat`, `drink`, `push`, `pull`, `listen`, `smell`, `wait`, `journal` (`j`)
* With **Steel & Peril**: `attack wolf with sword`, `status`, `rest`

Built-in game commands: `save [name]`, `load [name]`, `map`, `story`, `mods`, `verbose`, `brief`,
`again` (`g`), `help`, `quit`.

Exits list a **distance**. Travelling takes time in proportion to distance, and mods hook into
travel: ambient events, healing on the road, random encounters, the day/night cycle.

Saves are stored in `~/.local/share/patchwork/saves/`. A save holds the whole woven world, so it
loads even if you later change your mods.

## Bundled mods

| Mod | What it adds |
| --- | --- |
| **Core Rules** (`core`) | All the basic verbs, reusable traits (portable, container, door, lockable, person, edible...), compass directions and every line of interface text. No places, no story. |
| **The Wilds** (`wilds`) | Generated forest, hills, river, marsh and road regions; trees with nests and hollows, streams, berry bushes, signposts; forage and lost trinkets; travellers who pass on rumours; travel events. |
| **Hearthside Hamlet** (`hamlet`) | A village start area (inn, smithy, chapel, elder's cottage) with dialogue trees, and an opening story beat that hands off to whatever chapter comes next. |
| **The Barrow of Kings** (`barrow`) | A dungeon with a hidden key, a locked bronze door and a sarcophagus. A middle story beat whose relic gets a generated name. |
| **The Sorcerer's Spire** (`spire`) | A climactic tower and final story beat. It uses a relic found earlier in your story from *any* mod, or hides its own if none exists. |
| **Saga: The Waning Light** (`saga_waning_light`) | A fantasy premise: intro, ending and starting kit. Threads the beats above into one tale. |
| **Steel & Peril** (`combat`) | Health, attacking, death, healing food, resting. Makes creatures from other mods fight back and adds wolves, bandits, bog lurkers (and rogue drones on space stations) to matching regions. |
| **Turning Days** (`daycycle`) | A day/night cycle made entirely of rules, plus a `time` command. |
| **Derelict: Station Kestrel** (`derelict`) | A complete science-fiction set: its own premise, ship directions (fore/aft/port/starboard), station regions, three areas and a three-part story. Proof that nothing in the engine is fantasy-specific. |

`examples/lighthouse` is the worked example from the modding guide. Try it with
`./patchwork.sh --mod-dir examples`.

Some combinations to try:

* `core, wilds`: an endless generated wilderness, no story.
* `core, wilds, hamlet, barrow, spire, saga_waning_light, combat, daycycle`: the full fantasy tale.
* `core, derelict, combat`: the science-fiction tale.
* Everything at once: the chosen premise drives the story, and every other place is still stitched into the world.

## Writing mods

Everything is JSON: no code. See **[MODDING.md](MODDING.md)** for the complete guide and reference.
Put your mods in `Patchwork/mods/` or `~/.local/share/patchwork/mods/`, then run
`./patchwork.sh --validate --mods yourmod` to check them.

## Project layout

```
Patchwork/
  patchwork.sh          launcher
  patchwork/            the engine (Python standard library only)
    mods.py             mod discovery, dependency ordering, merging and patching
    world.py            entities (rooms and nested features), definitions, save format
    logic.py            the JSON condition / effect / template / expression language
    generator.py        world and story weaving
    describe.py         builds descriptions from nested features
    engine.py           parser, verb dispatch, travel, turns and story progress
    cli.py, ui.py       menus and terminal I/O
    validate.py         mod checker
  mods/                 the bundled mods
  examples/lighthouse/  the tutorial mod
  tests/                unit tests and full-story playthroughs on many seeds
```

Run the tests with `cd tests && python3 -m unittest`.
