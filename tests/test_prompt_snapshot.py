#!/usr/bin/env python3
"""Prompt anlık görüntüsü ve çeşitlilik ölçer araçları (21 Eki 2026, Gece 1 / Aşama 2).

Araçların kendisi doğru çalışıyor mu: aynı tohum aynı sonucu verir, GPT çağrılmaz (kod yedeği), süreç hafızası
sızmaz, fark aracı değişikliği bulur ve değişmeyeni "0" sayar, baseline dosyası okunur. Baseline'ın mevcut kodla birebir
aynı olması burada test EDİLMEZ (bilinçli değişiklikte baseline yenilenir: scripts/prompt_snapshot.py baseline).
Ağ yok, Kie/GPT/Notion yok.
"""
import copy
import logging
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402
import variety_report as vr   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)


class TestSnapshot(_Quiet):
    def test_active_events_exclude_disabled(self):
        events = ps.active_events()
        self.assertEqual(len(events), len(es.structured_events()) - len(sk.DISABLED_EVENTS & set(es.structured_events())))
        for e in sk.DISABLED_EVENTS:
            self.assertNotIn(e, events)

    def test_same_seed_same_result(self):
        for e in (es.FLOOD, es.FIRE_TORNADO, es.AVALANCHE_VILLAGE, es.VOLCANIC_BOMBS):
            with self.subTest(event=e):
                self.assertEqual(ps.snapshot_event(e, 7), ps.snapshot_event(e, 7))

    def test_story_comes_from_code_fallback(self):
        snap = ps.snapshot_event(es.EARTHQUAKE_APARTMENT, 3)
        self.assertEqual(snap["axes"]["story_source"], "fallback")
        self.assertTrue(snap["prompt"].startswith("0-4s: " + es.EVENT_KEY_VISUAL[es.EARTHQUAKE_APARTMENT]))

    def test_memory_does_not_leak_between_seeds(self):
        a = ps.snapshot_event(es.PYROCLASTIC, 5)
        for s in (1, 2, 3):
            ps.snapshot_event(es.PYROCLASTIC, s)
        self.assertEqual(ps.snapshot_event(es.PYROCLASTIC, 5), a)

    def test_story_source_log_not_written(self):
        import core.creative_pipeline as cp
        calls = []
        real = cp.record_story_source
        cp.record_story_source = lambda entry: calls.append(entry)
        try:
            ps.snapshot_event(es.MUDSLIDE, 1)
        finally:
            cp.record_story_source = real
        self.assertEqual(calls, [])   # build() kendi no-op'unu takar, gerçek kayda hiç ulaşılmaz

    def test_diff_zero_and_detects_change(self):
        base = ps.snapshot_all([es.FLOOD, es.SLOPE], seeds=(1, 2, 3))
        self.assertEqual(ps.diff(base, copy.deepcopy(base)), {})
        changed = copy.deepcopy(base)
        changed[es.SLOPE]["2"]["prompt"] += " X"
        out = ps.diff(base, changed)
        self.assertEqual(list(out), [es.SLOPE])
        self.assertEqual(out[es.SLOPE]["changed"], ["2"])
        self.assertTrue(out[es.SLOPE]["first"][2].endswith(" X"))
        removed = {es.FLOOD: base[es.FLOOD]}
        self.assertEqual(ps.diff(base, removed)[es.SLOPE]["note"], "olay artık yok")

    def test_baseline_file_shape(self):
        base = ps.load_baseline()
        self.assertEqual(set(base), set(ps.active_events()))
        for e, seeds in base.items():
            self.assertEqual(set(seeds), {str(s) for s in ps.SEEDS}, e)
            for item in seeds.values():
                self.assertIn("prompt", item)
                self.assertIn("axes", item)


class TestVariety(_Quiet):
    def test_simulation_uses_history_and_counts(self):
        rows = vr.simulate(es.FIRE_TORNADO, runs=6, seed=11)
        self.assertEqual(len(rows), 6)
        m = vr.measure(rows)
        self.assertEqual(m["errors"], 0)
        self.assertEqual(m["rep_environment"], 0)   # ateş hortumu ortamı son 2'yi eler (süreç hafızası)
        self.assertEqual(m["rep_beats"], 0)
        self.assertEqual(vr.simulate(es.FIRE_TORNADO, runs=6, seed=11), rows)

    def test_measure_copies(self):
        r = {"environment": "a", "spot": "s", "weather": "w", "vehicle": "v", "people": 3, "key_visual": "k",
             "beats": "A1+B1", "kadraj": "balkon", "on_plan": "boş", "kamera_modu": "—"}
        m = vr.measure([r, dict(r, beats="A2+B2"), dict(r, spot="t")])
        self.assertEqual(m["copies"], 1)
        self.assertEqual(m["rep_spot"], 1)
        self.assertEqual(m["uniq_beats"], 2)


if __name__ == "__main__":
    unittest.main()
