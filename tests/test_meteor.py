#!/usr/bin/env python3
"""
☄️ Meteor kategorisi (29 Eki 2026, Bahadır; TASLAK): "Denize dev meteor düşer", yapılandırılmış hat. Kilit cümle, kadraj
(K1-K3), ortam (O1-O4), ışık, 4-9s / 9-15s havuzları Bahadır'ın metni birebir. Ek kural: 6 ölçütte 3'ün altındaki madde
havuzda yok, durağan fiil yok (lint + GPT kapısı), her beat'te büyük temas. [DALGA] maddeleri bayrakla kapalı. Ayrıca
deniz kategorilerinin pasifliği ve helikopter kadrajı. Ağ yok, Kie/GPT çağrısı yok.
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
K1, K2, K3 = ("Rooftop terrace of a hillside villa above the bay", "High balcony of a seafront apartment",
              "Hilltop terrace above a coastal town")
KEY = ("A blazing meteor tears across the sky trailing fire and smoke and slams into the sea just off the coast, "
       "erupting in a blinding flash and a towering column of water and steam.")
FRAMES = {K1: "Handheld footage from the rooftop terrace of a modern hillside villa, overlooking the bay and the "
              "seafront houses below",
          K2: "Handheld footage from a high balcony of a seafront apartment, looking out over the promenade and the "
              "open sea",
          K3: "Handheld footage from a hilltop terrace above a coastal town, the whole bay and the rooftops below in "
              "view"}
TAIL = ("the impact point is visible offshore from the first second; slight hand shake, the camera stays fixed, never "
        "descending; no zoom, no cuts")
ENVS = {"O1": "white modern Mediterranean villas with glass railings and pools",
        "O2": "modern glass houses stepped down a green hillside",
        "O3": "a palm-lined coastal suburb of modern homes",
        "O4": "modern seafront apartment towers and low houses along a promenade"}
LIGHTS = ["golden sunset", "hazy midday light", "overcast grey sky"]
M_POOL = {"M1": "a blast of wind hits the waterfront, bending palm trees flat and blowing loungers and umbrellas off "
                "the villa terraces",
          "M2": "burning chunks of rock crash down across the hillside, smashing into roofs and setting a parked car "
                "on fire",
          "M6": "the blast rolls over the bay and hurls parked cars and palm trees across the coastal road"}
N_POOL = {"N1": "a towering wave rises from the impact and races toward the coast, crashing over the seawall into the "
                "first row of modern houses",
          "N2": "the wave sweeps cars off the coastal road and drives them into the villa gardens",
          "N3": "flaming debris sets the roofs of the hillside houses ablaze while people sprint up the street",
          "N6": "the shockwave tears roof tiles and solar panels off the houses and sends them flying over the street"}
ALLOWED = {("M1", "N3"), ("M6", "N3"), ("M6", "N6")}   # dalga kapalı, sığma ve anlam dışlamalarından sonra
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


def spec_of(b2, b3, spot=K1, env="O1", light="golden sunset", people=5):
    return es.build_spec(MET, None, spot, None, b2, b3, None, people, es.meteor_setting(env, light), None,
                         frame_of(spot))


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
        # Notion Paylaşımlar "Kategori" seçeneği (kod tarafı; select seçeneği ilk yazımda oluşur)
        self.assertEqual(capm.SHARE_CATEGORY[MET], "Meteor")
        self.assertEqual(capm.TAG_POOL[MET], "meteor")
        # Telegram: Meteor düğmesi menüde, altında tek olay + 🎲 Rastgele / 🔙 Geri; callback 64 bayt altında
        texts = [b.text for row in bot.domain_keyboard().inline_keyboard for b in row]
        self.assertIn("☄️ Meteor", texts)
        di = bot.DOMAIN_KEYS.index(DOMAIN)
        self.assertEqual(di, len(bot.DOMAIN_KEYS) - 1)   # sona eklendi: eski butonların numarası değişmedi
        labels = [b.text for row in bot.event_keyboard(di).inline_keyboard for b in row]
        self.assertEqual(labels[0], "☄️ Denize dev meteor düşer")
        self.assertIn("🎲 Rastgele", labels)
        self.assertEqual(len(labels), 3)
        self.assertEqual(bot.parse_selection(str(di), "0"), (DOMAIN, MET))

    def test_key_frames_envs_lights_locked(self):
        import core.creative_pipeline as cp
        self.assertEqual(es.EVENT_KEY_VISUAL[MET], KEY)
        found = {i["rule"] for i in cp.story_rule_issues(MET, None, KEY)}
        self.assertFalse(found & {"a_trigger_first", "b_no_camera_words", "e_event_and_ship_named"})
        self.assertEqual(list(sk.EVENT_SKELETONS[MET]["spots"]), [K1, K2, K3])
        self.assertEqual(sk.METEOR_CAMERA, FRAMES)
        self.assertEqual(es.METEOR_ENVS, ENVS)
        self.assertEqual(sk.EVENT_SKELETONS[MET]["weather"], LIGHTS)
        b = es.EVENT_BEATS[MET]
        self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, M_POOL)
        self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, N_POOL)

    def test_camera_high_fixed_and_suffix(self):
        from core.trace_format import count_constraints
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import prompt_rules as pr
        for spot in (K1, K2, K3):
            for env in ENVS:
                for light in LIGHTS:
                    with self.subTest(spot=spot, env=env, light=light):
                        suffix = sk.style_suffix(MET, None, spot, None, es.meteor_setting(env, light), None,
                                                 frame_of(spot))
                        self.assertTrue(suffix.startswith(f"{FRAMES[spot]}; {TAIL}, {sk.NO_FACE}."))
                        self.assertIn(f"Setting: {ENVS[env]}, {light}.", suffix)
                        self.assertIn(sk.ENV_GUARDRAILS, suffix)
                        self.assertIn(sk.REAL_TIME, suffix)
                        self.assertIn("No readable signs, text or flags.", suffix)
                        self.assertLessEqual(count_constraints(suffix)[0], 8)
                        self.assertEqual(pr.check(MET, {"style_suffix": suffix, "prompt": suffix, "axes": {}}), {})
                        self.assertLessEqual(len(es.meteor_setting(env, light).split()), es.SETTING_MAX_WORDS)

    def test_frame_is_spot_no_borrowing(self):
        for spot in (K1, K2, K3):
            frames = fx.all_frames(MET, spot, [K1, K2, K3])
            self.assertEqual(frames, [frame_of(spot)])
            frame, _ = fx.choose_frame(MET, spot, [spot], set(), [], random.Random(1))
            self.assertEqual(frame, frame_of(spot))

    def test_scores_and_held_beats(self):
        b = es.EVENT_BEATS[MET]
        pool = set(b["slice_2"]) | set(b["slice_3"])
        self.assertEqual(set(es.METEOR_BEAT_SCORES), pool)
        for bid, scores in es.METEOR_BEAT_SCORES.items():
            self.assertEqual(len(scores), 6)
            self.assertGreaterEqual(min(scores), 3, bid)
        self.assertEqual(set(es.METEOR_HELD_BEATS), {"M3", "M4", "M5", "N4", "N5"})
        for bid, (text, scores, why) in es.METEOR_HELD_BEATS.items():
            self.assertLess(min(scores), 3, bid)
            self.assertNotIn(bid, pool)
            self.assertTrue(why)

    def test_wave_flag_closed(self):
        self.assertFalse(es.METEOR_WAVE_ENABLED)
        self.assertEqual(es.DISABLED_BEATS[MET], {"N1", "N2"})
        for spot in (K1, K2, K3):
            pairs = set(es.allowed_pairs(MET, None, spot))
            self.assertEqual(pairs, ALLOWED)
            for v, d in pairs:
                self.assertNotIn(d, {"N1", "N2"})
                self.assertNotEqual(v, "M3")
        # bayrak açılınca dalga maddeleri (sığanlar) seçilebilir; N1 hiç sığmıyor
        with patch.dict(es.DISABLED_BEATS, {MET: set()}):
            opened = set(es.allowed_pairs(MET, None, K1))
            self.assertEqual(opened - ALLOWED, {("M1", "N2"), ("M2", "N2"), ("M6", "N2")})

    def test_static_words_lint_and_gate(self):
        for slot in ("slice_2", "slice_3"):
            for bid, beat in es.EVENT_BEATS[MET][slot].items():
                with self.subTest(beat=bid):
                    self.assertEqual(es.find_terms(es.METEOR_STATIC, beat["text"]), [])
                    self.assertTrue(es.find_terms(es.METEOR_CONTACT, beat["text"]))
        self.assertEqual(es.pool_lint_errors(), [])
        # lint: durağan fiilli ya da temassız madde havuza girerse açılış hatası
        bad = {**es.EVENT_BEATS[MET], "slice_2": {**es.EVENT_BEATS[MET]["slice_2"],
                                                  "M1": {**es.EVENT_BEATS[MET]["slice_2"]["M1"],
                                                         "text": "smoke billows slowly over the calm bay"}}}
        with patch.dict(es.EVENT_BEATS, {MET: bad}):
            errs = " ".join(es.pool_lint_errors())
            self.assertIn("durağan fiil", errs)
            self.assertIn("teması yok", errs)
        # GPT kapısı: durağan fiil reddedilir
        spec = spec_of("M6", "N3")
        for words in ("Five people stand and watch right below.", "Five people stare from right below.",
                      "Smoke drifts as five people run off right below.", "Five people run off gently right below."):
            sl = {"slice_1_rest": words, "slice_2": cap(M_POOL["M6"]) + ".", "slice_3": cap(N_POOL["N3"]) + "."}
            with self.subTest(text=words):
                self.assertIn("meteor_no_static", {i["rule"] for i in es.slice_issues(spec, sl)})
        ok = {"slice_1_rest": "Five people run off right below.", "slice_2": cap(M_POOL["M6"]) + ".",
              "slice_3": cap(N_POOL["N3"]) + "."}
        self.assertNotIn("meteor_no_static", {i["rule"] for i in es.slice_issues(spec, ok)})

    def test_every_allowed_pair_fallback_passes_final_check(self):
        for spot in (K1, K2, K3):
            for b2, b3 in sorted(ALLOWED):
                for people in (3, 6):
                    with self.subTest(spot=spot, pair=(b2, b3), people=people):
                        fitting = []
                        for env in ENVS:
                            for light in LIGHTS:
                                spec = spec_of(b2, b3, spot, env, light, people)
                                for sl in es.fallback_candidates(spec):
                                    prompt = es.assemble_prompt(spec, sl)
                                    self.assertEqual(es.final_prompt_issues(spec, sl, prompt,
                                                                            es.assemble_story(spec, sl)), [])
                                    self.assertLessEqual(len(prompt.split()), 175)
                                    fitting.append((env, light))
                        self.assertTrue(fitting)   # sığma koruması her çiftte en az bir ortam/ışık bulur

    def test_100_productions_axes_rotate(self):
        import core.creative_pipeline as cp
        scenes, msgs = [], []
        for _ in range(100):
            scene = asyncio.run(cp.build_creative_scene(DOMAIN, MET, [], [], met_gpt(msgs),
                                                        axes_loader=history_loader(scenes)))
            t, spec, sl = scene["trace"], scene["structure"]["spec"], scene["structure"]["slices"]
            self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
            self.assertIn((spec["beat_2"], spec["beat_3"]), ALLOWED)
            self.assertTrue(scene["prompt"].startswith(f"0-4s: {KEY} "))
            self.assertLessEqual(len(scene["prompt"].split()), 175)
            self.assertIsNone(t["vehicle"])
            self.assertIn("WORD BUDGET:", msgs[-1])
            self.assertIn("in the street right below, in the lower half of the frame", msgs[-1])
            ax = t["axes"]
            self.assertEqual(ax["kadraj"], fx.native(MET, ax["spot"])[0])
            self.assertIn(f"Setting: {ENVS[ax['env']]}, {ax['light']}.", scene["prompt"])
            self.assertIn(f"PLACE: {ENVS[ax['env']]}", msgs[-1])
            prev = [s["trace"]["axes"] for s in scenes[-2:]]
            for axis in ("spot", "light"):   # 3 seçenek: son 2 tekrar etmez
                self.assertNotIn(ax[axis], [p[axis] for p in prev], axis)
            if not (t.get("axes_excluded") or {}).get("ortam_sığmadı"):
                self.assertNotIn(ax["env"], [p["env"] for p in prev])
            gpt_text = " ".join(sl.values())
            self.assertEqual(es.find_terms(es.METEOR_STATIC, gpt_text), [])
            scenes.append(scene)
        self.assertEqual({s["trace"]["axes"]["spot"] for s in scenes}, {K1, K2, K3})
        self.assertEqual({s["trace"]["axes"]["env"] for s in scenes}, set(ENVS))
        self.assertEqual({s["trace"]["axes"]["beats"] for s in scenes}, {f"{a}+{b}" for a, b in ALLOWED})

    def test_fit_guard_changes_env_only_when_needed(self):
        import core.creative_pipeline as cp
        # en uzun ortam + öğle ışığı + en uzun çift: kod yedeği sığmaz, sığan ortam/ışık seçilir
        spec = spec_of("M1", "N3", K1, "O4", "hazy midday light", 6)
        self.assertEqual(es.fallback_candidates(spec), [])
        with patch.object(es, "choose_beats", lambda *a, **k: ("M1", "N3")), \
                patch.object(es, "choose_meteor_env", lambda *a, **k: "O4"), \
                patch.object(cp, "pick_setting", lambda *a, **k: (K1, "hazy midday light")):
            scene = asyncio.run(cp.build_creative_scene(DOMAIN, MET, [], [], met_gpt()))
        t = scene["trace"]
        self.assertEqual(t["axes_excluded"]["ortam_sığmadı"], ["O4/hazy midday light"])
        self.assertTrue(es.fallback_candidates(scene["structure"]["spec"]))
        self.assertIn(f"Setting: {ENVS[t['axes']['env']]}, {t['axes']['light']}.", scene["prompt"])

    def test_six_samples_clean(self):
        """Ek kural 5: 6 örnek promptun hiçbirinde [DALGA] beat'i, M3 ya da durağan fiil yok."""
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import prompt_snapshot as ps
        for seed in range(1, 7):
            item = ps.snapshot_event(MET, seed)
            with self.subTest(seed=seed):
                self.assertNotIn("error", item)
                b2, b3 = item["axes"]["beats"].split("+")
                self.assertNotIn(b2, {"M3", "M4", "M5"})
                self.assertNotIn(b3, {"N1", "N2", "N4", "N5"})
                story = item["prompt"].split(" Handheld footage")[0]
                self.assertEqual(es.find_terms(es.METEOR_STATIC, story), [])
                self.assertLessEqual(len(item["prompt"].split()), 175)


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
                self.assertTrue(DOMAIN_ATTRIBUTES[d]["events"])   # havuz yerinde
        self.assertTrue(sk.skeleton_events("cruise_ship_operations"))
        # rastgele kategori seçimi pasif kategoriye düşmez
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
                    cam = sk.style_suffix(H, None, spot, None, None, None, f).split(" no cuts")[0]
                    low = cam.lower()
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
