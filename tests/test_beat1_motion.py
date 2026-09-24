#!/usr/bin/env python3
"""
Beat 1 görsel hareket (2026-09-24, TUR 9).

Video 2: "The vessel lurches forward on the slipway, startling three workers" → Kie işçileri
4 sn donuk çizdi, gemi önce kameraya sonra ters yöne gitti. Düzeltmeler:
(a) yazıcı: Beat 1 = aksiyon + fiziksel etki, tepki sonra, tek yön;
(b) simplifier kuralı + G kapısı: ilk cümlede duygusal tepki yok;
(d) stil kilidi: tüm arketiplerde "hareket ilk karede başlamış";
ölçüm: infrastructure/motion_profile (ffmpeg). Gerçek API çağrısı yok.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.creative_engine import (
    CAMERA_ARCHETYPES,
    DOMAIN_CAST_RANGES,
    ENV_CENTRIC_DOMAINS,
    apply_style_lock,
    build_prompt_simplifier_system,
    build_scenario_writer_system,
)
from core.prompt_generator import validate_simplified_prompt
from infrastructure.motion_profile import format_motion, motion_profile, summarize

D = "shipyard_and_drydock_engineering"
SCEN = {"visible_start": "The sailing yacht lurches down the slipway as three workers leap back.",
        "beat1_action_verb": "lurches"}
GOOD = ("The sailing yacht lurches down the slipway, keel blocks splintering beneath the hull. "
        "Three workers in orange coveralls leap back. The yacht keeps sliding toward the water.")
VIDEO2 = ("The sailing yacht lurches forward on the slipway, startling three workers in orange coveralls. "
          "It accelerates, hull scraping the supports. The yacht continues thundering down.")
MOTION = "Motion is already under way in the very first frame"


def G(failures):
    return [f for f in failures if f.startswith("Simplifier: ilk cümlede insan tepkisi")]


class TestRules(unittest.TestCase):
    def test_writer_rule_all_domains(self):
        for d in list(DOMAIN_CAST_RANGES) + ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                s = build_scenario_writer_system(15, d)
                self.assertIn("visible_start pairs the trigger action with a visible physical effect", s)
                self.assertIn("ONE direction relative to the camera", s)

    def test_simplifier_rule(self):
        for d in list(DOMAIN_CAST_RANGES) + ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                s = build_prompt_simplifier_system(15, d)
                self.assertIn("Never put human emotional reactions", s)
                self.assertIn("Keep ONE movement direction", s)

    def test_style_lock_every_archetype(self):
        for cam in CAMERA_ARCHETYPES:
            for d in (D, "urban_city_disasters"):
                with self.subTest(camera=cam, domain=d):
                    out = apply_style_lock("A wave crashes", cam, {"domain_id": d, "forced_ship": "None"})
                    self.assertEqual(out.count(MOTION), 1)
        self.assertIn(MOTION, apply_style_lock("A wave crashes"))


class TestReactionGate(unittest.TestCase):
    def test_video2_opening_rejected(self):
        ok, failures = validate_simplified_prompt(VIDEO2, SCEN, D, "Sailing Yacht")
        self.assertFalse(ok)
        self.assertEqual(len(G(failures)), 1, failures)
        self.assertIn("startling", G(failures)[0])

    def test_action_plus_effect_passes(self):
        self.assertEqual(validate_simplified_prompt(GOOD, SCEN, D, "Sailing Yacht"), (True, []))

    def test_reaction_words(self):
        for w in ["startled", "alarming", "in alarm", "shocked", "stunned", "frightening",
                  "surprised", "panicked", "terrified", "horrified"]:
            with self.subTest(word=w):
                p = f"The sailing yacht lurches down the slipway, {w} workers. The yacht keeps sliding."
                self.assertTrue(G(validate_simplified_prompt(p, SCEN, D, "Sailing Yacht")[1]))

    def test_physical_words_not_reactions(self):
        # "shockwave", "fire alarm" gibi fiziksel ifadeler tepki sayılmaz
        for p in ["A shockwave ripples across the harbor, spray bursting. Water keeps surging.",
                  "The fire alarm bell swings loose, sparks bursting. Smoke keeps pouring."]:
            with self.subTest(p=p[:30]):
                self.assertFalse(G(validate_simplified_prompt(p, {}, "urban_city_disasters")[1]))

    def test_reaction_later_sentence_allowed(self):
        p = GOOD.replace("Three workers in orange coveralls leap back.",
                         "Three startled workers in orange coveralls leap back.")
        self.assertFalse(G(validate_simplified_prompt(p, SCEN, D, "Sailing Yacht")[1]))

    def test_env_centric_also_checked(self):
        p = "A tornado spins offshore, shocking pedestrians. Debris keeps swirling."
        self.assertTrue(G(validate_simplified_prompt(p, {}, "coastal_tornado_landfall")[1]))


class TestMotionSummary(unittest.TestCase):
    def test_ramp(self):
        diffs = [1.0] * 12 + [8.0] * 12   # 3 sn durgun, 3 sn hareket (4 fps)
        s = summarize(diffs)
        self.assertEqual(s["per_second"], [1.0, 1.0, 1.0, 8.0, 8.0, 8.0])
        self.assertEqual(s["opening_ratio"], 0.12)
        self.assertEqual(s["peak_second"], 4)

    def test_short_video_no_rest(self):
        s = summarize([2.0] * 8)
        self.assertIsNone(s["rest_avg"])
        self.assertIsNone(s["opening_ratio"])

    def test_format(self):
        s = summarize([1.0] * 12 + [8.0] * 12)
        self.assertIn("ilk3/sonrası=0.12", format_motion(s, "fixed_cctv"))
        self.assertIn("sallantı dahil", format_motion(s, "chase_pov"))
        self.assertNotIn("sallantı", format_motion(s, "fixed_cctv"))


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg yok")
class TestMotionFfmpeg(unittest.TestCase):
    def test_static_then_moving(self):
        # Durgun kısım 4 sn: gri→desen kesme karesi (tek büyük fark) açılış penceresine düşmesin
        path = os.path.join(tempfile.mkdtemp(), "ramp.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y",
                        "-f", "lavfi", "-i", "color=c=gray:s=128x224:d=4:r=24",
                        "-f", "lavfi", "-i", "testsrc2=s=128x224:d=3:r=24",
                        "-filter_complex", "[0][1]concat=n=2:v=1[v]", "-map", "[v]", path], check=True)
        p = motion_profile(path)
        self.assertLess(p["opening_avg"], 1.0)
        self.assertGreater(p["rest_avg"], p["opening_avg"] * 5)
        self.assertGreaterEqual(p["peak_second"], 4)


if __name__ == "__main__":
    unittest.main()
