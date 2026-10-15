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
import os
import random
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.skeleton_pipeline as sk

E = es.FIRE_TORNADO
SPOTS = ("Overlook above the burning valley road", "Balcony of a roadside house")
VEHICLES = ("pickup truck", "small car", "white van", "SUV")

REJECTED_REAL = {
    "T6": [
        'Flaming debris collides with the SUV, causing it to skid violently until it halts blocking the road.',
        "A shower of fiery debris smashes into the SUV's side, causing it to spin wildly before coming to rest across the road.",
        "Flaming debris crashes into the SUV's flank, causing it to spin wildly before grinding to a halt in the road.",
    ],
    "U4": [
        'The tornado engulfs a heap of burning brush, ejecting it in a blazing arc of sparks onto the roadway.',
        'A fierce surge of the tornado draws in a burning brush pile, hurling it across the road in a dazzling spray of embers.',
        'The tornado draws up burning brush, hurling it across the road in a spectacular shower of fiery sparks, still spinning.',
    ],
}
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
    "T3": [
        'The SUV rises into the fiery column, twirls around, and slams back onto the asphalt amid a burst of sparks.',
        'The van is carried aloft, rotating wildly, then smashes onto the road as sparks explode around it.',
        'Lifted high by the vortex, the small car whirls end over end before plunging onto the road in a spray of embers.',
        'The fire whirl hoists the pickup truck skyward, spins it, and drops it hard onto the road, scattering sparks.',
        'The tornado sucks the SUV off the ground, sends it spiraling, and hurls it down onto the road in a cascade of sparks.',
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
    "U3": [
        'The colossal fire whirl engulfs a roadside barn and rips it apart, burning boards spiraling up into the funnel.',
        'A wooden barn near the road disappears into the towering vortex, its flaming planks torn loose and lifted.',
        'The giant tornado smashes a timber barn to pieces and sucks the blazing wreckage up into its column.',
        'The fire tornado swallows a barn by the roadside, shredding its walls as burning boards whirl upward.',
        'A whole barn collapses into the huge fire column, its burning timbers ripped away and flung high.',
    ],
    "U4": [
        'The fire whirl inhales a heap of blazing scrub and flings it over the road in a burst of sparks.',
        'A mound of burning brush is pulled into the vortex and sprayed across the road as a shower of embers.',
        'The tornado lifts a pile of flaming undergrowth and blasts it across the asphalt in a jet of sparks.',
        'Burning shrubs are sucked into the spinning column and hurled over the road in a cascade of glowing cinders.',
        'The vortex scoops up a stack of smoldering brushwood and spews it across the road in a fountain of sparks.',
    ],
    "U5": [
        'The giant fire whirl plows through a huge stack of firewood and flings the flaming logs across the field.',
        'A massive woodpile is ripped apart by the towering vortex, its burning logs hurled high over the meadow.',
        'The colossal tornado scatters a big log pile, tossing blazing logs far across the field.',
        'Burning logs from a huge woodpile are sucked up by the fire tornado and thrown across the open field.',
        'The fire tornado tears into a big pile of logs and launches them, ablaze, high over the field.',
    ],
    "U6": [
        'The fire whirl rolls over a parked caravan and flips it aside amid billowing flames and smoke.',
        'A parked trailer is overturned by the passing vortex, vanishing in a cloud of fire and smoke.',
        'The spinning flames engulf a parked camper and throw it to the side in a burst of smoke and fire.',
        'The tornado crosses a parked trailer and knocks it over in a swirl of flames and black smoke.',
        'The burning vortex slams into a parked caravan and tips it onto its side inside a cloud of fire and smoke.',
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
    "T3": [
        'The fire tornado lifts the SUV high, spinning it violently before slamming it back down on the road in a burst of sparks.',
        'Swept into the air, the white van twists and tumbles, then crashes onto the road showering sparks.',
        'The small car is hurled upward by the inferno, spirals around, and smashes down onto the road amid sparks.',
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
    "U3": [
        'The towering fire whirl tears a wooden barn apart, sending its blazing planks spinning up into the sky.',
        'The massive vortex devours a barn beside the road, ripping its roof and walls away in flames.',
        'A roadside shed is flattened by the giant fire tornado, its burning boards hurled up into the column.',
    ],
    "U4": [
        'The fire tornado sucks in a pile of burning brush and sprays it across the road in a fountain of sparks.',
        'A heap of flaming scrub is drawn into the vortex and spat out across the road in a burst of embers.',
        'The tornado swallows a burning brush pile and hurls it over the road in a glowing shower of sparks.',
    ],
    "U5": [
        'The vortex rips through the stacked firewood, sending burning logs cartwheeling across the field.',
        'A huge woodpile is blasted apart by the fire whirl, its flaming logs flying high above the grass.',
        'The giant tornado hurls burning logs from a woodpile high over the field.',
    ],
    "U6": [
        'The fire tornado rolls over a parked trailer and flips it aside in a cloud of fire and smoke.',
        'A parked caravan is tossed aside by the vortex, disappearing in flames and smoke.',
        'The swirling flames sweep across a parked trailer, overturning it in a burst of fire and smoke.',
    ],
}

# 15 Eki (2): WORD BUDGET'e (4-9s/9-15s en fazla 18 kelime) uyan kısa serbest cümleler; kapı değiştirilmeden yazıldı
SHORT = {
    "T3": ["The giant vortex hoists the SUV skyward, twirls it, and slams it down onto the road.",
           "Sucked into the fire column, the van spins high and crashes back onto the asphalt.",
           "The pickup truck is lifted aloft, whirls around, and plunges onto the road in sparks."],
    "T6": ["Huge burning wreckage hits the van broadside; it spins and halts across the road.",
           "A mass of flaming debris rams the SUV, spinning it to a stop across the lane."],
    "U4": ["The giant vortex sucks in a burning brush pile and sprays it over the road as sparks.",
           "A heap of flaming scrub is drawn up and spat across the road in a shower of embers.",
           "The towering fire whirl swallows burning undergrowth and hurls it over the road in sparks."],
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
    "T3": [
        'The huge fire whirl picks up the van, spins it, and drops it onto the road in sparks.',
        'The SUV rises into the air in the giant vortex, whirls, and crashes back onto the road.',
        'Carried aloft by the fire tornado, the pickup truck twirls and slams down onto the asphalt.',
        'The small car is torn off the road, spins high in the fire column, and plunges onto the road.',
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
    "U3": [
        'The giant fire tornado knocks down a wooden barn, its burning planks whirling into the column.',
        'A roadside barn is knocked over by the towering vortex and its blazing boards fly upward.',
        'The huge fire whirl knocks the barn down and sucks the burning planks into its column.',
    ],
    "U6": [
        'The colossal fire whirl knocks over a parked trailer in a cloud of fire and smoke.',
        'A parked caravan is knocked over by the giant vortex amid flames and smoke.',
        'The huge fire whirl knocks the trailer onto its side in a burst of fire and smoke.',
    ],
}


def slot(bid):
    return "slice_2" if bid[0] == "T" else "slice_3"


def terms(bid):
    return es.EVENT_BEATS[E][slot(bid)][bid]["terms"]


def with_vehicle(text, vehicle):
    for v in ("pickup truck", "small car", "white van", "SUV", "van"):
        if v in text:
            return text.replace("white van" if v == "van" and "white van" in text else v, vehicle, 1)
    return text


def build(b2, b3, vehicle="SUV", spot=SPOTS[0], s2=None, s3=None, s1=None, people=3):
    spec = es.build_spec(E, None, spot, None, b2, b3, vehicle, people)
    word = es.NUMBER_WORDS[people].capitalize()
    sl = {"slice_1_rest": s1 or f"{word} people run from the fire tornado on the road right below.",
          "slice_2": s2 or with_vehicle(FREE[b2][0], vehicle), "slice_3": s3 or FREE[b3][0]}
    return spec, sl


KEY = ("A colossal fire tornado, several times taller than the tallest buildings and trees, tears across the burning "
       "roadside, its wide base engulfing a field of flames.")
CAMERA = ("Handheld footage shot by a person standing {spot}, high vantage close to the towering fire tornado filling "
          "at least half of the frame, its top and smoke cloud never cut off, two or three people fleeing it in the "
          "near foreground; slight hand shake, the camera pans to follow the fire tornado; one continuous shot, no "
          "zoom, no cuts.")
POOL = ({"T1": "the towering fire tornado lifts the {vehicle} off the road and flings it into a burning tree",
         "T2": "the huge fire tornado hurls a whole burning tree trunk onto the {vehicle}, crushing its roof",
         "T3": "the {vehicle} is sucked up into the towering fire tornado, spins, and crashes down onto the road in "
               "sparks",
         "T4": "the {vehicle} is shoved sideways as the huge base of the fire tornado sweeps past right behind it",
         "T5": "the huge fire tornado rolls the {vehicle} over onto its roof and it bursts into flames",
         "T6": "huge flaming debris flung by the towering tornado slams into the {vehicle}, which spins and stops "
               "across the road"},
        {"U1": "the towering fire tornado rips the burning roof off a house and sucks the sheets into its column",
         "U2": "the huge fire tornado uproots a cluster of burning trees and flings their trunks down the road",
         "U3": "the towering fire tornado swallows a wooden barn and tears it to pieces, burning planks whirling into "
               "the column",
         "U4": "the towering tornado sucks up a huge burning brush pile and spits it across the road in sparks",
         "U5": "the huge fire tornado tears through a big woodpile and hurls the burning logs high across the field",
         "U6": "the towering fire tornado sweeps over a parked trailer and tosses it aside in fire and smoke"})


class TestFireTornadoGate(unittest.TestCase):
    def test_key_camera_pool_locked(self):
        # 15 Eki (2), Bahadır: dev hortum (ölçek kıyası), yüksek ve yakın kamera, ön planda 2-3 kaçan kişi
        self.assertEqual(es.EVENT_KEY_VISUAL[E], KEY)
        self.assertLessEqual(len(KEY.split()), 26)
        for spot in SPOTS:
            with self.subTest(spot=spot):
                self.assertTrue(es.style_suffix(E, None, spot, None, None).startswith(
                    CAMERA.format(spot=sk.CAMERA_SPOTS[spot]) + " " + sk.FIRE_TORNADO_GUARDRAILS))
        b = es.EVENT_BEATS[E]
        self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, POOL[0])
        self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, POOL[1])
        self.assertEqual(b["excluded_pairs"], {("T1", "U2"), ("T2", "U2"), ("T4", "U4"), ("T2", "U5")})
        self.assertEqual(b["excluded_spots"], {"U1": {"Balcony of a roadside house"}})
        self.assertEqual(sk.count_range(E, None), (2, 3))

    def test_beats_big_targets_and_size(self):
        # Her maddede hortumun büyüklüğü; cam, ince direk, tel, çit, tabela hedef değil
        size = ("towering", "huge", "colossal", "giant", "swallow")
        small = ("glass", "window", "windshield", "pole", "wire", "cable", "fence", "sign", "billboard", "railing",
                 "guardrail", "ember")
        for sl in POOL:
            for bid, text in sl.items():
                with self.subTest(beat=bid):
                    self.assertTrue(es.find_terms(size, text), text)
                    self.assertEqual(es.find_terms(small, text), [], text)

    def test_rejected_real_gpt_sentences_pass(self):
        # 15 Eki 10:44: 3 denemede reddedilen gerçek GPT cümleleri kendi maddesinde geçer
        for bid, sents in REJECTED_REAL.items():
            for t in sents:
                with self.subTest(beat=bid, text=t):
                    self.assertEqual(es.missing_term_groups(terms(bid), t), [])
        for t in REJECTED_REAL["T6"]:
            spec, sl = build("T6", "U4", "SUV", s2=t, s3=REJECTED_REAL["U4"][1])
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
                    self.assertEqual(es.missing_term_groups(terms(bid), t), [])
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
                        self.assertTrue(es.missing_term_groups(terms(x), t))
        # "spinning/whirling" hortumun sıfatı: T1 cümlesi T3 (iniş yok), U1 cümlesi T6 (araç yok) sayılmaz
        self.assertTrue(es.missing_term_groups(terms("T3"), FREE["T1"][3]))
        self.assertTrue(es.missing_term_groups(terms("T6"), FREE["U1"][4]))

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
                    self.assertEqual(es.missing_term_groups(terms(bid), t), [])
                    self.assertNotEqual(t.lower().split()[:4], beat.split()[:4])
                    for o in ids:   # başka madde sayılmaz (yasak çiftler hariç)
                        if o != bid and (o, bid) not in ex:
                            self.assertTrue(es.missing_term_groups(terms(o), t), (o, t))

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
                    self.assertTrue(es.missing_term_groups(terms(bid), t))

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
                    self.assertTrue(es.missing_term_groups(terms(bid), t))
        bad = {"T1": "The van is pushed into a burning tree by the swirling flames.",
               "T2": "A burning tree stands beside the SUV on the road.",
               "T3": "The SUV spins on the road as the flames swirl around it.",
               "T4": "The SUV waits on the road as the fire tornado looms ahead.",
               "T5": "The fire tornado rolls past the van and smoke surrounds it.",
               "T6": "The SUV spins and stops across the road as the flames swirl.",
               "U3": "The fire tornado moves toward a wooden barn by the road.",
               "U4": "A pile of burning brush glows beside the road.",
               "U5": "A big woodpile burns quietly at the edge of the field.",
               "U6": "A parked trailer stands near the burning road."}
        for bid, t in bad.items():
            with self.subTest(beat=bid, text=t):
                self.assertTrue(es.missing_term_groups(terms(bid), t))

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
        spec = es.build_spec(E, None, SPOTS[0], None, "T6", "U4", "SUV", 3)
        for total, ok in ((73, True), (75, True), (76, False), (81, False)):
            sl = story(total)
            self.assertEqual(len(es.plain_story(spec, sl).split()), total)
            with self.subTest(total=total):
                self.assertEqual("total_words" not in {i["rule"] for i in es.slice_issues(spec, sl)}, ok)

    def test_prompt_never_exceeds_175_words(self):
        # En uzun stil eki + 75 + 3 etiket ≤ 175; kapı da ateş hortumunda 175'i denetler (WORD_CAP_EVENTS)
        self.assertEqual(sorted(sk.EVENT_SKELETONS[E]["spots"]), sorted(SPOTS))
        longest = max(len(es.style_suffix(E, None, s, None, None).split()) for s in SPOTS)
        self.assertEqual(longest + 75 + 3, 174)
        self.assertEqual(es.VOLC_MAX_PROMPT_WORDS, 175)
        self.assertIn(E, es.WORD_CAP_EVENTS)
        from core.trace_format import count_constraints
        for s in SPOTS:
            self.assertLessEqual(count_constraints(es.style_suffix(E, None, s, None, None))[0], 8)

    def test_word_budget_line(self):
        # Kilit cümle 26 kelime: GPT'ye dilim bütçesi (0-4s 10, 4-9s/9-15s 18, toplam 75)
        self.assertIn(E, es.BUDGET_EVENTS)
        line = es.word_budget_line({"event": E, "key_visual": es.EVENT_KEY_VISUAL[E]})
        self.assertEqual(line, "WORD BUDGET: the opening sentence has 26 words; slice_1_rest 6 to 10 words, slice_2 10 "
                               "to 18 words, slice_3 10 to 18 words; the opening plus the three fields must total at "
                               "most 75 words.\n")

    def test_people_two_or_three_close_by(self):
        spec, sl = build("T6", "U4")
        self.assertFalse({i["rule"] for i in es.slice_issues(spec, sl)} - {"total_words"})
        codes = {i["rule"] for i in es.slice_issues(spec, {**sl, "slice_1_rest": "The smoke hangs over the road."})}
        self.assertTrue(codes & {"slice_flee", "slice_count"}, codes)
        far = "Three people run from the fire tornado across the distant field."
        self.assertIn("slice_near_camera", {i["rule"] for i in es.slice_issues(spec, {**sl, "slice_1_rest": far})})
        line = es.people_line(spec)
        self.assertIn("near the railing or on the road right below", line)
        for n in range(200):
            self.assertIn(es.choose_people(E, None, random.Random(n)), (2, 3))
        self.assertEqual(es.NUMBER_WORDS[2], "two")
        spec2, sl2 = build("T1", "U3", people=2)
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


if __name__ == "__main__":
    unittest.main()
