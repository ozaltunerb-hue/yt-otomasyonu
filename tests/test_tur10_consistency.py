#!/usr/bin/env python3
"""
TUR 10 (2026-09-24): gemi-ortam uyumu, env-centric el kamerası çekim yeri, cast rolleri.
Gerçek API çağrısı yapılmaz.
"""
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.prompt_generator as pg
from core.creative_engine import (
    DOMAIN_ATTRIBUTES,
    ENV_CENTRIC_DOMAINS,
    MARITIME_INSPIRATION_DOMAINS,
    SHIP_INCOMPATIBLE,
    VESSEL_UNIVERSE,
    apply_style_lock,
    get_creative_catalyst,
)
from core.prompt_generator import validate_cast_size, validate_ship_setting

CRUISE = "cruise_ship_operations"
RAILING = "Filmed from a ship's railing"
ON_LAND = "Filmed by an onlooker on land"


def _cruise_catalyst():
    others = [d for d in MARITIME_INSPIRATION_DOMAINS if d != CRUISE]
    ship = lambda d: (DOMAIN_ATTRIBUTES[d]["ships"] or ["none"])[0].lower()
    return get_creative_catalyst(recent_history=[f"{d}|{ship(d)}|x|x|fixed_cctv" for d in others])


class TestShipIncompatible(unittest.TestCase):
    def test_table_matches_pools(self):
        """Yazım hatası sessizce filtreyi boşa düşürmesin: her kayıt gerçek havuz değerine işaret etmeli."""
        for ship, banned in SHIP_INCOMPATIBLE.items():
            self.assertIn(ship, VESSEL_UNIVERSE)
            domains = [d for d, a in DOMAIN_ATTRIBUTES.items() if ship in a["ships"]]
            for d in domains:
                self.assertTrue(banned["environments"] <= set(DOMAIN_ATTRIBUTES[d]["environments"]), d)
                self.assertTrue(banned["events"] <= set(DOMAIN_ATTRIBUTES[d]["events"]), d)

    def test_tender_never_gets_pool_deck(self):
        banned = SHIP_INCOMPATIBLE["Cruise Tender Boat"]
        tender_runs = 0
        for _ in range(300):
            cat = _cruise_catalyst()
            if cat["forced_ship"] != "Cruise Tender Boat":
                continue
            tender_runs += 1
            self.assertNotIn(cat["forced_environment"], banned["environments"])
            self.assertNotIn(cat["forced_event"], banned["events"])
        self.assertGreater(tender_runs, 20)

    def test_liner_still_gets_pool_deck(self):
        envs = {c["forced_environment"] for c in (_cruise_catalyst() for _ in range(300))
                if c["forced_ship"] != "Cruise Tender Boat"}
        self.assertIn("Open-air pool deck", envs)

    def test_scenario_gate(self):
        pool = {"visible_start": "A rogue wave surges onto the cruise tender boat's pool deck as fifteen passengers scatter."}
        berth = {"visible_start": "The cruise tender boat slams against the terminal berth as ten passengers grab the rail."}
        loungers = {"physical_movement": "Sun loungers slide across the tender."}
        self.assertFalse(validate_ship_setting(pool, "Cruise Tender Boat")[0])
        self.assertIn("pool deck", validate_ship_setting(pool, "Cruise Tender Boat")[1][0])
        self.assertFalse(validate_ship_setting(loungers, "Cruise Tender Boat")[0])
        self.assertEqual(validate_ship_setting(berth, "Cruise Tender Boat"), (True, []))
        self.assertEqual(validate_ship_setting(pool, "Ocean Cruise Liner"), (True, []))
        self.assertEqual(validate_ship_setting(pool, "None"), (True, []))


class TestHandheldVantage(unittest.TestCase):
    def test_style_lock_by_domain(self):
        for d in ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                out = apply_style_lock("A wave crashes", "bystander_handheld", {"domain_id": d, "forced_ship": "None"})
                self.assertNotIn("ship's railing", out)
                self.assertEqual(out.count(ON_LAND), 1)
        out = apply_style_lock("A ferry rolls", "bystander_handheld",
                               {"domain_id": "ferry_operations", "forced_ship": "Passenger Car Ferry"})
        self.assertEqual(out.count(RAILING), 1)
        self.assertNotIn(ON_LAND, out)

    def test_other_archetypes_unchanged(self):
        for cam in ("fixed_cctv", "chase_pov"):
            out = apply_style_lock("A wave crashes", cam, {"domain_id": "urban_city_disasters", "forced_ship": "None"})
            self.assertNotIn(ON_LAND, out)

    def test_writer_guidance_env(self):
        def captured(domain, ship):
            mock = AsyncMock(return_value={})
            cat = {"domain_id": domain, "domain_title": "t", "guidance": "g", "example_elements": [],
                   "camera_styles": [], "forced_ship": ship, "forced_event": "e", "forced_environment": "x"}
            with patch.object(pg, "_call_gpt", mock):
                asyncio.run(pg._generate_scenario(cat, "bystander_handheld"))
            return " ".join(str(a) for a in mock.call_args.args)
        env = captured("urban_city_disasters", "None")
        self.assertIn("onlooker on land", env)
        self.assertNotIn("from a ship's railing", env)
        self.assertIn("from a ship's railing", captured("ferry_operations", "Passenger Car Ferry"))


class TestCastRoles(unittest.TestCase):
    def test_riders_counted(self):
        ok, failures = validate_cast_size(
            {"visible_start": "A jet ski with two riders surges toward the dock."}, "marina_and_yacht_operations")
        self.assertFalse(ok)
        self.assertIn("2 kişi, alt sınır 3", failures[0])

    def test_new_roles(self):
        for role in ["riders", "drivers", "divers", "boaters", "skippers", "kayakers", "jet skiers",
                     "yacht owners", "residents", "motorists", "rescuers", "firefighters", "pilots"]:
            with self.subTest(role=role):
                ok, failures = validate_cast_size(
                    {"visible_start": f"The ferry rolls as three {role} grab the rail."}, "ferry_operations")
                self.assertTrue(ok, failures)

    def test_no_known_person_message(self):
        ok, failures = validate_cast_size({"visible_start": "The ferry rolls hard in the swell."}, "ferry_operations")
        self.assertFalse(ok)
        self.assertIn("tanınan sayılı kişi ifadesi yok", failures[0])


if __name__ == "__main__":
    unittest.main()
