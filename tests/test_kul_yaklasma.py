# 12 Kas 2026 (6), Bahadır: kül bulutu "⭐ Hit kalıbı · Yaklaşma" modu (core/hit_prompts.py YAKLASMA_KUL_BULUTU).
# Kül bulutu hit'i (13 Eki 11:23, P2+Q1) + ateş hortumu Yaklaşma / dev dalga 24 Eylül yapısı. GPT yok, zaman etiketleri
# var. Kül bulutunun normal yolu, kayıtlı hit prompt'u ve diğer bütün olay/modlar değişmez. Ağ yok.
import asyncio
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
import core.skeleton_pipeline as sk   # noqa: E402
import prompt_snapshot as ps   # noqa: E402
from core.trace_format import format_final_prompt, format_generation, sections_to_text   # noqa: E402

PY = es.PYROCLASTIC
KB = hp.YAKLASMA_KUL_BULUTU
DOMAIN = "volcano_disasters"
FOLLOW = "the camera stays on the terrace and tilts down slowly to follow the cloud, never descending"
FIXED = "the camera stays fixed on the terrace, never descending"
ACTION = "Ash rains down from the very first frame."
K2_TEXT = "hurls it, in one piece, against a house wall"


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
    for m in (hp._KUL_GEO_MEMORY, hp._KUL_VEHICLE_MEMORY, hp._DZ_GEO_MEMORY, hp._GEO_MEMORY):
        m.clear()


def gen(**extra) -> dict:
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": PY, "kul_yaklasma": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.KUL_MODE_LABEL, "⭐ Hit kalıbı · Yaklaşma (kül bulutu)")
        self.assertIs(hp.KUL_YAKLASMA_KAMERA_TAKIP, True)
        self.assertEqual(sorted(KB["geos"]), ["V1", "V2", "V3", "V4", "V5", "V6"])
        self.assertEqual(hp.kul_opening("V1"),
                         "A broad grey volcano rises above the far end of the street in a village of stone houses with "
                         "terracotta roofs and erupts violently, a massive explosion column bursting from its summit as a "
                         "pyroclastic cloud races down its flank into the street, rolling toward the camera.")
        self.assertEqual(hp.kul_people(3), "Three people run up the street below, away from the cloud.")
        self.assertEqual(hp.kul_people(4), "Four people run up the street below, away from the cloud.")
        self.assertEqual(KB["action"], ACTION)
        self.assertEqual(KB["vehicles"], ("parked car", "pickup truck", "small bus"))
        self.assertEqual(sorted(KB["mids"]), ["K1", "K2", "K5"])
        self.assertEqual(sorted(KB["finals"]), ["L1", "L2", "L4"])
        self.assertEqual(hp.kul_camera_text(True), FOLLOW)
        self.assertEqual(hp.kul_camera_text(False), FIXED)
        for f in (True, False):
            t = hp.kul_tail(f)
            self.assertIn("the whole erupting volcano visible in the upper part of the frame", t)
            self.assertIn("high vantage looking down the street, the whole erupting volcano visible", t)
            self.assertIn("grey pyroclastic cloud growing larger as it approaches", t)
            self.assertNotIn("toward the erupting volcano", t)
            self.assertNotIn("in the frame as it approaches", t)
            self.assertIn("a corner of the terrace railing in the foreground", t)

    def test_strong_eruption_opening_13kas(self):
        """13 Kas: güçlü patlama açılışı; "towering" bu modun hiçbir prompt'unda yok; eski metinler _V1 pasif."""
        for g in KB["geos"]:
            o = hp.kul_opening(g)
            self.assertIn("erupts violently", o)
            self.assertIn("a massive explosion column bursting from its summit", o)
        for g in KB["geos"]:
            for m in KB["mids"]:
                for f in KB["finals"]:
                    for follow in (True, False):
                        self.assertNotIn("towering", hp.kul_prompt(g, 3, m, "parked car", f, follow), (g, m, f))
        self.assertIn("erupts, sending a towering pyroclastic cloud", hp.KUL_OPENING_V1)
        self.assertIn("toward the erupting volcano, the whole volcano visible", hp.KUL_TAIL_V1)
        self.assertNotEqual(KB["opening"], hp.KUL_OPENING_V1)
        self.assertEqual(KB["geos"]["V5"]["volcano"], "A tall cone volcano")
        self.assertEqual(hp.KUL_PASIF["mids"]["K3"], "Halfway down the street, the blast of the cloud shatters every "
                                                     "window and tears the shutters off the houses.")
        self.assertEqual(hp.KUL_V5_VOLCANO_V1, "A towering cone volcano")
        self.assertIn("every window along the street", hp.KUL_K3_V1)

    def test_vehicle_fill(self):
        for v in KB["vehicles"]:
            self.assertEqual(hp.kul_mid("K2", v), f"Halfway down the street, the cloud swallows a {v} and hurls it, in "
                                                  "one piece, against a house wall.")
            self.assertEqual(hp.kul_mid("K5", v), f"Halfway down the street, the blast of the cloud slams a {v} "
                                                  "sideways into a shopfront, glass exploding around it.")
            self.assertNotIn("{", hp.kul_mid("K5", v))
            for m in ("K1",):
                text = hp.kul_mid(m, v)
                self.assertNotIn(v, text)
                for w in ("car", "truck", "bus", "vehicle", "{"):
                    self.assertNotIn(w, text)
        with self.assertRaises(es.StructureError):
            hp.kul_mid("K2", None)
        with self.assertRaises(es.StructureError):
            hp.kul_mid("K5", None)
        self.assertEqual(KB["vehicle_mids"], ("K2", "K5"))

    def test_weak_options_passive_13kas(self):
        """13 Kas (2): K3, K4, L3 pasif (KUL_PASIF'te, silinmedi); bu modda hiç seçilmez; LRU son 1."""
        self.assertEqual(sorted(hp.KUL_PASIF["mids"]), ["K3", "K4"])
        self.assertEqual(sorted(hp.KUL_PASIF["finals"]), ["L3"])
        self.assertIn("trying to reverse away and buries it in grey ash", hp.KUL_PASIF["mids"]["K4"])
        self.assertIn("rips apart the garden wall and fence", hp.KUL_PASIF["finals"]["L3"])
        for m in ("K3", "K4"):
            self.assertNotIn(m, KB["mids"])
            with self.assertRaises(es.StructureError):
                hp.kul_mid(m, "parked car")
        self.assertNotIn("L3", KB["finals"])
        self.assertEqual((hp.KUL_MID_BLOCK, hp.KUL_FINAL_BLOCK), (1, 1))
        passive = [hp.KUL_PASIF["mids"]["K3"], hp.KUL_PASIF["mids"]["K4"].split("{vehicle}")[1],
                   hp.KUL_PASIF["finals"]["L3"]]
        for seed in range(1, 31):
            reset()
            random.seed(seed)
            for _ in range(4):
                kb = gen()["structure"]["kul_yaklasma"]
                self.assertIn(kb["mid"], ("K1", "K2", "K5"))
                self.assertIn(kb["final"], ("L1", "L2", "L4"))
                for t in passive:
                    self.assertNotIn(t, kb["prompt"])

    def test_all_combos_within_limits(self):
        """Coğrafya × kişi × araç × orta × final × kamera: hepsi ≤ 230 kelime ve ≤ 1400 karakter."""
        n, over = 0, []
        for g in KB["geos"]:
            for ppl in (3, 4):
                for v in KB["vehicles"]:
                    for m in KB["mids"]:
                        for f in KB["finals"]:
                            for follow in (True, False):
                                p = hp.kul_prompt(g, ppl, m, v, f, follow)
                                n += 1
                                if len(p.split()) > hp.KUL_MAX_WORDS or len(p) > hp.KUL_MAX_CHARS:
                                    over.append((g, ppl, v, m, f, follow, len(p.split()), len(p)))
        self.assertEqual(n, 648)
        self.assertEqual(over, [])

    def test_sentences_only_in_this_mode(self):
        marks = [K2_TEXT, "trying to reverse away and buries it in grey ash", "Ash rains down from the very first frame",
                 "darkness racing up toward the camera", "tilts down slowly to follow the cloud",
                 "rolling toward the camera", "the whole erupting volcano visible in the upper part of the frame",
                 "a massive explosion column bursting from its summit"]
        pools = json.dumps({e: {s: {k: v["text"] for k, v in b[s].items()} for s in ("slice_2", "slice_3")}
                            for e, b in es.EVENT_BEATS.items()})
        others = (pools + json.dumps(hp.HIT_PROMPTS) + json.dumps(hp.YAKLASMA_ATES_HORTUMU, default=str)
                  + json.dumps(hp.DALGA_24EYLUL, default=str))
        for ev in ps.active_events():
            for seed in range(1, 6):
                others += json.dumps(ps.snapshot_event(ev, seed))
        for m in marks:
            self.assertNotIn(m, others, m)

    def test_recorded_hit_prompt_unchanged(self):
        h = hp.HIT_PROMPTS[PY]
        self.assertEqual(h["source"], "13 Eki 2026 11:23")
        self.assertIn("##P2+Q1|", h["combo_key"])
        self.assertTrue(h["prompt"].startswith("0-4s: A pyroclastic cloud races down the volcano’s flank and slams "
                                               "into a village street."))
        # 8d9c264'te kaydedilen metnin sha256'sı (birebir aynı kalmalı)
        import hashlib
        self.assertEqual(hashlib.sha256(h["prompt"].encode()).hexdigest(),
                         "6d9d3f1c332bfc47560c064245126253e038356537bfa475d4d2a0a2f5affdea")
        self.assertNotIn(PY, hp.HIT_ACTIVE_EVENTS)   # eski kül bulutu hit butonu gizli kalır


class TestKulMode(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        kb = st["kul_yaklasma"]
        prompt = sc["prompt"]
        g = KB["geos"][kb["geo"]]
        self.assertIn(g["volcano"], prompt)
        self.assertIn(g["place"], prompt)
        opening = prompt.split(" 4-9s: ")[0]
        self.assertTrue(prompt.startswith(f"0-4s: {hp.kul_opening(kb['geo'])} "))
        self.assertIn("erupts violently", opening)
        self.assertIn("a massive explosion column bursting from its summit", opening)
        self.assertNotIn("towering", prompt)
        self.assertIn("rolling toward the camera", opening)
        self.assertIn(f" {hp.kul_people(kb['people'])} {ACTION} 4-9s: ", prompt)
        self.assertIn(kb["vehicle"], KB["vehicles"])
        self.assertIn(f"4-9s: {hp.kul_mid(kb['mid'], kb['vehicle'])} 9-15s: {KB['finals'][kb['final']]} ", prompt)
        for lab in ("0-4s: ", " 4-9s: ", " 9-15s: "):
            self.assertIn(lab, prompt)
        self.assertNotIn("Full action", prompt)
        self.assertNotIn("Until the last frame", prompt)
        self.assertIn("the whole erupting volcano visible in the upper part of the frame", prompt)
        self.assertIn("a corner of the terrace railing in the foreground", prompt)
        self.assertTrue(prompt.endswith(" " + hp.kul_tail(kb["follow"])))
        self.assertEqual(sc["style_suffix"], hp.kul_tail(kb["follow"]))
        pos = [prompt.find(x) for x in ("0-4s: ", ACTION, " 4-9s: ", " 9-15s: ", " Handheld footage")]
        self.assertNotIn(-1, pos)
        self.assertEqual(pos, sorted(pos))
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        self.assertIn(f"#{kb['mid']}+{kb['final']}|", d["combo_key"])
        for slot in ("slice_2", "slice_3"):   # normal havuz (P*/Q*) metni yok
            for bid in es.EVENT_BEATS[PY][slot]:
                self.assertNotIn(es.beat_text(PY, slot, bid)[4:], prompt)
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        self.assertEqual("⚠️ Araç savurma ortası (K2)" in kb["lines"], kb["mid"] == "K2")
        return kb

    def test_50_seeds_each_geo_sees_every_mid_and_final(self):
        seen = {g: {"mid": set(), "final": set()} for g in KB["geos"]}
        for seed in range(1, 51):
            reset()
            random.seed(seed)
            for i in range(4):
                with self.subTest(seed=seed, i=i):
                    kb = self._check(gen())
                    if i == 0:
                        self.assertNotEqual(kb["geo"], "V1")   # ilk üretimde V1 yok
                    seen[kb["geo"]]["mid"].add(kb["mid"])
                    seen[kb["geo"]]["final"].add(kb["final"])
                    self.assertIn(f"slight hand shake, {FOLLOW}; one continuous shot", build_prompt_of(kb))
        for g, s in seen.items():
            self.assertEqual(s["mid"], set(KB["mids"]), g)
            self.assertEqual(s["final"], set(KB["finals"]), g)
        self.assertIsNone(es.HIT_OVERRIDE.get())

    def test_consecutive_lru(self):
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(8)]
            for key, block in (("geo", 3), ("vehicle", 2), ("mid", 1), ("final", 1)):
                vals = [r[key] for r in runs]
                for i in range(len(vals)):
                    self.assertNotIn(vals[i], vals[max(0, i - block):i], (seed, key, vals))
            self.assertNotEqual(runs[0]["geo"], "V1")
            self.assertEqual({r["people"] for r in runs} <= {3, 4}, True)

    def test_history_sources(self):
        def combo(tag):
            return f"{DOMAIN}|none|{PY.lower()}|rooftop terrace facing the erupting volcano##{tag}|bystander_handheld"
        reset()
        hist = [combo("K1+L1"), combo("P2+Q1"), combo("K5+L4")]
        for s in range(30):
            self.assertIn(hp.kul_choose_mid(hist, random.Random(s)), ("K1", "K2"))
            self.assertIn(hp.kul_choose_final(hist, random.Random(s)), ("L1", "L2"))
        recs = [{"eksenler": json.dumps({"event": PY, "axes": {"mod": "kul_yaklasma", "cografya": g, "arac": v}})}
                for g, v in (("V2", "small bus"), ("V3", "parked car"), ("V4", "small bus"))] + [{"eksenler": "x"}]
        self.assertEqual(hp.kul_axes_history(recs, "cografya"), ["V2", "V3", "V4"])
        self.assertEqual(hp.kul_axes_history(recs, "arac"), ["small bus", "parked car", "small bus"])
        self.assertIsNone(hp.kul_axes_history(None, "arac"))
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: recs)
            kb = d["structure"]["kul_yaklasma"]
            self.assertIn(kb["geo"], ("V1", "V5", "V6"))
            self.assertEqual(kb["vehicle"], "pickup truck")
            axes = json.loads(d["axes_json"])["axes"]
            self.assertEqual((axes["mod"], axes["cografya"], axes["arac"]), ("kul_yaklasma", kb["geo"], kb["vehicle"]))

    def test_camera_fixed(self):
        with patch.object(hp, "KUL_YAKLASMA_KAMERA_TAKIP", False):
            for seed in range(1, 11):
                d = build(seed)
                self._check(d)
                p = d["scenes"][0]["prompt"]
                self.assertIn(f"slight hand shake, {FIXED}; one continuous shot", p)
                self.assertNotIn(FOLLOW, p)
                self.assertIn("Kamera: sabit", d["structure"]["kul_yaklasma"]["lines"])

    def test_no_gpt_rewrite_tampering(self):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")):
            d = build(7)
        gpt.assert_not_called()
        sc, st = d["scenes"][0], d["structure"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"].replace(
            "No readable signs", f"{sk.FULL_MOTION} No readable signs")}))
        for bad in ({"geo": "V9"}, {"mid": "P2"}, {"final": "Q1"}, {"people": 6}):
            self.assertTrue(cp.submit_issues({**st, "kul_yaklasma": {**st["kul_yaklasma"], **bad}}, info), bad)
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])

    def test_approval_lines_and_display(self):
        for seed in range(1, 60):
            d = build(seed)
            if d["structure"]["kul_yaklasma"]["mid"] == "K2":
                break
        sc, st = d["scenes"][0], d["structure"]
        kb = st["kul_yaklasma"]
        self.assertEqual(kb["mid"], "K2")
        lines = kb["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kalıbı · Yaklaşma (kül bulutu)")
        self.assertEqual(lines[1], f"Coğrafya: {kb['geo']} {KB['geos'][kb['geo']]['name']}")
        self.assertEqual(lines[2], f"Araç: {kb['vehicle']}")
        self.assertTrue(lines[3].startswith("Orta (4-9s): K2 «Halfway down the street, the cloud swallows a "))
        self.assertTrue(lines[4].startswith(f"Final (9-15s): {kb['final']} «Right below the terrace"))
        self.assertEqual(lines[5], "Kamera: takip (terasta kalır, bulutu izlemek için yavaşça aşağı eğilir)")
        self.assertEqual(lines[6], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                   f"{len(sc['prompt'])} (en fazla 1400)")
        self.assertEqual(lines[7], "⚠️ Araç savurma ortası (K2): videoda aracın tek parça kalıp kalmadığını kontrol et.")
        # Onay görüntüsü: 1. Seçim / 3. Hikâye / Eksenler gerçek parçalar
        shown = sections_to_text(format_generation(d["trace"])) + "\n" + st["axes_line"]
        sel, _, rest = shown.partition("🔍 2.")
        story = rest.split("🔍 3. Hikâye\n", 1)[1]
        for part in (hp.kul_opening(kb["geo"]), hp.kul_mid("K2", kb["vehicle"]), KB["finals"][kb["final"]]):
            self.assertIn(part, sc["prompt"])
            self.assertIn(part, sel)
            self.assertIn(part, story)
        self.assertIn(hp.kul_camera_text(True), sel)
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (kül bulutu)", sel)
        self.assertIn(f"kamera modu=takip", st["axes_line"])
        self.assertIn(f"araç={kb['vehicle']}", st["axes_line"])
        for absent in (st["spec"]["key_visual"], "kamera modu=A", "kamera modu=B", "dağ eteği köyü"):
            self.assertNotIn(absent, shown)
        _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"],
                                       "hit_lines": kb["lines"], "environment": st["environment"]})
        self.assertIn("\nMod: ⭐ Hit kalıbı · Yaklaşma (kül bulutu)\n", body)
        self.assertIn("\n\n" + sc["prompt"], body)

    def test_normal_pyroclastic_untouched(self):
        reset()
        random.seed(5)
        d = asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": PY, "used_combos": [],
                                                     "recent_topics": []}))
        self.assertNotIn("kul_yaklasma", d["structure"])
        self.assertNotIn("mode_label", d["trace"])
        for x in (ACTION, "rolling toward the camera", "Right below the terrace"):
            self.assertNotIn(x, d["scenes"][0]["prompt"])


def build_prompt_of(kb: dict) -> str:
    return hp.kul_prompt(kb["geo"], kb["people"], kb["mid"], kb["vehicle"], kb["final"], kb["follow"])


class TestKulPipelineAndBot(_Quiet):
    def test_pipeline_passes_flag_and_sends_prompt(self):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        seen = {}

        async def fake_gen(config):
            seen["config"] = dict(config)
            reset()
            random.seed(21)
            cfg = {k: v for k, v in config.items() if k not in ("axes_loader", "caption_loader")}
            return await pg.generate_creative_prompts({**cfg, "domain": DOMAIN})
        t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
        t.setUp()
        try:
            rep = _Reporter(approve=True, needs_approval=True)
            orig = main.run_pipeline

            async def run_with(**kw):
                return await orig(**kw, kul_yaklasma=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=PY)
        finally:
            t.doCleanups()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["kul_yaklasma"], True)
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı · Yaklaşma (kül bulutu)\nCoğrafya: V"))
        self.assertEqual(t.create.await_args.args[1], info["prompt"])   # Kie'ye giden = onaydaki

    def test_bot_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ei = str(bot.domain_events(DOMAIN).index(PY))
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        labels = [b.text for r in kb.inline_keyboard for b in r]
        self.assertEqual(labels, ["✅ Üret", "❌ İptal", "⭐ Hit kalıbı · Yaklaşma"])
        self.assertNotIn("⭐ Hit kalıbı", labels)   # eski kül bulutu hit butonu gizli
        upd = _update(data=f"uret:ky:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (kül bulutu)",
                      upd.callback_query.edit_message_text.await_args.args[0])
        upd = _update(data=f"uret:kyok:{di}:{ei}")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["event"], kw["kul_yaklasma"]), (PY, True))
        self.assertTrue(kw["reporter"].needs_approval)
        # diğer volkan olaylarında buton yok
        for i, e in enumerate(bot.domain_events(DOMAIN)):
            if e == PY:
                continue
            upd = _update(data=f"uret:e:{di}:{i}")
            asyncio.run(bot.on_callback(upd, ctx))
            kw = upd.callback_query.edit_message_text.await_args.kwargs
            if "reply_markup" in kw:
                self.assertNotIn("⭐ Hit kalıbı · Yaklaşma", [b.text for r in kw["reply_markup"].inline_keyboard
                                                             for b in r], e)
        self.assertIsNone(bot.parse_kul(di, str(next(i for i, e in enumerate(bot.domain_events(DOMAIN)) if e != PY))))


if __name__ == "__main__":
    unittest.main()
