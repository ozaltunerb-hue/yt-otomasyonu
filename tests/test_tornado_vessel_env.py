#!/usr/bin/env python3
"""
TUR 11 (2026-09-24): coastal_tornado_landfall'da gemi sadece marina/liman ortamında atanır.
Şehir/plaj ortamında gemi None, "Marina equipment..." olayı seçilmez. Gerçek API çağrısı yok.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.creative_engine import (
    DOMAIN_ATTRIBUTES,
    MARITIME_INSPIRATION_DOMAINS,
    VESSEL_ENVIRONMENTS,
    VESSEL_UNIVERSE,
    build_scenario_writer_system,
    get_creative_catalyst,
    is_current_universe_combo,
)

T = "coastal_tornado_landfall"
RULE = VESSEL_ENVIRONMENTS[T]


def _catalyst(domain, runs=200):
    others = [d for d in MARITIME_INSPIRATION_DOMAINS if d != domain]
    ship = lambda d: (DOMAIN_ATTRIBUTES[d]["ships"] or ["none"])[0].lower()
    history = [f"{d}|{ship(d)}|x|x|fixed_cctv" for d in others]
    return [get_creative_catalyst(recent_history=history) for _ in range(runs)]


class TestTornadoVessel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cats = _catalyst(T)
        assert all(c["domain_id"] == T for c in cls.cats)

    def test_city_beach_no_vessel(self):
        land = [c for c in self.cats if c["forced_environment"] not in RULE["environments"]]
        self.assertGreater(len(land), 100)
        for c in land:
            self.assertEqual(c["forced_ship"], "None", c["forced_environment"])
            self.assertNotIn(c["forced_event"], RULE["vessel_only_events"])

    def test_marina_harbor_gets_vessel(self):
        wet = [c for c in self.cats if c["forced_environment"] in RULE["environments"]]
        self.assertGreater(len(wet), 5)
        for c in wet:
            self.assertIn(c["forced_ship"], DOMAIN_ATTRIBUTES[T]["ships"])

    def test_both_marina_envs_seen(self):
        seen = {c["forced_environment"] for c in self.cats} & RULE["environments"]
        self.assertEqual(seen, RULE["environments"])

    def test_combo_key_with_none_is_current_universe(self):
        c = next(c for c in self.cats if c["forced_ship"] == "None")
        key = f"{T}|none|{c['forced_event'].lower()}|{c['forced_environment'].lower()}|fixed_cctv"
        self.assertTrue(is_current_universe_combo(key))


class TestOtherEnvCentric(unittest.TestCase):
    def test_urban_beach_always_none(self):
        for d in ("urban_city_disasters", "open_beach_coastal_events"):
            with self.subTest(domain=d):
                self.assertEqual({c["forced_ship"] for c in _catalyst(d, 50)}, {"None"})


class TestUniverseAndWriter(unittest.TestCase):
    def test_tornado_ships_still_in_universe(self):
        for s in DOMAIN_ATTRIBUTES[T]["ships"]:
            self.assertIn(s, VESSEL_UNIVERSE)

    def test_table_matches_pool(self):
        self.assertTrue(RULE["environments"] <= set(DOMAIN_ATTRIBUTES[T]["environments"]))
        self.assertTrue(RULE["vessel_only_events"] <= set(DOMAIN_ATTRIBUTES[T]["events"]))

    def test_writer_none_rule_is_general(self):
        s = build_scenario_writer_system(15, T)
        self.assertIn('If `vessel_class` is "None" (in ANY domain, including Coastal Tornado', s)
        self.assertNotIn("If the domain is Urban City Disasters or Open Beach Events, and", s)


if __name__ == "__main__":
    unittest.main()
