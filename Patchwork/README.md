# Patchwork

A mod-oriented text RPG for the terminal. **The game has no world and no story of its own, and
neither do the mods.** Mods supply building blocks: places built as rooms of nested features,
characters with personalities, motives, goals and secrets, items and what they can be used for,
locks and obstacles, events that could befall a world, and snippets of lore. When you start a new
game you pick a collection of mods, and Patchwork generates a world, a story, its lore and its
quests out of all of them, filling the gaps with novel content: wilderness between places,
generated names, travellers with rumours, scattered items, random encounters.

Every feature a mod marks as **important** (an item, a character, a place) is woven into the main
quest, so with every mod enabled everything is part of the game. Play the same mods twice and you
get a different story: another event, another cast, another chain of keys, favours and hiding
places.

```
THE QUIET MACHINE
... When you dock, the station's AI, WARDEN, greets you politely and asks you to
remain exactly where you are.

~ A favour for Chief Engineer Kwame Moreau ~
Chief Engineer Kwame Moreau in the Cargo Hold will give you the command keycard in
exchange for the fusion coupling.

> give medkit to dr ines tanaka
"Oh, the medkit! Bless you. Thank you so much."
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
2. **Pick a world size.** Bigger worlds have more generated country between places.
3. Optionally give a **seed**: the same mods and seed always weave the same world and story.
4. Pick **where you begin** from the starting points your mods offer (the village inn, the docking
   ring, a crossroads in the wilds, the Black Mesa tram...), or press Enter to let the story decide.
   The story fits the start: begin at the docking ring and you answer the station's distress
   beacon; begin in the village with Half-Life loaded and the sky may split open in green light.
5. Optionally name your **character**. Leave it blank to get a generated name. Everyone, Black
   Mesa's scientists included, calls you by it.

The story is generated from your mods; there is nothing to choose. The opening tells you what has
happened and what you must do, and `journal` always shows the current step.

Useful command-line options:

| Option | Effect |
| --- | --- |
| `--mods core,wilds,hamlet` | skip the menus and start a new game with these mods |
| `--seed 42` / `--size large` / `--name Wren` | generation options |
| `--list-mods` | list every mod found |
| `--start hl_blackmesa` / `--list-starts` | choose a starting point, or list them |
| `--validate [--mods ...]` | check mods for mistakes and generate 20 test worlds |
| `--map --mods ... --seed N` | print a generated world's story, cast, quest steps and full layout (spoilers, for mod authors) |
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
* `talk to innkeeper` (characters tell you what the story needs from them, then offer a menu:
  who they are, what they want, the lore they know, advice, small talk)
* `give apple to pilgrim`, `use keycard on blast door`, `put coupling in socket`
* `read`, `eat`, `drink`, `push`, `pull`, `listen`, `smell`, `wait`, `journal` (`j`), `lore`
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
| **Core Rules** (`core`) | All the basic verbs, reusable traits (portable, container, door, lockable, person, edible...), compass directions, every line of interface text and the story generator's vocabulary (quest titles, personality-flavoured dialogue). No places, no story. |
| **Storyteller's Almanac** (`tales`) | Setting-neutral events (a theft, a blight, a disappearance) that cast whatever your other mods provide, so any combination can grow a story. |
| **The Wilds** (`wilds`) | Generated forest, hills, river, marsh and road regions; nested natural features; forage and trinkets; hermits and herb-wives with profiles; travellers with rumours; travel events; lore on waystones. |
| **Hearthside Hamlet** (`hamlet`) | A village start area whose villagers each have a personality, motives, goals and wants, so they can be quest-givers, informants, victims or villains. An important holy well and saint's bell, and village lore. |
| **The Barrow of Kings** (`barrow`) | A dungeon with an important relic (with a generated name) and bone key, a guardian with a profile, a bronze door and rune-sealed coffer as obstacles, barrow lore, and two events: a stolen relic and a restless guardian. |
| **The Sorcerer's Spire** (`spire`) | A tower that drinks the light, a sorcerer driven by power and darkness, an orb, a star-glass shard, a shadow ward that any light-giving item can break, and an "eclipse" event. Only appears if the story needs it. |
| **Derelict: Station Kestrel** (`derelict`) | A science-fiction set: station areas and regions with ship directions, the AI WARDEN, a doctor, an engineer and a quartermaster with full profiles, card readers, keypads and dead lifts, station lore, and three events (rogue AI, saboteur, outbreak). |
| **Steel & Peril** (`combat`) | Health, attacking, death, healing food, resting. Makes creatures from other mods fight back (so some villains can be defeated in battle) and adds wolves, bandits, bog lurkers and rogue drones to matching regions. |
| **Turning Days** (`daycycle`) | A day/night cycle made entirely of rules, plus a `time` command. |
| **Black Mesa: Core** (`hl_core`) | Shared Half-Life content: every weapon from the crowbar to the displacer cannon, HEV/PCV armour with suit power, batteries, health and HEV chargers, crates, every creature and person from Half-Life, Opposing Force and Blue Shift, generated Black Mesa offices, labs, maintenance and transit, the desert surface, military camps, Xen and Race X hives, and locked doors for the map generator. Adds `where` (map and chapter) and `suit`. |
| **Half-Life** (`hl_halflife`) | The Half-Life campaign map by map, c0a0 to c5a1 plus the Hazard Course: the tram ride, Anomalous Materials and the resonance cascade, Blast Pit's tentacles, Power Up, On a Rail, Apprehension, Questionable Ethics, Surface Tension, Lambda Core, Xen, the Gonarch, Interloper, the Nihilanth and the G-Man's offer. Starts: a research associate on the inbound tram, or the Hazard Course. |
| **Opposing Force** (`hl_opfor`) | Gearbox's expansion, of0a0 to of6a5 plus Boot Camp: the Osprey crash, Otis, the Black Ops, Race X, the barnacle grapple and displacer, the Pit Worm, Foxtrot Uniform, the nuke and the Gene Worm. Starts: a HECU corporal on the Osprey, or Boot Camp. |
| **Blue Shift** (`hl_blueshift`) | Gearbox's Blue Shift, ba_tram1 to ba_outro plus security training: the falling elevator, the canals, the freight yard and Dr. Rosenberg, the Xen relay and the prototype teleporter. Starts: a security guard on the outbound tram, or security training. |

`examples/lighthouse` is the worked example from the modding guide. Try it with
`./patchwork.sh --mod-dir examples`.

The Half-Life mods follow the original maps closely (each room records its BSP map code and
chapter; type `where`), condensing long maps to their memorable spaces. Locked doors and outdoor
areas grow generated sections, so every Black Mesa is a little bigger than the last, and the
story generator turns each campaign's set pieces and important gear into quests: load all three
and the scientist may need something from the security guard's freight yard. Black Mesa also
meshes with other mods' worlds: where its science fiction meets a fantasy mod's country, the
generator puts a seam between them (a portal storm, a rift scar, a chunk of displaced Black Mesa
floor, or the Storyteller's Almanac's misty Strange Mile), Xen wildlife only spills out through
those rifts, crossover lore turns up (the night the village sky turned green), and from any other
start the *Incursion* story can lead you back through the rifts to the Nihilanth or the Gene
Worm. *Decay*, the PlayStation 2 co-op
expansion, is not included. The Half-Life JSON is generated from compact specs in
`tools/halflife/` (`cd tools/halflife && python3 build.py`).

Some combinations to try:

* `core, wilds`: an endless generated wilderness, no story.
* `core, derelict`: play it twice, and you may be facing a rogue AI, a saboteur or an outbreak, with
  the crew in different roles and the keys, codes and couplings in different hands.
* `core, tales, wilds, hamlet, barrow, spire, combat, daycycle`: fantasy stories built from every piece.
* `core, tales, hl_halflife, hl_opfor, hl_blueshift`: Black Mesa three ways: start as a scientist,
  a marine or a guard.
* `core, tales, wilds, hamlet, hl_halflife`: start in the village and follow the rifts.
* Everything at once: one story that uses every important feature of every mod.

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
    generator.py        world generation and layout
    story.py            story generation: events, casting, quest planning, dialogue, lore
    describe.py         builds descriptions from nested features
    engine.py           parser, verb dispatch, travel, turns and story progress
    cli.py, ui.py       menus and terminal I/O
    validate.py         mod checker
  mods/                 the bundled mods
  examples/lighthouse/  the tutorial mod
  tools/halflife/       Python specs that generate the Half-Life mods' JSON
  tests/                unit tests, and an automated player that finishes generated stories
                        through the text parser on many seeds and mod combinations
```

Run the tests with `cd tests && python3 -m unittest`.
