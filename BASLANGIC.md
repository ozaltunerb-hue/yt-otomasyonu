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
| **YouTube OAuth Token** | ✅ Google uygulaması **Production** (2026-10-07). 7 günlük ömür ve haftalık yenileme KALKTI. Token yine 3 durumda ölür: 6 ay hiç kullanılmazsa, Google hesabından erişim iptal edilirse, çok sayıda yeni token alınırsa (en eskiler geçersizleşir). Sadece bot YouTube yetki hatası verirse `refresh_youtube_token.bat` (masaüstü kısayolu) çalıştırılır; BİTTİ yazısı görülmeden pencere kapatılmaz. Betik önce yerel `.env` + `master.env`'e, sonra Railway'e yazar; adım logu `dashboard_data/token_refresh_runs.log` |
| **Cron / Otomasyon** | ❌ Cron KALDIRILDI (2026-09-26). Üretim Telegram botundan: `python bot.py` (Railway start komutu), `/uret` → domain seç. Sadece `TELEGRAM_CHAT_ID` sohbeti, tek seferde tek üretim. Otomatik Kie harcaması yok |
| **Notion Dedup/Log** | ✅ AKTİF (2026-09-12) — `NOTION_ENABLED=True`, veritabanı kuruldu ve doğrulandı |

---

## 📋 DEVİR: Süper hücre terim kapısı eş anlamlı genişletmesi + terim kapısı kuralı (10 Eki)

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

## 📋 DEVİR: Süper hücre havuzlarında zayıf maddeler değişti + GENEL İLKE (10 Eki)

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

## 📋 DEVİR: ⛈️ Süper hücre fırtınası kategorisi (10 Eki)

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
(7 Eki: uygulama Production'a geçti, haftalık yenileme yok; bkz. GÜNCEL DURUM "YouTube OAuth Token".)

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
haftalık yenileme kuralı aynen geçerli (`refresh_youtube_token.bat`). (7 Eki: geçersiz, Production'a geçildi.)

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
