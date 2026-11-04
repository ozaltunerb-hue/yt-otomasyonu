#!/usr/bin/env python3
"""4 Kas 2026 (4), Bahadır: Özgürlük Anıtı kadraj ve 4-9s araç düzeltmesi.

Sebep: 4 Kas 04:56 videosu 3/10 (K3 + B4 + C1). Hortum karaya ~11. sn'de ulaştı; B4 sedanı 4-9s'te ittirdiği için
Seedance aracı suya koydu (önce tekne, karaya yaklaşınca araba). K3 açısı alçak, yan bakıyor, cam korkuluk kadrajı
kapatıyor. İlk iyi video (04:13, 8/10) K1 ile.

KİLİT (bu modül): B4, B6, K3 PASİF; K1 KANITLI. Biri değişirse TestLock kırılır (mutasyon testleri kanıtlar).
1) 4-9s'te araç yok: aktif 4-9s B1 B2 B3 B5; araçlar sadece 9-15s'te (C3 kamyon, C6 sedan yalnız B5 ile).
2) Kadraj: K1 KANITLI, K2 DENEME (en fazla %20, art arda yok), K3 PASİF. OZGURLUK_DOGRULAMA kadrajı etkilemez.
3) Anıt 3 derinlikte aday bitirebilir: aday kalmazsa 1'e düşer (BEAT_BLOCK_FALLBACK_EVENTS).
4) Kötü video kaydı (tests/fixtures/liberty_good_videos.json, bad_videos).
"""
import collections
import json
import logging
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import core.event_structure as es   # noqa: E402
import core.proven_axes as pa   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
from test_toplu_3kas import _sequence   # noqa: E402

L = es.LIBERTY
K1 = "Rooftop terrace of a Lower Manhattan high-rise facing the harbor"
K2 = "High apartment balcony in Battery Park City looking across the harbor"
K3 = "Top-floor terrace of a waterfront hotel next to Battery Park"
ACTIVE_2 = {"B1", "B2", "B3", "B5"}
ACTIVE_3 = {"C1", "C2", "C3", "C4", "C6"}


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)


def lock_violations() -> list[str]:
    """Kilitli kararların ihlalleri (boş = kilit sağlam)."""
    out = []
    off = es.disabled_beats(L)
    for b in ("B4", "B6"):
        if b not in off:
            out.append(f"{b} pasif değil")
        if b not in es.EVENT_BEATS[L]["slice_2"]:
            out.append(f"{b} havuzdan silinmiş (sadece pasif olmalı)")
    if K3 not in pa.PASSIVE_SPOTS.get(L, set()):
        out.append("K3 pasif değil")
    if K3 in pa.spots(L, list(sk.view_spots(L, None))):
        out.append("K3 kadraj rotasyonunda")
    if K3 not in sk.EVENT_SKELETONS[L]["spots"]:
        out.append("K3 silinmiş (sadece pasif olmalı)")
    if pa.PROVEN_SPOTS.get(L) != {K1}:
        out.append("K1 tek KANITLI kadraj değil")
    if pa.frame_status(L, K1, {"type": "çatı", "pos_spot": K1, "mode": None}) != pa.PROVEN:
        out.append("K1 kadraj durumu KANITLI değil")
    if pa.extra_trials(L, "spot") != (K2,):
        out.append("K2 DENEME değil")
    return out


# ── KİLİT ─────────────────────────────────────────────────────────────────────────────────────────────────────────
class TestLock(_Quiet):
    def test_lock_holds(self):
        self.assertEqual(lock_violations(), [])

    def test_lock_breaks_if_b4_active(self):
        with patch.dict(es.DISABLED_BEATS, {L: {"B6"}}):
            self.assertIn("B4 pasif değil", lock_violations())

    def test_lock_breaks_if_b6_active(self):
        with patch.dict(es.DISABLED_BEATS, {L: {"B4"}}):
            self.assertIn("B6 pasif değil", lock_violations())

    def test_lock_breaks_if_k3_active(self):
        with patch.dict(pa.PASSIVE_SPOTS, {L: set()}):
            v = lock_violations()
            self.assertIn("K3 pasif değil", v)

    def test_lock_breaks_if_k1_not_proven(self):
        with patch.dict(pa.PROVEN_SPOTS, {L: {K2}}):
            self.assertIn("K1 tek KANITLI kadraj değil", lock_violations())
        with patch.dict(pa.PROVEN_SPOTS, {L: {K1, K2}}):
            self.assertIn("K1 tek KANITLI kadraj değil", lock_violations())

    def test_lock_breaks_if_deleted(self):
        pool = {k: v for k, v in es.EVENT_BEATS[L]["slice_2"].items() if k != "B4"}
        with patch.dict(es.EVENT_BEATS[L], {"slice_2": pool}):
            self.assertIn("B4 havuzdan silinmiş (sadece pasif olmalı)", lock_violations())


# ── 1) 4-9s'te araç yok ───────────────────────────────────────────────────────────────────────────────────────────
class TestNoVehicleInSlice2(_Quiet):
    def test_active_items(self):
        for spot in sk.view_spots(L, None):
            pairs = es.allowed_pairs(L, None, spot)
            self.assertEqual({p[0] for p in pairs}, ACTIVE_2, spot)
            self.assertEqual({p[1] for p in pairs}, ACTIVE_3, spot)
            self.assertEqual(len(pairs), 15, spot)
            self.assertEqual([p for p in pairs if p[1] == "C6"], [("B5", "C6")])

    def test_no_vehicle_text_in_active_slice2(self):
        pool = es.EVENT_BEATS[L]["slice_2"]
        for b in ACTIVE_2:
            t = pool[b]["text"].lower()
            self.assertNotIn("{vehicle}", t, b)
            for w in ("car", "bus", "truck", "sedan", "taxi", "suv"):
                self.assertNotRegex(t, rf"\b{w}\b", b)

    def test_vehicles_only_in_slice3(self):
        pool3 = es.EVENT_BEATS[L]["slice_3"]
        self.assertIn("truck", pool3["C3"]["text"])
        self.assertIn("{vehicle}", pool3["C6"]["text"])

    def test_old_exclusions_kept(self):
        ex = es.EVENT_BEATS[L]["excluded_pairs"]
        self.assertIn(("B4", "C6"), ex)   # boşta, kayıtta durur
        self.assertIn(("B6", "C3"), ex)

    def test_productions_never_pick_passive(self):
        for seed in (1, 2):
            rows = _sequence(L, 40, seed)
            b2 = {r["trace"]["beats"].split("+")[0] for r in rows}
            self.assertEqual(b2, ACTIVE_2)

    def test_block_fallback_never_runs_out(self):
        self.assertIn(L, es.BEAT_BLOCK_FALLBACK_EVENTS)
        dead_end = ["B1+C3", "B3+C2", "B5+C4"]   # 3 derinlikte sadece B2 kalır, B2'nin C1/C6 eşi dışlı
        with patch.dict(es._BEAT_MEMORY, {L: dead_end}, clear=True):
            with patch.object(es, "BEAT_BLOCK_FALLBACK_EVENTS", ()):
                with self.assertRaises(es.StructureError):   # güvenlik ağı olmadan üretim durur
                    es.choose_beats(L, None, K1, [])
            b2, b3 = es.choose_beats(L, None, K1, [])
        self.assertIn((b2, b3), es.allowed_pairs(L, None, K1))
        self.assertNotEqual(f"{b2}+{b3}", "B5+C4")
        # 1 derinlikte her geçmişte aday var (tüm son-1 çiftleri)
        for spot in sk.view_spots(L, None):
            pairs = es.allowed_pairs(L, None, spot)
            for a, b in pairs:
                self.assertTrue([p for p in pairs if p[0] != a and p[1] != b], (spot, a, b))


# ── 2) Kadraj ─────────────────────────────────────────────────────────────────────────────────────────────────────
class TestFrame(_Quiet):
    def test_rotation(self):
        self.assertEqual(pa.spots(L, list(sk.view_spots(L, None))), [K1, K2])
        self.assertEqual(pa.guards(L, "spot"), {K2})
        # ROTATION_ON kapalıyken de K3 gelmez
        with patch.object(pa, "ROTATION_ON", False):
            self.assertNotIn(K3, pa.spots(L, list(sk.view_spots(L, None))))

    def test_k3_not_deleted(self):
        self.assertIn(K3, sk.LIBERTY_CAMERA)
        self.assertIn(K3, sk.EVENT_SKELETONS[L]["spots"])
        import core.frame_axis as fx
        self.assertIn(K3, fx.SPOT_FRAME[L])

    def test_share_and_no_consecutive_trial(self):
        self.assertTrue(es.OZGURLUK_DOGRULAMA)   # beat ekseni eşit LRU; kadraj ekseni etkilenmez
        ks = []
        for seed in (1, 2):
            rows = _sequence(L, 50, seed)
            spots = [r["spot"] for r in rows]
            self.assertNotIn(K3, spots)
            self.assertFalse([1 for a, b in zip(spots, spots[1:]) if a == b == K2], seed)
            for r in rows:   # kamera cümlesi seçilen noktanın
                self.assertIn(sk.LIBERTY_CAMERA[r["spot"]], r["prompt"])
            ks += spots
        c = collections.Counter(ks)
        self.assertGreaterEqual(c[K1] / len(ks), 0.75, c)
        self.assertGreater(c[K2], 0)


# ── 4) Kayıt ──────────────────────────────────────────────────────────────────────────────────────────────────────
class TestRecord(_Quiet):
    def test_fixture(self):
        with open(os.path.join(ROOT, "tests", "fixtures", "liberty_good_videos.json"), encoding="utf-8") as f:
            d = json.load(f)
        good = d["videos"]
        self.assertEqual([(v["date"], v["frame"], v["beats"], v["score"]) for v in good],
                         [("2026-11-04 04:13", "K1", "B5+C3", "8/10")])
        bad = d["bad_videos"]
        self.assertEqual(len(bad), 1)
        v = bad[0]
        self.assertEqual((v["date"], v["frame"], v["spot"], v["score"]), ("2026-11-04 04:56", "K3", K3, "3/10"))
        self.assertIn("B4", v["beats"])
        self.assertIn("tekne", v["note"])
        self.assertTrue(es.OZGURLUK_DOGRULAMA)


if __name__ == "__main__":
    unittest.main()
