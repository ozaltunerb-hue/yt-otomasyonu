# 12 Kas 2026 (3), Bahadır: ⭐ Hit kalıbı · Yaklaşma modu (core/hit_prompts.py YAKLASMA_ATES_HORTUMU). Tehdit caddenin
# ucundan kameraya doğru gelir, final terasın hemen altındaki evde. Hikâye tamamen koddan, GPT yok. Ateş hortumunun
# normal yolu ve mevcut "⭐ Hit kalıbı" modu birebir aynı kalır (snapshot eşitliği burada, 40 tohum kilidi ayrı testlerde).
# Ağ yok: GPT, Kie, Notion, Telegram sahte.
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
from core.trace_format import format_final_prompt   # noqa: E402

FT = es.FIRE_TORNADO
YK = hp.YAKLASMA_ATES_HORTUMU
ENVS = ("forest_edge", "tree_street", "village_woods")
SEEDS = range(1, 11)
FOLLOW = "the camera turns slowly to keep the tornado in frame as it approaches"
FIXED = "the camera stays fixed"
HIT_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "hit_kalibi_snapshot.json")


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


def build(env: str, seed: int, history=None, key: str = "approach_env") -> dict:
    """generate_creative_prompts (Telegram'daki ile aynı config anahtarı)."""
    ps.reset_memory()
    random.seed(seed)
    return asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": FT, key: env,
                                                     "used_combos": list(history or []), "recent_topics": []}))


def street(env: str) -> str:
    return "road" if env == "village_woods" else "street"


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.APPROACH_MODE_LABEL, "⭐ Hit kalıbı · Yaklaşma")
        self.assertIs(hp.YAKLASMA_KAMERA_TAKIP, True)
        self.assertEqual(tuple(YK["openings"]), ENVS)
        self.assertEqual(YK["openings"]["forest_edge"],
                         "A colossal spinning fire tornado, a twisting funnel several times taller than the houses and "
                         "trees, tears out of a burning forest at the far end of the street and advances down the street "
                         "toward the camera, its wide base engulfing the houses on both sides.")
        self.assertEqual(sorted(YK["finals"]), ["Y1", "Y2", "Y3", "Y4"])
        self.assertEqual(hp.yaklasma_people("village_woods", 2),
                         "Two people run up the road below, away from the fire tornado.")
        self.assertEqual(hp.yaklasma_people("tree_street", 3),
                         "Three people run up the street below, away from the fire tornado.")
        self.assertEqual(hp.yaklasma_camera_text(True), FOLLOW)
        self.assertEqual(hp.yaklasma_camera_text(False), FIXED)
        self.assertIn("looking straight down a long village road into the distance",
                      hp.yaklasma_tail("village_woods"))
        self.assertIn("looking straight down a long street into the distance", hp.yaklasma_tail("forest_edge"))
        for e in ENVS:
            self.assertTrue(hp.yaklasma_tail(e).startswith("Handheld footage filmed on a rooftop terrace"))
            self.assertTrue(hp.yaklasma_tail(e).endswith("No readable signs, text or flags."))

    def test_excluded_mids(self):
        # araç savrulması / dönmesi / takla: T1, T5, T6 (normal yolda da pasif); T4 kullanılabilir
        self.assertEqual(set(YK["excluded_mids"]), {"T1", "T5", "T6"})
        self.assertNotIn("T4", YK["excluded_mids"])
        with self.assertRaises(es.StructureError):
            hp.yaklasma_mid("forest_edge", "T5", "SUV")
        ov = hp.yaklasma_override(FT, "forest_edge")
        for spot in es.FIRE_TOR_ENVS["forest_edge"]["spots"]:
            token = es.HIT_OVERRIDE.set(ov)
            try:
                mids = {v for v, _ in es.allowed_pairs(FT, None, spot)}
            finally:
                es.HIT_OVERRIDE.reset(token)
            self.assertFalse(mids & set(YK["excluded_mids"]))
            self.assertIn("T4", mids)

    def test_all_combos_fit_or_are_guarded(self):
        """768 kombinasyonun sığmayanları (Y3 + takip) sığma korumasıyla elenir; her durumda en az 3 final kalır."""
        vehicles = [v for v, _ in es.event_vehicles(FT, None)]
        mids = [t for t in es.EVENT_BEATS[FT]["slice_2"]
                if t not in es.disabled_beats(FT) and t not in YK["excluded_mids"]]
        over = set()
        for env in ENVS:
            for n in (2, 3):
                for m in mids:
                    for v in vehicles:
                        fit = []
                        for f in YK["finals"]:
                            for follow in (True, False):
                                p = hp.yaklasma_prompt(env, n, m, v, f, follow)
                                self.assertLessEqual(len(p), hp.YAKLASMA_MAX_CHARS)
                                if len(p.split()) > hp.YAKLASMA_MAX_WORDS:
                                    over.add(f)
                                elif follow:
                                    fit.append(f)
                        self.assertGreaterEqual(len(fit), 3, (env, n, m, v))
        self.assertEqual(over, {"Y3"})


class TestYaklasmaMode(_Quiet):
    def _check(self, env, d):
        sc, st = d["scenes"][0], d["structure"]
        ap, spec = st["approach"], st["spec"]
        prompt, s = sc["prompt"], street(env)
        self.assertEqual(spec["fire_env"], env)
        self.assertEqual(ap["env"], env)
        # açılış birebir ve kameraya doğru
        self.assertTrue(prompt.startswith(f"0-4s: {YK['openings'][env]} "))
        self.assertIn("toward the camera", prompt.split(" 4-9s: ")[0])
        # insan cümlesi
        self.assertIn(f" {hp.yaklasma_people(env, spec['people'])} 4-9s: ", prompt)
        self.assertIn(spec["people"], (2, 3))
        # orta: havuzdan (T*), "Halfway down the street/road, " + küçük harf
        mid = prompt.split(" 4-9s: ")[1].split(" 9-15s: ")[0]
        self.assertTrue(mid.startswith(f"Halfway down the {s}, "), mid)
        pool = es.beat_text(FT, "slice_2", ap["mid"], spec["vehicle"])
        self.assertEqual(mid, f"Halfway down the {s}, {pool[0].lower()}{pool[1:]}.")
        self.assertIn(ap["mid"], es.EVENT_BEATS[FT]["slice_2"])
        self.assertNotIn(ap["mid"], YK["excluded_mids"])
        self.assertNotIn(ap["mid"], es.disabled_beats(FT))
        # final: Y1-Y4, "Right below the terrace"
        fin = prompt.split(" 9-15s: ")[1].split(" Handheld footage")[0]
        self.assertIn(ap["final"], ("Y1", "Y2", "Y3", "Y4"))
        self.assertEqual(fin, YK["finals"][ap["final"]])
        self.assertTrue(fin.startswith("Right below the terrace"))
        # U* finali yok
        for bid in es.EVENT_BEATS[FT]["slice_3"]:
            self.assertNotIn(es.beat_text(FT, "slice_3", bid, spec["vehicle"]), prompt)
            self.assertNotIn(bid, ap["final"])
        # eklenen iki cümle yok
        self.assertNotIn("Full action", prompt)
        self.assertNotIn("Until the last frame", prompt)
        # sıra: açılış + insan + 4-9s + 9-15s + stil eki
        pos = [prompt.find(x) for x in ("0-4s: ", " 4-9s: ", " 9-15s: ", " Handheld footage")]
        self.assertNotIn(-1, pos)
        self.assertEqual(pos, sorted(pos))
        self.assertTrue(prompt.endswith(" " + hp.yaklasma_tail(env)))
        self.assertEqual(sc["style_suffix"], hp.yaklasma_tail(env))
        self.assertEqual(prompt, f"{sc['story'][:-1]}. {sc['style_suffix']}")
        if env == "village_woods":
            self.assertNotIn("street", prompt)
        # sınırlar
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        # kayıt T*+Y*
        self.assertIn(f"#{ap['mid']}+{ap['final']}|", d["combo_key"])
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])

    def test_each_env_10_seeds_camera_follow(self):
        for env in ENVS:
            for seed in SEEDS:
                with self.subTest(env=env, seed=seed):
                    d = build(env, seed)
                    self._check(env, d)
                    p = d["scenes"][0]["prompt"]
                    self.assertIn(f"slight hand shake, {FOLLOW}, an empty foreground", p)
                    self.assertNotIn(FIXED, p)
                    self.assertTrue(d["structure"]["approach"]["follow"])
        self.assertIsNone(es.HIT_OVERRIDE.get())   # mod sızmaz

    def test_each_env_10_seeds_camera_fixed(self):
        with patch.object(hp, "YAKLASMA_KAMERA_TAKIP", False):
            for env in ENVS:
                for seed in SEEDS:
                    with self.subTest(env=env, seed=seed):
                        d = build(env, seed)
                        self._check(env, d)
                        p = d["scenes"][0]["prompt"]
                        self.assertIn(f"slight hand shake, {FIXED}, an empty foreground", p)
                        self.assertNotIn(FOLLOW, p)
                        self.assertFalse(d["structure"]["approach"]["follow"])
                        self.assertIn("Kamera: sabit", d["structure"]["approach"]["lines"])

    def test_final_lru(self):
        spot = es.FIRE_TOR_ENVS["forest_edge"]["spots"][1].lower()
        def combo(tag):
            return f"fire_disasters|none|{FT.lower()}|{spot}##{tag}|bystander_handheld"
        ps.reset_memory()
        hist = [combo("T2+Y1"), combo("T7+Y3"), combo("T8+Y2")]
        self.assertEqual(hp.yaklasma_choose_final(FT, hist, random.Random(1)), "Y4")
        hist.append(combo("T4+Y4"))
        self.assertEqual(hp.yaklasma_choose_final(FT, hist, random.Random(1)), "Y1")
        # hiç kullanılmamışlar arasında eşit
        got = {hp.yaklasma_choose_final(FT, [], random.Random(s)) for s in range(60)}
        self.assertEqual(got, {"Y1", "Y2", "Y3", "Y4"})
        # sığma koruması: Y3 aday olmaz, LRU kalanlarda
        self.assertEqual(hp.yaklasma_choose_final(FT, [combo("T2+Y1"), combo("T8+Y2"), combo("T7+Y4")],
                                                  random.Random(1), fits=lambda f: f != "Y3"), "Y1")
        # art arda üretim: hafıza T*+Y* tutar, 4 üretimde 4 farklı final
        ps.reset_memory()
        finals = []
        for seed in range(4):
            random.seed(seed)
            d = asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": FT,
                                                         "approach_env": "forest_edge", "used_combos": [],
                                                         "recent_topics": []}))
            finals.append(d["structure"]["approach"]["final"])
        self.assertEqual(sorted(finals), ["Y1", "Y2", "Y3", "Y4"])
        self.assertTrue(all("+Y" in t for t in es._BEAT_MEMORY[FT][-4:]))

    def test_no_gpt_call(self):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")):
            d = build("tree_street", 7)
        gpt.assert_not_called()
        self.assertTrue(d["scenes"][0]["prompt"].endswith(hp.yaklasma_tail("tree_street")))

    def test_submit_rejects_tampering_and_rewrite_same(self):
        d = build("forest_edge", 11)
        sc, st = d["scenes"][0], d["structure"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        added = {**info, "prompt": sc["prompt"].replace("No readable signs", f"{sk.FULL_MOTION} No readable signs")}
        self.assertTrue(cp.submit_issues(st, added))
        self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": st["spec"]["suffix"]}))
        bad = {**st, "approach": {**st["approach"], "final": "U11"}}
        self.assertTrue(cp.submit_issues(bad, info))
        bad = {**st, "approach": {**st["approach"], "mid": "T5"}}
        self.assertTrue(cp.submit_issues(bad, info))
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])

    def test_approval_lines(self):
        d = build("village_woods", 3)
        sc, st = d["scenes"][0], d["structure"]
        ap = st["approach"]
        lines = ap["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kalıbı · Yaklaşma")
        self.assertEqual(lines[1], "Ortam: köy kenarı, çevresi orman (village_woods)")
        self.assertTrue(lines[2].startswith(f"Orta (4-9s): {ap['mid']} «Halfway down the road, "))
        self.assertTrue(lines[3].startswith(f"Final (9-15s): {ap['final']} «Right below the terrace"))
        self.assertEqual(lines[4], "Kamera: takip (yaklaşan hortumu yavaşça takip eder)")
        self.assertTrue(lines[5].startswith(f"Kelime: {len(sc['prompt'].split())} (en fazla 230)"))
        _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"],
                                       "style_suffix": sc["style_suffix"], "hit_lines": ap["lines"],
                                       "environment": st["environment"]})
        self.assertIn("\nMod: ⭐ Hit kalıbı · Yaklaşma\n", body)
        self.assertIn("\n\n" + sc["prompt"], body)
        axes = json.loads(d["axes_json"])["axes"]
        self.assertEqual((axes["beats"], axes["mod"]), (f"{ap['mid']}+{ap['final']}", "yaklasma"))

    def test_override_rejects_inactive(self):
        with self.assertRaises(ValueError):
            hp.yaklasma_override(es.PYROCLASTIC, "forest_edge")
        with self.assertRaises(ValueError):
            hp.yaklasma_override(FT, "meadow")


class TestOtherModesUnchanged(_Quiet):
    def test_hit_mode_snapshot_equal(self):
        """Mevcut ⭐ Hit kalıbı modunun çıktısı (Yaklaşma eklenmeden önce alınan, 3 ortam × 10 tohum) birebir aynı."""
        with open(HIT_FIXTURE, encoding="utf-8") as f:
            base = json.load(f)
        self.assertEqual(len(base), 30)
        for key, want in sorted(base.items()):
            env, seed = key.split("/")
            d = build(env, int(seed), key="hit_env")
            with self.subTest(key=key):
                self.assertEqual(d["scenes"][0]["prompt"], want["prompt"])
                self.assertEqual(d["combo_key"], want["combo"])
                self.assertEqual(d["structure"]["hit"]["lines"], want["lines"])
                self.assertNotIn("approach", d["structure"])

    def test_normal_fire_tornado_has_no_approach(self):
        ps.reset_memory()
        random.seed(5)
        d = asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": FT, "used_combos": [],
                                                     "recent_topics": []}))
        self.assertNotIn("approach", d["structure"])
        self.assertNotIn("Halfway down the", d["scenes"][0]["prompt"])
        self.assertNotIn("Right below the terrace", d["scenes"][0]["prompt"])


class TestYaklasmaPipeline(_Quiet):
    def test_pipeline_passes_approach_env_and_sends_prompt(self):
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

            async def run_with(**kw):
                return await orig(**kw, approach_env="tree_street")
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=gen), reporter=rep, event=FT)
        finally:
            t.doCleanups()
        self.assertTrue(r["success"], r)
        self.assertEqual(seen["config"]["approach_env"], "tree_street")
        self.assertNotIn("hit_env", seen["config"])
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)   # Kie gönderimi Onay'a bağlı
        info = approve[0]
        self.assertTrue(info["prompt"].endswith(hp.yaklasma_tail("tree_street")))
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı · Yaklaşma\nOrtam: "))
        self.assertEqual(t.create.await_args.args[1], info["prompt"])   # Kie'ye giden = onaydaki


class TestYaklasmaTelegram(_Quiet):
    def setUp(self):
        import bot
        self.bot = bot
        self.di = str(bot.DOMAIN_KEYS.index("fire_disasters"))
        self.ei = str(bot.domain_events("fire_disasters").index(FT))

    def _buttons(self, markup):
        return [b for row in markup.inline_keyboard for b in row]

    def test_button_next_to_hit(self):
        from test_tur29_infra import _context, _update
        ctx = _context()
        upd = _update(data=f"uret:e:{self.di}:{self.ei}")
        asyncio.run(self.bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        rows = [[b.text for b in r] for r in kb.inline_keyboard]
        self.assertEqual(rows[-1], ["⭐ Hit kalıbı", "⭐ Hit kalıbı · Yaklaşma"])
        for b in self._buttons(kb):
            self.assertLessEqual(len(b.callback_data.encode()), 64)

    def test_env_menu_confirm_and_produce(self):
        from test_tur29_infra import _context, _update
        ctx = _context()
        upd = _update(data=f"uret:ya:{self.di}:{self.ei}")
        asyncio.run(self.bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual([b.text for b in self._buttons(kb)],
                         ["orman kenarı yerleşim (forest_edge)", "ağaçlık mahalle sokağı (tree_street)",
                          "köy kenarı, çevresi orman (village_woods)", "⬅️ Geri"])
        upd = _update(data=f"uret:yav:{self.di}:{self.ei}:2")
        asyncio.run(self.bot.on_callback(upd, ctx))
        text = upd.callback_query.edit_message_text.await_args.args[0]
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma", text)
        self.assertIn("(village_woods)", text)
        self.assertIn("Kamera: takip", text)
        upd = _update(data=f"uret:yaok:{self.di}:{self.ei}:2")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(self.bot.pipeline, "run_pipeline", runner), \
             patch.object(self.bot, "_production_lock", asyncio.Lock()):
            asyncio.run(self.bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["event"], kw["approach_env"]), (FT, "village_woods"))
        self.assertNotIn("hit_env", kw)
        self.assertTrue(kw["reporter"].needs_approval)   # TEST modunda ✋ Onay açık

    def test_invalid_selection(self):
        self.assertIsNone(self.bot.parse_approach(self.di, self.ei, "9"))
        wf = str(self.bot.domain_events("fire_disasters").index(es.WILDFIRE))
        self.assertIsNone(self.bot.parse_approach(self.di, wf))
        self.assertEqual(self.bot.parse_approach(self.di, self.ei, "0"), ("fire_disasters", FT, "forest_edge"))


if __name__ == "__main__":
    unittest.main()
