#!/usr/bin/env python3
"""Kalıcı tekrar önleme hafızası (21 Eki 2026, Gece 1 / Aşama 3).

- Notion "Eksenler" alanı: seçim anında tek satır JSON, Onay'dan önce yazılır; iptal edilen üretim de kayıtta kalır.
- Geçmiş Notion'dan (kategorinin son kayıtları, durum filtresi yok: iptaller dahil); eski kayıtlarda Combo Key / Ortam /
  Prompt Setting satırı. Okuma başarısızsa süreç hafızası + Onay'da uyarı satırı, üretim durmaz.
- Spot, ortam, ışık, araç, kişi: son 2 elenir (2 seçenekte son 1, tek seçenekte eleme yok).
GPT yok (kod yedeği), Kie yok, Notion sahte.
"""
import asyncio
import json
import logging
import os
import random
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import core.event_structure as es   # noqa: E402  (creative_pipeline'dan önce: döngüsel import sırası)
import core.axes_history as ah   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
import prompt_snapshot as ps   # noqa: E402
from core.trace_format import format_final_prompt   # noqa: E402
from infrastructure import notion_logger as nl   # noqa: E402

DOMAIN = {e: s["domain"] for e, s in sk.EVENT_SKELETONS.items()}


def rec(event: str, axes: dict, status: str = "✅ Tamamlandı (Test Modu / YouTube Atlandı)") -> dict:
    """Sahte Notion ham kaydı ("Eksenler" alanlı)."""
    full = dict.fromkeys(ah.AXIS_KEYS)
    full.update(axes)
    return {"combo_key": f"{DOMAIN[event]}|none|{event.lower()}|{(axes.get('spot') or 'x').lower()}##A1+B1|cam",
            "eksenler": ah.axes_json(event, full), "ortam": "", "prompt": "", "status": status, "date": ""}


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)
        ps.reset_memory()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        ps.reset_memory()

    def scene(self, event, records=None, loader=None, seed=1):
        random.seed(seed)
        if loader is None:
            loader = (lambda domain: list(records or []))
        return ps.build(event, axes_loader=loader)


class TestLruAxis(unittest.TestCase):
    def test_depth_by_option_count(self):
        self.assertEqual(es.lru_axis(["a"], ["a", "a"]), (["a"], []))           # tek seçenek: eleme yok
        self.assertEqual(es.lru_axis(["a", "b"], ["b", "a"]), (["b"], ["a"]))   # 2 seçenek: son 1
        self.assertEqual(es.lru_axis(["a", "b", "c"], ["a", "b"]), (["c"], ["a", "b"]))   # 3+: son 2
        self.assertEqual(es.lru_axis(["a", "b", "c", "d"], ["a", "b", "c"]), (["a", "d"], ["b", "c"]))
        self.assertEqual(es.lru_axis(["a", "b", "c"], [None, "", "c"]), (["a", "b"], ["c"]))   # boş değer sayılmaz
        self.assertEqual(es.lru_axis([2, 3, 4, 5], []), ([2, 3, 4, 5], []))

    def test_people_choice_same_draw_as_randint(self):
        # boş geçmişte choice(range) ile randint aynı sayıyı çeker: baseline değişmez
        for seed in range(30):
            random.seed(seed)
            a = random.randint(3, 6)
            random.seed(seed)
            self.assertEqual(es.choose_people(es.MUDSLIDE, None), a)


class TestParseRecord(unittest.TestCase):
    def test_eksenler_json_roundtrip(self):
        r = rec(es.FLOOD, {"spot": "Downtown city center", "view": "riviera", "light": "heavy rain",
                           "vehicle": "large SUV", "beats": "V1+D2"})
        p = ah.parse_record(r)
        self.assertEqual(p["source"], "eksenler")
        self.assertEqual(p["event"], es.FLOOD)
        self.assertEqual(p["axes"]["view"], "riviera")
        self.assertIsNone(p["axes"]["people"])

    def test_legacy_combo_key(self):
        p = ah.parse_record({"combo_key": "urban_city_disasters|none|flash flooding in city streets|"
                                          "downtown city center#east_asian_coast#V4+D8|bystander_handheld"})
        self.assertEqual(p["source"], "eski")
        self.assertEqual((p["axes"]["spot"], p["axes"]["view"], p["axes"]["beats"]),
                         ("Downtown city center", "east_asian_coast", "V4+D8"))
        self.assertIsNone(p["axes"]["light"])   # eski kayıtta ışık yok: boş
        self.assertIsNone(p["axes"]["vehicle"])

    def test_legacy_volcano_ortam_select(self):
        p = ah.parse_record({"combo_key": f"volcano_disasters|none|{es.VOLCANIC_BOMBS.lower()}|"
                                          "balcony of a village house facing the erupting volcano##R7+T8|cam",
                             "ortam": "dağ eteği köyü"})
        self.assertEqual(p["axes"]["env"], "mountain_village")
        self.assertEqual(p["axes"]["spot"], "Balcony of a village house facing the erupting volcano")
        old = ah.parse_record({"combo_key": f"volcano_disasters|none|{es.PYROCLASTIC.lower()}|"
                                            "rooftop terrace facing the erupting volcano##P2+Q5|cam", "ortam": ""})
        self.assertIsNone(old["axes"]["env"])   # 18 Eki öncesi: Ortam boş

    def test_legacy_fire_tornado_env_from_spot(self):
        p = ah.parse_record({"combo_key": f"fire_disasters|none|{es.FIRE_TORNADO.lower()}|"
                                          "hillside terrace above a village##T1+U8|cam"})
        self.assertEqual((p["axes"]["env"], p["axes"]["key"]), ("village_woods", "village_woods"))
        old = ah.parse_record({"combo_key": f"fire_disasters|none|{es.FIRE_TORNADO.lower()}|"
                                            "balcony of a roadside house##T1+U6|cam"})
        self.assertIsNone(old["axes"]["spot"])   # 16 Eki öncesi spot: bugünkü listede yok
        self.assertIsNone(old["axes"]["env"])

    def test_legacy_avalanche_setting_line(self):
        prompt = ("0-4s: x. Handheld footage ... no cuts. Setting: steep forested slopes, red timber houses, pale low "
                  "winter sun. Bystanders wear winter civilian clothes.")
        p = ah.parse_record({"combo_key": f"avalanche_disasters|none|{es.AVALANCHE_SKI.lower()}|"
                                          "terrace at the edge of the village##C2+D2|cam", "prompt": prompt})
        self.assertEqual(p["axes"]["env"], {"mountain": "steep forested slopes", "village": "red timber houses",
                                            "light": "pale low winter sun"})
        self.assertEqual(p["axes"]["light"], "pale low winter sun")

    def test_legacy_earthquake_dark_city(self):
        prompt = "Setting: dark grey concrete mid-rise apartment blocks, wide avenue, hazy dusty morning. Bystanders."
        p = ah.parse_record({"combo_key": f"earthquake_disasters|none|{es.EARTHQUAKE_APARTMENT.lower()}|"
                                          "rooftop terrace of a building across the street##P4+Q4|cam",
                             "prompt": prompt})
        self.assertEqual(p["axes"]["env"], {"city": "concrete mid-rise apartment blocks", "street": "wide avenue",
                                            "light": "hazy dusty morning"})

    def test_unparseable_is_empty_not_error(self):
        self.assertIsNone(ah.parse_record({"combo_key": ""}))
        self.assertIsNone(ah.parse_record({"combo_key": "a|b|unknown event|x|y"}))
        p = ah.parse_record({"combo_key": f"avalanche_disasters|none|{es.AVALANCHE_SKI.lower()}|"
                                          "terrace at the edge of the village##C2+D2|cam", "prompt": "no setting"})
        self.assertIsNone(p["axes"]["env"])
        broken = ah.parse_record({"eksenler": "{bozuk", "combo_key": "urban_city_disasters|none|flash flooding in "
                                                                       "city streets|downtown city center##V1+D2|c"})
        self.assertEqual(broken["source"], "eski")


class TestNotionSuccess(_Quiet):
    def test_last_two_excluded_on_every_axis(self):
        e = es.MUDSLIDE   # 3 spot, 3 ışık, 4 araç, kişi 3-6
        s = sk.EVENT_SKELETONS[e]
        spots, lights = list(s["spots"]), list(s["weather"])
        vehicles = [v for v, _ in es.EVENT_VEHICLES[e]]
        records = [rec(e, {"spot": spots[0], "light": lights[0], "vehicle": vehicles[0], "people": 3}),
                   rec(e, {"spot": spots[1], "light": lights[1], "vehicle": vehicles[1], "people": 4})]
        for seed in range(25):
            scene = self.scene(e, records, seed=seed)
            ax = scene["structure"]["axes"]
            self.assertEqual(ax["spot"], spots[2])
            self.assertNotIn(ax["light"], lights[:2])   # 21 Eki (Aşama 5): ışık listesi genişledi
            self.assertIn(ax["vehicle"], vehicles[2:])
            self.assertIn(ax["people"], (5, 6))
            self.assertEqual(scene["trace"]["axes_source"], "notion")
        line = scene["structure"]["axes_line"]
        self.assertTrue(line.startswith("Eksenler: spot="))
        self.assertIn("Tekrar önleme (notion): elenen spot:", line)

    def test_single_option_axis_not_excluded(self):
        e = es.MARINA_TORNADO   # tek spot
        spot = next(iter(sk.EVENT_SKELETONS[e]["spots"]))
        scene = self.scene(e, [rec(e, {"spot": spot}), rec(e, {"spot": spot})])
        self.assertEqual(scene["spot"], spot)
        self.assertEqual(scene["structure"]["axes"]["spot"], spot)

    def test_fire_tornado_env_and_spot(self):
        e = es.FIRE_TORNADO
        records = [rec(e, {"env": "forest_edge", "spot": es.FIRE_TOR_ENVS["forest_edge"]["spots"][0]}),
                   rec(e, {"env": "tree_street", "spot": es.FIRE_TOR_ENVS["tree_street"]["spots"][0]})]
        for seed in range(15):
            ax = self.scene(e, records, seed=seed)["structure"]["axes"]
            self.assertEqual(ax["env"], "village_woods")
            self.assertEqual(ax["key"], "village_woods")

    def test_avalanche_category_history_blocks_spot_and_env(self):
        # köy ve orman 2 spot (son 1), ortam ekseni son 2; kategori ortak (başka çığ olayının kaydı da sayılır)
        last_spot = "Terrace at the edge of the village"
        env = {"mountain": "jagged rocky peaks", "village": "dark timber chalets", "light": "heavy overcast sky"}
        records = [rec(es.AVALANCHE_SKI, {"spot": last_spot, "env": env, "light": env["light"]})]
        for seed in range(15):
            ax = self.scene(es.AVALANCHE_VILLAGE, records, seed=seed)["structure"]["axes"]
            self.assertNotEqual(ax["spot"], last_spot)
            self.assertNotEqual(ax["env"]["mountain"], env["mountain"])
            self.assertNotEqual(ax["light"], env["light"])

    def test_volcano_env_spot_light(self):
        e = es.VOLCANIC_BOMBS
        spots = list(sk.EVENT_SKELETONS[e]["spots"])
        lights = list(sk.VOLCANO_WEATHER_WEIGHTS[e])
        records = [rec(e, {"env": "pastel_town", "spot": spots[0], "light": lights[0]}),
                   rec(e, {"env": "suburb", "spot": spots[1], "light": lights[1]})]
        for seed in range(15):
            ax = self.scene(e, records, seed=seed)["structure"]["axes"]
            self.assertNotIn(ax["env"], ("pastel_town", "suburb"))
            self.assertEqual(ax["spot"], spots[2])
            self.assertNotIn(ax["light"], lights[:2])

    def test_region_view_from_notion(self):
        records = [rec(es.FLOOD, {"view": v, "spot": "Downtown city center"}) for v in list(sk.REGION_VIEWS)[:5]]
        scene = self.scene(es.FLOOD, records)
        self.assertEqual(scene["structure"]["axes"]["view"], list(sk.REGION_VIEWS)[5])

    def test_eksenler_json_written_shape(self):
        scene = self.scene(es.EARTHQUAKE_OLD_STREET, [])
        data = json.loads(scene["structure"]["axes_json"])
        self.assertEqual(data["event"], es.EARTHQUAKE_OLD_STREET)
        self.assertEqual(set(data["axes"]), set(ah.AXIS_KEYS))
        self.assertIn("excluded", data)
        self.assertEqual(ah.parse_record({"eksenler": scene["axes_json"]})["axes"], data["axes"])


class TestNotionFailure(_Quiet):
    def test_read_failure_does_not_stop_and_warns(self):
        def boom(domain):
            raise RuntimeError("Notion 502")
        scene = self.scene(es.SLOPE, loader=boom)
        self.assertEqual(scene["trace"]["axes_source"], "bellek")
        self.assertEqual(scene["structure"]["axes_warning"], cp.HISTORY_WARNING)
        self.assertIn(cp.HISTORY_WARNING, scene["structure"]["axes_line"])
        info = {"prompt": scene["prompt"], "story": scene["story"], "style_suffix": scene["style_suffix"],
                "axes_line": scene["structure"]["axes_line"]}
        self.assertIn(cp.HISTORY_WARNING, format_final_prompt(info)[1])

    def test_failure_falls_back_to_process_memory(self):
        def boom(domain):
            raise RuntimeError("Notion yok")
        first = self.scene(es.SLOPE, loader=boom, seed=3)["structure"]["axes"]
        for seed in range(10):   # 2 spot: son 1 elenir (süreç hafızası)
            second = self.scene(es.SLOPE, loader=boom, seed=seed)["structure"]["axes"]
            self.assertNotEqual(second["spot"], first["spot"])
            es._AXES_MEMORY[es.SLOPE] = [first]

    def test_non_list_result_is_failure(self):
        scene = self.scene(es.SLOPE, loader=lambda d: MagicMock())
        self.assertEqual(scene["structure"]["axes_warning"], cp.HISTORY_WARNING)

    def test_no_loader_keeps_old_behaviour(self):
        random.seed(4)
        a = ps.build(es.SLOPE)
        self.assertEqual(a["trace"]["axes_source"], "yok")
        self.assertIsNone(a["structure"]["axes_warning"])


class TestCancelledRecords(_Quiet):
    def test_cancelled_record_counts(self):
        e = es.HELICOPTER   # 2 spot: son 1
        spots = list(sk.EVENT_SKELETONS[e]["spots"])
        records = [rec(e, {"spot": spots[0]}, status=nl.STATUS_CANCELLED)]
        for seed in range(10):
            self.assertEqual(self.scene(e, records, seed=seed)["spot"], spots[1])

    def test_query_has_no_status_filter(self):
        page = {"properties": {"Combo Key": {"rich_text": [{"plain_text": "fire_disasters|none|x|y|z"}]},
                               "Eksenler": {"rich_text": [{"plain_text": "{}"}]},
                               "Durum": {"select": {"name": nl.STATUS_CANCELLED}}}}
        with patch.object(nl.settings, "NOTION_ENABLED", True), patch.object(nl.settings, "IS_DRY_RUN", False), \
                patch.object(nl, "_notion_request", return_value={"results": [page]}) as req:
            t = nl.NotionTracker()
            t.enabled = True
            out = t.get_axes_records("fire_disasters")
        payload = req.call_args.kwargs["json"]
        self.assertNotIn("Durum", json.dumps(payload, ensure_ascii=False))
        self.assertEqual(payload["filter"]["rich_text"]["starts_with"], "fire_disasters|")
        self.assertEqual(out[0]["status"], nl.STATUS_CANCELLED)
        self.assertEqual(out[0]["eksenler"], "{}")

    def test_disabled_notion_returns_none(self):
        with patch.object(nl.settings, "IS_DRY_RUN", True):
            self.assertIsNone(nl.NotionTracker().get_axes_records("fire_disasters"))

    def test_schema_has_eksenler(self):
        self.assertEqual(nl.EXTRA_PROPERTIES[nl.AXES_PROPERTY], {"rich_text": {}})
        self.assertEqual(nl.AXES_PROPERTY, ah.AXES_PROPERTY)


class TestDeployScenario(_Quiet):
    """Her üretim arasında deploy (süreç hafızası silinir), geçmiş sadece sahte Notion'dan: tekrar yine 0."""

    def test_no_repeat_after_every_deploy(self):
        import variety_report as vr
        for e in es.AVALANCHE_EVENTS + es.EARTHQUAKE_EVENTS + (es.FIRE_TORNADO,):
            with self.subTest(event=e):
                m = vr.measure(vr.simulate(e, runs=12, seed=7, reset_each=True, notion=True))
                self.assertEqual(m["errors"], 0)
                self.assertEqual(m["rep_spot"], 0)
                self.assertEqual(m["rep_environment"], 0)
                self.assertEqual(m["copies"], 0)

    def test_every_lru_axis_no_consecutive_repeat(self):
        import core.frame_axis as fx
        import variety_report as vr
        for e in ps.active_events():
            with self.subTest(event=e):
                rows = vr.simulate(e, runs=10, seed=3, reset_each=True, notion=True)
                m = vr.measure(rows)
                self.assertEqual(m["errors"], 0)
                single = {a for a, n in vr.option_counts(e).items() if n == 1}
                for axis in vr.LRU_AXES:
                    # kadraj: aşağıda (tek güvenli kadraj); ortam ve ön plan: aşağıda (uyum / bütçe zorunlu)
                    if axis not in single and axis not in ("kadraj", "environment", "on_plan", "key_visual"):
                        self.assertEqual(m[f"rep_{axis}"], 0, axis)
                # 21 Eki (Aşama 5): ortam tekrarı sadece spotla uyumlu ortamlar son 2 elenince bitiyorsa; ön plan
                # tekrarı sadece K5 sığma koruması devreye girdiyse (bütçe zorunlu)
                import core.scene_env as sv
                import core.opening_axis as ox
                envs = [r["environment"] for r in rows]
                keys = [r["key_visual"] for r in rows]
                # 21 Eki (Aşama 6): açılış tekrarı sadece ortam + beat çakışması son 2 dışında açılış bırakmadıysa
                for i in range(1, len(rows)):
                    if e in ox.OPENINGS and keys[i] == keys[i - 1]:
                        b2, b3 = rows[i]["beats"].split("+")
                        env = rows[i]["environment"] if e in sv.SCENE_ENVS else None
                        letters = {(ox.text(e, o) or es.EVENT_KEY_VISUAL[e]): o for o in ox.options(e)}
                        recent = {letters[k] for k in keys[max(0, i - 2):i]}
                        left = [o for o in ox.allowed(e, env, b2, b3) if o not in recent]
                        self.assertEqual(left, [], (e, i, rows[i]["beats"], env))
                for i in range(1, len(rows)):
                    a, b = rows[i - 1], rows[i]
                    if e in sv.SCENE_ENVS and a["environment"] == b["environment"]:
                        left = [x for x in sv.compatible_envs(e, b["spot"]) if x not in envs[max(0, i - 2):i]]
                        self.assertEqual(left, [], (e, i, b["spot"], envs[:i + 1]))
                    if a["on_plan"] == b["on_plan"] and b["on_plan"] != "—":
                        self.assertTrue(b["fit_guard"], (e, i, a, b))
                # 21 Eki (Aşama 4): kadraj tekrarı sadece seçilen beat'lerin dışlamaları tek güvenli kadraj bıraktıysa
                beats = es.EVENT_BEATS[e]["excluded_spots"]
                # 22 Eki: ön plandaki gibi K5 sığma koruması devreye girdiyse de (bütçe zorunlu; uzun heyelan beat'leri)
                for a, b in zip(rows, rows[1:]):
                    if a["kadraj"] != b["kadraj"] or b["fit_guard"]:
                        continue
                    b2, b3 = b["beats"].split("+")
                    risky = set(beats.get(b2, set())) | set(beats.get(b3, set()))
                    pool = (list(es.FIRE_TOR_ENVS[es.fire_env_of_spot(b["spot"])]["spots"]) if e == es.FIRE_TORNADO
                            else sk.view_spots(e, None if b["environment"] not in sk.REGION_VIEWS else b["environment"]))
                    types = {f["type"] for f in fx.all_frames(e, b["spot"], pool, risky)}
                    self.assertEqual(types, {b["kadraj"]}, (e, a, b))


class TestPipelineOrder(_Quiet):
    """Eksenler Onay'dan önce yazılır; iptalde kayıt silinmez, ❌ İptal olur."""

    def test_axes_written_before_approval_and_cancel_keeps_record(self):
        import main
        from test_zero_leak import Harness

        class Deny(main.PipelineReporter):
            needs_approval = True

            async def approve(self, info):
                self.info = info
                return False

        reporter = Deny()
        with patch.object(main, "PipelineReporter", return_value=reporter):
            h = Harness().run()
        self.assertEqual(h.result.get("reason"), "cancelled", h.result)
        t = h.trackers[-1]
        names = [c[0] for c in t.method_calls]
        self.assertIn("record_axes", names)
        first_status = next(i for i, c in enumerate(t.method_calls)
                            if c[0] == "update_status" and c[1][0] == nl.STATUS_AWAITING_APPROVAL)
        self.assertLess(names.index("record_axes"), first_status)
        self.assertNotIn("delete", " ".join(names))
        cancel = [c for c in t.method_calls if c[0] == "update_status" and c[1][0] == nl.STATUS_CANCELLED]
        self.assertEqual(len(cancel), 1)
        axes = json.loads(t.record_axes.call_args[0][0])
        self.assertEqual(axes["event"], es.FLOOD)
        self.assertIn("Eksenler:", reporter.info["axes_line"])
        h.create.assert_not_called()   # iptal: Kie çağrılmadı


if __name__ == "__main__":
    unittest.main()
