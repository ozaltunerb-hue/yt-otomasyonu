#!/usr/bin/env python3
"""
DeepMyster Telegram tetikleyici (python-telegram-bot, polling).

  /uret → 7 kategori butonu (+ 🔍 Ayrıntı / ✋ Onay aç-kapa) → kategorinin olay butonları (+ 🎲 Rastgele,
        🔙 Geri) → onay mesajı (kategori + olay + mod + tahmini maliyet) → ✅ Üret ile main.run_pipeline.
        Olay zorunlu olay olarak gider; ortam/gemi/kamera otomatik.
  Modlar (TUR 29): 🧪 TEST varsayılan, her açılışta TEST. Hat yayınla birebir aynı, sadece YouTube atlanır.
        /yayin + onay butonu ile YAYIN; settings.PUBLISH_LOCKED açılmadan YAYIN'a geçilemez.
  🔍 Ayrıntı: seçim, 5 aday, seçilen, simplifier, Kie'ye giden TAM prompt (4096'yı aşan mesaj bölünür).
  ✋ Onay: Kie'ye göndermeden önce "✅ Kie'ye gönder / ❌ İptal". Onaysız ücretli çağrı yok.
  Video altında 👍/👎 → Notion "Puan". Açılışta restart'tan kalan task'lar kurtarılır.

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
import concurrent.futures
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import main as pipeline
from config import settings
from core.creative_engine import DOMAIN_ATTRIBUTES, SIDE_LAUNCH_EVENT
from core.skeleton_pipeline import REGION_VIEW_EVENTS, REGION_VIEWS, skeleton_events
from core.trace_format import format_final_prompt, format_generation, sections_to_text, split_message
from infrastructure.archive import update_meta
from infrastructure.notion_logger import NotionTracker
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
    "landslide_disasters": "⛰️ Heyelan",   # 2 Eki, Bahadır (TASLAK olaylar)
    "fire_disasters": "🔥 Yangın",          # 8 Eki, Bahadır (TASLAK olaylar)
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
    "Mooring line snaps in a storm gust": "🪢 Halat fırtınada kopar",   # 1 Eki: iskelet dışı, menüde görünmez
    "Yacht loses control and rams moored boats in the marina": "🛥️ Yat kontrolsüz marinaya dalar",   # 1 Eki: iskelet dışı, menüde görünmez
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
    # 4 Eki (TASLAK): yapılandırılmış hat hortum olayları
    "Tornado crosses a marina quay": "🌪️ Hortum marina rıhtımını geçer",
    "Tornado sweeps down a coastal avenue": "🌪️ Hortum sahil caddesini süpürür",
    "Coastal debris movement": "🪨 Kıyıda enkaz savrulur",
    "Marina equipment reacting to severe weather": "⚓ Marina ekipmanı savrulur",
    # Şehir Afeti
    "Severe storm hitting downtown": "⛈️ Şehir merkezine fırtına",
    "Flash flooding in city streets": "🌊 Caddelerde ani sel",
    "Storm gust tears signs and scaffolding loose downtown": "🪧 Tabela ve iskele uçar",
    "Tidal wave surges over a coastal city street": "🌊 Kıyı şehrinde dev dalga baskını",
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
    # Heyelan (2 Eki, Bahadır; TASLAK)
    "Mudslide pours down a hillside street": "🌧️ Yamaç sokağına çamur seli",
    "Rain-soaked slope collapses onto a roadside": "⛰️ Yamaç çökmesi yola iner",
    "Mud and debris torrent tears through a hillside village": "🏘️ Köy yamacından çamur akıntısı",
    # Yangın (8 Eki, Bahadır; TASLAK)
    "Wall of flames sweeps into a hillside neighborhood": "🔥 Orman yangını mahalleye ulaşır",
    "Flames race up a tower facade": "🔥 Apartman cephe yangını",
    "Fire tornado tears across a burning roadside": "🔥 Ateş hortumu",
    "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood": "🔥 Yangın söndürme helikopteri",   # 10 Eki
}
RANDOM_LABEL = "🎲 Rastgele"
# Bölge görünümü menüsü (1 Eki, Bahadır): sadece REGION_VIEW_EVENTS (sel, kıyı dalga). Bayrak emojisi yok.
# Kısa kod = REGION_VIEWS sırası (0-5); 🎲 Rastgele = LRU.
VIEW_LABELS = {
    "gulf_metropolis": "🏜️ Körfez metropolü",
    "north_african_coast": "🌴 Kuzey Afrika kıyısı",
    "us_coastal_town": "🏖️ ABD kıyı kasabası",
    "north_european_seaside": "🏘️ Kuzey Avrupa sahili",
    "riviera": "🏛️ Fransız rivierası",
    "east_asian_coast": "🏙️ Doğu Asya kıyısı",
}
VIEW_KEYS = list(REGION_VIEWS)
if set(VIEW_LABELS) != set(VIEW_KEYS):
    raise RuntimeError(f"VIEW_LABELS görünümlerle uyuşmuyor: {set(VIEW_LABELS) ^ set(VIEW_KEYS)}")
VIEW_RANDOM_LABEL = "🎲 Rastgele (sıradaki görünüm)"
# Video başı ~175 Kie kredisi (BASLANGIC.md, 2026-09 ölçümü) + birkaç GPT çağrısı
ESTIMATED_COST = "~175 Kie kredisi + birkaç GPT çağrısı"

# Callback verisi kısa ID'lerle (Telegram 64 bayt sınırı): domain ve olay listedeki sıra numarası.
#   uret:d:<di>         → olay menüsü        uret:e:<di>:<ei|r> → onay mesajı (şehir olayında bölge menüsü)
#   uret:v:<di>:<ei>:<vi|r> → bölge seçildi, onay mesajı (sadece REGION_VIEW_EVENTS)
#   uret:ok:<di>:<ei|r>[:<vi|r>] → üretimi başlat     uret:back → kategori menüsü    uret:x → iptal
#   uret:t:<d|o>        → 🔍 Ayrıntı / ✋ Onay aç-kapa        uret:y:<ok|no> → yayın moduna geçiş onayı
#   uret:ap:<token>:<y|n> → Kie gönderim onayı               uret:r:<sayfa>:<g|b> → 👍 / 👎 puan
# Sıra değişirse eski butonun olayı kayar; onay mesajı olayı gösterdiği için fark edilmeden üretim başlamaz.
CALLBACK_PREFIX = "uret:"
RANDOM_ID = "r"
DOMAIN_KEYS = list(DOMAIN_LABELS)
TELEGRAM_VIDEO_LIMIT = 50 * 1024 * 1024   # Bot API dosya gönderim sınırı
BUSY_TEXT = "⏳ Üretim sürüyor, bitince tekrar dene."
APPROVAL_TIMEOUT = 30 * 60   # ✋ Onay bu sürede gelmezse Kie'ye gönderilmez
MODE_TEST, MODE_PUBLISH = pipeline.MODE_TEST, pipeline.MODE_PUBLISH
RATINGS = {"g": ("iyi", "👍"), "b": ("kötü", "👎")}
BOT_COMMANDS = [
    BotCommand("uret", "Kategori ve olay seçip video üret"),
    BotCommand("test", "🧪 TEST moduna geç (YouTube'a yüklenmez)"),
    BotCommand("yayin", "📢 Yayın moduna geç (onaylı; şu an kilitli)"),
]

_production_lock = asyncio.Lock()


def default_cfg(mode: str = MODE_TEST) -> dict:
    """Mod ayarları. TEST: 🔍 Ayrıntı ve ✋ Onay açık. YAYIN: ikisi kapalı. Bot her açılışta TEST'le başlar."""
    return {"mode": mode, "detail": mode == MODE_TEST, "approval": mode == MODE_TEST}


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
    """Menüdeki olaylar. creative (varsayılan) ve skeleton hatlarında aynı 22 olay; eski hatta hepsi."""
    if settings.PROMPT_PIPELINE in ("creative", "skeleton"):
        return skeleton_events(domain)
    return DOMAIN_ATTRIBUTES[domain]["events"]


def _onoff(v: bool) -> str:
    return "AÇIK" if v else "KAPALI"


def mode_label(mode: str) -> str:
    return "🧪 TEST (YouTube'a yüklenmez)" if mode == MODE_TEST else "📢 YAYIN"


def menu_text(cfg: dict) -> str:
    return (f"Mod: {mode_label(cfg['mode'])}\n🔍 Ayrıntı: {_onoff(cfg['detail'])} · ✋ Onay: {_onoff(cfg['approval'])}\n\n"
            "Hangi kategori?")


def domain_keyboard(cfg: dict | None = None) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(label, callback_data=f"{CALLBACK_PREFIX}d:{i}")
               for i, label in enumerate(DOMAIN_LABELS.values())]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    if cfg is not None:
        rows.append([InlineKeyboardButton(f"🔍 Ayrıntı: {_onoff(cfg['detail'])}", callback_data=f"{CALLBACK_PREFIX}t:d"),
                     InlineKeyboardButton(f"✋ Onay: {_onoff(cfg['approval'])}", callback_data=f"{CALLBACK_PREFIX}t:o")])
    return InlineKeyboardMarkup(rows)


def event_keyboard(di: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(EVENT_LABELS[e], callback_data=f"{CALLBACK_PREFIX}e:{di}:{ei}")]
            for ei, e in enumerate(domain_events(DOMAIN_KEYS[di]))]
    rows.append([InlineKeyboardButton(RANDOM_LABEL, callback_data=f"{CALLBACK_PREFIX}e:{di}:{RANDOM_ID}")])
    rows.append([InlineKeyboardButton("🔙 Geri", callback_data=f"{CALLBACK_PREFIX}back")])
    return InlineKeyboardMarkup(rows)


def view_keyboard(di: str, ei: str) -> InlineKeyboardMarkup:
    """Bölge adımı: 🎲 Rastgele, 6 görünüm, ⬅️ Geri (olay menüsüne)."""
    buttons = [InlineKeyboardButton(VIEW_LABELS[v], callback_data=f"{CALLBACK_PREFIX}v:{di}:{ei}:{vi}")
               for vi, v in enumerate(VIEW_KEYS)]
    rows = [[InlineKeyboardButton(RANDOM_LABEL, callback_data=f"{CALLBACK_PREFIX}v:{di}:{ei}:{RANDOM_ID}")]]
    rows += [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("⬅️ Geri", callback_data=f"{CALLBACK_PREFIX}d:{di}")])
    return InlineKeyboardMarkup(rows)


def parse_view(vid: str) -> tuple[bool, str | None]:
    """Kısa kod → (geçerli mi, görünüm). 'r' = rastgele (None)."""
    if vid == RANDOM_ID:
        return True, None
    if vid.isdigit() and int(vid) < len(VIEW_KEYS):
        return True, VIEW_KEYS[int(vid)]
    return False, None


def view_label(view: str | None) -> str:
    return VIEW_LABELS[view] if view else VIEW_RANDOM_LABEL


def confirm_keyboard(di: str, eid: str, vid: str | None = None) -> InlineKeyboardMarkup:
    tail = f":{vid}" if vid is not None else ""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Üret", callback_data=f"{CALLBACK_PREFIX}ok:{di}:{eid}{tail}"),
        InlineKeyboardButton("❌ İptal", callback_data=f"{CALLBACK_PREFIX}x"),
    ]])


def approval_keyboard(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Kie'ye gönder", callback_data=f"{CALLBACK_PREFIX}ap:{token}:y"),
        InlineKeyboardButton("❌ İptal", callback_data=f"{CALLBACK_PREFIX}ap:{token}:n"),
    ]])


def publish_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Yayına geç", callback_data=f"{CALLBACK_PREFIX}y:ok"),
        InlineKeyboardButton("❌ Vazgeç", callback_data=f"{CALLBACK_PREFIX}y:no"),
    ]])


def rating_keyboard(page_id: str) -> InlineKeyboardMarkup:
    page = page_id.replace("-", "")
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("👍", callback_data=f"{CALLBACK_PREFIX}r:{page}:g"),
        InlineKeyboardButton("👎", callback_data=f"{CALLBACK_PREFIX}r:{page}:b"),
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


def confirm_text(domain: str, event: str | None, cfg: dict | None = None, view: str | None = None) -> str:
    cfg = cfg or default_cfg()
    return (f"Kategori: {DOMAIN_LABELS[domain]}\n"
            f"Olay: {selection_label(event)}{'' if event else ' (motor seçer)'}\n"
            + (f"Bölge: {view_label(view)}\n" if event in REGION_VIEW_EVENTS else "") +
            f"Mod: {mode_label(cfg['mode'])}\n"
            f"🔍 Ayrıntı: {_onoff(cfg['detail'])} · ✋ Onay: {_onoff(cfg['approval'])}\n"
            f"Tahmini maliyet: {ESTIMATED_COST}\n\n"
            "Üretim sadece ✅ Üret'e basınca başlar."
            + ("\n✋ Onay açık: Kie'ye göndermeden önce son prompt'u gösterip onay isteyeceğim." if cfg["approval"] else ""))


def _allowed_chat(context: ContextTypes.DEFAULT_TYPE) -> int:
    return context.bot_data["allowed_chat_id"]


def _cfg(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.bot_data.setdefault("cfg", default_cfg(MODE_TEST))


class TelegramReporter(pipeline.PipelineReporter):
    """Pipeline (ayrı thread + event loop) → bot loop'u. 🔍 Ayrıntı mesajları ve ✋ Onay beklemesi (TUR 29).
    Onay beklenirken restart olursa future kaybolur, Kie çağrılmaz."""

    def __init__(self, bot, chat_id: int, loop: asyncio.AbstractEventLoop, approvals: dict,
                 detail: bool, approval: bool, labels: dict | None = None, timeout: float = APPROVAL_TIMEOUT):
        self.bot, self.chat_id, self.loop, self.approvals = bot, chat_id, loop, approvals
        self.detail, self.needs_approval, self.labels, self.timeout = detail, approval, labels or {}, timeout

    async def _on_bot_loop(self, coro):
        return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coro, self.loop))

    async def _send_sections(self, sections: list[tuple[str, str]], reply_markup=None) -> None:
        parts = split_message(sections_to_text(sections))
        for i, part in enumerate(parts):
            markup = reply_markup if i == len(parts) - 1 else None
            await self._on_bot_loop(self.bot.send_message(self.chat_id, part, reply_markup=markup))

    async def generation(self, trace: dict, prompt_data: dict | None = None) -> None:
        if self.detail and trace:
            await self._send_sections(format_generation(trace, self.labels))

    async def final_prompt(self, info: dict) -> None:
        # Onay açıksa son prompt onay mesajında gösterilir (çift mesaj olmasın)
        if self.detail and not self.needs_approval:
            await self._send_sections([format_final_prompt(info)])

    async def approve(self, info: dict) -> bool:
        token = secrets.token_hex(4)
        fut: concurrent.futures.Future = concurrent.futures.Future()
        self.approvals[token] = fut
        title, body = format_final_prompt(info)
        await self._send_sections(
            [(title, body + "\n\n✋ Kie'ye gönderilsin mi? Onay gelmeden ücretli çağrı yapılmaz.")],
            approval_keyboard(token))
        try:
            return bool(await asyncio.wait_for(asyncio.wrap_future(fut), self.timeout))
        except asyncio.TimeoutError:
            self.approvals.pop(token, None)
            await self._on_bot_loop(self.bot.send_message(self.chat_id, "⌛ Onay süresi doldu. Kie'ye gönderilmedi, kredi harcanmadı."))
            return False


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update, _allowed_chat(context)):
        return
    await update.effective_message.reply_text(
        "DeepMyster üretim botu. /uret ile kategori ve olay seçip video üret. "
        f"Mod: {mode_label(_cfg(context)['mode'])}. /test · /yayin")


async def cmd_uret(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update, _allowed_chat(context)):
        return
    if _production_lock.locked():
        await update.effective_message.reply_text(BUSY_TEXT)
        return
    cfg = _cfg(context)
    await update.effective_message.reply_text(menu_text(cfg), reply_markup=domain_keyboard(cfg))


async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update, _allowed_chat(context)):
        return
    context.bot_data["cfg"] = default_cfg(MODE_TEST)
    await update.effective_message.reply_text(
        "🧪 TEST modu açık. Hat gerçek üretimle birebir aynı, sadece YouTube'a yüklenmez. "
        "🔍 Ayrıntı ve ✋ Onay açık. /uret ile başla.")


async def cmd_yayin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update, _allowed_chat(context)):
        return
    lock = "\n🔒 Yayın kilidi şu an kapalı: onaylasan da TEST'te kalır." if settings.PUBLISH_LOCKED else ""
    await update.effective_message.reply_text(
        "📢 Yayın moduna geçilsin mi? Bu modda videolar YouTube'a yüklenir; 🔍 Ayrıntı ve ✋ Onay kapanır." + lock,
        reply_markup=publish_keyboard())


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menü adımları: kategori → olay → onay → üretim. Üretimi sadece ✅ Üret başlatır.
    Ayar, yayın onayı, Kie onayı ve puan butonları üretim sürerken de çalışır."""
    query = update.callback_query
    if not is_authorized(update, _allowed_chat(context)):
        return
    await query.answer()
    action, *args = (query.data or "").removeprefix(CALLBACK_PREFIX).split(":")
    cfg = _cfg(context)

    if action == "x" and not args:
        await query.edit_message_text("❌ İptal edildi. /uret ile yeniden başlayabilirsin.")
        return
    if action == "ap" and len(args) == 2 and args[1] in ("y", "n"):
        await _on_approval(query, context, *args)
        return
    if action == "r" and len(args) == 2 and args[1] in RATINGS:
        await _on_rating(query, context, *args)
        return
    if action == "t" and args in (["d"], ["o"]):
        key = "detail" if args[0] == "d" else "approval"
        cfg[key] = not cfg[key]
        await query.edit_message_text(menu_text(cfg), reply_markup=domain_keyboard(cfg))
        return
    if action == "y" and args in (["ok"], ["no"]):
        if args[0] == "no":
            await query.edit_message_text(f"Vazgeçildi. Mod: {mode_label(cfg['mode'])}")
        elif settings.PUBLISH_LOCKED:
            await query.edit_message_text("🔒 Yayın modu kilitli (kullanıcı onayı bekleniyor). Mod: "
                                          f"{mode_label(cfg['mode'])}. YouTube'a hiçbir şey yüklenmez.")
        else:
            context.bot_data["cfg"] = default_cfg(MODE_PUBLISH)
            await query.edit_message_text("📢 YAYIN modu açık: videolar YouTube'a yüklenir. 🔍 Ayrıntı ve ✋ Onay "
                                          "kapalı (/uret menüsünden açılabilir). /test ile geri dön.")
        return
    if _production_lock.locked():
        await query.edit_message_text(BUSY_TEXT)
        return
    if action == "back" and not args:
        await query.edit_message_text(menu_text(cfg), reply_markup=domain_keyboard(cfg))
        return

    sel, view = None, None
    if action == "d" and len(args) == 1:
        sel = parse_selection(args[0])
    elif action in ("e", "ok") and len(args) == 2:
        sel = parse_selection(*args)
    elif action in ("v", "ok") and len(args) == 3:
        # Bölge adımı sadece şehir olaylarında (1 Eki)
        sel = parse_selection(*args[:2])
        valid, view = parse_view(args[2])
        if not valid or sel is None or sel[1] not in REGION_VIEW_EVENTS:
            sel = None
    if sel is None:
        await query.edit_message_text("Geçersiz seçim. /uret ile tekrar dene.")
        return
    domain, event = sel

    if action == "d":
        await query.edit_message_text(f"{DOMAIN_LABELS[domain]}: hangi olay?", reply_markup=event_keyboard(int(args[0])))
    elif action == "e" and event in REGION_VIEW_EVENTS:
        await query.edit_message_text(f"{DOMAIN_LABELS[domain]} / {EVENT_LABELS[event]}\nBölge: hangi görünüm?",
                                      reply_markup=view_keyboard(*args))
    elif action == "e":
        await query.edit_message_text(confirm_text(domain, event, cfg), reply_markup=confirm_keyboard(*args))
    elif action == "v":
        await query.edit_message_text(confirm_text(domain, event, cfg, view), reply_markup=confirm_keyboard(*args))
    else:
        run_cfg = dict(cfg)   # üretim başlarken mod sabitlenir; sonradan değişiklik bu üretimi etkilemez
        async with _production_lock:
            await query.edit_message_text(
                f"🚀 Üretim başladı: {DOMAIN_LABELS[domain]} / {selection_label(event)}"
                + (f" / {view_label(view)}" if event in REGION_VIEW_EVENTS else "") + "\n"
                f"Mod: {mode_label(run_cfg['mode'])}\n"
                + ("Senaryo → video. YouTube'a yüklenmez." if run_cfg["mode"] == MODE_TEST
                   else "Senaryo → video → YouTube.") + " Birkaç dakika sürer."
            )
            await produce(context.bot, _allowed_chat(context), domain, event, cfg=run_cfg, bot_data=context.bot_data,
                          view=view)


async def _on_approval(query, context, token: str, answer: str) -> None:
    fut = context.bot_data.setdefault("approvals", {}).pop(token, None)
    await query.edit_message_reply_markup(reply_markup=None)
    if fut is None or fut.done():
        await context.bot.send_message(_allowed_chat(context), "Bu onay artık geçerli değil (süresi doldu veya bot yeniden başladı).")
        return
    approved = answer == "y"
    fut.set_result(approved)
    await context.bot.send_message(_allowed_chat(context), "✅ Onaylandı, Kie'ye gönderiliyor." if approved
                                   else "❌ İptal edildi. Kie'ye gönderilmeyecek, kredi harcanmayacak.")


async def _on_rating(query, context, page: str, code: str) -> None:
    value, icon = RATINGS[code]
    await asyncio.to_thread(NotionTracker(page_id=page).set_rating, value)
    archive_dir = context.bot_data.setdefault("archives", {}).get(page)
    if archive_dir:
        try:
            update_meta(archive_dir, rating=value)
        except OSError as e:
            log.warning(f"⚠️ Puan meta.json'a yazılamadı: {e}")
    await query.edit_message_reply_markup(reply_markup=None)
    await context.bot.send_message(_allowed_chat(context), f"{icon} Puan kaydedildi: {value}")


def _run_pipeline_blocking(kwargs: dict) -> dict:
    # Pipeline kendi event loop'unda, ayrı thread'de: bot üretim sırasında cevap vermeye devam eder
    return asyncio.run(pipeline.run_pipeline(**kwargs))


async def produce(bot, chat_id: int, domain: str, event: str | None = None, cfg: dict | None = None,
                  bot_data: dict | None = None, view: str | None = None) -> None:
    """Pipeline'ı çalıştırır, sonucu ve videoyu sohbete gönderir. Hiçbir hata dışarı sızmaz.
    TEST modunda skip_upload: YouTube adımı hiç çağrılmaz; hattın geri kalanı yayınla birebir aynı."""
    cfg = cfg or default_cfg(MODE_TEST)
    bot_data = bot_data if bot_data is not None else {}
    reporter = TelegramReporter(bot, chat_id, asyncio.get_running_loop(), bot_data.setdefault("approvals", {}),
                                cfg["detail"], cfg["approval"],
                                {"domain": DOMAIN_LABELS.get(domain, domain), "event": selection_label(event)})
    kwargs = {"domain": domain, "event": event, "trigger": "manual", "mode": cfg["mode"],
              "skip_upload": cfg["mode"] == MODE_TEST, "reporter": reporter, "view": view}
    try:
        result = await asyncio.to_thread(_run_pipeline_blocking, kwargs)
    except Exception as e:
        log.error(f"❌ Telegram üretimi çöktü: {e}", exc_info=True)
        status.fail(f"Telegram üretimi çöktü: {e}")
        await bot.send_message(chat_id, f"❌ Hata: {type(e).__name__}: {str(e)[:500]}")
        return

    if not result or not result.get("success"):
        result = result or {}
        reason = result.get("reason")
        error = result.get("error") or reason or "Bilinmeyen hata"
        if status.data.get("state") == "running":
            status.fail(error)
        if reason == "cancelled":
            await bot.send_message(chat_id, "❌ İptal edildi. Kie'ye gönderilmedi, kredi harcanmadı.")
            return
        if reason == "kie_timeout":
            await bot.send_message(chat_id, f"⏳ Kie zaman aşımı. Task {result.get('task_id')} Kie'de sürüyor olabilir; "
                                            "takip ediliyor, bitince video gelir.")
            asyncio.get_running_loop().create_task(follow_task(bot, chat_id, result.get("notion_page_id", ""), bot_data))
            return
        # Kalite kapısı retlerinde deneme başına tek satır özet (TUR 25): ham JSON 500 karakterde kesiliyordu
        summary = result.get("error_summary") or str(error)[:500]
        for part in split_message(f"❌ Üretim başarısız: {summary}"):
            await bot.send_message(chat_id, part)
        return

    title = result.get("title", "")
    youtube_url = result.get("youtube_url", "")
    is_test = result.get("mode") == MODE_TEST
    # 10 Eki, Bahadır: yapılandırılmış hatta danışman preflight riskli dediyse sonuç mesajında da (YAYIN dahil)
    warning = f"\n{result['preflight_warning']}" if result.get("preflight_warning") else ""
    if youtube_url:
        await bot.send_message(chat_id, f"✅ Yüklendi: {title}\n{youtube_url}{warning}")
    elif is_test:
        await bot.send_message(chat_id, f"🧪 TEST üretimi tamamlandı (YouTube'a yüklenmedi): {title}{warning}")
    else:
        await bot.send_message(chat_id, f"⚠️ Video üretildi ama YouTube'a yüklenmedi: {title}{warning}")
    await deliver_video(bot, chat_id, result.get("video_path", ""), title, result.get("mode", ""),
                        result.get("notion_page_id", ""), result.get("archive_dir", ""), bot_data)


async def deliver_video(bot, chat_id: int, path: str, title: str, mode: str, page_id: str, archive_dir: str,
                        bot_data: dict, prefix: str = "") -> None:
    """Videoyu 👍/👎 ile gönderir; Telegram file_id'yi Notion'a ve meta.json'a yazar (kalıcı kopya)."""
    caption = ("🧪 TEST | " if mode == MODE_TEST else "") + prefix + title
    msg = await send_video_file(bot, chat_id, path, caption, reply_markup=rating_keyboard(page_id) if page_id else None)
    if page_id and archive_dir:
        bot_data.setdefault("archives", {})[page_id.replace("-", "")] = archive_dir
    file_id = getattr(getattr(msg, "video", None), "file_id", None) if msg else None
    if not isinstance(file_id, str):
        return
    if page_id:
        await asyncio.to_thread(NotionTracker(page_id=page_id).set_telegram_file_id, file_id)
    if archive_dir:
        try:
            update_meta(archive_dir, telegram_file_id=file_id)
        except OSError as e:
            log.warning(f"⚠️ file_id meta.json'a yazılamadı: {e}")


async def send_video_file(bot, chat_id: int, path: str, caption: str, reply_markup=None):
    if not path or not os.path.exists(path):
        await bot.send_message(chat_id, "⚠️ Video dosyası bulunamadı, Telegram'a gönderilemedi.")
        return None
    if os.path.getsize(path) > TELEGRAM_VIDEO_LIMIT:
        await bot.send_message(chat_id, "⚠️ Video 50 MB'tan büyük, Telegram'a gönderilemedi.")
        return None
    try:
        with open(path, "rb") as f:
            return await bot.send_video(chat_id, video=f, caption=caption[:1024], supports_streaming=True,
                                        read_timeout=180, write_timeout=180, reply_markup=reply_markup)
    except Exception as e:
        log.error(f"❌ Video Telegram'a gönderilemedi: {e}", exc_info=True)
        await bot.send_message(chat_id, f"⚠️ Video Telegram'a gönderilemedi: {str(e)[:300]}")
        return None


async def _recovered_video(bot, chat_id: int, bot_data: dict, item: dict) -> None:
    await deliver_video(bot, chat_id, item["video_path"], item.get("title", ""), item.get("mode", ""),
                        item.get("page_id", ""), item.get("archive_dir", ""), bot_data, prefix="♻️ Kurtarıldı: ")


async def follow_task(bot, chat_id: int, page_id: str, bot_data: dict) -> None:
    """Zaman aşımına düşen task'ı arka planda bekler (yeni ücretli çağrı yok)."""
    if not page_id:
        return
    results = await pipeline.recover_pending_tasks(
        on_video=lambda item: _recovered_video(bot, chat_id, bot_data, item), only_page_id=page_id)
    if any(r["action"] == "still_running" for r in results):
        await bot.send_message(chat_id, "⏳ Task hâlâ bitmedi; bir sonraki bot açılışında tekrar denenecek.")
    for r in results:
        if r["action"] == "failed":
            await bot.send_message(chat_id, f"❌ Kie task başarısız: {r.get('error', '')[:300]}")


async def post_init(app: Application) -> None:
    """Açılış: BotFather komut listesi, Notion şeması, restart'tan kalan üretimlerin kurtarılması."""
    try:
        await app.bot.set_my_commands(BOT_COMMANDS)
    except Exception as e:
        log.warning(f"⚠️ Bot komut listesi ayarlanamadı: {e}")
    await asyncio.to_thread(NotionTracker.ensure_schema)
    chat_id = app.bot_data["allowed_chat_id"]

    async def recover() -> None:
        results = await pipeline.recover_pending_tasks(
            on_video=lambda item: _recovered_video(app.bot, chat_id, app.bot_data, item))
        log.info(f"♻️ Açılış kurtarması: {[(r['action'], r['page_id'][:8]) for r in results]}")

    app.create_task(recover())


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error(f"Telegram handler hatası: {context.error}", exc_info=context.error)


def build_application(token: str, allowed_chat_id: int) -> Application:
    # concurrent_updates: üretim sürerken yeni /uret, onay ve puan butonları cevap alabilsin
    app = Application.builder().token(token).concurrent_updates(True).post_init(post_init).build()
    app.bot_data["allowed_chat_id"] = allowed_chat_id
    app.bot_data["cfg"] = default_cfg(MODE_TEST)   # her açılışta TEST (yayın modu hafızada tutulmaz)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("uret", cmd_uret))
    app.add_handler(CommandHandler("test", cmd_test))
    app.add_handler(CommandHandler("yayin", cmd_yayin))
    app.add_handler(CallbackQueryHandler(on_callback, pattern=f"^{CALLBACK_PREFIX}"))
    app.add_error_handler(on_error)
    return app


def run() -> None:
    token, chat_id = load_telegram_config()
    status.enable(os.environ.get("STATUS_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "status.json"))
    log.info(f"🤖 DeepMyster Telegram botu başlıyor (izinli sohbet: {chat_id}, mod: TEST)")
    build_application(token, chat_id).run_polling(
        allowed_updates=[Update.MESSAGE, Update.CALLBACK_QUERY],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    run()
