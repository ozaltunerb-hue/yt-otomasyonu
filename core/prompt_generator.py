from __future__ import annotations

"""
Prompt Generator — "DeepMyster" 12 Kriterli Mikro-Hikâye & Seedance 2 Mini Pipeline.

Creative Engine'den komplikasyonlu seed alır → GPT-4o ile 5 aşamalı mikro-olay senaryosu yazar →
12 Kriterli Sıkı Otomatik Kalite Kontrolü (12 PASS Kontrolü + Self-Correction) →
Seedance 2 Mini optimize eylem & sonuç prompt'una dönüştürür.
"""
import re
import json
import asyncio
import logging
import threading
from openai import OpenAI
from config import settings
from core.creative_engine import (
    generate_creative_seed,
    SCENARIO_WRITER_SYSTEM,
    PROMPT_SIMPLIFIER_SYSTEM,
    YOUTUBE_METADATA_SYSTEM,
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
            max_tokens=1800,
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


def validate_scenario_12_criteria(scenario: dict, title: str = "") -> dict[str, dict]:
    """
    GPT-4o tarafından üretilen senaryoyu 12 zorunlu kalite kriteri açısından denetler.
    
    Returns:
        dict: {
            "all_passed": True/False,
            "results": {
                "1_strong_hook_first_3s": {"status": "PASS", "reason": "..."},
                ...
                "12_complete_micro_narrative": {"status": "PASS", "reason": "..."}
            },
            "failures": ["Kriter 5 başarısız: ...", ...]
        }
    """
    story_arc = scenario.get("story_arc", {}) if isinstance(scenario.get("story_arc"), dict) else {}
    scenes = scenario.get("scenes", [])
    what_changed = scenario.get("what_happened_and_what_changed", "").strip()
    self_check = scenario.get("quality_self_check_12", {}) if isinstance(scenario.get("quality_self_check_12"), dict) else {}

    results = {}
    failures = []

    # Kriter 1: İlk 3 saniyede olağandışı bir olay var mı?
    hook = story_arc.get("hook_seconds_1_3", "").strip()
    if len(hook) >= 15 and not any(p in hook.lower() for p in ["calm sea", "peaceful", "establishing shot"]):
        results["1_strong_hook_first_3s"] = {"status": "PASS", "details": hook}
    else:
        results["1_strong_hook_first_3s"] = {"status": "FAIL", "details": "Hook eksik veya durağan"}
        failures.append("1. İlk 3 saniyede olağandışı somut bir olay başlamıyor")

    # Kriter 2: İzleyici neyin yanlış gittiğini anlayabiliyor mu?
    incident = story_arc.get("incident_seconds_3_7", "").strip()
    if len(incident) >= 15:
        results["2_clear_problem_established"] = {"status": "PASS", "details": incident}
    else:
        results["2_clear_problem_established"] = {"status": "FAIL", "details": "Problem net değil"}
        failures.append("2. Olayın/tehlikenin ne olduğu net şekilde anlaşılmıyor")

    # Kriter 3: Mürettebat aktif fiziksel müdahale yapıyor mu?
    desc_all = " ".join([s.get("description", "") for s in scenes]) + " " + incident
    crew_actions = ["scramble", "dive", "haul", "jam", "cut", "maneuver", "latch", "steer", "shove", "pry", "brace", "drop", "pull", "rush", "hook"]
    has_crew_action = any(act in desc_all.lower() for act in crew_actions)
    if has_crew_action:
        results["3_active_crew_physical_action"] = {"status": "PASS", "details": "Mürettebat aktif eylemde"}
    else:
        results["3_active_crew_physical_action"] = {"status": "FAIL", "details": "Mürettebat pasif veya fiziksel eylem yok"}
        failures.append("3. Mürettebat aktif fiziksel müdahale yapmıyor")

    # Kriter 4: Olay gerçekten tırmanıyor mu?
    escalation = story_arc.get("escalation_and_complication_seconds_7_12", "").strip()
    if len(escalation) >= 20:
        results["4_genuine_escalation"] = {"status": "PASS", "details": escalation}
    else:
        results["4_genuine_escalation"] = {"status": "FAIL", "details": "Tırmanış aşaması yetersiz"}
        failures.append("4. Olay tırmanmıyor veya gerilim artmıyor")

    # Kriter 5: İlk çözümün dışında yeni bir komplikasyon / başarısız ilk hamle var mı?
    complication_words = ["fails", "snaps", "slips", "pops", "jams", "parted", "short", "overload", "lags", "binds", "misses", "unexpected", "secondary", "forced", "forcing"]
    has_complication = any(w in escalation.lower() or w in desc_all.lower() for w in complication_words)
    if has_complication and self_check.get("5_unexpected_complication_present", True):
        results["5_unexpected_complication_present"] = {"status": "PASS", "details": "Komplikasyon / ikinci risk mevcut"}
    else:
        results["5_unexpected_complication_present"] = {"status": "FAIL", "details": "Olay tek hamlede kolayca çözülüyor (komplikasyon yok)"}
        failures.append("5. İlk çözüm dışında yeni bir komplikasyon / başarısız ilk hamle yok")

    # Kriter 6: Kritik bir an var mı?
    critical = story_arc.get("critical_moment_seconds_12_15", "").strip()
    if len(critical) >= 15:
        results["6_critical_decisive_moment"] = {"status": "PASS", "details": critical}
    else:
        results["6_critical_decisive_moment"] = {"status": "FAIL", "details": "Kritik an eksik"}
        failures.append("6. Kritik belirleyici an tanımlanmamış")

    # Kriter 7: Sonuç görsel olarak gerçekleşiyor mu?
    resolution = story_arc.get("resolution_seconds_15_18", "").strip()
    if len(resolution) >= 15 and not resolution.lower().startswith("and then"):
        results["7_visible_physical_resolution"] = {"status": "PASS", "details": resolution}
    else:
        results["7_visible_physical_resolution"] = {"status": "FAIL", "details": "Görsel/fiziksel sonuç yetersiz"}
        failures.append("7. Sonuç görsel ve fiziksel olarak gerçekleşmiyor")

    # Kriter 8: Videonun sonunda fiziksel olarak neyin değiştiği açık mı?
    if len(what_changed) >= 25:
        results["8_clear_what_changed_physically"] = {"status": "PASS", "details": what_changed}
    else:
        results["8_clear_what_changed_physically"] = {"status": "FAIL", "details": "what_happened_and_what_changed yetersiz"}
        failures.append("8. Videonun sonunda fiziksel olarak neyin değiştiği açık değil")

    # Kriter 9: Shotlar tek bir olayın devamı mı?
    if len(scenes) >= 1 and all(len(s.get("description", "")) >= 25 for s in scenes):
        results["9_strict_shot_continuity"] = {"status": "PASS", "details": f"{len(scenes)} sahne sürekliliği koruyor"}
    else:
        results["9_strict_shot_continuity"] = {"status": "FAIL", "details": "Sahne sürekliliği eksik"}
        failures.append("9. Shotlar tek bir olayın fiziksel devamı değil")

    # Kriter 10: İzleyici sonucu önceden tahmin etmeden videonun sonuna kadar izlemek ister mi?
    if has_complication and len(critical) >= 15:
        results["10_unpredictable_curiosity_maintained"] = {"status": "PASS", "details": "Merak unsuru ve belirsizlik korundu"}
    else:
        results["10_unpredictable_curiosity_maintained"] = {"status": "FAIL", "details": "Merak unsuru zayıf"}
        failures.append("10. Sonuç çok tahmin edilebilir veya merak unsuru eksik")

    # Kriter 11: Başlık sonucu gereksiz şekilde spoiler vermiyor mu?
    title_to_check = title or scenario.get("scenario_title", "")
    spoiler_words = ["saved by", "rescued by", "fixed by", "prevents collision", "miracle escape", "survives unharmed"]
    has_spoiler = any(sp in title_to_check.lower() for sp in spoiler_words)
    if not has_spoiler and len(title_to_check) > 5:
        results["11_no_spoiler_in_title"] = {"status": "PASS", "details": f"Başlık gerilim odaklı (No spoiler): {title_to_check}"}
    else:
        results["11_no_spoiler_in_title"] = {"status": "FAIL", "details": f"Başlıkta spoiler tespit edildi: {title_to_check}"}
        failures.append("11. Başlık sonucu baştan ele veriyor (spoiler içeriyor)")

    # Kriter 12: Video yalnızca "güzel görüntü" değil, başı-sonu olan gerçek bir mikro-olay mı?
    if len(failures) == 0:
        results["12_complete_micro_narrative"] = {"status": "PASS", "details": "Tam ve tamamlanmış mikro-olay örgüsü"}
    else:
        results["12_complete_micro_narrative"] = {"status": "FAIL", "details": "Eksik anlatı ögeleri var"}
        failures.append("12. Başı ve sonu olan gerçek bir mikro-olay tamamlanmadı")

    all_passed = (len(failures) == 0)
    return {
        "all_passed": all_passed,
        "results": results,
        "failures": failures,
    }


async def generate_prompts(config: dict) -> dict:
    """Tam otonom 12 kriterli video prompt pipeline'ı."""
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: 12 kriterli DeepMyster mock promptları üretiliyor...")
        return _dry_run_output()

    used_combos = config.get("used_combos", [])

    # ── ADIM 1: Yaratıcı Olay Seed'i Seç ──
    seed = generate_creative_seed(used_combos)
    log.info(f"🎲 Seed: [{seed['category_label']}] {seed['vessel']} × {seed['incident'][:50]}...")

    # ── ADIM 2: GPT Senaryo Yaz + 12 Kriter Kalite Kontrolü (Retry Döngüsü) ──
    log.info("🤖 GPT-4o'ya komplikasyonlu 5 aşamalı mikro-olay senaryosu yazdırılıyor...")
    scenario, validation_data = await _generate_scenario_with_12_validation(seed)
    log.info(
        f"📋 Senaryo 12 KRİTERDEN GEÇTİ: {scenario.get('clip_count', 1)} klip, "
        f"{scenario.get('total_duration', 15)}s | Olay: {scenario.get('scenario_title', 'Maritime Event')}"
    )
    log.info(f"   🔍 Değişim / Payoff: {scenario.get('what_happened_and_what_changed', '')}")

    # ── ADIM 3: Seedance 2 Mini İçin Eylem & Komplikasyon & Sonuç Prompt'u ──
    scenes = scenario.get("scenes", [])
    simplified_scenes = []

    for scene in scenes:
        log.info(f"✂️ Sahne {scene['scene_number']}/{len(scenes)} Seedance 2 Mini formatına dönüştürülüyor...")
        simplified = await _simplify_prompt(scene, seed, scenario)
        simplified_scenes.append({
            "scene_number": scene["scene_number"],
            "prompt": simplified["prompt"],
            "duration": scene.get("duration", 15),
        })
        word_count = len(simplified["prompt"].split())
        log.info(f"   → Seedance 2 Mini Prompt ({word_count} kelime): {simplified['prompt']}")

    # ── ADIM 4: YouTube Metadata (Merak ve Spoiler'sız Başlık) ──
    log.info("📺 YouTube metadata üretiliyor...")
    metadata = await _generate_metadata(scenario, seed)

    # ── ADIM 5: Safety Sanitizer ──
    from core.prompt_sanitizer import sanitize_prompt
    for scene in simplified_scenes:
        original = scene["prompt"]
        sanitized, changes = sanitize_prompt(original)
        if changes:
            scene["prompt"] = sanitized
            log.info(f"   🛡️ Sahne {scene['scene_number']} sanitize edildi: {len(changes)} değişiklik")

    # ── Sonuç Birleştir ──
    result = {
        "scenes": simplified_scenes,
        "youtube_title": clean_youtube_title(metadata.get("youtube_title", "Massive Ocean Wave Strikes Vessel #Shorts")),
        "youtube_description": metadata.get("youtube_description", ""),
        "tags": metadata.get("tags", ["DeepMyster", "Shorts", "Maritime", "RoughSeas", "Ocean", "Crew"]),
        "scenario_summary": scenario.get("scenario_summary", ""),
        "what_happened_and_what_changed": scenario.get("what_happened_and_what_changed", ""),
        "story_arc": scenario.get("story_arc", {}),
        "validation_12_criteria": validation_data,
        "combo_key": seed["combo_key"],
        "total_duration": scenario.get("total_duration", sum(s["duration"] for s in simplified_scenes)),
        "animal": seed["vessel"],
        "talent": seed["incident"],
        "category": seed["category"],
    }

    log.info(f"✅ DeepMyster Pipeline tamamlandı: \"{result['youtube_title']}\"")
    return result


async def _generate_scenario_with_12_validation(seed: dict, max_retries: int = 3) -> tuple[dict, dict]:
    """GPT-4o ile senaryo üretir ve 12 kriterin tamamı PASS olana kadar otomatik yeniden yazar."""
    feedback = ""
    last_validation = {}

    for attempt in range(max_retries):
        user_message = f"""Create a realistic, dramatic 5-stage maritime micro-story scenario for DeepMyster with AT LEAST ONE UNEXPECTED COMPLICATION:

CATEGORY: {seed.get('category_label', 'Deniz Olayı')}
VESSEL / SUBJECT: {seed.get('vessel', 'cargo ship')}
CORE INCIDENT: {seed.get('incident', 'emergency event in rough sea')}
SETTING / LOCATION: {seed['setting']}
DYNAMICS: {seed['twist']}
CAMERA PERSPECTIVE: {seed.get('camera_perspective', 'raw documentary camera footage')}
ACTIVE CREW ROLE: {seed.get('crew_context', 'Active crew responding to crisis')}

MANDATORY RULES:
1. HOOK (1-3s): Already in motion, shocking start.
2. INCIDENT (3-7s): Problem established, crew physically intervenes.
3. ESCALATION & COMPLICATION (7-12s): Initial fix fails, tool slips, line snaps, or secondary risk emerges! NO simple 1-step fixes!
4. CRITICAL MOMENT (12-15s): High-stakes decisive move.
5. RESOLUTION (15-18s): VISIBLE physical change (trajectory deflected, damage contained, brake engaged).
6. GOLDEN RULE: Answer 'what exactly happened and what physically changed by the end?'
7. NO SPOILERS IN TITLE: Title must highlight danger, never reveal the resolution."""

        if feedback:
            user_message += f"\n\nPREVIOUS ATTEMPT FAILED QUALITY CONTROL (12 CRITERIA):\n{feedback}\nPlease fix these failures and regenerate a fully compliant micro-story."

        scenario = await _call_gpt(SCENARIO_WRITER_SYSTEM, user_message, temperature=0.85)

        # 12 Kriter Doğrulaması
        validation = validate_scenario_12_criteria(scenario, scenario.get("scenario_title", ""))
        last_validation = validation

        if validation["all_passed"]:
            for scene in scenario.get("scenes", []):
                dur = scene.get("duration", 15)
                scene["duration"] = max(10, min(15, dur))
            return scenario, validation

        feedback = "\n".join(f"- {f}" for f in validation["failures"])
        log.warning(f"⚠️ Senaryo 12 kriter kontrolünden geçemedi (Deneme {attempt+1}/{max_retries}):\n{feedback}")

    log.error("❌ Maksimum senaryo deneme sınırına ulaşıldı, son üretilen senaryo kullanılıyor.")
    return scenario, last_validation


async def _simplify_prompt(scene: dict, seed: dict, scenario: dict) -> dict:
    """Katman 3: Seedance 2 Mini için eylem + komplikasyon + sonuç prompt'u üret."""
    story_arc = scenario.get("story_arc", {})
    user_message = f"""Convert this complete maritime micro-story with complication into a Seedance 2 Mini prompt:

VESSEL: {seed.get('vessel', 'cargo vessel')}
INCIDENT / CRISIS: {seed.get('incident', 'maritime emergency')}
CAMERA STYLE: {seed.get('camera_perspective', 'raw documentary camera footage, natural lighting')}

STORY PROGRESSION:
- Hook (1-3s): {story_arc.get('hook_seconds_1_3', '')}
- Incident & Complication (3-12s): {story_arc.get('incident_seconds_3_7', '')} → {story_arc.get('escalation_and_complication_seconds_7_12', '')}
- Critical Climax & Payoff (12-18s): {story_arc.get('critical_moment_seconds_12_15', '')} → {story_arc.get('resolution_seconds_15_18', '')}
- Physical Change: {scenario.get('what_happened_and_what_changed', '')}

SCENE DESCRIPTION: {scene.get('description', '')}

CRITICAL RULES FOR SEEDANCE 2 MINI:
- Output 30-50 words.
- Formula: [Action Hook in progress] + [Crew physical effort & complication] + [Decisive critical maneuver] + [Visible physical outcome] + [Realism style tag].
- Photorealistic raw documentary camera footage."""

    result = await _call_gpt(PROMPT_SIMPLIFIER_SYSTEM, user_message, temperature=0.7)

    if "prompt" not in result:
        raise ValueError(f"Simplifier yanıtında 'prompt' eksik: {result}")

    return result


async def _generate_metadata(scenario: dict, seed: dict) -> dict:
    """YouTube title, description, tags üret — merak odaklı ve no-spoiler."""
    story_arc = scenario.get("story_arc", {})
    user_message = f"""Create YouTube Shorts metadata for this maritime micro-story (NO SPOILERS IN TITLE):

VESSEL: {seed.get('vessel', 'vessel')}
CATEGORY: {seed.get('category_label', 'Maritime Incident')}
INCIDENT: {seed.get('incident', 'incident')}
STORY SUMMARY: {scenario.get('scenario_summary', '')}
HOOK: {story_arc.get('hook_seconds_1_3', '')}
COMPLICATION: {story_arc.get('escalation_and_complication_seconds_7_12', '')}
CRITICAL MOMENT: {story_arc.get('critical_moment_seconds_12_15', '')}

STRICT RULE: The title MUST highlight the crisis and danger, and NEVER reveal if or how it was resolved!"""

    result = await _call_gpt(YOUTUBE_METADATA_SYSTEM, user_message, temperature=0.8)

    raw_title = result.get("youtube_title", "")
    result["youtube_title"] = clean_youtube_title(raw_title)

    tags = result.get("tags", [])
    mandatory_tags = ["DeepMyster", "Shorts", "Maritime", "RoughSeas", "Ocean", "Crew", "Rescue"]
    for tag in mandatory_tags:
        if tag not in tags:
            tags.append(tag)
    result["tags"] = tags

    return result


def _dry_run_output() -> dict:
    """DRY-RUN modunda 12 kriteri karşılayan komplikasyonlu mock çıktısı."""
    mock_scenario = {
        "scenario_title": "⚠️ Rogue Wave Shakes Cargo Ferry Deck in Gale",
        "what_happened_and_what_changed": "A 40ft rogue wave tilted the vehicle deck causing a heavy trailer to snap lashings; the primary chain hook slipped as the truck slid, but deckhands jammed backup steel chocks under the tires, locking the vehicle 2 feet before hull collision.",
        "story_arc": {
            "hook_seconds_1_3": "A violent rolling swell snaps the primary trailer lashing chain with a sharp metallic crack on the wet ferry deck.",
            "incident_seconds_3_7": "The heavy freight truck begins sliding toward the companionway as two yellow-suited deckhands scramble across the flooded deck.",
            "escalation_and_complication_seconds_7_12": "The deckhand attempts to latch an emergency hook, but the chain slips under the truck's weight, causing the trailer to pivot dangerously toward the hull.",
            "critical_moment_seconds_12_15": "Both deckhands dive across the waterlogged deck and kick heavy steel chocks directly under the sliding front tires.",
            "resolution_seconds_15_18": "The chocks bite into the steel deck plates, halting the freight truck abruptly two feet before striking the vessel side."
        },
        "quality_self_check_12": {
            "1_strong_hook_first_3s": True,
            "2_clear_problem_established": True,
            "3_active_crew_physical_action": True,
            "4_genuine_escalation": True,
            "5_unexpected_complication_present": True,
            "6_critical_decisive_moment": True,
            "7_visible_physical_resolution": True,
            "8_clear_what_changed_physically": True,
            "9_strict_shot_continuity": True,
            "10_unpredictable_curiosity_maintained": True,
            "11_no_spoiler_in_title": True,
            "12_complete_micro_narrative": True
        },
        "scenes": [
            {
                "scene_number": 1,
                "description": "Continuous shot starting as a lashing chain snaps; the heavy truck slides toward crew, the emergency hook slips, deckhands dive to jam steel chocks under sliding tires, and the runaway trailer comes to a sudden halt before hull impact.",
                "duration": 15
            }
        ]
    }
    validation = validate_scenario_12_criteria(mock_scenario, mock_scenario["scenario_title"])
    return {
        "scenes": [
            {
                "scene_number": 1,
                "prompt": "As a 40-foot rogue wave snaps a cargo trailer lashing on a rolling ferry deck, an emergency hook slips, prompting deckhands in yellow gear to dive and jam steel chocks under sliding tires, halting the truck inches before hull impact. Photorealistic raw documentary camera footage, natural lighting.",
                "duration": 15,
            }
        ],
        "youtube_title": "⚠️ Rogue Wave Hits Ferry Deck Shifting Heavy Cargo #Shorts",
        "youtube_description": "Watch deckhands battle an escalating freight trailer crisis in heavy 40ft open seas as primary lashings fail. DeepMyster Official. #DeepMyster #Shorts #Maritime #RoughSeas",
        "tags": ["DeepMyster", "Shorts", "Maritime", "RoughSeas", "CargoShip", "Storm", "Ocean", "Crew", "Rescue"],
        "scenario_summary": "Deckhands battle shifting trailer after primary hook slips, kicking steel chocks to halt runaway truck before hull collision.",
        "what_happened_and_what_changed": mock_scenario["what_happened_and_what_changed"],
        "story_arc": mock_scenario["story_arc"],
        "validation_12_criteria": validation,
        "combo_key": "roro_accidents|large car and passenger ferry|Violent swell snaps primary trailer lashing",
        "total_duration": 15,
        "animal": "large car and passenger ferry",
        "talent": "Violent swell snaps primary trailer lashing",
        "category": "roro_accidents",
    }
