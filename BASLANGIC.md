# 🧭 DeepMyster (YT_Otomasyonu) — BAŞLANGIÇ REHBERİ & DERSLER

> **Bu dosyayı her oturum başında İLK oku.** Bu dosya DeepMyster pipeline'ının GÜNCEL DURUMUNUN tek doğru kaynağıdır (single source of truth). `README.md`, `filo.json` ve `_knowledge/deploy-registry.md` burasıyla çelişmemeli — çelişki görürsen bu dosyayı esas al.

---

## 🔴 GÜNCEL DURUM (Son doğrulama: 2026-09-12)

| Alan | Değer |
|---|---|
| **Süre** | 15 saniye — `config.DEFAULT_DURATION` üzerinden `.env`'deki `DEFAULT_DURATION` ile dinamik, hardcoded değil |
| **Video Modeli** | `bytedance/seedance-2-fast` (Seedance 2 Mini), 480p — Seedance Full, Veo 3.1 ve Wan 2.6 ile karşılaştırıldıktan sonra bilinçli olarak seçildi |
| **Gemi/Olay Çeşitliliği** | Tam kapsam: kargo gemileri, tankerler, kruvaziyer/yolcu gemileri, feribotlar, Ro-Ro/araç taşıyıcılar, römorkörler, yat/marina, kruvaziyer güverte/havuz sahneleri — kargo-only kısıtlama hiçbir zaman uygulanmadı (terk edilmiş bir taslaktı) |
| **Kamera Sistemi** | 3 ağırlıklı arketip: `fixed_cctv` (varsayılan/en sık), `bystander_handheld`, `chase_pov` — kamera sabitliği ve gerçekçilik güvenceleriyle |
| **Sivil/Mürettebat Kıyafeti** | Ayrım net: mürettebat/personel = turuncu/kırmızı/sarı PPE; yolcu/misafir/sürücü = sıradan sivil kıyafet (asla PPE değil) |
| **Aksiyon/Kalite Kapısı** | `validate_high_action` aktif — sakin/statik senaryoları reddedip yeniden dener |
| **YouTube Yükleme** | `YOUTUBE_PRIVACY=private` — videolar OTOMATİK PUBLIC OLMAZ; kullanıcı videoyu manuel inceleyip yapay zeka etiketini (AI-disclosure toggle) işaretledikten sonra elle public yapar |
| **Cron / Otomasyon** | ⏸️ Hâlâ duraklatılmış durumda — ama duraklatma sebebi (Notion dedup kurulumunun eksik olması) 2026-09-12 itibarıyla ortadan kalktı. Cron'un tekrar aktif edilmesi ayrı, henüz alınmamış bir karar (bkz. `_knowledge/deploy-registry.md`) |
| **Notion Dedup/Log** | ✅ AKTİF (2026-09-12) — `NOTION_ENABLED=True`, veritabanı kuruldu ve doğrulandı |

---

## 🚨 KRİTİK REFERANS STANDARDI: DOĞUKAN METODOLOJİSİ & YARATICI SERBESTLİK

**Tarih / Karar:** 2026-09-11 (Dolunay direktifi — Yaratıcı Serbestlik Restorasyonu & Doğukan "Less is More" Mimarisi). **Güncelleme:** 2026-09-12 (kamera arketipleri, sivil/mürettebat kıyafet ayrımı, aksiyon kalite kapısı ve tam gemi çeşitliliği eklendi — aşağıdaki bölümlere bakın).

### 1. Yapılandırılabilir Süreli Tek Kesintisiz Çekim (Single Continuous Take)
Seedance 2 Mini'nin en yüksek fotogerçekçilik ve fiziksel tutarlılık sunduğu format **tek, kesintisiz, kamera kesmesi/kolajı içermeyen** plandır. Süre sabit değildir — `config.DEFAULT_DURATION` / `.env`'deki `DEFAULT_DURATION` ile kontrol edilir (şu an **15 saniye**):
- Çoklu sahne geçişleri ve ara kesmeler KESİNLİKLE YOKTUR.
- Dron akrobasisleri, yapay kamera dönüşleri (orbit) YOKTUR.
- Gerçekçi bir endüstriyel gözetleme (CCTV) veya sabit belgesel gözlemci kamerası kullanılır.

---

### 2. Doğukan Metodolojisi ("Less is More" — 25–45 Kelimelik Yüksek Sinyalli Prompt)
Seedance 2 Mini karmaşık, 6 parçalı mekanik checklistleri değil; görsel sinyali yüksek, doğrudan ve net dili anlar:
- **Uzunluk:** Kesinlikle **25–45 kelime** aralığında olmalıdır.
- **İçerik Formülü (Esnek):**
  `[Gemi/Lokasyon & Çevresel Kriz] + [Somut Fiziksel Eylem & Bağlamsal İnsan/Mekanizma Müdahalesi] + [Fiziksel Durum Değişimi/Sonuç] + [Sabit CCTV/Kamera & Doğal Işık Etiketi]`
- **Few-Shot Kuralı:** Asla tek tip cümle kalıbı taklit edilmez; eylem odaklı, perspektif odaklı, mekanik gerilim veya atmosfer odaklı çeşitli sözdizimleri kullanılır.

---

### 3. Tersine Çevrilmiş Kontrol (Inversion of Control) & Geniş Denizcilik Katalizörleri
GPT bir "boşluk doldurucu" (Mad-Libs) değil; sahneyi tasarlayan **yaratıcı yönetmendir**:
- Python kodu gemi, nesne, başlangıç ve bitiş cümlelerini tek tek seçip GPT'ye dikte ETMEZ.
- Python **12 geniş denizcilik ilham alanından** (Kutup/Buzul, Ağır Yük, Kurtarma/Römorkör, Açık Deniz İkmal, Ro-Ro/Feribot, Dökme/Tanker, Konteyner, Ticari Balıkçılık, Kılavuzluk, Tersane, **Marina & Yat Operasyonları**, **Yolcu Gemisi & Kruvaziyer Operasyonları**) bir katalizör ve son işlenen konuların negatif listesini iletir. Son ikisi 2026-09-12'de eklendi.
- GPT kendi özgün gemisini, kriz mekanizmasını ve koreografisini bu alan içinde tasarlar.
- **Gemi çeşitliliği kargo ile SINIRLI DEĞİLDİR:** kargo/tanker/konteyner gemilerinin yanı sıra kruvaziyer, feribot, Ro-Ro/araç taşıyıcı, römorkör, yat/tekne ve marina sahneleri de tam kapsamlıdır. 71 senaryoluk referans kütüphanesi (8 kategoride) bu tam çeşitliliği yansıtacak şekilde güncellendi.

---

### 4. Organik ve Rol Odaklı İnsan Varlığı
- Her videoda yapay bir şekilde takoza koşan sarı yelekli adam klişesi YASAKTIR.
- İnsan varlığı sahnenin doğasına göre organik olmalıdır (dümen konsolundaki kaptan, vinç operatörü, rıhtım palamarcısı, korumaya çekilen personel veya sadece devasa gemi ölçeğini veren gözlemci).
- **Sivil/Mürettebat kıyafet ayrımı (2026-09-12 eklendi):** Mürettebat/personel/marina çalışanları turuncu-kırmızı-sarı PPE, tulum veya dalgıç kıyafeti giyer. Yolcular, tekne sahipleri, misafirler ve araç sürücüleri/yolcuları MÜRETTEBAT DEĞİLDİR — sıradan sivil kıyafet giyerler (mayo/resort kıyafeti güverte-havuz sahnelerinde, günlük kıyafet araç güvertesi sahnelerinde). Sivillere asla PPE giydirilmez.

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

# Canlı GPT-4o tekli üretim testi:
python tests/test_live_prompt.py

# 5 farklı alandan çeşitlilik stres testi:
python tests/test_batch_diversity.py

# Sistem sağlık kontrolü:
python main.py --check
```
