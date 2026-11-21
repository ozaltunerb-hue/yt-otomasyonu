"""21 Kas 2026: 🌀 Kasırga "Kasırga kıyı kasabasını döver" coğrafya menüsü.

Akış: 🌀 Kasırga → olay → coğrafya ekranı (G1-G6 + 🎲 Rastgele + 🔙 Geri) → ksg:<Gx|r> onay metni → ksok:<Gx|r> üretim.
Menüden seçilen G o üretim için sabit; araç, orta, final, kişi mevcut LRU ile. 🎲 Rastgele bugünkü seçimle birebir.
Olay metinleri, kamera ve havuzlar değişmedi (KİLİT: 40 tohum, bütün olaylar + bütün modlar, Rastgele dahil).
"""
import asyncio
import hashlib
import json
import logging
import os
import random
import sys
import unittest
from unittest.mock import AsyncMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

import test_hit_kopya_sel as ths   # noqa: E402  (önce: core.* döngüsel import sırası)
import test_kasirga as tk   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.hit_prompts as hp   # noqa: E402
import core.prompt_generator as pg   # noqa: E402

EVENT, DOMAIN = tk.EVENT, tk.DOMAIN
GEOS = ("G1", "G2", "G3", "G4", "G5", "G6")
BUTTONS = {"G1": "🇺🇸 ABD Florida", "G2": "🇵🇭 Filipinler", "G3": "🌴 Meksika Karayipleri", "G4": "🇮🇳 Hindistan",
           "G5": "🇨🇺 Küba", "G6": "🇯🇵 Japonya"}
# Değişiklikten ÖNCEKİ kodla (d73e8e5) alınan kayıtlar: 🌀 Kasırga 40 tohum (🎲 Rastgele yolu) ve bütün olaylar +
# bütün modlar (test_hit_kopya_sel zinciri + ⭐ Hit kopyası (ani sel)) 40 tohum
KASIRGA_RANDOM_SHA256 = "c96655d503dbad8716b754039b55ca1cf9f760c4dde22663edbc3c9fd16b21e6"   # = tk.KASIRGA_V1_SHA256
# 21 Kas (2): kasırga v2 (açılış + F2) bilerek değişti; canlı 🎲 Rastgele kaydı artık tk.KASIRGA_SHA256 (v2 fixture).
# Zincirdeki kasırga kaydı v1 fixture'ından gelir, FULL_SHA256 değişmez.
FULL_SHA256 = "4db630349122185e7437b1dd501802a43cbeedaabcffc56367bced930ef4fbeb"


def _hash(data) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def gen_geo(geo=None, **extra) -> dict:
    with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
        return tk.gen(**({"kasirga_geo": geo} if geo is not None else {}), **extra)


class TestMenuScene(tk._Quiet):
    def test_each_menu_choice_produces_that_geo(self):
        for g in GEOS:
            for seed in range(1, 21):
                tk.reset()
                random.seed(seed)
                d = gen_geo(g)
                tb = d["structure"]["kasirga"]
                sc = d["scenes"][0]
                self.assertEqual(tb["geo"], g, (g, seed))
                self.assertEqual(sc["prompt"], hp.kasirga_prompt(g, tb["people"], tb["mid"], tb["vehicle"],
                                                                 tb["final"]))
                self.assertIn(tk.PLACES[g][1], sc["prompt"])
                for other in GEOS:
                    if other != g:
                        self.assertNotIn(tk.PLACES[other][1], sc["prompt"])
                axes = json.loads(d["axes_json"])
                self.assertEqual(axes["axes"]["cografya"], g)
                self.assertEqual(axes["axes"]["cografya_secim"], "menu")
                self.assertEqual(axes["excluded"], {"cografya": []})
                self.assertEqual(d["trace"]["cografya"], g)
                self.assertEqual(d["trace"]["cografya_secim"], "menu")
                self.assertEqual(hp._KASIRGA_GEO_MEMORY[-1], g)   # menü seçimi de sonraki 🎲 için sayılır
                lines = tb["lines"].split("\n")
                self.assertEqual(lines[1], tk.VERSION_LINE)   # 21 Kas (2)
                self.assertEqual(lines[2], f"Coğrafya: {g} {tk.PLACES[g][0]} (menü)")
                self.assertIn(f"Tekrar önleme: coğrafya menüden ({g}) · araç son 2 · orta son 1 · final son 1",
                              tb["lines"])

    def test_menu_ignores_geo_lru_but_other_axes_keep_lru(self):
        for seed in range(1, 11):
            tk.reset()
            random.seed(seed)
            runs = [gen_geo("G3")["structure"]["kasirga"] for _ in range(10)]
            self.assertEqual({r["geo"] for r in runs}, {"G3"})   # son 3'te olsa da sabit
            for key in ("mid", "final"):
                vals = [r[key] for r in runs]
                for i in range(1, len(vals)):
                    self.assertNotEqual(vals[i], vals[i - 1], (seed, key, vals))
            v = [r["vehicle"] for r in runs]
            for i in range(len(v)):
                self.assertNotIn(v[i], v[max(0, i - 2):i], (seed, v))
            self.assertEqual(hp._KASIRGA_VEHICLE_MEMORY[-10:], v)
            self.assertLessEqual({r["people"] for r in runs}, {4, 5})

    def test_menu_with_notion_records(self):
        """Notion "Eksenler" geçmişi okunduğunda da menü G'si sabit; araç geçmişi kayıtlardan."""
        def rec(g, v, tag):
            return {"eksenler": json.dumps({"event": EVENT, "axes": {"mod": "kasirga", "cografya": g, "arac": v,
                                                                     "beats": tag}})}
        records = [rec("G1", "SUV", "O1+F1"), rec("G5", "pickup truck", "O2+F2"), rec("G5", "small car", "O3+F3")]
        for seed in range(1, 11):
            tk.reset()
            random.seed(seed)
            sc = hp.kasirga_build_scene(DOMAIN, EVENT, [], records, history_source="notion", geo="G5")
            tb = sc["structure"]["kasirga"]
            self.assertEqual(tb["geo"], "G5")
            self.assertNotIn(tb["vehicle"], ("pickup truck", "small car"))
            self.assertNotEqual(tb["mid"], "O3")
            self.assertNotEqual(tb["final"], "F3")

    def test_random_path_unchanged(self):
        """🎲 Rastgele: kasirga_geo yok ya da None, bugünkü kayıtla birebir; Onay satırında "(rastgele)"."""
        runs, runs_none = {}, {}
        for s in range(1, 41):
            for target, extra in ((runs, {}), (runs_none, {"kasirga_geo": None})):
                tk.reset()
                random.seed(s)
                with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
                    d = tk.gen(**extra)
                sc = d["scenes"][0]
                axes = json.loads(d["axes_json"])
                axes.pop("caption", None)
                self.assertNotIn("cografya_secim", axes["axes"])
                self.assertNotIn("cografya_secim", d["trace"])
                tb = d["structure"]["kasirga"]
                self.assertEqual(tb["lines"].split("\n")[2], f"Coğrafya: {tb['geo']} {tk.PLACES[tb['geo']][0]} "
                                                             "(rastgele)")
                target[str(s)] = {"prompt": sc["prompt"], "story": sc["story"], "suffix": sc["style_suffix"],
                                  "combo": d["combo_key"], "axes": axes}
        self.assertEqual(runs, runs_none)
        self.assertEqual(_hash(runs), tk.KASIRGA_SHA256)   # 21 Kas (2): v2 (v1 = KASIRGA_RANDOM_SHA256, fixture)

    def test_bad_geo(self):
        for bad in ("G7", "g1", "", "r"):
            tk.reset()
            with self.assertRaises(es.StructureError):
                hp.kasirga_build_scene(DOMAIN, EVENT, [], None, geo=bad)

    def test_pools_untouched(self):
        self.assertEqual(hp.KASIRGA_GEO_BUTTONS, BUTTONS)
        self.assertEqual({g: (v["name"], v["place"]) for g, v in hp.KASIRGA["geos"].items()}, tk.PLACES)
        self.assertEqual(hp.KASIRGA["vehicles"], tk.VEHICLES)
        self.assertEqual(hp.KASIRGA["tail"], tk.TAIL)
        for t in BUTTONS.values():
            self.assertNotIn("—", t)


class TestLock(tk._Quiet):
    def test_full_snapshot_all_events_and_modes(self):
        """KİLİT: bütün olaylar (normal yol) + bütün modlar (🌀 Kasırga 🎲 Rastgele dahil), 40 tohum, fark 0."""
        snap = ths.others_snapshot()
        snap["modes"]["hit_kopya_sel"] = ths.hks_snapshot()
        self.assertIn("kasirga", snap["modes"])
        self.assertEqual(len(snap["modes"]["kasirga"]), 40)
        self.assertEqual(_hash(snap["modes"]["kasirga"]), KASIRGA_RANDOM_SHA256)
        self.assertEqual(_hash(snap), FULL_SHA256)


class TestPipelineAndBot(tk._Quiet):
    def test_pipeline_passes_geo(self):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        for geo in ("G2", None):
            seen = {}

            async def fake_gen(config):
                seen["config"] = dict(config)
                tk.reset()
                random.seed(21)
                cfg = {k: v for k, v in config.items() if k not in ("axes_loader", "caption_loader")}
                return await pg.generate_creative_prompts(cfg)
            t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
            t.setUp()
            try:
                rep = _Reporter(approve=True, needs_approval=True)
                orig = main.run_pipeline

                async def run_with(**kw):
                    return await orig(**{**kw, "domain": DOMAIN}, kasirga=True, kasirga_geo=geo)
                with patch.object(main, "run_pipeline", run_with):
                    r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=EVENT)
            finally:
                t.doCleanups()
            self.assertTrue(r["success"], r)
            info = [c[1] for c in rep.calls if c[0] == "approve"][0]
            if geo:
                self.assertEqual(seen["config"]["kasirga_geo"], geo)
                self.assertIn(f"\nCoğrafya: {geo} {tk.PLACES[geo][0]} (menü)\n", info["hit_lines"])
                self.assertIn(tk.PLACES[geo][1], info["prompt"])
            else:
                self.assertNotIn("kasirga_geo", seen["config"])
                self.assertIn(" (rastgele)\n", info["hit_lines"])
            self.assertEqual(t.create.await_args.args[1], info["prompt"])

    def test_bot_menu_choice_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        ctx = _context()
        for i, g in enumerate(GEOS, 1):
            upd = _update(data=f"uret:ksg:{g}")
            asyncio.run(bot.on_callback(upd, ctx))
            call = upd.callback_query.edit_message_text.await_args
            self.assertIn(f"Coğrafya: {g} {BUTTONS[g]}\n", call.args[0])
            self.assertIn(hp.KASIRGA_CONFIRM_DESC, call.args[0])
            self.assertEqual([b.callback_data for r in call.kwargs["reply_markup"].inline_keyboard for b in r],
                             [f"uret:ksok:{g}", "uret:x"])
            upd = _update(data=f"uret:ksok:{g}")
            runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
            with patch.object(bot.pipeline, "run_pipeline", runner), \
                    patch.object(bot, "_production_lock", asyncio.Lock()):
                asyncio.run(bot.on_callback(upd, ctx))
            kw = runner.await_args.kwargs
            self.assertEqual((kw["domain"], kw["event"], kw["kasirga"], kw["kasirga_geo"]), (DOMAIN, EVENT, True, g))
            started = upd.callback_query.edit_message_text.await_args_list[0].args[0]
            self.assertIn(f"🚀 Üretim başladı: 🌀 Kasırga / {tk.EVENT_LABEL} / {g} {BUTTONS[g]}", started)
        # argümansız eski düğme (önceki mesajlar): 🎲 Rastgele
        upd = _update(data="uret:ksok")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        self.assertNotIn("kasirga_geo", runner.await_args.kwargs)
        # 🔙 Geri → Kasırga olay menüsü
        upd = _update(data="uret:ks")
        asyncio.run(bot.on_callback(upd, ctx))
        cbs = [b.callback_data for r in upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
               .inline_keyboard for b in r]
        self.assertEqual(cbs, ["uret:kse", "uret:back"])

    def test_callback_prefix_unique(self):
        """"ksg" başka bir akışta kullanılmıyor; bütün düğmeler 64 bayt sınırında."""
        import bot
        with open(os.path.join(ROOT, "bot.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count('"ksg"'), 2)   # dispatch + _on_kasirga
        self.assertEqual(src.count("}ksg:"), 2)   # coğrafya düğmeleri + Rastgele
        for b in (b for r in bot.kasirga_geo_keyboard().inline_keyboard for b in r):
            self.assertLessEqual(len(b.callback_data.encode()), 64)


if __name__ == "__main__":
    unittest.main()
