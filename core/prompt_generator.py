from __future__ import annotations

"""
Prompt Generator — "DeepMyster" Doğukan Metodolojisi & Yaratıcı Serbestlik Pipeline.

Akış:
  1. Creative Engine'den geniş denizcilik katalizörü alır (Kutup, Ağır Yük, Kurtarma, vb. + Negatif Geçmiş).
  2. GPT-4o ile tam yaratıcı özgürlükle (config.DEFAULT_DURATION saniyelik) tek kesintisiz çekim fiziksel senaryo tasarlar.
  3. Sessiz Ekran Görünürlük Kontrolü (görünmez sualtı/makine durumlarını filtreler).
  4. GPT-4o ile Seedance 2 Mini'ye özel 25–45 kelimelik yüksek sinyalli prompt üretir (Doğukan Less is More).
  5. YouTube metadata (merak odaklı, no-spoiler) ve cerrahi safety sanitizer uygular.
"""
import re
import json
import asyncio
import logging
import threading
from openai import OpenAI
from config import settings
from core.creative_engine import (
    get_creative_catalyst,
    build_scenario_writer_system,
    build_prompt_simplifier_system,
    compute_duration_breakpoints,
    choose_camera_archetype,
    CAMERA_ARCHETYPES,
    YOUTUBE_METADATA_SYSTEM,
    VESSEL_UNIVERSE,
    SHIP_NAME_PATTERNS,
    DOMAIN_CAST_RANGES,
    ENV_CENTRIC_DOMAINS,
    apply_style_lock,
)

log = logging.getLogger("PromptGenerator")


def clean_youtube_title(title: str) -> str:
    """Başlığın başındaki 'DeepMyster:' vb. otomatik kanal öneklerini temizler."""
    if not title:
        return "Extreme Waves Crash Vessel in Storm #Shorts"
    cleaned = re.sub(r"^(?:\[?DeepMyster\]?[\s:\-\|]+)+", "", title.strip(), flags=re.IGNORECASE).strip()
    return cleaned if cleaned else title


# ── OpenAI Client Singleton (TCP bağlantı yeniden kullanımı) ──
_openai_client: OpenAI | None = None
_openai_lock = threading.Lock()


def _get_openai_client() -> OpenAI:
    """OpenAI client singleton — her çağrıda yeni bağlantı açmaz."""
    global _openai_client
    if _openai_client is None:
        with _openai_lock:
            if _openai_client is None:
                _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


async def _call_gpt(system_prompt: str, user_message: str, temperature: float = 0.85) -> dict:
    """GPT-4o'yu çağır ve JSON yanıtı parse et."""
    try:
        client = _get_openai_client()
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f"❌ GPT yanıtı JSON parse edilemedi: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"❌ GPT çağrısı başarısız: {e}", exc_info=True)
        raise


def validate_silent_visibility(scenario: dict) -> tuple[bool, list[str]]:
    """
    Sessiz Ekran Görünürlük Kontrolü (Hafif Mantıksal Sanity Check).
    
    Kontroller:
      1. Görünmez sualtı olayları (underwater rudder, submerged shaft, sonar screen) var mı?
      2. Senaryo özeti ve fiziksel hareket tanımlı mı?
    """
    failures = []
    desc = scenario.get("scene_description", "")
    summary = scenario.get("scenario_summary", "")
    full_text = f"{desc} {summary}".lower()

    # Görünmez / Sualtı / Sadece sesle anlaşılan yasaklı anahtar kelimeler
    invisible_keywords = [
        "underwater rudder", "submerged shaft", "engine room blackout",
        "sonar screen", "radar glitch", "radio static", "alarm sound only"
    ]
    for kw in invisible_keywords:
        if kw in full_text:
            failures.append(f"Görünmez/Sualtı öğesi tespit edildi: '{kw}'")

    if not summary and not desc:
        failures.append("Senaryo açıklaması veya özeti boş")

    is_valid = len(failures) == 0
    return is_valid, failures


# ── Aksiyon/Tehlike Yoğunluğu Kontrolü — kelime listeleri ──
_HIGH_ACTION_KEYWORDS = [
    "colli",       # collision, collide, colliding
    "crash", "slam", "snap", "flood", "swing", "list", "capsiz",
    "ruptur", "strain", "jam", "buckle", "shear", "sever", "detach",
    "spark", "smoke", "drift", "surge", "topple", "tilt", "sink",
    "grind", "wedge", "brace", "scramble", "out of control",
    # 2026-09-24: GPT'nin Beat 1'de gerçekte kullandığı fiiller (N3 dry-run).
    # roll/fall/pitch bilinçli yok: "clouds rolling in", "rain falling", "pitch black".
    "shake", "gush", "collapse", "hurl", "yank", "sweep", "whip", "plunge",
    "veer", "lash", "pound", "batter", "heave", "shatter", "twist", "barrel",
    "slide", "slip", "spray", "flip", "tumble",
    # 2026-09-24 N14: tornado/rüzgâr açılışları ("spins", "knocks", "swirling")
    "knock", "spin", "swirl", "shift", "rush", "sway", "jolt", "jerk",
    # 2026-09-24 N14c: yedek liste için son ekleme. Ana yol artık GPT'nin
    # bildirdiği beat1_action_verb; bu liste sonsuz genişletilmeyecek.
    "lift", "scatter", "erupt",
]

_STATIC_KEYWORDS = [
    "driving", "parking", "loading", "waiting", "standing by", "routine",
    "calm", "normal operations", "peacefully", "smoothly", "uneventful",
    "idle", "quietly", "nothing unusual", "business as usual",
]

# ── Beat 1'e özel: durgun kurulum kalıpları (2026-09-23 tespit edildi) ──
_STATIC_START_PATTERNS = [
    "one passenger standing", "one crew member standing",
    "can be seen at", "can be seen near",
    "watching as", "watches as",
    "starts to gather", "start to gather",
    "focuses on", "focused on",
    "positioned near", "stands near",
    "prepares to", "preparing to",
    "quietly waits", "silently waits",
    "a calm", "the calm",
]
# "Two yachts can be seen..." gibi genel "Two X can be seen" kalıbı (yukarıdaki
# "can be seen at/near" ikilisinin kaçırdığı, "at/near" olmayan varyantlar için)
_STATIC_START_REGEX = re.compile(r"\btwo\s+\w+[\w\s]{0,30}\bcan be seen\b", re.IGNORECASE)

# Kelime sınırlı kalıplar (2026-09-24 tespit edildi). Substring değil regex:
# "is visible" düz aramada "is visibly buckling"i, "opens on" ise "hatch opens
# onto"yu yanlışlıkla reddederdi.
_STATIC_START_REGEXES = [
    ("<iki X görülebilir kalıbı>", _STATIC_START_REGEX),
    ("is visible", re.compile(r"\bis\s+visible\b")),
    ("visible from", re.compile(r"\bvisible\s+from\b")),
    ("as X approaches", re.compile(r"\bas\s+(?:it|the\s+(?:[\w-]+\s+){0,3}?[\w-]+)\s+(?:is\s+)?approach(?:es|ing)\b")),
    ("scene opens", re.compile(r"\bscene\s+opens\b")),
    ("observing as", re.compile(r"\bobserv(?:es|ing)\s+as\b")),
    ("bustling", re.compile(r"\bbustling\b")),
    ("looming", re.compile(r"\blooming\b")),
    ("signals for/to", re.compile(r"\bsignals?\s+(?:for|to)\b")),
]

# Kamera/görüntü öznesiyle açılış (2026-09-24): "The image captures…", "A fixed camera shows…".
# Bildirilen fiil ("straining") geçerli olsa bile özne kamera olunca Kie durgun/kurulum
# tarzı açabilir. Sadece cümle BAŞI (BEAT etiketi atlanarak); ortadaki "…as the camera
# captures" serbest. "From the bow of…, the catamaran lurches" gibi konum girişleri serbest:
# orada özne hâlâ tekne.
_CAMERA_NOUNS = (r"(?:image|scene|camera|cam|cctv|shot|footage|video|frame|feed|view|lens|"
                 r"recording|clip|picture|surveillance)")
_CAMERA_VERBS = (r"(?:captures?|captured|shows?|opens?|catches|catch|films?|records?|reveals?|depicts?|"
                 r"displays?|pans?|focuses|frames?|zooms?|cuts?|begins?|starts?|looks|observes?|features?|"
                 r"presents?|is\s+trained|is\s+fixed|is\s+(?:capturing|showing|filming|recording|focusing|panning))")
_CAMERA_SUBJECT_RE = re.compile(
    r"^\s*(?:beat\s*\d+\s*(?:\([^)]*\))?\s*[:\-—]\s*)?"
    r"(?:"
    rf"(?:(?:the|a|an|this)\s+)?(?:[\w-]+\s+){{0,3}}?{_CAMERA_NOUNS}s?"
    r"(?:\s+(?:from|of|on)\s+(?:[\w'-]+\s+){0,5}?[\w'-]+)?"
    rf"\s+{_CAMERA_VERBS}\b"
    r"|(?:we|viewers?)\s+see\b|in\s+the\s+frame\b|on\s+(?:the\s+)?screen\b"
    r")",
    re.IGNORECASE,
)
_STATIC_START_REGEXES.append(("kamera öznesiyle açılış", _CAMERA_SUBJECT_RE))


def _static_start_hits(vstart_low: str) -> list[str]:
    """Beat 1 blacklist: visible_start'ta eşleşen durgun kurulum kalıpları (küçük harf girdi)."""
    hits = [p for p in _STATIC_START_PATTERNS if p in vstart_low]
    hits += [label for label, rx in _STATIC_START_REGEXES if rx.search(vstart_low)]
    return hits


_STRONG_OPENING_VERBS = [
    "crashes", "slams", "strikes", "surges", "swings", "snaps",
    "lurches", "breaks", "tears", "bursts", "rips",
]

# ── Beat 1 whitelist: ilk cümlede en az bir aksiyon fiili (2026-09-24) ──
# Kök + serbest ek: "crash" → crash/crashes/crashing. Kelime başına sabitli (\b).
# Sondaki "e" atılır ki buckle→buckling, scramble→scrambling da eşleşsin.
_BEAT1_ACTION_STEMS = sorted(set(
    re.sub(r"e$", "", s) for s in
    _HIGH_ACTION_KEYWORDS
    + [re.sub(r"(es|s)$", "", v) for v in _STRONG_OPENING_VERBS]  # crashes→crash, lurches→lurch
))
_BEAT1_ACTION_REGEX = re.compile(
    r"\b(?:" + "|".join(r"\s+".join(map(re.escape, s.split())) for s in _BEAT1_ACTION_STEMS) + r")[\w-]*",
    re.IGNORECASE,
)
# Kökü eşleşip anlamı durgun olan kelimeler
_BEAT1_FALSE_FRIENDS = {
    "several", "severe", "severely", "severity",   # sever
    "listen", "listens", "listening", "listless",  # list
    "sparkle", "sparkles", "sparkling",            # spark
    "surgeon", "surgery",                          # surg(e)
    "floodlight", "floodlights", "floodlit",       # flood
    "ripple", "ripples", "rippling",               # rip
    "smoky",                                       # smok(e)
    "slip", "slipway", "slipways", "slippery",     # slip: "yacht in its slip" (marina rıhtımı)
    "shaky",                                       # shak(e): "shaky footage"
    "heavy", "heavier", "heaviest", "heavily", "heaven",  # heav(e)
    "barrel",                                      # tekil isim: "an oil barrel"
    "lashings",                                    # isim: araç bağlama zincirleri
    "battery", "batteries",                        # batter
    "flip-flop", "flip-flops", "flippers",         # flip
    "spinnaker", "spinnakers", "spine", "spines", "spinal", "spindle", "spindles",  # spin
    "shifty", "jerky", "knockout", "knockouts",    # shift, jerk, knock
    "liftgate", "liftgates", "lifter", "lifters",  # lift
    "scattered", "scatterbrained",                 # scatter: "scattered clouds"
    # Bilinçli olarak YOK: "rush" ("rush hour"), "shift" ("night shift"), "lift"
    # ("travel lift") ve "lifts" ("ski lifts") fiil olarak da kullanılıyor
    # ("crew rush to...", "begins to shift", "a gust lifts"). Kabul edilmiş risk.
    "bracelet", "snapshot", "breakwater", "breakfast",
}
# GPT'nin alan içine sızdırdığı "BEAT 2 (1-8s):" gibi etiketler
_BEAT_LABEL_RE = re.compile(r"^\s*BEAT\s*\d+\s*(?:\([^)]*\))?\s*[:\-—]\s*", re.IGNORECASE)


def _action_words(text: str, first_sentence_only: bool) -> list[str]:
    """Metindeki aksiyon fiillerini döndürür (false friend'ler elenir, etiket temizlenir)."""
    text = _BEAT_LABEL_RE.sub("", text or "").strip()
    if first_sentence_only:
        text = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
    words = [m.group(0).lower() for m in _BEAT1_ACTION_REGEX.finditer(text)]
    return [w for w in words if w not in _BEAT1_FALSE_FRIENDS]


def _beat1_action_words(visible_start: str) -> list[str]:
    """visible_start'ın İLK cümlesindeki aksiyon fiillerini döndürür (boş liste = durgun)."""
    return _action_words(visible_start, first_sentence_only=True)


# ── Beat 3 kapısı: sonuç hâlâ tehlikeli ve sürüyor mu (2026-09-24) ──
# Kalıp önündeki en fazla 3 kelimede olumsuzluk varsa eşleşme sayılmaz:
# "shows no sign of stopping", "never settles", "far from calm" istediğimiz sonlar.
_NEGATION_BEFORE_RE = re.compile(
    r"\b(?:no|not|never|without|unable\s+to|fails?\s+to|cannot|can't|refuses?\s+to|far\s+from)\s+(?:\w+\s+){0,2}$"
)
# Kelime sınırlı: "to safety", "safety lines", "steadily rising" eşleşmez.
_BEAT3_BLACKLIST = [
    ("steady", re.compile(r"\bstead(?:y|ies|ied|ying)\b")),
    ("settle", re.compile(r"\bsettl(?:e|es|ed|ing)\b")),
    ("rest/halt/stop", re.compile(r"\b(?:comes?|came|coming|grinds?|ground|jerks?|screeches?)\s+to\s+(?:a\s+)?(?:rest|halt|stop|standstill)\b")),
    ("stop", re.compile(r"\bstop(?:s|ped|ping)\b")),
    ("calm", re.compile(r"\bcalm(?:s|ed|ing|ly)?\b")),
    ("anticipation", re.compile(r"\banticipation\b")),
    ("watch in/intently", re.compile(r"\bwatch(?:es|ing|ed)?\s+(?:in|intently)\b")),
    ("safe", re.compile(r"\bsafe(?:ly)?\b|\bsafety\s+returns\b")),
    ("resolve", re.compile(r"\bresolv(?:e|es|ed|ing)\b")),
    ("under control", re.compile(r"\bunder\s+control\b")),
    ("recover", re.compile(r"\brecover(?:s|ed|ing)?\b")),
    ("cautious distance", re.compile(r"\bmaintain(?:s|ing)?\s+a\s+cautious\s+distance\b")),
    # İzleyerek bitiş (2026-09-24, r9#5 "...tangling around a piling as they watch."):
    # "continues to thrash" işareti olsa da son kare izleyen insanlarda kalıyor.
    ("izleyerek bitiş", re.compile(
        r"\b(?:as|while)\s+(?:[\w'-]+\s+){0,3}(?:watch(?:es|ing)?|looks?\s+on|looking\s+on|"
        r"star(?:e|es|ing)|observ(?:e|es|ing))\b\W*$")),
]
# still/continues/keeps'ten sonra gelirse "devam eden aksiyon" sayılmayan fiiller
_BEAT3_STATIC_VERBS = {
    "standing", "waiting", "watching", "sitting", "looking", "staring", "observing",
    "idling", "resting", "remaining",
    "stand", "wait", "watch", "sit", "look", "stare", "observe", "remain",
}
_STILL_RE = re.compile(r"\bstill\s+(?:\w+ly\s+)?(being\s+\w+|\w+ing)\b")   # "still water" eşleşmez
_CONTINUE_RE = re.compile(r"\bcontinu(?:e|es|ed|ing)\s+(?:to\s+)?(\w+)")
_KEEP_RE = re.compile(r"\bkeeps?\s+(?:on\s+)?(\w+ing)\b")


# ── Beat 1 ana yol: GPT'nin bildirdiği aksiyon fiili (2026-09-24 N14c) ──
# Sabit kelime listesi her yeni fiilde genişletilmek zorundaydı. Yazıcı artık
# "beat1_action_verb" alanında fiili bildirir; kod fiilin gerçekten ilk cümlede,
# olumsuzlanmamış ve insan/kamera fiili olmadan geçtiğini doğrular.
_BEAT1_NON_ACTION_VERBS = _BEAT3_STATIC_VERBS | {
    "react", "reacts", "reacting", "see", "sees", "seeing", "gather", "gathers", "gathering",
    "show", "shows", "showing", "catch", "catches", "capture", "captures", "film", "films",
    "appear", "appears", "notice", "notices",
}


def _declared_beat1_verb_ok(scenario: dict) -> bool:
    """GPT'nin bildirdiği beat1_action_verb gerçek bir tehlike fiili olarak ilk cümlede mi?"""
    verb = (scenario.get("beat1_action_verb") or "").strip().lower()
    # Kelime türünü kod bilemez; bilinen durgun isimler (spinnaker, heavy) fiil sayılmaz
    if not verb or " " in verb or verb in _BEAT1_NON_ACTION_VERBS or verb in _BEAT1_FALSE_FRIENDS:
        return False
    first = re.split(
        r"(?<=[.!?])\s+", _BEAT_LABEL_RE.sub("", scenario.get("visible_start", "") or "").strip(), maxsplit=1
    )[0].lower()
    m = re.search(rf"\b{re.escape(verb)}\b", first)   # fiil gerçekten ilk cümlede mi
    return bool(m) and not _NEGATION_BEFORE_RE.search(first[:m.start()])


def _beat3_blacklist_hits(text: str) -> list[str]:
    """Olumsuzlanmamış 'çözülmüş/sakinleşmiş son' kalıpları."""
    low = text.lower()
    hits = []
    for label, rx in _BEAT3_BLACKLIST:
        if any(not _NEGATION_BEFORE_RE.search(low[:m.start()]) for m in rx.finditer(low)):
            hits.append(label)
    return hits


def _beat3_ongoing_markers(text: str) -> list[str]:
    """still/continues/keeps + hareketli fiil. Durgun fiiller (watching, standing) sayılmaz."""
    low = _BEAT_LABEL_RE.sub("", text or "").lower()
    markers = []
    for rx in (_STILL_RE, _CONTINUE_RE, _KEEP_RE):
        for m in rx.finditer(low):
            if m.group(1).split()[-1] not in _BEAT3_STATIC_VERBS:
                markers.append(m.group(0))
    return markers


def validate_beat3_ongoing_danger(scenario: dict) -> tuple[bool, list[str]]:
    """Beat 3 (visible_consequence) tehlike sürerken mi bitiyor?

    Red: çözülmüş/sakinleşmiş son kalıbı (blacklist) VEYA hiç devam eden aksiyon
    işareti yok (still/continues/keeps + hareketli fiil ya da aksiyon fiili).
    """
    consequence = _BEAT_LABEL_RE.sub("", scenario.get("visible_consequence", "") or "").strip()
    if not consequence:
        return False, ["Beat 3 boş"]
    failures = []
    hits = _beat3_blacklist_hits(consequence)
    if hits:
        failures.append(f"Beat 3 tehlike çözülmüş/sakinleşmiş bitiyor: {hits}")
    if not (_beat3_ongoing_markers(consequence) or _action_words(consequence, first_sentence_only=False)):
        failures.append("Beat 3'te devam eden aksiyon yok (still/continues/keeps veya aksiyon fiili)")
    return not failures, failures


# ── Cast sayı kapısı (2026-09-24) ──
# Yazıcıya DOMAIN_CAST_RANGES aralığı talimat olarak gidiyordu ama kontrol eden kapı yoktu
# (N14c ferry: "four crew members and about a dozen passengers" = 16, aralık 2-5).
# Sayı Beat 1'de bir kez söylenir; Beat 2/3 genelde "the workers" diye geri atıf yapar.
_CAST_NUM_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen twenty".split())}
_CAST_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}
_CAST_PERSON = (
    r"(?:people|persons?|deckhands?|crew\s+members?|crewmembers?|crewmen|crew|workers?|"
    r"dockworkers?|dockhands?|staff(?:\s+members?)?|passengers?|guests?|tourists?|officers?|"
    r"captains?|sailors?|technicians?|engineers?|riggers?|bystanders?|pedestrians?|beachgoers?|"
    r"spectators?|onlookers?|attendants?|lifeguards?|men|women|man|woman|swimmers?|surfers?|"
    r"stewards?|mechanics?|operators?|welders?|visitors?|holidaymakers?|sunbathers?|guards?|mariners?)"
)
_CAST_NUM = (
    r"(?:\d{1,3}|(?:twenty|thirty|forty|fifty)(?:[\s-](?:one|two|three|four|five|six|seven|eight|nine))?|"
    + "|".join(sorted(_CAST_NUM_WORDS, key=len, reverse=True))
    + r"|a\s+dozen|half\s+a\s+dozen|a\s+couple\s+of|a\s+pair\s+of|a\s+single|a\s+lone|a\s+solitary)"
)
_CAST_HEDGE = r"(?:about|approximately|around|roughly|some|nearly|almost)"
# Sayı ile kişi ismi arasında en fazla 2 niteleyici ("three dock workers"); bağlaç/edat varsa
# eşleşmez, böylece "two cars slide as workers" 2 kişi sayılmaz.
_CAST_MOD = r"(?:(?!(?:and|or|as|while|with|of|the|a|an|to|from|on|in|at|by|near|who|that|are|is)\b)[\w'-]+\s+){0,2}"
_CAST_RE = re.compile(
    rf"\b(?P<hedge>{_CAST_HEDGE}\s+)?(?P<num>{_CAST_NUM})\s+{_CAST_MOD}{_CAST_PERSON}\b(?!\s+of\b)", re.I)
_CAST_SUBSET_RE = re.compile(rf"\b{_CAST_NUM}\s+of\s+(?:the|them|these|those)\b", re.I)
_CAST_VAGUE_RE = re.compile(
    rf"\b(?:several|a\s+few|a\s+handful\s+of|a\s+group\s+of|a\s+crowd\s+of|dozens\s+of|many|numerous|"
    rf"multiple|various)\s+(?:[\w'-]+\s+){{0,2}}{_CAST_PERSON}\b", re.I)
_CAST_ANY_PERSON_RE = re.compile(rf"\b{_CAST_PERSON}\b", re.I)


def _cast_value(num: str) -> int:
    s = re.sub(r"\s+", " ", num.lower())
    if s.isdigit():
        return int(s)
    if s in _CAST_NUM_WORDS:
        return _CAST_NUM_WORDS[s]
    fixed = {"a dozen": 12, "half a dozen": 6, "a couple of": 2, "a pair of": 2,
             "a single": 1, "a lone": 1, "a solitary": 1}
    if s in fixed:
        return fixed[s]
    parts = re.split(r"[\s-]", s)
    return _CAST_TENS[parts[0]] + (_CAST_NUM_WORDS[parts[1]] if len(parts) > 1 else 0)


def _cast_counts(text: str) -> list[tuple[int, bool, str]]:
    """(sayı, hedge'li mi, eşleşen ifade) listesi; 'one of the deckhands' gibi alt kümeler hariç."""
    text = _CAST_SUBSET_RE.sub(" ", _BEAT_LABEL_RE.sub("", text or ""))
    return [(_cast_value(m["num"]), bool(m["hedge"]), m.group(0)) for m in _CAST_RE.finditer(text)]


def validate_cast_size(scenario: dict, domain_id: str) -> tuple[bool, list[str]]:
    """Ekrandaki kişi sayısı DOMAIN_CAST_RANGES aralığında mı, beat'ler boyunca artmıyor mu?

    Env-centric domainler atlanır. Beat 1 toplamı aralıkta olmalı (hedge'li sayıda üstte
    %20 / en az 1, altta 1 tolerans). Belirsiz ifade, sayısız kişi veya hiç insan yoksa red.
    Beat 2/3'te Beat 1'den FAZLA kişi red; eşit/az (geri atıf, alt küme) kabul.
    """
    if domain_id in ENV_CENTRIC_DOMAINS or domain_id not in DOMAIN_CAST_RANGES:
        return True, []
    lo, hi = DOMAIN_CAST_RANGES[domain_id]
    beat1 = scenario.get("visible_start", "") or ""
    beat1_counts = _cast_counts(beat1)
    if not beat1_counts:
        if _CAST_VAGUE_RE.search(beat1):
            return False, [f"Cast: Beat 1'de belirsiz kişi ifadesi, sayı yok (aralık {lo}-{hi})"]
        if _CAST_ANY_PERSON_RE.search(beat1):
            return False, [f"Cast: Beat 1'de kişi var ama sayı yok (aralık {lo}-{hi})"]
        return False, [f"Cast: Beat 1'de hiç insan yok (aralık {lo}-{hi})"]

    total = sum(n for n, _, _ in beat1_counts)
    hedged = any(h for _, h, _ in beat1_counts)
    up_tol = max(1, round(hi * 0.2)) if hedged else 0
    low_tol = 1 if hedged else 0
    phrases = [p for _, _, p in beat1_counts]
    failures = []
    if total > hi + up_tol:
        failures.append(f"Cast: {total} kişi, üst sınır {hi} aşıldı {phrases}")
    if total < lo - low_tol:
        failures.append(f"Cast: {total} kişi, alt sınır {lo} altında {phrases}")
    for label, key in (("Beat 2", "physical_movement"), ("Beat 3", "visible_consequence")):
        for n, _, phrase in _cast_counts(scenario.get(key, "")):
            if n > total:
                failures.append(f"Cast: {label}'de Beat 1'den fazla kişi ({phrase} > {total})")
    return not failures, failures


# ── Özet ↔ beat tutarlılığı (2026-09-24, TUR 6) ──
# Faz 3: özet "beachgoers scramble for safety" diyor, 3 beat'te insan yok; simplifier özeti de
# okuduğu için insanlar Kie prompt'una taşındı. Kişi ismi gibi görünen nesne ifadeleri hariç.
_PERSON_FALSE_FRIENDS_RE = re.compile(
    r"\bguard\s*rails?\b|\bguardrails?\b|\blifeguard\s+(?:tower|stand|station|hut|chair|post)s?\b|\bman-made\b|"
    r"\bpassengers?\s+(?:car\s+)?(?:ferry|ferries|ship|ships|vessel|vessels|deck|decks|terminal|gangway|ramp|"
    r"lounge|area|seats?|cabins?|liner)\b|"
    r"\bcrew\s+(?:quarters|cabins?|deck|boat|tender|lift)\b",
    re.IGNORECASE,
)


def _person_mentions(text: str) -> list[str]:
    """Metindeki kişi isimleri; 'guard rail', 'Passenger Car Ferry' gibi nesne ifadeleri sayılmaz."""
    return [m.group(0) for m in _CAST_ANY_PERSON_RE.finditer(_PERSON_FALSE_FRIENDS_RE.sub(" ", text or ""))]


def validate_scenario_consistency(scenario: dict) -> tuple[bool, list[str]]:
    """Özet, 3 beat'te olmayan insanları sahneye sokuyor mu? (simplifier özeti de okur)"""
    summary_people = _person_mentions(scenario.get("scenario_summary", ""))
    beat_people = [p for k in ("visible_start", "physical_movement", "visible_consequence")
                   for p in _person_mentions(scenario.get(k, ""))]
    if summary_people and not beat_people:
        return False, [f"Özet beat'lerde olmayan insanlardan bahsediyor: {summary_people}"]
    return True, []


# ── Simplifier çıktı kapısı (2026-09-24, TUR 5) ──
# Senaryo kapıları senaryoya bakıyordu; simplifier çıktısı Kie'ye kontrolsüz gidiyordu.
# Faz 1 ölçümü (20 çıktı): Beat 3 %10, Beat 1 fiili düşmüş %15, kişi sayısı düşmüş %20.
def _verb_stem(word: str) -> str:
    w = word.lower()
    for suf in ("ing", "es", "ed", "s", "e"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def _simplified_checks(prompt: str, scenario: dict, domain_id: str, ship: str = "") -> list[tuple[str, str]]:
    """(log için Türkçe hata, simplifier retry'ına İngilizce düzeltme talimatı) listesi.

    ship: atanan gemi (catalyst['forced_ship']); verilmezse F kontrolü atlanır.
    """
    sentences = re.split(r"(?<=[.!?])\s+", _BEAT_LABEL_RE.sub("", prompt or "").strip())
    first, last = sentences[0], sentences[-1]
    if not first:
        return [("Simplifier: boş prompt", "Return a non-empty prompt.")]
    issues = []

    # A — Beat 3 devamı: son cümle senaryo Beat 3 kapısından geçmeli
    b3_ok, b3_fail = validate_beat3_ongoing_danger({"visible_consequence": last})
    if not b3_ok:
        issues.append((f"Simplifier son cümle: {b3_fail}",
                       "End the final sentence mid-action with the danger still unfolding (keep 'still'/'continues'/"
                       "'keeps' from the scenario); never end on the danger stopping or on people watching."))

    # B — kamera öznesiyle açılış
    if _CAMERA_SUBJECT_RE.search(first):
        issues.append(("Simplifier: kamera öznesiyle açılış",
                       "Start with the physical thing in danger as the subject; never make the camera, image, "
                       "scene or footage the subject."))

    # C — Beat 1 fiil sadakati: yazıcının bildirdiği fiil (kök eşleşmesi) ilk cümlede
    verb = (scenario.get("beat1_action_verb") or "").strip()
    if verb and " " not in verb:
        stem = _verb_stem(verb)
        if not any(_verb_stem(w) == stem for w in re.findall(r"[\w-]+", first)):
            issues.append((f"Simplifier: Beat 1 fiili '{verb}' ilk cümlede yok (zaman sıkışması)",
                           f"The first sentence must show the scenario's opening action with the verb '{verb}' "
                           "(any tense); do not pull the later escalation into the first sentence."))

    # E — sayı sadakati: gemi domainlerinde senaryodaki kişi sayısı aynen korunmalı
    if domain_id in DOMAIN_CAST_RANGES:
        scen_counts = _cast_counts(scenario.get("visible_start", ""))
        total = sum(n for n, _, _ in scen_counts)
        if total:
            phrases = " and ".join(p for _, _, p in scen_counts)
            per_sentence = [_cast_counts(s) for s in sentences]
            stated = next((c for c in per_sentence if c), [])
            stated_total = sum(n for n, _, _ in stated)
            later_over = [p for c in per_sentence for n, _, p in c if n > total]
            if not stated:
                issues.append((f"Simplifier: kişi sayısı düşmüş (senaryo: {phrases})",
                               f"Keep the exact head count from the scenario: '{phrases}'."))
            elif stated_total != total or later_over:
                issues.append((f"Simplifier: kişi sayısı değişmiş ({stated_total} ≠ {total}, senaryo: {phrases})",
                               f"Keep the exact head count from the scenario: '{phrases}'; do not add people."))

    # F — gemi adı (TUR 8): gemi domainlerinde atanan geminin tipi prompt'ta geçmeli;
    # "the vessel" tek başına Kie'ye kargo gemisi çizdiriyordu.
    if domain_id in DOMAIN_CAST_RANGES and ship and ship.lower() != "none":
        pattern = SHIP_NAME_PATTERNS.get(ship)
        if pattern is None:
            raise RuntimeError(f"SHIP_NAME_PATTERNS'ta '{ship}' yok — evren dışı gemi, config hatası.")
        if not re.search(pattern, prompt, re.IGNORECASE):
            issues.append((f"Simplifier: gemi adı yok (atanan: {ship})",
                           f"Name the vessel by its type ('the {ship.lower()}'); never call it only "
                           "'the vessel', 'the ship' or 'the boat'."))
    return issues


def validate_simplified_prompt(prompt: str, scenario: dict, domain_id: str, ship: str = "") -> tuple[bool, list[str]]:
    """Simplifier ham çıktısı (stil kilidi öncesi) Kie'ye gitmeye uygun mu?

    A: son cümle Beat 3 kapısından geçer (izleyerek bitiş dahil). B: kamera öznesiyle açılmaz.
    C: yazıcının bildirdiği Beat 1 fiili ilk cümlede. E: gemi domainlerinde kişi sayısı korunur.
    F: gemi domainlerinde atanan geminin tipi adıyla geçer (ship verilirse).
    """
    failures = [msg for msg, _ in _simplified_checks(prompt, scenario, domain_id, ship)]
    return not failures, failures


def validate_high_action(scenario: dict) -> tuple[bool, list[str]]:
    """
    Aksiyon/Tehlike Yoğunluğu Kontrolü (Sakin/Statik Sahne Reddi).

    Kontroller:
      1. En az bir aktif tehlike/aksiyon kelimesi (collision, snap, flood, list,
         capsize, ...) var mı?
      2. Yoksa, sakin/rutin dile işaret eden anahtar kelimeler (driving, loading,
         waiting, routine, calm, ...) tespit edilip nedeni açıkça loglanır.
      3. Beat 1 (visible_start) durgun bir kurulum kalıbıyla mı başlıyor?
    """
    failures = []
    visible_start = scenario.get("visible_start", "")
    movement = scenario.get("physical_movement", "")
    consequence = scenario.get("visible_consequence", "")
    summary = scenario.get("scenario_summary", "")
    full_text = f"{visible_start} {movement} {consequence} {summary}".lower()

    matched_action = [kw for kw in _HIGH_ACTION_KEYWORDS if kw in full_text]
    matched_static = [kw for kw in _STATIC_KEYWORDS if kw in full_text]

    if not matched_action:
        if matched_static:
            failures.append(
                f"Sakin/rutin dil tespit edildi, dengeleyecek aksiyon kelimesi yok: {matched_static}"
            )
        else:
            failures.append(
                "Aktif tehlike/aksiyon anahtar kelimesi bulunamadı — sahne çok sakin/statik olabilir"
            )

    if not (_declared_beat1_verb_ok(scenario) or _beat1_action_words(visible_start)):
        failures.append("Beat 1'de aksiyon fiili yok, tehlike başlamamış")

    matched_static_start = _static_start_hits(visible_start.lower())
    if matched_static_start:
        failures.append(f"Beat 1 durgun kurulumla başlıyor: {matched_static_start}")

    is_valid = len(failures) == 0
    return is_valid, failures


def score_scenario(scenario: dict) -> int:
    """Kapıdan GEÇEN bir senaryonun aksiyon yoğunluğunu puanlar (LLM çağrısı yok, kod tabanlı).

    Girdi: scenario dict (visible_start, physical_movement, visible_consequence,
           scenario_summary alanlarını içeren GPT-4o çıktısı).
    Çıktı: int (negatif olabilir, üst sınır yok). Yüksek skor = daha güçlü/anlık aksiyon.
    """
    movement = scenario.get("physical_movement", "")
    consequence = scenario.get("visible_consequence", "")
    summary = scenario.get("scenario_summary", "")
    visible_start = scenario.get("visible_start", "")
    full_text = f"{movement} {consequence} {summary}".lower()
    vstart_low = visible_start.lower().strip()

    score = 0
    score += sum(1 for kw in _HIGH_ACTION_KEYWORDS if kw in full_text)

    if "already" in vstart_low:
        score += 3

    first_words = [w.strip(",.;:") for w in vstart_low.split()[:6]]
    if any(v in first_words for v in _STRONG_OPENING_VERBS):
        score += 2

    if "suddenly" in vstart_low:
        score += 1

    if _static_start_hits(vstart_low):
        score -= 5

    # Beat 3 hâlâ sürüyor (still/continues/keeps + hareketli fiil). Aksiyon
    # kelimeleri yukarıda full_text içinde zaten sayıldı, ayrıca puanlanmaz.
    if _beat3_ongoing_markers(consequence):
        score += 2

    return score


class NoValidScenarioError(RuntimeError):
    """5 senaryo denemesinin hiçbiri kalite kapısından geçemediğinde fırlatılır."""


async def generate_prompts(config: dict) -> dict:
    """
    Doğukan metodolojisinde tam otonom ve yaratıcı serbestlikli prompt pipeline'ı.
    """
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: Doğukan standardında DeepMyster mock promptları üretiliyor...")
        return _dry_run_output()

    used_combos = config.get("used_combos", [])
    recent_topics = config.get("recent_topics", [])
    combined_history = list(dict.fromkeys(used_combos + recent_topics))

    # ── ADIM 1 & 2: Kombinasyon Seçimi ve GPT-4o Senaryo Üretimi (5 deneme, skorla en iyisi) ──
    max_scenario_attempts = 5
    max_dedup_attempts = 50
    accepted = []   # kapıdan geçenler: {scenario, catalyst, camera_archetype, combo_key, score}
    attempt_log = []  # HİÇBİRİ geçmezse hata mesajında kullanılacak

    for attempt in range(max_scenario_attempts):
        # Geçerli bir catalyst bul (used_combos'ta olmayan)
        for _ in range(max_dedup_attempts):
            catalyst = get_creative_catalyst(recent_history=combined_history)
            camera_archetype = choose_camera_archetype(catalyst["domain_id"])
            combo_key = f"{catalyst['domain_id']}|{catalyst['forced_ship'].lower()}|{catalyst['forced_event'].lower()}|{catalyst['forced_environment'].lower()}|{camera_archetype}"
            if combo_key not in used_combos:
                break

        log.info(f"🧭 Denizcilik Alanı ({attempt+1}/{max_scenario_attempts}): [{catalyst['domain_id']}] {catalyst['domain_title']}")
        log.info(f"⚓ Seçilen Gemi: {catalyst['forced_ship']} | 🌊 Olay: {catalyst['forced_event']} | 🌍 Ortam: {catalyst['forced_environment']}")
        log.info(f"🎥 Kamera Arketipi: [{camera_archetype}]")

        raw_scenario = await _generate_scenario(catalyst, camera_archetype)
        is_visible, visibility_failures = validate_silent_visibility(raw_scenario)
        is_active, action_failures = validate_high_action(raw_scenario)
        is_ongoing, beat3_failures = validate_beat3_ongoing_danger(raw_scenario)
        is_cast_ok, cast_failures = validate_cast_size(raw_scenario, catalyst["domain_id"])
        is_consistent, consistency_failures = validate_scenario_consistency(raw_scenario)
        is_valid = is_visible and is_active and is_ongoing and is_cast_ok and is_consistent
        failures = visibility_failures + action_failures + beat3_failures + cast_failures + consistency_failures

        combined_history.append(combo_key)
        used_combos.append(combo_key)

        if is_valid:
            score = score_scenario(raw_scenario)
            accepted.append({
                "scenario": raw_scenario, "catalyst": catalyst,
                "camera_archetype": camera_archetype, "combo_key": combo_key,
                "score": score,
            })
            log.info(f"✅ Senaryo {attempt+1}/{max_scenario_attempts} kapıdan geçti (skor={score}): {raw_scenario.get('scenario_summary', '')}")
        else:
            attempt_log.append({"attempt": attempt + 1, "combo_key": combo_key, "failures": failures})
            log.warning(
                f"⚠️ Senaryo {attempt+1}/{max_scenario_attempts} reddedildi: {failures} "
                f"| Reddedilen senaryo: {raw_scenario.get('scenario_summary', '')}"
            )

    if not accepted:
        raise NoValidScenarioError(
            f"{max_scenario_attempts} senaryo denemesi kalite kapısından geçemedi. Bu tur video üretilmedi. "
            f"Denemeler: {json.dumps(attempt_log, ensure_ascii=False)}"
        )

    # ── ADIM 3: Seedance 2 Mini Doğukan Promptu (25–45 Kelime — DEFAULT_DURATION Standardı) ──
    # Skor sırasıyla sadeleştirilir; simplifier çıktı kapısından ilk geçen senaryo kullanılır.
    log.info(f"✂️ Sahne Doğukan standardına sadeleştiriliyor (25–45 kelime {settings.DEFAULT_DURATION}s)...")
    best, simplified, simplify_attempts = await simplify_with_gate(accepted)
    scenario, catalyst, camera_archetype, combo_key = (
        best["scenario"], best["catalyst"], best["camera_archetype"], best["combo_key"]
    )
    log.info(
        f"🏆 Senaryo seçildi (skor={best['score']}, {len(accepted)}/{max_scenario_attempts} kapıdan geçti, "
        f"{len(simplify_attempts)} simplifier denemesi): {scenario.get('scenario_summary', '')}"
    )
    raw_prompt_text = simplified.get("prompt", "").strip()
    raw_word_count = len(raw_prompt_text.split())

    # ── Cerrahi Safety Sanitizer — SADECE GPT'nin özgür metnine uygulanır ──
    # Stil kilidi (STYLE_LOCK_SUFFIX) bizim elle yazdığımız, önceden denetlenmiş
    # sabit metindir; sanitizer'dan SONRA eklenir ki regex kuralları (örn. "cgi"
    # kelimesi) kilidin kendi dilini ("CGI-clean" gibi) yanlışlıkla bozmasın.
    from core.prompt_sanitizer import sanitize_prompt
    sanitized_raw, changes = sanitize_prompt(raw_prompt_text)
    if changes:
        raw_prompt_text = sanitized_raw
        log.info(f"   🛡️ Prompt sanitize edildi: {len(changes)} değişiklik")

    # ── Sabit Stil Kilidi — GPT ne yazarsa yazsın değişmez şekilde, sanitizer'dan SONRA eklenir ──
    prompt_text = apply_style_lock(raw_prompt_text, camera_archetype, catalyst)
    word_count = len(prompt_text.split())

    log.info(
        f"   → GPT prompt [{raw_word_count} kelime, Doğukan hedefi 25-45] + stil kilidi "
        f"→ Kie'ye giden nihai prompt [{word_count} kelime]: {prompt_text}"
    )

    simplified_scenes = [{
        "scene_number": 1,
        "prompt": prompt_text,
        "duration": settings.DEFAULT_DURATION,
    }]

    # ── ADIM 4: YouTube Metadata (Merak Odaklı, No-Spoiler) ──
    log.info("📺 YouTube metadata üretiliyor...")
    metadata = await _generate_metadata(scenario, catalyst)

    # ── Sonuç Birleştir ──
    clean_title = clean_youtube_title(metadata.get("youtube_title", "Massive Ocean Swell Hits Vessel Deck #Shorts"))
    vessel = scenario.get("vessel_class", catalyst['forced_ship'])
    incident = scenario.get("incident_type", catalyst['forced_event'])
    # combo_key zaten yukarıda belirlenmişti

    result = {
        "scenes": simplified_scenes,
        "youtube_title": clean_title,
        "youtube_description": metadata.get("youtube_description", ""),
        "tags": metadata.get("tags", ["DeepMyster", "Shorts", "Maritime", "CCTV", "CruiseShip", "Ferry", "RoughSeas"]),
        "scenario_summary": scenario.get("scenario_summary", ""),
        "combo_key": combo_key,
        "total_duration": settings.DEFAULT_DURATION,
        "animal": vessel,
        "talent": incident,
        "category": catalyst["domain_id"],
    }

    log.info(f"✅ DeepMyster Pipeline hazır: \"{result['youtube_title']}\" ({settings.DEFAULT_DURATION}s tek kesintisiz çekim)")
    return result


async def _generate_scenario(catalyst: dict, camera_archetype: str) -> dict:
    """Katman 2: GPT-4o'ya yaratıcı yönetmenlik rolü vererek özgün denizcilik senaryosu ürettir."""
    duration = settings.DEFAULT_DURATION
    early, late = compute_duration_breakpoints(duration)
    sys_prompt = build_scenario_writer_system(duration, catalyst.get("domain_id", ""))
    history_text = "\n".join(f"- {h}" for h in catalyst.get("recent_history", [])[-15:]) if catalyst.get("recent_history") else "None (First run)"
    library_text = "\n".join(f"🔸 {s}" for s in catalyst.get("existing_library_reference", [])) if catalyst.get("existing_library_reference") else ""
    archetype = CAMERA_ARCHETYPES.get(camera_archetype, CAMERA_ARCHETYPES["fixed_cctv"])

    # Domain'in "camera_styles" örnekleri hep sabit CCTV tonunda — atanan arketip
    # CCTV değilse çelişki yaratmaması için bu satırı atlıyoruz.
    camera_styles_line = (
        f"RECOMMENDED CAMERA STYLES: {', '.join(catalyst['camera_styles'])}\n"
        if camera_archetype == "fixed_cctv" else ""
    )

    # chase_pov testte tek-tekne fırtına sahnesine düşüyordu — bu kural olmadan
    # GPT "kovalama" kavramını göz ardı edip sadece kendi teknesini anlatıyordu.
    chase_pov_directive = (
        "\n8. MANDATORY FOR CHASE POV: Include TWO distinct vessels — the "
        "observer vessel the camera films from, and a second, clearly separate "
        "vessel actively in crisis that remains visible throughout the shot. "
        "This is NOT a single-vessel storm scene. If a natural two-vessel setup "
        "doesn't fit this domain, pick a different incident within the same "
        "domain rather than defaulting to a single vessel."
        if camera_archetype == "chase_pov" else ""
    )

    user_message = f"""You are directing a new {duration}-second continuous raw documentary scene for DeepMyster.

MANDATORY ASSIGNMENT: You MUST base your scenario exactly on this combination:
- Vessel Type: {catalyst['forced_ship']}
- Event/Incident: {catalyst['forced_event']}
- Environment: {catalyst['forced_environment']}
Do not deviate from these core elements.

CAMERA PERSPECTIVE FOR THIS SCENE (MANDATORY): {archetype['gpt_guidance']}

EXPLORATION DOMAIN: {catalyst['domain_title']}
DOMAIN INSPIRATION & GUIDANCE: {catalyst['guidance']}
EXAMPLE ELEMENTS FOR INSPIRATION: {', '.join(catalyst['example_elements'])}
{camera_styles_line}
DEEPMYSTER BRAND UNIVERSE & EXISTING REFERENCE SAMPLES (FOR INSPIRATION & TONE):
{library_text}

RECENT PRODUCTION HISTORY (DO NOT REPEAT THESE RECENT CONCEPTS):
{history_text}

CREATIVE DIRECTIVE:
1. Use the brand library samples above to understand our tone, but DO NOT copy or mechanically re-skin them.
2. Use EXACTLY the assigned Vessel Type above. DeepMyster's vessel universe is limited to: {', '.join(VESSEL_UNIVERSE)}. If the Vessel Type is 'None', show no vessel at all. The physical crisis must be within or inspired by the '{catalyst['domain_title']}' domain.
3. The crisis must be completely visible and intuitive on a silent screen within 2-3 seconds.
4. Structure the {duration}-second single continuous take: visible start (0-{early}s) -> physical escalation & contextual crew/mechanical response ({early}-{late}s) -> concrete physical state change at {duration}s.
5. Keep human presence natural and context-appropriate (or pure raw industrial physics). No cartoonish shoehorned actions.
6. The scene must show CONSTANT HIGH ACTION — something actively breaking, colliding, flooding, swinging, or in danger in real time. Never calm, static, or purely observational.
7. Dress crew/staff in authentic high-visibility orange, red, or yellow PPE, wetsuits, or coveralls — never white hazmat/astronaut suits, even in arctic/polar settings (use red or orange polar immersion suits instead). Dress passengers, boat owners, guests, and vehicle drivers/occupants in ordinary civilian clothing appropriate to the setting (swimwear/resort wear for pool/deck scenes, casual clothing for car-deck scenes, yacht-casual for marina scenes) — never hi-vis PPE on civilians. Depict raw, natural weather and lighting — never glossy, CGI-clean, or cinematic, Hollywood-polished.{chase_pov_directive}"""

    system_prompt = build_scenario_writer_system(duration, catalyst.get("domain_id", ""))
    result = await _call_gpt(system_prompt, user_message, temperature=0.85)

    # Savunma katmanı: GPT alan içine "BEAT 1:" gibi etiket sızdırırsa temizle
    for field in ("visible_start", "physical_movement", "visible_consequence"):
        if isinstance(result.get(field), str):
            result[field] = _BEAT_LABEL_RE.sub("", result[field]).strip()

    # Geriye dönük uyumluluk alanları
    if "scene_description" not in result:
        result["scene_description"] = (
            f"From {result.get('observer_camera', 'fixed CCTV')}, {result.get('visible_start', '')} "
            f"leads to {result.get('physical_movement', '')}, finally {result.get('visible_consequence', '')}."
        )

    return result


async def _simplify_prompt(scenario: dict, catalyst: dict, feedback: list[str] | None = None) -> dict:
    """Katman 3: Senaryoyu Seedance 2 Mini için 25–45 kelimelik yüksek sinyalli prompt'a çevir.

    feedback: önceki denemenin çıktı kapısında kaldığı noktalar (İngilizce düzeltme talimatları).
    GPT boş dönerse {"prompt": ""} döner; yedek prompt yok, kapı bunu başarısız deneme sayar.
    """
    duration = settings.DEFAULT_DURATION
    early, late = compute_duration_breakpoints(duration)
    user_message = f"""Convert this realistic maritime incident into an exact 25–45 word Seedance 2 Mini prompt following the Doğukan methodology:

VESSEL CLASS: {scenario.get('vessel_class', 'Vessel')}
INCIDENT: {scenario.get('incident_type', 'Physical Emergency')}
SUMMARY: {scenario.get('scenario_summary', '')}
VISIBLE START (0-{early}s): {scenario.get('visible_start', '')}
PHYSICAL MOVEMENT ({early}-{late}s): {scenario.get('physical_movement', '')}
FINAL OUTCOME ({duration}s): {scenario.get('visible_consequence', '')}

REQUIREMENTS:
- Exactly 25 to 45 words.
- Single unbroken {duration}-second continuous shot.
- STRICT CHRONOLOGICAL FLOW: Start -> STRONG VISIBLE PHYSICAL MOVEMENT -> Final Outcome.
- STRONG VISIBLE ACTION: You MUST include at least one aggressive, highly visible physical action (e.g. swings, veers, slams, pitches, slides). Passive verbs (like 'approaches') are NOT enough.
- STRICT INVENTORY: Do NOT add new elements, people, vessels, or objects not explicitly detailed above. 
- Do NOT include any camera, POV, lighting, or shot-type description (e.g., no "From the escort boat", no "CCTV", no "lens").
- Preserve PPE colors and raw weather details from the scenario exactly — never white hazmat suits, never glossy/CGI-clean water or ice."""

    if feedback:
        user_message += "\n\nYOUR PREVIOUS ATTEMPT WAS REJECTED. Fix these points:\n" + "\n".join(
            f"- {f}" for f in feedback
        )

    system_prompt = build_prompt_simplifier_system(duration, catalyst.get("domain_id", ""))
    result = await _call_gpt(system_prompt, user_message, temperature=0.75)

    # Eski yedek prompt kaldırıldı (2026-09-24): env-centric'te "On a rolling None in rough
    # seas" üretiyor, varsayılanı Beat 3 kara listesindeki "settling" idi.
    if not result.get("prompt"):
        result = {**result, "prompt": ""}
    return result


SIMPLIFIER_MAX_RETRIES = 2


async def simplify_with_gate(candidates: list[dict]) -> tuple[dict, dict, list[dict]]:
    """Kabul edilmiş senaryoları skor sırasıyla sadeleştirir; çıktı kapısından ilk geçeni döndürür.

    Her senaryo için 1 + SIMPLIFIER_MAX_RETRIES deneme (retry'da GPT'ye neden kaldığı söylenir),
    sonra sıradaki senaryo. Hiçbiri geçmezse NoValidScenarioError (sessiz fallback yok).
    candidates: {"scenario", "catalyst", "score", ...} sözlükleri.
    Dönüş: (seçilen aday, simplifier sonucu, deneme kaydı).
    """
    attempts = []
    for cand in sorted(candidates, key=lambda c: c["score"], reverse=True):
        scenario, catalyst = cand["scenario"], cand["catalyst"]
        feedback = None
        for attempt in range(1 + SIMPLIFIER_MAX_RETRIES):
            simplified = await _simplify_prompt(scenario, catalyst, feedback)
            issues = _simplified_checks(simplified.get("prompt", ""), scenario, catalyst.get("domain_id", ""),
                                        catalyst.get("forced_ship") or "")
            attempts.append({
                "summary": scenario.get("scenario_summary", ""), "attempt": attempt + 1,
                "prompt": simplified.get("prompt", ""), "failures": [m for m, _ in issues],
            })
            if not issues:
                return cand, simplified, attempts
            log.warning(f"⚠️ Simplifier çıktısı kapıdan geçmedi (deneme {attempt + 1}): {[m for m, _ in issues]}")
            feedback = [hint for _, hint in issues]
    raise NoValidScenarioError(
        f"Hiçbir senaryonun simplifier çıktısı kapıdan geçmedi. "
        f"Denemeler: {json.dumps(attempts, ensure_ascii=False)}"
    )


async def _generate_metadata(scenario: dict, catalyst: dict) -> dict:
    """YouTube title, description, tags üret — merak odaklı ve no-spoiler."""
    user_message = f"""Create YouTube Shorts metadata for this maritime incident (NO SPOILERS IN TITLE):

VESSEL: {scenario.get('vessel_class', 'Vessel')}
INCIDENT: {scenario.get('incident_type', 'Emergency')}
SCENARIO SUMMARY: {scenario.get('scenario_summary', '')}
DOMAIN: {catalyst.get('domain_title', 'Maritime Operations')}

STRICT RULE: The title MUST highlight the immediate physical crisis and danger, NEVER revealing the ending or resolution! Max 55 characters."""

    result = await _call_gpt(YOUTUBE_METADATA_SYSTEM, user_message, temperature=0.8)

    raw_title = result.get("youtube_title", "")
    result["youtube_title"] = clean_youtube_title(raw_title)

    tags = result.get("tags", [])
    mandatory_tags = ["DeepMyster", "Shorts", "Maritime", "CCTV", "Ocean", "RoughSeas"]
    for tag in mandatory_tags:
        if tag not in tags:
            tags.append(tag)
    result["tags"] = tags

    return result


def _dry_run_output() -> dict:
    """DRY-RUN modunda 25-45 kelimelik 12s DeepMyster standardı mock çıktısı."""
    return {
        "scenes": [
            {
                "scene_number": 1,
                "prompt": "A heavy wash surges over the stern ramp of a passenger car ferry, flooding the open vehicle deck as two deckhands in orange hi-vis coveralls grab the railing. Seawater keeps sweeping between the parked cars. Fixed car deck CCTV camera, raw overcast daylight.",
                "duration": settings.DEFAULT_DURATION,
            }
        ],
        "youtube_title": "⚠️ Storm Wash Floods Ferry Car Deck #Shorts",
        "youtube_description": "Car deck CCTV captures a storm wash flooding the open vehicle deck of a passenger car ferry. #DeepMyster #Shorts #Maritime #CCTV #RoughSeas",
        "tags": ["DeepMyster", "Shorts", "Maritime", "CCTV", "Ferry", "CarDeck", "RoughSeas", "Ocean"],
        "scenario_summary": "A storm wash floods the open vehicle deck of a passenger car ferry and keeps sweeping between the parked cars.",
        "combo_key": "ferry_operations|passenger car ferry|water flooding open vehicle deck|open vehicle deck|fixed_cctv",
        "total_duration": settings.DEFAULT_DURATION,
        "animal": "Passenger Car Ferry",
        "talent": "Water flooding open vehicle deck",
        "category": "ferry_operations",
    }
