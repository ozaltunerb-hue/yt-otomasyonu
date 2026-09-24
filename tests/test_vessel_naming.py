#!/usr/bin/env python3
"""
Gemi adı kapısı ve shipyard gemi tipleri, 2026-09-24 TUR 8.

"Vessel on Slipway" bir tip değildi; prompt "the vessel" diyordu ve Kie kargo gemisi çizdi.
Shipyard artık evrendeki 4 gerçek tipi kullanır; simplifier çıktısında (F) atanan geminin
adı geçmeli. Gerçek API çağrısı yapılmaz.
"""
import asyncio
import os
import re
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.prompt_generator as pg
from core.creative_engine import (
    DEEPMYSTER_EXISTING_IDEAS_LIBRARY,
    DOMAIN_ATTRIBUTES,
    DOMAIN_CAST_RANGES,
    ENV_CENTRIC_DOMAINS,
    SHIP_NAME_PATTERNS,
    VESSEL_UNIVERSE,
    build_prompt_simplifier_system,
    build_scenario_writer_system,
)
from core.prompt_generator import NoValidScenarioError, simplify_with_gate, validate_simplified_prompt

D = "shipyard_and_drydock_engineering"
SCEN = {
    "visible_start": "The sailing yacht lurches forward on the slipway as three workers in orange coveralls leap back.",
    "beat1_action_verb": "lurches",
}
GOOD = ("The sailing yacht lurches forward on the slipway as three workers in orange coveralls leap back. "
        "It slides faster, hull scraping the supports. The yacht keeps sliding toward the water.")
VAGUE = GOOD.replace("The sailing yacht lurches", "The vessel lurches").replace("The yacht keeps", "It keeps")

FORBIDDEN_SHIP = re.compile(r"cargo|container|tanker|bulk|barge|trawler|fishing|\btug|\bfreight", re.I)
GENERIC = re.compile(r"\b(?:vessels?|ships?|boats?)\b", re.I)
ANY_TYPE = re.compile("|".join(f"(?:{p})" for p in SHIP_NAME_PATTERNS.values()), re.I)


def F(failures):
    return [f for f in failures if f.startswith("Simplifier: gemi adı yok")]


class TestShipyardShips(unittest.TestCase):
    def test_shipyard_uses_existing_types(self):
        ships = DOMAIN_ATTRIBUTES[D]["ships"]
        self.assertEqual(ships, ["Luxury Motor Yacht", "Sailing Yacht", "High-speed Catamaran", "Passenger Car Ferry"])
        self.assertNotIn("Vessel on Slipway", VESSEL_UNIVERSE)
        for s in ships:
            self.assertIsNone(FORBIDDEN_SHIP.search(s), s)

    def test_every_universe_ship_has_name_pattern(self):
        self.assertEqual(set(SHIP_NAME_PATTERNS), set(VESSEL_UNIVERSE))

    def test_pattern_matches_own_name(self):
        for ship, pat in SHIP_NAME_PATTERNS.items():
            with self.subTest(ship=ship):
                self.assertRegex(f"the {ship.lower()} slides", re.compile(pat, re.I))


class TestSystemPromptsRequireNaming(unittest.TestCase):
    def test_writer_rule(self):
        for d in list(DOMAIN_CAST_RANGES) + ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                self.assertIn("Always call the vessel by its assigned type", build_scenario_writer_system(15, d))

    def test_simplifier_rule(self):
        for d in DOMAIN_CAST_RANGES:
            with self.subTest(domain=d):
                self.assertIn("name the vessel by its type", build_prompt_simplifier_system(15, d))


class TestShipNameGate(unittest.TestCase):
    def test_named_passes(self):
        self.assertEqual(validate_simplified_prompt(GOOD, SCEN, D, "Sailing Yacht"), (True, []))

    def test_vessel_alone_rejected(self):
        ok, failures = validate_simplified_prompt(VAGUE, SCEN, D, "Sailing Yacht")
        self.assertFalse(ok)
        self.assertEqual(len(F(failures)), 1, failures)

    def test_all_vessel_domains(self):
        cases = {
            "ferry_operations": ("Passenger Car Ferry", "Water gushes onto the open vehicle deck",
                                 "Water gushes onto the ferry's open vehicle deck"),
            "cruise_ship_operations": ("Ocean Cruise Liner", "A rogue wave crashes over the pool deck",
                                       "A rogue wave crashes over the cruise liner's pool deck"),
            "marina_and_yacht_operations": ("Runaway Powerboat", "The boat veers into the pontoon",
                                            "The runaway powerboat veers into the pontoon"),
            D: ("Passenger Car Ferry", "The vessel tilts in the flooding drydock",
                "The passenger car ferry tilts in the flooding drydock"),
        }
        for d, (ship, vague, named) in cases.items():
            with self.subTest(domain=d):
                self.assertTrue(F(validate_simplified_prompt(vague + ", still moving.", {}, d, ship)[1]))
                self.assertFalse(F(validate_simplified_prompt(named + ", still moving.", {}, d, ship)[1]))

    def test_env_centric_and_none_skip(self):
        p = "A tornado tears across the marina, flinging boats. Debris keeps swirling."
        self.assertFalse(F(validate_simplified_prompt(p, {}, "coastal_tornado_landfall", "Sailing Yacht")[1]))
        self.assertFalse(F(validate_simplified_prompt(p, {}, "urban_city_disasters", "None")[1]))

    def test_no_ship_given_skips(self):
        self.assertFalse(F(validate_simplified_prompt(VAGUE, SCEN, D)[1]))

    def test_unknown_ship_is_config_error(self):
        with self.assertRaises(RuntimeError):
            validate_simplified_prompt(GOOD, SCEN, D, "Vessel on Slipway")


class TestGateRetryUsesForcedShip(unittest.TestCase):
    def _run(self, responses):
        mock = AsyncMock(side_effect=[{"prompt": p} for p in responses])
        cand = {"scenario": SCEN, "catalyst": {"domain_id": D, "forced_ship": "Sailing Yacht"}, "score": 5}
        with patch.object(pg, "_call_gpt", mock):
            return asyncio.run(simplify_with_gate([cand])), mock

    def test_retry_then_pass(self):
        (_, simp, attempts), mock = self._run([VAGUE, GOOD])
        self.assertEqual(simp["prompt"], GOOD)
        self.assertIn("the sailing yacht", mock.call_args_list[1].args[1])

    def test_always_vague_raises(self):
        with self.assertRaises(NoValidScenarioError):
            self._run([VAGUE, VAGUE, VAGUE])


class TestLibrary(unittest.TestCase):
    def test_generic_vessel_lines_name_a_type(self):
        for cat, data in DEEPMYSTER_EXISTING_IDEAS_LIBRARY.items():
            for line in data["reference_scenarios"]:
                if GENERIC.search(line):
                    with self.subTest(cat=cat, line=line[:60]):
                        self.assertRegex(line, ANY_TYPE)


if __name__ == "__main__":
    unittest.main()
