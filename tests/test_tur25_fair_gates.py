#!/usr/bin/env python3
"""
TUR 25 (2026-09-27): Tersane üretimi "5 senaryo kapıdan geçemedi" ile düştü. Ret sebepleri tek tek
ayrıldı: haksız retler düzeltildi, gerçek sorunlar (settle/stabilize, izleyerek bitiş, kamera
anlatımıyla bitiş) aynen reddedilmeye devam eder. Telegram'a deneme başına tek satır özet gider.
Gerçek API yok.
"""
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.prompt_generator import NoValidScenarioError, validate_beat3_ongoing_danger, validate_visible_trigger

# Notion ❌ Hata kaydı, 2026-09-26 20:57 (Railway üretimi)
REAL_ATTEMPTS = [
    {"attempt": 1, "combo_key": "a", "failures": [
        "Beat 3 son 12 kelimede hareket yok: 'from any potential backlash of water and debris, still visibly in motion'"]},
    {"attempt": 2, "combo_key": "b", "failures": ["Beat 3 tehlike çözülmüş/sakinleşmiş bitiyor: ['safe']"]},
    {"attempt": 3, "combo_key": "c", "failures": ["Beat 3 tehlike çözülmüş/sakinleşmiş bitiyor: ['settle', 'stabilize']"]},
    {"attempt": 4, "combo_key": "d", "failures": [
        "Beat 3 son 12 kelimede hareket yok: 'the dockworkers looking on as it nears the edge of the slipway'"]},
    {"attempt": 5, "combo_key": "e", "failures": [
        "Beat 3 son 12 kelimede hareket yok: 'the scene capturing the chaotic motion of the ferry still in jeopardy'",
        "ikinci sebep"]},
]


def ok(text):
    return validate_beat3_ongoing_danger({"visible_consequence": text})[0]


class TestUnfairRejectsFixed(unittest.TestCase):
    def test_still_in_motion_is_ongoing(self):
        """#1: 'still visibly in motion' devam işareti."""
        self.assertTrue(ok("The yacht races down the rails, workers diving clear from any potential backlash of "
                           "water and debris, still visibly in motion."))
        for t in ["The hull slides down the rails, still in motion.",
                  "The hull slides down the rails and the shattered cradle is still visibly moving."]:
            with self.subTest(t=t):
                self.assertTrue(ok(t))

    def test_safe_distance_is_escape_not_resolution(self):
        """#2: 'scramble to a safe distance' kaçışın hedefi, çözülmüş son değil."""
        for t in ["The hull keeps dropping into the basin as workers scramble to a safe distance.",
                  "The ferry hull keeps swinging as workers sprint toward a safe spot."]:
            with self.subTest(t=t):
                self.assertTrue(ok(t))

    def test_really_safe_still_rejected(self):
        for t in ["The hull drops as workers are safe now.", "Everyone is safe.",
                  "The crew safely secure the hull as it keeps swinging."]:
            with self.subTest(t=t):
                self.assertFalse(ok(t))

    def test_heavy_roll_is_a_trigger(self):
        """Kruvaziyer #5: 'heavy roll' kendi olay havuzumuzdaki tetik."""
        sc = {"visible_start": "The cruise liner experiences a heavy roll, sending loungers sliding.",
              "physical_movement": "Loungers slide toward the rail.",
              "visible_trigger": "The cruise liner experiences a heavy roll"}
        self.assertEqual(validate_visible_trigger(sc, "cruise_ship_operations"), (True, []))


class TestRealProblemsStillRejected(unittest.TestCase):
    def test_settle_stabilize(self):
        self.assertFalse(ok("The hull tips further as crew rush to stabilize it before it settles."))

    def test_watching_ending(self):
        self.assertFalse(ok("The yacht tilts on the rails, with the dockworkers looking on as it nears the edge "
                            "of the slipway."))

    def test_camera_narration_ending(self):
        self.assertFalse(ok("Water floods the dock, the scene capturing the chaotic motion of the ferry still in "
                            "jeopardy."))


class TestShortSummary(unittest.TestCase):
    def test_one_line_per_attempt(self):
        err = NoValidScenarioError("5 senaryo denemesi kalite kapısından geçemedi. Bu tur video üretilmedi. "
                                   "Denemeler: [...]", attempts=REAL_ATTEMPTS)
        lines = err.short_summary().split("\n")
        self.assertEqual(lines[0], "5 senaryo denemesi kalite kapısından geçemedi. Bu tur video üretilmedi.")
        self.assertEqual(lines[1:], [
            "#1 Beat 3 son 12 kelimede hareket yok",
            "#2 Beat 3 tehlike çözülmüş/sakinleşmiş bitiyor: ['safe']",
            "#3 Beat 3 tehlike çözülmüş/sakinleşmiş bitiyor: ['settle', 'stabilize']",
            "#4 Beat 3 son 12 kelimede hareket yok",
            "#5 Beat 3 son 12 kelimede hareket yok (+1)",
        ])

    def test_long_reason_truncated(self):
        err = NoValidScenarioError("x", attempts=[{"attempt": 1, "failures": ["A" * 300]}])
        self.assertLessEqual(len(err.short_summary().split("\n")[1]), 95)

    def test_no_attempts_falls_back_to_message(self):
        self.assertEqual(NoValidScenarioError("kısa").short_summary(), "kısa")

    def test_main_returns_summary_and_bot_sends_it(self):
        import bot
        from test_pipeline_flow import run
        err = NoValidScenarioError("5 senaryo denemesi kalite kapısından geçemedi. Denemeler: [...]",
                                   attempts=REAL_ATTEMPTS)
        r = run(gen=AsyncMock(side_effect=err))
        self.assertEqual(r.result["reason"], "no_valid_scenario")
        self.assertEqual(r.result["error_summary"], err.short_summary())

        sent = AsyncMock()
        fake_bot = MagicMock(send_message=sent)
        res = {"success": False, "reason": "no_valid_scenario", "error": "Denemeler: " + "x" * 5000,
               "error_summary": err.short_summary()}
        with patch.object(bot, "_run_pipeline_blocking", return_value=res), \
             patch.object(bot.status, "data", {"state": "failed"}):
            asyncio.run(bot.produce(fake_bot, 1, "shipyard_and_drydock_engineering"))
        text = sent.call_args.args[1]
        self.assertIn("#3 Beat 3 tehlike çözülmüş/sakinleşmiş bitiyor: ['settle', 'stabilize']", text)
        self.assertNotIn("xxxx", text)


if __name__ == "__main__":
    unittest.main()
