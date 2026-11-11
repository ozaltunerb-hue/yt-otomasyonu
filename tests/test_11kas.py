"""11 Kas 2026, Bahadır: kül bulutu yeniden tasarım (A), dev dalga kadraj/final/insan (B), cephe yangını pasif (C).

Kie / GPT yok. Kilitli 8 olay bu turda değişmez (tests/test_kilit_6kas.py kilit özeti); burada sadece yeni davranış.
"""
import logging
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import core.event_structure as es   # noqa: E402
import core.frame_axis as fx   # noqa: E402
import core.opening_axis as ox   # noqa: E402
import core.pool_word_gate as gate   # noqa: E402
import core.proven_axes as pa   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
import prompt_snapshot as ps   # noqa: E402

PY, TI = es.PYROCLASTIC, es.TIDAL

A2 = ("The whole volcano looms directly behind the town, its summit crater erupting a towering column of black ash, and "
      "part of the column collapses into a churning gray ash cloud that pours down the slope toward the first houses.")
A3 = ("Filmed from a high rooftop terrace at the edge of the town, wide angle, the entire volcano from its base to its "
      "summit filling the upper half of the frame directly behind the houses, the town below in the lower half; the "
      "camera stays fixed, never descending, the camera never pans, turns or follows.")   # 11 Kas (2) (0d): sabitlik eki
M_A = "the ash cloud reaches the first houses at the foot of the slope and swallows them one by one"
M_B = "the ash cloud pours over the edge of the town and buries the parked cars along the first street in gray ash"
# 11 Kas (2) (0d): "the camera never pans..." önüne "the camera stays fixed, never descending," eklendi
K_R = {"K_R1": "Filmed from the flat rooftop of a six-story apartment block right on the seafront, high vantage, wide "
               "angle, the whole coastal street and the sea behind it in frame; the camera stays fixed, never "
               "descending, the camera never pans, turns or follows.",
       "K_R2": "Filmed from a top-floor window of a tall seafront hotel, high vantage, wide angle, looking straight down "
               "the coastal street toward the sea; the camera stays fixed, never descending, the camera never pans, "
               "turns or follows.",
       "K_R3": "Filmed from a high rooftop terrace on the hillside just above the seafront, high vantage, wide angle, the "
               "coastal street and the apartment blocks below in frame; the camera stays fixed, never descending, the "
               "camera never pans, turns or follows."}
W_NEW = {"W10": "the wave smashes through the front wall of a seafront house and pours inside",
         "W11": "the surge swallows the ground floors of a row of shopfronts and a roof caves in",
         "W12": "the surge tears a wooden beach café off its foundations and smashes it against the apartment blocks"}
I_NEW = ("{N} people run up the street away from the sea toward the apartment entrances.",
         "{N} people run up the stairs of an apartment building.",
         "{N} people run up the side lane toward the hill behind the town.")


class _Quiet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.WARNING)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)


def _active(event, slot):
    return [b for b in es.EVENT_BEATS[event][slot] if b not in es.disabled_beats(event)]


class TestAshCloud(_Quiet):
    def test_opening_verbatim_and_rotation(self):
        self.assertEqual(ox.OPENINGS[PY]["E"], A2)
        self.assertEqual(ox.DISABLED_OPENINGS[PY], {"B", "C", "D"})
        for k in ("B", "C", "D"):
            self.assertIn(k, ox.OPENINGS[PY])   # silinmedi
        # A 13 Eki 2,13M hit'inde (kilit cümle): pasife alınmadı
        self.assertEqual(pa.openings(PY, ox.options(PY)), ["A", "E"])

    def test_frame_verbatim(self):
        self.assertEqual(fx.VERBATIM_FRAMES[PY]["K_V"][0], A3)
        frame = {"type": "K_V", "pos_spot": None, "fg": None, "mode": None}
        suffix = sk.style_suffix(PY, None, "Hillside terrace facing the erupting volcano", None, None, "suburb", frame)
        self.assertTrue(suffix.startswith(A3 + " One continuous shot, no zoom, no cuts"))
        self.assertIn("Setting: a suburban street of detached houses, garages and palm trees, no readable signs", suffix)
        self.assertLessEqual(len(suffix.split(";")) + suffix.count("."), 12)

    def test_hit_frames_kept_balcony_passive(self):
        # yamaç terası (13 Eki 2,13M) ve çatı terası (25 Eki 102K) hit: rotasyonda; balkon pasif
        self.assertEqual(set(pa.spots(PY, list(sk.EVENT_SKELETONS[PY]["spots"]))),
                         {pa.VOLC_HT, pa.VOLC_RT})
        self.assertIn(pa.VOLC_VB, pa.PASSIVE_SPOTS[PY])

    def test_middle_pool(self):
        b = es.EVENT_BEATS[PY]
        self.assertEqual(b["slice_2"]["P7"]["text"], M_A)
        self.assertEqual(b["slice_2"]["P8"]["text"], M_B)
        self.assertEqual(sorted(_active(PY, "slice_2")), ["P2", "P4", "P7", "P8"])   # P2 hit (13 Eki, 25 Eki)
        self.assertTrue({"P1", "P3", "P5"} <= es.DISABLED_BEATS[PY])
        # Q7, Q8 aynen (deneme)
        self.assertEqual(es.TRIAL_BEATS[PY], {"Q7", "Q8"})
        self.assertNotIn("P7", es.TRIAL_BEATS[PY])

    def test_every_spot_selectable_pools(self):
        for spot in sk.EVENT_SKELETONS[PY]["spots"]:
            pairs = es.allowed_pairs(PY, None, spot)
            self.assertGreaterEqual(len({p[0] for p in pairs}), 4, spot)
            self.assertGreaterEqual(len({p[1] for p in pairs}), 4, spot)

    def test_envs_at_foot_of_volcano(self):
        for name in sk.VOLC_ENVS:
            self.assertTrue(sk.volc_env_text(PY, name).endswith("right at the foot of the volcano"), name)
            self.assertNotIn("foot of the volcano", sk.volc_env_text(es.VOLCANIC_BOMBS, name))   # kilitli bombalar

    def test_word_gate_pyro_only(self):
        for w in ("fireball", "blast", "explosion", "exploded", "nuclear", "mushroom"):
            self.assertTrue(gate.term_hits(f"the {w} spreads", PY), w)
            self.assertEqual(gate.term_hits(f"the {w} spreads", es.VOLCANIC_BOMBS), [], w)
            self.assertEqual(gate.term_hits(f"the {w} spreads"), [], w)
        # 11 Kas (2) (0b), Bahadır: Q5 "blasts" -> "slams", istisna kalktı; Q5 aktif
        self.assertNotIn((PY, "beat", "Q5", "blast"), gate.KNOWN_HITS)
        q5 = es.EVENT_BEATS[PY]["slice_3"]["Q5"]["text"]
        self.assertEqual(q5, "the cloud slams the front off a shop building and the brickwork falls into the street")
        self.assertEqual(gate.term_hits(q5, PY), [])
        self.assertNotIn("Q5", es.disabled_beats(PY))

    def test_gpt_gate_pyro_only(self):
        spec = es.build_spec(PY, None, "Hillside terrace facing the erupting volcano", None, "P7", "Q1", None, 4,
                             volc_env="suburb")
        sl = {"slice_1_rest": "Four people run away.", "slice_2": "A fireball explodes over the houses.",
              "slice_3": "A house wall collapses."}
        codes = {i["rule"] for i in es.gpt_added_issues(spec, sl)}
        self.assertIn("pyro_blast_word", codes)
        spec_b = es.build_spec(es.VOLCANIC_BOMBS, None, "Hillside terrace facing the erupting volcano", None, "R5",
                               "T8", "pickup truck", 4, volc_env="suburb")
        self.assertNotIn("pyro_blast_word", {i["rule"] for i in es.gpt_added_issues(spec_b, sl)})

    def test_caps(self):
        self.assertEqual(es.max_prompt_words(PY), 205)
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[PY], (40, 92))
        self.assertEqual(es.max_prompt_words(es.VOLCANIC_BOMBS), 182)   # 11 Kas (2): K_B3 + birebir insan cümlesi

    def test_40_seeds_build(self):
        seen_k, seen_op = set(), set()
        for seed in range(1, 41):
            snap = ps.snapshot_event(PY, seed)
            self.assertNotIn("error", snap, seed)
            self.assertLessEqual(len(snap["prompt"].split()), 205)
            seen_k.add(snap["axes"]["kadraj"])
            seen_op.add(snap["axes"]["acilis"])
            for w in ("fireball", "explosion", "nuclear", "mushroom"):
                self.assertNotIn(w, snap["prompt"].lower())
        self.assertIn("K_V", seen_k)
        self.assertEqual(seen_op, {"A", "E"})


class TestTidal(_Quiet):
    def test_frames_verbatim_and_independent_of_spot(self):
        self.assertEqual({k: v[0] for k, v in fx.VERBATIM_FRAMES[TI].items()}, K_R)
        self.assertEqual({k: v[1] for k, v in fx.VERBATIM_FRAMES[TI].items()},
                         {"K_R1": "parapet", "K_R2": "pencere", "K_R3": "teras_korkuluk"})   # yaprak yok
        for spot in sk.EVENT_SKELETONS[TI]["spots"]:
            types = {f["type"] for f in fx.all_frames(TI, spot, list(sk.EVENT_SKELETONS[TI]["spots"]))}
            self.assertEqual(types, set(K_R), spot)   # balkon / teras rotasyonda yok

    def test_old_frames_kept_in_data(self):
        self.assertEqual(fx.SPOT_FRAME[TI]["Coastal street of low shopfronts"][0], "balkon")
        self.assertEqual(fx.SPOT_FRAME[TI]["Coastal road below a seafront promenade"][0], "teras")

    def test_frame_rotation_lru(self):
        seen = set()
        for seed in range(1, 41):
            snap = ps.snapshot_event(TI, seed)
            self.assertNotIn("error", snap, seed)
            k = snap["axes"]["kadraj"]
            seen.add(k)
            self.assertTrue(snap["style_suffix"].startswith(K_R[k]))
            self.assertIn("the camera never pans, turns or follows", snap["prompt"])
            self.assertNotIn("second-floor balcony", snap["prompt"])
            self.assertNotIn("raised seafront promenade", snap["prompt"])
        self.assertEqual(seen, set(K_R))

    def test_finals(self):
        b = es.EVENT_BEATS[TI]["slice_3"]
        self.assertEqual({k: b[k]["text"] for k in W_NEW}, W_NEW)
        self.assertEqual(sorted(_active(TI, "slice_3")), ["W1", "W10", "W11", "W12", "W5"])
        self.assertTrue({"W3", "W4"} <= es.DISABLED_BEATS[TI])
        self.assertFalse(set(W_NEW) & es.TRIAL_BEATS[TI])

    def test_middle_t5_passive(self):
        # 11 Kas (2) (0c), Bahadır: T5 PASİF (11 Kas'ta 13 Eki 247K adayı olduğu için bırakılmıştı); 4-9s'te 4 aktif
        self.assertIn("T5", es.DISABLED_BEATS[TI])
        self.assertIn("T5", es.EVENT_BEATS[TI]["slice_2"])   # silinmedi
        self.assertEqual(sorted(_active(TI, "slice_2")), ["T2", "T3", "T7", "T8"])

    def test_people_lines(self):
        pool = es.FALLBACK_PEOPLE[TI]
        self.assertEqual(pool[6:], I_NEW)
        self.assertEqual(pool[1], "{N} people run inland as the wave hits.")   # I2 silinmedi
        self.assertEqual(es.DISABLED_PEOPLE_LINES[TI], {"I2"})
        spec = es.build_spec(TI, None, "Coastal street of low shopfronts", "riviera", "T2", "W5", "red SUV", 4,
                             frame={"type": "K_R2", "pos_spot": None, "fg": "pencere", "mode": None},
                             light="driving rain and wind")
        ids = [i for i, _ in es.fallback_candidates_ids(spec)]
        self.assertNotIn("I2", ids)
        self.assertTrue({"I7", "I8", "I9"} <= set(ids))
        self.assertEqual(es.people_axis_proven(TI), ("I1", "I7", "I8", "I9"))
        self.assertEqual(es.people_axis_proven(es.FLOOD), ("I1", "I2"))

    def test_inland_gate_tidal_only(self):
        self.assertEqual(es.VAGUE_TARGET_GPT_BANNED, ("danger", "threat", "safety"))
        self.assertEqual(es.VAGUE_TARGET_GPT_BANNED_BY_EVENT, {TI: ("inland",)})
        spec = es.build_spec(TI, None, "Coastal street of low shopfronts", "riviera", "T2", "W5", "red SUV", 4,
                             light="driving rain and wind")
        sl = {"slice_1_rest": "Four pedestrians sprint inland.", "slice_2": "x", "slice_3": "y"}
        self.assertIn("vague_target", {i["rule"] for i in es.gpt_added_issues(spec, sl)})

    def test_lint_middle(self):
        risky = {b: gate.term_hits(es.EVENT_BEATS[TI]["slice_2"][b]["text"]) for b in _active(TI, "slice_2")}
        self.assertEqual({b: h for b, h in risky.items() if h}, {})


class TestFacade(_Quiet):
    def test_passive_menu_only(self):
        import bot
        self.assertIn(es.FACADE_FIRE, sk.DISABLED_EVENTS)
        self.assertNotIn(es.FACADE_FIRE, sk.skeleton_events("fire_disasters"))
        self.assertNotIn(es.FACADE_FIRE, bot.domain_events("fire_disasters"))
        self.assertIn(es.FACADE_FIRE, sk.EVENT_SKELETONS)   # kod ve havuz duruyor
        self.assertIn(es.FACADE_FIRE, es.EVENT_BEATS)
        self.assertEqual(bot.EVENT_LABELS[es.FACADE_FIRE], "🔥 Apartman cephe yangını")


class TestRandomFrameChoice(_Quiet):
    def test_lru_never_repeats_last(self):
        rng = random.Random(3)
        hist = []
        for _ in range(30):
            f, _ = fx.choose_frame(TI, "Coastal street of low shopfronts", list(sk.EVENT_SKELETONS[TI]["spots"]),
                                   set(), hist, rng)
            if hist:
                self.assertNotEqual(f["type"], hist[-1]["kadraj"])
            hist.append({"kadraj": f["type"]})


if __name__ == "__main__":
    unittest.main()
