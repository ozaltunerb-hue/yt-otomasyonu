# Havuz denetimi — 11 Kasım 2026

Kaynak: kod (core/), Notion Paylaşımlar (11 Kas okuması, 100K+ kayıtlar), `dashboard_data/notion_runs.json` (7 Kas senkronu).
Kie / GPT çağrısı yok. Tablolar `scripts/havuz_denetim.py` ile üretildi (salt okuma). "40 art arda basış": süreç hafızası
sıfırdan, her basış önceki basışların eksen kaydını görür (sahte Notion, üretimdeki LRU yolu), tohum = basış no.

## Hit (100K+) eşleşmesi

Paylaşım ile üretim kaydı arasında doğrudan bağ yok. Eşleşme: paylaşım tarihinden önceki tamamlanmış üretim + olay + açıklama.

| Olay | Paylaşım | Üretim | Hit öğeleri |
|---|---|---|---|
| Kül bulutu | 13 Eki 2,13M | 13 Eki 11:23 | yamaç terası, P2, Q1, açılış A, ışık ash-grey |
| Kül bulutu | 25 Eki 102K | 17 Eki 14:13 | çatı terası, P2, Q5, açılış A |
| Dev dalga | 24 Eyl 1,42M | kayıt yok (yapılandırılmış hat öncesi) | yüksek balkon (eski mod A cümlesi) |
| Dev dalga | 3 Eki 135K | 1 Eki / 3 Eki (beat'siz) | korkuluk ön planı (promenat, aday) |
| Dev dalga | 13 Eki 247K | aday: 4 Eki 11:06 T7+W1 ya da 4 Eki 10:16 T5+W5 (ikisi de seawall) | açıklama "cleared the sea wall… cars were swept away" 11:06'ya yakın, kesin değil |
| Orman yangını | 19 Eki 3,02M | 9 Eki 21:52 | balkon, K5, L4, açılış A |
| Orman yangını | 31 Eki 107K | 31 Eki 09:44 | set, K2, L5, açılış A, ortam A, çatı/parapet, öğle ışığı |
| Helikopter | 12 Eki 170K | 9 Eki 22:52 | balkon, F1, G2, açılış A |
| Hortum karaya vurur | 1 Kas 10,37M | 31 Eki 09:52 | konut bölgesi, C1, E1, açılış C, pencere kadrajı |
| Volkan bombaları | 10 Eki 1,36M | 10 Eki 02:06 | çatı terası, R4, T2, açılış A |
| Heyelan köy | 2 Eki 431K | 1 Eki 22:09 (beat'siz) | köy meydanı basamakları, açılış A |
| Sel | 29 Eyl 338K, 4 Eki 132K, 6 Eki 305K | beat'siz üretimler | kilit 3249de8 hâli |
| Ateş hortumu | 9 Eki 673K | 8 Eki 21:23 | T4, U2 |
| Ateş hortumu | 26 Eki 176K | aday 16 Eki 13:45 | T1, U8 (aday) |
| Özgürlük Anıtı | — | — | 100K+ paylaşım yok |

## Bu turun hit kararları (kül bulutu, dev dalga)

- **Pasife ALINMAYANLAR (hit):** kül bulutu açılış A (13 Eki 2,13M), yamaç terası ve çatı terası kadrajı (13 Eki, 25 Eki),
  P2 (iki hit), Q5 (25 Eki 102K; yeni "blast" kapısına takıldı, `KNOWN_HITS`'e yazıldı). Dev dalga T5 (13 Eki 247K adayı).
- **Pasife alınanlar (hit yok):** kül bulutu açılış B C D, balkon kadrajı, P1 P3 P5; dev dalga balkon ve teras kadrajı
  (bugünkü mod B cümleleri hiçbir hit'te yok; hit'ler eski mod A cümlesiyle), W3 (tek üretimi 4 Eki 10:25, seawall yok),
  W4 (tamamlanmış üretimi yok), I2 (hiçbir üretimde yok).

## Kilitli 8 olay: öne çıkan bulgular (D3)

- **Ping-pong (iki seçenek sırayla):** orman yangını spotu (Balcony / Embankment), helikopter spotu ve kadrajı, volkan
  bombaları spotu ve kadrajı (çatı / balkon), sel kadrajı (40 basışta 2 tip).
- **3'ten az aktif:** açılış her kilitli olayda 1-2 (A + koruma harfi; Özgürlük Anıtı tek açılış), ortam (orman, helikopter,
  karaya vurur, heyelan köy: A + koruma), bombalar ışık (2), ön plan (bombalar: korkuluk / boş), Özgürlük Anıtı spot (K1 +
  K2 deneme).
- Ateş hortumu açılışı ortama bağlı (her ortamın kendi kilit cümlesi); simülasyon sütununda "A" görünür, gerçek çeşitlilik
  ortam sütununda.
- Kilitli olaylarda kodda değişiklik yok; 40 tohum kilit özeti fark 0.

## Değişiklik öncesi ve sonrası özet (kül bulutu, dev dalga)

- **Kül bulutu önce:** açılış A + B (koruma ≤%20); kadraj yamaç/çatı yerli (+ korkuluk/boş); 4-9s P1 P2 P3 P4 P5 aktif (P6
  pasif); 9-15s Q1 Q3 Q4 Q5 + Q7 Q8 deneme; insan P1-P3 birebir; VERBATIM açık (GPT sadece 0-4s insan cümlesi, o da atılır);
  tavan 175 kelime / 1400 karakter, hikâye 40-75.
- **Kül bulutu sonra:** açılış A + E (son 1 hariç, sırayla); kadraj K_V (birebir) + hit yerli kadrajlar; 4-9s P2 P4 P7 P8;
  9-15s aynı; ortamlar "right at the foot of the volcano"; kapı fireball/blast/explosion/explode/nuclear/mushroom (sadece
  kül bulutu); tavan 205 / 1400, hikâye 40-92 (en uzun kod yedeği 205).
- **Dev dalga önce:** kadraj balkon (ikinci kat) + teras (promenat korkuluğu), mod B; 4-9s T2 T3 T5 T7 T8; 9-15s W1 W3 W4 W5;
  insan I1 I2 kanıtlı, I3-I6 deneme.
- **Dev dalga sonra:** kadraj K_R1 K_R2 K_R3 (birebir, spottan bağımsız, ön plan parapet / pencere kenarı / teras korkuluğu,
  son 1 hariç); 9-15s W1 W5 W10 W11 W12; insan I1 I7 I8 I9 ana, I3-I6 deneme, I2 pasif; GPT kapısı "inland" (sadece dev dalga).

---

## A1 / B1 — değişiklikten ÖNCE (HEAD dba1187)

### (önce) Pyroclastic cloud races down into a village street

Hit (100K+) eşleşmesi: 13 Eki 2,13M ← 13 Eki 11:23 · 25 Eki 102K ← 17 Eki 14:13

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Hillside terrace facing the erupting volcano | on a hillside terrace above the houses | aktif | 13 Eki 2,13M |
| Rooftop terrace facing the erupting volcano | on a rooftop terrace across the street | aktif | 25 Eki 102K |
| Balcony of a village house facing the erupting volcano | on a house balcony across the street | PASİF/rotasyon dışı |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| balkon @ Balcony of a village house facing the erupting volcano | Handheld footage filmed on a house balcony across the street, high vantage over a street of colorful painted stucco houses with balconies toward the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| çatı @ Rooftop terrace facing the erupting volcano | Handheld footage filmed on a rooftop terrace across the street, high vantage over a street of colorful painted stucco houses with balconies toward the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| tepe @ Hillside terrace facing the erupting volcano | Handheld footage filmed on a hillside terrace above the houses, high vantage over a street of colorful painted stucco houses with balconies toward the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| pencere @ kütüphane | Handheld footage filmed through an open upper-floor window, high vantage over a street of colorful painted stucco houses with balconies toward the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, the edge of the open window frame at one side; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| korkuluk (balkon @ Balcony of a village house facing the erupting volcano) | a railing corner in the foreground | rotasyon dışı |  |
| boş (balkon @ Balcony of a village house facing the erupting volcano) | nothing in the foreground | rotasyon dışı |  |
| korkuluk (çatı @ Rooftop terrace facing the erupting volcano) | a railing corner in the foreground | aktif |  |
| boş (çatı @ Rooftop terrace facing the erupting volcano) | nothing in the foreground | aktif |  |
| korkuluk (tepe @ Hillside terrace facing the erupting volcano) | a railing corner in the foreground | aktif |  |
| boş (tepe @ Hillside terrace facing the erupting volcano) | nothing in the foreground | aktif |  |
| pencere (pencere @ kütüphane) | the open window frame at one side | rotasyon dışı |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| pastel_town | a street of colorful painted stucco houses with balconies | aktif (ağırlık 2) |  |
| hillside_town | a wide hillside-town street of stone and painted houses | aktif (ağırlık 2) |  |
| suburb | a suburban street of detached houses, garages and palm trees | aktif (ağırlık 1) |  |
| mountain_village | a village street of wooden and stone houses among trees | aktif (ağırlık 1) |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A pyroclastic cloud races down the volcano’s flank and slams into the street. | aktif | 13 Eki 2,13M; 25 Eki 102K |
| B | The ash cloud races down the volcano's slope and swallows the highest houses on the slope in the first second. | aktif |  |
| C | A blast of hot air ahead of the cloud bends the trees, and the grey wall of ash surges into the street right behind it. | rotasyon dışı (deneme) |  |
| D | The ash cloud spreads across the valley and engulfs the houses on both sides of the street at once. | rotasyon dışı (deneme) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | ash-grey sky lit orange by a distant eruption plume | aktif | 13 Eki 2,13M |
| L2 | warm orange dusk sky glowing from the eruption | aktif |  |
| L3 | bright hazy daylight under a dark ash sky | rotasyon dışı |  |
| L4 | pink-orange dawn light under a dark ash sky | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| P1 | the cloud front slams into the houses across the street and tears the balconies off their facades | aktif |  |
| P2 | the cloud snaps a row of street trees and power poles and they crash across the street | aktif | 13 Eki 2,13M; 25 Eki 102K |
| P3 | the cloud rips roof tiles off the rooftops and hurls them down the street | aktif |  |
| P4 | the cloud front flattens a row of palm trees and hurls their fronds ahead of it | aktif |  |
| P5 | the cloud front shoves a stone garden wall over and rolls on across the street | aktif |  |
| P6 | the cloud front rips the corrugated roofs off a row of low sheds and sends them flying | PASİF |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Q1 | a house wall across the street collapses as the cloud engulfs it | aktif | 13 Eki 2,13M |
| Q2 | the cloud engulfs a whole block and the upper-floor windows burst outward in a shower of glass | PASİF |  |
| Q3 | a chimney topples and crashes through a roof as the cloud passes over | aktif |  |
| Q4 | the cloud hits a hillside retaining wall and the wall gives way, boulders tumbling into the street | aktif |  |
| Q5 | the cloud blasts the front off a shop building and the brickwork falls into the street | aktif | 25 Eki 102K |
| Q6 | the cloud flips a row of parked cars and piles them against a house wall | PASİF |  |
| Q7 | the cloud front tears the roof off the house right below before swallowing it | DENEME |  |
| Q8 | the cloud front knocks down the front wall of the two-storey house across the street, then swallows it | DENEME |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| P1 | {N} people sprint into the open doorway of the house right below. | DENEME (birebir) |  |
| P2 | {N} people run for the garage of a house across the street below. | DENEME (birebir) |  |
| P3 | {N} people sprint down the street toward a stone archway below. | DENEME (birebir) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| - | araçsız olay | - |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Hillside terrace facing the erupting volcano | çatı @ Rooftop terrace facing the erupting volcano [ön plan: korkuluk, boş]; tepe @ Hillside terrace facing the erupting volcano [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Rooftop terrace facing the erupting volcano | çatı @ Rooftop terrace facing the erupting volcano [ön plan: korkuluk, boş]; tepe @ Hillside terrace facing the erupting volcano [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Balcony of a village house facing the erupting volcano | çatı @ Rooftop terrace facing the erupting volcano [ön plan: korkuluk, boş]; tepe @ Hillside terrace facing the erupting volcano [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 2 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Kadraj | 2 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Ön plan | 4 | 2 | ⚠ 3'ten az |
| Ortam | 4 | 4 |  |
| Açılış (0-4 sn) | 2 | 2 | ⚠ 3'ten az |
| Işık | 2 | 2 | ⚠ 3'ten az |
| Orta (4-9 sn) | 5 | 5 |  |
| Final (9-15 sn) | 6 | 6 |  |
| İnsan cümlesi | 3 | 3 |  |
| Araç | 0 | 0 | araçsız |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Hillside terrace facing the erupting volcano | tepe | korkuluk | mountain_village | A | P5 | Q3 | P1 | - |
| 2 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | A | P2 | Q5 | P3 | - |
| 3 | Hillside terrace facing the erupting volcano | tepe | korkuluk | hillside_town | B | P1 | Q7 | P2 | - |
| 4 | Rooftop terrace facing the erupting volcano | çatı | boş | suburb | A | P4 | Q1 | P1 | - |
| 5 | Hillside terrace facing the erupting volcano | tepe | korkuluk | mountain_village | A | P2 | Q3 | P3 | - |
| 6 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | P5 | Q5 | P2 | - |
| 7 | Hillside terrace facing the erupting volcano | tepe | boş | pastel_town | A | P4 | Q8 | P1 | - |
| 8 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | P1 | Q4 | P3 | - |
| 9 | Hillside terrace facing the erupting volcano | tepe | korkuluk | hillside_town | A | P3 | Q1 | P2 | - |
| 10 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | B | P4 | Q5 | P1 | - |
| 11 | Hillside terrace facing the erupting volcano | tepe | korkuluk | suburb | A | P2 | Q4 | P3 | - |
| 12 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | B | P4 | Q8 | P2 | - |
| 13 | Hillside terrace facing the erupting volcano | tepe | korkuluk | mountain_village | A | P1 | Q3 | P1 | - |
| 14 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | B | P2 | Q1 | P3 | - |
| 15 | Hillside terrace facing the erupting volcano | tepe | korkuluk | hillside_town | A | P3 | Q4 | P2 | - |
| 16 | Rooftop terrace facing the erupting volcano | çatı | boş | suburb | B | P1 | Q5 | P1 | - |
| 17 | Hillside terrace facing the erupting volcano | tepe | korkuluk | mountain_village | A | P4 | Q3 | P3 | - |
| 18 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | P2 | Q4 | P2 | - |
| 19 | Hillside terrace facing the erupting volcano | tepe | korkuluk | pastel_town | A | P3 | Q5 | P1 | - |
| 20 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | P4 | Q1 | P3 | - |
| 21 | Hillside terrace facing the erupting volcano | tepe | korkuluk | suburb | A | P5 | Q3 | P2 | - |
| 22 | Rooftop terrace facing the erupting volcano | çatı | boş | pastel_town | A | P2 | Q8 | P1 | - |
| 23 | Hillside terrace facing the erupting volcano | tepe | korkuluk | hillside_town | B | P4 | Q4 | P3 | - |
| 24 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | suburb | A | P5 | Q5 | P2 | - |
| 25 | Hillside terrace facing the erupting volcano | tepe | korkuluk | pastel_town | A | P3 | Q8 | P1 | - |
| 26 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | P1 | Q4 | P3 | - |
| 27 | Hillside terrace facing the erupting volcano | tepe | korkuluk | mountain_village | A | P2 | Q5 | P2 | - |
| 28 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | A | P4 | Q1 | P1 | - |
| 29 | Hillside terrace facing the erupting volcano | tepe | korkuluk | hillside_town | A | P1 | Q3 | P3 | - |
| 30 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | P2 | Q8 | P2 | - |
| 31 | Hillside terrace facing the erupting volcano | tepe | korkuluk | pastel_town | A | P3 | Q1 | P1 | - |
| 32 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | P4 | Q5 | P3 | - |
| 33 | Hillside terrace facing the erupting volcano | tepe | korkuluk | mountain_village | A | P2 | Q3 | P2 | - |
| 34 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | suburb | A | P1 | Q4 | P1 | - |
| 35 | Hillside terrace facing the erupting volcano | tepe | korkuluk | hillside_town | A | P3 | Q5 | P3 | - |
| 36 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | P2 | Q1 | P2 | - |
| 37 | Hillside terrace facing the erupting volcano | tepe | korkuluk | pastel_town | A | P5 | Q7 | P1 | - |
| 38 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | suburb | B | P1 | Q5 | P3 | - |
| 39 | Hillside terrace facing the erupting volcano | tepe | boş | hillside_town | A | P3 | Q4 | P2 | - |
| 40 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | A | P4 | Q1 | P1 | - |

### (önce) Tidal wave surges over a coastal city street

Hit (100K+) eşleşmesi: 24 Eyl 1,42M ← 24 Eyl (yapılandırılmış hat öncesi, kayıt yok) (yüksek balkon, mod A) · 3 Eki 135K ← 1 Eki / 3 Eki (beat'siz) (korkuluk ön planı: promenat (aday)) · 13 Eki 247K ← aday: 4 Eki 11:06 T7+W1 (seawall) ya da 4 Eki 10:16 T5+W5 (seawall) (açıklama 'cleared the sea wall... cars were swept away': 11:06'ya yakın, kesin değil)

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Coastal road below a seafront promenade | at the railing of a raised seafront promenade, looking down at the coastal road | aktif |  |
| Coastal street of low shopfronts | on a second-floor balcony, looking down at the coastal street | aktif |  |
| Coastal avenue behind a seawall | on top of the seawall, looking down at the coastal avenue | aktif |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| balkon @ Coastal street of low shopfronts | Handheld footage filmed on a second-floor balcony, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the camera never pans, turns or follows, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ kütüphane | Handheld footage filmed on a flat rooftop above the coastal street, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the camera never pans, turns or follows, a low parapet edge in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| pencere @ kütüphane | Handheld footage filmed through an open upper-floor window across from the coastal street, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the camera never pans, turns or follows, the open window frame at one side; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| direk @ kütüphane | Footage from a fixed high security camera on a tall pole above the coastal street, slightly wide lens, no hand shake, no on-screen text or timestamp, high vantage; the camera stays fixed, the camera never pans, turns or follows; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| teras @ Coastal road below a seafront promenade mod A | Handheld footage filmed at the railing of a raised seafront promenade, looking down at the coastal road, eye level, normal lens; slight hand shake, the camera pans to follow the tidal wave; no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| teras @ Coastal road below a seafront promenade mod B | Handheld footage filmed at the railing of a raised seafront promenade, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the camera never pans, turns or follows, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| balkon @ Coastal street of low shopfronts mod A | Handheld footage filmed on a second-floor balcony, looking down at the coastal street, eye level, normal lens; slight hand shake, the camera pans to follow the tidal wave; no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| balkon @ Coastal street of low shopfronts mod B | Handheld footage filmed on a second-floor balcony, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the camera never pans, turns or follows, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| teras @ Coastal road below a seafront promenade | Handheld footage filmed at the railing of a raised seafront promenade, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the camera never pans, turns or follows, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| korkuluk (balkon @ Coastal street of low shopfronts) | a railing corner in the foreground | aktif |  |
| boş (balkon @ Coastal street of low shopfronts) | nothing in the foreground | aktif |  |
| parapet (çatı @ kütüphane) | a low parapet edge in the foreground | rotasyon dışı |  |
| boş (çatı @ kütüphane) | nothing in the foreground | rotasyon dışı |  |
| pencere (pencere @ kütüphane) | the open window frame at one side | rotasyon dışı |  |
| teras_korkuluk (teras @ Coastal road below a seafront promenade mod B) | a railing corner in the foreground | aktif |  |
| boş (teras @ Coastal road below a seafront promenade mod B) | nothing in the foreground | aktif |  |
| korkuluk (balkon @ Coastal street of low shopfronts mod B) | a railing corner in the foreground | aktif |  |
| boş (balkon @ Coastal street of low shopfronts mod B) | nothing in the foreground | aktif |  |
| teras_korkuluk (teras @ Coastal road below a seafront promenade) | a railing corner in the foreground | aktif |  |
| boş (teras @ Coastal road below a seafront promenade) | nothing in the foreground | aktif |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| gulf_metropolis | a seafront district with glass towers behind palm-lined boulevards, sand-colored low buildings | aktif |  |
| north_african_coast | a seafront district with sand-colored flat-roofed buildings, narrow streets, cloth awnings, arched doorways | aktif |  |
| us_coastal_town | a seafront district with wide asphalt roads, low wooden and brick houses, power lines | aktif |  |
| north_european_seaside | a seafront district with brick terraced houses, narrow streets, bay windows, wet slate roofs | aktif |  |
| riviera | a seafront district with cream stone buildings with shuttered windows, cobbled streets, plane trees | aktif |  |
| east_asian_coast | a seafront district with dense mid-rise apartment blocks with air-conditioners and tangled wires, narrow lanes | aktif |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A towering brown tidal wave thick with debris crashes over the waterfront onto the coastal street. | aktif | 13 Eki 247K |
| B | A towering wave rolls over the harbor breakwater and slams onto the coastal road, shoving parked cars in the first second. | PASİF |  |
| C | A foaming wall of seawater surges over the promenade and crashes into the street, sweeping benches and scooters ahead of it. | rotasyon dışı (deneme) |  |
| D | A giant wave explodes against the harbor wall and a white wall of water collapses onto the street in front of the seafront houses. | rotasyon dışı (deneme) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | driving rain and wind | aktif |  |
| L2 | a dark storm light | aktif |  |
| L3 | stormy late-afternoon light | aktif |  |
| L4 | strong gusting wind | aktif |  |
| L5 | pale early-morning light over a grey sea | rotasyon dışı |  |
| L6 | bright midday sun over a churning sea | rotasyon dışı |  |
| L7 | low orange sunset light over the sea | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| T1 | the {vehicle} is lifted and flung against a storefront | PASİF |  |
| T2 | the {vehicle} is carried down the street by the surge | aktif |  |
| T3 | the {vehicle} is slammed into the car parked ahead and both are shoved along | aktif |  |
| T4 | the {vehicle} is hurled onto the roof of a parked car, crushing it flat | PASİF |  |
| T5 | the {vehicle} tips over onto its side in the churning water | aktif | 13 Eki 247K (aday) |
| T6 | the {vehicle} is pushed onto the sidewalk and slams into a lamppost | PASİF |  |
| T7 | the {vehicle} is carried backwards down the street, bumping parked cars | aktif | 13 Eki 247K (aday) |
| T8 | the {vehicle} is driven into the front of a house and the porch collapses onto it | aktif |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| W1 | a row of parked vehicles is ripped loose one by one and washed away | aktif | 13 Eki 247K (aday) |
| W2 | a lamppost topples into the surge | PASİF |  |
| W3 | a street tree is uprooted and carried along | aktif |  |
| W4 | a roadside kiosk is torn off its base and swept away | aktif |  |
| W5 | a city bus is shoved sideways by the surge | aktif | 13 Eki 247K (aday) |
| W6 | a low wall collapses into the water | PASİF |  |
| W8 | a dumpster tumbles down the street and smashes into a parked car | PASİF |  |
| W9 | the surge rams a floating car through the front of a seafront café and its wall caves in | PASİF |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| I1 | {N} pedestrians run from the wave toward the buildings. | aktif (birebir) |  |
| I2 | {N} people run inland as the wave hits. | aktif (birebir) |  |
| I3 | {N} people sprint into the entrance of a seafront hotel. | DENEME (birebir) |  |
| I4 | {N} pedestrians run up the stairs of an apartment building. | DENEME (birebir) |  |
| I5 | {N} residents sprint for the stairway of a parking garage. | DENEME (birebir) |  |
| I6 | {N} people run for the doorway of a seafront café. | DENEME (birebir) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| blue sedan | blue sedan | aktif |  |
| green delivery van | green delivery van | aktif |  |
| orange box truck | orange box truck | aktif |  |
| orange delivery truck | orange delivery truck | aktif |  |
| red SUV | red SUV | aktif |  |
| yellow pickup truck | yellow pickup truck | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Coastal road below a seafront promenade | teras @ Coastal road below a seafront promenade mod B [ön plan: teras_korkuluk, boş]; balkon @ Coastal street of low shopfronts [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Coastal street of low shopfronts | balkon @ Coastal street of low shopfronts mod B [ön plan: korkuluk, boş]; teras @ Coastal road below a seafront promenade [ön plan: teras_korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Coastal avenue behind a seawall | balkon @ Coastal street of low shopfronts [ön plan: korkuluk, boş]; teras @ Coastal road below a seafront promenade [ön plan: teras_korkuluk, boş] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 3 | 3 |  |
| Kadraj | 4 | 2 | ⚠ 3'ten az |
| Ön plan | 8 | 3 |  |
| Ortam | 6 | 0 |  |
| Açılış (0-4 sn) | 1 | 1 | ⚠ 3'ten az |
| Işık | 4 | 4 |  |
| Orta (4-9 sn) | 5 | 5 |  |
| Final (9-15 sn) | 4 | 4 |  |
| İnsan cümlesi | 6 | 6 |  |
| Araç | 6 | 6 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Coastal avenue behind a seawall | balkon | boş | north_african_coast | A | T5 | W3 | I2 | red SUV |
| 2 | Coastal road below a seafront promenade | teras | teras_korkuluk | gulf_metropolis | A | T7 | W1 | I1 | yellow pickup truck |
| 3 | Coastal street of low shopfronts | balkon | boş | north_european_seaside | A | T8 | W4 | I2 | green delivery van |
| 4 | Coastal avenue behind a seawall | teras | teras_korkuluk | us_coastal_town | A | T3 | W5 | I3 | blue sedan |
| 5 | Coastal road below a seafront promenade | teras | boş | east_asian_coast | A | T2 | W3 | I1 | red SUV |
| 6 | Coastal street of low shopfronts | balkon | korkuluk | riviera | A | T5 | W1 | I2 | yellow pickup truck |
| 7 | Coastal avenue behind a seawall | teras | boş | north_african_coast | A | T7 | W4 | I1 | green delivery van |
| 8 | Coastal road below a seafront promenade | teras | teras_korkuluk | gulf_metropolis | A | T8 | W5 | I4 | red SUV |
| 9 | Coastal street of low shopfronts | balkon | boş | north_european_seaside | A | T3 | W3 | I2 | orange delivery truck |
| 10 | Coastal avenue behind a seawall | teras | teras_korkuluk | us_coastal_town | A | T5 | W1 | I6 | yellow pickup truck |
| 11 | Coastal road below a seafront promenade | teras | boş | east_asian_coast | A | T2 | W4 | I1 | red SUV |
| 12 | Coastal street of low shopfronts | balkon | korkuluk | riviera | A | T7 | W5 | I2 | green delivery van |
| 13 | Coastal avenue behind a seawall | teras | teras_korkuluk | north_african_coast | A | T8 | W3 | I5 | yellow pickup truck |
| 14 | Coastal road below a seafront promenade | teras | boş | gulf_metropolis | A | T3 | W1 | I1 | blue sedan |
| 15 | Coastal street of low shopfronts | balkon | korkuluk | north_european_seaside | A | T5 | W4 | I2 | red SUV |
| 16 | Coastal avenue behind a seawall | teras | boş | us_coastal_town | A | T2 | W5 | I3 | yellow pickup truck |
| 17 | Coastal road below a seafront promenade | balkon | korkuluk | east_asian_coast | A | T7 | W3 | I1 | orange box truck |
| 18 | Coastal street of low shopfronts | balkon | boş | riviera | A | T3 | W1 | I2 | red SUV |
| 19 | Coastal avenue behind a seawall | teras | teras_korkuluk | north_african_coast | A | T8 | W4 | I1 | green delivery van |
| 20 | Coastal road below a seafront promenade | teras | boş | gulf_metropolis | A | T5 | W5 | I2 | yellow pickup truck |
| 21 | Coastal street of low shopfronts | balkon | korkuluk | north_european_seaside | A | T2 | W3 | I1 | orange delivery truck |
| 22 | Coastal avenue behind a seawall | teras | teras_korkuluk | us_coastal_town | A | T7 | W1 | I2 | red SUV |
| 23 | Coastal road below a seafront promenade | teras | boş | east_asian_coast | A | T3 | W4 | I1 | green delivery van |
| 24 | Coastal street of low shopfronts | balkon | korkuluk | riviera | A | T8 | W5 | I2 | yellow pickup truck |
| 25 | Coastal avenue behind a seawall | teras | boş | north_african_coast | A | T5 | W3 | I6 | red SUV |
| 26 | Coastal road below a seafront promenade | teras | teras_korkuluk | gulf_metropolis | A | T7 | W1 | I1 | blue sedan |
| 27 | Coastal street of low shopfronts | balkon | korkuluk | north_european_seaside | A | T2 | W4 | I3 | orange delivery truck |
| 28 | Coastal avenue behind a seawall | teras | teras_korkuluk | us_coastal_town | A | T3 | W5 | I2 | yellow pickup truck |
| 29 | Coastal road below a seafront promenade | teras | boş | east_asian_coast | A | T8 | W3 | I1 | green delivery van |
| 30 | Coastal street of low shopfronts | balkon | korkuluk | riviera | A | T5 | W1 | I2 | red SUV |
| 31 | Coastal avenue behind a seawall | teras | boş | north_african_coast | A | T7 | W4 | I1 | yellow pickup truck |
| 32 | Coastal road below a seafront promenade | teras | teras_korkuluk | gulf_metropolis | A | T2 | W5 | I2 | blue sedan |
| 33 | Coastal street of low shopfronts | balkon | boş | north_european_seaside | A | T3 | W3 | I1 | green delivery van |
| 34 | Coastal avenue behind a seawall | teras | teras_korkuluk | us_coastal_town | A | T5 | W1 | I5 | red SUV |
| 35 | Coastal road below a seafront promenade | balkon | boş | east_asian_coast | A | T8 | W4 | I2 | orange box truck |
| 36 | Coastal street of low shopfronts | balkon | korkuluk | riviera | A | T7 | W5 | I6 | yellow pickup truck |
| 37 | Coastal avenue behind a seawall | teras | boş | north_african_coast | A | T2 | W3 | I1 | red SUV |
| 38 | Coastal road below a seafront promenade | teras | teras_korkuluk | gulf_metropolis | A | T3 | W1 | I2 | blue sedan |
| 39 | Coastal street of low shopfronts | balkon | korkuluk | north_european_seaside | A | T5 | W4 | I1 | orange delivery truck |
| 40 | Coastal avenue behind a seawall | teras | boş | us_coastal_town | A | T8 | W5 | I2 | yellow pickup truck |


---

## Kül bulutu ve dev dalga — değişiklikten SONRA

### (sonra) Pyroclastic cloud races down into a village street

Hit (100K+) eşleşmesi: 13 Eki 2,13M ← 13 Eki 11:23 · 25 Eki 102K ← 17 Eki 14:13

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Hillside terrace facing the erupting volcano | on a hillside terrace above the houses | aktif | 13 Eki 2,13M |
| Rooftop terrace facing the erupting volcano | on a rooftop terrace across the street | aktif | 25 Eki 102K |
| Balcony of a village house facing the erupting volcano | on a house balcony across the street | PASİF/rotasyon dışı |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| K_V @ kütüphane | Filmed from a high rooftop terrace at the edge of the town, wide angle, the entire volcano from its base to its summit filling the upper half of the frame directly behind the houses, the town below in the lower half; the camera never pans, turns or follows. One continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| balkon @ Balcony of a village house facing the erupting volcano | Handheld footage filmed on a house balcony across the street, high vantage over a street of colorful painted stucco houses with balconies right at the foot of the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| çatı @ Rooftop terrace facing the erupting volcano | Handheld footage filmed on a rooftop terrace across the street, high vantage over a street of colorful painted stucco houses with balconies right at the foot of the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| tepe @ Hillside terrace facing the erupting volcano | Handheld footage filmed on a hillside terrace above the houses, high vantage over a street of colorful painted stucco houses with balconies right at the foot of the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| pencere @ kütüphane | Handheld footage filmed through an open upper-floor window, high vantage over a street of colorful painted stucco houses with balconies right at the foot of the volcano toward the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, the edge of the open window frame at one side; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| korkuluk (balkon @ Balcony of a village house facing the erupting volcano) | a railing corner in the foreground | rotasyon dışı |  |
| boş (balkon @ Balcony of a village house facing the erupting volcano) | nothing in the foreground | rotasyon dışı |  |
| korkuluk (çatı @ Rooftop terrace facing the erupting volcano) | a railing corner in the foreground | aktif |  |
| boş (çatı @ Rooftop terrace facing the erupting volcano) | nothing in the foreground | aktif |  |
| korkuluk (tepe @ Hillside terrace facing the erupting volcano) | a railing corner in the foreground | aktif |  |
| boş (tepe @ Hillside terrace facing the erupting volcano) | nothing in the foreground | aktif |  |
| pencere (pencere @ kütüphane) | the open window frame at one side | rotasyon dışı |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| pastel_town | a street of colorful painted stucco houses with balconies right at the foot of the volcano | aktif (ağırlık 2) |  |
| hillside_town | a wide hillside-town street of stone and painted houses right at the foot of the volcano | aktif (ağırlık 2) |  |
| suburb | a suburban street of detached houses, garages and palm trees right at the foot of the volcano | aktif (ağırlık 1) |  |
| mountain_village | a village street of wooden and stone houses among trees right at the foot of the volcano | aktif (ağırlık 1) |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A pyroclastic cloud races down the volcano’s flank and slams into the street. | aktif | 13 Eki 2,13M; 25 Eki 102K |
| B | The ash cloud races down the volcano's slope and swallows the highest houses on the slope in the first second. | PASİF |  |
| C | A blast of hot air ahead of the cloud bends the trees, and the grey wall of ash surges into the street right behind it. | PASİF |  |
| D | The ash cloud spreads across the valley and engulfs the houses on both sides of the street at once. | PASİF |  |
| E | The whole volcano looms directly behind the town, its summit crater erupting a towering column of black ash, and part of the column collapses into a churning gray ash cloud that pours down the slope toward the first houses. | aktif |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | ash-grey sky lit orange by a distant eruption plume | aktif | 13 Eki 2,13M |
| L2 | warm orange dusk sky glowing from the eruption | aktif |  |
| L3 | bright hazy daylight under a dark ash sky | rotasyon dışı |  |
| L4 | pink-orange dawn light under a dark ash sky | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| P1 | the cloud front slams into the houses across the street and tears the balconies off their facades | PASİF |  |
| P2 | the cloud snaps a row of street trees and power poles and they crash across the street | aktif | 13 Eki 2,13M; 25 Eki 102K |
| P3 | the cloud rips roof tiles off the rooftops and hurls them down the street | PASİF |  |
| P4 | the cloud front flattens a row of palm trees and hurls their fronds ahead of it | aktif |  |
| P5 | the cloud front shoves a stone garden wall over and rolls on across the street | PASİF |  |
| P6 | the cloud front rips the corrugated roofs off a row of low sheds and sends them flying | PASİF |  |
| P7 | the ash cloud reaches the first houses at the foot of the slope and swallows them one by one | aktif |  |
| P8 | the ash cloud pours over the edge of the town and buries the parked cars along the first street in gray ash | aktif |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Q1 | a house wall across the street collapses as the cloud engulfs it | aktif | 13 Eki 2,13M |
| Q2 | the cloud engulfs a whole block and the upper-floor windows burst outward in a shower of glass | PASİF |  |
| Q3 | a chimney topples and crashes through a roof as the cloud passes over | aktif |  |
| Q4 | the cloud hits a hillside retaining wall and the wall gives way, boulders tumbling into the street | aktif |  |
| Q5 | the cloud blasts the front off a shop building and the brickwork falls into the street | aktif | 25 Eki 102K |
| Q6 | the cloud flips a row of parked cars and piles them against a house wall | PASİF |  |
| Q7 | the cloud front tears the roof off the house right below before swallowing it | DENEME |  |
| Q8 | the cloud front knocks down the front wall of the two-storey house across the street, then swallows it | DENEME |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| P1 | {N} people sprint into the open doorway of the house right below. | DENEME (birebir) |  |
| P2 | {N} people run for the garage of a house across the street below. | DENEME (birebir) |  |
| P3 | {N} people sprint down the street toward a stone archway below. | DENEME (birebir) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| - | araçsız olay | - |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Hillside terrace facing the erupting volcano | K_V @ kütüphane [ön plan: -]; çatı @ Rooftop terrace facing the erupting volcano [ön plan: korkuluk, boş]; tepe @ Hillside terrace facing the erupting volcano [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Rooftop terrace facing the erupting volcano | K_V @ kütüphane [ön plan: -]; çatı @ Rooftop terrace facing the erupting volcano [ön plan: korkuluk, boş]; tepe @ Hillside terrace facing the erupting volcano [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Balcony of a village house facing the erupting volcano | K_V @ kütüphane [ön plan: -]; çatı @ Rooftop terrace facing the erupting volcano [ön plan: korkuluk, boş]; tepe @ Hillside terrace facing the erupting volcano [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 2 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Kadraj | 3 | 3 |  |
| Ön plan | 4 | 2 | ⚠ 3'ten az |
| Ortam | 4 | 4 |  |
| Açılış (0-4 sn) | 2 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Işık | 2 | 2 | ⚠ 3'ten az |
| Orta (4-9 sn) | 4 | 4 |  |
| Final (9-15 sn) | 6 | 6 |  |
| İnsan cümlesi | 3 | 3 |  |
| Araç | 0 | 0 | araçsız |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Hillside terrace facing the erupting volcano | K_V | - | mountain_village | E | P8 | Q4 | P1 | - |
| 2 | Rooftop terrace facing the erupting volcano | tepe | korkuluk | pastel_town | A | P4 | Q1 | P3 | - |
| 3 | Hillside terrace facing the erupting volcano | K_V | - | hillside_town | E | P2 | Q7 | P2 | - |
| 4 | Rooftop terrace facing the erupting volcano | çatı | boş | suburb | A | P7 | Q4 | P1 | - |
| 5 | Hillside terrace facing the erupting volcano | K_V | - | mountain_village | E | P4 | Q3 | P3 | - |
| 6 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | P8 | Q1 | P2 | - |
| 7 | Hillside terrace facing the erupting volcano | tepe | boş | pastel_town | E | P7 | Q8 | P1 | - |
| 8 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | P2 | Q4 | P3 | - |
| 9 | Hillside terrace facing the erupting volcano | K_V | - | hillside_town | E | P8 | Q3 | P2 | - |
| 10 | Rooftop terrace facing the erupting volcano | tepe | korkuluk | pastel_town | A | P7 | Q1 | P1 | - |
| 11 | Hillside terrace facing the erupting volcano | çatı | korkuluk | suburb | E | P4 | Q4 | P3 | - |
| 12 | Rooftop terrace facing the erupting volcano | K_V | - | hillside_town | A | P8 | Q8 | P2 | - |
| 13 | Hillside terrace facing the erupting volcano | tepe | korkuluk | mountain_village | E | P2 | Q3 | P1 | - |
| 14 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | A | P7 | Q5 | P3 | - |
| 15 | Hillside terrace facing the erupting volcano | K_V | - | hillside_town | E | P8 | Q4 | P2 | - |
| 16 | Rooftop terrace facing the erupting volcano | çatı | boş | suburb | A | P2 | Q1 | P1 | - |
| 17 | Hillside terrace facing the erupting volcano | tepe | korkuluk | mountain_village | E | P7 | Q3 | P3 | - |
| 18 | Rooftop terrace facing the erupting volcano | K_V | - | hillside_town | A | P8 | Q5 | P2 | - |
| 19 | Hillside terrace facing the erupting volcano | tepe | korkuluk | pastel_town | E | P4 | Q1 | P1 | - |
| 20 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | P7 | Q4 | P3 | - |
| 21 | Hillside terrace facing the erupting volcano | tepe | korkuluk | suburb | E | P2 | Q5 | P2 | - |
| 22 | Rooftop terrace facing the erupting volcano | çatı | boş | pastel_town | A | P4 | Q8 | P1 | - |
| 23 | Hillside terrace facing the erupting volcano | K_V | - | hillside_town | E | P8 | Q1 | P3 | - |
| 24 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | suburb | A | P2 | Q4 | P2 | - |
| 25 | Hillside terrace facing the erupting volcano | K_V | - | pastel_town | E | P7 | Q7 | P1 | - |
| 26 | Rooftop terrace facing the erupting volcano | tepe | korkuluk | hillside_town | A | P4 | Q5 | P3 | - |
| 27 | Hillside terrace facing the erupting volcano | K_V | - | mountain_village | E | P8 | Q3 | P2 | - |
| 28 | Rooftop terrace facing the erupting volcano | tepe | korkuluk | pastel_town | A | P7 | Q1 | P1 | - |
| 29 | Hillside terrace facing the erupting volcano | çatı | korkuluk | hillside_town | E | P4 | Q4 | P3 | - |
| 30 | Rooftop terrace facing the erupting volcano | K_V | - | mountain_village | A | P2 | Q8 | P2 | - |
| 31 | Hillside terrace facing the erupting volcano | çatı | korkuluk | pastel_town | E | P7 | Q5 | P1 | - |
| 32 | Rooftop terrace facing the erupting volcano | K_V | - | hillside_town | A | P8 | Q4 | P3 | - |
| 33 | Hillside terrace facing the erupting volcano | tepe | korkuluk | mountain_village | E | P4 | Q3 | P2 | - |
| 34 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | suburb | A | P2 | Q1 | P1 | - |
| 35 | Hillside terrace facing the erupting volcano | tepe | korkuluk | hillside_town | E | P8 | Q5 | P3 | - |
| 36 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | P7 | Q4 | P2 | - |
| 37 | Hillside terrace facing the erupting volcano | K_V | - | pastel_town | E | P4 | Q7 | P1 | - |
| 38 | Rooftop terrace facing the erupting volcano | tepe | korkuluk | suburb | A | P2 | Q5 | P3 | - |
| 39 | Hillside terrace facing the erupting volcano | K_V | - | hillside_town | E | P7 | Q3 | P2 | - |
| 40 | Rooftop terrace facing the erupting volcano | tepe | korkuluk | pastel_town | A | P4 | Q1 | P1 | - |

### (sonra) Tidal wave surges over a coastal city street

Hit (100K+) eşleşmesi: 24 Eyl 1,42M ← 24 Eyl (yapılandırılmış hat öncesi, kayıt yok) (yüksek balkon, mod A) · 3 Eki 135K ← 1 Eki / 3 Eki (beat'siz) (korkuluk ön planı: promenat (aday)) · 13 Eki 247K ← aday: 4 Eki 11:06 T7+W1 (seawall) ya da 4 Eki 10:16 T5+W5 (seawall) (açıklama 'cleared the sea wall... cars were swept away': 11:06'ya yakın, kesin değil)

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Coastal road below a seafront promenade | at the railing of a raised seafront promenade, looking down at the coastal road | aktif |  |
| Coastal street of low shopfronts | on a second-floor balcony, looking down at the coastal street | aktif |  |
| Coastal avenue behind a seawall | on top of the seawall, looking down at the coastal avenue | aktif |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| K_R1 @ kütüphane | Filmed from the flat rooftop of a six-story apartment block right on the seafront, high vantage, wide angle, the whole coastal street and the sea behind it in frame; the camera never pans, turns or follows. A low parapet edge in the foreground, one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| K_R2 @ kütüphane | Filmed from a top-floor window of a tall seafront hotel, high vantage, wide angle, looking straight down the coastal street toward the sea; the camera never pans, turns or follows. The open window frame at one side, one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| K_R3 @ kütüphane | Filmed from a high rooftop terrace on the hillside just above the seafront, high vantage, wide angle, the coastal street and the apartment blocks below in frame; the camera never pans, turns or follows. A railing corner in the foreground, one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| parapet (K_R1 @ kütüphane) | a low parapet edge in the foreground | aktif |  |
| pencere (K_R2 @ kütüphane) | the open window frame at one side | aktif |  |
| teras_korkuluk (K_R3 @ kütüphane) | a railing corner in the foreground | aktif |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| gulf_metropolis | a seafront district with glass towers behind palm-lined boulevards, sand-colored low buildings | aktif |  |
| north_african_coast | a seafront district with sand-colored flat-roofed buildings, narrow streets, cloth awnings, arched doorways | aktif |  |
| us_coastal_town | a seafront district with wide asphalt roads, low wooden and brick houses, power lines | aktif |  |
| north_european_seaside | a seafront district with brick terraced houses, narrow streets, bay windows, wet slate roofs | aktif |  |
| riviera | a seafront district with cream stone buildings with shuttered windows, cobbled streets, plane trees | aktif |  |
| east_asian_coast | a seafront district with dense mid-rise apartment blocks with air-conditioners and tangled wires, narrow lanes | aktif |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A towering brown tidal wave thick with debris crashes over the waterfront onto the coastal street. | aktif | 13 Eki 247K |
| B | A towering wave rolls over the harbor breakwater and slams onto the coastal road, shoving parked cars in the first second. | PASİF |  |
| C | A foaming wall of seawater surges over the promenade and crashes into the street, sweeping benches and scooters ahead of it. | rotasyon dışı (deneme) |  |
| D | A giant wave explodes against the harbor wall and a white wall of water collapses onto the street in front of the seafront houses. | rotasyon dışı (deneme) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | driving rain and wind | aktif |  |
| L2 | a dark storm light | aktif |  |
| L3 | stormy late-afternoon light | aktif |  |
| L4 | strong gusting wind | aktif |  |
| L5 | pale early-morning light over a grey sea | rotasyon dışı |  |
| L6 | bright midday sun over a churning sea | rotasyon dışı |  |
| L7 | low orange sunset light over the sea | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| T1 | the {vehicle} is lifted and flung against a storefront | PASİF |  |
| T2 | the {vehicle} is carried down the street by the surge | aktif |  |
| T3 | the {vehicle} is slammed into the car parked ahead and both are shoved along | aktif |  |
| T4 | the {vehicle} is hurled onto the roof of a parked car, crushing it flat | PASİF |  |
| T5 | the {vehicle} tips over onto its side in the churning water | aktif | 13 Eki 247K (aday) |
| T6 | the {vehicle} is pushed onto the sidewalk and slams into a lamppost | PASİF |  |
| T7 | the {vehicle} is carried backwards down the street, bumping parked cars | aktif | 13 Eki 247K (aday) |
| T8 | the {vehicle} is driven into the front of a house and the porch collapses onto it | aktif |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| W1 | a row of parked vehicles is ripped loose one by one and washed away | aktif | 13 Eki 247K (aday) |
| W2 | a lamppost topples into the surge | PASİF |  |
| W3 | a street tree is uprooted and carried along | PASİF |  |
| W4 | a roadside kiosk is torn off its base and swept away | PASİF |  |
| W5 | a city bus is shoved sideways by the surge | aktif | 13 Eki 247K (aday) |
| W6 | a low wall collapses into the water | PASİF |  |
| W8 | a dumpster tumbles down the street and smashes into a parked car | PASİF |  |
| W9 | the surge rams a floating car through the front of a seafront café and its wall caves in | PASİF |  |
| W10 | the wave smashes through the front wall of a seafront house and pours inside | aktif |  |
| W11 | the surge swallows the ground floors of a row of shopfronts and a roof caves in | aktif |  |
| W12 | the surge tears a wooden beach café off its foundations and smashes it against the apartment blocks | aktif |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| I1 | {N} pedestrians run from the wave toward the buildings. | aktif (birebir) |  |
| I2 | {N} people run inland as the wave hits. | PASİF (birebir) |  |
| I3 | {N} people sprint into the entrance of a seafront hotel. | DENEME (birebir) |  |
| I4 | {N} pedestrians run up the stairs of an apartment building. | DENEME (birebir) |  |
| I5 | {N} residents sprint for the stairway of a parking garage. | DENEME (birebir) |  |
| I6 | {N} people run for the doorway of a seafront café. | DENEME (birebir) |  |
| I7 | {N} people run up the street away from the sea toward the apartment entrances. | aktif (birebir) |  |
| I8 | {N} people run up the stairs of an apartment building. | aktif (birebir) |  |
| I9 | {N} people run up the side lane toward the hill behind the town. | aktif (birebir) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| blue sedan | blue sedan | aktif |  |
| green delivery van | green delivery van | aktif |  |
| orange box truck | orange box truck | aktif |  |
| orange delivery truck | orange delivery truck | aktif |  |
| red SUV | red SUV | aktif |  |
| yellow pickup truck | yellow pickup truck | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Coastal road below a seafront promenade | K_R1 @ kütüphane [ön plan: parapet]; K_R2 @ kütüphane [ön plan: pencere]; K_R3 @ kütüphane [ön plan: teras_korkuluk] | hayır (kadraj ekseni seçer) |
| Coastal street of low shopfronts | K_R1 @ kütüphane [ön plan: parapet]; K_R2 @ kütüphane [ön plan: pencere]; K_R3 @ kütüphane [ön plan: teras_korkuluk] | hayır (kadraj ekseni seçer) |
| Coastal avenue behind a seawall | K_R1 @ kütüphane [ön plan: parapet]; K_R2 @ kütüphane [ön plan: pencere]; K_R3 @ kütüphane [ön plan: teras_korkuluk] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 3 | 3 |  |
| Kadraj | 3 | 3 |  |
| Ön plan | 3 | 3 |  |
| Ortam | 6 | 0 |  |
| Açılış (0-4 sn) | 1 | 1 | ⚠ 3'ten az |
| Işık | 4 | 4 |  |
| Orta (4-9 sn) | 5 | 5 |  |
| Final (9-15 sn) | 5 | 5 |  |
| İnsan cümlesi | 8 | 8 |  |
| Araç | 6 | 6 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Coastal avenue behind a seawall | K_R1 | parapet | north_african_coast | A | T3 | W12 | I9 | red SUV |
| 2 | Coastal road below a seafront promenade | K_R3 | teras_korkuluk | gulf_metropolis | A | T5 | W10 | I1 | yellow pickup truck |
| 3 | Coastal street of low shopfronts | K_R1 | parapet | north_european_seaside | A | T7 | W11 | I7 | green delivery van |
| 4 | Coastal avenue behind a seawall | K_R3 | teras_korkuluk | us_coastal_town | A | T8 | W5 | I3 | blue sedan |
| 5 | Coastal road below a seafront promenade | K_R1 | parapet | east_asian_coast | A | T3 | W1 | I8 | red SUV |
| 6 | Coastal street of low shopfronts | K_R2 | pencere | riviera | A | T2 | W10 | I9 | yellow pickup truck |
| 7 | Coastal avenue behind a seawall | K_R3 | teras_korkuluk | north_african_coast | A | T7 | W12 | I1 | green delivery van |
| 8 | Coastal road below a seafront promenade | K_R2 | pencere | gulf_metropolis | A | T5 | W5 | I4 | red SUV |
| 9 | Coastal street of low shopfronts | K_R1 | parapet | north_european_seaside | A | T3 | W11 | I8 | orange delivery truck |
| 10 | Coastal avenue behind a seawall | K_R2 | pencere | us_coastal_town | A | T2 | W10 | I6 | yellow pickup truck |
| 11 | Coastal road below a seafront promenade | K_R1 | parapet | east_asian_coast | A | T7 | W1 | I7 | red SUV |
| 12 | Coastal street of low shopfronts | K_R3 | teras_korkuluk | riviera | A | T5 | W12 | I9 | green delivery van |
| 13 | Coastal avenue behind a seawall | K_R2 | pencere | north_african_coast | A | T3 | W5 | I5 | yellow pickup truck |
| 14 | Coastal road below a seafront promenade | K_R3 | teras_korkuluk | gulf_metropolis | A | T8 | W11 | I1 | blue sedan |
| 15 | Coastal street of low shopfronts | K_R1 | parapet | north_european_seaside | A | T7 | W10 | I8 | red SUV |
| 16 | Coastal avenue behind a seawall | K_R2 | pencere | us_coastal_town | A | T5 | W1 | I3 | yellow pickup truck |
| 17 | Coastal road below a seafront promenade | K_R1 | parapet | east_asian_coast | A | T2 | W12 | I7 | orange box truck |
| 18 | Coastal street of low shopfronts | K_R2 | pencere | riviera | A | T8 | W5 | I9 | red SUV |
| 19 | Coastal avenue behind a seawall | K_R3 | teras_korkuluk | north_african_coast | A | T3 | W10 | I1 | green delivery van |
| 20 | Coastal road below a seafront promenade | K_R2 | pencere | gulf_metropolis | A | T5 | W11 | I8 | yellow pickup truck |
| 21 | Coastal street of low shopfronts | K_R1 | parapet | north_european_seaside | A | T7 | W12 | I9 | orange delivery truck |
| 22 | Coastal avenue behind a seawall | K_R2 | pencere | us_coastal_town | A | T2 | W5 | I7 | red SUV |
| 23 | Coastal road below a seafront promenade | K_R3 | teras_korkuluk | east_asian_coast | A | T3 | W1 | I1 | green delivery van |
| 24 | Coastal street of low shopfronts | K_R1 | parapet | riviera | A | T5 | W10 | I8 | yellow pickup truck |
| 25 | Coastal avenue behind a seawall | K_R3 | teras_korkuluk | north_african_coast | A | T8 | W12 | I6 | red SUV |
| 26 | Coastal road below a seafront promenade | K_R2 | pencere | gulf_metropolis | A | T2 | W11 | I9 | blue sedan |
| 27 | Coastal street of low shopfronts | K_R1 | parapet | north_european_seaside | A | T7 | W5 | I3 | orange delivery truck |
| 28 | Coastal avenue behind a seawall | K_R2 | pencere | us_coastal_town | A | T5 | W1 | I7 | yellow pickup truck |
| 29 | Coastal road below a seafront promenade | K_R3 | teras_korkuluk | east_asian_coast | A | T3 | W12 | I1 | green delivery van |
| 30 | Coastal street of low shopfronts | K_R2 | pencere | riviera | A | T2 | W10 | I8 | red SUV |
| 31 | Coastal avenue behind a seawall | K_R1 | parapet | north_african_coast | A | T7 | W11 | I9 | yellow pickup truck |
| 32 | Coastal road below a seafront promenade | K_R3 | teras_korkuluk | gulf_metropolis | A | T5 | W5 | I7 | blue sedan |
| 33 | Coastal street of low shopfronts | K_R1 | parapet | north_european_seaside | A | T3 | W1 | I1 | green delivery van |
| 34 | Coastal avenue behind a seawall | K_R3 | teras_korkuluk | us_coastal_town | A | T2 | W12 | I5 | red SUV |
| 35 | Coastal road below a seafront promenade | K_R2 | pencere | east_asian_coast | A | T8 | W11 | I8 | orange box truck |
| 36 | Coastal street of low shopfronts | K_R1 | parapet | riviera | A | T7 | W10 | I6 | yellow pickup truck |
| 37 | Coastal avenue behind a seawall | K_R2 | pencere | north_african_coast | A | T3 | W5 | I9 | red SUV |
| 38 | Coastal road below a seafront promenade | K_R3 | teras_korkuluk | gulf_metropolis | A | T5 | W12 | I7 | blue sedan |
| 39 | Coastal street of low shopfronts | K_R1 | parapet | north_european_seaside | A | T2 | W11 | I1 | orange delivery truck |
| 40 | Coastal avenue behind a seawall | K_R3 | teras_korkuluk | us_coastal_town | A | T7 | W1 | I8 | yellow pickup truck |


### Örnek tam promptlar (kod yedeği)

#### Pyroclastic cloud races down into a village street — tohum 18 (E, K_V, P7+Q4, hillside_town; 198 kelime, 1116 karakter)

0-4s: The whole volcano looms directly behind the town, its summit crater erupting a towering column of black ash, and part of the column collapses into a churning gray ash cloud that pours down the slope toward the first houses. Four people sprint into the open doorway of the house right below. 4-9s: The ash cloud reaches the first houses at the foot of the slope and swallows them one by one. 9-15s: The cloud hits a hillside retaining wall and the wall gives way, boulders tumbling into the street. Filmed from a high rooftop terrace at the edge of the town, wide angle, the entire volcano from its base to its summit filling the upper half of the frame directly behind the houses, the town below in the lower half; the camera never pans, turns or follows. One continuous shot, no zoom, no cuts, no person or face close to the camera. Setting: a wide hillside-town street of stone and painted houses, no readable signs, text or flags. All people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI. Everything moves in real time, never in slow motion, people run at full speed.

#### Pyroclastic cloud races down into a village street — tohum 4 (E, tepe, P8+Q8, pastel_town; 197 kelime, 1142 karakter)

0-4s: The whole volcano looms directly behind the town, its summit crater erupting a towering column of black ash, and part of the column collapses into a churning gray ash cloud that pours down the slope toward the first houses. Five people sprint down the street toward a stone archway below. 4-9s: The ash cloud pours over the edge of the town and buries the parked cars along the first street in gray ash. 9-15s: The cloud front knocks down the front wall of the two-storey house across the street, then swallows it. Handheld footage filmed on a hillside terrace above the houses, high vantage over a street of colorful painted stucco houses with balconies right at the foot of the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. All people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI. Everything moves in real time, never in slow motion, people run at full speed. No readable signs, text or flags.

#### Tidal wave surges over a coastal city street — tohum 1 (A, K_R1, T3+W12, north_african_coast; 175 kelime, 1043 karakter)

0-4s: A towering brown tidal wave thick with debris crashes over the waterfront onto the coastal street. Six people run up the side lane toward the hill behind the town. 4-9s: The red SUV is slammed into the car parked ahead and both are shoved along. 9-15s: The surge tears a wooden beach café off its foundations and smashes it against the apartment blocks. Filmed from the flat rooftop of a six-story apartment block right on the seafront, high vantage, wide angle, the whole coastal street and the sea behind it in frame; the camera never pans, turns or follows. A low parapet edge in the foreground, one continuous shot, no zoom, no cuts, no person or face close to the camera. All people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI. Everything moves in real time, never in slow motion, people run at full speed. Setting: a seafront district with sand-colored flat-roofed buildings, narrow streets, cloth awnings, arched doorways, in stormy late-afternoon light, no readable signs, text or flags.

#### Tidal wave surges over a coastal city street — tohum 5 (A, K_R2, T8+W11, riviera; 170 kelime, 985 karakter)

0-4s: A towering brown tidal wave thick with debris crashes over the waterfront onto the coastal street. Three people run up the stairs of an apartment building. 4-9s: The green delivery van is driven into the front of a house and the porch collapses onto it. 9-15s: The surge swallows the ground floors of a row of shopfronts and a roof caves in. Filmed from a top-floor window of a tall seafront hotel, high vantage, wide angle, looking straight down the coastal street toward the sea; the camera never pans, turns or follows. The open window frame at one side, one continuous shot, no zoom, no cuts, no person or face close to the camera. All people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI. Everything moves in real time, never in slow motion, people run at full speed. Setting: a seafront district with cream stone buildings with shuttered windows, cobbled streets, plane trees, in a dark storm light, no readable signs, text or flags.


---

## D — Kilitli 8 olay havuz denetimi (salt okuma, kodda değişiklik yok)

### Wall of flames sweeps into a hillside neighborhood

Hit (100K+) eşleşmesi: 19 Eki 3,02M ← 9 Eki 21:52 (kamera mod A (eye level, pans to follow): yüksek-sabit kuralı gereği rotasyonda değil) · 31 Eki 107K ← 31 Eki 09:44

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Balcony of a hillside house | on a balcony of a hillside house overlooking the street and the burning slope | aktif | 19 Eki 3,02M |
| Embankment above the village road | on a roadside embankment above the road | aktif | 31 Eki 107K |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| balkon @ Balcony of a hillside house mod A | Handheld footage filmed on a balcony of a hillside house overlooking the street and the burning slope, eye level, normal lens; slight hand shake, the camera pans to follow the wall of flames; no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| balkon @ Balcony of a hillside house mod B | Handheld footage filmed on a balcony of a hillside house, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the wall of flames always in frame, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ kütüphane | Handheld footage filmed on a flat rooftop above the burning slope, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the wall of flames always in frame, a low parapet edge in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif | 31 Eki 107K |
| tepe @ Embankment above the village road | Handheld footage filmed on a roadside embankment above the road, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the wall of flames always in frame, a few leaves at the frame edge; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| balkon @ Balcony of a hillside house | Handheld footage filmed on a balcony of a hillside house, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the wall of flames always in frame, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| tepe @ Embankment above the village road mod A | Handheld footage filmed on a roadside embankment above the road, eye level, normal lens; slight hand shake, the camera pans to follow the wall of flames; no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| tepe @ Embankment above the village road mod B | Handheld footage filmed on a roadside embankment above the road, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the wall of flames always in frame, a few leaves at the frame edge; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| korkuluk (balkon @ Balcony of a hillside house mod B) | a railing corner in the foreground | aktif |  |
| boş (balkon @ Balcony of a hillside house mod B) | nothing in the foreground | aktif |  |
| parapet (çatı @ kütüphane) | a low parapet edge in the foreground | aktif | 31 Eki 107K |
| boş (çatı @ kütüphane) | nothing in the foreground | aktif |  |
| yaprak (tepe @ Embankment above the village road) | a few leaves at the frame edge | rotasyon dışı |  |
| boş (tepe @ Embankment above the village road) | nothing in the foreground | rotasyon dışı |  |
| korkuluk (balkon @ Balcony of a hillside house) | a railing corner in the foreground | rotasyon dışı |  |
| boş (balkon @ Balcony of a hillside house) | nothing in the foreground | rotasyon dışı |  |
| yaprak (tepe @ Embankment above the village road mod B) | a few leaves at the frame edge | aktif |  |
| boş (tepe @ Embankment above the village road mod B) | nothing in the foreground | aktif |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | bugünkü görünüm (Setting satırı yok) | aktif | 31 Eki 107K |
| B | a hillside neighborhood of stucco houses with red tile roofs above dry brush slopes | aktif |  |
| C | a pine-forest edge of wooden cabins and log houses with gravel driveways | rotasyon dışı |  |
| D | a Mediterranean village of stone houses among olive groves and cypress trees | rotasyon dışı |  |
| E | a rural town of tin-roofed bungalows with verandas among eucalyptus trees | rotasyon dışı |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A towering wall of flames sweeps down the forested slope and slams into the edge of the neighborhood, igniting roofs and trees. | aktif | 19 Eki 3,02M; 31 Eki 107K |
| B | The wall of flames crests the ridge and slams into the first garden fences and trees of the neighborhood. | aktif |  |
| C | Wind-blown embers land on the first house of the neighborhood and its roof bursts into flames. | rotasyon dışı (deneme) |  |
| D | The flames jump across the road into the neighborhood and a parked car and the roadside bushes ignite at the same moment. | rotasyon dışı (deneme) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | hot dry wind and thick smoke haze | aktif |  |
| L2 | gusty dry wind under an orange smoky sky | aktif |  |
| L3 | heavy smoke and scorching still air | aktif |  |
| L4 | hazy early-morning light through drifting smoke | rotasyon dışı |  |
| L5 | harsh bright midday sun through the smoke | aktif | 31 Eki 107K |
| L6 | deep red sunset glow through the smoke | rotasyon dışı |  |
| L7 | dark smoke-filled overcast sky | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| K1 | the {vehicle} reverses hard down the road as a burning tree crashes across the lane in front of it | aktif |  |
| K2 | a burning tree crashes down onto the {vehicle} and crushes its roof | aktif | 31 Eki 107K |
| K5 | the {vehicle} U-turns in a cloud of smoke and speeds away as the flames close the road behind it | aktif | 19 Eki 3,02M |
| K7 | a wall of flames races up the slope and engulfs the first houses across the street | aktif |  |
| K8 | the flames leap across the street and ignite the roof of a house | aktif |  |
| K9 | the {vehicle} speeds past as the roof of a burning house collapses onto the road behind it | aktif |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | the flames leap onto the roofs of the nearest houses and ignite them one after another | aktif |  |
| L3 | the fire races across a garden, engulfing a parked trailer and a woodpile | aktif |  |
| L4 | the wall of flames swallows a row of trees along the road, sending sparks high into the air | aktif | 19 Eki 3,02M |
| L5 | a house roof catches fire and its tiles burst apart in the heat | aktif | 31 Eki 107K |
| L7 | a house across the street is engulfed and its roof collapses in a burst of flames | aktif |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| I1 | {N} residents run from the flames down the street. | kod yedeği (GPT yazar) |  |
| I2 | {N} villagers flee from the fire toward the road. | kod yedeği (GPT yazar) |  |
| I3 | {N} people sprint away from the flames. | kod yedeği (GPT yazar) |  |
| I4 | {N} residents scramble downhill away from the fire. | kod yedeği (GPT yazar) |  |
| I5 | {N} people run from the flames. | kod yedeği (GPT yazar) |  |
| I6 | {N} villagers dash away from the burning slope. | kod yedeği (GPT yazar) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| pickup truck | pickup truck | aktif |  |
| delivery truck | delivery truck | aktif |  |
| white van | white van | aktif |  |
| SUV | SUV | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Balcony of a hillside house | balkon @ Balcony of a hillside house mod B [ön plan: korkuluk, boş]; çatı @ kütüphane [ön plan: parapet, boş] | hayır (kadraj ekseni seçer) |
| Embankment above the village road | çatı @ kütüphane [ön plan: parapet, boş]; tepe @ Embankment above the village road mod B [ön plan: yaprak, boş] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 2 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Kadraj | 3 | 3 |  |
| Ön plan | 6 | 4 |  |
| Ortam | 2 | 2 | ⚠ 3'ten az |
| Açılış (0-4 sn) | 2 | 2 | ⚠ 3'ten az |
| Işık | 4 | 4 |  |
| Orta (4-9 sn) | 6 | 6 |  |
| Final (9-15 sn) | 5 | 5 |  |
| İnsan cümlesi | 6 | 0 |  |
| Araç | 4 | 4 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Balcony of a hillside house | çatı | parapet | A | A | K9 | L4 | GPT | pickup truck |
| 2 | Embankment above the village road | tepe | yaprak | A | A | K1 | L3 | GPT | white van |
| 3 | Balcony of a hillside house | çatı | boş | B | A | K5 | L7 | GPT | SUV |
| 4 | Embankment above the village road | tepe | yaprak | A | A | K2 | L1 | GPT | delivery truck |
| 5 | Balcony of a hillside house | balkon | korkuluk | A | A | K7 | L4 | GPT | white van |
| 6 | Embankment above the village road | çatı | parapet | B | A | K9 | L3 | GPT | pickup truck |
| 7 | Balcony of a hillside house | balkon | korkuluk | A | A | K1 | L7 | GPT | delivery truck |
| 8 | Embankment above the village road | tepe | boş | A | A | K5 | L1 | GPT | white van |
| 9 | Balcony of a hillside house | çatı | parapet | A | B | K8 | L4 | GPT | pickup truck |
| 10 | Embankment above the village road | tepe | yaprak | A | A | K9 | L5 | GPT | delivery truck |
| 11 | Balcony of a hillside house | balkon | korkuluk | A | A | K2 | L7 | GPT | white van |
| 12 | Embankment above the village road | çatı | parapet | A | B | K7 | L3 | GPT | SUV |
| 13 | Balcony of a hillside house | balkon | korkuluk | A | A | K5 | L4 | GPT | pickup truck |
| 14 | Embankment above the village road | tepe | boş | B | A | K1 | L5 | GPT | white van |
| 15 | Balcony of a hillside house | balkon | korkuluk | A | A | K9 | L7 | GPT | delivery truck |
| 16 | Embankment above the village road | tepe | yaprak | A | A | K8 | L3 | GPT | SUV |
| 17 | Balcony of a hillside house | balkon | boş | B | B | K2 | L4 | GPT | white van |
| 18 | Embankment above the village road | tepe | yaprak | A | A | K5 | L5 | GPT | delivery truck |
| 19 | Balcony of a hillside house | balkon | korkuluk | A | A | K1 | L7 | GPT | SUV |
| 20 | Embankment above the village road | tepe | boş | A | A | K9 | L1 | GPT | white van |
| 21 | Balcony of a hillside house | çatı | parapet | A | A | K2 | L3 | GPT | delivery truck |
| 22 | Embankment above the village road | tepe | yaprak | A | A | K7 | L4 | GPT | SUV |
| 23 | Balcony of a hillside house | çatı | parapet | B | A | K5 | L7 | GPT | white van |
| 24 | Embankment above the village road | tepe | yaprak | A | A | K1 | L1 | GPT | pickup truck |
| 25 | Balcony of a hillside house | çatı | parapet | A | A | K9 | L3 | GPT | SUV |
| 26 | Embankment above the village road | tepe | yaprak | B | B | K2 | L5 | GPT | delivery truck |
| 27 | Balcony of a hillside house | balkon | boş | A | A | K8 | L4 | GPT | pickup truck |
| 28 | Embankment above the village road | tepe | yaprak | A | A | K5 | L1 | GPT | white van |
| 29 | Balcony of a hillside house | balkon | korkuluk | A | A | K1 | L3 | GPT | delivery truck |
| 30 | Embankment above the village road | çatı | parapet | A | A | K9 | L5 | GPT | SUV |
| 31 | Balcony of a hillside house | balkon | boş | A | A | K2 | L7 | GPT | white van |
| 32 | Embankment above the village road | çatı | parapet | A | A | K5 | L4 | GPT | delivery truck |
| 33 | Balcony of a hillside house | balkon | boş | A | A | K7 | L3 | GPT | SUV |
| 34 | Embankment above the village road | tepe | yaprak | A | A | K1 | L5 | GPT | pickup truck |
| 35 | Balcony of a hillside house | çatı | parapet | B | A | K9 | L7 | GPT | delivery truck |
| 36 | Embankment above the village road | tepe | boş | A | A | K2 | L1 | GPT | SUV |
| 37 | Balcony of a hillside house | balkon | korkuluk | A | A | K5 | L3 | GPT | white van |
| 38 | Embankment above the village road | çatı | parapet | A | A | K7 | L4 | GPT | pickup truck |
| 39 | Balcony of a hillside house | balkon | boş | B | A | K1 | L7 | GPT | delivery truck |
| 40 | Embankment above the village road | çatı | parapet | A | A | K9 | L1 | GPT | SUV |

### Firefighting helicopter drops water on the flames racing toward a hillside neighborhood

Hit (100K+) eşleşmesi: 12 Eki 170K ← 9 Eki 22:52

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Balcony of a hillside house | on a balcony of a hillside house overlooking the street and the burning slope | aktif | 12 Eki 170K |
| Embankment above the village road | on a roadside embankment above the road | aktif |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| balkon @ Balcony of a hillside house | Handheld footage filmed on a high balcony of a hillside house, high wide view of the neighborhood and the wall of flames together, the helicopter large and close in frame, never a distant dot; slight hand shake, the camera stays fixed, never descending, empty foreground; no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ kütüphane | Handheld footage filmed on the rooftop terrace of a hillside house, high wide view of the neighborhood and the wall of flames together, the helicopter large and close in frame, never a distant dot; slight hand shake, the camera stays fixed, never descending, empty foreground; no zoom, no cuts, no person or face close to the camera. | aktif |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | bugünkü görünüm (Setting satırı yok) | aktif |  |
| B | a canyon neighborhood of hillside villas with swimming pools and winding roads | rotasyon dışı |  |
| C | a lakeside town of houses below wooded hills | aktif |  |
| D | a hillside town of white houses above a blue bay | rotasyon dışı |  |
| E | a valley village of farmhouses among vineyard rows on the slopes | rotasyon dışı |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A firefighting helicopter swoops over a hillside neighborhood and its bucket releases its whole load at once in a wide falling sheet onto the wall of flames racing toward the houses. | aktif | 12 Eki 170K |
| B | A firefighting helicopter sweeps in low and its bucket releases its whole load at once in a wide falling sheet onto the flames behind the houses. | rotasyon dışı (deneme) |  |
| C | A firefighting helicopter comes in over the ridge and its bucket releases its whole load at once in a wide falling sheet onto the flames. | rotasyon dışı (deneme) |  |
| D | The flames reach the back gardens as a firefighting helicopter passes just above the rooftops with its water bucket. | aktif |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | hot dry wind and thick smoke haze | aktif |  |
| L2 | gusty dry wind under an orange smoky sky | aktif |  |
| L3 | heavy smoke and scorching still air | aktif |  |
| L4 | hazy early-morning light through drifting smoke | rotasyon dışı |  |
| L5 | harsh bright midday sun through the smoke | rotasyon dışı |  |
| L6 | deep red sunset glow through the smoke | rotasyon dışı |  |
| L7 | dark smoke-filled overcast sky | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| F1 | the falling sheet of water slams into the flames, flattening a section of the wall into white steam | aktif | 12 Eki 170K |
| F2 | the falling sheet of water crashes onto a burning roof and the charred roof caves in | aktif |  |
| F3 | the {vehicle} speeds down the street as the helicopter's downdraft whips smoke and embers across the road | aktif |  |
| F4 | the downdraft fans the flames into a wooden house and its roof collapses in a burst of sparks | aktif |  |
| F5 | the falling sheet of water smashes a burning wooden deck off the back of a house | aktif |  |
| F6 | a burning tree crashes across the road and the {vehicle} swerves into a garden wall, crumpling its front | aktif |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| G1 | the flames fight back, a fresh burst of fire swallowing trees beside the water line | aktif |  |
| G2 | the helicopter circles back and another falling sheet of water puts out a row of burning trees in steam | aktif | 12 Eki 170K |
| G3 | the downdraft topples a burning tree onto the house next door, smashing through its roof | aktif |  |
| G5 | the helicopter pulls up and away as the flames roar back behind it | aktif |  |
| G6 | the downdraft knocks a burning carport roof flat onto the cars beneath it | aktif |  |
| G7 | the falling sheet of water hits a burning garage across the street and its walls collapse in steam | PASİF |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| I1 | {N} residents run from the flames down the street. | kod yedeği (GPT yazar) |  |
| I2 | {N} villagers flee from the fire toward the road. | kod yedeği (GPT yazar) |  |
| I3 | {N} people sprint away from the flames. | kod yedeği (GPT yazar) |  |
| I4 | {N} residents scramble downhill away from the fire. | kod yedeği (GPT yazar) |  |
| I5 | {N} people run from the flames. | kod yedeği (GPT yazar) |  |
| I6 | {N} villagers dash away from the burning slope. | kod yedeği (GPT yazar) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| pickup truck | pickup truck | aktif |  |
| delivery truck | delivery truck | aktif |  |
| white van | white van | aktif |  |
| SUV | SUV | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Balcony of a hillside house | balkon @ Balcony of a hillside house [ön plan: -]; çatı @ kütüphane [ön plan: -] | hayır (kadraj ekseni seçer) |
| Embankment above the village road | balkon @ Balcony of a hillside house [ön plan: -]; çatı @ kütüphane [ön plan: -] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 2 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Kadraj | 2 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Ön plan | 0 | 0 |  |
| Ortam | 2 | 2 | ⚠ 3'ten az |
| Açılış (0-4 sn) | 2 | 2 | ⚠ 3'ten az |
| Işık | 3 | 3 |  |
| Orta (4-9 sn) | 6 | 5 |  |
| Final (9-15 sn) | 5 | 5 |  |
| İnsan cümlesi | 6 | 0 |  |
| Araç | 4 | 4 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Balcony of a hillside house | balkon | - | C | D | F1 | G6 | GPT | white van |
| 2 | Embankment above the village road | çatı | - | A | A | F6 | G5 | GPT | pickup truck |
| 3 | Balcony of a hillside house | balkon | - | A | A | F4 | G6 | GPT | delivery truck |
| 4 | Embankment above the village road | çatı | - | A | D | F3 | G3 | GPT | SUV |
| 5 | Balcony of a hillside house | balkon | - | A | A | F1 | G6 | GPT | white van |
| 6 | Embankment above the village road | çatı | - | C | D | F2 | G3 | GPT | pickup truck |
| 7 | Balcony of a hillside house | balkon | - | A | A | F6 | G6 | GPT | delivery truck |
| 8 | Embankment above the village road | çatı | - | A | A | F4 | G3 | GPT | white van |
| 9 | Balcony of a hillside house | balkon | - | A | A | F3 | G6 | GPT | pickup truck |
| 10 | Embankment above the village road | çatı | - | A | A | F2 | G3 | GPT | delivery truck |
| 11 | Balcony of a hillside house | balkon | - | A | A | F1 | G6 | GPT | white van |
| 12 | Embankment above the village road | çatı | - | A | A | F6 | G3 | GPT | pickup truck |
| 13 | Balcony of a hillside house | balkon | - | A | D | F4 | G6 | GPT | delivery truck |
| 14 | Embankment above the village road | çatı | - | A | A | F3 | G3 | GPT | SUV |
| 15 | Balcony of a hillside house | balkon | - | A | A | F1 | G6 | GPT | pickup truck |
| 16 | Embankment above the village road | çatı | - | A | A | F2 | G3 | GPT | delivery truck |
| 17 | Balcony of a hillside house | balkon | - | A | A | F6 | G6 | GPT | white van |
| 18 | Embankment above the village road | çatı | - | A | A | F4 | G3 | GPT | pickup truck |
| 19 | Balcony of a hillside house | balkon | - | A | A | F3 | G6 | GPT | SUV |
| 20 | Embankment above the village road | çatı | - | A | A | F2 | G3 | GPT | white van |
| 21 | Balcony of a hillside house | balkon | - | A | A | F1 | G6 | GPT | delivery truck |
| 22 | Embankment above the village road | çatı | - | A | A | F6 | G2 | GPT | pickup truck |
| 23 | Balcony of a hillside house | balkon | - | A | A | F4 | G1 | GPT | SUV |
| 24 | Embankment above the village road | çatı | - | C | D | F3 | G3 | GPT | delivery truck |
| 25 | Balcony of a hillside house | balkon | - | A | A | F1 | G6 | GPT | white van |
| 26 | Embankment above the village road | çatı | - | A | A | F6 | G3 | GPT | pickup truck |
| 27 | Balcony of a hillside house | balkon | - | A | A | F4 | G6 | GPT | delivery truck |
| 28 | Embankment above the village road | çatı | - | A | A | F2 | G3 | GPT | white van |
| 29 | Balcony of a hillside house | balkon | - | A | A | F3 | G6 | GPT | pickup truck |
| 30 | Embankment above the village road | çatı | - | A | A | F6 | G3 | GPT | SUV |
| 31 | Balcony of a hillside house | balkon | - | A | A | F1 | G6 | GPT | delivery truck |
| 32 | Embankment above the village road | çatı | - | A | A | F4 | G3 | GPT | white van |
| 33 | Balcony of a hillside house | balkon | - | A | A | F3 | G6 | GPT | SUV |
| 34 | Embankment above the village road | çatı | - | A | D | F2 | G3 | GPT | delivery truck |
| 35 | Balcony of a hillside house | balkon | - | A | A | F6 | G6 | GPT | white van |
| 36 | Embankment above the village road | çatı | - | A | A | F4 | G3 | GPT | pickup truck |
| 37 | Balcony of a hillside house | balkon | - | A | A | F1 | G6 | GPT | SUV |
| 38 | Embankment above the village road | çatı | - | A | A | F3 | G3 | GPT | delivery truck |
| 39 | Balcony of a hillside house | balkon | - | C | D | F6 | G6 | GPT | pickup truck |
| 40 | Embankment above the village road | çatı | - | A | A | F2 | G3 | GPT | white van |

### Tornado making landfall

Hit (100K+) eşleşmesi: 1 Kas 10,37M ← 31 Eki 09:52 (kamera 7-8. sn'de pencereden dönüyor (7.5/10))

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Beachfront promenade | further along the promenade | aktif |  |
| Residential coastal district | on a front porch across the street | aktif | 1 Kas 10,37M |
| Downtown city center | on a sidewalk across the street | aktif |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| balkon @ Beachfront promenade | Handheld footage filmed on a high balcony of a seafront hotel above the promenade, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the tornado always in frame, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ Downtown city center | Handheld footage filmed on a flat rooftop above the waterfront, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the tornado always in frame, a low parapet edge in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| pencere @ Residential coastal district | Handheld footage filmed through an open upper-floor window across from a residential coastal street, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the tornado always in frame, the open window frame at one side; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı | 1 Kas 10,37M |
| direk @ kütüphane | Footage from a fixed high security camera on a tall pole above the waterfront, slightly wide lens, no hand shake, no on-screen text or timestamp, high vantage; the camera stays fixed, the tornado always in frame; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| korkuluk (balkon @ Beachfront promenade) | a railing corner in the foreground | aktif |  |
| boş (balkon @ Beachfront promenade) | nothing in the foreground | aktif |  |
| parapet (çatı @ Downtown city center) | a low parapet edge in the foreground | aktif |  |
| boş (çatı @ Downtown city center) | nothing in the foreground | aktif |  |
| pencere (pencere @ Residential coastal district) | the open window frame at one side | rotasyon dışı |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | bugünkü görünüm (Setting satırı yok) | aktif |  |
| B | a palm-lined seafront boulevard of pastel hotels and beach bars | rotasyon dışı |  |
| C | a harbor town of colorful terraced houses along a stone quay with small sailboats | aktif | 1 Kas 10,37M |
| D | a beach suburb of wooden houses on stilts with porches and pickup trucks | rotasyon dışı |  |
| E | a modern waterfront district of glass apartment towers and a wide promenade | rotasyon dışı |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A violent tornado makes landfall on the waterfront, tearing roofs and signs into the air. | aktif |  |
| B | The tornado roars ashore and hurls chairs, umbrellas and debris from the waterfront into the air. | rotasyon dışı (deneme) |  |
| C | The tornado makes landfall, crosses the seafront road and flips a parked car onto its side. | aktif | 1 Kas 10,37M |
| D | The tornado makes landfall and tears the solar panels off the roof of the first house, sending them spinning through the air. | rotasyon dışı (deneme) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | a dark green storm light | aktif |  |
| L2 | heavy rain under black clouds | aktif |  |
| L3 | howling wind and rain | aktif |  |
| L4 | stormy late-afternoon light | aktif |  |
| L5 | eerie yellow early-morning storm light | rotasyon dışı |  |
| L6 | harsh bright midday sun under a towering storm cloud | rotasyon dışı |  |
| L7 | orange sunset light behind the storm | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| C1 | the tornado shoves the {vehicle} sideways across the street and slams it into the far curb | aktif | 1 Kas 10,37M |
| C2 | the tornado tips the {vehicle} over onto its side in the middle of the street | aktif |  |
| C4 | the {vehicle} slides along the street and slams into a parked car | aktif |  |
| C5 | the {vehicle} is lifted off the road and flung down the street | aktif |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| E1 | the tornado tears the roof off a waterfront building and scatters the pieces across the street | aktif | 1 Kas 10,37M |
| E2 | the tornado tears the roof off a waterfront restaurant and flings it across the road | aktif |  |
| E4 | the tornado uproots a large tree and flings it through the air | aktif |  |
| E5 | the tornado lifts a wooden kiosk off the waterfront and smashes it into the building across the street | aktif |  |
| E7 | the tornado shreds the top floor of a building across the street, debris spiraling up | aktif |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| I1 | {N} people sprint for cover from the tornado. | kod yedeği (GPT yazar) |  |
| I2 | {N} onlookers run inland away from the tornado. | kod yedeği (GPT yazar) |  |
| I3 | {N} residents flee from the tornado toward the buildings. | kod yedeği (GPT yazar) |  |
| I4 | {N} pedestrians scramble for cover as the tornado hits. | kod yedeği (GPT yazar) |  |
| I5 | {N} people run from the tornado. | kod yedeği (GPT yazar) |  |
| I6 | {N} onlookers dash away from the swirling debris. | kod yedeği (GPT yazar) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| pickup truck | pickup truck | aktif |  |
| delivery truck | delivery truck | aktif |  |
| white van | white van | aktif |  |
| SUV | SUV | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Beachfront promenade | balkon @ Beachfront promenade [ön plan: korkuluk, boş]; çatı @ Downtown city center [ön plan: parapet, boş] | hayır (kadraj ekseni seçer) |
| Residential coastal district | balkon @ Beachfront promenade [ön plan: korkuluk, boş]; çatı @ Downtown city center [ön plan: parapet, boş] | hayır (kadraj ekseni seçer) |
| Downtown city center | çatı @ Downtown city center [ön plan: parapet, boş]; balkon @ Beachfront promenade [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 3 | 3 |  |
| Kadraj | 2 | 3 |  |
| Ön plan | 4 | 3 |  |
| Ortam | 2 | 2 | ⚠ 3'ten az |
| Açılış (0-4 sn) | 2 | 2 | ⚠ 3'ten az |
| Işık | 4 | 4 |  |
| Orta (4-9 sn) | 4 | 4 |  |
| Final (9-15 sn) | 5 | 5 |  |
| İnsan cümlesi | 6 | 0 |  |
| Araç | 4 | 4 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Beachfront promenade | balkon | boş | A | A | C2 | E5 | GPT | pickup truck |
| 2 | Residential coastal district | çatı | parapet | A | A | C1 | E2 | GPT | white van |
| 3 | Downtown city center | direk | - | C | A | C4 | E7 | GPT | SUV |
| 4 | Beachfront promenade | çatı | boş | A | A | C5 | E1 | GPT | delivery truck |
| 5 | Residential coastal district | balkon | korkuluk | A | A | C2 | E4 | GPT | white van |
| 6 | Downtown city center | çatı | boş | C | A | C1 | E5 | GPT | pickup truck |
| 7 | Beachfront promenade | balkon | korkuluk | A | A | C4 | E2 | GPT | delivery truck |
| 8 | Residential coastal district | çatı | parapet | A | A | C5 | E7 | GPT | white van |
| 9 | Downtown city center | balkon | boş | A | A | C2 | E1 | GPT | pickup truck |
| 10 | Beachfront promenade | çatı | parapet | A | A | C1 | E4 | GPT | delivery truck |
| 11 | Residential coastal district | balkon | boş | A | A | C4 | E5 | GPT | white van |
| 12 | Downtown city center | çatı | parapet | A | A | C5 | E2 | GPT | pickup truck |
| 13 | Beachfront promenade | balkon | boş | A | A | C2 | E7 | GPT | delivery truck |
| 14 | Residential coastal district | çatı | parapet | C | A | C1 | E1 | GPT | SUV |
| 15 | Downtown city center | balkon | boş | A | A | C4 | E4 | GPT | pickup truck |
| 16 | Beachfront promenade | çatı | parapet | A | A | C5 | E5 | GPT | white van |
| 17 | Residential coastal district | direk | - | C | A | C2 | E2 | GPT | SUV |
| 18 | Downtown city center | çatı | boş | A | A | C1 | E7 | GPT | delivery truck |
| 19 | Beachfront promenade | balkon | korkuluk | A | A | C4 | E1 | GPT | white van |
| 20 | Residential coastal district | çatı | boş | A | A | C5 | E4 | GPT | SUV |
| 21 | Downtown city center | balkon | korkuluk | A | A | C2 | E5 | GPT | delivery truck |
| 22 | Beachfront promenade | çatı | parapet | A | A | C1 | E2 | GPT | white van |
| 23 | Residential coastal district | direk | - | C | A | C4 | E7 | GPT | SUV |
| 24 | Downtown city center | çatı | boş | A | A | C5 | E1 | GPT | pickup truck |
| 25 | Beachfront promenade | balkon | korkuluk | A | A | C2 | E4 | GPT | white van |
| 26 | Residential coastal district | çatı | boş | C | C | C1 | E5 | GPT | delivery truck |
| 27 | Downtown city center | balkon | korkuluk | A | A | C4 | E2 | GPT | pickup truck |
| 28 | Beachfront promenade | çatı | parapet | A | A | C5 | E7 | GPT | white van |
| 29 | Residential coastal district | balkon | korkuluk | A | A | C2 | E1 | GPT | delivery truck |
| 30 | Downtown city center | çatı | boş | A | A | C1 | E4 | GPT | SUV |
| 31 | Beachfront promenade | balkon | korkuluk | A | A | C4 | E5 | GPT | white van |
| 32 | Residential coastal district | çatı | boş | A | A | C5 | E2 | GPT | delivery truck |
| 33 | Downtown city center | balkon | korkuluk | A | A | C2 | E7 | GPT | SUV |
| 34 | Beachfront promenade | çatı | boş | A | A | C1 | E1 | GPT | pickup truck |
| 35 | Residential coastal district | direk | - | C | A | C4 | E4 | GPT | delivery truck |
| 36 | Downtown city center | çatı | parapet | A | A | C5 | E5 | GPT | SUV |
| 37 | Beachfront promenade | balkon | korkuluk | A | A | C2 | E2 | GPT | white van |
| 38 | Residential coastal district | çatı | parapet | A | A | C1 | E7 | GPT | pickup truck |
| 39 | Downtown city center | direk | - | C | A | C4 | E1 | GPT | delivery truck |
| 40 | Beachfront promenade | balkon | boş | A | A | C5 | E4 | GPT | SUV |

### Volcanic bombs slam into a village street

Hit (100K+) eşleşmesi: 10 Eki 1,36M ← 10 Eki 02:06

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Hillside terrace facing the erupting volcano | on a hillside terrace above the houses | PASİF/rotasyon dışı |  |
| Rooftop terrace facing the erupting volcano | on a rooftop terrace across the street | aktif | 10 Eki 1,36M |
| Balcony of a village house facing the erupting volcano | on a house balcony across the street | aktif |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| balkon @ Balcony of a village house facing the erupting volcano | Handheld footage filmed on a house balcony across the street, high vantage over a street of colorful concrete houses with parked trucks toward the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ Rooftop terrace facing the erupting volcano | Handheld footage filmed on a rooftop terrace across the street, high vantage over a street of colorful concrete houses with parked trucks toward the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| tepe @ Hillside terrace facing the erupting volcano | Handheld footage filmed on a hillside terrace above the houses, high vantage over a street of colorful concrete houses with parked trucks toward the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| pencere @ kütüphane | Handheld footage filmed through an open upper-floor window, high vantage over a street of colorful concrete houses with parked trucks toward the volcano; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the volcano always in the upper third, the open window frame edge at one side; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| korkuluk (balkon @ Balcony of a village house facing the erupting volcano) | a railing corner in the foreground | aktif |  |
| boş (balkon @ Balcony of a village house facing the erupting volcano) | nothing in the foreground | aktif |  |
| korkuluk (çatı @ Rooftop terrace facing the erupting volcano) | a railing corner in the foreground | aktif |  |
| boş (çatı @ Rooftop terrace facing the erupting volcano) | nothing in the foreground | aktif |  |
| korkuluk (tepe @ Hillside terrace facing the erupting volcano) | a railing corner in the foreground | rotasyon dışı |  |
| boş (tepe @ Hillside terrace facing the erupting volcano) | nothing in the foreground | rotasyon dışı |  |
| pencere (pencere @ kütüphane) | the open window frame at one side | rotasyon dışı |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| pastel_town | a street of colorful concrete houses with parked trucks | aktif (ağırlık 1) |  |
| hillside_town | a wide hillside-town street of stone and painted houses | aktif (ağırlık 1) |  |
| suburb | a suburban street of detached houses, garages and palm trees | aktif (ağırlık 1) |  |
| mountain_village | a village street of wooden and stone houses among trees | aktif (ağırlık 1) |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | Glowing volcanic bombs streak down from the erupting volcano and slam into the street, punching through roofs and igniting cars. | aktif | 10 Eki 1,36M |
| B | A single huge glowing rock from the volcano punches straight through the roof of the house across the street. | rotasyon dışı (deneme) |  |
| C | Glowing rocks slam into the street one after another, throwing sparks and smoke off the asphalt. | aktif |  |
| D | A volcanic bomb smashes into a large parked truck and the truck bursts into flames. | rotasyon dışı (deneme) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | ash-grey sky lit orange by a distant eruption plume | aktif | 10 Eki 1,36M |
| L2 | warm orange dusk sky glowing from the eruption | aktif |  |
| L3 | pink-orange dawn light under a dark ash sky | rotasyon dışı |  |
| L4 | dark night sky lit by glowing lava and fires | rotasyon dışı |  |
| L5 | bright midday light under a towering ash plume | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| R1 | a glowing rock punches through the roof of the {vehicle} | aktif |  |
| R2 | a glowing rock smashes onto the street, bursts apart and sets a parked car on fire | aktif |  |
| R3 | a glowing rock tears through a shop awning and sets it ablaze | aktif |  |
| R4 | a glowing rock slams into a shop sign, which crashes onto the sidewalk | aktif | 10 Eki 1,36M |
| R5 | a volcanic bomb punches through a stone wall and the wall bursts apart | aktif |  |
| R7 | a huge glowing rock crashes through the roof of a house across the street | aktif |  |
| R8 | a glowing rock slams into a house across the street and its wall bursts apart | aktif |  |
| R9 | a glowing rock crashes through the front of a corner shop down the street and its wall caves in | aktif |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| T1 | glowing rocks slam into the roofs, sending tiles flying as flames rise | aktif |  |
| T2 | a glowing rock bounces along the road and slams into a parked car | aktif | 10 Eki 1,36M |
| T5 | a volcanic bomb lands in the middle of the street and the road blasts apart in a crater of sparks and rock | PASİF |  |
| T6 | a volcanic bomb hits a house's upper floor and a section of the wall bursts outward in flames | aktif |  |
| T7 | a volcanic bomb slams into a parked van and flips it onto its side in a burst of sparks | aktif |  |
| T8 | a huge glowing rock hits a house and its upper floor erupts in flames | aktif |  |
| T9 | a glowing rock smashes into a large parked truck and flames wrap the cab | aktif |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| I1 | {N} residents run from the falling rocks. | kod yedeği (GPT yazar) |  |
| I2 | {N} residents flee down the street from the rocks. | kod yedeği (GPT yazar) |  |
| I3 | {N} people sprint away from the falling rocks. | kod yedeği (GPT yazar) |  |
| I4 | {N} residents scramble for cover from the rocks. | kod yedeği (GPT yazar) |  |
| I5 | {N} people run for cover from it. | kod yedeği (GPT yazar) |  |
| I6 | {N} residents dash away between the houses. | kod yedeği (GPT yazar) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| pickup truck | pickup truck | aktif |  |
| delivery truck | delivery truck | aktif |  |
| white van | white van | aktif |  |
| SUV | SUV | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Hillside terrace facing the erupting volcano | balkon @ Balcony of a village house facing the erupting volcano [ön plan: korkuluk, boş]; çatı @ Rooftop terrace facing the erupting volcano [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Rooftop terrace facing the erupting volcano | balkon @ Balcony of a village house facing the erupting volcano [ön plan: korkuluk, boş]; çatı @ Rooftop terrace facing the erupting volcano [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Balcony of a village house facing the erupting volcano | balkon @ Balcony of a village house facing the erupting volcano [ön plan: korkuluk, boş]; çatı @ Rooftop terrace facing the erupting volcano [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 2 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Kadraj | 2 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Ön plan | 4 | 2 | ⚠ 3'ten az |
| Ortam | 4 | 4 |  |
| Açılış (0-4 sn) | 2 | 2 | ⚠ 3'ten az |
| Işık | 2 | 2 | ⚠ 3'ten az |
| Orta (4-9 sn) | 8 | 8 |  |
| Final (9-15 sn) | 6 | 4 |  |
| İnsan cümlesi | 6 | 0 |  |
| Araç | 4 | 4 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | R8 | T8 | GPT | SUV |
| 2 | Balcony of a village house facing the erupting volcano | balkon | boş | pastel_town | A | R5 | T9 | GPT | delivery truck |
| 3 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | R9 | T6 | GPT | pickup truck |
| 4 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | hillside_town | A | R3 | T2 | GPT | white van |
| 5 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | A | R1 | T8 | GPT | SUV |
| 6 | Balcony of a village house facing the erupting volcano | balkon | boş | mountain_village | A | R8 | T9 | GPT | delivery truck |
| 7 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | R2 | T6 | GPT | white van |
| 8 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | suburb | A | R4 | T2 | GPT | pickup truck |
| 9 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | A | R3 | T8 | GPT | SUV |
| 10 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | hillside_town | C | R9 | T9 | GPT | white van |
| 11 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | R1 | T6 | GPT | pickup truck |
| 12 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | suburb | C | R5 | T2 | GPT | SUV |
| 13 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | R2 | T8 | GPT | delivery truck |
| 14 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | mountain_village | A | R4 | T9 | GPT | white van |
| 15 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | suburb | C | R3 | T6 | GPT | pickup truck |
| 16 | Balcony of a village house facing the erupting volcano | balkon | boş | pastel_town | A | R8 | T2 | GPT | SUV |
| 17 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | R9 | T8 | GPT | white van |
| 18 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | suburb | A | R7 | T9 | GPT | delivery truck |
| 19 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | A | R4 | T6 | GPT | pickup truck |
| 20 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | mountain_village | A | R3 | T2 | GPT | white van |
| 21 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | suburb | A | R5 | T8 | GPT | SUV |
| 22 | Balcony of a village house facing the erupting volcano | balkon | boş | pastel_town | A | R8 | T9 | GPT | delivery truck |
| 23 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | R7 | T6 | GPT | pickup truck |
| 24 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | suburb | A | R9 | T2 | GPT | white van |
| 25 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | A | R4 | T8 | GPT | SUV |
| 26 | Balcony of a village house facing the erupting volcano | balkon | boş | hillside_town | A | R3 | T9 | GPT | pickup truck |
| 27 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | R2 | T6 | GPT | white van |
| 28 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | suburb | A | R7 | T2 | GPT | SUV |
| 29 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | hillside_town | A | R8 | T8 | GPT | delivery truck |
| 30 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | pastel_town | A | R5 | T9 | GPT | pickup truck |
| 31 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | suburb | A | R9 | T6 | GPT | white van |
| 32 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | hillside_town | A | R4 | T2 | GPT | delivery truck |
| 33 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | pastel_town | C | R7 | T8 | GPT | SUV |
| 34 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | suburb | A | R8 | T9 | GPT | white van |
| 35 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | mountain_village | A | R1 | T6 | GPT | pickup truck |
| 36 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | hillside_town | A | R5 | T2 | GPT | delivery truck |
| 37 | Rooftop terrace facing the erupting volcano | çatı | korkuluk | suburb | A | R3 | T8 | GPT | SUV |
| 38 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | mountain_village | A | R9 | T9 | GPT | white van |
| 39 | Rooftop terrace facing the erupting volcano | çatı | boş | pastel_town | C | R4 | T6 | GPT | delivery truck |
| 40 | Balcony of a village house facing the erupting volcano | balkon | korkuluk | hillside_town | A | R8 | T2 | GPT | pickup truck |

### Mud and debris torrent tears through a hillside village

Hit (100K+) eşleşmesi: 2 Eki 431K ← 1 Eki 22:09 (beat'siz)

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Terrace on the opposite hillside | on a terrace on the opposite hillside, facing the village | aktif |  |
| High steps on the village square | on the high steps at the edge of the village square | aktif | 2 Eki 431K |
| Upper-floor balcony of a village house | on the upper-floor balcony of a village house, facing up the slope | aktif |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| balkon @ Upper-floor balcony of a village house | Handheld footage filmed on the upper-floor balcony of a village house, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the debris torrent always in frame, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ kütüphane | Handheld footage filmed on a flat rooftop above the hillside village, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the debris torrent always in frame, a low parapet edge in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| tepe @ Terrace on the opposite hillside mod A | Handheld footage filmed on a terrace on the opposite hillside, facing the village, eye level, normal lens; slight hand shake, the camera pans to follow the debris torrent; no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| tepe @ Terrace on the opposite hillside mod B | Handheld footage filmed on a terrace on the opposite hillside, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the debris torrent always in frame, a few leaves at the frame edge; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| teras @ High steps on the village square | Handheld footage filmed on the high steps at the edge of the village square, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the debris torrent always in frame, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| tepe @ Terrace on the opposite hillside | Handheld footage filmed on a terrace on the opposite hillside, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the debris torrent always in frame, a few leaves at the frame edge; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| teras @ High steps on the village square mod A | Handheld footage filmed on the high steps at the edge of the village square, eye level, normal lens; slight hand shake, the camera pans to follow the debris torrent; no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| teras @ High steps on the village square mod B | Handheld footage filmed on the high steps at the edge of the village square, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the debris torrent always in frame, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| balkon @ Upper-floor balcony of a village house mod A | Handheld footage filmed on the upper-floor balcony of a village house, facing up the slope, eye level, normal lens; slight hand shake, the camera pans to follow the debris torrent; no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| balkon @ Upper-floor balcony of a village house mod B | Handheld footage filmed on the upper-floor balcony of a village house, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the debris torrent always in frame, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| korkuluk (balkon @ Upper-floor balcony of a village house) | a railing corner in the foreground | aktif |  |
| boş (balkon @ Upper-floor balcony of a village house) | nothing in the foreground | aktif |  |
| parapet (çatı @ kütüphane) | a low parapet edge in the foreground | rotasyon dışı |  |
| boş (çatı @ kütüphane) | nothing in the foreground | rotasyon dışı |  |
| yaprak (tepe @ Terrace on the opposite hillside mod B) | a few leaves at the frame edge | aktif |  |
| boş (tepe @ Terrace on the opposite hillside mod B) | nothing in the foreground | aktif |  |
| teras_korkuluk (teras @ High steps on the village square) | a railing corner in the foreground | rotasyon dışı |  |
| boş (teras @ High steps on the village square) | nothing in the foreground | rotasyon dışı |  |
| yaprak (tepe @ Terrace on the opposite hillside) | a few leaves at the frame edge | rotasyon dışı |  |
| boş (tepe @ Terrace on the opposite hillside) | nothing in the foreground | rotasyon dışı |  |
| teras_korkuluk (teras @ High steps on the village square mod B) | a railing corner in the foreground | aktif |  |
| boş (teras @ High steps on the village square mod B) | nothing in the foreground | aktif |  |
| korkuluk (balkon @ Upper-floor balcony of a village house mod B) | a railing corner in the foreground | aktif |  |
| boş (balkon @ Upper-floor balcony of a village house mod B) | nothing in the foreground | aktif |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | bugünkü görünüm (Setting satırı yok) | aktif |  |
| B | a terraced rice-field village of stilt houses among palm trees | rotasyon dışı |  |
| C | a highland village of adobe houses with red tile roofs around a small church | rotasyon dışı |  |
| D | a hill village of stone farmhouses and barns around a narrow square | aktif |  |
| E | a mountain village of grey-tiled houses, concrete steps and small vegetable gardens | rotasyon dışı |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A massive torrent of thick brown mud full of rocks, branches and debris bursts through the drenched hillside village. | aktif | 2 Eki 431K |
| B | The terraced hillside fields above the village turn to thick brown mud full of rocks, branches and debris and slide into the top row of houses. | aktif |  |
| C | A debris torrent bursts from the stream bed, floods the village lane and shoves a house off its foundations. | rotasyon dışı (deneme) |  |
| D | Half of the hillside behind the village breaks away with its trees and slides down to the roofs of the houses. | rotasyon dışı (deneme) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | driving rain and wind | aktif |  |
| L2 | heavy downpour under dark storm light | aktif |  |
| L3 | steady heavy rain, grey low cloud | aktif |  |
| L4 | grey dawn light after a night of rain | rotasyon dışı |  |
| L5 | bright midday light between heavy rain showers | rotasyon dışı |  |
| L6 | dim dusk light with steady drizzle | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| K1 | the {vehicle} is swept down the lane and rammed against a house wall | aktif |  |
| K2 | the {vehicle} is spun around by the torrent and dragged along the lane | aktif |  |
| K3 | the torrent shoves the {vehicle} down the lane and wedges it between two houses | aktif |  |
| K4 | the {vehicle} tips over onto its side in the torrent | aktif |  |
| K5 | the {vehicle} slams into a pile of logs and both are carried away | aktif |  |
| K6 | the {vehicle} is shoved into a parked motorbike and both are carried along | aktif |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | a wooden house along the lane is struck and its wall collapses | aktif |  |
| L3 | a large tree is uprooted and rolls down with the torrent | aktif |  |
| L4 | a roof section is torn off a house along the lane and swept away | aktif |  |
| L5 | the torrent smashes through the front wall of a wooden house along the lane | aktif |  |
| L6 | the torrent shoves a parked car along the lane into the front of a house | aktif |  |
| L7 | the landslide rips a wooden house off its foundation and carries it down the slope | aktif |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| I1 | {N} villagers run down the lane away from the mud. | kod yedeği (GPT yazar) |  |
| I2 | {N} residents sprint along the lane as the mud torrent smashes into the houses behind them. | kod yedeği (GPT yazar) |  |
| I3 | {N} villagers scramble up the stone steps. | kod yedeği (GPT yazar) |  |
| I4 | {N} villagers sprint away from the mud. | kod yedeği (GPT yazar) |  |
| I5 | {N} people flee from the mud. | kod yedeği (GPT yazar) |  |
| I6 | {N} residents dash away between the houses. | kod yedeği (GPT yazar) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| pickup truck | pickup truck | aktif |  |
| white van | white van | aktif |  |
| large SUV | large SUV | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Terrace on the opposite hillside | tepe @ Terrace on the opposite hillside mod B [ön plan: yaprak, boş]; balkon @ Upper-floor balcony of a village house [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| High steps on the village square | teras @ High steps on the village square mod B [ön plan: teras_korkuluk, boş]; balkon @ Upper-floor balcony of a village house [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Upper-floor balcony of a village house | balkon @ Upper-floor balcony of a village house mod B [ön plan: korkuluk, boş]; teras @ High steps on the village square [ön plan: teras_korkuluk, boş] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 3 | 3 |  |
| Kadraj | 4 | 3 |  |
| Ön plan | 8 | 4 |  |
| Ortam | 2 | 2 | ⚠ 3'ten az |
| Açılış (0-4 sn) | 2 | 2 | ⚠ 3'ten az |
| Işık | 3 | 3 |  |
| Orta (4-9 sn) | 6 | 6 |  |
| Final (9-15 sn) | 6 | 6 |  |
| İnsan cümlesi | 6 | 0 |  |
| Araç | 3 | 3 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Terrace on the opposite hillside | balkon | boş | A | A | K6 | L4 | GPT | pickup truck |
| 2 | High steps on the village square | teras | teras_korkuluk | A | A | K2 | L3 | GPT | large SUV |
| 3 | Upper-floor balcony of a village house | balkon | boş | D | A | K4 | L6 | GPT | white van |
| 4 | Terrace on the opposite hillside | tepe | yaprak | A | A | K3 | L1 | GPT | pickup truck |
| 5 | High steps on the village square | teras | teras_korkuluk | A | A | K6 | L7 | GPT | large SUV |
| 6 | Upper-floor balcony of a village house | balkon | boş | A | A | K5 | L5 | GPT | white van |
| 7 | Terrace on the opposite hillside | tepe | yaprak | D | A | K2 | L6 | GPT | pickup truck |
| 8 | High steps on the village square | balkon | korkuluk | A | A | K3 | L4 | GPT | large SUV |
| 9 | Upper-floor balcony of a village house | teras | boş | A | B | K4 | L3 | GPT | white van |
| 10 | Terrace on the opposite hillside | tepe | yaprak | A | A | K6 | L5 | GPT | pickup truck |
| 11 | High steps on the village square | teras | teras_korkuluk | A | A | K5 | L6 | GPT | large SUV |
| 12 | Upper-floor balcony of a village house | balkon | korkuluk | A | A | K2 | L4 | GPT | white van |
| 13 | Terrace on the opposite hillside | tepe | yaprak | A | B | K3 | L3 | GPT | pickup truck |
| 14 | High steps on the village square | teras | boş | D | A | K4 | L7 | GPT | large SUV |
| 15 | Upper-floor balcony of a village house | balkon | korkuluk | A | A | K6 | L6 | GPT | white van |
| 16 | Terrace on the opposite hillside | teras | boş | A | A | K5 | L1 | GPT | pickup truck |
| 17 | High steps on the village square | teras | teras_korkuluk | D | B | K2 | L5 | GPT | large SUV |
| 18 | Upper-floor balcony of a village house | balkon | korkuluk | A | A | K4 | L4 | GPT | white van |
| 19 | Terrace on the opposite hillside | tepe | yaprak | A | A | K6 | L3 | GPT | pickup truck |
| 20 | High steps on the village square | teras | boş | A | A | K3 | L7 | GPT | large SUV |
| 21 | Upper-floor balcony of a village house | balkon | korkuluk | A | A | K5 | L5 | GPT | white van |
| 22 | Terrace on the opposite hillside | tepe | yaprak | A | A | K1 | L4 | GPT | pickup truck |
| 23 | High steps on the village square | teras | boş | D | A | K2 | L1 | GPT | large SUV |
| 24 | Upper-floor balcony of a village house | balkon | korkuluk | A | A | K4 | L6 | GPT | white van |
| 25 | Terrace on the opposite hillside | tepe | yaprak | A | A | K3 | L5 | GPT | pickup truck |
| 26 | High steps on the village square | teras | teras_korkuluk | D | B | K5 | L7 | GPT | large SUV |
| 27 | Upper-floor balcony of a village house | balkon | boş | A | A | K1 | L3 | GPT | white van |
| 28 | Terrace on the opposite hillside | teras | teras_korkuluk | A | A | K4 | L1 | GPT | pickup truck |
| 29 | High steps on the village square | teras | boş | A | A | K6 | L4 | GPT | large SUV |
| 30 | Upper-floor balcony of a village house | balkon | korkuluk | A | A | K2 | L6 | GPT | white van |
| 31 | Terrace on the opposite hillside | tepe | boş | A | A | K5 | L3 | GPT | pickup truck |
| 32 | High steps on the village square | teras | teras_korkuluk | A | A | K4 | L5 | GPT | large SUV |
| 33 | Upper-floor balcony of a village house | balkon | boş | A | A | K3 | L4 | GPT | white van |
| 34 | Terrace on the opposite hillside | tepe | yaprak | A | A | K2 | L7 | GPT | pickup truck |
| 35 | High steps on the village square | teras | teras_korkuluk | D | A | K6 | L1 | GPT | large SUV |
| 36 | Upper-floor balcony of a village house | balkon | boş | A | A | K4 | L3 | GPT | white van |
| 37 | Terrace on the opposite hillside | tepe | yaprak | A | A | K5 | L4 | GPT | pickup truck |
| 38 | High steps on the village square | teras | teras_korkuluk | A | A | K2 | L5 | GPT | large SUV |
| 39 | Upper-floor balcony of a village house | balkon | boş | D | A | K6 | L6 | GPT | white van |
| 40 | Terrace on the opposite hillside | tepe | yaprak | A | A | K3 | L1 | GPT | pickup truck |

### Flash flooding in city streets

Hit (100K+) eşleşmesi: 29 Eyl 338K / 4 Eki 132K / 6 Eki 305K ← 26 Eyl-3 Eki (beat'siz) (beat kimliği yok; kilit 3249de8 hâli)

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Downtown city center | on a sidewalk across the street | aktif |  |
| Dense urban downtown | on a sidewalk across the street | aktif |  |
| Commercial city streets | on a sidewalk across the street | aktif |  |
| High-rise city district | on a sidewalk across the street | aktif |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| balkon @ Downtown city center | Handheld footage filmed on a high balcony over a downtown street, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the floodwater always in frame, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ Dense urban downtown | Handheld footage filmed on a flat rooftop above a dense downtown street, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the floodwater always in frame, a low parapet edge in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| pencere @ Commercial city streets | Handheld footage filmed through an open upper-floor window across from a commercial street, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the floodwater always in frame, the open window frame at one side; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| direk @ kütüphane | Footage from a fixed high security camera on a tall pole above the street, slightly wide lens, no hand shake, no on-screen text or timestamp, high vantage; the camera stays fixed, the floodwater always in frame; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| balkon @ High-rise city district | Handheld footage filmed on a high balcony of a high-rise above the street, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the floodwater always in frame, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| korkuluk (balkon @ Downtown city center) | a railing corner in the foreground | aktif |  |
| boş (balkon @ Downtown city center) | nothing in the foreground | aktif |  |
| parapet (çatı @ Dense urban downtown) | a low parapet edge in the foreground | aktif |  |
| boş (çatı @ Dense urban downtown) | nothing in the foreground | aktif |  |
| pencere (pencere @ Commercial city streets) | the open window frame at one side | rotasyon dışı |  |
| korkuluk (balkon @ High-rise city district) | a railing corner in the foreground | aktif |  |
| boş (balkon @ High-rise city district) | nothing in the foreground | aktif |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| gulf_metropolis | a city district with glass towers behind palm-lined boulevards, sand-colored low buildings | aktif |  |
| north_african_coast | a city district with sand-colored flat-roofed buildings, narrow streets, cloth awnings, arched doorways | aktif |  |
| us_coastal_town | a city district with wide asphalt roads, low wooden and brick houses, power lines | aktif |  |
| north_european_seaside | a city district with brick terraced houses, narrow streets, bay windows, wet slate roofs | aktif |  |
| riviera | a city district with cream stone buildings with shuttered windows, cobbled streets, plane trees | aktif |  |
| east_asian_coast | a city district with dense mid-rise apartment blocks with air-conditioners and tangled wires, narrow lanes | aktif |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A waist-high wall of brown muddy floodwater surges into the street. | aktif | 29 Eyl 338K / 4 Eki 132K / 6 Eki 305K |
| B | A wall of brown floodwater swings around the corner of an intersection and tips parked cars onto their sides. | PASİF |  |
| C | A surge of brown floodwater pours down the sloping street and drags a parked car along with it. | PASİF |  |
| D | Floodwater bursts over the low wall of a canal and spills straight into the street, sweeping parked cars sideways. | rotasyon dışı (deneme) |  |
| E | A wall of brown floodwater swings around the corner of an intersection and shoves parked cars sideways. | aktif |  |
| F | A surge of brown floodwater pours down the sloping street and drags parked cars along with it. | rotasyon dışı (deneme) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | heavy rain | aktif |  |
| L2 | driving rain and wind | aktif |  |
| L3 | a dark storm light | aktif |  |
| L4 | grey early-morning light with steady rain | rotasyon dışı |  |
| L5 | bright midday light after a cloudburst | rotasyon dışı |  |
| L6 | orange sunset light under breaking storm clouds | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| V1 | the {vehicle} is caught by the current, turns sideways and is dragged down the street | aktif |  |
| V2 | the {vehicle} is swept into another parked car and both are shoved along | aktif |  |
| V3 | the {vehicle} is lifted off its wheels and spun around | PASİF |  |
| V4 | the {vehicle} is pushed onto the sidewalk and slams into a lamppost | PASİF |  |
| V5 | the {vehicle} tips over onto its side in the current | PASİF |  |
| V6 | the {vehicle} is shoved into the side of a parked city bus and crumples against it | PASİF |  |
| V7 | the {vehicle} is rammed against a building wall, crumpling its whole front end | PASİF |  |
| V8 | the {vehicle} is swept into the front of a corner shop and the brick wall caves in | PASİF |  |
| V9 | the {vehicle} is shoved hard against the side of a parked city bus and pinned there | DENEME |  |
| V10 | the {vehicle} is rammed against a building front and pinned there by the current | DENEME |  |
| V11 | the {vehicle} is swept into a corner shop and its doors burst open as water pours inside | DENEME |  |
| V12 | the {vehicle} floats free and is carried fast down the middle of the street | DENEME |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| D2 | a lamppost topples into the current | PASİF |  |
| D3 | a street tree is uprooted and carried along | PASİF |  |
| D4 | a dumpster tumbles down the street and smashes into a parked car | PASİF |  |
| D5 | a city bus is shoved sideways by the current | PASİF |  |
| D8 | a car is lifted off the road and spins away downstream | PASİF |  |
| D9 | the flood bursts through the ground floor of a building across the street | PASİF |  |
| D10 | the current shoves parked cars into a shopfront and its wall caves in | DENEME |  |
| D12 | the current piles a row of parked cars against the front of a shop | DENEME |  |
| D13 | the street becomes a fast brown river and the {vehicle} is carried away toward the intersection | DENEME |  |
| D14 | the current pushes a parked city bus against a shopfront and floodwater pours in through its doors | DENEME |  |
| D15 | the flood bursts open a row of shop shutters and pours into the stores | DENEME |  |
| D16 | the surge tears the ground-floor fronts off the shops across the street | DENEME |  |
| D17 | the surge tips a city bus onto its side and pushes it along the street | DENEME |  |
| D18 | the surge slams the {vehicle} into a building front and the shopfront caves in around it | DENEME |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| I1 | {N} pedestrians run for the doorways as the water hits. | aktif (eksen) |  |
| I2 | {N} people run up the steps of the nearest building. | aktif (eksen) |  |
| I3 | {N} people sprint into the entrance of an office building. | DENEME (eksen) |  |
| I4 | {N} pedestrians run for the stairway of a parking garage. | DENEME (eksen) |  |
| I5 | {N} people sprint into a hotel lobby across the street. | DENEME (eksen) |  |
| I6 | {N} pedestrians run up the stairs of a shopping arcade. | DENEME (eksen) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| blue sedan | blue sedan | aktif |  |
| green delivery van | green delivery van | aktif |  |
| orange box truck | orange box truck | aktif |  |
| orange delivery truck | orange delivery truck | aktif |  |
| red SUV | red SUV | aktif |  |
| yellow pickup truck | yellow pickup truck | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Downtown city center | balkon @ Downtown city center [ön plan: korkuluk, boş]; çatı @ Dense urban downtown [ön plan: parapet, boş] | hayır (kadraj ekseni seçer) |
| Dense urban downtown | çatı @ Dense urban downtown [ön plan: parapet, boş]; balkon @ Downtown city center [ön plan: korkuluk, boş]; balkon @ High-rise city district [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Commercial city streets | balkon @ Downtown city center [ön plan: korkuluk, boş]; balkon @ High-rise city district [ön plan: korkuluk, boş]; çatı @ Dense urban downtown [ön plan: parapet, boş] | hayır (kadraj ekseni seçer) |
| High-rise city district | balkon @ High-rise city district [ön plan: korkuluk, boş]; çatı @ Dense urban downtown [ön plan: parapet, boş] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 4 | 4 |  |
| Kadraj | 3 | 2 | ⚠ 3'ten az ↔ ping-pong |
| Ön plan | 6 | 3 |  |
| Ortam | 6 | 0 |  |
| Açılış (0-4 sn) | 2 | 2 | ⚠ 3'ten az |
| Işık | 3 | 3 |  |
| Orta (4-9 sn) | 6 | 6 |  |
| Final (9-15 sn) | 8 | 8 |  |
| İnsan cümlesi | 6 | 6 |  |
| Araç | 6 | 6 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Commercial city streets | balkon | boş | north_african_coast | A | V9 | D13 | I2 | red SUV |
| 2 | Downtown city center | çatı | parapet | gulf_metropolis | A | V2 | D18 | I1 | yellow pickup truck |
| 3 | Dense urban downtown | balkon | boş | north_european_seaside | A | V12 | D14 | I2 | orange delivery truck |
| 4 | Commercial city streets | çatı | parapet | us_coastal_town | E | V10 | D12 | I3 | blue sedan |
| 5 | Downtown city center | balkon | boş | east_asian_coast | A | V9 | D16 | I1 | red SUV |
| 6 | Dense urban downtown | çatı | parapet | riviera | A | V1 | D10 | I2 | yellow pickup truck |
| 7 | Commercial city streets | balkon | boş | north_african_coast | A | V2 | D13 | I1 | green delivery van |
| 8 | High-rise city district | çatı | parapet | gulf_metropolis | A | V10 | D17 | I4 | red SUV |
| 9 | Dense urban downtown | balkon | boş | north_european_seaside | A | V9 | D15 | I2 | orange delivery truck |
| 10 | Commercial city streets | çatı | parapet | us_coastal_town | A | V1 | D12 | I6 | yellow pickup truck |
| 11 | Downtown city center | balkon | korkuluk | east_asian_coast | A | V12 | D18 | I1 | green delivery van |
| 12 | Dense urban downtown | çatı | boş | riviera | A | V2 | D17 | I2 | red SUV |
| 13 | Commercial city streets | balkon | korkuluk | north_african_coast | E | V10 | D16 | I1 | yellow pickup truck |
| 14 | Downtown city center | çatı | parapet | gulf_metropolis | A | V1 | D15 | I2 | blue sedan |
| 15 | Dense urban downtown | balkon | korkuluk | north_european_seaside | A | V9 | D12 | I1 | red SUV |
| 16 | Commercial city streets | çatı | boş | us_coastal_town | A | V12 | D10 | I3 | yellow pickup truck |
| 17 | Downtown city center | balkon | korkuluk | east_asian_coast | A | V10 | D13 | I2 | orange box truck |
| 18 | Dense urban downtown | çatı | parapet | riviera | A | V2 | D15 | I1 | red SUV |
| 19 | Commercial city streets | balkon | korkuluk | north_african_coast | A | V1 | D18 | I2 | green delivery van |
| 20 | High-rise city district | çatı | boş | gulf_metropolis | A | V12 | D12 | I1 | yellow pickup truck |
| 21 | Dense urban downtown | balkon | korkuluk | north_european_seaside | A | V10 | D14 | I2 | orange delivery truck |
| 22 | Downtown city center | çatı | parapet | us_coastal_town | A | V11 | D17 | I4 | blue sedan |
| 23 | Commercial city streets | balkon | boş | east_asian_coast | A | V9 | D18 | I1 | orange box truck |
| 24 | Dense urban downtown | çatı | parapet | riviera | A | V1 | D16 | I2 | red SUV |
| 25 | Downtown city center | balkon | boş | north_african_coast | A | V10 | D15 | I6 | green delivery van |
| 26 | Commercial city streets | çatı | parapet | gulf_metropolis | A | V2 | D14 | I1 | yellow pickup truck |
| 27 | Dense urban downtown | balkon | boş | north_european_seaside | A | V9 | D10 | I3 | red SUV |
| 28 | Downtown city center | çatı | parapet | us_coastal_town | A | V1 | D17 | I2 | blue sedan |
| 29 | Commercial city streets | balkon | boş | east_asian_coast | A | V12 | D15 | I5 | green delivery van |
| 30 | Dense urban downtown | çatı | parapet | riviera | A | V2 | D16 | I1 | red SUV |
| 31 | Downtown city center | balkon | boş | north_african_coast | A | V10 | D10 | I2 | yellow pickup truck |
| 32 | Commercial city streets | çatı | parapet | gulf_metropolis | A | V1 | D14 | I1 | blue sedan |
| 33 | Dense urban downtown | balkon | korkuluk | north_european_seaside | A | V12 | D17 | I2 | green delivery van |
| 34 | Downtown city center | çatı | parapet | us_coastal_town | E | V9 | D13 | I4 | red SUV |
| 35 | Commercial city streets | balkon | boş | east_asian_coast | A | V2 | D18 | I1 | orange box truck |
| 36 | Dense urban downtown | çatı | parapet | riviera | A | V10 | D12 | I6 | yellow pickup truck |
| 37 | Downtown city center | balkon | boş | north_african_coast | A | V12 | D16 | I2 | red SUV |
| 38 | High-rise city district | çatı | parapet | gulf_metropolis | A | V1 | D13 | I1 | blue sedan |
| 39 | Commercial city streets | balkon | korkuluk | north_european_seaside | E | V9 | D15 | I2 | orange delivery truck |
| 40 | Downtown city center | çatı | boş | us_coastal_town | A | V10 | D17 | I1 | yellow pickup truck |

### Tornado tears past the Statue of Liberty into Battery Park

Hit (100K+) eşleşmesi: yok (Notion Paylaşımlar'da 100K+ kayıt yok)

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| Rooftop terrace of a Lower Manhattan high-rise facing the harbor | the rooftop terrace of a Lower Manhattan high-rise facing the harbor | aktif |  |
| High apartment balcony in Battery Park City looking across the harbor | a high apartment balcony in Battery Park City looking across the harbor | aktif |  |
| Top-floor terrace of a waterfront hotel next to Battery Park | the top-floor terrace of a waterfront hotel next to Battery Park | PASİF/rotasyon dışı |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| çatı @ Rooftop terrace of a Lower Manhattan high-rise facing the harbor | Handheld footage from the rooftop terrace of a Lower Manhattan high-rise facing the harbor, high and wide, the Statue of Liberty standing intact in the distance across the harbor; slight hand shake, the camera stays fixed, never descending, the camera never pans, turns or follows; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| balkon @ High apartment balcony in Battery Park City looking across the harbor | Handheld footage from a high apartment balcony in Battery Park City looking across the harbor, high and wide, the Statue of Liberty standing intact in the distance across the harbor; slight hand shake, the camera stays fixed, never descending, the camera never pans, turns or follows; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| teras @ Top-floor terrace of a waterfront hotel next to Battery Park | Handheld footage from the top-floor terrace of a waterfront hotel next to Battery Park, high and wide, the Statue of Liberty standing intact in the distance across the harbor; slight hand shake, the camera stays fixed, never descending, the camera never pans, turns or follows; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| - | Setting: Battery Park and the harbor waterfront at the southern tip of Manhattan, no readable signs, text or flags. | aktif (tek) |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A colossal wedge tornado, far wider than Liberty Island, tears across New York Harbor past the Statue of Liberty, ripping spray off the water, and slams into the Battery Park waterfront promenade. | aktif (tek açılış) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | dark overcast storm afternoon | aktif |  |
| L2 | green-tinted storm sky | aktif |  |
| L3 | low late-afternoon sun under black storm clouds | aktif |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| B1 | the tornado tears the roof off the ferry terminal and hurls the metal sheets across the road | DENEME |  |
| B2 | the tornado rips the tall park trees out by the roots and throws them across the lawn | DENEME |  |
| B3 | the tornado smashes the waterfront café pavilion apart and flings its walls into the street | DENEME |  |
| B4 | the tornado shoves the {vehicle} across the road and slams it into the seawall | PASİF |  |
| B6 | the tornado shoves a city bus across the road and slams it into the side of the ferry terminal | PASİF |  |
| B5 | the tornado strips the scaffolding off a building front and throws it into the street | DENEME |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| C1 | the tornado crosses onto the avenue directly below the camera, tearing out the street trees and blasting debris against the building fronts | DENEME |  |
| C2 | the tornado tears the entire roof off the low brick building below and hurls it across the avenue | DENEME |  |
| C3 | the tornado tips a delivery truck onto its side in the middle of the avenue and drags it along | DENEME |  |
| C4 | the tornado collapses the front wall of the old waterfront warehouse into the street | DENEME |  |
| C6 | the tornado drives the {vehicle} along the avenue and slams it into the building corner below | DENEME |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| P1 | {N} people sprint off the waterfront promenade into the building entrances below. | aktif (birebir) |  |
| P2 | {N} people sprint across the park lawn toward the subway entrance. | aktif (birebir) |  |
| P3 | {N} people run into the lobby of the building below. | aktif (birebir) |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| yellow taxi | yellow taxi | aktif |  |
| red SUV | red SUV | aktif |  |
| blue sedan | blue sedan | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı @ Rooftop terrace of a Lower Manhattan high-rise facing the harbor [ön plan: -] | evet (tek kadraj) |
| High apartment balcony in Battery Park City looking across the harbor | balkon @ High apartment balcony in Battery Park City looking across the harbor [ön plan: -] | evet (tek kadraj) |
| Top-floor terrace of a waterfront hotel next to Battery Park | teras @ Top-floor terrace of a waterfront hotel next to Battery Park [ön plan: -] | evet (tek kadraj) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 2 | 2 | ⚠ 3'ten az |
| Kadraj | 3 | 2 | ⚠ 3'ten az |
| Ön plan | 0 | 0 |  |
| Ortam | 1 | 0 |  |
| Açılış (0-4 sn) | 1 | 1 | ⚠ 3'ten az |
| Işık | 3 | 3 |  |
| Orta (4-9 sn) | 4 | 4 |  |
| Final (9-15 sn) | 5 | 5 |  |
| İnsan cümlesi | 3 | 3 |  |
| Araç | 3 | 3 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B5 | C4 | P2 | yellow taxi |
| 2 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C1 | P3 | blue sedan |
| 3 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B3 | C2 | P1 | red SUV |
| 4 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B2 | C3 | P2 | yellow taxi |
| 5 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B5 | C6 | P3 | blue sedan |
| 6 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C4 | P1 | red SUV |
| 7 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B3 | C1 | P2 | yellow taxi |
| 8 | High apartment balcony in Battery Park City looking across the harbor | balkon | - | - | A | B2 | C2 | P3 | blue sedan |
| 9 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B5 | C3 | P1 | red SUV |
| 10 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C4 | P2 | yellow taxi |
| 11 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B3 | C1 | P3 | blue sedan |
| 12 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B2 | C2 | P1 | red SUV |
| 13 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B5 | C6 | P2 | yellow taxi |
| 14 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C3 | P3 | blue sedan |
| 15 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B3 | C4 | P1 | red SUV |
| 16 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B2 | C2 | P2 | yellow taxi |
| 17 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B5 | C1 | P3 | blue sedan |
| 18 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C3 | P1 | red SUV |
| 19 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B3 | C4 | P2 | yellow taxi |
| 20 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B2 | C2 | P3 | blue sedan |
| 21 | High apartment balcony in Battery Park City looking across the harbor | balkon | - | - | A | B5 | C6 | P1 | red SUV |
| 22 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C1 | P2 | yellow taxi |
| 23 | High apartment balcony in Battery Park City looking across the harbor | balkon | - | - | A | B3 | C3 | P3 | blue sedan |
| 24 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B2 | C4 | P1 | red SUV |
| 25 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B5 | C2 | P2 | yellow taxi |
| 26 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C1 | P3 | blue sedan |
| 27 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B3 | C3 | P1 | red SUV |
| 28 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B2 | C4 | P2 | yellow taxi |
| 29 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B5 | C6 | P3 | blue sedan |
| 30 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C1 | P1 | red SUV |
| 31 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B3 | C2 | P2 | yellow taxi |
| 32 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B2 | C3 | P3 | blue sedan |
| 33 | High apartment balcony in Battery Park City looking across the harbor | balkon | - | - | A | B5 | C4 | P1 | red SUV |
| 34 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C1 | P2 | yellow taxi |
| 35 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B3 | C2 | P3 | blue sedan |
| 36 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B2 | C3 | P1 | red SUV |
| 37 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B5 | C6 | P2 | yellow taxi |
| 38 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B1 | C4 | P3 | blue sedan |
| 39 | High apartment balcony in Battery Park City looking across the harbor | balkon | - | - | A | B3 | C1 | P1 | red SUV |
| 40 | Rooftop terrace of a Lower Manhattan high-rise facing the harbor | çatı | - | - | A | B2 | C2 | P2 | yellow taxi |

### Fire tornado tears across a burning roadside

Hit (100K+) eşleşmesi: 9 Eki 673K ← 8 Eki 21:23 (eski ortamsız nokta) · 26 Eki 176K ← aday: 16 Eki 13:45 T1+U8 (köy)

**Spot (kamera noktası)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| High balcony at the edge of a wooded neighborhood | on a high balcony above the wooded neighborhood | aktif |  |
| Rooftop terrace above a wooded residential area | on a rooftop terrace above a wooded area | aktif |  |
| High balcony over a tree-lined residential street | on a high balcony over a tree-lined street | aktif |  |
| Upper-floor terrace above a street of houses | on an upper-floor terrace above a street of houses | aktif |  |
| Hillside terrace above a village | on a hillside terrace above the village houses | aktif |  |
| High balcony of a village house | on a high balcony of a village house | aktif |  |

**Kadraj**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| balkon @ High balcony at the edge of a wooded neighborhood mod A | Handheld footage filmed on a high balcony above the wooded neighborhood, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera follows the tornado; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| balkon @ High balcony at the edge of a wooded neighborhood mod B | Handheld footage filmed on a high balcony above the wooded neighborhood, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ Rooftop terrace above a wooded residential area | Handheld footage filmed on a rooftop terrace above a wooded residential area, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a low parapet edge in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ Upper-floor terrace above a street of houses | Handheld footage filmed on an upper-floor terrace above a street of houses, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a low parapet edge in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| tepe @ Hillside terrace above a village | Handheld footage filmed on a hillside terrace above the village houses, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a few leaves at the frame edge; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| balkon @ High balcony at the edge of a wooded neighborhood | Handheld footage filmed on a high balcony above the wooded neighborhood, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| balkon @ High balcony over a tree-lined residential street | Handheld footage filmed on a high balcony overlooking a tree-lined residential street, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| balkon @ High balcony of a village house | Handheld footage filmed on a high balcony of a village house, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ Rooftop terrace above a wooded residential area mod A | Handheld footage filmed on a rooftop terrace above a wooded area, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera follows the tornado; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| çatı @ Rooftop terrace above a wooded residential area mod B | Handheld footage filmed on a rooftop terrace above a wooded residential area, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a low parapet edge in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| balkon @ High balcony over a tree-lined residential street mod A | Handheld footage filmed on a high balcony over a tree-lined street, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera follows the tornado; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| balkon @ High balcony over a tree-lined residential street mod B | Handheld footage filmed on a high balcony overlooking a tree-lined residential street, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| çatı @ Upper-floor terrace above a street of houses mod A | Handheld footage filmed on an upper-floor terrace above a street of houses, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera follows the tornado; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| çatı @ Upper-floor terrace above a street of houses mod B | Handheld footage filmed on an upper-floor terrace above a street of houses, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a low parapet edge in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| tepe @ Hillside terrace above a village mod A | Handheld footage filmed on a hillside terrace above the village houses, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera follows the tornado; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| tepe @ Hillside terrace above a village mod B | Handheld footage filmed on a hillside terrace above the village houses, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a few leaves at the frame edge; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |
| balkon @ High balcony of a village house mod A | Handheld footage filmed on a high balcony of a village house, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera follows the tornado; one continuous shot, no zoom, no cuts, no person or face close to the camera. | rotasyon dışı |  |
| balkon @ High balcony of a village house mod B | Handheld footage filmed on a high balcony of a village house, high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; slight hand shake, the camera stays fixed, a railing corner in the foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. | aktif |  |

**Ön plan**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| korkuluk (balkon @ High balcony at the edge of a wooded neighborhood mod B) | a railing corner in the foreground | aktif |  |
| boş (balkon @ High balcony at the edge of a wooded neighborhood mod B) | nothing in the foreground | aktif |  |
| parapet (çatı @ Rooftop terrace above a wooded residential area) | a low parapet edge in the foreground | aktif |  |
| boş (çatı @ Rooftop terrace above a wooded residential area) | nothing in the foreground | aktif |  |
| parapet (çatı @ Upper-floor terrace above a street of houses) | a low parapet edge in the foreground | aktif |  |
| boş (çatı @ Upper-floor terrace above a street of houses) | nothing in the foreground | aktif |  |
| yaprak (tepe @ Hillside terrace above a village) | a few leaves at the frame edge | rotasyon dışı |  |
| boş (tepe @ Hillside terrace above a village) | nothing in the foreground | rotasyon dışı |  |
| korkuluk (balkon @ High balcony at the edge of a wooded neighborhood) | a railing corner in the foreground | aktif |  |
| boş (balkon @ High balcony at the edge of a wooded neighborhood) | nothing in the foreground | aktif |  |
| korkuluk (balkon @ High balcony over a tree-lined residential street) | a railing corner in the foreground | aktif |  |
| boş (balkon @ High balcony over a tree-lined residential street) | nothing in the foreground | aktif |  |
| korkuluk (balkon @ High balcony of a village house) | a railing corner in the foreground | aktif |  |
| boş (balkon @ High balcony of a village house) | nothing in the foreground | aktif |  |
| parapet (çatı @ Rooftop terrace above a wooded residential area mod B) | a low parapet edge in the foreground | aktif |  |
| boş (çatı @ Rooftop terrace above a wooded residential area mod B) | nothing in the foreground | aktif |  |
| korkuluk (balkon @ High balcony over a tree-lined residential street mod B) | a railing corner in the foreground | aktif |  |
| boş (balkon @ High balcony over a tree-lined residential street mod B) | nothing in the foreground | aktif |  |
| parapet (çatı @ Upper-floor terrace above a street of houses mod B) | a low parapet edge in the foreground | aktif |  |
| boş (çatı @ Upper-floor terrace above a street of houses mod B) | nothing in the foreground | aktif |  |
| yaprak (tepe @ Hillside terrace above a village mod B) | a few leaves at the frame edge | aktif |  |
| boş (tepe @ Hillside terrace above a village mod B) | nothing in the foreground | aktif |  |
| korkuluk (balkon @ High balcony of a village house mod B) | a railing corner in the foreground | aktif |  |
| boş (balkon @ High balcony of a village house mod B) | nothing in the foreground | aktif |  |

**Ortam**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| forest_edge | orman kenarı yerleşim | aktif |  |
| tree_street | ağaçlık mahalle sokağı | aktif |  |
| village_woods | köy kenarı, çevresi orman | aktif |  |

**Açılış (0-4 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| A | A colossal spinning fire tornado, a twisting funnel several times taller than the houses and trees, tears out of a burning forest into a residential area, its wide base engulfing the houses. | aktif (tek açılış) | 9 Eki 673K |
| ortam forest_edge | A colossal spinning fire tornado, a twisting funnel several times taller than the houses and trees, tears out of a burning forest into a residential area, its wide base engulfing the houses. | aktif (ortama bağlı) |  |
| ortam tree_street | A colossal spinning fire tornado, a twisting funnel several times taller than the houses and trees, tears down a burning tree-lined street, its wide base engulfing the houses and cars along it. | aktif (ortama bağlı) |  |
| ortam village_woods | A colossal spinning fire tornado, a twisting funnel several times taller than the houses and trees, tears from the burning woods into a village, its wide base engulfing the first houses and trees. | aktif (ortama bağlı) |  |

**Işık**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| L1 | hot dry wind and thick smoke haze | aktif |  |
| L2 | gusty dry wind under an orange smoky sky | aktif |  |
| L3 | heavy smoke and scorching still air | aktif |  |
| L4 | hazy early-morning light through drifting smoke | rotasyon dışı |  |
| L5 | harsh bright midday sun through the smoke | rotasyon dışı |  |
| L6 | deep red sunset glow through the smoke | rotasyon dışı |  |
| L7 | dark smoke-filled overcast sky | rotasyon dışı |  |

**Orta (4-9 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| T1 | the towering fire tornado lifts the {vehicle} off the road and flings it into a burning tree | aktif | 26 Eki 176K (aday) |
| T2 | the huge fire tornado hurls a whole burning tree trunk onto the {vehicle}, crushing its roof | aktif |  |
| T4 | the {vehicle} is shoved sideways as the huge base of the fire tornado sweeps past right behind it | aktif | 9 Eki 673K |
| T5 | the huge fire tornado rolls the {vehicle} over onto its roof and it bursts into flames | PASİF |  |
| T6 | huge flaming debris flung by the towering tornado slams into the {vehicle}, which spins and stops across the road | PASİF |  |
| T7 | the {vehicle} races away from the fire tornado as burning debris crashes down behind it | aktif |  |

**Final (9-15 sn)**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| U1 | the fire tornado rips the burning roof off a house across the street into its funnel | aktif |  |
| U2 | the huge fire tornado uproots a cluster of burning trees and flings their trunks down the road | aktif | 9 Eki 673K |
| U6 | the towering fire tornado sweeps over a parked trailer and tosses it aside in fire and smoke | PASİF |  |
| U7 | a wooden house across the street is torn from its foundation, planks spiraling into the funnel | aktif |  |
| U8 | the roofs of two houses across the street are ripped off and sucked into the funnel | aktif | 26 Eki 176K (aday) |
| U9 | the front wall of a house across the street tears away, rubble sucked into the funnel | aktif |  |
| U10 | the porch and steps of a house across the street are ripped off and pulled in | PASİF |  |
| U11 | a wooden garage beside a house across the street bursts apart, burning boards spiraling up | aktif |  |

**İnsan cümlesi**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| forest_edge/1 | {N} people run between the houses below. | kod yedeği |  |
| forest_edge/2 | {N} neighbors flee in the yard below. | kod yedeği |  |
| forest_edge/3 | {N} people sprint away right below. | kod yedeği |  |
| forest_edge/4 | {N} residents run away in the street right below. | kod yedeği |  |
| forest_edge/5 | {N} people dash between the houses below. | kod yedeği |  |
| forest_edge/6 | {N} neighbors run through the yard below. | kod yedeği |  |
| tree_street/1 | {N} people run down the street below. | kod yedeği |  |
| tree_street/2 | {N} residents flee in the street below. | kod yedeği |  |
| tree_street/3 | {N} people sprint away right below. | kod yedeği |  |
| tree_street/4 | {N} neighbors run along the street below. | kod yedeği |  |
| tree_street/5 | {N} people dash away in the street right below. | kod yedeği |  |
| tree_street/6 | {N} residents run across the street below. | kod yedeği |  |
| village_woods/1 | {N} villagers run between the houses below. | kod yedeği |  |
| village_woods/2 | {N} villagers flee down the street below. | kod yedeği |  |
| village_woods/3 | {N} people sprint away right below. | kod yedeği |  |
| village_woods/4 | {N} villagers run through the yard below. | kod yedeği |  |
| village_woods/5 | {N} people run away in the street right below. | kod yedeği |  |
| village_woods/6 | {N} villagers dash in the gardens below. | kod yedeği |  |

**Araç**

| Kimlik | Metin | Durum | Hit |
|---|---|---|---|
| pickup truck | pickup truck | aktif |  |
| delivery truck | delivery truck | aktif |  |
| white van | white van | aktif |  |
| SUV | SUV | aktif |  |

**Spot → kadraj → ön plan (rotasyon)**

| Spot | Rotasyondaki kadraj [ön plan] | Spot kadrajı otomatik getiriyor mu |
|---|---|---|
| High balcony at the edge of a wooded neighborhood | balkon @ High balcony at the edge of a wooded neighborhood mod B [ön plan: korkuluk, boş]; çatı @ Rooftop terrace above a wooded residential area [ön plan: parapet, boş]; çatı @ Upper-floor terrace above a street of houses [ön plan: parapet, boş] | hayır (kadraj ekseni seçer) |
| Rooftop terrace above a wooded residential area | çatı @ Rooftop terrace above a wooded residential area mod B [ön plan: parapet, boş]; balkon @ High balcony at the edge of a wooded neighborhood [ön plan: korkuluk, boş]; balkon @ High balcony over a tree-lined residential street [ön plan: korkuluk, boş]; balkon @ High balcony of a village house [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| High balcony over a tree-lined residential street | balkon @ High balcony over a tree-lined residential street mod B [ön plan: korkuluk, boş]; çatı @ Rooftop terrace above a wooded residential area [ön plan: parapet, boş]; çatı @ Upper-floor terrace above a street of houses [ön plan: parapet, boş] | hayır (kadraj ekseni seçer) |
| Upper-floor terrace above a street of houses | çatı @ Upper-floor terrace above a street of houses mod B [ön plan: parapet, boş]; balkon @ High balcony at the edge of a wooded neighborhood [ön plan: korkuluk, boş]; balkon @ High balcony over a tree-lined residential street [ön plan: korkuluk, boş]; balkon @ High balcony of a village house [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| Hillside terrace above a village | tepe @ Hillside terrace above a village mod B [ön plan: yaprak, boş]; balkon @ High balcony at the edge of a wooded neighborhood [ön plan: korkuluk, boş]; balkon @ High balcony over a tree-lined residential street [ön plan: korkuluk, boş]; balkon @ High balcony of a village house [ön plan: korkuluk, boş] | hayır (kadraj ekseni seçer) |
| High balcony of a village house | balkon @ High balcony of a village house mod B [ön plan: korkuluk, boş]; çatı @ Rooftop terrace above a wooded residential area [ön plan: parapet, boş]; çatı @ Upper-floor terrace above a street of houses [ön plan: parapet, boş] | hayır (kadraj ekseni seçer) |

**Eksen başına aktif seçenek** (havuzdaki aktif/deneme sayısı; 40 basışta gerçekten görülen; ⚠ = 3'ten az; ↔ = iki seçenek arasında sırayla gidip geliyor)

| Eksen | Havuzda aktif | 40 basışta görülen | Uyarı |
|---|---|---|---|
| Spot (kamera noktası) | 6 | 6 |  |
| Kadraj | 11 | 3 |  |
| Ön plan | 22 | 4 |  |
| Ortam | 3 | 3 |  |
| Açılış (0-4 sn) | 4 | 1 | ⚠ 3'ten az |
| Işık | 3 | 3 |  |
| Orta (4-9 sn) | 4 | 4 |  |
| Final (9-15 sn) | 6 | 6 |  |
| İnsan cümlesi | 18 | 0 |  |
| Araç | 4 | 4 |  |

**40 art arda basış (GPT'siz, kod seçimi; geçmiş sıfırdan)**

| seed | spot | kadraj | ön plan | ortam | açılış | orta | final | insan | araç |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Rooftop terrace above a wooded residential area | çatı | boş | forest_edge | A | T1 | U9 | GPT | SUV |
| 2 | Upper-floor terrace above a street of houses | çatı | parapet | tree_street | A | T7 | U11 | GPT | pickup truck |
| 3 | High balcony of a village house | tepe | boş | village_woods | A | T4 | U7 | GPT | delivery truck |
| 4 | Rooftop terrace above a wooded residential area | balkon | korkuluk | forest_edge | A | T2 | U8 | GPT | white van |
| 5 | Upper-floor terrace above a street of houses | çatı | boş | tree_street | A | T1 | U1 | GPT | pickup truck |
| 6 | Hillside terrace above a village | balkon | korkuluk | village_woods | A | T7 | U2 | GPT | delivery truck |
| 7 | High balcony at the edge of a wooded neighborhood | balkon | boş | forest_edge | A | T4 | U9 | GPT | white van |
| 8 | High balcony over a tree-lined residential street | balkon | korkuluk | tree_street | A | T2 | U7 | GPT | pickup truck |
| 9 | Hillside terrace above a village | tepe | boş | village_woods | A | T1 | U8 | GPT | delivery truck |
| 10 | High balcony at the edge of a wooded neighborhood | balkon | korkuluk | forest_edge | A | T7 | U1 | GPT | SUV |
| 11 | High balcony over a tree-lined residential street | balkon | boş | tree_street | A | T4 | U2 | GPT | white van |
| 12 | Hillside terrace above a village | tepe | yaprak | village_woods | A | T2 | U11 | GPT | pickup truck |
| 13 | High balcony at the edge of a wooded neighborhood | balkon | korkuluk | forest_edge | A | T1 | U7 | GPT | delivery truck |
| 14 | Upper-floor terrace above a street of houses | çatı | boş | tree_street | A | T7 | U9 | GPT | white van |
| 15 | Hillside terrace above a village | balkon | boş | village_woods | A | T4 | U1 | GPT | pickup truck |
| 16 | Rooftop terrace above a wooded residential area | balkon | korkuluk | forest_edge | A | T2 | U8 | GPT | delivery truck |
| 17 | Upper-floor terrace above a street of houses | çatı | boş | tree_street | A | T1 | U11 | GPT | SUV |
| 18 | High balcony of a village house | balkon | korkuluk | village_woods | A | T7 | U7 | GPT | pickup truck |
| 19 | Rooftop terrace above a wooded residential area | çatı | boş | forest_edge | A | T4 | U9 | GPT | white van |
| 20 | Upper-floor terrace above a street of houses | balkon | korkuluk | tree_street | A | T2 | U1 | GPT | delivery truck |
| 21 | High balcony of a village house | balkon | boş | village_woods | A | T1 | U8 | GPT | pickup truck |
| 22 | Rooftop terrace above a wooded residential area | çatı | parapet | forest_edge | A | T7 | U11 | GPT | white van |
| 23 | Upper-floor terrace above a street of houses | çatı | boş | tree_street | A | T4 | U7 | GPT | SUV |
| 24 | Hillside terrace above a village | balkon | korkuluk | village_woods | A | T2 | U9 | GPT | pickup truck |
| 25 | Rooftop terrace above a wooded residential area | çatı | boş | forest_edge | A | T1 | U1 | GPT | delivery truck |
| 26 | High balcony over a tree-lined residential street | balkon | korkuluk | tree_street | A | T7 | U8 | GPT | SUV |
| 27 | Hillside terrace above a village | tepe | boş | village_woods | A | T4 | U11 | GPT | pickup truck |
| 28 | High balcony at the edge of a wooded neighborhood | balkon | korkuluk | forest_edge | A | T2 | U7 | GPT | white van |
| 29 | High balcony over a tree-lined residential street | balkon | boş | tree_street | A | T1 | U9 | GPT | SUV |
| 30 | High balcony of a village house | tepe | boş | village_woods | A | T7 | U2 | GPT | delivery truck |
| 31 | Rooftop terrace above a wooded residential area | balkon | boş | forest_edge | A | T4 | U8 | GPT | pickup truck |
| 32 | Upper-floor terrace above a street of houses | çatı | parapet | tree_street | A | T2 | U11 | GPT | SUV |
| 33 | High balcony of a village house | tepe | boş | village_woods | A | T1 | U7 | GPT | white van |
| 34 | High balcony at the edge of a wooded neighborhood | balkon | korkuluk | forest_edge | A | T7 | U1 | GPT | delivery truck |
| 35 | High balcony over a tree-lined residential street | balkon | boş | tree_street | A | T4 | U2 | GPT | SUV |
| 36 | High balcony of a village house | balkon | korkuluk | village_woods | A | T2 | U8 | GPT | pickup truck |
| 37 | Rooftop terrace above a wooded residential area | çatı | boş | forest_edge | A | T1 | U11 | GPT | white van |
| 38 | High balcony over a tree-lined residential street | balkon | korkuluk | tree_street | A | T7 | U9 | GPT | SUV |
| 39 | Hillside terrace above a village | tepe | boş | village_woods | A | T4 | U1 | GPT | pickup truck |
| 40 | Rooftop terrace above a wooded residential area | balkon | korkuluk | forest_edge | A | T2 | U7 | GPT | delivery truck |

