# Lokal videoların hareket profilini yazdırır (ffmpeg, Kie yok, bedava).
# Kullanım: python scripts/motion_profile.py video1.mp4 [video2.mp4 ...] [--camera fixed_cctv]
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from infrastructure.motion_profile import motion_profile, format_motion

args = sys.argv[1:]
camera = ""
if "--camera" in args:
    i = args.index("--camera")
    camera = args[i + 1]
    del args[i:i + 2]
for path in args:
    print(f"{os.path.basename(path)}: {format_motion(motion_profile(path), camera)}")
