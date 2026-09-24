#!/usr/bin/env python3
"""TUR 21: dokümanlar kodla senkron. TUR 15'ten sonra H/I/J ve "Beat1 Fiil" README'ye girmemişti.
Yeni simplifier kapısı veya Notion alanı eklenip README güncellenmezse bu test kırılır."""
import os
import re
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from core.prompt_generator import SIMPLIFIER_GATES


def _read(name):
    return open(os.path.join(ROOT, name), encoding="utf-8").read()


class TestDocsSync(unittest.TestCase):
    def test_every_gate_in_readme_table(self):
        readme = _read("README.md")
        for letter in SIMPLIFIER_GATES:
            with self.subTest(gate=letter):
                self.assertRegex(readme, rf"(?m)^\| {letter} \| \S")

    def test_every_gate_in_baslangic(self):
        text = _read("BASLANGIC.md")
        for letter in SIMPLIFIER_GATES:
            with self.subTest(gate=letter):
                self.assertRegex(text, rf"\b{letter} [a-zçğıöşüA-Z]")

    def test_every_notion_property_in_readme(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup_notion_db", os.path.join(ROOT, "setup_notion_db.py"))
        src = open(spec.origin, encoding="utf-8").read()
        block = src[src.index("DATABASE_PROPERTIES = {"):]
        block = block[:block.index("\n}\n")]
        props = re.findall(r'^\s{4}"([^"]+)":', block, re.M)
        self.assertIn("Beat1 Fiil", props)
        readme = _read("README.md")
        for p in props:
            with self.subTest(prop=p):
                self.assertRegex(readme, rf"(?m)^\| {re.escape(p)} \|")


if __name__ == "__main__":
    unittest.main()
