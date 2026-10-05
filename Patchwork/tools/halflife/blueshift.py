"""hl_blueshift: Half-Life: Blue Shift, Barney Calhoun's long day.

Chapter by chapter (ba_tram1 ... ba_outro, plus the ba_hazard training course).
Map codes follow the original BSP names; long maps are condensed to their
memorable spaces and small details are approximate.
"""

from common import ModBuilder

B = ModBuilder("hl_blueshift", "bs/")
HZ = "bsh/"   # the security training course is its own area

LOCKED = {"door": "bm_locked_door", "name": "locked door", "aliases": ["door", "locked door"]}
HATCH = {"door": "bm_jammed_hatch", "name": "jammed hatch", "aliases": ["hatch"]}


def locked(tags, length=(2, 4), chance=0.85, door=LOCKED):
    d = dict(door)
    d.update({"tags": list(tags), "length": list(length), "chance": chance})
    return d


def outdoors(tags, length=(2, 4), chance=0.9, name=None):
    d = {"tags": list(tags), "length": list(length), "chance": chance}
    if name:
        d["name"] = name
    return d


POST = ["post_cascade_bs"]
SURF = ["surface", "outdoor", "desert"]

# ===========================================================================
# Living Quarters Outbound  (ba_tram1 ... ba_tram3)
# ===========================================================================
B.set_chapter("Living Quarters Outbound")
B.room("ba_tram1", "Tram: Living Quarters Outbound", "Another morning on the Black Mesa Transit System. You are Barney Calhoun, security, riding in from the dormitories with your coffee going cold. The announcer recites the safety rules you could recite yourself. Out of the window, a crew argues with a broken-down elevator.",
       map="ba_tram1", tags=["blackmesa", "transit", "indoor", "tram"], feats=["bs_announcer"], aliases=["tram"])
B.room("ba_tram2", "Tram Ride: Sector Sweep", "The tram swings past sectors you know by heart. On a parallel line another tram goes by with a bespectacled man in it, reading a magazine, late for something. Further on, a scientist on a gantry seems to be pointing at a man in a blue suit. Then the tram jolts to a halt in a tunnel, and starts again.",
       map="ba_tram2", tags=["blackmesa", "transit", "indoor"], feats=["freeman_tram", "gman_glimpse_bs"])
B.room("ba_tram3", "Security Station Platform", "The tram pulls in at a platform beside the Sector C security station. A colleague leans out of the door: you're late, Calhoun, and they need you on the elevator in Sector G.",
       map="ba_tram3", tags=["blackmesa", "transit", "indoor"], feats=["platform_guard_bs"], aliases=["platform"])
B.chain(["ba_tram1", "ba_tram2", "ba_tram3"], "east", 3)

# ===========================================================================
# Insecurity  (ba_security1, ba_security2)
# ===========================================================================
B.set_chapter("Insecurity")
B.room("ba_security1_lobby", "Security Station", "The security station: a counter, a coffee machine on its last legs and a wall of mailboxes. Another guard is arguing with the retinal scanner. It's a perfectly normal morning.",
       map="ba_security1", tags=["blackmesa", "office", "indoor"], feats=["security_desk_bs", "vending_machine", "bm_memo"],
       expand=locked(["office", "blackmesa"], chance=0.6))
B.room("ba_security1_lockers", "Security Locker Room", "The guards' locker room, smelling of gun oil and somebody's gym bag. Your locker has CALHOUN stencilled on it.",
       map="ba_security1", tags=["blackmesa", "office", "indoor"], feats=["calhoun_locker", "health_charger"], aliases=["locker room"])
B.room("ba_security1_armory", "Security Armoury", "A caged armoury counter. The duty officer slides a 9mm pistol across to you and makes you sign for it, in triplicate.",
       map="ba_security1", tags=["blackmesa", "office", "indoor"], feats=["armory_officer", "glock", "ammo_box"], aliases=["armoury", "armory"])
B.room("ba_security2_monitors", "Security Monitoring Room", "A dark room of monitors showing the whole sector. On one screen, in the Anomalous Materials test chamber, a man in an orange HEV suit pushes a cart toward a beam.",
       map="ba_security2", tags=["blackmesa", "office", "indoor"], feats=["bs_monitors", "bm_terminal"], aliases=["monitors"])
B.room("ba_security2_elevator", "Sector G Service Elevator", "A service elevator full of scientists who keep telling you it's stuck. You fix the panel with a thump. The car starts down. Then the lights flicker green, the whole shaft shudders, and the cables let go.",
       map="ba_security2", tags=["blackmesa", "transit", "indoor", "story_skip"], aliases=["elevator"],
       enter=[{"if": {"not": {"flag": "bs_cascade"}}, "then": [{"macro": "bs_cascade"}]}])
B.link("ba_tram3", "ba_security1_lobby", "north")
B.link("ba_security1_lobby", "ba_security1_lockers", "west")
B.link("ba_security1_lobby", "ba_security1_armory", "east")
B.link("ba_security1_lobby", "ba_security2_monitors", "north")
B.link("ba_security2_monitors", "ba_security2_elevator", "east", name="service elevator", aliases=["elevator", "lift"])

# ===========================================================================
# Duty Calls  (ba_canal1 ... ba_canal3)
# ===========================================================================
B.set_chapter("Duty Calls")
B.room("ba_canal1_shaft", "Bottom of the Elevator Shaft", "You come to in the wreck of the elevator at the bottom of its shaft. The scientists didn't make it. The emergency lights are red, and something is scratching at the doors.",
       map="ba_canal1", tags=["blackmesa", "transit", "indoor"] + POST, feats=["dead_scientist", "headcrab", "battery"], aliases=["shaft", "wreck"])
B.room("ba_canal1_basement", "Flooded Basement", "A flooded basement of pipes and storage cages. The water is rising and the power is sparking on the walls.",
       map="ba_canal1", tags=["blackmesa", "maintenance", "indoor", "water"] + POST, feats=["zombie_guard", "supply_crate"], expand=locked(["maintenance"], chance=0.6, door=HATCH))
B.room("ba_canal2_canals", "Drainage Canals", "Wide concrete drainage canals, the water moving fast toward a sluice. Bullsquids nest in the overflow pipes. A guard on the far bank shouts that he's going for help, and doesn't come back.",
       map="ba_canal2", tags=["blackmesa", "maintenance", "indoor", "water"] + POST, feats=["bullsquid", "leech", "medkit"])
B.room("ba_canal3_pumps", "Pump House", "A pump house where the canals meet. A dead scientist clutches a clipboard listing the staff of a team led by a Dr. Rosenberg. The last line says: taken by the soldiers to the freight yard.",
       map="ba_canal3", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["rosenberg_clipboard", "houndeye", "health_charger"], expand=locked(["maintenance", "storage"], chance=0.6))
B.link("ba_security2_elevator", "ba_canal1_shaft", "down", name="the fall", aliases=["fall", "shaft"], oneway=True)
B.link("ba_canal1_shaft", "ba_canal1_basement", "east")
B.link("ba_canal1_shaft", "ba_security2_monitors", "up", name="maintenance ladder", aliases=["ladder"], back_name="maintenance hatch")
B.link("ba_canal1_basement", "ba_canal2_canals", "east")
B.link("ba_canal2_canals", "ba_canal3_pumps", "east")

# ===========================================================================
# Captive Freight  (ba_yard1 ... ba_yard6)
# ===========================================================================
B.set_chapter("Captive Freight")
B.room("ba_yard1_gate", "Freight Yard Gate", "The gate of the underground freight yard, with a guard hut and a barrier arm. Soldiers have strung razor wire across it, and one of them is on the radio about scientists in custody.",
       map="ba_yard1", tags=["blackmesa", "transit", "military", "indoor"] + POST, feats=["hecu_marine", "ammo_box"])
B.room("ba_yard2_trains", "Freight Rail Yard", "Rows of boxcars on parallel tracks under a high rock ceiling. A crane gantry spans the yard. Marines move between the cars, and so do things that aren't Marines.",
       map="ba_yard2", tags=["blackmesa", "transit", "storage", "indoor"] + POST, feats=["hecu_marine", "houndeye", "supply_crate", "mp5"],
       expand=locked(["storage", "transit"], chance=0.8))
B.room("ba_yard3_crane", "Crane Gantry", "The control cab of the gantry crane, high over the yard. From here you can move a boxcar and open a path through the yard.",
       map="ba_yard3", tags=["blackmesa", "transit", "indoor"] + POST, feats=["yard_crane", "battery"])
B.room("ba_yard4_holding", "Holding Area", "A row of offices the Marines turned into holding cells. In one of them sits a grey-haired scientist, hands bound, glaring at the guard. That will be Dr. Rosenberg.",
       map="ba_yard4", tags=["blackmesa", "military", "office", "indoor"] + POST, feats=["rosenberg", "hecu_marine", "health_charger"], aliases=["holding area", "cells"])
B.room("ba_yard5_warehouse", "Freight Warehouse", "A warehouse of crates stacked to the roof. Rosenberg knows a way through to his old team's lab, he says, if you can keep the two of you alive that far.",
       map="ba_yard5", tags=["blackmesa", "storage", "indoor"] + POST, feats=["zombie", "supply_crate", "shotgun"], expand=locked(["storage"], chance=0.7))
B.room("ba_yard6_service", "Service Corridor", "A long service corridor that leads, according to the signs, to the Sector F teleportation labs.",
       map="ba_yard6", tags=["blackmesa", "lab", "indoor"] + POST, feats=["alien_grunt", "medkit"])
B.link("ba_canal3_pumps", "ba_yard1_gate", "north")
B.link("ba_yard1_gate", "ba_yard2_trains", "north")
B.link("ba_yard2_trains", "ba_yard3_crane", "up", name="gantry ladder", aliases=["ladder", "gantry"])
B.link("ba_yard2_trains", "ba_yard4_holding", "east")
B.link("ba_yard4_holding", "ba_yard5_warehouse", "north")
B.link("ba_yard5_warehouse", "ba_yard6_service", "east")

# ===========================================================================
# Focal Point  (ba_teleport1, ba_xen1 ... ba_xen6)
# ===========================================================================
B.set_chapter("Focal Point")
B.room("ba_teleport1_lab", "Teleportation Lab", "Rosenberg's old teleport lab. Two of his team are still alive, barricaded in with the equipment. The prototype teleporter can get you all out, Rosenberg says, but first somebody has to go to Xen and set up a relay, so the jump has something to lock on to. He looks at you. You look at the security badge on your chest.",
       map="ba_teleport1", tags=["blackmesa", "lab", "indoor", "bs_lab"] + POST, feats=["rosenberg_team", "bs_test_pad", "suit_charger", "health_charger"], aliases=["teleport lab"])
B.room("ba_xen1_arrival", "Xen: Relay Island", "You land on a floating island under a violet sky. A cluster of light-stalks shrinks from you, and in the middle of the island the Xen relay crystal waits for its beacon.",
       map="ba_xen1", tags=["xen", "alien", "outdoor"], feats=["xen_relay", "xen_light", "houndeye"], expand=outdoors(["xen"], name="drifting rock"))
B.room("ba_xen2_pools", "Xen: Pools and Jump Pads", "Pools of glowing water and organic jump pads that launch you across the void. Something big moves on a far island.",
       map="ba_xen3", tags=["xen", "alien", "outdoor"], feats=["healing_pool", "alien_grunt", "xen_glyph"])
B.room("ba_xen3_focal", "Xen: Focal Point", "A high spire of rock where the relay's signal gathers. You can see the whole archipelago from here, and the Nihilanth's mountain far away. A portal back to Black Mesa flickers at the edge.",
       map="ba_xen6", tags=["xen", "alien", "outdoor"], feats=["controller", "battery"], aliases=["focal point"])
B.link("ba_yard6_service", "ba_teleport1_lab", "east")
B.link("ba_teleport1_lab", "ba_xen1_arrival", "in", name="the test teleporter", aliases=["teleporter", "pad", "test pad"], back_name="portal home")
B.link("ba_xen1_arrival", "ba_xen2_pools", "east")
B.link("ba_xen2_pools", "ba_xen3_focal", "up", name="jump pad", aliases=["pad", "jump pad"])

# ===========================================================================
# Power Struggle  (ba_power1, ba_power2)
# ===========================================================================
B.set_chapter("Power Struggle")
B.room("ba_power1_hall", "Generator Hall", "You arrive back in Black Mesa in the wrong place: a generator hall a long way from the lab. The teleporter needs more power than the grid can give. Rosenberg, over the radio, says there's a storage depot with the batteries it needs.",
       map="ba_power1", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["bs_generator", "hecu_marine", "suit_charger"], expand=locked(["maintenance"], chance=0.7, door=HATCH))
B.room("ba_power1_yard", "Battery Storage Depot", "A depot of heavy batteries on racks, half of them dead, guarded by a sentry gun the Marines left behind.",
       map="ba_power1", tags=["blackmesa", "storage", "indoor"] + POST, feats=["sentry_gun", "teleport_battery", "supply_crate"])
B.room("ba_power2_cliffs", "Cliffside Ducts", "Ducts and pipes that run along a cliff face outside the facility. Below, a canyon. Above, an Apache.",
       map="ba_power2", tags=["blackmesa"] + SURF + POST, feats=["apache", "ammo_box"], expand=outdoors(["surface", "military"]))
B.link("ba_xen3_focal", "ba_power1_hall", "in", name="flickering portal", aliases=["portal"])
B.link("ba_power1_hall", "ba_power1_yard", "north")
B.link("ba_power1_hall", "ba_power2_cliffs", "east")

# ===========================================================================
# A Leap of Faith  (ba_teleport2, ba_outro)
# ===========================================================================
B.set_chapter("A Leap of Faith")
B.room("ba_teleport2_chamber", "Prototype Teleporter Chamber", "The prototype teleporter fills the chamber: a ring of emitters around a platform, cables as thick as your arm running to an empty battery cradle. Rosenberg's team are at the controls. The Marines are at the door.",
       map="ba_teleport2", tags=["blackmesa", "lab", "indoor", "bs_lab"] + POST, feats=["prototype_teleporter", "health_charger", "hecu_marine"], aliases=["teleporter chamber", "chamber"])
B.room("ba_outro", "Desert Road", "The teleporter drops you, Rosenberg and his team in a garage near the surface. You find a jeep, and with the sun coming up, you drive out of Black Mesa down a long desert road. Behind you, the facility burns.",
       map="ba_outro", tags=["surface", "outdoor", "desert", "story_skip"])
B.link("ba_power2_cliffs", "ba_teleport2_chamber", "in", name="maintenance door", aliases=["door"])
B.link("ba_teleport2_chamber", "ba_teleport1_lab", "west")

# ===========================================================================
# Hazard course  (ba_hazard1 ... ba_hazard6)
# ===========================================================================
HZT = ["blackmesa", "training", "indoor"]
B.set_chapter("Security Training Course")
B.room(HZ + "ba_hazard1", "Security Training: Briefing", "A training hall for Black Mesa security, with a holographic instructor who looks remarkably like a guard you went to the academy with.",
       map="ba_hazard1", tags=HZT, feats=["holo_guard"])
B.room(HZ + "ba_hazard2", "Security Training: Movement", "Crates, ladders and a duct, with signs explaining each one.", map="ba_hazard2", tags=HZT, feats=["supply_crate"])
B.room(HZ + "ba_hazard3", "Security Training: Swimming", "A pool with a submerged corridor to swim through.", map="ba_hazard3", tags=HZT + ["water"])
B.room(HZ + "ba_hazard4", "Security Training: First Aid", "A health charger, a first aid kit and a hologram explaining which way round they go.", map="ba_hazard4", tags=HZT, feats=["health_charger", "medkit"])
B.room(HZ + "ba_hazard6", "Security Training: Firing Range", "A pistol range, the target at the end already full of holes.", map="ba_hazard6", tags=HZT, feats=["glock", "training_target_bs"])
B.chain([HZ + "ba_hazard1", HZ + "ba_hazard2", HZ + "ba_hazard3", HZ + "ba_hazard4", HZ + "ba_hazard6"], "north")

# ===========================================================================
# Features
# ===========================================================================
F = B.section("features")
F.update({
    "bs_announcer": {"extends": ["scenery"], "name": "tram announcer", "aliases": ["announcer", "speaker", "voice"], "appearance": False,
        "description": "A recorded voice from a speaker grille.",
        "actions": {"listen": ["#bs_announcement#"], "talk": ["It's a recording. It doesn't care that you're late."]}},
    "freeman_tram": {"extends": ["scenery"], "name": "other tram", "aliases": ["tram", "other tram", "man", "freeman", "scientist"], "appearance": False,
        "description": "A bespectacled, bearded scientist in the other tram, reading a magazine, oblivious. You'll learn his name later."},
    "gman_glimpse_bs": {"extends": ["scenery"], "name": "man in a blue suit", "aliases": ["man in a blue suit", "suit", "g-man", "gman"], "appearance": False,
        "description": "A thin man in a blue suit on a gantry. When the tram comes round again, he's gone."},
    "platform_guard_bs": {"extends": ["security_guard"], "appearance": "{self.Name} leans out of the security station door.",
        "actions": {"talk": [{"do": ["\"Calhoun! There you are. Some egghead's stuck in the Sector G elevator. Grab your gear and go fix it.\""]}]}},
    "security_desk_bs": {"extends": ["scenery", "surface"], "name": "security counter", "aliases": ["counter", "desk"], "appearance": False,
        "description": "A counter covered with sign-in sheets and a coffee mug that says WORLD'S OKAYEST GUARD."},
    "calhoun_locker": {"extends": ["scenery", "container", "openable"], "name": "locker marked CALHOUN", "aliases": ["locker", "calhoun locker", "my locker"],
        "appearance": "Your locker, stencilled CALHOUN, stands in the row.",
        "description": "Your locker. Inside, if you remember right, your vest and helmet.",
        "features": ["security_vest", "security_helmet"]},
    "armory_officer": {"extends": ["security_guard"], "appearance": "{self.Name} sits behind the armoury cage, clipboard in hand.",
        "actions": {"talk": [{"do": ["\"Sign here. And here. Don't shoot anybody important.\""]}]}},
    "bs_monitors": {"extends": ["scenery"], "name": "monitors", "aliases": ["monitors", "screens", "screen", "monitor"],
        "appearance": "A wall of security monitors flickers with views of the sector.",
        "description": [{"if": {"flag": "bs_cascade"}, "text": "The monitors show static, fire, and things moving that shouldn't be."},
                        {"text": "One monitor shows the Anomalous Materials test chamber, where a man in an orange suit pushes a sample cart toward the beam."}]},
    "rosenberg_clipboard": {"extends": ["portable", "readable"], "name": "clipboard", "aliases": ["clipboard", "list"],
        "props": {"text": "TEAM: DR. ROSENBERG (lead), DR. HARRIS, DR. WALTER, DR. SIMMONS. Teleport research, Sector F. Note added in pen: R. taken by HECU to the freight yard holding area."}},
    "yard_crane": {"extends": ["scenery"], "name": "crane controls", "aliases": ["crane", "controls", "gantry", "levers"],
        "appearance": "The crane's controls are a pair of levers and a big red button.", "description": "You've seen it done. How hard can it be?",
        "actions": {"use": ["You swing the crane over and drop a boxcar out of the way. The yard shakes. Several Marines below are suddenly very interested in where you are."]}},
    "rosenberg": {"extends": ["scientist"], "name": "Dr. Rosenberg", "proper": True, "aliases": ["rosenberg", "dr rosenberg", "scientist", "doctor"],
        "important": True, "tags": ["scientist", "bm_staff", "rosenberg"],
        "appearance": "Dr. Rosenberg, grey-haired and sharp-eyed, is here.",
        "description": "A senior scientist with a soft voice and absolutely no patience for soldiers.",
        "profile": {"personality": ["wise", "stubborn"], "motives": ["knowledge", "protect", "survive"],
            "motive_text": "get his team out alive, by the one road nobody else would dare",
            "goals": ["reach the teleportation lab", "save his team", "escape Black Mesa"],
            "backstory": "\"We warned them. The teleport work was years ahead of anything else, and we told them the crystal was too pure. And now? Now we'll have to use our own machine to get out.\"",
            "roles": ["giver", "informant", "ally", "victim", "authority"], "knows": ["science", "xen", "teleport", "blackmesa"],
            "wants": ["power", "access", "medicine"],
            "epilogue": "Dr. Rosenberg rides out of Black Mesa in the back of a jeep, already sketching corrections to the teleporter on a napkin."},
        "actions": {"talk": [{"do": ["\"You're not with those soldiers? Good. Then you'll help me get to my team, and I'll get us all out of here.\""]}]}},
    "rosenberg_team": {"extends": ["scientist"], "name": "Rosenberg's team", "proper": True, "aliases": ["team", "scientists", "harris", "walter", "simmons"],
        "appearance": "Rosenberg's surviving team huddle around their consoles.",
        "actions": {"talk": [{"do": ["\"The relay, Mr. Calhoun. Step on the test pad, set the beacon on the other side, and come back. It's perfectly safe. Statistically.\""]}]}},
    "bs_test_pad": {"extends": ["scenery"], "name": "test teleporter pad", "aliases": ["test pad", "pad"], "appearance": "A small test teleporter pad hums in the corner.",
        "description": "The test pad. It sends one person to Xen, and, the scientists promise, back."},
    "xen_relay": {"extends": ["scenery"], "name": "relay crystal", "aliases": ["relay", "crystal", "beacon", "relay crystal"],
        "appearance": [{"if": {"flag": "bs_relay"}, "text": "The relay crystal pulses with a steady beacon light."},
                       {"text": "A tall Xen crystal stands in the centre of the island, dark."}],
        "description": "The relay the teleporter needs to lock on to.",
        "actions": {"use": [{"if": {"flag": "bs_relay"}, "do": ["It's already pulsing."]},
                            {"do": [{"flag": "bs_relay"}, {"say": "You fix the beacon to the relay crystal. It hums, catches, and begins to pulse in time with something far away in Black Mesa.", "style": "story"}]}]}},
    "bs_generator": {"extends": ["scenery"], "name": "generator", "aliases": ["generator", "switch", "breaker"],
        "appearance": "A generator stands idle in the middle of the hall.", "description": "Not enough for the teleporter alone. It needs batteries too.",
        "actions": {"use": ["You get the generator turning over. The lights come up; the teleporter will still need its battery."]}},
    "teleport_battery": {"extends": ["portable"], "name": "teleporter battery", "aliases": ["battery", "teleporter battery", "power cell", "cell"],
        "important": True, "tags": ["bs_tele_battery"], "affords": ["power"],
        "description": "A huge rechargeable cell on a carry-frame, its gauge full. The one thing the prototype teleporter is missing."},
    "prototype_teleporter": {"extends": ["scenery"], "name": "prototype teleporter", "aliases": ["teleporter", "prototype", "cradle", "battery cradle", "emitters"],
        "important": True, "tags": ["bs_teleporter", "heart"],
        "appearance": "The prototype teleporter's ring of emitters surrounds the platform; its battery cradle is empty.",
        "description": "Rosenberg's machine. Fit the battery, set the relay, and it can throw all of you out of Black Mesa. Probably in one piece."},
    "holo_guard": {"extends": ["scenery"], "name": "holographic instructor", "aliases": ["hologram", "instructor", "guard"],
        "appearance": "A flickering hologram of a security guard waits to begin.", "description": "He's patient. More patient than you.",
        "actions": {"talk": ["\"Welcome to Black Mesa security training. Let's begin with the basics.\""]}},
    "training_target_bs": {"extends": ["scenery"], "name": "target", "aliases": ["target"], "appearance": "A paper target hangs at the end of the range.",
        "description": "Mostly holes.", "actions": {"attack": ["You put five rounds through it. The hologram nods approvingly."]}},
})

# Mark the shared core's equipment as important in this campaign.
for fid in ("security_vest", "security_helmet"):
    F[fid] = {"_patch": True, "important": True}

MACROS = {
    "bs_cascade": {"do": [
        {"if": {"flag": "bs_cascade"}, "then": [{"stop": True}]},
        {"flag": "bs_cascade"},
        {"say": "The elevator lurches. Green light flickers through the shaft, and the world shudders, once, twice: somewhere above, an experiment has gone horribly wrong. The cables snap. The car drops.", "style": "story"},
        {"macro": "hl_take_damage", "with": {"amount": 15}},
        {"teleport": "room:bs/ba_canal1_shaft"}]},
}

RULES = {
    "bs_cascade_catchup": {"on": "enter", "if": {"all": [{"in_room": "tag:post_cascade_bs"}, {"not": {"flag": "bs_cascade"}}]},
        "do": [{"flag": "bs_cascade"}]},
}

B.section("lore").update({
    "bs_calhoun": {"title": "Barney Calhoun", "about": ["area:bs_blackmesa"], "tags": ["security", "blackmesa"],
        "text": "Barney Calhoun, Black Mesa security, officer grade. Responsible for checking badges, fixing elevators and getting scientists out of trouble. Today, the job description is about to expand."},
    "bs_teleport": {"title": "Teleport research", "about": ["area:bs_blackmesa"], "tags": ["science", "teleport", "xen"],
        "text": "Before the Lambda team took over, Dr. Rosenberg's group built Black Mesa's first teleporter. It needed a relay on the far side to lock on to, and it needed more power than anyone wanted to give it. It was mothballed. It was never dismantled."},
    "bs_late": {"title": "Late again", "about": ["area:bs_blackmesa"], "tags": ["security", "rumour"], "chance": 0.7,
        "text": "Security logs show Officer Calhoun arriving late on the morning of the incident, on the same tram line as a research associate who was also late. Neither knew the other's name."},
})

EVENTS = {
    "bs_leap_of_faith": {
        "title": ["Blue Shift", "A Leap of Faith"],
        "tags": ["blackmesa", "blue-shift", "escape"], "start_areas": ["bs_blackmesa"],
        "roles": {
            "scientist": {"type": "character", "match": {"tag": ["rosenberg"]}},
            "device": {"type": "feature", "match": {"tag": ["bs_teleporter"]}},
            "power": {"type": "item", "match": {"tag": ["bs_tele_battery"]}},
            "facility": {"type": "place", "match": {"id": ["bs_blackmesa"]}}},
        "hook": "You are Barney Calhoun, Black Mesa security, running late for an ordinary shift. Then an experiment in Anomalous Materials tears the facility open, and the Marines who arrive to help start shooting everyone. Somewhere in the wreckage is {scientist}, whose old team built a machine that might just get you out: {device}.",
        "goal": "Find {scientist}, cross {facility}, and power {device} with {power} to escape.",
        "resolutions": [{"verb": "put", "target": "device", "means": "power", "title": "Take the leap",
                         "text": "{means.The} locks into {target}'s cradle. The emitters spin up to a scream, the relay locks on, and Rosenberg yells for everyone to get on the platform. You jump. The world turns blue.",
                         "effects": [{"teleport": "room:bs/ba_outro"}]}],
        "ending": "You drive out of Black Mesa with Rosenberg and his team, into the dawn. Nobody is ever going to believe a word of this."},
}

AREAS = {
    "bs_blackmesa": {
        "name": "the Black Mesa security sectors",
        "start_label": "Blue Shift - Barney Calhoun, security guard, late for his shift",
        "tags": ["blackmesa", "start", "blue-shift", "scifi", "security"], "theme": ["blackmesa", "office", "maintenance", "transit"],
        "important": True, "start": "bs/ba_tram1",
        "rooms": ["bs/*"],
        "entrances": ["bs/ba_canal2_canals", "bs/ba_yard2_trains", "bs/ba_power2_cliffs"],
        "player": {"name": "Barney Calhoun", "player_name": "Barney Calhoun", "aliases": ["barney", "calhoun"],
                   "description": "Barney Calhoun, Black Mesa security: blue shirt, ID badge, and a strong sense that he is underpaid."}},
    "bs_training": {
        "name": "the security training course", "tags": ["blackmesa", "training", "indoor"], "theme": ["blackmesa", "office"],
        "rooms": ["bsh/*"], "entrances": ["bsh/ba_hazard1"]},
}

GRAMMAR = {
    "bs_announcement": [
        "\"Good morning, and welcome to the Black Mesa Transit System. This automated train is provided for the security and convenience of Black Mesa Research Facility personnel.\"",
        "\"This train is outbound from Living Quarters to Sector C.\"",
        "\"Security personnel are reminded that their sidearms must be signed for at the beginning of each shift.\"",
        "\"Black Mesa: working to make a better tomorrow for all mankind.\""],
}


def build():
    problems = B.check()
    assert not problems, problems
    manifest = {
        "id": "hl_blueshift", "name": "Half-Life: Blue Shift", "version": "1.0.0", "author": "Patchwork",
        "description": "Gearbox's Blue Shift campaign map by map (ba_tram1 to ba_outro, plus the security training course): the outbound tram, the security station, the falling elevator, the canals, the freight yard and Dr. Rosenberg, the trip to Xen to set the relay, the battery depot and the prototype teleporter. Locked doors and outdoor areas grow generated sections. Spawn as Barney Calhoun.",
        "requires": ["core", "combat", "hl_core"], "load_after": ["hl_core"], "recommends": ["hl_halflife", "hl_opfor"],
        "priority": 66, "tags": ["half-life", "blackmesa", "scifi", "campaign", "blue-shift"]}
    by_chapter = {}
    for rid, r in B.rooms.items():
        key = "training" if rid.startswith(HZ) else r["props"]["map"].split("_")[1].rstrip("0123456789")
        by_chapter.setdefault(key, {})[rid] = r
    files = {"areas.json": {"areas": AREAS, "events": EVENTS, "lore": B.sections["lore"],
                            "macros": MACROS, "rules": RULES, "grammar": GRAMMAR},
             "features.json": {"features": F}}
    for key, chunk in sorted(by_chapter.items()):
        files["maps_%s.json" % key] = {"rooms": chunk}
    B.write(manifest, files)
