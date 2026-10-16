# Hibrit hikâye istatistiği (16 Eki 2026, Bahadır): data/story_source_log.jsonl'deki her yapılandırılmış üretimden olay
# bazında kod yedeği oranı ve en sık yedek nedenleri. Varsayılan: ağ yok, sadece dosya okur. Kie/GPT çağrısı hiç yok;
# --notion seçeneği Notion'u salt okur.
# Kullanım (proje kökünden): .venv\Scripts\python.exe tools\fallback_report.py [log.jsonl]
#   Varsayılan dosya: STORY_SOURCE_LOG ortam değişkeni, yoksa data/story_source_log.jsonl
# 17 Eki: .venv\Scripts\python.exe tools\fallback_report.py --notion  -> Notion "Hikâye kaynağı" alanından (salt okuma;
#   Railway diski geçici olduğu için kalıcı kaynak Notion, jsonl yerelde/kuru denemede kalır)
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


_NOTION_REASON = re.compile(r"deneme \d+:\s*([^|]*)")


def rows_from_notion(pages: list[dict]) -> list[dict]:
    """17 Eki: Notion sayfalarından (Hikâye kaynağı alanı dolu olanlar) jsonl satırı biçiminde kayıtlar. Olay "Olay"
    alanından, yoksa Combo Key'in 3. parçasından. Yedek nedeni alandaki "deneme N: a; b | deneme M: c" metninden."""
    from infrastructure.notion_logger import STORY_SOURCE_PROPERTY
    rows = []
    for page in pages:
        props = page.get("properties", {})

        def text(name):
            return "".join(x.get("plain_text") or x.get("text", {}).get("content", "")
                           for x in props.get(name, {}).get("rich_text", []) or []).strip()
        value = text(STORY_SOURCE_PROPERTY)
        if not value:
            continue
        event = text("Olay") or (text("Combo Key").split("|") + ["", "", "?"])[2]
        fallback = value.lower().startswith("kod yedeği")
        inner = value[value.find("neden:") + 6:value.rfind(")")] if fallback and "neden:" in value else value
        attempts = [[m.strip() for m in part.split(";") if m.strip()] for part in _NOTION_REASON.findall(inner)]
        gpt_n = re.search(r"deneme (\d+)", value)
        rows.append({"event": event, "source": "fallback" if fallback else "gpt",
                     "gpt_attempts": len(attempts) if fallback else int(gpt_n.group(1)) if gpt_n else None,
                     "attempt_missing": attempts, "environment": None})
    return rows


def fetch_notion() -> list[dict]:
    """Notion veritabanının tüm sayfaları (salt okuma, filtresiz: alan yoksa sorgu kırılmaz)."""
    sys.path.insert(0, ROOT)
    from config import settings
    from infrastructure.notion_logger import NOTION_API_URL, _notion_request
    pages, cursor = [], None
    while True:
        body = {"page_size": 100, **({"start_cursor": cursor} if cursor else {})}
        r = _notion_request("POST", f"{NOTION_API_URL}/databases/{settings.NOTION_DB_ID}/query", json=body)
        pages += r.get("results", [])
        if not r.get("has_more"):
            return pages
        cursor = r.get("next_cursor")


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--notion":   # 17 Eki: Notion "Hikâye kaynağı" alanından
        rows = rows_from_notion(fetch_notion())
        if not rows:
            print("Notion'da 'Hikâye kaynağı' dolu kayıt yok (alan yeni; ilk üretimden sonra dolar)")
            return 1
        print(report(rows))
        return 0
    path = argv[0] if argv else os.environ.get("STORY_SOURCE_LOG") or DEFAULT
    if not os.path.exists(path):
        print(f"Kayıt dosyası yok: {path} (henüz yapılandırılmış üretim olmamış olabilir)")
        return 1
    print(report(load(path)))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
