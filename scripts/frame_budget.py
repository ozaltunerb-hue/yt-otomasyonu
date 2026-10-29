# K5 kombinasyon denetimi (21 Eki 2026, Gece 1 / Aşama 4). Üretimi değiştirmez, sadece ölçer. GPT/Kie/Notion yok.
#
# Her yapılandırılmış aktif olayda her spot × görünüm × (volkan ortamı) × izinli beat çifti × araç için kod yedeğinin
# 175 kelimeye (ve karakter sınırına) sığıp sığmadığı:
#   önce   : bugünkü kamera cümlesi (frame yok)
#   varyant: her kadraj varyantı (core.frame_axis.all_frames, beat'lerin riskli spot süzgeciyle)
#   sonra  : en az bir kadraj varyantı sığıyor mu (üretimdeki sığma koruması)
# Çığ/deprem ortam satırı en uzun hâliyle (en kötü durum). Kişi sayısı aralığın en büyüğü.
#
# Kullanım: .venv\Scripts\python.exe scripts\frame_budget.py [--md yol]
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402


def _longest_setting(event: str) -> str | None:
    import core.event_structure as es
    if event == es.METEOR:   # 29 Eki: meteor ortam + ışık satırı (en uzun)
        import core.skeleton_pipeline as sk
        return max((es.meteor_setting(e, li) for e in es.METEOR_ENVS for li in sk.METEOR_WEATHER),
                   key=lambda x: len(x.split()))
    if event not in es.ENV_EVENTS:
        return None
    if event in es.EARTHQUAKE_EVENTS:
        envs = [{"city": c, "street": st, "light": li} for c in es.EQ_EVENT_CITIES[event]
                for st in es.EQ_EVENT_STREETS[event] for li in es.EQ_ENV_AXES["light"]]
    else:
        envs = [{"mountain": m, "village": v, "light": li} for m in es.ENV_AXES["mountain"]
                for v in es.ENV_AXES["village"] for li in es.ENV_AXES["light"]]
    lines = [es.setting_line(e) for e in envs if len(es.setting_line(e).split()) <= es.SETTING_MAX_WORDS]
    return max(lines, key=lambda x: len(x.split()))


def measure(event: str) -> dict:
    """Kombinasyon = görünüm × spot × beat çifti × araç × (volkan ortamı) × (ortam) × (açılış: Aşama 6). Her kombinasyonda
    kadraj varyantlarından en az biri kod yedeğini 175'e sığdırmalı (üretimdeki sığma koruması) ve sığan ilk varyantın
    kod yedeği son denetimden geçmeli (gate_fail: olay adı, ilk cümle tetiği, yasak kelime... açılışlar dahil)."""
    import core.event_structure as es
    import core.frame_axis as fx
    import core.opening_axis as ox
    import core.scene_env as sv
    import core.skeleton_pipeline as sk
    setting = _longest_setting(event)
    lo, hi = sk.count_range(event, None)
    people = hi if es.has_people_rule(event) else None
    volc_envs = list(sk.VOLC_ENVS) if event in es.VOLC_ENV_EVENTS else [None]
    out = {"combos": 0, "before_fail": 0, "after_fail": 0, "variants": 0, "variant_fail": 0, "max_suffix": 0,
           "gate_fail": 0, "env_reset": 0}
    beats = es.EVENT_BEATS[event]["excluded_spots"]
    for view in es.structure_views(event):
        for spot in sk.view_spots(event, view):
            pool = (list(es.FIRE_TOR_ENVS[es.fire_env_of_spot(spot)]["spots"]) if event == es.FIRE_TORNADO
                    else sk.view_spots(event, view))
            vehicles = [v for v, _ in es.event_vehicles(event, view)] if es.uses_vehicle(event) else [None]
            scene_envs = sv.compatible_envs(event, spot) if event in sv.SCENE_ENVS else [None]
            for b2, b3 in es.allowed_pairs(event, view, spot):
                risky = set(beats.get(b2, set())) | set(beats.get(b3, set()))
                for veh in vehicles:
                    for venv in volc_envs:
                        for senv0 in scene_envs:
                            senv, openings = senv0, ([None] if event not in ox.OPENINGS
                                                     else ox.allowed(event, senv0, b2, b3))
                            if not openings:   # üretimdeki gibi: ortam A'ya döner
                                out["env_reset"] += 1
                                senv, openings = sv.ENV_A, ox.allowed(event, sv.ENV_A, b2, b3)
                            for op in openings:
                                out["combos"] += 1
                                base = es.build_spec(event, None, spot, view, b2, b3, veh, people, setting, venv,
                                                     None, None, op)
                                out["before_fail"] += not es.fallback_candidates(base)
                                frames = [(senv, f) for f in fx.all_frames(event, spot, pool, risky,
                                                                           sv.excluded_positions(event, senv))]
                                if senv not in (None, "A"):   # üretimdeki koruma: en son ortam A'ya döner
                                    frames += [("A", f) for f in fx.all_frames(event, spot, pool, risky)]
                                first = None
                                for env_used, f in frames:
                                    spec = es.build_spec(event, None, spot, view, b2, b3, veh, people, setting, venv,
                                                         f, env_used, op)
                                    cands = es.fallback_candidates(spec)
                                    out["variants"] += 1
                                    out["variant_fail"] += not cands
                                    out["max_suffix"] = max(out["max_suffix"], len(spec["suffix"].split()))
                                    if cands and first is None:
                                        first = (spec, cands[0])
                                out["after_fail"] += first is None
                                if first is not None:
                                    spec, sl = first
                                    prompt = es.assemble_prompt(spec, sl)
                                    out["gate_fail"] += bool(es.final_prompt_issues(spec, sl, prompt,
                                                                                    es.assemble_story(spec, sl)))
    return out


def main(argv: list[str]) -> int:
    rows = {e: measure(e) for e in ps.active_events()}
    lines = ["| Olay | kombinasyon | kod yedeği sığmıyor: önce | sonra (koruma ile) | son denetimden kalan | "
             "sığmayan kadraj varyantı | en uzun stil eki |", "|---|---|---|---|---|---|---|"]
    for e, m in rows.items():
        lines.append(f"| {e} | {m['combos']} | {m['before_fail']} | {m['after_fail']} | {m['gate_fail']} | "
                     f"{m['variant_fail']}/{m['variants']} | {m['max_suffix']} |")
    tot = {k: sum(m[k] for m in rows.values()) for k in ("combos", "before_fail", "after_fail", "variants",
                                                          "variant_fail", "gate_fail")}
    lines.append(f"| **Toplam** | {tot['combos']} | {tot['before_fail']} | {tot['after_fail']} | {tot['gate_fail']} | "
                 f"{tot['variant_fail']}/{tot['variants']} | |")
    md = "\n".join(lines)
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
