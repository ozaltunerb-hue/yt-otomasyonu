# 🌊 DeepMyster — YouTube Shorts Otomasyon V3

> Gerçekçi deniz kazaları, fırtınalar, tehlikeli manevralar ve mürettebat mücadelesi videoları üretip YouTube Shorts'a yükleyen tam otonom pipeline.

## 🚨 Kalıcı Kural: Zorunlu İnsan / Mürettebat Varlığı & Rol Çeşitliliği
- Her videoda mutlaka en az bir insan/mürettebat görünür; tamamen insansız video kesinlikle üretilmez.
- İnsanlar olayın aktif parçasıdır (kaptan, zabit, güverte personeli, makine zabiti, marina/liman personeli, yolcu, kurtarma ekibi).
- Yapılan iş/müdahale kriz durumuna doğrudan bağlıdır (acil manevra, halat bağlama, lashing sabitleme, tahliye, arıza tamiri, kurtarma).
- Olay, gemi, lokasyon, rol ve kamera perspektifleri sürekli çeşitlendirilir.
- **Uygulama (2026-09-24):** Gemi sahnelerinde mürettebat/yolcu, sayılı ve domain aralığında (`DOMAIN_CAST_RANGES`). Çevre odaklı sahnelerde (hortum, şehir, plaj) en az 1 izleyici/sivil, arka plan ölçeği olarak (çatıdaki seyirciler, kaldırımdaki yayalar); sayı serbest. İnsansız senaryo ve prompt kapılarda reddedilir.

## 📋 Genel Bakış

> Güncel durumun tek doğru kaynağı `BASLANGIC.md`dir — burası sadece yapı/kurulum özetidir, ayrıntı ve gerekçe için `BASLANGIC.md`'ye bakın.

Bu sistem cron aktifken **sıfır insan müdahalesi** ile çalışır. Railway CronJob Pazartesi ve Cuma 16:30 TR'de tetikler ve şu akışı izler (cron durumu için bkz. Railway CronJob bölümü):

1. **🧠 Creative Engine** — 7 ilham alanı: 4 gemi domaini (feribot, tersane, marina/yat, kruvaziyer) + 3 çevre odaklı (kıyı hortumu, şehir afeti, plaj). 9 gemilik evren (feribot, katamaran, yat, powerboat, jet ski, kruvaziyer, tender); kargo/tanker/römorkör/balıkçı YOK (2026-09-24). Uyumsuz gemi-ortam kombinasyonları seçilmez. 71 senaryoluk referans kütüphane (8 kategori).
2. **🤖 GPT-4o** — Gerçekçi, fizik kurallarına uygun, yapılandırılabilir süreli (şu an 15s) tek plan 3 beat'lik senaryo yazar (5 aday); atanan kamera arketipine (`fixed_cctv`/`bystander_handheld`/`chase_pov`) göre yazılır
3. **✅ Senaryo Kapıları** — görünürlük, yüksek aksiyon, Beat 3 devam eden tehlike, cast aralığı, özet-beat tutarlılığı, gemi-ortam uyumu. Geçen adaylar skorlanır.
4. **✂️ Prompt Simplifier + Çıktı Kapısı** — Senaryoyu 25-45 kelimelik hikayeye çevirir; aşağıdaki A-J kapıları kontrol edilir, kalırsa geri bildirimle yeniden dener. Yazıcıya son kullanılan Beat 1 fiilleri "farklı fiil seç" ipucu olarak gider (Notion "Beat1 Fiil")
5. **🔒 Stil Kilidi** — Kamera arketipine ve domain'e göre deterministik kamera/çekim yeri/kıyafet/gerçekçilik eki hikayenin arkasına eklenir
6. **🛡️ Safety Check** — Regex + GPT preflight + Kie reddinde retry rewrite; hepsi sadece hikayeye uygulanır, stil eki korunur. Sessiz fallback yok.
7. **🎬 Seedance 2 Mini (Kie AI)** — Video üretir (`bytedance/seedance-2-fast`, 480p, portrait 9:16)
8. **📈 Hareket Profili** — İndirilen videonun saniye saniye hareket ölçümü (ffmpeg) Notion "Hareket" alanına yazılır
9. **📺 YouTube Upload** — Shorts olarak **private** yüklenir (`YOUTUBE_PRIVACY` varsayılanı); kullanıcı manuel inceleyip AI-etiketini işaretledikten sonra elle public yapar
10. **📋 Notion Log** — Tüm süreci ve tekrar-önleme combo key'ini kaydeder (2026-09-12'den beri aktif); reddedilen denemeler "❌ Hata" olarak kapanır

`infrastructure/replicate_merger.py` (çoklu klip birleştirme) kodda mevcuttur ama şu an ULAŞILAMAZ durumda — pipeline her zaman tek sahne ürettiği için hiç çağrılmıyor; gelecekte çoklu klip desteği geri gelirse devreye girer.

## 🏗️ Mimari

```
YT_Otomasyonu/
├── main.py                          # CronJob entry point
├── config.py                        # Fail-fast yapılandırma
├── logger.py                        # Logging
├── core/
│   ├── creative_engine.py           # Yaratıcı senaryo motoru (7 alan, 71 senaryo, 3 kamera arketipi, stil kilidi)
│   ├── prompt_generator.py          # Senaryo + kapılar + simplifier pipeline
│   └── prompt_sanitizer.py          # İçerik güvenliği (regex + preflight + rewrite)
├── infrastructure/
│   ├── kie_client.py                # Seedance 2.0 API (video üretim)
│   ├── motion_profile.py            # Hareket profili ölçümü (ffmpeg)
│   ├── replicate_merger.py          # Video birleştirme
│   ├── video_downloader.py          # Video indirme + cleanup
│   ├── youtube_uploader.py          # OAuth2 YouTube upload
│   └── notion_logger.py             # Notion DB tracking + tekrar önleme
├── railway.json                     # Railway deploy + cron (30 13 * * 1,5)
├── railpack.json                    # Railway build (railpack): çalışma imajına ffmpeg
├── .github/workflows/tests.yml      # CI: unittest; Railway "Wait for CI" buna bağlı
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
| **Sivil/Mürettebat** | Ayrık kurallar | Gemi domainleri: mürettebat = PPE, yolcu/misafir/sürücü = sivil kıyafet. Çevre odaklı domainler: sivil kıyafet + acil durum personeli üniforması |
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

# Testler (pytest değil)
python -m unittest discover -s tests
```

### Test / doğrulama betikleri (`scripts/`)

```bash
python scripts/dry_run_full.py                     # 5 senaryo, tüm kapılar, GPT (~$0.15), Kie YOK
python scripts/finalize_prompts.py scratch/dry_run_full_out.json 1,3   # seçilenleri Kie'ye hazır hikaye + stil ekine çevir
python scripts/run_kie_batch.py scratch/final_prompts.json test_prod_x  # ⚠️ GERÇEK KIE HARCAMASI — sadece açık onayla
python scripts/notion_test_page.py scratch/kie_batch_result.json "TEST — ..."  # Notion TEST sayfası (Combo Key'siz)
python scripts/motion_profile.py video.mp4 --camera fixed_cctv          # hareket profili (ffmpeg)
```
`scratch/` git'e girmez; geçici çıktılar oraya yazılır.

## 🕐 Railway CronJob

- **Komut:** `python main.py`
- **Zamanlama:** ✅ AKTİF — `railway.json` cronSchedule `30 13 * * 1,5` (Pazartesi + Cuma 16:30 TR). 2026-09-12'de açıldı (commit `1f7a389`); son doğrulanan otomatik koşu 2026-09-21. Kod düzeltme turları sürerken cron'un devam edip etmeyeceği kararı açık (2026-09-24). Cron'u aktif tutmak otomatik Kie harcaması demektir.
- **Tip:** CronJob (çalışır, iş bitince kapanır)
- **Deploy (2026-09-25):** `main`'e push → GitHub Actions `tests` (unittest) → geçerse Railway otomatik deploy eder ("Wait for CI"; test kırılırsa deploy atlanır). Öncesinde otomatik deploy YOKTU, Railway 23 Eylül'deki eski commit'te kalmıştı.
- **YouTube token (HAFTALIK, her Cuma 16:30'dan önce):** Google uygulaması "Testing" modunda olduğu için refresh token onaydan 7 gün sonra ölür; refresh çağrısı yeni refresh token vermez. `refresh_youtube_token.bat`'a çift tıkla → tarayıcıda DeepMyster hesabıyla "İzin ver" → betik kanalı doğrular, Railway'e yazar (Railway yeniden deploy eder), geri okuyup test eder, lokal `.env`'i günceller. Kalıcı çözüm: Google Cloud'da uygulamayı "In production" + doğrulama (ayrı iş).
- **Build:** Railway `railpack` kullanır, `nixpacks.toml` okunmaz. Sistem paketleri `railpack.json` → `deploy.aptPackages` (ffmpeg, hareket profili için).
- **Güncel durum ve gerekçe:** bkz. `_knowledge/deploy-registry.md` (bu dosya infra durumunun kaynağıdır)

## ✅ Kalite Kapıları

**Senaryo kapıları** (5 adayın her birine): görünürlük, yüksek aksiyon, Beat 3 devam eden tehlike (çözülmüş/sakinleşmiş, "halt", zayıf büyüklük "ripples/gently/slightly/bobbing" kara listede; insan jestleri "gesturing/inspecting" devam işareti sayılmaz), cast (gemi domainlerinde `DOMAIN_CAST_RANGES` aralığı; çevre odaklıda en az 1 insan), özet-beat tutarlılığı, gemi-ortam uyumu.

**Simplifier çıktı kapıları** (`SIMPLIFIER_GATES`, Kie'ye giden hikayeye):

| Kapı | Ne kontrol eder |
|------|-----------------|
| A | Son cümle Beat 3 kapısından geçer: tehlike sürüyor, zayıf/durmuş son yok |
| B | İlk cümlenin öznesi kamera/görüntü değil |
| C | Yazıcının bildirdiği Beat 1 fiili ilk cümlede (zaman sıkışması yok) |
| E | Gemi domainlerinde senaryodaki kişi sayısı korunur |
| F | Gemi domainlerinde atanan gemi tipiyle anılır ("the vessel" değil) |
| G | İlk cümlede duygusal insan tepkisi yok (startled, alarmed, shocked...) |
| H | Çevre odaklı domainlerde en az 1 insan (çatı seyircisi, yaya...) |
| I | İlk cümlede durağan insan yok (stand, watch, look, wait...) |
| J | İnsanlara senaryoda olmayan zarar fiili eklenmez (sweep, hurl, knock...) |

## 🛡️ Güvenlik Katmanları

1. **Prompt Sanitizer** — Tehlikeli kelimeleri otomatik değiştirir (regex)
2. **GPT Pre-flight Check** — Hikayeyi Kie'ye göndermeden değerlendirir; geçersiz cevapta 3 deneme, sonra `PreflightError` (api / content)
3. **Content Filter Retry** — Kie reddederse hikayeyi GPT ile yeniden yazar (2x); stil eki değişmez; rewrite başarısızsa sessiz yumuşatma yok, ret fırlar
3b. **Rewrite sonrası kalite kapıları** — Preflight veya Kie retry rewrite'ından dönen hikaye aynı simplifier kapılarından geçer (C hariç; güvenlik rewrite'ı Beat 1 fiilini değiştirmek zorunda kalabilir). Kalırsa geri bildirimle 1 kez daha yazılır, yine kalırsa yeni senaryo denenir
4. **Senaryo Retry** — Kie reddi veya içerik kaynaklı preflight hatasında farklı senaryo seçer (ortak 3 deneme); API kaynaklı preflight hatasında durur

## 📊 Tekrar Önleme

- **Durum: ✅ Aktif (2026-09-12)** — Notion veritabanı kuruldu, `NOTION_ENABLED=True`
- Kullanılan `domain\|vessel\|event\|environment\|camera` kombinasyonları Notion DB'de `Combo Key` alanında saklanır
- Her çalışmada son 60 günün tamamlanmış kayıtları (used combos) ve son 30 günün hata olmayan kayıtları (negatif hafıza) sorgulanır
- Sadece bugünkü evrene ait combo'lar sayılır (eski kargo/tug/trawler dönemi kayıtları ve Combo Key'siz TEST kayıtları hariç)

## 📝 Notion DB Alanları

| Alan | Tip | Açıklama |
|------|-----|----------|
| Video Adı | Title | YouTube başlığı |
| Durum | Select | Pipeline durumu |
| Model | Select | `bytedance/seedance-2-fast` |
| Tetikleyici | Select | "auto" (cron) veya "manual" |
| Konu | Rich Text | Senaryo özeti |
| Prompt | Rich Text | İlk sahne promptu |
| Combo Key | Rich Text | "domain\|vessel\|event\|environment\|camera" — tekrar önleme |
| Klip Sayısı | Number | Şu an her zaman 1 |
| Video URL | URL | CDN link |
| YouTube URL | URL | Shorts link |
| Tarih | Date | Üretim tarihi |
| Süre (sn) | Number | Pipeline süresi |
| Hata | Rich Text | Varsa hata mesajı |
| Güvenlik | Rich Text | Safety telemetrisi |
| Hareket | Rich Text | Hareket profili: ilk 3 sn / sonrası oranı, tepe saniye, saniyelik profil (2026-09-24) |
| Beat1 Fiil | Rich Text | Senaryonun Beat 1 fiili; son 10 kayıt yazıcıya "farklı fiil seç" ipucu olur (2026-09-24) |
