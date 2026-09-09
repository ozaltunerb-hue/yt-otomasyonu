"""
YouTube Otomasyonu V3 — Fail-Fast Config
"Pets Got Talent" Tam Otonom Pipeline.
Tüm gerekli env variable'ları boot time'da doğrular.
Telegram kaldırıldı — CronJob ile çalışır.
"""
import os
import sys
import logging
import shutil
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()


class Config:
    def __init__(self):
        self.ENV = os.environ.get("ENV", "production").lower()
        self.IS_DRY_RUN = self.ENV == "development" or os.environ.get("DRY_RUN", "0") == "1"

        # ── AI Servisleri ──
        self.OPENAI_API_KEY = self._require_env(
            "OPENAI_API_KEY",
            default="sk-test-placeholder" if self.IS_DRY_RUN else None
        )

        # ── Video Üretimi (Kie AI — Seedance 2.0 / Seedance 2 Mini) ──
        self.KIE_API_KEY = self._require_env(
            "KIE_API_KEY",
            default="test-kie-key" if self.IS_DRY_RUN else None
        )
        self.KIE_BASE_URL = os.environ.get("KIE_BASE_URL", "https://api.kie.ai/api/v1")

        # ── Video Birleştirme (Replicate — Çoklu Klip Durumunda) ──
        self.REPLICATE_API_TOKEN = os.environ.get(
            "REPLICATE_API_TOKEN",
            "test-replicate-token" if self.IS_DRY_RUN else ""
        )
        self.REPLICATE_MERGE_VERSION = os.environ.get(
            "REPLICATE_MERGE_VERSION",
            "14273448a57117b5d424410e2e79700ecde6cc7d60bf522a769b9c7cf989eba7"
        )

        # ── Sabit Üretim Parametreleri (DeepMyster — Seedance 2 Mini) ──
        self.DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "bytedance/seedance-2-fast")  # Seedance 2 Mini
        self.DEFAULT_ORIENTATION = "portrait"    # Sabit — Shorts (9:16)
        self.DEFAULT_AUDIO = True               # Sabit — ses her zaman açık (deniz/dalga/fırtına sesleri)
        self.DEFAULT_DURATION = 15              # Sabit — 15 saniye Shorts
        self.DEFAULT_RESOLUTION = os.environ.get("DEFAULT_RESOLUTION", "480p")  # Kredi tasarruflu 480p

        # ── YouTube Upload ──
        self.YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")
        self.YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
        self.YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
        self.YOUTUBE_CATEGORY_ID = os.environ.get("YOUTUBE_CATEGORY_ID", "24")  # Entertainment / Documentary
        self.YOUTUBE_PRIVACY = os.environ.get("YOUTUBE_PRIVACY", "private")
        self.YOUTUBE_ENABLED = os.environ.get("YOUTUBE_ENABLED", "true").lower() == "true"

        # ── Notion ──
        self.NOTION_TOKEN = os.environ.get(
            "NOTION_SOCIAL_TOKEN",
            os.environ.get("NOTION_API_TOKEN", "")
        )
        self.NOTION_DB_ID = os.environ.get("NOTION_DB_YOUTUBE_OTOMASYON", "")
        self.NOTION_ENABLED = bool(self.NOTION_TOKEN and self.NOTION_DB_ID)

        # ── Polling Ayarları (Kie AI video üretimi) ──
        self.POLL_INITIAL_WAIT = int(os.environ.get("POLL_INITIAL_WAIT", "60"))
        self.POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "15"))
        self.POLL_MAX_ATTEMPTS = int(os.environ.get("POLL_MAX_ATTEMPTS", "40"))

        # ── Sistem Bağımlılıkları (Opsiyonel — FFmpeg sadece fallback) ──
        self.FFMPEG_AVAILABLE = bool(shutil.which("ffmpeg"))
        if not self.FFMPEG_AVAILABLE and not self.IS_DRY_RUN:
            logging.getLogger("Config").warning(
                "⚠️ FFmpeg bulunamadı — video birleştirme sadece Replicate ile yapılacak."
            )

    def _require_env(self, key, default=None):
        """Gerekli env variable'ı al, yoksa çök."""
        val = os.environ.get(key, default)
        if not val:
            raise EnvironmentError(
                f"CRITICAL STARTUP FAILURE: Gerekli ortam değişkeni '{key}' bulunamadı!"
            )
        return val


# Boot time'da config'i oluştur — eksik var ise hemen çök
try:
    settings = Config()
except EnvironmentError as e:
    logging.critical(f"BOOT ERROR: {e}", exc_info=True)
    sys.exit(1)
