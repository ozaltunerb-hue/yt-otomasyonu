# generate_prompts döngüsünün birebir aşağı-seviye kopyası; Kie ve metadata çağrısı YOK.
# 5 senaryo üretir (GPT-4o, ~$0.15), kapılardan geçirir, kazananı simplifier + stil kilidinden geçirir.
# Kullanım: python scripts/dry_run_beat1.py [cikti.json]
import asyncio, json, sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from config import settings
from core.creative_engine import get_creative_catalyst, choose_camera_archetype, apply_style_lock
from core.prompt_generator import (_generate_scenario, simplify_with_gate, NoValidScenarioError, validate_silent_visibility,
    validate_high_action, validate_beat3_ongoing_danger, validate_cast_size, validate_scenario_consistency, score_scenario)
from core.prompt_sanitizer import sanitize_prompt

async def main(out_path):
    assert not settings.IS_DRY_RUN, "IS_DRY_RUN açık, gerçek GPT çağrısı olmaz"
    used, hist, rows = [], [], []
    for i in range(5):
        for _ in range(50):
            cat = get_creative_catalyst(recent_history=hist)
            cam = choose_camera_archetype(cat["domain_id"])
            key = f"{cat['domain_id']}|{cat['forced_ship'].lower()}|{cat['forced_event'].lower()}|{cat['forced_environment'].lower()}|{cam}"
            if key not in used: break
        sc = await _generate_scenario(cat, cam)
        v_ok, v_f = validate_silent_visibility(sc)
        a_ok, a_f = validate_high_action(sc)
        b_ok, b_f = validate_beat3_ongoing_danger(sc)
        c_ok, c_f = validate_cast_size(sc, cat["domain_id"])
        s_ok, s_f = validate_scenario_consistency(sc)
        hist.append(key); used.append(key)
        ok = v_ok and a_ok and b_ok and c_ok and s_ok
        rows.append({"n": i+1, "domain": cat["domain_id"], "camera": cam, "ship": cat["forced_ship"],
                     "event": cat["forced_event"], "accepted": ok, "failures": v_f + a_f + b_f + c_f + s_f,
                     "score": score_scenario(sc) if ok else None, "scenario": sc, "catalyst": cat})
        print(f"--- #{i+1} {cat['domain_id']} | {cam} | ok={ok} score={rows[-1]['score']} fail={v_f+a_f+b_f+c_f+s_f}", flush=True)
    acc = [r for r in rows if r["accepted"]]
    out = {"rows": [{k: v for k, v in r.items() if k != "catalyst"} for r in rows]}
    if acc:
        # Üretimle aynı yol: skor sırası + simplifier çıktı kapısı + retry (NoValidScenarioError fırlatabilir)
        try:
            best, simp, attempts = await simplify_with_gate(acc)
        except NoValidScenarioError as e:
            out["simplifier_error"] = str(e)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2, default=str)
            print(f"SİMPLİFİER KAPISI: hiçbir senaryo geçmedi -> {out_path}")
            return
        out["simplifier_attempts"] = attempts
        for a in attempts:
            print(f"  simplifier deneme {a['attempt']}: fail={a['failures']} | {a['prompt'][:90]}", flush=True)
        raw = simp.get("prompt", "").strip()
        san, ch = sanitize_prompt(raw)
        out["winner"] = best["n"]; out["raw_prompt"] = raw; out["sanitized"] = san
        out["sanitize_changes"] = ch
        out["final_prompt"] = apply_style_lock(san if ch else raw, best["camera"], best["catalyst"])
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(f"DONE -> {out_path}")

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "dry_run_beat1_out.json"))
