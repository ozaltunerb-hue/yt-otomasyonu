# Haftalık YouTube OAuth yenileme (TUR 23). refresh_youtube_token.bat çift tıklamayla çağırır.
#
# Neden onay akışı: Google "Testing" modundaki uygulamada refresh token onaydan 7 gün sonra ölür;
# refresh_token grant'i yeni refresh token DÖNDÜRMEZ (2026-09-25 doğrulandı). Tek çare yeniden onay.
#
# Akış: mevcut Railway token durumu (bilgi) -> tarayıcıda Google onayı -> yeni token ile kanal
# DeepMyster mı doğrula -> Railway YOUTUBE_REFRESH_TOKEN upsert (Railway yeniden deploy eder) ->
# Railway'den geri okuyup tekrar doğrula -> lokal .env + master.env güncelle.
# Hiçbir token değeri ekrana yazılmaz. Başarı: çıkış kodu 0, hata: 1.
import os
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.abspath(os.path.join(ROOT, "..", ".."))
LOCAL_ENV = os.path.join(ROOT, ".env")
MASTER_ENV = os.path.join(REPO_ROOT, "_knowledge", "credentials", "master.env")

PROJECT_ID = "9c2fa508-f546-43f4-b3a8-766ec1054a04"
SERVICE_ID = "0a7ef648-fefd-4c8c-8f32-75a00b04c04c"
ENV_ID = "48418ced-9480-4c7a-a539-4c83522c7c62"
EXPECTED_CHANNEL = "DeepMyster"
KEY = "YOUTUBE_REFRESH_TOKEN"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]


def read_env(path: str) -> dict:
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("\"'")
    return out


def set_env_value(path: str, key: str, value: str) -> None:
    """.env dosyasında key satırını değiştirir, yoksa sona ekler (diğer satırlara dokunmaz)."""
    lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
    new, found = [], False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new.append(f'{key}="{value}"')
            found = True
        else:
            new.append(line)
    if not found:
        new.append(f'{key}="{value}"')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(new) + "\n")


def access_token(client_id: str, client_secret: str, refresh_token: str) -> tuple[str | None, str]:
    r = requests.post("https://oauth2.googleapis.com/token", timeout=20, data={
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token"})
    j = r.json()
    return j.get("access_token"), f"{j.get('error', '')} {j.get('error_description', '')}".strip()


def channel_title(token: str) -> str | None:
    j = requests.get("https://www.googleapis.com/youtube/v3/channels", timeout=20,
                     params={"part": "snippet", "mine": "true"},
                     headers={"Authorization": f"Bearer {token}"}).json()
    items = j.get("items") or []
    return items[0]["snippet"]["title"] if items else None


def railway(query: str, variables: dict, token: str) -> dict:
    j = requests.post("https://backboard.railway.com/graphql/v2", timeout=45, json={"query": query, "variables": variables},
                      headers={"Authorization": f"Bearer {token}"}).json()
    if j.get("errors"):
        raise RuntimeError(f"Railway API: {[e.get('message') for e in j['errors']]}")
    return j["data"]


def railway_vars(token: str) -> dict:
    return railway("query($p:String!,$s:String!,$e:String!){ variables(projectId:$p, serviceId:$s, environmentId:$e) }",
                   {"p": PROJECT_ID, "s": SERVICE_ID, "e": ENV_ID}, token)["variables"]


def main() -> int:
    env = {**read_env(MASTER_ENV), **read_env(LOCAL_ENV)}
    cid, secret, rw = env.get("YOUTUBE_CLIENT_ID"), env.get("YOUTUBE_CLIENT_SECRET"), env.get("RAILWAY_TOKEN")
    if not (cid and secret and rw):
        print("❌ HATA: .env içinde YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET / RAILWAY_TOKEN eksik.")
        return 1

    print("1/5  Railway'deki mevcut token kontrol ediliyor...")
    old = railway_vars(rw).get(KEY, "")
    ok, err = access_token(cid, secret, old) if old else (None, "Railway'de token yok")
    print(f"     Mevcut token: {'geçerli' if ok else 'GEÇERSİZ (' + err + ')'} — yine de yenileniyor (7 günlük süre sıfırlanır).")

    print("2/5  Tarayıcıda Google onay sayfası açılıyor. DeepMyster kanalının hesabıyla gir ve 'İzin ver'e tıkla.")
    print("     'Google bu uygulamayı doğrulamadı' çıkarsa: Gelişmiş -> Devam et.")
    sys.path.insert(0, ROOT)
    from setup_youtube import get_credentials_via_local_server   # sadece onay fonksiyonu; o betiğin main'i çağrılmaz
    creds = get_credentials_via_local_server(cid, secret, SCOPES)
    new = creds.refresh_token
    if not new:
        print("❌ HATA: Google yeni refresh token vermedi. Tekrar dene.")
        return 1

    print("3/5  Yeni token doğrulanıyor...")
    tok, err = access_token(cid, secret, new)
    title = channel_title(tok) if tok else None
    if title != EXPECTED_CHANNEL:
        print(f"❌ HATA: Yeni token '{title or err}' kanalına ait, beklenen '{EXPECTED_CHANNEL}'. Hiçbir yere yazılmadı.")
        return 1
    print(f"     Kanal: {title} ✓")

    print("4/5  Railway'e yazılıyor (servis yeniden deploy edilir, ~3 dk)...")
    railway("mutation($i:VariableUpsertInput!){ variableUpsert(input:$i) }",
            {"i": {"projectId": PROJECT_ID, "environmentId": ENV_ID, "serviceId": SERVICE_ID, "name": KEY, "value": new}}, rw)
    stored = railway_vars(rw).get(KEY, "")
    if stored != new or not access_token(cid, secret, stored)[0]:
        print("❌ HATA: Railway'deki değer doğrulanamadı. Railway panelinden YOUTUBE_REFRESH_TOKEN'ı kontrol et.")
        return 1
    print("     Railway güncellendi ve doğrulandı ✓")

    print("5/5  Lokal .env ve master.env güncelleniyor...")
    for path in (LOCAL_ENV, MASTER_ENV):
        if os.path.exists(path):
            set_env_value(path, KEY, new)
    print("\n✅ BAŞARILI — YouTube token yenilendi, 7 gün geçerli. Gelecek Cuma 16:30'dan önce tekrar çalıştır.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        code = main()
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        code = 1
    sys.exit(code)
