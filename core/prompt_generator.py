from __future__ import annotations

"""
Prompt Generator V3 — "Pets Got Talent" Tam Otonom Pipeline.

Creative Engine'den seed alır → GPT-4.1 ile senaryo yazar →
Sora/Seedance-optimize basit prompt'a dönüştürür.

Dinamik klip sayısı ve süre: GPT hikayenin yapısına göre karar verir.
Ses her zaman açık, konuşma/diyalog asla yok.
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
        return "Extreme Rough Seas Battles Ship #Shorts"
    # Baştaki DeepMyster:, DeepMyster -, [DeepMyster], DeepMyster | gibi kalıpları temizle
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
            if _openai_client is None:  # Double-check locking
                _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


async def _call_gpt(system_prompt: str, user_message: str, temperature: float = 0.95) -> dict:
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
            max_tokens=1500,
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


async def generate_prompts(config: dict) -> dict:
    """
    Tam otonom video prompt pipeline'ı.

    Akış:
      1. Creative Engine → seed (hayvan + yetenek + sahne)
      2. GPT → senaryo (kaç klip, kaç saniye, ne oluyor)
      3. GPT → her sahne için Seedance-optimize basit prompt
      4. GPT → YouTube metadata (title, description, tags)
      5. Safety sanitizer → son güvenlik kontrolü

    Args:
        config: {
            "used_combos": ["animal|talent", ...],  # tekrar önleme
        }

    Returns:
        dict: {
            "scenes": [{"scene_number": 1, "prompt": "...", "duration": 10}, ...],
            "youtube_title": "...",
            "youtube_description": "...",
            "tags": [...],
            "scenario_summary": "...",
            "combo_key": "animal|talent",
            "total_duration": 25,
        }
    """
    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: Mock promptlar üretiliyor...")
        return _dry_run_output()

    used_combos = config.get("used_combos", [])

    # ── ADIM 1: Yaratıcı Seed Seç ──
    seed = generate_creative_seed(used_combos)
    log.info(f"🎲 Seed: {seed['animal']} × {seed['talent']}")

    # ── ADIM 2: GPT Senaryo Yaz ──
    log.info("🤖 GPT-4.1'e senaryo yazdırılıyor...")
    scenario = await _generate_scenario(seed)
    log.info(
        f"📋 Senaryo hazır: {scenario.get('clip_count', 1)} klip, "
        f"{scenario.get('total_duration', 10)}s"
    )

    # ── ADIM 3: Her Sahne İçin Seedance-Optimize Prompt ──
    scenes = scenario.get("scenes", [])
    simplified_scenes = []

    for scene in scenes:
        log.info(f"✂️ Sahne {scene['scene_number']}/{len(scenes)} simplify ediliyor...")
        simplified = await _simplify_prompt(scene, seed)
        simplified_scenes.append({
            "scene_number": scene["scene_number"],
            "prompt": simplified["prompt"],
            "duration": scene.get("duration", 10),
        })
        word_count = len(simplified["prompt"].split())
        log.info(f"   → {word_count} kelime: {simplified['prompt'][:80]}...")

    # ── ADIM 4: YouTube Metadata ──
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
        "youtube_title": clean_youtube_title(metadata.get("youtube_title", "Massive Waves Battle Ship at Sea #Shorts")),
        "youtube_description": metadata.get("youtube_description", ""),
        "tags": metadata.get("tags", ["DeepMyster", "Shorts", "Maritime", "RoughSeas"]),
        "scenario_summary": scenario.get("scenario_summary", ""),
        "combo_key": seed["combo_key"],
        "total_duration": scenario.get("total_duration", sum(s["duration"] for s in simplified_scenes)),
        "animal": seed["animal"],
        "talent": seed["talent"],
        "category": seed["category"],
    }

    log.info(f"✅ Pipeline tamamlandı: \"{result['youtube_title']}\"")
    log.info(f"   {len(simplified_scenes)} sahne, toplam {result['total_duration']}s")

    return result


async def _generate_scenario(seed: dict) -> dict:
    """Katman 2: GPT-4o ile gerçekçi denizcilik senaryosu üret."""
    user_message = f"""Create a realistic, dramatic maritime incident scenario for DeepMyster:

CATEGORY: {seed.get('category_label', 'Deniz Olayı')}
VESSEL / SUBJECT: {seed.get('vessel', seed.get('animal', 'cargo ship'))}
INCIDENT: {seed.get('incident', seed.get('talent', 'battling storm swells'))}
SETTING / LOCATION: {seed['setting']}
DYNAMICS: {seed['twist']}
CAMERA PERSPECTIVE: {seed.get('camera_perspective', 'raw documentary camera footage')}
CREW / HUMAN CONTEXT: {seed.get('crew_context', 'Active crew members responding to the crisis')}

Rules:
- 100% REALISTIC, physically plausible maritime incident.
- MANDATORY HUMAN / CREW PRESENCE: Every single scenario MUST prominently feature at least one human/crew member actively engaged in the situation (captain, deckhand, dockworker, marina staff, passenger, rescue crew, or marine engineer). Crewless/unmanned videos are STRICTLY FORBIDDEN.
- Humans must NOT be passive props; they must actively manage, brace, secure equipment, steer, or respond to the crisis.
- Real hydrodynamics, raw documentary footage feel, authentic human actions and vessel movements.
- DIVERSIFY human roles and camera perspectives; avoid repetitive templates.
- NO spoken dialogue, NO text overlays, NO narration.
- 1 single continuous 15-second dramatic shot."""

    result = await _call_gpt(SCENARIO_WRITER_SYSTEM, user_message, temperature=0.95)

    # Doğrulama
    if "scenes" not in result or not result["scenes"]:
        raise ValueError(f"GPT senaryo yanıtında 'scenes' eksik: {result}")

    # Clip süreleri Seedance limitleri içinde mi?
    for scene in result["scenes"]:
        dur = scene.get("duration", 15)
        if dur < 8:
            scene["duration"] = 8
        elif dur > 15:
            scene["duration"] = 15

    return result


async def _simplify_prompt(scene: dict, seed: dict) -> dict:
    """Katman 3: Sahne açıklamasını Seedance-optimize kısa prompt'a çevir."""
    user_message = f"""Simplify this maritime scene into a Seedance 2.0 video prompt:

SUBJECT: {seed.get('vessel', seed.get('animal', 'vessel'))}
SCENE DESCRIPTION: {scene['description']}
CAMERA STYLE: {seed.get('camera_perspective', 'raw documentary camera footage, natural lighting')}

CRITICAL RULE: The simplified prompt MUST explicitly feature at least one human/crew member (e.g. deckhand, captain, dockworker, passenger, marina staff, rescue crew, engineer) actively involved in the kinetic action. Unmanned / crewless prompts are strictly forbidden.
Output a SHORT prompt (15-30 words max). No dialogue. Direct visual action with raw realism."""

    result = await _call_gpt(PROMPT_SIMPLIFIER_SYSTEM, user_message, temperature=0.7)

    if "prompt" not in result:
        raise ValueError(f"Simplifier yanıtında 'prompt' eksik: {result}")

    return result


async def _generate_metadata(scenario: dict, seed: dict) -> dict:
    """YouTube title, description, tags üret."""
    user_message = f"""Create YouTube Shorts metadata for this maritime video:

VESSEL: {seed.get('vessel', seed.get('animal', 'vessel'))}
INCIDENT: {seed.get('incident', seed.get('talent', 'incident'))}
CATEGORY: {seed.get('category_label', 'Maritime Incident')}
SCENARIO: {scenario.get('scenario_summary', '')}
TOTAL DURATION: {scenario.get('total_duration', 15)} seconds"""

    result = await _call_gpt(YOUTUBE_METADATA_SYSTEM, user_message, temperature=0.8)

    # Başlığı temizle ("DeepMyster:" vb. önekleri kaldır)
    raw_title = result.get("youtube_title", "")
    result["youtube_title"] = clean_youtube_title(raw_title)

    # Tags'e sabit olanları ekle
    tags = result.get("tags", [])
    mandatory_tags = ["DeepMyster", "Shorts", "Maritime", "RoughSeas", "Ocean", "Crew"]
    for tag in mandatory_tags:
        if tag not in tags:
            tags.append(tag)
    result["tags"] = tags

    return result


def _dry_run_output() -> dict:
    """DRY-RUN modunda mock çıktı (DeepMyster)."""
    return {
        "scenes": [
            {
                "scene_number": 1,
                "prompt": "[DRY-RUN] A large cargo ship rolls heavily in 40-foot storm waves as deck crew in foul weather gear battle across flooded deck to secure equipment. Photorealistic, raw documentary camera footage, natural lighting.",
                "duration": 15,
            }
        ],
        "youtube_title": "[DRY-RUN] 🌊 Deck Crew Battles 40ft Storm Waves on Cargo Ship #Shorts",
        "youtube_description": "Watch the deck crew battle extreme ocean swells in the storm-tossed North Atlantic. DeepMyster Official.",
        "tags": ["DeepMyster", "Shorts", "Maritime", "RoughSeas", "CargoShip", "Storm", "Ocean", "Crew"],
        "scenario_summary": "Deck crew secures equipment as a large cargo ship navigates through massive oceanic storm waves",
        "combo_key": "large container ship|deckhands securing equipment in massive 40-foot oceanic swells",
        "total_duration": 15,
        "animal": "large container ship",
        "talent": "deckhands securing equipment in massive 40-foot oceanic swells",
        "category": "rough_seas_storms",
    }
