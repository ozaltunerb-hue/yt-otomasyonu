# 26 Kas 2026: v5 PASİF (aktif sürüm v6 hit kopyası: tests/test_yer_yarilmasi_v6.py). v5 kalıbı config
# "yer_yarilmasi_surum": "v5" ile aynen çalışır; bu dosya o yolu kilitler. Bot menüsü/pipeline testleri v6'ya taşındı.
# 25 Kas 2026, Bahadır: 🌍 Yer yarılması v5. Kamera, açılış, stil eki, G1-G6 ve F1 cümlesi v4 ile bayt bayt aynı;
# yeni orta havuzu M1/M2 (M3 tramvay: yer metninde tramvay geçen coğrafya yok, pasif), final F1/F2, coğrafya menüsü.
# v4 kalıbı ve 40 tohum kilidi tests/test_yer_yarilmasi.py'de. Ağ yok, Kie yok, GPT yok.
import asyncio
import copy
import json
import os
import random
import re
import sys
import unittest
from unittest.mock import AsyncMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

import test_yer_yarilmasi as ty   # noqa: E402  (v4 metinlerinin bağımsız kopyaları)
import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.hit_prompts as hp   # noqa: E402
import core.prompt_generator as pg   # noqa: E402
from core.trace_format import format_final_prompt, format_generation, sections_to_text   # noqa: E402

EVENT, DOMAIN, PLACES, STYLE, CAMERA_LINE = ty.EVENT, ty.DOMAIN, ty.PLACES, ty.STYLE, ty.CAMERA_LINE
GEOS = ("G1", "G2", "G3", "G4", "G5", "G6")
BUTTONS = {"G1": "🇺🇸 ABD Kaliforniya", "G2": "🇺🇸 ABD şehir merkezi", "G3": "🇲🇽 Meksika", "G4": "🇧🇷 Brezilya",
           "G5": "🇨🇱 Şili", "G6": "🇯🇵 Japonya"}
MODE_LABEL = "Yer yarılması · kod hikâye (v5: yeni orta havuzu + coğrafya menüsü)"
VERSION_LINE = ("Sürüm: yer_yar v5 (v4 kamera/açılış birebir + yeni orta havuzu + bina/üst geçit finali + coğrafya "
                "menüsü)")
# Talimat metinleri, birebir
MIDS = {
    "M1": "Cars parked along the curb slide sideways into the widening fissure one after another.",
    "M2": "A delivery truck brakes too late and plunges nose-first into the fissure, its rear wheels lifting into the "
          "air.",
}
M3 = "A tram derails at the edge of the fissure, tips over and slides in."
FINALS = {
    "F1": "The corner building on the far edge, big in frame, tilts and collapses into the fissure in a roar of dust.",
    "F2": "A pedestrian overpass spanning the street cracks at both ends and collapses into the fissure.",
}
V5_SHA256 = "fb7c0d5a363ba6b7d3e856ae3dd7037a4cbe112e9916352182a52f92d0c109c4"   # 40 tohum (🎲 Rastgele)
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "yer_yarilmasi_v5_runs_40.json")


def gen(**extra) -> dict:
    with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
        return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": EVENT, "yer_yarilmasi": True,
                                                         "yer_yarilmasi_surum": "v5",   # 26 Kas: aktif sürüm v6
                                                         "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int, **extra) -> dict:
    ty.reset()
    random.seed(seed)
    return gen(**extra)


def expected(g: str, m: str, f: str) -> str:
    return f"{ty.OPENING.format(place=PLACES[g])} 4-9s: {MIDS[m]} 9-15s: {FINALS[f]} {STYLE}"


def combos():
    return [(g, m, f) for g in GEOS for m in MIDS for f in FINALS]


def v5_snapshot() -> dict:
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


class TestTexts(ty._Quiet):
    def test_camera_opening_style_f1_byte_identical_to_v4(self):
        """v4 ÇIKTISI (çalışan v4 yolu, 40 tohum) ile v5 çıktısı: açılış, stil eki (kamera dahil), F1 bayt bayt aynı."""
        v4 = {}
        for s in range(1, 41):
            ty.reset()
            random.seed(s)
            d = ty.gen()
            v4.setdefault(d["structure"]["yer_yarilmasi"]["geo"], d["scenes"][0])
        self.assertEqual(set(v4), set(GEOS))
        for g, m, f in combos():
            v5 = hp.yer_yarilmasi_v5_prompt(g, m, f)
            old = v4[g]["prompt"]
            o4, rest4 = old.split(" 4-9s: ")
            o5, rest5 = v5.split(" 4-9s: ")
            self.assertEqual(o5.encode("utf-8"), o4.encode("utf-8"))
            self.assertEqual(v4[g]["style_suffix"].encode("utf-8"), STYLE.encode("utf-8"))
            self.assertTrue(v5.endswith(" " + v4[g]["style_suffix"]))
            for cam in ("Handheld footage shot by a person standing on the rooftop terrace of a corner building "
                        "diagonally across the street, normal lens; slight hand shake, the camera stays fixed on the "
                        "fissure, shaking with the quake; no zoom, no cuts. The terrace railing stays at the bottom "
                        "of the frame the whole time; the camera never moves forward or tilts down into the fissure.",
                        "no lava, no fire, no glowing light, no explosions."):
                self.assertIn(cam, old)
                self.assertIn(cam, v5)
            if f == "F1":   # final + stil = v4 finali + stili
                self.assertEqual(rest5.split(" 9-15s: ")[1].encode("utf-8"),
                                 rest4.split(" 9-15s: ")[1].encode("utf-8"))
        self.assertEqual(hp.YER_YARILMASI_V5_FINALS["F1"], hp.YER_YARILMASI["finals"]["F3"])

    def test_pools_verbatim(self):
        self.assertEqual(hp.YER_YARILMASI_V5_MIDS, MIDS)
        self.assertEqual(hp.YER_YARILMASI_V5_TRAM_MIDS, {"M3": M3})
        self.assertEqual(hp.YER_YARILMASI_V5_FINALS, FINALS)
        self.assertEqual({g: v["place"] for g, v in hp.YER_YARILMASI["geos"].items()}, PLACES)
        self.assertEqual(hp.YER_YARILMASI_V5_MODE_LABEL, MODE_LABEL)
        self.assertEqual(hp.YER_YARILMASI_V5_VERSION_LINE, VERSION_LINE)
        self.assertEqual(hp.YER_YARILMASI_GEO_BUTTONS, BUTTONS)
        # v4 silinmedi
        self.assertEqual(hp.YER_YARILMASI_MODE_LABEL, ty.MODE_LABEL)
        self.assertEqual(list(hp.YER_YARILMASI["mids"]), ["O3"])
        self.assertEqual(list(hp.YER_YARILMASI["finals"]), ["F3"])
        for bad in ("O1", "O2", "O3", "M3", "M4"):   # otobüs dahil eski ortalar + M3 (tramvaysız) istenemez
            for g in GEOS:
                with self.assertRaises(es.StructureError):
                    hp.yer_yarilmasi_v5_prompt(g, bad, "F1")
        for bad in ("F3", "F4"):
            with self.assertRaises(es.StructureError):
                hp.yer_yarilmasi_v5_prompt("G1", "M1", bad)
        self.assertNotIn("—", hp.YER_YARILMASI_V5_CONFIRM_DESC + VERSION_LINE + MODE_LABEL + "".join(BUTTONS.values()))

    def test_no_bus_in_mids_and_finals(self):
        """Orta ve finalde kelime başından "bus" yok (coğrafya metnindeki "busy" hariç)."""
        for t in [*hp.YER_YARILMASI_V5_MIDS.values(), *hp.YER_YARILMASI_V5_TRAM_MIDS.values(),
                  *hp.YER_YARILMASI_V5_FINALS.values()]:
            self.assertIsNone(re.search(r"\bbus", t, re.I), t)
        for g, m, f in combos():
            rest = hp.yer_yarilmasi_v5_prompt(g, m, f).replace(PLACES[g], "")
            self.assertIsNone(re.search(r"\bbus", rest, re.I), (g, m, f))

    def test_m3_only_in_tram_geos(self):
        self.assertEqual(hp.yer_yarilmasi_v5_tram_geos(), [])   # G1-G6 metinlerinde tramvay geçmiyor: M3 pasif
        for g in GEOS:
            self.assertNotIn("M3", hp.yer_yarilmasi_v5_mids(g))
        for s in range(1, 121):
            self.assertIn(build(s)["structure"]["yer_yarilmasi"]["mid"], MIDS)
        # kural metne bağlı: tramvaylı bir coğrafya olsaydı M3 yalnız orada seçilirdi
        fake = copy.deepcopy(hp.YER_YARILMASI["geos"])
        fake["G6"]["place"] = "a busy street with tram tracks in a Japanese city"
        with patch.dict(hp.YER_YARILMASI, {"geos": fake}):
            self.assertEqual(hp.yer_yarilmasi_v5_tram_geos(), ["G6"])
            seen = {}
            for s in range(1, 121):
                tb = build(s)["structure"]["yer_yarilmasi"]
                seen.setdefault(tb["geo"], set()).add(tb["mid"])
            self.assertEqual(seen["G6"], {"M1", "M2", "M3"})
            for g in GEOS[:5]:
                self.assertEqual(seen[g], {"M1", "M2"}, g)
        fake["G6"]["place"] = "a trampled street"   # "tram" ile başlayan başka kelime tramvay sayılmaz
        with patch.dict(hp.YER_YARILMASI, {"geos": fake}):
            self.assertEqual(hp.yer_yarilmasi_v5_tram_geos(), [])

    def test_all_combos_within_limits(self):
        """6 × 2 × 2 = 24 kombinasyon ≤ 230 kelime / ≤ 1400 karakter; zorunlular var, yasaklar yok, olay kapısı geçer."""
        words, chars = [], []
        for g, m, f in combos():
            p = hp.yer_yarilmasi_v5_prompt(g, m, f)
            self.assertEqual(p, expected(g, m, f))
            words.append(len(p.split()))
            chars.append(len(p))
            self.assertLessEqual(words[-1], 230)
            self.assertLessEqual(chars[-1], 1400)
            self.assertEqual(hp.yer_yarilmasi_v5_text_issues(p, g, f), [])
            self.assertEqual(sum(pl in p for pl in PLACES.values()), 1)
            self.assertEqual(pg.event_fidelity_issues(EVENT, hp.yer_yarilmasi_v5_story(g, m, f)), [])
            self.assertEqual(pg.event_fidelity_issues(EVENT, p), [])
        self.assertEqual(len(words), 24)
        self.assertEqual((min(words), max(words)), (206, 222))
        self.assertEqual((min(chars), max(chars)), (1211, 1273))
        # M3 bir gün açılırsa da sığar (M1 ve M2'den kısa)
        self.assertLess(len(M3.split()), len(MIDS["M2"].split()))


class TestScene(ty._Quiet):
    def _check(self, d, source="rastgele"):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["yer_yarilmasi"]
        self.assertEqual(tb["surum"], "v5")
        self.assertEqual(tb["geo_source"], source)
        self.assertEqual(sc["prompt"], expected(tb["geo"], tb["mid"], tb["final"]))
        self.assertEqual(sc["style_suffix"], STYLE)
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{EVENT.lower()}|{ty.SPOT}##{tb['mid']}+{tb['final']}|"
                                         "bystander_handheld")
        self.assertEqual(cp.submit_issues(st, {"prompt": sc["prompt"], "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        axes = json.loads(d["axes_json"])
        self.assertEqual(axes["event"], EVENT)
        for k, v in {"mod": "yer_yarilmasi", "surum": "v5", "cografya": tb["geo"], "cografya_kaynak": source,
                     "beats": f"{tb['mid']}+{tb['final']}", "kategori": "Yer yarılması", "spot": ty.SPOT}.items():
            self.assertEqual(axes["axes"][k], v, k)
        return tb

    def test_40_seeds_no_gpt(self):
        with patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))):
            seen = {(tb["geo"], tb["mid"], tb["final"]) for s in range(1, 121) for tb in [self._check(build(s))]}
        self.assertEqual(seen, set(combos()))   # 24 kombinasyonun hepsi gelir

    def test_random_lru(self):
        for seed in range(1, 16):
            ty.reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(10)]
            g = [x["geo"] for x in runs]
            for i in range(len(g)):
                self.assertNotIn(g[i], g[max(0, i - 3):i], (seed, g))
            for key in ("mid", "final"):
                v = [x[key] for x in runs]
                self.assertTrue(all(a != b for a, b in zip(v, v[1:])), (seed, key, v))

    def test_menu_geo_ignores_lru(self):
        for g in GEOS:
            ty.reset()
            random.seed(4)
            runs = [self._check(gen(yer_yarilmasi_geo=g), "menü") for _ in range(6)]
            self.assertEqual({x["geo"] for x in runs}, {g})   # son 3'te olsa da sabit
            for key in ("mid", "final"):
                v = [x[key] for x in runs]
                self.assertTrue(all(a != b for a, b in zip(v, v[1:])), (g, key, v))
            self.assertEqual(hp._YER_YARILMASI_GEO_MEMORY, [g] * 6)
            d = gen()   # sonraki 🎲 Rastgele menü seçimini de son 3'te sayar
            self.assertNotEqual(d["structure"]["yer_yarilmasi"]["geo"], g)
            d = gen(yer_yarilmasi_geo=g)
            self.assertEqual(json.loads(d["axes_json"])["excluded"], {"cografya": []})
            self.assertIn(f"Tekrar önleme: coğrafya menüden ({g}) · orta son 1 · final son 1",
                          d["structure"]["yer_yarilmasi"]["lines"])
        for bad in ("G7", "g1", "r", "V1"):
            ty.reset()
            with self.assertRaises(es.StructureError):
                hp.yer_yarilmasi_v5_build_scene(DOMAIN, EVENT, geo=bad)

    def test_none_geo_equals_random(self):
        for s in range(1, 11):
            self.assertEqual(build(s)["scenes"][0]["prompt"], build(s, yer_yarilmasi_geo=None)["scenes"][0]["prompt"])

    def test_history_sources(self):
        def rec(g, tag):
            return {"eksenler": json.dumps({"event": EVENT, "axes": {"mod": "yer_yarilmasi", "cografya": g,
                                                                     "beats": tag}})}
        recs = [rec("G1", "O3+F3"), rec("G2", "M2+F2"), {"eksenler": "x"}, rec("G3", "M1+F1")]
        for s in range(1, 11):
            d = build(s, axes_loader=lambda dom: recs)
            tb = self._check(d)
            self.assertIn(tb["geo"], ("G4", "G5", "G6"))
            self.assertEqual((tb["mid"], tb["final"]), ("M2", "F2"))
            self.assertEqual(d["trace"]["axes_source"], "notion")
            tb = self._check(build(s, axes_loader=lambda dom: recs, yer_yarilmasi_geo="G3"), "menü")
            self.assertEqual(tb["geo"], "G3")
        # v1-v4 kayıtları (O*+F*) orta/final LRU'ya girmez: eski F1/F2 başka cümleydi
        self.assertEqual(hp.yer_yarilmasi_v5_tags(["O1+F1", "O3+F3", "M1+F2"]), ["M1+F2"])
        finals = {build(s, axes_loader=lambda dom: [rec("G1", "O1+F1")])["structure"]["yer_yarilmasi"]["final"]
                  for s in range(1, 31)}
        self.assertEqual(finals, {"F1", "F2"})

        def broken(dom):
            raise RuntimeError("Notion yok")
        self.assertEqual(build(3, axes_loader=broken)["trace"]["axes_source"], "bellek")

    def test_v4_still_runs(self):
        d = build(7, yer_yarilmasi_surum="v4")
        self.assertEqual(d["structure"]["yer_yarilmasi"]["mid"], "O3")
        self.assertNotIn("surum", d["structure"]["yer_yarilmasi"])

    def test_kie_final_check(self):
        for s in range(1, 13):
            d = build(s)
            sc, st = d["scenes"][0], d["structure"]
            tb = st["yer_yarilmasi"]
            info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
            needs = [x for x in ty.REQUIRED if x != "big in frame"]
            needs.append({"F1": "big in frame", "F2": "pedestrian overpass"}[tb["final"]])
            for need in needs:
                bad = sc["prompt"].replace(need, "x")
                self.assertIn(f'"{need}" eksik', hp.yer_yarilmasi_v5_text_issues(bad, tb["geo"], tb["final"]))
                self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad}), need)
            for bad in ty.FORBIDDEN + ("city bus",):
                self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"] + f" {bad.upper()}."}), bad)
            for bad in ({"geo": "G7"}, {"mid": "O3"}, {"mid": "M3"}, {"final": "F3"}):
                self.assertTrue(cp.submit_issues({**st, "yer_yarilmasi": {**tb, **bad}}, info), bad)
            self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": "x"}))
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"].replace("4-9s: ", "")}))
            v4 = ty.expected(tb["geo"], "O3", "F3")   # v4 prompt'u (otobüs) v5 kapısından geçmez
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": v4}))
            story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
            self.assertEqual(story, sc["story"])

    def test_approval_lines(self):
        for s in range(1, 21):
            geo = None if s % 2 else "G4"
            d = build(s, yer_yarilmasi_geo=geo)
            sc, st = d["scenes"][0], d["structure"]
            tb = st["yer_yarilmasi"]
            lines = tb["lines"].split("\n")
            self.assertEqual(lines[0], f"Mod: {MODE_LABEL}")
            self.assertEqual(lines[1], VERSION_LINE)
            self.assertTrue(lines[2].startswith(f"Coğrafya: {tb['geo']} ") and
                            lines[2].endswith("(menü)" if geo else "(rastgele)"), lines[2])
            self.assertIn(PLACES[tb["geo"]], lines[2])
            self.assertEqual(lines[3], f"Orta (4-9s): {tb['mid']} «{MIDS[tb['mid']]}»")
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
            for text in (tb["lines"], shown, body):   # boş alan satırı yok
                self.assertNotIn("Araç:", text)
                self.assertNotIn("None", text)

    def test_other_modes_keep_vehicle_line(self):
        """🔍 Ayrıntı'daki araç satırı yalnız v5'te kalkar (v4 ve diğer modlar birebir)."""
        shown = sections_to_text(format_generation(build(5, yer_yarilmasi_surum="v4")["trace"], {}))
        self.assertIn("\nAraç: None\n4-9s olayı (O3)", shown)

    def test_caption(self):
        for s in range(1, 11):
            d = build(s)
            self.assertEqual(d["caption"]["category"], "Yer yarılması")
            self.assertEqual(len(d["caption"]["hashtags"]), 5)
            self.assertTrue(d["youtube_title"].endswith(" #Shorts"))


# 26 Kas: TestPipelineAndBot (menü + pipeline, aktif sürüm) tests/test_yer_yarilmasi_v6.py'ye taşındı.


class TestSnapshot(ty._Quiet):
    def test_v5_40_seeds_lock(self):
        snap = v5_snapshot()
        with open(FIXTURE, encoding="utf-8") as fh:
            self.assertEqual(snap, json.load(fh))
        self.assertEqual(ty.snapshot_hash(snap), V5_SHA256)
        self.assertNotIn(V5_SHA256, (ty.YY_SHA256, ty.YY_V3_SHA256))
        # ilk seçim coğrafya olduğu için 40 tohumun coğrafyası v4 ile tohum tohum aynı
        self.assertEqual("".join(snap[str(s)]["axes"]["axes"]["cografya"][1] for s in range(1, 41)), ty.V2_GEOS)


if __name__ == "__main__":
    unittest.main()
