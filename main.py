#!/usr/bin/env python3
from __future__ import annotations

"""
YouTube Otomasyonu V3 — "DeepMyster" Yeni Referans Standardı Pipeline
===================================================================
Telegram botundan tetiklenir: tek kesintisiz çekim fiziksel olay senaryosu üretir (süre config.DEFAULT_DURATION ile kontrol edilir) →
Seedance 2 Mini ile video üretir → YouTube Shorts olarak yükler.

Tetikleme: Telegram botu (bot.py, /uret → kategori → olay → onay). Railway'de start komutu `python bot.py`;
cron yok. Elle çalıştırma aşağıdaki CLI ile hâlâ mümkün.

Çalıştırma:
  python main.py                → Tam pipeline (rastgele domain)
  python main.py --dry-run      → Gerçek üretim yapmadan mock test
  python main.py --no-upload    → Gerçek video üret ama YouTube'a yükleme (Lokal test)
  python main.py --check        → Sistem sağlık kontrolü

"""
import os
import sys
import time
import asyncio
import logging
import argparse
import shutil
from datetime import datetime, timezone

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from logger import get_logger
from core.prompt_generator import (generate_prompts, NoValidScenarioError, make_story_validator, EventMismatchError,
                                   event_fidelity_issues, scenario_text)
from core.trace_format import format_generation, format_final_prompt
from infrastructure.kie_client import KieClient, ContentFilterError, KieTimeoutError, SubmissionCancelled
from core.prompt_sanitizer import PreflightError
from infrastructure.motion_profile import motion_profile, format_motion
from infrastructure.video_downloader import download_video, cleanup_video
from infrastructure.youtube_uploader import upload_to_youtube
from infrastructure.notion_logger import (NotionTracker, STATUS_AWAITING_APPROVAL, STATUS_CANCELLED, STATUS_RECOVERED,
                                          STATUS_TEST_DONE, STATUS_VIDEO_GENERATING, _rt)
from infrastructure.archive import current_commit, new_archive_dir, save_video, write_meta
from infrastructure.run_status import status

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

# Üretim modu (TUR 29). TEST: hat birebir aynı, sadece YouTube adımı atlanır. YAYIN: settings.PUBLISH_LOCKED
# açılmadan hiçbir yoldan YouTube'a yüklenmez.
MODE_TEST = "TEST"
MODE_PUBLISH = "YAYIN"


class PipelineReporter:
    """Pipeline → arayüz köprüsü (TUR 29, Telegram "🔍 Ayrıntı" / "✋ Onay"). Varsayılan sessizdir ve onay
    istemez (CLI). Raporlama hatası üretimi durdurmaz; approve False dönerse Kie çağrılmaz."""
    needs_approval = False

    async def generation(self, trace: dict, prompt_data: dict | None = None) -> None:
        return None

    async def final_prompt(self, info: dict) -> None:
        return None

    async def approve(self, info: dict) -> bool:
        return True


async def _report(coro) -> None:
    try:
        await coro
    except Exception as e:
        log.warning(f"⚠️ Raporlama hatası (üretim sürüyor): {e}")


async def _credit(kie) -> float | None:
    """Kie kredisi; okunamazsa None (meta.json'da doğrulanamadı). Üretimi asla durdurmaz."""
    try:
        return await kie.get_credit()
    except Exception as e:
        log.warning(f"⚠️ Kie kredisi okunamadı: {e}")
        return None


async def run_pipeline(dry_run: bool = False, skip_upload: bool = False, output_path: str = "",
                       domain: str | None = None, trigger: str = "auto", event: str | None = None,
                       mode: str | None = None, reporter: PipelineReporter | None = None):
    """
    Tam otonom video üretim pipeline'ı.

    Akış:
      1. Tekrar önleme → kullanılan senaryoları yükle
      2. Creative Engine + GPT → tek çekim senaryo + prompt üret (DEFAULT_DURATION saniye)
      3. Seedance 2 Mini → video üret (tek kesintisiz çekim, DEFAULT_DURATION saniye)
      4. YouTube → Shorts olarak yükle (yayın modu, kilit açıksa)
      5. Notion + arşiv (video.mp4, meta.json) → log kaydet

    domain: verilirse senaryolar sadece bu domain'den üretilir (Telegram /uret). trigger: Notion 'Tetikleyici'.
    event: verilirse senaryolar bu olayla üretilir (Telegram olay menüsü); ortam/gemi/kamera otomatik.
    mode: TEST (YouTube yok) / YAYIN. Verilmezse yükleme durumuna göre. reporter: Telegram ayrıntı/onay köprüsü.
    """
    if dry_run:
        settings.IS_DRY_RUN = True
        settings.ENV = "development"

    upload_active = settings.YOUTUBE_ENABLED and not skip_upload and mode != MODE_TEST
    if upload_active and settings.PUBLISH_LOCKED:
        log.warning("🔒 Yayın kilidi açık değil: YouTube'a yükleme yapılmayacak (settings.PUBLISH_LOCKED)")
        upload_active = False
    mode = mode or (MODE_PUBLISH if upload_active else MODE_TEST)

    run_label = "DRY-RUN" if settings.IS_DRY_RUN else "PRODUCTION"
    log.info(f"🚀 DeepMyster V3 (Yeni Referans Standardı) başlatılıyor... (Mod: {run_label}, {mode})")
    log.info(f"   Model: {settings.DEFAULT_MODEL} | Hedef Süre: {settings.DEFAULT_DURATION}s")
    log.info(f"   YouTube Upload: {'Aktif' if upload_active else 'Devre Dışı (TEST / kilit / skip)'}")
    log.info(f"   Notion Log: {'Aktif' if settings.NOTION_ENABLED else 'Devre Dışı'}")

    # ── Tekrar önleme & Semantik Negatif Hafıza ──
    used_combos = load_used_combos()
    tracker = NotionTracker()
    # creative hattı son 15 hikâyeyi "bunlardan farklı yaz" diye verir; konu+başlık çiftleri için 40 (TUR 31)
    recent_topics = tracker.get_recent_history(days=30, limit=40)
    recent_verbs = tracker.get_recent_beat1_verbs(limit=10)   # Beat 1 fiil rotasyonu (TUR 17)
    if recent_topics:
        log.info(f"🧠 Son 30 günden {len(recent_topics)} semantik konu negatif hafızaya eklendi")

    # ── Senaryoya bağlı ret retry'ı — 3 farklı senaryo dene ──
    # Kie içerik filtresi reddi ve içerik kaynaklı preflight hatası aynı bütçeyi paylaşır (TUR 13).
    # API kaynaklı preflight hatası sistem sorunudur: yeni senaryo denenmez, gün görünür düşer.
    max_retries = 3
    last_error, reason = None, ""

    for attempt in range(max_retries):
        status.start(run_label if upload_active else f"{run_label} (upload yok)", attempt + 1, max_retries)
        try:
            result = await _execute_pipeline(
                used_combos,
                recent_topics=recent_topics,
                recent_verbs=recent_verbs,
                upload_active=upload_active,
                output_path=output_path,
                domain=domain,
                event=event,
                trigger=trigger,
                mode=mode,
                reporter=reporter,
            )
            return result
        except (ContentFilterError, PreflightError) as err:
            last_error = err
            if isinstance(err, PreflightError):
                reason = f"preflight_{err.kind}"
                if err.kind == "api":
                    log.error(f"❌ Preflight API hatası, yeni senaryo denenmiyor: {err}")
                    return {"success": False, "reason": reason, "error": str(err)}
            else:
                reason = "content_filter"
            rejected_combo = getattr(err, "combo_key", "")
            if rejected_combo and rejected_combo not in used_combos:
                used_combos.append(rejected_combo)
                log.info(f"🚫 Reddedilen combo dedup listesine eklendi: {rejected_combo}")
            if attempt < max_retries - 1:
                log.warning(
                    f"🛡️ Senaryo reddedildi ({reason}, deneme {attempt + 1}/{max_retries}). "
                    f"Farklı senaryo ile tekrar denenecek..."
                )

    log.error(f"❌ {max_retries} farklı senaryo denendi, hepsi reddedildi.")
    return {"success": False, "reason": reason, "error": str(last_error)}


async def _execute_pipeline(
    used_combos: list[str],
    recent_topics: list[str] | None = None,
    recent_verbs: list[str] | None = None,
    upload_active: bool = True,
    output_path: str = "",
    domain: str | None = None,
    event: str | None = None,
    trigger: str = "auto",
    mode: str = MODE_PUBLISH,
    reporter: PipelineReporter | None = None,
) -> dict:
    """
    Pipeline'ın asıl implementasyonu.
    """
    reporter = reporter or PipelineReporter()
    tracker = NotionTracker()
    kie = KieClient()
    video_paths = []
    start_time = time.time()
    combo_key = ""
    commit = current_commit()
    archive_dir = ""
    # meta.json (TUR 29): kategori/olay/kamera/gemi, son Kie prompt'u, stil eki sürümü (commit), model, çözünürlük,
    # task ID, mod, kredi öncesi/sonrası
    meta = {"mode": mode, "commit": commit, "model": settings.DEFAULT_MODEL, "resolution": settings.DEFAULT_RESOLUTION,
            "duration": settings.DEFAULT_DURATION, "trigger": trigger, "menu_domain": domain, "menu_event": event,
            "started_at": datetime.now(timezone.utc).isoformat()}

    pipeline_config = {
        "used_combos": used_combos,
        "recent_topics": recent_topics or [],
        "recent_verbs": recent_verbs or [],
        "domain": domain,
        "event": event,
    }

    try:
        # ── ADIM 1: Prompt üret (Creative Engine + GPT) ──
        status.step("senaryo")
        log.info(f"🧠 Yaratıcı motor çalışıyor (Tek {settings.DEFAULT_DURATION}s kesintisiz çekim standardı)...")
        try:
            prompt_data = await generate_prompts(pipeline_config)
        except NoValidScenarioError as nvse:
            await _report(reporter.generation(nvse.trace))
            raise

        scenes = prompt_data.get("scenes", [])
        combo_key = prompt_data.get("combo_key", "")
        clip_count = len(scenes)
        total_duration = prompt_data.get("total_duration", settings.DEFAULT_DURATION)
        selection = prompt_data.get("selection") or {}
        meta.update({"domain": selection.get("domain_id", ""), "event": selection.get("event", ""),
                     "environment": selection.get("environment", ""), "ship": selection.get("ship", ""),
                     "camera": selection.get("camera", ""), "combo_key": combo_key,
                     "title": prompt_data.get("youtube_title", ""),
                     "scenario_summary": prompt_data.get("scenario_summary", "")})

        log.info(f"🎬 Senaryo: {prompt_data.get('scenario_summary', '')}")
        log.info(f"   {clip_count} sahne, {total_duration}s | Başlık: {prompt_data.get('youtube_title', '')}")
        log.info(f"   Prompt: {scenes[0]['prompt'] if scenes else ''}")
        status.set_title(prompt_data.get("youtube_title", "") or prompt_data.get("scenario_summary", ""))
        await _report(reporter.generation(prompt_data.get("trace") or {}, prompt_data))

        # ── ADIM 2: Notion entry ──
        notion_config = {
            "topic": prompt_data.get("scenario_summary", "DeepMyster maritime physical incident"),
            "model": settings.DEFAULT_MODEL,
            "clip_count": clip_count,
            "orientation": settings.DEFAULT_ORIENTATION,
            "audio": settings.DEFAULT_AUDIO,
            "combo_key": combo_key,
            "mode": mode,
        }
        await asyncio.to_thread(tracker.create_entry, notion_config, trigger=trigger)
        await asyncio.to_thread(tracker.update_with_prompts, prompt_data)
        if prompt_data.get("trace"):
            await asyncio.to_thread(tracker.append_body, format_generation(prompt_data["trace"]))

        # ── Zorunlu olay denetimi (TUR 29): menü olayı seçilen senaryoda ve hikayede yoksa Kie çağrılmaz ──
        if event:
            scenario = (prompt_data.get("gate_context") or {}).get("scenario") or {}
            story = (scenes[0].get("story") or scenes[0].get("prompt", "")) if scenes else ""
            # İskelet hattında senaryo = hikaye (scenario_text); eski hatta yazıcının 3 beat'i
            chosen = prompt_data.get("scenario_text") or scenario_text(scenario)
            issues = event_fidelity_issues(event, chosen) + event_fidelity_issues(event, story)
            if issues:
                raise EventMismatchError("; ".join(issues))

        # ── ADIM 3: Video üret (Seedance 2 Mini) ──
        log.info(f"🎬 Video üretimi başlıyor ({settings.DEFAULT_MODEL}, {settings.DEFAULT_DURATION}s)...")
        status.step("video")
        meta["credit_before"] = await _credit(kie)

        async def before_submit(info: dict) -> None:
            """Ücretli createTask'tan hemen önce: son prompt Notion'a, olay denetimi, ayrıntı, onay."""
            if event:
                issues = event_fidelity_issues(event, info.get("story", ""))
                if issues:
                    raise EventMismatchError("Kie'ye gidecek hikaye: " + "; ".join(issues))
            meta.update({"final_prompt": info["prompt"], "story": info.get("story", ""),
                         "style_suffix": info.get("style_suffix", ""), "preflight": info.get("preflight") or {}})
            await asyncio.to_thread(tracker.record_final_prompt, info["prompt"], selection, commit)
            await asyncio.to_thread(tracker.append_body, [format_final_prompt(info)])
            await _report(reporter.final_prompt(info))
            if reporter.needs_approval:
                await asyncio.to_thread(tracker.update_status, STATUS_AWAITING_APPROVAL)
                if not await reporter.approve(info):
                    raise SubmissionCancelled("Kie gönderimi onaylanmadı (iptal veya onay süresi doldu)")

        async def on_task_created(task_id: str, info: dict) -> None:
            """Polling başlamadan task ID'yi kalıcı yaz: restart olursa kurtarma buradan devam eder."""
            nonlocal archive_dir
            meta.update({"task_id": task_id, "task_created_at": datetime.now(timezone.utc).isoformat(),
                         "notion_page_id": tracker.page_id or "", "status": "video_uretiliyor"})
            try:
                archive_dir = archive_dir or new_archive_dir(meta.get("domain", ""), task_id)
                write_meta(archive_dir, meta)
            except OSError as e:
                log.warning(f"⚠️ meta.json yazılamadı: {e}")
            await asyncio.to_thread(tracker.record_task, task_id)

        # Hikaye + stil eki ayrı gider: preflight/retry sadece hikayeyi yeniden yazar (TUR 12)
        has_split = "story" in scenes[0] and "style_suffix" in scenes[0]
        video_url = await kie.create_video(
            model=settings.DEFAULT_MODEL,
            prompt=scenes[0]["story"] if has_split else scenes[0]["prompt"],
            style_suffix=scenes[0]["style_suffix"] if has_split else "",
            # Rewrite sonrası aynı kalite kapıları (TUR 21)
            story_validator=make_story_validator(prompt_data.get("gate_context")) if has_split else None,
            orientation=settings.DEFAULT_ORIENTATION,
            duration=scenes[0].get("duration", settings.DEFAULT_DURATION),
            audio=settings.DEFAULT_AUDIO,
            resolution=settings.DEFAULT_RESOLUTION,
            before_submit=before_submit,
            on_task_created=on_task_created,
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

        # ── ADIM 4: Video indir + kalıcı arşiv ──
        log.info("📥 Video indiriliyor...")
        status.step("indirme")
        final_video_url = video_urls[0]
        video_path = await asyncio.to_thread(download_video, final_video_url)
        video_paths.append(video_path)
        archived_path = ""
        if video_path and os.path.exists(video_path):
            try:
                archive_dir = archive_dir or new_archive_dir(meta.get("domain", ""), meta.get("task_id", ""))
                archived_path = save_video(archive_dir, video_path)
            except OSError as e:
                log.warning(f"⚠️ Video arşive kopyalanamadı: {e}")
        meta.update({"video_cdn_url": final_video_url, "credit_after": await _credit(kie)})

        # ── Hareket profili (TUR 9): açılış durgunluğu istatistiği, Kie harcamadan ──
        camera = combo_key.split("|")[-1] if combo_key else ""
        try:
            motion = await asyncio.to_thread(motion_profile, video_path)
            motion_text = format_motion(motion, camera)
        except Exception as me:
            motion_text = f"ölçülemedi: {me}"
            log.warning(f"⚠️ Hareket profili ölçülemedi: {me}")
        await asyncio.to_thread(tracker.update_with_motion, motion_text)
        meta["motion"] = motion_text

        saved_local_path = archived_path or video_path
        if output_path:
            shutil.copy(video_path, output_path)
            saved_local_path = output_path
            log.info(f"💾 Video yerel hedefe kopyalandı: {output_path}")

        status.skip("montaj", "Tek kesintisiz çekim, montaj yok")

        # ── ADIM 5: YouTube upload (Shorts) — sadece YAYIN modu ve kilit açıksa ──
        youtube_url = ""
        if not upload_active:
            status.skip("youtube", "TEST modu / yayın kilidi, yükleme atlandı")
        if upload_active:
            status.step("youtube")
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
                status.step_error("youtube", str(ue))
                # Video üretimi başarılı oldu, sadece YouTube yüklemesi başarısız.
                # Pipeline çökmez; Adım 6'ya devam ederek Notion'da '✅ Tamamlandı (Upload Başarısız)' kaydı açılır.

        if upload_active and not youtube_url:
            status.step_error("youtube", "YouTube URL dönmedi")
        status.manual("instagram", "Manuel: videoyu @deepmyster Instagram hesabında elle paylaş")

        # ── ADIM 6: Tamamlandı ──
        elapsed = time.time() - start_time

        if not youtube_url:
            if upload_active:
                await asyncio.to_thread(tracker.update_status, "✅ Tamamlandı (Upload Başarısız)")
            else:
                await asyncio.to_thread(tracker.update_status, STATUS_TEST_DONE)
        else:
            await asyncio.to_thread(tracker.update_status, "✅ Tamamlandı")

        meta.update({"status": "tamamlandi", "youtube_url": youtube_url, "elapsed_s": round(elapsed, 1),
                     "notion_page_id": tracker.page_id or "", "finished_at": datetime.now(timezone.utc).isoformat()})
        if archive_dir:
            try:
                write_meta(archive_dir, meta)
            except OSError as e:
                log.warning(f"⚠️ meta.json yazılamadı: {e}")

        status.finish(youtube_url)
        log.info(f"🎉 Pipeline tamamlandı! ({elapsed:.0f}s)")
        log.info(f"   📺 {youtube_url or 'Upload atlandı (TEST / kilit)'}")
        log.info(f"   🎬 Başlık: {prompt_data.get('youtube_title', 'N/A')}")
        log.info(f"   💾 Arşiv: {archive_dir or saved_local_path}")

        return {
            "success": True,
            "youtube_url": youtube_url,
            "title": prompt_data.get("youtube_title", ""),
            "scenario": prompt_data.get("scenario_summary", ""),
            "combo_key": combo_key,
            "clip_count": clip_count,
            "total_duration": total_duration,
            "elapsed": elapsed,
            "prompt": meta.get("final_prompt") or (scenes[0]["prompt"] if scenes else ""),
            "description": prompt_data.get("youtube_description", ""),
            "tags": prompt_data.get("tags", []),
            "model": settings.DEFAULT_MODEL,
            "resolution": settings.DEFAULT_RESOLUTION,
            "video_path": saved_local_path,
            "video_cdn_url": final_video_url,
            "privacy": settings.YOUTUBE_PRIVACY,
            "mode": mode,
            "task_id": meta.get("task_id", ""),
            "notion_page_id": tracker.page_id or "",
            "archive_dir": archive_dir,
        }

    except SubmissionCancelled as sc:
        log.info(f"✋ Kie gönderimi iptal edildi, kredi harcanmadı: {sc}")
        await asyncio.to_thread(tracker.update_status, STATUS_CANCELLED, {"Hata": _rt(str(sc))})
        status.fail(f"İptal: {sc}")
        return {"success": False, "reason": "cancelled", "error": str(sc), "notion_page_id": tracker.page_id or ""}

    except EventMismatchError as em:
        log.error(f"🚫 Zorunlu olay denetimi: {em}")
        await asyncio.to_thread(tracker.update_with_error, str(em))
        status.fail(str(em))
        return {"success": False, "reason": "event_mismatch", "error": str(em)}

    except KieTimeoutError as te:
        # Kayıt hata olarak kapatılmaz: "Video Üretiliyor" + Kie Task ID ile kalır, kurtarma devam eder
        log.warning(f"⏳ Kie zaman aşımı, task ID ile devam edilecek: {te.task_id}")
        status.fail(f"Kie zaman aşımı, task {te.task_id} takip ediliyor")
        return {"success": False, "reason": "kie_timeout", "error": str(te), "task_id": te.task_id,
                "notion_page_id": tracker.page_id or "", "mode": mode, "archive_dir": archive_dir}

    except (ContentFilterError, PreflightError) as err:
        # Senaryoya bağlı ret: bu denemenin Notion kaydı hata olarak kapanır (eskiden
        # "Video Üretiliyor"da takılı kalıyordu), run_pipeline yeni senaryo dener (TUR 13).
        if combo_key:
            err.combo_key = combo_key
        label = f"Preflight ({err.kind})" if isinstance(err, PreflightError) else "Kie içerik filtresi"
        await asyncio.to_thread(tracker.update_with_error, f"{label}: {err}")
        status.fail(f"{label}: {err}")
        raise

    except NoValidScenarioError as nvse:
        elapsed = time.time() - start_time
        log.error(f"🚫 Kalite kapısından geçen senaryo yok ({elapsed:.1f}s): {nvse}")
        # TUR 29: "Boş Cron" kaydı açılmaz (cron yok); ayrıntı Telegram'a ve loga gider
        if tracker.page_id:
            await asyncio.to_thread(tracker.update_with_error, str(nvse))
        status.fail(f"Kalite kapısından geçen senaryo yok: {nvse}")
        return {"success": False, "reason": "no_valid_scenario", "error": str(nvse),
                "error_summary": nvse.short_summary()}   # Telegram'a kısa özet (TUR 25)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        log.error(f"❌ Pipeline HATASI ({elapsed:.1f}s): {error_msg}", exc_info=True)
        await asyncio.to_thread(tracker.update_with_error, error_msg)
        status.fail(error_msg)
        return {"success": False, "error": error_msg}

    finally:
        # Geçici indirme her modda silinir (TUR 29: TEST'te sızıyordu); kalıcı kopya arşivde
        for vp in video_paths:
            if vp != output_path:
                cleanup_video(vp)


# ────────────────────────────────────────
# ♻️ KURTARMA (TUR 29)
# ────────────────────────────────────────

async def recover_pending_tasks(on_video=None, kie: KieClient | None = None, poll_attempts: int | None = None,
                                only_page_id: str | None = None) -> list[dict]:
    """Restart veya Kie zaman aşımından kalan kayıtları tamamlar. Yeni ücretli çağrı YAPMAZ.

    - "✋ Onay Bekliyor": Kie hiç çağrılmadı; sessizce "❌ İptal" olur.
    - "Video Üretiliyor" + Kie Task ID: task beklenir, video indirilir ve arşivlenir, Notion kapanır,
      on_video(item) çağrılır (bot videoyu Telegram'a gönderir). YouTube'a YÜKLENMEZ.
    - Task ID'si olmayan eski kayıtlar atlanır (elle temizlenir).
    """
    kie = kie or KieClient()
    results = []
    try:
        records = await asyncio.to_thread(NotionTracker.find_by_status,
                                          [STATUS_VIDEO_GENERATING, STATUS_AWAITING_APPROVAL])
    except Exception as e:
        log.warning(f"⚠️ Kurtarma: Notion sorgusu başarısız: {e}")
        return results
    for rec in records:
        if only_page_id and rec["page_id"].replace("-", "") != only_page_id.replace("-", ""):
            continue
        tracker = NotionTracker(page_id=rec["page_id"])
        item = {"page_id": rec["page_id"], "task_id": rec["task_id"], "title": rec["title"], "mode": rec["mode"]}
        if rec["status"] == STATUS_AWAITING_APPROVAL:
            await asyncio.to_thread(tracker.update_status, STATUS_CANCELLED, {
                "Hata": _rt("Onay beklerken bot yeniden başladı; Kie çağrılmadı, kredi harcanmadı.")})
            results.append({**item, "action": "cancelled"})
            continue
        if not rec["task_id"]:
            log.info(f"♻️ Kurtarma: task ID'siz eski kayıt atlandı: {rec['title'][:60]}")
            results.append({**item, "action": "skipped_no_task"})
            continue
        try:
            url = await kie.wait_for_task(rec["task_id"], max_attempts=poll_attempts)
        except KieTimeoutError:
            results.append({**item, "action": "still_running"})
            continue
        except Exception as e:
            await asyncio.to_thread(tracker.update_with_error, f"Kurtarma: Kie task başarısız: {e}")
            results.append({**item, "action": "failed", "error": str(e)})
            continue
        path = ""
        try:
            path = await asyncio.to_thread(download_video, url)
            domain = (rec["combo_key"].split("|")[0] if rec["combo_key"] else "") or "kurtarma"
            archive_dir = new_archive_dir(domain, rec["task_id"])
            archived = save_video(archive_dir, path)
            prompt = ""
            try:
                prompt = (await kie.get_task(rec["task_id"])).get("prompt", "")
            except Exception as e:
                log.warning(f"⚠️ Kurtarma: task prompt'u okunamadı: {e}")
            write_meta(archive_dir, {"mode": rec["mode"] or "bilinmiyor", "task_id": rec["task_id"],
                                     "notion_page_id": rec["page_id"], "combo_key": rec["combo_key"],
                                     "title": rec["title"], "final_prompt": prompt, "video_cdn_url": url,
                                     "model": settings.DEFAULT_MODEL, "resolution": settings.DEFAULT_RESOLUTION,
                                     "commit": current_commit(), "recovered": True, "status": "kurtarildi",
                                     "finished_at": datetime.now(timezone.utc).isoformat()})
        except Exception as e:
            await asyncio.to_thread(tracker.update_with_error, f"Kurtarma: video indirilemedi: {e}")
            results.append({**item, "action": "failed", "error": str(e)})
            continue
        finally:
            if path:
                cleanup_video(path)
        await asyncio.to_thread(tracker.update_status, STATUS_RECOVERED, {"Video URL": {"url": url}})
        done = {**item, "action": "recovered", "video_path": archived, "archive_dir": archive_dir, "video_url": url}
        log.info(f"♻️ Kurtarıldı: {rec['title'][:60]} (task {rec['task_id']})")
        if on_video:
            try:
                await on_video(done)
            except Exception as e:
                log.warning(f"⚠️ Kurtarılan video gönderilemedi: {e}")
        results.append(done)
    return results


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
    """CLI entry point (elle çalıştırma; Railway bot.py çalıştırır)."""
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

    # Canlı durum dosyası (dashboard.html okur). Sadece CLI'dan; testler run_pipeline'ı doğrudan çağırır.
    status.enable(os.environ.get("STATUS_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "status.json"))
    try:
        result = asyncio.run(run_pipeline(dry_run=args.dry_run, skip_upload=args.no_upload, output_path=args.output))
    except BaseException as e:   # Ctrl+C dahil: çalışan adım "çalışıyor"da takılı kalmasın
        status.fail(f"Süreç durduruldu: {type(e).__name__}: {e}")
        raise
    if result and not result.get("success") and status.data.get("state") == "running":
        status.fail(result.get("error") or result.get("reason") or "Bilinmeyen hata")

    if result and result.get("success"):
        log.info("🎉 DeepMyster video pipeline başarıyla tamamlandı!")
        sys.exit(0)
    else:
        error = result.get("error", "Bilinmeyen hata") if result else "Pipeline sonuç döndürmedi"
        log.error(f"💥 Pipeline başarısız: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
