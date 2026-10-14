#!/usr/bin/env python3
"""
Telegram teslim güvencesi (14 Eki 2026, Bahadır). Olay: 14 Eki 09:31 çığ köyü videosu Kie'de üretildi ama Telegram'a
gelmedi; "TEST üretimi tamamlandı" mesajı httpx.ConnectError ile düştü, deliver_video hiç çalışmadı.
Ağsız: Telegram ve Notion sahte, Kie/GPT çağrısı yok.
"""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import httpx
from telegram.error import BadRequest, NetworkError, TimedOut

import bot
from infrastructure import notion_logger as nl

CHAT = 7
PAGE = "3f9d048d-625e-812e-b1b3-d640157fcd63"
KEY = PAGE.replace("-", "")


def _video_msg(file_id="FID"):
    return MagicMock(video=MagicMock(file_id=file_id))


def _tmp_video(test):
    f = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    f.write(b"mp4")
    f.close()
    test.addCleanup(lambda: os.path.exists(f.name) and os.remove(f.name))
    return f.name


class _Base(unittest.TestCase):
    def setUp(self):
        p = patch.object(bot, "SEND_RETRY_DELAYS", (0, 0, 0))
        p.start()
        self.addCleanup(p.stop)
        self.tracker = MagicMock()
        self.notion = MagicMock(return_value=self.tracker)
        self.notion.find_undelivered = MagicMock(return_value=[])
        self.notion.get_record = MagicMock(return_value=None)
        p2 = patch.object(bot, "NotionTracker", self.notion)
        p2.start()
        self.addCleanup(p2.stop)
        self.bot = MagicMock()
        self.bot.send_message = AsyncMock()
        self.bot.send_video = AsyncMock(return_value=_video_msg())

    def statuses(self):
        return [c.args[0] for c in self.tracker.update_status.call_args_list]


class TestRetry(_Base):
    def test_network_errors_retried_then_success(self):
        self.bot.send_message.side_effect = [NetworkError("httpx.ConnectError: "), TimedOut(), "ok"]
        self.assertEqual(asyncio.run(bot.safe_send(self.bot, CHAT, "x")), "ok")
        self.assertEqual(self.bot.send_message.await_count, 3)

    def test_raw_httpx_connect_error_retried(self):
        self.bot.send_message.side_effect = [httpx.ConnectError("tls"), "ok"]
        self.assertEqual(asyncio.run(bot.safe_send(self.bot, CHAT, "x")), "ok")

    def test_gives_up_after_three_retries_without_raising(self):
        self.bot.send_message.side_effect = NetworkError("down")
        self.assertIsNone(asyncio.run(bot.safe_send(self.bot, CHAT, "x")))
        self.assertEqual(self.bot.send_message.await_count, 4)   # ilk deneme + 3 yeniden deneme (2, 5, 10 sn)

    def test_bad_request_not_retried(self):
        self.bot.send_message.side_effect = BadRequest("chat not found")
        self.assertIsNone(asyncio.run(bot.safe_send(self.bot, CHAT, "x")))
        self.assertEqual(self.bot.send_message.await_count, 1)

    def test_delays_and_timeouts_locked(self):
        self.assertEqual(bot.CONNECT_TIMEOUT, 20.0)
        sleeps = []

        async def fake_sleep(d):
            sleeps.append(d)
        with patch.object(bot, "SEND_RETRY_DELAYS", (2, 5, 10)), patch.object(bot.asyncio, "sleep", fake_sleep):
            self.bot.send_message.side_effect = NetworkError("down")
            asyncio.run(bot.safe_send(self.bot, CHAT, "x"))
        self.assertEqual(sleeps, [2, 5, 10])
        app = bot.build_application("123:ABC", CHAT)
        timeouts = [r._client.timeout for r in app.bot._request]
        self.assertTrue(all(t.connect == 20.0 for t in timeouts))   # long polling ve gönderimler
        self.assertEqual((timeouts[1].read, timeouts[1].write), (20.0, 30.0))


class TestProduceDelivery(_Base):
    def run_produce(self, path, page=PAGE, video_cdn_url=""):
        res = {"success": True, "title": "T", "mode": bot.MODE_TEST, "video_path": path, "notion_page_id": page,
               "archive_dir": "", "video_cdn_url": video_cdn_url}
        data = {}
        with patch.object(bot, "_run_pipeline_blocking", return_value=res):
            asyncio.run(bot.produce(self.bot, CHAT, "avalanche_disasters", cfg=bot.default_cfg(bot.MODE_TEST),
                                    bot_data=data))
        return data

    def test_result_message_fails_but_video_still_sent(self):
        # 14 Eki olayı: sonuç mesajı ağ hatasıyla düşer, video yine gider
        self.bot.send_message.side_effect = NetworkError("httpx.ConnectError: ")
        data = self.run_produce(_tmp_video(self))
        self.bot.send_video.assert_awaited_once()
        self.tracker.set_telegram_file_id.assert_called_once_with("FID")
        self.assertNotIn(nl.STATUS_UNDELIVERED, self.statuses())
        self.assertIn(KEY, data["delivered"])

    def test_video_fails_after_retries_marks_undelivered(self):
        self.bot.send_video.side_effect = NetworkError("down")
        data = self.run_produce(_tmp_video(self))
        self.assertEqual(self.bot.send_video.await_count, 4)
        self.assertEqual(self.statuses(), [nl.STATUS_UNDELIVERED])
        self.tracker.set_telegram_file_id.assert_not_called()
        self.assertIn(KEY, data["undelivered"])
        last = self.bot.send_message.call_args_list[-1]
        self.assertIn("teslim edilemedi", last.args[1])
        button = last.kwargs["reply_markup"].inline_keyboard[0][0]
        self.assertEqual(button.text, "🔁 Yeniden gönder")
        self.assertEqual(button.callback_data, f"{bot.CALLBACK_PREFIX}rs:{KEY}")
        self.assertLessEqual(len(button.callback_data.encode()), 64)

    def test_missing_file_falls_back_to_kie_link(self):
        tmp = _tmp_video(self)
        with patch.object(bot, "download_video", return_value=tmp) as dl, patch.object(bot, "cleanup_video") as cl:
            self.run_produce("/yok/video.mp4", video_cdn_url="https://tempfile.aiquickdraw.com/x.mp4")
        dl.assert_called_once_with("https://tempfile.aiquickdraw.com/x.mp4")
        cl.assert_called_once_with(tmp)
        self.bot.send_video.assert_awaited_once()

    def test_expired_link_and_no_file_marks_undelivered(self):
        with patch.object(bot, "download_video", side_effect=RuntimeError("404")):
            self.run_produce("/yok/video.mp4", video_cdn_url="https://tempfile.aiquickdraw.com/x.mp4")
        self.bot.send_video.assert_not_awaited()
        self.assertEqual(self.statuses(), [nl.STATUS_UNDELIVERED])
        self.assertTrue(any("bulunamadı" in c.args[1] for c in self.bot.send_message.call_args_list))

    def test_error_paths_never_raise(self):
        self.bot.send_message.side_effect = NetworkError("down")
        for res in ({"success": False, "reason": "cancelled"}, {"success": False, "error": "kapı"}):
            with patch.object(bot, "_run_pipeline_blocking", return_value=res), patch.object(bot.status, "fail"):
                asyncio.run(bot.produce(self.bot, CHAT, "avalanche_disasters"))
        with patch.object(bot, "_run_pipeline_blocking", side_effect=RuntimeError("boom")), \
                patch.object(bot.status, "fail"):
            asyncio.run(bot.produce(self.bot, CHAT, "avalanche_disasters"))

    def test_approval_message_failure_cancels(self):
        self.bot.send_message.side_effect = NetworkError("down")

        async def go():
            r = bot.TelegramReporter(self.bot, CHAT, asyncio.get_running_loop(), {}, True, True, timeout=5)
            return await r.approve({"prompt": "p", "story": "p", "style_suffix": ""})
        self.assertFalse(asyncio.run(go()))


class TestStartupRecovery(_Base):
    def rec(self, **kw):
        return {"page_id": PAGE, "status": nl.STATUS_TEST_DONE, "mode": bot.MODE_TEST, "title": "Çığ köyü",
                "telegram_file_id": "", "video_url": "https://tempfile.aiquickdraw.com/x.mp4", "youtube_url": "",
                "date": "2026-10-14T06:28:00.000+00:00", "combo_key": "", "task_id": "t", **kw}

    def test_orphan_recovered_once(self):
        started = datetime(2026, 10, 14, 7, 0, tzinfo=timezone.utc)
        self.notion.find_undelivered.return_value = [self.rec()]
        tmp = _tmp_video(self)
        data = {}
        with patch.object(bot, "download_video", return_value=tmp), patch.object(bot, "cleanup_video"), \
                patch.object(bot.settings, "ARCHIVE_DIR", tempfile.mkdtemp()):
            sent = asyncio.run(bot.redeliver_missing(self.bot, CHAT, data, started))
            # Notion henüz File ID'yi göstermese bile ikinci kurtarma aynı kaydı tekrar göndermez
            again = asyncio.run(bot.redeliver_missing(self.bot, CHAT, data, started))
        self.assertEqual(sent, [PAGE])
        self.assertEqual(again, [])
        self.bot.send_video.assert_awaited_once()
        self.assertTrue(self.bot.send_video.call_args.kwargs["caption"].startswith("🧪 TEST | ♻️ Kurtarıldı: "))
        self.tracker.set_telegram_file_id.assert_called_once_with("FID")
        self.assertEqual(self.statuses(), [nl.STATUS_TEST_DONE])   # teslim sonrası tamamlandıya döner
        since = self.notion.find_undelivered.call_args.args[0]
        self.assertEqual(since, (started - timedelta(hours=24)).isoformat())

    def test_record_after_startup_skipped_and_archive_preferred(self):
        started = datetime(2026, 10, 14, 7, 0, tzinfo=timezone.utc)
        root = tempfile.mkdtemp()
        adir = os.path.join(root, "2026-10-14_062848_avalanche_disasters_4a81a741")
        os.makedirs(adir)
        with open(os.path.join(adir, "video.mp4"), "wb") as f:
            f.write(b"mp4")
        with open(os.path.join(adir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump({"notion_page_id": PAGE}, f)
        later = self.rec(page_id="11111111-2222-3333-4444-555555555555", date="2026-10-14T07:05:00+00:00")
        self.notion.find_undelivered.return_value = [self.rec(), later]
        with patch.object(bot, "download_video") as dl, patch.object(bot.settings, "ARCHIVE_DIR", root):
            sent = asyncio.run(bot.redeliver_missing(self.bot, CHAT, {}, started))
        self.assertEqual(sent, [PAGE])
        dl.assert_not_called()   # arşiv varken Kie linki indirilmez

    def test_publish_record_restores_status_by_youtube(self):
        self.assertEqual(bot.done_status(self.rec()), nl.STATUS_TEST_DONE)
        self.assertEqual(bot.done_status(self.rec(mode=bot.MODE_PUBLISH, youtube_url="https://y")), nl.STATUS_COMPLETED)
        self.assertEqual(bot.done_status(self.rec(mode=bot.MODE_PUBLISH)), nl.STATUS_UPLOAD_FAILED)

    def test_notion_query_shape(self):
        self.assertIn(nl.STATUS_UNDELIVERED, nl.DELIVERABLE_STATUSES)
        self.assertIn(nl.STATUS_UNDELIVERED, nl.USED_COMBO_STATUSES)
        calls = []

        def fake(method, url, json=None):
            calls.append(json)
            return {"results": []}
        with patch.object(nl, "_notion_request", fake), patch.object(nl.settings, "NOTION_ENABLED", True), \
                patch.object(nl.settings, "IS_DRY_RUN", False):
            self.assertEqual(nl.NotionTracker.find_undelivered("2026-10-13T07:00:00+00:00"), [])
        self.assertEqual(len(calls), len(nl.DELIVERABLE_STATUSES))
        conds = calls[0]["filter"]["and"]
        self.assertIn({"property": "Telegram File ID", "rich_text": {"is_empty": True}}, conds)
        self.assertIn({"property": "Video URL", "url": {"is_not_empty": True}}, conds)


class TestTeslimCommand(_Base):
    def update(self):
        u = MagicMock()
        u.effective_chat.id = CHAT
        ctx = MagicMock()
        ctx.bot = self.bot
        ctx.bot_data = {"allowed_chat_id": CHAT}
        return u, ctx

    def test_empty_list(self):
        u, ctx = self.update()
        asyncio.run(bot.cmd_teslim(u, ctx))
        self.assertEqual(self.bot.send_message.call_args.args[1], bot.NO_UNDELIVERED_TEXT)

    def test_lists_with_resend_button_and_resend(self):
        rec = TestStartupRecovery.rec(self)
        self.notion.find_undelivered.return_value = [rec]
        u, ctx = self.update()
        asyncio.run(bot.cmd_teslim(u, ctx))
        last = self.bot.send_message.call_args
        self.assertIn("Çığ köyü", last.args[1])
        self.assertEqual(last.kwargs["reply_markup"].inline_keyboard[0][0].callback_data, f"{bot.CALLBACK_PREFIX}rs:{KEY}")
        # düğmeye basılır: Notion'dan okunur, Kie linkinden gönderilir (Kie API çağrısı yok)
        self.notion.get_record.return_value = rec
        q = MagicMock(data=f"{bot.CALLBACK_PREFIX}rs:{KEY}", answer=AsyncMock(), edit_message_reply_markup=AsyncMock())
        u.callback_query = q
        with patch.object(bot, "download_video", return_value=_tmp_video(self)), patch.object(bot, "cleanup_video"), \
                patch.object(bot.settings, "ARCHIVE_DIR", tempfile.mkdtemp()):
            asyncio.run(bot.on_callback(u, ctx))
        self.notion.get_record.assert_called_once_with(KEY)
        self.bot.send_video.assert_awaited_once()
        self.tracker.set_telegram_file_id.assert_called_once_with("FID")
        # zaten teslim edilmiş kayıt tekrar gönderilmez
        self.notion.get_record.return_value = {**rec, "telegram_file_id": "FID"}
        asyncio.run(bot.on_callback(u, ctx))
        self.bot.send_video.assert_awaited_once()
        self.assertIn("zaten teslim edildi", self.bot.send_message.call_args.args[1])

    def test_command_registered(self):
        self.assertIn("teslim", [c.command for c in bot.BOT_COMMANDS])
        app = bot.build_application("123:ABC", CHAT)
        self.assertIn("teslim", [c for h in app.handlers[0] for c in getattr(h, "commands", ())])


if __name__ == "__main__":
    unittest.main()
