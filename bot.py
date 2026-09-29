#!/usr/bin/env python3
"""
DeepMyster Telegram tetikleyici (python-telegram-bot, polling).

  /uret → 7 kategori butonu → kategorinin olay butonları (+ 🎲 Rastgele, 🔙 Geri)
        → onay mesajı (kategori + olay + tahmini maliyet) → ✅ Üret ile main.run_pipeline
          (senaryo → Kie → YouTube). Olay zorunlu olay olarak gider; ortam/gemi/kamera otomatik.

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
from core.creative_engine import DOMAIN_ATTRIBUTES, SIDE_LAUNCH_EVENT
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

# Olay butonları; anahtarlar DOMAIN_ATTRIBUTES "events" ile birebir (test_telegram_bot denetler)
EVENT_LABELS = {
    # Feribot
    "Lashing chain snaps and a parked car breaks loose": "⛓️ Zincir kopar, araç kayar",
    "Loading ramp hinge snaps and the ramp drops": "🚧 Rampa menteşesi kopar",
    "Green wave breaks over the rail onto the vehicle deck": "🌊 Dalga araç güvertesine vurur",
    # Tersane
    SIDE_LAUNCH_EVENT: "🚢 Yandan suya indirme",
    "Restraining cable snaps during slipway launch": "🪢 Kızak halatı kopar",
    "Keel blocks collapse under the launching hull": "🧱 Omurga takozları çöker",
    "Drydock flood gate bursts open": "💦 Havuz kapağı patlar",
    "Timber shores snap and the hull tips on its keel blocks": "🪵 Destek kütükleri kırılır",
    "Crane sling snaps while lowering the hull into the water": "🏗️ Vinç askısı kopar",
    # Marina & Yat
    "Mooring line snaps in a storm gust": "🪢 Halat fırtınada kopar",
    "Jammed throttle sends the boat careening": "🚤 Gaz kolu takılır",
    "Storm surge wave lifts and buckles the floating pontoon": "🌊 Dalga yüzer iskeleyi büker",
    "Passing boat's wake slams the boat sideways": "💥 Geçen teknenin dalgası çarpar",
    # Kruvaziyer
    "Mooring line snaps and whips across the quay": "🪢 Halat kopar, rıhtımı savurur",
    "Gangway tears loose as the hull surges": "🪜 Yolcu köprüsü kopar",
    "Rogue wave breaks over the rail onto the pool deck": "🌊 Dev dalga havuz güvertesinde",
    "Heavy roll tilts the deck and sends loungers sliding": "↔️ Yalpa şezlongları kaydırır",
    # Kıyı Hortumu
    "Tornado forming offshore": "🌪️ Açıkta hortum oluşur",
    "Tornado approaching coastline": "🌪️ Hortum kıyıya yaklaşır",
    "Tornado making landfall": "🌪️ Hortum karaya vurur",
    "Coastal evacuation": "🏃 Kıyı tahliyesi",
    "Waterfront disruption": "🏚️ Sahil şeridi karışır",
    "Tornado rain bands and flying debris lash the waterfront": "🌧️ Yağmur ve uçan enkaz",
    "Coastal debris movement": "🪨 Kıyıda enkaz savrulur",
    "Marina equipment reacting to severe weather": "⚓ Marina ekipmanı savrulur",
    # Şehir Afeti
    "Severe storm hitting downtown": "⛈️ Şehir merkezine fırtına",
    "Flash flooding in city streets": "🌊 Caddelerde ani sel",
    "Storm gust tears signs and scaffolding loose downtown": "🪧 Tabela ve iskele uçar",
    "Falling outdoor objects caused by severe weather": "🧱 Yukarıdan nesneler düşer",
    "Sudden coastal storm reaching the urban district": "🌀 Kıyı fırtınası şehre ulaşır",
    "Major weather event disrupting city traffic": "🚗 Trafik felç olur",
    "Heavy rain overwhelming city streets": "🌧️ Sağanak caddeleri basar",
    # Plaj & Sahil
    "Tornado approaching an open beach": "🌪️ Hortum plaja yaklaşır",
    "Sudden extreme storm hitting the beach": "⛈️ Plaja ani fırtına",
    "Storm gust rips umbrellas and beach chairs into the air": "⛱️ Şemsiyeler havaya uçar",
    "Large waves reaching the beach": "🌊 Dev dalgalar plaja ulaşır",
    "Severe storm disrupting a beachfront area": "🌬️ Sahil şeridinde fırtına",
    "Beach evacuation during extreme weather": "🏃 Plaj tahliyesi",
    "Coastal flooding reaching the beachfront": "💧 Sel sahile ulaşır",
}
RANDOM_LABEL = "🎲 Rastgele"
# Video başı ~175 Kie kredisi (BASLANGIC.md, 2026-09 ölçümü) + birkaç GPT çağrısı
ESTIMATED_COST = "~175 Kie kredisi + birkaç GPT çağrısı"

# Callback verisi kısa ID'lerle (Telegram 64 bayt sınırı): domain ve olay listedeki sıra numarası.
#   uret:d:<di>         → olay menüsü        uret:e:<di>:<ei|r> → onay mesajı
#   uret:ok:<di>:<ei|r> → üretimi başlat     uret:back → kategori menüsü    uret:x → iptal
# Sıra değişirse eski butonun olayı kayar; onay mesajı olayı gösterdiği için fark edilmeden üretim başlamaz.
CALLBACK_PREFIX = "uret:"
RANDOM_ID = "r"
DOMAIN_KEYS = list(DOMAIN_LABELS)
TELEGRAM_VIDEO_LIMIT = 50 * 1024 * 1024   # Bot API dosya gönderim sınırı
BUSY_TEXT = "⏳ Üretim sürüyor, bitince tekrar dene."

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


def domain_events(domain: str) -> list[str]:
    return DOMAIN_ATTRIBUTES[domain]["events"]


def domain_keyboard() -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(label, callback_data=f"{CALLBACK_PREFIX}d:{i}")
               for i, label in enumerate(DOMAIN_LABELS.values())]
    return InlineKeyboardMarkup([buttons[i:i + 2] for i in range(0, len(buttons), 2)])


def event_keyboard(di: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(EVENT_LABELS[e], callback_data=f"{CALLBACK_PREFIX}e:{di}:{ei}")]
            for ei, e in enumerate(domain_events(DOMAIN_KEYS[di]))]
    rows.append([InlineKeyboardButton(RANDOM_LABEL, callback_data=f"{CALLBACK_PREFIX}e:{di}:{RANDOM_ID}")])
    rows.append([InlineKeyboardButton("🔙 Geri", callback_data=f"{CALLBACK_PREFIX}back")])
    return InlineKeyboardMarkup(rows)


def confirm_keyboard(di: str, eid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Üret", callback_data=f"{CALLBACK_PREFIX}ok:{di}:{eid}"),
        InlineKeyboardButton("❌ İptal", callback_data=f"{CALLBACK_PREFIX}x"),
    ]])


def parse_selection(di_raw: str, eid: str | None = None) -> tuple[str, str | None] | None:
    """Kısa ID → (domain, olay). Olay None = rastgele (motor seçer). Geçersizse None."""
    if not di_raw.isdigit() or int(di_raw) >= len(DOMAIN_KEYS):
        return None
    domain = DOMAIN_KEYS[int(di_raw)]
    if eid is None or eid == RANDOM_ID:
        return domain, None
    events = domain_events(domain)
    if not eid.isdigit() or int(eid) >= len(events):
        return None
    return domain, events[int(eid)]


def selection_label(event: str | None) -> str:
    return EVENT_LABELS[event] if event else RANDOM_LABEL


def confirm_text(domain: str, event: str | None) -> str:
    return (f"Kategori: {DOMAIN_LABELS[domain]}\n"
            f"Olay: {selection_label(event)}{'' if event else ' (motor seçer)'}\n"
            f"Tahmini maliyet: {ESTIMATED_COST}\n\n"
            "Üretim sadece ✅ Üret'e basınca başlar.")


def _allowed_chat(context: ContextTypes.DEFAULT_TYPE) -> int:
    return context.bot_data["allowed_chat_id"]


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update, _allowed_chat(context)):
        return
    await update.effective_message.reply_text("DeepMyster üretim botu. /uret ile kategori ve olay seçip video üret.")


async def cmd_uret(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update, _allowed_chat(context)):
        return
    if _production_lock.locked():
        await update.effective_message.reply_text(BUSY_TEXT)
        return
    await update.effective_message.reply_text("Hangi kategori?", reply_markup=domain_keyboard())


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menü adımları: kategori → olay → onay → üretim. Üretimi sadece ✅ Üret başlatır."""
    query = update.callback_query
    if not is_authorized(update, _allowed_chat(context)):
        return
    await query.answer()
    action, *args = (query.data or "").removeprefix(CALLBACK_PREFIX).split(":")

    if action == "x" and not args:
        await query.edit_message_text("❌ İptal edildi. /uret ile yeniden başlayabilirsin.")
        return
    if _production_lock.locked():
        await query.edit_message_text(BUSY_TEXT)
        return
    if action == "back" and not args:
        await query.edit_message_text("Hangi kategori?", reply_markup=domain_keyboard())
        return

    sel = None
    if action == "d" and len(args) == 1:
        sel = parse_selection(args[0])
    elif action in ("e", "ok") and len(args) == 2:
        sel = parse_selection(*args)
    if sel is None:
        await query.edit_message_text("Geçersiz seçim. /uret ile tekrar dene.")
        return
    domain, event = sel

    if action == "d":
        await query.edit_message_text(f"{DOMAIN_LABELS[domain]}: hangi olay?", reply_markup=event_keyboard(int(args[0])))
    elif action == "e":
        await query.edit_message_text(confirm_text(domain, event), reply_markup=confirm_keyboard(*args))
    else:
        async with _production_lock:
            await query.edit_message_text(
                f"🚀 Üretim başladı: {DOMAIN_LABELS[domain]} / {selection_label(event)}\n"
                "Senaryo → video → YouTube. Birkaç dakika sürer."
            )
            await produce(context.bot, _allowed_chat(context), domain, event)


def _run_pipeline_blocking(domain: str, event: str | None, output_path: str) -> dict:
    # Pipeline kendi event loop'unda, ayrı thread'de: bot üretim sırasında cevap vermeye devam eder
    return asyncio.run(pipeline.run_pipeline(domain=domain, event=event, trigger="manual", output_path=output_path))


async def produce(bot, chat_id: int, domain: str, event: str | None = None) -> None:
    """Pipeline'ı çalıştırır, sonucu ve videoyu sohbete gönderir. Hiçbir hata dışarı sızmaz."""
    video_path = os.path.join(tempfile.gettempdir(), f"deepmyster_tg_{domain}_{int(time.time())}.mp4")
    try:
        try:
            result = await asyncio.to_thread(_run_pipeline_blocking, domain, event, video_path)
        except Exception as e:
            log.error(f"❌ Telegram üretimi çöktü: {e}", exc_info=True)
            status.fail(f"Telegram üretimi çöktü: {e}")
            await bot.send_message(chat_id, f"❌ Hata: {type(e).__name__}: {str(e)[:500]}")
            return

        if not result or not result.get("success"):
            error = (result or {}).get("error") or (result or {}).get("reason") or "Bilinmeyen hata"
            if status.data.get("state") == "running":
                status.fail(error)
            # Kalite kapısı retlerinde deneme başına tek satır özet (TUR 25): ham JSON 500 karakterde kesiliyordu
            summary = (result or {}).get("error_summary") or str(error)[:500]
            await bot.send_message(chat_id, f"❌ Üretim başarısız: {summary}"[:4000])
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
    app.add_handler(CallbackQueryHandler(on_callback, pattern=f"^{CALLBACK_PREFIX}"))
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
