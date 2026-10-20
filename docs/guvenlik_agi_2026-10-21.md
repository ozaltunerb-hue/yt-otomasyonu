# Güvenlik ağı — 21 Ekim 2026 (Gece 1 / Aşama 2)

Üretim kodu değişmedi. Eklenenler sadece `scripts/`, `tests/`, `docs/` altında. Kie, gerçek GPT ve Notion yazma yok.

## Araçlar

| Betik | Ne yapar | Komut |
|---|---|---|
| `scripts/prompt_snapshot.py` | Yapılandırılmış hattın 19 aktif olayı × 20 tohum (1-20) için seçim + Kie'ye gidecek son prompt. GPT yerine sahte cevap kapıdan kalır, hat kendi kod yedeğine düşer (üretimdeki yol). Her tohumda süreç hafızası boş, geçmiş boş. | `baseline` → `tests/snapshots/prompts_baseline.json` · `diff` → baseline ile karşılaştır (fark varsa çıkış 1) |
| `scripts/prompt_rules.py` | Her prompt için K1-K5, olay × kural tablosu. `--write-known` cırcır dosyasını yeniler. | `.venv\Scripts\python.exe scripts\prompt_rules.py [--baseline] [--md yol]` |
| `scripts/variety_report.py` | Olay başına 20 ardışık üretim, gerçek LRU, geçmiş birikir; iki senaryo (normal / her üretim öncesi deploy). | `--md docs\cesitlilik_2026-10-21.md` |

Testler: `tests/test_prompt_rules.py` (cırcır: yeni ihlal ya da düzelmiş ama listede kalan kayıt başarısız),
`tests/test_prompt_snapshot.py` (tohum kararlılığı, hafıza sızmaz, fark aracı, baseline biçimi, çeşitlilik ölçer).

**Akış (bundan sonraki her değişiklikte):** değişiklikten önce baseline güncel olmalı → değişiklik → `prompt_snapshot.py diff`
sadece hedef olayı göstermeli → bilinçliyse `prompt_snapshot.py baseline` ile yenile ve commit'e ekle. Kural düzeldiyse
`prompt_rules.py --write-known` (ya da elle sil).

**Kendi doğrulaması:** baseline yazıldıktan sonra ayrı bir süreçte `diff` → **"0 olay değişti"**. 19 olayın 18'inde 20
tohum 20 farklı prompt verdi (cephe yangını 19). Hepsi kod yedeği, kurulamayan üretim 0.

## Kural denetimi (mevcut kod, 19 olay × 20 tohum)

| Olay | K1 kamerada yasaklı ifade yok | K2 kamerada yükseklik ifadesi var | K3 kamerada sabitlik ifadesi var | K4 volkanda 'rain' kökü yok | K5 prompt ≤ 175 kelime |
|---|---|---|---|---|---|
| Flash flooding in city streets | ❌ 20/20 (eye level, sidewalk, pans to follow) | ❌ 20/20 (yükseklik ifadesi yok) | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Tidal wave surges over a coastal city street | ❌ 20/20 (eye level, pans to follow) | ✅ | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Mudslide pours down a hillside street | ❌ 20/20 (eye level, pans to follow) | ❌ 6/20 (yükseklik ifadesi yok) | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Rain-soaked slope collapses onto a roadside | ❌ 20/20 (eye level, pans to follow) | ❌ 20/20 (yükseklik ifadesi yok) | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Mud and debris torrent tears through a hillside village | ❌ 20/20 (eye level, pans to follow) | ✅ | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Tornado making landfall | ❌ 20/20 (eye level, pans to follow) | ❌ 20/20 (yükseklik ifadesi yok) | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Tornado crosses a marina quay | ❌ 20/20 (eye level, pans to follow) | ✅ | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Tornado sweeps down a coastal avenue | ❌ 20/20 (eye level, pans to follow) | ✅ | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Wall of flames sweeps into a hillside neighborhood | ❌ 20/20 (eye level, pans to follow) | ✅ | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Flames race up a tower facade | ❌ 20/20 (eye level, pans to follow) | ✅ | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Fire tornado tears across a burning roadside | ❌ 20/20 (pans to follow) | ✅ | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Firefighting helicopter drops water on the flames racing toward a hillside neighborhood | ❌ 20/20 (eye level, pans to follow) | ✅ | ❌ 20/20 (sabitlik ifadesi yok) | ✅ | ✅ |
| Pyroclastic cloud races down into a village street | ✅ | ✅ | ✅ | ✅ | ✅ |
| Volcanic bombs slam into a village street | ✅ | ✅ | ✅ | ✅ | ✅ |
| Avalanche slams into a mountain village | ✅ | ✅ | ✅ | ✅ | ✅ |
| Avalanche crashes down onto a ski lodge | ✅ | ✅ | ✅ | ✅ | ✅ |
| Avalanche rips through a pine forest into a valley | ✅ | ✅ | ✅ | ✅ | ✅ |
| Earthquake collapses an apartment block | ✅ | ✅ | ✅ | ✅ | ✅ |
| Earthquake collapses a row of old stone houses | ✅ | ✅ | ✅ | ✅ | ✅ |

Kural başına ihlal eden olay sayısı: K1 12 · K2 4 · K3 12 · K4 0 · K5 0

K1 yasaklı ifadeler: "eye level", "street level", "ground level", "sidewalk", "pans to follow", "follows the", "tracking", "walks with", "runs with"

K2 yükseklik ifadeleri: "high", "elevated", "rooftop", "balcony", "upper-floor", "upper floor", "high-floor", "overlook", "overlooking", "terrace", "raised", "vantage", "above", "looking down"

K3 sabitlik ifadeleri: "stays fixed", "fixed", "locked-off", "locked off", "stays in place", "never moves", "static", "never descending", "never descends"

K4 rain kökü: rain, rains, rained, raining, rainy (sadece volkan olayları, tüm prompt)

K5: prompt.split() ile en fazla 175 kelime

Bugünkü ihlaller `tests/snapshots/rules_known_violations.json`'a yazıldı (cırcır başlangıcı).

## LRU hafızası tespiti (salt okuma)

**Neden sıfırlanıyor:** dört ortam hafızası modül düzeyinde Python listeleri/sözlükleri, yani sadece süreç belleğinde:
`es._ENV_MEMORY` (çığ), `es._EQ_ENV_MEMORY` (deprem), `es._FIRE_TOR_ENV_MEMORY` (ateş hortumu), `es._VOLC_ENV_MEMORY` ve
`es._VOLC_SPOT_MEMORY` (volkan), ayrıca `es._BEAT_MEMORY` ve `sk._VIEW_MEMORY`. Hiçbiri dosyaya yazılmıyor. Bot
(`python bot.py`) yeniden başlayınca (her deploy, ON_FAILURE yeniden başlatma) boşalır. Railway projesinde volume yok
(GraphQL ile bakıldı: `volumes` boş), dosya sistemi de deploy'da sıfırlanıyor; `data/story_source_log.jsonl` de Railway'de
kalıcı değil.

**Deploy sonrası neler kalıyor:** sadece Notion'dan okunanlar. `get_used_combos` (60 gün, durum
`USED_COMBO_STATUSES`: tamamlandı / upload başarısız / test tamamlandı / teslim edilemedi; **İptal ve Hata sayılmaz**)
combo_key döndürür: `domain|gemi|olay|spot#görünüm#beatçifti|kamera`. Bu yüzden beat çifti, bölge görünümü ve volkan spotu
deploy'dan sonra da LRU'da; diğer eksenler değil.

**Notion'dan geri okunabilirlik (son 30 kayıt salt okundu):**

| Eksen | Kaynak | Durum |
|---|---|---|
| Spot | Combo Key 4. parça | ✅ var |
| Bölge görünümü (sel, kıyı dalga) | Combo Key `#görünüm` | ✅ var |
| Beat çifti | Combo Key `#V4+D8` | ✅ var |
| Ateş hortumu ortamı | Combo Key spotundan türetilebilir (her spot tek ortama ait, `es.fire_env_of_spot`) | ✅ türetilebilir (16 Eki öncesi eski spotlar eşleşmez) |
| Volkan ortamı (kül bulutu, bombalar) | "Ortam" select | ✅ 18 Eki (3) sonrası kayıtlarda var; öncesinde boş |
| Çığ ortamı (dağ, yerleşim, ışık) | "Prompt" kolonundaki `Setting:` satırı | ⚠️ ayrı alan yok, prompttan ayrıştırılabilir (değerler sabit listeden) |
| Deprem ortamı (şehir, sokak, ışık) | "Prompt" `Setting:` satırı | ⚠️ aynı; pus ışığında şehir koyu tonlu yazılır (`EQ_DARK_CITY` ters eşlemesi gerekir) |
| Işık / hava (diğer olaylar) | sadece GPT'nin WEATHER satırına gider, prompta girmez | ❌ geri okunamaz |
| Araç | hikâye metninde (GPT yazar; yedekte beat metni) | ⚠️ güvenilmez, ayrı alan yok |
| Kaçan kişi sayısı | hikâye metninde sayı kelimesi | ⚠️ güvenilmez, ayrı alan yok |
| Kilit cümle (ateş hortumu) | Prompt'un ilk cümlesi / spottan türetilir | ✅ türetilebilir |

**Eksik alanlar:** ortam (çığ, deprem, ateş hortumu için ayrı kolon ya da combo_key parçası), ışık/hava, araç, kişi sayısı.
Ayrıca İptal kayıtları geçmişe girmiyor: iptal edilen üretimin seçimi deploy sonrası unutuluyor (süreç hafızası varken
sayılıyordu). Ölçüm: `docs/cesitlilik_2026-10-21.md` "deploy" tablosunda çığ ve depremde spot 0 tekrardan 8-14 art arda
tekrara, ateş hortumu ortamı 0'dan 7'ye, volkan ortamı 0'dan 3-4'e çıkıyor.

## Güncelleme: Aşama 3 (aynı gün) — çözüldü

Eksen geçmişi artık Notion'da: her üretim seçim anında (Onay'dan önce) "Eksenler" alanına JSON yazar, sonraki üretim
kategorinin son kayıtlarını durum filtresi olmadan (iptaller dahil) okur (`core/axes_history.py`,
`NotionTracker.get_axes_records`). Eski kayıtlar yukarıdaki tablodaki yollarla ayrıştırılır. Spot, ortam, ışık, araç ve
kişide son 2 elenir. Okuma başarısızsa süreç hafızası + Onay'da "⚠️ geçmiş Notion'dan okunamadı". Ölçüm:
`docs/cesitlilik_2026-10-21.md` (deploy senaryosunda da 5 eksende art arda tekrar 0; tek istisna tek spotlu marina).
