# 26 Kas 2026, Bahadır: ⭐ Hit kopyası (ateş hortumu) v3 (core/hit_prompts.py HIT_KOPYA_ATES). 6 Kas hiti (370 bin,
# T4+U11, pickup truck, Kie prompt'u 175 kelime) birebir; YALNIZ üç değişiklik: (a) "into a residential area of
# {coğrafya},", (b) "Neighbors flee down the street below as cars speed away past them.", (c) "people and cars fleeing
# below". Coğrafya menüsü H1-H5 + 🎲 Rastgele. Açı ve hortum kilidi bayt bayt, hit ile diff yalnız bu üç yer, 40 tohum
# kaydı tests/fixtures/ates_hortumu_hit_runs_40.json. Ortak sabitler ve pasif v1/v2 + diğerleri kilidi:
# tests/test_hit_kopya_ates.py. Ağ yok.
import asyncio
import json
import os
import random
import sys
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_hit_kopya_ates import (  # noqa: E402
    ANGLE_1, ANGLE_2, CHANGE_A, CHANGE_B, CHANGE_C, DOMAIN, FIXTURE, FORBIDDEN, FT, HIT_PROMPT, HK, LIMITS, NAMES,
    PLACES, REQUIRED, SOURCE, TAIL, TORNADO_1, TORNADO_2, VERSION_LINE, WARNING, _Quiet, build, cp, es, expected,
    gen, hp, pg, reset, undo, v3_snapshot)


class TestHitPrompt(_Quiet):
    def test_source_is_hit_prompt(self):
        self.assertEqual(hp.HIT_PROMPTS[FT]["prompt"].encode("utf-8"), HIT_PROMPT.encode("utf-8"))
        self.assertEqual(hp.HIT_PROMPTS[FT]["notion"], "40ed048d-625e-81db-a114-c29e14ecd258")
        self.assertEqual(hp.HIT_PROMPTS[FT]["parts"]["vehicle"], "pickup truck")
        self.assertEqual((hp.HIT_PROMPTS[FT]["parts"]["beat_2"], hp.HIT_PROMPTS[FT]["parts"]["beat_3"]),
                         ("T4", "U11"))
        self.assertEqual(len(HIT_PROMPT.split()), 175)

    def test_template_is_hit_with_three_changes(self):
        t = HK["template"]
        self.assertEqual(t.count("{place}"), 1)
        self.assertEqual(t.count("{vehicle}"), 1)
        self.assertEqual(HK["vehicles"], ("pickup truck",))
        back = t.format(place="X", vehicle="pickup truck").replace("residential area of X,", "residential area,", 1)
        back = back.replace(CHANGE_B[1], CHANGE_B[0], 1).replace(CHANGE_C[1], CHANGE_C[0], 1)
        self.assertEqual(back.encode("utf-8"), HIT_PROMPT.encode("utf-8"))

    def test_angle_lock_byte_identical(self):
        """AÇI KİLİDİ: iki kamera parçası hit ile ve her coğrafyada bayt bayt aynı."""
        for part in (ANGLE_1, ANGLE_2):
            self.assertEqual(HIT_PROMPT.count(part), 1, part)
            for g in PLACES:
                p = hp.hit_kopya_prompt(g)
                self.assertEqual(p.count(part), 1, (g, part))
                i = p.index(part)
                self.assertEqual(p[i:i + len(part)].encode("utf-8"), part.encode("utf-8"))
        self.assertIn(ANGLE_1 + " " + CHANGE_C[1] + ANGLE_2, hp.hit_kopya_tail())

    def test_tornado_lock_byte_identical(self):
        """HORTUM KİLİDİ: hortum cümlesinin başı ve dönen alev cümlesi hit ile bayt bayt aynı."""
        for g in PLACES:
            p = hp.hit_kopya_prompt(g)
            self.assertTrue(p.startswith("0-4s: " + TORNADO_1 + " into a residential area of "), g)
            self.assertEqual(p.count(TORNADO_2), 1, g)
            self.assertEqual(HIT_PROMPT.count(TORNADO_2), 1)
            self.assertEqual(HIT_PROMPT.split(TORNADO_2)[1].encode("utf-8"), p.split(TORNADO_2)[1].encode("utf-8"))

    def test_diff_with_hit_only_three_places(self):
        """Coğrafya çıkarılıp üç değişiklik geri alınınca hit prompt'u birebir; başka fark yok."""
        import difflib
        for g in PLACES:
            p = hp.hit_kopya_prompt(g)
            self.assertEqual(p, expected(g), g)
            self.assertEqual(undo(p, g).encode("utf-8"), HIT_PROMPT.encode("utf-8"), g)
            ops = [op for op in difflib.SequenceMatcher(None, HIT_PROMPT.split(), p.split(),
                                                        autojunk=False).get_opcodes() if op[0] != "equal"]
            hw = HIT_PROMPT.split()
            zones = []   # hit tarafında üç değişikliğin kelime aralıkları
            for old, _ in (CHANGE_A, CHANGE_B, CHANGE_C):
                c = HIT_PROMPT.index(old)
                i = len(HIT_PROMPT[:c].split())
                zones.append((i, len(HIT_PROMPT[:c + len(old)].split())))
            touched = set()
            for _, i1, i2, _, _ in ops:   # her fark üç bölgeden birinin içinde
                z = [n for n, (a, b) in enumerate(zones) if a <= i1 and i2 <= b]
                self.assertEqual(len(z), 1, (g, i1, i2, hw[i1:i2]))
                touched.add(z[0])
            self.assertEqual(touched, {0, 1, 2}, g)
            # 4-9s kamyonet, 9-15s garaj cümleleri hit ile aynı
            mid = HIT_PROMPT.split("4-9s: ")[1].split(" Handheld footage")[0]
            self.assertIn("4-9s: " + mid + " Handheld footage", p)

    def test_forbidden_and_required(self):
        self.assertEqual(hp.HIT_KOPYA_REQUIRED, REQUIRED)
        self.assertEqual(hp.HIT_KOPYA_FORBIDDEN, FORBIDDEN)
        for g in PLACES:
            p = hp.hit_kopya_prompt(g)
            self.assertNotIn("Two people", p)
            self.assertNotIn("two or three people", p)
            self.assertNotIn("racing fast", p)
            self.assertNotIn("never standing still", p)
            self.assertEqual(hp.hit_kopya_camera_issues(p, g), [])
            for need in REQUIRED:
                self.assertTrue(hp.hit_kopya_camera_issues(p.replace(need, "x"), g), need)
        self.assertTrue(hp.hit_kopya_camera_issues(HIT_PROMPT))

    def test_limits_each_geo(self):
        """Her coğrafya ≤230 kelime ve ≤1400 karakter; en uzun H2 182 / 1071."""
        for g in PLACES:
            p = hp.hit_kopya_prompt(g)
            self.assertLessEqual(len(p.split()), 230, g)
            self.assertLessEqual(len(p), 1400, g)
            self.assertEqual((len(p.split()), len(p)), LIMITS[g], g)
            self.assertEqual(p, hp.hit_kopya_story(g) + " " + TAIL)
        self.assertEqual(max(LIMITS.values()), (182, 1071))

    def test_constants(self):
        self.assertEqual(hp.HIT_KOPYA_MODE_LABEL, "⭐ Hit kopyası (ateş hortumu)")
        self.assertEqual(hp.HIT_KOPYA_VERSION_LINE, VERSION_LINE)
        self.assertEqual(hp.HIT_KOPYA_WARNING, WARNING)
        self.assertEqual(hp.HIT_KOPYA_SOURCE, SOURCE)
        self.assertEqual({g: v["place"] for g, v in HK["geos"].items()}, PLACES)
        self.assertEqual({g: v["name"] for g, v in HK["geos"].items()}, NAMES)
        self.assertEqual(hp.HIT_KOPYA_GEO_BUTTONS, {g: f"{g} {NAMES[g]}" for g in PLACES})
        self.assertEqual(hp.HIT_KOPYA_GEO_BLOCK, 2)
        self.assertEqual(hp.hit_kopya_tail(), TAIL)
        self.assertNotIn("—", hp.HIT_KOPYA_CONFIRM_DESC + WARNING + VERSION_LINE)

    def test_bad_ids(self):
        for bad in (("G1", "pickup truck"), ("H6", "pickup truck"), ("H1", "SUV")):
            with self.assertRaises(es.StructureError):
                hp.hit_kopya_prompt(*bad)

    def test_event_gate_without_synonym(self):
        for g in PLACES:
            self.assertEqual(pg.event_fidelity_issues(FT, hp.hit_kopya_story(g)), [], g)
            self.assertEqual(pg.event_fidelity_issues(FT, hp.hit_kopya_prompt(g)), [], g)


class TestScene(_Quiet):
    def _check(self, d, geo=None):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["hit_kopya_ates"]
        prompt = sc["prompt"]
        self.assertIn(tb["geo"], PLACES)
        if geo:
            self.assertEqual((tb["geo"], tb["geo_source"]), (geo, "menü"))
        self.assertEqual(tb["vehicle"], "pickup truck")
        self.assertEqual(prompt, expected(tb["geo"]))
        self.assertEqual(sc["style_suffix"], TAIL)
        for bad in FORBIDDEN:
            self.assertNotIn(bad.lower(), prompt.lower())
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{FT.lower()}|rooftop terrace above a wooded residential "
                                         f"area##HK:{tb['geo']}|bystander_handheld")
        self.assertIsNone(es.beats_of_combo(d["combo_key"]))   # normal hattın T*/U* LRU'su etkilenmez
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        self.assertEqual((d["selection"]["domain_id"], d["selection"]["event"]), (DOMAIN, FT))
        for other in ("kasirga", "donma_firtina", "approach", "hit", "spec"):
            self.assertNotIn(other, st)
        return tb

    def test_40_seeds_snapshot_and_no_gpt(self):
        """40 tohum (🎲): hatasız, GPT ve normal hat çağrılmaz; kayıt ates_hortumu_hit_runs_40.json ile birebir."""
        with patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))) as normal:
            runs = v3_snapshot()
            for s in range(1, 41):
                self._check(build(s))
        normal.assert_not_called()
        with open(FIXTURE, encoding="utf-8") as fh:
            self.assertEqual(runs, json.load(fh))
        self.assertEqual({r["axes"]["axes"]["cografya"] for r in runs.values()}, set(PLACES))

    def test_menu_geo(self):
        for g in PLACES:
            d = build(3, **{hp.HIT_KOPYA_GEO_KEY: g})
            tb = self._check(d, geo=g)
            self.assertIn(f"Coğrafya: {g} {NAMES[g]} «{PLACES[g]}» (menü)", tb["lines"])
            self.assertEqual(json.loads(d["axes_json"])["excluded"]["cografya"], [])
        with self.assertRaises(es.StructureError):
            build(3, **{hp.HIT_KOPYA_GEO_KEY: "G1"})

    def test_random_lru_last_2(self):
        geos = set()
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            g = [self._check(gen())["geo"] for _ in range(12)]
            for i in range(len(g)):
                self.assertNotIn(g[i], g[max(0, i - 2):i], (seed, g))
            geos |= set(g)
        self.assertEqual(geos, set(PLACES))
        self.assertEqual(hp._KASIRGA_GEO_MEMORY, [])   # başka modların hafızası etkilenmez

    def test_history_sources(self):
        def rec(g, v="pickup truck", event=FT, mod="hit_kopya_ates"):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, "cografya": g, "arac": v}})}
        # eski v2 G kayıtları sayılmaz; son 2 H elenir
        recs = [rec("H1"), {"eksenler": "x"}, rec("G2", "SUV"), rec("H3"), rec("H5", mod="yaklasma"), rec("G4")]
        self.assertEqual(hp.hit_kopya_axes_history(recs, "cografya"), ["H1", "G2", "H3", "G4"])
        calls = []
        for seed in range(1, 11):
            d = build(seed, axes_loader=lambda dom: calls.append(dom) or recs)
            tb = d["structure"]["hit_kopya_ates"]
            self.assertIn(tb["geo"], ("H2", "H4", "H5"))
            axes = json.loads(d["axes_json"])
            self.assertEqual((axes["axes"]["mod"], axes["axes"]["surum"], axes["axes"]["cografya"],
                              axes["axes"]["arac"]), ("hit_kopya_ates", "v3", tb["geo"], "pickup truck"))
            self.assertEqual(axes["excluded"]["cografya"], ["H1", "H3"])
            self.assertEqual(d["trace"]["axes_source"], "notion")
        self.assertEqual(set(calls), {DOMAIN})

        def broken(dom):
            raise RuntimeError("Notion yok")
        d = build(3, axes_loader=broken)
        self.assertEqual(d["trace"]["axes_source"], "bellek")
        self._check(d)

    def test_kie_final_check(self):
        d = build(5)
        st, sc = d["structure"], d["scenes"][0]
        good = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, good), [])
        g = st["hit_kopya_ates"]["geo"]
        for need in REQUIRED:
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": sc["prompt"].replace(need, "x")}), need)
        for old, new in (CHANGE_B, CHANGE_C):
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": sc["prompt"].replace(new, old)}), old)
        other = next(x for x in PLACES if x != g)
        self.assertTrue(hp.hit_kopya_camera_issues(hp.hit_kopya_prompt(other), g))
        self.assertTrue(cp.submit_issues(st, {**good, "style_suffix": "x"}))
        self.assertTrue(cp.submit_issues(st, {**good, "story": sc["story"] + " x"}))
        self.assertEqual(asyncio.run(cp.rewrite_structured(st, "ret", AsyncMock(side_effect=AssertionError("GPT")))),
                         sc["story"])

    def test_approval_lines(self):
        d = build(7)
        tb = d["structure"]["hit_kopya_ates"]
        lines = tb["lines"].split("\n")
        g = tb["geo"]
        self.assertEqual(lines[0], "Mod: ⭐ Hit kopyası (ateş hortumu)")
        self.assertEqual(lines[1], VERSION_LINE)
        self.assertEqual(lines[2], f"Coğrafya: {g} {NAMES[g]} «{PLACES[g]}» (rastgele)")
        self.assertEqual(lines[3], "Araç: pickup truck")
        self.assertEqual(lines[4], SOURCE)
        p = tb["prompt"]
        self.assertEqual(lines[5], f"Kelime: {len(p.split())} (en fazla 230) · karakter: {len(p)} (en fazla 1400)")
        self.assertTrue(lines[6].startswith("Eksenler (⭐ Hit kopyası (ateş hortumu)): sürüm=v3"))
        self.assertTrue(lines[7].startswith("Tekrar önleme: coğrafya son 2 (yalnız rastgele)"))
        self.assertEqual(lines[-1], WARNING)
        self.assertNotIn("—", tb["lines"])


class TestPipelineAndBot(_Quiet):
    def _run(self, approve=True, geo=None):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        seen = {}

        async def fake_gen(config):
            seen["config"] = dict(config)
            reset()
            random.seed(21)
            cfg = {k: v for k, v in config.items() if k not in ("axes_loader", "caption_loader")}
            return await pg.generate_creative_prompts(cfg)
        t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
        t.setUp()
        try:
            rep = _Reporter(approve=approve, needs_approval=True)
            orig = main.run_pipeline

            async def run_with(**kw):
                return await orig(**{**kw, "domain": DOMAIN}, hit_kopya_ates=True, hit_kopya_ates_geo=geo)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=FT)
        finally:
            t.doCleanups()
        return r, rep, seen, t

    def test_pipeline_sends_verbatim_prompt_after_approval(self):
        r, rep, seen, t = self._run(geo="H4")
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["hit_kopya_ates"], True)
        self.assertEqual(seen["config"]["hit_kopya_ates_geo"], "H4")
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kopyası (ateş hortumu)\n" + VERSION_LINE +
                                                     "\nCoğrafya: H4 Yunanistan «Greece» (menü)"))
        self.assertIn(WARNING, info["hit_lines"])
        self.assertEqual(t.create.await_count, 1)
        self.assertEqual(t.create.await_args.args[1], info["prompt"])
        self.assertEqual(info["prompt"], expected("H4"))
        axes = [c.args[0] for c in t.tracker.record_axes.call_args_list]
        self.assertEqual(json.loads(axes[0])["axes"]["mod"], "hit_kopya_ates")

    def test_random_has_no_geo_key(self):
        r, _, seen, _ = self._run()
        self.assertTrue(r["success"], r)
        self.assertNotIn("hit_kopya_ates_geo", seen["config"])

    def test_rejected_approval_no_kie(self):
        r, _, _, t = self._run(approve=False)
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def _ids(self, bot):
        return str(bot.DOMAIN_KEYS.index(DOMAIN)), str(bot.domain_events(DOMAIN).index(FT))

    def test_button_menu_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di, ei = self._ids(bot)
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        rows = [[b.text for b in r] for r in kb.inline_keyboard]
        self.assertEqual(rows, [["✅ Üret", "❌ İptal"], ["⭐ Hit kalıbı", "⭐ Hit kopyası"]])
        # hk → coğrafya menüsü
        upd = _update(data=f"uret:hk:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        self.assertIn("Hangi coğrafya?", call.args[0])
        menu = call.kwargs["reply_markup"]
        self.assertEqual([[b.text for b in r] for r in menu.inline_keyboard],
                         [["H1 Britanya Kolumbiyası", "H2 Avustralya çalılığı"], ["H3 Orta Portekiz", "H4 Yunanistan"],
                          ["H5 Güney Şili"], ["🎲 Rastgele"], ["🔙 Geri"]])
        self.assertEqual(menu.inline_keyboard[-1][0].callback_data, f"uret:e:{di}:{ei}")
        # hk:H3 → onay metni
        upd = _update(data=f"uret:hk:{di}:{ei}:H3")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        text = call.args[0]
        for part in ("Mod: ⭐ Hit kopyası (ateş hortumu)", VERSION_LINE, "Coğrafya: H3 Orta Portekiz «central Portugal»",
                     SOURCE, "✋ Onay", hp.HIT_KOPYA_CONFIRM_DESC):
            self.assertIn(part, text)
        self.assertNotIn("—", text)
        prod = call.kwargs["reply_markup"]
        self.assertEqual([b.text for r in prod.inline_keyboard for b in r], ["✅ Üret", "❌ İptal"])
        self.assertEqual(prod.inline_keyboard[0][0].callback_data, f"uret:hkok:{di}:{ei}:H3")
        # hkok:H3 → üretim
        for gid, geo in (("H3", "H3"), ("r", None)):
            upd = _update(data=f"uret:hkok:{di}:{ei}:{gid}")
            runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
            with patch.object(bot.pipeline, "run_pipeline", runner), \
                 patch.object(bot, "_production_lock", asyncio.Lock()):
                asyncio.run(bot.on_callback(upd, ctx))
            kw = runner.await_args.kwargs
            self.assertEqual((kw["domain"], kw["event"], kw["hit_kopya_ates"]), (DOMAIN, FT, True))
            self.assertEqual(kw.get("hit_kopya_ates_geo"), geo)
            for other in ("kasirga", "donma_firtina", "cadde_yaklasma", "hortum_yaklasma", "heli_yaklasma",
                          "kul_yaklasma", "orman_yaklasma", "dalga24", "approach_env", "hit_env"):
                self.assertNotIn(other, kw)
            self.assertTrue(kw["reporter"].needs_approval)
        started = upd.callback_query.edit_message_text.await_args_list[0].args[0]
        self.assertIn("/ ⭐ Hit kopyası / 🎲 Rastgele (son 2 coğrafya elenir)", started)
        wf = str(bot.domain_events(DOMAIN).index(es.WILDFIRE))
        for bad in (f"uret:hk:{di}", f"uret:hk:{di}:{wf}", f"uret:hkok:{di}:{ei}", f"uret:hkok:{di}:{ei}:x",
                    f"uret:hk:{di}:{ei}:G1", f"uret:hkok:{di}:{ei}:G3", f"uret:hk:{di}:{ei}:H6"):
            upd = _update(data=bad)
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertIn("Geçersiz", upd.callback_query.edit_message_text.await_args.args[0], bad)
        busy = asyncio.Lock()
        asyncio.run(busy.acquire())
        with patch.object(bot, "_production_lock", busy):
            upd = _update(data=f"uret:hkok:{di}:{ei}:H1")
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertEqual(upd.callback_query.edit_message_text.await_args.args[0], bot.BUSY_TEXT)
        for m in (kb, menu, bot.hit_kopya_produce_keyboard(di, ei, "H5")):
            for b in (b for r in m.inline_keyboard for b in r):
                self.assertLessEqual(len(b.callback_data.encode()), 64)

    def test_approach_code_still_there(self):
        """Yaklaşma (ateş hortumu) menüde yok ama kodu ve adımları duruyor."""
        import bot
        from test_tur29_infra import _context, _update
        di, ei = self._ids(bot)
        self.assertIs(bot.APPROACH_MENU, False)
        self.assertTrue(hp.yaklasma_is_active(FT))
        ctx = _context()
        upd = _update(data=f"uret:ya:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertIn("(forest_edge)", " ".join(b.text for r in kb.inline_keyboard for b in r))

    def test_only_fire_tornado(self):
        for e in es.EVENT_SKELETONS:
            self.assertEqual(hp.hit_kopya_is_active(e), e == FT, e)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_build_scene(DOMAIN, es.WILDFIRE)


if __name__ == "__main__":
    import unittest
    unittest.main()
