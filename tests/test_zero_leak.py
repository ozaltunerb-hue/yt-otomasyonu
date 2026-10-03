#!/usr/bin/env python3
"""
Sıfır sızıntı (4 Eki 2026, Bahadır): yapılandırılmış olayda (sel) hiçbir hata Kie'ye istek göndermez.
main.run_pipeline gerçek KieClient ile çalışır; sadece HTTP uçları (_create_task, polling, kredi), GPT, preflight,
Notion, indirme ve arşiv sahtedir. Kie'ye istek = _create_task çağrısı; her senaryoda sayılır. Ağ çağrısı yok.
"""
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
import core.creative_pipeline as cp
import core.event_structure as es
import core.prompt_generator as pg
import core.prompt_sanitizer as ps
import main
from config import settings
from infrastructure.kie_client import ContentFilterError, KieClient
from infrastructure.notion_logger import NotionTracker

FLOOD = es.FLOOD
VIEW = "us_coastal_town"
VEHICLE = "pickup truck"
KEY = es.EVENT_KEY_VISUAL[FLOOD]
MOTION = {"per_second": [2.0, 3.0], "opening_avg": 2.5, "rest_avg": 3.0, "opening_ratio": 0.8, "peak_second": 1}


def slices(s2=None, s3=None, s1=None):
    return {"slice_1_rest": s1 or "It swallows the curbs and pours between the parked cars.",
            "slice_2": s2 or f"The {VEHICLE} is caught by the current, turns sideways and is dragged down the street.",
            "slice_3": s3 or "A lamppost topples into the current and crashes into the churning brown water."}


SAFE = (False, {"risk_score": 1, "risk_reasons": [], "preflight_passed": True, "attempts": 1})


def preflight_seq(*results):
    """Her çağrıda sıradaki sonuç: "safe" ya da ("unsafe", yeniden_yazılmış_metin)."""
    calls = []

    async def fake(prompt):
        calls.append(prompt)
        r = results[min(len(calls), len(results)) - 1]
        if r == "safe":
            return prompt, SAFE[0], dict(SAFE[1])
        return r[1], True, {"risk_score": 8, "risk_reasons": ["graphic"], "preflight_passed": False, "rewritten": True}
    fake.calls = calls
    return fake


class Harness:
    def __init__(self, gpt=None, preflight=None, create=None, combos=None, history=None, rewrite=None):
        self.gpt_responses = list(gpt or [slices()])
        self.gpt_calls = []
        self.preflight = preflight or preflight_seq("safe")
        self.create = create or AsyncMock(return_value="task-1")
        self.combos = combos
        self.history = history
        self.rewrite = rewrite
        self.trackers = []
        self.gen_calls = 0
        self.free_rewriter = AsyncMock(side_effect=AssertionError("serbest metin yeniden yazıcı çağrıldı"))

    async def fake_gpt(self, system, user, temperature=0.85, model="gpt-4o", json_schema=None):
        self.gpt_calls.append({"system": system, "user": user, "json_schema": json_schema})
        r = self.gpt_responses[min(len(self.gpt_calls), len(self.gpt_responses)) - 1]
        if isinstance(r, Exception):
            raise r
        return r

    def new_tracker(self):
        t = MagicMock()
        t.page_id = None
        if isinstance(self.history, Exception):
            t.get_recent_history.side_effect = self.history
        else:
            t.get_recent_history.return_value = []
        t.get_recent_beat1_verbs.return_value = []
        t.create_entry.side_effect = lambda *a, **k: setattr(t, "page_id", "p")
        self.trackers.append(t)
        return t

    async def gen(self, cfg):
        self.gen_calls += 1
        return await pg.generate_creative_prompts(cfg)

    def run(self):
        es._BEAT_MEMORY.clear()
        client = KieClient()
        patches = [
            patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "YOUTUBE_ENABLED", False),
            patch.object(settings, "POLL_INITIAL_WAIT", 0),
            patch.object(main, "load_used_combos", side_effect=self.combos) if isinstance(self.combos, Exception)
            else patch.object(main, "load_used_combos", return_value=[]),
            patch.object(main, "NotionTracker", side_effect=self.new_tracker),
            patch.object(main, "generate_prompts", self.gen),
            patch.object(main, "KieClient", return_value=client),
            patch.object(main, "download_video", MagicMock(return_value="v.mp4")),
            patch.object(main, "motion_profile", MagicMock(return_value=MOTION)),
            patch.object(main, "upload_to_youtube", AsyncMock()),
            patch.object(main, "cleanup_video"), patch.object(main, "new_archive_dir", return_value="arsiv-test"),
            patch.object(main, "write_meta"), patch.object(main, "save_video", return_value="arsiv-test/v.mp4"),
            patch.object(pg, "_call_gpt", self.fake_gpt),
            patch.object(pg, "_generate_metadata", AsyncMock(return_value={"youtube_title": "t", "tags": []})),
            patch.object(ps, "gpt_preflight_check", self.preflight),
            patch.object(ps, "gpt_rewrite_rejected_prompt", self.free_rewriter),
            patch.object(client, "_create_task", self.create),
            patch.object(client, "_poll_for_result", AsyncMock(return_value="https://cdn/v.mp4")),
            patch.object(client, "get_credit", AsyncMock(return_value=100.0)),
            patch.object(es, "choose_beats", lambda *a, **k: ("V1", "D2")),
            patch.object(es, "choose_vehicle", lambda v, rng=None: VEHICLE),
        ]
        if self.rewrite:
            patches.append(patch.object(cp, "rewrite_structured", self.rewrite))
        for p in patches:
            p.start()
        try:
            self.result = asyncio.run(main.run_pipeline(skip_upload=True, domain="urban_city_disasters",
                                                        event=FLOOD, view=VIEW))
        finally:
            for p in reversed(patches):
                p.stop()
        return self

    @property
    def sent_prompts(self):
        return [c.args[1] for c in self.create.call_args_list]


def expected_prompt(sl=None):
    spec = es.build_spec(FLOOD, None, "Downtown city center", VIEW, "V1", "D2", VEHICLE)
    return spec, es.parse_slices(sl or slices())


class TestHappyPath(unittest.TestCase):
    def test_structured_prompt_sent_once(self):
        h = Harness().run()
        self.assertTrue(h.result.get("success"), h.result)
        self.assertEqual(len(h.sent_prompts), 1)
        p = h.sent_prompts[0]
        self.assertTrue(p.startswith(f"0-4s: {KEY} "))
        self.assertIn(" 4-9s: The pickup truck", p)
        self.assertIn(" 9-15s: A lamppost", p)
        self.assertEqual(h.gpt_calls[0]["json_schema"], es.SLICE_SCHEMA)
        h.free_rewriter.assert_not_called()


class TestNothingReachesKie(unittest.TestCase):
    """Her hata: _create_task (Kie'ye istek) hiç çağrılmaz."""

    def assertNoKie(self, h):
        h.create.assert_not_called()
        h.free_rewriter.assert_not_called()

    def test_gpt_api_error(self):
        h = Harness(gpt=[RuntimeError("GPT API hatası")]).run()
        self.assertNoKie(h)
        self.assertFalse(h.result["success"])
        self.assertIn("GPT API hatası", h.result["error"])

    def test_bad_json_missing_field_extra_field_empty(self):
        for bad in ({"slice_1_rest": "a", "slice_2": "b"}, {**slices(), "story": "x"}, {**slices(), "slice_3": " "},
                    ["liste"], ValueError("Expecting value: line 1 column 1")):
            with self.subTest(bad=repr(bad)[:40]):
                h = Harness(gpt=[bad, slices()]).run()
                self.assertNoKie(h)
                self.assertFalse(h.result["success"])
                self.assertEqual(len(h.gpt_calls), 1)          # deneme yemez, ikinci yanıt istenmez
                self.assertEqual(h.gen_calls, 1)               # yeni senaryo denenmez

    def test_label_or_camera_inside_slice_three_times(self):
        bad = slices(s3="At 9-15s the camera shows a lamppost topple into the current and crash down.")
        h = Harness(gpt=[bad]).run()
        self.assertNoKie(h)
        self.assertEqual(h.result["reason"], "no_valid_scenario")
        self.assertEqual(len(h.gpt_calls), cp.MAX_ATTEMPTS)

    def test_beat_missing_three_times(self):
        h = Harness(gpt=[slices(s3="A low wall collapses into the water as the street fills with debris.")]).run()
        self.assertNoKie(h)
        self.assertEqual(h.result["reason"], "no_valid_scenario")
        self.assertIn("9-15s: seçilen olay (D2) görünmüyor", h.result["error_summary"])

    def test_preflight_unsafe_twice_stops(self):
        h = Harness(gpt=[slices(), slices(s1="It rushes over the curbs and floods the low porches.")],
                    preflight=preflight_seq(("unsafe", "a calm street"), ("unsafe", "a calm street"))).run()
        self.assertNoKie(h)
        self.assertEqual(h.result["reason"], "structure_check")
        self.assertIn("Preflight yeniden yazımdan sonra da riskli", h.result["error"])
        self.assertEqual(h.gen_calls, 1)                       # yeni senaryo denenmez
        self.assertEqual(len(h.gpt_calls), 2)                  # ilk yazım + tek yeniden yazım

    def test_rewrite_breaks_rules(self):
        # Preflight riskli; yeniden yazım kalite kapısında 3 denemede de kalır -> Kie'ye hiç istek yok
        bad_rewrite = slices(s2="The sedan rocks gently in the water as the rain keeps falling.")
        h = Harness(gpt=[slices(), bad_rewrite], preflight=preflight_seq(("unsafe", "x"), "safe")).run()
        self.assertNoKie(h)
        self.assertEqual(h.result["reason"], "structure_check")
        self.assertIn("Ret sonrası yeniden yazım kural kapısından geçmedi", h.result["error"])
        self.assertEqual(len(h.gpt_calls), 1 + cp.MAX_ATTEMPTS)

    def test_tampered_rewrite_caught_before_submit(self):
        # Yeniden yazım kilit görseli silen bir metin döndürse (structure güncellenmeden), son denetim yakalar
        async def tampered(structure, reason, call_gpt):
            return "0-4s: A low foamy wave rolls in. 4-9s: x. 9-15s: y."
        h = Harness(preflight=preflight_seq(("unsafe", "x"), "safe"), rewrite=tampered).run()
        self.assertNoKie(h)
        self.assertEqual(h.result["reason"], "structure_check")
        self.assertIn("son denetimden geçmedi", h.result["error"])

    def test_preflight_text_never_used(self):
        # Preflight'ın kilit görseli silen kendi metni gönderilmez; bizim yazar yeniden yazar
        h = Harness(gpt=[slices(), slices(s1="It rushes over the curbs and floods the low porches.")],
                    preflight=preflight_seq(("unsafe", "A gentle stream. 4-9s: car. 9-15s: pole."), "safe")).run()
        self.assertTrue(h.result.get("success"), h.result)
        self.assertEqual(len(h.sent_prompts), 1)
        self.assertTrue(h.sent_prompts[0].startswith(f"0-4s: {KEY} It rushes over the curbs"))
        self.assertNotIn("gentle stream", h.sent_prompts[0])
        h.free_rewriter.assert_not_called()

    def test_kie_rejects_twice_stops(self):
        create = AsyncMock(side_effect=[ContentFilterError("flagged"), ContentFilterError("flagged")])
        h = Harness(gpt=[slices(), slices(s1="It rushes over the curbs and floods the low porches.")],
                    create=create).run()
        self.assertEqual(create.call_count, 2)                 # ilk gönderim + tek yeniden yazım
        for p in h.sent_prompts:
            self.assertTrue(p.startswith(f"0-4s: {KEY} "))
        self.assertTrue(h.sent_prompts[1].startswith(f"0-4s: {KEY} It rushes over the curbs"))
        self.assertEqual(h.result["reason"], "structure_check")
        self.assertIn("Kie içerik filtresi yeniden yazımdan sonra da reddetti", h.result["error"])
        self.assertEqual(h.gen_calls, 1)
        h.free_rewriter.assert_not_called()

    def test_kie_reject_rewrite_passes_on_third_attempt(self):
        # Kie reddeder; yeniden yazım kalite kapısında 2 kez kalır, 3.'de geçer -> Kie'ye toplam 2 istek
        bad = slices(s2="The sedan rocks gently in the water as the rain keeps falling.")
        good = slices(s1="It rushes over the curbs and floods the low porches.")
        create = AsyncMock(side_effect=[ContentFilterError("flagged"), "task-2"])
        h = Harness(gpt=[slices(), bad, bad, good], create=create).run()
        self.assertTrue(h.result.get("success"), h.result)
        self.assertEqual(create.call_count, 2)
        self.assertEqual(len(h.gpt_calls), 4)
        self.assertIn("The video safety check rejected the previous text", h.gpt_calls[1]["user"])
        self.assertIn("YOUR PREVIOUS ANSWER WAS REJECTED", h.gpt_calls[2]["user"])
        self.assertTrue(h.sent_prompts[1].startswith(f"0-4s: {KEY} It rushes over the curbs"))
        h.free_rewriter.assert_not_called()

    def test_kie_reject_rewrite_fails_three_times(self):
        # Kie reddeder; yeniden yazım 3 denemede de kalır -> Kie'ye ikinci istek gitmez
        bad = slices(s2="The sedan rocks gently in the water as the rain keeps falling.")
        create = AsyncMock(side_effect=[ContentFilterError("flagged"), "task-2"])
        h = Harness(gpt=[slices(), bad, bad, bad], create=create).run()
        self.assertEqual(create.call_count, 1)
        self.assertEqual(len(h.gpt_calls), 1 + cp.MAX_ATTEMPTS)
        self.assertEqual(h.result["reason"], "structure_check")
        self.assertIn("Ret sonrası yeniden yazım kural kapısından geçmedi", h.result["error"])
        self.assertEqual(h.gen_calls, 1)
        h.free_rewriter.assert_not_called()

    def test_kie_rejects_once_then_ok(self):
        create = AsyncMock(side_effect=[ContentFilterError("flagged"), "task-2"])
        h = Harness(gpt=[slices(), slices(s1="It rushes over the curbs and floods the low porches.")],
                    create=create).run()
        self.assertTrue(h.result.get("success"), h.result)
        self.assertEqual(create.call_count, 2)

    def test_notion_used_combos_fails(self):
        h = Harness(combos=RuntimeError("Notion get_used_combos 3 denemede de başarısız"))
        with self.assertRaises(RuntimeError):
            h.run()
        h.create.assert_not_called()
        self.assertEqual(h.gen_calls, 0)

    def test_notion_recent_history_fails(self):
        h = Harness(history=RuntimeError("Notion get_recent_history başarısız"))
        with self.assertRaises(RuntimeError):
            h.run()
        h.create.assert_not_called()
        self.assertEqual(h.gen_calls, 0)

    def test_pool_without_candidates(self):
        b = es.EVENT_BEATS[FLOOD]
        saved = b["excluded_pairs"]
        es._BEAT_MEMORY.clear()
        try:
            b["excluded_pairs"] = {(v, d) for v in b["slice_2"] for d in b["slice_3"]}
            calls = []

            async def gpt(*a, **k):
                calls.append(1)
                return slices()
            with self.assertRaises(es.StructureError):
                asyncio.run(cp.build_creative_scene("urban_city_disasters", FLOOD, [], [], gpt, view=VIEW))
            self.assertEqual(calls, [])
        finally:
            b["excluded_pairs"] = saved


class TestSubmitIssues(unittest.TestCase):
    def setUp(self):
        spec, sl = expected_prompt()
        self.structure = {"spec": spec, "slices": sl}
        self.info = {"story": es.assemble_story(spec, sl), "style_suffix": spec["suffix"],
                     "prompt": es.assemble_prompt(spec, sl)}

    def test_clean(self):
        self.assertEqual(cp.submit_issues(self.structure, self.info), [])

    def test_suffix_changed(self):
        info = {**self.info, "style_suffix": self.info["style_suffix"] + " Zoom in."}
        self.assertIn("stil eki gönderimde değişmiş", cp.submit_issues(self.structure, info))

    def test_prompt_or_story_changed(self):
        info = {**self.info, "prompt": self.info["prompt"].replace("waist-high", "ankle-deep")}
        self.assertTrue(cp.submit_issues(self.structure, info))
        info = {**self.info, "story": self.info["story"].replace("4-9s:", "4–9s:")}
        self.assertTrue(cp.submit_issues(self.structure, info))


class TestNotionFailClosed(unittest.TestCase):
    def test_recent_history_raises(self):
        t = NotionTracker()
        with patch.object(t, "enabled", True), patch.object(settings, "IS_DRY_RUN", False), \
                patch("infrastructure.notion_logger._notion_request", side_effect=ConnectionError("Notion yok")):
            with self.assertRaises(RuntimeError):
                t.get_recent_history()

    def test_production_requires_notion(self):
        env = {"NOTION_SOCIAL_TOKEN": "", "NOTION_API_TOKEN": "", "NOTION_DB_YOUTUBE_OTOMASYON": "", "DRY_RUN": "0",
               "ENV": "production"}
        with patch.dict(os.environ, env):
            with self.assertRaises(EnvironmentError):
                config.Config()
        with patch.dict(os.environ, {**env, "DRY_RUN": "1"}):
            self.assertFalse(config.Config().NOTION_ENABLED)   # sadece deneme modunda kapalı olabilir



class TestReporting(unittest.TestCase):
    """Tur 4: Telegram "Ayrıntı" / Notion gövdesi ve kuru prova çıktısı yapılandırılmış hattı gösterir."""

    def scene(self):
        es._BEAT_MEMORY.clear()

        async def gpt(system, user, **kw):
            return slices()
        with patch.object(es, "choose_beats", lambda *a, **k: ("V1", "D2")), \
                patch.object(es, "choose_vehicle", lambda v, rng=None: VEHICLE):
            return asyncio.run(cp.build_creative_scene("urban_city_disasters", FLOOD, [], [], gpt, view=VIEW))

    def test_detail_sections(self):
        from core.trace_format import format_generation, sections_to_text
        text = sections_to_text(format_generation(self.scene()["trace"]))
        for part in ("🔍 1. Seçim (kod)", f"Görünüm: {VIEW} (menü)", f"Kilit görsel (0-4s): {KEY}",
                     f"Araç: {VEHICLE}", "4-9s olayı (V1): the pickup truck is caught by the current",
                     "9-15s olayı (D2): a lamppost topples into the current", "olay çifti V1+D2",
                     "🔍 2. GPT-4o dilimleri", "Deneme 1 · ✅ geçti", "🔍 3. Hikâye", "kelime (etiketsiz)",
                     f"0-4s: {KEY} It swallows"):
            self.assertIn(part, text)

    def test_other_creative_detail_unchanged(self):
        from core.trace_format import _format_creative, format_generation
        trace = {"pipeline": "creative", "event": "x", "attempts": [], "story": "s", "story_words": 1}
        self.assertEqual(format_generation(trace), _format_creative(trace, {}))

    def test_final_prompt_rewrite_note(self):
        from core.trace_format import format_final_prompt
        info = {"prompt": "p", "story": "b", "story_before_preflight": "a", "style_suffix": "",
                "preflight": {"risk_score": 8, "structured_rewrite": True}}
        self.assertIn("Yapılandırılmış yeniden yazım", format_final_prompt(info)[1])
        info["preflight"] = {"risk_score": 8}
        self.assertNotIn("Yapılandırılmış yeniden yazım", format_final_prompt(info)[1])

    def test_dry_run_writes_output_and_stops_on_structure_error(self):
        import json
        import tempfile
        import scripts.dry_run_full as dr
        out = os.path.join(tempfile.mkdtemp(), "out.json")
        es._BEAT_MEMORY.clear()
        with patch.object(pg, "_call_gpt", AsyncMock(return_value={"story": "x"})), \
                patch.object(settings, "IS_DRY_RUN", False):
            asyncio.run(dr.main_creative(out, only=[FLOOD], per_event=2, max_calls=9))
        rows = json.load(open(out, encoding="utf-8"))["rows"]
        self.assertEqual(rows[0]["status"], "stopped")
        self.assertIn("yapılandırılmış hat durdu", rows[0]["reason"])
        self.assertEqual(rows[1]["status"], "not_run")       # durduktan sonra devam edilmez

    def test_dry_run_passes_schema_and_shows_beats(self):
        import json
        import tempfile
        import scripts.dry_run_full as dr
        out = os.path.join(tempfile.mkdtemp(), "out.json")
        es._BEAT_MEMORY.clear()
        calls, chosen = [], {}

        def vehicle(view, rng=None):
            # görünüm rastgele gelir; araç o görünümün listesinden
            chosen["v"] = es.REGION_VEHICLES[view][0][0]
            return chosen["v"]

        async def fake(system, user, temperature=0.85, model="gpt-4o", json_schema=None):
            calls.append(json_schema)
            return slices(s2=f"The {chosen['v']} is caught by the current, turns sideways and is dragged down the street.")
        with patch.object(pg, "_call_gpt", fake), patch.object(settings, "IS_DRY_RUN", False), \
                patch.object(es, "choose_beats", lambda *a, **k: ("V1", "D2")), \
                patch.object(es, "choose_vehicle", vehicle):
            asyncio.run(dr.main_creative(out, only=[FLOOD], per_event=1, max_calls=3))
        row = json.load(open(out, encoding="utf-8"))["rows"][0]
        self.assertEqual(calls, [es.SLICE_SCHEMA])
        self.assertEqual((row["status"], row["beats"], row["vehicle"]), ("passed", "V1+D2", chosen["v"]))
        self.assertIn(row["view"], es.REGION_VEHICLES)
        self.assertEqual(set(row["slices"]), set(es.SLICE_FIELDS))
        self.assertTrue(row["prompt"].startswith(f"0-4s: {KEY} "))


if __name__ == "__main__":
    unittest.main()
