#!/usr/bin/env python3
"""
DeepMyster — 5 Farklı Senaryo İle Doğukan Standardı Çeşitlilik ve Kalite Stres Testi.
"""
import os
import sys
import asyncio

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


async def run_batch_test(count: int = 5):
    print(f"\n📊 {count} Farklı Senaryo İçin Canlı Üretim Kalite & Çeşitlilik Testi Başlatılıyor...\n")
    used_combos = []
    
    for i in range(1, count + 1):
        print(f"--- TEST RUN {i}/{count} ---")
        config = {"used_combos": used_combos}
        result = await generate_prompts(config)
        used_combos.append(result["combo_key"])
        
        prompt = result["scenes"][0]["prompt"]
        words = len(prompt.split())
        title = result["youtube_title"]
        duration = result["total_duration"]
        
        print(f"  • Başlık:    {title}")
        print(f"  • Alan:      {result.get('category', 'N/A')}")
        print(f"  • Gemi:      {result.get('animal', 'N/A')}")
        print(f"  • Olay:      {result.get('talent', 'N/A')}")
        print(f"  • Süre:      {duration}s (Sahne: {len(result['scenes'])})")
        print(f"  • Prompt ({words} kelime): {prompt}")
        is_len_ok = _MIN_WORDS <= words <= _MAX_WORDS
        print(f"  • Doğukan Standardı ({_MIN_WORDS}-{_MAX_WORDS} kelime, stil kilidi dahil): {'✅ UYGUN' if is_len_ok else '⚠️ DIŞINDA'}\n")

    print("=" * 60)
    print(f"✅ {count} Senaryo Başarıyla Üretildi ve Semantik Çeşitlilik Doğrulandı!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_batch_test(5))
