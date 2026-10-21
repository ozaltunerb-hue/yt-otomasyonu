# Caption simülasyonu — 21 Ekim 2026 (Aşama 7 + 7.1 + 7.2)

Sahte GPT adayları + şablon yedeği; geçmiş = Paylaşımlar (49 satır) + simülasyonda üretilenler. Olay başına 10 ardışık caption.

- Reddedilen GPT başlık adayı: 149/570 (%26)
- Şablona düşen başlık: 19/190 (%10); zorunlu şablon (hiçbiri geçmedi): 0
- Ret nedenleri (GPT başlık adayı): dinamik yasak 86, Jaccard 35, biçim 28
- Sahte GPT aday stilleri (6 stilin hepsi): T1 82, T2 99, T3 104, T4 96, T5 107, T6 82

## Aşama 7.2: önce / sonra (tohum 11, 19 olay × 10)

"Önce" = 7.1 kodu (967bbaa), "sonra" = 7.2. Sahte GPT bu turda yeni talimata uyar (sayı sadece 15 saniye ya da kişi
sayısı, sakinlik açılışı yok); aynı sahte GPT iki koda da verildi.

| GPT adaylı | önce | sonra |
|---|---|---|
| Reddedilen GPT başlık adayı | %24 (138/570) | %26 (149/570) |
| Şablona düşen başlık | %9 (17/190) | %10 (19/190) |
| Zorunlu şablon | 0 | 0 |
| Ret: dinamik yasak / Jaccard / biçim | 71 / 48 / 19 | 86 / 35 / 28 |
| Ret: ilk 3 kelime / kalıcı yasak | 0 / 0 | 0 / 0 |
| Art arda kelime tekrarı olan caption | 43 | 0 |
| Aynı CTA metni son 10'da | 35 | 0 |
| "one take" son 10'da 2+ | 24 | 0 |

| Sadece şablon | önce | sonra |
|---|---|---|
| Zorunlu şablon | 0 | 0 |
| Art arda kelime tekrarı olan caption | 96 | 0 |
| Aynı CTA metni son 10'da | 15 | 0 |
| "one take" son 10'da 2+ | 33 | 0 |

Eski sahte GPT ile (7.1 raporundaki "Three Floors of Avalanche", "One calm scene" üreten): 190 caption'ın 32'sinde
uydurma sayılı başlık, 52'sinde sakinlik ifadesi vardı; 7.2'de ikisi de reddedilir (test). 10 farklı tohumda
(1900 şablon caption) zorunlu şablon 0, aynı olayda Jaccard > 0.45 ya da ilk 3 kelimesi aynı açıklama çifti 0.

Değişenler: T3 sadece videodaki sayı (15 saniye, kaçan kişi sayısı, beat'te geçen "sayı + isim"; kat sayısı sadece
deprem / cephe ve beat'te kat varsa; GPT adayı da denetlenir); kalıcı yasak +calm, quiet, peaceful, ordinary, one calm
scene, it started as (kelime sınırıyla: "extraordinary" yakalanmaz); art arda iki parçada aynı içerik kelimesi yok,
ikinci geçişte zamir / eş anlamlı (it, one, they, the blaze; street -> lane, house -> home…; "street tree" gibi sıfat
kullanımı değişmez); başlıkta bir içerik kelimesi iki kez yok; CTA her tipte 7-9 metin, son 10 caption'da aynı metin
yok; "one take" son 10 caption'da en fazla 1.

## Aşama 7.1: önce / sonra (aynı sahte GPT, aynı tohum 11)

Sahte GPT bu turda üretimin beat cümlelerini bilir (gerçek GPT hikâyeyi yazdığı için bilir); beat'ler üretimdeki gibi
ÇİFT olarak döner (Eksenler "beats" = "Y2+Z7", çift tekrar etmez). "Önce" = 7.1 öncesi kod (f231944), "sonra" = 7.1.

| GPT adaylı simülasyon (19 olay × 10) | önce | sonra |
|---|---|---|
| Reddedilen GPT başlık adayı | %28 (159/570) | %28 (158/570) |
| Şablona düşen başlık | %13 (24/190) | %12 (23/190) |
| Zorunlu şablon | 0 | 0 |
| Ret: dinamik yasak | 77 | 94 |
| Ret: Jaccard | 54 | 46 |
| Ret: biçim (9 kelime, emoji) | 28 | 18 |
| Ret: ilk 3 kelime / kalıcı yasak | 0 / 0 | 0 / 0 |

| Sadece şablon (GPT adayı yok, 19 olay × 10) | önce | sonra |
|---|---|---|
| Genel kalıp içeren caption ("with every second", "The last frame:", "Nobody expected", "this part") | 32 | 0 |
| Zorunlu şablon (hiçbir şablon geçmedi) | 152 | 0 |
| Aynı olayda açıklama çifti Jaccard > 0.45 | 684 | 0 |
| Aynı olayda ilk 3 kelimesi aynı açıklama çifti | 684 | 0 |

10 farklı tohumda (1900 şablon caption) sonra: 1 zorunlu açıklama, 1 zorunlu başlık (ikisi de deprem).

Değişenler: şablon açıklaması o üretimin iki beat cümlesinin ilk cümleciğinden + tehdit + yer; başlık şablonları her
stilde 4 (T4 gerçek soru); yeni kalıcı yasaklar: "nobody expected", "this part", "this moment", "with every second",
"the last frame"; benzerlikte olayın kendi adındaki kelimeler ve eş anlamlılar (water, drop, load, rock, glowing,
facade) sayılmaz (kelime kalmazsa sayılır, birebir tekrar her zaman ret); cephe yangınına #buildingfire #apartmentfire.

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

stil: T1 1, T3 2, T4 3, T5 1, T6 3
· CTA: İstatistik 3, CTA yok 3, Sonuna kadar izle 2, Emoji seçimi 1, Soru 1

```
Flash Flood Buries a City Street 🌊

The flash flood arrives and the white sedan is swept into another parked car and both are shoved along.

15 seconds, no slow motion.

#extremeweather #naturepower #flashflood #rainstorm #weatherwatch
```
stil: T6 · CTA: İstatistik · kaynak: GPT

```
Could You Outrun the Flash Flood?

The flash flood reaches a city street and the flood bursts through the ground floor of a building across the street.

Comment 🏠 or 🚗: what would you save first?

#naturepower #severeweather #flashflood #floodwater #flooding
```
stil: T4 · CTA: Emoji seçimi · kaynak: GPT

## Tidal wave surges over a coastal city street

stil: T1 3, T2 1, T3 1, T4 1, T5 1, T6 3
· CTA: CTA yok 3, Emoji seçimi 2, Soru 2, İstatistik 2, Sonuna kadar izle 1

```
Five People, One Tidal Wave

The tidal wave reaches the seafront and a row of parked vehicles is ripped loose one by one and washed away.

#extremeweather #disaster #giantwave #roguewave #waves
```
stil: T3 · CTA: CTA yok · kaynak: GPT

```
Tidal Wave Batters the Seafront 🌊

The tidal wave arrives and the SUV is lifted and flung against a storefront.

Comment 🌊 if you would stay or 🏃 if you would run.

#naturepower #disaster #coastalflood #seastorm #waves
```
stil: T6 · CTA: Emoji seçimi · kaynak: GPT

## Mudslide pours down a hillside street

stil: T1 2, T3 2, T4 2, T5 1, T6 3
· CTA: Sonuna kadar izle 3, İstatistik 2, Emoji seçimi 2, CTA yok 2, Soru 1

```
How Long Would You Last Near the Mudslide?

The mudslide reaches a steep hillside street and a mass of mud and uprooted trees crashes onto the houses across the street.

Five people on screen, 15 seconds of mudslide.

#extremeweather #naturepower #landslide #debrisflow #heavyrain
```
stil: T4 · CTA: İstatistik · kaynak: GPT

```
Mudslide Hammers a Steep Hillside Street ⛰️

The pickup truck tips over onto its side in the mud. Then a low garden wall collapses and its stones tumble down the street.

🏃 or 📱: run or keep filming?

#naturaldisaster #disaster #landslide #heavyrain #monsoon
```
stil: T6 · CTA: Emoji seçimi · kaynak: GPT

## Rain-soaked slope collapses onto a roadside

stil: T1 3, T3 2, T4 2, T5 1, T6 2
· CTA: Emoji seçimi 3, Sonuna kadar izle 3, Soru 2, CTA yok 1, İstatistik 1

```
It Did Not Slow Down ⛰️

The slope collapse reaches a mountain road and more of the slope gives way and a second surge of mud and rocks pours onto the road.

Comment ⛰️ or 🏃

#naturepower #disaster #landslide #debrisflow #monsoon
```
stil: T1 · CTA: Emoji seçimi · kaynak: GPT

```
Five People, One Slope Collapse

The pickup truck is pushed against the guardrail and pinned there. Then a utility pole snaps and falls across the road.

Stay until the very end.

#naturaldisaster #naturepower #landslide #mudslide #heavyrain
```
stil: T3 · CTA: Sonuna kadar izle · kaynak: GPT

## Mud and debris torrent tears through a hillside village

stil: T1 2, T3 2, T4 2, T5 1, T6 3
· CTA: CTA yok 3, Soru 3, İstatistik 2, Sonuna kadar izle 1, Emoji seçimi 1

```
Debris Torrent Rolls Into a Hillside Village 🌧️

The white sedan is shoved into a parked motorbike and both are carried along. Then a pile of logs breaks loose and rolls down the lane.

#naturepower #disaster #landslide #debrisflow #heavyrain
```
stil: T6 · CTA: CTA yok · kaynak: GPT

```
Keep Your Eyes on the Roof 🌧️

The debris torrent arrives and the pickup truck tips over onto its side in the torrent.

Stay until the very end.

#naturaldisaster #disaster #landslide #mudslide #monsoon
```
stil: T1 · CTA: Sonuna kadar izle · kaynak: GPT

## Tornado sweeps down a coastal avenue

stil: T1 1, T3 3, T4 1, T5 2, T6 3
· CTA: Soru 3, Emoji seçimi 2, İstatistik 2, Sonuna kadar izle 2, CTA yok 1

```
Tornado Overruns a Coastal Avenue 🌪️

The tornado arrives and the pickup truck is swept up into the air, spins, and crashes down across the avenue.

Comment 🌪️ or 🏃

#severeweather #naturepower #tornado #twister #stormchasing
```
stil: T6 · CTA: Emoji seçimi · kaynak: GPT

```
Five People, One Tornado

The tornado arrives and the white sedan is shoved sideways across the avenue by the wind.

#extremeweather #disaster #supercell #stormchasing #storm
```
stil: T3 · CTA: CTA yok · kaynak: GPT

## Tornado crosses a marina quay

stil: T1 2, T3 3, T4 3, T6 2
· CTA: Sonuna kadar izle 3, CTA yok 3, Soru 2, İstatistik 1, Emoji seçimi 1

```
How Long Would You Last Near the Waterspout?

The waterspout reaches a marina and the tornado tears the awning off the harbor café and flings it across the quay.

15 seconds, one take, no cuts.

#extremeweather #severeweather #tornado #stormchasing #storm
```
stil: T4 · CTA: İstatistik · kaynak: GPT

```
Three People, One Waterspout

The waterspout reaches a marina and the tornado lifts the whole café terrace off the quay and scatters it across the road.

Stay until the very end.

#extremeweather #disaster #supercell #tornadowarning #waterspout
```
stil: T3 · CTA: Sonuna kadar izle · kaynak: GPT

## Tornado making landfall

stil: T1 1, T3 2, T4 2, T5 2, T6 3
· CTA: Sonuna kadar izle 3, CTA yok 3, İstatistik 2, Soru 1, Emoji seçimi 1

```
Waterspout Batters the Waterfront 🌪️

The waterspout reaches the waterfront and the tornado shreds the top floor of a building across the street, debris spiraling up.

Look at the background, not the waterspout.

#naturepower #disaster #tornado #twister #supercell
```
stil: T6 · CTA: Sonuna kadar izle · kaynak: GPT

```
Filmed From a Street Camera as the Waterspout Hit

The SUV is shoved sideways across the street by the wind. Then the tornado uproots a large tree and flings it through the air.

#extremeweather #disaster #twister #waterspout #storm
```
stil: T5 · CTA: CTA yok · kaynak: GPT

## Wall of flames sweeps into a hillside neighborhood

stil: T1 3, T2 1, T3 2, T4 1, T6 3
· CTA: Sonuna kadar izle 4, İstatistik 2, Emoji seçimi 2, CTA yok 1, Soru 1

```
Four People, One Wall of Flames

The wall of flames arrives and the SUV U-turns in a cloud of smoke and speeds away as the flames close the road behind it.

Stay until the very end.

#extremeweather #firesafety #bushfire #firefighters #smoke
```
stil: T3 · CTA: Sonuna kadar izle · kaynak: GPT

```
This Is How Fast It Moves 🔥

The wall of flames reaches a hillside neighborhood and a house roof catches fire and its tiles burst apart in the heat.

Fifteen seconds, one take.

#naturaldisaster #disaster #firestorm #firefighters #smoke
```
stil: T1 · CTA: İstatistik · kaynak: GPT

## Flames race up a tower facade

stil: T1 2, T3 2, T4 2, T5 1, T6 3
· CTA: Sonuna kadar izle 3, Soru 3, İstatistik 2, CTA yok 1, Emoji seçimi 1

```
Three People, One Facade Fire

Flaming debris smashes the windshield of the pickup truck as it brakes hard. Then a row of windows explodes outward, spraying glass and flames over the street.

#extremeweather #disaster #firestorm #smoke #buildingfire
```
stil: T3 · CTA: CTA yok · kaynak: GPT

```
Keep Your Eyes on the Roof 🔥

The flames leap up the facade to the balconies above in a roaring wall. Then a row of windows explodes outward, spraying glass and flames over the street.

Stay until the very end.

#naturaldisaster #firesafety #smoke #buildingfire #apartmentfire
```
stil: T1 · CTA: Sonuna kadar izle · kaynak: GPT

## Fire tornado tears across a burning roadside

stil: T1 2, T3 2, T4 1, T5 2, T6 3
· CTA: İstatistik 3, Soru 3, Sonuna kadar izle 2, CTA yok 1, Emoji seçimi 1

```
Five People, One Fire Tornado

The fire tornado reaches a burning roadside and the front wall of a house across the street tears away, rubble sucked into the funnel.

Fifteen seconds, one take.

#extremeweather #disaster #firetornado #firefighters #smoke
```
stil: T3 · CTA: İstatistik · kaynak: GPT

```
Fire Tornado Hammers a Burning Roadside 🔥

The fire tornado reaches a burning roadside and the towering fire tornado sweeps over a parked trailer and tosses it aside in fire and smoke.

#extremeweather #firesafety #wildfire #forestfire #bushfire
```
stil: T6 · CTA: CTA yok · kaynak: GPT

## Firefighting helicopter drops water on the flames racing toward a hillside neighborhood

stil: T1 1, T2 1, T3 1, T4 3, T5 2, T6 2
· CTA: Emoji seçimi 3, Sonuna kadar izle 3, CTA yok 2, İstatistik 1, Soru 1

```
Look at the Left Side 🚁

The water drop arrives and the helicopter roars low over the street, its downdraft bending the burning trees and scattering embers.

Comment 🚁 or 🏃

#naturaldisaster #extremeweather #bushfire #firefighters #aerialfirefighting
```
stil: T1 · CTA: Emoji seçimi · kaynak: GPT

```
Water Drop Breaks Over a Burning Hillside 🚁

The water drop arrives and a wall of water falls on a burning house, the flames collapsing into thick white steam.

#naturaldisaster #firesafety #forestfire #aerialfirefighting #smoke
```
stil: T6 · CTA: CTA yok · kaynak: GPT

## Pyroclastic cloud races down into a village street

stil: T1 3, T3 2, T4 2, T5 1, T6 2
· CTA: Sonuna kadar izle 4, Emoji seçimi 3, CTA yok 2, Soru 1

```
This Is How Fast It Moves 🌋

The ash cloud reaches a village street and the cloud engulfs a whole block and the upper-floor windows burst outward in a shower of glass.

Stay with it to the end.

#naturaldisaster #earthscience #volcano #volcaniceruption #pyroclasticflow
```
stil: T1 · CTA: Sonuna kadar izle · kaynak: GPT

```
Filmed From a Rooftop as the Ash Cloud Hit

The ash cloud arrives and the cloud front flattens a row of palm trees and hurls their fronds ahead of it.

One emoji for this ash cloud: go.

#naturepower #naturaldisaster #volcano #eruption #volcanic
```
stil: T5 · CTA: Emoji seçimi · kaynak: GPT

## Volcanic bombs slam into a village street

stil: T1 2, T2 1, T3 2, T4 3, T5 1, T6 1
· CTA: Emoji seçimi 3, İstatistik 3, Sonuna kadar izle 2, CTA yok 2

```
It Did Not Slow Down 🌋

A glowing rock slams into a shop sign, which crashes onto the sidewalk. Then a glowing rock bounces along the road and slams into a parked car.

Comment 🌋 or 🏃

#naturepower #naturaldisaster #volcano #ashcloud #lavabombs
```
stil: T1 · CTA: Emoji seçimi · kaynak: GPT

```
Could You Outrun the Volcanic Bombs?

A glowing rock smashes onto the street, bursts apart and sets a parked car on fire. Then a huge glowing rock hits a house and its upper floor erupts in flames.

15 seconds, filmed in a single shot.

#naturaldisaster #earthscience #eruption #lavabombs #volcanic
```
stil: T4 · CTA: İstatistik · kaynak: GPT

## Avalanche slams into a mountain village

stil: T1 2, T3 3, T4 1, T5 1, T6 3
· CTA: Emoji seçimi 3, İstatistik 3, Soru 2, Sonuna kadar izle 1, CTA yok 1

```
Avalanche Floods Into a Mountain Village 🏔️

The snow wall flattens a long wooden fence and a wooden shed beside the street, the dark boards flying. Then the snow wall crashes into a hillside retaining wall and the stones tumble out.

Stay until the very end.

#naturepower #extremeweather #mountains #backcountry #powdersnow
```
stil: T6 · CTA: Sonuna kadar izle · kaynak: GPT

```
How Long Would You Last Near the Avalanche?

The avalanche reaches a mountain village and the snow blast smashes into a stone chalet and its gable wall collapses.

Comment 🏔️ or 🏃

#naturaldisaster #extremeweather #avalanche #winterstorm #backcountry
```
stil: T4 · CTA: Emoji seçimi · kaynak: GPT

## Avalanche crashes down onto a ski lodge

stil: T1 2, T3 1, T4 3, T5 3, T6 1
· CTA: CTA yok 2, Emoji seçimi 2, Sonuna kadar izle 2, İstatistik 2, Soru 2

```
Would Anyone Survive the Avalanche?

The avalanche arrives and the avalanche rips the wooden terrace deck off the lodge and the dark planks fly.

#naturepower #disaster #snowstorm #backcountry #skiresort
```
stil: T4 · CTA: CTA yok · kaynak: GPT

```
Filmed From the Third Floor as the Avalanche Hit

The avalanche arrives and the avalanche smashes a wooden snack cabin by the slope and its dark boards scatter.

Comment ⛷️ if you would stay or 🏃 if you would run.

#naturepower #naturaldisaster #avalanche #snowstorm #powdersnow
```
stil: T5 · CTA: Emoji seçimi · kaynak: GPT

## Avalanche rips through a pine forest into a valley

stil: T1 2, T3 2, T4 3, T5 2, T6 1
· CTA: İstatistik 4, Sonuna kadar izle 3, CTA yok 2, Emoji seçimi 1

```
It Did Not Slow Down 🌲

The avalanche arrives and the avalanche front hurls snapped pine trunks into a row of wooden cabins.

Fifteen seconds, one take.

#extremeweather #disaster #avalanche #mountains #powdersnow
```
stil: T1 · CTA: İstatistik · kaynak: GPT

```
Filmed From the Third Floor as the Avalanche Hit

The avalanche arrives and the avalanche smashes through the front of a stone farmhouse and its roof caves in.

Comment 🌲 if you would stay or 🏃 if you would run.

#naturaldisaster #extremeweather #winterstorm #backcountry #powdersnow
```
stil: T5 · CTA: Emoji seçimi · kaynak: GPT

## Earthquake collapses an apartment block

stil: T1 3, T2 1, T3 2, T4 2, T5 1, T6 1
· CTA: Sonuna kadar izle 3, İstatistik 2, CTA yok 2, Soru 2, Emoji seçimi 1

```
Keep Your Eyes on the Roof 🏢

The building collapse reaches an apartment block and the top floors of the apartment block across the street collapse straight down.

Fifteen seconds, one take.

#catastrophe #survival #collapse #structuralfailure #dustcloud
```
stil: T1 · CTA: İstatistik · kaynak: GPT

```
How Long Would You Last Near the Building Collapse?

The whole front wall of the block peels off and crashes onto the street. Then the building next door crumbles floor by floor into the same dust cloud.

#disaster #survival #buildingcollapse #structuralfailure #urbandisaster
```
stil: T4 · CTA: CTA yok · kaynak: GPT

## Earthquake collapses a row of old stone houses

stil: T1 2, T2 1, T3 1, T4 2, T5 2, T6 2
· CTA: Sonuna kadar izle 4, CTA yok 2, Emoji seçimi 2, Soru 1, İstatistik 1

```
Look at the Left Side 🧱

The building collapse reaches a row of old houses and the roof of a stone house falls in and its walls collapse into the street.

Stay until the very end.

#catastrophe #survival #collapse #structuralfailure #urbandisaster
```
stil: T1 · CTA: Sonuna kadar izle · kaynak: GPT

```
Building Collapse Batters a Row of Old Houses 🧱

The building collapse arrives and a corner stone house crumbles and its rubble spreads across the junction.

#disaster #survival #buildingcollapse #collapse #dustcloud
```
stil: T6 · CTA: CTA yok · kaynak: GPT

