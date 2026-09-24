#!/usr/bin/env python3
"""
YouTube Kanal Bağlama — OAuth2 Setup Script
============================================
Bu scripti BİR KEZ çalıştırman yeterli.
Tarayıcı açılır → Google hesabınla giriş yap → YouTube izni ver → Token kaydedilir.

Kullanım:
  python3 setup_youtube.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

if sys.platform == "win32":
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Paths ──
PROJECT_DIR = os.path.dirname(__file__)
CREDS_PATH = os.path.join(PROJECT_DIR, "youtube_credentials.json")
TOKEN_PATH = os.path.join(PROJECT_DIR, "youtube_token.json")


REPO_ROOT = os.path.abspath(os.path.join(PROJECT_DIR, "..", ".."))
MASTER_ENV = os.path.join(REPO_ROOT, "_knowledge", "credentials", "master.env")
OAUTH_DIR = os.path.join(REPO_ROOT, "_knowledge", "credentials", "oauth")
OAUTH_TOKEN_PATH = os.path.join(OAUTH_DIR, "youtube_token.json")


def _write_secret(path, text):
    """Kimlik/token dosyasını yalnız sahibin okuyabileceği izinle (0600) yaz."""
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)


def _sync_token_everywhere(creds):
    """Yeni token'ı tüm ilgili dosyalara ve Railway'e senkronize et."""
    refresh_token = creds.refresh_token
    if not refresh_token:
        print("⚠️ Uyarı: creds objesinde refresh_token bulunamadı!")
        return

    # 1. Lokal repo-içi token dosyası
    _write_secret(TOKEN_PATH, creds.to_json())
    print(f"✅ Lokal token güncellendi: {TOKEN_PATH}")

    # 2. _knowledge/credentials/oauth/ altındaki kopya
    if os.path.exists(OAUTH_DIR):
        _write_secret(OAUTH_TOKEN_PATH, creds.to_json())
        print(f"✅ OAuth merkezi deposu güncellendi: {OAUTH_TOKEN_PATH}")

    # 3. master.env dosyasındaki YOUTUBE_REFRESH_TOKEN
    railway_token = ""
    if os.path.exists(MASTER_ENV):
        try:
            lines = []
            found = False
            with open(MASTER_ENV, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("RAILWAY_TOKEN="):
                        railway_token = line.split("=", 1)[1].strip().strip("\"'")
                    if line.startswith("YOUTUBE_REFRESH_TOKEN="):
                        lines.append(f'YOUTUBE_REFRESH_TOKEN="{refresh_token}"\n')
                        found = True
                    else:
                        lines.append(line)
            if not found:
                lines.append(f'\nYOUTUBE_REFRESH_TOKEN="{refresh_token}"\n')
            with open(MASTER_ENV, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"✅ master.env güncellendi: YOUTUBE_REFRESH_TOKEN yazıldı")
        except Exception as e:
            print(f"⚠️ master.env güncellenirken hata: {e}")

    # 4. Railway GraphQL API ile YT_Otomasyonu servisine aktar
    if railway_token:
        try:
            import urllib.request
            railway_project_id = "9c2fa508-f546-43f4-b3a8-766ec1054a04"
            railway_env_id = "48418ced-9480-4c7a-a539-4c83522c7c62"
            railway_service_id = "0a7ef648-fefd-4c8c-8f32-75a00b04c04c"

            mutation = """
            mutation ($input: VariableCollectionUpsertInput!) {
                variableCollectionUpsert(input: $input)
            }
            """
            variables = {
                "input": {
                    "projectId": railway_project_id,
                    "environmentId": railway_env_id,
                    "serviceId": railway_service_id,
                    "variables": {
                        "YOUTUBE_REFRESH_TOKEN": refresh_token
                    }
                }
            }
            payload = json.dumps({"query": mutation, "variables": variables}).encode()
            req = urllib.request.Request(
                "https://backboard.railway.com/graphql/v2",
                data=payload,
                headers={
                    "Authorization": f"Bearer {railway_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode())
                if "errors" in res_data:
                    print(f"⚠️ Railway env güncelleme uyarısı: {res_data['errors']}")
                else:
                    print("🚀 Railway üretim ortamı (yt-otomasyonu) YOUTUBE_REFRESH_TOKEN senkronize edildi!")
        except Exception as re:
            print(f"⚠️ Railway otomatik güncelleme yapılamadı ({re}). Lütfen Railway env'ine manuel ekleyin.")


# ── YouTube API Scopes ──
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def get_credentials_via_local_server(client_id, client_secret, scopes, port=8080):
    """
    Yerel HTTP sunucusu açarak OAuth2 kodunu yakalar ve doğrudan token alır.
    oauthlib'in MismatchingStateError (CSRF) hatasını tamamen bertaraf eder.
    """
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs, urlencode
    import urllib.request
    import webbrowser

    auth_code = None
    auth_error = None

    redirect_uri = f"http://localhost:{port}/"
    auth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(auth_params)}"

    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code, auth_error
            parsed = urlparse(self.path)
            # favicon.ico çağrılarını yoksay
            if parsed.path == "/favicon.ico":
                self.send_response(404)
                self.end_headers()
                return

            query_params = parse_qs(parsed.query)
            if "code" in query_params:
                auth_code = query_params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Yetkilendirme Başarılı</title></head>
<body style="font-family:sans-serif;text-align:center;padding-top:60px;background:#f0fdf4;">
<h1 style="color:#16a34a;font-size:32px;">✅ Yetkilendirme Başarılı!</h1>
<p style="font-size:18px;color:#374151;margin-top:16px;">YouTube kanal bağlantısı başarıyla tamamlandı.</p>
<p style="font-size:15px;color:#6b7280;">Bu sekmeyi güvenle kapatıp terminale dönebilirsiniz.</p>
</body>
</html>"""
                self.wfile.write(html.encode("utf-8"))
            elif "error" in query_params:
                auth_error = query_params["error"][0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"Hata: {auth_error}".encode("utf-8"))
            else:
                # Kullanıcı localhost:8080 adresine doğrudan girdiğinde otomatik olarak Google girişine yönlendir
                self.send_response(302)
                self.send_header("Location", auth_url)
                self.end_headers()

        def log_message(self, format, *args):
            return

    server = HTTPServer(("", port), OAuthCallbackHandler)
    server.timeout = 300  # 5 dakika bekleme süresi

    print(f"\n🌐 Google yetkilendirme sayfası açılıyor...")
    print(f"\nBağlantı: {auth_url}\n")
    try:
        if hasattr(os, "startfile"):
            os.startfile(auth_url)
        else:
            webbrowser.open(auth_url)
    except Exception:
        try:
            webbrowser.open(auth_url)
        except Exception:
            pass

    while not auth_code and not auth_error:
        server.handle_request()

    server.server_close()

    if auth_error:
        raise RuntimeError(f"Google OAuth onayında hata döndü: {auth_error}")
    if not auth_code:
        raise RuntimeError("Yetkilendirme kodu alınamadı (zaman aşımı).")

    # Kodu Google token endpoint'inden doğrudan takas et
    token_url = "https://oauth2.googleapis.com/token"
    token_data = urlencode({
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request(token_url, data=token_data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))

    from google.oauth2.credentials import Credentials
    creds = Credentials(
        token=tokens.get("access_token"),
        refresh_token=tokens.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )
    return creds



def main():
    print("=" * 60)
    print("🔐 YouTube Kanal Bağlama — OAuth2 Setup")
    print("=" * 60)

    # ── 1. Bağımlılık kontrolü ──
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError as e:
        print(f"\n❌ Eksik bağımlılık: {e}")
        print("   Çözüm: pip install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    # ── 2. Client ID & Secret ──
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        if os.path.exists(MASTER_ENV):
            with open(MASTER_ENV, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("YOUTUBE_CLIENT_ID="):
                        client_id = line.split("=", 1)[1].strip().strip("\"'")
                    elif line.startswith("YOUTUBE_CLIENT_SECRET="):
                        client_secret = line.split("=", 1)[1].strip().strip("\"'")

    if not client_id or not client_secret:
        print("\n❌ YOUTUBE_CLIENT_ID veya YOUTUBE_CLIENT_SECRET bulunamadı!")
        print(f"   master.env dosyasını ({MASTER_ENV}) kontrol et.")
        sys.exit(1)

    print(f"\n✅ Client ID: {client_id[:20]}...")
    print(f"✅ Client Secret: {client_secret[:4]}{'*' * 10}")

    # ── 3. credentials.json oluştur ──
    credentials_data = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }

    _write_secret(CREDS_PATH, json.dumps(credentials_data, indent=2))
    print(f"\n📝 Credentials dosyası oluşturuldu: {CREDS_PATH}")

    # ── 4. Mevcut token var mı? ──
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            if creds and creds.valid:
                print(f"\n✅ Mevcut token geçerli! Yeniden yetkilendirme gerekmez.")
            elif creds and creds.refresh_token:
                print("\n🔄 Token süresi dolmuş, yenileniyor...")
                try:
                    creds.refresh(Request())
                    _sync_token_everywhere(creds)
                    print("✅ Token başarıyla yenilendi!")
                except Exception as re:
                    print(f"⚠️ Token refresh başarısız oldu ({re}).")
                    print("   Google OAuth 'Testing' modunda refresh token 7 günde bir geçersiz kılınır.")
                    print("   Yeni tarayıcı oturumu ile taze yetkilendirme yapılacak...")
                    creds = None
            else:
                creds = None
        except Exception as te:
            print(f"⚠️ Mevcut token okunamadı: {te}")
            creds = None

    # ── 5. Yeni yetkilendirme ──
    if not creds or not creds.valid:
        print("\n🌐 YouTube yetkilendirmesi başlatılıyor...")
        print("   (Eğer 'This app isn't verified' uyarısı gelirse → Advanced → Go to ... tıkla)\n")

        creds = get_credentials_via_local_server(
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
            port=8080,
        )

        _sync_token_everywhere(creds)

    # ── 6. Kanal bilgisi test ──
    print("\n🔍 YouTube kanalı kontrol ediliyor...")
    try:
        youtube = build("youtube", "v3", credentials=creds)
        response = youtube.channels().list(
            part="snippet,statistics",
            mine=True
        ).execute()

        channels = response.get("items", [])
        if channels:
            ch = channels[0]
            snippet = ch.get("snippet", {})
            stats = ch.get("statistics", {})

            print(f"\n{'=' * 60}")
            print(f"✅ YOUTUBE KANALI BAŞARIYLA BAĞLANDI!")
            print(f"{'=' * 60}")
            print(f"   📺 Kanal: {snippet.get('title', 'N/A')}")
            print(f"   📝 Açıklama: {snippet.get('description', 'N/A')[:80]}")
            print(f"   👥 Abone: {stats.get('subscriberCount', 'N/A')}")
            print(f"   🎬 Video: {stats.get('videoCount', 'N/A')}")
            print(f"   👁️ Görüntülenme: {stats.get('viewCount', 'N/A')}")
            print(f"   🔗 ID: {ch.get('id', 'N/A')}")
            print(f"\n   Token: {TOKEN_PATH}")
            print(f"   ⚠️ Bu token ile video yükleme yapılabilir!")

            # Eskiden burada deepmyster_2026-09-18_ice_floe.mp4 dosyası varsa otomatik yükleniyordu.
            # Video 2026-09-19'da yayınlandı ve dosya yedek olarak saklanıyor; her çalıştırmada
            # kopya yüklenirdi. Kaldırıldı (2026-09-25). Haftalık yenileme: refresh_youtube_token.bat.

        else:
            print("\n⚠️ Bu Google hesabında YouTube kanalı bulunamadı.")
            print("   YouTube'da bir kanal oluşturup scripti tekrar çalıştır.")

    except Exception as e:
        print(f"\n⚠️ Kanal bilgisi kontrolünde hata: {e}")
        print("   Token yine de kaydedildi.")

    print(f"\n{'=' * 60}")
    print("📋 Son durum:")
    print("   1. Token lokal ve Railway'e senkronize edildi.")
    print("   2. Cron çalıştığında otomatik olarak YouTube'a Shorts yüklenecek.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

