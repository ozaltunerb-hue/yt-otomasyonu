# 12 Kas 2026 (5), Bahadır: dev dalga "⭐ Hit kalıbı · 24 Eylül" modu (core/hit_prompts.py DALGA_24EYLUL) ve Hit kalıbı
# modlarının Onay görüntü düzeltmesi. Hikâye tamamen koddan, GPT yok, zaman etiketi yok. Dev dalganın normal yolu, ateş
# hortumunun bütün modları ve diğer olaylar değişmez. Ağ yok: GPT, Kie, Notion, Telegram sahte.
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

TIDAL = es.TIDAL
FT = es.FIRE_TORNADO
DZ = hp.DALGA_24EYLUL
PEOPLE = "People watch from the rooftops across the street while others run along the street below."
CORE = ("The wave sweeps parked cars into the storefronts; vehicles smash like toys against the windows as the surging "
        "muddy water pushes half-submerged debris down the whole street toward the camera.")
FOLLOW = "the camera stays in place and turns slightly to follow the water"
FIXED = "the camera stays fixed"
DOMAIN = "urban_city_disasters"


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
    hp._DZ_GEO_MEMORY.clear()
    hp._GEO_MEMORY.clear()


def gen(**extra) -> dict:
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": TIDAL, "dalga24": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.DALGA24_MODE_LABEL, "⭐ Hit kalıbı · 24 Eylül")
        self.assertIs(hp.DALGA24_KAMERA_TAKIP, True)
        self.assertEqual(sorted(DZ["geos"]), ["D1", "D2", "D3", "D4", "D5", "D6"])
        self.assertEqual(DZ["geos"]["D3"], {"name": "Japonya", "place": "a Japanese coastal town",
                                            "shops": "the row of small shops with low tiled roofs"})
        self.assertEqual(hp.dalga24_opening("D1", "A1"),
                         "A colossal tidal wave rises behind the row of seafront shops and cafés with awnings across "
                         "the street in a grey British seaside town and crashes over their roofs into the street.")
        self.assertEqual(DZ["people"], PEOPLE)
        self.assertEqual(DZ["core"], CORE)
        self.assertEqual(sorted(DZ["finals"]), ["F1", "F2", "F3", "F4"])
        self.assertEqual(hp.dalga24_camera_text(True), FOLLOW)
        self.assertEqual(hp.dalga24_camera_text(False), FIXED)
        for follow in (True, False):
            t = hp.dalga24_tail(follow)
            self.assertIn("the balcony railing visible in the foreground", t)
            self.assertIn("Raw natural overcast light", t)
            self.assertTrue(t.endswith("No readable signs, text or flags."))

    def test_all_combos_within_limits(self):
        """Coğrafya × açılış × final × kamera: hepsi ≤ 230 kelime ve ≤ 1400 karakter."""
        n, over = 0, []
        for g in DZ["geos"]:
            for a in DZ["openings"]:
                for f in DZ["finals"]:
                    for follow in (True, False):
                        p = hp.dalga24_prompt(g, a, f, follow)
                        n += 1
                        if len(p.split()) > hp.DALGA24_MAX_WORDS or len(p) > hp.DALGA24_MAX_CHARS:
                            over.append((g, a, f, follow, len(p.split()), len(p)))
        self.assertEqual(n, 96)
        self.assertEqual(over, [])

    def test_sentences_only_in_this_mode(self):
        """Yeni modun cümleleri havuzlarda, hit kayıtlarında ve diğer modların / olayların çıktısında yok."""
        marks = ["vehicles smash like toys", "People watch from the rooftops across the street",
                 "a second, even bigger wave rises", "the balcony railing visible in the foreground",
                 "turns slightly to follow the water", "Raw natural overcast light under a grey sky"]
        pools = json.dumps({e: {s: {k: v["text"] for k, v in b[s].items()} for s in ("slice_2", "slice_3")}
                            for e, b in es.EVENT_BEATS.items()})
        others = pools + json.dumps(hp.HIT_PROMPTS) + json.dumps(hp.YAKLASMA_ATES_HORTUMU, default=str)
        for ev in ps.active_events():
            for seed in range(1, 6):
                others += json.dumps(ps.snapshot_event(ev, seed))
        for env in hp.yaklasma_envs(FT):
            reset()
            random.seed(1)
            others += asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": FT,
                                                               "approach_env": env, "used_combos": [],
                                                               "recent_topics": []}))["scenes"][0]["prompt"]
        for m in marks:
            self.assertNotIn(m, others, m)


class TestDalgaMode(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        dz = st["dalga24"]
        prompt = sc["prompt"]
        g = DZ["geos"][dz["geo"]]
        self.assertIn(g["place"], prompt)
        self.assertIn(g["shops"], prompt)
        self.assertIn(dz["opening"], ("A1", "A2"))
        self.assertTrue(prompt.startswith(hp.dalga24_opening(dz["geo"], dz["opening"]) + " "))
        self.assertIn(f" {PEOPLE} {CORE} ", prompt)
        self.assertIn(dz["final"], DZ["finals"])
        self.assertIn(f"{CORE} {DZ['finals'][dz['final']]}", prompt)
        for bad in ("0-4s", "4-9s", "9-15s", "Full action", "Until the last frame"):
            self.assertNotIn(bad, prompt)
        self.assertIn("balcony railing visible in the foreground", prompt)
        self.assertIn("Raw natural overcast light", prompt)
        self.assertTrue(prompt.endswith(" " + hp.dalga24_tail(dz["follow"])))
        self.assertEqual(sc["style_suffix"], hp.dalga24_tail(dz["follow"]))
        self.assertEqual(prompt, f"{sc['story'][:-1]}. {sc['style_suffix']}")
        pos = [prompt.find(x) for x in (hp.dalga24_opening(dz["geo"], dz["opening"]), PEOPLE, CORE,
                                        DZ["finals"][dz["final"]], "Handheld phone footage")]
        self.assertNotIn(-1, pos)
        self.assertEqual(pos, sorted(pos))
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        self.assertIn(f"#{dz['opening']}+{dz['final']}|", d["combo_key"])
        for slot in ("slice_2", "slice_3"):   # normal havuz metni yok
            for bid in es.EVENT_BEATS[TIDAL][slot]:
                self.assertNotIn(es.beat_text(TIDAL, slot, bid, "car")[4:], prompt)
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        return dz

    def test_first_production_and_seeds(self):
        geos = set()
        for seed in range(1, 31):
            with self.subTest(seed=seed):
                dz = self._check(build(seed))
                self.assertNotEqual(dz["geo"], "D1")    # ilk üretimde D1 yok
                self.assertEqual(dz["opening"], "A1")   # ilk üretimde A1
                self.assertIn(f"slight hand shake, {FOLLOW}; one continuous shot", build(seed)["scenes"][0]["prompt"])
                geos.add(dz["geo"])
        self.assertEqual(geos, {"D2", "D3", "D4", "D5", "D6"})

    def test_consecutive_lru(self):
        """Ardışık üretimler: coğrafya son 3, açılış son 2 (2 seçenekte derinlik 1'e iner: dönüşümlü), final son 2."""
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(8)]
            geos = [r["geo"] for r in runs]
            opens = [r["opening"] for r in runs]
            finals = [r["final"] for r in runs]
            for i in range(len(runs)):
                self.assertNotIn(geos[i], geos[max(0, i - 3):i], (seed, geos))
                self.assertNotIn(finals[i], finals[max(0, i - 2):i], (seed, finals))
            self.assertEqual(opens, ["A1", "A2"] * 4, (seed, opens))
            self.assertNotEqual(geos[0], "D1")

    def test_history_sources(self):
        def combo(tag):
            return f"{DOMAIN}|none|{TIDAL.lower()}|coastal avenue behind a seawall#riviera#{tag}|bystander_handheld"
        reset()
        hist = [combo("A1+F1"), combo("T7+W13"), combo("A2+F3")]
        for s in range(30):
            self.assertIn(hp.dalga24_choose_final(hist, random.Random(s)), ("F2", "F4"))
        self.assertEqual(hp.dalga24_choose_opening(hist, random.Random(1)), "A1")
        recs = [{"eksenler": json.dumps({"event": TIDAL, "axes": {"mod": "dalga24", "cografya": g}})}
                for g in ("D2", "D3", "D4")] + [{"eksenler": "bozuk"}]
        self.assertEqual(hp.dalga24_geo_history(recs), ["D2", "D3", "D4"])
        self.assertIsNone(hp.dalga24_geo_history(None))
        self.assertEqual({hp.dalga24_choose_geo(["D2", "D3", "D4"], random.Random(s)) for s in range(60)},
                         {"D1", "D5", "D6"})
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: recs)
            self.assertIn(d["structure"]["dalga24"]["geo"], ("D1", "D5", "D6"))
            self.assertEqual(json.loads(d["axes_json"])["axes"]["cografya"], d["structure"]["dalga24"]["geo"])

    def test_camera_fixed(self):
        with patch.object(hp, "DALGA24_KAMERA_TAKIP", False):
            for seed in range(1, 11):
                d = build(seed)
                self._check(d)
                p = d["scenes"][0]["prompt"]
                self.assertIn(f"slight hand shake, {FIXED}; one continuous shot", p)
                self.assertNotIn(FOLLOW, p)
                self.assertIn("Kamera: sabit", d["structure"]["dalga24"]["lines"])

    def test_no_gpt_and_rewrite_and_tampering(self):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")):
            d = build(7)
        gpt.assert_not_called()
        sc, st = d["scenes"][0], d["structure"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        self.assertTrue(cp.submit_issues(st, {**info, "prompt": "0-4s: " + sc["prompt"]}))
        self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"].replace(
            "No readable signs", f"{sk.FULL_MOTION} No readable signs")}))
        for bad in ({"geo": "D9"}, {"opening": "A3"}, {"final": "W13"}):
            self.assertTrue(cp.submit_issues({**st, "dalga24": {**st["dalga24"], **bad}}, info), bad)
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])

    def test_approval_lines(self):
        d = build(3)
        sc, dz = d["scenes"][0], d["structure"]["dalga24"]
        lines = dz["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kalıbı · 24 Eylül")
        self.assertEqual(lines[1], f"Coğrafya: {dz['geo']} {DZ['geos'][dz['geo']]['name']}")
        self.assertEqual(lines[2], "Açılış: A1 (binaların arkasından)")
        self.assertEqual(lines[3], f"Final: {dz['final']} «{DZ['finals'][dz['final']]}»")
        self.assertEqual(lines[4], "Kamera: takip (yerinde durur, suyu izlemek için hafifçe döner)")
        self.assertEqual(lines[5], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                   f"{len(sc['prompt'])} (en fazla 1400)")

    def test_normal_tidal_unchanged_path(self):
        reset()
        random.seed(5)
        d = asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": TIDAL, "used_combos": [],
                                                     "recent_topics": []}))
        self.assertNotIn("dalga24", d["structure"])
        self.assertTrue(d["scenes"][0]["prompt"].startswith("0-4s: "))
        self.assertNotIn("mode_label", d["trace"])


def _shown(d: dict) -> str:
    return sections_to_text(format_generation(d["trace"])) + "\n" + d["structure"]["axes_line"]


class TestApprovalDisplay(_Quiet):
    """Onay görüntüsü: 1. Seçim, 3. Hikâye ve Eksenler Kie prompt'unun gerçek parçalarını gösterir."""
    def _consistent(self, d: dict, parts: list[str], camera: str, absent: list[str]):
        prompt = d["scenes"][0]["prompt"]
        sel, _, rest = _shown(d).partition("🔍 2.")
        story = rest.split("🔍 3. Hikâye\n", 1)[1].split("\nEksenler (", 1)[0]
        for p in parts:
            self.assertIn(p, prompt)
            self.assertIn(p, sel)
            self.assertIn(p, story)
        self.assertIn(camera, prompt)
        self.assertIn(camera, sel)
        for a in absent:
            self.assertNotIn(a, _shown(d))
        # 3. Hikâye = prompt'un hikâye kısmı (etiketsiz)
        for chunk in story.split("\n", 1)[1].split(". "):
            self.assertIn(chunk.strip().rstrip("."), prompt)

    def test_yaklasma_display(self):
        for env in hp.yaklasma_envs(FT):
            for seed in range(1, 6):
                reset()
                random.seed(seed)
                d = asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": FT,
                                                             "approach_env": env, "used_combos": [],
                                                             "recent_topics": []}))
                ap = d["structure"]["approach"]
                normal_kv = d["structure"]["spec"]["key_visual"]
                self._consistent(d, [hp.yaklasma_opening(env, ap["geo"]),
                                     hp.yaklasma_mid(env, ap["mid"], ap["vehicle"]),
                                     hp.YAKLASMA_ATES_HORTUMU["finals"][ap["final"]]],
                                 hp.yaklasma_camera_text(ap["follow"]), [normal_kv, "kamera modu=B", "kamera modu=A"])
                self.assertIn(f"kamera modu={'takip' if ap['follow'] else 'sabit'}", d["structure"]["axes_line"])
                self.assertIn(f"({ap['mid']}): ", _shown(d))
                self.assertIn(f"({ap['final']}): ", _shown(d))

    def test_dalga_display(self):
        for seed in range(1, 6):
            d = build(seed)
            dz = d["structure"]["dalga24"]
            normal_kv = d["structure"]["spec"]["key_visual"]
            self._consistent(d, [hp.dalga24_opening(dz["geo"], dz["opening"]), CORE, DZ["finals"][dz["final"]]],
                             hp.dalga24_camera_text(dz["follow"]), [normal_kv, "kamera modu=B", "kamera modu=A",
                                                                     "0-4s", "4-9s olayı"])
            self.assertIn("Mod: ⭐ Hit kalıbı · 24 Eylül", _shown(d))
            self.assertIn(f"Final ({dz['final']}): ", _shown(d))

    def test_hit_display(self):
        for env in hp.envs(FT):
            reset()
            random.seed(2)
            d = asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": FT, "hit_env": env,
                                                         "used_combos": [], "recent_topics": []}))
            s = d["structure"]["hit"]["slices"]
            self._consistent(d, [d["structure"]["spec"]["key_visual"], s["slice_2"], s["slice_3"]],
                             "the camera stays fixed", ["kamera modu=B", "kamera modu=A"])
            self.assertIn("kamera modu=sabit (hit kalıbı)", d["structure"]["axes_line"])

    def test_final_prompt_block_has_mode_lines(self):
        d = build(4)
        sc, st = d["scenes"][0], d["structure"]
        _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"],
                                       "hit_lines": st["dalga24"]["lines"], "environment": st["environment"],
                                       "axes_line": st["axes_line"]})
        self.assertIn("\nMod: ⭐ Hit kalıbı · 24 Eylül\n", body)
        self.assertIn("\n\n" + sc["prompt"], body)


class TestDalgaPipelineAndBot(_Quiet):
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
                return await orig(**kw, dalga24=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=TIDAL)
        finally:
            t.doCleanups()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["dalga24"], True)
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı · 24 Eylül\nCoğrafya: D"))
        self.assertNotIn("0-4s", info["prompt"])
        self.assertEqual(t.create.await_args.args[1], info["prompt"])   # Kie'ye giden = onaydaki

    def test_bot_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ei = str(bot.domain_events(DOMAIN).index(TIDAL))
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        rows = [[b.text for b in r] for r in kb.inline_keyboard]
        self.assertEqual(rows[-2], ["⭐ Hit kalıbı · 24 Eylül"])
        self.assertEqual(rows[-1], ["⬅️ Geri"])
        self.assertEqual(len(rows), len(bot.view_keyboard(di, ei).inline_keyboard) + 1)   # bölge menüsü aynen
        upd = _update(data=f"uret:dz:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        self.assertIn("Mod: ⭐ Hit kalıbı · 24 Eylül", upd.callback_query.edit_message_text.await_args.args[0])
        upd = _update(data=f"uret:dzok:{di}:{ei}")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["event"], kw["dalga24"]), (TIDAL, True))
        self.assertTrue(kw["reporter"].needs_approval)
        # sel (diğer bölge olayı) menüsünde buton yok
        fi = str(bot.domain_events(DOMAIN).index("Flash flooding in city streets"))
        upd = _update(data=f"uret:e:{di}:{fi}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertNotIn("⭐ Hit kalıbı · 24 Eylül", [b.text for r in kb.inline_keyboard for b in r])
        self.assertIsNone(bot.parse_dalga24(di, fi))


if __name__ == "__main__":
    unittest.main()
