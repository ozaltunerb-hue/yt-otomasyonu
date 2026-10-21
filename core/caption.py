"""
Caption sistemi (21 Eki 2026, Aşama 7): başlık + açıklama + CTA + hashtag.

- Ek GPT çağrısı yok: hikâye dilimlerini yazan strict şemalı çağrıya CAPTION_FIELDS eklenir (3 başlık adayı + stilleri,
  2 açıklama adayı, CTA + tipi). Hashtag'leri kod seçer. Caption Kie prompt'una girmez (175 bütçesi dışında).
- Kod seçer ve denetler: başlık stili (T1-T6) ve CTA tipi hesap genelinde son 2 hariç; benzerlik (Paylaşımlar'daki tüm
  satırlar + son 20 üretilmiş caption): başlık içerik kelimesi Jaccard > 0.5 ya da ilk 3 kelime aynı -> ret, açıklama
  Jaccard > 0.45 -> ret; kalıcı yasak ifadeler; dinamik yasak (son 10 paylaşılan başlıkta 2+ kez geçen içerik kelimesi).
- Hiçbir aday geçmezse şablon yedeği (her stil için olay kategorisine göre 2 şablon), aynı kontrollerle. Telegram'da
  "kaynak: GPT / şablon".
- Hashtag: kategori havuzundan 2 geniş + 3 özel; aynı kategorideki önceki postla en fazla 2 ortak; son 10 postta aynı
  set yok; yasak etiketler (viral, reels, cinematic, fyp, AI...); denizcilik etiketleri sadece kıyı dalga ve su hortumu.
"""
from __future__ import annotations

import functools
import itertools
import random
import re
from datetime import datetime, timedelta, timezone

# ── GPT şeması ───────────────────────────────────────────────────────────────────────────────────────────────────
STYLES = {"T1": "short punchy statement", "T2": "\"the moment\" narration", "T3": "number or time (\"15 seconds...\", "
          "\"Six floors...\")", "T4": "question headline", "T5": "witness view (\"Filmed from the balcony as...\")",
          "T6": "threat + target (\"Volcanic Bombs Tear Through a Mountain Village\")"}
CTA_TYPES = {"question": "Soru", "watch": "Sonuna kadar izle", "emoji": "Emoji seçimi", "stat": "İstatistik",
             "none": "CTA yok"}
CTA_FROM_TR = {v: k for k, v in CTA_TYPES.items()}
CAPTION_FIELDS = ("title_1", "title_1_style", "title_2", "title_2_style", "title_3", "title_3_style",
                  "description_1", "description_2", "cta", "cta_type")


def schema_properties() -> dict:
    """Hikâye çağrısının strict şemasına eklenen alanlar."""
    props = {}
    for i in (1, 2, 3):
        props[f"title_{i}"] = {"type": "string"}
        props[f"title_{i}_style"] = {"type": "string", "enum": list(STYLES)}
    props["description_1"] = {"type": "string"}
    props["description_2"] = {"type": "string"}
    props["cta"] = {"type": "string"}
    props["cta_type"] = {"type": "string", "enum": list(CTA_TYPES)}
    return props


BANNED_PHRASES = ("massive", "in seconds", "would you run or stay", "the moment everything", "swallows the entire",
                  "out of nowhere",
                  # 21 Eki (Aşama 7.1): genel / tık tuzağı kalıplar
                  "nobody expected", "this part", "this moment", "with every second", "the last frame")
AI_WORDS = ("ai", "a.i.", "artificial", "generated", "aigenerated", "aiart", "aivideo", "midjourney", "sora", "kie",
            "seedance")
PLACE_WORDS = ("turkey", "türkiye", "greece", "italy", "spain", "france", "japan", "china", "india", "usa", "america",
               "american", "mexico", "brazil", "morocco", "portugal", "california", "florida", "texas", "bali",
               "thailand", "vietnam", "indonesia", "philippines", "switzerland", "austria", "peru", "chile", "hawaii",
               "iceland", "norway", "istanbul", "izmir", "antalya", "naples", "tokyo", "sicily", "alps", "europe",
               "asia", "africa")


def instruction_block(ctx: dict | None) -> str:
    """GPT'ye giden caption talimatı (İngilizce, kısa) + "tekrarlama" bağlamı (son 10 başlık, stil ve CTA tipleri)."""
    ctx = ctx or {}
    recent = ctx.get("recent_titles") or []
    styles = ctx.get("recent_styles") or []
    ctas = ctx.get("recent_cta_types") or []
    lines = [
        "CAPTION (separate fields, not part of the story):",
        "- title_1/2/3: max 9 words, 0-2 emojis, describe THIS video's opening and threat. Each title uses a different "
        "style; give its code in title_N_style: " + "; ".join(f"{k} {v}" for k, v in STYLES.items()) + ".",
        "- description_1/2: 1-2 sentences, max 35 words, what happens and how it escalates; never copy the opening "
        "sentence word for word.",
        "- cta: one line matching cta_type: question / watch (watch till the end) / emoji (emoji choice, e.g. "
        "\"Comment 🏃 or 🏠\") / stat (a concrete number from the video, no fake statistics) / none (empty cta).",
        "- English only. No country or real place names. No mention of AI. Never use: "
        + ", ".join(f'"{p}"' for p in BANNED_PHRASES) + ".",
    ]
    if recent:
        lines.append("RECENT POSTED TITLES (do not repeat their wording): " + " | ".join(recent[-10:]))
    if styles or ctas:
        lines.append(f"RECENT TITLE STYLES (avoid): {', '.join(styles[-2:]) or '-'}; RECENT CTA TYPES (avoid): "
                     f"{', '.join(ctas[-2:]) or '-'}")
    return "\n".join(lines) + "\n"


def extract_candidates(raw) -> dict | None:
    """GPT yanıtındaki caption alanları (yoksa None)."""
    if not isinstance(raw, dict) or not all(k in raw for k in CAPTION_FIELDS):
        return None
    titles = [(str(raw[f"title_{i}"] or "").strip(), raw[f"title_{i}_style"]) for i in (1, 2, 3)]
    return {"titles": [t for t in titles if t[0]],
            "descriptions": [d for d in (str(raw["description_1"] or "").strip(), str(raw["description_2"] or "").strip())
                             if d],
            "cta": str(raw["cta"] or "").strip(), "cta_type": raw["cta_type"]}


# ── Olay verisi: Paylaşımlar kategorisi, hashtag havuzu, şablon değişkenleri ─────────────────────────────────────────
FLOOD, TIDAL = "Flash flooding in city streets", "Tidal wave surges over a coastal city street"
MUDSLIDE, SLOPE = "Mudslide pours down a hillside street", "Rain-soaked slope collapses onto a roadside"
VILLAGE = "Mud and debris torrent tears through a hillside village"
LANDFALL, MARINA, AVENUE = "Tornado making landfall", "Tornado crosses a marina quay", "Tornado sweeps down a coastal avenue"
WILDFIRE, FACADE = "Wall of flames sweeps into a hillside neighborhood", "Flames race up a tower facade"
FIRE_TORNADO = "Fire tornado tears across a burning roadside"
HELICOPTER = "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood"
PYRO, BOMBS = "Pyroclastic cloud races down into a village street", "Volcanic bombs slam into a village street"
AVA_V, AVA_S, AVA_F = ("Avalanche slams into a mountain village", "Avalanche crashes down onto a ski lodge",
                       "Avalanche rips through a pine forest into a valley")
EQ_A, EQ_O = "Earthquake collapses an apartment block", "Earthquake collapses a row of old stone houses"

# Paylaşımlar "Kategori" select (21 Eki eşlemesi)
SHARE_CATEGORY = {FLOOD: "Sel", TIDAL: "Dev dalga", MUDSLIDE: "Heyelan", SLOPE: "Heyelan", VILLAGE: "Heyelan",
                  AVENUE: "Hortum", MARINA: "Su hortumu", LANDFALL: "Su hortumu", WILDFIRE: "Yangın", FACADE: "Yangın",
                  FIRE_TORNADO: "Yangın", HELICOPTER: "Yangın", PYRO: "Volkan", BOMBS: "Volkan", AVA_V: "Çığ",
                  AVA_S: "Çığ", AVA_F: "Çığ", EQ_A: "Deprem", EQ_O: "Deprem"}
_POOL = {
    "sel": (("#extremeweather", "#naturepower", "#disaster", "#severeweather"),
            ("#flashflood", "#flood", "#floodwater", "#flooding", "#rainstorm", "#stormdamage", "#weatherwatch")),
    "dalga": (("#extremeweather", "#naturepower", "#disaster", "#oceanpower"),
              ("#tidalwave", "#giantwave", "#bigwave", "#roguewave", "#coastalflood", "#seastorm", "#waves")),
    "heyelan": (("#naturaldisaster", "#extremeweather", "#naturepower", "#disaster"),
                ("#landslide", "#mudslide", "#debrisflow", "#rockfall", "#heavyrain", "#monsoon", "#mountainroad")),
    "hortum": (("#extremeweather", "#severeweather", "#naturepower", "#disaster"),
               ("#tornado", "#twister", "#supercell", "#stormchasing", "#tornadowarning", "#waterspout", "#storm")),
    "yangın": (("#naturaldisaster", "#extremeweather", "#disaster", "#firesafety"),
               ("#wildfire", "#firetornado", "#forestfire", "#bushfire", "#firestorm", "#firefighters",
                "#aerialfirefighting", "#smoke", "#buildingfire", "#apartmentfire")),   # 21 Eki (7.1): +2 cephe
    "volkan": (("#naturepower", "#naturaldisaster", "#disaster", "#earthscience"),
               ("#volcano", "#eruption", "#volcaniceruption", "#ashcloud", "#lavabombs", "#pyroclasticflow", "#volcanic")),
    "çığ": (("#naturepower", "#naturaldisaster", "#extremeweather", "#disaster"),
            ("#avalanche", "#snowstorm", "#winterstorm", "#mountains", "#backcountry", "#powdersnow", "#skiresort")),
    "deprem": (("#disaster", "#extremeevents", "#catastrophe", "#survival"),   # 21 Eki: +2 geniş (en fazla 2 ortak)
               ("#buildingcollapse", "#collapse", "#structuralfailure", "#urbandisaster", "#dustcloud")),
}
TAG_POOL = {FLOOD: "sel", TIDAL: "dalga", MUDSLIDE: "heyelan", SLOPE: "heyelan", VILLAGE: "heyelan", LANDFALL: "hortum",
            MARINA: "hortum", AVENUE: "hortum", WILDFIRE: "yangın", FACADE: "yangın", FIRE_TORNADO: "yangın",
            HELICOPTER: "yangın", PYRO: "volkan", BOMBS: "volkan", AVA_V: "çığ", AVA_S: "çığ", AVA_F: "çığ",
            EQ_A: "deprem", EQ_O: "deprem"}
# Olaya özgü etiketler sadece kendi olayında (ör. #firetornado sadece ateş hortumu)
TAG_ONLY = {"#firetornado": {FIRE_TORNADO}, "#aerialfirefighting": {HELICOPTER}, "#waterspout": {MARINA, LANDFALL},
            "#skiresort": {AVA_S}, "#mountainroad": {SLOPE}, "#pyroclasticflow": {PYRO}, "#lavabombs": {BOMBS},
            "#wildfire": {WILDFIRE, FIRE_TORNADO, HELICOPTER}, "#forestfire": {WILDFIRE, FIRE_TORNADO, HELICOPTER},
            "#bushfire": {WILDFIRE, FIRE_TORNADO, HELICOPTER}, "#rockfall": {SLOPE},
            "#buildingfire": {FACADE}, "#apartmentfire": {FACADE}}
MARITIME_TAGS = ("#maritime", "#ocean", "#shiplife", "#roughseas", "#cctv")
MARITIME_EVENTS = {TIDAL, MARINA, LANDFALL}
BANNED_TAGS = ("#viral", "#reels", "#cinematic", "#fyp", "#aivideo", "#foryou", "#foryoupage", "#explore",
               "#earthquake")


@functools.lru_cache(maxsize=4096)
def is_banned_tag(tag: str) -> bool:
    t = tag.lower()
    return t in BANNED_TAGS or bool(re.search(r"(^#ai|ai$|aiart|aigenerated|artificial)", t))


def event_tags(event: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(geniş, özel) olay için izinli etiketler."""
    broad, special = _POOL[TAG_POOL[event]]
    special = tuple(t for t in special if event in TAG_ONLY.get(t, {event}))
    return broad, special


# Şablon değişkenleri (21 Eki, Aşama 7.1): tehdit, hedef, emoji, nesneler (sahnede kesin olan; ör. marina: 4 Eki'den
# beri yat yok, kafe var), yer öbeği. Açıklama şablonları üretimin beat cümlelerini kullanır (info["beat_2"/"beat_3"]).
VARS = {
    FLOOD: ("Flash Flood", "a City Street", "🌊", "Parked Cars", "on a City Street"),
    TIDAL: ("Tidal Wave", "the Seafront", "🌊", "Parked Cars", "on the Seafront"),
    MUDSLIDE: ("Mudslide", "a Steep Hillside Street", "⛰️", "Hillside Houses", "on a Hillside Street"),
    SLOPE: ("Slope Collapse", "a Mountain Road", "⛰️", "Parked Cars", "on a Mountain Road"),
    VILLAGE: ("Debris Torrent", "a Hillside Village", "🌧️", "Village Houses", "in a Hillside Village"),
    LANDFALL: ("Waterspout", "the Waterfront", "🌪️", "Waterfront Houses", "on the Waterfront"),
    MARINA: ("Waterspout", "a Marina", "🌪️", "Quayside Cafés", "at a Marina"),
    AVENUE: ("Tornado", "a Coastal Avenue", "🌪️", "Palm Trees", "on a Coastal Avenue"),
    WILDFIRE: ("Wall of Flames", "a Hillside Neighborhood", "🔥", "Hillside Homes", "in a Hillside Neighborhood"),
    FACADE: ("Facade Fire", "an Apartment Tower", "🔥", "Upper Floors", "on an Apartment Tower"),
    FIRE_TORNADO: ("Fire Tornado", "a Burning Roadside", "🔥", "Roadside Houses", "on a Burning Roadside"),
    HELICOPTER: ("Water Drop", "a Burning Hillside", "🚁", "Hillside Homes", "over a Burning Hillside"),
    PYRO: ("Ash Cloud", "a Village Street", "🌋", "Village Houses", "on a Village Street"),
    BOMBS: ("Volcanic Bombs", "a Village Street", "🌋", "Village Roofs", "on a Village Street"),
    AVA_V: ("Avalanche", "a Mountain Village", "🏔️", "Stone Chalets", "in a Mountain Village"),
    AVA_S: ("Avalanche", "a Ski Lodge", "⛷️", "Lodge Buildings", "at a Ski Lodge"),
    AVA_F: ("Avalanche", "a Forest Valley", "🌲", "Wooden Cabins", "in a Forest Valley"),
    EQ_A: ("Building Collapse", "an Apartment Block", "🏢", "Upper Floors", "on a City Block"),
    EQ_O: ("Building Collapse", "a Row of Old Houses", "🧱", "Old Stone Houses", "on an Old Street"),
}
PLURAL_THREATS = {BOMBS}   # fiil uyumu: "Volcanic Bombs Tear", "Flash Flood Tears"
WITNESS = {"balkon": "the Balcony", "çatı": "the Rooftop", "pencere": "an Upper Window", "tepe": "the Hillside",
           "direk": "a Street Camera", "teras": "the Terrace", None: "Across the Street"}
_NUMW = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}
# 21 Eki (Aşama 7.1): genel / tık tuzağı kalıp yok ("Nobody expected", "this part", "with every second", "The last
# frame:"); T4 gerçek soru; her başlık olayın tehdidini, hedefini ya da sahnedeki nesneleri anar.
TITLE_TEMPLATES = {
    "T1": ("{threat} Hit{s} {target} {emoji}", "{target} Had No Warning {emoji}",
           "The {objects} Never Stood a Chance {emoji}", "{threat} Versus the {objects}"),
    "T2": ("The Second the {threat} Reached {target}", "When the {threat} Reached the {objects} {emoji}",
           "The Instant {target} Was Hit {emoji}", "The Moment the {objects} Gave Way {emoji}"),
    "T3": ("15 Seconds of {threat} {loc}", "{people} People Run From the {threat} {emoji}",
           "Fifteen Seconds Near the {objects} {emoji}", "One Take, One {threat_one} {emoji}"),
    "T4": ("Could These {objects} Survive the {threat}? {emoji}", "Could You Outrun the {threat}? {emoji}",
           "How Long Would the {objects} Last? {emoji}", "Could {target} Hold Back the {threat}?"),
    "T5": ("Filmed From {witness} as the {threat} Hit {emoji}", "Seen From {witness} as the {objects} Were Hit",
           "Caught From {witness} {loc}", "Watching the {objects} From {witness}"),
    "T6": ("{threat} Tear{s} Through {target} {emoji}", "{threat} Slam{s} Into the {objects} {emoji}",
           "{threat} Pound{s} {target} {emoji}", "{threat} Rip{s} Through the {objects}"),
}
# Açıklama: tehdit + hedef + üretimin beat cümlesi (somut). Beat bilgisi yoksa (eski durum) beat'siz iki şablon.
# h2/h3: beat cümlesinin ilk cümleciği (ortak kuyruklar benzerliği şişirmesin); i2/i3: tehdit adı başta geçiyorsa
# öznesi "it" (çerçeve tehdidi zaten adlandırıyor). İki beat'li şablonlar önce: üretimde beat ÇİFTİ tekrar etmez.
DESC_TWO_BEATS = 5   # ilk 5 şablon iki beat'li (önce denenir)
DESC_TEMPLATES = ("{Threat} {loc_l}: {i2}, then {i3}.",
                  "{H2}{as2}. Seconds later {h3}.",
                  "From {witness_l}: {h2}{as2}, then {h3}.",
                  "First the {threat_l}: {i2}. Moments later {h3}.",
                  "Camera rolling {loc_l}. {H2}{as2}, and soon {h3}.",
                  "The {threat_l} reach{es} {target_l}: {i3}.",
                  "{Threat} {loc_l}, one take: {i2}.",
                  "One take from {witness_l} as the {threat_l} hit{s}: {i3}.",
                  "Halfway through the {threat_l}, {h3}.")
DESC_TEMPLATES_NO_BEAT = ("The {threat_l} reach{es} {target_l} and the {objects_l} take the first hit.",
                          "Filmed from {witness_l} as the {threat_l} hit the {objects_l} {loc_l}.")
CTA_TEMPLATES = {
    "question": ("Would you have stayed near the {objects_l}?", "Where would you run {loc_l}?"),
    "watch": ("Keep your eyes on the {objects_l} until the end.", "Watch {target_l} until the very end."),
    "emoji": ("Comment {emoji} if you would stay or 🏃 if you would run.", "Comment 🏠 or 🚗: what would you save first?"),
    "stat": ("{people} people, 15 seconds, one take.", "15 seconds, one take, no cuts."),
    "none": ("",),
}

# ── Metin araçları ───────────────────────────────────────────────────────────────────────────────────────────────
_STOP = {"a", "an", "the", "of", "to", "in", "on", "as", "and", "it", "its", "this", "that", "into", "from", "with",
         "at", "for", "by", "is", "are", "was", "be", "you", "your", "what", "when", "how", "one", "all", "just", "up",
         "out", "over", "every", "there", "they", "their", "after", "before", "while", "through", "onto", "down",
         "off", "across", "toward", "towards", "near", "behind", "under", "than", "then", "so", "but", "or", "if",
         "we", "our", "us", "he", "she", "his", "her", "them", "who", "why", "where", "can", "could", "would", "will",
         "do", "does", "did", "has", "have", "had", "not", "no", "very", "too", "here", "these", "those", "s"}
# 21 Eki (Aşama 7 devam): olay / kategori adları ve eş anlamlıları benzerlikte sayılmaz (her caption olayını anar; bu
# kelimeler Jaccard'ı, ilk 3 kelimeyi ve dinamik yasağı haksız yere tetikliyordu). Kökler: çoğul/-ing hali de eşleşir.
EVENT_WORDS = {"tornado", "tornadoe", "twister", "funnel", "waterspout", "wave", "tidal", "flood", "floodwater",
               "flooding", "mud", "mudslide", "landslide", "slope", "hillside", "fire", "flame", "wildfire",
               "helicopter", "volcano", "volcanic", "ash", "bomb", "avalanche", "snow", "building", "block",
               "collapse", "street", "town", "village", "city", "road",
               # 21 Eki (7.1): olay adlarının eş anlamlıları (su bırakma = helikopter, kızgın kaya = volkan bombası)
               "water", "drop", "load", "rock", "glowing", "facade"}
_EMOJI = re.compile("[\U0001F000-\U0001FFFF☀-➿️‍]")


def words(text: str) -> tuple[str, ...]:
    return _words(text or "")


@functools.lru_cache(maxsize=16384)
def _words(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9']+", _EMOJI.sub(" ", text.lower())))


def _norm(w: str) -> str:
    w = w.strip("'")
    if w.endswith("'s"):
        w = w[:-2]
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def clean_words(text: str, stop: frozenset = frozenset()) -> list[str]:
    return list(_clean_words(text or "", frozenset(stop)))


@functools.lru_cache(maxsize=16384)   # 21 Eki (7.1): aynı geçmiş metinleri her adayda yeniden temizlenmesin
def _clean_words(text: str, stop: frozenset) -> tuple[str, ...]:
    """Benzerlik kelimeleri (sıralı): stopword, olay/kategori adı ve eş anlamlısı, sayı ve emoji çıkarılmış.
    stop: ek olarak sayılmayan kelimeler (aday olayının kendi adındaki kelimeler, event_stop)."""
    out = []
    for w in words(text):
        n = _norm(w)
        if not n or n in _STOP or w in _STOP or n in EVENT_WORDS or w in EVENT_WORDS or re.fullmatch(r"\d+", n) \
                or n in stop:
            continue
        out.append(n)
    return tuple(out)


def event_stop(event: str | None) -> frozenset:
    """21 Eki (7.1): olayın kendi adındaki kelimeler (ör. "row of old stone houses" -> row, old, stone, house) o olayın
    adaylarında benzerliğe sayılmaz: her caption olayını anar."""
    return frozenset(_norm(w) for w in words(event or "") if w not in _STOP) - {""}


def content_words(text: str, stop: frozenset = frozenset()) -> frozenset[str]:
    return _content_words(text or "", frozenset(stop))


@functools.lru_cache(maxsize=16384)
def _content_words(text: str, stop: frozenset) -> frozenset[str]:
    return frozenset(_clean_words(text, stop))


def jaccard(a: str, b: str, stop: frozenset = frozenset()) -> float:
    x, y = content_words(a, stop), content_words(b, stop)
    if stop and (len(x) < 2 or len(y) < 2):   # olay adı çıkınca kelime kalmıyorsa olay adı sayılır (boş = benzer değil
        x, y = content_words(a), content_words(b)   # olmasın: "Debris Torrent Tears Through a Hillside Village")
    return len(x & y) / len(x | y) if x | y else 0.0


def first3(text: str, stop: frozenset = frozenset()) -> tuple[str, ...]:
    """İlk 3 kelime kuralı temizlenmiş kelimelerle ("The…", "A…" ile başlayan başlıklar haksız ret almasın)."""
    out = clean_words(text, stop)
    return tuple((out if len(out) >= 3 or not stop else clean_words(text))[:3])


def same_text(a: str, b: str) -> bool:
    """Birebir tekrar (büyük/küçük harf, emoji ve noktalama hariç)."""
    return bool(words(a)) and words(a) == words(b)


def emoji_count(text: str) -> int:
    return len([c for c in _EMOJI.findall(text or "") if c not in ("️", "‍")])


def banned_phrases(text: str) -> list[str]:
    low = (text or "").lower()
    out = [p for p in BANNED_PHRASES if p in low]
    ws = set(words(text))
    out += [w for w in AI_WORDS if w in ws]
    out += [w for w in PLACE_WORDS if w in ws]
    return out


def infer_style(title: str) -> str:
    """Paylaşımlar'daki eski başlıkların stili (kayıtta stil yok): sezgisel."""
    low = (title or "").lower().strip()
    if "?" in low:
        return "T4"
    if re.match(r"^(\d|one|two|three|four|five|six|seven|eight|nine|ten|fifteen|twenty)\b", low) or "seconds" in low:
        return "T3"
    if re.match(r"^(filmed|seen from|caught on|from the|watch|shot from)\b", low):
        return "T5"
    if "moment" in low or low.startswith("when "):
        return "T2"
    if len(words(low)) >= 5 and re.search(r"\b(tears?|slams?|hits?|rips?|sweeps?|crash(es)?|engulfs?|bur(y|ies)|"
                                         r"punch(es)?|smash(es)?|races?|roars?)\b", low):
        return "T6"
    return "T1"


# ── Bağlam (geçmiş) ──────────────────────────────────────────────────────────────────────────────────────────────
def build_context(posted: list[dict] | None, generated: list[dict] | None) -> dict:
    """posted: Paylaşımlar satırları ({"Başlık","Açıklama","CTA Tipi","Hashtagler","Kategori","Paylaşım Tarihi"});
    generated: üretilmiş caption'lar, eskiden yeniye ({"title","description","style","cta_type","hashtags","category",
    "date"}). Dönüş: kontrollerin ve GPT bağlamının kullandığı alanlar."""
    posted = sorted(posted or [], key=lambda r: (r.get("Paylaşım Tarihi") or "", r.get("Başlık") or ""))
    generated = list(generated or [])[-20:]
    timeline = []
    for r in posted:
        timeline.append({"date": r.get("Paylaşım Tarihi") or "", "title": r.get("Başlık") or "",
                         "style": infer_style(r.get("Başlık") or ""), "cta_type": CTA_FROM_TR.get(r.get("CTA Tipi")),
                         "hashtags": set(re.findall(r"#\w+", (r.get("Hashtagler") or "").lower())),
                         "category": r.get("Kategori")})
    for g in generated:
        timeline.append({"date": g.get("date") or "9999", "title": g.get("title") or "", "style": g.get("style"),
                         "cta_type": g.get("cta_type"), "hashtags": set(t.lower() for t in g.get("hashtags") or []),
                         "category": g.get("category")})
    timeline.sort(key=lambda x: x["date"])
    recent_posted = [r.get("Başlık") or "" for r in posted][-10:]
    return {
        "titles": [r.get("Başlık") or "" for r in posted] + [g.get("title") or "" for g in generated],
        "descriptions": [r.get("Açıklama") or "" for r in posted if r.get("Açıklama")]
                        + [g.get("description") or "" for g in generated if g.get("description")],
        "recent_titles": recent_posted,
        "recent_styles": [t["style"] for t in timeline if t["style"]],
        "recent_cta_types": [t["cta_type"] for t in timeline if t["cta_type"]],
        "tag_history": [(t["category"], t["hashtags"]) for t in timeline if t["hashtags"]],
        "dynamic_banned": _dynamic_banned(recent_posted),
        "generated_ctas": [g.get("cta") or "" for g in generated],
    }


def _dynamic_banned(titles: list[str]) -> set[str]:
    from collections import Counter
    c = Counter(w for t in titles for w in content_words(t))
    return {w for w, n in c.items() if n >= 2}


# ── Kontroller ───────────────────────────────────────────────────────────────────────────────────────────────────
def title_issues(title: str, ctx: dict, extra_titles: list[str] = ()) -> list[str]:
    out = []
    n = len(words(title))
    if not title or n > 9:
        out.append(f"{n} kelime (en fazla 9)")
    if emoji_count(title) > 2:
        out.append("2'den fazla emoji")
    bad = banned_phrases(title)
    if bad:
        out.append("yasak: " + ", ".join(bad))
    stop = ctx.get("event_stop", frozenset())
    dyn = content_words(title, stop) & ctx.get("dynamic_banned", set())
    if dyn:
        out.append("son başlıklarda sık: " + ", ".join(sorted(dyn)))
    for old in list(ctx.get("titles", [])) + list(extra_titles):
        if not old:
            continue
        if same_text(title, old) or jaccard(title, old, stop) > 0.5:
            out.append(f"benzer: {old}")
            break
        if first3(title, stop) == first3(old, stop) and len(first3(title, stop)) == 3:
            out.append(f"ilk 3 kelime aynı: {old}")
            break
    return out


def description_issues(desc: str, ctx: dict, opening: str = "", extra: list[str] = ()) -> list[str]:
    out = []
    n = len(words(desc))
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", (desc or "").strip()) if s]
    if not desc or n > 35 or len(sentences) > 2:
        out.append(f"{n} kelime / {len(sentences)} cümle (en fazla 35 / 2)")
    bad = banned_phrases(desc)
    if bad:
        out.append("yasak: " + ", ".join(bad))
    if opening and opening.rstrip(".").lower() in (desc or "").lower():
        out.append("açılış cümlesi birebir")
    for old in list(ctx.get("descriptions", [])) + list(extra):
        if old and (same_text(desc, old) or jaccard(desc, old, ctx.get("event_stop", frozenset())) > 0.45):
            out.append(f"benzer: {old[:60]}")
            break
    return out


def cta_issues(cta: str, cta_type: str) -> list[str]:
    if cta_type == "none":
        return [] if not cta else ["CTA yok tipinde metin var"]
    out = []
    if not cta:
        out.append("boş CTA")
    bad = banned_phrases(cta)
    if bad:
        out.append("yasak: " + ", ".join(bad))
    if cta_type == "stat" and not re.search(r"\b(\d+|two|three|four|five|six|seven|eight|nine|ten|fifteen)\b",
                                           (cta or "").lower()):
        out.append("istatistikte sayı yok")
    if cta_type == "emoji" and emoji_count(cta) < 1:
        out.append("emoji seçiminde emoji yok")
    return out


def allowed_after(options: list[str], history: list[str], depth: int = 2) -> list[str]:
    recent = set(h for h in history[-depth:] if h)
    left = [o for o in options if o not in recent]
    return left or list(options)


# ── Seçim ────────────────────────────────────────────────────────────────────────────────────────────────────────
_NO_PEOPLE_ALT = {"{people} People Run From the {threat} {emoji}": "One Take, Fifteen Seconds, {objects} {emoji}",
                  "{people} people, 15 seconds, one take.": "15 seconds, one take, no cuts."}


def _cap1(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


_CLAUSE_CUT = re.compile(r",\s|\s(?:and|sending|as|while)\s")
# Tekil özne olarak "it" ile değiştirilebilen tehdit adları (çoğullar hariç: "the flames leap" -> "it leap" olmaz)
_IT_SUBJECTS = re.compile(r"^the (?:towering |huge |violent )?(?:fire tornado|tornado|avalanche(?: front)?|flood|floodwater|mudslide|"
                          r"tidal wave|wave|surge|cloud(?: front)?|ash cloud|snow blast|snow wall|current)\b")


def beat_head(text: str) -> str:
    """Beat cümlesinin ilk cümleciği (en az 4 kelime kalıyorsa kesilir)."""
    t = (text or "").strip().rstrip(".")
    for m in _CLAUSE_CUT.finditer(t):   # ilk uygun kesim ("the SUV and the car behind it" kesilmez)
        if len(t[:m.start()].split()) >= 5:
            return t[:m.start()]
    return t


def _it(head: str) -> str:
    return _IT_SUBJECTS.sub("it", head, count=1)


def mentions_threat(head: str, event: str) -> bool:
    """Beat cümleciği tehdidi zaten anıyor mu (olay adı / eş anlamlısı)."""
    ws = {_norm(w) for w in words(head)} | set(words(head))
    return bool(ws & (EVENT_WORDS | event_stop(event) | {_norm(w) for w in words(VARS[event][0])}))


def _fill(template: str, event: str, info: dict) -> str:
    threat, target, emoji, objects, loc = VARS[event]
    if "{people}" in template and not info.get("people"):   # kişi sayısı yoksa uydurma sayı yok
        template = _NO_PEOPLE_ALT.get(template, template.replace("{people} ", ""))
    people = _NUMW.get(info.get("people") or 0, str(info.get("people") or ""))
    plural = event in PLURAL_THREATS
    witness = WITNESS.get(info.get("kadraj"), WITNESS[None])
    h2, h3 = beat_head(info.get("beat_2") or ""), beat_head(info.get("beat_3") or "")
    text = template.format(threat=threat, Threat=_cap1(threat.lower()), target=target, emoji=emoji,
                           threat_one=threat[:-1] if plural else threat,
                           objects=objects, loc=loc, witness=witness, people=people, threat_l=threat.lower(),
                           target_l=_lower(target), objects_l=_lower(objects), loc_l=_lower(loc), Loc=_cap1(_lower(loc)),
                           witness_l=_lower(witness), h2=h2, h3=h3, H2=_cap1(h2), H3=_cap1(h3), i2=_it(h2), i3=_it(h3),
                           as2="" if mentions_threat(h2, event) else f" as the {threat.lower()} hit{'' if plural else 's'}",
                           s="" if plural else "s", es="" if plural else "es")
    return _cap1(" ".join(text.split()))


def _lower(s: str) -> str:
    return (s or "").lower()


def title_pool(event: str, info: dict, candidates: dict | None, styles: list[str], rng: random.Random) -> list:
    """(kaynak, stil, metin) sırası: önce izinli stildeki GPT adayları (aday sırasıyla), sonra şablonlar."""
    out = []
    for text, style in (candidates or {}).get("titles", []):
        if style in styles:
            out.append(("GPT", style, text))
    order = list(styles)
    rng.shuffle(order)
    for st in order:
        for tpl in TITLE_TEMPLATES[st]:
            out.append(("şablon", st, _fill(tpl, event, info)))
    return out


def desc_templates(info: dict) -> tuple[str, ...]:
    """Beat cümleleri varsa beat'li şablonlar (somut), yoksa beat'siz iki şablon."""
    return DESC_TEMPLATES if info.get("beat_2") and info.get("beat_3") else DESC_TEMPLATES_NO_BEAT


def desc_pool(event: str, info: dict, candidates: dict | None, rng: random.Random | None = None) -> list:
    tpls = list(desc_templates(info))
    if rng is not None:   # iki beat'li şablonlar (çift tekrar etmez) önce, kendi içinde karışık; sonra tek beat'liler
        k = DESC_TWO_BEATS if tpls[0] == DESC_TEMPLATES[0] else 0
        two, one = tpls[:k], tpls[k:]
        rng.shuffle(two)
        rng.shuffle(one)
        tpls = two + one
    return ([("GPT", d) for d in (candidates or {}).get("descriptions", [])]
            + [("şablon", _fill(t, event, info)) for t in tpls])


def choose_hashtags(event: str, ctx: dict, rng: random.Random, exclude_sets: list = ()) -> list[str]:
    broad, special = event_tags(event)
    category = SHARE_CATEGORY[event]
    hist = ctx.get("tag_history", [])
    prev_same = next((tags for cat, tags in reversed(hist) if cat == category), set())
    last10 = [frozenset(t) for _, t in hist[-10:]] + [frozenset(s) for s in exclude_sets]
    combos = [list(b) + list(s) for b in itertools.combinations(broad, 2) for s in itertools.combinations(special, 3)]
    rng.shuffle(combos)
    combos = [c for c in combos if not any(is_banned_tag(t) for t in c)
              and (event in MARITIME_EVENTS or not set(c) & set(MARITIME_TAGS))]
    ok = [c for c in combos if len(set(c) & prev_same) <= 2 and frozenset(c) not in last10]
    if ok:
        chosen = ok[0]
    else:   # kural karşılanamıyorsa en az ortaklı ve yeni set
        fresh = [c for c in combos if frozenset(c) not in last10] or combos
        chosen = min(fresh, key=lambda c: len(set(c) & prev_same))
    foreign = set(chosen) - set(broad) - set(special)
    if foreign:   # 21 Eki (7.1): başka kategorinin etiketi asla çıkmaz
        raise ValueError(f"Etiket olayın havuzunda değil ({event}): {sorted(foreign)}")
    return chosen


def choose(event: str, info: dict, candidates: dict | None, ctx: dict, rng: random.Random,
           exclude_titles: list[str] = (), exclude_tag_sets: list = (), exclude_descriptions: list[str] = ()) -> dict:
    """Seçilen caption: {"title","description","cta","cta_type","hashtags","style","source","rejected",...}.
    info: {"opening","people","kadraj"} (hikâyeden). exclude_titles: bu üretimde daha önce önerilenler (Yeni caption)."""
    ctx = {**ctx, "event_stop": event_stop(event)}
    stop = ctx["event_stop"]
    styles = allowed_after(list(STYLES), ctx.get("recent_styles", []))
    rejected = []
    title = style = t_src = None
    pool = title_pool(event, info, candidates, styles, rng)
    for src, st, text in pool:
        if text in exclude_titles:
            continue
        issues = title_issues(text, ctx, exclude_titles)
        if issues:
            rejected.append({"alan": "başlık", "kaynak": src, "metin": text, "neden": issues[0]})
            continue
        title, style, t_src = text, st, src
        break
    if title is None:   # hiçbiri geçmedi: en az benzer şablon (zorunlu)
        used = set(exclude_titles) | set(ctx.get("titles", []))   # zorunlu durumda da birebir tekrar yok
        tpls = [(st, text) for src, st, text in pool if src == "şablon" and text not in used] or \
               [(st, text) for src, st, text in pool if src == "şablon"]
        style, title = min(tpls, key=lambda x: (len(title_issues(x[1], ctx, exclude_titles)),
                                                max([jaccard(x[1], o, stop) for o in ctx.get("titles", []) if o] or [0])))
        t_src = "şablon (zorunlu)"
    description = d_src = None
    for src, text in desc_pool(event, info, candidates, rng):
        if text in exclude_descriptions:
            continue
        issues = description_issues(text, ctx, info.get("opening", ""))
        if not issues and src == "şablon":   # 21 Eki (7.1): şablonlar aynı ilk 3 kelimeyle başlamaz
            same = next((o for o in ctx.get("descriptions", []) if o and len(first3(text, stop)) == 3
                         and first3(text, stop) == first3(o, stop)), None)
            if same:
                issues = [f"ilk 3 kelime aynı: {same[:60]}"]
        if issues:
            rejected.append({"alan": "açıklama", "kaynak": src, "metin": text, "neden": issues[0]})
            continue
        description, d_src = text, src
        break
    if description is None:
        opts = [_fill(t, event, info) for t in desc_templates(info)]
        opts = [o for o in opts if o not in exclude_descriptions] or opts
        description = min(opts, key=lambda o: max([jaccard(o, x, stop) for x in ctx.get("descriptions", []) if x]
                                                  or [0]))
        d_src = "şablon (zorunlu)"
    types = allowed_after(list(CTA_TYPES), ctx.get("recent_cta_types", []))
    gpt_type = (candidates or {}).get("cta_type")
    gpt_cta = (candidates or {}).get("cta", "")
    if gpt_type in types and not cta_issues(gpt_cta if gpt_type != "none" else "", gpt_type):
        cta_type, cta, c_src = gpt_type, (gpt_cta if gpt_type != "none" else ""), "GPT"
    else:
        if candidates and gpt_type:
            rejected.append({"alan": "CTA", "kaynak": "GPT", "metin": gpt_cta,
                             "neden": "tip son 2'de" if gpt_type not in types else cta_issues(gpt_cta, gpt_type)[0]})
        cta_type = gpt_type if gpt_type in types else rng.choice(types)
        used = set(ctx.get("generated_ctas", []))
        opts = [_fill(t, event, info) for t in CTA_TEMPLATES[cta_type]]
        cta = next((o for o in opts if o not in used), opts[0])
        c_src = "şablon"
    hashtags = choose_hashtags(event, ctx, rng, exclude_tag_sets)
    srcs = {t_src.split(" ")[0], d_src.split(" ")[0]}
    source = "GPT" if srcs == {"GPT"} else ("şablon" if srcs == {"şablon"} else "GPT + şablon")
    return {"title": title, "description": description, "cta": cta, "cta_type": cta_type, "hashtags": hashtags,
            "style": style, "source": source, "title_source": t_src, "description_source": d_src, "cta_source": c_src,
            "category": SHARE_CATEGORY[event], "rejected": rejected}


def block(c: dict) -> str:
    """Kopyalanmaya hazır tek parça metin (CTA yoksa satırı ve boşluğu yok)."""
    parts = [c["title"], c["description"]]
    if c.get("cta"):
        parts.append(c["cta"])
    parts.append(" ".join(c["hashtags"]))
    return "\n\n".join(parts)


def info_line(c: dict) -> str:
    return f"stil: {c['style']} · CTA: {CTA_TYPES[c['cta_type']]} · kaynak: {c['source']}"


def meta(c: dict) -> dict:
    """Notion "Eksenler" / üretilmiş caption geçmişi için kısa kayıt."""
    return {"title": c["title"], "description": c["description"], "cta": c["cta"], "style": c["style"],
            "cta_type": c["cta_type"], "hashtags": c["hashtags"], "category": c["category"], "source": c["source"]}


TR_TZ = timezone(timedelta(hours=3))   # Türkiye saati (UTC+3, yaz saati yok)


def today_tr() -> str:
    return datetime.now(TR_TZ).date().isoformat()
