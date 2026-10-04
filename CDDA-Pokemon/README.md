# Pokémon Overhaul for Cataclysm: Dark Days Ahead (0.I "Ito")

A content mod that brings the 151 original Pokémon into the Cataclysm. You can catch them, train
them, evolve them and fight alongside them. It also adds Kanto landmarks, Gym Leaders, Team Rocket,
Professor Oak and three mission lines.

Built and load-tested against the CDDA `0.I-branch` (tag `cdda-0.I-2026-09-19-2324`).

## Installing

1. Copy the `pokemon_overhaul` folder into your game's `data/mods/` folder (or your user `mods/` folder).
2. When creating a world, enable **Pokémon Overhaul** in the mod list. It depends only on the core
   `dda` content.
3. Optional: pick the **Pokémon Journey** scenario to start inside Professor Oak's lab. Any other
   scenario works too. Oak's lab is placed near a town on every map.

## What's in it

### All 151 Pokémon
* Every Kanto Pokémon from Bulbasaur to Mew. Stats come from their Generation I base stats: HP, speed,
  melee skill, dodge, armor and move power.
* 15 Pokémon types are real damage types. A full type chart is applied in combat: super effective
  hits deal double damage (quadruple when both types are weak), resisted hits are halved, and the
  immunities work (Ghost vs Normal/Fighting, Ground vs Electric, Flying vs Ground, Normal vs Ghost).
* 45 attacking moves (three tiers per type, unlocked at levels 1, 18 and 36) plus status moves:
  Thunder Wave, Sleep Powder, Hypnosis, Sing, Confuse Ray, String Shot and Poison Powder. Status
  conditions are paralysis, sleep, freeze, burn, poison, slow and confusion.
* Wild Pokémon live in forests, fields, rivers, ponds, swamps, the coast, caves, sewers and town
  streets. They have their own faction. Most leave you alone unless provoked, but aggressive species
  (Beedrill, Spearow, Primeape, Gyarados, Tauros…) will attack.

### Capturing
* Activate a **Poké Ball**, **Great Ball**, **Ultra Ball**, **Safari Ball** or **Master Ball** to throw it at a
  Pokémon up to 6 tiles away. The ball is used up either way.
* Catch chance depends on the species' catch tier (common, uncommon, rare or legendary), the target's
  remaining HP, the ball, and any status condition. Sleep and freeze count most. Weaken Pokémon first!
* A caught Pokémon becomes your permanent pet. It follows you and fights for you. You also receive
  its **registered Poké Ball**, which uses CDDA's pet-carrier mechanics: activate it next to your
  Pokémon to recall it, and activate it again to send it out.
* Trainers' Pokémon can't be caught.

### Training, levels and evolution
* Every Pokémon has a level (1–100). Wild ones roll a level that fits their species.
* Your Pokémon earn experience for the damage they deal to anything hostile, zombies included, with a
  bonus for knockouts. Levels make them faster, more accurate and harder hitting, make their moves
  stronger, and unlock new moves.
* Talk to one of your Pokémon (examine it, then chat) to see its level and experience, check its
  condition, or run an hour-long training session every 6 hours.
* **Evolution** happens automatically at the canonical level. Stone evolutions use the **Fire / Water /
  Thunder / Leaf / Moon Stones**. The four trade evolutions (Kadabra, Machoke, Graveler, Haunter) use
  a **Link Cable**. Eevee evolves into Vaporeon, Jolteon or Flareon depending on the stone.
* **Rare Candy** raises a level instantly.
* **Fainting:** the first time one of your Pokémon is knocked out, it faints instead of dying. A
  fainted Pokémon can't act. Recall it and use a **Revive**, or take it to a Pokémon Center. If it takes
  another hit while fainted, it dies for good.

### Items
Poké Balls (5 kinds), registered Poké Balls, Potion, Super/Hyper/Max Potion, Revive, Max Revive,
Full Heal, Full Restore, Rare Candy, the five evolution stones, Link Cable, Pokédex (scans a Pokémon's
level, HP and experience), the 8 Gym badges and a badge case, Poké Food, Helix/Dome Fossils and Old
Amber, the Silph Scope, Team Rocket orders, Oak's Parcel and a Pokédex diploma. Poké Balls and medicine
also turn up as loot.

### Locations
| Location | What's there |
| --- | --- |
| Professor Oak's Lab | Professor Oak: starter Pokémon, Pokédex, free Poké Balls, fossil revival, the main mission line |
| Pokémon Center (several per map) | Nurse Joy heals all your Pokémon; her Chansey; Officer Jenny; Team Rocket grunts nearby |
| Poké Mart (several per map) | A shopkeeper selling balls, medicine and stones |
| 8 Gyms | Pewter, Cerulean, Vermilion, Celadon, Fuchsia, Saffron, Cinnabar and Viridian, each themed to its leader's type |
| Indigo Plateau | The Champion, Gary Oak |
| Rocket Game Corner and Hideout | Team Rocket grunts and their executive, Archer |
| Safari Zone | Rare Pokémon and the Safari warden, who sells Safari Balls |
| Pokémon Tower | Ghost Pokémon and Cubone |
| Mt. Moon | Clefairy, Zubat and Geodude; fossils and the Moon Stone |
| Power Plant | Zapdos and Electric Pokémon |
| Seafoam ice cave | Articuno and Water/Ice Pokémon |
| Mt. Ember | Moltres and Fire Pokémon |
| Sealed cave | Mewtwo |

Mew wanders the forests very rarely.

### NPCs and battles
Gym Leaders (Brock, Misty, Lt. Surge, Erika, Koga, Sabrina, Blaine, Giovanni), the rival/Champion Gary,
Team Rocket grunts and Archer all fight **Pokémon battles**. Talk to them with one of your Pokémon out
and challenge them. They send out their team at the canonical levels, and your Pokémon fight theirs.
When their team is down, talk to them again to claim your win, badge and prizes. You can forfeit to
recall their team, and you can ask for a tougher rematch any time to train. Gyms enforce badge
requirements, and Giovanni won't fight until Team Rocket's hideout is cleared. Rocket grunts can also
just be fought the CDDA way.

### Missions
* **Professor Oak:** deliver Oak's Parcel, then register 5 / 15 / 40 / 80 / 151 species. Also the
  Pokémon League line (all eight gyms in order, then the Champion), the legendary birds, and Mewtwo.
* **Nurse Joy:** bring bandages, then antibiotics, then clear 25 zombies around the Center.
* **Officer Jenny:** recover Team Rocket's orders, raid the Rocket Hideout, then defeat Giovanni.
* **Safari warden:** register Chansey, Kangaskhan and Tauros.

Mission targets are marked on your map, and the locations are generated if they don't exist yet.

## Editing / regenerating

Most of the JSON is generated from tables so it stays consistent:

```
python3 tools/generate.py        # Pokémon, moves, evolutions, Pokédex, type chart, spawns
python3 tools/generate_world.py  # NPCs, trainer battles, missions, maps, scenario
```

* `tools/pokedex_data.py` holds the species table: stats, types, evolutions, habitat, rarity and
  descriptions.
* Files ending in `_gen.json` are generated, so edit the scripts rather than these files.
* The rest of the files are handwritten: capture, items, effects, battle EOCs and the partner dialogue.

## Testing

`tests/pokemon_overhaul_test.cpp` is a Catch2 suite that runs inside the real game engine. Copy it
into a CDDA 0.I checkout's `tests/` folder, build `cata_test`, symlink the mod into `data/mods/`, and run:

```
./tests/cata_test --mods=dda,pokemon_overhaul "[pokemon_overhaul]"
```

It covers: all 151 species loading; capture odds (Master Ball, weakened vs. healthy, trainer
Pokémon blocked); wild level rolls and Pokédex registration; experience and level-ups from damage;
Rare Candy; level, stone, Eevee and Link Cable evolutions; the type chart (2×, ½×, 4× and
immunities); fainting, Revive and death on a second knockout; move power scaling and level-gated
moves; Oak's starter; a full gym battle from challenge to badge, including badge requirements; and
Pokémon Center healing. The vanilla `overmap_terrain_coverage` test also passes with the mod loaded.
That test generates overmaps, checks that every new location spawns, and runs its mapgen.

## Known limitations
* Pokémon battles are real-time CDDA combat, not turn-based. Your Pokémon pick their own moves.
* Gym battles run on the honor system. Nothing stops you from shooting a Gym Leader's Onix.
* Registered Poké Balls use the vanilla pet-carrier code. That code can also stuff a weakened hostile
  creature into the ball, but it stays hostile when released.
* No tileset sprites. Pokémon use ASCII letters, colored by species.

Pokémon is © Nintendo / Creatures Inc. / GAME FREAK inc. This is a non-commercial fan mod.
