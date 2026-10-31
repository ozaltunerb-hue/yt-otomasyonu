"""
Kanıtlı / deneme ayrımı (31 Eki 2026 (3), Bahadır: "kanıtlı formül" kuralı).

Ders (31 Eki üretim günü): hit formülle (orijinal açılış A + orijinal kamera) üretilen orman yangını 9/10 çıktı; 21 Eki'den
sonra eklenen denenmemiş seçenekler sorun çıkardı (pencere kadrajı: volkanda çerçeve oynadı, hortumda kamera 90° döndü;
volkan açılış D + şafak ışığı: füze gibi duman izli kayalar, Hollywood patlaması; orman açılış C: ölçek küçük).

KURAL
- KANITLI: 21 Eki öncesi orijinal değerler (açılış A, orijinal kamera/kadraj, orijinal ışık, 21 Eki öncesi ortam
  eksenleri) ve paylaşılan bir videoda kullanılmış değerler (Notion Paylaşımlar ↔ üretim kaydı "Eksenler").
- DENEME: diğerleri. Kodda kalır (silinmez), normal üretim rotasyonuna girmez.
- Pencere kadrajı tüm olaylarda DENEME (31 Eki: 2/2 sorun).
- Volkan (bombalar, kül bulutu): hit prompt'ta olmayan açılış/kadraj/ışık DENEME (bombalar 10 Eki 1,36M; kül bulutu
  13 Eki 2,1M). Araç patlatan açılış (bombalar D) DENEME.
- Yetersizlik koruması: bir eksende KANITLI seçenek 2'den azsa o eksende en az riskli bir DENEME değeri rotasyonda kalır
  (GUARD, gerekçeli; pencere ve volkan açılış D hiçbir zaman). Kadraj ve ön planda koruma seçim anında: kanıtlı
  tip/ön plan 2'den azsa 2 olana kadar en az riskli deneme (kendi noktası > ödünç nokta > kütüphane > direk; korkuluk >
  parapet > yaprak > boş) eklenir.

Paylaşılan videolar (21 Eki sonrası eksenli üretimler; öncekiler orijinal değerlerle üretildi):
- 30 Eki meteor (29 Eki 10:58 üretimi, W1+X1): kadraj K2 "High terrace of a seafront villa", ortam O2, ışık
  "overcast grey sky".
- 31 Eki orman yangını (09:44 üretimi, K2+L5): açılış A, ortam A, kadraj çatı (kütüphane), ön plan parapet, ışık
  "harsh bright midday sun through the smoke".
- Volkan: 18 Eki bombalar deneme reeli (16 Eki 17:11 üretimi: balkon, dağ eteği köyü), 25 Eki kül bulutu (17 Eki
  14:13 üretimi: çatı terası, dağ eteği köyü).

Seçimler mevcut ayrı rastgele akışlarda yapılır; bu modül sadece aday listelerini süzer.
"""
from __future__ import annotations

PROVEN, TRIAL = "KANITLI", "DENEME"
# Rotasyon anahtarı: True = normal üretim (sadece KANITLI + koruma). False = eski davranış (tüm değerler; deneme
# üretimi ya da eksen mekaniğini tüm seçeneklerle sınayan testler)
ROTATION_ON = True
WINDOW = "pencere"

FLOOD = "Flash flooding in city streets"
TIDAL = "Tidal wave surges over a coastal city street"
MUDSLIDE = "Mudslide pours down a hillside street"
SLOPE = "Rain-soaked slope collapses onto a roadside"
VILLAGE = "Mud and debris torrent tears through a hillside village"
LANDFALL = "Tornado making landfall"
MARINA = "Tornado crosses a marina quay"
AVENUE = "Tornado sweeps down a coastal avenue"
WILDFIRE = "Wall of flames sweeps into a hillside neighborhood"
FACADE = "Flames race up a tower facade"
FIRE_TORNADO = "Fire tornado tears across a burning roadside"
HELICOPTER = "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood"
PYROCLASTIC = "Pyroclastic cloud races down into a village street"
BOMBS = "Volcanic bombs slam into a village street"
AVA_VILLAGE = "Avalanche slams into a mountain village"
AVA_SKI = "Avalanche crashes down onto a ski lodge"
AVA_FOREST = "Avalanche rips through a pine forest into a valley"
EQ_APT = "Earthquake collapses an apartment block"
EQ_OLD = "Earthquake collapses a row of old stone houses"
METEOR = "Meteor slams into the sea off the coast"

VOLC_HIT_LIGHT = "ash-grey sky lit orange by a distant eruption plume"   # 10 Eki hava metni (hit'lerin ikisinde de)

# ── KANITLI değerler (açık liste; listede olmayan = DENEME) ─────────────────────────────────────────────────────
# Açılış: her olayda A (orijinal kilit cümle). Paylaşılan videolarda başka harf yok.
# Ortam (scene_env, 9 olay): A (bugünkü görünüm). 31 Eki orman yangını paylaşımı da A.
# Işık: olayın 21 Eki öncesi listesi (skeleton_pipeline weather) KANITLI; scene_env.LIGHT_ADD / ENV_LIGHT_ADD (21 Eki)
# DENEME, paylaşılanlar hariç. Volkanda sadece hit hava metni. Meteor (29 Eki, yeni kategori) sadece paylaşılan.
SHARED_LIGHTS = {WILDFIRE: {"harsh bright midday sun through the smoke"},   # 31 Eki paylaşımı
                 METEOR: {"overcast grey sky"}}                              # 30 Eki paylaşımı
VOLC_LIGHTS = {BOMBS: {VOLC_HIT_LIGHT}, PYROCLASTIC: {VOLC_HIT_LIGHT}}
# Volkan kamera noktası = kadraj (volkanda ödünç nokta yok). Bombalar: hit çatı terası (10 Eki) + 18 Eki paylaşımı
# balkon; kül bulutu: hit yamaç terası (13 Eki) + 25 Eki paylaşımı çatı terası.
VOLC_HT = "Hillside terrace facing the erupting volcano"
VOLC_RT = "Rooftop terrace facing the erupting volcano"
VOLC_VB = "Balcony of a village house facing the erupting volcano"
PROVEN_SPOTS = {BOMBS: {VOLC_RT, VOLC_VB}, PYROCLASTIC: {VOLC_HT, VOLC_RT},
                METEOR: {"High terrace of a seafront villa"}}   # 30 Eki paylaşımı (K2)
# Meteor ortamı (29 Eki, yeni): sadece paylaşılan
PROVEN_METEOR_ENVS = {"O2"}
# Paylaşılan kadraj varyantları: (olay, tip, kamera noktası (None = kütüphane), mod) ve ön planı
SHARED_FRAMES = {(WILDFIRE, "çatı", None, None)}           # 31 Eki paylaşımı (çatı kadrajı, kütüphane yeri)
SHARED_FG = {(WILDFIRE, "çatı", None, None, "parapet")}    # önde parapet/korkuluk

# ── Yetersizlik koruması: KANITLI < 2 olan eksende rotasyonda kalan en az riskli DENEME değeri (gerekçeli) ────────
GUARD = {
    "acilis": {
        FLOOD: ("B", "A'nın aynı su duvarı, kavşakta; ilk karede büyük tehdit"),
        TIDAL: ("B", "dev dalga + kıyı yolu, ilk karede büyük tehdit"),
        MUDSLIDE: ("D", "21 Eki üretiminde kullanıldı (Kie'ye gitti), sorun raporu yok"),
        SLOPE: ("B", "çamur kütlesi yolu gömer: A'ya en yakın"),
        VILLAGE: ("B", "tarla çamuru köyün üst sırasına: A'ya en yakın"),
        LANDFALL: ("C", "31 Eki C1+E1 iyi Onay'da kullanıldı (sorun kadrajdaydı)"),
        MARINA: ("B", "yatlar çarpışır: marina hit'ine en yakın"),
        AVENUE: ("D", "kavşakta arabalar savrulur (B minibüsü havaya kaldırır: uydurma hareket riski)"),
        WILDFIRE: ("B", "alev duvarı sırttan iner (C ölçek küçük çıktı, D araç tutuşur)"),
        FACADE: ("B", "alev cepheden yukarı: A'ya en yakın"),
        HELICOPTER: ("D", "31 Eki F6+G7 üretiminde kullanıldı; su tarifi içermiyor"),
        PYROCLASTIC: ("B", "kül bulutu yamaçtan iner, en üst evleri yutar: hit'e en yakın"),
        BOMBS: ("C", "kayalar sokağa düşer: hit'e en yakın (D araç patlatır: hiçbir zaman)"),
        AVA_VILLAGE: ("B", "çığ köyün en üst ahırına: A'ya en yakın"),
        AVA_SKI: ("B", "çığ telesiyej hattı altından tesise"),
        AVA_FOREST: ("B", "çığ ormandan çıkıp ilk evin çitine"),
        EQ_APT: ("B", "blok öne devrilir: büyük, tek hareket"),
        EQ_OLD: ("B", "taş evin cephesi sokağa"),
    },
    "ortam": {
        MUDSLIDE: ("E", "22 Eki üretiminde kullanıldı (Kie'ye gitti), sorun raporu yok"),
        SLOPE: ("B", "dağ yolu + küçük köy: A'ya en yakın"),
        VILLAGE: ("D", "taş çiftlik evleri ve meydan: A'ya en yakın (B çeltik/kazık ev uzak)"),
        LANDFALL: ("C", "31 Eki C1+E1 iyi Onay'da kullanıldı"),
        MARINA: ("B", "lüks marina + apartmanlar: marina hit'ine en yakın"),
        AVENUE: ("D", "Akdeniz kasaba caddesi apartmanlar: kıyı caddesi hit'ine en yakın"),
        WILDFIRE: ("B", "yamaç mahallesi: A'ya en yakın (E 31 Eki'de ölçek küçük çıktı)"),
        FACADE: ("B", "on katlı apartman kuleleri: kule kamerasıyla tutarlı"),
        HELICOPTER: ("C", "31 Eki F6+G7 üretiminde kullanıldı"),
    },
    "light": {
        BOMBS: ("warm orange dusk sky glowing from the eruption", "hit kapağındaki turuncu gün batımına en yakın"),
        PYROCLASTIC: ("warm orange dusk sky glowing from the eruption", "hit hava metnine en yakın (gece yok)"),
        METEOR: ("hazy midday light", "29 Eki test 1'de kullanıldı (sorun hikâyedeydi)"),
    },
    "meteor_env": {METEOR: ("O3", "29 Eki test 1'de kullanıldı (sorun hikâyedeydi)")},
    "spot": {METEOR: ("Rooftop terrace of a hillside villa above the bay", "29 Eki test 1'de kullanıldı")},
}
# Hiçbir zaman koruma adayı olmayanlar
NEVER = {("acilis", BOMBS, "D")}


# Koruma payı (31 Eki (3), Bahadır): kanıtlı ve koruma değeri birlikte aday olduğunda koruma(lar) en fazla %20
GUARD_SHARE = 0.20


def guard_lru(options: list, used: list, depth: int, guards: set) -> tuple[list, list]:
    """Korumalı eksende tekrar önleme: koruma değeri art arda gelmez (son 1); kanıtlı değerler kendi aralarında son
    `depth` (tek kanıtlı değer tekrar edebilir: aksi hâlde LRU korumayı her ikinci üretime zorlar ve %20'yi bozar).
    Korumasız eksende (ya da sadece koruma/sadece kanıtlı) None döner: çağıran eski LRU'yu kullanır."""
    prov = [o for o in options if o not in guards]
    if not ROTATION_ON or not prov or len(prov) == len(options):
        return None
    recent = [u for u in used if u not in (None, "", "-")]
    prov_recent = set(recent[-depth:]) if depth else set()
    cands = ([o for o in prov if o not in prov_recent] or prov) + [o for o in options
                                                                 if o in guards and o not in recent[-1:]]
    return cands, [o for o in options if o not in cands]


def guard_pick(rng, cands: list, guards: set, weights: dict | None = None):
    """Ağırlıklı seçim: adaylarda hem kanıtlı hem koruma varsa korumaların toplam payı GUARD_SHARE."""
    w = weights or {}
    prov = [c for c in cands if c not in guards]
    gs = [c for c in cands if c in guards]
    if not ROTATION_ON or not prov or not gs:
        return rng.choices(cands, weights=[w.get(c, 1) for c in cands], k=1)[0]
    tp, tg = sum(w.get(c, 1) for c in prov), sum(w.get(c, 1) for c in gs)
    ws = [(GUARD_SHARE * w.get(c, 1) / tg) if c in guards else ((1 - GUARD_SHARE) * w.get(c, 1) / tp) for c in cands]
    return rng.choices(cands, weights=ws, k=1)[0]


def guards(event: str, axis: str) -> set:
    """Eksenin koruma değerleri (GUARD; kadraj/ön plan seçim anında: frame_guards)."""
    g = _guard(axis, event)
    return {g} if (g is not None and ROTATION_ON) else set()


def frame_guards(event: str, spot: str, variants: list[dict]) -> tuple[set, set]:
    """Rotasyondaki varyantlarda koruma kadraj tipleri ve (tip, nokta, mod, ön plan) koruma ön planları."""
    if not ROTATION_ON:
        return set(), set()
    proven_types = {f["type"] for f in variants if frame_status(event, spot, f) == PROVEN}
    g_types = {f["type"] for f in variants if f["type"] not in proven_types}
    g_fg = {(f["type"], f.get("pos_spot"), f.get("mode"), f.get("fg")) for f in variants
            if f.get("fg") and fg_status(event, spot, f) == TRIAL}
    return g_types, g_fg


def _guard(axis: str, event: str):
    g = GUARD.get(axis, {}).get(event)
    return g[0] if g else None


def rotation(event: str, axis: str, options: list, proven: set) -> list:
    """options içinden KANITLI olanlar; 2'den azsa koruma değeri (options içindeyse; GUARD'da eksen başına tek değer
    yeter: KANITLI her eksende en az 1). Sıra korunur."""
    if not ROTATION_ON:
        return list(options)
    keep = [o for o in options if o in proven]
    if len(set(keep)) < 2:
        g = _guard(axis, event)
        if g is not None and g in options and g not in keep and (axis, event, g) not in NEVER:
            keep.append(g)
    return keep or list(options)   # güvenlik: hiç kalmazsa eski liste (aday hiç tükenmez)


# ── Eksen süzgeçleri (creative_pipeline / opening_axis / scene_env çağırır) ───────────────────────────────────────
def openings(event: str, cands: list[str]) -> list[str]:
    """Açılış adayları: A + koruma (adaylar ortam ve beat çakışmasından geçmiş olanlar). Boş dönebilir (çağıran ortamı
    A'ya çeker; A her zaman KANITLI)."""
    if not ROTATION_ON:
        return list(cands)
    keep = [o for o in cands if o == "A"]
    g = _guard("acilis", event)
    if g and g in cands and (("acilis", event, g) not in NEVER):
        keep.append(g)
    return keep


def scene_envs(event: str, cands: list[str]) -> list[str]:
    """Ortam (scene_env, 9 olay) adayları: A + koruma (spotla uyumlu olanlar)."""
    return rotation(event, "ortam", cands, {"A"})


def lights(event: str, options: list[str], base: list[str]) -> list[str]:
    """Işık adayları. base: olayın 21 Eki öncesi listesi (volkanda ağırlık listesi)."""
    if event in VOLC_LIGHTS:
        proven = VOLC_LIGHTS[event]
    elif event == METEOR:
        proven = SHARED_LIGHTS[METEOR]
    else:
        proven = set(base) | SHARED_LIGHTS.get(event, set())
    return rotation(event, "light", options, proven)


def env_lights(fam: str, options: list[str], base) -> list[str]:
    """Çığ/deprem ışığı (ortam satırının parçası): 14 Eki listesi KANITLI, 21 Eki eklenenler DENEME."""
    if not ROTATION_ON:
        return list(options)
    return [o for o in options if o in set(base)] or list(options)


def spots(event: str, options: list[str]) -> list[str]:
    """Volkan ve meteor kamera noktası (= kadraj) adayları."""
    if event not in PROVEN_SPOTS:
        return list(options)
    return rotation(event, "spot", options, PROVEN_SPOTS[event])


def meteor_envs(options: list[str]) -> list[str]:
    return rotation(METEOR, "meteor_env", options, PROVEN_METEOR_ENVS)


# ── Kadraj ve ön plan ───────────────────────────────────────────────────────────────────────────────────────────
_FG_RANK = {"korkuluk": 0, "teras_korkuluk": 0, "parapet": 1, "yaprak": 2, "boş": 3, None: 0, WINDOW: 9}


def frame_status(event: str, spot: str, f: dict) -> str:
    """Kadraj varyantının (tip, kamera noktası, mod) durumu; ön plan ayrı (fg_status)."""
    import core.frame_axis as fx
    t, ps, mode = f["type"], f.get("pos_spot"), f.get("mode")
    if t == WINDOW:
        return TRIAL
    if (event, t, ps, mode) in SHARED_FRAMES:
        return PROVEN
    if ps and ps in fx.SPOT_FRAME.get(event, {}):
        kind = fx.native(event, ps)[1]
        if kind == fx.NATIVE:   # volkan/çığ/deprem/meteor: noktanın orijinal cümlesi (ödünçte de aynı cümle)
            return PROVEN if ps in PROVEN_SPOTS.get(event, {ps}) else TRIAL
        if ps == spot and kind == fx.AB and mode == "A":
            return PROVEN   # kendi noktasının orijinal cümlesi (AB mod A)
    return TRIAL           # mod B, sabit-yüksek taşınmış nokta (21 Eki), ödünç şablon, kütüphane, direk


def fg_status(event: str, spot: str, f: dict) -> str:
    t, ps, mode, fg = f["type"], f.get("pos_spot"), f.get("mode"), f.get("fg")
    if (event, t, ps, mode, fg) in SHARED_FG:
        return PROVEN
    if fg is None:
        return PROVEN   # ön plan ekseni yok (mod A, meteor, helikopter)
    import core.frame_axis as fx
    if fg == "korkuluk" and ps in fx.SPOT_FRAME.get(event, {}) and fx.native(event, ps)[1] == fx.NATIVE:
        return PROVEN   # volkan/çığ/deprem orijinal korkuluk metni (ödünç yerli noktada da aynı cümle)
    return TRIAL


def _frame_rank(event: str, spot: str, f: dict) -> tuple:
    t, ps = f["type"], f.get("pos_spot")
    where = 0 if ps == spot else (1 if ps else (3 if t == "direk" else 2))
    return (t == WINDOW, where, _FG_RANK.get(f.get("fg"), 5))


def rotation_frames(event: str, spot: str, variants: list[dict]) -> tuple[list[dict], list[str]]:
    """Kadraj varyantlarından rotasyondakiler + koruma notları. Kadraj: kanıtlı tipler; 2'den azsa en az riskli deneme
    tipinden en iyi varyant(lar). Ön plan: kanıtlı ön planlar; 2'den azsa en az riskli deneme ön planı. Pencere sadece
    başka hiçbir varyant yoksa (son çare)."""
    notes = []
    if not ROTATION_ON:
        return list(variants), notes
    proven = [f for f in variants if frame_status(event, spot, f) == PROVEN]
    types = list(dict.fromkeys(f["type"] for f in proven))
    while len(types) < 2:   # koruma: 2 tip olana kadar en az riskli deneme tipi
        trial = sorted((f for f in variants if frame_status(event, spot, f) == TRIAL and f["type"] != WINDOW
                        and f["type"] not in types), key=lambda f: _frame_rank(event, spot, f))
        if not trial:
            break
        best = _frame_rank(event, spot, trial[0])[:2]
        t0 = trial[0]["type"]
        proven += [f for f in trial if f["type"] == t0 and _frame_rank(event, spot, f)[:2] == best]
        types.append(t0)
        notes.append(f"kadraj koruması: {t0} ({('kendi noktası', 'ödünç nokta', 'kütüphane', 'direk')[best[1]]})")
    if not proven:   # son çare: sadece pencere var
        proven = [f for f in variants if f["type"] == WINDOW] or list(variants)
        notes.append("kadraj: pencereden başka varyant yok (son çare)")
    # ön plan: her (tip, nokta, mod) için
    out = []
    groups = {}
    for f in proven:
        groups.setdefault((f["type"], f.get("pos_spot"), f.get("mode")), []).append(f)
    for key, fs in groups.items():
        ok = [f for f in fs if fg_status(event, spot, f) == PROVEN]
        rest = sorted((f for f in fs if f not in ok), key=lambda f: _FG_RANK.get(f.get("fg"), 5))
        while len(ok) < 2 and rest:   # koruma: 2 ön plan olana kadar en az riskli deneme
            ok.append(rest.pop(0))
        out += ok
    return out, notes


def allowed_variants(event: str, spot: str, variants: list[dict]) -> list[dict]:
    return rotation_frames(event, spot, variants)[0]
