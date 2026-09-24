# Onaylı prompt'ları (scripts/finalize_prompts.py çıktısı) üretimle aynı Kie çağrısıyla sırayla üretir:
# kredi önce/sonra, indirme (<prefix>_<i>_<ts>.mp4, proje kökü), ffprobe. Hikaye + stil eki ayrı gider,
# preflight/retry sadece hikayeye uygulanır (TUR 12).
# ⚠️ GERÇEK KIE HARCAMASI YAPAR — sadece kullanıcının açık onayıyla çalıştır.
# Kullanım: python scripts/run_kie_batch.py <final_prompts.json> <dosya_öneki> [sonuç.json]
#           (varsayılan sonuç: scratch/kie_batch_result.json)
import asyncio, json, sys, os, io, time, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import requests
from config import settings


def credit():
    r = requests.get(f"{settings.KIE_BASE_URL}/chat/credit",
                     headers={"Authorization": f"Bearer {settings.KIE_API_KEY}"}, timeout=20)
    r.raise_for_status()
    return r.json().get("data")


def ffprobe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
                          "-of", "json", path], capture_output=True, text=True)
    return json.loads(out.stdout or "{}")


async def main(src: str, prefix: str, out_path: str):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    settings.IS_DRY_RUN = False
    from infrastructure.kie_client import KieClient
    from infrastructure.motion_profile import format_motion, motion_profile
    prompts = json.load(open(src, encoding="utf-8"))
    res = {"credit_before": credit(), "model": settings.DEFAULT_MODEL, "videos": []}
    print(f"KREDİ ÖNCE: {res['credit_before']}", flush=True)

    def save():
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        json.dump(res, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)

    client = KieClient()
    for i, p in enumerate(prompts, 1):
        print(f"\n=== Video {i}: #{p['n']} {p['domain']} | {p['camera']} ===", flush=True)
        t0 = time.time()
        v = {k: p.get(k) for k in ("n", "domain", "camera", "ship", "story", "style_suffix", "final_prompt")}
        try:
            has_split = bool(p.get("story") and p.get("style_suffix"))
            url = await client.create_video(model=settings.DEFAULT_MODEL,
                                            prompt=p["story"] if has_split else p["final_prompt"],
                                            style_suffix=p["style_suffix"] if has_split else "",
                                            orientation=settings.DEFAULT_ORIENTATION, duration=settings.DEFAULT_DURATION,
                                            audio=settings.DEFAULT_AUDIO, resolution=settings.DEFAULT_RESOLUTION)
            v.update(url=url, preflight=getattr(client, "_last_preflight_meta", {}) or {},
                     seconds=round(time.time() - t0))
            fn = os.path.join(ROOT, f"{prefix}_{i}_{int(time.time())}.mp4")
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(fn, "wb") as f:
                    for chunk in r.iter_content(1 << 16):
                        f.write(chunk)
            v.update(file=fn, ffprobe=ffprobe(fn))
            try:
                v["motion"] = format_motion(motion_profile(fn), p["camera"])
            except Exception as me:
                v["motion"] = f"ölçülemedi: {me}"
            print(f"OK {v['seconds']}s -> {fn}\n   hareket: {v['motion']}", flush=True)
        except Exception as e:
            v["error"] = str(e)
            print(f"HATA: {e}", flush=True)
        res["videos"].append(v)
        save()
    res["credit_after"] = credit()
    print(f"\nKREDİ SONRA: {res['credit_after']}", flush=True)
    save()


if __name__ == "__main__":
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "scratch", "kie_batch_result.json")
    asyncio.run(main(sys.argv[1], sys.argv[2], out))
