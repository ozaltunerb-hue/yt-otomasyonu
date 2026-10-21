#!/usr/bin/env python3
"""Caption sistemi (21 Eki 2026, Aşama 7): başlık + açıklama + CTA + hashtag + Paylaşımlar bağlantısı.

Mock GPT; Kie/Notion yok (Notion istekleri sahte). Fixture: tests/fixtures/paylasimlar_snapshot.json (49 paylaşım).
"""
import asyncio
import json
import logging
import os
import random
import sys
import unittest
from unittest.mock import MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import core.event_structure as es   # noqa: E402  (önce: döngüsel import sırası)
import core.caption as cap   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import prompt_snapshot as ps   # noqa: E402
from infrastructure import notion_logger as nl   # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "paylasimlar_snapshot.json")
ROWS = json.load(open(FIXTURE, encoding="utf-8"))["rows"]
INFO = {"opening": "A volcanic bomb smashes into a large parked truck and the truck bursts into flames.", "people": 4,
        "kadraj": "balkon"}


def ctx(generated=()):
    return cap.build_context(ROWS, list(generated))


def gpt_candidates(styles=("T3", "T5", "T6"), cta_type="emoji", cta="Comment 🏃 or 🏠"):
    texts = {"T1": "Fire Rain Over the Rooftops 🔥", "T2": "The Instant the Sky Turns Red", "T3": "Six Glowing Rocks, One Street",
             "T4": "Could Anyone Stay on This Street?", "T5": "Filmed From a Balcony as Rocks Fell 🌋",
             "T6": "Glowing Rocks Pound a Quiet Lane"}
    return {"titles": [(texts[s], s) for s in styles],
            "descriptions": ["Glowing rocks begin to fall on a quiet lane, then one hits a parked truck and flames spread.",
                             "First a single rock, then a barrage: roofs crack and a truck burns in the middle of the lane."],
            "cta": cta, "cta_type": cta_type}


class TestFixture(unittest.TestCase):
    def test_snapshot_has_49_text_rows(self):
        self.assertEqual(len(ROWS), 49)
        for r in ROWS:
            self.assertIn("Başlık", r)
            for v in r.values():
                self.assertNotIn("secret_", str(v))
                self.assertNotIn("ntn_", str(v))


class TestChecks(unittest.TestCase):
    def test_similar_waterspout_rejected(self):
        issues = cap.title_issues("A Massive Waterspout Hits the Coast", ctx())
        self.assertTrue(any("massive" in i for i in issues))   # kalıcı yasak
        # temizlenmiş kelimelerle: olay adı (waterspout) ve stopword sayılmaz; ilk 3 kelime ve Jaccard aynı
        self.assertEqual(cap.first3("The Waterspout Hits the Coast"), ("hit", "coast"))
        near = cap.title_issues("Dark Sky Above the Burning Lane", cap.build_context(
            [{"Başlık": "Dark Sky Over the Burning Lane", "Paylaşım Tarihi": "2026-10-01"}], []))
        self.assertTrue(any(i.startswith("benzer") for i in near))

    def test_clean_words(self):
        self.assertEqual(cap.clean_words("The Moment the Tornado Hit the City Street 🌪️ in 15 seconds"),
                         ["moment", "hit", "second"])
        self.assertEqual(cap.first3("A Wall of Flames Reaches the Village Houses"), ("wall", "reache", "house"))
        # "The…" ile başlayan iki farklı başlık ilk 3 kelime kuralına takılmaz
        c = cap.build_context([{"Başlık": "The Moment the Tide Turned", "Paylaşım Tarihi": "2026-10-01"}], [])
        self.assertFalse([i for i in cap.title_issues("The Lane Before the Wave Hit", c) if "ilk 3" in i])

    def test_every_fixture_title_rejects_itself(self):
        c = ctx()
        for r in ROWS:
            self.assertTrue(cap.title_issues(r["Başlık"], c), r["Başlık"])

    def test_banned_phrases(self):
        for p in cap.BANNED_PHRASES:
            self.assertTrue(cap.banned_phrases(f"A {p} story"))
            self.assertTrue(cap.banned_phrases(f"A {p.upper()} story"))
        self.assertTrue(cap.banned_phrases("An AI flood"))
        self.assertTrue(cap.banned_phrases("Flood hits Florida"))

    def test_dynamic_ban(self):
        c = ctx()
        self.assertNotIn("volcanic", c["dynamic_banned"])   # olay adı sayılmaz
        self.assertNotIn("street", c["dynamic_banned"])
        word = sorted(c["dynamic_banned"])[0]
        self.assertTrue(any("son başlıklarda sık" in i for i in cap.title_issues(f"{word.title()} Rocks Over a Lane", c)))

    def test_description_rules(self):
        c = ctx()
        self.assertTrue(cap.description_issues(" ".join(["word"] * 40), c))
        self.assertTrue(cap.description_issues(INFO["opening"], c, INFO["opening"]))
        old = next(r["Açıklama"] for r in ROWS if r.get("Açıklama"))
        self.assertTrue(cap.description_issues(old, c))

    def test_cta_rules(self):
        self.assertTrue(cap.cta_issues("Fifteen seconds of chaos", "stat") == [])
        self.assertTrue(cap.cta_issues("Lots of chaos", "stat"))
        self.assertTrue(cap.cta_issues("Comment below", "emoji"))
        self.assertEqual(cap.cta_issues("", "none"), [])


class TestSelection(unittest.TestCase):
    def test_style_and_cta_lru(self):
        gen = [{"title": "x1", "style": "T3", "cta_type": "emoji", "date": "2026-10-22"},
               {"title": "x2", "style": "T5", "cta_type": "stat", "date": "2026-10-23"}]
        c = cap.choose(cap.BOMBS, INFO, gpt_candidates(), ctx(gen), random.Random(1))
        self.assertNotIn(c["style"], ("T3", "T5"))
        self.assertEqual(c["style"], "T6")   # izinli ilk GPT adayı
        self.assertNotIn(c["cta_type"], ("emoji", "stat"))
        self.assertEqual(c["cta_source"], "şablon")   # GPT tipi son 2'de -> şablon

    def test_gpt_first_passing_candidate(self):
        c = cap.choose(cap.BOMBS, INFO, gpt_candidates(), ctx(), random.Random(2))
        self.assertEqual(c["title_source"], "GPT")
        self.assertEqual(c["source"], "GPT")

    def test_template_fallback(self):
        bad = {"titles": [("A Massive Eruption", "T1"), ("In Seconds Everything Burns", "T3")],
               "descriptions": ["A massive eruption."], "cta": "", "cta_type": "none"}
        c = cap.choose(cap.BOMBS, INFO, bad, ctx(), random.Random(3))
        self.assertTrue(c["title_source"].startswith("şablon"))
        self.assertTrue(c["rejected"])
        self.assertEqual(cap.title_issues(c["title"], ctx()), [])

    def test_hashtag_rules(self):
        c = ctx()
        for e in cap.SHARE_CATEGORY:
            tags = cap.choose_hashtags(e, c, random.Random(4))
            broad, special = cap.event_tags(e)
            self.assertEqual(len(tags), 5)
            self.assertEqual(len([t for t in tags if t in broad]), 2, e)
            self.assertEqual(len([t for t in tags if t in special]), 3, e)
            for t in tags:
                self.assertFalse(cap.is_banned_tag(t))
                if t in cap.TAG_ONLY:
                    self.assertIn(e, cap.TAG_ONLY[t], (e, t))
            if e not in cap.MARITIME_EVENTS:
                self.assertFalse(set(tags) & set(cap.MARITIME_TAGS))
        self.assertTrue(cap.is_banned_tag("#AIvideo"))
        self.assertTrue(cap.is_banned_tag("#earthquake"))

    def test_hashtag_overlap_and_repeat(self):
        gen = []
        for i in range(10):
            c = cap.choose(cap.FLOOD, {"opening": "x", "people": None, "kadraj": "çatı"}, None, ctx(gen),
                           random.Random(i))
            prev = next((g["hashtags"] for g in reversed(gen) if g["category"] == "Sel"), None)
            if prev:
                self.assertLessEqual(len(set(c["hashtags"]) & set(prev)), 2)
            self.assertNotIn(set(c["hashtags"]), [set(g["hashtags"]) for g in gen[-10:]])
            gen.append({**cap.meta(c), "date": f"2026-10-{22 + i}"})

    def test_overlap_rule_every_event(self):
        # her olay art arda 10 post: aynı kategorideki önceki postla en fazla 2 ortak, son 10'da aynı set yok.
        # İstisna: cephe yangınında olaya uygun özel etiket sadece 3 (#firestorm #firefighters #smoke): 6 farklı set
        # var; ardışık cephe postlarında en az 3 ortak kaçınılmaz, 7. posttan sonra set tekrarı da kaçınılmaz. Kod önce
        # "son 10'da aynı set yok"u, sonra en az ortaklıyı seçer (raporda; havuza 2 etiket eklemek Bahadır kararı)
        for e in cap.SHARE_CATEGORY:
            gen = []
            for i in range(10):
                tags = cap.choose_hashtags(e, cap.build_context([], gen), random.Random(i))
                if gen:
                    common = len(set(tags) & set(gen[-1]["hashtags"]))
                    self.assertLessEqual(common, 4 if e == cap.FACADE else 2, (e, i))
                if e != cap.FACADE or i < 6:
                    self.assertNotIn(set(tags), [set(g["hashtags"]) for g in gen[-10:]], (e, i))
                gen.append({"hashtags": tags, "category": cap.SHARE_CATEGORY[e], "date": f"2026-11-{i + 1:02d}"})
        self.assertEqual(cap.event_tags(cap.EQ_A)[0], ("#disaster", "#extremeevents", "#catastrophe", "#survival"))

    def test_block_format(self):
        c = {"title": "T", "description": "D", "cta": "", "cta_type": "none", "hashtags": ["#a", "#b"],
             "style": "T1", "source": "GPT"}
        self.assertEqual(cap.block(c), "T\n\nD\n\n#a #b")
        self.assertEqual(cap.block({**c, "cta": "C"}), "T\n\nD\n\nC\n\n#a #b")
        self.assertEqual(cap.info_line({**c, "cta_type": "emoji", "style": "T3"}),
                         "stil: T3 · CTA: Emoji seçimi · kaynak: GPT")


class TestSchemaAndStory(unittest.TestCase):
    def test_schema_has_caption_fields(self):
        props = es.SLICE_SCHEMA["schema"]["properties"]
        for f in cap.CAPTION_FIELDS:
            self.assertIn(f, props)
        self.assertEqual(set(es.SLICE_SCHEMA["schema"]["required"]), set(es.SLICE_FIELDS) | set(cap.CAPTION_FIELDS))
        self.assertEqual(props["cta_type"]["enum"], list(cap.CTA_TYPES))

    def test_story_fields_unaffected(self):
        story = {"slice_1_rest": "Five people run from the falling rocks.",
                 "slice_2": "A glowing rock punches through the roof of the pickup truck.",
                 "slice_3": "Glowing rocks slam into the roofs, sending tiles flying as flames rise."}
        full = {**story, "title_1": "A", "title_1_style": "T1", "title_2": "B", "title_2_style": "T2", "title_3": "C",
                "title_3_style": "T3", "description_1": "d1", "description_2": "d2", "cta": "", "cta_type": "none"}
        self.assertEqual(es.parse_slices(full), es.parse_slices(story))
        self.assertEqual(cap.extract_candidates(full)["titles"][0], ("A", "T1"))
        self.assertIsNone(cap.extract_candidates(story))

    def test_caption_block_only_with_context(self):
        e = es.TIDAL
        spot = "Coastal avenue behind a seawall"
        spec = es.build_spec(e, None, spot, "riviera", "T2", "W3", "large SUV", 4)
        plain = cp._slices_message(spec, "P", "W", 3, 6, [], None)
        with_ctx = cp._slices_message(spec, "P", "W", 3, 6, [], None, ctx())
        self.assertNotIn("CAPTION", plain)
        self.assertTrue(with_ctx.startswith(plain))
        self.assertIn("RECENT POSTED TITLES", with_ctx)
        self.assertIn("title_1/2/3: max 9 words", with_ctx)

    def test_pipeline_uses_gpt_candidates_without_extra_call(self):
        import core.prompt_generator as pg
        calls = []

        async def fake(system, user, temperature=0.85, model="gpt-4o", json_schema=None):
            calls.append(json_schema)
            return {"slice_1_rest": "x", "slice_2": "x", "slice_3": "x", "title_1": "Six Glowing Rocks, One Street",
                    "title_1_style": "T3", "title_2": "Filmed From a Balcony as Rocks Fell 🌋", "title_2_style": "T5",
                    "title_3": "Glowing Rocks Pound a Quiet Lane", "title_3_style": "T6",
                    "description_1": "Rocks fall on a quiet lane and a parked truck catches fire.",
                    "description_2": "One rock, then many: roofs crack and the lane burns.",
                    "cta": "Which detail did you notice first?", "cta_type": "question"}
        logging.disable(logging.WARNING)
        try:
            ps.reset_memory()
            random.seed(5)
            with patch.object(pg, "_call_gpt", fake), patch.object(pg, "_generate_metadata",
                                                                   side_effect=AssertionError("ek GPT çağrısı")):
                out = asyncio.run(pg.generate_creative_prompts({"domain": "volcano_disasters", "event": es.VOLCANIC_BOMBS,
                                                                "caption_loader": lambda: {"posted": ROWS,
                                                                                           "generated": []}}))
        finally:
            logging.disable(logging.NOTSET)
        self.assertTrue(all(c == es.SLICE_SCHEMA for c in calls))
        self.assertEqual(len(calls), 2)   # hikâye denemeleri (kapıdan kalır -> kod yedeği); caption için ek çağrı yok
        c = out["caption"]
        self.assertTrue(out["youtube_title"].endswith(" #Shorts"))
        self.assertEqual(out["youtube_title"], c["title"] + " #Shorts")
        self.assertNotIn("Maritime", out["tags"])
        self.assertEqual(json.loads(out["axes_json"])["caption"]["title"], c["title"])
        self.assertIn(c["title"], [t for t, _ in out["caption_state"]["candidates"]["titles"]]
                      + [c["title"]])

    def test_caption_loader_failure_does_not_stop(self):
        import core.prompt_generator as pg

        async def fake(system, user, **kw):
            return {"slice_1_rest": "x", "slice_2": "x", "slice_3": "x"}

        def boom():
            raise RuntimeError("Notion 502")
        logging.disable(logging.WARNING)
        try:
            ps.reset_memory()
            random.seed(6)
            with patch.object(pg, "_call_gpt", fake):
                out = asyncio.run(pg.generate_creative_prompts({"domain": "fire_disasters", "event": es.WILDFIRE,
                                                                "caption_loader": boom}))
        finally:
            logging.disable(logging.NOTSET)
        self.assertEqual(out["caption"]["source"], "şablon")
        self.assertIn("okunamadı", out["caption"]["warning"])


class TestShareButton(unittest.TestCase):
    def test_add_shared_post_once(self):
        created = []

        def req(method, url, **kw):
            if url.endswith("/query"):
                return {"results": [{"id": "row-1"}]} if created else {"results": []}
            created.append(kw["json"])
            return {"id": "row-1"}
        c = {"title": "T", "description": "D", "cta": "", "cta_type": "none", "hashtags": ["#a", "#b"],
             "category": "Volkan"}
        with patch.object(nl, "_notion_request", side_effect=req):
            first = nl.NotionTracker.add_shared_post(c, "🌋 Volkan bombaları", "abcd" * 8, "2026-10-21")
            second = nl.NotionTracker.add_shared_post(c, "🌋 Volkan bombaları", "abcd" * 8, "2026-10-21")
        self.assertEqual(first, ("row-1", True))
        self.assertEqual(second, ("row-1", False))
        self.assertEqual(len(created), 1)
        props = created[0]["properties"]
        self.assertEqual(created[0]["parent"]["database_id"], nl.SHARES_DB_ID)
        self.assertEqual(props["CTA Tipi"]["select"]["name"], "CTA yok")
        self.assertEqual(props["Platform"]["multi_select"], [{"name": "Instagram"}])
        self.assertTrue(props["Deneme Reel"]["checkbox"])
        self.assertIn("sistem üretimi", props["Not"]["rich_text"][0]["text"]["content"])
        self.assertIn("abcd" * 8, props["Not"]["rich_text"][0]["text"]["content"])

    def test_bot_share_and_new_caption(self):
        import bot
        sent = []

        async def fake_send(b, chat, text, **kw):
            sent.append((text, kw))
            return MagicMock()
        context = MagicMock()
        context.bot_data = {}
        page = "abcd" * 8
        c = cap.choose(cap.BOMBS, INFO, gpt_candidates(), ctx(), random.Random(7))
        state = {"event": cap.BOMBS, "info": INFO, "candidates": gpt_candidates(), "ctx": ctx(), "shown": [c["title"]]}
        with patch.object(bot, "safe_send", fake_send), patch.object(bot, "_allowed_chat", return_value=1), \
                patch.object(bot.NotionTracker, "add_shared_post", return_value=("row", True)) as add, \
                patch.object(bot.NotionTracker, "record_caption") as rec:
            asyncio.run(bot.send_caption(MagicMock(), 1, page, c, state, context.bot_data))
            self.assertIn("<pre>", sent[-1][0])
            self.assertEqual(sent[-1][1]["parse_mode"], "HTML")
            asyncio.run(bot._on_caption_share(MagicMock(), context, page))
            self.assertEqual(add.call_count, 1)
            titles = {c["title"]}
            for _ in range(3):
                asyncio.run(bot._on_caption_new(MagicMock(), context, page))
                titles.add(context.bot_data["captions"][page]["caption"]["title"])
            self.assertEqual(len(titles), 4)   # her yeni caption farklı başlık
            self.assertEqual(rec.call_count, 3)
            asyncio.run(bot._on_caption_new(MagicMock(), context, page))
            self.assertIn("En fazla 3", sent[-1][0])

    def test_schema_has_caption_column(self):
        self.assertEqual(nl.EXTRA_PROPERTIES[nl.CAPTION_PROPERTY], {"rich_text": {}})


class TestSimulation(unittest.TestCase):
    def test_ten_in_a_row_each_event(self):
        import caption_sim
        logging.disable(logging.WARNING)
        try:
            res = caption_sim.simulate(runs=10, seed=11)
        finally:
            logging.disable(logging.NOTSET)
        for e, rows in res.items():
            styles = [r["style"] for r in rows]
            for i in range(2, len(styles)):
                self.assertNotIn(styles[i], styles[i - 2:i], e)
            titles = [r["title"] for r in rows]
            self.assertEqual(len(set(titles)), len(titles), e)


if __name__ == "__main__":
    unittest.main()
