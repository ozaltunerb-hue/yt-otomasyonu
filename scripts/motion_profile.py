# Lokal videoların hareket profilini yazdırır (ffmpeg, Kie yok, bedava).
# Kullanım: python scripts/motion_profile.py video1.mp4 [video2.mp4 ...] [--camera fixed_cctv]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from infrastructure.motion_profile import motion_profile, format_motion


def main(argv: list[str]):
    args = list(argv)
    camera = ""
    if "--camera" in args:
        i = args.index("--camera")
        camera = args[i + 1]
        del args[i:i + 2]
    for path in args:
        print(f"{os.path.basename(path)}: {format_motion(motion_profile(path), camera)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
