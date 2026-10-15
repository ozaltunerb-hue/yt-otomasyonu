# Hibrit hikâye kuru denemesi (16 Eki 2026, Bahadır): yapılandırılmış hattın her olayı için gerçek GPT üretimleri,
# üretim kodu yolu (creative_pipeline.build_creative_scene: aynı model, aynı sistem/kullanıcı mesajı, aynı kapılar).
# Kie YOK, Notion YOK, Telegram YOK, onay yok. Sadece OpenAI (gpt-4o) çağrılır; çağrı sayısı ve gerçek token
# kullanımından hesaplanan maliyet sınırında durur.
# Her üretim için: eski kapıda (16 Eki öncesi: sıkı beat kapısı, sert eklemeler yok) ilk deneme geçer miydi, yeni kapıda
# (sert + yumuşak) geçti mi, yedeğe düştü mü, hangi kontrol kaldı.
# Kullanım: .venv\Scripts\python.exe scripts\dry_run_hybrid.py --per-event 20 --max-calls 600 --max-usd 3 [cikti.json]
import asyncio
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# gpt-4o liste fiyatı (USD / 1M token)
PRICE_IN, PRICE_OUT = 2.50, 10.00
NEW_ONLY_RULES = {"beat_object", "beat_other_object", "beat_vehicle", "hard_camera", "hard_place_name", "hard_death"}


class BudgetExhausted(RuntimeError):
    pass


def _opt(argv, name, default):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


async def main(out_path: str, per_event: int, max_calls: int, max_usd: float, only: list[str] | None):
    import core.event_structure as es   # önce (döngüsel import sırası)
    import core.creative_pipeline as cp
    import core.prompt_generator as pg
    from config import settings
    from core.skeleton_pipeline import EVENT_SKELETONS
    assert not settings.IS_DRY_RUN
    # Gerçek istatistik dosyası kirlenmesin: kuru deneme kendi kaydına yazar
    os.environ["STORY_SOURCE_LOG"] = os.path.splitext(out_path)[0] + "_source_log.jsonl"
    usage = {"calls": 0, "in": 0, "out": 0}

    def cost():
        return usage["in"] / 1e6 * PRICE_IN + usage["out"] / 1e6 * PRICE_OUT

    async def gpt(system, user, temperature=0.85, model="gpt-4o", json_schema=None):
        if usage["calls"] >= max_calls:
            raise BudgetExhausted(f"{max_calls} GPT çağrısı sınırı")
        if cost() >= max_usd:
            raise BudgetExhausted(f"tahmini maliyet {cost():.2f} $ >= {max_usd} $")
        usage["calls"] += 1
        client = pg._get_openai_client()
        rf = {"type": "json_schema", "json_schema": json_schema} if json_schema else {"type": "json_object"}
        resp = await asyncio.to_thread(client.chat.completions.create, model=model,
                                       messages=[{"role": "system", "content": system},
                                                 {"role": "user", "content": user}],
                                       temperature=temperature, max_tokens=1000, response_format=rf)
        usage["in"] += resp.usage.prompt_tokens
        usage["out"] += resp.usage.completion_tokens
        msg = resp.choices[0].message
        if json_schema and getattr(msg, "refusal", None):
            raise RuntimeError(f"GPT şemalı yanıtı reddetti: {msg.refusal}")
        return json.loads(msg.content)

    events = only or list(es.structured_events())
    combos, recent, rows = {e: [] for e in events}, [], []
    stopped = None
    for rnd in range(1, per_event + 1):
        for event in events:
            if stopped:
                break
            domain = EVENT_SKELETONS[event]["domain"]
            recent_before = cp.recent_stories(list(recent))
            row = {"event": event, "round": rnd}
            try:
                scene = await cp.build_creative_scene(domain, event, combos[event], list(recent), gpt)
            except BudgetExhausted as e:
                stopped = str(e)
                break
            except Exception as e:   # yedeğin sığmadığı çift (FALLBACK_GAPS) ya da API hatası: kaydedilir
                row.update(status="error", error=f"{type(e).__name__}: {e}")
                rows.append(row)
                print(f"[{rnd}] {event[:46]:46} HATA {row['error'][:120]}", flush=True)
                continue
            st, tr = scene["structure"], scene["trace"]
            spec = st["spec"]
            attempts = []
            for a in tr["attempts"]:
                sl = a["slices"]
                new_found = cp.structured_issues(spec, sl, recent_before)
                old_found = [i for i in new_found if i["rule"] not in NEW_ONLY_RULES] + es.strict_beat_issues(spec, sl)
                attempts.append({"attempt": a["attempt"], "slices": sl,
                                 "new_pass": not new_found, "new_rules": sorted({i["rule"] for i in new_found}),
                                 "new_missing": [i["missing"] for i in new_found],
                                 "old_pass": not old_found, "old_rules": sorted({i["rule"] for i in old_found}),
                                 "old_missing": [i["missing"] for i in old_found],
                                 "strict_beat_fail": sorted({i["missing"][:4] for i in es.strict_beat_issues(spec, sl)})})
            row.update(status="ok", source=st["story_source_kind"], label=st["story_source"], spot=scene["spot"],
                       view=tr.get("view"),
                       env=spec.get("fire_env") or spec.get("setting"), beats=tr["beats"], vehicle=tr.get("vehicle"),
                       people=spec.get("people"), attempts=attempts, story=scene["story"],
                       prompt_words=len(scene["prompt"].split()))
            rows.append(row)
            combos[event].append(scene["combo_key"])
            recent.append(scene["story"])
            a1 = attempts[0] if attempts else {}
            print(f"[{rnd}] {event[:46]:46} {row['source']:8} eski1={'✓' if a1.get('old_pass') else '✗'} "
                  f"yeni1={'✓' if a1.get('new_pass') else '✗'} {tr['beats']} · {usage['calls']} çağrı "
                  f"{cost():.2f}$ · {'; '.join(a1.get('new_missing') or [])[:110]}", flush=True)
        if stopped:
            break

    # Özet
    summary = {}
    for event in events:
        ev = [r for r in rows if r["event"] == event and r["status"] == "ok"]
        n = len(ev)
        old1 = sum(1 for r in ev if r["attempts"] and r["attempts"][0]["old_pass"])
        new1 = sum(1 for r in ev if r["attempts"] and r["attempts"][0]["new_pass"])
        fb = [r for r in ev if r["source"] == "fallback"]
        reasons = collections.Counter(m.split(" (")[0] for r in fb for m in r["attempts"][-1]["new_missing"])
        errs = [r["error"] for r in rows if r["event"] == event and r["status"] == "error"]
        summary[event] = {"n": n, "old_first_pass": old1, "new_first_pass": new1, "fallback": len(fb),
                          "fallback_pct": round(100 * len(fb) / n, 1) if n else None,
                          "top_fallback_reasons": reasons.most_common(5), "errors": errs}
    result = {"gpt_calls": usage["calls"], "tokens_in": usage["in"], "tokens_out": usage["out"],
              "cost_usd": round(cost(), 3), "stopped": stopped, "summary": summary, "rows": rows}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(f"\nGPT çağrısı: {usage['calls']} · token {usage['in']}/{usage['out']} · maliyet ~{cost():.2f} $ · "
          f"durma: {stopped or '-'} · DONE -> {out_path}")


FIXTURE = os.path.join(ROOT, "tests", "fixtures", "rejected_real.json")


def false_rejections(result: dict, date: str) -> list[dict]:
    """Eski beat kapısının reddettiği ama yeni (yumuşak) beat kapısının geçirdiği GPT cümleleri. Üretimi birebir
    yeniden kurmak için olay, nokta, görünüm, araç, kişi ve beat çifti de yazılır."""
    import core.event_structure as es
    out, seen = [], set()
    for r in result["rows"]:
        if r.get("status") != "ok":
            continue
        b2, b3 = r["beats"].split("+")
        for a in r["attempts"]:
            spec = es.build_spec(r["event"], None, r["spot"], _view_of(r), b2, b3, r.get("vehicle"), r.get("people"),
                                 r["env"] if r["env"] and r["env"].startswith("Setting:") else None)
            strict = {i["missing"][:4] for i in es.strict_beat_issues(spec, a["slices"])}
            soft = {i["missing"][:4] for i in es.soft_beat_issues(spec, a["slices"])}
            for label, slot, bid in (("4-9s", "slice_2", b2), ("9-15", "slice_3", b3)):
                text = a["slices"][slot]
                if label in strict and label not in soft and text not in seen:
                    seen.add(text)
                    out.append({"date": date, "source": "2i kuru prova (hibrit hikâye)", "event": r["event"],
                                "beat": bid, "vehicle": r.get("vehicle") if slot == "slice_2" else None,
                                "spot": r["spot"], "view": _view_of(r), "beats": r["beats"],
                                "people": r.get("people"), "text": text})
    return out


def _view_of(row: dict):
    """Satırın görünümü (eski kayıtlarda yoksa aracı ve noktası uyan ilk görünüm: beat kapısı sadece araç terimine
    bakar, aynı araç adı her görünümde aynı terimlerle)."""
    import core.event_structure as es
    from core.skeleton_pipeline import view_spots
    if row.get("view") or None not in es.structure_views(row["event"]):
        return row.get("view") or next(v for v in es.structure_views(row["event"])
                                       if row["spot"] in view_spots(row["event"], v)
                                       and any(n == row.get("vehicle") for n, _ in es.REGION_VEHICLES[v]))
    return None


def add_to_fixture(entries: list[dict], path: str = FIXTURE) -> int:
    data = json.load(open(path, encoding="utf-8"))
    have = {x["text"] for x in data["false_rejections"]}
    new = [e for e in entries if e["text"] not in have]
    data["false_rejections"].extend(new)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return len(new)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:]
    fixtures_from = _opt(argv, "--fixtures-from", None)
    if fixtures_from:   # kuru deneme sonucundan yanlış retleri tests/fixtures/rejected_real.json'a ekle
        res = json.load(open(fixtures_from, encoding="utf-8"))
        n = add_to_fixture(false_rejections(res, _opt(argv, "--date", "2026-10-16")))
        print(f"rejected_real.json: {n} yeni yanlış ret eklendi")
        sys.exit(0)
    per_event = int(_opt(argv, "--per-event", "20"))
    max_calls = int(_opt(argv, "--max-calls", "600"))
    max_usd = float(_opt(argv, "--max-usd", "3"))
    events = _opt(argv, "--events", None)
    out = argv[0] if argv else os.path.join(ROOT, "scratch", "dry_run_hybrid.json")
    asyncio.run(main(out, per_event, max_calls, max_usd, events.split(";") if events else None))
