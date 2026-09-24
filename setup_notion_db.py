#!/usr/bin/env python3
"""
DeepMyster — Notion Veritabanı Tek Seferlik Kurulum Scripti
=============================================================
Bu script'i SADECE BİR KEZ, Notion entegrasyonunu ve veritabanını ilk kez
kurarken çalıştırın.

ÖN KOŞUL (ZORUNLU — script çalışmadan önce Notion'da elle yapılmalı):
  Notion API'deki dahili (internal) entegrasyonlar workspace kökünde
  doğrudan sayfa OLUŞTURAMAZ (Notion'un kendi kısıtlaması — sadece public
  entegrasyonlar/personal access token'lar bunu yapabilir). Bu yüzden:
    1. Notion'da HERHANGİ bir sayfa açın (ana sayfanız, boş bir sayfa, fark
       etmez).
    2. Sağ üstteki "..." menüsü → "Connections" (Bağlantılar) → entegrasyo-
       nunuzu ekleyin.
  Script bu paylaşılan sayfayı otomatik bulur ve "DeepMyster Youtube
  Otomasyonu" sayfasını onun ALTINDA bir alt sayfa olarak oluşturur (Notion
  arayüzünde normal bir sayfa gibi görünür, görsel bir fark yoktur).

NE YAPAR:
  1. .env'den NOTION_SOCIAL_TOKEN'ı okur.
  2. Entegrasyonun erişebildiği bir üst sayfa bulur (Notion Search API).
  3. O sayfanın altında "DeepMyster Youtube Otomasyonu" adlı yeni bir sayfa
     oluşturur.
  4. O sayfanın içinde, infrastructure/notion_logger.py'nin beklediği TAM
     14 property ile bir veritabanı oluşturur.
  5. Oluşan veritabanı ID'sini yazdırır — bunu .env'e
     NOTION_DB_YOUTUBE_OTOMASYON olarak eklemeniz gerekir.

NOT: Notion-Version sabit olarak "2022-06-28" kullanılır — bu,
infrastructure/notion_logger.py'nin kullandığı sürümle AYNI. Bu sayede
oluşan veritabanı klasik (tek "data source"lu) şemada kalır ve mevcut
sorgu/yazma kodu değişiklik gerektirmeden çalışır. Notion, bu eski sürümü
veritabanı tek data source'lu kaldığı sürece süresiz destekliyor.
"""
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"  # infrastructure/notion_logger.py ile AYNI sürüm

NOTION_TOKEN = os.environ.get("NOTION_SOCIAL_TOKEN", "")

DATABASE_TITLE = "DeepMyster Youtube Otomasyonu"

# infrastructure/notion_logger.py'nin okuduğu/yazdığı TAM property seti.
# İsimler ve tipler notion_logger.py'deki gerçek kullanımdan birebir çıkarıldı.
DATABASE_PROPERTIES = {
    "Video Adı": {"title": {}},
    "Durum": {
        "select": {
            "options": [
                {"name": "Başlatıldı", "color": "gray"},
                {"name": "Prompt Hazır", "color": "blue"},
                {"name": "Video Üretiliyor", "color": "yellow"},
                {"name": "Video Hazır", "color": "orange"},
                {"name": "Birleştiriliyor", "color": "orange"},
                {"name": "Yükleniyor", "color": "purple"},
                {"name": "✅ Tamamlandı", "color": "green"},
                {"name": "✅ Tamamlandı (Upload Başarısız)", "color": "green"},
                {"name": "✅ Tamamlandı (Test Modu / YouTube Atlandı)", "color": "green"},
                {"name": "❌ Hata", "color": "red"},
            ]
        }
    },
    "Model": {
        "select": {
            "options": [
                {"name": "bytedance/seedance-2-fast", "color": "blue"},
                {"name": "bytedance/seedance-2", "color": "purple"},
            ]
        }
    },
    "Tetikleyici": {
        "select": {
            "options": [
                {"name": "auto", "color": "gray"},
                {"name": "manual", "color": "brown"},
            ]
        }
    },
    "Konu": {"rich_text": {}},
    "Klip Sayısı": {"number": {"format": "number"}},
    "Tarih": {"date": {}},
    "Combo Key": {"rich_text": {}},
    "Prompt": {"rich_text": {}},
    "Video URL": {"url": {}},
    "YouTube URL": {"url": {}},
    "Süre (sn)": {"number": {"format": "number"}},
    "Hata": {"rich_text": {}},
    "Güvenlik": {"rich_text": {}},
    "Hareket": {"rich_text": {}},
}


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _raise_with_body(resp: httpx.Response):
    if resp.status_code >= 300:
        raise RuntimeError(f"Notion API hatası: HTTP {resp.status_code} — {resp.text[:500]}")


def find_accessible_parent_page() -> dict | None:
    """Entegrasyonun paylaşılmış olduğu ilk SAYFAYI bulur (Notion Search API)."""
    resp = httpx.post(
        f"{NOTION_API_URL}/search",
        headers=_headers(),
        json={"filter": {"value": "page", "property": "object"}, "page_size": 10},
        timeout=30,
    )
    _raise_with_body(resp)
    results = resp.json().get("results", [])
    return results[0] if results else None


def create_parent_page(parent_page_id: str) -> str:
    """'DeepMyster Youtube Otomasyonu' sayfasını verilen sayfanın altında oluşturur."""
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "properties": {"title": [{"text": {"content": DATABASE_TITLE}}]},
    }
    resp = httpx.post(f"{NOTION_API_URL}/pages", headers=_headers(), json=payload, timeout=30)
    _raise_with_body(resp)
    return resp.json()["id"]


def create_database(parent_page_id: str) -> str:
    """Verilen sayfanın içinde, notion_logger.py'nin beklediği 14 property'li veritabanını oluşturur."""
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": DATABASE_TITLE}}],
        "properties": DATABASE_PROPERTIES,
    }
    resp = httpx.post(f"{NOTION_API_URL}/databases", headers=_headers(), json=payload, timeout=30)
    _raise_with_body(resp)
    return resp.json()["id"]


def _page_title(page: dict) -> str:
    title_prop = page.get("properties", {}).get("title", {}).get("title", [])
    text = "".join(t.get("plain_text", "") for t in title_prop)
    return text or "(başlıksız sayfa)"


def main():
    if not NOTION_TOKEN:
        print("❌ NOTION_SOCIAL_TOKEN .env içinde bulunamadı veya boş.")
        print("   .env dosyasında NOTION_SOCIAL_TOKEN= satırının değerini doldurun, sonra tekrar deneyin.")
        sys.exit(1)

    print("🔍 Entegrasyonun erişebildiği sayfalar aranıyor...")
    try:
        parent = find_accessible_parent_page()
    except Exception as e:
        print(f"❌ Notion API'ye bağlanılamadı: {e}")
        sys.exit(1)

    if not parent:
        print(
            "❌ Entegrasyonunuzun erişimi olan HİÇBİR sayfa bulunamadı.\n\n"
            "   Notion'da herhangi bir sayfa açın → sağ üstteki '...' menüsü →\n"
            "   'Connections' (Bağlantılar) → entegrasyonunuzu ekleyin.\n"
            "   Sonra bu script'i tekrar çalıştırın."
        )
        sys.exit(1)

    print(f"✅ Üst sayfa bulundu: \"{_page_title(parent)}\" ({parent['id']})")

    print(f"📄 '{DATABASE_TITLE}' sayfası oluşturuluyor...")
    try:
        new_page_id = create_parent_page(parent["id"])
    except Exception as e:
        print(f"❌ Sayfa oluşturulamadı: {e}")
        sys.exit(1)
    print(f"✅ Sayfa oluşturuldu: {new_page_id}")

    print("🗄️ Veritabanı (14 property ile) oluşturuluyor...")
    try:
        database_id = create_database(new_page_id)
    except Exception as e:
        print(f"❌ Veritabanı oluşturulamadı: {e}")
        sys.exit(1)

    print("✅ Veritabanı oluşturuldu!\n")
    print("=" * 60)
    print(f"NOTION_DB_YOUTUBE_OTOMASYON={database_id}")
    print("=" * 60)
    print("Bu satırı .env dosyanıza ekleyin (NOTION_SOCIAL_TOKEN zaten orada, değerini doldurmuş olmalısınız).")


if __name__ == "__main__":
    main()
