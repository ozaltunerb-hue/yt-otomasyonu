#!/usr/bin/env python3
"""
Preflight kapısı (gpt_preflight_check), 2026-09-24 TUR 7.

Eskiden bozuk JSON / eksik alan / rewrite'sız riskli cevap prompt'u sessizce Kie'ye geçiriyordu.
Şimdi: 1 + PREFLIGHT_MAX_RETRIES deneme, hiçbiri geçmezse PreflightError; Kie task'ı açılmaz.
Gerçek API çağrısı yapılmaz; openai.AsyncOpenAI mock'lanır.
"""
import asyncio
import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.prompt_sanitizer import PREFLIGHT_MAX_RETRIES, PreflightError, gpt_preflight_check

PROMPT = "The vessel lurches forward on the slipway, startling three workers in orange coveralls."
SAFE = json.dumps({"safe": True, "risk_score": 1, "risk_reasons": []})
BROKEN = '{"safe": true, "risk_score": 1, "risk_reasons": ["unterminated'
REWRITE = "The vessel slides forward on the slipway as three workers in orange coveralls step back."


def _resp(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def run_preflight(*outputs):
    """outputs: sırayla GPT cevapları (str) veya fırlatılacak Exception. Dönüş: (sonuç|hata, create mock)."""
    create = AsyncMock(side_effect=[o if isinstance(o, Exception) else _resp(o) for o in outputs])
    client = MagicMock()
    client.chat.completions.create = create
    with patch("openai.AsyncOpenAI", return_value=client):
        try:
            return asyncio.run(gpt_preflight_check(PROMPT)), create
        except PreflightError as e:
            return e, create


class TestPreflightGate(unittest.TestCase):
    def test_valid_safe_single_call(self):
        (prompt, rewritten, meta), create = run_preflight(SAFE)
        self.assertEqual(create.await_count, 1)
        self.assertEqual(prompt, PROMPT)
        self.assertFalse(rewritten)
        self.assertEqual(meta["attempts"], 1)

    def test_broken_json_then_valid_retries(self):
        (prompt, _, meta), create = run_preflight(BROKEN, SAFE)
        self.assertEqual(create.await_count, 2)
        self.assertEqual(prompt, PROMPT)
        self.assertEqual(meta["attempts"], 2)
        retry_msg = create.await_args_list[1].kwargs["messages"][1]["content"]
        self.assertIn("previous answer was invalid", retry_msg)
        self.assertIn("bozuk JSON", retry_msg)

    def test_broken_json_all_attempts_raises(self):
        err, create = run_preflight(*[BROKEN] * (1 + PREFLIGHT_MAX_RETRIES))
        self.assertIsInstance(err, PreflightError)
        self.assertEqual(create.await_count, 3)

    def test_missing_safe_field_not_treated_as_safe(self):
        no_safe = json.dumps({"risk_score": 2, "risk_reasons": []})
        err, create = run_preflight(no_safe, no_safe, no_safe)
        self.assertIsInstance(err, PreflightError)
        self.assertIn("safe", str(err))

    def test_bad_risk_score_retries(self):
        (prompt, _, _), create = run_preflight(json.dumps({"safe": True, "risk_score": "low"}), SAFE)
        self.assertEqual(create.await_count, 2)
        self.assertEqual(prompt, PROMPT)

    def test_risky_with_rewrite_returns_rewrite(self):
        risky = json.dumps({"safe": False, "risk_score": 7, "risk_reasons": ["x"], "rewritten_prompt": REWRITE})
        (prompt, rewritten, meta), create = run_preflight(risky)
        self.assertEqual(prompt, REWRITE)
        self.assertTrue(rewritten)
        self.assertTrue(meta["rewritten"])

    def test_risky_without_rewrite_raises(self):
        risky = json.dumps({"safe": False, "risk_score": 7, "risk_reasons": ["x"]})
        err, create = run_preflight(risky, risky, risky)
        self.assertIsInstance(err, PreflightError)
        self.assertEqual(create.await_count, 3)

    def test_unsafe_low_score_passes_without_rewrite(self):
        # Mevcut eşik korunur: safe=false ama skor<=4 geçer, rewrite gerekmez
        (prompt, rewritten, _), _ = run_preflight(json.dumps({"safe": False, "risk_score": 3, "risk_reasons": []}))
        self.assertEqual(prompt, PROMPT)
        self.assertFalse(rewritten)

    def test_api_exception_all_attempts_raises(self):
        err, create = run_preflight(RuntimeError("timeout"), RuntimeError("timeout"), RuntimeError("timeout"))
        self.assertIsInstance(err, PreflightError)
        self.assertEqual(create.await_count, 3)


class TestKieClientStopsOnPreflightError(unittest.TestCase):
    def test_no_kie_task_when_preflight_fails(self):
        from config import settings
        from infrastructure.kie_client import KieClient
        client = KieClient()
        with patch.object(settings, "IS_DRY_RUN", False), \
             patch("core.prompt_sanitizer.gpt_preflight_check", AsyncMock(side_effect=PreflightError("x"))), \
             patch.object(KieClient, "_create_task", AsyncMock()) as create_task:
            with self.assertRaises(PreflightError):
                asyncio.run(client.create_video(model=settings.DEFAULT_MODEL, prompt=PROMPT))
            create_task.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
