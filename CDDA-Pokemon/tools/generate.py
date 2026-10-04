#!/usr/bin/env python3
"""
Generates the data-heavy JSON for the Pokémon Overhaul mod:

  monsters/pokemon_gen.json          all 151 Pokémon
  monsters/trainer_pokemon_gen.json  trainer-owned copies used by gym leaders / Team Rocket
  spells/moves_gen.json              battle moves (one set per type)
  spells/evolution_gen.json          evolution, level-init and Pokédex spells
  eocs/pokedex_gen.json              per-species Pokédex registration EOCs
  monstergroups/spawns_gen.json      habitat spawn groups + hooks into vanilla groups

Run from anywhere:  python3 tools/generate.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pokedex_data import POKEDEX  # noqa: E402

MOD_DIR = os.path.join(os.path.dirname(HERE), "pokemon_overhaul")

TYPES = ["normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison",
         "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon"]

# ---------------------------------------------------------------------------
# Moves.  tier 1 is known from the start, tier 2 from level 18, tier 3 from 36.
#   (id, name, description, base power, power per spell level, range, aoe,
#    shape, cooldown, status effect, status duration (moves), extra flags)
# ---------------------------------------------------------------------------
MOVES = {
    "normal": [
        ("quick_attack", "Quick Attack", "Lunges at the target at blinding speed.", 7, 0.4, 3, 0, "blast", 3, None, 0),
        ("body_slam", "Body Slam", "Slams the target with the full weight of its body.  May leave it paralyzed.", 14, 0.6, 1, 0, "blast", 7, "pkmn_paralysis", 300),
        ("hyper_beam", "Hyper Beam", "Fires a devastating beam of energy.  The user needs a long rest afterwards.", 26, 1.0, 8, 1, "line", 18, None, 0),
    ],
    "fire": [
        ("ember", "Ember", "Spits a small burst of flame that may leave the target burned.", 6, 0.4, 6, 0, "blast", 4, "pkmn_burn", 600),
        ("flamethrower", "Flamethrower", "Scorches the target with a stream of intense flame.", 13, 0.6, 7, 1, "line", 8, "pkmn_burn", 600),
        ("fire_blast", "Fire Blast", "An all-consuming blast of fire shaped like the character for 'big'.", 22, 1.0, 8, 1, "blast", 15, "pkmn_burn", 900),
    ],
    "water": [
        ("water_gun", "Water Gun", "Squirts a jet of water at the target.", 6, 0.4, 6, 0, "blast", 4, None, 0),
        ("bubble_beam", "Bubble Beam", "A spray of bubbles that may slow the target.", 12, 0.6, 7, 0, "blast", 8, "pkmn_slowed", 500),
        ("hydro_pump", "Hydro Pump", "Blasts the target with a huge volume of water at high pressure.", 22, 1.0, 8, 1, "line", 15, None, 0),
    ],
    "electric": [
        ("thunder_shock", "Thunder Shock", "A jolt of electricity that may paralyze the target.", 6, 0.4, 6, 0, "blast", 4, "pkmn_paralysis", 200),
        ("thunderbolt", "Thunderbolt", "A strong electric blast crashes down on the target.", 13, 0.6, 8, 0, "blast", 8, "pkmn_paralysis", 300),
        ("thunder", "Thunder", "A wicked thunderbolt is dropped on the target and everything near it.", 22, 1.0, 10, 1, "blast", 15, "pkmn_paralysis", 400),
    ],
    "grass": [
        ("vine_whip", "Vine Whip", "Strikes the target with slender, whiplike vines.", 6, 0.4, 3, 0, "blast", 3, None, 0),
        ("razor_leaf", "Razor Leaf", "Sharp-edged leaves are launched to slash at the target.", 12, 0.6, 7, 1, "line", 7, None, 0),
        ("solar_beam", "Solar Beam", "Gathers light, then blasts a bundled beam.", 22, 1.0, 9, 1, "line", 15, None, 0),
    ],
    "ice": [
        ("aurora_beam", "Aurora Beam", "Fires a rainbow-colored beam that chills the target.", 7, 0.4, 7, 0, "blast", 4, "pkmn_slowed", 300),
        ("ice_beam", "Ice Beam", "An icy beam that may freeze the target solid.", 13, 0.6, 8, 0, "blast", 8, "pkmn_freeze", 200),
        ("blizzard", "Blizzard", "A howling blizzard is summoned to strike everything near the target.", 21, 1.0, 8, 2, "blast", 15, "pkmn_freeze", 200),
    ],
    "fighting": [
        ("low_kick", "Low Kick", "A low, tripping kick.", 7, 0.4, 1, 0, "blast", 3, None, 0),
        ("karate_chop", "Karate Chop", "A sharp chop with a high chance of hitting something vital.", 13, 0.6, 1, 0, "blast", 6, None, 0),
        ("submission", "Submission", "Grabs the target and hurls it to the ground with immense force.", 23, 1.0, 1, 0, "blast", 12, "downed", 200),
    ],
    "poison": [
        ("poison_sting", "Poison Sting", "Stabs with a toxic barb that may poison the target.", 5, 0.4, 4, 0, "blast", 4, "pkmn_poison", 1200),
        ("acid", "Acid", "Sprays a hide-melting acid.", 11, 0.6, 6, 1, "blast", 7, "pkmn_poison", 900),
        ("sludge", "Sludge", "Hurls unsanitary sludge that badly poisons whatever it touches.", 20, 1.0, 7, 1, "blast", 13, "pkmn_poison", 1800),
    ],
    "ground": [
        ("bone_club", "Bone Club", "Clubs or flings a hard object at the target.", 7, 0.4, 3, 0, "blast", 4, None, 0),
        ("dig", "Dig", "Burrows underground, then strikes from below.", 13, 0.6, 5, 0, "blast", 8, None, 0),
        ("earthquake", "Earthquake", "A powerful quake that strikes everything around the target.", 21, 1.0, 5, 2, "blast", 15, None, 0),
    ],
    "flying": [
        ("gust", "Gust", "Whips up a gale of wind against the target.", 6, 0.4, 6, 0, "blast", 4, None, 0),
        ("wing_attack", "Wing Attack", "Strikes the target with wings spread wide.", 12, 0.6, 2, 0, "blast", 6, None, 0),
        ("sky_attack", "Sky Attack", "Climbs high and dives down on the target with tremendous force.", 23, 1.0, 8, 0, "blast", 15, None, 0),
    ],
    "psychic": [
        ("confusion", "Confusion", "A weak telekinetic attack that may leave the target confused.", 7, 0.4, 7, 0, "blast", 4, "stunned", 200),
        ("psybeam", "Psybeam", "A peculiar ray that may confuse the target.", 13, 0.6, 8, 0, "line", 8, "stunned", 300),
        ("psychic", "Psychic", "A strong telekinetic force crushes the target.", 23, 1.0, 9, 0, "blast", 14, None, 0),
    ],
    "bug": [
        ("leech_life", "Leech Life", "Bites into the target and drinks its fluids.", 6, 0.4, 1, 0, "blast", 3, None, 0),
        ("twineedle", "Twineedle", "Jabs the target twice with stinging barbs that may poison.", 11, 0.6, 3, 0, "blast", 6, "pkmn_poison", 600),
        ("pin_missile", "Pin Missile", "Fires a volley of sharp spikes at the target.", 20, 1.0, 7, 1, "blast", 12, None, 0),
    ],
    "rock": [
        ("rock_throw", "Rock Throw", "Picks up and throws a small rock at the target.", 7, 0.4, 6, 0, "blast", 4, None, 0),
        ("rock_slide", "Rock Slide", "Large boulders are hurled at the target and those around it.", 13, 0.6, 7, 1, "blast", 8, "downed", 100),
        ("stone_edge", "Stone Edge", "Stabs the target with sharpened stones.", 23, 1.0, 6, 0, "blast", 14, None, 0),
    ],
    "ghost": [
        ("lick", "Lick", "Licks with a long, ectoplasmic tongue.  May paralyze the target.", 5, 0.4, 1, 0, "blast", 3, "pkmn_paralysis", 300),
        ("night_shade", "Night Shade", "Makes the target see a frightening mirage that wounds the mind.", 13, 0.6, 7, 0, "blast", 8, None, 0),
        ("shadow_ball", "Shadow Ball", "Hurls a shadowy blob at the target.", 22, 1.0, 8, 0, "blast", 14, None, 0),
    ],
    "dragon": [
        ("twister", "Twister", "Whips up a vicious twister to tear at the target.", 7, 0.4, 6, 1, "blast", 4, None, 0),
        ("dragon_rage", "Dragon Rage", "A shock wave of draconic fury.", 15, 0.6, 7, 0, "blast", 8, None, 0),
        ("outrage", "Outrage", "Rampages and attacks with overwhelming fury.", 26, 1.0, 2, 1, "blast", 14, None, 0),
    ],
}

# Status moves: (id, name, description, range, cooldown, effect, duration)
STATUS_MOVES = {
    "electric": ("thunder_wave", "Thunder Wave", "A weak electric charge that paralyzes the target.", 6, 20, "pkmn_paralysis", 1000),
    "grass": ("sleep_powder", "Sleep Powder", "Scatters a big cloud of sleep-inducing dust.", 3, 25, "pkmn_sleep", 800),
    "psychic": ("hypnosis", "Hypnosis", "Hypnotic suggestion puts the target to sleep.", 5, 25, "pkmn_sleep", 800),
    "ghost": ("confuse_ray", "Confuse Ray", "A sinister ray that confuses the target.", 7, 20, "stunned", 600),
    "bug": ("string_shot", "String Shot", "Sprays silk to bind the target and slow it down.", 5, 15, "pkmn_slowed", 1000),
    "poison": ("poison_powder", "Poison Powder", "Scatters a cloud of toxic dust.", 3, 20, "pkmn_poison", 2400),
}
# Species that get Sing instead of whatever their typing would give them.
SINGERS = {"jigglypuff", "wigglytuff", "clefairy", "clefable", "chansey", "lapras"}
SING = ("sing", "Sing", "A soothing lullaby that lulls the target into a deep sleep.", 5, 25, "pkmn_sleep", 900)

# Pokémon that barely fight.
NO_MOVES = {"magikarp", "metapod", "kakuna", "ditto"}
TIER1_ONLY = {"caterpie", "weedle"}

TIER_LEVELS = [0, 18, 36]

# Species that will attack people who wander too close.
AGGRESSIVE = {"beedrill", "spearow", "fearow", "mankey", "primeape", "gyarados", "tauros",
              "golbat", "tentacruel", "rhyhorn", "rhydon", "arbok", "muk", "kingler",
              "pinsir", "scyther", "marowak", "electrode", "mewtwo", "dodrio", "nidoking"}
# Species that run from people.
SKITTISH = {"abra", "clefairy", "clefable", "chansey", "mew", "ditto", "eevee", "farfetchd",
            "pidgey", "rattata", "diglett", "dugtrio", "ponyta", "dratini", "lapras", "vulpix",
            "jigglypuff", "exeggcute", "magikarp"}

LEGENDARY = {"articuno", "zapdos", "moltres", "mewtwo", "mew"}

FLYERS_EXTRA = {"gastly", "haunter", "koffing", "weezing", "magnemite", "magneton", "porygon"}
NOT_FLYING = {"doduo", "dodrio"}  # flightless birds
SWIMMERS_EXTRA = {"psyduck", "golduck", "slowpoke", "slowbro", "lapras", "dratini", "dragonair"}

MATERIAL = {
    "rock": ["stone"], "ground": ["flesh"],
}
STONE_BODIES = {"geodude", "graveler", "golem", "onix"}
STEEL_BODIES = {"magnemite", "magneton", "voltorb", "electrode"}
PLASTIC_BODIES = {"porygon"}
GAS_BODIES = {"gastly", "haunter", "koffing", "weezing"}
VEGGY_BODIES = {"oddish", "gloom", "vileplume", "bellsprout", "weepinbell", "victreebel",
                "tangela", "exeggcute", "exeggutor"}
SLIME_BODIES = {"grimer", "muk", "ditto"}

BODYTYPE = {
    "bird": {"pidgey", "pidgeotto", "pidgeot", "spearow", "fearow", "farfetchd", "doduo", "dodrio",
             "articuno", "zapdos", "moltres", "aerodactyl", "zubat", "golbat"},
    "insect": {"caterpie", "metapod", "butterfree", "weedle", "kakuna", "beedrill", "paras", "parasect",
               "venonat", "venomoth", "scyther", "pinsir"},
    "snake": {"ekans", "arbok", "onix", "dratini", "dragonair"},
    "fish": {"magikarp", "gyarados", "goldeen", "seaking", "horsea", "seadra"},
    "blob": {"grimer", "muk", "ditto", "gastly", "koffing", "weezing", "magnemite", "magneton",
             "voltorb", "electrode", "tentacool", "tentacruel", "staryu", "starmie", "shellder",
             "cloyster", "exeggcute", "geodude", "omanyte", "omastar", "kabuto", "tangela", "porygon"},
    "crab": {"krabby", "kingler"},
    "human": {"abra", "kadabra", "alakazam", "machop", "machoke", "machamp", "hitmonlee", "hitmonchan",
              "mr_mime", "jynx", "electabuzz", "magmar", "drowzee", "hypno", "mewtwo", "haunter",
              "gengar", "poliwhirl", "poliwrath", "psyduck", "golduck", "jigglypuff", "wigglytuff",
              "clefairy", "clefable", "chansey", "kangaskhan", "snorlax", "lickitung", "cubone", "marowak",
              "mankey", "primeape", "charmander", "charmeleon", "charizard", "squirtle", "wartortle",
              "blastoise", "nidoqueen", "nidoking", "rhydon", "graveler", "golem", "kabutops",
              "dragonite", "mew", "sandshrew", "sandslash", "pikachu", "raichu"},
}


def bodytype(pid):
    for body, members in BODYTYPE.items():
        if pid in members:
            return body
    return "dog"


def material(pid, types):
    if pid in STONE_BODIES:
        return ["stone"]
    if pid in STEEL_BODIES:
        return ["steel"]
    if pid in PLASTIC_BODIES:
        return ["plastic"]
    if pid in VEGGY_BODIES:
        return ["veggy"]
    return ["flesh"]


def size_hint(weight):
    # Monster volume ~ weight at roughly the density of water, with sensible floors.
    liters = max(1.0, weight)
    if liters >= 1000:
        return "%d L" % 900
    return "%d ml" % int(liters * 1000)


def mid(pid):
    return "pkmn_" + pid


# ---------------------------------------------------------------------------
# Evolution graph helpers
# ---------------------------------------------------------------------------
BY_ID = {p[1]: p for p in POKEDEX}
PREEVO = {}
for p in POKEDEX:
    for evo in p[6]:
        target = evo.split(":")[-1]
        PREEVO[target] = (p[1], evo)


def wild_level(pid):
    if pid in LEGENDARY:
        return 70 if pid == "mewtwo" else 50
    if pid in PREEVO:
        parent, evo = PREEVO[pid]
        if evo.startswith("L"):
            return int(evo[1:].split(":")[0]) + 3
        return max(25, wild_level(parent) + 8)
    p = BY_ID[pid]
    if p[6]:  # base stage of a line
        return {"common": 4, "uncommon": 8, "rare": 12}.get(p[8], 10)
    return 25  # standalone Pokémon like Tauros or Lapras


LEVEL_BANDS = [3, 5, 8, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 70]


def band_for(level):
    return min(LEVEL_BANDS, key=lambda b: abs(b - level))


# ---------------------------------------------------------------------------
# Monsters
# ---------------------------------------------------------------------------
def spell_attack(attack_id, spell_id, cooldown, message, condition=None, self_target=False,
                 no_target=False, level=None):
    data = {"id": spell_id}
    if self_target:
        data["hit_self"] = True
    if level is not None:
        data["min_level"] = level
    atk = {"id": attack_id, "type": "spell", "spell_data": data, "cooldown": cooldown,
           "monster_message": message}
    if no_target:
        atk["allow_no_target"] = True
    if condition is not None:
        atk["condition"] = condition
    return atk


def level_at_least(n):
    return {"math": ["value_or(u_pkmn_level, 5) >= %d" % n]}


def is_owned():
    return {"math": ["u_val('friendly') != 0"]}


def build_monster(p):
    num, pid, name, types, stats, weight, evos, habitats, rarity, catch, sym, color, desc = p
    hp, atk, dfn, spc, spe = stats
    spell_level = max(1, min(30, spc // 5))

    flags = ["SEES", "HEARS", "SMELLS", "ANIMAL", "PATH_AVOID_DANGER", "PKMN_POKEMON",
             "PKMN_CATCH_%d" % catch]
    if pid not in GAS_BODIES and pid not in STEEL_BODIES and pid not in STONE_BODIES and pid not in PLASTIC_BODIES:
        flags.append("WARM")
    if ("flying" in types and pid not in NOT_FLYING) or pid in FLYERS_EXTRA:
        flags.append("FLIES")
    if "water" in types or pid in SWIMMERS_EXTRA:
        flags.append("SWIMS")
    if "ghost" in types:
        flags.append("NIGHT_INVISIBILITY")
    if "ghost" in types or pid in GAS_BODIES:
        flags.append("NO_BREATHE")
    if "fire" in types:
        flags.append("FIREPROOF")
    if atk >= 90 or weight >= 100:
        flags.append("BASHES")
    if pid in LEGENDARY:
        flags.append("PKMN_LEGENDARY")
    for t in types:
        flags.append("PKMN_TYPE_" + t.upper())

    aggression = -15
    morale = 30
    aggro_character = False
    fear = []
    if pid in AGGRESSIVE:
        aggression = 15
        morale = 60
        aggro_character = True
    elif pid in SKITTISH:
        aggression = -40
        morale = 10
        fear = ["PLAYER_CLOSE", "SOUND"]

    mon = {
        "id": mid(pid),
        "type": "MONSTER",
        "name": {"str_sp": name},
        "description": desc + "  (Kanto #%03d, %s type.)" % (num, "/".join(t.capitalize() for t in types)),
        "default_faction": "pokemon",
        "bodytype": bodytype(pid),
        "categories": ["WILDLIFE"],
        "species": ["POKEMON"] + ["PKMN_" + t.upper() for t in types],
        "volume": size_hint(weight),
        "weight": "%d g" % int(max(0.5, weight) * 1000),
        "hp": min(320, int(15 + hp * 1.2)),
        "speed": int(60 + spe * 0.75),
        "material": material(pid, types),
        "symbol": sym,
        "color": color,
        "aggression": aggression,
        "morale": morale,
        "aggro_character": aggro_character,
        "melee_skill": max(1, min(9, 2 + atk // 20)),
        "melee_dice": 1 + atk // 60,
        "melee_dice_sides": max(3, atk // 10),
        "melee_damage": [{"damage_type": "pkmn_" + ("normal" if types[0] in ("fire", "water", "electric", "psychic", "ice", "ghost") else types[0]), "amount": max(1, atk // 15)}],
        "dodge": max(1, spe // 25),
        "armor": {"bash": dfn // 10, "cut": dfn // 8, "stab": dfn // 9, "bullet": dfn // 12},
        "vision_day": 50,
        "vision_night": 30 if ("ghost" in types or pid in ("zubat", "golbat", "noctowl")) else 8,
        "regenerates": 0,
        "death_function": {"message": "The %s faints and does not get up again.", "corpse_type": "NORMAL"},
        "anger_triggers": ["HURT", "FRIEND_ATTACKED", "FRIEND_DIED"],
        "fear_triggers": fear,
        "flags": flags,
        "chat_topics": ["TALK_PKMN_PARTNER"],
        "harvest": "pkmn_harvest_" + ("stone" if pid in STONE_BODIES else "steel" if pid in STEEL_BODIES else "none" if (pid in GAS_BODIES or pid in PLASTIC_BODIES or pid in SLIME_BODIES) else "flesh"),
    }
    if not fear:
        del mon["fear_triggers"]
    if pid in ("magmar", "charmander", "charmeleon", "charizard", "moltres", "ponyta", "rapidash", "zapdos", "electabuzz", "flareon"):
        mon["luminance"] = 3
    if "ground" in types or "rock" in types:
        mon["armor"]["bash"] += 3

    attacks = []
    # Wild Pokémon pick up a level the first time they act.
    band = band_for(wild_level(pid))
    attacks.append(spell_attack("pkmn_init", "pkmn_init_lv%d" % band, 1, "",
                                {"math": ["value_or(u_pkmn_level, 0) == 0"]}, self_target=True, no_target=True))
    # Pokédex registration the first time one of yours is seen in the field.
    attacks.append(spell_attack("pkmn_register", "pkmn_dex_" + pid, 5, "",
                                {"and": [is_owned(), {"math": ["value_or(pkmn_dex_%s, 0) == 0" % pid]}]},
                                self_target=True, no_target=True))
    # Evolutions.
    for i, evo in enumerate(evos):
        parts = evo.split(":")
        target = parts[-1]
        if parts[0].startswith("L"):
            cond = {"and": [is_owned(), level_at_least(int(parts[0][1:]))]}
        elif parts[0] == "S":
            cond = {"and": [is_owned(), {"math": ["value_or(u_pkmn_stone_%s, 0) == 1" % parts[1]]}]}
        else:  # trade
            cond = {"and": [is_owned(), {"math": ["value_or(u_pkmn_stone_link, 0) == 1"]}]}
        attacks.append(spell_attack("pkmn_evolve_%d" % i, "pkmn_evolve_" + target, 1,
                                    "What?  %1$s is evolving!", cond, self_target=True, no_target=True))
    # Battle moves.
    if pid not in NO_MOVES:
        for t in types:
            for tier, move in enumerate(MOVES[t]):
                if tier > 0 and pid in TIER1_ONLY:
                    continue
                cond = level_at_least(TIER_LEVELS[tier]) if tier else None
                attacks.append(spell_attack("pkmn_move_" + move[0], "pkmn_move_" + move[0], move[8],
                                            "%1$s used " + move[1] + "!", cond, level=spell_level))
        status = None
        if pid in SINGERS:
            status = SING
        else:
            for t in types:
                if t in STATUS_MOVES:
                    status = STATUS_MOVES[t]
                    break
        if status and pid not in TIER1_ONLY:
            attacks.append(spell_attack("pkmn_move_" + status[0], "pkmn_move_" + status[0], status[4],
                                        "%1$s used " + status[1] + "!", None, level=spell_level))
    mon["special_attacks"] = attacks
    return mon


TRAINER_SPECIES = sorted({
    "geodude", "onix", "staryu", "starmie", "voltorb", "pikachu", "raichu", "victreebel",
    "tangela", "vileplume", "koffing", "muk", "weezing", "kadabra", "mr_mime", "venomoth",
    "alakazam", "growlithe", "ponyta", "rapidash", "arcanine", "rhyhorn", "dugtrio",
    "nidoqueen", "nidoking", "rhydon", "rattata", "raticate", "zubat", "golbat", "ekans", "arbok",
    "grimer", "meowth", "pidgeot", "exeggutor", "gyarados", "charizard", "blastoise", "venusaur",
    "machop", "machoke", "drowzee", "hypno", "sandshrew", "cubone", "gastly", "haunter",
})


def build_trainer_monster(pid):
    p = BY_ID[pid]
    return {
        "id": mid(pid) + "_trainer",
        "type": "MONSTER",
        "copy-from": mid(pid),
        "name": {"str_sp": "trainer's " + p[2]},
        "description": "This %s belongs to another trainer and has been trained for battle.  It cannot be caught.  %s" % (p[2], p[12]),
        "extend": {"species": ["PKMN_TRAINER_OWNED"], "flags": ["PKMN_TRAINER_OWNED"]},
        "aggression": 100,
        "morale": 100,
        "aggro_character": False,
        "death_function": {"message": "%s fainted!  Its trainer recalls it.", "corpse_type": "NO_CORPSE"},
        "harvest": "pkmn_harvest_none",
    }


# ---------------------------------------------------------------------------
# Spells
# ---------------------------------------------------------------------------
def move_spell(move, dtype):
    mid_, name, desc, power, incr, rng, aoe, shape, cooldown, status, dur = move
    sp = {
        "type": "SPELL",
        "id": "pkmn_move_" + mid_,
        "name": name,
        "description": desc,
        "valid_targets": ["hostile"],
        "effect": "attack",
        "shape": shape,
        "damage_type": dtype,
        "min_damage": {"math": ["%s * (0.5 + value_or(u_pkmn_level, 10) / 50)" % power]},
        "max_damage": 999,
        "damage_increment": incr,
        "max_level": 30,
        "min_range": rng,
        "max_range": rng,
        "flags": ["SILENT", "NO_EXPLOSION_SFX", "NON_MAGICAL", "NO_FAIL"],
        "base_casting_time": 100,
    }
    if aoe:
        sp["min_aoe"] = sp["max_aoe"] = aoe
    if status:
        sp["effect_str"] = status
        sp["min_duration"] = sp["max_duration"] = dur
    return sp


def status_spell(s):
    sid, name, desc, rng, cooldown, effect, dur = s
    return {
        "type": "SPELL",
        "id": "pkmn_move_" + sid,
        "name": name,
        "description": desc,
        "valid_targets": ["hostile"],
        "effect": "attack",
        "shape": "blast",
        "effect_str": effect,
        "min_duration": dur,
        "max_duration": dur,
        "min_damage": 0,
        "max_damage": 0,
        "max_level": 30,
        "min_range": rng,
        "max_range": rng,
        "flags": ["SILENT", "NO_EXPLOSION_SFX", "NON_MAGICAL", "NO_FAIL"],
    }


def build_spells():
    out = []
    for t in TYPES:
        for move in MOVES[t]:
            out.append(move_spell(move, "pkmn_" + t))
    seen = set()
    for s in list(STATUS_MOVES.values()) + [SING]:
        if s[0] not in seen:
            seen.add(s[0])
            out.append(status_spell(s))
    return out


def build_system_spells():
    out = []
    targets = sorted({evo.split(":")[-1] for p in POKEDEX for evo in p[6]})
    for target in targets:
        out.append({
            "type": "SPELL",
            "id": "pkmn_evolve_" + target,
            "name": "Evolve into " + BY_ID[target][2],
            "description": "Evolution: the Pokémon transforms into %s." % BY_ID[target][2],
            "valid_targets": ["self", "ally", "hostile"],
            "effect": "targeted_polymorph",
            "effect_str": mid(target),
            "shape": "blast",
            "min_damage": 100000,
            "max_damage": 100000,
            "min_range": 0,
            "max_range": 0,
            "message": "",
            "flags": ["SILENT", "NO_EXPLOSION_SFX", "NON_MAGICAL", "NO_FAIL"],
            "extra_effects": [{"id": "pkmn_after_evolve", "hit_self": True}],
        })
    for band in LEVEL_BANDS:
        out.append({
            "type": "SPELL",
            "id": "pkmn_init_lv%d" % band,
            "name": "Wild Pokémon level %d" % band,
            "description": "Internal: gives a wild Pokémon its level.",
            "valid_targets": ["self"],
            "effect": "effect_on_condition",
            "effect_str": "EOC_PKMN_INIT_LV%d" % band,
            "shape": "blast",
            "message": "",
            "flags": ["SILENT", "NO_EXPLOSION_SFX", "NON_MAGICAL", "NO_FAIL"],
        })
    for p in POKEDEX:
        out.append({
            "type": "SPELL",
            "id": "pkmn_dex_" + p[1],
            "name": "Pokédex: " + p[2],
            "description": "Internal: registers %s in the Pokédex." % p[2],
            "valid_targets": ["self"],
            "effect": "effect_on_condition",
            "effect_str": "EOC_PKMN_DEX_" + p[1].upper(),
            "shape": "blast",
            "message": "",
            "flags": ["SILENT", "NO_EXPLOSION_SFX", "NON_MAGICAL", "NO_FAIL"],
        })
    return out


def build_eocs():
    out = []
    for band in LEVEL_BANDS:
        lo, hi = max(2, band - 2), band + 2
        out.append({
            "type": "effect_on_condition",
            "id": "EOC_PKMN_INIT_LV%d" % band,
            "effect": [
                {"math": ["u_pkmn_level = rng(%d, %d)" % (lo, hi)]},
                {"math": ["u_pkmn_level = round(u_pkmn_level)"]},
                {"math": ["u_pkmn_xp = 0"]},
                {"run_eocs": "EOC_PKMN_APPLY_LEVEL"},
            ],
        })
    for p in POKEDEX:
        var = "pkmn_dex_" + p[1]
        out.append({
            "type": "effect_on_condition",
            "id": "EOC_PKMN_DEX_" + p[1].upper(),
            "condition": {"math": ["value_or(%s, 0) == 0" % var]},
            "effect": [
                {"math": ["%s = 1" % var]},
                {"math": ["pkmn_dex_count = value_or(pkmn_dex_count, 0) + 1"]},
                {"u_message": "Pokédex: data for #%03d %s was added!  (<global_val:pkmn_dex_count>/151 registered)" % (p[0], p[2]), "type": "good"},
                {"run_eocs": "EOC_PKMN_DEX_MILESTONES"},
            ],
        })
    return out


# ---------------------------------------------------------------------------
# Type chart.  Attacking type -> {defending type: multiplier}.
# Gen 1 matchups, except Ghost hits Psychic super effectively (the Gen 1 bug
# made it do nothing).  Immunities are handled by monster flags via the
# damage type's immune_flags; everything else by the on-damage EOCs below.
# ---------------------------------------------------------------------------
CHART = {
    "normal": {"rock": 0.5, "ghost": 0},
    "fire": {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 2, "bug": 2, "rock": 0.5, "dragon": 0.5},
    "water": {"fire": 2, "water": 0.5, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
    "electric": {"water": 2, "electric": 0.5, "grass": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
    "grass": {"fire": 0.5, "water": 2, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5,
              "bug": 0.5, "rock": 2, "dragon": 0.5},
    "ice": {"water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2},
    "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5,
                 "rock": 2, "ghost": 0},
    "poison": {"grass": 2, "poison": 0.5, "ground": 0.5, "bug": 2, "rock": 0.5, "ghost": 0.5},
    "ground": {"fire": 2, "electric": 2, "grass": 0.5, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2},
    "flying": {"electric": 0.5, "grass": 2, "fighting": 2, "bug": 2, "rock": 0.5},
    "psychic": {"fighting": 2, "poison": 2, "psychic": 0.5},
    "bug": {"fire": 0.5, "grass": 2, "fighting": 0.5, "poison": 2, "flying": 0.5, "psychic": 2, "ghost": 0.5},
    "rock": {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2},
    "ghost": {"normal": 0, "psychic": 2, "ghost": 2},
    "dragon": {"dragon": 2},
}

# How each Pokémon damage type is resisted by ordinary armor and monsters.
DERIVED = {
    "normal": "bash", "fire": "heat", "water": "bash", "electric": "electric", "grass": "cut",
    "ice": "cold", "fighting": "bash", "poison": "acid", "ground": "bash", "flying": "cut",
    "psychic": "bash", "bug": "stab", "rock": "bash", "ghost": "cold", "dragon": "cut",
}
COLORS = {
    "normal": "light_gray", "fire": "light_red", "water": "light_blue", "electric": "yellow",
    "grass": "light_green", "ice": "light_cyan", "fighting": "brown", "poison": "magenta",
    "ground": "brown", "flying": "white", "psychic": "pink", "bug": "green", "rock": "dark_gray",
    "ghost": "magenta", "dragon": "blue",
}


def build_type_chart():
    out = []
    for i, t in enumerate(TYPES):
        immune = [("PKMN_TYPE_" + d.upper()) for d, m in CHART[t].items() if m == 0]
        dt = {
            "type": "damage_type",
            "id": "pkmn_" + t,
            "name": t.capitalize() + " (Pokémon)",
            "physical": DERIVED[t] in ("bash", "cut", "stab"),
            "magic_color": COLORS[t],
            "derived_from": [DERIVED[t], 1.0],
            "mon_difficulty": True,
            "ondamage_eocs": ["EOC_PKMN_HIT_" + t.upper()],
        }
        if immune:
            dt["immune_flags"] = {"monster": immune}
        out.append(dt)
        out.append({
            "type": "damage_info_order",
            "id": "pkmn_" + t,
            "info_display": "none",
            "verb": t,
            "bionic_info": {"order": 2000 + i, "show_type": False},
            "protection_info": {"order": 2000 + i, "show_type": False},
            "pet_prot_info": {"order": 2000 + i, "show_type": False},
            "melee_combat_info": {"order": 2000 + i, "show_type": True},
            "ablative_info": {"order": 2000 + i, "show_type": False},
        })
        effect = [{"math": ["_pkmn_mult = 1"]}]
        for d, m in CHART[t].items():
            if m in (0,):
                continue
            effect.append({"if": {"npc_has_species": "PKMN_" + d.upper()},
                           "then": {"math": ["_pkmn_mult = _pkmn_mult * %s" % m]}})
        effect += [
            {"if": {"math": ["_pkmn_mult > 1.5"]},
             "then": [
                 {"npc_deal_damage": "pure", "amount": {"math": ["round(_damage_taken * (_pkmn_mult - 1))"]}},
                 {"u_message": "It's super effective!", "type": "good"}]},
            {"if": {"math": ["_pkmn_mult < 0.75"]},
             "then": [
                 {"math": ["n_hp('ALL') = n_hp('ALL') + round(_damage_taken * (1 - _pkmn_mult))"]},
                 {"u_message": "It's not very effective…", "type": "neutral"}]},
        ]
        out.append({
            "type": "effect_on_condition",
            "id": "EOC_PKMN_HIT_" + t.upper(),
            "//": "Type effectiveness of %s attacks.  u = attacker, npc = target." % t,
            "condition": {"and": ["has_beta", "npc_is_monster", {"npc_has_species": "POKEMON"},
                                  {"math": ["_damage_taken > 0"]}]},
            "effect": effect,
        })
    return out


def build_item_spells():
    """Evolution stone / link cable spells restricted to Pokémon that can use them."""
    out = []
    users = {}
    for p in POKEDEX:
        for evo in p[6]:
            parts = evo.split(":")
            if parts[0] == "S":
                users.setdefault(parts[1], set()).add(p[1])
            elif parts[0] == "T":
                users.setdefault("link", set()).add(p[1])
    names = {"fire": "Fire Stone", "water": "Water Stone", "thunder": "Thunder Stone",
             "leaf": "Leaf Stone", "moon": "Moon Stone", "link": "Link Cable"}
    for stone, members in sorted(users.items()):
        out.append({
            "type": "SPELL",
            "id": "pkmn_use_stone_" + stone,
            "name": "Use " + names[stone],
            "description": "Use the %s on one of your Pokémon that can evolve with it: %s." % (
                names[stone], ", ".join(BY_ID[m][2] for m in sorted(members, key=lambda x: BY_ID[x][0]))),
            "valid_targets": ["ally"],
            "targeted_monster_ids": [mid(m) for m in sorted(members)],
            "effect": "effect_on_condition",
            "effect_str": "EOC_PKMN_STONE_" + stone.upper(),
            "shape": "blast",
            "min_range": 2,
            "max_range": 2,
            "base_casting_time": 100,
            "message": "",
            "flags": ["SILENT", "NO_EXPLOSION_SFX", "NON_MAGICAL", "NO_FAIL", "NO_HANDS", "NO_LEGS"],
        })
        out.append({
            "type": "effect_on_condition",
            "id": "EOC_PKMN_STONE_" + stone.upper(),
            "effect": [
                {"math": ["u_pkmn_stone_%s = 1" % stone]},
                {"u_message": "The %s begins to glow…" % names[stone], "type": "good"},
            ],
        })
    return out


# ---------------------------------------------------------------------------
# Spawns
# ---------------------------------------------------------------------------
RARITY_WEIGHT = {"common": 100, "uncommon": 30, "rare": 7}
PACK = {"common": [1, 3], "uncommon": [1, 2], "rare": [1, 1]}
HABITAT_GROUPS = ["forest", "field", "water", "ocean", "cave", "mountain", "urban", "sewer",
                  "swamp", "power", "lab", "safari"]
VANILLA_HOOKS = {
    # Weights are tuned so Pokémon make up roughly a quarter to a third of each habitat's animals.
    "GROUP_FOREST": [("forest", 380), ("field", 280)],
    "GROUP_RIVER": [("water", 220)],
    "GROUP_POND_ANIMAL": [("water", 90)],
    "GROUP_SWAMP": [("swamp", 300)],
    "GROUP_OCEAN_SHORE": [("ocean", 30)],
    "GROUP_CAVE": [("cave", 450), ("mountain", 150)],
    "GROUP_SEWER": [("sewer", 250)],
    "GROUP_STRAY_CATS": [("urban", 40)],
    "GROUP_STRAY_DOGS": [("urban", 40)],
    "GROUP_BIRDFEEDER": [("field", 100)],
}


def build_spawns():
    out = []
    for hab in HABITAT_GROUPS:
        entries = []
        for p in POKEDEX:
            if hab in p[7] and p[8] in RARITY_WEIGHT:
                entries.append({"monster": mid(p[1]), "weight": RARITY_WEIGHT[p[8]],
                                "cost_multiplier": 1, "pack_size": PACK[p[8]]})
        out.append({"type": "monstergroup", "id": "PKMN_GROUP_" + hab.upper(), "is_animal": True,
                    "monsters": entries})
    for group, hooks in VANILLA_HOOKS.items():
        out.append({"type": "monstergroup", "id": group,
                    "monsters": [{"group": "PKMN_GROUP_" + h.upper(), "weight": w} for h, w in hooks]})
    return out


def write(rel, data):
    path = os.path.join(MOD_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote %s (%d objects)" % (rel, len(data)))


def main():
    write("monsters/pokemon_gen.json", [build_monster(p) for p in POKEDEX])
    write("monsters/trainer_pokemon_gen.json", [build_trainer_monster(s) for s in TRAINER_SPECIES])
    write("spells/moves_gen.json", build_spells())
    write("spells/system_gen.json", build_system_spells())
    write("eocs/pokedex_gen.json", build_eocs())
    write("monstergroups/spawns_gen.json", build_spawns())
    write("core/types_gen.json", build_type_chart())
    write("spells/stones_gen.json", build_item_spells())


if __name__ == "__main__":
    main()
