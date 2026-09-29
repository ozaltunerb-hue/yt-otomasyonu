#!/usr/bin/env python3
"""
TUR 29: altyapı (task ID, kurtarma, polling, loglar, Notion gövdesi, olay denetimi, kapı düzeltmeleri),
Telegram TEST modu, 🔍 Ayrıntı / ✋ Onay, 👍/👎 ve ölçüm (meta.json). Ağ çağrısı yok: GPT, Kie, Notion,
Telegram ve YouTube sahte. Ücretli hiçbir çağrı yapılmaz; arşiv geçici klasöre yazılır.
"""
import asyncio
import concurrent.futures
import json
import logging
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import bot
import core.prompt_generator as pg
import core.prompt_sanitizer as ps
import main
from config import settings
from core.creative_engine import DOMAIN_ATTRIBUTES, SIDE_LAUNCH_EVENT
from core.trace_format import count_constraints, format_final_prompt, format_generation, split_message, word_diff
from infrastructure import kie_client as kc
from infrastructure import notion_logger as nl
from infrastructure.archive import meta_path
from infrastructure.kie_client import KieClient, KieTimeoutError, SubmissionCancelled
from infrastructure.notion_logger import STATUS_AWAITING_APPROVAL, STATUS_CANCELLED, STATUS_RECOVERED, STATUS_TEST_DONE

CHAT = 424242
FERRY_EVENT = "Lashing chain snaps and a parked car breaks loose"
STORY = ("A lashing chain snaps on the passenger car ferry's open deck and a parked car breaks loose, skidding "
         "sideways as three deckhands lunge for the rail. The car keeps sliding with every roll.")
SUFFIX = "Static fixed-mount security CCTV camera, normal lens, no fisheye or drone view; the frame never moves, zooms or cuts."


_NO_NETWORK = []


def setUpModule():
    """Güvenlik ağı: bu modülde gerçek OpenAI istemcisi kurulursa test patlar (ücretli çağrı olmasın)."""
    import openai
    for name in ("OpenAI", "AsyncOpenAI"):
        p = patch.object(openai, name, side_effect=AssertionError(f"Testte gerçek openai.{name} kuruldu"))
        p.start()
        _NO_NETWORK.append(p)
    p = patch.object(pg, "_get_openai_client", side_effect=AssertionError("Testte gerçek GPT istemcisi istendi"))
    p.start()
    _NO_NETWORK.append(p)


def tearDownModule():
    for p in _NO_NETWORK:
        p.stop()


def _tmp_archive(test):
    d = tempfile.mkdtemp(prefix="arsiv_test_")
    test.addCleanup(shutil.rmtree, d, True)
    p = patch.object(settings, "ARCHIVE_DIR", d)
    p.start()
    test.addCleanup(p.stop)
    return d


def _fake_video():
    fd, path = tempfile.mkstemp(suffix=".mp4")
    with os.fdopen(fd, "wb") as f:
        f.write(b"\0" * 2048)
    return path


# ─────────────────────────── Logger (İŞ 1b) ───────────────────────────

class TestLoggers(unittest.TestCase):
    def test_pipeline_loggers_print_info(self):
        import logger
        for name in ("PromptGenerator", "CreativeEngine", "PromptSanitizer", "NotionLogger", "YouTubeUploader"):
            with self.subTest(name=name):
                self.assertIn(name, logger.PIPELINE_LOGGERS)
                lg = logging.getLogger(name)
                self.assertTrue(lg.isEnabledFor(logging.INFO))
                self.assertTrue(any(isinstance(h, logging.StreamHandler) and h.level <= logging.INFO for h in lg.handlers))


# ─────────────────────────── Kie polling (İŞ 1a) ───────────────────────────

class _Resp:
    def __init__(self, status=200, data=None, text="", bad_json=False):
        self.status_code, self._data, self.text, self._bad = status, data, text, bad_json

    def json(self):
        if self._bad:
            raise ValueError("not json")
        return self._data


def _client_with(responses):
    calls = {"n": 0}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            r = responses[min(calls["n"], len(responses) - 1)]
            calls["n"] += 1
            return r
    return _Client, calls


class TestKiePolling(unittest.TestCase):
    def setUp(self):
        for p in (patch.object(settings, "POLL_INTERVAL", 0), patch.object(settings, "IS_DRY_RUN", False)):
            p.start()
            self.addCleanup(p.stop)

    def _poll(self, responses, max_attempts=5):
        client, calls = _client_with(responses)
        with patch.object(kc.httpx, "AsyncClient", client):
            k = KieClient()
            coro = k._poll_for_result(kc.MODEL_CONFIG["bytedance/seedance-2-fast"], "task123", max_attempts=max_attempts)
            return asyncio.run(coro), calls

    def test_5xx_and_non_json_retried(self):
        ok = _Resp(data={"data": {"state": "success", "resultJson": json.dumps({"resultUrls": ["https://v/1.mp4"]})}})
        url, calls = self._poll([_Resp(502, text="Bad Gateway"), _Resp(200, text="<html>", bad_json=True), ok])
        self.assertEqual(url, "https://v/1.mp4")
        self.assertEqual(calls["n"], 3)

    def test_timeout_carries_task_id(self):
        waiting = _Resp(data={"data": {"state": "waiting"}})
        with self.assertRaises(KieTimeoutError) as cm:
            self._poll([waiting], max_attempts=3)
        self.assertEqual(cm.exception.task_id, "task123")
        self.assertIsInstance(cm.exception, RuntimeError)

    def test_wait_for_task_continues_existing_task(self):
        k = KieClient()
        with patch.object(KieClient, "_poll_for_result", AsyncMock(return_value="u")) as poll:
            self.assertEqual(asyncio.run(k.wait_for_task("t9", max_attempts=7)), "u")
        self.assertEqual(poll.await_args.args[1], "t9")
        self.assertEqual(poll.await_args.kwargs["max_attempts"], 7)


class TestKieHooks(unittest.TestCase):
    def setUp(self):
        for p in (patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "POLL_INITIAL_WAIT", 0),
                  patch.object(ps, "gpt_preflight_check", AsyncMock(return_value=(STORY, False, {"risk_score": 1})))):
            p.start()
            self.addCleanup(p.stop)

    def test_cancel_before_submit_makes_no_paid_call(self):
        create = AsyncMock(return_value="t1")

        async def cancel(info):
            raise SubmissionCancelled("iptal")
        with patch.object(KieClient, "_create_task", create), patch.object(KieClient, "_poll_for_result", AsyncMock()):
            with self.assertRaises(SubmissionCancelled):
                asyncio.run(KieClient().create_video(model=settings.DEFAULT_MODEL, prompt=STORY, style_suffix=SUFFIX,
                                                     before_submit=cancel))
        create.assert_not_awaited()

    def test_task_id_hook_runs_before_polling(self):
        order = []

        async def created(task_id, info):
            order.append(("created", task_id, info["prompt"]))

        async def poll(*a, **k):
            order.append(("poll",))
            return "u"
        with patch.object(KieClient, "_create_task", AsyncMock(return_value="t1")), \
             patch.object(KieClient, "_poll_for_result", side_effect=poll):
            asyncio.run(KieClient().create_video(model=settings.DEFAULT_MODEL, prompt=STORY, style_suffix=SUFFIX,
                                                 on_task_created=created))
        self.assertEqual(order[0][:2], ("created", "t1"))
        self.assertTrue(order[0][2].startswith(STORY.rstrip(".")) and SUFFIX in order[0][2])
        self.assertEqual(order[1], ("poll",))


# ─────────────────────────── Pipeline (İŞ 1-4) ───────────────────────────

def _prompt_data(story=STORY, event=FERRY_EVENT):
    scenario = {"scenario_summary": "A lashing chain snaps and a parked car breaks loose on the ferry.",
                "visible_trigger": "a lashing chain snaps", "visible_start": STORY,
                "physical_movement": "The car slides.", "visible_consequence": "The car keeps sliding."}
    trace = {"domain": "ferry_operations", "event": event, "candidates": [
        {"n": 1, "domain_id": "ferry_operations", "event": event, "environment": "Open vehicle deck",
         "ship": "Passenger Car Ferry", "camera": "fixed_cctv", "summary": "s", "passed": True, "failures": [], "score": 5}],
        "chosen": {"n": 1, "score": 5, "order": [1], "rule": "skor"}, "simplifier": [{"n": 1, "attempt": 1, "prompt": story, "failures": []}]}
    return {"scenes": [{"prompt": f"{story} {SUFFIX}", "story": story, "style_suffix": SUFFIX, "duration": 15}],
            "combo_key": f"ferry_operations|passenger car ferry|{event.lower()}|open vehicle deck|fixed_cctv",
            "scenario_summary": scenario["scenario_summary"], "youtube_title": "Chain Snaps", "total_duration": 15,
            "beat1_action_verb": "snaps", "trace": trace,
            "gate_context": {"scenario": scenario, "domain_id": "ferry_operations", "ship": "Passenger Car Ferry",
                             "event": event},
            "selection": {"domain_id": "ferry_operations", "event": event, "environment": "Open vehicle deck",
                          "ship": "Passenger Car Ferry", "camera": "fixed_cctv"}}


class _Reporter(main.PipelineReporter):
    def __init__(self, approve=True, needs_approval=False):
        self.needs_approval, self._approve, self.calls = needs_approval, approve, []

    async def generation(self, trace, prompt_data=None):
        self.calls.append(("generation", trace))

    async def final_prompt(self, info):
        self.calls.append(("final", info))

    async def approve(self, info):
        self.calls.append(("approve", info))
        return self._approve


class TestPipelineTur29(unittest.TestCase):
    def setUp(self):
        self.archive = _tmp_archive(self)

    def run_pipe(self, prompt_data=None, poll=None, preflight=None, reporter=None, event=FERRY_EVENT, mode="TEST",
                 skip_upload=True, youtube_enabled=True, publish_locked=False, gen=None):
        self.tracker = MagicMock()
        self.tracker.page_id = None
        self.tracker.get_recent_history.return_value = []
        self.tracker.get_recent_beat1_verbs.return_value = []
        self.tracker.create_entry.side_effect = lambda *a, **k: setattr(self.tracker, "page_id", "page-1")
        self.create = AsyncMock(return_value="task-1")
        self.upload = AsyncMock(return_value="https://youtu.be/x")
        self.downloaded = []

        def download(url):
            p = _fake_video()
            self.downloaded.append(p)
            return p
        preflight = preflight or AsyncMock(side_effect=lambda s: (s, False, {"risk_score": 1}))
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "POLL_INITIAL_WAIT", 0), \
             patch.object(settings, "YOUTUBE_ENABLED", youtube_enabled), \
             patch.object(settings, "PUBLISH_LOCKED", publish_locked), \
             patch.object(main, "load_used_combos", return_value=[]), \
             patch.object(main, "NotionTracker", return_value=self.tracker), \
             patch.object(main, "generate_prompts", gen or AsyncMock(return_value=prompt_data or _prompt_data())), \
             patch.object(ps, "gpt_preflight_check", preflight), \
             patch.object(KieClient, "_create_task", self.create), \
             patch.object(KieClient, "_poll_for_result", poll or AsyncMock(return_value="https://cdn/v.mp4")), \
             patch.object(KieClient, "get_credit", AsyncMock(side_effect=[100.0, 82.5])), \
             patch.object(main, "download_video", side_effect=download), \
             patch.object(main, "motion_profile", MagicMock(side_effect=RuntimeError("ffmpeg yok"))), \
             patch.object(main, "upload_to_youtube", self.upload):
            return asyncio.run(main.run_pipeline(skip_upload=skip_upload, event=event, mode=mode, reporter=reporter,
                                                 domain="ferry_operations", trigger="manual"))

    def statuses(self):
        return [c.args[0] for c in self.tracker.update_status.call_args_list]

    def test_test_mode_never_uploads_and_archives_full_meta(self):
        r = self.run_pipe(mode="TEST", skip_upload=True, youtube_enabled=True, publish_locked=False)
        self.assertTrue(r["success"])
        self.upload.assert_not_awaited()
        self.assertEqual(self.statuses()[-1], STATUS_TEST_DONE)
        self.assertEqual(self.tracker.create_entry.call_args.args[0]["mode"], "TEST")
        meta = json.load(open(meta_path(r["archive_dir"]), encoding="utf-8"))
        for key in ("domain", "event", "camera", "ship", "final_prompt", "commit", "model", "resolution", "task_id",
                    "mode", "credit_before", "credit_after"):
            self.assertIn(key, meta, key)
        self.assertEqual((meta["mode"], meta["task_id"], meta["resolution"]), ("TEST", "task-1", "480p"))
        self.assertEqual((meta["credit_before"], meta["credit_after"]), (100.0, 82.5))
        self.assertEqual(meta["final_prompt"], self.create.await_args.args[1])
        self.assertTrue(os.path.exists(os.path.join(r["archive_dir"], "video.mp4")))
        self.assertEqual(r["video_path"], os.path.join(r["archive_dir"], "video.mp4"))

    def test_temp_download_deleted_in_test_mode(self):
        self.run_pipe()
        self.assertTrue(self.downloaded)
        self.assertFalse(any(os.path.exists(p) for p in self.downloaded))   # main.py:363 sızıntısı kapandı

    def test_task_id_written_before_polling(self):
        seen = {}

        async def poll(cfg, task_id, *a, **k):
            seen["record_task"] = self.tracker.record_task.call_args
            dirs = os.listdir(self.archive)
            seen["meta"] = json.load(open(meta_path(os.path.join(self.archive, dirs[0])), encoding="utf-8"))
            return "https://cdn/v.mp4"
        self.run_pipe(poll=poll)
        self.assertEqual(seen["record_task"].args[0], "task-1")
        self.assertEqual(seen["meta"]["task_id"], "task-1")
        self.assertEqual(seen["meta"]["status"], "video_uretiliyor")

    def test_notion_gets_post_preflight_prompt(self):
        rewritten = STORY.replace("lunge for", "grab")
        r = self.run_pipe(preflight=AsyncMock(return_value=(rewritten, True, {"risk_score": 6, "rewritten": True})))
        self.assertTrue(r["success"])
        sent = self.create.await_args.args[1]
        self.assertIn("grab the rail", sent)
        self.assertEqual(self.tracker.record_final_prompt.call_args.args[0], sent)
        body = self.tracker.append_body.call_args_list[-1].args[0][0][1]
        self.assertIn(sent, body)
        self.assertIn("Preflight", body)
        self.assertEqual(self.tracker.record_final_prompt.call_args.args[1]["camera"], "fixed_cctv")

    def test_event_mismatch_stops_before_kie(self):
        other = "A tornado tears across the beach and flings umbrellas into the air as two bystanders run for cover."
        r = self.run_pipe(prompt_data=_prompt_data(story=other))
        self.assertEqual(r["reason"], "event_mismatch")
        self.create.assert_not_awaited()
        self.assertIn("Olay uyuşmuyor", r["error"])

    def test_event_mismatch_after_preflight_rewrite_stops_before_kie(self):
        # Kalite kapılarından geçen ama menü olayını (zincir kopması) taşımayan bir güvenlik rewrite'ı
        other = ("Storm waves wash across the passenger car ferry's open deck as three deckhands brace against the "
                 "rail. The waves keep surging over the rail, still soaking the deck and sweeping loose gear toward "
                 "the scuppers.")
        rewrite = AsyncMock(side_effect=AssertionError("ilk aday kapıdan geçmeliydi, GPT rewrite çağrılmamalı"))
        with patch.object(ps, "gpt_rewrite_rejected_prompt", rewrite):
            r = self.run_pipe(preflight=AsyncMock(return_value=(other, True, {"risk_score": 6})))
        self.assertEqual(r["reason"], "event_mismatch")
        self.assertIn("Kie'ye gidecek hikaye", r["error"])
        self.create.assert_not_awaited()
        rewrite.assert_not_awaited()

    def test_approval_cancel_spends_nothing(self):
        rep = _Reporter(approve=False, needs_approval=True)
        r = self.run_pipe(reporter=rep)
        self.assertEqual(r["reason"], "cancelled")
        self.create.assert_not_awaited()
        self.assertIn(STATUS_AWAITING_APPROVAL, self.statuses())
        self.assertEqual(self.statuses()[-1], STATUS_CANCELLED)
        self.assertEqual([c[0] for c in rep.calls], ["generation", "final", "approve"])

    def test_approval_yes_submits(self):
        rep = _Reporter(approve=True, needs_approval=True)
        r = self.run_pipe(reporter=rep)
        self.assertTrue(r["success"])
        self.create.assert_awaited_once()
        approve_info = [c[1] for c in rep.calls if c[0] == "approve"][0]
        self.assertEqual(approve_info["prompt"], self.create.await_args.args[1])

    def test_kie_timeout_keeps_record_open(self):
        r = self.run_pipe(poll=AsyncMock(side_effect=KieTimeoutError("zaman aşımı", "task-1")))
        self.assertEqual((r["reason"], r["task_id"]), ("kie_timeout", "task-1"))
        self.tracker.update_with_error.assert_not_called()
        self.tracker.record_task.assert_called_once_with("task-1")

    def test_no_valid_scenario_reports_trace(self):
        rep = _Reporter()
        err = pg.NoValidScenarioError("kaldı", attempts=[{"attempt": 1, "failures": ["x"]}], trace={"candidates": [1]})
        r = self.run_pipe(reporter=rep, gen=AsyncMock(side_effect=err))
        self.assertEqual(r["reason"], "no_valid_scenario")
        self.assertEqual(rep.calls[0], ("generation", {"candidates": [1]}))
        self.tracker.create_entry.assert_not_called()


# ─────────────────────────── Kurtarma (İŞ 1a) ───────────────────────────

class TestRecovery(unittest.TestCase):
    def setUp(self):
        self.archive = _tmp_archive(self)

    def recover(self, records, wait=None):
        cls = MagicMock()
        cls.find_by_status.return_value = records
        self.tracker = MagicMock()
        cls.return_value = self.tracker
        kie = MagicMock()
        kie.wait_for_task = wait or AsyncMock(return_value="https://cdn/r.mp4")
        kie.get_task = AsyncMock(return_value={"prompt": "the prompt"})
        kie.create_video = AsyncMock()
        self.kie = kie
        delivered = []

        async def on_video(item):
            delivered.append(item)
        with patch.object(main, "NotionTracker", cls), patch.object(main, "download_video", side_effect=lambda u: _fake_video()):
            results = asyncio.run(main.recover_pending_tasks(on_video=on_video, kie=kie))
        return results, delivered

    def test_recovers_task_without_new_paid_call(self):
        rec = {"page_id": "p1", "status": "Video Üretiliyor", "task_id": "t1", "mode": "TEST", "title": "T",
               "combo_key": "ferry_operations|x|y|z|fixed_cctv"}
        results, delivered = self.recover([rec])
        self.assertEqual(results[0]["action"], "recovered")
        self.kie.create_video.assert_not_awaited()
        self.kie.wait_for_task.assert_awaited_once()
        self.assertEqual(self.tracker.update_status.call_args.args[0], STATUS_RECOVERED)
        self.assertTrue(os.path.exists(delivered[0]["video_path"]))
        meta = json.load(open(meta_path(delivered[0]["archive_dir"]), encoding="utf-8"))
        self.assertEqual((meta["task_id"], meta["final_prompt"], meta["recovered"]), ("t1", "the prompt", True))

    def test_awaiting_approval_dropped_silently(self):
        rec = {"page_id": "p2", "status": STATUS_AWAITING_APPROVAL, "task_id": "", "mode": "TEST", "title": "T",
               "combo_key": ""}
        results, delivered = self.recover([rec])
        self.assertEqual(results[0]["action"], "cancelled")
        self.assertEqual(self.tracker.update_status.call_args.args[0], STATUS_CANCELLED)
        self.kie.wait_for_task.assert_not_awaited()
        self.assertEqual(delivered, [])

    def test_legacy_record_without_task_skipped(self):
        rec = {"page_id": "p3", "status": "Video Üretiliyor", "task_id": "", "mode": "", "title": "eski", "combo_key": ""}
        results, _ = self.recover([rec])
        self.assertEqual(results[0]["action"], "skipped_no_task")
        self.tracker.update_status.assert_not_called()

    def test_still_running_left_open(self):
        rec = {"page_id": "p4", "status": "Video Üretiliyor", "task_id": "t4", "mode": "TEST", "title": "T", "combo_key": ""}
        results, _ = self.recover([rec], wait=AsyncMock(side_effect=KieTimeoutError("x", "t4")))
        self.assertEqual(results[0]["action"], "still_running")
        self.tracker.update_with_error.assert_not_called()


# ─────────────────────────── Kapı düzeltmeleri (İŞ 1e) + olay denetimi (İŞ 1d) ───────────────────────────

class TestGateFixes(unittest.TestCase):
    def test_substring_no_longer_counts(self):
        calm = {"visible_start": "The harbor water sits still", "physical_movement": "A realistic specialist listens",
                "visible_consequence": "Everything stays quiet", "scenario_summary": "a realistic calm harbor"}
        self.assertNotIn("list", pg._action_keyword_hits(" ".join(calm.values())))
        ok, fails = pg.validate_high_action(calm)
        self.assertFalse(ok)
        base = {"visible_start": "A mooring line snaps", "physical_movement": "The yacht swings",
                "visible_consequence": "It keeps swinging", "scenario_summary": "x"}
        noisy = dict(base, scenario_summary="A realistic specialist listens in pajamas with a bracelet")
        self.assertEqual(pg.score_scenario(base), pg.score_scenario(noisy))

    def test_real_keywords_still_count(self):
        self.assertTrue({"snap", "list", "slide"} <= set(pg._action_keyword_hits("The ship lists hard, a line snaps and cars slide")))

    def test_given_way_is_a_trigger(self):
        ok, fails = pg.validate_visible_trigger({"visible_trigger": "the timber blocks and holding ropes have given way",
                                                 "visible_start": "The timber blocks give way under the ferry",
                                                 "physical_movement": "The holding ropes snap"},
                                                "shipyard_and_drydock_engineering")
        self.assertTrue(ok, fails)

    def test_bustling_and_shattered_calm_allowed(self):
        self.assertEqual(pg._static_start_hits("violent winds tear through a bustling street as two pedestrians sprint"), [])
        self.assertEqual(pg._static_start_hits("a tornado tears through the marina, shattering the calm"), [])
        self.assertIn("a/the calm", pg._static_start_hits("the calm harbor sits under grey skies"))

    def test_throwing_debris_is_motion(self):
        ok, fails = pg.validate_beat3_ongoing_danger({"visible_consequence":
            "The tornado tears down the street, throwing debris high into the air as pedestrians still seek shelter"})
        self.assertTrue(ok, fails)

    def test_jet_ski_cast_range(self):
        two = {"visible_start": "Two riders cling on as the jet ski slams into the pontoon.",
               "physical_movement": "x", "visible_consequence": "x"}
        self.assertTrue(pg.validate_cast_size(two, "marina_and_yacht_operations", "", "Jet Ski")[0])
        self.assertFalse(pg.validate_cast_size(two, "marina_and_yacht_operations", "", "Luxury Motor Yacht")[0])


class TestEventFidelity(unittest.TestCase):
    def test_every_event_matches_itself(self):
        for d, a in DOMAIN_ATTRIBUTES.items():
            for e in a["events"]:
                with self.subTest(event=e):
                    self.assertTrue(pg._event_stems(e))
                    self.assertEqual(pg.event_fidelity_issues(e, e), [])

    def test_mismatch_detected(self):
        self.assertTrue(pg.event_fidelity_issues(FERRY_EVENT, "A tornado tears across the beach."))
        self.assertEqual(pg.event_fidelity_issues(FERRY_EVENT, STORY), [])
        self.assertEqual(pg.event_fidelity_issues(None, "anything"), [])

    def test_side_launch_story_matches(self):
        story = ("The passenger car ferry, its entire long side facing the camera, tips sideways off the quay edge "
                 "and drops broadside into the water.")
        self.assertEqual(pg.event_fidelity_issues(SIDE_LAUNCH_EVENT, story), [])


# ─────────────────────────── Ayrıntı metni (İŞ 3) ───────────────────────────

class TestTraceFormat(unittest.TestCase):
    def test_split_lossless_under_limit(self):
        text = "\n".join(f"satır {i} " + "x" * (i % 300) for i in range(400)) + "\n" + "y" * 9000
        parts = split_message(text)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(p) <= 4096 for p in parts))
        self.assertEqual("".join(parts), text)

    def test_constraint_count(self):
        self.assertEqual(count_constraints(SUFFIX), (2, 2))

    def test_word_diff(self):
        self.assertEqual(word_diff("a b c", "a b c"), "")
        self.assertEqual(word_diff("a b c", "a x c"), "a [-b-] {+x+} c")

    def test_generation_sections(self):
        trace = _prompt_data()["trace"]
        trace["candidates"].append({"n": 2, "domain_id": "d", "event": "e", "environment": "v", "ship": "s",
                                    "camera": "c", "summary": "z", "passed": False, "failures": ["Cast: 2 kişi"]})
        text = "\n".join(t + "\n" + b for t, b in format_generation(trace, {"domain": "⛴️ Feribot"}))
        for part in ("1. Seçim", "⛴️ Feribot", "2. Adaylar (1/2", "#2 ❌ reddedildi", "Cast: 2 kişi", "3. Seçilen",
                     "4. Simplifier", STORY):
            self.assertIn(part, text)

    def test_final_prompt_full_text(self):
        prompt = STORY + " " + SUFFIX
        title, body = format_final_prompt({"prompt": prompt, "story": STORY, "style_suffix": SUFFIX,
                                           "story_before_preflight": STORY, "attempt": 1})
        self.assertIn(prompt, body)
        self.assertIn(f"{len(prompt.split())} kelime", body)
        self.assertNotIn("Preflight", body)


# ─────────────────────────── Notion (İŞ 1c, 4) ───────────────────────────

class TestNotion(unittest.TestCase):
    def setUp(self):
        for p in (patch.object(settings, "NOTION_ENABLED", True), patch.object(settings, "IS_DRY_RUN", False),
                  patch.object(nl.NotionTracker, "_schema", None)):
            p.start()
            self.addCleanup(p.stop)

    def test_body_splits_long_prompt(self):
        req = MagicMock(return_value={})
        with patch.object(nl, "_notion_request", req):
            nl.NotionTracker(page_id="pg").append_body([("Son prompt", "x" * 4500)])
        children = req.call_args.kwargs["json"]["children"]
        self.assertEqual([b["type"] for b in children], ["heading_3", "paragraph", "paragraph", "paragraph"])
        self.assertTrue(all(len(b["paragraph"]["rich_text"][0]["text"]["content"]) <= 2000 for b in children[1:]))
        self.assertEqual("".join(b["paragraph"]["rich_text"][0]["text"]["content"] for b in children[1:]), "x" * 4500)

    def test_ensure_schema_adds_only_missing(self):
        req = MagicMock(side_effect=[{"properties": {"Durum": {}, "Mod": {}}}, {}])
        with patch.object(nl, "_notion_request", req):
            have = nl.NotionTracker.ensure_schema()
        added = req.call_args_list[1].kwargs["json"]["properties"]
        self.assertNotIn("Mod", added)
        self.assertTrue({"Puan", "Kie Task ID", "Kamera", "Olay", "Commit", "Telegram File ID"} <= set(added))
        self.assertIn("Puan", have)

    def test_unknown_props_filtered_when_schema_known(self):
        req = MagicMock(return_value={})
        with patch.object(nl, "_notion_request", req), patch.object(nl.NotionTracker, "_schema", {"Durum", "Kie Task ID"}):
            nl.NotionTracker(page_id="pg").update_status("X", {"Kie Task ID": nl._rt("t"), "Yok": nl._rt("y")})
        self.assertEqual(set(req.call_args.kwargs["json"]["properties"]), {"Durum", "Kie Task ID"})

    def test_record_task_and_rating(self):
        req = MagicMock(return_value={})
        with patch.object(nl, "_notion_request", req):
            t = nl.NotionTracker(page_id="pg")
            t.record_task("task-9")
            t.set_rating("iyi")
        props0 = req.call_args_list[0].kwargs["json"]["properties"]
        self.assertEqual(props0["Durum"]["select"]["name"], "Video Üretiliyor")
        self.assertEqual(props0["Kie Task ID"]["rich_text"][0]["text"]["content"], "task-9")
        self.assertEqual(req.call_args_list[1].kwargs["json"]["properties"]["Puan"]["select"]["name"], "iyi")


# ─────────────────────────── Telegram (İŞ 2, 3, 4) ───────────────────────────

def _update(chat_id=CHAT, data=None):
    u = MagicMock()
    u.effective_chat.id = chat_id
    u.effective_message.reply_text = AsyncMock()
    u.callback_query.data = data
    u.callback_query.answer = AsyncMock()
    u.callback_query.edit_message_text = AsyncMock()
    u.callback_query.edit_message_reply_markup = AsyncMock()
    return u


def _context(cfg=None):
    c = MagicMock()
    c.bot_data = {"allowed_chat_id": CHAT, "cfg": cfg or bot.default_cfg()}
    c.bot.send_message = AsyncMock()
    c.bot.send_video = AsyncMock()
    return c


def _buttons(markup):
    return [b for row in markup.inline_keyboard for b in row]


class TestTelegramModes(unittest.TestCase):
    def test_restart_returns_to_test(self):
        app = bot.build_application("123:ABC", CHAT)
        app.bot_data["cfg"] = bot.default_cfg("YAYIN")
        self.assertEqual(bot.build_application("123:ABC", CHAT).bot_data["cfg"]["mode"], "TEST")

    def test_yayin_asks_confirmation(self):
        ctx, upd = _context(), _update()
        asyncio.run(bot.cmd_yayin(upd, ctx))
        markup = upd.effective_message.reply_text.await_args.kwargs["reply_markup"]
        self.assertEqual([b.callback_data for b in _buttons(markup)], ["uret:y:ok", "uret:y:no"])
        self.assertEqual(ctx.bot_data["cfg"]["mode"], "TEST")   # komut tek başına modu değiştirmez

    def test_confirm_while_locked_stays_test(self):
        ctx, upd = _context(), _update(data="uret:y:ok")
        with patch.object(settings, "PUBLISH_LOCKED", True):
            asyncio.run(bot.on_callback(upd, ctx))
        self.assertEqual(ctx.bot_data["cfg"]["mode"], "TEST")
        self.assertIn("kilitli", upd.callback_query.edit_message_text.await_args.args[0])

    def test_confirm_when_unlocked_switches(self):
        ctx, upd = _context(), _update(data="uret:y:ok")
        with patch.object(settings, "PUBLISH_LOCKED", False):
            asyncio.run(bot.on_callback(upd, ctx))
        self.assertEqual(ctx.bot_data["cfg"], {"mode": "YAYIN", "detail": False, "approval": False})

    def test_test_command_resets(self):
        ctx, upd = _context(bot.default_cfg("YAYIN")), _update()
        asyncio.run(bot.cmd_test(upd, ctx))
        self.assertEqual(ctx.bot_data["cfg"], bot.default_cfg("TEST"))

    def test_toggles(self):
        ctx, upd = _context(), _update(data="uret:t:d")
        asyncio.run(bot.on_callback(upd, ctx))
        self.assertFalse(ctx.bot_data["cfg"]["detail"])
        self.assertIn("🔍 Ayrıntı: KAPALI", upd.callback_query.edit_message_text.await_args.args[0])
        upd2 = _update(data="uret:t:o")
        asyncio.run(bot.on_callback(upd2, ctx))
        self.assertFalse(ctx.bot_data["cfg"]["approval"])

    def test_menu_callbacks_within_64_bytes(self):
        markups = [bot.domain_keyboard(bot.default_cfg()), bot.approval_keyboard("abcd1234"), bot.publish_keyboard(),
                   bot.rating_keyboard("3e7d048d-625e-816b-914a-c3ef23b65bc7")]
        for b in (b for m in markups for b in _buttons(m)):
            self.assertLessEqual(len(b.callback_data.encode()), 64, b.callback_data)

    def test_yayin_mode_production_passes_publish_kwargs(self):
        ctx = _context(bot.default_cfg("YAYIN"))
        upd = _update(data="uret:ok:0:r")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["mode"], kw["skip_upload"]), ("YAYIN", False))
        self.assertFalse(kw["reporter"].needs_approval)
        self.assertIn("kredi harcanmadı", ctx.bot.send_message.await_args.args[1])


class TestApprovalAndRating(unittest.TestCase):
    def test_approval_callback_resolves_future(self):
        ctx = _context()
        fut = concurrent.futures.Future()
        ctx.bot_data["approvals"] = {"tok1": fut}
        upd = _update(data="uret:ap:tok1:y")
        with patch.object(bot, "_production_lock", asyncio.Lock()):
            async def go():
                async with bot._production_lock:   # onay, üretim kilidi tutulurken gelir
                    await bot.on_callback(upd, ctx)
            asyncio.run(go())
        self.assertTrue(fut.result(timeout=1))
        upd.callback_query.edit_message_reply_markup.assert_awaited_once()
        self.assertEqual(ctx.bot_data["approvals"], {})

    def test_stale_approval(self):
        ctx, upd = _context(), _update(data="uret:ap:nope:y")
        asyncio.run(bot.on_callback(upd, ctx))
        self.assertIn("geçerli değil", ctx.bot.send_message.await_args.args[1])

    def test_rating_writes_notion_and_meta(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        ctx = _context()
        ctx.bot_data["archives"] = {"abc123": d}
        upd = _update(data="uret:r:abc123:b")
        tracker_cls = MagicMock()
        with patch.object(bot, "NotionTracker", tracker_cls):
            asyncio.run(bot.on_callback(upd, ctx))
        tracker_cls.assert_called_with(page_id="abc123")
        tracker_cls.return_value.set_rating.assert_called_once_with("kötü")
        upd.callback_query.edit_message_reply_markup.assert_awaited_once_with(reply_markup=None)
        self.assertEqual(json.load(open(meta_path(d), encoding="utf-8"))["rating"], "kötü")

    def test_deliver_video_test_caption_rating_and_file_id(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        video = _fake_video()
        self.addCleanup(os.remove, video)
        ctx = _context()
        msg = MagicMock()
        msg.video.file_id = "FILE123"
        ctx.bot.send_video = AsyncMock(return_value=msg)
        tracker_cls = MagicMock()
        with patch.object(bot, "NotionTracker", tracker_cls):
            asyncio.run(bot.deliver_video(ctx.bot, CHAT, video, "Başlık", "TEST", "pg-1", d, ctx.bot_data))
        kw = ctx.bot.send_video.await_args.kwargs
        self.assertTrue(kw["caption"].startswith("🧪 TEST | "))
        self.assertEqual([b.callback_data for b in _buttons(kw["reply_markup"])], ["uret:r:pg1:g", "uret:r:pg1:b"])
        tracker_cls.return_value.set_telegram_file_id.assert_called_once_with("FILE123")
        self.assertEqual(json.load(open(meta_path(d), encoding="utf-8"))["telegram_file_id"], "FILE123")
        self.assertEqual(ctx.bot_data["archives"]["pg1"], d)


class TestTelegramReporter(unittest.TestCase):
    INFO = {"prompt": STORY + " " + SUFFIX, "story": STORY, "style_suffix": SUFFIX, "story_before_preflight": STORY,
            "attempt": 1}

    def _run_approve(self, answer=None, timeout=5.0):
        async def main_():
            approvals = {}
            b = MagicMock()
            b.send_message = AsyncMock()
            rep = bot.TelegramReporter(b, CHAT, asyncio.get_running_loop(), approvals, True, True, timeout=timeout)
            # pipeline gibi: ayrı thread, ayrı event loop
            task = asyncio.ensure_future(asyncio.to_thread(asyncio.run, rep.approve(self.INFO)))
            if answer is not None:
                while not approvals:
                    await asyncio.sleep(0.01)
                next(iter(approvals.values())).set_result(answer)
            return await task, b
        return asyncio.run(main_())

    def test_approve_across_threads(self):
        ok, b = self._run_approve(answer=True)
        self.assertTrue(ok)
        text, kw = b.send_message.await_args_list[-1].args[1], b.send_message.await_args_list[-1].kwargs
        self.assertIn(self.INFO["prompt"], text)
        self.assertTrue(_buttons(kw["reply_markup"])[0].callback_data.startswith("uret:ap:"))

    def test_approve_cancel(self):
        ok, _ = self._run_approve(answer=False)
        self.assertFalse(ok)

    def test_approve_timeout_is_cancel(self):
        ok, b = self._run_approve(answer=None, timeout=0.05)
        self.assertFalse(ok)
        self.assertIn("süresi doldu", b.send_message.await_args_list[-1].args[1])

    def test_long_generation_split(self):
        trace = _prompt_data()["trace"]
        trace["candidates"] = [dict(trace["candidates"][0], n=i, summary="uzun " * 400) for i in range(1, 6)]

        async def main_():
            b = MagicMock()
            b.send_message = AsyncMock()
            rep = bot.TelegramReporter(b, CHAT, asyncio.get_running_loop(), {}, True, False)
            await asyncio.to_thread(asyncio.run, rep.generation(trace))
            return b
        b = asyncio.run(main_())
        texts = [c.args[1] for c in b.send_message.await_args_list]
        self.assertGreater(len(texts), 1)
        self.assertTrue(all(len(t) <= 4096 for t in texts))
        self.assertEqual("".join(texts).count("uzun"), 2000)   # bilgi kesilmedi

    def test_detail_off_sends_nothing(self):
        async def main_():
            b = MagicMock()
            b.send_message = AsyncMock()
            rep = bot.TelegramReporter(b, CHAT, asyncio.get_running_loop(), {}, False, False)
            await rep.generation(_prompt_data()["trace"])
            await rep.final_prompt(self.INFO)
            return b
        asyncio.run(main_()).send_message.assert_not_awaited()


class TestPostInit(unittest.TestCase):
    def test_commands_schema_and_recovery(self):
        app = MagicMock()
        app.bot.set_my_commands = AsyncMock()
        app.bot_data = {"allowed_chat_id": CHAT}
        scheduled = []
        app.create_task.side_effect = lambda coro: (scheduled.append(coro), coro.close())
        with patch.object(bot.NotionTracker, "ensure_schema") as schema:
            asyncio.run(bot.post_init(app))
        cmds = [c.command for c in app.bot.set_my_commands.await_args.args[0]]
        self.assertEqual(cmds, ["uret", "test", "yayin"])
        schema.assert_called_once()
        self.assertEqual(len(scheduled), 1)


if __name__ == "__main__":
    unittest.main()
