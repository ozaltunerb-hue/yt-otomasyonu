#!/usr/bin/env python3
"""
❄️ Çığ kategorisi (13 Eki 2026, Bahadır; TASLAK): 3 olay yapılandırılmış hatta, volkan yapısı (sabit yüksek kamera,
kod havuzu, araçsız, 175 kelime kapısı, olaya özel yasak kelimeler). KİLİT: havuz/kilit cümle/kamera Bahadır'ın
onayıyla değişir. Ağ yok, Kie/GPT çağrısı yok.
14 Eki (ilk test dersi): kamera aksiyona yakın, ilk temas 0-2 sn'de, nesneler büyük ve koyu; insanlar kameraya yakın.
"""
import asyncio
import os
import random
import re
import sys
import unittest
from itertools import combinations
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.skeleton_pipeline as sk

KOY, KAYAK, ORMAN = es.AVALANCHE_VILLAGE, es.AVALANCHE_SKI, es.AVALANCHE_FOREST
AVA = (KOY, KAYAK, ORMAN)
HT, BAL, LIFT = ("Terrace at the edge of the village", "Balcony of a chalet at the edge of the village",
                 "Terrace of the lift station")
# 14 Eki (2): kısa adlar ve kısa kamera şablonu (175 kelime sınırı)
CAMS = {HT: "a village-edge terrace", BAL: "a village-edge chalet balcony", LIFT: "the lift station terrace"}
# 14 Eki (5): yamaç ve çığ kadrajın üst yarısında, binalar ve korkuluk alt yarısında (kayakta yamaç kadrajda yoktu)
CAMERA = ("Handheld footage from {cam}, high vantage looking up a steep snowy slope where the avalanche is descending "
          "into the buildings just below it; the slope and the avalanche fill the upper half of the frame, the nearest "
          "buildings and a corner of the railing fill the lower half; slight hand shake, the camera stays fixed, "
          "tilting slightly and never descending; one continuous shot, no zoom, no cuts.")
# 14 Eki (4): "overcast daylight" ortamın ışığıyla çelişmesin diye "raw natural light"
# 21 Eki (genel kalite): giyim satırı kısa + gerçek zaman cümlesi; kamera kaynak metni aynı, ortak
# kurallar (kısaltma, ön plan yüzü yasağı) sk.camera_rules ile son adımda
GUARD = "Civilians in winter clothes, no hazmat suits. " + sk.REAL_TIME
ROOF = {"A3", "A6", "B2", "B3", "D3", "E6"}  # (*) sadece köy kenarı terasında (14 Eki (3): + B2 balkon)
DECK = {"C3"}                               # (‡) teras noktalarında seçilmez, sadece balkonda (14 Eki (3))
LIFTB = set()                               # (†) 14 Eki (3): teleferik maddesi kalmadı (kural test_pool_lint'te)


def cap(s):
    return s[0].upper() + s[1:]


KEY = {
    # 14 Eki (4), Bahadır: çığ ilk karede evlerin içinde ("is already ..."). 14 Eki (5): yamaç açıkça anılır
    KOY: "A powder avalanche is already roaring down the steep slope into the first chalets of a village, a wall of snow "
         "bursting over their roofs and through the street.",
    KAYAK: "An avalanche is already roaring down the ski slope into a mountain lodge, snow bursting over its terrace and "
           "walls.",
    ORMAN: "An avalanche is already roaring down through a pine forest into the cabins at its edge, a white cloud rolling "
           "over their roofs.",
}
# 14 Eki (4): ortam havuzu (her üretimde koddan; kategori LRU)
AXES = {"mountain": ("jagged rocky peaks", "wide snowy highlands below a steep slope", "steep forested slopes",
                     "sheer cliffs above a narrow valley"),
        "village": ("dark timber chalets", "red timber houses", "log cabins and a large lodge",
                    "stone-and-timber houses", "tall narrow wooden houses with heavy roofs"),
        "light": ("heavy overcast sky", "falling snow and low cloud", "pale low winter sun",
                  "late-afternoon blue-grey light", "bright cold sunny day")}
STONE = {"B1", "C5", "E3", "E7"}   # 18 Eki (2): E5 -> E7
# En uzun izinli ortam satırı (kelime sınırı testleri en kötü durumla çalışsın)
LONG_SETTING = "Setting: sheer cliffs above a narrow valley, dark timber chalets, falling snow and low cloud."
# Ülke, şehir, bölge, bayrak, yazı sızıntısı: ortam satırında ve promptta hiç geçmemeli ("No readable signs, text or
# flags." stil ekindeki yasak cümlesi hariç)
LEAK = ("swiss", "switzerland", "alps", "alpine", "austria", "tyrol", "norway", "norwegian", "japan", "japanese",
        "canada", "canadian", "colorado", "chamonix", "zermatt", "himalaya", "nepal", "italy", "italian", "france",
        "french", "germany", "bavaria", "sweden", "finland", "iceland", "russia", "usa", "american", "city", "town",
        "flag", "sign", "text", "logo", "banner", "billboard", "letter")
POOLS = {
    KOY: ({"A1": "the snow blast hurls a stack of heavy timber logs into a chalet wall",
           "A2": "the snow blast tears a wooden chalet off its foundation and sweeps it down the slope",
           "A3": "the snow blast rips the roof off a barn and scatters the planks",
           "A4": "the snow wall rams a stone barn and its dark stones burst out in all directions",
           "A5": "the snow wall flattens a long wooden fence and a wooden shed beside the street, the dark boards "
                 "flying",
           "A6": "the snow cloud smashes the balcony off a chalet facade"},
          {"B1": "the snow blast smashes into a stone chalet and its gable wall collapses",
           "B2": "the snow wall tears a wooden balcony and its staircase off a chalet and the dark timbers crash into "
                 "the street",
           "B3": "the snow blast topples a wooden church bell tower across the street",
           "B4": "the snow wall crashes into a hillside retaining wall and the stones tumble out",
           "B5": "the snow blast rips the entire front wall off a long wooden chalet and the dark timber beams fly "
                 "outward",
           "B6": "the snow wall carries a wooden shed off its base and breaks it apart"}),
    KAYAK: ({"C1": "the avalanche slams into the lodge's wooden ski-storage shed and its dark planks burst outward",
             "C2": "the snow wall smashes the lodge's wooden entrance porch and its dark beams collapse",
             "C3": "the avalanche rips the wooden terrace deck off the lodge and the dark planks fly",
             "C4": "the avalanche smashes a wooden snack cabin by the slope and its dark boards scatter",
             "C5": "the avalanche hits a stone service building and its wall bursts apart",
             "C6": "the avalanche shoves a stack of dark timber logs down the slope into the lodge wall"},
            {"D1": "a second surge slams into the lodge and its whole wooden front bursts open, beams and planks "
                   "flying",
             "D2": "the snow wall tears a wooden annex off the lodge and carries it downhill",
             "D3": "the avalanche lifts the lodge's roof deck and tosses it aside",
             "D4": "the snow blast smashes through a wooden ski-rental cabin beside the slope and its dark planks "
                   "scatter",
             "D5": "the avalanche sweeps a wooden ski-rental cabin off its base and breaks its dark planks apart",
             "D6": "the snow surge crashes through the lodge's side wall and dark timber beams burst out"}),
    ORMAN: ({"E1": "the avalanche front hurls snapped pine trunks into a row of wooden cabins",
             "E2": "the avalanche slams a wall of snapped dark pine trunks into a wooden cabin and its side bursts open",
             "E3": "the avalanche rams a stone farmhouse's barn door and the dark planks burst inward",
             "E4": "the snow wall tears a woodshed apart and scatters the logs",
             "E6": "the snow blast peels the roof off a cabin",
             # 18 Eki (2): E5 çıktı, E7 ve F7 yeni (Parti 2)
             "E7": "the avalanche smashes through the front of a stone farmhouse and its roof caves in"},
            {"F1": "a second surge slams into the cabins and their walls burst outward",
             "F2": "the snow blast rips a cabin's wooden porch and front steps off and sends them flying",
             "F4": "the snow blast knocks over a wooden water tower",
             "F5": "the snow cloud blows the front off a barn and the hay bursts out",
             "F6": "the snow wall flattens a long wooden barn and the dark boards scatter",
             "F7": "the avalanche front sweeps a wooden cabin off its base and breaks it apart"}),
}
# 17 Eki, Bahadır (temizlik turu, madde 1): kod yedeğinin kelime sınırına sığmadığı köy çiftleri hariç (yapı kuralı
# dışında; tests/test_story_fallback.py FALLBACK_GAPS_EXCLUDED)
FIT_GAPS = {KOY: {("A2", "B2"), ("A2", "B5"), ("A4", "B2"), ("A4", "B5"), ("A5", "B2"), ("A5", "B5")}}
# Aynı yapı sınıfı (14 Eki (3), zayıf madde temizliği sonrası). Etiketler event_structure yorumlarıyla aynı.
STRUCT = {
    KOY: {"A1": {"facade"}, "A2": {"chalet"}, "A3": {"roof"}, "A4": {"stone"}, "A5": {"shed"}, "A6": {"facade", "balcony"},
          "B1": {"facade", "stone"}, "B2": {"balcony"}, "B3": {"roof"}, "B4": {"stone"}, "B5": {"facade"},
          "B6": {"shed", "chalet"}},
    KAYAK: {"C1": {"hut"}, "C2": {"facade"}, "C3": {"deck"}, "C4": {"hut"}, "C5": {"stone"}, "C6": {"facade"},
            "D1": {"facade"}, "D2": {"hut"}, "D3": {"roof", "deck"}, "D4": {"hut"}, "D5": {"hut"}, "D6": {"facade"}},
    ORMAN: {"E1": {"tree", "wood"}, "E2": {"tree", "wood"}, "E3": {"stonehouse", "barn"}, "E4": {"wood"},
            "E6": {"roof"}, "E7": {"stonehouse"},
            "F1": {"wood"}, "F2": {"wood"}, "F4": {"tower"}, "F5": {"wood", "barn"},   # 17 Eki: F3 çıktı
            "F6": {"wood", "barn"}, "F7": {"wood"}},
}
VALID = {
    "A1": ["The snow blast flings a pile of heavy logs into the wall of a chalet.",
           "A stack of timber logs is hurled into a chalet wall by the snow blast.",
           "The avalanche drives heavy logs straight into the side of a wooden house.",
           "The snow blast sends a stack of thick logs crashing into a chalet.",
           "The snow blast hurls a stack of heavy timber logs into a chalet wall."],
    "A2": ["The snow blast rips a wooden chalet from its foundation and carries it down the slope.",
           "The avalanche tears a chalet off its base and drags it downhill.",
           "A wooden house is lifted off its foundation and swept away by the snow.",
           "The wall of snow shoves a chalet off its footings and rolls it down the mountainside.",
           "The snow blast tears a wooden chalet off its foundation and sweeps it down the slope."],
    "A3": ["The blast tears the roof off a barn and flings the planks across the snow.",
           "The barn's roof is ripped away and its planks scatter in the snow cloud.",
           "The snow blast lifts the roof off a wooden barn and hurls the boards away.",
           "The avalanche strips the roof from a barn, scattering planks everywhere.",
           "The snow blast rips the roof off a barn and scatters the planks."],
    "A4": ["The snow wall slams into a stone barn and its dark stones fly in every direction.",
           "A stone barn bursts apart as the avalanche rams it, stones scattering everywhere.",
           "The avalanche smashes into a stone stable and the masonry explodes outward.",
           "The snow wall crashes into a stone barn, hurling its dark stones across the street.",
           "The snow wall rams a stone barn and its dark stones burst out in all directions."],
    "A5": ["The snow wall knocks down a long wooden fence and a shed by the street, boards flying.",
           "A wooden fence and a shed beside the street are flattened, dark boards scattering.",
           "The avalanche crushes a long fence and a wooden shed, sending the boards flying.",
           "The snow wall levels a wooden shed and the fence beside the street, its planks flying.",
           "The snow wall flattens a long wooden fence and a wooden shed beside the street, the dark boards flying."],
    "A6": ["The snow cloud tears the balcony off a chalet's facade.",
           "A chalet balcony is ripped from the facade by the snow cloud.",
           "The blast smashes a wooden balcony and it breaks away from the chalet.",
           "The snow cloud rips the balcony off the front of a chalet.",
           "The snow cloud smashes the balcony off a chalet facade."],
    "B1": ["The snow blast slams into a stone chalet and its gable wall caves in.",
           "A stone chalet's gable wall collapses as the snow blast hits it.",
           "The avalanche crashes into a stone house and the gable end crumbles.",
           "The snow blast strikes a stone chalet, its gable wall tumbling down.",
           "The snow blast smashes into a stone chalet and its gable wall collapses."],
    "B2": ["The snow wall rips a wooden balcony and its stairs off a chalet, the timbers crashing into the street.",
           "A chalet's balcony and staircase are torn away and the dark timbers fall into the street.",
           "The avalanche wrenches the wooden balcony and staircase from a chalet and hurls the timbers into the street.",
           "The snow wall tears the balcony and its steps off a chalet, dark beams crashing down into the street.",
           "The snow wall tears a wooden balcony and its staircase off a chalet and the dark timbers crash into the street."],
    "B3": ["The snow blast knocks a wooden church bell tower across the street.",
           "A wooden bell tower topples over and crashes across the street.",
           "The church tower collapses in the snow blast and falls into the street.",
           "The blast brings down the wooden belfry across the road.",
           "The snow blast topples a wooden church bell tower across the street."],
    "B4": ["The snow wall slams into a retaining wall on the hillside and its stones tumble out.",
           "A hillside retaining wall gives way under the snow, stones spilling out.",
           "The avalanche smashes a retaining wall and the stones fall into the street.",
           "The retaining wall cracks open and its stones tumble down the slope.",
           "The snow wall crashes into a hillside retaining wall and the stones tumble out."],
    "B5": ["The snow blast tears the whole front wall off a long wooden chalet and dark beams fly outward.",
           "The front of a long wooden chalet is ripped away, its timber beams flying.",
           "The avalanche blows out the facade of a wooden chalet and the dark planks scatter.",
           "A long chalet's wooden front wall bursts outward, beams spinning through the air.",
           "The snow blast rips the entire front wall off a long wooden chalet and the dark timber beams fly outward."],
    "B6": ["The avalanche lifts a wooden shed off its base and smashes it to pieces.",
           "A wooden shed is swept off its foundation and breaks apart in the snow.",
           "The snow wall drags a shed off its base and crushes it.",
           "The snow tears a small shed from its base and it falls apart.",
           "The snow wall carries a wooden shed off its base and breaks it apart."],
    "C1": ["The avalanche crashes into the lodge's wooden ski-storage shed and its planks burst outward.",
           "The lodge's ski-storage shed bursts open as the avalanche hits, dark planks flying.",
           "The snow slams into a wooden storage shed by the lodge and its boards explode outward.",
           "The avalanche smashes the wooden ski shed beside the lodge, sending dark planks flying.",
           "The avalanche slams into the lodge's wooden ski-storage shed and its dark planks burst outward."],
    "C2": ["The snow wall crushes the lodge's wooden entrance porch and its dark beams cave in.",
           "The lodge's wooden porch collapses as the snow wall smashes into it.",
           "The avalanche tears the wooden porch off the lodge entrance and its beams break.",
           "The snow wall smashes the entrance porch of the lodge and its beams give way.",
           "The snow wall smashes the lodge's wooden entrance porch and its dark beams collapse."],
    "C3": ["The avalanche tears the wooden terrace deck from the lodge, sending dark planks flying.",
           "The lodge's terrace deck is ripped away and its planks scatter across the snow.",
           "The snow wrenches the wooden deck off the lodge and the dark boards fly.",
           "The avalanche lifts the lodge's wooden deck and flings the planks downhill.",
           "The avalanche rips the wooden terrace deck off the lodge and the dark planks fly."],
    "C4": ["The avalanche crushes a wooden snack cabin by the slope and its boards scatter.",
           "A wooden snack hut beside the slope bursts apart as the avalanche hits it.",
           "The snow smashes into a wooden snack bar and sends its dark boards flying.",
           "The avalanche slams into a wooden kiosk by the slope, its boards scattering.",
           "The avalanche smashes a wooden snack cabin by the slope and its dark boards scatter."],
    "C5": ["The avalanche slams into a stone service building and its wall bursts apart.",
           "A stone service building's wall collapses as the avalanche hits it.",
           "The snow crashes into a stone building and its wall breaks open.",
           "The avalanche smashes a stone outbuilding and its masonry explodes outward.",
           "The avalanche hits a stone service building and its wall bursts apart."],
    "C6": ["The avalanche pushes a stack of dark logs down the slope into the lodge wall.",
           "A pile of timber logs is swept down the slope and slams into the lodge.",
           "The snow wall drives a woodpile down the slope and rams it into the side of the lodge.",
           "The avalanche hurls a stack of logs down into the wall of the lodge building.",
           "The avalanche shoves a stack of dark timber logs down the slope into the lodge wall."],
    "D1": ["A second surge hits the lodge and its whole wooden front bursts open, planks flying.",
           "Another wave slams into the lodge, blowing out its wooden facade in a spray of beams.",
           "The lodge's wooden front wall caves in and beams and boards scatter.",
           "A second surge smashes the front of the lodge open and timber flies everywhere.",
           "A second surge slams into the lodge and its whole wooden front bursts open, beams and planks flying."],
    "D2": ["The snow wall rips a wooden annex off the lodge and carries it downhill.",
           "The avalanche tears the lodge's wooden extension away and sweeps it down the slope.",
           "A wooden annex is torn from the lodge and dragged downhill by the snow.",
           "The snow wall shoves the lodge's wooden wing off and carries it away.",
           "The snow wall tears a wooden annex off the lodge and carries it downhill."],
    "D3": ["The avalanche lifts the roof deck of the lodge and tosses it aside.",
           "The lodge's roof deck is ripped up and flung aside by the snow.",
           "The snow blast tears off the lodge roof and throws it away.",
           "The avalanche peels the lodge's roof deck up and hurls it to the side.",
           "The avalanche lifts the lodge's roof deck and tosses it aside."],
    "D4": ["The snow blast smashes a wooden ski-rental cabin and its dark planks fly.",
           "A ski-rental hut beside the slope bursts apart and its boards scatter.",
           "The avalanche crushes the wooden rental cabin, sending planks flying.",
           "The snow blast shatters a wooden cabin by the slope and the planks scatter across the snow.",
           "The snow blast smashes through a wooden ski-rental cabin beside the slope and its dark planks scatter."],
    "D5": ["The avalanche rips a wooden ski-rental cabin off its base and smashes its planks apart.",
           "A ski-rental cabin is swept off its base and breaks apart in the snow.",
           "The snow carries a wooden rental hut off its footings and its dark planks break apart.",
           "The avalanche pushes a ski-rental cabin off its base and it falls apart.",
           "The avalanche sweeps a wooden ski-rental cabin off its base and breaks its dark planks apart."],
    "D6": ["The snow surge smashes through the lodge's side wall and dark beams burst out.",
           "The lodge's side wall caves in under the snow surge, timber beams flying out.",
           "The surge crashes through the side of the lodge and its timber beams explode outward.",
           "A snow surge breaks through the lodge's side wall, sending dark beams flying.",
           "The snow surge crashes through the lodge's side wall and dark timber beams burst out."],
    "E1": ["The avalanche hurls snapped pine trunks into a row of wooden cabins.",
           "Broken pine trunks are flung into the wooden cabins by the avalanche front.",
           "The avalanche drives snapped trees into a row of cabins.",
           "The snow front throws broken trunks into the wooden huts.",
           "The avalanche front hurls snapped pine trunks into a row of wooden cabins."],
    "E2": ["The avalanche drives a mass of snapped pine trunks into a wooden cabin and its side bursts open.",
           "A wall of broken dark pine trunks slams into a wooden cabin, blowing its side open.",
           "The avalanche rams snapped pine trunks into a cabin and its wall caves in.",
           "Snapped pine trunks smash into a wooden cabin and its side splits open.",
           "The avalanche slams a wall of snapped dark pine trunks into a wooden cabin and its side bursts open."],
    "E3": ["The avalanche slams into a stone farmhouse's barn door and the planks burst inward.",
           "A farmhouse barn door bursts inward as the avalanche rams it.",
           "The snow crashes into the barn door of a stone farmhouse and its dark planks cave in.",
           "The avalanche smashes the wooden barn door of a farmhouse and the planks break inward.",
           "The avalanche rams a stone farmhouse's barn door and the dark planks burst inward."],
    "E4": ["The snow wall rips a woodshed open and scatters the logs.",
           "A woodshed bursts open in the snow and its logs fly everywhere.",
           "The avalanche smashes a woodshed and flings the firewood across the snow.",
           "The snow wall breaks a woodshed apart and scatters the logs.",
           "The snow wall tears a woodshed apart and scatters the logs."],
    "E6": ["The snow blast tears the roof off a cabin.",
           "A cabin's roof is ripped away by the snow blast.",
           "The avalanche lifts the roof off a wooden cabin and flings it away.",
           "The snow blast strips the roof from a small cabin.",
           "The snow blast peels the roof off a cabin."],
    # 18 Eki (2): Parti 2
    "E7": ["The avalanche smashes through the front of a stone farmhouse and its roof caves in.",
           "The snow wall crashes into a stone farmhouse, bursting its front open as the roof collapses.",
           "The avalanche rams the stone farmhouse, its front wall breaking and the roof caving in.",
           "A stone farmhouse is hit by the avalanche and its roof falls in.",
           "The snow blast slams into the farmhouse and its stone front shatters."],
    "F7": ["The avalanche front sweeps a wooden cabin off its base and breaks it apart.",
           "A wooden cabin is swept off its base by the avalanche and smashed apart.",
           "The snow wall carries a cabin off its foundation and tears it to pieces.",
           "The avalanche shoves the wooden cabin off its base and it breaks apart.",
           "The snow blast sweeps a cabin away and it collapses into dark planks."],
    "F1": ["Another surge hits the cabins and their walls burst outward.",
           "The second wave smashes into the wooden cabins and their walls cave in.",
           "A second surge strikes the cabins, blowing their walls out.",
           "The cabins' walls shatter as a second wave of snow hits them.",
           "A second surge slams into the cabins and their walls burst outward."],
    "F2": ["The snow blast tears a cabin's wooden porch and front steps off and flings them away.",
           "A cabin's porch and steps are ripped off and sent flying by the snow blast.",
           "The snow blast wrenches the wooden porch and stairs off a cabin, hurling them through the air.",
           "The avalanche strips the porch and front steps from a cabin and sends them flying.",
           "The snow blast rips a cabin's wooden porch and front steps off and sends them flying."],
    "F4": ["The snow blast knocks down a wooden water tower.",
           "A wooden water tower topples over in the snow blast.",
           "The avalanche brings down a water tower, which crashes into the snow.",
           "The blast knocks over a tall wooden water tank.",
           "The snow blast knocks over a wooden water tower."],
    "F5": ["The snow cloud rips the front off a barn and hay bursts out.",
           "A barn's front wall is torn away and the hay inside bursts out.",
           "The snow blast blows the barn's front open and straw explodes outward.",
           "The front of a barn bursts open and bales of hay spill into the snow.",
           "The snow cloud blows the front off a barn and the hay bursts out."],
    "F6": ["The snow wall knocks down a long wooden barn and its dark boards scatter.",
           "A long wooden barn is flattened by the snow wall, boards flying everywhere.",
           "The snow wall crushes a long barn and the dark planks scatter across the snow.",
           "The avalanche levels a wooden barn and sends its boards flying.",
           "The snow wall flattens a long wooden barn and the dark boards scatter."],
}
# 14 Eki 01:30 köy testi (A4+B5, balkon) 3 denemede reddedildi. GPT'nin gerçek cümleleri; madde kapısından geçmeli.
FIXTURES = {
    "A4": ["The raging snow mass crashes into a sturdy stone barn, sending its dark stones ricocheting violently across "
           "the snowy landscape.",
           "The avalanche crashes into a stone barn, sending dark stones exploding outward across the snowy street.",
           "The avalanche collides with a stone barn, dark stones bursting and scattering across the snowy expanse."],
    "B5": ["The force of the snow rips away a chalet's front wall, launching timber beams through the air.",
           "The snow's force tears away a chalet's front wall, sending timber beams and debris flying outward "
           "relentlessly."],
}
for _b, _l in FIXTURES.items():
    VALID[_b] = VALID[_b] + _l
# 14 Eki (2) tarama: deneme 1'deki kalıp ("crashes into X, sending Y flying") her maddede geçmeli. A3, A6, D3, E6
# reddediliyordu; uçma fiilleri eklendi. A4 ve B5 fixture'ları yukarıda.
IMPACT = {
 "A1": "The snow blast crashes into a stack of logs, sending them slamming into a chalet wall.",
 "A2": "The avalanche slams into a wooden chalet, ripping it off its foundation and carrying it downhill.",
 "A3": "The snow blast hits a barn, sending its roof and planks flying across the street.",
 "A5": "The snow wall crashes into a wooden fence and a shed, sending the boards flying.",
 "A6": "The avalanche slams into a chalet, sending its balcony crashing off the facade.",
 "B1": "The snow blast crashes into a stone chalet, its gable wall collapsing.",
 "B2": "The snow wall crashes into a chalet, sending its balcony and staircase flying into the street.",
 "B3": "The snow blast crashes into the church bell tower, sending it toppling across the street.",
 "B4": "The avalanche collides with a hillside retaining wall, sending its stones tumbling into the street.",
 "B6": "The snow mass slams into a wooden shed, sending it sliding off its base and breaking apart.",
 "C1": "The avalanche crashes into the lodge's ski-storage shed, sending its planks flying.",
 "C2": "The snow wall crashes into the lodge's entrance porch, its beams collapsing.",
 "C3": "The avalanche crashes into the lodge terrace, sending the deck planks flying.",
 "C4": "The avalanche crashes into a snack cabin, sending its boards scattering.",
 "C5": "The avalanche crashes into a stone service building, its wall bursting apart.",
 "C6": "The snow mass sends a stack of dark logs crashing down the slope into the lodge wall.",
 "D1": "A second surge crashes into the lodge, its wooden front exploding open with beams and planks flying.",
 "D2": "The snow mass slams into the lodge's wooden annex, ripping it away and carrying it downhill.",
 "D3": "The avalanche crashes over the lodge, sending its roof deck flying aside.",
 "D4": "The snow blast crashes into a wooden ski-rental cabin, sending its dark planks scattering across the snow.",
 "D5": "The avalanche crashes into a ski-rental cabin, sweeping it off its base as it breaks apart.",
 "D6": "The snow surge crashes into the lodge, sending its side wall beams bursting out.",
 "E1": "The avalanche sends snapped pine trunks crashing into a row of wooden cabins.",
 "E2": "The avalanche sends snapped pine trunks crashing into a wooden cabin, its side bursting open.",
 "E3": "The avalanche crashes into a farmhouse barn door, sending the planks bursting inward.",
 "E4": "The snow wall crashes into a woodshed, sending the logs scattering in all directions.",
 "E6": "The snow blast crashes into a cabin, sending its roof flying off.",
 "F1": "A second surge crashes into the cabins, their walls bursting outward.",
 "F2": "The snow blast crashes into a cabin, sending its porch and front steps flying.",
 "F4": "The snow blast slams into a wooden water tower, sending it crashing down.",
 "F5": "The snow cloud crashes into a barn, its front bursting open as hay explodes out.",
 "F6": "The snow wall crashes into a long wooden barn, sending its boards scattering.",
 "E7": "The avalanche crashes into a stone farmhouse, sending its front wall bursting and the roof caving in.",
 "F7": "The avalanche front crashes into a wooden cabin, sending it sliding off its base in pieces.",
}
for _b, _t in IMPACT.items():
    VALID[_b] = VALID[_b] + [_t]
# Sadece atmosfer (kar tozu, gökyüzü, uzaktan çığ): hiçbir maddeden geçmemeli
ATMOSPHERE = ["Snow dust drifts over the valley below the mountain.",
              "The avalanche roars down the slope under a grey sky.",
              "A white cloud rises high above the mountainside.",
              "Snow keeps falling over the quiet village.",
              "The mountain disappears behind a wall of white powder.",
              "A cloud of snow spreads across the sky above the valley."]


# 14 Eki (3): bütçeyi aşan maddelerin kısa hâlleri. GPT WORD BUDGET'a uyunca bunları kısaltır; sahte GPT ve build()
# birebir metin toplamı aşınca bu kısa hâlleri yazar (gerçek akışta GPT'nin kapı geri bildirimiyle yaptığı). 14 Eki (5):
# toplam 70, köy kilit cümlesi 29 kelime: köyde 4-9s ve 9-15s en fazla 15 kelime.
SHORT = {"A2": "The blast tears a wooden chalet off its foundation, sweeping it downhill",
         "A4": "The snow wall rams a stone barn and its dark stones burst out",
         "A5": "The snow wall flattens a wooden fence and shed, boards flying",
         "B2": "The snow wall tears a balcony and staircase off a chalet, timbers crashing down",
         "B5": "The snow blast rips the front wall off a wooden chalet, dark beams flying",
         "E2": "The avalanche slams snapped dark pine trunks into a wooden cabin and its side bursts open"}
for _b, _t in SHORT.items():   # kısa hâller de madde kapısından geçmeli
    VALID[_b] = VALID[_b] + [_t + "."]


def _short_slice(bid, text):
    return SHORT[bid] if bid in SHORT else text


def ava_gpt(messages=None):
    """Ağsız sahte GPT: seçilen maddeleri birebir dilim yapar (kod seçimi; ücretli çağrı yok). Ret geri bildirimi
    gelirse uzun maddeleri kısa yazar (SHORT)."""
    async def gpt(system, user, **kw):
        if messages is not None:
            messages.append(user)
        line = dict(l.split(": ", 1) for l in user.splitlines()
                    if l.startswith(("4-9s EVENT", "9-15s EVENT", "PEOPLE RUNNING AWAY")))
        word = line["PEOPLE RUNNING AWAY"].split()[0]
        away = line["PEOPLE RUNNING AWAY"].split("run away from ")[1].split(",")[0]
        s2, s3 = cap(line["4-9s EVENT"]), cap(line["9-15s EVENT"])
        if "REJECTED" in user:
            inv = {cap(es.beat_text(e, sl, b)): b for e in AVA for sl in ("slice_2", "slice_3")
                   for b in es.EVENT_BEATS[e][sl]}
            s2, s3 = _short_slice(inv.get(s2), s2), _short_slice(inv.get(s3), s3)
        s2 += " as the snow roars" if len(s2.split()) < 10 else ""
        s3 += " as the snow roars" if len(s3.split()) < 10 else ""
        return {"slice_1_rest": f"{cap(word)} people run from {away} right below.",   # 22 Eki: korkuluk yok
                "slice_2": s2 + ".", "slice_3": s3 + "."}
    return gpt


def build(e, b2, b3, spot=HT, people=5, setting=LONG_SETTING):
    spec = es.build_spec(e, None, spot, None, b2, b3, None, people, setting)
    s2, s3 = cap(es.beat_text(e, "slice_2", b2)), cap(es.beat_text(e, "slice_3", b3))
    s2 += " as the snow roars" if len(s2.split()) < 10 else ""
    s3 += " as the snow roars" if len(s3.split()) < 10 else ""
    sl = {"slice_1_rest": es.clean_slice(f"{cap(es.NUMBER_WORDS[people])} people run from the avalanche right "
                                         f"below."),   # 22 Eki: korkuluk yok
          "slice_2": es.clean_slice(s2), "slice_3": es.clean_slice(s3)}
    if len(es.plain_story(spec, sl).split()) > 70:   # GPT bütçeye uyar: uzun maddeler kısa yazılır
        sl.update(slice_2=es.clean_slice(_short_slice(b2, s2)), slice_3=es.clean_slice(_short_slice(b3, s3)))
    return spec, sl


def codes(spec, sl):
    return {i["rule"] for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl))}


def beats():
    for e in AVA:
        for slot in ("slice_2", "slice_3"):
            for bid, beat in es.EVENT_BEATS[e][slot].items():
                yield e, slot, bid, beat


class TestAvalanche(unittest.TestCase):
    def setUp(self):
        es._BEAT_MEMORY.clear()

    def test_category_menu_and_registrations(self):
        import bot
        import core.creative_pipeline as cp
        from core.creative_engine import DOMAIN_ATTRIBUTES, ENV_CENTRIC_DOMAINS, MARITIME_INSPIRATION_DOMAINS
        self.assertEqual(bot.DOMAIN_LABELS["avalanche_disasters"], "❄️ Çığ")
        self.assertIn('avalanche_disasters: "❄️ Çığ",', open(os.path.join(ROOT, "dashboard.html"), encoding="utf-8").read())
        self.assertEqual({e: bot.EVENT_LABELS[e] for e in AVA},
                         {KOY: "🏔️ Çığ köyü yutuyor", KAYAK: "⛷️ Çığ kayak merkezine iniyor",
                          ORMAN: "🌲 Çığ ormandan vadiye iniyor"})
        self.assertEqual(es.AVALANCHE_EVENTS, AVA)
        self.assertEqual(sk.skeleton_events("avalanche_disasters"), list(AVA))
        self.assertEqual(DOMAIN_ATTRIBUTES["avalanche_disasters"]["environments"], [HT, BAL, LIFT])
        self.assertEqual(DOMAIN_ATTRIBUTES["avalanche_disasters"]["ships"], [])
        self.assertIn("avalanche_disasters", MARITIME_INSPIRATION_DOMAINS)
        self.assertIn("avalanche_disasters", ENV_CENTRIC_DOMAINS)
        self.assertIn("avalanche_disasters", sk.NO_SIGNS_DOMAINS)
        self.assertEqual(sk.PHENOMENA["Çığ"], list(AVA))
        for e in AVA:
            with self.subTest(event=e):
                self.assertTrue(es.is_structured(e))
                self.assertLessEqual(len(bot.EVENT_LABELS[e]), 40)
                self.assertEqual(cp.EVENT_REQUIRED[e], [])
                self.assertIn(e, cp.EVENT_OUTCOMES)
                self.assertEqual(sk.count_range(e, None), (3, 6))
                self.assertEqual(es.TOTAL_WORDS_BY_EVENT[e], (40, 70))   # 14 Eki (5), Bahadır kararı
                self.assertFalse(es.uses_vehicle(e))
                self.assertNotIn(e, es.EVENT_VEHICLES)
                self.assertEqual(es.structure_views(e), [None])
                self.assertIn(e, es.WORD_CAP_EVENTS)
                self.assertNotIn(e, es.NO_RAIN_EVENTS)
        # Telegram: çığ düğmesi görünür, 3 olay seçilebilir
        texts = [b.text for row in bot.domain_keyboard().inline_keyboard for b in row]
        self.assertIn("❄️ Çığ", texts)
        ev = [b.text for row in bot.event_keyboard(bot.DOMAIN_KEYS.index("avalanche_disasters")).inline_keyboard
              for b in row]
        for label in ("🏔️ Çığ köyü yutuyor", "⛷️ Çığ kayak merkezine iniyor", "🌲 Çığ ormandan vadiye iniyor"):
            self.assertIn(label, ev)

    def test_key_visuals_and_pools_locked(self):
        import core.creative_pipeline as cp
        for e in AVA:
            with self.subTest(event=e):
                self.assertEqual(es.EVENT_KEY_VISUAL[e], KEY[e])
                found = {i["rule"] for i in cp.story_rule_issues(e, None, KEY[e])}
                self.assertFalse(found & {"a_trigger_first", "b_no_camera_words", "required"})
                self.assertIn(" is already ", KEY[e])   # 14 Eki (4): çığ ilk karede çarpıyor
                self.assertNotIn("right below the railing", KEY[e])
                self.assertNotIn("thunders down", KEY[e])
                self.assertIn("roaring down", KEY[e])   # 14 Eki (5): yamaç açıkça
                # 14 Eki (2): olay adı kapısı kilit cümlenin kendisiyle geçer (GPT ipucu yok)
                self.assertNotIn("e_event_and_ship_named", found)
                b = es.EVENT_BEATS[e]
                self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, POOLS[e][0])
                self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, POOLS[e][1])
                self.assertEqual(b["excluded_views"], {})

    def test_cameras_and_style_suffix(self):
        from core.trace_format import count_constraints
        self.assertEqual(sk.AVALANCHE_WEATHER, ["overcast winter daylight over snowy mountains"])
        spots = {KOY: [HT, BAL], KAYAK: [HT, BAL, LIFT], ORMAN: [HT, BAL]}
        for e in AVA:
            s = sk.EVENT_SKELETONS[e]
            self.assertIs(s["weather"], sk.AVALANCHE_WEATHER)
            self.assertEqual(list(s["spots"]), spots[e])
            for spot in spots[e]:
                suffix = sk.style_suffix(e, None, spot)
                with self.subTest(event=e, spot=spot):
                    self.assertEqual(sk.CAMERA_SPOTS[spot], CAMS[spot])
                    self.assertEqual(suffix, f"{sk.camera_rules(CAMERA.format(cam=CAMS[spot]))} {GUARD} No readable "
                                             f"signs, text or flags.")
                    self.assertNotIn("pans to follow", suffix)
                    self.assertNotIn("follow", suffix)
                    self.assertNotIn("across the valley", suffix)
                    self.assertNotIn("upper part of the frame", suffix)
                    self.assertIn("never descending", suffix)
                    # 14 Eki (2): stil eki ≤ 95 kelime; 75 kelimelik hikâye + 3 etiket + stil eki ≤ 175
                    # 14 Eki (5): yamaçlı şablonla stil eki en fazla 102 kelime; 70 kelimelik hikâye + 3 etiket ≤ 175
                    self.assertLessEqual(70 + 3 + len(suffix.split()), 175)
                    self.assertLessEqual(count_constraints(suffix)[0], 8)
        # volkan ve diğer kategorilerin kamera satırı çığdan bağımsız (18 Eki: patlama/bombalar kısa şablon, kül bulutu
        # eski şablon)
        # 21 Eki (genel kalite): ortak kamera kısaltmaları ("filmed", "high vantage over", "toward the volcano")
        self.assertTrue(sk.style_suffix(es.PYROCLASTIC, None, "Hillside terrace facing the erupting volcano")
                        .startswith("Handheld footage filmed on a hillside terrace above the village, "
                                    "high vantage over the village street toward the volcano;"))
        self.assertTrue(sk.style_suffix(es.ERUPTION, None, "Hillside terrace facing the erupting volcano")
                        .startswith("Handheld footage filmed on a hillside terrace above the village, "
                                    "high vantage over the village street toward the volcano;"))
        self.assertIn("the camera pans to follow the", sk.style_suffix(es.MUDSLIDE, None, list(
            sk.EVENT_SKELETONS[es.MUDSLIDE]["spots"])[0]))

    def test_term_lists_avalanche_only(self):
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(es))
        node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(getattr(t, "id", None) == "EVENT_BEATS" for t in n.targets))
        seen = 0
        for k, v in zip(node.keys, node.values):
            if getattr(k, "id", None) in ("AVALANCHE_VILLAGE", "AVALANCHE_SKI", "AVALANCHE_FOREST"):
                seen += 1
                names = {n.id for n in ast.walk(v) if isinstance(n, ast.Name)}
                self.assertTrue(names and all(n.startswith("_AVA_") for n in names), names)
        self.assertEqual(seen, 3)

    def test_every_beat_alone_and_five_natural_sentences(self):
        self.assertEqual(set(VALID), {bid for _, _, bid, _ in beats()})
        z6 = {"annihilate", "splinter", "obliterate", "demolish", "wreck", "wreak", "rupture", "pulverize",
              "tear apart", "tears apart", "tore apart", "torn apart", "blow apart", "blows apart", "blew apart",
              "blown apart"}
        for e, slot, bid, beat in beats():
            text = es.clean_slice(cap(es.beat_text(e, slot, bid)))
            with self.subTest(beat=bid):
                self.assertEqual(es.missing_term_groups(beat["terms"], text), [])
                self.assertGreaterEqual(len(VALID[bid]), 5)
                for s in VALID[bid]:
                    self.assertEqual(es.missing_term_groups(beat["terms"], s), [], s)
                    for code, terms, *_ in es.EVENT_BANNED_WORDS[e]:
                        self.assertEqual(es.find_terms(terms, s), [], s)
                for a in ATMOSPHERE:
                    self.assertTrue(es.missing_term_groups(beat["terms"], a), a)
                others = [o for o, ob in es.EVENT_BEATS[e][slot].items()
                          if o != bid and es.missing_term_groups(ob["terms"], text)]
                self.assertTrue(others, bid)
                self.assertNotIn("{vehicle}", beat["text"])
                self.assertFalse({w for g in beat["terms"] for w in g} & z6)

    def test_banned_and_slow_words_gate(self):
        spec, sl = build(KOY, "A1", "B2")
        self.assertFalse(codes(spec, sl) & {"avalanche_banned", "avalanche_no_slow"})
        for w in ("rescue", "helicopter", "skier", "snowmobile", "vehicle", "truck", "car", "cargo", "tugboat",
                  "ship", "boat", "siren", "text", "sign", "logo"):
            with self.subTest(word=w):
                bad = es.clean_slice(f"The snow wall buries a whole row of houses and a {w} up to their roofs")
                self.assertIn("avalanche_banned", codes(spec, {**sl, "slice_3": bad}))
        for w in ("slowly", "gently", "calmly", "gradually", "softly"):
            with self.subTest(word=w):
                bad = es.clean_slice(f"The snow wall {w} buries a whole row of houses up to their roofs")
                self.assertIn("avalanche_no_slow", codes(spec, {**sl, "slice_3": bad}))
        self.assertIn("avalanche_no_slow", codes(spec, {**sl, "slice_1_rest": "Five calm people run from the avalanche."}))
        # "carries", "signal"/"cartwheel" gibi kelimeler yasak sayılmaz; volkanda bu kapı yok
        self.assertEqual(es.find_terms(es._AVA_BANNED, "The avalanche carries the cabin, a cartwheel spins."), [])
        self.assertNotIn(es.ERUPTION, es.EVENT_BANNED_WORDS)
        self.assertEqual(set(es.EVENT_BANNED_WORDS), set(AVA) | set(es.EARTHQUAKE_EVENTS))   # 14 Eki: + deprem

    def test_failed_village_run_fixtures(self):
        # 14 Eki 01:30: A4 deneme 1 "crashes into ... ricocheting" reddedilmişti; şimdi hepsi geçer
        for bid, slot in (("A4", "slice_2"), ("B5", "slice_3")):
            for t in FIXTURES[bid]:
                with self.subTest(text=t):
                    self.assertEqual(es.missing_term_groups(es.EVENT_BEATS[KOY][slot][bid]["terms"], t), [])
                    for code, terms, *_ in es.EVENT_BANNED_WORDS[KOY]:
                        self.assertEqual(es.find_terms(terms, t), [])
        # Fixture'larla kurulan tam hikâye bütçe içinde son denetimden geçer
        spec = es.build_spec(KOY, None, BAL, None, "A4", "B5", None, 5)
        # 14 Eki (5): toplam 70; kısa insan cümlesiyle (WORD BUDGET 0-4s 6-10) fixture'lar sığar
        sl = {"slice_1_rest": es.clean_slice("Five villagers flee in the street right below"),
              "slice_2": es.clean_slice(FIXTURES["A4"][2]), "slice_3": es.clean_slice(FIXTURES["B5"][0])}
        self.assertEqual(es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl), es.assemble_story(spec, sl)), [])
        self.assertLessEqual(len(es.assemble_prompt(spec, sl).split()), 175)

    def test_word_budget_line(self):
        # 14 Eki (2): GPT'ye dilim bütçesi; çığ dışında satır yok
        import core.creative_pipeline as cp
        for e in AVA:
            spot = sk.view_spots(e, None)[0]
            spec = es.build_spec(e, None, spot, None, *sorted(es.allowed_pairs(e, None, spot))[0], None, 5)
            line = es.word_budget_line(spec)
            k = len(KEY[e].split())
            s23 = min(18, (70 - k - 10) // 2)   # 14 Eki (5): 0-4s 10, kalan eşit
            with self.subTest(event=e):
                self.assertEqual(line, f"WORD BUDGET: the opening sentence has {k} words; slice_1_rest 6 to 10 words, "
                                       f"slice_2 10 to {s23} words, slice_3 10 to {s23} words; the opening plus the "
                                       f"three fields must total at most 70 words.\n")
                self.assertLessEqual(k + 10 + 2 * s23, 70)
                self.assertGreaterEqual(s23, 10)
                self.assertIn(line, cp._slices_message(spec, "p", "w", 3, 6, [], None))
        self.assertEqual(es.word_budget_line({"event": es.ERUPTION, "key_visual": "x"}), "")

    def test_people_close_to_camera(self):
        # 14 Eki: 0-4s insan cümlesi kameraya yakın yeri söyler; "camera" kelimesi yine yasak (b kuralı)
        import core.creative_pipeline as cp
        spec, sl = build(KOY, "A1", "B2")
        self.assertEqual(codes(spec, sl) & {"slice_near_camera", "b_no_camera_words"}, set())
        self.assertIn("in the street right below, in the lower half of the frame", es.people_line(spec))   # 22 Eki
        self.assertNotIn("village street", es.people_line(spec))
        self.assertIn("in the street right below", es.people_line(build(KAYAK, "C2", "D2")[0]))
        # 22 Eki (genel kalite devam): yakınlık aşağıdaki sokak / karenin alt yarısı; sadece korkuluk / teras / balkon
        # yanını söyleyen cümle artık yakın sayılmaz (aşağıda "railing_only")
        ok = ["Five people run from the avalanche in the street right below.",
              "Five residents run from the avalanche just below the terrace.",
              "Five villagers run from the avalanche in the village street below the balcony.",
              "Five guests run from the avalanche in the lower half of the frame.",
              "Five guests run from the avalanche just beneath the balcony, screaming."]
        for t in ("Five villagers run from the avalanche near the railing.",
                  "Five people run from the avalanche along the railing of the terrace.",
                  "Five guests run from the avalanche beneath the balcony, screaming."):
            with self.subTest(railing_only=t):
                self.assertIn("slice_near_camera", {i["rule"] for i in es.slice_issues(spec, {**sl, "slice_1_rest": t})})
        for t in ok:
            with self.subTest(text=t):
                self.assertFalse(codes(spec, {**sl, "slice_1_rest": t}) & {"slice_near_camera", "b_no_camera_words"})
        for t in ("Five villagers run from the avalanche down the street.",
                  "Five people run from the avalanche across the village."):
            with self.subTest(text=t):
                self.assertIn("slice_near_camera", {i["rule"] for i in es.slice_issues(spec, {**sl, "slice_1_rest": t})})
        bad = "Five villagers run from the avalanche close to the camera."
        self.assertIn("b_no_camera_words", codes(spec, {**sl, "slice_1_rest": bad}))
        self.assertIn("b_no_camera_words", {i["rule"] for i in cp.structured_issues(spec, {**sl, "slice_1_rest": bad}, [])})
        # volkan insan kuralı değişmedi
        self.assertNotIn("slice_near_camera", {r["rule"] for r in es.SLICE_RULES[es.ERUPTION]})

    def test_forbidden_pairs_follow_same_structure_rule(self):
        for e, tags in STRUCT.items():
            b = es.EVENT_BEATS[e]
            self.assertEqual(set(tags), set(b["slice_2"]) | set(b["slice_3"]))
            with self.subTest(event=e):
                self.assertEqual(b["excluded_pairs"], {(v, d) for v in b["slice_2"] for d in b["slice_3"]
                                                      if tags[v] & tags[d]} | FIT_GAPS.get(e, set()))
        self.assertEqual(es.EVENT_BEATS[KOY]["excluded_pairs"],
                         {("A1", "B1"), ("A1", "B5"), ("A2", "B6"), ("A3", "B3"), ("A4", "B1"), ("A4", "B4"),
                          ("A5", "B6"), ("A6", "B1"), ("A6", "B2"), ("A6", "B5")} | FIT_GAPS[KOY])
        self.assertEqual(es.EVENT_BEATS[KAYAK]["excluded_pairs"],
                         {("C1", "D2"), ("C1", "D4"), ("C1", "D5"), ("C2", "D1"), ("C2", "D6"), ("C3", "D3"),
                          ("C4", "D2"), ("C4", "D4"), ("C4", "D5"), ("C6", "D1"), ("C6", "D6")})
        self.assertEqual(len(es.EVENT_BEATS[ORMAN]["excluded_pairs"]), 17)   # 18 Eki (2): F7 ahşap kabin (E1, E2, E4)

    def test_camera_exclusions(self):
        # çatı/baca (*) sadece yamaç terasında; teleferik (†) istasyon terasında yok
        for e in AVA:
            b = es.EVENT_BEATS[e]
            for bid in list(b["slice_2"]) + list(b["slice_3"]):
                spots = set(sk.view_spots(e, None)) - b["excluded_spots"].get(bid, set())
                with self.subTest(beat=bid):
                    if bid in ROOF:
                        self.assertEqual(spots, {HT})
                    elif bid in DECK:
                        self.assertEqual(spots, {BAL})
                    else:
                        self.assertEqual(spots, set(sk.view_spots(e, None)))
        counts = {e: [len(es.allowed_pairs(e, None, s)) for s in sk.view_spots(e, None)] for e in AVA}
        # 17 Eki: köy 6 yeni hariç çift (yedek sığmıyor), orman F3 çıktı
        self.assertEqual(counts, {KOY: [20, 7], KAYAK: [20, 20, 15], ORMAN: [19, 13]})   # 18 Eki (2): E7, F7

    def test_block_depth_never_runs_out(self):
        # 14 Eki (3): zayıf madde temizliğinden sonra köy 2, kayak 2, orman 1 (yasak çiftler arttı; her noktada en
        # kötü durumda en az bir aday kalan en büyük derinlik)
        self.assertEqual(es.RECENT_BEAT_BLOCK, 3)
        self.assertEqual({e: es.RECENT_BEAT_BLOCK_BY_EVENT[e] for e in AVA}, {KOY: 2, KAYAK: 2, ORMAN: 1})

        def worst(e, spot, k):
            b, ps = es.EVENT_BEATS[e], es.allowed_pairs(e, None, spot)
            return min(sum(1 for v, d in ps if v not in x2 and d not in x3)
                       for x2 in map(set, combinations(b["slice_2"], k))
                       for x3 in map(set, combinations(b["slice_3"], k)))
        for e in AVA:
            # 17 Eki: köyde 6 yeni hariç çift; balkonda 2 derinlik de adayı bitirebilir, aday kalmazsa 1'e düşer
            k = 1 if e in es.BEAT_BLOCK_FALLBACK_EVENTS else es.RECENT_BEAT_BLOCK_BY_EVENT[e]
            for spot in sk.view_spots(e, None):
                with self.subTest(event=e, spot=spot):
                    self.assertGreater(worst(e, spot, k), 0)
        self.assertIn(KOY, es.BEAT_BLOCK_FALLBACK_EVENTS)
        self.assertEqual(worst(KOY, BAL, 2), 0)       # 17 Eki: 1'e düşmenin sebebi
        self.assertEqual(worst(KOY, BAL, 3), 0)       # düşürmenin sebepleri
        self.assertEqual(worst(KAYAK, LIFT, 3), 0)
        self.assertEqual(worst(ORMAN, BAL, 2), 0)

    def test_all_combinations_pass_final_check(self):
        n = 0
        for e in AVA:
            for spot in sk.view_spots(e, None):
                for b2, b3 in es.allowed_pairs(e, None, spot):
                    spec, sl = build(e, b2, b3, spot, people=3 + n % 4)
                    issues = es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl), es.assemble_story(spec, sl))
                    if issues:
                        self.fail(f"{e}/{spot}/{b2}+{b3}: {issues}")
                    n += 1
        self.assertEqual(n, 20 + 7 + 20 + 20 + 15 + 19 + 13)   # 18 Eki (2): orman E5 -> E7, F7 eklendi

    def test_100_productions_each_event(self):
        import core.creative_pipeline as cp
        import core.scene_env as sv
        for e in AVA:
            es._BEAT_MEMORY.clear()
            es._ENV_MEMORY.clear()
            b = es.EVENT_BEATS[e]
            depth = es.RECENT_BEAT_BLOCK_BY_EVENT.get(e, es.RECENT_BEAT_BLOCK)
            msgs, tags, spots, most, envs = [], [], set(), 0, []
            with self.subTest(event=e):
                for _ in range(100):
                    scene = asyncio.run(cp.build_creative_scene("avalanche_disasters", e, [], [], ava_gpt(msgs)))
                    t, spec, sl = scene["trace"], scene["structure"]["spec"], scene["structure"]["slices"]
                    pair = (spec["beat_2"], spec["beat_3"])
                    self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
                    self.assertNotIn(pair, b["excluded_pairs"])
                    for x in pair:
                        if x in ROOF:
                            self.assertEqual(t["spot"], HT)
                        if x in LIFTB:
                            self.assertNotEqual(t["spot"], LIFT)
                        if x in DECK:
                            self.assertEqual(t["spot"], BAL)
                    # 14 Eki (4): ortam koddan, prompta ve GPT'ye gidiyor; art arda aynı eksen değeri yok
                    env = t["environment"]
                    self.assertEqual(env["spot"], t["spot"])
                    self.assertIn(es.setting_line(env), scene["prompt"])
                    self.assertEqual(spec["setting"], es.setting_line(env))
                    self.assertLessEqual(len(spec["setting"].split()), 15)
                    self.assertIn(f"WEATHER: {env['mountain']}, {env['village']}, {env['light']}", msgs[-1])
                    self.assertEqual(scene["structure"]["environment"], es.environment_label(env))
                    if set(pair) & STONE:
                        self.assertNotEqual(env["village"], "log cabins and a large lodge")
                    if envs:
                        for axis in ("mountain", "village", "light", "spot"):
                            self.assertNotEqual(env[axis], envs[-1][axis], axis)
                    for axis in ("mountain", "village", "light"):
                        # 21 Eki (Aşama 5): ışık kapsamı (sabah, gün batımı) eklendi
                        allowed = AXES[axis] + (sv.ENV_LIGHT_ADD["avalanche"] if axis == "light" else ())
                        self.assertIn(env[axis], allowed)
                    no_neg = scene["prompt"].lower().replace("no readable signs, text or flags", "")
                    self.assertEqual(es.find_terms(LEAK, no_neg), [])
                    envs.append(env)
                    for prev in tags[-depth:]:
                        self.assertNotEqual(pair[0], prev[0])
                        self.assertNotEqual(pair[1], prev[1])
                    n = len(scene["prompt"].split())
                    most = max(most, n)
                    self.assertLessEqual(n, 175)
                    self.assertNotIn("pans to follow", scene["prompt"])
                    self.assertIsNone(t["vehicle"])
                    self.assertNotIn("VEHICLE:", msgs[-1])
                    self.assertIn("in the street right below, in the lower half of the frame", msgs[-1])   # 22 Eki
                    self.assertTrue(scene["combo_key"].startswith("avalanche_disasters|none|"))
                    tags.append(pair)
                    spots.add(t["spot"])
                self.assertEqual(spots, set(sk.view_spots(e, None)))
                self.assertGreaterEqual(len(set(tags)), 15)
                self.assertLessEqual(most, 175)
                for axis in ("mountain", "village", "light"):   # her değer kullanılıyor (21 Eki: eklenen ışıklar dahil)
                    allowed = set(AXES[axis]) | (set(sv.ENV_LIGHT_ADD["avalanche"]) if axis == "light" else set())
                    self.assertEqual({x[axis] for x in envs}, allowed, axis)

    def test_environment_mixed_events_lru(self):
        # 14 Eki (4): LRU kategori bazında (köy ve kayak aynı görünmesin): karışık sırayla 150 üretim
        import core.creative_pipeline as cp
        es._BEAT_MEMORY.clear()
        es._ENV_MEMORY.clear()
        rng = random.Random(7)
        envs = []
        for i in range(150):
            e = rng.choice(AVA)
            scene = asyncio.run(cp.build_creative_scene("avalanche_disasters", e, [], [], ava_gpt()))
            env = scene["trace"]["environment"]
            self.assertEqual(es.final_prompt_issues(scene["structure"]["spec"], scene["structure"]["slices"],
                                                    scene["prompt"], scene["story"]), [])
            if envs:
                for axis in ("mountain", "village", "light", "spot"):
                    self.assertNotEqual(env[axis], envs[-1][axis], (i, axis))
            for axis in ("mountain", "village", "light"):
                self.assertNotIn(env[axis], [x[axis] for x in envs[-2:]], (i, axis))   # son 2 elenir
            envs.append(env)

    def test_environment_pool_and_line(self):
        self.assertEqual({k: tuple(v) for k, v in es.ENV_AXES.items()}, AXES)
        self.assertEqual(es.ENV_EVENTS, AVA + es.EARTHQUAKE_EVENTS)   # 14 Eki: + deprem (ayrı LRU)
        self.assertEqual(es.ENV_BLOCK, 2)
        for vals in AXES.values():
            for v in vals:
                self.assertEqual(es.find_terms(LEAK, v), [], v)
        lines = [es.setting_line({"mountain": m, "village": v, "light": li}) for m in AXES["mountain"]
                 for v in AXES["village"] for li in AXES["light"]]
        ok = [x for x in lines if len(x.split()) <= 15]
        self.assertIn(LONG_SETTING, ok)
        self.assertEqual(max(len(x.split()) for x in ok), len(LONG_SETTING.split()))
        # her blok durumunda aday kalır: son 2 değer her eksende elenir, en kötü durum
        from itertools import permutations
        for used_m in permutations(AXES["mountain"], 2):
            for used_v in permutations(AXES["village"], 2):
                for used_l in permutations(AXES["light"], 2):
                    es._ENV_MEMORY[:] = [{"mountain": m, "village": v, "light": li, "spot": HT}
                                         for m, v, li in zip(used_m, used_v, used_l)]
                    for b2, b3 in (("A1", "B1"), ("C5", "D1"), ("E7", "F4")):   # taş bina: kütük köyü elenir
                        e = KOY if b2[0] == "A" else KAYAK if b2[0] == "C" else ORMAN
                        env = es.choose_environment(e, HT, b2, b3, random.Random(1))
                        self.assertNotIn(env["mountain"], used_m)
                        self.assertNotIn(env["village"], used_v)
                        self.assertNotIn(env["light"], used_l)
                        self.assertNotEqual(env["village"], "log cabins and a large lodge")
        es._ENV_MEMORY.clear()
        # tek kamera noktası kaldıysa 1'e düşer: köyde iki nokta, ikisi de son 2'de
        es._ENV_MEMORY[:] = [{"mountain": "x", "village": "y", "light": "z", "spot": s} for s in (HT, BAL)]
        self.assertEqual(es.choose_env_spot(KOY, [HT, BAL], random.Random(1)), HT)
        es._ENV_MEMORY.clear()
        # taş ahır / istinat duvarı her yerleşimde
        seen = {es.choose_environment(KOY, HT, "A4", "B4", random.Random(i))["village"] for i in range(200)}
        self.assertIn("log cabins and a large lodge", seen)
        # stil eki ≤ 95 kelime, ortam satırı kamera cümlesinden sonra
        for e in AVA:
            for spot in sk.view_spots(e, None):
                suf = sk.style_suffix(e, None, spot, None, LONG_SETTING)
                self.assertLessEqual(len(suf.split()), 102)
                self.assertLessEqual(70 + 3 + len(suf.split()), 175)
                self.assertTrue(suf.startswith(sk.camera_rules(CAMERA.format(cam=CAMS[spot])) + " " + LONG_SETTING + " " + GUARD))
        with self.assertRaises(es.StructureError):   # volkanda ortam satırı yok
            es.build_spec(es.ERUPTION, None, "Hillside terrace facing the erupting volcano", None, "S1", "U1",
                          None, 5, LONG_SETTING)

    def test_environment_line_in_approval_message(self):
        from core.trace_format import format_final_prompt
        env = {"mountain": "jagged rocky peaks", "village": "red timber houses", "light": "bright cold sunny day",
               "spot": BAL}
        label = es.environment_label(env)
        self.assertEqual(label, f"Ortam: dağ = jagged rocky peaks · yerleşim = red timber houses · ışık = bright "
                                f"cold sunny day · kamera = {BAL}")
        title, body = format_final_prompt({"prompt": "p q", "story": "p", "style_suffix": "q", "environment": label})
        self.assertIn(label, body)
        self.assertNotIn("Ortam:", format_final_prompt({"prompt": "p q", "story": "p", "style_suffix": "q"})[1])
        src = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read()
        self.assertIn('info["environment"] = structure["environment"]', src)

    def test_skeleton_texts(self):
        import core.prompt_generator as pg
        for e in AVA:
            s = sk.EVENT_SKELETONS[e]
            for spot in s["spots"]:
                story = sk.fill_skeleton(e, None, {"spot": spot, "weather": s["weather"][0], "count": 4,
                                                   "people": s["people"][0]})
                with self.subTest(event=e, spot=spot):
                    self.assertTrue(35 <= len(story.split()) <= 70, len(story.split()))
                    self.assertEqual(pg.event_fidelity_issues(e, story), [])
                    for code, terms, *_ in es.EVENT_BANNED_WORDS[e]:
                        self.assertEqual(es.find_terms(terms, story), [], story)


if __name__ == "__main__":
    unittest.main()
