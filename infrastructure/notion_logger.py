from __future__ import annotations

"""
Notion Logger V2 — Her video üretimini Notion veritabanına kaydeder.
Adım adım durum güncellemesi, model/maliyet/süre takibi.
Inline database property'leriyle uyumlu.

NOT: Notion DB erişimi hazır olmadığında sessizce log'a yazar, pipeline'ı durdurmaz.
"""
import time
import logging
import requests
from datetime import datetime, timezone
from config import settings
from core.creative_engine import is_current_universe_combo

log = logging.getLogger("NotionLogger")

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Durum değerleri (Notion Select)
STATUS_STARTED = "Başlatıldı"
STATUS_PROMPT_DONE = "Prompt Hazır"
STATUS_VIDEO_GENERATING = "Video Üretiliyor"
STATUS_VIDEO_READY = "Video Hazır"
STATUS_MERGING = "Birleştiriliyor"
STATUS_UPLOADING = "Yükleniyor"
STATUS_COMPLETED = "✅ Tamamlandı"
STATUS_ERROR = "❌ Hata"

# Tarihçe sorguları (2026-09-24). used_combos = "yayınlandı/elde video var" sayımı;
# recent_history = "yazıldı" sayımı, sadece hata kayıtları hariç.
USED_COMBO_STATUSES = [STATUS_COMPLETED, "✅ Tamamlandı (Upload Başarısız)"]
RECENT_HISTORY_EXCLUDE_STATUSES = [STATUS_ERROR]


class NotionTracker:
    """Bir video üretim pipeline'ı boyunca Notion entry'sini yönetir."""

    def __init__(self):
        self.page_id = None
        self.enabled = settings.NOTION_ENABLED
        self._start_time = time.time()

    def create_entry(self, config: dict, trigger: str = "auto") -> str:
        """
        Yeni Notion entry oluşturur (pipeline başlangıcı).

        Args:
            config: Üretim config'i (topic, model, clip_count, vb.)
            trigger: "auto" (cron) veya "manual"
        """
        if not self.enabled:
            log.info("📝 Notion devre dışı — giriş oluşturulmadı")
            return ""

        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN: Notion entry — konu: {config.get('topic', 'N/A')}")
            self.page_id = "dry-run-page-id"
            return self.page_id

        model_name = config.get("model", settings.DEFAULT_MODEL)

        properties = {
            "Video Adı": {"title": [{"text": {"content": config.get("topic", "YouTube Video")[:100]}}]},
            "Durum": {"select": {"name": STATUS_STARTED}},
            "Model": {"select": {"name": model_name}},
            "Tetikleyici": {"select": {"name": trigger}},
            "Konu": {"rich_text": [{"text": {"content": config.get("topic", "")[:2000]}}]},
            "Klip Sayısı": {"number": config.get("clip_count", 1)},
            "Tarih": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }

        # V3: Combo key — tekrar önleme sistemi
        combo_key = config.get("combo_key", "")
        if combo_key:
            properties["Combo Key"] = {"rich_text": [{"text": {"content": combo_key}}]}

        payload = {
            "parent": {"database_id": settings.NOTION_DB_ID},
            "properties": properties,
        }

        try:
            response = _notion_request("POST", f"{NOTION_API_URL}/pages", json=payload)
            self.page_id = response.get("id", "")
            log.info(f"📋 Notion entry oluşturuldu: {self.page_id}")
            return self.page_id
        except Exception as e:
            log.warning(f"⚠️ Notion entry oluşturulamadı: {e}")
            return ""

    def update_status(self, status: str, extra_props: dict = None):
        """Mevcut entry'nin durumunu günceller."""
        if not self.enabled or not self.page_id:
            log.info(f"📝 Durum: {status}")
            return

        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN Notion güncelleme: {status}")
            return

        properties = {"Durum": {"select": {"name": status}}}
        if extra_props:
            properties.update(extra_props)

        try:
            _notion_request("PATCH", f"{NOTION_API_URL}/pages/{self.page_id}", json={"properties": properties})
            log.info(f"📋 Notion durum güncellendi: {status}")
        except Exception as e:
            log.warning(f"⚠️ Notion güncelleme hatası: {e}")

    def update_with_prompts(self, prompt_data: dict):
        """Prompt üretildikten sonra günceller."""
        extra = {}
        title = prompt_data.get("youtube_title", "")
        if title:
            extra["Video Adı"] = {"title": [{"text": {"content": title[:100]}}]}

        # İlk sahne promptunu kaydet
        scenes = prompt_data.get("scenes", [])
        if scenes:
            first_prompt = scenes[0].get("prompt", "")[:2000]
            extra["Prompt"] = {"rich_text": [{"text": {"content": first_prompt}}]}

        # Beat 1 fiil rotasyonu için (TUR 17)
        verb = (prompt_data.get("beat1_action_verb") or "").strip()
        if verb:
            extra["Beat1 Fiil"] = {"rich_text": [{"text": {"content": verb[:100]}}]}

        self.update_status(STATUS_PROMPT_DONE, extra)

    def update_with_video(self, video_url: str):
        """Video URL'sini ekler."""
        extra = {}
        if video_url and video_url.startswith("http"):
            extra["Video URL"] = {"url": video_url}
        self.update_status(STATUS_VIDEO_READY, extra)

    def update_with_motion(self, motion_text: str):
        """Hareket profilini (infrastructure/motion_profile) 'Hareket' alanına yazar; durum değişmez."""
        if not self.enabled or not self.page_id:
            log.info(f"📝 Hareket: {motion_text}")
            return
        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN Notion hareket: {motion_text}")
            return
        extra = {"Hareket": {"rich_text": [{"text": {"content": motion_text[:2000]}}]}}
        try:
            _notion_request("PATCH", f"{NOTION_API_URL}/pages/{self.page_id}", json={"properties": extra})
            log.info(f"📋 Notion hareket profili kaydedildi: {motion_text[:80]}")
        except Exception as e:
            log.warning(f"⚠️ Notion hareket profili hatası: {e}")

    def update_with_youtube(self, youtube_url: str):
        """YouTube URL'sini ekler ve tamamlandı olarak işaretler."""
        elapsed = time.time() - self._start_time
        extra = {"Süre (sn)": {"number": round(elapsed, 1)}}
        if youtube_url and youtube_url.startswith("http"):
            extra["YouTube URL"] = {"url": youtube_url}
        self.update_status(STATUS_COMPLETED, extra)

    def update_with_error(self, error_msg: str):
        """Hata durumunu kaydeder."""
        elapsed = time.time() - self._start_time
        extra = {
            "Hata": {"rich_text": [{"text": {"content": str(error_msg)[:2000]}}]},
            "Süre (sn)": {"number": round(elapsed, 1)},
        }
        self.update_status(STATUS_ERROR, extra)

    def get_used_combos(self, days: int = 60) -> list[str]:
        """
        Son N günde kullanılmış combo_key'leri Notion'dan çeker.
        Tekrar önleme sistemi için kullanılır.

        FAIL-FAST: 3 deneme (2s/4s/8s backoff) sonrası hâlâ başarısızsa
        exception fırlatır. Sebebi: Notion outage anında boş liste dönmek
        creative engine'in son zamanlarda kullanılmış bir combo'yu yeniden
        seçmesine ve duplicate video upload'a yol açar — bir günü atlamak,
        duplicate yüklemekten daha az zararlı.

        Args:
            days: Kaç gün geriye bakılacak

        Sadece USED_COMBO_STATUSES durumundaki ve bugünkü evrene ait combo'lar sayılır.

        Returns:
            list[str]: "domain|ship|event|env|camera" combo_key listesi, kronolojik
            (son eleman en yeni; tüketiciler [-N:] ile en yeniyi alır).

        Raises:
            RuntimeError: Notion API 3 denemede de yanıt vermediyse.
        """
        if not self.enabled or settings.IS_DRY_RUN:
            return []

        from datetime import timedelta

        since = datetime.now(timezone.utc) - timedelta(days=days)
        since_iso = since.isoformat()

        payload = {
            "filter": {
                "and": [
                    {
                        "property": "Tarih",
                        "date": {"on_or_after": since_iso}
                    },
                    {
                        "or": [
                            {"property": "Durum", "select": {"equals": s}}
                            for s in USED_COMBO_STATUSES
                        ]
                    }
                ]
            },
            "sorts": [{"property": "Tarih", "direction": "descending"}],
            "page_size": 100,
        }

        max_attempts = 3
        last_exc = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = _notion_request(
                    "POST",
                    f"{NOTION_API_URL}/databases/{settings.NOTION_DB_ID}/query",
                    json=payload,
                )

                combos = []  # Notion en yeni önce döner
                for page in response.get("results", []):
                    combo_text = _page_combo_key(page)
                    if is_current_universe_combo(combo_text):
                        combos.append(combo_text)

                log.info(f"📋 Notion'dan {len(combos)} kullanılmış combo yüklendi")
                return list(reversed(combos))

            except Exception as e:
                last_exc = e
                if attempt < max_attempts:
                    wait = 2 ** attempt  # 2s, 4s, 8s
                    log.warning(
                        f"⚠️ Notion combo sorgusu başarısız "
                        f"(deneme {attempt}/{max_attempts}): {e} — {wait}s bekleniyor..."
                    )
                    time.sleep(wait)
                else:
                    log.error(
                        f"❌ Notion combo sorgusu {max_attempts} denemede de başarısız: {e} "
                        f"— duplicate riski nedeniyle pipeline durduruluyor."
                    )

        raise RuntimeError(
            f"Notion get_used_combos {max_attempts} denemede de başarısız: {last_exc}"
        )

    def get_recent_history(self, days: int = 30) -> list[str]:
        """
        Son N günün konu ve başlıklarını çeker (GPT'ye negatif yönlendirme olarak vermek için).

        Hata kayıtları ve bugünkü evrene ait olmayan combo'lar (eski kargo/tug/trawler dönemi)
        alınmaz. Dönüş kronolojik: son eleman en yeni (yazıcı [-15:] ile en yeniyi alır).
        """
        if not self.enabled or settings.IS_DRY_RUN:
            return []

        from datetime import timedelta

        since = datetime.now(timezone.utc) - timedelta(days=days)
        since_iso = since.isoformat()

        payload = {
            "filter": {
                "and": [
                    {
                        "property": "Tarih",
                        "date": {"on_or_after": since_iso}
                    },
                    *[
                        {"property": "Durum", "select": {"does_not_equal": s}}
                        for s in RECENT_HISTORY_EXCLUDE_STATUSES
                    ],
                ]
            },
            "sorts": [{"property": "Tarih", "direction": "descending"}],
            "page_size": 100,
        }

        try:
            response = _notion_request(
                "POST",
                f"{NOTION_API_URL}/databases/{settings.NOTION_DB_ID}/query",
                json=payload,
            )
            history = []  # en yeni önce toplanır, sonda kronolojiğe çevrilir
            for page in response.get("results", []):
                if not is_current_universe_combo(_page_combo_key(page)):
                    continue
                props = page.get("properties", {})
                # Konu
                topic_rt = props.get("Konu", {}).get("rich_text", [])
                if topic_rt:
                    t = topic_rt[0].get("text", {}).get("content", "")
                    if t and t not in history:
                        history.append(t)
                # Video Adı
                title_rt = props.get("Video Adı", {}).get("title", [])
                if title_rt:
                    t = title_rt[0].get("text", {}).get("content", "")
                    if t and t not in history:
                        history.append(t)
            return list(reversed(history[:20]))
        except Exception as e:
            log.warning(f"⚠️ Notion get_recent_history hatası (ihmal edilebilir): {e}")
            return []

    def get_recent_beat1_verbs(self, limit: int = 10) -> list[str]:
        """Son `limit` hata-olmayan kaydın Beat 1 fiilleri (en yeni önce). Yazıcıya "farklı fiil seç"
        ipucu olarak gider (TUR 17). Hata olursa boş liste: ipucu, kapı değil."""
        if not self.enabled or settings.IS_DRY_RUN:
            return []
        payload = {
            "filter": {"and": [
                {"property": "Beat1 Fiil", "rich_text": {"is_not_empty": True}},
                *[{"property": "Durum", "select": {"does_not_equal": s}} for s in RECENT_HISTORY_EXCLUDE_STATUSES],
            ]},
            "sorts": [{"property": "Tarih", "direction": "descending"}],
            "page_size": limit,
        }
        try:
            response = _notion_request("POST", f"{NOTION_API_URL}/databases/{settings.NOTION_DB_ID}/query", json=payload)
            verbs = []
            for page in response.get("results", []):
                rt = page.get("properties", {}).get("Beat1 Fiil", {}).get("rich_text", [])
                v = "".join(x.get("plain_text") or x.get("text", {}).get("content", "") for x in rt).strip().lower()
                if v:
                    verbs.append(v)
            return verbs
        except Exception as e:
            log.warning(f"⚠️ Notion Beat1 fiil geçmişi okunamadı (ipucu atlanır): {e}")
            return []

    def update_with_safety_info(self, safety_data: dict):
        """
        İçerik güvenliği telemetrisi — pre-flight, retry ve fallback bilgilerini kaydeder.

        Args:
            safety_data: {
                "preflight_risk_score": 1-10,
                "preflight_rewritten": True/False,
                "content_retries": 0-3,
                "model_fallback_used": True/False,
                "rejection_reasons": ["reason1", ...],
                "original_prompt": "...",
                "final_prompt": "...",
            }
        """
        if not self.enabled or not self.page_id:
            return

        if settings.IS_DRY_RUN:
            log.info(f"🧪 DRY-RUN Notion güvenlik telemetrisi: {safety_data}")
            return

        # Güvenlik bilgilerini tek bir metin alanında birleştir
        parts = []
        risk_score = safety_data.get("preflight_risk_score", 0)
        if risk_score > 0:
            parts.append(f"Pre-flight Risk: {risk_score}/10")
        if safety_data.get("preflight_rewritten"):
            parts.append("Pre-flight: GPT Rewrite uygulandı")
        retries = safety_data.get("content_retries", 0)
        if retries > 0:
            parts.append(f"Content Filter Retry: {retries}x")
        if safety_data.get("model_fallback_used"):
            parts.append("Model Fallback kullanıldı")
        reasons = safety_data.get("rejection_reasons", [])
        if reasons:
            parts.append(f"Ret sebepleri: {', '.join(reasons[:3])}")

        if not parts:
            return  # Güvenlik olayı yok — güncelleme gerek yok

        safety_text = " | ".join(parts)

        extra = {
            "Güvenlik": {"rich_text": [{"text": {"content": safety_text[:2000]}}]},
        }

        try:
            _notion_request("PATCH", f"{NOTION_API_URL}/pages/{self.page_id}", json={"properties": extra})
            log.info(f"📋 Notion güvenlik telemetrisi kaydedildi: {safety_text[:80]}")
        except Exception as e:
            log.warning(f"⚠️ Notion güvenlik telemetrisi hatası: {e}")


def _page_combo_key(page: dict) -> str:
    """Notion sayfasından Combo Key metnini çıkarır; yoksa boş string."""
    combo_rt = page.get("properties", {}).get("Combo Key", {}).get("rich_text", [])
    return combo_rt[0].get("text", {}).get("content", "") if combo_rt else ""


def _notion_request(method: str, url: str, **kwargs) -> dict:
    """Notion API'ye istek gönderir — geçici ağ hataları + 429/5xx için retry mekanizmalı."""
    headers = {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    _TRANSIENT_KEYWORDS = ("eof", "ssl", "broken pipe", "connection reset", "timeout", "connection aborted")
    _TRANSIENT_STATUS = {429, 500, 502, 503, 504}
    max_retries = 3
    last_status_err = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(method, url, headers=headers, timeout=15, **kwargs)
        except requests.RequestException as e:
            err_lower = str(e).lower()
            if attempt < max_retries and any(kw in err_lower for kw in _TRANSIENT_KEYWORDS):
                wait = 2 ** attempt
                log.warning(f"⚠️ Notion geçici ağ hatası (deneme {attempt}/{max_retries}): {e} — {wait}s bekliyor...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"Notion API bağlantı hatası: {e}")

        if response.status_code in _TRANSIENT_STATUS:
            last_status_err = f"{response.status_code} — {response.text[:200]}"
            if attempt < max_retries:
                wait = 2 ** attempt
                log.warning(
                    f"⚠️ Notion geçici sunucu hatası (deneme {attempt}/{max_retries}): "
                    f"HTTP {response.status_code} — {wait}s bekliyor..."
                )
                time.sleep(wait)
                continue
            raise RuntimeError(f"Notion API hatası: {last_status_err}")

        if response.status_code not in (200, 201):
            raise RuntimeError(f"Notion API hatası: {response.status_code} — {response.text[:200]}")

        return response.json()

    raise RuntimeError(f"Notion API {max_retries} denemede de başarısız ({last_status_err or 'bilinmeyen sebep'})")
