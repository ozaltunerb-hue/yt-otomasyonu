# Hibrit hikâye istatistiği (16 Eki 2026, Bahadır): data/story_source_log.jsonl'deki her yapılandırılmış üretimden olay
# bazında kod yedeği oranı ve en sık yedek nedenleri. Ağ yok, Kie/GPT/Notion yok; sadece dosya okur.
# Kullanım (proje kökünden): .venv\Scripts\python.exe tools\fallback_report.py [log.jsonl]
#   Varsayılan dosya: STORY_SOURCE_LOG ortam değişkeni, yoksa data/story_source_log.jsonl
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.join(ROOT, "data", "story_source_log.jsonl")


def load(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def _reasons(row: dict) -> list[str]:
    """Son GPT denemesinin eksikleri, parantez içi ayrıntı atılmış ("9-15s: seçilen olayın nesnesi" gibi)."""
    missing = (row.get("attempt_missing") or [[]])[-1] or []
    return [re.sub(r"\s*\(.*?\)", "", m).strip() for m in missing]


def report(rows: list[dict]) -> str:
    by_event = collections.defaultdict(list)
    for r in rows:
        by_event[r.get("event", "?")].append(r)
    lines = [f"Toplam üretim: {len(rows)} · kod yedeği: {sum(r.get('source') == 'fallback' for r in rows)}", ""]
    for event, rs in sorted(by_event.items(), key=lambda kv: -len(kv[1])):
        fb = [r for r in rs if r.get("source") == "fallback"]
        gpt_first = sum(1 for r in rs if r.get("source") == "gpt" and r.get("gpt_attempts") == 1)
        pct = 100 * len(fb) / len(rs)
        lines.append(f"{event}: yedek {len(fb)}/{len(rs)} (%{pct:.0f}) · GPT ilk denemede {gpt_first}/{len(rs)}")
        envs = collections.Counter(r.get("environment") for r in fb if r.get("environment"))
        if envs:
            lines.append("   yedek düşen ortamlar: " + ", ".join(f"{k} {v}" for k, v in envs.most_common(5)))
        reasons = collections.Counter(x for r in fb for x in _reasons(r))
        for reason, n in reasons.most_common(5):
            lines.append(f"   - {reason}: {n}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    path = argv[0] if argv else os.environ.get("STORY_SOURCE_LOG") or DEFAULT
    if not os.path.exists(path):
        print(f"Kayıt dosyası yok: {path} (henüz yapılandırılmış üretim olmamış olabilir)")
        return 1
    print(report(load(path)))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
