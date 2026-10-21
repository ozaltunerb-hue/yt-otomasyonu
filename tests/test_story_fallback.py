#!/usr/bin/env python3
"""
🧩 Hibrit hikâye modu (16 Eki 2026, Bahadır): GPT iyi yazarsa kullanılır, yazamazsa kodun onaylı yedeği devreye girer;
üretim "kural kapısından geçmedi" diye durmaz. Ağ yok, Kie/GPT çağrısı yok (sahte GPT).

KALİTE GARANTİSİ: yapılandırılmış hattaki her olayda, kodun seçebileceği HER kombinasyon (görünüm × kamera noktası ×
izinli beat çifti × araç × kaçan kişi sayısı; ortamlı olaylarda en uzun ortam satırı) için yedek prompt sentezlenir ve
son denetimden (final_prompt_issues: sert kurallar, yumuşak beat kontrolü, yakınlık, 175 kelime, karakter) geçer. Hava
yedek prompt'a girmez (sadece GPT mesajında); ortam ekseni sadece stil ekindeki "Setting:" satırını değiştirir, en uzun
satırla denetlenir. Sığmayan kombinasyonlar havuzdan çıkarılmaz: FALLBACK_GAPS'te kilitli, raporda (Bahadır karar verir).
"""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.skeleton_pipeline as sk

# Yedeğin kelime sınırlarına sığmadığı beat çiftleri. 16 Eki ölçümü: bombalar (R6,T5), çığ köy A2/A4/A5 x B2/B5.
# 17 Eki, Bahadır (temizlik turu, madde 1): sığmayan çift hariç çifte çevrilir, beat silinmez. Çığ köyün 6 çifti hariç;
# R6 kurala göre çıktı. Parti 1'in yeni beat'lerinde sığmayan çiftler de (ateş hortumu 23, bombalar 7, şok
# dalgası 1) hariç. Artık
# seçilebilen her kombinasyonun yedeği var: üretim GPT yüzünden durmaz.
FALLBACK_GAPS = {}
# 17 Eki'de hariç çifte çevrilen sığmayan çiftler (her biri hariç listesinde olmalı; yeniden açılırsa test kırılır)
FALLBACK_GAPS_EXCLUDED = {
    es.AVALANCHE_VILLAGE: {("A2", "B2"), ("A2", "B5"), ("A4", "B2"), ("A4", "B5"), ("A5", "B2"), ("A5", "B5")},
    # 18 Eki: Parti 1 metinleri kısaldı, volkan stil eki 96 kelime: bombalar 7 -> 0, şok dalgası 1 -> 0, ateş hortumu
    # 23 -> 1 (T6 19 kelime + araç, U1 21 kelime; kilit 28-29 + insan 6 ile 75'i aşar)
    es.FIRE_TORNADO: {("T6", "U2"), ("T6", "U6")},   # 18 Eki (2): kilit cümle 32-33 kelime (dönen huni)
}


def all_envs(event):
    """Ortamlı olayın seçilebilecek tüm ortamları (ortam satırı ≤ 15 kelime)."""
    if event in es.EARTHQUAKE_EVENTS:
        envs = [{"city": c, "street": s, "light": li} for c in es.EQ_EVENT_CITIES[event]
                for s in es.EQ_EVENT_STREETS[event] for li in es.EQ_ENV_AXES["light"]
                if not (c == es.EQ_AVENUE_CITY and s not in es.EQ_AVENUE_STREETS)]
    else:
        envs = [{"mountain": m, "village": v, "light": li} for m in es.ENV_AXES["mountain"]
                for v in es.ENV_AXES["village"] for li in es.ENV_AXES["light"]]
    return [e for e in envs if len(es.setting_line(e).split()) <= es.SETTING_MAX_WORDS]


def combos(event):
    """(spec, ortam sayısı) her kombinasyon için. Ortamlı olayda en uzun ortam satırı (175 için en kötü durum)."""
    lo, hi = sk.count_range(event, None)
    peoples = list(range(lo, hi + 1)) if es.has_people_rule(event) else [None]
    setting, n_env = None, 1
    if event in es.ENV_EVENTS:
        envs = all_envs(event)
        n_env = len(envs)
        setting = max((es.setting_line(e) for e in envs), key=lambda s: len(s.split()))
    for view in es.structure_views(event):
        vehicles = [v for v, _ in es.event_vehicles(event, view)] if es.uses_vehicle(event) else [None]
        for spot in sk.view_spots(event, view):
            for b2, b3 in es.allowed_pairs(event, view, spot):
                for veh in vehicles:
                    for p in peoples:
                        yield es.build_spec(event, None, spot, view, b2, b3, veh, p, setting), n_env


class TestFallbackEveryCombination(unittest.TestCase):
    def test_every_combination_builds_a_valid_fallback(self):
        report, n_total = {}, 0
        for event in es.structured_events():
            n, n_weighted, gaps, longest, i = 0, 0, set(), 0, 0
            n_weather = len(sk.EVENT_SKELETONS[event]["weather"])
            for spec, n_env in combos(event):
                n += 1
                n_weighted += n_env * n_weather
                b = es.EVENT_BEATS[event]
                self.assertNotIn((spec["beat_2"], spec["beat_3"]), b["excluded_pairs"])
                cands = es.fallback_candidates(spec)
                if not cands:
                    gaps.add((spec["beat_2"], spec["beat_3"]))
                    continue
                sl = cands[i % len(cands)]   # insan cümleleri kombinasyonlar boyunca dönüşümlü denetlenir
                i += 1
                prompt = es.assemble_prompt(spec, sl)
                issues = es.final_prompt_issues(spec, sl, prompt, es.assemble_story(spec, sl))
                if issues:
                    self.fail(f"{event} / {spec['spot']} / {spec['beat_2']}+{spec['beat_3']} / {spec['vehicle']} / "
                              f"{spec.get('people')}: {[x['missing'] for x in issues]}\n{prompt}")
                self.assertEqual(es.strict_beat_issues(spec, sl), [])   # eski sıkı kapıdan da geçer
                self.assertEqual(es.hard_extra_issues(sl), [])
                self.assertLessEqual(len(prompt.split()), 175)
                self.assertLessEqual(len(prompt), es.MAX_PROMPT_CHARS)
                longest = max(longest, len(prompt.split()))
            self.assertEqual(gaps, FALLBACK_GAPS.get(event, set()), event)
            report[event] = {"kombinasyon": n, "hava_ve_ortam_dahil": n_weighted, "sigmayan_cift": sorted(gaps),
                             "en_uzun_prompt": longest}
            n_total += n
        self.assertGreater(n_total, 24000)   # 17 Eki: temizlik turu ve yedeği sığmayan çiftler hariç (16 Eki: > 30000)
        sys.stderr.write("\n🧩 YEDEK KOMBİNASYONLARI: " + json.dumps(report, ensure_ascii=False) + "\n")

    def test_every_people_sentence_passes_slice_one_rules(self):
        # Havuzdaki her insan cümlesi, her kişi sayısıyla: kaçış, sayı, yakınlık (yakınlık kuralı olan olaylarda),
        # yasak kelimeler (çığ, deprem), yağmur (yangın, volkan), çekim/ülke/can kaybı
        for event in es.structured_events():
            lo, hi = sk.count_range(event, None)
            peoples = list(range(lo, hi + 1)) if es.has_people_rule(event) else [None]
            view = es.structure_views(event)[0]
            for spot in sk.view_spots(event, view):
                b2, b3 = es.allowed_pairs(event, view, spot)[0]
                veh = [v for v, _ in es.event_vehicles(event, view)][0] if es.uses_vehicle(event) else None
                for p in peoples:
                    spec = es.build_spec(event, None, spot, view, b2, b3, veh, p)
                    pool = es.fallback_people_pool(spec)
                    self.assertGreaterEqual(len(pool), 6)
                    for t in pool:
                        s1 = es.clean_slice(t.format(N=es.people_word(spec).capitalize()))
                        sl = {"slice_1_rest": s1, "slice_2": es.fallback_beat_slice(spec, "slice_2"),
                              "slice_3": es.fallback_beat_slice(spec, "slice_3")}
                        codes = {x["rule"] for x in es.slice_issues(spec, sl)} - {"total_words", "volcano_prompt_words",
                                                                                 "prompt_chars"}
                        with self.subTest(event=event, spot=spot, people=p, text=s1):
                            self.assertEqual(codes, set())
                            self.assertTrue(6 <= len(s1.split()) <= 18)

    def test_fire_tornado_people_per_environment(self):
        self.assertEqual(set(es.FALLBACK_PEOPLE_FIRE_ENV), set(es.FIRE_TOR_ENVS))
        self.assertNotIn(es.FIRE_TORNADO, es.FALLBACK_PEOPLE)
        for env, pool in es.FALLBACK_PEOPLE_FIRE_ENV.items():
            self.assertGreaterEqual(len(pool), 6)
            for t in pool:
                self.assertTrue(es.find_terms(es._FIRE_TOR_NEAR, t), t)
                self.assertEqual(es.find_terms(es.FIRE_TOR_OPEN_LAND, t), [])

    def test_transition_only_when_needed(self):
        spec = es.build_spec(es.FLOOD, None, "Downtown city center", "riviera", "V1", "D2", "large SUV")
        self.assertEqual(es.fallback_beat_slice(spec, "slice_3"),
                         "Seconds later, in full view, a lamppost topples into the current.")
        self.assertEqual(es.fallback_beat_slice(spec, "slice_2"),
                         "The large SUV is caught by the current, turns sideways and is dragged down the street.")
        self.assertEqual(es.FALLBACK_TRANSITION, "Seconds later, in full view, ")

    def test_former_gaps_are_excluded_pairs(self):
        # 17 Eki, Bahadır (madde 1): yedeği sığmayan çiftler hariç çift oldu; beat'lerin kendisi havuzda
        for event, pairs in FALLBACK_GAPS_EXCLUDED.items():
            b = es.EVENT_BEATS[event]
            for v, d in pairs:
                with self.subTest(event=event, pair=(v, d)):
                    self.assertIn((v, d), b["excluded_pairs"])
                    self.assertIn(v, b["slice_2"])
                    self.assertIn(d, b["slice_3"])
        self.assertEqual(FALLBACK_GAPS, {})

    def test_gap_combination_raises(self):
        spec = es.build_spec(es.AVALANCHE_VILLAGE, None, "Terrace at the edge of the village", None, "A2", "B2", None, 3)
        with self.assertRaises(es.StructureError):
            es.build_fallback(spec)


# Yumuşak kapı: doğru nesne geçer, yanlış nesne/yanlış beat yedeğe düşer
WRONG = [
    # (olay, b2, b3, dilim, cümle, beklenen kod)
    # 17 Eki: T3 ve U3 çıktı; aynı cümleler T4/T1 + U2/U1 çiftlerinde
    (es.FIRE_TORNADO, "T4", "U2", "slice_3",
     "The giant fire tornado rips the burning roof off a house and scatters the house's sheets.", "beat_object"),
    (es.FIRE_TORNADO, "T4", "U2", "slice_3",
     "The fire tornado rips the burning roof off a house beside a tree, tearing the house apart in flames.",
     "beat_other_object"),
    (es.FIRE_TORNADO, "T1", "U1", "slice_2",
     "The towering vortex lifts a burning tree trunk and flings it high across the street.", "beat_vehicle"),
    (es.FLOOD, "V1", "D2", "slice_3", "A low wall collapses into the water as the street fills with debris.",
     "beat_object"),
    (es.AVALANCHE_VILLAGE, "A1", "B3", "slice_3",
     "The snow blast tears the roof off a wooden barn and scatters its dark planks across the street.", "beat_object"),
    (es.EARTHQUAKE_OLD_STREET, "R1", "T3", "slice_3",
     "The next stone house in the row caves in as dust billows across the lane.", "beat_object"),
]
RIGHT = [
    (es.FIRE_TORNADO, "T4", "U2", "slice_3",
     "Burning pines are ripped from the earth by the vortex and hurled along the street."),
    (es.FIRE_TORNADO, "T5", "U1", "slice_2", "The towering vortex tips the SUV upside down beside a burning tree."),
    (es.FLOOD, "V1", "D2", "slice_3", "A streetlight snaps at its base and falls into the brown torrent."),
    (es.AVALANCHE_VILLAGE, "A1", "B3", "slice_3", "The church bell tower bends and crashes across the street."),
]


class TestSoftGate(unittest.TestCase):
    def spec(self, event, b2, b3):
        spot = next(s for v in es.structure_views(event) for s in sk.view_spots(event, v)
                    if (b2, b3) in es.allowed_pairs(event, es.structure_views(event)[0], s))
        view = es.structure_views(event)[0]
        veh = "SUV" if es.uses_vehicle(event) and view is None else (
            [v for v, _ in es.event_vehicles(event, view)][0] if es.uses_vehicle(event) else None)
        lo, _ = sk.count_range(event, None)
        return es.build_spec(event, None, spot, view, b2, b3, veh, lo if es.has_people_rule(event) else None)

    def codes(self, spec, slot, text):
        sl = {"slice_2": es.fallback_beat_slice(spec, "slice_2"), "slice_3": es.fallback_beat_slice(spec, "slice_3"),
              slot: text}
        return {x["rule"] for x in es.soft_beat_issues(spec, sl)}

    def test_wrong_object_or_beat_rejected(self):
        for event, b2, b3, slot, text, code in WRONG:
            with self.subTest(event=event, text=text):
                self.assertIn(code, self.codes(self.spec(event, b2, b3), slot, text))

    def test_right_object_passes_without_verb_chain(self):
        for event, b2, b3, slot, text in RIGHT:
            spec = self.spec(event, b2, b3)
            with self.subTest(event=event, text=text):
                self.assertEqual(self.codes(spec, slot, text), set())

    def test_verb_chain_no_longer_rejects(self):
        # Eski kapı fiil zinciri ister (T4: kayma + hortumun yanından geçmesi; 17 Eki: T3 çıktı); yeni kapı aracı
        # görünce geçer
        spec = self.spec(es.FIRE_TORNADO, "T4", "U2")
        text = "The SUV spins wildly in the smoke beside the burning houses."
        self.assertIn("beat_terms", {x["rule"] for x in es.strict_beat_issues(spec, {"slice_2": text,
                                                                                    "slice_3": "x"})})
        self.assertEqual(self.codes(spec, "slice_2", text), set())

    def test_object_groups_cover_every_beat_and_own_text_passes(self):
        for event in es.structured_events():
            for slot in ("slice_2", "slice_3"):
                for bid, beat in es.EVENT_BEATS[event][slot].items():
                    if "{vehicle}" in beat["text"]:
                        self.assertNotIn(bid, es.OBJECT_GROUPS[event])
                    else:
                        self.assertIn(bid, es.OBJECT_GROUPS[event])
                        grp = beat["terms"][es.OBJECT_GROUPS[event][bid]]
                        self.assertTrue(es.find_terms(grp, beat["text"]), (event, bid))

    def test_rejected_real_pass_soft_gate(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures", "rejected_real.json"), encoding="utf-8") as f:
            data = json.load(f)["false_rejections"]
        # 15 Eki canlı retleri; 2i kayıtları ("source") üretimleriyle birebir test_rejected_real.py'de. 17 Eki:
        # çıkarılan maddelerin kayıtları atlanır, eski araç adları bugünkü karşılığına çevrilir
        sys.path.insert(0, os.path.dirname(__file__))
        from test_rejected_real import current, retired
        for r in [current(x) for x in data if "source" not in x and not retired(x)]:
            e, bid = r["event"], r["beat"]
            slot = "slice_2" if bid in es.EVENT_BEATS[e]["slice_2"] else "slice_3"
            view = es.structure_views(e)[0]
            # 17 Eki: maddenin herhangi bir noktada izinli ilk eşi (hariç çiftler arttı)
            b2, b3, spot = next((p[0], p[1], s) for s in sk.view_spots(e, view) for p in es.allowed_pairs(e, view, s)
                                if p[0 if slot == "slice_2" else 1] == bid)
            veh = r.get("vehicle") or ([v for v, _ in es.event_vehicles(e, view)][0] if es.uses_vehicle(e) else None)
            lo, _ = sk.count_range(e, None)
            spec = es.build_spec(e, None, spot, view, b2, b3, veh, lo if es.has_people_rule(e) else None)
            with self.subTest(event=e, beat=bid, text=r["text"]):
                self.assertEqual(self.codes(spec, slot, r["text"]), set())


class TestHardRules(unittest.TestCase):
    def test_hard_extra_words(self):
        for text, code in (("The SUV is filmed spinning across the road.", "hard_camera"),
                           ("A Japanese street floods as the wave hits.", "hard_place_name"),
                           ("The Mediterranean village burns.", "hard_place_name"),
                           ("Two people lie dead in the street.", "hard_death"),
                           ("An injured man limps away from the flames.", "hard_death")):
            with self.subTest(text=text):
                self.assertIn(code, {x["rule"] for x in es.hard_extra_issues({"slice_1_rest": text, "slice_2": "",
                                                                                 "slice_3": ""})})
        # serbest kalanlar: "die down", "kill the flames", "alpine", "car bodies"
        for text in ("The flames die down near the alpine chalets.", "The water load kills the flames.",
                     "The car bodies crumple."):
            self.assertEqual(es.hard_extra_issues({"slice_1_rest": text, "slice_2": "", "slice_3": ""}), [], text)

    def test_code_texts_never_hit_hard_words(self):
        texts = []
        for event in es.structured_events():
            texts.append(es.EVENT_KEY_VISUAL[event])
            texts += [b["text"] for sl in ("slice_2", "slice_3") for b in es.EVENT_BEATS[event][sl].values()]
            texts += list(es.FALLBACK_PEOPLE.get(event, ()))
        texts += [e["key"] for e in es.FIRE_TOR_ENVS.values()]
        texts += [t for p in es.FALLBACK_PEOPLE_FIRE_ENV.values() for t in p]
        texts.append(es.FALLBACK_TRANSITION)
        for t in texts:
            self.assertEqual(es.hard_extra_issues({"slice_1_rest": t, "slice_2": "", "slice_3": ""}), [], t)


def fake_gpt(answers):
    calls = []

    async def gpt(system, user, **kw):
        calls.append(user)
        r = answers[min(len(calls), len(answers)) - 1]
        return r(user) if callable(r) else r
    return gpt, calls


class TestFlow(unittest.TestCase):
    def setUp(self):
        es._BEAT_MEMORY.clear()
        es._FIRE_TOR_ENV_MEMORY.clear()
        es._ENV_MEMORY.clear()
        es._EQ_ENV_MEMORY.clear()

    tearDown = setUp

    def run_scene(self, domain, event, answers, view=None):
        import core.creative_pipeline as cp
        gpt, calls = fake_gpt(answers)
        scene = asyncio.run(cp.build_creative_scene(domain, event, [], [], gpt, view=view))
        return scene, calls

    def test_hard_violation_twice_falls_back(self):
        import core.creative_pipeline as cp
        bad = {"slice_1_rest": "Three people run away right below the balcony.",
               "slice_2": "The SUV is filmed as the towering vortex flips it over in flames.",
               "slice_3": "The vortex rips burning trees from the ground and hurls them down the street."}
        scene, calls = self.run_scene("fire_disasters", es.FIRE_TORNADO, [bad])
        self.assertEqual(len(calls), cp.STRUCTURED_MAX_ATTEMPTS)
        st = scene["structure"]
        self.assertEqual(st["story_source_kind"], "fallback")
        self.assertIn("çekim/kayıt kelimesi (filmed)", st["story_source"])
        # hikâyede çekim kelimesi yok (21 Eki: stil ekindeki kamera cümlesi "Handheld footage filmed ..." ile başlar)
        self.assertNotIn("filmed", scene["story"])
        self.assertEqual(es.final_prompt_issues(st["spec"], st["slices"], scene["prompt"], scene["story"]), [])
        self.assertTrue(scene["prompt"].startswith(f"0-4s: {es.FIRE_TOR_ENVS[st['spec']['fire_env']]['key']} "))

    def test_every_structured_event_falls_back_and_proceeds(self):
        # Sahte GPT her olayda iki kez de yasak kelime yazar: her olayda yedek devreye girer, son denetim temiz
        bad = {"slice_1_rest": "The scene is filmed from far away by people.", "slice_2": "Nothing much happens here at all.",
               "slice_3": "Nothing much happens there at all either."}
        for event in es.structured_events():
            domain = sk.EVENT_SKELETONS[event]["domain"]
            gaps = FALLBACK_GAPS.get(event, set())
            real = es.choose_beats

            def beats(ev, view, spot, history, rng=None):   # sığmayan çiftler (FALLBACK_GAPS) bu testin konusu değil
                return next(p for p in es.allowed_pairs(ev, view, spot) if p not in gaps)
            for _ in range(3):
                with patch.object(es, "choose_beats", beats if gaps else real):
                    scene, calls = self.run_scene(domain, event, [bad])
                st = scene["structure"]
                with self.subTest(event=event):
                    self.assertEqual(len(calls), 2)
                    self.assertEqual(st["story_source_kind"], "fallback")
                    self.assertEqual(es.final_prompt_issues(st["spec"], st["slices"], scene["prompt"],
                                                            scene["story"]), [])

    def test_good_gpt_used_and_labelled(self):
        good = {"slice_1_rest": "Three people sprint away right below the railing.",
                "slice_2": "The SUV is hoisted by the vortex and thrown into a blazing pine beside the houses.",
                "slice_3": "Burning pines are ripped from the earth by the vortex and hurled along the street."}
        with patch.object(es, "choose_beats", lambda *a, **k: ("T1", "U2")), \
                patch.object(es, "choose_event_vehicle", lambda e, rng=None: "SUV"), \
                patch.object(es, "choose_people", lambda e, s, rng=None: 3):
            scene, calls = self.run_scene("fire_disasters", es.FIRE_TORNADO, [good])
        self.assertEqual(len(calls), 1)
        self.assertEqual(scene["structure"]["story_source"], "Hikâye: GPT (deneme 1)")
        self.assertEqual(scene["structure"]["slices"], {k: es.clean_slice(v) for k, v in good.items()})
        from core.trace_format import format_final_prompt, format_generation
        onay = format_final_prompt({"prompt": scene["prompt"], "story": scene["story"],
                                    "style_suffix": scene["style_suffix"],
                                    "story_source": scene["structure"]["story_source"]})[1]
        self.assertIn("\nHikâye: GPT (deneme 1)\n", onay)
        self.assertIn("Hikâye: GPT (deneme 1)", "\n".join(b for _, b in format_generation(scene["trace"])))

    def test_old_line_attempts_unchanged(self):
        import core.creative_pipeline as cp
        self.assertEqual(cp.MAX_ATTEMPTS, 3)

    def test_source_log_and_report(self):
        import core.creative_pipeline as cp
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import fallback_report
        bad = {"slice_1_rest": "x y z w v u t.", "slice_2": "nothing.", "slice_3": "nothing."}
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "log.jsonl")
            with patch.dict(os.environ, {"STORY_SOURCE_LOG": path}):
                for _ in range(2):
                    self.run_scene("fire_disasters", es.FIRE_TORNADO, [bad])
                self.run_scene("avalanche_disasters", es.AVALANCHE_SKI, [bad])
            rows = [json.loads(l) for l in open(path, encoding="utf-8")]
            self.assertEqual(len(rows), 3)
            for r in rows:
                self.assertEqual(r["source"], "fallback")
                self.assertEqual(r["gpt_attempts"], 2)
                self.assertTrue(r["fallback_reason"].startswith("deneme 1: "))
                self.assertIn("ts", r)
            self.assertIn(rows[0]["environment"], es.FIRE_TOR_ENVS)
            text = fallback_report.report(fallback_report.load(path))
            self.assertIn("Fire tornado tears across a burning roadside", text)
            self.assertIn("2/2", text)
        # ortam değişkeni yokken testte yazılmaz (gerçek istatistik kirlenmesin)
        self.assertIsNone(cp.story_source_log_path() if "STORY_SOURCE_LOG" not in os.environ else None)


if __name__ == "__main__":
    unittest.main()
