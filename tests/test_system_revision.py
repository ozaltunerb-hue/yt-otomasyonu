#!/usr/bin/env python3
"""
DeepMyster Doğukan Metodolojisi & Yaratıcı Serbestlik Standardı — Test Paketi.

Testler:
  1. 10 Geniş Denizcilik İlham Alanı ve Yapısı
  2. 71 Senaryoluk DeepMyster İlham & Fikir Kütüphanesi (8 Kategori, artık eşit uzunlukta değil)
  3. Yaratıcı Katalizör Üretimi, Kütüphane & Negatif Geçmiş Entegrasyonu
  4. Sessiz Ekran Görünürlük Kontrolü
  5. Dry-Run Prompt Formatı (25–45 Kelime, DEFAULT_DURATION Tek Sahne)
  6. Cerrahi Prompt Sanitizer Güvenlik Testi
  7. Katalizör Çeşitlilik Dağılımı
  8. Aksiyon/Tehlike Yoğunluğu Kontrolü (Sakin/Statik Sahne Reddi)
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from core.creative_engine import (
    MARITIME_INSPIRATION_DOMAINS,
    DEEPMYSTER_EXISTING_IDEAS_LIBRARY,
    get_creative_catalyst,
)
from core.prompt_generator import (
    generate_prompts,
    _dry_run_output,
    validate_silent_visibility,
    validate_high_action,
)
from core.prompt_sanitizer import sanitize_prompt


class TestDeepMysterCreativeFreedom(unittest.TestCase):

    def test_01_domains_structure(self):
        """10 geniş denizcilik ilham alanı mevcut ve eksiksiz olmalı."""
        self.assertGreaterEqual(len(MARITIME_INSPIRATION_DOMAINS), 10)
        for domain_key, domain_data in MARITIME_INSPIRATION_DOMAINS.items():
            self.assertIn("title", domain_data)
            self.assertIn("guidance", domain_data)
            self.assertIn("example_elements", domain_data)
            self.assertIn("camera_styles", domain_data)
            self.assertGreaterEqual(len(domain_data["example_elements"]), 4)
            self.assertGreaterEqual(len(domain_data["camera_styles"]), 2)

    def test_02_ideas_library_structure(self):
        """71 senaryoluk DeepMyster fikir kütüphanesi 8 kategoride mevcut olmalı (kategoriler artık eşit uzunlukta değil)."""
        self.assertEqual(len(DEEPMYSTER_EXISTING_IDEAS_LIBRARY), 8)
        total_scenarios = 0
        for cat_key, cat_data in DEEPMYSTER_EXISTING_IDEAS_LIBRARY.items():
            self.assertIn("title", cat_data)
            self.assertIn("reference_scenarios", cat_data)
            self.assertGreaterEqual(len(cat_data["reference_scenarios"]), 7)
            total_scenarios += len(cat_data["reference_scenarios"])
        self.assertEqual(total_scenarios, 71)

    def test_03_catalyst_generation_with_library_and_history(self):
        """Katalizör üretimi hem fikir kütüphanesini hem negatif geçmişi doğru iletmeli."""
        mock_history = ["arctic_ice_navigation", "heavy_lift_and_project_cargo"]
        catalyst = get_creative_catalyst(recent_history=mock_history)
        self.assertIn("domain_id", catalyst)
        self.assertIn("domain_title", catalyst)
        self.assertIn("guidance", catalyst)
        self.assertIn("example_elements", catalyst)
        self.assertIn("camera_styles", catalyst)
        self.assertIn("existing_library_reference", catalyst)
        self.assertIn("recent_history", catalyst)
        self.assertGreaterEqual(len(catalyst["existing_library_reference"]), 5)

    def test_04_silent_visibility_validator(self):
        """Görünmez sualtı/makine durumları reddedilmeli, görünür eylemler geçmeli."""
        valid_scenario = {
            "scenario_summary": "A mooring line snaps under heavy swell strain and whips across the quay.",
            "scene_description": "From quayside CCTV, the line stretches and breaks.",
            "physical_movement": "line whipping across concrete",
            "visible_consequence": "resting limp on pier",
        }
        is_valid, failures = validate_silent_visibility(valid_scenario)
        self.assertTrue(is_valid)
        self.assertEqual(len(failures), 0)

        invalid_scenario = {
            "scenario_summary": "Underwater rudder failure occurs while engine room blackout disables sonar.",
            "scene_description": "Submerged shaft stops spinning under water.",
        }
        is_valid, failures = validate_silent_visibility(invalid_scenario)
        self.assertFalse(is_valid)
        self.assertGreater(len(failures), 0)

    def test_05_dry_run_output_structure(self):
        """Dry-run çıktısı 1 sahne, DEFAULT_DURATION ve 25-45 kelimelik prompt içermeli."""
        out = _dry_run_output()
        self.assertEqual(len(out["scenes"]), 1)
        self.assertEqual(out["scenes"][0]["duration"], settings.DEFAULT_DURATION)
        self.assertEqual(out["total_duration"], settings.DEFAULT_DURATION)

        words = out["scenes"][0]["prompt"].split()
        self.assertGreaterEqual(len(words), 25)
        self.assertLessEqual(len(words), 45)

    def test_06_sanitizer_surgical_accuracy(self):
        """Sanitizer riskli insan şiddetini temizlerken doğal denizcilik gerilimini korumalı."""
        raw = "A crewman with a knife encounters a violent storm wave crashing on deck"
        sanitized, changes = sanitize_prompt(raw)
        self.assertNotIn("knife", sanitized.lower())
        self.assertIn("crash", sanitized.lower())
        self.assertGreater(len(changes), 0)

    def test_07_catalyst_diversity_distribution(self):
        """10 ardışık katalizör çağrısında zengin alan dağılımı sağlanmalı."""
        used = []
        domains_seen = set()
        for _ in range(10):
            cat = get_creative_catalyst(recent_history=used)
            used.append(cat["domain_id"])
            domains_seen.add(cat["domain_id"])

        self.assertGreaterEqual(len(domains_seen), 4)

    def test_08_high_action_validator(self):
        """Sakin/rutin senaryolar reddedilmeli, aktif tehlike içeren senaryolar geçmeli."""
        calm_scenario = {
            "scenario_summary": "A delivery truck is driving onto the ferry ramp during routine loading operations.",
            "physical_movement": "The truck driver waits calmly while dock staff standing by wave it forward during normal operations.",
            "visible_consequence": "The truck finishes parking in its assigned spot with nothing further happening.",
        }
        is_valid, failures = validate_high_action(calm_scenario)
        self.assertFalse(is_valid)
        self.assertGreater(len(failures), 0)

        active_scenario = {
            "scenario_summary": "A mooring line snaps under heavy swell strain and whips violently across the quay.",
            "physical_movement": "The line whips across the deck as dockworkers scramble clear of the recoiling cable.",
            "visible_consequence": "The parted line finally goes slack, coiled dangerously near the bollard.",
        }
        is_valid, failures = validate_high_action(active_scenario)
        self.assertTrue(is_valid)
        self.assertEqual(len(failures), 0)


if __name__ == "__main__":
    unittest.main()
