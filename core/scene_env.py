"""
Ortam ekseni (9 olay) + ışık kapsamı (21 Eki 2026, Gece 1 / Aşama 5).

ORTAM: A = bugünkü görünüm (kelimesi kelimesine; Setting satırı yok). B-E Bahadır'ın metinleri; seçilince stil ekine
kamera cümlesinden sonra "Setting: ..." satırı girer ve GPT'nin PLACE satırı ortam metni olur (volkan ortamı gibi). Son
2 hariç LRU, Notion "Eksenler" JSON'unda "ortam". Ülke adı yok (testli).
UYUM: ENV_EXCLUDE (olay -> ortam -> uygun olmayan kamera noktaları: spot adı ya da "lib:<kadraj tipi>"). Seçilen spot
(sahne) ortamla çelişiyorsa o ortam seçilmez; kadraj o ortamda çelişen noktayı ödünç almaz. Her ortamda en az 2 kadraj
tipi kalır (testli).
IŞIK: her yapılandırılmış olayın ışık listesinde sabah, öğle (parlak gün), gün batımı/alacakaranlık, kapalı/fırtına
en az birer kez (LIGHT_ADD ekler, mevcut seçenekler silinmez). Yangında gün batımı ağırlığı 2. Volkanda "rain" yok.
Son 2 hariç LRU.
Seçimler ayrı rastgele akıştan (frame_axis.side_rng ile aynı yöntem, farklı tuz): ana akışın çekimleri (spot, beat, araç,
kişi, kod yedeği) değişmez.
"""
from __future__ import annotations

import hashlib
import random

MUDSLIDE = "Mudslide pours down a hillside street"
SLOPE = "Rain-soaked slope collapses onto a roadside"
VILLAGE = "Mud and debris torrent tears through a hillside village"
LANDFALL = "Tornado making landfall"
MARINA = "Tornado crosses a marina quay"
AVENUE = "Tornado sweeps down a coastal avenue"
WILDFIRE = "Wall of flames sweeps into a hillside neighborhood"
FACADE = "Flames race up a tower facade"
HELICOPTER = "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood"
FLOOD = "Flash flooding in city streets"
TIDAL = "Tidal wave surges over a coastal city street"
FIRE_TORNADO = "Fire tornado tears across a burning roadside"
PYROCLASTIC = "Pyroclastic cloud races down into a village street"
BOMBS = "Volcanic bombs slam into a village street"
AVALANCHE = ("Avalanche slams into a mountain village", "Avalanche crashes down onto a ski lodge",
             "Avalanche rips through a pine forest into a valley")
EARTHQUAKE = ("Earthquake collapses an apartment block", "Earthquake collapses a row of old stone houses")

ENV_A = "A"
# Bahadır'ın metinleri birebir (21 Eki, Aşama 5)
SCENE_ENVS = {
    # 21 Eki (genel kalite): 175 kelime için kısa (gerçek zaman / ön plan / çamur satırları eklendi). Önceki: "a steep
    # hillside town of pastel concrete houses with tin roofs, banana trees and tangled power lines", "...with terracotta
    # roofs and narrow stepped lanes"
    MUDSLIDE: {"B": "a steep town of pastel concrete houses with tin roofs and banana trees",
               "C": "a steep Mediterranean village of white-washed houses with terracotta roofs and stepped lanes",
               "D": "a hillside suburb of modern houses with garages, retaining walls and parked SUVs",
               "E": "a mountain town of wooden chalets with balconies among tall pine trees"},
    # 21 Eki (genel kalite): kısa. Önceki: "a mountain road through a small roadside village of shops and houses, with a
    # bus stop and parked motorbikes", "...above the sea, with guardrails and parked cars", "...beside a petrol station
    # and a row of houses"
    SLOPE: {"B": "a mountain road through a small village with a bus stop and parked motorbikes",
            "C": "a coastal cliff road lined with white houses above the sea, with parked cars",
            "D": "a highway cut through a forested hillside beside a petrol station and houses",
            "E": "a winding road through terraced tea fields with farmhouses on the slopes"},
    VILLAGE: {"B": "a terraced rice-field village of stilt houses among palm trees",
              "C": "a highland village of adobe houses with red tile roofs around a small church",
              "D": "a hill village of stone farmhouses and barns around a narrow square",
              "E": "a mountain village of grey-tiled houses, concrete steps and small vegetable gardens"},
    LANDFALL: {"B": "a palm-lined seafront boulevard of pastel hotels and beach bars",
               "C": "a harbor town of colorful terraced houses along a stone quay with small sailboats",
               "D": "a beach suburb of wooden houses on stilts with porches and pickup trucks",
               "E": "a modern waterfront district of glass apartment towers and a wide promenade"},
    MARINA: {"B": "a luxury marina below white apartment blocks with palm trees and a waterfront restaurant terrace",
             "C": "a small stone-walled harbor marina with sailboats and old townhouses behind it",
             "D": "a resort marina of moored yachts, a boardwalk of shops and hotel balconies",
             "E": "a lake marina of wooden piers and motor boats below pine hills dotted with houses"},
    AVENUE: {"B": "a small-town main street of brick shopfronts, traffic lights and parked pickups",
             "C": "a wide suburban avenue of low strip malls and a petrol station",
             "D": "a Mediterranean town avenue of cream apartment blocks with balconies and plane trees",
             "E": "an edge-of-town road of warehouses, parked trucks and small worker houses"},
    WILDFIRE: {"B": "a hillside neighborhood of stucco houses with red tile roofs above dry brush slopes",
               "C": "a pine-forest edge of wooden cabins and log houses with gravel driveways",
               "D": "a Mediterranean village of stone houses among olive groves and cypress trees",
               "E": "a rural town of tin-roofed bungalows with verandas among eucalyptus trees"},
    FACADE: {"B": "a dense city block of ten-storey apartment towers with balconies and satellite dishes",
             "C": "a historic quarter of five-storey stone apartment buildings with wrought-iron balconies",
             "D": "a modern clad residential tower beside a busy avenue",
             "E": "a 1970s concrete housing estate with long balcony corridors and a playground"},
    HELICOPTER: {"B": "a canyon neighborhood of hillside villas with swimming pools and winding roads",
                 "C": "a lakeside town of houses below wooded hills",
                 "D": "a hillside town of white houses above a blue bay",
                 "E": "a valley village of farmhouses among vineyard rows on the slopes"},
}
ENV_LABELS = {ENV_A: "A (bugünkü)"}
# Ortam seçilince kamera cümlesindeki sahne genel (ayrıntı Setting'den): frame_axis FRAME_EVENTS scene yerine
GENERIC_SCENE = {AVENUE: "the avenue", HELICOPTER: "the houses below", WILDFIRE: "the burning slope",
                 MUDSLIDE: "the steep street", SLOPE: "the road", VILLAGE: "the village", LANDFALL: "the waterfront",
                 MARINA: "the marina", FACADE: "the burning building"}   # 31 Eki (3): önceki "the burning tower"

# Spot × ortam uyumu: ortamda çelişen kamera noktaları (spot adı = sahne ve kamera yeri; "lib:<tip>" = kütüphane yeri)
ENV_EXCLUDE = {
    SLOPE: {"C": {"Far edge of the road across from the slope"}},          # deniz üstü uçurum yolu: karşı vadi yamacı yok
    VILLAGE: {"B": {"High steps on the village square"}},                  # çeltik terası, kazık evler: meydan yok
    LANDFALL: {"C": {"Beachfront promenade", "lib:balkon"},               # liman kasabası: sahil oteli / promenat yok
               "D": {"Beachfront promenade", "Downtown city center", "lib:balkon"}},   # plaj banliyösü: otel, merkez yok
    MARINA: {"C": {"lib:çatı"}, "E": {"lib:çatı"}},                        # küçük taş liman / göl: marina oteli yok
    AVENUE: {"B": {"High balcony over a high-rise avenue", "Upper-floor balcony over a residential avenue"},
             "C": {"High balcony over a high-rise avenue", "High balcony over a downtown avenue"},
             "D": {"High balcony over a high-rise avenue"},
             "E": {"High balcony over a high-rise avenue", "High balcony over a downtown avenue"}},
    FACADE: {"C": {"Balcony across from a coastal high-rise", "Rooftop terrace across from a coastal high-rise"}},
    # tarihi taş konut dokusu: kıyı yüksek binası yok (B, D, E kıyıda da olabilir)
}
# Kilit cümleyle çelişen ortamlar (açılış aşamasında çözülecek; bu aşamada seçilebilir, raporda)
KEY_VISUAL_CONFLICTS = {AVENUE: {"B", "C", "E"}, MARINA: {"E"}, FACADE: {"C"}}


def env_text(event: str, letter: str | None) -> str | None:
    if not letter or letter == ENV_A:
        return None
    return SCENE_ENVS[event][letter]


def env_options(event: str) -> list[str]:
    return [ENV_A] + list(SCENE_ENVS.get(event, {}))


def excluded_positions(event: str, letter: str | None) -> set[str]:
    return set(ENV_EXCLUDE.get(event, {}).get(letter or ENV_A, set()))


def compatible_envs(event: str, spot: str) -> list[str]:
    return [e for e in env_options(event) if spot not in excluded_positions(event, e)]


# ── Işık ─────────────────────────────────────────────────────────────────────────────────────────────────────────
# Eklenen ışık cümleleri (mevcutlar aynen). Kapsam anahtar kelimeleri LIGHT_CATEGORIES (testli).
_LANDSLIDE_ADD = ("grey dawn light after a night of rain", "bright midday light between heavy rain showers",
                  "dim dusk light with steady drizzle")
_TORNADO_ADD = ("eerie yellow early-morning storm light", "harsh bright midday sun under a towering storm cloud",
                "orange sunset light behind the storm")
_FIRE_ADD = ("hazy early-morning light through drifting smoke", "harsh bright midday sun through the smoke",
             "deep red sunset glow through the smoke", "dark smoke-filled overcast sky")
LIGHT_ADD = {
    FLOOD: ("grey early-morning light with steady rain", "bright midday light after a cloudburst",
            "orange sunset light under breaking storm clouds"),
    TIDAL: ("pale early-morning light over a grey sea", "bright midday sun over a churning sea",
            "low orange sunset light over the sea"),
    MUDSLIDE: _LANDSLIDE_ADD, SLOPE: _LANDSLIDE_ADD, VILLAGE: _LANDSLIDE_ADD,
    LANDFALL: _TORNADO_ADD, MARINA: _TORNADO_ADD, AVENUE: _TORNADO_ADD,
    WILDFIRE: _FIRE_ADD, FACADE: _FIRE_ADD, FIRE_TORNADO: _FIRE_ADD, HELICOPTER: _FIRE_ADD,
    # volkan (ağırlıklı listelere ağırlık 1 ile eklenir; "rain" yok)
    BOMBS: ("bright midday light under a towering ash plume",),
    PYROCLASTIC: ("pink-orange dawn light under a dark ash sky",),
}
# Çığ / deprem: ışık ortam ekseninin parçası (Setting satırı, ≤15 kelime)
ENV_LIGHT_ADD = {"avalanche": ("early-morning light on the peaks", "pink sunset glow on the peaks"),
                 "earthquake": ("bright midday sun", "golden sunset light")}
FIRE_EVENTS = (WILDFIRE, FACADE, FIRE_TORNADO, HELICOPTER)
LIGHT_CATEGORIES = {"sabah": ("morning", "dawn", "sunrise"),
                    "öğle": ("midday", "noon", "daylight", "sunny day", "bright cold"),
                    "gün batımı": ("sunset", "dusk", "twilight"),
                    "kapalı/fırtına": ("overcast", "storm", "rain", "cloud", "ash-grey", "smoke-filled", "snow",
                                       "downpour", "drizzle")}


def light_category(text: str) -> set[str]:
    low = text.lower()
    return {c for c, words in LIGHT_CATEGORIES.items() if any(w in low for w in words)}


def light_weight(event: str, text: str) -> int:
    return 2 if event in FIRE_EVENTS and "gün batımı" in light_category(text) else 1


def side_rng(salt: str) -> random.Random:
    """Ana akışı tüketmeyen ayrı akış (frame_axis.side_rng ile aynı yöntem, tuzlu: kadraj seçimi değişmez)."""
    digest = hashlib.sha256((salt + repr(random.getstate())).encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _lru(options: list, used: list, depth: int) -> tuple[list, list]:
    recent = [u for u in used if u not in (None, "", "-")][-depth:] if depth else []
    cands = [o for o in options if o not in set(recent)]
    return (list(options), []) if not cands else (cands, [o for o in options if o in set(recent)])


def depth(n: int) -> int:
    return 0 if n <= 1 else (1 if n <= 2 else 2)


def choose_env(event: str, spot: str, used: list, rng: random.Random) -> tuple[str, list]:
    """Ortam: seçilen spotla uyumlu ortamlardan, son 2 hariç (aday kalmazsa uyumlu hepsi). 31 Eki (3): rotasyonda
    sadece A + koruma ortamı (core.proven_axes)."""
    import core.proven_axes as pa
    options = pa.scene_envs(event, compatible_envs(event, spot))
    g = pa.guards(event, "ortam")   # 31 Eki (3): koruma ortamı en fazla %20, art arda gelmez
    guarded = pa.guard_lru(options, used, 2, g)
    if guarded:
        return pa.guard_pick(rng, guarded[0], g), guarded[1]
    cands, excluded = _lru(options, used, depth(len(options)))   # 31 Eki (3): derinlik rotasyondaki ortam sayısıyla
    return rng.choice(cands), excluded


def choose_light(event: str, options: list[str], used: list, rng: random.Random,
                 weights: dict[str, int] | None = None) -> tuple[str, list]:
    """Işık: son 2 hariç, ağırlıklı (yangında gün batımı 2; volkanda mevcut ağırlıklar + eklenenler 1). 31 Eki (3):
    koruma ışığı (volkan, meteor) en fazla %20, art arda gelmez (core.proven_axes)."""
    import core.proven_axes as pa
    g = pa.guards(event, "light")
    guarded = pa.guard_lru(options, used, depth(len(options)), g)
    if guarded:
        return pa.guard_pick(rng, guarded[0], g, {o: (weights or {}).get(o, light_weight(event, o))
                                                  for o in guarded[0]}), guarded[1]
    cands, excluded = _lru(options, used, depth(len(options)))
    w = [(weights or {}).get(o, light_weight(event, o)) for o in cands]
    return rng.choices(cands, weights=w, k=1)[0], excluded
