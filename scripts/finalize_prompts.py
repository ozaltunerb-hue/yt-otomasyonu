# Dry-run'dan seçilen senaryoları üretimle aynı yoldan geçirir: simplify_with_gate (tüm çıktı kapıları +
# retry) → regex sanitizer → stil eki. Kie'ye gidecek hikaye + stil ekini ayrı yazar (TUR 12).
# Kullanım: python scripts/finalize_prompts.py <dry_run_out.json> <n1,n2,...> [cikti.json]
#           (varsayılan çıktı: scratch/final_prompts.json). GPT çağrısı yapar, Kie YOK.
import asyncio, json, sys, os, io
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core.creative_engine import join_story_and_style, style_lock_suffix
from core.prompt_generator import simplify_with_gate
from core.prompt_sanitizer import sanitize_prompt


async def main(src: str, picks: list[int], out_path: str):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    rows = json.load(open(src, encoding="utf-8"))["rows"]
    res = []
    for n in picks:
        r = next(x for x in rows if x["n"] == n)
        cat = {"domain_id": r["domain"], "forced_ship": r["ship"], "forced_event": r["event"],
               "forced_environment": r.get("environment", "")}
        cand = {"scenario": r["scenario"], "catalyst": cat, "score": r["score"], "camera": r["camera"], "n": n}
        _, simp, attempts = await simplify_with_gate([cand])
        raw = simp.get("prompt", "").strip()
        san, changes = sanitize_prompt(raw)
        story = san if changes else raw
        suffix = style_lock_suffix(r["camera"], cat)
        res.append({"n": n, "domain": r["domain"], "camera": r["camera"], "ship": r["ship"], "attempts": attempts,
                    "story": story, "style_suffix": suffix, "sanitize_changes": changes,
                    "final_prompt": join_story_and_style(story, suffix)})
        print(f"#{n} {r['domain']} | {r['camera']} | denemeler={[a['failures'] for a in attempts]}\nHİKAYE: {story}\n")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(res, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
    print(f"DONE -> {out_path}")


if __name__ == "__main__":
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "scratch", "final_prompts.json")
    asyncio.run(main(sys.argv[1], [int(x) for x in sys.argv[2].split(",")], out))
