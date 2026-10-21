# Caption simülasyonu — 21 Ekim 2026 (Aşama 7)

Sahte GPT adayları + şablon yedeği; geçmiş = Paylaşımlar (49 satır) + simülasyonda üretilenler. Olay başına 10 ardışık caption.

- Reddedilen GPT başlık adayı: 146/570 (%26)
- Şablona düşen başlık: 16/190 (%8); zorunlu şablon (hiçbiri geçmedi): 0
- Ret nedenleri (GPT başlık adayı): dinamik yasak 84, Jaccard 37, biçim 25
- Sahte GPT aday stilleri (6 stilin hepsi): T1 96, T2 111, T3 92, T4 87, T5 98, T6 86


## Benzerlik iyileştirmesi: önce / sonra (aynı simülasyon, aynı tohum)

Önce: eski kelime hesabı (olay adları ve sayılar sayılıyordu; ilk 3 kelime ham kelimelerle). Sonra: stopword'ler, olay/
kategori adları ve eş anlamlıları, sayılar ve emojiler Jaccard'dan, ilk 3 kelime kuralından ve dinamik yasaktan çıktı.
Eşikler (0.5 / 0.45) ve kalıcı yasak listesi aynı. Sahte GPT iki ölçümde aynı (son 2 stilden kaçınır, en fazla 9 kelime,
6 stilin hepsinden aday).

| | önce | sonra |
|---|---|---|
| Reddedilen GPT başlık adayı | %42 (242/570) | %26 (146/570) |
| Şablona düşen başlık | %23 (43/190) | %8 (16/190) |
| Zorunlu şablon | 9 | 0 |
| Ret: dinamik yasak | 149 | 84 |
| Ret: Jaccard | 57 | 37 |
| Ret: biçim (9 kelime, emoji) | 36 | 25 |
| Ret: ilk 3 kelime / kalıcı yasak | 0 / 0 | 0 / 0 |

## Flash flooding in city streets

stil: T1 3, T3 1, T4 2, T5 2, T6 2
· CTA: İstatistik 3, CTA yok 2, Sonuna kadar izle 2, Emoji seçimi 2, Soru 1

```
Flash Flood Pours Across a City Street 🌊

It speeds up with every second. The last frame: cars dragged down the street.

#naturepower #disaster #flood #flooding #weatherwatch
```
stil: T6 · CTA: CTA yok · kaynak: GPT

```
Nobody Expected This Part 🌊

One calm scene, then the flash flood: cars dragged down the street, all in a single take.

Stay until the last frame.

#extremeweather #disaster #rainstorm #stormdamage #weatherwatch
```
stil: T1 · CTA: Sonuna kadar izle · kaynak: GPT

## Tidal wave surges over a coastal city street

stil: T1 3, T3 2, T4 1, T5 1, T6 3
· CTA: CTA yok 3, Soru 2, Sonuna kadar izle 2, Emoji seçimi 2, İstatistik 1

```
Tidal Wave Floods Into a Seafront Street 🌊

It starts at the edge of a seafront street. A few moments later the result is cars and benches pushed inland.

#extremeweather #naturepower #giantwave #roguewave #seastorm
```
stil: T6 · CTA: CTA yok · kaynak: GPT

```
Look at the Left Side 🌊

One calm scene, then the tidal wave: cars and benches pushed inland, all in a single take.

Fifteen seconds, one take.

#naturepower #oceanpower #giantwave #bigwave #waves
```
stil: T1 · CTA: İstatistik · kaynak: GPT

## Mudslide pours down a hillside street

stil: T1 1, T2 1, T3 2, T4 2, T5 2, T6 2
· CTA: Emoji seçimi 3, Sonuna kadar izle 2, Soru 2, İstatistik 2, CTA yok 1

```
Filmed From a Hillside as the Mudslide Hit

One calm scene, then the mudslide: the whole street under mud, all in a single take.

Stay until the last frame.

#naturaldisaster #extremeweather #mudslide #heavyrain #monsoon
```
stil: T5 · CTA: Sonuna kadar izle · kaynak: GPT

```
Mudslide Crashes Onto a Steep Hillside Street ⛰️

It starts at the edge of a steep hillside street. A few moments later the result is the whole street under mud.

Comment ⛰️ or 🏃

#naturaldisaster #disaster #landslide #debrisflow #heavyrain
```
stil: T6 · CTA: Emoji seçimi · kaynak: GPT

## Rain-soaked slope collapses onto a roadside

stil: T1 2, T2 1, T3 2, T4 2, T5 1, T6 2
· CTA: CTA yok 3, Soru 3, İstatistik 2, Sonuna kadar izle 1, Emoji seçimi 1

```
Two Streets of Slope Collapse

It starts at the edge of a mountain road. A few moments later the result is both lanes buried.

#extremeweather #disaster #debrisflow #heavyrain #mountainroad
```
stil: T3 · CTA: CTA yok · kaynak: GPT

```
This Is How Fast It Moves ⛰️

It speeds up with every second. The last frame: both lanes buried.

Four people, 15 seconds, one slope collapse.

#naturepower #disaster #mudslide #rockfall #heavyrain
```
stil: T1 · CTA: İstatistik · kaynak: GPT

## Mud and debris torrent tears through a hillside village

stil: T1 2, T2 1, T3 2, T4 2, T5 1, T6 2
· CTA: CTA yok 3, Sonuna kadar izle 3, Emoji seçimi 2, Soru 1, İstatistik 1

```
Filmed From a Rooftop as the Debris Torrent Hit

It starts at the edge of a hillside village. A few moments later the result is the village lanes torn apart.

#naturaldisaster #extremeweather #landslide #heavyrain #monsoon
```
stil: T5 · CTA: CTA yok · kaynak: GPT

```
Four Cars of Debris Torrent

It grows with every second. The last frame: the village lanes torn apart.

Stay until the last frame.

#naturepower #disaster #mudslide #heavyrain #monsoon
```
stil: T3 · CTA: Sonuna kadar izle · kaynak: GPT

## Tornado sweeps down a coastal avenue

stil: T1 3, T3 1, T4 1, T5 3, T6 2
· CTA: CTA yok 3, Sonuna kadar izle 2, Soru 2, Emoji seçimi 2, İstatistik 1

```
Six Houses of Tornado

One calm scene, then the tornado: cars and shop fronts flung across the road, all in a single take.

#extremeweather #naturepower #tornado #tornadowarning #storm
```
stil: T3 · CTA: CTA yok · kaynak: GPT

```
This Is How Fast It Moves 🌪️

It starts at the edge of a coastal avenue. A few moments later the result is cars and shop fronts flung across the road.

Stay until the last frame.

#naturepower #disaster #twister #stormchasing #storm
```
stil: T1 · CTA: Sonuna kadar izle · kaynak: GPT

## Tornado crosses a marina quay

stil: T1 1, T3 2, T4 2, T5 2, T6 3
· CTA: İstatistik 3, CTA yok 3, Emoji seçimi 2, Sonuna kadar izle 2

```
Waterspout Floods Into a Marina 🌪️

It builds with every second. The last frame: boats tossed against the quay.

Fifteen seconds, one take.

#extremeweather #naturepower #twister #stormchasing #tornadowarning
```
stil: T6 · CTA: İstatistik · kaynak: GPT

```
Two Streets of Waterspout

One calm scene, then the waterspout: boats tossed against the quay, all in a single take.

#severeweather #disaster #supercell #stormchasing #storm
```
stil: T3 · CTA: CTA yok · kaynak: GPT

## Tornado making landfall

stil: T1 1, T2 1, T3 2, T4 2, T5 2, T6 2
· CTA: CTA yok 3, Sonuna kadar izle 2, İstatistik 2, Emoji seçimi 2, Soru 1

```
Two Streets of Waterspout

It starts at the edge of the waterfront. A few moments later the result is debris thrown across the seafront.

#naturepower #disaster #twister #tornadowarning #storm
```
stil: T3 · CTA: CTA yok · kaynak: GPT

```
How Close Is Too Close to the Waterspout?

One calm scene, then the waterspout: debris thrown across the seafront, all in a single take.

Watch until the last second.

#extremeweather #disaster #tornado #stormchasing #waterspout
```
stil: T4 · CTA: Sonuna kadar izle · kaynak: GPT

## Wall of flames sweeps into a hillside neighborhood

stil: T1 2, T2 1, T3 3, T4 1, T6 3
· CTA: Sonuna kadar izle 2, Emoji seçimi 2, İstatistik 2, Soru 2, CTA yok 2

```
This Is How Fast It Moves 🔥

It builds with every second. The last frame: flames jumping from roof to roof.

Stay until the last frame.

#extremeweather #disaster #wildfire #bushfire #firestorm
```
stil: T1 · CTA: Sonuna kadar izle · kaynak: GPT

```
Wall of Flames Rips Through a Hillside Neighborhood 🔥

One calm scene, then the wall of flames: flames jumping from roof to roof, all in a single take.

Comment 🔥 if you would watch or 🏃 if you would leave.

#naturaldisaster #extremeweather #forestfire #firestorm #smoke
```
stil: T6 · CTA: Emoji seçimi · kaynak: GPT

## Flames race up a tower facade

stil: T1 2, T2 1, T3 3, T4 2, T5 1, T6 1
· CTA: Soru 3, CTA yok 2, Emoji seçimi 2, İstatistik 2, Sonuna kadar izle 1

```
Facade Fire Overruns an Apartment Tower 🔥

One calm scene, then the facade fire: fire climbing from floor to floor, all in a single take.

#naturaldisaster #extremeweather #firestorm #firefighters #smoke
```
stil: T6 · CTA: CTA yok · kaynak: GPT

```
Two Streets of Facade Fire

It builds with every second. The last frame: fire climbing from floor to floor.

Comment 🔥 or 🏃

#disaster #firesafety #firestorm #firefighters #smoke
```
stil: T3 · CTA: Emoji seçimi · kaynak: GPT

## Fire tornado tears across a burning roadside

stil: T1 2, T3 2, T4 4, T5 1, T6 1
· CTA: İstatistik 3, CTA yok 2, Emoji seçimi 2, Sonuna kadar izle 2, Soru 1

```
How Close Is Too Close to the Fire Tornado?

It builds with every second. The last frame: burning debris pulled into the funnel.

#extremeweather #disaster #bushfire #firestorm #smoke
```
stil: T4 · CTA: CTA yok · kaynak: GPT

```
It Did Not Slow Down 🔥

One calm scene, then the fire tornado: burning debris pulled into the funnel, all in a single take.

Fifteen seconds, one take.

#naturaldisaster #disaster #wildfire #firetornado #smoke
```
stil: T1 · CTA: İstatistik · kaynak: GPT

## Firefighting helicopter drops water on the flames racing toward a hillside neighborhood

stil: T1 2, T3 3, T4 3, T5 1, T6 1
· CTA: Soru 3, CTA yok 2, Sonuna kadar izle 2, Emoji seçimi 2, İstatistik 1

```
Would Anyone Survive the Water Drop?

One calm scene, then the water drop: a helicopter fighting the flames above the rooftops, all in a single take.

Fifteen seconds, one take.

#disaster #firesafety #wildfire #firefighters #aerialfirefighting
```
stil: T4 · CTA: İstatistik · kaynak: GPT

```
Six Houses of Water Drop

It speeds up with every second. The last frame: a helicopter fighting the flames above the rooftops.

#extremeweather #firesafety #firestorm #firefighters #smoke
```
stil: T3 · CTA: CTA yok · kaynak: GPT

## Pyroclastic cloud races down into a village street

stil: T1 3, T3 2, T4 2, T5 1, T6 2
· CTA: Sonuna kadar izle 3, Emoji seçimi 2, Soru 2, CTA yok 2, İstatistik 1

```
Six Houses of Ash Cloud

It grows with every second. The last frame: the whole street turned grey.

Comment 🌋 or 🏃

#disaster #earthscience #eruption #volcaniceruption #ashcloud
```
stil: T3 · CTA: Emoji seçimi · kaynak: GPT

```
Would Anyone Survive the Ash Cloud?

One calm scene, then the ash cloud: the whole street turned grey, all in a single take.

Stay until the last frame.

#naturepower #naturaldisaster #volcano #volcaniceruption #ashcloud
```
stil: T4 · CTA: Sonuna kadar izle · kaynak: GPT

## Volcanic bombs slam into a village street

stil: T1 1, T3 2, T4 3, T5 2, T6 2
· CTA: CTA yok 3, Emoji seçimi 3, Soru 2, Sonuna kadar izle 1, İstatistik 1

```
How Close Is Too Close to the Volcanic Bombs?

One calm scene, then the volcanic bombs: roofs punched through and cars on fire, all in a single take.

#naturepower #naturaldisaster #volcano #eruption #ashcloud
```
stil: T4 · CTA: CTA yok · kaynak: GPT

```
Three Floors of Volcanic Bombs

It starts at the edge of a village street. A few moments later the result is roofs punched through and cars on fire.

Comment 🌋 or 🏃

#disaster #earthscience #volcaniceruption #ashcloud #volcanic
```
stil: T3 · CTA: Emoji seçimi · kaynak: GPT

## Avalanche slams into a mountain village

stil: T1 1, T3 2, T4 2, T5 3, T6 2
· CTA: CTA yok 3, Emoji seçimi 3, Sonuna kadar izle 2, İstatistik 2

```
Filmed From a Rooftop as the Avalanche Hit

It starts at the edge of a mountain village. A few moments later the result is the first houses buried.

#extremeweather #disaster #snowstorm #mountains #powdersnow
```
stil: T5 · CTA: CTA yok · kaynak: GPT

```
Avalanche Buries a Mountain Village 🏔️

One calm scene, then the avalanche: the first houses buried, all in a single take.

Comment 🏔️ or 🏃

#naturaldisaster #disaster #avalanche #backcountry #powdersnow
```
stil: T6 · CTA: Emoji seçimi · kaynak: GPT

## Avalanche crashes down onto a ski lodge

stil: T1 3, T3 1, T4 1, T5 3, T6 2
· CTA: CTA yok 3, Sonuna kadar izle 2, Emoji seçimi 2, İstatistik 2, Soru 1

```
Filmed From an Upper Window as the Avalanche Hit

It grows with every second. The last frame: the resort buildings hit.

Stay until the last frame.

#naturepower #naturaldisaster #snowstorm #winterstorm #skiresort
```
stil: T5 · CTA: Sonuna kadar izle · kaynak: GPT

```
Avalanche Hammers a Ski Resort ⛷️

It starts at the edge of a ski resort. A few moments later the result is the resort buildings hit.

#naturepower #disaster #avalanche #winterstorm #mountains
```
stil: T6 · CTA: CTA yok · kaynak: GPT

## Avalanche rips through a pine forest into a valley

stil: T1 1, T3 1, T4 3, T5 2, T6 3
· CTA: CTA yok 3, Soru 3, Sonuna kadar izle 2, İstatistik 1, Emoji seçimi 1

```
Could You Outrun the Avalanche?

One calm scene, then the avalanche: snapped trees and broken cabins, all in a single take.

Fifteen seconds, one take.

#naturepower #naturaldisaster #avalanche #winterstorm #backcountry
```
stil: T4 · CTA: İstatistik · kaynak: GPT

```
Avalanche Rips Through a Forest Valley 🌲

It starts at the edge of a forest valley. A few moments later the result is snapped trees and broken cabins.

#naturaldisaster #disaster #avalanche #snowstorm #powdersnow
```
stil: T6 · CTA: CTA yok · kaynak: GPT

## Earthquake collapses an apartment block

stil: T1 2, T3 3, T4 2, T5 1, T6 2
· CTA: Sonuna kadar izle 3, CTA yok 3, İstatistik 2, Emoji seçimi 1, Soru 1

```
Two Streets of Building Collapse

It builds with every second. The last frame: the block down floor by floor.

Stay until the last frame.

#disaster #extremeevents #structuralfailure #urbandisaster #dustcloud
```
stil: T3 · CTA: Sonuna kadar izle · kaynak: GPT

```
Would Anyone Survive the Building Collapse?

It starts at the edge of an apartment block. A few moments later the result is the block down floor by floor.

#extremeevents #survival #buildingcollapse #collapse #urbandisaster
```
stil: T4 · CTA: CTA yok · kaynak: GPT

## Earthquake collapses a row of old stone houses

stil: T1 3, T3 1, T4 2, T5 3, T6 1
· CTA: CTA yok 3, Emoji seçimi 2, Soru 2, Sonuna kadar izle 2, İstatistik 1

```
Nobody Expected This Part 🧱

One calm scene, then the building collapse: the houses down one after another, all in a single take.

#catastrophe #survival #buildingcollapse #collapse #urbandisaster
```
stil: T1 · CTA: CTA yok · kaynak: GPT

```
Building Collapse Rolls Into a Row of Old Houses 🧱

It grows with every second. The last frame: the houses down one after another.

Comment 🧱 or 🏃

#disaster #extremeevents #buildingcollapse #collapse #structuralfailure
```
stil: T6 · CTA: Emoji seçimi · kaynak: GPT

