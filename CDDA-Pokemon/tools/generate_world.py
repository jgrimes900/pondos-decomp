#!/usr/bin/env python3
"""
Generates the world content for the Pokémon Overhaul mod: locations (overmap
terrain, specials and mapgen), NPCs, trainer battles, dialogue and missions.

  python3 tools/generate_world.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pokedex_data import POKEDEX  # noqa: E402

MOD_DIR = os.path.join(os.path.dirname(HERE), "pokemon_overhaul")
BY_ID = {p[1]: p for p in POKEDEX}


def pname(pid):
    return BY_ID[pid][2]


def write(rel, data):
    path = os.path.join(MOD_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote %s (%d objects)" % (rel, len(data)))


# ===========================================================================
# Trainers
# ===========================================================================
# id, display name, title, gym/location, badge item, badge var, required badges,
# team [(species, level)], intro line, battle line, win line, after line, prize
GYM_LEADERS = [
    ("brock", "Brock", "Pewter Gym Leader", "the Pewter City Gym", "pkmn_badge_boulder", 0,
     [("geodude", 14), ("onix", 16)],
     "I'm Brock, the Pewter City Gym Leader.  The dead tore the city apart, but my rock-hard willpower held.  My Pokémon are as solid as the walls of this gym.",
     "My rock-hard willpower is evident even in my Pokémon!  Go, Geodude!  Go, Onix!",
     "I took you for granted.  As proof of your victory, here's the Boulder Badge.",
     "There are all kinds of trainers in the world.  You appear to be very gifted as a Pokémon trainer."),
    ("misty", "Misty", "Cerulean Gym Leader", "the Cerulean City Gym", "pkmn_badge_cascade", 1,
     [("staryu", 18), ("starmie", 21)],
     "Hi, you're a new face!  Trainers who want to turn pro have to have a policy about Pokémon.  What's your policy?  Mine is an all-out offensive with Water-type Pokémon!",
     "Let's see how you handle the tide!  Go, Staryu!  Go, Starmie!",
     "Wow!  You're too much!  All right!  You can have the Cascade Badge to show you beat me!",
     "The Cascade Badge makes your Pokémon listen a little better.  The pool's still clean, by the way.  Water Pokémon are good at that."),
    ("surge", "Lt. Surge", "Vermilion Gym Leader", "the Vermilion City Gym", "pkmn_badge_thunder", 2,
     [("voltorb", 21), ("pikachu", 18), ("raichu", 24)],
     "Hey, kid!  What do you think you're doing here?  You won't live long in combat!  That's for sure!  I tell you, kid, electric Pokémon saved me during the war, and they kept the lights on after the end of the world.",
     "I'll zap you just like I do with my enemies in battle!",
     "Whoa!  You're the real deal, kid!  Fine then, take the Thunder Badge!",
     "A little word of advice, kid!  Electricity is sure powerful!  But Ground-type Pokémon shrug it off!"),
    ("erika", "Erika", "Celadon Gym Leader", "the Celadon City Gym", "pkmn_badge_rainbow", 3,
     [("victreebel", 29), ("tangela", 24), ("vileplume", 29)],
     "Hello.  Lovely weather, isn't it?  It's so pleasant.  Oh dear, I must have dozed off.  Welcome.  My name is Erika, and I am the leader of Celadon Gym.  I teach the art of flower arranging.  The garden is all that is left of the old city.",
     "Oh!  I concede defeat in advance… no, I jest.  Shall we?",
     "Oh!  I concede defeat.  You are remarkably strong.  I must confer on you the Rainbow Badge.",
     "You are cataloging Pokémon?  I must say I'm impressed.  I would never collect Pokémon if they were unattractive."),
    ("koga", "Koga", "Fuchsia Gym Leader", "the Fuchsia City Gym", "pkmn_badge_soul", 4,
     [("koffing", 37), ("muk", 39), ("weezing", 43)],
     "Fwahahaha!  A mere child like you dares to challenge me?  The very idea makes me shiver with mirth!  I shall show you true terror as a ninja master!  Poison brings steady doom.",
     "Sleep, confusion, poison… Let us see how you deal with it!",
     "Humph!  You have proven your worth!  Here!  Take the Soul Badge!",
     "When afflicted by status effects, focus and win at all costs!  Poison spreads quickly among the living."),
    ("sabrina", "Sabrina", "Saffron Gym Leader", "the Saffron City Gym", "pkmn_badge_marsh", 5,
     [("kadabra", 38), ("mr_mime", 37), ("venomoth", 38), ("alakazam", 43)],
     "I had a vision of your arrival!  I have had psychic powers since I was a child.  I foresaw the Cataclysm too, though no one would listen.",
     "I dislike fighting, but if you wish, I will show you my powers!",
     "I'm shocked!  But a loss is a loss.  I admit I didn't work hard enough to win!  You earned the Marsh Badge!",
     "Everyone has psychic power!  People just don't realize it!"),
    ("blaine", "Blaine", "Cinnabar Gym Leader", "the Cinnabar Island Gym", "pkmn_badge_volcano", 6,
     [("growlithe", 42), ("ponyta", 40), ("rapidash", 42), ("arcanine", 47)],
     "Hah!  I am Blaine!  I am the leader of Cinnabar Gym!  My fiery Pokémon will incinerate all challengers!  Hah!  You better have Burn Heal!",
     "My Pokémon are fired up!",
     "I have burned down to nothing!  Not even ashes remain!  You have earned the Volcano Badge!",
     "Fire Pokémon have kept the shamblers away from my island.  Keep that in mind."),
    ("giovanni", "Giovanni", "Viridian Gym Leader", "the Viridian City Gym", "pkmn_badge_earth", 7,
     [("rhyhorn", 45), ("dugtrio", 42), ("nidoqueen", 44), ("nidoking", 45), ("rhydon", 50)],
     "Fwahahaha!  This is my hideout!  I planned to resurrect Team Rocket here, in the ruins of the world.  But you have caught me again!  So be it!  This time, I'm not holding back!",
     "Once more, you shall face Giovanni, the greatest trainer!",
     "Ha!  That was a truly intense fight!  You have won!  As proof, here is the Earth Badge!",
     "Having lost, I cannot face my underlings.  Team Rocket is finished forever.  I will dedicate my life to the study of Pokémon.  Let us meet again some day!"),
]

ROCKET_TEAMS = [
    [("rattata", 14), ("zubat", 15)],
    [("ekans", 16), ("koffing", 17)],
    [("grimer", 18), ("raticate", 20)],
    [("zubat", 18), ("golbat", 22)],
    [("machop", 20), ("drowzee", 21)],
]

RIVAL_TEAM = [("pidgeot", 61), ("alakazam", 59), ("rhydon", 61), ("exeggutor", 61), ("gyarados", 63), ("charizard", 65)]


def team_ids(team):
    return ["pkmn_%s_trainer" % s for s, _ in team]


def spawn_team(team, level_bonus=0):
    effects = []
    for species, level in team:
        effects.append({
            "npc_spawn_monster": "pkmn_%s_trainer" % species,
            "real_count": 1,
            "min_radius": 2,
            "max_radius": 5,
            "mon_variables": {"pkmn_level": str(level + level_bonus)},
            "spawn_message": "%s sent out %s!" % ("<npc_name>", pname(species)),
        })
    return effects


def team_alive_cond(team, alive=True):
    ids = ", ".join("'%s'" % i for i in team_ids(team))
    op = ">" if alive else "=="
    return {"math": ["u_monsters_nearby(%s, 'radius': 40, 'attitude': 'both') %s 0" % (ids, op)]}


def have_pokemon_cond():
    return {"math": ["u_mon_species_nearby('POKEMON', 'radius': 12, 'attitude': 'friendly') > 0"]}


def trainer_topics(tid, name, team, intro, battle_line, win_line, after_line, on_win, extra_cond=None,
                   battle_cond_text=None, extra_responses=None, rematch=True):
    """Builds the talk topics for an NPC that fights Pokémon battles."""
    T = "TALK_PKMN_%s" % tid.upper()
    won = {"math": ["value_or(pkmn_trainer_%s_won, 0) == 1" % tid]}
    fighting = {"math": ["value_or(n_pkmn_battle, 0) == 1"]}
    not_fighting = {"math": ["value_or(n_pkmn_battle, 0) == 0"]}
    start_cond = [not_fighting, have_pokemon_cond(), {"not": won}]
    if extra_cond:
        start_cond.append(extra_cond)
    responses = [
        {"text": "I challenge you to a Pokémon battle!", "condition": {"and": start_cond},
         "effect": [{"math": ["n_pkmn_battle = 1"]}, {"math": ["n_pkmn_rematch = 0"]}] + spawn_team(team),
         "topic": T + "_BATTLE"},
    ]
    if extra_cond and battle_cond_text:
        responses.append({"text": "I want to battle you.", "condition": {"and": [not_fighting, {"not": won}, {"not": extra_cond}]},
                          "topic": T + "_NOT_READY"})
    responses.append({"text": "I want to battle you.", "condition": {"and": [not_fighting, {"not": won}, {"not": have_pokemon_cond()}]},
                      "topic": "TALK_PKMN_NEED_POKEMON"})
    responses += [
        {"text": "Your Pokémon are all down.  I win!", "condition": {"and": [fighting, team_alive_cond(team, False),
                                                                            {"math": ["value_or(n_pkmn_rematch, 0) == 0"]}]},
         "effect": [{"math": ["n_pkmn_battle = 0"]}, {"math": ["pkmn_trainer_%s_won = 1" % tid]}] + on_win,
         "topic": T + "_WIN"},
        {"text": "That was a good rematch.", "condition": {"and": [fighting, team_alive_cond(team, False),
                                                                  {"math": ["value_or(n_pkmn_rematch, 0) == 1"]}]},
         "effect": [{"math": ["n_pkmn_battle = 0"]}, {"u_spawn_item": "pkmn_loot_common", "use_item_group": True}],
         "topic": T + "_REMATCH_WON"},
        {"text": "(The battle is still going.)", "condition": {"and": [fighting, team_alive_cond(team, True)]},
         "topic": T + "_BATTLING"},
        {"text": "I give up.  Recall your Pokémon.", "condition": {"and": [fighting, team_alive_cond(team, True)]},
         "effect": [{"math": ["n_pkmn_battle = 0"]},
                    {"u_run_monster_eocs": [{"id": "EOC_PKMN_FORFEIT_" + tid.upper(), "effect": "u_die"}],
                     "mtype_ids": team_ids(team), "monster_range": 40}],
         "topic": T + "_FORFEIT"},
    ]
    if rematch:
        responses.append({"text": "How about a rematch?  [Training battle]", "condition": {"and": [not_fighting, won, have_pokemon_cond()]},
                          "effect": [{"math": ["n_pkmn_battle = 1"]}, {"math": ["n_pkmn_rematch = 1"]}] + spawn_team(team, 5),
                          "topic": T + "_BATTLE"})
    responses += extra_responses or []
    responses.append({"text": "See you around.", "topic": "TALK_DONE"})
    topics = [
        {"type": "talk_topic", "id": T,
         "dynamic_line": {"math": ["value_or(pkmn_trainer_%s_won, 0) == 1" % tid], "yes": after_line, "no": intro},
         "responses": responses},
        {"type": "talk_topic", "id": T + "_BATTLE", "dynamic_line": battle_line,
         "responses": [{"text": "Bring it on!", "topic": "TALK_DONE"}]},
        {"type": "talk_topic", "id": T + "_BATTLING", "dynamic_line": "We're in the middle of a battle!  Focus!",
         "responses": [{"text": "Right.", "topic": "TALK_DONE"}]},
        {"type": "talk_topic", "id": T + "_WIN", "dynamic_line": win_line,
         "responses": [{"text": "Thanks!", "topic": T}]},
        {"type": "talk_topic", "id": T + "_REMATCH_WON", "dynamic_line": "Still too strong for me.  Here, take these supplies for your trouble.",
         "responses": [{"text": "Thanks.", "topic": T}]},
        {"type": "talk_topic", "id": T + "_FORFEIT", "dynamic_line": "Hmph.  Come back when you and your Pokémon are ready.",
         "responses": [{"text": "I will.", "topic": T}]},
    ]
    if extra_cond and battle_cond_text:
        topics.append({"type": "talk_topic", "id": T + "_NOT_READY", "dynamic_line": battle_cond_text,
                       "responses": [{"text": "I understand.", "topic": T}]})
    return topics


def gym_leader_content():
    out = []
    for (tid, name, title, place, badge, need, team, intro, battle, win, after) in GYM_LEADERS:
        on_win = [
            {"u_spawn_item": badge},
            {"math": ["pkmn_badge_count = value_or(pkmn_badge_count, 0) + 1"]},
            {"u_spawn_item": "pkmn_loot_rare", "use_item_group": True},
            {"u_spawn_item": "pkmn_rare_candy", "count": 2},
            {"u_message": "You received the %s!  (<global_val:pkmn_badge_count>/8 badges)" % BADGE_NAMES[badge], "type": "good"},
        ]
        extra_cond = None
        not_ready = None
        if need:
            extra_cond = {"math": ["value_or(pkmn_badge_count, 0) >= %d" % need]}
            not_ready = "The League's rules haven't changed just because the world ended.  Come back when you have at least %d badge%s." % (need, "s" if need > 1 else "")
        if tid == "giovanni":
            extra_cond = {"and": [{"math": ["value_or(pkmn_badge_count, 0) >= 7"]},
                                  {"math": ["value_or(pkmn_rocket_hideout_cleared, 0) == 1"]}]}
            not_ready = "The Viridian Gym is closed.  Its leader is… away on business.  Come back when you have seven badges, and when you have dealt with a certain organization."
            on_win.append({"math": ["pkmn_giovanni_defeated = 1"]})
        out.append({"type": "npc", "id": "pkmn_npc_" + tid, "name_unique": name, "name_suffix": title,
                    "gender": "female" if tid in ("misty", "erika", "sabrina") else "male",
                    "class": "NC_PKMN_GYM_LEADER", "attitude": 0, "mission": 7,
                    "chat": "TALK_PKMN_" + tid.upper(), "faction": "pkmn_league"})
        out += trainer_topics(tid, name, team, intro, battle, win, after, on_win, extra_cond, not_ready)
    return out


BADGE_NAMES = {"pkmn_badge_boulder": "Boulder Badge", "pkmn_badge_cascade": "Cascade Badge",
               "pkmn_badge_thunder": "Thunder Badge", "pkmn_badge_rainbow": "Rainbow Badge",
               "pkmn_badge_soul": "Soul Badge", "pkmn_badge_marsh": "Marsh Badge",
               "pkmn_badge_volcano": "Volcano Badge", "pkmn_badge_earth": "Earth Badge"}


def rocket_content():
    out = []
    # Team Rocket grunts: one template per team so each spawns different Pokémon.
    for i, team in enumerate(ROCKET_TEAMS):
        tid = "rocket_grunt_%d" % (i + 1)
        T = "TALK_PKMN_" + tid.upper()
        out.append({"type": "npc", "id": "pkmn_npc_" + tid, "name_suffix": "Team Rocket Grunt",
                    "class": "NC_PKMN_ROCKET_GRUNT", "attitude": 1, "mission": 7, "chat": T, "faction": "pkmn_team_rocket"})
        topics = trainer_topics(
            tid, "Rocket Grunt", team,
            "Hey!  Team Rocket is taking over this place.  The world ended, so who's going to stop us?  Hand over your Pokémon, or else!",
            "You asked for it!  Get 'em!",
            "Urgh!  Team Rocket is blasting off again!  Here, take these stupid orders, I don't care anymore!",
            "I'm not talking to you.  The boss is going to kill me.",
            [{"u_spawn_item": "pkmn_rocket_orders"}, {"math": ["pkmn_rockets_defeated = value_or(pkmn_rockets_defeated, 0) + 1"]}],
            rematch=False,
            extra_responses=[{"text": "I'm not giving you anything.  [Attack]", "effect": "hostile", "topic": "TALK_DONE"}])
        # Grunt trainer IDs are shared: make the "won" flag per-NPC instead of global.
        for t in topics:
            js = json.dumps(t, ensure_ascii=False).replace("pkmn_trainer_%s_won" % tid, "n_pkmn_trainer_won")
            out.append(json.loads(js))
    # Rocket admin in the hideout.
    admin_team = [("arbok", 30), ("weezing", 31), ("golbat", 32), ("raticate", 30)]
    out.append({"type": "npc", "id": "pkmn_npc_rocket_admin", "name_unique": "Archer", "name_suffix": "Team Rocket Executive",
                "class": "NC_PKMN_ROCKET_ADMIN", "attitude": 1, "mission": 7, "chat": "TALK_PKMN_ROCKET_ADMIN",
                "faction": "pkmn_team_rocket"})
    out += trainer_topics(
        "rocket_admin", "Archer", admin_team,
        "So you're the one who has been interfering with our operations.  Team Rocket survived the end of the world and we will rule what's left of it.  Our boss, Giovanni, has gone to Viridian to rebuild.  You'll never reach him.",
        "I'll show you what happens to those who cross Team Rocket!",
        "I… I lost?  Team Rocket is finished here.  Take the Silph Scope.  We stole it anyway.  The boss is at the Viridian Gym… not that it'll help you.",
        "Leave me alone.  Team Rocket is through.",
        [{"u_spawn_item": "pkmn_silph_scope"}, {"math": ["pkmn_rocket_hideout_cleared = 1"]},
         {"u_spawn_item": "pkmn_ball_ultra", "count": 3},
         {"u_message": "Team Rocket's hideout has been cleared!", "type": "good"}],
        rematch=False,
        extra_responses=[{"text": "Enough talk.  [Attack]", "effect": "hostile", "topic": "TALK_DONE"}])
    return out


def rival_content():
    tid = "rival"
    team = RIVAL_TEAM
    out = [{"type": "npc", "id": "pkmn_npc_rival", "name_unique": "Gary Oak", "name_suffix": "Pokémon League Champion",
            "gender": "male", "class": "NC_PKMN_GYM_LEADER", "attitude": 0, "mission": 7, "chat": "TALK_PKMN_RIVAL",
            "faction": "pkmn_league"}]
    out += trainer_topics(
        tid, "Gary", team,
        "Hey!  I was looking forward to seeing you!  While you were busy scavenging, I took the Indigo Plateau.  My Pokémon are the toughest anywhere, and I'm the Champion of what's left of the League.  Do you know what that means?  I'll tell you.  I am the most powerful trainer in the world!",
        "Hahaha!  Let's go!  Smell ya later!",
        "NO!  That can't be!  You beat my best!  After all that work to become League Champion?  My reign is over already?  It's not fair!  …Fine.  You're the Champion now.  Gramps is going to love this.",
        "Hey.  Gramps was right about you.  You treat your Pokémon like partners, not weapons.  Maybe that's why you won.",
        [{"math": ["pkmn_champion = 1"]}, {"u_spawn_item": "pkmn_ball_master"},
         {"u_spawn_item": "pkmn_max_revive", "count": 3},
         {"u_message": "Congratulations!  You are the new Pokémon League Champion!", "type": "good", "popup": True}],
        extra_cond={"math": ["value_or(pkmn_badge_count, 0) >= 8"]},
        battle_cond_text="Ha!  You don't even have all eight badges.  The League has rules.  Come back when you're a real trainer!")
    return out


# ===========================================================================
# Professor Oak, Nurse Joy, Poké Mart, Officer Jenny, Safari warden, Mr. Fuji
# ===========================================================================
STARTERS = [("bulbasaur", "the Grass-type Pokémon, Bulbasaur"), ("charmander", "the Fire-type Pokémon, Charmander"),
            ("squirtle", "the Water-type Pokémon, Squirtle")]


def oak_content():
    out = [{"type": "npc", "id": "pkmn_npc_oak", "name_unique": "Professor Oak", "name_suffix": "Pokémon Professor",
            "gender": "male", "class": "NC_PKMN_PROFESSOR", "attitude": 0, "mission": 7, "chat": "TALK_PKMN_OAK",
            "faction": "pkmn_league", "mission_offered": "MISSION_PKMN_OAK_PARCEL"}]
    got_starter = {"math": ["value_or(pkmn_got_starter, 0) == 1"]}
    responses = [
        {"text": "Professor, I'd like a Pokémon of my own.", "condition": {"not": got_starter}, "topic": "TALK_PKMN_OAK_STARTER"},
        {"text": "What happened here?", "topic": "TALK_PKMN_OAK_STORY"},
        {"text": "How do I catch and train Pokémon?", "topic": "TALK_PKMN_OAK_TUTORIAL"},
        {"text": "How is my Pokédex coming along?", "condition": got_starter, "topic": "TALK_PKMN_OAK_DEX"},
        {"text": "Do you have any work for me?", "condition": got_starter, "topic": "TALK_MISSION_LIST"},
        {"text": "I found a fossil.  Can you revive it?", "condition": {"or": [{"u_has_item": "pkmn_fossil_helix"}, {"u_has_item": "pkmn_fossil_dome"}, {"u_has_item": "pkmn_old_amber"}]},
         "topic": "TALK_PKMN_OAK_FOSSIL"},
        {"text": "Could you spare a few Poké Balls?", "condition": {"and": [got_starter, {"or": [{"math": ["time_since(pkmn_oak_balls) == -1"]}, {"math": ["time_since(pkmn_oak_balls) > time('3 d')"]}]}]},
         "effect": [{"math": ["pkmn_oak_balls = time('now')"]}, {"u_spawn_item": "pkmn_ball_poke", "count": 5}],
         "topic": "TALK_PKMN_OAK_BALLS"},
        {"text": "Goodbye, Professor.", "topic": "TALK_DONE"},
    ]
    out.append({"type": "talk_topic", "id": "TALK_PKMN_OAK",
                "dynamic_line": {"math": ["value_or(pkmn_got_starter, 0) == 1"],
                                 "yes": "Ah, <name_g>!  How are you and your Pokémon getting along?",
                                 "no": "Hello there!  Welcome to the world of Pokémon!  My name is Oak.  People call me the Pokémon Prof.  This world is inhabited by creatures called Pokémon, and they survived the end of the world far better than we did.  For some people, Pokémon are pets.  Others use them for fights.  Myself, I study Pokémon as a profession.  And now, with the cities overrun, I think they may be our best hope."},
                "responses": responses})
    starter_responses = []
    for pid, desc in STARTERS:
        starter_responses.append({
            "text": "I choose %s!" % pname(pid),
            "effect": [
                {"math": ["pkmn_got_starter = 1"]},
                {"u_spawn_monster": "pkmn_" + pid, "real_count": 1, "min_radius": 1, "max_radius": 3, "friendly": True,
                 "mon_variables": {"pkmn_level": "5", "pkmn_xp": "0"},
                 "spawn_message": "%s pops out of its Poké Ball!" % pname(pid)},
                {"u_spawn_item": "pkmn_ball_registered"},
                {"u_spawn_item": "pkmn_pokedex"},
                {"u_spawn_item": "pkmn_ball_poke", "count": 5},
                {"u_spawn_item": "pkmn_potion", "count": 3},
                {"u_spawn_item": "pkmn_badge_case"},
                {"run_eocs": "EOC_PKMN_STARTER_SETUP"},
            ],
            "topic": "TALK_PKMN_OAK_STARTER_CHOSEN"})
    starter_responses.append({"text": "Let me think about it.", "topic": "TALK_PKMN_OAK"})
    out += [
        {"type": "talk_topic", "id": "TALK_PKMN_OAK_STARTER",
         "dynamic_line": "I kept three Pokémon safe in their Poké Balls through all of this.  Bulbasaur, Charmander, and Squirtle.  Each one is a fine partner.  Which will you choose?  Choose carefully; it will be your friend in a dangerous world.",
         "responses": starter_responses},
        {"type": "talk_topic", "id": "TALK_PKMN_OAK_STARTER_CHOSEN",
         "dynamic_line": "So you've chosen!  That Pokémon is really energetic.  Take this Pokédex too, it records data on every Pokémon you catch.  And here are some Poké Balls and Potions.  Your Pokémon's registered Poké Ball lets you recall it whenever you want; use it next to your Pokémon.  Complete the Pokédex for me.  It's my dream, and the world could use a few more dreams.",
         "responses": [{"text": "I'll do my best, Professor!", "topic": "TALK_PKMN_OAK"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_OAK_STORY",
         "dynamic_line": "When the dead began to walk, most people fled.  But the Pokémon stayed.  Wild Pokémon are spreading into the empty towns, and trainers who kept their partners have survived where others didn't.  Pokémon Centers still run on generators and the stubbornness of nurses, the Gym Leaders still hold their gyms, and Team Rocket… well, Team Rocket sees an opportunity.  I believe a skilled trainer could make a real difference.",
         "responses": [{"text": "I see.", "topic": "TALK_PKMN_OAK"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_OAK_TUTORIAL",
         "dynamic_line": "First, weaken a wild Pokémon by battling it with your own.  Use the Pokédex to check its health.  Then activate a Poké Ball to throw it.  The weaker the Pokémon, the better your chances.  Sleep, paralysis, freezing, burns and poison help a great deal too, and Great and Ultra Balls work better still.  Once caught, a Pokémon follows you and fights at your side.  It gains experience from every battle, grows in level, and evolves when the time is right.  Some evolve only with evolution stones, and a few needed a trade in the old days; the Link Cable handles that.  If one of your Pokémon faints, recall it with its Poké Ball immediately!  A fainted Pokémon that takes another hit will not get back up.",
         "responses": [{"text": "Thanks, Professor.", "topic": "TALK_PKMN_OAK"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_OAK_DEX",
         "dynamic_line": {"math": ["value_or(pkmn_dex_count, 0) >= 151"],
                          "yes": "Incredible!  You've completed the Pokédex!  All 151 Pokémon of Kanto, even in a world like this.  Congratulations!",
                          "no": "Let me see… You've registered <global_val:pkmn_dex_count> Pokémon so far, and caught <global_val:pkmn_caught_total> in all.  Keep going!  Different Pokémon live in forests, fields, rivers, the coast, caves and even sewers.  Some only live in special places."},
         "responses": [{"text": "I'll keep at it.", "topic": "TALK_PKMN_OAK"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_OAK_BALLS",
         "dynamic_line": "Of course!  Here are five Poké Balls.  Come back in a few days if you need more.",
         "responses": [{"text": "Thanks!", "topic": "TALK_PKMN_OAK"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_OAK_FOSSIL",
         "dynamic_line": "Oh!  A fossil of an ancient Pokémon!  My lab equipment can extract its DNA and regenerate it.  Which one should I revive?",
         "responses": [
             {"text": "The Helix Fossil.", "condition": {"u_has_item": "pkmn_fossil_helix"},
              "effect": [{"u_consume_item": "pkmn_fossil_helix", "count": 1},
                         {"u_spawn_monster": "pkmn_omanyte", "real_count": 1, "min_radius": 1, "max_radius": 3, "friendly": True, "mon_variables": {"pkmn_level": "30"}},
                         {"u_spawn_item": "pkmn_ball_registered"}],
              "topic": "TALK_PKMN_OAK_FOSSIL_DONE"},
             {"text": "The Dome Fossil.", "condition": {"u_has_item": "pkmn_fossil_dome"},
              "effect": [{"u_consume_item": "pkmn_fossil_dome", "count": 1},
                         {"u_spawn_monster": "pkmn_kabuto", "real_count": 1, "min_radius": 1, "max_radius": 3, "friendly": True, "mon_variables": {"pkmn_level": "30"}},
                         {"u_spawn_item": "pkmn_ball_registered"}],
              "topic": "TALK_PKMN_OAK_FOSSIL_DONE"},
             {"text": "The Old Amber.", "condition": {"u_has_item": "pkmn_old_amber"},
              "effect": [{"u_consume_item": "pkmn_old_amber", "count": 1},
                         {"u_spawn_monster": "pkmn_aerodactyl", "real_count": 1, "min_radius": 1, "max_radius": 3, "friendly": True, "mon_variables": {"pkmn_level": "30"}},
                         {"u_spawn_item": "pkmn_ball_registered"}],
              "topic": "TALK_PKMN_OAK_FOSSIL_DONE"},
             {"text": "Never mind.", "topic": "TALK_PKMN_OAK"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_OAK_FOSSIL_DONE",
         "dynamic_line": "There!  It's alive!  An ancient Pokémon, breathing again after millions of years.  Take good care of it.  Here's a registered Poké Ball for it.",
         "responses": [{"text": "Amazing.  Thank you, Professor.", "topic": "TALK_PKMN_OAK"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_NEED_POKEMON",
         "dynamic_line": "You don't have any Pokémon with you!  Send one out of its Poké Ball first.",
         "responses": [{"text": "Oh, right.", "topic": "TALK_DONE"}]},
        {"type": "effect_on_condition", "id": "EOC_PKMN_STARTER_SETUP",
         "effect": [{"u_run_monster_eocs": [{"id": "EOC_PKMN_STARTER_SETUP_MON",
                                             "condition": {"and": [{"u_has_species": "POKEMON"}, {"math": ["u_val('friendly') != 0"]}]},
                                             "effect": [{"u_add_effect": "pet", "duration": "PERMANENT"},
                                                        {"run_eocs": "EOC_PKMN_APPLY_LEVEL"}]}],
                     "monster_range": 6}]},
    ]
    return out


def joy_content():
    heal = {"u_run_monster_eocs": [{"id": "EOC_PKMN_CENTER_HEAL_MON",
                                    "condition": {"and": [{"u_has_species": "POKEMON"}, {"math": ["u_val('friendly') != 0"]}]},
                                    "effect": [{"math": ["u_hp('ALL') = u_hp_max('torso')"]}] +
                                              [{"u_lose_effect": e} for e in ["pkmn_fainted", "pkmn_paralysis", "pkmn_sleep", "pkmn_freeze",
                                                                              "pkmn_burn", "pkmn_poison", "pkmn_slowed", "stunned", "downed"]] +
                                              [{"u_add_effect": "pkmn_pokecenter_heal", "duration": "1 h"}]}],
            "monster_range": 15}
    out = [
        {"type": "npc", "id": "pkmn_npc_nurse_joy", "name_unique": "Nurse Joy", "name_suffix": "Pokémon Center",
         "gender": "female", "class": "NC_PKMN_NURSE", "attitude": 0, "mission": 7, "chat": "TALK_PKMN_JOY",
         "faction": "pkmn_league", "mission_offered": "MISSION_PKMN_JOY_SUPPLIES"},
        {"type": "talk_topic", "id": "TALK_PKMN_JOY",
         "dynamic_line": "Hello, and welcome to the Pokémon Center.  We restore your tired Pokémon to full health.  Even now.  Especially now.",
         "responses": [
             {"text": "Please heal my Pokémon.", "effect": [heal, {"u_assign_activity": "ACT_WAIT", "duration": "5 minutes"}], "topic": "TALK_PKMN_JOY_HEALED"},
             {"text": "Can you patch me up too?", "condition": {"math": ["u_hp('ALL') < u_hp_max('torso') + u_hp_max('head') + u_hp_max('arm_l') + u_hp_max('arm_r') + u_hp_max('leg_l') + u_hp_max('leg_r')"]},
              "effect": [{"u_spawn_item": "bandages", "count": 2}], "topic": "TALK_PKMN_JOY_PATCH"},
             {"text": "Do you need help with anything?", "topic": "TALK_MISSION_LIST"},
             {"text": "Goodbye.", "topic": "TALK_DONE"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_JOY_HEALED",
         "dynamic_line": "Thank you for waiting.  We've restored your Pokémon to full health.  We hope to see you again!",
         "responses": [{"text": "Thank you!", "topic": "TALK_DONE"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_JOY_PATCH",
         "dynamic_line": "We're a Pokémon Center, not a hospital… but here, take some bandages.  Please be careful out there.",
         "responses": [{"text": "Thanks.", "topic": "TALK_PKMN_JOY"}]},
    ]
    return out


def mart_content():
    return [
        {"type": "npc", "id": "pkmn_npc_mart_clerk", "name_suffix": "Poké Mart clerk", "class": "NC_PKMN_MART",
         "attitude": 0, "mission": 3, "chat": "TALK_PKMN_MART", "faction": "pkmn_league"},
        {"type": "talk_topic", "id": "TALK_PKMN_MART",
         "dynamic_line": "Hi there!  May I help you?  We still have Poké Balls, Potions and the rest.  Money's not what it used to be, so we take trades.",
         "responses": [
             {"text": "Let's trade.", "effect": "start_trade", "topic": "TALK_PKMN_MART"},
             {"text": "Professor Oak sent me for a parcel.", "condition": {"and": [{"u_has_mission": "MISSION_PKMN_OAK_PARCEL"}, {"not": {"u_has_item": "pkmn_oaks_parcel"}}]},
              "effect": {"u_spawn_item": "pkmn_oaks_parcel"}, "topic": "TALK_PKMN_MART_PARCEL"},
             {"text": "Goodbye.", "topic": "TALK_DONE"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_MART_PARCEL",
         "dynamic_line": "Oh, you're from Professor Oak's lab?  He ordered this before… everything.  It's been sitting in the back.  Please take it to him.",
         "responses": [{"text": "Will do.", "topic": "TALK_PKMN_MART"}]},
    ]


def jenny_content():
    return [
        {"type": "npc", "id": "pkmn_npc_jenny", "name_unique": "Officer Jenny", "name_suffix": "Police",
         "gender": "female", "class": "NC_PKMN_OFFICER", "attitude": 0, "mission": 7, "chat": "TALK_PKMN_JENNY",
         "faction": "pkmn_league", "mission_offered": "MISSION_PKMN_JENNY_ROCKET_1"},
        {"type": "talk_topic", "id": "TALK_PKMN_JENNY",
         "dynamic_line": "Officer Jenny.  What's left of the department, anyway.  If you're a trainer, I could use your help.  Team Rocket is using the chaos to steal Pokémon and loot what's left of Silph Co.",
         "responses": [
             {"text": "Tell me about Team Rocket.", "topic": "TALK_PKMN_JENNY_ROCKET"},
             {"text": "Do you have a job for me?", "topic": "TALK_MISSION_LIST"},
             {"text": "Goodbye, officer.", "topic": "TALK_DONE"}]},
        {"type": "talk_topic", "id": "TALK_PKMN_JENNY_ROCKET",
         "dynamic_line": "A criminal gang that uses Pokémon for crime.  Black uniforms, big red R.  Their grunts carry a couple of Pokémon each and they don't fight fair.  Rumor is their boss is an old Gym Leader.",
         "responses": [{"text": "I'll keep an eye out.", "topic": "TALK_PKMN_JENNY"}]},
    ]


def warden_content():
    return [
        {"type": "npc", "id": "pkmn_npc_safari_warden", "name_unique": "Safari Warden", "name_suffix": "Safari Zone",
         "gender": "male", "class": "NC_PKMN_WARDEN", "attitude": 0, "mission": 3, "chat": "TALK_PKMN_WARDEN",
         "faction": "pkmn_league", "mission_offered": "MISSION_PKMN_WARDEN_CATCH"},
        {"type": "talk_topic", "id": "TALK_PKMN_WARDEN",
         "dynamic_line": "Welcome to the Safari Zone!  The fences kept most of the dead out and the Pokémon in.  Rare Pokémon live here: Chansey, Kangaskhan, Tauros, Scyther, Pinsir, even Dratini.  You'll want Safari Balls.",
         "responses": [
             {"text": "I'll buy some Safari Balls.", "effect": "start_trade", "topic": "TALK_PKMN_WARDEN"},
             {"text": "Can I help around here?", "topic": "TALK_MISSION_LIST"},
             {"text": "Goodbye.", "topic": "TALK_DONE"}]},
    ]


# ===========================================================================
# Missions
# ===========================================================================
def mission(mid, name, desc, goal, dialogue, origins=("ORIGIN_SECONDARY",), followup=None, end_effects=None,
            start=None, extra=None, value=10000, difficulty=2):
    m = {"id": mid, "type": "mission_definition", "name": {"str": name}, "description": desc,
         "goal": goal, "difficulty": difficulty, "value": value, "origins": list(origins), "dialogue": dialogue}
    if followup:
        m["followup"] = followup
    if end_effects:
        m["end"] = {"effect": end_effects}
    if start:
        m["start"] = start
    if extra:
        m.update(extra)
    return m


def dlg(describe, offer, accepted, rejected, advice, inquire, success, failure="Don't give up.  Come back when you're ready."):
    return {"describe": describe, "offer": offer, "accepted": accepted, "rejected": rejected, "advice": advice,
            "inquire": inquire, "success": success, "success_lie": "That doesn't look right to me.", "failure": failure}


def missions_content():
    out = []
    # --- Professor Oak: the Pokédex line ---------------------------------
    out.append(mission(
        "MISSION_PKMN_OAK_PARCEL", "Deliver Oak's Parcel",
        "Professor Oak ordered a parcel from the Poké Mart before the Cataclysm.  Pick it up from any Poké Mart clerk and bring it back to him.",
        "MGOAL_FIND_ITEM",
        dlg("My parcel from the Poké Mart.", "Before you go off adventuring, could you do an old man a favor?  I ordered a parcel from the Poké Mart before everything fell apart.  If the clerk is still there, would you fetch it for me?",
            "Splendid!  The Poké Mart is in town.", "Ah, maybe later then.", "Just ask the clerk for Professor Oak's parcel.",
            "Did you get my parcel?", "Ah, this is the custom Poké Ball I ordered!  Thank you.  Now, I have a far bigger request…"),
        origins=("ORIGIN_SECONDARY",), followup="MISSION_PKMN_OAK_DEX_5",
        extra={"item": "pkmn_oaks_parcel", "count": 1},
        start={"assign_mission_target": {"om_terrain": "pkmn_mart", "om_special": "pkmn_mart", "reveal_radius": 1, "random": False}},
        end_effects=[{"u_spawn_item": "pkmn_ball_great", "count": 3}], value=5000, difficulty=1))
    dex_steps = [(5, "MISSION_PKMN_OAK_DEX_5", "MISSION_PKMN_OAK_DEX_15", [{"u_spawn_item": "pkmn_ball_great", "count": 5}, {"u_spawn_item": "pkmn_super_potion", "count": 3}]),
                 (15, "MISSION_PKMN_OAK_DEX_15", "MISSION_PKMN_OAK_DEX_40", [{"u_spawn_item": "pkmn_rare_candy", "count": 3}, {"u_spawn_item": "pkmn_revive", "count": 2}]),
                 (40, "MISSION_PKMN_OAK_DEX_40", "MISSION_PKMN_OAK_DEX_80", [{"u_spawn_item": "pkmn_ball_ultra", "count": 5}, {"u_spawn_item": "pkmn_link_cable"}]),
                 (80, "MISSION_PKMN_OAK_DEX_80", "MISSION_PKMN_OAK_DEX_151", [{"u_spawn_item": "pkmn_max_revive", "count": 3}, {"u_spawn_item": "pkmn_stone_moon"}]),
                 (151, "MISSION_PKMN_OAK_DEX_151", None, [{"u_spawn_item": "pkmn_ball_master"}, {"u_spawn_item": "pkmn_diploma"}])]
    for n, mid, nxt, rewards in dex_steps:
        out.append(mission(
            mid, "Register %d Pokémon in the Pokédex" % n,
            "Professor Oak wants you to register %d different species of Pokémon in your Pokédex.  A species is registered the first time you have one of your own." % n,
            "MGOAL_CONDITION",
            dlg("The Pokédex needs more data.", "The Pokédex is incomplete without field data.  Could you register %d different kinds of Pokémon?" % n,
                "Wonderful!  Off you go.", "Oh, well, I'll keep at it myself.", "Different Pokémon live in different places.  Forests, rivers, the sea, caves… even the sewers.",
                "How is the Pokédex coming along?",
                "Splendid work!  %d Pokémon!  Here, take these; you've earned them." % n),
            followup=nxt, end_effects=rewards,
            extra={"goal_condition": {"math": ["value_or(pkmn_dex_count, 0) >= %d" % n]}}, value=10000 + 200 * n, difficulty=1 + n // 30))
    out.append(mission(
        "MISSION_PKMN_OAK_LEGENDS", "The Legendary Birds",
        "Articuno, Zapdos and Moltres have been sighted.  Catch all three legendary birds.  Professor Oak marked their roosts on your map.",
        "MGOAL_CONDITION",
        dlg("The legendary birds.", "There are reports of three legendary birds: Articuno in an icy sea cave, Zapdos at the old power plant, and Moltres in a volcanic cave.  If you could catch them… well.  I've marked where I think they are.",
            "Be careful!  They're far stronger than anything you've faced.", "Not yet?  I understand.", "Bring Ultra Balls and Pokémon with an advantage.  Put them to sleep if you can.",
            "Any luck with the legendary birds?", "You actually did it!  All three!  History in the making."),
        origins=("ORIGIN_SECONDARY",),
        start={"assign_mission_target": {"om_terrain": "pkmn_power_plant", "om_special": "pkmn_power_plant", "reveal_radius": 2, "random": True, "search_range": 240}},
        end_effects=[{"u_spawn_item": "pkmn_max_revive", "count": 5}, {"u_spawn_item": "pkmn_rare_candy", "count": 5}],
        extra={"goal_condition": {"and": [{"math": ["value_or(pkmn_dex_articuno, 0) == 1"]}, {"math": ["value_or(pkmn_dex_zapdos, 0) == 1"]}, {"math": ["value_or(pkmn_dex_moltres, 0) == 1"]}]}},
        value=80000, difficulty=8))
    out.append(mission(
        "MISSION_PKMN_OAK_MEWTWO", "The Pokémon in the Cave",
        "A Pokémon created in a lab is said to hide in a sealed cave.  Find it and catch it.",
        "MGOAL_CONDITION",
        dlg("A cave, and something inside it.", "There is a cave that was sealed off by the League long ago.  Something terribly powerful lives in there: a Pokémon called Mewtwo, created by human hands.  Only the Champion should even attempt this.",
            "May fortune be with you.", "That's probably wise.", "It is psychic.  Bug and Ghost moves are your best bet, and bring every Ultra Ball you have.",
            "Have you been to the cave?", "Mewtwo… with you.  Treat it kindly.  It has known little kindness."),
        start={"assign_mission_target": {"om_terrain": "pkmn_cerulean_cave", "om_special": "pkmn_cerulean_cave", "reveal_radius": 2, "random": True, "search_range": 240}},
        end_effects=[{"u_spawn_item": "pkmn_full_restore", "count": 5}],
        extra={"goal_condition": {"math": ["value_or(pkmn_dex_mewtwo, 0) == 1"]}}, value=100000, difficulty=10))
    # --- The Pokémon League ---------------------------------------------
    gyms = [("brock", "pkmn_gym_pewter"), ("misty", "pkmn_gym_cerulean"), ("surge", "pkmn_gym_vermilion"),
            ("erika", "pkmn_gym_celadon"), ("koga", "pkmn_gym_fuchsia"), ("sabrina", "pkmn_gym_saffron"),
            ("blaine", "pkmn_gym_cinnabar"), ("giovanni", "pkmn_gym_viridian")]
    for i, (leader, omt) in enumerate(gyms):
        lname = [g[1] for g in GYM_LEADERS if g[0] == leader][0]
        nxt = "MISSION_PKMN_LEAGUE_%d" % (i + 2) if i < 7 else "MISSION_PKMN_LEAGUE_CHAMPION"
        out.append(mission(
            "MISSION_PKMN_LEAGUE_%d" % (i + 1), "Defeat Gym Leader %s" % lname,
            "Challenge %s at their gym and win the badge.  The gym is marked on your map." % lname,
            "MGOAL_CONDITION",
            dlg("The %s badge." % lname, "Every trainer worth the name collects the eight League badges.  Your next challenge is %s.  I've marked the gym on your map." % lname,
                "Good luck!", "Come back when you're ready.", "Gym Leaders specialize in one type.  Bring Pokémon that have the advantage.",
                "Did you beat %s?" % lname, "Another badge!  You're becoming a real trainer."),
            followup=nxt,
            start={"assign_mission_target": {"om_terrain": omt, "om_special": omt, "reveal_radius": 1, "random": False}},
            end_effects=[{"u_spawn_item": "pkmn_ball_great", "count": 3}],
            extra={"goal_condition": {"math": ["value_or(pkmn_trainer_%s_won, 0) == 1" % leader]}}, value=20000 + 5000 * i, difficulty=2 + i))
    out.append(mission(
        "MISSION_PKMN_LEAGUE_CHAMPION", "Become the Pokémon League Champion",
        "With all eight badges, travel to the Indigo Plateau and defeat the reigning Champion.",
        "MGOAL_CONDITION",
        dlg("The Indigo Plateau.", "You have all eight badges!  The Pokémon League waits at the Indigo Plateau.  The Champion there… well, you'll see.  I've marked it on your map.",
            "Show them what you're made of!", "Rest up first.  That's sensible.", "The Champion uses a balanced team, with a Charizard as the ace.",
            "Have you been to the Indigo Plateau?", "Champion!  I knew it.  Now then, how about that Pokédex…"),
        followup="MISSION_PKMN_OAK_LEGENDS",
        start={"assign_mission_target": {"om_terrain": "pkmn_indigo_plateau", "om_special": "pkmn_indigo_plateau", "reveal_radius": 1, "random": True, "search_range": 240}},
        end_effects=[{"u_spawn_item": "pkmn_rare_candy", "count": 5}],
        extra={"goal_condition": {"math": ["value_or(pkmn_champion, 0) == 1"]}}, value=100000, difficulty=9))
    # --- Nurse Joy ---------------------------------------------------------
    out.append(mission(
        "MISSION_PKMN_JOY_SUPPLIES", "Medical supplies for the Pokémon Center",
        "Nurse Joy needs 10 bandages to keep the Pokémon Center running.",
        "MGOAL_FIND_ITEM",
        dlg("Bandages.", "We're running low on everything, but bandages most of all.  Could you bring me ten?  I'll pay you in Pokémon medicine.",
            "Thank you so much!", "I understand.", "Pharmacies and hospitals are dangerous, but houses often have first aid supplies.",
            "Any luck with the bandages?", "These will help so many Pokémon.  Please take these."),
        origins=("ORIGIN_SECONDARY",), followup="MISSION_PKMN_JOY_ANTIBIOTICS",
        extra={"item": "bandages", "count": 10}, end_effects=[{"u_spawn_item": "pkmn_super_potion", "count": 4}, {"u_spawn_item": "pkmn_revive", "count": 2}]))
    out.append(mission(
        "MISSION_PKMN_JOY_ANTIBIOTICS", "Antibiotics for the Pokémon Center",
        "Nurse Joy needs antibiotics for infected Pokémon.",
        "MGOAL_FIND_ITEM",
        dlg("Antibiotics.", "Some of the Pokémon brought in have infected bites from the dead.  I need antibiotics.  Five doses would save a lot of lives.",
            "Thank you!", "I'll manage somehow.", "Hospitals and pharmacies, if you're brave.",
            "Did you find antibiotics?", "This is wonderful.  Here, my Chansey wants you to have these."),
        followup="MISSION_PKMN_JOY_ZOMBIES",
        extra={"item": "antibiotics", "count": 5}, end_effects=[{"u_spawn_item": "pkmn_full_restore", "count": 2}, {"u_spawn_item": "pkmn_max_revive", "count": 1}]))
    out.append(mission(
        "MISSION_PKMN_JOY_ZOMBIES", "Clear the dead around the Pokémon Center",
        "The dead keep wandering up to the Pokémon Center.  Destroy 25 zombies.",
        "MGOAL_KILL_MONSTER_SPEC",
        dlg("The zombies outside.", "The shamblers keep coming to the doors.  The Pokémon are frightened.  Could you thin them out?  Twenty-five should give us some peace.",
            "Please be careful.", "I understand.", "Let your Pokémon fight with you, they'll gain experience too.",
            "How is it going out there?", "It's so much quieter now.  Thank you, truly."),
        extra={"monster_species": "ZOMBIE", "monster_kill_goal": 25}, end_effects=[{"u_spawn_item": "pkmn_rare_candy", "count": 3}]))
    # --- Officer Jenny: Team Rocket ---------------------------------------
    out.append(mission(
        "MISSION_PKMN_JENNY_ROCKET_1", "Team Rocket's orders",
        "Defeat Team Rocket grunts in Pokémon battles and bring back a copy of their orders.",
        "MGOAL_FIND_ITEM",
        dlg("Team Rocket's plans.", "I need to know what Team Rocket is planning.  Their grunts carry orders.  Beat one in a Pokémon battle and bring me the papers.",
            "Good.  They hang around towns, sometimes near Pokémon Centers.", "Fine.", "Grunts use weak Pokémon: Rattata, Zubat, Ekans, Koffing.  Any decent team can beat them.",
            "Got those orders?", "A hideout… and a 'Project M2'.  This is worse than I thought."),
        followup="MISSION_PKMN_JENNY_ROCKET_2", extra={"item": "pkmn_rocket_orders", "count": 1},
        end_effects=[{"u_spawn_item": "pkmn_ball_great", "count": 5}]))
    out.append(mission(
        "MISSION_PKMN_JENNY_ROCKET_2", "Raid the Rocket Hideout",
        "Find Team Rocket's hideout beneath the old game corner, defeat their executive, and recover what they stole from Silph Co.",
        "MGOAL_CONDITION",
        dlg("The Rocket Hideout.", "The orders point to a hideout under an old game corner.  I've marked it on your map.  Their executive, Archer, runs things there.  Take him down.",
            "Be careful down there.", "I can't do this alone, you know.", "Take the stairs down.  Expect several grunts.",
            "Have you raided the hideout?", "You did it!  With Archer beaten, Team Rocket is on the ropes.  But their boss is still out there… Viridian City, you said?"),
        followup="MISSION_PKMN_JENNY_ROCKET_3",
        start={"assign_mission_target": {"om_terrain": "pkmn_rocket_hideout", "om_special": "pkmn_rocket_hideout", "reveal_radius": 1, "random": False}},
        extra={"goal_condition": {"math": ["value_or(pkmn_rocket_hideout_cleared, 0) == 1"]}},
        end_effects=[{"u_spawn_item": "pkmn_ball_ultra", "count": 5}, {"u_spawn_item": "pkmn_full_restore", "count": 2}], value=40000, difficulty=6))
    out.append(mission(
        "MISSION_PKMN_JENNY_ROCKET_3", "Defeat Giovanni",
        "Giovanni, the boss of Team Rocket, is the Viridian City Gym Leader.  Beat him once and for all.  He will not accept a challenge until you hold seven badges.",
        "MGOAL_CONDITION",
        dlg("Giovanni.", "The boss of Team Rocket is Giovanni, the Viridian Gym Leader.  Beat him at his own game and Team Rocket falls apart.",
            "Go get him.", "I'll wait.", "He uses Ground-type Pokémon.  Water and Grass moves will serve you well.",
            "Is it done?", "Team Rocket is finished.  The people of Kanto owe you, trainer.  Take this: Silph Co. made it for the police."),
        extra={"goal_condition": {"math": ["value_or(pkmn_giovanni_defeated, 0) == 1"]}},
        end_effects=[{"u_spawn_item": "pkmn_ball_master"}], value=80000, difficulty=8))
    # --- Safari Zone -----------------------------------------------------------
    out.append(mission(
        "MISSION_PKMN_WARDEN_CATCH", "Safari Zone survey",
        "The Safari Zone warden wants proof that the rare Pokémon still live here: register Chansey, Kangaskhan and Tauros.",
        "MGOAL_CONDITION",
        dlg("A survey of the Safari Zone.", "I don't know how many of our rare Pokémon survived.  Catch a Chansey, a Kangaskhan and a Tauros for me, and register them in your Pokédex.",
            "Thanks!  Good hunting.", "Too bad.", "They're skittish.  Safari Balls work better than normal Poké Balls.",
            "Found them?", "They made it!  Here, take this, I found it in the brush years ago."),
        extra={"goal_condition": {"and": [{"math": ["value_or(pkmn_dex_chansey, 0) == 1"]}, {"math": ["value_or(pkmn_dex_kangaskhan, 0) == 1"]}, {"math": ["value_or(pkmn_dex_tauros, 0) == 1"]}]}},
        end_effects=[{"u_spawn_item": "pkmn_stone_leaf"}, {"u_spawn_item": "pkmn_stone_water"}, {"u_spawn_item": "pkmn_ball_safari", "count": 10}],
        value=30000, difficulty=4))
    # Hook the League line and Rocket line onto Oak's later dialogue.
    return out


# ===========================================================================
# Factions and NPC classes
# ===========================================================================
def factions_and_classes():
    rel_friend = {"kill on sight": False, "watch your back": True, "share my stuff": True, "guard your stuff": True,
                  "lets you in": True, "defends your space": True, "knows your voice": True}
    out = [
        {"type": "faction", "id": "pkmn_league", "name": "Pokémon League", "likes_u": 20, "respects_u": 10,
         "known_by_u": True, "size": 40, "power": 40, "wealth": 10000000, "currency": "pkmn_poke_dollar",
         "description": "What remains of the Pokémon League: Gym Leaders, Pokémon Center nurses, Poké Mart clerks and Professor Oak.  They keep the old traditions alive and help trainers wherever they can.",
         "relations": {"pkmn_league": rel_friend, "your_followers": {"kill on sight": False, "lets you in": True},
                       "pkmn_team_rocket": {"kill on sight": False}}},
        {"type": "faction", "id": "pkmn_team_rocket", "name": "Team Rocket", "likes_u": -10, "respects_u": 0,
         "known_by_u": False, "size": 30, "power": 50, "wealth": 5000000,
         "description": "A criminal syndicate that uses Pokémon for crime.  It survived the Cataclysm and is trying to seize what's left of Kanto.",
         "relations": {"pkmn_team_rocket": rel_friend}},
    ]
    classes = [
        ("NC_PKMN_PROFESSOR", "Pokémon Professor", "I study Pokémon.", "pkmn_worn_professor", []),
        ("NC_PKMN_NURSE", "Pokémon nurse", "I heal Pokémon.", "pkmn_worn_nurse", []),
        ("NC_PKMN_MART", "Poké Mart clerk", "I run the Poké Mart.", "pkmn_worn_casual", [{"group": "pkmn_mart_stock"}]),
        ("NC_PKMN_GYM_LEADER", "Gym Leader", "I lead a Pokémon Gym.", "pkmn_worn_casual", []),
        ("NC_PKMN_OFFICER", "police officer", "I keep the peace.", "pkmn_worn_officer", []),
        ("NC_PKMN_WARDEN", "Safari Zone warden", "I look after the Safari Zone.", "pkmn_worn_casual", [{"group": "pkmn_safari_stock"}]),
        ("NC_PKMN_ROCKET_GRUNT", "Team Rocket grunt", "I work for Team Rocket.", "pkmn_worn_rocket", []),
        ("NC_PKMN_ROCKET_ADMIN", "Team Rocket executive", "I run Team Rocket's operations.", "pkmn_worn_rocket", []),
    ]
    for cid, name, job, worn, shop in classes:
        c = {"type": "npc_class", "id": cid, "name": {"str": name}, "job_description": job, "common": False,
             "worn_override": worn, "carry_override": "pkmn_carry_trainer" if "ROCKET" not in cid else "pkmn_rocket_loot",
             "weapon_override": "EMPTY_GROUP",
             "skills": [{"skill": "ALL", "level": {"constant": 1}}, {"skill": "dodge", "bonus": {"rng": [1, 3]}}]}
        if shop:
            c["shopkeeper_item_group"] = shop
            c["sells_belongings"] = False
        if "ROCKET" in cid:
            c["skills"].append({"skill": "melee", "bonus": {"rng": [1, 3]}})
            c["weapon_override"] = "pkmn_rocket_weapon"
        out.append(c)
    out += [
        {"type": "item_group", "id": "pkmn_worn_professor", "subtype": "collection",
         "items": ["coat_lab", "dress_shirt", "pants", "socks", "dress_shoes", "briefs"]},
        {"type": "item_group", "id": "pkmn_worn_nurse", "subtype": "collection",
         "items": ["dress_shirt", "skirt", "socks", "sneakers", "panties", "bra"]},
        {"type": "item_group", "id": "pkmn_worn_casual", "subtype": "collection",
         "items": ["tshirt", "jeans", "socks", "sneakers", "boxer_shorts", "hoodie"]},
        {"type": "item_group", "id": "pkmn_worn_officer", "subtype": "collection",
         "items": ["dress_shirt", "police_breeches", "police_belt", "socks", "boots", "panties", "bra", "hat_ball"]},
        {"type": "item_group", "id": "pkmn_worn_rocket", "subtype": "collection",
         "items": ["tshirt", "pants_cargo", "socks", "boots", "boxer_shorts", "gloves_leather", "hat_ball"]},
        {"type": "item_group", "id": "pkmn_carry_trainer", "subtype": "collection",
         "items": [{"item": "pkmn_ball_poke", "count": [1, 3]}, {"item": "pkmn_potion", "prob": 50}]},
        {"type": "item_group", "id": "pkmn_rocket_weapon", "subtype": "distribution",
         "items": [{"item": "bat", "prob": 40}, {"item": "knife_hunting", "prob": 30}, {"item": "crowbar", "prob": 30}]},
        {"type": "item_group", "id": "pkmn_safari_stock", "subtype": "distribution",
         "items": [{"item": "pkmn_ball_safari", "prob": 80, "count": [5, 10]}, {"item": "pkmn_poke_food", "prob": 20, "count": [1, 3]}]},
        {"type": "ITEM", "id": "pkmn_poke_dollar", "name": {"str": "Poké Dollar coin"},
         "description": "A coin minted by the Pokémon League as currency for trainers after the old money stopped meaning anything.  Poké Marts and the League accept it.",
         "weight": "5 g", "volume": "1 ml", "price": "100 USD", "price_postapoc": "100 USD", "material": ["steel"],
         "symbol": "$", "color": "yellow", "stackable": True},
        {"type": "ITEM", "id": "pkmn_oaks_parcel", "name": {"str": "Oak's Parcel"},
         "description": "A small parcel addressed to Professor Oak from the Poké Mart.", "weight": "400 g", "volume": "500 ml",
         "price": "1 USD", "price_postapoc": "1 USD", "material": ["cardboard"], "symbol": "#", "color": "brown"},
        {"type": "ITEM", "id": "pkmn_diploma", "name": {"str": "Pokédex diploma"},
         "description": "A diploma from Professor Oak certifying that you completed the Kanto Pokédex.  A ridiculous thing to carry in the apocalypse, and you will carry it anyway.",
         "weight": "20 g", "volume": "50 ml", "price": "1 USD", "price_postapoc": "1 USD", "material": ["paper"], "symbol": "?", "color": "yellow"},
    ]
    return out


def oak_extra_responses():
    """Extra Oak responses that hand out the League / legendary mission lines."""
    def assign(mid, var, text, cond):
        return {"text": text,
                "condition": {"and": [{"math": ["value_or(%s, 0) == 0" % var]}] + cond},
                "effect": [{"math": ["%s = 1" % var]}, {"assign_mission": mid}],
                "topic": "TALK_PKMN_OAK_MISSION_GIVEN"}
    got = {"math": ["value_or(pkmn_got_starter, 0) == 1"]}
    return [
        assign("MISSION_PKMN_LEAGUE_1", "pkmn_league_line_started", "I want to take on the Pokémon League.", [got]),
        assign("MISSION_PKMN_OAK_MEWTWO", "pkmn_mewtwo_line_started", "Is there anything truly dangerous out there?",
               [got, {"math": ["value_or(pkmn_champion, 0) == 1"]}]),
    ]


# ===========================================================================
# Maps.  Every map is 24x24, entrance on the north edge (road connects north).
# ===========================================================================
BASE_TERRAIN = {
    " ": "t_grass", ".": "t_floor", ",": "t_concrete", "#": "t_wall", "w": "t_window", "+": "t_door_c",
    "\"": "t_door_glass_c", "c": "t_floor", "h": "t_floor", "t": "t_floor", "b": "t_floor", "r": "t_floor",
    "B": "t_floor", "d": "t_floor", "l": "t_floor", "p": "t_floor", "s": "t_floor", "S": "t_floor",
    "T": "t_tree", "~": "t_water_sh", "=": "t_water_dp", "_": "t_dirt", "f": "t_chainfence", "R": "t_rock",
    "%": "t_rock_floor", "<": "t_stairs_up", ">": "t_stairs_down", "C": "t_floor", "m": "t_floor",
    "x": "t_floor", "X": "t_floor", "a": "t_floor", "L": "t_floor", "N": "t_floor", "H": "t_floor",
    "G": "t_floor", "P": "t_floor", "j": "t_floor", "k": "t_floor", "Y": "t_shrub", "O": "t_floor",
    "M": "t_floor", "F": "t_floor", "1": "t_floor", "2": "t_floor", "3": "t_floor", "4": "t_floor", "A": "t_floor",
}
BASE_FURNITURE = {
    "c": "f_counter", "h": "f_chair", "t": "f_table", "b": "f_bed", "r": "f_rack", "B": "f_bookcase",
    "d": "f_desk", "l": "f_locker", "p": "f_indoor_plant", "s": "f_sofa", "S": "f_statue",
    "C": "f_console_broken", "m": "f_machinery_electronic", "O": "f_boulder_large",
}


def palette(pid, terrain=None, furniture=None, extra=None):
    ter = dict(BASE_TERRAIN)
    ter.update(terrain or {})
    fur = dict(BASE_FURNITURE)
    fur.update(furniture or {})
    pal = {"type": "palette", "id": pid, "terrain": ter, "furniture": fur}
    pal.update(extra or {})
    return pal


def check_rows(name, rows):
    assert len(rows) == 24, "%s has %d rows" % (name, len(rows))
    for i, r in enumerate(rows):
        assert len(r) == 24, "%s row %d is %d wide: %r" % (name, i, len(r), r)


MAP_CENTER = [
    "          ,,,,          ",
    " #########\"\"\"\"######### ",
    " #p.......,,,,.......p# ",
    " w....................w ",
    " #hh..............hh..# ",
    " #tt..............tt..# ",
    " #hh..............hh..# ",
    " w....................w ",
    " #cccccccccc.ccccccccc# ",
    " #..........N.........# ",
    " #..H.................# ",
    " #rr..bb..bb..bb..ll..# ",
    " #rr..............ll..# ",
    " ###################### ",
    "                        ",
    "   Y    Y    Y    Y     ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
]
MAP_MART = [
    "          ,,,,          ",
    " #########\"\"\"\"######### ",
    " #p.......,,,,.......p# ",
    " #....................# ",
    " #..rrrr..rrrr..rrrr..# ",
    " #....................# ",
    " #..rrrr..rrrr..rrrr..# ",
    " #....................# ",
    " #....................# ",
    " #cccccccccc..........# ",
    " #....M...c..........l# ",
    " #........c..........l# ",
    " ###################### ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
]
MAP_LAB = [
    "          ,,,,          ",
    " #########\"\"\"\"######### ",
    " #BBBB....,,,,....BBBB# ",
    " w....................w ",
    " #dh..dh........C.mmm.# ",
    " #..............C.....# ",
    " #tt..........O.......# ",
    " #tt....t.............# ",
    " w......t....N........w ",
    " #......t.............# ",
    " #rrr.............rrrr# ",
    " #rrr..ll..bb.....rrrr# ",
    " ###################### ",
    "                        ",
    "   TT              TT   ",
    "  TTTT     __     TTTT  ",
    "   TT     ____     TT   ",
    "          ____          ",
    "           __           ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
]
MAP_GYM = [
    "          ,,,,          ",
    " #########\"\"\"\"######### ",
    " #xx......,,,,......xx# ",
    " #x.......,,,,.......x# ",
    " #..X.....,,,,.....X..# ",
    " #........,,,,........# ",
    " #....xxxx....xxxx....# ",
    " #...x............x...# ",
    " #...x............x...# ",
    " #...x.....aa.....x...# ",
    " #...x.....aa.....x...# ",
    " #...x............x...# ",
    " #...x............x...# ",
    " #....xxxx....xxxx....# ",
    " #X..................X# ",
    " #..........L.........# ",
    " #X.......S..S.......X# ",
    " ###################### ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
]
MAP_PLATEAU = [
    "          ,,,,          ",
    " #########\"\"\"\"######### ",
    " #S.......,,,,.......S# ",
    " #........,,,,........# ",
    " #..xxxxxxxxxxxxxxxx..# ",
    " #..x..............x..# ",
    " #..x..............x..# ",
    " #..x......aa......x..# ",
    " #..x......aa......x..# ",
    " #..x..............x..# ",
    " #..x..............x..# ",
    " #..xxxxxxxxxxxxxxxx..# ",
    " #..........L.........# ",
    " #S..................S# ",
    " ###################### ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
]
MAP_HIDEOUT_TOP = [
    "          ,,,,          ",
    " #########\"\"\"\"######### ",
    " #mm.mm.mm.,,.mm.mm.mm# ",
    " #....................# ",
    " #h.h.h.h.h..h.h.h.h..# ",
    " #mm.mm.mm.mm.mm.mm.mm# ",
    " #....................# ",
    " #h.h.h.h.h..h.h.h.h..# ",
    " #....................# ",
    " #ccccc..........1....# ",
    " #.....r..........>...# ",
    " #.....r..............# ",
    " ###################### ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
]
MAP_HIDEOUT_BASEMENT = [
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "R######################R",
    "R#....2.......#..rr...#R",
    "R#............#..rr...#R",
    "R#..C.C.C.....+.......#R",
    "R#............#...4...#R",
    "R####+#########.......#R",
    "R#.......#....#####+###R",
    "R#.3.....#............#R",
    "R#.......+.....A......#R",
    "R#..rr...#............#R",
    "R#..rr...#..C.C.C.....#R",
    "R#.......#.........<..#R",
    "R######################R",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
]
MAP_CAVE = [
    "RRRRRRRRRR%%%%RRRRRRRRRR",
    "RRRRRRRRR%%%%%%RRRRRRRRR",
    "RRRRRR%%%%%%%%%%%RRRRRRR",
    "RRRR%%%%%%%RR%%%%%%RRRRR",
    "RRR%%%%%%RRRRRR%%%%%RRRR",
    "RR%%%%%%RRRRRRRR%%%%%RRR",
    "RR%%%%%RRR~~~RRRR%%%%RRR",
    "R%%%%%%RR~~=~~RRR%%%%%RR",
    "R%%%%%RRR~===~RR%%%%%%RR",
    "R%%%%%%RR~~=~~R%%%%%%%RR",
    "RR%%%%%%RR~~~R%%%%%%%RRR",
    "RR%%%%%%%RRRR%%%%%%%%RRR",
    "RRR%%%%%%%%%%%%%%%%%RRRR",
    "RRR%%%%%%%%%%%%%%%%%RRRR",
    "RRRR%%%%%%%%%%%%%%%RRRRR",
    "RRRR%%%%%%%%%%%%%%%RRRRR",
    "RRRRR%%%%%%%%%%%%%RRRRRR",
    "RRRRR%%%%%%%%%%%%%RRRRRR",
    "RRRRRR%%%%%%%%%%%RRRRRRR",
    "RRRRRRR%%%%%%%%%RRRRRRRR",
    "RRRRRRRR%%%%%%%RRRRRRRRR",
    "RRRRRRRRR%%%%%RRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRR",
]
MAP_POWER = [
    "          ,,,,          ",
    " #########++++######### ",
    " #mmm.mmm.,,,,.mmm.mmm# ",
    " #....................# ",
    " #.m.m.m.m....m.m.m.m.# ",
    " #....................# ",
    " #..CCC..........CCC..# ",
    " #....................# ",
    " #mm......%%%%......mm# ",
    " #mm......%%%%......mm# ",
    " #....................# ",
    " #m.m.m.m.m..m.m.m.m.m# ",
    " ###################### ",
    "    m  m  m  m  m  m    ",
    "                        ",
    "    m  m  m  m  m  m    ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
]
MAP_SAFARI = [
    "ffffffffff,,,,ffffffffff",
    "f   TT    ,cc,    TT   f",
    "f  TTTT   ,,,,   TTTT  f",
    "f   TT     __     TT   f",
    "f          __          f",
    "f   Y   ________   Y   f",
    "f      __      __      f",
    "f  Y  __  ~~~~  __  Y  f",
    "f    __  ~~==~~  __    f",
    "f    _  ~~====~~  _    f",
    "f    _  ~~====~~  _    f",
    "f    __  ~~==~~  __    f",
    "f  Y  __  ~~~~  __  Y  f",
    "f      __      __      f",
    "f   Y   ________   Y   f",
    "f          __          f",
    "f  TT      __      TT  f",
    "f TTTT  Y  __  Y  TTTT f",
    "f  TT      __      TT  f",
    "f    YY    __    YY    f",
    "f   TTTT   __   TTTT   f",
    "f    TT    __    TT    f",
    "f          __          f",
    "ffffffffffffffffffffffff",
]
MAP_TOWER = [
    "          ,,,,          ",
    " #########\"\"\"\"######### ",
    " #S.S.S.S.,,,,.S.S.S.S# ",
    " #....................# ",
    " #.S.S.S.S....S.S.S.S.# ",
    " #....................# ",
    " #S.S.S.S......S.S.S.S# ",
    " #....................# ",
    " #.S.S.S.S....S.S.S.S.# ",
    " #....................# ",
    " #S.S.S.S......S.S.S.S# ",
    " #..........F.........# ",
    " ###################### ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
]

GYM_THEMES = {
    # gym id: (terrain for '.', terrain for 'x', furniture for 'x', furniture for 'X', arena terrain, symbol, color, name)
    "pewter": ("t_rock_floor", "t_rock_floor", "f_boulder_large", "f_boulder_medium", "t_dirt", "G", "light_gray", "Pewter Gym"),
    "cerulean": ("t_floor", "t_water_pool", None, "f_indoor_plant", "t_floor", "G", "light_blue", "Cerulean Gym"),
    "vermilion": ("t_floor", "t_floor", "f_machinery_electronic", "f_console_broken", "t_floor", "G", "yellow", "Vermilion Gym"),
    "celadon": ("t_grass", "t_shrub", None, "f_indoor_plant", "t_grass", "G", "light_green", "Celadon Gym"),
    "fuchsia": ("t_floor", "t_floor", "f_statue", "f_indoor_plant", "t_floor", "G", "magenta", "Fuchsia Gym"),
    "saffron": ("t_carpet_purple", "t_carpet_purple", "f_statue", "f_console_broken", "t_carpet_purple", "G", "pink", "Saffron Gym"),
    "cinnabar": ("t_floor", "t_floor", "f_brazier", "f_brazier", "t_floor", "G", "light_red", "Cinnabar Gym"),
    "viridian": ("t_floor", "t_dirt", "f_boulder_medium", "f_statue", "t_dirt", "G", "green", "Viridian Gym"),
}
GYM_LEADER_FOR = {"pewter": "brock", "cerulean": "misty", "vermilion": "surge", "celadon": "erika",
                  "fuchsia": "koga", "saffron": "sabrina", "cinnabar": "blaine", "viridian": "giovanni"}


def omt(oid, name, sym, color, flags=None, spawns=None):
    o = {"type": "overmap_terrain", "id": oid, "name": name, "sym": sym, "color": color, "see_cost": "high",
         "mondensity": 0, "flags": flags or []}
    if spawns:
        o["spawns"] = spawns
    return o


def special(oid, locations, city_distance, occurrences, connect=True, extra_overmaps=None, city_sizes=None, flags=None,
            rotate=True):
    s = {"type": "overmap_special", "id": oid,
         "overmaps": [{"point": [0, 0, 0], "overmap": oid + ("_north" if rotate else "")}] + (extra_overmaps or []),
         "locations": locations, "city_distance": city_distance, "occurrences": occurrences,
         "flags": flags or ["MAN_MADE"]}
    if connect:
        s["connections"] = [{"point": [0, -1, 0], "connection": "local_road", "terrain": "road", "existing": True, "from": [0, 0, 0]}]
    if city_sizes:
        s["city_sizes"] = city_sizes
    return s


def mapgen(om, rows, palettes, **extra):
    check_rows(om, rows)
    obj = {"rows": rows, "palettes": palettes, "fill_ter": "t_grass"}
    obj.update(extra)
    return {"type": "mapgen", "om_terrain": om, "object": obj}


def npc_spawn(cls, uid=None):
    d = {"class": cls}
    if uid:
        d["unique_id"] = uid
    return d


def world_content():
    out = []
    # Palettes ---------------------------------------------------------------
    out.append(palette("pkmn_palette_building", extra={
        "items": {"r": {"item": "pkmn_loot_common", "chance": 25}, "l": {"item": "pkmn_loot_common", "chance": 25},
                  "B": {"item": "pkmn_loot_common", "chance": 10}, "d": {"item": "pkmn_loot_common", "chance": 20}}}))
    out.append(palette("pkmn_palette_cave", terrain={" ": "t_rock_floor"}, extra={}))
    # Overmap terrain + specials + mapgen --------------------------------------
    simple = [
        ("pkmn_center", "Pokémon Center", "+", "light_red", MAP_CENTER, ["land"], [0, 3], [3, 8],
         {"npcs": {"N": npc_spawn("pkmn_npc_nurse_joy"),
                   "H": None},
          "place_monster": [{"monster": "pkmn_chansey", "x": 4, "y": 10, "friendly": True, "chance": 60, "name": "Nurse Joy's Chansey"}],
          "place_npcs": [{"class": "pkmn_npc_jenny", "x": 18, "y": 4, "unique_id": "pkmn_jenny"},
                         {"class": "pkmn_npc_rocket_grunt_1", "x": [3, 20], "y": [15, 21]}]}),
        ("pkmn_mart", "Poké Mart", "$", "light_blue", MAP_MART, ["land"], [0, 3], [3, 8],
         {"npcs": {"M": npc_spawn("pkmn_npc_mart_clerk")}}),
        ("pkmn_oak_lab", "Professor Oak's Lab", "L", "white", MAP_LAB, ["land"], [1, 6], [1, 1],
         {"npcs": {"N": npc_spawn("pkmn_npc_oak", "pkmn_oak")}}),
        ("pkmn_indigo_plateau", "Indigo Plateau", "I", "yellow", MAP_PLATEAU, ["land"], [10, 40], [1, 1],
         {"npcs": {"L": npc_spawn("pkmn_npc_rival", "pkmn_rival")}}),
        ("pkmn_pokemon_tower", "Pokémon Tower", "T", "magenta", MAP_TOWER, ["land"], [0, 6], [0, 1],
         {"place_monster": [{"group": "PKMN_GROUP_TOWER", "x": [3, 20], "y": [3, 11], "repeat": [3, 6]}],
          "place_loot": [{"group": "pkmn_loot_rare", "x": 11, "y": 11, "chance": 100}]}),
        ("pkmn_power_plant", "abandoned power plant", "P", "yellow", MAP_POWER, ["land"], [6, -1], [1, 1],
         {"place_monster": [{"monster": "pkmn_zapdos", "x": 11, "y": 9},
                            {"group": "PKMN_GROUP_POWER", "x": [3, 20], "y": [3, 11], "repeat": [4, 8]}],
          "place_loot": [{"item": "pkmn_stone_thunder", "x": 12, "y": 9, "chance": 100}]}),
        ("pkmn_safari_zone", "Safari Zone", "S", "green", MAP_SAFARI, ["land"], [3, 30], [1, 1],
         {"place_npcs": [{"class": "pkmn_npc_safari_warden", "x": 12, "y": 2, "unique_id": "pkmn_warden"}],
          "place_monster": [{"group": "PKMN_GROUP_SAFARI", "x": [2, 21], "y": [4, 21], "repeat": [6, 10]}]}),
        ("pkmn_rocket_hideout", "Rocket Game Corner", "R", "red", MAP_HIDEOUT_TOP, ["land"], [0, 4], [1, 1],
         {"terrain": {"1": "t_floor"},
          "place_npcs": [{"class": "pkmn_npc_rocket_grunt_2", "x": 17, "y": 9}]}),
    ]
    for oid, name, sym, color, rows, locs, cdist, occ, extra in simple:
        out.append(omt(oid, name, sym, color))
        overmaps = None
        if oid == "pkmn_rocket_hideout":
            overmaps = [{"point": [0, 0, -1], "overmap": "pkmn_rocket_hideout_b1_north"}]
        out.append(special(oid, locs, cdist, occ, extra_overmaps=overmaps, city_sizes=[1, -1] if cdist[1] in (3, 4, 6) else None))
        ex = dict(extra)
        if "npcs" in ex:
            ex["npcs"] = {k: v for k, v in ex["npcs"].items() if v}
        out.append(mapgen(oid, rows, ["pkmn_palette_building"], **ex))
    # Rocket hideout basement.
    out.append(omt("pkmn_rocket_hideout_b1", "Rocket Hideout", "R", "red"))
    out.append(mapgen("pkmn_rocket_hideout_b1", MAP_HIDEOUT_BASEMENT, ["pkmn_palette_building"],
                      fill_ter="t_rock_floor",
                      terrain={"2": "t_floor", "3": "t_floor", "4": "t_floor", "A": "t_floor"},
                      place_npcs=[{"class": "pkmn_npc_rocket_grunt_3", "x": 6, "y": 2},
                                  {"class": "pkmn_npc_rocket_grunt_4", "x": 3, "y": 8},
                                  {"class": "pkmn_npc_rocket_grunt_5", "x": 18, "y": 5},
                                  {"class": "pkmn_npc_rocket_admin", "x": 15, "y": 9, "unique_id": "pkmn_rocket_admin"}],
                      place_loot=[{"group": "pkmn_loot_rare", "x": 18, "y": 2, "chance": 100},
                                  {"group": "pkmn_loot_rare", "x": 4, "y": 10, "chance": 80},
                                  {"item": "pkmn_ball_master", "x": 19, "y": 3, "chance": 25}],
                      place_monster=[{"monster": "pkmn_porygon", "x": 12, "y": 11, "chance": 50}]))
    # Caves: Mt. Moon, Seafoam, Mt. Ember (Moltres), Cerulean Cave (Mewtwo).
    caves = [
        ("pkmn_mt_moon", "Mt. Moon cave", "M", "light_gray", "PKMN_GROUP_MT_MOON", None,
         [{"item": "pkmn_fossil_helix", "x": 6, "y": 14, "chance": 60}, {"item": "pkmn_fossil_dome", "x": 16, "y": 14, "chance": 60},
          {"item": "pkmn_stone_moon", "x": 11, "y": 17, "chance": 100}, {"item": "pkmn_old_amber", "x": 11, "y": 19, "chance": 30}],
         [{"class": "pkmn_npc_rocket_grunt_1", "x": 11, "y": 13}], [1, 2]),
        ("pkmn_seafoam", "Seafoam ice cave", "A", "light_cyan", "PKMN_GROUP_SEAFOAM", "pkmn_articuno",
         [{"group": "pkmn_loot_rare", "x": 11, "y": 15, "chance": 100}], [], [1, 1]),
        ("pkmn_mt_ember", "Mt. Ember volcanic cave", "E", "light_red", "PKMN_GROUP_EMBER", "pkmn_moltres",
         [{"item": "pkmn_stone_fire", "x": 11, "y": 15, "chance": 100}], [], [1, 1]),
        ("pkmn_cerulean_cave", "sealed cave", "?", "magenta", "PKMN_GROUP_CERULEAN_CAVE", "pkmn_mewtwo",
         [{"group": "pkmn_loot_rare", "x": 11, "y": 15, "chance": 100}, {"item": "pkmn_ball_ultra", "x": 12, "y": 16, "chance": 100}], [], [1, 1]),
    ]
    for oid, name, sym, color, group, boss, loot, npcs, occ in caves:
        out.append(omt(oid, name, sym, color, flags=["NO_ROTATE"]))
        s = special(oid, ["wilderness"], [8, -1], occ, connect=False, flags=["WILDERNESS"], rotate=False)
        out.append(s)
        monsters = [{"group": group, "x": [3, 20], "y": [2, 20], "repeat": [5, 9]}]
        if boss:
            monsters.append({"monster": boss, "x": 11, "y": 12})
        ter = {}
        if oid == "pkmn_seafoam":
            ter = {"~": "t_water_sh", "=": "t_water_dp"}
        if oid == "pkmn_mt_ember":
            ter = {"~": "t_rock_floor", "=": "t_lava"}
        out.append(mapgen(oid, MAP_CAVE, ["pkmn_palette_cave"], fill_ter="t_rock_floor", place_monster=monsters,
                          place_loot=loot, place_npcs=npcs, terrain=ter))
    # Gyms.
    for gid, (floor, xter, xfur, Xfur, arena, sym, color, name) in GYM_THEMES.items():
        oid = "pkmn_gym_" + gid
        out.append(omt(oid, name, sym, color))
        out.append(special(oid, ["land"], [0, 4], [1, 1], city_sizes=[1, -1]))
        pal_id = "pkmn_palette_gym_" + gid
        fur = {}
        if xfur:
            fur["x"] = xfur
        if Xfur:
            fur["X"] = Xfur
        out.append(palette(pal_id, terrain={".": floor, "x": xter, "X": floor, "a": arena, "L": floor, "S": floor},
                           furniture=fur))
        leader = GYM_LEADER_FOR[gid]
        out.append(mapgen(oid, MAP_GYM, [pal_id], npcs={"L": npc_spawn("pkmn_npc_" + leader, "pkmn_" + leader)}))
    # Extra spawn groups for special locations.
    groups = {
        "PKMN_GROUP_TOWER": [("gastly", 100), ("haunter", 30), ("cubone", 40), ("marowak", 8)],
        "PKMN_GROUP_MT_MOON": [("zubat", 100), ("geodude", 80), ("paras", 50), ("clefairy", 15), ("sandshrew", 30), ("onix", 8)],
        "PKMN_GROUP_SEAFOAM": [("seel", 60), ("dewgong", 15), ("shellder", 60), ("slowpoke", 40), ("golbat", 30), ("horsea", 30), ("jynx", 6)],
        "PKMN_GROUP_EMBER": [("ponyta", 60), ("rapidash", 15), ("magmar", 12), ("geodude", 60), ("graveler", 20), ("machop", 30), ("vulpix", 30)],
        "PKMN_GROUP_CERULEAN_CAVE": [("golbat", 50), ("kadabra", 30), ("parasect", 30), ("rhydon", 20), ("ditto", 40),
                                     ("electrode", 20), ("chansey", 8), ("magneton", 20), ("wigglytuff", 15)],
    }
    for gid, entries in groups.items():
        out.append({"type": "monstergroup", "id": gid, "monsters": [
            {"monster": "pkmn_" + s, "weight": w} for s, w in entries]})
    # Rarely, a wandering Mew or a Hitmon in the wild.
    out.append({"type": "monstergroup", "id": "PKMN_GROUP_FOREST", "monsters": [{"monster": "pkmn_mew", "weight": 1}]})
    out.append({"type": "monstergroup", "id": "PKMN_GROUP_MOUNTAIN", "monsters": [{"monster": "pkmn_hitmonlee", "weight": 2}, {"monster": "pkmn_hitmonchan", "weight": 2}]})
    out.append({"type": "monstergroup", "id": "PKMN_GROUP_WATER", "monsters": [{"monster": "pkmn_dragonair", "weight": 1}]})
    out.append({"type": "monstergroup", "id": "PKMN_GROUP_URBAN", "monsters": [
        {"monster": "pkmn_eevee", "weight": 8}, {"monster": "pkmn_jynx", "weight": 3}]})
    # Urban Pokémon live in a map extra scattered through towns.
    return out


def scenario_content():
    return [
        {"type": "start_location", "id": "sloc_pkmn_oak_lab", "name": "Professor Oak's Lab",
         "terrain": ["pkmn_oak_lab"]},
        {"type": "profession", "id": "pkmn_trainer", "name": "Pokémon Trainer",
         "description": "You always dreamed of becoming a Pokémon trainer.  The world ending isn't going to stop you now.  Professor Oak is expecting you.",
         "points": 0,
         "items": {"both": {"items": ["tshirt", "jeans", "socks", "sneakers", "hat_ball", "backpack", "water_clean", "granola"],
                            "entries": [{"item": "pkmn_ball_poke", "count": 3}, {"item": "pkmn_potion", "count": 1}]},
                   "male": ["boxer_shorts"], "female": ["sports_bra", "boy_shorts"]},
         "skills": [{"level": 1, "name": "survival"}]},
        {"type": "scenario", "id": "pkmn_new_trainer", "name": "Pokémon Journey",
         "description": "Your journey begins at Professor Oak's lab.  The Professor has a Pokémon for you, and the whole of a ruined world to explore.",
         "start_name": "Professor Oak's Lab", "allowed_locs": ["sloc_pkmn_oak_lab"],
         "professions": ["pkmn_trainer", "unemployed"], "points": 0,
         "flags": ["CITY_START"]},
    ]


def main():
    write("npcs/trainers_gen.json", gym_leader_content() + rocket_content() + rival_content())
    oak = oak_content()
    for o in oak:
        if o.get("id") == "TALK_PKMN_OAK":
            o["responses"] = o["responses"][:-1] + oak_extra_responses() + o["responses"][-1:]
    oak.append({"type": "talk_topic", "id": "TALK_PKMN_OAK_MISSION_GIVEN",
                "dynamic_line": "Then I'm counting on you!  I've marked your destination on your map.",
                "responses": [{"text": "I won't let you down.", "topic": "TALK_PKMN_OAK"}]})
    write("npcs/npcs_gen.json", oak + joy_content() + mart_content() + jenny_content() + warden_content())
    write("npcs/factions_classes_gen.json", factions_and_classes())
    write("missions/missions_gen.json", missions_content())
    write("mapgen/locations_gen.json", world_content())
    write("core/scenario_gen.json", scenario_content())


if __name__ == "__main__":
    main()
