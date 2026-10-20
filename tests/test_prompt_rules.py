#!/usr/bin/env python3
"""Prompt kural denetimi cırcırı (21 Eki 2026, Gece 1 / Aşama 2).

Mevcut koddan yapılandırılmış hattın her aktif olayı için 20 tohumla son prompt kurulur (scripts/prompt_snapshot.py:
GPT yok, kod yedeği hikâyesi; Kie/Notion yok) ve K1-K5 denetlenir (scripts/prompt_rules.py). Bugünkü ihlaller
tests/snapshots/rules_known_violations.json'da (kural -> olaylar). Test:
- YENİ bir (kural, olay) ihlali çıkarsa başarısız (geri kayma),
- listede olup artık ihlal etmeyen kayıt varsa başarısız (düzeltildi: listeden sil, cırcır bir diş ilerler).
"""
import json
import logging
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_rules as pr   # noqa: E402
import prompt_snapshot as ps   # noqa: E402


def _current_pairs() -> dict:
    logging.disable(logging.WARNING)
    try:
        return pr.known_pairs(pr.evaluate(ps.snapshot_all()))
    finally:
        logging.disable(logging.NOTSET)


class TestPromptRulesRatchet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(pr.KNOWN, encoding="utf-8") as f:
            cls.known = json.load(f)
        cls.now = _current_pairs()

    def test_no_new_violation(self):
        for rule in pr.RULES:
            with self.subTest(rule=rule):
                new = sorted(set(self.now[rule]) - set(self.known.get(rule, [])))
                self.assertEqual(new, [], f"{rule} ({pr.RULE_NAMES[rule]}) YENİ ihlal: {new}")

    def test_no_stale_known_violation(self):
        for rule in pr.RULES:
            with self.subTest(rule=rule):
                fixed = sorted(set(self.known.get(rule, [])) - set(self.now[rule]))
                self.assertEqual(fixed, [], f"{rule} artık ihlal etmiyor, rules_known_violations.json'dan sil: {fixed}")

    def test_known_file_lists_only_active_events(self):
        active = set(ps.active_events())
        for rule in pr.RULES:
            self.assertTrue(set(self.known.get(rule, [])) <= active, rule)


class TestRuleChecks(unittest.TestCase):
    """Kural fonksiyonlarının kendisi (sabit metinlerle)."""
    CAM_LOW = ("Handheld footage shot by a person standing on a sidewalk across the street, eye level, normal lens; "
               "slight hand shake, the camera pans to follow the waist-high wall of brown muddy floodwater; no zoom, "
               "no cuts. Bystanders wear civilian clothes.")
    CAM_HIGH = ("Handheld footage from a rooftop terrace, high vantage looking across the street; the camera stays "
                "fixed and never descends; one continuous shot, no zoom, no cuts. Raw natural light.")

    def item(self, suffix, story="0-4s: A thing happens."):
        return {"style_suffix": suffix, "prompt": f"{story} {suffix}"}

    def test_camera_sentence_stops_at_no_cuts(self):
        self.assertTrue(pr.camera_sentence(self.CAM_LOW).endswith("no zoom, no cuts."))
        self.assertNotIn("Bystanders", pr.camera_sentence(self.CAM_LOW))

    def test_low_following_camera_violates_k1_k2_k3(self):
        out = pr.check("Flash flooding in city streets", self.item(self.CAM_LOW))
        self.assertEqual(set(out), {"K1", "K2", "K3"})
        self.assertIn("eye level", out["K1"])
        self.assertIn("sidewalk", out["K1"])

    def test_waist_high_is_not_height(self):
        self.assertEqual(pr._has(pr.HEIGHT_TERMS, "the waist-high wall"), [])
        self.assertEqual(pr._has(pr.HEIGHT_TERMS, "a high-rise district"), [])
        self.assertEqual(pr._has(pr.HEIGHT_TERMS, "high vantage"), ["high", "vantage"])

    def test_high_fixed_camera_passes(self):
        self.assertEqual(pr.check("Volcanic bombs slam into a village street", self.item(self.CAM_HIGH)), {})

    def test_k4_rain_only_volcano(self):
        story = "0-4s: Ash rains down. Rocks rain."
        self.assertIn("K4", pr.check("Volcanic bombs slam into a village street", self.item(self.CAM_HIGH, story)))
        self.assertNotIn("K4", pr.check("Mudslide pours down a hillside street", self.item(self.CAM_HIGH, story)))
        self.assertNotIn("K4", pr.check("Volcanic bombs slam into a village street",
                                        self.item(self.CAM_HIGH, "0-4s: The terrain drains.")))

    def test_k5_word_limit(self):
        long = "0-4s: " + "word " * 175
        self.assertIn("K5", pr.check("Volcanic bombs slam into a village street", self.item(self.CAM_HIGH, long)))

    def test_build_error_counts_everywhere(self):
        self.assertEqual(set(pr.check("x", {"error": "StructureError: y"})), set(pr.RULES))


if __name__ == "__main__":
    unittest.main()
