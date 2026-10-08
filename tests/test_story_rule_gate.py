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
import core.event_structure as es
from test_event_structure import slices_from_message
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
                                             "mild", "mildly", "trickle", "puddle", "drizzle", "floats", "futilely",
                                             "futility", "bob"))
        self.assertEqual(set(cp.SHIP_TYPE_WORDS), set(sk.SHIP_PHRASES))

    def test_system_prompt_untouched(self):
        # Kural kapısı sadece kodda; sistem prompt'u 5 kural olarak kalır
        self.assertEqual(cp.CREATIVE_SYSTEM.count("\n1. ") + cp.CREATIVE_SYSTEM.count("\n5. "), 2)
        self.assertNotIn("\n6. ", cp.CREATIVE_SYSTEM)
        for word in ("sideways", "slides", "EVENT_REQUIRED", "bow-first"):
            self.assertNotIn(word, cp.CREATIVE_SYSTEM)

    def test_required_covers_all_22_events_with_budget(self):
        self.assertEqual(set(cp.EVENT_REQUIRED), set(sk.EVENT_SKELETONS))
        self.assertEqual(len(cp.EVENT_REQUIRED), 27)   # 2 Eki: + 3 heyelan; 8 Eki: + 3 yangın
        for e, groups in cp.EVENT_REQUIRED.items():
            with self.subTest(event=e):
                # yapılandırılmış olaylarda grup yok (olay terimleri event_structure'da)
                self.assertTrue(len(groups) == 0 if es.is_structured(e) else 1 <= len(groups) <= 3)
                self.assertTrue(all(g and all(isinstance(t, str) and t for t in g) for g in groups))

    def test_required_approved_exact(self):
        side = [("sideways", "on its side", "onto its side", "to one side")]
        self.assertEqual(cp.EVENT_REQUIRED[CABLE], side)
        self.assertEqual(cp.EVENT_REQUIRED[KEEL], side)
        # 4 Eki, Bahadır onayı: sel yapılandırılmış hatta, terimler seçilen olaydan (core/event_structure.py)
        self.assertEqual(cp.EVENT_REQUIRED[FLOOD], [])
        self.assertEqual(cp.EVENT_REQUIRED[WAVE], [("wave",), ("loungers", "chairs", "people", "passengers")])
        # 4 Eki, Bahadır onayı: kıyı dev dalga da yapılandırılmış hatta (core/event_structure.py)
        self.assertEqual(cp.EVENT_REQUIRED[TIDAL], [])
        self.assertEqual(set(cp.REQUIRED_APPROVED), {CABLE, KEEL, FLOOD, WAVE, TIDAL,
                                                     # 2 Eki: heyelan onaylandı
                                                     "Mudslide pours down a hillside street", "Rain-soaked slope collapses onto a roadside",
                                                     "Mud and debris torrent tears through a hillside village"})

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
        # Bahadır onayı, 30 Eyl: olayın ilk anahtar grubu tetik sayılır. Sel ve heyelan artık grupsuz (4 Eki);
        # mekanizma kızak olayıyla denenir: "sideways" olay kökü değil, ilk grupta.
        first = "The luxury motor yacht heels over sideways on the slipway as the workers sprint clear. "
        rest = ("Five residents run uphill as the flow shoves the cars sideways. More mud keeps rushing down the "
                "street, still dragging cars and debris along with it.")
        self.assertNotIn("a_trigger_first", rules(CABLE, YACHT, first + rest))
        self.assertIn("a_trigger_first", rules(CABLE, YACHT, "Heavy rain drums on the slipway. " + first + rest))
        # Grupsuz sel: kural çökmez; kilit görsel tek başına tetiği taşır
        self.assertNotIn("a_trigger_first", rules(FLOOD, None, es.EVENT_KEY_VISUAL[FLOOD] + " " + rest))
        self.assertIn("a_trigger_first", rules(FLOOD, None, "Heavy rain drums on the commercial street. " + FLOOD_OK))

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
        self.assertNotIn("required", rules(FLOOD, None, FLOOD_OK.replace("parked cars", "kiosks")
                                           .replace("shoving cars", "shoving stalls")))   # 4 Eki: grupsuz
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
        self.assertEqual(len(sk.EVENT_SKELETONS), 27)   # 2 Eki: + 3 heyelan; 8 Eki: + 3 yangın
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
        self.assertEqual(sk.count_range(TIDAL, None), (3, 6))   # 4 Eki, Bahadır: olaya özel, küçük belirli sayı
        self.assertEqual(set(s["spots"]), {"Coastal road below a seafront promenade", "Coastal street of low shopfronts",
                                            "Coastal avenue behind a seawall"})
        self.assertIn("promenade", sk.CAMERA_SPOTS["Coastal road below a seafront promenade"])
        self.assertIn("second-floor balcony", sk.CAMERA_SPOTS["Coastal street of low shopfronts"])
        self.assertIn("seawall", sk.CAMERA_SPOTS["Coastal avenue behind a seawall"])
        self.assertTrue({"a dark storm light", "stormy late-afternoon light"} & set(s["weather"]))
        self.assertEqual(cp.EVENT_OUTCOMES[TIDAL], "a towering brown churning tidal wave thick with debris crashes over "
                                                   "the coastal road, sweeps parked cars into storefronts and keeps "
                                                   "surging down the street")
        for spot in s["spots"]:
            self.assertNotIn("phone", sk.style_suffix(TIDAL, None, spot).lower())

    def test_tidal_story_passes_rules(self):
        story = ("A towering tidal wave crashes over the seawall onto the coastal road, slamming into a row of parked "
                 "cars. The water sweeps the cars into the storefronts as six pedestrians sprint up the stairs to the "
                 "promenade. The wave keeps surging down the street, still dragging cars and debris inland.")
        self.assertEqual(cp.story_rule_issues(TIDAL, None, story), [])
        # 4 Eki: anahtar gruplar kalktı (yapılandırılmış hat); olay terimleri seçilen 4-9s / 9-15s olayından gelir
        self.assertNotIn("required", rules(TIDAL, None, story.replace("parked cars", "benches")
                                           .replace("sweeps the cars", "sweeps the benches")
                                           .replace("dragging cars", "dragging benches")))


class TestRegionViews(unittest.TestCase):
    """1 Eki, Bahadır: aynı ortamda tekrar eden şehir videoları. Görünüm listesi kilitli."""
    PLACES = ("uae", "dubai", "qatar", "doha", "morocco", "tunisia", "africa", "america", "usa", "florida",
              "carolina", "europe", "netherlands", "dutch", "england", "british", "uk", "london", "france", "french",
              "italy", "italian", "riviera", "nice", "monaco", "japan", "japanese", "tokyo", "taiwan", "asia",
              "asian", "gulf", "arab", "flag", "sign", "text", "logo")

    def setUp(self):
        sk._VIEW_MEMORY.clear()   # süreç hafızası testler arasında taşınmasın

    def tearDown(self):
        sk._VIEW_MEMORY.clear()

    def _city_combo(self, view, event=FLOOD):
        return f"urban_city_disasters|none|{event.lower()}|downtown city center#{view}|{sk.SKELETON_CAMERA}"

    def test_views_locked(self):
        self.assertEqual(sk.REGION_VIEW_EVENTS, (FLOOD, TIDAL))
        self.assertEqual(sk.REGION_VIEWS, {
            "gulf_metropolis": "glass towers behind palm-lined multi-lane boulevards, sand-colored low buildings, "
                               "white SUVs",
            "north_african_coast": "sand-colored flat-roofed buildings, narrow streets, cloth awnings, small hatchback "
                                   "cars",
            "us_coastal_town": "wide asphalt roads, pickup trucks, low wooden and brick houses, overhead power lines",
            "north_european_seaside": "brick terraced houses, narrow streets, small parked cars",
            "riviera": "cream stone buildings with shuttered windows, cobbled streets, scooters, plane trees",
            "east_asian_coast": "dense mid-rise apartment blocks with air-conditioner units and tangled overhead "
                                "wires, narrow lanes, small boxy cars and scooters"})
        self.assertEqual(sk.REGION_VIEW_CLOTHING, "people in light everyday clothes suited to the climate")
        self.assertEqual(sk.NO_SIGNS, "no readable signs, text or flags")

    def test_lru_never_repeats_last_view(self):
        history = [self._city_combo(v) for v in ("riviera", "gulf_metropolis", "us_coastal_town", "east_asian_coast",
                                                  "north_african_coast", "north_european_seaside")]
        self.assertEqual(sk.choose_region_view(FLOOD, history), "riviera")        # en eskisi
        for _ in range(20):
            v = sk.choose_region_view(FLOOD, [self._city_combo("riviera")])
            self.assertNotEqual(v, "riviera")
        # Olay başına ayrı döngü: selin geçmişi kıyı dalgayı etkilemez, kıyı dalga kendi geçmişine bakar
        tidal = [self._city_combo(v, TIDAL) for v in ("gulf_metropolis", "riviera", "us_coastal_town",
                                                     "east_asian_coast", "north_african_coast",
                                                     "north_european_seaside")]
        self.assertEqual(sk.choose_region_view(TIDAL, history + tidal), "gulf_metropolis")
        self.assertEqual(sk.choose_region_view(FLOOD, history + tidal), "riviera")
        self.assertIn(sk.choose_region_view(TIDAL, history), sk.REGION_VIEWS)   # kendi geçmişi yok: herhangi biri
        for _ in range(20):
            self.assertNotEqual(sk.choose_region_view(TIDAL, [self._city_combo("riviera", TIDAL),
                                                              self._city_combo("gulf_metropolis")]), "riviera")
        self.assertIsNone(sk.choose_region_view(WAVE, history))                   # şehir dışı olay: görünüm yok
        self.assertEqual(sk.view_of_combo(self._city_combo("riviera")), "riviera")
        self.assertIsNone(sk.view_of_combo(f"urban_city_disasters|none|x|downtown city center|{sk.SKELETON_CAMERA}"))

    def test_spot_view_compat_and_tidal_on_coast(self):
        self.assertEqual(sk.view_spots(FLOOD, "gulf_metropolis"), list(sk.EVENT_SKELETONS[FLOOD]["spots"]))
        self.assertNotIn("High-rise city district", sk.view_spots(FLOOD, "us_coastal_town"))
        self.assertNotIn("Coastal street of low shopfronts", sk.view_spots(TIDAL, "east_asian_coast"))
        for e in sk.REGION_VIEW_EVENTS:
            for v in sk.REGION_VIEWS:
                self.assertTrue(sk.view_spots(e, v), (e, v))
                self.assertIn("seafront district" if e == TIDAL else "city district", sk.view_district(e, v))

    def test_no_place_names_and_no_signs_in_prompt(self):
        import re
        from core.trace_format import count_constraints
        for e in sk.REGION_VIEW_EVENTS:
            for v in sk.REGION_VIEWS:
                for spot in sk.view_spots(e, v):
                    place = sk.view_place(e, sk.EVENT_SKELETONS[e]["spots"][spot], v)
                    suffix = sk.style_suffix(e, None, spot, v)
                    self.assertIn("Setting: ", suffix)
                    self.assertTrue(suffix.endswith(", no readable signs, text or flags."))
                    self.assertLessEqual(count_constraints(suffix)[0], 8)
                    self.assertNotIn("phone", suffix.lower())
                    for text in (place, suffix.split("Setting: ", 1)[1].replace("no readable signs, text or flags", "")):
                        words = set(re.findall(r"[a-z]+", text.lower()))
                        self.assertFalse(words & set(self.PLACES), (v, words & set(self.PLACES)))
        self.assertNotIn("Setting:", sk.style_suffix(WAVE, "Ocean Cruise Liner", "Open-air pool deck"))

    def test_scene_carries_view(self):
        async def gpt(system, user, **kw):
            gpt.user = user
            return {"slice_1_rest": "It swallows the curbs and pours between the parked cars.",
                    "slice_2": f"The {gpt.vehicle} is caught by the current, turns sideways and is dragged down the street.",
                    "slice_3": "A lamppost topples into the current and crashes into the churning brown water."}
        history = [self._city_combo("riviera")]
        es._BEAT_MEMORY.clear()

        def vehicle(view, rng=None):
            gpt.vehicle = es.REGION_VEHICLES[view][0][0]
            return gpt.vehicle
        with patch.object(es, "choose_beats", lambda *a, **k: ("V1", "D2")), patch.object(es, "choose_vehicle", vehicle):
            scene = asyncio.run(cp.build_creative_scene("urban_city_disasters", FLOOD, history, [], gpt))
        view = scene["trace"]["view"]
        self.assertIn(view, sk.REGION_VIEWS)
        self.assertNotEqual(view, "riviera")
        self.assertIn(f"#{view}#V1+D2|", scene["combo_key"])
        self.assertEqual(sk.view_of_combo(scene["combo_key"]), view)
        self.assertTrue(sk.is_current_universe_combo(scene["combo_key"]))   # 5 parça korunur, tarihçeye girer
        self.assertIn(sk.REGION_VIEWS[view], gpt.user)
        self.assertIn(sk.REGION_VIEWS[view], scene["style_suffix"])
        self.assertIn(scene["spot"], sk.view_spots(FLOOD, view))
        detail = "\n".join(body for _, body in format_generation(scene["trace"]))
        self.assertIn(f"Görünüm: {view}", detail)
        self.assertNotIn("Görünüm:", "\n".join(body for _, body in format_generation(
            {**scene["trace"], "view": None})))


    def test_back_to_back_runs_do_not_repeat_view(self):
        # 1 Eki 15:34 ve 15:45: TEST modunda biten ilk üretim Notion geçmişine girmedi (durum sayılmıyor), ikinci
        # üretim aynı görünümü aldı. İkinci üretim ilkini beklemeden de başlayabilir: geçmiş iki seferde de aynı.
        async def gpt(system, user, **kw):
            return slices_from_message(user)   # 4 Eki: kıyı dev dalga yapılandırılmış hatta
        notion_history = []   # ilk üretim Notion'dan sayılmıyor
        seen = []
        for _ in range(6):
            scene = asyncio.run(cp.build_creative_scene("urban_city_disasters", TIDAL, notion_history, [], gpt))
            seen.append(scene["trace"]["view"])
        self.assertEqual(len(set(seen)), 6, seen)   # 6 üretimde 6 farklı görünüm, art arda tekrar yok
        scene = asyncio.run(cp.build_creative_scene("urban_city_disasters", TIDAL, notion_history, [], gpt))
        self.assertEqual(scene["trace"]["view"], seen[0])   # döngü en eskiye döner
        # Seçim anında hafızaya yazılır: ikinci seçim, ilk üretim bitmeden yapılsa da farklı
        sk._VIEW_MEMORY.clear()
        first = sk.choose_region_view(TIDAL, [])
        sk.remember_view(TIDAL, first)
        for _ in range(20):
            self.assertNotEqual(sk.choose_region_view(TIDAL, []), first)
        self.assertNotIn(FLOOD, sk._VIEW_MEMORY)   # olay başına ayrı

    def test_test_mode_counted_in_history(self):
        from infrastructure import notion_logger as nl
        self.assertIn("✅ Tamamlandı (Test Modu / YouTube Atlandı)", nl.USED_COMBO_STATUSES)
        self.assertEqual(nl.USED_COMBO_STATUSES[:2], ["✅ Tamamlandı", "✅ Tamamlandı (Upload Başarısız)"])
        self.assertNotIn("❌ İptal", nl.USED_COMBO_STATUSES)

    def test_six_runs_six_views_with_notion_and_memory(self):
        # Gerçek akış: her üretim hem hafızaya hem (TEST modunda bitince) Notion geçmişine girer
        async def gpt(system, user, **kw):
            return slices_from_message(user)   # 4 Eki: kıyı dev dalga yapılandırılmış hatta
        notion, seen = [], []
        for _ in range(6):
            scene = asyncio.run(cp.build_creative_scene("urban_city_disasters", TIDAL, list(notion), [], gpt))
            seen.append(scene["trace"]["view"])
            notion.append(scene["combo_key"])
        self.assertEqual(len(set(seen)), 6, seen)
        self.assertEqual(sk.view_history(TIDAL, notion), seen)   # çift sayım yok, sıra korunur
        scene = asyncio.run(cp.build_creative_scene("urban_city_disasters", TIDAL, list(notion), [], gpt))
        self.assertEqual(scene["trace"]["view"], seen[0])

    def test_double_count_keeps_lru_order(self):
        # Notion: önceki günlerden riviera, gulf; bu süreçte gulf sonra riviera seçildi (hafıza). Riviera en yeni.
        notion = [self._city_combo(v, TIDAL) for v in ("riviera", "gulf_metropolis", "us_coastal_town",
                                                      "east_asian_coast", "north_african_coast",
                                                      "north_european_seaside", "gulf_metropolis", "riviera")]
        sk.remember_view(TIDAL, "gulf_metropolis")
        sk.remember_view(TIDAL, "riviera")
        self.assertEqual(sk.view_history(TIDAL, notion), ["us_coastal_town", "east_asian_coast", "north_african_coast",
                                                          "north_european_seaside", "gulf_metropolis", "riviera"])
        self.assertEqual(sk.choose_region_view(TIDAL, notion), "us_coastal_town")   # en eski
        # Hafıza tek başına: iptal edilen üretim Notion'da yok ama sayılır
        sk._VIEW_MEMORY.clear()
        sk.remember_view(TIDAL, "us_coastal_town")
        self.assertEqual(sk.choose_region_view(TIDAL, notion), "east_asian_coast")

    def test_real_notion_combo_key_parsed(self):
        real = ("urban_city_disasters|none|tidal wave surges over a coastal city street|"
                "coastal avenue behind a seawall#east_asian_coast|bystander_handheld")
        self.assertEqual(sk.view_of_combo(real), "east_asian_coast")
        for _ in range(30):
            self.assertNotEqual(sk.choose_region_view(TIDAL, [real]), "east_asian_coast")



class TestLandslide(unittest.TestCase):
    """2 Eki, Bahadır: ⛰️ Heyelan (TASLAK). Hızlı çamur/su akıntısı; yavaş kayma yok. Kilitli."""
    EVENTS = ["Mudslide pours down a hillside street", "Rain-soaked slope collapses onto a roadside", "Mud and debris torrent tears through a hillside village"]
    PLACES = ("italy", "italian", "japan", "brazil", "rio", "peru", "nepal", "india", "china", "turkey", "alps",
              "andes", "himalaya", "sign", "flag", "logo", "phone")

    def test_events_and_menu(self):
        import bot
        self.assertEqual(sk.skeleton_events("landslide_disasters"), self.EVENTS)
        self.assertEqual(bot.DOMAIN_LABELS["landslide_disasters"], "⛰️ Heyelan")
        self.assertEqual([bot.EVENT_LABELS[e] for e in self.EVENTS],
                         ["🌧️ Yamaç sokağına çamur seli", "⛰️ Yamaç çökmesi yola iner", "🏘️ Köy yamacından çamur akıntısı"])
        self.assertIn("landslide_disasters", sk.ENV_CENTRIC_DOMAINS)
        for e in self.EVENTS:
            self.assertIn(e, cp.REQUIRED_APPROVED)       # 2 Eki: onaylı (test edildi)
            self.assertNotIn(e, sk.REGION_VIEW_EVENTS)   # ilk sürümde bölge görünümü yok

    def test_outcomes_and_groups_locked(self):
        self.assertEqual([cp.EVENT_OUTCOMES[e] for e in self.EVENTS], [
            "a wall of brown mud and water pours down the steep street, slams into parked cars and shoves them sideways "
            "as people run uphill from the flow",
            "the saturated slope gives way and a fast torrent of mud and rocks surges across the road, pushing cars into "
            "the guardrail while drivers scramble out",
            "a fast torrent of mud, logs and rocks tears down between the houses, ramming walls and sweeping away fences "
            "and parked vehicles as villagers run to higher ground"])
        # 4 Eki (TASLAK, onay bekliyor): yapılandırılmış hatta, anahtar gruplar kalktı (core/event_structure.py)
        self.assertEqual([cp.EVENT_REQUIRED[e] for e in self.EVENTS], [[], [], []])
        import re
        for e in self.EVENTS:
            o = cp.EVENT_OUTCOMES[e]
            self.assertLessEqual(len(o.split()), 30)
            self.assertIsNone(re.search(r"\b(?:slow|slowly|slides?|sliding|creeps?|creeping|rises?|rising)\b", o), o)

    def test_spots_weather_people_style(self):
        import re
        from core.trace_format import count_constraints
        for e in self.EVENTS:
            s = sk.EVENT_SKELETONS[e]
            # 2 Eki: köprü noktası yol çökmesinden çıktı (çamur yola ulaşmadı)
            self.assertEqual(len(s["spots"]), 2 if e == self.EVENTS[1] else 3)
            self.assertEqual(s["weather"], ["driving rain and wind", "heavy downpour under dark storm light",
                                            "steady heavy rain, grey low cloud"])
            self.assertIsNone(s["ships"])
            self.assertEqual(sk.count_range(e, None), (3, 6))   # 4 Eki (TASLAK): olaya özel 3-6
            for spot in s["spots"]:
                suffix = sk.style_suffix(e, None, spot)
                self.assertLessEqual(count_constraints(suffix)[0], 8, suffix)
                self.assertTrue(suffix.endswith(" No readable signs, text or flags."))
                self.assertIn("Bystanders wear civilian clothes", suffix)
                self.assertIn("emergency responders wear service uniforms", suffix)
                self.assertIn(sk.CAMERA_SPOTS[spot], suffix)
                text = (suffix.replace("No readable signs, text or flags.", "") + " " + s["spots"][spot]).lower()
                self.assertFalse(set(re.findall(r"[a-z]+", text)) & set(self.PLACES), text)
        self.assertEqual(sk.count_range("Flash flooding in city streets", None), (2, 10))   # diğer env-centric aynı
        self.assertNotIn("No readable signs", sk.style_suffix("Large waves reaching the beach", None, "Open sandy beach"))

    def test_bridge_spot_removed_only_from_road_collapse(self):
        self.assertEqual(list(sk.EVENT_SKELETONS[self.EVENTS[1]]["spots"]),
                         ["Behind the guardrail of a hillside road", "Far edge of the road across from the slope"])
        for e in self.EVENTS:
            self.assertNotIn("Bridge on a side road below the slope", sk.EVENT_SKELETONS[e]["spots"])
        for _ in range(30):
            self.assertNotEqual(cp.pick_setting(self.EVENTS[1])[0], "Bridge on a side road below the slope")

    def test_good_stories_pass(self):
        ok = {
            "Mudslide pours down a hillside street": "A wall of brown mud and water pours down the steep hillside street in driving rain, slamming into "
                    "a row of parked cars. The mudslide shoves the cars sideways as five residents run uphill from the "
                    "flow. More mud keeps pouring down the street, still dragging cars and debris downhill.",
            "Rain-soaked slope collapses onto a roadside": "The rain-soaked slope above the hillside road collapses and a fast torrent of mud and rocks surges "
                    "across the roadside. It pushes two cars into the guardrail as four drivers scramble out. More mud "
                    "keeps pouring off the slope, still shoving the cars along the road.",
            "Mud and debris torrent tears through a hillside village": "A mud and debris torrent tears through the hillside village, carrying logs and rocks between the "
                    "stone houses. It rams walls and sweeps away fences and parked vehicles as six villagers run to "
                    "higher ground. The torrent keeps tearing downhill, still ramming more walls.",
        }
        for e, story in ok.items():
            with self.subTest(event=e):
                self.assertEqual(cp.story_rule_issues(e, None, story), [])


class TestFlashFloodFix(unittest.TestCase):
    """3 Eki, Bahadır: sel test videosu. Yakın koşan kişi dönüştü + kamera savruldu (A), 8-15. sn boş (B),
    su duvarı yerine alçak köpük dalgası (C). Değişiklik sadece sel olayında."""

    CAMERA = ("the camera pans to follow the waist-high wall of brown muddy floodwater in one slow short arc, never "
              "swinging around, people only in the middle and far distance; no zoom, no cuts.")
    def test_flood_camera_sentence_locked(self):
        from core.trace_format import count_constraints
        self.assertEqual(sk.EVENT_SKELETONS[FLOOD]["object"], "waist-high wall of brown muddy floodwater")
        for spot in sk.EVENT_SKELETONS[FLOOD]["spots"]:
            for v in [None] + list(sk.REGION_VIEWS):
                if v and spot not in sk.view_spots(FLOOD, v):
                    continue
                with self.subTest(spot=spot, view=v):
                    suffix = sk.style_suffix(FLOOD, None, spot, v)
                    self.assertIn(f"Handheld footage shot by a person standing {sk.CAMERA_SPOTS[spot]}, eye level, "
                                  f"normal lens; slight hand shake, {self.CAMERA}", suffix)
                    self.assertLessEqual(count_constraints(suffix)[0], 8, suffix)
                    self.assertNotIn("phone", suffix.lower())

    def test_other_events_suffix_untouched(self):
        self.assertEqual(set(sk.CAMERA_MOTION_EXTRA), {FLOOD})
        for e, s in sk.EVENT_SKELETONS.items():
            if e == FLOOD:
                continue
            ship = (s["ships"] or [None])[0]
            for spot in s["spots"]:
                with self.subTest(event=e, spot=spot):
                    suffix = sk.style_suffix(e, ship, spot)
                    self.assertIn(f"the camera pans to follow the {s['object']}; no zoom, no cuts.", suffix)
                    self.assertNotIn("slow short arc", suffix)
                    self.assertNotIn("middle and far distance", suffix)

    def test_bob_is_a_scale_reducer(self):
        # 4 Eki: "Cars bob like toys" süzülme ima eder; çekimleri otomatik
        for w in ("bob", "bobs", "bobbed", "bobbing"):
            with self.subTest(word=w):
                story = FLOOD_OK.replace("lifting them", f"the cars {w} as the water lifts them")
                self.assertIn("d_no_scale_reducers", [i["rule"] for i in cp.story_rule_issues(FLOOD, None, story)])
        self.assertEqual(cp.find_terms(("bob",), "Bobby's boat"), [])   # başka kelimenin içinde eşleşmez

    def test_futility_is_a_scale_reducer(self):
        story = FLOOD_OK.replace("lifting them", "their horns blaring in futility, lifting them")
        self.assertIn("d_no_scale_reducers", [i["rule"] for i in cp.story_rule_issues(FLOOD, None, story)])
        self.assertEqual(cp.find_terms(cp.SCALE_REDUCERS, FLOOD_OK), [])


    def test_no_hint_mechanism_left(self):
        # 4 Eki: sel ipucu ve ilk cümle kapısı yapılandırılmış hatta taşındı
        for name in ("EVENT_HINTS", "EVENT_FIRST_SENTENCE", "FIRST_SENTENCE_FEEDBACK"):
            self.assertFalse(hasattr(cp, name), name)
        for e in sk.EVENT_SKELETONS:
            self.assertNotIn("HINT:", cp._message(e, None, "x", "y", 2, 10, [], None))
        self.assertEqual(cp.EVENT_OUTCOMES[FLOOD], "a wall of brown floodwater surges down the street, slams into "
                                                   "parked cars and shoves them sideways as people run for higher ground")


class TestRivieraStreets(unittest.TestCase):
    """4 Eki, Bahadır: Riviera görünümü "cobbled promenade" -> "cobbled streets". Etkilenen diğer tek olay kıyı dev
    dalga: stil ekinde ve GPT'ye giden yer tarifinde aynı değişiklik, başka fark yok."""

    def test_riviera_text(self):
        self.assertIn("cobbled streets", sk.REGION_VIEWS["riviera"])
        self.assertNotIn("promenade", sk.REGION_VIEWS["riviera"])

    def test_tidal_wave_riviera_suffix_and_place(self):
        old = sk.REGION_VIEWS["riviera"].replace("cobbled streets", "cobbled promenade")
        for spot in sk.view_spots(TIDAL, "riviera"):
            with self.subTest(spot=spot):
                suffix = sk.style_suffix(TIDAL, None, spot, "riviera")
                self.assertIn("seafront district with cream stone buildings with shuttered windows, cobbled streets, "
                              "scooters, plane trees", suffix)
                place = sk.view_place(TIDAL, sk.EVENT_SKELETONS[TIDAL]["spots"][spot], "riviera")
                self.assertIn("cobbled streets", place)
                self.assertNotIn("cobbled promenade", suffix + place)
                # eski metinle tek fark bu kelime
                self.assertEqual(suffix.replace("cobbled streets", "cobbled promenade"),
                                 suffix.replace(sk.REGION_VIEWS["riviera"], old))
        # kıyı dalganın kendi çekim noktası adı değişmedi
        self.assertIn("Coastal road below a seafront promenade", sk.EVENT_SKELETONS[TIDAL]["spots"])


class TestStructuredScene(unittest.TestCase):
    """4 Eki (Tur 2): sel creative hatta yapılandırılmış yazımla üretilir; diğer olaylar eski yolda."""

    def setUp(self):
        es._BEAT_MEMORY.clear()
        sk._VIEW_MEMORY.clear()

    def slices(self, vehicle, s2=None, s3=None):
        return {"slice_1_rest": "It swallows the curbs and pours between the parked cars.",
                "slice_2": s2 or f"The {vehicle} is caught by the current, turns sideways and is dragged down the street.",
                "slice_3": s3 or "A lamppost topples into the current and crashes into the churning brown water."}

    def run_scene(self, responses, view="us_coastal_town"):
        calls = []

        async def gpt(system, user, **kw):
            calls.append({"system": system, "user": user, **kw})
            r = responses[min(len(calls), len(responses)) - 1]
            if isinstance(r, Exception):
                raise r
            return r
        with patch.object(es, "choose_beats", lambda *a, **k: ("V1", "D2")), \
                patch.object(es, "choose_vehicle", lambda v, rng=None: "pickup truck"):
            scene = asyncio.run(cp.build_creative_scene("urban_city_disasters", FLOOD, [], [], gpt, view=view))
        return scene, calls

    def test_scene_structure(self):
        scene, calls = self.run_scene([self.slices("pickup truck")])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["json_schema"], es.SLICE_SCHEMA)
        self.assertEqual(calls[0]["system"], cp.SLICES_SYSTEM)
        self.assertIn("4-9s EVENT: the pickup truck is caught by the current, turns sideways and is dragged down "
                      "the street", calls[0]["user"])
        self.assertIn("9-15s EVENT: a lamppost topples into the current", calls[0]["user"])
        self.assertIn(f"OPENING SENTENCE (fixed, already written): {es.EVENT_KEY_VISUAL[FLOOD]}", calls[0]["user"])
        self.assertTrue(scene["story"].startswith(f"0-4s: {es.EVENT_KEY_VISUAL[FLOOD]} It swallows"))
        self.assertIn(" 4-9s: The pickup truck", scene["story"])
        self.assertIn(" 9-15s: A lamppost", scene["story"])
        self.assertEqual(scene["prompt"], f"{scene['story'].rstrip('.')}. {scene['style_suffix']}")
        self.assertNotIn("0-4s", scene["plain_story"])
        self.assertTrue(scene["combo_key"].endswith("#us_coastal_town#V1+D2|bystander_handheld"))
        self.assertEqual(es.beats_of_combo(scene["combo_key"]), "V1+D2")
        self.assertTrue(sk.is_current_universe_combo(scene["combo_key"]))
        spec, sl = scene["structure"]["spec"], scene["structure"]["slices"]
        self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
        self.assertEqual(es.beat_history(FLOOD, []), ["V1+D2"])   # süreç hafızası seçim anında
        self.assertEqual(scene["trace"]["beats"], "V1+D2")
        self.assertEqual(scene["trace"]["vehicle"], "pickup truck")

    def test_slices_system_locked(self):
        # 4 Eki, Bahadır onayı. Tüm yapılandırılmış olaylarda ortak: olaya özel kelime içermez.
        self.assertEqual(cp.SLICES_SYSTEM, (
            "You write the three time slices of one 15-second realistic video of a real incident.\n"
            "The code already wrote the opening sentence of 0-4s and adds the time labels; never write labels.\n"
            "Return JSON with three fields:\n"
            "- slice_1_rest: one sentence of 6 to 18 words that continues 0-4s right after the opening sentence: "
            "how the opening event hits this place.\n"
            "- slice_2: the given 4-9s event in 10 to 24 words, in your own words for this place; use every given "
            "detail.\n"
            "- slice_3: the given 9-15s event in 10 to 24 words, a new and bigger destruction, still moving at the "
            "very end.\n"
            "Rules: describe only what is visible, never sounds, the camera or the video. People stay in the middle "
            "and far distance and are never the main event. Catastrophic in scale, never mild or harmless. Make it "
            "different from the recent stories."))
        low = cp.SLICES_SYSTEM.lower()
        for word in ("water", "flood", "vehicle", "street", "car ", "cars", "hint", "halfway"):
            self.assertNotIn(word, low)

    def test_vehicle_is_given_detail_and_checked(self):
        spec = es.build_spec(FLOOD, None, "Downtown city center", "riviera", "V2", "D5", "delivery van")
        msg = cp._slices_message(spec, "x", "heavy rain", 2, 10, [], None)
        self.assertIn("\nVEHICLE: delivery van\n", msg)
        self.assertIn("4-9s EVENT: the delivery van is swept into another parked car", msg)
        sl = es.parse_slices(self.slices("delivery van", s2="The small car is swept into another parked car and both "
                                         "are shoved along the street.",
                                         s3="A city bus is shoved sideways by the current and slides across the street."))
        self.assertIn("4-9s: araç (delivery van)",
                      [i["missing"] for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl))])

    def test_bad_json_stops_without_retry(self):
        for bad in ({"story": "x"}, {"slice_1_rest": "a", "slice_2": "b"}, ["x"], ValueError("bozuk JSON"),
                    RuntimeError("GPT API hatası")):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises((es.StructureError, ValueError, RuntimeError)):
                    _, calls = self.run_scene([bad, self.slices("pickup truck")])
                # ikinci yanıt hiç istenmedi: hata deneme yemez, akış durur

    def test_bad_json_calls_gpt_once(self):
        calls = []

        async def gpt(system, user, **kw):
            calls.append(1)
            return {"story": "x"}
        with patch.object(es, "choose_beats", lambda *a, **k: ("V1", "D2")), \
                patch.object(es, "choose_vehicle", lambda v, rng=None: "pickup truck"):
            with self.assertRaises(es.StructureError):
                asyncio.run(cp.build_creative_scene("urban_city_disasters", FLOOD, [], [], gpt, view="us_coastal_town"))
        self.assertEqual(len(calls), 1)

    def test_quality_failure_retries_with_feedback(self):
        bad = self.slices("pickup truck", s3="A low wall collapses into the brown water as more debris arrives.")
        scene, calls = self.run_scene([bad, self.slices("pickup truck")])
        self.assertEqual(len(calls), 2)
        self.assertIn("YOUR PREVIOUS ANSWER WAS REJECTED: 'slice_3' must clearly show this event: a lamppost topples "
                      "into the current.", calls[1]["user"])
        self.assertEqual(len(scene["trace"]["attempts"]), 2)
        self.assertIn("9-15s: seçilen olay (D2) görünmüyor", scene["trace"]["attempts"][0]["missing"])

    def test_three_failures_raise(self):
        bad = self.slices("pickup truck", s2="The sedan rocks gently in the water as it rises around the wheels.")
        with self.assertRaises(cp.CreativeStoryError) as ctx:
            self.run_scene([bad])
        self.assertEqual(len(ctx.exception.attempts), cp.MAX_ATTEMPTS)
        self.assertEqual(ctx.exception.trace["beats"], "V1+D2")

    def test_diversity_ignores_shared_key_visual(self):
        spec = es.build_spec(FLOOD, None, "Downtown city center", "us_coastal_town", "V1", "D2", "pickup truck")
        sl = es.parse_slices(self.slices("pickup truck"))
        other = es.parse_slices(self.slices("pickup truck", s2="The pickup truck spins side-on and slides along the "
                                            "road past the low wooden houses.",
                                            s3="A streetlight snaps at its base and falls flat into the fast flow."))
        recent = [es.assemble_story(spec, other)]
        self.assertEqual(cp.diversity_issues(" ".join(sl.values()), [cp._gpt_text(spec, r) for r in recent]), [])
        self.assertNotIn("diversity", [i["rule"] for i in cp.structured_issues(spec, sl, recent)])

    def test_other_events_use_old_path(self):
        calls = []

        async def gpt(system, user, **kw):
            calls.append(kw)
            return {"story": WAVE_OK}
        scene = asyncio.run(cp.build_creative_scene("cruise_ship_operations", WAVE, [], [], gpt))
        self.assertNotIn("json_schema", calls[0])
        self.assertNotIn("structure", scene)
        self.assertNotIn("0-4s", scene["story"])

    def test_metadata_gets_plain_story(self):
        src = inspect.getsource(pg.generate_creative_prompts)
        self.assertIn('"scenario_summary": scene.get("plain_story") or story', src)
        self.assertIn('"structure": scene.get("structure")', src)


class TestVideoConfigLocks(unittest.TestCase):
    """3 Eki, Bahadır: 15 sn altı video yok (açılışta hata); çözünürlük tek yerden (config.py)."""

    def test_current_values(self):
        import config
        self.assertEqual((settings.DEFAULT_DURATION, settings.DEFAULT_RESOLUTION), (15, "480p"))
        self.assertEqual(config.VIDEO_DURATION_SECONDS, 15)
        self.assertEqual(config.VIDEO_RESOLUTIONS, ("480p", "720p"))

    def test_duration_lock(self):
        import config
        for bad in ("10", "5", "14", "20"):
            with self.subTest(duration=bad), patch.dict(os.environ, {"DEFAULT_DURATION": bad}):
                with self.assertRaises(EnvironmentError):
                    config.Config()
        with patch.dict(os.environ, {"DEFAULT_DURATION": "15"}):
            self.assertEqual(config.Config().DEFAULT_DURATION, 15)

    def test_resolution_single_source(self):
        import re
        hits = []
        for folder in ("core", "infrastructure", "scripts", "."):
            base = os.path.join(ROOT, folder)
            for name in os.listdir(base):
                path = os.path.join(base, name)
                if not name.endswith(".py") or name == "config.py" or not os.path.isfile(path):
                    continue
                for n, line in enumerate(open(path, encoding="utf-8"), 1):
                    if not line.lstrip().startswith("#") and re.search(r"""["']480p["']|["']720p["']""", line):
                        hits.append(f"{folder}/{name}:{n}")
        self.assertEqual(hits, [])
        self.assertIsNone(inspect.signature(KieClient.create_video).parameters["resolution"].default)

    def test_create_video_uses_settings_resolution(self):
        client = KieClient()
        seen = {}

        async def fake_create(cfg, prompt, aspect, duration, audio, resolution):
            seen["resolution"] = resolution
            raise RuntimeError("stop")

        async def fake_preflight(story):
            return story, False, {}

        with patch.object(settings, "IS_DRY_RUN", False), patch.object(client, "_create_task", fake_create), \
                patch("core.prompt_sanitizer.gpt_preflight_check", fake_preflight):
            with self.assertRaises(RuntimeError):
                asyncio.run(client.create_video(model="bytedance/seedance-2-fast", prompt="x", style_suffix="y"))
        self.assertEqual(seen["resolution"], settings.DEFAULT_RESOLUTION)


if __name__ == "__main__":
    unittest.main()
