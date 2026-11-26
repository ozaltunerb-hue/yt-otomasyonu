# 26 Kas 2026, Bahadır: 🌍 Yer yarılması v6 = HİT KOPYASI (AKTİF). Temel: 18 Kas hiti (production DB, 17 Kas 23:20,
# commit e0ca7fd, G5 Santiago + O3 otobüs + F3 köşe binası). Açılış, kamera, stil eki, O_BUS ve F_BINA hit prompt'uyla
# bayt bayt aynı; yeni Y1-Y6 coğrafya, O_TRAM (yalnız Y2/Y4), F_GECIT. v4 ve v5 pasif (config "yer_yarilmasi_surum").
# Ağ yok, Kie yok, GPT yok.
import asyncio
import json
import os
import random
import sys
import unittest
from unittest.mock import AsyncMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

import test_yer_yarilmasi as ty   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.hit_prompts as hp   # noqa: E402
import core.prompt_generator as pg   # noqa: E402
from core.trace_format import format_final_prompt, format_generation, sections_to_text   # noqa: E402

EVENT, DOMAIN, CAMERA_LINE = ty.EVENT, ty.DOMAIN, ty.CAMERA_LINE

# 18 Kas hit prompt'u (e0ca7fd'de koddan kurulan G5+O3+F3), elle kopya, birebir
HIT_PLACE = "a busy avenue of Santiago with the Andes rising behind it"
HIT_OPENING = ("From the very first frame a busy avenue of Santiago with the Andes rising behind it is breaking apart: "
               "a wide, jagged earthquake fissure cuts across the street from left to right in front of the camera, "
               "asphalt slabs dropping into it as it keeps widening. People sprint away from its edges.")
HIT_MID = ("A city bus brakes at the edge, tilts sideways and topples into the fissure in a burst of dust as more road "
           "breaks off.")
HIT_FINAL = "The corner building on the far edge, big in frame, tilts and collapses into the fissure in a roar of dust."
HIT_STYLE = ("Handheld footage shot by a person standing on the rooftop terrace of a corner building diagonally across "
             "the street, normal lens; slight hand shake, the camera stays fixed on the fissure, shaking with the "
             "quake; no zoom, no cuts. The terrace railing stays at the bottom of the frame the whole time; the camera "
             "never moves forward or tilts down into the fissure. The ground keeps shaking and the fissure keeps "
             "widening the whole time, never a calm moment. Real earthquake footage: irregular broken asphalt, soil "
             "and rock, never thin drawn cracks, never glossy or CGI; no lava, no fire, no glowing light, no "
             "explosions. No readable signs or text. Everything moves in real time, never in slow motion, people run "
             "at full speed.")
HIT_PROMPT = f"0-4s: {HIT_OPENING} 4-9s: {HIT_MID} 9-15s: {HIT_FINAL} {HIT_STYLE}"
HIT_CAMERA = ("Handheld footage shot by a person standing on the rooftop terrace of a corner building diagonally "
              "across the street, normal lens; slight hand shake, the camera stays fixed on the fissure, shaking with "
              "the quake; no zoom, no cuts. The terrace railing stays at the bottom of the frame the whole time; the "
              "camera never moves forward or tilts down into the fissure.")

# Talimat metinleri, birebir
PLACES = {
    "Y1": "a busy avenue of Mexico City with the Popocatépetl volcano rising behind it",
    "Y2": "a busy avenue of Lisbon with tram tracks and red-roofed hills rising behind it",
    "Y3": "a busy avenue of Naples with Mount Vesuvius rising behind it",
    "Y4": "a busy avenue of Zurich with tram tracks and the Alps rising behind it",
    "Y5": "a busy avenue of Vancouver with snow-capped mountains rising behind it",
    "Y6": "a busy avenue of Cape Town with Table Mountain rising behind it",
}
GEOS = tuple(PLACES)
TRAM_GEOS = ("Y2", "Y4")
O_BUS = HIT_MID
O_TRAM = ("A tram brakes at the edge, tilts sideways and topples into the fissure in a burst of dust as more road "
          "breaks off.")
FINALS = {
    "F_BINA": HIT_FINAL,
    "F_GECIT": "The pedestrian overpass on the far edge, big in frame, snaps and collapses into the fissure in a roar "
               "of dust.",
}
BEAT_FORBIDDEN = ("parked along the curb", "slide sideways", "delivery truck", "glass towers")
MODE_LABEL = "Yer yarılması · kod hikâye (v6: hit kopyası)"
VERSION_LINE = "Sürüm: yer_yar v6 (hit kopyası: 18 Kas hit promptu birebir + yeni coğrafya + tramvay/üst geçit)"
V6_SHA256 = "a39113746ca73560a520d755823e67ed67e183f1fd85809723209a8f33be2375"   # 40 tohum (🎲 Rastgele)
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "yer_yarilmasi_v6_runs_40.json")


def mids_for(g: str) -> dict:
    return {"O_BUS": O_BUS, **({"O_TRAM": O_TRAM} if g in TRAM_GEOS else {})}


def gen(**extra) -> dict:
    with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
        return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": EVENT, "yer_yarilmasi": True,
                                                         "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int, **extra) -> dict:
    ty.reset()
    random.seed(seed)
    return gen(**extra)


def expected(g: str, m: str, f: str) -> str:
    return (f"0-4s: {HIT_OPENING.replace(HIT_PLACE, PLACES[g])} 4-9s: {mids_for(g)[m]} 9-15s: {FINALS[f]} "
            f"{HIT_STYLE}")


def combos():
    return [(g, m, f) for g in GEOS for m in mids_for(g) for f in FINALS]


def v6_snapshot() -> dict:
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


class TestHitTexts(ty._Quiet):
    def test_hit_prompt_is_v4_g5_o3_f3(self):
        """Elle kopya hit prompt'u = pasif v4 kalıbının G5+O3+F3 çıktısı (e0ca7fd'den beri değişmedi)."""
        self.assertEqual(hp.yer_yarilmasi_prompt("G5", "O3", "F3").encode("utf-8"), HIT_PROMPT.encode("utf-8"))
        self.assertEqual((len(HIT_PROMPT.split()), len(HIT_PROMPT)), (224, 1259))

    def test_opening_camera_style_bus_building_byte_identical(self):
        hit_open = HIT_PROMPT.split(" 4-9s: ")[0]
        for g, m, f in combos():
            p = hp.yer_yarilmasi_v6_prompt(g, m, f)
            opening, rest = p.split(" 4-9s: ")
            self.assertEqual(opening.replace(PLACES[g], HIT_PLACE).encode("utf-8"), hit_open.encode("utf-8"))
            self.assertTrue(p.endswith(" " + HIT_STYLE))
            self.assertIn(HIT_CAMERA, p)
            mid, final_style = rest.split(" 9-15s: ")
            if m == "O_BUS":
                self.assertEqual(mid.encode("utf-8"), HIT_MID.encode("utf-8"))
            if f == "F_BINA":
                self.assertEqual(final_style.encode("utf-8"), (HIT_FINAL + " " + HIT_STYLE).encode("utf-8"))
            if (m, f) == ("O_BUS", "F_BINA"):   # coğrafya dışında hit prompt'u birebir
                self.assertEqual(p.replace(PLACES[g], HIT_PLACE).encode("utf-8"), HIT_PROMPT.encode("utf-8"))
        self.assertEqual(hp.yer_yarilmasi_tail().encode("utf-8"), HIT_STYLE.encode("utf-8"))
        self.assertEqual(hp.YER_YARILMASI_V6_MIDS["O_BUS"].encode("utf-8"), HIT_MID.encode("utf-8"))
        self.assertEqual(hp.YER_YARILMASI_V6_FINALS["F_BINA"].encode("utf-8"), HIT_FINAL.encode("utf-8"))

    def test_pools_verbatim(self):
        self.assertEqual({g: v["place"] for g, v in hp.YER_YARILMASI_V6_GEOS.items()}, PLACES)
        self.assertEqual(hp.YER_YARILMASI_V6_MIDS, {"O_BUS": O_BUS})
        self.assertEqual(hp.YER_YARILMASI_V6_TRAM_MIDS, {"O_TRAM": O_TRAM})
        self.assertEqual(hp.YER_YARILMASI_V6_FINALS, FINALS)
        self.assertEqual(hp.YER_YARILMASI_V6_MODE_LABEL, MODE_LABEL)
        self.assertEqual(hp.YER_YARILMASI_V6_VERSION_LINE, VERSION_LINE)
        self.assertEqual(list(hp.YER_YARILMASI_V6_GEO_BUTTONS), list(GEOS))
        self.assertNotIn("—", hp.YER_YARILMASI_V6_CONFIRM_DESC + VERSION_LINE + MODE_LABEL
                         + "".join(hp.YER_YARILMASI_V6_GEO_BUTTONS.values()))
        # pasif: v4 G1-G6 (hitin Santiago'su dahil), v5 M1/M2/M3, F1/F2 ve v4 O3/F3 kimlikleri v6'da seçilemez
        for bad in ("G1", "G5", "Y7", "y1"):
            with self.assertRaises(es.StructureError):
                hp.yer_yarilmasi_v6_prompt(bad, "O_BUS", "F_BINA")
        for g in GEOS:
            for bad in ("O3", "M1", "M2", "M3", "O_TRUCK"):
                with self.assertRaises(es.StructureError):
                    hp.yer_yarilmasi_v6_prompt(g, bad, "F_BINA")
            for bad in ("F1", "F2", "F3"):
                with self.assertRaises(es.StructureError):
                    hp.yer_yarilmasi_v6_prompt(g, "O_BUS", bad)
        # v4 ve v5 silinmedi
        self.assertEqual(list(hp.YER_YARILMASI["mids"]), ["O3"])
        self.assertEqual(list(hp.YER_YARILMASI["finals"]), ["F3"])
        self.assertEqual(list(hp.YER_YARILMASI_V5_MIDS), ["M1", "M2"])
        self.assertEqual(list(hp.YER_YARILMASI_V5_FINALS), ["F1", "F2"])

    def test_forbidden_beat_phrases(self):
        texts = [*hp.YER_YARILMASI_V6_MIDS.values(), *hp.YER_YARILMASI_V6_TRAM_MIDS.values(),
                 *hp.YER_YARILMASI_V6_FINALS.values()]
        for t in texts:
            for bad in BEAT_FORBIDDEN:
                self.assertNotIn(bad, t.lower())
        for g, m, f in combos():
            p = hp.yer_yarilmasi_v6_prompt(g, m, f).lower()
            for bad in BEAT_FORBIDDEN:
                self.assertNotIn(bad, p, (g, m, f))
        for bad in BEAT_FORBIDDEN:
            self.assertIn(bad, hp.YER_YARILMASI_V6_FORBIDDEN)

    def test_tram_only_in_y2_y4(self):
        self.assertEqual(hp.YER_YARILMASI_V6_TRAM_GEOS, TRAM_GEOS)
        self.assertEqual([g for g, v in PLACES.items() if "tram tracks" in v], list(TRAM_GEOS))
        for g in GEOS:
            self.assertEqual(set(hp.yer_yarilmasi_v6_mids(g)), set(mids_for(g)), g)
            if g not in TRAM_GEOS:
                with self.assertRaises(es.StructureError):
                    hp.yer_yarilmasi_v6_prompt(g, "O_TRAM", "F_BINA")
        seen = {}
        for s in range(1, 121):
            tb = build(s)["structure"]["yer_yarilmasi"]
            seen.setdefault(tb["geo"], set()).add(tb["mid"])
        for g in GEOS:
            self.assertEqual(seen[g], set(mids_for(g)), g)

    def test_big_in_frame_in_both_finals(self):
        for f, t in hp.YER_YARILMASI_V6_FINALS.items():
            self.assertIn("big in frame", t, f)
        self.assertIn("big in frame", hp.YER_YARILMASI_V6_REQUIRED)
        for g, m, f in combos():
            p = hp.yer_yarilmasi_v6_prompt(g, m, f)
            self.assertIn('"big in frame" eksik',
                          hp.yer_yarilmasi_v6_text_issues(p.replace("big in frame", "x"), g, m, f))

    def test_all_combos_within_limits(self):
        """4 × 1 × 2 + 2 × 2 × 2 = 16 kombinasyon ≤ 230 kelime / ≤ 1400 karakter; kapılar geçer."""
        words, chars = [], []
        for g, m, f in combos():
            p = hp.yer_yarilmasi_v6_prompt(g, m, f)
            self.assertEqual(p, expected(g, m, f))
            words.append(len(p.split()))
            chars.append(len(p))
            self.assertLessEqual(words[-1], 230)
            self.assertLessEqual(chars[-1], 1400)
            self.assertEqual(hp.yer_yarilmasi_v6_text_issues(p, g, m, f), [])
            self.assertEqual(sum(pl in p for pl in PLACES.values()), 1)
            self.assertEqual(pg.event_fidelity_issues(EVENT, hp.yer_yarilmasi_v6_story(g, m, f)), [])
            self.assertEqual(pg.event_fidelity_issues(EVENT, p), [])
        self.assertEqual(len(words), 16)
        self.assertEqual((min(words), max(words)), (224, 227))
        self.assertEqual((min(chars), max(chars)), (1262, 1284))
        self.assertEqual(max(zip(words, chars)), (227, 1284))
        self.assertEqual(len(hp.yer_yarilmasi_v6_prompt("Y2", "O_BUS", "F_GECIT").split()), 227)


class TestScene(ty._Quiet):
    def _check(self, d, source="rastgele"):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["yer_yarilmasi"]
        self.assertEqual(tb["surum"], "v6")
        self.assertEqual(tb["geo_source"], source)
        self.assertEqual(sc["prompt"], expected(tb["geo"], tb["mid"], tb["final"]))
        self.assertEqual(sc["style_suffix"], HIT_STYLE)
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{EVENT.lower()}|{ty.SPOT}##{tb['mid']}+{tb['final']}|"
                                         "bystander_handheld")
        self.assertEqual(cp.submit_issues(st, {"prompt": sc["prompt"], "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        axes = json.loads(d["axes_json"])
        self.assertEqual(axes["event"], EVENT)
        for k, v in {"mod": "yer_yarilmasi", "surum": "v6", "cografya": tb["geo"], "cografya_kaynak": source,
                     "beats": f"{tb['mid']}+{tb['final']}", "kategori": "Yer yarılması", "spot": ty.SPOT}.items():
            self.assertEqual(axes["axes"][k], v, k)
        return tb

    def test_seeds_no_gpt_all_combos(self):
        with patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))):
            seen = {(tb["geo"], tb["mid"], tb["final"]) for s in range(1, 121) for tb in [self._check(build(s))]}
        self.assertEqual(seen, set(combos()))

    def test_random_lru(self):
        for seed in range(1, 16):
            ty.reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(10)]
            g = [x["geo"] for x in runs]
            for i in range(len(g)):
                self.assertNotIn(g[i], g[max(0, i - 3):i], (seed, g))
            f = [x["final"] for x in runs]
            self.assertTrue(all(a != b for a, b in zip(f, f[1:])), (seed, f))

    def test_menu_geo_ignores_lru(self):
        for g in GEOS:
            ty.reset()
            random.seed(4)
            runs = [self._check(gen(yer_yarilmasi_geo=g), "menü") for _ in range(6)]
            self.assertEqual({x["geo"] for x in runs}, {g})
            for key in ("mid", "final") if g in TRAM_GEOS else ("final",):
                v = [x[key] for x in runs]
                self.assertTrue(all(a != b for a, b in zip(v, v[1:])), (g, key, v))
            if g not in TRAM_GEOS:
                self.assertEqual({x["mid"] for x in runs}, {"O_BUS"})
            self.assertEqual(hp._YER_YARILMASI_GEO_MEMORY, [g] * 6)
            d = gen()   # sonraki 🎲 Rastgele menü seçimini de son 3'te sayar
            self.assertNotEqual(d["structure"]["yer_yarilmasi"]["geo"], g)
            d = gen(yer_yarilmasi_geo=g)
            self.assertEqual(json.loads(d["axes_json"])["excluded"], {"cografya": []})
            mid_rep = "orta son 1" if g in TRAM_GEOS else "orta tek (O_BUS)"
            self.assertIn(f"Tekrar önleme: coğrafya menüden ({g}) · {mid_rep} · final son 1",
                          d["structure"]["yer_yarilmasi"]["lines"])
        for bad in ("G5", "Y7", "y1", "r"):
            ty.reset()
            with self.assertRaises(es.StructureError):
                hp.yer_yarilmasi_v6_build_scene(DOMAIN, EVENT, geo=bad)

    def test_history_sources(self):
        def rec(g, tag):
            return {"eksenler": json.dumps({"event": EVENT, "axes": {"mod": "yer_yarilmasi", "cografya": g,
                                                                     "beats": tag}})}
        recs = [rec("G5", "O3+F3"), rec("Y1", "M2+F2"), rec("Y2", "O_TRAM+F_GECIT"), {"eksenler": "x"},
                rec("Y4", "O_BUS+F_BINA")]
        for s in range(1, 11):
            d = build(s, axes_loader=lambda dom: recs)
            tb = self._check(d)
            self.assertIn(tb["geo"], ("Y3", "Y5", "Y6"))   # son 3 Y (Y1, Y2, Y4) elenir; G5 sayılmaz
            self.assertEqual(tb["final"], "F_GECIT")
            self.assertEqual(d["trace"]["axes_source"], "notion")
            tb = self._check(build(s, axes_loader=lambda dom: recs, yer_yarilmasi_geo="Y4"), "menü")
            self.assertEqual((tb["geo"], tb["mid"], tb["final"]), ("Y4", "O_TRAM", "F_GECIT"))
        # v1-v5 kayıtları (O3+F3, M*+F*) LRU'ya girmez
        self.assertEqual(hp.yer_yarilmasi_v6_tags(["O1+F1", "O3+F3", "M1+F2", "O_BUS+F_GECIT"]), ["O_BUS+F_GECIT"])

        def broken(dom):
            raise RuntimeError("Notion yok")
        self.assertEqual(build(3, axes_loader=broken)["trace"]["axes_source"], "bellek")

    def test_v4_v5_still_run_passive(self):
        d = build(7, yer_yarilmasi_surum="v4")
        self.assertEqual(d["structure"]["yer_yarilmasi"]["mid"], "O3")
        self.assertNotIn("surum", d["structure"]["yer_yarilmasi"])
        d = build(7, yer_yarilmasi_surum="v5")
        self.assertEqual(d["structure"]["yer_yarilmasi"]["surum"], "v5")
        self.assertIn(d["structure"]["yer_yarilmasi"]["mid"], ("M1", "M2"))

    def test_kie_final_check(self):
        for s in range(1, 13):
            d = build(s)
            sc, st = d["scenes"][0], d["structure"]
            tb = st["yer_yarilmasi"]
            info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
            needs = list(ty.REQUIRED) + [{"O_BUS": "city bus", "O_TRAM": "a tram brakes"}[tb["mid"]],
                                         {"F_BINA": "corner building on the far edge",
                                          "F_GECIT": "pedestrian overpass on the far edge"}[tb["final"]]]
            for need in needs:
                bad = sc["prompt"].replace(need, "x").replace(need.capitalize(), "x")
                self.assertIn(f'"{need}" eksik', hp.yer_yarilmasi_v6_text_issues(bad, tb["geo"], tb["mid"],
                                                                                 tb["final"]))
                self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad}), need)
            for bad in ty.FORBIDDEN + BEAT_FORBIDDEN:
                self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"] + f" {bad.upper()}."}), bad)
            for bad in ({"geo": "G5"}, {"mid": "O3"}, {"mid": "M1"}, {"final": "F3"}, {"final": "F1"}):
                self.assertTrue(cp.submit_issues({**st, "yer_yarilmasi": {**tb, **bad}}, info), bad)
            self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": "x"}))
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"].replace("4-9s: ", "")}))
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": HIT_PROMPT}))   # Santiago v6'da yok
            story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
            self.assertEqual(story, sc["story"])

    def test_approval_lines(self):
        for s in range(1, 21):
            geo = None if s % 2 else "Y2"
            d = build(s, yer_yarilmasi_geo=geo)
            sc, st = d["scenes"][0], d["structure"]
            tb = st["yer_yarilmasi"]
            lines = tb["lines"].split("\n")
            self.assertEqual(lines[0], f"Mod: {MODE_LABEL}")
            self.assertEqual(lines[1], VERSION_LINE)
            self.assertTrue(lines[2].startswith(f"Coğrafya: {tb['geo']} ") and
                            lines[2].endswith("(menü)" if geo else "(rastgele)"), lines[2])
            self.assertIn(PLACES[tb["geo"]], lines[2])
            self.assertEqual(lines[3], f"Orta (4-9s): {tb['mid']} «{mids_for(tb['geo'])[tb['mid']]}»")
            self.assertEqual(lines[4], f"Final (9-15s): {tb['final']} «{FINALS[tb['final']]}»")
            self.assertEqual(lines[5], CAMERA_LINE)
            self.assertEqual(lines[6], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                       f"{len(sc['prompt'])} (en fazla 1400)")
            self.assertEqual(lines[-1], hp.YER_YARILMASI_WARNING)
            shown = sections_to_text(format_generation(d["trace"], {"domain": ty.CATEGORY, "event": ty.EVENT_LABEL}))
            _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"],
                                           "style_suffix": sc["style_suffix"], "hit_lines": tb["lines"],
                                           "story_source": st["story_source"], "axes_line": st["axes_line"]})
            self.assertIn("\n\n" + sc["prompt"], body)
            self.assertIn(VERSION_LINE, body)
            for text in (tb["lines"], shown, body):
                self.assertNotIn("Araç:", text)
                self.assertNotIn("None", text)

    def test_caption(self):
        for s in range(1, 11):
            d = build(s)
            self.assertEqual(d["caption"]["category"], "Yer yarılması")
            self.assertEqual(len(d["caption"]["hashtags"]), 5)
            self.assertTrue(d["youtube_title"].endswith(" #Shorts"))


class TestPipelineAndBot(ty._Quiet):
    def test_pipeline_passes_geo_and_sends_prompt(self):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        for geo in (None, "Y4"):
            seen = {}

            async def fake_gen(config):
                seen["config"] = dict(config)
                ty.reset()
                random.seed(21)
                return await pg.generate_creative_prompts({k: v for k, v in config.items()
                                                           if k not in ("axes_loader", "caption_loader")})
            t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
            t.setUp()
            try:
                rep = _Reporter(approve=True, needs_approval=True)
                orig = main.run_pipeline

                async def run_with(**kw):
                    return await orig(**{**kw, "domain": DOMAIN}, yer_yarilmasi=True, yer_yarilmasi_geo=geo)
                with patch.object(main, "run_pipeline", run_with):
                    r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=EVENT)
            finally:
                t.doCleanups()
            self.assertTrue(r["success"], r)
            self.assertEqual(seen["config"].get("yer_yarilmasi_geo"), geo)
            info = [c[1] for c in rep.calls if c[0] == "approve"][0]
            self.assertTrue(info["hit_lines"].startswith(f"Mod: {MODE_LABEL}\n{VERSION_LINE}\nCoğrafya: {geo or 'Y'}"))
            sent = t.create.await_args.args[1]
            self.assertEqual(sent, info["prompt"])
            self.assertTrue(sent.endswith(HIT_STYLE))
            if geo:
                self.assertIn(PLACES[geo], sent)

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
        buttons = hp.YER_YARILMASI_V6_GEO_BUTTONS
        kb = bot.domain_keyboard(bot.default_cfg())
        texts = [b.text for r in kb.inline_keyboard for b in r]
        self.assertEqual(texts.count(ty.CATEGORY), 1)
        row = next(r for r in kb.inline_keyboard if r[0].text == ty.CATEGORY)
        self.assertEqual((len(row), row[0].callback_data), (1, "uret:yy"))
        self.assertEqual(self._buttons(self._cb("uret:yy")), [(ty.EVENT_LABEL, "uret:yye"), ("🔙 Geri", "uret:back")])
        self.assertEqual(self._buttons(self._cb("uret:yye")),
                         [(buttons[g], f"uret:yyg:{g}") for g in GEOS]
                         + [(bot.RANDOM_LABEL, f"uret:yyg:{bot.RANDOM_ID}"), ("🔙 Geri", "uret:yy")])
        for gid in GEOS + (bot.RANDOM_ID,):
            call = self._cb(f"uret:yyg:{gid}")
            self.assertEqual(self._buttons(call), [("✅ Üret", f"uret:yyok:{gid}"), ("❌ İptal", "uret:x")])
            text = call.args[0]
            for part in (f"Kategori: {ty.CATEGORY}", f"Olay: {ty.EVENT_LABEL}", f"Mod: {MODE_LABEL}", VERSION_LINE,
                         CAMERA_LINE, hp.YER_YARILMASI_V6_CONFIRM_DESC, "Coğrafya: " +
                         (f"{gid} {buttons[gid]}" if gid in buttons else "🎲 Rastgele (son 3 coğrafya elenir)")):
                self.assertIn(part, text)
            self.assertNotIn("—", text)
            runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
            self._cb(f"uret:yyok:{gid}", runner)
            kw = runner.await_args.kwargs
            self.assertEqual((kw["domain"], kw["event"], kw["yer_yarilmasi"]), (DOMAIN, EVENT, True))
            self.assertEqual(kw.get("yer_yarilmasi_geo"), gid if gid in buttons else None)
            self.assertTrue(kw["reporter"].needs_approval)
            for other in ("kasirga", "kasirga_geo", "hit_kopya_kul", "hit_kopya_kul_geo", "donma_firtina"):
                self.assertNotIn(other, kw)
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        self._cb("uret:yyok", runner)   # eski mesajdaki argümansız düğme: 🎲 Rastgele
        self.assertNotIn("yer_yarilmasi_geo", runner.await_args.kwargs)
        for bad in ("uret:yy:1", "uret:yye:0", "uret:yyok:x", "uret:yyg", "uret:yyg:G1", "uret:yyok:G5",
                    "uret:yyg:Y7", "uret:yyg:Y1:Y2"):
            self.assertIn("Geçersiz", self._cb(bad).args[0], bad)
        for b in (b for m in (kb, bot.yer_yarilmasi_geo_keyboard(), bot.yer_yarilmasi_produce_keyboard())
                  for r in m.inline_keyboard for b in r):
            self.assertLessEqual(len(b.callback_data.encode()), 64)

    def test_callback_actions_unique(self):
        import inspect
        import bot
        body = inspect.getsource(bot.on_callback)
        for a in ("yy", "yye", "yyg", "yyok"):
            hits = [ln for ln in body.split("\n") if ln.startswith("    if action in (") and f'"{a}"' in ln]
            self.assertEqual(len(hits), 1, (a, hits))
            self.assertIn("Yer yarılması", hits[0])


class TestSnapshot(ty._Quiet):
    def test_v6_40_seeds_lock(self):
        snap = v6_snapshot()
        with open(FIXTURE, encoding="utf-8") as fh:
            self.assertEqual(snap, json.load(fh))
        self.assertEqual(ty.snapshot_hash(snap), V6_SHA256)
        self.assertNotIn(V6_SHA256, (ty.YY_SHA256, ty.YY_V3_SHA256))

    def test_v5_fixture_unchanged(self):
        """v5 pasif yolu 40 tohum kilidi (config "v5") aynen."""
        import test_yer_yarilmasi_v5 as t5
        self.assertEqual(ty.snapshot_hash(t5.v5_snapshot()), t5.V5_SHA256)


if __name__ == "__main__":
    unittest.main()
