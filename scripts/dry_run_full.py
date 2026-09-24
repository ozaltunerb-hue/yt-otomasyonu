# Tam dry-run: 5 senaryo, üretimdeki tüm senaryo kapıları + koşu içi Beat 1 fiil rotasyonu; kabul edilen
# her aday ayrı ayrı simplify_with_gate'ten geçer (retry sayısı ölçülür). GPT-4o (~$0.15), Kie YOK.
# Kullanım: python scripts/dry_run_full.py [cikti.json]   (varsayılan: scratch/dry_run_full_out.json)
import asyncio, json, sys, os, io
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from config import settings
from core.creative_engine import get_creative_catalyst, choose_camera_archetype, ENV_CENTRIC_DOMAINS
from core.prompt_generator import (_generate_scenario, simplify_with_gate, NoValidScenarioError, validate_silent_visibility,
    validate_high_action, validate_beat3_ongoing_danger, validate_cast_size, validate_scenario_consistency,
    validate_ship_setting, score_scenario, _person_mentions)


async def main(out_path: str):
    sys.stdout.reconfigure(encoding="utf-8")
    assert not settings.IS_DRY_RUN
    used, hist, rows, verbs = [], [], [], []
    for i in range(5):
        for _ in range(50):
            cat = get_creative_catalyst(recent_history=hist)
            cam = choose_camera_archetype(cat["domain_id"])
            key = f"{cat['domain_id']}|{cat['forced_ship'].lower()}|{cat['forced_event'].lower()}|{cat['forced_environment'].lower()}|{cam}"
            if key not in used:
                break
        cat["recent_verbs"] = list(verbs)   # üretimle aynı: koşu içi fiil rotasyonu (TUR 17)
        sc = await _generate_scenario(cat, cam)
        if sc.get("beat1_action_verb"):
            verbs.insert(0, sc["beat1_action_verb"].lower())
        checks = {
            "visibility": validate_silent_visibility(sc), "high_action": validate_high_action(sc),
            "beat3": validate_beat3_ongoing_danger(sc), "cast": validate_cast_size(sc, cat["domain_id"]),
            "consistency": validate_scenario_consistency(sc), "ship_setting": validate_ship_setting(sc, cat["forced_ship"]),
        }
        hist.append(key); used.append(key)
        ok = all(v[0] for v in checks.values())
        people = [p for k in ("visible_start", "physical_movement", "visible_consequence") for p in _person_mentions(sc.get(k, ""))]
        row = {"n": i + 1, "domain": cat["domain_id"], "env": cat["domain_id"] in ENV_CENTRIC_DOMAINS, "camera": cam,
               "ship": cat["forced_ship"], "event": cat["forced_event"], "environment": cat["forced_environment"],
               "accepted": ok, "failed_gates": {k: v[1] for k, v in checks.items() if not v[0]},
               "people": people, "score": score_scenario(sc) if ok else None, "scenario": sc}
        if ok:
            cand = {"scenario": sc, "catalyst": cat, "score": row["score"], "camera": cam, "n": i + 1}
            try:
                _, simp, attempts = await simplify_with_gate([cand])
                row["simplifier"] = {"passed": True, "attempts": attempts, "prompt": simp.get("prompt", "")}
            except NoValidScenarioError as e:
                row["simplifier"] = {"passed": False, "error": str(e)[:1500]}
        rows.append(row)
        s = row.get("simplifier", {})
        print(f"#{i+1} {cat['domain_id']} | {cam} | ship={cat['forced_ship']} | env={cat['forced_environment']} | "
              f"verb={sc.get('beat1_action_verb')} | ok={ok} fail={row['failed_gates']} | people={people} | "
              f"simp={'-' if not s else (str(len(s['attempts'])) + ' deneme' if s.get('passed') else 'KALDI')}", flush=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump({"rows": rows}, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
    print(f"DONE -> {out_path}")


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "scratch", "dry_run_full_out.json")
    asyncio.run(main(out_path))
