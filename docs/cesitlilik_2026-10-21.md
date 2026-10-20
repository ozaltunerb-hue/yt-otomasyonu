# Çeşitlilik ölçümü — 21 Ekim 2026 (Aşama 4 sonrası)

Üretim: `scripts/variety_report.py --runs 20 --seed 2026`. Her olayda 20 ardışık üretim, gerçek seçim mantığı, boş geçmişle başlar, her üretim sonrakinin geçmişine eklenir. Hikâye kod yedeğinden (GPT yok). Kie yok, Notion sahte (her üretim bir "Eksenler" kaydı ekler, durum filtresi yok).

**Önce** = Notion eksen geçmişi olmadan (Aşama 3 öncesi davranışın birebir aynısı: `prompt_snapshot.py diff` 0). **Sonra** = Notion eksen geçmişiyle (üretimdeki yol). **Deploy** = her üretimden önce süreç hafızası silinir.

## Aşama 3 sonu → Aşama 4 (normal / deploy)

Kamera: Aşama 3'te kamera = spot (spot başına tek cümle); Aşama 4'te kadraj × kamera noktası × ön plan × mod. `spot` sütunu Aşama 3'te aynı zamanda kameraydı.

| Olay | tam kopya normal (önce → sonra) | tam kopya deploy | spot/kamera art arda (önce) | kadraj art arda (sonra n / d) | ön plan art arda (sonra n / d) | kamera modu art arda (sonra n / d) | benzersiz kadraj / ön plan / mod |
|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 4 / 5 / 1 |
| Tidal wave surges over a coastal city street | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 5 / 6 / 3 |
| Mudslide pours down a hillside street | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 3 / 4 / 3 |
| Rain-soaked slope collapses onto a roadside | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 3 / 4 / 1 |
| Mud and debris torrent tears through a hillside village | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 4 / 5 / 3 |
| Tornado making landfall | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 4 / 5 / 1 |
| Tornado crosses a marina quay | 0 → 0 | 0 → 0 | 19 / 19 | 0 / 0 | 0 / 0 | 0 / 0 | 4 / 4 / 3 |
| Tornado sweeps down a coastal avenue | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 4 / 5 / 3 |
| Wall of flames sweeps into a hillside neighborhood | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 3 / 5 / 3 |
| Flames race up a tower facade | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 3 / 4 / 3 |
| Fire tornado tears across a burning roadside | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 3 / 5 / 3 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 3 / 5 / 3 |
| Pyroclastic cloud races down into a village street | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 4 / 3 / 1 |
| Volcanic bombs slam into a village street | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 4 / 3 / 1 |
| Avalanche slams into a mountain village | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 3 / 3 / 1 |
| Avalanche crashes down onto a ski lodge | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 3 / 3 / 1 |
| Avalanche rips through a pine forest into a valley | 0 → 0 | 0 → 0 | 0 / 0 | 2 / 2 | 0 / 0 | 0 / 0 | 3 / 3 / 1 |
| Earthquake collapses an apartment block | 0 → 0 | 0 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 3 / 3 / 1 |
| Earthquake collapses a row of old stone houses | 0 → 0 | 0 → 0 | 0 / 0 | 2 / 2 | 0 / 0 | 0 / 0 | 3 / 3 / 1 |

Kadraj tekrarı sadece seçilen beat'lerin dışlamaları tek güvenli kadraj bıraktığında olur (çığ orman, eski sokak; `tests/test_axes_history.py` her tekrarı bu koşulla doğrular). Marina rıhtımında spot tek, kadraj 4.

## K5: kod yedeği 175 kelimeye sığıyor mu (tüm kombinasyonlar, `scripts/frame_budget.py`)

| Olay | kombinasyon | kod yedeği sığmıyor: önce | sonra (koruma ile) | sığmayan kadraj varyantı | en uzun stil eki |
|---|---|---|---|---|---|
| Flash flooding in city streets | 2430 | 0 | 0 | 9/15120 | 123 |
| Tidal wave surges over a coastal city street | 2508 | 0 | 0 | 267/26772 | 124 |
| Mudslide pours down a hillside street | 360 | 0 | 0 | 0/2520 | 94 |
| Rain-soaked slope collapses onto a roadside | 216 | 0 | 0 | 0/1296 | 94 |
| Mud and debris torrent tears through a hillside village | 258 | 0 | 0 | 0/2658 | 94 |
| Tornado making landfall | 216 | 0 | 0 | 0/1272 | 86 |
| Tornado crosses a marina quay | 120 | 0 | 0 | 0/840 | 84 |
| Tornado sweeps down a coastal avenue | 336 | 0 | 0 | 0/2352 | 84 |
| Wall of flames sweeps into a hillside neighborhood | 152 | 0 | 0 | 0/1120 | 94 |
| Flames race up a tower facade | 272 | 0 | 0 | 0/2720 | 95 |
| Fire tornado tears across a burning roadside | 1056 | 0 | 0 | 560/8448 | 100 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 224 | 0 | 0 | 0/1672 | 90 |
| Pyroclastic cloud races down into a village street | 216 | 0 | 0 | 0/1212 | 113 |
| Volcanic bombs slam into a village street | 1808 | 0 | 0 | 0/11536 | 103 |
| Avalanche slams into a mountain village | 27 | 0 | 0 | 0/96 | 102 |
| Avalanche crashes down onto a ski lodge | 55 | 0 | 0 | 0/280 | 102 |
| Avalanche rips through a pine forest into a valley | 32 | 0 | 0 | 0/142 | 102 |
| Earthquake collapses an apartment block | 25 | 0 | 0 | 0/104 | 95 |
| Earthquake collapses a row of old stone houses | 24 | 0 | 0 | 0/108 | 95 |
| **Toplam** | 10335 | 0 | 0 | 836/80268 | |

Sığmayan kadraj varyantları üretimde seçilmez: sığma koruması aynı spotta sığan başka bir varyant seçer (tekrar önlemeye uyanlar önce).

## Önce / sonra (Notion eksen geçmişi yok / var)

| Olay | tam kopya normal (önce → sonra) | tam kopya deploy (önce → sonra) | art arda tekrar, 5 LRU ekseni normal (önce → sonra) | art arda tekrar, 5 LRU ekseni deploy (önce → sonra) |
|---|---|---|---|---|
| Flash flooding in city streets | 0 → 0 | 0 → 0 | 27 → 0 | 27 → 0 |
| Tidal wave surges over a coastal city street | 0 → 0 | 0 → 0 | 34 → 0 | 34 → 0 |
| Mudslide pours down a hillside street | 0 → 0 | 0 → 0 | 34 → 0 | 34 → 0 |
| Rain-soaked slope collapses onto a roadside | 2 → 0 | 2 → 0 | 34 → 0 | 34 → 0 |
| Mud and debris torrent tears through a hillside village | 3 → 0 | 3 → 0 | 37 → 0 | 37 → 0 |
| Tornado making landfall | 3 → 0 | 3 → 0 | 30 → 0 | 30 → 0 |
| Tornado crosses a marina quay | 3 → 0 | 3 → 0 | 49 → 19 | 49 → 19 |
| Tornado sweeps down a coastal avenue | 1 → 0 | 1 → 0 | 30 → 0 | 30 → 0 |
| Wall of flames sweeps into a hillside neighborhood | 4 → 0 | 4 → 0 | 44 → 0 | 44 → 0 |
| Flames race up a tower facade | 2 → 0 | 2 → 0 | 37 → 0 | 37 → 0 |
| Fire tornado tears across a burning roadside | 0 → 0 | 3 → 0 | 34 → 0 | 49 → 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 4 → 0 | 4 → 0 | 36 → 0 | 36 → 0 |
| Pyroclastic cloud races down into a village street | 0 → 0 | 0 → 0 | 29 → 0 | 34 → 0 |
| Volcanic bombs slam into a village street | 0 → 0 | 0 → 0 | 29 → 0 | 34 → 0 |
| Avalanche slams into a mountain village | 0 → 0 | 0 → 0 | 15 → 0 | 30 → 0 |
| Avalanche crashes down onto a ski lodge | 0 → 0 | 0 → 0 | 13 → 0 | 27 → 0 |
| Avalanche rips through a pine forest into a valley | 0 → 0 | 0 → 0 | 25 → 2 | 37 → 2 |
| Earthquake collapses an apartment block | 0 → 0 | 1 → 0 | 16 → 0 | 43 → 0 |
| Earthquake collapses a row of old stone houses | 0 → 0 | 0 → 0 | 11 → 2 | 41 → 2 |

## Sonra, normal (süreç hafızası korunur)

Hücre biçimi: `benzersiz değer sayısı / arka arkaya aynı değer sayısı` (en fazla 19). "—" olan eksen tekrar sayılmaz.

| Olay | ortam (benzersiz / art arda) | spot (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | kadraj (benzersiz / art arda) | ön plan (benzersiz / art arda) | kamera modu (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 4 / 0 | 3 / 0 | 7 / 0 | 1 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 1 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 0 | 4 / 0 | 8 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 5 / 0 | 6 / 0 | 3 / 0 | 0 |
| Mudslide pours down a hillside street | 1 / 0 | 3 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 4 / 0 | 3 / 0 | 0 |
| Rain-soaked slope collapses onto a roadside | 1 / 0 | 2 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 4 / 0 | 1 / 0 | 0 |
| Mud and debris torrent tears through a hillside village | 1 / 0 | 3 / 0 | 3 / 0 | 3 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 3 / 0 | 0 |
| Tornado making landfall | 1 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 17 / 0 | 4 / 0 | 5 / 0 | 1 / 0 | 0 |
| Tornado crosses a marina quay | 1 / 0 | 1 / 19 | 4 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 4 / 0 | 3 / 0 | 0 |
| Tornado sweeps down a coastal avenue | 1 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 3 / 0 | 0 |
| Wall of flames sweeps into a hillside neighborhood | 1 / 0 | 2 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Flames race up a tower facade | 1 / 0 | 4 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 16 / 0 | 3 / 0 | 4 / 0 | 3 / 0 | 0 |
| Fire tornado tears across a burning roadside | 3 / 0 | 6 / 0 | 3 / 0 | 4 / 0 | 2 / 0 | 3 / 0 | 20 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 1 / 0 | 2 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Pyroclastic cloud races down into a village street | 4 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 18 / 0 | 4 / 0 | 3 / 0 | 1 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche slams into a mountain village | 11 / 0 | 2 / 0 | 5 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 15 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 11 / 0 | 3 / 0 | 5 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 10 / 0 | 2 / 0 | 5 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 3 / 2 | 3 / 0 | 1 / 0 | 0 |
| Earthquake collapses an apartment block | 3 / 0 | 2 / 0 | 4 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 15 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Earthquake collapses a row of old stone houses | 6 / 0 | 2 / 0 | 4 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 14 / 0 | 3 / 2 | 3 / 0 | 1 / 0 | 0 |

## Sonra, her üretimden önce deploy

| Olay | ortam (benzersiz / art arda) | spot (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | kadraj (benzersiz / art arda) | ön plan (benzersiz / art arda) | kamera modu (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 4 / 0 | 3 / 0 | 7 / 0 | 1 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 1 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 0 | 4 / 0 | 8 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 5 / 0 | 6 / 0 | 3 / 0 | 0 |
| Mudslide pours down a hillside street | 1 / 0 | 3 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 4 / 0 | 3 / 0 | 0 |
| Rain-soaked slope collapses onto a roadside | 1 / 0 | 2 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 4 / 0 | 1 / 0 | 0 |
| Mud and debris torrent tears through a hillside village | 1 / 0 | 3 / 0 | 3 / 0 | 3 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 3 / 0 | 0 |
| Tornado making landfall | 1 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 17 / 0 | 4 / 0 | 5 / 0 | 1 / 0 | 0 |
| Tornado crosses a marina quay | 1 / 0 | 1 / 19 | 4 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 4 / 0 | 3 / 0 | 0 |
| Tornado sweeps down a coastal avenue | 1 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 5 / 0 | 3 / 0 | 0 |
| Wall of flames sweeps into a hillside neighborhood | 1 / 0 | 2 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Flames race up a tower facade | 1 / 0 | 4 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 16 / 0 | 3 / 0 | 4 / 0 | 3 / 0 | 0 |
| Fire tornado tears across a burning roadside | 3 / 0 | 6 / 0 | 3 / 0 | 4 / 0 | 2 / 0 | 3 / 0 | 20 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 1 / 0 | 2 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 3 / 0 | 5 / 0 | 3 / 0 | 0 |
| Pyroclastic cloud races down into a village street | 4 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 18 / 0 | 4 / 0 | 3 / 0 | 1 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 0 | 3 / 0 | 4 / 0 | 4 / 0 | 4 / 0 | 1 / 19 | 20 / 0 | 4 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche slams into a mountain village | 11 / 0 | 2 / 0 | 5 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 15 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 11 / 0 | 3 / 0 | 5 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 10 / 0 | 2 / 0 | 5 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 19 / 0 | 3 / 2 | 3 / 0 | 1 / 0 | 0 |
| Earthquake collapses an apartment block | 3 / 0 | 2 / 0 | 4 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 15 / 0 | 3 / 0 | 3 / 0 | 1 / 0 | 0 |
| Earthquake collapses a row of old stone houses | 6 / 0 | 2 / 0 | 4 / 0 | 1 / 0 | 4 / 0 | 1 / 19 | 14 / 0 | 3 / 2 | 3 / 0 | 1 / 0 | 0 |

## Önce, normal (karşılaştırma için)

| Olay | ortam (benzersiz / art arda) | spot (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | kadraj (benzersiz / art arda) | ön plan (benzersiz / art arda) | kamera modu (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 3 / 8 | 3 / 7 | 7 / 2 | 1 / 0 | 1 / 19 | 20 / 0 | 4 / 7 | 5 / 3 | 1 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 7 | 4 / 6 | 8 / 4 | 4 / 9 | 1 / 19 | 20 / 0 | 5 / 4 | 6 / 2 | 3 / 2 | 0 |
| Mudslide pours down a hillside street | 1 / 0 | 3 / 5 | 3 / 4 | 3 / 5 | 4 / 4 | 1 / 19 | 20 / 0 | 3 / 6 | 5 / 3 | 3 / 7 | 0 |
| Rain-soaked slope collapses onto a roadside | 1 / 0 | 2 / 8 | 3 / 4 | 3 / 5 | 4 / 5 | 1 / 19 | 19 / 0 | 3 / 5 | 4 / 7 | 1 / 0 | 2 |
| Mud and debris torrent tears through a hillside village | 1 / 0 | 3 / 8 | 3 / 6 | 3 / 4 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 5 | 5 / 3 | 3 / 5 | 3 |
| Tornado making landfall | 1 / 0 | 3 / 6 | 3 / 6 | 4 / 3 | 4 / 3 | 1 / 19 | 16 / 0 | 4 / 6 | 5 / 6 | 1 / 0 | 3 |
| Tornado crosses a marina quay | 1 / 0 | 1 / 19 | 4 / 3 | 4 / 7 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 8 | 5 / 4 | 3 / 2 | 3 |
| Tornado sweeps down a coastal avenue | 1 / 0 | 3 / 4 | 4 / 4 | 4 / 4 | 4 / 4 | 1 / 19 | 20 / 0 | 4 / 8 | 5 / 4 | 3 / 2 | 1 |
| Wall of flames sweeps into a hillside neighborhood | 1 / 0 | 2 / 11 | 3 / 6 | 4 / 5 | 4 / 8 | 1 / 19 | 20 / 0 | 3 / 4 | 4 / 5 | 3 / 5 | 4 |
| Flames race up a tower facade | 1 / 0 | 4 / 4 | 3 / 7 | 4 / 5 | 4 / 4 | 1 / 19 | 16 / 0 | 3 / 8 | 5 / 6 | 3 / 3 | 2 |
| Fire tornado tears across a burning roadside | 3 / 0 | 6 / 0 | 3 / 4 | 4 / 3 | 2 / 13 | 3 / 0 | 20 / 0 | 3 / 10 | 4 / 2 | 3 / 2 | 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 1 / 0 | 2 / 10 | 3 / 8 | 4 / 3 | 4 / 3 | 1 / 19 | 20 / 0 | 3 / 2 | 5 / 3 | 3 / 7 | 4 |
| Pyroclastic cloud races down into a village street | 4 / 0 | 3 / 0 | 3 / 6 | 1 / 0 | 4 / 8 | 1 / 19 | 17 / 0 | 4 / 8 | 3 / 7 | 1 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 0 | 3 / 0 | 4 / 4 | 4 / 5 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 6 | 3 / 8 | 1 / 0 | 0 |
| Avalanche slams into a mountain village | 11 / 0 | 2 / 0 | 5 / 0 | 1 / 0 | 4 / 6 | 1 / 19 | 15 / 0 | 3 / 4 | 3 / 5 | 1 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 11 / 0 | 3 / 0 | 5 / 0 | 1 / 0 | 4 / 6 | 1 / 19 | 20 / 0 | 3 / 4 | 3 / 3 | 1 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 12 / 0 | 2 / 0 | 5 / 0 | 1 / 0 | 4 / 5 | 1 / 19 | 18 / 0 | 3 / 11 | 3 / 9 | 1 / 0 | 0 |
| Earthquake collapses an apartment block | 3 / 0 | 2 / 0 | 4 / 0 | 1 / 0 | 4 / 3 | 1 / 19 | 15 / 0 | 3 / 5 | 3 / 8 | 1 / 0 | 0 |
| Earthquake collapses a row of old stone houses | 6 / 0 | 2 / 0 | 4 / 0 | 1 / 0 | 4 / 3 | 1 / 19 | 14 / 0 | 3 / 4 | 3 / 4 | 1 / 0 | 0 |

## Önce, her üretimden önce deploy (karşılaştırma için)

| Olay | ortam (benzersiz / art arda) | spot (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | kadraj (benzersiz / art arda) | ön plan (benzersiz / art arda) | kamera modu (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 3 / 8 | 3 / 7 | 7 / 2 | 1 / 0 | 1 / 19 | 20 / 0 | 4 / 7 | 5 / 3 | 1 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 7 | 4 / 6 | 8 / 4 | 4 / 9 | 1 / 19 | 20 / 0 | 5 / 4 | 6 / 2 | 3 / 2 | 0 |
| Mudslide pours down a hillside street | 1 / 0 | 3 / 5 | 3 / 4 | 3 / 5 | 4 / 4 | 1 / 19 | 20 / 0 | 3 / 6 | 5 / 3 | 3 / 7 | 0 |
| Rain-soaked slope collapses onto a roadside | 1 / 0 | 2 / 8 | 3 / 4 | 3 / 5 | 4 / 5 | 1 / 19 | 19 / 0 | 3 / 5 | 4 / 7 | 1 / 0 | 2 |
| Mud and debris torrent tears through a hillside village | 1 / 0 | 3 / 8 | 3 / 6 | 3 / 4 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 5 | 5 / 3 | 3 / 5 | 3 |
| Tornado making landfall | 1 / 0 | 3 / 6 | 3 / 6 | 4 / 3 | 4 / 3 | 1 / 19 | 16 / 0 | 4 / 6 | 5 / 6 | 1 / 0 | 3 |
| Tornado crosses a marina quay | 1 / 0 | 1 / 19 | 4 / 3 | 4 / 7 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 8 | 5 / 4 | 3 / 2 | 3 |
| Tornado sweeps down a coastal avenue | 1 / 0 | 3 / 4 | 4 / 4 | 4 / 4 | 4 / 4 | 1 / 19 | 20 / 0 | 4 / 8 | 5 / 4 | 3 / 2 | 1 |
| Wall of flames sweeps into a hillside neighborhood | 1 / 0 | 2 / 11 | 3 / 6 | 4 / 5 | 4 / 8 | 1 / 19 | 20 / 0 | 3 / 4 | 4 / 5 | 3 / 5 | 4 |
| Flames race up a tower facade | 1 / 0 | 4 / 4 | 3 / 7 | 4 / 5 | 4 / 4 | 1 / 19 | 16 / 0 | 3 / 8 | 5 / 6 | 3 / 3 | 2 |
| Fire tornado tears across a burning roadside | 3 / 7 | 5 / 5 | 3 / 6 | 4 / 4 | 2 / 8 | 3 / 7 | 20 / 0 | 3 / 9 | 5 / 3 | 3 / 7 | 3 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 1 / 0 | 2 / 10 | 3 / 8 | 4 / 3 | 4 / 3 | 1 / 19 | 20 / 0 | 3 / 2 | 5 / 3 | 3 / 7 | 4 |
| Pyroclastic cloud races down into a village street | 4 / 5 | 3 / 0 | 3 / 6 | 1 / 0 | 4 / 8 | 1 / 19 | 17 / 0 | 4 / 8 | 3 / 7 | 1 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 5 | 3 / 0 | 4 / 4 | 4 / 5 | 4 / 6 | 1 / 19 | 20 / 0 | 4 / 6 | 3 / 8 | 1 / 0 | 0 |
| Avalanche slams into a mountain village | 10 / 0 | 2 / 14 | 5 / 2 | 1 / 0 | 3 / 3 | 1 / 19 | 13 / 0 | 3 / 6 | 3 / 5 | 1 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 13 / 0 | 3 / 8 | 5 / 3 | 1 / 0 | 4 / 6 | 1 / 19 | 18 / 0 | 3 / 5 | 3 / 5 | 1 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 11 / 2 | 2 / 13 | 4 / 3 | 1 / 0 | 3 / 7 | 1 / 19 | 17 / 0 | 3 / 7 | 3 / 5 | 1 / 0 | 0 |
| Earthquake collapses an apartment block | 6 / 5 | 2 / 13 | 4 / 4 | 1 / 0 | 4 / 4 | 1 / 19 | 14 / 0 | 3 / 9 | 3 / 8 | 1 / 0 | 1 |
| Earthquake collapses a row of old stone houses | 6 / 2 | 2 / 14 | 4 / 4 | 1 / 0 | 4 / 3 | 1 / 19 | 12 / 0 | 3 / 10 | 3 / 8 | 1 / 0 | 0 |

## Sıralama

**Önce en kötü 5 (normal) ve sonraki durumları:**
- Firefighting helicopter drops water on the flames racing toward a hillside neighborhood: tam kopya 4 → 0
- Wall of flames sweeps into a hillside neighborhood: tam kopya 4 → 0
- Tornado crosses a marina quay: tam kopya 3 → 0
- Mud and debris torrent tears through a hillside village: tam kopya 3 → 0
- Tornado making landfall: tam kopya 3 → 0

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

