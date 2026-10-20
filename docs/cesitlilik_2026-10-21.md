# Çeşitlilik ölçümü — 21 Ekim 2026

Üretim: `scripts/variety_report.py --runs 20 --seed 2026`. Her olayda 20 ardışık üretim, gerçek seçim mantığı (LRU dahil), boş geçmişle başlar, her üretimin combo_key'i ve hikâyesi sonrakinin geçmişine eklenir. Hikâye kod yedeğinden (GPT yok). Kie, Notion yok.

Hücre biçimi: `benzersiz değer sayısı / arka arkaya aynı değer sayısı` (en fazla 19). "—" olan eksen (ortamı ya da aracı olmayan olay) tekrar sayılmaz. **Tam kopya**: spot + ortam + ışık + kilit cümle bir öncekiyle birebir aynı.

## Normal (süreç hafızası korunur)

| Olay | ortam (benzersiz / art arda) | spot/kamera (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 3 / 8 | 3 / 7 | 7 / 2 | 1 / 0 | 1 / 19 | 20 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 7 | 4 / 6 | 8 / 4 | 4 / 9 | 1 / 19 | 20 / 0 | 0 |
| Mudslide pours down a hillside street | 1 / 0 | 3 / 5 | 3 / 4 | 3 / 5 | 4 / 4 | 1 / 19 | 20 / 0 | 0 |
| Rain-soaked slope collapses onto a roadside | 1 / 0 | 2 / 8 | 3 / 4 | 3 / 5 | 4 / 5 | 1 / 19 | 19 / 0 | 2 |
| Mud and debris torrent tears through a hillside village | 1 / 0 | 3 / 8 | 3 / 6 | 3 / 4 | 4 / 6 | 1 / 19 | 20 / 0 | 3 |
| Tornado making landfall | 1 / 0 | 3 / 6 | 3 / 6 | 4 / 3 | 4 / 3 | 1 / 19 | 16 / 0 | 3 |
| Tornado crosses a marina quay | 1 / 0 | 1 / 19 | 4 / 3 | 4 / 7 | 4 / 6 | 1 / 19 | 20 / 0 | 3 |
| Tornado sweeps down a coastal avenue | 1 / 0 | 3 / 4 | 4 / 4 | 4 / 4 | 4 / 4 | 1 / 19 | 20 / 0 | 1 |
| Wall of flames sweeps into a hillside neighborhood | 1 / 0 | 2 / 11 | 3 / 6 | 4 / 5 | 4 / 8 | 1 / 19 | 20 / 0 | 4 |
| Flames race up a tower facade | 1 / 0 | 4 / 4 | 3 / 7 | 4 / 5 | 4 / 4 | 1 / 19 | 16 / 0 | 2 |
| Fire tornado tears across a burning roadside | 3 / 0 | 6 / 0 | 3 / 4 | 4 / 3 | 2 / 13 | 3 / 0 | 20 / 0 | 0 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 1 / 0 | 2 / 10 | 3 / 8 | 4 / 3 | 4 / 3 | 1 / 19 | 20 / 0 | 4 |
| Pyroclastic cloud races down into a village street | 4 / 0 | 3 / 0 | 3 / 6 | 1 / 0 | 4 / 12 | 1 / 19 | 16 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 0 | 3 / 0 | 4 / 4 | 4 / 7 | 4 / 7 | 1 / 19 | 20 / 0 | 0 |
| Avalanche slams into a mountain village | 11 / 0 | 2 / 0 | 5 / 0 | 1 / 0 | 4 / 6 | 1 / 19 | 15 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 11 / 0 | 3 / 0 | 5 / 0 | 1 / 0 | 4 / 6 | 1 / 19 | 20 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 12 / 0 | 2 / 0 | 5 / 0 | 1 / 0 | 4 / 5 | 1 / 19 | 18 / 0 | 0 |
| Earthquake collapses an apartment block | 3 / 0 | 2 / 0 | 4 / 0 | 1 / 0 | 4 / 3 | 1 / 19 | 15 / 0 | 0 |
| Earthquake collapses a row of old stone houses | 6 / 0 | 2 / 0 | 4 / 0 | 1 / 0 | 4 / 3 | 1 / 19 | 14 / 0 | 0 |

## Her üretimden önce deploy (süreç hafızası silinir, sadece Notion combo_key kalır)

| Olay | ortam (benzersiz / art arda) | spot/kamera (benzersiz / art arda) | ışık (benzersiz / art arda) | araç (benzersiz / art arda) | kişi (benzersiz / art arda) | kilit cümle (benzersiz / art arda) | beat çifti (benzersiz / art arda) | tam kopya |
|---|---|---|---|---|---|---|---|---|
| Flash flooding in city streets | 6 / 0 | 3 / 8 | 3 / 7 | 7 / 2 | 1 / 0 | 1 / 19 | 20 / 0 | 0 |
| Tidal wave surges over a coastal city street | 6 / 0 | 3 / 7 | 4 / 6 | 8 / 4 | 4 / 9 | 1 / 19 | 20 / 0 | 0 |
| Mudslide pours down a hillside street | 1 / 0 | 3 / 5 | 3 / 4 | 3 / 5 | 4 / 4 | 1 / 19 | 20 / 0 | 0 |
| Rain-soaked slope collapses onto a roadside | 1 / 0 | 2 / 8 | 3 / 4 | 3 / 5 | 4 / 5 | 1 / 19 | 19 / 0 | 2 |
| Mud and debris torrent tears through a hillside village | 1 / 0 | 3 / 8 | 3 / 6 | 3 / 4 | 4 / 6 | 1 / 19 | 20 / 0 | 3 |
| Tornado making landfall | 1 / 0 | 3 / 6 | 3 / 6 | 4 / 3 | 4 / 3 | 1 / 19 | 16 / 0 | 3 |
| Tornado crosses a marina quay | 1 / 0 | 1 / 19 | 4 / 3 | 4 / 7 | 4 / 6 | 1 / 19 | 20 / 0 | 3 |
| Tornado sweeps down a coastal avenue | 1 / 0 | 3 / 4 | 4 / 4 | 4 / 4 | 4 / 4 | 1 / 19 | 20 / 0 | 1 |
| Wall of flames sweeps into a hillside neighborhood | 1 / 0 | 2 / 11 | 3 / 6 | 4 / 5 | 4 / 8 | 1 / 19 | 20 / 0 | 4 |
| Flames race up a tower facade | 1 / 0 | 4 / 4 | 3 / 7 | 4 / 5 | 4 / 4 | 1 / 19 | 16 / 0 | 2 |
| Fire tornado tears across a burning roadside | 3 / 7 | 5 / 5 | 3 / 6 | 4 / 4 | 2 / 8 | 3 / 7 | 20 / 0 | 3 |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | 1 / 0 | 2 / 10 | 3 / 8 | 4 / 3 | 4 / 3 | 1 / 19 | 20 / 0 | 4 |
| Pyroclastic cloud races down into a village street | 4 / 3 | 3 / 0 | 3 / 6 | 1 / 0 | 4 / 12 | 1 / 19 | 16 / 0 | 0 |
| Volcanic bombs slam into a village street | 4 / 4 | 3 / 0 | 4 / 4 | 4 / 7 | 4 / 7 | 1 / 19 | 20 / 0 | 0 |
| Avalanche slams into a mountain village | 10 / 0 | 2 / 14 | 5 / 2 | 1 / 0 | 3 / 3 | 1 / 19 | 13 / 0 | 0 |
| Avalanche crashes down onto a ski lodge | 13 / 0 | 3 / 8 | 5 / 3 | 1 / 0 | 4 / 6 | 1 / 19 | 18 / 0 | 0 |
| Avalanche rips through a pine forest into a valley | 11 / 2 | 2 / 13 | 4 / 3 | 1 / 0 | 3 / 7 | 1 / 19 | 17 / 0 | 0 |
| Earthquake collapses an apartment block | 6 / 5 | 2 / 13 | 4 / 4 | 1 / 0 | 4 / 4 | 1 / 19 | 14 / 0 | 1 |
| Earthquake collapses a row of old stone houses | 6 / 2 | 2 / 14 | 4 / 4 | 1 / 0 | 4 / 3 | 1 / 19 | 12 / 0 | 0 |

## Sıralama (normal senaryo)

**En kötü 5:**
- Firefighting helicopter drops water on the flames racing toward a hillside neighborhood: tam kopya 4, art arda tekrar (ortam+spot+ışık+kilit) 37
- Wall of flames sweeps into a hillside neighborhood: tam kopya 4, art arda tekrar (ortam+spot+ışık+kilit) 36
- Tornado crosses a marina quay: tam kopya 3, art arda tekrar (ortam+spot+ışık+kilit) 41
- Mud and debris torrent tears through a hillside village: tam kopya 3, art arda tekrar (ortam+spot+ışık+kilit) 33
- Tornado making landfall: tam kopya 3, art arda tekrar (ortam+spot+ışık+kilit) 31

**En iyi 3:**
- Fire tornado tears across a burning roadside: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 4
- Avalanche slams into a mountain village: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 19
- Avalanche crashes down onto a ski lodge: tam kopya 0, art arda tekrar (ortam+spot+ışık+kilit) 19

