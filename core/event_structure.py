"""
Yapılandırılmış olay hattı (3 Eki 2026, Bahadır): olayın kurgusu kodda, GPT sadece cümle yazar.

Hikâye üç zaman diliminden oluşur ("0-4s: ... 4-9s: ... 9-15s: ..."). Etiketleri ve 0-4s'nin kilit görselini kod
yazar; 4-9s ve 9-15s'de ne olacağını kod havuzdan seçer (Notion geçmişi + süreç hafızası, LRU, son üretimlerde
geçen olay tekrar gelmez). GPT strict JSON şemasıyla üç alanı döndürür: slice_1_rest (kilit görselin devamı),
slice_2, slice_3. Kie'ye gönderimden hemen önce final_prompt_issues son prompt'u spec'ten yeniden kurup birebir
karşılaştırır; tek madde tutmazsa istek gitmez (kapalı başarısızlık, sessiz yedek yok).

Kaynak: 3 Eki sel testleri. Zaman damgalı prompt'la Seedance 15 sn'nin tamamını aksiyonla doldurdu; serbest
GPT ise su duvarını zayıf yazdı, son saniyeleri genel cümleyle ("more cars") bitirdi. Yeni olay eklemek sadece
veri eklemektir (EVENT_KEY_VISUAL + EVENT_BEATS); import anı denetimi eksik veriyi yakalar.
"""
from __future__ import annotations

import random
import re
import threading

import config
from core.skeleton_pipeline import (EVENT_SKELETONS, REGION_VIEW_EVENTS, REGION_VIEWS, VOLC_ENV_WEIGHTS, VOLC_ENVS,
                                    VOLC_SPOT_KIND, VOLC_SPOT_WEIGHTS, VOLCANO_WEATHER_WEIGHTS, count_range,
                                    style_suffix, view_spots)
from core.trace_format import count_constraints

FLOOD = "Flash flooding in city streets"
TIDAL = "Tidal wave surges over a coastal city street"
MUDSLIDE = "Mudslide pours down a hillside street"
SLOPE = "Rain-soaked slope collapses onto a roadside"
VILLAGE = "Mud and debris torrent tears through a hillside village"
LANDFALL = "Tornado making landfall"
MARINA_TORNADO = "Tornado crosses a marina quay"
AVENUE = "Tornado sweeps down a coastal avenue"
# 🔥 Yangın (TASLAK, 8 Eki, Bahadır)
WILDFIRE = "Wall of flames sweeps into a hillside neighborhood"
FACADE_FIRE = "Flames race up a tower facade"
FIRE_TORNADO = "Fire tornado tears across a burning roadside"
# 10 Eki, Bahadır (havuzlar onaylı): yangın söndürme helikopteri
HELICOPTER = "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood"
FIRE_EVENTS = (WILDFIRE, FACADE_FIRE, FIRE_TORNADO, HELICOPTER)
# 🌋 Volkan (TASLAK, 10 Eki, Bahadır)
ERUPTION = "Volcano erupts and a shockwave blows out windows"
PYROCLASTIC = "Pyroclastic cloud races down into a village street"
VOLCANIC_BOMBS = "Volcanic bombs slam into a village street"
# 13 Eki (4), Bahadır: lav nehri çıkarıldı (4 testte de kabul edilmedi; arşiv: EVENT_BEATS üstündeki ARŞİV notu)
VOLCANO_EVENTS = (ERUPTION, PYROCLASTIC, VOLCANIC_BOMBS)
# ❄️ Çığ (TASLAK, 13 Eki, Bahadır). Bahadır'ın kısa adları: koy, kayak, orman
AVALANCHE_VILLAGE = "Avalanche slams into a mountain village"
AVALANCHE_SKI = "Avalanche crashes down onto a ski lodge"
AVALANCHE_FOREST = "Avalanche rips through a pine forest into a valley"
AVALANCHE_EVENTS = (AVALANCHE_VILLAGE, AVALANCHE_SKI, AVALANCHE_FOREST)
# 🏚️ Deprem (TASLAK, 14 Eki, Bahadır). Bahadır'ın anahtarları: apartment, old stone
EARTHQUAKE_APARTMENT = "Earthquake collapses an apartment block"
EARTHQUAKE_OLD_STREET = "Earthquake collapses a row of old stone houses"
EARTHQUAKE_EVENTS = (EARTHQUAKE_APARTMENT, EARTHQUAKE_OLD_STREET)
# ☄️ Meteor (TASLAK, 29 Eki, Bahadır): denize dev meteor düşer. Kadraj (kamera noktası), ortam ve ışık her üretimde
# değişir (son 2 tekrar etmez); araç yok
METEOR = "Meteor slams into the sea off the coast"
METEOR_EVENTS = (METEOR,)

SLICE_LABELS = ("0-4s", "4-9s", "9-15s")
SLICE_FIELDS = ("slice_1_rest", "slice_2", "slice_3")
# Kelime aralıkları (etiketsiz). Toplam = kilit görsel + üç alan. 4 Eki, Bahadır: kuru provada 7 denemenin 3'ü
# sınır aşımıyla kaldı; 6-14/10-20/40-60'tan genişletildi. Genel 40-60 kuralı (creative_pipeline "length")
# yapılandırılmış olaylarda yerini bu toplama bırakır; diğer olaylarda aynen geçerli.
SLICE_WORDS = {"slice_1_rest": (6, 18), "slice_2": (10, 24), "slice_3": (10, 24)}
TOTAL_WORDS = (40, 70)
# Olaya özel toplam kelime aralığı (genel TOTAL_WORDS yerine). 4 Eki, Bahadır: hortum marina 40-75
TOTAL_WORDS_BY_EVENT = {"Tornado crosses a marina quay": (40, 75),
                        # 10 Eki, Bahadır: orman yangını 40-75 (kilit cümle 22 kelime; diğer yangınlar 40-70)
                        "Wall of flames sweeps into a hillside neighborhood": (40, 75),
                        # 10 Eki, Bahadır: helikopter 40-75 (kilit cümle 24 kelime)
                        "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood": (40, 75),
                        # 15 Eki, Bahadır: ateş hortumu 40-75 (GPT insan cümlesini uzun yazıyor; diğer yangınlar aynı)
                        "Fire tornado tears across a burning roadside": (40, 75),
                        # 10 Eki, Bahadır: volkanın 4 olayı 40-75
                        "Volcano erupts and a shockwave blows out windows": (40, 75),
                        "Pyroclastic cloud races down into a village street": (40, 75),
                        "Volcanic bombs slam into a village street": (40, 75),
                        # 13 Eki, Bahadır: çığ 40-75 (volkan gibi). 14 Eki (5), Bahadır kararı: 40-70 (yamaçlı
                        # kamera şablonuyla stil eki en fazla 101 kelime; 70 + 3 etiket + 101 = 174 ≤ 175)
                        "Avalanche slams into a mountain village": (40, 70), "Avalanche crashes down onto a ski lodge": (40, 70), "Avalanche rips through a pine forest into a valley": (40, 70),
                        # 14 Eki, Bahadır: deprem 40-70 (çığ gibi)
                        "Earthquake collapses an apartment block": (40, 70), "Earthquake collapses a row of old stone houses": (40, 70),
                        # 29 Eki, Bahadır: meteor 40-75 (diğer yapılandırılmış olaylarla aynı; kilit cümle 33 kelime)
                        "Meteor slams into the sea off the coast": (40, 75)}
# Kie seedance-2-fast prompt sınırı 20000 karakter (docs.kie.ai/market/bytedance/seedance-2-fast, 4 Eki doğrulandı).
# Bizim sınırımız onun çok altında: en uzun stil eki 742 + 60 kelimelik hikâye (kelime başına 8 karakterle ~480)
# ≈ 1224; 1200 bu hikâyeyi haksız reddederdi. Tam kapsam testinde ölçülen en uzun prompt 1062. 70 kelimelik
# toplamla (4 Eki): ölçülen ortalama kelime uzunluğu 5,58 harf -> ~1221; 1400'e ulaşmak için ortalama 8,6 harf
# gerekir. Aşım dilim kalite kapısında GPT'ye "kısalt" geri bildirimi olur; son denetimde kapalı başarısızlık.
SEEDANCE_PROMPT_LIMIT = 20000
MAX_PROMPT_CHARS = 1400
RECENT_BEAT_BLOCK = 3          # son N üretimde geçen 4-9s / 9-15s olayı tekrar seçilmez
# Olaya özel engelleme derinliği (10 Eki, volkan): havuzu küçük (dilim başına 3-4 madde) olaylarda 3 derinlik, kamera
# dışlamalarıyla birlikte adayı bitirir. Değerler her kamera noktasında en kötü durumda en az bir çift kalacak şekilde
# seçildi (TestVolcano.test_no_candidates_never); 0 = engelleme yok, sadece LRU. Diğer olaylar RECENT_BEAT_BLOCK.
# 13 Eki (4), Bahadır: volkan havuzları 5-6 maddeye çıktı; patlama ve bombalar standart 3 (önceki geçici değerler
# patlama 1, lav 1, bombalar 1, piroklastik 0). Kül bulutu 2 (Bahadır kararı): çatı maddeleri (P3, P6, Q3, Q6) çatı
# terası ve balkonda seçilmediği için orada 4 × 4 madde ve 8 yasak çift kalıyor, 3 derinlik en kötü durumda adayı
# bitirir.
RECENT_BEAT_BLOCK_BY_EVENT = {PYROCLASTIC: 2,
                              # 13 Eki, çığ: köy standart 3; kayak 2 (istasyon terasında teleferik ve çatı maddeleri
                              # yok, 4 × 4 madde, 3 derinlik en kötü durumda adayı bitirir); orman 2 (balkonda çatı
                              # maddesi yok, 10 yasak çift, aynı sebep). Bahadır talimatı: aday kalmazsa 2.
                              # 14 Eki (3), zayıf madde temizliği: yasak çiftler arttı (köy 10, kayak 11, orman 18).
                              # Köy 2 (balkonda 4 × 4 madde, 3 derinlikte aday biter); kayak 2 (istasyon terası);
                              # orman 1 (balkonda E1/E2'nin tek eşi F4, 2 derinlikte aday biter). Testli.
                              AVALANCHE_VILLAGE: 2, AVALANCHE_SKI: 2, AVALANCHE_FOREST: 1,
                              # 14 Eki, Bahadır: deprem havuzları 4 + 4, son 2 üretimin maddeleri elenir. Apartmanda
                              # balkon noktası (*) maddeleri elediği için 3 × 3 kalır; 2 derinlikte kalan tek çift yasak
                              # çifte denk gelebilir: o durumda 1'e düşer (BEAT_BLOCK_FALLBACK_EVENTS, testli)
                              EARTHQUAKE_APARTMENT: 2, EARTHQUAKE_OLD_STREET: 2,
                              # 29 Eki: meteor havuzu puanlamadan sonra 2 + 2 madde, kod yedeğine sığan 3 çift. 1
                              # derinlikte bile (M6+N3 sonrası) aday kalmıyor: engelleme yok, en uzun süredir
                              # kullanılmayan çift (LRU) seçilir; 3 çift sırayla döner
                              METEOR: 0}
# Aday kalmazsa derinliği 1'e düşen olaylar (14 Eki, deprem). Diğer olaylarda davranış aynı (aday bitince hata).
# 17 Eki (temizlik turu): hortum karaya vuruş (4 + 4 kaldı), orman yangını (balkonda 3 + 3) ve çığ köy (6 yeni hariç
# çift, balkonda 7 çift) de: en kötü durumda olaya özel derinlik adayı bitirir, 1 derinlikte en az 3 çift kalır.
# 18 Eki: ateş hortumu listeden çıktı (kısa metinlerle 45 izinli çift, 3 derinlikte en kötü durumda 12 çift kalıyor;
# 17 Eki'de 23 çiftle eklenmişti)
# 18 Eki (2): cephe yangını da (Parti 2 sonrası 6 + 4 madde, 7 hariç çift: 3 derinlikte en kötü durumda aday biter,
# 1 derinlikte 9 çift kalır)
BEAT_BLOCK_FALLBACK_EVENTS = (EARTHQUAKE_APARTMENT, EARTHQUAKE_OLD_STREET, LANDFALL, WILDFIRE, AVALANCHE_VILLAGE,
                              FACADE_FIRE)

# ── Kilit görsel (0-4s'nin ilk cümlesi, kod yazar) ──────────────────────────────────────────────────────────
EVENT_KEY_VISUAL = {
    # 3 Eki, Bahadır onayı. Kaynak: zaman damgalı Seedance testi (fd6882cd) ve stil ekindeki kamera nesnesi.
    FLOOD: "A waist-high wall of brown muddy floodwater surges into the street.",
    # 4 Eki, Bahadır onayı. Kaynak: EVENT_OUTCOMES'taki kahverengi molozlu dalga (1 Eki, 6 görünüm videosu).
    TIDAL: "A towering brown tidal wave thick with debris crashes over the waterfront onto the coastal street.",
    # TASLAK (4 Eki, Bahadır hazırlığı, onay bekliyor): heyelan
    # 21 Eki (genel kalite), Bahadır: çamur gri lapa gibi çıktı; "mud" geçen ilk ifadeye doku. Önceki: "A massive wall
    # of brown mud and rocks tears loose...", "...a fast torrent of brown mud and rocks surges across the road.", "A
    # massive torrent of brown mud, logs and rocks bursts through the drenched hillside village."
    MUDSLIDE: "A massive wall of thick brown mud full of rocks, branches and debris tears loose from the saturated "
              "hillside and pours down the steep street.",
    SLOPE: "The saturated slope collapses and a fast torrent of thick brown mud full of rocks, branches and debris "
           "surges across the road.",
    VILLAGE: "A massive torrent of thick brown mud full of rocks, branches and debris bursts through the drenched "
             "hillside village.",
    # TASLAK (4 Eki, Bahadır hazırlığı, onay bekliyor): hortum
    LANDFALL: "A violent tornado makes landfall on the waterfront, tearing roofs and signs into the air.",
    # 4 Eki, Bahadır: marina test videosunda sorun çıktı. Eski: "A violent tornado crosses the marina, bending masts
    # and ripping covers off the yachts as it sweeps toward the quay road." Ara taslak (canlıya alınmadı; Z6/Y5 ile
    # aynı nesneler, 22 kelime): "A violent tornado slams into the marina, ripping covers off the yachts and hurling
    # deck chairs and dock boxes across the quay."
    # 4 Eki, Bahadır: marina yeniden tasarımı (yüksek teras, rıhtım ve kafe sahneleri). Önceki canlı metin:
    # "A violent tornado slams into the marina, ripping covers off the yachts and hurling debris across the quay."
    MARINA_TORNADO: "A violent tornado tears in from the sea onto the marina quay, ripping palms and umbrellas off the "
                    "ground.",
    AVENUE: "A violent tornado sweeps down a palm-lined coastal avenue, hurling signs, branches and debris along the "
            "road.",
    # TASLAK (8 Eki, Bahadır): yangın kilit cümleleri, Bahadır'ın metni birebir
    WILDFIRE: "A towering wall of flames sweeps down the forested slope and slams into the edge of the neighborhood, "
              "igniting roofs and trees.",
    FACADE_FIRE: "Flames race up the glass facade of a tower, blowing out windows and raining burning debris onto the "
                 "street.",
    # 15 Eki (2), Bahadır: hortum dev ve karenin ana unsuru, ölçek kıyası. Önceki: "A violent fire tornado tears across
    # a burning roadside, hurling flames, burning branches and embers across the road."
    # 16 Eki, Bahadır: ortam ekseni (FIRE_TOR_ENVS). Gerçek kilit cümle seçilen ortamınkidir (event_key_visual); bu
    # değer ilk ortamın cümlesi (varsayılan). Önceki (15 Eki 2): "A colossal fire tornado, several times taller than the
    # tallest buildings and trees, tears across the burning roadside, its wide base engulfing a field of flames."
    # 18 Eki (2), Bahadır: dönen huni (videolarda düz yangın sütunu çıkıyordu). Önceki başlangıç: "A colossal fire
    # tornado, several times taller than the houses and trees, ..."
    FIRE_TORNADO: "A colossal spinning fire tornado, a twisting funnel several times taller than the houses and trees, "
                  "tears out of a burning forest into a residential area, its wide base engulfing the houses.",
    # 10 Eki, Bahadır onayı: helikopter kilit cümlesi birebir
    HELICOPTER: "A firefighting helicopter swoops over a hillside neighborhood and drops a huge load of water onto the "
                "wall of flames racing toward the houses.",
    # 10 Eki, Bahadır: volkan kilit cümleleri birebir
    ERUPTION: "The volcano erupts above a village, a shockwave blowing out windows along the street as an ash column "
              "towers into the sky.",
    PYROCLASTIC: "A pyroclastic cloud races down the volcano’s flank and slams into a village street.",
    VOLCANIC_BOMBS: "Glowing volcanic bombs streak down from the erupting volcano and slam into a village street, "
                    "punching through roofs and igniting cars.",
    # 13 Eki, Bahadır: çığ kilit cümleleri birebir. 14 Eki (ilk test dersi): ilk temas ilk 2 saniyede, kameranın hemen
    # altındaki yapıya (köy testinde ilk ev ~5. sn'de vuruldu). Bahadır kararı (14 Eki): b kuralı (hikâyede "camera"
    # yok) korunur, metindeki "right below the camera" yerine "right below the railing". Önceki köy: "...slams into a mountain village, a wall
    # of snow engulfing the first chalets."; kayak: "...hits a mountain lodge, a cloud of snow bursting over its
    # terrace."; orman: "...rips through a pine forest above a valley and hits the houses below, a white cloud rolling
    # over them."
    # 14 Eki (2), Bahadır: köyde "village" eklendi (olay adı kapısı en az 2 kök ister; GPT ipucu kaldırıldı)
    # 14 Eki (4), Bahadır: çığ ilk ~10 sn yavaş yaklaştı (ilk temas 11. sn). Çığ ilk karede evlerin içinde ("is
    # already crashing"); "right below the railing" çıktı (insanların yakınlığı kodda aynen: slice_near_camera).
    # Önceki köy: "A powder avalanche thunders down the slope and smashes into the village chalets right below the
    # railing, snow bursting over their roofs and through the street."; kayak: "An avalanche crashes down the ski
    # slope and slams into the lodge right below the railing, a cloud of snow bursting over its terrace."; orman:
    # "A huge avalanche rips through the pine forest above and hits the cabins right below the railing, a white cloud
    # rolling over their roofs."
    # 14 Eki (5), Bahadır: yamaç açıkça anılır ("roaring down the steep slope / ski slope / through a pine forest").
    # Önceki (4): köy "...is already crashing into the first chalets of a village..."; kayak "...is already slamming
    # into a mountain lodge, snow bursting over its terrace and walls."; orman "...is already ripping through a pine
    # forest and hitting the cabins at its edge, a white cloud rolling over their roofs."
    AVALANCHE_VILLAGE: "A powder avalanche is already roaring down the steep slope into the first chalets of a village, a "
                       "wall of snow bursting over their roofs and through the street.",
    AVALANCHE_SKI: "An avalanche is already roaring down the ski slope into a mountain lodge, snow bursting over its "
                   "terrace and walls.",
    AVALANCHE_FOREST: "An avalanche is already roaring down through a pine forest into the cabins at its edge, a white "
                      "cloud rolling over their roofs.",
    # 14 Eki, Bahadır: deprem kilit cümleleri birebir (aksiyon ilk karede: "is already shaking")
    EARTHQUAKE_APARTMENT: "The ground is already shaking violently and a six-storey apartment block across the street "
                          "collapses floor by floor, a huge dust cloud bursting out of it.",
    EARTHQUAKE_OLD_STREET: "The ground is already shaking violently and a row of old stone houses along the street "
                           "collapses one after another, dust and rubble bursting into the street.",
    # 29 Eki, Bahadır: meteor kilit cümlesi birebir (0-4s)
    METEOR: "A blazing meteor tears across the sky trailing fire and smoke and slams into the sea just off the coast, "
            "erupting in a blinding flash and a towering column of water and steam.",
}

# ── Bölge araçları (4-9s'deki {vehicle}). Görünüm tariflerindeki araçlardan. terms: dilimde aranan ad. ──────
# 17 Eki, Bahadır (temizlik turu): küçük araç yok (küçük araba, hatchback, kompakt, küçük van videoda kayboluyor).
# Önceki: north_african_coast small hatchback / small car, north_european_seaside small car / hatchback, riviera
# small car / hatchback, east_asian_coast small boxy car / compact car / small van. Eski adlar RETIRED_VEHICLES'ta.
REGION_VEHICLES = {
    "gulf_metropolis": [("white SUV", ("suv",)), ("pickup truck", ("pickup", "truck")), ("sedan", ("sedan", "saloon"))],
    "north_african_coast": [("large SUV", ("suv",)), ("pickup truck", ("pickup", "truck")),
                            ("delivery van", ("van",))],
    "us_coastal_town": [("pickup truck", ("pickup", "truck")), ("SUV", ("suv",)), ("sedan", ("sedan", "saloon"))],
    "north_european_seaside": [("large SUV", ("suv",)), ("delivery truck", ("truck", "lorry")),
                               ("delivery van", ("van",))],
    "riviera": [("large SUV", ("suv",)), ("pickup truck", ("pickup", "truck")), ("delivery van", ("van",))],
    "east_asian_coast": [("large SUV", ("suv",)), ("box truck", ("truck", "lorry")), ("delivery van", ("van",))],
}
# ── Olay araçları: bölge görünümü olmayan olaylarda (TASLAK, 4 Eki, heyelan). Görünümlü olaylar REGION_VEHICLES. ─
# 17 Eki: "small car" -> "delivery truck"; köyde "small van" / "old hatchback" -> "white van" / "large SUV"
_BIG_VEHICLES = [("pickup truck", ("pickup", "truck")), ("delivery truck", ("truck", "lorry")), ("white van", ("van",)),
                 ("SUV", ("suv",))]
EVENT_VEHICLES = {
    MUDSLIDE: _BIG_VEHICLES,
    SLOPE: _BIG_VEHICLES,
    VILLAGE: [("pickup truck", ("pickup", "truck")), ("white van", ("van",)), ("large SUV", ("suv",))],
    # TASLAK (4 Eki, hortum)
    LANDFALL: _BIG_VEHICLES,
    MARINA_TORNADO: _BIG_VEHICLES,
    AVENUE: _BIG_VEHICLES,
    # TASLAK (8 Eki, yangın). Orman ve cephe yangınında araç havalanmaz (NO_LIFT_SLICE); ateş hortumunda havalanır
    WILDFIRE: _BIG_VEHICLES,
    FACADE_FIRE: _BIG_VEHICLES,
    FIRE_TORNADO: _BIG_VEHICLES,
    # 10 Eki: helikopter (araç sadece F3/F6'da; havalanmaz, NO_LIFT_SLICE)
    HELICOPTER: _BIG_VEHICLES,
    # 10 Eki: volkan. 13 Eki: lav ve kül bulutu araçsız (havuzlarında {vehicle} yok, uses_vehicle)
    ERUPTION: _BIG_VEHICLES,
    VOLCANIC_BOMBS: _BIG_VEHICLES,
}
# 17 Eki: çıkarılan küçük araç adları -> yerine gelen büyük araç (eski kayıt/fixture okunurken; üretimde seçilmez).
# Görünümlü olaylarda karşılık görünümün listesinden (RETIRED_VEHICLES_BY_VIEW), diğerlerinde olayın listesinden.
RETIRED_VEHICLES = {"small car": "delivery truck", "small hatchback": "large SUV", "hatchback": "large SUV",
                    "small boxy car": "large SUV", "compact car": "box truck", "small van": "white van",
                    "old hatchback": "large SUV"}
RETIRED_VEHICLES_BY_VIEW = {
    "north_african_coast": {"small hatchback": "large SUV", "small car": "pickup truck"},
    "north_european_seaside": {"small car": "large SUV", "hatchback": "delivery truck"},
    "riviera": {"small car": "large SUV", "hatchback": "pickup truck"},
    "east_asian_coast": {"small boxy car": "large SUV", "compact car": "box truck", "small van": "delivery van"},
}


def retired_vehicle(old: str, view: str | None) -> str:
    """Çıkarılan araç adının bugünkü karşılığı (görünüm varsa görünümün listesinden)."""
    return RETIRED_VEHICLES_BY_VIEW.get(view, {}).get(old) or RETIRED_VEHICLES[old]

# ── Olay havuzları. terms: her gruptan en az bir terim dilimde geçmeli (kök + eşanlamlı; çekimler otomatik:
# s/es/d/ed/ing/ies, ünsüz ikizleşmesi, e düşmesi). Düzensiz çekimler (spun, swept, tore...) ayrıca yazılır. ──
_DRAG = ("drag", "sweep", "swept", "carry", "carried", "shove", "push", "haul", "pull", "wash", "slide", "slid",
         "drift", "tow", "sweep away")
_SPIN = ("spin", "spun", "twirl", "whirl", "rotate", "swing", "swung", "pivot", "turn", "twist", "spiral")
_LIFT = ("lift", "hoist", "raise", "heave", "off its wheels", "off the ground", "off the road", "off the pavement",
         "airborne", "pick up", "picked up")
_POLE = ("lamppost", "lamp post", "streetlight", "street light", "street lamp", "streetlamp", "light pole",
         "lamp pole", "utility pole", "pole")
_HIT = ("into", "against", "crash", "slam", "smash", "collide", "ram", "hit", "strike", "struck", "plow", "plough",
        "bang", "jam", "pin", "wedge", "press", "hurl", "throw", "threw", "thrown")
_CAR = ("car", "cars", "vehicle", "sedan", "hatchback", "suv", "van", "truck", "pickup")
# Kıyı dev dalga (4 Eki). Sel girdileriyle aynı terimler burada adlandırıldı; sel girdileri olduğu gibi kalır.
_SIDEWAYS = ("sideways", "sideway", "broadside", "side-on", "side on")
_FLING = ("fling", "flung", "toss", "hurl", "throw", "threw", "thrown", "launch")
_SHOP = ("storefront", "store front", "shopfront", "shop front", "shop window", "shop", "store", "facade", "façade",
         "building")
_CURB = ("sidewalk", "pavement", "curb", "kerb", "footpath")
_TIP = ("tip", "topple", "overturn", "flip", "roll over", "rolls over", "rolled over", "capsize", "keel over",
        "on its side", "onto its side", "on to its side", "on its roof")
_BACKWARD = ("backward", "backwards", "in reverse", "rear-first", "rear first", "tail-first", "tail first",
             "rear end first", "boot first", "trunk first")
_TOGETHER = ("together", "bumper", "side by side", "in tandem", "locked", "both", "pair")
_ROW = ("row", "line", "one by one", "one after another", "one after the other", "in turn", "in sequence",
        "in succession",
        "sequence")   # 4 Eki, Bahadır: kuru provada "A sequence of parked vehicles" reddedildi
_RIP_AWAY = ("rip", "tear", "tore", "torn", "wrench", "break loose", "breaks loose", "broke loose", "pull", "drag",
             "sweep", "swept", "carry", "carried", "peel", "wash")
_FALL = ("topple", "fall", "fell", "collapse", "crash", "snap", "tip", "keel over", "go down", "goes down",
         "went down", "bend", "buckle", "give way", "gives way")
# Heyelan (TASLAK, 4 Eki). Kıyı dev dalga/sel girdilerindeki aynı terimler adlandırıldı; o girdiler olduğu gibi kalır.
_COLLAPSE = ("collapse", "crumble", "topple", "fall", "fell", "give way", "gives way", "gave way", "burst", "break",
             "broke", "cave", "tumble", "burst apart")
_UPROOT = ("uproot", "rip", "tear", "tore", "torn", "topple", "fall", "fell", "wrench", "pull", "snap", "carry",
           "carried", "sweep", "swept", "wash")
_FENCE = ("fence", "fences", "fencing", "picket")
_TEAR = ("tear", "tore", "torn", "rip", "wrench", "sweep", "swept", "carry", "carried", "pull", "snap", "break",
         "broke", "collapse", "flatten", "uproot")
_BURY = ("bury", "buried", "engulf", "swallow", "submerge", "sink", "sank", "sunk", "to its windows",
         "up to its windows", "window-deep", "door-deep")
# 23 Eki, Bahadır (heyelan testi): GPT "crashing it into a chalet's wooden balcony" yazdı, M8 reddedildi. "chalet"
# eklendi (çoğul ve "chalet's" çekimle eşleşir; home, cottage, cabin zaten vardı)
_HOUSE = ("wall", "house", "home", "building", "facade", "façade", "cottage", "cabin", "doorway", "chalet")
_GUARDRAIL = ("guardrail", "guard rail", "crash barrier", "barrier", "railing")
_ROCK = ("boulder", "rock", "stone")
_LOGS = ("log", "logs", "timber", "lumber", "woodpile", "wood pile", "tree trunk", "trunks")
_BUMP = ("bump", "knock", "clip", "scrape", "graze", "jostle", "hit", "slam", "crash", "ram", "smash", "collide")
_NEIGHBOR = ("beside", "next", "another", "other", "second", "parked", "adjacent", "neighboring", "neighbouring")
# Heyelan H6/R6 (4 Eki, Bahadır onayı): kuru provada GPT "the car behind it", "the trailing car" yazdı. Ortak
# _TOGETHER (sel, kıyı dev dalga) değişmez; çıplak "behind" bilerek yok.
_TOGETHER_LANDSLIDE = _TOGETHER + ("the car behind it", "trailing", "following")
# 22 Eki (heyelan denetimi): yeni H6 (evin ön basamakları) ve R2 (yolun karşısındaki kaya duvarı)
_STEPS = ("front steps", "steps", "stairs", "stairway", "stoop", "doorstep", "porch", "entrance")
_ROCK_FACE = ("rock face", "rock wall", "cliff", "slope", "hillside", "embankment", "rock", "rocks")
# Hortum (TASLAK, 4 Eki). Mevcut listeler yeniden kullanılır; aşağıdakiler sadece hortum girdilerinde.
_BLOW = ("blow", "blew", "blown", "gust")
_WINDSHIELD = ("windshield", "windscreen", "front glass", "glass", "window")
_AIRBORNE = ("fly", "flew", "flying", "whirl", "swirl", "blow", "blew", "blown", "scatter", "spin", "spun")
_SIGN = ("sign", "signboard", "signpost", "billboard", "hoarding", "advertising board")
_SHELTER = ("bus shelter", "bus stop", "shelter")
_BOAT = ("yacht", "boat", "sailboat", "motorboat", "cruiser")
# Uçma maddeleri (4 Eki, Bahadır onayı): C5/C6, Y5/Y6, P5/P6 araç havalanır
# 4 Eki, Bahadır: sadece fiilli kalıplar; "into the air" gibi yer ifadeleri başka nesneyle eşleşiyordu (kuru provada
# "hovers ... fragments into the air" Y5'ten geçti). "ascend" eklendi, "hover" bilerek yok.
_LIFT_AIR = _LIFT + ("swept up", "sweep up", "sweeps up", "ascend")
_CRASH_DOWN = ("crash", "slam", "smash", "land", "drop", "plunge", "plummet", "come down", "comes down", "came down",
               "fall", "fell", "hit", "strike", "struck",
               "collapse")   # 4 Eki, Bahadır: sadece kabulü genişletir
# Marina söküm/fırlatma (4 Eki, Bahadır): hortuma özel; heyelanın ortak _TEAR listesi değişmez
_TORNADO_RIP = ("tear", "tore", "torn", "rip", "wrench", "strip", "peel", "dislodge", "snap", "break", "broke",
                "sweep", "swept", "carry", "carried") + _FLING + _AIRBORNE
# 23 Eki (hortum denetimi): marina ofisi (Y3, Z2) ve marina suyu (Y5, Z3); sadece marina girdilerinde
_MARINA_OFFICE = ("office", "marina office", "harbor office", "harbour office", "harbormaster", "harbourmaster",
                  "clubhouse", "building")
_MARINA_WATER = ("water", "sea", "harbor", "harbour", "basin", "splash")
_DOWNHILL = ("downhill", "down the hill", "down the slope", "down the street", "down the lane", "along the lane",
             "down the road", "along the road")
# Yangın (TASLAK, 8 Eki, Bahadır): yangına özel YENİ listeler; mevcut sel/heyelan/hortum listelerine dokunulmaz ve
# onlardan türetilmez. Alevin bir şeye değdiği görünmeli: alev/tutuşma grupları sadece "rüzgâr esiyor" anlatımını
# geçirmez. Çok kelimeli terimlerde çekim sadece son kelimeye uygulanır, diğer çekimler ayrıca yazılır.
_FIRE_FLAME = ("flame", "fire", "blaze", "burn", "burnt", "inferno", "ablaze", "alight", "afire", "firestorm",
               "fiery", "aflame", "smolder", "smoulder")   # 10 Eki, Bahadır: canlıda "fiery" reddedildi
_FIRE_IGNITE = ("ignite", "catch fire", "catches fire", "caught fire", "catching fire", "set alight", "sets alight",
                "setting alight", "set ablaze", "sets ablaze", "setting ablaze", "set on fire", "sets on fire",
                "setting on fire", "set fire", "sets fire", "setting fire", "burst into flame", "bursts into flame",
                "burst into flames", "bursts into flames", "bursting into flames", "go up in flames",
                "goes up in flames", "went up in flames", "going up in flames", "engulf", "consume", "torch",
                "kindle", "swallow", "devour", "envelop", "ablaze", "alight", "on fire", "in flames")
_FIRE_EMBER = ("ember", "spark", "cinder", "glowing ash", "burning ash", "firebrand")
_FIRE_FALL = ("fall", "fell", "fallen", "crash", "topple", "drop", "collapse", "come down", "comes down",
              "came down", "coming down", "tumble", "plunge", "slam", "smash", "land")
_FIRE_TREE = ("tree", "pine", "trunk", "branch", "limb", "bough")
# 17 Eki (yumuşak kapı düzeltmesi): helikopterde "treetops" ağaç sayılır (2i kuru deneme yanlış reddi, G1). Sadece
# helikopter (F4, G1, G2); orman yangınının _FIRE_TREE listesi değişmez.
_FIRE_HELI_TREE = _FIRE_TREE + ("treetop", "treeline", "tree line")
_FIRE_REVERSE = ("reverse", "back up", "backs up", "backed up", "backing up", "backward", "backwards", "retreat")
_FIRE_BACK = _FIRE_REVERSE + ("back away", "backs away", "backed away", "backing away", "lurch back",
                              "lurches back", "lurched back", "lurching back", "jerk back", "jerks back",
                              "jerked back", "pull back", "pulls back", "pulled back", "roll back", "rolls back",
                              "rolled back")
_FIRE_STOP = ("skid", "stop", "brake", "halt", "screech", "jolt", "slide", "slid")
_FIRE_TOUCH = ("lick", "touch", "reach", "scorch", "sear", "engulf", "wrap", "lap", "curl", "blister", "char",
               "singe", "envelop", "cover", "brush", "swallow")
_FIRE_FRONT = ("hood", "bonnet", "bumper", "grille", "grill", "front", "windshield", "windscreen")
_FIRE_ROOF = ("roof", "rooftop", "roofs")
_FIRE_SWERVE = ("swerve", "veer", "dodge", "weave", "steer", "jerk", "lurch", "swing", "swung",
                # 10 Eki, Bahadır: canlıda "maneuvers" reddedildi
                "maneuver", "manoeuvre", "evade", "sidestep", "careen", "zigzag")
_FIRE_RAIL = ("guardrail", "guard rail", "crash barrier", "barrier", "railing")
_FIRE_UTURN = ("u-turn", "turn around", "turns around", "turned around", "turning around", "whip around",
               "whips around", "whipped around", "wheel around", "wheels around", "spin around", "spins around",
               "spun around", "swing around", "swings around", "swung around", "turn back", "turns back",
               "turned back", "about-face")
_FIRE_CLOSE = ("close", "block", "cut off", "cuts off", "seal", "swallow", "engulf", "cover", "fill", "consume",
               "behind")
_FIRE_SPEED = ("race", "speed", "sped", "flee", "fled", "accelerate", "tear", "tore", "hurtle", "barrel", "zoom",
               "dash", "bolt", "drive", "drove", "away")
_FIRE_GLASS = ("window", "glass", "windshield", "windscreen")
_FIRE_CRACK = ("crack", "shatter", "split", "craze", "burst", "break", "broke", "blow out",
               "blows out", "blew out", "explode")
_FIRE_HOUSE = ("roof", "rooftop", "house", "home", "cottage")
_FIRE_FENCE = ("fence", "fencing", "picket", "palisade")
_FIRE_POLE = ("power pole", "utility pole", "telephone pole", "electricity pole", "pole", "pylon")
_FIRE_WIRE = ("wire", "cable", "power line", "line")
_FIRE_SNAP = ("snap", "break", "broke", "sever", "part", "fall", "fell", "drop", "whip", "lash", "spark")
_FIRE_PANEL = ("panel", "cladding", "sheet", "section", "slab")
_FIRE_DEBRIS = ("debris", "wreckage", "rubble", "fragment", "chunk", "piece", "panel", "cladding")
_FIRE_CRUSH = ("crush", "crumple", "cave", "flatten", "dent", "roof", "smash")
_FIRE_CURB = ("curb", "kerb", "sidewalk", "pavement", "footpath")
_FIRE_AWNING = ("awning", "canopy", "sunshade", "shade")
_FIRE_FLOOR = ("floor", "storey", "story", "level", "above", "upper", "higher")
_FIRE_BLOWOUT = ("blow out", "blows out", "blew out", "blowing out", "burst", "shatter", "explode", "smash", "break",
                 "broke", "pop")
_FIRE_PEEL = ("peel", "tear", "tore", "torn", "rip", "strip", "detach", "break", "broke", "come loose",
              "comes loose", "fall", "fell", "tumble", "drop", "plunge")
_FIRE_SMOKE = ("smoke",)
_FIRE_POUR = ("pour", "billow", "roll", "surge", "erupt", "belch", "spew", "gush", "burst", "climb")
_FIRE_TOWER = ("tower", "facade", "façade", "building", "floor", "storey", "story")
_FIRE_BALCONY = ("balcony", "balconies", "terrace")
_FIRE_FURNITURE = ("plant", "furniture", "chair", "table", "sofa", "cushion", "pot")
# Ateş hortumu (15 Eki, Bahadır): 10:44 testinde GPT'nin doğru T6/U4 cümleleri reddedildi. Kapı anlam bazlı (deprem
# yaklaşımı): her maddede NESNE + EYLEM grupları, eş anlamlılar geniş; listeler SADECE ateş hortumunun (_FIRE_TOR_*),
# diğer yangın olaylarının ortak listeleri değişmez. T maddelerinde araç grubu var: U maddelerinin cümleleri (çatı,
# ağaç, çalı yığını...) T sayılmasın. "spinning/whirling/swirling" hortumun kendi sıfatı olduğu için dönme grubu tek
# başına ayırt edici değil: T3 aşağı iniş (_FIRE_TOR_DOWN), T6 enkaz + çarpma ister. Yanlış pozitif testi:
# tests/test_fire_tornado_gate.py.
_FIRE_TOR_VEH = ("vehicle", "car", "suv", "truck", "pickup", "van")
# "into the air" araç grubuyla birlikte güvenli (8 Eki'de tek başına bilerek yoktu)
_FIRE_TOR_LIFT = ("lift", "hoist", "raise", "heave", "airborne", "aloft", "skyward", "skywards", "into the air",
                  "into the sky", "into the vortex", "into the funnel", "into the column", "suck into", "sucks into", "sucked into", "sucking into",
                  "drawn into", "pulled into", "swept into", "into the tornado",
                  "into the fire tornado", "into the whirlwind", "off its wheels",
                  "off the ground", "off the road", "off the asphalt", "off the pavement", "off the tarmac", "from the road",
                  "from the asphalt", "from the ground", "from the pavement", "upward", "upwards", "up into", "pick up",
                  "picks up", "picked up", "sweep up", "sweeps up", "swept up", "suck up", "sucks up", "sucked up",
                  "pluck", "snatch", "rise", "rose", "risen", "ascend", "levitate", "haul up", "hauls up", "hauled up",
                  "yank up", "yanks up", "yanked up", "carry up", "carries up", "carried up", "loft")
_FIRE_TOR_HURL = ("fling", "flung", "toss", "hurl", "throw", "threw", "thrown", "launch", "slam", "smash", "crash",
                  "hurtle", "ram", "dash", "pitch", "send", "sent", "drive", "drove", "driven", "hit", "strike",
                  "struck", "plow", "plough", "wrap", "impale", "pin", "wedge", "carry", "carried", "deposit", "dump",
                  "drop", "shove", "propel", "catapult", "bash", "batter")
# Bütün ağaç (T1, U2); "fir" yok ("fired" ile karışır). T2 dalı ayrıca.
_FIRE_TOR_TREE = ("tree", "pine", "trunk", "oak", "cedar", "cypress", "eucalyptus", "poplar", "olive", "birch", "spruce")
# 15 Eki (2): T2 dal yerine bütün ağaç gövdesi aracın üstüne; "onto" yok (T1 "aracı ağaca fırlatır" ile karışır)
_FIRE_TOR_TRUNK = _FIRE_TOR_TREE + ("log", "timber")
_FIRE_TOR_CRUSH = ("crush", "cave", "flatten", "crumple", "pin", "bury", "dent", "squash", "roof", "cab", "on top of",
                   "land on", "lands on", "landed on", "fall on", "falls on", "fell on", "drop on", "drops on",
                   "dropped on", "pancake", "buckle")
_FIRE_TOR_SPIN = ("spin", "spun", "twirl", "whirl", "rotate", "twist", "spiral", "tumble", "cartwheel", "roll", "flip",
                  "end over end", "somersault", "revolve", "corkscrew", "pirouette", "turn over", "turns over",
                  "turned over", "gyrate")
_FIRE_TOR_DOWN = ("crash down", "crashes down", "crashed down", "slam down", "slams down", "slammed down",
                  "smash down", "smashes down", "smashed down", "come down", "comes down", "came down", "coming down",
                  "drop", "plunge", "plummet", "land", "fall", "fell", "onto the road", "onto the asphalt",
                  "onto the pavement", "onto the tarmac", "onto the ground", "to the ground", "back onto", "back down",
                  "down onto", "down on", "hit the road", "hits the road", "hit the ground", "hits the ground",
                  "slam onto", "slams onto", "slammed onto", "crash onto", "crashes onto", "crashed onto",
                  "smash onto", "smashes onto", "smashed onto", "thud", "touch down", "touches down")
# T3 (15 Eki (4), Bahadır): canlıda doğru T3 cümleleri reddedildi ("draws the van upward ... crashes", "engulfs a van
# ... crashing down", "caught in the vortex ... crashing"). Şart: araç + hortuma kapılma/kaldırma + çarpma/iniş; dönme
# şart değil. "crash/slam/smash" tek başına iniş sayılır, bu yüzden T1 (ağaca çarpar) ve T5 (ters döner) cümleleri
# "unless" ile ayrılır. "whirl/spin" kapılma sayılmaz ("fire whirl" hortumun adı).
# 17 Eki: T3 havuzdan çıktı (RETIRED_BEATS); aşağıdaki listeler artık hiçbir maddede kullanılmıyor (arşiv, madde geri
# gelirse hazır).
_FIRE_TOR_SWEPT = _FIRE_TOR_LIFT + ("draw", "drew", "drawn", "pull", "suck", "catch", "caught", "grab", "snatch",
                                    "engulf", "swallow", "whisk", "carry", "carried", "seize", "scoop", "haul", "drag",
                                    "yank", "overhead", "high above", "midair", "mid-air", "in the air")
_FIRE_TOR_LANDING = _FIRE_TOR_DOWN + ("crashing down", "slamming down", "smashing down", "come crashing",
                                      "comes crashing", "came crashing", "coming crashing", "crash", "slam", "smash",
                                      "hit", "strike", "struck", "fallen", "down")
_FIRE_TOR_T3_UNLESS = _FIRE_TOR_TREE + ("upside down", "onto its roof", "on its roof", "onto its side", "overturn",
                                        "belly up", "roll over", "rolls over", "rolled over")
_FIRE_TOR_SKID = ("skid", "slide", "slid", "fishtail", "sideways", "swerve", "veer", "slew", "drift", "broadside",
                  "careen", "lurch", "spin out", "spins out", "spun out", "slip", "swing", "swung", "jackknife", "yaw",
                  "sidelong", "crabwise")
_FIRE_TOR_EMBER = _FIRE_EMBER + ("ash",)
# T4 (15 Eki (2)): hortumun tabanı aracın hemen arkasından geçer. "by" yok (T6 "flung by the tornado")
_FIRE_TOR_PASS = ("behind", "past", "passes", "passed", "passing", "alongside", "right next", "next to", "inches",
                  "close", "beside", "cross", "at its back", "in its wake", "graze", "skim", "brush past",
                  "brushes past", "just miss", "just misses", "just missed", "rake", "tail")
# T5 (15 Eki (2)): araç takla atar/ters döner. "roll" tek başına var ("rolls the van over")
_FIRE_TOR_FLIP = ("roll over", "rolls over", "rolled over", "rolling over", "roll", "flip", "overturn", "tip over",
                  "tips over", "tipped over", "onto its roof", "on its roof", "onto its side", "upside down",
                  "capsize", "turn over", "turns over", "turned over", "topple", "keel over", "keels over",
                  "keeled over", "somersault", "cartwheel", "belly up", "wheels up", "upend",
                  # 15 Eki (3): "is knocked over" (denetim boşluğu)
                  "knock over", "knocks over", "knocked over", "knocking over")
# T5 tutuşma: "catch/caught/lick/spread" yok ("caught in the vortex" T3 cümlesini T5 sayıyordu)
_FIRE_TOR_IGNITE = _FIRE_IGNITE + ("take hold", "takes hold", "took hold", "taking hold", "flare up", "flares up",
                                   "flared up", "light up", "lights up", "lit up", "erupt in flame", "erupts in flame",
                                   "erupted in flame", "erupt in flames", "erupts in flames", "erupted in flames",
                                   "erupting in flames", "start burning", "starts burning", "started burning",
                                   "begin burning", "begins burning", "began burning", "start to burn",
                                   "starts to burn", "started to burn", "begin to burn", "begins to burn",
                                   "began to burn", "scorch", "sear", "char", "blacken", "smolder", "smoulder",
                                   "blister", "melt", "erupt into flames", "erupts into flames", "erupted into flames",
                                   "fireball", "inferno")
_FIRE_TOR_DEBRIS = _FIRE_DEBRIS + ("shard", "scrap", "plank", "board", "firebrand", "projectile", "fireball")
_FIRE_TOR_IMPACT = ("slam", "smash", "crash", "collide", "hit", "strike", "struck", "pound", "ram", "batter", "punch",
                    "plow", "plough", "bash", "smack", "barrel into", "barrels into", "barreled into", "barrelled into",
                    "sideswipe", "clip", "clout", "thump", "pummel", "hammer", "t-bone", "knock", "crunch", "dent",
                    "cave", "tear into", "tears into", "tore into", "rip into", "rips into", "ripped into", "plunge into",
                    "plunges into", "plunged into", "shove", "slap", "thud", "impact")
_FIRE_TOR_TURNSTOP = ("spin", "spun", "whirl", "twirl", "rotate", "pivot", "skid", "slew", "slide", "slid", "fishtail",
                      "swing around", "swings around", "swung around", "whip around", "whips around", "whipped around",
                      "turn sideways", "turns sideways", "turned sideways", "sideways", "crosswise", "broadside",
                      "sidelong", "halt", "stop", "rest", "stall", "standstill", "stranded", "block", "jackknife",
                      "careen", "grind", "ground to", "screech", "shudder")
# 15 Eki (2): "barn/shed/building" U3'ün (ahır) nesnesi, burada yok
_FIRE_TOR_HOUSE = ("house", "home", "cottage", "cabin", "farmhouse", "bungalow", "dwelling", "homestead")
_FIRE_TOR_RIP = ("rip", "tear", "tore", "torn", "wrench", "strip", "peel", "snap", "break", "broke", "broken", "lift",
                 "hurl", "fling", "flung", "toss", "throw", "threw", "thrown", "scatter", "blow off", "blows off",
                 "blew off", "blown off", "blow away", "blows away", "blew away", "blown away", "sweep", "swept",
                 "carry", "carried", "pull", "uproot", "suck", "spit", "yank", "pluck", "snatch", "wrest", "lose",
                 "loses", "lost", "drag", "haul", "rend", "shred", "detach", "free", "loose", "launch", "send", "sent",
                 "whisk", "heave", "pry", "prise", "dislodge", "shear", "claw", "sever", "split", "hoist")
_FIRE_TOR_UPROOT = _FIRE_TOR_RIP + ("root", "out of the ground", "from the ground", "out of the earth",
                                    "from the earth", "from the soil", "topple", "knock down", "knocks down",
                                    "knocked down", "flatten")
# U3 (15 Eki (2)): tabela yerine ahır. Marina Z6 kelimeleri (wreck, demolish, splinter, tear apart...) bilerek yok.
_FIRE_TOR_BARN = ("barn", "shed", "stable", "outbuilding", "farm building", "storehouse", "granary", "hayloft",
                  "toolshed")
_FIRE_TOR_WRECK = _FIRE_TOR_RIP + ("swallow", "engulf", "consume", "devour", "apart", "to pieces", "shred", "explode",
                                   "burst", "collapse", "flatten", "smash", "crush", "cave", "crumple", "level", "raze",
                                   "gut",
                                   # 15 Eki (3): "knocks down/over the barn" (denetim boşluğu)
                                   "knock down", "knocks down", "knocked down", "knocking down", "knock over",
                                   "knocks over", "knocked over", "knocking over")
# U5 (15 Eki (2)): çit yerine odun yığını. "plank/beam/timber" yok (U3 ahırının tahtaları)
_FIRE_TOR_LOGS = ("log", "woodpile", "wood pile", "firewood", "lumber", "log pile", "cordwood", "woodstack",
                  "wood stack")
_FIRE_TOR_SCATTER = _FIRE_TOR_RIP + ("blast", "apart", "fly", "flies", "flew", "flying", "explode", "burst", "plow",
                                     "plough", "smash")
# Çalı yığını (U4): "debris" yok (U1'in "burning debris" cümlesi U4 sayılıyordu). 15 Eki (2): "pile/heap/stack/dry
# wood" yok (U5 odun yığını U4 sayılmasın); "pile of brush" brush ile geçer
_FIRE_TOR_BRUSH = ("brush", "brushwood", "scrub", "scrubland", "undergrowth", "shrub", "bush", "dry grass", "grass",
                   "twig", "thicket", "bramble", "kindling", "foliage", "vegetation", "leaves", "hay", "straw",
                   "chaparral", "sagebrush", "weeds", "tumbleweed")
_FIRE_TOR_INTAKE = ("suck", "draw", "drew", "drawn", "pull", "engulf", "lift", "swallow", "inhale", "scoop", "gather",
                    "gulp", "devour", "sweep up", "sweeps up", "swept up", "snatch", "pick up", "picks up", "picked up",
                    "take in", "takes in", "took in", "taken in", "vacuum", "consume", "absorb", "ingest", "whip up",
                    "whips up", "whipped up", "haul", "drag", "grab", "seize", "hoover", "siphon", "into the vortex",
                    "into the funnel", "into the column", "envelop", "wrap", "catch", "caught", "hoist", "raise",
                    "heave", "yank", "pluck", "rip up", "rips up", "ripped up", "tear up", "tears up", "tore up")
_FIRE_TOR_EJECT = ("spit", "spat", "spew", "hurl", "fling", "flung", "toss", "throw", "threw", "thrown", "scatter",
                   "eject", "spray", "shower", "fountain", "blast", "launch", "burst", "explode", "jet", "cascade",
                   "rain", "arc", "spill", "belch", "disgorge", "release", "send", "sent", "shoot", "shot", "flying",
                   "expel", "sling", "slung", "catapult", "hurtle", "strew", "strewn", "flick", "fan out", "fans out",
                   "fanned out", "propel", "discharge", "pour")
_FIRE_TOR_TRAILER = ("trailer", "caravan", "camper", "motorhome", "mobile home", "rv")
# 17 Eki (Parti 1): yeni yerleşim beat'lerinin nesne ve sütun grupları
_FIRE_TOR_COLUMN = ("column", "vortex", "funnel", "tornado", "whirlwind", "into the fire", "into the flames")
_FIRE_TOR_WALL = ("front wall", "facade", "façade", "house front", "front of the house", "front of a house",
                  "front of the home", "outer wall", "exterior wall")
_FIRE_TOR_PORCH = ("porch", "front steps", "steps", "stairs", "staircase", "stairway", "veranda", "stoop", "entrance")
_FIRE_TOR_GARAGE = ("garage", "carport", "workshop")
_FIRE_TOR_WHOLE = ("foundation", "whole house", "entire house", "whole home", "entire home", "whole", "entire",
                   "swallow", "devour", "gulp")
_FIRE_TOR_PLANKS = ("plank", "beam", "timber", "board", "rafter", "lumber")   # "splinter" yok (sadece marina Z6)
_FIRE_TOR_ROW = ("two houses", "both houses", "two homes", "pair of houses", "one after another", "one after the other",
                 "one by one", "in a row", "row of houses", "next house", "neighboring house", "neighbouring house",
                 "second house", "house next door", "in turn", "in quick succession")
_FIRE_TOR_ESCAPE = ("race", "speed", "sped", "accelerate", "flee", "fled", "escape", "drive away", "drives away",
                    "drove away", "driving away", "pull away", "pulls away", "pulled away", "zoom", "dash", "bolt",
                    "outrun", "hurtle", "barrel", "tear away", "tears away", "tore away", "floor it", "floors it")
_FIRE_TOR_TOSS = _FIRE_TOR_RIP + ("tip", "topple", "overturn", "flip", "roll", "knock", "capsize", "upend",
                                  "bowl over", "bowls over", "bowled over", "shove", "push", "slam", "smash", "crush",
                                  "engulf", "swallow", "flatten", "crumple", "overwhelm", "bounce", "tumble",
                                  "cartwheel")
_FIRE_FUEL = ("trailer", "caravan", "camper", "woodpile", "wood pile", "firewood", "log pile", "log", "logs")
_FIRE_TILE = ("tile", "shingle", "slate")
# Helikopter (10 Eki, Bahadır): su, buhar, helikopter, rotor rüzgârı. Yeni listeler; mevcutlar değişmez.
_FIRE_WATER = ("water", "deluge", "cascade", "torrent", "spray", "retardant", "slurry", "waterload")
_FIRE_STEAM = ("steam", "vapor", "vapour", "mist", "white cloud", "white smoke")
_FIRE_HELI = ("helicopter", "chopper", "rotorcraft", "aircraft", "heli")
_FIRE_DROP = ("drop", "dump", "release", "unload", "pour", "spill", "fall", "fell", "crash", "slam", "douse",
              "drench", "unleash", "let go", "lets go")
_FIRE_DOUSE = ("extinguish", "douse", "drench", "quench", "smother", "snuff", "put out", "puts out", "knock down",
               "knocks down", "flatten", "collapse", "die down", "dies down", "die out", "dies out", "sink", "sank",
               "shrink", "fizzle", "beat back", "beats back", "kill")
_FIRE_DOWNDRAFT = ("downdraft", "down draft", "downwash", "rotor wash", "rotorwash", "rotor", "blade", "gust", "blast",
                   "wind")
_FIRE_SMOKE_EMBER = ("smoke", "ember", "spark", "ash", "cinder")
_FIRE_BEND = ("bend", "bent", "sway", "thrash", "whip", "flatten", "lash", "shake", "shook", "toss", "scatter", "blow",
              "blew", "blown", "swirl", "fling", "flung")
_FIRE_LOW = ("low", "skim", "swoop", "roar", "thunder", "buzz", "sweep", "swept", "hover", "fly", "flies", "flew",
             "pass", "scream")
_FIRE_PATH = ("road", "street", "lane", "in front", "ahead", "path")
_FIRE_RETURN = ("fight back", "fights back", "flare", "reignite", "re-ignite", "rekindle", "surge", "burst", "erupt",
                "roar back", "roars back", "fresh", "again", "renewed")
_FIRE_AGAIN = ("another", "second", "again", "circle back", "circles back", "circled back", "return", "come back",
               "comes back", "came back", "fresh", "new", "more")
_FIRE_RETREAT = ("sink", "sank", "shrink", "retreat", "die down", "dies down", "recede", "fall back", "falls back",
                 "fell back", "subside", "dwindle", "ebb", "beaten back", "pushed back", "driven back")
_FIRE_LEAP = ("leap", "jump", "spread", "race", "catch", "ignite", "engulf", "climb", "lick", "reach")
_FIRE_PULLUP = ("pull up", "pulls up", "pulled up", "pulling up", "climb", "rise", "rose", "peel away", "peels away",
                "bank away", "banks away", "fly off", "flies off", "flew off", "away", "veer off", "veers off", "soar")
_FIRE_SECOND = ("second", "another", "other", "new", "two", "pair")
# 🌋 Volkan (10 Eki, Bahadır): yeni _VOLC_* listeleri, baştan geniş eş anlamlılarla (terim kapısı kuralı: GPT'nin
# doğal anlatımı reddedilmemeli). Mevcut listeler değişmez ve kullanılmaz. Çok kelimeli terimde çekim sadece son
# kelimede; diğer çekimler ayrıca yazıldı.
_VOLC_ROCK = ("rock", "boulder", "stone", "bomb", "chunk", "block", "lump", "fragment", "ejecta", "projectile",
              "fireball", "hunk", "slab")
_VOLC_SMASH = ("smash", "slam", "crash", "hit", "strike", "struck", "punch", "pierce", "puncture", "tear", "tore",
               "torn", "rip", "burst", "shatter", "crush", "crumple", "cave", "dent", "break", "broke", "blast",
               "blow out", "blows out", "blew out", "blown out", "explode", "destroy",
               "plow", "plough", "ram", "bash", "batter", "pound", "hammer", "split",
               "gouge", "land", "drill", "bore", "slice", "cleave", "impact")
_VOLC_SHOCK = ("shockwave", "shock wave", "blast wave", "pressure wave", "blast", "shock", "concussion", "air blast",
               "wave of pressure", "explosion")
_VOLC_SHOP = ("shop", "store", "storefront", "shopfront", "shop front", "window", "display", "café", "cafe",
              "boutique", "bakery", "facade", "façade", "glass front", "showroom")
_VOLC_GLASS = ("window", "windshield", "windscreen", "glass", "pane", "windowpane", "sunroof", "glazing")
_VOLC_BURST = ("burst", "shatter", "blow out", "blows out", "blew out", "blown out", "explode", "smash", "break",
               "broke", "pop", "implode", "cave in", "caves in", "caved in", "crack",
               "blast out", "blasts out", "blasted out", "spray", "shard", "fragment", "punch out",
               "punches out", "blow in", "blows in", "blew in", "blown in")
_VOLC_BRAKE = ("brake", "stop", "halt", "skid", "screech", "jolt", "standstill", "stop short", "stops short",
               "decelerate", "lurch")
_VOLC_TILE = ("tile", "shingle", "slate", "roofing", "roof", "terracotta", "pantile")
_VOLC_ROOF = ("roof", "rooftop", "tile", "shingle", "slate", "roofing", "rafter", "beam", "eave", "chimney")
_VOLC_VEH_ROOF = ("roof", "top", "sunroof", "cabin", "hood", "bonnet", "windshield", "windscreen")
_VOLC_RIP = ("rip", "tear", "tore", "torn", "strip", "peel", "wrench", "yank", "blow off", "blows off", "blew off",
             "blown off", "break loose", "breaks loose", "broke loose", "break free", "breaks free", "broke free",
             "come loose", "comes loose", "came loose", "detach", "dislodge", "lift", "shear", "snap", "pry",
             "blow the roof off", "blows the roof off", "blew the roof off", "blowing the roof off",
             "blow the tiles off", "blows the tiles off", "blew the tiles off")
_VOLC_FLING = ("hurl", "fling", "flung", "throw", "threw", "thrown", "toss", "send", "sent", "scatter", "spray",
               "sweep", "swept", "carry", "carried", "blow", "blew", "blown", "whirl", "fly", "flies", "flew",
               "shower", "cascade", "pelt", "rocket", "catapult", "launch", "hurtle", "slam", "smash", "crash",
               "tumble", "sail", "spin", "spun", "suck", "drag")
_VOLC_SIGN = ("sign", "signboard", "billboard", "placard", "banner", "signpost", "hoarding", "plaque", "awning",
              "canopy")
_VOLC_AWNING = ("awning", "canopy", "sunshade", "shade", "overhang", "tarp", "tarpaulin", "canvas", "marquee",
                "blind", "sunblind", "parasol", "umbrella")
_VOLC_FALL = ("fall", "fell", "fallen", "crash", "slam", "smash", "drop", "plunge", "plummet", "topple", "tumble",
              "collapse", "land", "hit", "strike", "struck", "come down", "comes down", "came down", "coming down",
              "hurtle", "thud", "give way", "gives way", "gave way", "keel over", "keels over", "keeled over",
              "go down", "goes down", "went down")
_VOLC_CAR = ("car", "cars", "vehicle", "sedan", "hatchback", "suv", "van", "truck", "pickup", "automobile", "coupe",
             "minivan", "jeep", "taxi", "wagon", "convertible")
_VOLC_SHUTTER = ("shutter", "roller shutter", "grille", "grate", "shop door", "door", "security gate", "metal blind",
                 "gate")
_VOLC_BUCKLE = ("buckle", "bend", "bent", "warp", "twist", "crumple", "bulge", "burst", "explode", "blow out",
                "blows out", "blew out", "blown out", "break", "broke", "tear", "tore", "torn", "rip", "fly", "flies",
                "flew", "cave", "pop", "snap", "fold", "blast")
_VOLC_ENGULF = ("engulf", "surround", "swallow", "envelop", "encircle", "consume", "devour", "bury", "buried",
                "swamp", "submerge", "close around", "closes around", "closed around", "flow around", "flows around",
                "flowed around", "wrap", "inundate", "overrun", "overwhelm", "overtake", "drown", "smother",
                "gulp", "eat")
_VOLC_PUSH = ("push", "shove", "drag", "carry", "carried", "sweep", "swept", "bulldoze", "plow", "plough", "force",
              "drive", "drove", "nudge", "heave", "slide", "slid", "roll", "propel", "ram", "move", "shunt",
              "bear", "bore")
_VOLC_WALL = ("wall", "garden wall", "stone wall", "brick wall", "boundary wall", "masonry", "brick",
              "retaining wall", "stonework")   # 13 Eki
_VOLC_TOPPLE = ("topple", "collapse", "crumble", "knock down", "knocks down", "knocked down", "flatten",
                "bulldoze", "burst", "break", "broke", "smash", "crush", "give way", "gives way", "gave way", "cave",
                "tumble", "fall", "fell", "burst through", "bursts through", "tear down", "tears down",
                "tore down", "push over", "pushes over", "pushed over", "breach", "overrun", "swallow",
                # 13 Eki (yeni lav L1): sadece kabulü genişletir
                "cave in", "caves in", "caved in", "uproot", "buckle", "sweep", "swept", "sweep away", "engulf", "bury", "buried", "shatter", "split", "crack", "pour over", "pours over",
                "poured over", "spill over", "spills over", "spilled over", "flow over", "flows over", "flowed over",
                # 13 Eki (2), yavaş lav L1: sadece kabulü genişletir
                "grind", "crawl over", "crawls over", "crawled over", "crawl across", "crawls across",
                "crawled across", "creep over", "creeps over", "crept over", "shove over", "shoves over",
                "shoved over", "push over", "bulge")
_VOLC_FENCE = ("fence", "fencing", "picket", "palisade", "railing", "gate", "hedge", "paling")
# 13 Eki (lav L2): kulübe/baraka
_VOLC_SHED = ("shed", "woodshed", "toolshed", "hut", "shack", "outbuilding", "outhouse", "barn", "lean-to",
              "storeroom", "storehouse", "garage", "cabin", "kiosk", "coop", "stable")
_VOLC_IGNITE = ("ignite", "catch fire", "catches fire", "caught fire", "catching fire", "burst into flames",
                "bursts into flames", "burst into flame", "bursts into flame", "go up in flames", "goes up in flames",
                "went up in flames", "set alight", "sets alight", "set ablaze", "sets ablaze", "set on fire",
                "sets on fire", "set fire", "sets fire", "ablaze", "alight", "on fire", "in flames", "aflame",
                "flare", "burn", "combust", "kindle", "torch", "blaze", "flame", "fire", "smolder", "smoulder",
                "inferno", "erupt in flames", "erupts in flames", "erupted in flames")   # 13 Eki
_VOLC_HOUSE = ("house", "home", "cottage", "building", "villa", "dwelling", "wall", "corner",
               "townhouse", "farmhouse", "residence")   # 13 Eki ("facade" bilerek yok: dükkân cephesi M3 ayrı kalsın)
# 13 Eki (lav M4; 13 Eki 4: bombalar T6): kat
_VOLC_FLOOR = ("floor", "storey", "story", "ground floor", "first floor", "lower floor", "level")
# Çökme (13 Eki, lav L3/M2 ve kül bulutu Q1). Çıplak "fall/fell/drop/crash/snap/break" bilerek yok: "ash keeps falling
# over the houses" gibi atmosfer cümlesi ev + düşme ile Q1'den geçmesin (önceki listede vardı, sadece eski M2'de).
# "burst/shatter" da yok: M1/M4'ün "flames bursting" cümlesi M2'den geçmesin (havuz içi ayırt edicilik testi).
# 13 Eki eklemelerinde de marina Z6 kelimeleri (wreck, demolish, splinter, tear/blow apart) bilerek yok
_VOLC_COLLAPSE = ("collapse", "cave", "cave in", "caves in", "caved in", "give way", "gives way", "gave way", "sag",
                  "bulge",   # 13 Eki (2), L3
                  "buckle", "crumble", "come down", "comes down", "came down", "fold", "tumble", "implode", "topple",
                  "crack", "split", "disintegrate", "slump", "crush", "flatten",
                  "crash down", "crashes down", "crashed down", "fall in", "falls in", "fell in",
                  "break apart", "breaks apart", "broke apart", "burst open", "bursts open")
_VOLC_POLE = ("utility pole", "power pole", "telephone pole", "electricity pole", "telegraph pole", "pole", "pylon",
              "lamppost", "lamp post", "streetlight", "street light", "light pole", "mast")
_VOLC_SPARK = ("spark", "arc", "flash", "cinder", "fireball", "ember", "electric arc", "glow")
_VOLC_CRUSH = ("crush", "smash", "shatter", "burst", "break", "broke", "cave", "flatten",
               "destroy", "swallow", "engulf", "bulldoze", "plow", "plough", "burst through",
               "bursts through", "tear through", "tears through", "tore through", "punch through", "punches through",
               "crash through", "crashes through", "crashed through", "blow out", "blows out", "blew out", "pour through",
               "pours through", "poured through", "flood", "fill",
               # 13 Eki (lav L2/M1): sadece kabulü genişletir
               "crumple", "topple", "collapse", "cave", "snap", "buckle", "sweep",
               "swept", "carry", "carried", "bury", "buried", "consume", "devour", "pour into", "pours into",
               "poured into", "break through", "breaks through", "broke through", "surge through", "surges through",
               "surged through", "flow through", "flows through", "flowed through", "pour in", "pours in",
               "poured in")
_VOLC_CLOUD = ("cloud", "pyroclastic", "ash cloud", "ash flow", "surge", "flow", "avalanche", "wall of ash",
               "ash wall", "billow", "plume", "cloud front", "debris cloud", "grey mass", "gray mass", "ash", "dust",
               "mass", "torrent")
# 13 Eki (kül bulutu P1): balkonlar
_VOLC_BALCONY = ("balcony", "veranda", "loggia", "railing", "balustrade")
# 13 Eki (kül bulutu Q3): baca
_VOLC_CHIMNEY = ("chimney", "chimney stack", "chimneystack", "smokestack", "flue", "chimney pot")
# 13 Eki (4): lav nehri çıktı; lava özel listeler (_LAVA_FAST, _LAVA_IMPACT, _LAVA_PEOPLE_FADE, _VOLC_HEAT, _VOLC_DOOR,
# _VOLC_LAVA) silindi, içerikleri EVENT_BEATS üstündeki ARŞİV notunda.
# 13 Eki (3), Bahadır kararı: volkan Kie prompt'u (hikâye + stil eki) en fazla 175 kelime
VOLC_MAX_PROMPT_WORDS = 175
# 29 Eki (2), Bahadır: sadece meteor 205 kelime (29 Eki (3); önce 195, 202) ve 11 kısıt (tek meteor / beyaz su / kalıcı hasar cümlesi ve kamera
# kuyruğu stil ekini uzattı). Diğer olaylar 175 / 8 / 1400.
PROMPT_WORDS_BY_EVENT = {"Meteor slams into the sea off the coast": 205}   # 29 Eki (3), Bahadır: 195 -> 202 -> 205
CONSTRAINTS_BY_EVENT = {"Meteor slams into the sea off the coast": 11}
PROMPT_CHARS_BY_EVENT: dict[str, int] = {}


def max_prompt_words(event: str) -> int:
    return PROMPT_WORDS_BY_EVENT.get(event, VOLC_MAX_PROMPT_WORDS)


def max_constraints(event: str) -> int:
    return CONSTRAINTS_BY_EVENT.get(event, 8)


def max_prompt_chars(event: str) -> int:
    return PROMPT_CHARS_BY_EVENT.get(event, MAX_PROMPT_CHARS)
# 13 Eki (4) yeni volkan maddeleri: çan kulesi (U5), oluklu sac çatı (P6), yol/krater (T5)
_VOLC_TOWER = ("bell tower", "belfry", "church tower", "clock tower", "steeple", "campanile", "spire", "tower")
_VOLC_METAL_ROOF = ("corrugated", "sheet metal", "metal sheet", "tin roof", "metal roof", "roofing sheet", "roof")
_VOLC_ROAD = ("road", "street", "asphalt", "pavement", "tarmac", "cobble", "cobblestone", "roadway")
_VOLC_CRATER = ("crater", "hole", "pit", "blast", "explode", "shatter", "crack", "burst", "split open", "splits open",
                "rip open", "rips open", "tear open", "tears open", "erupt", "heave", "buckle", "gouge")
_VOLC_TREE = ("tree", "trunk", "branch", "limb", "bough", "pine", "palm", "oak", "olive", "cypress", "elm", "maple",
              "frond",   # 13 Eki (4), P4
              "sapling", "twig", "log")
_VOLC_SNAP = ("snap", "break", "broke", "split", "crack", "shear", "topple", "fall", "fell", "flatten",
              "uproot", "tear", "tore", "torn", "rip", "bend", "bent", "collapse", "crash", "shatter", "fly", "flies",
              "flew", "hurl", "fling", "flung", "whirl", "blow", "blew", "blown", "go down", "goes down", "went down",
              "snap off", "snaps off", "snapped off",
              "knock down", "knocks down", "knocked down", "crash", "uproot", "sweep", "swept")   # 13 Eki
# Volkan bombaları (Bahadır): taşlar tek tek ve büyük görünmeli; genel/küçük anlatım (barrage, shower of rocks,
# pebbles...) kapıdan geçmez (VOLC_SINGLE_ROCK_FORBIDDEN)
_VOLC_SMALL_ROCKS = ("barrage", "volley", "hail of", "shower of rocks", "shower of stones", "shower of debris",
                     "rain of", "swarm", "pebble", "gravel", "grit", "small stone", "small rock", "tiny rock",
                     "tiny stone", "lapilli", "spray of rocks", "spray of stones", "hail")
# ❄️ Çığ (13 Eki, Bahadır): yeni _AVA_* listeleri (volkan derslerinden: nesne + fiil aranır; tek kelime eşleşmesi gevşek,
# anlam sıkı). "wall" tek başına duvar nesnesi değil ("snow wall" çığın kendisi): duvar grupları niteli ("stone wall").
# Marina Z6 kelimeleri (wreck, demolish, splinter, tear/blow apart...) bilerek yok.
_AVA_TREE = ("tree", "pine", "fir", "spruce", "larch", "conifer", "trunk")
_AVA_CHALET = ("chalet", "house", "home", "cabin", "cottage", "hut", "lodge", "building")
_AVA_SHED = ("shed", "woodshed", "hut", "shack", "outbuilding", "cabin", "storehouse", "barn", "annex", "lean-to",
             "extension", "wing")
_AVA_CABIN = ("cabin", "hut", "chalet", "house", "cottage", "lodge", "shed", "home")
_AVA_BARN = ("barn", "stable", "hayloft", "shed")
_AVA_HAY = ("hay", "straw", "bale")
_AVA_ROOF = ("roof", "rooftop", "roof deck", "roofing", "rafter", "shingle", "eave")
_AVA_STONEWALL = ("stone wall", "garden wall", "brick wall", "dry-stone wall", "retaining wall", "boundary wall",
                  "low wall", "field wall", "stonework", "masonry", "stones", "boulder", "rocks")
_AVA_FARMHOUSE = ("farmhouse", "farm house", "stone house", "stone wall", "farm", "stone cottage")
_AVA_STONEHOUSE = ("stone house", "house", "farmhouse", "cottage", "building", "home")
_AVA_FENCE = ("fence", "fencing", "fence post", "post", "railing", "barrier", "snow barrier", "safety fence", "rail",
              "balustrade", "handrail", "netting", "net", "snow fence")
_AVA_BALCONY = ("balcony", "veranda", "loggia")
_AVA_HOUSES = ("house", "chalet", "home", "cottage", "building", "cabin")
_AVA_TOWER = ("bell tower", "belfry", "church tower", "steeple", "spire", "campanile", "tower")
# 14 Eki (3): teleferik maddesi kalmadı; liste havuz kontrolünde (istasyon terası dışlaması) kullanılıyor
_AVA_LIFT = ("ski-lift", "ski lift", "chairlift", "chair lift", "lift tower", "lift pylon", "gondola", "cable",
             "pylon", "tower", "lift station", "station")
_AVA_LOGS = ("log", "firewood", "woodpile", "wood pile", "timber", "plank", "board", "trunk")
_AVA_WATERTOWER = ("water tower", "water tank", "tank", "tower", "cistern")
# 14 Eki, Bahadır (ilk test dersi): zayıf maddeler büyük ve koyu ahşap/taş nesneyle değişti. Yeni terimler: ahşap
# cephe (B5, D1), taş ahır (A4), kütük yığını (C6), kulübe (D4). "wall" tek başına yine yok ("snow wall").
_AVA_FACADE = ("front wall", "facade", "façade", "front", "side wall", "timber wall", "wooden wall", "outer wall",
               "beam", "timber", "plank", "board")
_AVA_STONEBARN = ("barn", "stable", "stone", "stones", "masonry", "stonework", "boulder", "rocks")
_AVA_LOGPILE = ("log", "timber", "woodpile", "wood pile", "log pile", "firewood", "trunk", "lumber")
_AVA_LODGE_TARGET = ("lodge", "building", "hotel", "chalet")
_AVA_HUT = ("ski-rental", "rental", "cabin", "hut", "shack", "shed", "kiosk", "booth",
            "storage", "ski-storage", "snack", "snack bar", "cafe", "café")   # 14 Eki (3): C1, C4
_AVA_FLY = ("fly", "flies", "flew", "flying", "scatter", "spray", "explode", "spill", "hurl", "fling", "flung",
            "launch", "shoot", "shot")
# 14 Eki (2), Bahadır: A4 false reject ("crashes into a sturdy stone barn, sending its dark stones ricocheting").
# Temas fiilleri: nesne (taş ahır) ayrıca aranır, fiil tek başına yetmez.
_AVA_IMPACT = ("crash", "collide", "slam", "hit", "ram", "smash", "strike", "struck", "plow", "plough", "ricochet",
               "send", "sent", "scatter", "burst", "explode")
# 14 Eki (3), Bahadır: zayıf madde temizliğinin yeni nesneleri. "wall" tek başına yine yok ("snow wall").
_AVA_STONECHALET = ("stone chalet", "stone house", "chalet", "house", "gable", "gable wall", "stone wall", "stonework",
                    "masonry", "stones")
_AVA_STAIRS = ("staircase", "stairs", "stairway", "steps", "stair")
_AVA_PORCH = ("porch", "entrance", "entryway", "doorway", "veranda", "portico", "canopy", "front")
_AVA_DECK = ("deck", "decking", "terrace", "platform", "boardwalk")
_AVA_STONEBUILDING = ("stone building", "service building", "building", "stone", "stones", "masonry", "stonework",
                      "outbuilding", "block")
_AVA_BARNDOOR = ("barn door", "barn", "door", "gate", "farmhouse", "stable")
_AVA_FLATTEN = ("flatten", "level", "mow down", "mows down", "mowed down", "knock down", "knocks down", "knocked down",
                "snap", "break", "broke", "topple", "uproot", "bend", "bent", "crush", "sweep", "swept", "tear", "tore",
                "torn", "rip", "whip", "swallow", "engulf", "bury", "buried", "fell", "lay flat", "lays flat",
                "laid flat", "push over", "pushes over", "pushed over")
_AVA_HURL = ("hurl", "fling", "flung", "throw", "threw", "thrown", "toss", "carry", "carried", "sweep", "swept", "drive",
             "drove", "send", "sent", "scatter", "launch", "propel", "shove", "push", "ram", "smash", "slam", "crash",
             "spear", "batter", "pile")
_AVA_RIP = ("rip", "tear", "tore", "torn", "wrench", "strip", "peel", "lift", "blow off", "blows off", "blew off",
            "blown off", "break loose", "breaks loose", "broke loose", "break away", "breaks away", "broke away", "shear",
            "pull", "yank", "snap off", "snaps off", "snapped off", "pry", "knock off", "knocks off", "knocked off",
            "smash", "scatter")
_AVA_SWEEP = ("sweep", "swept", "carry", "carried", "push", "shove", "drag", "slide", "slid", "bulldoze", "knock",
              "toss", "hurl", "fling", "flung", "roll", "tumble", "lift", "shift", "rip", "tear", "tore", "torn",
              "wrench", "dislodge", "pluck", "throw", "threw", "thrown", "move")
_AVA_COLLAPSE = ("collapse", "cave in", "caves in", "caved in", "give way", "gives way", "gave way", "crumble",
                 "topple", "burst", "shatter", "split", "crack", "break apart", "breaks apart", "broke apart",
                 "fall apart", "falls apart", "fell apart", "cave", "implode", "buckle", "fold", "smash", "crush",
                 "flatten", "disintegrate", "break up", "breaks up", "broke up", "break", "broke", "tumble")
_AVA_BLOWOUT = ("blow out", "blows out", "blew out", "blown out", "blow", "blew", "blown", "burst", "shatter",
                "explode", "smash", "break", "broke", "implode", "cave in", "caves in", "pop", "crack", "blast")
_AVA_TOPPLE = ("topple", "knock over", "knocks over", "knocked over", "knock down", "knocks down", "knocked down",
               "fall", "fell", "crash", "collapse", "tip", "keel over", "keels over", "keeled over", "bring down",
               "brings down", "brought down", "go down", "goes down", "went down", "flatten", "snap", "break", "broke",
               "tumble", "shove over", "shoves over", "shoved over", "push over", "pushes over", "pushed over", "mow down",
               "mows down", "mowed down", "buckle",
               "knock")   # "knocks a bell tower across the street" (ayrık, B3)
_AVA_SHATTER = ("shatter", "smash", "burst", "explode", "break", "broke", "blow out", "blows out", "blew out",
                "blown out", "implode", "crack", "cave in", "caves in", "crush", "blast")
_AVA_LIFT_UP = ("lift", "toss", "fling", "flung", "hurl", "throw", "threw", "thrown", "rip", "tear", "tore", "torn",
                "peel", "blow off", "blows off", "blew off", "flip", "heave", "sweep", "swept", "carry", "carried",
                "launch", "strip", "wrench")
# Çığ yasak kelimeleri (13 Eki, Bahadır): araç ve insan kurtarma yok, çığın kendisi ana aktör; yazı yok. Yavaşlatıcı
# kelimeler de yasak (toz çığı saatte 100+ km). "calmly/gradually/softly/peacefully" Bahadır'ın örneklerine eklendi.
_AVA_BANNED = ("rescue", "helicopter", "skier", "snowmobile", "vehicle", "truck", "car", "cargo", "tugboat", "ship",
               "boat", "siren", "text", "sign", "logo")
_AVA_SLOW = ("slowly", "gently", "calm", "calmly", "gradually", "softly", "peacefully")
# 🏚️ Deprem (14 Eki, Bahadır): _EQ_* listeleri. Nesne + fiil aranır. "wall" tek başına yok ("wall of dust" tozun
# kendisi). Yasak: ölü/yaralı/gömülme/kurtarma, araç ve gemi, ülke/şehir adı, yavaşlatıcılar.
# 14 Eki (2), Bahadır: 11:19 testinde eski sokak 3 denemede de "seçilen olay görünmüyor" kapısına takıldı; GPT'nin doğru
# ama serbest cümleleri reddedildi (simülasyon cümleleri madde metnine yakın yazılmıştı). Deprem kapısı anlam bazlı:
# her maddede NESNE (toz, kat, cephe, ev, moloz...) + EYLEM (çöker, akar, ilerler...) grupları; eş anlamlılar geniş.
# Gruplar maddeleri birbirinden ayıracak şekilde seçildi (yanlış pozitif testi: tests/test_earthquake.py).
_EQ_FALLV = ("collapse", "crumble", "cave", "cave in", "caves in", "caved in", "fall", "fell", "fallen", "topple",
             "tumble", "succumb", "fold", "give way", "gives way", "gave way", "come down", "comes down", "came down",
             "coming down", "pancake", "crash", "slam", "drop", "plunge", "implode", "buckle", "disintegrate", "crush",
             "flatten", "level", "reduce", "sink", "sank", "sag", "break apart", "breaks apart", "broke apart",
             "fall apart", "falls apart", "fell apart", "go down", "goes down", "went down", "smash", "crumple",
             "shatter", "rubble", "stack", "squash")
_EQ_MOVE = ("pour", "rush", "surge", "roll", "race", "sweep", "swept", "advance", "speed", "sped", "run", "ran", "flood",
            "cascade", "billow", "spread", "stream", "fill", "engulf", "swallow", "charge", "spill", "flow", "travel",
            "barrel", "tear through", "tears through", "tore through", "blast", "boil", "gush", "sweep through")
_EQ_DUST = ("dust", "dust cloud", "cloud", "smoke", "plume", "haze")
_EQ_UPPER = ("upper", "top", "higher", "high", "lower", "beneath", "underneath", "below them", "on top of")
_EQ_FLOORS = ("floor", "storey", "story", "level", "upper floors")
# "face" tek başına "facing" ile karışır (Q2 "facing blocks" P2 sanılıyordu)
_EQ_FRONT = ("front wall", "facade", "façade", "front", "face of", "outer wall", "exterior wall", "exterior")
_EQ_PEEL = ("peel", "tear", "tore", "torn", "rip", "strip", "shear", "slide", "slid", "come away", "comes away",
            "came away", "break away", "breaks away", "broke away", "break off", "breaks off", "broke off", "split off",
            "detach", "fall away", "falls away", "fell away", "drop away", "tear loose", "tears loose", "tore loose",
            "come loose", "comes loose", "came loose", "break loose", "breaks loose", "broke loose", "shed", "slough")
_EQ_NEXTDOOR = ("next door", "next-door", "neighbouring", "neighboring", "neighbor", "neighbour", "adjacent",
                "next to it", "alongside", "beside it", "nearby")
_EQ_OTHER = ("second", "another", "across", "opposite", "other", "far side")
_EQ_LEAN = ("lean", "tilt", "sway", "list", "keel", "tip", "tip over", "topple", "buckle", "sag", "bend", "bent", "slump",
            "slant", "pitch")
_EQ_BUILDING = ("building", "block", "apartment", "apartments", "tower", "high-rise", "mid-rise", "flats", "structure")
# "piece" yok: "in one piece" cepheyi (P2) beton parçası (P4) sandırıyordu
_EQ_SLAB = ("slab", "concrete", "chunk", "section", "panel")
_EQ_ROAD = ("road", "street", "asphalt", "pavement", "roadway", "tarmac", "lane", "alley")
_EQ_IMPACT = ("slam", "crash", "smash", "break", "broke", "crack", "split", "shatter", "hit", "punch", "gouge", "land",
              "fall", "fell", "drop", "plunge", "strike", "struck", "smack", "pierce", "tear", "rip", "crater")
_EQ_HOUSES = ("house", "home", "cottage", "dwelling", "townhouse", "bungalow")
_EQ_WALLS = ("stone wall", "walls", "masonry", "brickwork", "stonework", "brick wall")
_EQ_ROOF = ("roof", "rooftop", "tiles", "rafters")
_EQ_RUBBLE = ("rubble", "debris", "stones", "masonry", "bricks", "heap", "pile", "ruins")
_EQ_SPREAD = ("slide", "slid", "spill", "pour", "spread", "tumble", "scatter", "fan out", "fans out", "fanned out", "flow",
              "roll", "surge", "sweep", "swept", "slump", "stream", "cascade", "shift")
_EQ_CORNER = ("corner", "junction", "intersection", "crossroads", "end of the row", "end house")
_EQ_NEXTONE = ("next", "neighbouring", "neighboring", "adjacent", "another house", "following", "neighbour house",
               "one more house")
# 18 Eki (2): T7 yana çöker (T1 "sıradaki ev çöker, toz büyür" cümlesinden ayırır)
_EQ_SIDEWAYS = ("sideways", "on its side", "onto its side", "keels over", "keel over", "tips over", "tip over",
                "topples over", "topple over", "falls sideways", "leans over")
_EQ_CHAIN = ("house after house", "each house", "every house", "one after another", "one by one", "house by house",
             "building after building", "in turn", "domino", "one house after another", "each of the houses",
             # 17 Eki (yumuşak kapı düzeltmesi): 2i kuru deneme yanlış reddi ("collapse sequentially")
             "sequentially", "in sequence", "in succession", "one by one down the street")
_EQ_PROGRESS = ("down the street", "along the street", "along the row", "toward us", "towards us", "our way", "closer",
                "nearer", "advance", "progress", "race", "speed", "sped", "run", "ran", "sweep", "swept", "rush",
                "spread", "move", "march", "roll", "travel", "chase", "accelerate", "charge", "near us")
_EQ_BANNED = ("dead", "death", "bodies", "body", "victim", "injured", "injury", "blood", "trapped", "buried", "burial",
              "rescue", "rescuer", "casualty", "corpse", "killed",
              "vehicle", "truck", "car", "trailer", "ship", "boat", "cargo", "tugboat", "siren", "text", "sign", "logo",
              # ülke ve şehir adları (Bahadır: ülke adı yok)
              "turkey", "türkiye", "turkish", "syria", "syrian", "japan", "japanese", "italy", "italian", "greece",
              "greek", "iran", "iranian", "nepal", "mexico", "mexican", "chile", "haiti", "china", "chinese", "india",
              "indian", "pakistan", "afghanistan", "morocco", "ecuador", "peru", "indonesia", "philippines", "istanbul",
              "ankara", "izmir", "antakya", "hatay", "tokyo", "kobe", "rome", "athens", "tehran", "kathmandu")
_EQ_SLOW = ("slowly", "gently", "calm", "calmly", "gradually", "softly", "peacefully")
_FIRE_BURST = ("burst", "shatter", "crack", "explode", "split", "pop", "fly", "flies", "flew", "break",
               "broke")

# 17 Eki (Parti 1, madde 1 kuralı): kod yedeğinin 175 kelimeye sığmadığı çiftler hariç (beat silinmez). Ölçüm:
# tests/test_story_fallback.py (FALLBACK_GAPS_EXCLUDED).
# 18 Eki: kısa metinler ve kısa stil eki (96 kelime) ile sığmayan çift kalmadı (17 Eki: bombalar 7, şok dalgası 1)
# ☄️ Meteor (29 Eki (2), Bahadır): tek meteor, tek çarpma; sonuç zinciri şok dalgası + beyaz buhar, ardından alçak,
# geniş, BEYAZ, köpüklü taşkın. Nesne koruma kapısı (METEOR_OBJECT_GATES): GPT'nin 4-9s / 9-15s cümlesi seçilen
# maddenin İKİ ana nesnesini de taşır ("furniture scatters" gibi genelleme reddedilir). Gruplar beat terimleriyle aynı.
_MET_PALM = ("palm", "palm tree")
_MET_ROOFTILE = ("roof", "rooftop", "tile", "roof tile")
_MET_STEAM = ("steam", "spray")
_MET_CAR = ("car", "vehicle")
_MET_SUNBED = ("sunbed", "sun lounger")
_MET_POOL = ("pool", "terrace")
_MET_FLOOD = ("flood",)
_MET_PROMENADE = ("promenade", "kiosk")
_MET_SURGE = ("surge", "flood")
_MET_GARDEN = ("garden",)
_MET_WALL = ("wall",)
_MET_SURF = ("seawall", "surf")
_MET_BAR = ("bar", "beach bar", "lounger")
# 29 Eki (3), Bahadır: W2, W3, X1, X3 yeni metin; nesneler W2 buhar/sprey + araç, W3 şezlong + havuz/teras, X1 taşkın +
# promenat/büfe, X3 bahçe + duvar
METEOR_OBJECT_GATES = {"W1": (_MET_PALM, _MET_ROOFTILE), "W2": (_MET_STEAM, _MET_CAR),
                       "W3": (_MET_SUNBED, _MET_POOL), "X1": (_MET_FLOOD, _MET_PROMENADE),
                       "X2": (_MET_SURGE, _MET_CAR), "X3": (_MET_GARDEN, _MET_WALL), "X4": (_MET_SURF, _MET_BAR)}
# Tek meteor (kural 2): GPT'nin insan cümlesi, 4-9s ve 9-15s'te yasak (kod yedeği de aynı denetimden geçer)
METEOR_ONE_BANNED = ("rain", "shower", "fragment", "debris", "ember", "fireball", "meteors", "meteorite", "second",
                     "another", "streak", "chunk", "falling rock")
# Tsunami değil (kural 3): beat lint + GPT ret
METEOR_TSUNAMI_BANNED = ("tsunami", "wall of water", "towering wave", "giant wave", "tidal", "brown", "muddy",
                         "rises up", "rising wall")
# Suyun geçtiği dilimde beyaz su kelimesi zorunlu (kural 3)
METEOR_WATER = ("water", "seawater", "sea", "surge", "flood", "surf", "spray", "wave", "foam")
METEOR_WHITE = ("white", "foaming", "steaming")
# Kalıcı hasar (kural 4): her W/X maddesinde ve GPT'nin 4-9s / 9-15s cümlesinde en az biri (çekimleriyle)
METEOR_DAMAGE = ("snap", "rip", "tear", "tore", "torn", "flip", "smash", "shove", "knock over", "knocks over",
                 "knocked over", "knocking over", "crush", "topple", "break", "broke", "broken")
# Ek kural (29 Eki, Bahadır): sakin/atmosferik beat yok. Bu fiiller hiçbir meteor beat'inde (lint) ve GPT'nin yazdığı
# dilimlerde (EVENT_BANNED_WORDS) geçmez. Çekimleri find_terms ile eşleşir (billows, drifting, stood, staring...)
METEOR_STATIC = ("billow", "drift", "rolls slowly", "roll slowly", "rolling slowly", "rolled slowly", "watch", "stare",
                 "stand", "stood", "calm", "calmly", "gentle", "gently", "slowly", "gradually", "softly", "peacefully",
                 "linger", "gaze", "hover")
# Ek kural (29 Eki): her beat'te ekranda büyük temas (ev, araç, insan, ağaç). Lint her meteor beat'inde birini arar
METEOR_CONTACT = ("house", "home", "villa", "roof", "building", "garden", "terrace", "car", "vehicle", "people",
                  "person", "resident", "palm", "tree",
                  "beach bar", "kiosk")   # 29 Eki (2): plaj barı yapı (X4); 29 Eki (3): plaj büfesi (X1)
_VOLC_BOMBS_GAPS = set()
_VOLC_ERUPTION_GAPS = set()
EVENT_BEATS = {
    FLOOD: {
        "slice_2": {
            "V1": {"text": "the {vehicle} is caught by the current, turns sideways and is dragged down the street",
                   "terms": [("sideways", "sideway", "broadside", "side-on", "side on") + _SPIN, _DRAG]},
            "V2": {"text": "the {vehicle} is swept into another parked car and both are shoved along",
                   "terms": [_HIT, ("another", "second", "other", "next", "parked") ]},
            "V3": {"text": "the {vehicle} is lifted off its wheels and spun around",
                   "terms": [_LIFT, _SPIN]},
            "V4": {"text": "the {vehicle} is pushed onto the sidewalk and slams into a lamppost",
                   "terms": [("sidewalk", "pavement", "curb", "kerb", "footpath"), _POLE]},
            "V5": {"text": "the {vehicle} tips over onto its side in the current",
                   "terms": [("tip", "topple", "overturn", "flip", "roll over", "rolls over", "rolled over", "capsize",
                              "keel over", "on its side", "onto its side", "on to its side", "on its roof")]},
            "V6": {"text": "the {vehicle} is carried backwards down the street, bumping parked cars",
                   "terms": [("backward", "backwards", "in reverse", "rear-first", "rear first", "tail-first",
                              "tail first", "rear end first", "boot first", "trunk first"), _DRAG]},
            "V7": {"text": "the {vehicle} is rammed against a building wall",
                   "terms": [("wall", "building", "facade", "façade", "house", "shopfront", "storefront"), _HIT]},
            "V8": {"text": "the {vehicle} and the car behind it are dragged away together, bumper to bumper",
                   "terms": [("together", "bumper", "side by side", "in tandem", "locked", "both", "pair"), _DRAG]},
        },
        "slice_3": {
            "D2": {"text": "a lamppost topples into the current",
                   "terms": [_POLE, ("topple", "fall", "fell", "collapse", "crash", "snap", "tip", "keel over",
                                     "go down", "goes down", "went down", "bend", "buckle", "give way", "gives way")]},
            "D3": {"text": "a street tree is uprooted and carried along",
                   "terms": [("tree", "trees"), ("uproot", "rip", "tear", "tore", "torn", "topple", "fall", "fell",
                                                 "wrench", "pull", "snap", "carry", "carried", "sweep", "swept")]},
            "D4": {"text": "a dumpster tumbles down the street and smashes into a parked car",
                   "terms": [("dumpster", "skip", "trash bin", "rubbish bin", "garbage bin", "waste container",
                              "garbage container", "trash container", "container", "bin"),
                             ("tumble", "roll", "smash", "slam", "crash", "barrel", "bounce", "hurtle", "careen",
                              "ram")]},
            "D5": {"text": "a city bus is shoved sideways by the current",
                   "terms": [("bus", "buses"), ("shove", "push", "sideways", "sweep", "swept", "drag", "slide", "slid",
                                                "tilt", "lurch", "skid", "swing", "swung", "turn")]},
            "D8": {"text": "a car is lifted off the road and spins away downstream",
                   "terms": [_CAR, _LIFT, _SPIN + ("drift", "float away", "downstream")]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "D9": {"text": "the flood bursts through the ground floor of a building across the street",
                   "terms": [("building", "house", "shop", "storefront", "shopfront", "facade", "façade",
                             "ground floor", "doorway", "entrance"), ("burst", "smash", "crash", "pour", "flood",
                             "break", "broke", "sweep", "swept", "surge", "rush", "cave", "give way", "gives way")]},
        },
        # Aynı videoda tekrar/çelişki (Bahadır onayı, 3 Eki)
        # 17 Eki (temizlik turu): D1, D6, D7 çıktı; (V7,D6) (V6,D1) (V8,D1) çiftleri ve D7'nin görünüm/nokta kısıtı
        # onlarla gitti (önceki: "excluded_views": {"D7": {"gulf_metropolis"}}, "excluded_spots": {"D7": {"High-rise
        # city district"}})
        # 18 Eki (2): D9 binanın zemin katı, V7 bina duvarı (aynı yapı)
        "excluded_pairs": {("V3", "D8"), ("V4", "D2"), ("V7", "D9")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    # 4 Eki, Bahadır onayı (havuzlar ve yasak eşleşmeler).
    TIDAL: {
        "slice_2": {
            "T1": {"text": "the {vehicle} is lifted and flung against a storefront",
                   "terms": [_LIFT + _FLING, _SHOP]},
            # 4 Eki, Bahadır: araç havalanmaz, su taşır (eski: "is lifted and carried down the street on top of
            # the surge")
            "T2": {"text": "the {vehicle} is carried down the street by the surge",
                   "terms": [("carry", "carried", "sweep", "swept", "drag", "dragged", "push", "pushed", "wash",
                              "washed"), ("down the street", "along the street", "down the road")]},
            "T3": {"text": "the {vehicle} is slammed into the car parked ahead and both are shoved along",
                   "terms": [_HIT, ("ahead", "in front", "another", "second", "other", "next", "parked")]},
            "T4": {"text": "the {vehicle} is spun sideways and dragged along the street",
                   "terms": [_SIDEWAYS + _SPIN, _DRAG]},
            "T5": {"text": "the {vehicle} tips over onto its side in the churning water",
                   "terms": [_TIP]},
            "T6": {"text": "the {vehicle} is pushed onto the sidewalk and slams into a lamppost",
                   "terms": [_CURB, _POLE]},
            # 4 Eki, Bahadır: "thrust" (kuru provada "thrust backward" reddedildi); _DRAG selle ortak, ona eklenmez
            "T7": {"text": "the {vehicle} is carried backwards down the street, bumping parked cars",
                   "terms": [_BACKWARD, _DRAG + ("thrust",)]},
            "T8": {"text": "the {vehicle} and the car behind it are dragged away together, bumper to bumper",
                   "terms": [_TOGETHER, _DRAG]},
        },
        "slice_3": {
            "W1": {"text": "a row of parked vehicles is ripped loose one by one and washed away",
                   "terms": [_ROW, _CAR, _RIP_AWAY]},
            "W2": {"text": "a lamppost topples into the surge",
                   "terms": [_POLE, _FALL]},
            "W3": {"text": "a street tree is uprooted and carried along",
                   "terms": [("tree", "trees"), ("uproot", "rip", "tear", "tore", "torn", "topple", "fall", "fell",
                                                 "wrench", "pull", "snap", "carry", "carried", "sweep", "swept",
                                                 "wash")]},
            "W4": {"text": "a roadside kiosk is torn off its base and swept away",
                   "terms": [("kiosk", "booth", "newsstand", "news stand", "snack bar", "hut", "shack"),
                             ("tear", "tore", "torn", "rip", "wrench", "sweep", "swept", "carry", "carried", "wash",
                              "pull", "snap", "break", "broke", "topple", "lift", "uproot")]},
            "W5": {"text": "a city bus is shoved sideways by the surge",
                   "terms": [("bus", "buses"), ("shove", "push", "sideways", "sweep", "swept", "drag", "slide", "slid",
                                                "tilt", "lurch", "skid", "swing", "swung", "turn")]},
            "W6": {"text": "a low wall collapses into the water",
                   "terms": [("wall", "walls"), ("collapse", "crumble", "topple", "fall", "fell", "give way",
                                                 "gives way", "gave way", "burst", "break", "broke", "cave",
                                                 "tumble", "burst apart")]},
            "W8": {"text": "a dumpster tumbles down the street and smashes into a parked car",
                   "terms": [("dumpster", "skip", "trash bin", "rubbish bin", "garbage bin", "waste container",
                              "garbage container", "trash container", "container", "bin"),
                             ("tumble", "roll", "smash", "slam", "crash", "barrel", "bounce", "hurtle", "careen",
                              "ram")]},
        },
        "excluded_pairs": {("T6", "W2"), ("T2", "W1"), ("T8", "W1"), ("T3", "W8")},   # 17 Eki: (T1,W7) W7 ile gitti
        "excluded_views": {},
        # Kamera seawall'un üstünde duruyor: "alçak duvar çöker" olayı kameranın durduğu duvar gibi çizilir
        "excluded_spots": {"W6": {"Coastal avenue behind a seawall"}},
    },
    # ── Heyelan (TASLAK, 4 Eki, Bahadır hazırlığı; onay bekliyor) ──
    MUDSLIDE: {
        "slice_2": {
            "H1": {"text": "the {vehicle} is shoved sideways by the mud and slams into the car parked beside it",
                   "terms": [_SIDEWAYS, _HIT, _NEIGHBOR]},
            # 22 Eki, Bahadır (heyelan denetimi, zayıf beat'ler): H2, H4, H6, M3, M6; R2, R4, R6, S4; K3, L5, L6 metni
            # değişti, kodlar aynı. Önceki H2: "the {vehicle} is pushed down the street by the mud, bumping parked cars"
            "H2": {"text": "the mud swings the {vehicle} sideways and drags it down the steep street",
                   "terms": [_SIDEWAYS + _SPIN, _DRAG + _DOWNHILL]},
            "H3": {"text": "the {vehicle} is spun around by the mud and dragged downhill",
                   "terms": [_SPIN, _DRAG + _DOWNHILL]},
            # Önceki: "the {vehicle} is buried to its windows and pushed against a house wall"
            "H4": {"text": "the mud shoves the {vehicle} across the street and crushes it against the parked cars on "
                           "the other side",
                   "terms": [_HIT + ("crush",), _NEIGHBOR]},
            "H5": {"text": "the {vehicle} tips over onto its side in the mud",
                   "terms": [_TIP]},
            # Önceki: "the {vehicle} and the car behind it are pushed down the street together, bumper to bumper"
            "H6": {"text": "the mud pushes the {vehicle} nose-first into the front steps of a house lining the street "
                           "and buries its front half",
                   "terms": [_HOUSE + _STEPS, _HIT + _BURY]},
        },
        "slice_3": {
            # 22 Eki: önceki "a garden wall along the street collapses and its stones tumble downhill" (21 Eki: "a
            # low garden wall collapses and its stones tumble down the street"). Açılış B ile seçilmez (opening_axis).
            "M3": {"text": "the mud shoves the row of parked cars along the curb downhill, one car after another",
                   "terms": [_CAR, _ROW, _DRAG]},
            # Önceki: "a tree is torn out of the slope and carried down with the mud" (yamaç kadrajda tanımlı değil)
            "M4": {"text": "a tree along the street is torn out and swept downhill",
                   "terms": [("tree", "trees"), _UPROOT]},
            # Önceki: "the mud rams a house corner and tears off its wooden porch" (21 Eki 17:39 testi H2+M6: 12. sn'de
            # kamera tanımsız "ev köşesi"ne döndü, gizli kesme)
            # 22 Eki: önceki "the mud rams the nearest house and tears off its wooden porch"
            "M6": {"text": "the mud rams the nearest house lining the street and buries its ground floor up to the "
                           "windows",
                   "terms": [_HOUSE + ("ground floor",), _HIT + _BURY + ("up to the windows", "to the windows")]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "M7": {"text": "mud slams into a house across the street and bursts through its ground floor",
                   "terms": [_HOUSE + ("ground floor",), ("burst", "smash", "crash", "slam", "break", "broke",
                             "ram", "plow", "plough", "tear", "tore", "pour", "flood", "sweep", "swept")]},
            # Önceki: "the mud shoves a large truck sideways into the front of a house"
            "M8": {"text": "the mud shoves a parked truck sideways into a house on the street",
                   "terms": [_CAR, _SIDEWAYS + _DRAG, _HOUSE + ("front of a house", "front of the house")]},
            "M9": {"text": "a mass of mud and uprooted trees crashes onto the houses across the street",
                   "terms": [("tree", "trees", "trunk", "trunks"), _HOUSE, ("crash", "slam", "smash", "hit",
                             "bury", "buried", "engulf", "sweep", "swept", "pile", "pour")]},
        },
        # 18 Eki (2): M1 çıktı; ev duvarı/ön cephe iki kez (H4: M7, M8, M9), araç yana itilir (H1: M8)
        # 22 Eki: H4 artık ev değil, park hâlindeki arabalar (H4-ev çiftleri çıktı; H4+M3 park arabaları itilir). Ev iki
        # kez kuralı yeni H6'ya geçti (araç evin ön basamaklarına gömülür: M6 eve gömülür, M7, M8 eve itilir, M9)
        # 22 Eki: H4+M6 175 bütçesi (açılış B ile kod yedeği sığmıyor; metinler onaylı, kısaltılmadı)
        "excluded_pairs": {("H4", "M3"), ("H6", "M6"), ("H6", "M7"), ("H6", "M8"), ("H6", "M9"), ("H1", "M8"),
                           ("H4", "M6")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    SLOPE: {
        "slice_2": {
            "R1": {"text": "the {vehicle} is shoved sideways across the road by the mud and rocks",
                   "terms": [_SIDEWAYS + ("across the road", "across both lanes"), _DRAG]},
            # 22 Eki (heyelan denetimi): önceki "the {vehicle} is pushed against the guardrail and pinned there"
            # 22 Eki (2): kısaldı (bütçe dışlamaları kalksın). Önceki: "the mud shoves the {vehicle} across both lanes
            # and slams it into the rock face on the far side of the road"
            "R2": {"text": "the mud shoves the {vehicle} across the road into the rock face",
                   "terms": [_HIT, _ROCK_FACE]},
            "R3": {"text": "a rolling boulder strikes the {vehicle}, which spins and slides down the road",
                   "terms": [_ROCK, _SPIN + ("slide", "slid", "skid")]},
            # Önceki: "the {vehicle} is buried to its windows in the mud and pushed toward the road edge"
            "R4": {"text": "a wave of mud and rocks hits the front of the {vehicle} and shoves it backwards down the "
                           "road",
                   "terms": [_BACKWARD, _DRAG + _HIT]},
            "R5": {"text": "the {vehicle} tips over onto its side in the mud",
                   "terms": [_TIP]},
            # Önceki: "the {vehicle} and the car behind it are shoved along the road together"
            "R6": {"text": "the mud spins the {vehicle} around and drags it backwards along the road toward the slope",
                   "terms": [_SPIN, _DRAG + _BACKWARD]},
        },
        "slice_3": {
            # 21 Eki (genel kalite): kadraj dışı hedef. Önceki: "...smashes into a parked car" (dağ yolunda park yeri
            # tanımlı değil)
            "S2": {"text": "a large boulder rolls across the road and smashes into a stopped car",
                   "terms": [_ROCK, ("roll", "tumble", "bounce", "crash", "smash", "slam", "hurtle", "careen",
                                     "barrel", "ram", "hit", "strike", "struck"), _CAR]},
            "S3": {"text": "a tree is torn out of the slope and slides across the road",
                   "terms": [("tree", "trees"), _UPROOT + ("slide", "slid")]},
            # 22 Eki: önceki "a utility pole snaps and falls across the road" (ince hedef, kadrajda tanımlı değil)
            "S4": {"text": "a huge slab of rock breaks off the slope and crashes onto the road in front of the stopped "
                           "cars",
                   "terms": [("slab", "rock", "chunk", "block of rock", "rock face", "cliff"),
                             ("break off", "breaks off", "broke off", "crash", "slam", "smash", "fall", "fell", "drop",
                              "plunge", "land", "tumble", "topple", "collapse", "split", "shear off", "shears off")]},
            "S5": {"text": "more of the slope gives way and a second surge of mud and rocks pours onto the road",
                   "terms": [("more", "second", "another", "again", "fresh", "new", "further"),
                             ("slope", "hillside", "mud", "rock", "rocks", "landslide", "torrent", "surge"),
                             ("give way", "gives way", "gave way", "collapse", "pour", "surge", "slide", "slid",
                              "crash", "tumble", "break", "broke", "burst")]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            # Önceki: "the mud and boulders shove a large truck sideways toward the edge of the road"
            "S7": {"text": "the mud and boulders shove a stopped truck sideways toward the edge of the road",
                   "terms": [_CAR, _SIDEWAYS + _DRAG, ("edge", "shoulder", "verge", "side of the road", "roadside",
                             "drop-off", "drop off")]},
        },
        # 17 Eki (temizlik turu): S1 (korkuluk) ve S6 (sıralı araçlar) çıktı; (R2,S1) (R6,S6) ve S1'in nokta kısıtı
        # onlarla gitti (önceki: {"S1": {"Behind the guardrail of a hillside road"}})
        # 18 Eki (2): S7 kamyon yana/yol kenarına itilir (R1 yana itilir, R4 yol kenarına itilir)
        # 22 Eki: R2 araç iki şeridi geçip itilir (S7 gibi); R4 artık geriye itilir (yine araç itilir, çift kalır)
        # 22 Eki (2): R2 kısaldı (12 kelime), bütçe için konan R2+S4, R2+S5 dışlamaları kalktı
        "excluded_pairs": {("R3", "S2"), ("R1", "S7"), ("R4", "S7"), ("R2", "S7")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    VILLAGE: {
        "slice_2": {
            "K1": {"text": "the {vehicle} is swept down the lane and rammed against a house wall",
                   "terms": [_DRAG, _HIT, _HOUSE]},
            "K2": {"text": "the {vehicle} is spun around by the torrent and dragged along the lane",
                   "terms": [_SPIN, _DRAG]},
            # 22 Eki (heyelan denetimi): önceki "the {vehicle} is buried to its windows and pushed against a fence"
            "K3": {"text": "the torrent shoves the {vehicle} down the lane and wedges it between two houses",
                   "terms": [_DRAG, _HIT + ("between",), _HOUSE]},
            "K4": {"text": "the {vehicle} tips over onto its side in the torrent",
                   "terms": [_TIP]},
            "K5": {"text": "the {vehicle} slams into a pile of logs and both are carried away",
                   "terms": [_LOGS, _DRAG]},
            "K6": {"text": "the {vehicle} is shoved into a parked motorbike and both are carried along",
                   "terms": [("motorbike", "motorcycle", "moped", "scooter", "bike"), _DRAG]},
        },
        "slice_3": {
            # 21 Eki (genel kalite): kadraj dışı hedef. Önceki: "a wooden house corner is struck and its wall collapses"
            "L1": {"text": "a wooden house along the lane is struck and its wall collapses",
                   "terms": [("house", "home", "cottage", "cabin", "building"), _COLLAPSE]},
            "L3": {"text": "a large tree is uprooted and rolls down with the torrent",
                   "terms": [("tree", "trees"), _UPROOT + ("roll", "tumble")]},
            # Önceki: "a roof section is torn off a shed and swept away" (kulübe kadrajda tanımlı değil)
            "L4": {"text": "a roof section is torn off a house along the lane and swept away",
                   "terms": [("roof", "roofing", "rooftop"), _TEAR]},
            # 22 Eki: önceki "a pile of logs breaks loose and rolls down the lane" (K5 kütük tekrarı)
            "L5": {"text": "the torrent smashes through the front wall of a wooden house along the lane",
                   "terms": [_HOUSE, ("smash", "burst", "crash", "break", "broke", "tear", "tore", "rip", "ram", "slam",
                                      "plow", "plough", "punch", "cave", "collapse")]},
            # 22 Eki: önceki "a stone wall along the lane collapses and its stones tumble into the torrent" (21 Eki: "a
            # stone wall collapses and its stones tumble into the torrent")
            "L6": {"text": "the torrent shoves a parked car along the lane into the front of a house",
                   "terms": [_CAR, _DRAG, _HOUSE]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "L7": {"text": "the landslide rips a wooden house off its foundation and carries it down the slope",
                   "terms": [("house", "home", "cottage", "cabin", "building"), _TEAR + ("foundation", "rip off",
                             "sweep away")]},
        },
        # 17 Eki: (K3,L2) L2 ile gitti. 18 Eki (2): L7 ev temelinden kopar, K1 ev duvarı (aynı yapı)
        # 22 Eki: (K5,L5) çıktı (L5 artık kütük değil); L5 ev ön duvarı (K1 ev duvarı), L6 araç itilir (K3 araç itilir)
        "excluded_pairs": {("K1", "L1"), ("K1", "L5"), ("K1", "L6"), ("K1", "L7"), ("K3", "L6")},
        "excluded_views": {},
        # Kamera bir köy evinin üst kat balkonunda: "ev köşesi vurulur, duvarı çöker" kameranın durduğu ev gibi çizilir
        "excluded_spots": {"L1": {"Upper-floor balcony of a village house"},
                           "L7": {"Upper-floor balcony of a village house"}},   # 18 Eki: kameranın evi olabilir
    },
    # ── Hortum (TASLAK, 4 Eki, Bahadır hazırlığı; onay bekliyor) ──
    LANDFALL: {
        "slice_2": {
            # 23 Eki, Bahadır (hortum denetimi): C1, C2, E1, E2 metni değişti, kodlar aynı (sebep ekranda: hortum).
            # Önceki C1 "the {vehicle} is shoved sideways across the street by the wind", C2 "the {vehicle} tips over
            # onto its side as roof tiles rain down around it"
            "C1": {"text": "the tornado shoves the {vehicle} sideways across the street and slams it into the far curb",
                   "terms": [_SIDEWAYS, _DRAG + _BLOW]},
            "C2": {"text": "the tornado tips the {vehicle} over onto its side in the middle of the street",
                   "terms": [_TIP]},
            "C4": {"text": "the {vehicle} slides along the street and slams into a parked car",
                   "terms": [_DRAG + ("skid",), _HIT, ("parked", "another", "second", "other", "next",
                                                        "stationary")]},
            # 4 Eki, Bahadır onayı: uçma güncellemesi (eski C5 "a fallen tree branch crashes onto the roof of the
            # {vehicle}", eski C6 "the {vehicle} is pushed onto the sidewalk against a shop front")
            "C5": {"text": "the {vehicle} is lifted off the road and flung down the street",
                   "terms": [_LIFT_AIR, _FLING + ("hurtle", "tumble", "slam", "crash")]},
        },
        "slice_3": {
            # Önceki E1 "the tornado tears the roof off a house and scatters the pieces across the street" (şehir
            # merkezinde ev yok), E2 "the tornado rips a billboard frame from its supports and throws it aside" (ince)
            "E1": {"text": "the tornado tears the roof off a waterfront building and scatters the pieces across the "
                           "street",
                   "terms": [("roof", "roofs", "roofing"), _TEAR + ("scatter", "peel", "strip", "rip off")]},
            "E2": {"text": "the tornado tears the roof off a waterfront restaurant and flings it across the road",
                   "terms": [("roof", "roofs", "roofing"), _TEAR + _FLING + ("rip off",)]},
            "E4": {"text": "the tornado uproots a large tree and flings it through the air",
                   "terms": [("tree", "trees"), _UPROOT + _FLING]},
            "E5": {"text": "the tornado rips the front off a small shop, sending shutters and signs flying",
                   "terms": [("shop", "store", "storefront", "shopfront", "shop front", "shutter", "shutters"),
                             _TEAR + _AIRBORNE + _FLING + ("shear",)]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "E7": {"text": "the tornado shreds the top floor of a building across the street, debris spiraling up",
                   "terms": [("floor", "storey", "story", "top floor", "building", "upper floor"),
                             _TORNADO_RIP + ("shred", "spiral", "rip apart")]},   # "tear apart" sadece marina Z6
        },
        # 4 Eki: C5/C6 uçma maddesi oldu, ağaç (C5/E4) ve dükkân önü (C6/E5) artık ortak nesne değil, o iki çift kalktı.
        # 18 Eki (2): E7 bina üst katı, 4-9s'de bina yok. 23 Eki: (C2, E1) çatı iki kez çıktı (C2'de kiremit yok); E1 ve
        # E2 (ikisi de çatı) aynı dilimde, birlikte seçilmez
        "excluded_pairs": set(),
        "excluded_views": {},
        # 23 Eki: E1'in kıyı mahallesi dışlaması çıktı (önceki "a house" kameranın durduğu verandalı ev gibi
        # çiziliyordu; şimdi "a waterfront building")
        "excluded_spots": {},
    },
    MARINA_TORNADO: {
        # 4 Eki, Bahadır: marina yeniden tasarımı. Y1/Y3 yeni metin; Z1-Z6 tamamen yeni (direk ve yat sahneleri çıktı)
        "slice_2": {
            # 23 Eki, Bahadır (hortum denetimi): Y1, Y3, Y5; Z1, Z2, Z3, Z6, Z7 metni değişti, kodlar aynı. Önceki Y1
            # "the {vehicle} is hit by flying debris and slides sideways across the quay" (sebep küçük döküntü)
            "Y1": {"text": "the tornado shoves the {vehicle} sideways across the quay toward the water's edge",
                   "terms": [_SIDEWAYS, _DRAG + _BLOW + ("hurl", "force")]},
            "Y2": {"text": "the {vehicle} tips over onto its side on the quay road",
                   "terms": [_TIP]},
            # Önceki Y3 "...slams into a lamppost" (ince), Y5 "...flung into a stack of dock boxes" (küçük, açık renk)
            "Y3": {"text": "the {vehicle} slides along the quay and slams into the front of the marina office",
                   "terms": [_DRAG + _BLOW + ("hurl", "force", "skid"), _HIT, _MARINA_OFFICE]},
            "Y5": {"text": "the {vehicle} is lifted off the quay road and flung over the edge into the marina water",
                   "terms": [_LIFT_AIR, _FLING + ("slam", "smash", "crash", "hurtle", "plunge", "drop", "fall", "fell"),
                             _MARINA_WATER]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "Y7": {"text": "the tornado rips the roof off the café across the quay and hurls it away",
                   "terms": [("roof", "roofing"), ("café", "cafe", "bar", "restaurant", "building"), _TORNADO_RIP]},
            "Y8": {"text": "the tornado smashes into the quayside building and its front wall bursts outward",
                   "terms": [("building", "front wall", "wall", "facade", "façade", "shopfront", "storefront"),
                             ("smash", "burst", "blow out", "blows out", "explode", "shatter", "collapse", "tear",
                             "tore", "rip", "cave")]},
        },
        "slice_3": {
            # Önceki Z1 "the tornado tears the awning off the harbor café and flings it across the quay" (ince), Z2
            # "the tornado rips the front off a small kiosk, sending its shutters and signs flying" (küçük), Z3 "a wall
            # of dust and debris rolls across the quay and engulfs the café terrace" (temas yok)
            "Z1": {"text": "the tornado rips the whole roof off the harbor café and flings it across the quay",
                   "terms": [("roof", "roofing"), ("café", "cafe", "bar", "restaurant", "building"), _TORNADO_RIP]},
            "Z2": {"text": "the tornado rips the front off the marina office, sending its shutters and furniture across "
                           "the quay",
                   "terms": [_MARINA_OFFICE + ("shutter", "shutters"), _TORNADO_RIP]},
            "Z3": {"text": "the tornado tears through the café terrace and hurls its heavy tables and chairs into the "
                           "marina water",
                   "terms": [("table", "tables", "chair", "chairs", "furniture"),
                             _TORNADO_RIP + ("tear through", "tears through", "tore through", "tearing through"),
                             _MARINA_WATER]},
            "Z4": {"text": "the tornado rips the roof off the marina office and scatters the pieces across the quay",
                   "terms": [("roof", "roofing"), ("office", "building", "hut", "cabin", "clubhouse", "shed",
                                                   "kiosk"), _TORNADO_RIP]},
            # Önceki Z6 "the tornado shatters the glass front of a quayside shop and hurls tables and chairs into the
            # street" (cam); Z7 "the tornado lifts the whole café terrace off the quay and scatters it across the road"
            # (teras zemin, kalkmaz)
            "Z6": {"text": "the tornado bursts through the front of a quayside shop and hurls its contents across the "
                           "quay",
                   "terms": [("shop", "store", "shopfront", "storefront", "shop front", "boutique"),
                             ("hurl", "fling", "flung", "throw", "threw", "thrown", "tear through", "tears through",
                              "tore through", "rip", "tear", "tore",
                              "shatter", "smash", "burst", "break", "broke", "explode", "blow out", "blew out",
                              "annihilate", "splinter",   # 4 Eki, Bahadır: kuru provada reddediliyordu
                              # 4 Eki, Bahadır: "obliterates" reddediliyordu. Çok kelimeli terimlerde çekim sadece
                              # son kelimeye uygulandığı için "tears/tore/torn apart" vb. ayrıca yazıldı
                              "obliterate", "demolish", "wreck", "wreak", "rupture", "pulverize",
                              "tear apart", "tears apart", "tore apart", "torn apart", "tearing apart",
                              "blow apart", "blows apart", "blew apart", "blown apart", "blowing apart")]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "Z7": {"text": "the tornado lifts the café's heavy dark wooden pergola off the terrace and smashes it across "
                           "the road",
                   "terms": [("pergola", "gazebo", "wooden frame", "wooden canopy", "canopy", "beams"),
                             _TORNADO_RIP + ("lift", "scatter", "fling", "hurl", "smash", "crash", "slam")]},
        },
        # Aynı nesne iki kez: kutu (Y5/Z5), sandık (Y4/Z5)
        # 17 Eki: Y4 ve Z5 çıktı. 18 Eki (2): çatı iki kez (Y7: Z4), kafe iki kez (Y7: Z1, Z3, Z7), rıhtım binası cephesi
        # iki kez (Y8: Z2, Z6)
        # 23 Eki: Y7/Y8 çiftleri yeni metinlerde de geçerli (Y7 kafe çatısı: Z1 kafe çatısı, Z3 kafe terası, Z4 çatı,
        # Z7 kafe pergolası; Y8 rıhtım binası cephesi: Z2 ofis cephesi, Z6 dükkân cephesi). Yeni: marina ofisi iki kez
        # (Y3: Z2, Z4)
        # 29 Eki (4), Bahadır: marina suyuna fırlatma iki kez (Y5 araç: Z3 masalar)
        "excluded_pairs": {("Y7", "Z4"), ("Y7", "Z1"), ("Y7", "Z3"), ("Y7", "Z7"), ("Y8", "Z2"), ("Y8", "Z6"),
                           ("Y3", "Z4"), ("Y3", "Z2"), ("Y5", "Z3")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    AVENUE: {
        "slice_2": {
            "P1": {"text": "the {vehicle} is shoved sideways across the avenue by the wind",
                   "terms": [_SIDEWAYS, _DRAG + _BLOW]},
            "P2": {"text": "the {vehicle} tips over onto its side",
                   "terms": [_TIP]},
            # 4 Eki, Bahadır: cadde test videosunda sorun çıktı; palmiye artık araca çarpar (eski: "a palm tree
            # crashes onto the road in front of the {vehicle}"; "narrowly/missing" kaldırıldı)
            "P4": {"text": "a falling palm tree crashes onto the {vehicle}, crushing its roof",
                   "terms": [("palm", "palms", "palm tree", "tree", "trunk"),
                             ("crash", "fall", "fell", "topple", "slam", "smash", "drop", "come down", "comes down",
                              "came down", "collapse"), ("roof", "rooftop", "crush", "crumple", "cave", "flatten",
                                                         "dent")]},
            # 4 Eki, Bahadır onayı: uçma güncellemesi (eski P5 "slides into a bus shelter, shattering its glass",
            # eski P6 "and the car behind it are pushed along the avenue together")
            "P5": {"text": "the {vehicle} is lifted off the avenue and flung into a bus shelter, shattering its glass",
                   "terms": [_LIFT_AIR, _FLING + ("slam", "smash", "crash", "hurtle"), _SHELTER]},
            "P6": {"text": "the {vehicle} is swept up into the air, spins, and crashes down across the avenue",
                   "terms": [_LIFT_AIR, _SPIN, _CRASH_DOWN]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "P7": {"text": "the tornado flings a large truck across the avenue into the front of a building",
                   "terms": [_CAR, _FLING + _DRAG + ("slam", "smash", "crash"), ("building", "front", "facade",
                             "façade", "storefront", "shopfront", "wall")]},
        },
        "slice_3": {
            "Q1": {"text": "the tornado rips a row of palm trees out of the ground and flings them across the avenue",
                   "terms": [("palm", "palms", "palm tree", "tree", "trees"), _UPROOT + _FLING]},
            "Q2": {"text": "the tornado tears a billboard from its frame and sends it spinning away",
                   "terms": [_SIGN, _TEAR + _FLING + _SPIN]},
            "Q3": {"text": "the tornado hurls a cloud of signs, branches and bins along the avenue",
                   "terms": [("sign", "signs", "branch", "branches", "bin", "bins", "trash can", "debris"),
                             _FLING + _DRAG + _AIRBORNE]},
            "Q4": {"text": "the tornado tears the roof off a bus shelter and throws it aside",
                   "terms": [_SHELTER, ("roof", "canopy", "top", "panel", "panels"), _TEAR + _FLING]},
            "Q6": {"text": "the tornado rips the awnings off a row of shops and flings them high",
                   "terms": [("awning", "awnings", "canopy", "canopies", "shade", "blind", "blinds"),
                             _TEAR + _FLING + _AIRBORNE]},
        },
        # Aynı nesne iki kez: lamba (P3/Q5), otobüs durağı (P5/Q4), palmiye (P4/Q1)
        "excluded_pairs": {("P5", "Q4"), ("P4", "Q1")},   # 17 Eki: (P3,Q5) P3 ve Q5 ile gitti
        "excluded_views": {},
        # 10 Eki, Bahadır: kamera yüksek balkonda, Q5 dışlaması kalktı (eski: kamera kaldırımdaydı, "sokak
        # lambaları devrilir" kameranın durduğu kaldırıma düşüyordu: {"Q5": {"Downtown city center",
        # "High-rise coastal city"}})
        "excluded_spots": {},
    },
    # ── Yangın (TASLAK, 8 Eki, Bahadır): metinler ve yasak eşleşmeler Bahadır'ın, terim grupları yangına özel ──
    WILDFIRE: {
        "slice_2": {
            "K1": {"text": "the {vehicle} reverses hard down the road as a burning tree crashes across the lane in front "
                           "of it",
                   "terms": [_FIRE_REVERSE, _FIRE_FLAME, _FIRE_TREE, _FIRE_FALL]},
            "K2": {"text": "the {vehicle} skids to a stop as flames leap across the road and lick its hood",
                   "terms": [_FIRE_STOP, _FIRE_FLAME, _FIRE_TOUCH, _FIRE_FRONT]},
            "K5": {"text": "the {vehicle} U-turns in a cloud of smoke and speeds away as the flames close the road "
                           "behind it",
                   "terms": [_FIRE_UTURN, _FIRE_FLAME, _FIRE_CLOSE]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "K7": {"text": "a wall of flames races up the slope and engulfs the first houses across the street",
                   "terms": [_FIRE_FLAME, _FIRE_HOUSE, _FIRE_IGNITE + _FIRE_LEAP + ("hit", "slam", "sweep",
                             "swept", "consume")]},
            "K8": {"text": "the flames leap across the street and ignite the roof of a house",
                   "terms": [_FIRE_FLAME, _FIRE_ROOF, _FIRE_IGNITE + _FIRE_LEAP]},
            "K9": {"text": "the {vehicle} speeds down the road past burning houses as flames lick the asphalt",
                   "terms": [_FIRE_SPEED, _FIRE_FLAME, _FIRE_PATH + ("asphalt",)]},
        },
        "slice_3": {
            "L1": {"text": "the flames leap onto the roofs of the nearest houses and ignite them one after another",
                   "terms": [_FIRE_FLAME, _FIRE_HOUSE, _FIRE_IGNITE]},
            "L3": {"text": "the fire races across a garden, engulfing a parked trailer and a woodpile",
                   "terms": [_FIRE_FLAME, _FIRE_FUEL, _FIRE_IGNITE]},
            "L4": {"text": "the wall of flames swallows a row of trees along the road, sending sparks high into the air",
                   "terms": [_FIRE_FLAME, _FIRE_TREE, _FIRE_IGNITE]},
            "L5": {"text": "a house roof catches fire and its tiles burst apart in the heat",
                   "terms": [_FIRE_ROOF, _FIRE_IGNITE, _FIRE_TILE, _FIRE_BURST]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "L7": {"text": "a house across the street is engulfed and its roof collapses in a burst of flames",
                   "terms": [_FIRE_HOUSE, _FIRE_FLAME + _FIRE_IGNITE, _FIRE_FALL + ("cave", "cave in", "caves in",
                             "fall in", "give way", "gives way", "engulf")]},
        },
        # 17 Eki: (K3,L2) (K6,L2) L2 ile gitti. 18 Eki (2): evler/çatı iki kez (K7, K8: L1, L5, L7)
        "excluded_pairs": {("K1", "L4"), ("K7", "L1"), ("K7", "L5"), ("K7", "L7"), ("K8", "L1"), ("K8", "L5"),
                           ("K8", "L7")},
        "excluded_views": {},
        # Kamera bir yamaç evinin balkonunda (Bahadır onayı, 8 Eki): ev çatısını yakan maddeler o noktada seçilmez
        "excluded_spots": {"L1": {"Balcony of a hillside house"}, "L5": {"Balcony of a hillside house"}},
    },
    FACADE_FIRE: {
        "slice_2": {
            "M6": {"text": "flaming debris smashes the windshield of the {vehicle} as it brakes hard",
                   "terms": [_FIRE_FLAME, _FIRE_DEBRIS, _FIRE_GLASS, _FIRE_STOP]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "M7": {"text": "burning cladding panels peel off the facade beside the balcony and fall in flames",
                   "terms": [_FIRE_FLAME, _FIRE_PANEL, _FIRE_PEEL + _FIRE_FALL]},
            "M8": {"text": "flames race up the facade, panel after panel igniting right beside the balcony",
                   "terms": [_FIRE_FLAME, _FIRE_PANEL + _FIRE_TOWER, _FIRE_IGNITE + _FIRE_LEAP]},
            "M9": {"text": "a huge sheet of burning facade tears loose and crashes down the tower",
                   "terms": [_FIRE_FLAME, _FIRE_PANEL + ("facade", "façade"), _FIRE_PEEL + _FIRE_FALL]},
            "M10": {"text": "thick fire pours out of the windows of the floor below the balcony",
                    "terms": [_FIRE_FLAME, _FIRE_GLASS + _FIRE_FLOOR, _FIRE_POUR]},
            "M11": {"text": "the flames leap up the facade to the balconies above in a roaring wall",
                    "terms": [_FIRE_FLAME, _FIRE_BALCONY + _FIRE_TOWER, _FIRE_LEAP + _FIRE_POUR]},
        },
        "slice_3": {
            "N1": {"text": "the flames climb floor after floor, blowing out window after window",
                   "terms": [_FIRE_FLAME, _FIRE_FLOOR, _FIRE_GLASS, _FIRE_BLOWOUT]},
            "N3": {"text": "burning panels peel off the facade and tumble down in a trail of sparks",
                   "terms": [_FIRE_FLAME, _FIRE_PANEL, _FIRE_PEEL]},
            "N4": {"text": "a wall of smoke and fire pours out of the upper floors and rolls up the tower",
                   "terms": [_FIRE_SMOKE, _FIRE_FLAME, _FIRE_POUR, _FIRE_TOWER]},
            "N5": {"text": "a row of windows explodes outward, spraying glass and flames over the street",
                   "terms": [_FIRE_GLASS, _FIRE_BLOWOUT, _FIRE_FLAME]},
        },
        # 17 Eki: (M5,N2) N2 ile gitti. 18 Eki (2): M1-M5 çıktı; panel/cephe parçası iki kez (M7, M9: N3), pencereden
        # ateş/kat kat tırmanma iki kez (M8, M10, M11: N1; M10: N4, N5)
        "excluded_pairs": {("M7", "N3"), ("M9", "N3"), ("M8", "N1"), ("M10", "N1"), ("M11", "N1"), ("M10", "N4"),
                           ("M10", "N5")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    FIRE_TORNADO: {
        "slice_2": {
            # 15 Eki (2), Bahadır: her maddede hortumun büyüklüğü; cam/çit/tabela/ince hedef yok (T2, T4, T5, U3, U5 yeni)
            "T1": {"text": "the towering fire tornado lifts the {vehicle} off the road and flings it into a burning "
                           "tree",
                   "terms": [_FIRE_TOR_VEH, _FIRE_TOR_LIFT, _FIRE_TOR_HURL, _FIRE_TOR_TREE, _FIRE_FLAME]},
            "T2": {"text": "the huge fire tornado hurls a whole burning tree trunk onto the {vehicle}, crushing its roof",
                   "terms": [_FIRE_TOR_VEH, _FIRE_FLAME, _FIRE_TOR_TRUNK, _FIRE_TOR_CRUSH]},
            "T4": {"text": "the {vehicle} is shoved sideways as the huge base of the fire tornado sweeps past right "
                           "behind it",
                   "terms": [_FIRE_TOR_VEH, _FIRE_TOR_SKID, _FIRE_TOR_PASS]},
            "T5": {"text": "the huge fire tornado rolls the {vehicle} over onto its roof and it bursts into flames",
                   "terms": [_FIRE_TOR_VEH, _FIRE_TOR_FLIP, _FIRE_TOR_IGNITE]},
            "T6": {"text": "huge flaming debris flung by the towering tornado slams into the {vehicle}, which spins "
                           "and stops across the road",
                   "terms": [_FIRE_TOR_VEH, _FIRE_TOR_DEBRIS, _FIRE_TOR_IMPACT, _FIRE_TOR_TURNSTOP]},
            # 17 Eki, Bahadır (Parti 1): araç hortumdan kaçar, arkasına yanan moloz düşer. 18 Eki: Parti 1 metinleri
            # kısaldı (≤16 kelime, kod yedeği 75 kelimeye sığsın; önceki uzun metinler commit d77655d)
            "T7": {"text": "the {vehicle} races away from the fire tornado as burning debris crashes down behind it",
                   "terms": [_FIRE_TOR_VEH, _FIRE_TOR_ESCAPE, _FIRE_TOR_DEBRIS]},
        },
        "slice_3": {
            # 17 Eki, Bahadır: "across the street" (ev kameranın durduğu ev değil), nokta kısıtı kalktı. Önceki: "the
            # towering fire tornado rips the burning roof off a house and sucks the sheets into its column"
            # 18 Eki (2): "column" -> "funnel", ≤16 kelime. Önceki: "the towering fire tornado rips the burning roof off
            # a house across the street and sucks the sheets into its column"
            "U1": {"text": "the fire tornado rips the burning roof off a house across the street into its funnel",
                   # 18 Eki (2) kuru deneme: nesne ev VEYA çatı ("yanks a burning roof into its vortex" evsiz
                   # reddediliyordu); çatı grubu ayrıca duruyor
                   # (araç tavanı "its roof" sayılmaz: sadece yanan çatı bileşikleri)
                   "terms": [_FIRE_TOR_HOUSE + ("burning roof", "blazing roof", "flaming roof", "roof of a house",
                                                "house roof", "house's roof"), _FIRE_ROOF, _FIRE_TOR_RIP, _FIRE_FLAME],
                   # 17 Eki: iki evin çatısı sırayla (U8) U1 sayılmaz (eski sıkı kapı raporu; üretim kapısı nesneye bakar)
                   "unless": _FIRE_TOR_ROW},
            "U2": {"text": "the huge fire tornado uproots a cluster of burning trees and flings their trunks down the "
                           "road",
                   "terms": [_FIRE_TOR_TREE, _FIRE_TOR_UPROOT, _FIRE_FLAME]},
            "U6": {"text": "the towering fire tornado sweeps over a parked trailer and tosses it aside in fire and "
                           "smoke",
                   "terms": [_FIRE_TOR_TRAILER, _FIRE_TOR_TOSS, _FIRE_FLAME]},
            # 17 Eki, Bahadır (Parti 1): yerleşim yıkımı, büyük ve koyu yapı + hortum sütunu (U3 ahır, U4 çalı yığını,
            # U5 odun yığını yerine)
            "U7": {"text": "a wooden house across the street is torn from its foundation, planks spiraling into the "
                           "funnel",
                   "terms": [_FIRE_TOR_HOUSE, _FIRE_TOR_WHOLE, _FIRE_TOR_PLANKS]},
            "U8": {"text": "the roofs of two houses across the street are ripped off and sucked into the funnel",
                   "terms": [_FIRE_ROOF, _FIRE_TOR_RIP, _FIRE_TOR_ROW]},
            "U9": {"text": "the front wall of a house across the street tears away, rubble sucked into the funnel",
                   "terms": [_FIRE_TOR_WALL, _FIRE_TOR_RIP, _FIRE_TOR_INTAKE]},   # 18 Eki: kısa metinde alev yok
            "U10": {"text": "the porch and steps of a house across the street are ripped off and pulled in",
                    "terms": [_FIRE_TOR_PORCH, _FIRE_TOR_RIP, _FIRE_TOR_INTAKE + _FIRE_TOR_COLUMN]},   # 18 Eki: kıvılcım yok
            "U11": {"text": "a wooden garage beside a house across the street bursts apart, burning boards spiraling "
                            "up",
                    "terms": [_FIRE_TOR_GARAGE, _FIRE_TOR_WRECK, _FIRE_FLAME]},
        },
        # 15 Eki (2): T2 ağaç gövdesi / U2 yanan ağaçlar. 17 Eki: (T4,U4) (T2,U5) U4/U5 ile gitti.
        # 17 Eki (Parti 1, madde 1 kuralı): kod yedeğinin kelime sınırına sığmayan çiftler de hariç (kilit cümle 28-29 +
        # insan cümlesi 6-7 + uzun çift > 75). 18 Eki: yeni metinler ≤16 kelime, 23 çiftten sadece T6+U1 sığmıyordu.
        # 18 Eki (2): kilit cümle 32-33 kelime (dönen huni); U1 16 kelimeye kısaldı, T6+U1 sığıyor; T6 (19 + araç) U2 ve
        # U6 (17'şer) ile 75'i aşıyor
        "excluded_pairs": {("T1", "U2"), ("T2", "U2"), ("T6", "U2"), ("T6", "U6")},
        "excluded_views": {},
        # 17 Eki, Bahadır: U1 "across the street" oldu, nokta kısıtı kalktı. Önceki (16 Eki): U1 sadece köy yamaç
        # terasında (balkonlar, çatı ve üst kat terası hariç)
        "excluded_spots": {},
    },
    # ── Helikopter (10 Eki, Bahadır: havuzlar ve yasak eşleşmeler ONAYLI, metin birebir) ──
    HELICOPTER: {
        "slice_2": {
            "F1": {"text": "the water load slams into the flames, flattening a section of the wall into a cloud of white "
                           "steam",
                   "terms": [_FIRE_WATER, _FIRE_FLAME, _FIRE_STEAM]},
            "F2": {"text": "the helicopter drops a second load and the water crashes down onto burning rooftops, sending "
                           "steam and sparks billowing",
                   "terms": [_FIRE_WATER, _FIRE_HOUSE, _FIRE_STEAM]},
            "F3": {"text": "the {vehicle} speeds down the street as the helicopter's downdraft whips smoke and embers "
                           "across the road",
                   "terms": [_FIRE_SPEED, _FIRE_DOWNDRAFT, _FIRE_SMOKE_EMBER]},
            "F4": {"text": "the helicopter roars low over the street, its downdraft bending the burning trees and "
                           "scattering embers",
                   "terms": [_FIRE_HELI, _FIRE_DOWNDRAFT, _FIRE_HELI_TREE, _FIRE_BEND]},
            "F5": {"text": "a wall of water falls on a burning house, the flames collapsing into thick white steam",
                   "terms": [_FIRE_WATER, _FIRE_HOUSE, _FIRE_STEAM]},
            "F6": {"text": "the {vehicle} brakes hard as a drenching cascade of water spills across the road in front of "
                           "it",
                   "terms": [_FIRE_STOP, _FIRE_WATER, _FIRE_PATH]},
        },
        "slice_3": {
            "G1": {"text": "the flames fight back, a fresh burst of fire swallowing trees beside the water line",
                   "terms": [_FIRE_FLAME, _FIRE_RETURN, _FIRE_HELI_TREE]},
            "G2": {"text": "the helicopter circles back and drops another huge load, extinguishing a row of burning trees "
                           "in a cloud of steam",
                   "terms": [_FIRE_HELI, _FIRE_DROP + _FIRE_WATER, _FIRE_HELI_TREE, _FIRE_DOUSE]},
            "G3": {"text": "thick white steam rolls over the street as the wall of flames sinks back toward the slope",
                   "terms": [_FIRE_STEAM, _FIRE_FLAME, _FIRE_RETREAT]},
            "G5": {"text": "the helicopter pulls up and away as the flames roar back behind it",
                   "terms": [_FIRE_HELI, _FIRE_PULLUP, _FIRE_FLAME, _FIRE_RETURN]},
            "G6": {"text": "a second helicopter swoops in and drops water on the flames along the road",
                   "terms": [_FIRE_SECOND, _FIRE_HELI, _FIRE_DROP + _FIRE_WATER, _FIRE_FLAME]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "G7": {"text": "burning treetops erupt as the helicopter's water load hits the ridge above the houses",
                   "terms": [_FIRE_HELI_TREE, _FIRE_WATER, _FIRE_FLAME]},
        },
        "excluded_pairs": {("F1", "G3"), ("F2", "G2"), ("F5", "G3")},
        "excluded_views": {},
        # Kamera bir yamaç evinin balkonunda (orman yangınındaki L1/L5 gibi): yanan çatıya/eve su düşmesi (F2, F5)
        # ve alevin ıskalanan bir çatıya sıçraması (G4) kameranın durduğu ev gibi çizilebilir; o noktada seçilmez
        # 17 Eki: G4 çıktı (ince/uzak), nokta kısıtı onunla gitti
        "excluded_spots": {"F2": {"Balcony of a hillside house"}, "F5": {"Balcony of a hillside house"}},
    },
    # ── 🌋 Volkan (TASLAK, 10 Eki, Bahadır). Her madde somut temas/yıkım (atmosfer maddesi yok); U2 ve Q3 Bahadır'ın
    # metni birebir, diğerleri Bahadır'ın Türkçe tarifinden. Yasak eşleşmeler: aynı nesne iki kez. ──
    # ── ARŞİV: 🌋 Lav nehri (10-13 Eki 2026, ÇIKARILDI 13 Eki, Bahadır). 4 testte de kabul edilmedi: gerçek lav yürüme
    # hızından yavaş ilerler ve evi saniyeler içinde yıkmaz; Seedance lavı hızlandırıyor, ev yıkımı gerçek dışı çıkıyor.
    # Ders: olay/madde yazarken "gerçekte bunu yapar mı" kontrolü. Son hâli (kod silindi, geri almak için commit d58330a):
    # olay "Lava river pours down into a village street", menü "🌋 Lav nehri sokağı yutuyor", sadece yamaç ve çatı terası,
    # araçsız. Kilit görsel: "A thick lava front crawls down the volcano’s flank into a village street, setting the
    # houses ahead of it alight." Stil eki ek cümlesi: "The lava is thick, black-crusted and tar-like, advancing at a
    # slow walking pace." (lavda "emergency responders" kısıtı yoktu, 8 kısıt). Havuz: L1 lav taş duvarı itip üstünden
    # geçer, L2 sıcaklık ağaçları tutuşturur, L3 ev köşesi şişip çöker, L4 çit + kulübe / M1 kapı ve pencereler patlar,
    # M2 ev duvarı çöker, M3 dükkân cephesi, M4 bina birinci katı. Yasak çiftler (L1,M2) (L1,M4) (L3,M1) (L3,M2)
    # (L3,M4). Kapılar: hız/sıvı kelimeleri (race, rush, surge, torrent, gush, flood, rapids, like water, wave, pour,
    # stream; insan kaçışı ve alev öznesi serbest), çarpma fiilleri (crash, slam, smash, hurl, blast, ram, plow),
    # araç ve balkon kelimeleri, insan cümlesinde fade/vanish süsü.
    ERUPTION: {
        "slice_2": {
            "S2": {"text": "the shockwave blows out the windows of the {vehicle}, which brakes hard",
                   "terms": [_VOLC_GLASS, _VOLC_BURST, _VOLC_BRAKE]},
            "S3": {"text": "the shockwave rips roof tiles off a house and hurls them into the street",
                   "terms": [_VOLC_TILE, _VOLC_RIP, _VOLC_FLING]},
            # 13 Eki (4), Bahadır: S4-S5 birebir (S6 "roof tiles off the houses" S3 ile aynı nesne, Bahadır kararıyla yok)
            "S4": {"text": "the shockwave bends a row of street trees flat and snaps power poles in two",
                   "terms": [_VOLC_TREE + _VOLC_POLE, _VOLC_SNAP]},
            "S5": {"text": "the shockwave topples a stone wall along the street and the stones scatter across the road",
                   "terms": [_VOLC_WALL, _VOLC_TOPPLE]},
            # 17 Eki, Bahadır (Parti 1): karşıdaki ev ve büyük kamyon (S1 vitrin camı yerine). 18 Eki: kısa metinler
            "S6": {"text": "the shockwave hits the house across the street and its front wall bursts outward",
                   "terms": [_VOLC_SHOCK, _VOLC_HOUSE, _VOLC_BURST + _VOLC_FLING]},
            "S7": {"text": "the shockwave lifts the roof off a house across the street and hurls it away",
                   "terms": [_VOLC_SHOCK, _VOLC_ROOF, _VOLC_RIP + _VOLC_FLING]},
            "S8": {"text": "the shockwave shoves a large truck sideways down the street and flips it",
                   "terms": [_VOLC_SHOCK, _VOLC_CAR, _VOLC_PUSH + ("flip", "overturn", "tip over", "roll over",
                                                                    "onto its side", "on its side")]},
        },
        "slice_3": {
            "U2": {"text": "a glowing rock from the eruption slams into a parked car and shatters its rear window",
                   "terms": [_VOLC_ROCK, _VOLC_CAR, _VOLC_SMASH]},
            "U3": {"text": "the shop shutters buckle and burst outward into the street",
                   "terms": [_VOLC_SHUTTER, _VOLC_BUCKLE]},
            # 13 Eki (4), Bahadır: U5-U6 birebir. U4 Bahadır'ın metninin temaslı hâli (Bahadır kararı; önerilen metin
            # "a second blast sends a wave of dust and rubble through the village street" bir şeye çarpmıyordu)
            "U4": {"text": "a second blast tears the front off a house across the street and the rubble spills into the "
                           "road",
                   "terms": [_VOLC_HOUSE, _VOLC_RIP + _VOLC_COLLAPSE]},
            "U5": {"text": "a bell tower cracks and its top section topples across the street",
                   "terms": [_VOLC_TOWER, _VOLC_COLLAPSE + _VOLC_FALL]},
            "U6": {"text": "the shockwave collapses a row of garden walls and a tin-roofed shed",
                   "terms": [_VOLC_WALL + _VOLC_SHED, _VOLC_COLLAPSE + _VOLC_TOPPLE]},
            # 17 Eki, Bahadır (Parti 1): evler çöker (U1 tabela/tente yerine)
            "U7": {"text": "the shockwave rolls down the street and the houses on both sides collapse inward",
                   "terms": [_VOLC_SHOCK, _VOLC_HOUSE, _VOLC_COLLAPSE]},
            "U8": {"text": "the shockwave tears the upper floor off a stone house across the street",
                   "terms": [_VOLC_SHOCK, _VOLC_HOUSE + _VOLC_FLOOR, _VOLC_RIP + _VOLC_COLLAPSE + _VOLC_FALL]},
        },
        # Aynı yapı iki dilimde yok: vitrin/kepenk aynı dükkân cephesi (S1,U3); araç camı iki kez (S2,U2); duvar iki
        # kez (S5,U6, 13 Eki 4). Ev cephesi (U4) S3'ün çatısı ve S5'in sokak duvarıyla aynı yapı sayılmadı. 17 Eki:
        # (S1,U3) S1 ile gitti. 17 Eki (Parti 1), aynı yapı iki dilimde yok: ev (S6 ön duvar: U4, U7, U8), araç (S8
        # kamyon: U2). S7 (çatı) S3 gibi: ev cephesi/katıyla aynı yapı sayılmaz.
        "excluded_pairs": {("S2", "U2"), ("S5", "U6"), ("S6", "U4"), ("S6", "U7"), ("S6", "U8"), ("S8", "U2")}
                          | _VOLC_ERUPTION_GAPS,
        "excluded_views": {},
        # Kamera evinin/terasın çatısı: "çatı kiremitleri kopar" çatı terasında ve köy evi balkonunda seçilmez.
        # 17 Eki: U7 (sokağın iki yanındaki evler çöker) aynı sebeple: kameranın durduğu ev de sokakta
        "excluded_spots": {"S3": {"Rooftop terrace facing the erupting volcano", "Balcony of a village house facing the erupting volcano"},
                           "U7": {"Rooftop terrace facing the erupting volcano", "Balcony of a village house facing the erupting volcano"}},
    },
    # 13 Eki, Bahadır: kül bulutu maddeleri yukarıdan görünen büyük şeylere çevrildi (birebir). Gerekçe: tente,
    # sandalye, çöp kutusu, araba camı teras kamerasında seçilmiyor. Araç hareketi yok. Kilit görsel aynı. Önceki
    # havuz (10 Eki): P1 tente + sandalye, P2 kaçan araç, P3 kiremit / Q1 ağaçlar, Q2 park halindeki araba camı, Q3 çatı.
    PYROCLASTIC: {
        "slice_2": {
            "P1": {"text": "the cloud front slams into the houses across the street and tears the balconies off their "
                           "facades",
                   "terms": [_VOLC_CLOUD, _VOLC_BALCONY, _VOLC_RIP + _VOLC_FALL]},
            "P2": {"text": "the cloud snaps a row of street trees and power poles and they crash across the street",
                   "terms": [_VOLC_TREE + _VOLC_POLE, _VOLC_SNAP]},
            "P3": {"text": "the cloud rips roof tiles off the rooftops and hurls them down the street",
                   "terms": [_VOLC_CLOUD, _VOLC_TILE, _VOLC_RIP + _VOLC_FLING]},
            # 13 Eki (4), Bahadır: P4-P6 birebir. P4 P2 ile aynı nesne (ağaç) ama aynı dilimde, Bahadır kararıyla var
            "P4": {"text": "the cloud front flattens a row of palm trees and hurls their fronds ahead of it",
                   "terms": [_VOLC_TREE, _VOLC_SNAP]},
            "P5": {"text": "the cloud front shoves a stone garden wall over and rolls on across the street",
                   "terms": [_VOLC_WALL, _VOLC_TOPPLE + ("shove", "push")]},   # "shoves a wall over" (ayrık)
            "P6": {"text": "the cloud front rips the corrugated roofs off a row of low sheds and sends them flying",
                   "terms": [_VOLC_SHED + _VOLC_METAL_ROOF, _VOLC_RIP + _VOLC_FLING]},
        },
        "slice_3": {
            "Q1": {"text": "a house wall across the street collapses as the cloud engulfs it",
                   "terms": [_VOLC_HOUSE, _VOLC_COLLAPSE]},
            "Q2": {"text": "the cloud engulfs a whole block and the upper-floor windows burst outward in a shower of "
                           "glass",
                   "terms": [_VOLC_GLASS, _VOLC_BURST]},
            "Q3": {"text": "a chimney topples and crashes through a roof as the cloud passes over",
                   "terms": [_VOLC_CHIMNEY, _VOLC_FALL + _VOLC_SMASH]},
            # 13 Eki (4), Bahadır: Q4-Q6 birebir
            "Q4": {"text": "the cloud hits a hillside retaining wall and the wall gives way, boulders tumbling into the "
                           "street",
                   "terms": [_VOLC_WALL + _VOLC_ROCK, _VOLC_COLLAPSE + _VOLC_FALL]},
            "Q5": {"text": "the cloud blasts the front off a shop building and the brickwork falls into the street",
                   "terms": [_VOLC_SHOP + _VOLC_WALL, _VOLC_RIP + _VOLC_COLLAPSE + _VOLC_FALL]},
            "Q6": {"text": "the cloud engulfs a house and its balcony and flat roof slab tear away",
                   "terms": [_VOLC_BALCONY + _VOLC_ROOF + ("slab",), _VOLC_RIP + _VOLC_COLLAPSE]},
        },
        # Kural (13 Eki): aynı yapı iki dilimde yok. Çatı (P3,Q3) (P3,Q6) (P6,Q3) (P6,Q6); ev cephesi/duvarı (P1,Q1);
        # balkon (P1,Q6); duvar (P5,Q1) (P5,Q4). Dükkân binası (Q5) ev sayılmaz.
        "excluded_pairs": {("P3", "Q3"), ("P1", "Q1"), ("P3", "Q6"), ("P6", "Q3"), ("P6", "Q6"), ("P1", "Q6"),
                           ("P5", "Q1"), ("P5", "Q4")},
        "excluded_views": {},
        # Kamera evinin/terasın çatısı: çatı maddeleri (P3 kiremit, P6 sac çatı, Q3 baca, Q6 çatı döşemesi) çatı
        # terasında ve köy evi balkonunda seçilmez, sadece yamaç terasında
        "excluded_spots": {"P3": {"Rooftop terrace facing the erupting volcano", "Balcony of a village house facing the erupting volcano"}, "Q3": {"Rooftop terrace facing the erupting volcano", "Balcony of a village house facing the erupting volcano"},
                           "P6": {"Rooftop terrace facing the erupting volcano", "Balcony of a village house facing the erupting volcano"}, "Q6": {"Rooftop terrace facing the erupting volcano", "Balcony of a village house facing the erupting volcano"}},
    },
    VOLCANIC_BOMBS: {
        "slice_2": {
            "R1": {"text": "a glowing rock punches through the roof of the {vehicle}",
                   "terms": [_VOLC_ROCK, _VOLC_SMASH, _VOLC_VEH_ROOF]},
            "R2": {"text": "a glowing rock smashes onto the street, bursts apart and sets a parked car on fire",
                   "terms": [_VOLC_ROCK, _VOLC_CAR, _VOLC_IGNITE]},
            "R3": {"text": "a glowing rock tears through a shop awning and sets it ablaze",
                   "terms": [_VOLC_ROCK, _VOLC_AWNING, _VOLC_IGNITE + _VOLC_SMASH]},
            "R4": {"text": "a glowing rock slams into a shop sign, which crashes onto the sidewalk",
                   "terms": [_VOLC_ROCK, _VOLC_SIGN, _VOLC_FALL]},
            # 13 Eki (4), Bahadır: R5-R6 birebir
            "R5": {"text": "a volcanic bomb punches through a stone wall and the wall bursts apart",
                   "terms": [_VOLC_ROCK, _VOLC_WALL, _VOLC_SMASH]},
            # 17 Eki, Bahadır (Parti 1): büyük ve yakın hedefler (ev çatısı, ev duvarı, yol). 18 Eki: kısa metinler
            "R7": {"text": "a huge glowing rock crashes through the roof of a house across the street",
                   "terms": [_VOLC_ROCK, _VOLC_HOUSE + _VOLC_ROOF, _VOLC_SMASH]},
            "R8": {"text": "a glowing rock slams into a house across the street and its wall bursts apart",
                   "terms": [_VOLC_ROCK, _VOLC_HOUSE + _VOLC_WALL, _VOLC_BURST + _VOLC_SMASH]},
            "R9": {"text": "a glowing rock hits the road ahead and sends burning chunks across the street",
                   "terms": [_VOLC_ROCK, _VOLC_ROAD, _VOLC_CRATER + _VOLC_SNAP + _VOLC_SMASH]},
        },
        "slice_3": {
            "T1": {"text": "glowing rocks slam into the roofs, sending tiles flying as flames rise",
                   "terms": [_VOLC_ROCK, _VOLC_ROOF, _VOLC_SMASH]},
            "T2": {"text": "a glowing rock bounces along the road and slams into a parked car",
                   "terms": [_VOLC_ROCK, _VOLC_CAR, _VOLC_SMASH]},
            # 13 Eki (4), Bahadır: T5-T6 birebir
            "T5": {"text": "a volcanic bomb lands in the middle of the street and the road blasts apart in a crater of "
                           "sparks and rock",
                   "terms": [_VOLC_ROCK, _VOLC_ROAD, _VOLC_CRATER]},
            "T6": {"text": "a volcanic bomb hits a house's upper floor and a section of the wall bursts outward in flames",
                   "terms": [_VOLC_ROCK, _VOLC_HOUSE + _VOLC_FLOOR, _VOLC_BURST + _VOLC_IGNITE + _VOLC_SMASH]},
            # 17 Eki, Bahadır (Parti 1)
            "T7": {"text": "glowing rocks hit a row of houses and set their roofs ablaze",
                   "terms": [_VOLC_ROCK, _VOLC_HOUSE + _VOLC_ROOF, _VOLC_IGNITE]},
            "T8": {"text": "a huge glowing rock hits a house and its upper floor erupts in flames",
                   "terms": [_VOLC_ROCK, _VOLC_HOUSE + _VOLC_FLOOR, _VOLC_IGNITE + _VOLC_COLLAPSE + _VOLC_SMASH]},
            "T9": {"text": "a glowing rock smashes into a large parked truck and flames wrap the cab",
                   "terms": [_VOLC_ROCK, _VOLC_CAR, _VOLC_SMASH + _VOLC_IGNITE]},
        },
        # araç iki kez (R2,T2) (R1,T2); dükkân yangını iki kez (R3,T3); 13 Eki (4): duvar iki kez (R5,T6), ağaç/direk
        # iki kez (R6,T4). 17 Eki: (R3,T3) (R6,T4) T3/T4/R6 ile gitti. 17 Eki (Parti 1), aynı yapı iki dilimde yok
        # (13 Eki kuralı; çatı ve cephe/kat aynı yapı sayılmaz): çatı (R7: T1, T7), duvar (R8: T6), yol (R9: T5), araç
        # (R1, R2: T9 kamyon)
        "excluded_pairs": {("R2", "T2"), ("R1", "T2"), ("R5", "T6"),
                           ("R7", "T1"), ("R7", "T7"), ("R8", "T6"), ("R9", "T5"), ("R1", "T9"), ("R2", "T9")}
                          | _VOLC_BOMBS_GAPS,
        "excluded_views": {},
        # Kamera evinin/terasın çatısı: "taşlar çatılara çarpar" çatı terasında ve köy evi balkonunda seçilmez.
        # 17 Eki: T7 (bir sıra evin çatısı) aynı sebeple
        "excluded_spots": {"T1": {"Rooftop terrace facing the erupting volcano", "Balcony of a village house facing the erupting volcano"},
                           "T7": {"Rooftop terrace facing the erupting volcano", "Balcony of a village house facing the erupting volcano"}},
    },
    # ── ❄️ Çığ (TASLAK, 13 Eki, Bahadır). Maddeler Bahadır'ın metni birebir; araç ve kurtarma yok. Yasak çiftler: aynı
    # yapı sınıfı iki dilimde yok. 14 Eki (3), Bahadır: zayıf madde temizliği. Kural: her madde kameraya yakın, BÜYÜK,
    # KOYU ve kar bulutunda kaybolmayan bir nesneye temas eder (ince direk/kablo/korkuluk, cam, uzak yamaç, gömülme
    # yok). Havuz kontrolü: tests/test_pool_lint.py (çığda zorunlu). Kamera dışlamaları:
    # (*) çatı/kule/balkon: sadece köy kenarı terasında (kamera dağ evi balkonundaysa kendi binası olabilir).
    # (‡) teras döşemesi (C3): teras noktalarında seçilmez, sadece balkonda (kamera kendi durduğu terasa bakabilir).
    # (†) teleferik: istasyon terasında seçilmez. 14 Eki (3) itibarıyla teleferik maddesi kalmadı; kural testte duruyor
    # (teleferik kelimesi geçen her kayak maddesi istasyon terasında dışlanmalı), madde geri gelirse dışlama eklenir.
    AVALANCHE_VILLAGE: {
        "slice_2": {
            # 14 Eki (3): önceki "the snow wall flattens a row of pine trees and hurls the trunks ahead of it" (uzak)
            "A1": {"text": "the snow blast hurls a stack of heavy timber logs into a chalet wall",
                   "terms": [_AVA_LOGPILE, _AVA_HURL + _AVA_SWEEP + _AVA_IMPACT, _AVA_HOUSES]},
            "A2": {"text": "the snow blast tears a wooden chalet off its foundation and sweeps it down the slope",
                   "terms": [_AVA_CHALET, _AVA_SWEEP]},
            # 14 Eki (2), false reject taraması: "sending its roof flying"
            "A3": {"text": "the snow blast rips the roof off a barn and scatters the planks",
                   "terms": [_AVA_ROOF, _AVA_RIP + _AVA_LIFT_UP + _AVA_FLY]},
            # 14 Eki, Bahadır: A4 taş duvar (küçük) yerine taş ahır. Önceki: "the snow wall shoves a stone wall over
            # and rolls on through the village street"
            "A4": {"text": "the snow wall rams a stone barn and its dark stones burst out in all directions",
                   "terms": [_AVA_STONEBARN, _AVA_COLLAPSE + _AVA_BLOWOUT + _AVA_FLY + _AVA_IMPACT]},
            # 14 Eki (3): önceki "the snow blast snaps a row of wooden fence posts and power poles" (ince)
            "A5": {"text": "the snow wall flattens a long wooden fence and a wooden shed beside the street, the dark "
                           "boards flying",
                   "terms": [_AVA_FENCE + _AVA_SHED, _AVA_FLATTEN + _AVA_COLLAPSE + _AVA_FLY + _AVA_SWEEP]},
            # 14 Eki (2), false reject taraması: "balcony crashing off"
            "A6": {"text": "the snow cloud smashes the balcony off a chalet facade",
                   "terms": [_AVA_BALCONY, _AVA_RIP + _AVA_COLLAPSE + _AVA_FLY + ("crash",)]},
        },
        "slice_3": {
            # 14 Eki (3): önceki "a second wave hits a chalet and its front wall bursts inward" (B5 ile aynı)
            "B1": {"text": "the snow blast smashes into a stone chalet and its gable wall collapses",
                   "terms": [_AVA_STONECHALET, _AVA_COLLAPSE + _AVA_IMPACT]},
            # 14 Eki (3): önceki "the snow wall buries a whole row of houses up to their roofs" (beyaz üstüne beyaz)
            "B2": {"text": "the snow wall tears a wooden balcony and its staircase off a chalet and the dark timbers "
                           "crash into the street",
                   "terms": [_AVA_BALCONY + _AVA_STAIRS, _AVA_RIP + _AVA_SWEEP + _AVA_COLLAPSE + _AVA_FLY + ("crash",)]},
            "B3": {"text": "the snow blast topples a wooden church bell tower across the street",
                   "terms": [_AVA_TOWER, _AVA_TOPPLE]},
            "B4": {"text": "the snow wall crashes into a hillside retaining wall and the stones tumble out",
                   "terms": [_AVA_STONEWALL, _AVA_COLLAPSE + _AVA_TOPPLE]},
            # 14 Eki, Bahadır: pencere yerine büyük ahşap cephe. Önceki: "the snow cloud blows the windows out of a
            # long wooden building"
            "B5": {"text": "the snow blast rips the entire front wall off a long wooden chalet and the dark timber "
                           "beams fly outward",
                   "terms": [_AVA_FACADE, _AVA_RIP + _AVA_BLOWOUT + _AVA_FLY]},
            "B6": {"text": "the snow wall carries a wooden shed off its base and breaks it apart",
                   "terms": [_AVA_SHED, _AVA_SWEEP + _AVA_COLLAPSE]},
        },
        # 14 Eki (3) sınıflar: ahşap kulübe (A5,B6), dağ evi bütün yapı (A2,B6); çatı/kule (A3,B3); taş yapı (A4 taş
        # ahır: B1 taş dağ evi, B4 istinat duvarı); dağ evi duvarı/cephe (A1 kütükler duvara, A6 balkon cephesi: B1
        # kalkan duvarı, B5 ön duvar); balkon (A6,B2)
        # 17 Eki, Bahadır (temizlik turu, madde 1): kod yedeğinin kelime sınırına sığmadığı 6 çift de hariç (kilit
        # cümle 29 + uzun A/B çifti + en kısa insan cümlesi toplam 70'i aşıyordu; GPT iki denemede kalırsa üretim
        # duruyordu). Beat silinmedi.
        "excluded_pairs": {("A1", "B1"), ("A1", "B5"), ("A2", "B6"), ("A3", "B3"), ("A4", "B1"), ("A4", "B4"),
                           ("A5", "B6"), ("A6", "B1"), ("A6", "B2"), ("A6", "B5"),
                           ("A2", "B2"), ("A2", "B5"), ("A4", "B2"), ("A4", "B5"), ("A5", "B2"), ("A5", "B5")},
        "excluded_views": {},
        "excluded_spots": {"A3": {"Balcony of a chalet at the edge of the village"},
                           "A6": {"Balcony of a chalet at the edge of the village"},
                           "B2": {"Balcony of a chalet at the edge of the village"},
                           "B3": {"Balcony of a chalet at the edge of the village"}},
    },
    AVALANCHE_SKI: {
        "slice_2": {
            # 14 Eki (3): önceki "the avalanche front mows down a row of ski-lift towers, one after another" (uzak)
            "C1": {"text": "the avalanche slams into the lodge's wooden ski-storage shed and its dark planks burst "
                           "outward",
                   "terms": [_AVA_HUT, _AVA_COLLAPSE + _AVA_BLOWOUT + _AVA_FLY + _AVA_IMPACT]},
            # 14 Eki (3): önceki "the snow wall shatters a glass-fronted lodge entrance" (küçük/cam)
            "C2": {"text": "the snow wall smashes the lodge's wooden entrance porch and its dark beams collapse",
                   "terms": [_AVA_PORCH, _AVA_COLLAPSE + _AVA_SHATTER + _AVA_RIP]},
            # 14 Eki (3): önceki "the avalanche rips the wooden terrace railing off the lodge and sweeps it away" (ince)
            "C3": {"text": "the avalanche rips the wooden terrace deck off the lodge and the dark planks fly",
                   "terms": [_AVA_DECK, _AVA_RIP + _AVA_SWEEP + _AVA_FLY + _AVA_LIFT_UP]},
            # 14 Eki (3): önceki "the snow blast flattens a line of wooden snow barriers and orange safety fences"
            "C4": {"text": "the avalanche smashes a wooden snack cabin by the slope and its dark boards scatter",
                   "terms": [_AVA_HUT, _AVA_SHATTER + _AVA_COLLAPSE + _AVA_FLY + _AVA_IMPACT]},
            # 14 Eki (3): önceki "the avalanche hits a stone chairlift station and its upper wall breaks apart" (uzak)
            "C5": {"text": "the avalanche hits a stone service building and its wall bursts apart",
                   "terms": [_AVA_STONEBUILDING, _AVA_COLLAPSE + _AVA_BLOWOUT]},
            # 14 Eki, Bahadır: çam ormanı (beyaz üstüne beyaz) yerine koyu kütük yığını. Önceki: "the avalanche
            # rolls through a grove of pines and snaps them like matchsticks"
            "C6": {"text": "the avalanche shoves a stack of dark timber logs down the slope into the lodge wall",
                   "terms": [_AVA_LOGPILE, _AVA_HURL + _AVA_SWEEP, _AVA_LODGE_TARGET]},
        },
        "slice_3": {
            # 14 Eki, Bahadır: pencere yerine büyük ahşap cephe. Önceki: "a second surge buries the lodge's ground
            # floor, snow bursting through the windows"
            "D1": {"text": "a second surge slams into the lodge and its whole wooden front bursts open, beams and "
                           "planks flying",
                   "terms": [_AVA_FACADE, _AVA_BLOWOUT + _AVA_COLLAPSE + _AVA_RIP + _AVA_FLY]},
            "D2": {"text": "the snow wall tears a wooden annex off the lodge and carries it downhill",
                   "terms": [_AVA_SHED, _AVA_SWEEP]},
            # 14 Eki (2), false reject taraması: "roof deck flying aside"
            "D3": {"text": "the avalanche lifts the lodge's roof deck and tosses it aside",
                   "terms": [_AVA_ROOF, _AVA_LIFT_UP + _AVA_FLY]},
            # 14 Eki, Bahadır: ince çelik ışık kulesi yerine ahşap kiralama kulübesi. Önceki: "the snow blast knocks
            # over a floodlight tower and its steel frame crashes down"
            "D4": {"text": "the snow blast smashes through a wooden ski-rental cabin beside the slope and its dark "
                           "planks scatter",
                   "terms": [_AVA_HUT, _AVA_SHATTER + _AVA_COLLAPSE + _AVA_FLY]},
            # 14 Eki (3): önceki "the avalanche sweeps a small wooden hut off its base and breaks it up" ("small")
            "D5": {"text": "the avalanche sweeps a wooden ski-rental cabin off its base and breaks its dark planks "
                           "apart",
                   "terms": [_AVA_HUT, _AVA_SWEEP + _AVA_COLLAPSE]},
            # 14 Eki (3): önceki "the snow cloud engulfs the chairlift cables and a cable pylon topples" (ince)
            "D6": {"text": "the snow surge crashes through the lodge's side wall and dark timber beams burst out",
                   "terms": [_AVA_FACADE, _AVA_BLOWOUT + _AVA_COLLAPSE + _AVA_FLY + _AVA_IMPACT]},
        },
        # 14 Eki (3) sınıflar: ahşap kulübe/ek bina (C1 kayak deposu, C4 büfe: D2 ek bina, D4 ve D5 kiralama kulübesi);
        # loca cephesi/duvarı (C2 giriş sundurması, C6 kütükler duvara: D1 ön cephe, D6 yan duvar); döşeme (C3 teras
        # döşemesi, D3 çatı döşemesi). C5 taş servis binasının eşi yok.
        "excluded_pairs": {("C1", "D2"), ("C1", "D4"), ("C1", "D5"), ("C2", "D1"), ("C2", "D6"), ("C3", "D3"),
                           ("C4", "D2"), ("C4", "D4"), ("C4", "D5"), ("C6", "D1"), ("C6", "D6")},
        "excluded_views": {},
        "excluded_spots": {"C3": {"Terrace at the edge of the village", "Terrace of the lift station"},
                           "D3": {"Balcony of a chalet at the edge of the village", "Terrace of the lift station"}},
    },
    AVALANCHE_FOREST: {
        "slice_2": {
            "E1": {"text": "the avalanche front hurls snapped pine trunks into a row of wooden cabins",
                   "terms": [_AVA_TREE + _AVA_LOGS, _AVA_CABIN, _AVA_HURL]},
            # 14 Eki (3): önceki "the snow cloud swallows a stand of tall pines whole, their tops whipping flat"
            "E2": {"text": "the avalanche slams a wall of snapped dark pine trunks into a wooden cabin and its side "
                           "bursts open",
                   "terms": [_AVA_TREE + _AVA_LOGS, _AVA_CABIN, _AVA_HURL + _AVA_BLOWOUT + _AVA_COLLAPSE]},
            # 14 Eki (3): önceki "the avalanche sweeps a wooden footbridge off its piers" (uzak)
            "E3": {"text": "the avalanche rams a stone farmhouse's barn door and the dark planks burst inward",
                   "terms": [_AVA_BARNDOOR, _AVA_BLOWOUT + _AVA_COLLAPSE + _AVA_IMPACT]},
            "E4": {"text": "the snow wall tears a woodshed apart and scatters the logs",
                   "terms": [_AVA_SHED + _AVA_LOGS, _AVA_RIP + _AVA_COLLAPSE + _AVA_HURL]},
            # 14 Eki (2), false reject taraması: "sending its roof flying off"
            "E6": {"text": "the snow blast peels the roof off a cabin",
                   "terms": [_AVA_ROOF, _AVA_RIP + _AVA_LIFT_UP + _AVA_FLY]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "E7": {"text": "the avalanche smashes through the front of a stone farmhouse and its roof caves in",
                   "terms": [_AVA_FARMHOUSE, _AVA_IMPACT + _AVA_COLLAPSE + _AVA_SHATTER]},
        },
        "slice_3": {
            "F1": {"text": "a second surge slams into the cabins and their walls burst outward",
                   "terms": [_AVA_CABIN, _AVA_COLLAPSE + _AVA_BLOWOUT]},
            # 14 Eki (3): önceki "the snow wall buries a wooden cabin to the roofline" (gömülme)
            "F2": {"text": "the snow blast rips a cabin's wooden porch and front steps off and sends them flying",
                   "terms": [_AVA_PORCH + _AVA_STAIRS, _AVA_RIP + _AVA_FLY + _AVA_LIFT_UP + _AVA_SWEEP]},
            "F4": {"text": "the snow blast knocks over a wooden water tower",
                   "terms": [_AVA_WATERTOWER, _AVA_TOPPLE]},
            "F5": {"text": "the snow cloud blows the front off a barn and the hay bursts out",
                   "terms": [_AVA_BARN + _AVA_HAY, _AVA_RIP + _AVA_BLOWOUT]},
            # 14 Eki (3): önceki "the avalanche sweeps a row of fences and a footbridge railing away" (ince)
            "F6": {"text": "the snow wall flattens a long wooden barn and the dark boards scatter",
                   "terms": [_AVA_BARN + ("building", "shed"), _AVA_FLATTEN + _AVA_COLLAPSE + _AVA_FLY]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "F7": {"text": "the avalanche front sweeps a wooden cabin off its base and breaks it apart",
                   "terms": [_AVA_CABIN, _AVA_SWEEP + _AVA_COLLAPSE + _AVA_HURL]},
        },
        # 14 Eki (3) sınıflar: ahşap kabin/ahır (E1, E2, E4: F1, F2, F5, F6); ağaç gövdesi (E1, E2: F3); taş çiftlik
        # evi (E3, E5: F3); ahır (E3 ahır kapısı: F5, F6). E6 (kabin çatısı) çatı sınıfı, F'de çatı yok.
        # 17 Eki (temizlik turu): F3 (uzak vadi tabanı) çıktı; F3 çiftleri onunla gitti. 18 Eki (2): E5 çıktı (yerine E7
        # taş çiftlik evi), F7 yeni
        "excluded_pairs": {("E1", "F1"), ("E1", "F2"), ("E1", "F5"), ("E1", "F6"),
                           ("E2", "F1"), ("E2", "F2"), ("E2", "F5"), ("E2", "F6"),
                           ("E3", "F5"), ("E3", "F6"),
                           ("E4", "F1"), ("E4", "F2"), ("E4", "F5"), ("E4", "F6"),
                           ("E1", "F7"), ("E2", "F7"), ("E4", "F7")},   # 18 Eki (2): F7 ahşap kabin
        "excluded_views": {},
        "excluded_spots": {"E6": {"Balcony of a chalet at the edge of the village"}},
    },
    # ── 🏚️ Deprem (TASLAK, 14 Eki, Bahadır). Maddeler Bahadır'ın metni birebir (onaylı düzeltmeler: Q2 yıkım fiili, R3
    # yapı teması, T2 "toward us"). Çöken bina her zaman konut. (*) yüksek açı gerektirir: sadece çatı terasında, yüksek
    # kat balkonunda seçilmez. Yasak çiftler: aynı yapı/görüntü iki dilimde yok.
    EARTHQUAKE_APARTMENT: {
        "slice_2": {
            "P1": {"text": "the upper floors pancake down onto the lower ones and a wall of dust surges across the street",
                   "terms": [_EQ_UPPER, _EQ_FLOORS, _EQ_FALLV]},
            "P2": {"text": "the whole front wall of the block peels off and crashes onto the street",
                   "terms": [_EQ_FRONT, _EQ_PEEL + _EQ_FALLV]},
            "P3": {"text": "the neighboring apartment block leans and its side wall collapses",
                   "terms": [_EQ_NEXTDOOR, _EQ_BUILDING, _EQ_LEAN]},
            "P4": {"text": "a huge concrete slab from the collapsing block slams into the road and breaks it apart",
                   "terms": [_EQ_SLAB, _EQ_ROAD, _EQ_IMPACT]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
        },
        "slice_3": {
            "Q1": {"text": "the building next door crumbles floor by floor into the same dust cloud",
                   "terms": [_EQ_NEXTDOOR, _EQ_BUILDING, _EQ_FALLV]},
            "Q2": {"text": "the dust wave rolls down the street and the upper floors of the apartment blocks opposite "
                           "cave in",
                   "terms": [_EQ_DUST, _EQ_MOVE, _EQ_FALLV]},
            "Q3": {"text": "a row of low houses beside the block is flattened under falling concrete",
                   "terms": [_EQ_HOUSES, _EQ_FALLV]},
            "Q4": {"text": "a second apartment block across the street tilts and falls into the dust",
                   "terms": [_EQ_OTHER, _EQ_BUILDING, _EQ_LEAN]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "Q5": {"text": "the top floors of the apartment block across the street collapse straight down",
                   "terms": [("top floors", "top floor", "upper floors", "upper floor", "top storeys", "top storey",
                              "upper storeys",
                              # 18 Eki (2) kuru deneme: "the upper levels collapse" tanınmıyordu
                              "upper levels", "upper level", "top levels", "top level", "upper stories", "top stories",
                              "upper storey"), _EQ_FALLV],   # bileşik terimler (Q2 "upper floors" tek yer)
                   "unless": _EQ_DUST},   # eski sıkı kapı raporu: tozlu üst kat çökmesi Q2'dir
        },
        # komşu blok (P3 eğilir, yan duvarı çöker: Q1 yan bina, Q4 eğilip düşen ikinci blok); toz dalgası (P1,Q2)
        # 18 Eki (2): üst katlar çöker iki kez (P1: Q5)
        "excluded_pairs": {("P3", "Q1"), ("P3", "Q4"), ("P1", "Q2"), ("P1", "Q5")},
        "excluded_views": {},
        "excluded_spots": {"P2": {"High-floor balcony across the street"}, "Q4": {"High-floor balcony across the street"}},
    },
    EARTHQUAKE_OLD_STREET: {
        "slice_2": {
            "R1": {"text": "the facade of the nearest old stone house slides off in one piece and crashes down",
                   "terms": [_EQ_FRONT, _EQ_PEEL + _EQ_FALLV]},
            "R2": {"text": "the stone walls of two houses fold inward and their roofs fall in",
                   "terms": [_EQ_WALLS + _EQ_HOUSES, _EQ_FALLV, _EQ_ROOF]},
            "R3": {"text": "a thick dust cloud pours down the narrow street as the stone houses keep falling",
                   "terms": [_EQ_DUST, _EQ_MOVE]},
            "R4": {"text": "a corner stone house crumbles and its rubble spreads across the junction",
                   "terms": [_EQ_CORNER, _EQ_HOUSES + _EQ_RUBBLE, _EQ_FALLV + _EQ_SPREAD]},
        },
        "slice_3": {
            "T1": {"text": "the next house in the row caves in and the dust cloud grows",
                   # 18 Eki (2) kuru deneme: "the adjacent building collapses" (eski sokakta bina = ev) tanınmıyordu
                   "terms": [_EQ_NEXTONE, _EQ_HOUSES + ("building", "stone building"), _EQ_FALLV]},
            "T3": {"text": "the rubble heap of a fallen house slides out into the street",
                   "terms": [_EQ_RUBBLE, _EQ_SPREAD, _EQ_ROAD]},
            "T4": {"text": "the roof of a stone house falls in and its walls collapse into the street",
                   "terms": [_EQ_ROOF, _EQ_FALLV, _EQ_HOUSES + _EQ_WALLS]},
            # 18 Eki (2), Bahadır (Parti 2): yeni beat'ler (≤16 kelime)
            "T5": {"text": "the upper floor of a stone house slides off and crashes onto the street below",
                   "terms": [("upper floor", "upper storey", "top floor", "top storey", "floor", "storey"),
                             _EQ_PEEL + _EQ_FALLV]},   # nesne kat (T4 çatı/T1 ev cümlelerini almasın)
            "T7": {"text": "a stone house across the street collapses sideways in a huge wall of dust and rubble",
                   "terms": [_EQ_HOUSES, _EQ_FALLV + _EQ_LEAN, _EQ_SIDEWAYS, _EQ_DUST + _EQ_RUBBLE]},
        },
        # çatı içe göçer (R2,T4); toz bulutu (R3,T1); moloz sokağa yayılır (R4,T3)
        # 18 Eki (2): cephe/üst kat kayar (R1: T5), toz ve moloz (R3, R4: T7)
        "excluded_pairs": {("R2", "T4"), ("R3", "T1"), ("R4", "T3"), ("R1", "T5"), ("R3", "T7"), ("R4", "T7")},
        "excluded_views": {},
        "excluded_spots": {"R1": {"High-floor balcony across the street"}},
    },
    # ── ☄️ Meteor (TASLAK, 29 Eki (2), Bahadır): yeni kurgu, maddeler Bahadır'ın metni birebir. Havuza girmeyenler
    # (METEOR_HELD_BEATS): W2 ve X1 hasar fiili yok (kural 4), W3 "awnings" ve X3 "fences" kalıcı havuz lintinde ince
    # hedef. Eski M/N havuzu RETIRED_BEATS'te.
    METEOR: {
        "slice_2": {
            "W1": {"text": "the shockwave hits the shore, snapping palm trees and ripping roof tiles off the villas",
                   "terms": [_MET_PALM, _MET_ROOFTILE]},
            # 29 Eki (3), Bahadır: yeni metin (önceki "...engulfs the seafront houses": hasar fiili yoktu)
            "W2": {"text": "a ring of white steam and spray races ashore and flips the cars on the seafront road",
                   "terms": [_MET_STEAM, _MET_CAR]},
            # 29 Eki (3), Bahadır: yeni metin (önceki "...pergolas and awnings...": ince hedef)
            "W3": {"text": "the blast rips the sunbeds off the villa terraces and smashes them into the pools",
                   "terms": [_MET_SUNBED, _MET_POOL]},
        },
        "slice_3": {
            # 29 Eki (3), Bahadır: "knocking down" -> "knocking over" (hasar listesinde knock over)
            "X3": {"text": "white, foaming seawater bursts into the villa gardens right below, knocking over the garden "
                           "walls",
                   "terms": [_MET_GARDEN, _MET_WALL]},
            # 29 Eki (3), Bahadır: yeni metin (önceki "...pours across the promenade": hasar fiili yoktu)
            "X1": {"text": "the falling water column crashes onto the promenade as a white, foaming flood, smashing the "
                           "beach kiosks",
                   "terms": [_MET_FLOOD, _MET_PROMENADE]},
            "X2": {"text": "a white, steaming surge floods the coastal road and shoves parked cars into the villa walls",
                   "terms": [_MET_SURGE, _MET_CAR]},
            "X4": {"text": "white surf bursts over the seawall and smashes the beach bars and loungers into the road",
                   "terms": [_MET_SURF, _MET_BAR]},
        },
        # Aynı nesne iki dilimde (29 Eki (3), Bahadır): araba (W2: X2), şezlong (W3: X4). Sığma (Bahadır kararı): W2+X1
        # (17 + 17 kelime) O1 + öğle/kapalı ışıkta 205'i 1 kelime aşıyordu
        "excluded_pairs": {("W2", "X2"), ("W3", "X4"), ("W2", "X1")},
        "excluded_views": {},
        "excluded_spots": {},
    },
}

# Olay -> seçilemeyen beat'ler (havuzda ve lint'te durur, çift seçiminde yok). 29 Eki (2): meteor [DALGA] bayrağı
# kaldırıldı; mekanizma boş.
DISABLED_BEATS: dict[str, set[str]] = {}
# 29 Eki (2), Bahadır: yeni W/X maddelerinden havuza girmeyenler (yerine yeni madde Bahadır'ın kararıyla). Puan sırası:
# büyüklük, kontrast, yakınlık, çizilebilirlik, aksiyon, farklılık.
# 29 Eki (3): W2, W3, X1 yeni metinle, X3 "knocking over" ile havuza girdi; bekleyen madde yok.
METEOR_HELD_BEATS: dict[str, tuple] = {}
# Havuzdaki maddelerin puanları (rapor ve test; hepsi en az 3)
METEOR_BEAT_SCORES = {"W1": (4, 3, 4, 4, 5, 4), "W2": (5, 4, 4, 4, 5, 4), "W3": (4, 3, 4, 4, 5, 4),
                      "X1": (5, 4, 3, 4, 5, 4), "X2": (5, 4, 4, 4, 5, 4), "X3": (4, 4, 5, 4, 4, 4),
                      "X4": (4, 4, 3, 4, 5, 4)}

# ── 17 Eki 2026, Bahadır (temizlik turu): kurala göre çıkarılan beat'ler. Kural: denetimde (scratch/
# asama3_havuz_denetimi.md) ZAYIF/ÇIKAR + en az biri: ince/uzak/küçük hedef, fizik ≤2, aksiyon ≤2, yakın ≤2, büyük ≤2,
# koyu 1, boş arazi/kırsal (ateş hortumu U3-U5). Korunan (üretilmiş videoda kullanılmış) ve grubu 4'ün altına
# düşürecek olanlar çıkarılmadı. Kimlikler tekrar kullanılmaz (Notion geçmişindeki combo_key'ler eski beat'i gösterir).
# Bu kayıt: eski kayıt/fixture okunurken (tests/test_rejected_real.py) ve devir notu için; üretimde seçilmez.
RETIRED_BEATS = {
    FLOOD: {"D1": ("a row of parked cars is ripped loose one by one and dragged away", "fizik(2)"),
            "D6": ("a low wall collapses into the water", "ince/alçak duvar, büyük(2), aksiyon(2)"),
            "D7": ("a wooden fence is torn away and carried off", "ince (çit), büyük(2)")},
    TIDAL: {"W7": ("shopfront windows burst and the surge pours through, carrying out chairs and tables",
                   "ince (cam, mobilya), fizik(2)")},
    MUDSLIDE: {"M1": ("a row of parked cars is pushed down the street one by one", "fizik(2); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
               "M2": ("a utility pole snaps and falls into the mud", "ince (direk), büyük(2); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
               "M5": ("a wooden fence is torn away and carried off", "ince (çit), büyük(2); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı")},
    SLOPE: {"S1": ("a section of the guardrail is bent and torn away by the mud", "ince (bariyer), büyük(2)"),
            "S6": ("a row of parked cars is shoved toward the road edge", "fizik(2)")},
    VILLAGE: {"L2": ("a stretch of wooden fence is torn away and carried off", "ince (çit), büyük(2)")},
    LANDFALL: {"C3": ("a flying street sign slams into the windshield of the {vehicle}",
                      "ince (tabela, cam), büyük(2), fizik(2)"),
               "C6": ("the {vehicle} is swept up into the air, spins, and crashes down onto the sidewalk", "fizik(2)"),
               "E3": ("a wall of dust and debris sweeps across the street and engulfs the end of the block",
                      "uzak, yakın(2)"),
               "E6": ("the tornado tears away a section of fence and carries it down the street", "ince (çit), büyük(2)")},
    MARINA_TORNADO: {"Y4": ("a flying wooden crate smashes the windshield of the {vehicle}",
                            "ince (cam), büyük(2), yakın(2), fizik(2)"),
                     "Y6": ("the {vehicle} is swept up into the air, spins, and crashes down onto the quay", "fizik(2)"),
                     "Z5": ("the tornado sweeps dock boxes and rubbish bins off the quay and hurls them across the road",
                            "küçük/uzak, büyük(2), yakın(2)")},
    AVENUE: {"P3": ("the {vehicle} is pushed against a lamppost and pinned there", "aksiyon(2)"),
             "Q5": ("the tornado topples a line of street lamps one by one", "ince (direk), büyük(2)")},
    WILDFIRE: {"K3": ("a burning branch falls onto the {vehicle}, setting its roof alight", "küçük (dal); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
               "K4": ("the {vehicle} swerves around a falling burning pine and slams into the guardrail",
                      "fizik(2), bariyer; " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
               "K6": ("embers rain onto the {vehicle} as it races down the road, its rear window cracking in the heat",
                      "cam, büyük(2), fizik(2); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
               "L2": ("a shower of glowing embers rains onto the street and sets a wooden fence alight",
                      "ince (çit), büyük(2)"),
               "L6": ("the flames climb a power pole and snap the wires, which whip across the street in a shower of "
                      "sparks", "ince (direk, tel), büyük(1), fizik(2)")},
    FACADE_FIRE: {"M1": ("a burning panel crashes onto the {vehicle} parked below, crushing its roof",
                         "cephe yangınında araç (yakın 2); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
                  "M2": ("shattered glass rains onto the {vehicle} as it speeds away from the tower",
                         "cam, cephe yangınında araç; " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
                  "M3": ("burning debris lands on the hood of the {vehicle}, which lurches back in a hurry",
                         "cephe yangınında araç (yakın 2); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
                  "M4": ("the {vehicle} swerves around a falling flaming panel and mounts the curb",
                         "cephe yangınında araç (yakın 2, fizik 2); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
                  "M5": ("a burning awning drops onto the {vehicle}, which reverses sharply",
                         "tente, cephe yangınında araç; " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
                  "N2": ("a balcony awning catches fire and the flames leap to the floor above", "ince (tente)"),
                  "N6": ("the fire jumps to the neighboring balcony, igniting its plants and furniture",
                         "küçük, büyük(2)")},
    FIRE_TORNADO: {"T3": ("the {vehicle} is sucked up into the towering fire tornado, spins, and crashes down onto the "
                          "road in sparks", "fizik(2)"),
                   "U3": ("the towering fire tornado swallows a wooden barn and tears it to pieces, burning planks "
                          "whirling into the column", "kırsal/boş arazi (Bahadır)"),
                   "U4": ("the towering tornado sucks up a huge burning brush pile and spits it across the road in "
                          "sparks", "boş arazi, büyük(2), koyu(1), fizik(2)"),
                   "U5": ("the huge fire tornado tears through a big woodpile and hurls the burning logs high across "
                          "the field", "boş arazi (field)")},
    HELICOPTER: {"G4": ("embers blow past the helicopter as flames leap to a roof the water missed",
                        "küçük/belirsiz, yakın(2), fizik(2)")},
    ERUPTION: {"S1": ("the shockwave bursts the shop windows along the street one after another",
                      "ince (cam), büyük(2), fizik(2)"),
               "U1": ("a shop sign and an awning tear loose and slam onto the road", "ince (tabela, tente), büyük(2)")},
    VOLCANIC_BOMBS: {"R6": ("a volcanic bomb hits a row of street trees and splits one in two as it falls in flames",
                            "fizik(2)"),
                     "T3": ("a glowing rock smashes through a shop window and sets the curtains on fire",
                            "ince (cam), büyük(2), fizik(2)"),
                     "T4": ("a glowing rock splits a utility pole and its cable falls into the street spitting sparks",
                            "ince (direk, kablo), büyük(1), fizik(2)")},
    EARTHQUAKE_OLD_STREET: {"T2": ("the collapse runs down the street, house after house, toward us",
                                   "fizik(2) (zincirleme çöküş); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı")},
    # 29 Eki (2), Bahadır: meteor yeni kurgu (tek çarpma, beyaz taşkın). İlk test videosunda su sütunu dumana döndü,
    # 5-9s boş, gökten ikinci meteorlar yağıp hasarsız söndü. M3-M5, N4, N5 ilk turda puanlamada düşmüştü (havuza hiç
    # girmedi). Kimlikler tekrar kullanılmaz.
    METEOR: {"M1": ("a blast of wind hits the waterfront, bending palm trees flat and blowing loungers and umbrellas off "
                    "the villa terraces", "29 Eki (2) yeni kurgu"),
             "M2": ("burning chunks of rock crash down across the hillside, smashing into roofs and setting a parked car "
                    "on fire", "29 Eki (2): ikinci meteor / parça yağmuru"),
             "M3": ("the sea pulls back sharply from the beach, exposing the seabed as people on the promenade turn and "
                    "run", "puan: yakınlık 2"),
             "M4": ("people on the terraces below are knocked to the ground by the shockwave, then scramble up and run "
                    "inland", "puan: büyüklük 2, çizilebilirlik 2"),
             "M5": ("a second, smaller fireball streaks down and explodes on the hillside behind the houses",
                    "puan: yakınlık 2; ikinci meteor"),
             "M6": ("the blast rolls over the bay and hurls parked cars and palm trees across the coastal road",
                    "29 Eki (2) yeni kurgu"),
             "N1": ("a towering wave rises from the impact and races toward the coast, crashing over the seawall into the "
                    "first row of modern houses", "29 Eki (2): tsunami duvarı yasak"),
             "N2": ("the wave sweeps cars off the coastal road and drives them into the villa gardens",
                    "29 Eki (2) yeni kurgu"),
             "N3": ("flaming debris sets the roofs of the hillside houses ablaze while people sprint up the street",
                    "29 Eki (2): parça yağmuru"),
             "N4": ("a shower of seawater and burning fragments falls over the whole neighborhood as people run for "
                    "cover under the balconies", "puan: çizilebilirlik 2"),
             "N5": ("a second, larger fireball slams into the sea closer to the shore, throwing a wall of spray over the "
                    "promenade", "puan: farklılık 2; ikinci meteor"),
             "N6": ("the shockwave tears roof tiles and solar panels off the houses and sends them flying over the "
                    "street", "29 Eki (2) yeni kurgu")},
    AVALANCHE_FOREST: {"E5": ("the avalanche hits a stone farmhouse wall and the wall cracks open", "aksiyon(2); " + "çıkış bekliyordu; 18 Eki Parti 2 ile çıktı"),
                       "F3": ("the avalanche carries a pile of broken trunks across the valley floor into a stone house",
                              "uzak, yakın(2)")},
}


# ── HİBRİT HİKÂYE (16 Eki 2026, Bahadır): yumuşak beat kontrolü ────────────────────────────────────────────────────
# Ders: doğru GPT cümleleri fiil/kelime-grubu zincirine (kaldırma + çarpma...) takılıp 3 denemede reddediliyordu, üretim
# boşa gidiyordu. Yeni kapı her beat için SADECE ana nesneye bakar: (i) seçilen beat'in nesne grubu cümlede var mı,
# (ii) cümle aynı dilimdeki seçilmeyen başka bir beat'in nesne grubunu daha çok anıyor mu (yanlış beat). Araçlı
# beat'lerde ana nesne seçilen araçtır (araç adı terimleri); diğerlerinde aşağıdaki tablo, mevcut terim gruplarından
# nesne grubunun sırasını verir (eylem grupları artık kapı değil, sadece eski kapı raporunda: strict_beat_issues).
OBJECT_GROUPS = {
    FLOOD: {"D9": 0, "D2": 0, "D3": 0, "D4": 0, "D5": 0, "D8": 0},
    TIDAL: {"W1": 1, "W2": 0, "W3": 0, "W4": 0, "W5": 0, "W6": 0, "W8": 0},
    # 18 Eki (2) kuru deneme: M8'in nesnesi ev (kamyon evin önüne; "house's facade" M7'ye benzetiliyordu)
    MUDSLIDE: {"M9": 1, "M8": 2, "M7": 0, "M3": 0, "M4": 0, "M6": 0},   # 22 Eki: M3 park arabaları, M6 ev (M7 ile aynı)
    SLOPE: {"S7": 0, "S2": 0, "S3": 0, "S4": 0, "S5": 1},
    VILLAGE: {"L7": 0, "L1": 0, "L3": 0, "L4": 0, "L5": 0, "L6": 0},
    LANDFALL: {"E7": 0, "E1": 0, "E2": 0, "E4": 0, "E5": 0},
    MARINA_TORNADO: {"Z7": 0, "Y8": 0, "Y7": 0, "Z1": 0, "Z2": 0, "Z3": 0, "Z4": 0, "Z6": 0},
    AVENUE: {"P7": 0, "Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0, "Q6": 0},
    WILDFIRE: {"L7": 0, "K8": 1, "K7": 1, "L1": 1, "L3": 1, "L4": 1, "L5": 0},
    FACADE_FIRE: {"M11": 1, "M10": 1, "M9": 1, "M8": 1, "M7": 1, "N1": 2, "N3": 1, "N4": 0, "N5": 0},
    FIRE_TORNADO: {"U1": 0, "U2": 0, "U6": 0, "U7": 0, "U8": 0, "U9": 0, "U10": 0, "U11": 0},
    HELICOPTER: {"G7": 0, "F1": 0, "F2": 1, "F4": 0, "F5": 1, "G1": 2, "G2": 0, "G3": 0, "G5": 0, "G6": 1},
    ERUPTION: {"S3": 0, "S4": 0, "S5": 0, "S6": 1, "S7": 1, "S8": 1, "U2": 1, "U3": 0, "U4": 0, "U5": 0, "U6": 0,
               "U7": 1, "U8": 1},
    PYROCLASTIC: {"P1": 1, "P2": 0, "P3": 1, "P4": 0, "P5": 0, "P6": 0, "Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0, "Q5": 0,
                  "Q6": 0},
    VOLCANIC_BOMBS: {"R2": 1, "R3": 1, "R4": 1, "R5": 1, "R7": 1, "R8": 1, "R9": 1, "T1": 1, "T2": 1, "T5": 1, "T6": 1,
                     "T7": 1, "T8": 1, "T9": 1},
    AVALANCHE_VILLAGE: {"A1": 0, "A2": 0, "A3": 0, "A4": 0, "A5": 0, "A6": 0, "B1": 0, "B2": 0, "B3": 0, "B4": 0,
                        "B5": 0, "B6": 0},
    AVALANCHE_SKI: {"C1": 0, "C2": 0, "C3": 0, "C4": 0, "C5": 0, "C6": 0, "D1": 0, "D2": 0, "D3": 0, "D4": 0, "D5": 0,
                    "D6": 0},
    AVALANCHE_FOREST: {"F7": 0, "E7": 0, "E1": 0, "E2": 0, "E3": 0, "E4": 0, "E6": 0, "F1": 0, "F2": 0, "F4": 0, "F5": 0, "F6": 0},
    EARTHQUAKE_APARTMENT: {"Q5": 0, "P1": 1, "P2": 0, "P3": 1, "P4": 0, "Q1": 1, "Q2": 0, "Q3": 0, "Q4": 1},
    EARTHQUAKE_OLD_STREET: {"T7": 0, "T5": 0, "R1": 0, "R2": 0, "R3": 0, "R4": 1, "T1": 1, "T3": 0, "T4": 0},   # 18 Eki: T2 çıktı
    # 29 Eki (2): meteor nesneleri palmiye (W1), araç (X2), bar/şezlong (X4); iki nesne zorunluluğu METEOR_OBJECT_GATES
    METEOR: {"W1": 0, "W2": 1, "W3": 0, "X1": 1, "X2": 1, "X3": 0, "X4": 1},
}

# Sert kurallara 16 Eki eklemeleri (yapılandırılmış hat, sadece GPT'nin yazdığı üç dilim; mevcut kurallar aynen durur):
# çekim/kayıt kelimeleri (b kuralının "camera/video/phone/footage" listesine ek), ülke/bölge adı, can kaybı. Eski hat
# (story_rule_issues) değişmez. "die/dies" yok ("the flames die down"), "kill" yok ("kill the flames"), "bodies" yok
# ("car bodies"), "alpine" yok (sıfat).
HARD_CAMERA_EXTRA = ("filming", "filmed", "recording", "recorded", "camcorder", "smartphone", "cellphone")
HARD_PLACE_NAMES = ("turkey", "türkiye", "turkish", "syria", "syrian", "japan", "japanese", "italy", "italian", "greece",
                    "greek", "iran", "iranian", "nepal", "mexico", "mexican", "chile", "haiti", "china", "chinese",
                    "india", "indian", "pakistan", "afghanistan", "morocco", "moroccan", "ecuador", "peru", "indonesia",
                    "philippines", "istanbul", "ankara", "izmir", "antakya", "hatay", "tokyo", "kobe", "rome", "athens",
                    "tehran", "kathmandu", "usa", "u.s.", "america", "american", "united states", "california",
                    "florida", "texas", "carolina", "europe", "european", "asia", "asian", "africa", "african",
                    "australia", "australian", "canada", "canadian", "brazil", "spain", "spanish", "france", "french",
                    "germany", "german", "britain", "british", "england", "portugal", "norway", "norwegian",
                    "switzerland", "swiss", "austria", "austrian", "alps", "himalaya", "himalayas", "sahara",
                    "mediterranean", "riviera", "caribbean", "hawaii", "scandinavia", "scandinavian", "middle east",
                    "tunisia", "tunisian", "dubai", "qatar", "taiwan", "holland", "dutch", "netherlands", "iceland")
HARD_DEATH = ("dead", "death", "deaths", "died", "killed", "corpse", "corpses", "victim", "victims", "casualty",
              "casualties", "blood", "bloody", "bloodied", "injured", "injury", "injuries", "wounded", "lifeless",
              "fatal", "fatally", "perish", "perished")
HARD_EXTRA_RULES = (
    ("hard_camera", HARD_CAMERA_EXTRA, "çekim/kayıt kelimesi",
     "Remove {words}: describe only the scene itself, never filming or recording."),
    ("hard_place_name", HARD_PLACE_NAMES, "ülke/bölge adı",
     "Remove {words}: never name a country, city or region."),
    ("hard_death", HARD_DEATH, "can kaybı ifadesi",
     "Remove {words}: no dead, injured or bleeding people."),
)


# 17 Eki, Bahadır (yumuşak kapı düzeltmesi): bu olaylarda "başka beat'e daha çok benziyor" kontrolü yalnızca seçilen
# beat'in kendi nesnesi cümlede YOKSA devreye girer (o durumda zaten beat_object reddi verilir). Sebep: helikopterde
# su bırakma beat'leri (F1 su/alev, F2 çatılar, F5 ev) aynı su kelimelerini paylaşıyor; "A cascade of water hits a
# burning house" F5 için doğru cümle, F1'in nesnesi (water, cascade) daha çok geçtiği için reddediliyordu (2i).
OWN_OBJECT_ENOUGH_EVENTS = (HELICOPTER,)


def beat_object_terms(spec: dict, slot: str, bid: str) -> tuple[str, ...]:
    """Beat'in ana nesne grubu: araçlı beat'te seçilen aracın terimleri, diğerlerinde OBJECT_GROUPS'un gösterdiği
    mevcut terim grubu."""
    beat = EVENT_BEATS[spec["event"]][slot][bid]
    if "{vehicle}" in beat["text"]:
        return spec_vehicle_terms(spec)
    return tuple(beat["terms"][OBJECT_GROUPS[spec["event"]][bid]])


def _object_spans(terms, text: str) -> list[tuple[int, int]]:
    """Nesnenin metindeki anılma yerleri; iç içe eşleşmeler birleşir ("palm tree" = 1 yer)."""
    from core.creative_pipeline import term_pattern
    low = (text or "").lower()
    merged: list[list[int]] = []
    for s, e in sorted((m.start(), m.end()) for t in terms for m in term_pattern(t).finditer(low)):
        if merged and s < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [tuple(x) for x in merged]


def object_mentions(terms, text: str, exclude: list[tuple[int, int]] = ()) -> int:
    """Nesnenin kaç ayrı yerde anıldığı; exclude ile çakışan yerler sayılmaz (seçilen beat'in kendi nesnesi)."""
    return sum(1 for s, e in _object_spans(terms, text) if not any(s < xe and xs < e for xs, xe in exclude))


def _group_match_ratio(beat: dict, text: str) -> float:
    return sum(1 for g in beat["terms"] if find_terms(g, text)) / len(beat["terms"])


def soft_beat_issues(spec: dict, slices: dict[str, str]) -> list[dict]:
    """Yumuşak beat kontrolü (16 Eki): (i) seçilen beat'in nesnesi dilimde var mı; (ii) aynı dilimde seçilmeyen ve
    nesnesi farklı bir beat cümleye daha çok benziyor mu: o beat'in nesnesi (seçilen nesneyle çakışmayan yerlerde)
    daha çok anılıyor VE o beat'in terim gruplarından en az seçilen kadarı cümlede var. Terim grupları sadece bu
    karşılaştırmada kullanılır, tek başına kapı değil (fiil zinciri ret sebebi olmaz)."""
    event, out = spec["event"], []
    beats = EVENT_BEATS[event]
    for slot, bid in (("slice_2", spec["beat_2"]), ("slice_3", spec["beat_3"])):
        text = slices.get(slot, "")
        label = "4-9s" if slot == "slice_2" else "9-15s"
        own = beat_object_terms(spec, slot, bid)
        own_spans = _object_spans(own, text)
        event_text = beat_text(event, slot, bid, spec["vehicle"])
        if not own_spans:
            if "{vehicle}" in beats[slot][bid]["text"]:   # araçlı beat'in nesnesi araç: eski araç kuralının metni
                out.append(_issue("beat_vehicle", f"{label}: araç ({spec['vehicle']})",
                                  f"'{slot}' must name the {spec['vehicle']}."))
            else:
                out.append(_issue("beat_object", f"{label}: seçilen olayın nesnesi ({bid}: {own[0]}) yok",
                                  f"'{slot}' must clearly show this event: {event_text}."))
            continue
        if event in OWN_OBJECT_ENOUGH_EVENTS:   # 17 Eki: kendi nesnesi varsa benzerlik kontrolü yok (helikopter)
            continue
        own_ratio = _group_match_ratio(beats[slot][bid], text)
        for other in beats[slot]:
            terms = beat_object_terms(spec, slot, other)
            if other == bid or set(terms) == set(own):
                continue
            if (object_mentions(terms, text, own_spans) > len(own_spans)
                    and _group_match_ratio(beats[slot][other], text) >= own_ratio):
                out.append(_issue("beat_other_object", f"{label}: cümle başka olaya ({other}) daha çok benziyor",
                                  f"'{slot}' must show this event, not another one: {event_text}."))
                break
    return out


def strict_beat_issues(spec: dict, slices: dict[str, str]) -> list[dict]:
    """ESKİ (16 Eki öncesi) beat kapısı: araç adı + tüm terim grupları (fiil zinciri dahil). Artık kapı değil; sadece
    kuru prova raporunda "eski kapıda geçer miydi" ölçümü için."""
    event, out = spec["event"], []
    beats = EVENT_BEATS[event]
    s2, s3 = slices.get("slice_2", ""), slices.get("slice_3", "")
    if "{vehicle}" in beats["slice_2"][spec["beat_2"]]["text"] and not find_terms(spec_vehicle_terms(spec), s2):
        out.append(_issue("beat_vehicle", f"4-9s: araç ({spec['vehicle']})",
                          f"'slice_2' must name the {spec['vehicle']}."))
    for slot, bid, text in (("slice_2", spec["beat_2"], s2), ("slice_3", spec["beat_3"], s3)):
        if beat_missing(beats[slot][bid], text):
            label = "4-9s" if slot == "slice_2" else "9-15s"
            out.append(_issue("beat_terms", f"{label}: seçilen olay ({bid}) görünmüyor",
                              f"'{slot}' must clearly show this event: {beat_text(event, slot, bid, spec['vehicle'])}."))
    return out


def hard_extra_issues(slices: dict[str, str]) -> list[dict]:
    """16 Eki sert eklemeleri (çekim kelimesi, ülke/bölge adı, can kaybı), GPT'nin yazdığı üç dilimde."""
    text = " ".join(slices.get(f, "") for f in SLICE_FIELDS)
    out = []
    for code, terms, missing, feedback in HARD_EXTRA_RULES:
        found = find_terms(terms, text)
        if found:
            out.append(_issue(code, f"{missing} ({', '.join(found)})",
                              feedback.format(words=", ".join(repr(w) for w in found))))
    return out


# ── Yangın kapıları (TASLAK, 8 Eki, Bahadır). Sadece FIRE_EVENTS; diğer olayların denetimi değişmez. ─────────────
# Yağmur/ıslaklık yasağı: kilit cümle, havuz, hava, yer metni, stil eki ve GPT hikâyesinde. "rain" fiili sadece
# yanan/düşen bir şeyle birlikte geçerse serbest ("embers rain onto", "raining burning debris": Bahadır'ın kendi
# metinleri); yağış anlamındaki her "rain" reddedilir.
NO_RAIN_EVENTS = FIRE_EVENTS + VOLCANO_EVENTS   # 10 Eki: volkan da ateş benzeri (yağmur yok, "fall/shower")
_FIRE_WET = ("wet", "wetness", "soak", "drench", "rain-soaked", "waterlogged", "puddle", "downpour", "drizzle",
             "rainfall", "rainstorm", "raindrop", "rainwater", "rainy", "sleet", "damp", "monsoon")
_RAIN_TOKENS = ("rain", "rains", "rained", "raining")
_RAIN_FALLING_OK = ("ember", "spark", "cinder", "ash", "debris", "glass", "shard", "burning", "flaming", "glowing",
                    "fragment", "panel", "branch", "piece", "firebrand", "rubble", "flame")
_RAIN_WINDOW = 3
# Volkan bombaları (10 Eki, Bahadır): bu dilimlerde genel/küçük taş anlatımı (_VOLC_SMALL_ROCKS) reddedilir
VOLC_SINGLE_ROCK_SLICES = {VOLCANIC_BOMBS: ("slice_2", "slice_3")}
# Olaya özel yasak kelimeler, GPT'nin yazdığı üç dilimde (13 Eki, çığ; mekanizma lav için kurulmuştu):
# (kod, terimler, Telegram satırı, GPT geri bildirimi)
EVENT_BANNED_WORDS = {e: (("avalanche_banned", _AVA_BANNED, "çığda yasak kelime",
                           "Remove {words}: the avalanche itself is the only actor; no rescue, vehicles, boats, sirens or "
                           "readable text."),
                          ("avalanche_no_slow", _AVA_SLOW, "çığ yavaş/sakin değil",
                           "A powder avalanche moves at over 100 km/h and is violent: remove {words}."))
                      for e in AVALANCHE_EVENTS}
# 14 Eki, Bahadır: deprem yasakları (ölü/yaralı/gömülme/kurtarma, araç ve gemi, ülke/şehir adı, yazı) ve yavaşlatıcılar
# (bina ani ve hızlı çöker)
EVENT_BANNED_WORDS.update({e: (("earthquake_banned", _EQ_BANNED, "depremde yasak kelime",
                                "Remove {words}: show only the buildings collapsing; no dead, injured or trapped "
                                "people, no rescue, no vehicles or boats, no country or city names, no readable text."),
                               ("earthquake_no_slow", _EQ_SLOW, "deprem yavaş/sakin değil",
                                "The buildings collapse suddenly and fast: remove {words}."))
                           for e in EARTHQUAKE_EVENTS})
# 29 Eki, Bahadır (ek kural): meteorda sakin/atmosferik fiil yok; 0. saniyeden 15. saniyeye aksiyon kesintisiz
EVENT_BANNED_WORDS[METEOR] = (("meteor_no_static", METEOR_STATIC, "meteorda durağan/sakin fiil",
                               "Every second is violent, nonstop action: remove {words}. No one stands or watches; "
                               "nothing drifts, billows or moves slowly."),
                              # 29 Eki (2): tek meteor, tsunami değil
                              ("meteor_one_impact", METEOR_ONE_BANNED, "meteorda ikinci meteor / parça yağmuru",
                               "There is only one meteor and one impact; nothing else falls from the sky: remove "
                               "{words}."),
                              ("meteor_no_tsunami", METEOR_TSUNAMI_BANNED, "meteorda tsunami / kahverengi su",
                               "The water is a low, wide, white, foaming, steaming flood, never a tsunami or a brown "
                               "rising wall: remove {words}."))
# 175 kelime kapısı olan olaylar (13 Eki: volkan + çığ; 14 Eki: deprem)
# ── Tüm eksenlerde tekrar önleme (21 Eki 2026, Gece 1 / Aşama 3) ──────────────────────────────────────────────────
# Spot, ışık/hava, araç, kişi sayısı: son AXIS_BLOCK kullanılan değer seçilemez. 2 ya da daha az seçenekli eksende
# sadece son 1, tek seçenekli eksende hiç eleme yok. Geçmiş Notion "Eksenler" alanından (iptaller dahil), okunamazsa
# süreç hafızası (_AXES_MEMORY). Boş geçmişte aday listesi tam liste: rastgele çekim eskisiyle birebir aynı.
AXIS_BLOCK = 2
_AXES_MEMORY: dict[str, list[dict]] = {}
_AXES_MEMORY_LIMIT = 12


def axis_block_depth(n_options: int) -> int:
    return 0 if n_options <= 1 else (1 if n_options <= 2 else AXIS_BLOCK)


def lru_axis(options: list, used: list) -> tuple[list, list]:
    """(adaylar, elenenler). used eskiden yeniye; boş değerler sayılmaz. Seçenek sırası korunur."""
    depth = axis_block_depth(len(set(options)))
    recent = [u for u in used if u is not None and u != ""][-depth:] if depth else []
    blocked = set(recent)
    cands = [o for o in options if o not in blocked]
    if not cands:   # güvenlik: hepsi eleniyorsa eleme yok
        return list(options), []
    return cands, [o for o in options if o in blocked]


def remember_axes(event: str, axes: dict) -> None:
    """Seçim anında eksen değerlerini süreç hafızasına yazar (Notion okunamazsa yedek)."""
    with _ENV_LOCK:
        mem = _AXES_MEMORY.setdefault(event, [])
        mem.append(dict(axes))
        del mem[:-_AXES_MEMORY_LIMIT]


def axes_memory(event: str) -> list[dict]:
    with _ENV_LOCK:
        return [dict(a) for a in _AXES_MEMORY.get(event, [])]


WORD_CAP_EVENTS = VOLCANO_EVENTS + AVALANCHE_EVENTS + EARTHQUAKE_EVENTS + (FIRE_TORNADO,)   # 15 Eki (2)
WORD_CAP_EVENTS += (FLOOD, TIDAL)   # 21 Eki (Aşama 5): sel ve kıyı dalga da 175 tavanlı (GPT bütçesi + kod yedeği)
WORD_CAP_EVENTS += METEOR_EVENTS   # 29 Eki: meteor

# ── Ortam havuzu (14 Eki (4), Bahadır; şimdilik sadece çığ) ──────────────────────────────────────────────────────────
# Ders: köy ve kayak videoları birbirinin aynısıydı (aynı balkon korkuluğu, aynı bulut, aynı koşan insanlar). Her
# üretimde dağ, yerleşim, ışık ve kamera noktası koddan seçilir; menüde ek ekran yok, GPT'ye yeni kural yok. Ortam
# satırı stil ekine girer ("Setting: dağ, yerleşim, ışık."). LRU kategori bazında (köy, kayak, orman ortak): her
# eksende son ENV_BLOCK üretimin değerleri elenir, aday kalmazsa 1'e düşer. Ülke, şehir, bayrak, yazı yok (testli).
# 14 Eki, Bahadır: deprem de ortam havuzunda (şehir, sokak, ışık + kamera noktası; EQ_ENV_AXES). LRU her kategoride
# ayrı (çığ ve deprem birbirini elemez).
ENV_EVENTS = AVALANCHE_EVENTS + EARTHQUAKE_EVENTS
ENV_AXES = {
    # 14 Eki (5), Bahadır kararı: "wide rounded snowy highlands" yamaç dik görünmeyebilir; "wide snowy highlands
    # below a steep slope" (Bahadır'ın 10 kelimelik metni 15 kelime sınırına sığmıyordu, kısaltıldı)
    "mountain": ("jagged rocky peaks", "wide snowy highlands below a steep slope", "steep forested slopes",
                 "sheer cliffs above a narrow valley"),
    "village": ("dark timber chalets", "red timber houses", "log cabins and a large lodge", "stone-and-timber houses",
                "tall narrow wooden houses with heavy roofs"),
    "light": ("heavy overcast sky", "falling snow and low cloud", "pale low winter sun",
              "late-afternoon blue-grey light", "bright cold sunny day"),
}
ENV_BLOCK = 2
SETTING_MAX_WORDS = 15
# Beat uyumu: taş BİNA maddeleri (taş dağ evi, taş servis binası, taş çiftlik evi ve ahır kapısı, taş ev) tamamen
# kütük yerleşimde anlamsız; bu maddeler seçilince o yerleşim elenir. Taş ahır (A4) ve istinat duvarı (B4) her
# yerleşimde olur (ahşap köylerde de taş ahır ve duvar bulunur).
STONE_BUILDING_BEATS = {AVALANCHE_VILLAGE: {"B1"}, AVALANCHE_SKI: {"C5"}, AVALANCHE_FOREST: {"E3", "E7"}}   # 18 Eki: E5 -> E7
WOOD_ONLY_VILLAGES = ("log cabins and a large lodge",)
_ENV_MEMORY: list[dict] = []
_ENV_MEMORY_LIMIT = 12
_ENV_LOCK = threading.Lock()

# ── 🏚️ Deprem ortamı (14 Eki, Bahadır). Eksenler: şehir (yerleşim), sokak, ışık; LRU son 2 (aday kalmazsa 1, sonra 0),
# satır en fazla 15 kelime. Uyum (kodda):
# - Apartman olayı: beton/yamaç/cadde apartmanları; "narrow residential street" yok.
# - Eski sokak: tuğla-taş konutlar ve yamaçta eski taş evler (Bahadır: "taş evlerle uyumlu ifade"); "wide avenue" yok.
# - "apartment blocks lining a wide avenue" sadece meydan kenarıyla (sakin sokakla çelişir, "wide avenue" tekrar olur).
# - Beyaz üstüne beyaz: "hazy dusty morning" seçilince şehir koyu tonlu ifadesiyle yazılır (EQ_DARK_CITY).
EQ_ENV_AXES = {
    "city": ("concrete mid-rise apartment blocks", "old brick-and-stone residential buildings",
             "a dense hillside neighbourhood of apartment blocks", "apartment blocks lining a wide avenue",
             "a dense hillside neighbourhood of old stone houses"),
    "light": ("hazy dusty morning", "heavy grey overcast sky", "late-afternoon low sun", "blue dawn light"),
    "street": ("wide avenue", "narrow residential street", "tree-lined square edge", "quiet residential street"),
}
EQ_EVENT_CITIES = {
    EARTHQUAKE_APARTMENT: ("concrete mid-rise apartment blocks", "a dense hillside neighbourhood of apartment blocks",
                           "apartment blocks lining a wide avenue"),
    EARTHQUAKE_OLD_STREET: ("old brick-and-stone residential buildings",
                            "a dense hillside neighbourhood of old stone houses"),
}
EQ_EVENT_STREETS = {
    EARTHQUAKE_APARTMENT: ("wide avenue", "tree-lined square edge", "quiet residential street"),
    EARTHQUAKE_OLD_STREET: ("narrow residential street", "tree-lined square edge", "quiet residential street"),
}
EQ_AVENUE_CITY = "apartment blocks lining a wide avenue"
EQ_AVENUE_STREETS = ("tree-lined square edge",)   # "wide avenue" sokağı şehirde zaten var (tekrar olmasın)
EQ_HAZY_LIGHT = "hazy dusty morning"
EQ_DARK_CITY = {
    "concrete mid-rise apartment blocks": "dark grey concrete mid-rise apartment blocks",
    "a dense hillside neighbourhood of apartment blocks": "a dense hillside neighbourhood of dark apartment blocks",
    "apartment blocks lining a wide avenue": "dark-toned apartment blocks lining a wide avenue",
    "old brick-and-stone residential buildings": "dark old brick-and-stone residential buildings",
    "a dense hillside neighbourhood of old stone houses": "a dense hillside neighbourhood of dark stone houses",
}
_EQ_ENV_MEMORY: list[dict] = []


def _is_eq_env(env: dict) -> bool:
    return "city" in env


def eq_city_text(env: dict) -> str:
    """Prompta giden şehir ifadesi (pus/toz ışığında koyu tonlu)."""
    return EQ_DARK_CITY[env["city"]] if env["light"] == EQ_HAZY_LIGHT else env["city"]


def setting_line(env: dict) -> str:
    if _is_eq_env(env):   # 14 Eki: deprem
        return f"Setting: {eq_city_text(env)}, {env['street']}, {env['light']}."
    return f"Setting: {env['mountain']}, {env['village']}, {env['light']}."


def env_weather(env: dict) -> str:
    """GPT'ye giden WEATHER satırı (ortamın kendisi)."""
    if _is_eq_env(env):
        return f"{eq_city_text(env)}, {env['street']}, {env['light']}"
    return f"{env['mountain']}, {env['village']}, {env['light']}"


def environment_label(env: dict) -> str:
    """Telegram onay/Notion satırı (Bahadır okusun diye; değerler prompttaki İngilizce metin)."""
    if _is_eq_env(env):
        return (f"Ortam: şehir = {eq_city_text(env)} · sokak = {env['street']} · ışık = {env['light']} · "
                f"kamera = {env['spot']}")
    return (f"Ortam: dağ = {env['mountain']} · yerleşim = {env['village']} · ışık = {env['light']} · "
            f"kamera = {env['spot']}")


def _env_memory(event: str) -> list[dict]:
    return _EQ_ENV_MEMORY if event in EARTHQUAKE_EVENTS else _ENV_MEMORY


def _lru_candidates(values, used: list) -> list:
    for depth in (ENV_BLOCK, 1, 0):
        blocked = set(used[-depth:]) if depth else set()
        left = [v for v in values if v not in blocked]
        if left:
            return left
    return list(values)


def choose_env_spot(event: str, spots: list[str], rng: random.Random | None = None,
                    used: list[str] | None = None) -> str:
    """Kamera noktası ekseni: kategoride son ENV_BLOCK üretimin noktaları elenir (aday kalmazsa 1). used: 21 Eki,
    Notion'dan kurulan kategori geçmişi (eskiden yeniye); None ise süreç hafızası."""
    rng = rng or random
    if used is None:
        with _ENV_LOCK:
            used = [m["spot"] for m in _env_memory(event)]
    return rng.choice(_lru_candidates(spots, [u for u in used if u]))


def choose_environment(event: str, spot: str, b2: str, b3: str, rng: random.Random | None = None,
                       mem: list[dict] | None = None) -> dict:
    """Dağ, yerleşim, ışık: LRU + beat uyumu + satır en fazla SETTING_MAX_WORDS kelime. Aday kalmazsa StructureError.
    mem: 21 Eki, Notion'dan kurulan kategori ortam geçmişi (eskiden yeniye); None ise süreç hafızası."""
    rng = rng or random
    if event in EARTHQUAKE_EVENTS:
        return _choose_eq_environment(event, spot, rng, mem)
    if mem is None:
        with _ENV_LOCK:
            mem = list(_ENV_MEMORY)
    mem = [m for m in mem if m and all(m.get(a) for a in ("mountain", "village", "light"))]
    villages = ENV_AXES["village"]
    if {b2, b3} & STONE_BUILDING_BEATS.get(event, set()):
        villages = tuple(v for v in villages if v not in WOOD_ONLY_VILLAGES)
    cands = {"mountain": _lru_candidates(ENV_AXES["mountain"], [m["mountain"] for m in mem]),
             "village": _lru_candidates(villages, [m["village"] for m in mem]),
             "light": _lru_candidates(ENV_AXES["light"], [m["light"] for m in mem])}
    combos = [{"mountain": m, "village": v, "light": li} for m in cands["mountain"] for v in cands["village"]
              for li in cands["light"]
              if len(setting_line({"mountain": m, "village": v, "light": li}).split()) <= SETTING_MAX_WORDS]
    if not combos:
        raise StructureError(f"{event}: ortam adayı kalmadı ({cands})")
    return {**rng.choice(combos), "spot": spot}


def _choose_eq_environment(event: str, spot: str, rng, mem: list[dict] | None = None) -> dict:
    """Deprem: şehir, sokak, ışık. Her eksende son ENV_BLOCK üretimin değeri elenir; uyumlu ve en fazla 15 kelimelik
    üçlü kalmazsa derinlik birlikte 1'e, sonra 0'a düşer."""
    if mem is None:
        with _ENV_LOCK:
            mem = list(_EQ_ENV_MEMORY)
    mem = [m for m in mem if m and all(m.get(a) for a in ("city", "street", "light"))]
    for depth in (ENV_BLOCK, 1, 0):
        recent = mem[-depth:] if depth else []
        blocked = {a: {m[a] for m in recent} for a in ("city", "street", "light")}
        combos = []
        for c in EQ_EVENT_CITIES[event]:
            for st in EQ_EVENT_STREETS[event]:
                for li in EQ_ENV_AXES["light"]:
                    if c in blocked["city"] or st in blocked["street"] or li in blocked["light"]:
                        continue
                    if c == EQ_AVENUE_CITY and st not in EQ_AVENUE_STREETS:
                        continue
                    env = {"city": c, "street": st, "light": li}
                    if len(setting_line(env).split()) <= SETTING_MAX_WORDS:
                        combos.append(env)
        if combos:
            return {**rng.choice(combos), "spot": spot}
    raise StructureError(f"{event}: deprem ortam adayı kalmadı")


def remember_environment(env: dict) -> None:
    mem = _EQ_ENV_MEMORY if _is_eq_env(env) else _ENV_MEMORY
    with _ENV_LOCK:
        mem.append(dict(env))
        del mem[:-_ENV_MEMORY_LIMIT]


# ── ☄️ Meteor ortam ekseni (29 Eki, Bahadır; metinler birebir). Kadraj = kamera noktası (spot, son 2 hariç), ışık =
# iskeletin hava listesi (son 2 hariç), ortam = aşağıdaki 4 seçenek (son 2 hariç, olayın eksen geçmişindeki "env").
# Stil ekine "Setting: ortam, ışık." satırı, GPT'ye PLACE satırı olarak gider.
METEOR_ENVS = {"O1": "white modern Mediterranean villas with glass railings and pools",
               "O2": "modern glass houses stepped down a green hillside",
               "O3": "a palm-lined coastal suburb of modern homes"}
# 29 Eki (3), Bahadır: O4 pasif (2. test videosunda yüksek kuleler sebepsiz yer ve şekil değiştirdi). Kimlik tekrar
# kullanılmaz; eski Notion kaydındaki "O4" tekrar önlemede zararsız.
METEOR_RETIRED_ENVS = {"O4": "modern seafront apartment towers and low houses along a promenade"}
SETTING_EVENTS = ENV_EVENTS + METEOR_EVENTS   # build_spec: ortam satırı taşıyabilen olaylar


def choose_meteor_env(rng: random.Random | None = None, used: list[str] | None = None) -> str:
    """Meteor ortamı: son 2 üretimin ortamı elenir (lru_axis), kalanlardan rastgele."""
    return (rng or random).choice(lru_axis(list(METEOR_ENVS), used or [])[0])


def meteor_setting(env: str, light: str) -> str:
    return f"Setting: {METEOR_ENVS[env]}, {light}."


# ── 🔥 Ateş hortumu ortam ekseni (16 Eki, Bahadır) ────────────────────────────────────────────────────────────────
# Ders: canlı üretimlerde hortum ilk 10 sn boş yanan tarlada ilerledi, ev en sonda göründü (kilit cümle "burning
# roadside ... a field of flames", noktalar "valley road"). Sahne her zaman içinde ev olan, ağaçlık bir yerleşim; açık
# arazi yok. Her ortamın kendi kilit cümlesi ve iki kamera noktası var. LRU: son FIRE_TOR_ENV_BLOCK ortam elenir (3
# ortamda art arda aynı ortam gelmez). Süreç hafızası (çığ gibi). Kilit cümlelerde ve noktalarda açık arazi sözcüğü yok,
# her kilit cümlede ev ve ağaç birlikte (testli). Stil ekinde "Setting:" satırı yok: ortam kilit cümle + yer metni +
# kamera noktasıyla söylenir.
FIRE_TOR_ENVS = {
    "forest_edge": {"label": "orman kenarı yerleşim",
                    "key": EVENT_KEY_VISUAL[FIRE_TORNADO],
                    "spots": ("High balcony at the edge of a wooded neighborhood",
                              "Rooftop terrace above a wooded residential area")},
    "tree_street": {"label": "ağaçlık mahalle sokağı",
                    "key": "A colossal spinning fire tornado, a twisting funnel several times taller than the houses "
                           "and trees, tears down a burning tree-lined street, its wide base engulfing the houses and "
                           "cars along it.",
                    "spots": ("High balcony over a tree-lined residential street",
                              "Upper-floor terrace above a street of houses")},
    "village_woods": {"label": "köy kenarı, çevresi orman",
                      "key": "A colossal spinning fire tornado, a twisting funnel several times taller than the houses "
                             "and trees, tears from the burning woods into a village, its wide base engulfing the first "
                             "houses and trees.",
                      "spots": ("Hillside terrace above a village", "High balcony of a village house")},
}
FIRE_TOR_ENV_BLOCK = 2
# Kilit cümlede, yer metninde ve kamera noktasında olmaması gereken açık arazi sözcükleri (testli)
FIRE_TOR_OPEN_LAND = ("field", "roadside", "meadow", "farm", "farmland", "open land", "valley road", "pasture",
                      "prairie", "grassland", "empty lot", "vacant lot", "wasteland")
_FIRE_TOR_ENV_MEMORY: list[str] = []


def fire_env_of_spot(spot: str) -> str:
    for name, env in FIRE_TOR_ENVS.items():
        if spot in env["spots"]:
            return name
    raise StructureError(f"Ateş hortumu kamera noktası hiçbir ortamda yok: {spot}")


def choose_fire_env(rng: random.Random | None = None, used: list[str] | None = None) -> str:
    """Ortam: son FIRE_TOR_ENV_BLOCK üretimin ortamları elenir (aday kalmazsa 1, sonra 0). used: 21 Eki, Notion
    geçmişi (eskiden yeniye); None ise süreç hafızası."""
    if used is None:
        with _ENV_LOCK:
            used = list(_FIRE_TOR_ENV_MEMORY)
    used = [u for u in used if u]
    return (rng or random).choice(_lru_candidates_depth(list(FIRE_TOR_ENVS), used, FIRE_TOR_ENV_BLOCK))


def _lru_candidates_depth(values, used: list, block: int) -> list:
    for depth in (block, 1, 0):
        blocked = set(used[-depth:]) if depth else set()
        left = [v for v in values if v not in blocked]
        if left:
            return left
    return list(values)


def remember_fire_env(name: str) -> None:
    with _ENV_LOCK:
        _FIRE_TOR_ENV_MEMORY.append(name)
        del _FIRE_TOR_ENV_MEMORY[:-_ENV_MEMORY_LIMIT]


def fire_env_label(name: str, spot: str) -> str:
    """Telegram onay/Notion satırı (çığ/deprem biçimi)."""
    return f"Ortam: {FIRE_TOR_ENVS[name]['label']} ({name}) · kamera = {spot}"


# ── 🌋 Bombalar ve kül bulutu ortam ekseni + yer ağırlığı + ışık (18 Eki (3), Bahadır) ─────────────────────────────
# Hep aynı köy sokağı ve aynı gökyüzü çıkıyordu; yer eşit ağırlıkla, hafızasız seçiliyordu. Ortam (sk.VOLC_ENVS) kamera
# cümlesine ve GPT'nin PLACE satırına girer, kilit cümleye girmez. LRU: son VOLC_ENV_BLOCK ortam ve son VOLC_SPOT_BLOCK
# yer elenir (aday kalmazsa daha sığ), kalanlar ağırlıklı seçilir. Süreç hafızası (ateş hortumu gibi); yer geçmişi
# Notion kayıtlarından da okunur (combo_key'de yer var). Hava ağırlıklı rastgele (sk.VOLCANO_WEATHER_WEIGHTS).
VOLC_ENV_EVENTS = (PYROCLASTIC, VOLCANIC_BOMBS)
VOLC_ENV_BLOCK = 2
VOLC_SPOT_BLOCK = 2   # 21 Eki (Gece 1 / Aşama 3): tüm eksenlerde son 2 (önceki 1); ağırlıklar aynı
_VOLC_ENV_MEMORY: dict[str, list[str]] = {}
_VOLC_SPOT_MEMORY: dict[str, list[str]] = {}


def _weighted_choice(weights: dict[str, int], allowed: list[str], rng) -> str:
    keys = [k for k in weights if k in allowed]
    return (rng or random).choices(keys, weights=[weights[k] for k in keys], k=1)[0]


def choose_volc_env(event: str, rng: random.Random | None = None, used: list[str] | None = None) -> str:
    """Ortam: son VOLC_ENV_BLOCK üretimin ortamı elenir, kalanlardan ağırlıklı (olay başına ayrı hafıza). used: 21 Eki,
    Notion geçmişi (eskiden yeniye); None ise süreç hafızası."""
    if used is None:
        with _ENV_LOCK:
            used = list(_VOLC_ENV_MEMORY.get(event, []))
    used = [u for u in used if u]
    weights = VOLC_ENV_WEIGHTS[event]
    return _weighted_choice(weights, _lru_candidates_depth(list(weights), used, VOLC_ENV_BLOCK), rng)


def remember_volc_env(event: str, name: str) -> None:
    with _ENV_LOCK:
        mem = _VOLC_ENV_MEMORY.setdefault(event, [])
        mem.append(name)
        del mem[:-_ENV_MEMORY_LIMIT]


def volc_spot_weight(spot: str) -> int:
    return VOLC_SPOT_WEIGHTS[VOLC_SPOT_KIND[spot]]


def volc_spot_history(event: str, history: list[str]) -> list[str]:
    """Olayın yer geçmişi, eskiden yeniye: Notion kayıtları (combo_key) + süreç hafızası (daha yeni)."""
    with _ENV_LOCK:
        memory = list(_VOLC_SPOT_MEMORY.get(event, []))
    spots = {sp.lower(): sp for sp in EVENT_SKELETONS[event]["spots"]}
    notion = []
    for h in history or []:
        parts = (h or "").split("|")
        if len(parts) == 5 and parts[2].strip().lower() == event.lower():
            sp = spots.get(parts[3].split("#")[0].strip().lower())
            if sp:
                notion.append(sp)
    return notion + memory


def choose_volc_spot(event: str, history: list[str] | None = None, rng: random.Random | None = None,
                     used: list[str] | None = None) -> str:
    """Kamera noktası: son VOLC_SPOT_BLOCK yer elenir; kalanlardan ağırlıklı (balkon 2, çatı/yamaç 1). used: 21 Eki,
    Notion eksen geçmişi (eskiden yeniye); None ise combo_key geçmişi + süreç hafızası."""
    spots = list(EVENT_SKELETONS[event]["spots"])
    if used is None:
        used = volc_spot_history(event, history or [])
    left = _lru_candidates_depth(spots, [u for u in used if u], VOLC_SPOT_BLOCK)
    return _weighted_choice({sp: volc_spot_weight(sp) for sp in spots}, left, rng)


def remember_volc_spot(event: str, spot: str) -> None:
    with _ENV_LOCK:
        mem = _VOLC_SPOT_MEMORY.setdefault(event, [])
        mem.append(spot)
        del mem[:-_ENV_MEMORY_LIMIT]


def choose_volc_weather(event: str, rng: random.Random | None = None, used: list[str] | None = None) -> str:
    """Işık: ağırlıklı; 21 Eki: son AXIS_BLOCK ışık elenir (lru_axis), ağırlıklar aynı."""
    weights = VOLCANO_WEATHER_WEIGHTS[event]
    return _weighted_choice(weights, lru_axis(list(weights), used or [])[0], rng)


def volc_env_label(name: str, spot: str) -> str:
    """Telegram onay/Notion gövde satırı (ateş hortumu biçimi)."""
    return f"Ortam: {VOLC_ENVS[name]['label']} ({name}) · kamera = {spot}"


def volc_place(event: str, name: str) -> str:
    """GPT'ye giden PLACE: ortam metni + volkana göre konum (iskelet yer metninin sonu)."""
    tail = "on the lower flank of the volcano" if event == PYROCLASTIC else "below the erupting volcano"
    return f"{VOLC_ENVS[name]['text']}, {tail}"


def expected_key_visual(event: str, spot: str, opening: str | None = None) -> str:
    """Spec'in kilit cümlesi: ateş hortumunda kamera noktasının ortamından (16 Eki), diğer olaylarda sabit. Bilinmeyen
    olayda boş metin (son denetim tutmaz)."""
    if event == FIRE_TORNADO:
        return FIRE_TOR_ENVS[fire_env_of_spot(spot)]["key"]
    if opening and opening != "A":   # 21 Eki (Aşama 6): açılış varyantı (core/opening_axis.py); A = bugünkü
        from core.opening_axis import text as opening_text
        return opening_text(event, opening)
    return EVENT_KEY_VISUAL.get(event, "")


def event_key_visual(event: str, fire_env: str | None = None) -> str:
    """Olayın kilit cümlesi. Ateş hortumunda seçilen ortamınki (16 Eki), diğer olaylarda EVENT_KEY_VISUAL."""
    if event == FIRE_TORNADO and fire_env is not None:
        return FIRE_TOR_ENVS[fire_env]["key"]
    return EVENT_KEY_VISUAL[event]
# Orman ve cephe yangınında araç havalanmaz (Bahadır onayı, 8 Eki): 4-9s'de kalkma ifadesi reddedilir
NO_LIFT_SLICE = {WILDFIRE: ("slice_2",), FACADE_FIRE: ("slice_2",),
                 HELICOPTER: ("slice_2",)}   # 10 Eki: helikopterde de araç havalanmaz
# Helikopter (10 Eki, Bahadır): ıslaklığın sebebi yağmur değil, helikopterin bıraktığı su. Bu olayda su bırakma
# ıslaklığı (wet, soak, drench...) serbest ve "rain" fiili suyla birlikte de geçebilir ("water rains down"); yağış
# ("heavy rain", downpour, rainfall, rain-soaked...) yine reddedilir.
WATER_DROP_EVENTS = (HELICOPTER,)
_WATER_DROP_OK = ("wet", "wetness", "soak", "drench", "waterlogged", "puddle", "damp")
_WATER_FALLING_OK = ("water", "spray", "droplet", "load")
_FIRE_NO_LIFT = ("lift", "hoist", "airborne", "off its wheels", "off the ground", "swept up", "sweep up", "sweeps up",
                 "levitate")


def rain_words(text: str, water_drop: bool = False) -> list[str]:
    """Yağış/ıslaklık ifadeleri. Yanan/düşen bir nesnenin yanında (±3 kelime) geçen "rain" fiili sayılmaz.
    water_drop (helikopter, 10 Eki): su bırakma ıslaklığı serbest, "rain" suyla birlikte de serbest; yağış yasak."""
    wet = tuple(w for w in _FIRE_WET if w not in _WATER_DROP_OK) if water_drop else _FIRE_WET
    falling_ok = _RAIN_FALLING_OK + (_WATER_FALLING_OK if water_drop else ())
    found = find_terms(wet, text)
    tokens = re.findall(r"[a-z]+(?:-[a-z]+)*", (text or "").lower())
    for i, tok in enumerate(tokens):
        if tok in _RAIN_TOKENS:
            near = tokens[max(0, i - _RAIN_WINDOW):i] + tokens[i + 1:i + 1 + _RAIN_WINDOW]
            if not any(w.startswith(ok) for w in near for ok in falling_ok):
                found.append(tok)
    return list(dict.fromkeys(found))

# ── Olaya özel dilim kapıları (4 Eki, Bahadır onayı): terimlerden biri dilimde geçmeli. Çekimler otomatik
# (find_terms). "people": True olan kuralın terimi koddan gelir: spec'teki N'in sayı kelimesi (kod N'i olayın kişi
# aralığından seçer, GPT cümleye döker). "away_from": kaçılan şey (mesaj satırı ve geri bildirim). ───────────────
NUMBER_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}   # 15 Eki (2): ateş hortumu 2-3
_FLEE = ("run", "ran", "running", "flee", "fled", "fleeing", "sprint", "scatter", "dash", "bolt", "race",
         # 4 Eki, Bahadır: kuru provada "scramble", "darting" reddedildi. "rush" YOK (su da "rushes")
         "scramble", "dart", "hurry")


def _people_rules(away_from: str) -> list[dict]:
    return [
        {"rule": "slice_flee", "field": "slice_1_rest", "terms": _FLEE,
         "missing": "0-4s: insanların kaçışı",
         "feedback": f"'slice_1_rest' must show people running away from {away_from}."},
        {"rule": "slice_count", "field": "slice_1_rest", "people": True, "away_from": away_from,
         "missing": "0-4s: kaçan kişi sayısı ({word})",
         "feedback": "'slice_1_rest' must say that {word} people run away from " + away_from + "."},
    ]


# ❄️ Çığ (14 Eki, Bahadır, ilk test dersi): 0-4s'deki insan cümlesi kameraya yakın yeri söyler ("near the railing",
# "in the street below"). Bahadır kararı: b kuralı korunur, "camera" kelimesi hikâyede yine yasak; yakınlık
# korkuluk/sokak/teras ile söylenir. Eş anlamlılar ekleme; yakınlık bildirmeyen cümle reddedilir.
# 22 Eki, Bahadır (genel kalite devam): kaçanlar kameranın yanında değil, aşağıdaki sokakta ve karenin alt yarısında
# ("no person or face close to the camera" ile çelişmesin). Korkuluk / teras / balkon ifadeleri listeden çıktı (kontrol
# gevşemedi: kalan ifadelerin hepsi aynı); "lower half" ve "street below" eklendi. Önceki ilk terimler: "near the
# railing", "by the railing", ..., "close to the terrace", "beneath the balcony".
# 22 Eki, Bahadır: "in the foreground" çıktı (yüz yasağıyla çelişiyor); diğerleri aynı.
_AVA_NEAR = ("right below", "just below", "in the street below", "on the street below",
             "right beneath", "just beneath", "street below", "lower half")
_AVA_NEAR_RULE = {"rule": "slice_near_camera", "field": "slice_1_rest", "terms": _AVA_NEAR,
                  "missing": "0-4s: insanlar aşağıdaki sokakta değil",
                  "feedback": "'slice_1_rest' must place the running people in the street right below, in the lower "
                              "half of the frame (never use the word camera)."}
# 🔥 Ateş hortumu (16 Eki, ortam ekseni): yakınlık yeni mekânlara göre (evlerin arası, aşağıdaki bahçe/avlu, balkonun/
# terasın hemen altı, aşağıdaki sokak). Çığ/deprem listesi değişmez; "road below" tek başına yakın sayılmaz.
_FIRE_TOR_NEAR = _AVA_NEAR + ("between the houses", "between the nearby houses", "among the houses below",
                              "in the yard below", "in the yards below", "across the yard below", "through the yard below",
                              "in the garden below", "in the gardens below", "through the garden below",
                              "across the garden below", "along the street below", "down the street below",
                              "across the street below", "through the street below", "street right below",
                              "street just below")
_FIRE_TOR_NEAR_RULE = {**_AVA_NEAR_RULE, "terms": _FIRE_TOR_NEAR}

SLICE_RULES = {
    TIDAL: _people_rules("the wave"),
    # TASLAK (4 Eki, heyelan)
    MUDSLIDE: _people_rules("the mud"),
    SLOPE: _people_rules("the mud"),
    VILLAGE: _people_rules("the mud"),
    # TASLAK (4 Eki, hortum)
    LANDFALL: _people_rules("the tornado"),
    MARINA_TORNADO: _people_rules("the tornado"),
    AVENUE: _people_rules("the tornado"),
    # TASLAK (8 Eki, yangın): mevcut kaçış listesi (_FLEE, "rush" yok)
    WILDFIRE: _people_rules("the flames"),
    FACADE_FIRE: _people_rules("the flames"),
    # 15 Eki (2), Bahadır: ateş hortumunda 2-3 kişi ön planda kaçar (çığdaki yakınlık kapısının aynısı)
    # 16 Eki: yakınlık listesi yerleşim mekânlarına göre (_FIRE_TOR_NEAR_RULE)
    FIRE_TORNADO: _people_rules("the fire tornado") + [_FIRE_TOR_NEAR_RULE],
    HELICOPTER: _people_rules("the flames"),   # 10 Eki: orman gibi
    # 10 Eki: volkan, insanlar kaçar (mevcut _FLEE); kimse lav/taşla temas etmez
    ERUPTION: _people_rules("the eruption"),
    PYROCLASTIC: _people_rules("the cloud"),
    VOLCANIC_BOMBS: _people_rules("the falling rocks"),
    # 13 Eki: çığ, insanlar çığdan kaçar (mevcut _FLEE); kurtarma yok
    # 14 Eki, Bahadır: insanlar ön planda, kameraya yakın (_AVA_NEAR_RULE)
    AVALANCHE_VILLAGE: _people_rules("the avalanche") + [_AVA_NEAR_RULE],
    AVALANCHE_SKI: _people_rules("the avalanche") + [_AVA_NEAR_RULE],
    AVALANCHE_FOREST: _people_rules("the avalanche") + [_AVA_NEAR_RULE],
    # 14 Eki: deprem, insanlar kameraya yakın (çığdaki yakınlık kapısının aynısı)
    EARTHQUAKE_APARTMENT: _people_rules("the collapsing buildings") + [_AVA_NEAR_RULE],
    EARTHQUAKE_OLD_STREET: _people_rules("the collapsing buildings") + [_AVA_NEAR_RULE],
    # 29 Eki: meteor, kamera yüksekte; insanlar aşağıdaki sokakta kaçar (her karede insan, ön planda yüz yok)
    METEOR: _people_rules("the impact") + [_AVA_NEAR_RULE],
}


def has_people_rule(event: str) -> bool:
    return any(r.get("people") for r in SLICE_RULES.get(event, ()))


def choose_people(event: str, ship: str | None, rng: random.Random | None = None,
                  used: list[int] | None = None) -> int | None:
    """Kaçan kişi sayısı N (olayın kişi aralığından); kişi kuralı olmayan olayda None."""
    if not has_people_rule(event):
        return None
    lo, hi = count_range(event, ship)
    # 21 Eki: son AXIS_BLOCK sayı elenir. choice(range listesi) boş geçmişte randint ile aynı çekimi yapar
    return (rng or random).choice(lru_axis(list(range(lo, hi + 1)), used or [])[0])


class StructureError(RuntimeError):
    """Yapılandırılmış hat verisi/çıktısı kullanılamaz; Kie'ye gidilmez (sessiz yedek yok)."""


class StructuredRejectError(StructureError):
    """Preflight ya da Kie içerik filtresi, bizim yazarın tek yeniden yazımından sonra da reddetti. Akış durur:
    run_pipeline yeni senaryo denemez (Bahadır onayı, 4 Eki: "bir kez yeniden çağır, ikinci retta dur ve bildir")."""


def structured_events() -> tuple[str, ...]:
    return tuple(EVENT_KEY_VISUAL)


def is_structured(event: str) -> bool:
    return event in EVENT_KEY_VISUAL


# ── Terim eşleşmesi (creative_pipeline ile aynı çekim kuralı) ───────────────────────────────────────────────
def find_terms(terms, text: str) -> list[str]:
    from core.creative_pipeline import find_terms as _find
    return _find(terms, text)


def missing_term_groups(groups, text: str) -> list[tuple[str, ...]]:
    return [g for g in groups if not find_terms(g, text)]


def beat_missing(beat: dict, text: str) -> list[tuple[str, ...]]:
    """Maddenin görünmeyen terim grupları. 15 Eki (4): "unless" (isteğe bağlı, şimdilik sadece ateş hortumu T3)
    terimlerinden biri geçerse cümle başka maddeyi anlatıyordur; o terimler eksik grup gibi döner."""
    out = missing_term_groups(beat["terms"], text)
    hit = find_terms(beat.get("unless", ()), text)
    return out + ([("unless",) + tuple(hit)] if hit else [])


# ── Seçim ───────────────────────────────────────────────────────────────────────────────────────────────────
_BEAT_MEMORY: dict[str, list[str]] = {}
_BEAT_MEMORY_LIMIT = 12
_BEAT_LOCK = threading.Lock()


def beat_tag(b2: str, b3: str) -> str:
    return f"{b2}+{b3}"


def beats_of_combo(combo_key: str) -> str | None:
    """combo_key yer parçasındaki olay çifti ("spot#görünüm#V3+D5"), yoksa None."""
    parts = (combo_key or "").split("|")
    if len(parts) != 5:
        return None
    place = parts[3].split("#")
    if len(place) < 3 or not re.fullmatch(r"[A-Z]\d+\+[A-Z]\d+", place[2].strip().upper()):
        return None
    return place[2].strip().upper()


def remember_beats(event: str, tag: str) -> None:
    with _BEAT_LOCK:
        _BEAT_MEMORY.setdefault(event, []).append(tag)
        del _BEAT_MEMORY[event][:-_BEAT_MEMORY_LIMIT]


def beat_history(event: str, history: list[str]) -> list[str]:
    """Olayın olay çifti geçmişi, eskiden yeniye: Notion combo_key'leri + süreç hafızası (hafıza daha yeni)."""
    same = [h for h in history if len(h.split("|")) == 5 and h.split("|")[2].strip().lower() == event.lower()]
    with _BEAT_LOCK:
        memory = list(_BEAT_MEMORY.get(event, []))
    notion = [t for t in (beats_of_combo(h) for h in same) if t and t not in memory]
    return notion + memory


def allowed_pairs(event: str, view: str | None, spot: str) -> list[tuple[str, str]]:
    b = EVENT_BEATS[event]
    def ok3(d):
        return view not in b["excluded_views"].get(d, set()) and spot not in b["excluded_spots"].get(d, set())

    def ok2(v):   # 10 Eki: kamera noktası dışlaması 4-9s maddesinde de olabilir (helikopter F2/F5)
        return spot not in b["excluded_spots"].get(v, set())
    off = DISABLED_BEATS.get(event, set())   # 29 Eki: bayrakla kapalı beat'ler (meteor [DALGA])
    return [(v, d) for v in b["slice_2"] for d in b["slice_3"]
            if (v, d) not in b["excluded_pairs"] and ok2(v) and ok3(d) and v not in off and d not in off]


def choose_beats(event: str, view: str | None, spot: str, history: list[str],
                 rng: random.Random | None = None) -> tuple[str, str]:
    """İzinli çiftler içinden: son RECENT_BEAT_BLOCK üretimde geçen 4-9s/9-15s olayları elenir, kalanlardan en uzun
    süredir kullanılmayan çift (eşitlikte rastgele). Aday kalmazsa StructureError (yedek yok)."""
    rng = rng or random
    seen = beat_history(event, history)
    depth = RECENT_BEAT_BLOCK_BY_EVENT.get(event, RECENT_BEAT_BLOCK)
    # 14 Eki: deprem olaylarında aday kalmazsa derinlik 1'e düşer; diğer olaylarda tek deneme (davranış aynı)
    depths = [depth] + ([1] if event in BEAT_BLOCK_FALLBACK_EVENTS and depth > 1 else [])
    for d in depths:
        recent = seen[-d:] if d else []
        blocked2 = {t.split("+")[0] for t in recent}
        blocked3 = {t.split("+")[1] for t in recent}
        pairs = [p for p in allowed_pairs(event, view, spot) if p[0] not in blocked2 and p[1] not in blocked3]
        if pairs:
            break
    if not pairs:
        raise StructureError(f"{event}: seçilebilir olay çifti kalmadı (görünüm={view}, yer={spot}, son={recent})")

    def last(p):
        return max((i for i, t in enumerate(seen) if t == beat_tag(*p)), default=-1)
    best = min(last(p) for p in pairs)
    return rng.choice([p for p in pairs if last(p) == best])


def choose_vehicle(view: str, rng: random.Random | None = None, used: list[str] | None = None,
                   exclude: list[str] = ()) -> str:
    if view not in REGION_VEHICLES:
        raise StructureError(f"Görünümün araç listesi yok: {view}")
    return (rng or random).choice(lru_axis(_vehicle_options(REGION_VEHICLES[view], exclude), used or [])[0])


# 23 Eki, Bahadır (heyelan testi): seçilen çiftte sabit geçen araçla (M8 "a parked truck", S7 "a stopped truck") aynı
# türdeki araç seçilmez ("the pickup truck ... a parked truck" iki kamyon). Şimdilik heyelan olaylarında; diğer
# olaylarda (sel/dev dalga sedan + "car", hortum P7 ve volkan S8/T9 kamyon) davranış aynı.
VEHICLE_KINDS = (("truck", "lorry", "pickup"), ("car", "sedan", "saloon", "hatchback"), ("van",), ("suv",))
SAME_KIND_VEHICLE_EVENTS = {MUDSLIDE, SLOPE, VILLAGE}
# 23 Eki, Bahadır (hortum denetimi): açılıştaki sabit araç da sayılır (marina C "drags a pickup truck along the quay").
# Şimdilik sadece marina; diğer olayların açılış-araç çakışmaları raporda
SAME_KIND_OPENING_EVENTS = {MARINA_TORNADO}


def clashing_vehicles(event: str, view: str | None, b2: str, b3: str, opening_text: str | None = None) -> list[str]:
    """Olay çiftinin (ve açılışın) sabit araçlarıyla ({vehicle} dışında) aynı türdeki araç adları; bunlar seçilmez."""
    texts = []
    if event in SAME_KIND_VEHICLE_EVENTS:
        beats = EVENT_BEATS[event]
        texts += [beats[s][b]["text"].replace("{vehicle}", "") for s, b in (("slice_2", b2), ("slice_3", b3))]
    if opening_text and event in SAME_KIND_OPENING_EVENTS:
        texts.append(opening_text)
    if not texts:
        return []
    fixed = " ".join(texts)
    kinds = [set(k) for k in VEHICLE_KINDS if find_terms(k, fixed)]
    return [v for v, terms in event_vehicles(event, view) if any(k & set(terms) for k in kinds)]


def _vehicle_options(vehicles, exclude) -> list[str]:
    out = [v for v, _ in vehicles if v not in exclude]
    if not out:
        raise StructureError(f"Seçilebilir araç kalmadı (elenen: {list(exclude)})")
    return out


def vehicle_terms(view: str, vehicle: str) -> tuple[str, ...]:
    for v, terms in REGION_VEHICLES.get(view, []):
        if v == vehicle:
            return terms
    raise StructureError(f"Araç görünümde yok: {vehicle} / {view}")


# Görünümü olmayan olaylar (TASLAK, 4 Eki, heyelan): araç olayın kendi listesinden (EVENT_VEHICLES).
def event_vehicles(event: str, view: str | None) -> list[tuple[str, tuple[str, ...]]]:
    """Olayın araç listesi: görünüm varsa görünümün (REGION_VEHICLES), yoksa olayın (EVENT_VEHICLES)."""
    if view is not None:
        if view not in REGION_VEHICLES:
            raise StructureError(f"Görünümün araç listesi yok: {view}")
        return REGION_VEHICLES[view]
    if event not in EVENT_VEHICLES:
        raise StructureError(f"Olayın araç listesi yok: {event}")
    return EVENT_VEHICLES[event]


def choose_event_vehicle(event: str, rng: random.Random | None = None, used: list[str] | None = None,
                         exclude: list[str] = ()) -> str:
    return (rng or random).choice(lru_axis(_vehicle_options(event_vehicles(event, None), exclude), used or [])[0])


def uses_vehicle(event: str) -> bool:
    """Olay havuzunda {vehicle} geçen madde var mı. Yoksa (13 Eki: lav, kül bulutu) araç seçilmez, GPT'ye gitmez."""
    b = EVENT_BEATS[event]
    return any("{vehicle}" in beat["text"] for slot in ("slice_2", "slice_3") for beat in b[slot].values())


def spec_vehicle_terms(spec: dict) -> tuple[str, ...]:
    if spec["vehicle"] is None:
        return ()
    for v, terms in event_vehicles(spec["event"], spec["view"]):
        if v == spec["vehicle"]:
            return terms
    raise StructureError(f"Araç listede yok: {spec['vehicle']} / {spec['event']} / {spec['view']}")


def structure_views(event: str) -> list[str | None]:
    """Olayın görünümleri: bölge görünümlü olaylarda 6 görünüm, diğerlerinde [None]."""
    return list(REGION_VIEWS) if event in REGION_VIEW_EVENTS else [None]


def beat_text(event: str, slot: str, beat_id: str, vehicle: str | None = None) -> str:
    return EVENT_BEATS[event][slot][beat_id]["text"].format(vehicle=vehicle or "")


# ── GPT çıktısı: strict JSON şeması ──────────────────────────────────────────────────────────────────────────
SLICE_SCHEMA = {
    "name": "story_slices",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {f: {"type": "string"} for f in SLICE_FIELDS},
        "required": list(SLICE_FIELDS),
        "additionalProperties": False,
    },
}
# 21 Eki (Aşama 7): caption alanları aynı strict şemada (ek GPT çağrısı yok). Hikâye alanları ve kapıları aynı.
from core.caption import CAPTION_FIELDS as _CAPTION_FIELDS, schema_properties as _caption_props   # noqa: E402
SLICE_SCHEMA["schema"]["properties"].update(_caption_props())
SLICE_SCHEMA["schema"]["required"] = list(SLICE_FIELDS) + list(_CAPTION_FIELDS)


def parse_slices(raw) -> dict[str, str]:
    """GPT yanıtı → {alan: metin}. Biçim hatası StructureError (geri bildirimle düzeltilmez, akış durur).
    21 Eki (Aşama 7): yanıt caption alanlarını da taşıyabilir (core.caption.CAPTION_FIELDS); hikâye dilimleri aynı."""
    if not isinstance(raw, dict):
        raise StructureError(f"GPT yanıtı nesne değil: {type(raw).__name__}")
    from core.caption import CAPTION_FIELDS
    keys = set(raw)
    if keys == set(SLICE_FIELDS) | set(CAPTION_FIELDS):
        keys = set(SLICE_FIELDS)
    if keys != set(SLICE_FIELDS):
        raise StructureError(f"GPT yanıtı alanları hatalı: eksik={sorted(set(SLICE_FIELDS) - keys)}, "
                             f"fazla={sorted(keys - set(SLICE_FIELDS))}")
    out = {}
    for f in SLICE_FIELDS:
        v = raw[f]
        if not isinstance(v, str) or not v.strip():
            raise StructureError(f"GPT yanıtında '{f}' boş ya da metin değil")
        out[f] = clean_slice(v)
    return out


def clean_slice(text: str) -> str:
    """Boşlukları tekler, sondaki noktalama tek noktaya iner (birleştirmede '!.' gibi kırık metin olmasın)."""
    t = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"[.!?…]+$", "", t).rstrip() + "."


# ── Birleştirme ve spec ─────────────────────────────────────────────────────────────────────────────────────
def build_spec(event: str, ship: str | None, spot: str, view: str | None, b2: str, b3: str, vehicle: str,
               people: int | None = None, setting: str | None = None, volc_env: str | None = None,
               frame: dict | None = None, scene_env: str | None = None, opening: str | None = None) -> dict:
    """Kie'ye gidecek prompt'u kuran ve denetleyen her şey (slices hariç). people: kaçan kişi sayısı N (sadece
    kişi kuralı olan olaylarda, zorunlu)."""
    if not is_structured(event):
        raise StructureError(f"Yapılandırılmış olay değil: {event}")
    if has_people_rule(event) != (people is not None):
        raise StructureError(f"Kaçan kişi sayısı uyuşmuyor: {event} / {people}")
    if uses_vehicle(event) != (vehicle is not None):   # 13 Eki: araçsız olayda araç yok
        raise StructureError(f"Araç uyuşmuyor: {event} / {vehicle}")
    if setting is not None and (event not in SETTING_EVENTS or len(setting.split()) > SETTING_MAX_WORDS):
        raise StructureError(f"Ortam satırı bu olayda kullanılamaz ya da uzun: {event} / {setting}")
    if volc_env is not None and (event not in VOLC_ENV_EVENTS or volc_env not in VOLC_ENVS):   # 18 Eki (3)
        raise StructureError(f"Volkan ortamı bu olayda kullanılamaz: {event} / {volc_env}")
    fire_env = fire_env_of_spot(spot) if event == FIRE_TORNADO else None
    spec = {"event": event, "ship": ship, "spot": spot, "view": view, "beat_2": b2, "beat_3": b3,
            "vehicle": vehicle, "key_visual": expected_key_visual(event, spot, opening),
            "suffix": style_suffix(event, ship, spot, view, setting, volc_env, frame, fire_env, scene_env)}
    if scene_env is not None:
        spec["scene_env"] = scene_env   # 21 Eki (Aşama 5): ortam ekseni (9 olay)
    if opening is not None:
        spec["opening"] = opening       # 21 Eki (Aşama 6): açılış ekseni (18 olay)
    if frame is not None:
        spec["frame"] = dict(frame)   # 21 Eki (Aşama 4): kadraj ekseni (son denetim stil ekini bununla yeniden kurar)
    if volc_env is not None:
        spec["volc_env"] = volc_env   # 18 Eki (3): bombalar / kül bulutu ortamı (stil ekinde kamera cümlesi)
    if people is not None:
        spec["people"] = people
    if setting is not None:
        spec["setting"] = setting   # 14 Eki (4): çığ ortam satırı (stil ekinde)
    if event == FIRE_TORNADO:
        spec["fire_env"] = fire_env_of_spot(spot)   # 16 Eki: ortam kamera noktasından (kilit cümle onun)
    return spec


def people_word(spec: dict) -> str:
    return NUMBER_WORDS.get(spec.get("people"), "")


def people_line(spec: dict) -> str:
    """GPT'ye giden kaçan kişi satırı (kişi kuralı olan olaylarda), yoksa boş."""
    rule = next((r for r in SLICE_RULES.get(spec["event"], ()) if r.get("people")), None)
    if not rule:
        return ""
    w = people_word(spec)
    # 14 Eki: çığda insanlar ön planda. (14 Eki (2): köydeki "village street" ipucu kaldırıldı, "village" kilit
    # cümlede)
    # 22 Eki (genel kalite devam): önceki ipucu ", close by: near the railing or in the street right below"
    near = (", in the street right below, in the lower half of the frame"
            if spec["event"] in AVALANCHE_EVENTS + EARTHQUAKE_EVENTS + (FIRE_TORNADO,) + METEOR_EVENTS else "")
    return (f"PEOPLE RUNNING AWAY: {w} (slice_1_rest must say that {w} people run away from "
            f"{rule['away_from']}{near})\n")


# ❄️ Çığ (14 Eki (2), Bahadır): köy testi 3 denemede de 40-75 toplamını aştı. GPT'ye dilim bütçesi açıkça yazılır.
# Kapı aralıkları (SLICE_WORDS, TOTAL_WORDS_BY_EVENT) aynı; sadece GPT satırı. 14 Eki (5): toplam 70 ve köy kilit
# cümlesi 28 kelime; 0-4s insan cümlesine sabit 10 kelime (sayı + kaçış + yakın yer), 4-9s ve 9-15s kalanı eşit
# paylaşır (en fazla 18). Önceki: 4-9s/9-15s 18, 0-4s kalan.
# 15 Eki (2): ateş hortumu da (kilit cümle 18 -> 26 kelime, toplam 75)
BUDGET_EVENTS = AVALANCHE_EVENTS + EARTHQUAKE_EVENTS + (FIRE_TORNADO,)   # 14 Eki: deprem de
# 18 Eki (2), kuru deneme: Parti 2 olaylarında GPT toplamı 71-78 kelime yazıp yedeğe düşüyordu (bütçe satırı yoktu)
BUDGET_EVENTS += (FLOOD, MUDSLIDE, SLOPE, VILLAGE, WILDFIRE, FACADE_FIRE, HELICOPTER, LANDFALL, MARINA_TORNADO, AVENUE)
# 18 Eki (3), Bahadır kararı: ortam metni stil ekini uzattı (bombalar 103, kül bulutu 113 kelime); GPT'ye söylenen toplam
# 175 - stil eki - 3 etiket (kapı aralığı aynı, 40-75). Geçmiş GPT hikâyelerinin kül bulutunda çoğu 175'i aşacaktı.
BUDGET_EVENTS += VOLC_ENV_EVENTS
BUDGET_EVENTS += (TIDAL,)   # 21 Eki (Aşama 5): kıyı dalga (sel zaten listede)
# GPT'ye söylenen toplam = min(olay toplamı, 175 - stil eki - 3): volkan ortam olayları + sel + kıyı dalga (Aşama 5)
CAP_BUDGET_EVENTS = VOLC_ENV_EVENTS + (FLOOD, TIDAL)
# 21 Eki (genel kalite): stil eki uzadı (gerçek zaman, ön plan yüzü); 175 tavanlı diğer olaylarda da GPT bütçesi stil
# ekine göre (yoksa bütçeye uyan GPT hikâyesi 176-178 kelimeyle son denetimden dönüyordu)
CAP_BUDGET_EVENTS += AVALANCHE_EVENTS + EARTHQUAKE_EVENTS + (FIRE_TORNADO,)
BUDGET_EVENTS += METEOR_EVENTS        # 29 Eki: meteor (kilit cümle 33 kelime, toplam 75, prompt 175)
CAP_BUDGET_EVENTS += METEOR_EVENTS
BUDGET_SLICE_MAX = 18
BUDGET_SLICE_1 = 10


def word_budget_line(spec: dict) -> str:
    """GPT'ye giden dilim kelime bütçesi satırı (BUDGET_EVENTS), yoksa boş."""
    event = spec["event"]
    if event not in BUDGET_EVENTS:
        return ""
    lo1, hi1 = SLICE_WORDS["slice_1_rest"]
    lo2 = SLICE_WORDS["slice_2"][0]
    key = len(spec["key_visual"].split())
    total = TOTAL_WORDS_BY_EVENT.get(event, TOTAL_WORDS)[1]
    if event in CAP_BUDGET_EVENTS:   # 18 Eki (3) / 21 Eki: prompt 175 kelimeye sığsın (3 = dilim etiketleri)
        total = min(total, max_prompt_words(event) - 3 - len(spec["suffix"].split()))
    s1 = min(hi1, BUDGET_SLICE_1)
    s23 = max(lo2, min(BUDGET_SLICE_MAX, (total - key - s1) // 2))
    return (f"WORD BUDGET: the opening sentence has {key} words; slice_1_rest {lo1} to {s1} words, slice_2 {lo2} to "
            f"{s23} words, slice_3 {lo2} to {s23} words; the opening plus the three fields must total at most {total} "
            f"words.\n")


def assemble_story(spec: dict, slices: dict[str, str]) -> str:
    s1, s2, s3 = (slices[f] for f in SLICE_FIELDS)
    a, b, c = SLICE_LABELS
    return f"{a}: {spec['key_visual']} {s1} {b}: {s2} {c}: {s3}"


def plain_story(spec: dict, slices: dict[str, str]) -> str:
    """Etiketsiz düz metin (YouTube metadata, çeşitlilik ölçümü)."""
    return " ".join([spec["key_visual"]] + [slices[f] for f in SLICE_FIELDS])


def assemble_prompt(spec: dict, slices: dict[str, str]) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(assemble_story(spec, slices), spec["suffix"])


# ── Son denetim (Kie'den hemen önce) ─────────────────────────────────────────────────────────────────────────
_LABEL_LIKE = re.compile(r"\b\d{1,2}\s*[-–—]\s*\d{1,2}\s*(?:s|sec|secs|seconds?)\b", re.IGNORECASE)


def _issue(code: str, missing: str, feedback: str = "") -> dict:
    return {"rule": code, "missing": missing, "feedback": feedback}


def slice_issues(spec: dict, slices: dict[str, str]) -> list[dict]:
    """Dilim içeriği: kelime aralıkları, etiket benzeri ifade, satır sonu, seçilen olay ve araç terimleri.
    feedback GPT'ye gider (kalite kapısı); yapı hataları final_prompt_issues'ta."""
    event = spec["event"]
    out = []
    for f in SLICE_FIELDS:
        text = slices.get(f, "")
        lo, hi = SLICE_WORDS[f]
        n = len(text.split())
        if not lo <= n <= hi:
            out.append(_issue("slice_words", f"{f}: {lo}-{hi} kelime ({n} kelime)",
                              f"'{f}' must be {lo} to {hi} words; it has {n}."))
        if _LABEL_LIKE.search(text) or any(l in text for l in SLICE_LABELS):
            out.append(_issue("slice_label", f"{f}: dilim içinde zaman etiketi",
                              f"Do not write time labels like '0-4s' in '{f}'; the code adds them."))
        if "\n" in text:
            out.append(_issue("slice_newline", f"{f}: satır sonu", f"Write '{f}' as one line."))
    prompt_len = len(assemble_prompt(spec, slices))
    max_chars = max_prompt_chars(event)
    if prompt_len > max_chars:
        out.append(_issue("prompt_chars", f"prompt {prompt_len} karakter (en fazla {max_chars})",
                          f"The full prompt is {prompt_len} characters; shorten the three fields so it is at most "
                          f"{max_chars}."))
    total = len(plain_story(spec, slices).split())
    tw = TOTAL_WORDS_BY_EVENT.get(event, TOTAL_WORDS)
    if not tw[0] <= total <= tw[1]:
        out.append(_issue("total_words", f"toplam {tw[0]}-{tw[1]} kelime ({total})",
                          f"The three fields plus the fixed opening must total {tw[0]} to {tw[1]} "
                          f"words; now {total}."))
    for r in SLICE_RULES.get(event, ()):
        word = people_word(spec)
        terms = (word,) if r.get("people") else r["terms"]
        if not (all(terms) and find_terms(terms, slices.get(r["field"], ""))):
            out.append(_issue(r["rule"], r["missing"].format(word=word), r["feedback"].format(word=word)))
    # 16 Eki, Bahadır (hibrit hikâye): beat kapısı yumuşak (sadece ana nesne; araçlı beat'te araç adı). Eski kapı
    # (araç adı + tüm terim grupları) strict_beat_issues'ta, sadece raporda.
    out += soft_beat_issues(spec, slices)
    out += hard_extra_issues(slices)   # 16 Eki: çekim kelimesi, ülke/bölge adı, can kaybı
    # Yangın (8 Eki): yağmur/ıslaklık yasağı (kilit cümle dahil tüm hikâye) ve 4-9s'de araç havalanmaz
    if event in NO_RAIN_EVENTS:
        wet = rain_words(plain_story(spec, slices), event in WATER_DROP_EVENTS)
        if wet:
            out.append(_issue("fire_no_rain", f"yağmur/ıslaklık yasak ({', '.join(wet)})",
                              f"Remove {', '.join(repr(w) for w in wet)}: the air is hot and dry; no rain, wet or "
                              f"soaked surfaces anywhere."))
    for slot in NO_LIFT_SLICE.get(event, ()):
        lifted = find_terms(_FIRE_NO_LIFT, slices.get(slot, ""))
        if lifted:
            label = "4-9s" if slot == "slice_2" else "9-15s"
            out.append(_issue("fire_no_lift", f"{label}: araç havalanmaz ({', '.join(lifted)})",
                              f"In '{slot}' the {spec['vehicle']} stays on the ground: remove "
                              f"{', '.join(repr(w) for w in lifted)}."))
    # Volkan bombaları (10 Eki, Bahadır): taşlar tek tek ve büyük; genel/küçük taş anlatımı reddedilir
    for slot in VOLC_SINGLE_ROCK_SLICES.get(event, ()):
        small = find_terms(_VOLC_SMALL_ROCKS, slices.get(slot, ""))
        if small:
            label = "4-9s" if slot == "slice_2" else "9-15s"
            out.append(_issue("volcano_single_rock", f"{label}: taşlar tek tek ve büyük olmalı ({', '.join(small)})",
                              f"In '{slot}' show single large glowing rocks, each bigger than a softball: remove "
                              f"{', '.join(repr(w) for w in small)}."))
    # 13 Eki: GPT'nin yazdığı dilimlerde olaya özel yasak kelimeler (çığ)
    gpt_text = " ".join(slices.get(f, "") for f in SLICE_FIELDS)
    for code, terms, missing, feedback in EVENT_BANNED_WORDS.get(event, ()):
        found = find_terms(terms, gpt_text)
        if found:
            out.append(_issue(code, f"{missing} ({', '.join(found)})",
                              feedback.format(words=", ".join(repr(w) for w in found))))
    if event in METEOR_EVENTS:   # 29 Eki (2): beyaz su, kalıcı hasar, nesne koruma
        out += meteor_slice_issues(spec, slices)
    if event in WORD_CAP_EVENTS:   # 13 Eki (3): volkan (ve çığ) prompt'u en fazla 175 kelime
        n_words = len(assemble_prompt(spec, slices).split())
        cap = max_prompt_words(event)
        if n_words > cap:
            budget = cap - (n_words - len(" ".join(slices[f] for f in SLICE_FIELDS).split()))
            out.append(_issue("volcano_prompt_words", f"prompt {n_words} kelime (en fazla {cap})",
                              f"The full prompt is {n_words} words; shorten the three fields to at most {budget} words "
                              f"in total."))
    return out


def meteor_slice_issues(spec: dict, slices: dict[str, str]) -> list[dict]:
    """29 Eki (2), Bahadır (sadece meteor; GPT çıktısı ve kod yedeği aynı denetim):
    - suyun geçtiği her dilimde white / foaming / steaming,
    - 4-9s ve 9-15s'te en az bir hasar fiili (METEOR_DAMAGE),
    - 4-9s ve 9-15s seçilen maddenin iki ana nesnesini de taşır (METEOR_OBJECT_GATES)."""
    out = []
    for f in SLICE_FIELDS:
        text = slices.get(f, "")
        if find_terms(METEOR_WATER, text) and not find_terms(METEOR_WHITE, text):
            out.append(_issue("meteor_white_water", f"{f}: su beyaz/köpüklü/buharlı değil",
                              f"In '{f}' the water must be described as white, foaming or steaming."))
    for slot, bid in (("slice_2", spec["beat_2"]), ("slice_3", spec["beat_3"])):
        text = slices.get(slot, "")
        label = "4-9s" if slot == "slice_2" else "9-15s"
        if not find_terms(METEOR_DAMAGE, text):
            out.append(_issue("meteor_damage", f"{label}: kalıcı hasar fiili yok",
                              f"'{slot}' must show lasting damage with a verb like snap, rip, tear, flip, smash, shove, "
                              f"knock over, crush, topple or break."))
        missing = [g[0] for g in METEOR_OBJECT_GATES.get(bid, ()) if not find_terms(g, text)]
        if missing:
            out.append(_issue("meteor_objects", f"{label}: maddenin nesnesi yok ({bid}: {', '.join(missing)})",
                              f"'{slot}' must keep the exact objects of this event: "
                              f"{beat_text(spec['event'], slot, bid)}."))
    return out


def final_prompt_issues(spec: dict, slices: dict[str, str], prompt: str, story: str | None = None) -> list[dict]:
    """Kie'ye gidecek son prompt'un tam denetimi. Boş liste = gönderilebilir. Her madde kapalı başarısızlık."""
    from core.creative_pipeline import STORY_RULES, story_rule_issues
    out = []
    expected_suffix = style_suffix(spec["event"], spec["ship"], spec["spot"], spec["view"], spec.get("setting"),
                                   spec.get("volc_env"), spec.get("frame"),
                                   fire_env_of_spot(spec["spot"]) if spec["event"] == FIRE_TORNADO else None,
                                   spec.get("scene_env"))
    expected_key = expected_key_visual(spec["event"], spec["spot"], spec.get("opening"))
    if spec.get("key_visual") != expected_key:
        out.append(_issue("key_visual", "kilit görsel spec'te değişmiş"))
    if spec.get("suffix") != expected_suffix:
        out.append(_issue("suffix", "stil eki beklenenle aynı değil"))
    if has_people_rule(spec["event"]):
        lo, hi = count_range(spec["event"], spec["ship"])
        if not (isinstance(spec.get("people"), int) and lo <= spec["people"] <= hi and people_word(spec)):
            out.append(_issue("people", f"kaçan kişi sayısı {lo}-{hi} değil ({spec.get('people')})"))
    elif "people" in spec:
        out.append(_issue("people", "kişi kuralı olmayan olayda kaçan kişi sayısı var"))
    if uses_vehicle(spec["event"]) != (spec.get("vehicle") is not None):
        out.append(_issue("vehicle", f"araç uyuşmuyor ({spec.get('vehicle')})"))
    rebuilt_story = assemble_story({**spec, "key_visual": expected_key}, slices)
    rebuilt = assemble_prompt({**spec, "key_visual": expected_key,
                               "suffix": expected_suffix}, slices)
    if prompt != rebuilt:
        out.append(_issue("rebuild", "prompt koddan yeniden kurulan metinle birebir aynı değil"))
    if story is not None and story != rebuilt_story:
        out.append(_issue("rebuild_story", "hikâye koddan yeniden kurulan metinle birebir aynı değil"))
    head = f"{SLICE_LABELS[0]}: {expected_key} "
    if not prompt.startswith(head):
        out.append(_issue("key_visual", "0-4s kilit görselle başlamıyor"))
    positions = [prompt.find(f"{l}: ") for l in SLICE_LABELS]
    if any(prompt.count(f"{l}:") != 1 for l in SLICE_LABELS) or positions != sorted(positions) or -1 in positions:
        out.append(_issue("labels", "zaman etiketleri eksik, fazla ya da sırası yanlış"))
    out += slice_issues(spec, slices)
    n_constraints = count_constraints(expected_suffix)[0]
    if n_constraints > max_constraints(spec["event"]):
        out.append(_issue("suffix_constraints", f"stil eki {n_constraints} kısıt (en fazla "
                                                f"{max_constraints(spec['event'])})"))
    suffix_wet = rain_words(expected_suffix, spec["event"] in WATER_DROP_EVENTS)
    if spec["event"] in NO_RAIN_EVENTS and suffix_wet:   # 8 Eki: yangında stil eki de yağmursuz
        out.append(_issue("fire_no_rain_suffix", f"stil ekinde yağmur/ıslaklık ({', '.join(suffix_wet)})"))
    if len(prompt) > max_prompt_chars(spec["event"]) and not any(i["rule"] == "prompt_chars" for i in out):
        out.append(_issue("prompt_chars", f"prompt {len(prompt)} karakter (en fazla "
                                          f"{max_prompt_chars(spec['event'])})"))
    # 6 sabit kural (genel 40-60 "length" yerine TOTAL_WORDS; olay grupları ve çeşitlilik burada değil)
    fixed = set(STORY_RULES)
    for i in story_rule_issues(spec["event"], spec["ship"], plain_story(spec, slices), expected_suffix):
        if i["rule"] in fixed:
            out.append(i)
    return out


# ── KOD YEDEĞİ (16 Eki 2026, Bahadır: hibrit hikâye) ─────────────────────────────────────────────────────────
# GPT iki denemede de kapıdan geçemezse üretim durmaz: üç dilim koddaki onaylı metinlerden kurulur. 0-4s: kilit cümle
# (zaten kodda) + olayın/ortamın insan cümlesi havuzundan biri (rastgele, kelime sınırlarına sığanlar arasından);
# 4-9s ve 9-15s: seçilen beat'in kod metni olduğu gibi. Beat metni dilim alt sınırından (10 kelime) kısaysa tek sabit
# geçiş kalıbı (FALLBACK_TRANSITION) başa eklenir. Yedek de son denetimden (final_prompt_issues) geçer; hiçbir uygun
# insan cümlesi sığmazsa StructureError (Kie'ye gidilmez). Hangi kombinasyonların sığmadığı
# tests/test_story_fallback.py'de tek tek sayılır (havuzdan çıkarılmaz, Bahadır karar verir).
FALLBACK_TRANSITION = "Seconds later, in full view, "
# {N}: kaçan kişi sayısı (büyük harfle). Kişi kuralı olmayan olayda (sel) sayı yok.
_FB_TORNADO = ("{N} people sprint for cover from the tornado.", "{N} onlookers run inland away from the tornado.",
               "{N} residents flee from the tornado toward the buildings.",
               "{N} pedestrians scramble for cover as the tornado hits.", "{N} people run from the tornado.",
               "{N} onlookers dash away from the swirling debris.")
_FB_FLAMES = ("{N} residents run from the flames down the street.", "{N} villagers flee from the fire toward the road.",
              "{N} people sprint away from the flames.", "{N} residents scramble downhill away from the fire.",
              "{N} people run from the flames.", "{N} villagers dash away from the burning slope.")
# 22 Eki (genel kalite devam): korkuluk / teras / balkon geçen insan cümleleri "in the street right below" oldu
_FB_AVA_NEAR = ("{N} villagers run away right below.", "{N} people flee in the street right below.",
                "{N} villagers sprint off right below.", "{N} residents run from it just below.",
                "{N} people scatter in the street below.", "{N} villagers dash away just beneath.")
_FB_EQ_NEAR = ("{N} residents run away in the street below.", "{N} neighbours flee in the street right below.",
               "{N} people sprint off right below.", "{N} residents scatter in the street below.",
               "{N} people run away in the street right below.", "{N} neighbours dash away just below.")
FALLBACK_PEOPLE = {
    FLOOD: ("Pedestrians scramble onto steps and ledges as it hits.", "People run for the doorways as the water hits.",
            "Pedestrians flee up the steps of the nearest buildings.",
            "Residents climb onto high ledges as the water spreads.",
            "People scramble away from the curb toward higher steps.",
            "Pedestrians dash for the doorways as the street floods."),
    TIDAL: ("{N} pedestrians run from the wave toward the buildings.", "{N} residents sprint away from the wave up the street.",
            "{N} people flee from the wave toward higher steps.", "{N} pedestrians scramble up the steps away from the wave.",
            "{N} people run inland as the wave hits.", "{N} residents dash away from the wave."),
    # 23 Eki, Bahadır (heyelan testi): çamur yukarıdan geliyor; "uphill" / "up the street" insanları çamura doğru
    # koşturuyordu. Önceki: "{N} residents run uphill away from the mud.", "{N} people flee from the mud up the
    # street.", "{N} pedestrians scramble uphill as the mud hits.", "{N} pedestrians dash uphill away from the flow."
    # 23 Eki (2), Bahadır: "{N} people run for higher ground." de çıktı (üç heyelan olayında; yukarı = çamura doğru).
    # Yerine gelen aynı uzunlukta (6 kelime): en kısa cümle sıkışık kombinasyonları 175'e sığdırıyor
    MUDSLIDE: ("{N} residents run down the street away from the mud.",
               "{N} people flee from the mud toward the lower street.",
               "{N} pedestrians scramble away as the mud hits.", "{N} residents sprint away from the mud.",
               "{N} people run from the mud.", "{N} pedestrians dash away from the flow."),
    SLOPE: ("{N} drivers scramble out and run from the mud.", "{N} drivers flee from the mud along the road.",
            "{N} residents run away from the mud.", "{N} drivers sprint for the far side of the road.",
            "{N} people run from the mud.", "{N} drivers dash away as the mud hits."),
    # 23 Eki: MUDSLIDE gibi. Önceki: "{N} villagers run uphill away from the mud.", "{N} residents dash uphill
    # between the houses."
    VILLAGE: ("{N} villagers run down the lane away from the mud.",
              "{N} residents flee from the torrent to higher ground.",
              "{N} villagers scramble up the stone steps.", "{N} villagers sprint away from the mud.",
              "{N} people flee from the mud.", "{N} residents dash away between the houses."),
    LANDFALL: _FB_TORNADO, MARINA_TORNADO: _FB_TORNADO, AVENUE: _FB_TORNADO,
    WILDFIRE: _FB_FLAMES, HELICOPTER: _FB_FLAMES,
    FACADE_FIRE: ("{N} pedestrians run from the burning tower.", "{N} people flee from the flames across the street.",
                  "{N} pedestrians sprint away from the tower.", "{N} residents scramble away from the falling debris.",
                  "{N} people run from the flames.", "{N} pedestrians dash across the street away from the tower."),
    ERUPTION: ("{N} villagers run from the eruption down the street.", "{N} residents flee from the eruption toward the houses.",
               "{N} people sprint away from the eruption.", "{N} villagers scramble down the street away from it.",
               "{N} people run from the eruption.", "{N} residents dash away along the village street."),
    PYROCLASTIC: ("{N} villagers run from the cloud down the street.", "{N} residents flee from the cloud between the houses.",
                  "{N} people sprint away from the cloud.", "{N} villagers scramble away from the cloud.",
                  "{N} people run from the cloud.", "{N} residents dash down the street away from it."),
    VOLCANIC_BOMBS: ("{N} villagers run from the falling rocks.", "{N} residents flee down the street from the rocks.",
                     "{N} people sprint away from the falling rocks.", "{N} villagers scramble for cover from the rocks.",
                     "{N} people run for cover from it.", "{N} residents dash away between the houses."),
    AVALANCHE_VILLAGE: _FB_AVA_NEAR, AVALANCHE_FOREST: _FB_AVA_NEAR,
    AVALANCHE_SKI: ("{N} guests run away right below.", "{N} guests flee in the street right below.",
                    "{N} people sprint off right below.", "{N} guests run from it just below.",
                    "{N} people scatter in the street below.", "{N} guests dash away just beneath."),
    EARTHQUAKE_APARTMENT: _FB_EQ_NEAR, EARTHQUAKE_OLD_STREET: _FB_EQ_NEAR,
    # 29 Eki: meteor (kilit cümle 33 kelime; en kısa cümle 6 kelime, sığma çiftleri ona göre)
    METEOR: ("{N} people run off right below.", "{N} residents flee in the street right below.",
             "{N} people sprint inland in the street below.", "{N} residents run from it just below.",
             "{N} people scatter in the street below.", "{N} neighbours dash inland right below."),
}
# 🔥 Ateş hortumu: ortama göre (kilit cümle 28-29 kelime, en uzun beat çifti 39: insan cümlesi 6-7 kelime)
FALLBACK_PEOPLE_FIRE_ENV = {
    "forest_edge": ("{N} people run between the houses below.", "{N} neighbors flee in the yard below.",
                    "{N} people sprint away right below.", "{N} residents run away in the street right below.",
                    "{N} people dash between the houses below.", "{N} neighbors run through the yard below."),
    "tree_street": ("{N} people run down the street below.", "{N} residents flee in the street below.",
                    "{N} people sprint away right below.", "{N} neighbors run along the street below.",
                    "{N} people dash away in the street right below.", "{N} residents run across the street below."),
    "village_woods": ("{N} villagers run between the houses below.", "{N} villagers flee down the street below.",
                      "{N} people sprint away right below.", "{N} villagers run through the yard below.",
                      "{N} people run away in the street right below.", "{N} villagers dash in the gardens below."),
}


def fallback_people_pool(spec: dict) -> tuple[str, ...]:
    if spec["event"] == FIRE_TORNADO:
        return FALLBACK_PEOPLE_FIRE_ENV[spec["fire_env"]]
    return FALLBACK_PEOPLE[spec["event"]]


def fallback_beat_slice(spec: dict, slot: str) -> str:
    """Seçilen beat'in kod metni; dilim alt sınırından kısaysa sabit geçiş kalıbıyla."""
    bid = spec["beat_2"] if slot == "slice_2" else spec["beat_3"]
    text = beat_text(spec["event"], slot, bid, spec["vehicle"])
    if len(text.split()) < SLICE_WORDS[slot][0]:
        text = FALLBACK_TRANSITION + text
    return clean_slice(text[0].upper() + text[1:])


def _fallback_fits(spec: dict, slices: dict[str, str]) -> bool:
    """Kelime/karakter sınırları (dilim aralıkları, toplam aralık, 175 kelime, karakter)."""
    for f in SLICE_FIELDS:
        lo, hi = SLICE_WORDS[f]
        if not lo <= len(slices[f].split()) <= hi:
            return False
    lo, hi = TOTAL_WORDS_BY_EVENT.get(spec["event"], TOTAL_WORDS)
    if not lo <= len(plain_story(spec, slices).split()) <= hi:
        return False
    prompt = assemble_prompt(spec, slices)
    if len(prompt.split()) > max_prompt_words(spec["event"]):   # yedekte 175 kelime (16 Eki); meteor 195 (29 Eki)
        return False
    return len(prompt) <= max_prompt_chars(spec["event"])


def fallback_candidates(spec: dict) -> list[dict[str, str]]:
    """Kelime sınırlarına sığan yedek dilim takımları (her biri havuzdan bir insan cümlesiyle)."""
    word = people_word(spec).capitalize()
    s2, s3 = fallback_beat_slice(spec, "slice_2"), fallback_beat_slice(spec, "slice_3")
    out = []
    for t in fallback_people_pool(spec):
        sl = {"slice_1_rest": clean_slice(t.format(N=word)), "slice_2": s2, "slice_3": s3}
        textured = mud_texture(spec, sl)   # 21 Eki (genel kalite): sığarsa dokulu hâl
        if textured is not None and _fallback_fits(spec, textured):
            out.append(textured)
        elif _fallback_fits(spec, sl):
            out.append(sl)
    return out


# 21 Eki (genel kalite), Bahadır: heyelanda çamur gri lapa gibi çıktı. Kilit cümlede "mud" yoksa (yamaç C, köy C/D) kod
# yedeğinde "mud" geçen ilk ifadeye doku eklenir; kilit cümlede varsa dokuyu kilit cümle taşır.
MUD_TEXTURE = "thick brown mud full of rocks, branches and debris"
LANDSLIDE_EVENTS = (MUDSLIDE, SLOPE, VILLAGE)
_MUD_RE = re.compile(r"\b(?:the )?mud(?: and (?:rocks|boulders))?\b", re.I)


def mud_texture(spec: dict, slices: dict[str, str]) -> dict[str, str] | None:
    """Kod yedeği dilimlerinde ilk "mud" ifadesi dokulu (kilit cümlede "mud" yoksa); değişiklik yoksa None."""
    if spec["event"] not in LANDSLIDE_EVENTS or "mud" in spec["key_visual"].lower():
        return None
    for f in SLICE_FIELDS:
        m = _MUD_RE.search(slices[f])
        if m:
            new = MUD_TEXTURE[0].upper() + MUD_TEXTURE[1:] if m.start() == 0 else MUD_TEXTURE
            return {**slices, f: slices[f][:m.start()] + new + slices[f][m.end():]}
    return None


def build_fallback(spec: dict, rng: random.Random | None = None) -> dict[str, str]:
    """Kod yedeği dilimleri. Sığan insan cümlesi yoksa StructureError (kelime sınırı; kombinasyon raporda)."""
    cands = fallback_candidates(spec)
    if not cands:
        raise StructureError(f"Kod yedeği kelime sınırına sığmadı: {spec['event']} / {spec['spot']} / "
                             f"{spec['beat_2']}+{spec['beat_3']} / {spec['vehicle']}")
    return (rng or random).choice(cands)


# ── KALICI HAVUZ LİNTİ (17 Eki 2026, Bahadır: temizlik turu) ────────────────────────────────────────────────────
# Yapılandırılmış hattaki her beat metni ve her araç adı aşağıdaki sözcükleri içeremez; içerirse modül açılışta
# StructureError verir (uyarı değil, HATA). Ders: ince/uzak hedef (direk, tel, çit, tabela, cam), açık arazi ve küçük
# araç videoda kayboluyor ya da yanlış ortam çiziliyor; kusur bizim taraftan gelmesin.
# Mevcut ama kurala göre korunan beat'ler (daha önce üretilmiş videoda kullanıldı ya da zayıflığı sadece tekrar/koyu)
# POOL_LINT_GRANDFATHERED'da tek tek, gerekçeyle durur. Listeye yeni madde eklemek Bahadır onayı ister; listedeki bir
# beat değişir, çıkar ya da artık ihlal etmezse açılış yine hata verir (liste her zaman birebir güncel).
POOL_LINT_THIN = ("glass", "pole", "wire", "cable", "fence", "fencing", "picket", "sign", "signboard", "signpost",
                  "awning", "railing", "guardrail", "guard rail", "window pane", "windowpane", "pane", "windshield",
                  "windscreen", "shop window", "rear window", "lamppost", "lamp post", "street lamp", "streetlamp",
                  "streetlight", "street light", "low wall", "power line", "crate")
POOL_LINT_OPEN_LAND = ("field", "fields", "empty land", "open land", "open ground", "plot", "meadow", "pasture",
                       "farmland", "grassland", "prairie", "empty lot", "vacant lot", "wasteland", "valley floor")
POOL_LINT_SMALL_VEHICLE = ("small car", "small van", "small boxy car", "small vehicle", "small hatchback", "hatchback",
                           "compact", "compact car", "subcompact", "mini car", "minicar", "microcar")
POOL_LINT_SHIP = ("cargo", "tugboat", "tug boat", "fishing boat", "trawler", "freighter", "container ship", "tanker",
                  "commercial ship", "barge")
# 18 Eki (2): ateş hortumu beat'lerinde düz sütun / patlama çağrıştıran sözcükler (videoda huni yerine sütun çıkıyordu)
FIRE_TOR_SHAPE_BANNED = ("column", "plume", "pillar", "explosion", "explode", "blast")
POOL_LINT_RULES = (("ince/uzak hedef", POOL_LINT_THIN), ("açık arazi", POOL_LINT_OPEN_LAND),
                   ("küçük araç", POOL_LINT_SMALL_VEHICLE), ("ticari gemi", POOL_LINT_SHIP))
_PROTECTED = "korunan: daha önce üretilmiş videoda kullanıldı"
_ONLY_REPEAT = "denetimde sadece tekrar/koyu zayıflığı (kural dışı, silinmez)"
_KEPT = "denetimde KALSIN (zayıf değil)"
_WAITING = "çıkış bekliyor: grup 4'ün altına düşerdi, yerine yeni beat sonraki partide"
# (olay, beat) -> gerekçe. Kül bulutu bu turda dokunulmaz (Bahadır).
POOL_LINT_GRANDFATHERED = {
    (FLOOD, "V4"): _KEPT + " (özne araç, direk ikincil)", (FLOOD, "D2"): _PROTECTED + " (3 Eki Kie sel testi V6+D2)",
    (TIDAL, "T6"): _PROTECTED, (TIDAL, "W2"): _PROTECTED, (TIDAL, "W6"): _PROTECTED,
    (LANDFALL, "E5"): _KEPT + " (özne dükkân önü)",
    # 23 Eki, Bahadır: marina Y3, Z1, Z2, Z6 yeni metin, korumaları kalktı (lint'ten korumasız geçer)
    (AVENUE, "P5"): _PROTECTED, (AVENUE, "Q3"): _PROTECTED, (AVENUE, "Q6"): _PROTECTED,
    (FACADE_FIRE, "M6"): _PROTECTED,
    (FACADE_FIRE, "N5"): _ONLY_REPEAT,
    (ERUPTION, "S4"): _KEPT + " (özne ağaç sırası)", (ERUPTION, "U2"): _KEPT + " (özne araç)",
    (PYROCLASTIC, "P2"): _PROTECTED + "; kül bulutu bu turda dokunulmaz",
    (PYROCLASTIC, "Q2"): _PROTECTED + "; kül bulutu bu turda dokunulmaz",
    (VOLCANIC_BOMBS, "R3"): _PROTECTED, (VOLCANIC_BOMBS, "R4"): _PROTECTED,
    (AVALANCHE_VILLAGE, "A5"): _PROTECTED + " (özne kulübe, çit ikincil)",
}


def pool_lint_hits(text: str) -> list[tuple[str, list[str]]]:
    """Metindeki yasak sözcükler, kural adıyla: [(kural, [sözcükler])]."""
    return [(name, found) for name, terms in POOL_LINT_RULES for found in [find_terms(terms, text)] if found]


def pool_lint_errors() -> list[str]:
    """Havuz lintinin tüm ihlalleri (boş liste = temiz): muaf olmayan beat'ler, araç adları ve güncel olmayan muafiyet
    kayıtları."""
    out = []
    for event, b in EVENT_BEATS.items():
        for slot in ("slice_2", "slice_3"):
            for bid, beat in b[slot].items():
                hits = pool_lint_hits(beat["text"].replace("{vehicle}", "vehicle"))
                if hits and (event, bid) not in POOL_LINT_GRANDFATHERED:
                    out.append(f"{event}/{bid}: {hits}")
                if not hits and (event, bid) in POOL_LINT_GRANDFATHERED:
                    out.append(f"{event}/{bid}: muafiyet gereksiz (ihlal yok)")
    for slot in ("slice_2", "slice_3"):   # 18 Eki (2): ateş hortumu dönen huni; sütun/patlama sözcüğü yok
        for bid, beat in EVENT_BEATS[FIRE_TORNADO][slot].items():
            shape = find_terms(FIRE_TOR_SHAPE_BANNED, beat["text"])
            if shape:
                out.append(f"{FIRE_TORNADO}/{bid}: ateş hortumu beat'inde şekil sözcüğü ({', '.join(shape)})")
    for event in METEOR_EVENTS:   # 29 Eki (ek kural): meteor beat'inde durağan fiil yok, her beat'te büyük temas var
        for slot in ("slice_2", "slice_3"):
            for bid, beat in EVENT_BEATS[event][slot].items():
                static = find_terms(METEOR_STATIC, beat["text"])
                if static:
                    out.append(f"{event}/{bid}: meteor beat'inde durağan fiil ({', '.join(static)})")
                if not find_terms(METEOR_CONTACT, beat["text"]):
                    out.append(f"{event}/{bid}: meteor beat'inde ev/araç/insan/ağaç teması yok")
                if min(METEOR_BEAT_SCORES.get(bid, (0,))) < 3:
                    out.append(f"{event}/{bid}: meteor beat puanı 3'ün altında ya da puansız")
                # 29 Eki (2): kalıcı hasar fiili, tsunami / ikinci meteor yok, su beyaz, nesne koruma kaydı var
                if not find_terms(METEOR_DAMAGE, beat["text"]):
                    out.append(f"{event}/{bid}: meteor beat'inde hasar fiili yok")
                bad = find_terms(METEOR_TSUNAMI_BANNED + METEOR_ONE_BANNED, beat["text"])
                if bad:
                    out.append(f"{event}/{bid}: meteor beat'inde yasak kök ({', '.join(bad)})")
                if find_terms(METEOR_WATER, beat["text"]) and not find_terms(METEOR_WHITE, beat["text"]):
                    out.append(f"{event}/{bid}: meteor beat'inde su beyaz değil")
                if bid not in METEOR_OBJECT_GATES or any(not find_terms(g, beat["text"])
                                                         for g in METEOR_OBJECT_GATES[bid]):
                    out.append(f"{event}/{bid}: meteor nesne koruma kaydı yok ya da metinle uyuşmuyor")
            for bid in METEOR_HELD_BEATS:
                if bid in EVENT_BEATS[event][slot]:
                    out.append(f"{event}/{bid}: puanı düşük madde havuzda")
    for event in VOLCANO_EVENTS:   # 18 Eki: volkan beat'inde "rain" fiili yok (yağmur kapısı/yağış çağrışımı)
        for slot in ("slice_2", "slice_3"):
            for bid, beat in EVENT_BEATS[event][slot].items():
                rain = [t for t in re.findall(r"[a-z]+", beat["text"].lower()) if t in _RAIN_TOKENS]
                if rain:
                    out.append(f"{event}/{bid}: volkan beat'inde 'rain' fiili ({', '.join(rain)})")
    for event, bid in POOL_LINT_GRANDFATHERED:
        if bid not in EVENT_BEATS.get(event, {}).get("slice_2", {}) and bid not in EVENT_BEATS.get(event, {}).get(
                "slice_3", {}):
            out.append(f"{event}/{bid}: muafiyet kaydı havuzda olmayan beat için")
    vehicles = [(v, n) for v, lst in REGION_VEHICLES.items() for n, _ in lst] + \
               [(e, n) for e, lst in EVENT_VEHICLES.items() for n, _ in lst]
    for owner, name in vehicles:
        hits = pool_lint_hits(name)
        if hits:
            out.append(f"araç {owner}/{name}: {hits}")
    for view, text in REGION_VIEWS.items():   # görünüm tarifi stil ekine girer: küçük araç / ticari gemi yok
        hits = [h for h in pool_lint_hits(text) if h[0] in ("küçük araç", "ticari gemi")]
        if hits:
            out.append(f"görünüm {view}: {hits}")
    return out


# ── Import anı tutarlılık denetimi: eksik/yanlış veri üretimde değil, açılışta patlasın ──────────────────────
def _validate_data() -> None:
    end = int(SLICE_LABELS[-1].split("-")[1].rstrip("s"))
    if end != config.VIDEO_DURATION_SECONDS:
        raise StructureError(f"Son zaman etiketi {SLICE_LABELS[-1]} video süresiyle ({config.VIDEO_DURATION_SECONDS} sn) "
                             f"uyuşmuyor")
    if set(REGION_VEHICLES) != set(REGION_VIEWS):
        raise StructureError(f"Araç listesi görünümlerle uyuşmuyor: {set(REGION_VEHICLES) ^ set(REGION_VIEWS)}")
    for view, vehicles in REGION_VEHICLES.items():
        if not vehicles or any(not t for _, t in vehicles):
            raise StructureError(f"Görünümde araç/terim yok: {view}")
    if set(EVENT_VEHICLES) - set(EVENT_KEY_VISUAL):
        raise StructureError(f"Araç listesi yapılandırılmamış olayda: {set(EVENT_VEHICLES) - set(EVENT_KEY_VISUAL)}")
    if set(SLICE_RULES) - set(EVENT_KEY_VISUAL):
        raise StructureError(f"Dilim kapısı yapılandırılmamış olayda: {set(SLICE_RULES) - set(EVENT_KEY_VISUAL)}")
    for event, key in EVENT_KEY_VISUAL.items():
        if event not in EVENT_BEATS or not key.endswith(".") or "\n" in key:
            raise StructureError(f"Kilit görsel/olay havuzu eksik: {event}")
        b = EVENT_BEATS[event]
        ids = list(b["slice_2"]) + list(b["slice_3"])
        if len(ids) != len(set(ids)) or not b["slice_2"] or not b["slice_3"]:
            raise StructureError(f"Olay havuzu boş ya da id tekrarı: {event}")
        for slot in ("slice_2", "slice_3"):
            for bid, beat in b[slot].items():
                if not beat.get("text") or not beat.get("terms") or any(not g for g in beat["terms"]):
                    raise StructureError(f"Olay verisi eksik: {event}/{bid}")
        for v, d in b["excluded_pairs"]:
            if v not in b["slice_2"] or d not in b["slice_3"]:
                raise StructureError(f"Yasak eşleşme bilinmeyen id: {v}-{d}")
        for d in b["excluded_views"]:
            if d not in b["slice_3"]:
                raise StructureError(f"Bölge kısıtı bilinmeyen id: {d}")
        for d in b["excluded_spots"]:   # 10 Eki: kamera noktası dışlaması 4-9s ya da 9-15s maddesinde
            if d not in b["slice_3"] and d not in b["slice_2"]:
                raise StructureError(f"Bölge kısıtı bilinmeyen id: {d}")
        for r in SLICE_RULES.get(event, ()):
            if r["field"] not in SLICE_FIELDS or not (r.get("people") or r.get("terms")):
                raise StructureError(f"Dilim kapısı hatalı: {event}/{r.get('rule')}")
        if has_people_rule(event):
            lo, hi = count_range(event, None)
            if any(n not in NUMBER_WORDS for n in range(lo, hi + 1)):
                raise StructureError(f"Kişi aralığının sayı kelimesi yok: {event} {lo}-{hi}")
        if event in REGION_VIEW_EVENTS:
            if event in EVENT_VEHICLES or b["excluded_views"] and set().union(*b["excluded_views"].values()) - set(REGION_VIEWS):
                raise StructureError(f"Görünümlü olayda olay araç listesi ya da bilinmeyen görünüm: {event}")
        elif b["excluded_views"]:
            raise StructureError(f"Görünümsüz olayda görünüm kısıtı var: {event}")
        elif not uses_vehicle(event):   # 13 Eki: araçsız olayın araç listesi olmaz
            if event in EVENT_VEHICLES:
                raise StructureError(f"Araçsız olayda araç listesi var: {event}")
        elif not EVENT_VEHICLES.get(event) or any(not t for _, t in EVENT_VEHICLES[event]):
            raise StructureError(f"Görünümsüz olayın araç listesi yok: {event}")
        for code, terms, *_ in EVENT_BANNED_WORDS.get(event, ()):   # 13 Eki: kod metinleri yasak kelime içermez
            fixed = " ".join([key] + [beat["text"] for slot in ("slice_2", "slice_3") for beat in b[slot].values()])
            if not terms or find_terms(terms, fixed):
                raise StructureError(f"Yasak kelime kod metninde: {event}/{code}")
        for d, spots in b["excluded_spots"].items():
            if spots - set(EVENT_SKELETONS[event]["spots"]):
                raise StructureError(f"Bilinmeyen spot: {event}/{d}: {spots - set(EVENT_SKELETONS[event]['spots'])}")
        for view in structure_views(event):
            for spot in view_spots(event, view):
                if not allowed_pairs(event, view, spot):
                    raise StructureError(f"İzinli olay çifti yok: {event} / {view} / {spot}")
    # 16 Eki: ateş hortumu ortam ekseni. Her nokta tam bir ortamda; ortam noktaları iskeletle aynı; kilit cümleler tek
    # satır ve noktayla biter
    tor_spots = [s for env in FIRE_TOR_ENVS.values() for s in env["spots"]]
    if sorted(tor_spots) != sorted(EVENT_SKELETONS[FIRE_TORNADO]["spots"]) or len(tor_spots) != len(set(tor_spots)):
        raise StructureError("Ateş hortumu ortam noktaları iskeletle uyuşmuyor")
    for name, env in FIRE_TOR_ENVS.items():
        if not env["key"].endswith(".") or "\n" in env["key"] or not env["label"]:
            raise StructureError(f"Ateş hortumu ortam verisi hatalı: {name}")
    # 16 Eki (hibrit hikâye): her araçsız beat'in nesne grubu var; her olayın (ateş hortumunda her ortamın) en az 6
    # insan cümlesi var
    for event, b in EVENT_BEATS.items():
        for slot in ("slice_2", "slice_3"):
            for bid, beat in b[slot].items():
                if "{vehicle}" in beat["text"]:
                    if bid in OBJECT_GROUPS.get(event, {}):
                        raise StructureError(f"Araçlı beat'te nesne grubu sırası olmaz: {event}/{bid}")
                elif not 0 <= OBJECT_GROUPS.get(event, {}).get(bid, -1) < len(beat["terms"]):
                    raise StructureError(f"Nesne grubu eksik/hatalı: {event}/{bid}")
        pools = (FALLBACK_PEOPLE_FIRE_ENV.values() if event == FIRE_TORNADO else [FALLBACK_PEOPLE.get(event, ())])
        if any(len(p) < 6 for p in pools):
            raise StructureError(f"Yedek insan cümlesi havuzu 6'dan az: {event}")
    for event, off in DISABLED_BEATS.items():   # 29 Eki: kapalı beat'ler havuzda olmalı
        if off - set(EVENT_BEATS[event]["slice_2"]) - set(EVENT_BEATS[event]["slice_3"]):
            raise StructureError(f"Kapalı beat havuzda yok: {event}/{off}")
    for light in EVENT_SKELETONS[METEOR]["weather"]:   # 29 Eki: meteor ortam satırı her ışıkla en fazla 15 kelime
        for env in METEOR_ENVS:
            if len(meteor_setting(env, light).split()) > SETTING_MAX_WORDS:
                raise StructureError(f"Meteor ortam satırı uzun: {env} / {light}")
    for event, retired in RETIRED_BEATS.items():   # 17 Eki: çıkarılan kimlik havuza geri gelmez (Notion geçmişi)
        for bid in retired:
            if bid in EVENT_BEATS[event]["slice_2"] or bid in EVENT_BEATS[event]["slice_3"]:
                raise StructureError(f"Çıkarılmış beat kimliği yeniden kullanılmış: {event}/{bid}")
    # 17 Eki: kalıcı havuz linti (ince/uzak hedef, açık arazi, küçük araç, ticari gemi). Uyarı değil, hata.
    errors = pool_lint_errors()
    if errors:
        raise StructureError("Havuz linti: " + "; ".join(errors))


_validate_data()
