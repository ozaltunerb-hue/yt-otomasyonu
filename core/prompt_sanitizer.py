from __future__ import annotations

"""
Prompt Sanitizer — İçerik Güvenliği Katmanı (DeepMyster Doğukan Standardı).

Kie AI (Seedance 2 Mini) modellerinin content safety filtresini
tetikleyebilecek gerçek riskli unsurları (kan, açık şiddet, uzuv zararı, çocuk tehlikesi)
prompt gönderilmeden ÖNCE temizler veya yumuşatır; doğal denizcilik gerilimini
(dalga çarpması, sürtünme, yük kayması) korur.

3 Katmanlı Savunma:
  1. Regex — Gerçek riskli terimleri güvenli denizcilik operasyon terimlerine çevirir (sync, <1ms)
  2. GPT Pre-flight — Prompt'u GPT ile değerlendirir (async, ~2s)
     → Riskli ise 25–45 kelimelik güvenli versiyonunu üretir
  3. GPT Retry Rewrite — Model reddederse 25–45 kelimede güvenli yeniden yazma
"""
import re
import json
import logging

log = logging.getLogger("PromptSanitizer")

# ── Gerçekten riskli terim → güvenli alternatif eşlemeleri ──
REPLACEMENT_RULES = [
    # Suç / Hırsızlık
    (r"\bsteal(?:s|ing)?\b", "retrieve", "hırsızlık→alma"),
    (r"\bstole\b", "took", "hırsızlık→alma"),
    (r"\btheft\b", "incident", "hırsızlık→olay"),
    (r"\bthief\b", "trespasser", "hırsız→izinsiz giren"),
    (r"\brob(?:s|bing|bed)?\b", "secure", "soygun→güvenceye alma"),
    (r"\bcrime\b", "emergency", "suç→acil durum"),
    (r"\bcriminal\b", "troublemaker", "suçlu→sorun çıkaran"),

    # Silah / Gerçek İnsan Şiddeti / Kan
    (r"\bgun(?:s)?\b", "flare gun", "silah→işaret fişeği tabancası"),
    (r"\bweapon(?:s)?\b", "tool", "silah→alet"),
    (r"\bknife\b", "rigging tool", "bıçak→halat aleti"),
    (r"\bknives\b", "rigging tools", "bıçaklar→donanım aletleri"),
    (r"\bblood(?:y)?\b", "sea spray", "kan→deniz serpintisi"),
    (r"\bphysical fight(?:s|ing)?\b", "struggle", "kavga→mücadele"),
    (r"\bhuman attack(?:s|ing|ed)?\b", "confrontation", "saldırı→yüzleşme"),
    (r"\bkill(?:s|ing|ed)?\b", "sweep away", "öldürme→sürükleme"),
    (r"\bdrown(?:s|ed|ing)?\b", "struggle in water", "boğulma→suda mücadele"),
    (r"\bcorpse(?:s)?\b", "debris", "ceset→enkaz"),
    (r"\bdead body\b", "unresponsive crewman", "ölü beden→tepkisiz personel"),

    # Yapay / Fantezi / CGI öğeler
    (r"\b(?:glowing|luminous|radiant)\b", "storm-lit", "parıltı→fırtına ışığı"),
    (r"\b(?:mystical|magical|magic|supernatural)\b", "dramatic", "mistik→dramatik"),
    (r"\b(?:artifact|runes|relic|totem)\b", "equipment", "eser/rün→ekipman"),
    (r"\b(?:sci-fi|futuristic|alien)\b", "industrial", "bilimkurgu→endüstriyel"),
    (r"\b(?:obsidian|crystal|fantasy)\b", "steel", "obsidyen/fantezi→çelik"),
    (r"\b(?:anime|cgi|3d render|unreal engine|cinematic drone)\b", "raw footage", "yapay→ham görüntü"),
]

# ── Yüksek riskli pattern'ler ──
HIGH_RISK_PATTERNS = [
    (r"\bchild(?:ren)? .{0,30}(?:danger|harm|hurt|injur)", "Çocuk+tehlike"),
    (r"\bbaby .{0,30}(?:danger|harm|hurt|fall)", "Bebek+tehlike"),
]

# ── GPT Pre-flight System Prompt ──
_PREFLIGHT_SYSTEM = """You are a content safety evaluator for AI video generation models (Seedance 2 Mini).

Your job: Evaluate if a realistic maritime CCTV/documentary video prompt would be REJECTED by an AI model's safety filter.

AI video models reject prompts containing:
- Graphic human injury, gore, blood, or death
- Real weapon violence, shooting, stabbing
- Children in perilous situations
- Explicit sexual content or nudity

CRITICAL MARITIME CONTEXT (SEPARATE CREATIVITY FROM SAFETY):
- Authentic maritime weather and heavy machinery emergencies (e.g. ferry rolling in storm, green swells swamping the vehicle deck, secured cars breaking loose, mooring lines snapping at a marina, drydock flooding under a yacht on a slipway, crane boom swinging, tornadoes, people evacuating) are 100% SAFE. Do not sterilize dramatic physical action unless it explicitly depicts graphic injuries, blood, or gore.

Respond in JSON:
{
  "safe": true/false,
  "risk_score": 1-10 (1=completely safe, 10=definitely rejected),
  "risk_reasons": ["reason1"],
  "rewritten_prompt": "only if safe=false: output the EXACT original prompt with ONLY the minimum local edits necessary to remove the safety risk. DO NOT rewrite the entire prompt. Preserve all camera instructions, environments, events, audio, and visual details perfectly."
}"""

# ── GPT Retry Rewrite System Prompt ──
_RETRY_REWRITE_SYSTEM = """You are a prompt repair specialist for AI video generation (Seedance 2 Mini).

A realistic maritime CCTV/documentary video prompt was REJECTED by the AI model's content safety filter.
Rejection reason: "{rejection_reason}"

Your job: Rewrite the prompt to capture the SAME realistic maritime incident with ZERO content safety risks.

RULES:
- Maintain 100% CCTV / raw surveillance documentary realism.
- Remove any graphic words (blood, death, kill, violent human attack).
- Apply the minimum local edits necessary to fix the rejection reason.
- DO NOT rewrite the entire prompt. Preserve all original camera instructions, environments, events, audio, and visual details perfectly.
- Output ONLY the fixed prompt text, no JSON, no explanation."""


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
        (r"\bpanic\b", "urgency"),
        (r"\bdesperate\b", "rapid"),
        (r"\bchaos\b", "heavy gale"),
    ]

    for pattern, replacement in aggressive_replacements:
        softened = re.sub(pattern, replacement, softened, flags=re.IGNORECASE)

    if "surveillance" not in softened.lower() and "cctv" not in softened.lower():
        softened += " Raw CCTV footage, natural lighting."

    log.info("🛡️ Yumuşatma uygulandı (regex fallback)")
    return softened


PREFLIGHT_MAX_RETRIES = 2  # toplam 1 + 2 = 3 deneme


class PreflightError(RuntimeError):
    """Pre-flight güvenlik kontrolü tüm denemelerde geçerli sonuç üretemedi; prompt Kie'ye gitmez."""


def _parse_preflight(raw: str) -> dict:
    """GPT preflight cevabını doğrular. Eksik/bozuk alan = başarısız kontrol (ValueError).

    Eskiden bozuk JSON ve eksik 'safe' alanı sessizce 'güvenli' sayılıyordu (2026-09-24 TUR 7).
    """
    try:
        result = json.loads(raw or "")
    except json.JSONDecodeError as e:
        raise ValueError(f"bozuk JSON: {e}")
    if not isinstance(result, dict):
        raise ValueError("JSON nesne değil")
    if not isinstance(result.get("safe"), bool):
        raise ValueError("'safe' alanı eksik veya bool değil")
    score = result.get("risk_score")
    if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 10:
        raise ValueError(f"'risk_score' 1-10 arası tamsayı değil: {score!r}")
    if not result["safe"] and score > 4:
        rewritten = result.get("rewritten_prompt")
        if not isinstance(rewritten, str) or len(rewritten.strip()) <= 20:
            raise ValueError("riskli (safe=false, skor>4) ama 'rewritten_prompt' yok/çok kısa")
    return result


async def gpt_preflight_check(prompt: str) -> tuple[str, bool, dict]:
    """GPT Pre-flight Safety Check — Kie AI'a göndermeden ÖNCE prompt'u değerlendirir.

    API hatası, bozuk JSON veya eksik alan başarısız kontroldür: hata sebebi GPT'ye
    söylenerek 1 + PREFLIGHT_MAX_RETRIES kez denenir, hiçbiri geçmezse PreflightError.
    Sessiz geçiş yok.
    """
    from config import settings
    import openai
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    user_msg = f"Evaluate this CCTV video prompt:\n\n{prompt}"
    errors = []
    result = None
    for attempt in range(1 + PREFLIGHT_MAX_RETRIES):
        content = user_msg
        if errors:
            content += (f"\n\nYour previous answer was invalid ({errors[-1]}). Respond with ONE complete JSON "
                        f"object with all required fields: safe (bool), risk_score (int 1-10), risk_reasons, "
                        f"and rewritten_prompt when safe=false.")
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": _PREFLIGHT_SYSTEM},
                    {"role": "user", "content": content},
                ],
                temperature=0.3,
                max_tokens=400,
                response_format={"type": "json_object"},
            )
            result = _parse_preflight(response.choices[0].message.content)
            break
        except Exception as e:
            errors.append(str(e))
            log.warning(f"⚠️ GPT Pre-flight geçersiz (deneme {attempt + 1}/{1 + PREFLIGHT_MAX_RETRIES}): {e}")

    if result is None:
        raise PreflightError(f"GPT Pre-flight {1 + PREFLIGHT_MAX_RETRIES} denemede geçerli sonuç vermedi: {errors}")

    risk_score = result["risk_score"]
    risk_reasons = result.get("risk_reasons", [])
    metadata = {
        "risk_score": risk_score,
        "risk_reasons": risk_reasons,
        "preflight_passed": result["safe"],
        "attempts": len(errors) + 1,
    }

    if result["safe"] or risk_score <= 4:
        log.info(f"✅ GPT Pre-flight: GÜVENLİ (skor: {risk_score}/10)")
        return prompt, False, metadata

    rewritten = result["rewritten_prompt"]
    log.warning(
        f"🛡️ GPT Pre-flight: RİSKLİ (skor: {risk_score}/10) — "
        f"Sebepler: {', '.join(map(str, risk_reasons))}"
    )
    log.info(f"   ✏️ GPT yeniden yazdı: {rewritten[:100]}...")
    metadata["rewritten"] = True
    return rewritten, True, metadata


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
                {"role": "user", "content": f"Rewrite this rejected maritime CCTV prompt:\n\n{original_prompt}"},
            ],
            temperature=0.7,
            max_tokens=250,
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

        if "cctv" not in rewritten.lower() and "surveillance" not in rewritten.lower():
            rewritten += " Raw surveillance footage, natural lighting."

        log.info(f"✏️ GPT Retry Rewrite başarılı: {rewritten[:100]}...")
        return rewritten

    except Exception as e:
        log.warning(f"⚠️ GPT rewrite hatası — regex fallback: {e}")
        return create_softened_prompt(original_prompt)
