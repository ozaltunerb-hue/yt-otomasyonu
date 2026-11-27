# 27 Kas 2026, Bahadır: yeni kategori "💧 Baraj", tek olay "Baraj yıkılır" (core/hit_prompts.py BARAJ_*), kod hikâye v1.
# Hikâyeyi GPT değil kod yazar (birebir). Prompt = AÇILIŞ + ORTA + FİNAL + STİL EKİ; metinler talimattan birebir
# (aşağıda bağımsız kopya, bayt bayt karşılaştırılır). Coğrafya B1-B6 (menü; 🎲 Rastgele'de son 2 elenir), orta M1/M2
# (son 1), final F1-F3 (son 1). Preflight danışman (senaryo yeniden yazılmaz). Ağ yok, Kie yok, GPT yok.
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
from core.trace_format import format_final_prompt, format_generation, sections_to_text   # noqa: E402

EVENT = "Dam wall bursts above a town"
DOMAIN = "dam_disasters"
CATEGORY = "💧 Baraj"
EVENT_LABEL = "💧 Baraj yıkılır"
SPOT = "rooftop terrace of a house in the town"
VERSION_LINE = "Sürüm: baraj v1 (kod hikâye: çatı terası, baraj üst yarıda + coğrafya menüsü)"
CHECK_QUESTION = ("baraj ilk kareden kadrajın üst yarısında mı, sokakta koşan insanlar var mı, kamera terasta sabit "
                  "mi, su çamurlu kahverengi ve gerçekçi mi?")

# ── Talimat metinleri, birebir (KİLİT) ──
OPENING = ("0-4s: Behind {coğrafya}, a towering concrete dam fills the upper half of the frame; jets of water burst "
           "from long cracks across its wall while people run down the street below. ")
MIDS = {
    "M1": "4-9s: A huge section of the dam wall breaks away and a wall of water bursts out and rushes down toward the "
          "houses. ",
    "M2": "4-9s: Giant concrete blocks tumble from the dam as its center gives way and a wall of water bursts out "
          "toward the houses. ",
}
FINALS = {
    "F1": "9-15s: The water slams into the first houses and sweeps the parked cars down the street.",
    "F2": "9-15s: The water hits the street and sweeps a bus along, tipping it onto its side.",
    "F3": "9-15s: The water tears a house from its foundation and carries it down the street.",
}
STYLE = (" Handheld footage shot by a person standing on the rooftop terrace of a house in the town, high vantage "
         "looking toward the dam; slight hand shake, the camera stays fixed on the terrace, never descending, the dam "
         "always visible in the upper half of the frame, a corner of the terrace railing in the foreground; one "
         "continuous shot, no zoom, no cuts. Real dam-break footage: muddy brown water, broken concrete, never glossy "
         "or CGI; no explosions, no fire. Bystanders wear civilian clothes. No readable signs, text or flags. "
         "Everything moves in real time, people run at full speed.")
PLACES = {
    "B1": "a small mountain town in the Swiss Alps",
    "B2": "a small town in a Norwegian valley",
    "B3": "a small mountain town in Japan",
    "B4": "a small Andean town in Colombia",
    "B5": "a small mountain town in Austria",
    "B6": "a small valley town in Chile",
}
NAMES = {"B1": "İsviçre", "B2": "Norveç", "B3": "Japonya", "B4": "Kolombiya", "B5": "Avusturya", "B6": "Şili"}
GEOS = tuple(PLACES)
FORBIDDEN = ("explosion", "explode", "fire", "flames", "slowly", "calm")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "baraj_v1_runs_40.json")
BARAJ_SHA256 = "2546cb5ebd89229f3087070eb09e7b591b5511f73459423062f21be7bce28643"   # 40 tohum (🎲 Rastgele)


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
    with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
        return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": EVENT, "baraj": True,
                                                         "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int, **extra) -> dict:
    reset()
    random.seed(seed)
    return gen(**extra)


def expected(g: str, m: str, f: str) -> str:
    return OPENING.replace("{coğrafya}", PLACES[g]) + MIDS[m] + FINALS[f] + STYLE


def combos():
    return [(g, m, f) for g in GEOS for m in MIDS for f in FINALS]


def snapshot_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def baraj_snapshot() -> dict:
    """40 tohum (🎲 Rastgele): prompt, hikâye, stil eki, combo, eksenler (caption hariç)."""
    runs = {}
    for s in range(1, 41):
        d = build(s)
        sc = d["scenes"][0]
        axes = json.loads(d["axes_json"])
        axes.pop("caption", None)
        runs[str(s)] = {"prompt": sc["prompt"], "story": sc["story"], "suffix": sc["style_suffix"],
                        "combo": d["combo_key"], "axes": axes}
    return runs


class TestLockedTexts(_Quiet):
    def test_locked_sentences_byte_identical(self):
        self.assertEqual(hp.BARAJ_OPENING.replace("{place}", "{coğrafya}").encode("utf-8"), OPENING.encode("utf-8"))
        for k, v in MIDS.items():
            self.assertEqual(hp.BARAJ_MIDS[k].encode("utf-8"), v.encode("utf-8"), k)
        for k, v in FINALS.items():
            self.assertEqual(hp.BARAJ_FINALS[k].encode("utf-8"), v.encode("utf-8"), k)
        self.assertEqual(hp.BARAJ_STYLE.encode("utf-8"), STYLE.encode("utf-8"))
        self.assertEqual(list(hp.BARAJ_MIDS), ["M1", "M2"])
        self.assertEqual(list(hp.BARAJ_FINALS), ["F1", "F2", "F3"])
        self.assertEqual(hp.baraj_tail().encode("utf-8"), STYLE[1:].encode("utf-8"))

    def test_geo_menu_verbatim(self):
        self.assertEqual({g: v["place"] for g, v in hp.BARAJ_GEOS.items()}, PLACES)
        self.assertEqual({g: v["name"] for g, v in hp.BARAJ_GEOS.items()}, NAMES)
        self.assertEqual(list(hp.BARAJ_GEO_BUTTONS), list(GEOS))
        for g, label in hp.BARAJ_GEO_BUTTONS.items():
            self.assertIn(NAMES[g], label)
        self.assertEqual((hp.BARAJ_GEO_BLOCK, hp.BARAJ_MID_BLOCK, hp.BARAJ_FINAL_BLOCK), (2, 1, 1))

    def test_every_prompt_is_plain_concatenation(self):
        for g, m, f in combos():
            p = hp.baraj_prompt(g, m, f)
            self.assertEqual(p.encode("utf-8"), expected(g, m, f).encode("utf-8"), (g, m, f))
            story = hp.baraj_story(g, m, f)
            from core.creative_engine import join_story_and_style
            self.assertEqual(join_story_and_style(story, hp.baraj_tail()), p)   # Kie istemcisinin birleştirmesi
            self.assertTrue(p.startswith("0-4s: Behind " + PLACES[g] + ", "))
            self.assertEqual(sum(pl in p for pl in PLACES.values()), 1)

    def test_forbidden_words_outside_style(self):
        texts = [OPENING, *MIDS.values(), *FINALS.values(), *PLACES.values()]
        for t in texts:
            for bad in FORBIDDEN:
                self.assertNotIn(bad, t.lower(), (bad, t))
        for g, m, f in combos():
            body = hp.baraj_story(g, m, f).lower()
            for bad in FORBIDDEN:
                self.assertNotIn(bad, body, (g, m, f, bad))
        self.assertEqual(hp.BARAJ_FORBIDDEN, FORBIDDEN)
        # stil ekindeki olumsuzlama ("no explosions, no fire") yasak sayılmaz
        p = hp.baraj_prompt("B1", "M1", "F1")
        self.assertEqual(hp.baraj_text_issues(p, "B1"), [])
        for bad in FORBIDDEN:
            out = hp.baraj_text_issues(p.replace("4-9s: ", f"4-9s: {bad.upper()} "), "B1")
            self.assertIn(f"bu kategoride olmayan ifade var: {bad}", out, bad)

    def test_all_36_combos_within_limits(self):
        words, chars = [], []
        for g, m, f in combos():
            p = hp.baraj_prompt(g, m, f)
            words.append(len(p.split()))
            chars.append(len(p))
            self.assertLessEqual(words[-1], 230)
            self.assertLessEqual(chars[-1], 1400)
            self.assertEqual(hp.baraj_text_issues(p, g), [])
            self.assertEqual(pg.event_fidelity_issues(EVENT, hp.baraj_story(g, m, f)), [])
            self.assertEqual(pg.event_fidelity_issues(EVENT, p), [])
        self.assertEqual(len(words), 36)
        self.assertEqual(max(zip(words, chars)), (175, 994))
        self.assertEqual(len(hp.baraj_prompt("B1", "M2", "F1").split()), 175)
        self.assertEqual(len(hp.baraj_prompt("B1", "M2", "F1")), 994)
        self.assertEqual(max(chars), 994)

    def test_unknown_ids_raise(self):
        for bad in ("B0", "B7", "b1", "G1", "Y1"):
            with self.assertRaises(es.StructureError):
                hp.baraj_prompt(bad, "M1", "F1")
        for bad in ("M3", "O1", "m1"):
            with self.assertRaises(es.StructureError):
                hp.baraj_prompt("B1", bad, "F1")
        for bad in ("F4", "F0", "F_BINA"):
            with self.assertRaises(es.StructureError):
                hp.baraj_prompt("B1", "M1", bad)

    def test_not_in_normal_pool(self):
        """Olay normal havuzda değil: rastgele domain rotasyonu ve diğer olayların snapshot'ları değişmez."""
        from core.creative_engine import DOMAIN_ATTRIBUTES
        pool = [e for a in DOMAIN_ATTRIBUTES.values() for e in a["events"]]
        self.assertTrue(pool)
        self.assertNotIn(EVENT, pool)
        self.assertNotIn(EVENT, es.EVENT_BEATS)
        self.assertFalse(es.is_structured(EVENT))
        self.assertNotIn("—", hp.BARAJ_CONFIRM_DESC + VERSION_LINE + hp.BARAJ_MODE_LABEL + hp.BARAJ_CHECK
                         + hp.BARAJ_CAMERA_LINE + "".join(hp.BARAJ_GEO_BUTTONS.values()))


class TestScene(_Quiet):
    def _check(self, d, source="rastgele"):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["baraj"]
        self.assertEqual(tb["surum"], "v1")
        self.assertEqual(tb["geo_source"], source)
        self.assertEqual(sc["prompt"], expected(tb["geo"], tb["mid"], tb["final"]))
        self.assertEqual(sc["style_suffix"], STYLE[1:])
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{EVENT.lower()}|{SPOT}##{tb['mid']}+{tb['final']}|"
                                         "bystander_handheld")
        self.assertEqual(cp.submit_issues(st, {"prompt": sc["prompt"], "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        axes = json.loads(d["axes_json"])
        self.assertEqual(axes["event"], EVENT)
        for k, v in {"mod": "baraj", "surum": "v1", "kategori": "Baraj", "olay": "Baraj yıkılır",
                     "cografya": tb["geo"], "cografya_kaynak": source, "orta": tb["mid"], "final": tb["final"],
                     "beats": f"{tb['mid']}+{tb['final']}", "spot": SPOT}.items():
            self.assertEqual(axes["axes"][k], v, k)
        self.assertEqual(d["selection"]["notion_event"], "Baraj yıkılır")
        self.assertEqual(d["selection"]["event"], EVENT)
        return tb

    def test_seeds_no_gpt_all_combos(self):
        with patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))):
            seen = {(tb["geo"], tb["mid"], tb["final"]) for s in range(1, 301) for tb in [self._check(build(s))]}
        self.assertEqual(seen, set(combos()))

    def test_random_lru(self):
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(12)]
            g = [x["geo"] for x in runs]
            for i in range(len(g)):
                self.assertNotIn(g[i], g[max(0, i - 2):i], (seed, g))
            for key in ("mid", "final"):
                v = [x[key] for x in runs]
                self.assertTrue(all(a != b for a, b in zip(v, v[1:])), (seed, key, v))

    def test_menu_geo_ignores_lru(self):
        for g in GEOS:
            reset()
            random.seed(4)
            runs = [self._check(gen(baraj_geo=g), "menü") for _ in range(6)]
            self.assertEqual({x["geo"] for x in runs}, {g})
            for key in ("mid", "final"):
                v = [x[key] for x in runs]
                self.assertTrue(all(a != b for a, b in zip(v, v[1:])), (g, key, v))
            self.assertEqual(hp._BARAJ_GEO_MEMORY, [g] * 6)
            d = gen()   # sonraki 🎲 Rastgele menü seçimini de son 2'de sayar
            self.assertNotEqual(d["structure"]["baraj"]["geo"], g)
            d = gen(baraj_geo=g)
            self.assertEqual(json.loads(d["axes_json"])["excluded"], {"cografya": []})
            self.assertIn(f"Tekrar önleme: coğrafya menüden ({g}) · orta son 1 · final son 1",
                          d["structure"]["baraj"]["lines"])
        for bad in ("B7", "G1", "b1", "r"):
            reset()
            with self.assertRaises(es.StructureError):
                hp.baraj_build_scene(DOMAIN, EVENT, geo=bad)
        with self.assertRaises(es.StructureError):
            hp.baraj_build_scene("fissure_disasters", EVENT)
        with self.assertRaises(es.StructureError):
            hp.baraj_build_scene(DOMAIN, "Earthquake fissure splits a city avenue")

    def test_history_sources(self):
        def rec(g, tag, mod="baraj", event=EVENT):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, "cografya": g, "beats": tag}})}
        recs = [rec("B3", "M2+F2"), rec("Y1", "O_BUS+F_BINA", mod="yer_yarilmasi",
                                       event="Earthquake fissure splits a city avenue"),
                {"eksenler": "x"}, rec("B1", "M2+F1"), rec("B5", "M1+F3")]
        for s in range(1, 11):
            d = build(s, axes_loader=lambda dom: recs)
            tb = self._check(d)
            self.assertNotIn(tb["geo"], ("B1", "B5"))   # son 2 B elenir
            self.assertEqual(tb["mid"], "M2")
            self.assertIn(tb["final"], ("F1", "F2"))
            self.assertEqual(d["trace"]["axes_source"], "notion")
            tb = self._check(build(s, axes_loader=lambda dom: recs, baraj_geo="B5"), "menü")
            self.assertEqual((tb["geo"], tb["mid"]), ("B5", "M2"))
        self.assertEqual(hp.baraj_tags(["O1+F1", "M1+F2", "O_BUS+F_BINA", "M2+F3"]), ["M1+F2", "M2+F3"])

        def broken(dom):
            raise RuntimeError("Notion yok")
        self.assertEqual(build(3, axes_loader=broken)["trace"]["axes_source"], "bellek")

    def test_kie_final_check(self):
        for s in range(1, 13):
            d = build(s)
            sc, st = d["scenes"][0], d["structure"]
            tb = st["baraj"]
            info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
            for need in hp.BARAJ_REQUIRED:
                bad = sc["prompt"].replace(need, "x")
                self.assertIn(f'"{need}" eksik', hp.baraj_text_issues(bad, tb["geo"]))
                self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad}), need)
            for bad in FORBIDDEN:
                self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"] + f" {bad.upper()}."}), bad)
            for bad in ({"geo": "B7"}, {"mid": "M3"}, {"final": "F4"}):
                self.assertTrue(cp.submit_issues({**st, "baraj": {**tb, **bad}}, info), bad)
            self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": "x"}))
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"].replace("4-9s: ", "")}))
            other = next(g for g in GEOS if g != tb["geo"])
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"].replace(PLACES[tb["geo"]],
                                                                                          PLACES[other])}))
            # preflight danışman: Kie reddinde de hikâye yeniden yazılmaz (GPT çağrısı yok)
            story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
            self.assertEqual(story, sc["story"])

    def test_approval_lines(self):
        for s in range(1, 21):
            geo = None if s % 2 else "B4"
            d = build(s, baraj_geo=geo)
            sc, st = d["scenes"][0], d["structure"]
            tb = st["baraj"]
            lines = tb["lines"].split("\n")
            self.assertEqual(lines[0], "Mod: Baraj · kod hikâye (v1)")
            self.assertEqual(lines[1], VERSION_LINE)
            self.assertEqual(lines[2], f"Coğrafya: {tb['geo']} {NAMES[tb['geo']]} «{PLACES[tb['geo']]}» "
                                       f"({'menü' if geo else 'rastgele'})")
            self.assertEqual(lines[3], f"Orta (4-9s): {tb['mid']} «{MIDS[tb['mid']][6:-1]}»")
            self.assertEqual(lines[4], f"Final (9-15s): {tb['final']} «{FINALS[tb['final']][7:]}»")
            self.assertEqual(lines[5], hp.BARAJ_CAMERA_LINE)
            self.assertEqual(lines[6], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                       f"{len(sc['prompt'])} (en fazla 1400)")
            self.assertTrue(lines[-1].endswith(CHECK_QUESTION), lines[-1])
            self.assertNotIn("Hit karşılaştırma", tb["lines"])
            shown = sections_to_text(format_generation(d["trace"], {"domain": CATEGORY, "event": EVENT_LABEL}))
            _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"],
                                           "style_suffix": sc["style_suffix"], "hit_lines": tb["lines"],
                                           "story_source": st["story_source"], "axes_line": st["axes_line"]})
            self.assertIn("\n\n" + sc["prompt"], body)
            self.assertIn(VERSION_LINE, body)
            for text in (tb["lines"], shown, body):
                for empty in ("Araç:", "None", "kişi aralığı", "?-?", "kişi="):
                    self.assertNotIn(empty, text, (empty, text[:200]))

    def test_caption(self):
        for s in range(1, 11):
            d = build(s)
            self.assertEqual(d["caption"]["category"], "Baraj")
            self.assertEqual(len(d["caption"]["hashtags"]), 5)
            self.assertTrue(d["youtube_title"].endswith(" #Shorts"))


class TestPipelineAndBot(_Quiet):
    def test_pipeline_passes_geo_and_notion_fields(self):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        for geo in (None, "B6"):
            seen = {}

            async def fake_gen(config):
                seen["config"] = dict(config)
                reset()
                random.seed(21)
                return await pg.generate_creative_prompts({k: v for k, v in config.items()
                                                           if k not in ("axes_loader", "caption_loader")})
            t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
            t.setUp()
            try:
                rep = _Reporter(approve=True, needs_approval=True)
                orig = main.run_pipeline

                async def run_with(**kw):
                    return await orig(**{**kw, "domain": DOMAIN}, baraj=True, baraj_geo=geo)
                with patch.object(main, "run_pipeline", run_with):
                    r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=EVENT)
            finally:
                t.doCleanups()
            self.assertTrue(r["success"], r)
            self.assertTrue(seen["config"]["baraj"])
            self.assertEqual(seen["config"].get("baraj_geo"), geo)
            info = [c[1] for c in rep.calls if c[0] == "approve"][0]
            self.assertTrue(info["hit_lines"].startswith(f"Mod: Baraj · kod hikâye (v1)\n{VERSION_LINE}\nCoğrafya: "
                                                         f"{geo or 'B'}"))
            sent = t.create.await_args.args[1]
            self.assertEqual(sent, info["prompt"])
            self.assertTrue(sent.endswith(STYLE))
            if geo:
                self.assertIn(PLACES[geo], sent)
            # Notion: üretim kaydı Olay "Baraj yıkılır", Eksenler kategori "Baraj" + coğrafya/orta/final
            rfp, rax = t.tracker.record_final_prompt, t.tracker.record_axes
            selection = rfp.call_args.args[1]
            self.assertEqual(selection["notion_event"], "Baraj yıkılır")
            axes = json.loads(rax.call_args.args[0])["axes"]
            self.assertEqual((axes["kategori"], axes["olay"]), ("Baraj", "Baraj yıkılır"))
            for k in ("cografya", "orta", "final"):
                self.assertTrue(axes[k], k)

    def test_notion_olay_field(self):
        from infrastructure.notion_logger import NotionTracker
        tr = NotionTracker.__new__(NotionTracker)
        sent = {}
        tr._patch = lambda props: sent.update(props)
        tr.record_final_prompt("p", {"event": EVENT, "notion_event": "Baraj yıkılır", "camera": "c"}, "abc")
        self.assertEqual(sent["Olay"]["rich_text"][0]["text"]["content"], "Baraj yıkılır")
        sent.clear()
        tr.record_final_prompt("p", {"event": "Flash flooding in city streets", "camera": "c"}, "abc")   # diğerleri aynı
        self.assertEqual(sent["Olay"]["rich_text"][0]["text"]["content"], "Flash flooding in city streets")

    def _cb(self, data, runner=None):
        import bot
        from test_tur29_infra import _context, _update
        upd = _update(data=data)
        with patch.object(bot.pipeline, "run_pipeline", runner or AsyncMock(side_effect=AssertionError("üretim"))), \
             patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, _context()))
        return upd.callback_query.edit_message_text.await_args

    @staticmethod
    def _buttons(call):
        return [(b.text, b.callback_data) for r in call.kwargs["reply_markup"].inline_keyboard for b in r]

    def test_menu_flow(self):
        import bot
        buttons = hp.BARAJ_GEO_BUTTONS
        kb = bot.domain_keyboard(bot.default_cfg())
        texts = [b.text for r in kb.inline_keyboard for b in r]
        self.assertEqual(texts.count(CATEGORY), 1)
        row = next(r for r in kb.inline_keyboard if r[0].text == CATEGORY)
        self.assertEqual((len(row), row[0].callback_data), (1, "uret:bj"))
        self.assertEqual(bot.CODE_DOMAIN_LABELS[DOMAIN], CATEGORY)
        self.assertEqual(bot.CODE_EVENT_LABELS[EVENT], EVENT_LABEL)
        self.assertEqual(self._buttons(self._cb("uret:bj")), [(EVENT_LABEL, "uret:bje"), ("🔙 Geri", "uret:back")])
        self.assertEqual(self._buttons(self._cb("uret:bje")),
                         [(buttons[g], f"uret:bjg:{g}") for g in GEOS]
                         + [(bot.RANDOM_LABEL, f"uret:bjg:{bot.RANDOM_ID}"), ("🔙 Geri", "uret:bj")])
        for gid in GEOS + (bot.RANDOM_ID,):
            call = self._cb(f"uret:bjg:{gid}")
            self.assertEqual(self._buttons(call), [("✅ Üret", f"uret:bjok:{gid}"), ("❌ İptal", "uret:x")])
            text = call.args[0]
            for part in (f"Kategori: {CATEGORY}", f"Olay: {EVENT_LABEL}", VERSION_LINE, hp.BARAJ_CAMERA_LINE,
                         hp.BARAJ_CONFIRM_DESC, "Coğrafya: " +
                         (f"{gid} {buttons[gid]}" if gid in buttons else "🎲 Rastgele (son 2 coğrafya elenir)")):
                self.assertIn(part, text)
            self.assertNotIn("—", text)
            runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
            self._cb(f"uret:bjok:{gid}", runner)
            kw = runner.await_args.kwargs
            self.assertEqual((kw["domain"], kw["event"], kw["baraj"]), (DOMAIN, EVENT, True))
            self.assertEqual(kw.get("baraj_geo"), gid if gid in buttons else None)
            self.assertTrue(kw["reporter"].needs_approval)
            for other in ("kasirga", "yer_yarilmasi", "yer_yarilmasi_geo", "hit_kopya_kul", "donma_firtina"):
                self.assertNotIn(other, kw)
        for bad in ("uret:bj:1", "uret:bje:0", "uret:bjok", "uret:bjok:x", "uret:bjg", "uret:bjg:G1",
                    "uret:bjok:Y1", "uret:bjg:B7", "uret:bjg:B1:B2"):
            self.assertIn("Geçersiz", self._cb(bad).args[0], bad)
        for b in (b for m in (kb, bot.baraj_geo_keyboard(), bot.baraj_produce_keyboard())
                  for r in m.inline_keyboard for b in r):
            self.assertLessEqual(len(b.callback_data.encode()), 64)

    def test_callback_actions_unique(self):
        import inspect
        import bot
        body = inspect.getsource(bot.on_callback)
        for a in ("bj", "bje", "bjg", "bjok"):
            hits = [ln for ln in body.split("\n") if ln.startswith("    if action") and f'"{a}"' in ln]
            self.assertEqual(len(hits), 1, (a, hits))
            self.assertIn("Baraj", hits[0])


class TestSnapshot(_Quiet):
    def test_baraj_40_seeds_lock(self):
        snap = baraj_snapshot()
        with open(FIXTURE, encoding="utf-8") as fh:
            self.assertEqual(snap, json.load(fh))
        self.assertEqual(snapshot_hash(snap), BARAJ_SHA256)


if __name__ == "__main__":
    unittest.main()
