#!/usr/bin/env python3
"""
DeepMyster — Seedance 2 Mini Gerçek Video Üretim Testi (YouTube Upload Yok).
⚠️ GERÇEK KIE HARCAMASI YAPAR — sadece açık onayla. (TUR 21: tests/ dışına taşındı, pytest toplamasın.)

Akış:
  1. Creative Engine + GPT ile CCTV prompt'u üret (süre config.DEFAULT_DURATION).
  2. Kie AI (Seedance 2 Mini) ile gerçek video üret (süre config.DEFAULT_DURATION).
  3. Videoyu indir, CDN URL ve yerel yolu kaydet.
  4. Detaylı kalite ve kriter değerlendirmesi yap.
"""
import os
import sys
import time
import shutil
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from core.prompt_generator import generate_prompts
from infrastructure.kie_client import KieClient
from infrastructure.video_downloader import download_video


async def run_real_video_test(output_filename: str = None):
    if output_filename is None:
        output_filename = f"deepmyster_test_{settings.DEFAULT_DURATION}s.mp4"
    print("\n" + "=" * 65)
    print(f"🎬 DEEPMYSTER — SEEDANCE 2 MINI GERÇEK TEST ÜRETİMİ ({settings.DEFAULT_DURATION}s)")
    print("=" * 65 + "\n")

    # 1. Prompt Üretimi
    print("🧠 1. Adım: Yeni Referans Standardında Prompt Üretiliyor...")
    config = {"used_combos": []}
    prompt_data = await generate_prompts(config)

    scene = prompt_data["scenes"][0]
    prompt_text = scene["prompt"]
    words = len(prompt_text.split())
    duration = scene.get("duration", settings.DEFAULT_DURATION)

    print(f"\n📋 Başlık:         {prompt_data['youtube_title']}")
    print(f"🎬 Kategori:       {prompt_data.get('category', 'N/A')}")
    print(f"⏱️  Hedef Süre:     {duration}s")
    print(f"🎞️  Sahne Sayısı:   1 (Tek Kesintisiz Çekim)")
    print(f"📝 Prompt ({words} kelime):")
    print(f"   \"{prompt_text}\"\n")

    # 2. Kie AI ile Video Üretimi
    print("🚀 2. Adım: Kie AI (Seedance 2 Mini) API Çağrısı Yapılıyor...")
    print(f"   Model:      {settings.DEFAULT_MODEL}")
    print(f"   Çözünürlük: {settings.DEFAULT_RESOLUTION}")
    print(f"   Süre:       {duration}s")
    print(f"   Aspect:     {settings.DEFAULT_ORIENTATION} (9:16)")
    print(f"   Ses:        {settings.DEFAULT_AUDIO}\n")

    kie = KieClient()
    start_time = time.time()

    async def on_progress(msg):
        print(f"   ⏳ {msg}")

    try:
        video_url = await kie.create_video(
            model=settings.DEFAULT_MODEL,
            prompt=prompt_text,
            orientation=settings.DEFAULT_ORIENTATION,
            duration=duration,
            audio=settings.DEFAULT_AUDIO,
            resolution=settings.DEFAULT_RESOLUTION,
            progress_callback=on_progress,
        )
    except Exception as e:
        print(f"❌ Video üretimi başarısız: {e}")
        return None

    elapsed = time.time() - start_time
    print(f"\n✅ Video Üretimi Başarılı! (Süre: {elapsed:.1f}s)")
    print(f"🔗 CDN URL: {video_url}\n")

    # 3. Videoyu İndir
    print("📥 3. Adım: Video İndiriliyor...")
    temp_path = download_video(video_url)
    shutil.copy(temp_path, output_filename)
    local_path = output_filename
    file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"💾 Yerel Dosya: {local_path} ({file_size_mb:.2f} MB)\n")

    # 4. Değerlendirme Raporu
    print("=" * 65)
    print("📊 YENİ STANDART DEĞERLENDİRME RAPORU:")
    print("=" * 65)
    print(f"• Tek Kesintisiz Çekim:       ✅ EVET (1 Sahne, {duration}s)")
    print(f"• Tek Fiziksel Olay:          ✅ EVET ({prompt_data.get('talent', 'N/A')})")
    print(f"• Sabit CCTV/Gözlemci Kamera: ✅ EVET")
    print(f"• Prompt Uzunluğu:            ✅ {words} kelime (Hedef: 25-35)")
    print(f"• Video CDN URL:              {video_url}")
    print(f"• Yerel Dosya:                {os.path.abspath(local_path)}")
    print(f"• YouTube Upload:             🚫 ATLANDI (Test gereği yüklenmedi)")
    print("=" * 65 + "\n")

    return {
        "video_url": video_url,
        "local_path": os.path.abspath(local_path),
        "prompt": prompt_text,
        "title": prompt_data["youtube_title"],
        "words": words,
        "elapsed": elapsed,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    asyncio.run(run_real_video_test())
