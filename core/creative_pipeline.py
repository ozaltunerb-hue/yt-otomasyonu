"""
Creative hattı (TUR 31): GPT-4o hikâyeyi kendisi yazar, iskelet yok.

İskelet hattı aynı olayda neredeyse birebir aynı prompt'u üretiyordu (kruvaziyer dev dalga iki kez seçildi,
iki prompt aynıydı). Bu hatta Python olay/gemi (LRU), yer ve havayı (iskelet listelerinden rastgele) seçer;
GPT-4o kısa bir sistem prompt'uyla 40-60 kelimelik hikâyeyi yazar. Kurallar sadece: 40-60 kelime, 3 beat
(tetik, hareket, hâlâ süren sonuç), görünür tetik, son cümle hareketle biter. Sert kontrol iki tane: olay
uyuşması ve kelime sayısı; kalırsa 1 kez geri bildirimle yeniden istenir. Tekrar önleme: son 15 hikâye
"bunlardan farklı yaz" diye verilir. Kamera satırı ve stil eki iskelet hattıyla birebir aynıdır.
"""
from __future__ import annotations

import json
import logging
import random
import re

from core.prompt_generator import NoValidScenarioError
from core.skeleton_pipeline import (
    EVENT_SKELETONS,
    SKELETON_CAMERA,
    SHIP_PHRASES,
    choose_event_and_ship,
    count_range,
    style_suffix,
)

log = logging.getLogger("CreativeEngine")

MIN_WORDS, MAX_WORDS = 40, 60
RECENT_STORIES = 15

CREATIVE_SYSTEM = """You write one short scene for a 15-second realistic video of a real incident.
Input: event, vessel, place, weather, visible people, outcome to reach.

Rules:
1. 40 to 60 words.
2. Three beats: the trigger happens; the movement it causes; the result, still unfolding, reaching the given outcome. The first sentence shows the moment the trigger happens (the wave clears the rail, the cable snaps, the wall of water enters the street); never open with waiting, tension or buildup; describe the scene, never the camera or the video. Show only what is visible, never sounds.
3. The trigger is clearly visible on camera.
4. The last sentence shows the danger still visibly moving at the very end.
5. Catastrophic in scale: violent, high-volume water or force dominating the frame; never mild or harmless images (ankle-deep, floats, honking futilely).
Name any given vessel by its type. Make it different from the recent stories.
Return JSON only: {"story": "..."}"""

# 3. beat'in ulaşacağı sonuç (TUR 31, veri; kural değil): GPT hikâyeyi kendisi yazar, son beat bu sonuca varır.
EVENT_OUTCOMES = {
    # Feribot
    "Lashing chain snaps and a parked car breaks loose":
        "the loose car slams into the next row and keeps sliding across the deck with every roll",
    "Loading ramp hinge snaps and the ramp drops":
        "the steel ramp crashes onto the quay and keeps twisting as the ferry surges against its lines",
    "Green wave breaks over the rail onto the vehicle deck":
        "seawater pours across the vehicle deck and shoves parked cars sideways into each other",
    # Tersane
    # Yat kızakta ileri gitmez: olduğu yerde yana yatar, sonra yan tarafıyla suya devrilir (altın video).
    # İleri kayma yazılınca model yatı suya kafadan sokuyordu.
    "Restraining cable snaps during slipway launch":
        "the yacht heels over onto its side in place, then topples sideways into the water beside it with a "
        "huge splash and keeps rolling hard from side to side",
    "Keel blocks collapse under the launching hull":
        "the yacht heels over onto its side in place, then topples sideways into the water beside it with a "
        "huge splash and keeps rolling hard from side to side",
    "Drydock flood gate bursts open":
        "a wall of seawater lifts the hull off its blocks and swings it against the dock wall",
    "Timber shores snap and the hull tips on its keel blocks":
        "the hull topples sideways off its keel blocks, snapping the remaining shores",
    "Crane sling snaps while lowering the hull into the water":
        "the hull plunges nose-first into the basin, throwing up a wall of spray while still swinging on the last sling",
    # Marina
    # ÇIKARILDI (1 Eki, Bahadır): marina_yat_3 ve halat_kopar videolarında halat kopması görünmedi (bkz. skeleton_pipeline)
    # "Mooring line snaps in a storm gust":
    #     "the mooring line snaps and whips across the dock, the yacht swings free and slams its hull into the "
    #     "neighboring moored yacht again and again",
    "Storm surge wave lifts and buckles the floating pontoon":
        "the pontoon buckles and tilts, throwing the moored boat against it as more waves roll in",
    "Passing boat's wake slams the boat sideways":
        "the boat heels hard and keeps slamming against the dock as the wake rolls through",
    # ÇIKARILDI (1 Eki, Bahadır): kontrolsüz yat videosunda çarpma yok (bkz. skeleton_pipeline)
    # # EKLENDİ (1 Eki, Bahadır; TASLAK)
    # "Yacht loses control and rams moored boats in the marina":
    #     "the yacht races into the marina out of control, plows into the moored boats along the dock and shoves them "
    #     "aside while people jump back",
    # Kruvaziyer
    "Mooring line snaps and whips across the quay":
        "the snapped line keeps thrashing across the quay while the towering hull swings away from the berth",
    "Gangway tears loose as the hull surges":
        "the gangway tears free at one end and swings against the hull as the ship keeps surging",
    "Rogue wave breaks over the rail onto the pool deck":
        "waves keep sweeping loungers and people across the pool deck",
    # Kıyı hortumu
    "Tornado approaching coastline":
        "the tornado reaches the shore, ripping sand, water and debris high into the air",
    "Tornado making landfall":
        "the tornado tears roofs and signs away and hurls debris across the street",
    "Tornado rain bands and flying debris lash the waterfront":
        "sheets of rain and flying debris batter the waterfront, smashing railings and signs",
    # Şehir
    "Flash flooding in city streets":
        "a wall of brown floodwater surges down the street, slams into parked cars and shoves them sideways "
        "as people run for higher ground",
    # ÇIKARILDI (30 Eyl, Bahadır): aksiyonsuz videolar veriyordu (bkz. skeleton_pipeline)
    # "Storm gust tears signs and scaffolding loose downtown":
    #     "scaffolding and signs crash onto the street and parked cars as more panels tear loose",
    # EKLENDİ (30 Eyl, Bahadır onayı). Kaynak: 24 Eyl videosu (dosya 1790240764259-vf8owrlvyva)
    "Tidal wave surges over a coastal city street":
        "a towering tidal wave crashes over the coastal road, sweeps parked cars into storefronts and keeps surging "
        "down the street",
    # Plaj
    "Tornado approaching an open beach":
        "the tornado reaches the sand, hurling umbrellas, chairs and sand high into the air",
    "Storm gust rips umbrellas and beach chairs into the air":
        "dozens of umbrellas and chairs cartwheel across the sand and into the air",
    "Large waves reaching the beach":
        "huge waves surge far up the beach, sweeping chairs and towels inland toward the promenade",
}
if set(EVENT_OUTCOMES) != set(EVENT_SKELETONS):
    raise RuntimeError(f"EVENT_OUTCOMES iskelet olaylarıyla uyuşmuyor: {set(EVENT_OUTCOMES) ^ set(EVENT_SKELETONS)}")


# ── HİKÂYE KURAL KAPISI (30 Eyl) ────────────────────────────────────────────────────────────────────────────
# Sistem prompt'una dokunulmaz; bu kurallar sadece kodda denetlenir, kalan hikâye GPT'ye kısa geri bildirimle
# yeniden yazdırılır. 3 denemede de geçmezse Kie'ye gidilmez. KİLİTLİ: aşağıdaki listeleri gevşetmek ya da
# kaldırmak için Bahadır'ın açık onayı gerekir; tests/test_story_rule_gate.py tam içeriği denetler.
# Bütçe: sabit kural en fazla 6, olay başına anahtar grup en fazla 3, yasak liste sadece iki kızak olayında.

MAX_ATTEMPTS = 3
SLIPWAY_EVENTS = ("Restraining cable snaps during slipway launch", "Keel blocks collapse under the launching hull")

# Sabit kurallar (22 olayın hepsinde). kural → Telegram'da görünen unsur adı.
STORY_RULES = {
    # Sebep: açılış bekleyiş/gerilimle başlayınca tetik 15 sn'ye sığmıyor. Kaynak: final turu hazırlığı
    # (30 Eyl, eb3a9f2), sistem prompt'u 2. kuralın kodda denetimi.
    "a_trigger_first": "ilk cümlede tetik",
    # Sebep: model elde tutulan telefonu ve kayıt (REC) ekranını çizdi. Kaynak: final turu öncesi Kie
    # videoları (30 Eyl, eb3a9f2 notu).
    "b_no_camera_words": "kamera/video/telefon kelimesi olmaması",
    # Sebep: "as the video ends", "tension builds" gibi cümlelerin görüntüde karşılığı yok, boş saniye üretir.
    # Kaynak: final turu hazırlığı (30 Eyl, eb3a9f2), sistem prompt'u 2. kuralın kodda denetimi.
    "c_no_meta_or_waiting": "meta/bekleyiş ifadesi olmaması",
    # Sebep: "ankle-deep floods", "honking futilely", "debris floats" olayı zararsız gösterdi. Kaynak: TUR 31
    # creative kanıt koşusu, şehir sel hikâyesi (30 Eyl, GPT çıktısı; video değil).
    "d_no_scale_reducers": "ölçek küçültücü ifade olmaması",
    # Sebep: menü olayı hikâyede yoksa Kie başka bir olay çizer; gemi adı yoksa başka tekne çizer. Kaynak: TUR 29
    # zorunlu olay denetimi ve TUR 8 gemi adı kapısı.
    "e_event_and_ship_named": "olay adı ve gemi türü",
    # Sebep: stil ekindeki "phone" elde tutulan telefonu çizdirdi. Kaynak: final turu öncesi Kie videoları
    # (30 Eyl, eb3a9f2; zaten testli, korunur).
    "f_no_phone_in_style": "stil ekinde 'phone' olmaması",
}

# b: kamera/kayıt kelimeleri (hikâyede; stil eki ayrı kuraldır)
CAMERA_WORDS = ("camera", "video", "phone", "footage")
# c: meta anlatım ve bekleyiş
META_PHRASES = ("as the video ends", "as the clip ends", "the scene ends", "tension builds", "tension mounts",
                "suspense", "anticipation", "about to", "moments before", "calm before", "holds its breath",
                "waiting", "waits")
# d: ölçek küçültücüler (sistem prompt'u 5. kuraldaki örneklerle uyumlu)
SCALE_REDUCERS = ("ankle-deep", "ripple", "harmless", "harmlessly", "gentle", "gently", "mild", "mildly",
                  "trickle", "puddle", "drizzle", "floats", "futilely")
# e: gemi türü (VESSEL satırındaki ad). Hikâyede bu kelimelerden biri geçmeli.
SHIP_TYPE_WORDS = {
    "Passenger Car Ferry": ("ferry",),
    "High-speed Catamaran": ("catamaran",),
    "Luxury Motor Yacht": ("yacht",),
    "Sailing Yacht": ("yacht",),
    "Runaway Powerboat": ("powerboat", "power boat"),
    "Ocean Cruise Liner": ("cruise liner", "cruise ship", "liner"),
    "Mega Cruise Ship": ("cruise ship", "cruise liner"),
}
# a: olay adındaki yer/bağlam kökleri tetik sayılmaz ("pool deck", "city streets" tetik değil)
_SETTING_STEMS = {"park", "deck", "rail", "vehi", "gree", "laun", "hull", "open", "wate", "lowe", "stor", "pass",
                  "side", "boat", "acro", "quay", "coas", "appr", "city", "stre", "down", "beac", "larg", "floa",
                  "dryd", "load", "pool", "slip"}

# Olay başına 1-3 anahtar grup: her gruptan en az bir kelime/kök hikâyede geçmeli. Kelimeler çekimleriyle
# eşleşir (surge → surges, surging; car → cars). Onaylı: iki kızak, şehir sel, kruvaziyer dev dalga.
# TASLAK: diğer 18 olay EVENT_OUTCOMES'tan türetildi, Bahadır kontrol edecek; henüz testle kilitli değil.
EVENT_REQUIRED = {
    # ── Feribot (TASLAK) ──
    "Lashing chain snaps and a parked car breaks loose": [("car", "vehicle"), ("slide", "slid", "skid", "slam")],
    "Loading ramp hinge snaps and the ramp drops": [("ramp",), ("crash", "slam", "drop", "fall", "fell")],
    "Green wave breaks over the rail onto the vehicle deck": [("wave", "seawater", "water"), ("car", "vehicle")],
    # ── Tersane ──
    # ONAYLI. Sebep: yat kızaktan kayıp suya kafadan girdi (30 Eyl tersane videosu); istenen görüntü 12 Eyl
    # altın videosu: yerinde yana yatış, yan tarafıyla suya düşüş.
    # "to one side": Bahadır onayı, 30 Eyl; "tilting to one side" yazan doğru omurga hikâyesi reddediliyordu
    # (hedefli kuru prova). İleri kaymayı yasak liste engelliyor.
    "Restraining cable snaps during slipway launch": [("sideways", "on its side", "onto its side", "to one side")],
    "Keel blocks collapse under the launching hull": [("sideways", "on its side", "onto its side", "to one side")],
    # TASLAK
    "Drydock flood gate bursts open": [("seawater", "water", "torrent"), ("lift", "float", "swing")],
    "Timber shores snap and the hull tips on its keel blocks": [("topple", "tip", "sideways", "on its side",
                                                                 "onto its side")],
    "Crane sling snaps while lowering the hull into the water": [("plunge", "drop", "fall", "fell", "crash"),
                                                                 ("spray", "splash")],
    # ── Marina (TASLAK) ──
    # ÇIKARILDI (1 Eki, Bahadır): marina_yat_3 ve halat_kopar videolarında halat kopması görünmedi
    # "Mooring line snaps in a storm gust": [("snap", "parts", "parted", "break", "broke"),
    #                                        ("neighboring yacht", "neighboring moored yacht", "neighbouring yacht",
    #                                         "next yacht", "adjacent yacht", "neighboring boat"),
    #                                        ("slam", "crash", "ram", "smash", "bang")],
    "Storm surge wave lifts and buckles the floating pontoon": [("pontoon",), ("buckle", "tilt", "twist", "heave")],
    "Passing boat's wake slams the boat sideways": [("wake",), ("heel", "slam", "rock", "roll")],
    # ÇIKARILDI (1 Eki, Bahadır): kontrolsüz yat videosunda çarpma yok
    # # TASLAK (1 Eki). Sebep: yat bağlı teknelere çarpmalı; çarpma fiili ve somut hedef (bağlı tekne) görünmezse
    # # model yatı düzgün seyreder çizer (halat olayının 1 Eki videolarındaki hata).
    # "Yacht loses control and rams moored boats in the marina": [("plow", "ram", "slam", "crash", "smash"),
    #                                                             ("moored boat", "moored yacht", "moored boats",
    #                                                              "docked boat", "docked yachts")],
    # ── Kruvaziyer ──
    # TASLAK
    "Mooring line snaps and whips across the quay": [("line", "rope", "hawser", "cable"), ("whip", "thrash", "lash")],
    "Gangway tears loose as the hull surges": [("gangway",), ("tear", "tore", "swing", "rip", "break", "collapse")],
    # ONAYLI. Sebep: dalga güverteye inip şezlong ve insanları sürüklemeli. Kaynak: TUR 24 kruvaziyer Kie
    # videosu (kabul edildi) ve Bahadır'ın tanımı.
    "Rogue wave breaks over the rail onto the pool deck": [("wave",), ("loungers", "chairs", "people", "passengers")],
    # ── Kıyı hortumu (TASLAK) ──
    "Tornado approaching coastline": [("tornado", "twister", "funnel"), ("shore", "coast", "beach", "waterfront"),
                                      ("debris", "sand", "spray")],
    "Tornado making landfall": [("tornado", "twister", "funnel"), ("roof", "sign", "debris")],
    "Tornado rain bands and flying debris lash the waterfront": [("tornado", "twister", "funnel"), ("rain",),
                                                                 ("debris",)],
    # ── Şehir ──
    # ONAYLI. Sebep: su yerinde yükselmez, sokaktan gelen bir duvar olur ve arabaları sürükler. Kaynak: final turu
    # "hareketli sel" (30 Eyl, eb3a9f2) ve Bahadır'ın tanımı.
    "Flash flooding in city streets": [("wall", "surge", "torrent", "wave", "rush"), ("car", "cars", "vehicle")],
    # ÇIKARILDI (30 Eyl, Bahadır): aksiyonsuz videolar veriyordu
    # "Storm gust tears signs and scaffolding loose downtown": [("sign", "scaffold"),
    #                                                          ("crash", "fall", "fell", "topple", "tear", "rip")],
    # ONAYLI. Sebep: dalga kıyı yoluna çarpıp arabaları sürüklemeli. Kaynak: Bahadır'ın beğendiği 24 Eyl videosu
    # (dosya 1790240764259-vf8owrlvyva) ve Bahadır'ın tanımı (30 Eyl).
    "Tidal wave surges over a coastal city street": [("wave", "surge", "torrent"), ("car", "cars", "vehicle")],
    # ── Plaj (TASLAK) ──
    "Tornado approaching an open beach": [("tornado", "twister", "funnel"), ("umbrella", "chair", "sand")],
    "Storm gust rips umbrellas and beach chairs into the air": [("umbrella", "chair"),
                                                                ("air", "cartwheel", "tumble", "fly", "flies")],
    "Large waves reaching the beach": [("wave", "surf", "breaker"), ("chair", "towel", "umbrella", "people")],
}
REQUIRED_APPROVED = SLIPWAY_EVENTS + ("Flash flooding in city streets", "Rogue wave breaks over the rail onto the pool deck",
                                      "Tidal wave surges over a coastal city street")

# Sadece iki kızak olayı. Sebep: GPT 2. beat'te yatı kızaktan ileri kaydırdı (30 Eyl kızak halatı hikâyeleri),
# model de yatı suya kafadan soktu (30 Eyl tersane videosu).
EVENT_FORBIDDEN = {
    e: ("slides down", "sliding", "slides", "lurch", "lurches", "surges forward", "hurtle", "hurtles",
        "races down", "plunges", "plunging", "dives", "nose", "bow-first",
        # Bahadır onayı, 30 Eyl: kuru provada geçen hikâyelerde "careening down the slipway", "plummeting into
        # the water" vardı. "dive/diving" bilerek yok (işçiler "diving to safety" yazılabilir).
        "careen", "careens", "careening", "plummet", "plummets", "plummeting", "slide", "slid",
        # Bahadır onayı, 30 Eyl; kızak halatı hikâyesi 'begins its descent down the slipway... accelerates
        # uncontrollably' ile kapıdan geçti. Çekimleriyle eşleşir (descends, descending, accelerates...).
        "down the slipway", "descent", "descend", "accelerate")
    for e in SLIPWAY_EVENTS
}
FORBIDDEN_FEEDBACK_TR = "yat ileri gitmez; olduğu yerde yana yatar, sonra yan tarafıyla suya düşer."
FORBIDDEN_FEEDBACK_EN = ("The yacht does not move forward: it heels over onto its side where it stands, then falls "
                         "into the water on its side.")

# ÇEŞİTLİLİK KAPISI (6 sabit kurala sayılmaz, ayrı kategori). Sebep: hedefli kuru provada "Hortum kıyıya
# yaklaşıyor" iki kez birebir aynı hikâyeyi verdi (Jaccard 1.0), tekrar önleme listesine rağmen. Bahadır onayı,
# 30 Eyl. KİLİTLİ: eşik onaysız gevşetilmez. Deneme sayılır (3 deneme sınırı aynı).
DIVERSITY_THRESHOLD = 0.6
DIVERSITY_FEEDBACK_TR = "Bu hikâye son hikâyelere çok benziyor: farklı sahne, farklı ilk cümle yaz."
DIVERSITY_FEEDBACK_EN = "This story is too similar to the recent stories: write a different scene and a different first sentence."


def jaccard(a: str, b: str) -> float:
    """Kelime kümesi Jaccard benzerliği (eski örtüşme ölçümü), 1 = aynı."""
    A, B = set(re.findall(r"[a-z]+", (a or "").lower())), set(re.findall(r"[a-z]+", (b or "").lower()))
    return len(A & B) / len(A | B) if A | B else 0.0


def diversity_issues(story: str, recent: list[str]) -> list[dict]:
    """Son hikâyelerden biriyle Jaccard >= eşik ise tek sorun döner. Boş liste = yeterince farklı."""
    top = max((jaccard(story, r) for r in recent), default=0.0)
    if top >= DIVERSITY_THRESHOLD:
        return [{"rule": "diversity", "missing": f"çeşitlilik (benzerlik {top:.2f}): {DIVERSITY_FEEDBACK_TR}",
                 "feedback": DIVERSITY_FEEDBACK_EN}]
    return []

for _e in set(EVENT_REQUIRED) ^ set(EVENT_OUTCOMES):
    raise RuntimeError(f"EVENT_REQUIRED olaylarla uyuşmuyor: {_e}")


def _term_re(term: str) -> str:
    """Kelime/kök deseni: son kelime çekimleriyle (s, es, d, ed, ing, ies, ikizleşen ünsüz, e düşmesi)."""
    head, _, last = term.lower().rpartition(" ")
    forms = {last, last + "s", last + "es", last + "d", last + "ed", last + "ing"}
    if last.endswith("e"):
        forms.add(last[:-1] + "ing")
    if last.endswith("y"):
        forms |= {last[:-1] + "ies", last[:-1] + "ied"}
    if re.fullmatch(r".*[^aeiou][aeiou][bdgmnprt]", last):
        forms |= {last + last[-1] + "ed", last + last[-1] + "ing"}
    words = "|".join(sorted((re.escape(f) for f in forms), key=len, reverse=True))
    prefix = (re.escape(head) + r"\s+") if head else ""
    return rf"\b{prefix}(?:{words})\b"


def find_terms(terms, text: str) -> list[str]:
    """Metinde geçen terimler (çekimleriyle)."""
    low = (text or "").lower()
    return [t for t in terms if re.search(_term_re(t), low)]


def _first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s+", (text or "").strip(), maxsplit=1)[0]


def trigger_stems(event: str) -> set[str]:
    """Olay adının tetik kökleri: olay kökleri eksi yer/bağlam kökleri."""
    from core.prompt_generator import _event_stems
    return _event_stems(event) - _SETTING_STEMS


def story_rule_issues(event: str, ship: str | None, story: str, suffix: str | None = None) -> list[dict]:
    """Kural kapısı. Her sorun: {"rule", "missing" (Telegram, Türkçe), "feedback" (GPT, İngilizce)}.
    Boş liste = geçti. 40-60 kelime biçim kontrolü de burada (önceden vardı, 6 kurala sayılmaz)."""
    from core.prompt_generator import _event_stems, _verb_stem, event_fidelity_issues, text_event_stems
    story = story or ""
    out = []

    def add(rule, missing, feedback):
        out.append({"rule": rule, "missing": missing, "feedback": feedback})

    n = len(story.split())
    if not MIN_WORDS <= n <= MAX_WORDS:
        add("length", f"40-60 kelime ({n} kelime)", f"The story has {n} words; write {MIN_WORDS} to {MAX_WORDS} words.")
    # a
    first_sentence = _first_sentence(story)
    # Gevşetme (Bahadır onayı, 30 Eyl, iyi sel hikâyeleri reddediliyordu: "a wall of brown water bursts..."):
    # olayın ilk anahtar grubundaki kelimeler de tetik sayılır.
    if not (trigger_stems(event) & text_event_stems(first_sentence)
            or find_terms(EVENT_REQUIRED[event][0], first_sentence)):
        add("a_trigger_first", STORY_RULES["a_trigger_first"],
            f"The first sentence must show the trigger happening: '{event}'.")
    # b
    cam = find_terms(CAMERA_WORDS, story)
    if cam:
        add("b_no_camera_words", f"{STORY_RULES['b_no_camera_words']} ({', '.join(cam)})",
            f"Remove the words {', '.join(cam)}; describe only the scene itself.")
    # c
    meta = find_terms(META_PHRASES, story)
    if meta:
        add("c_no_meta_or_waiting", f"{STORY_RULES['c_no_meta_or_waiting']} ({', '.join(meta)})",
            f"Remove {', '.join(repr(m) for m in meta)}: no waiting, tension or talk about the video; show action.")
    # d
    small = find_terms(SCALE_REDUCERS, story)
    if small:
        add("d_no_scale_reducers", f"{STORY_RULES['d_no_scale_reducers']} ({', '.join(small)})",
            f"Remove {', '.join(repr(s) for s in small)}: the event is catastrophic, never mild or harmless.")
    # e
    if event_fidelity_issues(event, story):
        # Geri bildirim eksik kelimeleri söyler (29 Eyl kanıt koşusu: "deluge" yazan sel hikâyesi iki kez kaldı)
        missing = _event_stems(event) - _event_stems(story)
        words = list(dict.fromkeys(w for w in re.findall(r"[A-Za-z]+", event) if _verb_stem(w.lower())[:4] in missing))
        add("e_event_and_ship_named", f"olay adı ({', '.join(words)})",
            f"The story must clearly show this event: '{event}'. Name it with its own words "
            f"(for example: {', '.join(words)}).")
    ship_words = SHIP_TYPE_WORDS.get(ship or "", ())
    if ship_words and not find_terms(ship_words, story):
        add("e_event_and_ship_named", f"gemi türü ({ship_words[0]})",
            f"Name the vessel by its type: {SHIP_PHRASES.get(ship, ship)}.")
    # f
    if suffix is not None and "phone" in suffix.lower():
        add("f_no_phone_in_style", STORY_RULES["f_no_phone_in_style"], "")
    # Olay anahtar grupları
    for group in EVENT_REQUIRED[event]:
        if not find_terms(group, story):
            add("required", f"anahtar grup: {' / '.join(group)}",
                f"The story must show one of: {', '.join(group)}.")
    # Yasak liste (sadece iki kızak olayı)
    bad = find_terms(EVENT_FORBIDDEN.get(event, ()), story)
    if bad:
        add("forbidden", f"yasak kelime: {', '.join(bad)} ({FORBIDDEN_FEEDBACK_TR})",
            f"Do not use: {', '.join(bad)}. {FORBIDDEN_FEEDBACK_EN}")
    return out


class CreativeStoryError(NoValidScenarioError):
    """GPT-4o hikâyesi 3 denemede de kural kapısından geçemedi; Kie'ye gidilmez. NoValidScenarioError olduğu için
    main.py Telegram'a ayrıntıyı (trace) ve açık hata özetini gönderir."""

    def __init__(self, message: str, attempts: list[dict], trace: dict | None = None):
        super().__init__(message, attempts=attempts, trace=trace)

    def short_summary(self, max_reason: int = 0) -> str:
        """Deneme başına tek satır: 'Deneme 2 · ❌ eksik: ilk cümlede tetik; anahtar grup: wave'."""
        lines = [str(self)] + [f"Deneme {a.get('attempt')} · ❌ eksik: {'; '.join(a.get('missing') or ['?'])}"
                               for a in self.attempts]
        return "\n".join(lines)


def story_issues(event: str, story: str, ship: str | None = None) -> list[str]:
    """GPT'ye giden geri bildirim cümleleri (kural kapısı). Boş liste = geçti."""
    return [i["feedback"] for i in story_rule_issues(event, ship, story) if i["feedback"]]


def pick_setting(event: str, rng: random.Random | None = None) -> tuple[str, str]:
    """(yer anahtarı, hava) iskelet listelerinden rastgele."""
    rng = rng or random
    s = EVENT_SKELETONS[event]
    return rng.choice(list(s["spots"])), rng.choice(s["weather"])


def recent_stories(history_texts: list[str], limit: int = RECENT_STORIES) -> list[str]:
    """Geçmişten hikâye gibi olan (en az 20 kelimelik) son metinler; başlıklar elenir."""
    return [t for t in history_texts if len((t or "").split()) >= 20][-limit:]


def _message(event: str, ship: str | None, place: str, weather: str, lo: int, hi: int, recent: list[str],
             feedback: list[str] | None) -> str:
    msg = (f"EVENT: {event}\nVESSEL: {SHIP_PHRASES.get(ship or '', 'none')}\nPLACE: {place}\nWEATHER: {weather}\n"
           f"PEOPLE VISIBLE: {lo} to {hi}\nOUTCOME TO REACH IN THE LAST BEAT: {EVENT_OUTCOMES[event]}\nRECENT STORIES:\n" + ("\n".join(f"- {s}" for s in recent) or "- (none)"))
    if feedback:
        msg += "\n\nYOUR PREVIOUS STORY WAS REJECTED: " + " ".join(feedback)
    return msg


async def write_story(event: str, ship: str | None, place: str, weather: str, recent: list[str],
                      call_gpt) -> tuple[str, list[dict]]:
    """GPT-4o hikâyesi; kural kapısından kalırsa geri bildirimle yeniden, en fazla MAX_ATTEMPTS deneme.
    (hikâye, deneme kaydı). Deneme kaydında "issues" GPT'ye giden geri bildirim, "missing" Türkçe unsurlar."""
    lo, hi = count_range(event, ship)
    attempts, feedback = [], None
    for attempt in range(MAX_ATTEMPTS):
        raw = await call_gpt(CREATIVE_SYSTEM, _message(event, ship, place, weather, lo, hi, recent, feedback),
                             temperature=0.9, model="gpt-4o")
        story = str((raw or {}).get("story") or "").strip()
        found = story_rule_issues(event, ship, story) + diversity_issues(story, recent)
        issues = [i["feedback"] for i in found if i["feedback"]]
        attempts.append({"attempt": attempt + 1, "story": story, "words": len(story.split()), "issues": issues,
                         "missing": [i["missing"] for i in found]})
        if not found:
            return story, attempts
        feedback = issues
    raise CreativeStoryError(f"Hikâye {MAX_ATTEMPTS} denemede kural kapısından geçmedi, Kie'ye gönderilmedi.",
                             attempts)


async def build_creative_scene(domain: str | None, event: str | None, history: list[str], history_texts: list[str],
                               call_gpt) -> dict:
    """Seçim (Python) + GPT-4o hikâyesi + iskeletle aynı stil eki."""
    domain, event, ship = choose_event_and_ship(domain, event, history)
    spot, weather = pick_setting(event)
    place = EVENT_SKELETONS[event]["spots"][spot]
    recent = recent_stories(history_texts)
    lo, hi = count_range(event, ship)
    trace = {"pipeline": "creative", "domain": domain, "event": event, "ship": ship or "None",
             "camera": SKELETON_CAMERA, "spot": spot, "place": place, "weather": weather, "count_range": [lo, hi],
             "outcome": EVENT_OUTCOMES[event], "recent_count": len(recent), "attempts": [], "story": "",
             "story_words": 0}
    try:
        story, attempts = await write_story(event, ship, place, weather, recent, call_gpt)
    except CreativeStoryError as e:
        e.trace = {**trace, "attempts": e.attempts}
        raise
    suffix = style_suffix(event, ship, spot)
    # f: stil eki sabittir; "phone" girerse Kie'ye gitmez (kod hatası, GPT'ye geri bildirim yok)
    phone = [i for i in story_rule_issues(event, ship, story, suffix) if i["rule"] == "f_no_phone_in_style"]
    if phone:
        raise CreativeStoryError("Stil ekinde 'phone' var, Kie'ye gönderilmedi.", attempts, trace)
    combo_key = f"{domain}|{(ship or 'none').lower()}|{event.lower()}|{spot.lower()}|{SKELETON_CAMERA}"
    trace.update(attempts=attempts, story=story, story_words=len(story.split()))
    log.info(f"✍️ Creative: [{domain}] {event} | gemi={ship} | yer={spot} | hava={weather} | {len(story.split())} kelime")
    return {"domain": domain, "event": event, "ship": ship, "spot": spot, "story": story, "style_suffix": suffix,
            "prompt": f"{story.rstrip('.')}. {suffix}", "combo_key": combo_key, "trace": trace}
