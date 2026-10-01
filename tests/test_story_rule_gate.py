#!/usr/bin/env python3
"""
Hikâye kural kapısı (30 Eyl): 6 sabit kural, olay anahtar grupları (EVENT_REQUIRED), iki kızak olayında yasak
liste (EVENT_FORBIDDEN), 3 deneme, 3'ünde de kalırsa Kie yok. KİLİT: bu dosyadaki tam içerik testleri ancak
Bahadır'ın açık onayıyla değiştirilir. Ağ çağrısı yok: GPT, Kie, Notion sahte.
"""
import asyncio
import inspect
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.creative_pipeline as cp
import core.prompt_generator as pg
import core.prompt_sanitizer as ps
import core.skeleton_pipeline as sk
import main
from config import settings
from core.trace_format import format_generation
from infrastructure.kie_client import KieClient

_GUARDS = []


def setUpModule():
    import openai
    for name in ("OpenAI", "AsyncOpenAI"):
        p = patch.object(openai, name, side_effect=AssertionError(f"Testte gerçek openai.{name} kuruldu"))
        p.start()
        _GUARDS.append(p)
    p = patch.object(pg, "_get_openai_client", side_effect=AssertionError("Testte gerçek GPT istemcisi istendi"))
    p.start()
    _GUARDS.append(p)


def tearDownModule():
    for p in _GUARDS:
        p.stop()


CABLE, KEEL = cp.SLIPWAY_EVENTS
FLOOD = "Flash flooding in city streets"
WAVE = "Rogue wave breaks over the rail onto the pool deck"
TIDAL = "Tidal wave surges over a coastal city street"
SIGNS = "Storm gust tears signs and scaffolding loose downtown"
MOORING = "Mooring line snaps in a storm gust"   # 1 Eki: çıkarıldı
RUNAWAY = "Yacht loses control and rams moored boats in the marina"   # 1 Eki: çıkarıldı
YACHT = "Luxury Motor Yacht"

GOLDEN = ("The restraining cable snaps with a crack and the luxury motor yacht heels over onto its side on the "
          "slipway as eight shipyard workers sprint clear. The hull topples into the water beside the quay, "
          "throwing up a huge white splash. Waves surge over the quay while the yacht keeps rolling hard from "
          "side to side.")
FORWARD = GOLDEN.replace("heels over onto its side on the slipway", "slides down the slipway") \
                .replace("topples into the water", "plunges into the water")
FLOOD_OK = ("A wall of brown floodwater surges down the flooded street and slams into a row of parked cars, "
            "lifting them off the road as six shoppers run for the steps. The torrent keeps rushing between the "
            "buildings, shoving cars sideways into each other while more water pours in from the side streets.")
WAVE_OK = ("A towering rogue wave breaks over the rail of the ocean cruise liner and crashes onto the open-air pool "
           "deck. Sun loungers skid across the soaked tiles as twelve passengers stagger toward the stairs. Seawater "
           "keeps pouring over the rail, still sweeping chairs and towels across the pool deck toward the far railing.")


def rules(event, ship, story, suffix=None):
    return {i["rule"] for i in cp.story_rule_issues(event, ship, story, suffix)}


class TestLocks(unittest.TestCase):
    """Gevşetmek/kaldırmak Bahadır'ın açık onayını gerektirir."""

    def test_six_fixed_rules(self):
        self.assertLessEqual(len(cp.STORY_RULES), 6)
        self.assertEqual(list(cp.STORY_RULES), ["a_trigger_first", "b_no_camera_words", "c_no_meta_or_waiting",
                                                "d_no_scale_reducers", "e_event_and_ship_named",
                                                "f_no_phone_in_style"])

    def test_each_rule_has_reason_and_source_comment(self):
        lines = inspect.getsource(cp).split("STORY_RULES = {", 1)[1].split("\n}", 1)[0].splitlines()
        for key in cp.STORY_RULES:
            with self.subTest(rule=key):
                i = next(n for n, l in enumerate(lines) if l.strip().startswith(f'"{key}"'))
                comment = []
                while i > 0 and lines[i - 1].strip().startswith("#"):
                    i -= 1
                    comment.insert(0, lines[i])
                text = " ".join(comment)
                self.assertIn("# Sebep:", text)
                self.assertIn("Kaynak:", text)

    def test_rule_word_lists_exact(self):
        self.assertEqual(cp.CAMERA_WORDS, ("camera", "video", "phone", "footage"))
        self.assertEqual(cp.META_PHRASES, ("as the video ends", "as the clip ends", "the scene ends", "tension builds",
                                           "tension mounts", "suspense", "anticipation", "about to", "moments before",
                                           "calm before", "holds its breath", "waiting", "waits"))
        self.assertEqual(cp.SCALE_REDUCERS, ("ankle-deep", "ripple", "harmless", "harmlessly", "gentle", "gently",
                                             "mild", "mildly", "trickle", "puddle", "drizzle", "floats", "futilely"))
        self.assertEqual(set(cp.SHIP_TYPE_WORDS), set(sk.SHIP_PHRASES))

    def test_system_prompt_untouched(self):
        # Kural kapısı sadece kodda; sistem prompt'u 5 kural olarak kalır
        self.assertEqual(cp.CREATIVE_SYSTEM.count("\n1. ") + cp.CREATIVE_SYSTEM.count("\n5. "), 2)
        self.assertNotIn("\n6. ", cp.CREATIVE_SYSTEM)
        for word in ("sideways", "slides", "EVENT_REQUIRED", "bow-first"):
            self.assertNotIn(word, cp.CREATIVE_SYSTEM)

    def test_required_covers_all_22_events_with_budget(self):
        self.assertEqual(set(cp.EVENT_REQUIRED), set(sk.EVENT_SKELETONS))
        self.assertEqual(len(cp.EVENT_REQUIRED), 21)
        for e, groups in cp.EVENT_REQUIRED.items():
            with self.subTest(event=e):
                self.assertTrue(1 <= len(groups) <= 3)
                self.assertTrue(all(g and all(isinstance(t, str) and t for t in g) for g in groups))

    def test_required_approved_exact(self):
        side = [("sideways", "on its side", "onto its side", "to one side")]
        self.assertEqual(cp.EVENT_REQUIRED[CABLE], side)
        self.assertEqual(cp.EVENT_REQUIRED[KEEL], side)
        self.assertEqual(cp.EVENT_REQUIRED[FLOOD], [("wall", "surge", "torrent", "wave", "rush"), ("car", "cars", "vehicle")])
        self.assertEqual(cp.EVENT_REQUIRED[WAVE], [("wave",), ("loungers", "chairs", "people", "passengers")])
        self.assertEqual(cp.EVENT_REQUIRED[TIDAL], [("wave", "surge", "torrent"), ("car", "cars", "vehicle")])
        self.assertEqual(set(cp.REQUIRED_APPROVED), {CABLE, KEEL, FLOOD, WAVE, TIDAL})

    def test_marina_removed_events_and_rule2(self):
        # 1 Eki: halat ve kontrolsüz yat iskelet hattından çıktı; ses açılışı yasağı 2. kuralda kalır
        for e in (MOORING, RUNAWAY):
            self.assertIn(e, sk.REMOVED_EVENTS)
            self.assertNotIn(e, cp.EVENT_OUTCOMES)
            self.assertNotIn(e, cp.EVENT_REQUIRED)
        self.assertIn("Show only what is visible, never sounds.",
                      cp.CREATIVE_SYSTEM.split("\n2. ", 1)[1].split("\n3. ", 1)[0])

    def test_forbidden_exact_and_only_slipway(self):
        self.assertEqual(set(cp.EVENT_FORBIDDEN), {CABLE, KEEL})
        self.assertEqual(cp.SLIPWAY_EVENTS, ("Restraining cable snaps during slipway launch",
                                             "Keel blocks collapse under the launching hull"))
        for e in cp.SLIPWAY_EVENTS:
            self.assertEqual(cp.EVENT_FORBIDDEN[e], (
                "slides down", "sliding", "slides", "lurch", "lurches", "surges forward", "hurtle", "hurtles",
                "races down", "plunges", "plunging", "dives", "nose", "bow-first",
                "careen", "careens", "careening", "plummet", "plummets", "plummeting", "slide", "slid",
                "down the slipway", "descent", "descend", "accelerate"))
            self.assertNotIn("dive", cp.EVENT_FORBIDDEN[e])
            self.assertNotIn("diving", cp.EVENT_FORBIDDEN[e])
        self.assertEqual(cp.FORBIDDEN_FEEDBACK_TR,
                         "yat ileri gitmez; olduğu yerde yana yatar, sonra yan tarafıyla suya düşer.")

    def test_three_attempts(self):
        self.assertEqual(cp.MAX_ATTEMPTS, 3)

    def test_diversity_gate_locked_and_separate(self):
        # Ayrı kategori: 6 sabit kurala sayılmaz; eşik Bahadır onayı olmadan gevşetilmez
        self.assertEqual(cp.DIVERSITY_THRESHOLD, 0.6)
        self.assertNotIn("diversity", cp.STORY_RULES)
        self.assertEqual(cp.RECENT_STORIES, 15)
        self.assertEqual(cp.DIVERSITY_FEEDBACK_TR,
                         "Bu hikâye son hikâyelere çok benziyor: farklı sahne, farklı ilk cümle yaz.")


class TestRules(unittest.TestCase):
    def test_good_stories_pass(self):
        self.assertEqual(cp.story_rule_issues(CABLE, YACHT, GOLDEN), [])
        self.assertEqual(cp.story_rule_issues(KEEL, YACHT, GOLDEN.replace(
            "The restraining cable snaps with a crack", "The keel blocks collapse with a crack")), [])
        self.assertEqual(cp.story_rule_issues(FLOOD, None, FLOOD_OK), [])
        self.assertEqual(cp.story_rule_issues(WAVE, "Ocean Cruise Liner", WAVE_OK), [])

    def test_a_trigger_in_first_sentence(self):
        late = ("Rain lashes the empty shipyard and eight workers in orange coveralls sprint along the quay beside "
                "the luxury motor yacht. " + GOLDEN)
        self.assertIn("a_trigger_first", rules(CABLE, YACHT, late))
        # yer kelimesi tetik sayılmaz: "pool deck" açılışı dalga değildir
        calm = "Passengers relax on the pool deck of the ocean cruise liner. " + WAVE_OK
        self.assertIn("a_trigger_first", rules(WAVE, "Ocean Cruise Liner", calm))

    def test_a_first_required_group_counts_as_trigger(self):
        # Bahadır onayı, 30 Eyl: kuru provada reddedilen iyi sel açılışı
        wall = ("A wall of brown water bursts from an alley, engulfing the commercial street. Shoppers scream and "
                "sprint for shop entrances as the floodwater crashes into parked cars, shoving them sideways. The "
                "torrent keeps rushing down the street while more water pours in from the side alleys.")
        self.assertNotIn("a_trigger_first", rules(FLOOD, None, wall))
        rain = "Heavy rain drums on the awnings of the commercial street. " + FLOOD_OK
        self.assertIn("a_trigger_first", rules(FLOOD, None, rain))

    def test_e_phrase_synonyms_for_tornado(self):
        land = "A monstrous tornado suddenly touches down in the coastal neighborhood, tearing roofs away."
        self.assertEqual(pg.event_fidelity_issues("Tornado making landfall", land), [])
        coast = "A swirling tornado churns across the water toward the shore, ripping sand into the air."
        self.assertEqual(pg.event_fidelity_issues("Tornado approaching coastline", coast), [])
        self.assertTrue(pg.event_fidelity_issues("Tornado making landfall", "A tornado spins far out at sea."))
        self.assertEqual(pg._EVENT_PHRASE_SYNONYMS, {r"\btouch(?:es|ed|ing)?\s+down\b": "land",
                                                     r"\bshores?\b": "coas",
                                                     r"\binland\b": "land",
                                                     r"\bashore\b": "land"})
        for text in ("The tornado surges inland, striking the coastal neighborhood.",
                     "The tornado roars ashore, tearing roofs off the houses."):
            self.assertEqual(pg.event_fidelity_issues("Tornado making landfall", text), [], text)

    def test_to_one_side_counts_for_slipway(self):
        keel = ("With a resounding snap, the keel blocks collapse beneath the sailing yacht on the slipway. The vessel "
                "heaves abruptly, tilting to one side as workers shout and dash for safety. It teeters further, then "
                "crashes into the adjacent water with an enormous splash, rolling forcefully side to side.")
        self.assertNotIn("required", rules(KEEL, "Sailing Yacht", keel))
        self.assertEqual(cp.story_rule_issues(KEEL, "Sailing Yacht", keel), [])

    def test_b_camera_words(self):
        for w in ("camera", "video", "phone", "footage", "phones"):
            with self.subTest(word=w):
                self.assertIn("b_no_camera_words", rules(FLOOD, None, FLOOD_OK + f" A {w} shakes."))

    def test_c_meta_and_waiting(self):
        self.assertIn("c_no_meta_or_waiting", rules(FLOOD, None, FLOOD_OK.replace("The torrent", "Tension builds; the torrent")))
        self.assertIn("c_no_meta_or_waiting", rules(FLOOD, None, FLOOD_OK + " It is still going as the clip ends."))

    def test_d_scale_reducers(self):
        for w in ("ankle-deep", "ripples", "harmlessly", "gently", "floats"):
            with self.subTest(word=w):
                self.assertIn("d_no_scale_reducers", rules(FLOOD, None, FLOOD_OK.replace("lifting", f"{w} lifting")))

    def test_e_event_and_ship(self):
        self.assertIn("e_event_and_ship_named", rules(CABLE, YACHT, GOLDEN.replace("luxury motor yacht", "vessel")
                                                      .replace("the yacht keeps", "it keeps")))
        self.assertNotIn("e_event_and_ship_named", rules(WAVE, "Mega Cruise Ship", WAVE_OK.replace(
            "ocean cruise liner", "mega cruise ship")))

    def test_f_phone_in_style_suffix(self):
        self.assertIn("f_no_phone_in_style", rules(CABLE, YACHT, GOLDEN, "Handheld phone footage."))
        suffix = sk.style_suffix(CABLE, YACHT, "Construction slipway")
        self.assertNotIn("phone", suffix.lower())
        self.assertNotIn("f_no_phone_in_style", rules(CABLE, YACHT, GOLDEN, suffix))

    def test_required_groups(self):
        no_side = GOLDEN.replace("heels over onto its side", "tilts hard")
        self.assertIn("required", rules(CABLE, YACHT, no_side))
        self.assertIn("required", rules(FLOOD, None, FLOOD_OK.replace("parked cars", "kiosks")
                                        .replace("shoving cars", "shoving stalls")))
        self.assertIn("required", rules(WAVE, "Ocean Cruise Liner", WAVE_OK.replace("passengers", "crew")
                                        .replace("loungers", "tables").replace("chairs", "towels")))

    def test_term_inflections(self):
        self.assertEqual(cp.find_terms(("surge",), "water surging in"), ["surge"])
        self.assertEqual(cp.find_terms(("car",), "two cars"), ["car"])
        self.assertEqual(cp.find_terms(("car",), "cargo and a careful driver"), [])
        self.assertEqual(cp.find_terms(("lurch",), "it lurched"), ["lurch"])
        self.assertEqual(cp.find_terms(("nose",), "a nose-first drop"), ["nose"])
        self.assertEqual(cp.find_terms(("on its side",), "rolls on  its side"), [])   # tam ifade
        self.assertEqual(cp.find_terms(("slam",), "slammed"), ["slam"])

    def test_forbidden_only_on_slipway(self):
        issues = cp.story_rule_issues(CABLE, YACHT, FORWARD)
        bad = [i for i in issues if i["rule"] == "forbidden"]
        self.assertEqual(len(bad), 1)
        self.assertIn("slides", bad[0]["missing"])
        self.assertIn("plunges", bad[0]["missing"])
        self.assertIn(cp.FORBIDDEN_FEEDBACK_TR, bad[0]["missing"])
        self.assertIn("does not move forward", bad[0]["feedback"])
        for w in ("lurches", "hurtles", "dives", "bow-first", "surges forward", "races down", "sliding",
                  "careening down", "plummets", "slid", "slide", "moves down the slipway", "descends",
                  "is descending", "accelerates", "accelerating"):
            with self.subTest(word=w):
                self.assertIn("forbidden", rules(KEEL, YACHT, GOLDEN + f" It {w}."))
        self.assertNotIn("forbidden", rules(KEEL, YACHT, GOLDEN + " Two workers are diving clear."))
        # 30 Eyl hedefli provada kapıdan geçen hikâye artık reddedilir
        passed_before = ("The restraining cable snaps with a loud crack as the luxury motor yacht begins its descent "
                         "down the slipway. Crew members scatter, shouting warnings, as the vessel accelerates "
                         "uncontrollably. The yacht heaves violently to one side, crashing into the water with an "
                         "explosive splash, rolling back and forth in the strong wind.")
        bad = [i for i in cp.story_rule_issues(CABLE, YACHT, passed_before) if i["rule"] == "forbidden"][0]
        for w in ("down the slipway", "descent", "accelerate"):
            self.assertIn(w, bad["missing"])
        crane = "Crane sling snaps while lowering the hull into the water"
        self.assertEqual(cp.EVENT_FORBIDDEN.get(crane), None)
        self.assertNotIn("forbidden", rules(crane, YACHT, "The crane sling snaps and the yacht plunges nose-first."))


class TestAttempts(unittest.TestCase):
    def test_feedback_reaches_gpt_and_third_try_passes(self):
        gpt = AsyncMock(side_effect=[{"story": FORWARD}, {"story": FORWARD}, {"story": GOLDEN}])
        story, attempts = asyncio.run(cp.write_story(CABLE, YACHT, "x", "y", [], gpt))
        self.assertEqual(story, GOLDEN)
        self.assertEqual(gpt.await_count, 3)
        self.assertIn("does not move forward", gpt.await_args_list[1].args[1])
        self.assertEqual([bool(a["missing"]) for a in attempts], [True, True, False])

    def test_diversity_rejects_near_copy_and_counts_as_attempt(self):
        near = GOLDEN.replace("eight shipyard workers", "nine shipyard workers")
        self.assertGreaterEqual(cp.jaccard(near, GOLDEN), 0.6)
        self.assertEqual(cp.diversity_issues(GOLDEN, [WAVE_OK, FLOOD_OK]), [])
        self.assertEqual(len(cp.diversity_issues(near, [WAVE_OK, GOLDEN])), 1)
        other = ("A sharp metallic crack rings out as the restraining cable parts under heavy rain. The luxury motor "
                 "yacht heels over to one side while six welders sprint along the quay. Its hull slams sideways into "
                 "the harbor, throwing a wall of spray, and keeps rocking violently from side to side.")
        self.assertLess(cp.jaccard(other, GOLDEN), 0.6)
        gpt = AsyncMock(side_effect=[{"story": near}, {"story": other}])
        story, attempts = asyncio.run(cp.write_story(CABLE, YACHT, "x", "y", [GOLDEN], gpt))
        self.assertEqual(story, other)
        self.assertEqual(len(attempts), 2)   # benzer hikâye bir deneme sayıldı
        self.assertIn("çeşitlilik", attempts[0]["missing"][0])
        self.assertIn(cp.DIVERSITY_FEEDBACK_TR, attempts[0]["missing"][0])
        self.assertIn("too similar to the recent stories", gpt.await_args_list[1].args[1])
        # sınır: tam eşikte reddedilir
        with patch.object(cp, "jaccard", return_value=0.6):
            self.assertEqual(len(cp.diversity_issues("x", ["y"])), 1)
        with patch.object(cp, "jaccard", return_value=0.59):
            self.assertEqual(cp.diversity_issues("x", ["y"]), [])

    def test_three_failures_no_kie_and_clear_error(self):
        gpt = AsyncMock(return_value={"story": FORWARD})
        with self.assertRaises(cp.CreativeStoryError) as ctx:
            asyncio.run(cp.write_story(CABLE, YACHT, "x", "y", [], gpt))
        err = ctx.exception
        self.assertIsInstance(err, pg.NoValidScenarioError)
        summary = err.short_summary()
        self.assertIn("3 denemede", summary)
        for n in (1, 2, 3):
            self.assertIn(f"Deneme {n} · ❌ eksik: ", summary)
        self.assertIn("yasak kelime: slides", summary)

    def test_detail_message_format(self):
        trace = {"pipeline": "creative", "attempts": [
            {"attempt": 1, "story": FORWARD, "words": 50, "issues": ["x"], "missing": ["anahtar grup: sideways"]},
            {"attempt": 2, "story": GOLDEN, "words": 52, "issues": [], "missing": []}]}
        text = "\n".join(t + "\n" + b for t, b in format_generation(trace))
        self.assertIn("Deneme 1 · ❌ eksik: anahtar grup: sideways", text)
        self.assertIn("Deneme 2 · ✅ geçti", text)


def _fake_gpt(story):
    async def call(system, user, temperature=0.85, model="gpt-4o"):
        if system == cp.CREATIVE_SYSTEM:
            return {"story": story}
        return {"youtube_title": "⚠️ Test #Shorts", "youtube_description": "d", "tags": ["x"]}
    return AsyncMock(side_effect=call)


class TestPipeline(unittest.TestCase):
    def run_pipeline(self, story, preflight=None):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        tracker = MagicMock()
        tracker.page_id = None
        tracker.get_recent_history.return_value = []
        tracker.get_recent_beat1_verbs.return_value = []
        create = AsyncMock(return_value="t1")
        preflight = preflight or (lambda s: (s, False, {"risk_score": 1}))
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "PROMPT_PIPELINE", "creative"), \
             patch.object(settings, "ARCHIVE_DIR", d), patch.object(settings, "POLL_INITIAL_WAIT", 0), \
             patch.object(pg, "_call_gpt", _fake_gpt(story)), \
             patch.object(main, "load_used_combos", return_value=[]), patch.object(main, "NotionTracker", return_value=tracker), \
             patch.object(ps, "gpt_preflight_check", AsyncMock(side_effect=preflight)), \
             patch.object(KieClient, "_create_task", create), \
             patch.object(KieClient, "_poll_for_result", AsyncMock(return_value="https://cdn/v.mp4")), \
             patch.object(KieClient, "get_credit", AsyncMock(return_value=None)), \
             patch.object(main, "download_video", side_effect=RuntimeError("indirme yok")), \
             patch.object(main, "upload_to_youtube", AsyncMock()):
            r = asyncio.run(main.run_pipeline(skip_upload=True, mode="TEST", domain="shipyard_and_drydock_engineering",
                                              event=CABLE, trigger="manual"))
        return r, create

    def test_three_failures_never_reach_kie(self):
        r, create = self.run_pipeline(FORWARD)
        self.assertFalse(r["success"])
        self.assertEqual(r["reason"], "no_valid_scenario")
        self.assertIn("Deneme 3 · ❌ eksik", r["error_summary"])
        create.assert_not_awaited()

    def test_preflight_rewrite_rechecked_before_kie(self):
        r, create = self.run_pipeline(GOLDEN, lambda s: (s.replace("heels over onto its side", "slides down"),
                                                         True, {"risk_score": 5}))
        self.assertFalse(r["success"])
        self.assertIn("kural kapısı", r["error"])
        create.assert_not_awaited()



class TestCityEventSwap(unittest.TestCase):
    """30 Eyl: tabela/iskele çıktı (aksiyonsuz video), kıyı şehrinde dev dalga baskını girdi (24 Eyl videosu)."""

    def test_event_sets_equal(self):
        self.assertEqual(set(cp.EVENT_OUTCOMES), set(sk.EVENT_SKELETONS))
        self.assertEqual(set(cp.EVENT_REQUIRED), set(sk.EVENT_SKELETONS))
        self.assertEqual(len(sk.EVENT_SKELETONS), 21)
        self.assertIn(TIDAL, sk.EVENT_SKELETONS)
        self.assertNotIn(SIGNS, sk.EVENT_SKELETONS)
        self.assertIn(SIGNS, sk.REMOVED_EVENTS)   # kod silinmedi: havuzda, iskelet dışında

    def test_menu(self):
        import bot
        with patch.object(settings, "PROMPT_PIPELINE", "creative"):
            city = bot.domain_events("urban_city_disasters")
        self.assertEqual(city, ["Flash flooding in city streets", TIDAL])
        self.assertEqual(bot.EVENT_LABELS[TIDAL], "🌊 Kıyı şehrinde dev dalga baskını")

    def test_tidal_wave_data(self):
        s = sk.EVENT_SKELETONS[TIDAL]
        self.assertEqual(s["domain"], "urban_city_disasters")
        self.assertIsNone(s["ships"])
        self.assertEqual(sk.count_range(TIDAL, None), (2, 10))
        self.assertEqual(set(s["spots"]), {"Coastal road below a seafront promenade", "Coastal street of low shopfronts",
                                            "Coastal avenue behind a seawall"})
        self.assertIn("promenade", sk.CAMERA_SPOTS["Coastal road below a seafront promenade"])
        self.assertIn("second-floor balcony", sk.CAMERA_SPOTS["Coastal street of low shopfronts"])
        self.assertIn("seawall", sk.CAMERA_SPOTS["Coastal avenue behind a seawall"])
        self.assertTrue({"a dark storm light", "stormy late-afternoon light"} & set(s["weather"]))
        self.assertEqual(cp.EVENT_OUTCOMES[TIDAL], "a towering tidal wave crashes over the coastal road, sweeps parked "
                                                   "cars into storefronts and keeps surging down the street")
        for spot in s["spots"]:
            self.assertNotIn("phone", sk.style_suffix(TIDAL, None, spot).lower())

    def test_tidal_story_passes_rules(self):
        story = ("A towering tidal wave crashes over the seawall onto the coastal road, slamming into a row of parked "
                 "cars. The water sweeps the cars into the storefronts as six pedestrians sprint up the stairs to the "
                 "promenade. The wave keeps surging down the street, still dragging cars and debris inland.")
        self.assertEqual(cp.story_rule_issues(TIDAL, None, story), [])
        self.assertIn("required", rules(TIDAL, None, story.replace("parked cars", "benches")
                                        .replace("sweeps the cars", "sweeps the benches")
                                        .replace("dragging cars", "dragging benches")))

if __name__ == "__main__":
    unittest.main()
