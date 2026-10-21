# Çeşitlilik ölçümü — 21 Ekim 2026 (Aşama 5 sonrası)

Üretim: `scripts/variety_report.py --runs 20 --seed 2026`. Her olayda 20 ardışık üretim, gerçek seçim mantığı, boş geçmişle başlar, her üretim sonrakinin geçmişine eklenir. Hikâye kod yedeğinden (GPT yok). Kie yok, Notion sahte (her üretim bir "Eksenler" kaydı ekler, durum filtresi yok).

**Önce** = Notion eksen geçmişi olmadan (Aşama 3 öncesi davranışın birebir aynısı: `prompt_snapshot.py diff` 0). **Sonra** = Notion eksen geçmişiyle (üretimdeki yol). **Deploy** = her üretimden önce süreç hafızası silinir.

## Aşama 4 sonu → Aşama 5 (normal / deploy)

Ortam: 9 olayda A-E (A = bugünkü görünüm); diğer olaylarda önceki ortam eksenleri. Işık: her olayda sabah, öğle, gün batımı, kapalı/fırtına kapsamı.

| Olay | ortam benzersiz (önce → sonra) | ortam art arda (sonra n / d) | ışık benzersiz (önce → sonra) | ışık art arda (sonra n / d) | tam kopya (önce → sonra, n / d) |
|---|---|---|---|---|---|
| Flash flooding in city streets | 6 → 6 | 0 / 0 | 3 → 5 | 0 / 0 | 0 → 0 / 0 → 0 |
| Tidal wave surges over a coastal city street | 6 → 6 | 0 / 0 | 4 → 7 | 0 / 0 | 0 → 0 / 0 → 0 |
| Mudslide pours down a hillside street | 1 → 5 | 0 / 0 | 3 → 6 | 0 / 0 | 0 → 0 / 0 → 0 |
| Rain-soaked slope collapses onto a roadside | 1 → 5 | 0 / 0 | 3 → 6 | 0 / 0 | 0 → 0 / 0 → 0 |
| Mud and debris torrent tears through a hillside village | 1 → 5 | 0 / 0 | 3 → 6 | 0 / 0 | 0 → 0 / 0 → 0 |
| Tornado making landfall | 1 → 5 | 0 / 0 | 4 → 7 | 0 / 0 | 0 → 0 / 0 → 0 |
| Tornado crosses a marina quay | 1 → 5 | 0 / 0 | 4 → 7 | 0 / 0 | 0 → 0 / 0 → 0 |
| Tornado sweeps down a coastal avenue | 1 → 5 | 0 / 0 | 4 → 7 | 0 / 0 | 0 → 0 / 0 → 0 |
| Wall of flames sweeps into a hillside neighborhood | 1 → 5 | 0 / 0 | 3 → 7 | 0 / 0 | 0 → 0 / 0 → 0 |
| Flames race up a tower facade | 1 → 5 | 0 / 0 | 3 → 7 | 0 / 0 | 0 → 0 / 0 → 0 |
| Fire tornado tears across a burning roadside | 3 → 3 | 0 / 0 | 3 → 7 | 0 / 0 | 0 → 0 / 0 → 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 1 → 5 | 0 / 0 | 3 → 7 | 0 / 0 | 0 → 0 / 0 → 0 |
| Pyroclastic cloud races down into a village street | 4 → 4 | 0 / 0 | 3 → 4 | 0 / 0 | 0 → 0 / 0 → 0 |
| Volcanic bombs slam into a village street | 4 → 4 | 0 / 0 | 4 → 5 | 0 / 0 | 0 → 0 / 0 → 0 |
| Avalanche slams into a mountain village | 11 → 12 | 0 / 0 | 5 → 6 | 0 / 0 | 0 → 0 / 0 → 0 |
| Avalanche crashes down onto a ski lodge | 11 → 11 | 0 / 0 | 5 → 6 | 0 / 0 | 0 → 0 / 0 → 0 |
| Avalanche rips through a pine forest into a valley | 10 → 7 | 0 / 0 | 5 → 6 | 0 / 0 | 0 → 0 / 0 → 0 |
| Earthquake collapses an apartment block | 3 → 3 | 0 / 0 | 4 → 6 | 0 / 0 | 0 → 0 / 0 → 0 |
| Earthquake collapses a row of old stone houses | 6 → 6 | 0 / 0 | 4 → 6 | 0 / 0 | 0 → 0 / 0 → 0 |

Zorunlu tekrarlar (testli): kadraj tekrarı sadece seçilen beat'ler tek güvenli kadraj bıraktığında; ortam tekrarı sadece spotla uyumlu ortamlar son 2 elenince bittiğinde (cadde: yüksek bina spotunda sadece A); ön plan tekrarı sadece K5 sığma koruması devreye girdiğinde (ateş hortumu, orman yangını: kısa "boş" ön plan sığar).

## K5: kod yedeği 175 kelimeye sığıyor mu (tüm kombinasyonlar, `scripts/frame_budget.py`)

| Olay | kombinasyon | kod yedeği sığmıyor: önce | sonra (koruma ile) | sığmayan kadraj varyantı | en uzun stil eki |
|---|---|---|---|---|---|
| Flash flooding in city streets | 2430 | 0 | 0 | 9/15120 | 123 |
| Tidal wave surges over a coastal city street | 2508 | 0 | 0 | 267/23892 | 124 |
| Mudslide pours down a hillside street | 1800 | 0 | 0 | 0/18360 | 112 |
| Rain-soaked slope collapses onto a roadside | 972 | 0 | 0 | 0/10368 | 114 |
| Mud and debris torrent tears through a hillside village | 1194 | 0 | 0 | 0/17886 | 109 |
| Tornado making landfall | 852 | 0 | 0 | 0/8376 | 99 |
| Tornado crosses a marina quay | 600 | 0 | 0 | 0/7080 | 100 |
| Tornado sweeps down a coastal avenue | 896 | 0 | 0 | 0/10192 | 97 |
| Wall of flames sweeps into a hillside neighborhood | 760 | 0 | 0 | 82/9000 | 109 |
| Flames race up a tower facade | 1224 | 0 | 0 | 0/17136 | 109 |
| Fire tornado tears across a burning roadside | 1056 | 0 | 0 | 560/7392 | 100 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 1120 | 0 | 0 | 0/13392 | 103 |
| Pyroclastic cloud races down into a village street | 216 | 0 | 0 | 0/1212 | 113 |
| Volcanic bombs slam into a village street | 1808 | 0 | 0 | 0/11536 | 103 |
| Avalanche slams into a mountain village | 27 | 0 | 0 | 0/96 | 102 |
| Avalanche crashes down onto a ski lodge | 55 | 0 | 0 | 0/280 | 102 |
| Avalanche rips through a pine forest into a valley | 32 | 0 | 0 | 0/142 | 102 |
| Earthquake collapses an apartment block | 25 | 0 | 0 | 0/104 | 95 |
| Earthquake collapses a row of old stone houses | 24 | 0 | 0 | 0/108 | 95 |
| **Toplam** | 17599 | 0 | 0 | 918/171672 | |

## Önce / sonra (Notion eksen geçmişi yok / var)

| Olay | tam kopya normal (önce → sonra) | tam kopya deploy (önce → sonra) | art arda tekrar, 5 LRU ekseni normal (önce → sonra) | art arda tekrar, 5 LRU ekseni deploy (önce → sonra) |
|---|---|---|---|---|
| Flash flooding in city streets | 0 → 0 | 0 → 0 | 22 → 0 | 22 → 0 |
| Tidal wave surges over a coastal city street | 0 → 0 | 0 → 0 | 30 → 0 | 30 → 0 |
| Mudslide pours down a hillside street | 0 → 0 | 0 → 0 | 31 → 0 | 31 → 0 |
| Rain-soaked slope collapses onto a roadside | 0 → 0 | 0 → 0 | 39 → 0 | 39 → 0 |
| Mud and debris torrent tears through a hillside village | 0 → 0 | 0 → 0 | 35 → 0 | 35 → 0 |
| Tornado making landfall | 1 → 0 | 1 → 0 | 30 → 0 | 30 → 0 |
| Tornado crosses a marina quay | 0 → 0 | 0 → 0 | 48 → 19 | 48 → 19 |
| Tornado sweeps down a coastal avenue | 1 → 0 | 1 → 0 | 36 → 0 | 36 → 0 |
| Wall of flames sweeps into a hillside neighborhood | 0 → 0 | 0 → 0 | 41 → 0 | 41 → 0 |
| Flames race up a tower facade | 0 → 0 | 0 → 0 | 34 → 0 | 34 → 0 |
| Fire tornado tears across a burning roadside | 0 → 0 | 0 → 0 | 32 → 2 | 42 → 2 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 1 → 0 | 1 → 0 | 33 → 0 | 33 → 0 |
| Pyroclastic cloud races down into a village street | 0 → 0 | 0 → 0 | 31 → 0 | 36 → 0 |
| Volcanic bombs slam into a village street | 0 → 0 | 0 → 0 | 26 → 0 | 31 → 0 |
| Avalanche slams into a mountain village | 0 → 0 | 0 → 0 | 13 → 0 | 28 → 0 |
| Avalanche crashes down onto a ski lodge | 0 → 0 | 0 → 0 | 10 → 0 | 26 → 0 |
| Avalanche rips through a pine forest into a valley | 0 → 0 | 1 → 0 | 20 → 1 | 36 → 1 |
| Earthquake collapses an apartment block | 0 → 0 | 0 → 0 | 11 → 0 | 42 → 0 |
| Earthquake collapses a row of old stone houses | 0 → 0 | 0 → 0 | 15 → 0 | 39 → 0 |

## Sonra, normal (süreç hafızası korunur)

Hücre biçimi: `benzersiz değer sayısı / arka arkaya aynı değer sayısı` (en fazla 19). "—" olan eksen tekrar sayılmaz.

| Olay | ortam (benzersiz / art arda) | spot (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | kadraj (benzersiz / art arda) | ön plan (benzersiz / art arda) | kamera modu (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 4 / 0 | 5 / 0 | 7 / 0 | 1 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 1 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 0 | 7 / 0 | 7 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 5 / 0 | 6 / 0 | 3 / 0 | 0 |
| Mudslide pours down a hillside street | 5 / 0 | 3 / 0 | 6 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Rain-soaked slope collapses onto a roadside | 5 / 0 | 2 / 0 | 6 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 18 / 0 | 3 / 0 | 4 / 0 | 1 / 0 | 0 |
| Mud and debris torrent tears through a hillside village | 5 / 0 | 3 / 0 | 6 / 0 | 3 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 6 / 0 | 3 / 0 | 0 |
| Tornado making landfall | 5 / 0 | 3 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 4 / 0 | 4 / 0 | 1 / 0 | 0 |
| Tornado crosses a marina quay | 5 / 0 | 1 / 19 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 3 / 0 | 0 |
| Tornado sweeps down a coastal avenue | 5 / 0 | 3 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 3 / 0 | 0 |
| Wall of flames sweeps into a hillside neighborhood | 5 / 0 | 2 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 18 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Flames race up a tower facade | 5 / 0 | 4 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 15 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Fire tornado tears across a burning roadside | 3 / 0 | 6 / 0 | 7 / 0 | 4 / 0 | 2 / 0 | 3 / 0 | 20 / 0 | 3 / 0 | 5 / 2 | 3 / 0 | 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 5 / 0 | 2 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Pyroclastic cloud races down into a village street | 4 / 0 | 3 / 0 | 4 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 18 / 0 | 4 / 0 | 3 / 0 | 1 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 0 | 3 / 0 | 5 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche slams into a mountain village | 12 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 17 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 11 / 0 | 3 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 7 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 3 / 1 | 3 / 0 | 1 / 0 | 0 |
| Earthquake collapses an apartment block | 3 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 16 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Earthquake collapses a row of old stone houses | 6 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 14 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |

## Sonra, her üretimden önce deploy

| Olay | ortam (benzersiz / art arda) | spot (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | kadraj (benzersiz / art arda) | ön plan (benzersiz / art arda) | kamera modu (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 4 / 0 | 5 / 0 | 7 / 0 | 1 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 1 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 0 | 7 / 0 | 7 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 5 / 0 | 6 / 0 | 3 / 0 | 0 |
| Mudslide pours down a hillside street | 5 / 0 | 3 / 0 | 6 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Rain-soaked slope collapses onto a roadside | 5 / 0 | 2 / 0 | 6 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 18 / 0 | 3 / 0 | 4 / 0 | 1 / 0 | 0 |
| Mud and debris torrent tears through a hillside village | 5 / 0 | 3 / 0 | 6 / 0 | 3 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 6 / 0 | 3 / 0 | 0 |
| Tornado making landfall | 5 / 0 | 3 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 4 / 0 | 4 / 0 | 1 / 0 | 0 |
| Tornado crosses a marina quay | 5 / 0 | 1 / 19 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 3 / 0 | 0 |
| Tornado sweeps down a coastal avenue | 5 / 0 | 3 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 3 / 0 | 0 |
| Wall of flames sweeps into a hillside neighborhood | 5 / 0 | 2 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 18 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Flames race up a tower facade | 5 / 0 | 4 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 15 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Fire tornado tears across a burning roadside | 3 / 0 | 6 / 0 | 7 / 0 | 4 / 0 | 2 / 0 | 3 / 0 | 20 / 0 | 3 / 0 | 5 / 2 | 3 / 0 | 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 5 / 0 | 2 / 0 | 7 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Pyroclastic cloud races down into a village street | 4 / 0 | 3 / 0 | 4 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 18 / 0 | 4 / 0 | 3 / 0 | 1 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 0 | 3 / 0 | 5 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche slams into a mountain village | 12 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 17 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 11 / 0 | 3 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 7 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 3 / 1 | 3 / 0 | 1 / 0 | 0 |
| Earthquake collapses an apartment block | 3 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 16 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Earthquake collapses a row of old stone houses | 6 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 14 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |

## Önce, normal (karşılaştırma için)

| Olay | ortam (benzersiz / art arda) | spot (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | kadraj (benzersiz / art arda) | ön plan (benzersiz / art arda) | kamera modu (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 3 / 8 | 6 / 2 | 7 / 2 | 1 / 0 | 1 / 19 | 20 / 0 | 4 / 7 | 5 / 3 | 1 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 7 | 7 / 3 | 8 / 4 | 4 / 9 | 1 / 19 | 20 / 0 | 5 / 4 | 6 / 3 | 3 / 0 | 0 |
| Mudslide pours down a hillside street | 5 / 4 | 3 / 5 | 5 / 5 | 3 / 5 | 4 / 4 | 1 / 19 | 20 / 0 | 3 / 6 | 5 / 2 | 3 / 0 | 0 |
| Rain-soaked slope collapses onto a roadside | 4 / 5 | 2 / 8 | 6 / 4 | 3 / 5 | 4 / 5 | 1 / 19 | 19 / 0 | 3 / 5 | 4 / 7 | 1 / 0 | 0 |
| Mud and debris torrent tears through a hillside village | 5 / 6 | 3 / 8 | 5 / 1 | 3 / 4 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 5 | 6 / 5 | 3 / 0 | 0 |
| Tornado making landfall | 5 / 4 | 3 / 6 | 7 / 3 | 4 / 3 | 4 / 3 | 1 / 19 | 16 / 0 | 4 / 6 | 5 / 5 | 1 / 0 | 1 |
| Tornado crosses a marina quay | 5 / 3 | 1 / 19 | 6 / 1 | 4 / 7 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 7 | 5 / 3 | 3 / 2 | 0 |
| Tornado sweeps down a coastal avenue | 4 / 9 | 3 / 4 | 7 / 1 | 4 / 4 | 4 / 4 | 1 / 19 | 20 / 0 | 4 / 8 | 5 / 4 | 3 / 2 | 1 |
| Wall of flames sweeps into a hillside neighborhood | 5 / 4 | 2 / 10 | 6 / 5 | 4 / 8 | 4 / 5 | 1 / 19 | 20 / 0 | 3 / 4 | 5 / 4 | 3 / 1 | 0 |
| Flames race up a tower facade | 5 / 5 | 4 / 4 | 7 / 2 | 4 / 5 | 4 / 4 | 1 / 19 | 16 / 0 | 3 / 8 | 5 / 6 | 3 / 0 | 0 |
| Fire tornado tears across a burning roadside | 3 / 0 | 6 / 0 | 7 / 1 | 4 / 3 | 2 / 13 | 3 / 0 | 20 / 0 | 3 / 10 | 5 / 5 | 3 / 0 | 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 5 / 5 | 2 / 10 | 6 / 4 | 4 / 3 | 4 / 3 | 1 / 19 | 20 / 0 | 3 / 2 | 5 / 3 | 3 / 3 | 1 |
| Pyroclastic cloud races down into a village street | 4 / 0 | 3 / 0 | 4 / 8 | 1 / 0 | 4 / 8 | 1 / 19 | 17 / 0 | 4 / 8 | 3 / 7 | 1 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 0 | 3 / 0 | 5 / 1 | 4 / 5 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 6 | 3 / 8 | 1 / 0 | 0 |
| Avalanche slams into a mountain village | 12 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 3 | 1 / 19 | 17 / 0 | 3 / 3 | 3 / 7 | 1 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 9 / 0 | 3 / 0 | 7 / 0 | 1 / 0 | 4 / 5 | 1 / 19 | 20 / 0 | 3 / 1 | 3 / 4 | 1 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 11 / 0 | 2 / 0 | 7 / 0 | 1 / 0 | 4 / 7 | 1 / 19 | 19 / 0 | 3 / 4 | 3 / 9 | 1 / 0 | 0 |
| Earthquake collapses an apartment block | 3 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 3 | 1 / 19 | 16 / 0 | 3 / 4 | 3 / 4 | 1 / 0 | 0 |
| Earthquake collapses a row of old stone houses | 6 / 0 | 2 / 0 | 6 / 0 | 1 / 0 | 4 / 3 | 1 / 19 | 14 / 0 | 3 / 7 | 3 / 5 | 1 / 0 | 0 |

## Önce, her üretimden önce deploy (karşılaştırma için)

| Olay | ortam (benzersiz / art arda) | spot (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | kadraj (benzersiz / art arda) | ön plan (benzersiz / art arda) | kamera modu (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 3 / 8 | 6 / 2 | 7 / 2 | 1 / 0 | 1 / 19 | 20 / 0 | 4 / 7 | 5 / 3 | 1 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 7 | 7 / 3 | 8 / 4 | 4 / 9 | 1 / 19 | 20 / 0 | 5 / 4 | 6 / 3 | 3 / 0 | 0 |
| Mudslide pours down a hillside street | 5 / 4 | 3 / 5 | 5 / 5 | 3 / 5 | 4 / 4 | 1 / 19 | 20 / 0 | 3 / 6 | 5 / 2 | 3 / 0 | 0 |
| Rain-soaked slope collapses onto a roadside | 4 / 5 | 2 / 8 | 6 / 4 | 3 / 5 | 4 / 5 | 1 / 19 | 19 / 0 | 3 / 5 | 4 / 7 | 1 / 0 | 0 |
| Mud and debris torrent tears through a hillside village | 5 / 6 | 3 / 8 | 5 / 1 | 3 / 4 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 5 | 6 / 5 | 3 / 0 | 0 |
| Tornado making landfall | 5 / 4 | 3 / 6 | 7 / 3 | 4 / 3 | 4 / 3 | 1 / 19 | 16 / 0 | 4 / 6 | 5 / 5 | 1 / 0 | 1 |
| Tornado crosses a marina quay | 5 / 3 | 1 / 19 | 6 / 1 | 4 / 7 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 7 | 5 / 3 | 3 / 2 | 0 |
| Tornado sweeps down a coastal avenue | 4 / 9 | 3 / 4 | 7 / 1 | 4 / 4 | 4 / 4 | 1 / 19 | 20 / 0 | 4 / 8 | 5 / 4 | 3 / 2 | 1 |
| Wall of flames sweeps into a hillside neighborhood | 5 / 4 | 2 / 10 | 6 / 5 | 4 / 8 | 4 / 5 | 1 / 19 | 20 / 0 | 3 / 4 | 5 / 4 | 3 / 1 | 0 |
| Flames race up a tower facade | 5 / 5 | 4 / 4 | 7 / 2 | 4 / 5 | 4 / 4 | 1 / 19 | 16 / 0 | 3 / 8 | 5 / 6 | 3 / 0 | 0 |
| Fire tornado tears across a burning roadside | 3 / 7 | 5 / 5 | 7 / 3 | 4 / 4 | 2 / 8 | 3 / 7 | 20 / 0 | 3 / 7 | 4 / 6 | 3 / 2 | 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 5 / 5 | 2 / 10 | 6 / 4 | 4 / 3 | 4 / 3 | 1 / 19 | 20 / 0 | 3 / 2 | 5 / 3 | 3 / 3 | 1 |
| Pyroclastic cloud races down into a village street | 4 / 5 | 3 / 0 | 4 / 8 | 1 / 0 | 4 / 8 | 1 / 19 | 17 / 0 | 4 / 8 | 3 / 7 | 1 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 5 | 3 / 0 | 5 / 1 | 4 / 5 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 6 | 3 / 8 | 1 / 0 | 0 |
| Avalanche slams into a mountain village | 10 / 0 | 2 / 14 | 7 / 0 | 1 / 0 | 3 / 3 | 1 / 19 | 13 / 0 | 3 / 6 | 3 / 5 | 1 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 13 / 0 | 3 / 8 | 7 / 2 | 1 / 0 | 4 / 6 | 1 / 19 | 18 / 0 | 3 / 5 | 3 / 5 | 1 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 11 / 2 | 2 / 13 | 7 / 2 | 1 / 0 | 3 / 7 | 1 / 19 | 17 / 0 | 3 / 7 | 3 / 5 | 1 / 0 | 1 |
| Earthquake collapses an apartment block | 6 / 5 | 2 / 13 | 6 / 3 | 1 / 0 | 4 / 4 | 1 / 19 | 14 / 0 | 3 / 9 | 3 / 8 | 1 / 0 | 0 |
| Earthquake collapses a row of old stone houses | 6 / 2 | 2 / 14 | 6 / 2 | 1 / 0 | 4 / 3 | 1 / 19 | 12 / 0 | 3 / 10 | 3 / 8 | 1 / 0 | 0 |

## Sıralama

**Önce en kötü 5 (normal) ve sonraki durumları:**
- Firefighting helicopter drops water on the flames racing toward a hillside neighborhood: tam kopya 1 → 0
- Tornado sweeps down a coastal avenue: tam kopya 1 → 0
- Tornado making landfall: tam kopya 1 → 0
- Tornado crosses a marina quay: tam kopya 0 → 0
- Wall of flames sweeps into a hillside neighborhood: tam kopya 0 → 0

**Sonra en kötü 5 (normal):**
- Tornado crosses a marina quay: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 38
- Earthquake collapses a row of old stone houses: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 19
- Earthquake collapses an apartment block: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 19
- Avalanche rips through a pine forest into a valley: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 19
- Avalanche crashes down onto a ski lodge: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 19

**Sonra en iyi 3 (normal):**
- Fire tornado tears across a burning roadside: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 0
- Flash flooding in city streets: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 19
- Tidal wave surges over a coastal city street: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 19

## Tek seçenekli eksenler (tekrar önleme uygulanamaz)

- Tornado crosses a marina quay: spot

Kilit cümle ateş hortumu dışında her olayda tek (açılış varyantları sonraki aşamada).

