"""
Üretim ayrıntısı metinleri (TUR 29): Telegram "🔍 Ayrıntı" / "✋ Onay" mesajları ve Notion sayfa gövdesi
aynı metni kullanır. Sadece biçimlendirme; seçim ya da kapı mantığı yok.
"""
from __future__ import annotations

import difflib
import json
import re

TELEGRAM_LIMIT = 4096
_SAFE_LIMIT = 4000   # bölme sınırı: Telegram 4096'nın altında pay

_NEG_RE = re.compile(r"\b(?:no|never|not|nobody|nothing|without)\b", re.IGNORECASE)


def split_message(text: str, limit: int = _SAFE_LIMIT) -> list[str]:
    """Metni satır sınırından bölerek parçalara ayırır; tek satır sınırı aşarsa satır da bölünür.
    Hiçbir karakter kaybolmaz: parçaların birleşimi orijinal metindir."""
    if len(text) <= limit:
        return [text]
    parts, current = [], ""
    for line in text.splitlines(keepends=True):
        while len(line) > limit:
            if current:
                parts.append(current)
                current = ""
            parts.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) > limit:
            parts.append(current)
            current = ""
        current += line
    if current:
        parts.append(current)
    return parts


def count_constraints(style_suffix: str) -> tuple[int, int]:
    """Stil ekindeki kısıt sayısı (cümle / noktalı virgül parçası) ve bunların kaçı olumsuz."""
    clauses = [c for c in re.split(r"(?<=[.;])\s+", (style_suffix or "").strip()) if c.strip()]
    return len(clauses), sum(1 for c in clauses if _NEG_RE.search(c))


def word_diff(before: str, after: str) -> str:
    """Kelime düzeyinde fark: [-silinen-] {+eklenen+}. Aynıysa boş."""
    a, b = (before or "").split(), (after or "").split()
    if a == b:
        return ""
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(" ".join(a[i1:i2]))
        if op in ("delete", "replace"):
            out.append("[-" + " ".join(a[i1:i2]) + "-]")
        if op in ("insert", "replace"):
            out.append("{+" + " ".join(b[j1:j2]) + "+}")
    return " ".join(out)


def _fmt_candidate(c: dict) -> str:
    head = (f"#{c['n']} {'✅ geçti' if c['passed'] else '❌ reddedildi'}"
            + (f" · skor {c['score']}" if c.get("score") is not None else "")
            + f"\n   ortam: {c.get('environment')} · gemi: {c.get('ship')} · kamera: {c.get('camera')}"
            + f"\n   olay: {c.get('event')}"
            + f"\n   özet: {c.get('summary') or '-'}")
    if c.get("failures"):
        head += "\n   ret nedeni: " + " | ".join(c["failures"])
    return head


def format_generation(trace: dict, labels: dict | None = None) -> list[tuple[str, str]]:
    """(başlık, metin) bölümleri: Seçim, Adaylar, Seçilen, Simplifier sonrası hikaye."""
    labels = labels or {}
    if trace.get("pipeline") == "skeleton":
        return _format_skeleton(trace, labels)
    if trace.get("pipeline") == "creative":
        return _format_creative(trace, labels)
    cands = trace.get("candidates") or []
    sections = [("🔍 1. Seçim",
                 f"Kategori: {labels.get('domain') or trace.get('domain') or 'rastgele'}\n"
                 f"Olay: {labels.get('event') or trace.get('event') or '🎲 rastgele (motor seçer)'}\n"
                 f"Her aday için ortam, gemi ve kamera ayrı çekilir (aşağıda).")]
    sections.append((f"🔍 2. Adaylar ({sum(c['passed'] for c in cands)}/{len(cands)} kapıdan geçti)",
                     "\n\n".join(_fmt_candidate(c) for c in cands) or "-"))
    chosen = trace.get("chosen") or {}
    if chosen:
        pick = next((c for c in cands if c["n"] == chosen.get("n")), {})
        sections.append(("🔍 3. Seçilen",
                         f"Aday #{chosen.get('n')} · skor {chosen.get('score')}\n"
                         f"Sıralama: {' → '.join('#' + str(n) for n in chosen.get('order', []))}\n"
                         f"Kural: {chosen.get('rule')}\n"
                         f"Ortam: {pick.get('environment')} · gemi: {pick.get('ship')} · kamera: {pick.get('camera')}"))
    simp = trace.get("simplifier") or []
    if simp:
        lines = []
        for a in simp:
            status = "✅ kapıdan geçti" if not a.get("failures") else "❌ " + " | ".join(a["failures"])
            lines.append(f"Aday #{a.get('n')} deneme {a.get('attempt')} · {len((a.get('prompt') or '').split())} kelime · "
                         f"{status}\n{a.get('prompt') or '(boş)'}")
        sections.append(("🔍 4. Simplifier sonrası hikaye", "\n\n".join(lines)))
    return sections


def _format_skeleton(trace: dict, labels: dict) -> list[tuple[str, str]]:
    """İskelet hattı (TUR 30): seçim, iskelet + boşluklar, hikaye. Aday/skor/simplifier bu hatta yok."""
    slots = trace.get("slots") or {}
    attempts = trace.get("slot_attempts") or []
    lines = [f"Deneme {a.get('attempt')}: {json.dumps(a.get('raw'), ensure_ascii=False)}"
             + (" · ❌ " + " | ".join(a["errors"]) if a.get("errors") else " · ✅ geçerli") for a in attempts]
    return [
        ("🔍 1. Seçim",
         f"Hat: iskelet (PROMPT_PIPELINE=skeleton)\n"
         f"Kategori: {labels.get('domain') or trace.get('domain')}\n"
         f"Olay: {labels.get('event') or trace.get('event')}\n"
         f"Gemi: {trace.get('ship')} (Python, LRU) · kamera: el kamerası\n"
         f"Ortam: {slots.get('spot', '-')}"),
        ("🔍 2. İskelet ve boşluklar (gpt-4o-mini)",
         f"İskelet: {trace.get('skeleton')}\n\n"
         f"Boşluklar: yer={slots.get('spot')} · hava={slots.get('weather')} · kişi={slots.get('count')} "
         f"{slots.get('people')}\n" + "\n".join(lines)),
        ("🔍 3. Hikaye", f"{trace.get('story_words')} kelime\n{trace.get('story')}"),
    ]


def _format_creative(trace: dict, labels: dict) -> list[tuple[str, str]]:
    """Creative hattı (TUR 31): seçim, GPT-4o denemeleri (kural kapısı, 30 Eyl), hikâye."""
    lo, hi = (trace.get("count_range") or ["?", "?"])[:2]

    def status(a: dict) -> str:
        missing = a.get("missing", a.get("issues"))   # eski kayıtlarda "missing" yok
        return "✅ geçti" if not missing else "❌ eksik: " + "; ".join(missing)
    lines = [f"Deneme {a.get('attempt')} · {status(a)} · {a.get('words')} kelime\n{a.get('story') or '(boş)'}"
             for a in trace.get("attempts") or []]
    return [
        ("🔍 1. Seçim",
         f"Hat: creative (PROMPT_PIPELINE=creative)\n"
         f"Kategori: {labels.get('domain') or trace.get('domain')}\n"
         f"Olay: {labels.get('event') or trace.get('event')}\n"
         f"Gemi: {trace.get('ship')} (Python, LRU) · kamera: el kamerası\n"
         f"Yer: {trace.get('spot')} · hava: {trace.get('weather')} (Python, rastgele) · kişi aralığı: {lo}-{hi}\n"
         + (f"Görünüm: {trace['view']}\n" if trace.get("view") else "") +
         f"Ulaşılacak sonuç: {trace.get('outcome', '-')}\n"
         f"Tekrar önleme: son {trace.get('recent_count', 0)} hikâye GPT'ye verildi"),
        ("🔍 2. GPT-4o hikâyesi (kural kapısı: 6 sabit kural + olay anahtar grupları, en fazla 3 deneme)", "\n\n".join(lines) or "-"),
        ("🔍 3. Hikâye", f"{trace.get('story_words')} kelime\n{trace.get('story')}"),
    ]


def format_final_prompt(info: dict) -> tuple[str, str]:
    """(başlık, metin): Kie'ye giden TAM prompt, kelime ve kısıt sayısı, preflight farkı."""
    prompt = info.get("prompt", "")
    total, negative = count_constraints(info.get("style_suffix", ""))
    text = (f"{len(prompt.split())} kelime (hikaye {len((info.get('story') or '').split())} + stil eki "
            f"{len((info.get('style_suffix') or '').split())}) · stil ekinde {total} kısıt, {negative} olumsuz\n"
            f"Kie denemesi: {info.get('attempt', 1)}\n\n{prompt}")
    diff = word_diff(info.get("story_before_preflight", ""), info.get("story", ""))
    if diff:
        risk = (info.get("preflight") or {}).get("risk_score", "?")
        text += f"\n\n⚠️ Preflight / güvenlik yeniden yazımı hikayeyi değiştirdi (risk {risk}/10):\n{diff}"
    return "🔍 5. Kie'ye giden son prompt", text


def sections_to_text(sections: list[tuple[str, str]]) -> str:
    return "\n\n".join(f"{title}\n{body}" for title, body in sections)
