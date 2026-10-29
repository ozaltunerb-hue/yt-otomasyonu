"""
İskelet hattı (TUR 30, İŞ 5): olay başına kilitli hikaye iskeleti, GPT sadece boşlukları doldurur.

Eski hat (settings.PROMPT_PIPELINE="legacy"): 1.530 kelimelik yazıcı sistem prompt'u → 5 aday → 8 senaryo
kapısı → skor/sıralama → simplifier → A-N kapıları. Denetimde çelişkili kurallar, %39 aday reddi ve kalitenin
seçime girmemesi görüldü. Bu hatta hikayeyi iskelet yazar; gpt-4o-mini sadece yer, hava, kişi sayısı ve kişi
rolünü seçer, seçimler listeden/aralıktan doğrulanır. Son prompt = hikaye + tek kamera satırı + kıyafet/ışık
(en fazla 8 kısıt). Görünür büyük fiziksel tetiği olmayan 17 olay bu hatta yok (bkz. REMOVED_EVENTS).

Sonraki tur notu: olay başına 2-3 iskelet varyantı (aynı tetik, farklı cümle akışı/nesne) eklenip LRU ile
dönülecek; şu an her olayın tek iskeleti var, çeşitlilik yer/hava/kişi/gemi boşluklarından geliyor.
"""
from __future__ import annotations

import json
import logging
import random
import re
import threading

from core.creative_engine import (
    DOMAIN_ATTRIBUTES,
    ENV_CENTRIC_DOMAINS,
    MARITIME_INSPIRATION_DOMAINS,
    cast_range,
    get_realism_guardrails,
    is_current_universe_combo,
)

log = logging.getLogger("CreativeEngine")

SKELETON_CAMERA = "bystander_handheld"

# Hava boşluğu: iskelette "in {weather}" olarak geçer
WEATHER_SEA = ["grey overcast light", "heavy rain", "strong gusting wind", "stormy late-afternoon light",
               "driving rain and wind", "cold bright daylight with a strong wind"]
WEATHER_STORM = ["a dark green storm light", "heavy rain under black clouds", "howling wind and rain",
                 "stormy late-afternoon light"]

# Telefonu tutan kişinin durduğu yer (kamera satırı). Tek kamera tanımı: el kamerası.
CAMERA_SPOTS = {
    "Open vehicle deck": "on the open vehicle deck",
    "Island crossing route": "on the open vehicle deck",
    "Ferry terminal ramp": "on the quay beside the loading ramp",
    # Final turu: yat yana devrilerek suya girer; ön-yan açı hem bordayı hem devrilmeyi gösterir
    "Construction slipway": "on the quay beside the slipway, level with the yacht's bow, seeing its whole side",
    "Drydock interior": "on the drydock wall",
    "Shipyard basin": "on the basin quay",
    "Floating pontoon dock": "on the next pontoon",
    "Marina fuel dock": "on the fuel dock",
    "Marina fairway": "on the marina breakwater",
    "Yacht club entrance": "on the marina breakwater",
    # Kontrolsüz yat (1 Eki): yat marinaya girer, bağlı teknelere çarpar
    "Breakwater at the marina entrance": "on the breakwater beside the marina entrance",
    "Marina berthing pier": "on the berthing pier",
    # 4 Eki, Bahadır: hortum marina olayının yeni kamera noktası
    "High marina balcony": "on a high balcony overlooking the marina and quay",
    # 10 Eki, Bahadır: hortum cadde olayının yüksek kamera noktaları (eski kaldırım/veranda noktaları başka olaylarda)
    "High balcony over a downtown avenue": "on a high balcony across the street, overlooking the avenue",
    "Upper-floor balcony over a residential avenue": "on an upper-floor balcony across the street, overlooking the "
                                                     "avenue",
    "High balcony over a high-rise avenue": "on a high balcony across the street, overlooking the avenue",
    "Narrow channel between moored boats": "on the pontoon at the edge of the narrow channel",
    "Cruise terminal berth": "on the terminal quay",
    "Open-air pool deck": "on the pool deck",
    "Downtown city center": "on a sidewalk across the street",
    "Dense urban downtown": "on a sidewalk across the street",
    "High-rise coastal city": "on a sidewalk across the street",
    "High-rise city district": "on a sidewalk across the street",
    "Commercial city streets": "on a sidewalk across the street",
    "Residential city district": "on a front porch across the street",
    "Residential coastal district": "on a front porch across the street",
    "Suburban coastal city": "on a sidewalk across the street",
    # Dev dalga baskını (30 Eyl): yüksekten bakış, dalga kıyı yoluna/caddeye çarpar
    "Coastal road below a seafront promenade": "at the railing of a raised seafront promenade, looking down at the coastal road",
    "Coastal street of low shopfronts": "on a second-floor balcony, looking down at the coastal street",
    "Coastal avenue behind a seawall": "on top of the seawall, looking down at the coastal avenue",
    # Heyelan (2 Eki): her yer akıntıyı karede gösterir
    "Balcony across a steep hillside street": "on a balcony across the steep hillside street",
    "Rooftop terrace below a hillside street": "on a rooftop terrace just below the hillside street, facing up the street",
    # 21 Eki (genel kalite): 175 kelime için kısa. Önceki: "at the top of a side stairway beside the narrow hillside
    # lane", "behind the guardrail on the far side of the hillside road"
    "Side stairway off a narrow hillside lane": "atop a side stairway beside the hillside lane",
    "Behind the guardrail of a hillside road": "behind the guardrail across the hillside road",
    "Bridge on a side road below the slope": "on a bridge on a side road, facing the slope and the road",
    "Far edge of the road across from the slope": "on the far edge of the road, across from the slope",
    "Terrace on the opposite hillside": "on a terrace on the opposite hillside, facing the village",
    "High steps on the village square": "on the high steps at the edge of the village square",
    "Upper-floor balcony of a village house": "on the upper-floor balcony of a village house, facing up the slope",
    # Yangın (8 Eki, Bahadır; TASLAK): olay başına 2 kamera, Bahadır'ın kamera cümleleri birebir
    "Balcony of a hillside house": "on a balcony of a hillside house overlooking the street and the burning slope",
    "Embankment above the village road": "on a roadside embankment above the village road",
    # 8 Eki (2), Bahadır: cephe yangını ve ateş hortumu balkonunda kamera yüksek; kaldırım noktaları çıktı
    "Balcony across from a downtown tower": "on a high balcony across the street from the tower",
    "Rooftop terrace across from a downtown tower": "on a rooftop terrace across the street from the tower",
    "Balcony across from a coastal high-rise": "on a high balcony across the street from the tower",
    "Rooftop terrace across from a coastal high-rise": "on a rooftop terrace across the street from the tower",
    # 16 Eki, Bahadır: ateş hortumu ortam ekseni (event_structure.FIRE_TOR_ENVS). Sahne her zaman ağaçlık bir yerleşim;
    # açık arazi yok. Önceki iki nokta: "Overlook above the burning valley road" ("on a roadside overlook above the
    # burning valley road"), "Balcony of a roadside house" ("on a high balcony of a roadside house overlooking the road")
    # 18 Eki (2): ateş hortumu stil eki 175 için kısaldı. Önceki: "on a high balcony of a house at the edge of the
    # wooded neighborhood, looking down at the houses and trees" / "on a high balcony of a village house looking down
    # the street"
    "High balcony at the edge of a wooded neighborhood": "on a high balcony above the wooded neighborhood",
    # 21 Eki (genel kalite): 175 kelime için kısa. Önceki: "...above a wooded residential area", "on a high balcony
    # overlooking a tree-lined residential street"
    "Rooftop terrace above a wooded residential area": "on a rooftop terrace above a wooded area",
    "High balcony over a tree-lined residential street": "on a high balcony over a tree-lined street",
    "Upper-floor terrace above a street of houses": "on an upper-floor terrace above a street of houses",
    "Hillside terrace above a village": "on a hillside terrace above the village houses",
    "High balcony of a village house": "on a high balcony of a village house",
    # 🌋 Volkan (10 Eki, Bahadır): hepsi yüksek ve dağa bakıyor. 13 Eki: "facing the erupting volcano" volkan kamera
    # cümlesine taşındı (VOLCANO_CAMERA_PERCH); önceki metinler "..., facing the erupting volcano (across the street)"
    "Hillside terrace facing the erupting volcano": "on a hillside terrace above the village",
    "Rooftop terrace facing the erupting volcano": "on a rooftop terrace across the street",
    "Balcony of a village house facing the erupting volcano": "on a village house balcony across the street",   # 21 Eki: 175 (önceki "on the balcony of a village house...")
    # ❄️ Çığ (13 Eki, Bahadır): hepsi yüksek; yön kamera cümlesinde. 14 Eki: köyün/tesisin kenarına, çığın yoluna
    # taşındı. 14 Eki (2): kısa adlar, kamera cümlesi "Handheld footage from ..." (175 kelime sınırı). Önceki: "on a
    # terrace at the edge of the village", "on the balcony of a chalet at the edge of the village", "on the terrace
    # of the ski-lift station"
    "Terrace at the edge of the village": "a village-edge terrace",
    "Balcony of a chalet at the edge of the village": "a village-edge chalet balcony",
    "Terrace of the lift station": "the lift station terrace",
    # 🏚️ Deprem (14 Eki, Bahadır): karşı binada yüksekte; kamera cümlesi "Handheld footage from ..." (kısa adlar)
    "Rooftop terrace of a building across the street": "a rooftop terrace",
    "High-floor balcony across the street": "a high-floor balcony",
    # ☄️ Meteor (29 Eki, Bahadır): kadraj K1-K3, hepsi yüksek; tam cümle METEOR_CAMERA'da (birebir)
    "Rooftop terrace of a hillside villa above the bay": "the rooftop terrace of a modern hillside villa",
    "High balcony of a seafront apartment": "a high balcony of a seafront apartment",
    "Hilltop terrace above a coastal town": "a hilltop terrace above a coastal town",
    "Open sandy beach": "at the top of the beach",
    "Wide public beach": "at the top of the beach",
    "Beachfront promenade": "further along the promenade",
    "Coastal resort beach": "on a hotel terrace above the beach",
    "Beach parking area": "at the edge of the beach parking area",
}

# Gemi boşluğu: iskelette görünen ad (Seedance'ın tanıdığı biçim)
SHIP_PHRASES = {
    "Passenger Car Ferry": "passenger car ferry",
    "High-speed Catamaran": "twin-hull high-speed catamaran",
    "Luxury Motor Yacht": "luxury motor yacht",
    "Sailing Yacht": "sailing yacht",
    "Runaway Powerboat": "powerboat",
    "Ocean Cruise Liner": "ocean cruise liner",
    "Mega Cruise Ship": "mega cruise ship",
}

# Heyelan havası (2 Eki): üçü de şiddetli yağmur
LANDSLIDE_WEATHER = ["driving rain and wind", "heavy downpour under dark storm light", "steady heavy rain, grey low cloud"]
# Yangın havası (8 Eki, Bahadır): kuru ve dumanlı; yağmur/ıslaklık yok (event_structure yağmur kapısı denetler)
# Volkan havası (10 Eki, Bahadır)
VOLCANO_WEATHER = ["ash-grey sky lit orange by a distant eruption plume"]
# 18 Eki (3), Bahadır: bombalar ve kül bulutunda ışık çeşitliliği (ağırlıklı; mevcut metin bir seçenek). Her metin
# mevcut hava metninden (9 kelime) uzun değil. Kül bulutunda gece yok (gri bulut gecede kaybolur). Şok dalgası aynı.
# Gece metni Bahadır'ınkinden kısaldı (10 -> 9): "dark night sky lit by glowing lava and burning fires"
VOLCANO_WEATHER_WEIGHTS = {
    "Volcanic bombs slam into a village street": {
        "ash-grey sky lit orange by a distant eruption plume": 1,
        "warm orange dusk sky glowing from the eruption": 2,
        "pink-orange dawn light under a dark ash sky": 1,
        "dark night sky lit by glowing lava and fires": 1},
    "Pyroclastic cloud races down into a village street": {
        "ash-grey sky lit orange by a distant eruption plume": 2,
        "warm orange dusk sky glowing from the eruption": 1,
        "bright hazy daylight under a dark ash sky": 1},
}
# 18 Eki (3), Bahadır: bombalar ve kül bulutunda ORTAM ekseni (ateş hortumu gibi; kilit cümleye girmez). Metin kamera
# cümlesinde "the village street" yerine geçer ve GPT'ye PLACE satırında gider. Her metin ≤10 kelime; Bahadır'ın
# metinlerinden kısalanlar: A "a street of colorful concrete houses with parked cars and trucks" (11), B "a wide street
# of stone and painted houses in a hillside town" (12), D "a village street of wooden and stone houses among trees
# below the volcano" (13; volkan kamera cümlesinde zaten var).
VOLC_ENVS = {
    "pastel_town": {"label": "pastel kasaba caddesi",
                    "text": "a street of colorful concrete houses with parked trucks"},
    "hillside_town": {"label": "Akdeniz tepe kasabası",
                      "text": "a wide hillside-town street of stone and painted houses"},
    "suburb": {"label": "banliyö mahallesi",
               "text": "a suburban street of detached houses, garages and palm trees"},
    "mountain_village": {"label": "dağ eteği köyü",
                         "text": "a village street of wooden and stone houses among trees"},
}
# Ağırlıklar: bombalarda eşit; kül bulutunda renkli evler bulutu daha koyu gösteriyor (A=2, B=2, C=1, D=1)
VOLC_ENV_WEIGHTS = {
    "Volcanic bombs slam into a village street": {"pastel_town": 1, "hillside_town": 1, "suburb": 1,
                                                  "mountain_village": 1},
    "Pyroclastic cloud races down into a village street": {"pastel_town": 2, "hillside_town": 2, "suburb": 1,
                                                           "mountain_village": 1},
}
# Kamera noktası ağırlığı (yer metinleri aynı): sokağa yakın balkon 2 (hit), çatı terası ve yamaç terası (uzak/yüksek) 1
VOLC_SPOT_KIND = {"Balcony of a village house facing the erupting volcano": "balkon",
                  "Rooftop terrace facing the erupting volcano": "çatı",
                  "Hillside terrace facing the erupting volcano": "yamaç"}
VOLC_SPOT_WEIGHTS = {"balkon": 2, "çatı": 1, "yamaç": 1}
# Çığ havası (13 Eki, Bahadır): kapalı kış günü (giyim/ışık satırıyla aynı: "raw natural overcast daylight")
AVALANCHE_WEATHER = ["overcast winter daylight over snowy mountains"]
# Deprem havası (14 Eki): sadece iskelet hattı ve pick_setting için; yapılandırılmış hatta ortam havuzundan gelir
EARTHQUAKE_WEATHER = ["hazy dusty morning light"]
# Meteor ışık ekseni (29 Eki, Bahadır; son 2 tekrar etmez). Yapılandırılmış hatta "Setting: ortam, ışık." satırına girer
METEOR_WEATHER = ["golden sunset", "hazy midday light", "overcast grey sky"]
FIRE_WEATHER = ["hot dry wind and thick smoke haze", "gusty dry wind under an orange smoky sky",
                "heavy smoke and scorching still air"]

_CITY_SPOTS = {"Downtown city center": "the downtown city center", "Dense urban downtown": "a dense downtown street",
               "Commercial city streets": "a commercial street", "High-rise city district": "a high-rise district"}
_BEACH_SPOTS = {"Open sandy beach": "an open sandy beach", "Wide public beach": "a wide public beach",
                "Coastal resort beach": "a resort beach", "Beachfront promenade": "the beachfront promenade"}

# Olay → kilitli iskelet. {N}/{n}: kişi sayısı (yazıyla), {people}: rol, {ship}: gemi, {spot}: yer, {weather}: hava.
# "object": kameranın takip ettiği şey. "ships": None = gemisiz sahne.
EVENT_SKELETONS = {
    # ── Feribot ──
    "Lashing chain snaps and a parked car breaks loose": {
        "domain": "ferry_operations", "ships": ["Passenger Car Ferry", "High-speed Catamaran"],
        "spots": {"Open vehicle deck": "open vehicle deck", "Island crossing route": "open vehicle deck far out on an island crossing"},
        "people": ["deckhands", "passengers"], "weather": WEATHER_SEA, "object": "sliding car",
        "text": "On the {ship}'s {spot} in {weather}, a lashing chain snaps and a parked, driverless car breaks loose. "
                "The car slides sideways across the wet deck and slams into the next row as {n} {people} scramble clear. "
                "It keeps sliding with every roll of the {ship}, still grinding along the rail.",
    },
    "Loading ramp hinge snaps and the ramp drops": {
        "domain": "ferry_operations", "ships": ["Passenger Car Ferry"],
        "spots": {"Ferry terminal ramp": "the ferry terminal"},
        "people": ["dock workers", "passengers"], "weather": WEATHER_SEA, "object": "dropping ramp",
        "text": "At {spot} in {weather}, a hinge on the {ship}'s loading ramp snaps and the steel ramp drops hard onto "
                "the quay with a burst of spray. {N} {people} jump back as the ramp bucks and twists. It keeps grinding "
                "against the quay edge as the {ship} still surges against its lines.",
    },
    "Green wave breaks over the rail onto the vehicle deck": {
        "domain": "ferry_operations", "ships": ["Passenger Car Ferry", "High-speed Catamaran"],
        "spots": {"Open vehicle deck": "the open vehicle deck", "Island crossing route": "the open vehicle deck"},
        "people": ["deckhands", "passengers"], "weather": WEATHER_SEA, "object": "wave",
        "text": "In {weather}, a green wave breaks over the rail of the {ship} and pours across {spot}. The water sweeps "
                "between the parked, driverless cars and shoves them sideways as {n} {people} grab the railings. More "
                "seawater keeps surging over the rail, still pushing the cars across the vehicle deck.",
    },
    # ── Tersane ──
    "Restraining cable snaps during slipway launch": {
        "domain": "shipyard_and_drydock_engineering", "ships": ["Luxury Motor Yacht"],
        "spots": {"Construction slipway": "the construction slipway"},
        "people": ["shipyard workers"], "weather": WEATHER_SEA, "object": "tilting yacht",
        "text": "On {spot} in {weather}, a restraining cable snaps and whips across the concrete as the {ship} breaks "
                "free on its launch cradle. The {ship} slides bow-first down the inclined rails toward the open water "
                "while {n} {people} dive clear. It hits the water with a huge splash and keeps rolling and pitching.",
    },
    "Keel blocks collapse under the launching hull": {
        "domain": "shipyard_and_drydock_engineering", "ships": ["Luxury Motor Yacht", "Sailing Yacht"],
        "spots": {"Construction slipway": "the construction slipway"},
        "people": ["shipyard workers"], "weather": WEATHER_SEA, "object": "tilting hull",
        "text": "On {spot} in {weather}, the timber keel blocks under the {ship} collapse and splinter as it starts "
                "its launch. The hull drops onto the launch cradle and lurches down the inclined rails, tilting to one "
                "side as {n} {people} scramble away. The {ship} keeps sliding toward the water, still tilting.",
    },
    "Drydock flood gate bursts open": {
        "domain": "shipyard_and_drydock_engineering", "ships": ["Luxury Motor Yacht", "Sailing Yacht", "Passenger Car Ferry"],
        "spots": {"Drydock interior": "the drydock"},
        "people": ["shipyard workers"], "weather": WEATHER_SEA, "object": "rushing water",
        "text": "Inside {spot} in {weather}, the steel flood gate bursts open and a wall of seawater roars across the "
                "dock floor. The water lifts the {ship} off its keel blocks and swings it toward the dock wall as {n} "
                "{people} run for the ladders. The water keeps pouring in, still rising around the hull.",
    },
    "Timber shores snap and the hull tips on its keel blocks": {
        "domain": "shipyard_and_drydock_engineering", "ships": ["Luxury Motor Yacht", "Sailing Yacht", "Passenger Car Ferry"],
        "spots": {"Drydock interior": "the drydock"},
        "people": ["shipyard workers"], "weather": WEATHER_SEA, "object": "tipping hull",
        "text": "Inside {spot} in {weather}, the timber shores bracing the {ship} snap one after another. The hull tips "
                "sideways on its keel blocks, splinters flying, as {n} {people} sprint clear of its shadow. The {ship} "
                "keeps leaning further, still cracking the remaining shores as it tilts.",
    },
    "Crane sling snaps while lowering the hull into the water": {
        "domain": "shipyard_and_drydock_engineering", "ships": ["Luxury Motor Yacht", "Sailing Yacht"],
        "spots": {"Shipyard basin": "the shipyard basin"},
        "people": ["shipyard workers"], "weather": WEATHER_SEA, "object": "falling hull",
        "text": "Over {spot} in {weather}, one crane sling snaps while the {ship} is being lowered into the water. The "
                "hull swings nose-down and drops hard into the basin, throwing up a wall of spray as {n} {people} on the "
                "quay step back. The {ship} keeps rocking violently, still swinging on the last sling.",
    },
    # ── Marina ──
    # ÇIKARILDI (1 Eki, Bahadır): iki test videosunda (marina_yat_3 ve halat_kopar) halat kopması görünmedi, yat
    # serbest kalıp komşu yata çarpmadı; kural kapısından geçen prompt da yatı düzgün seyreder gösterdi. Olay havuzda
    # kalır, iskelette olmadığı için REMOVED_EVENTS'e düşer ve menüde görünmez. Geri almak için bu bloğu,
    # EVENT_OUTCOMES ve EVENT_REQUIRED satırlarını açmak yeterli.
    # "Mooring line snaps in a storm gust": {
    #     "domain": "marina_and_yacht_operations", "ships": ["Luxury Motor Yacht", "Sailing Yacht"],
    #     "spots": {"Floating pontoon dock": "the floating pontoon dock", "Marina fuel dock": "the marina fuel dock"},
    #     "people": ["marina staff", "boat owners"], "weather": WEATHER_SEA, "object": "swinging yacht",
    #     "text": "At {spot} in {weather}, a storm gust hits and a mooring line on the {ship} snaps with a crack. The "
    #             "{ship} swings away from the dock and slams its side into the next berth as {n} {people} scramble along "
    #             "the pontoon. It keeps swinging in the gusts, still straining against its last line.",
    # },
    "Storm surge wave lifts and buckles the floating pontoon": {
        "domain": "marina_and_yacht_operations", "ships": ["Luxury Motor Yacht", "Sailing Yacht", "Runaway Powerboat"],
        "spots": {"Floating pontoon dock": "the floating pontoon dock", "Marina fuel dock": "the marina fuel dock"},
        "people": ["marina staff", "boat owners"], "weather": WEATHER_SEA, "object": "buckling pontoon",
        "text": "At {spot} in {weather}, a storm surge wave rolls in and lifts the floating pontoon, buckling it like a "
                "ramp. The {ship} moored alongside is thrown against the bent pontoon as {n} {people} stumble and grab "
                "the cleats. More waves keep lifting the pontoon, still twisting it under the {ship}.",
    },
    "Passing boat's wake slams the boat sideways": {
        "domain": "marina_and_yacht_operations", "ships": ["Luxury Motor Yacht", "Sailing Yacht", "Runaway Powerboat"],
        "spots": {"Marina fairway": "the marina fairway", "Yacht club entrance": "the yacht club entrance",
                  "Floating pontoon dock": "the floating pontoon dock"},
        "people": ["marina staff", "boat owners"], "weather": WEATHER_SEA, "object": "rocking boat",
        "text": "In {spot} in {weather}, a passing boat's wake rolls in and slams the {ship} sideways. It heels hard, "
                "fenders squeal against the dock and loose gear flies off the deck as {n} {people} grab the rails. The "
                "wake keeps rocking the {ship}, still slamming it against the dock.",
    },
    # ÇIKARILDI (1 Eki, Bahadır): kontrolsüz yat videosunda yat kanaldan hızla geçti ama bağlı teknelere
    # çarpmadı, kontrollü seyreder göründü (halat olayıyla aynı hata). Not: tekne-tekneye çarpma Seedance'te iki
    # olayda da çıkmadı; su gücü olayları (wake, pontoon) iyi çıktı. Olay havuzda kalır, REMOVED_EVENTS'e düşer.
    # Geri almak için bu bloğu, EVENT_OUTCOMES ve EVENT_REQUIRED satırlarını açmak yeterli.
    # # EKLENDİ (1 Eki, Bahadır; TASLAK). Halat olayının yerine: yat kontrolü kaybeder, marinaya dalar ve bağlı
    # # teknelere çarpar. Motor yat; kişi 3-6 (marina aralığı), giyim marina kuralı (personel hi-vis).
    # "Yacht loses control and rams moored boats in the marina": {
    #     "domain": "marina_and_yacht_operations", "ships": ["Luxury Motor Yacht"],
    #     "spots": {"Breakwater at the marina entrance": "the marina entrance",
    #               "Marina berthing pier": "the marina berthing pier",
    #               "Narrow channel between moored boats": "the narrow channel between rows of moored boats"},
    #     "people": ["marina staff", "boat owners"],
    #     # rüzgârlı gün, yağmur ve rüzgâr, parlak gün + güçlü rüzgâr
    #     "weather": ["strong gusting wind", "driving rain and wind", "cold bright daylight with a strong wind"],
    #     "object": "runaway yacht",
    #     "text": "At {spot} in {weather}, the {ship} loses control and races into the marina at full speed. It rams the "
    #             "moored boats along the dock and shoves them aside as {n} {people} jump back onto the pontoon. The "
    #             "{ship} keeps plowing forward, still smashing into more moored boats.",
    # },
    # ── Kruvaziyer ──
    "Mooring line snaps and whips across the quay": {
        "domain": "cruise_ship_operations", "ships": ["Ocean Cruise Liner", "Mega Cruise Ship"],
        "spots": {"Cruise terminal berth": "the cruise terminal berth"},
        "people": ["dock workers", "passengers"], "weather": WEATHER_SEA, "object": "whipping line",
        "text": "At {spot} in {weather}, a thick mooring line from the {ship} snaps under load and whips across the "
                "quay. {N} {people} dive flat as the line lashes past, and the towering hull drifts away from the "
                "fenders. The loose line keeps thrashing on the quay while the {ship} still swings off the berth.",
    },
    "Gangway tears loose as the hull surges": {
        "domain": "cruise_ship_operations", "ships": ["Ocean Cruise Liner", "Mega Cruise Ship"],
        "spots": {"Cruise terminal berth": "the cruise terminal berth"},
        "people": ["dock workers", "passengers"], "weather": WEATHER_SEA, "object": "swinging gangway",
        "text": "At {spot} in {weather}, the {ship}'s hull surges against the fenders and the passenger gangway tears "
                "loose from its hinges. The gangway twists and drops at one end as {n} {people} scramble back onto the "
                "quay. It keeps swinging and scraping along the hull as the {ship} still surges.",
    },
    "Rogue wave breaks over the rail onto the pool deck": {
        "domain": "cruise_ship_operations", "ships": ["Ocean Cruise Liner", "Mega Cruise Ship"],
        "spots": {"Open-air pool deck": "the open-air pool deck"},
        "people": ["passengers"], "weather": WEATHER_SEA, "object": "wave",
        "text": "In {weather}, a rogue wave breaks over the rail of the {ship} and crashes onto {spot}. The water sweeps "
                "sun loungers and pool toys across the tiles as {n} {people} in swimwear scramble for the railings. More "
                "seawater keeps pouring over the rail, still surging across the pool deck.",
    },
    # ── Kıyı hortumu (gemisiz ortamlar) ──
    # ÇIKARILDI (4 Eki, Bahadır; TASLAK, onay bekliyor): hortum yapılandırılmış hatta 3 olayla (karaya vurma, marina,
    # sahil caddesi). Olay havuzda kalır, iskelette olmadığı için REMOVED_EVENTS'e düşer ve menüde görünmez. Geri
    # almak için bu bloğu, EVENT_OUTCOMES ve EVENT_REQUIRED satırlarını açmak yeterli.
    # "Tornado approaching coastline": {
    #     "domain": "coastal_tornado_landfall", "ships": None,
    #     "spots": {"Beachfront promenade": "the beachfront promenade", "Coastal resort beach": "a resort beach",
    #               "High-rise coastal city": "a high-rise waterfront"},
    #     "people": ["onlookers", "residents", "beachgoers"], "weather": WEATHER_STORM, "object": "tornado",
    #     "text": "In {weather}, a huge tornado spins across the sea toward {spot}, pulling up a column of spray. Debris "
    #             "starts lifting along the coast as {n} {people} run inland. The tornado keeps approaching the coastline, "
    #             "still tearing up water and debris.",
    # },
    "Tornado making landfall": {
        "domain": "coastal_tornado_landfall", "ships": None,
        "spots": {"Beachfront promenade": "the beachfront promenade", "Residential coastal district": "a coastal neighborhood",
                  "Downtown city center": "the downtown waterfront"},
        "people": ["onlookers", "residents", "pedestrians"], "weather": WEATHER_STORM, "object": "tornado",
        "text": "In {weather}, a tornado crosses the shoreline and makes landfall at {spot}, ripping roofs and signs "
                "into the air. Sand and debris whirl around its base as {n} {people} sprint for cover. The tornado keeps "
                "moving inland, still hurling debris across the street.",
    },
    # ÇIKARILDI (4 Eki, Bahadır; TASLAK, onay bekliyor): yukarıdaki notla aynı
    # "Tornado rain bands and flying debris lash the waterfront": {
    #     "domain": "coastal_tornado_landfall", "ships": None,
    #     "spots": {"Beachfront promenade": "the beachfront promenade", "Coastal resort beach": "a resort waterfront",
    #               "High-rise coastal city": "a high-rise waterfront"},
    #     "people": ["onlookers", "residents", "pedestrians"], "weather": WEATHER_STORM, "object": "flying debris",
    #     "text": "At {spot} in {weather}, the outer rain bands of a tornado lash the waterfront, driving sheets of rain "
    #             "sideways. Flying debris tumbles along the ground and smashes into railings as {n} {people} run for "
    #             "shelter. The rain bands keep sweeping in, still hurling debris across the waterfront.",
    # },
    # EKLENDİ (4 Eki, Bahadır; TASLAK, onay bekliyor). Gemisiz; tek spot marina kategorisinin rıhtımı.
    "Tornado crosses a marina quay": {
        "domain": "coastal_tornado_landfall", "ships": None,
        # 4 Eki, Bahadır: tek spot yüksek teras (eski: "Marina berthing pier": "the marina berthing pier beside
        # the quay road")
        "spots": {"High marina balcony": "the marina quay"},
        "people": ["onlookers", "boat owners", "pedestrians"], "weather": WEATHER_STORM, "object": "tornado",
        "text": "In {weather}, a tornado crosses the marina at {spot}, bending masts and ripping covers off the moored "
                "yachts. Canvas and debris whirl across the quay as {n} {people} run inland. The tornado keeps crossing "
                "the marina quay, still hurling debris toward the road.",
    },
    # EKLENDİ (4 Eki, Bahadır; TASLAK, onay bekliyor). Spotlar hortumun mevcut şehir spotları.
    "Tornado sweeps down a coastal avenue": {
        "domain": "coastal_tornado_landfall", "ships": None,
        # 10 Eki, Bahadır: kamera yüksek balkonda (eski: Downtown city center, Residential coastal district,
        # High-rise coastal city; aynı yer metinleri)
        "spots": {"High balcony over a downtown avenue": "a palm-lined coastal avenue downtown",
                  "Upper-floor balcony over a residential avenue":
                      "a palm-lined coastal avenue through a residential neighborhood",
                  "High balcony over a high-rise avenue": "a palm-lined coastal avenue below high-rise towers"},
        "people": ["onlookers", "residents", "pedestrians"], "weather": WEATHER_STORM, "object": "tornado",
        "text": "In {weather}, a tornado sweeps down {spot}, hurling signs, branches and debris along the road. Palm "
                "trees bend and snap as {n} {people} sprint for cover. The tornado keeps sweeping down the coastal "
                "avenue, still flinging debris across the street.",
    },
    # ── Şehir ──
    "Flash flooding in city streets": {
        "domain": "urban_city_disasters", "ships": None, "spots": _CITY_SPOTS,
        "people": ["pedestrians", "residents"], "weather": ["heavy rain", "driving rain and wind", "a dark storm light"],
        # 3 Eki, Bahadır: son test videosunda su duvarı yerine alçak köpük dalgası geldi; kilit görsel kodla sabit
        "object": "waist-high wall of brown muddy floodwater",
        "text": "In {spot} in {weather}, a brown flash flood surges down the block, rising over the curbs. The "
                "fast water shoves parked cars sideways and carries one down the road as {n} {people} climb onto steps "
                "and ledges. The flood keeps rising, still dragging the car along the street.",
    },
    # ÇIKARILDI (30 Eyl, Bahadır): aksiyonsuz videolar veriyordu. Olay havuzda kalır, iskelette olmadığı için
    # REMOVED_EVENTS'e düşer ve menüde görünmez. Geri almak için bu bloğu, EVENT_OUTCOMES ve EVENT_REQUIRED
    # satırlarını açmak yeterli.
    # "Storm gust tears signs and scaffolding loose downtown": {
    #     "domain": "urban_city_disasters", "ships": None, "spots": _CITY_SPOTS,
    #     "people": ["pedestrians", "residents"], "weather": WEATHER_SEA, "object": "flying scaffolding",
    #     "text": "In {spot} in {weather}, a violent storm gust tears a sign and a sheet of scaffolding loose from a "
    #             "building downtown. The metal crashes onto the street and parked cars as {n} {people} sprint for "
    #             "doorways. The gust keeps ripping more panels loose, still tumbling debris across the road.",
    # },
    # EKLENDİ (30 Eyl, Bahadır onayı). Kaynak: 24 Eyl videosu (dosya 1790240764259-vf8owrlvyva), "A towering tidal
    # wave crashes over the coastal road, sweeping parked cars into storefronts." Gemi yok; kişi 2-10 (env-centric).
    "Tidal wave surges over a coastal city street": {
        "domain": "urban_city_disasters", "ships": None,
        "spots": {"Coastal road below a seafront promenade": "the coastal road below a raised seafront promenade",
                  "Coastal street of low shopfronts": "a coastal street lined with low shopfronts",
                  "Coastal avenue behind a seawall": "the coastal avenue behind the seawall"},
        "people": ["pedestrians", "residents"],
        # şehir hava listesinden; "a dark storm light" ve "stormy late-afternoon light" dramatik gökyüzü
        "weather": ["driving rain and wind", "a dark storm light", "stormy late-afternoon light", "strong gusting wind"],
        "object": "tidal wave",
        "text": "At {spot} in {weather}, a towering tidal wave crashes over the sea wall onto the coastal road. The "
                "water sweeps parked cars into the storefronts as {n} {people} run for the upper floors. The wave "
                "keeps surging down the street, still carrying cars and debris inland.",
    },
    # ── Heyelan (TASLAK) ──
    # 2 Eki, Bahadır: Seedance hızlı akan su gücünü iyi çiziyor, yavaş kayan toprağı 15 sn'de göstermiyor; heyelan,
    # aşırı yağıştan yamaçtan hızla inen çamur ve su akıntısı olarak tanımlanır (kayma/yükselme/yavaş çökme yok).
    "Mudslide pours down a hillside street": {
        "domain": "landslide_disasters", "ships": None,
        "spots": {"Balcony across a steep hillside street": "a steep hillside street",
                  "Rooftop terrace below a hillside street": "a steep residential street running down the hillside",
                  "Side stairway off a narrow hillside lane": "a narrow hillside lane"},
        "people": ["residents", "pedestrians"], "weather": LANDSLIDE_WEATHER, "object": "mud flow",
        "text": "On {spot} in {weather}, a mudslide pours down the hillside street as a wall of brown mud and water. "
                "It slams into parked cars and shoves them sideways as {n} {people} run uphill from the flow. The "
                "mud keeps pouring down the street, still dragging the cars along.",
    },
    "Rain-soaked slope collapses onto a roadside": {
        "domain": "landslide_disasters", "ships": None,
        "spots": {"Behind the guardrail of a hillside road": "a road cut into a steep hillside",
                  # ÇIKARILDI (2 Eki, Bahadır): bu noktadan çekilen testte çamur yola ulaşmadı; 2. deneme
                  # "Far edge of the road" ile çözüldü. Ortam ve kamera cümlesi havuzda kalır, geri almak için aç.
                  # "Bridge on a side road below the slope": "a hillside road below a steep slope",
                  "Far edge of the road across from the slope": "a road at the foot of a steep slope"},
        "people": ["drivers", "residents"], "weather": LANDSLIDE_WEATHER, "object": "mud torrent",
        "text": "At {spot} in {weather}, the rain-soaked slope collapses onto the roadside and a fast torrent of mud "
                "and rocks surges across the road. It pushes cars into the guardrail as {n} {people} scramble out. "
                "More mud keeps pouring off the slope, still shoving the cars along the road.",
    },
    "Mud and debris torrent tears through a hillside village": {
        "domain": "landslide_disasters", "ships": None,
        "spots": {"Terrace on the opposite hillside": "a hillside village of stone houses",
                  "High steps on the village square": "a hillside village above its square",
                  "Upper-floor balcony of a village house": "a steep hillside village"},
        "people": ["villagers", "residents"], "weather": LANDSLIDE_WEATHER, "object": "debris torrent",
        "text": "In {spot} in {weather}, a mud and debris torrent tears through the hillside village, carrying logs "
                "and rocks between the houses. It rams walls and sweeps away fences and parked vehicles as {n} "
                "{people} run to higher ground. The torrent keeps tearing downhill, still ramming more walls.",
    },
    # ── Yangın (TASLAK, 8 Eki, Bahadır) ──
    # Yapılandırılmış hatta (core/event_structure.py); bu metin sadece PROMPT_PIPELINE=skeleton içindir.
    # Yer metinleri Bahadır'ın ortam tarifleri; kamera noktası spot anahtarı (heyelan deseni).
    "Wall of flames sweeps into a hillside neighborhood": {
        "domain": "fire_disasters", "ships": None,
        "spots": {"Balcony of a hillside house": "a hillside village neighborhood",
                  "Embankment above the village road": "a hillside village neighborhood"},
        "people": ["residents", "villagers"], "weather": FIRE_WEATHER, "object": "wall of flames",
        "text": "In {spot} in {weather}, a towering wall of flames sweeps down the forested slope into the "
                "neighborhood, igniting roofs and trees. Glowing embers shower the street as {n} {people} run from "
                "the flames. The fire keeps spreading from house to house, still igniting more roofs.",
    },
    "Flames race up a tower facade": {
        "domain": "fire_disasters", "ships": None,
        # 8 Eki (2): 4 nokta, hepsi yüksek (balkon + çatı terası)
        "spots": {"Balcony across from a downtown tower": "the downtown city center",
                  "Rooftop terrace across from a downtown tower": "the downtown city center",
                  "Balcony across from a coastal high-rise": "a high-rise coastal city",
                  "Rooftop terrace across from a coastal high-rise": "a high-rise coastal city"},
        "people": ["pedestrians", "residents"], "weather": FIRE_WEATHER, "object": "burning facade",
        "text": "In {spot} in {weather}, flames race up the glass facade of a tower, blowing out windows. Burning "
                "debris falls onto the street as {n} {people} run from the tower. The fire keeps climbing floor "
                "after floor, still blowing out more windows.",
    },
    "Fire tornado tears across a burning roadside": {
        "domain": "fire_disasters", "ships": None,
        # 16 Eki, Bahadır: ortam ekseni, ortam başına 2 nokta (yer metni GPT'ye PLACE olarak gider). Önceki: iki nokta,
        # yer metni "a burning valley road"
        "spots": {"High balcony at the edge of a wooded neighborhood": "a residential area at the edge of a burning forest",
                  "Rooftop terrace above a wooded residential area": "a residential area at the edge of a burning forest",
                  "High balcony over a tree-lined residential street": "a burning tree-lined residential street",
                  "Upper-floor terrace above a street of houses": "a burning tree-lined residential street",
                  "Hillside terrace above a village": "a village of houses at the edge of the burning woods",
                  "High balcony of a village house": "a village of houses at the edge of the burning woods"},
        "people": ["drivers", "residents"], "weather": FIRE_WEATHER, "object": "fire tornado",
        "text": "On {spot} in {weather}, a violent fire tornado tears across the burning roadside, hurling flames "
                "and burning branches across the road. Embers whirl around its base as {n} {people} run from it. "
                "The fire tornado keeps tearing along the road, still flinging burning debris.",
    },
    # 10 Eki, Bahadır: helikopter. Kamera noktaları orman yangınıyla aynı iki yüksek nokta (alçak kamera yok)
    "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood": {
        "domain": "fire_disasters", "ships": None,
        "spots": {"Balcony of a hillside house": "a hillside village neighborhood",
                  "Embankment above the village road": "a hillside village neighborhood"},
        "people": ["residents", "villagers"], "weather": FIRE_WEATHER, "object": "firefighting helicopter",
        "text": "In {spot} in {weather}, a firefighting helicopter swoops over the neighborhood and drops a huge load "
                "of water onto the wall of flames racing toward the houses. Thick white steam rolls up as {n} {people} "
                "run from the flames. The helicopter circles back, still fighting the fire along the slope.",
    },
    # ── 🌋 Volkan (TASLAK, 10 Eki, Bahadır). Yapılandırılmış hatta; metin sadece PROMPT_PIPELINE=skeleton için. Kamera noktalarının hepsi yüksek ve dağa bakıyor. ──
    "Volcano erupts and a shockwave blows out windows": {
        "domain": "volcano_disasters", "ships": None,
        "spots": {"Hillside terrace facing the erupting volcano": "a village street below the erupting volcano",
                  "Rooftop terrace facing the erupting volcano": "a village street below the erupting volcano",
                  "Balcony of a village house facing the erupting volcano": "a village street below the erupting volcano"},
        "people": ["residents", "villagers"], "weather": VOLCANO_WEATHER, "object": "ash column",
        "text": "In {spot} under {weather}, the volcano erupts above the village and a shockwave blows out windows "
                "along the street. Roof tiles and signs tear loose as {n} {people} run from the eruption. The "
                "ash column keeps towering above the volcano, still hurling glowing rocks.",
    },
    "Pyroclastic cloud races down into a village street": {
        "domain": "volcano_disasters", "ships": None,
        "spots": {"Hillside terrace facing the erupting volcano": "a village street on the lower flank of the volcano",
                  "Rooftop terrace facing the erupting volcano": "a village street on the lower flank of the volcano",
                  "Balcony of a village house facing the erupting volcano": "a village street on the lower flank of the volcano"},
        "people": ["residents", "villagers"], "object": "pyroclastic cloud",
        "weather": list(VOLCANO_WEATHER_WEIGHTS["Pyroclastic cloud races down into a village street"]),   # 18 Eki (3)
        "text": "In {spot} under {weather}, a pyroclastic cloud races down the volcano's flank and slams into the "
                "street, tearing balconies off the houses and roof tiles off the rooftops as {n} {people} run from the "
                "cloud. The cloud keeps rolling through the village, still ripping roofs apart.",
    },
    "Volcanic bombs slam into a village street": {
        "domain": "volcano_disasters", "ships": None,
        "spots": {"Hillside terrace facing the erupting volcano": "a village street below the erupting volcano",
                  "Rooftop terrace facing the erupting volcano": "a village street below the erupting volcano",
                  "Balcony of a village house facing the erupting volcano": "a village street below the erupting volcano"},
        "people": ["residents", "villagers"], "object": "glowing rocks",
        "weather": list(VOLCANO_WEATHER_WEIGHTS["Volcanic bombs slam into a village street"]),   # 18 Eki (3)
        "text": "In {spot} under {weather}, glowing volcanic bombs streak down and slam into the street, punching "
                "through roofs and igniting cars as {n} {people} run from the falling rocks. More rocks keep "
                "crashing down, still setting the street alight.",
    },
    # ── ❄️ Çığ (TASLAK, 13 Eki, Bahadır). Yapılandırılmış hatta; metin sadece PROMPT_PIPELINE=skeleton için. Kamera
    # noktaları yüksek; teleferik istasyonu terası sadece kayak olayında. ──
    "Avalanche slams into a mountain village": {
        "domain": "avalanche_disasters", "ships": None,
        "spots": {"Terrace at the edge of the village": "a mountain village below a steep snowy slope",
                  "Balcony of a chalet at the edge of the village": "a mountain village below a steep snowy slope"},
        "people": ["residents", "villagers"], "weather": AVALANCHE_WEATHER, "object": "avalanche",
        "text": "In {spot} under {weather}, a powder avalanche thunders down the mountainside and slams into the "
                "village, a wall of snow engulfing the first chalets. Roofs and fences tear loose as {n} {people} run from "
                "the avalanche. The snow wall keeps tearing between the houses, still flattening chalets.",
    },
    "Avalanche crashes down onto a ski lodge": {
        "domain": "avalanche_disasters", "ships": None,
        "spots": {"Terrace at the edge of the village": "a ski resort at the foot of a steep ski slope",
                  "Balcony of a chalet at the edge of the village": "a ski resort at the foot of a steep ski slope",
                  "Terrace of the lift station": "a ski resort at the foot of a steep ski slope"},
        "people": ["guests", "residents"], "weather": AVALANCHE_WEATHER, "object": "avalanche",
        "text": "In {spot} under {weather}, an avalanche crashes down the ski slope onto the lodge, a cloud of snow "
                "bursting over its terrace. Lift towers snap as {n} {people} run from the avalanche. The snow keeps "
                "crashing down the slope, still burying the lodge.",
    },
    "Avalanche rips through a pine forest into a valley": {
        "domain": "avalanche_disasters", "ships": None,
        "spots": {"Terrace at the edge of the village": "a valley below a steep pine forest",
                  "Balcony of a chalet at the edge of the village": "a valley below a steep pine forest"},
        "people": ["residents", "villagers"], "weather": AVALANCHE_WEATHER, "object": "avalanche",
        "text": "In {spot} under {weather}, a huge avalanche rips through the pine forest above the valley and hits the "
                "houses below. Snapped trunks fly as {n} {people} run from the avalanche. The white cloud keeps rolling "
                "down into the valley, still burying the houses.",
    },
    # ── 🏚️ Deprem (TASLAK, 14 Eki, Bahadır). Yapılandırılmış hatta; metin sadece PROMPT_PIPELINE=skeleton için. Kamera
    # karşı binada yüksekte. ──
    "Earthquake collapses an apartment block": {
        "domain": "earthquake_disasters", "ships": None,
        "spots": {"Rooftop terrace of a building across the street": "a residential street lined with apartment blocks",
                  "High-floor balcony across the street": "a residential street lined with apartment blocks"},
        "people": ["residents", "neighbours"], "weather": EARTHQUAKE_WEATHER, "object": "collapse",
        "text": "In {spot} under {weather}, the ground shakes violently and a six-storey apartment block collapses "
                "floor by floor, a huge dust cloud bursting out. Concrete slabs crash onto the road as {n} {people} run "
                "from the collapsing buildings. The dust keeps rolling down the street as the block next door starts "
                "to fall.",
    },
    "Earthquake collapses a row of old stone houses": {
        "domain": "earthquake_disasters", "ships": None,
        "spots": {"Rooftop terrace of a building across the street": "a narrow residential street of old stone houses",
                  "High-floor balcony across the street": "a narrow residential street of old stone houses"},
        "people": ["residents", "neighbours"], "weather": EARTHQUAKE_WEATHER, "object": "collapse",
        "text": "In {spot} under {weather}, the ground shakes violently and a row of old stone houses collapses one "
                "after another, dust and rubble bursting into the street. Roofs fall in as {n} {people} run from the "
                "collapsing buildings. The collapse keeps running down the street, house after house.",
    },
    # ── ☄️ Meteor (TASLAK, 29 Eki, Bahadır). Yapılandırılmış hatta; metin sadece PROMPT_PIPELINE=skeleton için. Kamera
    # yüksekte, körfeze bakar; araç değil, ev ve insanlar. ──
    "Meteor slams into the sea off the coast": {
        "domain": "meteor_disasters", "ships": None,
        "spots": {"Rooftop terrace of a hillside villa above the bay": "a hillside of modern villas above the bay",
                  "High balcony of a seafront apartment": "a seafront promenade below modern apartments",
                  "Hilltop terrace above a coastal town": "a coastal town around a wide bay"},
        "people": ["residents", "people"], "weather": METEOR_WEATHER, "object": "impact",
        "text": "Over {spot} in {weather}, a blazing meteor streaks down and slams into the sea just off the coast in a "
                "blinding flash and a towering column of water. The blast tears across the waterfront as {n} {people} "
                "run inland. Flaming debris keeps crashing onto the roofs of the houses.",
    },
    # ── Plaj & sahil ──
    "Tornado approaching an open beach": {
        "domain": "open_beach_coastal_events", "ships": None,
        "spots": {k: v for k, v in _BEACH_SPOTS.items() if k != "Beachfront promenade"},
        "people": ["beachgoers", "onlookers"], "weather": WEATHER_STORM, "object": "tornado",
        "text": "In {weather}, a tornado spins across the sea toward {spot}, lifting sand into a spinning wall. Beach "
                "umbrellas and towels fly up as {n} {people} run toward the dunes. The tornado keeps approaching the open "
                "beach, still ripping sand and debris into the air.",
    },
    "Storm gust rips umbrellas and beach chairs into the air": {
        "domain": "open_beach_coastal_events", "ships": None, "spots": _BEACH_SPOTS,
        "people": ["beachgoers", "onlookers"], "weather": WEATHER_SEA, "object": "flying umbrellas",
        "text": "At {spot} in {weather}, a storm gust rips beach umbrellas and chairs out of the sand and flings them "
                "into the air. Chairs cartwheel along the beach as {n} {people} duck and run. The gusts keep tearing "
                "more umbrellas loose, still tumbling chairs across the sand.",
    },
    "Large waves reaching the beach": {
        "domain": "open_beach_coastal_events", "ships": None, "spots": _BEACH_SPOTS,
        "people": ["beachgoers", "onlookers"], "weather": WEATHER_SEA, "object": "waves",
        "text": "At {spot} in {weather}, a line of large waves rolls in and breaks far up the beach. The whitewater "
                "rushes over the sand, sweeping towels and chairs inland as {n} {people} run up the beach. More waves "
                "keep reaching the beach, still surging higher each time.",
    },
}

ALL_EVENTS = [e for a in DOMAIN_ATTRIBUTES.values() for e in a["events"]]
# Bu hatta olmayan olaylar (görünür büyük fiziksel tetik yok / başka olayın kopyası / dikey kadraja sığmıyor)
REMOVED_EVENTS = [e for e in ALL_EVENTS if e not in EVENT_SKELETONS]

# ── BÖLGE GÖRÜNÜMÜ (1 Eki, Bahadır: aynı ortamda tekrar eden videolar) ─────────────────────────────────────────
# Şehir olaylarında Python, gemi seçer gibi LRU ile bir görünüm seçer (olay başına ayrı döngü). Spot kamera
# konumunu verir, görünüm mimari, sokak ve araçları; ışığı hava belirler (gökyüzü ifadesi yok). Görünüm hem GPT girdisine (PLACE) hem stil ekine girer. Prompt'a ülke/şehir adı, bayrak ya da
# yazı girmez; ülke ilhamı sadece bu yorumlarda. Giyim her görünümde nötr (etnik/kültürel giyim tarif edilmez).
# Seçilen görünüm combo_key'in yer parçasına "#görünüm" olarak yazılır (Notion şeması değişmez, 5 parça korunur).
REGION_VIEW_EVENTS = ("Flash flooding in city streets", "Tidal wave surges over a coastal city street")
REGION_VIEWS = {
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: Körfez metropolü (BAE, Katar)
    "gulf_metropolis": "glass towers behind palm-lined boulevards, sand-colored low buildings, white SUVs",   # 21 Eki: -"multi-lane" (175)
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: Kuzey Afrika kıyısı (Fas, Tunus)
    # 17 Eki, Bahadır (temizlik turu): küçük araç yok. Önceki: "small hatchback cars"
    "north_african_coast": "sand-colored flat-roofed buildings, narrow streets, cloth awnings, large SUVs",
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: ABD kıyı kasabası (Florida, Carolina)
    "us_coastal_town": "wide asphalt roads, pickup trucks, low wooden and brick houses, power lines",   # 21 Eki: -"overhead" (175)
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: Kuzey Avrupa sahil kasabası (Hollanda, İngiltere)
    # 17 Eki: küçük araç yok. Önceki: "small parked cars"
    "north_european_seaside": "brick terraced houses, narrow streets, parked SUVs and vans",
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: Riviera (Fransa, İtalya)
    # 4 Eki, Bahadır: "cobbled promenade" GPT'ye caddeyi "promenade" diye yazdırıyordu (sel kuru provası, olay adı
    # kuralından ret); "cobbled streets" oldu. Kıyı dev dalga da bu görünümü kullanır.
    "riviera": "cream stone buildings with shuttered windows, cobbled streets, scooters, plane trees",
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: Doğu Asya kıyısı (Japonya, Tayvan)
    # 1 Eki (2): videoda Akdeniz çıktı; "covered arcade entrances" Akdeniz çağrışımı yaptı, klima ve kablo eklendi
    # 17 Eki: küçük araç yok. Önceki son parça: "small boxy cars and scooters"
    # 21 Eki (genel kalite): 175 kelime için kısa. Önceki: "...and tangled overhead wires, narrow lanes, delivery vans
    # and box trucks"
    "east_asian_coast": "dense mid-rise apartment blocks with air-conditioners and tangled wires, narrow lanes, "
                        "delivery vans",
}
REGION_VIEW_CLOTHING = "people in light everyday clothes suited to the climate"
NO_SIGNS = "no readable signs, text or flags"
# Spot ile görünüm cümlede çakışmasın: yüksek bina yeri alçak yapılı görünümlerle, alçak dükkanlı sokak yoğun orta
# katlı görünümle, yoğun şehir merkezi küçük kasaba görünümüyle eşleşmez. Kamera konumu yine spot'tan gelir.
REGION_VIEW_EXCLUDED_SPOTS = {
    "north_african_coast": {"High-rise city district"},
    "us_coastal_town": {"High-rise city district", "Dense urban downtown"},
    "north_european_seaside": {"High-rise city district"},
    "riviera": {"High-rise city district"},
    "east_asian_coast": {"High-rise city district", "Coastal street of low shopfronts"},
}


def view_spots(event: str, view: str | None) -> list[str]:
    """Olayın görünümle çakışmayan spot'ları (görünüm yoksa hepsi)."""
    spots = list(EVENT_SKELETONS[event]["spots"])
    return [s for s in spots if s not in REGION_VIEW_EXCLUDED_SPOTS.get(view or "", set())]


def view_of_combo(combo_key: str) -> str | None:
    """combo_key yer parçasındaki görünüm ("...|yer#görünüm|..."), yoksa None."""
    parts = (combo_key or "").split("|")
    if len(parts) != 5 or "#" not in parts[3]:
        return None
    # 4 Eki: yer parçası "spot#görünüm#V3+D5" olabilir (yapılandırılmış olaylarda olay çifti)
    return parts[3].split("#")[1].strip().lower() or None


# Süreç içi görünüm hafızası (1 Eki, yedek). Sebep: 1 Eki 15:34 ve 15:45 kıyı dalga üretimleri, ikisi de
# east_asian_coast. Notion geçmişi (get_used_combos) artık TEST modunda bitenleri de sayar; iptal edilen ve henüz
# bitmemiş üretimler orada yok, onları bu hafıza kapsar. Seçim anında yazılır, Notion geçmişinden daha yeni sayılır.
# Bot üretimi aynı süreçte çalıştırır; yeniden başlatmada (deploy) silinir, o zaman sadece Notion geçmişi kalır.
_VIEW_MEMORY: dict[str, list[str]] = {}
_VIEW_MEMORY_LIMIT = 12
_VIEW_LOCK = threading.Lock()


def remember_view(event: str, view: str | None) -> None:
    """Seçilen görünümü süreç hafızasına yazar (üretim bitmeden, seçim anında)."""
    if not view:
        return
    with _VIEW_LOCK:
        _VIEW_MEMORY.setdefault(event, []).append(view)
        del _VIEW_MEMORY[event][:-_VIEW_MEMORY_LIMIT]


def view_history(event: str, history: list[str]) -> list[str]:
    """Olayın görünüm geçmişi, eskiden yeniye: Notion kayıtları + süreç hafızası. Hafızadaki her üretim Notion'dakinden
    yenidir; aynı üretim iki yerde de varsa (çift sayım) Notion'daki kopyası düşer, sıra hafızadan gelir."""
    same = [h for h in history if is_current_universe_combo(h) and h.split("|")[2].strip().lower() == event.lower()]
    with _VIEW_LOCK:
        memory = list(_VIEW_MEMORY.get(event, []))
    notion = [v for v in (view_of_combo(h) for h in same) if v and v not in memory]
    return notion + memory


def choose_region_view(event: str, history: list[str]) -> str | None:
    """Şehir olayları için LRU görünüm, olay başına ayrı döngü: sadece aynı olayın kayıtları sayılır, son seçilen
    tekrar gelmez. Geçmiş = Notion kayıtları + süreç hafızası (daha yeni). Diğer olaylar için None."""
    if event not in REGION_VIEW_EVENTS:
        return None
    seen = view_history(event, history)
    return _lru(list(REGION_VIEWS), seen)


def view_district(event: str, view: str) -> str:
    """Görünümün cümle hâli. Kıyı dalgasında her görünüm kıyıda geçer."""
    kind = "seafront district" if event == "Tidal wave surges over a coastal city street" else "city district"
    return f"a {kind} with {REGION_VIEWS[view]}"


def view_place(event: str, place: str, view: str | None) -> str:
    """GPT'ye giden PLACE: spot cümlesi + görünüm."""
    return f"{place}, in {view_district(event, view)}" if view else place

# Olayların fiziksel türü (rapor ve menü gruplama için; seçim mantığına girmez)
PHENOMENA = {
    # 4 Eki (TASLAK): kıyıya yaklaşma ve yağmur bantları menüden çıktı, marina ve sahil caddesi eklendi
    "Hortum": ["Tornado making landfall", "Tornado crosses a marina quay", "Tornado sweeps down a coastal avenue",
               "Tornado approaching an open beach"],
    "Tsunami": [],
    "Sel": ["Flash flooding in city streets"],
    "Heyelan": ["Mudslide pours down a hillside street", "Rain-soaked slope collapses onto a roadside", "Mud and debris torrent tears through a hillside village"],
    # 8 Eki (TASLAK)
    "Yangın": ["Wall of flames sweeps into a hillside neighborhood", "Flames race up a tower facade",
               "Fire tornado tears across a burning roadside",
               "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood"],   # 10 Eki
    # 10 Eki (TASLAK)
    # 13 Eki (4): lav nehri çıkarıldı
    "Volkan": ["Volcano erupts and a shockwave blows out windows",
               "Pyroclastic cloud races down into a village street", "Volcanic bombs slam into a village street"],
    # 13 Eki (TASLAK)
    "Çığ": ["Avalanche slams into a mountain village", "Avalanche crashes down onto a ski lodge", "Avalanche rips through a pine forest into a valley"],
    # 14 Eki (TASLAK)
    "Deprem": ["Earthquake collapses an apartment block", "Earthquake collapses a row of old stone houses"],
    # 29 Eki (TASLAK)
    "Meteor": ["Meteor slams into the sea off the coast"],
    "Dev Dalga": ["Green wave breaks over the rail onto the vehicle deck", "Rogue wave breaks over the rail onto the pool deck",
                  "Large waves reaching the beach", "Storm surge wave lifts and buckles the floating pontoon",
                  "Tidal wave surges over a coastal city street"],
}

_NUM = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen",
        18: "eighteen", 19: "nineteen", 20: "twenty"}
ENV_CENTRIC_COUNT = (2, 10)
# Domain'e özel kişi aralığı (env-centric içinde). 2 Eki, Bahadır: heyelan 2-8
ENV_CENTRIC_COUNT_BY_DOMAIN = {"landslide_disasters": (2, 8)}
# Olaya özel kişi aralığı (domain'den önce gelir). 4 Eki, Bahadır: kıyı dev dalgada küçük, belirli sayı 3-6
EVENT_COUNT = {"Tidal wave surges over a coastal city street": (3, 6),
               # 4 Eki, Bahadır onayı (canlı, 5c9ca3d): heyelan 3-6
               "Mudslide pours down a hillside street": (3, 6),
               "Rain-soaked slope collapses onto a roadside": (3, 6),
               "Mud and debris torrent tears through a hillside village": (3, 6),
               # TASLAK (4 Eki, Bahadır hazırlığı, onay bekliyor): hortum 3-6
               "Tornado making landfall": (3, 6),
               "Tornado crosses a marina quay": (3, 6),
               "Tornado sweeps down a coastal avenue": (3, 6),
               # TASLAK (8 Eki, Bahadır): yangın 3-6
               "Wall of flames sweeps into a hillside neighborhood": (3, 6),
               "Flames race up a tower facade": (3, 6),
               # 15 Eki (2), Bahadır: ateş hortumunda ön planda 2-3 kişi kaçar
               "Fire tornado tears across a burning roadside": (2, 3),
               # 10 Eki, Bahadır: helikopter 3-6 (orman gibi)
               "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood": (3, 6),
               # TASLAK (10 Eki, Bahadır): volkan 3-6
               "Volcano erupts and a shockwave blows out windows": (3, 6),
               "Pyroclastic cloud races down into a village street": (3, 6),
               "Volcanic bombs slam into a village street": (3, 6),
               # TASLAK (13 Eki, Bahadır): çığ 3-6
               "Avalanche slams into a mountain village": (3, 6), "Avalanche crashes down onto a ski lodge": (3, 6), "Avalanche rips through a pine forest into a valley": (3, 6),
               # TASLAK (14 Eki, Bahadır): deprem 3-6
               "Earthquake collapses an apartment block": (3, 6), "Earthquake collapses a row of old stone houses": (3, 6),
               # TASLAK (29 Eki, Bahadır): meteor 3-6
               "Meteor slams into the sea off the coast": (3, 6)}
# "No readable signs, text or flags" ayrı cümle olarak stil ekine girer (şehirde görünüm cümlesinin içinde)
NO_SIGNS_DOMAINS = {"landslide_disasters",
                    "fire_disasters",   # 8 Eki: yangın (heyelan deseni, toplam 8 kısıt)
                    "volcano_disasters",   # 10 Eki: volkan
                    "avalanche_disasters",   # 13 Eki: çığ (yazı/tabela yok)
                    "earthquake_disasters",   # 14 Eki: deprem (yazı/tabela/bayrak yok)
                    "meteor_disasters"}   # 29 Eki: meteor (yazı/tabela/bayrak yok)

# Import anında kontrol: iskelet verisi havuzla uyumlu olmalı
for _e, _s in EVENT_SKELETONS.items():
    _a = DOMAIN_ATTRIBUTES[_s["domain"]]
    _bad = [x for x in (_s["ships"] or []) if x not in _a["ships"] or x not in SHIP_PHRASES]
    _bad += [x for x in _s["spots"] if x not in _a["environments"] or x not in CAMERA_SPOTS]
    if _e not in _a["events"] or _bad:
        raise RuntimeError(f"EVENT_SKELETONS[{_e}] havuzla uyuşmuyor: {_bad}")


# Olaya özel kamera hareketi eki (kamera cümlesinin içinde, virgülle; yeni kısıt sayılmaz). 3 Eki, Bahadır: sel
# test videosunda kameraya çok yakın koşan adam ~7. sn'de başka birine dönüştü, kamera savrulunca arkadaki
# gökdelenler de şekil değiştirdi.
CAMERA_MOTION_EXTRA = {
    "Flash flooding in city streets": " in one slow short arc, never swinging around, people only in the middle and "
                                      "far distance",
    # 10 Eki volkan eki ("the erupting volcano always visible above the rooftops") 13 Eki'de volkan kamera cümlesine
    # taşındı (VOLCANO_CAMERA_PERCH)
}

# 🌋 Volkan kamera sabitleme (13 Eki 2026, Bahadır). Sebep: "the camera pans to follow the lava river / pyroclastic
# cloud" ile 3 videoda Kie kamerayı terastan sokak seviyesine indirdi, kamera olaydan kaçtı, ikinci yarıda yüksek açı
# kayboldu, bir videoda gizli kesme oldu. Volkanın 4 olayında takip (pan) yok: kamera durduğu yerde sabit, sadece
# hafif eğilir. Değer: kameranın durduğu yerin kısa adı ("stays fixed in place on the ..."). Kısıt sayısı değişmedi (3).
VOLCANO_CAMERA_PERCH = {
    "Hillside terrace facing the erupting volcano": "terrace",
    "Rooftop terrace facing the erupting volcano": "rooftop",
    "Balcony of a village house facing the erupting volcano": "balcony",
}


# 18 Eki, Bahadır: kül bulutuna bu turda dokunulmaz; kısa şablon sadece patlama (şok dalgası) ve bombalarda
VOLCANO_SHORT_CAMERA_EXCLUDED = ("Pyroclastic cloud races down into a village street",)


def volcano_camera(spot: str, event: str | None = None, volc_env: str | None = None) -> str:
    # 13 Eki (2), Bahadır: lav testinde kamera aşağı eğilip volkanı kadrajdan çıkardı, çekim drone gibi göründü.
    # Volkan üst üçte birde, eğilme sınırı, ön planda korkuluk köşesi eklendi (kamera cümlesinin içinde, virgülle).
    # Korkuluk durulan yerin adıyla: terrace / rooftop / balcony railing.
    # 13 Eki (3), Bahadır: tekrarsız şablon (prompt 216 kelimeye uzamıştı). "only tilts slightly" + "tilts down no more
    # than slightly" tek ifade; "always visible above the rooftops" + "stays in the upper third" tek ifade; yön için
    # "toward the erupting volcano" kaldı.
    # 18 Eki, Bahadır: 175 kelime için kısaldı (en uzun stil eki 106 -> 97; 97 + 75 + 3 etiket = 175), kurallar aynı.
    # Önceki: "...high vantage looking down over the village street toward the erupting volcano; slight hand shake, the
    # camera stays fixed on the {perch}, tilting down no more than slightly and never descending, ... a corner of the
    # {perch} railing in the foreground; ..."
    perch = VOLCANO_CAMERA_PERCH[spot]
    # 18 Eki (3): ortam ekseni (bombalar, kül bulutu): sokak metni ortamdan; ortam yoksa eski metin
    street = VOLC_ENVS[volc_env]["text"] if volc_env else "the village street"
    if event in VOLCANO_SHORT_CAMERA_EXCLUDED:   # kül bulutu: 13 Eki (3) metni aynen
        return (f"Handheld footage shot by a person standing {CAMERA_SPOTS[spot]}, high vantage looking down over "
                f"{street} toward the erupting volcano; slight hand shake, the camera stays fixed on the {perch}, "
                f"tilting down no more than slightly and never descending, the erupting volcano always visible in the "
                f"upper third of the frame, a corner of the {perch} railing in the foreground; one continuous shot, no "
                f"zoom, no cuts.")
    return (f"Handheld footage shot by a person standing {CAMERA_SPOTS[spot]}, high vantage over {street} "
            f"toward the erupting volcano; slight hand shake, the camera stays fixed on the {perch}, tilting down only "
            f"slightly, never descending, the erupting volcano always visible in the upper third of the frame, a "
            f"{perch} railing corner in the foreground; one continuous shot, no zoom, no cuts.")


# 13 Eki (3), Bahadır kararı: volkan prompt'u en fazla 175 kelime; kısıt silinmeden giyim/ışık satırları kısa yazıldı
# (aynı 4 kısıt). Ortak metin (get_realism_guardrails) diğer kategorilerde aynen kalır. (Lav nehrine özel hız cümlesi
# ve "responders"sız satır 13 Eki 4'te lavla birlikte çıktı; arşiv: event_structure ARŞİV notu.)
# ❄️ Çığ kamerası (13 Eki, Bahadır): volkanla aynı yapı, tek şablon; takip (pan) yok. 14 Eki (2): durulan yerin adı
# (AVALANCHE_CAMERA_PERCH) şablondan çıktı, sözlük kaldırıldı.
# Çığ giyim/ışık (Bahadır'ın metni birebir, 175 kelime kapısı için kısa; 2 kısıt). 14 Eki (4): ışık artık ortam
# satırından geliyor (güneşli gün, kar yağışı...); "overcast daylight" ile çelişmesin diye "raw natural light". Önceki:
# "Bystanders wear winter civilian clothes; raw natural overcast daylight, no hazmat suits."
# 21 Eki (genel kalite): 175 kelime için kısa (aynı 2 kısıt). Önceki: "Bystanders wear winter civilian clothes; raw
# natural light, no hazmat suits."
AVALANCHE_GUARDRAILS = "Civilians in winter clothes, no hazmat suits."   # ışık ortam satırından (Setting)


def avalanche_camera(spot: str) -> str:
    # 14 Eki, Bahadır (ilk test dersi): kamera vadinin karşısından uzaktan bakınca çığ ve evler küçük kaldı, aksiyon
    # beyaz bulutta kayboldu. Yeni şablon birebir: kamera aksiyona yakın, en yakın binalar kadrajın ortasında.
    # "across the valley" ve "avalanche always visible in the upper part of the frame" çıktı; sabit kamera kuralları
    # aynı. Önceki: "...high vantage looking across the valley toward the avalanche on the mountain slope; slight
    # hand shake, the camera stays fixed on the {perch}, tilting down no more than slightly and never descending, the
    # avalanche always visible in the upper part of the frame, a corner of the railing in the foreground; ..."
    # 14 Eki (2), Bahadır: köy testi 3 denemede reddedildi, prompt 175 kelimeyi aşıyordu. Kısa şablon birebir (stil
    # eki ≤ 95 kelime). Önceki: "Handheld footage shot by a person standing {spot}, high vantage looking up the slope
    # as the avalanche rushes down toward the buildings just below and beside the camera; the nearest buildings fill
    # the middle of the frame, slight hand shake, the camera stays fixed on the {perch}, tilting no more than
    # slightly and never descending, a corner of the railing in the foreground; one continuous shot, no zoom, no cuts."
    # 14 Eki (4), Bahadır: çığ ilk ~10 sn yavaş yaklaştı, ilk temas 11. sn'de; yaklaşma ifadesi çıkmıştı.
    # 14 Eki (5), Bahadır: kayak testinde yamaç kadrajda yoktu, çığ görünmedi, model çatıdan kayan kar çizdi. Yamaç ve
    # çığ kadrajın üst yarısında, binalar ve korkuluk alt yarısında (Bahadır'ın metni birebir). Önceki: "...high
    # vantage looking at the avalanche crashing through the buildings just below; slight hand shake, the camera stays
    # fixed, tilting slightly and never descending, a corner of the railing in the foreground; ..."
    return (f"Handheld footage from {CAMERA_SPOTS[spot]}, high vantage looking up a steep snowy slope where the "
            f"avalanche is descending into the buildings just below it; the slope and the avalanche fill the upper half "
            f"of the frame, the nearest buildings and a corner of the railing fill the lower half; slight hand shake, "
            f"the camera stays fixed, tilting slightly and never descending; one continuous shot, no zoom, no cuts.")


# 🏚️ Deprem kamerası (14 Eki, Bahadır; metin birebir): karşı binadan sabit, yüksek açı; çöken binalar ve toz üst üçte
# ikide, sokak ve korkuluk köşesi altta. Yer sarsıntısıyla güçlü el titremesi; kamera sabit, inmez.
# 21 Eki (genel kalite): kısa. Önceki: "Bystanders wear everyday clothes; raw natural light, no hazmat suits."
EARTHQUAKE_GUARDRAILS = "Civilians in everyday clothes, no hazmat suits."   # ışık ortam satırından (Setting)


def earthquake_camera(spot: str) -> str:
    return (f"Handheld footage from {CAMERA_SPOTS[spot]}, high vantage looking across the street at the buildings "
            f"collapsing opposite; the collapsing buildings and the dust fill the upper two thirds of the frame, the "
            f"street and a corner of the railing fill the lower part; strong hand shake from the ground tremor, the "
            f"camera stays fixed and never descends; one continuous shot, no zoom, no cuts.")


# ☄️ Meteor kamerası (29 Eki, Bahadır). Kadraj cümleleri K1-K3 ve tüm kadrajlara eklenen kuyruk birebir; Bahadır kararı
# (29 Eki): kuyruğa sabitlik ifadesi eklendi ("the camera stays fixed, never descending"; K3 kuralı, diğer olaylarla
# aynı). K1-K3 cümlesinin sonundaki nokta ";" oldu (en fazla 8 kısıt).
METEOR_CAMERA = {
    "Rooftop terrace of a hillside villa above the bay":
        "Handheld footage from the rooftop terrace of a modern hillside villa, overlooking the bay and the seafront "
        "houses below",
    "High balcony of a seafront apartment":
        "Handheld footage from a high balcony of a seafront apartment, looking out over the promenade and the open sea",
    "Hilltop terrace above a coastal town":
        "Handheld footage from a hilltop terrace above a coastal town, the whole bay and the rooftops below in view",
}
METEOR_CAMERA_TAIL = ("the impact point is visible offshore from the first second; slight hand shake, the camera stays "
                      "fixed, never descending; no zoom, no cuts.")


def meteor_camera(spot: str) -> str:
    return f"{METEOR_CAMERA[spot]}; {METEOR_CAMERA_TAIL}"


# 🔥 Ateş hortumu kamerası (15 Eki (2), Bahadır): hortum dev ve kareyi dolduruyor. Yüksek bakış, hortuma yakın; gövde
# karenin en az yarısı, tepesi ve bulutu kesilmez; önde 2-3 kişi kaçar. Takip (pan) ve el titremesi aynı. "eye level,
# normal lens" çıktı (yüksek bakışla çelişiyordu). 175 kelime için giyim/ışık kısa (aynı kısıtlar, görevli satırı yok:
# havuzda görevli yok). Kısıt sayısı 8 -> 7. Önceki kamera: "Handheld footage shot by a person standing {spot}, eye
# level, normal lens; slight hand shake, the camera pans to follow the fire tornado; no zoom, no cuts."
# 16 Eki, Bahadır (ortam ekseni): yeni kamera noktaları uzun (en uzunu 21 kelime), 175 kelime kapısı için stil eki
# kısaldı; kurallar aynı (yüksek bakış, hortum karenin en az yarısı, tepesi ve dumanı kesilmez, önde 2-3 kişi kaçar,
# takip, tek çekim). Önceki giyim/ışık: "...raw natural light matching the weather, never glossy or CGI; no white hazmat
# suits." Önceki kamera: "...filling at least half of the frame, its top and smoke cloud never cut off, two or three
# people fleeing it in the near foreground; slight hand shake, the camera pans to follow the fire tornado; ..." (ölçek
# kilit cümlede: "towering" kamera cümlesinden çıktı)
# 18 Eki (2), Bahadır: videolarda hortum dönen huni değil düz yangın sütunu / patlama gibi çıkıyordu. Şekil cümlesi
# eklendi (FIRE_TORNADO_SHAPE); 175 kelime için kamera cümlesi, giyim/ışık satırı ve iki kamera noktası kısaldı (en uzun
# stil eki 97: 97 + 75 + 3 = 175; kısıt sayısı 8). Önceki giyim/ışık: "Bystanders wear civilian clothes, never hi-vis
# PPE; raw natural light, never glossy or CGI; no hazmat suits." Önceki kamera: "...high vantage close to the fire
# tornado filling at least half the frame, its top and smoke never cut off, two or three people fleeing in the near
# foreground; slight hand shake, the camera pans to follow the tornado; one continuous shot, no zoom, no cuts."
# 21 Eki (genel kalite): 175 kelime için kısa (gerçek zaman ve ön plan yüzü cümleleri eklendi; kısıtlar aynı). Önceki:
# "The fire tornado is a visibly rotating funnel of flame with debris orbiting it, never a straight smoke plume or an
# explosion." / "Bystanders wear civilian clothes, never hi-vis PPE; natural light, never glossy or CGI; no hazmat suits."
FIRE_TORNADO_SHAPE = "A rotating funnel of flame with orbiting debris, never a straight plume or explosion."
FIRE_TORNADO_GUARDRAILS = "Civilians in everyday clothes, no hazmat suits, never CGI. " + FIRE_TORNADO_SHAPE


def fire_tornado_camera(spot: str) -> str:
    return (f"Handheld footage shot by a person standing {CAMERA_SPOTS[spot]}, high vantage, the tornado filling half "
            f"the frame, top never cut off, two or three people fleeing close below; slight hand shake, the camera "
            f"pans to follow the tornado; one continuous shot, no zoom, no cuts.")


# 18 Eki: "matching the weather" çıktı (175 kelime; kısıtlar aynı). Kül bulutu eski metinle (VOLCANO_GUARDRAILS_LONG)
# 21 Eki (genel kalite): üniforma cümlesi çıktı, herkes sivil. Önceki: "Bystanders wear civilian clothes, no hi-vis PPE;
# responders wear service uniforms. Raw natural light..."
VOLCANO_GUARDRAILS = "All people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI."
VOLCANO_GUARDRAILS_LONG = VOLCANO_GUARDRAILS   # 21 Eki (genel kalite): kül bulutu da kısa satır (ışık ekseni var)
# 21 Eki (genel kalite), Bahadır: çamur seli testinde insanlar ağır çekimde koştu, alt kenarda bir yüz kadraja girdi,
# çamur gri lapa gibiydi. Tüm yapılandırılmış olayların stil ekine gerçek zaman cümlesi, kamera cümlesine ön plan yüzü
# yasağı; heyelanda çamur rengi. Kamera "shot by a person standing" -> "filmed" (kişi ifadesi ön plana insan çizdiriyor
# olabilir; 175 kelime için de kısa).
# Bahadır'ın metni; ";" yerine virgül: stil eki en fazla 8 kısıt (count_constraints ";" ve "." ile sayar)
REAL_TIME = "Everything moves in real time, never in slow motion, people run at full speed."
NO_FACE = "no person or face close to the camera"
MUD_COLOR = "The mud is dark brown, never grey."
# Yapılandırılmış hat, gemisiz ortam olayları: giyim + ışık tek satır (önceki iki satır 25 kelime; ışık ortam / ışık
# ekseninden). Serbest hat get_realism_guardrails ile iki satırı kullanır (üniformasız giyim satırıyla).
ENV_GUARDRAILS = "All people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI."


# 175 kelime için kamera kısaltmaları (anlam ve kurallar aynı: yükseklik, sabitlik, inmez, tehdit karede, tek çekim).
# Kaynak cümleler ve kadraj eksenindeki birebir eşleştirmeler (NATIVE_FG) değişmez; kısaltma son adımda uygulanır.
CAMERA_SHORTEN = (
    ("shot by a person standing ", "filmed "),
    (" where the avalanche is descending into the buildings just below it;",
     " as the avalanche descends into the buildings below;"),
    ("the slope and the avalanche fill the upper half of the frame", "slope and avalanche fill the upper half"),
    ("high vantage looking up a steep snowy slope", "high vantage up a snowy slope"),
    ("the nearest buildings and a corner of the railing fill the lower half",
     "the nearest buildings and a railing corner below"),
    ("the street and a corner of the railing fill the lower part", "the street and a railing corner below"),
    ("high vantage looking across the street", "high vantage across the street"),
    ("high vantage across the street at the buildings collapsing opposite;", "high vantage across the street;"),
    ("strong hand shake from the ground tremor", "strong hand shake from the tremor"),
    ("a corner of the railing", "a railing corner"),
    ("the camera stays fixed, tilting slightly and never descending", "the camera stays fixed, never descending"),
    ("tilting slightly and never descending", "tilting slightly, never descending"),
    ("tilting down no more than slightly and never descending", "tilting only slightly, never descending"),
    ("tilting down only slightly, never descending", "tilting only slightly, never descending"),
    ("the erupting volcano always visible in the upper third of the frame", "the volcano always in the upper third"),
    ("high vantage looking down over ", "high vantage over "),
    ("high vantage looking down toward ", "high vantage down toward "),
    ("no on-screen text, no timestamp", "no on-screen text or timestamp"),
    (" toward the erupting volcano;", " toward the volcano;"),
    ("the collapsing buildings and the dust fill the upper two thirds of the frame",
     "the collapsing buildings and dust fill the upper two thirds"),
    ("the camera pans to follow the tornado", "the camera follows the tornado"),
    ("two or three people fleeing close below", "two or three people fleeing below"),
)
_THREAT_TWICE = re.compile(r"high vantage (?:looking )?down toward (?P<t>[^;,]+); (?P<rest>[^;]*?)(?P=t) always in frame")
_FIXED_ON = re.compile(r"the camera stays fixed (?:on|at) the [\w-]+(?: [\w-]+)?,")
_RAILING_CORNER = re.compile(r"a corner of the \w+ railing|a (?!railing\b)\w+ railing corner")


def camera_rules(camera: str) -> str:
    """Kamera cümlesine ortak kurallar: kısaltmalar ("shot by a person standing" -> "filmed"...); sonuna ön plan yüzü
    yasağı."""
    for old, new in CAMERA_SHORTEN:
        camera = camera.replace(old, new)
    camera = _RAILING_CORNER.sub("a railing corner", camera).replace("nothing in the foreground", "an empty foreground")
    # mod B: tehdit iki kez anılıyordu ("high vantage down toward X; ... X always in frame") -> bir kez (175 kelime)
    camera = _THREAT_TWICE.sub(r"high vantage; \g<rest>\g<t> always in frame", camera)
    # mod B: yer cümlenin başında söyleniyor ("filmed on a high balcony…"); "stays fixed on the balcony" tekrarı çıktı
    camera = _FIXED_ON.sub("the camera stays fixed,", camera)
    if camera.endswith("no cuts."):
        return camera[:-1] + f", {NO_FACE}."
    return camera.rstrip(".") + f"; {NO_FACE}."


class SlotFillError(RuntimeError):
    """gpt-4o-mini boşlukları iki denemede de geçerli dolduramadı (sessiz yedek yok)."""


# 29 Eki, Bahadır: deniz kategorileri (feribot, tersane, marina & yat) PASİF. Telegram menüsünde görünmez, otomatik
# (LRU) seçime girmez; kod, havuzlar, iskeletler ve testler aynen durur. Açmak için SEA_CATEGORIES_ACTIVE = True (tek
# satır). Kruvaziyer aktif.
SEA_CATEGORIES_ACTIVE = False
SEA_CATEGORIES = ("ferry_operations", "shipyard_and_drydock_engineering", "marina_and_yacht_operations")
DISABLED_DOMAINS = set() if SEA_CATEGORIES_ACTIVE else set(SEA_CATEGORIES)


def domain_active(domain: str) -> bool:
    return domain not in DISABLED_DOMAINS


# 18 Eki (2), Bahadır: DEVRE DIŞI olaylar. Telegram menüsünde görünmez, otomatik (LRU) seçime girmez; havuz, beat'ler,
# iskelet, Notion kayıtları ve testler aynen durur (kombinasyon testleri ve havuz linti bu olayları da denetler). Yeniden
# açmak için olayı bu kümeden çıkarmak yeter (tek satır). Şok dalgası: videolar gri, uzak ve sönük çıkıyordu.
DISABLED_EVENTS = {"Volcano erupts and a shockwave blows out windows"}


def skeleton_events(domain: str) -> list[str]:
    """Domain'in bu hatta kullanılabilen olayları, havuz sırasıyla (Telegram menüsü bu listeyi gösterir). 18 Eki (2):
    DISABLED_EVENTS listede yok (menü ve otomatik seçim). Kodla doğrudan olay vermek (kuru deneme betiği) yine çalışır.
    29 Eki: pasif kategoride (DISABLED_DOMAINS) liste boş."""
    if not domain_active(domain):
        return []
    return [e for e in DOMAIN_ATTRIBUTES[domain]["events"] if e in EVENT_SKELETONS and e not in DISABLED_EVENTS]


def count_range(event: str, ship: str | None) -> tuple[int, int]:
    s = EVENT_SKELETONS[event]
    if event in EVENT_COUNT:
        return EVENT_COUNT[event]
    if s["domain"] in ENV_CENTRIC_DOMAINS:
        return ENV_CENTRIC_COUNT_BY_DOMAIN.get(s["domain"], ENV_CENTRIC_COUNT)
    lo, hi = cast_range(s["domain"], event, ship or "")
    return max(2, lo), min(20, hi)


def fill_skeleton(event: str, ship: str | None, slots: dict) -> str:
    s = EVENT_SKELETONS[event]
    n = _NUM[int(slots["count"])]
    return s["text"].format(ship=SHIP_PHRASES.get(ship or "", ""), spot=s["spots"][slots["spot"]],
                            weather=slots["weather"], n=n, N=n.capitalize(), people=slots["people"])


def legacy_camera(event: str, spot: str, volc_env: str | None = None) -> str:
    """Bugünkü (21 Eki öncesi) kamera cümlesi. Aşama 4'te kadraj ekseninin mod A'sı ve volkan/çığ/deprem yerli cümlesi;
    serbest hat ve frame verilmeyen çağrılar da bunu kullanır."""
    s = EVENT_SKELETONS[event]
    # Final turu: "phone" kelimesi çıktı; model elde tutulan telefonu ve kayıt (REC) ekranını çiziyordu
    camera = (f"Handheld footage shot by a person standing {CAMERA_SPOTS[spot]}, eye level, normal lens; slight hand "
              f"shake, the camera pans to follow the {s['object']}{CAMERA_MOTION_EXTRA.get(event, '')}; no zoom, no cuts.")
    if s["domain"] == "volcano_disasters":   # 13 Eki: volkanda takip yok, kamera sabit (VOLCANO_CAMERA_PERCH)
        camera = volcano_camera(spot, event, volc_env)
    if s["domain"] == "avalanche_disasters":
        camera = avalanche_camera(spot)
    if s["domain"] == "earthquake_disasters":
        camera = earthquake_camera(spot)
    if event == "Fire tornado tears across a burning roadside":
        camera = fire_tornado_camera(spot)
    if s["domain"] == "meteor_disasters":   # 29 Eki: meteor, sabit yüksek kadraj (K1-K3)
        camera = meteor_camera(spot)
    return camera


def style_suffix(event: str, ship: str | None, spot: str, view: str | None = None, setting: str | None = None,
                 volc_env: str | None = None, frame: dict | None = None, fire_env: str | None = None,
                 scene_env: str | None = None) -> str:
    """Tek kamera satırı + kıyafet + ışık (+ şehirde görünüm satırı; en fazla 8 kısıt). Eski ekten kaldırılanlar:
    TUR 30 notu. setting: 14 Eki (4), çığ ortam satırı ("Setting: dağ, yerleşim, ışık."), kamera cümlesinden sonra.
    frame: 21 Eki (Aşama 4) kadraj ekseni (core/frame_axis.py); None ise bugünkü kamera (legacy_camera)."""
    s = EVENT_SKELETONS[event]
    camera = legacy_camera(event, spot, volc_env)
    if frame is not None:
        from core.frame_axis import frame_camera
        camera = frame_camera(event, spot, frame, volc_env, fire_env, legacy=legacy_camera, scene_env=scene_env)
    scene_signs = False
    if scene_env and scene_env != "A":   # 21 Eki (Aşama 5): ortam ekseni (9 olay), çığ ortam satırı gibi kameradan sonra
        from core.scene_env import env_text
        # en fazla 8 kısıt: yazı/tabela yasağı ortam cümlesine katılır (bölge görünümündeki gibi tek kısıt)
        scene_signs = s["domain"] in NO_SIGNS_DOMAINS
        setting = f"Setting: {env_text(event, scene_env)}" + (f", {NO_SIGNS}." if scene_signs else ".")
    guardrails = get_realism_guardrails(s['domain'], ship or 'None', spot)
    if s["domain"] in ENV_CENTRIC_DOMAINS and not ship:   # 21 Eki (genel kalite): birleşik satır
        guardrails = ENV_GUARDRAILS
    if s["domain"] == "volcano_disasters":   # 13 Eki (3): kısa ifade, aynı kısıtlar
        guardrails = VOLCANO_GUARDRAILS_LONG if event in VOLCANO_SHORT_CAMERA_EXCLUDED else VOLCANO_GUARDRAILS
    if s["domain"] == "avalanche_disasters":   # 13 Eki: çığ, volkan yapısı (sabit kamera, kısa giyim/ışık)
        guardrails = AVALANCHE_GUARDRAILS
    if s["domain"] == "earthquake_disasters":   # 14 Eki: deprem, çığ yapısı (sabit kamera, günlük sivil giyim)
        guardrails = EARTHQUAKE_GUARDRAILS
    if event == "Fire tornado tears across a burning roadside":   # 15 Eki (2): dev hortum, ön planda kaçanlar
        guardrails = FIRE_TORNADO_GUARDRAILS
    env_centric = s["domain"] in ENV_CENTRIC_DOMAINS
    if env_centric:   # 21 Eki (genel kalite): kamera ortak kuralları, gerçek zaman, heyelanda çamur rengi
        camera = camera_rules(camera)
        guardrails = f"{guardrails} {REAL_TIME}" + (f" {MUD_COLOR}" if s["domain"] == "landslide_disasters" else "")
    out = f"{camera} {setting} {guardrails}" if setting else f"{camera} {guardrails}"
    if view:
        # 1 Eki: görünüm + nötr giyim + yazı/bayrak yasağı tek cümle (tek kısıt; toplam 7 -> 8). 21 Eki (genel kalite):
        # giyim ifadesi çıktı (giyim satırı "ordinary civilians in everyday clothes" diyor; 175 kelime)
        clothing = "" if env_centric else f", {REGION_VIEW_CLOTHING}"
        out += f" Setting: {view_district(event, view)}{clothing}, {NO_SIGNS}."
    elif s["domain"] in NO_SIGNS_DOMAINS and not scene_signs:
        out += f" {NO_SIGNS[0].upper()}{NO_SIGNS[1:]}."   # 2 Eki: heyelan (toplam 8 kısıt)
    return out


def validate_slots(event: str, ship: str | None, slots: dict) -> list[str]:
    """Boşluk doğrulaması: seçimler listeden, sayı aralıkta. Boş liste = geçerli."""
    s = EVENT_SKELETONS[event]
    errors = []
    if slots.get("spot") not in s["spots"]:
        errors.append(f"spot must be exactly one of {list(s['spots'])}")
    if slots.get("weather") not in s["weather"]:
        errors.append(f"weather must be exactly one of {s['weather']}")
    if slots.get("people") not in s["people"]:
        errors.append(f"people must be exactly one of {s['people']}")
    lo, hi = count_range(event, ship)
    try:
        count = int(slots.get("count"))
    except (TypeError, ValueError):
        count = None
    if count is None or not lo <= count <= hi:
        errors.append(f"count must be an integer from {lo} to {hi}")
    return errors


SLOT_SYSTEM = """You fill the blanks of a fixed documentary video scene. You never write or change the scene itself.
Return ONLY a JSON object: {"spot": ..., "weather": ..., "count": ..., "people": ...}.
- spot, weather and people: copy one option EXACTLY from its list.
- count: an integer inside the given range (how many people are visible).
- Prefer options that are not in the recently used list, and pick a combination that is physically plausible for the event."""


def _slot_message(event: str, ship: str | None, recent: list[str], feedback: list[str] | None) -> str:
    s = EVENT_SKELETONS[event]
    lo, hi = count_range(event, ship)
    msg = (f"EVENT: {event}\nVESSEL: {ship or 'none'}\nSCENE TEMPLATE: {s['text']}\n"
           f"SPOT OPTIONS: {json.dumps(list(s['spots']))}\nWEATHER OPTIONS: {json.dumps(s['weather'])}\n"
           f"PEOPLE OPTIONS: {json.dumps(s['people'])}\nCOUNT RANGE: {lo}-{hi}\n"
           f"RECENTLY USED: {json.dumps(recent[-6:])}")
    if feedback:
        msg += "\nYOUR PREVIOUS ANSWER WAS INVALID: " + "; ".join(feedback)
    return msg


async def fill_slots(event: str, ship: str | None, recent: list[str], call_gpt) -> tuple[dict, list[dict]]:
    """gpt-4o-mini ile boşluk doldurma; geçersizse 1 kez geri bildirimle tekrar. (slots, deneme kaydı)."""
    attempts, feedback = [], None
    for attempt in range(2):
        raw = await call_gpt(SLOT_SYSTEM, _slot_message(event, ship, recent, feedback), temperature=0.9,
                             model="gpt-4o-mini")
        errors = validate_slots(event, ship, raw)
        attempts.append({"attempt": attempt + 1, "raw": raw, "errors": errors})
        if not errors:
            return {**raw, "count": int(raw["count"])}, attempts
        feedback = errors
    raise SlotFillError(f"Boşluklar 2 denemede geçerli doldurulamadı: {attempts}")


def _lru(options: list[str], history: list[str]) -> str:
    """Geçmişte hiç görülmeyen, yoksa en eski görülen seçenek (eşitlikte rastgele)."""
    low = [h.lower() for h in history]

    def last(o):
        return max((i for i, h in enumerate(low) if h == o.lower()), default=-1)
    best = min(last(o) for o in options)
    return random.choice([o for o in options if last(o) == best])


def choose_event_and_ship(domain: str | None, event: str | None, history: list[str]) -> tuple[str, str, str | None]:
    """(domain, olay, gemi). Olay/domain verilmezse Python LRU ile seçer; gemi iskeletin gemilerinden LRU."""
    combos = [h.split("|") for h in history if is_current_universe_combo(h)]
    if event is not None:
        if event not in EVENT_SKELETONS:
            raise ValueError(f"Bu olay iskelet hattında yok: {event}")
        domain = domain or EVENT_SKELETONS[event]["domain"]
        if EVENT_SKELETONS[event]["domain"] != domain:
            raise ValueError(f"Olay bu domain'de yok: {domain} / {event}")
    else:
        if domain is None:
            domain = _lru([d for d in MARITIME_INSPIRATION_DOMAINS if skeleton_events(d)], [c[0] for c in combos])
        if domain not in MARITIME_INSPIRATION_DOMAINS:
            raise ValueError(f"Bilinmeyen domain: {domain}")
        event = _lru(skeleton_events(domain), [c[2] for c in combos if c[0] == domain])
    ships = EVENT_SKELETONS[event]["ships"]
    ship = _lru(ships, [c[1] for c in combos]) if ships else None
    return domain, event, ship


async def build_skeleton_scene(domain: str | None, event: str | None, history: list[str], call_gpt) -> dict:
    """Seçim + boşluk doldurma + hikaye + stil eki. GPT sadece fill_slots'ta (gpt-4o-mini) çağrılır."""
    domain, event, ship = choose_event_and_ship(domain, event, history)
    recent = [" / ".join(h.split("|")[3:4]) for h in history if is_current_universe_combo(h)]
    slots, attempts = await fill_slots(event, ship, recent, call_gpt)
    story = fill_skeleton(event, ship, slots)
    suffix = style_suffix(event, ship, slots["spot"])
    combo_key = f"{domain}|{(ship or 'none').lower()}|{event.lower()}|{slots['spot'].lower()}|{SKELETON_CAMERA}"
    trace = {"pipeline": "skeleton", "domain": domain, "event": event, "ship": ship or "None",
             "camera": SKELETON_CAMERA, "skeleton": EVENT_SKELETONS[event]["text"], "slots": slots,
             "slot_attempts": attempts, "story": story, "story_words": len(story.split())}
    log.info(f"🦴 İskelet: [{domain}] {event} | gemi={ship} | boşluklar={slots}")
    return {"domain": domain, "event": event, "ship": ship, "slots": slots, "story": story, "style_suffix": suffix,
            "prompt": f"{story.rstrip('.')}. {suffix}", "combo_key": combo_key, "trace": trace}


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
