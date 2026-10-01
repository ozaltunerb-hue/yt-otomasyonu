#!/usr/bin/env python3
"""
Telegram tetikleyici (bot.py) + domain parametresi (2026-09-26) + iki seviyeli olay menüsü ve
zorunlu olay parametresi (2026-09-29). API çağrısı yok:
Telegram, GPT, Kie, Notion, YouTube mock'lanır. Ücretli hiçbir çağrı yapılmaz.
"""
import asyncio
import json
import os
import re
import sys
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import bot
import core.prompt_generator as pg
from config import settings
import main
from core.creative_engine import (
    DOMAIN_ATTRIBUTES,
    EVENT_ENV_COMPAT,
    EVENT_SHIP_ONLY,
    MARITIME_INSPIRATION_DOMAINS,
    SHIP_INCOMPATIBLE,
    VESSEL_ENVIRONMENTS,
    get_creative_catalyst,
)
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
    u.callback_query.edit_message_reply_markup = AsyncMock()
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

    def _run_generate(self, domain, used_combos=(), event=None, events_seen=None):
        calls = []
        real = pg.get_creative_catalyst

        def spy(**kw):
            calls.append(kw.get("domain"))
            if events_seen is not None:
                events_seen.append(kw.get("event"))
            return real(**kw)

        gen = AsyncMock(return_value={"scenario_summary": "calm harbor", "beat1_action_verb": "sits"})
        config = {"used_combos": list(used_combos), "recent_topics": [], "recent_verbs": [], "domain": domain,
                  "event": event, "prompt_pipeline": "legacy"}   # eski hat testleri (TUR 30)
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
        seen = []
        calls, _, _ = self._run_generate(None, events_seen=seen)
        self.assertEqual(set(calls), {None})
        self.assertEqual(set(seen), {None})

    def test_generate_prompts_forced_event_all_five_scenarios(self):
        event = "Drydock flood gate bursts open"
        seen = []
        _, gen, _ = self._run_generate("shipyard_and_drydock_engineering", event=event, events_seen=seen)
        self.assertEqual(set(seen), {event})
        self.assertEqual(gen.await_count, 5)
        for c in gen.await_args_list:
            self.assertEqual((c.args[0]["forced_event"], c.args[0]["forced_environment"]), (event, "Drydock interior"))


class TestForcedEvent(unittest.TestCase):
    """get_creative_catalyst(event=...): olay zorunlu, ortam EVENT_ENV_COMPAT'a uyumlu, gemi olaya izinli."""

    def _check(self, domain, event, cat):
        self.assertEqual((cat["domain_id"], cat["forced_event"]), (domain, event))
        env, ship = cat["forced_environment"], cat["forced_ship"]
        compat = EVENT_ENV_COMPAT.get(domain, {})
        if event in compat:
            self.assertIn(env, compat[event])
        self.assertIn(env, DOMAIN_ATTRIBUTES[domain]["environments"])
        vessel = VESSEL_ENVIRONMENTS.get(domain)
        if vessel:
            if event in vessel["vessel_only_events"]:
                self.assertIn(env, vessel["environments"])
            self.assertEqual(ship != "None", env in vessel["environments"])
        elif DOMAIN_ATTRIBUTES[domain]["ships"]:
            self.assertIn(ship, EVENT_SHIP_ONLY.get(event, DOMAIN_ATTRIBUTES[domain]["ships"]))
            banned = SHIP_INCOMPATIBLE.get(ship, {})
            self.assertNotIn(event, banned.get("events", set()))
            self.assertNotIn(env, banned.get("environments", set()))
        else:
            self.assertEqual(ship, "None")

    def test_every_event_forced_and_compatible(self):
        for d, a in DOMAIN_ATTRIBUTES.items():
            for e in a["events"]:
                with self.subTest(domain=d, event=e):
                    for _ in range(15):
                        self._check(d, e, get_creative_catalyst(recent_history=[], domain=d, event=e))

    def test_forced_event_beats_recent_history(self):
        d, e = "ferry_operations", "Loading ramp hinge snaps and the ramp drops"
        history = [f"{d}|passenger car ferry|{e.lower()}|ferry terminal ramp|fixed_cctv"] * 3
        for _ in range(10):
            self._check(d, e, get_creative_catalyst(recent_history=history, domain=d, event=e))

    def test_event_without_domain_uses_owner(self):
        cat = get_creative_catalyst(recent_history=[], event="Coastal evacuation")
        self.assertEqual(cat["domain_id"], "coastal_tornado_landfall")

    def test_event_domain_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            get_creative_catalyst(recent_history=[], domain="ferry_operations", event="Coastal evacuation")
        with self.assertRaises(ValueError):
            get_creative_catalyst(recent_history=[], domain="ferry_operations", event="Ship explodes")

    def test_run_pipeline_passes_event_to_prompt_config(self):
        seen = {}

        async def gen(config):
            seen.update(config)
            raise RuntimeError("stop")

        tracker = MagicMock()
        tracker.get_recent_history.return_value = []
        tracker.get_recent_beat1_verbs.return_value = []
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(main, "load_used_combos", return_value=[]), \
             patch.object(main, "NotionTracker", return_value=tracker), patch.object(main, "KieClient"), \
             patch.object(main, "generate_prompts", side_effect=gen):
            result = asyncio.run(main.run_pipeline(skip_upload=True, domain="ferry_operations",
                                                   event="Coastal evacuation", trigger="manual"))
        self.assertFalse(result.get("success"))
        self.assertEqual((seen["domain"], seen["event"]), ("ferry_operations", "Coastal evacuation"))


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


def _buttons(markup):
    return [b for row in markup.inline_keyboard for b in row]


class TestKeyboard(unittest.TestCase):
    def test_seven_domain_buttons(self):
        self.assertEqual(list(bot.DOMAIN_LABELS), DOMAINS)
        buttons = _buttons(bot.domain_keyboard())
        self.assertEqual(len(buttons), 8)   # 2 Eki: + ⛰️ Heyelan
        self.assertEqual([b.callback_data for b in buttons], [f"{bot.CALLBACK_PREFIX}d:{i}" for i in range(8)])

    def test_event_labels_match_pool(self):
        pool = [e for a in DOMAIN_ATTRIBUTES.values() for e in a["events"]]
        self.assertEqual(set(bot.EVENT_LABELS), set(pool))
        for d, a in DOMAIN_ATTRIBUTES.items():
            labels = [bot.EVENT_LABELS[e] for e in a["events"]]
            self.assertEqual(len(labels), len(set(labels)), d)   # aynı menüde iki aynı etiket yok
            for label in labels:
                self.assertLessEqual(len(label), 40, label)

    def test_event_keyboard_per_domain(self):
        for di, d in enumerate(DOMAINS):
            with self.subTest(domain=d):
                rows = bot.event_keyboard(di).inline_keyboard
                events = bot.domain_events(d)   # iskelet hattında sadece iskeleti olan olaylar (TUR 30)
                self.assertEqual([r[0].text for r in rows[:-2]], [bot.EVENT_LABELS[e] for e in events])
                self.assertEqual(rows[-2][0].text, "🎲 Rastgele")
                self.assertEqual(rows[-1][0].text, "🔙 Geri")
                for ei, e in enumerate(events):
                    self.assertEqual(bot.parse_selection(*rows[ei][0].callback_data.split(":")[2:]), (d, e))

    def test_all_callback_data_within_64_bytes(self):
        markups = [bot.domain_keyboard()]
        for di, d in enumerate(DOMAINS):
            markups.append(bot.event_keyboard(di))
            markups += [bot.confirm_keyboard(str(di), str(ei)) for ei in range(len(DOMAIN_ATTRIBUTES[d]["events"]))]
            markups.append(bot.confirm_keyboard(str(di), bot.RANDOM_ID))
        for b in (b for m in markups for b in _buttons(m)):
            self.assertLessEqual(len(b.callback_data.encode()), 64, b.callback_data)   # Telegram sınırı

    def test_application_builds_with_handlers(self):
        app = bot.build_application("123:ABC", CHAT)
        self.assertEqual(app.bot_data["allowed_chat_id"], CHAT)
        self.assertEqual(len(app.handlers[0]), 5)   # start, uret, test, yayin, callback (TUR 29)
        self.assertEqual(app.bot_data["cfg"], {"mode": "TEST", "detail": True, "approval": True})


class TestHandlers(unittest.TestCase):
    def setUp(self):
        self.lock_patch = patch.object(bot, "_production_lock", asyncio.Lock())
        self.lock_patch.start()
        self.addCleanup(self.lock_patch.stop)

    def _click(self, data, chat_id=CHAT):
        ctx, upd = _context(), _update(chat_id, data=bot.CALLBACK_PREFIX + data)
        runner = AsyncMock()
        with patch.object(bot.pipeline, "run_pipeline", runner):
            asyncio.run(bot.on_callback(upd, ctx))
        return upd, runner

    def _select(self, domain, result=None, side_effect=None, chat_id=CHAT, video=True, eid="r"):
        di = DOMAINS.index(domain) if domain in DOMAINS else 99
        ctx, upd = _context(), _update(chat_id, data=f"{bot.CALLBACK_PREFIX}ok:{di}:{eid}")
        path = {}

        async def fake_run(**kw):
            path["kw"] = kw
            if side_effect:
                raise side_effect
            if not result.get("success"):
                return result
            out = os.path.join(tempfile.gettempdir(), f"tg_test_{time.time_ns()}.mp4")
            if video:
                with open(out, "wb") as f:
                    f.write(b"mp4")
                self.addCleanup(lambda: os.path.exists(out) and os.remove(out))
            path["out"] = out
            return dict(result, video_path=out)

        runner = AsyncMock(side_effect=fake_run)
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot.status, "fail"):
            asyncio.run(bot.on_callback(upd, ctx))
        return ctx, upd, runner, path.get("out")

    def test_domain_click_shows_events_without_running(self):
        upd, runner = self._click("d:1")
        runner.assert_not_awaited()
        args, kwargs = upd.callback_query.edit_message_text.await_args
        self.assertIn("Tersane", args[0])
        texts = [b.text for b in _buttons(kwargs["reply_markup"])]
        self.assertIn("🪢 Kızak halatı kopar", texts)
        self.assertNotIn("🚢 Yandan suya indirme", texts)   # iskelet hattında yok (TUR 30)
        self.assertEqual(texts[-2:], ["🎲 Rastgele", "🔙 Geri"])

    def test_event_click_shows_confirm_without_running(self):
        upd, runner = self._click("e:0:1")
        runner.assert_not_awaited()
        args, kwargs = upd.callback_query.edit_message_text.await_args
        for part in ("⛴️ Feribot", "🚧 Rampa menteşesi kopar", "Tahmini maliyet", "175"):
            self.assertIn(part, args[0])
        buttons = _buttons(kwargs["reply_markup"])
        self.assertEqual([b.text for b in buttons], ["✅ Üret", "❌ İptal"])
        self.assertEqual(buttons[0].callback_data, f"{bot.CALLBACK_PREFIX}ok:0:1")

    def test_random_confirm_text(self):
        upd, runner = self._click("e:4:r")
        runner.assert_not_awaited()
        text = upd.callback_query.edit_message_text.await_args.args[0]
        self.assertIn("🌪️ Kıyı Hortumu", text)
        self.assertIn("🎲 Rastgele", text)

    def test_back_returns_to_domains(self):
        upd, runner = self._click("back")
        runner.assert_not_awaited()
        markup = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual(len(_buttons(markup)), 10)   # 8 kategori + 🔍 Ayrıntı / ✋ Onay (TUR 29; 2 Eki heyelan)

    def test_cancel_does_not_run(self):
        upd, runner = self._click("x")
        runner.assert_not_awaited()
        self.assertIn("İptal", upd.callback_query.edit_message_text.await_args.args[0])

    def test_invalid_ids_do_not_run(self):
        for data in ("d:8", "d:x", "e:0:3", "e:0:-1", "ok:0:9", "ok:8:r", "ok:0", "ok:0:1:2", "zzz", "", "back:1"):
            with self.subTest(data=data):
                upd, runner = self._click(data)
                runner.assert_not_awaited()
                self.assertIn("Geçersiz", upd.callback_query.edit_message_text.await_args.args[0])

    def test_unauthorized_menu_clicks_ignored(self):
        for data in ("d:0", "e:0:0", "ok:0:0", "back", "x"):
            with self.subTest(data=data):
                upd, runner = self._click(data, chat_id=999)
                runner.assert_not_awaited()
                upd.callback_query.edit_message_text.assert_not_awaited()
                upd.callback_query.answer.assert_not_awaited()

    def test_busy_menu_clicks_do_not_advance(self):
        for data in ("d:0", "e:0:0", "back"):
            ctx, upd = _context(), _update(data=bot.CALLBACK_PREFIX + data)

            async def go():
                async with bot._production_lock:
                    await bot.on_callback(upd, ctx)
            asyncio.run(go())
            self.assertIn("Üretim sürüyor", upd.callback_query.edit_message_text.await_args.args[0])

    def test_confirm_runs_with_forced_event(self):
        ok = {"success": True, "youtube_url": "u", "title": "t"}
        ctx, upd, runner, _ = self._select("shipyard_and_drydock_engineering", result=ok, eid="0")
        kw = runner.await_args.kwargs
        self.assertEqual((kw["domain"], kw["event"], kw["trigger"]),
                         ("shipyard_and_drydock_engineering", "Restraining cable snaps during slipway launch", "manual"))
        self.assertIn("Kızak halatı kopar", upd.callback_query.edit_message_text.await_args_list[0].args[0])

    def test_unauthorized_command_ignored(self):
        ctx, upd = _context(), _update(chat_id=999)
        asyncio.run(bot.cmd_uret(upd, ctx))
        upd.effective_message.reply_text.assert_not_awaited()

    def test_uret_shows_keyboard(self):
        ctx, upd = _context(), _update()
        asyncio.run(bot.cmd_uret(upd, ctx))
        kwargs = upd.effective_message.reply_text.await_args.kwargs
        self.assertEqual(len([b for r in kwargs["reply_markup"].inline_keyboard for b in r]), 10)   # 2 Eki: 8 kategori
        self.assertIn("🧪 TEST", upd.effective_message.reply_text.await_args.args[0])

    def test_uret_busy(self):
        ctx, upd = _context(), _update()

        async def go():
            async with bot._production_lock:
                await bot.cmd_uret(upd, ctx)
        asyncio.run(go())
        self.assertIn("Üretim sürüyor", upd.effective_message.reply_text.await_args.args[0])

    def test_selection_busy_does_not_run(self):
        ctx, upd = _context(), _update(data=bot.CALLBACK_PREFIX + "ok:0:0")
        runner = AsyncMock()

        async def go():
            async with bot._production_lock:
                await bot.on_callback(upd, ctx)
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
        self.assertEqual((kw["domain"], kw["event"], kw["trigger"]), ("ferry_operations", None, "manual"))   # 🎲 Rastgele
        # TUR 29: varsayılan TEST modu → YouTube adımı atlanır, ayrıntı + onay raporlayıcısı bağlı
        self.assertEqual((kw["mode"], kw["skip_upload"]), ("TEST", True))
        self.assertTrue(kw["reporter"].detail and kw["reporter"].needs_approval)
        self.assertIn("başladı", upd.callback_query.edit_message_text.await_args.args[0])
        texts = _sent_texts(ctx)
        self.assertTrue(any("https://youtube.com/shorts/abc" in t and t.startswith("✅") for t in texts))
        ctx.bot.send_video.assert_awaited_once()
        self.assertEqual(ctx.bot.send_video.await_args.args[0], CHAT)
        self.assertTrue(os.path.exists(out))   # arşiv videosu silinmez (kalıcı kopya)
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


class TestRegionViewMenu(unittest.TestCase):
    """1 Eki, Bahadır: şehir olaylarında olaydan sonra bölge görünümü adımı. Kilitli."""
    CITY = DOMAINS.index("urban_city_disasters")
    LABELS = ["🎲 Rastgele", "🏜️ Körfez metropolü", "🌴 Kuzey Afrika kıyısı", "🏖️ ABD kıyı kasabası",
              "🏘️ Kuzey Avrupa sahili", "🏛️ Fransız rivierası", "🏙️ Doğu Asya kıyısı", "⬅️ Geri"]

    def setUp(self):
        import core.skeleton_pipeline as sk
        self.sk = sk
        sk._VIEW_MEMORY.clear()
        self.addCleanup(sk._VIEW_MEMORY.clear)
        p = patch.object(bot, "_production_lock", asyncio.Lock())
        p.start()
        self.addCleanup(p.stop)

    def _ei(self, event):
        return bot.domain_events("urban_city_disasters").index(event)

    def _click(self, data):
        ctx, upd = _context(), _update(CHAT, data=bot.CALLBACK_PREFIX + data)
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot.status, "fail"):
            asyncio.run(bot.on_callback(upd, ctx))
        return upd, runner

    def test_labels_and_codes_locked(self):
        self.assertEqual(bot.VIEW_LABELS, {
            "gulf_metropolis": "🏜️ Körfez metropolü", "north_african_coast": "🌴 Kuzey Afrika kıyısı",
            "us_coastal_town": "🏖️ ABD kıyı kasabası", "north_european_seaside": "🏘️ Kuzey Avrupa sahili",
            "riviera": "🏛️ Fransız rivierası", "east_asian_coast": "🏙️ Doğu Asya kıyısı"})
        self.assertEqual(bot.VIEW_KEYS, list(self.sk.REGION_VIEWS))
        for label in bot.VIEW_LABELS.values():   # bayrak emojisi (bölgesel gösterge harfleri) yok
            self.assertFalse(any(0x1F1E6 <= ord(ch) <= 0x1F1FF for ch in label), label)

    def test_city_event_shows_view_step(self):
        for event in self.sk.REGION_VIEW_EVENTS:
            with self.subTest(event=event):
                ei = self._ei(event)
                upd, runner = self._click(f"e:{self.CITY}:{ei}")
                runner.assert_not_awaited()
                args, kwargs = upd.callback_query.edit_message_text.await_args
                self.assertIn("Bölge: hangi görünüm?", args[0])
                buttons = _buttons(kwargs["reply_markup"])
                self.assertEqual([b.text for b in buttons], self.LABELS)
                self.assertEqual(buttons[0].callback_data, f"{bot.CALLBACK_PREFIX}v:{self.CITY}:{ei}:r")
                self.assertEqual(buttons[-1].callback_data, f"{bot.CALLBACK_PREFIX}d:{self.CITY}")
                for vi, b in enumerate(buttons[1:-1]):
                    self.assertEqual(b.callback_data, f"{bot.CALLBACK_PREFIX}v:{self.CITY}:{ei}:{vi}")

    def test_non_city_and_random_event_skip_view_step(self):
        for data in ("e:0:1", f"e:{self.CITY}:r", f"e:{DOMAINS.index('marina_and_yacht_operations')}:0"):
            with self.subTest(data=data):
                upd, _ = self._click(data)
                args, kwargs = upd.callback_query.edit_message_text.await_args
                self.assertNotIn("Bölge", args[0])
                self.assertEqual([b.text for b in _buttons(kwargs["reply_markup"])], ["✅ Üret", "❌ İptal"])
        upd, _ = self._click("v:0:1:2")   # şehir dışı olayda bölge kodu geçersiz
        self.assertIn("Geçersiz seçim", upd.callback_query.edit_message_text.await_args.args[0])
        upd, _ = self._click(f"v:{self.CITY}:{self._ei(TIDAL_EVENT)}:9")
        self.assertIn("Geçersiz seçim", upd.callback_query.edit_message_text.await_args.args[0])

    def test_view_click_confirm_and_run(self):
        ei = self._ei(TIDAL_EVENT)
        upd, runner = self._click(f"v:{self.CITY}:{ei}:5")
        runner.assert_not_awaited()
        args, kwargs = upd.callback_query.edit_message_text.await_args
        self.assertIn("Bölge: 🏙️ Doğu Asya kıyısı", args[0])
        self.assertEqual(_buttons(kwargs["reply_markup"])[0].callback_data, f"{bot.CALLBACK_PREFIX}ok:{self.CITY}:{ei}:5")
        upd, runner = self._click(f"ok:{self.CITY}:{ei}:5")
        self.assertEqual(runner.await_args.kwargs["view"], "east_asian_coast")
        self.assertIn("🏙️ Doğu Asya kıyısı", upd.callback_query.edit_message_text.await_args_list[0].args[0])
        upd, runner = self._click(f"ok:{self.CITY}:{ei}:r")
        self.assertIsNone(runner.await_args.kwargs["view"])
        upd, runner = self._click("ok:0:1")   # şehir dışı: view yok
        self.assertIsNone(runner.await_args.kwargs["view"])

    def test_view_callbacks_within_64_bytes(self):
        markups = []
        for event in self.sk.REGION_VIEW_EVENTS:
            ei = str(self._ei(event))
            markups.append(bot.view_keyboard(str(self.CITY), ei))
            markups += [bot.confirm_keyboard(str(self.CITY), ei, v) for v in ["r"] + [str(i) for i in range(6)]]
        for b in (b for m in markups for b in _buttons(m)):
            self.assertLessEqual(len(b.callback_data.encode()), 64, b.callback_data)

    def test_chosen_view_reaches_scene_and_combo_key(self):
        import core.creative_pipeline as cp

        async def gpt(system, user, **kw):
            gpt.user = user
            return {"story": TIDAL_STORY}
        for view in self.sk.REGION_VIEWS:
            with self.subTest(view=view):
                scene = asyncio.run(cp.build_creative_scene("urban_city_disasters", TIDAL_EVENT, [], [], gpt, view=view))
                self.assertEqual(scene["trace"]["view"], view)
                self.assertEqual(scene["trace"]["view_source"], "menü")
                self.assertIn(f"#{view}|", scene["combo_key"])
                self.assertIn(self.sk.REGION_VIEWS[view], gpt.user)
                self.assertIn(self.sk.REGION_VIEWS[view], scene["style_suffix"])
                self.assertIn(scene["spot"], self.sk.view_spots(TIDAL_EVENT, view))   # çakışma kuralı geçerli
                self.assertEqual(self.sk._VIEW_MEMORY[TIDAL_EVENT][-1], view)          # LRU belleğine yazıldı
        with self.assertRaises(ValueError):
            asyncio.run(cp.build_creative_scene("cruise_ship_operations", "Rogue wave breaks over the rail onto the pool deck",
                                                [], [], gpt, view="riviera"))

    def test_random_equals_lru(self):
        import core.creative_pipeline as cp

        async def gpt(system, user, **kw):
            return {"story": TIDAL_STORY}
        order = ["riviera", "gulf_metropolis", "us_coastal_town", "east_asian_coast", "north_african_coast",
                 "north_european_seaside"]
        history = [f"urban_city_disasters|none|{TIDAL_EVENT.lower()}|coastal avenue behind a seawall#{v}|"
                   f"{self.sk.SKELETON_CAMERA}" for v in order]
        expected = self.sk.choose_region_view(TIDAL_EVENT, history)
        scene = asyncio.run(cp.build_creative_scene("urban_city_disasters", TIDAL_EVENT, history, [], gpt))
        self.assertEqual((scene["trace"]["view"], expected), ("riviera", "riviera"))
        self.assertEqual(scene["trace"]["view_source"], "Python, LRU")

    def test_run_pipeline_passes_view_to_prompt_config(self):
        seen = {}

        async def gen(config):
            seen.update(config)
            raise RuntimeError("stop")
        tracker = MagicMock()
        tracker.get_recent_history.return_value = []
        tracker.get_recent_beat1_verbs.return_value = []
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(main, "load_used_combos", return_value=[]), \
             patch.object(main, "NotionTracker", return_value=tracker), patch.object(main, "KieClient"), \
             patch.object(main, "generate_prompts", side_effect=gen):
            asyncio.run(main.run_pipeline(skip_upload=True, domain="urban_city_disasters", event=TIDAL_EVENT,
                                          trigger="manual", view="riviera"))
        self.assertEqual(seen["view"], "riviera")


TIDAL_EVENT = "Tidal wave surges over a coastal city street"
TIDAL_STORY = ("A towering brown tidal wave thick with debris crashes over the seawall onto the coastal road, slamming "
               "into a row of parked cars. The water sweeps the cars into the storefronts as six pedestrians sprint up "
               "the stairs. The wave keeps surging down the street, still dragging cars and debris inland.")


if __name__ == "__main__":
    unittest.main()
