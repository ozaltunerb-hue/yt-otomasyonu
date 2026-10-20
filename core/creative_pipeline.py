"""
Creative hattı (TUR 31): GPT-4o hikâyeyi kendisi yazar, iskelet yok.

İskelet hattı aynı olayda neredeyse birebir aynı prompt'u üretiyordu (kruvaziyer dev dalga iki kez seçildi,
iki prompt aynıydı). Bu hatta Python olay/gemi (LRU), yer ve havayı (iskelet listelerinden rastgele) seçer;
GPT-4o kısa bir sistem prompt'uyla 40-60 kelimelik hikâyeyi yazar. Kurallar sadece: 40-60 kelime, 3 beat
(tetik, hareket, hâlâ süren sonuç), görünür tetik, son cümle hareketle biter. Sert kontrol iki tane: olay
uyuşması ve kelime sayısı; kalırsa 1 kez geri bildirimle yeniden istenir. Tekrar önleme: son 15 hikâye
"bunlardan farklı yaz" diye verilir. Kamera satırı ve stil eki iskelet hattıyla birebir aynıdır.
"""
from __future__ import annotations

import functools
import json
import logging
import os
import random
import re
import sys
from datetime import datetime, timezone

import asyncio

import core.event_structure as es
from core.prompt_generator import NoValidScenarioError
from core.skeleton_pipeline import (
    EVENT_SKELETONS,
    REGION_VIEW_EVENTS,
    REGION_VIEWS,
    SKELETON_CAMERA,
    SHIP_PHRASES,
    choose_event_and_ship,
    choose_region_view,
    count_range,
    remember_view,
    style_suffix,
    view_place,
    view_spots,
)

log = logging.getLogger("CreativeEngine")

MIN_WORDS, MAX_WORDS = 40, 60
RECENT_STORIES = 15

CREATIVE_SYSTEM = """You write one short scene for a 15-second realistic video of a real incident.
Input: event, vessel, place, weather, visible people, outcome to reach.

Rules:
1. 40 to 60 words.
2. Three beats: the trigger happens; the movement it causes; the result, still unfolding, reaching the given outcome. The first sentence shows the moment the trigger happens (the wave clears the rail, the cable snaps, the wall of water enters the street); never open with waiting, tension or buildup; describe the scene, never the camera or the video. Show only what is visible, never sounds.
3. The trigger is clearly visible on camera.
4. The last sentence shows the danger still visibly moving at the very end.
5. Catastrophic in scale: violent, high-volume water or force dominating the frame; never mild or harmless images (ankle-deep, floats, honking futilely).
Name any given vessel by its type. Make it different from the recent stories.
Return JSON only: {"story": "..."}"""

# 3. beat'in ulaşacağı sonuç (TUR 31, veri; kural değil): GPT hikâyeyi kendisi yazar, son beat bu sonuca varır.
EVENT_OUTCOMES = {
    # Feribot
    "Lashing chain snaps and a parked car breaks loose":
        "the loose car slams into the next row and keeps sliding across the deck with every roll",
    "Loading ramp hinge snaps and the ramp drops":
        "the steel ramp crashes onto the quay and keeps twisting as the ferry surges against its lines",
    "Green wave breaks over the rail onto the vehicle deck":
        "seawater pours across the vehicle deck and shoves parked cars sideways into each other",
    # Tersane
    # Yat kızakta ileri gitmez: olduğu yerde yana yatar, sonra yan tarafıyla suya devrilir (altın video).
    # İleri kayma yazılınca model yatı suya kafadan sokuyordu.
    "Restraining cable snaps during slipway launch":
        "the yacht heels over onto its side in place, then topples sideways into the water beside it with a "
        "huge splash and keeps rolling hard from side to side",
    "Keel blocks collapse under the launching hull":
        "the yacht heels over onto its side in place, then topples sideways into the water beside it with a "
        "huge splash and keeps rolling hard from side to side",
    "Drydock flood gate bursts open":
        "a wall of seawater lifts the hull off its blocks and swings it against the dock wall",
    "Timber shores snap and the hull tips on its keel blocks":
        "the hull topples sideways off its keel blocks, snapping the remaining shores",
    "Crane sling snaps while lowering the hull into the water":
        "the hull plunges nose-first into the basin, throwing up a wall of spray while still swinging on the last sling",
    # Marina
    # ÇIKARILDI (1 Eki, Bahadır): marina_yat_3 ve halat_kopar videolarında halat kopması görünmedi (bkz. skeleton_pipeline)
    # "Mooring line snaps in a storm gust":
    #     "the mooring line snaps and whips across the dock, the yacht swings free and slams its hull into the "
    #     "neighboring moored yacht again and again",
    "Storm surge wave lifts and buckles the floating pontoon":
        "the pontoon buckles and tilts, throwing the moored boat against it as more waves roll in",
    "Passing boat's wake slams the boat sideways":
        "the boat heels hard and keeps slamming against the dock as the wake rolls through",
    # ÇIKARILDI (1 Eki, Bahadır): kontrolsüz yat videosunda çarpma yok (bkz. skeleton_pipeline)
    # # EKLENDİ (1 Eki, Bahadır; TASLAK)
    # "Yacht loses control and rams moored boats in the marina":
    #     "the yacht races into the marina out of control, plows into the moored boats along the dock and shoves them "
    #     "aside while people jump back",
    # Kruvaziyer
    "Mooring line snaps and whips across the quay":
        "the snapped line keeps thrashing across the quay while the towering hull swings away from the berth",
    "Gangway tears loose as the hull surges":
        "the gangway tears free at one end and swings against the hull as the ship keeps surging",
    "Rogue wave breaks over the rail onto the pool deck":
        "waves keep sweeping loungers and people across the pool deck",
    # Kıyı hortumu
    # ÇIKARILDI (4 Eki, Bahadır; TASLAK): menüden çıktı (bkz. skeleton_pipeline)
    # "Tornado approaching coastline":
    #     "the tornado reaches the shore, ripping sand, water and debris high into the air",
    "Tornado making landfall":
        "the tornado tears roofs and signs away and hurls debris across the street",
    # ÇIKARILDI (4 Eki, Bahadır; TASLAK): menüden çıktı (bkz. skeleton_pipeline)
    # "Tornado rain bands and flying debris lash the waterfront":
    #     "sheets of rain and flying debris batter the waterfront, smashing railings and signs",
    # EKLENDİ (4 Eki, Bahadır; TASLAK)
    # 4 Eki, Bahadır: marina yeniden tasarımı (eski: "...snapping masts and hurling boat covers and debris toward
    # the road")
    "Tornado crosses a marina quay":
        "the tornado tears across the marina quay, ripping awnings, signs and quay furniture loose and hurling debris "
        "toward the road",
    "Tornado sweeps down a coastal avenue":
        "the tornado sweeps down the coastal avenue, uprooting palm trees and hurling signs and debris along the road",
    # Şehir
    "Flash flooding in city streets":
        "a wall of brown floodwater surges down the street, slams into parked cars and shoves them sideways "
        "as people run for higher ground",
    # ÇIKARILDI (30 Eyl, Bahadır): aksiyonsuz videolar veriyordu (bkz. skeleton_pipeline)
    # "Storm gust tears signs and scaffolding loose downtown":
    #     "scaffolding and signs crash onto the street and parked cars as more panels tear loose",
    # EKLENDİ (30 Eyl, Bahadır onayı). Kaynak: 24 Eyl videosu (dosya 1790240764259-vf8owrlvyva)
    # 1 Eki (Bahadır): 6 görünümün videosunda en iyileri kahverengi, çalkantılı, molozlu suydu; temiz kıvrılan dalga
    # yapay göründü.
    "Tidal wave surges over a coastal city street":
        "a towering brown churning tidal wave thick with debris crashes over the coastal road, sweeps parked cars into "
        "storefronts and keeps surging down the street",
    # Heyelan (TASLAK)
# 2 Eki, Bahadır: Seedance hızlı akan su gücünü iyi çiziyor, yavaş kayan toprağı 15 sn'de göstermiyor; heyelan,
# aşırı yağıştan yamaçtan hızla inen çamur ve su akıntısı olarak tanımlanır (kayma/yükselme/yavaş çökme yok).
    "Mudslide pours down a hillside street":
        "a wall of brown mud and water pours down the steep street, slams into parked cars and shoves them sideways "
        "as people run uphill from the flow",
    "Rain-soaked slope collapses onto a roadside":
        "the saturated slope gives way and a fast torrent of mud and rocks surges across the road, pushing cars into "
        "the guardrail while drivers scramble out",
    "Mud and debris torrent tears through a hillside village":
        "a fast torrent of mud, logs and rocks tears down between the houses, ramming walls and sweeping away fences "
        "and parked vehicles as villagers run to higher ground",
    # Yangın (TASLAK, 8 Eki, Bahadır): yapılandırılmış hatta; trace/rapor için, GPT mesajına girmez
    "Wall of flames sweeps into a hillside neighborhood":
        "the wall of flames slams into the neighborhood, igniting roofs, trees and fences one after another as "
        "residents run from the fire",
    "Flames race up a tower facade":
        "the flames keep climbing the tower facade, blowing out windows and dropping burning debris onto the street "
        "below",
    "Fire tornado tears across a burning roadside":
        "the fire tornado keeps tearing along the roadside, hurling burning branches, embers and debris across the "
        "road",
    # 10 Eki, Bahadır
    "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood":
        "the helicopter keeps dropping water on the wall of flames, turning sections into white steam as the fire "
        "fights back toward the houses",
    # Volkan (TASLAK, 10 Eki, Bahadır): yapılandırılmış hatta; trace/rapor için
    "Volcano erupts and a shockwave blows out windows":
        "the shockwave and falling rocks keep smashing windows, signs and roofs along the street below the volcano",
    # 13 Eki: lav araçsız, kül bulutu büyük yapılar (yukarıdan görünen)
    "Pyroclastic cloud races down into a village street":
        "the cloud keeps tearing through the street, ripping balconies and roof tiles off the houses and snapping trees "
        "and power poles",
    "Volcanic bombs slam into a village street":
        "glowing rocks keep slamming into the street, punching through roofs and setting cars on fire",
    # Çığ (TASLAK, 13 Eki, Bahadır): yapılandırılmış hatta; trace/rapor için
    "Avalanche slams into a mountain village": "the snow wall keeps tearing through the village, flattening chalets, fences and trees",
    "Avalanche crashes down onto a ski lodge": "the avalanche keeps crashing into the ski resort, snapping lift towers and burying the lodge",
    "Avalanche rips through a pine forest into a valley": "the avalanche keeps tearing through the forest into the valley, hurling trunks into the houses",
    # Deprem (TASLAK, 14 Eki, Bahadır): yapılandırılmış hatta; trace/rapor için
    "Earthquake collapses an apartment block": "the ground keeps shaking and the apartment blocks keep collapsing floor by floor into the dust",
    "Earthquake collapses a row of old stone houses": "the collapse keeps running down the street, old stone houses caving in one after another",
    # Plaj
    "Tornado approaching an open beach":
        "the tornado reaches the sand, hurling umbrellas, chairs and sand high into the air",
    "Storm gust rips umbrellas and beach chairs into the air":
        "dozens of umbrellas and chairs cartwheel across the sand and into the air",
    "Large waves reaching the beach":
        "huge waves surge far up the beach, sweeping chairs and towels inland toward the promenade",
}
if set(EVENT_OUTCOMES) != set(EVENT_SKELETONS):
    raise RuntimeError(f"EVENT_OUTCOMES iskelet olaylarıyla uyuşmuyor: {set(EVENT_OUTCOMES) ^ set(EVENT_SKELETONS)}")


# ── HİKÂYE KURAL KAPISI (30 Eyl) ────────────────────────────────────────────────────────────────────────────
# Sistem prompt'una dokunulmaz; bu kurallar sadece kodda denetlenir, kalan hikâye GPT'ye kısa geri bildirimle
# yeniden yazdırılır. 3 denemede de geçmezse Kie'ye gidilmez. KİLİTLİ: aşağıdaki listeleri gevşetmek ya da
# kaldırmak için Bahadır'ın açık onayı gerekir; tests/test_story_rule_gate.py tam içeriği denetler.
# Bütçe: sabit kural en fazla 6, olay başına anahtar grup en fazla 3, yasak liste sadece iki kızak olayında.

MAX_ATTEMPTS = 3
SLIPWAY_EVENTS = ("Restraining cable snaps during slipway launch", "Keel blocks collapse under the launching hull")

# Sabit kurallar (22 olayın hepsinde). kural → Telegram'da görünen unsur adı.
STORY_RULES = {
    # Sebep: açılış bekleyiş/gerilimle başlayınca tetik 15 sn'ye sığmıyor. Kaynak: final turu hazırlığı
    # (30 Eyl, eb3a9f2), sistem prompt'u 2. kuralın kodda denetimi.
    "a_trigger_first": "ilk cümlede tetik",
    # Sebep: model elde tutulan telefonu ve kayıt (REC) ekranını çizdi. Kaynak: final turu öncesi Kie
    # videoları (30 Eyl, eb3a9f2 notu).
    "b_no_camera_words": "kamera/video/telefon kelimesi olmaması",
    # Sebep: "as the video ends", "tension builds" gibi cümlelerin görüntüde karşılığı yok, boş saniye üretir.
    # Kaynak: final turu hazırlığı (30 Eyl, eb3a9f2), sistem prompt'u 2. kuralın kodda denetimi.
    "c_no_meta_or_waiting": "meta/bekleyiş ifadesi olmaması",
    # Sebep: "ankle-deep floods", "honking futilely", "debris floats" olayı zararsız gösterdi. Kaynak: TUR 31
    # creative kanıt koşusu, şehir sel hikâyesi (30 Eyl, GPT çıktısı; video değil).
    "d_no_scale_reducers": "ölçek küçültücü ifade olmaması",
    # Sebep: menü olayı hikâyede yoksa Kie başka bir olay çizer; gemi adı yoksa başka tekne çizer. Kaynak: TUR 29
    # zorunlu olay denetimi ve TUR 8 gemi adı kapısı.
    "e_event_and_ship_named": "olay adı ve gemi türü",
    # Sebep: stil ekindeki "phone" elde tutulan telefonu çizdirdi. Kaynak: final turu öncesi Kie videoları
    # (30 Eyl, eb3a9f2; zaten testli, korunur).
    "f_no_phone_in_style": "stil ekinde 'phone' olmaması",
}

# b: kamera/kayıt kelimeleri (hikâyede; stil eki ayrı kuraldır)
CAMERA_WORDS = ("camera", "video", "phone", "footage")
# c: meta anlatım ve bekleyiş
META_PHRASES = ("as the video ends", "as the clip ends", "the scene ends", "tension builds", "tension mounts",
                "suspense", "anticipation", "about to", "moments before", "calm before", "holds its breath",
                "waiting", "waits")
# d: ölçek küçültücüler (sistem prompt'u 5. kuraldaki örneklerle uyumlu)
SCALE_REDUCERS = ("ankle-deep", "ripple", "harmless", "harmlessly", "gentle", "gently", "mild", "mildly",
                  "trickle", "puddle", "drizzle", "floats", "futilely",
                  # 3 Eki, Bahadır: sel kuru provasında "horn blaring in futility" kaçtı ("futilely" eşleşmiyor)
                  "futility",
                  # 4 Eki, Bahadır: sel kuru provasında "Cars bob like toys" (süzülme ima eder); bobs/bobbed/bobbing
                  "bob")
# e: gemi türü (VESSEL satırındaki ad). Hikâyede bu kelimelerden biri geçmeli.
SHIP_TYPE_WORDS = {
    "Passenger Car Ferry": ("ferry",),
    "High-speed Catamaran": ("catamaran",),
    "Luxury Motor Yacht": ("yacht",),
    "Sailing Yacht": ("yacht",),
    "Runaway Powerboat": ("powerboat", "power boat"),
    "Ocean Cruise Liner": ("cruise liner", "cruise ship", "liner"),
    "Mega Cruise Ship": ("cruise ship", "cruise liner"),
}
# a: olay adındaki yer/bağlam kökleri tetik sayılmaz ("pool deck", "city streets" tetik değil)
_SETTING_STEMS = {"park", "deck", "rail", "vehi", "gree", "laun", "hull", "open", "wate", "lowe", "stor", "pass",
                  "side", "boat", "acro", "quay", "coas", "appr", "city", "stre", "down", "beac", "larg", "floa",
                  "dryd", "load", "pool", "slip"}

# Olay başına 1-3 anahtar grup: her gruptan en az bir kelime/kök hikâyede geçmeli. Kelimeler çekimleriyle
# eşleşir (surge → surges, surging; car → cars). Onaylı: iki kızak, şehir sel, kruvaziyer dev dalga.
# TASLAK: diğer 18 olay EVENT_OUTCOMES'tan türetildi, Bahadır kontrol edecek; henüz testle kilitli değil.
EVENT_REQUIRED = {
    # ── Feribot (TASLAK) ──
    "Lashing chain snaps and a parked car breaks loose": [("car", "vehicle"), ("slide", "slid", "skid", "slam")],
    "Loading ramp hinge snaps and the ramp drops": [("ramp",), ("crash", "slam", "drop", "fall", "fell")],
    "Green wave breaks over the rail onto the vehicle deck": [("wave", "seawater", "water"), ("car", "vehicle")],
    # ── Tersane ──
    # ONAYLI. Sebep: yat kızaktan kayıp suya kafadan girdi (30 Eyl tersane videosu); istenen görüntü 12 Eyl
    # altın videosu: yerinde yana yatış, yan tarafıyla suya düşüş.
    # "to one side": Bahadır onayı, 30 Eyl; "tilting to one side" yazan doğru omurga hikâyesi reddediliyordu
    # (hedefli kuru prova). İleri kaymayı yasak liste engelliyor.
    "Restraining cable snaps during slipway launch": [("sideways", "on its side", "onto its side", "to one side")],
    "Keel blocks collapse under the launching hull": [("sideways", "on its side", "onto its side", "to one side")],
    # TASLAK
    "Drydock flood gate bursts open": [("seawater", "water", "torrent"), ("lift", "float", "swing")],
    "Timber shores snap and the hull tips on its keel blocks": [("topple", "tip", "sideways", "on its side",
                                                                 "onto its side")],
    "Crane sling snaps while lowering the hull into the water": [("plunge", "drop", "fall", "fell", "crash"),
                                                                 ("spray", "splash")],
    # ── Marina (TASLAK) ──
    # ÇIKARILDI (1 Eki, Bahadır): marina_yat_3 ve halat_kopar videolarında halat kopması görünmedi
    # "Mooring line snaps in a storm gust": [("snap", "parts", "parted", "break", "broke"),
    #                                        ("neighboring yacht", "neighboring moored yacht", "neighbouring yacht",
    #                                         "next yacht", "adjacent yacht", "neighboring boat"),
    #                                        ("slam", "crash", "ram", "smash", "bang")],
    "Storm surge wave lifts and buckles the floating pontoon": [("pontoon",), ("buckle", "tilt", "twist", "heave")],
    "Passing boat's wake slams the boat sideways": [("wake",), ("heel", "slam", "rock", "roll")],
    # ÇIKARILDI (1 Eki, Bahadır): kontrolsüz yat videosunda çarpma yok
    # # TASLAK (1 Eki). Sebep: yat bağlı teknelere çarpmalı; çarpma fiili ve somut hedef (bağlı tekne) görünmezse
    # # model yatı düzgün seyreder çizer (halat olayının 1 Eki videolarındaki hata).
    # "Yacht loses control and rams moored boats in the marina": [("plow", "ram", "slam", "crash", "smash"),
    #                                                             ("moored boat", "moored yacht", "moored boats",
    #                                                              "docked boat", "docked yachts")],
    # ── Kruvaziyer ──
    # TASLAK
    "Mooring line snaps and whips across the quay": [("line", "rope", "hawser", "cable"), ("whip", "thrash", "lash")],
    "Gangway tears loose as the hull surges": [("gangway",), ("tear", "tore", "swing", "rip", "break", "collapse")],
    # ONAYLI. Sebep: dalga güverteye inip şezlong ve insanları sürüklemeli. Kaynak: TUR 24 kruvaziyer Kie
    # videosu (kabul edildi) ve Bahadır'ın tanımı.
    "Rogue wave breaks over the rail onto the pool deck": [("wave",), ("loungers", "chairs", "people", "passengers")],
    # ── Kıyı hortumu (TASLAK) ──
    # ÇIKARILDI (4 Eki, Bahadır; TASLAK): menüden çıktı (bkz. skeleton_pipeline)
    # "Tornado approaching coastline": [("tornado", "twister", "funnel"), ("shore", "coast", "beach", "waterfront"),
    #                                   ("debris", "sand", "spray")],
    # TASLAK (4 Eki, Bahadır hazırlığı, onay bekliyor): yapılandırılmış hatta; tetik kilit cümlede olay adından.
    # Eski: [("tornado", "twister", "funnel"), ("roof", "sign", "debris")]
    "Tornado making landfall": [],
    # ÇIKARILDI (4 Eki, Bahadır; TASLAK): menüden çıktı (bkz. skeleton_pipeline)
    # "Tornado rain bands and flying debris lash the waterfront": [("tornado", "twister", "funnel"), ("rain",),
    #                                                              ("debris",)],
    # EKLENDİ (4 Eki, Bahadır; TASLAK): yapılandırılmış hatta, grupsuz
    "Tornado crosses a marina quay": [],
    "Tornado sweeps down a coastal avenue": [],
    # ── Şehir ──
    # ONAYLI. Sebep: su yerinde yükselmez, sokaktan gelen bir duvar olur ve arabaları sürükler. Kaynak: final turu
    # "hareketli sel" (30 Eyl, eb3a9f2) ve Bahadır'ın tanımı.
    # 4 Eki, Bahadır onayı: yapılandırılmış hatta (core/event_structure.py) kilit görsel kodda, olay terimleri
    # seçilen 4-9s / 9-15s olayından gelir; bu gruplar kalktı. Eski: [("wall", "surge", "torrent", "wave", "rush"),
    # ("car", "cars", "vehicle")]
    "Flash flooding in city streets": [],
    # ÇIKARILDI (30 Eyl, Bahadır): aksiyonsuz videolar veriyordu
    # "Storm gust tears signs and scaffolding loose downtown": [("sign", "scaffold"),
    #                                                          ("crash", "fall", "fell", "topple", "tear", "rip")],
    # ONAYLI. Sebep: dalga kıyı yoluna çarpıp arabaları sürüklemeli. Kaynak: Bahadır'ın beğendiği 24 Eyl videosu
    # (dosya 1790240764259-vf8owrlvyva) ve Bahadır'ın tanımı (30 Eyl).
    # 4 Eki, Bahadır onayı: yapılandırılmış hatta (sel gibi); tetik kilit cümlede olay adından (tidal, wave).
    # Eski: [("wave", "surge", "torrent"), ("car", "cars", "vehicle")]
    "Tidal wave surges over a coastal city street": [],
    # ── Heyelan (ONAYLI, 2 Eki, Bahadır: 3 olay test edildi) ──
    # Sebep: çamur akıntısı ve çarptığı somut nesne (araç/ev) görünmezse model yavaş kayan toprak ya da boş yamaç
    # çiziyor; Seedance hızlı akan su gücünü iyi çiziyor.
    # TASLAK (4 Eki, Bahadır hazırlığı, onay bekliyor): yapılandırılmış hatta; tetik kilit cümlede olay adından.
    # Eski: [("mud",), ("car", "cars", "vehicle", "vehicles")]
    "Mudslide pours down a hillside street": [],
    # Eski: [("mud", "slope", "hillside"), ("car", "cars", "vehicle", "vehicles", "road")]
    "Rain-soaked slope collapses onto a roadside": [],
    # Eski: [("mud",), ("house", "houses", "wall", "walls", "village")]
    "Mud and debris torrent tears through a hillside village": [],
    # ── Yangın (TASLAK, 8 Eki, Bahadır): yapılandırılmış hatta, grupsuz; tetik kilit cümlede olay adından ──
    "Wall of flames sweeps into a hillside neighborhood": [],
    "Flames race up a tower facade": [],
    "Fire tornado tears across a burning roadside": [],
    "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood": [],   # 10 Eki
    # ── Volkan (TASLAK, 10 Eki): yapılandırılmış hatta, grupsuz ──
    "Volcano erupts and a shockwave blows out windows": [],
    "Pyroclastic cloud races down into a village street": [],
    "Volcanic bombs slam into a village street": [],
    "Avalanche slams into a mountain village": [], "Avalanche crashes down onto a ski lodge": [], "Avalanche rips through a pine forest into a valley": [],   # 13 Eki: çığ (yapılandırılmış hat kapıları)
    "Earthquake collapses an apartment block": [], "Earthquake collapses a row of old stone houses": [],   # 14 Eki: deprem (yapılandırılmış hat kapıları)
    # ── Plaj (TASLAK) ──
    "Tornado approaching an open beach": [("tornado", "twister", "funnel"), ("umbrella", "chair", "sand")],
    "Storm gust rips umbrellas and beach chairs into the air": [("umbrella", "chair"),
                                                                ("air", "cartwheel", "tumble", "fly", "flies")],
    "Large waves reaching the beach": [("wave", "surf", "breaker"), ("chair", "towel", "umbrella", "people")],
}
REQUIRED_APPROVED = SLIPWAY_EVENTS + ("Flash flooding in city streets", "Rogue wave breaks over the rail onto the pool deck",
                                      "Tidal wave surges over a coastal city street",
                                      # ONAYLI (2 Eki, Bahadır): 3 heyelan olayı test edildi
                                      "Mudslide pours down a hillside street", "Rain-soaked slope collapses onto a roadside",
                                      "Mud and debris torrent tears through a hillside village")

# Sadece iki kızak olayı. Sebep: GPT 2. beat'te yatı kızaktan ileri kaydırdı (30 Eyl kızak halatı hikâyeleri),
# model de yatı suya kafadan soktu (30 Eyl tersane videosu).
EVENT_FORBIDDEN = {
    e: ("slides down", "sliding", "slides", "lurch", "lurches", "surges forward", "hurtle", "hurtles",
        "races down", "plunges", "plunging", "dives", "nose", "bow-first",
        # Bahadır onayı, 30 Eyl: kuru provada geçen hikâyelerde "careening down the slipway", "plummeting into
        # the water" vardı. "dive/diving" bilerek yok (işçiler "diving to safety" yazılabilir).
        "careen", "careens", "careening", "plummet", "plummets", "plummeting", "slide", "slid",
        # Bahadır onayı, 30 Eyl; kızak halatı hikâyesi 'begins its descent down the slipway... accelerates
        # uncontrollably' ile kapıdan geçti. Çekimleriyle eşleşir (descends, descending, accelerates...).
        "down the slipway", "descent", "descend", "accelerate")
    for e in SLIPWAY_EVENTS
}
FORBIDDEN_FEEDBACK_TR = "yat ileri gitmez; olduğu yerde yana yatar, sonra yan tarafıyla suya düşer."
FORBIDDEN_FEEDBACK_EN = ("The yacht does not move forward: it heels over onto its side where it stands, then falls "
                         "into the water on its side.")

# ÇEŞİTLİLİK KAPISI (6 sabit kurala sayılmaz, ayrı kategori). Sebep: hedefli kuru provada "Hortum kıyıya
# yaklaşıyor" iki kez birebir aynı hikâyeyi verdi (Jaccard 1.0), tekrar önleme listesine rağmen. Bahadır onayı,
# 30 Eyl. KİLİTLİ: eşik onaysız gevşetilmez. Deneme sayılır (3 deneme sınırı aynı).
DIVERSITY_THRESHOLD = 0.6
DIVERSITY_FEEDBACK_TR = "Bu hikâye son hikâyelere çok benziyor: farklı sahne, farklı ilk cümle yaz."
DIVERSITY_FEEDBACK_EN = "This story is too similar to the recent stories: write a different scene and a different first sentence."


def jaccard(a: str, b: str) -> float:
    """Kelime kümesi Jaccard benzerliği (eski örtüşme ölçümü), 1 = aynı."""
    A, B = set(re.findall(r"[a-z]+", (a or "").lower())), set(re.findall(r"[a-z]+", (b or "").lower()))
    return len(A & B) / len(A | B) if A | B else 0.0


def diversity_issues(story: str, recent: list[str]) -> list[dict]:
    """Son hikâyelerden biriyle Jaccard >= eşik ise tek sorun döner. Boş liste = yeterince farklı."""
    top = max((jaccard(story, r) for r in recent), default=0.0)
    if top >= DIVERSITY_THRESHOLD:
        return [{"rule": "diversity", "missing": f"çeşitlilik (benzerlik {top:.2f}): {DIVERSITY_FEEDBACK_TR}",
                 "feedback": DIVERSITY_FEEDBACK_EN}]
    return []

for _e in set(EVENT_REQUIRED) ^ set(EVENT_OUTCOMES):
    raise RuntimeError(f"EVENT_REQUIRED olaylarla uyuşmuyor: {_e}")


def _term_re(term: str) -> str:
    """Kelime/kök deseni: son kelime çekimleriyle (s, es, d, ed, ing, ies, ikizleşen ünsüz, e düşmesi)."""
    head, _, last = term.lower().rpartition(" ")
    forms = {last, last + "s", last + "es", last + "d", last + "ed", last + "ing"}
    if last.endswith("e"):
        forms.add(last[:-1] + "ing")
    if last.endswith("y"):
        forms |= {last[:-1] + "ies", last[:-1] + "ied"}
    if re.fullmatch(r".*[^aeiou][aeiou][bdgmnprt]", last):
        forms |= {last + last[-1] + "ed", last + last[-1] + "ing"}
    words = "|".join(sorted((re.escape(f) for f in forms), key=len, reverse=True))
    prefix = (re.escape(head) + r"\s+") if head else ""
    return rf"\b{prefix}(?:{words})\b"


@functools.lru_cache(maxsize=None)
def term_pattern(term: str) -> re.Pattern:
    """Terimin derlenmiş deseni (16 Eki: önbellek; eşleşme aynı, sadece hız)."""
    return re.compile(_term_re(term))


def find_terms(terms, text: str) -> list[str]:
    """Metinde geçen terimler (çekimleriyle)."""
    low = (text or "").lower()
    return [t for t in terms if term_pattern(t).search(low)]


def _first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s+", (text or "").strip(), maxsplit=1)[0]


def trigger_stems(event: str) -> set[str]:
    """Olay adının tetik kökleri: olay kökleri eksi yer/bağlam kökleri."""
    from core.prompt_generator import _event_stems
    return _event_stems(event) - _SETTING_STEMS


def story_rule_issues(event: str, ship: str | None, story: str, suffix: str | None = None) -> list[dict]:
    """Kural kapısı. Her sorun: {"rule", "missing" (Telegram, Türkçe), "feedback" (GPT, İngilizce)}.
    Boş liste = geçti. 40-60 kelime biçim kontrolü de burada (önceden vardı, 6 kurala sayılmaz)."""
    from core.prompt_generator import _event_stems, _verb_stem, event_fidelity_issues, text_event_stems
    story = story or ""
    out = []

    def add(rule, missing, feedback):
        out.append({"rule": rule, "missing": missing, "feedback": feedback})

    n = len(story.split())
    if not MIN_WORDS <= n <= MAX_WORDS:
        add("length", f"40-60 kelime ({n} kelime)", f"The story has {n} words; write {MIN_WORDS} to {MAX_WORDS} words.")
    # a
    first_sentence = _first_sentence(story)
    # Gevşetme (Bahadır onayı, 30 Eyl, iyi sel hikâyeleri reddediliyordu: "a wall of brown water bursts..."):
    # olayın ilk anahtar grubundaki kelimeler de tetik sayılır.
    groups = EVENT_REQUIRED[event]
    if not (trigger_stems(event) & text_event_stems(first_sentence)
            or (groups and find_terms(groups[0], first_sentence))):
        add("a_trigger_first", STORY_RULES["a_trigger_first"],
            f"The first sentence must show the trigger happening: '{event}'.")
    # b
    cam = find_terms(CAMERA_WORDS, story)
    if cam:
        add("b_no_camera_words", f"{STORY_RULES['b_no_camera_words']} ({', '.join(cam)})",
            f"Remove the words {', '.join(cam)}; describe only the scene itself.")
    # c
    meta = find_terms(META_PHRASES, story)
    if meta:
        add("c_no_meta_or_waiting", f"{STORY_RULES['c_no_meta_or_waiting']} ({', '.join(meta)})",
            f"Remove {', '.join(repr(m) for m in meta)}: no waiting, tension or talk about the video; show action.")
    # d
    small = find_terms(SCALE_REDUCERS, story)
    if small:
        add("d_no_scale_reducers", f"{STORY_RULES['d_no_scale_reducers']} ({', '.join(small)})",
            f"Remove {', '.join(repr(s) for s in small)}: the event is catastrophic, never mild or harmless.")
    # e
    if event_fidelity_issues(event, story):
        # Geri bildirim eksik kelimeleri söyler (29 Eyl kanıt koşusu: "deluge" yazan sel hikâyesi iki kez kaldı)
        missing = _event_stems(event) - _event_stems(story)
        words = list(dict.fromkeys(w for w in re.findall(r"[A-Za-z]+", event) if _verb_stem(w.lower())[:4] in missing))
        add("e_event_and_ship_named", f"olay adı ({', '.join(words)})",
            f"The story must clearly show this event: '{event}'. Name it with its own words "
            f"(for example: {', '.join(words)}).")
    ship_words = SHIP_TYPE_WORDS.get(ship or "", ())
    if ship_words and not find_terms(ship_words, story):
        add("e_event_and_ship_named", f"gemi türü ({ship_words[0]})",
            f"Name the vessel by its type: {SHIP_PHRASES.get(ship, ship)}.")
    # f
    if suffix is not None and "phone" in suffix.lower():
        add("f_no_phone_in_style", STORY_RULES["f_no_phone_in_style"], "")
    # Olay anahtar grupları
    for group in EVENT_REQUIRED[event]:
        if not find_terms(group, story):
            add("required", f"anahtar grup: {' / '.join(group)}",
                f"The story must show one of: {', '.join(group)}.")
    # Yasak liste (sadece iki kızak olayı)
    bad = find_terms(EVENT_FORBIDDEN.get(event, ()), story)
    if bad:
        add("forbidden", f"yasak kelime: {', '.join(bad)} ({FORBIDDEN_FEEDBACK_TR})",
            f"Do not use: {', '.join(bad)}. {FORBIDDEN_FEEDBACK_EN}")
    return out


class CreativeStoryError(NoValidScenarioError):
    """GPT-4o hikâyesi 3 denemede de kural kapısından geçemedi; Kie'ye gidilmez. NoValidScenarioError olduğu için
    main.py Telegram'a ayrıntıyı (trace) ve açık hata özetini gönderir."""

    def __init__(self, message: str, attempts: list[dict], trace: dict | None = None):
        super().__init__(message, attempts=attempts, trace=trace)

    def short_summary(self, max_reason: int = 0) -> str:
        """Deneme başına tek satır: 'Deneme 2 · ❌ eksik: ilk cümlede tetik; anahtar grup: wave'."""
        lines = [str(self)] + [f"Deneme {a.get('attempt')} · ❌ eksik: {'; '.join(a.get('missing') or ['?'])}"
                               for a in self.attempts]
        return "\n".join(lines)


def story_issues(event: str, story: str, ship: str | None = None) -> list[str]:
    """GPT'ye giden geri bildirim cümleleri (kural kapısı). Boş liste = geçti."""
    return [i["feedback"] for i in story_rule_issues(event, ship, story) if i["feedback"]]


def pick_setting(event: str, rng: random.Random | None = None, view: str | None = None) -> tuple[str, str]:
    """(yer anahtarı, hava) iskelet listelerinden rastgele; görünüm varsa onunla çakışmayan yerlerden."""
    rng = rng or random
    s = EVENT_SKELETONS[event]
    return rng.choice(view_spots(event, view)), rng.choice(s["weather"])


def recent_stories(history_texts: list[str], limit: int = RECENT_STORIES) -> list[str]:
    """Geçmişten hikâye gibi olan (en az 20 kelimelik) son metinler; başlıklar elenir."""
    return [t for t in history_texts if len((t or "").split()) >= 20][-limit:]


def _message(event: str, ship: str | None, place: str, weather: str, lo: int, hi: int, recent: list[str],
             feedback: list[str] | None) -> str:
    msg = (f"EVENT: {event}\nVESSEL: {SHIP_PHRASES.get(ship or '', 'none')}\nPLACE: {place}\nWEATHER: {weather}\n"
           f"PEOPLE VISIBLE: {lo} to {hi}\nOUTCOME TO REACH IN THE LAST BEAT: {EVENT_OUTCOMES[event]}\nRECENT STORIES:\n" + ("\n".join(f"- {s}" for s in recent) or "- (none)"))
    if feedback:
        msg += "\n\nYOUR PREVIOUS STORY WAS REJECTED: " + " ".join(feedback)
    return msg


async def write_story(event: str, ship: str | None, place: str, weather: str, recent: list[str],
                      call_gpt) -> tuple[str, list[dict]]:
    """GPT-4o hikâyesi; kural kapısından kalırsa geri bildirimle yeniden, en fazla MAX_ATTEMPTS deneme.
    (hikâye, deneme kaydı). Deneme kaydında "issues" GPT'ye giden geri bildirim, "missing" Türkçe unsurlar."""
    lo, hi = count_range(event, ship)
    attempts, feedback = [], None
    for attempt in range(MAX_ATTEMPTS):
        raw = await call_gpt(CREATIVE_SYSTEM, _message(event, ship, place, weather, lo, hi, recent, feedback),
                             temperature=0.9, model="gpt-4o")
        story = str((raw or {}).get("story") or "").strip()
        found = story_rule_issues(event, ship, story) + diversity_issues(story, recent)
        issues = [i["feedback"] for i in found if i["feedback"]]
        attempts.append({"attempt": attempt + 1, "story": story, "words": len(story.split()), "issues": issues,
                         "missing": [i["missing"] for i in found]})
        if not found:
            return story, attempts
        feedback = issues
    raise CreativeStoryError(f"Hikâye {MAX_ATTEMPTS} denemede kural kapısından geçmedi, Kie'ye gönderilmedi.",
                             attempts)


# ── YAPILANDIRILMIŞ HAT (4 Eki, Bahadır): core/event_structure.py olayları ─────────────────────────────────────
# GPT sadece üç dilim metnini yazar (strict JSON şeması); kilit görsel, etiketler, 4-9s/9-15s olayı ve araç kodda.
# API/JSON/şema hatası deneme yemez, akış durur (sessiz yedek yok). Kalite kapısından kalan dilimler geri
# bildirimle yeniden yazılır (MAX_ATTEMPTS).
SLICES_SYSTEM = """You write the three time slices of one 15-second realistic video of a real incident.
The code already wrote the opening sentence of 0-4s and adds the time labels; never write labels.
Return JSON with three fields:
- slice_1_rest: one sentence of 6 to 18 words that continues 0-4s right after the opening sentence: how the opening event hits this place.
- slice_2: the given 4-9s event in 10 to 24 words, in your own words for this place; use every given detail.
- slice_3: the given 9-15s event in 10 to 24 words, a new and bigger destruction, still moving at the very end.
Rules: describe only what is visible, never sounds, the camera or the video. People stay in the middle and far distance and are never the main event. Catastrophic in scale, never mild or harmless. Make it different from the recent stories."""


def _slices_message(spec: dict, place: str, weather: str, lo: int, hi: int, recent: list[str],
                    feedback: list[str] | None) -> str:
    event = spec["event"]
    # 13 Eki: araçsız olaylarda (lav, kül bulutu) VEHICLE satırı yok
    vehicle_line = f"VEHICLE: {spec['vehicle']}\n" if spec["vehicle"] is not None else ""
    msg = (f"OPENING SENTENCE (fixed, already written): {spec['key_visual']}\nPLACE: {place}\nWEATHER: {weather}\n"
           f"PEOPLE VISIBLE: {lo} to {hi}\n{vehicle_line}"
           # 4 Eki, Bahadır: kişi sayısını kod seçer, GPT cümleye döker (sadece kişi kuralı olan olaylarda)
           + es.people_line(spec)
           + es.word_budget_line(spec)   # 14 Eki (2): çığda dilim kelime bütçesi
           + f"4-9s EVENT: {es.beat_text(event, 'slice_2', spec['beat_2'], spec['vehicle'])}\n"
           f"9-15s EVENT: {es.beat_text(event, 'slice_3', spec['beat_3'])}\n"
           "RECENT STORIES:\n" + ("\n".join(f"- {s}" for s in recent) or "- (none)"))
    if feedback and es.SLICE_RULES.get(event):
        # 4 Eki, Bahadır: birikimli geri bildirim; düzeltilen madde sonraki denemede silinmesin
        msg += ("\n\nYOUR PREVIOUS ANSWERS WERE REJECTED. Fix ALL of these and keep everything that was already "
                "correct: " + " ".join(feedback))
    elif feedback:
        msg += "\n\nYOUR PREVIOUS ANSWER WAS REJECTED: " + " ".join(feedback)
    return msg


def _gpt_text(spec: dict, text: str) -> str:
    """Çeşitlilik ölçümü için sadece GPT'nin yazdığı kısım: kilit görsel ve etiketler çıkar (ortak oldukları için
    benzerliği yapay olarak şişirmesinler)."""
    text = (text or "").replace(spec["key_visual"], " ")
    for label in es.SLICE_LABELS:
        text = text.replace(f"{label}:", " ")
    return " ".join(text.split())


def structured_issues(spec: dict, slices: dict, recent: list[str]) -> list[dict]:
    """Dilim kalite kapısı: dilim içeriği (event_structure; toplam kelime ve karakter dahil) + 6 sabit kural +
    çeşitlilik (GPT metni üzerinde). Genel 40-60 "length" kuralı burada yok: yerini es.TOTAL_WORDS aldı."""
    out = es.slice_issues(spec, slices)
    fixed = set(STORY_RULES)
    out += [i for i in story_rule_issues(spec["event"], spec["ship"], es.plain_story(spec, slices)) if i["rule"] in fixed]
    gpt_only = " ".join(slices[f] for f in es.SLICE_FIELDS)
    out += diversity_issues(gpt_only, [_gpt_text(spec, r) for r in recent])
    return out


async def write_slices(spec: dict, place: str, weather: str, recent: list[str], call_gpt,
                       max_attempts: int = MAX_ATTEMPTS, initial_feedback: list[str] | None = None
                       ) -> tuple[dict, list[dict]]:
    """Strict şemalı GPT-4o dilimleri; kapıdan kalırsa geri bildirimle yeniden, en fazla max_attempts deneme.
    (dilimler, deneme kaydı). GPT/JSON/şema hatası yükselir (deneme sayılmaz, yedek yok)."""
    lo, hi = count_range(spec["event"], spec["ship"])
    attempts, feedback = [], initial_feedback
    for attempt in range(max_attempts):
        raw = await call_gpt(SLICES_SYSTEM, _slices_message(spec, place, weather, lo, hi, recent, feedback),
                             temperature=0.9, model="gpt-4o", json_schema=es.SLICE_SCHEMA)
        slices = es.parse_slices(raw)
        found = structured_issues(spec, slices, recent)
        story = es.assemble_story(spec, slices)
        issues = [i["feedback"] for i in found if i["feedback"]]
        attempts.append({"attempt": attempt + 1, "story": story, "slices": slices,
                         "words": len(es.plain_story(spec, slices).split()), "issues": issues,
                         "missing": [i["missing"] for i in found]})
        if not found:
            return slices, attempts
        # Dilim kapısı olan olaylarda önceki tüm ret nedenleri (tekrarsız) birikir; diğerlerinde sadece son ret
        feedback = list(dict.fromkeys((feedback or []) + issues)) if es.SLICE_RULES.get(spec["event"]) else issues
    raise CreativeStoryError(f"Hikâye {max_attempts} denemede kural kapısından geçmedi, Kie'ye gönderilmedi.",
                             attempts)


# ── HİBRİT HİKÂYE (16 Eki 2026, Bahadır) ────────────────────────────────────────────────────────────────────
# Yapılandırılmış hatta GPT en fazla 2 deneme; geçemezse kod yedeği (es.build_fallback). Eski hat MAX_ATTEMPTS (3)
# ile aynı kalır; Kie reddi sonrası yeniden yazım (rewrite_structured) da MAX_ATTEMPTS kullanır (değişmedi).
STRUCTURED_MAX_ATTEMPTS = 2
# Her yapılandırılmış üretimin hikâye kaynağı bir satır JSON olarak eklenir (tools/fallback_report.py okur). Yol:
# STORY_SOURCE_LOG ortam değişkeni, yoksa data/story_source_log.jsonl. Testler (unittest yüklüyken) ortam değişkeni
# verilmedikçe yazmaz: gerçek istatistik test üretimleriyle kirlenmesin.
STORY_SOURCE_LOG_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data",
                                        "story_source_log.jsonl")


def story_source_log_path() -> str | None:
    path = os.environ.get("STORY_SOURCE_LOG")
    if path:
        return path
    if "unittest" in sys.modules:
        return None
    return STORY_SOURCE_LOG_DEFAULT


def record_story_source(entry: dict) -> None:
    """data/story_source_log.jsonl'e bir satır (zaman damgalı). Yazılamazsa üretimi düşürmez."""
    path = story_source_log_path()
    if not path:
        return
    row = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **entry}
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as e:
        log.warning(f"⚠️ Hikâye kaynağı kaydı yazılamadı: {e}")


def fallback_reason(attempts: list[dict]) -> str:
    """Yedeğe düşme nedeni: her denemenin eksikleri (kısa)."""
    parts = [f"deneme {a.get('attempt')}: " + "; ".join(a.get("missing") or ["?"]) for a in attempts]
    text = " | ".join(parts) or "GPT denemesi yok"
    return text if len(text) <= 300 else text[:297] + "..."


def story_source_label(source: dict) -> str:
    """Onay mesajı satırı: "Hikâye: GPT (deneme N)" ya da "Hikâye: kod yedeği (neden: ...)"."""
    if source["kind"] == "gpt":
        return f"Hikâye: GPT (deneme {source['attempt']})"
    return f"Hikâye: kod yedeği (neden: {source['reason']})"


REWRITE_FEEDBACK = ("The video safety check rejected the previous text ({reason}). Rewrite the three fields to show "
                    "the same events with no graphic injury, blood or death.")


async def rewrite_structured(structure: dict, reason: str, call_gpt) -> str:
    """Preflight/Kie reddinden sonra TEK yeniden yazım turu (Bahadır onayı, 4 Eki): bizim yazar aynı şema ve aynı
    olaylarla, ret nedeni geri bildirimiyle çağrılır; kalite kapısı için ilk yazımdaki gibi MAX_ATTEMPTS deneme.
    Kie'ye yeniden gönderim hakkı yine tek (kie_client). Kilit görsel, etiketler, olaylar ve stil eki koddan yeniden
    kurulur. Kapıdan ya da son denetimden geçmezse StructureError (akış durur). Başarılıysa structure["slices"]
    güncellenir, yeni etiketli hikâye döner."""
    spec = structure["spec"]
    # 10 Eki, Bahadır: her denemenin tam metni ve sonucu kaydedilir (main.py Notion gövdesine yazar)
    entry = {"reason": reason, "attempts": [], "result": "?"}
    structure.setdefault("rewrite_log", []).append(entry)
    try:
        slices, attempts = await write_slices(spec, structure["place"], structure["weather"], structure["recent"],
                                              call_gpt, max_attempts=MAX_ATTEMPTS,
                                              initial_feedback=[REWRITE_FEEDBACK.format(reason=reason)])
    except CreativeStoryError as e:
        entry["attempts"] = e.attempts
        missing = "; ".join((e.attempts[-1].get("missing") or ["?"])) if e.attempts else "?"
        entry["result"] = f"kural kapısından geçmedi: {missing}"
        raise es.StructureError(f"Ret sonrası yeniden yazım kural kapısından geçmedi: {missing}") from e
    entry["attempts"] = attempts
    final = es.final_prompt_issues(spec, slices, es.assemble_prompt(spec, slices), es.assemble_story(spec, slices))
    if final:
        entry["result"] = "son denetimden geçmedi: " + "; ".join(i["missing"] for i in final)
        raise es.StructureError("Ret sonrası yeniden yazım son denetimden geçmedi: "
                                + "; ".join(i["missing"] for i in final))
    entry["result"] = "geçti"
    structure["slices"] = slices
    structure["rewrites"] = structure.get("rewrites", 0) + 1
    return es.assemble_story(spec, slices)


def submit_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce (main.before_submit): gönderilecek metin structure'dan yeniden kurulanla birebir aynı mı,
    stil eki beklenen mi, son denetim temiz mi. Boş liste = gönderilebilir."""
    spec, slices = structure["spec"], structure["slices"]
    out = []
    if info.get("style_suffix") != spec["suffix"]:
        out.append("stil eki gönderimde değişmiş")
    out += [i["missing"] for i in es.final_prompt_issues(spec, slices, info.get("prompt", ""), info.get("story", ""))]
    return out


HISTORY_WARNING = "⚠️ geçmiş Notion'dan okunamadı"


def _with_used(fn, *args, used=None, kw: str = "used", **kwargs):
    """Seçiciyi geçmişle çağırır; geçmiş boşsa parametresiz (eski çağrı biçimi, eski davranış: süreç hafızası)."""
    return fn(*args, **({kw: used} if used else {}), **kwargs)


async def load_axes_history(domain: str, event: str, axes_loader) -> dict:
    """21 Eki (Gece 1 / Aşama 3): seçimden önce eksen geçmişi. axes_loader(domain) -> ham Notion kayıtları (eskiden
    yeniye, iptaller dahil). Dönüş: {"event": olayın son 10 kaydı, "category": kategorinin son 10 kaydı (çığ/deprem
    ortamı ve spotu), "source": "notion" | "bellek" | "yok", "warning": str | None}. Okuma başarısızsa ya da Notion
    kapalıysa süreç hafızası (es._AXES_MEMORY; kategori ortamı için event_structure'ın kendi hafızası, category=None);
    okuma hatası üretimi durdurmaz, Onay mesajına uyarı satırı gider. Yükleyici hiç verilmediyse (betikler, testler,
    kuru deneme) yeni eksenlerde geçmiş yok ("yok"): eski davranış birebir (ortam eksenleri kendi süreç hafızasıyla)."""
    import core.axes_history as ah
    warning = None
    if axes_loader is None:
        return {"event": [], "category": None, "source": "yok", "warning": None}
    else:
        try:
            records = await asyncio.to_thread(axes_loader, domain)
            if records is not None and not isinstance(records, list):
                raise TypeError(f"eksen geçmişi liste değil: {type(records).__name__}")
            if records is not None:
                parsed = ah.build_history(records)
                group = (es.AVALANCHE_EVENTS if event in es.AVALANCHE_EVENTS
                         else es.EARTHQUAKE_EVENTS if event in es.EARTHQUAKE_EVENTS else (event,))
                return {"event": ah.event_history(parsed, event), "category": ah.category_history(parsed, group),
                        "source": "notion", "warning": None}
        except Exception as e:   # noqa: BLE001 - okuma hatası üretimi durdurmaz
            log.warning(f"⚠️ Eksen geçmişi Notion'dan okunamadı, süreç hafızasıyla devam: {e}")
            warning = HISTORY_WARNING
    return {"event": es.axes_memory(event), "category": None, "source": "bellek", "warning": warning}


def _axes_line(axes: dict, excluded: dict, source: str, warning: str | None) -> str:
    """Onay mesajı satırı (Bahadır okusun diye kısa)."""
    env = axes.get("view") or axes.get("env")
    if isinstance(env, dict):
        env = ", ".join(str(v) for v in env.values())
    shown = {"spot": axes.get("spot"), "ortam": env, "ışık": axes.get("light"), "araç": axes.get("vehicle"),
             "kişi": axes.get("people")}
    line = "Eksenler: " + " · ".join(f"{k}={v if v not in (None, '') else '-'}" for k, v in shown.items())
    names = {"spot": "spot", "env": "ortam", "view": "ortam", "light": "ışık", "vehicle": "araç", "people": "kişi"}
    gone = [f"{names[k]}: {', '.join(str(x) for x in v)}" for k, v in excluded.items() if v and k in names]
    line += f"\nTekrar önleme ({source}): " + ("elenen " + " · ".join(gone) if gone else "elenen yok")
    if warning:
        line += f"\n{warning}"
    return line


async def build_creative_scene(domain: str | None, event: str | None, history: list[str], history_texts: list[str],
                               call_gpt, view: str | None = None, axes_loader=None) -> dict:
    """Seçim (Python) + GPT-4o hikâyesi + iskeletle aynı stil eki. view: Telegram bölge menüsünden seçilen görünüm
    (sadece şehir olayları); None ise LRU seçer. axes_loader: 21 Eki, Notion eksen geçmişi okuyucusu (domain ->
    ham kayıtlar); None ise süreç hafızası (betikler, testler)."""
    import core.axes_history as ah
    domain, event, ship = choose_event_and_ship(domain, event, history)
    structured = es.is_structured(event)
    hist = (await load_axes_history(domain, event, axes_loader) if structured
            else {"event": [], "category": None, "source": "bellek", "warning": None})
    from_notion = hist["source"] == "notion"
    ev_hist, cat_hist = hist["event"], hist["category"]
    excluded = {}
    if view is not None:
        if event not in REGION_VIEW_EVENTS or view not in REGION_VIEWS:
            raise ValueError(f"Bu olayda bu görünüm seçilemez: {event} / {view}")
        view_source = "menü"
    elif from_notion and event in REGION_VIEW_EVENTS:   # 21 Eki: Notion eksen geçmişinden LRU (iptaller dahil)
        from core.skeleton_pipeline import _lru
        seen = ah.values(ev_hist, "view")
        view = _lru(list(REGION_VIEWS), seen)
        view_source = "Python, LRU (Notion)"
        excluded["view"] = [v for v in REGION_VIEWS if v in seen[-es.AXIS_BLOCK:]]
    else:
        view = choose_region_view(event, history)   # şehir olayları (1 Eki); diğerlerinde None
        view_source = "Python, LRU" if view else None
    remember_view(event, view)                   # seçim anında: TEST/iptal/bitmemiş üretim de sayılsın
    used_spot, used_light = ah.values(ev_hist, "spot"), ah.values(ev_hist, "light")
    if structured and (used_spot or used_light):   # 21 Eki: spot ve ışıkta son 2 elenir (pick_setting ile aynı sıra)
        spot_c, excluded["spot"] = es.lru_axis(view_spots(event, view), used_spot)
        light_c, excluded["light"] = es.lru_axis(list(EVENT_SKELETONS[event]["weather"]), used_light)
        spot, weather = random.choice(spot_c), random.choice(light_c)
    else:
        spot, weather = pick_setting(event, view=view)
    if event in es.ENV_EVENTS:   # 14 Eki (4): çığda kamera noktası da ortam ekseni (kategori LRU)
        spots = view_spots(event, view)
        used = ah.values(cat_hist, "spot") if cat_hist is not None else None
        spot = _with_used(es.choose_env_spot, event, spots, used=used)
        excluded["spot"] = es.lru_axis(spots, used)[1] if used is not None else []
        excluded["light"] = []   # ışık ortam ekseninin parçası (choose_environment)
    elif event == es.FIRE_TORNADO:   # 16 Eki: ateş hortumu ortam ekseni (LRU), nokta ortamın iki noktasından
        used_env = ah.values(ev_hist, "env") if from_notion else None
        fire_env = _with_used(es.choose_fire_env, used=used_env)
        excluded["env"] = es.lru_axis(list(es.FIRE_TOR_ENVS), used_env)[1] if used_env is not None else []
        es.remember_fire_env(fire_env)           # seçim anında: TEST/iptal/bitmemiş üretim de sayılsın
        spot_c, excluded["spot"] = es.lru_axis(list(es.FIRE_TOR_ENVS[fire_env]["spots"]), ah.values(ev_hist, "spot"))
        spot = random.choice(spot_c)
    volc_env = None
    if event in es.VOLC_ENV_EVENTS:   # 18 Eki (3): bombalar ve kül bulutu ortam ekseni + yer ağırlığı + ışık
        used_env = ah.values(ev_hist, "env") if from_notion else None
        used_spot = ah.values(ev_hist, "spot") if from_notion else None
        volc_env = _with_used(es.choose_volc_env, event, used=used_env)
        spot = _with_used(es.choose_volc_spot, event, history, used=used_spot)
        weather = _with_used(es.choose_volc_weather, event, used=ah.values(ev_hist, "light"))
        spots = list(EVENT_SKELETONS[event]["spots"])
        excluded["env"] = es.lru_axis(list(es.VOLC_ENV_WEIGHTS[event]), used_env)[1] if used_env is not None else []
        excluded["spot"] = (es.lru_axis(spots, used_spot)[1] if used_spot is not None
                            else es.lru_axis(spots, es.volc_spot_history(event, history))[1])
        excluded["light"] = es.lru_axis(list(es.VOLCANO_WEATHER_WEIGHTS[event]), ah.values(ev_hist, "light"))[1]
        es.remember_volc_env(event, volc_env)    # seçim anında: TEST/iptal/bitmemiş üretim de sayılsın
        es.remember_volc_spot(event, spot)
    place = view_place(event, EVENT_SKELETONS[event]["spots"][spot], view)
    if volc_env:
        place = es.volc_place(event, volc_env)
    recent = recent_stories(history_texts)
    if structured:
        return await _build_structured_scene(domain, event, ship, spot, view, view_source, weather, place, recent,
                                             history, call_gpt, volc_env=volc_env, hist=hist, excluded=excluded)
    lo, hi = count_range(event, ship)
    trace = {"pipeline": "creative", "domain": domain, "event": event, "ship": ship or "None",
             "camera": SKELETON_CAMERA, "spot": spot, "view": view, "view_source": view_source, "place": place, "weather": weather, "count_range": [lo, hi],
             "outcome": EVENT_OUTCOMES[event], "recent_count": len(recent), "attempts": [], "story": "",
             "story_words": 0}
    try:
        story, attempts = await write_story(event, ship, place, weather, recent, call_gpt)
    except CreativeStoryError as e:
        e.trace = {**trace, "attempts": e.attempts}
        raise
    suffix = style_suffix(event, ship, spot, view)
    # f: stil eki sabittir; "phone" girerse Kie'ye gitmez (kod hatası, GPT'ye geri bildirim yok)
    phone = [i for i in story_rule_issues(event, ship, story, suffix) if i["rule"] == "f_no_phone_in_style"]
    if phone:
        raise CreativeStoryError("Stil ekinde 'phone' var, Kie'ye gönderilmedi.", attempts, trace)
    spot_key = f"{spot.lower()}#{view}" if view else spot.lower()
    combo_key = f"{domain}|{(ship or 'none').lower()}|{event.lower()}|{spot_key}|{SKELETON_CAMERA}"
    trace.update(attempts=attempts, story=story, story_words=len(story.split()))
    log.info(f"✍️ Creative: [{domain}] {event} | gemi={ship} | yer={spot} | görünüm={view} | hava={weather} | {len(story.split())} kelime")
    axes = {"spot": spot, "view": view, "light": weather}   # 21 Eki: serbest hatta sadece kayıt (LRU yok)
    return {"domain": domain, "event": event, "ship": ship, "spot": spot, "story": story, "style_suffix": suffix,
            "prompt": f"{story.rstrip('.')}. {suffix}", "combo_key": combo_key, "trace": trace,
            "axes_json": ah.axes_json(event, axes)}


async def _build_structured_scene(domain, event, ship, spot, view, view_source, weather, place, recent, history,
                                  call_gpt, volc_env: str | None = None, hist: dict | None = None,
                                  excluded: dict | None = None) -> dict:
    """Yapılandırılmış olay: olay çifti + araç (kod), dilimler (GPT), son denetim (kod). Son denetim tutmazsa
    StructureError: Kie'ye gidilmez."""
    import core.axes_history as ah
    hist = hist or {"event": [], "category": None, "source": "yok", "warning": None}
    excluded = dict(excluded or {})
    ev_hist, cat_hist = hist["event"], hist["category"]
    b2, b3 = es.choose_beats(event, view, spot, history)
    # Görünümü olmayan olayda (heyelan, TASLAK) araç olayın kendi listesinden; araçsız olayda (13 Eki: lav, kül
    # bulutu) araç seçilmez. 21 Eki: araç ve kişi sayısında son 2 elenir
    used_vehicle = ah.values(ev_hist, "vehicle")
    if not es.uses_vehicle(event):
        vehicle = None
    else:
        vehicle = (_with_used(es.choose_vehicle, view, used=used_vehicle) if view is not None
                   else _with_used(es.choose_event_vehicle, event, used=used_vehicle))
        options = [v for v, _ in es.event_vehicles(event, view)]
        excluded["vehicle"] = es.lru_axis(options, used_vehicle)[1]
    used_people = ah.values(ev_hist, "people")
    people = _with_used(es.choose_people, event, ship, used=used_people)   # kaçan kişi sayısı N; combo_key'e girmez
    if people is not None:
        lo_p, hi_p = count_range(event, ship)
        excluded["people"] = es.lru_axis(list(range(lo_p, hi_p + 1)), used_people)[1]
    tag = es.beat_tag(b2, b3)
    es.remember_beats(event, tag)                # seçim anında: TEST/iptal/bitmemiş üretim de sayılsın
    # 14 Eki (4): çığda ortam (dağ, yerleşim, ışık) koddan; GPT'ye WEATHER satırı olarak, Kie'ye stil ekinde gider
    env = setting = None
    env_label = None
    if event == es.FIRE_TORNADO:   # 16 Eki: ortam kamera noktasından (spec["fire_env"]); onay mesajında "Ortam:" satırı
        env_label = es.fire_env_label(es.fire_env_of_spot(spot), spot)
    if volc_env:   # 18 Eki (3): bombalar / kül bulutu
        env_label = es.volc_env_label(volc_env, spot)
    if event in es.ENV_EVENTS:
        mem = ([h["env"] for h in cat_hist if isinstance(h.get("env"), dict)] if cat_hist is not None else None)
        env = _with_used(es.choose_environment, event, spot, b2, b3, used=mem, kw="mem")
        es.remember_environment(env)             # seçim anında (beat hafızası gibi)
        setting = es.setting_line(env)
        weather = es.env_weather(env)   # 14 Eki: çığ ve deprem
    spec = es.build_spec(event, ship, spot, view, b2, b3, vehicle, people, setting, volc_env)
    # 21 Eki: seçilen tüm eksenler (Notion "Eksenler" + süreç hafızası + Onay satırı)
    axes = {"spot": spot, "view": view,
            "env": ({k: v for k, v in env.items() if k != "spot"} if env else (spec.get("fire_env") or volc_env)),
            "light": env["light"] if env else weather, "vehicle": vehicle, "people": people,
            "key": spec.get("fire_env") or "default", "beats": tag}
    es.remember_axes(event, axes)
    axes_line = _axes_line(axes, excluded, hist["source"], hist["warning"])
    lo, hi = count_range(event, ship)
    trace = {"pipeline": "creative", "structured": True, "domain": domain, "event": event, "ship": ship or "None",
             "camera": SKELETON_CAMERA, "spot": spot, "view": view, "view_source": view_source, "place": place,
             "weather": weather, "count_range": [lo, hi], "key_visual": spec["key_visual"], "beats": tag,
             "vehicle": vehicle, "people_running": people, "beat_2_text": es.beat_text(event, "slice_2", b2, vehicle),
             "beat_3_text": es.beat_text(event, "slice_3", b3), "outcome": EVENT_OUTCOMES[event],
             "recent_count": len(recent), "attempts": [], "story": "", "story_words": 0}
    trace["axes"] = axes
    trace["axes_excluded"] = excluded
    trace["axes_source"] = hist["source"]
    if env:
        trace["environment"] = env
    if env_label and event == es.FIRE_TORNADO:
        trace["fire_env"] = spec["fire_env"]
        trace["fire_env_label_short"] = es.FIRE_TOR_ENVS[spec["fire_env"]]["label"]
    if volc_env:   # 18 Eki (3): onay "Yer" satırında "ortam: ..." (aynı alan), Notion "Ortam" alanı
        trace["volc_env"] = volc_env
        trace["fire_env_label_short"] = es.VOLC_ENVS[volc_env]["label"]
    # 16 Eki, Bahadır (hibrit hikâye): GPT en fazla STRUCTURED_MAX_ATTEMPTS deneme; ikisi de kapıdan geçemezse kod
    # yedeği (üretim durmaz). GPT/JSON/şema hatası yine akışı durdurur (yedek sadece kapı retleri için).
    try:
        slices, attempts = await write_slices(spec, place, weather, recent, call_gpt,
                                              max_attempts=STRUCTURED_MAX_ATTEMPTS)
        source = {"kind": "gpt", "attempt": len(attempts), "reason": ""}
    except CreativeStoryError as e:
        attempts = e.attempts
        slices = es.build_fallback(spec)
        source = {"kind": "fallback", "attempt": len(attempts), "reason": fallback_reason(attempts)}
        log.warning(f"🧩 Kod yedeği: {event} | {tag} | {source['reason']}")
    source["label"] = story_source_label(source)
    story = es.assemble_story(spec, slices)
    prompt = es.assemble_prompt(spec, slices)
    final = es.final_prompt_issues(spec, slices, prompt, story)
    if final:
        raise es.StructureError("Son denetim geçmedi, Kie'ye gönderilmedi: " + "; ".join(i["missing"] for i in final))
    record_story_source({"event": event, "environment": (spec.get("fire_env") or spec.get("volc_env")
                                                         or (es.setting_line(env) if env else None)),
                         "spot": spot, "view": view, "beats": tag, "vehicle": vehicle, "source": source["kind"],
                         "gpt_attempts": len(attempts), "fallback_reason": source["reason"] or None,
                         "attempt_missing": [a.get("missing") for a in attempts]})
    # Görünüm yoksa boş bırakılır ("spot##H1+M1"): view_of_combo None döner, olay çifti 3. parçada kalır
    combo_key = (f"{domain}|{(ship or 'none').lower()}|{event.lower()}|{spot.lower()}#{view or ''}#{tag}|"
                 f"{SKELETON_CAMERA}")
    plain = es.plain_story(spec, slices)
    trace.update(attempts=attempts, story=story, story_words=len(plain.split()), slices=slices,
                 story_source=source["label"])
    log.info(f"✍️ Creative (yapılandırılmış): [{domain}] {event} | yer={spot} | görünüm={view} | olaylar={tag} | "
             f"araç={vehicle} | {len(plain.split())} kelime")
    return {"domain": domain, "event": event, "ship": ship, "spot": spot, "story": story, "plain_story": plain,
            "style_suffix": spec["suffix"], "prompt": prompt, "combo_key": combo_key, "trace": trace,
            "structure": {"spec": spec, "slices": slices, "place": place, "weather": weather, "recent": recent,
                          "environment": es.environment_label(env) if env else env_label,
                          # 18 Eki (3): Notion "Ortam" alanı (sadece bombalar / kül bulutu)
                          "env_option": es.VOLC_ENVS[volc_env]["label"] if volc_env else None,
                          "story_source": source["label"], "story_source_kind": source["kind"],
                          # 21 Eki: Notion "Eksenler" (seçim anında yazılır) ve Onay mesajı satırı
                          "axes": axes, "axes_json": ah.axes_json(event, axes, excluded), "axes_line": axes_line,
                          "axes_warning": hist["warning"]},
            "axes_json": ah.axes_json(event, axes, excluded)}
