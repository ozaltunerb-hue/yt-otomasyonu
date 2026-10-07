# Push öncesi tam test paketi, ÇEVRİMDIŞI (7 Eki kuralı: tamamı yeşil değilse push yok).
# Kullanım (proje kökünden): .venv\Scripts\python.exe scripts\run_tests_offline.py
#
# Neden: yerelde gerçek anahtarlı .env var, CI'da yok. Bir test mock'u kaçırırsa gerçek Kie/OpenAI/Google/Railway
# çağrısı olmasın diye localhost dışı tüm bağlantılar engellenir. CI'daki sahte anahtarlar verilir.
# Ayrıca testler gerçek .env, master.env ve dashboard_data/ dosyalarına dokunduysa koşu BAŞARISIZ sayılır.
# Çıkış kodu: 0 = tamamı yeşil, ağ denemesi yok, gerçek dosyalar aynı; 1 = aksi.
import os
import socket
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHED = [os.path.join(ROOT, ".env"),
           os.path.join(ROOT, "..", "..", "_knowledge", "credentials", "master.env"),
           os.path.join(ROOT, "dashboard_data")]
# .github/workflows'taki unittest adımıyla aynı
CI_ENV = {"KIE_API_KEY": "ci-dummy", "OPENAI_API_KEY": "sk-ci-dummy",
          "NOTION_SOCIAL_TOKEN": "ci-dummy", "NOTION_DB_YOUTUBE_OTOMASYON": "ci-dummy"}
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1", None)

blocked = []


def snapshot() -> dict:
    """İzlenen dosyaların (klasörse içindekilerin) boyut + değişiklik zamanı."""
    out = {}
    for path in WATCHED:
        files = [os.path.join(path, f) for f in sorted(os.listdir(path))] if os.path.isdir(path) else [path]
        for f in files:
            if os.path.isfile(f):
                st = os.stat(f)
                out[os.path.normpath(f)] = (st.st_size, st.st_mtime_ns)
    return out


def block_network() -> None:
    real_connect, real_getaddrinfo = socket.socket.connect, socket.getaddrinfo

    def connect(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if host not in LOCAL_HOSTS:
            blocked.append(str(host))
            raise ConnectionRefusedError(f"ÇEVRİMDIŞI TEST: {host} engellendi")
        return real_connect(self, address, *args, **kwargs)

    def getaddrinfo(host, *args, **kwargs):
        if host not in LOCAL_HOSTS:
            blocked.append(str(host))
            raise socket.gaierror(f"ÇEVRİMDIŞI TEST: {host} engellendi")
        return real_getaddrinfo(host, *args, **kwargs)

    socket.socket.connect = connect
    socket.getaddrinfo = getaddrinfo


def main() -> int:
    os.chdir(ROOT)
    sys.path.insert(0, ROOT)
    os.environ.update(CI_ENV)
    if ".venv" not in sys.executable:
        print(f"⚠️  .venv dışındaki Python ile koşuyor: {sys.executable}")
    before = snapshot()
    block_network()
    result = unittest.main(module=None, argv=["unittest", "discover", "-s", "tests"], exit=False).result
    after = snapshot()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))

    print("\n=== Çevrimdışı test özeti ===")
    print(f"Test: {result.testsRun}, hata: {len(result.errors)}, başarısız: {len(result.failures)}")
    print(f"Engellenen ağ denemesi: {len(blocked)}" + (f" ({', '.join(sorted(set(blocked)))})" if blocked else ""))
    print("Gerçek dosyalarda değişiklik: " + (", ".join(os.path.relpath(c, ROOT) for c in changed) or "yok"))
    ok = result.wasSuccessful() and not blocked and not changed
    print("✅ PUSH EDİLEBİLİR" if ok else "❌ PUSH YOK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
