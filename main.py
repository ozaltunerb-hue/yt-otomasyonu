#!/usr/bin/env python3
from __future__ import annotations

"""
YouTube Otomasyonu V3 — "DeepMyster" Yeni Referans Standardı Pipeline
===================================================================
Her gün otomatik çalışır: tek kesintisiz çekim fiziksel olay senaryosu üretir (süre config.DEFAULT_DURATION ile kontrol edilir) →
Seedance 2 Mini ile video üretir → YouTube Shorts olarak yükler.

Telegram YOK — CronJob ile tetiklenir, insan müdahalesi gerektirmez.

Çalıştırma:
  python main.py                → Tam pipeline (CronJob bu komutu çalıştırır)
  python main.py --dry-run      → Gerçek üretim yapmadan mock test
  python main.py --no-upload    → Gerçek video üret ama YouTube'a yükleme (Lokal test)
  python main.py --check        → Sistem sağlık kontrolü

Railway CronJob: `python main.py` — iş günleri 16:30 TR (13:30 UTC) tetiklenir.
"""
import os
import sys
import time
import asyncio
import logging
import argparse
import shutil

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from logger import get_logger
from core.prompt_generator import generate_prompts, NoValidScenarioError
from infrastructure.kie_client import KieClient, ContentFilterError
from infrastructure.motion_profile import motion_profile, format_motion
from infrastructure.replicate_merger import merge_videos
from infrastructure.video_downloader import download_video, cleanup_video
from infrastructure.youtube_uploader import upload_to_youtube
from infrastructure.notion_logger import NotionTracker

log = get_logger("DeepMyster")


# ────────────────────────────────────────
# 📋 TEKRAR ÖNLEME (Notion-backed)
# ────────────────────────────────────────

def load_used_combos() -> list[str]:
    """
    Notion'dan son 60 günün kullanılan combo_key'lerini yükler.
    Fail-fast: Notion erişilemezse hata verir.
    """
    tracker = NotionTracker()
    combos = tracker.get_used_combos(days=60)
    log.info(f"📋 Son 60 günde {len(combos)} benzersiz senaryo kullanılmış")
    return combos


# ────────────────────────────────────────
# ⚙️ ANA PİPELINE
# ────────────────────────────────────────

async def run_pipeline(dry_run: bool = False, skip_upload: bool = False, output_path: str = ""):
    """
    Tam otonom video üretim pipeline'ı.

    Akış:
      1. Tekrar önleme → kullanılan senaryoları yükle
      2. Creative Engine + GPT → tek çekim senaryo + prompt üret (DEFAULT_DURATION saniye)
      3. Seedance 2 Mini → video üret (tek kesintisiz çekim, DEFAULT_DURATION saniye)
      4. YouTube → Shorts olarak yükle (skip_upload=False ise)
      5. Notion → log kaydet
    """
    if dry_run:
        settings.IS_DRY_RUN = True
        settings.ENV = "development"

    upload_active = settings.YOUTUBE_ENABLED and not skip_upload

    mode = "DRY-RUN" if settings.IS_DRY_RUN else "PRODUCTION"
    log.info(f"🚀 DeepMyster V3 (Yeni Referans Standardı) başlatılıyor... (Mod: {mode})")
    log.info(f"   Model: {settings.DEFAULT_MODEL} | Hedef Süre: {settings.DEFAULT_DURATION}s")
    log.info(f"   YouTube Upload: {'Aktif' if upload_active else 'Devre Dışı (Skip Upload / Test)'}")
    log.info(f"   Notion Log: {'Aktif' if settings.NOTION_ENABLED else 'Devre Dışı'}")

    # ── Tekrar önleme & Semantik Negatif Hafıza ──
    used_combos = load_used_combos()
    tracker = NotionTracker()
    recent_topics = tracker.get_recent_history(days=30)
    if recent_topics:
        log.info(f"🧠 Son 30 günden {len(recent_topics)} semantik konu negatif hafızaya eklendi")

    # ── Content filter retry — 3 farklı senaryo dene ──
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            result = await _execute_pipeline(
                used_combos,
                recent_topics=recent_topics,
                upload_active=upload_active,
                output_path=output_path,
            )
            return result
        except ContentFilterError as cfe:
            last_error = cfe
            rejected_combo = getattr(cfe, "combo_key", "")
            if rejected_combo and rejected_combo not in used_combos:
                used_combos.append(rejected_combo)
                log.info(f"🚫 Reddedilen combo dedup listesine eklendi: {rejected_combo}")
            if attempt < max_retries - 1:
                log.warning(
                    f"🛡️ İçerik filtresi reddetti (deneme {attempt + 1}/{max_retries}). "
                    f"Farklı senaryo ile tekrar denenecek..."
                )
            else:
                log.error(f"❌ {max_retries} farklı senaryo denendi, hepsi reddedildi.")
                return {"success": False, "error": str(last_error)}

    return {"success": False, "error": "Tüm denemeler başarısız"}


async def _execute_pipeline(
    used_combos: list[str],
    recent_topics: list[str] | None = None,
    upload_active: bool = True,
    output_path: str = "",
) -> dict:
    """
    Pipeline'ın asıl implementasyonu.
    """
    tracker = NotionTracker()
    kie = KieClient()
    video_paths = []
    start_time = time.time()
    combo_key = ""

    pipeline_config = {
        "used_combos": used_combos,
        "recent_topics": recent_topics or [],
    }

    try:
        # ── ADIM 1: Prompt üret (Creative Engine + GPT) ──
        log.info(f"🧠 Yaratıcı motor çalışıyor (Tek {settings.DEFAULT_DURATION}s kesintisiz çekim standardı)...")
        prompt_data = await generate_prompts(pipeline_config)

        scenes = prompt_data.get("scenes", [])
        combo_key = prompt_data.get("combo_key", "")
        clip_count = len(scenes)
        total_duration = prompt_data.get("total_duration", settings.DEFAULT_DURATION)

        log.info(f"🎬 Senaryo: {prompt_data.get('scenario_summary', '')}")
        log.info(f"   {clip_count} sahne, {total_duration}s | Başlık: {prompt_data.get('youtube_title', '')}")
        log.info(f"   Prompt: {scenes[0]['prompt'] if scenes else ''}")

        # ── ADIM 2: Notion entry ──
        notion_config = {
            "topic": prompt_data.get("scenario_summary", "DeepMyster maritime physical incident"),
            "model": settings.DEFAULT_MODEL,
            "clip_count": clip_count,
            "orientation": settings.DEFAULT_ORIENTATION,
            "audio": settings.DEFAULT_AUDIO,
            "combo_key": combo_key,
        }
        await asyncio.to_thread(tracker.create_entry, notion_config, trigger="auto")
        await asyncio.to_thread(tracker.update_with_prompts, prompt_data)

        # ── ADIM 3: Video üret (Seedance 2 Mini) ──
        log.info(f"🎬 Video üretimi başlıyor ({settings.DEFAULT_MODEL}, {settings.DEFAULT_DURATION}s)...")
        await asyncio.to_thread(tracker.update_status, "Video Üretiliyor")

        video_url = await kie.create_video(
            model=settings.DEFAULT_MODEL,
            prompt=scenes[0]["prompt"],
            orientation=settings.DEFAULT_ORIENTATION,
            duration=scenes[0].get("duration", settings.DEFAULT_DURATION),
            audio=settings.DEFAULT_AUDIO,
            resolution=settings.DEFAULT_RESOLUTION,
        )
        video_urls = [video_url]

        await asyncio.to_thread(tracker.update_with_video, video_urls[0])
        log.info(f"✅ {settings.DEFAULT_DURATION}s video hazır")

        # ── Güvenlik Telemetrisi ──
        try:
            preflight_meta = getattr(kie, '_last_preflight_meta', {})
            if preflight_meta and preflight_meta.get('risk_score', 0) > 0:
                safety_data = {
                    "preflight_risk_score": preflight_meta.get('risk_score', 0),
                    "preflight_rewritten": preflight_meta.get('rewritten', False),
                    "rejection_reasons": preflight_meta.get('risk_reasons', []),
                }
                await asyncio.to_thread(tracker.update_with_safety_info, safety_data)
        except Exception as e:
            log.debug(f"Güvenlik telemetrisi hatası (önemsiz): {e}")

        # ── ADIM 4: Video indir ──
        log.info("📥 Video indiriliyor...")
        final_video_url = video_urls[0]
        video_path = await asyncio.to_thread(download_video, final_video_url)
        video_paths.append(video_path)

        # ── Hareket profili (TUR 9): açılış durgunluğu istatistiği, Kie harcamadan ──
        camera = combo_key.split("|")[-1] if combo_key else ""
        try:
            motion = await asyncio.to_thread(motion_profile, video_path)
            motion_text = format_motion(motion, camera)
        except Exception as me:
            motion_text = f"ölçülemedi: {me}"
            log.warning(f"⚠️ Hareket profili ölçülemedi: {me}")
        await asyncio.to_thread(tracker.update_with_motion, motion_text)

        saved_local_path = video_path
        if output_path:
            shutil.copy(video_path, output_path)
            saved_local_path = output_path
            log.info(f"💾 Video yerel hedefe kopyalandı: {output_path}")

        # ── ADIM 5: YouTube upload (Shorts) ──
        youtube_url = ""
        if upload_active:
            log.info("📺 YouTube Shorts olarak yükleniyor...")
            await asyncio.to_thread(tracker.update_status, "Yükleniyor")
            try:
                youtube_url = await upload_to_youtube(
                    video_path, prompt_data, is_shorts=True
                )
                if youtube_url:
                    await asyncio.to_thread(tracker.update_with_youtube, youtube_url)
                    log.info(f"✅ YouTube'a yüklendi: {youtube_url}")
            except Exception as ue:
                log.error(f"❌ YouTube upload adımı başarısız oldu: {ue}", exc_info=True)
                # Video üretimi başarılı oldu, sadece YouTube yüklemesi başarısız.
                # Pipeline çökmez; Adım 6'ya devam ederek Notion'da '✅ Tamamlandı (Upload Başarısız)' kaydı açılır.

        # ── ADIM 6: Tamamlandı ──
        elapsed = time.time() - start_time

        if not youtube_url:
            if upload_active:
                await asyncio.to_thread(tracker.update_status, "✅ Tamamlandı (Upload Başarısız)")
            else:
                await asyncio.to_thread(tracker.update_status, "✅ Tamamlandı (Test Modu / YouTube Atlandı)")
        else:
            await asyncio.to_thread(tracker.update_status, "✅ Tamamlandı")

        log.info(f"🎉 Pipeline tamamlandı! ({elapsed:.0f}s)")
        log.info(f"   📺 {youtube_url or 'Upload atlandı (Test modu)'}")
        log.info(f"   🎬 Başlık: {prompt_data.get('youtube_title', 'N/A')}")
        log.info(f"   💾 Yerel Dosya: {saved_local_path}")

        return {
            "success": True,
            "youtube_url": youtube_url,
            "title": prompt_data.get("youtube_title", ""),
            "scenario": prompt_data.get("scenario_summary", ""),
            "combo_key": combo_key,
            "clip_count": clip_count,
            "total_duration": total_duration,
            "elapsed": elapsed,
            "prompt": scenes[0]["prompt"] if scenes else "",
            "description": prompt_data.get("youtube_description", ""),
            "tags": prompt_data.get("tags", []),
            "model": settings.DEFAULT_MODEL,
            "resolution": settings.DEFAULT_RESOLUTION,
            "video_path": saved_local_path,
            "video_cdn_url": final_video_url,
            "privacy": settings.YOUTUBE_PRIVACY,
        }

    except ContentFilterError as cfe:
        if combo_key:
            cfe.combo_key = combo_key
        raise

    except NoValidScenarioError as nvse:
        elapsed = time.time() - start_time
        timestamp = time.strftime("%Y-%m-%d %H:%M")
        log.error(f"🚫 Kalite kapısından geçen senaryo yok ({elapsed:.1f}s): {nvse}")

        if not tracker.page_id:
            await asyncio.to_thread(
                tracker.create_entry,
                {
                    "topic": f"Boş Cron — {timestamp} | 5 senaryo kalite kapısından geçemedi: {str(nvse)[:300]}",
                    "model": settings.DEFAULT_MODEL,
                    "clip_count": 0,
                    "orientation": settings.DEFAULT_ORIENTATION,
                    "audio": settings.DEFAULT_AUDIO,
                    "combo_key": "",
                },
                "auto",
            )
        await asyncio.to_thread(tracker.update_with_error, str(nvse))
        return {"success": False, "reason": "no_valid_scenario", "error": str(nvse)}

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        log.error(f"❌ Pipeline HATASI ({elapsed:.1f}s): {error_msg}", exc_info=True)
        await asyncio.to_thread(tracker.update_with_error, error_msg)
        return {"success": False, "error": error_msg}

    finally:
        # Eğer upload yapıldıysa veya output_path belirtilmişse temp dosyayı temizle
        if upload_active or output_path:
            for vp in video_paths:
                if vp != output_path:
                    cleanup_video(vp)


# ────────────────────────────────────────
# 🏥 SİSTEM SAĞLIK KONTROLÜ
# ────────────────────────────────────────

def health_check():
    """Sistem sağlık kontrolü — tüm servisleri test eder."""
    checks = []

    # Config
    checks.append(("Config Boot", True, f"ENV={settings.ENV}"))

    # OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        checks.append(("OpenAI API Key", not settings.OPENAI_API_KEY.startswith("sk-test"), ""))
    except Exception as e:
        checks.append(("OpenAI", False, str(e)))

    # Kie AI
    checks.append(("Kie AI API Key", not settings.KIE_API_KEY.startswith("test-"), ""))

    # YouTube
    yt_ok = bool(settings.YOUTUBE_CLIENT_ID and settings.YOUTUBE_CLIENT_SECRET and settings.YOUTUBE_REFRESH_TOKEN)
    checks.append(("YouTube OAuth2", yt_ok, f"Upload: {'Aktif' if settings.YOUTUBE_ENABLED else 'Kapalı'}"))

    # Notion
    checks.append(("Notion", settings.NOTION_ENABLED, f"DB: {settings.NOTION_DB_ID[:8]}..." if settings.NOTION_DB_ID else "DB yok"))

    # Replicate
    checks.append(("Replicate", not settings.REPLICATE_API_TOKEN.startswith("test-"), ""))

    # FFmpeg
    checks.append(("FFmpeg", settings.FFMPEG_AVAILABLE, "Opsiyonel"))

    print("\n🏥 Sistem Sağlık Raporu — DeepMyster V3 (Yeni Referans Standardı)\n" + "=" * 60)
    all_ok = True
    for name, ok, detail in checks:
        icon = "✅" if ok else "❌"
        detail_str = f" — {detail}" if detail else ""
        print(f"  {icon} {name}{detail_str}")
        if not ok and name not in ("FFmpeg",):
            all_ok = False

    print("=" * 60)
    if all_ok:
        print("✅ Tüm kritik sistemler hazır!")
    else:
        print("❌ Bazı sistemler hazır değil — yukarıdaki hataları kontrol edin.")
    print()

    return all_ok


# ────────────────────────────────────────
# 🚀 ENTRY POINT
# ────────────────────────────────────────

def main():
    """CLI entry point — CronJob bu fonksiyonu çalıştırır."""
    parser = argparse.ArgumentParser(
        description="DeepMyster V3 — Yeni Referans Standardı Günlük Otonom Video Pipeline"
    )
    parser.add_argument("--dry-run", action="store_true", help="Gerçek üretim yapmadan test")
    parser.add_argument("--no-upload", action="store_true", help="Gerçek video üret ama YouTube'a yükleme")
    parser.add_argument("--output", type=str, default="", help="Üretilen videoyu kaydedecek dosya yolu")
    parser.add_argument("--check", action="store_true", help="Sistem sağlık kontrolü")
    args = parser.parse_args()

    if args.check:
        health_check()
        return

    result = asyncio.run(run_pipeline(dry_run=args.dry_run, skip_upload=args.no_upload, output_path=args.output))

    if result and result.get("success"):
        log.info("🎉 DeepMyster video pipeline başarıyla tamamlandı!")
        sys.exit(0)
    else:
        error = result.get("error", "Bilinmeyen hata") if result else "Pipeline sonuç döndürmedi"
        log.error(f"💥 Pipeline başarısız: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
