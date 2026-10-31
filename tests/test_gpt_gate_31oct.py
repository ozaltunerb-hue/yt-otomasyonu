#!/usr/bin/env python3
"""
31 Eki 2026, Bahadır (üretim bulguları): GPT çıktısını denetleyen kod kapıları. GPT'ye yeni hint kuralı yok; kapı reddeder,
mevcut geri bildirim mekanizmasıyla yeniden dener ya da kod yedeğine düşer.
- çapa: birleşik hedefli beat'te asıl hedef (K9 "burning house", R9 "corner shop"...) cümlede zorunlu,
- yangın olaylarında torrent / disintegrat / explod kökleri yasak,
- insan öznesiyle "scatter" yasak (enkaz cümleleri serbest),
- araca havuzda olmayan ayrılma/yuvarlanma hareketi yasak ("as it rolls downhill").
Ayrıca karaya vurur E5 ve bombalar R9 yeni metni, kamera cümlesi × ortam tutarlılığı. Ağ yok, Kie/GPT yok.
"""
import os
import re
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.frame_axis as fx
import core.skeleton_pipeline as sk

NEW_RULES = {"beat_anchor", "fire_banned_root", "people_scatter", "invented_vehicle_move"}
WF, LF, VB = es.WILDFIRE, es.LANDFALL, es.VOLCANIC_BOMBS
EMB, BALC = "Embankment above the village road", "Balcony of a hillside house"
HT = "Hillside terrace facing the erupting volcano"

# Bugünkü (31 Eki) Onay metinleri birebir (Notion "Konu"; 0-4s kilit cümlesi çıkarıldı). (olay, spot, beat_2, beat_3,
# araç, kişi, açılış, ortam, dilimler, beklenen yeni kurallar)
ONAY = {
    "a_b_K9_L3": (WF, EMB, "K9", "L3", "delivery truck", 5, "B", "D", {
        "slice_1_rest": "Five people sprint away from the flames engulfing the grove.",
        "slice_2": "The delivery truck accelerates, narrowly avoiding the collapsing roof that crumbles onto the stone "
                   "road.",
        "slice_3": "The fiery torrent blazes through, consuming a garden, as the trailer disintegrates in a burst of "
                   "flames."}, {"beat_anchor", "fire_banned_root"}),
    "c_K2_L5": (WF, EMB, "K2", "L5", "white van", 3, None, None, {
        "slice_1_rest": "Three people scatter in panic, fleeing the advancing inferno.",
        "slice_2": "A flaming tree collapses onto a van, crushing its roof instantly.",
        "slice_3": "Another house ignites, its roof exploding violently, casting debris toward the street."},
        {"people_scatter", "fire_banned_root"}),
    "g_R9_T9": (VB, HT, "R9", "T9", None, 4, "B", "hillside_town", {
        "slice_1_rest": "Four people run away from the falling rocks.",
        "slice_2": "A glowing rock crashes onto the street, sending fiery fragments scattering across the roadway.",
        "slice_3": "The next impact engulfs a truck, flames rapidly consuming the cab as it rolls downhill."},
        {"beat_anchor", "invented_vehicle_move"}),   # R9 artık köşe dükkânı: eski yol cümlesi çapasız
    "ok_C1_E1": (LF, "Residential coastal district", "C1", "E1", "pickup truck", 5, "C", "C", {
        "slice_1_rest": "Five people run away from the tornado.",
        "slice_2": "The tornado shoves the pickup truck sideways, crashing it into the stone quay's far curb.",
        "slice_3": "It tears the roof from a nearby waterfront building, scattering debris across the quay."}, set()),
    "ok_K1_L7": (WF, BALC, "K1", "L7", "pickup truck", 4, "C", "E", {
        "slice_1_rest": "Four people run away from the flames.",
        "slice_2": "The pickup truck reverses sharply as the flaming eucalyptus tree smashes onto the road ahead.",
        "slice_3": "Across the street, the next house is engulfed, its roof collapsing in burning debris."}, set()),
}


def _spec(event, spot, b2, b3, vehicle, people, opening, env):
    volc = env if event in es.VOLC_ENV_EVENTS else None
    scene = None if event in es.VOLC_ENV_EVENTS else env
    if vehicle is None and es.uses_vehicle(event):
        vehicle = es.event_vehicles(event, None)[0][0]
    return es.build_spec(event, None, spot, None, b2, b3, vehicle, people, None, volc, None, scene, opening)


def new_rules(event, spot, b2, b3, vehicle, people, opening, env, slices):
    spec = _spec(event, spot, b2, b3, vehicle, people, opening, env)
    return {i["rule"] for i in es.slice_issues(spec, slices)} & NEW_RULES


class TestTodayOnay(unittest.TestCase):
    def test_bad_rejected_good_pass(self):
        # a, b, c, g reddedilir; bugünkü iyi Onay'lar (C1+E1, K1+L7) yeni kapılardan geçer
        for name, (e, spot, b2, b3, veh, n, op, env, slices, expected) in ONAY.items():
            with self.subTest(onay=name):
                self.assertEqual(new_rules(e, spot, b2, b3, veh, n, op, env, slices), expected)

    def test_k2_l5_without_exploding_still_scatter(self):
        # K2+L5'ten "exploding" cümlesi çıkarılınca yangın kökü kalmaz, "scatter" reddi durur
        e, spot, b2, b3, veh, n, op, env, slices, _ = ONAY["c_K2_L5"]
        sl = {**slices, "slice_3": "Another house ignites and its roof tiles burst apart in the heat."}
        self.assertEqual(new_rules(e, spot, b2, b3, veh, n, op, env, sl), {"people_scatter"})

    def test_why_k9_passed_before(self):
        # K9 araçlı: yumuşak kapının nesnesi araç; eski sıkı grup _FIRE_HOUSE "roof" içerdiği için o da geçerdi
        spec = _spec(*ONAY["a_b_K9_L3"][:8])
        sl = ONAY["a_b_K9_L3"][8]
        self.assertEqual(es.beat_object_terms(spec, "slice_2", "K9"), es.spec_vehicle_terms(spec))
        self.assertNotIn("beat_vehicle", {i["rule"] for i in es.soft_beat_issues(spec, sl)})
        self.assertIn("roof", es.find_terms(es.EVENT_BEATS[WF]["slice_2"]["K9"]["terms"][1], sl["slice_2"]))
        fixed = {**sl, "slice_2": "The delivery truck speeds past as the roof of a burning house collapses onto the "
                                  "road behind it."}
        self.assertEqual(es.beat_anchor_issues(spec, fixed), [])


class TestRules(unittest.TestCase):
    def test_anchors_only_on_known_beats_and_in_own_text(self):
        self.assertEqual(es.BEAT_ANCHORS[WF]["K9"], ("burning house", "burning home"))
        for e, anchors in es.BEAT_ANCHORS.items():
            for bid, anchor in anchors.items():
                beat = es.EVENT_BEATS[e]["slice_2"].get(bid) or es.EVENT_BEATS[e]["slice_3"].get(bid)
                with self.subTest(beat=(e, bid)):
                    self.assertTrue(es.find_terms(anchor, beat["text"]))
                    # araç terimleriyle çakışmaz (hedef seçilen araç sanılmasın)
                    for veh, terms in (es.event_vehicles(e, es.structure_views(e)[0]) if es.uses_vehicle(e) else []):
                        self.assertFalse(set(anchor) & set(terms), veh)

    def test_fire_roots_only_in_fire_events(self):
        self.assertEqual(es.fire_root_words("The torrential flames explode and the trailer disintegrated."),
                         ["torrential", "explode", "disintegrated"])
        sl = {"slice_1_rest": "Four people run away from the falling rocks.",
              "slice_2": "A house across the street is struck by a glowing rock, exploding the wall outward.",
              "slice_3": "A glowing rock bounces along the road and slams into a parked car."}
        # volkan (yangın değil): kök serbest (bugünkü R8+T2 Onay'ı)
        self.assertNotIn("fire_banned_root", new_rules(VB, HT, "R8", "T2", None, 4, None, None, sl))

    def test_scatter_people_only(self):
        for t in ("Three people scatter in panic.", "Six people scatter in the street below.",
                  "The pedestrians quickly scatter.", "Residents, scattering in every direction.",
                  "The crowd scatters."):
            self.assertTrue(es.people_scatter(t), t)
        for t in ("The tornado tears the roof off and scatters the pieces across the street.",
                  "The stones scatter across the road as five people run.",
                  "Five people run as debris scatters behind them.",
                  "It tears the roof from a nearby building, scattering debris across the quay."):
            self.assertEqual(es.people_scatter(t), [], t)

    def test_invented_move(self):
        t9 = es.EVENT_BEATS[VB]["slice_3"]["T9"]["text"]
        self.assertEqual(es.invented_vehicle_moves("The next impact engulfs a truck, flames rapidly consuming the cab "
                                                   "as it rolls downhill.", t9), ["rolls downhill"])
        # eş anlamlı ayrılma serbest (ateş hortumu T7 "races away" -> GPT "speeds away", 16 Eki Onay'ı)
        t7 = es.EVENT_BEATS[es.FIRE_TORNADO]["slice_2"]["T7"]["text"]
        self.assertEqual(es.invented_vehicle_moves("The delivery truck speeds away, as flaming debris crashes mere feet "
                                                   "behind.", t7), [])
        # özne araç değil: kaya, çamur, helikopter
        for t in ("A boulder rolls downhill into a parked car.", "The mud rolls down the street toward the cars.",
                  "The helicopter pulls away as the flames roar back."):
            self.assertEqual(es.invented_vehicle_moves(t, ""), [], t)
        for t in ("The SUV drives off as the roof collapses.", "The van speeds away from the fire.",
                  "The pickup careens down the road."):
            self.assertTrue(es.invented_vehicle_moves(t, ""), t)

    def test_fallback_pool_clean(self):
        self.assertEqual(es.pool_lint_errors(), [])
        for pool in list(es.FALLBACK_PEOPLE.values()) + list(es.FALLBACK_PEOPLE_FIRE_ENV.values()):
            for t in pool:
                self.assertNotIn("scatter", t)


class TestPoolTexts(unittest.TestCase):
    def test_new_texts(self):
        self.assertEqual(es.EVENT_BEATS[LF]["slice_3"]["E5"]["text"],
                         "the tornado lifts a wooden kiosk off the waterfront and smashes it into the building across the street")   # 31 Eki (2)
        self.assertEqual(es.EVENT_BEATS[VB]["slice_2"]["R9"]["text"],
                         "a glowing rock crashes through the front of a corner shop down the street and its wall caves in")
        self.assertNotIn((LF, "E5"), es.POOL_LINT_GRANDFATHERED)
        for e, slot, bid in ((LF, "slice_3", "E5"), (VB, "slice_2", "R9")):
            text = es.EVENT_BEATS[e][slot][bid]["text"]
            self.assertEqual(es.pool_lint_hits(text), [])
            self.assertEqual(es.missing_term_groups(es.EVENT_BEATS[e][slot][bid]["terms"], text), [])
        # açılış B "roof of the house across the street" ile aynı yapı değil
        self.assertNotIn("house", es.EVENT_BEATS[VB]["slice_2"]["R9"]["text"])

    def test_r9_does_not_steal_shop_beats(self):
        # nesne grubu duvar: korunan R3/R4 dükkân cümleleri R9'a benzetilmez
        spec = _spec(VB, HT, "R4", "T2", None, 4, None, None)
        sl = {"slice_2": "A volcanic bomb plows into a shop sign above an old store, sending shards clattering onto the "
                         "pavement.", "slice_3": "A glowing rock bounces along the road and slams into a parked car."}
        self.assertEqual(es.soft_beat_issues(spec, sl), [])


class TestCameraEnvironment(unittest.TestCase):
    SETTLEMENT = re.compile(r"\b(village|town|suburb|suburban|downtown|city)\b", re.IGNORECASE)

    def test_camera_phrases_neutral(self):
        # 31 Eki: ortam ekseni olan olayların kamera yer cümlesinde yerleşim türü yok (ortam ne olursa olsun çelişmez)
        for spot in ("Hillside terrace facing the erupting volcano", "Rooftop terrace facing the erupting volcano",
                     "Balcony of a village house facing the erupting volcano", EMB, "Hilltop terrace above a coastal town"):
            self.assertIsNone(self.SETTLEMENT.search(sk.CAMERA_SPOTS[spot]), spot)
        self.assertIsNone(self.SETTLEMENT.search(sk.METEOR_CAMERA["Hilltop terrace above a coastal town"]))
        self.assertEqual(fx.SPOT_FRAME[LF]["Downtown city center"][2], "on a flat rooftop above the waterfront")
        for e in (WF, es.HELICOPTER):
            self.assertEqual(fx.SPOT_FRAME[e][EMB][2], "on a roadside embankment above the road")

    def test_volcano_suburb_camera_has_no_village(self):
        for e in es.VOLC_ENV_EVENTS:
            for spot in sk.view_spots(e, None):
                for env in sk.VOLC_ENVS:
                    cam = sk.volcano_camera(spot, e, env)
                    with self.subTest(event=e, spot=spot, env=env):
                        if env != "mountain_village":
                            self.assertNotIn("village", cam)
                        if env != "suburb":
                            self.assertNotIn("suburb", cam)


if __name__ == "__main__":
    unittest.main()
