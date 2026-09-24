# run_kie_batch.py sonucundan Notion'a TEST sayfası yazar (her video bir alt bölüm, izleme notu boş).
# Combo Key YOK -> tarihçe/used_combos sorgularına girmez (is_current_universe_combo False).
# Kullanım: python scripts/notion_test_page.py <kie_batch_result.json> "<Sayfa başlığı>" ["<giriş paragrafı>"]
import json, sys, os, io
from datetime import datetime, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from config import settings


def txt(s):
    s = str(s)
    return [{"type": "text", "text": {"content": s[i:i + 1900]}} for i in range(0, len(s), 1900)] or [{"type": "text", "text": {"content": ""}}]


def para(s): return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": txt(s)}}
def h2(s): return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": txt(s)}}
def bullet(s): return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": txt(s)}}
def code(s): return {"object": "block", "type": "code", "code": {"language": "plain text", "rich_text": txt(s)}}


def probe_line(p):
    fmt = p.get("format", {})
    parts = [f"süre {float(fmt.get('duration', 0)):.2f}s", f"boyut {int(fmt.get('size', 0)) / 1e6:.2f} MB"]
    for s in p.get("streams", []):
        if s.get("codec_type") == "video":
            parts.append(f"video {s.get('codec_name')} {s.get('width')}x{s.get('height')} @ {s.get('r_frame_rate')}")
        elif s.get("codec_type") == "audio":
            parts.append(f"ses {s.get('codec_name')} {s.get('sample_rate')}Hz {s.get('channels')}ch")
    return " | ".join(parts)


def build_payload(res: dict, title: str, intro: str = "") -> dict:
    cb, ca = res.get("credit_before"), res.get("credit_after")
    spent = round(cb - ca, 2) if isinstance(cb, (int, float)) and isinstance(ca, (int, float)) else "?"
    children = ([para(intro)] if intro else []) + [
        bullet(f"Model: {res.get('model')} | {settings.DEFAULT_RESOLUTION} | {settings.DEFAULT_DURATION}s | portrait | ses açık"),
        bullet(f"Kie kredi: önce {cb} → sonra {ca} → harcanan {spent}"),
    ]
    for i, v in enumerate(res["videos"], 1):
        children.append(h2(f"{i}) {v.get('domain')} | {v.get('camera')} | {v.get('ship')}"))
        if v.get("error"):
            children.append(bullet(f"HATA: {v['error']}"))
        else:
            pf = v.get("preflight") or {}
            children += [bullet(f"Dosya: {os.path.basename(v['file'])}"), bullet(f"URL: {v['url']}"),
                         bullet(f"ffprobe: {probe_line(v.get('ffprobe', {}))}"),
                         bullet(f"Hareket: {v.get('motion', '-')}"),
                         bullet(f"Üretim süresi: {v.get('seconds')}s"),
                         bullet(f"Preflight: risk {pf.get('risk_score', 0)}, yeniden yazıldı={pf.get('rewritten', False)}")]
        children += [para("Nihai prompt (stil kilidi dahil):"), code(v.get("final_prompt") or ""),
                     para("İzleme notu: (boş — izleyince doldur)")]
    return {
        "parent": {"database_id": settings.NOTION_DB_ID},
        "properties": {
            "Video Adı": {"title": txt(title)},
            "Durum": {"select": {"name": "Video Hazır"}},
            "Model": {"select": {"name": res.get("model") or settings.DEFAULT_MODEL}},
            "Tetikleyici": {"select": {"name": "manual"}},
            "Klip Sayısı": {"number": len(res["videos"])},
            "Tarih": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        },
        "children": children,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    from infrastructure.notion_logger import _notion_request, NOTION_API_URL
    result = json.load(open(sys.argv[1], encoding="utf-8"))
    page = _notion_request("POST", f"{NOTION_API_URL}/pages",
                           json=build_payload(result, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
    print("NOTION:", page.get("url"))
