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
S1_TIDAL = "It smashes over the railings as {word} pedestrians run from the wave."
PAD = " in the churning brown water"


def s1_tidal(people):
    return S1_TIDAL.format(word=es.NUMBER_WORDS[people])


def fake_slices(b2, b3, vehicle, event=FLOOD, s1=S1):
    s2 = cap(es.beat_text(event, "slice_2", b2, vehicle))
    s3 = cap(es.beat_text(event, "slice_3", b3))
    if len(s2.split()) < 12:
        s2 += PAD
    if len(s3.split()) < 12:
        s3 += PAD
    return {"slice_1_rest": es.clean_slice(s1), "slice_2": es.clean_slice(s2), "slice_3": es.clean_slice(s3)}


def build(b2="V1", b3="D2", view="us_coastal_town", spot="Downtown city center", vehicle="pickup truck", event=FLOOD,
          people=5):
    people = people if es.has_people_rule(event) else None
    spec = es.build_spec(event, None, spot, view, b2, b3, vehicle, people)
    slices = fake_slices(b2, b3, vehicle, event, s1_tidal(people) if event == TIDAL else S1)
    return spec, slices, es.assemble_prompt(spec, slices)


def slices_from_message(user):
    """Sahte GPT (yapılandırılmış hat): kullanıcı mesajındaki 4-9s / 9-15s olaylarını ve kaçan kişi sayısını (N)
    dilim olarak döndürür."""
    line = dict(l.split(": ", 1) for l in user.splitlines()
                if l.startswith(("4-9s EVENT", "9-15s EVENT", "PEOPLE RUNNING AWAY")))
    s2, s3 = cap(line["4-9s EVENT"]), cap(line["9-15s EVENT"])
    if len(s2.split()) < 12:
        s2 += PAD
    if len(s3.split()) < 12:
        s3 += PAD
    word = line["PEOPLE RUNNING AWAY"].split()[0]
    return {"slice_1_rest": S1_TIDAL.format(word=word), "slice_2": s2 + ".", "slice_3": s3 + "."}


class TestLockedData(unittest.TestCase):
    def test_key_visual_and_labels(self):
        self.assertEqual(es.EVENT_KEY_VISUAL, {
            FLOOD: "A waist-high wall of brown muddy floodwater surges into the street.",
            # 4 Eki, Bahadır onayı
            TIDAL: "A towering brown tidal wave thick with debris crashes over the waterfront onto the coastal street.",
            # 4 Eki, TASLAK (Bahadır hazırlığı, onay bekliyor): heyelan
            es.MUDSLIDE: "A massive wall of brown mud and rocks tears loose from the saturated hillside and pours "
                         "down the steep street.",
            es.SLOPE: "The saturated slope collapses and a fast torrent of brown mud and rocks surges across the road.",
            es.VILLAGE: "A massive torrent of brown mud, logs and rocks bursts through the drenched hillside village.",
            # 4 Eki, TASLAK (Bahadır hazırlığı, onay bekliyor): hortum
            es.LANDFALL: "A violent tornado makes landfall on the waterfront, tearing roofs and signs into the air.",
            # 4 Eki, Bahadır: marina yeniden tasarımı
            es.MARINA_TORNADO: "A violent tornado tears in from the sea onto the marina quay, ripping palms and "
                               "umbrellas off the ground.",
            es.AVENUE: "A violent tornado sweeps down a palm-lined coastal avenue, hurling signs, branches and debris "
                       "along the road.",
            # 8 Eki, TASLAK: yangın kilit cümleleri (Bahadır'ın metni birebir; TestFireStructure ayrıca kilitler)
            es.WILDFIRE: "A towering wall of flames sweeps down the forested slope and slams into the edge of the "
                         "neighborhood, igniting roofs and trees.",
            es.FACADE_FIRE: "Flames race up the glass facade of a tower, blowing out windows and raining burning "
                            "debris onto the street.",
            es.FIRE_TORNADO: "A violent fire tornado tears across a burning roadside, hurling flames, burning "
                             "branches and embers across the road.",
            # 10 Eki, Bahadır onayı: helikopter (TestHelicopter ayrıca kilitler)
            es.HELICOPTER: "A firefighting helicopter swoops over a hillside neighborhood and drops a huge load of "
                           "water onto the wall of flames racing toward the houses.",
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
        self.assertEqual(es.structured_events(), (FLOOD, TIDAL, es.MUDSLIDE, es.SLOPE, es.VILLAGE,
                                                  es.LANDFALL, es.MARINA_TORNADO, es.AVENUE,
                                                  es.WILDFIRE, es.FACADE_FIRE, es.FIRE_TORNADO,   # 8 Eki
                                                  es.HELICOPTER))   # 10 Eki
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
            "T2": "the {vehicle} is carried down the street by the surge",   # 4 Eki: havalanma yok
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
              "T2": "The surge sweeps the pickup truck along the street.",
              "T4": "The SUV whirls broadside and is dragged along the road.",
              "W1": "One after another, the parked cars are torn loose and washed away.",
              "W4": "A newsstand is ripped off its base and carried down the street.",
              "W7": "The shop glass shatters and the water carries tables and chairs out.",
              "W8": "A green trash bin rolls through the water and slams into a car."}
        # 4 Eki, Bahadır: kuru provada reddedilen ifadeler artık geçer
        ok.update({"W1": "A sequence of parked vehicles is torn free, each swept away in a chaotic stream.",
                   "T7": "The SUV is thrust backward, colliding forcefully with parked trucks."})
        bad = {"T1": "The sedan is lifted by the water.",
               "T7": "The SUV is thrust forward into parked trucks.",
               "T2": "The SUV is lifted on top of the surge.",
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

    def test_people_count_range(self):
        self.assertEqual(sk.count_range(TIDAL, None), (3, 6))
        self.assertEqual(sk.count_range(FLOOD, None), (2, 10))   # diğer olaylar aynı
        self.assertEqual(sk.EVENT_COUNT, {TIDAL: (3, 6), es.MUDSLIDE: (3, 6), es.SLOPE: (3, 6), es.VILLAGE: (3, 6),
                                          es.LANDFALL: (3, 6), es.MARINA_TORNADO: (3, 6), es.AVENUE: (3, 6),
                                          # 8 Eki (TASLAK): yangın
                                          es.WILDFIRE: (3, 6), es.FACADE_FIRE: (3, 6), es.FIRE_TORNADO: (3, 6),
                                          es.HELICOPTER: (3, 6)})   # 10 Eki

    def test_slice_rules_locked(self):
        # selde dilim kapısı yok; heyelan (TASLAK) aynı mekanizma
        self.assertEqual(set(es.SLICE_RULES), {TIDAL, es.MUDSLIDE, es.SLOPE, es.VILLAGE,
                                               es.LANDFALL, es.MARINA_TORNADO, es.AVENUE,
                                               es.WILDFIRE, es.FACADE_FIRE, es.FIRE_TORNADO,   # 8 Eki: yangın
                                               es.HELICOPTER})   # 10 Eki
        r = {x["rule"]: x for x in es.SLICE_RULES[TIDAL]}
        self.assertEqual(set(r), {"slice_flee", "slice_count"})
        self.assertEqual(r["slice_flee"]["terms"], ("run", "ran", "running", "flee", "fled", "fleeing", "sprint",
                                                    "scatter", "dash", "bolt", "race",
                                                    "scramble", "dart", "hurry"))
        self.assertTrue(r["slice_count"]["people"])
        self.assertNotIn("terms", r["slice_count"])   # terim koddan: spec'teki N'in kelimesi
        self.assertEqual(es.NUMBER_WORDS, {3: "three", 4: "four", 5: "five", 6: "six"})
        self.assertEqual(r["slice_flee"]["feedback"], "'slice_1_rest' must show people running away from the wave.")
        self.assertEqual(r["slice_count"]["feedback"].format(word="five"),
                         "'slice_1_rest' must say that five people run away from the wave.")
        self.assertTrue(all(x["field"] == "slice_1_rest" for x in r.values()))

    def test_people_chosen_by_code(self):
        rng = random.Random(4)
        seen = {es.choose_people(TIDAL, None, rng) for _ in range(300)}
        self.assertEqual(seen, {3, 4, 5, 6})
        self.assertIsNone(es.choose_people(FLOOD, None, rng))
        spec = es.build_spec(TIDAL, None, "Coastal avenue behind a seawall", "riviera", "T2", "W3", "small car", 4)
        self.assertEqual(spec["people"], 4)
        self.assertNotIn("people", build()[0])   # sel spec'i aynı
        with self.assertRaises(es.StructureError):
            es.build_spec(TIDAL, None, "Coastal avenue behind a seawall", "riviera", "T2", "W3", "small car")
        with self.assertRaises(es.StructureError):
            es.build_spec(FLOOD, None, "Downtown city center", "riviera", "V1", "D2", "small car", 4)

    def test_people_line_in_message(self):
        import core.creative_pipeline as cp
        for n, word in es.NUMBER_WORDS.items():
            spec, _, _ = build("T2", "W3", "riviera", "Coastal avenue behind a seawall", "small car", TIDAL, n)
            msg = cp._slices_message(spec, "P", "W", 3, 6, [], None)
            with self.subTest(n=n):
                self.assertIn(f"\nVEHICLE: small car\nPEOPLE RUNNING AWAY: {word} (slice_1_rest must say that {word} "
                              f"people run away from the wave)\n4-9s EVENT: ", msg)

    def test_people_out_of_range_caught_in_final_check(self):
        spec, slices, prompt = build("T2", "W3", "riviera", "Coastal avenue behind a seawall", "small car", TIDAL, 5)
        self.assertEqual(es.final_prompt_issues(spec, slices, prompt), [])
        for bad in (2, 7, None, "five"):
            with self.subTest(people=bad):
                self.assertIn("people", {i["rule"] for i in es.final_prompt_issues({**spec, "people": bad}, slices,
                                                                                    prompt)})
        fspec, fsl, fprompt = build()
        self.assertIn("people", {i["rule"] for i in es.final_prompt_issues({**fspec, "people": 4}, fsl, fprompt)})

    def test_flee_and_count_gates(self):
        spec, slices, _ = build("T4", "W2", "riviera", "Coastal road below a seafront promenade", "small car",
                                event=TIDAL, people=5)

        def codes(s1, sp=spec):
            sl = {**slices, "slice_1_rest": es.clean_slice(s1)}
            return {i["rule"] for i in es.final_prompt_issues(sp, sl, es.assemble_prompt(sp, sl))}
        ok = ["It smashes over the railings as five pedestrians run from the wave.",
              "Five residents sprint away from the promenade as it hits.",
              "Five people scatter up the steps away from the water.",
              "Five pedestrians are fleeing up the side street.",
              "Five people dash for the stairs as the water pours in.",
              "Five residents raced away from the seafront.",
              # 4 Eki: kuru provada reddedilen kaçış fiilleri
              "Five people scramble frantically, darting between shops.",
              "Five residents hurry toward higher ground."]
        for s1 in ok:
            with self.subTest(ok=s1):
                self.assertFalse(codes(s1) & {"slice_flee", "slice_count", "slice_words"})
        self.assertIn("slice_flee", codes("It smashes over the railings and five pedestrians watch the wave."))
        # "rush" kaçış sayılmaz: suyun kendisi de "rushes" (4 Eki, Bahadır)
        self.assertIn("slice_flee", codes("Five pedestrians stand still as the water rushes over the railings."))
        self.assertIn("slice_flee", codes("Five shoppers rush up the stairs away from the water."))
        self.assertIn("slice_count", codes("It smashes over the railings as pedestrians run from the wave."))
        # N'e özel: başka sayı ya da belirsiz miktar yetmez
        for s1 in ("It smashes over the railings as three pedestrians run from the wave.",
                   "It smashes over the railings as eight pedestrians run away.",
                   "A handful of people scatter up the steps away from the water.",
                   "Several pedestrians are fleeing up the side street.",
                   "A few residents run from the seafront."):
            with self.subTest(bad=s1):
                self.assertIn("slice_count", codes(s1))
        # aynı cümle N=3 olan spec'te geçer
        spec3 = es.build_spec(TIDAL, None, spec["spot"], spec["view"], "T4", "W2", "small car", 3)
        self.assertNotIn("slice_count", codes("It smashes over the railings as three pedestrians run from the wave.",
                                              spec3))
        both = codes("It smashes over the railings and pours between the parked cars.")
        self.assertTrue({"slice_flee", "slice_count"} <= both)
        # kapılar sadece slice_1_rest'e bakar: kaçış 4-9s'de yazılırsa sayılmaz
        sl = {**slices, "slice_1_rest": es.clean_slice("It smashes over the railings and pours into the street."),
              "slice_2": es.clean_slice(slices["slice_2"] + " as five people run")}
        self.assertTrue({"slice_flee", "slice_count"} <= {i["rule"] for i in es.slice_issues(spec, sl)})
        # feedback GPT'ye gider
        fb = {i["rule"]: i["feedback"] for i in es.slice_issues(spec, {**slices, "slice_1_rest": "It hits the road."})}
        self.assertEqual(fb["slice_flee"], "'slice_1_rest' must show people running away from the wave.")
        self.assertEqual(fb["slice_count"], "'slice_1_rest' must say that five people run away from the wave.")

    def test_cumulative_feedback(self):
        import asyncio
        import core.creative_pipeline as cp
        spec, good, _ = build("T4", "W2", "riviera", "Coastal road below a seafront promenade", "small car",
                              event=TIDAL, people=5)
        no_flee = {**good, "slice_1_rest": es.clean_slice("It smashes over the railings and pours into the street.")}
        no_w2 = {**good, "slice_3": es.clean_slice("A low wall collapses into the churning brown water nearby.")}
        answers, users = [no_flee, no_w2, good], []

        async def gpt(system, user, **kw):
            users.append(user)
            return answers[len(users) - 1]
        slices, attempts = asyncio.run(cp.write_slices(spec, "P", "W", [], gpt))
        self.assertEqual(len(attempts), 3)
        head = "YOUR PREVIOUS ANSWERS WERE REJECTED. Fix ALL of these and keep everything that was already correct: "
        flee = "'slice_1_rest' must show people running away from the wave."
        count = "'slice_1_rest' must say that five people run away from the wave."
        w2 = "'slice_3' must clearly show this event: a lamppost topples into the surge."
        self.assertNotIn("REJECTED", users[0])
        self.assertIn(head, users[1])
        self.assertIn(flee, users[1])
        self.assertIn(count, users[1])
        # 3. denemede 1. denemenin nedenleri de listede (düzeltilmiş olsa bile), tekrarsız
        tail = users[2].split(head, 1)[1]
        self.assertTrue(all(x in tail for x in (flee, count, w2)))
        self.assertEqual(tail.count(flee), 1)

    def test_flood_feedback_and_message_unchanged(self):
        import asyncio
        import core.creative_pipeline as cp
        spec = es.build_spec(FLOOD, None, "Downtown city center", "riviera", "V2", "D5", "delivery van")
        self.assertEqual(cp._slices_message(spec, "PLACE X", "heavy rain", 2, 10, ["old story one", "old story two"],
                                            None),
                         "OPENING SENTENCE (fixed, already written): A waist-high wall of brown muddy floodwater "
                         "surges into the street.\nPLACE: PLACE X\nWEATHER: heavy rain\nPEOPLE VISIBLE: 2 to 10\n"
                         "VEHICLE: delivery van\n4-9s EVENT: the delivery van is swept into another parked car and "
                         "both are shoved along\n9-15s EVENT: a city bus is shoved sideways by the current\n"
                         "RECENT STORIES:\n- old story one\n- old story two")
        self.assertTrue(cp._slices_message(spec, "PLACE X", "heavy rain", 2, 10, [], ["Fix A.", "Fix B."]).endswith(
            "RECENT STORIES:\n- (none)\n\nYOUR PREVIOUS ANSWER WAS REJECTED: Fix A. Fix B."))
        # sel yeniden denemesi birikmez: 3. mesajda sadece 2. denemenin nedeni var
        spec, good, _ = build("V1", "D2", "riviera", "Downtown city center", "small car")
        bad_v1 = {**good, "slice_2": es.clean_slice("The small car sits in the churning brown water on the street.")}
        bad_d2 = {**good, "slice_3": es.clean_slice("A low wall collapses into the churning brown water nearby.")}
        answers, users = [bad_v1, bad_d2, good], []

        async def gpt(system, user, **kw):
            users.append(user)
            return answers[len(users) - 1]
        asyncio.run(cp.write_slices(spec, "P", "W", [], gpt))
        self.assertIn("YOUR PREVIOUS ANSWER WAS REJECTED: ", users[2])
        self.assertNotIn("WERE REJECTED", users[2])
        self.assertNotIn("'slice_2' must clearly show", users[2])
        self.assertIn("'slice_3' must clearly show", users[2])
        self.assertNotIn("PEOPLE RUNNING AWAY", users[0])

    def test_flood_has_no_slice_gates(self):
        spec, slices, prompt = build()
        sl = {**slices, "slice_1_rest": es.clean_slice("It swallows the curbs and pours between the parked cars.")}
        rules = {i["rule"] for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl))}
        self.assertFalse(rules & {"slice_flee", "slice_count"})

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
                        # N her prompt'ta değişir (3-6 döngü): her sayı kelimesi kapıdan geçer
                        spec, slices, prompt = build(b2, b3, view, spot, vehicle, event=TIDAL, people=3 + n % 4)
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
            # 4 Eki: görünümsüz olaylarda (heyelan) tek görünüm None
            for view in es.structure_views(event):
                for spot in sk.view_spots(event, view):
                    pairs = es.allowed_pairs(event, view, spot)
                    worst = min(sum(1 for v, d in pairs if v not in x2 and d not in x3)
                                for x2 in blocks2 for x3 in blocks3)
                    with self.subTest(event=event, view=view, spot=spot):
                        self.assertGreater(worst, 0)

    def test_choose_beats_long_run(self):
        # Gerçek akış: her seçim geçmişe eklenir; 200 üretim boyunca hiç aday tükenmez
        cases = [(FLOOD, "Downtown city center"), (TIDAL, "Coastal avenue behind a seawall")]
        cases += [(e, spot) for e in LANDSLIDE for spot in sk.EVENT_SKELETONS[e]["spots"]]
        for event, spot in cases:
            for view in es.structure_views(event):
                if spot not in sk.view_spots(event, view):
                    continue
                es._BEAT_MEMORY.clear()
                rng, hist = random.Random(7), []
                for _ in range(200):
                    p = es.choose_beats(event, view, spot, hist, rng)
                    hist.append(combo(view=view or "", tag=es.beat_tag(*p), spot=spot.lower(), event=event))
        es._BEAT_MEMORY.clear()


LANDSLIDE = (es.MUDSLIDE, es.SLOPE, es.VILLAGE)


class TestLandslideStructure(unittest.TestCase):
    """4 Eki, TASLAK (Bahadır hazırlığı, onay bekliyor): heyelan 3 olayı yapılandırılmış hatta, bölge görünümü yok.
    KİLİT: havuz metinleri, yasak eşleşmeler ve araç listeleri onaysız değişmez."""

    POOLS = {
        es.MUDSLIDE: ({
            "H1": "the {vehicle} is shoved sideways by the mud and slams into the car parked beside it",
            "H2": "the {vehicle} is pushed down the street by the mud, bumping parked cars",
            "H3": "the {vehicle} is spun around by the mud and dragged downhill",
            "H4": "the {vehicle} is buried to its windows and pushed against a house wall",
            "H5": "the {vehicle} tips over onto its side in the mud",
            "H6": "the {vehicle} and the car behind it are pushed down the street together, bumper to bumper",
        }, {
            "M1": "a row of parked cars is pushed down the street one by one",
            "M2": "a utility pole snaps and falls into the mud",
            "M3": "a low garden wall collapses and its stones tumble down the street",
            "M4": "a tree is torn out of the slope and carried down with the mud",
            "M5": "a wooden fence is torn away and carried off",
            "M6": "the mud rams a house corner and tears off its wooden porch",
        }, {("H2", "M1"), ("H6", "M1"), ("H4", "M3"), ("H4", "M6")}, {}),
        es.SLOPE: ({
            "R1": "the {vehicle} is shoved sideways across the road by the mud and rocks",
            "R2": "the {vehicle} is pushed against the guardrail and pinned there",
            "R3": "a rolling boulder strikes the {vehicle}, which spins and slides down the road",
            "R4": "the {vehicle} is buried to its windows in the mud and pushed toward the road edge",
            "R5": "the {vehicle} tips over onto its side in the mud",
            "R6": "the {vehicle} and the car behind it are shoved along the road together",
        }, {
            "S1": "a section of the guardrail is bent and torn away by the mud",
            "S2": "a large boulder rolls across the road and smashes into a parked car",
            "S3": "a tree is torn out of the slope and slides across the road",
            "S4": "a utility pole snaps and falls across the road",
            "S5": "more of the slope gives way and a second surge of mud and rocks pours onto the road",
            "S6": "a row of parked cars is shoved toward the road edge",
        }, {("R3", "S2"), ("R2", "S1"), ("R6", "S6")},
            # kamera korkuluğun hemen arkasında
            {"S1": {"Behind the guardrail of a hillside road"}}),
        es.VILLAGE: ({
            "K1": "the {vehicle} is swept down the lane and rammed against a house wall",
            "K2": "the {vehicle} is spun around by the torrent and dragged along the lane",
            "K3": "the {vehicle} is buried to its windows and pushed against a fence",
            "K4": "the {vehicle} tips over onto its side in the torrent",
            "K5": "the {vehicle} slams into a pile of logs and both are carried away",
            "K6": "the {vehicle} is shoved into a parked motorbike and both are carried along",
        }, {
            "L1": "a wooden house corner is struck and its wall collapses",
            "L2": "a stretch of wooden fence is torn away and carried off",
            "L3": "a large tree is uprooted and rolls down with the torrent",
            "L4": "a roof section is torn off a shed and swept away",
            "L5": "a pile of logs breaks loose and rolls down the lane",
            "L6": "a stone wall collapses and its stones tumble into the torrent",
        }, {("K1", "L1"), ("K3", "L2"), ("K5", "L5"), ("K1", "L6")},
            # kamera köy evinin üst kat balkonunda
            {"L1": {"Upper-floor balcony of a village house"}}),
    }
    VEHICLES = {es.MUDSLIDE: ["pickup truck", "small car", "white van", "SUV"],
                es.SLOPE: ["pickup truck", "small car", "white van", "SUV"],
                es.VILLAGE: ["pickup truck", "small van", "old hatchback"]}

    def setUp(self):
        es._BEAT_MEMORY.clear()

    def build(self, event, b2, b3, spot, vehicle, people=5, s1=None):
        spec = es.build_spec(event, None, spot, None, b2, b3, vehicle, people)
        word = es.NUMBER_WORDS[people]
        slices = fake_slices(b2, b3, vehicle, event, s1 or f"Within seconds {word} residents run uphill from the flow.")
        return spec, slices, es.assemble_prompt(spec, slices)

    def test_names_from_code(self):
        self.assertEqual(sk.skeleton_events("landslide_disasters"), list(LANDSLIDE))
        for e in LANDSLIDE:
            self.assertNotIn(e, sk.REGION_VIEW_EVENTS)
            self.assertEqual(es.structure_views(e), [None])
        self.assertEqual(es.structure_views(FLOOD), list(sk.REGION_VIEWS))

    def test_pools_locked(self):
        for e, (s2, s3, pairs, spots) in self.POOLS.items():
            b = es.EVENT_BEATS[e]
            with self.subTest(event=e):
                self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, s2)
                self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, s3)
                self.assertEqual(b["excluded_pairs"], pairs)
                self.assertEqual(b["excluded_views"], {})
                self.assertEqual(b["excluded_spots"], spots)

    def test_vehicles_locked(self):
        self.assertEqual({e: [n for n, _ in es.EVENT_VEHICLES[e]] for e in LANDSLIDE}, self.VEHICLES)
        rng = random.Random(5)
        for e, names in self.VEHICLES.items():
            self.assertEqual({es.choose_event_vehicle(e, rng) for _ in range(200)}, set(names))
        spec = es.build_spec(es.VILLAGE, None, "High steps on the village square", None, "K2", "L3", "old hatchback", 4)
        self.assertEqual(es.spec_vehicle_terms(spec), ("hatchback",))
        with self.assertRaises(es.StructureError):
            es.choose_event_vehicle(FLOOD)        # sel araç listesini görünümden alır, değişmedi
        with self.assertRaises(es.StructureError):
            es.spec_vehicle_terms({**spec, "vehicle": "SUV"})

    def test_key_visuals_pass_trigger_and_event_name(self):
        import core.creative_pipeline as cp
        for e in LANDSLIDE:
            with self.subTest(event=e):
                self.assertEqual(cp.EVENT_REQUIRED[e], [])
                found = {i["rule"] for i in cp.story_rule_issues(e, None, es.EVENT_KEY_VISUAL[e])}
                self.assertFalse(found & {"a_trigger_first", "e_event_and_ship_named", "required"})

    def test_canonical_terms_pass(self):
        for e in LANDSLIDE:
            for slot in ("slice_2", "slice_3"):
                for bid, beat in es.EVENT_BEATS[e][slot].items():
                    for vehicle in self.VEHICLES[e]:
                        text = cap(es.beat_text(e, slot, bid, vehicle))
                        with self.subTest(beat=bid, vehicle=vehicle):
                            self.assertEqual(es.missing_term_groups(beat["terms"], text), [])

    def test_variants_and_wrong_event(self):
        ok = {(es.MUDSLIDE, "H1"): "The mud shoves the SUV broadside into the neighboring parked car.",
              (es.MUDSLIDE, "H3"): "The pickup truck whirls around and is dragged down the slope.",
              (es.MUDSLIDE, "H4"): "The small car is engulfed up to its windows and pressed against a cottage.",
              (es.MUDSLIDE, "M6"): "The flow smashes into the corner of a house, ripping away its veranda.",
              (es.SLOPE, "R2"): "The mud rams the white van into the crash barrier and pins it there.",
              (es.SLOPE, "R3"): "A boulder slams into the SUV, which skids and spins along the road.",
              (es.SLOPE, "S5"): "Another section of hillside gives way and fresh mud pours over the road.",
              (es.VILLAGE, "K5"): "The small van crashes into a stack of timber and both are swept away.",
              (es.VILLAGE, "K6"): "The torrent shoves the pickup truck into a moped and carries both along.",
              (es.VILLAGE, "L5"): "A woodpile breaks loose and its logs tumble down the lane."}
        bad = {(es.MUDSLIDE, "H1"): "The SUV is pushed down the street by the mud.",
               (es.MUDSLIDE, "H4"): "The small car is pushed against a house wall.",
               (es.MUDSLIDE, "M6"): "A low garden wall collapses into the mud.",
               (es.SLOPE, "R2"): "The white van is shoved sideways across the road.",
               (es.SLOPE, "S1"): "A utility pole snaps and falls across the road.",
               (es.VILLAGE, "K6"): "The pickup truck is shoved into a parked car and both are carried along.",
               (es.VILLAGE, "L1"): "A stone wall is struck by the torrent."}
        for (e, bid), s in ok.items():
            slot = "slice_3" if bid[0] in "MSL" else "slice_2"
            with self.subTest(ok=bid):
                self.assertEqual(es.missing_term_groups(es.EVENT_BEATS[e][slot][bid]["terms"], s), [])
        for (e, bid), s in bad.items():
            slot = "slice_3" if bid[0] in "MSL" else "slice_2"
            with self.subTest(bad=bid):
                self.assertTrue(es.missing_term_groups(es.EVENT_BEATS[e][slot][bid]["terms"], s))

    def test_together_terms_h6_r6(self):
        # 4 Eki, Bahadır onayı: heyelana özel "birlikte" grubu; sel/tidal ortak _TOGETHER aynı
        self.assertEqual(es._TOGETHER, ("together", "bumper", "side by side", "in tandem", "locked", "both", "pair"))
        self.assertEqual(es._TOGETHER_LANDSLIDE, es._TOGETHER + ("the car behind it", "trailing", "following"))
        self.assertIs(es.EVENT_BEATS[FLOOD]["slice_2"]["V8"]["terms"][0], es._TOGETHER)
        self.assertIs(es.EVENT_BEATS[TIDAL]["slice_2"]["T8"]["terms"][0], es._TOGETHER)
        h6 = es.EVENT_BEATS[es.MUDSLIDE]["slice_2"]["H6"]["terms"]
        r6 = es.EVENT_BEATS[es.SLOPE]["slice_2"]["R6"]["terms"]
        ok = [(h6, "The pickup truck and the car behind it are forcibly pushed down the street by the mud."),
              (r6, "The relentless mudflow catches the pickup truck, dragging it and the trailing car along the road."),
              (h6, "The SUV is shoved down the street, the following car swept along with it."),
              (r6, "The white van and the car behind it slide along the road in the torrent.")]
        for terms, text in ok:
            with self.subTest(ok=text):
                self.assertEqual(es.missing_term_groups(terms, text), [])
        bad = [(h6, "The SUV is pushed down the street behind a parked car."),
               (r6, "The small car is shoved along the road behind the parked cars."),
               (r6, "The small car is shoved along the road, a parked car behind it.")]
        for terms, text in bad:
            with self.subTest(bad=text):
                self.assertTrue(es.missing_term_groups(terms, text))
        # sel ve tidal: aynı ifade hâlâ reddedilir (ortak liste değişmedi)
        v8 = es.EVENT_BEATS[FLOOD]["slice_2"]["V8"]["terms"]
        self.assertTrue(es.missing_term_groups(v8, "The sedan and the car behind it are swept down the street."))

    def test_all_combinations_pass_final_check(self):
        n, longest = 0, 0
        for e in LANDSLIDE:
            head = f"0-4s: {es.EVENT_KEY_VISUAL[e]} "
            for spot in sk.view_spots(e, None):
                pairs = es.allowed_pairs(e, None, spot)
                self.assertTrue(pairs, (e, spot))
                for b2, b3 in pairs:
                    self.assertNotIn((b2, b3), es.EVENT_BEATS[e]["excluded_pairs"])
                    for vehicle in self.VEHICLES[e]:
                        spec, slices, prompt = self.build(e, b2, b3, spot, vehicle, people=3 + n % 4)
                        issues = es.final_prompt_issues(spec, slices, prompt, es.assemble_story(spec, slices))
                        if issues:
                            self.fail(f"{e}/{spot}/{b2}+{b3}/{vehicle}: {issues}\n{prompt}")
                        self.assertTrue(prompt.startswith(head))
                        self.assertNotIn("Setting:", prompt)   # görünüm cümlesi yok
                        longest = max(longest, len(prompt))
                        n += 1
        # çamur: 3 spot × 32 çift × 4 araç; yol: (28 + 33) × 4; köy: (32 + 32 + 27) × 3
        self.assertEqual(n, 384 + 244 + 273)
        self.assertLess(longest, es.MAX_PROMPT_CHARS)

    def test_excluded_spots(self):
        self.assertNotIn("S1", {d for _, d in es.allowed_pairs(es.SLOPE, None, "Behind the guardrail of a hillside road")})
        self.assertIn("S1", {d for _, d in es.allowed_pairs(es.SLOPE, None, "Far edge of the road across from the slope")})
        self.assertNotIn("L1", {d for _, d in es.allowed_pairs(es.VILLAGE, None, "Upper-floor balcony of a village house")})
        self.assertIn("L1", {d for _, d in es.allowed_pairs(es.VILLAGE, None, "Terrace on the opposite hillside")})

    def test_people_gate_and_line(self):
        import core.creative_pipeline as cp
        for e in LANDSLIDE:
            self.assertEqual(sk.count_range(e, None), (3, 6))
            r = {x["rule"]: x for x in es.SLICE_RULES[e]}
            self.assertEqual(r["slice_flee"]["terms"], es.SLICE_RULES[TIDAL][0]["terms"])
            self.assertNotIn("rush", r["slice_flee"]["terms"])
            self.assertEqual(r["slice_flee"]["feedback"], "'slice_1_rest' must show people running away from the mud.")
        spec, slices, _ = self.build(es.MUDSLIDE, "H3", "M2", "Balcony across a steep hillside street", "SUV", 4)
        msg = cp._slices_message(spec, "P", "W", 3, 6, [], None)
        self.assertIn("\nVEHICLE: SUV\nPEOPLE RUNNING AWAY: four (slice_1_rest must say that four people run away "
                      "from the mud)\n4-9s EVENT: ", msg)

        def codes(s1):
            sl = {**slices, "slice_1_rest": es.clean_slice(s1)}
            return {i["rule"] for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl))}
        self.assertFalse(codes("Four residents scramble uphill away from the mud.") & {"slice_flee", "slice_count"})
        self.assertIn("slice_count", codes("Five residents scramble uphill away from the mud."))
        self.assertIn("slice_count", codes("Several residents scramble uphill away from the mud."))
        self.assertIn("slice_flee", codes("Four residents watch from a doorway as it comes."))
        self.assertIn("slice_flee", codes("Four residents stand still as the mud rushes past."))
        fb = {i["rule"]: i["feedback"] for i in es.slice_issues(spec, {**slices, "slice_1_rest": "It hits the road."})}
        self.assertEqual(fb["slice_count"], "'slice_1_rest' must say that four people run away from the mud.")

    def test_scene_without_view(self):
        import asyncio
        import core.creative_pipeline as cp
        from core.trace_format import format_generation
        calls = []

        async def gpt(system, user, **kw):
            calls.append(user)
            sl = slices_from_message(user)
            return {**sl, "slice_1_rest": sl["slice_1_rest"].replace("pedestrians run from the wave",
                                                                     "residents run uphill from the mud")}
        for e in LANDSLIDE:
            with self.subTest(event=e):
                scene = asyncio.run(cp.build_creative_scene("landslide_disasters", e, [], [], gpt))
                t = scene["trace"]
                self.assertIsNone(t["view"])
                self.assertIn(t["vehicle"], self.VEHICLES[e])
                self.assertIn(t["people_running"], (3, 4, 5, 6))
                self.assertIn(f"|{t['spot'].lower()}##{t['beats']}|", scene["combo_key"])
                self.assertIsNone(sk.view_of_combo(scene["combo_key"]))
                self.assertEqual(es.beats_of_combo(scene["combo_key"]), t["beats"])
                self.assertEqual(es.beat_history(e, [scene["combo_key"]])[-1], t["beats"])
                self.assertTrue(sk.is_current_universe_combo(scene["combo_key"]))
                self.assertNotIn("None", scene["combo_key"])
                detail = "\n".join(body for _, body in format_generation(t))
                self.assertNotIn("Görünüm", detail)
                self.assertNotIn("None", scene["prompt"])
                spec, sl = scene["structure"]["spec"], scene["structure"]["slices"]
                self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
                self.assertIn("run away from the mud", calls[-1])

    def test_flood_and_tidal_messages_unchanged(self):
        import core.creative_pipeline as cp
        spec = es.build_spec(TIDAL, None, "Coastal avenue behind a seawall", "riviera", "T2", "W3", "small car", 5)
        self.assertEqual(
            cp._slices_message(spec, "P", "W", 3, 6, ["old"], ["Fix A."]),
            "OPENING SENTENCE (fixed, already written): A towering brown tidal wave thick with debris crashes over the "
            "waterfront onto the coastal street.\nPLACE: P\nWEATHER: W\nPEOPLE VISIBLE: 3 to 6\nVEHICLE: small car\n"
            "PEOPLE RUNNING AWAY: five (slice_1_rest must say that five people run away from the wave)\n"
            "4-9s EVENT: the small car is carried down the street by the surge\n"
            "9-15s EVENT: a street tree is uprooted and carried along\nRECENT STORIES:\n- old\n\n"
            "YOUR PREVIOUS ANSWERS WERE REJECTED. Fix ALL of these and keep everything that was already correct: Fix A.")
        fspec = es.build_spec(FLOOD, None, "Downtown city center", "riviera", "V2", "D5", "delivery van")
        self.assertNotIn("PEOPLE RUNNING AWAY", cp._slices_message(fspec, "P", "W", 2, 10, [], None))


TORNADO = (es.LANDFALL, es.MARINA_TORNADO, es.AVENUE)


class TestTornadoStructure(unittest.TestCase):
    """4 Eki, TASLAK (Bahadır hazırlığı, onay bekliyor): hortum 3 olayı yapılandırılmış hatta, bölge görünümü yok
    (heyelandaki yol). KİLİT: havuz metinleri, yasak eşleşmeler, kamera dışlamaları ve araç listeleri onaysız değişmez."""

    POOLS = {
        es.LANDFALL: ({
            "C1": "the {vehicle} is shoved sideways across the street by the wind",
            "C2": "the {vehicle} tips over onto its side as roof tiles rain down around it",
            "C3": "a flying street sign slams into the windshield of the {vehicle}",
            "C4": "the {vehicle} slides along the street and slams into a parked car",
            "C5": "the {vehicle} is lifted off the road and flung down the street",
            "C6": "the {vehicle} is swept up into the air, spins, and crashes down onto the sidewalk",
        }, {
            "E1": "the tornado tears the roof off a house and scatters the pieces across the street",
            "E2": "the tornado rips a billboard frame from its supports and throws it aside",
            "E3": "a wall of dust and debris sweeps across the street and engulfs the end of the block",
            "E4": "the tornado uproots a large tree and flings it through the air",
            "E5": "the tornado rips the front off a small shop, sending shutters and signs flying",
            "E6": "the tornado tears away a section of fence and carries it down the street",
        }, {("C2", "E1")},
            {"E1": {"Residential coastal district"}}),
        es.MARINA_TORNADO: ({
            "Y1": "the {vehicle} is hit by flying debris and slides sideways across the quay",
            "Y2": "the {vehicle} tips over onto its side on the quay road",
            "Y3": "the {vehicle} slides along the quay and slams into a lamppost",
            "Y4": "a flying wooden crate smashes the windshield of the {vehicle}",
            "Y5": "the {vehicle} is lifted off the quay road and flung into a stack of dock boxes",
            "Y6": "the {vehicle} is swept up into the air, spins, and crashes down onto the quay",
        }, {
            "Z1": "the tornado tears the awning off the harbor café and flings it across the quay",
            "Z2": "the tornado rips the front off a small kiosk, sending its shutters and signs flying",
            "Z3": "a wall of dust and debris rolls across the quay and engulfs the café terrace",
            "Z4": "the tornado rips the roof off the marina office and scatters the pieces across the quay",
            "Z5": "the tornado sweeps dock boxes and rubbish bins off the quay and hurls them across the road",
            "Z6": "the tornado shatters the glass front of a quayside shop and hurls tables and chairs into the street",
        }, {("Y5", "Z5"), ("Y4", "Z5")}, {}),
        es.AVENUE: ({
            "P1": "the {vehicle} is shoved sideways across the avenue by the wind",
            "P2": "the {vehicle} tips over onto its side",
            "P3": "the {vehicle} is pushed against a lamppost and pinned there",
            "P4": "a falling palm tree crashes onto the {vehicle}, crushing its roof",
            "P5": "the {vehicle} is lifted off the avenue and flung into a bus shelter, shattering its glass",
            "P6": "the {vehicle} is swept up into the air, spins, and crashes down across the avenue",
        }, {
            "Q1": "the tornado rips a row of palm trees out of the ground and flings them across the avenue",
            "Q2": "the tornado tears a billboard from its frame and sends it spinning away",
            "Q3": "the tornado hurls a cloud of signs, branches and bins along the avenue",
            "Q4": "the tornado tears the roof off a bus shelter and throws it aside",
            "Q5": "the tornado topples a line of street lamps one by one",
            "Q6": "the tornado rips the awnings off a row of shops and flings them high",
        }, {("P3", "Q5"), ("P5", "Q4"), ("P4", "Q1")},
            {}),   # 10 Eki, Bahadır: kamera yüksek balkonda, Q5 dışlaması kalktı
    }
    SPOTS = {es.LANDFALL: ["Beachfront promenade", "Residential coastal district", "Downtown city center"],
             es.MARINA_TORNADO: ["High marina balcony"],
             # 10 Eki, Bahadır: cadde yüksek balkon noktaları
             es.AVENUE: ["High balcony over a downtown avenue", "Upper-floor balcony over a residential avenue",
                         "High balcony over a high-rise avenue"]}
    VEHICLES = ["pickup truck", "small car", "white van", "SUV"]

    def setUp(self):
        es._BEAT_MEMORY.clear()

    def build(self, event, b2, b3, spot, vehicle, people=5):
        spec = es.build_spec(event, None, spot, None, b2, b3, vehicle, people)
        s1 = f"Within seconds {es.NUMBER_WORDS[people]} people run for cover from the tornado."
        slices = fake_slices(b2, b3, vehicle, event, s1)
        return spec, slices, es.assemble_prompt(spec, slices)

    def test_menu_and_category(self):
        import bot
        import core.creative_pipeline as cp
        from core.creative_engine import DOMAIN_ATTRIBUTES
        self.assertEqual(sk.skeleton_events("coastal_tornado_landfall"), list(TORNADO))
        for e in ("Tornado approaching coastline", "Tornado rain bands and flying debris lash the waterfront"):
            self.assertIn(e, sk.REMOVED_EVENTS)          # kod silinmedi: havuzda, iskelet dışında
            self.assertNotIn(e, cp.EVENT_OUTCOMES)
            self.assertNotIn(e, cp.EVENT_REQUIRED)
        self.assertEqual(bot.EVENT_LABELS[es.MARINA_TORNADO], "🌪️ Hortum marina rıhtımını geçer")
        self.assertEqual(bot.EVENT_LABELS[es.AVENUE], "🌪️ Hortum sahil caddesini süpürür")
        env = DOMAIN_ATTRIBUTES["coastal_tornado_landfall"]["environments"]
        self.assertIn("Marina berthing pier", env)        # eski nokta silinmedi
        self.assertIn("High marina balcony", env)         # 4 Eki: marinanın yeni tek noktası
        self.assertEqual(len(env), 17)                    # 12 + rıhtım + yüksek teras + 3 cadde balkonu (10 Eki)
        self.assertEqual(sk.PHENOMENA["Hortum"], list(TORNADO) + ["Tornado approaching an open beach"])
        # plaj olayı aynı kaldı
        self.assertEqual(sk.EVENT_SKELETONS["Tornado approaching an open beach"]["domain"], "open_beach_coastal_events")
        self.assertFalse(es.is_structured("Tornado approaching an open beach"))

    def test_skeletons_and_outcomes(self):
        import core.creative_pipeline as cp
        for e in TORNADO:
            s = sk.EVENT_SKELETONS[e]
            with self.subTest(event=e):
                self.assertEqual(list(s["spots"]), self.SPOTS[e])
                self.assertIsNone(s["ships"])            # marina dahil gemisiz
                self.assertEqual(s["weather"], sk.WEATHER_STORM)
                self.assertEqual(sk.count_range(e, None), (3, 6))
                self.assertEqual(cp.EVENT_REQUIRED[e], [])
                self.assertNotIn(e, sk.REGION_VIEW_EVENTS)
                self.assertEqual(es.structure_views(e), [None])
        self.assertEqual(sk.CAMERA_SPOTS["Marina berthing pier"], "on the berthing pier")   # tabloda kaldı
        self.assertEqual(sk.CAMERA_SPOTS["High marina balcony"], "on a high balcony overlooking the marina and quay")
        self.assertEqual(cp.EVENT_OUTCOMES[es.MARINA_TORNADO],
                         "the tornado tears across the marina quay, ripping awnings, signs and quay furniture loose and "
                         "hurling debris "
                         "toward the road")
        self.assertEqual(cp.EVENT_OUTCOMES[es.AVENUE],
                         "the tornado sweeps down the coastal avenue, uprooting palm trees and hurling signs and debris "
                         "along the road")

    def test_pools_locked(self):
        for e, (s2, s3, pairs, spots) in self.POOLS.items():
            b = es.EVENT_BEATS[e]
            with self.subTest(event=e):
                self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, s2)
                self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, s3)
                self.assertEqual(b["excluded_pairs"], pairs)
                self.assertEqual(b["excluded_views"], {})
                self.assertEqual(b["excluded_spots"], spots)
                self.assertEqual([n for n, _ in es.EVENT_VEHICLES[e]], self.VEHICLES)

    def test_key_visuals_pass_trigger_and_event_name(self):
        import core.creative_pipeline as cp
        for e in TORNADO:
            with self.subTest(event=e):
                found = {i["rule"] for i in cp.story_rule_issues(e, None, es.EVENT_KEY_VISUAL[e])}
                self.assertFalse(found & {"a_trigger_first", "e_event_and_ship_named", "required"})
                # kilit cümle olmadan tetik kuralı kalır
                self.assertIn("a_trigger_first", {i["rule"] for i in cp.story_rule_issues(e, None, "Cars sit still.")})

    def test_canonical_terms_pass(self):
        for e in TORNADO:
            for slot in ("slice_2", "slice_3"):
                for bid, beat in es.EVENT_BEATS[e][slot].items():
                    for vehicle in self.VEHICLES:
                        text = cap(es.beat_text(e, slot, bid, vehicle))
                        with self.subTest(beat=bid, vehicle=vehicle):
                            self.assertEqual(es.missing_term_groups(beat["terms"], text), [])

    def test_variants_and_wrong_event(self):
        ok = {(es.LANDFALL, "C1"): "A gust shoves the SUV broadside across the street.",
              (es.LANDFALL, "C3"): "A spinning signpost smashes through the windscreen of the white van.",
              (es.LANDFALL, "E2"): "The tornado wrenches a huge billboard off its frame and hurls it away.",
              (es.MARINA_TORNADO, "Y4"): "A wooden pallet slams into the pickup truck, shattering its front glass.",
              (es.MARINA_TORNADO, "Z1"): "The wind wrenches the café awning loose and hurls it over the quay.",
              (es.MARINA_TORNADO, "Z3"): "A cloud of dust and debris sweeps over the quay, swallowing the terrace.",
              (es.AVENUE, "P5"): "The wind heaves the small car off the road and hurls it into a bus stop.",
              (es.AVENUE, "P4"): "A falling palm tree crashes onto the white van, crushing its roof.",
              (es.LANDFALL, "C4"): "The SUV skids across the road and crashes into a stationary car.",
              (es.LANDFALL, "E5"): "The tornado shears the front off a small store, launching its shutters.",
              (es.LANDFALL, "C5"): "The wind lifts the white van off the road and hurls it down the street.",
              (es.LANDFALL, "C6"): "The SUV is swept up into the air, spun around and slammed onto the sidewalk.",
              (es.MARINA_TORNADO, "Y1"): "Flying debris hammers the white van and it skids sideways across the quay.",
              (es.MARINA_TORNADO, "Y6"): "The pickup truck is hoisted skyward, whirls and plunges onto the quay.",
              (es.AVENUE, "Q5"): "One by one the street lights bend and crash onto the avenue.",
              (es.AVENUE, "Q6"): "The tornado tears the shop awnings away and they whirl high above the road."}
        bad = {(es.LANDFALL, "C3"): "A flying street sign slams into the side of a parked bus.",
               (es.LANDFALL, "E1"): "The tornado tears a billboard off its frame.",
               (es.MARINA_TORNADO, "Y3"): "The SUV is pushed along the quay into a stack of boxes.",
               (es.MARINA_TORNADO, "Z4"): "The marina office shakes in the wind.",
               (es.AVENUE, "P4"): "A palm tree crashes down, narrowly missing the car.",
               (es.LANDFALL, "C5"): "The SUV is pushed down the street by the wind.",
               (es.LANDFALL, "C6"): "The SUV is swept up into the air and spins.",
               (es.MARINA_TORNADO, "Y5"): "The white van is flung into a stack of dock boxes.",
               (es.MARINA_TORNADO, "Z3"): "The café terrace stands empty in the rain.",
               (es.AVENUE, "P6"): "The SUV and the car behind it are pushed along the avenue together.",
               (es.AVENUE, "Q4"): "The tornado tears the roof off a house and throws it aside."}
        for (e, bid), s in ok.items():
            slot = "slice_3" if bid[0] in "EZQ" else "slice_2"
            with self.subTest(ok=bid):
                self.assertEqual(es.missing_term_groups(es.EVENT_BEATS[e][slot][bid]["terms"], s), [])
        for (e, bid), s in bad.items():
            slot = "slice_3" if bid[0] in "EZQ" else "slice_2"
            with self.subTest(bad=bid):
                self.assertTrue(es.missing_term_groups(es.EVENT_BEATS[e][slot][bid]["terms"], s))

    def test_all_combinations_pass_final_check(self):
        n, longest = 0, 0
        for e in TORNADO:
            head = f"0-4s: {es.EVENT_KEY_VISUAL[e]} "
            for spot in sk.view_spots(e, None):
                pairs = es.allowed_pairs(e, None, spot)
                self.assertTrue(pairs, (e, spot))
                for b2, b3 in pairs:
                    self.assertNotIn((b2, b3), es.EVENT_BEATS[e]["excluded_pairs"])
                    for vehicle in self.VEHICLES:
                        spec, slices, prompt = self.build(e, b2, b3, spot, vehicle, people=3 + n % 4)
                        issues = es.final_prompt_issues(spec, slices, prompt, es.assemble_story(spec, slices))
                        if issues:
                            self.fail(f"{e}/{spot}/{b2}+{b3}/{vehicle}: {issues}\n{prompt}")
                        self.assertTrue(prompt.startswith(head))
                        self.assertNotIn("Setting:", prompt)
                        longest = max(longest, len(prompt))
                        n += 1
        # karaya vurma (35 + 30 + 35) × 4; marina (36 - 2) × 4; cadde 3 × 33 × 4 (10 Eki: Q5 dışlaması kalktı)
        self.assertEqual(n, 400 + 136 + 396)
        self.assertLess(longest, es.MAX_PROMPT_CHARS)

    def test_excluded_spots(self):
        def d3(e, spot):
            return {d for _, d in es.allowed_pairs(e, None, spot)}
        self.assertNotIn("E1", d3(es.LANDFALL, "Residential coastal district"))
        self.assertIn("E1", d3(es.LANDFALL, "Downtown city center"))
        self.assertEqual(sk.view_spots(es.MARINA_TORNADO, None), ["High marina balcony"])
        self.assertEqual(d3(es.MARINA_TORNADO, "High marina balcony"), {"Z1", "Z2", "Z3", "Z4", "Z5", "Z6"})
        # 10 Eki, Bahadır: cadde kamerası yüksek balkonda, Q5 üç noktada da seçilebilir
        for spot in self.SPOTS[es.AVENUE]:
            self.assertEqual(d3(es.AVENUE, spot), {"Q1", "Q2", "Q3", "Q4", "Q5", "Q6"})

    def test_people_gate_and_line(self):
        import core.creative_pipeline as cp
        for e in TORNADO:
            r = {x["rule"]: x for x in es.SLICE_RULES[e]}
            self.assertEqual(r["slice_flee"]["terms"], es.SLICE_RULES[TIDAL][0]["terms"])
            self.assertEqual(r["slice_flee"]["feedback"],
                             "'slice_1_rest' must show people running away from the tornado.")
        spec, slices, _ = self.build(es.AVENUE, "P1", "Q2", "Downtown city center", "SUV", 6)
        msg = cp._slices_message(spec, "P", "W", 3, 6, [], None)
        self.assertIn("\nVEHICLE: SUV\nPEOPLE RUNNING AWAY: six (slice_1_rest must say that six people run away "
                      "from the tornado)\n4-9s EVENT: ", msg)

        def codes(s1):
            sl = {**slices, "slice_1_rest": es.clean_slice(s1)}
            return {i["rule"] for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl))}
        self.assertFalse(codes("Six pedestrians sprint for cover from the tornado.") & {"slice_flee", "slice_count"})
        self.assertIn("slice_count", codes("Four pedestrians sprint for cover from the tornado."))
        self.assertIn("slice_count", codes("A few pedestrians sprint for cover from the tornado."))
        self.assertIn("slice_flee", codes("Six pedestrians stare up at the funnel."))
        fb = {i["rule"]: i["feedback"] for i in es.slice_issues(spec, {**slices, "slice_1_rest": "It hits the road."})}
        self.assertEqual(fb["slice_count"], "'slice_1_rest' must say that six people run away from the tornado.")

    def test_scene_without_view(self):
        import asyncio
        import core.creative_pipeline as cp
        from core.trace_format import format_generation
        calls = []

        async def gpt(system, user, **kw):
            calls.append(user)
            sl = slices_from_message(user)
            return {**sl, "slice_1_rest": sl["slice_1_rest"].replace("pedestrians run from the wave",
                                                                     "pedestrians run from the tornado")}
        for e in TORNADO:
            with self.subTest(event=e):
                scene = asyncio.run(cp.build_creative_scene("coastal_tornado_landfall", e, [], [], gpt))
                t = scene["trace"]
                self.assertIsNone(t["view"])
                self.assertIsNone(scene["ship"])
                self.assertIn(t["vehicle"], self.VEHICLES)
                self.assertIn(t["people_running"], (3, 4, 5, 6))
                self.assertIn(f"|{t['spot'].lower()}##{t['beats']}|", scene["combo_key"])
                self.assertIsNone(sk.view_of_combo(scene["combo_key"]))
                self.assertEqual(es.beats_of_combo(scene["combo_key"]), t["beats"])
                self.assertTrue(sk.is_current_universe_combo(scene["combo_key"]))
                self.assertNotIn("Görünüm", "\n".join(body for _, body in format_generation(t)))
                spec, sl = scene["structure"]["spec"], scene["structure"]["slices"]
                self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
                self.assertIn("run away from the tornado", calls[-1])

    def test_flying_beats(self):
        # 4 Eki, Bahadır onayı: C5/C6, Y5/Y6, P5/P6 araç havalanır; Y6/P6 artık "birlikte itilir" değil
        for e, ids in ((es.LANDFALL, ("C5", "C6")), (es.MARINA_TORNADO, ("Y5", "Y6")), (es.AVENUE, ("P5", "P6"))):
            for bid in ids:
                terms = es.EVENT_BEATS[e]["slice_2"][bid]["terms"]
                with self.subTest(beat=bid):
                    self.assertIs(terms[0], es._LIFT_AIR)
        self.assertEqual(es._LIFT_AIR, es._LIFT + ("swept up", "sweep up", "sweeps up", "ascend"))
        for w in ("into the air", "in the air", "through the air", "skyward", "aloft", "hover"):
            self.assertNotIn(w, es._LIFT_AIR)
        y5 = es.EVENT_BEATS[es.MARINA_TORNADO]["slice_2"]["Y5"]["terms"]
        y6 = es.EVENT_BEATS[es.MARINA_TORNADO]["slice_2"]["Y6"]["terms"]
        # 4 Eki kuru prova: araba havalanmadan "into the air" başka nesneyle geçiyordu, artık reddedilir
        self.assertTrue(es.missing_term_groups(y5, "The small car hovers momentarily before crashing into dock boxes, "
                                                   "scattering shattered fragments into the air."))
        self.assertEqual(es.missing_term_groups(y6, "The small car ascends in a chaotic spin, flinging shards of glass "
                                                    "and metal before it crashes onto the quay."), [])
        # 4 Eki kuru prova: doğru anlatılan Y3 reddediliyordu (Z3 yat maddesi marina yeniden tasarımında çıktı)
        y3 = es.EVENT_BEATS[es.MARINA_TORNADO]["slice_2"]["Y3"]["terms"]
        for text in ("The wind hurls the SUV across the quay, crashing it into a steel lamppost.",
                     "The wind forces the SUV along the quay, crashing it with a crunch into a lamppost."):
            self.assertEqual(es.missing_term_groups(y3, text), [], text)
        for e in TORNADO:
            for beat in es.EVENT_BEATS[e]["slice_2"].values():
                self.assertNotIn(es._TOGETHER_LANDSLIDE, beat["terms"])
        # heyelan H6/R6 hâlâ kendi listesini kullanır
        self.assertIs(es.EVENT_BEATS[es.MUDSLIDE]["slice_2"]["H6"]["terms"][0], es._TOGETHER_LANDSLIDE)
        self.assertIs(es.EVENT_BEATS[es.SLOPE]["slice_2"]["R6"]["terms"][0], es._TOGETHER_LANDSLIDE)

    def test_p4_hits_vehicle_and_marina_key(self):
        # 4 Eki, Bahadır: P4 palmiye araca çarpar; "narrowly/missing" artık geçmez
        import core.creative_pipeline as cp
        p4 = es.EVENT_BEATS[es.AVENUE]["slice_2"]["P4"]["terms"]
        self.assertNotIn("missing", p4[2])
        self.assertNotIn("narrowly", p4[2])
        for text in ("A palm tree crashes down, narrowly missing the car.",
                     "A palm tree sways beside the small car.",
                     "A palm tree crashes onto the road in front of the SUV."):
            self.assertTrue(es.missing_term_groups(p4, text), text)
        for text in ("A falling palm tree crashes onto the white van, crushing its roof.",
                     "A towering palm topples onto the SUV and crumples its roof.",
                     # 4 Eki ikinci tur: kuru provada "collapsing onto a small car" reddediliyordu
                     "A towering palm tree collapses onto the small car, crumpling its roof."):
            self.assertEqual(es.missing_term_groups(p4, text), [], text)
        self.assertIn(("P4", "Q1"), es.EVENT_BEATS[es.AVENUE]["excluded_pairs"])
        found = {i["rule"] for i in cp.story_rule_issues(es.MARINA_TORNADO, None, es.EVENT_KEY_VISUAL[es.MARINA_TORNADO])}
        self.assertFalse(found & {"a_trigger_first", "e_event_and_ship_named", "required"})

    def test_landslide_message_unchanged(self):
        # 4 Eki: hortum eklenirken heyelan mesajı bayt bayt aynı (sel ve tidal: test_flood_and_tidal_messages_unchanged)
        import core.creative_pipeline as cp
        spec = es.build_spec(es.MUDSLIDE, None, "Balcony across a steep hillside street", None, "H3", "M2", "SUV", 4)
        self.assertEqual(
            cp._slices_message(spec, "P", "W", 3, 6, [], ["Fix A.", "Fix B."]),
            "OPENING SENTENCE (fixed, already written): A massive wall of brown mud and rocks tears loose from the "
            "saturated hillside and pours down the steep street.\nPLACE: P\nWEATHER: W\nPEOPLE VISIBLE: 3 to 6\n"
            "VEHICLE: SUV\nPEOPLE RUNNING AWAY: four (slice_1_rest must say that four people run away from the mud)\n"
            "4-9s EVENT: the SUV is spun around by the mud and dragged downhill\n"
            "9-15s EVENT: a utility pole snaps and falls into the mud\nRECENT STORIES:\n- (none)\n\n"
            "YOUR PREVIOUS ANSWERS WERE REJECTED. Fix ALL of these and keep everything that was already correct: "
            "Fix A. Fix B.")

    def test_no_candidates_never(self):
        from itertools import combinations
        k = es.RECENT_BEAT_BLOCK
        for e in TORNADO:
            b = es.EVENT_BEATS[e]
            for spot in sk.view_spots(e, None):
                pairs = es.allowed_pairs(e, None, spot)
                worst = min(sum(1 for v, d in pairs if v not in x2 and d not in x3)
                            for x2 in map(set, combinations(b["slice_2"], k))
                            for x3 in map(set, combinations(b["slice_3"], k)))
                with self.subTest(event=e, spot=spot):
                    self.assertGreater(worst, 0)


class TestMarinaRedesign(unittest.TestCase):
    """4 Eki, Bahadır: hortum marina olayı yeniden tasarlandı (yüksek teras, rıhtım/kafe sahneleri, 40-75 kelime)."""

    def setUp(self):
        es._BEAT_MEMORY.clear()

    def test_key_visual_rules(self):
        import core.creative_pipeline as cp
        key = es.EVENT_KEY_VISUAL[es.MARINA_TORNADO]
        self.assertEqual(key, "A violent tornado tears in from the sea onto the marina quay, ripping palms and umbrellas "
                              "off the ground.")
        found = {i["rule"] for i in cp.story_rule_issues(es.MARINA_TORNADO, None, key)}
        self.assertFalse(found & {"a_trigger_first", "e_event_and_ship_named", "required"})

    def test_total_words_override_only_marina(self):
        self.assertEqual(es.TOTAL_WORDS, (40, 70))
        # 10 Eki, Bahadır: orman yangını da 40-75 (TestFireStructure ayrıca kilitler)
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT, {es.MARINA_TORNADO: (40, 75), es.WILDFIRE: (40, 75),
                                                   es.HELICOPTER: (40, 75)})   # 10 Eki: helikopter
        w = "abcd"

        def total_rules(event, spot, b2, b3, vehicle, extra):
            spec = es.build_spec(event, None, spot, None, b2, b3, vehicle, 5)
            s2 = cap(es.beat_text(event, "slice_2", b2, vehicle))
            s3 = cap(es.beat_text(event, "slice_3", b3))
            sl = {"slice_1_rest": es.clean_slice("Five people run away from the tornado " + " ".join([w] * extra)),
                  "slice_2": es.clean_slice(s2 + PAD + " " + " ".join([w] * 8)), "slice_3": es.clean_slice(s3 + PAD)}
            n = len(es.plain_story(spec, sl).split())
            return n, {i["rule"] for i in es.slice_issues(spec, sl)}
        # marina: 75'e kadar geçer, 76 ve üstü kalır (iki taraf da denenir)
        seen = set()
        for extra in range(0, 12):
            n, rules = total_rules(es.MARINA_TORNADO, "High marina balcony", "Y2", "Z3", "SUV", extra)
            seen.add(n)
            with self.subTest(event="marina", words=n):
                self.assertEqual("total_words" in rules, not 40 <= n <= 75)
        self.assertTrue({71, 75, 76} <= seen, seen)
        # karaya vurma ve cadde: 70 üstü kalır
        for event, spot, b2, b3 in ((es.LANDFALL, "Downtown city center", "C2", "E3"),
                                    (es.AVENUE, "High balcony over a downtown avenue", "P2", "Q3")):
            for extra in range(0, 12):
                n, rules = total_rules(event, spot, b2, b3, "SUV", extra)
                with self.subTest(event=event, words=n):
                    self.assertEqual("total_words" in rules, not 40 <= n <= 70)

    def test_y1_y3_accept(self):
        b = es.EVENT_BEATS[es.MARINA_TORNADO]["slice_2"]
        ok = {"Y1": ["The white van is hit by flying debris and slides sideways across the quay.",
                     "Wreckage slams into the SUV, shoving it broadside along the quay.",
                     "Flying debris pelts the pickup truck as it skids sideways over the wet stones."],
              "Y3": ["The small car slides along the quay and slams into a lamppost.",
                     "The SUV skids down the quay and crashes into a street light.",
                     "The wind forces the white van along the quay until it hits a light pole."]}
        bad = {"Y1": "Flying debris rains down on the white van.",
               "Y3": "The SUV slides along the quay into a stack of boxes."}
        for bid, texts in ok.items():
            for t in texts:
                with self.subTest(ok=t):
                    self.assertEqual(es.missing_term_groups(b[bid]["terms"], t), [])
        for bid, t in bad.items():
            with self.subTest(bad=t):
                self.assertTrue(es.missing_term_groups(b[bid]["terms"], t))

    def test_new_z_terms(self):
        b = es.EVENT_BEATS[es.MARINA_TORNADO]["slice_3"]
        ok = {"Z2": "The tornado dislodges the kiosk front, its shutters cartwheeling away.",
              "Z4": "The tornado peels the roof off the marina office, scattering pieces everywhere.",
              "Z5": "The wind sweeps the rubbish bins off the quay and hurls them across the road.",
              "Z6": "The quayside shop's glass front shatters and tables and chairs fly into the street."}
        for bid, t in ok.items():
            with self.subTest(ok=bid):
                self.assertEqual(es.missing_term_groups(b[bid]["terms"], t), [])
        self.assertTrue(es.missing_term_groups(b["Z6"]["terms"], "The shop's glass front shatters."))
        # yeni söküm listesi hortuma özel; heyelanın ortak _TEAR listesi değişmedi
        self.assertIn("dislodge", es._TORNADO_RIP)
        self.assertNotIn("dislodge", es._TEAR)
        self.assertIn("collapse", es._CRASH_DOWN)
        self.assertIn("plummet", es._CRASH_DOWN)

    def test_camera_line_balcony(self):
        # 4 Eki, Bahadır: "High marina terrace" → "High marina balcony"; Kie'ye giden kamera cümlesi düzgün okunur
        from core.creative_engine import DOMAIN_ATTRIBUTES
        self.assertNotIn("High marina terrace", sk.CAMERA_SPOTS)
        self.assertEqual(list(sk.EVENT_SKELETONS[es.MARINA_TORNADO]["spots"]), ["High marina balcony"])
        env = DOMAIN_ATTRIBUTES["coastal_tornado_landfall"]["environments"]
        self.assertIn("High marina balcony", env)
        self.assertNotIn("High marina terrace", env)
        suffix = sk.style_suffix(es.MARINA_TORNADO, None, "High marina balcony")
        self.assertTrue(suffix.startswith("Handheld footage shot by a person standing on a high balcony overlooking "
                                          "the marina and quay, eye level"), suffix)
        for spot, cam in sk.CAMERA_SPOTS.items():
            self.assertFalse(cam.startswith("from "), spot)   # "standing from ..." kırık cümle olmasın

    def test_z6_break_group_only_marina(self):
        z6 = es.EVENT_BEATS[es.MARINA_TORNADO]["slice_3"]["Z6"]["terms"]
        for t in ("The whirlwind annihilates the shop's glass front, scattering tables and chairs down the quay.",
                  "The tornado strikes a quayside shop, splintering the glass facade and launching tables and chairs.",
                  "The tornado smashes the shop window and chairs and tables fly into the street.",
                  # 4 Eki ikinci tur: kuru provada "obliterates" reddediliyordu
                  "The tornado obliterates the shop's glass facade, violently propelling tables and chairs across the "
                  "drenched street.",
                  "The wind demolishes the shop window and flings tables and chairs.",
                  "The gust tears apart the shop's glass front, hurling tables.",
                  "The glass front blew apart and chairs flew into the street.",
                  "The glass front ruptures and chairs fly.",
                  "The tornado pulverizes the window, scattering tables.",
                  "The storm wreaks havoc on the shop window, throwing chairs.",
                  "The tornado wrecks the shop's glass front and tables tumble out."):
            with self.subTest(text=t):
                self.assertEqual(es.missing_term_groups(z6, t), [])
        # yeni kelimeler başka hiçbir olayın terimlerinde yok (sadece marina Z6)
        new = {"annihilate", "splinter", "obliterate", "demolish", "wreck", "wreak", "rupture", "pulverize",
               "tear apart", "tears apart", "tore apart", "torn apart", "tearing apart",
               "blow apart", "blows apart", "blew apart", "blown apart", "blowing apart"}
        self.assertTrue(new <= set(z6[1]))
        for e, b in es.EVENT_BEATS.items():
            for slot in ("slice_2", "slice_3"):
                for bid, beat in b[slot].items():
                    if (e, bid) == (es.MARINA_TORNADO, "Z6"):
                        continue
                    words = {w for g in beat["terms"] for w in g}
                    self.assertFalse(words & new, (e, bid))

    def test_crash_down_addition_only_widens(self):
        # "collapse" eklenmesi C6/P6'da hiçbir hikâyeyi reddetmeye başlamaz; sadece yeni ifadeleri kabul eder
        for e, bid, area in ((es.LANDFALL, "C6", "the sidewalk"), (es.AVENUE, "P6", "the avenue")):
            terms = es.EVENT_BEATS[e]["slice_2"][bid]["terms"]
            for t in (f"The SUV is swept up into the air, spins, and crashes down onto {area}.",
                      f"The SUV is lifted, whirls and slams onto {area}.",
                      f"The SUV is lifted, spins and collapses onto {area}."):
                with self.subTest(beat=bid, text=t):
                    self.assertEqual(es.missing_term_groups(terms, t), [])



FIRE = (es.WILDFIRE, es.FACADE_FIRE, es.FIRE_TORNADO)


class TestFireStructure(unittest.TestCase):
    """8 Eki, TASLAK (Bahadır): 🔥 Yangın kategorisi, 3 olay yapılandırılmış hatta (heyelan/hortum deseni, bölge
    görünümü yok). KİLİT: kilit cümleler, kamera satırları, hava, havuz metinleri, yasak eşleşmeler, kamera
    dışlamaları, araç listeleri ve yağmur/uçma yasakları onaysız değişmez. Terim listeleri yangına özel ve yeni."""

    KEY = {
        es.WILDFIRE: "A towering wall of flames sweeps down the forested slope and slams into the edge of the "
                     "neighborhood, igniting roofs and trees.",
        es.FACADE_FIRE: "Flames race up the glass facade of a tower, blowing out windows and raining burning debris "
                        "onto the street.",
        es.FIRE_TORNADO: "A violent fire tornado tears across a burning roadside, hurling flames, burning branches "
                         "and embers across the road.",
    }
    POOLS = {
        es.WILDFIRE: ({
            "K1": "the {vehicle} reverses hard down the road as a burning tree crashes across the lane in front of it",
            "K2": "the {vehicle} skids to a stop as flames leap across the road and lick its hood",
            "K3": "a burning branch falls onto the {vehicle}, setting its roof alight",
            "K4": "the {vehicle} swerves around a falling burning pine and slams into the guardrail",
            "K5": "the {vehicle} U-turns in a cloud of smoke and speeds away as the flames close the road behind it",
            "K6": "embers rain onto the {vehicle} as it races down the road, its rear window cracking in the heat",
        }, {
            "L1": "the flames leap onto the roofs of the nearest houses and ignite them one after another",
            "L2": "a shower of glowing embers rains onto the street and sets a wooden fence alight",
            "L3": "the fire races across a garden, engulfing a parked trailer and a woodpile",
            "L4": "the wall of flames swallows a row of trees along the road, sending sparks high into the air",
            "L5": "a house roof catches fire and its tiles burst apart in the heat",
            "L6": "the flames climb a power pole and snap the wires, which whip across the street in a shower of sparks",
        }, {("K1", "L4"), ("K3", "L2"), ("K6", "L2")},
            {"L1": {"Balcony of a hillside house"}, "L5": {"Balcony of a hillside house"}}),
        es.FACADE_FIRE: ({
            "M1": "a burning panel crashes onto the {vehicle} parked below, crushing its roof",
            "M2": "shattered glass rains onto the {vehicle} as it speeds away from the tower",
            "M3": "burning debris lands on the hood of the {vehicle}, which lurches back in a hurry",
            "M4": "the {vehicle} swerves around a falling flaming panel and mounts the curb",
            "M5": "a burning awning drops onto the {vehicle}, which reverses sharply",
            "M6": "flaming debris smashes the windshield of the {vehicle} as it brakes hard",
        }, {
            "N1": "the flames climb floor after floor, blowing out window after window",
            "N2": "a balcony awning catches fire and the flames leap to the floor above",
            "N3": "burning panels peel off the facade and tumble down in a trail of sparks",
            "N4": "a wall of smoke and fire pours out of the upper floors and rolls up the tower",
            "N5": "a row of windows explodes outward, spraying glass and flames over the street",
            "N6": "the fire jumps to the neighboring balcony, igniting its plants and furniture",
        }, {("M1", "N3"), ("M2", "N5"), ("M5", "N2")}, {}),
        es.FIRE_TORNADO: ({
            "T1": "the {vehicle} is lifted off the road by the swirling flames and flung into a burning tree",
            "T2": "a burning branch hurled by the tornado smashes the windshield of the {vehicle}",
            "T3": "the {vehicle} is swept up into the air, spins, and crashes down onto the road in a shower of sparks",
            "T4": "the {vehicle} skids sideways as the fire tornado crosses the road behind it, throwing embers across "
                  "its roof",
            "T5": "the {vehicle} is shoved against the guardrail by the whirling flames and its hood catches fire",
            "T6": "flaming debris slams into the side of the {vehicle}, which spins and stops across the road",
        }, {
            "U1": "the fire tornado rips the burning roof off a house and scatters flaming pieces across the street",
            "U2": "the fire tornado uproots a burning tree and flings it down the road",
            "U3": "the whirling flames tear a billboard from its supports and hurl it aside",
            "U4": "the tornado sucks up a pile of burning brush and spits it across the road in a fountain of sparks",
            "U5": "the fire tornado tears a section of burning fence away and carries it across the field",
            "U6": "the fire tornado sweeps over a parked trailer, tossing it aside in a cloud of fire and smoke",
        }, {("T1", "U2"), ("T2", "U2"), ("T4", "U4")}, {"U1": {"Balcony of a roadside house"}}),
    }
    # spot (kamera noktası) -> (kamera satırı, PLACE metni = Bahadır'ın ortam tarifi)
    SPOTS = {
        es.WILDFIRE: {
            "Balcony of a hillside house": ("on a balcony of a hillside house overlooking the street and the burning "
                                            "slope", "a hillside village neighborhood"),
            "Embankment above the village road": ("on a roadside embankment above the village road",
                                                  "a hillside village neighborhood"),
        },
        es.FACADE_FIRE: {
            # 8 Eki (2), Bahadır: hepsi yüksek; kaldırım noktaları çıktı
            "Balcony across from a downtown tower": ("on a high balcony across the street from the tower",
                                                     "the downtown city center"),
            "Rooftop terrace across from a downtown tower": ("on a rooftop terrace across the street from the "
                                                             "tower", "the downtown city center"),
            "Balcony across from a coastal high-rise": ("on a high balcony across the street from the tower",
                                                        "a high-rise coastal city"),
            "Rooftop terrace across from a coastal high-rise": ("on a rooftop terrace across the street from the "
                                                                "tower", "a high-rise coastal city"),
        },
        es.FIRE_TORNADO: {
            "Overlook above the burning valley road": ("on a roadside overlook above the burning valley road",
                                                       "a burning valley road"),
            "Balcony of a roadside house": ("on a high balcony of a roadside house overlooking the road",
                                            "a burning valley road"),
        },
    }
    WEATHER = ["hot dry wind and thick smoke haze", "gusty dry wind under an orange smoky sky",
               "heavy smoke and scorching still air"]
    VEHICLES = ["pickup truck", "small car", "white van", "SUV"]
    AWAY = {es.WILDFIRE: "the flames", es.FACADE_FIRE: "the flames", es.FIRE_TORNADO: "the fire tornado"}

    def setUp(self):
        es._BEAT_MEMORY.clear()

    def slices(self, e, b2, b3, vehicle, people):
        s1 = f"{cap(es.NUMBER_WORDS[people])} people run from {self.AWAY[e]}."
        return {"slice_1_rest": es.clean_slice(s1),
                "slice_2": es.clean_slice(cap(es.beat_text(e, "slice_2", b2, vehicle))),
                "slice_3": es.clean_slice(cap(es.beat_text(e, "slice_3", b3)))}

    def build(self, e, b2, b3, spot, vehicle, people=5):
        spec = es.build_spec(e, None, spot, None, b2, b3, vehicle, people)
        slices = self.slices(e, b2, b3, vehicle, people)
        return spec, slices, es.assemble_prompt(spec, slices)

    def codes(self, spec, slices):
        return {i["rule"] for i in es.final_prompt_issues(spec, slices, es.assemble_prompt(spec, slices))}

    def test_menu_and_category(self):
        import bot
        import core.creative_pipeline as cp
        from core.creative_engine import DOMAIN_ATTRIBUTES, ENV_CENTRIC_DOMAINS, MARITIME_INSPIRATION_DOMAINS
        self.assertEqual(es.FIRE_EVENTS, FIRE + (es.HELICOPTER,))   # 10 Eki: 4. olay (TestHelicopter)
        self.assertEqual(bot.DOMAIN_LABELS["fire_disasters"], "🔥 Yangın")
        self.assertEqual([bot.EVENT_LABELS[e] for e in FIRE],
                         ["🔥 Orman yangını mahalleye ulaşır", "🔥 Apartman cephe yangını", "🔥 Ateş hortumu"])
        self.assertEqual(sk.skeleton_events("fire_disasters"), list(FIRE) + [es.HELICOPTER])
        self.assertEqual(DOMAIN_ATTRIBUTES["fire_disasters"]["ships"], [])
        self.assertEqual(DOMAIN_ATTRIBUTES["fire_disasters"]["environments"],
                         [s for e in FIRE for s in self.SPOTS[e]])
        self.assertIn("fire_disasters", MARITIME_INSPIRATION_DOMAINS)
        self.assertIn("fire_disasters", ENV_CENTRIC_DOMAINS)
        self.assertEqual(sk.PHENOMENA["Yangın"], list(FIRE) + [es.HELICOPTER])
        for e in FIRE:
            with self.subTest(event=e):
                self.assertTrue(es.is_structured(e))
                self.assertNotIn(e, sk.REGION_VIEW_EVENTS)
                self.assertEqual(es.structure_views(e), [None])
                self.assertEqual(cp.EVENT_REQUIRED[e], [])
                self.assertNotIn(e, cp.REQUIRED_APPROVED)      # TASLAK
                self.assertEqual(sk.count_range(e, None), (3, 6))
                self.assertIsNone(sk.EVENT_SKELETONS[e]["ships"])
                self.assertEqual(sk.EVENT_SKELETONS[e]["domain"], "fire_disasters")

    def test_key_visuals_locked_and_pass(self):
        import core.creative_pipeline as cp
        for e in FIRE:
            with self.subTest(event=e):
                self.assertEqual(es.EVENT_KEY_VISUAL[e], self.KEY[e])
                found = {i["rule"] for i in cp.story_rule_issues(e, None, self.KEY[e])}
                self.assertFalse(found & {"a_trigger_first", "e_event_and_ship_named", "required"})
                self.assertIn("a_trigger_first", {i["rule"] for i in cp.story_rule_issues(e, None, "Cars sit still.")})
                self.assertEqual(es.rain_words(self.KEY[e]), [])

    def test_camera_lines_place_and_weather(self):
        from core.creative_engine import DOMAIN_ATTRIBUTES
        for e in FIRE:
            s = sk.EVENT_SKELETONS[e]
            with self.subTest(event=e):
                self.assertEqual(s["weather"], self.WEATHER)
                self.assertIs(s["weather"], sk.FIRE_WEATHER)
                self.assertEqual({k: v for k, v in s["spots"].items()}, {k: p for k, (_, p) in self.SPOTS[e].items()})
                for spot, (camera, place) in self.SPOTS[e].items():
                    self.assertEqual(sk.CAMERA_SPOTS[spot], camera)
                    suffix = sk.style_suffix(e, None, spot)
                    self.assertTrue(suffix.startswith(f"Handheld footage shot by a person standing {camera}, eye level"),
                                    suffix)
                    self.assertTrue(suffix.endswith(" No readable signs, text or flags."), suffix)
                    self.assertNotIn("phone", suffix.lower())
                    self.assertEqual(es.rain_words(suffix), [])
                    from core.trace_format import count_constraints
                    self.assertLessEqual(count_constraints(suffix)[0], 8)
                for x in list(s["spots"].values()) + s["weather"] + [s["text"]]:
                    self.assertEqual(es.rain_words(x), [], x)
        # 8 Eki (2): yangında alçak (kaldırım) kamera noktası yok; cephe yangınının 4 noktası da yüksek
        env = DOMAIN_ATTRIBUTES["fire_disasters"]["environments"]
        self.assertFalse([s for s in env if "sidewalk" in s.lower() or "sidewalk" in sk.CAMERA_SPOTS[s]])
        self.assertEqual(len(sk.EVENT_SKELETONS[es.FACADE_FIRE]["spots"]), 4)
        for spot in sk.EVENT_SKELETONS[es.FACADE_FIRE]["spots"]:
            self.assertRegex(sk.CAMERA_SPOTS[spot], r"^on a (high balcony|rooftop terrace) ")
        # mevcut olayların kamera satırları değişmedi (aynı ortam adları başka olaylarda)
        self.assertEqual(sk.CAMERA_SPOTS["Downtown city center"], "on a sidewalk across the street")
        self.assertEqual(sk.CAMERA_SPOTS["High-rise coastal city"], "on a sidewalk across the street")
        self.assertEqual(sk.LANDSLIDE_WEATHER, ["driving rain and wind", "heavy downpour under dark storm light",
                                                "steady heavy rain, grey low cloud"])

    def test_pools_locked(self):
        for e, (s2, s3, pairs, spots) in self.POOLS.items():
            b = es.EVENT_BEATS[e]
            with self.subTest(event=e):
                self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, s2)
                self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, s3)
                self.assertEqual(b["excluded_pairs"], pairs)
                self.assertEqual(b["excluded_views"], {})
                self.assertEqual(b["excluded_spots"], spots)
                self.assertEqual([n for n, _ in es.EVENT_VEHICLES[e]], self.VEHICLES)
                for t in list(s2.values()) + list(s3.values()):
                    self.assertEqual(es.rain_words(t), [], t)

    def test_fire_term_lists_are_new(self):
        # Yangın maddeleri kaynakta sadece _FIRE_* listelerini kullanır; mevcut sel/heyelan/hortum listelerine
        # (_TEAR, _CRASH_DOWN, _TORNADO_RIP...) başvuru yok. Kimlik (is) karşılaştırması kullanılmaz: Python aynı
        # içerikli sabit demetleri tek nesnede birleştirebilir.
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(es))
        beats = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                     and any(getattr(t, "id", None) == "EVENT_BEATS" for t in n.targets))
        fire_names = {"WILDFIRE", "FACADE_FIRE", "FIRE_TORNADO"}
        seen = 0
        for key, val in zip(beats.keys, beats.values):
            if getattr(key, "id", None) not in fire_names:
                continue
            seen += 1
            for slot in ("slice_2", "slice_3"):
                slot_node = val.values[[k.value for k in val.keys].index(slot)]
                for bid_node, beat in zip(slot_node.keys, slot_node.values):
                    terms = beat.values[[k.value for k in beat.keys].index("terms")]
                    names = {n.id for n in ast.walk(terms) if isinstance(n, ast.Name)}
                    with self.subTest(beat=bid_node.value):
                        self.assertTrue(names and all(n.startswith("_FIRE_") for n in names), names)
        self.assertEqual(seen, 3)
        # mevcut ortak listeler aynı kaldı (örnek kilitler)
        self.assertEqual(es._CRASH_DOWN, ("crash", "slam", "smash", "land", "drop", "plunge", "plummet", "come down",
                                          "comes down", "came down", "fall", "fell", "hit", "strike", "struck",
                                          "collapse"))
        self.assertEqual(es._TEAR, ("tear", "tore", "torn", "rip", "wrench", "sweep", "swept", "carry", "carried",
                                    "pull", "snap", "break", "broke", "collapse", "flatten", "uproot"))
        self.assertEqual(es._FLEE, ("run", "ran", "running", "flee", "fled", "fleeing", "sprint", "scatter", "dash",
                                    "bolt", "race", "scramble", "dart", "hurry"))
        self.assertEqual(es.TOTAL_WORDS, (40, 70))
        # 10 Eki, Bahadır: sadece orman yangını 40-75; cephe ve ateş hortumu genel 40-70
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[es.WILDFIRE], (40, 75))
        for e in (es.FACADE_FIRE, es.FIRE_TORNADO):
            self.assertNotIn(e, es.TOTAL_WORDS_BY_EVENT)

    def test_canonical_terms_pass(self):
        for e in FIRE:
            for slot in ("slice_2", "slice_3"):
                for bid, beat in es.EVENT_BEATS[e][slot].items():
                    for vehicle in self.VEHICLES:
                        text = cap(es.beat_text(e, slot, bid, vehicle))
                        with self.subTest(beat=bid, vehicle=vehicle):
                            self.assertEqual(es.missing_term_groups(beat["terms"], text), [])

    def test_variants_and_flame_contact(self):
        ok = {(es.WILDFIRE, "K1"): "The SUV backs up fast as a blazing pine topples across the lane ahead.",
              (es.WILDFIRE, "K2"): "The white van screeches to a halt as flames sweep over the road and scorch its "
                                   "bonnet.",
              (es.WILDFIRE, "K3"): "A flaming limb crashes onto the small car and its roof bursts into flames.",
              (es.WILDFIRE, "K5"): "The pickup truck whips around in the smoke and races off as the fire seals the road.",
              (es.WILDFIRE, "L2"): "Glowing embers shower the street and set a picket fence ablaze.",
              (es.WILDFIRE, "L6"): "Fire climbs a utility pole and the burning cables snap and lash across the street.",
              (es.FACADE_FIRE, "M3"): "Burning wreckage lands on the hood of the SUV, which jerks back in a hurry.",
              (es.FACADE_FIRE, "N2"): "A balcony canopy catches fire and the flames leap to the upper floor.",
              (es.FACADE_FIRE, "N6"): "The fire leaps to the next balcony and engulfs its plants and chairs.",
              (es.FIRE_TORNADO, "T1"): "The swirling flames heave the van off the road and hurl it into a burning "
                                       "tree.",
              (es.FIRE_TORNADO, "T3"): "The SUV is picked up by the vortex, spins wildly and slams down onto the road.",
              (es.FIRE_TORNADO, "U4"): "The tornado sucks up burning brush and spews it across the road in sparks."}
        bad = {
            # sadece rüzgâr: alev bir şeye değmiyor
            (es.WILDFIRE, "L4"): "The hot wind bends a row of trees along the road.",
            (es.WILDFIRE, "L1"): "Strong wind sweeps over the roofs of the nearest houses.",
            (es.WILDFIRE, "K2"): "The SUV skids to a stop as the wind gusts across the road.",
            (es.FACADE_FIRE, "N4"): "A gust of wind rolls up the tower.",
            (es.FACADE_FIRE, "N6"): "The wind shakes the plants on the neighboring balcony.",
            (es.FIRE_TORNADO, "U3"): "The wind tears a billboard from its supports.",
            # olay eksik
            (es.WILDFIRE, "K3"): "A burning branch falls beside the small car.",
            (es.FACADE_FIRE, "M1"): "A burning panel falls near the SUV.",
            (es.FIRE_TORNADO, "T1"): "The van is pushed into a burning tree.",
            (es.FIRE_TORNADO, "T3"): "The SUV spins on the road.",
        }
        for (e, bid), s in ok.items():
            slot = "slice_2" if bid[0] in "KMT" else "slice_3"
            with self.subTest(ok=bid):
                self.assertEqual(es.missing_term_groups(es.EVENT_BEATS[e][slot][bid]["terms"], s), [])
        for (e, bid), s in bad.items():
            slot = "slice_2" if bid[0] in "KMT" else "slice_3"
            with self.subTest(bad=bid, text=s):
                self.assertTrue(es.missing_term_groups(es.EVENT_BEATS[e][slot][bid]["terms"], s))

    def test_rain_ban(self):
        for t in ("Heavy rain falls on the burning roofs.", "It is raining.", "The rain-soaked road shines.",
                  "Drenched trees burn.", "Cars roll over the wet asphalt.", "A downpour hits the street.",
                  "The street is soaked.", "Puddles reflect the flames.", "Rainy smoke drifts.",
                  "Embers fall as the rain starts."):
            with self.subTest(text=t):
                self.assertTrue(es.rain_words(t), t)
        for t in ("Embers rain onto the SUV.", "A shower of glowing embers rains onto the street.",
                  "Shattered glass rains onto the van.", "Raining burning debris onto the street.",
                  "Sparks rain down on the road.", "A shower of sparks whips across the street."):
            with self.subTest(text=t):
                self.assertEqual(es.rain_words(t), [], t)
        for e in FIRE:
            spot = next(iter(self.SPOTS[e]))
            b2, b3 = es.allowed_pairs(e, None, spot)[0]
            spec, slices, _ = self.build(e, b2, b3, spot, "SUV")
            with self.subTest(event=e):
                self.assertNotIn("fire_no_rain", self.codes(spec, slices))
                for f in es.SLICE_FIELDS:
                    wet = {**slices, f: es.clean_slice(slices[f].rstrip(".") + " on the wet road")}
                    self.assertIn("fire_no_rain", self.codes(spec, wet), f)
                rain = {**slices, "slice_3": es.clean_slice(slices["slice_3"].rstrip(".") + " in the heavy rain")}
                fb = {i["rule"]: i for i in es.slice_issues(spec, rain)}
                self.assertEqual(fb["fire_no_rain"]["missing"], "yağmur/ıslaklık yasak (rain)")
                self.assertEqual(fb["fire_no_rain"]["feedback"],
                                 "Remove 'rain': the air is hot and dry; no rain, wet or soaked surfaces anywhere.")
        # diğer olaylarda yağmur kapısı yok (heyelan yağmurlu kalır)
        spec = es.build_spec(es.MUDSLIDE, None, "Balcony across a steep hillside street", None, "H3", "M2", "SUV", 4)
        sl = {"slice_1_rest": "Four people run from the mud in the heavy rain.",
              "slice_2": "The SUV is spun around by the mud and dragged downhill in the rain.",
              "slice_3": "A utility pole snaps and falls into the mud on the wet street."}
        self.assertFalse({i["rule"] for i in es.slice_issues(spec, sl)} & {"fire_no_rain", "fire_no_lift"})

    def test_no_lift_only_wildfire_and_facade(self):
        self.assertEqual(es.NO_LIFT_SLICE, {es.WILDFIRE: ("slice_2",), es.FACADE_FIRE: ("slice_2",),
                                            es.HELICOPTER: ("slice_2",)})   # 10 Eki
        for e, b2, b3, spot in ((es.WILDFIRE, "K2", "L3", "Embankment above the village road"),
                                (es.FACADE_FIRE, "M6", "N1", "Rooftop terrace across from a downtown tower")):
            spec, slices, _ = self.build(e, b2, b3, spot, "SUV")
            self.assertNotIn("fire_no_lift", self.codes(spec, slices))
            for add in (", lifted off its wheels", " as it goes airborne", " and is swept up by the blast"):
                lifted = {**slices, "slice_2": es.clean_slice(slices["slice_2"].rstrip(".") + add)}
                with self.subTest(event=e, add=add):
                    self.assertIn("fire_no_lift", self.codes(spec, lifted))
            fb = {i["rule"]: i for i in es.slice_issues(spec, {**slices, "slice_2": "The SUV goes airborne."})}
            self.assertEqual(fb["fire_no_lift"]["feedback"], "In 'slice_2' the SUV stays on the ground: remove "
                                                             "'airborne'.")
        # ateş hortumunda araç havalanır (T1/T3)
        spec, slices, _ = self.build(es.FIRE_TORNADO, "T3", "U5", "Overlook above the burning valley road", "SUV")
        self.assertEqual(self.codes(spec, slices), set())

    def test_all_combinations_pass_final_check(self):
        n, longest = 0, 0
        for e in FIRE:
            head = f"0-4s: {self.KEY[e]} "
            for spot in sk.view_spots(e, None):
                pairs = es.allowed_pairs(e, None, spot)
                self.assertTrue(pairs, (e, spot))
                for b2, b3 in pairs:
                    for vehicle in self.VEHICLES:
                        spec, slices, prompt = self.build(e, b2, b3, spot, vehicle, people=3 + n % 4)
                        issues = es.final_prompt_issues(spec, slices, prompt, es.assemble_story(spec, slices))
                        if issues:
                            self.fail(f"{e}/{spot}/{b2}+{b3}/{vehicle}: {issues}\n{prompt}")
                        self.assertTrue(prompt.startswith(head))
                        self.assertIn(sk.CAMERA_SPOTS[spot], prompt)
                        longest = max(longest, len(prompt))
                        n += 1
        # orman: balkon 24 - 3 + set 33; cephe 4 nokta × 33; ateş hortumu: tepe 33 + balkon 30 - 3; × 4 araç
        self.assertEqual(n, (21 + 33) * 4 + 33 * 4 * 4 + (33 + 27) * 4)
        self.assertLess(longest, es.MAX_PROMPT_CHARS)

    def test_excluded_spots(self):
        def d3(e, spot):
            return {d for _, d in es.allowed_pairs(e, None, spot)}
        self.assertFalse({"L1", "L5"} & d3(es.WILDFIRE, "Balcony of a hillside house"))
        self.assertTrue({"L1", "L5"} <= d3(es.WILDFIRE, "Embankment above the village road"))
        self.assertNotIn("U1", d3(es.FIRE_TORNADO, "Balcony of a roadside house"))
        self.assertIn("U1", d3(es.FIRE_TORNADO, "Overlook above the burning valley road"))
        for spot in self.SPOTS[es.FACADE_FIRE]:
            self.assertEqual(d3(es.FACADE_FIRE, spot), {"N1", "N2", "N3", "N4", "N5", "N6"})

    def test_people_gate_and_line(self):
        import core.creative_pipeline as cp
        for e in FIRE:
            r = {x["rule"]: x for x in es.SLICE_RULES[e]}
            self.assertIs(r["slice_flee"]["terms"], es._FLEE)
            self.assertNotIn("rush", r["slice_flee"]["terms"])
            self.assertEqual(r["slice_flee"]["feedback"],
                             f"'slice_1_rest' must show people running away from {self.AWAY[e]}.")
        spec, slices, _ = self.build(es.FIRE_TORNADO, "T2", "U5", "Overlook above the burning valley road", "SUV", 6)
        msg = cp._slices_message(spec, "P", "W", 3, 6, [], None)
        self.assertIn("\nVEHICLE: SUV\nPEOPLE RUNNING AWAY: six (slice_1_rest must say that six people run away "
                      "from the fire tornado)\n4-9s EVENT: ", msg)

        def codes(s1):
            return self.codes(spec, {**slices, "slice_1_rest": es.clean_slice(s1)})
        self.assertFalse(codes("Six drivers sprint away from the fire tornado.") & {"slice_flee", "slice_count"})
        self.assertIn("slice_count", codes("Four drivers sprint away from the fire tornado."))
        self.assertIn("slice_flee", codes("Six drivers rush away from the fire tornado."))   # "rush" kaçış sayılmaz
        self.assertIn("slice_flee", codes("Six drivers stare at the fire tornado."))

    def test_message_camera_place_weather(self):
        import core.creative_pipeline as cp
        spec, _, _ = self.build(es.WILDFIRE, "K2", "L3", "Balcony of a hillside house", "white van", 4)
        msg = cp._slices_message(spec, "a hillside village neighborhood", self.WEATHER[1], 3, 6, [], None)
        self.assertEqual(
            msg,
            "OPENING SENTENCE (fixed, already written): " + self.KEY[es.WILDFIRE] + "\n"
            "PLACE: a hillside village neighborhood\nWEATHER: gusty dry wind under an orange smoky sky\n"
            "PEOPLE VISIBLE: 3 to 6\nVEHICLE: white van\n"
            "PEOPLE RUNNING AWAY: four (slice_1_rest must say that four people run away from the flames)\n"
            "4-9s EVENT: the white van skids to a stop as flames leap across the road and lick its hood\n"
            "9-15s EVENT: the fire races across a garden, engulfing a parked trailer and a woodpile\n"
            "RECENT STORIES:\n- (none)")
        self.assertEqual(es.rain_words(msg), [])
        self.assertEqual(spec["suffix"], sk.style_suffix(es.WILDFIRE, None, "Balcony of a hillside house"))

    def test_scene_without_view(self):
        import asyncio
        import core.creative_pipeline as cp
        calls = []

        async def gpt(system, user, **kw):
            calls.append(user)
            line = dict(l.split(": ", 1) for l in user.splitlines()
                        if l.startswith(("4-9s EVENT", "9-15s EVENT", "PEOPLE RUNNING AWAY")))
            word = line["PEOPLE RUNNING AWAY"].split()[0]
            away = line["PEOPLE RUNNING AWAY"].split("run away from ")[1].rstrip(")")
            return {"slice_1_rest": f"{cap(word)} people run from {away}.",
                    "slice_2": cap(line["4-9s EVENT"]) + ".", "slice_3": cap(line["9-15s EVENT"]) + "."}
        for e in FIRE:
            with self.subTest(event=e):
                scene = asyncio.run(cp.build_creative_scene("fire_disasters", e, [], [], gpt))
                t = scene["trace"]
                self.assertIsNone(t["view"])
                self.assertIsNone(scene["ship"])
                self.assertIn(t["spot"], self.SPOTS[e])
                self.assertEqual(t["place"], self.SPOTS[e][t["spot"]][1])
                self.assertIn(t["weather"], self.WEATHER)
                self.assertIn(t["vehicle"], self.VEHICLES)
                self.assertIn(t["people_running"], (3, 4, 5, 6))
                self.assertIn(f"|{t['spot'].lower()}##{t['beats']}|", scene["combo_key"])
                self.assertTrue(scene["combo_key"].startswith("fire_disasters|none|"))
                self.assertTrue(sk.is_current_universe_combo(scene["combo_key"]))
                self.assertIn(self.SPOTS[e][t["spot"]][0], scene["prompt"])
                spec, sl = scene["structure"]["spec"], scene["structure"]["slices"]
                self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
                self.assertIn(f"run away from {self.AWAY[e]}", calls[-1])

    def test_no_candidates_never(self):
        from itertools import combinations
        k = es.RECENT_BEAT_BLOCK
        for e in FIRE:
            b = es.EVENT_BEATS[e]
            for spot in sk.view_spots(e, None):
                pairs = es.allowed_pairs(e, None, spot)
                worst = min(sum(1 for v, d in pairs if v not in x2 and d not in x3)
                            for x2 in map(set, combinations(b["slice_2"], k))
                            for x3 in map(set, combinations(b["slice_3"], k)))
                with self.subTest(event=e, spot=spot):
                    self.assertGreater(worst, 0)


class TestOct10Changes(unittest.TestCase):
    """10 Eki, Bahadır: hortum cadde yüksek balkon, orman 75 kelime + terim genişletmesi. KİLİT."""

    def test_avenue_high_balcony_cameras(self):
        cams = {"High balcony over a downtown avenue": "on a high balcony across the street, overlooking the avenue",
                "Upper-floor balcony over a residential avenue":
                    "on an upper-floor balcony across the street, overlooking the avenue",
                "High balcony over a high-rise avenue": "on a high balcony across the street, overlooking the avenue"}
        places = ["a palm-lined coastal avenue downtown",
                  "a palm-lined coastal avenue through a residential neighborhood",
                  "a palm-lined coastal avenue below high-rise towers"]
        s = sk.EVENT_SKELETONS[es.AVENUE]
        self.assertEqual(list(s["spots"]), list(cams))
        self.assertEqual(list(s["spots"].values()), places)              # yer metinleri aynı kaldı
        for spot, cam in cams.items():
            self.assertEqual(sk.CAMERA_SPOTS[spot], cam)
            suffix = sk.style_suffix(es.AVENUE, None, spot)
            self.assertTrue(suffix.startswith(f"Handheld footage shot by a person standing {cam}, eye level,"), suffix)
        self.assertEqual(es.EVENT_BEATS[es.AVENUE]["excluded_spots"], {})

    def test_other_tornado_and_beach_cameras_unchanged(self):
        self.assertEqual({spot: sk.CAMERA_SPOTS[spot] for spot in sk.EVENT_SKELETONS[es.LANDFALL]["spots"]}, {
            "Beachfront promenade": "further along the promenade",
            "Residential coastal district": "on a front porch across the street",
            "Downtown city center": "on a sidewalk across the street"})
        self.assertEqual({spot: sk.CAMERA_SPOTS[spot] for spot in sk.EVENT_SKELETONS[es.MARINA_TORNADO]["spots"]},
                         {"High marina balcony": "on a high balcony overlooking the marina and quay"})
        beach = "Tornado approaching an open beach"
        self.assertEqual({spot: sk.CAMERA_SPOTS[spot] for spot in sk.EVENT_SKELETONS[beach]["spots"]}, {
            "Open sandy beach": "at the top of the beach", "Wide public beach": "at the top of the beach",
            "Coastal resort beach": "on a hotel terrace above the beach"})
        # eski cadde noktaları tablolarda kalır (başka olaylar kullanıyor)
        self.assertEqual(sk.CAMERA_SPOTS["High-rise coastal city"], "on a sidewalk across the street")
        self.assertIn("Downtown city center", sk.EVENT_SKELETONS[es.FLOOD]["spots"])
        from core.creative_engine import DOMAIN_ATTRIBUTES
        env = DOMAIN_ATTRIBUTES["coastal_tornado_landfall"]["environments"]
        for old in ("Downtown city center", "Residential coastal district", "High-rise coastal city"):
            self.assertIn(old, env)

    def test_wildfire_75_words_only(self):
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[es.WILDFIRE], (40, 75))
        self.assertEqual(es.TOTAL_WORDS, (40, 70))

        def rules(event, spot, b2, b3, words):
            spec = es.build_spec(event, None, spot, None, b2, b3, "SUV", 5)
            s2 = es.clean_slice(cap(es.beat_text(event, "slice_2", b2, "SUV")))
            s3 = es.clean_slice(cap(es.beat_text(event, "slice_3", b3)))
            base = len(es.plain_story(spec, {"slice_1_rest": "", "slice_2": s2, "slice_3": s3}).split())
            extra = words - base - 6
            sl = {"slice_1_rest": es.clean_slice("Five people run from the flames" + " far" * extra),
                  "slice_2": s2, "slice_3": s3}
            self.assertEqual(len(es.plain_story(spec, sl).split()), words)
            return {i["rule"] for i in es.slice_issues(spec, sl)}
        for words, bad in ((70, False), (75, False), (76, True)):
            with self.subTest(event="orman", words=words):
                self.assertEqual("total_words" in rules(es.WILDFIRE, "Embankment above the village road", "K2",
                                                         "L3", words), bad)
        for words, bad in ((70, False), (71, True)):
            with self.subTest(event="cephe", words=words):
                self.assertEqual("total_words" in rules(es.FACADE_FIRE, "Rooftop terrace across from a downtown tower",
                                                         "M5", "N2", words), bad)

    def test_fire_term_additions(self):
        for w in ("fiery", "aflame", "smolder", "smoulder"):
            self.assertIn(w, es._FIRE_FLAME)
        for w in ("maneuver", "manoeuvre", "evade", "sidestep", "careen", "zigzag"):
            self.assertIn(w, es._FIRE_SWERVE)
        k4 = es.EVENT_BEATS[es.WILDFIRE]["slice_2"]["K4"]["terms"]
        # 8 Eki canlı ret: "fiery" ve "maneuvers" eşleşmiyordu
        for t in ("The SUV maneuvers around a falling fiery pine and slams into the guardrail.",
                  "The small car sidesteps a toppling pine, smouldering branches everywhere, and hits the barrier.",
                  "The white van careens past a fiery tree and crashes into the railing."):
            with self.subTest(text=t):
                self.assertEqual(es.missing_term_groups(k4, t), [])
        # sadece rüzgâr hâlâ geçmez
        self.assertTrue(es.missing_term_groups(k4, "The SUV maneuvers around a pine bending in the wind and hits the "
                                                   "guardrail."))


class TestHelicopter(unittest.TestCase):
    """10 Eki, Bahadır: 🔥 Yangın söndürme helikopteri (4. yangın olayı). Havuzlar ONAYLI. KİLİT."""

    E = es.HELICOPTER
    KEY = ("A firefighting helicopter swoops over a hillside neighborhood and drops a huge load of water onto the wall "
           "of flames racing toward the houses.")
    S2 = {
        "F1": "the water load slams into the flames, flattening a section of the wall into a cloud of white steam",
        "F2": "the helicopter drops a second load and the water crashes down onto burning rooftops, sending steam and "
              "sparks billowing",
        "F3": "the {vehicle} speeds down the street as the helicopter's downdraft whips smoke and embers across the road",
        "F4": "the helicopter roars low over the street, its downdraft bending the burning trees and scattering embers",
        "F5": "a wall of water falls on a burning house, the flames collapsing into thick white steam",
        "F6": "the {vehicle} brakes hard as a drenching cascade of water spills across the road in front of it",
    }
    S3 = {
        "G1": "the flames fight back, a fresh burst of fire swallowing trees beside the water line",
        "G2": "the helicopter circles back and drops another huge load, extinguishing a row of burning trees in a cloud "
              "of steam",
        "G3": "thick white steam rolls over the street as the wall of flames sinks back toward the slope",
        "G4": "embers blow past the helicopter as flames leap to a roof the water missed",
        "G5": "the helicopter pulls up and away as the flames roar back behind it",
        "G6": "a second helicopter swoops in and drops water on the flames along the road",
    }
    SPOTS = {"Balcony of a hillside house": "on a balcony of a hillside house overlooking the street and the burning "
                                            "slope",
             "Embankment above the village road": "on a roadside embankment above the village road"}
    VEHICLES = ["pickup truck", "small car", "white van", "SUV"]

    def setUp(self):
        es._BEAT_MEMORY.clear()

    def slices(self, b2, b3, vehicle, people, s1=None):
        return {"slice_1_rest": es.clean_slice(s1 or f"{cap(es.NUMBER_WORDS[people])} people run from the flames."),
                "slice_2": es.clean_slice(cap(es.beat_text(self.E, "slice_2", b2, vehicle))),
                "slice_3": es.clean_slice(cap(es.beat_text(self.E, "slice_3", b3)))}

    def build(self, b2, b3, spot="Embankment above the village road", vehicle="SUV", people=5, **kw):
        spec = es.build_spec(self.E, None, spot, None, b2, b3, vehicle, people)
        sl = self.slices(b2, b3, vehicle, people, **kw)
        return spec, sl

    def codes(self, spec, sl):
        return {i["rule"] for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl))}

    def test_menu_and_registrations(self):
        import bot
        import core.creative_pipeline as cp
        from core.creative_engine import DOMAIN_ATTRIBUTES
        self.assertEqual(self.E, "Firefighting helicopter drops water on the flames racing toward a hillside "
                                 "neighborhood")
        self.assertEqual(bot.EVENT_LABELS[self.E], "🔥 Yangın söndürme helikopteri")
        self.assertEqual(DOMAIN_ATTRIBUTES["fire_disasters"]["events"][-1], self.E)
        self.assertIn(self.E, es.FIRE_EVENTS)
        self.assertIn(self.E, es.NO_RAIN_EVENTS)
        self.assertEqual(es.WATER_DROP_EVENTS, (self.E,))
        self.assertEqual(cp.EVENT_REQUIRED[self.E], [])
        self.assertNotIn(self.E, cp.REQUIRED_APPROVED)
        self.assertIn(self.E, cp.EVENT_OUTCOMES)
        self.assertEqual(sk.count_range(self.E, None), (3, 6))
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[self.E], (40, 75))
        self.assertEqual(es.structure_views(self.E), [None])
        self.assertEqual([n for n, _ in es.EVENT_VEHICLES[self.E]], self.VEHICLES)

    def test_key_visual_and_pools_locked(self):
        import core.creative_pipeline as cp
        self.assertEqual(es.EVENT_KEY_VISUAL[self.E], self.KEY)
        found = {i["rule"] for i in cp.story_rule_issues(self.E, None, self.KEY)}
        self.assertFalse(found & {"a_trigger_first", "e_event_and_ship_named", "required"})
        b = es.EVENT_BEATS[self.E]
        self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, self.S2)
        self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, self.S3)
        self.assertEqual(b["excluded_pairs"], {("F1", "G3"), ("F2", "G2"), ("F5", "G3")})
        self.assertEqual(b["excluded_views"], {})
        # kamera evi: yanan çatıya/eve su (F2, F5) ve ıskalanan çatıya alev (G4) balkon noktasında seçilmez
        self.assertEqual(b["excluded_spots"], {"F2": {"Balcony of a hillside house"},
                                               "F5": {"Balcony of a hillside house"},
                                               "G4": {"Balcony of a hillside house"}})

    def test_cameras_high_and_weather(self):
        s = sk.EVENT_SKELETONS[self.E]
        self.assertEqual(list(s["spots"]), list(self.SPOTS))
        self.assertEqual(set(s["spots"].values()), {"a hillside village neighborhood"})
        self.assertIs(s["weather"], sk.FIRE_WEATHER)
        for spot, cam in self.SPOTS.items():
            self.assertEqual(sk.CAMERA_SPOTS[spot], cam)
            suffix = sk.style_suffix(self.E, None, spot)
            self.assertTrue(suffix.startswith(f"Handheld footage shot by a person standing {cam}, eye level"))
            self.assertIn("the camera pans to follow the firefighting helicopter", suffix)
            self.assertTrue(suffix.endswith(" No readable signs, text or flags."))
            self.assertEqual(es.rain_words(suffix, True), [])
        # orman yangını aynı iki noktayı kullanmaya devam eder
        self.assertEqual(list(sk.EVENT_SKELETONS[es.WILDFIRE]["spots"]), list(self.SPOTS))

    def test_term_lists_fire_only_and_canonical_pass(self):
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(es))
        beats = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                     and any(getattr(t, "id", None) == "EVENT_BEATS" for t in n.targets))
        node = next(v for k, v in zip(beats.keys, beats.values) if getattr(k, "id", None) == "HELICOPTER")
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        self.assertTrue(names and all(n.startswith("_FIRE_") for n in names), names)
        for slot in ("slice_2", "slice_3"):
            for bid, beat in es.EVENT_BEATS[self.E][slot].items():
                for v in self.VEHICLES:
                    text = cap(es.beat_text(self.E, slot, bid, v))
                    with self.subTest(beat=bid, vehicle=v):
                        self.assertEqual(es.missing_term_groups(beat["terms"], text), [])
                        self.assertEqual(es.rain_words(text, True), [])

    def test_variants_and_wrong_event(self):
        ok = {"F1": "The water crashes into the blaze, turning a stretch of flames into white vapor.",
              "F3": "The pickup truck races away as the rotor wash blasts smoke and sparks over the road.",
              "F6": "The SUV stops short as a deluge of water spills over the street ahead.",
              "G2": "The chopper returns and dumps more water, dousing a line of burning pines in steam.",
              "G3": "White steam drifts across the street as the flames recede toward the slope.",
              "G5": "The helicopter climbs away as the fire flares again behind it."}
        bad = {"F1": "The helicopter flies over the neighborhood.",
               "F4": "The helicopter roars low over the street.",
               "G2": "The helicopter circles back over the trees.",
               "G6": "A second helicopter appears over the road."}
        for bid, s in ok.items():
            slot = "slice_2" if bid[0] == "F" else "slice_3"
            with self.subTest(ok=bid):
                self.assertEqual(es.missing_term_groups(es.EVENT_BEATS[self.E][slot][bid]["terms"], s), [])
        for bid, s in bad.items():
            slot = "slice_2" if bid[0] == "F" else "slice_3"
            with self.subTest(bad=bid):
                self.assertTrue(es.missing_term_groups(es.EVENT_BEATS[self.E][slot][bid]["terms"], s))

    def test_water_not_rain(self):
        # su bırakma ıslaklığı serbest, yağış yine yasak
        for t in ("A drenching cascade of water spills across the road.", "The roofs are soaked and wet.",
                  "Water rains down on the burning roofs."):
            with self.subTest(text=t):
                self.assertEqual(es.rain_words(t, True), [])
        for t in ("Heavy rain falls on the flames.", "A downpour hits the street.", "The rain-soaked road.",
                  "Rainy smoke drifts."):
            with self.subTest(text=t):
                self.assertTrue(es.rain_words(t, True))
        # diğer yangın olaylarında "drench" hâlâ reddedilir (varsayılan davranış aynı)
        self.assertEqual(es.rain_words("A drenching cascade of water spills across the road."), ["drench"])
        spec, sl = self.build("F6", "G1", vehicle="white van")
        self.assertNotIn("fire_no_rain", self.codes(spec, sl))
        rain = {**sl, "slice_3": es.clean_slice(sl["slice_3"].rstrip(".") + " in the heavy rain")}
        self.assertIn("fire_no_rain", self.codes(spec, rain))
        wf = es.build_spec(es.WILDFIRE, None, "Embankment above the village road", None, "K2", "L3", "SUV", 5)
        wsl = {"slice_1_rest": "Five people run from the flames.",
               "slice_2": "The SUV skids to a stop as flames leap across the road and lick its hood.",
               "slice_3": "The fire races across a garden, engulfing a trailer and a woodpile on the drenched lawn."}
        self.assertIn("fire_no_rain", {i["rule"] for i in es.slice_issues(wf, wsl)})

    def test_vehicle_required_only_in_vehicle_beats(self):
        for b2 in ("F1", "F2", "F4", "F5"):
            spec, sl = self.build(b2, "G1", vehicle="pickup truck")
            with self.subTest(beat=b2):
                self.assertNotIn("beat_vehicle", self.codes(spec, sl))
        for b2 in ("F3", "F6"):
            spec, sl = self.build(b2, "G1", vehicle="pickup truck")
            no_vehicle = {**sl, "slice_2": es.clean_slice(sl["slice_2"].replace("pickup truck", "crowd"))}
            with self.subTest(beat=b2):
                self.assertNotIn("beat_vehicle", self.codes(spec, sl))
                self.assertIn("beat_vehicle", self.codes(spec, no_vehicle))

    def test_no_lift(self):
        spec, sl = self.build("F3", "G1")
        lifted = {**sl, "slice_2": es.clean_slice(sl["slice_2"].rstrip(".") + ", lifted off its wheels")}
        self.assertIn("fire_no_lift", self.codes(spec, lifted))

    def test_total_words_75(self):
        spec, sl = self.build("F2", "G2")
        base = len(es.plain_story(spec, {**sl, "slice_1_rest": ""}).split())
        for words, bad in ((75, False), (76, True)):
            s1 = "Five people run from the flames" + " far" * (words - base - 6)
            sl2 = {**sl, "slice_1_rest": es.clean_slice(s1)}
            self.assertEqual(len(es.plain_story(spec, sl2).split()), words)
            with self.subTest(words=words):
                self.assertEqual("total_words" in {i["rule"] for i in es.slice_issues(spec, sl2)}, bad)

    def test_all_combinations_and_spot_exclusions(self):
        def pairs(spot):
            return es.allowed_pairs(self.E, None, spot)
        balcony = pairs("Balcony of a hillside house")
        self.assertFalse({v for v, _ in balcony} & {"F2", "F5"})
        self.assertNotIn("G4", {d for _, d in balcony})
        self.assertEqual(len(balcony), 4 * 5 - 1)
        self.assertEqual(len(pairs("Embankment above the village road")), 36 - 3)
        n = 0
        for spot in self.SPOTS:
            for b2, b3 in pairs(spot):
                for v in self.VEHICLES:
                    spec, sl = self.build(b2, b3, spot=spot, vehicle=v, people=3 + n % 4)
                    issues = es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl), es.assemble_story(spec, sl))
                    if issues:
                        self.fail(f"{spot}/{b2}+{b3}/{v}: {issues}")
                    n += 1
        self.assertEqual(n, (19 + 33) * 4)
        # 4-9s dışlaması diğer olaylarda hiçbir şeyi değiştirmez (mevcut dışlamaların hepsi 9-15s)
        for e, b in es.EVENT_BEATS.items():
            if e != self.E:
                self.assertFalse(set(b["excluded_spots"]) & set(b["slice_2"]), e)

    def test_no_candidates_never(self):
        from itertools import combinations
        b = es.EVENT_BEATS[self.E]
        for spot in self.SPOTS:
            ps_ = es.allowed_pairs(self.E, None, spot)
            worst = min(sum(1 for v, d in ps_ if v not in x2 and d not in x3)
                        for x2 in map(set, combinations(b["slice_2"], es.RECENT_BEAT_BLOCK))
                        for x3 in map(set, combinations(b["slice_3"], es.RECENT_BEAT_BLOCK)))
            with self.subTest(spot=spot):
                self.assertGreater(worst, 0)

    def test_scene_build(self):
        import asyncio
        import core.creative_pipeline as cp

        async def gpt(system, user, **kw):
            line = dict(l.split(": ", 1) for l in user.splitlines()
                        if l.startswith(("4-9s EVENT", "9-15s EVENT", "PEOPLE RUNNING AWAY")))
            word = line["PEOPLE RUNNING AWAY"].split()[0]
            return {"slice_1_rest": f"{cap(word)} people run from the flames.",
                    "slice_2": cap(line["4-9s EVENT"]) + ".", "slice_3": cap(line["9-15s EVENT"]) + "."}
        scene = asyncio.run(cp.build_creative_scene("fire_disasters", self.E, [], [], gpt))
        t = scene["trace"]
        self.assertIn(t["spot"], self.SPOTS)
        self.assertIn(self.SPOTS[t["spot"]], scene["prompt"])
        self.assertTrue(scene["combo_key"].startswith("fire_disasters|none|firefighting helicopter"))
        spec, sl = scene["structure"]["spec"], scene["structure"]["slices"]
        self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])

if __name__ == "__main__":
    unittest.main()
