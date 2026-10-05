"""hl_opfor: Half-Life: Opposing Force, from boot camp to the G-Man's Osprey.

Corporal Adrian Shephard's campaign, chapter by chapter (of0a0 ... of6a5, plus the
ofboot Boot Camp).  Map codes follow the original BSP names where they are known
and are approximate elsewhere; long maps are condensed to their memorable spaces.
"""

import core
from common import ModBuilder

B = ModBuilder("hl_opfor", "of/")
BC = "ofb/"   # Boot Camp is its own area

LOCKED = {"door": "bm_locked_door", "name": "locked door", "aliases": ["door", "locked door"]}
HATCH = {"door": "bm_jammed_hatch", "name": "jammed hatch", "aliases": ["hatch"]}
WELDED = {"door": "of_welded_door", "name": "welded door", "aliases": ["door", "welded door"]}


def locked(tags, length=(2, 4), chance=0.85, door=LOCKED):
    d = dict(door)
    d.update({"tags": list(tags), "length": list(length), "chance": chance})
    return d


def outdoors(tags, length=(2, 4), chance=0.9, name=None):
    d = {"tags": list(tags), "length": list(length), "chance": chance}
    if name:
        d["name"] = name
    return d


SURF = ["surface", "outdoor", "desert"]

# ===========================================================================
# Welcome to Black Mesa  (of0a0 ... of0a2)
# ===========================================================================
B.set_chapter("Welcome to Black Mesa")
B.room("of0a0_osprey", "Osprey: Final Approach", "You sit strapped into the troop bay of a V-22 Osprey with the rest of your squad, rifles between your knees. The rear ramp is open on the New Mexico desert; Black Mesa's buildings slide by below. The sergeant shouts the drop orders over the rotors: secure the facility, neutralise the scientist Gordon Freeman. Then something huge and winged screams past the ramp, and the Osprey lurches.",
       map="of0a0", tags=["military", "transit", "osprey", "story_skip"], feats=["of_squad", "osprey_ramp"], aliases=["osprey", "troop bay"])
B.room("of0a0_wreck", "Osprey Crash Site", "The Osprey lies broken-backed in a canyon below the facility, one rotor still turning. Bodies in HECU fatigues are scattered around it. The last thing you remember is a scientist's face leaning over you and a voice saying you'd be fine.",
       map="of0a0", tags=["blackmesa", "military", "story_skip"] + SURF, feats=["osprey_wreck_of", "dead_marine"], aliases=["wreck", "crash site"])
B.room("of0a1_infirmary", "Black Mesa Infirmary", "You wake on a cot in a white infirmary, your head ringing. A scientist bends over you: he's waking up, he says, and the security guard at the door says it's a miracle anyone survived that crash. Through the window, the desert is on fire.",
       map="of0a1", tags=["blackmesa", "lab", "indoor"], feats=["infirmary_scientist", "combat_knife", "medkit", "health_charger"], aliases=["infirmary"])
B.room("of0a2_corridor", "Medical Wing Corridor", "A corridor of offices and observation windows. Behind one window a thin man in a blue suit talks with a scientist. When you look again, only the scientist is there.",
       map="of0a2", tags=["blackmesa", "lab", "indoor"], feats=["gman_glimpse_of", "vending_machine", "headcrab"], expand=locked(["lab", "office"], chance=0.6))
B.link("of0a0_osprey", "of0a0_wreck", "down", name="the crash", aliases=["crash", "ramp"], oneway=True)
B.link("of0a0_wreck", "of0a1_infirmary", "in", name="stretcher", aliases=["stretcher"], oneway=True)
B.link("of0a1_infirmary", "of0a2_corridor", "east")

# ===========================================================================
# We Are Pulling Out  (of1a1 ... of1a4)
# ===========================================================================
B.set_chapter("We Are Pulling Out")
B.room("of1a1_staging", "HECU Staging Room", "A storage room the Marines turned into a staging post: ammo crates, a radio on a folding table, a map pinned to the wall with red pins all over Sector C. The radio crackles: all units, we are pulling out. Repeat, we are pulling out.",
       map="of1a1", tags=["blackmesa", "military", "indoor"], feats=["of_radio_set", "ammo_box", "supply_crate"])
B.room("of1a1_lockers", "Maintenance Lockers", "A row of maintenance lockers, one bent open. On the floor, a big pipe wrench.",
       map="of1a1", tags=["blackmesa", "maintenance", "indoor"], feats=["pipe_wrench", "suit_charger_pcv"], expand=locked(["maintenance"], chance=0.6, door=HATCH))
B.room("of1a2_trench", "Desert Trenches", "Back out in the sun. A network of sandbagged trenches runs across the desert toward a landing zone; dead Marines and dead aliens share the sand. A houndeye pack yips somewhere over the berm.",
       map="of1a2", tags=["blackmesa", "military"] + SURF, feats=["houndeye", "houndeye", "dead_marine", "grenade"], expand=outdoors(["surface", "military"]))
B.room("of1a3_lz", "Evacuation Landing Zone", "The landing zone, a flat shelf of rock above the canyon. The last Osprey is lifting off without you, ramp closing. As you watch, an alien flier dives out of the sun and rakes it; it banks away trailing smoke, and is gone.",
       map="of1a3", tags=["blackmesa", "military"] + SURF, feats=["dead_marine", "ammo_box"], aliases=["lz", "landing zone"], expand=outdoors(["surface"]))
B.room("of1a4_cliffs", "Cliffside Pipeline", "A huge pipeline clings to the cliff face above a drop to the river. You'll have to walk along the top of it. A bullsquid watches from a ledge.",
       map="of1a4", tags=["blackmesa"] + SURF, feats=["bullsquid", "battery"], expand=outdoors(["surface"], chance=0.6))
B.link("of0a2_corridor", "of1a1_staging", "north")
B.link("of1a1_staging", "of1a1_lockers", "west")
B.link("of1a1_staging", "of1a2_trench", "up", name="stairs to the surface", aliases=["stairs", "surface"])
B.link("of1a2_trench", "of1a3_lz", "north", 3)
B.link("of1a3_lz", "of1a4_cliffs", "east", 3)

# ===========================================================================
# Missing in Action  (of1a5, of1a6)
# ===========================================================================
B.set_chapter("Missing in Action")
B.room("of1a5_offices", "Abandoned Offices", "Back inside, a wing of offices that the Marines swept and left. Desks are overturned into barricades, and the walls are pocked with bullet holes. A radio on a dead Marine's belt says your unit is listed as missing in action.",
       map="of1a5", tags=["blackmesa", "office", "indoor"], feats=["zombie_guard", "dead_marine_radio", "bm_memo"], expand=locked(["office"], chance=0.7))
B.room("of1a5_checkpoint", "Security Checkpoint", "A security checkpoint where a heavyset guard has holed up behind the window, eating a sandwich. Otis, his name tag says. He's not keen on Marines, but he's less keen on headcrabs.",
       map="of1a5", tags=["blackmesa", "office", "indoor"], feats=["otis", "health_charger", "desert_eagle"])
B.room("of1a6_vents", "Ventilation System", "A cramped ventilation network. Fans turn behind grilles; somewhere ahead, a vent drops into darkness.",
       map="of1a6", tags=["blackmesa", "maintenance", "indoor"], feats=["headcrab", "battery"])
B.room("of1a6_dock", "Loading Dock", "A loading dock at the bottom of a freight shaft, with trucks backed up to the bays and a forklift on its side. Gonomes lurch among the pallets.",
       map="of1a6", tags=["blackmesa", "storage", "indoor"], feats=["gonome", "supply_crate", "supply_crate"], expand=locked(["storage", "transit"], chance=0.7))
B.link("of1a4_cliffs", "of1a5_offices", "in", name="maintenance door", aliases=["door"])
B.link("of1a5_offices", "of1a5_checkpoint", "east")
B.link("of1a5_checkpoint", "of1a6_vents", "north", name="air vent", aliases=["vent", "duct"])
B.link("of1a6_vents", "of1a6_dock", "down", name="drop", aliases=["drop"])

# ===========================================================================
# Friendly Fire  (of2a1 ... of2a3)
# ===========================================================================
B.set_chapter("Friendly Fire")
B.room("of2a1_rail", "Supply Rail Tunnels", "Long service-rail tunnels, lit by the occasional caged bulb. A HECU fireteam is pinned at a junction ahead: they wave you in, glad of another gun.",
       map="of2a1", tags=["blackmesa", "transit", "military", "indoor"], feats=["hecu_ally", "zombie_soldier", "ammo_box"])
B.room("of2a2_ambush", "Black Ops Ambush", "A storage yard where the Marines walked into an ambush. Black-clad agents dropped from the catwalks and cut them down. The killers aren't aliens. They're people on your own side, and they aren't taking prisoners either.",
       map="of2a2", tags=["blackmesa", "storage", "military", "indoor"], feats=["male_assassin", "dead_marine", "m249"])
B.room("of2a3_medbay", "Field Aid Station", "A makeshift aid station in an office, red crosses taped to the doors. A HECU medic is still here, out of morphine and patience, and a combat engineer is trying to cut through a welded door.",
       map="of2a3", tags=["blackmesa", "office", "military", "indoor"], feats=["hecu_medic", "hecu_engineer", "medkit"],
       expand=locked(["office", "storage"], chance=0.9, door=WELDED))
B.link("of1a6_dock", "of2a1_rail", "east", 3)
B.link("of2a1_rail", "of2a2_ambush", "east", 3)
B.link("of2a2_ambush", "of2a3_medbay", "north")

# ===========================================================================
# We Are Not Alone  (of2a4 ... of2a6)
# ===========================================================================
B.set_chapter("We Are Not Alone")
B.room("of2a4_storm", "Portal Storm Courtyard", "An enclosed courtyard where the air keeps splitting open in green light. Out of the portals step creatures nobody has a name for: tall one-eyed soldiers carrying living weapons, and spiny things that spit needles. These are not Xen's aliens. Something else is coming through.",
       map="of2a4", tags=["blackmesa", "racex"] + SURF, feats=["shock_trooper", "pit_drone", "dead_marine"], expand=outdoors(["surface", "racex"]))
B.room("of2a5_barnacles", "Biology Lab: Barnacle Research", "A biology lab full of tanks of Xen fauna, most of them broken. Barnacles hang from the ceiling, tongues dangling. On a bench sits a barnacle in a harness: someone has turned one into a tool.",
       map="of2a5", tags=["blackmesa", "lab", "indoor"], feats=["grapple", "barnacle", "dead_scientist", "bm_terminal"], expand=locked(["lab"], chance=0.6))
B.room("of2a6_gorge", "Grapple Gorge", "A gorge between two cliffs, with barnacles clinging under an overhang on the far side. There is no bridge. There is, however, something to swing from.",
       map="of2a6", tags=["blackmesa"] + SURF, feats=["barnacle", "pit_drone", "spore_launcher"], expand=outdoors(["surface", "racex"]))
B.link("of2a3_medbay", "of2a4_storm", "up")
B.link("of2a4_storm", "of2a5_barnacles", "east")
B.link("of2a5_barnacles", "of2a6_gorge", "north")

# ===========================================================================
# Crush Depth  (of3a1 ... of3a3)
# ===========================================================================
B.set_chapter("Crush Depth")
B.room("of3a1_reservoir", "Underground Reservoir", "A vast reservoir under the facility, its surface glassy and black. Catwalks run along the walls above the water, and something long moves below the surface.",
       map="of3a1", tags=["blackmesa", "maintenance", "indoor", "water"], feats=["ichthyosaur", "supply_crate"], expand=locked(["maintenance"], chance=0.6, door=HATCH))
B.room("of3a2_pumps", "Deep Pump Station", "A pump station so far down the walls sweat. Gauges read pressures nobody should be under. Black Ops agents are planting charges on the pumps.",
       map="of3a2", tags=["blackmesa", "maintenance", "indoor", "military"], feats=["male_assassin", "female_assassin", "satchel", "battery"])
B.room("of3a3_lift", "Cargo Lift Shaft", "A huge cargo lift that rises through the rock, past level after level of Black Mesa. Shock troopers warp in on the landings as you pass.",
       map="of3a3", tags=["blackmesa", "transit", "indoor"], feats=["shock_trooper", "shock_roach", "ammo_box"])
B.link("of2a6_gorge", "of3a1_reservoir", "down", name="swing across the gorge", aliases=["gorge", "overhang"])
B.link("of3a1_reservoir", "of3a2_pumps", "east")
B.link("of3a2_pumps", "of3a3_lift", "up", name="cargo lift", aliases=["lift"])

# ===========================================================================
# Vicarious Reality  (of3a4 ... of3a6)
# ===========================================================================
B.set_chapter("Vicarious Reality")
B.room("of3a4_lab", "Displacer Research Lab", "A teleport research lab where the scientists are still at work, mostly from denial. One of them presents you with a bulky weapon wired to a backpack: the displacer cannon. It fires a portal, he explains, and if you shoot it at your own feet it takes you somewhere else entirely.",
       map="of3a4", tags=["blackmesa", "lab", "indoor"], feats=["displacer_scientist", "displacer", "health_charger", "suit_charger"])
B.room("of3a5_xen", "Xen: Displaced", "A step through green light and you're somewhere else: a spongy island floating in a violet void, light-stalks shrinking from you. A portal flickers on the rock where you landed.",
       map="of3a5", tags=["xen", "alien", "outdoor"], feats=["xen_light", "healing_pool", "houndeye", "xen_glyph"], expand=outdoors(["xen"], name="drifting rock"))
B.room("of3a6_return", "Teleport Return Lab", "You spill out of a portal into another of the teleport labs, back in Black Mesa. The scientists here seem pleased with the result, and terrified of what came through after you.",
       map="of3a6", tags=["blackmesa", "lab", "indoor"], feats=["alien_slave_of", "battery"], expand=locked(["lab"], chance=0.6))
B.link("of3a3_lift", "of3a4_lab", "north")
B.link("of3a4_lab", "of3a5_xen", "in", name="the displacer field", aliases=["field", "portal", "displacer field"], back_name="the portal home")
B.link("of3a5_xen", "of3a6_return", "east", name="flickering portal", aliases=["portal"])

# ===========================================================================
# Pit Worm's Nest  (of4a1 ... of4a3)
# ===========================================================================
B.set_chapter("Pit Worm's Nest")
B.room("of4a1_waste", "Waste Processing Approach", "The waste processing levels again, but worse: Race X spores have grown over everything, and the air tastes of rust.",
       map="of4a1", tags=["blackmesa", "maintenance", "indoor", "racex"], feats=["pit_drone", "baby_voltigore", "medkit"], expand=locked(["maintenance", "racex"], chance=0.6, door=HATCH))
B.room("of4a2_nest", "Pit Worm's Nest", "A huge flooded processing pit. In the middle of it a worm the size of a submarine rears out of the sludge, its single eye tracking you with a cutting beam. Two waste valves stand on platforms above the pit; a big control lever sits in the booth.",
       map="of4a2", tags=["blackmesa", "maintenance", "indoor", "racex", "water"], feats=["pit_worm_of", "worm_valve", "worm_lever"], aliases=["nest", "pit"])
B.room("of4a3_sluice", "Sluice Gate Control", "A control room for the sluice gates, with a window on the pit. Beyond it, a ladder leads up toward daylight.",
       map="of4a3", tags=["blackmesa", "maintenance", "indoor"], feats=["voltigore_corpse", "battery", "suit_charger"])
B.link("of3a6_return", "of4a1_waste", "down")
B.link("of4a1_waste", "of4a2_nest", "east")
B.link("of4a2_nest", "of4a3_sluice", "north")

# ===========================================================================
# Foxtrot Uniform  (of4a4, of4a5)
# ===========================================================================
B.set_chapter("Foxtrot Uniform")
B.room("of4a4_canyon", "Sniper's Canyon", "A canyon outside the facility where Black Ops snipers hold the high ground. A HECU sniper lies dead behind a rock, his rifle beside him. Over the radio, somebody uses the phrase that names this place: foxtrot uniform.",
       map="of4a4", tags=["blackmesa", "military"] + SURF, feats=["sniper_rifle", "dead_marine", "male_assassin"], expand=outdoors(["surface", "military"]))
B.room("of4a5_parking", "Military Motor Pool", "A motor pool of trucks and Humvees, Marines and Black Ops shooting it out across it. A voltigore wanders into the middle of the firefight, and everybody stops shooting each other for a moment.",
       map="of4a5", tags=["blackmesa", "military"] + SURF, feats=["voltigore", "hecu_ally", "supply_crate", "night_vision"], expand=outdoors(["military", "surface"]))
B.link("of4a3_sluice", "of4a4_canyon", "up", name="ladder", aliases=["ladder"])
B.link("of4a4_canyon", "of4a5_parking", "east", 3)

# ===========================================================================
# The Package  (of5a1 ... of5a4)
# ===========================================================================
B.set_chapter("The Package")
B.room("of5a1_tracks", "Freight Rail Spur", "A freight spur where a small engine has been abandoned with its doors open. Black Ops agents passed this way with something heavy, and the scrape marks lead into the facility.",
       map="of5a1", tags=["blackmesa", "transit", "indoor"], feats=["female_assassin", "ammo_box"], expand=locked(["transit", "storage"], chance=0.6))
B.room("of5a2_warehouse", "Black Ops Warehouse", "A warehouse the Black Ops have been using as a base: crates of their equipment, a whiteboard with a countdown written on it, a table with a radio and a coffee flask.",
       map="of5a2", tags=["blackmesa", "storage", "military", "indoor"], feats=["male_assassin", "black_ops_board", "supply_crate", "penguin"])
B.room("of5a3_tunnel", "Freight Tunnel", "A low freight tunnel with gonomes in the shadows. Ahead, through a gate, the underground garage.",
       map="of5a3", tags=["blackmesa", "transit", "indoor"], feats=["gonome", "medkit"])
B.room("of5a4_garage", "Underground Garage: The Package", "A parking garage deep in the facility, cars still in their bays. In the middle of the floor, on a wheeled cart, sits the package: a nuclear device with a countdown display. Black Ops agents guard it from behind the pillars.",
       map="of5a4", tags=["blackmesa", "military", "indoor"], feats=["nuke", "male_assassin", "health_charger"], aliases=["garage"])
B.link("of4a5_parking", "of5a1_tracks", "down")
B.link("of5a1_tracks", "of5a2_warehouse", "east")
B.link("of5a2_warehouse", "of5a3_tunnel", "east")
B.link("of5a3_tunnel", "of5a4_garage", "east")

# ===========================================================================
# Worlds Collide  (of6a1 ... of6a4)
# ===========================================================================
B.set_chapter("Worlds Collide")
B.room("of6a1_plant", "Power Plant Approach", "A huge power plant complex where Race X has broken through in force. Purple-veined growths cover the walls. Shock troopers hold the walkways.",
       map="of6a1", tags=["blackmesa", "maintenance", "indoor", "racex"], feats=["shock_trooper", "pit_drone", "battery"], expand=locked(["maintenance", "racex"], chance=0.6))
B.room("of6a2_cooling", "Cooling Tower", "The inside of a cooling tower, a great hollow throat of concrete open to the sky. A portal storm crackles at the top.",
       map="of6a2", tags=["blackmesa", "maintenance", "racex"], feats=["voltigore", "medkit", "suit_charger"])
B.room("of6a3_bay", "Coolant Bay: The Gene Worm", "A cavernous coolant bay. At its far end a portal has torn open, and out of it the Gene Worm is pushing its way into the world: a vast slick body, two armoured eyes, and a mouth that sprays poison. Two plasma cannons are mounted on the walkways either side of it.",
       map="of6a3", tags=["blackmesa", "maintenance", "indoor", "racex"], feats=["gene_worm_of", "plasma_cannon", "plasma_cannon_2"], aliases=["coolant bay", "bay"])
B.link("of5a4_garage", "of6a1_plant", "up")
B.link("of6a1_plant", "of6a2_cooling", "east")
B.link("of6a2_cooling", "of6a3_bay", "down")

# ===========================================================================
# Conclusion  (of6a5)
# ===========================================================================
B.set_chapter("Conclusion")
B.room("of6a5_osprey", "An Osprey, Going Nowhere", "You are sitting in an Osprey's troop bay again. The engines are running, but nobody's flying it. Opposite you, legs crossed, briefcase on his knee, sits the man in the blue suit.",
       map="of6a5", tags=["osprey", "void", "story_skip"], feats=["gman_of"])
B.link("of6a5_osprey", "of6a3_bay", "out", name="the ramp", aliases=["ramp", "back"], oneway=True)

# ===========================================================================
# Boot Camp  (ofboot0 ... ofboot4)  - its own area
# ===========================================================================
BOOT = ["military", "training", "outdoor", "desert"]
B.set_chapter("Boot Camp")
B.room(BC + "ofboot0_barracks", "Santego Military Base: Barracks", "A long barracks of steel bunks and footlockers at Santego Military Base, Arizona. Your drill instructor is standing very close to you and shouting.",
       map="ofboot0", tags=["military", "training", "indoor"], feats=["drill_instructor"], aliases=["barracks"])
B.room(BC + "ofboot1_course", "Obstacle Course", "An obstacle course of walls, crawl nets, ladders and a muddy rope swing. A corporal times you with a stopwatch and an expression of contempt.",
       map="ofboot1", tags=BOOT, feats=["supply_crate"])
B.room(BC + "ofboot2_climb", "Climbing and Rappelling Tower", "A wooden tower with ropes, ladders and a zip line. The instructor says you'll be dropping into worse than this.", map="ofboot2", tags=BOOT)
B.room(BC + "ofboot3_range", "Firing Range", "A firing range of pop-up targets and sandbags. A rack holds a 9mm and a pipe wrench for the melee drills.",
       map="ofboot3", tags=BOOT, feats=["glock", "training_target_of"])
B.room(BC + "ofboot4_grenades", "Grenade Pit and Medical Drill", "A grenade pit behind a concrete wall, and a medical tent where a corpsman teaches you which end of a syringe to hold. Your graduation is waiting at the end.",
       map="ofboot4", tags=BOOT, feats=["grenade", "medkit"])
B.chain([BC + "ofboot0_barracks", BC + "ofboot1_course", BC + "ofboot2_climb", BC + "ofboot3_range", BC + "ofboot4_grenades"], "north")

# ===========================================================================
# Features
# ===========================================================================
F = B.section("features")
F.update({
    "of_squad": {"extends": ["scenery"], "name": "your squad", "proper": True, "aliases": ["squad", "marines", "sergeant", "soldiers"],
        "appearance": "Your squadmates sit along the bulkhead, masks on.",
        "description": "Eight Marines and a sergeant, all as new to this as you are.",
        "actions": {"talk": ["The sergeant bellows over the rotors: \"Listen up! We're dropping in hot. Freeman is our priority. Anybody gets in the way, you put them down!\""]}},
    "osprey_ramp": {"extends": ["scenery"], "name": "rear ramp", "aliases": ["ramp", "desert", "view"], "appearance": False,
        "description": "Through the open ramp, Black Mesa: hangars, chimneys, the dam, and smoke rising from somewhere it shouldn't."},
    "osprey_wreck_of": {"extends": ["scenery"], "name": "Osprey wreck", "aliases": ["osprey", "wreck"], "appearance": False,
        "description": "Your ride in, folded around a boulder."},
    "infirmary_scientist": {"extends": ["scientist"], "appearance": "{self.Name} hovers by your cot.",
        "actions": {"talk": [{"do": ["\"Easy, Corporal. You took a nasty blow. Your squad? I... I don't know. The Marines are pulling everybody out, I hear. You'd better hurry.\""]}]}},
    "gman_glimpse_of": {"extends": ["scenery"], "name": "man in a blue suit", "aliases": ["man", "suit", "g-man", "gman"], "appearance": False,
        "description": "Through the observation window, the man in the blue suit is talking to a scientist. He looks up at you, and then he isn't there."},
    "of_radio_set": {"extends": ["scenery"], "name": "radio set", "aliases": ["radio", "radio set", "map"],
        "appearance": "A HECU radio set crackles on the table.", "description": "The radio repeats the order: all units, pull out to the evacuation point.",
        "actions": {"listen": ["\"...all units, we are pulling out. Repeat, we are pulling out. Proceed to the evac point immediately...\""],
                    "use": ["You key the handset. Nobody answers you; they're busy leaving."]}},
    "suit_charger_pcv": {"extends": ["suit_charger"], "name": "PCV charger", "aliases": ["charger", "pcv charger", "suit charger"]},
    "dead_marine_radio": {"extends": ["dead_marine"], "features": ["radio"],
        "appearance": "A dead Marine is slumped against a desk, his radio still talking."},
    "otis": {"extends": ["security_guard"], "name": "Otis", "proper": True, "aliases": ["otis", "guard", "fat guard"], "important": True,
        "tags": ["security", "bm_staff", "otis"],
        "appearance": "Otis, a heavyset Black Mesa guard, leans in the checkpoint window.",
        "description": "Big, sweaty, unhurried, with a revolver on his hip and a sandwich in his hand.",
        "profile": {"personality": ["cheerful", "greedy"], "motives": ["survive", "comfort", "duty"],
            "motive_text": "get out of here alive, preferably with lunch",
            "goals": ["get out of Black Mesa", "find his cousin", "not get shot by a Marine"],
            "backstory": "\"Otis Laurey, Black Mesa security. Fourteen years, never once fired this thing in anger. Today I fired it in panic.\"",
            "roles": ["giver", "informant", "holder", "ally", "victim"], "knows": ["blackmesa", "security", "rumour"],
            "wants": ["food", "weapon", "medicine"],
            "epilogue": "Otis makes it out. Rumour says he still has the sandwich."},
        "actions": {"talk": [{"do": ["\"Whoa, whoa, Marine! I'm on your side, all right? ...Am I on your side?\""]}]}},
    "black_ops_board": {"extends": ["scenery", "readable"], "name": "whiteboard", "aliases": ["whiteboard", "board", "countdown"],
        "appearance": "A whiteboard on the wall is covered in a Black Ops plan.",
        "props": {"text": "PACKAGE -> GARAGE LEVEL 4. ARM AT T-15. ALL TEAMS EXFIL BY T-5. NO HECU SURVIVORS."},
        "description": "Times, arrows, and a sketch of the facility with an X on it."},
    "nuke": {"extends": ["scenery"], "name": "nuclear device", "aliases": ["nuke", "bomb", "device", "package", "warhead"],
        "important": True, "tags": ["of_nuke", "heart"],
        "appearance": [{"if": {"flag": "of_nuke_disarmed"}, "text": "The nuclear device sits on its cart, its display dark."},
                       {"text": "The nuclear device squats on its cart, its countdown display glowing red."}],
        "description": "A tactical nuclear device on a wheeled cart: a fat steel cylinder, a keypad, a display counting down, and a stencil that says, unhelpfully, PROPERTY OF U.S. GOVERNMENT.",
        "actions": {"use": [{"if": {"flag": "of_nuke_disarmed"}, "do": ["It's off. For now."]},
                            {"do": [{"flag": "of_nuke_disarmed"}, {"say": "You pry off the access panel and pull the arming key. The countdown blinks, stutters and goes dark. For a while, the world is a little less likely to end.", "style": "story"}]}]}},
    "pit_worm_of": {"extends": ["pit_worm"], "important": True, "tags": ["pit_worm_boss"],
        "solve": ["turn waste valve", "pull control lever"],
        "on_death": [{"flag": "of_pitworm_dead"}]},
    "worm_valve": {"extends": ["scenery"], "name": "waste valve", "aliases": ["valve", "valves", "waste valve", "wheel"],
        "appearance": [{"if": {"flag": "of_worm_valve"}, "text": "The waste valves stand open, venting gas into the pit."},
                       {"text": "Two big waste valves stand on platforms above the pit, closed."}],
        "description": "They vent processing gas into the pit. The gas is extremely flammable.",
        "actions": {"use": [{"if": {"flag": "of_worm_valve"}, "do": ["They're already open."]},
                            {"do": [{"flag": "of_worm_valve"}, "You spin the valves open. Gas hisses down into the pit around the worm."]}],
                    "turn": [{"do": [{"flag": "of_worm_valve"}, "You spin the valves open. Gas hisses down into the pit."]}]}},
    "worm_lever": {"extends": ["scenery"], "name": "control lever", "aliases": ["lever", "control lever", "booth", "igniter"],
        "appearance": "A heavy control lever marked IGNITION sits in the booth.", "description": "Ignition for the waste-gas burners.",
        "actions": {"use": [{"macro": "of_burn_worm"}], "pull": [{"macro": "of_burn_worm"}], "push": [{"macro": "of_burn_worm"}]}},
    "voltigore_corpse": {"extends": ["scenery"], "name": "voltigore carcass", "aliases": ["carcass", "voltigore", "corpse"],
        "appearance": "A dead voltigore lies across the floor, still sparking.", "description": "Even dead, its jaw crackles with purple light."},
    "displacer_scientist": {"extends": ["scientist"], "appearance": "{self.Name} holds out the displacer cannon proudly.",
        "actions": {"talk": [{"do": ["\"Take it. Point it at the floor and squeeze, and it'll put you on the other side, a place we call Xen. Point it at something else and that goes instead. Don't ask where.\""]}]}},
    "alien_slave_of": {"extends": ["vortigaunt"]},
    "plasma_cannon": {"extends": ["scenery"], "name": "left plasma cannon", "aliases": ["left cannon", "cannon", "plasma cannon", "left plasma cannon"],
        "appearance": [{"if": {"flag": "of_cannon_1"}, "text": "The left plasma cannon smokes, spent."},
                       {"text": "A plasma cannon is mounted on the left-hand walkway, aimed at the portal."}],
        "description": "Built to keep things from coming through the portal. Its controls are simple: aim, fire.",
        "actions": {"use": [{"macro": "of_cannon", "with": {"which": 1}}], "push": [{"macro": "of_cannon", "with": {"which": 1}}]}},
    "plasma_cannon_2": {"extends": ["scenery"], "name": "right plasma cannon", "aliases": ["right cannon", "cannon", "plasma cannon", "right plasma cannon"],
        "appearance": [{"if": {"flag": "of_cannon_2"}, "text": "The right plasma cannon smokes, spent."},
                       {"text": "A plasma cannon is mounted on the right-hand walkway."}],
        "description": "A twin of the other cannon.",
        "actions": {"use": [{"macro": "of_cannon", "with": {"which": 2}}], "push": [{"macro": "of_cannon", "with": {"which": 2}}]}},
    "gene_worm_of": {"extends": ["gene_worm"], "important": True, "tags": ["gene_worm", "villain", "racex"],
        "solve": ["use left plasma cannon", "use right plasma cannon"],
        "profile": {"personality": ["cold"], "motives": ["dominion", "hunger", "survive"],
            "motive_text": "remake this world into one where Race X can live",
            "goals": ["breach the portal", "terraform Black Mesa"],
            "backstory": "There is no mind in it you could talk to. It has come to change the air, the water and the ground, and everything that lives on them.",
            "roles": ["antagonist"], "knows": ["racex"],
            "greet": ["The Gene Worm's eyes swivel toward you, each as big as a truck."],
            "confront": ["The Gene Worm opens its mouth, and the air fills with toxin."], "epilogue": ""},
        "on_death": [{"flag": "of_geneworm_dead"},
                     {"say": "The portal implodes around the Gene Worm's corpse, and a flash of green light swallows the coolant bay. When it clears, you are somewhere else...", "style": "story"},
                     {"teleport": "room:of/of6a5_osprey"}]},
    "gman_of": {"extends": ["gman"], "profile": dict(core.F["gman"]["profile"], menu=False),
        "actions": {"talk": [{"if": {"all": [{"flag": "of_geneworm_dead"}, {"flag": "story_resolved"}]}, "do": [{"end_game": "\"Corporal Shephard,\" the man in the suit says, with that peculiar rhythm. \"You have... adapted. Survived against all the odds. I can relate. I have recommended your... detainment, in a place where you can do no harm. There's no sense in letting you... speak about what you've seen.\" He smiles thinly as the Osprey's doors slide shut. \"I'm sure you understand.\" Far away, a Black Ops nuke you thought you had disarmed counts down to zero, re-armed by a man with a briefcase.", "win": True}]},
            {"do": ["\"Not yet, {player.name},\" he says. \"There is... unfinished business. Not... yet.\" The Osprey's ramp drops open behind you."]}]}},
    "drill_instructor": {"extends": ["person"], "name": "the drill instructor", "proper": True, "aliases": ["drill instructor", "instructor", "sergeant", "di"],
        "appearance": "The drill instructor stands in front of you, face red, campaign hat level.",
        "description": "Every inch a drill sergeant, and he has a lot of inches.",
        "actions": {"talk": ["\"Did I say you could talk, maggot? Get out to that course and show me something!\""]}},
    "training_target_of": {"extends": ["scenery"], "name": "pop-up target", "aliases": ["target", "targets"],
        "appearance": "Pop-up targets line the range.", "description": "Green silhouettes on spring arms.",
        "actions": {"attack": ["You drop three targets in a row. The instructor grunts, which is high praise."]}},
})

# Mark the shared core's equipment as important in this campaign.
for fid in ("displacer", "grapple"):
    F[fid] = {"_patch": True, "important": True}

MACROS = {
    "of_burn_worm": {"do": [
        {"if": {"flag": "of_pitworm_dead"}, "then": ["The pit is a charred hole now.", {"stop": True}]},
        {"if": {"not": {"flag": "of_worm_valve"}}, "then": ["You throw the lever. A spark spits from the burners, but there's no gas in the pit to light.", {"stop": True}]},
        {"flag": "of_pitworm_dead"},
        {"say": "You haul the lever down. The burners spark, and the gas in the pit goes up in a single rolling fireball. The pit worm thrashes, screams through the flames, and sinks into the boiling sludge.", "style": "story"},
        {"find": {"def": "pit_worm_of"}, "in": "room:of/of4a2_nest", "as": "worm", "hidden_too": True},
        {"if": {"exists": "local:worm"}, "then": [{"destroy": "local:worm"}]}]},
    "of_cannon": {"do": [
        {"if": {"flag": "of_cannon_{which}"}, "then": ["That cannon is spent.", {"stop": True}]},
        {"flag": "of_cannon_{which}"},
        {"find": {"def": "gene_worm_of"}, "in": "room:of/of6a3_bay", "as": "worm", "hidden_too": True},
        {"if": {"exists": "local:worm"},
         "then": [{"say": "The plasma cannon thumps a bolt of green fire straight into one of the Gene Worm's eyes. It shrieks, and its armour plates gape around the wound.", "style": "good"},
                  {"set": {"armor": 0}, "on": "local:worm"}],
         "else": ["The cannon fires into the empty portal."]}]},
}

RULES = {}

B.section("lore").update({
    "of_mission": {"title": "Mission orders", "about": ["area:of_blackmesa"], "tags": ["hecu", "military"],
        "text": "Corporal Adrian Shephard's unit was sent into Black Mesa with simple orders: contain the incident, eliminate the alien threat and silence anyone who knows too much, starting with a physicist named Gordon Freeman."},
    "of_racex": {"title": "Race X", "about": ["area:of_blackmesa"], "tags": ["racex", "xen", "science"],
        "text": "The second wave of invaders aren't from Xen at all. Shock troopers, pit drones, voltigores: a species from somewhere else entirely, following the rift in. The scientists call them Race X, for lack of anything better."},
    "of_black_ops": {"title": "The Black Ops", "about": ["area:of_blackmesa"], "tags": ["military", "black_ops", "hecu"],
        "text": "When the Marines started losing, someone sent in the Black Ops: silent, black-clad, answering to nobody you know. Their orders cover the Marines too. And they brought a package."},
    "of_shephard": {"title": "Missing in action", "about": ["area:of_blackmesa"], "tags": ["hecu", "rumour"], "chance": 0.7,
        "text": "Corporal Adrian Shephard: listed missing in action after his Osprey went down over Black Mesa. The listing never gets updated."},
    "of_gene_worm": {"title": "The Gene Worm", "about": ["def:gene_worm_of"], "tags": ["racex"],
        "text": "Race X doesn't conquer a world. It changes it. The Gene Worm is how: a living factory that reshapes the land around it into something Race X can live in."},
})

EVENTS = {
    "of_worlds_collide": {
        "title": ["Opposing Force", "Worlds Collide", "Race X"],
        "tags": ["blackmesa", "opposing-force", "racex"], "start_areas": ["of_blackmesa"],
        "roles": {
            "villain": {"type": "character", "match": {"tag": ["gene_worm"]}},
            "facility": {"type": "place", "match": {"id": ["of_blackmesa"]}}},
        "hook": "You are Corporal Adrian Shephard of the Hazardous Environment Combat Unit, dropped into the Black Mesa Research Facility to clean up a mess and silence a physicist. Your Osprey never lands. By the time you wake, your unit has pulled out without you, and something new is coming through the portals: something called {villain}.",
        "goal": "Survive {facility} without your unit, and stop {villain} before it remakes the world.",
        "resolutions": [{"verb": "attack", "target": "villain", "title": "Kill the Gene Worm",
                         "text": "{target.The} comes apart in the portal's collapse. Race X's way into the world closes behind it."}],
        "ending": "The Gene Worm is dead and the portal is shut. But you are still in Black Mesa, and somebody very patient has been watching you."},
    "of_the_package": {
        "title": ["The Package", "Foxtrot Uniform"], "tags": ["blackmesa", "opposing-force", "military"], "start_areas": ["of_blackmesa"],
        "weight": 0.6,
        "roles": {
            "device": {"type": "feature", "match": {"tag": ["of_nuke"]}},
            "facility": {"type": "place", "match": {"id": ["of_blackmesa"]}}},
        "hook": "You are Corporal Adrian Shephard, HECU, left behind at Black Mesa when your unit pulled out. The Marines are losing, the aliens are winning, and the Black Ops have brought in something to end the argument: {device}.",
        "goal": "Cross {facility}, find {device} and stop it before it goes off.",
        "resolutions": [{"verb": "use", "target": "device", "title": "Disarm the package",
                         "text": "You pull the arming key from {target}. The countdown dies. Somewhere very close, someone in a blue suit sighs, and makes a note."}],
        "ending": "The package is disarmed, for now. You don't see the man with the briefcase kneel beside it after you've gone and turn the key back."},
}

AREAS = {
    "of_blackmesa": {
        "name": "the Black Mesa complex",
        "start_label": "Opposing Force - Corporal Adrian Shephard, HECU, dropping in by Osprey",
        "tags": ["blackmesa", "start", "opposing-force", "military", "scifi", "racex"], "theme": ["blackmesa", "military", "surface", "maintenance"],
        "important": True, "start": "of/of0a0_osprey",
        "rooms": ["of/*"],
        "entrances": ["of/of1a2_trench", "of/of2a4_storm", "of/of4a4_canyon", "of/of1a6_dock"],
        "player": {"name": "Adrian Shephard", "player_name": "Corporal Adrian Shephard", "aliases": ["adrian", "shephard", "corporal"],
                   "description": "Corporal Adrian Shephard, HECU: gas mask, fatigues, a Powered Combat Vest, and orders that stopped making sense an hour ago."},
        "kit": ["pcv"]},
    "of_bootcamp": {
        "name": "Santego Military Base", "tags": ["military", "training", "outdoor"], "theme": ["military", "surface"],
        "rooms": ["ofb/*"], "entrances": ["ofb/ofboot0_barracks"]},
}

GRAMMAR = {}


def build():
    problems = B.check()
    assert not problems, problems
    manifest = {
        "id": "hl_opfor", "name": "Half-Life: Opposing Force", "version": "1.0.0", "author": "Patchwork",
        "description": "Gearbox's Opposing Force campaign map by map (of0a0 to of6a5, plus the Boot Camp): the Osprey crash, the Marines pulling out, Otis, the Black Ops, Race X, the barnacle grapple, the displacer cannon, the Pit Worm, Foxtrot Uniform, the Black Ops' package, the Gene Worm and the G-Man's Osprey. Locked and welded doors and outdoor areas grow generated sections. Spawn as Corporal Adrian Shephard.",
        "requires": ["core", "combat", "hl_core"], "load_after": ["hl_core"], "recommends": ["hl_halflife", "hl_blueshift"],
        "priority": 65, "tags": ["half-life", "blackmesa", "scifi", "campaign", "opposing-force"]}
    by_chapter = {}
    for rid, r in B.rooms.items():
        key = "boot" if rid.startswith(BC) else r["props"]["map"][:3]
        by_chapter.setdefault(key, {})[rid] = r
    files = {"areas.json": {"areas": AREAS, "events": EVENTS, "lore": B.sections["lore"],
                            "macros": MACROS, "rules": RULES, "grammar": GRAMMAR},
             "features.json": {"features": F}}
    for key, chunk in sorted(by_chapter.items()):
        files["maps_%s.json" % key] = {"rooms": chunk}
    B.write(manifest, files)
