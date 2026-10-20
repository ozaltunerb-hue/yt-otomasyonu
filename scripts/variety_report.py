# Çeşitlilik ölçer (21 Eki 2026, Gece 1 / Aşama 2; Aşama 3'te Notion eksen geçmişi eklendi). Üretimi değiştirmez.
#
# Her yapılandırılmış aktif olay için gerçek seçim mantığıyla (LRU dahil) art arda N üretim simüle edilir: boş geçmiş
# ve boş süreç hafızasıyla başlar, her üretimin combo_key'i ve hikâyesi bir sonrakinin geçmişine eklenir. Hikâye kod
# yedeğinden (GPT yok, scripts/prompt_snapshot.py ile aynı yol); Kie yok, Notion sahte.
# Dört senaryo:
#   önce / normal  : yükleyicisiz yol (Aşama 3 öncesi davranışın birebir aynısı), süreç hafızası korunur
#   önce / deploy  : aynı, her üretimden önce süreç hafızası silinir (her üretim arasında deploy)
#   sonra / normal : sahte Notion "Eksenler" geçmişi (her üretim bir kayıt ekler) + süreç hafızası
#   sonra / deploy : sahte Notion geçmişi, her üretimden önce süreç hafızası silinir
# Ölçülen eksenler: ortam, spot, ışık, araç, kişi sayısı, kilit cümle, beat çifti; Aşama 4: kadraj, ön plan, kamera
# modu (kamera modu sadece A/B noktalarında, diğerlerinde "—"). Ortam: çığ/deprem ortamı (ışık
# hariç), ateş hortumu ve volkan ortamı, sel/kıyı dalgada bölge görünümü; diğerlerinde yok ("—").
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

AXES = ("environment", "spot", "weather", "vehicle", "people", "key_visual", "beats", "kadraj", "on_plan",
        "kamera_modu")
AXIS_NAMES = {"environment": "ortam", "spot": "spot", "weather": "ışık", "vehicle": "araç",
              "people": "kişi", "key_visual": "kilit cümle", "beats": "beat çifti", "kadraj": "kadraj",
              "on_plan": "ön plan", "kamera_modu": "kamera modu"}
COPY_AXES = ("spot", "environment", "weather", "key_visual")
LRU_AXES = ("environment", "spot", "weather", "vehicle", "people", "kadraj", "on_plan", "kamera_modu")   # 21 Eki: +3
SCENARIOS = {"önce_normal": (False, False), "önce_deploy": (False, True),
             "sonra_normal": (True, False), "sonra_deploy": (True, True)}


def _row(scene: dict) -> dict:
    a = ps.axes(scene)
    env = scene["trace"].get("environment")
    if env:   # çığ/deprem: ışık ortam ekseninin parçası; ortam = ışık dışındaki eksenler, ışık ayrı sayılır
        a["environment"] = " · ".join(f"{k}={v}" for k, v in env.items() if k not in ("spot", "light"))
        a["weather"] = env["light"]
    a["environment"] = a["environment"] or a["view"] or "—"
    return {k: (a[k] if a[k] is not None else "—") for k in AXES}


def simulate(event: str, runs: int = 20, seed: int = 2026, reset_each: bool = False,
             notion: bool = False) -> list[dict]:
    """notion=True: sahte Notion yükleyicisi, her üretimin "Eksenler" kaydını (iptal gibi durum filtresiz) biriktirir."""
    ps.reset_memory()
    random.seed(seed)
    history, texts, rows, records = [], [], [], []
    loader = (lambda domain: [r for r in records if r["combo_key"].startswith(f"{domain}|")]) if notion else None
    for _ in range(runs):
        if reset_each:
            ps.reset_memory()
        try:
            scene = ps.build(event, history, texts, axes_loader=loader)
        except Exception as e:   # noqa: BLE001 - kurulamayan üretim de ölçülür
            rows.append({"error": f"{type(e).__name__}: {e}"})
            continue
        history.append(scene["combo_key"])
        texts.append(scene.get("plain_story") or scene["story"])
        records.append({"combo_key": scene["combo_key"], "eksenler": scene.get("axes_json", ""), "ortam": "",
                        "prompt": scene["prompt"], "status": "✅", "date": ""})
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
    m["rep_lru"] = sum(m[f"rep_{k}"] for k in LRU_AXES)
    return m


def option_counts(event: str) -> dict:
    """Eksen başına seçenek sayısı (tek seçenekli eksen raporu). Araç/kişi olmayan olayda None."""
    import core.event_structure as es
    import core.skeleton_pipeline as sk
    s = sk.EVENT_SKELETONS[event]
    region = event in sk.REGION_VIEW_EVENTS
    if event == es.FIRE_TORNADO:
        spot = min(len(v["spots"]) for v in es.FIRE_TOR_ENVS.values())
    else:
        spot = min(len(sk.view_spots(event, v)) for v in es.structure_views(event))
    if region:
        env = len(sk.REGION_VIEWS)
    elif event == es.FIRE_TORNADO:
        env = len(es.FIRE_TOR_ENVS)
    elif event in es.VOLC_ENV_EVENTS:
        env = len(sk.VOLC_ENVS)
    elif event in es.ENV_EVENTS:
        env = "eksen"   # çok eksenli ortam (dağ/yerleşim veya şehir/sokak)
    else:
        env = None
    if event in es.AVALANCHE_EVENTS:
        light = len(es.ENV_AXES["light"])
    elif event in es.EARTHQUAKE_EVENTS:
        light = len(es.EQ_ENV_AXES["light"])
    elif event in es.VOLC_ENV_EVENTS:
        light = len(sk.VOLCANO_WEATHER_WEIGHTS[event])
    else:
        light = len(s["weather"])
    if not es.uses_vehicle(event):
        vehicle = None
    elif region:
        vehicle = min(len(v) for v in es.REGION_VEHICLES.values())
    else:
        vehicle = len(es.EVENT_VEHICLES[event])
    if es.has_people_rule(event):
        lo, hi = sk.count_range(event, None)
        people = hi - lo + 1
    else:
        people = None
    key = len(es.FIRE_TOR_ENVS) if event == es.FIRE_TORNADO else 1
    return {"spot": spot, "environment": env, "weather": light, "vehicle": vehicle, "people": people, "key": key}


def single_option_axes() -> list[tuple[str, str]]:
    out = []
    for e in ps.active_events():
        for axis, n in option_counts(e).items():
            if n == 1 and axis != "key":   # kilit cümle LRU ekseni değil (ayrı not)
                out.append((e, AXIS_NAMES.get(axis, "kilit cümle")))
    return out


def report(runs: int = 20, seed: int = 2026) -> dict:
    return {e: {name: measure(simulate(e, runs, seed, reset, notion)) for name, (notion, reset) in SCENARIOS.items()}
            for e in ps.active_events()}


def _table(data: dict, key: str) -> list[str]:
    head = "| Olay | " + " | ".join(f"{AXIS_NAMES[k]} (benzersiz / art arda)" for k in AXES) + " | tam kopya |"
    lines = [head, "|---|" + "---|" * (len(AXES) + 1)]
    for e, d in data.items():
        m = d[key]
        cells = [f"{m['uniq_' + k]} / {m['rep_' + k]}" for k in AXES]
        err = f" ⚠️ {m['errors']} hata" if m["errors"] else ""
        lines.append(f"| {e}{err} | " + " | ".join(cells) + f" | {m['copies']} |")
    return lines


def _compare(data: dict) -> list[str]:
    lines = ["| Olay | tam kopya normal (önce → sonra) | tam kopya deploy (önce → sonra) | art arda tekrar, 5 LRU "
             "ekseni normal (önce → sonra) | art arda tekrar, 5 LRU ekseni deploy (önce → sonra) |",
             "|---|---|---|---|---|"]
    for e, d in data.items():
        lines.append(f"| {e} | {d['önce_normal']['copies']} → {d['sonra_normal']['copies']} | "
                     f"{d['önce_deploy']['copies']} → {d['sonra_deploy']['copies']} | "
                     f"{d['önce_normal']['rep_lru']} → {d['sonra_normal']['rep_lru']} | "
                     f"{d['önce_deploy']['rep_lru']} → {d['sonra_deploy']['rep_lru']} |")
    return lines


def ranking(data: dict, key: str = "sonra_normal") -> tuple[list[str], list[str]]:
    """(en kötü 5, en iyi 3): önce tam kopya, sonra ortam+spot+ışık+kilit cümle art arda tekrar toplamı."""
    order = sorted(data, key=lambda e: (data[e][key]["copies"], data[e][key]["rep_total"]))
    return order[::-1][:5], order[:3]


def to_markdown(data: dict, runs: int, seed: int) -> str:
    def line(e, key):
        m = data[e][key]
        return f"- {e}: tam kopya {m['copies']}, art arda tekrar (ortam+spot+ışık+kilit) {m['rep_total']}"
    worst_before, _ = ranking(data, "önce_normal")
    worst, best = ranking(data, "sonra_normal")
    single = single_option_axes()
    parts = ["# Çeşitlilik ölçümü — 21 Ekim 2026 (Aşama 3 sonrası)", "",
             f"Üretim: `scripts/variety_report.py --runs {runs} --seed {seed}`. Her olayda {runs} ardışık üretim, gerçek "
             "seçim mantığı, boş geçmişle başlar, her üretim sonrakinin geçmişine eklenir. Hikâye kod yedeğinden (GPT "
             "yok). Kie yok, Notion sahte (her üretim bir \"Eksenler\" kaydı ekler, durum filtresi yok).", "",
             "**Önce** = Notion eksen geçmişi olmadan (Aşama 3 öncesi davranışın birebir aynısı: `prompt_snapshot.py "
             "diff` 0). **Sonra** = Notion eksen geçmişiyle (üretimdeki yol). **Deploy** = her üretimden önce süreç "
             "hafızası silinir.", "",
             "## Önce / sonra", "", *_compare(data), "",
             "## Sonra, normal (süreç hafızası korunur)", "",
             "Hücre biçimi: `benzersiz değer sayısı / arka arkaya aynı değer sayısı` (en fazla "
             f"{runs - 1}). \"—\" olan eksen tekrar sayılmaz.", "", *_table(data, "sonra_normal"), "",
             "## Sonra, her üretimden önce deploy", "", *_table(data, "sonra_deploy"), "",
             "## Önce, normal (karşılaştırma için)", "", *_table(data, "önce_normal"), "",
             "## Önce, her üretimden önce deploy (karşılaştırma için)", "", *_table(data, "önce_deploy"), "",
             "## Sıralama", "", "**Önce en kötü 5 (normal) ve sonraki durumları:**",
             *[f"- {e}: tam kopya {data[e]['önce_normal']['copies']} → {data[e]['sonra_normal']['copies']}"
               for e in worst_before], "",
             "**Sonra en kötü 5 (normal):**", *[line(e, "sonra_normal") for e in worst], "",
             "**Sonra en iyi 3 (normal):**", *[line(e, "sonra_normal") for e in best], "",
             "## Tek seçenekli eksenler (tekrar önleme uygulanamaz)", "",
             *[f"- {e}: {axis}" for e, axis in single], "",
             "Kilit cümle ateş hortumu dışında her olayda tek (açılış varyantları sonraki aşamada).", ""]
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
