"""
Eksen geçmişi (21 Eki 2026, Gece 1 / Aşama 3): kalıcı tekrar önleme hafızası.

Sorun: çığ/deprem/ateş hortumu/volkan ortam hafızası süreç belleğindeydi (her deploy'da sıfırlanıyordu); ışık, araç ve
kişi sayısında tekrar önleme yoktu; iptal edilen üretimler geçmişe girmiyordu.

Çözüm: her üretim, seçim yapıldığı anda (Onay mesajından önce) Notion "Eksenler" alanına tek satır JSON yazar
(`axes_json`). Bir sonraki üretim seçimden önce aynı kategorinin son kayıtlarını (iptaller dahil, durum filtresi yok)
okur ve geçmişi buradan kurar. "Eksenler" alanı olmayan eski kayıtlarda geçmiş eski alanlardan ayrıştırılır
(`parse_record`): Combo Key (spot, bölge görünümü, beat çifti), "Ortam" select (volkan ortamı), Prompt'taki Setting
satırı (çığ / deprem ortamı), spot (ateş hortumu ortamı). Ayrıştırılamayan eksen o kayıt için boş (None).

Bu modül ağa çıkmaz: Notion okuma `infrastructure.notion_logger.NotionTracker.get_axes_records`'ta, kayıtlar buraya ham
sözlük olarak gelir ({"combo_key", "eksenler", "ortam", "prompt", "status", "date"}).
"""
from __future__ import annotations

import json
import re

import core.event_structure as es
from core.skeleton_pipeline import EVENT_SKELETONS, REGION_VIEWS, VOLC_ENVS

AXES_VERSION = 1
AXES_PROPERTY = "Eksenler"
HISTORY_LIMIT = 10   # olay başına okunan son kayıt (görev: "o olayın son 10 kaydı")
# Eksen anahtarları (genişletilebilir: yeni eksen eklenince JSON'a yeni anahtar girer, eski kayıtta None sayılır)
AXIS_KEYS = ("spot", "view", "env", "light", "vehicle", "people", "key", "beats",
             "kadraj", "on_plan", "kamera_modu", "kamera_noktasi",
             "ortam",   # 21 Eki (Aşama 5): 9 olayın ortam ekseni (A-E); eski kayıtta boş
             "acilis")  # 21 Eki (Aşama 6): açılış ekseni (A-D); eski kayıtta boş   # 21 Eki (Aşama 4): kadraj ekseni; eski kayıtta boş

_EVENTS_LOWER = {e.lower(): e for e in EVENT_SKELETONS}
_VOLC_LABEL = {v["label"]: k for k, v in VOLC_ENVS.items()}
_EQ_DARK_REVERSE = {dark: plain for plain, dark in es.EQ_DARK_CITY.items()}


def axes_json(event: str, axes: dict, excluded: dict | None = None) -> str:
    """Notion "Eksenler" alanına giden tek satır JSON."""
    return json.dumps({"v": AXES_VERSION, "event": event, "axes": {k: axes.get(k) for k in axes},
                       "excluded": excluded or {}}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _canonical_spot(event: str, spot_lower: str) -> str | None:
    for sp in EVENT_SKELETONS.get(event, {}).get("spots", {}):
        if sp.lower() == spot_lower:
            return sp
    return None


def _setting_line(prompt: str) -> str:
    m = re.search(r"Setting: ([^.]*)\.", prompt or "")
    return m.group(1) if m else ""


def _longest_in(values, text: str) -> str | None:
    hits = [v for v in values if v in text]
    return max(hits, key=len) if hits else None


def parse_setting_env(event: str, prompt: str) -> dict | None:
    """Çığ / deprem: Prompt'taki "Setting: ..." satırından ortam (değerler sabit listeden). Bulunamazsa None."""
    line = _setting_line(prompt)
    if not line:
        return None
    if event in es.EARTHQUAKE_EVENTS:
        city = _longest_in(list(es.EQ_ENV_AXES["city"]) + list(_EQ_DARK_REVERSE), line)
        city = _EQ_DARK_REVERSE.get(city, city)
        env = {"city": city, "street": _longest_in(es.EQ_ENV_AXES["street"], line),
               "light": _longest_in(es.EQ_ENV_AXES["light"], line)}
    elif event in es.AVALANCHE_EVENTS:
        env = {a: _longest_in(es.ENV_AXES[a], line) for a in ("mountain", "village", "light")}
    else:
        return None
    return env if all(env.values()) else None


def parse_record(rec: dict) -> dict | None:
    """Ham Notion kaydı -> {"event", "axes": {...}, "source": "eksenler" | "eski"}; olay bilinmiyorsa None."""
    raw = (rec.get("eksenler") or "").strip()
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("event") in EVENT_SKELETONS and isinstance(data.get("axes"), dict):
                return {"event": data["event"], "axes": {k: data["axes"].get(k) for k in AXIS_KEYS},
                        "source": "eksenler"}
        except ValueError:
            pass   # bozuk JSON: eski yoldan dene
    parts = (rec.get("combo_key") or "").split("|")
    if len(parts) != 5:
        return None
    event = _EVENTS_LOWER.get(parts[2].strip().lower())
    if not event:
        return None
    place = parts[3].split("#")
    axes = dict.fromkeys(AXIS_KEYS)
    axes["spot"] = _canonical_spot(event, place[0].strip().lower())
    if len(place) > 1 and place[1].strip().lower() in REGION_VIEWS:
        axes["view"] = place[1].strip().lower()
    if len(place) > 2 and re.fullmatch(r"[A-Z]\d+\+[A-Z]\d+", place[2].strip().upper()):
        axes["beats"] = place[2].strip().upper()
    if event in es.VOLC_ENV_EVENTS:
        axes["env"] = _VOLC_LABEL.get((rec.get("ortam") or "").strip())
    elif event == es.FIRE_TORNADO and axes["spot"]:
        try:
            axes["env"] = es.fire_env_of_spot(axes["spot"])
        except es.StructureError:
            axes["env"] = None   # 16 Eki öncesi spot (ortamı yok)
    elif event in es.ENV_EVENTS:
        env = parse_setting_env(event, rec.get("prompt") or "")
        axes["env"] = env
        axes["light"] = env["light"] if env else None
    if event == es.FIRE_TORNADO and axes["env"]:
        axes["key"] = axes["env"]
    return {"event": event, "axes": axes, "source": "eski"}


def build_history(records: list[dict]) -> list[dict]:
    """Ham kayıtlar (eskiden yeniye) -> ayrıştırılmış kayıtlar (ayrıştırılamayanlar atılır)."""
    return [p for p in (parse_record(r) for r in records) if p]


def event_history(parsed: list[dict], event: str, limit: int = HISTORY_LIMIT) -> list[dict]:
    """Olayın son `limit` kaydının eksenleri (eskiden yeniye)."""
    return [p["axes"] for p in parsed if p["event"] == event][-limit:]


def category_history(parsed: list[dict], events, limit: int = HISTORY_LIMIT) -> list[dict]:
    """Kategori geçmişi (çığ ve deprem ortamı + spotu kategori bazında: 14 Eki kararı, köy/kayak/orman ortak)."""
    events = set(events)
    return [p["axes"] for p in parsed if p["event"] in events][-limit:]


def values(hist: list[dict], axis: str) -> list:
    return [h.get(axis) for h in hist if h.get(axis) not in (None, "")]
