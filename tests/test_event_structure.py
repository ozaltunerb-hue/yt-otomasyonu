#!/usr/bin/env python3
"""
Yapılandırılmış olay hattı (3 Eki 2026, Bahadır): kilit görsel, olay havuzları, esnek terimler, seçim, şema ve
Kie öncesi son denetim. KİLİT: havuz/terim/kilit görsel içerikleri Bahadır'ın onayıyla değişir. Ağ çağrısı yok.
"""
import os
import random
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.skeleton_pipeline as sk

FLOOD = es.FLOOD
TIDAL = es.TIDAL
B = es.EVENT_BEATS[FLOOD]
BT = es.EVENT_BEATS[TIDAL]


def cap(s):
    return s[0].upper() + s[1:]


def combo(view="riviera", tag=None, spot="downtown city center", event=FLOOD):
    place = f"{spot}#{view}" + (f"#{tag}" if tag else "")
    return f"urban_city_disasters|none|{event.lower()}|{place}|bystander_handheld"


S1 = "It swallows the curbs and pours between the parked cars."
S1_TIDAL = "It smashes over the railings and pours between the parked cars."
PAD = " in the churning brown water"


def fake_slices(b2, b3, vehicle, event=FLOOD, s1=S1):
    s2 = cap(es.beat_text(event, "slice_2", b2, vehicle))
    s3 = cap(es.beat_text(event, "slice_3", b3))
    if len(s2.split()) < 12:
        s2 += PAD
    if len(s3.split()) < 12:
        s3 += PAD
    return {"slice_1_rest": es.clean_slice(s1), "slice_2": es.clean_slice(s2), "slice_3": es.clean_slice(s3)}


def build(b2="V1", b3="D2", view="us_coastal_town", spot="Downtown city center", vehicle="pickup truck", event=FLOOD):
    spec = es.build_spec(event, None, spot, view, b2, b3, vehicle)
    slices = fake_slices(b2, b3, vehicle, event, S1_TIDAL if event == TIDAL else S1)
    return spec, slices, es.assemble_prompt(spec, slices)


def slices_from_message(user):
    """Sahte GPT (yapılandırılmış hat): kullanıcı mesajındaki 4-9s / 9-15s olaylarını dilim olarak döndürür."""
    line = dict(l.split(": ", 1) for l in user.splitlines() if l.startswith(("4-9s EVENT", "9-15s EVENT")))
    s2, s3 = cap(line["4-9s EVENT"]), cap(line["9-15s EVENT"])
    if len(s2.split()) < 12:
        s2 += PAD
    if len(s3.split()) < 12:
        s3 += PAD
    return {"slice_1_rest": S1_TIDAL, "slice_2": s2 + ".", "slice_3": s3 + "."}


class TestLockedData(unittest.TestCase):
    def test_key_visual_and_labels(self):
        self.assertEqual(es.EVENT_KEY_VISUAL, {
            FLOOD: "A waist-high wall of brown muddy floodwater surges into the street.",
            # 4 Eki, Bahadır onayı
            TIDAL: "A towering brown tidal wave thick with debris crashes over the waterfront onto the coastal street.",
        })
        self.assertEqual(es.SLICE_LABELS, ("0-4s", "4-9s", "9-15s"))
        self.assertEqual(es.SLICE_FIELDS, ("slice_1_rest", "slice_2", "slice_3"))
        # 4 Eki, Bahadır onayı: 6-14/10-20/40-60'tan genişletildi
        self.assertEqual(es.SLICE_WORDS, {"slice_1_rest": (6, 18), "slice_2": (10, 24), "slice_3": (10, 24)})
        self.assertEqual(es.TOTAL_WORDS, (40, 70))
        self.assertEqual(es.RECENT_BEAT_BLOCK, 3)

    def test_pools_locked(self):
        self.assertEqual({k: v["text"] for k, v in B["slice_2"].items()}, {
            "V1": "the {vehicle} is caught by the current, turns sideways and is dragged down the street",
            "V2": "the {vehicle} is swept into another parked car and both are shoved along",
            "V3": "the {vehicle} is lifted off its wheels and spun around",
            "V4": "the {vehicle} is pushed onto the sidewalk and slams into a lamppost",
            "V5": "the {vehicle} tips over onto its side in the current",
            "V6": "the {vehicle} is carried backwards down the street, bumping parked cars",
            "V7": "the {vehicle} is rammed against a building wall",
            "V8": "the {vehicle} and the car behind it are dragged away together, bumper to bumper",
        })
        self.assertEqual({k: v["text"] for k, v in B["slice_3"].items()}, {
            "D1": "a row of parked cars is ripped loose one by one and dragged away",
            "D2": "a lamppost topples into the current",
            "D3": "a street tree is uprooted and carried along",
            "D4": "a dumpster tumbles down the street and smashes into a parked car",
            "D5": "a city bus is shoved sideways by the current",
            "D6": "a low wall collapses into the water",
            "D7": "a wooden fence is torn away and carried off",
            "D8": "a car is lifted off the road and spins away downstream",
        })
        self.assertEqual(B["excluded_pairs"], {("V3", "D8"), ("V4", "D2"), ("V7", "D6"), ("V6", "D1"), ("V8", "D1")})
        self.assertEqual(B["excluded_views"], {"D7": {"gulf_metropolis"}})
        self.assertEqual(B["excluded_spots"], {"D7": {"High-rise city district"}})

    def test_vehicles_match_views(self):
        self.assertEqual(set(es.REGION_VEHICLES), set(sk.REGION_VIEWS))
        self.assertEqual({v: [n for n, _ in l] for v, l in es.REGION_VEHICLES.items()}, {
            "gulf_metropolis": ["white SUV", "pickup truck", "sedan"],
            "north_african_coast": ["small hatchback", "small car", "delivery van"],
            "us_coastal_town": ["pickup truck", "SUV", "sedan"],
            "north_european_seaside": ["small car", "hatchback", "delivery van"],
            "riviera": ["small car", "hatchback", "delivery van"],
            "east_asian_coast": ["small boxy car", "compact car", "small van"],
        })

    def test_prompt_limit_below_seedance(self):
        # Kie seedance-2-fast: prompt en fazla 20000 karakter (doküman, 4 Eki). Bizim sınırımız çok altında.
        self.assertEqual(es.SEEDANCE_PROMPT_LIMIT, 20000)
        self.assertEqual(es.MAX_PROMPT_CHARS, 1400)
        self.assertLess(es.MAX_PROMPT_CHARS, es.SEEDANCE_PROMPT_LIMIT)

    def test_structured_events(self):
        # 4 Eki: kıyı dev dalga da yapılandırılmış hatta; diğer olaylar eski yolda
        self.assertEqual(es.structured_events(), (FLOOD, TIDAL))
        self.assertEqual(TIDAL, "Tidal wave surges over a coastal city street")
        self.assertFalse(es.is_structured("Rogue wave breaks over the rail onto the pool deck"))


class TestFlexibleTerms(unittest.TestCase):
    """Her olay: kendi cümlesi + doğal varyantlar geçer (farklı kelime seçimi boşa ret olmasın)."""

    OK = {
        "V1": ["The white SUV is caught by the current, turns sideways and is dragged down the street.",
               "The current catches the sedan, swings it broadside and drags it along the street.",
               "The pickup truck spins side-on in the torrent and is swept down the road.",
               "Caught by the flow, the SUV twists sideways and slides down the street."],
        "V2": ["The small car is swept into another parked car and both are shoved along.",
               "The current slams the hatchback against a second parked car, pushing both down the street.",
               "The delivery van crashes into the next parked car and the two are carried along."],
        "V3": ["The sedan is lifted off its wheels and spun around.",
               "The water heaves the pickup truck off the ground and it whirls around.",
               "The SUV is picked up by the torrent and rotates in the brown water."],
        "V4": ["The compact car is pushed onto the sidewalk and slams into a lamppost.",
               "The current shoves the small van over the curb into a streetlight.",
               "The hatchback is forced onto the pavement and hits a light pole."],
        "V5": ["The small car tips over onto its side in the current.",
               "The delivery van topples onto its side as the water hits it.",
               "The current flips the sedan and it rolls over in the flow.",
               "The SUV overturns in the brown water."],
        "V6": ["The pickup truck is carried backwards down the street, bumping parked cars.",
               "The current drags the hatchback in reverse down the street.",
               "The small car slides rear-first down the road, knocking into parked cars."],
        "V7": ["The delivery van is rammed against a building wall.",
               "The current slams the sedan into the front of a house.",
               "The water pins the SUV against a shopfront facade."],
        "V8": ["The small car and the car behind it are dragged away together, bumper to bumper.",
               "The current sweeps the sedan and the next car away side by side.",
               "The hatchback and a parked van are pulled down the street together."],
        "D1": ["A row of parked cars is ripped loose one by one and dragged away.",
               "One after another, the parked cars are torn loose and swept down the street.",
               "The water peels a line of parked vehicles off the curb and carries them away."],
        "D2": ["A lamppost topples into the current.",
               "A streetlight snaps and falls into the brown water.",
               "The light pole bends and goes down into the flood."],
        "D3": ["A street tree is uprooted and carried along.",
               "The water rips a tall tree out of the sidewalk and sweeps it away.",
               "A tree topples and is carried down the street."],
        "D4": ["A dumpster tumbles down the street and smashes into a parked car.",
               "A green trash bin rolls through the water and slams into a car.",
               "A metal waste container barrels down the road."],
        "D5": ["A city bus is shoved sideways by the current.",
               "The water pushes a bus across the street.",
               "A bus skids sideways in the torrent."],
        "D6": ["A low wall collapses into the water.",
               "A garden wall crumbles under the force of the flood.",
               "The brick wall gives way and falls into the current."],
        "D7": ["A wooden fence is torn away and carried off.",
               "The current rips a picket fence from the ground.",
               "A section of fencing breaks and is swept down the street."],
        "D8": ["A car is lifted off the road and spins away downstream.",
               "The water heaves a parked sedan off the ground and it spins away.",
               "A van is picked up by the flood and whirls down the street."],
    }
    # Olayı göstermeyen dilimler kalmalı
    BAD = {
        "V1": "The sedan sits in the water as rain falls.",
        "V4": "The compact car is pushed onto the sidewalk.",
        "V5": "The small car shakes in the current.",
        "V6": "The hatchback rocks in place as water rushes past.",
        "D2": "A tree falls into the brown water.",
        "D4": "A parked car rolls down the street.",
        "D5": "A truck is shoved sideways by the current.",
        "D7": "A low wall collapses into the water.",
    }

    def slot(self, bid):
        return "slice_2" if bid.startswith("V") else "slice_3"

    def test_every_beat_has_variants(self):
        self.assertEqual(set(self.OK), set(B["slice_2"]) | set(B["slice_3"]))

    def test_canonical_and_variants_pass(self):
        for bid, sentences in self.OK.items():
            groups = B[self.slot(bid)][bid]["terms"]
            canonical = cap(es.beat_text(FLOOD, self.slot(bid), bid, "white SUV"))
            for s in [canonical] + sentences:
                with self.subTest(beat=bid, text=s):
                    self.assertEqual(es.missing_term_groups(groups, s), [])

    def test_wrong_event_fails(self):
        for bid, s in self.BAD.items():
            with self.subTest(beat=bid):
                self.assertTrue(es.missing_term_groups(B[self.slot(bid)][bid]["terms"], s))

    def test_vehicle_terms(self):
        cases = {("gulf_metropolis", "white SUV"): "The white SUV spins.",
                 ("us_coastal_town", "pickup truck"): "The truck spins.",
                 ("riviera", "delivery van"): "The van spins.",
                 ("east_asian_coast", "small boxy car"): "The boxy little car spins.",
                 ("north_african_coast", "small hatchback"): "The hatchback spins."}
        for (view, v), text in cases.items():
            with self.subTest(vehicle=v):
                self.assertTrue(es.find_terms(es.vehicle_terms(view, v), text))
        self.assertFalse(es.find_terms(es.vehicle_terms("riviera", "delivery van"), "The car spins."))


class TestExhaustive(unittest.TestCase):
    """Tüm izinli olay çiftleri × tüm görünümler × görünüme uyan tüm çekim noktaları × görünümün tüm araçları:
    kurulan her prompt son denetimden geçer, kilit görsel ve etiket sırası doğru."""

    def test_all_combinations_pass_final_check(self):
        n = 0
        head = f"0-4s: {es.EVENT_KEY_VISUAL[FLOOD]} "
        longest = 0
        for view in sk.REGION_VIEWS:
            for spot in sk.view_spots(FLOOD, view):
                pairs = es.allowed_pairs(FLOOD, view, spot)
                self.assertTrue(pairs)
                for b2, b3 in pairs:
                    for vehicle, _ in es.REGION_VEHICLES[view]:
                        spec, slices, prompt = build(b2, b3, view, spot, vehicle)
                        issues = es.final_prompt_issues(spec, slices, prompt, es.assemble_story(spec, slices))
                        if issues:
                            self.fail(f"{view}/{spot}/{b2}+{b3}/{vehicle}: {issues}\n{prompt}")
                        self.assertTrue(prompt.startswith(head))
                        i = [prompt.index(f"{l}: ") for l in es.SLICE_LABELS]
                        self.assertEqual(i, sorted(i))
                        longest = max(longest, len(prompt))
                        n += 1
        self.assertGreater(n, 3000)
        self.assertLess(longest, es.MAX_PROMPT_CHARS)

    def test_longest_realistic_story_fits(self):
        # 70 kelime, kelime başına 7 harf (ölçülen ortalama 5,58) + en uzun stil eki: sınırın altında
        spec = es.build_spec(FLOOD, None, "Downtown city center", "east_asian_coast", "V1", "D1", "small boxy car")
        w = "abcdefg"
        slices = {"slice_1_rest": es.clean_slice(" ".join([w] * 18)),
                  "slice_2": es.clean_slice("small boxy car sideways dragged " + " ".join([w] * 15)),
                  "slice_3": es.clean_slice("row cars ripped " + " ".join([w] * 18))}
        self.assertEqual(len(es.plain_story(spec, slices).split()), 70)
        self.assertLess(len(es.assemble_prompt(spec, slices)), es.MAX_PROMPT_CHARS)

    def test_total_words_replace_general_length_rule(self):
        import core.creative_pipeline as cp
        spec = es.build_spec(FLOOD, None, "Downtown city center", "us_coastal_town", "V1", "D2", "pickup truck")
        pad = " ".join(["brown"] * 8)
        sl = {"slice_1_rest": es.clean_slice("It swallows the curbs and pours between the parked cars " + pad),
              "slice_2": es.clean_slice("The pickup truck is caught by the current, turns sideways and is dragged "
                                        "down the street " + pad[:17]),
              "slice_3": es.clean_slice("A lamppost topples into the current and crashes into the churning water " + pad)}
        n = len(es.plain_story(spec, sl).split())
        self.assertTrue(60 < n <= 70, n)
        self.assertEqual(es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl)), [])
        self.assertNotIn("length", [i["rule"] for i in cp.structured_issues(spec, sl, [])])
        # diğer olaylarda genel 40-60 aynen
        self.assertIn("length", [i["rule"] for i in cp.story_rule_issues(
            "Rogue wave breaks over the rail onto the pool deck", None, " ".join(["wave"] * 65))])
        # 70 üstü yapılandırılmış olayda kalır
        sl2 = {**sl, "slice_3": es.clean_slice(sl["slice_3"] + " " + " ".join(["water"] * 6))}
        self.assertIn("total_words", [i["rule"] for i in es.final_prompt_issues(spec, sl2, es.assemble_prompt(spec, sl2))])

    def test_prompt_chars_feedback_in_quality_gate(self):
        spec = es.build_spec(FLOOD, None, "Downtown city center", "east_asian_coast", "V1", "D2", "small boxy car")
        long = "extraordinarilyextraordinarily"
        sl = {"slice_1_rest": es.clean_slice(" ".join([long] * 8)),
              "slice_2": es.clean_slice("The small boxy car turns sideways and is dragged " + " ".join([long] * 8)),
              "slice_3": es.clean_slice("A lamppost topples into the current " + " ".join([long] * 8))}
        issue = [i for i in es.slice_issues(spec, sl) if i["rule"] == "prompt_chars"]
        self.assertEqual(len(issue), 1)
        self.assertIn("shorten the three fields", issue[0]["feedback"])
        final = [i for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl)) if i["rule"] == "prompt_chars"]
        self.assertEqual(len(final), 1)   # son denetimde de var (kapalı başarısızlık), çift değil


class TestSelection(unittest.TestCase):
    def setUp(self):
        es._BEAT_MEMORY.clear()

    def test_combo_parse(self):
        self.assertEqual(es.beats_of_combo(combo(tag="V3+D5")), "V3+D5")
        self.assertIsNone(es.beats_of_combo(combo()))
        self.assertIsNone(es.beats_of_combo("bozuk"))
        self.assertEqual(sk.view_of_combo(combo(view="riviera")), "riviera")

    def test_excluded_never_chosen(self):
        rng = random.Random(1)
        for _ in range(400):
            p = es.choose_beats(FLOOD, "riviera", "Downtown city center", [], rng)
            self.assertNotIn(p, B["excluded_pairs"])
        for _ in range(200):
            self.assertNotEqual(es.choose_beats(FLOOD, "gulf_metropolis", "Downtown city center", [], rng)[1], "D7")
            self.assertNotEqual(es.choose_beats(FLOOD, "riviera", "High-rise city district", [], rng)[1], "D7")

    def test_recent_beats_blocked(self):
        hist = [combo(tag="V1+D1"), combo(tag="V2+D2"), combo(tag="V3+D3")]
        rng = random.Random(2)
        for _ in range(200):
            b2, b3 = es.choose_beats(FLOOD, "riviera", "Downtown city center", hist, rng)
            self.assertNotIn(b2, {"V1", "V2", "V3"})
            self.assertNotIn(b3, {"D1", "D2", "D3"})
        # 4. eski üretim engellenmez
        hist = [combo(tag="V4+D4")] + hist
        seen = {es.choose_beats(FLOOD, "riviera", "Downtown city center", hist, rng)[0] for _ in range(300)}
        self.assertIn("V4", seen)

    def test_lru_cycles_all_pairs(self):
        # 59 izinli çift. Son-3 engeli döngü sonunda birkaç çifti erteleyebilir; ölçüm (300 tohum): ilk tekrar en
        # erken 48. üretimde, 59 üretimde en az 55 farklı çift.
        pairs = es.allowed_pairs(FLOOD, "riviera", "Downtown city center")
        self.assertEqual(len(pairs), 59)
        for seed in range(40):
            es._BEAT_MEMORY.clear()
            rng, hist, chosen = random.Random(seed), [], []
            for _ in range(len(pairs)):
                p = es.choose_beats(FLOOD, "riviera", "Downtown city center", hist, rng)
                chosen.append(p)
                hist.append(combo(tag=es.beat_tag(*p)))
            with self.subTest(seed=seed):
                self.assertEqual(len(set(chosen[:45])), 45)
                self.assertGreaterEqual(len(set(chosen)), 55)

    def test_memory_counts_unfinished(self):
        es.remember_beats(FLOOD, "V5+D5")
        self.assertEqual(es.beat_history(FLOOD, [combo(tag="V1+D1")]), ["V1+D1", "V5+D5"])
        for _ in range(50):
            b2, b3 = es.choose_beats(FLOOD, "riviera", "Downtown city center", [], random.Random())
            self.assertNotEqual(b2, "V5")
            self.assertNotEqual(b3, "D5")

    def test_other_event_history_ignored(self):
        hist = [combo(tag="V1+D1", event="Tidal wave surges over a coastal city street")]
        self.assertEqual(es.beat_history(FLOOD, hist), [])

    def test_no_candidates_raises(self):
        b = es.EVENT_BEATS[FLOOD]
        saved = b["excluded_pairs"]
        try:
            b["excluded_pairs"] = {(v, d) for v in b["slice_2"] for d in b["slice_3"]}
            with self.assertRaises(es.StructureError):
                es.choose_beats(FLOOD, "riviera", "Downtown city center", [])
        finally:
            b["excluded_pairs"] = saved

    def test_vehicle_from_view(self):
        for view, vehicles in es.REGION_VEHICLES.items():
            for _ in range(20):
                self.assertIn(es.choose_vehicle(view), [v for v, _ in vehicles])
        with self.assertRaises(es.StructureError):
            es.choose_vehicle("mars")


class TestSchemaParse(unittest.TestCase):
    GOOD = {"slice_1_rest": "It swallows the curbs and pours between the parked cars",
            "slice_2": "The pickup truck spins sideways and is dragged down the street!",
            "slice_3": "  A lamppost   snaps and falls into the brown water.  "}

    def test_schema_strict(self):
        s = es.SLICE_SCHEMA
        self.assertTrue(s["strict"])
        self.assertFalse(s["schema"]["additionalProperties"])
        self.assertEqual(s["schema"]["required"], list(es.SLICE_FIELDS))

    def test_good_cleaned(self):
        out = es.parse_slices(self.GOOD)
        self.assertEqual(out["slice_1_rest"], "It swallows the curbs and pours between the parked cars.")
        self.assertEqual(out["slice_2"], "The pickup truck spins sideways and is dragged down the street.")
        self.assertEqual(out["slice_3"], "A lamppost snaps and falls into the brown water.")

    def test_bad_raise(self):
        cases = {"liste": ["x"], "eksik": {k: v for k, v in self.GOOD.items() if k != "slice_3"},
                 "fazla": {**self.GOOD, "story": "x"}, "boş": {**self.GOOD, "slice_2": "   "},
                 "sayı": {**self.GOOD, "slice_2": 5}, "None": None}
        for name, raw in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(es.StructureError):
                    es.parse_slices(raw)


class TestFinalCheckNegatives(unittest.TestCase):
    def codes(self, spec, slices, prompt, story=None):
        return {i["rule"] for i in es.final_prompt_issues(spec, slices, prompt, story)}

    def test_good(self):
        spec, slices, prompt = build()
        self.assertEqual(es.final_prompt_issues(spec, slices, prompt, es.assemble_story(spec, slices)), [])

    def test_key_visual_removed_or_changed(self):
        spec, slices, prompt = build()
        bad = prompt.replace("waist-high wall of brown muddy floodwater", "low wave of foam")
        self.assertTrue({"rebuild", "key_visual"} <= self.codes(spec, slices, bad))
        self.assertIn("key_visual", self.codes({**spec, "key_visual": "A wave."}, slices, prompt))

    def test_labels_tampered(self):
        spec, slices, prompt = build()
        self.assertIn("labels", self.codes(spec, slices, prompt.replace("4-9s: ", "")))
        self.assertIn("rebuild", self.codes(spec, slices, prompt.replace("4-9s:", "4–9s:")))
        sl = {**slices, "slice_3": "At 9-15s a lamppost snaps and falls into the brown water."}
        self.assertIn("slice_label", self.codes(spec, sl, es.assemble_prompt(spec, sl)))

    def test_suffix_tampered(self):
        spec, slices, prompt = build()
        self.assertIn("rebuild", self.codes(spec, slices, prompt.replace("no zoom, no cuts", "zoom in")))
        self.assertIn("suffix", self.codes({**spec, "suffix": spec["suffix"] + " Extra."}, slices, prompt))

    def test_story_mismatch(self):
        spec, slices, prompt = build()
        self.assertIn("rebuild_story", self.codes(spec, slices, prompt, "0-4s: something else"))

    def test_word_limits(self):
        spec, slices, _ = build()
        sl = {**slices, "slice_2": "The pickup truck spins sideways."}
        c = self.codes(spec, sl, es.assemble_prompt(spec, sl))
        self.assertIn("slice_words", c)
        sl = {**slices, "slice_2": es.clean_slice("The pickup truck turns sideways and is dragged " + "far " * 17)}
        self.assertIn("slice_words", self.codes(spec, sl, es.assemble_prompt(spec, sl)))   # 25 kelime
        sl = {**slices, "slice_2": es.clean_slice("The pickup truck turns sideways and is dragged " + "far " * 16)}
        self.assertNotIn("slice_words", self.codes(spec, sl, es.assemble_prompt(spec, sl)))   # 24 kelime sınırda

    def test_beat_and_vehicle_missing(self):
        spec, slices, _ = build("V4", "D3", vehicle="SUV")
        sl = {**slices, "slice_2": "The sedan is pushed onto the sidewalk and slams into a lamppost in the water."}
        self.assertIn("beat_vehicle", self.codes(spec, sl, es.assemble_prompt(spec, sl)))
        sl = {**slices, "slice_3": "A low wall collapses into the water as the street fills with debris."}
        self.assertIn("beat_terms", self.codes(spec, sl, es.assemble_prompt(spec, sl)))

    def test_forbidden_words(self):
        spec, slices, _ = build()
        for word, rule in (("camera", "b_no_camera_words"), ("footage", "b_no_camera_words"),
                           ("about to", "c_no_meta_or_waiting"), ("harmlessly", "d_no_scale_reducers"),
                           ("floats", "d_no_scale_reducers")):
            sl = {**slices, "slice_1_rest": es.clean_slice(f"It swallows the curbs, {word} the parked cars")}
            with self.subTest(word=word):
                self.assertIn(rule, self.codes(spec, sl, es.assemble_prompt(spec, sl)))

    def test_newline_and_length(self):
        spec, slices, _ = build()
        sl = {**slices, "slice_1_rest": "It swallows the curbs\nand pours between the parked cars."}
        self.assertIn("slice_newline", self.codes(spec, sl, es.assemble_prompt(spec, sl)))
        long_spec = {**spec}
        prompt = es.assemble_prompt(long_spec, slices) + " x" * 800
        self.assertIn("prompt_chars", self.codes(spec, slices, prompt))

    def test_not_structured_event(self):
        with self.assertRaises(es.StructureError):
            es.build_spec("Rogue wave breaks over the rail onto the pool deck", None, "x", None, "V1", "D1", "car")


class TestTidal(unittest.TestCase):
    """4 Eki, Bahadır onayı: kıyı dev dalga selin yapısında. KİLİT: havuz ve yasaklar onaysız değişmez."""

    TIDAL_SPOTS = ["Coastal road below a seafront promenade", "Coastal street of low shopfronts",
                   "Coastal avenue behind a seawall"]

    def setUp(self):
        es._BEAT_MEMORY.clear()

    def test_pools_locked(self):
        self.assertEqual({k: v["text"] for k, v in BT["slice_2"].items()}, {
            "T1": "the {vehicle} is lifted and flung against a storefront",
            "T2": "the {vehicle} is lifted and carried down the street on top of the surge",
            "T3": "the {vehicle} is slammed into the car parked ahead and both are shoved along",
            "T4": "the {vehicle} is spun sideways and dragged along the street",
            "T5": "the {vehicle} tips over onto its side in the churning water",
            "T6": "the {vehicle} is pushed onto the sidewalk and slams into a lamppost",
            "T7": "the {vehicle} is carried backwards down the street, bumping parked cars",
            "T8": "the {vehicle} and the car behind it are dragged away together, bumper to bumper",
        })
        self.assertEqual({k: v["text"] for k, v in BT["slice_3"].items()}, {
            "W1": "a row of parked vehicles is ripped loose one by one and washed away",
            "W2": "a lamppost topples into the surge",
            "W3": "a street tree is uprooted and carried along",
            "W4": "a roadside kiosk is torn off its base and swept away",
            "W5": "a city bus is shoved sideways by the surge",
            "W6": "a low wall collapses into the water",
            "W7": "shopfront windows burst and the surge pours through, carrying out chairs and tables",
            "W8": "a dumpster tumbles down the street and smashes into a parked car",
        })
        self.assertEqual(BT["excluded_pairs"], {("T6", "W2"), ("T1", "W7"), ("T2", "W1"), ("T8", "W1"), ("T3", "W8")})
        self.assertEqual(BT["excluded_views"], {})
        # Kamera seawall'un üstünde: "alçak duvar çöker" kameranın durduğu duvar gibi çizilir
        self.assertEqual(BT["excluded_spots"], {"W6": {"Coastal avenue behind a seawall"}})

    def test_spots_and_views(self):
        self.assertIn(TIDAL, sk.REGION_VIEW_EVENTS)   # araç bölge görünümünden gelir
        self.assertEqual(list(sk.EVENT_SKELETONS[TIDAL]["spots"]), self.TIDAL_SPOTS)
        self.assertEqual(sum(len(sk.view_spots(TIDAL, v)) for v in sk.REGION_VIEWS), 17)
        for view in sk.REGION_VIEWS:
            self.assertTrue(es.REGION_VEHICLES[view])

    def test_key_visual_passes_trigger_and_event_name(self):
        import core.creative_pipeline as cp
        self.assertEqual(cp.EVENT_REQUIRED[TIDAL], [])
        key = es.EVENT_KEY_VISUAL[TIDAL]
        found = {i["rule"] for i in cp.story_rule_issues(TIDAL, None, key)}
        self.assertNotIn("a_trigger_first", found)
        self.assertNotIn("e_event_and_ship_named", found)
        self.assertNotIn("required", found)
        # kilit cümle olmadan tetik kuralı kalır (kural gevşemedi)
        self.assertIn("a_trigger_first", {i["rule"] for i in cp.story_rule_issues(TIDAL, None, "Cars sit on the street.")})

    def test_canonical_terms_pass(self):
        for slot in ("slice_2", "slice_3"):
            for bid, beat in BT[slot].items():
                for view, vehicles in es.REGION_VEHICLES.items():
                    for vehicle, _ in vehicles:
                        text = cap(es.beat_text(TIDAL, slot, bid, vehicle))
                        with self.subTest(beat=bid, vehicle=vehicle):
                            self.assertEqual(es.missing_term_groups(beat["terms"], text), [])

    def test_variants_and_wrong_event(self):
        ok = {"T1": "The surge heaves the sedan up and hurls it into a shop window.",
              "T2": "The pickup truck rides on top of the surge and is swept down the street.",
              "T4": "The SUV whirls broadside and is dragged along the road.",
              "W1": "One after another, the parked cars are torn loose and washed away.",
              "W4": "A newsstand is ripped off its base and carried down the street.",
              "W7": "The shop glass shatters and the water carries tables and chairs out.",
              "W8": "A green trash bin rolls through the water and slams into a car."}
        bad = {"T1": "The sedan is lifted by the water.",
               "T6": "The SUV is pushed onto the sidewalk.",
               "W4": "A low wall collapses into the water.",
               "W7": "Shop windows burst as the water rises."}
        for bid, s in ok.items():
            slot = "slice_2" if bid.startswith("T") else "slice_3"
            with self.subTest(ok=bid):
                self.assertEqual(es.missing_term_groups(BT[slot][bid]["terms"], s), [])
        for bid, s in bad.items():
            slot = "slice_2" if bid.startswith("T") else "slice_3"
            with self.subTest(bad=bid):
                self.assertTrue(es.missing_term_groups(BT[slot][bid]["terms"], s))

    def test_all_combinations_pass_final_check(self):
        n, longest = 0, 0
        head = f"0-4s: {es.EVENT_KEY_VISUAL[TIDAL]} "
        for view in sk.REGION_VIEWS:
            for spot in sk.view_spots(TIDAL, view):
                pairs = es.allowed_pairs(TIDAL, view, spot)
                self.assertTrue(pairs, (view, spot))
                for b2, b3 in pairs:
                    self.assertNotIn((b2, b3), BT["excluded_pairs"])
                    for vehicle, _ in es.REGION_VEHICLES[view]:
                        spec, slices, prompt = build(b2, b3, view, spot, vehicle, event=TIDAL)
                        issues = es.final_prompt_issues(spec, slices, prompt, es.assemble_story(spec, slices))
                        if issues:
                            self.fail(f"{view}/{spot}/{b2}+{b3}/{vehicle}: {issues}\n{prompt}")
                        self.assertTrue(prompt.startswith(head))
                        i = [prompt.index(f"{l}: ") for l in es.SLICE_LABELS]
                        self.assertEqual(i, sorted(i))
                        longest = max(longest, len(prompt))
                        n += 1
        # 12 görünüm×spot × 59 çift + 5 seawall × 51 çift = 708 + 255 = 963 çift; × 3 araç
        self.assertEqual(n, 2865)
        self.assertLess(longest, es.MAX_PROMPT_CHARS)

    def test_w6_never_on_seawall(self):
        for view in sk.REGION_VIEWS:
            self.assertNotIn("W6", {d for _, d in es.allowed_pairs(TIDAL, view, "Coastal avenue behind a seawall")})
            self.assertIn("W6", {d for _, d in es.allowed_pairs(TIDAL, view, "Coastal road below a seafront promenade")})

    def test_recent_beats_blocked_and_events_separate(self):
        hist = [combo(tag="T1+W1", event=TIDAL), combo(tag="T2+W2", event=TIDAL), combo(tag="T3+W3", event=TIDAL),
                combo(tag="V4+D4")]
        rng = random.Random(3)
        for _ in range(200):
            b2, b3 = es.choose_beats(TIDAL, "riviera", "Coastal road below a seafront promenade", hist, rng)
            self.assertNotIn(b2, {"T1", "T2", "T3"})
            self.assertNotIn(b3, {"W1", "W2", "W3"})
        self.assertEqual(es.beat_history(TIDAL, hist), ["T1+W1", "T2+W2", "T3+W3"])
        es.remember_beats(FLOOD, "V5+D5")
        self.assertEqual(es.beat_history(TIDAL, []), [])


class TestNeverRunsOutOfCandidates(unittest.TestCase):
    """Son RECENT_BEAT_BLOCK üretim en kötü durumda RECENT_BEAT_BLOCK farklı 4-9s ve RECENT_BEAT_BLOCK farklı
    9-15s olayını engeller. Her yapılandırılmış olay × her görünüm × her spot için, olası her engel kümesinde en az
    bir izinli çift kalır: choose_beats StructureError'a düşmez."""

    def test_every_block_leaves_a_pair(self):
        from itertools import combinations
        k = es.RECENT_BEAT_BLOCK
        for event in es.structured_events():
            b = es.EVENT_BEATS[event]
            blocks2 = [set(c) for c in combinations(b["slice_2"], k)]
            blocks3 = [set(c) for c in combinations(b["slice_3"], k)]
            for view in sk.REGION_VIEWS:
                for spot in sk.view_spots(event, view):
                    pairs = es.allowed_pairs(event, view, spot)
                    worst = min(sum(1 for v, d in pairs if v not in x2 and d not in x3)
                                for x2 in blocks2 for x3 in blocks3)
                    with self.subTest(event=event, view=view, spot=spot):
                        self.assertGreater(worst, 0)

    def test_choose_beats_long_run(self):
        # Gerçek akış: her seçim geçmişe eklenir; 200 üretim boyunca hiç aday tükenmez
        for event, spot in ((FLOOD, "Downtown city center"), (TIDAL, "Coastal avenue behind a seawall")):
            for view in sk.REGION_VIEWS:
                if spot not in sk.view_spots(event, view):
                    continue
                es._BEAT_MEMORY.clear()
                rng, hist = random.Random(7), []
                for _ in range(200):
                    p = es.choose_beats(event, view, spot, hist, rng)
                    hist.append(combo(view=view, tag=es.beat_tag(*p), spot=spot.lower(), event=event))
        es._BEAT_MEMORY.clear()


if __name__ == "__main__":
    unittest.main()
