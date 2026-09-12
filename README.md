# 🌊 DeepMyster — YouTube Shorts Otomasyon V3

> Gerçekçi deniz kazaları, fırtınalar, tehlikeli manevralar ve mürettebat mücadelesi videoları üretip YouTube Shorts'a yükleyen tam otonom pipeline.

## 🚨 Kalıcı Kural: Zorunlu İnsan / Mürettebat Varlığı & Rol Çeşitliliği
- Her videoda mutlaka en az bir insan/mürettebat görünür; tamamen insansız video kesinlikle üretilmez.
- İnsanlar olayın aktif parçasıdır (kaptan, zabit, güverte personeli, makine zabiti, marina/liman personeli, yolcu, kurtarma ekibi).
- Yapılan iş/müdahale kriz durumuna doğrudan bağlıdır (acil manevra, halat bağlama, lashing sabitleme, tahliye, arıza tamiri, kurtarma).
- Olay, gemi, lokasyon, rol ve kamera perspektifleri sürekli çeşitlendirilir.

## 📋 Genel Bakış

> Güncel durumun tek doğru kaynağı `BASLANGIC.md`dir — burası sadece yapı/kurulum özetidir, ayrıntı ve gerekçe için `BASLANGIC.md`'ye bakın.

Bu sistem cron aktifken **sıfır insan müdahalesi** ile çalışır. Railway CronJob günde 1 kez tetikler ve şu akışı izler (cron şu an duraklatılmış, bkz. Railway CronJob bölümü):

1. **🧠 Creative Engine** — 12 Denizcilik Alanı + 71 senaryoluk referans kütüphane (tam gemi çeşitliliği: kargo, tanker, kruvaziyer, feribot, Ro-Ro, römorkör, yat/marina)
2. **🤖 GPT-4o** — Gerçekçi, fizik kurallarına uygun, yapılandırılabilir süreli (şu an 15s) tek plan belgesel senaryosu yazar; atanan kamera arketipine (`fixed_cctv`/`bystander_handheld`/`chase_pov`) göre yazılır
3. **✅ Kalite Kapıları** — `validate_silent_visibility` (görünmezlik) + `validate_high_action` (sakin/statik sahne reddi) aynı retry döngüsünde
4. **✂️ Prompt Simplifier** — Senaryoyu Seedance 2 Mini'ye optimize 25-45 kelimelik prompt'a çevirir
5. **🔒 Stil Kilidi** — Seçilen kamera arketipine göre deterministik kamera/PPE/sivil-kıyafet/gerçekçilik son eki eklenir
6. **🛡️ Safety Check** — İçerik güvenliği filtresi (regex + GPT preflight + retry rewrite)
7. **🎬 Seedance 2 Mini (Kie AI)** — Video üretir (`bytedance/seedance-2-fast`, 480p, portrait 9:16)
8. **📺 YouTube Upload** — Shorts olarak **private** yüklenir; kullanıcı manuel inceleyip AI-etiketini işaretledikten sonra elle public yapar
9. **📋 Notion Log** — Tüm süreci ve tekrar-önleme combo key'ini kaydeder (2026-09-12'den beri aktif)

`infrastructure/replicate_merger.py` (çoklu klip birleştirme) kodda mevcuttur ama şu an ULAŞILAMAZ durumda — pipeline her zaman tek sahne ürettiği için hiç çağrılmıyor; gelecekte çoklu klip desteği geri gelirse devreye girer.

## 🏗️ Mimari

```
YT_Otomasyonu/
├── main.py                          # CronJob entry point
├── config.py                        # Fail-fast yapılandırma
├── logger.py                        # Logging
├── core/
│   ├── creative_engine.py           # Yaratıcı senaryo motoru (12 alan, 71 senaryo, 3 kamera arketipi)
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
| **Model** | `bytedance/seedance-2-fast` | Seedance 2 Mini — Full Seedance, Veo 3.1 ve Wan 2.6 ile karşılaştırılıp bilinçli seçildi |
| **Çözünürlük** | `480p` | Kredi tasarruflu — `.env`'deki `DEFAULT_RESOLUTION` |
| **Format** | `portrait (9:16)` | Sabit — YouTube Shorts |
| **Ses** | `Açık` | Sabit — ambient ses, dalga, motor, sirenler |
| **Konuşma** | `Yok` | Sabit — global kitle, dil bariyeri yok |
| **Klip sayısı** | `1` | Sabit — çoklu klip desteği kodda var ama şu an ulaşılamaz |
| **Süre/klip** | `15s` | Dinamik — `.env`'deki `DEFAULT_DURATION`, hardcoded değil |
| **Kamera Sistemi** | 3 arketip | `fixed_cctv` / `bystander_handheld` / `chase_pov`, ağırlıklı rastgele seçim |
| **Sivil/Mürettebat** | Ayrık kurallar | Mürettebat = PPE; yolcu/misafir/sürücü = sivil kıyafet |
| **Upload** | `private` | Manuel inceleme + AI-etiketi sonrası kullanıcı elle public yapar |
| **Kategori** | `24 (Entertainment)` | `.env`'deki `YOUTUBE_CATEGORY_ID` |

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
- **Zamanlama:** ⏸️ Duraklatılmış. Duraklatma sebebi (Notion tekrar-önleme kurulumunun eksik olması) 2026-09-12 itibarıyla ortadan kalktı; cron'un tekrar aktif edilmesi ayrı, henüz alınmamış bir karar. Eski değer: `30 13 * * 1-5` (16:30 TR)
- **Tip:** CronJob (çalışır, iş bitince kapanır)
- **Güncel durum ve gerekçe:** bkz. `_knowledge/deploy-registry.md` (bu dosya infra durumunun kaynağıdır)

## 🛡️ Güvenlik Katmanları

1. **GPT Pre-flight Check** — Riskli prompt'u Kie AI'a göndermeden yakalar
2. **Content Filter Retry** — Reddedilen prompt'u GPT ile yeniden yazar (2x)
3. **Senaryo Retry** — Tüm prompt denemeleri başarısız olursa farklı senaryo seçer (3x)
4. **Prompt Sanitizer** — Tehlikeli kelimeleri otomatik değiştirir

## 📊 Tekrar Önleme

- **Durum: ✅ Aktif (2026-09-12)** — Notion veritabanı kuruldu, `NOTION_ENABLED=True`
- Kullanılan `domain\|vessel\|incident` kombinasyonları Notion DB'de `Combo Key` alanında saklanır
- Her çalışmada son 60 günün geçmişi sorgulanır

## 📝 Notion DB Alanları

| Alan | Tip | Açıklama |
|------|-----|----------|
| Video Adı | Title | YouTube başlığı |
| Durum | Select | Pipeline durumu |
| Model | Select | `bytedance/seedance-2-fast` |
| Tetikleyici | Select | "auto" |
| Konu | Rich Text | Senaryo özeti |
| Prompt | Rich Text | İlk sahne promptu |
| Combo Key | Rich Text | "domain\|vessel\|incident" — tekrar önleme |
| Klip Sayısı | Number | Şu an her zaman 1 |
| Video URL | URL | CDN link |
| YouTube URL | URL | Shorts link |
| Tarih | Date | Üretim tarihi |
| Süre (sn) | Number | Pipeline süresi |
| Hata | Rich Text | Varsa hata mesajı |
| Güvenlik | Rich Text | Safety telemetrisi |
