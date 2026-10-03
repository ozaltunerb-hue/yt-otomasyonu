"""
YouTube Otomasyonu V3 — Fail-Fast Config
"DeepMyster" Tam Otonom Pipeline.
Tüm gerekli env variable'ları boot time'da doğrular.
Telegram botu (bot.py) ile tetiklenir; cron yok.
"""
import os
import sys
import logging
import shutil
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()


VIDEO_DURATION_SECONDS = 15
VIDEO_RESOLUTIONS = ("480p", "720p")   # seedance-2-fast'in desteklediği çözünürlükler


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
        # A/B test: DEFAULT_MODEL değeri "seedance-2-mini" (varsayılan), "seedance-2"
        # veya "veo-3.1" olabilir — bkz. infrastructure/kie_client.py MODEL_CONFIG.
        self.DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "bytedance/seedance-2-fast")  # Seedance 2 Mini
        self.DEFAULT_ORIENTATION = "portrait"    # Sabit — Shorts (9:16)
        self.DEFAULT_AUDIO = True               # Sabit — ses her zaman açık (deniz/dalga/fırtına sesleri)
        self.DEFAULT_DURATION = int(os.environ.get("DEFAULT_DURATION", "15"))  # 15 saniye (senaryoya göre sabit)
        # 3 Eki, Bahadır: 15 saniyenin altında video yok (kesin kural). Seedance üst sınırı da 15 sn: tam 15.
        if self.DEFAULT_DURATION != VIDEO_DURATION_SECONDS:
            raise EnvironmentError(f"DEFAULT_DURATION {self.DEFAULT_DURATION} sn; video süresi {VIDEO_DURATION_SECONDS} "
                                   f"sn olmalı (15 sn altı video yok).")
        # Çözünürlüğü değiştirmek için TEK yer burası (kodun geri kalanı settings.DEFAULT_RESOLUTION okur).
        # Kie seedance-2-fast, 15 sn: 480p = 175,5 kredi (11,7/sn), 720p = 372 kredi (24,8/sn). Env değişkeni yok.
        self.DEFAULT_RESOLUTION = "480p"
        if self.DEFAULT_RESOLUTION not in VIDEO_RESOLUTIONS:
            raise EnvironmentError(f"DEFAULT_RESOLUTION {self.DEFAULT_RESOLUTION!r}; izinli: {VIDEO_RESOLUTIONS}")

        # ── YouTube Upload ──
        self.YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")
        self.YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
        self.YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
        self.YOUTUBE_CATEGORY_ID = os.environ.get("YOUTUBE_CATEGORY_ID", "24")  # Entertainment / Documentary
        self.YOUTUBE_PRIVACY = os.environ.get("YOUTUBE_PRIVACY", "private")
        self.YOUTUBE_ENABLED = os.environ.get("YOUTUBE_ENABLED", "true").lower() == "true"
        # Yayın kilidi (TUR 29): kullanıcı açıkça onaylayana kadar hiçbir yoldan (Telegram /yayin, CLI)
        # YouTube'a yükleme yapılmaz. Açmak bilinçli bir kod değişikliği + push ister, ortam değişkeniyle açılmaz.
        self.PUBLISH_LOCKED = True

        # Prompt hattı: "creative" (TUR 31, varsayılan) = GPT-4o hikâyeyi kısa sistem prompt'uyla kendisi yazar;
        # "skeleton" (TUR 30) = olay başına kilitli iskelet + gpt-4o-mini boşluk doldurma; "legacy" = eski yol
        # (yazıcı sistem prompt'u, 5 aday, skor, simplifier, A-N kapıları, fikir kütüphanesi). Final test geçene
        # kadar hiçbiri silinmez, bu anahtarla geri açılır.
        self.PROMPT_PIPELINE = os.environ.get("PROMPT_PIPELINE", "creative").strip().lower()

        # Kalıcı video arşivi (TUR 29): video.mp4 + meta.json. Railway diski geçicidir; kalıcı kopya
        # Telegram file_id'dir (Notion "Telegram File ID").
        self.ARCHIVE_DIR = os.environ.get(
            "ARCHIVE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "arsiv"))

        # ── Notion ──
        self.NOTION_TOKEN = os.environ.get(
            "NOTION_SOCIAL_TOKEN",
            os.environ.get("NOTION_API_TOKEN", "")
        )
        self.NOTION_DB_ID = os.environ.get("NOTION_DB_YOUTUBE_OTOMASYON", "")
        self.NOTION_ENABLED = bool(self.NOTION_TOKEN and self.NOTION_DB_ID)
        # 4 Eki, Bahadır: üretimde Notion zorunlu (geçmiş/tekrar önleme olmadan üretim yok). Sadece DRY_RUN'da kapalı
        # olabilir.
        if not self.NOTION_ENABLED and not self.IS_DRY_RUN:
            raise EnvironmentError("Notion kapalı (NOTION_SOCIAL_TOKEN/NOTION_API_TOKEN ve NOTION_DB_YOUTUBE_OTOMASYON "
                                   "gerekli); üretim Notion olmadan çalışmaz. Deneme için DRY_RUN=1.")

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
