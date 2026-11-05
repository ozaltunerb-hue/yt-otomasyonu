# Kilitli olayların 40 tohum özeti (6 Kas 2026, Bahadır). Her kayıt prompt_snapshot sonucunun SHA-256'sı (prompt, stil eki,
# eksenler, combo). tests/test_kilit_6kas.py bu dosyayla karşılaştırır.
#
# Kullanım (proje kökünden):
#   .venv\Scripts\python.exe scripts\locked_prompts.py write   -> SADECE Bahadır onaylı kilit değişikliğinde
#   .venv\Scripts\python.exe scripts\locked_prompts.py check   -> çıkış 1 = fark var (commit/push YOK)
import hashlib
import json
import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402

PATH = os.path.join(ROOT, "tests", "fixtures", "locked_prompts_40.json")
SEEDS = tuple(range(1, 41))


def hashes(seeds=SEEDS) -> dict:
    import core.event_structure as es
    snap = ps.snapshot_all(list(es.LOCKED_EVENTS), seeds=seeds)
    return {e: {s: hashlib.sha256(json.dumps(rec, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
                for s, rec in by_seed.items()} for e, by_seed in snap.items()}


def load() -> dict:
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)


def main(argv) -> int:
    mode = argv[1] if len(argv) > 1 else "check"
    now = hashes()
    if mode == "write":
        with open(PATH, "w", encoding="utf-8", newline="\n") as f:
            json.dump(now, f, ensure_ascii=False, indent=0, sort_keys=True)
            f.write("\n")
        print(f"Yazıldı: {len(now)} olay × {len(SEEDS)} tohum")
        return 0
    saved = load()
    changed = {e: [s for s in now[e] if saved.get(e, {}).get(s) != now[e][s]] for e in now}
    changed = {e: s for e, s in changed.items() if s}
    print(f"{len(changed)} kilitli olay değişti")
    for e, s in changed.items():
        print(f"  {e}: {len(s)}/{len(SEEDS)} tohum")
    return 1 if changed or set(saved) != set(now) else 0


if __name__ == "__main__":
    logging.disable(logging.WARNING)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
