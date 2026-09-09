# 🌊 DeepMyster — YouTube Shorts Otomasyon V3

> Gerçekçi deniz kazaları, fırtınalar, tehlikeli manevralar ve mürettebat mücadelesi videoları üretip YouTube Shorts'a yükleyen tam otonom pipeline.

## 🚨 Kalıcı Kural: Zorunlu İnsan / Mürettebat Varlığı & Rol Çeşitliliği
- Her videoda mutlaka en az bir insan/mürettebat görünür; tamamen insansız video kesinlikle üretilmez.
- İnsanlar olayın aktif parçasıdır (kaptan, zabit, güverte personeli, makine zabiti, marina/liman personeli, yolcu, kurtarma ekibi).
- Yapılan iş/müdahale kriz durumuna doğrudan bağlıdır (acil manevra, halat bağlama, lashing sabitleme, tahliye, arıza tamiri, kurtarma).
- Olay, gemi, lokasyon, rol ve kamera perspektifleri sürekli çeşitlendirilir.

## 📋 Genel Bakış

Bu sistem cron aktifken **sıfır insan müdahalesi** ile çalışır. Railway CronJob günde 1 kez tetikler ve şu akışı izler:

1. **🧠 Creative Engine** — 8 Denizcilik Kategorisi + Gemi + İnsanlı Olay + Kamera + Aktif Mürettebat seed havuzu
2. **🤖 GPT-4o** — Gerçekçi, fizik kurallarına uygun 15s tek plan belgesel senaryosu yazar (aktif insan aksiyonu zorunlu)
3. **✂️ Prompt Simplifier** — Senaryoyu Seedance 2.0'a optimize 15-30 kelimelik prompt'a çevirir
4. **🛡️ Safety Check** — İçerik güvenliği filtresi
5. **🎬 Seedance 2.0 (Kie AI)** — Video üretir (15 saniye, portrait 9:16)
6. **🎞️ Replicate Merge** — Çoklu klipleri birleştirir (gerekirse)
7. **📺 YouTube Upload** — Shorts olarak yükler (public)
8. **📋 Notion Log** — Tüm süreci kaydeder

## 🏗️ Mimari

```
YT_Otomasyonu/
├── main.py                          # CronJob entry point
├── config.py                        # Fail-fast yapılandırma
├── logger.py                        # Logging
├── core/
│   ├── creative_engine.py           # Yaratıcı senaryo motoru (8 kategori + aktif mürettebat seedleri)
│   ├── prompt_generator.py          # 3 katmanlı prompt pipeline
│   └── prompt_sanitizer.py          # İçerik güvenliği filtresi
├── infrastructure/
│   ├── kie_client.py                # Seedance 2.0 API (video üretim)
│   ├── replicate_merger.py          # Video birleştirme
│   ├── video_downloader.py          # Video indirme + cleanup
│   ├── youtube_uploader.py          # OAuth2 YouTube upload
│   └── notion_logger.py             # Notion DB tracking + tekrar önleme
├── nixpacks.toml                    # Railway build config
└── requirements.txt                 # Python bağımlılıkları
```

## ⚙️ Sabit Parametreler (V3)

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| **Model** | `seedance-2` | Sabit — sadece Seedance 2.0 |
| **Format** | `portrait (9:16)` | Sabit — YouTube Shorts |
| **Ses** | `Açık` | Sabit — ambient ses, dalga, motor, sirenler |
| **Konuşma** | `Yok` | Sabit — global kitle, dil bariyeri yok |
| **Klip sayısı** | `1` | Sabit — 15s tek kesintisiz dramatik plan |
| **Süre/klip** | `15s` | Sabit |
| **Upload** | `public` | Sabit |
| **Kategori** | `19 (Travel & Events)` | Sabit |

## 🔑 Gerekli Ortam Değişkenleri

```env
# ── AI ──
OPENAI_API_KEY=sk-...
KIE_API_KEY=...

# ── Video Birleştirme ──
REPLICATE_API_TOKEN=...

# ── YouTube OAuth2 ──
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...
YOUTUBE_ENABLED=true

# ── Notion ──
NOTION_SOCIAL_TOKEN=...
NOTION_DB_YOUTUBE_OTOMASYON=...

# ── Sistem ──
# ⚠️ Öğrenci varsayılanı: Geliştirme modunda başlar. Canlıya alırken production yap.
ENV=development
```

## 🚀 Çalıştırma

```bash
# Tam pipeline (CronJob bu komutu çalıştırır)
python main.py

# Test (gerçek üretim yapmadan)
python main.py --dry-run

# Sistem sağlık kontrolü
python main.py --check
```

## 🕐 Railway CronJob

- **Komut:** `python main.py`
- **Zamanlama:** ⏸️ Kaldırıldı (2026-06-06, maliyet kararı). Eski değer: `0 14 * * *` (her gün 14:00 UTC = 17:00 TR)
- **Tip:** CronJob (çalışır, iş bitince kapanır)
- **Yeniden başlatma:** cron schedule alanına eski değeri geri yazmak yeterli

## 🛡️ Güvenlik Katmanları

1. **GPT Pre-flight Check** — Riskli prompt'u Kie AI'a göndermeden yakalar
2. **Content Filter Retry** — Reddedilen prompt'u GPT ile yeniden yazar (2x)
3. **Senaryo Retry** — Tüm prompt denemeleri başarısız olursa farklı senaryo seçer (3x)
4. **Prompt Sanitizer** — Tehlikeli kelimeleri otomatik değiştirir

## 📊 Tekrar Önleme

- Kullanılan `hayvan|yetenek` kombinasyonları Notion DB'de `Combo Key` alanında saklanır
- Her çalışmada son 60 günün geçmişi sorgulanır
- **2686 kombinasyon** — yıllar boyunca tekrarsız içerik garanti

## 📝 Notion DB Alanları

| Alan | Tip | Açıklama |
|------|-----|----------|
| Video Adı | Title | YouTube başlığı |
| Durum | Select | Pipeline durumu |
| Model | Select | seedance-2 |
| Tetikleyici | Select | "auto" |
| Konu | Rich Text | Senaryo özeti |
| Prompt | Rich Text | İlk sahne promptu |
| Combo Key | Rich Text | "animal\|talent" — tekrar önleme |
| Klip Sayısı | Number | 1-3 |
| Video URL | URL | CDN link |
| YouTube URL | URL | Shorts link |
| Tarih | Date | Üretim tarihi |
| Süre (sn) | Number | Pipeline süresi |
| Hata | Rich Text | Varsa hata mesajı |
| Güvenlik | Rich Text | Safety telemetrisi |
