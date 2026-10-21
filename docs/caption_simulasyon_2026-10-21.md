# Caption simülasyonu — 21 Ekim 2026 (Aşama 7 + 7.1)

Sahte GPT adayları + şablon yedeği; geçmiş = Paylaşımlar (49 satır) + simülasyonda üretilenler. Olay başına 10 ardışık caption.

- Reddedilen GPT başlık adayı: 158/570 (%28)
- Şablona düşen başlık: 23/190 (%12); zorunlu şablon (hiçbiri geçmedi): 0
- Ret nedenleri (GPT başlık adayı): dinamik yasak 94, Jaccard 46, biçim 18
- Sahte GPT aday stilleri (6 stilin hepsi): T1 91, T2 116, T3 99, T4 90, T5 87, T6 87

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

stil: T1 2, T3 2, T4 2, T5 1, T6 3
· CTA: İstatistik 3, Soru 3, Sonuna kadar izle 2, Emoji seçimi 1, CTA yok 1

```
Flash Flood Buries a City Street 🌊

The white sedan is swept into another parked car and both are shoved along. Then a car is lifted off the road and spins away downstream.

Four people, 15 seconds, one take.

#disaster #severeweather #flashflood #flooding #weatherwatch
```
stil: T6 · CTA: İstatistik · kaynak: GPT

```
Two Streets of Flash Flood

The SUV is carried backwards down the street, bumping parked cars. Then the flood bursts through the ground floor of a building across the street.

Comment 🌊 or 🏃

#extremeweather #naturepower #flood #rainstorm #weatherwatch
```
stil: T3 · CTA: Emoji seçimi · kaynak: GPT

## Tidal wave surges over a coastal city street

stil: T1 2, T2 1, T3 2, T4 1, T5 1, T6 3
· CTA: CTA yok 2, Sonuna kadar izle 2, Soru 2, Emoji seçimi 2, İstatistik 2

```
How Close Is Too Close to the Tidal Wave?

The tidal wave reaches the seafront and a city bus is shoved sideways by the surge.

#disaster #oceanpower #tidalwave #giantwave #waves
```
stil: T4 · CTA: CTA yok · kaynak: GPT

```
Tidal Wave Buries the Seafront 🌊

The tidal wave reaches the seafront and a dumpster tumbles down the street and smashes into a parked car.

Keep your eyes on the parked cars until the end.

#naturepower #oceanpower #tidalwave #bigwave #seastorm
```
stil: T6 · CTA: Sonuna kadar izle · kaynak: GPT

## Mudslide pours down a hillside street

stil: T1 2, T3 3, T4 2, T5 1, T6 2
· CTA: İstatistik 3, CTA yok 2, Soru 2, Sonuna kadar izle 2, Emoji seçimi 1

```
Filmed From a Rooftop as the Mudslide Hit

The mudslide reaches a steep hillside street and the mud rams a house corner and tears off its wooden porch.

Fifteen seconds, one take.

#naturaldisaster #naturepower #mudslide #debrisflow #heavyrain
```
stil: T5 · CTA: İstatistik · kaynak: GPT

```
Would Anyone Survive the Mudslide?

The delivery van and the car behind it are pushed down the street together, bumper to bumper. Then mud slams into a house across the street and bursts through its ground floor.

#naturaldisaster #disaster #landslide #heavyrain #monsoon
```
stil: T4 · CTA: CTA yok · kaynak: GPT

## Rain-soaked slope collapses onto a roadside

stil: T1 2, T2 1, T3 2, T4 3, T5 1, T6 1
· CTA: İstatistik 2, Emoji seçimi 2, CTA yok 2, Soru 2, Sonuna kadar izle 2

```
Would Anyone Survive the Slope Collapse?

The slope collapse reaches a mountain road and a utility pole snaps and falls across the road.

Fifteen seconds, one take.

#naturaldisaster #naturepower #debrisflow #monsoon #mountainroad
```
stil: T4 · CTA: İstatistik · kaynak: GPT

```
Filmed From a Hillside as the Slope Collapse Hit

The SUV tips over onto its side in the mud. Then a tree is torn out of the slope and slides across the road.

Comment ⛰️ or 🏃

#naturaldisaster #naturepower #mudslide #rockfall #heavyrain
```
stil: T5 · CTA: Emoji seçimi · kaynak: GPT

## Mud and debris torrent tears through a hillside village

stil: T1 2, T2 1, T3 1, T4 2, T5 1, T6 3
· CTA: Sonuna kadar izle 3, CTA yok 2, Soru 2, Emoji seçimi 2, İstatistik 1

```
Debris Torrent Breaks Over a Hillside Village 🌧️

The debris torrent reaches a hillside village and a pile of logs breaks loose and rolls down the lane.

Stay until the very end.

#extremeweather #naturepower #landslide #heavyrain #monsoon
```
stil: T6 · CTA: Sonuna kadar izle · kaynak: GPT

```
Would Anyone Survive the Debris Torrent?

The debris torrent reaches a hillside village and a large tree is uprooted and rolls down with the torrent.

#naturaldisaster #disaster #landslide #mudslide #monsoon
```
stil: T4 · CTA: CTA yok · kaynak: GPT

## Tornado sweeps down a coastal avenue

stil: T1 2, T3 2, T4 2, T5 2, T6 2
· CTA: CTA yok 3, İstatistik 3, Sonuna kadar izle 2, Emoji seçimi 2

```
Would Anyone Survive the Tornado?

The tornado flings a large truck across the avenue into the front of a building. Then the tornado rips the awnings off a row of shops and flings them high.

#extremeweather #severeweather #twister #supercell #storm
```
stil: T4 · CTA: CTA yok · kaynak: GPT

```
Tornado Breaks Over a Coastal Avenue 🌪️

One calm scene, then the tornado: the tornado flings a large truck across the avenue into the front of a building.

Fifteen seconds, one take.

#naturepower #disaster #tornado #supercell #tornadowarning
```
stil: T6 · CTA: İstatistik · kaynak: GPT

## Tornado crosses a marina quay

stil: T1 1, T3 1, T4 3, T5 3, T6 2
· CTA: Sonuna kadar izle 3, İstatistik 2, CTA yok 2, Emoji seçimi 2, Soru 1

```
Filmed From the Third Floor as the Waterspout Hit

The pickup truck tips over onto its side on the quay road. Then a wall of dust and debris rolls across the quay and engulfs the café terrace.

Fifteen seconds, one take.

#extremeweather #naturepower #tornado #supercell #storm
```
stil: T5 · CTA: İstatistik · kaynak: GPT

```
Could You Outrun the Waterspout?

One calm scene, then the waterspout: the delivery van slides along the quay and slams into a lamppost.

Keep your eyes on the quayside cafés until the end.

#extremeweather #severeweather #twister #waterspout #storm
```
stil: T4 · CTA: Sonuna kadar izle · kaynak: GPT

## Tornado making landfall

stil: T1 1, T3 1, T4 3, T5 2, T6 3
· CTA: Sonuna kadar izle 3, CTA yok 2, Soru 2, Emoji seçimi 2, İstatistik 1

```
Waterspout Buries the Waterfront 🌪️

The pickup truck slides along the street and slams into a parked car. Then the tornado rips a billboard frame from its supports and throws it aside.

#extremeweather #severeweather #twister #supercell #waterspout
```
stil: T6 · CTA: CTA yok · kaynak: GPT

```
It Did Not Slow Down 🌪️

One calm scene, then the waterspout: the SUV is lifted off the road and flung down the street.

Stay until the very end.

#severeweather #disaster #tornado #stormchasing #waterspout
```
stil: T1 · CTA: Sonuna kadar izle · kaynak: GPT

## Wall of flames sweeps into a hillside neighborhood

stil: T1 3, T2 1, T3 2, T4 1, T5 1, T6 2
· CTA: CTA yok 3, Sonuna kadar izle 2, Emoji seçimi 2, Soru 2, İstatistik 1

```
Keep Your Eyes on the Roof 🔥

The wall of flames reaches a hillside neighborhood and the fire races across a garden, engulfing a parked trailer and a woodpile.

Stay until the very end.

#naturaldisaster #extremeweather #wildfire #firestorm #smoke
```
stil: T1 · CTA: Sonuna kadar izle · kaynak: GPT

```
Would Anyone Survive the Wall of Flames?

One calm scene, then the wall of flames: the pickup truck reverses hard down the road as a burning tree crashes across the lane in front of it.

#extremeweather #disaster #forestfire #bushfire #firestorm
```
stil: T4 · CTA: CTA yok · kaynak: GPT

## Flames race up a tower facade

stil: T1 4, T3 1, T4 2, T5 1, T6 2
· CTA: CTA yok 2, Emoji seçimi 2, İstatistik 2, Soru 2, Sonuna kadar izle 2

```
Look at the Left Side 🔥

The facade fire reaches an apartment tower and a wall of smoke and fire pours out of the upper floors and rolls up the tower.

#extremeweather #firesafety #firestorm #buildingfire #apartmentfire
```
stil: T1 · CTA: CTA yok · kaynak: GPT

```
How Close Is Too Close to the Facade Fire?

One calm scene, then the facade fire: flaming debris smashes the windshield of the white sedan as it brakes hard.

Comment 🔥 or 🏃

#naturaldisaster #disaster #firestorm #smoke #buildingfire
```
stil: T4 · CTA: Emoji seçimi · kaynak: GPT

## Fire tornado tears across a burning roadside

stil: T1 3, T3 2, T4 3, T5 1, T6 1
· CTA: CTA yok 2, İstatistik 2, Sonuna kadar izle 2, Soru 2, Emoji seçimi 2

```
Could You Outrun the Fire Tornado?

The fire tornado reaches a burning roadside and the fire tornado rips the burning roof off a house across the street into its funnel.

#disaster #firesafety #wildfire #firetornado #bushfire
```
stil: T4 · CTA: CTA yok · kaynak: GPT

```
Two Streets of Fire Tornado

One calm scene, then the fire tornado: the towering fire tornado lifts the delivery van off the road and flings it into a burning tree.

Three people, 15 seconds, one take.

#extremeweather #firesafety #firetornado #firestorm #firefighters
```
stil: T3 · CTA: İstatistik · kaynak: GPT

## Firefighting helicopter drops water on the flames racing toward a hillside neighborhood

stil: T1 2, T2 1, T3 2, T4 2, T5 1, T6 2
· CTA: Emoji seçimi 3, Sonuna kadar izle 3, İstatistik 2, CTA yok 2

```
Four Cars of Water Drop

The pickup truck speeds down the street as the helicopter's downdraft whips smoke and embers across the road. Then the flames fight back, a fresh burst of fire swallowing trees beside the water line.

Fifteen seconds, one take.

#naturaldisaster #firesafety #firestorm #aerialfirefighting #smoke
```
stil: T3 · CTA: İstatistik · kaynak: GPT

```
Filmed From a Rooftop as the Water Drop Hit

One calm scene, then the water drop: the white sedan brakes hard as a drenching cascade of water spills across the road in front of it.

Comment 🚁 or 🏃

#extremeweather #disaster #bushfire #firefighters #aerialfirefighting
```
stil: T5 · CTA: Emoji seçimi · kaynak: GPT

## Pyroclastic cloud races down into a village street

stil: T1 2, T3 3, T4 2, T5 1, T6 2
· CTA: Sonuna kadar izle 3, İstatistik 3, Emoji seçimi 2, Soru 1, CTA yok 1

```
Could You Outrun the Ash Cloud?

The cloud front flattens a row of palm trees and hurls their fronds ahead of it. Then the cloud blasts the front off a shop building and the brickwork falls into the street.

Stay until the very end.

#disaster #earthscience #volcano #eruption #ashcloud
```
stil: T4 · CTA: Sonuna kadar izle · kaynak: GPT

```
Ash Cloud Hammers a Village Street 🌋

The cloud snaps a row of street trees and power poles and they crash across the street. Then the cloud hits a hillside retaining wall and the wall gives way, boulders tumbling into the street.

Fifteen seconds, one take.

#naturepower #naturaldisaster #volcano #volcaniceruption #ashcloud
```
stil: T6 · CTA: İstatistik · kaynak: GPT

## Volcanic bombs slam into a village street

stil: T1 2, T2 1, T3 1, T4 3, T5 1, T6 2
· CTA: Sonuna kadar izle 3, İstatistik 3, Emoji seçimi 2, Soru 2

```
How Close Is Too Close to the Volcanic Bombs?

One calm scene, then the volcanic bombs: a huge glowing rock crashes through the roof of a house across the street.

Stay until the very end.

#naturaldisaster #disaster #volcano #lavabombs #volcanic
```
stil: T4 · CTA: Sonuna kadar izle · kaynak: GPT

```
Volcanic Bombs Rolls Into a Village Street 🌋

The volcanic bombs reaches a village street and a volcanic bomb lands in the middle of the street and the road blasts apart in a crater of sparks and rock.

Fifteen seconds, one take.

#naturepower #disaster #volcano #volcaniceruption #ashcloud
```
stil: T6 · CTA: İstatistik · kaynak: GPT

## Avalanche slams into a mountain village

stil: T1 2, T3 2, T4 3, T5 1, T6 2
· CTA: İstatistik 2, Sonuna kadar izle 2, Soru 2, Emoji seçimi 2, CTA yok 2

```
Look at the Left Side 🏔️

One calm scene, then the avalanche: the snow cloud smashes the balcony off a chalet facade.

Fifteen seconds, one take.

#naturaldisaster #disaster #avalanche #winterstorm #backcountry
```
stil: T1 · CTA: İstatistik · kaynak: GPT

```
Would Anyone Survive the Avalanche?

The snow cloud smashes the balcony off a chalet facade. Then the snow wall carries a wooden shed off its base and breaks it apart.

Keep your eyes on the stone chalets until the end.

#naturepower #naturaldisaster #snowstorm #winterstorm #mountains
```
stil: T4 · CTA: Sonuna kadar izle · kaynak: GPT

## Avalanche crashes down onto a ski lodge

stil: T1 2, T3 3, T4 1, T5 2, T6 2
· CTA: CTA yok 3, Sonuna kadar izle 2, İstatistik 2, Emoji seçimi 2, Soru 1

```
Three Floors of Avalanche

One calm scene, then the avalanche: the avalanche shoves a stack of dark timber logs down the slope into the lodge wall.

Stay until the very end.

#naturepower #naturaldisaster #winterstorm #backcountry #powdersnow
```
stil: T3 · CTA: Sonuna kadar izle · kaynak: GPT

```
Filmed From an Upper Window as the Avalanche Hit

The avalanche reaches a ski lodge and the snow wall tears a wooden annex off the lodge and carries it downhill.

Fifteen seconds, one take.

#naturaldisaster #disaster #snowstorm #powdersnow #skiresort
```
stil: T5 · CTA: İstatistik · kaynak: GPT

## Avalanche rips through a pine forest into a valley

stil: T1 3, T2 1, T3 1, T4 1, T5 1, T6 3
· CTA: Sonuna kadar izle 3, İstatistik 2, Emoji seçimi 2, Soru 2, CTA yok 1

```
It Did Not Slow Down 🌲

One calm scene, then the avalanche: the avalanche smashes through the front of a stone farmhouse and its roof caves in.

Fifteen seconds, one take.

#naturepower #disaster #snowstorm #mountains #powdersnow
```
stil: T1 · CTA: İstatistik · kaynak: GPT

```
How Close Is Too Close to the Avalanche?

One calm scene, then the avalanche: the avalanche slams a wall of snapped dark pine trunks into a wooden cabin and its side bursts open.

Comment 🌲 or 🏃

#naturepower #naturaldisaster #avalanche #snowstorm #backcountry
```
stil: T4 · CTA: Emoji seçimi · kaynak: GPT

## Earthquake collapses an apartment block

stil: T1 2, T3 2, T4 2, T5 1, T6 3
· CTA: CTA yok 3, Emoji seçimi 3, Soru 2, İstatistik 1, Sonuna kadar izle 1

```
Building Collapse Buries an Apartment Block 🏢

One calm scene, then the building collapse: the whole front wall of the block peels off and crashes onto the street.

#extremeevents #catastrophe #collapse #urbandisaster #dustcloud
```
stil: T6 · CTA: CTA yok · kaynak: GPT

```
Could You Outrun the Building Collapse?

A huge concrete slab from the collapsing block slams into the road and breaks it apart. Then a second apartment block across the street tilts and falls into the dust.

Comment 🏢 or 🏃

#disaster #survival #buildingcollapse #collapse #dustcloud
```
stil: T4 · CTA: Emoji seçimi · kaynak: GPT

## Earthquake collapses a row of old stone houses

stil: T1 2, T2 1, T3 2, T4 2, T5 2, T6 1
· CTA: Emoji seçimi 3, CTA yok 2, İstatistik 2, Sonuna kadar izle 2, Soru 1

```
Caught From an Upper Window on an Old Street

The building collapse reaches a row of old houses and the rubble heap of a fallen house slides out into the street.

#disaster #survival #buildingcollapse #structuralfailure #urbandisaster
```
stil: T5 · CTA: CTA yok · kaynak: GPT + şablon

```
Could You Outrun the Building Collapse?

One calm scene, then the building collapse: the facade of the nearest old stone house slides off in one piece and crashes down.

Comment 🧱 if you would stay or 🏃 if you would run.

#catastrophe #survival #collapse #urbandisaster #dustcloud
```
stil: T4 · CTA: Emoji seçimi · kaynak: GPT

