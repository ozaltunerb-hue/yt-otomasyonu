#!/usr/bin/env python3
"""
Simplifier çıktı kapısı (validate_simplified_prompt / simplify_with_gate), 2026-09-24 TUR 5.

Fixture: Faz 1 ölçüm dry-run'ının 20 gerçek simplifier çıktısı (10 senaryo × 2).
Beklenen: 7 red (A Beat 3: 2, C Beat 1 fiili: 3, E kişi sayısı: 4; bazıları çakışıyor).
Gerçek API çağrısı yapılmaz; _call_gpt mock'lanır.
"""
import asyncio
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.prompt_generator as pg
from core.prompt_generator import (
    NoValidScenarioError,
    simplify_with_gate,
    validate_beat3_ongoing_danger,
    validate_simplified_prompt,
)

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "simplifier_outputs.json")
LETTER = {"Simplifier son cümle": "A", "Simplifier: kamera": "B", "Simplifier: Beat 1 fiili": "C",
          "Simplifier: kişi sayısı": "E", "Simplifier: boş": "EMPTY"}


def letters(failures):
    return sorted({v for f in failures for k, v in LETTER.items() if f.startswith(k)})


SHIPYARD = {
    "scenario_summary": "Keel blocks give way under a vessel on the slipway.",
    "visible_start": "Keel blocks crack under the hull as three workers in orange coveralls leap back.",
    "physical_movement": "The vessel lurches sideways off the blocks, scraping the slipway rails.",
    "visible_consequence": "The hull keeps sliding toward the water as the three workers are still scrambling clear.",
    "beat1_action_verb": "crack",
}
GOOD = ("Keel blocks crack under the hull as three workers in orange coveralls leap back. "
        "The vessel lurches sideways, scraping the rails. The hull keeps sliding toward the water.")


class TestRealOutputs(unittest.TestCase):
    def test_faz1_twenty_outputs(self):
        rows = json.load(open(FIXTURE, encoding="utf-8"))
        self.assertEqual(len(rows), 20)
        self.assertEqual(sum(1 for r in rows if r["expect"]), 7)
        for r in rows:
            with self.subTest(tag=r["tag"]):
                ok, failures = validate_simplified_prompt(r["prompt"], r["scenario"], r["domain"])
                self.assertEqual(letters(failures), sorted(r["expect"]), failures)
                self.assertEqual(ok, not r["expect"])

    def test_n14b_watch_ending(self):
        """Önceki oturum r9#5: 'continues to thrash' işareti var ama izleyerek bitiyor."""
        prompt = ("The mooring line on a luxury motor yacht vibrates and snaps, whipping violently toward the dock. "
                  "Three people duck, covering their heads in alarm. "
                  "The line continues to thrash, tangling around a piling as they watch.")
        scen = {"visible_start": "Three people stand on the dock as the mooring line strains against the cleat."}
        ok, failures = validate_simplified_prompt(prompt, scen, "marina_and_yacht_operations")
        self.assertEqual(letters(failures), ["A"])


class TestChecks(unittest.TestCase):
    D = "shipyard_and_drydock_engineering"

    def test_good_prompt_passes(self):
        self.assertEqual(validate_simplified_prompt(GOOD, SHIPYARD, self.D), (True, []))

    def test_verb_any_tense(self):
        p = GOOD.replace("Keel blocks crack", "Keel blocks cracking")
        self.assertTrue(validate_simplified_prompt(p, SHIPYARD, self.D)[0])

    def test_time_compression_rejected(self):
        p = ("The vessel lurches sideways off the blocks as three workers in orange coveralls leap back. "
             "The hull keeps sliding toward the water.")
        self.assertEqual(letters(validate_simplified_prompt(p, SHIPYARD, self.D)[1]), ["C"])

    def test_camera_subject_rejected(self):
        p = "The camera captures keel blocks that crack as three workers in orange coveralls leap back. " + GOOD.split(". ", 1)[1]
        self.assertIn("B", letters(validate_simplified_prompt(p, SHIPYARD, self.D)[1]))

    def test_count_changed_or_added(self):
        dropped = GOOD.replace("three workers", "workers")
        changed = GOOD.replace("three workers", "five workers")
        added = GOOD.replace("The hull keeps sliding", "Six workers watch as the hull keeps sliding")
        for p in (dropped, changed, added):
            with self.subTest(p=p[:60]):
                self.assertIn("E", letters(validate_simplified_prompt(p, SHIPYARD, self.D)[1]))

    def test_hedged_scenario_count_matches_plain(self):
        scen = {**SHIPYARD, "visible_start": "Keel blocks crack as about three workers leap back."}
        self.assertTrue(validate_simplified_prompt(GOOD, scen, self.D)[0])

    def test_env_centric_skips_count(self):
        scen = {"visible_start": "A tornado tears across the beach.", "beat1_action_verb": "tears"}
        p = "A tornado tears across the beach, flinging chairs. Debris keeps swirling inland."
        self.assertTrue(validate_simplified_prompt(p, scen, "open_beach_coastal_events")[0])

    def test_empty_prompt(self):
        self.assertEqual(letters(validate_simplified_prompt("", SHIPYARD, self.D)[1]), ["EMPTY"])

    def test_scenario_beat3_gate_watch_ending(self):
        ok, failures = validate_beat3_ongoing_danger(
            {"visible_consequence": "The line keeps whipping across the quay as the crew watches."})
        self.assertFalse(ok)
        self.assertIn("izleyerek bitiş", failures[0])
        self.assertTrue(validate_beat3_ongoing_danger(
            {"visible_consequence": "The line keeps whipping as the crew watches it, still lashing the bollard."})[0])


def _cand(score, scenario=SHIPYARD, domain="shipyard_and_drydock_engineering"):
    return {"scenario": scenario, "catalyst": {"domain_id": domain}, "score": score}


class TestSimplifyWithGate(unittest.TestCase):
    def run_gate(self, responses, candidates):
        mock = AsyncMock(side_effect=[{"prompt": p} for p in responses])
        with patch.object(pg, "_call_gpt", mock):
            result = asyncio.run(simplify_with_gate(candidates))
        return result, mock

    def test_retry_with_feedback(self):
        bad = GOOD.replace("three workers", "workers")
        (cand, simp, attempts), mock = self.run_gate([bad, GOOD], [_cand(5)])
        self.assertEqual(simp["prompt"], GOOD)
        self.assertEqual(len(attempts), 2)
        second_user_msg = mock.call_args_list[1].args[1]
        self.assertIn("YOUR PREVIOUS ATTEMPT WAS REJECTED", second_user_msg)
        self.assertIn("three workers", second_user_msg)
        self.assertNotIn("PREVIOUS ATTEMPT", mock.call_args_list[0].args[1])

    def test_next_candidate_after_retries(self):
        bad = GOOD.replace("three workers", "workers")
        other = {**SHIPYARD, "scenario_summary": "second"}
        (cand, simp, attempts), mock = self.run_gate([bad, bad, bad, GOOD], [_cand(3, other), _cand(9)])
        self.assertEqual(cand["score"], 3)          # önce skor 9 denendi, 3 retry'da kaldı
        self.assertEqual(len(attempts), 4)
        self.assertEqual(mock.call_count, 4)

    def test_all_fail_raises(self):
        with self.assertRaises(NoValidScenarioError):
            self.run_gate(["", "", ""], [_cand(5)])

    def test_empty_gpt_response_has_no_fallback(self):
        mock = AsyncMock(return_value={})
        with patch.object(pg, "_call_gpt", mock):
            result = asyncio.run(pg._simplify_prompt(SHIPYARD, {"domain_id": "open_beach_coastal_events"}))
        self.assertEqual(result["prompt"], "")


if __name__ == "__main__":
    unittest.main()
