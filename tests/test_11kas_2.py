"""11 Kas 2026 (2), Bahadır: 6 kilitli olay (orman, helikopter, karaya vurur, bombalar, heyelan köy, ateş hortumu) + kül bulutu
ve dev dalga bilerek değişti (onaylı). Dünkü 4 karar (0a-0d), yeni birebir kadrajlar, pasifler, yeni beat'ler, birebir
insan ekseni. Sel (3249de8) ve Özgürlük Anıtı kilidi aynen (tests/test_kilit_6kas.py, 40 tohum özeti).

Kie / GPT yok.
"""
import asyncio
import logging
import os
import re
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
import core.proven_axes as pa   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402

WF, HE, LF, VB, VI, FT = es.WILDFIRE, es.HELICOPTER, es.LANDFALL, es.VOLCANIC_BOMBS, es.VILLAGE, es.FIRE_TORNADO
PY, TI = es.PYROCLASTIC, es.TIDAL
CHANGED = (WF, HE, LF, VB, VI, FT, PY, TI)
FIXED = "the camera stays fixed, never descending, the camera never pans, turns or follows"

# Bahadır'ın metinleri (birebir)
K_O3 = ("Handheld footage filmed from the top-floor window of a tall house high on the hillside, high vantage, wide angle, "
        "the burning slope and the street below both in frame; slight hand shake, the camera stays fixed, never "
        "descending, the camera never pans, turns or follows, a window frame edge in the foreground; one continuous "
        "shot, no zoom, no cuts, no person or face close to the camera.")
K_H3 = ("Handheld footage filmed from the flat rooftop of a three-story house at the top of the street, high wide view of "
        "the neighborhood and the wall of flames together, the helicopter large and close in frame, never a distant dot; "
        "slight hand shake, the camera stays fixed, never descending, empty foreground; no zoom, no cuts, no person or "
        "face close to the camera.")
# 11 Kas (3): "always in frame" -> "in frame", aktif
K_Y3 = ("Handheld footage filmed from the flat rooftop of a tall stone house at the bottom of the village, high vantage, "
        "facing up the slope with the lanes and houses below in frame; slight hand shake, the camera stays fixed, tilting "
        "only slightly, never descending, the debris torrent in frame, a low parapet edge in the foreground; one "
        "continuous shot, no zoom, no cuts, no person or face close to the camera.")
BOMBS_POINT = ("filmed from the top-floor window of a tall house at the end of the street, high vantage over {street} "
               "toward the")
NEW_BEATS = {
    (WF, "slice_3", "L8"): "a burning house across the street collapses in on itself in a shower of sparks",
    (WF, "slice_3", "L9"): "the flames engulf a wooden garage and its roof caves in onto the car inside",
    (HE, "slice_3", "G8"): "a burning wooden house beside the water line collapses in on itself in a burst of sparks and "
                           "steam",
    (HE, "slice_3", "G9"): "the downdraft tears the burning roof off a wooden shed and its walls fall in",
    # Bahadır'ın C6'sı: "scatters" kelime kapısına takıldı, verdiği yedek ifade; C6 kimliği çıkarılmış eski maddenin -> C8
    (LF, "slice_2", "C8"): "the tornado rips the balconies off the front of a waterfront apartment block and throws the "
                           "pieces into the street",
    (LF, "slice_2", "C7"): "the tornado tears the front off a waterfront café and drags its tables and chairs into the "
                           "street",
    (LF, "slice_3", "E8"): "the tornado collapses the front wall of a waterfront house into the street, the rooms behind it "
                           "torn open",
    (FT, "slice_2", "T8"): "the base of the fire tornado sweeps over the parked {vehicle} and it bursts into flames where "
                           "it stands",
}
PASSIVE = {WF: {"K1", "K5", "L3"}, HE: {"F3", "G1", "G5"}, LF: {"C2", "C5", "E4", "E5"}, VB: {"R3", "T7"},
           VI: {"K2", "K4", "L3", "L6"}, FT: {"T1"}, TI: {"T5"}}
PEOPLE = {
    WF: ("{N} residents run down the street toward the parked cars at the bottom of the hill.",
         "{N} people run up the steps of the nearest house.",
         "{N} neighbors sprint down the road toward the town below.",
         "{N} people run across the street into the house below the camera."),
    HE: ("{N} residents run down the street toward the parked cars.",
         "{N} people sprint across the gardens toward the houses below the camera.",
         "{N} neighbors run down the road toward the bottom of the hill."),
    LF: ("{N} people sprint into the entrance of the building across the street.",
         "{N} pedestrians run up the steps of the nearest building.",
         "{N} people run off the waterfront into the side street behind the houses."),
    VB: ("{N} residents run into the doorway of the house across the street.",
         "{N} people sprint down the street toward the corner shop and run inside.",
         "{N} villagers run under the stone archway at the end of the street."),
    VI: ("{N} villagers run down the lane away from the mud.",
         "{N} villagers run up the stone steps of the nearest house.",
         "{N} residents sprint across the square into the doorway of a stone barn."),
}
# Talimattaki havuz kelime listesi (yeni metinler bunlardan geçmez)
USER_BANNED = {"spin": r"spin(?:s|ning)?|spun", "flip": r"flip(?:s|ped|ping)?",
               "roll over": r"roll(?:s|ed|ing)?\s+(?:\w+\s+){0,3}?over", "toss": r"toss(?:es|ed|ing)?",
               "lift": r"lift(?:s|ed|ing)?", "fly": r"fl(?:y|ies|ying|ew)", "U-turn": r"u-?turn(?:s|ed|ing)?",
               "reverse": r"revers(?:e|es|ed|ing)", "tip over": r"tip(?:s|ped|ping)?\s+(?:\w+\s+){0,3}?over",
               "scatter": r"scatter(?:s|ed|ing)?", "dash": r"dash(?:es|ed|ing)?", "scramble": r"scrambl\w*",
               "inland": r"inland", "safety": r"safety", "danger": r"danger\w*"}


def _active(event, slot):
    return [b for b in es.EVENT_BEATS[event][slot] if b not in es.disabled_beats(event)]


def _user_hits(text):
    low = text.replace(gate.ALLOWED_PHRASES[0], " ")
    return [k for k, v in USER_BANNED.items() if re.search(rf"\b(?:{v})\b", low, re.IGNORECASE)]


def _cam(event, frame_id, volc_env=None):
    f = {"type": frame_id, "pos_spot": None, "fg": fx.VERBATIM_FRAMES[event][frame_id][1], "mode": None}
    return sk.camera_rules(fx.verbatim_camera(event, f, volc_env))


class _Quiet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.WARNING)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)


class TestDecisions0(_Quiet):
    def test_0a_ash_openings_alternate(self):
        self.assertEqual(pa.PRIMARY["acilis"][PY], ("E",))
        self.assertEqual(ox.DISABLED_OPENINGS[PY], {"B", "C", "D"})

    def test_0b_q5_slams(self):
        q5 = es.EVENT_BEATS[PY]["slice_3"]["Q5"]["text"]
        self.assertEqual(q5, "the cloud slams the front off a shop building and the brickwork falls into the street")
        self.assertNotIn("Q5", es.disabled_beats(PY))
        self.assertFalse([k for k in gate.KNOWN_HITS if k[0] == PY])
        self.assertEqual(gate.term_hits(q5, PY), [])

    def test_0c_tidal_t5_passive(self):
        self.assertIn("T5", es.DISABLED_BEATS[TI])
        self.assertIn("T5", es.EVENT_BEATS[TI]["slice_2"])   # silinmedi

    def test_0d_fixed_phrase(self):
        # 11 Kas (8) (1): K_V, K_R1, K_R2 (ve yeni K_R4) "; slight hand shake, " + sabitlik; pasif K_R3 metni aynen
        for e, ids in ((PY, ("K_V",)), (TI, ("K_R1", "K_R2", "K_R4"))):
            for k in ids:
                with self.subTest(frame=k):
                    self.assertIn(f"; slight hand shake, {FIXED}.", fx.VERBATIM_FRAMES[e][k][0])
        self.assertIn(f"; {FIXED}.", fx.VERBATIM_FRAMES[TI]["K_R3"][0])
        self.assertIn("never pans", __import__("prompt_rules").FIXED_TERMS)   # sözlük eklemesi kalır


class TestFrames(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(_cam(WF, "K_O3"), K_O3)
        self.assertEqual(_cam(HE, "K_H3"), K_H3)
        self.assertEqual(_cam(VI, "K_Y3"), K_Y3)   # 11 Kas (3): aktif
        for env in sk.VOLC_ENVS:
            cam = _cam(VB, "K_B3", env)
            with self.subTest(env=env):
                self.assertIn(BOMBS_POINT.format(street=sk.volc_env_text(VB, env)), cam)
                self.assertIn("slight hand shake, the camera stays fixed, tilting only slightly, never descending, the "
                              "volcano always in the upper third, a window frame edge in the foreground; one continuous "
                              "shot, no zoom, no cuts, no person or face close to the camera.", cam)

    def test_frames_independent_of_spot(self):
        for e, k in ((WF, "K_O3"), (HE, "K_H3"), (VB, "K_B3")):
            spots = list(sk.EVENT_SKELETONS[e]["spots"])
            for spot in spots:
                with self.subTest(event=e, spot=spot):
                    rot = pa.allowed_variants(e, spot, fx.all_frames(e, spot, spots))
                    self.assertIn(k, {f["type"] for f in rot})

    def test_wildfire_embankment_frame_passive(self):
        spots = list(sk.EVENT_SKELETONS[WF]["spots"])
        self.assertIn("Embankment above the village road", spots)   # spot aktif (31 Eki hit'i bu spottan)
        for spot in spots:
            allv = fx.all_frames(WF, spot, spots)
            self.assertFalse([f for f in allv if f["type"] == "tepe"], spot)
            self.assertFalse([f for f in allv if f.get("fg") == "yaprak"], spot)

    def test_village_frames(self):
        spots = list(sk.EVENT_SKELETONS[VI]["spots"])
        self.assertIn("High steps on the village square", spots)   # spot kalır
        for spot in spots:
            allv = fx.all_frames(VI, spot, spots)
            with self.subTest(spot=spot):
                self.assertFalse([f for f in allv if f["type"] == "teras"])
                self.assertFalse([f for f in allv if f["type"] == "tepe" and f.get("fg") == "yaprak"])
                self.assertTrue([f for f in allv if f["type"] == "tepe" and f.get("fg") == "boş"])
                self.assertTrue([f for f in allv if f["type"] == "K_Y3"])   # 11 Kas (3): spottan bağımsız

    def test_village_k_y3_active_word_gate(self):
        # 11 Kas (3), Bahadır: "always" çıktı, kelime kapısından geçer, aktif
        self.assertEqual(fx.PASSIVE_VERBATIM_FRAMES, {TI: {"K_R3"}})   # 11 Kas (8) (2): sadece dev dalga K_R3
        self.assertEqual(gate.term_hits(fx.VERBATIM_FRAMES[VI]["K_Y3"][0], VI), [])


class TestBeats(_Quiet):
    def test_new_texts_verbatim(self):
        for (e, slot, bid), text in NEW_BEATS.items():
            with self.subTest(beat=bid):
                self.assertEqual(es.EVENT_BEATS[e][slot][bid]["text"], text)
                self.assertNotIn(bid, es.disabled_beats(e))

    def test_passive_kept_in_pool(self):
        for e, off in PASSIVE.items():
            with self.subTest(event=e):
                self.assertTrue(off <= es.disabled_beats(e))
                self.assertTrue(off <= set(es.EVENT_BEATS[e]["slice_2"]) | set(es.EVENT_BEATS[e]["slice_3"]))

    def test_hits_kept(self):
        self.assertFalse({"L4"} & es.disabled_beats(WF))
        self.assertFalse({"C1", "E1"} & es.disabled_beats(LF))
        self.assertIn("C", pa.openings(LF, ox.options(LF)))
        self.assertFalse({"R4", "T2"} & es.disabled_beats(VB))

    def test_at_least_four_active_per_slice(self):
        for e in CHANGED:
            for slot in ("slice_2", "slice_3"):
                with self.subTest(event=e, slot=slot):
                    self.assertGreaterEqual(len(_active(e, slot)), 4)

    def test_bombs_vehicle_middle_never_with_t2_t9(self):
        for spot in sk.view_spots(VB, None):
            pairs = es.allowed_pairs(VB, None, spot)
            with self.subTest(spot=spot):
                self.assertFalse([p for p in pairs if p[0] in ("R1", "R2") and p[1] in ("T2", "T9")])

    def test_new_texts_pass_word_gates(self):
        texts = [t for t in NEW_BEATS.values()]
        texts += [fx.VERBATIM_FRAMES[e][k][0] for e, k in ((WF, "K_O3"), (HE, "K_H3"), (VB, "K_B3"))]
        texts += [l for pool in PEOPLE.values() for l in pool]
        for t in texts:
            with self.subTest(text=t[:50]):
                self.assertEqual(gate.term_hits(t), [])
                self.assertEqual(_user_hits(t), [])


class TestPeople(_Quiet):
    def test_pools_verbatim_and_old_retired(self):
        for e, lines in PEOPLE.items():
            with self.subTest(event=e):
                self.assertEqual(es.FALLBACK_PEOPLE[e], lines)
                self.assertIn(e, es.PEOPLE_AXIS_EVENTS)
                self.assertIn(e, es.VERBATIM_PEOPLE_EVENTS)
                self.assertEqual(set(es.people_axis_proven(e)), {f"I{i + 1}" for i in range(len(lines))})
                self.assertTrue(es.FALLBACK_PEOPLE_RETIRED[e])   # önceki havuz silinmedi
        self.assertEqual(es.FALLBACK_PEOPLE[es.MARINA_TORNADO], es.FALLBACK_PEOPLE_RETIRED[LF])   # marina aynen

    def test_fire_tornado_people_unchanged(self):
        self.assertNotIn(FT, es.PEOPLE_AXIS_EVENTS)
        self.assertEqual(es.FALLBACK_PEOPLE_FIRE_ENV["forest_edge"][0], "{N} people run between the houses below.")

    def test_gpt_people_line_dropped_slices_kept(self):
        async def gpt(system, msg, **kw):
            return {"slice_1_rest": "Four people scramble everywhere in panic.", "slice_2": "X two.", "slice_3": "Y three."}
        for e in PEOPLE:
            spot = list(sk.EVENT_SKELETONS[e]["spots"])[0]
            b2, b3 = es.allowed_pairs(e, None, spot)[0]
            veh = es.event_vehicles(e, None)[0][0] if es.uses_vehicle(e) else None
            spec = es.build_spec(e, None, spot, None, b2, b3, veh, 4, None, "pastel_town" if e == VB else None)
            spec["people_line"] = "I2"
            try:
                _, att = asyncio.run(cp.write_slices(spec, "P", "W", [], gpt, max_attempts=1))
            except cp.CreativeStoryError as err:
                att = err.attempts
            sl = att[0]["slices"]
            with self.subTest(event=e):
                self.assertEqual(sl["slice_1_rest"], es.clean_slice(PEOPLE[e][1].format(N="Four")))
                # 11 Kas (3): HEDEF 8'de 4-9s / 9-15s de birebir (VERBATIM açık); üretimde write_slices hiç çağrılmaz
                self.assertEqual((sl["slice_2"], sl["slice_3"]),
                                 (es.fallback_beat_slice(spec, "slice_2"), es.fallback_beat_slice(spec, "slice_3")))

    def test_people_lru_no_repeat(self):
        for e in PEOPLE:
            rows = [ps.snapshot_event(e, s)["axes"] for s in range(1, 4)]
            self.assertTrue(rows)
        # 40 art arda basışta (sahte Notion) insan ekseni art arda aynı cümleyi seçmez
        import havuz_denetim as hd
        for e in PEOPLE:
            seq = [r["insan"] for r in hd.simulate(e, 12)]
            with self.subTest(event=e):
                self.assertTrue(all(seq))
                # 11 Kas (3): 205 tavanında bazı üretimlerde tek insan cümlesi sığıyor (helikopter): en fazla 1 tekrar
                reps = [i for i in range(1, len(seq)) if seq[i] == seq[i - 1]]
                self.assertLessEqual(len(reps), 1 if e == HE else 0)


class TestBuildAndCaps(_Quiet):
    def test_caps(self):
        # 11 Kas (3): devam + hareket cümleleri: tavan en fazla 205 (karaya vurur ölçülen 198); hikâye üst sınırı +
        # devam cümlesi
        self.assertEqual({e: es.max_prompt_words(e) for e in CHANGED},
                         {WF: 205, HE: 205, LF: 198, VB: 205, VI: 205, FT: 215, PY: 215, TI: 215})   # 11 Kas (4)
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[HE], (40, 92))
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[FT], (40, 87))
        for e in CHANGED:
            self.assertLessEqual(es.max_prompt_words(e), 215)   # 11 Kas (4)
            self.assertEqual(es.max_prompt_chars(e), 1400)

    def test_40_seeds_build(self):
        for e in CHANGED:
            for seed in range(1, 41):
                snap = ps.snapshot_event(e, seed)
                with self.subTest(event=e, seed=seed):
                    self.assertNotIn("error", snap)
                    self.assertLessEqual(len(snap["prompt"].split()), es.max_prompt_words(e))
                    self.assertLessEqual(len(snap["prompt"]), 1400)


if __name__ == "__main__":
    unittest.main()
