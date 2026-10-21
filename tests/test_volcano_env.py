#!/usr/bin/env python3
"""
18 Eki (3), Bahadır: volkan bombaları ve kül bulutu için ORTAM ekseni + yer ağırlığı + ışık çeşitliliği. Ağ yok,
Kie/GPT/Notion çağrısı yok.

- Ortam (sk.VOLC_ENVS): kamera cümlesinde "the village street" yerine, GPT'ye PLACE satırında; kilit cümleye girmez.
  Son 2 üretimin ortamı tekrar etmez, kalanlar ağırlıklı (bombalar eşit; kül bulutu A=2 B=2 C=1 D=1).
- Yer: balkon 2, çatı terası ve yamaç terası 1; son yer arka arkaya gelmez. Yer metinleri aynı.
- Işık (sk.VOLCANO_WEATHER_WEIGHTS): mevcut metin bir seçenek; kül bulutunda gece yok; her metin ≤ 9 kelime.
- Kilit cümleler, havuzlar, çiftler, hariç çiftler, kapılar aynı; hiçbir kombinasyon 175 kelimeyi aşmaz.
"""
import asyncio
import collections
import os
import random
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.skeleton_pipeline as sk

VB, PY, ER = es.VOLCANIC_BOMBS, es.PYROCLASTIC, es.ERUPTION
BAL = "Balcony of a village house facing the erupting volcano"
RT = "Rooftop terrace facing the erupting volcano"
HT = "Hillside terrace facing the erupting volcano"
OLD_WEATHER = "ash-grey sky lit orange by a distant eruption plume"

ENVS = {   # (Notion etiketi, kamera/yer metni)
    "pastel_town": ("pastel kasaba caddesi", "a street of colorful concrete houses with parked trucks"),
    "hillside_town": ("Akdeniz tepe kasabası", "a wide hillside-town street of stone and painted houses"),
    "suburb": ("banliyö mahallesi", "a suburban street of detached houses, garages and palm trees"),
    "mountain_village": ("dağ eteği köyü", "a village street of wooden and stone houses among trees"),
}
WEATHER = {
    VB: {OLD_WEATHER: 1, "warm orange dusk sky glowing from the eruption": 2,
         "pink-orange dawn light under a dark ash sky": 1, "dark night sky lit by glowing lava and fires": 1},
    PY: {OLD_WEATHER: 2, "warm orange dusk sky glowing from the eruption": 1,
         "bright hazy daylight under a dark ash sky": 1},
}
# Değişmemesi gerekenler (18 Eki (3) öncesi, 6f16609)
KEYS = {VB: "Glowing volcanic bombs streak down from the erupting volcano and slam into a village street, punching "
            "through roofs and igniting cars.",
        PY: "A pyroclastic cloud races down the volcano’s flank and slams into a village street."}


class TestVolcEnvData(unittest.TestCase):
    def test_envs_texts_labels_weights(self):
        self.assertEqual({k: (v["label"], v["text"]) for k, v in sk.VOLC_ENVS.items()}, ENVS)
        for _, text in ENVS.values():
            self.assertLessEqual(len(text.split()), 10, text)
            self.assertEqual(es.pool_lint_hits(text), [], text)
            self.assertNotIn("small", text)
        self.assertEqual(sk.VOLC_ENV_WEIGHTS[VB], {k: 1 for k in ENVS})
        self.assertEqual(sk.VOLC_ENV_WEIGHTS[PY], {"pastel_town": 2, "hillside_town": 2, "suburb": 1,
                                                   "mountain_village": 1})
        self.assertEqual(es.VOLC_ENV_EVENTS, (PY, VB))
        self.assertNotIn(ER, sk.VOLC_ENV_WEIGHTS)   # şok dalgası (devre dışı) dokunulmadı

    def test_weather_options(self):
        self.assertEqual(sk.VOLCANO_WEATHER_WEIGHTS, WEATHER)
        for e, opts in WEATHER.items():
            self.assertEqual(sk.EVENT_SKELETONS[e]["weather"], list(opts))
            for t in opts:
                self.assertLessEqual(len(t.split()), len(OLD_WEATHER.split()), t)
        self.assertFalse([t for t in WEATHER[PY] if "night" in t])   # kül bulutunda gece yok
        self.assertEqual(sk.EVENT_SKELETONS[ER]["weather"], [OLD_WEATHER])
        self.assertEqual(sk.VOLCANO_WEATHER, [OLD_WEATHER])

    def test_spot_kinds_and_weights(self):
        self.assertEqual(sk.VOLC_SPOT_KIND, {BAL: "balkon", RT: "çatı", HT: "yamaç"})
        self.assertEqual({sp: es.volc_spot_weight(sp) for sp in (BAL, RT, HT)}, {BAL: 2, RT: 1, HT: 1})
        for e in es.VOLC_ENV_EVENTS:
            self.assertEqual(set(sk.EVENT_SKELETONS[e]["spots"]), {BAL, RT, HT})
        self.assertEqual(sk.CAMERA_SPOTS[BAL], "on the balcony of a village house across the street")


class TestVolcEnvSelection(unittest.TestCase):
    def setUp(self):
        es._VOLC_ENV_MEMORY.clear()
        es._VOLC_SPOT_MEMORY.clear()

    def tearDown(self):
        es._VOLC_ENV_MEMORY.clear()
        es._VOLC_SPOT_MEMORY.clear()

    def test_env_lru_last_two_never_repeat(self):
        rng = random.Random(7)
        for e in es.VOLC_ENV_EVENTS:
            seq = []
            for _ in range(400):
                env = es.choose_volc_env(e, rng)
                es.remember_volc_env(e, env)
                seq.append(env)
            for i in range(2, len(seq)):
                self.assertNotIn(seq[i], seq[i - 2:i], (e, i))
            self.assertEqual(set(seq), set(ENVS))

    def test_env_memory_per_event(self):
        es.remember_volc_env(VB, "suburb")
        es.remember_volc_env(VB, "pastel_town")
        for _ in range(50):
            self.assertIn(es.choose_volc_env(VB), {"hillside_town", "mountain_village"})
        self.assertIn(es.choose_volc_env(PY, random.Random(1)), ENVS)   # kül bulutu hafızası ayrı

    def test_env_weights_without_lru(self):
        rng = random.Random(3)
        c = collections.Counter(es._weighted_choice(sk.VOLC_ENV_WEIGHTS[PY], list(ENVS), rng) for _ in range(6000))
        self.assertAlmostEqual(c["pastel_town"] / c["suburb"], 2, delta=0.3)
        self.assertAlmostEqual(c["hillside_town"] / c["mountain_village"], 2, delta=0.3)

    def test_spot_last_two_never_repeat_and_weighted(self):
        # 21 Eki (Gece 1 / Aşama 3): tüm eksenlerde son 2 elenir (önceki: son 1). 3 yerde son 2 elenince tek aday
        # kalır, sıra döner; ağırlık sadece ilk seçimde ve aday biterse etkili (ağırlıklar değişmedi, aşağıda)
        self.assertEqual(es.VOLC_SPOT_BLOCK, 2)
        rng = random.Random(5)
        for e in es.VOLC_ENV_EVENTS:
            seq = []
            for _ in range(300):
                sp = es.choose_volc_spot(e, [], rng)
                es.remember_volc_spot(e, sp)
                seq.append(sp)
            self.assertFalse([i for i in range(2, len(seq)) if seq[i] in (seq[i - 1], seq[i - 2])])
            self.assertEqual(set(seq), {BAL, RT, HT})
        # ağırlık tek başına (LRU yok): balkon ≈ 2 x çatı
        c = collections.Counter(es._weighted_choice({sp: es.volc_spot_weight(sp) for sp in (BAL, RT, HT)},
                                                    [BAL, RT, HT], rng) for _ in range(6000))
        self.assertAlmostEqual(c[BAL] / c[RT], 2, delta=0.3)

    def test_spot_history_from_notion(self):
        combo = f"volcano_disasters|none|{VB.lower()}|{BAL.lower()}##R2+T5|skeleton"
        for _ in range(50):
            self.assertNotEqual(es.choose_volc_spot(VB, [combo]), BAL)
        es.remember_volc_spot(VB, RT)   # süreç hafızası Notion'dan yeni
        for _ in range(50):
            self.assertNotEqual(es.choose_volc_spot(VB, [combo]), RT)

    def test_weather_weighted(self):
        rng = random.Random(9)
        c = collections.Counter(es.choose_volc_weather(VB, rng) for _ in range(6000))
        self.assertAlmostEqual(c["warm orange dusk sky glowing from the eruption"] / c[OLD_WEATHER], 2, delta=0.3)
        c = collections.Counter(es.choose_volc_weather(PY, rng) for _ in range(6000))
        self.assertAlmostEqual(c[OLD_WEATHER] / c["bright hazy daylight under a dark ash sky"], 2, delta=0.3)


class TestVolcEnvPrompt(unittest.TestCase):
    def _spec(self, e, spot, env, b2=None, b3=None):
        b2, b3 = (b2, b3) if b2 else sorted(es.allowed_pairs(e, None, spot))[0]
        veh = es.event_vehicles(e, None)[0][0] if es.uses_vehicle(e) else None
        return es.build_spec(e, None, spot, None, b2, b3, veh, sk.count_range(e, None)[0], None, env)

    def test_env_in_camera_sentence_not_in_key(self):
        for e in es.VOLC_ENV_EVENTS:
            for env, (_, text) in ENVS.items():
                for spot in (BAL, RT, HT):
                    spec = self._spec(e, spot, env)
                    self.assertEqual(spec["key_visual"], KEYS[e])
                    self.assertNotIn(text, spec["key_visual"])
                    self.assertIn(f"over {text} toward the erupting volcano", spec["suffix"])
                    self.assertNotIn("the village street", spec["suffix"])
                    old = sk.style_suffix(e, None, spot)
                    self.assertEqual(spec["suffix"], old.replace("the village street", text))   # başka bir şey değişmez
                    self.assertEqual(spec["volc_env"], env)

    def test_env_rejected_elsewhere(self):
        with self.assertRaises(es.StructureError):
            es.build_spec(ER, None, BAL, None, "S2", "U3", None, 3, None, "suburb")
        with self.assertRaises(es.StructureError):
            self._spec(VB, BAL, "desert")

    def test_final_check_needs_same_env(self):
        spec = self._spec(VB, BAL, "suburb")
        sl = es.build_fallback(spec, random.Random(1))
        prompt = es.assemble_prompt(spec, sl)
        self.assertEqual(es.final_prompt_issues(spec, sl, prompt, es.assemble_story(spec, sl)), [])
        bad = {**spec, "volc_env": "pastel_town"}
        self.assertIn("suffix", {i["rule"] for i in es.final_prompt_issues(bad, sl, prompt)})

    def test_every_combination_fits_175_and_passes(self):
        """olay × ortam × yer × beat çifti × araç × kişi sayısı × kod yedeği: ≤175 kelime, son denetim temiz."""
        worst = 0
        for e in es.VOLC_ENV_EVENTS:
            lo, hi = sk.count_range(e, None)
            vehicles = [v for v, _ in es.event_vehicles(e, None)] if es.uses_vehicle(e) else [None]
            for env in ENVS:
                for spot in sk.view_spots(e, None):
                    for b2, b3 in es.allowed_pairs(e, None, spot):
                        for veh in vehicles:
                            for people in (lo, hi):
                                spec = es.build_spec(e, None, spot, None, b2, b3, veh, people, None, env)
                                cands = es.fallback_candidates(spec)
                                self.assertTrue(cands, (e, env, spot, b2, b3, veh, people))
                                for sl in cands:
                                    prompt = es.assemble_prompt(spec, sl)
                                    worst = max(worst, len(prompt.split()))
                                    self.assertLessEqual(len(prompt.split()), 175)
                                self.assertEqual(es.final_prompt_issues(spec, cands[0], es.assemble_prompt(
                                    spec, cands[0]), es.assemble_story(spec, cands[0])), [])
        self.assertEqual(worst, 174)

    def test_word_budget_keeps_gpt_prompt_within_175(self):
        """Bahadır kararı (18 Eki (3)): GPT'ye söylenen toplam = 175 - stil eki - 3 (en fazla kapının 75'i)."""
        seen = set()
        for e in es.VOLC_ENV_EVENTS:
            self.assertIn(e, es.BUDGET_EVENTS)
            for env in [None, *ENVS]:
                for spot in (BAL, RT, HT):
                    spec = self._spec(e, spot, env)
                    total = min(75, 175 - 3 - len(spec["suffix"].split()))
                    line = es.word_budget_line(spec)
                    self.assertIn(f"must total at most {total} words", line)
                    self.assertGreaterEqual(total, len(spec["key_visual"].split()) + 6 + 10 + 10)
                    seen.add((e, total))
                    # bütçeye tam uyan bir hikâye (toplam = total) prompt'u 175'te tutar
                    key = len(spec["key_visual"].split())
                    rest = total - key
                    sl = {"slice_1_rest": " ".join(["run"] * 6), "slice_2": " ".join(["x"] * (rest // 2 - 3)),
                          "slice_3": " ".join(["y"] * (rest - 6 - (rest // 2 - 3)))}
                    self.assertLessEqual(len(es.assemble_prompt(spec, sl).split()), 175)
        self.assertIn((PY, 59), seen)   # en uzun kül bulutu eki (113)
        self.assertIn((VB, 69), seen)   # en uzun bombalar eki (103)
        self.assertEqual(es.word_budget_line({"event": ER, "key_visual": "x"}), "")

    def test_pools_pairs_unchanged(self):
        self.assertEqual(len(es.EVENT_BEATS[VB]["slice_2"]), 8)
        self.assertEqual(len(es.EVENT_BEATS[VB]["slice_3"]), 7)
        self.assertEqual(len(es.EVENT_BEATS[PY]["slice_2"]), 6)
        self.assertEqual(len(es.EVENT_BEATS[PY]["slice_3"]), 6)
        # hariç çiftler 6f16609 ile aynı (kod yedeği ve hikâye kuralları değişmedi)
        self.assertEqual(es.EVENT_BEATS[VB]["excluded_pairs"],
                         {("R1", "T2"), ("R1", "T9"), ("R2", "T2"), ("R2", "T9"), ("R5", "T6"), ("R7", "T1"),
                          ("R7", "T7"), ("R8", "T6"), ("R9", "T5")})
        self.assertEqual(es.EVENT_BEATS[PY]["excluded_pairs"],
                         {("P1", "Q1"), ("P1", "Q6"), ("P3", "Q3"), ("P3", "Q6"), ("P5", "Q1"), ("P5", "Q4"),
                          ("P6", "Q3"), ("P6", "Q6")})


class TestVolcEnvPipeline(unittest.TestCase):
    def setUp(self):
        es._VOLC_ENV_MEMORY.clear()
        es._VOLC_SPOT_MEMORY.clear()
        es._BEAT_MEMORY.clear()

    def test_scene_trace_place_and_labels(self):
        import core.creative_pipeline as cp
        from core.trace_format import format_final_prompt
        from tests.test_event_structure import _volc_gpt
        msgs = []
        for e in es.VOLC_ENV_EVENTS:
            seen_env, seen_spot = [], []
            for _ in range(6):
                msgs.clear()
                scene = asyncio.run(cp.build_creative_scene("volcano_disasters", e, [], [], _volc_gpt(msgs)))
                tr, st = scene["trace"], scene["structure"]
                env = tr["volc_env"]
                self.assertIn(env, ENVS)
                import core.scene_env as sv   # 21 Eki (Aşama 5): ışık kapsamı (eklenenler ağırlık 1)
                self.assertIn(tr["weather"], list(WEATHER[e]) + list(sv.LIGHT_ADD[e]))
                self.assertIn(ENVS[env][1], scene["prompt"])
                self.assertTrue(scene["prompt"].startswith(f"0-4s: {KEYS[e]}"))
                self.assertIn(f"PLACE: {ENVS[env][1]}, ", msgs[0])
                self.assertIn(f"WEATHER: {tr['weather']}\n", msgs[0])
                self.assertEqual(st["env_option"], ENVS[env][0])
                self.assertEqual(st["environment"], f"Ortam: {ENVS[env][0]} ({env}) · kamera = {scene['spot']}")
                self.assertEqual(tr["fire_env_label_short"], ENVS[env][0])   # onay "Yer" satırında "ortam: ..."
                text = format_final_prompt({**scene, "environment": st["environment"]})[1]
                self.assertIn(f"Ortam: {ENVS[env][0]}", text)
                seen_env.append(env)
                seen_spot.append(scene["spot"])
            for i in range(2, 6):
                self.assertNotIn(seen_env[i], seen_env[i - 2:i])
            for i in range(1, 6):
                self.assertNotEqual(seen_spot[i], seen_spot[i - 1])

    def test_other_volcano_and_events_no_env(self):
        import core.creative_pipeline as cp
        from tests.test_event_structure import _volc_gpt
        scene = asyncio.run(cp.build_creative_scene("volcano_disasters", ER, [], [], _volc_gpt()))
        self.assertNotIn("volc_env", scene["trace"])
        self.assertIsNone(scene["structure"]["env_option"])
        self.assertIn("the village street", scene["prompt"])


class TestVolcEnvNotion(unittest.TestCase):
    def setUp(self):
        import infrastructure.notion_logger as nl
        self.nl = nl
        for name, value in (("NOTION_ENABLED", True), ("IS_DRY_RUN", False), ("NOTION_DB_ID", "db")):
            p = patch.object(nl.settings, name, value)
            p.start()
            self.addCleanup(p.stop)

    def test_property_and_options(self):
        nl = self.nl
        self.assertEqual(nl.ENV_PROPERTY, "Ortam")
        self.assertEqual(set(nl.ENV_OPTIONS), {v[0] for v in ENVS.values()})
        self.assertEqual([o["name"] for o in nl.EXTRA_PROPERTIES["Ortam"]["select"]["options"]], list(nl.ENV_OPTIONS))

    def test_ensure_schema_creates_field_with_options(self):
        nl, calls = self.nl, []

        def fake(method, url, json=None):
            calls.append((method, json))
            return {"properties": {k: {} for k in nl.EXTRA_PROPERTIES if k != "Ortam"}}
        with patch.object(nl, "_notion_request", fake), patch.object(nl.NotionTracker, "ensure_status_options"):
            have = nl.NotionTracker.ensure_schema()
        self.assertIn("Ortam", have)
        body = [j for m, j in calls if m == "PATCH"][0]
        self.assertEqual(body["properties"]["Ortam"], nl.EXTRA_PROPERTIES["Ortam"])

    def test_existing_field_missing_options_added(self):
        nl, calls = self.nl, []
        existing = [{"id": "x1", "name": "pastel kasaba caddesi", "color": "pink"}]

        def fake(method, url, json=None):
            calls.append((method, json))
            props = {k: {} for k in nl.EXTRA_PROPERTIES}
            props["Ortam"] = {"select": {"options": existing}}
            return {"properties": props}
        with patch.object(nl, "_notion_request", fake), patch.object(nl.NotionTracker, "ensure_status_options"):
            nl.NotionTracker.ensure_schema()
        body = [j for m, j in calls if m == "PATCH"][0]
        opts = body["properties"]["Ortam"]["select"]["options"]
        self.assertEqual(opts[0], existing[0])
        self.assertEqual([o["name"] for o in opts[1:]], [n for n in nl.ENV_OPTIONS if n != "pastel kasaba caddesi"])

    def test_record_env_option(self):
        nl = self.nl
        t = nl.NotionTracker("page")
        with patch.object(t, "_patch") as p:
            t.record_env_option("banliyö mahallesi")
        p.assert_called_once_with({"Ortam": {"select": {"name": "banliyö mahallesi"}}})


if __name__ == "__main__":
    unittest.main()
