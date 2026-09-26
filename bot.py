#!/usr/bin/env python3
"""
DeepMyster Telegram tetikleyici (python-telegram-bot, polling).

  /uret  → 7 domain butonu → seçilen domain ile main.run_pipeline (senaryo → Kie → YouTube)

Kurallar:
  - Sadece TELEGRAM_CHAT_ID'deki sohbete cevap verir; diğerleri sessizce yok sayılır.
  - Aynı anda tek üretim (kilit). Meşgulken gelen seçim "üretim sürüyor" cevabı alır.
  - Açılışta bekleyen eski güncellemeler atılır: restart, eski bir buton basışını
    ücretli üretime çevirmez.
  - Token ve chat ID sadece ortamdan (.env / Railway Variables) okunur.

Çalıştırma: python bot.py   (Railway start komutu)
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import main as pipeline
from core.creative_engine import MARITIME_INSPIRATION_DOMAINS
from infrastructure.run_status import status
from logger import get_logger

log = get_logger("DeepMysterBot")

# Buton etiketleri; anahtarlar MARITIME_INSPIRATION_DOMAINS ile birebir (test_telegram_bot denetler)
DOMAIN_LABELS = {
    "ferry_operations": "⛴️ Feribot",
    "shipyard_and_drydock_engineering": "🏗️ Tersane",
    "marina_and_yacht_operations": "⛵ Marina & Yat",
    "cruise_ship_operations": "🚢 Kruvaziyer",
    "coastal_tornado_landfall": "🌪️ Kıyı Hortumu",
    "urban_city_disasters": "🏙️ Şehir Afeti",
    "open_beach_coastal_events": "🏖️ Plaj & Sahil",
}
CALLBACK_PREFIX = "uret:"
TELEGRAM_VIDEO_LIMIT = 50 * 1024 * 1024   # Bot API dosya gönderim sınırı

_production_lock = asyncio.Lock()


def load_telegram_config() -> tuple[str, int]:
    """TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID. Eksik/bozuksa açık mesajla durur."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID ortam değişkenleri gerekli (.env / Railway Variables).")
    try:
        return token, int(chat_id)
    except ValueError:
        raise SystemExit(f"TELEGRAM_CHAT_ID sayı olmalı, gelen: {chat_id!r}")


def is_authorized(update: Update, allowed_chat_id: int) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.id == allowed_chat_id


def domain_keyboard() -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(label, callback_data=CALLBACK_PREFIX + key) for key, label in DOMAIN_LABELS.items()]
    return InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])


def _allowed_chat(context: ContextTypes.DEFAULT_TYPE) -> int:
    return context.bot_data["allowed_chat_id"]


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update, _allowed_chat(context)):
        return
    await update.effective_message.reply_text("DeepMyster üretim botu. /uret ile domain seçip video üret.")


async def cmd_uret(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update, _allowed_chat(context)):
        return
    if _production_lock.locked():
        await update.effective_message.reply_text("⏳ Üretim sürüyor, bitince tekrar dene.")
        return
    await update.effective_message.reply_text("Hangi domain?", reply_markup=domain_keyboard())


async def on_domain_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not is_authorized(update, _allowed_chat(context)):
        return
    await query.answer()
    domain = (query.data or "").removeprefix(CALLBACK_PREFIX)
    if domain not in DOMAIN_LABELS:
        await query.edit_message_text("Bilinmeyen domain. /uret ile tekrar dene.")
        return
    if _production_lock.locked():
        await query.edit_message_text("⏳ Üretim sürüyor, bitince tekrar dene.")
        return
    async with _production_lock:
        await query.edit_message_text(
            f"🚀 Üretim başladı: {DOMAIN_LABELS[domain]}\nSenaryo → video → YouTube. Birkaç dakika sürer."
        )
        await produce(context.bot, _allowed_chat(context), domain)


def _run_pipeline_blocking(domain: str, output_path: str) -> dict:
    # Pipeline kendi event loop'unda, ayrı thread'de: bot üretim sırasında cevap vermeye devam eder
    return asyncio.run(pipeline.run_pipeline(domain=domain, trigger="manual", output_path=output_path))


async def produce(bot, chat_id: int, domain: str) -> None:
    """Pipeline'ı çalıştırır, sonucu ve videoyu sohbete gönderir. Hiçbir hata dışarı sızmaz."""
    video_path = os.path.join(tempfile.gettempdir(), f"deepmyster_tg_{domain}_{int(time.time())}.mp4")
    try:
        try:
            result = await asyncio.to_thread(_run_pipeline_blocking, domain, video_path)
        except Exception as e:
            log.error(f"❌ Telegram üretimi çöktü: {e}", exc_info=True)
            status.fail(f"Telegram üretimi çöktü: {e}")
            await bot.send_message(chat_id, f"❌ Hata: {type(e).__name__}: {str(e)[:500]}")
            return

        if not result or not result.get("success"):
            error = (result or {}).get("error") or (result or {}).get("reason") or "Bilinmeyen hata"
            if status.data.get("state") == "running":
                status.fail(error)
            await bot.send_message(chat_id, f"❌ Üretim başarısız: {str(error)[:500]}")
            return

        title = result.get("title", "")
        youtube_url = result.get("youtube_url", "")
        if youtube_url:
            await bot.send_message(chat_id, f"✅ Yüklendi: {title}\n{youtube_url}")
        else:
            await bot.send_message(chat_id, f"⚠️ Video üretildi ama YouTube'a yüklenmedi: {title}")

        await send_video_file(bot, chat_id, result.get("video_path") or video_path, title)
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)


async def send_video_file(bot, chat_id: int, path: str, caption: str) -> None:
    if not path or not os.path.exists(path):
        await bot.send_message(chat_id, "⚠️ Video dosyası bulunamadı, Telegram'a gönderilemedi.")
        return
    if os.path.getsize(path) > TELEGRAM_VIDEO_LIMIT:
        await bot.send_message(chat_id, "⚠️ Video 50 MB'tan büyük, Telegram'a gönderilemedi.")
        return
    try:
        with open(path, "rb") as f:
            await bot.send_video(chat_id, video=f, caption=caption[:1024], supports_streaming=True,
                                 read_timeout=180, write_timeout=180)
    except Exception as e:
        log.error(f"❌ Video Telegram'a gönderilemedi: {e}", exc_info=True)
        await bot.send_message(chat_id, f"⚠️ Video Telegram'a gönderilemedi: {str(e)[:300]}")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error(f"Telegram handler hatası: {context.error}", exc_info=context.error)


def build_application(token: str, allowed_chat_id: int) -> Application:
    # concurrent_updates: üretim sürerken yeni /uret ve buton basışları "üretim sürüyor" cevabı alabilsin
    app = Application.builder().token(token).concurrent_updates(True).build()
    app.bot_data["allowed_chat_id"] = allowed_chat_id
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("uret", cmd_uret))
    app.add_handler(CallbackQueryHandler(on_domain_selected, pattern=f"^{CALLBACK_PREFIX}"))
    app.add_error_handler(on_error)
    return app


def run() -> None:
    token, chat_id = load_telegram_config()
    status.enable(os.environ.get("STATUS_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "status.json"))
    log.info(f"🤖 DeepMyster Telegram botu başlıyor (izinli sohbet: {chat_id})")
    build_application(token, chat_id).run_polling(
        allowed_updates=[Update.MESSAGE, Update.CALLBACK_QUERY],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    run()
