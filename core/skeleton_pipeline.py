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
    "Side stairway off a narrow hillside lane": "at the top of a side stairway beside the narrow hillside lane",
    "Behind the guardrail of a hillside road": "behind the guardrail on the far side of the hillside road",
    "Bridge on a side road below the slope": "on a bridge on a side road, facing the slope and the road",
    "Far edge of the road across from the slope": "on the far edge of the road, across from the slope",
    "Terrace on the opposite hillside": "on a terrace on the opposite hillside, facing the village",
    "High steps on the village square": "on the high steps at the edge of the village square",
    "Upper-floor balcony of a village house": "on the upper-floor balcony of a village house, facing up the slope",
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
    "Tornado approaching coastline": {
        "domain": "coastal_tornado_landfall", "ships": None,
        "spots": {"Beachfront promenade": "the beachfront promenade", "Coastal resort beach": "a resort beach",
                  "High-rise coastal city": "a high-rise waterfront"},
        "people": ["onlookers", "residents", "beachgoers"], "weather": WEATHER_STORM, "object": "tornado",
        "text": "In {weather}, a huge tornado spins across the sea toward {spot}, pulling up a column of spray. Debris "
                "starts lifting along the coast as {n} {people} run inland. The tornado keeps approaching the coastline, "
                "still tearing up water and debris.",
    },
    "Tornado making landfall": {
        "domain": "coastal_tornado_landfall", "ships": None,
        "spots": {"Beachfront promenade": "the beachfront promenade", "Residential coastal district": "a coastal neighborhood",
                  "Downtown city center": "the downtown waterfront"},
        "people": ["onlookers", "residents", "pedestrians"], "weather": WEATHER_STORM, "object": "tornado",
        "text": "In {weather}, a tornado crosses the shoreline and makes landfall at {spot}, ripping roofs and signs "
                "into the air. Sand and debris whirl around its base as {n} {people} sprint for cover. The tornado keeps "
                "moving inland, still hurling debris across the street.",
    },
    "Tornado rain bands and flying debris lash the waterfront": {
        "domain": "coastal_tornado_landfall", "ships": None,
        "spots": {"Beachfront promenade": "the beachfront promenade", "Coastal resort beach": "a resort waterfront",
                  "High-rise coastal city": "a high-rise waterfront"},
        "people": ["onlookers", "residents", "pedestrians"], "weather": WEATHER_STORM, "object": "flying debris",
        "text": "At {spot} in {weather}, the outer rain bands of a tornado lash the waterfront, driving sheets of rain "
                "sideways. Flying debris tumbles along the ground and smashes into railings as {n} {people} run for "
                "shelter. The rain bands keep sweeping in, still hurling debris across the waterfront.",
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
    "gulf_metropolis": "glass towers behind palm-lined multi-lane boulevards, sand-colored low buildings, white SUVs",
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: Kuzey Afrika kıyısı (Fas, Tunus)
    "north_african_coast": "sand-colored flat-roofed buildings, narrow streets, cloth awnings, small hatchback cars",
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: ABD kıyı kasabası (Florida, Carolina)
    "us_coastal_town": "wide asphalt roads, pickup trucks, low wooden and brick houses, overhead power lines",
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: Kuzey Avrupa sahil kasabası (Hollanda, İngiltere)
    "north_european_seaside": "brick terraced houses, narrow streets, small parked cars",
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: Riviera (Fransa, İtalya)
    # 4 Eki, Bahadır: "cobbled promenade" GPT'ye caddeyi "promenade" diye yazdırıyordu (sel kuru provası, olay adı
    # kuralından ret); "cobbled streets" oldu. Kıyı dev dalga da bu görünümü kullanır.
    "riviera": "cream stone buildings with shuttered windows, cobbled streets, scooters, plane trees",
    # 1 Eki, Bahadır: aynı ortamda tekrar eden videolar. İlham: Doğu Asya kıyısı (Japonya, Tayvan)
    # 1 Eki (2): videoda Akdeniz çıktı; "covered arcade entrances" Akdeniz çağrışımı yaptı, klima ve kablo eklendi
    "east_asian_coast": "dense mid-rise apartment blocks with air-conditioner units and tangled overhead wires, "
                        "narrow lanes, small boxy cars and scooters",
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
    "Hortum": ["Tornado approaching coastline", "Tornado making landfall",
               "Tornado rain bands and flying debris lash the waterfront", "Tornado approaching an open beach"],
    "Tsunami": [],
    "Sel": ["Flash flooding in city streets"],
    "Heyelan": ["Mudslide pours down a hillside street", "Rain-soaked slope collapses onto a roadside", "Mud and debris torrent tears through a hillside village"],
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
# "No readable signs, text or flags" ayrı cümle olarak stil ekine girer (şehirde görünüm cümlesinin içinde)
NO_SIGNS_DOMAINS = {"landslide_disasters"}

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
}


class SlotFillError(RuntimeError):
    """gpt-4o-mini boşlukları iki denemede de geçerli dolduramadı (sessiz yedek yok)."""


def skeleton_events(domain: str) -> list[str]:
    """Domain'in bu hatta kullanılabilen olayları, havuz sırasıyla (Telegram menüsü bu listeyi gösterir)."""
    return [e for e in DOMAIN_ATTRIBUTES[domain]["events"] if e in EVENT_SKELETONS]


def count_range(event: str, ship: str | None) -> tuple[int, int]:
    s = EVENT_SKELETONS[event]
    if s["domain"] in ENV_CENTRIC_DOMAINS:
        return ENV_CENTRIC_COUNT_BY_DOMAIN.get(s["domain"], ENV_CENTRIC_COUNT)
    lo, hi = cast_range(s["domain"], event, ship or "")
    return max(2, lo), min(20, hi)


def fill_skeleton(event: str, ship: str | None, slots: dict) -> str:
    s = EVENT_SKELETONS[event]
    n = _NUM[int(slots["count"])]
    return s["text"].format(ship=SHIP_PHRASES.get(ship or "", ""), spot=s["spots"][slots["spot"]],
                            weather=slots["weather"], n=n, N=n.capitalize(), people=slots["people"])


def style_suffix(event: str, ship: str | None, spot: str, view: str | None = None) -> str:
    """Tek kamera satırı + kıyafet + ışık (+ şehirde görünüm satırı; en fazla 8 kısıt). Eski ekten kaldırılanlar:
    TUR 30 notu."""
    s = EVENT_SKELETONS[event]
    # Final turu: "phone" kelimesi çıktı; model elde tutulan telefonu ve kayıt (REC) ekranını çiziyordu
    camera = (f"Handheld footage shot by a person standing {CAMERA_SPOTS[spot]}, eye level, normal lens; slight hand "
              f"shake, the camera pans to follow the {s['object']}{CAMERA_MOTION_EXTRA.get(event, '')}; no zoom, no cuts.")
    out = f"{camera} {get_realism_guardrails(s['domain'], ship or 'None', spot)}"
    if view:
        # 1 Eki: görünüm + nötr giyim + yazı/bayrak yasağı tek cümle (tek kısıt; toplam 7 -> 8)
        out += f" Setting: {view_district(event, view)}, {REGION_VIEW_CLOTHING}, {NO_SIGNS}."
    elif s["domain"] in NO_SIGNS_DOMAINS:
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
