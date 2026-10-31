#!/usr/bin/env python3
"""
31 Eki 2026 (3), Bahadır: "kanıtlı formül" kuralı + üretim günü düzeltmeleri.
- Kanıtlı / deneme ayrımı (core.proven_axes): rotasyonda sadece KANITLI değerler + yetersizlik koruması; pencere
  kadrajı ve volkan açılış D hiçbir zaman; aday hiç tükenmez.
- GPT kapısı ekleri (gpt_added_issues): scramble, volkan kökleri, insan yönü, ses, soyut final, helikopter suyu, araç
  hareketi. Seçilen beat/kilit/açılış metninde geçen kelime ve kod yedeğinin insan cümlesi muaf.
- Zayıf finaller (heyelan M3/M4, cephe N1, helikopter F5), helikopter su tarifi, cephe spot-ortam tutarlılığı.
Ağ yok, Kie/GPT yok.
"""
import os
import random
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.frame_axis as fx
import core.opening_axis as ox
import core.proven_axes as pa
import core.scene_env as sv
import core.skeleton_pipeline as sk

MUD, SLOPE, HELI, FACADE = es.MUDSLIDE, es.SLOPE, es.HELICOPTER, es.FACADE_FIRE
VB, PY, WF, LF = es.VOLCANIC_BOMBS, es.PYROCLASTIC, es.WILDFIRE, es.LANDFALL
ADDED = {"people_scramble", "volcano_banned_root", "people_uphill", "sound_word", "abstract_final",
         "heli_water_shape", "vehicle_motion"}

# 31 Eki Onay metinleri birebir (Notion "Konu"; 0-4s açılış cümlesi çıkarıldı). (olay, açılış harfi, b2, b3, araç, kişi,
# dilimler, beklenen kurallar)
ONAY = {
    "heyelan_H6_M3": (MUD, "D", "H6", "M3", "SUV", 3, {
        "slice_1_rest": "Three people scramble to higher ground, avoiding the rushing mud.",
        "slice_2": "The SUV is swept forward, embedding its front into a house's steps.",
        "slice_3": "A surge of mud pushes the parked cars downhill, cascading in waves."},
        {"people_scramble", "people_uphill", "vehicle_motion"}),
    "heyelan_H2_M7": (MUD, "B", "H2", "M7", "pickup truck", 4, {
        "slice_1_rest": "Four people sprint away from the approaching mud.",
        "slice_2": "The swirling torrent lifts the pickup truck, spinning it down the hill.",
        "slice_3": "A forceful surge slams into a house, breaching its walls with muddy wreckage."},
        {"vehicle_motion"}),
    "heyelan_H1_M4": (MUD, "C", "H1", "M4", "white van", 6, {
        "slice_1_rest": "Six people run away from the mud.",
        "slice_2": "The van is shoved sideways, crashing into the parked SUV with a loud thud.",
        "slice_3": "A tall tree is ripped from the ground and swept swiftly down the street."},
        {"sound_word"}),
    "heyelan_H4_M9": (MUD, "D", "H4", "M9", "SUV", 3, {
        "slice_1_rest": "Three people scramble uphill, desperately avoiding the cascading sludge.",
        "slice_2": "The relentless mud drives the SUV sideways, crushing it against parked cars lining the street.",
        "slice_3": "A larger torrent of mud and uprooted trees slams into the pastel houses, causing more destruction."},
        {"people_scramble", "people_uphill", "abstract_final"}),
    "helikopter_F4_G1": (HELI, "C", "F4", "G1", "SUV", 4, {
        "slice_1_rest": "Four people immediately sprint away from the approaching danger.",
        "slice_2": "The downdraft intensifies the flames, engulfing a wooden house whose roof collapses in a fiery "
                   "cascade.",
        "slice_3": "Raging flames consume nearby trees as a fresh surge threatens further devastation."},
        {"abstract_final"}),
    "volkan_R8_T5": (VB, "D", "R8", "T5", "SUV", 3, {
        "slice_1_rest": "Three people run away from the falling rocks.",
        "slice_2": "A glowing rock plummets into a house, shattering the wall and flinging debris outward.",
        "slice_3": "A volcanic bomb explodes on the street, creating a crater of sparks and stone."},
        {"volcano_banned_root"}),   # "crater of sparks" T5'in kendi metninde: muaf; plummets, explodes değil
    # bugün Kie'ye gönderilen iki iyi Onay yeni kurallardan geçer (K2+L5'in scatter/exploding'i 31 Eki (1) kuralları)
    "iyi_C1_E1": (LF, "C", "C1", "E1", "pickup truck", 5, {
        "slice_1_rest": "Five people run away from the tornado.",
        "slice_2": "The tornado shoves the pickup truck sideways, crashing it into the stone quay's far curb.",
        "slice_3": "It tears the roof from a nearby waterfront building, scattering debris across the quay."}, set()),
    "iyi_K2_L5": (WF, None, "K2", "L5", "white van", 3, {
        "slice_1_rest": "Three people scatter in panic, fleeing the advancing inferno.",
        "slice_2": "A flaming tree collapses onto a van, crushing its roof instantly.",
        "slice_3": "Another house ignites, its roof exploding violently, casting debris toward the street."}, set()),
}


def _spec(event, opening, b2, b3, vehicle, people):
    spot = list(sk.EVENT_SKELETONS[event]["spots"])[0]
    if not es.uses_vehicle(event):
        vehicle = None
    return es.build_spec(event, None, spot, None, b2, b3, vehicle, people, None, None, None, None, opening)


class TestGptAdded(unittest.TestCase):
    def test_today_onay(self):
        for name, (e, op, b2, b3, veh, n, slices, expected) in ONAY.items():
            with self.subTest(onay=name):
                spec = _spec(e, op, b2, b3, veh, n)
                self.assertEqual({i["rule"] for i in es.gpt_added_issues(spec, slices)}, expected)

    def test_selected_text_exempt(self):
        # kilit cümlesindeki "streak" ve T5'in "crater of sparks" ifadesi bizim metnimiz: muaf
        spec = _spec(VB, None, "R8", "T5", "SUV", 4)
        sl = {"slice_1_rest": "Four people run from the glowing rocks streaking down.",
              "slice_2": "A glowing rock slams into a house across the street and its wall bursts apart.",
              "slice_3": "A volcanic bomb lands in the street and the road blasts apart in a crater of sparks."}
        self.assertEqual(es.gpt_added_issues(spec, sl), [])

    def test_word_forms(self):
        self.assertEqual(es._added_words(es.VOLC_GPT_BANNED, "a trailer, rocks trailing smoke", ""), ["trailing"])
        self.assertEqual(es._added_words(es.HELI_WATER_GPT_BANNED, "the jetty and a jet of water", ""), ["jet"])
        self.assertEqual(es._added_words(es.SOUND_GPT_BANNED, "the cloud rolls in", ""), [])   # "cloud" ≠ loud
        # "cascading" sadece araç öznesiyle (16 Eki helikopter: "the deluge cascading over its path" su)
        spec = _spec(HELI, None, "F6", "G1", "SUV", 4)
        sl = {"slice_1_rest": "Four people flee from the flames down the street.",
              "slice_2": "A nearby SUV skids to a stop, halted by the deluge cascading over its path.",
              "slice_3": "The flames fight back, a fresh burst of fire swallowing trees beside the water line."}
        self.assertNotIn("vehicle_motion", {i["rule"] for i in es.gpt_added_issues(spec, sl)})

    def test_code_fallback_never_rejected(self):
        # kod yedeğinin insan cümlesi (dokulu çamur dahil) yeni kurallara takılmaz
        rng = random.Random(3)
        for e in (SLOPE, MUD, es.VILLAGE, es.FLOOD, es.TIDAL, HELI, VB, PY):
            b = es.EVENT_BEATS[e]
            spot = list(sk.EVENT_SKELETONS[e]["spots"])[0]
            view = es.structure_views(e)[0]
            veh = es.event_vehicles(e, view)[0][0] if es.uses_vehicle(e) else None
            people = sk.count_range(e, None)[1] if es.has_people_rule(e) else None
            for b2, b3 in list(es.allowed_pairs(e, view, spot))[:6]:
                spec = es.build_spec(e, None, spot, view, b2, b3, veh, people, None, None, None, None, None)
                for sl in es.fallback_candidates(spec):
                    with self.subTest(event=e, pair=(b2, b3), line=sl["slice_1_rest"]):
                        self.assertEqual(es.gpt_added_issues(spec, sl), [])


class TestProvenRotation(unittest.TestCase):
    def test_window_and_volcano_d_never(self):
        for e in es.structured_events():
            if e in sk.DISABLED_EVENTS:
                continue
            for view in es.structure_views(e):
                spots = sk.view_spots(e, view)
                for spot in spots:
                    pool = (list(es.FIRE_TOR_ENVS[es.fire_env_of_spot(spot)]["spots"]) if e == es.FIRE_TORNADO
                            else spots)
                    allv = fx.all_frames(e, spot, pool, set(), set())
                    rot = pa.allowed_variants(e, spot, allv)
                    with self.subTest(event=e, spot=spot):
                        self.assertTrue(rot)   # aday hiç tükenmez
                        if any(f["type"] != "pencere" for f in allv):
                            self.assertFalse([f for f in rot if f["type"] == "pencere"])
        self.assertNotIn("D", pa.openings(VB, ox.options(VB)))
        self.assertEqual(pa.openings(VB, ox.options(VB)), ["A", "C"])

    def test_openings_envs_lights(self):
        for e in ox.OPENINGS:
            self.assertEqual(pa.openings(e, ox.options(e)), ["A", pa.GUARD["acilis"][e][0]], e)
        for e in sv.SCENE_ENVS:
            self.assertEqual(pa.scene_envs(e, sv.env_options(e)), ["A", pa.GUARD["ortam"][e][0]], e)
        for e in (VB, PY):
            opts = list(es.VOLCANO_WEATHER_WEIGHTS[e]) + list(sv.LIGHT_ADD[e])
            self.assertEqual(pa.lights(e, opts, opts), [pa.VOLC_HIT_LIGHT, "warm orange dusk sky glowing from the "
                                                                           "eruption"])
        base = list(sk.EVENT_SKELETONS[WF]["weather"])
        self.assertEqual(pa.lights(WF, base + list(sv.LIGHT_ADD[WF]), base),
                         base + ["harsh bright midday sun through the smoke"])   # 31 Eki paylaşımı
        self.assertEqual(pa.spots(VB, list(sk.EVENT_SKELETONS[VB]["spots"])), [pa.VOLC_RT, pa.VOLC_VB])
        self.assertEqual(sorted(pa.spots(PY, list(sk.EVENT_SKELETONS[PY]["spots"]))), sorted([pa.VOLC_HT, pa.VOLC_RT]))

    def test_shared_values_proven(self):
        # 31 Eki orman yangını paylaşımı: çatı (kütüphane) + parapet; 30 Eki meteor: K2
        f = {"type": "çatı", "pos_spot": None, "fg": "parapet", "mode": None}
        self.assertEqual(pa.frame_status(WF, "Embankment above the village road", f), pa.PROVEN)
        self.assertEqual(pa.fg_status(WF, "Embankment above the village road", f), pa.PROVEN)
        self.assertEqual(pa.meteor_envs(list(es.METEOR_ENVS)), ["O2", "O3"])


class TestTexts(unittest.TestCase):
    def test_new_beats(self):
        b = es.EVENT_BEATS
        self.assertEqual(b[MUD]["slice_3"]["M4"]["text"],
                         "the mud knocks a corner shop off its foundation and its walls fold into the street")
        self.assertEqual(b[MUD]["slice_3"]["M3"]["text"],
                         "the mud rams a parked minibus into the front of a house and the wall caves in")
        self.assertEqual(b[FACADE]["slice_3"]["N1"]["text"],
                         "a burning section of the roof caves in and a column of flames shoots up from the top floor")
        self.assertEqual(b[HELI]["slice_2"]["F5"]["text"],
                         "the falling sheet of water smashes a burning wooden deck off the back of a house")
        self.assertIn(("H6", "M4"), b[MUD]["excluded_pairs"])
        self.assertIn("white van", es.clashing_vehicles(MUD, None, "H1", "M3"))

    def test_helicopter_water_sheet(self):
        texts = [es.EVENT_KEY_VISUAL[HELI], ox.OPENINGS[HELI]["B"], ox.OPENINGS[HELI]["C"]]
        texts += [es.EVENT_BEATS[HELI][s][b]["text"] for s, b in (("slice_2", "F1"), ("slice_2", "F2"),
                                                                    ("slice_2", "F5"), ("slice_3", "G2"),
                                                                    ("slice_3", "G7"))]
        for t in texts:
            self.assertIn("falling sheet", t)
            self.assertFalse(es._added_words(es.HELI_WATER_GPT_BANNED, t, ""), t)

    def test_facade_neutral_building(self):
        for spot in sk.EVENT_SKELETONS[FACADE]["spots"]:
            for env in ("C", "E"):
                for f in fx.all_frames(FACADE, spot, list(sk.EVENT_SKELETONS[FACADE]["spots"]), set(),
                                       sv.excluded_positions(FACADE, env)):
                    cam = sk.style_suffix(FACADE, None, spot, None, None, None, f, None, env).split("Setting:")[0]
                    self.assertNotIn("tower", cam.lower(), (spot, env, f))
        self.assertIn("C", ox.OPENING_ENV_EXCLUDE[FACADE]["D"])


class TestGuardShare(unittest.TestCase):
    """31 Eki (3) ek: koruma değeri en fazla %20, art arda gelmez; helikopter kalıcı hasarsız finalleri %10."""
    N = 1500

    def test_opening_env_light_share(self):
        rng = random.Random(7)
        for e in (es.FLOOD, WF, VB, es.AVALANCHE_SKI):
            used, g = [], pa.guards(e, "acilis")
            for _ in range(self.N):
                used.append(ox.choose(e, None, "", "", used, rng)[0])
            with self.subTest(event=e):
                self.assertLessEqual(sum(u in g for u in used) / self.N, 0.20)
                self.assertGreaterEqual(sum(u in g for u in used) / self.N, 0.10)
                self.assertFalse([1 for a, b in zip(used, used[1:]) if a == b and a in g])
        used = []
        for _ in range(self.N):
            used.append(sv.choose_env(WF, "Balcony of a hillside house", used, rng)[0])
        self.assertLessEqual(sum(u in pa.guards(WF, "ortam") for u in used) / self.N, 0.20)
        opts = list(es.VOLCANO_WEATHER_WEIGHTS[VB])
        rot = pa.lights(VB, opts, opts)
        used = []
        for _ in range(self.N):
            used.append(sv.choose_light(VB, rot, used, rng, dict(es.VOLCANO_WEATHER_WEIGHTS[VB]))[0])
        self.assertLessEqual(sum(u in pa.guards(VB, "light") for u in used) / self.N, 0.20)

    def test_guard_pick_plain_when_no_guard(self):
        rng = random.Random(1)
        self.assertIsNone(pa.guard_lru(["a", "b"], [], 1, set()))
        self.assertEqual(pa.guard_lru(["A", "B"], ["B"], 2, {"B"}), (["A"], ["B"]))
        self.assertEqual(pa.guard_lru(["A", "B"], ["A"], 2, {"B"}), (["A", "B"], []))
        self.assertIn(pa.guard_pick(rng, ["A", "B"], {"B"}), ("A", "B"))

    def test_helicopter_trial_finals(self):
        self.assertEqual(es.TRIAL_FINALS[HELI], {"G1", "G2", "G5"})
        rng = random.Random(3)
        for spot in sk.EVENT_SKELETONS[HELI]["spots"]:
            es._BEAT_MEMORY.clear()
            finals = []
            for _ in range(600):   # aday hiç tükenmez (StructureError yok)
                b2, b3 = es.choose_beats(HELI, None, spot, [], rng)
                es.remember_beats(HELI, es.beat_tag(b2, b3))
                finals.append(b3)
            with self.subTest(spot=spot):
                share = sum(f in es.TRIAL_FINALS[HELI] for f in finals) / len(finals)
                self.assertLessEqual(share, 0.15)
                self.assertFalse([1 for a, b in zip(finals, finals[1:]) if a == b])
        es._BEAT_MEMORY.clear()

    def test_env_neutral_words(self):
        spots = list(sk.EVENT_SKELETONS[HELI]["spots"])
        for spot in spots:
            for f in fx.all_frames(HELI, spot, spots, set(), set()):
                self.assertIn("view of the houses", sk.style_suffix(HELI, None, spot, None, None, None, f, None, "E"))
                self.assertIn("view of the neighborhood", sk.style_suffix(HELI, None, spot, None, None, None, f, None,
                                                                          "A"))
        bal = "Balcony of a hillside house"
        f = {"type": "balkon", "pos_spot": bal, "fg": None, "mode": "A"}
        # 3M hit cümlesi ortam A'da aynen; E'de "hillside" yok
        self.assertIn("on a balcony of a hillside house overlooking the street and the burning slope",
                      sk.style_suffix(WF, None, bal, None, None, None, f, None, "A"))
        self.assertNotIn("hillside", sk.style_suffix(WF, None, bal, None, None, None, f, None, "E").split("Setting")[0])
        steps = "High steps on the village square"
        f = {"type": "teras", "pos_spot": steps, "fg": None, "mode": "A"}
        self.assertIn("village lane", sk.style_suffix(es.VILLAGE, None, steps, None, None, None, f, None, "E"))
        for t in es.FALLBACK_PEOPLE[FACADE]:
            self.assertNotIn("tower", t)


if __name__ == "__main__":
    unittest.main()
