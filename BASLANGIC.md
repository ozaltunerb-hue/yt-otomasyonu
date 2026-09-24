# 🧭 DeepMyster (YT_Otomasyonu) — BAŞLANGIÇ REHBERİ & DERSLER

> **Bu dosyayı her oturum başında İLK oku.** Bu dosya DeepMyster pipeline'ının GÜNCEL DURUMUNUN tek doğru kaynağıdır (single source of truth). `README.md`, `filo.json` ve `_knowledge/deploy-registry.md` burasıyla çelişmemeli — çelişki görürsen bu dosyayı esas al.

---

## 🔴 GÜNCEL DURUM (Son doğrulama: 2026-09-24)

| Alan | Değer |
|---|---|
| **Süre** | 15 saniye — `config.DEFAULT_DURATION` üzerinden `.env`'deki `DEFAULT_DURATION` ile dinamik, hardcoded değil |
| **Video Modeli** | `bytedance/seedance-2-fast` (Seedance 2 Mini), 480p — Seedance Full, Veo 3.1 ve Wan 2.6 ile karşılaştırıldıktan sonra bilinçli olarak seçildi |
| **Gemi/Olay Çeşitliliği** | 7 domain: 4 gemi (`ferry_operations`, `shipyard_and_drydock_engineering`, `marina_and_yacht_operations`, `cruise_ship_operations`) + 3 çevre odaklı (`coastal_tornado_landfall`, `urban_city_disasters`, `open_beach_coastal_events`). 9 gemilik evren `DOMAIN_ATTRIBUTES`'tan türer: Passenger Car Ferry, High-speed Catamaran, Luxury Motor Yacht, Sailing Yacht, Runaway Powerboat, Jet Ski, Ocean Cruise Liner, Mega Cruise Ship, Cruise Tender Boat. **Kargo, tanker, konteyner, römorkör, balıkçı teknesi YOK** (2026-09-24 kargo temizliği; testler bu kelimeleri yasaklar). Uyumsuz kombinasyonlar seçilmez (`SHIP_INCOMPATIBLE`, `VESSEL_ENVIRONMENTS`: tender'da havuz güvertesi yok, tornado'da gemi sadece marina/limanda) |
| **Kalite Kapıları** | Senaryo: görünürlük, yüksek aksiyon, Beat 3 devam eden tehlike, cast aralığı (`DOMAIN_CAST_RANGES`), özet-beat tutarlılığı, gemi-ortam uyumu. Simplifier çıktısı (`SIMPLIFIER_GATES`, retry'lı): A Beat 3 devamı (zayıf büyüklük / halt dahil), B kamera öznesi, C Beat 1 fiili, E kişi sayısı, F gemi adı, G ilk cümlede insan tepkisi, H çevre odaklıda en az 1 insan, I ilk cümlede durağan insan, J insanlara yeni zarar fiili (tablo: README "Kalite Kapıları"). Preflight/Kie rewrite'ından dönen hikaye de aynı kapılardan geçer (C hariç). Preflight: geçersiz cevapta 3 deneme, `PreflightError` (api/content). Hiçbir kapıda sessiz fallback yok |
| **Her Videoda İnsan** | Gemi domainlerinde sayılı mürettebat/yolcu (`DOMAIN_CAST_RANGES`); çevre odaklı domainlerde en az 1 izleyici/sivil (senaryo kapısı + H). 2026-09-24 öncesi 8 env-centric çıktının 8'i insansızdı |
| **Beat 1 Fiil Rotasyonu** | Notion "Beat1 Fiil" alanı; son 10 fiil + koşu içi önceki adayların fiilleri yazıcıya "farklı, belirgin hareketli fiil seç" ipucu olarak gider (kapı değil) |
| **Hareket Ölçümü** | Her üretim videosu için `infrastructure/motion_profile.py` (ffmpeg) Notion "Hareket" alanına ilk 3 sn / sonrası oranını yazar. Baz: iki test videosunda ≈0.5 |
| **Kamera Sistemi** | 3 ağırlıklı arketip: `fixed_cctv` (varsayılan/en sık), `bystander_handheld`, `chase_pov` — kamera sabitliği ve gerçekçilik güvenceleriyle |
| **Sivil/Mürettebat Kıyafeti** | Ayrım net: mürettebat/personel = turuncu/kırmızı/sarı PPE; yolcu/misafir/sürücü = sıradan sivil kıyafet (asla PPE değil) |
| **Aksiyon/Kalite Kapısı** | `validate_high_action` aktif — sakin/statik senaryoları reddedip yeniden dener |
| **YouTube Yükleme** | `YOUTUBE_PRIVACY=private` — videolar OTOMATİK PUBLIC OLMAZ; kullanıcı videoyu manuel inceleyip yapay zeka etiketini (AI-disclosure toggle) işaretledikten sonra elle public yapar |
| **Cron / Otomasyon** | ✅ AKTİF — `railway.json` cronSchedule `30 13 * * 1,5` (Pazartesi + Cuma 16:30 TR). 2026-09-12'de açıldı (commit `1f7a389`); son doğrulanan otomatik koşu 2026-09-21. Kod düzeltme turları sürerken cron'un devam edip etmeyeceği kararı açık (2026-09-24). Cron aktifken her tetikleme otomatik Kie harcamasıdır (bkz. `_knowledge/deploy-registry.md`) |
| **Notion Dedup/Log** | ✅ AKTİF (2026-09-12) — `NOTION_ENABLED=True`, veritabanı kuruldu ve doğrulandı |

---

## 📋 DEVİR — Açık işler (2026-09-25, gece kapanışı)

**Durum (doğrulandı):** TUR 1-23 kodu `main`'de (son `b097590`), 279/279 test. Railway aktif deploy = `b097590`
(GitHub Actions `tests` yeşilse otomatik deploy, "Wait for CI"; tetikleyici 54618a0d). Çalışma imajında ffmpeg var
(railpack.json). Cron `30 13 * * 1,5` UTC. TUR 21 Kie doğrulaması: 2 video kullanıcı tarafından kabul edildi
(Video 2 bug'ları — durağan açılış, "the vessel", kargo, zayıf Beat 3 — çözüldü).

**Sıradaki somut adımlar:**
1. **Cuma 25 Eylül 16:30 TR'den ÖNCE:** YouTube token'ını yenile — `refresh_youtube_token.bat` (ilk kez komut satırından:
   `python scripts\refresh_youtube_token.py`, tarayıcıda DeepMyster hesabıyla onay). Sonra masaüstü kısayolu.
2. **Cuma 16:45 TR'den sonra:** ilk production cron koşusunun 10 maddelik kontrolü — Railway çalışma logları (kapılar,
   retry, preflight, Kie, indirme, YouTube), Notion'daki yeni `auto` kaydı (Durum, Hareket ARTIK DOLU olmalı, Beat1 Fiil,
   YouTube URL), Kie kredisi (koşu öncesi 726.0, `scratch/cron_credit_before.json`).
3. Ayrı iş: Google Cloud'da OAuth uygulamasını "In production" + doğrulama (7 günlük token sorunu kalıcı biter).

**Bilerek açık:** P1 stil kilidi uzunluğu (cron hareket verisi bekliyor), U3 yön dönüşü ölçülmüyor, Kie kredi/dolar kuru
doğrulanmadı (video başı ~175 kredi), süreç dışarıdan öldürülürse Notion kaydı takılabilir (süpürücü yok).

**Nerede yanılmış olabilirim:** "Upload Başarısız" kayıtlarının lokal ölü token'dan geldiği çıkarımdır, loglarla
doğrulanmadı. ffmpeg'in Railway'de çalıştığı build logundan görüldü; kesin kanıt ilk cron'da Hareket alanının dolması.

---

## 🚨 KRİTİK REFERANS STANDARDI: DOĞUKAN METODOLOJİSİ & YARATICI SERBESTLİK

**Tarih / Karar:** 2026-09-11 (Dolunay direktifi — Yaratıcı Serbestlik Restorasyonu & Doğukan "Less is More" Mimarisi). **Güncelleme:** 2026-09-12 (kamera arketipleri, sivil/mürettebat kıyafet ayrımı, aksiyon kalite kapısı ve tam gemi çeşitliliği eklendi — aşağıdaki bölümlere bakın).

### 1. Yapılandırılabilir Süreli Tek Kesintisiz Çekim (Single Continuous Take)
Seedance 2 Mini'nin en yüksek fotogerçekçilik ve fiziksel tutarlılık sunduğu format **tek, kesintisiz, kamera kesmesi/kolajı içermeyen** plandır. Süre sabit değildir — `config.DEFAULT_DURATION` / `.env`'deki `DEFAULT_DURATION` ile kontrol edilir (şu an **15 saniye**):
- Çoklu sahne geçişleri ve ara kesmeler KESİNLİKLE YOKTUR.
- Dron akrobasisleri, yapay kamera dönüşleri (orbit) YOKTUR.
- Kamera, 3 arketipten biridir (`fixed_cctv`, `bystander_handheld`, `chase_pov`; bkz. bölüm 7).

---

### 2. Doğukan Metodolojisi ("Less is More" — 25–45 Kelimelik Yüksek Sinyalli Prompt)
Seedance 2 Mini karmaşık, 6 parçalı mekanik checklistleri değil; görsel sinyali yüksek, doğrudan ve net dili anlar:
- **Uzunluk:** Kesinlikle **25–45 kelime** aralığında olmalıdır.
- **İçerik Formülü (Esnek):**
  `[Adıyla anılan gemi veya çevre olayı + aksiyon + fiziksel etki] + [Fiziksel Eylem & İnsan/Mekanizma Müdahalesi] + [Hâlâ süren Sonuç]`
- **Kamera ve ışık 25-45 kelimenin içinde YOKTUR:** Simplifier kamera/ışık yazmaz; kamera, çekim yeri, kıyafet ve gerçekçilik kuralları stil kilidiyle (`style_lock_suffix`) arkadan eklenir. Kie retry'larında GPT sadece hikayeyi yeniden yazar, stil eki değişmez.
- **Few-Shot Kuralı:** Asla tek tip cümle kalıbı taklit edilmez; eylem odaklı, perspektif odaklı, mekanik gerilim veya atmosfer odaklı çeşitli sözdizimleri kullanılır.

---

### 3. Tersine Çevrilmiş Kontrol (Inversion of Control) & Geniş Denizcilik Katalizörleri
GPT bir "boşluk doldurucu" (Mad-Libs) değil; sahneyi tasarlayan **yaratıcı yönetmendir**:
- Python kodu gemi, nesne, başlangıç ve bitiş cümlelerini tek tek seçip GPT'ye dikte ETMEZ.
- Python **7 ilham alanından** (Feribot, Tersane/Kuru Havuz, Marina & Yat, Kruvaziyer + çevre odaklı Kıyı Hortumu, Şehir Afeti, Plaj) bir katalizör (alan + atanan gemi/olay/ortam) ve son işlenen konuların negatif listesini iletir. 2026-09-24'te 12 alandan 7'ye inildi (kargo evreni kaldırıldı).
- GPT senaryoyu atanan gemiyle (adıyla anarak, "the vessel" değil) ve bu alan içinde tasarlar.
- **Gemi evreni 9 tiptir, kargo YOKTUR:** kargo/tanker/konteyner/römorkör/balıkçı teknesi yazıcıya hiç önerilmez ve testler bu kelimeleri yasaklar. 71 senaryoluk referans kütüphanesi (8 kategoride) bu evrene göre temizlendi.

---

### 4. Organik ve Rol Odaklı İnsan Varlığı
- Her videoda yapay bir şekilde takoza koşan sarı yelekli adam klişesi YASAKTIR.
- İnsan varlığı sahnenin doğasına göre organik olmalıdır (dümen konsolundaki kaptan, vinç operatörü, rıhtım palamarcısı, korumaya çekilen personel veya sadece devasa gemi ölçeğini veren gözlemci).
- **Sivil/Mürettebat kıyafet ayrımı (2026-09-12 eklendi):** Mürettebat/personel/marina çalışanları turuncu-kırmızı-sarı PPE, tulum veya dalgıç kıyafeti giyer. Yolcular, tekne sahipleri, misafirler ve araç sürücüleri/yolcuları MÜRETTEBAT DEĞİLDİR — sıradan sivil kıyafet giyerler (mayo/resort kıyafeti güverte-havuz sahnelerinde, günlük kıyafet araç güvertesi sahnelerinde). Sivillere asla PPE giydirilmez.
- **Çevre odaklı domainler (2026-09-24):** Şehir/plaj/hortum prompt'larına gemi rolleri (ferry officer, car-deck) gitmez; sadece sivil kıyafet + acil durum personeli üniforması kuralı eklenir (gemi varsa marina/iskele işçisi PPE).

---

### 5. Semantik Negatif Hafıza (Anti-Tekrar)
- Tekrar engelleme sadece string eşleşmesi ile değil; Notion'dan gelen son 15-20 konunun GPT'ye `DO NOT REPEAT` negatif promptu olarak verilmesiyle sağlanır.
- **Durum (2026-09-12):** Notion veritabanı kuruldu ve `NOTION_ENABLED=True` — bu mekanizma artık AKTİF. Kurulumdan önce Notion devre dışıydı ve bu bölümdeki anti-tekrar sağlanamıyordu.

---

### 6. Merak Kuralı & Spoiler Yasağı
- Başlık ve açıklama sonucu baştan ele veremez (Örn: "Saved by Crew" ❌, "⚠️ Heavy Swell Slams Open Ro-Ro Ramp #Shorts" ✅).
- Başlık MAX 55 karakterdir ve doğrudan KRİZE odaklanır.

---

### 7. Kamera Arketip Sistemi (2026-09-12 eklendi)
Her üretimde Python ağırlıklı rastgele 3 kamera arketipinden birini seçer (GPT'ye ve deterministik "stil kilidi"ne aynı seçim aktarılır, çelişki olmaz):
- **`fixed_cctv`** (varsayılan/en sık) — sabit güvenlik/CCTV kamerası; dışarıdan çekimlerde gövde/pruva/üst yapı görünür olmalı, güverte/havuz/araç güvertesi gibi gemi-içi sahnelerde ise güverte mimarisi/korkuluklar yeterlidir.
- **`bystander_handheld`** — yolcu/izleyici elde telefon görüntüsü; çerçeveleme ilk anda sabitlenir ve TÜM SÜRE BOYUNCA değişmez (yavaş zoom/push-in dahil YASAK); korkuluk/pencere/lombar gibi bir sınır öğesi varsa sahne boyunca kadrajda kalmalıdır.
- **`chase_pov`** — yakındaki bir tekneden takip/kovalama POV'u; İKİ AYRI GEMİ zorunludur (gözlemci tekne + krizdeki ikinci gemi), tek gemi fırtına sahnesine düşülemez.

### 8. Aksiyon/Kalite Kapısı: `validate_high_action` (2026-09-12 eklendi)
`validate_silent_visibility` ile aynı retry döngüsünde çalışır. Senaryoda en az bir aktif tehlike/aksiyon kelimesi (collision, snap, flood, list, capsize...) yoksa reddedilir ve farklı bir katalizörle yeniden denenir — "sakin/rutin" sahneler (örn. bir aracın sorunsuzca rampaya girmesi) bu şekilde elenir.

---

## 🛠️ Hızlı Doğrulama Komutları

```bash
# Dry-run testi (Mock pipeline):
python main.py --dry-run

# Birim testleri (API çağrısı yok):
python -m unittest discover -s tests

# Tam dry-run: 5 senaryo, tüm kapılar (GPT ~$0.15, Kie yok):
python scripts/dry_run_full.py

# Canlı GPT-4o tekli üretim testi (eski betik, gerçek GPT):
python scripts/live_prompt_check.py

# 5 farklı alandan çeşitlilik stres testi (eski betik, gerçek GPT):
python scripts/batch_diversity_check.py

# Sistem sağlık kontrolü:
python main.py --check
```
