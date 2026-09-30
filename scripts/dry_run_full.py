# Tam dry-run: 5 senaryo, üretimdeki tüm senaryo kapıları + koşu içi Beat 1 fiil rotasyonu; kabul edilen
# her aday ayrı ayrı simplify_with_gate'ten geçer (retry sayısı ölçülür). GPT-4o (~$0.15), Kie YOK.
# Kullanım: python scripts/dry_run_full.py [cikti.json]   (varsayılan: scratch/dry_run_full_out.json)
# Creative kural kapısı kuru provası (30 Eyl): python scripts/dry_run_full.py --creative [cikti.json]
#   22 olayın her biri için 2 hikâye (üretimdeki build_creative_scene: 3 deneme + kural kapısı), sadece GPT-4o;
#   Kie YOK, preflight YOK, en fazla 100 GPT çağrısı. Varsayılan çıktı: scratch/dry_run_creative_out.json
import asyncio, json, sys, os, io, itertools, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from config import settings
from core.creative_engine import get_creative_catalyst, choose_camera_archetype, ENV_CENTRIC_DOMAINS
from core.prompt_generator import (_generate_scenario, simplify_with_gate, NoValidScenarioError,
    scenario_gate_results, score_scenario, _person_mentions)


async def main(out_path: str):
    sys.stdout.reconfigure(encoding="utf-8")
    assert not settings.IS_DRY_RUN
    used, hist, rows, verbs = [], [], [], []
    for i in range(5):
        for _ in range(50):
            cat = get_creative_catalyst(recent_history=hist)
            cam = choose_camera_archetype(cat["domain_id"], cat["forced_environment"])
            key = f"{cat['domain_id']}|{cat['forced_ship'].lower()}|{cat['forced_event'].lower()}|{cat['forced_environment'].lower()}|{cam}"
            if key not in used:
                break
        cat["recent_verbs"] = list(verbs)   # üretimle aynı: koşu içi fiil rotasyonu (TUR 17)
        sc = await _generate_scenario(cat, cam)
        if sc.get("beat1_action_verb"):
            verbs.insert(0, sc["beat1_action_verb"].lower())
        checks = scenario_gate_results(sc, cat)   # üretimle aynı kapı listesi (TUR 24: tetik + fizik dahil)
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


MAX_GPT_CALLS = 100
STORIES_PER_EVENT = 2


class GptBudgetExhausted(RuntimeError):
    pass


def _words(t: str) -> set[str]:
    return set(re.findall(r"[a-z]+", (t or "").lower()))


def jaccard(a: str, b: str) -> float:
    """Eski örtüşme ölçümü (29-30 Eyl creative kanıt koşusu): kelime kümesi Jaccard, 1 = aynı."""
    A, B = _words(a), _words(b)
    return len(A & B) / len(A | B) if A | B else 0.0


async def main_creative(out_path: str):
    import core.prompt_generator as pg
    from core.creative_pipeline import (CreativeStoryError, EVENT_OUTCOMES, MAX_ATTEMPTS, REQUIRED_APPROVED,
                                        build_creative_scene)
    from core.skeleton_pipeline import EVENT_SKELETONS
    sys.stdout.reconfigure(encoding="utf-8")
    assert not settings.IS_DRY_RUN
    calls = {"n": 0}

    async def gpt(system, user, temperature=0.85, model="gpt-4o"):
        if calls["n"] >= MAX_GPT_CALLS:
            raise GptBudgetExhausted(f"{MAX_GPT_CALLS} GPT çağrısı sınırı doldu")
        calls["n"] += 1
        return await pg._call_gpt(system, user, temperature=temperature, model=model)

    events = list(REQUIRED_APPROVED) + [e for e in EVENT_OUTCOMES if e not in REQUIRED_APPROVED]
    combos, recent, rows = [], [], []
    stopped = None
    for rnd in range(1, STORIES_PER_EVENT + 1):
        for event in events:
            if stopped:
                rows.append({"event": event, "round": rnd, "status": "not_run", "reason": stopped})
                continue
            domain = EVENT_SKELETONS[event]["domain"]
            row = {"event": event, "round": rnd, "domain": domain}
            try:
                scene = await build_creative_scene(domain, event, combos, list(recent), gpt)
                t = scene["trace"]
                row.update(status="passed", ship=scene["ship"], spot=scene["spot"], weather=t["weather"],
                           attempts=t["attempts"], story=scene["story"], prompt=scene["prompt"])
                combos.append(scene["combo_key"])
                recent.append(scene["story"])
            except CreativeStoryError as e:
                t = getattr(e, "trace", {}) or {}
                row.update(status="failed", ship=t.get("ship"), spot=t.get("spot"), weather=t.get("weather"),
                           attempts=e.attempts, story=(e.attempts[-1]["story"] if e.attempts else ""))
            except GptBudgetExhausted as e:
                stopped = str(e)
                row.update(status="not_run", reason=stopped)
            row["n_attempts"] = len(row.get("attempts") or [])
            rows.append(row)
            miss = " | ".join("; ".join(a["missing"]) or "✅" for a in row.get("attempts") or [])
            print(f"[{rnd}] {event[:48]:48} {row['status']:7} deneme={row['n_attempts']} {miss}", flush=True)

    summary = {}
    for event in events:
        ev = [r for r in rows if r["event"] == event and r["status"] != "not_run"]
        stories = [r["story"] for r in ev if r["status"] == "passed"]
        summary[event] = {
            "run": len(ev), "passed": sum(r["status"] == "passed" for r in ev),
            "avg_attempts": round(sum(r["n_attempts"] for r in ev) / len(ev), 2) if ev else None,
            "jaccard_pairs": [round(jaccard(a, b), 2) for a, b in itertools.combinations(stories, 2)],
        }
    passed = [r["story"] for r in rows if r["status"] == "passed"]
    cross = [jaccard(a, b) for a, b in itertools.combinations(passed, 2)]
    result = {"gpt_calls": calls["n"], "max_attempts": MAX_ATTEMPTS, "stopped": stopped, "summary": summary,
              "all_pairs_jaccard": {"min": round(min(cross), 2), "max": round(max(cross), 2),
                                    "mean": round(sum(cross) / len(cross), 2)} if cross else None,
              "rows": rows}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
    print(f"GPT çağrısı: {calls['n']} · DONE -> {out_path}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--creative"]
    if "--creative" in sys.argv[1:]:
        out_path = args[0] if args else os.path.join(ROOT, "scratch", "dry_run_creative_out.json")
        asyncio.run(main_creative(out_path))
    else:
        out_path = args[0] if args else os.path.join(ROOT, "scratch", "dry_run_full_out.json")
        asyncio.run(main(out_path))
