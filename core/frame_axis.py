"""
Kadraj ekseni (21 Eki 2026, Gece 1 / Aşama 4): kadraj tipi + ön plan + kamera modu.

Model: kanıtlanmış volkan/çığ/deprem kamera şablonu (yüksek, sabit, inmez, tehdit hep karede, ön plan, tek çekim).
Hiçbir yeni cümlede eye level / street level / ground level / sidewalk / pans to follow / follows the / tracking /
walks with / runs with yok (scripts/prompt_rules.py K1-K3, tests/test_frame_axis.py).

- Kadraj tipi: balkon, çatı, pencere, tepe, direk (+ teras: sadece mevcut teras/promenat/basamak noktaları). Olay
  başına izinli tipler FRAME_EVENTS. Ağırlık: direk 1 (test adayı), diğerleri 2.
- Spot (sahne, GPT PLACE, beat dışlamaları) eskisi gibi seçilir; kamera yeri kadrajdan gelir:
  1) kadraj = seçilen spotun kendi tipi -> spotun kendi kamera yeri,
  2) olayda o tipte başka bir spot varsa (ve seçilen beat'ler orada dışlanmamışsa) -> onun kamera yeri ("ödünç"),
  3) yoksa -> kütüphane yeri (olayın sahnesiyle).
- Kamera modu (sadece A/B spotlarda): A = bugünkü cümle kelimesi kelimesine, B = aynı yer için ana şablon.
- Volkan/çığ/deprem: mevcut cümleler aynen; sadece ön plan ekseni (mevcut korkuluk metni ya da "boş"). Korkuluk
  seçildiğinde cümle bugünküyle birebir aynı.
- Seçim ayrı bir rastgele akıştan (side_rng): ana akış tüketilmez, mevcut seçimler (spot, beat, ortam...) her tohumda
  aynı kalır.
"""
from __future__ import annotations

import hashlib
import random

# ── Kütüphane ────────────────────────────────────────────────────────────────────────────────────────────────────
FRAME_WEIGHTS = {"balkon": 2, "çatı": 2, "pencere": 2, "tepe": 2, "direk": 1, "teras": 2}
# Ön plan anahtarları -> metin (kütüphane şablonları). Volkan/çığ/deprem kendi metinleri NATIVE_FG'de.
# K5 (175 kelime): ön plan metinleri Bahadır'ın metinlerinden kısaldı (anlam aynı). Uzun hâlleri: "a corner of the
# balcony railing in the foreground", "the edge of a low parapet wall in the foreground", "the edge of the open window
# frame at one side of the frame", "a few leaves at the edge of the frame".
FG_TEXT = {"korkuluk": "a railing corner in the foreground",
           "parapet": "a low parapet edge in the foreground",
           "pencere": "the open window frame at one side",
           "yaprak": "a few leaves at the frame edge",
           "teras_korkuluk": "a railing corner in the foreground",
           "boş": "nothing in the foreground"}
FRAME_FG = {"balkon": ("korkuluk", "boş"), "çatı": ("parapet", "boş"), "pencere": ("pencere",),
            "tepe": ("yaprak", "boş"), "direk": (), "teras": ("teras_korkuluk", "boş")}
# Kütüphane yeri (olayda o tipte spot yoksa): yer metni sahneyi içerir (sahne cümlede bir kez geçer)
LIB_POS = {"balkon": ("on a high balcony above {scene}", "balcony"), "çatı": ("on a flat rooftop above {scene}", "rooftop"),
           "tepe": ("on a hillside overlook above {scene}", "overlook"), "pencere": ("across from {scene}", "window"),
           "direk": ("", "")}
SHAKE = "slight hand shake"


def generic_camera(ftype: str, pos: str, perch: str, scene: str, threat: str, fg: str | None,
                   shake: str = SHAKE) -> str:
    """Ana şablondan türeyen cümle (yüksek bakış, sabit, inmez, tehdit hep karede, ön plan, tek çekim). Sahne yer
    metninin içinde (175 kelime için tekrar yok). fg: ön plan metni (direkte yok)."""
    tail = "one continuous shot, no zoom, no cuts."
    if ftype == "direk":
        return (f"Footage from a fixed high security camera on a tall pole above {scene}, slightly wide lens, no hand "
                f"shake, no on-screen text, no timestamp, high vantage looking down toward {threat}; the camera stays "
                f"fixed, {threat} always in frame; {tail}")
    if ftype == "pencere":
        return (f"Handheld footage filmed through an open upper-floor window {pos}, high vantage looking down toward "
                f"{threat}; {shake}, the camera stays fixed at the window, tilting only slightly, never descending, "
                f"{threat} always in frame, {fg}; {tail}")
    return (f"Handheld footage shot by a person standing {pos}, high vantage looking down toward {threat}; {shake}, "
            f"the camera stays fixed on the {perch}, tilting only slightly, never descending, {threat} always in frame, "
            f"{fg}; {tail}")


def fire_tornado_b(pos: str, perch: str, fg: str) -> str:
    """Ateş hortumu mod B: mod A'nın kuralları (hortum karenin yarısı, tepesi kesilmez, önde 2-3 kişi kaçar), takip
    yerine sabit kamera. 175 kelime için kısa (A'dan en fazla birkaç kelime uzun)."""
    return (f"Handheld footage shot by a person standing {pos}, high vantage, the tornado filling half the frame, top "
            f"never cut off, two or three people fleeing close below; slight hand shake, the camera stays fixed, {fg}; "
            f"one continuous shot, no zoom, no cuts.")


# ── Olaylar ──────────────────────────────────────────────────────────────────────────────────────────────────────
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
ERUPTION = "Volcano erupts and a shockwave blows out windows"
PYROCLASTIC = "Pyroclastic cloud races down into a village street"
BOMBS = "Volcanic bombs slam into a village street"
AVA_VILLAGE = "Avalanche slams into a mountain village"
AVA_SKI = "Avalanche crashes down onto a ski lodge"
AVA_FOREST = "Avalanche rips through a pine forest into a valley"
EQ_APT = "Earthquake collapses an apartment block"
EQ_OLD = "Earthquake collapses a row of old stone houses"
VOLCANO = (ERUPTION, PYROCLASTIC, BOMBS)
AVALANCHE = (AVA_VILLAGE, AVA_SKI, AVA_FOREST)
EARTHQUAKE = (EQ_APT, EQ_OLD)

# types: izinli kadraj tipleri (görev listesi; "teras" = mevcut teras/promenat/basamak noktalarının tipi, sadece
# yerli/ödünç, kütüphanesi yok). scene / threat: şablondaki {sahne} / {tehdit}. lib: kütüphane yeri (tip -> (yer, perch))
FRAME_EVENTS = {
    FLOOD: {"types": ("balkon", "çatı", "pencere", "direk"), "scene": "the street",
            "threat": "the floodwater"},
    TIDAL: {"types": ("balkon", "çatı", "pencere", "direk", "teras"), "scene": "the coastal street",
            "threat": "the tidal wave"},
    MUDSLIDE: {"types": ("balkon", "çatı", "pencere"), "scene": "the steep hillside street", "threat": "the mud flow"},
    SLOPE: {"types": ("balkon", "çatı", "tepe"), "scene": "the hillside road", "threat": "the mud torrent",
            "lib": {"çatı": ("on the flat roof of a roadside shop", "roof")}},
    VILLAGE: {"types": ("balkon", "çatı", "tepe", "teras"), "scene": "the hillside village",
              "threat": "the debris torrent"},
    LANDFALL: {"types": ("balkon", "çatı", "pencere", "direk"), "scene": "the waterfront", "threat": "the tornado",
               "lib": {"balkon": ("on a high balcony of a seafront hotel", "balcony")}},
    MARINA: {"types": ("balkon", "çatı", "pencere", "direk"), "scene": "the marina and quay", "threat": "the tornado",
             "lib": {"çatı": ("on the flat rooftop of a marina hotel", "rooftop")}},
    AVENUE: {"types": ("balkon", "çatı", "pencere", "direk"), "scene": "the coastal avenue",
             "threat": "the tornado"},
    WILDFIRE: {"types": ("balkon", "çatı", "tepe"), "scene": "the burning slope",
               "threat": "the wall of flames"},
    FACADE: {"types": ("balkon", "çatı", "pencere"), "scene": "the burning tower", "threat": "the burning facade",
             "lib": {"pencere": ("of an apartment across from the burning tower", "window")}},
    FIRE_TORNADO: {"types": ("balkon", "çatı", "tepe"), "scene": None, "threat": "the fire tornado"},
    HELICOPTER: {"types": ("balkon", "çatı", "tepe"), "scene": "the hillside neighborhood",
                 "threat": "the helicopter"},
    ERUPTION: {"types": ("balkon", "çatı", "tepe", "pencere")},
    PYROCLASTIC: {"types": ("balkon", "çatı", "tepe", "pencere")},
    BOMBS: {"types": ("balkon", "çatı", "tepe", "pencere")},
    AVA_VILLAGE: {"types": ("balkon", "teras", "pencere")},
    AVA_SKI: {"types": ("balkon", "teras", "pencere")},
    AVA_FOREST: {"types": ("balkon", "teras", "pencere")},
    EQ_APT: {"types": ("balkon", "çatı", "pencere")},
    EQ_OLD: {"types": ("balkon", "çatı", "pencere")},
}
# Ateş hortumu sahnesi ortamdan (event_structure.FIRE_TOR_ENVS)
FIRE_SCENE = {"forest_edge": "the wooded neighborhood", "tree_street": "the tree-lined street",
              "village_woods": "the village houses"}

# Spot -> (yerli tip, tür, kamera yeri, perch). Tür: "AB" (mod A bugünkü cümle / B şablon), "sabit" (alçak kamera
# yüksek yere taşındı, mod A yok), "yerli" (volkan/çığ/deprem: bugünkü cümle + ön plan ekseni).
AB, FIXED, NATIVE = "AB", "sabit", "yerli"
SPOT_FRAME = {
    FLOOD: {"Downtown city center": ("balkon", FIXED, "on a high balcony over a downtown street", "balcony"),
            "Dense urban downtown": ("çatı", FIXED, "on a flat rooftop above a dense downtown street", "rooftop"),
            "Commercial city streets": ("pencere", FIXED, "across from a commercial street", "window"),
            "High-rise city district": ("balkon", FIXED, "on a high balcony of a high-rise above the street",
                                        "balcony")},
    TIDAL: {"Coastal road below a seafront promenade": ("teras", AB, "at the railing of a raised seafront promenade",
                                                        "promenade"),
            "Coastal street of low shopfronts": ("balkon", AB, "on a second-floor balcony", "balcony"),
            "Coastal avenue behind a seawall": ("teras", AB, "on top of the seawall", "seawall")},
    MUDSLIDE: {"Balcony across a steep hillside street": ("balkon", AB, "on a balcony across the steep hillside street",
                                                          "balcony"),
               "Rooftop terrace below a hillside street": ("çatı", AB, "on a rooftop terrace just below the hillside "
                                                                       "street", "rooftop terrace"),
               "Side stairway off a narrow hillside lane": ("pencere", FIXED, "across from the narrow hillside lane",
                                                            "window")},
    SLOPE: {"Behind the guardrail of a hillside road": ("balkon", FIXED, "on the high balcony of a roadside house "
                                                                        "facing the slope", "balcony"),
            "Far edge of the road across from the slope": ("tepe", FIXED, "on the opposite slope of the valley above "
                                                                          "the road", "slope")},
    VILLAGE: {"Terrace on the opposite hillside": ("tepe", AB, "on a terrace on the opposite hillside", "terrace"),
              "High steps on the village square": ("teras", AB, "on the high steps at the edge of the village square",
                                                   "steps"),
              "Upper-floor balcony of a village house": ("balkon", AB, "on the upper-floor balcony of a village house",
                                                         "balcony")},
    LANDFALL: {"Beachfront promenade": ("balkon", FIXED, "on a high balcony of a seafront hotel above the promenade",
                                        "balcony"),
               "Residential coastal district": ("pencere", FIXED, "across from a residential coastal street", "window"),
               "Downtown city center": ("çatı", FIXED, "on a flat rooftop above the downtown waterfront", "rooftop")},
    MARINA: {"High marina balcony": ("balkon", AB, "on a high balcony overlooking the marina", "balcony")},
    AVENUE: {"High balcony over a downtown avenue": ("balkon", AB, "on a high balcony across the street", "balcony"),
             "Upper-floor balcony over a residential avenue": ("balkon", AB, "on an upper-floor balcony across the "
                                                                             "street", "balcony"),
             "High balcony over a high-rise avenue": ("balkon", AB, "on a high balcony across the street", "balcony")},
    WILDFIRE: {"Balcony of a hillside house": ("balkon", AB, "on a balcony of a hillside house", "balcony"),
               "Embankment above the village road": ("tepe", AB, "on a roadside embankment above the village road",
                                                     "embankment")},
    FACADE: {"Balcony across from a downtown tower": ("balkon", AB, "on a high balcony across the street from the "
                                                                    "tower", "balcony"),
             "Rooftop terrace across from a downtown tower": ("çatı", AB, "on a rooftop terrace across the street from "
                                                                          "the tower", "rooftop terrace"),
             "Balcony across from a coastal high-rise": ("balkon", AB, "on a high balcony across the street from the "
                                                                       "tower", "balcony"),
             "Rooftop terrace across from a coastal high-rise": ("çatı", AB, "on a rooftop terrace across the street "
                                                                             "from the tower", "rooftop terrace")},
    FIRE_TORNADO: {"High balcony at the edge of a wooded neighborhood": ("balkon", AB, "on a high balcony above the "
                                                                                       "wooded neighborhood", "balcony"),
                   "Rooftop terrace above a wooded residential area": ("çatı", AB, "on a rooftop terrace above a wooded "
                                                                                   "residential area", "rooftop terrace"),
                   "High balcony over a tree-lined residential street": ("balkon", AB, "on a high balcony overlooking "
                                                                                       "a tree-lined residential street",
                                                                         "balcony"),
                   "Upper-floor terrace above a street of houses": ("çatı", AB, "on an upper-floor terrace above a "
                                                                                "street of houses", "terrace"),
                   "Hillside terrace above a village": ("tepe", AB, "on a hillside terrace above the village houses",
                                                        "terrace"),
                   "High balcony of a village house": ("balkon", AB, "on a high balcony of a village house", "balcony")},
    HELICOPTER: {"Balcony of a hillside house": ("balkon", AB, "on a balcony of a hillside house", "balcony"),
                 "Embankment above the village road": ("tepe", AB, "on a roadside embankment above the village road",
                                                       "embankment")},
}
for _e in VOLCANO:
    SPOT_FRAME[_e] = {"Hillside terrace facing the erupting volcano": ("tepe", NATIVE, None, "terrace"),
                      "Rooftop terrace facing the erupting volcano": ("çatı", NATIVE, None, "rooftop"),
                      "Balcony of a village house facing the erupting volcano": ("balkon", NATIVE, None, "balcony")}
for _e in AVALANCHE:
    SPOT_FRAME[_e] = {"Terrace at the edge of the village": ("teras", NATIVE, None, None),
                      "Balcony of a chalet at the edge of the village": ("balkon", NATIVE, None, None),
                      "Terrace of the lift station": ("teras", NATIVE, None, None)}
for _e in EARTHQUAKE:
    SPOT_FRAME[_e] = {"Rooftop terrace of a building across the street": ("çatı", NATIVE, None, None),
                      "High-floor balcony across the street": ("balkon", NATIVE, None, None)}

# Volkan/çığ/deprem ön planı: (bugünkü metin, "boş" metni). Volkanda bugünkü metin perch'li ({perch} doldurulur).
NATIVE_FG = {"volcano": ("a {perch} railing corner in the foreground", "nothing in the foreground"),
             "volcano_long": ("a corner of the {perch} railing in the foreground", "nothing in the foreground"),
             "avalanche": ("the nearest buildings and a corner of the railing fill the lower half",
                           "the nearest buildings fill the lower half"),
             "earthquake": ("the street and a corner of the railing fill the lower part", "the street fills the lower part")}
NATIVE_FG_KEYS = ("korkuluk", "boş")


def family(event: str) -> str | None:
    if event in VOLCANO:
        return "volcano"
    if event in AVALANCHE:
        return "avalanche"
    if event in EARTHQUAKE:
        return "earthquake"
    if event == FIRE_TORNADO:
        return "fire_tornado"
    return None


def native(event: str, spot: str) -> tuple:
    return SPOT_FRAME[event][spot]


def fg_options(event: str, ftype: str, pos_spot: str | None, mode: str | None) -> tuple[str, ...]:
    """Ön plan anahtarları. Mod A'da yok (bugünkü cümle). Yerli (volkan/çığ/deprem) noktada korkuluk / boş."""
    if mode == "A":
        return ()
    if pos_spot and native(event, pos_spot)[1] == NATIVE:
        return NATIVE_FG_KEYS
    return FRAME_FG[ftype]


def family_window(event: str, volc_env: str | None = None) -> str:
    """Volkan/çığ/deprem pencere kadrajı: ailenin kanıtlanmış şablonu, yer pencere (175 kelime için kısa)."""
    from core.skeleton_pipeline import VOLC_ENVS, VOLCANO_SHORT_CAMERA_EXCLUDED
    tail = "one continuous shot, no zoom, no cuts."
    if event in VOLCANO:
        street = VOLC_ENVS[volc_env]["text"] if volc_env else "the village street"
        if event in VOLCANO_SHORT_CAMERA_EXCLUDED:
            return (f"Handheld footage filmed through an open upper-floor window, high vantage looking down over "
                    f"{street} toward the erupting volcano; slight hand shake, the camera stays fixed at the window, "
                    f"tilting down no more than slightly and never descending, the erupting volcano always visible in the "
                    f"upper third of the frame, the edge of the open window frame at one side; {tail}")
        return (f"Handheld footage filmed through an open upper-floor window, high vantage over {street} toward the "
                f"erupting volcano; slight hand shake, the camera stays fixed at the window, tilting down only "
                f"slightly, never descending, the erupting volcano always visible in the upper third of the frame, the "
                f"open window frame edge at one side; {tail}")
    if event in AVALANCHE:
        return ("Handheld footage through an open chalet window, high vantage looking up a steep snowy slope where the "
                "avalanche is descending into the buildings just below it; the slope and the avalanche fill the upper "
                "half of the frame, the nearest buildings and the open window frame fill the lower half; slight hand "
                "shake, the camera stays fixed, tilting slightly and never descending; " + tail)
    return ("Handheld footage through an open upper-floor window, high vantage looking across the street at the buildings "
            "collapsing opposite; the collapsing buildings and the dust fill the upper two thirds of the frame, the "
            "street and the open window frame fill the lower part; strong hand shake from the ground tremor, the camera "
            "stays fixed and never descends; " + tail)


def frame_camera(event: str, spot: str, frame: dict, volc_env: str | None = None, fire_env: str | None = None,
                 legacy=None) -> str:
    """Kadraja göre kamera cümlesi. legacy(event, spot, volc_env) -> bugünkü cümle (skeleton_pipeline verir)."""
    ftype, pos_spot, fg, mode = frame["type"], frame.get("pos_spot"), frame.get("fg"), frame.get("mode")
    fam = family(event)
    if pos_spot and (mode == "A" or native(event, pos_spot)[1] == NATIVE):
        cam = legacy(event, pos_spot, volc_env)
        if native(event, pos_spot)[1] == NATIVE and fg == "boş":
            from core.skeleton_pipeline import VOLCANO_SHORT_CAMERA_EXCLUDED
            key = (("volcano_long" if event in VOLCANO_SHORT_CAMERA_EXCLUDED else "volcano") if fam == "volcano"
                   else fam)
            old, new = NATIVE_FG[key]
            old = old.format(perch=native(event, pos_spot)[3])
            assert cam.count(old) == 1, (event, pos_spot, old)
            cam = cam.replace(old, new)
        return cam
    if ftype == "pencere" and fam in ("volcano", "avalanche", "earthquake"):
        return family_window(event, volc_env)
    data = FRAME_EVENTS[event]
    scene = FIRE_SCENE[fire_env] if fam == "fire_tornado" else data["scene"]
    if pos_spot:
        _, _, pos, perch = native(event, pos_spot)
    else:
        pos, perch = data.get("lib", {}).get(ftype, LIB_POS[ftype])
        pos = pos.format(scene=scene or "")
    fg_text = FG_TEXT[fg] if fg else None
    if fam == "fire_tornado":
        return fire_tornado_b(pos, perch, fg_text)
    return generic_camera(ftype, pos, perch, scene, data["threat"], fg_text)


# ── Seçim ────────────────────────────────────────────────────────────────────────────────────────────────────────
def side_rng() -> random.Random:
    """Ana rastgele akışı TÜKETMEYEN ikinci akış (durumun özetinden tohum): mevcut seçimler tohum başına aynı kalır."""
    digest = hashlib.sha256(repr(random.getstate()).encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def frame_depth(n_types: int) -> int:
    """Kadraj LRU derinliği: son 2 hariç; 3 ya da daha az seçenekte son 1; tek seçenekte yok."""
    return 0 if n_types <= 1 else (1 if n_types <= 3 else 2)


def _lru(options: list, used: list, depth: int) -> tuple[list, list]:
    recent = [u for u in used if u not in (None, "", "-")][-depth:] if depth else []
    cands = [o for o in options if o not in set(recent)]
    if not cands:
        return list(options), []
    return cands, [o for o in options if o in set(recent)]


def _weighted(options: list[str], rng) -> str:
    return rng.choices(options, weights=[FRAME_WEIGHTS[o] for o in options], k=1)[0]


def choose_frame(event: str, spot: str, pool: list[str], risky: set[str], hist: list[dict],
                 rng: random.Random) -> tuple[dict, dict]:
    """(frame, elenenler). pool: bu üretimde kamera yeri ödünç alınabilecek spotlar (görünüm/ortam süzülmüş). risky:
    seçilen beat'lerin dışlandığı spotlar (orada kamera olmaz; pencere balkon riskini de taşır)."""
    types = FRAME_EVENTS[event]["types"]
    fam = family(event)
    risky_types = {native(event, s)[0] for s in risky if s in SPOT_FRAME[event]}
    if "balkon" in risky_types:
        risky_types.add("pencere")
    available, pos_for = [], {}
    for t in types:
        if native(event, spot)[0] == t:
            available.append(t)
            pos_for[t] = [spot]
            continue
        natives = [s for s in pool if s in SPOT_FRAME[event] and native(event, s)[0] == t]
        usable = [s for s in natives if s not in risky]
        if natives:
            if usable:
                available.append(t)
                pos_for[t] = usable
        elif t not in risky_types and (fam not in ("volcano", "avalanche", "earthquake") or t == "pencere") \
                and t != "teras":
            available.append(t)
            pos_for[t] = [None]
    if not available:   # güvenlik: seçilen spotun kendi tipi her zaman vardır (izinli listede değilse bile)
        t = native(event, spot)[0]
        available, pos_for = [t], {t: [spot]}
    excluded = {}
    cands, excluded["kadraj"] = _lru(available, [h.get("kadraj") for h in hist], frame_depth(len(types)))
    ftype = _weighted(cands, rng)
    pos_spot = pos_for[ftype][0] if len(pos_for[ftype]) == 1 else rng.choice(pos_for[ftype])
    mode = None
    if pos_spot and native(event, pos_spot)[1] == AB:
        modes, excluded["kamera_modu"] = _lru(["A", "B"], [h.get("kamera_modu") for h in hist], 1)
        mode = rng.choice(modes)
    fgs = list(fg_options(event, ftype, pos_spot, mode))
    fg = None
    if fgs:
        fgs, excluded["on_plan"] = _lru(fgs, [h.get("on_plan") for h in hist], 1 if len(fgs) > 1 else 0)
        fg = rng.choice(fgs)
    return {"type": ftype, "pos_spot": pos_spot, "fg": fg, "mode": mode}, excluded


def frame_label(frame: dict | None) -> str:
    if not frame:
        return "-"
    mode = {"A": "A (mevcut)", "B": "B (sabit)"}.get(frame.get("mode"), "-")
    return (f"kadraj={frame['type']} · ön plan={frame.get('fg') or '-'} · kamera modu={mode}"
            + (f" · kamera noktası={frame['pos_spot']}" if frame.get("pos_spot") else " · kamera noktası=kütüphane"))


def all_frames(event: str, spot: str, pool: list[str], risky: set[str] | None = None) -> list[dict]:
    """Bu spotta olası tüm kadraj varyantları (testler, kural denetimi, K5 sığma koruması). risky verilirse seçilen
    beat'lerin dışlandığı spotlar ödünç alınmaz (choose_frame ile aynı süzgeç)."""
    risky = risky or set()
    risky_types = {native(event, s)[0] for s in risky if s in SPOT_FRAME[event]}
    if "balkon" in risky_types:
        risky_types.add("pencere")
    out = []
    for t in FRAME_EVENTS[event]["types"]:
        if native(event, spot)[0] == t:
            spots = [spot]
        else:
            natives = [s for s in pool if s in SPOT_FRAME[event] and native(event, s)[0] == t]
            if natives:
                natives = [s for s in natives if s not in risky]
                if not natives:
                    continue
            elif t in risky_types:
                continue
            if natives:
                spots = natives
            elif t == "teras" or (family(event) in ("volcano", "avalanche", "earthquake") and t != "pencere"):
                continue
            else:
                spots = [None]
        for ps in spots:
            modes = ["A", "B"] if ps and native(event, ps)[1] == AB else [None]
            for m in modes:
                fgs = fg_options(event, t, ps, m) or (None,)
                for fg in fgs:
                    out.append({"type": t, "pos_spot": ps, "fg": fg, "mode": m})
    return out
