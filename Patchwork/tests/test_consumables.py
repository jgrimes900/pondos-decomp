"""Consumers: things that spend a resource when used (guns, grenades, spells, blades that wear out)."""

import unittest

from helpers import Player

FANTASY = ["core", "combat", "wilds", "spire"]
HL = ["core", "wilds", "hl_core"]


class Base(unittest.TestCase):
    mods = FANTASY

    def setUp(self):
        self.p = Player(self.mods, 1)
        self.w = self.p.world

    def give(self, fid, **props):
        e = self.w.spawn_spec({"id": fid}, self.w.player)[0]
        e.props.update(props)
        return e

    def foe(self, fid="grey_wolf", health=999):
        e = self.w.spawn_spec({"id": fid}, self.w.room)[0]
        e.props.update(health=health, max_health=health, damage=0)
        return e

    def held(self, e):
        return e.uid in self.w.entities and self.w.is_inside(e, self.w.player)


class Guns(Base):
    mods = HL

    def test_shots_come_out_of_the_magazine(self):
        gun = self.give("glock")
        self.foe("headcrab")
        self.assertEqual(gun.props.get("stored", gun.props["capacity"]), 17)   # comes loaded
        self.p.do("attack headcrab with pistol")
        self.assertEqual(gun.props["stored"], 16)

    def test_empty_gun_clicks_and_does_no_harm(self):
        gun = self.give("glock", stored=0)
        crab = self.foe("headcrab")
        out = self.p.do("attack headcrab with pistol")
        self.assertIn("out of rounds", out)
        self.assertEqual(crab.props["health"], 999)

    def test_reload_from_matching_ammo_only(self):
        gun = self.give("glock", stored=3)
        shells = self.give("ammo_buckshot")
        self.assertIn("won't fit", self.p.do("reload pistol with buckshot"))
        self.assertEqual(gun.props["stored"], 3)
        box = self.give("ammo_9mm")
        self.p.do("reload pistol")
        self.assertEqual(gun.props["stored"], 17)
        self.assertEqual(box.props["ammo"], 34 - 14)
        self.assertEqual(shells.props["ammo"], 12)

    def test_using_ammo_on_a_gun_or_by_itself_loads_it(self):
        gun = self.give("python", stored=0)
        self.give("ammo_357")
        self.p.do("use 357 rounds on revolver")
        self.assertEqual(gun.props["stored"], 6)
        gun.props["stored"] = 1
        self.p.do("use 357 rounds")
        self.assertEqual(gun.props["stored"], 6)

    def test_drained_ammo_box_is_thrown_away(self):
        gun = self.give("python", stored=0)
        box = self.give("ammo_357", ammo=4)
        self.p.do("reload revolver")
        self.assertEqual(gun.props["stored"], 4)
        self.assertNotIn(box.uid, self.w.entities)

    def test_auto_feed_reloads_when_dry(self):
        gun = self.give("glock", stored=0)
        self.give("ammo_9mm")
        crab = self.foe("headcrab")
        self.p.do("attack headcrab with pistol")
        self.assertEqual(gun.props["stored"], 16)
        self.assertLess(crab.props["health"], 999)

    def test_direct_feed_draws_from_carried_supply(self):
        tau = self.give("gauss")
        self.foe("headcrab")
        self.assertIn("out of uranium", self.p.do("attack headcrab with tau cannon"))
        cell = self.give("ammo_uranium")
        self.p.do("attack headcrab with tau cannon")
        self.assertEqual(cell.props["ammo"], 18)
        self.assertIn("uranium", self.p.do("reload tau cannon"))   # nothing to load: it draws directly
        self.assertTrue(self.held(tau))

    def test_grenade_is_consumed(self):
        nade = self.give("grenade")
        crab = self.foe("headcrab")
        out = self.p.do("attack headcrab with grenade")
        self.assertIn("flat crack", out)
        self.assertNotIn(nade.uid, self.w.entities)
        self.assertLess(crab.props["health"], 999)
        self.assertIn("can't be reloaded", self.p.do("reload snarks") if self.give("snark_nest") else "")

    def test_best_weapon_skips_empty_guns(self):
        self.give("glock", stored=0)
        self.give("crowbar")
        crab = self.foe("headcrab")
        out = self.p.do("attack headcrab")
        self.assertNotIn("out of rounds", out)
        self.assertLess(crab.props["health"], 999)
        self.assertIn("Attack: 15", self.p.do("status"))   # 5 + crowbar's 10, not the dry pistol


class Fantasy(Base):
    def test_sword_wears_out_and_breaks(self):
        sword = self.give("rusty_sword", stored=2)
        self.foe()
        self.p.do("attack wolf with sword")
        self.assertEqual(sword.props["stored"], 1)
        out = self.p.do("attack wolf with sword")
        self.assertIn("snaps off", out)
        self.assertNotIn(sword.uid, self.w.entities)
        broken = [e for e in self.w.descendants(self.w.player) if e.def_id == "broken_sword"]
        self.assertEqual(len(broken), 1)

    def test_whetstone_repairs(self):
        sword = self.give("rusty_sword", stored=1)
        stone = self.give("whetstone")
        self.p.do("repair sword with whetstone")
        self.assertEqual(sword.props["stored"], 9)
        self.assertNotIn(stone.uid, self.w.entities)

    def test_bow_draws_arrows_from_the_quiver(self):
        self.give("short_bow")
        quiver = self.give("quiver", arrows=2)
        self.foe()
        self.p.do("attack wolf with bow")
        self.assertEqual(quiver.props["arrows"], 1)
        self.p.do("attack wolf with bow")
        self.assertNotIn(quiver.uid, self.w.entities)
        self.assertIn("find none", self.p.do("attack wolf with bow"))

    def test_firepot_is_thrown_once(self):
        pot = self.give("firepot")
        self.foe()
        self.assertIn("sheet of flame", self.p.do("attack wolf with firepot"))
        self.assertNotIn(pot.uid, self.w.entities)

    def test_wand_burns_mana_from_a_crystal(self):
        self.give("ember_wand")
        crystal = self.give("mana_crystal")
        self.foe()
        for expected in (6, 3, 0):
            self.p.do("attack wolf with wand")
            if expected:
                self.assertEqual(crystal.props["mana"], expected)
        self.assertNotIn(crystal.uid, self.w.entities)
        self.assertIn("smoulders", self.p.do("attack wolf with wand"))

    def test_wand_can_draw_from_the_player(self):
        self.give("ember_wand")
        self.w.player.props["mana"] = 5
        self.foe()
        self.p.do("attack wolf with wand")
        self.assertEqual(self.w.player.props["mana"], 2)
        self.assertIn("player", self.w.entities)

    def test_scroll_spent_on_reading_turns_blank(self):
        scroll = self.give("scroll_of_thunder")
        out = self.p.do("read scroll of thunder")
        self.assertIn("thunder rolls", out)
        self.assertNotIn(scroll.uid, self.w.entities)
        blank = [e for e in self.w.descendants(self.w.player) if e.def_id == "blank_scroll"]
        self.assertTrue(blank)
        self.assertIn("Nothing", self.p.do("read blank scroll"))

    def test_reload_everything(self):
        sword = self.give("rusty_sword", stored=4)
        self.give("whetstone")
        self.assertIn("load", self.p.do("reload"))
        self.assertEqual(sword.props["stored"], 12)
        self.assertIn("nothing", self.p.do("reload"))


if __name__ == "__main__":
    unittest.main()
