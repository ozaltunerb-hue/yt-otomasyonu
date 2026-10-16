#!/usr/bin/env python3
"""
🔥 Ateş hortumu kapısı (15 Eki 2026, Bahadır): Telegram 10:44 üretimi 3 denemede kapıdan geçmedi. GPT'nin doğru T6/U4
cümleleri "seçilen olay görünmüyor" diye reddedildi, sonraki denemeler 40-70 toplamını aştı (81, 73). Madde terimleri
anlam bazlı nesne + eylem gruplarına çevrildi (_FIRE_TOR_*, sadece bu olay), toplam 40-75. Ağ yok, Kie/GPT çağrısı yok.
REJECTED_REAL: gerçek GPT retleri. FREE: madde metninden farklı kurulmuş serbest cümleler. HELD_OUT: ilk grup tasarımından
SONRA yazılan kontrol cümleleri (ilk ölçümde 3/36 ret; "upward", "from the road" eklendi).
15 Eki (2), Bahadır: hortum dev (kilit cümlede ölçek kıyası), kamera yüksek ve yakın, ön planda 2-3 kaçan kişi; T2, T4,
T5, U3, U5 yeni (cam/korkuluk/tabela/çit yerine büyük hedefler). Yeni maddelerin kontrol cümlelerinde ilk ölçüm 1/15 ret.
"""
import asyncio
import json
import os
import random
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.skeleton_pipeline as sk

E = es.FIRE_TORNADO
# 16 Eki, Bahadır: ortam ekseni, 3 ortam × 2 nokta (ağaçlık yerleşim; önceki: "Overlook above the burning valley road",
# "Balcony of a roadside house")
ENVS = {
    "forest_edge": ("A colossal fire tornado, several times taller than the houses and trees, tears out of a burning "
                    "forest into a residential area, its wide base engulfing the houses.",
                    ("High balcony at the edge of a wooded neighborhood", "Rooftop terrace above a wooded residential area")),
    "tree_street": ("A colossal fire tornado, several times taller than the houses and trees, tears down a burning "
                    "tree-lined street, its wide base engulfing the houses and cars along it.",
                    ("High balcony over a tree-lined residential street", "Upper-floor terrace above a street of houses")),
    "village_woods": ("A colossal fire tornado, several times taller than the houses and trees, tears from the burning "
                      "woods into a village, its wide base engulfing the first houses and trees.",
                      ("Hillside terrace above a village", "High balcony of a village house")),
}
SPOTS = tuple(sp for _, spots in ENVS.values() for sp in spots)
VEHICLES = ("pickup truck", "delivery truck", "white van", "SUV")   # 17 Eki: küçük araç yok

# Gerçek GPT retleri tek dosyada (tests/fixtures/rejected_real.json, test_rejected_real.py da okur)
with open(os.path.join(os.path.dirname(__file__), "fixtures", "rejected_real.json"), encoding="utf-8") as _f:
    REJECTED_REAL = {}
    for _r in json.load(_f)["false_rejections"]:
        # 16 Eki: sadece 15 Eki canlı retleri (eski sıkı kapı testleri); "source" alanlı 2i kayıtları test_rejected_real'de
        # 17 Eki: çıkarılan maddelerin (T3, U4...) kayıtları burada değil, test_rejected_real'de (RETIRED_BEATS)
        if (_r["event"] == "Fire tornado tears across a burning roadside" and "source" not in _r
                and _r["beat"] not in es.RETIRED_BEATS[es.FIRE_TORNADO]):
            REJECTED_REAL.setdefault(_r["beat"], []).append(_r["text"])
FREE = {
    "T1": [
        'The swirling flames heave the pickup truck off the asphalt and hurl it against a blazing tree.',
        'Caught in the fiery vortex, the van rises off the road and is thrown into a burning pine.',
        'The fire whirl yanks the SUV into the air and smashes it into a tree engulfed in flames.',
        'The small car is pulled off the ground by the spinning fire and slammed into a flaming trunk.',
        'Whirling flames pluck the van from the road, tossing it into a tree that is already ablaze.',
    ],
    "T2": [
        'The colossal vortex flings an entire blazing pine onto the SUV, caving its roof in.',
        'A whole burning trunk, ripped up by the fire tornado, slams down on the van and flattens its cab.',
        'The towering fire whirl drops a flaming tree right on top of the pickup truck, crumpling the roof.',
        'Hurled by the giant tornado, a burning oak lands on the small car and crushes it.',
        'The fire tornado launches a massive flaming log onto the SUV, pinning it beneath the burning wood.',
    ],
    "T4": [
        "The SUV is knocked sideways across the lane as the tornado's enormous base roars past just behind it.",
        'With the giant fire column brushing past its rear, the van skids broadside over the road.',
        'The pickup truck slides sideways across the asphalt while the huge burning vortex passes inches behind it.',
        'The base of the towering fire whirl sweeps by right at its back, sending the small car sliding sideways.',
        'The SUV slews across the road as the massive fire tornado grazes past behind it.',
    ],
    "T5": [
        'The giant fire whirl flips the SUV upside down and the whole vehicle erupts in flames.',
        'The towering vortex overturns the van onto its roof, and fire quickly engulfs it.',
        'The pickup truck is rolled onto its roof by the colossal tornado and goes up in flames.',
        'The colossal fire whirl tips the small car over, leaving it belly up and ablaze.',
        'Caught by the enormous fire column, the SUV tumbles onto its roof and bursts into flames.',
    ],
    "T6": [
        'Burning wreckage strikes the van broadside, sending it into a spin until it stalls across the lane.',
        "A blazing chunk of debris hits the pickup truck's flank and it whips around, ending sideways across the road.",
        'Fiery debris pounds the side of the small car, which slews around and comes to rest blocking the road.',
        "A mass of burning debris rams the SUV's door, knocking it into a skid that leaves it stranded across the asphalt.",
        "Flaming fragments batter the van's side panel, spinning it until it halts crosswise on the road.",
    ],
    "U1": [
        'The fiery vortex peels the blazing roof from a house and flings burning chunks all over the street.',
        'A burning house loses its roof to the fire whirl, its flaming fragments strewn across the road.',
        'The tornado wrenches the flaming roof off a home, sending fiery shards raining across the street.',
        "The spinning fire tears away a house's burning roof and hurls its glowing pieces over the street.",
        "With a violent twist, the fire tornado lifts a house's roof, already ablaze, and showers the street with burning debris.",
    ],
    "U2": [
        'The flaming vortex rips a blazing tree out by its roots and hurls it along the road.',
        'A burning pine is torn from the ground by the fire whirl and thrown down the roadway.',
        'The tornado yanks a flaming tree from the earth, sending it tumbling down the road.',
        'Roots and all, a burning oak is pulled up by the spinning fire and tossed down the highway.',
        'The fire tornado wrenches a blazing tree loose and launches it far down the road.',
    ],
    "U6": [
        'The fire whirl rolls over a parked caravan and flips it aside amid billowing flames and smoke.',
        'A parked trailer is overturned by the passing vortex, vanishing in a cloud of fire and smoke.',
        'The spinning flames engulf a parked camper and throw it to the side in a burst of smoke and fire.',
        'The tornado crosses a parked trailer and knocks it over in a swirl of flames and black smoke.',
        'The burning vortex slams into a parked caravan and tips it onto its side inside a cloud of fire and smoke.',
    ],
    # 17 Eki, Bahadır (Parti 1): yeni maddeler T7, U7-U11 (T3, U3-U5 çıktı)
    "T7": [
        "Down the road the SUV races away as burning wreckage from the vortex crashes onto the asphalt behind it.",
        "The pickup truck speeds off from the giant fire column while flaming debris slams down at its back.",
        "The white van accelerates down the road, burning debris from the tornado falling just behind it.",
        "Fleeing the colossal fire whirl, the small car tears away as blazing debris rains onto the road behind.",
        "The SUV bolts down the road, flaming wreckage crashing onto the lane right behind it.",
    ],
    "U7": [
        "The colossal vortex rips a wooden house from its foundation and swallows it whole, beams and planks whirling upward.",
        "A whole wooden house is torn off its foundation by the fire tornado, its burning timbers spiraling into the column.",
        "The giant fire whirl lifts an entire house off its foundation, planks and rafters flying up into the flames.",
        "The towering tornado devours a wooden house, its burning beams spinning up into the fiery column.",
        "Torn from its foundation, the whole house vanishes into the fire tornado as burning planks whirl skyward.",
    ],
    "U8": [
        "The fire tornado tears the roofs off two houses one after another and sucks them up into its column.",
        "One roof, then the next, is ripped from two houses in a row and pulled into the spinning flames.",
        "Two neighboring houses have their roofs torn away one by one and lifted into the fire column.",
        "The colossal vortex strips the roofs from both houses in quick succession, hurling them into the flames.",
        "Two roofs in a row are peeled away by the giant fire whirl and drawn up into its spinning column.",
    ],
    "U9": [
        "A house's front wall rips away and the rubble is sucked into the vortex as flames pour inside.",
        "The fire tornado tears the facade off a house, drawing the rubble up while fire floods the rooms.",
        "A house loses its whole front wall to the giant vortex, the debris sucked into the burning column.",
        "The colossal fire whirl rips the front of a house away and pulls the rubble in, flames rushing inside.",
        "The towering tornado peels the facade from a house and sucks the broken wall into its flaming core.",
    ],
    "U10": [
        "The fire tornado tears the porch and front steps off a house and sucks them into its column amid sparks.",
        "The giant vortex rips away the wooden porch of a house, pulling the steps into the flames in a burst of sparks.",
        "A burning porch and its steps are torn from a house and drawn up into the towering column.",
        "The colossal fire whirl wrenches the porch off a house and swallows the steps in a storm of embers.",
        "The front steps and porch of a house are ripped loose and sucked into the vortex in a shower of sparks.",
    ],
    "U11": [
        "The towering vortex engulfs a wooden garage next to a house and its walls burst apart, burning boards flying up.",
        "A garage beside a house is torn to pieces by the fire tornado, its flaming boards spiraling into the column.",
        "The giant fire whirl smashes a wooden garage apart, burning planks spinning up into the flames.",
        "The colossal tornado rips through a garage by a house, its blazing walls bursting apart and whirling upward.",
        "The fire tornado shreds a wooden garage, sending its burning boards spiraling into the column.",
    ],
}
HELD_OUT = {
    "T1": [
        'The roaring fire vortex tears the white van from the road and hurls it into a blazing pine.',
        'The pickup truck is ripped from the asphalt by the flames and thrown against a burning tree, wedged in its branches.',
        'The fiery whirlwind snatches the small car upward, smashing it into the trunk of a flaming tree.',
    ],
    "T2": [
        'A burning tree torn loose by the vortex crashes down onto the van, its roof buckling under the weight.',
        "The giant fire whirl smashes a blazing trunk into the pickup truck's roof, crushing the cab.",
        'The tornado tosses a flaming pine that falls on the small car, flattening it.',
    ],
    "T4": [
        'The van is pushed sideways over the road as the immense fire tornado tears past close behind.',
        'Right behind the pickup truck the giant vortex rakes across the road, shoving it sideways.',
        "The small car fishtails across the lane as the fire tornado's wide base crosses just behind it.",
    ],
    "T5": [
        'The fire tornado rolls the van over twice and it lands on its roof, engulfed in flames.',
        'The massive vortex heaves the pickup truck onto its side and flames swallow it.',
        'The small car is turned over by the towering fire whirl and catches fire upside down.',
    ],
    "T6": [
        "A burst of flaming debris rams into the SUV's side, sending it spinning to a stop across the lane.",
        'Burning wreckage smashes the white van broadside and it spins out, stopping across the road.',
        'Fiery debris hammers into the side of the pickup truck, which whips around and halts sideways on the road.',
    ],
    "U1": [
        'The fire tornado tears the flaming roof from a house, scattering burning shingles across the street.',
        "A house's blazing roof is ripped away by the vortex and its fiery pieces rain over the street.",
        'The swirling flames strip the roof off a burning home and fling its fragments into the street.',
    ],
    "U2": [
        'The fire tornado rips a flaming tree from the ground and throws it along the road.',
        'A burning tree is uprooted by the vortex and hurled down the roadway.',
        'The fiery whirl tears a blazing pine out of the earth and sends it crashing down the road.',
    ],
    "U6": [
        'The fire tornado rolls over a parked trailer and flips it aside in a cloud of fire and smoke.',
        'A parked caravan is tossed aside by the vortex, disappearing in flames and smoke.',
        'The swirling flames sweep across a parked trailer, overturning it in a burst of fire and smoke.',
    ],
    # 17 Eki (Parti 1): yeni maddelerin kontrol cümleleri
    "T7": [
        "The delivery truck speeds away from the tornado as a mass of burning debris slams down behind it.",
        "The van flees down the road, flaming wreckage crashing onto the asphalt at its back.",
        "Burning debris crashes down behind the SUV as it races away from the giant fire column.",
    ],
    "U7": [
        "The fire tornado rips a whole house from its foundation, its burning planks spiraling upward.",
        "A wooden house is swallowed by the vortex, beams and boards flying up into the flames.",
        "The giant fire whirl tears an entire house loose, its burning timbers spinning into the column.",
    ],
    "U8": [
        "The vortex rips the roofs off two houses one after another, sucking them into the column.",
        "Two roofs in a row are torn away and pulled up into the spinning fire.",
        "The roofs of both houses are ripped off in quick succession and lifted into the flames.",
    ],
    "U9": [
        "The vortex tears the front wall of a house loose and sucks the rubble in, flames filling the rooms.",
        "The tornado rips the facade off a house and draws the broken wall into the flames.",
        "A house front is torn away and sucked into the burning column as flames pour into the rooms.",
    ],
    "U10": [
        "The vortex rips the porch off a house and pulls the front steps into its column in a burst of sparks.",
        "A house loses its porch and steps to the fire tornado, sucked upward in a shower of embers.",
        "The tornado tears the front steps and porch away and drags them into the flames amid sparks.",
    ],
    "U11": [
        "The fire tornado engulfs a garage beside a house and its walls burst apart, burning boards whirling up.",
        "A wooden garage is torn apart by the vortex, its flaming planks spinning into the column.",
        "The towering fire whirl smashes a garage to pieces, burning boards spiraling upward.",
    ],
}

# 15 Eki (2): WORD BUDGET'e (4-9s/9-15s en fazla 18 kelime) uyan kısa serbest cümleler; kapı değiştirilmeden yazıldı
SHORT = {
    "T6": ["Huge burning wreckage hits the van broadside; it spins and halts across the road.",
           "A mass of flaming debris rams the SUV, spinning it to a stop across the lane."],
}

# 15 Eki (3): denetim boşlukları; kaldırma ve yana itme zaten geçiyordu (kilit), devirme (knock over/down) eklendi
GAP = {
    "T1": [
        'The giant fire tornado picks up the SUV and hurls it into a blazing pine.',
        'The van rises into the air inside the towering vortex and slams into a burning tree.',
        'Carried aloft by the colossal fire whirl, the pickup truck smashes into a flaming oak.',
        'The small car is torn off the road by the huge fire column and flung into a burning tree.',
        'The towering vortex lifts the SUV and throws it against a blazing pine.',
    ],
    "T4": [
        'The giant fire tornado drives the SUV sideways as its huge base roars past right behind it.',
        'The towering vortex forces the van sideways across the lane while its base sweeps past behind.',
        'The pickup truck is driven sideways by the colossal fire whirl passing just behind it.',
        'The huge fire column forces the small car sideways as it tears past close behind.',
    ],
    "T5": [
        'The giant fire tornado knocks the SUV over onto its roof and it bursts into flames.',
        'The towering vortex knocks over the van, which lands upside down and erupts in flames.',
        'The pickup truck is knocked over by the huge fire whirl and goes up in flames.',
    ],
    "U2": [
        'The giant vortex knocks down a cluster of burning trees and flings the trunks down the road.',
        'A stand of blazing trees is knocked over by the giant vortex, their trunks hurled along the road.',
        'The towering fire whirl knocks down burning trees and sends their trunks flying down the road.',
    ],
    "U6": [
        'The colossal fire whirl knocks over a parked trailer in a cloud of fire and smoke.',
        'A parked caravan is knocked over by the giant vortex amid flames and smoke.',
        'The huge fire whirl knocks the trailer onto its side in a burst of fire and smoke.',
    ],
}

# 15 Eki (4): T3 için 8 yeni serbest cümle (beat ve gerçek retlerden farklı)
T3_NEW = [
    'The vortex snatches the white van off the asphalt, whirls it around and slams it back down in sparks.',
    'Pulled into the burning column, the pickup truck twists in midair and smashes onto the road.',
    'The SUV is swallowed by the fire tornado, tumbles high above the road and plummets back down.',
    'The giant fire whirl grabs the small car, flings it around overhead and drops it hard on the asphalt.',
    'The van is hoisted into the flames, rotating wildly, then hits the road in a spray of embers.',
    'Caught by the roaring column, the truck lurches upward, spins and comes crashing back down.',
    'The towering vortex carries the car up into the smoke before it falls and smashes onto the road.',
    'The white van is yanked up into the fire tornado, twirls, and lands hard on the road amid sparks.',
]
# 15 Eki (4): her T/U maddesine 4 GPT tarzı serbest cümle (gevşeklik denetimi; ilk ölçüm 1/48 ret, T3)
AUDIT_4 = {
    "T1": [
        'The vortex hauls the white van upward and hurls it straight into a blazing pine.',
        'The pickup truck is ripped from the road by the fire column and slammed against a burning tree.',
        'The towering tornado lifts the SUV and throws it into the burning trees beside the road.',
        'Snatched by the vortex, the car is flung into a flaming tree at the roadside.',
    ],
    "T2": [
        'The vortex flings a whole burning tree trunk down onto the white van, caving in its roof.',
        'A blazing trunk hurled by the fire tornado smashes onto the pickup truck and crushes the cab.',
        'The tornado drops a huge flaming tree on top of the SUV, flattening its roof.',
        'A massive burning trunk crashes onto the car, crushing it under the weight.',
    ],
    "T4": [
        "The white van is shoved sideways as the tornado's huge base roars past right behind it.",
        'The vortex sweeps past just behind the pickup truck, knocking it sideways across the road.',
        'The SUV slides sideways while the giant fire column passes close behind it.',
        "As the tornado's base tears by behind it, the car is pushed sideways across the lane.",
    ],
    "T5": [
        'The vortex flips the white van onto its roof and the van bursts into flames.',
        'The pickup truck is rolled over by the fire tornado and catches fire on its roof.',
        'The tornado overturns the SUV, which goes up in flames upside down.',
        'The car is tipped onto its roof by the towering column and erupts in flames.',
    ],
    "T6": [
        'Huge burning debris thrown by the tornado slams into the white van, spinning it to a stop across the road.',
        'A mass of flaming wreckage hits the pickup truck, which spins and halts across the lane.',
        'Burning debris from the vortex crashes into the SUV, sending it spinning until it stops sideways.',
        'Flaming chunks hurled by the tornado strike the car, which spins and comes to rest across the road.',
    ],
    "U1": [
        'The tornado tears the burning roof off a house and sucks the sheets up into its column.',
        'The vortex rips a flaming roof from a house, pulling the panels into the fire column.',
        'A house loses its blazing roof as the towering tornado drags the sheets upward.',
        'The fire column strips the burning roof from a home and swallows the sheets.',
    ],
    "U2": [
        'The vortex rips a cluster of burning trees out of the ground and throws the trunks down the road.',
        'The tornado uproots a stand of blazing trees, hurling the trunks along the road.',
        'A group of burning trees is torn from the earth by the fire column and flung down the road.',
        'The towering tornado yanks burning trees out by their roots and scatters the trunks on the road.',
    ],
    "U6": [
        'The vortex sweeps over a parked trailer and tosses it aside in fire and smoke.',
        'The tornado flips a parked trailer aside in a cloud of flames and smoke.',
        'A parked trailer is thrown aside by the fire column amid fire and smoke.',
        'The towering tornado rolls a parked trailer over and casts it aside in flames and smoke.',
    ],
    # 17 Eki (Parti 1): yeni maddeler
    "T7": [
        "The white van races away from the vortex as burning debris crashes onto the road behind it.",
        "The pickup truck accelerates hard, flaming wreckage slamming down on the asphalt behind it.",
        "The SUV speeds off as a shower of burning debris from the tornado crashes down at its back.",
        "Fleeing the giant fire whirl, the car drives away while flaming debris lands behind it.",
    ],
    "U7": [
        "The vortex tears a wooden house off its foundation and swallows it, burning planks spiraling up.",
        "The tornado devours a whole house, its beams and boards whirling up into the column.",
        "A wooden house is ripped from its foundation and its burning timbers spin up into the fire column.",
        "The towering tornado swallows an entire house, planks and beams flying into the flames.",
    ],
    "U8": [
        "The tornado rips the roofs off two houses in a row and pulls them up into its column.",
        "The vortex tears off one roof after another from two houses and sucks them into the flames.",
        "Two houses lose their roofs one by one to the spinning fire column.",
        "The fire column strips the roofs from both houses in quick succession and draws them upward.",
    ],
    "U9": [
        "The vortex tears the front wall off a house and sucks the rubble in as flames pour into the rooms.",
        "The facade of a house rips away and the tornado draws the debris into its burning column.",
        "The tornado peels the front wall from a house, pulling the rubble into the flames.",
        "A house front is ripped off and sucked into the fire column while flames rush inside.",
    ],
    "U10": [
        "The vortex rips the porch and front steps off a house and pulls them into its column in sparks.",
        "The tornado tears away the porch of a house and sucks the steps up in a storm of sparks.",
        "A porch and its front steps are ripped off a house and drawn into the burning column.",
        "The fire column wrenches the front steps from a house and swallows the porch in a burst of embers.",
    ],
    "U11": [
        "The vortex engulfs a wooden garage beside a house and its walls burst apart in burning boards.",
        "The tornado smashes a garage to pieces, its flaming planks spiraling into the column.",
        "A wooden garage is torn apart by the fire column as burning boards whirl upward.",
        "The towering tornado shreds a garage next to a house, sending burning boards into the flames.",
    ],
}


def slot(bid):
    return "slice_2" if bid[0] == "T" else "slice_3"


def terms(bid):
    return es.EVENT_BEATS[E][slot(bid)][bid]["terms"]


def beat(bid):
    return es.EVENT_BEATS[E][slot(bid)][bid]


def gate(bid, text):
    """Maddenin kapısı (terim grupları + 15 Eki (4) "unless"); boş liste = geçer."""
    return es.beat_missing(beat(bid), text)


def with_vehicle(text, vehicle):
    for v in ("pickup truck", "delivery truck", "small car", "white van", "SUV", "van"):
        if v in text:
            return text.replace("white van" if v == "van" and "white van" in text else v, vehicle, 1)
    return text


def build(b2, b3, vehicle="SUV", spot=SPOTS[4], s2=None, s3=None, s1=None, people=3):   # 16 Eki: en kısa stil eki (yamaç terası)
    spec = es.build_spec(E, None, spot, None, b2, b3, vehicle, people)
    word = es.NUMBER_WORDS[people].capitalize()
    sl = {"slice_1_rest": s1 or f"{word} people run from the fire tornado on the road right below.",
          "slice_2": s2 or with_vehicle(FREE[b2][0], vehicle), "slice_3": s3 or FREE[b3][0]}
    return spec, sl


KEY = ENVS["forest_edge"][0]   # EVENT_KEY_VISUAL'daki varsayılan (ilk ortam)
# 16 Eki: 175 kelime için kısaldı, kurallar aynı. Önceki: "...high vantage close to the towering fire tornado filling at
# least half of the frame, its top and smoke cloud never cut off, two or three people fleeing it in the near foreground;
# slight hand shake, the camera pans to follow the fire tornado; ..."
CAMERA = ("Handheld footage shot by a person standing {spot}, high vantage close to the fire tornado filling at least "
          "half the frame, its top and smoke never cut off, two or three people fleeing in the near foreground; slight "
          "hand shake, the camera pans to follow the tornado; one continuous shot, no zoom, no cuts.")
# 17 Eki, Bahadır (temizlik + Parti 1): T3 (fizik 2), U3 (ahır), U4 (çalı yığını), U5 (odun yığını, tarla) çıktı;
# U1 "across the street"; T7, U7-U11 yeni (Bahadır'ın metni birebir)
POOL = ({"T1": "the towering fire tornado lifts the {vehicle} off the road and flings it into a burning tree",
         "T2": "the huge fire tornado hurls a whole burning tree trunk onto the {vehicle}, crushing its roof",
         "T4": "the {vehicle} is shoved sideways as the huge base of the fire tornado sweeps past right behind it",
         "T5": "the huge fire tornado rolls the {vehicle} over onto its roof and it bursts into flames",
         "T6": "huge flaming debris flung by the towering tornado slams into the {vehicle}, which spins and stops "
               "across the road",
         # 18 Eki: Parti 1 metinleri kısaldı (≤16 kelime)
         "T7": "the {vehicle} races away from the fire tornado as burning debris crashes down behind it"},
        {"U1": "the towering fire tornado rips the burning roof off a house across the street and sucks the sheets into "
               "its column",
         "U2": "the huge fire tornado uproots a cluster of burning trees and flings their trunks down the road",
         "U6": "the towering fire tornado sweeps over a parked trailer and tosses it aside in fire and smoke",
         "U7": "a wooden house across the street is torn from its foundation, planks spiraling into the column",
         "U8": "the roofs of two houses across the street are ripped off and sucked into the column",
         "U9": "the front wall of a house across the street tears away, rubble sucked into the column",
         "U10": "the porch and steps of a house across the street are ripped off and pulled in",
         "U11": "a wooden garage beside a house across the street bursts apart, burning boards spiraling up"})
# Kod yedeğinin 75 kelimeye sığmadığı çiftler (tests/test_story_fallback.py FALLBACK_GAPS_EXCLUDED). 18 Eki: kısa
# metinlerle 23 -> 1
FIT_GAPS = {("T6", "U1")}


class TestFireTornadoGate(unittest.TestCase):
    def test_key_camera_pool_locked(self):
        # 15 Eki (2), Bahadır: dev hortum (ölçek kıyası), yüksek ve yakın kamera, ön planda 2-3 kaçan kişi
        self.assertEqual(es.EVENT_KEY_VISUAL[E], KEY)
        self.assertEqual({k: (v["key"], v["spots"]) for k, v in es.FIRE_TOR_ENVS.items()}, ENVS)
        for key, _ in ENVS.values():   # 16 Eki: ~29-30 kelime (önceki 26), ölçek ifadesi duruyor
            self.assertLessEqual(len(key.split()), 30)
            self.assertIn("several times taller than the houses and trees", key)
        for spot in SPOTS:
            with self.subTest(spot=spot):
                self.assertTrue(es.style_suffix(E, None, spot, None, None).startswith(
                    CAMERA.format(spot=sk.CAMERA_SPOTS[spot]) + " " + sk.FIRE_TORNADO_GUARDRAILS))
        b = es.EVENT_BEATS[E]
        self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, POOL[0])
        self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, POOL[1])
        self.assertEqual(b["excluded_pairs"], {("T1", "U2"), ("T2", "U2")} | FIT_GAPS)
        # 17 Eki, Bahadır: U1 "across the street", nokta kısıtı kalktı (önceki: sadece köy yamaç terasında)
        self.assertEqual(b["excluded_spots"], {})
        self.assertEqual(sk.count_range(E, None), (2, 3))

    def test_beats_big_targets_and_size(self):
        # Her maddede hortumun büyüklüğü; cam, ince direk, tel, çit, tabela hedef değil
        size = ("towering", "huge", "colossal", "giant", "swallow")
        small = ("glass", "window", "windshield", "pole", "wire", "cable", "fence", "sign", "billboard", "railing",
                 "guardrail", "ember")
        # 17-18 Eki: Parti 1 kısa metinleri Bahadır'ın metni birebir (büyüklük sıfatı yok); kilit cümle ölçeği verir
        no_size = {"T7", "U7", "U8", "U9", "U10", "U11"}
        for sl in POOL:
            for bid, text in sl.items():
                with self.subTest(beat=bid):
                    self.assertEqual(bool(es.find_terms(size, text)), bid not in no_size, text)
                    self.assertEqual(es.find_terms(small, text), [], text)

    def test_rejected_real_gpt_sentences_pass(self):
        # 15 Eki 10:44: 3 denemede reddedilen gerçek GPT cümleleri kendi maddesinde geçer
        for bid, sents in REJECTED_REAL.items():
            for t in sents:
                with self.subTest(beat=bid, text=t):
                    self.assertEqual(gate(bid, t), [])
        for t in REJECTED_REAL["T6"]:
            spec, sl = build("T6", "U6", "SUV", s2=t, s3=FREE["U6"][1])   # 17 Eki: U4 çıktı
            with self.subTest(text=t):
                codes = {i["rule"] for i in es.slice_issues(spec, sl)}
                self.assertFalse(codes & {"beat_terms", "beat_vehicle"}, codes)

    def test_free_paraphrases_pass_every_beat(self):
        ids = [b for sl in ("slice_2", "slice_3") for b in es.EVENT_BEATS[E][sl]]
        self.assertEqual(sorted(FREE), sorted(ids))
        self.assertEqual(sorted(HELD_OUT), sorted(ids))
        for bid in ids:
            beat = es.beat_text(E, slot(bid), bid, "SUV").lower()
            self.assertGreaterEqual(len(FREE[bid]), 5)
            for t in FREE[bid] + HELD_OUT[bid] + SHORT.get(bid, []):
                with self.subTest(beat=bid, text=t):
                    self.assertEqual(gate(bid, t), [])
                    self.assertNotEqual(t.lower().rstrip("."), beat)
                    self.assertNotEqual(t.lower().split()[:4], beat.split()[:4])   # farklı kurulmuş
                    self.assertTrue(10 <= len(t.split()) <= 24)
                    if slot(bid) == "slice_2":
                        for v in VEHICLES:   # araç kapısı da geçer
                            vt = dict(es.event_vehicles(E, None))[v]
                            self.assertTrue(es.find_terms(vt, with_vehicle(t, v)), (v, t))

    def test_no_false_positive_between_beats(self):
        # Bir maddenin cümlesi başka maddenin kapısından geçmez. İstisna: yasak çiftler (aynı videoda hiç birlikte yok)
        b = es.EVENT_BEATS[E]
        ex = b["excluded_pairs"] | {(d, v) for v, d in b["excluded_pairs"]}
        ids = list(b["slice_2"]) + list(b["slice_3"])
        for x in ids:
            for o in ids:
                if o == x or (x, o) in ex:
                    continue
                for t in FREE[o] + HELD_OUT[o] + SHORT.get(o, []) + REJECTED_REAL.get(o, []):
                    with self.subTest(beat=x, other=o, text=t):
                        self.assertTrue(gate(x, t))
        # "spinning/whirling" hortumun sıfatı: U1 cümlesi T6 (araç yok) sayılmaz; 17 Eki: U1 iki evin çatısını (U8)
        # anlatan cümleyi almaz ("unless")
        self.assertTrue(gate("T6", FREE["U1"][4]))
        self.assertTrue(gate("U1", FREE["U8"][0]))
        self.assertEqual(gate("U8", FREE["U8"][0]), [])

    def test_audit_gap_phrases(self):
        # 15 Eki (3): kaldırma (picks up, rises into the air, carried aloft, torn off the road, lifts), yana itme
        # (drives/forces sideways), devirme (knocks down/over); her grup en az 3 serbest cümle
        groups = {"lift": ("picks up", "rises into the air", "carried aloft", "torn off the road", "lifts"),
                  "sideways": ("drives the", "forces the", "driven sideways", "forces the small car"),
                  "knock": ("knock",)}
        for name, keys in groups.items():
            hits = [t for ts in GAP.values() for t in ts if any(k in t for k in keys)]
            self.assertGreaterEqual(len(hits), 3, name)
        b = es.EVENT_BEATS[E]
        ex = b["excluded_pairs"] | {(d, v) for v, d in b["excluded_pairs"]}
        ids = list(b["slice_2"]) + list(b["slice_3"])
        for bid, sents in GAP.items():
            beat = es.beat_text(E, slot(bid), bid, "SUV").lower()
            for t in sents:
                with self.subTest(beat=bid, text=t):
                    self.assertEqual(gate(bid, t), [])
                    self.assertNotEqual(t.lower().split()[:4], beat.split()[:4])
                    for o in ids:   # başka madde sayılmaz (yasak çiftler hariç)
                        if o != bid and (o, bid) not in ex:
                            self.assertTrue(gate(o, t), (o, t))

    def test_audit_gap_words_without_tornado_event_rejected(self):
        # Aynı fiiller, ama hortumun yaptığı bir olay yok: hiçbir maddeden geçmez
        texts = ["A crane lifts the SUV onto a flatbed parked beside the road.",
                 "The pickup truck rises over the hill and drives past the parked trailer.",
                 "A driver picks up a branch from the road next to his van.",
                 "The wind drives the van sideways on the empty road.",
                 "Strong gusts force the small car sideways near the field.",
                 "A gust knocks over a plastic chair beside the barn.",
                 "Workers knock down an old wooden fence by the road.",
                 "The van is carried aloft on a car transporter along the highway.",
                 "A tow truck pulls the SUV off the road into the field."]
        for bid in [x for sl in ("slice_2", "slice_3") for x in es.EVENT_BEATS[E][sl]]:
            for t in texts:
                with self.subTest(beat=bid, text=t):
                    self.assertTrue(gate(bid, t))

    def test_retired_beats_17oct(self):
        # 17 Eki, Bahadır (temizlik turu): T3 (emilip dönüp çakılma, fizik 2), U3 (ahır), U4 (çalı yığını), U5 (odun
        # yığını, tarla) havuzda yok, kimlikleri tekrar kullanılmaz; "unless" artık sadece U1'de (U8'den ayırır)
        b = es.EVENT_BEATS[E]
        for bid in ("T3", "U3", "U4", "U5"):
            with self.subTest(beat=bid):
                self.assertNotIn(bid, b["slice_2"])
                self.assertNotIn(bid, b["slice_3"])
                self.assertIn(bid, es.RETIRED_BEATS[E])
        self.assertEqual(b["slice_3"]["U1"].get("unless"), es._FIRE_TOR_ROW)
        self.assertTrue(all("unless" not in x for e, d in es.EVENT_BEATS.items() for sl in ("slice_2", "slice_3")
                            for k, x in d[sl].items() if (e, k) != (E, "U1")))
        # yeni maddeler açık arazi/kırsal değil, yerleşim: ev, çatı, ön duvar, veranda, garaj
        for bid in ("U7", "U8", "U9", "U10", "U11"):
            text = es.beat_text(E, "slice_3", bid)
            with self.subTest(new=bid):
                self.assertTrue(es.find_terms(("house", "roof", "garage"), text), text)
                self.assertEqual(es.find_terms(es.FIRE_TOR_OPEN_LAND + ("barn", "field", "woodpile", "brush"), text), [])

    def test_audit_4_every_beat(self):
        # Her T/U maddesi: 4 GPT tarzı cümle kendi maddesinde geçer, başka maddede geçmez (yasak çiftler hariç)
        b = es.EVENT_BEATS[E]
        ex = b["excluded_pairs"] | {(d, v) for v, d in b["excluded_pairs"]}
        ids = list(b["slice_2"]) + list(b["slice_3"])
        self.assertEqual(sorted(AUDIT_4), sorted(ids))
        for bid, sents in AUDIT_4.items():
            self.assertEqual(len(sents), 4)
            for t in sents:
                with self.subTest(beat=bid, text=t):
                    self.assertEqual(gate(bid, t), [])
                    for o in ids:
                        if o != bid and (o, bid) not in ex:
                            self.assertTrue(gate(o, t), (o, t))

    def test_unrelated_sentences_rejected(self):
        # Hortumsuz, olaysız ya da alakasız cümleler hiçbir maddeden geçmez
        unrelated = ["Three people run along the road as smoke drifts over the valley.",
                     "The SUV drives slowly down the road past the burning field.",
                     "A wooden barn stands beside the road under an orange sky.",
                     "A big woodpile sits next to the house at the edge of the field.",
                     "A tall pine sways in the hot dry wind beside the road.",
                     "A parked trailer waits on the gravel shoulder of the road.",
                     "The van stops on the road while thick smoke hangs in the air.",
                     "A pile of dry brush lies at the side of the road.",
                     "The wind tears a billboard from its supports and hurls it aside.",
                     "A shop window shatters in the heat on the street below.",
                     "The pickup truck is parked under a tree near the house roof."]
        for bid in [b for sl in ("slice_2", "slice_3") for b in es.EVENT_BEATS[E][sl]]:
            for t in unrelated:
                with self.subTest(beat=bid, text=t):
                    self.assertTrue(gate(bid, t))
        bad = {"T1": "The van is pushed into a burning tree by the swirling flames.",
               "T2": "A burning tree stands beside the SUV on the road.",
               "T4": "The SUV waits on the road as the fire tornado looms ahead.",
               "T5": "The fire tornado rolls past the van and smoke surrounds it.",
               "T6": "The SUV spins and stops across the road as the flames swirl.",
               "U6": "A parked trailer stands near the burning road.",
               # 17 Eki (Parti 1): yeni maddeler, olay eksik
               "T7": "The SUV waits on the road as burning debris falls nearby.",
               "U7": "The fire tornado passes a wooden house at the edge of the woods.",
               "U8": "The fire tornado rips the roof off a house.",
               "U9": "The fire tornado roars past a house as flames rise.",
               "U10": "A porch light flickers as the tornado passes.",
               "U11": "A garage stands beside the house under the orange sky."}
        for bid, t in bad.items():
            with self.subTest(beat=bid, text=t):
                self.assertTrue(gate(bid, t))

    def test_term_lists_only_fire_tornado(self):
        # _FIRE_TOR_* listeleri sadece ateş hortumunda; diğer yangın olayları ortak _FIRE_* listelerini kullanır
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(es))
        node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(getattr(t, "id", None) == "EVENT_BEATS" for t in n.targets))
        for k, v in zip(node.keys, node.values):
            names = {n.id for n in ast.walk(v) if isinstance(n, ast.Name)}
            tor = {n for n in names if n.startswith("_FIRE_TOR_")}
            with self.subTest(event=getattr(k, "id", None)):
                if getattr(k, "id", None) == "FIRE_TORNADO":
                    self.assertTrue(tor)
                else:
                    self.assertFalse(tor)

    def test_total_words_75_only_fire_tornado(self):
        self.assertEqual(es.TOTAL_WORDS, (40, 70))
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[E], (40, 75))
        self.assertNotIn(es.FACADE_FIRE, es.TOTAL_WORDS_BY_EVENT)
        key = len(es.EVENT_KEY_VISUAL[E].split())

        def story(total):
            s1 = "Three people run from the fire tornado on the road right below."
            s2 = "Burning debris slams into the SUV, which spins to a halt."
            base = "The tornado lifts burning brush and hurls it over the road in sparks".split()
            need = total - key - len(s1.split()) - len(s2.split())
            return {"slice_1_rest": s1, "slice_2": s2, "slice_3": " ".join((base + ["again"] * 40)[:need])}
        spec = es.build_spec(E, None, SPOTS[0], None, "T6", "U6", "SUV", 3)   # 17 Eki: U4 çıktı
        for total, ok in ((73, True), (75, True), (76, False), (81, False)):
            sl = story(total)
            self.assertEqual(len(es.plain_story(spec, sl).split()), total)
            with self.subTest(total=total):
                self.assertEqual("total_words" not in {i["rule"] for i in es.slice_issues(spec, sl)}, ok)

    def test_prompt_never_exceeds_175_words(self):
        # En uzun stil eki + 75 + 3 etiket ≤ 175; kapı da ateş hortumunda 175'i denetler (WORD_CAP_EVENTS)
        self.assertEqual(sorted(sk.EVENT_SKELETONS[E]["spots"]), sorted(SPOTS))
        longest = max(len(es.style_suffix(E, None, s, None, None).split()) for s in SPOTS)
        self.assertEqual(longest + 75 + 3, 175)   # 16 Eki: en uzun nokta 21 kelime, stil eki kısaldı (önceki 174)
        self.assertEqual(es.VOLC_MAX_PROMPT_WORDS, 175)
        self.assertIn(E, es.WORD_CAP_EVENTS)
        from core.trace_format import count_constraints
        for s in SPOTS:
            self.assertLessEqual(count_constraints(es.style_suffix(E, None, s, None, None))[0], 8)

    def test_word_budget_line(self):
        # 16 Eki: kilit cümle ortama göre 28-29 kelime; dilim bütçesi aynı (0-4s 10, 4-9s/9-15s 18, toplam 75)
        self.assertIn(E, es.BUDGET_EVENTS)
        for name, (key, spots) in ENVS.items():
            spec = es.build_spec(E, None, spots[0], None, "T1", "U6", "SUV", 3)   # 17 Eki: U3 çıktı
            self.assertEqual(spec["key_visual"], key)
            self.assertEqual(spec["fire_env"], name)
            n = len(key.split())
            self.assertIn(n, (28, 29))
            self.assertEqual(es.word_budget_line(spec),
                             f"WORD BUDGET: the opening sentence has {n} words; slice_1_rest 6 to 10 words, slice_2 10 "
                             "to 18 words, slice_3 10 to 18 words; the opening plus the three fields must total at "
                             "most 75 words.\n")
            self.assertLessEqual(n + 10 + 18 + 18, 75)

    def test_people_two_or_three_close_by(self):
        spec, sl = build("T6", "U6")   # 17 Eki: U4 çıktı
        self.assertFalse({i["rule"] for i in es.slice_issues(spec, sl)} - {"total_words"})
        codes = {i["rule"] for i in es.slice_issues(spec, {**sl, "slice_1_rest": "The smoke hangs over the road."})}
        self.assertTrue(codes & {"slice_flee", "slice_count"}, codes)
        far = "Three people run from the fire tornado across the distant field."
        self.assertIn("slice_near_camera", {i["rule"] for i in es.slice_issues(spec, {**sl, "slice_1_rest": far})})
        line = es.people_line(spec)
        self.assertIn("near the railing or in the street right below", line)   # 16 Eki (önceki "on the road right below")
        for n in range(200):
            self.assertIn(es.choose_people(E, None, random.Random(n)), (2, 3))
        self.assertEqual(es.NUMBER_WORDS[2], "two")
        spec2, sl2 = build("T1", "U6", people=2)
        self.assertTrue(sl2["slice_1_rest"].startswith("Two people"))
        self.assertFalse({i["rule"] for i in es.slice_issues(spec2, sl2)} - {"total_words"})

    def test_200_productions_free_paraphrase(self):
        # Sahte GPT madde metnini değil serbest/gerçek cümlelerden birini yazar; ilk denemede en az %90
        import core.creative_pipeline as cp
        rng = random.Random(15)
        # GPT'ye WORD BUDGET satırı gider (4-9s/9-15s en fazla 18 kelime): sahte GPT de bütçeye uyan cümleleri yazar
        pool = {b: [t for t in FREE[b] + HELD_OUT[b] + SHORT.get(b, []) + REJECTED_REAL.get(b, [])
                    if len(t.split()) <= 18]
                for b in FREE}
        self.assertTrue(all(len(v) >= 3 for v in pool.values()), {b: len(v) for b, v in pool.items()})
        people = ["{w} people run from the fire tornado on the road right below.",
                  "{w} drivers flee on foot near the railing.",
                  "{w} people sprint away just below the balcony.",
                  "{w} residents run from the fire tornado in the foreground."]

        async def gpt(system, user, **kw):
            line = dict(l.split(": ", 1) for l in user.splitlines() if ": " in l)
            w = line["PEOPLE RUNNING AWAY"].split()[0].capitalize()
            v = line["VEHICLE"].strip()
            b2 = next(b for b in es.EVENT_BEATS[E]["slice_2"]
                      if es.beat_text(E, "slice_2", b, v) == line["4-9s EVENT"])
            b3 = next(b for b in es.EVENT_BEATS[E]["slice_3"] if es.beat_text(E, "slice_3", b) == line["9-15s EVENT"])
            return {"slice_1_rest": rng.choice(people).format(w=w),
                    "slice_2": with_vehicle(rng.choice(pool[b2]), v), "slice_3": rng.choice(pool[b3])}
        es._BEAT_MEMORY.clear()
        first, longest = 0, 0
        for _ in range(200):
            scene = asyncio.run(cp.build_creative_scene("fire_disasters", E, [], [], gpt))
            spec, sl = scene["structure"]["spec"], scene["structure"]["slices"]
            self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
            self.assertIn(spec["people"], (2, 3))
            longest = max(longest, len(scene["prompt"].split()))
            first += len(scene["trace"]["attempts"]) == 1
        self.assertGreaterEqual(first, 180)
        self.assertLessEqual(longest, 175)
        es._BEAT_MEMORY.clear()


class TestFireTornadoEnvironments(unittest.TestCase):
    """16 Eki 2026, Bahadır: canlıda hortum ilk 10 sn boş yanan tarlada ilerledi, ev en sonda göründü. Ortam ekseni: sahne
    her zaman içinde ev olan ağaçlık bir yerleşim (orman kenarı, ağaçlık sokak, köy kenarı); açık arazi yok."""

    # Her yeni noktaya uygun, GPT tarzı serbest yakın insan cümleleri (4'er)
    NEAR = {
        "High balcony at the edge of a wooded neighborhood": [
            "Two neighbors sprint between the houses right below the balcony.",
            "Three people flee through the yard below, ducking under the trees.",
            "Two residents run down the street below, past the burning hedges.",
            "Three people dash away near the railing as embers swirl."],
        "Rooftop terrace above a wooded residential area": [
            "Two residents race across the yard below the terrace.",
            "Three people run between the houses just below.",
            "Two neighbors flee along the street below the rooftop.",
            "Three people sprint away in the garden below."],
        "High balcony over a tree-lined residential street": [
            "Two people sprint down the tree-lined street right below.",
            "Three residents flee along the sidewalk right below the balcony.",
            "Two neighbors run in the street below, shielding their faces.",
            "Three people dash away beneath the balcony."],
        "Upper-floor terrace above a street of houses": [
            "Two people run past the parked cars in the street below.",
            "Three residents flee just below the terrace.",
            "Two neighbors bolt across the street below.",
            "Three people scramble away in the foreground near the railing."],
        "Hillside terrace above a village": [
            "Two villagers run between the houses right below the terrace.",
            "Three people flee in the gardens below.",
            "Two villagers sprint down the street below the terrace.",
            "Three people run away just beneath the terrace."],
        "High balcony of a village house": [
            "Two villagers run down the street right below.",
            "Three people flee in the yard below the balcony.",
            "Two neighbors dash away under the balcony.",
            "Three villagers scramble between the houses below."],
    }
    FAR = ["Two people run far away on the hill.",
           "Two people sprint away from it near the road below.",
           "Three people flee down the distant road.",
           "Two people run toward the forest in the distance.",
           "Three villagers run across the valley far below.",
           "Two people run away on the road below."]
    COUNTRIES = es._EQ_BANNED[es._EQ_BANNED.index("turkey"):]

    def setUp(self):
        es._FIRE_TOR_ENV_MEMORY.clear()
        es._BEAT_MEMORY.clear()

    def tearDown(self):
        es._FIRE_TOR_ENV_MEMORY.clear()
        es._BEAT_MEMORY.clear()

    def test_keys_and_spots_settled_not_open_land(self):
        self.assertEqual(list(es.FIRE_TOR_ENVS), ["forest_edge", "tree_street", "village_woods"])
        self.assertEqual(sorted(sk.EVENT_SKELETONS[E]["spots"]), sorted(SPOTS))
        texts = []
        for name, env in es.FIRE_TOR_ENVS.items():
            key = env["key"]
            with self.subTest(env=name):
                self.assertTrue(es.find_terms(("house",), key), key)                          # ev
                self.assertTrue(es.find_terms(("tree", "forest", "woods"), key), key)        # ağaç/orman
                self.assertEqual(len(env["spots"]), 2)
            texts.append(key)
            for spot in env["spots"]:
                texts += [spot, sk.CAMERA_SPOTS[spot], sk.EVENT_SKELETONS[E]["spots"][spot]]
        texts += list(sk.FIRE_WEATHER)   # hava listesi aynı, arazi ima eden ifade yok
        for t in texts:
            with self.subTest(text=t):
                self.assertEqual(es.find_terms(es.FIRE_TOR_OPEN_LAND, t), [])
                self.assertEqual(es.find_terms(self.COUNTRIES, t), [])
                self.assertEqual(es.rain_words(t), [])
        self.assertEqual(sk.FIRE_WEATHER, ["hot dry wind and thick smoke haze", "gusty dry wind under an orange smoky sky",
                                           "heavy smoke and scorching still air"])

    def test_camera_rules_same_for_every_spot(self):
        for spot in SPOTS:
            with self.subTest(spot=spot):
                suffix = es.style_suffix(E, None, spot, None, None)
                self.assertTrue(suffix.startswith(f"Handheld footage shot by a person standing {sk.CAMERA_SPOTS[spot]}, "
                                                  "high vantage close to the fire tornado filling at least half the frame"))
                for rule in ("two or three people fleeing in the near foreground", "its top and smoke never cut off",
                             "slight hand shake", "one continuous shot, no zoom, no cuts"):
                    self.assertIn(rule, suffix)
                self.assertTrue(sk.CAMERA_SPOTS[spot].startswith("on "))

    def test_env_lru_never_repeats_back_to_back(self):
        rng = random.Random(7)
        seq = []
        for _ in range(300):
            name = es.choose_fire_env(rng)
            es.remember_fire_env(name)
            seq.append(name)
        self.assertEqual(set(seq), set(es.FIRE_TOR_ENVS))
        for a, b in zip(seq, seq[1:]):
            self.assertNotEqual(a, b)
        for a, b in zip(seq, seq[2:]):   # son 2 ortam elenir: 3 ortamda üçüncü üretim kalan ortam
            self.assertNotEqual(a, b)
        self.assertEqual(es.fire_env_of_spot("High balcony of a village house"), "village_woods")
        with self.assertRaises(es.StructureError):
            es.fire_env_of_spot("Balcony of a roadside house")

    def test_near_gate_new_spots(self):
        for spot, sents in self.NEAR.items():
            spec = es.build_spec(E, None, spot, None, "T1", "U6", "SUV", 2)   # 17 Eki: U3 çıktı
            for t in sents:
                n = 3 if t.startswith("Three") else 2
                spec = {**spec, "people": n}
                codes = {i["rule"] for i in es.slice_issues(spec, {"slice_1_rest": t, "slice_2": FREE["T1"][0],
                                                                   "slice_3": FREE["U6"][0]})}
                with self.subTest(spot=spot, text=t):
                    self.assertFalse(codes & {"slice_near_camera", "slice_flee", "slice_count"}, codes)
        spec = es.build_spec(E, None, SPOTS[4], None, "T1", "U6", "SUV", 2)
        for t in self.FAR:
            spec = {**spec, "people": 3 if t.startswith("Three") else 2}
            codes = {i["rule"] for i in es.slice_issues(spec, {"slice_1_rest": t, "slice_2": FREE["T1"][0],
                                                               "slice_3": FREE["U6"][0]})}
            with self.subTest(far=t):
                self.assertIn("slice_near_camera", codes)
        # çığ/deprem yakınlık listesi değişmedi
        self.assertIs(es.SLICE_RULES[es.AVALANCHE_VILLAGE][-1], es._AVA_NEAR_RULE)
        self.assertNotIn("between the houses", es._AVA_NEAR)

    def test_scenes_rotate_env_and_label(self):
        import core.creative_pipeline as cp
        from core.trace_format import format_final_prompt, format_generation
        pool = {b: [t for t in FREE[b] + HELD_OUT[b] + SHORT.get(b, []) if len(t.split()) <= 18] for b in FREE}

        async def gpt(system, user, **kw):
            line = dict(l.split(": ", 1) for l in user.splitlines() if ": " in l)
            w = line["PEOPLE RUNNING AWAY"].split()[0].capitalize()
            v = line["VEHICLE"].strip()
            b2 = next(b for b in es.EVENT_BEATS[E]["slice_2"] if es.beat_text(E, "slice_2", b, v) == line["4-9s EVENT"])
            b3 = next(b for b in es.EVENT_BEATS[E]["slice_3"] if es.beat_text(E, "slice_3", b) == line["9-15s EVENT"])
            return {"slice_1_rest": f"{w} people run away right below.", "slice_2": with_vehicle(pool[b2][0], v),
                    "slice_3": pool[b3][0]}
        envs = []
        for _ in range(30):
            scene = asyncio.run(cp.build_creative_scene("fire_disasters", E, [], [], gpt))
            spec, st = scene["structure"]["spec"], scene["structure"]
            envs.append(spec["fire_env"])
            self.assertIn(scene["spot"], es.FIRE_TOR_ENVS[spec["fire_env"]]["spots"])
            self.assertTrue(scene["prompt"].startswith(f"0-4s: {es.FIRE_TOR_ENVS[spec['fire_env']]['key']} "))
            self.assertEqual(st["place"], sk.EVENT_SKELETONS[E]["spots"][scene["spot"]])   # GPT'ye giden PLACE
            self.assertEqual(st["environment"], es.fire_env_label(spec["fire_env"], scene["spot"]))
            onay = format_final_prompt({"prompt": scene["prompt"], "story": scene["story"],
                                        "style_suffix": scene["style_suffix"], "environment": st["environment"]})[1]
            self.assertIn(f"Ortam: {es.FIRE_TOR_ENVS[spec['fire_env']]['label']} ({spec['fire_env']}) · kamera = "
                          f"{scene['spot']}", onay)
            detail = "\n".join(b for _, b in format_generation(scene["trace"]))
            self.assertIn(f"Yer: {scene['spot']} · ortam: {es.FIRE_TOR_ENVS[spec['fire_env']]['label']} · hava: ",
                          detail)
        for a, b in zip(envs, envs[1:]):
            self.assertNotEqual(a, b)
        self.assertEqual(set(envs), set(es.FIRE_TOR_ENVS))

    def test_other_structured_events_have_no_fire_env(self):
        spec = es.build_spec(es.WILDFIRE, None, "Balcony of a hillside house", None, "K1", "L3", "SUV", 3)
        self.assertNotIn("fire_env", spec)
        self.assertEqual(spec["key_visual"], es.EVENT_KEY_VISUAL[es.WILDFIRE])


if __name__ == "__main__":
    unittest.main()
