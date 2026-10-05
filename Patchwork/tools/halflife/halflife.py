"""hl_halflife: the Half-Life campaign, map by map, from the inbound tram to the G-Man.

Each room corresponds to a recognisable place in one of the original maps
(c0a0 ... c5a1, and the t0a0 Hazard Course).  Long maps are condensed to their
memorable spaces; small details are approximate where the originals are hazy.
"""

import core
from common import ModBuilder

B = ModBuilder("hl_halflife", "hl/")
H = "hlh/"   # the Hazard Course is its own area

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


POST = ["post_cascade"]   # rooms that only exist after the disaster

# ===========================================================================
# Black Mesa Inbound  (c0a0 - c0a0e)
# ===========================================================================
B.set_chapter("Black Mesa Inbound")
B.room("c0a0_tram", "Tram Car: Departure", "You sit in the Black Mesa Transit System's tram, rattling into the mountain on an overhead rail. Through the windows the desert light gives way to concrete and sodium lamps. The recorded announcer welcomes you, gives the time as 8:47 a.m. and reminds you that the facility's safety record is a matter of pride.",
       after="The tram car sits dead on its rail, windows cracked, the announcer's speaker hissing static.",
       map="c0a0", tags=["transit", "indoor", "tram"], feats=["tram_announcer", "tram_window"], aliases=["tram", "tram car"])
B.room("c0a0a_loading", "Tram Ride: Cargo Loading Bay", "The tram glides through an enormous loading bay where yellow robotic arms swing pallets of crates onto conveyors. A security guard bangs on a jammed door, and a forklift beeps in reverse somewhere below.",
       after="The loading bay is dark. A robotic arm hangs frozen mid-swing, and crates lie burst across the floor.",
       map="c0a0a", tags=["transit", "indoor", "storage"], feats=["robot_arm"])
B.room("c0a0b_sectors", "Tram Ride: Sector Junctions", "You pass a dozen sector signs in quick succession: research, storage, living quarters, waste processing. Scientists ride moving walkways past windows full of equipment. On a parallel track, another tram slides by. Standing in it is a thin man in a blue suit, holding a briefcase, looking straight at you.",
       after="The junction is half-collapsed. Rubble covers the parallel track where the other tram once ran.",
       map="c0a0b", tags=["transit", "indoor"], feats=["gman_glimpse"])
B.room("c0a0c_hazmat", "Tram Ride: Radioactive Materials Handling", "The tram crawls past a hazardous-materials area where workers in yellow suits move drums of radioactive waste behind leaded glass, and a rocket-shaped test rig towers over a pit.",
       after="Green light spills from a ruptured drum. The yellow-suited workers are gone.",
       map="c0a0c", tags=["transit", "indoor", "storage"])
B.room("c0a0d_descent", "Tram Ride: Descent", "The rail dips down a long shaft into the deep complex, past giant pipes and a hydroelectric turbine hall. The announcer recites the radiation-safety rules and the dangers of unauthorised experiments.",
       after="Steam billows through the shaft from ruptured pipes. The turbines have stopped.",
       map="c0a0d", tags=["transit", "indoor"])
B.room("c0a0e_platform", "Sector C Arrival Platform", "The tram comes to rest at a platform marked SECTOR C: TEST LABS AND CONTROL FACILITIES. A security guard taps on the window and opens the door for you, grinning: morning, Mr. Freeman, running a little late?",
       after="The Sector C platform is dark and littered with ceiling tiles. The security booth's glass has been smashed in.",
       map="c0a0e", tags=["transit", "indoor", "blackmesa"], feats=["platform_guard"], aliases=["platform", "sector c platform"])
B.chain(["c0a0_tram", "c0a0a_loading", "c0a0b_sectors", "c0a0c_hazmat", "c0a0d_descent", "c0a0e_platform"], "east", 3)

# ===========================================================================
# Anomalous Materials  (c1a0, c1a0d, c1a0a, c1a0b, c1a0c, c1a0e)
# ===========================================================================
B.set_chapter("Anomalous Materials")
B.room("c1a0_lobby", "Sector C Lobby", "The Sector C reception area: a curved security desk, a retinal scanner beside a heavy door, a Black Mesa logo on the wall and a computer system that, the guard complains, keeps crashing. Scientists drift past with coffee and clipboards and tell you you're late.",
       after="The lobby is wrecked. Ceiling tiles hang from their frames, the security desk is splashed with something dark, and the retinal scanner sparks uselessly. Somewhere, a scientist is screaming for help.",
       map="c1a0", tags=["blackmesa", "office", "indoor"], feats=["lobby_guard", "lobby_scientist", "retinal_scanner", "security_desk"],
       aliases=["lobby", "reception"], expand=locked(["office", "blackmesa"], chance=0.6))
B.room("c1a0_offices", "Sector C Office Corridor", "A corridor of offices and labs. Doors open onto rooms of whirring equipment; two scientists argue about a grant; a man in a lab coat pushes a cart of samples past you.",
       after="Bodies lie in the corridor. A vortigaunt's crackling green light flickers at one end.",
       map="c1a0", tags=["blackmesa", "office", "indoor"], feats=["sector_c_scientist", "bm_terminal"])
B.room("c1a0_breakroom", "Sector C Break Room", "The staff kitchen. A scientist is heating a casserole in the microwave; the dial says it will be a while. There's a coffee machine, a soda machine and a fridge with someone's name on everything.",
       after="The break room is a ruin. The microwave has exploded, painting the wall with casserole.",
       map="c1a0", tags=["blackmesa", "office", "indoor"], feats=["microwave", "vending_machine"])
B.room("c1a0_locker", "Sector C Locker Room", "Rows of grey lockers and benches. Yours has your name on it: FREEMAN. Through the far door, a glass-fronted storage room holds HEV suits on their charging racks.",
       after="Locker doors hang open. The suit storage room's glass is cracked, and an alarm drones overhead.",
       map="c1a0", tags=["blackmesa", "indoor"], feats=["freeman_locker", "hev_rack", "suit_charger", "health_charger"],
       aliases=["locker room", "lockers"])
B.room("c1a0d_elevator", "Freight Elevator to the Test Labs", "A big caged freight elevator descends to the Anomalous Materials test labs. A guard rides down with you, chatting about the experiment everybody's nervous about.",
       after="The elevator's cage is twisted; the cables groan with every movement.",
       map="c1a0d", tags=["blackmesa", "transit", "indoor"], aliases=["elevator", "freight elevator"])
B.room("c1a0a_labs", "Anomalous Materials Laboratories", "Lab corridors with windows onto clean rooms where scientists work behind glass. A sign points to the TEST CHAMBER. A scientist hurries past: the spectrometer's running hot, he says, but everything's within tolerance.",
       after="Lab windows have shattered outward. Something green and wet crawls in one of the clean rooms.",
       map="c1a0a", tags=["blackmesa", "lab", "indoor"], feats=["lab_scientist", "bm_terminal"], expand=locked(["lab", "blackmesa"], chance=0.6))
B.room("c1a0c_dorms", "Sector C Staff Corridor", "A side corridor of offices and a small staff lounge, where a television plays to an empty sofa.",
       after="The staff corridor is dark, the television showing static. Something moves in the lounge.",
       map="c1a0c", tags=["blackmesa", "office", "indoor"], feats=["vending_machine"])
B.room("c1a0b_decon", "Decontamination and Test Lab Approach", "A white decontamination corridor with blast doors and warning lights. Signs warn that the anti-mass spectrometer is in operation. The doors cycle open as you approach.",
       after="The decontamination doors are jammed half open, sparking.",
       map="c1a0b", tags=["blackmesa", "lab", "indoor"])
B.room("c1a0e_control", "Test Chamber Control Room", "Two senior scientists hunch over consoles, one balding and bespectacled, the other bearded. A big window overlooks the test chamber below. They assure you the sample is unusually pure and the system has never been pushed this far, and that nothing can possibly go wrong. Through the speaker, a colleague reports the beam is at one hundred and five percent.",
       after="The control room window has blown out. Consoles spark and smoke; a scientist lies under a fallen panel, pleading for someone to get help from the surface.",
       map="c1a0e", tags=["blackmesa", "lab", "indoor"], feats=["senior_scientists", "control_console"], aliases=["control room"])
B.room("c1a0e_chamber", "Anti-Mass Spectrometer Test Chamber", "A vast cylindrical chamber. The anti-mass spectrometer's emitters crackle with energy around a central beam. A sample cart sits on its track, ready to be pushed into the beam. The scientists talk you through it over the intercom: you have to push the sample in yourself.",
       after="The test chamber is a smoking ruin. The spectrometer's emitters are cracked and dead, and the floor is scorched in strange concentric rings.",
       map="c1a0e", tags=["blackmesa", "lab", "indoor"], feats=["anti_mass_spectrometer", "sample_cart"], aliases=["test chamber", "chamber"])
B.link("c0a0e_platform", "c1a0_lobby", "north")
B.link("c1a0_lobby", "c1a0_offices", "east")
B.link("c1a0_offices", "c1a0_breakroom", "north")
B.link("c1a0_offices", "c1a0_locker", "east")
B.link("c1a0_offices", "c1a0c_dorms", "south")
B.link("c1a0_locker", "c1a0d_elevator", "east")
B.link("c1a0d_elevator", "c1a0a_labs", "down")
B.link("c1a0a_labs", "c1a0b_decon", "east")
B.link("c1a0b_decon", "c1a0e_control", "east")
B.link("c1a0e_control", "c1a0e_chamber", "down", name="stairs to the chamber", aliases=["stairs"])

# ===========================================================================
# Unforeseen Consequences  (c1a1, c1a1a, c1a1b, c1a1c, c1a1d, c1a1f)
# ===========================================================================
B.set_chapter("Unforeseen Consequences")
B.room("c1a1_ruins", "Ruined Test Lab Corridors", "Everything is wrong. Lights strobe, alarms bray, fire crawls along cable trays. A scientist stumbles past screaming about the surface. Somewhere in the walls you hear scuttling.",
       map="c1a1", tags=["blackmesa", "lab", "indoor"] + POST, feats=["headcrab", "dead_scientist"])
B.room("c1a1_crowbar", "Collapsed Storage Room", "A storage room half-buried by a fallen ceiling. Shelving has toppled; a toolbox lies spilled across the floor, and among the tools gleams a red crowbar.",
       map="c1a1", tags=["blackmesa", "storage", "indoor"] + POST, feats=["crowbar", "supply_crate"], expand=locked(["maintenance", "storage"], chance=0.5, door=HATCH))
B.room("c1a1_lobby_ruin", "Sector C Lobby, Ruined", "You come back out into what's left of the Sector C lobby. The guard who greeted you lies dead behind the security desk; his 9mm pistol is still in its holster. A zombie in a lab coat groans by the retinal scanner.",
       map="c1a1", tags=["blackmesa", "office", "indoor"] + POST, feats=["zombie", "dead_guard_glock", "health_charger"])
B.room("c1a1a_shaft", "Elevator Shaft", "The main elevator shaft. As you watch, an elevator car full of scientists drops past, its cables snapping, and smashes into the bottom. Ladders run down the shaft wall.",
       map="c1a1a", tags=["blackmesa", "transit", "indoor"] + POST, feats=["headcrab"], aliases=["shaft"])
B.room("c1a1b_flooded", "Flooded Maintenance Level", "Water ankle-deep floods a maintenance level, and a severed power cable dangles in it, spitting sparks. The water is live. There is a power junction on a catwalk above.",
       map="c1a1b", tags=["blackmesa", "maintenance", "indoor", "water"] + POST, feats=["power_junction", "houndeye", "suit_charger"])
B.room("c1a1f_vents", "Ventilation Ducts", "You crawl through a tight sheet-metal air duct. Ahead, something chitters. A grille below looks down into a security office.",
       map="c1a1f", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["headcrab", "battery"])
B.room("c1a1c_security", "Security Office", "A security office with a bank of black-and-white monitors showing chaos from across the sector. A guard crouches behind the desk with a pistol, very glad to see you. A weapons locker stands open.",
       map="c1a1c", tags=["blackmesa", "office", "indoor"] + POST, feats=["uc_guard", "medkit", "ammo_box"], expand=locked(["office", "blackmesa"], chance=0.6))
B.room("c1a1d_offices", "Darkened Office Wing Entrance", "A corridor where the lights have died. Vortigaunts flicker in with green crackles. A sign points onward to the administrative offices.",
       map="c1a1d", tags=["blackmesa", "office", "indoor"] + POST, feats=["vortigaunt", "health_charger"])
B.link("c1a0e_chamber", "c1a1_ruins", "north", name="wrecked blast door", aliases=["blast door", "door"])
B.link("c1a1_ruins", "c1a1_crowbar", "east")
B.link("c1a1_ruins", "c1a1_lobby_ruin", "north")
B.link("c1a1_lobby_ruin", "c1a1a_shaft", "east")
B.link("c1a1a_shaft", "c1a1b_flooded", "down")
B.link("c1a1b_flooded", "c1a1f_vents", "east", name="air duct", aliases=["duct", "vent"])
B.link("c1a1f_vents", "c1a1c_security", "down", name="grille", aliases=["grille"])
B.link("c1a1c_security", "c1a1d_offices", "north")

# ===========================================================================
# Office Complex  (c1a2, c1a2a, c1a2b, c1a2c, c1a2d)
# ===========================================================================
B.set_chapter("Office Complex")
B.room("c1a2_reception", "Office Complex Reception", "The administrative wing's reception, with potted plants, a waiting area and a framed photo of the facility administrator. Water pours from a broken sprinkler.",
       map="c1a2", tags=["blackmesa", "office", "indoor"] + POST, feats=["zombie", "vending_machine", "bm_terminal"], expand=locked(["office"], chance=0.7))
B.room("c1a2_cubicles", "Cubicle Farm", "A maze of grey cubicle partitions. Monitors glow, phones ring with nobody to answer. Headcrabs move between the desks, and a sentry gun ticks somewhere ahead.",
       map="c1a2", tags=["blackmesa", "office", "indoor"] + POST, feats=["headcrab", "headcrab", "bm_memo", "supply_crate"])
B.room("c1a2a_kitchen", "Cafeteria and Kitchen", "A staff cafeteria with plastic trays still on the tables. Through the kitchen, a walk-in freezer stands ajar, frost spilling out, and something inside is moving among the hanging meat.",
       map="c1a2a", tags=["blackmesa", "office", "indoor"] + POST, feats=["zombie", "zombie", "vending_machine", "medkit"])
B.room("c1a2b_sentries", "Sentry Gun Corridor", "A long office corridor guarded by an automated sentry gun behind a tripwire laser. A scientist's body lies just past the beam: he didn't see it either.",
       map="c1a2b", tags=["blackmesa", "office", "indoor"] + POST, feats=["sentry_gun", "dead_scientist", "battery"])
B.room("c1a2c_flood", "Flooded Office Basement", "Stairs down to a basement of offices, knee-deep in water with live wiring trailing in it. A circuit breaker panel sits on a dry landing.",
       map="c1a2c", tags=["blackmesa", "office", "maintenance", "indoor", "water"] + POST, feats=["power_junction", "houndeye", "houndeye"])
B.room("c1a2d_storage", "Office Supply Storage", "Shelves of paper, toner and folding chairs. A guard has barricaded himself in, and gratefully joins you. A freight lift leads down toward the storage and loading areas.",
       map="c1a2d", tags=["blackmesa", "storage", "indoor"] + POST, feats=["office_guard", "supply_crate", "health_charger"], expand=locked(["storage", "office"], chance=0.6))
B.link("c1a1d_offices", "c1a2_reception", "north")
B.link("c1a2_reception", "c1a2_cubicles", "east")
B.link("c1a2_cubicles", "c1a2a_kitchen", "north")
B.link("c1a2_cubicles", "c1a2b_sentries", "east")
B.link("c1a2b_sentries", "c1a2c_flood", "down")
B.link("c1a2c_flood", "c1a2d_storage", "east")

# ===========================================================================
# We've Got Hostiles  (c1a3, c1a3a, c1a3b, c1a3c, c1a3d)
# ===========================================================================
B.set_chapter("We've Got Hostiles")
B.room("c1a3_execution", "Office Corridor: The Marines Arrive", "Through an office window you see soldiers in gas masks drag a scientist out and shoot him. The radio chatter is clear: no witnesses, and Freeman is priority. Help has arrived, and it isn't for you.",
       map="c1a3", tags=["blackmesa", "office", "military", "indoor"] + POST, feats=["hecu_marine", "dead_scientist"])
B.room("c1a3a_lift", "Freight Lift Shaft", "A huge freight lift, its platform halfway up a shaft lined with laser tripmines. Marines rappel down ropes from above.",
       map="c1a3a", tags=["blackmesa", "transit", "military", "indoor"] + POST, feats=["hecu_marine", "tripmine", "ammo_box"])
B.room("c1a3b_storage", "Bulk Storage Area", "A cavernous storage hall of crates on steel shelving, with forklifts and an overhead crane. Marines have set up a sentry gun on the catwalk, and one of them shouts that he's found you.",
       map="c1a3b", tags=["blackmesa", "storage", "military", "indoor"] + POST, feats=["hecu_marine", "sentry_gun", "supply_crate", "supply_crate", "mp5"],
       expand=locked(["storage", "maintenance"], chance=0.8))
B.room("c1a3c_pipes", "Pipe Gallery and Water Tunnels", "A tangle of huge pipes over a slow concrete channel. Bullsquids lurk at the water's edge. A grenade crate sits under a gantry.",
       map="c1a3c", tags=["blackmesa", "maintenance", "indoor", "water"] + POST, feats=["bullsquid", "grenade", "supply_crate"], expand=locked(["maintenance"], chance=0.6, door=HATCH))
B.room("c1a3d_silo_door", "Silo Access Blast Doors", "Massive blast doors mark the way to the rocket engine test facility. A warning sign advises that testing is in progress. Soldiers lie dead around a smoking crater.",
       map="c1a3d", tags=["blackmesa", "military", "indoor"] + POST, feats=["dead_marine", "health_charger"])
B.link("c1a2d_storage", "c1a3_execution", "down", name="freight lift", aliases=["lift"])
B.link("c1a3_execution", "c1a3a_lift", "east")
B.link("c1a3a_lift", "c1a3b_storage", "down")
B.link("c1a3b_storage", "c1a3c_pipes", "east")
B.link("c1a3c_pipes", "c1a3d_silo_door", "east")

# ===========================================================================
# Blast Pit  (c1a4, c1a4k, c1a4b, c1a4f, c1a4d, c1a4e, c1a4i, c1a4g, c1a4j)
# ===========================================================================
B.set_chapter("Blast Pit")
TENT = ["tentacle_zone"]
B.room("c1a4_catwalk", "Rocket Test Silo: Upper Catwalk", "A circular catwalk around the rim of an immense silo built to test rocket engines. Far below, three gigantic tentacles rise from the pit, beaked heads twitching toward every sound. A dying scientist whispers that the only way to kill them is to fire the engine at the bottom of the silo, and that needs fuel, oxygen and power.",
       map="c1a4", tags=["blackmesa", "indoor"] + POST + TENT, feats=["tentacle", "dying_scientist", "grenade"], aliases=["silo", "catwalk"])
B.room("c1a4k_floor", "Rocket Test Silo: Floor", "The bottom of the silo, littered with crushed equipment. The tentacles are right here, hammering the floor wherever they hear a footstep. Doors lead off to the fuel, oxygen and power systems.",
       map="c1a4k", tags=["blackmesa", "indoor"] + POST + TENT, feats=["tentacle", "ammo_box"], aliases=["silo floor"])
B.room("c1a4b_power", "Generator Plant", "A generator room reached through a long corridor and a ladder. A huge switch on the wall controls power to the silo. The room is crawling with houndeyes.",
       map="c1a4b", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["silo_power_switch", "houndeye", "houndeye", "suit_charger"])
B.room("c1a4d_oxygen", "Oxygen Pumping Station", "A pump room of tanks stencilled O2, with a big valve wheel and a ladder from a flooded tunnel. Bullsquids nest in the overflow.",
       map="c1a4d", tags=["blackmesa", "maintenance", "indoor", "water"] + POST, feats=["oxygen_valve", "bullsquid", "medkit"])
B.room("c1a4f_fuel", "Fuel Pump Room", "Fuel lines snake into a pump room. The pumps are off; the controls are on a gantry above a pool of something that smells of kerosene. A pipeline duct leads back to the silo.",
       map="c1a4f", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["fuel_pump_switch", "zombie", "battery"], expand=locked(["maintenance"], chance=0.5, door=HATCH))
B.room("c1a4e_tunnels", "Silo Service Tunnels", "Narrow service tunnels ring the silo, with ladders and pipe runs and a train-track underpass. Water drips everywhere.",
       map="c1a4e", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["headcrab", "supply_crate"])
B.room("c1a4i_control", "Engine Test Control Room", "A control room overlooking the silo through thick glass. A big red button is labelled ENGINE TEST - FIRE. Gauges for fuel, oxygen and power sit beside it.",
       map="c1a4i", tags=["blackmesa", "lab", "indoor"] + POST, feats=["engine_fire_button", "health_charger"], aliases=["control room"])
B.room("c1a4g_exhaust", "Silo Exhaust Shaft", "Below the silo floor, the engine's exhaust shaft drops away into the dark. Where the tentacles were rooted there is now a hole into the levels below.",
       map="c1a4g", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["houndeye"])
B.room("c1a4j_underpass", "Rail Underpass", "A low tunnel beneath the silo complex, where the track for the power plant's service trains begins. Signs point toward the POWER FACILITY.",
       map="c1a4j", tags=["blackmesa", "transit", "indoor"] + POST, feats=["zombie", "ammo_box"])
B.link("c1a3d_silo_door", "c1a4_catwalk", "east", name="blast doors", aliases=["blast doors", "doors"])
B.link("c1a4_catwalk", "c1a4k_floor", "down", name="ladder", aliases=["ladder"])
B.link("c1a4k_floor", "c1a4b_power", "north")
B.link("c1a4k_floor", "c1a4d_oxygen", "east")
B.link("c1a4k_floor", "c1a4f_fuel", "west")
B.link("c1a4_catwalk", "c1a4i_control", "east")
B.link("c1a4b_power", "c1a4e_tunnels", "east")
B.link("c1a4e_tunnels", "c1a4d_oxygen", "south")
B.link("c1a4k_floor", "c1a4g_exhaust", "down", name="exhaust shaft", aliases=["shaft", "hole"],
       cond={"flag": "hl_tentacles_dead"}, blocked="The tentacles are rooted down there. Nothing goes down that shaft while they live.",
       solve=[["goto", "hl/c1a4b_power"], ["do", "use power switch"], ["goto", "hl/c1a4d_oxygen"], ["do", "turn valve"],
              ["goto", "hl/c1a4f_fuel"], ["do", "use fuel pump controls"], ["goto", "hl/c1a4i_control"], ["do", "push button"]])
B.link("c1a4g_exhaust", "c1a4j_underpass", "east")

# ===========================================================================
# Power Up  (c2a1, c2a1a, c2a1b)
# ===========================================================================
B.set_chapter("Power Up")
B.room("c2a1_tracks", "Power Facility Rail Yard", "Rail tracks lead into a cavernous power facility. A security guard, pinned behind a train car, tells you there's something huge out there, and the electrified rails are dead.",
       map="c2a1", tags=["blackmesa", "transit", "indoor"] + POST, feats=["powerup_guard", "health_charger"], expand=locked(["transit", "maintenance"], chance=0.6))
B.room("c2a1_garg", "Gargantua's Hunting Ground", "A huge open yard of rails and catwalks. A gargantua stalks here, flame jets sputtering from its arms, armour shrugging off bullets. In the middle of the yard is a stretch of high-voltage rail, dead for now.",
       map="c2a1", tags=["blackmesa", "transit", "indoor", "garg_trap"] + POST, feats=["gargantua", "dead_guard"], aliases=["yard"])
B.room("c2a1a_generator", "Generator Room", "Up a ladder and through a maze of ducts, the power generator itself: a turbine the size of a house, and on the wall, the switches that would put power back on the rails.",
       map="c2a1a", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["generator_switch", "houndeye", "suit_charger"])
B.room("c2a1b_substation", "Electrical Substation", "A substation of transformers behind chain-link, where cable trays lead to the rail power system. Zombies shamble between the cabinets.",
       map="c2a1b", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["zombie", "zombie", "battery", "grenade"], expand=locked(["maintenance"], chance=0.6, door=HATCH))
B.link("c1a4j_underpass", "c2a1_tracks", "east")
B.link("c2a1_tracks", "c2a1_garg", "north")
B.link("c2a1_tracks", "c2a1b_substation", "east")
B.link("c2a1b_substation", "c2a1a_generator", "up", name="ladder", aliases=["ladder"])

# ===========================================================================
# On a Rail  (c2a2 ... c2a2h)
# ===========================================================================
B.set_chapter("On a Rail")
B.room("c2a2_rail_yard", "Rail Switching Yard", "A maintenance train on the electrified rail sits waiting, its controls glowing. Tracks fan out into tunnels in every direction, and a signal box controls the points.",
       map="c2a2", tags=["blackmesa", "transit", "indoor"] + POST, feats=["rail_car", "hecu_marine", "ammo_box"])
B.room("c2a2a_tunnels", "Rail Tunnels", "You ride the rail car through long tunnels. Marines have set up sentry guns at the junctions, and the track is blocked by a fallen gate here and there.",
       map="c2a2a", tags=["blackmesa", "transit", "indoor", "military"] + POST, feats=["sentry_gun", "hecu_marine", "supply_crate"], expand=locked(["transit", "storage"], chance=0.6))
B.room("c2a2b_junction", "Track Junction and Signal Box", "A junction where you must climb into a signal box and throw the points to send the car down the right line. Houndeyes yap in the dark beneath the track.",
       map="c2a2b1", tags=["blackmesa", "transit", "indoor"] + POST, feats=["houndeye", "houndeye", "health_charger"])
B.room("c2a2d_depot", "Rail Depot and Armoury", "A depot of rail cars and cargo containers that the Marines have turned into a fortified position: sandbags, crates and a lot of guns.",
       map="c2a2d", tags=["blackmesa", "transit", "military", "indoor"] + POST, feats=["hecu_marine", "hecu_marine", "supply_crate", "shotgun"])
B.room("c2a2e_launch_ctrl", "Rocket Launch Control", "A control room overlooking a satellite launch silo. A scientist tells you the Lambda team needs this satellite launched to deliver a payload. The launch console waits for someone to arm it.",
       map="c2a2e", tags=["blackmesa", "lab", "indoor"] + POST, feats=["launch_console", "launch_scientist", "suit_charger"])
B.room("c2a2f_silo", "Satellite Launch Silo", "The silo floor, where a slender rocket stands under scaffolding, its satellite fairing open at the top.",
       map="c2a2f", tags=["blackmesa", "lab", "indoor"] + POST, feats=["satellite_rocket", "battery"])
B.room("c2a2h_terminus", "Rail Terminus", "The rail line ends at a buffer stop before a set of doors marked AQUATIC RESEARCH. The tracks behind you are a long way down.",
       map="c2a2h", tags=["blackmesa", "transit", "indoor"] + POST, feats=["zombie", "medkit"])
B.link("c2a1_garg", "c2a2_rail_yard", "east", name="the electrified rail", aliases=["rail", "rails"],
       cond={"flag": "hl_power_on"}, blocked="The rail car won't move with the power off. The generator needs to come back on.",
       solve=[["goto", "hl/c2a1a_generator"], ["do", "use generator switch"]])
B.link("c2a2_rail_yard", "c2a2a_tunnels", "east", 3)
B.link("c2a2a_tunnels", "c2a2b_junction", "east", 3)
B.link("c2a2b_junction", "c2a2d_depot", "east", 3)
B.link("c2a2d_depot", "c2a2e_launch_ctrl", "north")
B.link("c2a2e_launch_ctrl", "c2a2f_silo", "down")
B.link("c2a2d_depot", "c2a2h_terminus", "east", 3)

# ===========================================================================
# Apprehension  (c2a3, c2a3a ... c2a3e)
# ===========================================================================
B.set_chapter("Apprehension")
B.room("c2a3_tank", "Aquatic Research Tank", "An enormous water tank with a catwalk across it and a submerged cage. Something huge circles in the water: an ichthyosaur, released from its pen.",
       map="c2a3", tags=["blackmesa", "lab", "indoor", "water"] + POST, feats=["ichthyosaur", "medkit"], aliases=["tank"])
B.room("c2a3a_cage", "Submerged Cage and Research Platform", "A research platform over the tank with a shark cage hanging by a cable. Lab equipment and fish food on the bench. Somebody was very brave or very stupid here.",
       map="c2a3a", tags=["blackmesa", "lab", "indoor", "water"] + POST, feats=["crossbow", "dead_scientist"])
B.room("c2a3b_labs", "Aquatic Research Laboratories", "Labs full of empty aquariums, sample freezers and a vending machine. Marines are sweeping the corridors.",
       map="c2a3b", tags=["blackmesa", "lab", "indoor", "military"] + POST, feats=["hecu_marine", "vending_machine", "bm_terminal"], expand=locked(["lab"], chance=0.6))
B.room("c2a3d_maintenance", "Water Treatment Maintenance", "Pump rooms and settling tanks, where bullsquids bob in the scum and leeches swirl in the deep water.",
       map="c2a3d", tags=["blackmesa", "maintenance", "indoor", "water"] + POST, feats=["bullsquid", "leech", "supply_crate"])
B.room("c2a3e_ambush", "Dark Corridor", "A dark corridor that ends at a door. As you reach for it the lights snap on, and soldiers step out of the shadows on every side.",
       map="c2a3e", tags=["blackmesa", "military", "indoor", "story_skip"] + POST, aliases=["corridor"],
       enter=[{"if": {"not": {"flag": "hl_captured"}}, "then": [{"macro": "hl_capture"}]}])
B.link("c2a2h_terminus", "c2a3_tank", "east")
B.link("c2a3_tank", "c2a3a_cage", "up")
B.link("c2a3_tank", "c2a3b_labs", "east")
B.link("c2a3b_labs", "c2a3d_maintenance", "south")
B.link("c2a3b_labs", "c2a3e_ambush", "east")

# ===========================================================================
# Residue Processing  (c2a4, c2a4a, c2a4b, c2a4c)
# ===========================================================================
B.set_chapter("Residue Processing")
B.room("c2a4_compactor", "Trash Compactor", "You wake up in a garbage compactor, head pounding, your weapons gone. The walls grind toward each other. A ladder in the corner is your only hope. Beside it, someone has dumped a crate of confiscated gear.",
       map="c2a4", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["confiscated_crate"], aliases=["compactor"])
B.room("c2a4a_conveyors", "Conveyor Lines", "Conveyor belts carry refuse past grinding rollers and stamping presses. You have to ride the belts and jump the crushers.",
       map="c2a4a", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["headcrab", "battery"], expand=locked(["maintenance", "storage"], chance=0.6, door=HATCH))
B.room("c2a4b_vats", "Waste Processing Vats", "Vats of bubbling green sludge under catwalks. A pipe across the room drips something that eats through steel.",
       map="c2a4b", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["bullsquid", "houndeye", "medkit"])
B.room("c2a4c_grinders", "Grinder Room", "A room of giant rotating grinders that turn waste into sludge, and anything else into worse. A control booth sits above.",
       map="c2a4c", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["zombie", "health_charger"])
B.link("c2a4_compactor", "c2a4a_conveyors", "up", name="ladder", aliases=["ladder"])
B.link("c2a4a_conveyors", "c2a4b_vats", "east")
B.link("c2a4b_vats", "c2a4c_grinders", "east")
B.link("c2a3e_ambush", "c2a4_compactor", "down", name="garbage chute", aliases=["chute"], back="out", back_name="garbage chute")

# ===========================================================================
# Questionable Ethics  (c2a4d, c2a4e, c2a4f, c2a4g)
# ===========================================================================
B.set_chapter("Questionable Ethics")
B.room("c2a4d_entrance", "Biological Research Entrance", "Clean white corridors again, and a sign: ADVANCED BIOLOGICAL RESEARCH. Scientists cower in an office, and one begs you to escort them to safety.",
       map="c2a4d", tags=["blackmesa", "lab", "indoor"] + POST, feats=["qe_scientist", "health_charger", "suit_charger"])
B.room("c2a4e_laser", "Laser Laboratory", "A lab built around a huge industrial laser on a gantry. The scientists say they can use it to cut through to the next section, if somebody stands very still in the right place, which is you.",
       map="c2a4e", tags=["blackmesa", "lab", "indoor"] + POST, feats=["big_laser", "hecu_marine", "bm_memo"])
B.room("c2a4f_specimens", "Specimen Holding", "Holding cells with thick glass, each containing an alien specimen: houndeyes, a bullsquid, and an alien grunt that has just smashed its way out.",
       map="c2a4f", tags=["blackmesa", "lab", "indoor"] + POST, feats=["alien_grunt", "houndeye", "snark_nest"], expand=locked(["lab"], chance=0.7))
B.room("c2a4g_tau", "Prototype Weapons Lab", "A lab where a prototype weapon sits on a test stand: the tau cannon, still connected to its power supply. A sign reads DO NOT REMOVE.",
       map="c2a4g", tags=["blackmesa", "lab", "indoor"] + POST, feats=["gauss", "dead_scientist", "battery"])
B.room("c2a4g_surgery", "Surgical Laboratory", "An operating theatre where an alien lies strapped to a table, dissected. Instruments still sit on the tray. A scientist says it's for science. You don't believe him.",
       map="c2a4g", tags=["blackmesa", "lab", "indoor"] + POST, feats=["zombie", "medkit"])
B.link("c2a4c_grinders", "c2a4d_entrance", "east")
B.link("c2a4d_entrance", "c2a4e_laser", "north")
B.link("c2a4e_laser", "c2a4f_specimens", "east")
B.link("c2a4f_specimens", "c2a4g_tau", "north")
B.link("c2a4f_specimens", "c2a4g_surgery", "east")

# ===========================================================================
# Surface Tension  (c2a5, c2a5w, c2a5x, c2a5a ... c2a5g)
# ===========================================================================
B.set_chapter("Surface Tension")
SURF = ["surface", "outdoor", "desert"]
B.room("c2a5_spillway", "Dam Spillway", "Daylight. You emerge onto a concrete spillway below a huge dam. The desert sun is blinding after so long underground, and an ichthyosaur thrashes in the reservoir behind.",
       map="c2a5", tags=["blackmesa"] + SURF + POST + ["water"], feats=["ichthyosaur", "supply_crate"], expand=outdoors(["surface"], chance=0.6))
B.room("c2a5w_dam", "Top of the Dam", "The dam's crest road, with a view over the canyons and the facility's smoking chimneys. A Marine helicopter swings around the cliffs.",
       map="c2a5w", tags=["blackmesa"] + SURF + POST, feats=["apache", "dead_marine"])
B.room("c2a5x_cliffs", "Canyon Cliffs", "A trail along sheer red cliffs, with snipers in the rocks above and Marines moving in pairs below. The wind smells of hot stone and jet fuel.",
       map="c2a5x", tags=["blackmesa"] + SURF + POST + ["military"], feats=["hecu_marine", "hecu_marine", "ammo_box"], expand=outdoors(["surface", "military"]))
B.room("c2a5a_crash", "Osprey Crash Site", "The burning wreck of a V-22 Osprey lies in a canyon, its rotors folded like broken wings. Bodies and cargo are scattered around it, and so are rockets.",
       map="c2a5a", tags=["blackmesa"] + SURF + POST + ["military"], feats=["osprey_wreck", "rpg", "dead_marine"], expand=outdoors(["surface"]))
B.room("c2a5b_minefield", "Minefield", "A flat stretch of sand marked with warning signs, and craters where others found the mines. A sentry gun watches from a sandbagged post.",
       map="c2a5b", tags=["blackmesa"] + SURF + POST + ["military"], feats=["sentry_gun", "minefield"])
B.room("c2a5c_compound", "HECU Command Compound", "A fenced military compound of tents and trucks around a radio post. A gargantua has broken in through the fence, and the Marines are losing.",
       map="c2a5c", tags=["blackmesa"] + SURF + POST + ["military"], feats=["airstrike_radio", "hecu_marine", "supply_crate", "supply_crate"],
       expand=outdoors(["military", "surface"]))
B.room("c2a5d_courtyard", "Facility Courtyard", "A walled courtyard between facility buildings. The gargantua stalks here among wrecked trucks, setting everything alight.",
       map="c2a5d", tags=["blackmesa"] + SURF + POST + ["garg_courtyard"], feats=["gargantua"])
B.room("c2a5e_garage", "Parking Garage", "A multi-storey car park cut into the cliff. Cars sit abandoned; one's alarm wails endlessly. Marines hold the ramps.",
       map="c2a5e", tags=["blackmesa", "indoor", "military"] + POST, feats=["hecu_marine", "medkit", "battery"], expand=locked(["storage", "maintenance"], chance=0.6))
B.room("c2a5f_tunnel", "Drainage Tunnel", "A storm drain big enough for a truck, leading back underground. Graffiti on the wall says, in Marine shorthand, that someone owes someone twenty bucks.",
       map="c2a5f", tags=["blackmesa", "maintenance", "indoor"] + POST, feats=["bullsquid", "ammo_box"])
B.room("c2a5g_bridge", "Canyon Bridge", "A rickety bridge across a gorge. Tanks rumble on the far side and an Apache patrols the gap. The way forward leads down into the earth again.",
       map="c2a5g", tags=["blackmesa"] + SURF + POST + ["military"], feats=["hecu_marine", "grenade"], expand=outdoors(["surface", "military"]))
B.link("c2a4g_surgery", "c2a5_spillway", "up", name="stairs to the surface", aliases=["stairs", "surface"])
B.link("c2a5_spillway", "c2a5w_dam", "up")
B.link("c2a5w_dam", "c2a5x_cliffs", "north", 3)
B.link("c2a5x_cliffs", "c2a5a_crash", "east", 3)
B.link("c2a5a_crash", "c2a5b_minefield", "north", 3)
B.link("c2a5b_minefield", "c2a5c_compound", "north", 3)
B.link("c2a5c_compound", "c2a5d_courtyard", "east")
B.link("c2a5c_compound", "c2a5e_garage", "north")
B.link("c2a5e_garage", "c2a5f_tunnel", "down")
B.link("c2a5f_tunnel", "c2a5g_bridge", "east", 3)

# ===========================================================================
# Forget About Freeman!  (c3a1, c3a1a, c3a1b)
# ===========================================================================
B.set_chapter("Forget About Freeman!")
B.room("c3a1_sewer", "Sewer Outflow", "A sewer outflow beneath the canyon. Over the radio, a Marine commander orders his men to pull out: forget about Freeman, he says.",
       map="c3a1", tags=["blackmesa", "maintenance", "indoor", "water"] + POST, feats=["bullsquid", "zombie_soldier", "medkit"])
B.room("c3a1a_yard", "Retreat Staging Yard", "A yard of concrete and razor wire where the Marines are trying to withdraw. Alien grunts are cutting them to pieces, and a tank sits burning by the gate.",
       map="c3a1a", tags=["blackmesa"] + SURF + POST + ["military"], feats=["alien_grunt", "hecu_marine", "tank_wreck", "supply_crate"],
       expand=outdoors(["surface", "military"]))
B.room("c3a1b_bunker", "Tank Bunker", "A concrete bunker where an Abrams tank still works its turret, firing at anything that moves. A trench leads around behind it. The sign on the bunker door reads LAMBDA COMPLEX.",
       map="c3a1b", tags=["blackmesa", "military", "indoor"] + POST, feats=["hecu_marine", "satchel", "battery"])
B.link("c2a5g_bridge", "c3a1_sewer", "down")
B.link("c3a1_sewer", "c3a1a_yard", "north")
B.link("c3a1a_yard", "c3a1b_bunker", "east")

# ===========================================================================
# Lambda Core  (c3a2, c3a2a ... c3a2f)
# ===========================================================================
B.set_chapter("Lambda Core")
B.room("c3a2_entrance", "Lambda Complex Entrance", "The Lambda Complex: a huge white lambda symbol over a security checkpoint. Scientists inside wave you through. They've been waiting for you.",
       map="c3a2", tags=["blackmesa", "lab", "indoor", "lambda"] + POST, feats=["lambda_scientist", "health_charger", "suit_charger"], aliases=["lambda complex"])
B.room("c3a2a_coolant", "Reactor Coolant Tunnels", "The reactor's coolant tunnels are flooded to the ceiling. Pumps on two levels have to be started to drain them, and things live in the water.",
       map="c3a2a", tags=["blackmesa", "maintenance", "indoor", "water", "lambda"] + POST, feats=["coolant_pump", "leech", "ichthyosaur"])
B.room("c3a2b_teleports", "Teleport Test Labs", "A warren of teleport labs, each with a glowing pad that flings you somewhere else in the complex. Only one sequence leads where you want to go.",
       map="c3a2b", tags=["blackmesa", "lab", "indoor", "lambda"] + POST, feats=["teleport_pad", "vortigaunt", "controller"], expand=locked(["lab"], chance=0.7))
B.room("c3a2c_longjump", "Advanced Mobility Lab", "A lab with a test track, a padded wall and an HEV harness on a stand. Fitted to it is a long jump module.",
       map="c3a2c", tags=["blackmesa", "lab", "indoor", "lambda"] + POST, feats=["long_jump", "lambda_scientist_2"])
B.room("c3a2d_reactor", "Lambda Reactor Core", "The reactor itself: a towering cylinder of humming machinery in a vast shaft, with walkways spiralling up its sides and the crackle of teleport fields at every level.",
       map="c3a2d", tags=["blackmesa", "lab", "indoor", "lambda"] + POST, feats=["controller", "alien_grunt", "health_charger"], aliases=["reactor", "core"])
B.room("c3a2f_portal", "Portal Chamber", "At the top of the reactor, scientists stand at consoles around a chamber where a portal swirls open: green-white light, and beyond it, a landscape of floating islands. They tell you their satellite delivery made this possible, and that you must go through.",
       map="c3a2f", tags=["blackmesa", "lab", "indoor", "lambda"] + POST, feats=["lambda_portal", "portal_scientists"], aliases=["portal chamber"])
B.link("c3a1b_bunker", "c3a2_entrance", "east")
B.link("c3a2_entrance", "c3a2a_coolant", "down")
B.link("c3a2a_coolant", "c3a2b_teleports", "east")
B.link("c3a2b_teleports", "c3a2c_longjump", "north", name="teleport pad", aliases=["pad", "teleport"])
B.link("c3a2b_teleports", "c3a2d_reactor", "east")
B.link("c3a2d_reactor", "c3a2f_portal", "up")

# ===========================================================================
# Xen  (c4a1)
# ===========================================================================
B.set_chapter("Xen")
XEN = ["xen", "alien", "outdoor"]
B.room("c4a1_arrival", "Xen: Arrival", "You fall out of the portal onto spongy alien ground. Islands of rock float in a green-violet void, connected by nothing at all. The remains of an HEV-suited researcher lie nearby, along with his equipment.",
       map="c4a1", tags=XEN, feats=["xen_researcher", "battery", "xen_light"], aliases=["xen"], expand=outdoors(["xen"], name="drifting rock"))
B.room("c4a1_pool", "Xen: Healing Pool", "A grotto around a pool of glowing water. Light-stalks retract as you approach. Houndeyes drink at the far edge.",
       map="c4a1", tags=XEN, feats=["healing_pool", "houndeye", "xen_light"])
B.room("c4a1_islands", "Xen: Island Chain", "A chain of islands linked by jump pads, organic launch pads that puff you through the air. Below, the void. Above, the void.",
       map="c4a1", tags=XEN, feats=["jump_pad", "headcrab"], expand=outdoors(["xen"], name="far island"))
B.link("c3a2f_portal", "c4a1_arrival", "in", name="the portal", aliases=["portal", "rift"], back_name="rift back to Black Mesa")
B.link("c4a1_arrival", "c4a1_pool", "east")
B.link("c4a1_pool", "c4a1_islands", "north", name="jump pad", aliases=["pad"])

# ===========================================================================
# Gonarch's Lair  (c4a2, c4a2a, c4a2b)
# ===========================================================================
B.set_chapter("Gonarch's Lair")
B.room("c4a2_web", "Gonarch's Web", "A cavern strung with sticky webbing, littered with bones and egg cases. Something enormous stalks above, dropping baby headcrabs as it moves.",
       map="c4a2", tags=XEN + ["cave"], feats=["gonarch", "baby_headcrab"])
B.room("c4a2a_pit", "The Long Fall", "The web gives way and you plunge down a shaft of fleshy rock into a lower chamber. The Gonarch comes after you.",
       map="c4a2a", tags=XEN + ["cave"], feats=["baby_headcrab", "medkit"])
B.room("c4a2b_exit", "Gonarch's Pit", "The bottom of the lair, a bowl of rock where the Gonarch makes its last stand. A crack in the wall glows with teleport light.",
       map="c4a2b", tags=XEN + ["cave"], feats=["xen_light", "battery"])
B.link("c4a1_islands", "c4a2_web", "east", 3)
B.link("c4a2_web", "c4a2a_pit", "down")
B.link("c4a2a_pit", "c4a2b_exit", "down")

# ===========================================================================
# Interloper  (c4a1a ... c4a1f)
# ===========================================================================
B.set_chapter("Interloper")
B.room("c4a1a_caves", "Xen Caverns", "Organic tunnels lit by veins of light, where vortigaunts in shackles work on something that pulses.",
       map="c4a1a", tags=XEN + ["cave"], feats=["vortigaunt", "vortigaunt", "xen_glyph"])
B.room("c4a1b_factory", "Alien Grunt Factory", "A vast industrial hive where alien grunts are grown in vats, assembled on conveyors and marched out by the hundred. Controllers float overhead, directing it all.",
       map="c4a1b", tags=["xen", "alien", "indoor"], feats=["alien_grunt", "controller", "hivehand"], aliases=["factory"])
B.room("c4a1c_conveyors", "Factory Conveyors", "Conveyors of half-formed bodies, chutes of slime, and crushers. Vortigaunts work the machinery, collars glowing.",
       map="c4a1c", tags=["xen", "alien", "indoor"], feats=["vortigaunt", "medkit"])
B.room("c4a1d_tower", "Ascent Through the Hive", "A climb up the hive's interior on ledges and platforms that drift, toward a portal at the top.",
       map="c4a1d", tags=["xen", "alien", "indoor"], feats=["controller", "battery"])
B.room("c4a1f_teleport", "Hive Teleporter", "A great teleporter at the top of the hive, powered by Xen crystals, linked to the Nihilanth's lair.",
       map="c4a1f", tags=["xen", "alien", "indoor"], feats=["xen_glyph", "health_charger_xen"])
B.link("c4a2b_exit", "c4a1a_caves", "east", name="glowing crack", aliases=["crack"])
B.link("c4a1a_caves", "c4a1b_factory", "east")
B.link("c4a1b_factory", "c4a1c_conveyors", "north")
B.link("c4a1c_conveyors", "c4a1d_tower", "up")
B.link("c4a1d_tower", "c4a1f_teleport", "up")

# ===========================================================================
# Nihilanth  (c4a3)
# ===========================================================================
B.set_chapter("Nihilanth")
B.room("c4a3_chamber", "Nihilanth's Chamber", "A cavernous hollow in a floating mountain, its walls lined with teleport portals. The Nihilanth hangs in the centre, colossal, flanked by golden crystals that feed it. Its voice is inside your head.",
       map="c4a3", tags=["xen", "alien", "indoor"], feats=["nihilanth", "healing_crystal", "healing_crystal", "healing_crystal"], aliases=["chamber"])
B.link("c4a1f_teleport", "c4a3_chamber", "in", name="the teleporter", aliases=["teleporter", "portal"])

# ===========================================================================
# Endgame  (c5a1)
# ===========================================================================
B.set_chapter("Endgame")
B.room("c5a1_gman", "Between Worlds", "Darkness, then flickers of places: Xen, Black Mesa, somewhere else. And the man in the suit, standing in front of you, completely at ease.",
       map="c5a1", tags=["indoor", "void", "story_skip"], feats=["gman"], aliases=["void"])
B.link("c5a1_gman", "c4a1_arrival", "out", name="the way back", aliases=["back", "way back"], oneway=True)

# ===========================================================================
# Hazard Course  (t0a0 ...)  - its own area
# ===========================================================================
HZ = ["blackmesa", "training", "indoor"]
B.set_chapter("Hazard Course")
B.room(H + "t0a0_start", "Hazard Course: Welcome", "A grey training hall. A holographic projection of a balding scientist welcomes you to the Hazardous Environment Course and explains that he will teach you the HEV suit's basic functions.",
       map="t0a0", tags=HZ, feats=["holo_instructor"])
B.room(H + "t0a0a_moving", "Hazard Course: Movement", "Ramps, crates and a low duct to crawl through, each with a hologram demonstrating how.", map="t0a0a", tags=HZ, feats=["supply_crate"])
B.room(H + "t0a0b_jumps", "Hazard Course: Jumping and Ladders", "Platforms over a padded pit, a ladder up a wall, and a long jump you'll make on the third try.", map="t0a0b", tags=HZ)
B.room(H + "t0a0b1_water", "Hazard Course: Swimming", "A deep pool with a submerged tunnel and a timer: hold your breath and swim.", map="t0a0b1", tags=HZ + ["water"])
B.room(H + "t0a0c_charge", "Hazard Course: Health and Suit", "A room with a health charger, an HEV charger and a battery on a stand, and a hologram explaining all three.",
       map="t0a0c", tags=HZ, feats=["health_charger", "suit_charger", "battery", "medkit"])
B.room(H + "t0a0d_range", "Hazard Course: Firing Range", "A shooting range with paper targets and a rack of training weapons. At the end, a hologram congratulates you on completing the course.",
       map="t0a0d", tags=HZ, feats=["glock", "training_target"])
B.chain([H + "t0a0_start", H + "t0a0a_moving", H + "t0a0b_jumps", H + "t0a0b1_water", H + "t0a0c_charge", H + "t0a0d_range"], "north")

# ===========================================================================
# Features specific to this campaign
# ===========================================================================
F = B.section("features")
F.update({
    "tram_announcer": {"extends": ["scenery"], "name": "tram announcer", "aliases": ["announcer", "speaker", "voice"],
        "appearance": False, "description": "A recorded voice from a speaker grille.",
        "actions": {"listen": ["#tram_announcement#"], "talk": ["The announcer is a recording. It carries on regardless."]}},
    "tram_window": {"extends": ["scenery"], "name": "tram window", "aliases": ["window", "windows"], "appearance": False,
        "description": "Through the scratched plexiglass, Black Mesa slides past."},
    "robot_arm": {"extends": ["scenery"], "name": "robotic arm", "aliases": ["arm", "robot", "robotic arm"],
        "appearance": "A yellow robotic arm swings a pallet past the tram.", "description": "Hydraulic, enormous and indifferent."},
    "gman_glimpse": {"extends": ["scenery"], "name": "man in a blue suit", "aliases": ["man", "suit", "g-man", "gman", "man in the suit"],
        "appearance": False, "description": "He's gone before you can get a proper look. You feel, unreasonably, that he was looking at you."},
    "platform_guard": {"extends": ["security_guard"], "name": "Officer #bm_surname#",
        "description": "A cheerful guard in a blue shirt who seems to know who you are.",
        "actions": {"talk": [{"do": ["\"Morning, Mr. Freeman. They're waiting for you upstairs in the test lab. Better hurry.\""]}]}},
    "lobby_guard": {"extends": ["security_guard"], "name": "Officer #bm_surname#", "important": False,
        "appearance": "{self.Name} sits behind the security desk, hitting the side of his monitor.",
        "description": "He's been fighting with the computer all morning, he says, and the computer is winning.",
        "actions": {"talk": [{"if": {"flag": "hl_cascade"}, "do": ["\"Freeman? You're alive! Get to the surface, I'll hold the door!\""]},
                             {"do": ["\"Hey, Mr. Freeman. The system's down again, so I'll scan you through. Good luck in there today.\""]}]}},
    "lobby_scientist": {"extends": ["scientist"], "appearance": "{self.Name} paces by the reception desk, looking at a watch.",
        "actions": {"talk": [{"if": {"flag": "hl_cascade"}, "do": ["\"What have you done? What have we done?\""]},
                             {"do": ["\"Gordon! You're late. The administrator wants the test run before noon. Suit up, quickly.\""]}]}},
    "retinal_scanner": {"extends": ["scenery"], "name": "retinal scanner", "aliases": ["scanner", "retinal scanner"],
        "appearance": False, "description": "A wall-mounted retinal scanner, its lens blinking green.",
        "actions": {"use": ["A beam sweeps your eye. ACCESS GRANTED, says the panel."]}},
    "security_desk": {"extends": ["scenery", "surface"], "name": "security desk", "aliases": ["desk"], "appearance": False,
        "description": "A curved reception desk with a monitor, a phone and a sign-in book.", "features": ["bm_memo"]},
    "lab_scientist": {"extends": ["scientist"], "appearance": "{self.Name} hurries past with a clipboard.",
        "actions": {"talk": [{"if": {"flag": "hl_cascade"}, "do": ["\"The spectrometer... it was running hot, I said so! Nobody listens!\""]},
                             {"do": ["\"The spectrometer's running hot, but everything's within tolerance. Probably.\""]}]}},
    "sector_c_scientist": {"extends": ["scientist"], "appearance": "{self.Name} argues with a colleague about a grant proposal."},
    "microwave": {"extends": ["scenery"], "name": "microwave", "aliases": ["microwave", "casserole", "oven"],
        "appearance": [{"if": {"flag": "hl_microwave"}, "text": "The microwave's door is blown off, and casserole covers the wall."},
                       {"text": "A microwave hums on the counter, a casserole turning inside."}],
        "description": "Somebody's lunch. It has a long way to go.",
        "actions": {"use": [{"if": {"flag": "hl_microwave"}, "do": ["It's beyond help."]},
                            {"do": [{"flag": "hl_microwave"}, "You turn the dial all the way up out of sheer curiosity. After a few seconds there is a muffled bang, and casserole paints the inside of the door. A scientist, somewhere, will be very upset."]}]}},
    "freeman_locker": {"extends": ["scenery", "container", "openable"], "name": "locker marked FREEMAN", "aliases": ["locker", "freeman locker", "my locker"],
        "appearance": "Your locker, labelled FREEMAN, stands in the row.",
        "description": "Your locker. Your name. A dent where you once kicked it.",
        "features": [{"name": "photo of a cat", "extends": ["portable"], "aliases": ["photo", "photograph"], "description": "A photo of a cat. You don't remember putting it there."}]},
    "hev_rack": {"extends": ["scenery", "surface"], "name": "HEV suit rack", "aliases": ["rack", "suit rack", "storage"],
        "appearance": "Behind the glass, HEV suits hang on charging frames.", "description": "Charging frames for HEV suits. One has your size on it.",
        "contents_text": "Hanging on the rack: {contents}.", "features": ["hev_suit"]},
    "senior_scientists": {"extends": ["scientist"], "name": "the senior scientists", "proper": True, "aliases": ["senior scientists", "scientists", "scientist"],
        "appearance": "The two senior scientists bend over their consoles.",
        "description": "One is balding with glasses and a lab coat that's seen better years; the other has a grey beard and a calm voice.",
        "profile": {"personality": ["wise", "nervous"], "motives": ["knowledge", "survive"], "motive_text": "understand what is on the other side",
                    "goals": ["finish the test", "get to the Lambda Complex"], "roles": ["giver", "informant", "ally"],
                    "knows": ["xen", "lambda", "science"], "backstory": "\"We've been working toward today for a very long time.\""},
        "actions": {"talk": [{"if": {"flag": "hl_cascade"}, "do": ["\"Gordon! We'll go to the surface and find help. You must make it to the Lambda Complex: they'll know what to do. Hurry!\""]},
                             {"do": ["\"Ah, Gordon. The sample is in place. Just push it into the beam when we're ready. Nothing to worry about. Probably.\""]}]}},
    "control_console": {"extends": ["scenery"], "name": "console", "aliases": ["console", "consoles", "controls"], "appearance": False,
        "description": "Readouts for the anti-mass spectrometer. The numbers are all slightly higher than anyone would like."},
    "anti_mass_spectrometer": {"extends": ["scenery"], "name": "anti-mass spectrometer", "aliases": ["spectrometer", "beam", "anti-mass spectrometer", "emitters"],
        "important": True, "tags": ["heart", "cascade_heart"],
        "appearance": [{"if": {"flag": "hl_cascade"}, "text": "The spectrometer's emitters are cracked and dead."},
                       {"text": "The anti-mass spectrometer's beam crackles at the centre of the chamber."}],
        "description": "A machine for analysing exotic matter, pushed well past its design limits."},
    "sample_cart": {"extends": ["scenery"], "name": "sample cart", "aliases": ["cart", "sample", "crystal", "sample cart"],
        "appearance": [{"if": {"flag": "hl_cascade"}, "text": "What's left of the sample cart lies twisted against the wall."},
                       {"text": "The sample cart waits on its rail, a yellowish crystal glowing in its holder."}],
        "description": "A wheeled cart carrying a crystal sample of unprecedented purity.",
        "actions": {"push": [{"if": {"flag": "hl_cascade"}, "do": ["It's wreckage now."]}, {"do": [{"macro": "hl_cascade", "with": {"here": 1}}]}],
                    "use": [{"if": {"flag": "hl_cascade"}, "do": ["It's wreckage now."]}, {"do": [{"macro": "hl_cascade", "with": {"here": 1}}]}]}},
    "dead_guard_glock": {"extends": ["dead_guard"], "features": ["glock", "ammo_box"],
        "appearance": "The guard who greeted you lies dead behind the desk, his pistol still holstered."},
    "power_junction": {"extends": ["scenery"], "name": "power junction", "aliases": ["junction", "switch", "breaker", "panel"],
        "appearance": "A power junction box sits on a catwalk above the water.", "description": "A breaker for this section's power. It's on, and so is the water.",
        "actions": {"use": ["You throw the breaker. The sparks in the water die. Safe to wade, now."], "push": ["You throw the breaker. The sparks die."]}},
    "uc_guard": {"extends": ["security_guard"], "appearance": "{self.Name} crouches behind the desk, pistol up."},
    "office_guard": {"extends": ["security_guard"], "appearance": "{self.Name} has barricaded himself behind a stack of toner boxes."},
    "tripmine": {"extends": ["scenery"], "name": "laser tripmine", "aliases": ["tripmine", "laser", "mine", "beam"],
        "appearance": "A tripmine's red laser line crosses the shaft.", "description": "Step through the beam and the mine goes off.",
        "actions": {"attack": [{"do": ["You shoot the mine. It goes off with a deafening crack, taking a chunk of wall with it.", {"destroy": "self"}]}]}},
    "dying_scientist": {"extends": ["scientist"], "appearance": "{self.Name} lies wounded against the railing.",
        "actions": {"talk": [{"do": ["\"They... the tentacles... you have to fire the engine. Fuel, oxygen, power. Get them all running, then fire it from the control room.\""]}]}},
    "silo_power_switch": {"extends": ["scenery"], "name": "power switch", "aliases": ["switch", "power switch", "lever"],
        "appearance": [{"if": {"flag": "hl_bp_power"}, "text": "The silo power switch is thrown, its lamp green."}, {"text": "A huge power switch for the silo sits in the off position."}],
        "description": "SILO POWER, says the plate.",
        "actions": {"use": [{"if": {"flag": "hl_bp_power"}, "do": ["It's already on."]}, {"do": [{"flag": "hl_bp_power"}, "You haul the switch over. Generators roar into life, and somewhere above, lights come on in the silo."]}],
                    "push": [{"do": [{"flag": "hl_bp_power"}, "You haul the switch over. Generators roar into life."]}],
                    "pull": [{"do": [{"flag": "hl_bp_power"}, "You haul the switch over. Generators roar into life."]}]}},
    "oxygen_valve": {"extends": ["scenery"], "name": "oxygen valve", "aliases": ["valve", "wheel", "oxygen valve"],
        "appearance": [{"if": {"flag": "hl_bp_oxygen"}, "text": "The oxygen valve is open; the pumps thrum."}, {"text": "A big red valve wheel controls the oxygen pumps."}],
        "description": "OXYGEN SUPPLY: ENGINE TEST.",
        "actions": {"use": [{"if": {"flag": "hl_bp_oxygen"}, "do": ["It's already open."]}, {"do": [{"flag": "hl_bp_oxygen"}, "You spin the wheel. The oxygen pumps start up with a deep thrum."]}],
                    "turn": [{"do": [{"flag": "hl_bp_oxygen"}, "You spin the wheel. The pumps start up."]}]}},
    "fuel_pump_switch": {"extends": ["scenery"], "name": "fuel pump controls", "aliases": ["controls", "fuel pumps", "pump", "switch"],
        "appearance": [{"if": {"flag": "hl_bp_fuel"}, "text": "The fuel pumps are running."}, {"text": "The fuel pump controls sit on a gantry, all lights red."}],
        "description": "FUEL: ENGINE TEST.",
        "actions": {"use": [{"if": {"flag": "hl_bp_fuel"}, "do": ["They're already running."]}, {"do": [{"flag": "hl_bp_fuel"}, "You start the fuel pumps. Kerosene surges through the lines toward the silo."]}],
                    "push": [{"do": [{"flag": "hl_bp_fuel"}, "You start the fuel pumps."]}]}},
    "engine_fire_button": {"extends": ["scenery"], "name": "engine test button", "aliases": ["button", "red button", "fire button"],
        "appearance": "A big red button reads ENGINE TEST - FIRE.", "description": "Gauges beside it show fuel, oxygen and power.",
        "actions": {"push": [{"macro": "hl_fire_engine"}], "use": [{"macro": "hl_fire_engine"}]}},
    "powerup_guard": {"extends": ["security_guard"], "appearance": "{self.Name} is pinned behind an overturned rail car.",
        "actions": {"talk": [{"do": ["\"There's something out there, big as a house, breathes fire. Bullets don't do a thing. If we could get power back to those rails...\""]}]}},
    "generator_switch": {"extends": ["scenery"], "name": "generator switch", "aliases": ["switch", "generator", "lever", "controls"],
        "appearance": [{"if": {"flag": "hl_power_on"}, "text": "The generator roars; the rail power indicator glows."}, {"text": "The generator's master switch is in the off position."}],
        "description": "RAIL POWER, reads the plate. Also: KEEP CLEAR OF TRACKS WHEN ENERGISED.",
        "actions": {"use": [{"macro": "hl_power_up"}], "push": [{"macro": "hl_power_up"}], "pull": [{"macro": "hl_power_up"}]}},
    "rail_car": {"extends": ["scenery"], "name": "rail car", "aliases": ["car", "train", "rail car", "controls"],
        "appearance": "A small maintenance rail car waits on the track.", "description": "Throttle forward, throttle back, a horn. You'll manage.",
        "actions": {"use": ["You nudge the throttle. The car hums along a few metres and stops."]}},
    "launch_console": {"extends": ["scenery"], "name": "launch console", "aliases": ["console", "launch console", "button"],
        "appearance": [{"if": {"flag": "hl_rocket"}, "text": "The launch console reads: LAUNCH SUCCESSFUL."}, {"text": "The launch console blinks: AWAITING AUTHORISATION."}],
        "description": "The controls for the satellite launch.",
        "actions": {"use": [{"if": {"flag": "hl_rocket"}, "do": ["The satellite's already on its way."]},
                            {"do": [{"flag": "hl_rocket"}, {"say": "You arm the launch. Far below, the rocket's engines ignite; the whole complex shakes as it climbs out of the silo and away. The scientist whoops: the Lambda team will have their satellite.", "style": "story"}]}],
                    "push": [{"do": [{"flag": "hl_rocket"}, "You hit the launch button. The rocket goes."]}]}},
    "launch_scientist": {"extends": ["scientist"], "appearance": "{self.Name} hovers by the launch console.",
        "actions": {"talk": [{"do": ["\"You're Freeman? Thank heaven. We need this satellite in orbit for the Lambda team. Arm the launch from here, then get yourself to the Lambda Complex.\""]}]}},
    "satellite_rocket": {"extends": ["scenery"], "name": "rocket", "aliases": ["rocket", "satellite"],
        "appearance": [{"if": {"flag": "hl_rocket"}, "text": "The silo is empty and scorched; the rocket is gone."}, {"text": "A slender rocket stands in the silo, ready to launch."}],
        "description": "The payload fairing carries a satellite for the Lambda team."},
    "confiscated_crate": {"extends": ["scenery", "container"], "name": "crate of confiscated gear", "aliases": ["crate", "gear", "confiscated gear"],
        "tags": ["hl_confiscated"], "appearance": "A crate of confiscated gear sits by the ladder.",
        "description": "Your things, dumped in a box by somebody who expected you to be dead.",
        "contents_text": "In the crate: {contents}.", "empty_text": "It's empty now."},
    "qe_scientist": {"extends": ["scientist"], "appearance": "{self.Name} peers out of an office doorway."},
    "big_laser": {"extends": ["scenery"], "name": "industrial laser", "aliases": ["laser", "gantry"], "appearance": "A huge industrial laser hangs from a gantry.",
        "description": "It cuts through steel. It would cut through you faster."},
    "osprey_wreck": {"extends": ["scenery"], "name": "Osprey wreck", "aliases": ["osprey", "wreck", "plane"], "appearance": False,
        "description": "A V-22 tiltrotor, nose crumpled, still burning."},
    "minefield": {"extends": ["scenery"], "name": "minefield", "aliases": ["mines", "minefield", "signs"], "appearance": "Signs warn: DANGER - MINES.",
        "description": "Walk where the craters are. They've already gone off."},
    "airstrike_radio": {"extends": ["scenery"], "name": "field radio", "aliases": ["radio", "radio post", "field radio"],
        "appearance": "A field radio sits on a table in the command tent.", "description": "Tuned to the HECU's artillery net.",
        "actions": {"use": [{"macro": "hl_airstrike"}]}},
    "tank_wreck": {"extends": ["scenery"], "name": "burning tank", "aliases": ["tank", "abrams"], "appearance": False, "description": "An M1 Abrams, brewed up."},
    "lambda_scientist": {"extends": ["scientist"], "appearance": "{self.Name}, a Lambda team scientist, waves you through the checkpoint.",
        "actions": {"talk": [{"do": ["\"Freeman! We've been waiting. The satellite delivered its payload; we can open a portal to the border world. But first we need the reactor coolant running.\""]}]}},
    "lambda_scientist_2": {"extends": ["scientist"], "appearance": "{self.Name} adjusts the long jump harness.",
        "actions": {"talk": [{"do": ["\"Take the module. You'll need it where you're going. The jumps there are... large.\""]}]}},
    "coolant_pump": {"extends": ["scenery"], "name": "coolant pump", "aliases": ["pump", "coolant pump", "switch"],
        "appearance": "A coolant pump control panel sits by the waterline.", "description": "PRIMARY COOLANT. Its lamps are red.",
        "actions": {"use": [{"do": [{"flag": "hl_coolant"}, "You start the pump. The water level begins to fall."]}]}},
    "teleport_pad": {"extends": ["scenery"], "name": "teleport pad", "aliases": ["pad", "teleport", "teleporter"],
        "appearance": "A teleport pad glows on the floor.", "description": "Step on it and you're somewhere else. Which somewhere is the question."},
    "lambda_portal": {"extends": ["scenery"], "name": "portal", "aliases": ["portal", "rift", "gateway"], "important": True, "tags": ["lambda_heart", "heart"],
        "appearance": "The portal churns in the centre of the chamber, showing another world.",
        "description": "Green-white light around a hole in the world. On the other side: Xen."},
    "portal_scientists": {"extends": ["scientist"], "name": "the Lambda team", "proper": True, "aliases": ["lambda team", "scientists", "team"],
        "appearance": "The Lambda team works frantically at the portal consoles.",
        "actions": {"talk": [{"do": ["\"The portal is stable. We think. Whatever is holding the rift open is on the other side. You have to find it and stop it. Go, Gordon!\""]}]}},
    "xen_researcher": {"extends": ["scenery"], "name": "dead researcher", "aliases": ["researcher", "body", "corpse"],
        "appearance": "A researcher in an HEV suit lies dead on the rock.", "description": "Someone sent through before you. Expeditions, it seems, were not new.",
        "features": [{"id": "long_jump_note", "hidden": True}]},
    "long_jump_note": {"extends": ["portable", "readable"], "name": "expedition notebook", "aliases": ["notebook", "notes"],
        "props": {"text": "Survey notes on Xen: low gravity, healing pools, vast fauna. The last page just says THEY KNOW WE'RE HERE."}},
    "jump_pad": {"extends": ["scenery"], "name": "jump pad", "aliases": ["pad", "jump pad"], "appearance": "An organic jump pad pulses on the rock.",
        "description": "Step on it, and it flings you across the void.",
        "actions": {"use": ["You step on the pad. It puffs, and you sail across to the next island and back again. Exhilarating."]}},
    "health_charger_xen": {"extends": ["healing_pool"], "name": "luminous pool", "aliases": ["pool"]},
    "healing_crystal": {"extends": ["scenery"], "name": "healing crystal", "aliases": ["crystal", "crystals", "healing crystal"],
        "tags": ["nihilanth_crystal"], "appearance": "A golden healing crystal glows on its pillar, feeding the Nihilanth.",
        "description": "While these glow, the Nihilanth heals.",
        "actions": {"attack": [{"do": ["You shoot the crystal. It cracks, flares, and goes dark, and the Nihilanth screams.", {"destroy": "self"}]}]}},
    "holo_instructor": {"extends": ["scenery"], "name": "holographic instructor", "aliases": ["hologram", "instructor", "scientist"],
        "appearance": "A flickering hologram of a balding scientist stands here.",
        "description": "He gestures at things you are about to do, with great patience.",
        "actions": {"talk": ["The hologram explains, again, how to crouch."]}},
    "training_target": {"extends": ["scenery"], "name": "paper target", "aliases": ["target"], "appearance": "A paper target hangs at the end of the range.",
        "description": "A silhouette with bullseye rings.", "actions": {"attack": ["You put a few rounds through the centre ring. The hologram applauds."]}},
})

# The Nihilanth and others as story characters
F["nihilanth_hl"] = {"extends": ["nihilanth"], "important": True, "tags": ["nihilanth", "villain"],
    # For automated players: what to do before attacking it.
    "solve": ["attack healing crystal", "attack healing crystal", "attack healing crystal"],
    "profile": {"personality": ["cold"], "motives": ["hold_rift", "survive", "dominion", "power"],
                "motive_text": "hold the rift open, and never again be caged",
                "goals": ["keep the rift open", "end the last of the humans who came"],
                "backstory": "Its voice crawls through your skull: \"...last of them... you are the last... others came... others die...\"",
                "roles": ["antagonist"], "knows": ["xen"],
                "greet": ["The Nihilanth's voice rolls through your mind: \"...Freeman... you come... you will not leave...\""],
                "confront": ["\"...you are man... and I am the last...\" The words fall apart in your head."],
                "epilogue": ""},
    "on_turn": [{"if": {"here": "tag:nihilanth_crystal"}, "do": [
        {"if": "self.health < self.max_health", "then": [{"add": {"health": "=min(15, self.max_health - self.health)"}},
         {"say": "The healing crystals pulse; the Nihilanth's wounds close. ({self.health}/{self.max_health})", "style": "dim"}]}]}],
    "on_death": [{"flag": "hl_nihilanth_dead"}, {"say": "Light pours out of the Nihilanth's split skull. Every portal in the chamber flares, and the world tilts away from under you...", "style": "story"},
                 {"teleport": "room:hl/c5a1_gman"}]}
F["gman_hl"] = {"extends": ["gman"], "profile": dict(core.F["gman"]["profile"], menu=False),
    "actions": {"talk": [{"if": {"all": [{"flag": "hl_nihilanth_dead"}, {"flag": "story_resolved"}]}, "do": [{"choice": {
        "prompt": "\"Mister Freeman,\" the man in the suit says, with that odd rhythm. \"You have done... rather well. My employers have authorised me to offer you a job. I'd advise you... to accept. The alternative is... a battle you have no chance of winning.\"",
        "options": [
            {"text": "Accept the offer.", "do": [{"end_game": "\"Excellent,\" he says, and straightens his tie. \"Time to... choose. I'll see you... up ahead.\" The world goes dark around you, and you wait for the next job.", "win": True}]},
            {"text": "Refuse.", "do": [{"end_game": "\"Wise, or not... we shall see.\" He vanishes. You are standing in a cavern surrounded by alien grunts, every one of them turning toward you.", "win": False}]}],
        "cancel": "He waits. He's very good at waiting."}}]},
        {"do": ["He adjusts his tie and regards you with polite interest. \"Not yet, {player.name}. You have... unfinished business. Not... yet.\" Behind you, a way back opens."]}]}}

ROOM_FIX = {"c4a3_chamber": ("nihilanth", "nihilanth_hl"), "c5a1_gman": ("gman", "gman_hl")}
for short, (old, new) in ROOM_FIX.items():
    feats = B.rooms[B.rid(short)]["features"]
    feats[feats.index(old)] = new

# Mark the shared core's equipment as important in this campaign.
for fid in ("crowbar", "hev_suit", "long_jump"):
    F[fid] = {"_patch": True, "important": True}

MACROS = {
    "hl_cascade": {"do": [
        {"if": {"flag": "hl_cascade"}, "then": [{"stop": True}]},
        {"flag": "hl_cascade"},
        {"if": {"local": "here", "eq": 1},
         "then": [{"say": "You shove the cart into the beam. For a moment nothing happens. Then the beam bends, turns green, and splits into a dozen crackling arcs. The scientists' voices rise in panic over the intercom; the chamber shakes; the world flickers - concrete, then violet sky and floating rock and huge alien shapes, then concrete again - and everything goes white.", "style": "story"}],
         "else": [{"say": "A tremor runs through the floor, then a deep, rolling boom far below. The lights die and come back red. Somewhere in the depths of Black Mesa, the Anomalous Materials test has gone catastrophically wrong.", "style": "story"}]},
        {"spawn": "headcrab", "in": "room:hl/c1a0_lobby"}, {"spawn": "zombie", "in": "room:hl/c1a0_offices"},
        {"spawn": "headcrab", "in": "room:hl/c1a0_breakroom"}, {"spawn": "vortigaunt", "in": "room:hl/c1a0a_labs"},
        {"spawn": "houndeye", "in": "room:hl/c1a0c_dorms"},
        {"say": "Resonance cascade. Nobody will ever be sure who said it first.", "style": "dim"}]},
    "hl_fire_engine": {"do": [
        {"if": {"flag": "hl_tentacles_dead"}, "then": ["The engine's already been fired. There's nothing left down there but charcoal.", {"stop": True}]},
        {"if": {"all": [{"flag": "hl_bp_power"}, {"flag": "hl_bp_oxygen"}, {"flag": "hl_bp_fuel"}]},
         "then": [{"flag": "hl_tentacles_dead"},
                  {"say": "You slam the button. The rocket engine at the bottom of the silo ignites with a roar that shakes your teeth. A pillar of fire fills the pit; the tentacles thrash, shriek and burn. When the smoke clears there is nothing left of them but charred stumps.", "style": "story"}],
         "else": ["The button clicks. ENGINE NOT READY, says the display: it needs fuel, oxygen and power all running.",
                  {"if": {"not": {"flag": "hl_bp_fuel"}}, "then": ["The FUEL gauge reads empty."]},
                  {"if": {"not": {"flag": "hl_bp_oxygen"}}, "then": ["The OXYGEN gauge reads empty."]},
                  {"if": {"not": {"flag": "hl_bp_power"}}, "then": ["The POWER lamp is dark."]}]}]},
    "hl_power_up": {"do": [
        {"if": {"flag": "hl_power_on"}, "then": ["The generator is already running.", {"stop": True}]},
        {"flag": "hl_power_on"},
        {"say": "You throw the generator's master switch. The turbine spools up with a scream, and power floods into the rails.", "style": "story"},
        {"find": {"def": "gargantua"}, "in": "room:hl/c2a1_garg", "as": "garg", "hidden_too": True},
        {"if": {"exists": "local:garg"}, "then": [{"say": "Down in the yard, the gargantua is standing on the high-voltage rail. Lightning crawls over it; it roars, staggers, and bursts apart in a shower of sparks.", "style": "good"}, {"destroy": "local:garg"}]}]},
    "hl_airstrike": {"do": [
        {"if": {"flag": "hl_airstrike"}, "then": ["The radio hisses. Nobody's answering now.", {"stop": True}]},
        {"flag": "hl_airstrike"},
        {"say": "You key the radio and read off the grid reference the Marines scrawled on the map. A voice confirms. Seconds later, jets scream over the canyon.", "style": "story"},
        {"find": {"def": "gargantua"}, "in": "room:hl/c2a5d_courtyard", "as": "garg", "hidden_too": True},
        {"if": {"exists": "local:garg"}, "then": [{"say": "The airstrike falls squarely on the courtyard. When the dust settles, the gargantua is in pieces.", "style": "good"}, {"destroy": "local:garg"}]}]},
    "hl_capture": {"do": [
        {"flag": "hl_captured"},
        {"say": "A rifle butt comes out of nowhere. The last thing you hear is a soldier laughing, and someone saying to take you to the compactor.", "style": "story"},
        {"for_each": {"tag": "hl_weapon"}, "in": "player", "hidden_too": True, "direct": True, "do": [{"move": "it", "to": "any:tag:hl_confiscated"}]},
        {"teleport": "room:hl/c2a4_compactor"}]},
    "hl_take_damage": {"do": [
        {"let": {"soak": "=min(player.suit, int(amount * 2 / 3))"}},
        {"add": {"suit": "=-soak", "health": "=-(amount - soak)"}, "on": "player"},
        {"macro": "check_player_death"}]},
}
RULES = {
    "hl_cascade_catchup": {"on": "enter", "if": {"all": [{"in_room": "tag:post_cascade"}, {"not": {"flag": "hl_cascade"}}]},
        "do": [{"macro": "hl_cascade", "with": {"here": 0}}]},
    "hl_tentacle_strike": {"on": ["turn", "enter"], "if": {"all": [{"in_room": "tag:tentacle_zone"}, {"not": {"flag": "hl_tentacles_dead"}}, {"chance": 0.35}]},
        "do": [{"say": "A tentacle hears you. Its beak slams down a few feet away, then again, closer.", "style": "warn"},
               {"macro": "hl_take_damage", "with": {"amount": 12}}]},
}

B.section("lore").update({
    "hl_cascade": {"title": "The resonance cascade", "about": ["area:hl_blackmesa"], "tags": ["science", "xen", "lambda", "blackmesa"],
        "text": "A crystal sample of extraordinary purity, pushed into the anti-mass spectrometer at over a hundred percent. The beam tore a hole between worlds, and the creatures of Xen began pouring through. The scientists call it a resonance cascade. They also said it was impossible."},
    "hl_lambda_plan": {"title": "The Lambda team's plan", "about": ["area:hl_blackmesa"], "tags": ["lambda", "science"],
        "text": "The Lambda team believes something on the far side is holding the rift open. A satellite launch from Sector E carries the instruments they need; with it in orbit, they can open a stable portal and send someone through to stop whatever is on the other side."},
    "hl_late": {"title": "Running late", "about": ["area:hl_blackmesa"], "tags": ["blackmesa", "security", "rumour"], "chance": 0.7,
        "text": "Gordon Freeman, twenty-seven, PhD in theoretical physics from MIT, research associate in Anomalous Materials. On the morning of the incident his time card shows he was late. Nobody has ever found out why."},
    "hl_nihilanth": {"title": "The Nihilanth", "about": ["def:nihilanth_hl"], "tags": ["xen"],
        "text": "The creature at the heart of Xen is vast, ancient and telepathic. It keeps the vortigaunts enslaved and the rift open. Every expedition before yours was found and destroyed."},
    "hl_hecu_orders": {"title": "HECU orders", "about": ["area:hl_blackmesa"], "tags": ["hecu", "military"],
        "text": "Intercepted Marine traffic is blunt: secure the facility, neutralise hostiles, and leave no witnesses. Freeman is named specifically."},
})

EVENTS = {
    "hl_cascade_war": {
        "title": ["Half-Life", "Black Mesa Incident", "Resonance Cascade"],
        "tags": ["blackmesa", "half-life"], "start_areas": ["hl_blackmesa"],
        "roles": {
            "villain": {"type": "character", "match": {"tag": ["nihilanth"]}},
            "facility": {"type": "place", "match": {"id": ["hl_blackmesa"]}}},
        "hook": "It is a normal morning at the Black Mesa Research Facility, and you are late. You are Gordon Freeman, research associate in Anomalous Materials, and today's test pushes an unusually pure sample into the anti-mass spectrometer further than anyone has gone before. What happens next will tear the facility apart, and the one who keeps the rift open waits in another world: {villain}.",
        "goal": "Survive {facility}, reach the Lambda Complex, cross into Xen, and destroy {villain}.",
        "resolutions": [{"verb": "attack", "target": "villain", "title": "Kill the Nihilanth",
                         "text": "{target.The} dies, and with it, the rift begins to close. But someone has been watching all along..."}],
        "ending": "The rift collapses. Black Mesa is in ruins, the Marines are gone, the vortigaunts are free. And you, Gordon Freeman, have been noticed."},
    "hl_military_cleanup": {
        "title": ["No Witnesses", "Surface Tension"], "tags": ["blackmesa", "half-life", "military"], "start_areas": ["hl_blackmesa"],
        "weight": 0.6,
        "roles": {
            "villain": {"type": "character", "match": {"tag": ["nihilanth"]}},
            "witness": {"type": "character", "match": {"tag": ["scientist"], "role": ["victim", "informant"]}, "optional": True},
            "facility": {"type": "place", "match": {"id": ["hl_blackmesa"]}}},
        "hook": "The resonance cascade was bad. What came next was worse: the Marines, sent to contain the incident, with orders to silence every witness. You are Gordon Freeman, and you are top of their list. The only way out is through - all the way to {villain}.",
        "goal": "Fight through the Marines and the aliens across {facility}, and end the incursion at its source: {villain}.",
        "resolutions": [{"verb": "attack", "target": "villain", "text": "{target.The} falls; Xen's grip on Black Mesa breaks."}],
        "lore": [{"title": "Witness", "about": ["cast:witness"], "text": "{witness.The} watched the Marines execute colleagues in the office wing, and has been hiding ever since."}],
        "ending": "The incursion ends. Somewhere, a report is filed that says nobody survived Black Mesa. It is wrong about you."},
}

AREAS = {
    "hl_blackmesa": {
        "name": "the Black Mesa Research Facility",
        "start_label": "Half-Life - Gordon Freeman, riding the inbound tram to work",
        "tags": ["blackmesa", "start", "half-life", "scifi", "indoor", "lambda"], "theme": ["blackmesa", "office", "lab", "maintenance", "surface"],
        "important": True, "start": "hl/c0a0_tram",
        "rooms": ["hl/*"],
        "entrances": ["hl/c1a3b_storage", "hl/c2a5x_cliffs", "hl/c3a1a_yard", "hl/c2a2a_tunnels"],
        "player": {"name": "Gordon Freeman", "player_name": "Gordon Freeman", "aliases": ["gordon", "freeman"],
                   "description": "Gordon Freeman: theoretical physicist, MIT graduate, wearer of glasses, and a man who never says a word."}},
    "hl_hazard": {
        "name": "the Hazard Course", "tags": ["blackmesa", "training", "indoor"], "theme": ["blackmesa", "office"],
        "rooms": ["hlh/*"], "entrances": ["hlh/t0a0_start"]},
}


def build():
    problems = B.check()
    assert not problems, problems
    manifest = {
        "id": "hl_halflife", "name": "Half-Life: Black Mesa Incident", "version": "1.0.0", "author": "Patchwork",
        "description": "The Half-Life campaign, chapter by chapter and map by map (c0a0 to c5a1, plus the t0a0 Hazard Course): the inbound tram, the resonance cascade, the office complex, the Marines, Blast Pit's tentacles, Power Up's gargantua, On a Rail, capture and the trash compactor, Questionable Ethics, Surface Tension, Lambda Core, Xen, the Gonarch, the alien factory, the Nihilanth and the G-Man's offer. Locked doors and outdoor areas grow generated sections. Spawn as Gordon Freeman on the tram.",
        "requires": ["core", "combat", "hl_core"], "load_after": ["hl_core"], "recommends": ["hl_opfor", "hl_blueshift", "daycycle"],
        "priority": 64, "tags": ["half-life", "blackmesa", "scifi", "campaign"]}
    rooms = B.rooms
    by_chapter = {}
    for rid, r in rooms.items():
        by_chapter.setdefault(r["props"]["map"][:4] if not rid.startswith(H) else "t0a0", {})[rid] = r
    files = {"areas.json": {"areas": AREAS, "events": EVENTS, "lore": B.sections["lore"],
                            "macros": MACROS, "rules": RULES, "grammar": GRAMMAR},
             "features.json": {"features": F}}
    for key, chunk in sorted(by_chapter.items()):
        files["maps_%s.json" % key] = {"rooms": chunk}
    B.write(manifest, files)


GRAMMAR = {
    "tram_announcement": [
        "\"Good morning, and welcome to the Black Mesa Transit System. This automated train is provided for the security and convenience of the Black Mesa Research Facility personnel.\"",
        "\"The time is 8:47 a.m. Current outside temperature is 93 degrees.\"",
        "\"This train is inbound from Black Mesa Topside to Sector C Test Labs and Control Facilities.\"",
        "\"Please keep your arms and legs inside the train at all times.\"",
        "\"A reminder: radioactive and biological hazards are a part of life at Black Mesa. Please report any contamination to your supervisor.\""],
}
