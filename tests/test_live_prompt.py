#!/usr/bin/env python3
"""
DeepMyster — Gerçek GPT Prompt Üretim ve Doğukan Standardı Doğrulama Testi.
"""
import os
import sys
import asyncio

# UTF-8 stdout encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.prompt_generator import generate_prompts
from core.creative_engine import STYLE_LOCK_SUFFIX

# Doğukan hedefi (25-45 kelime) artık sabit stil kilidi eklendikten SONRAKİ
# nihai prompt'a uygulanıyor — bu yüzden beklenen aralık stil kilidinin
# kelime sayısı kadar kaydırılır.
_STYLE_LOCK_WORDS = len(STYLE_LOCK_SUFFIX.split())
_MIN_WORDS = 25 + _STYLE_LOCK_WORDS
_MAX_WORDS = 45 + _STYLE_LOCK_WORDS


async def test_live_prompt_generation():
    print("\n🔍 GPT-4o ile Doğukan Standardında Canlı Prompt Üretim Testi Başlatılıyor...")
    config = {"used_combos": []}
    
    result = await generate_prompts(config)
    
    print("\n" + "=" * 60)
    print("CANLI ÜRETİM SONUCU:")
    print("=" * 60)
    print(f"YouTube Başlığı: {result['youtube_title']}")
    print(f"Açıklama:       {result['youtube_description']}")
    print(f"Etiketler:       {', '.join(result['tags'])}")
    print(f"Senaryo Özeti:   {result['scenario_summary']}")
    print(f"Gemi Sınıfı:     {result.get('animal', 'N/A')}")
    print(f"Olay Türü:       {result.get('talent', 'N/A')}")
    print(f"Toplam Süre:     {result['total_duration']}s")
    print(f"Sahne Sayısı:    {len(result['scenes'])}")
    
    for i, sc in enumerate(result['scenes'], 1):
        prompt = sc['prompt']
        words = prompt.split()
        print(f"\n--- Sahne {i} ({sc['duration']}s) ---")
        print(f"Prompt ({len(words)} kelime): {prompt}")
        
        is_len_ok = _MIN_WORDS <= len(words) <= _MAX_WORDS
        has_camera = any(w in prompt.lower() for w in ["cctv", "camera", "surveillance", "angle", "view", "footage"])
        print(f"  • Kelime Sayısı ({_MIN_WORDS}-{_MAX_WORDS} hedef, stil kilidi dahil): {'[UYGUN]' if is_len_ok else '[SINIRDA]'} ({len(words)} kelime)")
        print(f"  • Sabit/CCTV Kamera İbaresi:  {'[VAR]' if has_camera else '[EKSIK]'}")

    print("=" * 60 + "\n")
    return result


if __name__ == "__main__":
    asyncio.run(test_live_prompt_generation())
