# Prompt kural denetimi (21 Eki 2026, Gece 1 / Aşama 2). Üretim davranışını değiştirmez, sadece ölçer.
#
# Girdi: prompt anlık görüntüsü (scripts/prompt_snapshot.py; varsayılan: mevcut koddan yeniden üretilir, --baseline ile
# tests/snapshots/prompts_baseline.json okunur). Her prompt için K1-K5 denetlenir, olay × kural tablosu çıkar.
#   K1 kamera cümlesinde yasaklı ifade yok (CAMERA_BANNED)
#   K2 kamera cümlesinde yükseklik ifadesi var (HEIGHT_TERMS; bugünkü yüksek spot metinlerinden çıkarıldı)
#   K3 kamera cümlesinde sabitlik ifadesi var (FIXED_TERMS; bugünkü sabit kamera şablonlarından çıkarıldı)
#   K4 volkan olaylarında "rain" kökü yok (tüm prompt)
#   K5 toplam prompt en fazla 175 kelime
# Cırcır testi: tests/test_prompt_rules.py, bugünkü ihlaller tests/snapshots/rules_known_violations.json.
#
# Kullanım (proje kökünden):
#   .venv\Scripts\python.exe scripts\prompt_rules.py                  -> tablo (mevcut kod)
#   .venv\Scripts\python.exe scripts\prompt_rules.py --md docs\x.md   -> tabloyu markdown dosyasına da yazar
#   .venv\Scripts\python.exe scripts\prompt_rules.py --write-known    -> bugünkü ihlalleri cırcır dosyasına yazar
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402

KNOWN = os.path.join(ROOT, "tests", "snapshots", "rules_known_violations.json")
RULES = ("K1", "K2", "K3", "K4", "K5")
RULE_NAMES = {"K1": "kamerada yasaklı ifade yok", "K2": "kamerada yükseklik ifadesi var",
              "K3": "kamerada sabitlik ifadesi var", "K4": "volkanda 'rain' kökü yok", "K5": "prompt ≤ 175 kelime"}
CAMERA_BANNED = ("eye level", "street level", "ground level", "sidewalk", "pans to follow", "follows the", "tracking",
                 "walks with", "runs with")
# Bugünkü yüksek kamera noktalarının (balkon, çatı terası, üst kat, yamaç terası, istasyon terası, yüksek basamak, set,
# yükseltilmiş promenat) ve sabit şablonların (volkan/çığ/deprem/ateş hortumu) kamera cümlelerinden çıkarıldı
HEIGHT_TERMS = ("high", "elevated", "rooftop", "balcony", "upper-floor", "upper floor", "high-floor", "overlook",
                "overlooking", "terrace", "raised", "vantage", "above", "looking down")
FIXED_TERMS = ("stays fixed", "fixed", "locked-off", "locked off", "stays in place", "never moves", "static",
               "never descending", "never descends")
RAIN_RE = re.compile(r"\brain(?:s|ed|ing|y)?\b", re.IGNORECASE)
MAX_WORDS = 175


def camera_sentence(style_suffix: str) -> str:
    """Stil ekinin kamera kısmı: baştan "no cuts."a kadar (tüm şablonlarda kamera cümlesi bununla biter)."""
    i = style_suffix.find("no cuts.")
    return style_suffix[: i + len("no cuts.")] if i >= 0 else style_suffix


def _has(terms, text: str) -> list[str]:
    low = text.lower()
    # Tireli bileşik sayılmaz: "waist-high wall" (sel kilit nesnesi) yükseklik değil, "high-rise" de değil
    return [t for t in terms if re.search(r"(?<![a-z-])" + re.escape(t) + r"(?![a-z-])", low)]


def check(event: str, item: dict) -> dict[str, str]:
    """{kural: ihlal açıklaması}; boş sözlük = hepsi geçti. Kurulamayan üretim tüm kurallarda ihlal sayılır."""
    if "error" in item:
        return {r: "üretim kurulamadı: " + item["error"] for r in RULES}
    cam = camera_sentence(item["style_suffix"])
    out = {}
    banned = _has(CAMERA_BANNED, cam)
    if banned:
        out["K1"] = ", ".join(banned)
    if not _has(HEIGHT_TERMS, cam):
        out["K2"] = "yükseklik ifadesi yok"
    if not _has(FIXED_TERMS, cam):
        out["K3"] = "sabitlik ifadesi yok"
    if "volcan" in event.lower() or "pyroclastic" in event.lower():
        rain = sorted({m.group(0).lower() for m in RAIN_RE.finditer(item["prompt"])})
        if rain:
            out["K4"] = ", ".join(rain)
    words = len(item["prompt"].split())
    if words > MAX_WORDS:
        out["K5"] = f"{words} kelime"
    return out


def evaluate(snapshot: dict) -> dict:
    """{olay: {kural: [tohum, ...]}} + örnek açıklama: {"violations": ..., "examples": {olay: {kural: metin}}}."""
    viol, examples = {}, {}
    for event, seeds in snapshot.items():
        for seed, item in sorted(seeds.items(), key=lambda kv: int(kv[0])):
            for rule, why in check(event, item).items():
                viol.setdefault(event, {}).setdefault(rule, []).append(int(seed))
                examples.setdefault(event, {}).setdefault(rule, why)
    return {"violations": viol, "examples": examples}


def known_pairs(result: dict) -> dict[str, list[str]]:
    """Cırcır biçimi: {kural: [olay, ...]} (olay × kural düzeyi; hangi tohum olduğu önemli değil)."""
    out = {r: [] for r in RULES}
    for event, rules in result["violations"].items():
        for rule in rules:
            out[rule].append(event)
    return {r: sorted(v) for r, v in out.items()}


def table_md(snapshot: dict, result: dict) -> str:
    n = len(next(iter(snapshot.values())))
    lines = ["| Olay | " + " | ".join(f"{r} {RULE_NAMES[r]}" for r in RULES) + " |",
             "|---|" + "---|" * len(RULES)]
    for event in snapshot:
        cells = []
        for r in RULES:
            seeds = result["violations"].get(event, {}).get(r)
            cells.append("✅" if not seeds else f"❌ {len(seeds)}/{n} ({result['examples'][event][r]})")
        lines.append(f"| {event} | " + " | ".join(cells) + " |")
    pairs = known_pairs(result)
    lines += ["", "Kural başına ihlal eden olay sayısı: " + " · ".join(f"{r} {len(pairs[r])}" for r in RULES), "",
              "K1 yasaklı ifadeler: " + ", ".join(f'"{t}"' for t in CAMERA_BANNED),
              "", "K2 yükseklik ifadeleri: " + ", ".join(f'"{t}"' for t in HEIGHT_TERMS),
              "", "K3 sabitlik ifadeleri: " + ", ".join(f'"{t}"' for t in FIXED_TERMS),
              "", "K4 rain kökü: rain, rains, rained, raining, rainy (sadece volkan olayları, tüm prompt)",
              "", f"K5: prompt.split() ile en fazla {MAX_WORDS} kelime"]
    return "\n".join(lines)


def write_known(result: dict, path: str = KNOWN) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {"_note": "Cırcır: bugünkü bilinen ihlaller (kural -> olaylar). tests/test_prompt_rules.py yeni ihlalde ve "
                     "artık ihlal etmeyen kayıtta başarısız olur; düzeltilen olayı buradan sil. Üretim: "
                     "scripts/prompt_rules.py --write-known",
            **known_pairs(result)}
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main(argv: list[str]) -> int:
    snapshot = ps.load_baseline() if "--baseline" in argv else ps.snapshot_all()
    result = evaluate(snapshot)
    md = table_md(snapshot, result)
    print(md)
    if "--md" in argv:
        path = argv[argv.index("--md") + 1]
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(md + "\n")
    if "--write-known" in argv:
        write_known(result)
        print(f"\nBilinen ihlaller yazıldı: {os.path.relpath(KNOWN, ROOT)}")
    return 0


if __name__ == "__main__":
    import logging
    logging.disable(logging.WARNING)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
