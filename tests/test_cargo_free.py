#!/usr/bin/env python3
"""
Kargo-temizliği, cast tablosu ve VESSEL_UNIVERSE testleri (2026-09-24).

GPT'ye giden hiçbir metinde kargo/tanker/container gemisi geçmemeli: DeepMyster'ın
7 domain'inde bu gemiler yok, ama kütüphane ve prompt'lar üzerinden sızıyorlardı.
Gerçek API çağrısı yapılmaz; _call_gpt mock'lanır.
"""
import asyncio
import os
import re
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.creative_engine import (
    DEEPMYSTER_EXISTING_IDEAS_LIBRARY,
    DOMAIN_ATTRIBUTES,
    DOMAIN_CAST_RANGES,
    ENV_CENTRIC_DOMAINS,
    MARITIME_INSPIRATION_DOMAINS,
    VESSEL_UNIVERSE,
    YOUTUBE_METADATA_SYSTEM,
    build_prompt_simplifier_system,
    build_scenario_writer_system,
    choose_camera_archetype,
    get_creative_catalyst,
)
import core.creative_engine as ce
import core.prompt_generator as pg
import core.prompt_sanitizer as ps

# 2026-09-24 genişletme: trawler, tug(boat), freight(er), truck/trailer/lorry (TIR yok,
# ferry'de sadece araba). Kelime başı sınırı: "freight" hem freight hem freighter'ı yakalar.
FORBIDDEN = re.compile(
    r"cargo|container|tanker|bulk|barge|pctc|trawler|\btug|\bfreight|\btrucks?\b|\btrailers?\b|\blorry\b|\blorries\b",
    re.IGNORECASE,
)
ALL_DOMAINS = list(MARITIME_INSPIRATION_DOMAINS)


def _catalyst_for(domain_id: str) -> dict:
    """Diğer 6 domain'i geçmişe koyarak rotasyonu tek domain'e zorlar."""
    # Rotasyon sadece geçerli combo sayar (5 parça + evrendeki gemi veya none).
    ship = lambda d: (DOMAIN_ATTRIBUTES[d]["ships"] or ["none"])[0].lower()
    history = [f"{d}|{ship(d)}|x|x|fixed_cctv" for d in ALL_DOMAINS if d != domain_id]
    catalyst = get_creative_catalyst(recent_history=history)
    assert catalyst["domain_id"] == domain_id
    return catalyst


class TestCargoFree(unittest.TestCase):

    def assertNoCargo(self, text: str, where: str):
        hits = FORBIDDEN.findall(text)
        self.assertEqual(hits, [], f"{where}: yasak kelime {hits}")

    def test_writer_system_prompts(self):
        for d in ALL_DOMAINS:
            with self.subTest(domain=d):
                self.assertNoCargo(build_scenario_writer_system(15, d), f"writer/{d}")

    def test_writer_never_names_forbidden_vessel(self):
        """Yasak bile olsa telaffuz edilmez: eski kural 6 'NEVER spawn a fishing trawler' diyordu."""
        for d in ALL_DOMAINS:
            with self.subTest(domain=d):
                self.assertNotRegex(build_scenario_writer_system(15, d), r"(?i)fishing|trawler")

    def test_simplifier_system_prompts(self):
        for d in ALL_DOMAINS:
            with self.subTest(domain=d):
                self.assertNoCargo(build_prompt_simplifier_system(15, d), f"simplifier/{d}")

    def test_metadata_system_prompt(self):
        self.assertNoCargo(YOUTUBE_METADATA_SYSTEM, "metadata")

    def test_inspiration_library(self):
        rows = [r for cat in DEEPMYSTER_EXISTING_IDEAS_LIBRARY.values() for r in cat["reference_scenarios"]]
        self.assertEqual(len(rows), 71)
        for cat in DEEPMYSTER_EXISTING_IDEAS_LIBRARY.values():
            self.assertNoCargo(cat["title"], "kütüphane başlığı")
        for r in rows:
            with self.subTest(row=r[:50]):
                self.assertNoCargo(r, "kütüphane")

    def test_generate_scenario_messages(self):
        """_generate_scenario'nun GPT'ye yolladığı system + user mesajı, 7 domain × 3 kamera."""
        mock = AsyncMock(return_value={"visible_start": "A wave slams the bow."})
        with patch.object(pg, "_call_gpt", mock):
            for d in ALL_DOMAINS:
                for cam in ["fixed_cctv", "bystander_handheld", "chase_pov"]:
                    if cam == "chase_pov" and d in ENV_CENTRIC_DOMAINS:
                        continue
                    with self.subTest(domain=d, camera=cam):
                        mock.reset_mock()
                        asyncio.run(pg._generate_scenario(_catalyst_for(d), cam))
                        system_prompt, user_message = mock.call_args.args[:2]
                        self.assertNoCargo(system_prompt, f"system/{d}")
                        self.assertNoCargo(user_message, f"user/{d}/{cam}")

    def test_simplify_fallback_defaults(self):
        """Senaryo alanları boşsa kullanılan varsayılanlar; yedek prompt 2026-09-24'te kaldırıldı (boş döner)."""
        mock = AsyncMock(return_value={})
        with patch.object(pg, "_call_gpt", mock):
            result = asyncio.run(pg._simplify_prompt({}, {"domain_id": "ferry_operations"}))
        self.assertNoCargo(mock.call_args.args[1], "simplifier user")
        self.assertEqual(result["prompt"], "")

    def test_domain_definitions(self):
        """Domain guidance + example_elements, GPT user mesajına birebir gider."""
        for d, data in MARITIME_INSPIRATION_DOMAINS.items():
            with self.subTest(domain=d):
                self.assertNoCargo(data["guidance"], f"guidance/{d}")
                self.assertNoCargo(" | ".join(data["example_elements"]), f"example_elements/{d}")

    def test_sanitizer_system_prompts(self):
        """Pre-flight güvenlik ve retry-rewrite GPT'lerinin system prompt'ları."""
        self.assertNoCargo(ps._PREFLIGHT_SYSTEM, "sanitizer preflight")
        self.assertNoCargo(ps._RETRY_REWRITE_SYSTEM, "sanitizer retry")

    def test_dry_run_output(self):
        """DRY-RUN mock'u main.py tarafından Notion'a (topic + combo_key) yazılır."""
        out = pg._dry_run_output()
        texts = [s["prompt"] for s in out["scenes"]] + [
            out["youtube_title"], out["youtube_description"], " ".join(out["tags"]),
            out["scenario_summary"], out["combo_key"], out["animal"], out["talent"], out["category"],
        ]
        for t in texts:
            self.assertNoCargo(t, "dry-run mock")
        parts = out["combo_key"].split("|")
        self.assertEqual(len(parts), 5, "combo_key güncel 5 parçalı formatta olmalı")
        self.assertIn(parts[0], MARITIME_INSPIRATION_DOMAINS)
        self.assertEqual(out["category"], parts[0])

    def test_realism_guardrails_source(self):
        """Ölü dal çıktı üretmez, bu yüzden kaynak taranır (fishing/trawler, arctic/ice)."""
        import inspect
        src = inspect.getsource(ce.get_realism_guardrails)
        self.assertNoCargo(src, "get_realism_guardrails kaynak")
        self.assertNotRegex(src, r"(?i)fishing|arctic", "ölü domain dalı geri gelmiş")
        for d, attrs in ce.DOMAIN_ATTRIBUTES.items():
            for ship in attrs["ships"] or ["None"]:
                with self.subTest(domain=d, ship=ship):
                    self.assertNoCargo(ce.get_realism_guardrails(d, ship), f"guardrail/{d}")


class TestCastRanges(unittest.TestCase):

    def test_vessel_domains_get_their_range(self):
        for d, (lo, hi) in DOMAIN_CAST_RANGES.items():
            with self.subTest(domain=d):
                s = build_scenario_writer_system(15, d)
                self.assertIn(f"approximately {lo}-{hi} people", s)
                self.assertIn(f"Do not exceed {hi}.", s)
                self.assertNotIn("MAXIMUM 2", s)
                self.assertNotIn("Maximum 2 people", s)
                self.assertIn("close estimate", s)

    def test_env_centric_domains(self):
        for d in ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                s = build_scenario_writer_system(15, d)
                self.assertIn("ENVIRONMENT-CENTRIC (CAST OPTIONAL)", s)
                self.assertNotIn("CAST SIZE", s)

    def test_unknown_domain_raises(self):
        for bad in ["", "cargo_operations", "Ferry_Operations"]:
            with self.subTest(domain=bad):
                with self.assertRaises(RuntimeError):
                    build_scenario_writer_system(15, bad)

    def test_every_domain_covered(self):
        """Import-anı kontrolünün garanti ettiği şey: 7 domain'in hepsi bir kurala sahip."""
        covered = set(DOMAIN_CAST_RANGES) | set(ENV_CENTRIC_DOMAINS)
        self.assertEqual(covered, set(ALL_DOMAINS))
        self.assertEqual(set(DOMAIN_CAST_RANGES) & set(ENV_CENTRIC_DOMAINS), set())


class TestVesselUniverse(unittest.TestCase):

    EXPECTED = [
        "Cruise Tender Boat", "High-speed Catamaran", "Jet Ski", "Luxury Motor Yacht",
        "Mega Cruise Ship", "Ocean Cruise Liner", "Passenger Car Ferry",
        "Runaway Powerboat", "Sailing Yacht", "Vessel on Slipway",
    ]

    def test_expected_ships(self):
        self.assertEqual(VESSEL_UNIVERSE, self.EXPECTED)

    def test_derived_from_domain_attributes(self):
        from core.creative_engine import DOMAIN_ATTRIBUTES
        pooled = {s for a in DOMAIN_ATTRIBUTES.values() for s in a["ships"]}
        self.assertEqual(set(VESSEL_UNIVERSE), pooled)

    def test_universe_reaches_user_message(self):
        mock = AsyncMock(return_value={})
        with patch.object(pg, "_call_gpt", mock):
            asyncio.run(pg._generate_scenario(_catalyst_for("ferry_operations"), "fixed_cctv"))
        user_message = mock.call_args.args[1]
        self.assertIn(", ".join(self.EXPECTED), user_message)


if __name__ == "__main__":
    unittest.main()
