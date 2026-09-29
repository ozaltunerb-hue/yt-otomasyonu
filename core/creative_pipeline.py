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
2. Three beats: the trigger happens; the movement it causes; the result, still unfolding, reaching the given outcome. The first sentence shows the moment the trigger happens (the wave clears the rail, the cable snaps, the wall of water enters the street); never open with waiting, tension or buildup; describe the scene, never the camera or the video.
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
    "Mooring line snaps in a storm gust":
        "the yacht swings free and slams its hull into the neighboring berth again and again",
    "Storm surge wave lifts and buckles the floating pontoon":
        "the pontoon buckles and tilts, throwing the moored boat against it as more waves roll in",
    "Passing boat's wake slams the boat sideways":
        "the boat heels hard and keeps slamming against the dock as the wake rolls through",
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
    "Storm gust tears signs and scaffolding loose downtown":
        "scaffolding and signs crash onto the street and parked cars as more panels tear loose",
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


class CreativeStoryError(RuntimeError):
    """GPT-4o hikâyesi iki denemede de sert kontrollerden (olay uyuşması, 40-60 kelime) geçemedi."""


def story_issues(event: str, story: str) -> list[str]:
    """Sadece iki sert kontrol: olay uyuşması ve 40-60 kelime. Boş liste = geçti."""
    from core.prompt_generator import _event_stems, _verb_stem, event_fidelity_issues   # döngüsel import olmasın
    issues = []
    n = len((story or "").split())
    if not MIN_WORDS <= n <= MAX_WORDS:
        issues.append(f"The story has {n} words; write {MIN_WORDS} to {MAX_WORDS} words.")
    if event_fidelity_issues(event, story or ""):
        # Geri bildirim eksik kelimeleri söyler (29 Eyl kanıt koşusu: "deluge" yazan sel hikâyesi iki kez kaldı)
        missing = _event_stems(event) - _event_stems(story or "")
        words = list(dict.fromkeys(w for w in re.findall(r"[A-Za-z]+", event)
                                   if _verb_stem(w.lower())[:4] in missing))
        issues.append(f"The story must clearly show this event: '{event}'. Name it with its own words "
                      f"(for example: {', '.join(words)}).")
    return issues


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
    """GPT-4o hikâyesi; kontrolden kalırsa 1 kez geri bildirimle yeniden. (hikâye, deneme kaydı)."""
    lo, hi = count_range(event, ship)
    attempts, feedback = [], None
    for attempt in range(2):
        raw = await call_gpt(CREATIVE_SYSTEM, _message(event, ship, place, weather, lo, hi, recent, feedback),
                             temperature=0.9, model="gpt-4o")
        story = str((raw or {}).get("story") or "").strip()
        issues = story_issues(event, story)
        attempts.append({"attempt": attempt + 1, "story": story, "words": len(story.split()), "issues": issues})
        if not issues:
            return story, attempts
        feedback = issues
    raise CreativeStoryError(f"Hikâye 2 denemede kontrolden geçmedi: {json.dumps(attempts, ensure_ascii=False)}")


async def build_creative_scene(domain: str | None, event: str | None, history: list[str], history_texts: list[str],
                               call_gpt) -> dict:
    """Seçim (Python) + GPT-4o hikâyesi + iskeletle aynı stil eki."""
    domain, event, ship = choose_event_and_ship(domain, event, history)
    spot, weather = pick_setting(event)
    place = EVENT_SKELETONS[event]["spots"][spot]
    recent = recent_stories(history_texts)
    story, attempts = await write_story(event, ship, place, weather, recent, call_gpt)
    suffix = style_suffix(event, ship, spot)
    lo, hi = count_range(event, ship)
    combo_key = f"{domain}|{(ship or 'none').lower()}|{event.lower()}|{spot.lower()}|{SKELETON_CAMERA}"
    trace = {"pipeline": "creative", "domain": domain, "event": event, "ship": ship or "None",
             "camera": SKELETON_CAMERA, "spot": spot, "place": place, "weather": weather, "count_range": [lo, hi],
             "outcome": EVENT_OUTCOMES[event],
             "recent_count": len(recent), "attempts": attempts, "story": story, "story_words": len(story.split())}
    log.info(f"✍️ Creative: [{domain}] {event} | gemi={ship} | yer={spot} | hava={weather} | {len(story.split())} kelime")
    return {"domain": domain, "event": event, "ship": ship, "spot": spot, "story": story, "style_suffix": suffix,
            "prompt": f"{story.rstrip('.')}. {suffix}", "combo_key": combo_key, "trace": trace}
