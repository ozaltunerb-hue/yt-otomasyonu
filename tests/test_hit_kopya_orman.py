# 20 Kas 2026, Bahadır: orman yangını "⭐ Hit kopyası" modu (core/hit_prompts.py HIT_KOPYA_ORMAN).
# Sebep: orman Yaklaşma v4-v7 testlerinin hiçbiri paylaşılabilir çıkmadı. Kaynak: 9 Eki 2026 21:52 üretimi (19 Eki
# paylaşımı, 3,02M), Kie prompt'u HIT_PROMPTS[es.WILDFIRE]["prompt"] (Notion 3f4d048d-625e-81f9-a10f-eaf888802f52).
# Ateş hortumu Hit kopyasıyla (test_hit_kopya_ates) birebir aynı düzen. Hit'in Kie prompt'u kelimesi kelimesine; sadece
# "the edge of the neighborhood" → "the edge of {place}" ve "The white van" → "The {vehicle}". GPT yok. Orman Yaklaşma
# v7 kodda ve menüde aynen kalır. Diğer 19 olay ve tüm modlar birebir aynı (40 tohum). Ağ yok.
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

WF = es.WILDFIRE
FT = es.FIRE_TORNADO
DOMAIN = "fire_disasters"
HKO = hp.HIT_KOPYA_ORMAN
# 9 Eki 21:52 üretiminin (19 Eki paylaşımı, 3,02M) Kie prompt'u, birebir (Notion üretim kaydı "Prompt" alanı)
HIT_PROMPT = (
    "0-4s: A towering wall of flames sweeps down the forested slope and slams into the edge of the "
    "neighborhood, igniting roofs and trees. Five people run desperately, scattering in various directions to "
    "escape the rapidly encroaching inferno. 4-9s: The white van accelerates, executing a sharp U-turn and "
    "leaves the scene, just as the flames close in behind. 9-15s: The advancing fire consumes an entire line "
    "of trees, their tops exploding into fiery embers, rising into the swirling sky. Handheld footage shot by "
    "a person standing on a balcony of a hillside house overlooking the street and the burning slope, eye "
    "level, normal lens; slight hand shake, the camera pans to follow the wall of flames; no zoom, no cuts. "
    "Bystanders wear civilian clothes, never hi-vis PPE on civilians; emergency responders wear service "
    "uniforms. Raw natural light matching the weather, never glossy or CGI; no white hazmat suits. No "
    "readable signs, text or flags.")
PLACES = {"G1": ("Kaliforniya", "a Californian hillside suburb"), "G2": ("Avustralya", "an Australian bush town"),
          "G3": ("Yunanistan", "a Greek hillside village"), "G4": ("Kanada", "a Canadian mountain town"),
          "G5": ("Portekiz", "a Portuguese hillside village"), "G6": ("Şili", "a Chilean hillside town")}
VEHICLES = ("white van", "pickup truck", "SUV")
TAIL = HIT_PROMPT[HIT_PROMPT.index("Handheld footage shot by a person standing on a balcony"):]
REQUIRED = ("sweeps down the forested slope and slams into the edge of", "rapidly encroaching inferno", "sharp U-turn",
            "the camera pans to follow the wall of flames", "never glossy or CGI")
FORBIDDEN = ("Full action", "Until the last frame", "big in frame", "From the very first frame",
             "never along the asphalt")
SOURCE = "Kaynak: 9 Eki 21:52 üretimi (19 Eki paylaşımı, 3M), birebir"
WARNING = ("⚠️ Hit karşılaştırması: alev duvarı ilk saniyelerde yamaçtan inip mahalleye çarpıyor mu, video 19 Eki "
           "hit'iyle boy ölçüşür mü?")
CONFIRM_DESC = ("9 Eki 21:52 üretiminin (19 Eki paylaşımı, 3M) Kie prompt'u kelimesi kelimesine; sadece coğrafya (G1-G6) "
                "ve araç değişir. Alev duvarı ormanlık yamaçtan inip mahalleye çarpar, insanlar kaçar, araç U dönüşü "
                "yapıp kaçar, ağaç sırası tepeden kıvılcım saçarak yanar. Yamaç evinin balkonu, kamera alevleri takip "
                "eder. Hikâye için GPT çağrılmaz.")
# Değişiklikten önceki kod (14063ac): test_yer_yarilmasi kaydı (19 olay + modlar, orman v3 fixture'ı) + 🌍 Yer
# yarılması, 40 tohum. Canlı orman Yaklaşma v7 ayrıca ORMAN_SHA256 ile.
OTHERS_SHA256 = "d719e05d8370ca2d526710ba8814f6860a6d320ffdd3076908fcd36ad76c49f2"
ORMAN_SHA256 = "b3ecda2ac3cb673b68ffb22c1024d978057d64419e993b720e825684c0541fc5"   # orman Yaklaşma v7 (değişmez)
# ⭐ Hit kopyası (orman yangını) kendi 40 tohum kilidi (prompt / hikâye / stil eki / combo / eksenler; caption hariç)
HIT_KOPYA_ORMAN_SHA256 = "f0e9e1576c0142bf102813c3f8e1bccfe0104c71defb61242a3170397d5e4d35"


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
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": WF, "hit_kopya_orman": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def expected(g: str, v: str) -> str:
    """Hit prompt'unun kendisinden: "the edge of the neighborhood" → yer, "The white van" → araç."""
    return HIT_PROMPT.replace("the edge of the neighborhood,", f"the edge of {PLACES[g][1]},", 1) \
                     .replace("The white van accelerates", f"The {v} accelerates", 1)


def snapshot_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def others_snapshot() -> dict:
    """test_yer_yarilmasi kaydı (19 olay + modlar + ⭐ Hit kopyası (ateş hortumu)) + 🌍 Yer yarılması; 40 tohum."""
    import test_yer_yarilmasi as ty
    snap = ty.others_snapshot()
    snap["modes"]["yer_yarilmasi"] = ty.yy_snapshot()
    return snap


def hko_snapshot() -> dict:
    """⭐ Hit kopyası (orman yangını) 40 tohum: prompt, hikâye, stil eki, combo, eksenler (caption hariç)."""
    runs = {}
    for s in range(1, 41):
        reset()
        random.seed(s)
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
            d = gen()
        sc = d["scenes"][0]
        axes = json.loads(d["axes_json"])
        axes.pop("caption", None)
        runs[str(s)] = {"prompt": sc["prompt"], "story": sc["story"], "suffix": sc["style_suffix"],
                        "combo": d["combo_key"], "axes": axes}
    return runs


class TestTemplate(_Quiet):
    def test_template_is_hit_prompt_verbatim(self):
        """Şablon = hit prompt'u; yalnız "the edge of {place}" ve "The {vehicle}". {place}="the neighborhood",
        {vehicle}="white van" verilince hit prompt'u karakter karakter geri gelir."""
        self.assertEqual(hp.HIT_PROMPTS[WF]["prompt"], HIT_PROMPT)
        self.assertEqual(hp.HIT_PROMPTS[WF]["notion"], "3f4d048d-625e-81f9-a10f-eaf888802f52")
        t = HKO["template"]
        self.assertEqual(t.count("{place}"), 1)
        self.assertEqual(t.count("{vehicle}"), 1)
        self.assertIn("slams into the edge of {place}, igniting roofs", t)
        self.assertIn("4-9s: The {vehicle} accelerates", t)
        self.assertEqual(t.format(place="the neighborhood", vehicle="white van"), HIT_PROMPT)
        self.assertEqual(t.replace("the edge of {place}", "the edge of the neighborhood", 1)
                         .replace("The {vehicle}", "The white van", 1), HIT_PROMPT)
        self.assertEqual(HKO["tail_start"], "Handheld footage shot by a person standing on a balcony")
        self.assertEqual(hp.hit_kopya_orman_tail(), TAIL)
        self.assertEqual(hp.hit_kopya_orman_story("G1", "white van")
                         .replace(PLACES["G1"][1], "the neighborhood") + " " + TAIL, HIT_PROMPT)

    def test_constants(self):
        self.assertEqual(hp.HIT_KOPYA_ORMAN_MODE_LABEL, "⭐ Hit kopyası (orman yangını)")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_EVENTS, (WF,))
        self.assertEqual(hp.HIT_KOPYA_ORMAN_DOMAIN, DOMAIN)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_MOD, "hit_kopya_orman")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_SOURCE, SOURCE)
        self.assertEqual((hp.HIT_KOPYA_ORMAN_MAX_WORDS, hp.HIT_KOPYA_ORMAN_MAX_CHARS), (230, 1400))
        self.assertEqual((hp.HIT_KOPYA_ORMAN_GEO_BLOCK, hp.HIT_KOPYA_ORMAN_GEO_SEED, hp.HIT_KOPYA_ORMAN_VEHICLE_BLOCK),
                         (3, ("G4",), 2))
        self.assertEqual({g: (v["name"], v["place"]) for g, v in HKO["geos"].items()}, PLACES)
        self.assertEqual(HKO["vehicles"], VEHICLES)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_REQUIRED, REQUIRED)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_FORBIDDEN, FORBIDDEN)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_WARNING, WARNING)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_CONFIRM_DESC, CONFIRM_DESC)
        self.assertNotIn("—", CONFIRM_DESC + WARNING + SOURCE)

    def test_all_18_combos_within_limits(self):
        words, chars = [], []
        for g in PLACES:
            for v in VEHICLES:
                p = hp.hit_kopya_orman_prompt(g, v)
                self.assertEqual(p, expected(g, v), (g, v))
                self.assertEqual(p, hp.hit_kopya_orman_story(g, v) + " " + TAIL)
                words.append(len(p.split()))
                chars.append((len(p), g, v))
                self.assertLessEqual(len(p.split()), 230)
                self.assertLessEqual(len(p), 1400)
                self.assertEqual(hp.hit_kopya_orman_camera_issues(p, g), [])
        self.assertEqual(len(words), 18)
        self.assertEqual((min(words), max(words)), (154, 155))
        self.assertEqual(min(chars), (941, "G2", "SUV"))
        self.assertEqual(max(chars), (956, "G5", "pickup truck"))

    def test_bad_ids(self):
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_orman_prompt("G7", "SUV")
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_orman_prompt("G1", "delivery van")

    def test_event_gate_without_synonym(self):
        """Ana hattın olay denetimi bu modda da geçer; eş anlamlı eklenmedi."""
        for g in PLACES:
            for v in VEHICLES:
                self.assertEqual(pg.event_fidelity_issues(WF, hp.hit_kopya_orman_story(g, v)), [], (g, v))
                self.assertEqual(pg.event_fidelity_issues(WF, hp.hit_kopya_orman_prompt(g, v)), [], (g, v))

    def test_ates_hit_kopya_untouched(self):
        """Ateş hortumu Hit kopyası sabitleri ayrı ve aynen."""
        self.assertIsNot(hp.HIT_KOPYA_ATES, HKO)
        self.assertEqual(hp.HIT_KOPYA_MODE_LABEL, "⭐ Hit kopyası (ateş hortumu)")
        self.assertEqual(hp.HIT_KOPYA_MOD, "hit_kopya_ates")
        self.assertEqual(hp.HIT_KOPYA_GEO_SEED, ("G3",))
        self.assertEqual(hp.HIT_KOPYA_EVENTS, (FT,))


class TestScene(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["hit_kopya_orman"]
        prompt = sc["prompt"]
        self.assertIn(tb["geo"], PLACES)
        self.assertIn(tb["vehicle"], VEHICLES)
        self.assertEqual(prompt, expected(tb["geo"], tb["vehicle"]))
        self.assertEqual(sc["style_suffix"], TAIL)
        for need in REQUIRED + (PLACES[tb["geo"]][1],):
            self.assertIn(need, prompt)
        for bad in FORBIDDEN:
            self.assertNotIn(bad.lower(), prompt.lower())
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{WF.lower()}|balcony of a hillside house##HKO:{tb['geo']}"
                                         "|bystander_handheld")
        self.assertIsNone(es.beats_of_combo(d["combo_key"]))   # normal K*/L* ve Yaklaşma M*/N* LRU'su etkilenmez
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        self.assertEqual(pg.event_fidelity_issues(WF, sc["story"]), [])
        self.assertEqual((d["selection"]["domain_id"], d["selection"]["event"]), (DOMAIN, WF))
        for other in ("hit_kopya_ates", "orman_yaklasma", "kasirga", "donma_firtina", "approach", "hit", "spec"):
            self.assertNotIn(other, st)
        return tb

    def test_40_seeds_no_error_and_no_gpt(self):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))) as normal:
            seen = set()
            for seed in range(1, 41):
                tb = self._check(build(seed))
                seen.add((tb["geo"], tb["vehicle"]))
                self.assertNotEqual(tb["geo"], "G4")   # ilk üretim: G4 tohumu
        gpt.assert_not_called()
        normal.assert_not_called()
        self.assertGreater(len(seen), 8)

    def test_lru_and_g4_seed(self):
        geos, vehs = set(), set()
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(12)]
            g = [r["geo"] for r in runs]
            self.assertNotIn("G4", g[:3], (seed, g))   # G4 tohumu: ilk 3 üretimde G4 gelmez
            hist = ["G4"] + g
            for i in range(1, len(hist)):
                self.assertNotIn(hist[i], hist[max(0, i - 3):i], (seed, g))
            v = [r["vehicle"] for r in runs]
            for i in range(len(v)):
                self.assertNotIn(v[i], v[max(0, i - 2):i], (seed, v))
            self.assertEqual(hp._HIT_KOPYA_ORMAN_GEO_MEMORY[-12:], g)
            self.assertEqual(hp._HIT_KOPYA_ORMAN_VEHICLE_MEMORY[-12:], v)
            geos |= set(g)
            vehs |= set(v)
        self.assertEqual(geos, set(PLACES))
        self.assertEqual(vehs, set(VEHICLES))
        self.assertEqual(hp._HIT_KOPYA_GEO_MEMORY, [])   # ateş Hit kopyası hafızası etkilenmez
        self.assertEqual(hp._HIT_KOPYA_VEHICLE_MEMORY, [])

    def test_history_sources(self):
        def rec(g, v, event=WF, mod="hit_kopya_orman"):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, "cografya": g, "arac": v}})}
        recs = [rec("G1", "SUV"), {"eksenler": "x"}, rec("G2", "pickup truck"), rec("G5", "SUV", mod="orman_yaklasma"),
                rec("G6", "white van", event=FT, mod="hit_kopya_ates")]
        self.assertEqual(hp.hit_kopya_orman_axes_history(recs, "cografya"), ["G1", "G2"])
        self.assertEqual(hp.hit_kopya_orman_axes_history(recs, "arac"), ["SUV", "pickup truck"])
        self.assertIsNone(hp.hit_kopya_orman_axes_history(None, "arac"))
        calls = []
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: calls.append(dom) or recs)
            tb = d["structure"]["hit_kopya_orman"]
            self.assertIn(tb["geo"], ("G3", "G5", "G6"))   # son 3 (G4 tohum, G1, G2) elenir
            self.assertEqual(tb["vehicle"], "white van")   # son 2 (SUV, pickup truck) elenir
            axes = json.loads(d["axes_json"])
            self.assertEqual(axes["event"], WF)
            self.assertEqual((axes["axes"]["mod"], axes["axes"]["cografya"], axes["axes"]["arac"]),
                             ("hit_kopya_orman", tb["geo"], tb["vehicle"]))
            self.assertEqual(axes["axes"]["beats"], f"HKO:{tb['geo']}")
            self.assertEqual(axes["excluded"]["cografya"], ["G1", "G2", "G4"])
            self.assertEqual(axes["excluded"]["arac"], ["pickup truck", "SUV"])
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
        geo = st["hit_kopya_orman"]["geo"]
        good = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, good), [])
        for need in REQUIRED:
            bad = sc["prompt"].replace(need, "x")
            self.assertTrue(hp.hit_kopya_orman_camera_issues(bad, geo), need)
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": bad}), need)
        self.assertTrue(hp.hit_kopya_orman_camera_issues(sc["prompt"].replace(PLACES[geo][1], "a town"), geo))
        for bad_phrase in FORBIDDEN:
            bad = sc["prompt"].replace("eye level", f"eye level, {bad_phrase.lower()}")
            self.assertTrue(hp.hit_kopya_orman_camera_issues(bad), bad_phrase)
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": bad}), bad_phrase)
        other = next(g for g in PLACES if g != geo)
        self.assertTrue(hp.hit_kopya_orman_camera_issues(hp.hit_kopya_orman_prompt(other, "SUV"), geo))
        self.assertTrue(cp.submit_issues(st, {**good, "style_suffix": "x"}))
        self.assertTrue(cp.submit_issues(st, {**good, "story": sc["story"] + " x"}))
        long = sc["prompt"] + " word" * 80
        self.assertTrue(any("kelime" in x for x in hp.hit_kopya_orman_issues(st, {**good, "prompt": long})))
        self.assertEqual(asyncio.run(cp.rewrite_structured(st, "ret", AsyncMock(side_effect=AssertionError("GPT")))),
                         sc["story"])

    def test_approval_lines(self):
        reset()
        random.seed(7)
        d = gen()
        tb = d["structure"]["hit_kopya_orman"]
        lines = tb["lines"].split("\n")
        g = tb["geo"]
        self.assertEqual(lines[0], "Mod: ⭐ Hit kopyası (orman yangını)")
        self.assertEqual(lines[1], f"Coğrafya: {g} {PLACES[g][0]} «{PLACES[g][1]}»")
        self.assertEqual(lines[2], f"Araç: {tb['vehicle']}")
        self.assertEqual(lines[3], SOURCE)
        p = tb["prompt"]
        self.assertEqual(lines[4], f"Kelime: {len(p.split())} (en fazla 230) · karakter: {len(p)} (en fazla 1400)")
        self.assertTrue(lines[5].startswith("Eksenler (⭐ Hit kopyası (orman yangını)): coğrafya="))
        self.assertTrue(lines[6].startswith("Tekrar önleme: coğrafya son 3 elendi (G4 tohum) · araç son 2"))
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
                return await orig(**{**kw, "domain": DOMAIN}, hit_kopya_orman=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=WF, poll=poll)
        finally:
            t.doCleanups()
        return r, rep, seen, t

    def test_pipeline_sends_verbatim_prompt_after_approval(self):
        r, rep, seen, t = self._run()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["hit_kopya_orman"], True)
        for other in ("hit_kopya_ates", "orman_yaklasma", "kasirga", "donma_firtina", "approach_env", "hit_env"):
            self.assertNotIn(other, seen["config"])
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kopyası (orman yangını)\nCoğrafya: G"))
        self.assertIn(SOURCE, info["hit_lines"])
        self.assertIn(WARNING, info["hit_lines"])
        self.assertEqual(t.create.await_count, 1)
        self.assertEqual(t.create.await_args.args[1], info["prompt"])
        self.assertTrue(info["prompt"].endswith(TAIL))
        axes = [c.args[0] for c in t.tracker.record_axes.call_args_list]
        self.assertEqual(json.loads(axes[0])["axes"]["mod"], "hit_kopya_orman")

    def test_event_gate_blocks_mismatch(self):
        import main
        with patch.object(main, "event_fidelity_issues", side_effect=lambda e, t, *a: ["uyuşmuyor"]
                          if e == WF else []):
            r, _, _, t = self._run()
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def test_rejected_approval_no_kie(self):
        r, _, _, t = self._run(approve=False)
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def _ids(self, bot, event=WF):
        return str(bot.DOMAIN_KEYS.index(DOMAIN)), str(bot.domain_events(DOMAIN).index(event))

    def test_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di, ei = self._ids(bot)
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        rows = [[b.text for b in r] for r in kb.inline_keyboard]
        self.assertEqual(rows, [["✅ Üret", "❌ İptal"], ["⭐ Hit kalıbı · Yaklaşma", "⭐ Hit kopyası"]])
        cbs = [b.callback_data for r in kb.inline_keyboard for b in r]
        self.assertIn(f"uret:oy:{di}:{ei}", cbs)   # orman Yaklaşma v7 menüde aynen
        self.assertIn(f"uret:hko:{di}:{ei}", cbs)
        self.assertNotIn(f"uret:hk:{di}:{ei}", cbs)
        upd = _update(data=f"uret:hko:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        text = call.args[0]
        for part in ("Mod: ⭐ Hit kopyası (orman yangını)", SOURCE, "✋ Onay", CONFIRM_DESC):
            self.assertIn(part, text)
        self.assertNotIn("—", text)
        self.assertEqual([b.text for r in call.kwargs["reply_markup"].inline_keyboard for b in r], ["✅ Üret", "❌ İptal"])
        upd = _update(data=f"uret:hkook:{di}:{ei}")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["domain"], kw["event"], kw["hit_kopya_orman"]), (DOMAIN, WF, True))
        for other in ("hit_kopya_ates", "kasirga", "donma_firtina", "cadde_yaklasma", "hortum_yaklasma",
                      "heli_yaklasma", "kul_yaklasma", "orman_yaklasma", "dalga24", "approach_env", "hit_env"):
            self.assertNotIn(other, kw)
        self.assertTrue(kw["reporter"].needs_approval)
        started = upd.callback_query.edit_message_text.await_args_list[0].args[0]
        self.assertIn("/ ⭐ Hit kopyası", started)
        _, ft = self._ids(bot, FT)
        for bad in (f"uret:hko:{di}", f"uret:hko:{di}:{ft}", f"uret:hkook:{di}:{ft}", f"uret:hkook:{di}:{ei}:x"):
            upd = _update(data=bad)
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertIn("Geçersiz", upd.callback_query.edit_message_text.await_args.args[0])
        busy = asyncio.Lock()
        asyncio.run(busy.acquire())
        with patch.object(bot, "_production_lock", busy):
            upd = _update(data=f"uret:hkook:{di}:{ei}")
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertEqual(upd.callback_query.edit_message_text.await_args.args[0], bot.BUSY_TEXT)
        for b in (b for m in (kb, bot.hit_kopya_orman_produce_keyboard(di, ei)) for r in m.inline_keyboard for b in r):
            self.assertLessEqual(len(b.callback_data.encode()), 64)

    def test_fire_tornado_buttons_unchanged(self):
        """Ateş hortumu onay ekranı ve Hit kopyası (hk) aynen; orman butonu orada yok."""
        import bot
        from test_tur29_infra import _context, _update
        di, ft = self._ids(bot, FT)
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ft}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual([[b.text for b in r] for r in kb.inline_keyboard],
                         [["✅ Üret", "❌ İptal"], ["⭐ Hit kalıbı", "⭐ Hit kopyası"]])
        cbs = [b.callback_data for r in kb.inline_keyboard for b in r]
        self.assertIn(f"uret:hk:{di}:{ft}", cbs)
        self.assertFalse(any(c.startswith("uret:hko") for c in cbs))
        upd = _update(data=f"uret:hk:{di}:{ft}")
        asyncio.run(bot.on_callback(upd, ctx))
        text = upd.callback_query.edit_message_text.await_args.args[0]
        self.assertIn("Mod: ⭐ Hit kopyası (ateş hortumu)", text)
        self.assertIn(hp.HIT_KOPYA_CONFIRM_DESC, text)
        self.assertNotIn("orman", text.split("Mod:")[1])

    def test_other_fire_events_no_hko_button(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ctx = _context()
        for i, e in enumerate(bot.domain_events(DOMAIN)):
            if e == WF:
                continue
            upd = _update(data=f"uret:e:{di}:{i}")
            asyncio.run(bot.on_callback(upd, ctx))
            kw = upd.callback_query.edit_message_text.await_args.kwargs
            if "reply_markup" in kw:
                cbs = [b.callback_data for r in kw["reply_markup"].inline_keyboard for b in r]
                self.assertFalse(any(c.startswith("uret:hko") for c in cbs), e)

    def test_only_wildfire(self):
        for e in es.EVENT_SKELETONS:
            self.assertEqual(hp.hit_kopya_orman_is_active(e), e == WF, e)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_orman_build_scene(DOMAIN, FT)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_orman_build_scene("city_disasters", WF)


class TestLocks(_Quiet):
    """Diğer 19 olay ve tüm modlar (önceki kod 14063ac) 40 tohum birebir; orman Yaklaşma v7 ORMAN_SHA256 aynen;
    bu modun kendi kilidi HIT_KOPYA_ORMAN_SHA256."""

    def test_others_verbatim_40_seeds(self):
        snap = others_snapshot()
        self.assertEqual(len(snap["events"]), 19)
        for name, runs in snap["modes"].items():
            for s, r in runs.items():
                self.assertNotIn("error", r, (name, s))
        self.assertNotIn("hit_kopya_orman", snap["modes"])
        self.assertEqual(snapshot_hash(snap), OTHERS_SHA256)

    def test_orman_yaklasma_v7_untouched(self):
        import test_orman_yaklasma as to
        self.assertEqual(snapshot_hash(to.orman_snapshot()), ORMAN_SHA256)
        self.assertEqual(to.ORMAN_SHA256, ORMAN_SHA256)

    def test_hit_kopya_orman_lock(self):
        runs = hko_snapshot()
        self.assertEqual(len(runs), 40)
        for s, r in runs.items():
            self.assertTrue(r["combo"].endswith(f"##HKO:{r['axes']['axes']['cografya']}|bystander_handheld"), s)
            self.assertEqual(r["axes"]["axes"]["mod"], "hit_kopya_orman")
        self.assertEqual(snapshot_hash(runs), HIT_KOPYA_ORMAN_SHA256)

    def test_locked_events_hash_file(self):
        import locked_prompts as lp
        self.assertEqual(lp.hashes(), lp.load())


if __name__ == "__main__":
    unittest.main()
