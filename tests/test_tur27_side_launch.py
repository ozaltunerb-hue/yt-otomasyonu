#!/usr/bin/env python3
"""
TUR 27 (2026-09-27): Tersane domain'i yandan suya indirme (side launch) üzerine kuruldu.
Feribot, karşı rıhtımdan sabit kamera, tek hızlı hareket, dalga karşı rıhtıma vurur ve insanlar kaçar.
Gerçek API yok.
"""
import asyncio
import collections
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.prompt_generator as pg
from core.creative_engine import (
    SIDE_LAUNCH_ENV,
    SIDE_LAUNCH_EVENT,
    choose_camera_archetype,
    get_creative_catalyst,
    style_lock_suffix,
)
from core.prompt_generator import scenario_gate_results

D = "shipyard_and_drydock_engineering"
CAT = {"domain_id": D, "forced_ship": "Passenger Car Ferry", "forced_event": SIDE_LAUNCH_EVENT,
       "forced_environment": SIDE_LAUNCH_ENV}
COMBO = f"{D}|passenger car ferry|{SIDE_LAUNCH_EVENT.lower()}|{SIDE_LAUNCH_ENV.lower()}|fixed_cctv"

GOOD = {
    "scenario_summary": "The passenger car ferry slides sideways off the side-launch rails, crashes into the basin "
                        "and throws a huge wave onto the opposite quay.",
    "visible_start": "The passenger car ferry slides sideways off the side-launch rails as the holding ropes snap "
                     "and six workers in orange coveralls sprint clear.",
    "visible_trigger": "the holding ropes snap",
    "beat1_action_verb": "slides",
    "physical_movement": "The passenger car ferry crashes broadside into the basin, heeling violently and throwing "
                         "up a wall of water.",
    "visible_consequence": "The ferry keeps rolling hard as the huge wave slams onto the opposite quay and the six "
                           "workers run back from the edge.",
}


class TestSelection(unittest.TestCase):
    def test_mostly_side_launch_always_ferry(self):
        c = collections.Counter()
        for _ in range(1000):
            k = get_creative_catalyst(domain=D)
            if k["forced_event"] == SIDE_LAUNCH_EVENT:
                c["side"] += 1
                self.assertEqual(k["forced_ship"], "Passenger Car Ferry")
                self.assertEqual(k["forced_environment"], SIDE_LAUNCH_ENV)
            else:
                self.assertNotEqual(k["forced_environment"], SIDE_LAUNCH_ENV)
        self.assertGreater(c["side"], 550)   # beklenen ~%71
        self.assertLess(c["side"], 900)      # diğer olaylar tamamen kaybolmaz

    def test_repeatable_despite_history(self):
        """Side launch son 5 tersane üretiminin hepsi olsa da seçilmeye devam eder (dedup/ceza muaf)."""
        hist = [COMBO] * 5
        n = sum(get_creative_catalyst(recent_history=hist, domain=D)["forced_event"] == SIDE_LAUNCH_EVENT
                for _ in range(300))
        self.assertGreater(n, 150)

    def test_camera_only_cctv_or_handheld(self):
        self.assertEqual({choose_camera_archetype(D, SIDE_LAUNCH_ENV) for _ in range(300)},
                         {"fixed_cctv", "bystander_handheld"})

    def test_generate_prompts_not_blocked_by_60_day_dedup(self):
        """used_combos'ta olsa bile side launch combo'su kullanılır (2 combo'luk olay 60 gün kilitlenmez)."""
        side_cat = {**CAT, "domain_title": "t", "guidance": "g", "example_elements": [], "camera_styles": [],
                    "existing_library_reference": [], "recent_history": []}
        calls = AsyncMock(return_value={})
        used = [f"{D}|passenger car ferry|{SIDE_LAUNCH_EVENT.lower()}|{SIDE_LAUNCH_ENV.lower()}|{c}"
                for c in ("fixed_cctv", "bystander_handheld")]
        with patch.object(pg.settings, "IS_DRY_RUN", False), \
             patch.object(pg, "get_creative_catalyst", side_effect=lambda **k: dict(side_cat)) as gcc, \
             patch.object(pg, "_generate_scenario", calls):
            with self.assertRaises(pg.NoValidScenarioError) as cm:
                asyncio.run(pg.generate_prompts({"used_combos": list(used), "domain": D}))
        self.assertEqual(gcc.call_count, 5)   # deneme başına 1 çağrı: dedup döngüsü dönmedi
        self.assertTrue(all(SIDE_LAUNCH_EVENT.lower() in a["combo_key"] for a in cm.exception.attempts))


class TestPrompts(unittest.TestCase):
    def test_suffix(self):
        for cam in ("fixed_cctv", "bystander_handheld"):
            with self.subTest(cam=cam):
                s = style_lock_suffix(cam, CAT)
                self.assertLessEqual(len(s.split()), 115)
                self.assertIn("Filmed from the opposite quay across the basin", s)
                self.assertIn("One continuous fast motion, no slow start; the hull is already sliding in the first frame", s)
                self.assertIn("side-launch rails parallel to the basin edge", s)
                self.assertIn("Spectators on the opposite quay run back as the wave hits.", s)
                self.assertNotIn("Already moving in the first frame", s)   # genel hareket satırının yerine geçer
                self.assertNotIn("by hand", s)

    def test_writer_gets_beat_plan(self):
        mock = AsyncMock(return_value={})
        base = {"domain_title": "t", "guidance": "g", "example_elements": [], "camera_styles": []}
        with patch.object(pg, "_call_gpt", mock):
            asyncio.run(pg._generate_scenario({**base, **CAT}, "fixed_cctv"))
        user = mock.call_args.args[1]
        self.assertIn("BEAT PLAN (MANDATORY): BEAT 1: the timber blocks and holding ropes have already given way", user)
        self.assertIn("the spectators there turn and run back", user)


class TestGate(unittest.TestCase):
    def test_good_passes(self):
        gates = scenario_gate_results(GOOD, CAT)
        self.assertEqual({k: v for k, v in gates.items() if not v[0]}, {})

    def test_flee_ending_counts_as_motion(self):
        self.assertTrue(pg.validate_beat3_ongoing_danger(
            {"visible_consequence": "The wave slams onto the opposite quay and the four workers run back from the edge."})[0])

    def test_crowd_allowed_only_for_side_launch(self):
        """K1 dry-run: 'about twenty spectators' tersane aralığını (2-5) aşıp eleniyordu; side launch 5-20."""
        sc = {**GOOD, "visible_start": "The passenger car ferry slides sideways off the rails as about twenty "
                                       "spectators on the opposite quay scramble back."}
        self.assertTrue(pg.validate_cast_size(sc, D, SIDE_LAUNCH_EVENT)[0])
        self.assertFalse(pg.validate_cast_size(sc, D, "Drydock flood gate bursts open")[0])
        from core.creative_engine import build_scenario_writer_system
        self.assertIn("approximately 5-20 people", build_scenario_writer_system(15, D, SIDE_LAUNCH_EVENT))
        self.assertIn("approximately 2-5 people", build_scenario_writer_system(15, D))

    def test_race_and_sprint_are_action(self):
        """K1 dry-run simplifier: '...forcing about five spectators to sprint back' devam eden aksiyon."""
        self.assertTrue(pg.validate_beat3_ongoing_danger(
            {"visible_consequence": "The wave races across the basin, forcing about five spectators to sprint back "
                                    "from the impact."})[0])

    def test_still_in_adjective_motion(self):
        """K1 dry-run: 'still in heightened motion' (TUR 25'teki 'still in motion' ile aynı sınıf)."""
        self.assertTrue(pg.validate_beat3_ongoing_danger(
            {"visible_consequence": "The yacht careens toward the water, still in heightened motion as the yacht's "
                                    "bow nears the open water."})[0])
        self.assertFalse(pg.validate_beat3_ongoing_danger(
            {"visible_consequence": "Workers maintain their grip and the yacht remains in a precarious, unstable "
                                    "position."})[0])

    def test_no_wave_on_quay(self):
        sc = {**GOOD, "visible_consequence": "The ferry keeps rolling hard as the four workers run back."}
        ok, f = gates_physics(sc)
        self.assertFalse(ok)
        self.assertIn("dalga", " ".join(f))

    def test_spectators_only_watch(self):
        sc = {**GOOD, "visible_consequence": "The ferry keeps rolling hard as the huge wave slams onto the opposite "
                                             "quay in front of the four workers."}
        ok, f = gates_physics(sc)
        self.assertFalse(ok)
        self.assertIn("kaçmıyor", " ".join(f))

    def test_other_events_not_checked(self):
        cat = {**CAT, "forced_event": "Drydock flood gate bursts open", "forced_environment": "Drydock interior"}
        sc = {**GOOD, "visible_consequence": "The yacht keeps tilting as water floods in."}
        self.assertTrue(pg.validate_scene_physics(sc, cat)[0])


def gates_physics(sc):
    return pg.validate_scene_physics(sc, CAT)


if __name__ == "__main__":
    unittest.main()
