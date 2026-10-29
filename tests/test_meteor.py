#!/usr/bin/env python3
"""
☄️ Meteor kategorisi (29 Eki 2026, Bahadır; TASLAK): "Denize dev meteor düşer", yapılandırılmış hat. Kilit cümle, kadraj
(K1-K3), ortam (O1-O4), ışık Bahadır'ın metni birebir. 29 Eki (2) yeni kurgu: tek meteor, tek çarpma; şok dalgası + beyaz
buhar, ardından alçak, BEYAZ, köpüklü taşkın; tsunami yok; her temas kalıcı hasar. Kapılar kod tarafında (yasak kökler,
beyaz su, hasar fiili, nesne koruma). Ayrıca deniz kategorilerinin pasifliği ve helikopter kadrajı. Ağ yok, Kie/GPT yok.
"""
import asyncio
import os
import random
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import core.event_structure as es
import core.frame_axis as fx
import core.skeleton_pipeline as sk

MET = es.METEOR
DOMAIN = "meteor_disasters"
K1, K2, K3 = ("Rooftop terrace of a hillside villa above the bay", "High terrace of a seafront villa",
              "Hilltop terrace above a coastal town")   # 29 Eki (3): K2 villa terası
KEY = ("A blazing meteor tears across the sky trailing fire and smoke and slams into the sea just off the coast, "
       "erupting in a blinding flash and a towering column of water and steam.")
FRAMES = {K1: "Handheld footage from the rooftop terrace of a modern hillside villa, overlooking the bay and the "
              "seafront houses below",
          K2: "Handheld footage from the high terrace of a seafront villa, looking out over the promenade and the open "
              "sea",
          K3: "Handheld footage from a hilltop terrace above a coastal town, the whole bay and the rooftops below in "
              "view"}
TAIL = ("the impact point is visible offshore from the first second; slight hand shake, the camera stays fixed on the "
        "bay, never tilting down or descending; no zoom, no cuts")
RULE = ("Only one meteor and nothing else falls; the water stays white, foaming and steaming, never a brown tsunami "
        "wall; every hit leaves lasting damage.")
ENVS = {"O1": "white modern Mediterranean villas with glass railings and pools",
        "O2": "modern glass houses stepped down a green hillside",
        "O3": "a palm-lined coastal suburb of modern homes"}   # 29 Eki (3): O4 pasif (yüksek kuleler)
LIGHTS = ["golden sunset", "hazy midday light", "overcast grey sky"]
W_POOL = {"W1": "the shockwave hits the shore, snapping palm trees and ripping roof tiles off the villas",
          # 29 Eki (3), Bahadır: yeni metinler
          "W2": "a ring of white steam and spray races ashore and flips the cars on the seafront road",
          "W3": "the blast rips the sunbeds off the villa terraces and smashes them into the pools"}
X_POOL = {"X3": "white, foaming seawater bursts into the villa gardens right below, knocking over the garden walls",
          "X1": "the falling water column crashes onto the promenade as a white, foaming flood, smashing the beach kiosks",
          "X2": "a white, steaming surge floods the coastal road and shoves parked cars into the villa walls",
          "X4": "white surf bursts over the seawall and smashes the beach bars and loungers into the road"}
HELD = {}
OLD = {"M1", "M2", "M3", "M4", "M5", "M6", "N1", "N2", "N3", "N4", "N5", "N6"}
# aynı nesne: W2+X2 araba, W3+X4 şezlong; sığma: W2+X1 (29 Eki (3), Bahadır)
ALLOWED = {("W1", "X1"), ("W1", "X2"), ("W1", "X3"), ("W1", "X4"), ("W2", "X3"), ("W2", "X4"), ("W3", "X1"),
           ("W3", "X2"), ("W3", "X3")}
# Test videosundaki gerçek GPT çıktısı (29 Eki): ikisi de yeni kapılardan RET almalı
OLD_GPT_1 = "Burning fragments rain down, igniting rooftops as people race uphill in panic."
OLD_GPT_2 = "A fierce wind levels palm trees and scatters furniture across villa terraces."
SEA = ("ferry_operations", "shipyard_and_drydock_engineering", "marina_and_yacht_operations")
H = es.HELICOPTER


def cap(s):
    return s[0].upper() + s[1:]


def met_gpt(messages=None):
    """Ağsız sahte GPT: seçilen maddeleri birebir dilim yapar, insan cümlesi en kısa hâliyle (ücretli çağrı yok)."""
    async def gpt(system, user, **kw):
        if messages is not None:
            messages.append(user)
        line = dict(l.split(": ", 1) for l in user.splitlines()
                    if l.startswith(("4-9s EVENT", "9-15s EVENT", "PEOPLE RUNNING AWAY")))
        word = line["PEOPLE RUNNING AWAY"].split()[0]
        return {"slice_1_rest": f"{cap(word)} people run off right below.",
                "slice_2": cap(line["4-9s EVENT"]) + ".", "slice_3": cap(line["9-15s EVENT"]) + "."}
    return gpt


def frame_of(spot):
    return {"type": fx.native(MET, spot)[0], "pos_spot": spot, "fg": None, "mode": None}


def spec_of(b2="W1", b3="X2", spot=K2, env="O3", light="golden sunset", people=5):
    return es.build_spec(MET, None, spot, None, b2, b3, None, people, es.meteor_setting(env, light), None,
                         frame_of(spot))


def good_slices(b2="W1", b3="X2"):
    return {"slice_1_rest": "Five people run off right below.",
            "slice_2": cap(es.beat_text(MET, "slice_2", b2)) + ".", "slice_3": cap(es.beat_text(MET, "slice_3", b3)) + "."}


def rules(spec, sl):
    return {i["rule"] for i in es.slice_issues(spec, sl)}


def history_loader(scenes):
    """Önceki üretimlerin Notion "Eksenler" kaydı (eskiden yeniye): üretimdeki tekrar önleme yolu."""
    return lambda domain: [{"eksenler": s["axes_json"]} for s in scenes]


class TestMeteor(unittest.TestCase):
    def setUp(self):
        es._BEAT_MEMORY.clear()
        es._AXES_MEMORY.clear()

    def test_registrations_and_menu(self):
        import bot
        import core.caption as capm
        import core.creative_pipeline as cp
        from core.creative_engine import DOMAIN_ATTRIBUTES, ENV_CENTRIC_DOMAINS, MARITIME_INSPIRATION_DOMAINS
        self.assertEqual(bot.DOMAIN_LABELS[DOMAIN], "☄️ Meteor")
        self.assertEqual(bot.EVENT_LABELS[MET], "☄️ Denize dev meteor düşer")
        self.assertIn('meteor_disasters: "☄️ Meteor",', open(os.path.join(ROOT, "dashboard.html"), encoding="utf-8").read())
        self.assertEqual(sk.skeleton_events(DOMAIN), [MET])
        self.assertEqual(DOMAIN_ATTRIBUTES[DOMAIN]["environments"], [K1, K2, K3])
        self.assertEqual(DOMAIN_ATTRIBUTES[DOMAIN]["ships"], [])
        self.assertIn(DOMAIN, MARITIME_INSPIRATION_DOMAINS)
        self.assertIn(DOMAIN, ENV_CENTRIC_DOMAINS)
        self.assertIn(DOMAIN, sk.NO_SIGNS_DOMAINS)
        self.assertEqual(sk.PHENOMENA["Meteor"], [MET])
        self.assertTrue(es.is_structured(MET))
        self.assertEqual(cp.EVENT_REQUIRED[MET], [])
        self.assertEqual(sk.count_range(MET, None), (3, 6))
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[MET], (40, 75))
        self.assertFalse(es.uses_vehicle(MET))
        for group in (es.WORD_CAP_EVENTS, es.BUDGET_EVENTS, es.CAP_BUDGET_EVENTS, es.SETTING_EVENTS):
            self.assertIn(MET, group)
        self.assertNotIn(MET, es.ENV_EVENTS)
        self.assertEqual(capm.SHARE_CATEGORY[MET], "Meteor")
        self.assertEqual(capm.TAG_POOL[MET], "meteor")
        texts = [b.text for row in bot.domain_keyboard().inline_keyboard for b in row]
        self.assertIn("☄️ Meteor", texts)
        di = bot.DOMAIN_KEYS.index(DOMAIN)
        self.assertEqual(di, len(bot.DOMAIN_KEYS) - 1)
        labels = [b.text for row in bot.event_keyboard(di).inline_keyboard for b in row]
        self.assertEqual(labels[0], "☄️ Denize dev meteor düşer")
        self.assertEqual(len(labels), 3)
        self.assertEqual(bot.parse_selection(str(di), "0"), (DOMAIN, MET))

    def test_limits_only_meteor(self):
        # 29 Eki (2-3), Bahadır: sadece meteor 205 kelime / 11 kısıt; diğer olaylar 175 / 8 / 1400
        self.assertEqual(es.max_prompt_words(MET), 205)
        self.assertEqual(es.max_constraints(MET), 11)
        self.assertEqual(es.max_prompt_chars(MET), es.MAX_PROMPT_CHARS)
        for e in es.structured_events():
            if e != MET:
                self.assertEqual((es.max_prompt_words(e), es.max_constraints(e), es.max_prompt_chars(e)),
                                 (175, 8, 1400), e)

    def test_key_frames_envs_lights_locked(self):
        import core.creative_pipeline as cp
        self.assertEqual(es.EVENT_KEY_VISUAL[MET], KEY)
        found = {i["rule"] for i in cp.story_rule_issues(MET, None, KEY)}
        self.assertFalse(found & {"a_trigger_first", "b_no_camera_words", "e_event_and_ship_named"})
        self.assertEqual(list(sk.EVENT_SKELETONS[MET]["spots"]), [K1, K2, K3])
        self.assertEqual(sk.METEOR_CAMERA, FRAMES)
        self.assertEqual(sk.METEOR_RULE, RULE)
        self.assertEqual(es.METEOR_ENVS, ENVS)
        self.assertEqual(sk.EVENT_SKELETONS[MET]["weather"], LIGHTS)

    def test_pool_retired_and_held(self):
        b = es.EVENT_BEATS[MET]
        self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, W_POOL)
        self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, X_POOL)
        self.assertEqual(set(es.RETIRED_BEATS[MET]), OLD)
        self.assertEqual({k: v[0] for k, v in es.METEOR_HELD_BEATS.items()}, HELD)
        self.assertNotIn(MET, es.DISABLED_BEATS)
        self.assertFalse(hasattr(es, "METEOR_WAVE_ENABLED"))
        pool = set(b["slice_2"]) | set(b["slice_3"])
        self.assertEqual(set(es.METEOR_BEAT_SCORES), pool)
        for bid, scores in list(es.METEOR_BEAT_SCORES.items()) + [(k, v[1]) for k, v in es.METEOR_HELD_BEATS.items()]:
            self.assertEqual(len(scores), 6)
            self.assertGreaterEqual(min(scores), 3, bid)   # 29 Eki (2): hiçbiri puandan düşmedi
        self.assertEqual(b["excluded_pairs"], {("W2", "X2"), ("W3", "X4"), ("W2", "X1")})
        self.assertEqual(es.METEOR_RETIRED_ENVS, {"O4": "modern seafront apartment towers and low houses along a "
                                                        "promenade"})
        self.assertNotIn("O4", es.METEOR_ENVS)
        for spot in (K1, K2, K3):
            self.assertEqual(set(es.allowed_pairs(MET, None, spot)), ALLOWED)

    def test_camera_and_suffix(self):
        from core.trace_format import count_constraints
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import prompt_rules as pr
        for spot in (K1, K2, K3):
            for env in ENVS:
                for light in LIGHTS:
                    with self.subTest(spot=spot, env=env, light=light):
                        suffix = sk.style_suffix(MET, None, spot, None, es.meteor_setting(env, light), None,
                                                 frame_of(spot))
                        # 29 Eki (3): meteorda ön planda yüksek bina da yok
                        self.assertTrue(suffix.startswith(f"{FRAMES[spot]}; {TAIL}, no person, face or tall building "
                                                          f"close to the camera."))
                        self.assertTrue(suffix.endswith(RULE))
                        for part in (f"Setting: {ENVS[env]}, {light}.", sk.ENV_GUARDRAILS, sk.REAL_TIME,
                                     "No readable signs, text or flags."):
                            self.assertIn(part, suffix)
                        self.assertLessEqual(count_constraints(suffix)[0], 11)
                        self.assertEqual(pr.check(MET, {"style_suffix": suffix, "prompt": suffix, "axes": {}}), {})

    def test_other_events_keep_no_face(self):
        # 29 Eki (3): "tall building" sadece meteorda
        for e in es.structured_events():
            if e == MET:
                continue
            spot = next(iter(sk.EVENT_SKELETONS[e]["spots"]))
            view = es.structure_views(e)[0]
            spot = sk.view_spots(e, view)[0]
            self.assertNotIn("tall building", sk.style_suffix(e, None, spot, view), e)

    def test_frame_is_spot_no_borrowing(self):
        for spot in (K1, K2, K3):
            self.assertEqual(fx.all_frames(MET, spot, [K1, K2, K3]), [frame_of(spot)])

    def test_lint_rules(self):
        self.assertEqual(es.pool_lint_errors(), [])
        for slot in ("slice_2", "slice_3"):
            for bid, beat in es.EVENT_BEATS[MET][slot].items():
                with self.subTest(beat=bid):
                    t = beat["text"]
                    self.assertEqual(es.find_terms(es.METEOR_STATIC + es.METEOR_ONE_BANNED + es.METEOR_TSUNAMI_BANNED,
                                                   t), [])
                    self.assertTrue(es.find_terms(es.METEOR_DAMAGE, t))
                    self.assertTrue(es.find_terms(es.METEOR_CONTACT, t))
                    if es.find_terms(es.METEOR_WATER, t):
                        self.assertTrue(es.find_terms(es.METEOR_WHITE, t))
        # lint: yasak kök / hasarsız / kahverengi su maddesi havuza girerse açılış hatası
        for text, why in (("a towering wave of brown water rises up and smashes the villas", "yasak kök"),
                          ("the shockwave hits the shore and engulfs the palm trees and roof tiles", "hasar fiili"),
                          ("a second fireball snaps palm trees and roof tiles", "yasak kök")):
            bad = {**es.EVENT_BEATS[MET], "slice_2": {"W1": {**es.EVENT_BEATS[MET]["slice_2"]["W1"], "text": text}}}
            with self.subTest(text=text), patch.dict(es.EVENT_BEATS, {MET: bad}):
                self.assertIn(why, " ".join(es.pool_lint_errors()))

    def test_gpt_gates(self):
        spec = spec_of()
        self.assertEqual(es.slice_issues(spec, good_slices()), [])
        ok_paraphrase = {"slice_1_rest": "Six residents run off right below.",
                         "slice_2": "The shockwave slams into the shore, snapping the palm trees and tearing roof tiles "
                                    "off the villas.",
                         "slice_3": "A white, foaming surge floods the road and shoves the parked cars into the walls."}
        self.assertEqual(es.slice_issues(spec_of(people=6), ok_paraphrase), [])
        cases = [
            ("slice_1_rest", "Five people run off right below as debris falls.", "meteor_one_impact"),
            ("slice_2", "Another fireball streaks down, snapping palm trees and ripping roof tiles off.",
             "meteor_one_impact"),
            ("slice_3", "A towering brown tsunami wall rises up and shoves parked cars into the villa walls.",
             "meteor_no_tsunami"),
            ("slice_3", "A surge floods the coastal road and shoves parked cars into the villa walls.",
             "meteor_white_water"),
            ("slice_2", "The shockwave hits the shore and bends palm trees over the roof tiles of the villas.",
             "meteor_damage"),
            ("slice_3", "A white, steaming surge floods the coastal road and smashes everything in its path.",
             "meteor_objects"),
            ("slice_2", "The shockwave hits the shore, snapping palm trees along the waterfront.", "meteor_objects"),
            ("slice_1_rest", "Five people stand and watch right below.", "meteor_no_static"),
        ]
        for field, text, rule in cases:
            with self.subTest(text=text):
                self.assertIn(rule, rules(spec, {**good_slices(), field: text}))

    def test_old_gpt_sentences_rejected(self):
        """Test videosundaki gerçek GPT çıktısı (29 Eki) yeni kapılardan geçmez."""
        for b3 in ("X1", "X2", "X4"):
            spec = spec_of("W1", b3)
            for field in ("slice_1_rest", "slice_2", "slice_3"):
                with self.subTest(text=1, field=field):
                    self.assertIn("meteor_one_impact", rules(spec, {**good_slices("W1", b3), field: OLD_GPT_1}))
            # "levels" / "scatters" hasar fiili değil, kiremit/çatı yok ("furniture scatters" genellemesi)
            r = rules(spec, {**good_slices("W1", b3), "slice_2": OLD_GPT_2})
            self.assertIn("meteor_damage", r)
            self.assertIn("meteor_objects", r)
            r = rules(spec, {**good_slices("W1", b3), "slice_3": OLD_GPT_2})
            self.assertIn("meteor_damage", r)
            self.assertIn("meteor_objects", r)

    def test_fallback_texts_clean(self):
        for t in es.FALLBACK_PEOPLE[MET]:
            self.assertEqual(es.find_terms(es.METEOR_STATIC + es.METEOR_ONE_BANNED + es.METEOR_TSUNAMI_BANNED, t), [])

    def test_every_combination_fits_205(self):
        """29 Eki (3): 205 kelimede her kadraj × ortam × ışık × çift × kişi sayısında kod yedeği sığar ve son denetimden
        geçer (sığmayan 0; 3 × 3 × 3 × 9 × 4 = 972)."""
        for spot in (K1, K2, K3):
            for b2, b3 in ALLOWED:
                for env in ENVS:
                    for light in LIGHTS:
                        for people in (3, 4, 5, 6):
                            spec = spec_of(b2, b3, spot, env, light, people)
                            cands = es.fallback_candidates(spec)
                            self.assertTrue(cands, (spot, b2, b3, env, light, people))
                            for sl in cands:
                                prompt = es.assemble_prompt(spec, sl)
                                self.assertEqual(es.final_prompt_issues(spec, sl, prompt,
                                                                        es.assemble_story(spec, sl)), [])
                                self.assertLessEqual(len(prompt.split()), 205)

    def test_productions_pass_final_check(self):
        import core.creative_pipeline as cp
        scenes, msgs = [], []
        for _ in range(30):
            scene = asyncio.run(cp.build_creative_scene(DOMAIN, MET, [], [], met_gpt(msgs),
                                                        axes_loader=history_loader(scenes)))
            t, spec, sl = scene["trace"], scene["structure"]["spec"], scene["structure"]["slices"]
            self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
            self.assertIn((spec["beat_2"], spec["beat_3"]), ALLOWED)
            self.assertTrue(scene["prompt"].startswith(f"0-4s: {KEY} "))
            self.assertLessEqual(len(scene["prompt"].split()), 205)
            self.assertTrue(scene["prompt"].endswith(RULE))
            self.assertIn("WORD BUDGET:", msgs[-1])
            prev = [s["trace"]["axes"] for s in scenes[-2:]]
            self.assertNotIn(t["axes"]["spot"], [p["spot"] for p in prev])
            scenes.append(scene)


class TestSeaCategoriesPassive(unittest.TestCase):
    def test_flag_and_menu(self):
        import bot
        from core.creative_engine import DOMAIN_ATTRIBUTES
        self.assertFalse(sk.SEA_CATEGORIES_ACTIVE)
        self.assertEqual(sk.DISABLED_DOMAINS, set(SEA))
        texts = [b.text for row in bot.domain_keyboard().inline_keyboard for b in row]
        for label in ("⛴️ Feribot", "🏗️ Tersane", "⛵ Marina & Yat"):
            self.assertNotIn(label, texts)
        self.assertIn("🚢 Kruvaziyer", texts)
        for d in SEA:
            with self.subTest(domain=d):
                self.assertEqual(sk.skeleton_events(d), [])
                self.assertIsNone(bot.parse_selection(str(bot.DOMAIN_KEYS.index(d)), "0"))
                self.assertIsNone(bot.parse_selection(str(bot.DOMAIN_KEYS.index(d)), "r"))
                self.assertTrue(DOMAIN_ATTRIBUTES[d]["events"])
        self.assertTrue(sk.skeleton_events("cruise_ship_operations"))
        for _ in range(50):
            domain, event, _ = sk.choose_event_and_ship(None, None, [])
            self.assertNotIn(domain, SEA)

    def test_flag_reopens(self):
        import bot
        with patch.object(sk, "DISABLED_DOMAINS", set()):
            texts = [b.text for row in bot.domain_keyboard().inline_keyboard for b in row]
            for label in ("⛴️ Feribot", "🏗️ Tersane", "⛵ Marina & Yat"):
                self.assertIn(label, texts)
            for d in SEA:
                self.assertTrue(sk.skeleton_events(d))
                self.assertIsNotNone(bot.parse_selection(str(bot.DOMAIN_KEYS.index(d)), "0"))

    def test_button_numbers_unchanged(self):
        import bot
        self.assertEqual(bot.DOMAIN_KEYS[:12], ["ferry_operations", "shipyard_and_drydock_engineering",
                                                "marina_and_yacht_operations", "cruise_ship_operations",
                                                "coastal_tornado_landfall", "urban_city_disasters",
                                                "open_beach_coastal_events", "landslide_disasters", "fire_disasters",
                                                "volcano_disasters", "avalanche_disasters", "earthquake_disasters"])
        cruise = [b for row in bot.domain_keyboard().inline_keyboard for b in row if b.text == "🚢 Kruvaziyer"][0]
        self.assertEqual(cruise.callback_data, "uret:d:3")


class TestHelicopterFrame(unittest.TestCase):
    BANNED = ("eye level", "normal lens", "pans to follow", "follows the", "street level", "sidewalk")

    def test_every_frame_high_wide_close_no_foreground(self):
        spots = list(sk.EVENT_SKELETONS[H]["spots"])
        seen = set()
        for spot in spots:
            for f in fx.all_frames(H, spot, spots):
                with self.subTest(spot=spot, frame=f):
                    self.assertIn(f["type"], ("balkon", "çatı"))
                    self.assertIsNone(f["mode"])
                    self.assertIsNone(f["fg"])
                    low = sk.style_suffix(H, None, spot, None, None, None, f).split(" no cuts")[0].lower()
                    for w in self.BANNED:
                        self.assertNotIn(w, low)
                    self.assertTrue("rooftop terrace of a hillside house" in low or "high balcony of a hillside house"
                                    in low)
                    for w in ("high wide view", "the wall of flames", "the helicopter large and close in frame",
                              "never a distant dot", "the camera stays fixed", "empty foreground"):
                        self.assertIn(w, low)
                    seen.add(f["type"])
        self.assertEqual(seen, {"balkon", "çatı"})


if __name__ == "__main__":
    unittest.main()
