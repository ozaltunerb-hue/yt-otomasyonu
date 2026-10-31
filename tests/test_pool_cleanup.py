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
NEW_BEATS = {   # 18 Eki: kısa metinler (≤16 kelime; 17 Eki uzun metinleri commit d77655d)
    (FT, "slice_2", "T7"): "the {vehicle} races away from the fire tornado as burning debris crashes down behind it",
    # 18 Eki (2): "column" -> "funnel" (dönen huni)
    (FT, "slice_3", "U7"): "a wooden house across the street is torn from its foundation, planks spiraling into the "
                           "funnel",
    (FT, "slice_3", "U8"): "the roofs of two houses across the street are ripped off and sucked into the funnel",
    (FT, "slice_3", "U9"): "the front wall of a house across the street tears away, rubble sucked into the funnel",
    (FT, "slice_3", "U10"): "the porch and steps of a house across the street are ripped off and pulled in",
    (FT, "slice_3", "U11"): "a wooden garage beside a house across the street bursts apart, burning boards spiraling "
                            "up",
    (VB, "slice_2", "R7"): "a huge glowing rock crashes through the roof of a house across the street",
    (VB, "slice_2", "R8"): "a glowing rock slams into a house across the street and its wall bursts apart",
    # 31 Eki, Bahadır: R9 yeni metin (önceki "a glowing rock hits the road ahead and sends burning chunks across the
    # street": kalıcı hasar yok)
    (VB, "slice_2", "R9"): "a glowing rock crashes through the front of a corner shop down the street and its wall caves "
                           "in",
    # 30 Eki, Bahadır (Aşama B): T7 yeni metin (önceki "glowing rocks hit a row of houses and set their roofs ablaze")
    (VB, "slice_3", "T7"): "a volcanic bomb slams into a parked van and flips it onto its side in a burst of sparks",
    (VB, "slice_3", "T8"): "a huge glowing rock hits a house and its upper floor erupts in flames",
    (VB, "slice_3", "T9"): "a glowing rock smashes into a large parked truck and flames wrap the cab",
    (ER, "slice_2", "S6"): "the shockwave hits the house across the street and its front wall bursts outward",
    (ER, "slice_2", "S7"): "the shockwave lifts the roof off a house across the street and hurls it away",
    (ER, "slice_2", "S8"): "the shockwave shoves a large truck sideways down the street and flips it",
    (ER, "slice_3", "U7"): "the shockwave rolls down the street and the houses on both sides collapse inward",
    (ER, "slice_3", "U8"): "the shockwave tears the upper floor off a stone house across the street",
}
# 30 Eki: Bahadır'ın onayladığı yeni T7 metni 19 kelime; kısaltılmadı, 16 sınırı bu maddede açık (Z7 gibi; bütçe
# denetiminde bombaların tüm kombinasyonu 175'e sığıyor)
NEW_BEATS_LONG = {(VB, "T7"): 19, (VB, "R9"): 19}   # 31 Eki: R9 onaylı metin 19 kelime (bütçe denetimi 0 sığmayan)
# 18 Eki: seçilemeyen yeni beat kalmadı (17 Eki'de U10 24 kelimeydi)
UNUSABLE = {}
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
    (VB, "R9"): ["A glowing rock smashes into a corner shop down the street and its front wall caves in.",   # 31 Eki
           "A red-hot bomb punches through a corner store's front and the brick wall collapses."],
    (VB, "T7"): ["A red-hot boulder smashes into a parked van and tips it onto its side in sparks.",
           "A glowing volcanic bomb hits a van at the curb and flips it over."],
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
    (VB, "T7"): "A glowing rock crashes onto the roofs of the houses in a burst of sparks.",
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
        # 18 Eki (2): çıkış bekleyen 6 lint muafiyeti çıktı. 22 Eki: yamaç R2, S4 ve köy K3 yeni metinle ihlal etmiyor
        # 23 Eki (hortum denetimi): marina Y3, Z1, Z2, Z6 yeni metin, korumaları kalktı
        # 30 Eki: cadde P5, Q3, Q6 ve cephe N5 yeni metin, korumaları kalktı
        # 31 Eki: karaya vurur E5 yeni metin (plaj büfesi), koruması kalktı
        self.assertEqual(len(es.POOL_LINT_GRANDFATHERED), 13)
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
               es.AVENUE: {"P3", "Q5"}, es.WILDFIRE: {"L2", "L6", "K3", "K4", "K6"},
               es.FACADE_FIRE: {"N2", "N6", "M1", "M2", "M3", "M4", "M5"},
               FT: {"T3", "U3", "U4", "U5"}, es.HELICOPTER: {"G4"}, ER: {"S1", "U1"}, VB: {"R6", "T3", "T4"},
               es.AVALANCHE_FOREST: {"F3", "E5"},
               # 18 Eki (2): çıkış bekleyenler Parti 2 ile çıktı
               es.MUDSLIDE: {"M1", "M2", "M5"}, es.EARTHQUAKE_OLD_STREET: {"T2"},
               # 29 Eki (2), Bahadır: meteor yeni kurgu, eski M/N havuzu (tests/test_meteor.py)
               es.METEOR: {"M1", "M2", "M3", "M4", "M5", "M6", "N1", "N2", "N3", "N4", "N5", "N6"}}
    # daha önce üretilmiş videoda kullanılan (Notion, 17 Eki anlık görüntü) ve kurala göre zayıf: havuzda kalır
    PROTECTED_WEAK = {es.FLOOD: {"D2"}, es.TIDAL: {"W1", "W2", "W6"}, es.MUDSLIDE: {"M3"}, es.SLOPE: {"R2", "S4"},
                      es.MARINA_TORNADO: {"Z6"}, es.AVENUE: {"P6", "Q3", "Q6"}, es.WILDFIRE: {"K5"},
                      es.FACADE_FIRE: {"M6"}, ER: {"S2", "U3"}, VB: {"R3", "R4"}}
    # grup 4'ün altına düşerdi (ya da nokta seçilemez olurdu): çıkış bekliyor, yerine yeni beat sonraki partide
    # 18 Eki (2): çıkış bekleyenlerin hepsi Parti 2 ile çıktı (RETIRED'da)
    WAITING = {}

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
                if e == es.METEOR:   # 29 Eki (3-4): ek kurala takılan madde havuza girmez; X3 4. turda girdi, 3 + 4
                    # madde (tests/test_meteor.py)
                    self.assertEqual((len(b["slice_2"]), len(b["slice_3"])), (3, 4))
                    continue
                self.assertGreaterEqual(len(b["slice_2"]), 4)
                self.assertGreaterEqual(len(b["slice_3"]), 4)
                for view in es.structure_views(e):
                    for spot in sk.view_spots(e, view):
                        self.assertTrue(es.allowed_pairs(e, view, spot), (view, spot))

    def test_item1_pairs(self):
        koy = es.EVENT_BEATS[es.AVALANCHE_VILLAGE]
        for v in ("A2", "A4", "A5"):
            for d in ("B2", "B5"):
                # 30 Eki (3), Bahadır: yeni B2 kısa; (A4, B2), (A5, B2) bütçe dışlaması kalktı
                if d == "B2" and v != "A2":
                    self.assertNotIn((v, d), koy["excluded_pairs"])
                else:
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

    def test_short_texts_fit_and_pair_widely(self):
        # 18 Eki, Bahadır: Parti 1 metinleri ≤16 kelime; ateş hortumunda T6 ve T7 en az 4 farklı U ile eşleşir; yedeği
        # sığmayan çift ateş hortumunda sadece T6+U1, volkanda hiç yok; her yeni beat en az bir çiftte seçilebilir
        for (e, slot, bid), text in NEW_BEATS.items():
            with self.subTest(beat=(e, bid)):
                self.assertLessEqual(len(text.replace("{vehicle}", "x").split()), NEW_BEATS_LONG.get((e, bid), 16))
                self.assertTrue([p for s in sk.view_spots(e, None) for p in es.allowed_pairs(e, None, s)
                                 if p[0 if slot == "slice_2" else 1] == bid])
        pairs = {p for s in sk.view_spots(FT, None) for p in es.allowed_pairs(FT, None, s)}
        for b2 in ("T6", "T7"):
            self.assertGreaterEqual(len({d for v, d in pairs if v == b2}), 4, b2)
        # 18 Eki (2): kilit cümle 32-33 kelime: T6 (19 + araç) U2 ve U6 ile 75'i aşar
        self.assertEqual(es.EVENT_BEATS[FT]["excluded_pairs"], {("T1", "U2"), ("T2", "U2"), ("T6", "U2"), ("T6", "U6")})
        self.assertEqual(es._VOLC_BOMBS_GAPS | es._VOLC_ERUPTION_GAPS, set())
        self.assertNotIn(FT, es.BEAT_BLOCK_FALLBACK_EVENTS)

    def test_volcano_prompt_never_over_175(self):
        # 18 Eki: patlama ve bombalarda en uzun stil eki 96 kelime: 96 + 75 + 3 etiket ≤ 175 (GPT'ye kural yok). Kül
        # bulutu bu turda dokunulmadı (eski kamera metni aynen)
        for e in (ER, VB):
            longest = max(len(sk.style_suffix(e, None, s).split()) for s in sk.view_spots(e, None))
            self.assertLessEqual(longest + es.TOTAL_WORDS_BY_EVENT[e][1] + 3, es.VOLC_MAX_PROMPT_WORDS, e)
        self.assertIn(es.PYROCLASTIC, sk.VOLCANO_SHORT_CAMERA_EXCLUDED)
        # 21 Eki (genel kalite): kül bulutu da kısa giyim/ışık satırı; "looking down over" -> "over" (175)
        self.assertEqual(sk.VOLCANO_GUARDRAILS_LONG, sk.VOLCANO_GUARDRAILS)
        self.assertIn("high vantage over the village street", sk.style_suffix(es.PYROCLASTIC, None, RT))

    def test_volcano_rain_verb_lint(self):
        # 18 Eki: volkan beat'inde "rain" fiili lint hatası
        b = es.EVENT_BEATS[VB]["slice_3"]
        b["TX"] = {"text": "glowing rocks rain onto the roofs of the houses", "terms": [("rock",)]}
        es.OBJECT_GROUPS[VB]["TX"] = 0
        try:
            self.assertIn(f"{VB}/TX: volkan beat'inde 'rain' fiili (rain)", es.pool_lint_errors())
        finally:
            del b["TX"]
            del es.OBJECT_GROUPS[VB]["TX"]
        for e in es.VOLCANO_EVENTS:
            for slot in ("slice_2", "slice_3"):
                for bid, beat in es.EVENT_BEATS[e][slot].items():
                    self.assertNotIn("rain", beat["text"].lower().split(), (e, bid))

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


# ── 18 Eki (2), Bahadır: Parti 2 (kalan olaylar), ateş hortumu şekli, şok dalgası devre dışı ────────────────────────
PARTI2 = {   # (olay, dilim, kimlik): (metin, GPT tarzı doğru anlatım)
    (es.MUDSLIDE, "slice_3", "M7"): ("mud slams into a house across the street and bursts through its ground floor",
                                      "The mud smashes into a house across the street and floods its ground floor."),
    # 21 Eki (genel kalite): kadraj dışı hedef düzeltmesi (M8, S7)
    (es.MUDSLIDE, "slice_3", "M8"): ("the mud shoves a parked truck sideways into a house on the street",
                                      "The mudflow shoves a big truck sideways into the front of a house."),
    (es.MUDSLIDE, "slice_3", "M9"): ("a mass of mud and uprooted trees crashes onto the houses across the street",
                                      "Mud and uprooted trees crash down onto the houses across the street."),
    (es.SLOPE, "slice_3", "S7"): ("the mud and boulders shove a stopped truck sideways toward the edge of the road",
                                   "The torrent of mud and boulders pushes a large truck sideways to the road edge."),
    (es.VILLAGE, "slice_3", "L7"): ("the landslide rips a wooden house off its foundation and carries it down the slope",
                                     "The torrent tears a wooden house off its foundation and sweeps it downhill."),
    (es.FLOOD, "slice_3", "D9"): ("the flood bursts through the ground floor of a building across the street",
                                   "The floodwater smashes through the ground floor of a building across the street."),
    (es.WILDFIRE, "slice_2", "K7"): ("a wall of flames races up the slope and engulfs the first houses across the street",
                                      "The wall of flames sweeps up the slope and engulfs the nearest houses."),
    (es.WILDFIRE, "slice_2", "K8"): ("the flames leap across the street and ignite the roof of a house",
                                      "Flames jump across the street and set the roof of a house ablaze."),
    # 30 Eki (2), Bahadır: K9 yeni metin (önceki "the {vehicle} speeds down the road past burning houses as flames
    # lick the asphalt"); 17 kelime, Parti 2 sınırı bu maddede 17 (PARTI2_LONG)
    (es.WILDFIRE, "slice_2", "K9"): ("the {vehicle} speeds past as the roof of a burning house collapses onto the road "
                                      "behind it",
                                      "The SUV speeds past as a burning house's roof collapses onto the road behind it."),
    (es.WILDFIRE, "slice_3", "L7"): ("a house across the street is engulfed and its roof collapses in a burst of flames",
                                      "A house across the street is swallowed by fire and its roof caves in."),
    (es.FACADE_FIRE, "slice_2", "M7"): ("burning cladding panels peel off the facade beside the balcony and fall in flames",
                                         "Burning cladding panels tear off the facade next to the balcony and drop."),
    (es.FACADE_FIRE, "slice_2", "M8"): ("flames race up the facade, panel after panel igniting right beside the balcony",
                                         "Fire races up the facade, igniting one panel after another by the balcony."),
    (es.FACADE_FIRE, "slice_2", "M9"): ("a huge sheet of burning facade tears loose and crashes down the tower",
                                         "A huge burning sheet of cladding breaks loose and crashes down the tower."),
    (es.FACADE_FIRE, "slice_2", "M10"): ("thick fire pours out of the windows of the floor below the balcony",
                                          "Thick flames pour out of the windows on the floor below the balcony."),
    # 30 Eki, Bahadır (Aşama B): M11 ve G7 yeni metin. Önceki M11 "the flames leap up the facade to the balconies above
    # in a roaring wall", G7 "burning treetops erupt as the helicopter's water load hits the ridge above the houses"
    (es.FACADE_FIRE, "slice_2", "M11"): ("a burning balcony slab on the floor above breaks off and crashes down the facade",
                                          "A blazing balcony slab above breaks loose and plunges down the facade."),
    (es.HELICOPTER, "slice_3", "G7"): ("the water load hits a burning garage across the street and its walls collapse in "
                                       "steam", "The water drop slams into a burning garage opposite and its walls cave in."),
    (es.LANDFALL, "slice_3", "E7"): ("the tornado shreds the top floor of a building across the street, debris spiraling up",
                                      "The tornado rips the top floor off a building across the street, debris whirling up."),
    (es.MARINA_TORNADO, "slice_2", "Y7"): ("the tornado rips the roof off the café across the quay and hurls it away",
                                            "The tornado tears the roof off the café across the quay and flings it away."),
    (es.MARINA_TORNADO, "slice_2", "Y8"): ("the tornado smashes into the quayside building and its front wall bursts outward",
                                            "The tornado slams into the quayside building, blowing its front wall outward."),
    # 23 Eki (hortum denetimi): Z7 pergola (önceki "the tornado lifts the whole café terrace off the quay and scatters it
    # across the road"; teras zemin, kalkmaz). Onaylı metin 18 kelime: Parti 2'nin 16 kelime sınırı bu maddede 18
    (es.MARINA_TORNADO, "slice_3", "Z7"): ("the tornado lifts the café's heavy dark wooden pergola off the terrace and smashes "
                                           "it across the road",
                                           "The tornado tears the café's dark pergola off the terrace and hurls it onto the road."),
    (es.AVENUE, "slice_2", "P7"): ("the tornado flings a large truck across the avenue into the front of a building",
                                    "The tornado hurls a large truck across the avenue into the front of a building."),
    (es.EARTHQUAKE_APARTMENT, "slice_3", "Q5"): ("the top floors of the apartment block across the street collapse straight "
                                                 "down", "The top floors of the block across the street collapse straight down."),
    (es.EARTHQUAKE_OLD_STREET, "slice_3", "T5"): ("the upper floor of a stone house slides off and crashes onto the street "
                                                  "below", "The upper floor of a stone house slides off and crashes into the street."),
    (es.EARTHQUAKE_OLD_STREET, "slice_3", "T7"): ("a stone house across the street collapses sideways in a huge wall of dust "
                                                  "and rubble", "A stone house across the street topples over sideways in a cloud of dust."),
    (es.AVALANCHE_FOREST, "slice_2", "E7"): ("the avalanche smashes through the front of a stone farmhouse and its roof caves "
                                             "in", "The avalanche crashes through the front of a stone farmhouse and its roof caves in."),
    (es.AVALANCHE_FOREST, "slice_3", "F7"): ("the avalanche front sweeps a wooden cabin off its base and breaks it apart",
                                             "The avalanche sweeps a wooden cabin off its base and smashes it apart."),
}
# Bahadır'ın listesinden eklenmeyenler (neden) — rapor ve kilit
PARTI2_NOT_ADDED = {
    "a huge wave of mud and boulders crashes across the road, burying it completely": "yamaç S5 ile aynı (aynı dilim)",
    "the fire storm tears through the trees beside the houses, huge flames towering over the roofs": "orman L4 ile aynı",
    "the whole upper section of the tower is engulfed, flames roaring from every window": "cephe N4 ile aynı",
    "a burning section of the facade collapses and avalanches down the tower in flames": "cephe N3 ile aynı",
    "the tornado tears the roof off a building across the street and flings it down the avenue": "17 kelime (≤16)",
    "the tornado lifts a large truck and flings it across the street": "karaya vuruş C5 ile aynı (aynı dilim)",
    "the tornado rips a row of palm trees out of the ground and flings them down the street": "E4 ile aynı, 18 kelime",
    "the tornado tears the upper floors off a hotel across the avenue in a storm of debris": "17 kelime (≤16)",
    "the front wall of a stone house splits open and crashes into the street": "eski sokak R1 ile aynı",
    "the stone facade across the street peels away and collapses into a cloud of dust": "eski sokak R1 ile aynı",
    "a stone house across the street caves in and its roof drops through the floors": "eski sokak T4 ile aynı",
    "two stone houses lean together and collapse, walls burying the street in rubble": "deprem kuralı: gömülme yok",
    "the facade of the apartment block across the street cracks open and slabs fall away": "apartman P2 ile aynı",
    "a whole column of balconies on the apartment block across the street breaks away": "deprem kuralı: balkon düşmesi yok",
    "the apartment block across the street tilts and its side wall crashes into the street": "apartman Q4 ile aynı",
}


class TestParti2(unittest.TestCase):
    def test_counts_and_not_added(self):
        self.assertEqual(len(PARTI2), 26)
        self.assertEqual(len(PARTI2) + len(PARTI2_NOT_ADDED), 41)
        pool_texts = {b["text"] for e in es.EVENT_BEATS.values() for sl in ("slice_2", "slice_3") for b in e[sl].values()}
        for t in PARTI2_NOT_ADDED:
            self.assertNotIn(t, pool_texts)

    def test_every_group_at_least_four_and_spots_selectable(self):
        for e in {k[0] for k in PARTI2}:
            b = es.EVENT_BEATS[e]
            self.assertGreaterEqual(min(len(b["slice_2"]), len(b["slice_3"])), 4, e)
            for view in es.structure_views(e):
                for spot in sk.view_spots(e, view):
                    self.assertTrue(es.allowed_pairs(e, view, spot), (e, spot))


# 23 Eki (hortum denetimi): Bahadır'ın onayladığı yeni metin 16 kelimeyi aşıyor; kısaltılmadı, sınır bu maddede açık
PARTI2_LONG = {(es.MARINA_TORNADO, "Z7"): 18, (es.WILDFIRE, "K9"): 17}   # 30 Eki (2): K9 onaylı metin 17 kelime


def _make_parti2_test(event, slot, bid, text, para):
    def test(self):
        beat = es.EVENT_BEATS[event][slot][bid]
        self.assertEqual(beat["text"], text)
        self.assertLessEqual(len(text.replace("{vehicle}", "x").split()), PARTI2_LONG.get((event, bid), 16))
        self.assertEqual(es.pool_lint_hits(text.replace("{vehicle}", "vehicle")), [])
        self.assertNotIn(bid, es.RETIRED_BEATS.get(event, {}))
        for code, terms, *_ in es.EVENT_BANNED_WORDS.get(event, ()):
            self.assertEqual(es.find_terms(terms, text), [], code)
        view = es.structure_views(event)[0]
        found = 0
        for s in sk.view_spots(event, view):
            for p2, p3 in es.allowed_pairs(event, view, s):
                if (p2 if slot == "slice_2" else p3) != bid:
                    continue
                vehicles = [v for v, _ in es.event_vehicles(event, view)] if es.uses_vehicle(event) else [None]
                lo, hi = sk.count_range(event, None)
                for veh in vehicles:
                    for people in (range(lo, hi + 1) if es.has_people_rule(event) else [None]):
                        spec = es.build_spec(event, None, s, view, p2, p3, veh, people)
                        cands = es.fallback_candidates(spec)
                        self.assertTrue(cands, (s, p2, p3, veh, people))   # kod yedeği 75 kelimeye sığar
                        sl = cands[0]
                        prompt = es.assemble_prompt(spec, sl)
                        # son denetim: yakınlık kapısı (olan olaylarda), 175 kelime, sert kurallar, yumuşak kapı
                        self.assertEqual(es.final_prompt_issues(spec, sl, prompt, es.assemble_story(spec, sl)), [],
                                         (s, p2, p3, veh, people))
                        self.assertEqual(es.strict_beat_issues(spec, sl), [])
                        found += 1
                if found:
                    # GPT tarzı doğru anlatım (ana nesne tanınır, başka beat'e benzetilmez)
                    veh = "SUV" if "{vehicle}" in text else (vehicles[0] if es.uses_vehicle(event) else None)
                    spec = es.build_spec(event, None, s, view, p2, p3, veh,
                                         sk.count_range(event, None)[0] if es.has_people_rule(event) else None)
                    base = {"slice_1_rest": "x", "slice_2": es.fallback_beat_slice(spec, "slice_2"),
                            "slice_3": es.fallback_beat_slice(spec, "slice_3")}
                    self.assertEqual(es.soft_beat_issues(spec, {**base, slot: para}), [], para)
                    return
        self.fail(f"izinli çift yok: {event}/{bid}")
    return test


for (_e, _sl, _bid), (_text, _para) in PARTI2.items():
    _name = "".join(w[0] for w in _e.split()[:4]).lower()
    setattr(TestParti2, f"test_beat_{_name}_{_bid}", _make_parti2_test(_e, _sl, _bid, _text, _para))


class TestParti2WordBudget(unittest.TestCase):
    """18 Eki (2) kuru deneme: toplam kelime aşımı yedekleri -> Parti 2 olaylarına da WORD BUDGET satırı."""
    def test_budget_line_for_parti2_events(self):
        for e in (es.FLOOD, es.MUDSLIDE, es.SLOPE, es.VILLAGE, es.WILDFIRE, es.FACADE_FIRE, es.HELICOPTER,
                  es.LANDFALL, es.MARINA_TORNADO, es.AVENUE):
            self.assertIn(e, es.BUDGET_EVENTS)
            total = es.TOTAL_WORDS_BY_EVENT.get(e, es.TOTAL_WORDS)[1]
            for view in es.structure_views(e):
                spot = sk.view_spots(e, view)[0]
                p2, p3 = sorted(es.allowed_pairs(e, view, spot))[0]
                veh = es.event_vehicles(e, view)[0][0] if es.uses_vehicle(e) else None
                ppl = sk.count_range(e, None)[0] if es.has_people_rule(e) else None
                spec = es.build_spec(e, None, spot, view, p2, p3, veh, ppl)
                line = es.word_budget_line(spec)
                if e in es.CAP_BUDGET_EVENTS:   # 21 Eki (Aşama 5): sel 175 tavanlı (toplam stil ekine göre)
                    total = min(es.TOTAL_WORDS_BY_EVENT.get(e, es.TOTAL_WORDS)[1],
                                es.VOLC_MAX_PROMPT_WORDS - 3 - len(spec["suffix"].split()))
                key = len(spec["key_visual"].split())
                self.assertIn(f"the opening sentence has {key} words; slice_1_rest 6 to 10 words", line)
                self.assertIn(f"must total at most {total} words", line)
                if e not in es.CAP_BUDGET_EVENTS:   # 21 Eki: heyelan kilit cümlesi dokuyla uzadı; dilim üst
                    self.assertLessEqual(key + 10 + 16 + 16, total)   # sınırı bütçeden hesaplanır (önceki 18 + 18)
                total = es.TOTAL_WORDS_BY_EVENT.get(e, es.TOTAL_WORDS)[1]
        # şok dalgası bütçe satırı almaz (18 Eki (3): bombalar ve kül bulutu alır, tests/test_volcano_env.py)
        self.assertNotIn(ER, es.BUDGET_EVENTS)


class TestParti2DryRunGateFixes(unittest.TestCase):
    """18 Eki (2) kuru deneme: doğru anlatılmış ama nesnesi tanınmayan gerçek GPT cümleleri (eş anlamlı sadece ekleme)."""
    CASES = [   # (olay, b2, b3, dilim, gerçek GPT cümlesi)
        (es.MUDSLIDE, "H5", "M8", "slice_3",
         "Behind, the mud forces a large truck sideways, crashing it into a nearby house's facade."),
        (FT, "T6", "U1", "slice_3", "The tornado yanks a burning roof into its vortex, swirling ferociously as it moves away."),
        (es.EARTHQUAKE_OLD_STREET, "R4", "T1", "slice_3",
         "The adjacent building collapses, expanding the dust cloud, as rubble continues to fall."),
        (es.EARTHQUAKE_APARTMENT, "P4", "Q5", "slice_3",
         "The upper levels collapse directly downward, sending debris shifting, still moving at the end."),
    ]

    def _spec(self, event, b2, b3):
        view = es.structure_views(event)[0]
        spot = next(s for s in sk.view_spots(event, view) if (b2, b3) in es.allowed_pairs(event, view, s))
        veh = [v for v, _ in es.event_vehicles(event, view)][0] if es.uses_vehicle(event) else None
        ppl = sk.count_range(event, None)[0] if es.has_people_rule(event) else None
        return es.build_spec(event, None, spot, view, b2, b3, veh, ppl)

    def test_real_gpt_sentences_pass_soft_gate(self):
        for event, b2, b3, slot, text in self.CASES:
            with self.subTest(event=event, beat=b3):
                spec = self._spec(event, b2, b3)
                sl = {"slice_2": es.fallback_beat_slice(spec, "slice_2"),
                      "slice_3": es.fallback_beat_slice(spec, "slice_3"), slot: text}
                self.assertEqual(es.soft_beat_issues(spec, sl), [])

    def test_u1_vehicle_roof_still_not_u1(self):
        spec = self._spec(FT, "T4", "U1")
        sl = {"slice_2": es.fallback_beat_slice(spec, "slice_2"), "slice_3": "The vortex flings a burning tree trunk "
              "onto the van, caving in its roof."}
        self.assertIn("beat_object", {x["rule"] for x in es.soft_beat_issues(spec, sl)})


class TestFireTornadoShape(unittest.TestCase):
    def test_keys_spinning_funnel(self):
        for name, env in es.FIRE_TOR_ENVS.items():
            self.assertTrue(env["key"].startswith("A colossal spinning fire tornado, a twisting funnel several times "
                                                  "taller than the houses and trees,"), name)
        self.assertEqual(es.EVENT_KEY_VISUAL[FT], es.FIRE_TOR_ENVS["forest_edge"]["key"])

    def test_suffix_shape_sentence_and_175(self):
        for spot in sk.view_spots(FT, None):
            suf = sk.style_suffix(FT, None, spot)
            # 21 Eki (genel kalite): kısa şekil cümlesi (175). Önceki: "The fire tornado is a visibly rotating funnel
            # of flame with debris orbiting it, never a straight smoke plume or an explosion."
            self.assertIn("A rotating funnel of flame with orbiting debris, never a straight plume or explosion.", suf)
            self.assertLessEqual(len(suf.split()) + 75 + 3, 175)
        for e in es.structured_events():
            if e != FT:
                for spot in sk.view_spots(e, es.structure_views(e)[0]):
                    self.assertNotIn(sk.FIRE_TORNADO_SHAPE, sk.style_suffix(e, None, spot, es.structure_views(e)[0]))

    def test_shape_words_lint(self):
        for slot in ("slice_2", "slice_3"):
            for bid, beat in es.EVENT_BEATS[FT][slot].items():
                self.assertEqual(es.find_terms(es.FIRE_TOR_SHAPE_BANNED, beat["text"]), [], bid)
        b = es.EVENT_BEATS[FT]["slice_3"]
        for word in ("column", "plume", "pillar", "explosion", "blast"):
            b["UX"] = {"text": f"the fire tornado rips the roof off a house into its {word}", "terms": [("roof",)]}
            es.OBJECT_GROUPS[FT]["UX"] = 0
            try:
                self.assertTrue([x for x in es.pool_lint_errors() if "UX" in x and "şekil" in x], word)
            finally:
                del b["UX"]
                del es.OBJECT_GROUPS[FT]["UX"]
        # diğer olaylarda "column" serbest (ör. deprem dışı)
        self.assertNotIn("column", [w for w in es.POOL_LINT_THIN])


class TestDisabledEvents(unittest.TestCase):
    def test_shockwave_disabled_single_flag(self):
        self.assertEqual(sk.DISABLED_EVENTS, {ER})
        self.assertNotIn(ER, sk.skeleton_events("volcano_disasters"))
        self.assertEqual(sk.skeleton_events("volcano_disasters"), [es.PYROCLASTIC, VB])
        # havuz, iskelet, kilit cümle, kombinasyon denetimi duruyor
        self.assertIn(ER, sk.EVENT_SKELETONS)
        self.assertIn(ER, es.structured_events())
        self.assertIn(ER, es.EVENT_BEATS)
        # otomatik seçime girmez (domain verilse de verilmese de)
        seen = set()
        for _ in range(300):
            _, e, _ = sk.choose_event_and_ship("volcano_disasters", None, [])
            seen.add(e)
        self.assertEqual(seen, {es.PYROCLASTIC, VB})
        # Telegram menüsü aynı listeyi gösterir
        import bot
        self.assertNotIn(ER, bot.domain_events("volcano_disasters"))
        # yeniden açmak tek satır: kümeden çıkınca menüye ve seçime döner
        with patch.object(sk, "DISABLED_EVENTS", set()):
            self.assertIn(ER, sk.skeleton_events("volcano_disasters"))
            self.assertIn(ER, bot.domain_events("volcano_disasters"))


if __name__ == "__main__":
    unittest.main()
