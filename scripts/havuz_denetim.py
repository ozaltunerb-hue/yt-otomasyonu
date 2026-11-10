# Havuz denetimi (11 Kas 2026, Bahadır: Bölüm A1, B1, D). SADECE OKUMA: üretimi değiştirmez; GPT/Kie/Notion yok.
#
# Her olay için eksenlerin tam listesi (spot, kadraj, ön plan, ortam, açılış, ışık, orta, final, insan, araç), aktif/pasif
# durumu, hit (100K+ paylaşım) kullanımı; spot -> kadraj -> ön plan eşleşmesi; eksen başına aktif seçenek sayısı; 40 art
# arda basış simülasyonu (eksen geçmişi sıfırdan, sahte Notion kaydı ile üretimdeki LRU yolu; GPT'siz, kod seçimi).
#
# Kullanım (proje kökünden):
#   .venv\Scripts\python.exe scripts\havuz_denetim.py --events kilitli --md reports\havuz_denetim_2026-11-11.md
#   .venv\Scripts\python.exe scripts\havuz_denetim.py --events "Pyroclastic cloud races down into a village street"
import argparse
import collections
import logging
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402

# ── Hit (100K+) paylaşımları ve eşleşen üretim (Notion Paylaşımlar + dashboard_data/notion_runs.json, 11 Kas okuması).
# Paylaşım ile üretim arasında doğrudan bağ yok: eşleşme tarih (paylaşımdan önceki tamamlanmış üretim), olay, açıklama
# ve Paylaşımlar notuyla. "aday" = birden çok üretim olası. 21 Eki öncesi üretimlerde açılış A, kamera mod A (eski cümle).
HITS = {
    "Pyroclastic cloud races down into a village street": [
        {"share": "13 Eki 2,13M", "prod": "13 Eki 11:23", "spot": "Hillside terrace facing the erupting volcano",
         "beats": ("P2", "Q1"), "acilis": "A", "light": "ash-grey sky lit orange by a distant eruption plume"},
        {"share": "25 Eki 102K", "prod": "17 Eki 14:13", "spot": "Rooftop terrace facing the erupting volcano",
         "beats": ("P2", "Q5"), "acilis": "A"}],
    "Tidal wave surges over a coastal city street": [
        {"share": "24 Eyl 1,42M", "prod": "24 Eyl (yapılandırılmış hat öncesi, kayıt yok)", "note": "yüksek balkon, mod A"},
        {"share": "3 Eki 135K", "prod": "1 Eki / 3 Eki (beat'siz)", "note": "korkuluk ön planı: promenat (aday)"},
        {"share": "13 Eki 247K", "prod": "aday: 4 Eki 11:06 T7+W1 (seawall) ya da 4 Eki 10:16 T5+W5 (seawall)",
         "beats": ("T7", "W1", "T5", "W5"), "candidate": True, "acilis": "A",
         "note": "açıklama 'cleared the sea wall... cars were swept away': 11:06'ya yakın, kesin değil"}],
    "Wall of flames sweeps into a hillside neighborhood": [
        {"share": "19 Eki 3,02M", "prod": "9 Eki 21:52", "spot": "Balcony of a hillside house", "beats": ("K5", "L4"),
         "acilis": "A", "note": "kamera mod A (eye level, pans to follow): yüksek-sabit kuralı gereği rotasyonda değil"},
        {"share": "31 Eki 107K", "prod": "31 Eki 09:44", "spot": "Embankment above the village road",
         "beats": ("K2", "L5"), "acilis": "A", "ortam": "A", "kadraj": "çatı", "on_plan": "parapet",
         "light": "harsh bright midday sun through the smoke"}],
    "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood": [
        {"share": "12 Eki 170K", "prod": "9 Eki 22:52", "spot": "Balcony of a hillside house", "beats": ("F1", "G2"),
         "acilis": "A"}],
    "Tornado making landfall": [
        {"share": "1 Kas 10,37M", "prod": "31 Eki 09:52", "spot": "Residential coastal district", "beats": ("C1", "E1"),
         "acilis": "C", "kadraj": "pencere", "ortam": "C", "note": "kamera 7-8. sn'de pencereden dönüyor (7.5/10)"}],
    "Volcanic bombs slam into a village street": [
        {"share": "10 Eki 1,36M", "prod": "10 Eki 02:06", "spot": "Rooftop terrace facing the erupting volcano",
         "beats": ("R4", "T2"), "acilis": "A", "light": "ash-grey sky lit orange by a distant eruption plume"}],
    "Mud and debris torrent tears through a hillside village": [
        {"share": "2 Eki 431K", "prod": "1 Eki 22:09 (beat'siz)", "spot": "High steps on the village square",
         "acilis": "A"}],
    "Flash flooding in city streets": [
        {"share": "29 Eyl 338K / 4 Eki 132K / 6 Eki 305K", "prod": "26 Eyl-3 Eki (beat'siz)", "acilis": "A",
         "note": "beat kimliği yok; kilit 3249de8 hâli"}],
    "Tornado tears past the Statue of Liberty into Battery Park": [],
    "Fire tornado tears across a burning roadside": [
        {"share": "9 Eki 673K", "prod": "8 Eki 21:23 (eski ortamsız nokta)", "beats": ("T4", "U2"), "acilis": "A"},
        {"share": "26 Eki 176K", "prod": "aday: 16 Eki 13:45 T1+U8 (köy)", "beats": ("T1", "U8"), "candidate": True}],
}


def _m():
    import core.event_structure as es
    import core.creative_pipeline as cp
    import core.frame_axis as fx
    import core.opening_axis as ox
    import core.proven_axes as pa
    import core.scene_env as sv
    import core.skeleton_pipeline as sk
    return es, cp, fx, ox, pa, sv, sk


def hit_marks(event: str, axis: str, value) -> str:
    out = []
    for h in HITS.get(event, []):
        if axis == "beat" and value in h.get("beats", ()):
            out.append(h["share"] + (" (aday)" if h.get("candidate") else ""))
        elif axis in ("spot", "acilis", "kadraj", "on_plan", "light", "ortam") and h.get(axis) == value:
            out.append(h["share"])
    return "; ".join(out)


def _status_beat(event, bid):
    es = _m()[0]
    if bid in es.disabled_beats(event):
        return "PASİF"
    if bid in es.TRIAL_BEATS.get(event, set()):
        return "DENEME"
    return "aktif"


def axis_rows(event: str) -> dict:
    """{eksen: [(kimlik, metin, durum, hit)]}"""
    es, cp, fx, ox, pa, sv, sk = _m()
    rows = collections.OrderedDict()
    spots = list(sk.EVENT_SKELETONS[event]["spots"])
    rot_spots = set(pa.spots(event, spots)) if event in pa.PROVEN_SPOTS or event in pa.PASSIVE_SPOTS else set(spots)
    rows["spot"] = [(s, sk.CAMERA_SPOTS.get(s, ""), "aktif" if s in rot_spots else "PASİF/rotasyon dışı",
                     hit_marks(event, "spot", s)) for s in spots]
    # kadraj + ön plan (tüm varyantlar, rotasyon)
    kad, fgs = [], []
    seen_k, seen_f = set(), set()
    for s in spots:
        allv = fx.all_frames(event, s, sk.view_spots(event, None) if event not in sk.REGION_VIEW_EVENTS
                             else spots)
        rot = pa.allowed_variants(event, s, allv)
        for f in allv:
            key = (f["type"], f.get("pos_spot"), f.get("mode"))
            label = f"{f['type']} @ {f.get('pos_spot') or 'kütüphane'}" + (f" mod {f['mode']}" if f.get("mode") else "")
            try:
                cam = fx.frame_camera(event, s, f, legacy=sk.legacy_camera,
                                      volc_env="pastel_town" if event in es.VOLC_ENV_EVENTS else None,
                                      fire_env=es.fire_env_of_spot(s) if event == es.FIRE_TORNADO else None)
            except Exception as e:   # noqa: BLE001
                cam = f"(kurulamadı: {e})"
            st = "aktif" if f in rot else "rotasyon dışı"
            if key not in seen_k:
                seen_k.add(key)
                kad.append((label, sk.camera_rules(cam) if sk.EVENT_SKELETONS[event]["domain"] else cam, st,
                            hit_marks(event, "kadraj", f["type"])))
            fk = (f["type"], f.get("pos_spot"), f.get("mode"), f.get("fg"))
            if fk not in seen_f and f.get("fg"):
                seen_f.add(fk)
                fgs.append((f"{f.get('fg')} ({label})", fx.FG_TEXT.get(f["fg"], f["fg"]), st,
                            hit_marks(event, "on_plan", f.get("fg"))))
    rows["kadraj"] = kad
    rows["on_plan"] = fgs
    # ortam
    env = []
    if event in sv.SCENE_ENVS:
        rot = set(pa.scene_envs(event, sv.env_options(event)))
        env = [("A", "bugünkü görünüm (Setting satırı yok)", "aktif" if "A" in rot else "rotasyon dışı",
                hit_marks(event, "ortam", "A"))]
        env += [(k, v, "aktif" if k in rot else "rotasyon dışı", hit_marks(event, "ortam", k))
                for k, v in sv.SCENE_ENVS[event].items()]
    elif event in es.VOLC_ENV_EVENTS:
        env = [(k, sk.volc_env_text(event, k), f"aktif (ağırlık {w})", "") for k, w in es.VOLC_ENV_WEIGHTS[event].items()]
    elif event == es.FIRE_TORNADO:
        env = [(k, v.get("label", ""), "aktif", "") for k, v in es.FIRE_TOR_ENVS.items()]
    elif event in sk.REGION_VIEW_EVENTS:
        env = [(v, sk.view_district(event, v), "aktif", "") for v in sk.REGION_VIEWS]
    elif event == es.LIBERTY:
        env = [("-", sk.liberty_setting(None) if hasattr(sk, "liberty_setting") else "", "aktif (tek)", "")]
    rows["ortam"] = env
    # açılış
    op = []
    if event in ox.OPENINGS:
        opts = ox.options(event)
        rot = set(pa.openings(event, opts))
        off = ox.DISABLED_OPENINGS.get(event, set())
        op.append(("A", es.EVENT_KEY_VISUAL[event], "aktif" if "A" in rot else "rotasyon dışı",
                   hit_marks(event, "acilis", "A")))
        for k, v in ox.OPENINGS[event].items():
            st = "PASİF" if k in off else ("aktif" if k in rot else "rotasyon dışı (deneme)")
            op.append((k, v, st, hit_marks(event, "acilis", k)))
    else:
        key = es.event_key_visual(event) if event != es.FIRE_TORNADO else None
        op.append(("A", es.EVENT_KEY_VISUAL[event], "aktif (tek açılış)", hit_marks(event, "acilis", "A")))
        if event == es.FIRE_TORNADO:
            op += [(f"ortam {k}", v["key"], "aktif (ortama bağlı)", "") for k, v in es.FIRE_TOR_ENVS.items()]
    rows["acilis"] = op
    # ışık
    lights = []
    base = (list(es.VOLCANO_WEATHER_WEIGHTS[event]) if event in es.VOLC_ENV_EVENTS
            else list(sk.EVENT_SKELETONS[event]["weather"]))
    opts = base + [x for x in sv.LIGHT_ADD.get(event, ()) if x not in base]
    rot = set(pa.lights(event, opts, base))
    lights = [(f"L{i + 1}", li, "aktif" if li in rot else "rotasyon dışı", hit_marks(event, "light", li))
              for i, li in enumerate(opts)]
    rows["isik"] = lights
    # orta / final
    for slot, name in (("slice_2", "orta"), ("slice_3", "final")):
        rows[name] = [(b, v["text"], _status_beat(event, b), hit_marks(event, "beat", b))
                      for b, v in es.EVENT_BEATS[event][slot].items()]
    # insan
    if event == es.FIRE_TORNADO:
        ppl = [(f"{env}/{i + 1}", t, "kod yedeği", "") for env, pool in es.FALLBACK_PEOPLE_FIRE_ENV.items()
               for i, t in enumerate(pool)]
    else:
        off = getattr(es, "DISABLED_PEOPLE_LINES", {}).get(event, set())
        proven = (es.people_axis_proven(event) if hasattr(es, "people_axis_proven") else es.PEOPLE_AXIS_PROVEN)
        ppl = []
        for i, t in enumerate(es.FALLBACK_PEOPLE.get(event, ())):
            pid = es.people_line_id(i, event)
            if event in es.PEOPLE_AXIS_EVENTS:
                st = "PASİF" if pid in off else ("aktif" if pid in proven or event == es.LIBERTY else "DENEME")
                st += " (birebir)" if event in es.VERBATIM_PEOPLE_EVENTS else " (eksen)"
            else:
                st = "kod yedeği (GPT yazar)"
            ppl.append((pid, t, st, ""))
    rows["insan"] = ppl
    # araç
    if es.uses_vehicle(event):
        if event in sk.REGION_VIEW_EVENTS:
            veh = sorted({n for lst in es.REGION_VEHICLES.values() for n, _ in lst})
        else:
            veh = [n for n, _ in es.event_vehicles(event, None)]
        rows["arac"] = [(v, v, "aktif", "") for v in veh]
    else:
        rows["arac"] = [("-", "araçsız olay", "-", "")]
    return rows


def spot_frame_map(event: str) -> list[tuple]:
    es, cp, fx, ox, pa, sv, sk = _m()
    out = []
    spots = list(sk.EVENT_SKELETONS[event]["spots"])
    for s in spots:
        allv = fx.all_frames(event, s, spots)
        rot = pa.allowed_variants(event, s, allv)
        kinds = collections.OrderedDict()
        for f in rot:
            kinds.setdefault(f"{f['type']} @ {f.get('pos_spot') or 'kütüphane'}" + (f" mod {f['mode']}" if f.get('mode') else ""),
                             []).append(f.get("fg") or "-")
        auto = "evet (tek kadraj)" if len(kinds) == 1 else "hayır (kadraj ekseni seçer)"
        out.append((s, "; ".join(f"{k} [ön plan: {', '.join(v)}]" for k, v in kinds.items()), auto))
    return out


def simulate(event: str, n: int = 40) -> list[dict]:
    """40 art arda basış: süreç hafızaları sıfırdan, her basış önceki basışların eksen kaydını görür (sahte Notion)."""
    es, cp, fx, ox, pa, sv, sk = _m()
    ps.reset_memory()
    records, history, out = [], [], []
    domain = sk.EVENT_SKELETONS[event]["domain"]
    for seed in range(1, n + 1):
        random.seed(seed)
        scene = ps.build(event, history=list(history), axes_loader=lambda d: list(records))
        records.append({"combo_key": scene["combo_key"], "eksenler": scene["axes_json"], "status": "test",
                        "date": f"2026-11-11T00:{seed:02d}:00"})
        history.append(scene["combo_key"])
        a = scene["structure"]["axes"] if scene.get("structure") else {}
        t = scene["trace"]
        out.append({"seed": seed, "spot": a.get("spot"), "kadraj": a.get("kadraj"), "on_plan": a.get("on_plan"),
                    "ortam": a.get("ortam") or (a.get("env") if isinstance(a.get("env"), str) else None)
                    or (", ".join(f"{k}={v}" for k, v in a["env"].items()) if isinstance(a.get("env"), dict) else None),
                    "acilis": a.get("acilis") or "A", "beats": a.get("beats"), "insan": a.get("insan"),
                    "arac": a.get("vehicle"), "light": a.get("light"), "view": t.get("view")})
    return out


def pingpong(values: list) -> bool:
    """Değerler sadece iki seçenek arasında sırayla gidip geliyor mu (ABAB...)."""
    v = [x for x in values if x not in (None, "-")]
    if len(set(v)) != 2 or len(v) < 6:
        return False
    return all(a != b for a, b in zip(v, v[1:]))


def _cell(x: str, width: int = 0) -> str:
    x = str(x or "").replace("|", "/").replace("\n", " ")
    return x


def event_md(event: str, sim: bool = True) -> list[str]:
    es = _m()[0]
    rows = axis_rows(event)
    lines = [f"### {event}", ""]
    hits = HITS.get(event, [])
    if hits:
        lines.append("Hit (100K+) eşleşmesi: " + " · ".join(f"{h['share']} ← {h['prod']}"
                                                              + (f" ({h['note']})" if h.get("note") else "")
                                                              for h in hits))
    else:
        lines.append("Hit (100K+) eşleşmesi: yok (Notion Paylaşımlar'da 100K+ kayıt yok)")
    lines.append("")
    names = {"spot": "Spot (kamera noktası)", "kadraj": "Kadraj", "on_plan": "Ön plan", "ortam": "Ortam",
             "acilis": "Açılış (0-4 sn)", "isik": "Işık", "orta": "Orta (4-9 sn)", "final": "Final (9-15 sn)",
             "insan": "İnsan cümlesi", "arac": "Araç"}
    for axis, items in rows.items():
        lines += [f"**{names[axis]}**", "", "| Kimlik | Metin | Durum | Hit |", "|---|---|---|---|"]
        lines += [f"| {_cell(i)} | {_cell(t)} | {_cell(s)} | {_cell(h)} |" for i, t, s, h in items]
        lines.append("")
    lines += ["**Spot → kadraj → ön plan (rotasyon)**", "", "| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |",
              "|---|---|---|"]
    lines += [f"| {_cell(s)} | {_cell(k)} | {a} |" for s, k, a in spot_frame_map(event)]
    lines.append("")
    if sim:
        rows_sim = simulate(event)
        counts = {ax: sum(1 for _, _, st, _ in items if str(st).startswith(("aktif", "DENEME", "kod")))
                  for ax, items in rows.items()}
        seen = {ax: len({r[k] for r in rows_sim if r.get(k)}) for ax, k in
                (("spot", "spot"), ("kadraj", "kadraj"), ("on_plan", "on_plan"), ("ortam", "ortam"),
                 ("acilis", "acilis"), ("insan", "insan"), ("arac", "arac"), ("isik", "light"))}
        b2 = [r["beats"].split("+")[0] for r in rows_sim if r.get("beats")]
        b3 = [r["beats"].split("+")[1] for r in rows_sim if r.get("beats")]
        seen["orta"], seen["final"] = len(set(b2)), len(set(b3))
        series = {"spot": [r["spot"] for r in rows_sim], "kadraj": [r["kadraj"] for r in rows_sim],
                  "on_plan": [r["on_plan"] for r in rows_sim], "ortam": [r["ortam"] for r in rows_sim],
                  "acilis": [r["acilis"] for r in rows_sim], "isik": [r["light"] for r in rows_sim],
                  "orta": b2, "final": b3, "insan": [r["insan"] for r in rows_sim], "arac": [r["arac"] for r in rows_sim]}
        lines += ["**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az;"
                  " ↔ = iki seçenek arasında sırayla gidip geliyor)", "",
                  "| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |", "|---|---|---|---|"]
        for ax in names:
            warn = []
            if seen.get(ax, 0) and seen[ax] < 3 and ax != "arac":
                warn.append("⚠ 3'ten az")
            if pingpong(series.get(ax, [])):
                warn.append("↔ ping-pong")
            if ax == "arac" and not es.uses_vehicle(event):
                warn = ["araçsız"]
            lines.append(f"| {names[ax]} | {counts.get(ax, 0)} | {seen.get(ax, 0)} | {' '.join(warn)} |")
        lines += ["", "**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**", "",
                  "| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows_sim:
            o, f = (r["beats"] or "+").split("+")
            lines.append(f"| {r['seed']} | {_cell(r['spot'])} | {_cell(r['kadraj'])} | {_cell(r['on_plan'] or '-')} | "
                         f"{_cell(r['ortam'] or r.get('view') or '-')} | {r['acilis']} | {o} | {f} | {r['insan'] or 'GPT'} | "
                         f"{_cell(r['arac'] or '-')} |")
        lines.append("")
    return lines


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", default="kilitli")
    ap.add_argument("--md")
    ap.add_argument("--no-sim", action="store_true")
    a = ap.parse_args(argv[1:])
    es = _m()[0]
    events = list(es.LOCKED_EVENTS) if a.events == "kilitli" else [e.strip() for e in a.events.split(";")]
    lines = []
    for e in events:
        lines += event_md(e, sim=not a.no_sim)
    md = "\n".join(lines)
    if a.md:
        with open(a.md, "w", encoding="utf-8", newline="\n") as f:
            f.write(md + "\n")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    logging.disable(logging.WARNING)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
