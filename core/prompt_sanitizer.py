from __future__ import annotations

"""
Prompt Sanitizer — İçerik Güvenliği Katmanı (DeepMyster).

Kie AI (Seedance 2.0 / Seedance 2 Mini) modellerinin content safety filtresini
tetikleyebilecek ifadeleri prompt gönderilmeden ÖNCE yumuşatır.

3 Katmanlı Savunma:
  1. Regex — Bilinen tehlikeli terimleri hızlıca yakalar (sync, <1ms)
  2. GPT Pre-flight — Prompt'u GPT'ye "bu reddedilir mi?" diye sorar (async, ~2s)
     → Reddedilecekse GPT aynı anda güvenli versiyonunu da yazar
  3. GPT Retry Rewrite — Reddedildikten sonra rejection reason ile GPT'ye
     "aynı denizcilik olayını güvenli şekilde yeniden yaz" komutu verir
"""
import re
import json
import logging

log = logging.getLogger("PromptSanitizer")

# ── Tehlikeli terim → güvenli alternatif eşlemeleri (Denizcilik Odaklı) ──
REPLACEMENT_RULES = [
    # Suç / Hırsızlık
    (r"\bsteal(?:s|ing)?\b", "retrieve", "hırsızlık→alma"),
    (r"\bstole\b", "took", "hırsızlık→alma"),
    (r"\btheft\b", "incident", "hırsızlık→olay"),
    (r"\bthief\b", "trespasser", "hırsız→izinsiz giren"),
    (r"\brob(?:s|bing|bed)?\b", "secure", "soygun→güvenceye alma"),
    (r"\bcrime\b", "emergency", "suç→acil durum"),
    (r"\bcriminal\b", "troublemaker", "suçlu→sorun çıkaran"),

    # Silah / Şiddet / Kan
    (r"\bgun(?:s)?\b", "flare gun", "silah→işaret fişeği tabancası"),
    (r"\bweapon(?:s)?\b", "tool", "silah→alet"),
    (r"\bknife\b", "rigging knife", "bıçak→halat bıçağı"),
    (r"\bknives\b", "rigging tools", "bıçaklar→donanım aletleri"),
    (r"\bblood(?:y)?\b", "sea spray", "kan→deniz serpintisi"),
    (r"\bviolence\b", "extreme storm tension", "şiddet→fırtına gerilimi"),
    (r"\bviolent\b", "severe", "şiddetli→sert"),
    (r"\bfight(?:s|ing)?\b", "battle", "kavga→mücadele"),
    (r"\battack(?:s|ing|ed)?\b", "surge toward", "saldırı→üzerine kabarma"),
    (r"\bkill(?:s|ing|ed)?\b", "sweep away", "öldürme→sürükleme"),
    (r"\bdrown(?:s|ed|ing)?\b", "struggle in water", "boğulma→suda mücadele"),
    (r"\bcorpse(?:s)?\b", "debris", "ceset→enkaz"),
    (r"\bdead\b", "unresponsive", "ölü→tepkisiz"),

    # Fantastik / Yapay öğeler (DeepMyster gerçekçilik koruması)
    (r"\b(?:glowing|luminous|radiant)\b", "storm-lit", "parıltı→fırtına ışığı"),
    (r"\b(?:mystical|magical|magic|supernatural)\b", "dramatic", "mistik→dramatik"),
    (r"\b(?:artifact|runes|relic|totem)\b", "equipment", "eser/rün→ekipman"),
    (r"\b(?:sci-fi|futuristic|alien)\b", "industrial", "bilimkurgu→endüstriyel"),
    (r"\b(?:obsidian|crystal|fantasy)\b", "steel", "obsidyen/fantezi→çelik"),
    (r"\b(?:anime|cgi|3d render|unreal engine)\b", "photorealistic", "animasyon/cgi→fotogerçekçi"),
]

# ── Yüksek riskli pattern'ler ──
HIGH_RISK_PATTERNS = [
    (r"\bchild(?:ren)? .{0,30}(?:danger|harm|hurt|injur)", "Çocuk+tehlike"),
    (r"\bbaby .{0,30}(?:danger|harm|hurt|fall)", "Bebek+tehlike"),
]

# ── GPT Pre-flight System Prompt ──
_PREFLIGHT_SYSTEM = """You are a content safety evaluator for AI video generation models (Seedance 2.0 / Seedance 2 Mini).

Your job: Evaluate if a realistic maritime documentary video prompt would be REJECTED by an AI model's safety filter.

AI video models reject prompts containing:
- Graphic human injury, gore, blood, or death
- Real weapon violence, shooting, stabbing
- Children in perilous life-threatening situations
- Explicit sexual content or nudity
- Illegal drug trafficking

CRITICAL MARITIME CONTEXT:
- Authentic maritime emergencies (e.g. ship battling storm waves, deckhands securing shifting cargo, marina staff deploying fenders, emergency towing, crew extinguishing an engine room fire, rescue swimmers pulling seamen to safety) are SAFE and PERMISSIBLE as long as there is no blood, gore, or graphic death.

Respond in JSON:
{
  "safe": true/false,
  "risk_score": 1-10 (1=completely safe, 10=definitely rejected),
  "risk_reasons": ["reason1"],
  "rewritten_prompt": "only if safe=false: rewrite preserving the SAME maritime incident, kinetic action, human roles, and concrete resolution, but replacing unsafe words (blood, kill, gore) with realistic safe maritime operations terminology (spray, secure, rescue)."
}"""

# ── GPT Retry Rewrite System Prompt ──
_RETRY_REWRITE_SYSTEM = """You are a prompt repair specialist for AI video generation (Seedance 2 Mini).

A realistic maritime documentary video prompt was REJECTED by the AI model's content safety filter.
The model returned this rejection reason: "{rejection_reason}"

Your job: Rewrite the prompt to tell the EXACT SAME realistic maritime micro-story (problem → crew action → concrete resolution) with ZERO content safety risks.

RULES:
- Maintain 100% photorealistic documentary maritime realism.
- Remove any graphic words (blood, death, kill, violent attack).
- Keep active crew members, vessel maneuvers, storm elements, and concrete payoff/resolution.
- Keep the prompt between 25-45 words.
- End with 'Photorealistic raw documentary footage, natural lighting.'
- Output ONLY the rewritten prompt text, no JSON, no explanation."""


def sanitize_prompt(prompt: str) -> tuple[str, list[str]]:
    """Video prompt'unu içerik güvenliği açısından temizler (SYNC — regex tabanlı)."""
    changes = []
    sanitized = prompt

    for pattern, replacement, description in REPLACEMENT_RULES:
        matches = re.findall(pattern, sanitized, flags=re.IGNORECASE)
        if matches:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            changes.append(f"{description}: '{matches[0]}' -> '{replacement}'")

    for pattern, risk_name in HIGH_RISK_PATTERNS:
        if re.search(pattern, sanitized, flags=re.IGNORECASE):
            log.warning(f"⚠️ Yüksek riskli pattern tespit edildi: {risk_name}")
            changes.append(f"⚠️ UYARI: {risk_name}")

    if changes:
        log.info(f"🛡️ Prompt sanitize edildi — {len(changes)} değişiklik:")
        for change in changes:
            log.info(f"   • {change}")
    else:
        log.info("✅ Prompt güvenli — değişiklik gerekmedi")

    return sanitized, changes


def create_softened_prompt(original_prompt: str) -> str:
    """Content filter tarafından reddedilen bir prompt'un yumuşatılmış versiyonunu üretir."""
    softened, _ = sanitize_prompt(original_prompt)

    aggressive_replacements = [
        (r"\bviolent\b", "severe"),
        (r"\bpanic\b", "urgency"),
        (r"\bdesperate\b", "rapid"),
        (r"\bchaos\b", "high winds"),
        (r"\bcrash(?:es|ing)?\b", "impact"),
    ]

    for pattern, replacement in aggressive_replacements:
        softened = re.sub(pattern, replacement, softened, flags=re.IGNORECASE)

    if "photorealistic" not in softened.lower():
        softened += " Photorealistic raw documentary footage, natural lighting."

    log.info("🛡️ Agresif yumuşatma uygulandı (regex fallback)")
    return softened


async def gpt_preflight_check(prompt: str) -> tuple[str, bool, dict]:
    """GPT Pre-flight Safety Check — Kie AI'a göndermeden ÖNCE prompt'u değerlendirir."""
    from config import settings

    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: GPT pre-flight atlanıyor")
        return prompt, False, {"risk_score": 0, "risk_reasons": [], "dry_run": True}

    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _PREFLIGHT_SYSTEM},
                {"role": "user", "content": f"Evaluate this video prompt:\n\n{prompt}"},
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        risk_score = result.get("risk_score", 1)
        is_safe = result.get("safe", True)
        risk_reasons = result.get("risk_reasons", [])

        metadata = {
            "risk_score": risk_score,
            "risk_reasons": risk_reasons,
            "preflight_passed": is_safe,
        }

        if is_safe or risk_score <= 4:
            log.info(f"✅ GPT Pre-flight: GÜVENLİ (skor: {risk_score}/10)")
            return prompt, False, metadata

        rewritten = result.get("rewritten_prompt", "")
        if rewritten and len(rewritten) > 20:
            log.warning(
                f"🛡️ GPT Pre-flight: RİSKLİ (skor: {risk_score}/10) — "
                f"Sebepler: {', '.join(risk_reasons)}"
            )
            log.info(f"   ✏️ GPT yeniden yazdı: {rewritten[:100]}...")
            metadata["rewritten"] = True
            return rewritten, True, metadata

        log.warning(f"⚠️ GPT Pre-flight: riskli ama rewrite üretemedi (skor: {risk_score})")
        return prompt, False, metadata

    except Exception as e:
        log.warning(f"⚠️ GPT Pre-flight hatası (atlanıyor): {e}")
        return prompt, False, {"risk_score": -1, "error": str(e)}


async def gpt_rewrite_rejected_prompt(
    original_prompt: str,
    rejection_reason: str,
) -> str:
    """GPT-Powered Retry Rewrite — Reddedilmiş prompt'u güvenli şekilde yeniden yazar."""
    from config import settings

    if settings.IS_DRY_RUN:
        log.info("🧪 DRY-RUN: GPT rewrite atlanıyor, regex fallback kullanılıyor")
        return create_softened_prompt(original_prompt)

    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        system = _RETRY_REWRITE_SYSTEM.format(rejection_reason=rejection_reason)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Rewrite this rejected maritime prompt:\n\n{original_prompt}"},
            ],
            temperature=0.7,
            max_tokens=300,
        )

        rewritten = response.choices[0].message.content.strip()

        if not rewritten or len(rewritten) < 20:
            log.warning("⚠️ GPT rewrite çok kısa — regex fallback kullanılıyor")
            return create_softened_prompt(original_prompt)

        if rewritten.startswith("{") or rewritten.startswith('"'):
            try:
                parsed = json.loads(rewritten)
                if isinstance(parsed, dict):
                    rewritten = parsed.get("prompt", parsed.get("rewritten_prompt", rewritten))
                elif isinstance(parsed, str):
                    rewritten = parsed
            except json.JSONDecodeError:
                pass

        if "photorealistic" not in rewritten.lower():
            rewritten += " Photorealistic raw documentary footage, natural lighting."

        log.info(f"✏️ GPT Retry Rewrite başarılı: {rewritten[:100]}...")
        return rewritten

    except Exception as e:
        log.warning(f"⚠️ GPT rewrite hatası — regex fallback: {e}")
        return create_softened_prompt(original_prompt)
