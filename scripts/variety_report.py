# Çeşitlilik ölçer (21 Eki 2026, Gece 1 / Aşama 2). Üretim davranışını değiştirmez, sadece ölçer.
#
# Her yapılandırılmış aktif olay için gerçek seçim mantığıyla (LRU dahil) art arda N üretim simüle edilir: boş geçmiş
# ve boş süreç hafızasıyla başlar, her üretimin combo_key'i ve hikâyesi bir sonrakinin geçmişine eklenir (Notion'un
# yaptığı gibi). Hikâye kod yedeğinden (GPT yok, scripts/prompt_snapshot.py ile aynı yol); Kie/Notion yok.
# İki senaryo:
#   normal  : süreç hafızası korunur (bot aynı süreçte art arda üretir)
#   deploy  : her üretimden önce süreç hafızası silinir (her üretim arasında deploy/yeniden başlatma olmuş gibi;
#             geriye sadece Notion combo_key'den okunan eksenler kalır)
# Ölçülen eksenler: ortam, spot, ışık, araç, kişi sayısı, kilit cümle, beat çifti. Ortam: çığ/deprem ortam satırı,
# ateş hortumu ve volkan ortamı, sel/kıyı dalgada bölge görünümü; diğerlerinde yok ("—").
# "Tam kopya": spot + ortam + ışık + kilit cümle bir önceki üretimle birebir aynı.
#
# Kullanım (proje kökünden):
#   .venv\Scripts\python.exe scripts\variety_report.py [--runs 20] [--seed 2026] [--md docs\cesitlilik_2026-10-21.md]
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402

AXES = ("environment", "spot", "weather", "vehicle", "people", "key_visual", "beats")
AXIS_NAMES = {"environment": "ortam", "spot": "spot/kamera", "weather": "ışık", "vehicle": "araç",
              "people": "kişi", "key_visual": "kilit cümle", "beats": "beat çifti"}
COPY_AXES = ("spot", "environment", "weather", "key_visual")


def _row(scene: dict) -> dict:
    a = ps.axes(scene)
    env = scene["trace"].get("environment")
    if env:   # çığ/deprem: ışık ortam ekseninin parçası; ortam = ışık dışındaki eksenler, ışık ayrı sayılır
        a["environment"] = " · ".join(f"{k}={v}" for k, v in env.items() if k not in ("spot", "light"))
        a["weather"] = env["light"]
    a["environment"] = a["environment"] or a["view"] or "—"
    return {k: (a[k] if a[k] is not None else "—") for k in AXES}


def simulate(event: str, runs: int = 20, seed: int = 2026, reset_each: bool = False) -> list[dict]:
    ps.reset_memory()
    random.seed(seed)
    history, texts, rows = [], [], []
    for _ in range(runs):
        if reset_each:
            ps.reset_memory()
        try:
            scene = ps.build(event, history, texts)
        except Exception as e:   # noqa: BLE001 - kurulamayan üretim de ölçülür
            rows.append({"error": f"{type(e).__name__}: {e}"})
            continue
        history.append(scene["combo_key"])
        texts.append(scene.get("plain_story") or scene["story"])
        rows.append(_row(scene))
    return rows


def measure(rows: list[dict]) -> dict:
    ok = [r for r in rows if "error" not in r]
    m = {"runs": len(rows), "errors": len(rows) - len(ok)}
    for k in AXES:
        m[f"uniq_{k}"] = len({r[k] for r in ok})
        m[f"rep_{k}"] = sum(1 for a, b in zip(ok, ok[1:]) if a[k] == b[k] and a[k] != "—")
    m["copies"] = sum(1 for a, b in zip(ok, ok[1:]) if all(a[k] == b[k] for k in COPY_AXES))
    m["rep_total"] = sum(m[f"rep_{k}"] for k in ("environment", "spot", "weather", "key_visual"))
    return m


def report(runs: int = 20, seed: int = 2026) -> dict:
    out = {}
    for e in ps.active_events():
        out[e] = {"normal": measure(simulate(e, runs, seed)), "deploy": measure(simulate(e, runs, seed, True))}
    return out


def _table(data: dict, key: str) -> list[str]:
    head = "| Olay | " + " | ".join(f"{AXIS_NAMES[k]} (benzersiz / art arda)" for k in AXES) + " | tam kopya |"
    lines = [head, "|---|" + "---|" * (len(AXES) + 1)]
    for e, d in data.items():
        m = d[key]
        cells = [f"{m['uniq_' + k]} / {m['rep_' + k]}" for k in AXES]
        err = f" ⚠️ {m['errors']} hata" if m["errors"] else ""
        lines.append(f"| {e}{err} | " + " | ".join(cells) + f" | {m['copies']} |")
    return lines


def ranking(data: dict, key: str = "normal") -> tuple[list[str], list[str]]:
    """(en kötü 5, en iyi 3): önce tam kopya, sonra ortam+spot+ışık+kilit cümle art arda tekrar toplamı."""
    order = sorted(data, key=lambda e: (data[e][key]["copies"], data[e][key]["rep_total"]))
    return order[::-1][:5], order[:3]


def to_markdown(data: dict, runs: int, seed: int) -> str:
    worst, best = ranking(data)
    def line(e):
        m = data[e]["normal"]
        return f"- {e}: tam kopya {m['copies']}, art arda tekrar (ortam+spot+ışık+kilit) {m['rep_total']}"
    parts = [f"# Çeşitlilik ölçümü — 21 Ekim 2026", "",
             f"Üretim: `scripts/variety_report.py --runs {runs} --seed {seed}`. Her olayda {runs} ardışık üretim, gerçek "
             "seçim mantığı (LRU dahil), boş geçmişle başlar, her üretimin combo_key'i ve hikâyesi sonrakinin geçmişine "
             "eklenir. Hikâye kod yedeğinden (GPT yok). Kie, Notion yok.", "",
             "Hücre biçimi: `benzersiz değer sayısı / arka arkaya aynı değer sayısı` (en fazla "
             f"{runs - 1}). \"—\" olan eksen (ortamı ya da aracı olmayan olay) tekrar sayılmaz. **Tam kopya**: spot + "
             "ortam + ışık + kilit cümle bir öncekiyle birebir aynı.", "",
             "## Normal (süreç hafızası korunur)", "", *_table(data, "normal"), "",
             "## Her üretimden önce deploy (süreç hafızası silinir, sadece Notion combo_key kalır)", "",
             *_table(data, "deploy"), "",
             "## Sıralama (normal senaryo)", "", "**En kötü 5:**", *[line(e) for e in worst], "",
             "**En iyi 3:**", *[line(e) for e in best], ""]
    return "\n".join(parts)


def main(argv: list[str]) -> int:
    runs = int(argv[argv.index("--runs") + 1]) if "--runs" in argv else 20
    seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 2026
    data = report(runs, seed)
    md = to_markdown(data, runs, seed)
    print(md)
    if "--md" in argv:
        with open(argv[argv.index("--md") + 1], "w", encoding="utf-8", newline="\n") as f:
            f.write(md + "\n")
    return 0


if __name__ == "__main__":
    import logging
    logging.disable(logging.WARNING)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
