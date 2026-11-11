"""11 Kas 2026 (3), Bahadır: HEDEF 8 (orman, helikopter, karaya vurur, bombalar, heyelan köy, ateş hortumu, kül bulutu,
dev dalga) hikâyesi tamamen koddan (GPT hikâye çağrısı yok), devam cümlesi (2a), hareket cümlesi (2b), K_Y3 aktif, orman
aynı tür orta+final dışlamaları, bütçe dışlamaları. Sel ve Özgürlük Anıtı 40 tohumda aynen (tests/test_kilit_6kas.py).

Kie / GPT yok.
"""
import asyncio
import logging
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.frame_axis as fx   # noqa: E402
import core.opening_axis as ox   # noqa: E402
import core.pool_word_gate as gate   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402

HEDEF = (es.WILDFIRE, es.HELICOPTER, es.LANDFALL, es.VOLCANIC_BOMBS, es.VILLAGE, es.FIRE_TORNADO, es.PYROCLASTIC,
         es.TIDAL)
CONT = {
    es.TIDAL: "Until the last frame, the floodwater keeps surging through the street.",
    es.PYROCLASTIC: "Until the last frame, the ash cloud keeps rolling over the town.",
    es.WILDFIRE: "Until the last frame, the flames keep spreading from house to house.",
    es.HELICOPTER: "Until the last frame, the flames keep spreading toward the houses.",
    es.LANDFALL: "Until the last frame, the tornado keeps tearing through the street.",
    es.VOLCANIC_BOMBS: "Until the last frame, glowing rocks keep slamming into the street.",
    es.VILLAGE: "Until the last frame, the mud keeps pouring down the lane.",
    es.FIRE_TORNADO: "Until the last frame, the fire tornado keeps tearing through the houses.",
}
MOTION = "Full action from the very first frame to the last."   # 11 Kas (4): kısa hâl
K_Y3 = ("Handheld footage filmed from the flat rooftop of a tall stone house at the bottom of the village, high vantage, "
        "facing up the slope with the lanes and houses below in frame; slight hand shake, the camera stays fixed, tilting "
        "only slightly, never descending, the debris torrent in frame, a low parapet edge in the foreground; one "
        "continuous shot, no zoom, no cuts, no person or face close to the camera.")


async def _no_gpt(*args, **kwargs):
    raise AssertionError("HEDEF 8'de GPT hikâye çağrısı yapılmamalı")


class _Quiet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.WARNING)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def setUp(self):
        self._rec = cp.record_story_source
        cp.record_story_source = lambda entry: None
        ps.reset_memory()

    def tearDown(self):
        cp.record_story_source = self._rec


class TestCodeStory(_Quiet):
    def test_set_and_flags(self):
        self.assertEqual(set(es.CODE_STORY_EVENTS), set(HEDEF))
        for e in HEDEF:
            self.assertTrue(es.verbatim_on(e), e)
        for e in (es.FLOOD, es.LIBERTY):   # kilitli, HEDEF dışı: GPT yolu aynen
            self.assertFalse(es.code_story(e), e)

    def test_no_gpt_call_and_label(self):
        """GPT fonksiyonu çağrılırsa test kırılır: HEDEF 8'de hikâye çağrısı yok."""
        from core.trace_format import format_final_prompt, format_generation
        for e in HEDEF:
            for seed in (1, 2):
                with self.subTest(event=e, seed=seed):
                    ps.reset_memory()
                    random.seed(seed)
                    sc = asyncio.run(cp.build_creative_scene(None, e, [], [], _no_gpt))
                    st = sc["structure"]
                    self.assertEqual(st["story_source_kind"], "code")
                    self.assertEqual(st["story_source"], "Hikâye: kod (birebir)")
                    self.assertEqual(sc["trace"]["attempts"], [])
                    self.assertIsNone(st["caption_candidates"])   # caption şablondan (ek GPT çağrısı yok)
                    onay = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"],
                                                "style_suffix": sc["style_suffix"],
                                                "story_source": st["story_source"]})[1]
                    self.assertIn("\nHikâye: kod (birebir)\n", onay)
                    blocks = dict(format_generation(sc["trace"]))
                    self.assertIn("🔍 2. Hikâye kaynağı", blocks)
                    self.assertNotIn("Deneme 1", "\n".join(blocks.values()))
                    self.assertFalse([k for k in blocks if "GPT-4o dilimleri" in k])

    def test_same_text_as_code_fallback(self):
        """Birebir hâl kod yedeğiyle aynı metin: dilimler build_fallback'in seçtiği insan cümlesiyle birebir."""
        for e in HEDEF:
            ps.reset_memory()
            random.seed(3)
            sc = asyncio.run(cp.build_creative_scene(None, e, [], [], _no_gpt))
            spec, sl = sc["structure"]["spec"], sc["structure"]["slices"]
            with self.subTest(event=e):
                self.assertIn(sl, [x for _, x in es.fallback_candidates_ids(spec)])
                for slot in ("slice_2", "slice_3"):
                    self.assertIn(sl[slot], es.verbatim_forms(spec, slot))
                self.assertEqual(es.final_prompt_issues(spec, sl, sc["prompt"], sc["story"]), [])

    def test_rewrite_after_reject_no_gpt(self):
        for e in (es.WILDFIRE, es.TIDAL):
            ps.reset_memory()
            random.seed(1)
            sc = asyncio.run(cp.build_creative_scene(None, e, [], [], _no_gpt))
            story = asyncio.run(cp.rewrite_structured(sc["structure"], "test", _no_gpt))
            self.assertEqual(story, sc["story"])
            self.assertIn("kod (birebir)", sc["structure"]["rewrite_log"][-1]["result"])

    def test_other_events_still_use_gpt(self):
        calls = []

        async def gpt(system, user, **kw):
            calls.append(user)
            return {"slice_1_rest": "x", "slice_2": "x", "slice_3": "x"}
        random.seed(1)
        sc = asyncio.run(cp.build_creative_scene(None, es.MUDSLIDE, [], [], gpt))
        self.assertEqual(len(calls), cp.STRUCTURED_MAX_ATTEMPTS)
        self.assertEqual(sc["structure"]["story_source_kind"], "fallback")


class TestActionSentences(_Quiet):
    def test_continuation_right_after_final(self):
        self.assertEqual(es.CONTINUATION_LINES, CONT)
        for e in HEDEF:
            snap = ps.snapshot_event(e, 1)
            prompt = snap["prompt"]
            with self.subTest(event=e):
                head, tail = prompt.split("9-15s: ", 1)
                story_end = tail.index(CONT[e]) + len(CONT[e])
                self.assertEqual(tail.count(CONT[e]), 1)
                self.assertTrue(tail[story_end:].startswith(" "))   # devam cümlesinden sonra stil eki
                self.assertTrue(snap["style_suffix"] and prompt.endswith(snap["style_suffix"]))
                self.assertNotIn(CONT[e], snap["style_suffix"])

    def test_motion_sentence_place(self):
        self.assertEqual(sk.FULL_MOTION, MOTION)
        for e in HEDEF:
            suf = ps.snapshot_event(e, 2)["style_suffix"]
            with self.subTest(event=e):
                self.assertEqual(suf.count(MOTION), 1)
                self.assertIn(f"{MOTION} {sk.REAL_TIME}", suf)
                self.assertLess(suf.index("no cuts"), suf.index(MOTION))   # kamera cümlesinden sonra
        for e in (es.FLOOD, es.LIBERTY, es.MUDSLIDE):
            self.assertNotIn(MOTION, ps.snapshot_event(e, 2)["style_suffix"])


class TestFramesAndPairs(_Quiet):
    def test_k_y3_active(self):
        f = {"type": "K_Y3", "pos_spot": None, "fg": "parapet", "mode": None}
        self.assertEqual(sk.camera_rules(fx.verbatim_camera(es.VILLAGE, f)), K_Y3)
        self.assertEqual(gate.term_hits(fx.VERBATIM_FRAMES[es.VILLAGE]["K_Y3"][0], es.VILLAGE), [])
        spots = list(sk.EVENT_SKELETONS[es.VILLAGE]["spots"])
        for spot in spots:
            self.assertIn("K_Y3", {x["type"] for x in fx.all_frames(es.VILLAGE, spot, spots)})

    def test_wildfire_same_type_exclusions(self):
        ex = es.EVENT_BEATS[es.WILDFIRE]["excluded_pairs"]
        for p in (("K9", "L7"), ("K9", "L8"), ("K8", "L1"), ("K8", "L5"), ("K7", "L1")):
            self.assertIn(p, ex)
        pairs = {p for s in sk.view_spots(es.WILDFIRE, None) for p in es.allowed_pairs(es.WILDFIRE, None, s)}
        self.assertFalse(pairs & {("K9", "L7"), ("K9", "L8")})

    def test_budget_exclusions_recorded(self):
        # 11 Kas (4): sıfırdan hesap: çift dışlaması kalmadı; tek bütçe dışlaması kül bulutu E + P8 + Q4/Q8
        self.assertEqual(es.BUDGET_PAIRS_11KAS_3, {})
        self.assertEqual(ox.BUDGET_TRIPLES_11KAS_3, {es.PYROCLASTIC: {("E", "P8", "Q4"), ("E", "P8", "Q8")}})
        self.assertTrue(es.BUDGET_PAIRS_11KAS_3_ESKI and ox.BUDGET_TRIPLES_11KAS_3_ESKI)   # kayıt
        ft = {p for s in sk.view_spots(es.FIRE_TORNADO, None) for p in es.allowed_pairs(es.FIRE_TORNADO, None, s)}
        self.assertIn(("T4", "U11"), ft)
        self.assertTrue({p for p in ft if p[0] == "T8"})
        ti = {p for v in es.structure_views(es.TIDAL) for s in sk.view_spots(es.TIDAL, v)
              for p in es.allowed_pairs(es.TIDAL, v, s)}
        self.assertEqual(len({p[0] for p in ti}), 4)
        for e, pairs in es.BUDGET_PAIRS_11KAS_3.items():
            for view in es.structure_views(e):
                for spot in sk.view_spots(e, view):
                    self.assertFalse(set(es.allowed_pairs(e, view, spot)) & pairs, (e, spot))
        for e, triples in ox.BUDGET_TRIPLES_11KAS_3.items():
            for o, b2, b3 in triples:
                self.assertNotIn(o, ox.allowed(e, None, b2, b3))
        self.assertIn("E", ox.allowed(es.PYROCLASTIC, None, "P2", "Q1"))


class TestCaps(_Quiet):
    def test_caps_max_205(self):
        caps = {e: es.max_prompt_words(e) for e in HEDEF}
        # 11 Kas (4): ateş hortumu, kül bulutu, dev dalga 215
        self.assertEqual(caps, {es.WILDFIRE: 205, es.HELICOPTER: 205, es.LANDFALL: 198, es.VOLCANIC_BOMBS: 205,
                                es.VILLAGE: 205, es.FIRE_TORNADO: 215, es.PYROCLASTIC: 215, es.TIDAL: 215})
        for e in HEDEF:
            self.assertEqual(es.max_prompt_chars(e), 1400)

    def test_40_seeds_within_caps(self):
        for e in HEDEF:
            for seed in range(1, 41):
                snap = ps.snapshot_event(e, seed)
                with self.subTest(event=e, seed=seed):
                    self.assertNotIn("error", snap)
                    self.assertLessEqual(len(snap["prompt"].split()), es.max_prompt_words(e))
                    self.assertLessEqual(len(snap["prompt"]), 1400)
                    low = snap["style_suffix"].lower()
                    for w in ("eye level", "pans to follow", "follows the"):
                        self.assertNotIn(w, low)   # sığma koruması hiçbir zaman alçak kameraya düşmez


class TestRound4(_Quiet):
    """11 Kas (4), Bahadır: kısa hareket cümlesi, 215 tavanı, ateş hortumu "dash" -> "run", aynı tür dışlamalar,
    alçak kamera hiçbir koşulda yok."""

    def test_fire_tornado_people_no_dash(self):
        pools = es.FALLBACK_PEOPLE_FIRE_ENV
        for env, pool in pools.items():
            for t in pool:
                self.assertNotIn("dash", t, (env, t))
        self.assertEqual(pools["forest_edge"][4], "{N} people run between the houses below.")
        self.assertEqual(pools["tree_street"][4], "{N} people run away in the street right below.")
        self.assertEqual(pools["village_woods"][5], "{N} villagers run in the gardens below.")

    def test_same_type_exclusions_and_min_partners(self):
        applied = {es.WILDFIRE: {("K2", "L9")}, es.HELICOPTER: {("F2", "G9"), ("F6", "G3")},
                   es.LANDFALL: {("C8", "E7"), ("C7", "E8")},
                   es.VOLCANIC_BOMBS: {("R7", "T6"), ("R7", "T8"), ("R8", "T8")},
                   es.PYROCLASTIC: {("P7", "Q1"), ("P7", "Q7"), ("P7", "Q8")}}
        for e, pairs in applied.items():
            self.assertTrue(pairs <= es.EVENT_BEATS[e]["excluded_pairs"], e)
        # uygulanmayanlar (spot içinde ortanın tek final eşi kalıyordu)
        self.assertNotIn(("K9", "L9"), es.EVENT_BEATS[es.WILDFIRE]["excluded_pairs"])
        self.assertNotIn(("F2", "G6"), es.EVENT_BEATS[es.HELICOPTER]["excluded_pairs"])
        for e in applied:
            allp = set()
            for v in es.structure_views(e):
                for s in sk.view_spots(e, v):
                    ps_ = es.allowed_pairs(e, v, s)
                    allp |= set(ps_)
                    for m in {a for a, _ in ps_}:
                        self.assertGreaterEqual(len({d for a, d in ps_ if a == m}), 2, (e, s, m))
            self.assertGreaterEqual(len({a for a, _ in allp}), 4, e)
            self.assertGreaterEqual(len({d for _, d in allp}), 4, e)

    def test_fit_guard_never_low_camera(self):
        import inspect
        src = inspect.getsource(cp._build_structured_scene)
        self.assertIn("pa.frame_status(event, spot, a[1]) != pa.LOW", src)


if __name__ == "__main__":
    unittest.main()
