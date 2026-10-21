# Caption simülasyonu (21 Eki 2026, Aşama 7). GPT/Kie/Notion yok: sahte GPT adayları + şablon yedeği.
#
# Her yapılandırılmış olay için art arda N caption: geçmiş = Paylaşımlar fixture'ı (tests/fixtures/paylasimlar_snapshot.json)
# + bu simülasyonda üretilen caption'lar (üretimdeki gibi son 20). Sahte GPT her turda 3 başlık (farklı stiller), 2 açıklama
# ve bir CTA verir; ifadeler olaya göre değişen bir bankadan rastgele seçilir (gerçek GPT'nin çeşitliliğine yakın olsun).
# Çıktı: olay başına 2 örnek blok, stil/CTA dağılımı, reddedilen aday oranı, şablona düşme oranı.
#
# Kullanım: .venv\Scripts\python.exe scripts\caption_sim.py [--runs 10] [--seed 11] [--md yol]
import collections
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "paylasimlar_snapshot.json")
VERBS = ("Rolls Into", "Overruns", "Breaks Over", "Pours Across", "Batters", "Rips Through", "Buries", "Hammers",
         "Floods Into", "Crashes Onto", "Charges Down", "Tears Into")
HOOKS = ("Nobody Expected This Part", "Look at the Left Side", "Wait for the Last Second", "Watch the Car on the Right",
         "This Is How Fast It Moves", "It Did Not Slow Down")
WITNESS = ("From a Rooftop", "From an Upper Window", "From a Hillside", "From the Third Floor",
           "From a Street Camera")   # gerçek GPT'ye "en fazla 9 kelime" denir; sahte adaylar da kısa
NUMBERS = ("Fifteen Seconds", "Ten Seconds", "Three Floors", "Four Cars", "Six Houses", "Two Streets")


def mock_candidates(event: str, rng: random.Random, avoid_styles: list[str] = ()) -> dict:
    """Sahte GPT: gerçek GPT'ye söylendiği gibi son 2 stilden kaçınır (kalan 4 stilden 3'ü); 6 stilin hepsi üretilebilir."""
    import core.caption as cap
    threat, target, emoji, escalation = cap.VARS[event]
    pool = [s for s in cap.STYLES if s not in set(avoid_styles)] or list(cap.STYLES)
    styles = rng.sample(pool, min(3, len(pool)))
    make = {
        "T1": lambda: f"{rng.choice(HOOKS)} {emoji}",
        "T2": lambda: f"The Second the {threat} {rng.choice(('Arrived', 'Hit', 'Broke Through', 'Turned'))}",
        "T3": lambda: f"{rng.choice(NUMBERS)} of {threat}",
        "T4": lambda: f"{rng.choice(('Could You Outrun', 'Would Anyone Survive', 'How Close Is Too Close to'))} the {threat}?",
        "T5": lambda: f"Filmed {rng.choice(WITNESS)} as the {threat} Hit",
        "T6": lambda: f"{threat} {rng.choice(VERBS)} {target} {emoji}",
    }
    descs = [f"It starts at the edge of {target.lower()}. A few moments later the result is {escalation}.",
             f"It {rng.choice(('builds', 'grows', 'speeds up'))} with every second. The last frame: {escalation}.",
             f"One calm scene, then the {threat.lower()}: {escalation}, all in a single take."]
    cta_type = rng.choice(list(cap.CTA_TYPES))
    cta = {"question": "Where would you have gone first?", "watch": "Stay until the last frame.",
           "emoji": f"Comment {emoji} or 🏃", "stat": "Fifteen seconds, one take.", "none": ""}[cta_type]
    return {"titles": [(make[s](), s) for s in styles], "descriptions": rng.sample(descs, 2), "cta": cta,
            "cta_type": cta_type}


def reason_kind(neden: str) -> str:
    if neden.startswith("benzer"):
        return "Jaccard"
    if neden.startswith("ilk 3"):
        return "ilk 3 kelime"
    if neden.startswith("yasak"):
        return "kalıcı yasak"
    if neden.startswith("son başlıklarda"):
        return "dinamik yasak"
    return "biçim"


def simulate(runs: int = 10, seed: int = 11) -> dict:
    import core.caption as cap
    rows = json.load(open(FIXTURE, encoding="utf-8"))["rows"]
    rng = random.Random(seed)
    out = {}
    for event in cap.SHARE_CATEGORY:
        generated, results = [], []
        for i in range(runs):
            ctx = cap.build_context(rows, generated)
            info = {"opening": "", "people": rng.choice((None, 3, 4, 5)), "kadraj": rng.choice(list(cap.WITNESS))}
            cands = mock_candidates(event, rng, ctx["recent_styles"][-2:])
            c = cap.choose(event, info, cands, ctx, rng)
            gpt_rej = [r for r in c["rejected"] if r["kaynak"] == "GPT" and r["alan"] == "başlık"]
            results.append({**c, "gpt_titles": len(cands["titles"]), "gpt_title_rejected": len(gpt_rej),
                            "reasons": [reason_kind(r["neden"]) for r in gpt_rej],
                            "cand_styles": [s for _, s in cands["titles"]]})
            generated.append({**cap.meta(c), "date": f"2026-11-{i + 1:02d}"})
        out[event] = results
    return out


def to_markdown(res: dict) -> str:
    import core.caption as cap
    total_c = sum(r["gpt_titles"] for rows in res.values() for r in rows)
    total_r = sum(r["gpt_title_rejected"] for rows in res.values() for r in rows)
    n = sum(len(rows) for rows in res.values())
    tpl = sum(1 for rows in res.values() for r in rows if r["title_source"] != "GPT")
    forced = sum(1 for rows in res.values() for r in rows if "zorunlu" in r["title_source"])
    lines = ["# Caption simülasyonu — 21 Ekim 2026 (Aşama 7)", "",
             "Sahte GPT adayları + şablon yedeği; geçmiş = Paylaşımlar (49 satır) + simülasyonda üretilenler. Olay başına "
             f"{len(next(iter(res.values())))} ardışık caption.", "",
             f"- Reddedilen GPT başlık adayı: {total_r}/{total_c} (%{100 * total_r / max(total_c, 1):.0f})",
             f"- Şablona düşen başlık: {tpl}/{n} (%{100 * tpl / max(n, 1):.0f}); zorunlu şablon (hiçbiri geçmedi): {forced}",
             "- Ret nedenleri (GPT başlık adayı): " + ", ".join(
                 f"{k} {v}" for k, v in collections.Counter(x for rows in res.values() for r in rows
                                                              for x in r["reasons"]).most_common()),
             "- Sahte GPT aday stilleri (6 stilin hepsi): " + ", ".join(
                 f"{k} {v}" for k, v in sorted(collections.Counter(s for rows in res.values() for r in rows
                                                                   for s in r["cand_styles"]).items())),
             ""]
    for event, rows in res.items():
        st = collections.Counter(r["style"] for r in rows)
        ct = collections.Counter(cap.CTA_TYPES[r["cta_type"]] for r in rows)
        lines += [f"## {event}", "", "stil: " + ", ".join(f"{k} {v}" for k, v in sorted(st.items())),
                  "· CTA: " + ", ".join(f"{k} {v}" for k, v in ct.most_common()), ""]
        for r in rows[:2]:
            lines += ["```", cap.block(r), "```", cap.info_line(r), ""]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    runs = int(argv[argv.index("--runs") + 1]) if "--runs" in argv else 10
    seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 11
    md = to_markdown(simulate(runs, seed))
    print(md)
    if "--md" in argv:
        with open(argv[argv.index("--md") + 1], "w", encoding="utf-8", newline="\n") as f:
            f.write(md + "\n")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
