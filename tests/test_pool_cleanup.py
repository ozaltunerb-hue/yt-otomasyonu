#!/usr/bin/env python3
"""
Temizlik turu (17 Eki 2026, Bahadır): kural tabanlı havuz temizliği, Parti 1 yeni beat'leri, yumuşak kapı düzeltmeleri,
kalıcı havuz linti ve Notion "Hikâye kaynağı" alanı. Ağ yok, Kie/GPT/Notion çağrısı yok.

- Lint (es.pool_lint_errors): ince/uzak hedef, açık arazi, küçük araç, ticari gemi sözcükleri beat metninde ve araç
  adında HATA (modül açılışta düşer). Mevcut korunan/KALSIN/çıkış bekleyen beat'ler POOL_LINT_GRANDFATHERED'da tek tek.
- Yeni beat'ler: her biri ayrı test (metin birebir, lint, kendi kapısı, her izinli kombinasyonda kod yedeği + son
  denetim, yakınlık kapısı, GPT tarzı paraphrase'ler, yanlış nesne reddi).
"""
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.skeleton_pipeline as sk

FT, VB, ER = es.FIRE_TORNADO, es.VOLCANIC_BOMBS, es.ERUPTION
RT, BAL = "Rooftop terrace facing the erupting volcano", "Balcony of a village house facing the erupting volcano"

# Bahadır'ın metni birebir (17 Eki, Parti 1)
NEW_BEATS = {
    (FT, "slice_2", "T7"): "the {vehicle} races down the road away from the towering fire tornado as burning debris "
                           "crashes down behind it",
    (FT, "slice_3", "U7"): "the towering fire tornado tears a wooden house off its foundation and swallows it, planks "
                           "and beams spiraling up into the flaming column",
    (FT, "slice_3", "U8"): "the roofs of two houses in a row are ripped off one after another and pulled up into the "
                           "spinning fire column",
    (FT, "slice_3", "U9"): "the front wall of a house tears away and the rubble is sucked into the fire tornado, flames "
                           "pouring into the open rooms",
    (FT, "slice_3", "U10"): "the towering fire tornado rips the porch and front steps off a house and pulls them into "
                            "its column in a storm of sparks",
    (FT, "slice_3", "U11"): "the towering fire tornado engulfs a wooden garage beside a house, its walls bursting apart "
                            "as burning boards spiral up into the column",
    (VB, "slice_2", "R7"): "a huge glowing rock crashes through the roof of a house across the street, tiles and "
                           "burning timbers flying skyward",
    (VB, "slice_2", "R8"): "a glowing rock slams into the side wall of a house and the wall bursts apart in a shower "
                           "of sparks and stone",
    (VB, "slice_2", "R9"): "a glowing rock hits the road ahead, splitting the asphalt and sending burning chunks flying "
                           "across the street",
    (VB, "slice_3", "T7"): "glowing rocks rain onto a row of houses and set their roofs ablaze one after another",
    (VB, "slice_3", "T8"): "a huge glowing rock hits a house and its whole upper floor erupts in flames, burning beams "
                           "collapsing into the street",
    (VB, "slice_3", "T9"): "a glowing rock smashes into a large parked truck and flames wrap the cab and the box behind "
                           "it",
    (ER, "slice_2", "S6"): "the shockwave hits the house across the street and its front wall bursts outward, bricks "
                           "and roof tiles flying",
    (ER, "slice_2", "S7"): "the shockwave lifts the roof off a house across the street and hurls it down the road in "
                           "pieces",
    (ER, "slice_2", "S8"): "the shockwave shoves a large truck sideways down the street and flips it onto its side",
    (ER, "slice_3", "U7"): "the shockwave rolls down the village street and the houses on both sides collapse inward "
                           "one after another, walls and roofs crumbling",
    (ER, "slice_3", "U8"): "the shockwave tears the upper floor off a stone house and its walls fall into the street in "
                           "a cloud of dust",
}
# Seçilemeyen yeni beat (kod yedeği hiçbir 4-9s maddesiyle 75 kelimeye sığmıyor; metin Bahadır onayıyla kısalır)
UNUSABLE = {(FT, "U10"): "24 kelime: kilit cümle 28-29 + insan cümlesi 6 + her 4-9s maddesi ile 75'i aşar"}
# GPT tarzı doğru anlatımlar (yumuşak kapıdan geçer) ve yanlış nesne (beat_object)
PARAPHRASE = {
    (FT, "T7"): ["The SUV speeds off down the road as flaming debris from the vortex crashes behind it.",
           "Fleeing the giant fire whirl, the SUV races away while burning wreckage slams onto the road."],
    (FT, "U7"): ["The vortex rips a whole wooden house off its foundation and swallows it in flames.",
           "A wooden house is torn from its foundation and its burning beams whirl up into the fire column."],
    (FT, "U8"): ["The fire column rips the roofs off two houses one after another and sucks them upward.",
           "One roof, then the next, is torn off two houses in a row and pulled into the flames."],
    (FT, "U9"): ["The tornado tears the front wall off a house and sucks the rubble into its burning column.",
           "A house's facade rips away and the vortex draws the debris in as fire fills the rooms."],
    (FT, "U10"): ["The vortex tears the porch and front steps off a house and pulls them into the flames.",
            "A house's porch and its steps are ripped loose and sucked into the fire column in sparks."],
    (FT, "U11"): ["The fire tornado smashes a wooden garage beside a house, its burning boards whirling upward.",
            "A garage next to a house bursts apart as the vortex sucks its flaming planks into the column."],
    (VB, "R7"): ["A red-hot boulder crashes through the roof of the house opposite, tiles flying.",
           "A glowing bomb punches through a house's roof across the street, burning timbers bursting upward."],
    (VB, "R8"): ["A glowing rock hits the side of a house and the wall explodes in sparks and stone.",
           "A red-hot boulder smashes into a house wall, which bursts apart."],
    (VB, "R9"): ["A glowing rock slams into the road ahead and the asphalt splits open, burning chunks flying.",
           "A red-hot bomb hits the street and cracks the tarmac apart."],
    (VB, "T7"): ["Glowing rocks pound a row of houses and their roofs catch fire one by one.",
           "Red-hot stones crash onto the houses along the street, setting the roofs ablaze."],
    (VB, "T8"): ["A huge glowing rock smashes into a house and its upper floor bursts into flames.",
           "A red-hot boulder hits a home and the top storey goes up in flames, beams crashing down."],
    (VB, "T9"): ["A glowing rock slams into a big parked truck and fire engulfs its cab.",
           "A red-hot boulder hits a parked lorry, setting the whole truck ablaze."],
    (ER, "S6"): ["The blast wave hits the house opposite and its front wall bursts outward in bricks and tiles.",
           "The shock wave slams the house across the street, blowing its facade out."],
    (ER, "S7"): ["The blast wave tears the roof off the house across the street and flings it down the road.",
           "The shock wave rips a house's roof away and throws the pieces into the street."],
    (ER, "S8"): ["The blast wave pushes a large truck down the street and tips it onto its side.",
           "The shock wave shoves a heavy truck sideways until it overturns."],
    (ER, "U7"): ["The blast wave races down the street and the houses on both sides cave in one after another.",
           "The shock wave rolls along the village street, collapsing the houses on either side."],
    (ER, "U8"): ["The blast wave rips the upper floor off a stone house and its walls crash into the street.",
           "The shock wave strips the top storey from a house, its walls tumbling onto the road."],
}
WRONG_OBJECT = {   # olay doğru, ana nesne yanlış: yumuşak kapı reddeder
    (FT, "U7"): "The fire tornado sweeps over the road and flings burning branches high.",
    (FT, "U8"): "The fire tornado sweeps across the street and flings burning trees aside.",
    (FT, "U9"): "The fire tornado sweeps over the yard and hurls burning branches.",
    (FT, "U10"): "The fire tornado sweeps over the yard and hurls burning branches.",
    (FT, "U11"): "The fire tornado sweeps over the yard and hurls burning branches.",
    (VB, "R7"): "A glowing rock bounces along the pavement in a shower of sparks.",
    (VB, "R8"): "A glowing rock bounces along the pavement in a shower of sparks.",
    (VB, "R9"): "A glowing rock crashes into a parked car in a burst of sparks.",
    (VB, "T7"): "A glowing rock crashes into a parked car in a burst of sparks.",
    (VB, "T8"): "A glowing rock crashes into a parked car in a burst of sparks.",
    (VB, "T9"): "A glowing rock bounces along the pavement in a shower of sparks.",
    (ER, "S6"): "The shockwave bends the street trees flat in a burst of dust.",
    (ER, "S7"): "The shockwave bends the street trees flat in a burst of dust.",
    (ER, "S8"): "The shockwave bends the street trees flat in a burst of dust.",
    (ER, "U7"): "The shockwave knocks over a bell tower in a cloud of dust.",
    (ER, "U8"): "The shockwave bends the street trees flat in a burst of dust.",
}


def _people_sentence(spec):
    return es.clean_slice(es.fallback_people_pool(spec)[0].format(N=es.people_word(spec).capitalize()))


def _spec(event, b2, b3, spot, vehicle="SUV", people=None):
    lo, _ = sk.count_range(event, None)
    return es.build_spec(event, None, spot, None, b2, b3, vehicle if es.uses_vehicle(event) else None,
                         people or lo if es.has_people_rule(event) else None)


def _any_pair(event, slot, bid):
    """Maddenin izinli bir (b2, b3, nokta) üçlüsü; yoksa maddenin dilimindeki ilk karşı madde ve ilk nokta."""
    for spot in sk.view_spots(event, None):
        for b2, b3 in es.allowed_pairs(event, None, spot):
            if (b2 if slot == "slice_2" else b3) == bid:
                return b2, b3, spot
    other = next(iter(es.EVENT_BEATS[event]["slice_3" if slot == "slice_2" else "slice_2"]))
    spot = sk.view_spots(event, None)[0]
    return (bid, other, spot) if slot == "slice_2" else (other, bid, spot)


class TestPoolLint(unittest.TestCase):
    def test_pool_is_clean(self):
        self.assertEqual(es.pool_lint_errors(), [])

    def test_lint_catches_banned_words(self):
        cases = {"ince/uzak hedef": ["a glass storefront shatters", "a utility pole snaps", "a wooden fence tears away",
                                     "a shop sign falls", "a café awning rips loose", "the guardrail buckles",
                                     "a window pane bursts", "the windshield cracks", "power lines whip around",
                                     "a lamppost topples", "the street lamps fall", "a low wall crumbles"],
                 "açık arazi": ["the logs fly across the field", "a fire sweeps an empty land", "a vacant lot burns",
                                "the meadow catches fire", "a burning plot of grass", "flames race over the pasture"],
                 "küçük araç": ["the small car spins", "a hatchback tips over", "a compact car slides",
                                "the small van is crushed"],
                 "ticari gemi": ["a cargo ship rolls", "a tugboat capsizes", "a fishing boat sinks",
                                 "a container ship drifts"]}
        for rule, texts in cases.items():
            for t in texts:
                with self.subTest(rule=rule, text=t):
                    self.assertIn(rule, [r for r, _ in es.pool_lint_hits(t)])
        # ağaçlı yerleşim ve büyük hedefler yakalanmaz
        for t in ("a tree-lined residential street", "the front wall of a house", "a large parked truck",
                  "a wooden garage beside a house", "the roofs of two houses", "a wooden house off its foundation"):
            with self.subTest(clean=t):
                self.assertEqual(es.pool_lint_hits(t), [])

    def test_new_bad_beat_fails_at_import_check(self):
        # Yeni bir beat lint sözcüğü içerirse _validate_data (modül açılışı) hata verir: test geçmeden eklenemez
        b = es.EVENT_BEATS[FT]["slice_3"]
        for text in ("the fire tornado snaps a utility pole across the road",
                     "the fire tornado hurls burning logs across the field",
                     "the fire tornado flips a small car onto its roof"):
            with self.subTest(text=text):
                b["UX"] = {"text": text, "terms": [("fire",)]}
                es.OBJECT_GROUPS[FT]["UX"] = 0
                try:
                    with self.assertRaises(es.StructureError) as ctx:
                        es._validate_data()
                    self.assertIn("Havuz linti", str(ctx.exception))
                finally:
                    del b["UX"]
                    del es.OBJECT_GROUPS[FT]["UX"]
        es._validate_data()   # geri alındı, temiz

    def test_small_vehicle_name_fails(self):
        lst = es.EVENT_VEHICLES[es.MUDSLIDE]
        lst.append(("small car", ("car",)))
        try:
            with self.assertRaises(es.StructureError):
                es._validate_data()
        finally:
            lst.pop()

    def test_grandfather_list_is_exact(self):
        # her muafiyetin gerekçesi var; havuzda olmayan ya da artık ihlal etmeyen beat muaf kalamaz
        self.assertEqual(len(es.POOL_LINT_GRANDFATHERED), 31)
        for (event, bid), why in es.POOL_LINT_GRANDFATHERED.items():
            with self.subTest(beat=(event, bid)):
                self.assertTrue(why.startswith(("korunan", "denetimde", "çıkış bekliyor")), why)
        with patch.dict(es.POOL_LINT_GRANDFATHERED, {(FT, "U2"): "deneme"}):
            self.assertIn(f"{FT}/U2: muafiyet gereksiz (ihlal yok)", es.pool_lint_errors())
        with patch.dict(es.POOL_LINT_GRANDFATHERED, {(FT, "U4"): "deneme"}):
            self.assertIn(f"{FT}/U4: muafiyet kaydı havuzda olmayan beat için", es.pool_lint_errors())

    def test_vehicles_and_views_large_only(self):
        names = {n for lst in list(es.REGION_VEHICLES.values()) + list(es.EVENT_VEHICLES.values()) for n, _ in lst}
        self.assertFalse({n for n in names if es.pool_lint_hits(n)})
        for view, text in sk.REGION_VIEWS.items():
            with self.subTest(view=view):
                self.assertEqual(es.find_terms(es.POOL_LINT_SMALL_VEHICLE + es.POOL_LINT_SHIP, text), [])
        # eski araç adları okunurken bugünkü listeden bir araca çevrilir
        for view, m in es.RETIRED_VEHICLES_BY_VIEW.items():
            for old, new in m.items():
                self.assertIn(new, [n for n, _ in es.REGION_VEHICLES[view]], (view, old))
        event_names = {n for lst in es.EVENT_VEHICLES.values() for n, _ in lst}
        for old, new in es.RETIRED_VEHICLES.items():
            self.assertIn(new, event_names | {n for lst in es.REGION_VEHICLES.values() for n, _ in lst}, old)


class TestCleanupRule(unittest.TestCase):
    # 17 Eki kural tabanlı temizlik: çıkan beat'ler (kod -> kural), korunan ve çıkış bekleyenler havuzda
    RETIRED = {es.FLOOD: {"D1", "D6", "D7"}, es.TIDAL: {"W7"}, es.SLOPE: {"S1", "S6"}, es.VILLAGE: {"L2"},
               es.LANDFALL: {"C3", "C6", "E3", "E6"}, es.MARINA_TORNADO: {"Y4", "Y6", "Z5"},
               es.AVENUE: {"P3", "Q5"}, es.WILDFIRE: {"L2", "L6"}, es.FACADE_FIRE: {"N2", "N6"},
               FT: {"T3", "U3", "U4", "U5"}, es.HELICOPTER: {"G4"}, ER: {"S1", "U1"}, VB: {"R6", "T3", "T4"},
               es.AVALANCHE_FOREST: {"F3"}}
    # daha önce üretilmiş videoda kullanılan (Notion, 17 Eki anlık görüntü) ve kurala göre zayıf: havuzda kalır
    PROTECTED_WEAK = {es.FLOOD: {"D2"}, es.TIDAL: {"W1", "W2", "W6"}, es.MUDSLIDE: {"M3"}, es.SLOPE: {"R2", "S4"},
                      es.MARINA_TORNADO: {"Z6"}, es.AVENUE: {"P6", "Q3", "Q6"}, es.WILDFIRE: {"K5"},
                      es.FACADE_FIRE: {"M6"}, ER: {"S2", "U3"}, VB: {"R3", "R4"}}
    # grup 4'ün altına düşerdi (ya da nokta seçilemez olurdu): çıkış bekliyor, yerine yeni beat sonraki partide
    WAITING = {es.MUDSLIDE: {"M1", "M2", "M5"}, es.WILDFIRE: {"K3", "K4", "K6"},
               es.FACADE_FIRE: {"M1", "M2", "M3", "M4", "M5"}, es.EARTHQUAKE_OLD_STREET: {"T2"},
               es.AVALANCHE_FOREST: {"E5"}}

    def test_retired_exactly(self):
        self.assertEqual({e: set(d) for e, d in es.RETIRED_BEATS.items()}, self.RETIRED)
        for e, ids in self.RETIRED.items():
            for bid in ids:
                with self.subTest(event=e, beat=bid):
                    self.assertNotIn(bid, es.EVENT_BEATS[e]["slice_2"])
                    self.assertNotIn(bid, es.EVENT_BEATS[e]["slice_3"])
                    self.assertTrue(es.RETIRED_BEATS[e][bid][1])   # kural gerekçesi yazılı
                    for v, d in es.EVENT_BEATS[e]["excluded_pairs"]:
                        self.assertNotIn(bid, (v, d))

    def test_protected_and_waiting_stay(self):
        for group in (self.PROTECTED_WEAK, self.WAITING):
            for e, ids in group.items():
                for bid in ids:
                    with self.subTest(event=e, beat=bid):
                        self.assertTrue(bid in es.EVENT_BEATS[e]["slice_2"] or bid in es.EVENT_BEATS[e]["slice_3"])

    def test_pyroclastic_untouched(self):
        b = es.EVENT_BEATS[es.PYROCLASTIC]
        self.assertEqual((sorted(b["slice_2"]), sorted(b["slice_3"])),
                         (["P1", "P2", "P3", "P4", "P5", "P6"], ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]))
        self.assertEqual(len(b["excluded_pairs"]), 8)
        self.assertNotIn(es.PYROCLASTIC, es.RETIRED_BEATS)

    def test_every_group_at_least_four_and_every_spot_selectable(self):
        for e in es.structured_events():
            b = es.EVENT_BEATS[e]
            with self.subTest(event=e):
                self.assertGreaterEqual(len(b["slice_2"]), 4)
                self.assertGreaterEqual(len(b["slice_3"]), 4)
                for view in es.structure_views(e):
                    for spot in sk.view_spots(e, view):
                        self.assertTrue(es.allowed_pairs(e, view, spot), (view, spot))

    def test_item1_pairs(self):
        koy = es.EVENT_BEATS[es.AVALANCHE_VILLAGE]
        for v in ("A2", "A4", "A5"):
            for d in ("B2", "B5"):
                self.assertIn((v, d), koy["excluded_pairs"])
                self.assertIn(v, koy["slice_2"])
                self.assertIn(d, koy["slice_3"])
        # bombalar R6+T5: R6 kurala göre çıktı (fizik 2), çift onunla gitti
        self.assertIn("R6", es.RETIRED_BEATS[VB])
        self.assertIn("T5", es.EVENT_BEATS[VB]["slice_3"])


class TestNewBeats(unittest.TestCase):
    """Parti 1 (17 Eki): her yeni beat ayrı test edilir (aşağıda üretilen test_new_<olay>_<id> metotları)."""

    def test_all_new_beats_listed(self):
        self.assertEqual(len(NEW_BEATS), 17)
        self.assertEqual(set(PARAPHRASE), {(e, bid) for (e, _, bid) in NEW_BEATS})
        self.assertEqual(set(WRONG_OBJECT), {(e, bid) for (e, _, bid) in NEW_BEATS if bid != "T7" or e != FT})

    def test_fire_tornado_near_gate_new_beats(self):
        # yakınlık kapısı: kaçan insanlar kameraya yakın (yeni beat'lerde de aynı kural)
        for (e, slot, bid) in [k for k in NEW_BEATS if k[0] == FT]:
            b2, b3, spot = _any_pair(e, slot, bid)
            spec = _spec(e, b2, b3, spot, people=2)
            sl = {"slice_1_rest": _people_sentence(spec), "slice_2": es.fallback_beat_slice(spec, "slice_2"),
                  "slice_3": es.fallback_beat_slice(spec, "slice_3")}
            with self.subTest(beat=bid):
                self.assertNotIn("slice_near_camera", {i["rule"] for i in es.slice_issues(spec, sl)})
                far = {**sl, "slice_1_rest": "Two people run far away on the distant road."}
                self.assertIn("slice_near_camera", {i["rule"] for i in es.slice_issues(spec, far)})

    def test_volcano_camera_building_exclusions(self):
        # kameranın durduğu ev/teras: sokağın iki yanındaki evler (şok U7) ve bir sıra evin çatısı (bombalar T7)
        # çatı terasında ve köy evi balkonunda seçilmez; karşıdaki ev ("across the street") her noktada
        self.assertEqual(es.EVENT_BEATS[ER]["excluded_spots"]["U7"], {RT, BAL})
        self.assertEqual(es.EVENT_BEATS[VB]["excluded_spots"]["T7"], {RT, BAL})
        for e, bid in ((ER, "S6"), (ER, "S7"), (VB, "R7")):
            self.assertIn("across the street", es.beat_text(e, "slice_2", bid))
            self.assertNotIn(bid, es.EVENT_BEATS[e]["excluded_spots"])

    def test_u10_unusable_until_shortened(self):
        # U10 metni 24 kelime; kod yedeği hiçbir 4-9s maddesiyle 75'e sığmadığı için hiçbir çifti izinli değil.
        # Metin kısalırsa (Bahadır onayı) bu test kırılır: UNUSABLE ve FALLBACK_GAPS_EXCLUDED güncellenir.
        for (e, bid), why in UNUSABLE.items():
            with self.subTest(beat=bid, why=why):
                self.assertFalse([p for s in sk.view_spots(e, None) for p in es.allowed_pairs(e, None, s)
                                  if bid in p])
                self.assertEqual(len(es.beat_text(e, "slice_3", bid).split()), 24)


def _make_test(event, slot, bid, text):
    def test(self):
        beat = es.EVENT_BEATS[event][slot][bid]
        self.assertEqual(beat["text"], text)                       # Bahadır'ın metni birebir
        self.assertEqual(es.pool_lint_hits(text.replace("{vehicle}", "vehicle")), [])   # lint temiz
        self.assertNotIn((event, bid), es.POOL_LINT_GRANDFATHERED)
        self.assertNotIn(bid, es.RETIRED_BEATS.get(event, {}))     # kimlik yeni
        # kendi metni: eski sıkı kapı (her terim grubu) ve yumuşak kapı (ana nesne) geçer
        b2, b3, spot = _any_pair(event, slot, bid)
        for veh in ([v for v, _ in es.event_vehicles(event, None)] if es.uses_vehicle(event) else [None]):
            spec = _spec(event, b2, b3, spot, veh)
            sl = {"slice_1_rest": _people_sentence(spec), "slice_2": es.fallback_beat_slice(spec, "slice_2"),
                  "slice_3": es.fallback_beat_slice(spec, "slice_3")}
            self.assertEqual(es.strict_beat_issues(spec, sl), [], veh)
            self.assertEqual(es.soft_beat_issues(spec, sl), [], veh)
        # her izinli kombinasyon (nokta × eş × araç × kişi): kod yedeği var ve son denetimden (yakınlık dahil) geçer
        n = 0
        lo, hi = sk.count_range(event, None)
        for s in sk.view_spots(event, None):
            for p2, p3 in es.allowed_pairs(event, None, s):
                if (p2 if slot == "slice_2" else p3) != bid:
                    continue
                for veh in ([v for v, _ in es.event_vehicles(event, None)] if es.uses_vehicle(event) else [None]):
                    for people in range(lo, hi + 1):
                        spec = _spec(event, p2, p3, s, veh, people)
                        cands = es.fallback_candidates(spec)
                        self.assertTrue(cands, (s, p2, p3, veh, people))
                        for sl in cands:
                            prompt = es.assemble_prompt(spec, sl)
                            self.assertEqual(es.final_prompt_issues(spec, sl, prompt, es.assemble_story(spec, sl)),
                                             [], (s, p2, p3, veh, people, sl))
                            n += 1
        if (event, bid) not in UNUSABLE:
            self.assertGreater(n, 0)
        # GPT tarzı doğru anlatım geçer, yanlış ana nesne reddedilir
        spec = _spec(event, b2, b3, spot)
        base = {"slice_1_rest": _people_sentence(spec), "slice_2": es.fallback_beat_slice(spec, "slice_2"),
                "slice_3": es.fallback_beat_slice(spec, "slice_3")}
        for t in PARAPHRASE[(event, bid)]:
            self.assertEqual(es.soft_beat_issues(spec, {**base, slot: t}), [], t)
        if (event, bid) in WRONG_OBJECT:
            codes = {i["rule"] for i in es.soft_beat_issues(spec, {**base, slot: WRONG_OBJECT[(event, bid)]})}
            self.assertIn("beat_object", codes)
    return test


_SHORT = {FT: "fire_tornado", VB: "bombs", ER: "eruption"}
for (_e, _slot, _bid), _text in NEW_BEATS.items():
    setattr(TestNewBeats, f"test_new_{_SHORT[_e]}_{_bid}", _make_test(_e, _slot, _bid, _text))


class TestStorySourceNotion(unittest.TestCase):
    def test_schema_and_value(self):
        import infrastructure.notion_logger as nl
        self.assertEqual(nl.STORY_SOURCE_PROPERTY, "Hikâye kaynağı")
        self.assertEqual(nl.EXTRA_PROPERTIES[nl.STORY_SOURCE_PROPERTY], {"rich_text": {}})
        self.assertEqual(nl.story_source_value("Hikâye: GPT (deneme 2)"), "GPT (deneme 2)")
        self.assertEqual(nl.story_source_value("Hikâye: kod yedeği (neden: deneme 1: a | deneme 2: b)"),
                         "kod yedeği (neden: deneme 1: a | deneme 2: b)")

    def test_written_in_separate_request_and_filtered_when_missing(self):
        import infrastructure.notion_logger as nl
        calls = []
        tr = nl.NotionTracker(page_id="p1")
        with patch.object(nl.settings, "NOTION_ENABLED", True), patch.object(nl.settings, "IS_DRY_RUN", False), \
                patch.object(nl, "_notion_request", lambda m, u, **k: calls.append(k.get("json")) or {}):
            tr.enabled = True
            with patch.object(nl.NotionTracker, "_schema", {"Prompt", nl.STORY_SOURCE_PROPERTY}):
                tr.record_story_source("Hikâye: GPT (deneme 1)")
            self.assertEqual(calls[-1], {"properties": {nl.STORY_SOURCE_PROPERTY: nl._rt("GPT (deneme 1)")}})
            n = len(calls)
            with patch.object(nl.NotionTracker, "_schema", {"Prompt"}):   # alan yok: istek gitmez, hata yok
                tr.record_story_source("Hikâye: GPT (deneme 1)")
            self.assertEqual(len(calls), n)

    def test_ensure_schema_keeps_schema_if_add_fails(self):
        import infrastructure.notion_logger as nl
        have = {k: {} for k in nl.EXTRA_PROPERTIES if k != nl.STORY_SOURCE_PROPERTY}
        have["Durum"] = {"select": {"options": [{"name": n} for n in nl.REQUIRED_STATUS_OPTIONS]}}

        def fake(method, url, **kw):
            if method == "PATCH":
                raise RuntimeError("Notion API hatası: 403")
            return {"properties": have}
        with patch.object(nl.settings, "NOTION_ENABLED", True), patch.object(nl.settings, "IS_DRY_RUN", False), \
                patch.object(nl, "_notion_request", fake), patch.object(nl.NotionTracker, "_schema", None):
            got = nl.NotionTracker.ensure_schema()
            self.assertEqual(got, set(have))
            self.assertNotIn(nl.STORY_SOURCE_PROPERTY, nl.NotionTracker._schema)

    def test_main_writes_story_source(self):
        src = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read()
        self.assertIn('tracker.record_story_source, info["story_source"]', src)

    def test_report_reads_notion_pages(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import fallback_report as fr

        def page(olay, value, combo=""):
            rt = (lambda t: {"rich_text": [{"plain_text": t}]})
            return {"properties": {"Olay": rt(olay), "Combo Key": rt(combo), "Hikâye kaynağı": rt(value)}}
        pages = [page(FT, "GPT (deneme 1)"), page(FT, "kod yedeği (neden: deneme 1: toplam 40-75 kelime (78); "
                                                       "0-4s: insanlar kameraya yakın değil | deneme 2: toplam 40-75 "
                                                       "kelime (77))"),
                 page("", "GPT (deneme 2)", f"fire_disasters|none|{VB.lower()}|x|cam"), page(ER, "")]
        rows = fr.rows_from_notion(pages)
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["source"] for r in rows], ["gpt", "fallback", "gpt"])
        self.assertEqual(rows[0]["gpt_attempts"], 1)
        self.assertEqual(rows[1]["attempt_missing"], [["toplam 40-75 kelime (78)", "0-4s: insanlar kameraya yakın değil"],
                                                      ["toplam 40-75 kelime (77)"]])
        self.assertEqual(rows[2]["event"], VB.lower())
        text = fr.report(rows)
        self.assertIn(f"{FT}: yedek 1/2 (%50)", text)
        self.assertIn("toplam 40-75 kelime: 1", text)


if __name__ == "__main__":
    unittest.main()
