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
CAMERA_RULES = ("K1", "K2", "K3")
MODE_A_SUFFIX = "A"   # "K1A": mod A cümlesindeki K1 (izinli, cırcırda "mod_a" kovası)
MODE_A_NOTE = "mod A — kanıtlanmış kamera"
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
    # 21 Eki (Aşama 4): mod A = kanıtlanmış bugünkü cümle (kelimesi kelimesine). K1-K3 orada izinli, ayrı kovada sayılır
    if (item.get("axes") or {}).get("kamera_modu") == "A":
        out = {(f"{r}{MODE_A_SUFFIX}" if r in CAMERA_RULES else r): why for r, why in out.items()}
    return out


def camera_items() -> dict:
    """Tüm kamera varyantları (olay -> {anahtar: öğe}): her görünüm × spot × kadraj varyantı (core.frame_axis.all_frames;
    volkanda her ortam). K1-K3 için tohumdan bağımsız tam kapsam; öğede prompt = stil eki (K4/K5 burada anlamsız)."""
    import core.event_structure as es
    import core.frame_axis as fx
    import core.skeleton_pipeline as sk
    out = {}
    for event in ps.active_events():
        items = {}
        for view in es.structure_views(event):
            for spot in sk.view_spots(event, view):
                pool = (list(es.FIRE_TOR_ENVS[es.fire_env_of_spot(spot)]["spots"]) if event == es.FIRE_TORNADO
                        else sk.view_spots(event, view))
                fire_env = es.fire_env_of_spot(spot) if event == es.FIRE_TORNADO else None
                import core.scene_env as sv
                scene_envs = sv.compatible_envs(event, spot) if event in sv.SCENE_ENVS else [None]
                for venv in (list(sk.VOLC_ENVS) if event in es.VOLC_ENV_EVENTS else [None]):
                    for senv in scene_envs:
                      for f in fx.all_frames(event, spot, pool, blocked=sv.excluded_positions(event, senv)):
                        suffix = sk.style_suffix(event, None, spot, view, None, venv, f, fire_env, senv)
                        key = f"{spot}|{view}|{venv}|{senv}|{f['type']}|{f['pos_spot']}|{f['mode']}|{f['fg']}"
                        items[key] = {"style_suffix": suffix, "prompt": suffix, "axes": {"kamera_modu": f["mode"]},
                                      "frame": f}
        out[event] = items
    return out


def evaluate(snapshot: dict) -> dict:
    """{olay: {kural: [anahtar, ...]}} + örnek açıklama: {"violations": ..., "examples": {olay: {kural: metin}}}.
    Anahtar: tohum (anlık görüntü) ya da varyant anahtarı (camera_items)."""
    viol, examples = {}, {}
    for event, seeds in snapshot.items():
        for seed, item in seeds.items():
            for rule, why in check(event, item).items():
                viol.setdefault(event, {}).setdefault(rule, []).append(seed)
                examples.setdefault(event, {}).setdefault(rule, why)
    return {"violations": viol, "examples": examples}


def known_pairs(result: dict) -> dict:
    """Cırcır biçimi: {kural: [olay, ...], "mod_a": {kural: [olay, ...]}} (olay × kural düzeyi)."""
    out = {r: [] for r in RULES}
    mode_a = {r: [] for r in CAMERA_RULES}
    for event, rules in result["violations"].items():
        for rule in rules:
            if rule.endswith(MODE_A_SUFFIX) and rule[:-1] in CAMERA_RULES:
                mode_a[rule[:-1]].append(event)
            else:
                out[rule].append(event)
    return {**{r: sorted(set(v)) for r, v in out.items()}, "mod_a": {r: sorted(set(v)) for r, v in mode_a.items()}}


def merge_pairs(*pairs: dict) -> dict:
    out = {r: sorted(set().union(*(p[r] for p in pairs))) for r in RULES}
    out["mod_a"] = {r: sorted(set().union(*(p["mod_a"][r] for p in pairs))) for r in CAMERA_RULES}
    return out


def table_md(snapshot: dict, result: dict, cams: dict | None = None, cam_result: dict | None = None) -> str:
    """Olay × kural tablosu. Hücre: ihlal eden tohum (K1-K3'te ayrıca kamera varyantı) sayısı; "A" = sadece mod A'da
    (izinli, kanıtlanmış bugünkü cümle)."""
    n = len(next(iter(snapshot.values())))
    lines = ["| Olay | " + " | ".join(f"{r} {RULE_NAMES[r]}" for r in RULES) + " | kamera varyantı |",
             "|---|" + "---|" * (len(RULES) + 1)]
    for event in snapshot:
        cells = []
        for r in RULES:
            bad = result["violations"].get(event, {}).get(r)
            cam_bad = (cam_result or {"violations": {}})["violations"].get(event, {}).get(r) if r in CAMERA_RULES else None
            mode_a = (result["violations"].get(event, {}).get(r + MODE_A_SUFFIX)
                      or (cam_result or {"violations": {}})["violations"].get(event, {}).get(r + MODE_A_SUFFIX))
            if bad or cam_bad:
                why = (result["examples"].get(event, {}).get(r) or cam_result["examples"][event][r])
                cells.append(f"❌ {len(bad or [])}/{n} tohum, {len(cam_bad or [])} varyant ({why})")
            else:
                cells.append("✅" + (" (mod A izinli)" if mode_a else ""))
        nvar = len((cams or {}).get(event, {}))
        lines.append(f"| {event} | " + " | ".join(cells) + f" | {nvar} |")
    pairs = merge_pairs(known_pairs(result), known_pairs(cam_result)) if cam_result else known_pairs(result)
    lines += ["", "Kural başına ihlal eden olay sayısı (mod A hariç): "
              + " · ".join(f"{r} {len(pairs[r])}" for r in RULES),
              "Mod A (izinli, " + MODE_A_NOTE + "): " + " · ".join(f"{r} {len(pairs['mod_a'][r])}" for r in CAMERA_RULES),
              "", "K1 yasaklı ifadeler: " + ", ".join(f'"{t}"' for t in CAMERA_BANNED),
              "", "K2 yükseklik ifadeleri: " + ", ".join(f'"{t}"' for t in HEIGHT_TERMS),
              "", "K3 sabitlik ifadeleri: " + ", ".join(f'"{t}"' for t in FIXED_TERMS),
              "", "K4 rain kökü: rain, rains, rained, raining, rainy (sadece volkan olayları, tüm prompt)",
              "", f"K5: prompt.split() ile en fazla {MAX_WORDS} kelime (tohumlar; tüm kombinasyonlar: "
                  "scripts/frame_budget.py)"]
    return "\n".join(lines)


def current_pairs(snapshot: dict | None = None) -> dict:
    """Tohum anlık görüntüsü + tüm kamera varyantları birleşik cırcır biçimi (test bunu kullanır)."""
    snapshot = snapshot if snapshot is not None else ps.snapshot_all()
    return merge_pairs(known_pairs(evaluate(snapshot)), known_pairs(evaluate(camera_items())))


def write_known(result: dict, path: str = KNOWN) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {"_note": "Cırcır: bilinen ihlaller (kural -> olaylar). tests/test_prompt_rules.py yeni ihlalde ve artık "
                     "ihlal etmeyen kayıtta başarısız olur; düzeltilen olayı buradan sil. Üretim: "
                     "scripts/prompt_rules.py --write-known. 21 Eki (Aşama 4): K1-K3 sadece mod A cümlelerinde izinli "
                     "(\"mod_a\" kovası: " + MODE_A_NOTE + "); mod B ve tüm yeni cümleler K1-K3'ü geçmeli.",
            **result}
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main(argv: list[str]) -> int:
    snapshot = ps.load_baseline() if "--baseline" in argv else ps.snapshot_all()
    result = evaluate(snapshot)
    cams = camera_items()
    cam_result = evaluate(cams)
    md = table_md(snapshot, result, cams, cam_result)
    print(md)
    if "--md" in argv:
        path = argv[argv.index("--md") + 1]
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(md + "\n")
    if "--write-known" in argv:
        write_known(merge_pairs(known_pairs(result), known_pairs(cam_result)))
        print(f"\nBilinen ihlaller yazıldı: {os.path.relpath(KNOWN, ROOT)}")
    return 0


if __name__ == "__main__":
    import logging
    logging.disable(logging.WARNING)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
