# 12 Kas 2026 (3)-(4), Bahadır: ⭐ Hit kalıbı · Yaklaşma modu v2 (core/hit_prompts.py YAKLASMA_ATES_HORTUMU). Tehdit
# caddenin ucundan kameraya doğru gelir, final terasın hemen altındaki evde. Coğrafya ekseni G1-G5, sürekli aksiyon,
# yan görünüm huni, orta O1-O5 (O5 araç savurma sadece bu modda). Hikâye tamamen koddan, GPT yok. Ateş hortumunun
# normal yolu ve mevcut "⭐ Hit kalıbı" modu birebir aynı kalır. Ağ yok: GPT, Kie, Notion, Telegram sahte.
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
SEEDS = range(1, 51)
FOLLOW = "the camera turns slowly to keep the tornado in frame"
FIXED = "the camera stays fixed"
ACTION = "Burning debris rains down from the very first frame."
O5_TEXT = "hurls it, in one piece, into the burning front yard"
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


def reset():
    ps.reset_memory()
    hp._GEO_MEMORY.clear()


def gen(env: str, key: str = "approach_env", history=None, **extra) -> dict:
    return asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": FT, key: env,
                                                     "used_combos": list(history or []), "recent_topics": [],
                                                     **extra}))


def build(env: str, seed: int, key: str = "approach_env") -> dict:
    reset()
    random.seed(seed)
    return gen(env, key)


def street(env: str) -> str:
    return "road" if env == "village_woods" else "street"


def all_combos():
    vehicles = [v for v, _ in es.event_vehicles(FT, None)]
    for env in ENVS:
        for geo in YK["geos"]:
            for n in (2, 3):
                for m in YK["mids"]:
                    for v in vehicles:
                        for f in YK["finals"]:
                            if (m, f) in YK["banned_pairs"]:
                                continue
                            for follow in (True, False):
                                yield (env, geo, n, m, v, f, follow), hp.yaklasma_prompt(env, geo, n, m, v, f, follow)


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.APPROACH_MODE_LABEL, "⭐ Hit kalıbı · Yaklaşma")
        self.assertIs(hp.YAKLASMA_KAMERA_TAKIP, True)
        self.assertEqual(sorted(YK["geos"]), ["G1", "G2", "G3", "G4", "G5"])
        self.assertEqual(YK["geos"]["G2"], {"name": "Avustralya", "forest": "burning eucalyptus bushland",
                                            "houses": "tin-roofed weatherboard houses"})
        self.assertEqual(hp.yaklasma_opening("forest_edge", "G1"),
                         "A colossal fire tornado, a twisting funnel several times taller than the houses, tears out of "
                         "a burning pine forest at the far end of the street and advances toward the camera, engulfing "
                         "the wooden suburban houses on both sides, flinging burning branches and roof shingles into "
                         "the street.")
        self.assertEqual(hp.yaklasma_people("village_woods", 2), "Two people run up the road below.")
        self.assertEqual(hp.yaklasma_people("tree_street", 3), "Three people run up the street below.")
        self.assertEqual(YK["action"], ACTION)
        self.assertEqual(sorted(YK["mids"]), ["O1", "O2", "O3", "O4", "O5"])
        self.assertEqual(sorted(YK["finals"]), ["Y1", "Y2", "Y3", "Y4"])
        self.assertEqual(YK["banned_pairs"], {("O1", "Y1"), ("O4", "Y1")})
        self.assertEqual(hp.yaklasma_mid("village_woods", "O1", "SUV"),
                         "Halfway down the road, the fire tornado rips the roof off a house and a power pole crashes "
                         "across the road just in front of the SUV.")
        self.assertEqual(hp.yaklasma_camera_text(True), FOLLOW)
        self.assertEqual(hp.yaklasma_camera_text(False), FIXED)
        self.assertIn("looking down a long village road, high vantage", hp.yaklasma_tail("village_woods"))
        self.assertIn("looking down a long street, high vantage", hp.yaklasma_tail("forest_edge"))
        for e in ENVS:
            t = hp.yaklasma_tail(e)
            self.assertIn("Seen from the side, a tall funnel of flame narrowing toward the ground", t)
            self.assertNotIn("A rotating funnel of flame with orbiting debris", t)
            self.assertTrue(t.endswith("No readable signs, text or flags."))
        # v1 pasif kayıt olarak duruyor (silinmedi)
        self.assertIn("forest_edge", hp.YAKLASMA_ATES_HORTUMU_V1["openings"])
        self.assertIs(hp.YAKLASMA_SIGMA_KORUMASI, False)

    def test_all_combos_within_limits(self):
        """Ortam × coğrafya × orta × final × araç × kişi × kamera: hepsi ≤ 230 kelime ve ≤ 1400 karakter."""
        over = [(k, len(p.split()), len(p)) for k, p in all_combos()
                if len(p.split()) > hp.YAKLASMA_MAX_WORDS or len(p) > hp.YAKLASMA_MAX_CHARS]
        self.assertEqual(over, [])

    def test_o5_only_in_this_mode(self):
        """O5 (araç savurma) metni hiçbir havuzda / başka modda yok; normal yol ve hit modu 40 tohumda görmez."""
        for event, b in es.EVENT_BEATS.items():
            for slot in ("slice_2", "slice_3"):
                for bid, beat in b[slot].items():
                    self.assertNotIn("hurls it, in one piece", beat["text"], (event, bid))
        self.assertNotIn("hurls it, in one piece", json.dumps(hp.HIT_PROMPTS))
        for env in ENVS:
            for seed in range(1, 11):
                d = build(env, seed, key="hit_env")
                self.assertNotIn(O5_TEXT, d["scenes"][0]["prompt"])
        for event in ps.active_events():
            for seed in range(1, 6):
                self.assertNotIn(O5_TEXT, json.dumps(ps.snapshot_event(event, seed)))


class TestYaklasmaMode(_Quiet):
    def _check(self, env, d):
        sc, st = d["scenes"][0], d["structure"]
        ap, spec = st["approach"], st["spec"]
        prompt, s = sc["prompt"], street(env)
        geo = YK["geos"][ap["geo"]]
        self.assertEqual(spec["fire_env"], env)
        self.assertEqual(ap["env"], env)
        # coğrafya: forest + houses ifadeleri
        self.assertIn(f"tears out of {geo['forest']} at the far end", prompt)
        self.assertIn(f"engulfing the {geo['houses']} on both sides", prompt)
        # açılış birebir
        opening = prompt.split(" 4-9s: ")[0]
        self.assertTrue(prompt.startswith(f"0-4s: {hp.yaklasma_opening(env, ap['geo'])} "))
        self.assertIn("advances toward the camera", opening)
        self.assertIn("flinging burning branches and roof shingles", opening)
        # insan + sürekli aksiyon (insandan hemen sonra)
        self.assertIn(f" {hp.yaklasma_people(env, spec['people'])} {ACTION} 4-9s: ", prompt)
        self.assertIn(spec["people"], (2, 3))
        # orta O1-O5, T* yok
        mid = prompt.split(" 4-9s: ")[1].split(" 9-15s: ")[0]
        self.assertIn(ap["mid"], YK["mids"])
        self.assertEqual(mid, hp.yaklasma_mid(env, ap["mid"], spec["vehicle"]))
        self.assertTrue(mid.startswith(f"Halfway down the {s}, "))
        for slot in ("slice_2", "slice_3"):
            for bid in es.EVENT_BEATS[FT][slot]:
                self.assertNotIn(es.beat_text(FT, slot, bid, spec["vehicle"]), prompt)
        # final Y1-Y4, yasak çift yok
        fin = prompt.split(" 9-15s: ")[1].split(" Handheld footage")[0]
        self.assertEqual(fin, YK["finals"][ap["final"]])
        self.assertTrue(fin.startswith("Right below the terrace"))
        self.assertNotIn((ap["mid"], ap["final"]), YK["banned_pairs"])
        # eklenen cümleler yok, yan görünüm var
        self.assertNotIn("Full action", prompt)
        self.assertNotIn("Until the last frame", prompt)
        self.assertIn("Seen from the side", prompt)
        self.assertNotIn("A rotating funnel of flame with orbiting debris", prompt)
        # sıra
        pos = [prompt.find(x) for x in ("0-4s: ", f" {ACTION}", " 4-9s: ", " 9-15s: ", " Handheld footage")]
        self.assertNotIn(-1, pos)
        self.assertEqual(pos, sorted(pos))
        self.assertTrue(prompt.endswith(" " + hp.yaklasma_tail(env)))
        self.assertEqual(sc["style_suffix"], hp.yaklasma_tail(env))
        if env == "village_woods":
            self.assertNotIn("street", prompt)
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        self.assertIn(f"#{ap['mid']}+{ap['final']}|", d["combo_key"])
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        return ap

    def test_each_env_50_seeds(self):
        for env in ENVS:
            mids, pairs = set(), set()
            for seed in SEEDS:
                with self.subTest(env=env, seed=seed):
                    d = build(env, seed)
                    ap = self._check(env, d)
                    mids.add(ap["mid"])
                    pairs.add((ap["mid"], ap["final"]))
                    self.assertNotEqual(ap["geo"], "G1")   # ilk üretimde G1 yok
                    p = d["scenes"][0]["prompt"]
                    self.assertIn(f"slight hand shake, {FOLLOW}; one continuous shot", p)
                    self.assertNotIn(FIXED, p)
                    self.assertEqual("⚠️ Araç savurma ortası (O5)" in ap["lines"], ap["mid"] == "O5")
            self.assertEqual(mids, set(YK["mids"]), env)
            self.assertFalse(pairs & YK["banned_pairs"], env)
        self.assertIsNone(es.HIT_OVERRIDE.get())   # mod sızmaz

    def test_camera_fixed(self):
        with patch.object(hp, "YAKLASMA_KAMERA_TAKIP", False):
            for env in ENVS:
                for seed in range(1, 11):
                    with self.subTest(env=env, seed=seed):
                        d = build(env, seed)
                        self._check(env, d)
                        p = d["scenes"][0]["prompt"]
                        self.assertIn(f"slight hand shake, {FIXED}; one continuous shot", p)
                        self.assertNotIn(FOLLOW, p)
                        self.assertIn("Kamera: sabit", d["structure"]["approach"]["lines"])

    def test_geo_lru_consecutive(self):
        """Ardışık üretimlerde son 3 coğrafya tekrar etmez; G1 ilk üretimde yok (5 Kas hit'i G1 sayılır)."""
        for seed in range(1, 21):
            reset()
            random.seed(seed)
            geos = [gen(ENVS[i % 3])["structure"]["approach"]["geo"] for i in range(8)]
            self.assertNotEqual(geos[0], "G1")
            for i in range(len(geos)):
                self.assertNotIn(geos[i], geos[max(0, i - 3):i], (seed, geos))
            self.assertNotIn(geos[0], ([*hp.YAKLASMA_GEO_SEED],))
        # Notion geçmişi: eksen kayıtlarından okunur (mod=yaklasma), son 3 elenir
        recs = [{"eksenler": json.dumps({"event": FT, "axes": {"mod": "yaklasma", "cografya": g}})}
                for g in ("G2", "G3", "G4")] + [{"eksenler": json.dumps({"event": FT, "axes": {"beats": "T2+U7"}})},
                                                {"eksenler": "bozuk"}]
        self.assertEqual(hp.yaklasma_geo_history(recs), ["G2", "G3", "G4"])
        self.assertIsNone(hp.yaklasma_geo_history(None))
        got = {hp.yaklasma_choose_geo(["G2", "G3", "G4"], random.Random(s)) for s in range(40)}
        self.assertEqual(got, {"G1", "G5"})
        self.assertEqual({hp.yaklasma_choose_geo([], random.Random(s)) for s in range(60)}, {"G2", "G3", "G4", "G5"})

    def test_geo_from_notion_loader(self):
        recs = [{"eksenler": json.dumps({"event": FT, "axes": {"mod": "yaklasma", "cografya": g}})}
                for g in ("G5", "G2", "G4")]
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            d = gen("tree_street", axes_loader=lambda dom: recs)
            self.assertIn(d["structure"]["approach"]["geo"], ("G1", "G3"))
            self.assertEqual(json.loads(d["axes_json"])["axes"]["cografya"], d["structure"]["approach"]["geo"])

    def test_mid_final_lru(self):
        spot = es.FIRE_TOR_ENVS["forest_edge"]["spots"][1].lower()

        def combo(tag):
            return f"fire_disasters|none|{FT.lower()}|{spot}##{tag}|bystander_handheld"
        reset()
        hist = [combo("O1+Y2"), combo("O2+Y3"), combo("T4+U11"), combo("O3+Y4"), combo("O4+Y2")]
        self.assertEqual(hp.yaklasma_choose_mid(FT, hist, random.Random(1)), "O5")
        self.assertEqual(hp.yaklasma_choose_final(FT, hist, random.Random(1), mid="O5"), "Y1")
        # yasak çift: O1/O4 ile Y1 aday değil
        for s in range(30):
            self.assertNotEqual(hp.yaklasma_choose_final(FT, [], random.Random(s), mid="O1"), "Y1")
            self.assertNotEqual(hp.yaklasma_choose_final(FT, [], random.Random(s), mid="O4"), "Y1")
        # art arda 5 üretim: 5 farklı orta
        reset()
        mids = []
        for seed in range(5):
            random.seed(seed)
            mids.append(gen("forest_edge")["structure"]["approach"]["mid"])
        self.assertEqual(sorted(mids), ["O1", "O2", "O3", "O4", "O5"])
        self.assertTrue(all(t.startswith("O") and "+Y" in t for t in es._BEAT_MEMORY[FT][-5:]))

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
        for bad in ({"final": "U11"}, {"mid": "T4"}, {"geo": "G9"}, {"mid": "O1", "final": "Y1"}):
            self.assertTrue(cp.submit_issues({**st, "approach": {**st["approach"], **bad}}, info), bad)
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])

    def test_approval_lines(self):
        for seed in range(1, 40):
            d = build("village_woods", seed)
            if d["structure"]["approach"]["mid"] == "O5":
                break
        sc, st = d["scenes"][0], d["structure"]
        ap = st["approach"]
        self.assertEqual(ap["mid"], "O5")
        lines = ap["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kalıbı · Yaklaşma")
        self.assertEqual(lines[1], f"Coğrafya: {ap['geo']} {YK['geos'][ap['geo']]['name']}")
        self.assertEqual(lines[2], "Ortam: köy kenarı, çevresi orman (village_woods)")
        self.assertTrue(lines[3].startswith("Orta (4-9s): O5 «Halfway down the road, "))
        self.assertTrue(lines[4].startswith(f"Final (9-15s): {ap['final']} «Right below the terrace"))
        self.assertEqual(lines[5], "Kamera: takip (yaklaşan hortumu yavaşça takip eder)")
        self.assertEqual(lines[6], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                   f"{len(sc['prompt'])} (en fazla 1400)")
        self.assertEqual(lines[7], "Hortum tarifi: yan görünüm (v2)")
        self.assertEqual(lines[8], "⚠️ Araç savurma ortası (O5): videoda aracın tek parça kalıp kalmadığını kontrol et.")
        _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"],
                                       "style_suffix": sc["style_suffix"], "hit_lines": ap["lines"],
                                       "environment": st["environment"]})
        self.assertIn("\nMod: ⭐ Hit kalıbı · Yaklaşma\n", body)
        self.assertIn("\n\n" + sc["prompt"], body)
        axes = json.loads(d["axes_json"])["axes"]
        self.assertEqual((axes["beats"], axes["mod"], axes["cografya"]),
                         (f"{ap['mid']}+{ap['final']}", "yaklasma", ap["geo"]))

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
        reset()
        random.seed(5)
        d = asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": FT, "used_combos": [],
                                                     "recent_topics": []}))
        self.assertNotIn("approach", d["structure"])
        for x in ("Halfway down the", "Right below the terrace", ACTION, "Seen from the side", O5_TEXT):
            self.assertNotIn(x, d["scenes"][0]["prompt"])


class TestYaklasmaPipeline(_Quiet):
    def test_pipeline_passes_approach_env_and_sends_prompt(self):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        seen = {}

        async def fake_gen(config):
            seen["config"] = dict(config)
            reset()
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
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=FT)
        finally:
            t.doCleanups()
        self.assertTrue(r["success"], r)
        self.assertEqual(seen["config"]["approach_env"], "tree_street")
        self.assertNotIn("hit_env", seen["config"])
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)   # Kie gönderimi Onay'a bağlı
        info = approve[0]
        self.assertTrue(info["prompt"].endswith(hp.yaklasma_tail("tree_street")))
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı · Yaklaşma\nCoğrafya: G"))
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
        self.assertIn("Hortum tarifi: yan görünüm (v2)", text)
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
