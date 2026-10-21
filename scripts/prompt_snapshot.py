# Prompt anlık görüntüsü ve fark aracı (21 Eki 2026, Gece 1 / Aşama 2: güvenlik ağı).
#
# Amaç: bir değişiklikten sonra "sadece hedef olay etkilendi, diğer olayların promptu birebir aynı" diye kanıtlamak.
# Yapılandırılmış hattaki her AKTİF olay için 20 sabit tohumla (1-20) üretim kodu yolundan (creative_pipeline.
# build_creative_scene) seçim + Kie'ye gidecek son prompt kurulur. GPT çağrılmaz: sahte GPT kapıdan geçemeyen dilim
# döndürür, hat kendi onaylı kod yedeğine (es.build_fallback) düşer. Kie, Notion, Telegram ve hikâye kaynağı günlüğü
# (data/story_source_log.jsonl) yok. Her tohumda süreç hafızaları boşaltılır, geçmiş boştur: aynı tohum = aynı sonuç.
#
# Kullanım (proje kökünden):
#   .venv\Scripts\python.exe scripts\prompt_snapshot.py baseline   -> tests/snapshots/prompts_baseline.json
#   .venv\Scripts\python.exe scripts\prompt_snapshot.py diff       -> baseline ile karşılaştırır (çıkış 1 = fark var)
import asyncio
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

BASELINE = os.path.join(ROOT, "tests", "snapshots", "prompts_baseline.json")
SEEDS = tuple(range(1, 21))
# GPT yerine: alanlar dolu (şema geçer) ama kelime sınırı tutmaz -> kapı reddi -> kod yedeği (üretimdeki yol)
FAKE_SLICES = {"slice_1_rest": "x", "slice_2": "x", "slice_3": "x"}


def _modules():
    import core.event_structure as es   # önce bu: creative_pipeline ile döngüsel import (üretimdeki sıra)
    import core.creative_pipeline as cp
    import core.skeleton_pipeline as sk
    return cp, es, sk


def active_events() -> list[str]:
    """Yapılandırılmış hattaki aktif olaylar (DISABLED_EVENTS hariç), havuz sırasıyla."""
    _, es, sk = _modules()
    return [e for e in es.structured_events() if e not in sk.DISABLED_EVENTS]


def reset_memory() -> None:
    """Süreç içi LRU hafızalarını boşaltır (görünüm, beat, çığ/deprem ortamı, ateş hortumu, volkan ortamı ve yeri)."""
    _, es, sk = _modules()
    for mem in (sk._VIEW_MEMORY, es._BEAT_MEMORY, es._ENV_MEMORY, es._EQ_ENV_MEMORY, es._FIRE_TOR_ENV_MEMORY,
                es._VOLC_ENV_MEMORY, es._VOLC_SPOT_MEMORY, es._AXES_MEMORY):   # 21 Eki: eksen hafızası
        mem.clear()


async def _fake_gpt(*args, **kwargs):
    return dict(FAKE_SLICES)


def build(event: str, history: list[str] | None = None, history_texts: list[str] | None = None,
          axes_loader=None) -> dict:
    """Tek üretim (seçim + kod yedeği hikâyesi + son prompt). Rastgelelik çağıranın tohumundan gelir. axes_loader:
    21 Eki, sahte Notion eksen geçmişi (domain -> ham kayıtlar); None = üretimdeki yükleyicisiz yol (eski davranış)."""
    cp, es, _ = _modules()
    real_record = cp.record_story_source
    cp.record_story_source = lambda entry: None   # günlüğe yazılmaz
    try:
        scene = asyncio.run(cp.build_creative_scene(None, event, list(history or []), list(history_texts or []),
                                                    _fake_gpt, axes_loader=axes_loader))
    finally:
        cp.record_story_source = real_record
    return scene


def axes(scene: dict) -> dict:
    """Seçilen eksen değerleri (rapor ve karşılaştırma için)."""
    t = scene["trace"]
    env = t.get("environment")
    return {"spot": scene["spot"], "view": t.get("view"), "weather": t.get("weather"),
            "environment": (t.get("fire_env") or t.get("volc_env") or t.get("scene_env")
                            or (" · ".join(f"{k}={v}" for k, v in env.items() if k != "spot") if env else None)),
            "vehicle": t.get("vehicle"), "people": t.get("people_running"), "beats": t.get("beats"),
            "key_visual": t.get("key_visual"),
            "story_source": (scene.get("structure") or {}).get("story_source_kind"),
            # 21 Eki (Aşama 4): kadraj ekseni
            **{k: (t.get("axes") or {}).get(k) for k in ("kadraj", "on_plan", "kamera_modu", "kamera_noktasi")},
            # 21 Eki (Aşama 5): K5 sığma koruması devreye girdi mi (kadraj/ortam bütçe yüzünden değişti)
            "fit_guard": bool((t.get("axes_excluded") or {}).get("kadraj_sığmadı"))}


def snapshot_event(event: str, seed: int) -> dict:
    """Tek tohum. Kurulamayan üretim (ör. kod yedeği sığmadı) hata metniyle kaydedilir; o da karşılaştırılır."""
    reset_memory()
    random.seed(seed)
    try:
        scene = build(event)
    except Exception as e:   # noqa: BLE001 - davranışı kaydetmek amaç
        return {"error": f"{type(e).__name__}: {e}"}
    return {"axes": axes(scene), "prompt": scene["prompt"], "style_suffix": scene["style_suffix"],
            "combo_key": scene["combo_key"]}


def snapshot_all(events: list[str] | None = None, seeds=SEEDS) -> dict:
    events = events or active_events()
    return {e: {str(s): snapshot_event(e, s) for s in seeds} for e in events}


def diff(base: dict, now: dict) -> dict:
    """{olay: {"changed": [tohum], "first": (tohum, önce, sonra) | None, "note": str}}; sadece farklı olanlar."""
    out = {}
    for e in sorted(set(base) | set(now)):
        if e not in now:
            out[e] = {"changed": sorted(base[e], key=int), "first": None, "note": "olay artık yok"}
            continue
        if e not in base:
            out[e] = {"changed": sorted(now[e], key=int), "first": None, "note": "yeni olay (baseline'da yok)"}
            continue
        changed = [s for s in sorted(set(base[e]) | set(now[e]), key=int) if base[e].get(s) != now[e].get(s)]
        if changed:
            s = changed[0]
            out[e] = {"changed": changed, "note": "",
                      "first": (s, (base[e].get(s) or {}).get("prompt"), (now[e].get(s) or {}).get("prompt"))}
    return out


def write_baseline(data: dict, path: str = BASELINE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def load_baseline(path: str = BASELINE) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "diff"
    if mode not in ("baseline", "diff"):
        print("Kullanım: prompt_snapshot.py baseline|diff")
        return 2
    now = snapshot_all()
    if mode == "baseline":
        write_baseline(now)
        print(f"Baseline yazıldı: {len(now)} olay × {len(SEEDS)} tohum -> {os.path.relpath(BASELINE, ROOT)}")
        return 0
    result = diff(load_baseline(), now)
    print(f"{len(result)} olay değişti")
    for e, r in result.items():
        print(f"\n■ {e}: {len(r['changed'])}/{len(SEEDS)} tohum değişti {r['note']}".rstrip())
        if r["first"]:
            s, before, after = r["first"]
            print(f"  İlk fark (tohum {s}):\n  ÖNCE : {before}\n  SONRA: {after}")
    return 1 if result else 0


if __name__ == "__main__":
    import logging
    logging.disable(logging.WARNING)   # üretim logları (kod yedeği uyarısı vb.) çıktıyı boğmasın
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
