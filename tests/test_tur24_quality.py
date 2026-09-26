#!/usr/bin/env python3
"""
TUR 24 (2026-09-26): bugünkü 4 problemli video (Tersane, Marina, Kruvaziyer, Feribot-katamaran).
Görünür tetik, Beat 3 yasak kelimeleri, sahne fiziği, sahneye göre kısa stil eki, olay×ortam uyumu
ve LRU cezası, 45-60 kelimelik hikaye. Gerçek API yok.
"""
import asyncio
import os
import re
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.prompt_generator as pg
from core.creative_engine import (
    CAMERA_ARCHETYPES,
    DOMAIN_ATTRIBUTES,
    ENV_CENTRIC_DOMAINS,
    EVENT_ENV_COMPAT,
    MARITIME_INSPIRATION_DOMAINS,
    ONBOARD_ENVIRONMENTS,
    RECENT_PAIR_WINDOW,
    REPEATABLE_EVENTS,
    EVENT_SHIP_ONLY,
    SIDE_LAUNCH_ENV,
    get_creative_catalyst,
    style_lock_suffix,
)
from core.prompt_generator import (
    scenario_gate_results,
    validate_beat3_ongoing_danger,
    validate_scene_physics,
    validate_simplified_prompt,
    validate_visible_trigger,
)

SHIPYARD, MARINA, CRUISE, FERRY = ("shipyard_and_drydock_engineering", "marina_and_yacht_operations",
                                   "cruise_ship_operations", "ferry_operations")

# Bugün Kie'ye giden gerçek hikayeler (Notion, 2026-09-26)
TODAY_SHIPYARD = ("The high-speed catamaran lurches down the slipway, with four workers bracing along the sides. "
                  "Suddenly, it skews sideways from unexpected friction, tilting dangerously as beams creak and "
                  "workers struggle to stabilize the vessel")
TODAY_MARINA = ("A storm surge lifts floating docks, tilting them as five marina workers in orange vests shout "
                "warnings. The docks slam into a luxury motor yacht, which rocks violently, mooring lines "
                "straining as workers push against the docks")


def _letters(failures):
    return sorted({letter for f in failures for letter, prefix in pg.SIMPLIFIER_GATES.items() if f.startswith(prefix)})


def _all_suffixes():
    for d, a in DOMAIN_ATTRIBUTES.items():
        for env in a["environments"]:
            for ship in (a["ships"] or ["None"]):
                for cam in CAMERA_ARCHETYPES:
                    # TUR 27: side launch sadece feribot + CCTV/el kamerası ile seçilir
                    if env == SIDE_LAUNCH_ENV and (ship != "Passenger Car Ferry" or cam == "chase_pov"):
                        continue
                    cat = {"domain_id": d, "forced_ship": ship, "forced_environment": env}
                    yield d, env, ship, cam, style_lock_suffix(cam, cat)


class TestTodayVideosRejected(unittest.TestCase):
    def test_shipyard_story(self):
        ok, f = validate_simplified_prompt(TODAY_SHIPYARD, {}, SHIPYARD)
        self.assertFalse(ok)
        self.assertTrue({"A", "K", "M"} <= set(_letters(f)), f)   # stabilize, friction, 33 kelime

    def test_marina_story(self):
        ok, f = validate_simplified_prompt(TODAY_MARINA, {}, MARINA)
        self.assertIn("L", _letters(f), f)
        self.assertIn("workers push against the docks", " ".join(f))


class TestBeat3Words(unittest.TestCase):
    def ok(self, text):
        return validate_beat3_ongoing_danger({"visible_consequence": text})[0]

    def test_banned(self):
        for t in ["The hull tilts as workers struggle to stabilize the vessel.",
                  "The yacht swings wide before the skipper regains control of the helm.",
                  "The cars keep sliding until the deck steadies.",
                  "The water keeps surging, then settles.",
                  "The loungers slide and the deck calms."]:
            with self.subTest(t=t):
                self.assertFalse(self.ok(t))

    def test_negated_and_substring_allowed(self):
        self.assertTrue(self.ok("Water keeps surging across the deck, further destabilizing the cars."))
        self.assertTrue(self.ok("The hull keeps sliding, crew unable to stabilize it as it still slides."))

    def test_tail_must_move(self):
        self.assertFalse(self.ok("The ferry slams the quay hard and afterwards the four deckhands in orange "
                                 "coveralls gather near the bollard at the far end of the pier."))
        self.assertTrue(self.ok("The parted line is still whipping across the quay, coiled dangerously near the bollard."))
        # K1 dry-run: "moves" hareket sayılmıyordu
        self.assertTrue(self.ok("The tornado tears across the sand, the funnel clearly visible as it moves parallel to the waterline."))

    def test_civilians_count_as_people(self):
        from core.prompt_generator import validate_cast_size
        sc = {"visible_start": "A tornado crashes onto the promenade.",
              "physical_movement": "It hurls debris, sending civilians scrambling.", "visible_consequence": "Debris keeps flying."}
        self.assertTrue(validate_cast_size(sc, "coastal_tornado_landfall")[0])


GOOD_SCEN = {
    "scenario_summary": "A restraining cable snaps and the sailing yacht slides down the slipway into the water.",
    "visible_start": "A restraining cable snaps at the bollard as three workers in orange coveralls leap back.",
    "visible_trigger": "the restraining cable snaps",
    "physical_movement": "The sailing yacht lurches down the inclined rails, the launch cradle grinding.",
    "visible_consequence": "The hull keeps sliding into the water, spray still bursting from the bow.",
    "beat1_action_verb": "snaps",
}
SLIPWAY_CAT = {"domain_id": SHIPYARD, "forced_ship": "Sailing Yacht", "forced_environment": "Construction slipway"}


class TestVisibleTrigger(unittest.TestCase):
    def test_good_passes(self):
        self.assertEqual(validate_visible_trigger(GOOD_SCEN), (True, []))

    def test_missing(self):
        self.assertFalse(validate_visible_trigger({**GOOD_SCEN, "visible_trigger": ""})[0])

    def test_invisible_cause(self):
        for word in ["friction", "an unexpected force", "instability", "for no reason"]:
            with self.subTest(word=word):
                sc = {**GOOD_SCEN, "physical_movement": f"The sailing yacht skews sideways from {word}."}
                ok, f = validate_visible_trigger(sc)
                self.assertFalse(ok)
                self.assertIn("görünmez", f[0])

    def test_trigger_not_on_camera(self):
        sc = {**GOOD_SCEN, "visible_trigger": "a hydraulic valve bursts below deck"}
        self.assertFalse(validate_visible_trigger(sc)[0])

    def test_env_centric_phenomenon_is_trigger(self):
        sc = {"visible_start": "A tornado forms offshore and tears toward the promenade as two bystanders run.",
              "physical_movement": "The tornado rips umbrellas loose.", "visible_consequence": "Debris keeps flying.",
              "visible_trigger": "A tornado forms offshore"}
        self.assertTrue(validate_visible_trigger(sc, "coastal_tornado_landfall")[0])
        self.assertFalse(validate_visible_trigger(sc, SHIPYARD)[0])

    def test_trigger_needs_action(self):
        self.assertFalse(validate_visible_trigger({**GOOD_SCEN, "visible_trigger": "the restraining cable"})[0])
        self.assertTrue(validate_visible_trigger({**GOOD_SCEN, "visible_trigger": "the ship heels hard",
                                                  "physical_movement": "The ship heels hard to port."})[0])


class TestScenePhysics(unittest.TestCase):
    def test_hand_push_rejected(self):
        for t in ["Four workers push against the docks as they rise.",
                  "Two deckhands shove the yacht away from the pontoon.",
                  "Marina staff hold back the runaway powerboat."]:
            with self.subTest(t=t):
                self.assertFalse(validate_scene_physics({"physical_movement": t}, {"domain_id": MARINA})[0])

    def test_rail_and_hooks_allowed(self):
        for t in ["Three deckhands grab the yacht's rail as it lurches.",
                  "Marina staff fend off the drifting yacht with long boat hooks."]:
            with self.subTest(t=t):
                self.assertTrue(validate_scene_physics({"physical_movement": t}, {"domain_id": MARINA})[0])

    def test_ferry_driving(self):
        cat = {"domain_id": FERRY, "forced_environment": "Open vehicle deck"}
        for t in ["A car drives across the vehicle deck.", "Cars slide with headlights on.", "A driver drove off."]:
            with self.subTest(t=t):
                self.assertFalse(validate_scene_physics({"physical_movement": t}, cat)[0])
        for t in ["Driving rain lashes the parked cars as they skid sideways.",
                  "Two drivers scramble out as the cars slide."]:
            with self.subTest(t=t):
                self.assertTrue(validate_scene_physics({"physical_movement": t}, cat)[0])
        # Sürüş kuralı sadece feribot domain'inde
        self.assertTrue(validate_scene_physics({"physical_movement": "A car drives down the flooded street."},
                                               {"domain_id": "urban_city_disasters"})[0])

    def test_slipway_needs_water(self):
        dry = {**GOOD_SCEN, "visible_consequence": "The hull keeps sliding across flat concrete.",
               "scenario_summary": "A cable snaps on the slipway."}
        self.assertFalse(validate_scene_physics(dry, SLIPWAY_CAT)[0])
        self.assertTrue(validate_scene_physics(GOOD_SCEN, SLIPWAY_CAT)[0])

    def test_gate_results_include_new_gates(self):
        gates = scenario_gate_results(GOOD_SCEN, SLIPWAY_CAT)
        self.assertTrue({"trigger", "physics"} <= set(gates))


class TestSimplifierNewGates(unittest.TestCase):
    STORY = ("A restraining cable snaps at the bollard as three workers in orange coveralls leap back. The sailing "
             "yacht lurches down the inclined slipway rails, the launch cradle grinding and timber blocks splintering "
             "under the hull. The hull keeps sliding faster into the open water, spray still bursting from the bow "
             "as the snapped cable whips across the rails.")

    def test_good_passes(self):
        self.assertTrue(45 <= len(self.STORY.split()) <= 60)
        self.assertEqual(validate_simplified_prompt(self.STORY, GOOD_SCEN, SHIPYARD, "Sailing Yacht"), (True, []))

    def test_length(self):
        short = "A restraining cable snaps as three workers leap back. The sailing yacht keeps sliding into the water."
        self.assertIn("M", _letters(validate_simplified_prompt(short, GOOD_SCEN, SHIPYARD, "Sailing Yacht")[1]))
        long = self.STORY + " " + " ".join(["The spray keeps bursting."] * 6)
        self.assertIn("M", _letters(validate_simplified_prompt(long, GOOD_SCEN, SHIPYARD, "Sailing Yacht")[1]))

    def test_rewrite_skips_m_but_keeps_k_l(self):
        v = pg.make_story_validator({"scenario": GOOD_SCEN, "domain_id": SHIPYARD, "ship": "Sailing Yacht"})
        short = "A restraining cable snaps as three workers leap back. The sailing yacht keeps sliding into the water."
        self.assertEqual(_letters([m for m, _ in v(short)]), [])
        bad = self.STORY.replace("A restraining cable snaps", "Unexpected friction jolts the cradle and a cable snaps")
        self.assertIn("K", _letters([m for m, _ in v(bad)]))


class TestStyleSuffix(unittest.TestCase):
    def test_length(self):
        for d, env, ship, cam, s in _all_suffixes():
            with self.subTest(d=d, env=env, ship=ship, cam=cam):
                self.assertLessEqual(len(s.split()), 115)

    def test_handheld_no_hands(self):
        for d, env, ship, cam, s in _all_suffixes():
            if cam == "bystander_handheld":
                with self.subTest(d=d, env=env):
                    self.assertIn("no phone, hands or fingers in frame", s)
                    self.assertNotRegex(s, r"hint of|phone edge")

    def test_onboard_no_second_ship(self):
        for d, env, ship, cam, s in _all_suffixes():
            if d not in ENV_CENTRIC_DOMAINS and env in ONBOARD_ENVIRONMENTS and cam != "chase_pov":  # chase_pov burada seçilmez
                with self.subTest(d=d, env=env, cam=cam):
                    self.assertIn("no second ship on the horizon", s)
                    self.assertNotIn("stays fully in frame", s)
                    self.assertNotIn("by hand", s)

    def test_no_cross_domain_leak(self):
        for d, env, ship, cam, s in _all_suffixes():
            with self.subTest(d=d, env=env, cam=cam):
                if d != CRUISE:
                    self.assertNotRegex(s, r"(?i)swimwear|pool|cruise uniform")
                if d != FERRY:
                    self.assertNotRegex(s, r"(?i)driverless|car-deck")

    def test_slipway_and_ferry_physics(self):
        s = style_lock_suffix("fixed_cctv", SLIPWAY_CAT)
        self.assertIn("inclined slipway rails", s)
        self.assertIn("open water", s)
        self.assertIn("by hand", s)
        f = style_lock_suffix("fixed_cctv", {"domain_id": FERRY, "forced_ship": "High-speed Catamaran",
                                             "forced_environment": "Open vehicle deck"})
        # Gemi üstü çekim: gövdeler kadraja giremez, sadece tip söylenir; dış çekimde iki gövde görünür
        self.assertIn("Aboard a twin-hull catamaran.", f)
        self.assertNotIn("by hand", f)   # gemi üstü ortamda elle itme kuralı gitmez
        self.assertNotIn("two parallel hulls visible", f)
        self.assertIn("never drive", f)
        out = style_lock_suffix("bystander_handheld", {"domain_id": FERRY, "forced_ship": "High-speed Catamaran",
                                                       "forced_environment": "Ferry terminal ramp"})
        self.assertIn("Twin-hull catamaran, two parallel hulls visible.", out)
        ramp = style_lock_suffix("fixed_cctv", {"domain_id": FERRY, "forced_ship": "Passenger Car Ferry",
                                                "forced_environment": "Ferry terminal ramp"})
        self.assertNotIn("never drive", ramp)


class TestCatalyst(unittest.TestCase):
    def test_no_chase_pov_onboard(self):
        from core.creative_engine import choose_camera_archetype
        for env in ONBOARD_ENVIRONMENTS:
            for _ in range(80):
                self.assertNotEqual(choose_camera_archetype(CRUISE, env), "chase_pov")
        self.assertIn("chase_pov", {choose_camera_archetype(CRUISE, "Cruise terminal berth") for _ in range(200)})

    def test_no_catamaran_in_shipyard(self):
        self.assertNotIn("High-speed Catamaran", DOMAIN_ATTRIBUTES[SHIPYARD]["ships"])
        self.assertIn("High-speed Catamaran", DOMAIN_ATTRIBUTES[FERRY]["ships"])

    def test_no_abstract_event_names(self):
        rx = re.compile(r"(?i)friction|instability|stress|settling|wind-blown")
        for d, a in DOMAIN_ATTRIBUTES.items():
            for e in a["events"]:
                with self.subTest(event=e):
                    self.assertIsNone(rx.search(e))

    def test_event_env_compat_forced_domain(self):
        for d, table in EVENT_ENV_COMPAT.items():
            for _ in range(150):
                c = get_creative_catalyst(domain=d)
                with self.subTest(domain=d, event=c["forced_event"], env=c["forced_environment"]):
                    self.assertIn(c["forced_environment"], table[c["forced_event"]])

    def test_pair_penalty(self):
        """Aynı domain'in son 5 üretimindeki olay+ortam ikilisi, gemi/kamera farklı olsa da tekrar gelmez."""
        for d in (FERRY, CRUISE, SHIPYARD, MARINA):
            table = EVENT_ENV_COMPAT[d]
            # Tekrarı serbest olaylar (TUR 27, side launch) cezadan muaf: beklentiden çıkarılır
            pairs = [(e, v) for e, envs in table.items() for v in sorted(envs) if e not in REPEATABLE_EVENTS]
            recent = pairs[:min(RECENT_PAIR_WINDOW, len(pairs) - 1)]
            ship = DOMAIN_ATTRIBUTES[d]["ships"][0].lower()
            hist = [f"{d}|{ship}|{e.lower()}|{v.lower()}|fixed_cctv" for e, v in recent]
            for _ in range(60):
                c = get_creative_catalyst(recent_history=hist, domain=d)
                with self.subTest(domain=d):
                    self.assertNotIn((c["forced_event"], c["forced_environment"]), recent)
                    if c["forced_event"] in REPEATABLE_EVENTS:
                        self.assertIn(c["forced_ship"], EVENT_SHIP_ONLY[c["forced_event"]])

    def test_today_ferry_repeat_avoided(self):
        hist = ["ferry_operations|passenger car ferry|green wave breaks over the rail onto the vehicle deck|"
                "open vehicle deck|bystander_handheld"]
        for _ in range(60):
            c = get_creative_catalyst(recent_history=hist, domain=FERRY)
            self.assertNotEqual((c["forced_event"], c["forced_environment"]),
                                ("Green wave breaks over the rail onto the vehicle deck", "Open vehicle deck"))


class TestWriterAndSimplifierMessages(unittest.TestCase):
    def _writer_msg(self, cat):
        base = {"domain_title": "t", "guidance": "g", "example_elements": [], "camera_styles": []}
        mock = AsyncMock(return_value={})
        with patch.object(pg, "_call_gpt", mock):
            asyncio.run(pg._generate_scenario({**base, **cat}, "fixed_cctv"))
        return mock.call_args.args

    def test_writer_gets_physics_and_hull_visual(self):
        sys_msg, user = self._writer_msg({"domain_id": FERRY, "forced_ship": "High-speed Catamaran",
                                          "forced_event": "Lashing chain snaps and a parked car breaks loose",
                                          "forced_environment": "Open vehicle deck"})
        self.assertIn("High-speed Catamaran (twin-hull catamaran, two parallel hulls visible)", user)
        self.assertIn("SCENE PHYSICS (MANDATORY)", user)
        self.assertIn("never drive", user)
        self.assertIn('"visible_trigger"', sys_msg)
        self.assertIn("8. VISIBLE TRIGGER", sys_msg)
        self.assertIn("never end on people trying to stabilize", sys_msg)

    def test_env_centric_no_physics_line(self):
        _, user = self._writer_msg({"domain_id": "urban_city_disasters", "forced_ship": "None",
                                    "forced_event": "Flash flooding in city streets",
                                    "forced_environment": "Downtown city center"})
        self.assertNotIn("SCENE PHYSICS", user)

    def test_simplifier_message(self):
        mock = AsyncMock(return_value={"prompt": "x"})
        with patch.object(pg, "_call_gpt", mock):
            asyncio.run(pg._simplify_prompt(GOOD_SCEN, {"domain_id": SHIPYARD}))
        sys_msg, user = mock.call_args.args
        self.assertIn("VISIBLE TRIGGER: the restraining cable snaps", user)
        self.assertIn("45 to 60 words", user)
        self.assertNotIn("25", user.split("REQUIREMENTS")[1][:40])
        self.assertIn("12. LENGTH AND ENDING: 45 to 60 words", sys_msg)


if __name__ == "__main__":
    unittest.main()
