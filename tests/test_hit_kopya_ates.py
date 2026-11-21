# 16 Kas 2026, Bahadır: ateş hortumu "⭐ Hit kopyası" modu (core/hit_prompts.py HIT_KOPYA_ATES).
# Sebep: Yaklaşma modundan çıkan video (Portekiz, 16 Kas paylaşımı) zayıf kaldı, hortum uzaktan başladığı için ilk
# saniyeler boştu. En iyi ateş hortumu (6 Kas paylaşımı, 5 Kas 00:13 üretimi, "Filmed as the truck is swept away",
# T4+U11, forest_edge, çatı terası) farklıydı: hortum ilk saniyeden kadrajın yarısını dolduran bir dev. Hit'in Kie
# prompt'u kelimesi kelimesine; sadece coğrafya ({place}) ve araç ({vehicle}) değişir. GPT yok. Yaklaşma menüden kalktı
# (kodu duruyor). KASIRGA / DONMA_FIRTINA ile aynı kod-hikâye yolu. Diğer 19 olay ve 14 mod birebir aynı (40 tohum).
# Ağ yok.
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

import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.hit_prompts as hp   # noqa: E402
import core.prompt_generator as pg   # noqa: E402
import prompt_snapshot as ps   # noqa: E402

FT = "Fire tornado tears across a burning roadside"
DOMAIN = "fire_disasters"
HK = hp.HIT_KOPYA_ATES
# 5 Kas 00:13 üretiminin (6 Kas paylaşımı) Kie prompt'u, birebir (Notion üretim kaydı "Prompt" alanı)
HIT_PROMPT = (
    "0-4s: A colossal spinning fire tornado, a twisting funnel several times taller than the houses and "
    "trees, tears out of a burning forest into a residential area, its wide base engulfing the houses. Two "
    "people run away in the street below. 4-9s: The pickup truck is shoved sideways as the huge base of the "
    "fire tornado sweeps past right behind it. 9-15s: A wooden garage beside a house across the street bursts"
    " apart, burning boards spiraling up. Handheld footage filmed on a rooftop terrace above a wooded "
    "residential area, high vantage, the tornado filling half the frame, top never cut off, two or three "
    "people fleeing below; slight hand shake, the camera stays fixed, an empty foreground; one continuous "
    "shot, no zoom, no cuts, no person or face close to the camera. Civilians in everyday clothes, no hazmat "
    "suits, never CGI. A rotating funnel of flame with orbiting debris, never a straight plume or explosion. "
    "Everything moves in real time, never in slow motion, people run at full speed. No readable signs, text "
    "or flags.")
PLACES = {"G1": ("Kanada", "a Canadian lakeside town"), "G2": ("Avustralya", "an Australian bush town"),
          "G3": ("Portekiz", "a Portuguese hillside village"), "G4": ("ABD", "a Californian suburb"),
          "G5": ("Yunanistan", "a Greek coastal town"), "G6": ("Şili", "a Chilean hillside town")}
VEHICLES = ("pickup truck", "SUV", "delivery van")
TAIL = HIT_PROMPT[HIT_PROMPT.index("Handheld footage"):]
# 17 Kas: SADECE hareket. Hit metnine iki ekleme (hortum ilk iki üretimde, Yunanistan ve Kanada, neredeyse yerinde
# durdu). Hit metniyle izin verilen farklar: {place}, {vehicle} ve bu iki ekleme.
ADD_OPENING = "racing fast across the neighborhood,"
ADD_TAIL = "The fire tornado keeps moving fast the whole time, never standing still."
NEW_TAIL = TAIL.replace("explosion. ", "explosion. " + ADD_TAIL + " ", 1)
REQUIRED = ("several times taller than the houses", "the tornado filling half the frame", "rooftop terrace",
            "never CGI", "racing fast across the neighborhood", "never standing still")
FORBIDDEN = ("pans to follow", "Full action", "Until the last frame", "approaches from", "in the distance")
SOURCE = "Kaynak: 5 Kas 00:13 üretimi (6 Kas paylaşımı), birebir"
WARNING = ("⚠️ Hit karşılaştırması: hortum ilk saniyeden kadrajın yarısını dolduruyor mu, video 6 Kas hit'iyle boy "
           "ölçüşür mü?")
# Değişiklikten önceki kod (20124a8): 19 olay (normal yol) + 13 mod + 🌀 Kasırga, 40 tohum
OTHERS_SHA256 = "13591326765059ef0be36cf9b9b75e1ae182c42f21a17c74b61871b99fab17be"


class _Quiet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.WARNING)
        cls._rec = patch.object(cp, "record_story_source", lambda entry: None)
        cls._rec.start()

    @classmethod
    def tearDownClass(cls):
        cls._rec.stop()
        logging.disable(logging.NOTSET)


def reset():
    ps.reset_memory()
    for name in dir(hp):
        if name.startswith("_") and name.endswith("_MEMORY") and isinstance(getattr(hp, name), list):
            getattr(hp, name).clear()


def gen(**extra) -> dict:
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": FT, "hit_kopya_ates": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def expected(g: str, v: str) -> str:
    """Hit prompt'unun kendisinden: "residential area" (ilk) → "residential area of {place}, racing fast across the
    neighborhood,", "pickup truck" → araç, stil ekine "never standing still" cümlesi (17 Kas)."""
    return HIT_PROMPT.replace("into a residential area,",
                              f"into a residential area of {PLACES[g][1]}, {ADD_OPENING}", 1) \
                     .replace("The pickup truck is shoved", f"The {v} is shoved", 1) \
                     .replace("explosion. ", "explosion. " + ADD_TAIL + " ", 1)


def others_snapshot() -> dict:
    import test_kasirga as tk

    def strip(js):
        try:
            d = json.loads(js)
        except (TypeError, ValueError):
            return js
        d.pop("caption", None)
        return d
    snap = tk.others_snapshot()
    # 21 Kas (2): 🌀 Kasırga v2 bilerek değişti (açılış + F2). Bu kilit diğer olay/modlar içindir; kasırga kaydı v1
    # (35411fc) fixture'ından gelir (tk.KASIRGA_V1_SHA256), canlı v2 test_kasirga KASIRGA_SHA256 ile kilitli.
    with open(tk.FIXTURE_V1, encoding="utf-8") as fh:
        snap["modes"]["kasirga"] = json.load(fh)
    return snap


def snapshot_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class TestTemplate(_Quiet):
    def test_template_is_hit_prompt_verbatim(self):
        """Şablon = hit prompt'u; farklar yalnızca "of {place}", araç yeri ve 17 Kas'ın iki hareket eklemesi."""
        self.assertEqual(hp.HIT_PROMPTS[FT]["prompt"], HIT_PROMPT)
        t = HK["template"]
        self.assertEqual(t.count("{place}"), 1)
        self.assertEqual(t.count("{vehicle}"), 1)
        self.assertEqual(t.count(ADD_OPENING), 1)
        self.assertEqual(t.count(ADD_TAIL), 1)
        self.assertIn("residential area of {place}, " + ADD_OPENING + " its wide base engulfing the houses.", t)
        self.assertIn("never a straight plume or explosion. " + ADD_TAIL + " Everything moves in real time", t)
        self.assertEqual(t.replace(" of {place}", "", 1).replace("{vehicle}", "pickup truck")
                         .replace(" " + ADD_OPENING, "", 1).replace(" " + ADD_TAIL, "", 1), HIT_PROMPT)
        self.assertEqual(hp.hit_kopya_tail(), NEW_TAIL)

    def test_v1_template_passive(self):
        """16 Kas şablonu HIT_KOPYA_ATES_V1 pasif kayıtta: birebir eski metin, aktif şablon değil."""
        v1 = hp.HIT_KOPYA_PASIF["HIT_KOPYA_ATES_V1"]
        self.assertIs(v1, hp.HIT_KOPYA_ATES_V1)
        self.assertEqual(v1["template"].replace(" of {place}", "", 1).replace("{vehicle}", "pickup truck"), HIT_PROMPT)
        self.assertEqual(v1["tail_start"], HK["tail_start"])
        self.assertNotIn(ADD_OPENING, v1["template"])
        self.assertNotIn(ADD_TAIL, v1["template"])
        self.assertNotEqual(v1["template"], HK["template"])
        for g in PLACES:
            for v in VEHICLES:
                self.assertNotIn(v1["template"].split(" Handheld")[0].format(place=PLACES[g][1], vehicle=v),
                                 hp.hit_kopya_prompt(g, v))

    def test_required_list(self):
        self.assertEqual(hp.HIT_KOPYA_REQUIRED, REQUIRED)
        self.assertEqual(hp.HIT_KOPYA_FORBIDDEN, FORBIDDEN)
        self.assertEqual(hp.HIT_KOPYA_MODE_LABEL, "⭐ Hit kopyası (ateş hortumu)")
        self.assertEqual({g: (v["name"], v["place"]) for g, v in HK["geos"].items()}, PLACES)
        self.assertEqual(HK["vehicles"], VEHICLES)
        self.assertEqual((hp.HIT_KOPYA_GEO_BLOCK, hp.HIT_KOPYA_GEO_SEED, hp.HIT_KOPYA_VEHICLE_BLOCK),
                         (3, ("G3",), 2))

    def test_all_18_combos_within_limits(self):
        words, chars = [], []
        for g in PLACES:
            for v in VEHICLES:
                p = hp.hit_kopya_prompt(g, v)
                self.assertEqual(p, expected(g, v), (g, v))
                self.assertEqual(p, hp.hit_kopya_story(g, v) + " " + NEW_TAIL)
                words.append((len(p.split()), g, v))
                chars.append((len(p), g, v))
                self.assertLessEqual(len(p.split()), 230)
                self.assertLessEqual(len(p), 1400)
                self.assertEqual(hp.hit_kopya_camera_issues(p, g), [])
        self.assertEqual(len(words), 18)
        self.assertEqual(min(w for w, *_ in words), 195)   # 17 Kas (önce 178-180, en uzun 1059)
        self.assertEqual(max(w for w, *_ in words), 197)
        self.assertEqual(min(chars), (1151, "G4", "SUV"))
        self.assertEqual(max(chars), (1169, "G3", "pickup truck"))

    def test_bad_ids(self):
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_prompt("G7", "SUV")
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_prompt("G1", "small car")

    def test_event_gate_without_synonym(self):
        """Ana hattın olay denetimi bu modda da geçer; eş anlamlı eklenmedi."""
        for g in PLACES:
            for v in VEHICLES:
                self.assertEqual(pg.event_fidelity_issues(FT, hp.hit_kopya_story(g, v)), [], (g, v))
                self.assertEqual(pg.event_fidelity_issues(FT, hp.hit_kopya_prompt(g, v)), [], (g, v))
        self.assertTrue(pg.event_fidelity_issues(FT, "A garage bursts apart in a quiet street."))


class TestScene(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["hit_kopya_ates"]
        prompt = sc["prompt"]
        self.assertIn(tb["geo"], PLACES)
        self.assertIn(tb["vehicle"], VEHICLES)
        self.assertEqual(prompt, expected(tb["geo"], tb["vehicle"]))
        self.assertEqual(sc["style_suffix"], NEW_TAIL)
        for need in REQUIRED + (PLACES[tb["geo"]][1],):
            self.assertIn(need, prompt)
        for bad in FORBIDDEN:
            self.assertNotIn(bad.lower(), prompt.lower())
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{FT.lower()}|rooftop terrace above a wooded residential "
                                         f"area##HK:{tb['geo']}|bystander_handheld")
        self.assertIsNone(es.beats_of_combo(d["combo_key"]))   # normal hattın T*/U* LRU'su etkilenmez
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        self.assertEqual(pg.event_fidelity_issues(FT, sc["story"]), [])
        self.assertEqual((d["selection"]["domain_id"], d["selection"]["event"]), (DOMAIN, FT))
        for other in ("kasirga", "donma_firtina", "approach", "hit", "spec"):
            self.assertNotIn(other, st)
        return tb

    def test_40_seeds_no_error_and_no_gpt(self):
        """EK KONTROL: 40 tohumda hatasız; GPT hiç çağrılmaz, OpenAI istemcisi istenmez, normal hat çalışmaz."""
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))) as normal:
            seen = set()
            for seed in range(1, 41):
                tb = self._check(build(seed))
                seen.add((tb["geo"], tb["vehicle"]))
                self.assertNotEqual(tb["geo"], "G3")   # ilk üretim: G3 tohumu
        gpt.assert_not_called()
        normal.assert_not_called()
        self.assertGreater(len(seen), 8)

    def test_lru_and_g3_seed(self):
        geos, vehs = set(), set()
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(12)]
            g = [r["geo"] for r in runs]
            self.assertNotIn("G3", g[:3], (seed, g))   # G3 tohumu: ilk 3 üretimde G3 gelmez
            hist = ["G3"] + g
            for i in range(1, len(hist)):
                self.assertNotIn(hist[i], hist[max(0, i - 3):i], (seed, g))
            v = [r["vehicle"] for r in runs]
            for i in range(len(v)):
                self.assertNotIn(v[i], v[max(0, i - 2):i], (seed, v))
            self.assertEqual(hp._HIT_KOPYA_GEO_MEMORY[-12:], g)
            self.assertEqual(hp._HIT_KOPYA_VEHICLE_MEMORY[-12:], v)
            geos |= set(g)
            vehs |= set(v)
        self.assertEqual(geos, set(PLACES))
        self.assertEqual(vehs, set(VEHICLES))
        self.assertEqual(hp._KASIRGA_GEO_MEMORY, [])   # başka modların hafızası etkilenmez

    def test_history_sources(self):
        def rec(g, v, event=FT, mod="hit_kopya_ates"):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, "cografya": g, "arac": v}})}
        recs = [rec("G1", "SUV"), {"eksenler": "x"}, rec("G2", "pickup truck"), rec("G5", "SUV", mod="yaklasma"),
                rec("G4", "delivery van", event=hp.KASIRGA_EVENT, mod="kasirga")]
        self.assertEqual(hp.hit_kopya_axes_history(recs, "cografya"), ["G1", "G2"])
        self.assertEqual(hp.hit_kopya_axes_history(recs, "arac"), ["SUV", "pickup truck"])
        self.assertIsNone(hp.hit_kopya_axes_history(None, "arac"))
        calls = []
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: calls.append(dom) or recs)
            tb = d["structure"]["hit_kopya_ates"]
            self.assertIn(tb["geo"], ("G4", "G5", "G6"))    # son 3 (G3 tohum, G1, G2) elenir
            self.assertEqual(tb["vehicle"], "delivery van")  # son 2 (SUV, pickup truck) elenir
            axes = json.loads(d["axes_json"])
            self.assertEqual(axes["event"], FT)
            self.assertEqual((axes["axes"]["mod"], axes["axes"]["cografya"], axes["axes"]["arac"]),
                             ("hit_kopya_ates", tb["geo"], tb["vehicle"]))
            self.assertEqual(axes["excluded"]["cografya"], ["G1", "G2", "G3"])
            self.assertEqual(d["trace"]["axes_source"], "notion")
        self.assertEqual(set(calls), {DOMAIN})

        def broken(dom):
            raise RuntimeError("Notion yok")
        reset()
        random.seed(3)
        d = gen(axes_loader=broken)
        self.assertEqual(d["trace"]["axes_source"], "bellek")
        self._check(d)

    def test_kie_final_check_required_and_forbidden(self):
        reset()
        random.seed(5)
        d = gen()
        st, sc = d["structure"], d["scenes"][0]
        good = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, good), [])
        for need in REQUIRED:
            bad = sc["prompt"].replace(need, "x")
            self.assertTrue(hp.hit_kopya_camera_issues(bad, st["hit_kopya_ates"]["geo"]), need)
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": bad}), need)
        self.assertTrue(hp.hit_kopya_camera_issues(sc["prompt"].replace(PLACES[st["hit_kopya_ates"]["geo"]][1],
                                                                        "a town"), st["hit_kopya_ates"]["geo"]))
        for bad_phrase in FORBIDDEN:
            bad = sc["prompt"].replace("high vantage", f"high vantage, {bad_phrase.lower()}")
            self.assertTrue(hp.hit_kopya_camera_issues(bad), bad_phrase)
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": bad}), bad_phrase)
        other = next(g for g in PLACES if g != st["hit_kopya_ates"]["geo"])
        self.assertTrue(hp.hit_kopya_camera_issues(hp.hit_kopya_prompt(other, "SUV"), st["hit_kopya_ates"]["geo"]))
        self.assertTrue(cp.submit_issues(st, {**good, "style_suffix": "x"}))
        self.assertTrue(cp.submit_issues(st, {**good, "story": sc["story"] + " x"}))
        self.assertEqual(asyncio.run(cp.rewrite_structured(st, "ret", AsyncMock(side_effect=AssertionError("GPT")))),
                         sc["story"])

    def test_approval_lines(self):
        reset()
        random.seed(7)
        d = gen()
        tb = d["structure"]["hit_kopya_ates"]
        lines = tb["lines"].split("\n")
        g = tb["geo"]
        self.assertEqual(lines[0], "Mod: ⭐ Hit kopyası (ateş hortumu)")
        self.assertEqual(lines[1], f"Coğrafya: {g} {PLACES[g][0]} «{PLACES[g][1]}»")
        self.assertEqual(lines[2], f"Araç: {tb['vehicle']}")
        self.assertEqual(lines[3], SOURCE)
        p = tb["prompt"]
        self.assertEqual(lines[4], f"Kelime: {len(p.split())} (en fazla 230) · karakter: {len(p)} (en fazla 1400)")
        self.assertTrue(lines[5].startswith("Eksenler (⭐ Hit kopyası (ateş hortumu)): coğrafya="))
        self.assertTrue(lines[6].startswith("Tekrar önleme: coğrafya son 3 elendi (G3 tohum) · araç son 2"))
        self.assertEqual(lines[-1], WARNING)
        self.assertNotIn("—", tb["lines"])


class TestPipelineAndBot(_Quiet):
    def _run(self, poll=None, approve=True):
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
                return await orig(**{**kw, "domain": DOMAIN}, hit_kopya_ates=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=FT, poll=poll)
        finally:
            t.doCleanups()
        return r, rep, seen, t

    def test_pipeline_sends_verbatim_prompt_after_approval(self):
        r, rep, seen, t = self._run()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["hit_kopya_ates"], True)
        for other in ("kasirga", "donma_firtina", "approach_env", "hit_env"):
            self.assertNotIn(other, seen["config"])
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kopyası (ateş hortumu)\nCoğrafya: G"))
        self.assertIn(SOURCE, info["hit_lines"])
        self.assertIn(WARNING, info["hit_lines"])
        self.assertEqual(t.create.await_count, 1)
        self.assertEqual(t.create.await_args.args[1], info["prompt"])
        self.assertTrue(info["prompt"].endswith(NEW_TAIL))
        axes = [c.args[0] for c in t.tracker.record_axes.call_args_list]
        self.assertEqual(json.loads(axes[0])["axes"]["mod"], "hit_kopya_ates")

    def test_event_gate_blocks_mismatch(self):
        import main
        with patch.object(main, "event_fidelity_issues", side_effect=lambda e, t, *a: ["uyuşmuyor"]
                          if e == FT else []):
            r, _, _, t = self._run()
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def test_rejected_approval_no_kie(self):
        r, _, _, t = self._run(approve=False)
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def _ids(self, bot):
        return str(bot.DOMAIN_KEYS.index(DOMAIN)), str(bot.domain_events(DOMAIN).index(FT))

    def test_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di, ei = self._ids(bot)
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        rows = [[b.text for b in r] for r in kb.inline_keyboard]
        self.assertEqual(rows, [["✅ Üret", "❌ İptal"], ["⭐ Hit kalıbı", "⭐ Hit kopyası"]])
        self.assertNotIn("⭐ Hit kalıbı · Yaklaşma", [t for r in rows for t in r])
        cbs = [b.callback_data for r in kb.inline_keyboard for b in r]
        self.assertIn(f"uret:hk:{di}:{ei}", cbs)
        upd = _update(data=f"uret:hk:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        text = call.args[0]
        for part in ("Mod: ⭐ Hit kopyası (ateş hortumu)", SOURCE, "✋ Onay", hp.HIT_KOPYA_CONFIRM_DESC):
            self.assertIn(part, text)
        self.assertNotIn("—", text)
        self.assertEqual([b.text for r in call.kwargs["reply_markup"].inline_keyboard for b in r], ["✅ Üret", "❌ İptal"])
        upd = _update(data=f"uret:hkok:{di}:{ei}")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["domain"], kw["event"], kw["hit_kopya_ates"]), (DOMAIN, FT, True))
        for other in ("kasirga", "donma_firtina", "cadde_yaklasma", "hortum_yaklasma", "heli_yaklasma",
                      "kul_yaklasma", "orman_yaklasma", "dalga24", "approach_env", "hit_env"):
            self.assertNotIn(other, kw)
        self.assertTrue(kw["reporter"].needs_approval)
        started = upd.callback_query.edit_message_text.await_args_list[0].args[0]
        self.assertIn("/ ⭐ Hit kopyası", started)
        wf = str(bot.domain_events(DOMAIN).index(es.WILDFIRE))
        for bad in (f"uret:hk:{di}", f"uret:hk:{di}:{wf}", f"uret:hkok:{di}:{ei}:x"):
            upd = _update(data=bad)
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertIn("Geçersiz", upd.callback_query.edit_message_text.await_args.args[0])
        busy = asyncio.Lock()
        asyncio.run(busy.acquire())
        with patch.object(bot, "_production_lock", busy):
            upd = _update(data=f"uret:hkok:{di}:{ei}")
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertEqual(upd.callback_query.edit_message_text.await_args.args[0], bot.BUSY_TEXT)
        for b in (b for m in (kb, bot.hit_kopya_produce_keyboard(di, ei)) for r in m.inline_keyboard for b in r):
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
        with patch.object(bot, "APPROACH_MENU", True):
            rows = [[b.text for b in r] for r in bot.hit_confirm_keyboard(di, ei).inline_keyboard]
        self.assertEqual(rows[-1], ["⭐ Hit kalıbı", "⭐ Hit kalıbı · Yaklaşma", "⭐ Hit kopyası"])

    def test_only_fire_tornado(self):
        for e in es.EVENT_SKELETONS:
            self.assertEqual(hp.hit_kopya_is_active(e), e == FT, e)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_build_scene(DOMAIN, es.WILDFIRE)


class TestOthersUntouched(_Quiet):
    """Diğer 19 olay (normal yol), 13 mod ve 🌀 Kasırga: 40 tohum prompt / hikâye / stil eki / combo / eksenler birebir
    (önceki kod 20124a8)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.snap = others_snapshot()

    def test_other_prompts_verbatim_40_seeds(self):
        self.assertEqual(len(self.snap["events"]), 19)
        self.assertEqual(len(self.snap["modes"]), 14)
        for name, runs in self.snap["modes"].items():
            for s, r in runs.items():
                self.assertNotIn("error", r, (name, s))
        self.assertEqual(snapshot_hash(self.snap), OTHERS_SHA256)

    def test_locked_events_hash_file(self):
        import locked_prompts as lp
        self.assertEqual(lp.hashes(), lp.load())


if __name__ == "__main__":
    unittest.main()
