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


def validate_scenario_13_criteria(scenario: dict, title: str = "") -> dict:
    """
    GPT-4o tarafından üretilen senaryoyu 13 zorunlu kalite kriteri (12+1) açısından denetler.
    Her kriter için somut durum (PASS/FAIL) ve gerekçe/kanıt raporlar.
    
    Returns:
        dict: {
            "all_passed": True/False,
            "results": {
                "1_strong_hook_0_3s": {"status": "PASS", "reason": "..."},
                ...
                "13_story_driven_camera": {"status": "PASS", "reason": "..."}
            },
            "failures": ["Kriter 3 başarısız: ...", ...]
        }
    """
    story_arc = scenario.get("story_arc", {}) if isinstance(scenario.get("story_arc"), dict) else {}
    camera_plan = scenario.get("camera_plan", {}) if isinstance(scenario.get("camera_plan"), dict) else {}
    scenes = scenario.get("scenes", [])
    what_changed = scenario.get("what_happened_and_what_changed", "").strip()
    self_check = scenario.get("quality_self_check_13", {}) or scenario.get("quality_self_check_12", {})
    if not isinstance(self_check, dict):
        self_check = {}

    results = {}
    failures = []

    def _get_self_check_reason(key: str, default: str = "") -> str:
        val = self_check.get(key)
        if isinstance(val, dict):
            return str(val.get("reason", default))
        elif isinstance(val, str):
            return val
        return default

    # Kriter 1: İlk 3 saniyede olağandışı bir olay var mı? (Hook 0-3s)
    hook = (story_arc.get("hook_seconds_0_3") or story_arc.get("hook_seconds_1_3") or "").strip()
    reason_1 = _get_self_check_reason("1_strong_hook_0_3s") or _get_self_check_reason("1_strong_hook_first_3s") or hook
    if len(hook) >= 15 and not any(p in hook.lower() for p in ["calm sea", "peaceful", "establishing shot", "wide landscape", "ambient"]):
        results["1_strong_hook_0_3s"] = {"status": "PASS", "reason": f"Olay ilk karede başlamış: {reason_1}"}
    else:
        results["1_strong_hook_0_3s"] = {"status": "FAIL", "reason": "İlk 3 saniyede olağandışı somut bir olay başlamıyor (Hook eksik veya durağan)"}
        failures.append("1. İlk 3 saniyede olağandışı somut bir olay başlamıyor (establishing shot veya durağan görüntü yasak)")

    # Kriter 2: İzleyici neyin yanlış gittiğini anlayabiliyor mu? (Problem 3-6s)
    incident = (story_arc.get("incident_seconds_3_6") or story_arc.get("incident_seconds_3_7") or "").strip()
    reason_2 = _get_self_check_reason("2_clear_problem_3_6s") or _get_self_check_reason("2_clear_problem_established") or incident
    if len(incident) >= 15:
        results["2_clear_problem_3_6s"] = {"status": "PASS", "reason": f"Tehlike mekanizması net: {reason_2}"}
    else:
        results["2_clear_problem_3_6s"] = {"status": "FAIL", "reason": "Olayın ve tehlikenin mekanizması net şekilde anlaşılmıyor"}
        failures.append("2. Olayın/tehlikenin mekanizması net şekilde anlaşılmıyor")

    # Kriter 3: Mürettebat / insan karakter aktif fiziksel müdahale yapıyor mu? (Pasif duruş kesinlikle FAIL)
    desc_all = " ".join([s.get("description", "") for s in scenes]) + " " + incident + " " + hook
    crew_actions = [
        "scramble", "dive", "haul", "jam", "cut", "maneuver", "latch", "steer", "shove",
        "pry", "brace", "drop", "pull", "rush", "hook", "crank", "tackle", "deploy",
        "wrestle", "bleed", "twist", "spray", "sprint", "clamp", "sever", "heave"
    ]
    has_crew_action = any(act in desc_all.lower() for act in crew_actions)
    reason_3 = _get_self_check_reason("3_active_crew_physical_action")
    if has_crew_action:
        results["3_active_crew_physical_action"] = {"status": "PASS", "reason": f"Mürettebat aktif fiziksel müdahalede: {reason_3 or 'Somut beden gücü ve eylem mevcut'}"}
    else:
        results["3_active_crew_physical_action"] = {"status": "FAIL", "reason": "Mürettebat pasif veya fiziksel müdahale yok (yalnızca kadrajda görünmek kabul edilmez)"}
        failures.append("3. Mürettebat aktif fiziksel müdahale yapmıyor (yalnızca kadrajda durmak kabul edilmez, aktif beden eylemi zorunludur)")

    # Kriter 4: Olay gerçekten tırmanıyor mu? (Tırmanış)
    escalation = (story_arc.get("escalation_and_complication_seconds_6_9") or story_arc.get("escalation_and_complication_seconds_7_12") or "").strip()
    reason_4 = _get_self_check_reason("4_genuine_escalation") or escalation
    if len(escalation) >= 15:
        results["4_genuine_escalation"] = {"status": "PASS", "reason": f"Gerilim ve risk fiziksel olarak artıyor: {reason_4}"}
    else:
        results["4_genuine_escalation"] = {"status": "FAIL", "reason": "Tırmanış aşaması yetersiz veya gerilim artmıyor"}
        failures.append("4. Olay tırmanmıyor veya gerilim artmıyor")

    # Kriter 5: İlk çözümün dışında yeni bir komplikasyon / başarısız ilk hamle var mı? (Komplikasyon 6-9s)
    complication_words = [
        "fails", "snaps", "slips", "pops", "jams", "parted", "short", "overload",
        "lags", "binds", "misses", "unexpected", "secondary", "forced", "forcing",
        "unable", "stalls", "cracks", "shears", "kinks", "tangles"
    ]
    has_complication = any(w in escalation.lower() or w in desc_all.lower() for w in complication_words)
    reason_5 = _get_self_check_reason("5_unexpected_complication_6_9s") or _get_self_check_reason("5_unexpected_complication_present")
    if has_complication:
        results["5_unexpected_complication_6_9s"] = {"status": "PASS", "reason": f"İlk müdahale yetersiz kaldı, komplikasyon mevcut: {reason_5 or 'Başarısız hamle veya ikinci risk var'}"}
    else:
        results["5_unexpected_complication_6_9s"] = {"status": "FAIL", "reason": "Olay tek hamlede kolayca çözülüyor (komplikasyon yok)"}
        failures.append("5. İlk çözüm dışında yeni bir komplikasyon / başarısız ilk hamle yok (basit tehlike -> hemen kurtuldu kalıbı reddedildi)")

    # Kriter 6: Kritik bir an var mı? (Kritik An 9-12s)
    critical = (story_arc.get("critical_moment_seconds_9_12") or story_arc.get("critical_moment_seconds_12_15") or "").strip()
    reason_6 = _get_self_check_reason("6_critical_moment_9_12s") or _get_self_check_reason("6_critical_decisive_moment") or critical
    if len(critical) >= 15:
        results["6_critical_moment_9_12s"] = {"status": "PASS", "reason": f"Sonucu belirleyen nihai fiziksel hareket mevcut: {reason_6}"}
    else:
        results["6_critical_moment_9_12s"] = {"status": "FAIL", "reason": "Kritik belirleyici an tanımlanmamış"}
        failures.append("6. Kritik belirleyici an tanımlanmamış")

    # Kriter 7: Sonuç görsel olarak gerçekleşiyor mu? (Görsel Sonuç 12-15s)
    resolution = (story_arc.get("resolution_seconds_12_15") or story_arc.get("resolution_seconds_15_18") or "").strip()
    reason_7 = _get_self_check_reason("7_visible_physical_resolution_12_15s") or _get_self_check_reason("7_visible_physical_resolution") or resolution
    if len(resolution) >= 15 and not resolution.lower().startswith("and then"):
        results["7_visible_physical_resolution_12_15s"] = {"status": "PASS", "reason": f"Sonuç ekranda görsel/fiziksel olarak gerçekleşiyor: {reason_7}"}
    else:
        results["7_visible_physical_resolution_12_15s"] = {"status": "FAIL", "reason": "Görsel/fiziksel sonuç yetersiz veya soyut"}
        failures.append("7. Sonuç görsel ve fiziksel olarak gerçekleşmiyor (varsayımsal anlatım yasak)")

    # Kriter 8: Videonun sonunda fiziksel olarak neyin değiştiği açık mı? (Değişim)
    reason_8 = _get_self_check_reason("8_clear_what_changed_physically") or what_changed
    if len(what_changed) >= 20:
        results["8_clear_what_changed_physically"] = {"status": "PASS", "reason": f"Fiziksel değişim somut: {reason_8}"}
    else:
        results["8_clear_what_changed_physically"] = {"status": "FAIL", "reason": "what_happened_and_what_changed yetersiz"}
        failures.append("8. Videonun sonunda fiziksel olarak neyin değiştiği açık değil")

    # Kriter 9: Shotlar tek bir olayın fiziksel devamı ve neden-sonuç zinciri mi? (Süreklilik)
    reason_9 = _get_self_check_reason("9_strict_shot_continuity_and_causality") or _get_self_check_reason("9_strict_shot_continuity")
    if len(scenes) >= 1 and all(len(s.get("description", "")) >= 20 for s in scenes):
        results["9_strict_shot_continuity_and_causality"] = {"status": "PASS", "reason": f"Shotlar tek bir fiziksel olayın neden-sonuç devamı: {reason_9 or 'Tutarlı kronoloji'}"}
    else:
        results["9_strict_shot_continuity_and_causality"] = {"status": "FAIL", "reason": "Sahne sürekliliği veya neden-sonuç bağı eksik"}
        failures.append("9. Shotlar tek bir olayın fiziksel devamı değil")

    # Kriter 10: İzleyici sonucu önceden tahmin etmeden sonuna kadar izlemek ister mi? (Merak / Tension)
    reason_10 = _get_self_check_reason("10_unpredictable_curiosity_maintained")
    if has_complication and len(critical) >= 15:
        results["10_unpredictable_curiosity_maintained"] = {"status": "PASS", "reason": f"Merak ve belirsizlik son ana kadar korundu: {reason_10 or 'Komplikasyon sonucu tahmin edilemez kılıyor'}"}
    else:
        results["10_unpredictable_curiosity_maintained"] = {"status": "FAIL", "reason": "Merak unsuru zayıf veya sonuç baştan tahmin edilebilir"}
        failures.append("10. Sonuç çok tahmin edilebilir veya merak unsuru eksik")

    # Kriter 11: Başlık sonucu gereksiz şekilde spoiler vermiyor mu? (No-Spoiler Title)
    title_to_check = title or scenario.get("scenario_title", "")
    spoiler_words = ["saved by", "rescued by", "fixed by", "prevents collision", "miracle escape", "survives unharmed", "stops runaway"]
    has_spoiler = any(sp in title_to_check.lower() for sp in spoiler_words)
    reason_11 = _get_self_check_reason("11_no_spoiler_in_title")
    if not has_spoiler and len(title_to_check) > 5:
        results["11_no_spoiler_in_title"] = {"status": "PASS", "reason": f"Başlık tehlike odaklı ve spoiler içermiyor: {title_to_check} ({reason_11 or 'No spoiler'})"}
    else:
        results["11_no_spoiler_in_title"] = {"status": "FAIL", "reason": f"Başlıkta spoiler tespit edildi: {title_to_check}"}
        failures.append("11. Başlık sonucu baştan ele veriyor (spoiler içeriyor)")

    # Kriter 12: Video yalnızca güzel görüntülerden oluşmuyor, başı-sonu olan gerçek bir mikro-olay mı?
    reason_12 = _get_self_check_reason("12_complete_micro_narrative")
    if len(failures) == 0:
        results["12_complete_micro_narrative"] = {"status": "PASS", "reason": f"Başı, tırmanışı, komplikasyonu ve somut sonucu olan tam mikro-hikaye: {reason_12 or 'Tam olay örgüsü'}"}
    else:
        results["12_complete_micro_narrative"] = {"status": "FAIL", "reason": "Eksik anlatı ögeleri var"}
        failures.append("12. Başı ve sonu olan gerçek bir mikro-olay tamamlanmadı")

    # Kriter 13: Kamera açıları ve hareketleri fiziksel olayı en anlaşılır şekilde gösteriyor mu? (Story-Driven Camera)
    has_camera_plan = len(camera_plan) >= 3 or any(
        cam in desc_all.lower() for cam in ["cctv", "camera", "bodycam", "bridge", "lens", "view", "witness", "phone", "quayside", "telephoto"]
    )
    reason_13 = _get_self_check_reason("13_story_driven_camera")
    if has_camera_plan:
        results["13_story_driven_camera"] = {"status": "PASS", "reason": f"Kamera fiziksel aksiyonu en anlaşılır şekilde aktaracak kayıt kaynağından seçildi: {reason_13 or 'STORY -> ACTION -> CAMERA kuralı uygulandı'}"}
    else:
        results["13_story_driven_camera"] = {"status": "FAIL", "reason": "Kamera planı veya fiziksel kayıt kaynağı gerekçesi eksik"}
        failures.append("13. Kamera açıları hikayedeki fiziksel olayı anlaşılır kılacak şekilde kurgulanmamış (Story-Driven Camera eksik)")

    all_passed = (len(failures) == 0)
    return {
        "all_passed": all_passed,
        "results": results,
        "failures": failures,
    }


async def generate_prompts(config: dict) -> dict:
    """Tam otonom 13 kriterli (12+1) ve 5-shot × 3s video prompt pipeline'ı."""
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: 13 kriterli DeepMyster mock promptları üretiliyor...")
        return _dry_run_output()

    used_combos = config.get("used_combos", [])

    # ── ADIM 1: Yaratıcı Olay Seed'i Seç ──
    seed = generate_creative_seed(used_combos)
    log.info(f"🎲 Seed: [{seed['category_label']}] {seed['vessel']} × {seed['incident'][:50]}...")

    # ── ADIM 2: GPT Senaryo Yaz + 13 Kriter Kalite Kontrolü (Hard Quality Gate Loop) ──
    log.info("🤖 GPT-4o'ya 5 shot × 3s (15s) komplikasyonlu mikro-olay senaryosu yazdırılıyor...")
    scenario, validation_data = await _generate_scenario_with_13_validation(seed)
    
    if not validation_data.get("all_passed", False):
        raise ValueError(f"CRITICAL QUALITY GATE FAILURE: Senaryo 13/13 kriteri sağlayamadı: {validation_data.get('failures')}")

    log.info(
        f"📋 Senaryo 13 KRİTERİN TAMAMINDAN GEÇTİ (13/13 PASS): {scenario.get('clip_count', 1)} klip, "
        f"{scenario.get('total_duration', 15)}s | Olay: {scenario.get('scenario_title', 'Maritime Event')}"
    )
    log.info(f"   🔍 Değişim / Payoff: {scenario.get('what_happened_and_what_changed', '')}")

    # ── ADIM 3: Seedance 2 Mini İçin 5 Shot Eylem & Neden-Sonuç Prompt'u ──
    scenes = scenario.get("scenes", [])
    simplified_scenes = []

    for scene in scenes:
        log.info(f"✂️ Sahne {scene['scene_number']}/{len(scenes)} Seedance 2 Mini 5-shot formatına dönüştürülüyor...")
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
        "camera_plan": scenario.get("camera_plan", {}),
        "validation_13_criteria": validation_data,
        "combo_key": seed["combo_key"],
        "total_duration": scenario.get("total_duration", sum(s["duration"] for s in simplified_scenes)),
        "animal": seed["vessel"],
        "talent": seed["incident"],
        "category": seed["category"],
    }

    log.info(f"✅ DeepMyster Pipeline tamamlandı: \"{result['youtube_title']}\"")
    return result


async def _generate_scenario_with_13_validation(seed: dict, max_retries: int = 3) -> tuple[dict, dict]:
    """GPT-4o ile senaryo üretir ve 13 kriterin tamamı (13/13) PASS olana kadar otomatik yeniden yazar (HARD GATE)."""
    feedback = ""
    last_validation = {}

    for attempt in range(max_retries):
        user_message = f"""Create a realistic, dramatic 5-shot × 3-second (Total 15s) maritime micro-story scenario for DeepMyster with AT LEAST ONE UNEXPECTED COMPLICATION:

CATEGORY: {seed.get('category_label', 'Deniz Olayı')}
VESSEL / SUBJECT: {seed.get('vessel', 'cargo ship')}
CORE INCIDENT: {seed.get('incident', 'emergency event in rough sea')}
SETTING / LOCATION: {seed['setting']}
DYNAMICS: {seed['twist']}
CAMERA PERSPECTIVE: {seed.get('camera_perspective', 'quayside CCTV / bridge cam / bodycam footage')}
ACTIVE CREW ROLE: {seed.get('crew_context', 'Active deckhands and officers fighting the crisis')}

MANDATORY 13 RULES & 5-SHOT STRUCTURE:
1. SHOT 1 (0-3s) HOOK: In media res shocking start. No calm establishing shot!
2. SHOT 2 (3-6s) INCIDENT & CREW ACTION: Problem mechanism clear, crew ACTIVELY and PHYSICALLY intervenes (no passive standing!).
3. SHOT 3 (6-9s) ESCALATION & COMPLICATION: Initial fix fails, line snaps, tool slips, or secondary risk emerges! NO simple 1-step fixes!
4. SHOT 4 (9-12s) CRITICAL MOMENT: Decisive high-stakes physical maneuver at danger peak.
5. SHOT 5 (12-15s) VISUAL PAYOFF: Concrete physical change happens on screen.
6. STORY CAUSALITY: Cause -> Action -> Consequence -> Complication -> Critical Action -> Result.
7. STRICT CONTINUITY: Same ship, same crew, same weather, same location across all 15s.
8. STORY-DRIVEN CAMERA: STORY -> ACTION -> CAMERA. Camera frames the essential physical info from a realistic recording source.
9. ANSWER: 'What exactly happened and what physically changed by the end?'
10. NO SPOILERS IN TITLE: Title must highlight danger, never reveal the resolution."""

        if feedback:
            user_message += f"\n\nPREVIOUS ATTEMPT FAILED QUALITY CONTROL (13 CRITERIA):\n{feedback}\nPlease fix these specific failures and regenerate a fully compliant 13/13 PASS micro-story."

        scenario = await _call_gpt(SCENARIO_WRITER_SYSTEM, user_message, temperature=0.85)

        # 13 Kriter Doğrulaması
        validation = validate_scenario_13_criteria(scenario, scenario.get("scenario_title", ""))
        last_validation = validation

        if validation["all_passed"]:
            for scene in scenario.get("scenes", []):
                dur = scene.get("duration", 15)
                scene["duration"] = max(10, min(15, dur))
            return scenario, validation

        feedback = "\n".join(f"- {f}" for f in validation["failures"])
        log.warning(f"⚠️ Senaryo 13 kriter kontrolünden geçemedi (Deneme {attempt+1}/{max_retries}):\n{feedback}")

    log.error("❌ Maksimum senaryo deneme sınırına ulaşıldı — 13/13 PASS sağlanamadı.")
    return scenario, last_validation


async def _simplify_prompt(scene: dict, seed: dict, scenario: dict) -> dict:
    """Katman 3: Seedance 2 Mini için 5-shot eylem + neden-sonuç + ortam sesi prompt'u üret."""
    story_arc = scenario.get("story_arc", {})
    camera_plan = scenario.get("camera_plan", {})
    user_message = f"""Convert this complete maritime micro-story with complication into a 5-shot Seedance 2 Mini prompt:

VESSEL: {seed.get('vessel', 'cargo vessel')}
INCIDENT / CRISIS: {seed.get('incident', 'maritime emergency')}
CAMERA PERSPECTIVE: {seed.get('camera_perspective', 'raw documentary camera footage, natural lighting')}

5-SHOT PROGRESSION:
- Shot 1 (0-3s Hook): {story_arc.get('hook_seconds_0_3', '')} [Cam: {camera_plan.get('shot_1_camera', '')}]
- Shot 2 (3-6s Crew Action): {story_arc.get('incident_seconds_3_6', '')} [Cam: {camera_plan.get('shot_2_camera', '')}]
- Shot 3 (6-9s Complication): {story_arc.get('escalation_and_complication_seconds_6_9', '')} [Cam: {camera_plan.get('shot_3_camera', '')}]
- Shot 4 (9-12s Critical Move): {story_arc.get('critical_moment_seconds_9_12', '')} [Cam: {camera_plan.get('shot_4_camera', '')}]
- Shot 5 (12-15s Physical Payoff): {story_arc.get('resolution_seconds_12_15', '')} [Cam: {camera_plan.get('shot_5_camera', '')}]
- Physical State Change: {scenario.get('what_happened_and_what_changed', '')}

SCENE DESCRIPTION: {scene.get('description', '')}

CRITICAL RULES FOR SEEDANCE 2 MINI:
- Output 35-55 words in chronological 5-shot format or single continuous narrative.
- Each shot must connect: CAMERA + SUBJECT + ACTION + CAUSE/CONTINUITY + DIEGETIC AUDIO.
- Photorealistic raw documentary footage, natural lighting, ambient environmental sounds."""

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
HOOK (0-3s): {story_arc.get('hook_seconds_0_3', '')}
COMPLICATION (6-9s): {story_arc.get('escalation_and_complication_seconds_6_9', '')}
CRITICAL MOMENT (9-12s): {story_arc.get('critical_moment_seconds_9_12', '')}

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
    """DRY-RUN modunda 13 kriterin tamamını karşılayan 5 shot × 3s (15s) komplikasyonlu mock çıktısı."""
    mock_scenario = {
        "scenario_title": "⚠️ Rogue Wave Hits Ferry Deck Snapping Heavy Lashing",
        "what_happened_and_what_changed": "A 40ft rogue swell snapped trailer lashings on a rolling vehicle deck; the primary emergency chain hook slipped under tension, but two deckhands dove across flooded plates to jam heavy steel chocks under front tires, locking the runaway truck 2 feet before hull collision.",
        "story_arc": {
            "hook_seconds_0_3": "A violent rolling swell snaps the primary trailer lashing chain with a sharp metallic crack on the wet ferry deck as the truck lurches sideways.",
            "incident_seconds_3_6": "The freight truck slides toward the companionway while two deckhands in yellow suits sprint across flooded steel plates hauling an emergency chain.",
            "escalation_and_complication_seconds_6_9": "The deckhand attempts to latch the backup hook, but the chain slips under the shifting weight, pivoting the trailer dangerously toward the outer hull.",
            "critical_moment_seconds_9_12": "Both deckhands dive across the waterlogged deck and kick heavy steel chocks directly under the sliding front tires.",
            "resolution_seconds_12_15": "The steel chocks bite firmly into deck plates with loud screeching friction, locking the freight truck abruptly two feet before hull impact."
        },
        "camera_plan": {
            "shot_1_camera": "Vehicle deck CCTV surveillance camera framing sudden chain snap and truck shift at 0-3s",
            "shot_2_camera": "Deckhand chest bodycam rushing forward showing physical crew intervention at 3-6s",
            "shot_3_camera": "Wide companionway safety camera capturing hook slip and trailer pivoting at 6-9s",
            "shot_4_camera": "Low-angle deck camera framing deckhands diving with steel chocks at 9-12s",
            "shot_5_camera": "Quayside/hull perspective framing chocks locking tires inches from wall at 12-15s"
        },
        "quality_self_check_13": {
            "1_strong_hook_0_3s": {"pass": True, "reason": "Olay ilk karede lashing zincirinin kopmasıyla in media res başlamış"},
            "2_clear_problem_3_6s": {"pass": True, "reason": "Kayan tır ve su basan güverte tehlike mekanizmasını net kuruyor"},
            "3_active_crew_physical_action": {"pass": True, "reason": "İki güverte personeli aktif beden gücüyle koşuyor, zincir taşıyor ve çock takoz çakıyor"},
            "4_genuine_escalation": {"pass": True, "reason": "Tırın güverteye doğru kontrolsüz kayması gerilimi artırıyor"},
            "5_unexpected_complication_6_9s": {"pass": True, "reason": "Yedek zincir kancası yük altında kayarak tırı bordaya doğru savuruyor"},
            "6_critical_moment_9_12s": {"pass": True, "reason": "Personelin ıslak sac üzerinde dalarak ön teker altına çelik takoz sokması"},
            "7_visible_physical_resolution_12_15s": {"pass": True, "reason": "Takozların sacı ısırıp tırı bordaya 2 fit kala kilitlemesi ekranda somut gerçekleşiyor"},
            "8_clear_what_changed_physically": {"pass": True, "reason": "Serbest kayan tır kilitlendi ve borda delinmesi önlendi"},
            "9_strict_shot_continuity_and_causality": {"pass": True, "reason": "5 shot aynı feribotta kesintisiz neden-sonuç zinciriyle birbirine bağlı"},
            "10_unpredictable_curiosity_maintained": {"pass": True, "reason": "Kancanın kayması sonucu belirsiz kılıyor ve izleyiciyi son ana kadar tutuyor"},
            "11_no_spoiler_in_title": {"pass": True, "reason": "Başlık yalnızca krize ve kopan zincire odaklanıyor, durdurulduğunu söylemiyor"},
            "12_complete_micro_narrative": {"pass": True, "reason": "Başı, gelişimi, komplikasyonu ve somut payoff'u olan tam bir mikro-olay"},
            "13_story_driven_camera": {"pass": True, "reason": "Kamera CCTV ve bodycam açılarıyla fiziksel aksiyonu en anlaşılır şekilde gösteriyor"}
        },
        "scenes": [
            {
                "scene_number": 1,
                "description": "Continuous 15-second physical action: rolling swell snaps trailer chain, yellow-suited deckhands sprint with emergency gear, hook slips pivoting trailer toward hull, crew dives to kick steel chocks under tires, locking the truck 2 feet before hull collision.",
                "duration": 15
            }
        ]
    }
    validation = validate_scenario_13_criteria(mock_scenario, mock_scenario["scenario_title"])
    return {
        "scenes": [
            {
                "scene_number": 1,
                "prompt": "SHOT 1 (0-3s): Deck CCTV captures violent wave snapping ferry trailer lashing with metallic crack. SHOT 2 (3-6s): Yellow-suited deckhands sprint across flooded plates hauling emergency chain. SHOT 3 (6-9s): Hook slips under load as trailer pivots toward hull. SHOT 4 (9-12s): Deckhands dive and jam heavy steel chocks under front tires. SHOT 5 (12-15s): Chocks bite firmly, locking trailer two feet before hull impact. Photorealistic raw documentary footage, natural lighting, ambient storm audio.",
                "duration": 15,
            }
        ],
        "youtube_title": "⚠️ Rogue Wave Hits Ferry Deck Snapping Heavy Lashing #Shorts",
        "youtube_description": "Watch deckhands battle an escalating freight trailer crisis in heavy 40ft open seas as primary lashings fail on a rolling ferry. DeepMyster Official. #DeepMyster #Shorts #Maritime #RoughSeas",
        "tags": ["DeepMyster", "Shorts", "Maritime", "RoughSeas", "CargoShip", "Storm", "Ocean", "Crew", "Rescue"],
        "scenario_summary": "Deckhands battle shifting trailer after primary hook slips, kicking steel chocks to halt runaway truck before hull collision.",
        "what_happened_and_what_changed": mock_scenario["what_happened_and_what_changed"],
        "story_arc": mock_scenario["story_arc"],
        "camera_plan": mock_scenario["camera_plan"],
        "validation_13_criteria": validation,
        "combo_key": "roro_accidents|large car and passenger ferry|Violent swell snaps primary trailer lashing",
        "total_duration": 15,
        "animal": "large car and passenger ferry",
        "talent": "Violent swell snaps primary trailer lashing",
        "category": "roro_accidents",
    }

