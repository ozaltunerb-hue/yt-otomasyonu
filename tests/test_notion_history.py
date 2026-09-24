#!/usr/bin/env python3
"""
Notion tarihçe filtreleri (2026-09-24): evren filtresi, Durum filtresi, kronolojik sıra.

Gerçek Notion çağrısı yapılmaz. _notion_request sahte bir Notion ile değiştirilir; sahte
Notion sorgudaki and/or/equals/does_not_equal şartlarını fixture üzerinde gerçekten uygular,
böylece Durum filtresi kodun gönderdiği sorgu üzerinden test edilir.
"""
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.creative_engine as ce
import core.prompt_generator as pg
import infrastructure.notion_logger as nl
from config import settings

DONE = "✅ Tamamlandı"
UPLOAD_FAIL = "✅ Tamamlandı (Upload Başarısız)"
TEST_MODE = "✅ Tamamlandı (Test Modu / YouTube Atlandı)"
TEST_MANUAL = "✅ Tamamlandı (Test — YouTube atlandı)"
GENERATING = "Video Üretiliyor"
ERROR = "❌ Hata"

CLEAN = [
    "cruise_ship_operations|mega cruise ship|bow thruster docking failure|open-air pool deck|fixed_cctv",
    "ferry_operations|passenger car ferry|secured vehicles breaking loose|island crossing route|chase_pov",
    "marina_and_yacht_operations|runaway powerboat|wake collision|marina fairway|bystander_handheld",
    "shipyard_and_drydock_engineering|vessel on slipway|drydock flooding instability|shipyard basin|fixed_cctv",
    "open_beach_coastal_events|none|storm surge|sandy shoreline|fixed_cctv",
    "coastal_tornado_landfall|sailing yacht|tornado landfall|harbor area|bystander_handheld",
]
DIRTY = [
    "container_and_gantry_operations|feeder container ship|container stack collapse",
    "commercial_storm_fishing|north sea stern trawler|trawl winch cable snap",
    "heavy_lift_and_project_cargo|heavy lift barge|deck crane load shift",
    "arctic_ice_navigation|arctic lng carrier|ice floe collision|frozen pack ice|chase_pov",
    "ferry_operations|harbor tugboat|tug push|ferry terminal ramp|fixed_cctv",  # domain doğru, gemi evren dışı
    "",
]


def _page(day: int, combo: str, status: str, topic: str, title: str) -> dict:
    return {"properties": {
        "Tarih": {"date": {"start": f"2026-09-{day:02d}T12:00:00+00:00"}},
        "Durum": {"select": {"name": status}},
        "Combo Key": {"rich_text": [{"text": {"content": combo}}] if combo else []},
        "Konu": {"rich_text": [{"text": {"content": topic}}]},
        "Video Adı": {"title": [{"text": {"content": title}}]},
    }}


def _matches(page: dict, f: dict) -> bool:
    if "and" in f:
        return all(_matches(page, x) for x in f["and"])
    if "or" in f:
        return any(_matches(page, x) for x in f["or"])
    prop = page["properties"][f["property"]]
    if "select" in f:
        name = (prop["select"] or {}).get("name")
        cond = f["select"]
        if "equals" in cond:
            return name == cond["equals"]
        if "does_not_equal" in cond:
            return name != cond["does_not_equal"]
    if "date" in f:
        return prop["date"]["start"] >= f["date"]["on_or_after"][:10]
    raise AssertionError(f"sahte Notion bilinmeyen şart: {f}")


class FakeNotion:
    def __init__(self, pages):
        self.pages = pages
        self.payloads = []

    def __call__(self, method, url, json=None, **kw):
        self.payloads.append(json)
        hits = [p for p in self.pages if _matches(p, json["filter"])]
        hits.sort(key=lambda p: p["properties"]["Tarih"]["date"]["start"], reverse=True)
        return {"results": hits[: json["page_size"]], "has_more": False}


class NotionHistoryBase(unittest.TestCase):
    def run_tracker(self, pages, method, **kw):
        fake = FakeNotion(pages)
        with patch.object(nl, "_notion_request", fake), patch.object(settings, "IS_DRY_RUN", False):
            tracker = nl.NotionTracker()
            tracker.enabled = True
            with patch("infrastructure.notion_logger.datetime") as dt:
                dt.now.return_value = __import__("datetime").datetime(2026, 9, 24, tzinfo=nl.timezone.utc)
                result = getattr(tracker, method)(**kw)
        return result, fake


class TestStatusFilter(NotionHistoryBase):
    PAGES = [
        _page(d, CLEAN[i], st, f"topic {st}", f"title {st}")
        for i, (d, st) in enumerate([(18, DONE), (19, UPLOAD_FAIL), (20, TEST_MODE),
                                     (21, TEST_MANUAL), (22, GENERATING), (23, ERROR)])
    ]

    def test_used_combos_only_published_or_upload_failed(self):
        combos, fake = self.run_tracker(self.PAGES, "get_used_combos")
        self.assertEqual(combos, [CLEAN[0], CLEAN[1]])  # kronolojik
        self.assertEqual(fake.payloads[0]["page_size"], 100)

    def test_recent_history_everything_but_error(self):
        history, fake = self.run_tracker(self.PAGES, "get_recent_history")
        self.assertEqual(len(history), 10)  # 5 kayıt × (Konu + Video Adı)
        self.assertNotIn(f"title {ERROR}", history)
        for st in (DONE, UPLOAD_FAIL, TEST_MODE, TEST_MANUAL, GENERATING):
            self.assertIn(f"title {st}", history)
        self.assertEqual(fake.payloads[0]["page_size"], 100)


class TestUniverseFilter(NotionHistoryBase):
    def test_dirty_combos_dropped_clean_kept(self):
        pages = [_page(10 + i, c, DONE, f"dirty topic {i}", f"dirty title {i}") for i, c in enumerate(DIRTY)]
        pages += [_page(17 + i, c, DONE, f"clean topic {i}", f"clean title {i}") for i, c in enumerate(CLEAN)]
        combos, _ = self.run_tracker(pages, "get_used_combos")
        self.assertEqual(combos, CLEAN)
        history, _ = self.run_tracker(pages, "get_recent_history")
        self.assertFalse([h for h in history if h.startswith("dirty")])
        self.assertEqual(len(history), 2 * len(CLEAN))

    def test_new_domain_accepted_automatically(self):
        combo = "hovercraft_operations|rescue hovercraft|skirt tear|mud flats|fixed_cctv"
        self.assertFalse(ce.is_current_universe_combo(combo))
        with patch.dict(ce.MARITIME_INSPIRATION_DOMAINS, {"hovercraft_operations": {}}), \
             patch.object(ce, "VESSEL_UNIVERSE", ce.VESSEL_UNIVERSE + ["Rescue Hovercraft"]):
            self.assertTrue(ce.is_current_universe_combo(combo))
        self.assertFalse(ce.is_current_universe_combo(combo))


def _writer_user_message(used_combos, recent_topics) -> str:
    """generate_prompts'un tarihçeyi birleştirip yazıcıya verdiği yolun birebir kopyası."""
    combined = list(dict.fromkeys(used_combos + recent_topics))
    mock = AsyncMock(return_value={})
    with patch.object(pg, "_call_gpt", mock):
        catalyst = ce.get_creative_catalyst(recent_history=combined)
        asyncio.run(pg._generate_scenario(catalyst, "fixed_cctv"))
    return mock.call_args.args[1]


class TestChronologyAndEmpty(NotionHistoryBase):
    def test_newest_record_reaches_writer(self):
        # 12 temiz kayıt = 24 metin; 20'ye kırpılır, yazıcı [-15:] alır. En yeni mutlaka görünmeli.
        pages = [_page(1 + i, CLEAN[i % len(CLEAN)], TEST_MODE, f"topic day{1+i:02d}", f"title day{1+i:02d}")
                 for i in range(12)]
        history, _ = self.run_tracker(pages, "get_recent_history")
        self.assertEqual(history[-1], "topic day12")
        self.assertEqual(history[0], "title day03")  # en eski 2 kayıt 20 sınırında düştü
        msg = _writer_user_message([], history)
        self.assertIn("title day12", msg)
        self.assertIn("topic day12", msg)
        self.assertNotIn("day03", msg)

    def test_no_valid_records(self):
        pages = [_page(10 + i, c, DONE, f"t{i}", f"v{i}") for i, c in enumerate(DIRTY)]
        combos, _ = self.run_tracker(pages, "get_used_combos")
        history, _ = self.run_tracker(pages, "get_recent_history")
        self.assertEqual((combos, history), ([], []))
        self.assertIn("None (First run)", _writer_user_message(combos, history))

    def test_disabled_or_dry_run_returns_empty(self):
        tracker = nl.NotionTracker()
        tracker.enabled = False
        self.assertEqual(tracker.get_used_combos(), [])
        self.assertEqual(tracker.get_recent_history(), [])
        tracker.enabled = True
        with patch.object(settings, "IS_DRY_RUN", True):
            self.assertEqual(tracker.get_used_combos(), [])
            self.assertEqual(tracker.get_recent_history(), [])


if __name__ == "__main__":
    unittest.main()
