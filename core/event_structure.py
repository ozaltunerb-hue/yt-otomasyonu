"""
Yapılandırılmış olay hattı (3 Eki 2026, Bahadır): olayın kurgusu kodda, GPT sadece cümle yazar.

Hikâye üç zaman diliminden oluşur ("0-4s: ... 4-9s: ... 9-15s: ..."). Etiketleri ve 0-4s'nin kilit görselini kod
yazar; 4-9s ve 9-15s'de ne olacağını kod havuzdan seçer (Notion geçmişi + süreç hafızası, LRU, son üretimlerde
geçen olay tekrar gelmez). GPT strict JSON şemasıyla üç alanı döndürür: slice_1_rest (kilit görselin devamı),
slice_2, slice_3. Kie'ye gönderimden hemen önce final_prompt_issues son prompt'u spec'ten yeniden kurup birebir
karşılaştırır; tek madde tutmazsa istek gitmez (kapalı başarısızlık, sessiz yedek yok).

Kaynak: 3 Eki sel testleri. Zaman damgalı prompt'la Seedance 15 sn'nin tamamını aksiyonla doldurdu; serbest
GPT ise su duvarını zayıf yazdı, son saniyeleri genel cümleyle ("more cars") bitirdi. Yeni olay eklemek sadece
veri eklemektir (EVENT_KEY_VISUAL + EVENT_BEATS); import anı denetimi eksik veriyi yakalar.
"""
from __future__ import annotations

import random
import re
import threading

import config
from core.skeleton_pipeline import REGION_VIEWS, style_suffix, view_spots
from core.trace_format import count_constraints

FLOOD = "Flash flooding in city streets"

SLICE_LABELS = ("0-4s", "4-9s", "9-15s")
SLICE_FIELDS = ("slice_1_rest", "slice_2", "slice_3")
# Kelime aralıkları (etiketsiz). Toplam = kilit görsel + üç alan. 4 Eki, Bahadır: kuru provada 7 denemenin 3'ü
# sınır aşımıyla kaldı; 6-14/10-20/40-60'tan genişletildi. Genel 40-60 kuralı (creative_pipeline "length")
# yapılandırılmış olaylarda yerini bu toplama bırakır; diğer olaylarda aynen geçerli.
SLICE_WORDS = {"slice_1_rest": (6, 18), "slice_2": (10, 24), "slice_3": (10, 24)}
TOTAL_WORDS = (40, 70)
# Kie seedance-2-fast prompt sınırı 20000 karakter (docs.kie.ai/market/bytedance/seedance-2-fast, 4 Eki doğrulandı).
# Bizim sınırımız onun çok altında: en uzun stil eki 742 + 60 kelimelik hikâye (kelime başına 8 karakterle ~480)
# ≈ 1224; 1200 bu hikâyeyi haksız reddederdi. Tam kapsam testinde ölçülen en uzun prompt 1062. 70 kelimelik
# toplamla (4 Eki): ölçülen ortalama kelime uzunluğu 5,58 harf -> ~1221; 1400'e ulaşmak için ortalama 8,6 harf
# gerekir. Aşım dilim kalite kapısında GPT'ye "kısalt" geri bildirimi olur; son denetimde kapalı başarısızlık.
SEEDANCE_PROMPT_LIMIT = 20000
MAX_PROMPT_CHARS = 1400
RECENT_BEAT_BLOCK = 3          # son N üretimde geçen 4-9s / 9-15s olayı tekrar seçilmez

# ── Kilit görsel (0-4s'nin ilk cümlesi, kod yazar) ──────────────────────────────────────────────────────────
EVENT_KEY_VISUAL = {
    # 3 Eki, Bahadır onayı. Kaynak: zaman damgalı Seedance testi (fd6882cd) ve stil ekindeki kamera nesnesi.
    FLOOD: "A waist-high wall of brown muddy floodwater surges into the street.",
}

# ── Bölge araçları (4-9s'deki {vehicle}). Görünüm tariflerindeki araçlardan. terms: dilimde aranan ad. ──────
REGION_VEHICLES = {
    "gulf_metropolis": [("white SUV", ("suv",)), ("pickup truck", ("pickup", "truck")), ("sedan", ("sedan", "saloon"))],
    "north_african_coast": [("small hatchback", ("hatchback",)), ("small car", ("car",)),
                            ("delivery van", ("van",))],
    "us_coastal_town": [("pickup truck", ("pickup", "truck")), ("SUV", ("suv",)), ("sedan", ("sedan", "saloon"))],
    "north_european_seaside": [("small car", ("car",)), ("hatchback", ("hatchback",)), ("delivery van", ("van",))],
    "riviera": [("small car", ("car",)), ("hatchback", ("hatchback",)), ("delivery van", ("van",))],
    "east_asian_coast": [("small boxy car", ("car",)), ("compact car", ("car",)), ("small van", ("van",))],
}

# ── Olay havuzları. terms: her gruptan en az bir terim dilimde geçmeli (kök + eşanlamlı; çekimler otomatik:
# s/es/d/ed/ing/ies, ünsüz ikizleşmesi, e düşmesi). Düzensiz çekimler (spun, swept, tore...) ayrıca yazılır. ──
_DRAG = ("drag", "sweep", "swept", "carry", "carried", "shove", "push", "haul", "pull", "wash", "slide", "slid",
         "drift", "tow", "sweep away")
_SPIN = ("spin", "spun", "twirl", "whirl", "rotate", "swing", "swung", "pivot", "turn", "twist", "spiral")
_LIFT = ("lift", "hoist", "raise", "heave", "off its wheels", "off the ground", "off the road", "off the pavement",
         "airborne", "pick up", "picked up")
_POLE = ("lamppost", "lamp post", "streetlight", "street light", "street lamp", "streetlamp", "light pole",
         "lamp pole", "utility pole", "pole")
_HIT = ("into", "against", "crash", "slam", "smash", "collide", "ram", "hit", "strike", "struck", "plow", "plough",
        "bang", "jam", "pin", "wedge", "press", "hurl", "throw", "threw", "thrown")
_CAR = ("car", "cars", "vehicle", "sedan", "hatchback", "suv", "van", "truck", "pickup")

EVENT_BEATS = {
    FLOOD: {
        "slice_2": {
            "V1": {"text": "the {vehicle} is caught by the current, turns sideways and is dragged down the street",
                   "terms": [("sideways", "sideway", "broadside", "side-on", "side on") + _SPIN, _DRAG]},
            "V2": {"text": "the {vehicle} is swept into another parked car and both are shoved along",
                   "terms": [_HIT, ("another", "second", "other", "next", "parked") ]},
            "V3": {"text": "the {vehicle} is lifted off its wheels and spun around",
                   "terms": [_LIFT, _SPIN]},
            "V4": {"text": "the {vehicle} is pushed onto the sidewalk and slams into a lamppost",
                   "terms": [("sidewalk", "pavement", "curb", "kerb", "footpath"), _POLE]},
            "V5": {"text": "the {vehicle} tips over onto its side in the current",
                   "terms": [("tip", "topple", "overturn", "flip", "roll over", "rolls over", "rolled over", "capsize",
                              "keel over", "on its side", "onto its side", "on to its side", "on its roof")]},
            "V6": {"text": "the {vehicle} is carried backwards down the street, bumping parked cars",
                   "terms": [("backward", "backwards", "in reverse", "rear-first", "rear first", "tail-first",
                              "tail first", "rear end first", "boot first", "trunk first"), _DRAG]},
            "V7": {"text": "the {vehicle} is rammed against a building wall",
                   "terms": [("wall", "building", "facade", "façade", "house", "shopfront", "storefront"), _HIT]},
            "V8": {"text": "the {vehicle} and the car behind it are dragged away together, bumper to bumper",
                   "terms": [("together", "bumper", "side by side", "in tandem", "locked", "both", "pair"), _DRAG]},
        },
        "slice_3": {
            "D1": {"text": "a row of parked cars is ripped loose one by one and dragged away",
                   "terms": [("row", "line", "one by one", "one after another", "one after the other", "in turn",
                              "in sequence", "in succession"), _CAR,
                             ("rip", "tear", "tore", "torn", "wrench", "break loose", "breaks loose", "broke loose",
                              "pull", "drag", "sweep", "swept", "carry", "carried", "peel")]},
            "D2": {"text": "a lamppost topples into the current",
                   "terms": [_POLE, ("topple", "fall", "fell", "collapse", "crash", "snap", "tip", "keel over",
                                     "go down", "goes down", "went down", "bend", "buckle", "give way", "gives way")]},
            "D3": {"text": "a street tree is uprooted and carried along",
                   "terms": [("tree", "trees"), ("uproot", "rip", "tear", "tore", "torn", "topple", "fall", "fell",
                                                 "wrench", "pull", "snap", "carry", "carried", "sweep", "swept")]},
            "D4": {"text": "a dumpster tumbles down the street and smashes into a parked car",
                   "terms": [("dumpster", "skip", "trash bin", "rubbish bin", "garbage bin", "waste container",
                              "garbage container", "trash container", "container", "bin"),
                             ("tumble", "roll", "smash", "slam", "crash", "barrel", "bounce", "hurtle", "careen",
                              "ram")]},
            "D5": {"text": "a city bus is shoved sideways by the current",
                   "terms": [("bus", "buses"), ("shove", "push", "sideways", "sweep", "swept", "drag", "slide", "slid",
                                                "tilt", "lurch", "skid", "swing", "swung", "turn")]},
            "D6": {"text": "a low wall collapses into the water",
                   "terms": [("wall", "walls"), ("collapse", "crumble", "topple", "fall", "fell", "give way",
                                                 "gives way", "gave way", "burst", "break", "broke", "cave",
                                                 "tumble", "burst apart")]},
            "D7": {"text": "a wooden fence is torn away and carried off",
                   "terms": [("fence", "fences", "fencing", "picket"),
                             ("tear", "tore", "torn", "rip", "wrench", "sweep", "swept", "carry", "carried", "pull",
                              "snap", "break", "broke", "collapse", "flatten", "uproot")]},
            "D8": {"text": "a car is lifted off the road and spins away downstream",
                   "terms": [_CAR, _LIFT, _SPIN + ("drift", "float away", "downstream")]},
        },
        # Aynı videoda tekrar/çelişki (Bahadır onayı, 3 Eki)
        "excluded_pairs": {("V3", "D8"), ("V4", "D2"), ("V7", "D6"), ("V6", "D1"), ("V8", "D1")},
        # Bölge uyumu: tahta çit körfez metropolünde ve yüksek bina bölgesinde seçilmez
        "excluded_views": {"D7": {"gulf_metropolis"}},
        "excluded_spots": {"D7": {"High-rise city district"}},
    },
}


class StructureError(RuntimeError):
    """Yapılandırılmış hat verisi/çıktısı kullanılamaz; Kie'ye gidilmez (sessiz yedek yok)."""


class StructuredRejectError(StructureError):
    """Preflight ya da Kie içerik filtresi, bizim yazarın tek yeniden yazımından sonra da reddetti. Akış durur:
    run_pipeline yeni senaryo denemez (Bahadır onayı, 4 Eki: "bir kez yeniden çağır, ikinci retta dur ve bildir")."""


def structured_events() -> tuple[str, ...]:
    return tuple(EVENT_KEY_VISUAL)


def is_structured(event: str) -> bool:
    return event in EVENT_KEY_VISUAL


# ── Terim eşleşmesi (creative_pipeline ile aynı çekim kuralı) ───────────────────────────────────────────────
def find_terms(terms, text: str) -> list[str]:
    from core.creative_pipeline import find_terms as _find
    return _find(terms, text)


def missing_term_groups(groups, text: str) -> list[tuple[str, ...]]:
    return [g for g in groups if not find_terms(g, text)]


# ── Seçim ───────────────────────────────────────────────────────────────────────────────────────────────────
_BEAT_MEMORY: dict[str, list[str]] = {}
_BEAT_MEMORY_LIMIT = 12
_BEAT_LOCK = threading.Lock()


def beat_tag(b2: str, b3: str) -> str:
    return f"{b2}+{b3}"


def beats_of_combo(combo_key: str) -> str | None:
    """combo_key yer parçasındaki olay çifti ("spot#görünüm#V3+D5"), yoksa None."""
    parts = (combo_key or "").split("|")
    if len(parts) != 5:
        return None
    place = parts[3].split("#")
    if len(place) < 3 or not re.fullmatch(r"[A-Z]\d+\+[A-Z]\d+", place[2].strip().upper()):
        return None
    return place[2].strip().upper()


def remember_beats(event: str, tag: str) -> None:
    with _BEAT_LOCK:
        _BEAT_MEMORY.setdefault(event, []).append(tag)
        del _BEAT_MEMORY[event][:-_BEAT_MEMORY_LIMIT]


def beat_history(event: str, history: list[str]) -> list[str]:
    """Olayın olay çifti geçmişi, eskiden yeniye: Notion combo_key'leri + süreç hafızası (hafıza daha yeni)."""
    same = [h for h in history if len(h.split("|")) == 5 and h.split("|")[2].strip().lower() == event.lower()]
    with _BEAT_LOCK:
        memory = list(_BEAT_MEMORY.get(event, []))
    notion = [t for t in (beats_of_combo(h) for h in same) if t and t not in memory]
    return notion + memory


def allowed_pairs(event: str, view: str | None, spot: str) -> list[tuple[str, str]]:
    b = EVENT_BEATS[event]
    def ok3(d):
        return view not in b["excluded_views"].get(d, set()) and spot not in b["excluded_spots"].get(d, set())
    return [(v, d) for v in b["slice_2"] for d in b["slice_3"]
            if (v, d) not in b["excluded_pairs"] and ok3(d)]


def choose_beats(event: str, view: str | None, spot: str, history: list[str],
                 rng: random.Random | None = None) -> tuple[str, str]:
    """İzinli çiftler içinden: son RECENT_BEAT_BLOCK üretimde geçen 4-9s/9-15s olayları elenir, kalanlardan en uzun
    süredir kullanılmayan çift (eşitlikte rastgele). Aday kalmazsa StructureError (yedek yok)."""
    rng = rng or random
    seen = beat_history(event, history)
    recent = seen[-RECENT_BEAT_BLOCK:]
    blocked2 = {t.split("+")[0] for t in recent}
    blocked3 = {t.split("+")[1] for t in recent}
    pairs = [p for p in allowed_pairs(event, view, spot) if p[0] not in blocked2 and p[1] not in blocked3]
    if not pairs:
        raise StructureError(f"{event}: seçilebilir olay çifti kalmadı (görünüm={view}, yer={spot}, son={recent})")

    def last(p):
        return max((i for i, t in enumerate(seen) if t == beat_tag(*p)), default=-1)
    best = min(last(p) for p in pairs)
    return rng.choice([p for p in pairs if last(p) == best])


def choose_vehicle(view: str, rng: random.Random | None = None) -> str:
    if view not in REGION_VEHICLES:
        raise StructureError(f"Görünümün araç listesi yok: {view}")
    return (rng or random).choice([v for v, _ in REGION_VEHICLES[view]])


def vehicle_terms(view: str, vehicle: str) -> tuple[str, ...]:
    for v, terms in REGION_VEHICLES.get(view, []):
        if v == vehicle:
            return terms
    raise StructureError(f"Araç görünümde yok: {vehicle} / {view}")


def beat_text(event: str, slot: str, beat_id: str, vehicle: str | None = None) -> str:
    return EVENT_BEATS[event][slot][beat_id]["text"].format(vehicle=vehicle or "")


# ── GPT çıktısı: strict JSON şeması ──────────────────────────────────────────────────────────────────────────
SLICE_SCHEMA = {
    "name": "story_slices",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {f: {"type": "string"} for f in SLICE_FIELDS},
        "required": list(SLICE_FIELDS),
        "additionalProperties": False,
    },
}


def parse_slices(raw) -> dict[str, str]:
    """GPT yanıtı → {alan: metin}. Biçim hatası StructureError (geri bildirimle düzeltilmez, akış durur)."""
    if not isinstance(raw, dict):
        raise StructureError(f"GPT yanıtı nesne değil: {type(raw).__name__}")
    keys = set(raw)
    if keys != set(SLICE_FIELDS):
        raise StructureError(f"GPT yanıtı alanları hatalı: eksik={sorted(set(SLICE_FIELDS) - keys)}, "
                             f"fazla={sorted(keys - set(SLICE_FIELDS))}")
    out = {}
    for f in SLICE_FIELDS:
        v = raw[f]
        if not isinstance(v, str) or not v.strip():
            raise StructureError(f"GPT yanıtında '{f}' boş ya da metin değil")
        out[f] = clean_slice(v)
    return out


def clean_slice(text: str) -> str:
    """Boşlukları tekler, sondaki noktalama tek noktaya iner (birleştirmede '!.' gibi kırık metin olmasın)."""
    t = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"[.!?…]+$", "", t).rstrip() + "."


# ── Birleştirme ve spec ─────────────────────────────────────────────────────────────────────────────────────
def build_spec(event: str, ship: str | None, spot: str, view: str | None, b2: str, b3: str, vehicle: str) -> dict:
    """Kie'ye gidecek prompt'u kuran ve denetleyen her şey (slices hariç)."""
    if not is_structured(event):
        raise StructureError(f"Yapılandırılmış olay değil: {event}")
    return {"event": event, "ship": ship, "spot": spot, "view": view, "beat_2": b2, "beat_3": b3,
            "vehicle": vehicle, "key_visual": EVENT_KEY_VISUAL[event],
            "suffix": style_suffix(event, ship, spot, view)}


def assemble_story(spec: dict, slices: dict[str, str]) -> str:
    s1, s2, s3 = (slices[f] for f in SLICE_FIELDS)
    a, b, c = SLICE_LABELS
    return f"{a}: {spec['key_visual']} {s1} {b}: {s2} {c}: {s3}"


def plain_story(spec: dict, slices: dict[str, str]) -> str:
    """Etiketsiz düz metin (YouTube metadata, çeşitlilik ölçümü)."""
    return " ".join([spec["key_visual"]] + [slices[f] for f in SLICE_FIELDS])


def assemble_prompt(spec: dict, slices: dict[str, str]) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(assemble_story(spec, slices), spec["suffix"])


# ── Son denetim (Kie'den hemen önce) ─────────────────────────────────────────────────────────────────────────
_LABEL_LIKE = re.compile(r"\b\d{1,2}\s*[-–—]\s*\d{1,2}\s*(?:s|sec|secs|seconds?)\b", re.IGNORECASE)


def _issue(code: str, missing: str, feedback: str = "") -> dict:
    return {"rule": code, "missing": missing, "feedback": feedback}


def slice_issues(spec: dict, slices: dict[str, str]) -> list[dict]:
    """Dilim içeriği: kelime aralıkları, etiket benzeri ifade, satır sonu, seçilen olay ve araç terimleri.
    feedback GPT'ye gider (kalite kapısı); yapı hataları final_prompt_issues'ta."""
    event = spec["event"]
    out = []
    for f in SLICE_FIELDS:
        text = slices.get(f, "")
        lo, hi = SLICE_WORDS[f]
        n = len(text.split())
        if not lo <= n <= hi:
            out.append(_issue("slice_words", f"{f}: {lo}-{hi} kelime ({n} kelime)",
                              f"'{f}' must be {lo} to {hi} words; it has {n}."))
        if _LABEL_LIKE.search(text) or any(l in text for l in SLICE_LABELS):
            out.append(_issue("slice_label", f"{f}: dilim içinde zaman etiketi",
                              f"Do not write time labels like '0-4s' in '{f}'; the code adds them."))
        if "\n" in text:
            out.append(_issue("slice_newline", f"{f}: satır sonu", f"Write '{f}' as one line."))
    prompt_len = len(assemble_prompt(spec, slices))
    if prompt_len > MAX_PROMPT_CHARS:
        out.append(_issue("prompt_chars", f"prompt {prompt_len} karakter (en fazla {MAX_PROMPT_CHARS})",
                          f"The full prompt is {prompt_len} characters; shorten the three fields so it is at most "
                          f"{MAX_PROMPT_CHARS}."))
    total = len(plain_story(spec, slices).split())
    if not TOTAL_WORDS[0] <= total <= TOTAL_WORDS[1]:
        out.append(_issue("total_words", f"toplam {TOTAL_WORDS[0]}-{TOTAL_WORDS[1]} kelime ({total})",
                          f"The three fields plus the fixed opening must total {TOTAL_WORDS[0]} to {TOTAL_WORDS[1]} "
                          f"words; now {total}."))
    beats = EVENT_BEATS[event]
    s2, s3 = slices.get("slice_2", ""), slices.get("slice_3", "")
    vterms = vehicle_terms(spec["view"], spec["vehicle"])
    if not find_terms(vterms, s2):
        out.append(_issue("beat_vehicle", f"4-9s: araç ({spec['vehicle']})",
                          f"'slice_2' must name the {spec['vehicle']}."))
    for slot, bid, text in (("slice_2", spec["beat_2"], s2), ("slice_3", spec["beat_3"], s3)):
        miss = missing_term_groups(beats[slot][bid]["terms"], text)
        if miss:
            label = "4-9s" if slot == "slice_2" else "9-15s"
            event_text = beat_text(event, slot, bid, spec["vehicle"])
            out.append(_issue("beat_terms", f"{label}: seçilen olay ({bid}) görünmüyor",
                              f"'{slot}' must clearly show this event: {event_text}."))
    return out


def final_prompt_issues(spec: dict, slices: dict[str, str], prompt: str, story: str | None = None) -> list[dict]:
    """Kie'ye gidecek son prompt'un tam denetimi. Boş liste = gönderilebilir. Her madde kapalı başarısızlık."""
    from core.creative_pipeline import STORY_RULES, story_rule_issues
    out = []
    expected_suffix = style_suffix(spec["event"], spec["ship"], spec["spot"], spec["view"])
    if spec.get("key_visual") != EVENT_KEY_VISUAL.get(spec["event"]):
        out.append(_issue("key_visual", "kilit görsel spec'te değişmiş"))
    if spec.get("suffix") != expected_suffix:
        out.append(_issue("suffix", "stil eki beklenenle aynı değil"))
    rebuilt_story = assemble_story({**spec, "key_visual": EVENT_KEY_VISUAL.get(spec["event"], "")}, slices)
    rebuilt = assemble_prompt({**spec, "key_visual": EVENT_KEY_VISUAL.get(spec["event"], ""),
                               "suffix": expected_suffix}, slices)
    if prompt != rebuilt:
        out.append(_issue("rebuild", "prompt koddan yeniden kurulan metinle birebir aynı değil"))
    if story is not None and story != rebuilt_story:
        out.append(_issue("rebuild_story", "hikâye koddan yeniden kurulan metinle birebir aynı değil"))
    head = f"{SLICE_LABELS[0]}: {EVENT_KEY_VISUAL.get(spec['event'], '')} "
    if not prompt.startswith(head):
        out.append(_issue("key_visual", "0-4s kilit görselle başlamıyor"))
    positions = [prompt.find(f"{l}: ") for l in SLICE_LABELS]
    if any(prompt.count(f"{l}:") != 1 for l in SLICE_LABELS) or positions != sorted(positions) or -1 in positions:
        out.append(_issue("labels", "zaman etiketleri eksik, fazla ya da sırası yanlış"))
    out += slice_issues(spec, slices)
    n_constraints = count_constraints(expected_suffix)[0]
    if n_constraints > 8:
        out.append(_issue("suffix_constraints", f"stil eki {n_constraints} kısıt (en fazla 8)"))
    if len(prompt) > MAX_PROMPT_CHARS and not any(i["rule"] == "prompt_chars" for i in out):
        out.append(_issue("prompt_chars", f"prompt {len(prompt)} karakter (en fazla {MAX_PROMPT_CHARS})"))
    # 6 sabit kural (genel 40-60 "length" yerine TOTAL_WORDS; olay grupları ve çeşitlilik burada değil)
    fixed = set(STORY_RULES)
    for i in story_rule_issues(spec["event"], spec["ship"], plain_story(spec, slices), expected_suffix):
        if i["rule"] in fixed:
            out.append(i)
    return out


# ── Import anı tutarlılık denetimi: eksik/yanlış veri üretimde değil, açılışta patlasın ──────────────────────
def _validate_data() -> None:
    end = int(SLICE_LABELS[-1].split("-")[1].rstrip("s"))
    if end != config.VIDEO_DURATION_SECONDS:
        raise StructureError(f"Son zaman etiketi {SLICE_LABELS[-1]} video süresiyle ({config.VIDEO_DURATION_SECONDS} sn) "
                             f"uyuşmuyor")
    if set(REGION_VEHICLES) != set(REGION_VIEWS):
        raise StructureError(f"Araç listesi görünümlerle uyuşmuyor: {set(REGION_VEHICLES) ^ set(REGION_VIEWS)}")
    for view, vehicles in REGION_VEHICLES.items():
        if not vehicles or any(not t for _, t in vehicles):
            raise StructureError(f"Görünümde araç/terim yok: {view}")
    for event, key in EVENT_KEY_VISUAL.items():
        if event not in EVENT_BEATS or not key.endswith(".") or "\n" in key:
            raise StructureError(f"Kilit görsel/olay havuzu eksik: {event}")
        b = EVENT_BEATS[event]
        ids = list(b["slice_2"]) + list(b["slice_3"])
        if len(ids) != len(set(ids)) or not b["slice_2"] or not b["slice_3"]:
            raise StructureError(f"Olay havuzu boş ya da id tekrarı: {event}")
        for slot in ("slice_2", "slice_3"):
            for bid, beat in b[slot].items():
                if not beat.get("text") or not beat.get("terms") or any(not g for g in beat["terms"]):
                    raise StructureError(f"Olay verisi eksik: {event}/{bid}")
        for v, d in b["excluded_pairs"]:
            if v not in b["slice_2"] or d not in b["slice_3"]:
                raise StructureError(f"Yasak eşleşme bilinmeyen id: {v}-{d}")
        for d in list(b["excluded_views"]) + list(b["excluded_spots"]):
            if d not in b["slice_3"]:
                raise StructureError(f"Bölge kısıtı bilinmeyen id: {d}")
        for view in REGION_VIEWS:
            for spot in view_spots(event, view):
                if not allowed_pairs(event, view, spot):
                    raise StructureError(f"İzinli olay çifti yok: {event} / {view} / {spot}")


_validate_data()
