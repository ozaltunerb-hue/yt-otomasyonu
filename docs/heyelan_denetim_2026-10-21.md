# Genel kalite düzeltmesi + heyelan havuz denetimi — 21 Ekim 2026

Arka plan: "Yamaç sokağına çamur seli" testi (21 Eki 17:39, açılış D, H2+M6). İnsanlar ağır çekimde koştu, 12. saniyede
kamera başka bir eve döndü (M6 "a house corner": kadrajda tanımlı olmayan ev, gizli kesme), kaçanların bir kısmı
üniformalı, alt kenarda bir yüz kadraja girdi, çamur gri lapa gibiydi.

## 1-3, 5. Stil ekine eklenenler (19 yapılandırılmış olay)

- Gerçek zaman: "Everything moves in real time, never in slow motion, people run at full speed." Bahadır'ın metni,
  ";" yerine virgül: stil eki en fazla 8 kısıt kuralı ";" ve "." ile sayıyor; noktalı virgülle bazı olaylar 9 kısıta
  çıkıyordu. Not: bombalarda bu cümle kodda yoktu (sadece eski serbest hattın talimatında "in real time" geçiyor),
  19 olayın hepsine yeni eklendi.
- Üniforma: "emergency responders wear service uniforms" (ortam olayları) ve "responders wear service uniforms"
  (volkan) çıktı. Yerine "All people are ordinary civilians in everyday clothes". Çığ, deprem ve ateş hortumunda
  üniforma cümlesi zaten yoktu, onlarda "Civilians in winter / everyday clothes". Helikopter olayında helikopter
  kalır, giyim satırı yerdeki herkesi sivil yapar. Serbest (eski) hatta da üniforma cümlesi çıktı, ama oradaki iki
  satırlık giyim / ışık yapısı (ve "matching the weather") korundu.
- Ön plan yüzü: her kamera cümlesinin sonuna ", no person or face close to the camera". Ayrıca "shot by a person
  standing" -> "filmed" (kamerayı tutan kişiyi anmak ön plana insan çizdirebilir; 175 için de kısa).
- Heyelan: "The mud is dark brown, never grey." + kilit cümlelerde ve açılış varyantlarında "mud" geçen ilk ifade
  "thick brown mud full of rocks, branches and debris". Kilit cümlesinde "mud" olmayan varyantlarda (yamaç C, köy C/D)
  kod yedeğinde "mud" geçen ilk ifade dokulu (sığarsa).

Bütçe için yan değişiklik: çığ, deprem ve ateş hortumunda GPT'ye söylenen toplam kelime artık stil ekine göre
(volkan, sel ve kıyı dalgadaki gibi: 175 - 3 - stil eki). Yoksa bütçeye uyan GPT hikâyesi 176-178 kelimeyle son
denetimden dönüyordu.

## Kısaltılan kamera / sahne metinleri (175 kelime, tüm kombinasyonlar)

Kurallar aynı (yükseklik, sabitlik, inmez, tehdit karede, tek çekim). Kamera kısaltmaları son adımda uygulanır
(skeleton_pipeline.camera_rules / CAMERA_SHORTEN); kaynak cümleler ve kadraj eksenindeki birebir eşleştirmeler
(NATIVE_FG) değişmedi.

| Önce | Sonra |
|---|---|
| shot by a person standing | filmed |
| (mod B) high vantage looking down toward X; … X always in frame | high vantage; … X always in frame (tehdit bir kez) |
| (mod B) the camera stays fixed on the balcony / at the window | the camera stays fixed (yer cümlenin başında) |
| high vantage looking down over | high vantage over |
| (çığ) high vantage looking up a steep snowy slope where the avalanche is descending into the buildings just below it | high vantage up a snowy slope as the avalanche descends into the buildings below |
| (çığ) the slope and the avalanche fill the upper half of the frame, the nearest buildings and a corner of the railing fill the lower half; … the camera stays fixed, tilting slightly and never descending | slope and avalanche fill the upper half, the nearest buildings and a railing corner below; … the camera stays fixed, never descending |
| (deprem) high vantage looking across the street at the buildings collapsing opposite; the collapsing buildings and the dust fill the upper two thirds of the frame, the street and a corner of the railing fill the lower part; strong hand shake from the ground tremor | high vantage across the street; the collapsing buildings and dust fill the upper two thirds, the street and a railing corner below; strong hand shake from the tremor |
| (volkan) tilting down no more than slightly and never descending, the erupting volcano always visible in the upper third of the frame, a corner of the terrace railing … toward the erupting volcano | tilting only slightly, never descending, the volcano always in the upper third, a railing corner … toward the volcano |
| (hortumlar) the camera pans to follow the tornado | the camera follows the tornado |
| (ateş hortumu) two or three people fleeing close below | two or three people fleeing below |
| (direk) no on-screen text, no timestamp | no on-screen text or timestamp |
| nothing in the foreground | an empty foreground |
| Ortam olayları giyim + ışık (iki satır, 25 kelime) | "All people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI." (16; ışık ortam / ışık ekseninden) |
| Volkan (iki varyant) | ortam satırıyla aynı; kül bulutu da kısa satır |
| Çığ: "Bystanders wear winter civilian clothes; raw natural light, no hazmat suits." | "Civilians in winter clothes, no hazmat suits." (ışık ortam satırından) |
| Deprem: "Bystanders wear everyday clothes; raw natural light, no hazmat suits." | "Civilians in everyday clothes, no hazmat suits." (ışık ortam satırından) |
| Ateş hortumu giyim + şekil | "Civilians in everyday clothes, no hazmat suits, never CGI. A rotating funnel of flame with orbiting debris, never a straight plume or explosion." |
| Bölge görünümü satırı: "…, people in light everyday clothes suited to the climate, no readable signs…" | giyim ifadesi çıktı (giyim satırında) |
| Görünüm: east_asian "…air-conditioner units and tangled overhead wires, narrow lanes, delivery vans and box trucks" | "…air-conditioners and tangled wires, narrow lanes, delivery vans" |
| Görünüm: gulf "palm-lined multi-lane boulevards", us_coastal "overhead power lines" | "palm-lined boulevards", "power lines" |
| Ortam (çamur seli) B "a steep hillside town of pastel concrete houses with tin roofs, banana trees and tangled power lines", C "…white-washed stone houses … and narrow stepped lanes", D "…two-storey modern houses…" | B "a steep town of pastel concrete houses with tin roofs and banana trees", C "…white-washed houses … and stepped lanes", D "a hillside suburb of modern houses…" |
| Ortam (yamaç) B "a mountain road through a small roadside village of shops and houses, with a bus stop and parked motorbikes", C "…with guardrails and parked cars", D "…a petrol station and a row of houses" | B "a mountain road through a small village with a bus stop and parked motorbikes", C "…with parked cars", D "…a petrol station and houses" |
| Kamera noktası: ateş hortumu "…above a wooded residential area", "…overlooking a tree-lined residential street"; bombalar / kül bulutu "on the balcony of a village house across the street" | "…above a wooded area", "…over a tree-lined street"; "on a village house balcony across the street" |
| Kamera noktası: çamur seli "at the top of a side stairway beside the narrow hillside lane", yamaç "behind the guardrail on the far side of the hillside road" | "atop a side stairway beside the hillside lane", "behind the guardrail across the hillside road" |
| Açılış (doku eklenince 175 için): çamur seli B, yamaç B | "…around the bend at the top of the street and flips the first parked car over.", "…breaks off the slope and buries the road, cutting off a pickup truck." |

Beat metinlerine bütçe için dokunulmadı.

Bütçe sonucu (19 olay, tüm kombinasyonlar: görünüm × spot × beat çifti × araç × ortam × açılış × kadraj): her
kombinasyonda en az bir kadraj varyantıyla kod yedeği 175'e sığıyor, sığmayan 0. Kısıt sayısı her olayda en fazla 8.
Çeşitlilik: çamur seli, yamaç ve ateş hortumunda "sadece tek kamera modunda sığan" kombinasyon sayısı değişiklik
öncesindekiyle aynı düzeyde (çamur selinde değişiklik öncesi de 109 kombinasyon sadece mod A ile sığıyordu).

## 7. prompt_snapshot

19 olay × 20 tohum = 380 üretim. Stil eki 380'inde değişti (1-3 nedeniyle). Beat, ortam, açılış harfi, araç ve kişi
seçimleri 380'inde aynı. Hikâye metni heyelanda kilit cümle dokusu ve kadraj düzeltmesi yapılan beat'ler kadar değişti.
Kadraj / ön plan ekseni 8 üretimde değişti (sel, kıyı dalga, yangın, çamur seli, yamaç: 1'er; ateş hortumu: 3): 175
sığma koruması iki yönde etkiledi (kısalan mod B eskiden sığmayan varyantı sığdırdı ya da tersi). Baseline yenilendi.

## 3. Kameranın yanında insan ifade eden cümleler (sadece liste, değiştirilmedi)

- Çığ (3 olay), deprem (2 olay), ateş hortumu: `slice_near_camera` kuralı kaçan insanları kameranın yanına koyar. GPT
  satırı "close by: near the railing or in the street right below"; kod yedeği havuzunda "{N} people flee near the
  railing.", "{N} neighbours flee right below the railing." gibi cümleler. "near / by / along / next to / beside the
  railing", "close to the terrace / balcony" ön plan yüzü yasağıyla çelişir. Öneri: yakınlık "in the street right
  below" ile kalsın, railing / terrace / balcony'li ifadeler listeden ve yedek havuzdan çıksın.
- Ateş hortumu kamerası: "two or three people fleeing close below" -> "fleeing below" ("close" çıktı).
- Hortum kod yedeği: "{N} onlookers run inland…", "{N} onlookers dash away…" (izleyici kelimesi; kameraya yakınlık
  söylemiyor).

## 4. Kadraj dışı hedef

### Heyelan (düzeltildi)

| Olay | Beat | Önce | Sonra |
|---|---|---|---|
| Çamur seli | M3 | a low garden wall collapses and its stones tumble down the street | a garden wall along the street collapses and its stones tumble downhill |
| Çamur seli | M4 | a tree is torn out of the slope and carried down with the mud | a tree along the street is torn out and swept downhill |
| Çamur seli | M6 | the mud rams a house corner and tears off its wooden porch | the mud rams the nearest house and tears off its wooden porch |
| Çamur seli | M8 | the mud shoves a large truck sideways into the front of a house | the mud shoves a parked truck sideways into a house on the street |
| Yamaç | S2 | … smashes into a parked car | … smashes into a stopped car |
| Yamaç | S7 | … shove a large truck sideways … | … shove a stopped truck sideways … |
| Köy | L1 | a wooden house corner is struck and its wall collapses | a wooden house along the lane is struck and its wall collapses |
| Köy | L4 | a roof section is torn off a shed and swept away | a roof section is torn off a house along the lane and swept away |
| Köy | L6 | a stone wall collapses and its stones tumble into the torrent | a stone wall along the lane collapses and its stones tumble into the torrent |

Değiştirilmeyen (havuz lintinde korumalı, Bahadır kararı gerekir): köy K3 "pushed against a fence" (çit kadrajda
tanımlı değil, ince hedef), yamaç S4 "a utility pole snaps" (direk kadrajda tanımlı değil, ince hedef).

### Diğer olaylar (sadece liste, onaydan sonra)

| Olay | Beat | Hedef | Neden |
|---|---|---|---|
| Kıyı dalga | W4 | a roadside kiosk | açılışta / sahnede kiosk yok |
| Marina | Z2 | a small kiosk | açılışta kiosk yok (kafe var) |
| Hortum karaya | E2 / E5 | a billboard frame / a small shop | sahil yolunda tanımlı değil |
| Ateş hortumu | U11 | a wooden garage beside a house across the street | garaj tanımlı değil (ev görünür) |
| Kül bulutu | P6 | a row of low sheds | sokakta baraka tanımlı değil |
| Çığ köy | A3, A4, B6 | a barn, a stone barn, a wooden shed | ahır / baraka ortam satırında yok (kulübe, köşk var) |
| Çığ köy | A5 | a long wooden fence and a wooden shed beside the street | çit + baraka (A5 lintte korumalı) |
| Çığ köy | B3 | a wooden church bell tower across the street | çan kulesi tanımlı değil |
| Çığ kayak | C4, D4, D5 | a snack cabin / ski-rental cabin by the slope | kayak evi dışında yapı, yamaç kenarı kadrajın dışı olabilir |
| Çığ orman | E3, E7, F5, F6 | stone farmhouse / barn | orman vadisinde çiftlik evi tanımlı değil (kulübeler var) |
| Çığ orman | E4 | a woodshed | tanımlı değil |
| Deprem eski sokak | R4 | a corner stone house … across the junction | kavşak tanımlı değil |

## 6. Heyelan havuz denetimi

Puan 1-5 (5 iyi). Ölçütler: B büyüklük, K kontrast (hedef çamurdan ayrışıyor mu), Y kameraya yakınlık (kamera yüksek
ve sabit; hepsi orta mesafe), Ç çizilebilirlik, A aksiyon, F diğer beat'lerden farklılık. Gör: hedef açılış kadrajında
görünür mü. Ger: fiziksel olarak gerçekçi mi. ⚠️ = zayıf.

### Çamur seli (dik yamaç sokağı)

| Beat | Metin | B | K | Y | Ç | A | F | Gör | Ger | |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | {vehicle} shoved sideways, slams into the car parked beside it | 4 | 3 | 3 | 5 | 4 | 3 | evet | evet | |
| H2 | {vehicle} pushed down the street, bumping parked cars | 4 | 3 | 3 | 4 | 3 | 2 | evet | evet | ⚠️ |
| H3 | {vehicle} spun around and dragged downhill | 4 | 3 | 3 | 4 | 4 | 4 | evet | evet | |
| H4 | {vehicle} buried to its windows, pushed against a house wall | 4 | 2 | 3 | 3 | 2 | 4 | evet | evet | ⚠️ |
| H5 | {vehicle} tips over onto its side | 4 | 4 | 3 | 5 | 5 | 4 | evet | evet | |
| H6 | {vehicle} and the car behind it pushed down together | 4 | 3 | 3 | 4 | 3 | 2 | evet | evet | ⚠️ |
| M3 | a garden wall along the street collapses, stones tumble | 2 | 2 | 3 | 4 | 3 | 4 | evet* | evet | ⚠️ |
| M4 | a tree along the street torn out, swept downhill | 3 | 3 | 3 | 4 | 4 | 3 | evet* | evet | |
| M6 | the mud rams the nearest house, tears off its wooden porch | 3 | 3 | 3 | 3 | 3 | 4 | evet* | evet | ⚠️ |
| M7 | mud slams into a house across the street, bursts through its ground floor | 5 | 3 | 3 | 4 | 5 | 4 | evet | evet | |
| M8 | the mud shoves a parked truck sideways into a house | 5 | 4 | 3 | 4 | 4 | 3 | evet* | evet | |
| M9 | mud and uprooted trees crash onto the houses across the street | 5 | 3 | 3 | 4 | 5 | 3 | evet | evet | |

\* bu turda düzeltildi (önceden kadraj dışı).

Önerilen alternatifler (zayıf olanlar):
- H2 -> "the {vehicle} is lifted by the mud and rammed into the parked motorbikes along the curb" (görünür hedef, ayrışan).
- H4 -> "the {vehicle} flips onto its roof and is carried down the street by the mud" (yüksek aksiyon ve kontrast).
- H6 -> "the {vehicle} is shoved nose-first into the front door of a house lining the street" (H2 / H1'den farklı).
- M3 -> "a wave of mud lifts the parked motorbikes along the curb and tumbles them downhill" (açılış D ile çakışır: D'de M3 hariç tutulmalı).
- M6 -> "the mud lifts a parked car and drops it onto the porch of the nearest house" (büyük nesne, kontrast).

### Yamaç (dağ yolu)

| Beat | Metin | B | K | Y | Ç | A | F | Gör | Ger | |
|---|---|---|---|---|---|---|---|---|---|---|
| R1 | {vehicle} shoved sideways across the road by mud and rocks | 4 | 3 | 3 | 5 | 4 | 3 | evet | evet | |
| R2 | {vehicle} pushed against the guardrail and pinned there | 3 | 3 | 3 | 3 | 2 | 3 | evet | evet | ⚠️ |
| R3 | a rolling boulder strikes the {vehicle}, which spins and slides | 5 | 4 | 3 | 4 | 5 | 5 | evet | evet | |
| R4 | {vehicle} buried to its windows, pushed toward the road edge | 3 | 2 | 3 | 3 | 3 | 3 | evet | evet | ⚠️ |
| R5 | {vehicle} tips over onto its side in the mud | 4 | 4 | 3 | 5 | 5 | 4 | evet | evet | |
| R6 | {vehicle} and the car behind it shoved along together | 4 | 3 | 3 | 4 | 3 | 2 | evet | evet | ⚠️ |
| S2 | a large boulder rolls across the road, smashes into a stopped car | 5 | 4 | 3 | 5 | 5 | 3 | evet* | evet | |
| S3 | a tree torn out of the slope slides across the road | 4 | 3 | 3 | 4 | 4 | 3 | evet | evet | |
| S4 | a utility pole snaps and falls across the road | 2 | 3 | 3 | 3 | 3 | 4 | hayır | evet | ⚠️ |
| S5 | more of the slope gives way, a second surge pours onto the road | 5 | 2 | 3 | 4 | 4 | 4 | evet | evet | |
| S7 | mud and boulders shove a stopped truck toward the road edge | 5 | 4 | 3 | 4 | 4 | 3 | evet* | evet | |

Önerilen alternatifler:
- R2 -> "the {vehicle} is spun around and slammed backwards into the rock face beside the road" (yamaç kadrajda; sabit "pinned" yerine aksiyon).
- R4 -> "the {vehicle} flips onto its roof in the middle of the road" (kontrast, aksiyon).
- R6 -> "a falling rock slab crushes the bonnet of the {vehicle}" (R1'den farklı; büyük gri kaya kahverengi çamurdan ayrışır).
- S4 -> "a huge slab of rock breaks off the slope and crashes onto the road in front of the cars" (ince hedef yerine büyük kütle).

### Köy (yamaç köyü sokağı)

| Beat | Metin | B | K | Y | Ç | A | F | Gör | Ger | |
|---|---|---|---|---|---|---|---|---|---|---|
| K1 | {vehicle} swept down the lane, rammed against a house wall | 4 | 3 | 3 | 4 | 4 | 3 | evet | evet | |
| K2 | {vehicle} spun around, dragged along the lane | 4 | 3 | 3 | 4 | 4 | 3 | evet | evet | |
| K3 | {vehicle} buried to its windows, pushed against a fence | 3 | 2 | 3 | 3 | 2 | 3 | hayır | evet | ⚠️ |
| K4 | {vehicle} tips over onto its side in the torrent | 4 | 4 | 3 | 5 | 5 | 4 | evet | evet | |
| K5 | {vehicle} slams into a pile of logs, both carried away | 4 | 3 | 3 | 3 | 4 | 4 | evet | evet | |
| K6 | {vehicle} shoved into a parked motorbike, both carried along | 3 | 3 | 3 | 4 | 3 | 4 | evet | evet | |
| L1 | a wooden house along the lane struck, its wall collapses | 5 | 4 | 3 | 4 | 5 | 4 | evet* | evet | |
| L3 | a large tree uprooted, rolls down with the torrent | 4 | 3 | 3 | 4 | 4 | 3 | evet | evet | |
| L4 | a roof section torn off a house along the lane | 4 | 3 | 3 | 4 | 4 | 3 | evet* | evet | |
| L5 | a pile of logs breaks loose, rolls down the lane | 4 | 3 | 3 | 4 | 4 | 2 | evet | evet | ⚠️ |
| L6 | a stone wall along the lane collapses, stones tumble | 3 | 2 | 3 | 4 | 3 | 3 | evet* | evet | ⚠️ |
| L7 | the landslide rips a wooden house off its foundation | 5 | 4 | 3 | 3 | 5 | 4 | evet | zor | |

Önerilen alternatifler:
- K3 -> "the {vehicle} is lifted and wedged between two houses along the lane" (çit yerine görünür evler).
- L5 -> "the torrent tears a wooden balcony off a house along the lane" (K5 kütük tekrarı yerine; ince hedef değil, büyük ahşap).
- L6 -> "the torrent smashes a parked car against the front of a house along the lane" (gri taş / çamur düşük kontrastı yerine araç).

Kameraya yakınlık hepsinde 3: kamera yüksek ve sabit, beat'ler sokak ortası. Yakınlık artırmak "no person or face close
to the camera" ile çelişmeden nesneyle yapılabilir ("right below the balcony" araç / ev), bu raporda öneri yok.

## 22 Ekim: uygulanan beat değişikliği (Bahadır onayı)

12 zayıf beat'in metni değişti, kodlar aynı: çamur seli H2, H4, H6, M3, M6; yamaç R2, R4, R6, S4; köy K3, L5, L6.
Terim grupları yeni metne göre (araçlı beat'lerde lift / airborne / flip / flung / into the air / tumble yok, testli).
R2, S4 ve K3 artık ince hedef taşımıyor: havuz lintindeki muafiyetleri çıktı (25 -> 22).

Dışlamalar (aynı hedef + aynı fiil):
- Çamur seli: H4 artık ev değil, eski H4-ev çiftleri (M6, M7, M8, M9) çıktı; H4+M3 (park arabaları itilir) kaldı. Ev iki
  kez kuralı yeni H6'ya geçti: H6+M6 (eve gömülür), H6+M7, H6+M8 (eve itilir), H6+M9. H1+M8 aynı.
- Yamaç: R2+S7 eklendi (araç itilir). R4+S7 kaldı (yine araç itilir).
- Köy: K1+L6 kaldı. K1+L5 (ev duvarı) ve K3+L6 (araç sokakta itilir) eklendi. K5+L5 çıktı (L5 artık kütük değil).
- Açılış: çamur seli B+M3 (ilk park arabası devrilir / park arabaları itilir); C+M3 çıktı (M3 artık duvar değil).
  Yamaç B+S4 (yamaçtan kopar, yola düşer) ve C+S4 (kaya yola düşer). Köy C ve D'nin aday listesindeki L5 (ev) elle
  süzüldü: aynı fiil değil (temelinden itmek / çatıya kaymak), dışlanmadı.

175 bütçesi: yeni metinler uzun (H6 22, R2 23, H4 20 kelime). Kod yedeği 3 çiftte sığmadı, metin kısaltılmadı, çift
dışlandı: H4+M6 (açılış B ile 60 kombinasyon), R2+S4 (63 / 72), R2+S5 (63 / 144). Sonra sığmayan 0.

Yakınlık listesi: "in the foreground" çıktı (_AVA_NEAR; ateş hortumu listesi bundan türediği için onda da). Etkilenen:
çığ (3), deprem (2), ateş hortumu kapısı. Kod yedeği havuzlarında ve GPT ipucunda bu ifade yoktu, prompt değişmedi.
