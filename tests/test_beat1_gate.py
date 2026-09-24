#!/usr/bin/env python3
"""
Beat 1 kapısı (whitelist + blacklist) ve stil kilidi gemi kadrajı testleri.

Fixture'lar 2026-09-24 dry-run'ındaki gerçek GPT-4o çıktılarıdır: #3 aksiyonla
başlıyordu (kazanan), #1 #2 #4 #5 durgun kurulumla başlıyordu.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.creative_engine import apply_style_lock, CAMERA_ARCHETYPES
from core.prompt_generator import (
    validate_high_action,
    validate_beat3_ongoing_danger,
    score_scenario,
    _beat1_action_words,
    _declared_beat1_verb_ok,
    _beat3_blacklist_hits,
    _beat3_ongoing_markers,
    _static_start_hits,
)

# Beat 2/3 her fixture'da aksiyonlu: sadece Beat 1'in etkisini ölçüyoruz.
_ACTIVE_REST = {
    "physical_movement": "The ramp violently swings downward and slams into the water.",
    "visible_consequence": "The ramp keeps grinding against the hull as the deckhand scrambles clear.",
    "scenario_summary": "A loading ramp hinge snaps and the ramp slams into the sea.",
}

DRY_RUN_VISIBLE_STARTS = {
    1: "From the bow of a nearby observer vessel, one deckhand in high-visibility gear is visible on the catamaran's deck as it approaches the ferry terminal.",
    2: "One dockworker stands near the ship's stern, observing as the general cargo ship smoothly begins its descent down the slipway.",
    3: "BEAT 1: The fixed security camera shows an overcast sky with waves crashing violently against the beach, already encroaching on the coastal road.",
    4: "One deckhand on the tender boat, visible from the fixed sun-deck security camera, signals for docking as the boat approaches the cruise ship.",
    5: "The scene opens on a bustling city street with towering skyscrapers looming overhead, dark storm clouds quickly rolling in, casting a menacing shadow over the area.",
}


def _scenario(visible_start: str) -> dict:
    return {"visible_start": visible_start, **_ACTIVE_REST}


class TestBeat1Gate(unittest.TestCase):

    def test_dry_run_fixtures(self):
        """Gerçek dry-run: #1 #2 #4 #5 aksiyon fiili yok diye reddedilir. #3'ün fiili var
        (crashing); 2026-09-24'ten beri SADECE kamera öznesiyle açıldığı için reddedilir."""
        for n, vs in DRY_RUN_VISIBLE_STARTS.items():
            with self.subTest(senaryo=n):
                ok, failures = validate_high_action(_scenario(vs))
                if n == 3:
                    self.assertFalse(ok)
                    self.assertEqual(failures, ["Beat 1 durgun kurulumla başlıyor: ['kamera öznesiyle açılış']"])
                else:
                    self.assertFalse(ok)
                    self.assertIn("Beat 1'de aksiyon fiili yok, tehlike başlamamış", failures)

    def test_false_friend_several(self):
        self.assertTrue(validate_high_action(_scenario("Several deckhands brace against the rail as the wave hits."))[0])
        self.assertFalse(validate_high_action(_scenario("Several deckhands stand on the open deck."))[0])

    def test_false_friend_severe(self):
        self.assertFalse(validate_high_action(_scenario("Severe storm clouds gather over the harbor."))[0])
        self.assertEqual(_beat1_action_words("Sparkling water beside a listening passenger."), [])

    def test_inflected_stems(self):
        """Sondaki e atılmış kökler: buckling, scrambling, toppling eşleşmeli."""
        words = _beat1_action_words("The hull buckling, crew scrambling as boxes topple.")
        self.assertEqual(words, ["buckling", "scrambling", "topple"])

    def test_visibly_not_blacklisted(self):
        self.assertEqual(_static_start_hits("the hull is visibly buckling under the load."), [])
        self.assertTrue(validate_high_action(_scenario("The hull is visibly buckling under the load."))[0])

    def test_opens_onto_not_blacklisted(self):
        vs = "The cargo hatch opens onto the deck as a wave slams over the rail."
        self.assertEqual(_static_start_hits(vs.lower()), [])
        self.assertTrue(validate_high_action(_scenario(vs))[0])

    def test_beat_label_stripped(self):
        self.assertEqual(_beat1_action_words("BEAT 1: waves crashing over the quay."), ["crashing"])
        self.assertEqual(_beat1_action_words("BEAT 2 (1-8s): the line snaps."), ["snaps"])
        self.assertTrue(validate_high_action(_scenario("BEAT 1: waves crashing over the quay."))[0])

    def test_action_only_in_second_sentence(self):
        vs = "One deckhand stands at the rail. A wave slams over the bow."
        self.assertEqual(_beat1_action_words(vs), [])
        self.assertFalse(validate_high_action(_scenario(vs))[0])

    def test_empty_visible_start(self):
        self.assertFalse(validate_high_action(_scenario(""))[0])
        self.assertFalse(validate_high_action(_ACTIVE_REST)[0])

    def test_blacklist_wins_over_action(self):
        """Aksiyon fiili olsa bile blacklist kalıbı reddeder."""
        vs = "One deckhand is visible as a wave slams over the bow."
        self.assertTrue(_beat1_action_words(vs))
        ok, failures = validate_high_action(_scenario(vs))
        self.assertFalse(ok)
        self.assertTrue(any("durgun kurulum" in f for f in failures))

    def test_approach_variants(self):
        for vs in ["as it approaches the pier", "as the tender boat approaches the ship",
                   "as the high-speed catamaran is approaching"]:
            with self.subTest(vs=vs):
                self.assertIn("as X approaches", _static_start_hits(vs))


class TestBeat1ExpandedStems(unittest.TestCase):
    """2026-09-24 N4: genişletilmiş whitelist kökleri ve yeni false friend'ler."""

    # Her yeni kök için gerçekçi bir Beat 1 açılışı ve beklenen eşleşme
    NEW_STEM_EXAMPLES = {
        "shake": ("A gust violently shakes the scaffolding.", "shakes"),
        "gush": ("Water gushes under the keel blocks.", "gushes"),
        "collapse": ("The gangway collapses under the crowd.", "collapses"),
        "hurl": ("The wave hurls a deck chair across the pool.", "hurls"),
        "yank": ("The storm yanks jet skis off the dock.", "yanks"),
        "sweep": ("A breaker sweeps across the vehicle deck.", "sweeps"),
        "whip": ("A parted hawser whips across the stern.", "whips"),
        "plunge": ("The bow plunges into a steep swell.", "plunges"),
        "veer": ("The tender veers toward the pier.", "veers"),
        "lash": ("Rain lashing the bridge windows.", "lashing"),
        "pound": ("Surf pounding the breakwater wall.", "pounding"),
        "batter": ("Gale-force waves batter the ferry's bow.", "batter"),
        "heave": ("The deck heaves under one deckhand.", "heaves"),
        "shatter": ("The wind-break glass shatters over the pool.", "shatters"),
        "twist": ("A waterspout twisting over the marina.", "twisting"),
        "barrel": ("A tornado barrels into the marina.", "barrels"),
        "slide": ("A loose trailer slides across the deck.", "slides"),
        "slip": ("One deckhand slips on the flooded ramp.", "slips"),
        "spray": ("Green water sprays over the forecastle.", "sprays"),
        "flip": ("The jet ski flips in the breaking surf.", "flips"),
        "tumble": ("Containers tumble off the stack.", "tumble"),
    }

    # Kökü eşleşen ama anlamı durgun kelimeler: whitelist'i geçmemeli
    FALSE_FRIEND_EXAMPLES = [
        "A cargo ship waits on the slipway.",
        "A slippery quay beside the ferry.",
        "A yacht sits in its slip at the marina.",
        "Shaky phone footage of the harbor.",
        "Heavy rain over the container port.",
        "One passenger wearing flip-flops on the deck.",
        "An oil barrel on the quay.",
        "Vehicle lashings on the car deck.",
        "A battery pack beside the winch.",
    ]

    # N3 dry-run (2026-09-24) gerçek metinleri: dar whitelist bunları yanlış reddetti
    N3_FIXTURES = {
        1: ("Two dock workers in high-visibility gear are seen securing equipment near the ship's hull as water suddenly gushes under the keel blocks.", "gushes"),
        3: ("A powerful gust of wind violently shakes the high-rise scaffolding.", "shakes"),
    }

    def test_new_stems_match(self):
        for stem, (vs, expected) in self.NEW_STEM_EXAMPLES.items():
            with self.subTest(kök=stem):
                self.assertIn(expected, _beat1_action_words(vs))
                self.assertTrue(validate_high_action(_scenario(vs))[0])

    def test_false_friends_rejected(self):
        for vs in self.FALSE_FRIEND_EXAMPLES:
            with self.subTest(vs=vs):
                self.assertEqual(_beat1_action_words(vs), [])
                self.assertFalse(validate_high_action(_scenario(vs))[0])

    def test_slipped_is_action(self):
        """'slipped' bilinçli false friend değil: düşme gerçek bir aksiyon."""
        self.assertEqual(_beat1_action_words("One deckhand slipped on the wet deck."), ["slipped"])

    def test_n3_regression_fixtures(self):
        for n, (vs, expected) in self.N3_FIXTURES.items():
            with self.subTest(senaryo=n):
                self.assertIn(expected, _beat1_action_words(vs))
                self.assertTrue(validate_high_action(_scenario(vs))[0])

    def test_previous_dry_run_unchanged(self):
        """Genişletme önceki turun sonucunu değiştirmemeli: #3'te aksiyon fiili bulunur, diğerlerinde
        bulunmaz. (#3 artık kamera öznesi yüzünden reddediliyor; bkz. test_dry_run_fixtures.)"""
        for n, vs in DRY_RUN_VISIBLE_STARTS.items():
            with self.subTest(senaryo=n):
                self.assertEqual(bool(_beat1_action_words(vs)), n == 3)


class TestBeat1N14Stems(unittest.TestCase):
    """2026-09-24 N14b: rüzgâr/tornado açılış kökleri ve yeni false friend'ler."""

    NEW_STEM_EXAMPLES = {
        "knock": ("A gust suddenly knocks deck chairs across the pool.", "knocks"),
        "spin": ("A massive tornado spins ferociously just offshore.", "spins"),
        "swirl": ("Debris swirling over the marina as the gust hits.", "swirling"),
        "shift": ("The hull begins to shift on the keel blocks.", "shift"),
        "rush": ("Water rushing across the vehicle deck.", "rushing"),
        "sway": ("The gangway sways violently under the crowd.", "sways"),
        "jolt": ("The tender jolts against the liner's platform.", "jolts"),
        "jerk": ("The mooring line jerks the yacht sideways.", "jerks"),
    }

    FALSE_FRIEND_EXAMPLES = [
        "A sailing yacht with its spinnaker set in the marina.",
        "Two spinnakers flap above the pontoon.",
        "The steel spine of the hull on the slipway.",
        "Workers stand beside the winch spindle.",
        "A shifty passenger on the deck.",
        "A jerky phone video of the harbor.",
        "A knockout view of the cruise terminal.",
    ]

    # N14 dry-run gerçek metinleri: dar whitelist bunları yanlış reddetti
    N14_FIXTURES = {
        3: ("About ten passengers gather on the cruise tender's sun deck when a strong gust of wind suddenly knocks a row of deck chairs off balance.", "knocks"),
        4: ("A massive tornado spins ferociously just offshore, darkening the sky and swirling debris through the air.", "spins"),
    }

    def test_new_stems_match(self):
        for stem, (vs, expected) in self.NEW_STEM_EXAMPLES.items():
            with self.subTest(kök=stem):
                self.assertIn(expected, _beat1_action_words(vs))
                self.assertTrue(validate_high_action(_scenario(vs))[0])

    def test_false_friends_rejected(self):
        for vs in self.FALSE_FRIEND_EXAMPLES:
            with self.subTest(vs=vs):
                self.assertEqual(_beat1_action_words(vs), [])
                self.assertFalse(validate_high_action(_scenario(vs))[0])

    def test_known_risk_rush_hour_and_night_shift(self):
        """BELGELENMİŞ RİSK: 'rush' ve 'shift' fiil olarak da geçtiği için false friend
        yapılamadı. Bu kalıplar bilerek eşleşir; test bu kabulü kanıt olarak tutar."""
        self.assertEqual(_beat1_action_words("Rush hour traffic on the coastal road."), ["rush"])
        self.assertEqual(_beat1_action_words("The night shift crew on the quay."), ["shift"])

    def test_n14_regression_fixtures(self):
        for n, (vs, expected) in self.N14_FIXTURES.items():
            with self.subTest(senaryo=n):
                self.assertIn(expected, _beat1_action_words(vs))
                self.assertTrue(validate_high_action(_scenario(vs))[0])


class TestSimplifierBeat3Fidelity(unittest.TestCase):
    """Simplifier kural 8: Beat 3 devam işaretini koru. Sabit metin: kuralın prompt'ta
    varlığı test edilir; GPT'nin uyumu ancak dry-run'da görülür."""

    RULE = "8. BEAT 3 CONTINUATION FIDELITY"

    def test_rule_present_in_all_domains(self):
        from core.creative_engine import MARITIME_INSPIRATION_DOMAINS, build_prompt_simplifier_system
        for d in MARITIME_INSPIRATION_DOMAINS:
            with self.subTest(domain=d):
                s = build_prompt_simplifier_system(15, d)
                self.assertIn(self.RULE, s)
                self.assertIn("ongoing action verb", s)
                self.assertNotIn("present continuous", s)

    def test_rule_follows_number_fidelity(self):
        from core.creative_engine import build_prompt_simplifier_system
        s = build_prompt_simplifier_system(15, "ferry_operations")
        self.assertLess(s.index("7. NUMBER FIDELITY"), s.index(self.RULE))

    def test_rule_numbering(self):
        """N14c sonrası: gemi domainleri 1-9, env-centric 1-10."""
        import re
        from core.creative_engine import ENV_CENTRIC_DOMAINS, build_prompt_simplifier_system
        self.assertEqual(re.findall(r"(?m)^(\d+)\. ", build_prompt_simplifier_system(15, "ferry_operations")),
                         [str(i) for i in range(1, 10)])
        for d in ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                s = build_prompt_simplifier_system(15, d)
                self.assertEqual(re.findall(r"(?m)^(\d+)\. ", s), [str(i) for i in range(1, 11)])
                self.assertIn("10. STRICT ENVIRONMENT-CENTRIC FOCUS", s)


class TestSimplifierBeat1SubjectFidelity(unittest.TestCase):
    """Simplifier kural 9: ilk cümle senaryonun öznesiyle başlar (seyirciyle değil)."""

    RULE = "9. BEAT 1 SUBJECT FIDELITY"

    def test_rule_present_in_all_domains(self):
        from core.creative_engine import MARITIME_INSPIRATION_DOMAINS, build_prompt_simplifier_system
        for d in MARITIME_INSPIRATION_DOMAINS:
            with self.subTest(domain=d):
                s = build_prompt_simplifier_system(15, d)
                self.assertIn(self.RULE, s)
                self.assertIn("BAD: 'Three workers watch in shock as water gushes'", s)

    def test_rule_order(self):
        from core.creative_engine import build_prompt_simplifier_system
        s = build_prompt_simplifier_system(15, "open_beach_coastal_events")
        self.assertLess(s.index("8. BEAT 3 CONTINUATION FIDELITY"), s.index(self.RULE))
        self.assertLess(s.index(self.RULE), s.index("10. STRICT ENVIRONMENT-CENTRIC FOCUS"))


class TestDeclaredBeat1Verb(unittest.TestCase):
    """Beat 1 ana yol: GPT'nin bildirdiği beat1_action_verb (N14c). Yedek: kelime listesi."""

    @staticmethod
    def _sc(visible_start: str, verb=None) -> dict:
        sc = {"visible_start": visible_start, **_ACTIVE_REST}
        if verb is not None:
            sc["beat1_action_verb"] = verb
        return sc

    def test_declared_verb_outside_list_passes(self):
        """'cascades' kelime listesinde yok: sadece ana yol geçirebilir."""
        vs = "Seawater cascades through the open hatch onto the car deck."
        self.assertEqual(_beat1_action_words(vs), [])
        self.assertTrue(_declared_beat1_verb_ok(self._sc(vs, "cascades")))
        self.assertTrue(validate_high_action(self._sc(vs, "cascades"))[0])

    def test_missing_verb_falls_back_to_list(self):
        self.assertTrue(validate_high_action(self._sc("A wave crashes over the bow."))[0])
        self.assertTrue(validate_high_action(self._sc("A wave crashes over the bow.", ""))[0])
        self.assertFalse(validate_high_action(self._sc("Seawater cascades through the hatch."))[0])

    def test_human_or_camera_verb_rejected(self):
        for vs, verb in [("Passengers react as seawater cascades onto the deck.", "react"),
                         ("The camera catches seawater cascading onto the deck.", "catches"),
                         ("Crew see seawater cascade over the rail.", "see"),
                         ("Workers watch seawater cascade over the rail.", "watch")]:
            with self.subTest(verb=verb):
                self.assertFalse(_declared_beat1_verb_ok(self._sc(vs, verb)))

    def test_verb_not_in_first_sentence_rejected(self):
        vs = "Three passengers sit by the pool. Seawater cascades over the rail."
        self.assertFalse(_declared_beat1_verb_ok(self._sc(vs, "cascades")))
        self.assertFalse(validate_high_action(self._sc(vs, "cascades"))[0])

    def test_verb_must_match_exactly(self):
        """Kök benzerliği yetmez: 'cascade' bildirilip metinde 'cascades' varsa ret."""
        self.assertFalse(_declared_beat1_verb_ok(self._sc("Seawater cascades over the rail.", "cascade")))

    def test_negated_verb_rejected(self):
        vs = "Seawater never cascades over the high rail of the ferry."
        self.assertFalse(_declared_beat1_verb_ok(self._sc(vs, "cascades")))
        self.assertFalse(validate_high_action(self._sc(vs, "cascades"))[0])

    def test_multiword_verb_rejected(self):
        self.assertFalse(_declared_beat1_verb_ok(self._sc("The ramp breaks loose.", "breaks loose")))

    def test_false_friend_declared_as_verb_rejected(self):
        """GPT bir ismi fiil diye bildirse bile (mock), bilinen durgun isimler geçmez."""
        vs = "A sailing yacht with its spinnaker set drifts past the pontoon."
        self.assertFalse(_declared_beat1_verb_ok(self._sc(vs, "spinnaker")))

    def test_blacklist_still_applies(self):
        vs = "Seawater cascades over the deck, clearly visible from the pier."
        self.assertTrue(_declared_beat1_verb_ok(self._sc(vs, "cascades")))
        self.assertFalse(validate_high_action(self._sc(vs, "cascades"))[0])

    def test_writer_schema_has_field(self):
        from core.creative_engine import build_scenario_writer_system
        for d in ["ferry_operations", "open_beach_coastal_events"]:
            with self.subTest(domain=d):
                self.assertIn('"beat1_action_verb"', build_scenario_writer_system(15, d))


class TestBackupStemsN14c(unittest.TestCase):
    """Yedek listeye son 3 kök: lift, scatter, erupt."""

    def test_new_stems_match(self):
        for vs, expected in [("A gust lifts beach umbrellas into the air.", "lifts"),
                             ("Debris scatters across the coastal road.", "scatters"),
                             ("Seawater erupts through the car deck hatch.", "erupts")]:
            with self.subTest(vs=vs):
                self.assertIn(expected, _beat1_action_words(vs))

    def test_false_friends_rejected(self):
        for vs in ["The liftgate of the car ferry.", "A boat lifter on the quay.",
                   "Scattered clouds over the marina.", "A scatterbrained tourist on the pier."]:
            with self.subTest(vs=vs):
                self.assertEqual(_beat1_action_words(vs), [])

    def test_known_risk_lift_nouns(self):
        """BELGELENMİŞ RİSK: 'lift'/'lifts' fiil olarak da geçtiği için false friend yapılamadı."""
        self.assertEqual(_beat1_action_words("A yard travel lift holds the yacht."), ["lift"])
        self.assertEqual(_beat1_action_words("Ski lifts above the beach."), ["lifts"])


class TestBeat1OpeningsRegression(unittest.TestCase):
    """6 dry-run'dan 30 gerçek visible_start (tests/fixtures/beat1_openings.json).
    Beklenen sonuçlar N14c anındaki kapı kararıdır; bildirilen fiil yok, yedek yol test edilir.
    2026-09-24 kamera öznesi kuralıyla bilinçli olarak True→False: beat1_out#3, n14_out#1, n14b_out#2."""

    def test_30_openings(self):
        import json
        path = os.path.join(os.path.dirname(__file__), "fixtures", "beat1_openings.json")
        rows = json.load(open(path, encoding="utf-8"))
        self.assertEqual(len(rows), 30)
        for tag, vs, expected in rows:
            with self.subTest(tag=tag):
                self.assertEqual(validate_high_action(_scenario(vs))[0], expected)


class TestBeat1CameraSubject(unittest.TestCase):
    """Beat 1 kamera/görüntü öznesiyle açılamaz (2026-09-24)."""

    REAL = [  # gerçek dry-run açılışları, hepsi eski kapıdan geçiyordu
        "The image captures a runaway powerboat's mooring line under extreme tension, straining against a cleat, with three marina staff in bright orange vests rushing toward the scene.",  # N14c #3
        "The camera catches the instant a powerful gust of wind lifts beach umbrellas into the air, scattering sand and debris.",  # N14b
        "A fixed camera shows four workers in orange coveralls, their attention is drawn urgently to the vessel as it begins to shift.",  # N14
        "BEAT 1: The fixed security camera shows an overcast sky with waves crashing violently against the beach, already encroaching on the coastal road.",  # beat1
    ]

    def assertCameraReject(self, vs, scenario=None):
        ok, failures = validate_high_action(scenario or _scenario(vs))
        self.assertFalse(ok)
        self.assertTrue(any("kamera öznesiyle açılış" in f for f in failures), failures)

    def test_real_openings_rejected(self):
        for vs in self.REAL:
            with self.subTest(vs=vs[:40]):
                self.assertCameraReject(vs)

    def test_declared_verb_does_not_bypass(self):
        vs = self.REAL[0]
        self.assertCameraReject(vs, {**_scenario(vs), "beat1_action_verb": "straining"})

    def test_other_variants_rejected(self):
        for vs in ("Footage from the pier camera shows a mooring line snapping.",
                   "The CCTV feed is showing a wave slamming the ferry ramp.",
                   "Security footage of the car deck captures cars sliding loose.",
                   "The shot captures a hull slamming into the pier.",
                   "The video opens on a wave crashing over the pool deck.",
                   "The scene shows cars sliding across the flooded deck.",
                   "We see a mooring line snap as the yacht lurches.",
                   "In the frame, a wave crashes over the bow."):
            with self.subTest(vs=vs):
                self.assertCameraReject(vs)

    def test_real_subjects_pass(self):
        for vs in ("The wave crashes over the deck as two deckhands grab the rail.",
                   "Waves crash onto the ramp as the camera captures the surge.",
                   "From the bow of the observer vessel, the catamaran lurches violently in the swell.",
                   "The frame of the gantry buckles and swings toward the dock.",
                   "The view deck railing snaps as a wave slams the ship.",
                   "Scenery flashes as the yacht slams into the pier."):
            with self.subTest(vs=vs):
                self.assertEqual(_static_start_hits(vs.lower()), [], vs)

    def test_writer_rule7_subject_sentence(self):
        from core.creative_engine import MARITIME_INSPIRATION_DOMAINS, build_scenario_writer_system
        for d in MARITIME_INSPIRATION_DOMAINS:
            with self.subTest(domain=d):
                self.assertIn("camera position and framing belong only in observer_camera",
                              build_scenario_writer_system(15, d))


class TestBeat3Gate(unittest.TestCase):
    """Beat 3 (visible_consequence) tehlike sürerken bitmeli (2026-09-24)."""

    # N10 dry-run gerçek Beat 3 sonları: #3 "steadying" ile sakinleşiyordu
    N10_CONSEQUENCES = {
        1: ("The gangway continues to flex alarmingly, with passengers clinging to the railings, some dropping to their knees to stabilize themselves as the gangway teeters with no immediate signs of stabilization.", True),
        2: ("As the observer vessel maintains pace nearby, the catamaran continues to list heavily, with crew members still trying to stabilize the vehicles, while the water relentlessly sloshes across the deck, clearly threatening further instability.", True),
        3: ("The vessel slides rapidly towards the water, its motion steadying but still visibly uncontrolled, with workers maintaining a cautious distance, watching intently.", False),
        4: ("Water floods the promenade, swirling around the base of palm trees and scattering beach chairs, with the wave still advancing forcefully inland.", True),
        5: ("The fallen debris shatters on the street, with pedestrians quickly darting to safety amidst the chaos, as more debris threatens to fall.", True),
    }

    @staticmethod
    def _ok(consequence: str) -> bool:
        return validate_beat3_ongoing_danger({"visible_consequence": consequence})[0]

    def test_n10_fixtures(self):
        for n, (vc, expected) in self.N10_CONSEQUENCES.items():
            with self.subTest(senaryo=n):
                self.assertEqual(self._ok(vc), expected)

    def test_n10_winner_hits_three_patterns(self):
        hits = _beat3_blacklist_hits(self.N10_CONSEQUENCES[3][0])
        self.assertEqual(set(hits), {"steady", "cautious distance", "watch in/intently"})

    def test_empty(self):
        self.assertFalse(self._ok(""))
        self.assertFalse(validate_beat3_ongoing_danger({})[0])

    def test_settle_disputes_rejected(self):
        """Bilinçli: Beat 3 fiziksel sahne, metafora yer yok."""
        self.assertFalse(self._ok("The crew argue as the officers try to settle disputes on deck."))

    def test_cruise_evacuation_passes(self):
        self.assertTrue(self._ok("Passengers continue evacuating amid the tilting deck."))

    def test_still_disambiguation(self):
        self.assertEqual(_beat3_ongoing_markers("Still water laps at the hull."), [])
        self.assertEqual(_beat3_ongoing_markers("Workers are still standing on the quay."), [])
        self.assertEqual(_beat3_ongoing_markers("The crew continue to watch the hull."), [])
        self.assertTrue(_beat3_ongoing_markers("The wave is still surging over the rail."))
        self.assertTrue(_beat3_ongoing_markers("The ferry is still visibly advancing on the pier."))
        self.assertTrue(_beat3_ongoing_markers("Chairs are still being swept inland."))
        self.assertTrue(_beat3_ongoing_markers("The car keeps sliding toward the ramp."))

    def test_static_only_ending_rejected(self):
        """Ne işaretçi ne aksiyon fiili: durgun son reddedilir."""
        self.assertFalse(self._ok("Workers are still standing on the quay, looking at the hull."))

    def test_negation_guard(self):
        for vc in ["The water shows no sign of stopping as it floods the deck.",
                   "The listing hull never settles as waves keep pounding it.",
                   "The harbor is far from calm, spray still bursting over the quay."]:
            with self.subTest(vc=vc):
                self.assertEqual(_beat3_blacklist_hits(vc), [])
                self.assertTrue(self._ok(vc))

    def test_resolution_endings_rejected(self):
        for vc in ["The car stops inches from the edge of the ramp.",
                   "The yacht comes to rest against the pontoon.",
                   "The runaway powerboat grinds to a halt on the sand.",
                   "The crew bring the ferry back under control.",
                   "The sea calms as the tornado moves away."]:
            with self.subTest(vc=vc):
                self.assertFalse(self._ok(vc))

    def test_safe_word_boundaries(self):
        for vc in ["Passengers dart to safety as the deck floods.",
                   "Crew clinging to safety lines as water surges over the rail.",
                   "Steadily rising water floods the vehicle deck."]:
            with self.subTest(vc=vc):
                self.assertEqual(_beat3_blacklist_hits(vc), [])
                self.assertTrue(self._ok(vc))

    def test_beat_label_stripped(self):
        self.assertTrue(self._ok("BEAT 3 (11-15s): the wave is still surging inland."))

    def test_score_bonus_ongoing(self):
        base = {"visible_start": "A wave crashes over the bow.", "physical_movement": "", "scenario_summary": ""}
        still = score_scenario({**base, "visible_consequence": "Water is still surging across the deck."})
        plain = score_scenario({**base, "visible_consequence": "Water is surging across the deck."})
        self.assertEqual(still - plain, 2)


class TestStyleLockVesselFraming(unittest.TestCase):

    CCTV_FRAMING = CAMERA_ARCHETYPES["fixed_cctv"]["vessel_framing"]
    HANDHELD_FRAMING = CAMERA_ARCHETYPES["bystander_handheld"]["vessel_framing"]

    def test_env_centric_with_yacht_has_no_framing(self):
        cat = {"domain_id": "coastal_tornado_landfall", "forced_ship": "Sailing Yacht"}
        self.assertNotIn(self.CCTV_FRAMING, apply_style_lock("X", "fixed_cctv", cat))
        self.assertNotIn(self.HANDHELD_FRAMING, apply_style_lock("X", "bystander_handheld", cat))

    def test_env_centric_without_ship_has_no_framing(self):
        for d in ["open_beach_coastal_events", "urban_city_disasters"]:
            with self.subTest(domain=d):
                out = apply_style_lock("X", "fixed_cctv", {"domain_id": d, "forced_ship": "None"})
                self.assertNotIn("hull, bow", out)

    def test_vessel_domain_has_framing(self):
        cat = {"domain_id": "cruise_ship_operations", "forced_ship": "Mega Cruise Ship"}
        self.assertIn(self.CCTV_FRAMING, apply_style_lock("X", "fixed_cctv", cat))
        self.assertIn(self.HANDHELD_FRAMING, apply_style_lock("X", "bystander_handheld", cat))

    def test_none_catalyst_keeps_framing(self):
        """Geriye uyumluluk: catalyst verilmezse kural eklenir."""
        self.assertIn(self.CCTV_FRAMING, apply_style_lock("X", "fixed_cctv"))
        self.assertIn(self.HANDHELD_FRAMING, apply_style_lock("X", "bystander_handheld", None))


if __name__ == "__main__":
    unittest.main()
