#!/usr/bin/env python3
"""6 Kasım 2026, Bahadır: kilit kontrolü + havuz temizliği + kül bulutu insan ekseni + ateş hortumu kilidi. Ağ yok,
Kie/GPT çağrısı yok (sahte GPT).

KİLİT: 8 olay (es.LOCKED_EVENTS). prompt_snapshot 40 tohumda tests/fixtures/locked_prompts_40.json ile aynı olmalı.
Sel bu fixture'a 3249de8 kaynak ağacında alınan 40 tohumla bayt bayt doğrulandıktan sonra girdi. Bir kilitli olay
bilinçli değişirse fixture sadece Bahadır onayıyla yenilenir: scripts/locked_prompts.py
"""
import asyncio
import json
import logging
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import locked_prompts as lp   # noqa: E402
import prompt_snapshot as ps   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402

F, L, FT, PY, TI = es.FLOOD, es.LIBERTY, es.FIRE_TORNADO, es.PYROCLASTIC, es.TIDAL
FIRST_FIVE = {es.WILDFIRE, es.HELICOPTER, es.LANDFALL, es.VOLCANIC_BOMBS, es.VILLAGE}
# 3249de8 metinleri (4 Kas 02:00, 8/10 videonun kodu)
FLOOD_3249 = {
    "V11": "the {vehicle} is swept into a corner shop and its doors burst open as water pours inside",
    "D10": "the current shoves parked cars into a shopfront and its wall caves in",
    "D12": "the current piles a row of parked cars against the front of a shop",
    "D13": "the street becomes a fast brown river and the {vehicle} is carried away toward the intersection",
    "D14": "the current pushes a parked city bus against a shopfront and floodwater pours in through its doors",
    "D17": "the surge tips a city bus onto its side and pushes it along the street",
    "D18": "the surge slams the {vehicle} into a building front and the shopfront caves in around it",
}
PEOPLE = ("{N} people sprint into the open doorway of the house right below.",
          "{N} people run for the garage of a house across the street below.",
          "{N} people sprint down the street toward a stone archway below.")


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)


def _pool(event, bid):
    b = es.EVENT_BEATS[event]
    return (b["slice_2"].get(bid) or b["slice_3"][bid])["text"]


def _active(event, slot):
    return [b for b in es.EVENT_BEATS[event][slot] if b not in es.disabled_beats(event)]


class TestLock(_Quiet):
    def test_list(self):
        self.assertEqual(set(es.LOCKED_EVENTS), FIRST_FIVE | {F, L, FT})
        self.assertEqual(len(es.LOCKED_EVENTS), 8)

    def test_snapshot_40_seeds(self):
        saved = lp.load()
        self.assertEqual(set(saved), set(es.LOCKED_EVENTS))
        now = lp.hashes()
        for event in es.LOCKED_EVENTS:
            with self.subTest(event=event):
                self.assertEqual(saved[event], now[event], "kilitli olay değişti: commit/push YOK")

    def test_verbatim_flag_separate_from_lock(self):
        """Sonradan kilide giren olaylar VERBATIM kalır (kilitlendikleri hâlin GPT yolu); ilk 5 kapalı (HEAD davranışı)."""
        self.assertEqual(set(es.VERBATIM_OFF_EVENTS), FIRST_FIVE)
        for e in FIRST_FIVE:
            self.assertFalse(es.verbatim_on(e), e)
        for e in (F, L, FT):
            self.assertTrue(es.verbatim_on(e), e)


class TestFloodBack(_Quiet):
    def test_texts_and_water(self):
        for bid, text in FLOOD_3249.items():
            self.assertEqual(_pool(F, bid), text)
        self.assertEqual(es.WATER_LEVEL_LINES[F]["slice_2"], "Water rises past the car windows.")

    def test_limits(self):
        self.assertEqual(es.PROMPT_WORDS_BY_EVENT[F], 185)
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[F], (40, 80))
        self.assertEqual(es.SLICE_WORDS_BY_EVENT[F], {"slice_2": (10, 26), "slice_3": (10, 30)})

    def test_4kas_additions_passive_not_deleted(self):
        self.assertEqual(set(es.FLOOD_STORIES), {"H1", "H2", "H3", "H4", "H5"})
        self.assertFalse(es.story_axis_on(F))
        self.assertEqual(es.FLOOD_4KAS_PASSIVE_WATER, "Water rises past the car windows and races toward the camera.")
        self.assertEqual(es.FLOOD_4KAS_PASSIVE_LIMITS["prompt_words"], 215)
        self.assertEqual(set(es.FLOOD_4KAS_PASSIVE_TEXTS), set(FLOOD_3249))
        self.assertIn("swept up onto the sidewalk", es.FLOOD_4KAS_PASSIVE_TEXTS["V11"])
        for bid, text in es.FLOOD_4KAS_PASSIVE_TEXTS.items():
            if bid != "V11":
                self.assertIn("below the camera", text)

    def test_people_axis_is_i1_i6_gpt_writes_line(self):
        self.assertEqual(len(es.FALLBACK_PEOPLE[F]), 6)
        self.assertNotIn(F, es.VERBATIM_PEOPLE_EVENTS)
        self.assertNotIn(F, es.CAMERA_EXEMPT_EVENTS)
        self.assertTrue(es.has_people_rule(F))

    def test_a1_vehicle_fix_stays(self):
        """A1 tek istisna: 9-15s Seçim satırında araç adı dolu (önceki hâl "and the  is carried away")."""
        filled = es.beat_text(F, "slice_3", "D13", "red SUV")
        self.assertIn("the red SUV is carried away", filled)
        self.assertIn('es.beat_text(event, "slice_3", b3, vehicle)', open(os.path.join(ROOT, "core", "creative_pipeline.py"),
                                                                         encoding="utf-8").read())


class TestPoolCleanup(_Quiet):
    PASSIVE = {FT: {"T5", "T6", "U6", "U10"}, PY: {"Q2"}, TI: {"W9"}, es.MARINA_TORNADO: {"Y5"}, es.AVENUE: {"P5", "P7"}}
    # Bahadır kararı: P6 684K hiti, T4 + U11 5 Kas 9/10, W2 bu turda aktif
    KEPT = {FT: {"T4", "U11"}, es.AVENUE: {"P6"}, es.METEOR: {"W2"}}

    def test_passive_in_pool_not_selectable(self):
        for event, ids in self.PASSIVE.items():
            for bid in ids:
                self.assertTrue(_pool(event, bid))
                self.assertIn(bid, es.disabled_beats(event))
                view = (es.structure_views(event) or [None])[0]
                for spot in sk.view_spots(event, view):
                    self.assertFalse([p for p in es.allowed_pairs(event, view, spot) if bid in p])

    def test_kept_active(self):
        for event, ids in self.KEPT.items():
            for bid in ids:
                self.assertNotIn(bid, es.disabled_beats(event), (event, bid))

    def test_min_four_active_each_slice(self):
        for event in self.PASSIVE:
            for slot in ("slice_2", "slice_3"):
                self.assertGreaterEqual(len(_active(event, slot)), 4, (event, slot))

    def test_pyroclastic_fallback_only_on_dead_end(self):
        """Kül bulutu: Q2 pasif, aday bitince derinlik 1 (StructureError yok). Aday varken fallback seçimi değiştirmez."""
        import random
        self.assertIn(PY, es.BEAT_BLOCK_FALLBACK_EVENTS)
        spot = "Rooftop terrace facing the erupting volcano"
        pairs = es.allowed_pairs(PY, None, spot)
        self.assertFalse([p for p in pairs if "Q2" in p])
        # 8/646 çıkmaz sıradan biri: eskiden StructureError
        hist = ["x|none|y|z##P2+Q4|c", "x|none|y|z##P4+Q5|c"]
        dead = {("P2", "Q4"), ("P4", "Q5")}
        b2, b3 = {p[0] for p in dead}, {p[1] for p in dead}
        self.assertFalse([p for p in pairs if p[0] not in b2 and p[1] not in b3])
        self.assertIn(es.choose_beats(PY, None, spot, hist, random.Random(1)), pairs)
        # Normal akış: aday varken listeden çıkarılsa da seçim aynı
        hist = ["x|none|y|z##P1+Q4|c", "x|none|y|z##P2+Q5|c"]
        real = es.BEAT_BLOCK_FALLBACK_EVENTS
        for seed in range(50):
            with_fb = es.choose_beats(PY, None, spot, hist, random.Random(seed))
            es.BEAT_BLOCK_FALLBACK_EVENTS = tuple(e for e in real if e != PY)
            try:
                self.assertEqual(es.choose_beats(PY, None, spot, hist, random.Random(seed)), with_fb)
            finally:
                es.BEAT_BLOCK_FALLBACK_EVENTS = real

    def test_tidal_camera_only_tidal(self):
        for seed in range(1, 21):
            prompt = ps.snapshot_event(TI, seed)["prompt"]
            self.assertIn("the camera never pans, turns or follows", prompt)
            self.assertNotIn("always in frame", prompt)
        # Şablon ortak: diğer olayların kamerası aynı kalır
        self.assertEqual(sk.camera_rules("the tornado always in frame; one continuous shot, no zoom, no cuts.").count(
            "the tornado always in frame"), 1)


class TestPyroclasticPeople(_Quiet):
    def test_axis(self):
        self.assertEqual(es.FALLBACK_PEOPLE[PY], PEOPLE)
        self.assertIn(PY, es.PEOPLE_AXIS_EVENTS)
        self.assertIn(PY, es.VERBATIM_PEOPLE_EVENTS)
        self.assertEqual(sk.count_range(PY, None), (3, 6))
        self.assertEqual(len(es.FALLBACK_PEOPLE_RETIRED[PY]), 6)   # önceki havuz silinmedi

    def test_prompt_carries_pool_line_verbatim(self):
        seen = set()
        for seed in range(1, 41):
            snap = ps.snapshot_event(PY, seed)
            self.assertNotIn("error", snap)
            first = snap["prompt"].split("4-9s:")[0]
            hit = [p for p in PEOPLE if p.split("{N} ")[1] in first]
            self.assertEqual(len(hit), 1, first)
            seen.add(hit[0])
        self.assertEqual(seen, set(PEOPLE))   # üçü de çıkıyor

    def test_gpt_sentence_discarded(self):
        async def gpt(system, msg, **kw):
            return {"slice_1_rest": "Five villagers scatter in terror.", "slice_2": "x", "slice_3": "x"}
        real = cp.record_story_source
        cp.record_story_source = lambda entry: None
        try:
            scene = asyncio.run(cp.build_creative_scene(None, PY, [], [], gpt))
        finally:
            cp.record_story_source = real
        self.assertIn(scene["trace"]["axes"]["insan"], ("P1", "P2", "P3"))
        self.assertNotIn("villagers scatter", scene["prompt"])

    def test_all_trial(self):
        """Üçü de DENEME: kanıtlı öğe yok, art arda yok kuralı aday tüketmez, LRU ile döner."""
        self.assertFalse(set(es.PEOPLE_AXIS_PROVEN) & {"P1", "P2", "P3"})


class TestPoolsDoNotRunOut(_Quiet):
    def test_long_sequence(self):
        """Havuzu küçülen olaylarda 100 art arda üretim: aday tükenmez, pasif öğe gelmez (kod yedeğiyle, geçmişli)."""
        for event in (FT, PY, TI, es.MARINA_TORNADO, es.AVENUE):
            with self.subTest(event=event):
                hist, recs = [], []
                for _ in range(100):
                    sc = ps.build(event, history=list(hist), axes_loader=lambda d: list(recs))
                    recs.append({"eksenler": sc["axes_json"], "combo_key": sc["combo_key"], "prompt": sc["prompt"]})
                    hist.append(sc["combo_key"])
                    beats = sc["trace"]["beats"].split("+")
                    self.assertFalse(set(beats) & es.disabled_beats(event), beats)
                ps.reset_memory()


class TestFireTornadoLock(_Quiet):
    def test_good_video_fixture(self):
        with open(os.path.join(ROOT, "tests", "fixtures", "fire_tornado_good_videos.json"), encoding="utf-8") as f:
            data = json.load(f)
        v = data["videos"][0]
        self.assertEqual((v["date"], v["beats"], v["environment"], v["score"]),
                         ("2026-11-05 00:13", "T4+U11", "forest_edge", "9/10"))
        self.assertIn("Rooftop terrace", v["spot"])
        self.assertTrue(set(v["spot"].split()) and v["spot"] in es.FIRE_TOR_ENVS["forest_edge"]["spots"])
        self.assertIn(("T4", "U11"), [p for s in es.FIRE_TOR_ENVS["forest_edge"]["spots"]
                                      for p in es.allowed_pairs(FT, None, s)])


if __name__ == "__main__":
    unittest.main()
