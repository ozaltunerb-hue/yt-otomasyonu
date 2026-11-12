# 12 Kas 2026, Bahadır: ⭐ Hit kalıbı modu (core/hit_prompts.py). Hit videonun gerçek Kie prompt'unun çerçevesi birebir,
# olaylar havuzdan. Sadece ateş hortumu aktif. Normal üretim yolu değişmez (kilit + 40 tohum diff testleri ayrı).
# Ağ yok: GPT, Kie, Notion, Telegram sahte.
import asyncio
import logging
import os
import random
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

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
from core.trace_format import format_final_prompt   # noqa: E402

FT = es.FIRE_TORNADO
TAIL = hp.HIT_TAIL[FT]
FULL = sk.FULL_MOTION
CONT = es.CONTINUATION_LINES[FT]
HIT_PROMPT = hp.HIT_PROMPTS[FT]["prompt"]


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


def hit_build(env: str, seed: int, history=None) -> dict:
    """generate_creative_prompts hit yolu (Telegram'daki ile aynı config anahtarı)."""
    ps.reset_memory()
    random.seed(seed)
    return asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": FT, "hit_env": env,
                                                     "used_combos": list(history or []), "recent_topics": []}))


class TestHitPrompts(_Quiet):
    def test_three_hit_prompts_recorded(self):
        self.assertEqual(set(hp.HIT_PROMPTS), {FT, es.PYROCLASTIC, es.WILDFIRE})
        self.assertEqual(hp.HIT_PROMPTS[FT]["source"], "5 Kas 2026 00:13")
        self.assertEqual(hp.HIT_PROMPTS[es.PYROCLASTIC]["source"], "13 Eki 2026 11:23")
        self.assertEqual(hp.HIT_PROMPTS[es.WILDFIRE]["source"], "9 Eki 2026 21:52")
        self.assertIn("##T4+U11|", hp.HIT_PROMPTS[FT]["combo_key"])
        self.assertIn("##P2+Q1|", hp.HIT_PROMPTS[es.PYROCLASTIC]["combo_key"])
        self.assertIn("##K5+L4|", hp.HIT_PROMPTS[es.WILDFIRE]["combo_key"])
        for e, h in hp.HIT_PROMPTS.items():
            self.assertTrue(h["prompt"].startswith("0-4s: ") and h["prompt"].endswith("No readable signs, text or flags."))
        # Notion'daki tam metin (1026 karakter, 175 kelime)
        self.assertEqual((len(HIT_PROMPT), len(HIT_PROMPT.split())), (1026, 175))

    def test_only_fire_tornado_active(self):
        self.assertEqual(hp.HIT_ACTIVE_EVENTS, (FT,))
        self.assertFalse(hp.is_active(es.PYROCLASTIC))
        self.assertFalse(hp.is_active(es.WILDFIRE))
        self.assertEqual(hp.envs(FT), ("forest_edge", "tree_street", "village_woods"))

    def test_template_rebuilds_hit_exactly(self):
        """Kalıp parçaları hit ile birebir: hit'in kendi seçimleri (forest_edge, T4+U11, pickup, hit insan cümlesi)
        kalıba konunca Notion'daki prompt bayt bayt çıkar."""
        p = hp.HIT_PROMPTS[FT]["parts"]
        spec = {"key_visual": es.FIRE_TOR_ENVS[p["env"]]["key"]}
        s2 = es.beat_text(FT, "slice_2", p["beat_2"], p["vehicle"])
        s3 = es.beat_text(FT, "slice_3", p["beat_3"], p["vehicle"])
        slices = {"slice_1_rest": p["people"], "slice_2": s2[0].upper() + s2[1:] + ".",
                  "slice_3": s3[0].upper() + s3[1:] + "."}
        self.assertEqual(hp.build_prompt(FT, hp.build_story(spec, slices)), HIT_PROMPT)
        self.assertEqual(HIT_PROMPT.count(TAIL), 1)
        self.assertTrue(TAIL.startswith("Handheld footage filmed on a rooftop terrace above a wooded residential area, "
                                        "high vantage, the tornado filling half the frame, top never cut off,"))
        self.assertNotIn(FULL, HIT_PROMPT)
        self.assertNotIn(CONT, HIT_PROMPT)


class TestHitMode(_Quiet):
    def test_40_seeds_each_env(self):
        allowed_mid = set(es.EVENT_BEATS[FT]["slice_2"])
        allowed_fin = set(es.EVENT_BEATS[FT]["slice_3"])
        off = es.disabled_beats(FT)
        for env in hp.envs(FT):
            spots = es.FIRE_TOR_ENVS[env]["spots"]
            for seed in range(1, 41):
                d = hit_build(env, seed)
                sc, st = d["scenes"][0], d["structure"]
                spec, hit = st["spec"], st["hit"]
                prompt = sc["prompt"]
                with self.subTest(env=env, seed=seed):
                    self.assertEqual(spec["fire_env"], env)
                    self.assertIn(spec["spot"], spots)
                    self.assertNotEqual((spec["beat_2"], spec["beat_3"]), ("T4", "U11"))
                    self.assertIn(spec["beat_2"], allowed_mid)
                    self.assertIn(spec["beat_3"], allowed_fin)
                    self.assertNotIn(spec["beat_2"], off)
                    self.assertNotIn(spec["beat_3"], off)
                    # kalıp: açılış = ortamın kod metni, kamera/stil kuyruğu hit'ten birebir, sıra 0-4s/4-9s/9-15s
                    self.assertTrue(prompt.startswith(f"0-4s: {es.FIRE_TOR_ENVS[env]['key']} "))
                    self.assertTrue(prompt.endswith(" " + TAIL))
                    self.assertEqual(sc["style_suffix"], TAIL)
                    self.assertEqual(prompt, f"{sc['story']}. {TAIL}" if not sc["story"].endswith(".")
                                     else f"{sc['story'][:-1]}. {TAIL}")
                    pos = [prompt.find(x) for x in ("0-4s: ", " 4-9s: ", " 9-15s: ", " Handheld footage")]
                    self.assertEqual(pos, sorted(pos))
                    self.assertNotIn(-1, pos)
                    # olaylar havuzdan (araç dahil), insan cümlesi ortamın birebir havuzundan
                    s2 = es.beat_text(FT, "slice_2", spec["beat_2"], spec["vehicle"])
                    s3 = es.beat_text(FT, "slice_3", spec["beat_3"], spec["vehicle"])
                    self.assertIn(s2[1:], hit["slices"]["slice_2"])
                    self.assertIn(s3[1:], hit["slices"]["slice_3"])
                    self.assertIn(spec["vehicle"], [v for v, _ in es.event_vehicles(FT, None)])
                    people = {t.replace("{N}", es.people_word(spec).capitalize())
                              for t in es.FALLBACK_PEOPLE_FIRE_ENV[env]}
                    self.assertIn(hit["slices"]["slice_1_rest"], people)
                    # eklenen iki cümle yok
                    self.assertNotIn(FULL, prompt)
                    self.assertNotIn(CONT, prompt)
                    self.assertLessEqual(len(prompt.split()), es.max_prompt_words(FT))
                    self.assertLessEqual(len(prompt), es.max_prompt_chars(FT))
                    self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                                           "style_suffix": sc["style_suffix"]}), [])
        self.assertIsNone(es.HIT_OVERRIDE.get())   # mod sızmaz

    def test_t4_u11_never_even_when_lru_best(self):
        # geçmişte T4+U11 hiç yok, diğer bütün çiftler yakın zamanda kullanılmış gibi: yine de T4+U11 gelmez
        spot = es.FIRE_TOR_ENVS["forest_edge"]["spots"][1]
        token = es.HIT_OVERRIDE.set(hp.override(FT, "forest_edge"))
        try:
            self.assertNotIn(("T4", "U11"), es.allowed_pairs(FT, None, spot))
            for seed in range(60):
                self.assertNotEqual(es.choose_beats(FT, None, spot, [], random.Random(seed)), ("T4", "U11"))
        finally:
            es.HIT_OVERRIDE.reset(token)
        self.assertIn(("T4", "U11"), es.allowed_pairs(FT, None, spot))   # normal yol aynen

    def test_no_gpt_call(self):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")):
            d = hit_build("tree_street", 7)
        gpt.assert_not_called()
        self.assertTrue(d["scenes"][0]["prompt"].endswith(TAIL))
        with self.assertRaises(RuntimeError):
            asyncio.run(hp.no_gpt("x"))

    def test_approval_lines(self):
        d = hit_build("village_woods", 3)
        st = d["structure"]
        spec, hit = st["spec"], st["hit"]
        lines = hit["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kalıbı (kaynak: 5 Kas 2026 00:13)")
        self.assertTrue(lines[2].startswith("• Açılış (forest_edge → village_woods): «"))
        self.assertIn(f"» → «{es.FIRE_TOR_ENVS['village_woods']['key']}»", lines[2])
        self.assertEqual(lines[3], f"• İnsan: «Two people run away in the street below.» → "
                                   f"«{hit['slices']['slice_1_rest']}»")
        self.assertTrue(lines[4].startswith(f"• 4-9s (T4 → {spec['beat_2']}): "))
        self.assertTrue(lines[4].endswith(f"→ «{hit['slices']['slice_2']}»"))
        self.assertTrue(lines[5].startswith(f"• 9-15s (U11 → {spec['beat_3']}): "))
        self.assertTrue(lines[5].endswith(f"→ «{hit['slices']['slice_3']}»"))
        self.assertEqual(lines[6], "• Araç: aynı" if spec["vehicle"] == "pickup truck"
                         else f"• Araç: «pickup truck» → «{spec['vehicle']}»")
        self.assertIn("Full action from the very first frame to the last.", lines[7])
        # onay mesajında (format_final_prompt) mod satırı ayrı satır olarak, prompt aynen
        sc = d["scenes"][0]
        _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"], "style_suffix": TAIL,
                                       "hit_lines": hit["lines"], "environment": st["environment"]})
        self.assertIn("\nMod: ⭐ Hit kalıbı (kaynak: 5 Kas 2026 00:13)\n", body)
        self.assertIn(hit["lines"], body)
        self.assertIn("\n\n" + sc["prompt"], body)
        # normal üretimde satır yok
        _, normal = format_final_prompt({"prompt": "p", "story": "s", "style_suffix": "x"})
        self.assertNotIn("Hit kalıbı", normal)

    def test_submit_rejects_tampering(self):
        d = hit_build("forest_edge", 11)
        sc, st = d["scenes"][0], d["structure"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        added = {**info, "prompt": sc["prompt"].replace("No readable signs", f"{FULL} No readable signs")}
        self.assertTrue(cp.submit_issues(st, added))
        self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": st["spec"]["suffix"]}))
        bad = {**st, "spec": {**st["spec"], "beat_2": "T4", "beat_3": "U11"}}
        self.assertTrue(any("hit çifti" in x for x in cp.submit_issues(bad, info)))

    def test_rewrite_returns_same_hit_story(self):
        d = hit_build("tree_street", 5)
        st = d["structure"]
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, d["scenes"][0]["story"])
        self.assertNotIn(CONT, story)

    def test_override_rejects_inactive(self):
        with self.assertRaises(ValueError):
            hp.override(es.PYROCLASTIC, "forest_edge")
        with self.assertRaises(ValueError):
            hp.override(FT, "meadow")


class TestHitPipeline(_Quiet):
    def test_pipeline_passes_hit_env_and_sends_hit_prompt(self):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        seen = {}

        async def gen(config):
            seen["config"] = dict(config)
            ps.reset_memory()
            random.seed(21)
            cfg = {k: v for k, v in config.items() if k not in ("axes_loader", "caption_loader")}
            return await pg.generate_creative_prompts({**cfg, "domain": "fire_disasters"})
        t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
        t.setUp()
        try:
            rep = _Reporter(approve=True, needs_approval=True)
            orig = main.run_pipeline

            async def run_with_hit(**kw):
                return await orig(**kw, hit_env="village_woods")
            with patch.object(main, "run_pipeline", run_with_hit):
                r = t.run_pipe(gen=AsyncMock(side_effect=gen), reporter=rep, event=FT)
        finally:
            t.doCleanups()
        self.assertTrue(r["success"], r)
        self.assertEqual(seen["config"]["hit_env"], "village_woods")
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)   # Kie gönderimi Onay'a bağlı
        info = approve[0]
        self.assertTrue(info["prompt"].endswith(TAIL))
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı (kaynak: 5 Kas 2026 00:13)"))
        self.assertEqual(t.create.await_args.args[1], info["prompt"])   # Kie'ye giden = onaydaki
        self.assertNotIn(FULL, info["prompt"])
        self.assertNotIn(CONT, info["prompt"])

    def test_normal_pipeline_has_no_hit_env(self):
        import main
        from test_tur29_infra import TestPipelineTur29
        seen = {}

        async def gen(config):
            seen["config"] = dict(config)
            raise RuntimeError("dur")
        t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
        t.setUp()
        try:
            t.run_pipe(gen=AsyncMock(side_effect=gen), event=FT)
        finally:
            t.doCleanups()
        self.assertNotIn("hit_env", seen["config"])


class TestHitTelegram(_Quiet):
    def setUp(self):
        import bot
        self.bot = bot
        self.di = str(bot.DOMAIN_KEYS.index("fire_disasters"))
        self.ei = str(bot.domain_events("fire_disasters").index(FT))

    def _buttons(self, markup):
        return [b for row in markup.inline_keyboard for b in row]

    def test_button_only_on_fire_tornado(self):
        from test_tur29_infra import _context, _update
        ctx = _context()
        upd = _update(data=f"uret:e:{self.di}:{self.ei}")
        asyncio.run(self.bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        labels = [b.text for b in self._buttons(kb)]
        # 12 Kas (3): yanında ⭐ Hit kalıbı · Yaklaşma (tests/test_yaklasma.py)
        self.assertEqual(labels, ["✅ Üret", "❌ İptal", "⭐ Hit kalıbı", "⭐ Hit kalıbı · Yaklaşma"])
        # diğer olaylarda yok (orman yangını, kül bulutu dahil)
        for d in self.bot.DOMAIN_KEYS:
            if not self.bot.domain_active(d):
                continue
            for i, e in enumerate(self.bot.domain_events(d)):
                if e == FT:
                    continue
                upd = _update(data=f"uret:e:{self.bot.DOMAIN_KEYS.index(d)}:{i}")
                asyncio.run(self.bot.on_callback(upd, ctx))
                kw = upd.callback_query.edit_message_text.await_args.kwargs
                if "reply_markup" in kw:
                    self.assertNotIn("⭐ Hit kalıbı", [b.text for b in self._buttons(kw["reply_markup"])], e)

    def test_env_menu_confirm_and_produce(self):
        from test_tur29_infra import _context, _update
        ctx = _context()
        upd = _update(data=f"uret:h:{self.di}:{self.ei}")
        asyncio.run(self.bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual([b.text for b in self._buttons(kb)],
                         ["orman kenarı yerleşim (forest_edge)", "ağaçlık mahalle sokağı (tree_street)",
                          "köy kenarı, çevresi orman (village_woods)", "⬅️ Geri"])
        for b in self._buttons(kb):
            self.assertLessEqual(len(b.callback_data.encode()), 64)
        upd = _update(data=f"uret:hv:{self.di}:{self.ei}:1")
        asyncio.run(self.bot.on_callback(upd, ctx))
        text = upd.callback_query.edit_message_text.await_args.args[0]
        self.assertIn("Mod: ⭐ Hit kalıbı (kaynak: 5 Kas 2026 00:13)", text)
        self.assertIn("(tree_street)", text)
        upd = _update(data=f"uret:hok:{self.di}:{self.ei}:1")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(self.bot.pipeline, "run_pipeline", runner), \
             patch.object(self.bot, "_production_lock", asyncio.Lock()):
            asyncio.run(self.bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["event"], kw["hit_env"]), (FT, "tree_street"))
        self.assertTrue(kw["reporter"].needs_approval)   # TEST modunda ✋ Onay açık

    def test_invalid_hit_selection(self):
        self.assertIsNone(self.bot.parse_hit(self.di, self.ei, "9"))
        wf = str(self.bot.domain_events("fire_disasters").index(es.WILDFIRE))
        self.assertIsNone(self.bot.parse_hit(self.di, wf))
        self.assertEqual(self.bot.parse_hit(self.di, self.ei, "2"), ("fire_disasters", FT, "village_woods"))


if __name__ == "__main__":
    unittest.main()
