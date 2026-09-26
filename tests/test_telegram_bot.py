#!/usr/bin/env python3
"""
Telegram tetikleyici (bot.py) + domain parametresi (2026-09-26). API çağrısı yok:
Telegram, GPT, Kie, Notion, YouTube mock'lanır. Ücretli hiçbir çağrı yapılmaz.
"""
import asyncio
import json
import os
import re
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import bot
import core.prompt_generator as pg
from config import settings
from core.creative_engine import MARITIME_INSPIRATION_DOMAINS, get_creative_catalyst
from core.prompt_generator import NoValidScenarioError

CHAT = 424242
DOMAINS = list(MARITIME_INSPIRATION_DOMAINS)


def _update(chat_id=CHAT, data=None):
    u = MagicMock()
    u.effective_chat.id = chat_id
    u.effective_message.reply_text = AsyncMock()
    u.callback_query.data = data
    u.callback_query.answer = AsyncMock()
    u.callback_query.edit_message_text = AsyncMock()
    return u


def _context():
    c = MagicMock()
    c.bot_data = {"allowed_chat_id": CHAT}
    c.bot.send_message = AsyncMock()
    c.bot.send_video = AsyncMock()
    return c


def _sent_texts(ctx):
    return [call.args[1] for call in ctx.bot.send_message.call_args_list]


class TestDomainParameter(unittest.TestCase):
    def test_forced_domain_always_chosen(self):
        for d in DOMAINS:
            # d en son kullanılmış olsa bile (rotasyon normalde dışlar) zorunlu domain seçilir
            history = [f"{d}|none|x|x|fixed_cctv"]
            with self.subTest(domain=d):
                for _ in range(10):
                    self.assertEqual(get_creative_catalyst(recent_history=history, domain=d)["domain_id"], d)

    def test_unknown_domain_rejected(self):
        with self.assertRaises(ValueError):
            get_creative_catalyst(recent_history=[], domain="cargo_ships")

    def test_no_domain_keeps_rotation(self):
        history = [f"{d}|none|x|x|fixed_cctv" for d in DOMAINS[:-1]]
        self.assertEqual(get_creative_catalyst(recent_history=history)["domain_id"], DOMAINS[-1])

    def _run_generate(self, domain, used_combos=()):
        calls = []
        real = pg.get_creative_catalyst

        def spy(**kw):
            calls.append(kw.get("domain"))
            return real(**kw)

        gen = AsyncMock(return_value={"scenario_summary": "calm harbor", "beat1_action_verb": "sits"})
        config = {"used_combos": list(used_combos), "recent_topics": [], "recent_verbs": [], "domain": domain}
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(pg, "get_creative_catalyst", side_effect=spy), \
             patch.object(pg, "_generate_scenario", gen),              patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrılmamalı"))):
            with self.assertRaises(NoValidScenarioError) as cm:
                asyncio.run(pg.generate_prompts(config))
        return calls, gen, str(cm.exception)

    def test_generate_prompts_five_scenarios_from_domain_and_gates_still_run(self):
        calls, gen, err = self._run_generate("urban_city_disasters")
        self.assertEqual(gen.await_count, 5)
        self.assertTrue(calls and set(calls) == {"urban_city_disasters"})
        for cat_call in gen.await_args_list:
            self.assertEqual(cat_call.args[0]["domain_id"], "urban_city_disasters")
        # Sakin/boş senaryo kapıda reddedildi: kapılar domain verilince de çalışıyor
        attempts = json.loads(err.split("Denemeler: ", 1)[1])
        self.assertEqual(len(attempts), 5)
        self.assertTrue(all(a["combo_key"].startswith("urban_city_disasters|") and a["failures"] for a in attempts))

    def test_generate_prompts_dedup_with_domain(self):
        calls, gen, err = self._run_generate("ferry_operations")
        keys = [a["combo_key"] for a in json.loads(err.split("Denemeler: ", 1)[1])]
        # İlk koşunun combo'ları "kullanılmış" verilince aynı combo tekrar seçilmez
        _, _, err2 = self._run_generate("ferry_operations", used_combos=keys)
        keys2 = [a["combo_key"] for a in json.loads(err2.split("Denemeler: ", 1)[1])]
        self.assertFalse(set(keys) & set(keys2))

    def test_generate_prompts_without_domain_passes_none(self):
        calls, _, _ = self._run_generate(None)
        self.assertEqual(set(calls), {None})


class TestConfig(unittest.TestCase):
    def test_missing_env_stops(self):
        for env in ({}, {"TELEGRAM_BOT_TOKEN": "t"}, {"TELEGRAM_CHAT_ID": "1"}, {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "abc"}):
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True):
                with self.assertRaises(SystemExit):
                    bot.load_telegram_config()

    def test_reads_env(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": " tok ", "TELEGRAM_CHAT_ID": "-100123"}, clear=True):
            self.assertEqual(bot.load_telegram_config(), ("tok", -100123))

    def test_no_hardcoded_token_or_chat_id(self):
        src = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
        self.assertIsNone(re.search(r"\d{8,10}:[A-Za-z0-9_-]{30,}", src))
        self.assertNotIn(str(CHAT), src)

    def test_railway_json_runs_bot_without_cron(self):
        deploy = json.load(open(os.path.join(ROOT, "railway.json"), encoding="utf-8"))["deploy"]
        self.assertEqual(deploy["startCommand"], "python bot.py")
        self.assertEqual(deploy["restartPolicyType"], "ON_FAILURE")   # Railway ALWAYS'u zaten buna çeviriyordu (2026-09-26)
        self.assertNotIn("cronSchedule", deploy)

    def test_requirements_pin_telegram(self):
        reqs = open(os.path.join(ROOT, "requirements.txt"), encoding="utf-8").read()
        self.assertRegex(reqs, r"(?m)^python-telegram-bot==\d+\.\d+(\.\d+)?$")


class TestKeyboard(unittest.TestCase):
    def test_seven_domain_buttons(self):
        self.assertEqual(list(bot.DOMAIN_LABELS), DOMAINS)
        buttons = [b for row in bot.domain_keyboard().inline_keyboard for b in row]
        self.assertEqual(len(buttons), 7)
        self.assertEqual([b.callback_data for b in buttons], [bot.CALLBACK_PREFIX + d for d in DOMAINS])
        for b in buttons:
            self.assertLessEqual(len(b.callback_data.encode()), 64)   # Telegram callback_data sınırı

    def test_application_builds_with_handlers(self):
        app = bot.build_application("123:ABC", CHAT)
        self.assertEqual(app.bot_data["allowed_chat_id"], CHAT)
        self.assertEqual(len(app.handlers[0]), 3)


class TestHandlers(unittest.TestCase):
    def setUp(self):
        self.lock_patch = patch.object(bot, "_production_lock", asyncio.Lock())
        self.lock_patch.start()
        self.addCleanup(self.lock_patch.stop)

    def _select(self, domain, result=None, side_effect=None, chat_id=CHAT, video=True):
        ctx, upd = _context(), _update(chat_id, data=bot.CALLBACK_PREFIX + domain)
        path = {}

        async def fake_run(**kw):
            path["out"] = kw["output_path"]
            if side_effect:
                raise side_effect
            if video:
                with open(kw["output_path"], "wb") as f:
                    f.write(b"mp4")
            return dict(result, video_path=kw["output_path"]) if result.get("success") else result

        runner = AsyncMock(side_effect=fake_run)
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot.status, "fail"):
            asyncio.run(bot.on_domain_selected(upd, ctx))
        return ctx, upd, runner, path.get("out")

    def test_unauthorized_command_ignored(self):
        ctx, upd = _context(), _update(chat_id=999)
        asyncio.run(bot.cmd_uret(upd, ctx))
        upd.effective_message.reply_text.assert_not_awaited()

    def test_uret_shows_keyboard(self):
        ctx, upd = _context(), _update()
        asyncio.run(bot.cmd_uret(upd, ctx))
        kwargs = upd.effective_message.reply_text.await_args.kwargs
        self.assertEqual(len([b for r in kwargs["reply_markup"].inline_keyboard for b in r]), 7)

    def test_uret_busy(self):
        ctx, upd = _context(), _update()

        async def go():
            async with bot._production_lock:
                await bot.cmd_uret(upd, ctx)
        asyncio.run(go())
        self.assertIn("Üretim sürüyor", upd.effective_message.reply_text.await_args.args[0])

    def test_selection_busy_does_not_run(self):
        ctx, upd = _context(), _update(data=bot.CALLBACK_PREFIX + "ferry_operations")
        runner = AsyncMock()

        async def go():
            async with bot._production_lock:
                await bot.on_domain_selected(upd, ctx)
        with patch.object(bot.pipeline, "run_pipeline", runner):
            asyncio.run(go())
        runner.assert_not_awaited()
        self.assertIn("Üretim sürüyor", upd.callback_query.edit_message_text.await_args.args[0])

    def test_unauthorized_selection_does_not_run(self):
        ctx, upd, runner, _ = self._select("ferry_operations", result={"success": True}, chat_id=999)
        runner.assert_not_awaited()
        upd.callback_query.edit_message_text.assert_not_awaited()

    def test_unknown_domain_does_not_run(self):
        ctx, upd, runner, _ = self._select("cargo_ships", result={"success": True})
        runner.assert_not_awaited()

    def test_success_flow(self):
        ok = {"success": True, "youtube_url": "https://youtube.com/shorts/abc", "title": "Wave Hits Ferry"}
        ctx, upd, runner, out = self._select("ferry_operations", result=ok)
        kw = runner.await_args.kwargs
        self.assertEqual((kw["domain"], kw["trigger"]), ("ferry_operations", "manual"))
        self.assertIn("başladı", upd.callback_query.edit_message_text.await_args.args[0])
        texts = _sent_texts(ctx)
        self.assertTrue(any("https://youtube.com/shorts/abc" in t and t.startswith("✅") for t in texts))
        ctx.bot.send_video.assert_awaited_once()
        self.assertEqual(ctx.bot.send_video.await_args.args[0], CHAT)
        self.assertFalse(os.path.exists(out))   # geçici video silindi
        self.assertFalse(bot._production_lock.locked())

    def test_upload_failed_still_sends_video(self):
        ctx, _, _, _ = self._select("marina_and_yacht_operations", result={"success": True, "youtube_url": "", "title": "t"})
        self.assertTrue(any(t.startswith("⚠️") and "YouTube" in t for t in _sent_texts(ctx)))
        ctx.bot.send_video.assert_awaited_once()

    def test_pipeline_failure_reports_error(self):
        ctx, _, _, _ = self._select("urban_city_disasters", result={"success": False, "error": "kapı reddi"}, video=False)
        self.assertTrue(any(t.startswith("❌ Üretim başarısız") and "kapı reddi" in t for t in _sent_texts(ctx)))
        ctx.bot.send_video.assert_not_awaited()
        self.assertFalse(bot._production_lock.locked())

    def test_pipeline_exception_reports_error_and_releases_lock(self):
        ctx, _, _, _ = self._select("cruise_ship_operations", result={}, side_effect=RuntimeError("boom"))
        self.assertTrue(any(t.startswith("❌ Hata") and "boom" in t for t in _sent_texts(ctx)))
        self.assertFalse(bot._production_lock.locked())

    def test_missing_video_file_reported(self):
        ctx, _, _, _ = self._select("ferry_operations", result={"success": True, "youtube_url": "u", "title": "t"}, video=False)
        ctx.bot.send_video.assert_not_awaited()
        self.assertTrue(any("bulunamadı" in t for t in _sent_texts(ctx)))

    def test_oversized_video_not_sent(self):
        ctx = _context()
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"x")
        self.addCleanup(os.remove, f.name)
        with patch.object(bot, "TELEGRAM_VIDEO_LIMIT", 0):
            asyncio.run(bot.send_video_file(ctx.bot, CHAT, f.name, "t"))
        ctx.bot.send_video.assert_not_awaited()
        self.assertIn("50 MB", _sent_texts(ctx)[0])


if __name__ == "__main__":
    unittest.main()
