"""
Hareket profili — üretilen videonun saniye saniye hareket miktarı (2026-09-24, TUR 9).

Seedance ilk 3-4 saniyede yavaş/durgun açılıyordu. Her üretim videosu için ffmpeg ile
ardışık kareler arası ortalama parlaklık farkı (gri, küçültülmüş) ölçülür ve Notion'a yazılır;
Kie harcamadan cron videolarından istatistik toplanır.

Sınır: el kamerası / chase POV'da kamera sallantısı da hareket sayılır, sayı şişer.
Temiz karşılaştırma fixed_cctv içindir. Yön dönüşü ölçülmez (sadece hareket miktarı).
"""
import re
import shutil
import subprocess

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
_YAVG_RE = re.compile(r"lavfi\.signalstats\.YAVG=([0-9.]+)")


def frame_diffs(path: str, fps: int = 4, width: int = 124) -> list[float]:
    """Ardışık kareler arası ortalama mutlak fark (0-255), fps örneklemiyle."""
    vf = (f"fps={fps},scale={width}:-2,format=gray,tblend=all_mode=difference,"
          f"signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-")
    out = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-vf", vf, "-f", "null", "-"],
                         capture_output=True, text=True, timeout=120)
    values = [float(v) for v in _YAVG_RE.findall(out.stdout)]
    if not values:
        raise RuntimeError(f"ffmpeg hareket ölçümü boş döndü: {out.stderr.strip()[:200]}")
    return values


def summarize(diffs: list[float], fps: int = 4, opening_seconds: int = 3) -> dict:
    """Kare farklarını saniyelere toplar; açılış (ilk N sn) / sonrası oranını hesaplar."""
    per_second = [round(sum(diffs[i:i + fps]) / len(diffs[i:i + fps]), 1) for i in range(0, len(diffs), fps)]
    opening, rest = per_second[:opening_seconds], per_second[opening_seconds:]
    opening_avg = round(sum(opening) / len(opening), 1)
    rest_avg = round(sum(rest) / len(rest), 1) if rest else None
    return {
        "per_second": per_second,
        "opening_avg": opening_avg,
        "rest_avg": rest_avg,
        "opening_ratio": round(opening_avg / rest_avg, 2) if rest_avg else None,
        "peak_second": per_second.index(max(per_second)) + 1,
    }


def motion_profile(path: str) -> dict:
    return summarize(frame_diffs(path))


def format_motion(profile: dict, camera: str = "") -> str:
    """Notion 'Hareket' alanı için tek satır. Oran < 1: açılış sonrasından durgun."""
    parts = [f"ilk3/sonrası={profile['opening_ratio']}",
             f"ilk3={profile['opening_avg']}", f"sonrası={profile['rest_avg']}",
             f"tepe={profile['peak_second']}.sn"]
    if camera:
        parts.append(f"kamera={camera}" + ("" if camera == "fixed_cctv" else " (sallantı dahil)"))
    parts.append("profil " + " ".join(str(v) for v in profile["per_second"]))
    return " | ".join(parts)
