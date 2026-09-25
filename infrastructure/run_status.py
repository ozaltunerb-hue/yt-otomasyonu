from __future__ import annotations

"""
Canlı çalışma durumu — pipeline her adımda status.json'a yazar, dashboard.html 3 sn'de bir okur.

Sadece CLI (main.main) enable() çağırınca yazar; testler run_pipeline'ı doğrudan çağırdığı için
dosyaya dokunmaz. Yazma hatası pipeline'ı asla durdurmaz (sadece log).
Railway'de çalışan cron'un status.json'u konteynerde kalır; lokalde görünen sadece lokal çalışmalardır.
"""
import json
import logging
import os
import time
from datetime import datetime, timezone

log = logging.getLogger("RunStatus")

# (id, etiket, ağırlık) — ağırlıklar toplamı 100, ilerleme yüzdesi bunlardan hesaplanır
STEPS = [
    ("senaryo", "Senaryo (GPT + kalite kapıları)", 20),
    ("video", "Video üretimi (Seedance)", 50),
    ("indirme", "İndirme + hareket profili", 10),
    ("montaj", "Montaj", 5),
    ("youtube", "YouTube yükleme", 10),
    ("instagram", "Instagram (@deepmyster, elle paylaşılır)", 5),
]
_WEIGHT = {sid: w for sid, _, w in STEPS}
_FINISHED = ("done", "skipped", "manual", "error")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RunStatus:
    def __init__(self):
        self.path: str | None = None
        self.data: dict = {}

    def enable(self, path: str) -> None:
        self.path = path

    def start(self, mode: str, attempt: int = 1, max_attempts: int = 1) -> None:
        """Yeni deneme: tüm adımlar 'pending'. Retry'da çağrılır, deneme sayısı görünür."""
        started = self.data.get("started_at") if attempt > 1 and self.data else _now()
        self.data = {
            "state": "running",
            "mode": mode,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "started_at": started,
            "attempt_started_at": _now(),
            "current_step": None,
            "current_label": "",
            "progress": 0,
            "error": None,
            "title": "",
            "youtube_url": "",
            "steps": [{"id": sid, "label": label, "state": "pending", "started_at": None,
                       "finished_at": None, "note": ""} for sid, label, _ in STEPS],
        }
        self._write()

    def step(self, step_id: str) -> None:
        """step_id'yi 'running' yapar; önceki çalışan adım 'done' olur."""
        self._close_running("done")
        s = self._get(step_id)
        if s is None:
            return
        s.update(state="running", started_at=_now())
        self.data.update(current_step=step_id, current_label=s["label"])
        self._write()

    def skip(self, step_id: str, note: str) -> None:
        self._close_running("done")
        s = self._get(step_id)
        if s is None:
            return
        s.update(state="skipped", finished_at=_now(), note=note)
        self._write()

    def manual(self, step_id: str, note: str) -> None:
        """Pipeline'ın yapmadığı, kullanıcının elle yaptığı adım (ör. Instagram paylaşımı)."""
        self._close_running("done")
        s = self._get(step_id)
        if s is None:
            return
        s.update(state="manual", finished_at=_now(), note=note)
        self._write()

    def step_error(self, step_id: str, message: str) -> None:
        """Adım hata verdi ama çalışma devam ediyor (ör. YouTube upload başarısız)."""
        s = self._get(step_id)
        if s is None:
            return
        s.update(state="error", finished_at=_now(), note=str(message)[:500])
        if self.data.get("current_step") == step_id:
            self.data["current_step"] = None
        self._write()

    def set_title(self, title: str) -> None:
        if self.data:
            self.data["title"] = title
            self._write()

    def fail(self, message: str) -> None:
        """Çalışma hata ile bitti: çalışan adım kırmızı, mesaj kaydedilir."""
        if not self.data:
            return
        self._close_running("error", note=str(message)[:500])
        self.data.update(state="error", error=str(message)[:1000], finished_at=_now(), current_step=None)
        self._write()

    def finish(self, youtube_url: str = "") -> None:
        if not self.data:
            return
        self._close_running("done")
        self.data.update(state="done", progress=100, youtube_url=youtube_url or "",
                         finished_at=_now(), current_step=None)
        self._write()

    # ── iç ──

    def _get(self, step_id: str) -> dict | None:
        for s in self.data.get("steps", []):
            if s["id"] == step_id:
                return s
        return None

    def _close_running(self, state: str, note: str = "") -> None:
        for s in self.data.get("steps", []):
            if s["state"] == "running":
                s.update(state=state, finished_at=_now())
                if note:
                    s["note"] = note

    def _write(self) -> None:
        if not self.path or not self.data:
            return
        self.data["progress"] = max(self.data.get("progress", 0), sum(
            _WEIGHT.get(s["id"], 0) for s in self.data["steps"] if s["state"] in _FINISHED))
        self.data["updated_at"] = _now()
        tmp = f"{self.path}.tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            # Windows'ta dashboard dosyayı o an okuyorsa replace kısa süre reddedilebilir
            for i in range(5):
                try:
                    os.replace(tmp, self.path)
                    return
                except PermissionError:
                    time.sleep(0.1 * (i + 1))
            log.warning("status.json yazılamadı (dosya kilitli)")
        except Exception as e:
            log.warning(f"status.json yazılamadı: {e}")


status = RunStatus()
