#!/usr/bin/env python3
"""
TUR 14 (2026-09-24): env-centric prompt'ta gemi rolü kıyafet gürültüsü yok (P2);
preflight/rewrite sistem prompt'ları "maritime CCTV" çerçevesinden arındı (P4). Gerçek API yok.
"""
import asyncio
import json
import os
import re
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.prompt_sanitizer as ps
from core.creative_engine import (
    CAMERA_ARCHETYPES,
    DOMAIN_CAST_RANGES,
    ENV_CENTRIC_DOMAINS,
    apply_style_lock,
    get_realism_guardrails,
)

VESSEL_ROLE = re.compile(r"deckhand|ferry officer|cruise officer|cruise uniform|car-deck|pool/deck|swimwear", re.I)
# TUR 24: kıyafet kuralı sadece o domain/ortamın rollerini taşır (tersaneye havuz/yolcu maddesi sızıyordu)
LEAK = re.compile(r"swimwear|resort|pool|passenger|cruise|ferry officer|car-deck", re.I)


class TestClothingByDomain(unittest.TestCase):
    def test_env_centric_no_vessel_roles(self):
        for d in ENV_CENTRIC_DOMAINS:
            for cam in CAMERA_ARCHETYPES:
                with self.subTest(domain=d, cam=cam):
                    out = apply_style_lock("A tornado tears across the beach", cam, {"domain_id": d, "forced_ship": "None"})
                    self.assertIsNone(VESSEL_ROLE.search(out), VESSEL_ROLE.search(out))
                    self.assertIn("never hi-vis PPE on civilians", out)
                    self.assertIn("emergency responders", out)
                    self.assertNotIn("Dock workers", out)

    def test_tornado_marina_adds_dock_workers(self):
        g = get_realism_guardrails("coastal_tornado_landfall", "Sailing Yacht")
        self.assertIn("Dock workers wear orange hi-vis PPE", g)
        self.assertIn("never hi-vis PPE on civilians", g)
        self.assertIsNone(VESSEL_ROLE.search(g))

    def test_shipyard_only_workers(self):
        for env in ("Construction slipway", "Drydock interior", "Shipyard basin"):
            with self.subTest(env=env):
                g = get_realism_guardrails("shipyard_and_drydock_engineering", "Sailing Yacht", env)
                self.assertIn("Shipyard workers wear orange hi-vis PPE", g)
                self.assertIsNone(LEAK.search(g), LEAK.search(g))

    def test_cruise_by_environment(self):
        onboard = get_realism_guardrails("cruise_ship_operations", "Mega Cruise Ship", "Sun deck")
        berth = get_realism_guardrails("cruise_ship_operations", "Mega Cruise Ship", "Cruise terminal berth")
        self.assertIn("swimwear", onboard)
        self.assertNotIn("swimwear", berth)
        self.assertIn("Dock crew wear orange hi-vis PPE", berth)

    def test_ferry_and_marina_roles(self):
        self.assertIn("drivers and passengers wear casual clothes",
                      get_realism_guardrails("ferry_operations", "Passenger Car Ferry", "Open vehicle deck"))
        m = get_realism_guardrails("marina_and_yacht_operations", "Sailing Yacht", "Floating pontoon dock")
        self.assertIn("Marina staff wear orange hi-vis PPE", m)
        self.assertIsNone(re.search(r"swimwear|cruise|ferry", m, re.I))

    def test_legacy_no_domain_generic_text(self):
        g = get_realism_guardrails("", "")
        self.assertIn("never hi-vis PPE on civilians", g)
        self.assertIn(g, apply_style_lock("x"))


class TestSafetyPromptContext(unittest.TestCase):
    BANNED = ["maritime CCTV", "MARITIME CONTEXT", "CCTV video prompt", "camera instructions", "CCTV prompt"]

    def test_system_prompts_neutral(self):
        for name in ("_PREFLIGHT_SYSTEM", "_RETRY_REWRITE_SYSTEM"):
            text = getattr(ps, name)
            for b in self.BANNED:
                with self.subTest(prompt=name, banned=b):
                    self.assertNotIn(b, text)
        self.assertIn("urban", ps._PREFLIGHT_SYSTEM)
        self.assertIn("tsunami flooding a city street", ps._PREFLIGHT_SYSTEM)

    def test_preflight_across_scenes(self):
        scenes = {
            "tornado": "A tornado tears across the open sandy beach, flinging chairs. Debris keeps swirling inland.",
            "city": "A tidal wave crashes over the coastal road, sweeping parked cars into storefronts.",
            "vessel": "The passenger car ferry rolls hard as four deckhands grab the rail. Cars keep sliding.",
        }
        safe = json.dumps({"safe": True, "risk_score": 2, "risk_reasons": []})
        for name, story in scenes.items():
            with self.subTest(scene=name):
                client = MagicMock()
                client.chat.completions.create = AsyncMock(return_value=SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content=safe))]))
                with patch("openai.AsyncOpenAI", return_value=client):
                    out, rewritten, meta = asyncio.run(ps.gpt_preflight_check(story))
                self.assertEqual((out, rewritten, meta["risk_score"]), (story, False, 2))
                msgs = client.chat.completions.create.await_args.kwargs["messages"]
                self.assertIn(story, msgs[1]["content"])
                self.assertNotIn("CCTV", msgs[1]["content"])


if __name__ == "__main__":
    unittest.main()
