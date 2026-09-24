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

VESSEL_ROLE = re.compile(r"deckhand|ferry officer|cruise officer|car-deck|pool/deck", re.I)
VESSEL_TEXT = ("Clothing follows each person's role: deckhands, dockworkers, and technicians wear "
               "high-visibility orange or yellow PPE coveralls; officers and captains wear proper "
               "uniforms (ferry officer uniform, white cruise officer uniform); passengers, guests, "
               "and bystanders wear ordinary civilian clothing appropriate to the setting (swimwear, "
               "resort or casual wear, sun hats for pool/deck scenes; regular casual clothing for "
               "car-deck scenes) — never hi-vis PPE on civilians.")


class TestClothingByDomain(unittest.TestCase):
    def test_env_centric_no_vessel_roles(self):
        for d in ENV_CENTRIC_DOMAINS:
            for cam in CAMERA_ARCHETYPES:
                with self.subTest(domain=d, cam=cam):
                    out = apply_style_lock("A tornado tears across the beach", cam, {"domain_id": d, "forced_ship": "None"})
                    self.assertIsNone(VESSEL_ROLE.search(out), VESSEL_ROLE.search(out))
                    self.assertIn("never hi-vis PPE on civilians", out)
                    self.assertIn("Emergency responders", out)
                    self.assertNotIn("Marina and dock workers", out)

    def test_tornado_marina_adds_dock_workers(self):
        g = get_realism_guardrails("coastal_tornado_landfall", "Sailing Yacht")
        self.assertIn("Marina and dock workers wear high-visibility", g)
        self.assertIn("never hi-vis PPE on civilians", g)
        self.assertIsNone(VESSEL_ROLE.search(g))

    def test_vessel_domains_unchanged(self):
        for d in DOMAIN_CAST_RANGES:
            with self.subTest(domain=d):
                self.assertTrue(get_realism_guardrails(d, "Passenger Car Ferry").startswith(VESSEL_TEXT))

    def test_legacy_no_domain_keeps_vessel_text(self):
        self.assertTrue(get_realism_guardrails("", "").startswith(VESSEL_TEXT))
        self.assertIn(VESSEL_TEXT, apply_style_lock("x"))


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
