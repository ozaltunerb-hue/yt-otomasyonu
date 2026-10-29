# 🧭 DeepMyster (YT_Otomasyonu) — BAŞLANGIÇ REHBERİ & DERSLER

> **Bu dosyayı her oturum başında İLK oku.** Bu dosya DeepMyster pipeline'ının GÜNCEL DURUMUNUN tek doğru kaynağıdır (single source of truth). `README.md`, `filo.json` ve `_knowledge/deploy-registry.md` burasıyla çelişmemeli — çelişki görürsen bu dosyayı esas al.

---

## 🔴 GÜNCEL DURUM (Son doğrulama: 2026-09-24)

| Alan | Değer |
|---|---|
| **Süre** | 15 saniye — `config.DEFAULT_DURATION` üzerinden `.env`'deki `DEFAULT_DURATION` ile dinamik, hardcoded değil |
| **Video Modeli** | `bytedance/seedance-2-fast` (Seedance 2 Mini), 480p — Seedance Full, Veo 3.1 ve Wan 2.6 ile karşılaştırıldıktan sonra bilinçli olarak seçildi |
| **Gemi/Olay Çeşitliliği** | 8 domain: 4 gemi (`ferry_operations`, `shipyard_and_drydock_engineering`, `marina_and_yacht_operations`, `cruise_ship_operations`) + 4 çevre odaklı (`coastal_tornado_landfall`, `urban_city_disasters`, `open_beach_coastal_events`, `landslide_disasters` 2 Eki). Menüde 24 aktif olay (iskelet hattı). 9 gemilik evren `DOMAIN_ATTRIBUTES`'tan türer: Passenger Car Ferry, High-speed Catamaran, Luxury Motor Yacht, Sailing Yacht, Runaway Powerboat, Jet Ski, Ocean Cruise Liner, Mega Cruise Ship, Cruise Tender Boat. **Kargo, tanker, konteyner, römorkör, balıkçı teknesi YOK** (2026-09-24 kargo temizliği; testler bu kelimeleri yasaklar). Uyumsuz kombinasyonlar seçilmez (`SHIP_INCOMPATIBLE`, `VESSEL_ENVIRONMENTS`: tender'da havuz güvertesi yok, tornado'da gemi sadece marina/limanda) |
| **Kalite Kapıları** | Senaryo: görünürlük, yüksek aksiyon, Beat 3 devam eden tehlike, cast aralığı (`DOMAIN_CAST_RANGES`), özet-beat tutarlılığı, gemi-ortam uyumu. Simplifier çıktısı (`SIMPLIFIER_GATES`, retry'lı): A Beat 3 devamı (zayıf büyüklük / halt dahil), B kamera öznesi, C Beat 1 fiili, E kişi sayısı, F gemi adı, G ilk cümlede insan tepkisi, H çevre odaklıda en az 1 insan, I ilk cümlede durağan insan, J insanlara yeni zarar fiili, K görünmez sebep, L fizik ihlali, M kelime sayısı, N side launch metni (tablo: README "Kalite Kapıları"). Senaryo kapılarına TUR 24'te görünür tetik ve sahne fiziği eklendi. Preflight/Kie rewrite'ından dönen hikaye de aynı kapılardan geçer (C ve M hariç). Preflight: geçersiz cevapta 3 deneme, `PreflightError` (api/content). Hiçbir kapıda sessiz fallback yok |
| **Her Videoda İnsan** | Gemi domainlerinde sayılı mürettebat/yolcu (`DOMAIN_CAST_RANGES`); çevre odaklı domainlerde en az 1 izleyici/sivil (senaryo kapısı + H). 2026-09-24 öncesi 8 env-centric çıktının 8'i insansızdı |
| **Beat 1 Fiil Rotasyonu** | Notion "Beat1 Fiil" alanı; son 10 fiil + koşu içi önceki adayların fiilleri yazıcıya "farklı, belirgin hareketli fiil seç" ipucu olarak gider (kapı değil) |
| **Hareket Ölçümü** | Her üretim videosu için `infrastructure/motion_profile.py` (ffmpeg) Notion "Hareket" alanına ilk 3 sn / sonrası oranını yazar. Baz: iki test videosunda ≈0.5 |
| **Kamera Sistemi** | 3 ağırlıklı arketip: `fixed_cctv` (varsayılan/en sık), `bystander_handheld`, `chase_pov` — kamera sabitliği ve gerçekçilik güvenceleriyle |
| **Sivil/Mürettebat Kıyafeti** | Ayrım net: mürettebat/personel = turuncu/kırmızı/sarı PPE; yolcu/misafir/sürücü = sıradan sivil kıyafet (asla PPE değil) |
| **Aksiyon/Kalite Kapısı** | `validate_high_action` aktif — sakin/statik senaryoları reddedip yeniden dener |
| **YouTube Yükleme** | `YOUTUBE_PRIVACY=private` — videolar OTOMATİK PUBLIC OLMAZ; kullanıcı videoyu manuel inceleyip yapay zeka etiketini (AI-disclosure toggle) işaretledikten sonra elle public yapar |
| **YouTube OAuth Token** | ⚠️ Google uygulaması **TESTING** modunda: refresh token 7 gün sonra ölür. (12 Eki 2026 düzeltmesi: "7 Eki'de Production'a alındı" kaydı YANLIŞTI, kullanıcı doğruladı; Railway'de invalid_grant görüldü.) Her 7 günde bir `refresh_youtube_token.bat` (masaüstü kısayolu) çalıştırılır; panel son geçerliliği gösterir. Production'a alınırsa sınır kalkar; BİTTİ yazısı görülmeden pencere kapatılmaz. Betik önce yerel `.env` + `master.env`'e, sonra Railway'e yazar; adım logu `dashboard_data/token_refresh_runs.log` |
| **Cron / Otomasyon** | ❌ Cron KALDIRILDI (2026-09-26). Üretim Telegram botundan: `python bot.py` (Railway start komutu), `/uret` → domain seç. Sadece `TELEGRAM_CHAT_ID` sohbeti, tek seferde tek üretim. Otomatik Kie harcaması yok |
| **Notion Dedup/Log** | ✅ AKTİF (2026-09-12) — `NOTION_ENABLED=True`, veritabanı kuruldu ve doğrulandı |

---

## 📋 DEVİR: ☄️ Meteor (4): O4 pasif, K2 villa terası, ön planda yüksek bina yok, X3 (29 Eki 2026)

2. test videosu: kameranın yanındaki dev kule ve O4'ün yüksek binaları sebepsiz yer/şekil değiştirdi. O4 pasif
(`es.METEOR_RETIRED_ENVS`); K2 "High terrace of a seafront villa" (kadraj tipi balkon); meteorda ön plan cümlesi
`sk.METEOR_NO_FACE` ("no person, face or tall building close to the camera"; diğer olaylar aynı). X3 "knocking over" ile
havuzda. Bahadır kararı: W2+X1 dışlandı (yeni ön plan cümlesiyle O1 + öğle/kapalı ışıkta 205'i 1 kelime aşıyordu). 9 çift,
972 kombinasyon, sığmayan 0.

## 📋 DEVİR: ☄️ Meteor (3): yeni W2/W3/X1, tavan 205 (29 Eki 2026)

Bahadır kararları: meteor tavanı 195 -> 202 -> 205 (202'de 1008 kombinasyonun 204'ü 1-3 kelime aşıyordu; 205'te 0).
W2, W3, X1, X3 yeni metin; X3 yine havuza girmedi ("knocking down" hasar listesinde yok, listede "knock over"). X1 için
temas listesine "kiosk" eklendi (plaj büfesi yapı; "beach bar" gibi). Dışlanan çiftler (aynı nesne): W2+X2 araba, W3+X4
şezlong. Seçilebilir 7 çift: W1+X1, W1+X2, W1+X4, W2+X1, W2+X4, W3+X1, W3+X2. Aşağıdaki (2) notunun "push edilmedi"
durumu bu turla kapandı.

## 📋 DEVİR: ☄️ Meteor (2): tek çarpma zinciri, tsunami yasağı, kalıcı hasar (29 Eki 2026, PUSH EDİLMEDİ)

Yerel dal `meteor-2-bekliyor` (main'e gitmedi; canlı hâlâ 285c4c0). Sebep: Bahadır'ın kuralı "195'e sığmayan kombinasyon
olursa push etme". Kamera kuyruğu birebir ("the camera stays fixed on the bay, never tilting down or descending";
ortak kısaltma `_FIXED_ON` "on the bay"i silmesin diye muaf) ve tek kural cümlesiyle (`sk.METEOR_RULE`) stil eki 125-129
kelime; hikâye en az 70 (kilit 33 + insan 6 + W 15 + X 16). 195'te kod yedeği HİÇBİR kombinasyona sığmıyor (en kısa 198);
tavan 202 olursa 288/288 sığıyor ve son denetimden geçiyor (karakter en fazla 1196).
- Havuz: W1 / X2, X4 (2 çift). Havuza girmeyen (`es.METEOR_HELD_BEATS`): W2, X1 hasar fiili yok (engulfs, crashes/pours
  listede değil); W3 "awnings", X3 "fences" kalıcı lintte ince hedef. Puanların hepsi ≥3. Eski M/N havuzu RETIRED_BEATS'te;
  dalga bayrağı ve DISABLED_BEATS meteor kaydı kalktı.
- Kapılar (GPT ve kod yedeği): `meteor_one_impact` (rain, shower, fragment, debris, ember, fireball, meteors, meteorite,
  second, another, streak, chunk, falling rock), `meteor_no_tsunami`, `meteor_white_water`, `meteor_damage`,
  `meteor_objects` (`es.METEOR_OBJECT_GATES`). Eski iki GPT cümlesi ret alıyor (test).
- Sınırlar olaya göre: `es.PROMPT_WORDS_BY_EVENT` (meteor 195), `es.CONSTRAINTS_BY_EVENT` (11), diğerleri 175 / 8 / 1400.
- Karar bekleyen: meteor tavanı 202 (tek satır) ya da metin kısaltma; W2/W3/X1/X3 için yeni metin.

---

## 📋 DEVİR: ☄️ Meteor + deniz kategorileri pasif + helikopter kadrajı (29 Eki 2026)

Kie ve gerçek GPT çağrısı yok (kuru deneme de yok). Meteor dışındaki aktif olayların promptu önce/sonra birebir aynı
(`scripts/prompt_snapshot.py diff`: sadece helikopter kamera cümlesi ve yeni Meteor).

**Deniz kategorileri pasif:** ⛴️ Feribot, 🏗️ Tersane, ⛵ Marina & Yat Telegram menüsünde yok, eski düğmesi seçilemez,
rastgele kategori seçimine girmez (`sk.SEA_CATEGORIES_ACTIVE = False`, `sk.DISABLED_DOMAINS`). Kod, havuzlar, iskeletler,
testler yerinde. Açmak: `SEA_CATEGORIES_ACTIVE = True`. 🚢 Kruvaziyer aktif. Menü sıra numaraları değişmedi
(`bot.DOMAIN_KEYS` tüm kategoriler; Meteor sona eklendi).

**Helikopter kadrajı:** sadece yamaç evinin çatı terası ya da yüksek balkon (set/tepe kadrajı ve balkon mod A çıktı).
Cümle `fx.helicopter_camera`: "high wide view of the neighborhood and the wall of flames together, the helicopter large
and close in frame, never a distant dot; ... the camera stays fixed, never descending, empty foreground". "eye level",
"normal lens", "pans to follow" yok. Ön plan ekseni yok. Hikâye, beat, ortam seçimleri aynı (snapshot: 20/20 tohumda
sadece kamera cümlesi değişti, en uzun prompt 174). Hortum karaya vurur: tüm kadrajlar zaten yüksekti, dokunulmadı.

**☄️ Meteor (TASLAK)** `Meteor slams into the sea off the coast`, kategori `meteor_disasters`, menüde "☄️ Meteor" →
"☄️ Denize dev meteor düşer". Kilit cümle (33 kelime), kadraj K1-K3 (= kamera noktası, ödünç/kütüphane/ön plan yok,
`fx.OWN_SPOT_ONLY`), ortam O1-O4 (`es.METEOR_ENVS`), ışık 3 (`sk.METEOR_WEATHER`) Bahadır'ın metni birebir; her eksende son
2 tekrar etmez (Notion "Eksenler"). Kamera kuyruğuna Bahadır kararıyla "the camera stays fixed, never descending" eklendi
(K3 kuralı). Stil eki: Setting satırı + ENV_GUARDRAILS + gerçek zaman + yazı/tabela yok (8 kısıt), 95-99 kelime.
Hikâye 40-75, prompt en fazla 175, kişi 3-6, insanlar aşağıdaki sokakta (`_AVA_NEAR_RULE`). Araç yok.
- **Ek kural (puanlama):** 6 ölçütte 3'ün altındaki madde havuzda yok: M3, M4, M5, N4, N5 (`es.METEOR_HELD_BEATS`, puan +
  gerekçe). Havuz: M1, M2, M6 / N1, N2, N3, N6 (`es.METEOR_BEAT_SCORES`). Durağan fiil (`es.METEOR_STATIC`: billow, drift,
  rolls slowly, watch, stare, stand, calm, gently, slowly...) beat'te lint HATASI, GPT dilimlerinde ret
  (`meteor_no_static`). Her beat'te ev/araç/insan/ağaç teması lint'te zorunlu (`es.METEOR_CONTACT`).
- **[DALGA] bayrağı:** `es.METEOR_WAVE_ENABLED = False`; N1, N2 seçilmez (`es.DISABLED_BEATS`, genel mekanizma). M3 bayrağa
  bağlıydı ama puanlamada düştü (havuzda yok).
- **Seçilebilir çiftler (dalga kapalı):** M1+N3, M6+N3, M6+N6. Dışlananlar: M2+N3 (yanan çatı iki kez); kod yedeği hiç
  sığmayan M1+N6, M2+N6, N1'in tüm eşleri (kilit 33 + insan 6 + çift > 75). M2 dalga kapalıyken hiç seçilmez. Tekrar
  önleme derinliği 0 (3 çift LRU ile döner; 1 derinlikte M6+N3 sonrası aday kalmıyor).
- **Sığma koruması (meteor ortamı):** en uzun ortam (O4/O1) öğle/kapalı ışıkla M1+N3 ve M6+N6'da kod yedeğini 175'i 1-2
  kelime aşırıyor; o durumda sığan bir ortam/ışık seçilir (önce aynı ışık + tekrar önlemeye uyan ortam). Kayıt:
  `axes_excluded["ortam_sığmadı"]`.
- **Paylaşımlar Kategori:** caption `SHARE_CATEGORY` "Meteor" (Notion select seçeneği ilk yazımda oluşur; mevcut kayıtlara
  dokunulmadı), hashtag havuzu "meteor".
- Testler: `tests/test_meteor.py` (kilit metinler, kamera K1-K3, puan/lint, bayrak, tüm çiftlerde kod yedeği son
  denetimden geçer, 100 üretimde eksen tekrar önleme, sığma koruması, 6 örnek temiz, deniz kategorileri pasif, helikopter
  kadrajı).

**Açık kararlar (Bahadır):** Meteor havuzu ince (3 çift, M2 kullanılmıyor): M3/M4/M5/N4/N5 yerine yeni madde ve/veya N1
kısaltma (23 kelime, hiçbir eşle sığmıyor), M1/N6 kısaltma. Sığma koruması yerine kamera kuyruğundan "never descending"
çıkarılırsa (2 kelime) tüm ortam/ışık kombinasyonları sığar. 23 Ekim gecesinden bekleyenler (cadde P/Q önerileri, Y5+Z3,
köy "higher ground", Z7 18 kelime, açılış-araç kuralı genişlemesi) bu turda dokunulmadı.

---

## 📋 DEVİR: 🧹 Havuz temizliği + Parti 1 yeni beat'ler + kalıcı lint + Notion "Hikâye kaynağı" (17 Eki 2026)

Amaç: kusur sadece video motorundan gelsin, bizim taraftan hiç gelmesin. Kie çağrısı yok. Kül bulutuna dokunulmadı.

**Kural (çıkarma):** denetimde (`scratch/asama3_havuz_denetimi.md`) ZAYIF/ÇIKAR ve en az biri: ince/uzak/küçük hedef
(direk, tel, çit, tabela, cam, bariyer, tente, alçak duvar), fizik ≤2, aksiyon ≤2, yakın ≤2, büyük ≤2, koyu 1, boş arazi/
kırsal, cephe yangınında araç. Sadece tekrar(2)/koyu(2) yüzünden zayıf olan kalır. Daha önce videosu üretilmiş beat
KORUNAN (Notion'daki 40 videolu kayıt + 3 Eki sel testi V6+D2), çıkarılmaz. Grup 4'ün altına düşecekse ya da bir nokta
seçilemez olacaksa o grupta çıkarma yok: ÇIKIŞ BEKLİYOR.
- **Çıkanlar** (`es.RETIRED_BEATS`, kimlikler tekrar kullanılmaz): sel D1 D6 D7 · dalga W7 · yamaç S1 S6 · heyelan köy L2 ·
  hortum karaya C3 C6 E3 E6 · marina Y4 Y6 Z5 · cadde P3 Q5 · orman yangını L2 L6 · cephe N2 N6 · ateş hortumu T3 U3 U4 U5 ·
  helikopter G4 · şok dalgası S1 U1 · bombalar R6 T3 T4 · çığ orman F3.
- **Korunan ama kurala göre zayıf:** sel D2 · dalga W1 W2 W6 · yokuş M3 · yamaç R2 S4 · marina Z6 · cadde P6 Q3 Q6 ·
  orman K5 · cephe M6 · şok S2 U3 · bombalar R3 R4.
- **Çıkış bekliyor** (yerine yeni beat gelince çıkar): yokuş M1 M2 M5 · orman yangını K3 K4 K6 · cephe M1-M5 (araç
  beat'leri) · deprem eski sokak T2 · çığ orman E5 (çıkarsa balkon noktasında 1 derinlikte bile çift kalmıyor).
- **Küçük araç yok:** `REGION_VEHICLES`/`EVENT_VEHICLES` ve görünüm tarifleri büyük araç (large SUV, pickup, delivery/box
  truck, van). Eski adlar `RETIRED_VEHICLES(_BY_VIEW)` ile eski kayıt okunurken çevrilir.

**Parti 1 yeni beat'ler (Bahadır'ın metni birebir):** ateş hortumu T7, U7-U11 · bombalar R7-R9, T7-T9 · şok dalgası S6-S8,
U7-U8. U1 metni "across the street", nokta kısıtı kalktı. Havuzlar: ateş hortumu 6+8, bombalar 8+7, şok 7+7.
- Hariç çiftler: aynı yapı iki dilimde yok (bombalar R7×T1/T7 çatı, R8×T6 duvar, R9×T5 yol, R1/R2×T9 araç; şok S6×U4/U7/U8
  ev, S8×U2 araç). Kamera evi: şok U7 ve bombalar T7 çatı terası/köy evi balkonunda seçilmez.
- **Kod yedeği sığmayan çiftler hariç** (madde 1 kuralı): çığ köy A2/A4/A5 × B2/B5 (6), bombalar R7×T5/T8/T9, R8×T5/T8/T9,
  R9×T8 (7), şok S7×U8 (1), ateş hortumu 23 çift (yeni U7-U11 20-24 kelime; kilit 28-29 + insan 6 + çift > 75). Ateş
  hortumunda T6/T7 sadece U2/U6 ile eşleşir. **U10 hiç seçilemez** (24 kelime, her eşle 75'i 1-2 kelime aşıyor):
  kısaltma Bahadır onayı bekliyor (öneri: "...pulls them into its column" sonundaki "in a storm of sparks" çıkarsa 19).
- U8 ve U9 metninde büyüklük sıfatı yok (Bahadır'ın metni; kilit cümle ölçeği verir), testte istisna.
- Aday kalmazsa derinlik 1'e düşen olaylar (`BEAT_BLOCK_FALLBACK_EVENTS`): deprem + ateş hortumu, hortum karaya vuruş,
  orman yangını, çığ köy (normal akışta derinlik aynı).

**Yumuşak kapı düzeltmeleri:** helikopterde kendi nesnesi varsa "başka beat'e benziyor" kontrolü yok
(`OWN_OBJECT_ENOUGH_EVENTS`; F5 "cascade of water hits a burning house" F1'e benzetiliyordu) · helikopter ağaç listesi
"treetop(s)" tanır (`_FIRE_HELI_TREE`, orman yangını aynı) · deprem T2 nesnesi evler/binalar, "sequentially" zincir
grubunda. Regresyon: `tests/fixtures/rejected_real.json` 5 yeni kayıt ("origin" alanlı).

**Kalıcı lint** (`es.pool_lint_errors`, modül açılışında HATA): ince/uzak hedef, açık arazi, küçük araç, ticari gemi
sözcükleri beat metninde, araç adında ve görünüm tarifinde yok. Mevcut korunan/KALSIN/çıkış bekleyen 31 beat
`POOL_LINT_GRANDFATHERED`'da gerekçesiyle (liste birebir güncel olmak zorunda). Yeni beat lint'ten geçmeden paket açılmaz.

**Notion "Hikâye kaynağı":** `EXTRA_PROPERTIES`'te (`ensure_schema` ekler; ekleyemezse şema yine bilinir, alan yazılmaz).
Her yapılandırılmış üretimde ayrı istekle "GPT (deneme N)" / "kod yedeği (neden: ...)". İstatistik:
`tools\fallback_report.py --notion` (salt okuma). `data/story_source_log.jsonl` aynen sürer.

**Gerçek GPT kuru deneme** (`scratch/dry_run_parti1_17eki.json`, 54 çağrı, ~0,25 $, Kie yok, olay başına 10):
ateş hortumu GPT 9/10 (yedek 1: U1 cümlesinde "house" yok), bombalar GPT 6/10, şok dalgası GPT 5/10. Volkan yedek
nedeni yine uzunluk (175 kelime / toplam 75), 16 Eki ile aynı düzey (%41). Yeni beat'li 15 üretimin 9'u GPT.

**Testler:** `tests/test_pool_cleanup.py` (lint, kural, her yeni beat ayrı test: metin, kapı, her izinli kombinasyonda
yedek + son denetim, yakınlık, paraphrase, yanlış nesne; Notion alanı). Kilitli havuz testleri yeni havuzlara göre
güncellendi.

**Açık kararlar (Bahadır):** U10 kısaltma · çıkış bekleyenlerin yerine Parti 2 beat'leri · volkan uzunluk kaynaklı yedek
oranı · yeni ev beat'lerinde (U7-U11) "across the street" yok (kameranın evi gibi çizilme riski; U1'deki gibi eklenebilir).

**18 Eki, küçük düzeltme turu:** Parti 1'in 17 metni Bahadır'ın kısa metinleriyle değişti (≤16 kelime, anahtarlar aynı;
ev beat'lerinde "across the street" var, bombalar T7'de "rain" fiili yok). U9/U10 terimlerinden alev grubu çıktı (kısa
metinde yok). Yedeği sığmayan hariç çift: ateş hortumu 23 -> 1 (T6+U1: T6 19 + araç, U1 21 kelime), bombalar 7 -> 0, şok
dalgası 1 -> 0; çığ köyün 6 çifti (1. madde, değişmedi) duruyor. Ateş hortumunda T6 7, T7 8 farklı U ile eşleşir; U10
artık seçilebilir; ateş hortumu "aday kalmazsa 1'e düş" listesinden çıktı (3 derinlikte en kötü durumda 12 çift).
Volkan stil eki patlama ve bombalarda kısaldı (en uzun 106 -> 96 kelime; 96 + 75 + 3 = 174, kurallar ve 8 kısıt aynı;
`sk.VOLCANO_SHORT_CAMERA_EXCLUDED`: kül bulutu eski metinde, dokunulmadı). Lint: volkan beat'inde "rain" fiili HATA.
Kuru deneme (`scratch/dry_run_kisa_18eki.json`, 42 çağrı, ~0,20 $): ateş hortumu GPT 9/10, bombalar 8/10, şok dalgası
10/10 (17 Eki: 9/6/5).

**18 Eki (2): ateş hortumu şekli + Parti 2 + şok dalgası devre dışı** (Kie yok; kül bulutu, bombalar, eski gemi hattı
değişmedi):
- **Ateş hortumu şekli:** 3 kilit cümle "A colossal spinning fire tornado, a twisting funnel several times taller than the
  houses and trees, ..." (32-33 kelime, bütçe kendiliğinden 4-9s/9-15s 16 kelime). U1/U7/U8/U9 "column" -> "funnel"
  (U1 16 kelimeye kısaldı). Stil ekinde `sk.FIRE_TORNADO_SHAPE` ("visibly rotating funnel of flame with debris orbiting
  it, never a straight smoke plume or an explosion"); 175 için kamera cümlesi ve 2 balkon noktası kısaldı (en uzun ek
  96, en uzun prompt 174). Lint: ateş hortumu beat'inde column/plume/pillar/explosion/blast HATA
  (`es.FIRE_TOR_SHAPE_BANNED`). Yedeği sığmayan hariç çiftler T1+U2, T2+U2, T6+U2, T6+U6.
- **Parti 2:** 41 metinden 26'sı eklendi (yokuş M7-M9, yamaç S7, köy L7, sel D9, orman K7-K9 L7, cephe M7-M11, helikopter
  G7, karaya E7, marina Y7 Y8 Z7, cadde P7, deprem apartman Q5, eski sokak T5 T7, çığ orman E7 F7). 15'i eklenmedi
  (aynı dilimde aynı anlam 10, 16 kelimeyi aşan 3, deprem kilit kuralı 2: gömülme / balkon düşmesi): liste ve neden
  `tests/test_pool_cleanup.py` `PARTI2_NOT_ADDED`. Çıkış bekleyenlerin hepsi çıktı (yokuş M1 M2 M5, orman K3 K4 K6, cephe
  M1-M5, eski sokak T2, çığ orman E5); grandfather 31 -> 25. Cephe yangını `BEAT_BLOCK_FALLBACK_EVENTS`'e girdi.
- **Şok dalgası devre dışı:** `sk.DISABLED_EVENTS` (tek bayrak). Menüde ve otomatik seçimde yok; havuz, iskelet ve tüm
  testler duruyor. Açmak için kümeden çıkar. Volkan menüsü 2 olay: kül bulutu ve bombalar volkan seçimlerinin 1/2'sini
  alır (önce 1/3). Eski Telegram düğmeleri indeks bazlı: eski mesajdaki düğme kayabilir.
- **Kelime bütçesi satırı** Parti 2 olaylarına da (`es.BUDGET_EVENTS`: sel, yokuş, yamaç, köy, orman, cephe, helikopter,
  karaya, marina, cadde). Kuru denemede GPT toplamı 71-78 kelime yazıp yedeğe düşüyordu; satırla ikinci denemede 21/21 GPT.
- **Nesne kapısı (eş anlamlı ekleme):** deprem T1 "building", Q5 "upper levels/stories", ateş hortumu U1 nesnesi ev veya
  yanan çatı ("burning roof"; araç tavanı sayılmaz), yokuş M8 nesnesi ev (kamyon evin önüne; M7'ye benzetiliyordu).
- **Kuru deneme** (`scratch/dry_run_parti2_18eki.json` 70 üretim, `_2` 21, `_3` 12; toplam ~0,86 $ dahil yanlışlıkla
  başlayan 0,17 $): ilk koşu GPT 62/70, düzeltmeden sonra 31/33. Kalan yedek nedeni "0-4s insanlar kameraya yakın
  değil" (deprem, çığ orman, ateş hortumu); yakınlık kuralına dokunulmadı, karar Bahadır'da.

**18 Eki (3): bombalar ve kül bulutu ortam ekseni + yer ağırlığı + ışık** (Kie/GPT yok; kilit cümleler, havuzlar,
çiftler, hariç çiftler, kapılar aynı; şok dalgası devre dışı ve dokunulmadı):
- **Ortam** (`sk.VOLC_ENVS`, `es.choose_volc_env`): pastel kasaba caddesi "a street of colorful concrete houses with
  parked trucks" · Akdeniz tepe kasabası "a wide hillside-town street of stone and painted houses" · banliyö mahallesi
  "a suburban street of detached houses, garages and palm trees" · dağ eteği köyü "a village street of wooden and stone
  houses among trees" (≤10 kelime; A, B, D Bahadır'ın metninden kısaldı). Kamera cümlesinde "the village street" yerine
  ve GPT PLACE satırında; kilit cümleye girmez. Son 2 ortam tekrar etmez (olay başına süreç hafızası). Ağırlık: bombalar
  eşit, kül bulutu A=2 B=2 C=1 D=1. Onay: "Ortam: ..." satırı + Yer satırında "ortam: ..."; Notion "Ortam" select alanı
  (`ENV_PROPERTY`, ensure_schema seçenekleriyle ekler, ayrı istekle yazılır).
- **Yer ağırlığı** (`sk.VOLC_SPOT_KIND`): köy evi balkonu = balkon 2; çatı terası = çatı 1; yamaç terası = yamaç 1. Son
  yer arka arkaya gelmez (süreç hafızası + Notion combo_key). Yer metinleri aynı.
- **Işık** (`sk.VOLCANO_WEATHER_WEIGHTS`): bombalar eski metin 1, "warm orange dusk sky glowing from the eruption" 2,
  "pink-orange dawn light under a dark ash sky" 1, "dark night sky lit by glowing lava and fires" 1 (Bahadır'ınki 10
  kelimeydi). Kül bulutu eski metin 2, dusk 1, "bright hazy daylight under a dark ash sky" 1; gece yok. Işık sadece GPT
  WEATHER satırına gider (stil ekinde ışık satırı yok, kod yedeğinde ışık Kie'ye ulaşmaz).
- **175:** ortam stil ekini 6-7 kelime uzattı (en uzun: bombalar 103, kül bulutu 113). Kod yedeğiyle her kombinasyon
  sığıyor (en uzun bombalar 174, kül bulutu 173). Bahadır kararı: bu iki olay da `BUDGET_EVENTS`'te; GPT'ye söylenen toplam
  175 - stil eki - 3 (kül bulutu 59-69, bombalar 69-75; kapı aralığı 40-75 aynı). Ölçüm: eski GPT hikâyelerinin kül
  bulutunda 17'de 12-14'ü, bombalarda 24'te 3-5'i bütçesiz 175'i aşacaktı. Testler: `tests/test_volcano_env.py`.

---

## 📋 DEVİR: 🔥 Ateş hortumu ortam ekseni + 🧩 hibrit hikâye modu (16 Eki 2026)

**1) Ateş hortumu ortam ekseni** (commit "ateş hortumu: ortam ekseni"): hortum boş tarlada ilerliyordu. 3 ortam
(`es.FIRE_TOR_ENVS`: orman kenarı yerleşim, ağaçlık mahalle sokağı, köy kenarı), ortam başına kilit cümle (28-29 kelime,
ev + ağaç) ve 2 yüksek nokta; LRU son 2 (art arda aynı ortam yok). Açık arazi sözcüğü yok (testli). Yakınlık listesi
`_FIRE_TOR_NEAR` ("between the houses", "in the yard below"...; "road below" tek başına yakın değil). Stil eki 175 için
kısaldı (kurallar aynı), en uzun prompt 175. U1 (ev çatısı) kamera bir evin üstündeyken seçilmez (sadece köy yamaç
terası). Onayda "Ortam: ..." satırı. Beat'ler DEĞİŞMEDİ: U3 ahır, U4 çalı yığını, U5 "field" ortamla uyumsuz (karar bekliyor).

**2) Hibrit hikâye** (commit "hibrit hikâye modu"): yapılandırılmış hatta GPT en fazla 2 deneme
(`cp.STRUCTURED_MAX_ATTEMPTS`), geçemezse kod yedeği (`es.build_fallback`), üretim durmaz. Beat kapısı yumuşak:
ana nesne (`es.OBJECT_GROUPS`, araçlı beat'te araç adı) + "başka beat'e daha çok benziyor mu". Eski sıkı kapı sadece
raporda (`strict_beat_issues`). Yeni sert kurallar: çekim kelimesi, ülke/bölge adı, can kaybı. Onayda
"Hikâye: GPT (deneme N)" / "Hikâye: kod yedeği (neden: ...)". İstatistik `data/story_source_log.jsonl` →
`tools/fallback_report.py`. Eski hat (MAX_ATTEMPTS 3) ve Kie reddi sonrası yeniden yazım (3 deneme) değişmedi.
- Kalite garantisi `tests/test_story_fallback.py`: 30.254 kombinasyon (hava/ortam dahil 139.634) yedek prompt son
  denetimden geçer. Sığmayan 7 beat çifti `FALLBACK_GAPS`'te (bombalar R6+T5: 175 aşımı; çığ köy A2/A4/A5 × B2/B5: 70
  aşımı). Havuzdan çıkarılmadı; bu çiftlerde GPT de 2 kez kalırsa üretim durur. Karar Bahadır'da.
- 2i gerçek GPT kuru deneme (`scripts/dry_run_hybrid.py`): 3 $ sınırında durdu, 543 çağrı, 344 üretim (olay başına
  16-18). İlk denemede geçme eski kapı 119/344, yeni kapı 148/344. Yedeğe düşme 57/344 (%16,6). Baskın neden uzunluk
  (toplam kelime, 175 kelime), yakınlık; yumuşak kapı tek başına hiç yedeğe düşürmedi. %10 üstü olaylar ve gözlenen
  yumuşak kapı yanlış retleri (helikopter F5↔F1, deprem T2 "house after house") onay bekliyor; kapı gevşetilmedi.
  133 eski-kapı yanlış reddi `tests/fixtures/rejected_real.json`'a eklendi ("source" alanlı).
- Not: tek test dosyası başına koşunca `core.creative_pipeline` önce import edilirse döngüsel import hatası (HEAD'de de
  var); tam paket sırası yüzünden görünmüyor.

---

## 📋 DEVİR: 🔥 Ateş hortumu T3 kapısı + canlı ret dosyası (15 Eki 2026, dördüncü tur)

Canlıda 3 doğru T3 cümlesi reddedildi. Hepsi "yere iniş" grubuna takıldı: "crashes" tek başına sayılmıyordu, "crashing
down" listede yoktu. Biri ayrıca "kaldırma"ya takıldı ("engulfs").
- T3 artık araç + hortuma kapılma/kaldırma (`_FIRE_TOR_SWEPT`) + çarpma/iniş (`_FIRE_TOR_LANDING`); dönme şart değil.
- Yeni `beat_missing` + isteğe bağlı "unless" (sadece T3): ağaç ya da ters dönme geçen cümle T3 sayılmaz. Bu olmadan
  T1/T5'ten 8 cümle T3 sayılıyordu.
- Denetim (her T/U maddesine 4 GPT tarzı cümle): ilk ölçüm 1/48 ret (T3), düzeltmeden sonra 0. T3'e 8 yeni cümle: önce
  3/8 ret, sonra 0. Maddeler arası yanlış pozitif yok.
- **Canlı retler tek dosyada:** `tests/fixtures/rejected_real.json` (`test_rejected_real.py`). Yeni canlı ret görülünce
  oraya ekle. Doğru retler ("insanlar kameraya yakın değil") ayrı listede, ret sürmeli.
- Diğer olaylar HEAD ile aynı. En uzun prompt 174.

---

## 📋 DEVİR: 🔥 Ateş hortumu terim boşlukları (15 Eki 2026, üçüncü tur)

Denetimdeki boşluklar ateş hortumunda ölçüldü. Kaldırma ("picks up", "rises into the air", "carried aloft", "torn off the
road", "lifts") ve yana itme ("drives/forces sideways") zaten geçiyordu; testle kilitlendi. Eksik olan devirmeydi:
T5'e "knock(s/ed) over", U3'e "knock(s/ed) down/over" eklendi (`_FIRE_TOR_FLIP`, `_FIRE_TOR_WRECK`). Testler: 25 boşluk
cümlesi, maddeler arası yanlış pozitif, aynı fiillerle hortumsuz 9 cümle reddedilir. Diğer olaylar HEAD ile aynı. En uzun
prompt 174. Not: kapı olayı yapanı denetlemez (hortum olmadan "residents knock over ... burning shed" U3 sayılır).

---

## 📋 DEVİR: 🔥 Ateş hortumu büyüdü: dev hortum, yakın kamera, ön planda 2-3 kişi (15 Eki 2026, ikinci tur)

Sadece ateş hortumu; diğer olaylar aynı. Henüz video testi yok.
- Kilit cümle (26 kelime, ölçek kıyası): "A colossal fire tornado, several times taller than the tallest buildings and
  trees, tears across the burning roadside, its wide base engulfing a field of flames." Önceki 18 kelimeydi.
- Kamera (`fire_tornado_camera`): yüksek bakış, hortuma yakın; gövde karenin en az yarısı, tepe ve bulut kesilmez; önde
  2-3 kişi kaçar; el titremesi ve takip aynı, "eye level, normal lens" çıktı. Giyim/ışık kısa satır
  (`FIRE_TORNADO_GUARDRAILS`), kısıt 8 -> 7.
- Kişi 3-6 -> 2-3 (`NUMBER_WORDS`'e "two"); insanlar ön planda: çığdaki yakınlık kapısı (`slice_near_camera`) ve
  "near the railing or on the road right below" ipucu.
- Beat'ler en fazla 18 kelime ve hepsinde hortumun büyüklüğü var. Yeni hedefler: T2 cam -> ağaç gövdesi araca, T4 kor ->
  dev taban arkadan geçer, T5 korkuluk -> araç ters döner ve yanar, U3 tabela -> ahır, U5 çit -> odun yığını. Yeni
  yasak çift T2/U5 (yanan odun).
- 175 kelime: WORD BUDGET satırı (0-4s 10, 4-9s/9-15s 18, toplam 75) ve WORD_CAP_EVENTS'e eklendi. En uzun prompt
  kuramsal ve simülasyonda 174.
- Risk: kilit cümle 8 kelime uzadı; GPT bütçeyi aşarsa (eskiden 81/73 yazmıştı) 75 sınırına takılır.
- Havuz lint uyarısı 55 -> 52 (ateş hortumu 3 -> 0).

---

## 📋 DEVİR: 🔥 Ateş hortumu kapısı anlam bazlı + 75 kelime (15 Eki 2026)

**Olay:** 15 Eki 10:44 ateş hortumu (T6+U4) 3 denemede kapıdan geçmedi (Kie'ye gitmedi). İki sebep: GPT'nin doğru
T6/U4 cümleleri reddedildi ("collides ... skid ... halts", "engulfs ... ejecting"); 2. ve 3. deneme toplamı 81 ve 73
kelime (sınır 70).
- Ateş hortumu T1-T6/U1-U6 terimleri NESNE + EYLEM gruplarına çevrildi (`_FIRE_TOR_*`, sadece bu olay; orman, cephe,
  helikopter aynı). T maddelerinde araç grubu var (U cümleleri T sayılmasın). "spinning/whirling" hortumun sıfatı:
  T3 aşağı iniş, T6 enkaz + çarpma ister.
- Toplam 40-75 (sadece ateş hortumu). GPT'ye yeni satır yok: WORD BUDGET sadece çığ/deprem; 75 GPT'ye ret geri
  bildiriminde gider. En uzun prompt: simülasyonda 145, kuramsal en fazla 149 kelime (175 altı).
- Testler (`tests/test_fire_tornado_gate.py`): 6 gerçek ret geçer, 12 madde x 5 serbest + 3 kontrol cümlesi geçer,
  maddeler arası yanlış pozitif yok, 200 sahte üretim ilk denemede geçer.
- Salt okuma denetimi (her madde 5 serbest cümle, kod değişmedi): hiçbir olay %20'yi aşmadı. En yüksekler kıyı hortumu
  sahil caddesi 10/60, karaya vuruş 9/60, heyelan çamur 7/60. Ortak boşluklar: hortum kaldırma grubunda "picks up",
  "rises", "carried aloft", "torn off the road" yok; itme grubunda "drives/forces sideways" yok; devrilme gruplarında
  "knocks down/over" yok. Onay bekliyor, dokunulmadı.

---

## 📋 DEVİR: 🏚️ Deprem kapısı anlam bazlı (14 Eki 2026, ikinci tur)

**Ders:** simülasyon cümleleri madde metnine yakın olunca kapı fazla sıkı kalmıştı; gerçek GPT paraphrase'iyle test
edilmeli. 11:19 testinde 🧱 Eski sokak 3 denemede de "seçilen olay görünmüyor" kapısına takıldı (Kie'ye gitmedi). R3 ve
T2 için GPT'nin doğru ama serbest cümleleri reddedildi ("cascades down the street", "each house succumbing", "advances
... toward us").
- Deprem madde terimleri NESNE + EYLEM gruplarına çevrildi (`_EQ_FALLV`, `_EQ_MOVE`, `_EQ_DUST`, `_EQ_CHAIN`,
  `_EQ_PROGRESS`...); kelimesi kelimesine eşleşme yok. Örn. R3 = toz + akış eylemi; T2 = ev ev zincir + ilerleme.
  Sadece deprem; diğer kategorilerin kapıları ve 55 uyarı aynı.
- Testler: 6 reddedilen gerçek cümle (`REJECTED_REAL`) geçer; 16 maddenin her biri için madde metninden farklı 5 serbest
  cümle (`FREE`) geçer; bir maddenin cümlesi başka maddeden geçmez (yasak çiftler hariç: aynı görüntü bilerek iki
  dilimde yok); insan yakınlık kapısı aynı.
- Yanlış eşleşme düzeltmeleri: "face" tek başına yok ("facing" cephe sanılıyordu), "piece" yok ("in one piece" beton
  parçası sanılıyordu), "ripple" yok (genel ölçek küçültücü kuralına takılır).
- Serbest üsluplu simülasyon (5 farklı üslup, Kie/GPT yok): apartman 100/100, eski sokak 100/100 ilk denemede.

---

## 📋 DEVİR: 🏚️ Deprem kategorisi eklendi (14 Eki 2026, TASLAK, henüz video testi yok)

`earthquake_disasters` "🏚️ Deprem", 2 olay yapılandırılmış hatta, çığ yapısı birebir (kod havuzu, sabit yüksek kamera,
araçsız, 175 kelime kapısı, yasak kelimeler, ortam havuzu, yakınlık kapısı, havuz kontrolü):
🏢 Apartman bloğu çöküyor (`EARTHQUAKE_APARTMENT`, P1-P4 / Q1-Q4), 🧱 Eski sokak çöküyor (`EARTHQUAKE_OLD_STREET`, R1-R4 /
T1-T4). Kilit cümleler ve maddeler Bahadır'ın metni. Onaylı düzeltmeler: Q2 "...the upper floors of the apartment blocks
opposite cave in" (gömme fiili çıktı), R3 "...as the stone houses keep falling" (yapı teması), T2 "...toward us"
("camera" kelimesi hikâyede yasak).
- **Kurallar:** çöken bina her zaman konut; dükkan, kapı, kemer, ofis, cam/pencere, balkon düşmesi yok. Yasak
  (`earthquake_banned`): dead, bodies, victims, injured, blood, trapped, buried, rescue, casualties, araç/gemi, ülke ve
  şehir adları, yazı. Yavaşlatıcılar da yasak (bina ani ve hızlı çöker). İnsanlar 3-6, kameraya yakın (yakınlık kapısı).
  Giyim/ışık: "Bystanders wear everyday clothes; raw natural light, no hazmat suits." + "No readable signs, text or flags."
- **Kamera:** "Rooftop terrace of a building across the street" ("a rooftop terrace"), "High-floor balcony across the
  street" ("a high-floor balcony"). Bahadır'ın şablonu birebir (`earthquake_camera`). (*) maddeler P2, Q4, R1 sadece çatı
  terasında. Stil eki en fazla 95 kelime, prompt en fazla 167 (ölçülen), sınır 175. Hikâye 40-70.
- **Ortam** (`EQ_ENV_AXES`, deprem LRU'su çığdan ayrı): şehir, sokak, ışık + kamera noktası, son 2 elenir (aday kalmazsa
  birlikte 1, sonra 0). Uyum: apartman olayında beton/yamaç/cadde apartmanları, "narrow residential street" yok; eski
  sokakta tuğla-taş konutlar ve "a dense hillside neighbourhood of old stone houses" (benim ifadem: yamaç değerinin taş
  evlerle uyumlu hâli), "wide avenue" yok. "apartment blocks lining a wide avenue" sadece "tree-lined square edge" ile.
  "hazy dusty morning" seçilince şehir koyu tonlu yazılır (beyaz üstüne beyaz olmasın, `EQ_DARK_CITY`).
- **Yasak çiftler:** apartman (P3,Q1) (P3,Q4) komşu blok, (P1,Q2) toz dalgası; eski sokak (R2,T4) çatı, (R3,T1) toz,
  (R4,T3) moloz. İzinli çift (çatı / balkon): apartman 13/7, eski sokak 13/9.
- **Tekrar önleme 2**; apartmanda balkon noktasında 3 × 3 kalır ve kalan tek çift yasak çifte denk gelebilir, o durumda 1'e
  düşer (`BEAT_BLOCK_FALLBACK_EVENTS`, sadece deprem; diğer olaylarda davranış aynı).
- **Havuz kontrolü** depremde zorunlu; "floor", "storey", "slab", "block" sadece deprem için büyük nesne sayılır.
- **Simülasyon** (Kie/GPT yok, sahte GPT her maddenin 5 doğal cümlesinden rastgele yazar): 2 × 100 üretimin hepsi tamamlandı;
  175 aşımı 0, (*) ihlali 0, boş havuz 0, art arda aynı ortam 0, art arda aynı madde 0. Apartman 100/100 ilk denemede;
  eski sokak 94/100 (6 ret: örnek cümle 10 kelimenin altında, ikinci denemede geçti). Yedek derinlik (1) apartmanda 4 kez.
- **Notion:** kategori ya da olay için select alanı yok (olay metin, kombinasyon anahtarı metin); yeni şema seçeneği
  gerekmedi. Deprem kombinasyonları geçmişe sayılıyor (`MARITIME_INSPIRATION_DOMAINS`).

---

## 📋 DEVİR: ACİL: Notion Durum seçeneği eksikti, hiçbir üretim başlamadı (14 Eki 2026)

83b0d71'de "⚠️ Teslim edilemedi" koda (`USED_COMBO_STATUSES`) eklendi ama Notion "Durum" select'ine eklenmedi;
`get_used_combos` 400 validation_error ("select option ... not found") verdi, 10:12 çığ kayak üretimi başlamadan
durdu. Testler Notion'u sahte kullandığı için yakalamadı.
- **Ders:** yeni bir durum eklendiğinde `notion_logger.REQUIRED_STATUS_OPTIONS`'a da eklenmeli (ad -> renk).
  `ensure_schema` (bot açılışında) eksik seçeneği ekler; mevcut seçenekleri id/ad/renkleriyle aynen korur.
- **Savunma:** Durum filtreli sorgular (`_query_status_filtered`: get_used_combos, get_recent_history,
  get_recent_beat1_verbs) "seçenek yok" hatasında önce şemayı tamamlayıp yeniden dener, yine olmazsa o durumu
  filtreden çıkarıp uyarıyla devam eder. Ağ ve 5xx hatalarında davranış aynı (3 deneme, sonra durur).

---

## 📋 DEVİR: Telegram teslim güvencesi (14 Eki 2026)

**Olay:** 14 Eki 09:28 çığ köyü (A2+B5) Kie'de üretildi (task 4a81a741), Notion "✅ Tamamlandı" oldu ama video Telegram'a
gelmedi. **Kök neden (Railway logu):** `produce` sonundaki "🧪 TEST üretimi tamamlandı" mesajı Telegram'a bağlanırken
`httpx.ConnectError` ile düştü; hata yakalanmadığı için `deliver_video` hiç çalışmadı. Son 30 üretimde tek vaka. Video
kurtarıldı (mesaj 702), Notion'a File ID yazıldı.
- **1) Yeniden deneme:** `bot.tg_retry` / `safe_send`: ağ hatasında ilk denemeden sonra 2, 5, 10 sn arayla (BadRequest
  yeniden denenmez). Sonuç mesajı ve video ayrı korunur, biri diğerini kesmez. Üretim yolundaki tüm gönderimler
  (sonuç, hata, onay, iptal, puan, takip) bu yoldan. Onay mesajı gitmezse üretim iptal (görünmeyen onay beklenmez).
- **2) Kayıt ve açılış kurtarması:** video gitmezse Notion `⚠️ Teslim edilemedi` (`STATUS_UNDELIVERED`, LRU'da sayılır,
  panelde "Teslim edilemedi"). Açılışta son 24 saatin (açılıştan önce) videosu olup File ID'si boş kayıtları
  `redeliver_missing` arşivden ya da Kie linkinden "♻️ Kurtarıldı" notuyla gönderir; teslimde File ID yazılır, durum
  mod'a göre tamamlandıya döner. Tekilleştirme: File ID + `bot_data["delivered"]` + `redelivering`.
- **3) `/teslim` ve "🔁 Yeniden gönder":** son 15 günün teslim edilmemiş kayıtları; Kie'ye çağrı yok.
- **4) Zaman aşımı:** bağlantı 5 -> 20 sn (gönderim ve long polling), okuma 20, yazma 30, havuz 10.
- Not: Railway'de arşiv diski geçici; deploy sonrası kaynak Kie linki. `C:\DeepMyster_videolar` Railway'den görünmez.
- Bilinen risk: video yüklemesi TimedOut verip aslında gitmişse yeniden deneme aynı videoyu ikinci kez gönderebilir.

---

## 📋 DEVİR: ❄️ Çığ: yamaç kadraja girdi (14 Eki 2026, beşinci tur)

**Ders (14 Eki kayak testi):** yamaç kadrajda olmayınca çığ görünmedi; model çatıdan kayan kar çizdi. Kamera şablonu
düzeltildi: "...high vantage looking up a steep snowy slope where the avalanche is descending into the buildings just
below it; the slope and the avalanche fill the upper half of the frame, the nearest buildings and a corner of the
railing fill the lower half; ...". Kilit cümleler yamacı açıkça anıyor ("is already roaring down the steep slope / the
ski slope / through a pine forest into ..."), olay adı kapısı kendi başına geçiyor.
- Dağ ekseni: "wide rounded snowy highlands" -> "wide snowy highlands below a steep slope" (Bahadır'ın 10 kelimelik
  metni Setting 15 kelime sınırına hiç sığmıyordu; Bahadır kararıyla kısaltıldı).
- Stil eki en fazla 102 kelime. Bahadır kararı: çığ hikâye toplamı 40-75 -> 40-70 (70 + 3 etiket + 102 = 175).
  WORD BUDGET: 0-4s 6-10 kelime, 4-9s ve 9-15s kalanı eşit paylaşır (köy 15, kayak/orman 18).

---

## 📋 DEVİR: ❄️ Çığ: aksiyon ilk saniyeden + her üretimde farklı ortam (14 Eki 2026, dördüncü tur)

**Ders (14 Eki testleri):** köy (A5+B3) iyi çıktı ama kayak (C5+D6) ve köy videoları birbirinin aynısıydı (aynı balkon
korkuluğu, aynı yaklaşan bulut, aynı koşan insanlar). Çığ ilk ~10 sn yavaş yaklaştı, ilk temas 11. sn'de oldu.
**Şartlar:** aksiyon 0. saniyeden 15. saniyeye kesintisiz; her üretimde ortam farklı.

- **Kilit cümleler** "is already ..." (çığ ilk karede evlerin içinde): köy "...is already crashing into the first
  chalets of a village...", kayak "...is already slamming into a mountain lodge...", orman "...is already ripping
  through a pine forest and hitting the cabins at its edge...". Olay adı kapısı kendi başına geçiyor. İnsan yakınlık
  kapısı (`slice_near_camera`) aynen.
- **Kamera:** "high vantage looking at the avalanche crashing through the buildings just below" (yaklaşma yok).
  Giyim/ışık satırı "raw natural light" oldu (ışık artık ortamdan; "overcast daylight" güneşli günle çelişirdi).
- **Ortam havuzu** (`es.ENV_AXES`, `choose_environment`, `choose_env_spot`): dağ (4), yerleşim (5), ışık (5) ve kamera
  noktası. Her eksende son 2 üretimin değeri elenir (aday kalmazsa 1). LRU **kategori bazında** (köy, kayak, orman
  ortak) ve süreç hafızasında (Railway yeniden başlarsa sıfırlanır). Stil ekinde "Setting: dağ, yerleşim, ışık."
  (en fazla 15 kelime; daha uzun üçlüler seçilmez). GPT'ye WEATHER satırı olarak gider. Telegram onay mesajında ve
  Notion'da "Ortam: dağ = ... · yerleşim = ... · ışık = ... · kamera = ..." satırı.
- **Beat uyumu:** taş bina maddeleri (B1, C5, E3, E5, F3) seçilince "log cabins and a large lodge" elenir. Taş ahır (A4)
  ve istinat duvarı (B4) her yerleşimde olur.
- Stil eki en fazla 78 kelime, prompt en fazla 156 kelime. Ülke, şehir, bayrak, yazı sızıntısı testle yasak.
- **Yayılma planı** (aynı mekanizma, sırayla, her biri ayrı tur ve video testiyle): 1) heyelan, 2) yangın, 3) hortum,
  4) sel ve dev dalga (şehir görünümleriyle çakışmasın diye görünümlü olaylarda sadece ışık ekseni), 5) volkan en son.
  Her kategoride önce eksen değerleri Bahadır'dan, sonra beat uyumu ve kelime bütçesi kontrolü.

---

## 📋 DEVİR: ❄️ Çığ zayıf madde temizliği + havuz kontrol testi (14 Eki 2026, üçüncü tur)

14 Eki testinde A5 (ince direkler) çıktı. Kural (Bahadır): her madde kameraya yakın, BÜYÜK, KOYU ve kar bulutunda
kaybolmayan bir nesneye temas eder. 15 madde değişti (kimlikler aynı, metin Bahadır'ın): A1, A5, B1, B2, C1, C2, C3,
C4, C5, D5, D6, E2, E3, F2, F6. Teleferik maddesi kalmadı.
- **Kamera dışlamaları:** (*) çatı/kule/balkon sadece köy kenarı terasında: A3, A6, B2 (yeni), B3, D3, E6. C3 (teras
  döşemesi) teras noktalarında seçilmez, sadece balkonda (kamera kendi terasının söküldüğünü sanmasın). (†)
  teleferik kuralı `tests/test_pool_lint.py` içinde duruyor: teleferik kelimesi geçen kayak maddesi istasyon
  terasında dışlanmalı.
- **Yasak çiftler** (`excluded_pairs` yorumları): köy 10, kayak 11, orman 18. İzinli çift (köy kenarı terası / balkon /
  istasyon): köy 26/10, kayak 20/20/15, orman 18/12.
- **Tekrar önleme:** köy 3 -> 2, kayak 2, orman 2 -> 1 (balkonda E1/E2'nin tek eşi F4; daha derinde aday biter).
- **Havuz kontrolü** (`tests/test_pool_lint.py`): (a) büyük/koyu yapı nesnesi, (b) ilk nesne zayıf değil (direk,
  kablo, korkuluk, cam, tabela...), (c) gömülme fiili ana fiil değil. Çığda zorunlu; diğer kategorilerde sadece
  uyarı (14 Eki: 55 madde, değiştirilmedi).
- A5, B2, B5, E2 18 kelimeyi aşıyor; GPT WORD BUDGET ile kısaltıyor. Testte sahte GPT ret gelince kısa hâli yazar.

---

## 📋 DEVİR: ❄️ Çığ köy testi 3 denemede reddedildi, düzeltildi (14 Eki 2026, ikinci tur)

14 Eki 01:30 köy testi (A4+B5, balkon) hikâye kapısından 3 denemede de geçmedi. Üç sebep, üçü de düzeltildi:
- **Uzunluk:** GPT her denemede 40-75 toplamını aştı. Kamera cümlesi kısaldı (Bahadır'ın şablonu: "Handheld footage
  from {kısa yer}, high vantage looking up the slope as the avalanche rushes down onto the buildings just below; ...").
  Kısa yer adları: "a village-edge terrace", "a village-edge chalet balcony", "the lift station terrace". Stil eki en
  fazla 68 kelime; 75 kelimelik hikâye + 3 etiket + stil eki en fazla 146. GPT'ye `WORD BUDGET` satırı gidiyor
  (`es.word_budget_line`): 4-9s ve 9-15s en fazla 18 kelime, 0-4s kalan bütçe.
- **Olay adı kapısı:** köy kilit cümlesinde "village" yoktu. Cümleye eklendi ("...smashes into the village chalets
  right below the railing..."); GPT'deki "village street" ipucu kaldırıldı. Kayak ve orman kilit cümleleri kapıdan
  kendi başına geçiyor.
- **A4 false reject:** "crashes into a sturdy stone barn, sending its dark stones ricocheting" reddediliyordu. A4'e
  temas fiilleri eklendi (`_AVA_IMPACT`). 36 maddenin tamamı aynı kalıpla ("crashes into X, sending Y flying")
  tarandı; A3, A6, D3, E6 da reddediyordu, uçma fiilleri eklendi. GPT'nin 5 gerçek cümlesi ve tarama cümleleri
  `tests/test_avalanche.py` içinde sabit örnek.

---

## 📋 DEVİR: ❄️ Çığ ilk test dersi ve düzeltme (14 Eki 2026)

**Ders (13 Eki çığ köyü testi):** kamera aksiyona yakın olsun, ilk temas 0-2 sn'de olsun, nesneler büyük ve koyu olsun
(beyaz üstüne beyaz görünmez). Testte kamera vadinin karşısındaydı; çığ ve evler küçük kaldı, ilk ev ~5. sn'de
vuruldu, aksiyon beyaz bulutta kayboldu. Volkan bombalarında kamera yakındı, insanlar ve koyu nesneler ön plandaydı,
işe yaradı.

- **Kamera noktaları** köyün/tesisin kenarına taşındı: "Terrace at the edge of the village", "Balcony of a chalet at
  the edge of the village", "Terrace of the lift station" (aynı). Yeni tek şablon (Bahadır'ın metni): "...high vantage
  looking up the slope as the avalanche rushes down toward the buildings just below and beside the camera; the
  nearest buildings fill the middle of the frame, ... never descending, a corner of the railing in the foreground;
  ...". "across the valley" ve "avalanche always visible in the upper part of the frame" çıktı. Çatı/kule ve
  teleferik dışlamaları aynı.
- **Kilit cümleler** ilk teması içeriyor ("...smashes into the chalets right below the railing..."). Bahadır kararı:
  b kuralı (hikâyede "camera" yok) korunur; Bahadır'ın metnindeki "right below the camera" yerine "right below the
  railing".
- **Maddeler:** A4 taş ahır, B5 ve D1 büyük ahşap cephe, C6 koyu kütük yığını, D4 ahşap kiralama kulübesi. Yeni yasak
  çift (C6,D1). İzinli çift: köy 31/18, kayak 32/26/14, orman 26/20. Tekrar önleme aynı (köy 3, kayak ve orman 2).
- **İnsanlar ön planda:** 0-4s insan cümlesi yakın yer söyler (`slice_near_camera`: "near the railing", "in the street
  right below"...). GPT satırı: "...run away from the avalanche, close by: near the railing or in the street right
  below". Köyde "the village street" (yeni kilit cümlede "village" yok, olay adı kapısı için).
- En uzun prompt 175 kelime (köy, balkon, B5 ile).

---

## 📋 DEVİR: ❄️ Çığ kategorisi eklendi (13 Eki 2026, TASLAK, henüz video testi yok)

`avalanche_disasters` "❄️ Çığ", 3 olay yapılandırılmış hatta, volkan yapısı birebir (kod havuzu, sabit yüksek kamera,
araçsız, 175 kelime kapısı, olaya özel yasak kelimeler, danışman preflight):
🏔️ Çığ köyü yutuyor (`AVALANCHE_VILLAGE`, A1-A6 / B1-B6), ⛷️ Çığ kayak merkezine iniyor (`AVALANCHE_SKI`, C1-C6 /
D1-D6), 🌲 Çığ ormandan vadiye iniyor (`AVALANCHE_FOREST`, E1-E6 / F1-F6). Kilit cümleler ve maddeler Bahadır'ın metni
birebir. Lav dersi uygulandı: maddeler "gerçekte bunu yapar mı" kontrolünden geçmiş sayıldı (toz çığı 100+ km/sa,
ahşap yapıları söker).

- **Kamera:** "Hillside terrace", "Balcony of a mountain chalet", "Terrace of the lift station" (istasyon terası sadece
  kayakta). Çatı/kule maddeleri (A3, A6, B3, D3, E6) sadece yamaç terasında; teleferik maddeleri (C1, C5, D6) istasyon
  terasında seçilmez. Kamera cümlesi: "...high vantage looking across the valley toward the avalanche on the mountain
  slope; ... the camera stays fixed on the {terrace/balcony}, tilting down no more than slightly and never
  descending, the avalanche always visible in the upper part of the frame, a corner of the railing in the foreground;
  one continuous shot, no zoom, no cuts." Giyim/ışık: "Bystanders wear winter civilian clothes; raw natural overcast
  daylight, no hazmat suits." + "No readable signs, text or flags." (6 kısıt, stil eki 90 kelime).
- **Yasak çiftler** (aynı yapı sınıfı iki dilimde yok): köy (A2,B6) (A3,B3) (A4,B4) (A6,B1) (A6,B5); kayak (C1,D6)
  (C5,D6) (C2,D1); orman (E1,F1) (E1,F2) (E1,F3) (E1,F5) (E2,F3) (E3,F6) (E4,F1) (E4,F2) (E4,F5) (E5,F3). Yorumlarım:
  B3 çan kulesi A3 çatısıyla aynı sınıf (çatı/kule); B1 ön duvar ve B5 pencereler cephe; E6 kabin çatısı çatı sınıfı.
- **İzinli çift** (yamaç / balkon / istasyon): köy 31/18, kayak 33/27/15, orman 26/20.
- **Tekrar önleme:** köy standart 3; kayak ve orman 2 (talimat: aday kalmazsa 2). Sebep: kayakta istasyon terası
  (4 × 4 madde) ve ormanda balkon (10 yasak çift) 3 derinlikte en kötü durumda adaysız kalıyor (testli).
- **Yasak kelimeler** (GPT dilimleri, `EVENT_BANNED_WORDS`): rescue, helicopter, skier, snowmobile, vehicle, truck,
  car, cargo, tugboat, ship, boat, siren, text, sign, logo; yavaşlatıcılar slowly, gently, calm (+ calmly, gradually,
  softly, peacefully, benim eklemem).
- Testler: `tests/test_avalanche.py` (her madde tek başına + 5 doğal cümle, atmosfer reddi, yasak çift kuralı, kamera
  dışlamaları, 100 üretim simülasyonu, Telegram menüsü). 803 test yeşil.

## 📋 DEVİR: 🌋 Volkan kapandı (13 Eki 2026, dördüncü tur)

**Volkan 3 olay:** patlama şok dalgası, kül bulutu (piroklastik), volkan bombaları. **Lav nehri çıkarıldı.**
Gerekçe: 13 Eki'de lav nehri 4 testte de kabul edilmedi. Gerçek lav yürüme hızından yavaş ilerler ve evi saniyeler
içinde yıkmaz; Seedance lavı hızlandırıyor, ev yıkımı gerçek dışı çıkıyor. **Ders:** olay/madde yazarken "gerçekte
bunu yapar mı" kontrolü. Lav kodu silindi (menü, olay havuzu, kilit görsel, hız/çarpma kapıları, lav stil eki);
son hâli `event_structure.py` EVENT_BEATS üstündeki ARŞİV notunda, kod commit `d58330a`'da. Ortak kazanımlar
kaldı: sabit yüksek kamera (upper third, korkuluk), araçsız olay (`uses_vehicle`), 175 kelime kapısı, kısa giyim/ışık.

- **Havuzlar** (Bahadır'ın metni birebir; yeni maddeler büyük, yüksekten görünen, gerçekçi temas):
  patlama S1-S5 / U1-U6 (S4 ağaç+direk, S5 taş duvar; U4 ev cephesi, U5 çan kulesi, U6 bahçe duvarları + sac kulübe),
  kül bulutu P1-P6 / Q1-Q6 (P4 palmiyeler, P5 bahçe duvarı, P6 sac çatılar; Q4 istinat duvarı, Q5 dükkân binası
  cephesi, Q6 balkon + çatı döşemesi), bombalar R1-R6 / T1-T6 (R5 taş duvar, R6 ağaç; T5 yolda krater, T6 evin üst
  katı).
- **Bahadır kararları:** S6 ("roof tiles off the houses") S3 ile aynı nesne, eklenmedi. P4 P2 ile aynı nesne (ağaç)
  ama aynı dilimde, eklendi (çatı terası/balkonda seçeneği 3'ten 4'e çıkarır). U4 önerisi ("a wave of dust and
  rubble") atmosferikti; temaslı hâli girdi: "a second blast tears the front off a house across the street and the
  rubble spills into the road". Tekrar önleme: patlama ve bombalar standart 3; kül bulutu 2 (çatı maddeleri P3/P6/Q3/Q6
  çatı terası ve balkonda yok, orada 4 × 4 madde ve 8 yasak çift kalıyor, 3 derinlik adayı bitirir).
- **Yasak çiftler** (aynı yapı iki dilimde yok): patlama (S1,U3) (S2,U2) (S5,U6); kül bulutu (P1,Q1) (P1,Q6)
  (P3,Q3) (P3,Q6) (P6,Q3) (P6,Q6) (P5,Q1) (P5,Q4); bombalar (R1,T2) (R2,T2) (R3,T3) (R5,T6) (R6,T4).
- **Sayılar:** dilim başına madde patlama 5/6, kül bulutu 6/6, bombalar 6/6. İzinli çift (yamaç terası / çatı terası /
  balkon): patlama 27/21/21, kül bulutu 28/13/13, bombalar 31/25/25.
- Not: bombalarda R6+T5 kelimesi kelimesine yazılırsa balkon noktasında 178 kelime; GPT kapının geri bildirimiyle
  kısaltır. 791 test yeşil.

**🌋 Volkan düzeltmesi 3 (13 Eki, üçüncü tur):** lav Onay prompt'u 216 kelimeye uzamıştı. Volkan kamera cümlesi
tekrarsız şablona indi (eğilme ve "upper third" birer kez), lav hız cümlesi "The lava is thick, black-crusted and
tar-like, advancing at a slow walking pace." (suya benzetme yok), volkan giyim/ışık satırları kısa ifade (Bahadır
kararı, kısıt silinmedi), volkan prompt'u en fazla 175 kelime (`VOLC_MAX_PROMPT_WORDS`, aşarsa GPT'ye "kısalt";
lavda hikâyeye ~60 kelime kalıyor, uzun maddeler L1/L2/M1/M4 kısaltılarak yazılır), lavda crash/slam/smash/hurl/
blast/ram/plow yasak (`lava_no_impact`) ve insan cümlesinde fade/vanish/disappear gibi süs yasak
(`lava_people_visible`). 794 test yeşil.

## 📋 DEVİR: 🌋 Lav düzeltmesi 2: lav fiziği ve kamera (13 Eki 2026, ikinci tur)

**Gerekçe:** 13 Eki lav testinde lav su gibi hızlı yayıldı, sokağı birkaç saniyede kapladı (gerçek lav kalın kabuklu,
yürüme hızından yavaş). Kamera aşağı eğilip volkanı kadrajdan çıkardı, çekim drone gibi göründü. Ücretli çağrı yok.

- **Lav fiziği:** yavaş, kalın, temas dramı. Kilit görsel: "A thick lava front crawls down the volcano’s flank into a
  village street, setting the houses ahead of it alight." Havuz Bahadır'ın metni birebir: L1 taş duvarı itip üstünden
  geçer, L2 sıcaklık ağaçları tutuşturur, L3 ev köşesi şişip çöker, L4 çit + kulübe / M1 kapı ve pencereler patlar,
  M2 ev duvarı çöker, M3 dükkân, M4 bina katı. Yasak çiftler aynı: (L1,M2) (L1,M4) (L3,M1) (L3,M2) (L3,M4).
- **Hız kelimeleri yasak** (sadece lav, kilit görsel + havuz + GPT dilimleri, `lava_fast_words`): race, rush, surge,
  torrent, gush, flood, rapids, like water, wave, pour, stream (çekimleriyle). Önceki 3 kelimede lav yoksa insanlar
  için "race/rush" ("five people race away") ve alev/kıvılcım/duman için "pour/stream/gush/surge" ("flames and sparks
  pouring out", M4 metni) serbest. "slowly/gradually/steadily" yasağı kaldırıldı.
- **Lav stil eki:** kamera cümlesinden sonra "The lava is thick and crusted and advances slowly at a walking pace,
  never fast or fluid like water." 9. kısıt olurdu; Bahadır kararıyla sadece lavda "emergency responders wear service
  uniforms" çıktı (sahnede ekip yok). Lav eki 8 kısıt, en uzun prompt ~1340 karakter (sınır 1400).
- **Kamera ince ayarı (4 volkan olayı):** kamera cümlesine "the erupting volcano stays in the upper third of the frame,
  the camera tilts down no more than slightly, a corner of the {terrace/rooftop/balcony} railing stays visible in the
  foreground" eklendi (virgülle, kısıt sayısı değişmez). Diğer kategoriler aynı.
- Not: L2 metni 25 kelime (dilim sınırı 24); GPT kısaltıyor. M3 metninde "lava" yok ("the front"), M3 kapısı lav
  grubu aramıyor. Testler: `TestVolcanoCameraLava13Oct` genişledi; 791 test yeşil.

## 📋 DEVİR: 🌋 Volkan düzeltmesi (13 Eki 2026)

**Gerekçe:** 3 videoda stil ekindeki "the camera pans to follow the lava river / pyroclastic cloud" yüzünden Kie
kamerayı terastan sokak seviyesine indirdi; kamera olaydan kaçtı, ikinci yarıda yüksek açı kayboldu, bir videoda gizli
kesme oluştu. Bahadır yüksek kamera istiyor. Hiçbir Kie/GPT çağrısı yapılmadı; Bahadır Telegram'dan onayla deneyecek.

- **Kamera (4 volkan olayı):** pan-follow kaldırıldı. `skeleton_pipeline.volcano_camera`: "... standing {yer}, high
  vantage looking down over the village street toward the erupting volcano; slight hand shake, the camera stays fixed
  in place on the {terrace/rooftop/balcony} and never descends or moves closer to the ground, only tilts slightly, the
  erupting volcano always visible above the rooftops; one continuous shot, no zoom, no cuts." "facing the erupting
  volcano" CAMERA_SPOTS'tan bu cümleye taşındı; volkan artık CAMERA_MOTION_EXTRA'da yok. Kısıt sayısı 8 (aynı).
  Yangın, hortum, heyelan, kıyı dalga kamera satırları değişmedi (testli).
- **Lav nehri araçsız, sadece iki teras** (yamaç terası, çatı terası; köy evi balkonu bu olaydan çıktı, diğer volkan
  olaylarında kalır). Kilit görsel: "A lava river pours down the volcano’s flank and surges through a village street,
  engulfing the houses along it." Havuz: L1 taş duvar devrilir, L2 çit + kulübe ezilir, L3 ev köşesi çöker, L4 ağaçlar
  sökülür / M1 kapı ve pencerelerden girer, M2 ev duvarı çöker, M3 dükkân cephesi, M4 bina birinci katı patlar.
  Yasak çiftler (aynı yapı iki kez yok): (L1,M2) (L1,M4) (L3,M1) (L3,M2) (L3,M4). Kamera dışlaması kalmadı (çatı
  maddesi yok, balkon yok). GPT dilimlerinde araç, balkon ve "slowly/gradually/steadily" reddedilir
  (`EVENT_BANNED_WORDS`). Tekrar önleme derinliği 1 (aynı).
- **Kül bulutu** (kilit görsel aynı): P1 balkonlar sökülür, P2 ağaç + direk devrilir, P3 kiremit / Q1 ev duvarı çöker,
  Q2 blok pencereleri patlar, Q3 baca çatıyı deler. Tente, sandalye, çöp kutusu, araba camı çıktı (teras kamerasında
  seçilmiyordu). Yasak çiftler: (P3,Q3) (P1,Q1). P3 ve Q3 sadece yamaç terasında (çatı terası ve balkonda yok).
- **Araçsız olay (benim kararım):** havuzunda `{vehicle}` olmayan olayda (`uses_vehicle`: lav ve kül bulutu) araç
  seçilmez, GPT mesajında VEHICLE satırı yok, `EVENT_VEHICLES`'tan çıktılar. Kül bulutunda araç kelimesi yasak değil
  (sadece lavda istendi).
- Terimler: yeni `_VOLC_SHED/_DOOR/_FLOOR/_BALCONY/_CHIMNEY/_SLOW`; topple/crush/cave in/uproot/burst/buckle/ignite/
  swallow/sweep/collapse eklendi. `_VOLC_COLLAPSE` daraltıldı (çıplak fall/drop/burst yok, "kül evlerin üstüne yağıyor"
  Q1'den geçmesin). Kullanılmayan `_VOLC_FURN/_MELT/_ROW` silindi. Marina Z6 kelimeleri yine volkanda yok.
- Patlama ve bombalar: sadece kamera cümlesi değişti, havuz ve kilit cümle aynı.
- Testler: `TestVolcano` güncellendi, yeni `TestVolcanoCameraLava13Oct` (kamera, araçsız lav, yasak kelime kapısı,
  her madde tek başına + 5 doğal cümle, yasak çift kuralı, 100 üretim simülasyonu). 790 test yeşil.

## 📋 DEVİR: Panel video yedeği + YouTube token düzeltmesi (12 Eki)

**DURUM (doğrulandı):** Commit'ler `c3c0737`, `60333f8`, `efd7d5f`, `0cf70cf` canlı (Railway `44091d68` SUCCESS). 783 test.
- Panel videoları artık kalıcı: `scripts/video_backup.py` her Notion senkronunda videoları `C:\DeepMyster_videolar\<notion id>.mp4`
  olarak indirir (Telegram File ID, sonra Kie; ffprobe doğrulamalı). Elle kurtarılan 8 video `C:\DeepMyster_videolar_kurtarilan\`
  (dizin.json) de yerel kopya sayılır. 8 herkese açık YouTube videosu yt-dlp ile indi (girişsiz en iyi 480p).
- Panel iki sekme: Videolar 72 (oynatılabilir), Arşiv 44 (11 sadece YouTube gizli/erişilemez, 8 tamamen kayıp, 25 hata/iptal).
- Kie linki ~15 günde ölür; Railway'de volume yok. Gerçekten kayıp 8 video: 20 Eyl 07:21/07:35/07:50/07:54, 21 Eyl 14:24/16:42/23:37, 23 Eyl TEST.
- **YouTube OAuth uygulaması TESTING** ("7 Eki Production" kaydı yanlıştı). Token 7 günde ölür; son yenileme 7 Eki 21:31 ->
  **son geçerlilik 14 Eki 21:31**. Panel kartı geri sayım gösterir. Yayın açılmadan önce `refresh_youtube_token.bat`.

**TUZAKLAR:** `start_dashboard.bat` iki kez açılınca çift sunucu/döngü oluşur, ikinci sunucu port dolu diye kapanır (artık sebep
yazıp `pause` ediyor). Panel kodu değişince eski senkron döngüsü eski modülü hafızada tutar: yeniden başlat. Panel "eski görünüyorsa"
önce port 8771'de sunucu var mı bak.

**AÇIK (kullanıcının kararı):** Google Cloud'da OAuth uygulamasını Production'a almak; `ARBİTİRAJ KAMPI` içinde kalan 5,49 GB zip.

## 📋 DEVİR: Akşam kapanışı (10 Eki)

**Volkan canlı** (commit `d617a70`, deploy `0573b803` SUCCESS, bot TEST modunda).
- Volkan bombaları videosu test edildi, Bahadır beğendi (Bahadır'ın puanı 8,5/10).
- Lav nehri, patlama/şok dalgası ve kül bulutu henüz denenmedi; yarın denenecek.
- Gözlem 1: videoda gizli bir kamera kesmesi vardı (kareler arasında başka sokağa atlıyor), "no cuts" kısıtına
  rağmen. Tekrar ederse stil eki incelensin.
- Gözlem 2: tabela yazısı okunur gibi çıktı ("No readable signs, text or flags." tam tutmadı). Tekrar ederse not
  edilecek.
- Volkan havuzları küçük (dilim başına 3-4, bu yüzden olaya özel tekrar önleme derinliği var); videolar iyi çıkarsa
  6'ya çıkarılacak.

**Kuzey Denizi kategorisi (HENÜZ KODLANMAYACAK, sadece not):**
- Onaylı olaylar: balıkçı trawleri ("Dev dalga trawleri süpürüyor") ve açık deniz platformu ("Dev dalga platformu
  dövüyor"; riskli, denenip olmazsa çıkarılacak).
- Kesin dışlananlar: kargo gemisi, römorkör, feribot (mevcut feribot kategorisiyle çakışıyor).
- Karar bekleyen: üçüncü/dördüncü olay (fener ve araştırma gemisi önerildi).
- Havuz taslağı yarın Bahadır onayından sonra gelecek; talimat o zaman verilecek.
- Dikkat (kod öncesi karar gerekecek): 24 Eyl kargo temizliğinden beri `tests/test_cargo_free.py`, GPT'ye giden
  mesajlarda (kategori açıklaması, örnek öğeler, eski hattın senaryo mesajları) "trawler" kelimesini yasaklıyor ve
  gemi evreni (`VESSEL_UNIVERSE`) balıkçı teknesi içermiyor. Trawler olayı kodlanırken bu kilidin nasıl
  daraltılacağı (ya da teknenin nasıl adlandırılacağı) Bahadır'a sorulmalı.

**Bahadır'ın onayını bekleyen volkan kararları (d617a70):**
1. Tekrar önleme derinliği volkana özel (patlama 1, lav 1, bombalar 1, piroklastik 0; diğer olaylar 3): küçük
   havuzlarda genel 3 derinlik adayı bitirirdi. Alternatif: havuzları 6'ya çıkarmak.
2. Olay 1 düğmesi "🌋 Patlama şok dalgası camları kırıyor" (orijinal 48 karakter, Telegram sınırı 40).
3. Volkan bombalarında tek ve büyük taş kapısı: "barrage", "shower of rocks", "hail of", "pebble", "gravel" vb.
   reddediliyor; T1'deki çoğul büyük taşlar serbest. Yasak kelime listesi benim seçimim.

Railway boşta; bu not dışında kod değişikliği ve push yok.

---

## 📋 DEVİR: 🌋 Volkan kategorisi (10 Eki) + ZAYIF HİKÂYE YOK kuralı

**ZAYIF HİKÂYE YOK (Bahadır, 10 Eki; volkan için ve bundan sonraki her yeni kategori için BAĞLAYICI):** Her madde
(4-9s ve 9-15s) somut bir temas ya da yıkım içerir: bir şey bir şeye çarpar, kırar, devirir, yırtar, yutar ya da
tutuşturur. "Sütun büyüyor", "kül yağıyor", "gökyüzü kararıyor", "ışıklar sönüyor" gibi atmosfer maddeleri havuza
girmez. İki maddenin birlikte kurduğu hikâye de denetlenir: 4-9s ve 9-15s aynı nesneyi tekrar etmez, ikisi farklı
nesnelere temas eder; çakışan çiftler `excluded_pairs`'e girer. (Genel aksiyon/temas ilkesi aşağıda; bu kural onu
yeni kategoriler için bağlayıcı yapar.)

**Durum:** `volcano_disasters` "🌋 Volkan", 4 TASLAK olay yapılandırılmış hatta; yangın mimarisi (kilit cümle kodda,
araç kodda, GPT sadece cümle, 3 deneme, kapalı başarısızlık). Henüz video testi yapılmadı. Sebep ekranda görünür
(patlama, lav, kül bulutu, düşen taşlar) ve ağır kütle hareket eder (ders: süper hücre notu).

| Menü | Olay sabiti (İngilizce ad) | Havuz |
|---|---|---|
| 🌋 Patlama şok dalgası camları kırıyor | ERUPTION (Volcano erupts and a shockwave blows out windows) | S1-S3 / U1-U3 |
| 🌋 Lav nehri sokağı yutuyor | LAVA_RIVER (Lava river pours down into a village street) | L1-L4 / M1-M4 |
| 🌋 Kül bulutu köyü sarıyor | PYROCLASTIC (Pyroclastic cloud races down into a village street) | P1-P3 / Q1-Q3 |
| 🌋 Volkan bombaları çatıları deliyor | VOLCANIC_BOMBS (Volcanic bombs slam into a village street) | R1-R4 / T1-T4 |

- Olay 1 düğmesi ("Yanardağ patlıyor, şok dalgası camları kırıyor", 48 karakter) Telegram 40 karakter sınırı için
  kısaldı. U2 ve Q3 Bahadır'ın metni birebir (eski U2 "kül yağıyor", eski Q3 "kül gömüyor" atmosfer maddeleriydi).
- Kameralar (hepsi yüksek, dağa bakıyor): "Hillside terrace facing the erupting volcano", "Rooftop terrace facing the
  erupting volcano", "Balcony of a village house facing the erupting volcano". Stil ekinde kamera cümlesinin içinde
  ", the erupting volcano always visible above the rooftops" (CAMERA_MOTION_EXTRA, yeni kısıt sayılmaz); kamera
  takip nesnesi olaya göre ash column / lava river / pyroclastic cloud / glowing rocks. Hava "ash-grey sky lit orange
  by a distant eruption plume", kişi 3-6, toplam 40-75, NO_RAIN_EVENTS içinde, preflight danışman.
- 13 Eki: kamera cümlesi, lav ve kül bulutu havuzları değişti (yukarıdaki 13 Eki devri esas). Aşağısı 10 Eki hâli.
- Yasak eşleşmeler (aynı nesne iki kez): (S1,U3) dükkân cephesi, (S2,U2) araç camı; (L1,M1) (L2,M1) (L4,M1) araç,
  (L3,M2) duvar; (P2,Q2) araç, (P3,Q3) çatı; (R1,T2) (R2,T2) araç, (R3,T3) dükkân yangını.
- Kamera dışlamaları: çatı/kiremit maddeleri (S3, P3, Q3, T1) ve ev köşesi/çatı kirişi (M2) çatı terasında ve köy evi
  balkonunda; bahçe duvarı/avlu (L3) köy evi balkonunda seçilmez.
- Tekrar önleme derinliği: havuzlar küçük (dilim başına 3-4, kamera dışlamasıyla bazı noktalarda 2), genel 3 derinlik
  adayı bitirirdi. `RECENT_BEAT_BLOCK_BY_EVENT`: patlama 1, lav 1, bombalar 1, piroklastik 0 (sadece LRU); her
  noktada en kötü durumda aday kalıyor (testli). Diğer olaylar 3. Çeşitlilik için ileride havuzları 6'ya çıkarmak iyi
  olur.
- Volkan bombalarında taşlar tek tek ve büyük: "barrage", "shower of rocks", "hail of", "pebble", "gravel" vb.
  4-9s ve 9-15s'de reddedilir (`VOLC_SINGLE_ROCK_SLICES`, `_VOLC_SMALL_ROCKS`).
- Terim kapısı baştan geniş `_VOLC_*` listeleri; her madde 5 gerçekçi GPT cümlesiyle geçiyor, 8 atmosfer cümlesi
  hiçbir maddeden geçmiyor (`TestVolcano`). Marina Z6'ya özel kırma kelimeleri (obliterate, demolish, wreck...)
  volkan listelerine konmadı, Z6 kilidi aynen. P2 ve L2'ye araç grubu eklendi ("bulut gökyüzünü yutar" geçmesin).
- Not: P2 metni 8 kelime (10 altı); GPT dilimi 10-24'e tamamlıyor.

---

## 📋 DEVİR: ⛈️ Süper hücre fırtınası kategorisi tamamen kaldırıldı + DERS (Ekim 2026)

**Karar (Bahadır):** Süper hücre fırtınası kategorisi komple çıktı (dolu, düz hat rüzgârı/downburst, yıldırım,
otoyol). Gerekçe: bu kategoride yayınlanabilir tek video çıkmadı; dolu görünmeyen tanelerle, otoyol sebepsiz tır
devrilmesiyle zayıf çıktı, diğerleri beğenilmedi.

**DERS:** Seedance görünür sebebi ve ağır/hareketli kütlesi olan olayları iyi çiziyor. Görünmeyen sebepli olaylar
(rüzgâr-only, dolu taneleri) zayıf çıkıyor. Süper hücre kategorisi bu yüzden Ekim 2026'da tamamen kaldırıldı. Yeni
kategori önerirken önce "sebep ekranda görünüyor mu?" sorusu sorulur.

**Nasıl kaldırıldı:** Kod ve testler (`bot.py`, `dashboard.html`, `core/`, `tests/`), süper hücre eklenmeden önceki
commit `f5b7998`'deki haline döndürüldü (o tarihten sonra bu dosyalara sadece süper hücre commit'leri dokunmuştu:
`7e04996`, `80d76f8`, `86e241e`). Böylece menü, olaylar, havuzlar, `_STORM_*` listeleri ve eş anlamlı bloğu,
`STORM_WEATHER`, kamera noktaları, `supercell_storms` domain'i, EVENT_OUTCOMES/REQUIRED girdileri ve süper hücre
testleri gitti; marina Z6 kilit testi ilk haline döndü (storm hariç tutması yok). Aşağıdaki üç süper hücre devir
notu tarihçe olarak duruyor; içlerindeki terim kapısı kuralı ve GENEL İLKE (aksiyon/temas birinci planda) bütün
kategoriler için geçerli olmaya devam ediyor.

Notion'daki eski `supercell_storms` kayıtları evren dışı sayılır (`is_current_universe_combo`), seçim ve tekrar
önlemeye girmez; panel bu kayıtlarda kategori adını ham gösterir.

---

## 📋 DEVİR (ESKİ, KATEGORİ KALDIRILDI) — Süper hücre terim kapısı eş anlamlı genişletmesi + terim kapısı kuralı (10 Eki)

**TERİM KAPISI KURALI (Bahadır, 10 Eki):** Eş anlamlılar için sadece EKLEME yapılır, mevcut terim çıkarılmaz. GPT'nin
doğal anlatımı reddedilmemeli; sadece atmosfer (rüzgâr, gökyüzü, yağmur) anlatan cümleler ret almaya devam eder.
Çok kelimeli terimlerde çekim sadece son kelimeye uygulanır ("keel over" → "keels over" eşleşmez), diğer çekimler
ayrıca yazılır.

**Sebep:** Canlı testte dolu A2+B1 3 denemede reddedildi (para harcanmadı): GPT "obliterating shopfronts", "reducing
shop windows to shards", "obliterating shop windows" yazdı; B1 "9-15s: seçilen olay görünmüyor".

**Yapılan:** `core/event_structure.py` içinde `_STORM_PILEUP` tanımının hemen altındaki `+=` bloğu, süper hücre
`_STORM_*` listelerine eş anlamlı ekledi (obliterate, destroy, demolish, pulverize, annihilate, wreck, ravage,
devastate, rip/tear apart, blow/blast out, shard, rubble, gut, strip; dolu için barrage/onslaught/bombardment/pellet;
araç, ağaç, tabela, tel, devrilme, savrulma, takla, zincirleme kaza vb.). Diğer kategorilerin listelerine dokunulmadı.
- Test: `TestSupercellSynonyms`; 51 maddenin her biri 5 gerçekçi GPT cümlesiyle geçiyor (B1'de 6), canlıdaki üç B1
  cümlesi geçiyor (tam denetim dahil), 8 atmosfer cümlesi 51 maddenin hiçbirinden geçmiyor.
- `test_z6_break_group_only_marina` kilidi (obliterate, demolish, wreck, splinter... sadece marina Z6'da) süper hücre
  olaylarını kapsamıyor artık; diğer bütün olaylarda aynen geçerli. Marina listesi değişmedi.

---

## 📋 DEVİR (ESKİ, KATEGORİ KALDIRILDI) — Süper hücre havuzlarında zayıf maddeler değişti + GENEL İLKE (10 Eki)

**GENEL İLKE (Bahadır, 10 Eki):** Bütün kategorilerde aksiyon/temas birinci planda; atmosferik veya sakin maddeler
istenmiyor. Yeni havuz maddesi yazarken ve mevcutları gözden geçirirken bu esas alınır.

**Değişen 11 madde (Bahadır onaylı, metin birebir; eski metinler kodda yorum olarak duruyor):**
- Dolu: A6 "a hailstone punches through the roof of a parked car and its windows burst outward"; B3 "hail rips a
  shop awning loose and it tumbles down the street over the parked cars"; B4 "hail smashes through a skylight above a
  shop and glass rains onto the sidewalk below"; B6 "hail blasts the windows out of a parked bus and glass sprays
  across the road".
- Downburst: I3 "a heavy branch crashes onto the hood of the {vehicle} as it swerves"; J3 "a sheet of metal roofing
  slices down the street and slams into a parked car"; J4 "the wind rips a garage door off its frame and sends it
  skidding down the street".
- Yıldırım: X1 "a burning wire drops onto a parked car and flames leap across its hood"; X3 "a bolt hits a car roof
  in a burst of sparks and its windows blow out".
- Otoyol: S2 "a gust flips a car onto its roof and it slides along the asphalt"; S3 "a chain of cars slams into each
  other in the blowing rain and dust, one after another".

**Yeni yasak eşleşmeler (aynı nesne/eylem iki kez):** (A6,B5) park halindeki araba çatısı; (A4,B3) dükkân tentesi;
(I5,J3) caddeden uçan yassı parça (tabela / metal levha); (O1,X1) kopan tel aşağı düşer; (H7,S2) araç takla atıp ters
döner. Eski onaylı eşleşmeler duruyor; (H3,S2) yeni S2 ile gerekçesini yitirdi (karar Bahadır'da).

**Yeni kamera dışlamaları:** B4 (çatı penceresi) çatı terasında; J4 (garaj kapısı) tepe evi balkonunda. S2/S3
üstgeçide dokunmuyor, orada seçilebilir.

**Terimler:** yeni `_STORM_*` listeleri (_STORM_ROOF, _STORM_BUS, _STORM_BLAST, _STORM_HOOD, _STORM_METAL,
_STORM_SLICE, _STORM_GARAGE, _STORM_SKID_AWAY, _STORM_ROOF_FLIP, _STORM_PILEUP); artık kullanılmayan 9 fırtına listesi
silindi. Diğer kategorilerin listeleri değişmedi. I3'te araç kapısı geçerli. Yeni maddelerin hepsi 13-17 kelime;
10 kelime altında kalan onaylı maddeler: J2, O6, X6, H6, S5 (GPT dilimi 10-24'e tamamlıyor).

---

## 📋 DEVİR (ESKİ, KATEGORİ KALDIRILDI) — ⛈️ Süper hücre fırtınası kategorisi (10 Eki)

**Durum:** Yeni kategori `supercell_storms` "⛈️ Süper hücre fırtınası", 4 TASLAK olay yapılandırılmış hatta. Havuzlar
ve kameralar Bahadır onaylı, metin birebir. Henüz video testi yapılmadı. Bölge görünümü yok, araç `EVENT_VEHICLES`
(pickup truck, small car, white van, SUV), kaçan kişi 3-6 ("the storm"), toplam kelime 40-75 (olaya özel).
Hava `STORM_WEATHER` (yangından ayrı): a dark greenish-grey supercell sky with dramatic storm light / towering
supercell clouds and violent gusting wind / dramatic green-tinted light under a dark supercell.

| Menü | Olay sabiti (İngilizce ad) | Havuz |
|---|---|---|
| ⛈️ Dev dolu araç ve camları parçalıyor | HAIL (Giant hail pounds a street under a dark supercell) | A1-A6 / B1-B6 |
| ⛈️ Düz hat rüzgârı ağaçları deviriyor | DOWNBURST (Downburst slams into a tree-lined street) | I1-I7 / J1-J6 |
| ⛈️ Yıldırım trafoya çarpıyor | LIGHTNING (Lightning bolt slams into a transformer on a utility pole) | O1-O6 / X1-X6 |
| ⛈️ Fırtına otoyolda tırı deviriyor | STORM_HIGHWAY (Violent gust slams into a highway) | H1-H7 / S1-S6 |

- Menü etiketleri: Telegram butonu en fazla 40 karakter (test kilidi); "Dev dolu araçları ve camları parçalıyor" ve
  "Düz hat rüzgârı (downburst) ağaç ve direkleri devirip..." kısaltıldı.
- Otoyol olayının İngilizce adında ve kategori açıklamasında "truck" yok: kargo temizliği testi (test_cargo_free)
  eski hattın GPT mesajlarında truck/trailer/lorry'yi yasaklıyor. Kilit cümle ve havuzlar onaylı metinle birebir
  ("truck", "trailer" geçiyor; o test onları taramıyor).
- Kameralar (hepsi yüksek): olay 1-3 "Balcony of a high apartment across the street" (on a high balcony across the
  street, overlooking the street), "Rooftop terrace across the street" (on a rooftop terrace across the street),
  "Balcony of a hillside house over the street" (on a balcony of a hillside house overlooking the street); olay 4
  "Overpass above the highway" (on an overpass above the highway), "Balcony of a house above the highway" (on a high
  balcony of a house overlooking the highway). "Balcony of a hillside house" adı yangında başka kamera cümlesiyle
  kayıtlı olduğu için fırtına noktasının adı "... over the street" (kamera cümlesi onaylı metin).
- Kamera dışlamaları: J5 (bir evin çatı kiremitleri uçar) tepe evi balkonunda; H5 (otoyol tabelası kopar) üstgeçitte
  (tabelalar çoğu zaman üstgeçide asılı). Diğer maddeler kameranın durduğu yapıya dokunmuyor.
- Kapılar: yağmur/dolu/fırtına serbest (NO_RAIN_EVENTS dışı), araç havalanabilir (NO_LIFT_SLICE yok; I7, H7). 4-9s
  araç kapısı sadece `{vehicle}` geçen maddelerde. Terim listeleri yeni `_STORM_*`; mevcut listeler değişmedi.
  Preflight danışman.
- Not: bazı onaylı maddeler 10 kelimenin altında (ör. X6 "burning branches fall onto a parked car"); GPT dilimi
  10-24 kelimeye tamamlıyor (dilim kelime kapısı aynı).

---

## 📋 DEVİR: Yangın söndürme helikopteri eklendi (10 Eki)

**Durum:** 🔥 Yangın kategorisinin 4. olayı, TASLAK, yapılandırılmış hatta: `Firefighting helicopter drops water on the
flames racing toward a hillside neighborhood` (menü "🔥 Yangın söndürme helikopteri"). Havuzlar Bahadır onaylı,
birebir. Henüz video testi yapılmadı.
- Kilit cümle: "A firefighting helicopter swoops over a hillside neighborhood and drops a huge load of water onto the
  wall of flames racing toward the houses." (24 kelime). Havuzlar F1-F6 (4-9s), G1-G6 (9-15s); yasak eşleşmeler
  (F1,G3), (F2,G2), (F5,G3).
- Kamera: orman yangınının iki yüksek noktası ("Balcony of a hillside house", "Embankment above the village road"),
  alçak kamera yok. Hava `FIRE_WEATHER`, kaçan kişi 3-6 ("the flames"), toplam kelime 40-75 (olaya özel).
- Kamera evi dışlaması (balkon noktasında seçilmez): F2 (yanan çatılara su), F5 (yanan eve su duvarı), G4 (alev
  ıskalanan çatıya sıçrar). Bunun için `excluded_spots` artık 4-9s maddelerini de kabul ediyor; mevcut olayların
  tüm dışlamaları 9-15s'de olduğu için onlarda değişiklik yok.
- Araç sadece F3 ve F6'da geçiyor: 4-9s araç kapısı artık seçilen maddenin metninde `{vehicle}` varsa zorunlu
  (mevcut tüm olayların 4-9s maddelerinde var, davranış aynı). `NO_LIFT_SLICE` bu olayda da 4-9s'de geçerli.
- Yağmur kapısı: bu olayda ıslaklığın sebebi helikopterin suyu. `WATER_DROP_EVENTS`: wet, soak, drench, damp,
  puddle serbest; "rain" fiili suyla birlikte serbest ("water rains down"); yağış (heavy rain, downpour, rainfall,
  rain-soaked, rainy...) yine reddedilir. Diğer yangın olaylarında kapı değişmedi.
- Terim listeleri yeni `_FIRE_*` (_FIRE_WATER, _FIRE_STEAM, _FIRE_HELI, _FIRE_DROP, _FIRE_DOUSE, _FIRE_DOWNDRAFT
  ...); mevcut listeler değişmedi. Preflight bu olayda da danışman.

**Gözlemler (karar Bahadır'da, kod yok):**
- Orman yangını videosunda alev, yerde yakıt varmış gibi evlerin önünde birden her yeri tutuşturuyor (Bahadır
  gözlemi). Orman testlerinde tekrar ederse havuz/kilit cümle ayarı düşünülecek.
- Karaya vurmanın 3 kamerası hâlâ yer seviyesinde; onaylı, değişmedi.

---

## 📋 DEVİR: Preflight danışman, yeniden yazım kaydı, orman 75 kelime, hortum cadde balkonu (10 Eki)

**Preflight (sadece yapılandırılmış hat: sel, tidal, 3 heyelan, 3 hortum, 3 yangın).** Preflight artık danışman:
riskli dese de senaryo kodun ürettiği haliyle kalır, yeniden yazılmaz, `StructuredRejectError` ile durulmaz
(`infrastructure/kie_client.py`, `create_video` KATMAN 1; meta'da `advisory`/`risky`). Riskliyse (safe=false ve
puan 5+) "⚠️ Preflight riski X/10: <sebep>" satırı ✋ Onay mesajına ve Notion gövdesine (`format_final_prompt`),
Notion "Güvenlik" alanına ("Pre-flight: riskli (danışman, senaryo değişmedi)") ve Telegram sonuç mesajına (YAYIN
dahil, `result["preflight_warning"]`) yazılır. Değişmeyenler: serbest hat (feribot, tersane, marina, kruvaziyer,
plaj) preflight'ın yeniden yazdığı hikâyeyi eskisi gibi kullanır; preflight çökerse (`PreflightError`) üretim durur;
Kie'nin gerçek reddinden sonraki tek yapılandırılmış yeniden yazım aynı. Kaynak: 8 Eki yangında 3 durma (puan
6-8/10, sebepler "people in peril", "children if any are minors" gibi metinde olmayan varsayımlar; preflight sabit
kilit cümledeki "burning" kelimesini de siliyordu).

**Yeniden yazım kaydı.** Kie reddi sonrası yapılandırılmış yeniden yazımın tüm denemeleri (tam dilim metni, kapı
retleri, sebep, sonuç) başarılı da olsa başarısız da olsa Notion gövdesine "🔁 Yapılandırılmış yeniden yazım
denemeleri" bölümü olarak yazılır (`structure["rewrite_log"]`, `format_rewrite_attempts`). Not: ilk yazımın 3
denemede de kaldığı üretimlerde (ör. 8 Eki K4+L2) Notion kaydı açılmıyor, ayrıntı sadece Telegram'da.

**Orman yangını.** `TOTAL_WORDS_BY_EVENT` içinde 40-75 (marina gibi olaya özel); cephe ve ateş hortumu dahil diğer
tüm olaylar 40-70. `_FIRE_FLAME`'e fiery, aflame, smolder, smoulder; `_FIRE_SWERVE`'e maneuver, manoeuvre, evade,
sidestep, careen, zigzag eklendi (sadece ekleme; 8 Eki K4 retleri "fiery", "maneuvers").

**Hortum cadde (Tornado sweeps down a coastal avenue).** Kamera yüksek balkonda: "High balcony over a downtown
avenue" ve "High balcony over a high-rise avenue" (on a high balcony across the street, overlooking the avenue),
"Upper-floor balcony over a residential avenue" (on an upper-floor balcony across the street, overlooking the
avenue). Yer metinleri aynı. Eski üç nokta (Downtown city center, Residential coastal district, High-rise coastal
city) caddenin listesinden çıktı, tablolarda kalıyor (sel ve karaya vurma kullanıyor). Q5 dışlaması kalktı (kamera
artık kaldırımda değil). Karaya vurma, marina ve plaj kameraları değişmedi; karaya vurmanın üç noktası hâlâ yer
seviyesinde (karar Bahadır'da). Stil ekindeki "eye level" yüksek noktalarla çelişiyor, bilerek dokunulmadı.

**Kanıt:** 735 test; sel, tidal, 3 heyelan, karaya vurma, marina, cephe yangını ve ateş hortumu için mesaj, stil eki
ve prompt bayt bayt aynı (cephe ve ateş hortumunda sadece terim genişlemesinin denetim etkisi kontrol edildi).
Ücretli çağrı yapılmadı.

---

## 📋 DEVİR: Yangın devir notu (8 Eki)

**Durum:** Yeni kategori 🔥 Yangın (`fire_disasters`), 3 TASLAK olay yapılandırılmış hatta (commit `338e575`, kamera
düzeltmesi bu notla aynı commit'te). Bölge görünümü yok, araç `EVENT_VEHICLES` (pickup truck, small car, white van,
SUV), kaçan kişi 3-6 (`EVENT_COUNT`). Henüz video testi yapılmadı.

**Olaylar ve kilit cümleler (Bahadır'ın metni birebir):**
- 🔥 Orman yangını mahalleye ulaşır (`Wall of flames sweeps into a hillside neighborhood`): "A towering wall of flames
  sweeps down the forested slope and slams into the edge of the neighborhood, igniting roofs and trees." Havuz K1-K6 /
  L1-L6, kaçış "the flames".
- 🔥 Apartman cephe yangını (`Flames race up a tower facade`): "Flames race up the glass facade of a tower, blowing out
  windows and raining burning debris onto the street." Havuz M1-M6 / N1-N6, kaçış "the flames".
- 🔥 Ateş hortumu (`Fire tornado tears across a burning roadside`): "A violent fire tornado tears across a burning
  roadside, hurling flames, burning branches and embers across the road." Havuz T1-T6 / U1-U6, kaçış "the fire
  tornado".

**Kamera noktaları (hepsi yüksek; nokta = ortam anahtarı, Bahadır'ın ortam tarifi PLACE metninde):**
- Orman yangını: "Balcony of a hillside house" (on a balcony of a hillside house overlooking the street and the
  burning slope), "Embankment above the village road" (on a roadside embankment above the village road). PLACE: a
  hillside village neighborhood. L1 ve L5 balkon noktasında seçilmez (kameranın durduğu ev).
- Cephe yangını: "Balcony across from a downtown tower" ve "Balcony across from a coastal high-rise" (on a high
  balcony across the street from the tower); "Rooftop terrace across from a downtown tower" ve "Rooftop terrace
  across from a coastal high-rise" (on a rooftop terrace across the street from the tower). PLACE: the downtown city
  center / a high-rise coastal city. Kaldırım noktaları 8 Eki'de çıktı.
- Ateş hortumu: "Overlook above the burning valley road" (on a roadside overlook above the burning valley road),
  "Balcony of a roadside house" (on a high balcony of a roadside house overlooking the road). PLACE: a burning
  valley road. U1 balkon noktasında seçilmez.

**Hava havuzu (`FIRE_WEATHER`):** hot dry wind and thick smoke haze / gusty dry wind under an orange smoky sky /
heavy smoke and scorching still air.

**Kapılar (sadece yangın olayları, `core/event_structure.py`):**
- Yağmur/ıslaklık yasağı (`rain_words`): hikâyede (kilit cümle dahil) ve stil ekinde yağış anlamındaki "rain",
  wet, soaked, drenched, rain-soaked, downpour, puddle vb. geçerse ret.
- Kural: "rain" fiili yanan ya da düşen bir nesneyle (±3 kelime: ember, spark, debris, glass, burning, flaming...)
  birlikte geçerse serbesttir ("embers rain onto", "raining burning debris": Bahadır'ın kendi metinleri).
- Uçma yasağı (`NO_LIFT_SLICE`): orman ve cephe yangınında 4-9s'de araç havalanırsa (lift, airborne, off the ground,
  swept up...) ret. Ateş hortumunda araç havalanır (T1, T3).
- Terim listeleri yangına özel (`_FIRE_*`); alev bir şeye değmeli, sadece rüzgâr anlatımı geçmez. "rush" kaçış
  sayılmaz (mevcut `_FLEE`).

**Gözlem:** Genel 40-70 kelime sınırı orman yangınında sık 2.-3. denemeye itiyordu (kilit cümle 22 kelime; ilk kuru
provada 6 hikâyenin 3'ü sınır yüzünden en az bir kez reddedildi, hepsi 3 denemede geçti). 10 Eki: orman 40-75
oldu (yukarıdaki 10 Eki notu); cephe ve ateş hortumu 40-70.

**Bekleyen iş:** ~~4. olay "Yangın söndürme helikopteri alev duvarına su bırakır", ilk yangın testi geçince
eklenecek.~~ 10 Eki: eklendi (yukarıdaki helikopter notu).

---

## 📋 DEVİR — Hortum devir notu (4 Eki)

**KURAL (Bahadır, bağlayıcı):** Olay ya da kategori çıkarılmaz, başka bir şeyle değiştirilmez; karar verilen olay
çalışana kadar iyileştirilir. Tüm düzeltmeler kodda yapılır (havuz, kilit cümle, sınır); GPT'ye yeni kural eklenmez.
Olay bazlı sınırlar diğer olayları etkilememeli.

**Hortum yapılandırılmış hatta (3 olay, görünüm yok, araç `EVENT_VEHICLES`, kaçan kişi N 3-6).** Menüden çıkanlar
(kod silinmedi, `REMOVED_EVENTS`): "Tornado approaching coastline", "Tornado rain bands and flying debris lash the
waterfront". Plajdaki "Tornado approaching an open beach" dokunulmadı.

- **Karaya vurma (Tornado making landfall) — ONAYLI.** Kodda kilit cümle ("A violent tornado makes landfall on the
  waterfront, tearing roofs and signs into the air."), C1–C6 / E1–E6 havuzları.
- **Marina (Tornado crosses a marina quay) — yeniden tasarlandı, commit `efb4115` canlıda.**
  - Kilit cümle: "A violent tornado tears in from the sea onto the marina quay, ripping palms and umbrellas off the
    ground."
  - Kamera noktası "High marina balcony" ("on a high balcony overlooking the marina and quay"); olayın tek noktası.
    "Marina berthing pier" kamera tablosunda ve hortum ortam listesinde duruyor.
  - Havuzlar: Y1–Y6 (araç), Z1–Z6 (hortum temaslı rıhtım/kafe/kiosk/ofis/dükkân sahneleri; yat ve direk sahneleri
    çıkarıldı). Dışlamalar: (Y5,Z5), (Y4,Z5).
  - Toplam kelime: marinaya özel `TOTAL_WORDS_BY_EVENT` 40–75; diğer tüm olaylar genel `TOTAL_WORDS` 40–70.
  - `_CRASH_DOWN`'a "collapse"; hortuma özel `_TORNADO_RIP` listesi ("dislodge" dahil); Z6 kırılma grubu genişletildi
    (annihilate, splinter, obliterate, demolish, wreck, wreak, rupture, pulverize, tear apart, blow apart).
  - Yeni tasarımın ilk üretimi Kie kredisi bittiği için (402 Credits insufficient) video üretemedi, tasarım henüz
    DENENMEDİ. Yarın Kie kredisi yüklendikten sonra aynı Onay metniyle yeniden denenecek. Olay menüde kalıyor,
    çıkarılmayacak.
- **Cadde (Tornado sweeps down a coastal avenue):** P4 düzeltmesi ("a falling palm tree crashes onto the {vehicle},
  crushing its roof") canlıda (`41747ba`). Yeni video henüz üretilmedi, yarın test edilecek.

**Açık gözlemler (karar Bahadır'da, kod yok):**
- Y1 "sideways" şartı fazla katı: GPT "skidding across the quay" yazınca reddediyor.
- Eski iskelet metninde (`skeleton_pipeline.py`) hâlâ "bending masts and ripping covers off the moored yachts" duruyor
  (aktif creative hatta kullanılmıyor, sadece `PROMPT_PIPELINE=skeleton`).
- Y2: "winds tip" gibi sadece-rüzgâr anlatımlarına dikkat.
- 70 kelime toplam sınırı hikâyeleri sık reddediyor (marina için 75 yapıldı).

**Sıradaki:** Önce Kie kredisi yüklenmeli (marina ve cadde testleri için). Marina tekrar test, cadde testi, sonra plaj ("Tornado approaching an open beach" olduğu gibi),
kruvaziyer + marina kategorisi, tersane, feribot. ~~YouTube OAuth token yenileme: 6 Ekim gecesine kadar.~~
(7 Eki: uygulama Production'a geçti, haftalık yenileme yok; bkz. GÜNCEL DURUM "YouTube OAuth Token".) (12 Eki düzeltme: YANLIŞ, uygulama hâlâ Testing, haftalık yenileme gerekli.)

**Not:** Push her zaman `git push origin HEAD:main` (yerel dal `master`). Kuru provalar `scripts/dry_run_full.py`
ile; olay çifti zorlamak için oturumlarda geçici bir sarmalayıcı kullanıldı (repoda yok).

---

## 📋 DEVİR (ESKİ) — Heyelan: yapılandırılmış hat (2026-10-04 kapanışı)

**DURUM — doğrulanan:** commit `5c9ca3d`, Railway deploy `9383ff44` SUCCESS (CI'ı bekledi), bot TEST modunda açıldı.
687 test. Heyelanın 3 olayı (`Mudslide pours down a hillside street`, `Rain-soaked slope collapses onto a roadside`,
`Mud and debris torrent tears through a hillside village`) yapılandırılmış hatta canlı. Yapılandırılmış olaylar artık:
sel, kıyı dev dalga, heyelan (3).
- Kilit cümleler `EVENT_KEY_VISUAL`'da; 4-9s H1–H6 / R1–R6 / K1–K6, 9-15s M1–M6 / S1–S6 / L1–L6. `EVENT_REQUIRED`
  bu üç olayda `[]` (kilit cümleler tetik ve olay adı kurallarından grupsuz geçiyor).
- Kaçan kişi sayısı 3-6 (`EVENT_COUNT`), kod seçer, GPT'ye kelimeyle gider ("... run away from the mud").
- Bölge görünümü yok: araç olaya özel listeden (`EVENT_VEHICLES`); combo_key yer parçası `spot##H3+M1` (görünüm
  boş, "None" yazılmaz); ayrıntıda "Görünüm" satırı yok.
- Kamera noktası dışlamaları: S1 (korkuluk kopar) "Behind the guardrail of a hillside road" spotunda yok; L1 (ev
  köşesi çöker) "Upper-floor balcony of a village house" spotunda yok (kamera o yapının üstünde).
- H6/R6 için heyelana özel `_TOGETHER_LANDSLIDE` ("the car behind it", "trailing", "following"); sel/tidal ortak
  `_TOGETHER` listesi değişmedi.

**Test videoları (Bahadır değerlendirmesi):** çamur seli (H1+M3) iyi, 3 kesme; yamaç çökmesi (R2+S4) çok iyi, tek
çekim; köy (K4+L3) iyi, ağaç yuvarlanmıyor, kesmeler var.

**Açık gözlemler (karar Bahadır'da, kod yok):**
- 70 kelime toplam sınırı çamur selinde sık ret nedeni (kilit cümle 21 kelime; 3. denemeye gidiyor).
- "the car behind it" kalıbı katı ("the sedan behind it", "joined by the car behind" reddedildi).
- S5 fiil grubu dar ("crumbles", "cascades", "spills" yok).
- Araç havalanması: GPT kendi "lifted" yazabiliyor.
- Seedance kesme yapabiliyor.
- L3 (ağaç yuvarlanır) zayıf çiziliyor.

**Fikir (karar yok):** İleride farklı kamera açılarıyla üretim denenebilir; spot listesi veri olduğu için geri dönüş
kolay. Yeni açıda kameranın durduğu yapıyı çökerten maddeler `excluded_spots` ile dışlanmalı.

**Sıradaki:** hortum + plaj, sonra kruvaziyer + marina, tersane, feribot.

**Not:** Push her zaman `git push origin HEAD:main` (yerel dal `master`). `.git/worktrees/yt_head_wt` boş kalıntı
klasörü OneDrive kilidi yüzünden silinemiyor; commit'lerde "Permission denied" uyarısı verir, işleve etkisi yok.

---

## 📋 DEVİR (ESKİ) — Kıyı dev dalga: yapılandırılmış hat (2026-10-04 kapanışı)

**DURUM — doğrulanan:** commit `0592fe6`, Railway deploy `4129f174` SUCCESS (CI'ı bekledi), bot açıldı. 675 test.
Yapılandırılmış hat (kilit cümle + havuzlar + Kie öncesi son denetim) artık sel VE kıyı dev dalgada canlı.
- Kilit cümle: "A towering brown tidal wave thick with debris crashes over the waterfront onto the coastal street."
- 4-9s T1–T8 (araç), 9-15s W1–W8 (yıkım); 5 yasak eşleşme. W6 (alçak duvar) "Coastal avenue behind a seawall"
  spotunda yok: kamera seawall'un üstünde duruyor. T2 "carried down the street by the surge" (araç havalanmaz).
- Kaçan kişi sayısı N (3-6) kodla seçilir, GPT'ye kelimeyle verilir ("PEOPLE RUNNING AWAY: five ..."); slice_1_rest'te
  N'in kelimesi ve kaçış fiili zorunlu (`SLICE_RULES`). "rush" kaçış listesinde YOK (su da "rushes").
- Birikimli geri bildirim (sadece `SLICE_RULES` olan olaylar): önceki tüm ret nedenleri tek listede gider. Sel aynı.
- Kuru prova (GPT, Kie yok): 6/6 geçti, 4'ü ilk denemede.

**Test videoları (Bahadır değerlendirmesi):** 6 video (Körfez, Riviera, Kuzey Afrika, ABD x2, Doğu Asya): 4 çok iyi,
1 iyi, 1 orta (Riviera, otobüs).

**Açık gözlemler (karar Bahadır'da, kod yok):**
- Araç, GPT'nin kendi yazdığı "lifts" ile havalanabiliyor (yasak kelime kapısı bilerek eklenmedi).
- W5 (otobüs) zayıf kalabilir.
- Seedance bazen kesme yapıyor.
- Dalga 3-5 sn'de duman gibi görünebiliyor.

**Silinecek ölü kod (sistem oturunca ayrı tur, onayla; şimdi SİLİNMEZ):**
1. `EVENT_SKELETONS[...]["text"]` (sel ve kıyı dev dalga): creative hatta kullanılmıyor, sadece `PROMPT_PIPELINE=skeleton`.
2. `EVENT_REQUIRED` içindeki "Eski: [...]" yorum satırları (sel, kıyı dev dalga).
3. `write_story` / `_message` / `CREATIVE_SYSTEM`: bu iki olay girmiyor; diğer olaylar kullandığı için sadece bu iki
   olaya özel parçalar.
4. `main.before_submit` içindeki `if not structure and ...` kural kapısı dalı: bu iki olay için çalışmıyor.
5. `core/creative_engine.py` legacy havuzundaki kıyı dev dalga satırı (sadece `PROMPT_PIPELINE=legacy`).
Not: `EVENT_OUTCOMES` ölü değil (yapılandırılmış hattın ayrıntısında "outcome" olarak yazılıyor).

**Sıradaki:** Heyelan yapılandırılmış hatta taşınacak, sonra hortum/plaj, kruvaziyer/marina, tersane, feribot.

**Not:** Yerel dal `master`, GitHub dalı `main`. Push her zaman `git push origin HEAD:main`. GitHub'da yanlışlıkla
açılmış `master` dalı duruyor (silme Bahadır'da).

---

## 📋 DEVİR (ESKİ) — Şehir sel: yapılandırılmış hat (2026-10-04 kapanışı)

**DEĞİŞMEZLER (Bahadır kararı, bağlayıcı):**
- 15 saniyenin altında video yok (`config.py` açılışta kilitler). Üretim `seedance-2-fast`, 480p, 15 sn; Kling
  denendi ve elendi (su duvarı durdu, son saniyeler boş), Kling desteği eklenmeyecek.
- Hedef "bizim sistemimizden sıfır hata": hiçbir yerde sessiz yedek yok, şüphede Kie'ye istek gitmez.
- Onaylı bir değerden/davranıştan sapmadan önce Bahadır'a sorulur (gerekçe + ölçümle).
- Kie çağrısı yalnızca Bahadır'ın açık onayıyla. Ölü kod temizliği ayrı turda, onayla.

**DURUM — doğrulanan:** commit `86d93e5`, CI yeşil, Railway deploy `8afc625a` SUCCESS. 656 test, ağ kapalıyken de
geçiyor. Sel olayı (`Flash flooding in city streets`) yapılandırılmış hatta (`core/event_structure.py`):
- Hikâye `0-4s: … 4-9s: … 9-15s: …`. 0-4s kilit görseli kodda: "A waist-high wall of brown muddy floodwater surges
  into the street." Etiketleri kod ekler.
- 4-9s (V1–V8 araç olayı) ve 9-15s (D1–D8 büyük yıkım) havuzdan: son 3 üretimin olayları elenir, LRU (Notion
  combo_key `spot#görünüm#V6+D2` + süreç hafızası). 5 yasak eşleşme, D7 (tahta çit) körfezde/yüksek binada yok.
  Araç bölge görünümünün listesinden.
- GPT-4o strict JSON şemasıyla sadece 3 dilim yazar (`SLICES_SYSTEM`, olaydan bağımsız, testle kilitli). Kelime
  6-18 / 10-24 / 10-24, toplam 40-70 (genel 40-60 bu olayda yok). Esnek olay terimleri (kök + eşanlamlı).
- Kie öncesi son denetim (`final_prompt_issues`, `main.before_submit` → `submit_issues`): prompt koddan yeniden
  kurulanla birebir aynı olmalı; 1400 karakter (Seedance sınırı 20000).
- Preflight/Kie reddinde serbest yeniden yazıcı KULLANILMAZ: bizim yazar ret nedeniyle yeniden yazar (3 kalite
  denemesi), Kie'ye yeniden gönderim tek, ikinci retta durur (yeni senaryo denenmez).
- Notion: `get_recent_history` hatası üretimi durdurur; üretimde Notion zorunlu (CI'da `ci-dummy`).
- Kie testleri (3-4 Eki): zaman damgalı prompt'la Seedance 15 sn'yi aksiyonla doldurdu; yapılandırılmış prompt
  (task `57713f97`, V6+D2) üç dilimi zamanında çizdi, Bahadır kabul etti. İnsan kuralına gerek yok: Seedance kamera
  cümlesinden insanları uzakta çiziyor.
- Riviera görünümü "cobbled streets" (kıyı dev dalgayı da etkiler). Ölçek küçültücüye "futility" ve "bob".

**DURUM — borç / doğrulanmadı:** Canlıda Telegram'dan yeni hatla sel üretimi henüz yapılmadı (bot üzerinden ilk
gerçek akış, "Ayrıntı" mesajının görünümü teyitsiz). Kuru provada 7 denemenin 3'ü kelime sınırıyla kalmıştı; sınırlar
genişletildi ama yeni sınırlarla kuru prova koşulmadı.

**YAKLAŞIMIM (öneri, bağlayıcı değil):** Diğer olayları tek tek taşımak sadece veri işi (`EVENT_KEY_VISUAL` +
`EVENT_BEATS`); önce test videosuyla kanıtlanmış kilit görsel, havuz listesi Bahadır'a gösterilir. Kıyı dev dalga en
yakın aday (aynı bölge görünümleri ve araç listesi kullanılabilir).

**Nerede yanılmış olabilirim:** Tek bir yapılandırılmış Kie videosu var; havuzdaki 16 olayın çoğu Seedance'te
denenmedi (özellikle V5 yana yatma, D5 otobüs, D1 sıra sıra araçlar). Kelime kapısı anlamı tam yakalamıyor
("The uprooted tree…" sökülme anını göstermeden geçti).

**Sıradaki somut adım:** Bahadır Telegram'dan bir sel üretimi bassın (TEST modu); Ayrıntı mesajı ve video kontrol
edilsin. Sonra: ölü kod listesi (legacy `generate_legacy_prompts` zinciri, skeleton boşluk doldurma,
`get_recent_beat1_verbs` + `recent_verbs`, bot legacy dalı) ayrı turda; ardından sıradaki olayın taşınması.

---

## 📋 DEVİR (ESKİ) — Marina, Şehir bölge görünümü, Heyelan (2026-10-02 kapanışı)

**DEĞİŞMEZLER (Bahadır kararı):** Kie çağrısı ve üretim sadece Bahadır'ın açık isteğiyle (Telegram'dan kendisi
basar). Push öncesi Railway boşta mı bakılır (deploymentLogs: son "başlatılıyor" sonrası "Pipeline tamamlandı" ya da
"İptal"). Kural/liste gevşetmek onay ister; sabit kural bütçesi 6, olay başına en fazla 3 anahtar grup.

**Durum (doğrulandı):** Son commit `862c608`, deploy `759957c7` SUCCESS, bot TEST modunda açık, 575 test yeşil.
- **Marina:** halat (`Mooring line snaps in a storm gust`) ve kontrolsüz yat olayları ÇIKTI (REMOVED_EVENTS=20).
  **Ders: tekne-tekneye çarpma Seedance'te çıkmıyor** (iki videoda da yat çarpmadan düzgün seyretti); su gücü olayları
  (wake, pontoon) iyi çıkıyor. Menüde marina = wake + pontoon. 2. kurala "Show only what is visible, never sounds."
  eklendi (sistem prompt'u sınırı 160 kelime).
- **Şehir bölge görünümü:** sel ve kıyı dalgada 6 görünüm (`REGION_VIEWS`, skeleton_pipeline), olay başına LRU,
  Telegram'da olaydan sonra "Bölge: hangi görünüm?" adımı (`uret:v:...`). Görünüm Combo Key'in yer parçasında
  `spot#görünüm`. Kıyı dalga sonucu "brown churning ... thick with debris".
- **Geçmiş:** `get_used_combos` artık TEST modunda biteni de sayar (olay/gemi/görünüm LRU'su); elle test durumu
  ("Test — YouTube atlandı") bilerek sayılmaz. İptal/bitmemiş üretim için görünüm süreç hafızası (deploy'da silinir).
- **Heyelan (ONAYLI):** `landslide_disasters`, 3 çamur akıntısı olayı (hızlı akıntı, yavaş kayma yok), kişi 2-8,
  stil ekinde "No readable signs, text or flags." Köprü noktası yol çökmesinden çıktı (çamur yola ulaşmadı).

**Açık gözlemler (karar Bahadır'da, kod yok):** kıyı dalga hikâyelerinde "brown" çoğunlukla son cümlede (ilk kare
temiz dalga olabilir); Doğu Asya'nın yeni öğeleri (klima, kablo) hikâyede geçmiyor, sadece stil ekinde; heyelanda
"cars slide", "roars" gibi kelimeleri kapı yakalamıyor.

**Nerede yanılmış olabilirim:** Bölge görünümlerinin videoda tutup tutmadığını yalnızca Bahadır'ın 1 Eki videoları
gösterdi (Doğu Asya tutmamıştı, metni değişti, yeni hali Kie'de denenmedi).

---

## 📋 DEVİR (ESKİ) — Tersane side launch (2026-09-27 kapanışı)

**DEĞİŞMEZLER (kullanıcı kararı):** Ücretli çağrı (GPT/Kie) açık onay olmadan çalıştırılmaz. **Tersane domain'i
düzelene kadar üretimde kullanılmaz** (Telegram'da Tersane'ye basılmaz). Side launch'ta gemi artık feribot DEĞİL:
**büyük yat (superyacht / large luxury motor yacht)**.

**Durum (doğrulandı):** TUR 24-28 main'de, CI yeşil, son deploy `69ec2fc4` (`fbaa0b2`) SUCCESS, 400 test.
- TUR 24 (`2eb3513`): görünür tetik, sahne fiziği, sahneye göre kısa stil eki (63-111 kelime), 45-60 kelimelik
  hikaye, K/L/M kapıları. **Kruvaziyer Kie testinde kabul edildi.**
- TUR 25-26: Tersane haksız retleri, Telegram'a deneme başına tek satır ret özeti, "unexpectedly" serbest.
- TUR 27-28: Tersane side launch (ağırlık ~%70, `EVENT_SHIP_ONLY` şu an Passenger Car Ferry, `REPEATABLE_EVENTS`,
  beat planı, N kapısı, `rank_candidates` ile son seçim olay ağırlığıyla). GPT dry-run'ları geçti (son: 4/5).

**Sorun (Kie'de doğrulandı): TUR 27-28 side launch Kie testleri başarısız, 3 video.** Son testte prompt "long side
faces camera", "about 50 m away", "same size and position throughout" dediği halde Seedance feribotu uzakta, burnu
önde, rıhtım ucundan düşürdü; 9. saniyede sahne kesmesi, ardından devrik gemi. **Sonuç: metinle kompozisyon kontrolü
yetmiyor.** Prompt'a kural eklemek bu sorunu çözmez.

**Sıradaki oturum (sırayla):**
1. `EVENT_SHIP_ONLY[SIDE_LAUNCH_EVENT]` süper yata çevrilsin (superyacht / large luxury motor yacht). Evrende
   "Luxury Motor Yacht" var; ayrı "Superyacht" tipi gerekiyorsa `SHIP_NAME_PATTERNS` ve testler de güncellenir.
   Side launch beat planı, stil eki ve kişi aralığı feribot varsayıyor; hepsi yata göre gözden geçirilir.
2. Görselden videoya akış: önce ilk kare görseli üretilir (süper yat yan indirme raylarında, uzun kenarı kameraya
   dönük), sonra Seedance first-frame ile canlandırılır. **Önce araştırma:** Kie'nin Seedance 2 Mini
   (`bytedance/seedance-2-fast`) için ilk kare / image-to-video desteği var mı, hangi parametreyle? Görsel üretimi
   hangi modelle yapılacak? Ücretli deneme kullanıcı onayıyla.
3. Kullanıcının eski başarılı side launch videosunun prompt'u ve ayarları bulunsun (Notion geçmişi, lokal dosyalar,
   eski scratch çıktıları). Neyin işe yaradığı oradan çıkarılır.

**Nerede yanılmış olabilirim:** 3 başarısız video tek bir modelle (Seedance 2 Mini, 480p) alındı; daha büyük model
kompozisyonu tutabilir, denenmedi. Tersane dışındaki domainlerin TUR 24 sonrası Kie sonucu sadece Kruvaziyer'de görüldü.

---

## 📋 DEVİR (ESKİ) — Telegram tetikleyici (2026-09-26 kapanışı)

**DEĞİŞMEZLER (kullanıcı kararı):** Ücretli çağrı (GPT/Kie) açık onay olmadan çalıştırılmaz. Cron YOK; her üretim
Telegram `/uret` → domain butonu ile. Restart politikası ON_FAILURE kalır, tekrar kontrol edilmez.

**Durum (doğrulandı):** `bot.py` Railway'de (@DeepMysterUretimBot, izinli sohbet tek chat ID; Railway Variables
TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID). Commit `55b1114` + panel `16a7677`, CI yeşil, deploy `ab56e339` SUCCESS, bot açılış
logu var. Gerçek Feribot testi (onaylı): 209 sn, YouTube private https://youtube.com/shorts/LrQwJxLLreo, Notion
`manual` + ferry_operations combo, Hareket 0.58, Kie kredisi 375 (video başı ~175). Kullanıcı Telegram'da 3 mesaj + videoyu
aldı. Panel: Tetikleme kartı, şemada Telegram kutuları, kayıtlarda tetik + domain. 322 test.

**Borç (doğrulanmadı):** `ab56e339` deploy'undan sonra `/uret` butonlarının geldiği kullanıcıdan teyit edilmedi
(bot logu temiz). Railway log API'si Feribot koşusunun senaryo satırlarını eksik döndürdü; 5 senaryonun 5'inin feribot
olduğu bu koşu için logla görülmedi (birim testle güvenceli, görülen 2 ret + seçilen senaryo feribot).

**Nerede yanılmış olabilirim:** Railway'in ALWAYS'u neden ON_FAILURE'a çevirdiği bilinmiyor (plan kısıtı tahmini,
API "Not Authorized"). Telegram token'ı sohbete yapıştırıldı; iş bitince @BotFather `/revoke` + `.env` ve Railway
güncellemesi önerildi, kullanıcı karar vermedi.

**Sıradaki somut adım:** Kullanıcı `/uret` ile butonları görür (basmadan). Sonra normal üretim akışı; YouTube token
haftalık yenileme kuralı aynen geçerli (`refresh_youtube_token.bat`). (7 Eki: geçersiz, Production'a geçildi.) (12 Eki düzeltme: YANLIŞ, uygulama hâlâ Testing; haftalık yenileme kuralı geçerli.)

---

## 📋 DEVİR (ESKİ) — Açık işler (2026-09-25, gece kapanışı)

**Durum (doğrulandı):** TUR 1-23 kodu `main`'de (son `b097590`), 279/279 test. Railway aktif deploy = `b097590`
(GitHub Actions `tests` yeşilse otomatik deploy, "Wait for CI"; tetikleyici 54618a0d). Çalışma imajında ffmpeg var
(railpack.json). Cron 2026-09-26'da kaldırıldı, üretim Telegram /uret ile. TUR 21 Kie doğrulaması: 2 video kullanıcı tarafından kabul edildi
(Video 2 bug'ları — durağan açılış, "the vessel", kargo, zayıf Beat 3 — çözüldü).

**Sıradaki somut adımlar:**
1. **Cuma 25 Eylül 16:30 TR'den ÖNCE:** YouTube token'ını yenile — `refresh_youtube_token.bat` (ilk kez komut satırından:
   `python scripts\refresh_youtube_token.py`, tarayıcıda DeepMyster hesabıyla onay). Sonra masaüstü kısayolu.
2. **Cuma 16:45 TR'den sonra:** ilk production cron koşusunun 10 maddelik kontrolü — Railway çalışma logları (kapılar,
   retry, preflight, Kie, indirme, YouTube), Notion'daki yeni `auto` kaydı (Durum, Hareket ARTIK DOLU olmalı, Beat1 Fiil,
   YouTube URL), Kie kredisi (koşu öncesi 726.0, `scratch/cron_credit_before.json`).
3. Ayrı iş: Google Cloud'da OAuth uygulamasını "In production" + doğrulama (7 günlük token sorunu kalıcı biter).
   (7 Eki: YAPILDI, uygulama Production. 1. maddedeki haftalık yenileme artık gerekmez.)
   (12 Eki düzeltme: YANLIŞ, uygulama hâlâ Testing. Bu iş açık; haftalık yenileme gerekli.)

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

### 2. Doğukan Metodolojisi ("Less is More" — 45–60 Kelimelik Yüksek Sinyalli Prompt)
Seedance 2 Mini karmaşık, 6 parçalı mekanik checklistleri değil; görsel sinyali yüksek, doğrudan ve net dili anlar:
- **Uzunluk:** **45–60 kelime** (TUR 24, 2026-09-26; önce 25–45). Eski 36 kelimelik hikaye 270-341 kelimelik stil ekinin yanında prompt'un %10'u kalıyor, Beat 3 yarım cümleye sığıyordu. Kapı M 40-65 dışını reddeder.
- **İçerik Formülü (Esnek):**
  `[Adıyla anılan gemi veya çevre olayı + aksiyon + fiziksel etki] + [Fiziksel Eylem & İnsan/Mekanizma Müdahalesi] + [Hâlâ süren Sonuç]`
- **Kamera ve ışık hikayenin içinde YOKTUR:** Simplifier kamera/ışık yazmaz; kamera, çekim yeri, kıyafet ve gerçekçilik kuralları stil kilidiyle (`style_lock_suffix`) arkadan eklenir. Kie retry'larında GPT sadece hikayeyi yeniden yazar, stil eki değişmez.
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
