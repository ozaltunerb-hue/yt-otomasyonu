"""
Açılış ekseni (21 Eki 2026, Gece 1 / Aşama 6): kilit cümle varyantları (0-4 sn ilk cümle).

- Ateş hortumu hariç 18 yapılandırılmış olayda A = bugünkü kilit cümle (event_structure.EVENT_KEY_VISUAL, kelimesi
  kelimesine), B/C/D Bahadır'ın cümleleri (OPENINGS; düzeltilenler yorumda). Seçilen açılış GPT'ye kilit cümle, kod
  yedeğinde 0-4 sn cümlesi olarak gider (A ile aynı yol: spec["key_visual"]).
- Son 2 hariç LRU (Notion "Eksenler" -> "acilis"), ayrı rastgele akış (ana akış değişmez).
- Ortam uyumu: A_ENV_CONFLICTS (bugünkü kilit cümle ortama özgü ifade taşıyor: "palm-lined coastal avenue", "from the
  sea", "glass facade"...) ve OPENING_ENV_EXCLUDE (B/C/D'nin çeliştiği ortamlar). Çelişen kombinasyon seçilmez.
- Beat çakışması: açılış bir beat'le aynı hedefi aynı fiille anlatıyorsa o açılışla o beat aynı üretimde seçilmez
  (BEAT_CONFLICTS; aday liste candidate_beat_conflicts, elle süzüldü; testli ve raporlu).
"""
from __future__ import annotations

import functools
import random

A = "A"
OPENINGS = {
    "Flash flooding in city streets": {
        # K5 (175): Bahadır'ın metninden kısaldı (24 -> 17 kelime), bkz. ORIGINAL
        "B": "A wall of brown floodwater swings around the corner of an intersection and tips parked cars onto "
             "their sides.",
        "C": "A surge of brown floodwater pours down the sloping street and drags a parked car along with it.",
        "D": "Floodwater bursts over the low wall of a canal and spills straight into the street, sweeping parked "
             "cars sideways."},
    "Tidal wave surges over a coastal city street": {
        "B": "A towering wave rolls over the harbor breakwater and slams onto the coastal road, shoving parked "
             "cars in the first second.",
        "C": "A foaming wall of seawater surges over the promenade and crashes into the street, sweeping benches "
             "and scooters ahead of it.",
        "D": "A giant wave explodes against the harbor wall and a white wall of water collapses onto the street "
             "in front of the seafront houses."},
    "Mudslide pours down a hillside street": {
        # 21 Eki (genel kalite): çamur dokusu ("mud" geçen ilk ifade). Önceki: "A torrent of mud and rocks pours
        # around...", "...bursts apart and mud and boulders pour straight into the steep street.", "Mud pours down the
        # steep street in waves..."
        # 23 Eki, Bahadır (heyelan testi): "flips the first parked car over" -> "tips ... over" ("onto its side" 2
        # kelime uzun: H1+M6, H4+M7, H4+M9 ile kod yedeği 175'e sığmadı, Bahadır kararı)
        "B": "A torrent of thick brown mud full of rocks, branches and debris pours around the bend at the top of the "
             "street and tips the first parked car over.",
        "C": "A retaining wall on the slope bursts apart and thick brown mud full of rocks, branches and debris pours "
             "straight into the steep street.",
        "D": "Thick brown mud full of rocks, branches and debris pours down the steep street in waves, dragging flower "
             "pots and parked motorbikes with it."},
    "Rain-soaked slope collapses onto a roadside": {
        # 21 Eki (genel kalite): çamur dokusu. Önceki: "A mass of rock and mud breaks off the slope...", "Mud and tree
        # trunks slide off the slope over the roadside guardrail and pile up against a stopped bus."
        "B": "A mass of thick brown mud full of rocks, branches and debris breaks off the slope and buries the road, "
             "cutting off a pickup truck.",
        "C": "A huge boulder crashes onto the road and tumbles across it, and the whole slope slides down right "
             "behind it.",
        "D": "Thick brown mud full of rocks, branches and debris slides off the slope over the roadside guardrail "
             "and piles up against a stopped bus."},
    "Mud and debris torrent tears through a hillside village": {
        # 21 Eki (genel kalite): çamur dokusu. Önceki: "...turn to mud and slide into the top row of houses."
        "B": "The terraced hillside fields above the village turn to thick brown mud full of rocks, branches and "
             "debris and slide into the top row of houses.",
        "C": "A debris torrent bursts from the stream bed, floods the village lane and shoves a house off its "
             "foundations.",
        "D": "Half of the hillside behind the village breaks away with its trees and slides down to the roofs of "
             "the houses."},
    "Tornado making landfall": {
        "B": "The tornado roars ashore and hurls chairs, umbrellas and debris from the waterfront into the air.",
        "C": "The tornado makes landfall, crosses the seafront road and flips a parked car onto its side.",
        "D": "The tornado makes landfall and tears the solar panels off the roof of the first house, sending them "
             "spinning through the air."},
    "Tornado crosses a marina quay": {
        "B": "The tornado reaches the marina and slams the moored yachts into one another.",
        "C": "The tornado drags a pickup truck along the quay.",
        "D": "The tornado crosses the marina, ripping planks off the wooden pier and tipping the sailboats onto "
             "their sides."},
    "Tornado sweeps down a coastal avenue": {
        "B": "The tornado enters the far end of the avenue and lifts a parked minibus into the air.",
        "C": "The tornado tears the metal canopy off a row of shops and hurls it across the avenue.",
        "D": "The tornado sweeps down to the intersection and flings the cars there into one another."},
    "Wall of flames sweeps into a hillside neighborhood": {
        "B": "The wall of flames crests the ridge and slams into the first garden fences and trees of the "
             "neighborhood.",
        "C": "Wind-blown embers land on the first house of the neighborhood and its roof bursts into flames.",
        "D": "The flames jump across the road into the neighborhood and a parked car and the roadside bushes "
             "ignite at the same moment."},
    "Flames race up a tower facade": {
        "B": "Flames from a lower-floor balcony race up the facade and engulf the balconies above.",
        "C": "A fireball bursts out of an apartment window and the facade around it bursts into flames.",
        "D": "The top floor of the tower bursts into flames and burning debris falls onto the street below."},
    "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood": {
        # 31 Eki (3), Bahadır (su tarifi): önceki B "...sweeps in low and dumps its water straight onto the wall of
        # flames behind the houses.", C "...comes in over the ridge and its water drop crashes down in a white curtain
        # onto the flames."
        "B": "A firefighting helicopter sweeps in low and its bucket releases its whole load at once in a wide "
             "falling sheet onto the flames behind the houses.",
        "C": "A firefighting helicopter comes in over the ridge and its bucket releases its whole load at once in "
             "a wide falling sheet onto the flames.",
        "D": "The flames reach the back gardens as a firefighting helicopter passes just above the rooftops with "
             "its water bucket."},
    "Pyroclastic cloud races down into a village street": {
        # 31 Eki (2), Bahadır: ortam nötr. Önceki "...swallows the highest houses of the village in the first second."
        "B": "The ash cloud races down the volcano's slope and swallows the highest houses on the slope in the "
             "first second.",
        "C": "A blast of hot air ahead of the cloud bends the trees, and the grey wall of ash surges into the "
             "street right behind it.",
        "D": "The ash cloud spreads across the valley and engulfs the houses on both sides of the street at once."},
    "Volcanic bombs slam into a village street": {
        "B": "A single huge glowing rock from the volcano punches straight through the roof of the house across "
             "the street.",
        "C": "Glowing rocks slam into the street one after another, throwing sparks and smoke off the asphalt.",
        "D": "A volcanic bomb smashes into a large parked truck and the truck bursts into flames."},
    "Avalanche slams into a mountain village": {
        "B": "The avalanche breaks loose and slams into the highest barn of the village in the first second.",
        "C": "An avalanche cloud of powder snow rushes between the village houses, and the mass of snow rides up "
             "onto the roofs right behind it.",
        "D": "The avalanche pours down the stream bed and buries the village bridge and road."},
    "Avalanche crashes down onto a ski lodge": {
        "B": "The avalanche breaks off the top of the piste and roars down beneath the chairlift line into the "
             "resort.",
        "C": "The avalanche comes down behind the hotel and slams straight into the ski rental building.",
        "D": "The avalanche crashes down and buries the parking area of the resort."},
    "Avalanche rips through a pine forest into a valley": {
        "B": "The avalanche bursts out of the forest snapping trees and reaches the fence of the first house.",
        "C": "Avalanche snow and broken tree trunks pour over the valley road and bury it.",
        "D": "The avalanche slams into the back wall of a mountain house at the forest edge."},
    "Earthquake collapses an apartment block": {
        "B": "The residential apartment block topples forward from its front facade into the street.",
        "C": "The lower floors of the apartment block collapse and the upper floors drop straight down, filling "
             "the street with dust.",
        "D": "One of two neighboring residential blocks collapses sideways onto the other."},
    "Earthquake collapses a row of old stone houses": {
        "B": "The facade of an old stone house breaks away and crashes into the street.",
        "C": "The balconies of the stone houses tear off one after another, and the walls behind them collapse.",
        "D": "The house above an arched passage collapses and the rubble blocks the street."},
}
# Bahadır'ın metninden değişen açılışlar (olay, harf) -> özgün metin. Nedenler: a kuralı (ilk cümlede tetik), e kuralı
# (hikâyede olay adından en az 2 kök; kilit cümle tek başına sağlar, A gibi), çığda araç kelimesi yasak ("car").
ORIGINAL = {
    ("Flash flooding in city streets", "B"):   # K5: 175 kelime (Doğu Asya görünümü + uzun Setting satırı)
        "A wall of brown floodwater swings around the corner of an intersection and tips parked cars onto their sides "
        "as it spreads down the street.",
    ("Avalanche crashes down onto a ski lodge", "D"):
        "The mass of snow buries the cars in the resort car park.",
    ("Mudslide pours down a hillside street", "B"):
        "A torrent of mud and rocks rounds the bend at the top of the steep street and flips the first parked car "
        "onto its side.",
    ("Mudslide pours down a hillside street", "D"):
        "Mud surges down the steep street in waves, dragging flower pots and parked motorbikes with it.",
    ("Wall of flames sweeps into a hillside neighborhood", "D"):
        "The fire jumps across the road and a parked car and the roadside bushes ignite at the same moment.",
    ("Avalanche slams into a mountain village", "C"):
        "A cloud of powder snow rushes between the houses, and the mass of snow rides up onto the roofs right "
        "behind it.",
    ("Earthquake collapses an apartment block", "C"):
        "The lower floors give way and the upper floors drop straight down, filling the street with dust.",
    ("Rain-soaked slope collapses onto a roadside", "D"):
        "Mud and tree trunks spill over the roadside guardrail and pile up against a stopped bus.",
    ("Mud and debris torrent tears through a hillside village", "B"):
        "The terraced fields above the village turn to mud and slide into the top row of houses.",
    ("Tornado making landfall", "C"):
        "The tornado crosses the seafront road and flips a parked car onto its side.",
    ("Tornado making landfall", "D"):
        "The tornado tears the solar panels off the roof of the first house, sending them spinning through the "
        "air.",
    ("Tornado crosses a marina quay", "D"):
        "The tornado rips planks off the wooden pier and tips the sailboats onto their sides.",
    ("Tornado sweeps down a coastal avenue", "D"):
        "The tornado reaches the intersection and flings the cars there into one another.",
    ("Wall of flames sweeps into a hillside neighborhood", "C"):
        "Wind-blown embers land on the first house and its roof bursts into flames.",
    ("Flames race up a tower facade", "C"):
        "A fireball bursts out of an apartment window and the facade around it catches fire.",
    ("Flames race up a tower facade", "D"):
        "The top floor bursts into flames and burning debris falls onto the street below.",
    ("Avalanche rips through a pine forest into a valley", "C"):
        "Snow and broken tree trunks pour over the valley road and bury it.",
    ("Earthquake collapses an apartment block", "B"):
        "The residential block topples forward from its front facade into the street.",
    ("Earthquake collapses a row of old stone houses", "B"):
        "The facade of an old house breaks away and crashes into the street.",
}

# Bugünkü kilit cümle (A) ortama özgü ifade taşıyor: bu ortamlarda A seçilmez (Aşama 5 KEY_VISUAL_CONFLICTS + ek)
A_ENV_CONFLICTS = {
    "Tornado sweeps down a coastal avenue": {"B", "C", "D", "E"},   # "palm-lined coastal avenue" (D: plane trees)
    "Tornado crosses a marina quay": {"E"},                         # "tears in from the sea" (E: göl marinası)
    "Flames race up a tower facade": {"C", "E"},                    # "glass facade of a tower" (C tarihi, E 1970 beton)
    "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood": {"C", "E"},
    # "swoops over a hillside neighborhood" (C göl kıyısı kasabası, E bağ vadisi köyü)
}
# B/C/D'nin çeliştiği ortamlar (olay -> harf -> ortamlar)
OPENING_ENV_EXCLUDE = {
    "Tornado making landfall": {"D": {"B", "E"}},       # "roof of the first house": B otel bulvarı, E cam kuleler
    "Tornado crosses a marina quay": {"B": {"E"},       # "moored yachts": E göl marinası (motorlu tekne)
                                      "D": {"C"}},      # "wooden pier": C taş duvarlı liman
    "Tornado sweeps down a coastal avenue": {"C": {"E"}},   # "a row of shops": E depolar ve işçi evleri
    # 31 Eki (3), spot-ortam tutarlılığı: "the top floor of the tower" C tarihi taş binalar, E 1970 sitesi (kule yok)
    "Flames race up a tower facade": {"D": {"C", "E"}},
}


def options(event: str) -> list[str]:
    return [A] + list(OPENINGS.get(event, {}))


def text(event: str, letter: str | None) -> str | None:
    """Açılış metni; A ya da None -> None (çağıran bugünkü kilit cümleyi kullanır)."""
    if not letter or letter == A:
        return None
    return OPENINGS[event][letter]


def env_compatible(event: str, letter: str, env: str | None) -> bool:
    env = env or A
    if letter == A:
        return env not in A_ENV_CONFLICTS.get(event, set())
    return env not in OPENING_ENV_EXCLUDE.get(event, {}).get(letter, set())


# Açılış × beat çakışması (aynı hedef + aynı fiil): aynı üretimde seçilmez. Aday liste candidate_beat_conflicts ile
# (terim gruplarının hepsi açılışta) çıkarıldı, elle süzüldü: sadece gerçekten aynı şeyi anlatanlar (rapor 21 Eki).
BEAT_CONFLICTS = {
    # 30 Eki (2), Bahadır: B+V6, D+T7 (bombalar), D+N5 (cephe), B+T4 (eski sokak)
    "Flash flooding in city streets": {"B": {"V5", "V6"}, "D": {"V1"}},    # araba yan yatar / yana süpürülür
    "Tidal wave surges over a coastal city street": {"B": {"T3"}},         # park hâlindeki arabalar itilir
    # 22 Eki (heyelan denetimi): M3 artık park arabaları sırası (B ilk park arabasını devirir); C+M3 (duvar) çıktı
    "Mudslide pours down a hillside street": {"B": {"H5", "M3"}},         # araba yan yatar / park arabaları
    # 22 Eki: S4 kaya kütlesi yamaçtan kopup yola düşer (B yamaçtan kopar, yolu gömer; C kaya yola düşer)
    "Rain-soaked slope collapses onto a roadside": {"B": {"S4"}, "C": {"S4"}, "D": {"S3"}},   # D: ağaç gövdesi yola kayar
    "Mud and debris torrent tears through a hillside village": {"C": {"L7"}},   # ev temelinden sökülür
    # 23 Eki (hortum denetimi): C+C2 araç yan yatar; D+E2 yeni E2 de çatı söker (E1 gibi)
    "Tornado making landfall": {"C": {"C2"}, "D": {"E1", "E2"}},           # araba yan yatar / çatı sökülür
    # 30 Eki, Bahadır: B+P6 araç havaya kalkar (B minibüsü havaya kaldırır)
    "Tornado sweeps down a coastal avenue": {"B": {"P6"}, "C": {"Q6"}},    # dükkân önü sökülür
    "Wall of flames sweeps into a hillside neighborhood": {"C": {"K8", "L1"}},   # evin çatısı tutuşur
    "Flames race up a tower facade": {"B": {"M8", "M11"}, "C": {"M10", "N5"}, "D": {"N5"}},  # cepheden yukarı / pencereden alev
    # 31 Eki (2), Bahadır: C+R9 kaldırıldı (gerekçesi yol idi; yeni R9 köşe dükkânı). Önceki "C": {"R9"}
    "Volcanic bombs slam into a village street": {"B": {"R7"}, "D": {"T9", "R2", "T7"}},
    "Avalanche slams into a mountain village": {"B": {"A4"}},              # ahıra çarpar
    "Avalanche crashes down onto a ski lodge": {"C": {"C1"}},              # kayak deposu / kiralama binası
    "Avalanche rips through a pine forest into a valley": {"D": {"F1"}},   # dağ evinin duvarına çarpar
    "Earthquake collapses an apartment block": {"B": {"P2"}, "C": {"P1", "Q5"}},   # ön cephe / üst katlar çöker
    "Earthquake collapses a row of old stone houses": {"B": {"R1", "T4"}},   # eski taş evin cephesi kopar
}


def beat_conflicts(event: str, letter: str) -> frozenset[str]:
    return frozenset(BEAT_CONFLICTS.get(event, {}).get(letter, set()))


@functools.lru_cache(maxsize=None)
def candidate_beat_conflicts(event: str, letter: str) -> frozenset[str]:
    """Aday: açılışın tüm terim gruplarını taşıdığı beat'ler (geniş; BEAT_CONFLICTS bunlardan elle seçildi)."""
    if letter == A:
        return frozenset()
    import core.event_structure as es
    sentence = OPENINGS[event][letter]
    out = set()
    for slot in ("slice_2", "slice_3"):
        for bid, beat in es.EVENT_BEATS[event][slot].items():
            terms = list(beat["terms"])
            if "{vehicle}" in beat["text"]:   # araçlı beat'te araç adı ayrıca aranır: açılıştaki araç kelimesi
                terms = terms + [es._CAR]
            if not es.missing_term_groups(terms, sentence):
                out.add(bid)
    return frozenset(out)


def allowed(event: str, env: str | None, b2: str, b3: str) -> list[str]:
    return [o for o in options(event) if env_compatible(event, o, env)
            and not ({b2, b3} & beat_conflicts(event, o))]


def choose(event: str, env: str | None, b2: str, b3: str, used: list, rng: random.Random) -> tuple[str | None, list]:
    """(harf, elenenler). Aday yoksa None (çağıran ortamı A'ya çeker; A ortamında A her zaman uyumlu). 31 Eki (3):
    rotasyonda sadece A + koruma harfi (core.proven_axes; diğerleri DENEME, kodda durur)."""
    import core.proven_axes as pa
    cands = pa.openings(event, allowed(event, env, b2, b3))
    if not cands:
        return None, []
    # 31 Eki (3): A + koruma harfi: koruma en fazla %20, art arda gelmez; A tekrar edebilir (pa.guard_lru)
    g = pa.guards(event, "acilis")
    guarded = pa.guard_lru(cands, used, 2, g)
    if guarded:
        return pa.guard_pick(rng, guarded[0], g), guarded[1]
    recent = [u for u in used if u not in (None, "", "-")][-(1 if len(cands) <= 2 else 2):]
    left = [o for o in cands if o not in set(recent)]
    if not left:
        left = cands
    return rng.choice(left), [o for o in cands if o in set(recent)]
