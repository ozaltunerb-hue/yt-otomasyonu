# 🧭 DeepMyster (YT_Otomasyonu) — BAŞLANGIÇ REHBERİ & DERSLER

> **Bu dosyayı her oturum başında İLK oku.** DeepMyster YouTube Shorts üretiminin kritik kuralları ve dersleri buradadır.

---

## 🚨 KRİTİK KURAL: Zorunlu İnsan / Mürettebat Varlığı & Rol Çeşitliliği

**Tarih / Karar:** 2026-09-09 (Dolunay direktifi)

### 1. Sıfır İnsansız Video Toleransı
- **Her videoda mutlaka en az bir insan/mürettebat görünmelidir.**
- İnsansız (sadece boş gemi/deniz) video üretimi **KESİNLİKLE YASAKTIR**.
- İnsanlar yalnızca arka planda duran cansız figüranlar olmamalı; senaryoya uygun şekilde olayın, krizin, tehlikeli manevranın veya mücadelenin **aktif parçası** olmalıdır.

### 2. Doğal & Aktif Roller
Senaryo ve kategoriye göre roller çeşitlendirilmelidir:
- **Kaptan & Zabitler:** Köprüüstünde (wheelhouse/bridge) acil durum kontrolleri, dümen çarkı, itici (thruster) kolları, radar ekranları başında veya açık bridge wing'de arama ışığı/dürbün ile fırtınayı yönetirken.
- **Güverte Personeli (Deckhands / Seamen):** Yüksek görünürlüklü (hi-vis) fırtına tulumları/can yelekleri içinde su basmış güvertede lashing zincirlerini sıkarken, kayan yükleri bağlarken, can salı veya seyyar drenaj pompası kurarken.
- **Marina Personeli & Palamar:** Yüzer pontonlarda koşarak kontrolden çıkan yata usturmaça (fender) atarken, kakıçla tekneleri fırlatmadan ayırırken veya yakıt iskelesinde acil hat bağlarken.
- **Liman Çalışanları & Halatçılar:** Rıhtımda aşırı gerilen palamar halatlarından kaçarken, kopan halat anında refleks verirken veya kılavuz botuyla dev gemiye yanaşırken.
- **Yolcular:** Fırtınada veya sert yanaşmada korkuluklara (safety handrails) tutunup sarsıntıya direnirken, güverte zabitlerinin yönlendirmesiyle güvenli bölgeye geçerken.
- **Kurtarma Ekipleri (Coast Guard / SAR):** Zodyak/RIB botu dalgalı sörfe indirirken, helikopter vinciyle güverteye inen dalgıçlar veya can simidi fırlatan kurtarma ekipleri.
- **Gemi Mühendisleri (Engine Room):** Makine dairesinde titreşen borular ve kırmızı acil durum ışıkları altında jeneratör/şalter veya hidrolik dümen arızasına müdahale ederken.

### 3. Şablon Tekrarını Önleme (Rol & Kamera Matrisi)
Tekrar eden insan/kamera şablonlarından kaçınılır. Her videoda farklı bir insan rolü ve kamera açısı rotasyona girer:
- Kamera Perspektifleri: `bridge wheelhouse cam`, `deck action cam`, `crew bodycam`, `quayside CCTV`, `marina pontoon cam`, `pilot boat cam`, `engine room cam`, `telephoto dock cam`.

---

## 🏗️ 3 Katmanlı Senaryo & Prompt Mimarisi

1. **Katman 1 (`creative_engine.py`):** 8 Denizcilik Kategorisi + Gemi + İnsanlı Olay + Kamera + Aktif Mürettebat Seed Havuzu.
2. **Katman 2 (`prompt_generator.py` - `SCENARIO_WRITER_SYSTEM`):** GPT-4o ile 15 saniyelik tek plan gerçekçi belgesel sahnesi (insan aksiyonu zorunlu).
3. **Katman 3 (`PROMPT_SIMPLIFIER_SYSTEM`):** Seedance 2.0 / Kling için 15-30 kelimelik basit, fotogerçekçi, insan aksiyonu içeren video prompt'u.

---

## 🛠️ Hızlı Doğrulama Komutu

```bash
# Proje dizininde test çalıştırması:
python main.py --dry-run
```
