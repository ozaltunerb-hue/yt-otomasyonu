#!/usr/bin/env python3
"""
TUR 17 (2026-09-24): K1 dry-run kalite bulguları.
I: ilk cümlede durağan insan (stand/watch/look...) red. J: insanlara senaryoda olmayan zarar fiili red.
Beat 3 zayıf büyüklük (ripples/gently/bobbing) red. Beat 1 fiil rotasyonu (Notion + koşu içi). Gerçek API yok.
"""
import asyncio
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.prompt_generator as pg
from config import settings
from core.creative_engine import build_prompt_simplifier_system, build_scenario_writer_system
from core.prompt_generator import validate_beat3_ongoing_danger, validate_simplified_prompt
from infrastructure.notion_logger import NotionTracker

D = "shipyard_and_drydock_engineering"
SHIP = "Luxury Motor Yacht"
SCEN = {"visible_start": "Water gushes into the drydock as three dockworkers in orange vests scramble back.",
        "physical_movement": "The luxury motor yacht rocks violently as the flood surges.",
        "visible_consequence": "The yacht keeps swaying while the dockworkers keep dashing along the wall.",
        "beat1_action_verb": "gushes"}


def fails(prompt, scen=SCEN, domain=D, ship=SHIP, prefix=""):
    return [f for f in validate_simplified_prompt(prompt, scen, domain, ship)[1] if f.startswith(prefix)]


I_ = "Simplifier: ilk cümlede durağan"
J_ = "Simplifier: insanlara yeni zarar"


class TestStaticHumans(unittest.TestCase):
    def test_k1_case4_rejected(self):
        p = ("Water gushes into the shipyard basin as three dockworkers in orange vests stand near the luxury "
             "motor yacht. The yacht rocks violently. The yacht keeps swaying as dockworkers dash.")
        self.assertTrue(fails(p, prefix=I_))

    def test_static_verbs(self):
        for v in ["stand", "standing", "watch", "watching", "look on", "stare", "pause", "wait", "observe"]:
            with self.subTest(verb=v):
                p = f"Water gushes into the drydock, three dockworkers {v} by the luxury motor yacht. The yacht keeps swaying."
                self.assertTrue(fails(p, prefix=I_))

    def test_not_static(self):
        for p in ["Water gushes into the drydock as three dockworkers scramble back from the luxury motor yacht. The yacht keeps swaying.",
                  "Water gushes over standing water around the luxury motor yacht as three dockworkers brace. The yacht keeps swaying.",
                  "Three dockworkers brace as the luxury motor yacht, standing on its blocks, gushes water. The yacht keeps swaying.",
                  "Water gushes into the drydock around the luxury motor yacht. Three dockworkers watch from the wall. The yacht keeps swaying."]:
            with self.subTest(p=p[:50]):
                self.assertFalse(fails(p, prefix=I_))


class TestHarmDrift(unittest.TestCase):
    FERRY = {"visible_start": "Water gushes across the vehicle deck of the high-speed catamaran, setting three crew members into action.",
             "physical_movement": "The water pushes two cars sideways as the crew members struggle.",
             "visible_consequence": "Both cars keep sliding while the crew members keep grabbing ropes.",
             "beat1_action_verb": "gushes"}

    def test_k1_case1_rejected(self):
        p = ("Water gushes across the vehicle deck of the high-speed catamaran, sweeping three crew members into action. "
             "Cars keep sliding.")
        f = fails(p, self.FERRY, "ferry_operations", "High-speed Catamaran", J_)
        self.assertEqual(len(f), 1)
        self.assertIn("sweeping three crew members", f[0])

    def test_same_stem_allowed(self):
        scen = {**self.FERRY, "physical_movement": "The surge knocking two passengers off their feet."}
        p = "Water gushes across the high-speed catamaran's deck and knocks two passengers down. Cars keep sliding."
        self.assertFalse(fails(p, scen, "ferry_operations", "High-speed Catamaran", J_))

    def test_objects_not_people(self):
        for p in ["Water gushes across the high-speed catamaran's deck, sweeping two cars sideways. Cars keep sliding.",
                  "A tornado tears across the beach, flinging chairs past distant beachgoers. Debris keeps swirling."]:
            with self.subTest(p=p[:40]):
                self.assertFalse(fails(p, self.FERRY, "ferry_operations", "High-speed Catamaran", J_))

    def test_irregular_forms(self):
        scen = {**self.FERRY, "physical_movement": "A wave sweeps two deckhands against the rail."}
        p = "Water gushes across the high-speed catamaran as the wave swept two deckhands against the rail. Cars keep sliding."
        self.assertFalse(fails(p, scen, "ferry_operations", "High-speed Catamaran", J_))


class TestWeakBeat3(unittest.TestCase):
    def test_weak_rejected(self):
        for end in ["Still accelerating, it continues causing ripples that rock nearby boats.",
                    "The jet ski keeps bobbing gently in the water.",
                    "The hull continues to list slightly."]:
            with self.subTest(end=end):
                ok, f = validate_beat3_ongoing_danger({"visible_consequence": end})
                self.assertFalse(ok)
                self.assertIn("zayıf büyüklük", f[0])

    def test_halt_and_gesture_not_ongoing(self):
        # K1 dry-run 2 #2: tehlike duruyor, sadece insan jesti "still" ile sürüyor
        ok, f = validate_beat3_ongoing_danger(
            {"visible_consequence": "It accelerates with loud scraping, then abruptly halts halfway, workers still gesturing anxiously."})
        self.assertFalse(ok)
        self.assertIn("halt", f[0])
        ok, f = validate_beat3_ongoing_danger({"visible_consequence": "The yacht sits on the blocks, workers still gesturing."})
        self.assertFalse(ok)

    def test_strong_pass(self):
        for end in ["The yacht keeps rocking violently against the pontoon.", "The cars keep sliding toward the edge."]:
            with self.subTest(end=end):
                self.assertTrue(validate_beat3_ongoing_danger({"visible_consequence": end})[0])


class TestRules(unittest.TestCase):
    def test_writer_and_simplifier(self):
        self.assertIn("never standing, watching, looking, or waiting", build_scenario_writer_system(15, D))
        s = build_prompt_simplifier_system(15, D)
        self.assertIn("static people (standing, watching, looking, waiting)", s)
        self.assertIn("keep the scenario's own verbs for them", s)


class TestVerbRotation(unittest.TestCase):
    CAT = {"domain_id": D, "domain_title": "t", "guidance": "g", "example_elements": [], "camera_styles": [],
           "forced_ship": SHIP, "forced_event": "e", "forced_environment": "x"}

    def user_msg(self, verbs):
        mock = AsyncMock(return_value={})
        with patch.object(pg, "_call_gpt", mock):
            asyncio.run(pg._generate_scenario({**self.CAT, "recent_verbs": verbs}, "fixed_cctv"))
        return mock.call_args.args[1]

    def test_line_added(self):
        msg = self.user_msg(["lurches", "crashes"])
        self.assertIn("RECENTLY USED OPENING VERBS", msg)
        self.assertIn("lurches, crashes", msg)

    def test_no_line_when_empty(self):
        self.assertNotIn("RECENTLY USED OPENING VERBS", self.user_msg([]))

    def test_in_run_accumulation(self):
        seen = []

        async def fake(cat, cam):
            seen.append(list(cat["recent_verbs"]))
            return {"beat1_action_verb": f"verb{len(seen)}"}

        with patch.object(pg, "_generate_scenario", side_effect=fake), \
             patch.object(pg, "validate_silent_visibility", return_value=(False, ["x"])):
            with self.assertRaises(pg.NoValidScenarioError):
                asyncio.run(pg.generate_prompts({"used_combos": [], "recent_topics": [], "recent_verbs": ["lurches"]}))
        self.assertEqual(seen[0], ["lurches"])
        self.assertEqual(seen[2], ["verb2", "verb1", "lurches"])

    def test_notion_read(self):
        page = lambda v: {"properties": {"Beat1 Fiil": {"rich_text": [{"plain_text": v}]}}}
        t = NotionTracker()
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(t, "enabled", True), \
             patch("infrastructure.notion_logger._notion_request",
                   return_value={"results": [page("Lurches"), page("crashes")]}) as req:
            self.assertEqual(t.get_recent_beat1_verbs(limit=10), ["lurches", "crashes"])
        self.assertEqual(req.call_args.kwargs["json"]["page_size"], 10)

    def test_notion_write(self):
        t = NotionTracker()
        with patch.object(t, "update_status") as upd:
            t.update_with_prompts({"scenes": [{"prompt": "p"}], "beat1_action_verb": "slams"})
        extra = upd.call_args.args[1]
        self.assertEqual(extra["Beat1 Fiil"]["rich_text"][0]["text"]["content"], "slams")


if __name__ == "__main__":
    unittest.main()
