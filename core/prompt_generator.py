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
]

_STATIC_KEYWORDS = [
    "driving", "parking", "loading", "waiting", "standing by", "routine",
    "calm", "normal operations", "peacefully", "smoothly", "uneventful",
    "idle", "quietly", "nothing unusual", "business as usual",
]


def validate_high_action(scenario: dict) -> tuple[bool, list[str]]:
    """
    Aksiyon/Tehlike Yoğunluğu Kontrolü (Sakin/Statik Sahne Reddi).

    Kontroller:
      1. En az bir aktif tehlike/aksiyon kelimesi (collision, snap, flood, list,
         capsize, ...) var mı?
      2. Yoksa, sakin/rutin dile işaret eden anahtar kelimeler (driving, loading,
         waiting, routine, calm, ...) tespit edilip nedeni açıkça loglanır.
    """
    failures = []
    movement = scenario.get("physical_movement", "")
    consequence = scenario.get("visible_consequence", "")
    summary = scenario.get("scenario_summary", "")
    full_text = f"{movement} {consequence} {summary}".lower()

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

    is_valid = len(failures) == 0
    return is_valid, failures


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

    # ── ADIM 1 & 2: Kombinasyon Seçimi ve GPT-4o Senaryo Üretimi ──
    max_scenario_retries = 3
    max_dedup_attempts = 50
    scenario = None
    catalyst = None
    camera_archetype = None
    combo_key = ""

    for attempt in range(max_scenario_retries):
        # Geçerli bir catalyst bul (used_combos'ta olmayan)
        for _ in range(max_dedup_attempts):
            catalyst = get_creative_catalyst(recent_history=combined_history)
            camera_archetype = choose_camera_archetype(catalyst["domain_id"])
            combo_key = f"{catalyst['domain_id']}|{catalyst['forced_ship'].lower()}|{catalyst['forced_event'].lower()}|{catalyst['forced_environment'].lower()}|{camera_archetype}"
            if combo_key not in used_combos:
                break
                
        log.info(f"🧭 Denizcilik Alanı ({attempt+1}/{max_scenario_retries}): [{catalyst['domain_id']}] {catalyst['domain_title']}")
        log.info(f"⚓ Seçilen Gemi: {catalyst['forced_ship']} | 🌊 Olay: {catalyst['forced_event']} | 🌍 Ortam: {catalyst['forced_environment']}")
        log.info(f"🎥 Kamera Arketipi: [{camera_archetype}]")

        raw_scenario = await _generate_scenario(catalyst, camera_archetype)
        is_visible, visibility_failures = validate_silent_visibility(raw_scenario)
        is_active, action_failures = validate_high_action(raw_scenario)
        is_valid = is_visible and is_active
        failures = visibility_failures + action_failures

        if is_valid:
            scenario = raw_scenario
            log.info(f"✅ Senaryo Onaylandı: {scenario.get('scenario_summary', '')}")
            break
        else:
            log.warning(
                f"⚠️ Senaryo kontrolü başarısız: {failures} "
                f"| Reddedilen senaryo: {raw_scenario.get('scenario_summary', '')}"
            )
            # Eğer başarısızsa, döngü başa dönecek ve YENİ bir catalyst seçecek.
            # Ancak yeni seçilen catalyst'in daha önce seçilmemiş olmasını sağlamak için 
            # başarısız combo_key'i geçici olarak used_combos'a ekleyebiliriz veya 
            # get_creative_catalyst'in history rotasyonuna güvenebiliriz. Biz rotasyona güveniyoruz 
            # ama aynı zamanda bu başarısız komboyu tekrar denemesin diye history'ye ekliyoruz:
            combined_history.append(combo_key)
            used_combos.append(combo_key)

    if scenario is None:
        scenario = raw_scenario  # Fallback

    # ── ADIM 3: Seedance 2 Mini Doğukan Promptu (25–45 Kelime — DEFAULT_DURATION Standardı) ──
    log.info(f"✂️ Sahne Doğukan standardına sadeleştiriliyor (25–45 kelime {settings.DEFAULT_DURATION}s)...")
    simplified = await _simplify_prompt(scenario, catalyst)
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
        "tags": metadata.get("tags", ["DeepMyster", "Shorts", "Maritime", "CCTV", "CargoShip", "Ferry", "RoughSeas"]),
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
2. Choose an authentic, realistic vessel — cruise/passenger ship, ferry, Ro-Ro carrier, general cargo ship, container ship, tanker, tugboat/rescue boat, yacht/marina craft, or another realistic sea vessel — and physical crisis within or inspired by the '{catalyst['domain_title']}' domain. Vary vessel type across generations rather than defaulting to the same type.
3. The crisis must be completely visible and intuitive on a silent screen within 2-3 seconds.
4. Structure the {duration}-second single continuous take: visible start (0-{early}s) -> physical escalation & contextual crew/mechanical response ({early}-{late}s) -> concrete physical state change at {duration}s.
5. Keep human presence natural and context-appropriate (or pure raw industrial physics). No cartoonish shoehorned actions.
6. The scene must show CONSTANT HIGH ACTION — something actively breaking, colliding, flooding, swinging, or in danger in real time. Never calm, static, or purely observational.
7. Dress crew/staff in authentic high-visibility orange, red, or yellow PPE, wetsuits, or coveralls — never white hazmat/astronaut suits, even in arctic/polar settings (use red or orange polar immersion suits instead). Dress passengers, boat owners, guests, and vehicle drivers/occupants in ordinary civilian clothing appropriate to the setting (swimwear/resort wear for pool/deck scenes, casual clothing for car-deck scenes, yacht-casual for marina scenes) — never hi-vis PPE on civilians. Depict raw, natural weather and lighting — never glossy, CGI-clean, or movie-trailer polished.{chase_pov_directive}"""

    system_prompt = build_scenario_writer_system(duration, catalyst.get("domain_id", ""))
    result = await _call_gpt(system_prompt, user_message, temperature=0.85)

    # Geriye dönük uyumluluk alanları
    if "scene_description" not in result:
        result["scene_description"] = (
            f"From {result.get('observer_camera', 'fixed CCTV')}, {result.get('visible_start', '')} "
            f"leads to {result.get('physical_movement', '')}, finally {result.get('visible_consequence', '')}."
        )

    return result


async def _simplify_prompt(scenario: dict, catalyst: dict) -> dict:
    """Katman 3: Senaryoyu Seedance 2 Mini için 25–45 kelimelik yüksek sinyalli prompt'a çevir."""
    duration = settings.DEFAULT_DURATION
    early, late = compute_duration_breakpoints(duration)
    user_message = f"""Convert this realistic maritime incident into an exact 25–45 word Seedance 2 Mini prompt following the Doğukan methodology:

VESSEL CLASS: {scenario.get('vessel_class', 'Cargo Vessel')}
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

    system_prompt = build_prompt_simplifier_system(duration, catalyst.get("domain_id", ""))
    result = await _call_gpt(system_prompt, user_message, temperature=0.75)

    if "prompt" not in result or not result["prompt"]:
        fallback_prompt = (
            f"On a rolling {scenario.get('vessel_class', 'vessel')} in rough seas, "
            f"{scenario.get('physical_movement', 'cargo shifts under wave impact')}, "
            f"finally {scenario.get('visible_consequence', 'settling against the deck barrier')}."
        )
        result = {"prompt": fallback_prompt, "word_count": len(fallback_prompt.split())}

    return result


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
                "prompt": "A towering green swell crashes over the bow of an arctic stern trawler, swamping the foredeck as a deckhand braces against the winch housing. Seawater violently rushes through freeing ports into the foam. Fixed forecastle CCTV camera, raw overcast daylight.",
                "duration": settings.DEFAULT_DURATION,
            }
        ],
        "youtube_title": "⚠️ Giant Green Swell Swamps Arctic Trawler Bow #Shorts",
        "youtube_description": "Forecastle CCTV captures a towering arctic swell breaching the foredeck of a working stern trawler. #DeepMyster #Shorts #Maritime #CCTV #RoughSeas",
        "tags": ["DeepMyster", "Shorts", "Maritime", "CCTV", "Trawler", "Arctic", "RoughSeas", "Ocean"],
        "scenario_summary": "A massive arctic wave swamps the forward working deck of a stern trawler before draining rapidly through side freeing ports.",
        "combo_key": "commercial_storm_fishing|arctic stern trawler|bow wave swamping",
        "total_duration": settings.DEFAULT_DURATION,
        "animal": "arctic stern trawler",
        "talent": "bow wave swamping",
        "category": "commercial_storm_fishing",
    }
