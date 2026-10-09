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
from core.skeleton_pipeline import (EVENT_SKELETONS, REGION_VIEW_EVENTS, REGION_VIEWS, count_range, style_suffix,
                                    view_spots)
from core.trace_format import count_constraints

FLOOD = "Flash flooding in city streets"
TIDAL = "Tidal wave surges over a coastal city street"
MUDSLIDE = "Mudslide pours down a hillside street"
SLOPE = "Rain-soaked slope collapses onto a roadside"
VILLAGE = "Mud and debris torrent tears through a hillside village"
LANDFALL = "Tornado making landfall"
MARINA_TORNADO = "Tornado crosses a marina quay"
AVENUE = "Tornado sweeps down a coastal avenue"
# 🔥 Yangın (TASLAK, 8 Eki, Bahadır)
WILDFIRE = "Wall of flames sweeps into a hillside neighborhood"
FACADE_FIRE = "Flames race up a tower facade"
FIRE_TORNADO = "Fire tornado tears across a burning roadside"
# 10 Eki, Bahadır (havuzlar onaylı): yangın söndürme helikopteri
HELICOPTER = "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood"
FIRE_EVENTS = (WILDFIRE, FACADE_FIRE, FIRE_TORNADO, HELICOPTER)
# ⛈️ Süper hücre fırtınası (TASLAK, 10 Eki, Bahadır). Yağmur/dolu serbest (NO_RAIN_EVENTS dışı), araç havalanır.
HAIL = "Giant hail pounds a street under a dark supercell"
DOWNBURST = "Downburst slams into a tree-lined street"
LIGHTNING = "Lightning bolt slams into a transformer on a utility pole"
STORM_HIGHWAY = "Violent gust slams into a highway"
STORM_EVENTS = (HAIL, DOWNBURST, LIGHTNING, STORM_HIGHWAY)

SLICE_LABELS = ("0-4s", "4-9s", "9-15s")
SLICE_FIELDS = ("slice_1_rest", "slice_2", "slice_3")
# Kelime aralıkları (etiketsiz). Toplam = kilit görsel + üç alan. 4 Eki, Bahadır: kuru provada 7 denemenin 3'ü
# sınır aşımıyla kaldı; 6-14/10-20/40-60'tan genişletildi. Genel 40-60 kuralı (creative_pipeline "length")
# yapılandırılmış olaylarda yerini bu toplama bırakır; diğer olaylarda aynen geçerli.
SLICE_WORDS = {"slice_1_rest": (6, 18), "slice_2": (10, 24), "slice_3": (10, 24)}
TOTAL_WORDS = (40, 70)
# Olaya özel toplam kelime aralığı (genel TOTAL_WORDS yerine). 4 Eki, Bahadır: hortum marina 40-75
TOTAL_WORDS_BY_EVENT = {"Tornado crosses a marina quay": (40, 75),
                        # 10 Eki, Bahadır: orman yangını 40-75 (kilit cümle 22 kelime; diğer yangınlar 40-70)
                        "Wall of flames sweeps into a hillside neighborhood": (40, 75),
                        # 10 Eki, Bahadır: helikopter 40-75 (kilit cümle 24 kelime)
                        "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood": (40, 75),
                        # 10 Eki, Bahadır: süper hücre fırtınasının 4 olayı 40-75 (kilit cümleler uzun)
                        "Giant hail pounds a street under a dark supercell": (40, 75),
                        "Downburst slams into a tree-lined street": (40, 75),
                        "Lightning bolt slams into a transformer on a utility pole": (40, 75),
                        "Violent gust slams into a highway": (40, 75)}
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
    # 4 Eki, Bahadır onayı. Kaynak: EVENT_OUTCOMES'taki kahverengi molozlu dalga (1 Eki, 6 görünüm videosu).
    TIDAL: "A towering brown tidal wave thick with debris crashes over the waterfront onto the coastal street.",
    # TASLAK (4 Eki, Bahadır hazırlığı, onay bekliyor): heyelan
    MUDSLIDE: "A massive wall of brown mud and rocks tears loose from the saturated hillside and pours down the steep "
              "street.",
    SLOPE: "The saturated slope collapses and a fast torrent of brown mud and rocks surges across the road.",
    VILLAGE: "A massive torrent of brown mud, logs and rocks bursts through the drenched hillside village.",
    # TASLAK (4 Eki, Bahadır hazırlığı, onay bekliyor): hortum
    LANDFALL: "A violent tornado makes landfall on the waterfront, tearing roofs and signs into the air.",
    # 4 Eki, Bahadır: marina test videosunda sorun çıktı. Eski: "A violent tornado crosses the marina, bending masts
    # and ripping covers off the yachts as it sweeps toward the quay road." Ara taslak (canlıya alınmadı; Z6/Y5 ile
    # aynı nesneler, 22 kelime): "A violent tornado slams into the marina, ripping covers off the yachts and hurling
    # deck chairs and dock boxes across the quay."
    # 4 Eki, Bahadır: marina yeniden tasarımı (yüksek teras, rıhtım ve kafe sahneleri). Önceki canlı metin:
    # "A violent tornado slams into the marina, ripping covers off the yachts and hurling debris across the quay."
    MARINA_TORNADO: "A violent tornado tears in from the sea onto the marina quay, ripping palms and umbrellas off the "
                    "ground.",
    AVENUE: "A violent tornado sweeps down a palm-lined coastal avenue, hurling signs, branches and debris along the "
            "road.",
    # TASLAK (8 Eki, Bahadır): yangın kilit cümleleri, Bahadır'ın metni birebir
    WILDFIRE: "A towering wall of flames sweeps down the forested slope and slams into the edge of the neighborhood, "
              "igniting roofs and trees.",
    FACADE_FIRE: "Flames race up the glass facade of a tower, blowing out windows and raining burning debris onto the "
                 "street.",
    FIRE_TORNADO: "A violent fire tornado tears across a burning roadside, hurling flames, burning branches and embers "
                  "across the road.",
    # 10 Eki, Bahadır onayı: helikopter kilit cümlesi birebir
    HELICOPTER: "A firefighting helicopter swoops over a hillside neighborhood and drops a huge load of water onto the "
                "wall of flames racing toward the houses.",
    # 10 Eki, Bahadır onayı: süper hücre fırtınası kilit cümleleri birebir
    HAIL: "Giant hail pounds a street under a dark supercell, shattering windshields and tearing through shop awnings.",
    DOWNBURST: "A violent downburst slams into a tree-lined street, bending trees flat and tearing signs and branches "
               "through the air.",
    LIGHTNING: "A lightning bolt slams into a transformer on a utility pole, exploding in a shower of sparks above the "
               "street.",
    STORM_HIGHWAY: "A violent gust slams into a highway, flipping a truck onto its side as cars brake hard around it.",
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
# ── Olay araçları: bölge görünümü olmayan olaylarda (TASLAK, 4 Eki, heyelan). Görünümlü olaylar REGION_VEHICLES. ─
EVENT_VEHICLES = {
    MUDSLIDE: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)),
               ("SUV", ("suv",))],
    SLOPE: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)),
            ("SUV", ("suv",))],
    VILLAGE: [("pickup truck", ("pickup", "truck")), ("small van", ("van",)), ("old hatchback", ("hatchback",))],
    # TASLAK (4 Eki, hortum)
    LANDFALL: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)),
               ("SUV", ("suv",))],
    MARINA_TORNADO: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)),
                     ("SUV", ("suv",))],
    AVENUE: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)),
             ("SUV", ("suv",))],
    # TASLAK (8 Eki, yangın). Orman ve cephe yangınında araç havalanmaz (NO_LIFT_SLICE); ateş hortumunda havalanır
    WILDFIRE: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)),
               ("SUV", ("suv",))],
    FACADE_FIRE: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)),
                  ("SUV", ("suv",))],
    FIRE_TORNADO: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)),
                   ("SUV", ("suv",))],
    # 10 Eki: helikopter (araç sadece F3/F6'da; havalanmaz, NO_LIFT_SLICE)
    HELICOPTER: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)),
                 ("SUV", ("suv",))],
    # 10 Eki: süper hücre fırtınası (araç havalanabilir)
    HAIL: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)), ("SUV", ("suv",))],
    DOWNBURST: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)), ("SUV", ("suv",))],
    LIGHTNING: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)), ("SUV", ("suv",))],
    STORM_HIGHWAY: [("pickup truck", ("pickup", "truck")), ("small car", ("car",)), ("white van", ("van",)), ("SUV", ("suv",))],
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
# Kıyı dev dalga (4 Eki). Sel girdileriyle aynı terimler burada adlandırıldı; sel girdileri olduğu gibi kalır.
_SIDEWAYS = ("sideways", "sideway", "broadside", "side-on", "side on")
_FLING = ("fling", "flung", "toss", "hurl", "throw", "threw", "thrown", "launch")
_SHOP = ("storefront", "store front", "shopfront", "shop front", "shop window", "shop", "store", "facade", "façade",
         "building")
_CURB = ("sidewalk", "pavement", "curb", "kerb", "footpath")
_TIP = ("tip", "topple", "overturn", "flip", "roll over", "rolls over", "rolled over", "capsize", "keel over",
        "on its side", "onto its side", "on to its side", "on its roof")
_BACKWARD = ("backward", "backwards", "in reverse", "rear-first", "rear first", "tail-first", "tail first",
             "rear end first", "boot first", "trunk first")
_TOGETHER = ("together", "bumper", "side by side", "in tandem", "locked", "both", "pair")
_ROW = ("row", "line", "one by one", "one after another", "one after the other", "in turn", "in sequence",
        "in succession",
        "sequence")   # 4 Eki, Bahadır: kuru provada "A sequence of parked vehicles" reddedildi
_RIP_AWAY = ("rip", "tear", "tore", "torn", "wrench", "break loose", "breaks loose", "broke loose", "pull", "drag",
             "sweep", "swept", "carry", "carried", "peel", "wash")
_FALL = ("topple", "fall", "fell", "collapse", "crash", "snap", "tip", "keel over", "go down", "goes down",
         "went down", "bend", "buckle", "give way", "gives way")
# Heyelan (TASLAK, 4 Eki). Kıyı dev dalga/sel girdilerindeki aynı terimler adlandırıldı; o girdiler olduğu gibi kalır.
_COLLAPSE = ("collapse", "crumble", "topple", "fall", "fell", "give way", "gives way", "gave way", "burst", "break",
             "broke", "cave", "tumble", "burst apart")
_UPROOT = ("uproot", "rip", "tear", "tore", "torn", "topple", "fall", "fell", "wrench", "pull", "snap", "carry",
           "carried", "sweep", "swept", "wash")
_FENCE = ("fence", "fences", "fencing", "picket")
_TEAR = ("tear", "tore", "torn", "rip", "wrench", "sweep", "swept", "carry", "carried", "pull", "snap", "break",
         "broke", "collapse", "flatten", "uproot")
_BURY = ("bury", "buried", "engulf", "swallow", "submerge", "sink", "sank", "sunk", "to its windows",
         "up to its windows", "window-deep", "door-deep")
_HOUSE = ("wall", "house", "home", "building", "facade", "façade", "cottage", "cabin", "doorway")
_GUARDRAIL = ("guardrail", "guard rail", "crash barrier", "barrier", "railing")
_ROCK = ("boulder", "rock", "stone")
_LOGS = ("log", "logs", "timber", "lumber", "woodpile", "wood pile", "tree trunk", "trunks")
_BUMP = ("bump", "knock", "clip", "scrape", "graze", "jostle", "hit", "slam", "crash", "ram", "smash", "collide")
_NEIGHBOR = ("beside", "next", "another", "other", "second", "parked", "adjacent", "neighboring", "neighbouring")
# Heyelan H6/R6 (4 Eki, Bahadır onayı): kuru provada GPT "the car behind it", "the trailing car" yazdı. Ortak
# _TOGETHER (sel, kıyı dev dalga) değişmez; çıplak "behind" bilerek yok.
_TOGETHER_LANDSLIDE = _TOGETHER + ("the car behind it", "trailing", "following")
# Hortum (TASLAK, 4 Eki). Mevcut listeler yeniden kullanılır; aşağıdakiler sadece hortum girdilerinde.
_BLOW = ("blow", "blew", "blown", "gust")
_WINDSHIELD = ("windshield", "windscreen", "front glass", "glass", "window")
_AIRBORNE = ("fly", "flew", "flying", "whirl", "swirl", "blow", "blew", "blown", "scatter", "spin", "spun")
_SIGN = ("sign", "signboard", "signpost", "billboard", "hoarding", "advertising board")
_SHELTER = ("bus shelter", "bus stop", "shelter")
_BOAT = ("yacht", "boat", "sailboat", "motorboat", "cruiser")
# Uçma maddeleri (4 Eki, Bahadır onayı): C5/C6, Y5/Y6, P5/P6 araç havalanır
# 4 Eki, Bahadır: sadece fiilli kalıplar; "into the air" gibi yer ifadeleri başka nesneyle eşleşiyordu (kuru provada
# "hovers ... fragments into the air" Y5'ten geçti). "ascend" eklendi, "hover" bilerek yok.
_LIFT_AIR = _LIFT + ("swept up", "sweep up", "sweeps up", "ascend")
_CRASH_DOWN = ("crash", "slam", "smash", "land", "drop", "plunge", "plummet", "come down", "comes down", "came down",
               "fall", "fell", "hit", "strike", "struck",
               "collapse")   # 4 Eki, Bahadır: sadece kabulü genişletir
# Marina söküm/fırlatma (4 Eki, Bahadır): hortuma özel; heyelanın ortak _TEAR listesi değişmez
_TORNADO_RIP = ("tear", "tore", "torn", "rip", "wrench", "strip", "peel", "dislodge", "snap", "break", "broke",
                "sweep", "swept", "carry", "carried") + _FLING + _AIRBORNE
_DOWNHILL = ("downhill", "down the hill", "down the slope", "down the street", "down the lane", "along the lane",
             "down the road", "along the road")
# Yangın (TASLAK, 8 Eki, Bahadır): yangına özel YENİ listeler; mevcut sel/heyelan/hortum listelerine dokunulmaz ve
# onlardan türetilmez. Alevin bir şeye değdiği görünmeli: alev/tutuşma grupları sadece "rüzgâr esiyor" anlatımını
# geçirmez. Çok kelimeli terimlerde çekim sadece son kelimeye uygulanır, diğer çekimler ayrıca yazılır.
_FIRE_FLAME = ("flame", "fire", "blaze", "burn", "burnt", "inferno", "ablaze", "alight", "afire", "firestorm",
               "fiery", "aflame", "smolder", "smoulder")   # 10 Eki, Bahadır: canlıda "fiery" reddedildi
_FIRE_IGNITE = ("ignite", "catch fire", "catches fire", "caught fire", "catching fire", "set alight", "sets alight",
                "setting alight", "set ablaze", "sets ablaze", "setting ablaze", "set on fire", "sets on fire",
                "setting on fire", "set fire", "sets fire", "setting fire", "burst into flame", "bursts into flame",
                "burst into flames", "bursts into flames", "bursting into flames", "go up in flames",
                "goes up in flames", "went up in flames", "going up in flames", "engulf", "consume", "torch",
                "kindle", "swallow", "devour", "envelop", "ablaze", "alight", "on fire", "in flames")
_FIRE_EMBER = ("ember", "spark", "cinder", "glowing ash", "burning ash", "firebrand")
_FIRE_FALL = ("fall", "fell", "fallen", "crash", "topple", "drop", "collapse", "come down", "comes down",
              "came down", "coming down", "tumble", "plunge", "slam", "smash", "land")
_FIRE_TREE = ("tree", "pine", "trunk", "branch", "limb", "bough")
_FIRE_REVERSE = ("reverse", "back up", "backs up", "backed up", "backing up", "backward", "backwards", "retreat")
_FIRE_BACK = _FIRE_REVERSE + ("back away", "backs away", "backed away", "backing away", "lurch back",
                              "lurches back", "lurched back", "lurching back", "jerk back", "jerks back",
                              "jerked back", "pull back", "pulls back", "pulled back", "roll back", "rolls back",
                              "rolled back")
_FIRE_STOP = ("skid", "stop", "brake", "halt", "screech", "jolt", "slide", "slid")
_FIRE_TOUCH = ("lick", "touch", "reach", "scorch", "sear", "engulf", "wrap", "lap", "curl", "blister", "char",
               "singe", "envelop", "cover", "brush", "swallow")
_FIRE_FRONT = ("hood", "bonnet", "bumper", "grille", "grill", "front", "windshield", "windscreen")
_FIRE_ROOF = ("roof", "rooftop", "roofs")
_FIRE_SWERVE = ("swerve", "veer", "dodge", "weave", "steer", "jerk", "lurch", "swing", "swung",
                # 10 Eki, Bahadır: canlıda "maneuvers" reddedildi
                "maneuver", "manoeuvre", "evade", "sidestep", "careen", "zigzag")
_FIRE_RAIL = ("guardrail", "guard rail", "crash barrier", "barrier", "railing")
_FIRE_UTURN = ("u-turn", "turn around", "turns around", "turned around", "turning around", "whip around",
               "whips around", "whipped around", "wheel around", "wheels around", "spin around", "spins around",
               "spun around", "swing around", "swings around", "swung around", "turn back", "turns back",
               "turned back", "about-face")
_FIRE_CLOSE = ("close", "block", "cut off", "cuts off", "seal", "swallow", "engulf", "cover", "fill", "consume",
               "behind")
_FIRE_SPEED = ("race", "speed", "sped", "flee", "fled", "accelerate", "tear", "tore", "hurtle", "barrel", "zoom",
               "dash", "bolt", "drive", "drove", "away")
_FIRE_GLASS = ("window", "glass", "windshield", "windscreen")
_FIRE_CRACK = ("crack", "shatter", "split", "craze", "burst", "break", "broke", "blow out",
               "blows out", "blew out", "explode")
_FIRE_HOUSE = ("roof", "rooftop", "house", "home", "cottage")
_FIRE_FENCE = ("fence", "fencing", "picket", "palisade")
_FIRE_POLE = ("power pole", "utility pole", "telephone pole", "electricity pole", "pole", "pylon")
_FIRE_WIRE = ("wire", "cable", "power line", "line")
_FIRE_SNAP = ("snap", "break", "broke", "sever", "part", "fall", "fell", "drop", "whip", "lash", "spark")
_FIRE_PANEL = ("panel", "cladding", "sheet", "section", "slab")
_FIRE_DEBRIS = ("debris", "wreckage", "rubble", "fragment", "chunk", "piece", "panel", "cladding")
_FIRE_CRUSH = ("crush", "crumple", "cave", "flatten", "dent", "roof", "smash")
_FIRE_CURB = ("curb", "kerb", "sidewalk", "pavement", "footpath")
_FIRE_AWNING = ("awning", "canopy", "sunshade", "shade")
_FIRE_FLOOR = ("floor", "storey", "story", "level", "above", "upper", "higher")
_FIRE_BLOWOUT = ("blow out", "blows out", "blew out", "blowing out", "burst", "shatter", "explode", "smash", "break",
                 "broke", "pop")
_FIRE_PEEL = ("peel", "tear", "tore", "torn", "rip", "strip", "detach", "break", "broke", "come loose",
              "comes loose", "fall", "fell", "tumble", "drop", "plunge")
_FIRE_SMOKE = ("smoke",)
_FIRE_POUR = ("pour", "billow", "roll", "surge", "erupt", "belch", "spew", "gush", "burst", "climb")
_FIRE_TOWER = ("tower", "facade", "façade", "building", "floor", "storey", "story")
_FIRE_BALCONY = ("balcony", "balconies", "terrace")
_FIRE_FURNITURE = ("plant", "furniture", "chair", "table", "sofa", "cushion", "pot")
# Ateş hortumu: araç havalanır (hortumdaki mantık, yangına özel kopya). "into the air" bilerek yok
_FIRE_LIFT = ("lift", "hoist", "raise", "heave", "off its wheels", "off the ground", "off the road",
              "off the pavement", "airborne", "pick up", "picked up", "picks up", "swept up", "sweep up", "sweeps up",
              "ascend")
_FIRE_FLING = ("fling", "flung", "toss", "hurl", "throw", "threw", "thrown", "launch", "slam", "smash", "crash",
               "hurtle")
_FIRE_SPIN = ("spin", "spun", "twirl", "whirl", "rotate", "twist", "spiral", "tumble", "cartwheel", "roll")
_FIRE_CRASH_DOWN = ("crash", "slam", "smash", "land", "drop", "plunge", "plummet", "come down", "comes down",
                    "came down", "fall", "fell", "hit", "strike", "struck", "collapse")
_FIRE_SKID = ("skid", "slide", "slid", "fishtail", "sideways", "swerve", "veer")
_FIRE_RIP = ("rip", "tear", "tore", "torn", "wrench", "strip", "peel", "snap", "break", "broke", "lift", "hurl",
             "fling", "flung", "toss", "throw", "threw", "thrown", "scatter", "blow off", "blows off", "blew off",
             "sweep", "swept", "carry", "carried", "pull", "uproot", "suck", "spit")
_FIRE_SIGN = ("billboard", "hoarding", "advertising board", "signboard", "sign")
_FIRE_BRUSH = ("brush", "brushwood", "scrub", "undergrowth", "shrub", "bush", "dry grass", "grass", "twig")
_FIRE_SUCK = ("suck", "spit", "spew", "hurl", "fling", "flung", "toss", "throw", "threw", "thrown", "scatter",
              "whirl", "swirl", "lift", "draw", "pull", "sweep", "swept", "blast")
_FIRE_TRAILER = ("trailer", "caravan", "camper")
_FIRE_TOSS = _FIRE_RIP + ("tip", "topple", "overturn", "flip", "roll")
_FIRE_FUEL = ("trailer", "caravan", "camper", "woodpile", "wood pile", "firewood", "log pile", "log", "logs")
_FIRE_TILE = ("tile", "shingle", "slate")
# Helikopter (10 Eki, Bahadır): su, buhar, helikopter, rotor rüzgârı. Yeni listeler; mevcutlar değişmez.
_FIRE_WATER = ("water", "deluge", "cascade", "torrent", "spray", "retardant", "slurry", "waterload")
_FIRE_STEAM = ("steam", "vapor", "vapour", "mist", "white cloud", "white smoke")
_FIRE_HELI = ("helicopter", "chopper", "rotorcraft", "aircraft", "heli")
_FIRE_DROP = ("drop", "dump", "release", "unload", "pour", "spill", "fall", "fell", "crash", "slam", "douse",
              "drench", "unleash", "let go", "lets go")
_FIRE_DOUSE = ("extinguish", "douse", "drench", "quench", "smother", "snuff", "put out", "puts out", "knock down",
               "knocks down", "flatten", "collapse", "die down", "dies down", "die out", "dies out", "sink", "sank",
               "shrink", "fizzle", "beat back", "beats back", "kill")
_FIRE_DOWNDRAFT = ("downdraft", "down draft", "downwash", "rotor wash", "rotorwash", "rotor", "blade", "gust", "blast",
                   "wind")
_FIRE_SMOKE_EMBER = ("smoke", "ember", "spark", "ash", "cinder")
_FIRE_BEND = ("bend", "bent", "sway", "thrash", "whip", "flatten", "lash", "shake", "shook", "toss", "scatter", "blow",
              "blew", "blown", "swirl", "fling", "flung")
_FIRE_LOW = ("low", "skim", "swoop", "roar", "thunder", "buzz", "sweep", "swept", "hover", "fly", "flies", "flew",
             "pass", "scream")
_FIRE_PATH = ("road", "street", "lane", "in front", "ahead", "path")
_FIRE_RETURN = ("fight back", "fights back", "flare", "reignite", "re-ignite", "rekindle", "surge", "burst", "erupt",
                "roar back", "roars back", "fresh", "again", "renewed")
_FIRE_AGAIN = ("another", "second", "again", "circle back", "circles back", "circled back", "return", "come back",
               "comes back", "came back", "fresh", "new", "more")
_FIRE_RETREAT = ("sink", "sank", "shrink", "retreat", "die down", "dies down", "recede", "fall back", "falls back",
                 "fell back", "subside", "dwindle", "ebb", "beaten back", "pushed back", "driven back")
_FIRE_LEAP = ("leap", "jump", "spread", "race", "catch", "ignite", "engulf", "climb", "lick", "reach")
_FIRE_PULLUP = ("pull up", "pulls up", "pulled up", "pulling up", "climb", "rise", "rose", "peel away", "peels away",
                "bank away", "banks away", "fly off", "flies off", "flew off", "away", "veer off", "veers off", "soar")
_FIRE_SECOND = ("second", "another", "other", "new", "two", "pair")
# ⛈️ Süper hücre fırtınası (10 Eki, Bahadır): yeni _STORM_* listeleri; mevcut listeler değişmez ve kullanılmaz.
_STORM_HAIL = ("hail", "hailstone", "ice", "ice ball", "ice chunk")
_STORM_GLASS = ("windshield", "windscreen", "window", "glass", "pane")
_STORM_SMASH = ("smash", "shatter", "crack", "break", "broke", "burst", "explode", "punch through",
                "punches through", "cave", "crumple", "dent", "pierce")
_STORM_BRAKE = ("brake", "stop", "skid", "halt", "screech", "jolt")
_STORM_SWERVE = ("swerve", "veer", "dodge", "jerk", "lurch", "skid", "slide", "slid", "fishtail", "zigzag")
_STORM_ROW = ("row", "line", "one after another", "one after the other", "one by one", "in turn", "in succession",
              "all the")
_STORM_CAR = ("car", "cars", "vehicle", "sedan", "hatchback", "suv", "van", "truck", "pickup")
_STORM_AWNING = ("awning", "canopy", "sunshade", "shade")
_STORM_COLLAPSE = ("collapse", "cave", "crash", "fall", "fell", "drop", "tear", "tore", "torn", "rip", "give way",
                   "gives way", "gave way", "buckle", "sag", "tumble")
_STORM_UMBRELLA = ("umbrella", "parasol")
_STORM_FURNITURE = ("table", "chair", "furniture", "stool")
_STORM_TREE = ("tree", "branch", "limb", "bough", "trunk", "leaves", "foliage", "pine", "palm", "oak")
_STORM_STRIP = ("strip", "shred", "tear", "tore", "torn", "rip", "snap", "break", "broke", "batter", "pound", "lash",
                "split")
_STORM_SHOP = ("shop", "store", "storefront", "shopfront", "shop front", "window", "café", "cafe", "display")
_STORM_SHELTER = ("bus shelter", "bus stop", "shelter")
_STORM_BOUNCE = ("bounce", "rebound", "ricochet", "skip", "scatter", "spray", "pile", "carpet", "cover")
_STORM_WHITE = ("white", "carpet", "cover", "blanket", "pile", "bury", "buried", "coat")
_STORM_GREENHOUSE = ("greenhouse", "glasshouse", "conservatory", "hothouse", "skylight", "glass roof")
_STORM_CAVE = ("cave", "crumple", "dent", "crush", "flatten", "pound", "batter", "buckle", "smash", "punch")
_STORM_FALL = ("crash", "fall", "fell", "drop", "topple", "collapse", "come down", "comes down", "came down", "slam",
               "smash", "plunge", "land", "tumble")
_STORM_CRUSH = ("crush", "crumple", "cave", "flatten", "smash", "dent", "pin", "roof")
_STORM_POLE = ("utility pole", "power pole", "telephone pole", "electricity pole", "pole", "pylon")
_STORM_WIRE = ("wire", "cable", "power line", "line")
_STORM_SNAP = ("snap", "break", "broke", "split", "crack", "fall", "fell", "topple", "collapse", "crash", "give way",
               "gives way", "gave way")
_STORM_WHIP = ("whip", "lash", "thrash", "flail", "writhe", "snake", "dance", "jerk", "swing", "swung")
_STORM_SIGN = ("sign", "signboard", "billboard", "hoarding", "advertising board", "signpost")
_STORM_RIP = ("rip", "tear", "tore", "torn", "wrench", "peel", "strip", "snap", "break loose", "breaks loose",
              "broke loose", "pull", "blow off", "blows off", "blew off", "pry", "lift")
_STORM_FLY = ("fly", "flies", "flew", "flying", "hurl", "fling", "flung", "toss", "throw", "threw", "thrown", "sail",
              "tumble", "cartwheel", "spin", "spun", "whirl", "blow", "blew", "blown", "carry", "carried", "sweep",
              "swept")
# Araç havalanır (bu kategoride NO_LIFT_SLICE yok)
_STORM_LIFT = ("lift", "hoist", "raise", "heave", "off the road", "off the ground", "off its wheels", "off the lane",
               "airborne", "pick up", "picks up", "picked up", "swept up", "sweep up", "sweeps up")
_STORM_SIDE = ("on its side", "onto its side", "on to its side", "on its roof", "onto its roof", "flip", "overturn",
               "roll over", "rolls over", "rolled over", "tip", "topple", "capsize", "keel over")
_STORM_SLAM_DOWN = ("slam", "crash", "smash", "drop", "land", "plunge", "come down", "comes down", "came down", "hurl",
                    "throw", "threw", "thrown", "fling", "flung")
_STORM_SECOND = ("second", "another", "more", "next", "fresh", "new", "further", "again")
_STORM_BEND = ("bend", "bent", "bow", "flatten", "lean", "sway", "whip", "lash")
_STORM_LAMP = ("streetlamp", "street lamp", "streetlight", "street light", "lamppost", "lamp post", "light pole",
               "lamp")
_STORM_DUST = ("dust", "leaves", "leaf", "debris", "dirt", "sand", "grit")
_STORM_SWEEP = ("sweep", "swept", "roll", "rush", "race", "surge", "barrel", "blow", "blew", "blown", "tear", "tore",
                "drive", "drove")
_STORM_BINS = ("bin", "trash can", "dumpster", "branch", "debris", "garbage can", "rubbish")
_STORM_FENCE = ("fence", "fencing", "picket", "panel")
_STORM_TILE = ("tile", "shingle", "slate", "roofing")
_STORM_PEEL = ("peel", "rip", "tear", "tore", "torn", "strip", "fly", "flies", "flew", "blow off", "blows off",
               "blew off", "lift", "scatter")
_STORM_SHOVE = ("shove", "push", "slide", "slid", "drag", "sweep", "swept", "skid", "roll", "blow", "blew", "blown",
                "pin", "slam")
_STORM_SIDEWAYS = ("sideways", "broadside", "side-on", "side on", "across the lane", "across the lanes",
                   "across lanes")
_STORM_SPARK = ("spark", "arc", "flash", "fireball", "ember")
_STORM_TRANSFORMER = ("transformer", "power box", "electrical box", "substation")
_STORM_FIRE = ("fire", "flame", "blaze", "burn", "ablaze", "alight", "fireball", "spark", "fiery")
_STORM_BOLT = ("bolt", "lightning", "strike", "struck")
_STORM_SPLIT = ("split", "shatter", "crack", "explode", "blast", "rip", "tear", "tore", "torn", "cleave",
                "burst")
_STORM_EXPLODE = ("explode", "burst", "blow", "blew", "blown", "pop", "shatter", "flash", "spark", "blow out",
                  "blows out", "blew out")
_STORM_DARK = ("dark", "black", "blackout", "power cut", "goes out", "go out", "went out", "lights out", "unlit")
_STORM_CLIMB = ("climb", "spread", "lick", "creep", "engulf", "catch", "ignite", "flare", "crawl")
_STORM_TRUCK = ("truck", "lorry", "semi", "tractor-trailer", "big rig", "rig", "trailer")
_STORM_GRIND = ("grind", "scrape", "slide", "slid", "skid", "drag", "screech", "skate", "plow", "plough", "careen")
_STORM_LANE = ("lane", "highway", "road", "carriageway", "motorway", "asphalt")
_STORM_CARGO = ("cargo", "box", "crate", "load", "goods", "parcel", "package", "debris")
_STORM_SPIN = ("spin", "spun", "twirl", "whirl", "rotate", "pirouette", "turn", "swing", "swung")
_STORM_CLIP = ("clip", "hit", "strike", "struck", "graze", "bump", "nick", "slam", "smash", "crash", "ram")
_STORM_GUARDRAIL = ("guardrail", "guard rail", "crash barrier", "barrier", "railing", "median")
_STORM_VAN = ("van", "minivan", "camper")
_STORM_SCATTER = ("scatter", "strew", "spray", "fling", "flung", "hurl", "throw", "threw", "thrown", "litter", "shower",
                  "send", "sent", "spill", "dump", "sweep", "swept", "blow", "blew", "blown")
_STORM_RAINDUST = ("dust", "rain", "spray", "debris", "grit", "sand", "hail")
_FIRE_BURST = ("burst", "shatter", "crack", "explode", "split", "pop", "fly", "flies", "flew", "break",
               "broke")

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
    # 4 Eki, Bahadır onayı (havuzlar ve yasak eşleşmeler).
    TIDAL: {
        "slice_2": {
            "T1": {"text": "the {vehicle} is lifted and flung against a storefront",
                   "terms": [_LIFT + _FLING, _SHOP]},
            # 4 Eki, Bahadır: araç havalanmaz, su taşır (eski: "is lifted and carried down the street on top of
            # the surge")
            "T2": {"text": "the {vehicle} is carried down the street by the surge",
                   "terms": [("carry", "carried", "sweep", "swept", "drag", "dragged", "push", "pushed", "wash",
                              "washed"), ("down the street", "along the street", "down the road")]},
            "T3": {"text": "the {vehicle} is slammed into the car parked ahead and both are shoved along",
                   "terms": [_HIT, ("ahead", "in front", "another", "second", "other", "next", "parked")]},
            "T4": {"text": "the {vehicle} is spun sideways and dragged along the street",
                   "terms": [_SIDEWAYS + _SPIN, _DRAG]},
            "T5": {"text": "the {vehicle} tips over onto its side in the churning water",
                   "terms": [_TIP]},
            "T6": {"text": "the {vehicle} is pushed onto the sidewalk and slams into a lamppost",
                   "terms": [_CURB, _POLE]},
            # 4 Eki, Bahadır: "thrust" (kuru provada "thrust backward" reddedildi); _DRAG selle ortak, ona eklenmez
            "T7": {"text": "the {vehicle} is carried backwards down the street, bumping parked cars",
                   "terms": [_BACKWARD, _DRAG + ("thrust",)]},
            "T8": {"text": "the {vehicle} and the car behind it are dragged away together, bumper to bumper",
                   "terms": [_TOGETHER, _DRAG]},
        },
        "slice_3": {
            "W1": {"text": "a row of parked vehicles is ripped loose one by one and washed away",
                   "terms": [_ROW, _CAR, _RIP_AWAY]},
            "W2": {"text": "a lamppost topples into the surge",
                   "terms": [_POLE, _FALL]},
            "W3": {"text": "a street tree is uprooted and carried along",
                   "terms": [("tree", "trees"), ("uproot", "rip", "tear", "tore", "torn", "topple", "fall", "fell",
                                                 "wrench", "pull", "snap", "carry", "carried", "sweep", "swept",
                                                 "wash")]},
            "W4": {"text": "a roadside kiosk is torn off its base and swept away",
                   "terms": [("kiosk", "booth", "newsstand", "news stand", "snack bar", "hut", "shack"),
                             ("tear", "tore", "torn", "rip", "wrench", "sweep", "swept", "carry", "carried", "wash",
                              "pull", "snap", "break", "broke", "topple", "lift", "uproot")]},
            "W5": {"text": "a city bus is shoved sideways by the surge",
                   "terms": [("bus", "buses"), ("shove", "push", "sideways", "sweep", "swept", "drag", "slide", "slid",
                                                "tilt", "lurch", "skid", "swing", "swung", "turn")]},
            "W6": {"text": "a low wall collapses into the water",
                   "terms": [("wall", "walls"), ("collapse", "crumble", "topple", "fall", "fell", "give way",
                                                 "gives way", "gave way", "burst", "break", "broke", "cave",
                                                 "tumble", "burst apart")]},
            "W7": {"text": "shopfront windows burst and the surge pours through, carrying out chairs and tables",
                   "terms": [("window", "glass", "shopfront", "shop front", "storefront", "store front", "shop",
                              "cafe", "café", "restaurant"),
                             ("burst", "shatter", "smash", "break", "broke", "explode", "blow out", "blew out",
                              "cave", "give way", "gives way", "gave way"),
                             ("chair", "table", "furniture", "stool")]},
            "W8": {"text": "a dumpster tumbles down the street and smashes into a parked car",
                   "terms": [("dumpster", "skip", "trash bin", "rubbish bin", "garbage bin", "waste container",
                              "garbage container", "trash container", "container", "bin"),
                             ("tumble", "roll", "smash", "slam", "crash", "barrel", "bounce", "hurtle", "careen",
                              "ram")]},
        },
        "excluded_pairs": {("T6", "W2"), ("T1", "W7"), ("T2", "W1"), ("T8", "W1"), ("T3", "W8")},
        "excluded_views": {},
        # Kamera seawall'un üstünde duruyor: "alçak duvar çöker" olayı kameranın durduğu duvar gibi çizilir
        "excluded_spots": {"W6": {"Coastal avenue behind a seawall"}},
    },
    # ── Heyelan (TASLAK, 4 Eki, Bahadır hazırlığı; onay bekliyor) ──
    MUDSLIDE: {
        "slice_2": {
            "H1": {"text": "the {vehicle} is shoved sideways by the mud and slams into the car parked beside it",
                   "terms": [_SIDEWAYS, _HIT, _NEIGHBOR]},
            "H2": {"text": "the {vehicle} is pushed down the street by the mud, bumping parked cars",
                   "terms": [_DRAG, _BUMP]},
            "H3": {"text": "the {vehicle} is spun around by the mud and dragged downhill",
                   "terms": [_SPIN, _DRAG + _DOWNHILL]},
            "H4": {"text": "the {vehicle} is buried to its windows and pushed against a house wall",
                   "terms": [_BURY, _HOUSE]},
            "H5": {"text": "the {vehicle} tips over onto its side in the mud",
                   "terms": [_TIP]},
            "H6": {"text": "the {vehicle} and the car behind it are pushed down the street together, bumper to bumper",
                   "terms": [_TOGETHER_LANDSLIDE, _DRAG]},
        },
        "slice_3": {
            "M1": {"text": "a row of parked cars is pushed down the street one by one",
                   "terms": [_ROW, _CAR, _DRAG]},
            "M2": {"text": "a utility pole snaps and falls into the mud",
                   "terms": [_POLE, _FALL]},
            "M3": {"text": "a low garden wall collapses and its stones tumble down the street",
                   "terms": [("wall", "walls"), _COLLAPSE]},
            "M4": {"text": "a tree is torn out of the slope and carried down with the mud",
                   "terms": [("tree", "trees"), _UPROOT]},
            "M5": {"text": "a wooden fence is torn away and carried off",
                   "terms": [_FENCE, _TEAR]},
            "M6": {"text": "the mud rams a house corner and tears off its wooden porch",
                   "terms": [("porch", "veranda", "front steps", "stoop", "house corner", "corner of a house",
                              "corner of the house"), _TEAR + ("crush", "smash", "rip off", "rip away")]},
        },
        "excluded_pairs": {("H2", "M1"), ("H6", "M1"), ("H4", "M3"), ("H4", "M6")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    SLOPE: {
        "slice_2": {
            "R1": {"text": "the {vehicle} is shoved sideways across the road by the mud and rocks",
                   "terms": [_SIDEWAYS + ("across the road", "across both lanes"), _DRAG]},
            "R2": {"text": "the {vehicle} is pushed against the guardrail and pinned there",
                   "terms": [_GUARDRAIL, _HIT]},
            "R3": {"text": "a rolling boulder strikes the {vehicle}, which spins and slides down the road",
                   "terms": [_ROCK, _SPIN + ("slide", "slid", "skid")]},
            "R4": {"text": "the {vehicle} is buried to its windows in the mud and pushed toward the road edge",
                   "terms": [_BURY, ("edge", "shoulder", "verge", "side of the road", "roadside", "drop-off",
                                     "drop off")]},
            "R5": {"text": "the {vehicle} tips over onto its side in the mud",
                   "terms": [_TIP]},
            "R6": {"text": "the {vehicle} and the car behind it are shoved along the road together",
                   "terms": [_TOGETHER_LANDSLIDE, _DRAG]},
        },
        "slice_3": {
            "S1": {"text": "a section of the guardrail is bent and torn away by the mud",
                   "terms": [_GUARDRAIL, ("bend", "bent", "buckle", "twist", "tear", "tore", "torn", "rip", "wrench",
                                          "snap", "break", "broke", "collapse", "crumple", "flatten")]},
            "S2": {"text": "a large boulder rolls across the road and smashes into a parked car",
                   "terms": [_ROCK, ("roll", "tumble", "bounce", "crash", "smash", "slam", "hurtle", "careen",
                                     "barrel", "ram", "hit", "strike", "struck"), _CAR]},
            "S3": {"text": "a tree is torn out of the slope and slides across the road",
                   "terms": [("tree", "trees"), _UPROOT + ("slide", "slid")]},
            "S4": {"text": "a utility pole snaps and falls across the road",
                   "terms": [_POLE, _FALL]},
            "S5": {"text": "more of the slope gives way and a second surge of mud and rocks pours onto the road",
                   "terms": [("more", "second", "another", "again", "fresh", "new", "further"),
                             ("slope", "hillside", "mud", "rock", "rocks", "landslide", "torrent", "surge"),
                             ("give way", "gives way", "gave way", "collapse", "pour", "surge", "slide", "slid",
                              "crash", "tumble", "break", "broke", "burst")]},
            "S6": {"text": "a row of parked cars is shoved toward the road edge",
                   "terms": [_ROW, _CAR, _DRAG]},
        },
        "excluded_pairs": {("R3", "S2"), ("R2", "S1"), ("R6", "S6")},
        "excluded_views": {},
        # Kamera korkuluğun hemen arkasında duruyor: "korkuluk eğilip kopar" kameranın durduğu korkuluk gibi çizilir
        "excluded_spots": {"S1": {"Behind the guardrail of a hillside road"}},
    },
    VILLAGE: {
        "slice_2": {
            "K1": {"text": "the {vehicle} is swept down the lane and rammed against a house wall",
                   "terms": [_DRAG, _HIT, _HOUSE]},
            "K2": {"text": "the {vehicle} is spun around by the torrent and dragged along the lane",
                   "terms": [_SPIN, _DRAG]},
            "K3": {"text": "the {vehicle} is buried to its windows and pushed against a fence",
                   "terms": [_BURY, _FENCE]},
            "K4": {"text": "the {vehicle} tips over onto its side in the torrent",
                   "terms": [_TIP]},
            "K5": {"text": "the {vehicle} slams into a pile of logs and both are carried away",
                   "terms": [_LOGS, _DRAG]},
            "K6": {"text": "the {vehicle} is shoved into a parked motorbike and both are carried along",
                   "terms": [("motorbike", "motorcycle", "moped", "scooter", "bike"), _DRAG]},
        },
        "slice_3": {
            "L1": {"text": "a wooden house corner is struck and its wall collapses",
                   "terms": [("house", "home", "cottage", "cabin", "building"), _COLLAPSE]},
            "L2": {"text": "a stretch of wooden fence is torn away and carried off",
                   "terms": [_FENCE, _TEAR]},
            "L3": {"text": "a large tree is uprooted and rolls down with the torrent",
                   "terms": [("tree", "trees"), _UPROOT + ("roll", "tumble")]},
            "L4": {"text": "a roof section is torn off a shed and swept away",
                   "terms": [("roof", "roofing", "rooftop"), _TEAR]},
            "L5": {"text": "a pile of logs breaks loose and rolls down the lane",
                   "terms": [_LOGS, ("roll", "tumble", "break loose", "breaks loose", "broke loose", "scatter",
                                     "spill", "crash", "bounce", "slide", "slid", "sweep", "swept", "carry",
                                     "carried")]},
            "L6": {"text": "a stone wall collapses and its stones tumble into the torrent",
                   "terms": [("wall", "walls"), _COLLAPSE]},
        },
        "excluded_pairs": {("K1", "L1"), ("K3", "L2"), ("K5", "L5"), ("K1", "L6")},
        "excluded_views": {},
        # Kamera bir köy evinin üst kat balkonunda: "ev köşesi vurulur, duvarı çöker" kameranın durduğu ev gibi çizilir
        "excluded_spots": {"L1": {"Upper-floor balcony of a village house"}},
    },
    # ── Hortum (TASLAK, 4 Eki, Bahadır hazırlığı; onay bekliyor) ──
    LANDFALL: {
        "slice_2": {
            "C1": {"text": "the {vehicle} is shoved sideways across the street by the wind",
                   "terms": [_SIDEWAYS, _DRAG + _BLOW]},
            "C2": {"text": "the {vehicle} tips over onto its side as roof tiles rain down around it",
                   "terms": [_TIP, ("tile", "roof", "shingle", "slate")]},
            "C3": {"text": "a flying street sign slams into the windshield of the {vehicle}",
                   "terms": [_SIGN, _WINDSHIELD]},
            "C4": {"text": "the {vehicle} slides along the street and slams into a parked car",
                   "terms": [_DRAG + ("skid",), _HIT, ("parked", "another", "second", "other", "next",
                                                        "stationary")]},
            # 4 Eki, Bahadır onayı: uçma güncellemesi (eski C5 "a fallen tree branch crashes onto the roof of the
            # {vehicle}", eski C6 "the {vehicle} is pushed onto the sidewalk against a shop front")
            "C5": {"text": "the {vehicle} is lifted off the road and flung down the street",
                   "terms": [_LIFT_AIR, _FLING + ("hurtle", "tumble", "slam", "crash")]},
            "C6": {"text": "the {vehicle} is swept up into the air, spins, and crashes down onto the sidewalk",
                   "terms": [_LIFT_AIR, _SPIN, _CRASH_DOWN]},
        },
        "slice_3": {
            "E1": {"text": "the tornado tears the roof off a house and scatters the pieces across the street",
                   "terms": [("roof", "roofs", "roofing"), _TEAR + ("scatter", "peel", "strip", "rip off")]},
            "E2": {"text": "the tornado rips a billboard frame from its supports and throws it aside",
                   "terms": [("billboard", "hoarding", "advertising board", "sign frame", "signboard"),
                             _TEAR + _FLING]},
            "E3": {"text": "a wall of dust and debris sweeps across the street and engulfs the end of the block",
                   "terms": [("dust", "debris", "dirt", "sand"),
                             ("engulf", "swallow", "sweep", "swept", "envelop", "bury", "buried", "blanket",
                              "smother")]},
            "E4": {"text": "the tornado uproots a large tree and flings it through the air",
                   "terms": [("tree", "trees"), _UPROOT + _FLING]},
            "E5": {"text": "the tornado rips the front off a small shop, sending shutters and signs flying",
                   "terms": [("shop", "store", "storefront", "shopfront", "shop front", "shutter", "shutters"),
                             _TEAR + _AIRBORNE + _FLING + ("shear",)]},
            "E6": {"text": "the tornado tears away a section of fence and carries it down the street",
                   "terms": [_FENCE, _TEAR]},
        },
        # Aynı nesne iki kez: çatı (C2/E1). 4 Eki: C5/C6 uçma maddesi oldu, ağaç (C5/E4) ve dükkân önü (C6/E5)
        # artık ortak nesne değil, o iki çift kalktı
        "excluded_pairs": {("C2", "E1")},
        "excluded_views": {},
        # Kamera evin ön verandasında: "evin çatısı kopar" kameranın durduğu ev gibi çizilir
        "excluded_spots": {"E1": {"Residential coastal district"}},
    },
    MARINA_TORNADO: {
        # 4 Eki, Bahadır: marina yeniden tasarımı. Y1/Y3 yeni metin; Z1-Z6 tamamen yeni (direk ve yat sahneleri çıktı)
        "slice_2": {
            "Y1": {"text": "the {vehicle} is hit by flying debris and slides sideways across the quay",
                   "terms": [("debris", "wreckage", "rubble", "shrapnel", "flying object", "flying objects"),
                             _SIDEWAYS]},
            "Y2": {"text": "the {vehicle} tips over onto its side on the quay road",
                   "terms": [_TIP]},
            "Y3": {"text": "the {vehicle} slides along the quay and slams into a lamppost",
                   "terms": [_DRAG + _BLOW + ("hurl", "force", "skid"), _POLE]},
            "Y4": {"text": "a flying wooden crate smashes the windshield of the {vehicle}",
                   "terms": [("crate", "box", "pallet", "barrel", "cask"), _WINDSHIELD]},
            "Y5": {"text": "the {vehicle} is lifted off the quay road and flung into a stack of dock boxes",
                   "terms": [_LIFT_AIR, _FLING + ("slam", "smash", "crash", "hurtle"),
                             ("box", "boxes", "crate", "crates", "dock box", "locker", "bin", "bins", "stack")]},
            "Y6": {"text": "the {vehicle} is swept up into the air, spins, and crashes down onto the quay",
                   "terms": [_LIFT_AIR, _SPIN, _CRASH_DOWN]},
        },
        "slice_3": {
            "Z1": {"text": "the tornado tears the awning off the harbor café and flings it across the quay",
                   "terms": [("awning", "awnings", "canopy", "canopies", "sunshade", "parasol"), _TORNADO_RIP]},
            "Z2": {"text": "the tornado rips the front off a small kiosk, sending its shutters and signs flying",
                   "terms": [("kiosk", "booth", "stall", "hut", "shutter", "shutters", "sign", "signs"), _TORNADO_RIP]},
            "Z3": {"text": "a wall of dust and debris rolls across the quay and engulfs the café terrace",
                   "terms": [("dust", "debris", "dirt", "sand", "spray"),
                             ("engulf", "swallow", "envelop", "blanket", "smother", "bury", "buried", "roll", "sweep",
                              "swept")]},
            "Z4": {"text": "the tornado rips the roof off the marina office and scatters the pieces across the quay",
                   "terms": [("roof", "roofing"), ("office", "building", "hut", "cabin", "clubhouse", "shed",
                                                   "kiosk"), _TORNADO_RIP]},
            "Z5": {"text": "the tornado sweeps dock boxes and rubbish bins off the quay and hurls them across the road",
                   "terms": [("box", "boxes", "dock box", "bin", "bins", "rubbish bin", "trash can", "crate",
                              "crates"), _TORNADO_RIP]},
            "Z6": {"text": "the tornado shatters the glass front of a quayside shop and hurls tables and chairs into the "
                           "street",
                   "terms": [("glass", "window", "windows", "shopfront", "storefront", "shop front"),
                             ("shatter", "smash", "burst", "break", "broke", "explode", "blow out", "blew out",
                              "annihilate", "splinter",   # 4 Eki, Bahadır: kuru provada reddediliyordu
                              # 4 Eki, Bahadır: "obliterates" reddediliyordu. Çok kelimeli terimlerde çekim sadece
                              # son kelimeye uygulandığı için "tears/tore/torn apart" vb. ayrıca yazıldı
                              "obliterate", "demolish", "wreck", "wreak", "rupture", "pulverize",
                              "tear apart", "tears apart", "tore apart", "torn apart", "tearing apart",
                              "blow apart", "blows apart", "blew apart", "blown apart", "blowing apart"),
                             ("table", "tables", "chair", "chairs", "furniture", "stool")]},
        },
        # Aynı nesne iki kez: kutu (Y5/Z5), sandık (Y4/Z5)
        "excluded_pairs": {("Y5", "Z5"), ("Y4", "Z5")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    AVENUE: {
        "slice_2": {
            "P1": {"text": "the {vehicle} is shoved sideways across the avenue by the wind",
                   "terms": [_SIDEWAYS, _DRAG + _BLOW]},
            "P2": {"text": "the {vehicle} tips over onto its side",
                   "terms": [_TIP]},
            "P3": {"text": "the {vehicle} is pushed against a lamppost and pinned there",
                   "terms": [_POLE, _HIT]},
            # 4 Eki, Bahadır: cadde test videosunda sorun çıktı; palmiye artık araca çarpar (eski: "a palm tree
            # crashes onto the road in front of the {vehicle}"; "narrowly/missing" kaldırıldı)
            "P4": {"text": "a falling palm tree crashes onto the {vehicle}, crushing its roof",
                   "terms": [("palm", "palms", "palm tree", "tree", "trunk"),
                             ("crash", "fall", "fell", "topple", "slam", "smash", "drop", "come down", "comes down",
                              "came down", "collapse"), ("roof", "rooftop", "crush", "crumple", "cave", "flatten",
                                                         "dent")]},
            # 4 Eki, Bahadır onayı: uçma güncellemesi (eski P5 "slides into a bus shelter, shattering its glass",
            # eski P6 "and the car behind it are pushed along the avenue together")
            "P5": {"text": "the {vehicle} is lifted off the avenue and flung into a bus shelter, shattering its glass",
                   "terms": [_LIFT_AIR, _FLING + ("slam", "smash", "crash", "hurtle"), _SHELTER]},
            "P6": {"text": "the {vehicle} is swept up into the air, spins, and crashes down across the avenue",
                   "terms": [_LIFT_AIR, _SPIN, _CRASH_DOWN]},
        },
        "slice_3": {
            "Q1": {"text": "the tornado rips a row of palm trees out of the ground and flings them across the avenue",
                   "terms": [("palm", "palms", "palm tree", "tree", "trees"), _UPROOT + _FLING]},
            "Q2": {"text": "the tornado tears a billboard from its frame and sends it spinning away",
                   "terms": [_SIGN, _TEAR + _FLING + _SPIN]},
            "Q3": {"text": "the tornado hurls a cloud of signs, branches and bins along the avenue",
                   "terms": [("sign", "signs", "branch", "branches", "bin", "bins", "trash can", "debris"),
                             _FLING + _DRAG + _AIRBORNE]},
            "Q4": {"text": "the tornado tears the roof off a bus shelter and throws it aside",
                   "terms": [_SHELTER, ("roof", "canopy", "top", "panel", "panels"), _TEAR + _FLING]},
            "Q5": {"text": "the tornado topples a line of street lamps one by one",
                   "terms": [_POLE, _FALL]},
            "Q6": {"text": "the tornado rips the awnings off a row of shops and flings them high",
                   "terms": [("awning", "awnings", "canopy", "canopies", "shade", "blind", "blinds"),
                             _TEAR + _FLING + _AIRBORNE]},
        },
        # Aynı nesne iki kez: lamba (P3/Q5), otobüs durağı (P5/Q4), palmiye (P4/Q1)
        "excluded_pairs": {("P3", "Q5"), ("P5", "Q4"), ("P4", "Q1")},
        "excluded_views": {},
        # 10 Eki, Bahadır: kamera yüksek balkonda, Q5 dışlaması kalktı (eski: kamera kaldırımdaydı, "sokak
        # lambaları devrilir" kameranın durduğu kaldırıma düşüyordu: {"Q5": {"Downtown city center",
        # "High-rise coastal city"}})
        "excluded_spots": {},
    },
    # ── Yangın (TASLAK, 8 Eki, Bahadır): metinler ve yasak eşleşmeler Bahadır'ın, terim grupları yangına özel ──
    WILDFIRE: {
        "slice_2": {
            "K1": {"text": "the {vehicle} reverses hard down the road as a burning tree crashes across the lane in front "
                           "of it",
                   "terms": [_FIRE_REVERSE, _FIRE_FLAME, _FIRE_TREE, _FIRE_FALL]},
            "K2": {"text": "the {vehicle} skids to a stop as flames leap across the road and lick its hood",
                   "terms": [_FIRE_STOP, _FIRE_FLAME, _FIRE_TOUCH, _FIRE_FRONT]},
            "K3": {"text": "a burning branch falls onto the {vehicle}, setting its roof alight",
                   "terms": [_FIRE_TREE, _FIRE_FALL, _FIRE_ROOF, _FIRE_IGNITE]},
            "K4": {"text": "the {vehicle} swerves around a falling burning pine and slams into the guardrail",
                   "terms": [_FIRE_SWERVE, _FIRE_FLAME, _FIRE_TREE, _FIRE_RAIL]},
            "K5": {"text": "the {vehicle} U-turns in a cloud of smoke and speeds away as the flames close the road "
                           "behind it",
                   "terms": [_FIRE_UTURN, _FIRE_FLAME, _FIRE_CLOSE]},
            "K6": {"text": "embers rain onto the {vehicle} as it races down the road, its rear window cracking in the "
                           "heat",
                   "terms": [_FIRE_EMBER, _FIRE_GLASS, _FIRE_CRACK]},
        },
        "slice_3": {
            "L1": {"text": "the flames leap onto the roofs of the nearest houses and ignite them one after another",
                   "terms": [_FIRE_FLAME, _FIRE_HOUSE, _FIRE_IGNITE]},
            "L2": {"text": "a shower of glowing embers rains onto the street and sets a wooden fence alight",
                   "terms": [_FIRE_EMBER, _FIRE_FENCE, _FIRE_IGNITE]},
            "L3": {"text": "the fire races across a garden, engulfing a parked trailer and a woodpile",
                   "terms": [_FIRE_FLAME, _FIRE_FUEL, _FIRE_IGNITE]},
            "L4": {"text": "the wall of flames swallows a row of trees along the road, sending sparks high into the air",
                   "terms": [_FIRE_FLAME, _FIRE_TREE, _FIRE_IGNITE]},
            "L5": {"text": "a house roof catches fire and its tiles burst apart in the heat",
                   "terms": [_FIRE_ROOF, _FIRE_IGNITE, _FIRE_TILE, _FIRE_BURST]},
            "L6": {"text": "the flames climb a power pole and snap the wires, which whip across the street in a shower "
                           "of sparks",
                   "terms": [_FIRE_FLAME, _FIRE_POLE, _FIRE_WIRE, _FIRE_SNAP]},
        },
        "excluded_pairs": {("K1", "L4"), ("K3", "L2"), ("K6", "L2")},
        "excluded_views": {},
        # Kamera bir yamaç evinin balkonunda (Bahadır onayı, 8 Eki): ev çatısını yakan maddeler o noktada seçilmez
        "excluded_spots": {"L1": {"Balcony of a hillside house"}, "L5": {"Balcony of a hillside house"}},
    },
    FACADE_FIRE: {
        "slice_2": {
            "M1": {"text": "a burning panel crashes onto the {vehicle} parked below, crushing its roof",
                   "terms": [_FIRE_FLAME, _FIRE_PANEL, _FIRE_FALL, _FIRE_CRUSH]},
            "M2": {"text": "shattered glass rains onto the {vehicle} as it speeds away from the tower",
                   "terms": [("glass", "shard"), _FIRE_SPEED]},
            "M3": {"text": "burning debris lands on the hood of the {vehicle}, which lurches back in a hurry",
                   "terms": [_FIRE_FLAME, _FIRE_DEBRIS, _FIRE_FRONT, _FIRE_BACK]},
            "M4": {"text": "the {vehicle} swerves around a falling flaming panel and mounts the curb",
                   "terms": [_FIRE_SWERVE, _FIRE_FLAME, _FIRE_DEBRIS, _FIRE_CURB]},
            "M5": {"text": "a burning awning drops onto the {vehicle}, which reverses sharply",
                   "terms": [_FIRE_FLAME, _FIRE_AWNING, _FIRE_FALL, _FIRE_BACK]},
            "M6": {"text": "flaming debris smashes the windshield of the {vehicle} as it brakes hard",
                   "terms": [_FIRE_FLAME, _FIRE_DEBRIS, _FIRE_GLASS, _FIRE_STOP]},
        },
        "slice_3": {
            "N1": {"text": "the flames climb floor after floor, blowing out window after window",
                   "terms": [_FIRE_FLAME, _FIRE_FLOOR, _FIRE_GLASS, _FIRE_BLOWOUT]},
            "N2": {"text": "a balcony awning catches fire and the flames leap to the floor above",
                   "terms": [_FIRE_AWNING + _FIRE_BALCONY, _FIRE_IGNITE, _FIRE_FLOOR]},
            "N3": {"text": "burning panels peel off the facade and tumble down in a trail of sparks",
                   "terms": [_FIRE_FLAME, _FIRE_PANEL, _FIRE_PEEL]},
            "N4": {"text": "a wall of smoke and fire pours out of the upper floors and rolls up the tower",
                   "terms": [_FIRE_SMOKE, _FIRE_FLAME, _FIRE_POUR, _FIRE_TOWER]},
            "N5": {"text": "a row of windows explodes outward, spraying glass and flames over the street",
                   "terms": [_FIRE_GLASS, _FIRE_BLOWOUT, _FIRE_FLAME]},
            "N6": {"text": "the fire jumps to the neighboring balcony, igniting its plants and furniture",
                   "terms": [_FIRE_FLAME, _FIRE_BALCONY, _FIRE_IGNITE, _FIRE_FURNITURE]},
        },
        "excluded_pairs": {("M1", "N3"), ("M2", "N5"), ("M5", "N2")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    FIRE_TORNADO: {
        "slice_2": {
            "T1": {"text": "the {vehicle} is lifted off the road by the swirling flames and flung into a burning tree",
                   "terms": [_FIRE_LIFT, _FIRE_FLING, _FIRE_FLAME, _FIRE_TREE]},
            "T2": {"text": "a burning branch hurled by the tornado smashes the windshield of the {vehicle}",
                   "terms": [_FIRE_FLAME, _FIRE_TREE, _FIRE_GLASS]},
            "T3": {"text": "the {vehicle} is swept up into the air, spins, and crashes down onto the road in a shower "
                           "of sparks",
                   "terms": [_FIRE_LIFT, _FIRE_SPIN, _FIRE_CRASH_DOWN]},
            "T4": {"text": "the {vehicle} skids sideways as the fire tornado crosses the road behind it, throwing "
                           "embers across its roof",
                   "terms": [_FIRE_SKID, _FIRE_EMBER, _FIRE_ROOF]},
            "T5": {"text": "the {vehicle} is shoved against the guardrail by the whirling flames and its hood catches "
                           "fire",
                   "terms": [_FIRE_RAIL, _FIRE_FRONT, _FIRE_IGNITE]},
            "T6": {"text": "flaming debris slams into the side of the {vehicle}, which spins and stops across the road",
                   "terms": [_FIRE_FLAME, _FIRE_DEBRIS, _FIRE_SPIN]},
        },
        "slice_3": {
            "U1": {"text": "the fire tornado rips the burning roof off a house and scatters flaming pieces across the "
                           "street",
                   "terms": [_FIRE_ROOF, _FIRE_RIP, _FIRE_FLAME]},
            "U2": {"text": "the fire tornado uproots a burning tree and flings it down the road",
                   "terms": [_FIRE_TREE, _FIRE_RIP, _FIRE_FLAME]},
            "U3": {"text": "the whirling flames tear a billboard from its supports and hurl it aside",
                   "terms": [_FIRE_SIGN, _FIRE_RIP, _FIRE_FLAME]},
            "U4": {"text": "the tornado sucks up a pile of burning brush and spits it across the road in a fountain of "
                           "sparks",
                   "terms": [_FIRE_BRUSH, _FIRE_SUCK, _FIRE_FLAME + _FIRE_EMBER]},
            "U5": {"text": "the fire tornado tears a section of burning fence away and carries it across the field",
                   "terms": [_FIRE_FENCE, _FIRE_RIP, _FIRE_FLAME]},
            "U6": {"text": "the fire tornado sweeps over a parked trailer, tossing it aside in a cloud of fire and smoke",
                   "terms": [_FIRE_TRAILER, _FIRE_TOSS, _FIRE_FLAME]},
        },
        "excluded_pairs": {("T1", "U2"), ("T2", "U2"), ("T4", "U4")},
        "excluded_views": {},
        # Kamera bir yol kenarı evinin balkonunda (Bahadır onayı, 8 Eki): "evin çatısı kopar" o noktada seçilmez
        "excluded_spots": {"U1": {"Balcony of a roadside house"}},
    },
    # ── Helikopter (10 Eki, Bahadır: havuzlar ve yasak eşleşmeler ONAYLI, metin birebir) ──
    HELICOPTER: {
        "slice_2": {
            "F1": {"text": "the water load slams into the flames, flattening a section of the wall into a cloud of white "
                           "steam",
                   "terms": [_FIRE_WATER, _FIRE_FLAME, _FIRE_STEAM]},
            "F2": {"text": "the helicopter drops a second load and the water crashes down onto burning rooftops, sending "
                           "steam and sparks billowing",
                   "terms": [_FIRE_WATER, _FIRE_HOUSE, _FIRE_STEAM]},
            "F3": {"text": "the {vehicle} speeds down the street as the helicopter's downdraft whips smoke and embers "
                           "across the road",
                   "terms": [_FIRE_SPEED, _FIRE_DOWNDRAFT, _FIRE_SMOKE_EMBER]},
            "F4": {"text": "the helicopter roars low over the street, its downdraft bending the burning trees and "
                           "scattering embers",
                   "terms": [_FIRE_HELI, _FIRE_DOWNDRAFT, _FIRE_TREE, _FIRE_BEND]},
            "F5": {"text": "a wall of water falls on a burning house, the flames collapsing into thick white steam",
                   "terms": [_FIRE_WATER, _FIRE_HOUSE, _FIRE_STEAM]},
            "F6": {"text": "the {vehicle} brakes hard as a drenching cascade of water spills across the road in front of "
                           "it",
                   "terms": [_FIRE_STOP, _FIRE_WATER, _FIRE_PATH]},
        },
        "slice_3": {
            "G1": {"text": "the flames fight back, a fresh burst of fire swallowing trees beside the water line",
                   "terms": [_FIRE_FLAME, _FIRE_RETURN, _FIRE_TREE]},
            "G2": {"text": "the helicopter circles back and drops another huge load, extinguishing a row of burning trees "
                           "in a cloud of steam",
                   "terms": [_FIRE_HELI, _FIRE_DROP + _FIRE_WATER, _FIRE_TREE, _FIRE_DOUSE]},
            "G3": {"text": "thick white steam rolls over the street as the wall of flames sinks back toward the slope",
                   "terms": [_FIRE_STEAM, _FIRE_FLAME, _FIRE_RETREAT]},
            "G4": {"text": "embers blow past the helicopter as flames leap to a roof the water missed",
                   "terms": [_FIRE_EMBER, _FIRE_HOUSE, _FIRE_FLAME, _FIRE_LEAP]},
            "G5": {"text": "the helicopter pulls up and away as the flames roar back behind it",
                   "terms": [_FIRE_HELI, _FIRE_PULLUP, _FIRE_FLAME, _FIRE_RETURN]},
            "G6": {"text": "a second helicopter swoops in and drops water on the flames along the road",
                   "terms": [_FIRE_SECOND, _FIRE_HELI, _FIRE_DROP + _FIRE_WATER, _FIRE_FLAME]},
        },
        "excluded_pairs": {("F1", "G3"), ("F2", "G2"), ("F5", "G3")},
        "excluded_views": {},
        # Kamera bir yamaç evinin balkonunda (orman yangınındaki L1/L5 gibi): yanan çatıya/eve su düşmesi (F2, F5)
        # ve alevin ıskalanan bir çatıya sıçraması (G4) kameranın durduğu ev gibi çizilebilir; o noktada seçilmez
        "excluded_spots": {"F2": {"Balcony of a hillside house"}, "F5": {"Balcony of a hillside house"},
                           "G4": {"Balcony of a hillside house"}},
    },
    # ── ⛈️ Süper hücre fırtınası (10 Eki, Bahadır: havuzlar, yasak eşleşmeler ve kameralar ONAYLI, metin birebir) ──
    HAIL: {
        "slice_2": {
            "A1": {"text": "giant hail smashes the windshield of the {vehicle} as it brakes hard",
                   "terms": [_STORM_HAIL, _STORM_GLASS, _STORM_BRAKE]},
            "A2": {"text": "hailstones hammer a row of parked cars, shattering their windows one after another",
                   "terms": [_STORM_HAIL, _STORM_ROW, _STORM_CAR, _STORM_GLASS]},
            "A3": {"text": "the {vehicle} swerves as hail shatters its rear window and dents the hood",
                   "terms": [_STORM_SWERVE, _STORM_HAIL, _STORM_GLASS]},
            "A4": {"text": "a shop awning collapses under a pile of giant hail and crashes onto the sidewalk",
                   "terms": [_STORM_AWNING, _STORM_COLLAPSE, _STORM_HAIL]},
            "A5": {"text": "hail tears through a patio umbrella and flips café tables across the terrace",
                   "terms": [_STORM_HAIL, _STORM_UMBRELLA, _STORM_FURNITURE]},
            "A6": {"text": "hail strips the branches from a tree and bounces across the street",
                   "terms": [_STORM_HAIL, _STORM_TREE, _STORM_STRIP]},
        },
        "slice_3": {
            "B1": {"text": "a wall of hail sweeps down the street, shattering shop windows along the row",
                   "terms": [_STORM_HAIL, _STORM_SHOP, _STORM_SMASH]},
            "B2": {"text": "hail shatters the glass of a bus shelter and the pieces scatter across the sidewalk",
                   "terms": [_STORM_HAIL, _STORM_SHELTER, _STORM_SMASH]},
            "B3": {"text": "the street turns white as hailstones bounce high off the road and the cars",
                   "terms": [_STORM_HAIL, _STORM_BOUNCE, _STORM_WHITE]},
            "B4": {"text": "hail smashes through a greenhouse roof and glass rains down",
                   "terms": [_STORM_HAIL, _STORM_GREENHOUSE, _STORM_SMASH]},
            "B5": {"text": "hail caves in the roofs of a line of parked cars",
                   "terms": [_STORM_HAIL, _STORM_CAR, _STORM_CAVE]},
            "B6": {"text": "hailstones crack a tree trunk and a heavy branch crashes onto the road",
                   "terms": [_STORM_HAIL, _STORM_TREE, _STORM_FALL]},
        },
        "excluded_pairs": {("A2", "B5"), ("A4", "B1"), ("A1", "B5")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    DOWNBURST: {
        "slice_2": {
            "I1": {"text": "a huge tree crashes across the road in front of the {vehicle} as it brakes hard",
                   "terms": [_STORM_TREE, _STORM_FALL, _STORM_BRAKE]},
            "I2": {"text": "a tree topples onto a row of parked cars, crushing their roofs",
                   "terms": [_STORM_TREE, _STORM_CAR, _STORM_CRUSH]},
            "I3": {"text": "the {vehicle} swerves as a heavy branch slams into the road beside it",
                   "terms": [_STORM_SWERVE, _STORM_TREE, _STORM_FALL]},
            "I4": {"text": "a utility pole snaps and falls across the street, wires whipping",
                   "terms": [_STORM_POLE, _STORM_SNAP, _STORM_WIRE]},
            "I5": {"text": "a shop sign rips from a wall and flies down the street",
                   "terms": [_STORM_SIGN, _STORM_RIP + _STORM_FLY]},
            "I6": {"text": "wind rips the awning off a shop and hurls it down the street",
                   "terms": [_STORM_AWNING, _STORM_RIP + _STORM_FLY]},
            "I7": {"text": "the wind lifts the {vehicle} off the road and slams it down on its side",
                   "terms": [_STORM_LIFT, _STORM_SLAM_DOWN, _STORM_SIDE]},
        },
        "slice_3": {
            "J1": {"text": "a second line of trees bends flat and snaps one after another along the road",
                   "terms": [_STORM_SECOND + _STORM_ROW, _STORM_TREE, _STORM_BEND + _STORM_SNAP]},
            "J2": {"text": "a streetlamp bends and collapses onto the sidewalk",
                   "terms": [_STORM_LAMP, _STORM_BEND + _STORM_SNAP]},
            "J3": {"text": "a wall of dust and leaves sweeps down the avenue, hurling bins and branches",
                   "terms": [_STORM_DUST, _STORM_SWEEP, _STORM_BINS]},
            "J4": {"text": "a fence collapses and its panels tumble across the yards",
                   "terms": [_STORM_FENCE, _STORM_COLLAPSE + _STORM_FLY]},
            "J5": {"text": "roof tiles peel off a house and fly across the street",
                   "terms": [_STORM_TILE, _STORM_PEEL]},
            "J6": {"text": "the wind shoves a parked car sideways into a fence",
                   "terms": [_STORM_CAR, _STORM_SHOVE, _STORM_FENCE]},
        },
        "excluded_pairs": {("I2", "J1"), ("I4", "J2"), ("I6", "J3")},
        "excluded_views": {},
        # Kamera yamaçtaki bir evin balkonunda: "bir evin çatı kiremitleri uçar" kameranın durduğu ev gibi çizilir
        "excluded_spots": {"J5": {"Balcony of a hillside house over the street"}},
    },
    LIGHTNING: {
        "slice_2": {
            "O1": {"text": "broken wires drop and whip across the road, spitting sparks in front of the {vehicle}",
                   "terms": [_STORM_WIRE, _STORM_WHIP + _STORM_FALL, _STORM_SPARK]},
            "O2": {"text": "the transformer falls onto the road in a burst of fire and sparks",
                   "terms": [_STORM_TRANSFORMER, _STORM_FALL, _STORM_FIRE]},
            "O3": {"text": "the {vehicle} brakes hard as sparks rain over its hood",
                   "terms": [_STORM_BRAKE, _STORM_SPARK]},
            "O4": {"text": "a second bolt splits a tree beside the road, throwing burning branches onto the street",
                   "terms": [_STORM_BOLT, _STORM_TREE, _STORM_SPLIT]},
            "O5": {"text": "the pole snaps and crashes across the road, wires whipping and sparking",
                   "terms": [_STORM_POLE, _STORM_SNAP, _STORM_WIRE]},
            "O6": {"text": "the streetlights explode one after another along the road",
                   "terms": [_STORM_LAMP, _STORM_EXPLODE, _STORM_ROW]},
        },
        "slice_3": {
            "X1": {"text": "the whole block goes dark as sparks keep pouring from the broken lines",
                   "terms": [_STORM_DARK, _STORM_SPARK]},
            "X2": {"text": "lightning strikes again, shattering a tree trunk and scattering burning branches",
                   "terms": [_STORM_BOLT, _STORM_TREE, _STORM_SPLIT]},
            "X3": {"text": "loose wires whip along the road, throwing sparks",
                   "terms": [_STORM_WIRE, _STORM_WHIP, _STORM_SPARK]},
            "X4": {"text": "flames climb the base of a broken pole in the rain",
                   "terms": [_STORM_FIRE, _STORM_POLE, _STORM_CLIMB]},
            "X5": {"text": "another transformer blows farther down the street in a flash of fire",
                   "terms": [_STORM_SECOND, _STORM_TRANSFORMER, _STORM_EXPLODE]},
            "X6": {"text": "burning branches fall onto a parked car",
                   "terms": [_STORM_FIRE, _STORM_TREE, _STORM_CAR]},
        },
        "excluded_pairs": {("O2", "X5"), ("O4", "X2"), ("O5", "X1")},
        "excluded_views": {},
        "excluded_spots": {},
    },
    STORM_HIGHWAY: {
        "slice_2": {
            "H1": {"text": "the overturned truck grinds across the lanes in a shower of sparks as the {vehicle} swerves "
                           "to avoid it",
                   "terms": [_STORM_TRUCK, _STORM_GRIND, _STORM_SWERVE]},
            "H2": {"text": "the {vehicle} brakes hard and skids sideways as the wind pushes it across the lane",
                   "terms": [_STORM_BRAKE, _STORM_SIDEWAYS, _STORM_SHOVE]},
            "H3": {"text": "a trailer breaks loose and slides across the highway, scattering cargo",
                   "terms": [_STORM_TRUCK, _STORM_GRIND, _STORM_CARGO]},
            "H4": {"text": "a car clips the fallen truck and spins across the lane",
                   "terms": [_STORM_CLIP, _STORM_TRUCK, _STORM_SPIN]},
            "H5": {"text": "a highway sign tears loose and crashes onto the lanes",
                   "terms": [_STORM_SIGN, _STORM_RIP + _STORM_FALL]},
            "H6": {"text": "a second truck tips over behind the {vehicle}",
                   "terms": [_STORM_SECOND, _STORM_TRUCK, _STORM_SIDE]},
            "H7": {"text": "the wind lifts the {vehicle} off the lane and flips it over the guardrail",
                   "terms": [_STORM_LIFT, _STORM_SIDE, _STORM_GUARDRAIL]},
        },
        "slice_3": {
            "S1": {"text": "a van tips over and slides along the guardrail in a shower of sparks",
                   "terms": [_STORM_VAN, _STORM_SIDE, _STORM_GUARDRAIL]},
            "S2": {"text": "the wind sweeps boxes and debris across all lanes",
                   "terms": [_STORM_CARGO, _STORM_SCATTER, _STORM_LANE]},
            "S3": {"text": "cars skid to a stop in a long line as dust and rain sweep over the road",
                   "terms": [_STORM_CAR, _STORM_BRAKE, _STORM_ROW, _STORM_RAINDUST]},
            "S4": {"text": "a row of trees along the highway bends flat and scatters branches across the lanes",
                   "terms": [_STORM_TREE, _STORM_BEND, _STORM_SCATTER]},
            "S5": {"text": "a car spins around and slams into the guardrail",
                   "terms": [_STORM_CAR, _STORM_SPIN, _STORM_GUARDRAIL]},
            "S6": {"text": "a second truck tips over and slides across the lanes",
                   "terms": [_STORM_SECOND, _STORM_TRUCK, _STORM_SIDE]},
        },
        "excluded_pairs": {("H6", "S6"), ("H4", "S5"), ("H3", "S2")},
        "excluded_views": {},
        # Kamera üstgeçitte: otoyol tabelaları çoğu zaman üstgeçide asılı, "tabela kopup şeritlere düşer" kameranın
        # durduğu üstgeçitten kopuyor gibi çizilir
        "excluded_spots": {"H5": {"Overpass above the highway"}},
    },
}

# ── Yangın kapıları (TASLAK, 8 Eki, Bahadır). Sadece FIRE_EVENTS; diğer olayların denetimi değişmez. ─────────────
# Yağmur/ıslaklık yasağı: kilit cümle, havuz, hava, yer metni, stil eki ve GPT hikâyesinde. "rain" fiili sadece
# yanan/düşen bir şeyle birlikte geçerse serbest ("embers rain onto", "raining burning debris": Bahadır'ın kendi
# metinleri); yağış anlamındaki her "rain" reddedilir.
NO_RAIN_EVENTS = FIRE_EVENTS
_FIRE_WET = ("wet", "wetness", "soak", "drench", "rain-soaked", "waterlogged", "puddle", "downpour", "drizzle",
             "rainfall", "rainstorm", "raindrop", "rainwater", "rainy", "sleet", "damp", "monsoon")
_RAIN_TOKENS = ("rain", "rains", "rained", "raining")
_RAIN_FALLING_OK = ("ember", "spark", "cinder", "ash", "debris", "glass", "shard", "burning", "flaming", "glowing",
                    "fragment", "panel", "branch", "piece", "firebrand", "rubble", "flame")
_RAIN_WINDOW = 3
# Orman ve cephe yangınında araç havalanmaz (Bahadır onayı, 8 Eki): 4-9s'de kalkma ifadesi reddedilir
NO_LIFT_SLICE = {WILDFIRE: ("slice_2",), FACADE_FIRE: ("slice_2",),
                 HELICOPTER: ("slice_2",)}   # 10 Eki: helikopterde de araç havalanmaz
# Helikopter (10 Eki, Bahadır): ıslaklığın sebebi yağmur değil, helikopterin bıraktığı su. Bu olayda su bırakma
# ıslaklığı (wet, soak, drench...) serbest ve "rain" fiili suyla birlikte de geçebilir ("water rains down"); yağış
# ("heavy rain", downpour, rainfall, rain-soaked...) yine reddedilir.
WATER_DROP_EVENTS = (HELICOPTER,)
_WATER_DROP_OK = ("wet", "wetness", "soak", "drench", "waterlogged", "puddle", "damp")
_WATER_FALLING_OK = ("water", "spray", "droplet", "load")
_FIRE_NO_LIFT = ("lift", "hoist", "airborne", "off its wheels", "off the ground", "swept up", "sweep up", "sweeps up",
                 "levitate")


def rain_words(text: str, water_drop: bool = False) -> list[str]:
    """Yağış/ıslaklık ifadeleri. Yanan/düşen bir nesnenin yanında (±3 kelime) geçen "rain" fiili sayılmaz.
    water_drop (helikopter, 10 Eki): su bırakma ıslaklığı serbest, "rain" suyla birlikte de serbest; yağış yasak."""
    wet = tuple(w for w in _FIRE_WET if w not in _WATER_DROP_OK) if water_drop else _FIRE_WET
    falling_ok = _RAIN_FALLING_OK + (_WATER_FALLING_OK if water_drop else ())
    found = find_terms(wet, text)
    tokens = re.findall(r"[a-z]+(?:-[a-z]+)*", (text or "").lower())
    for i, tok in enumerate(tokens):
        if tok in _RAIN_TOKENS:
            near = tokens[max(0, i - _RAIN_WINDOW):i] + tokens[i + 1:i + 1 + _RAIN_WINDOW]
            if not any(w.startswith(ok) for w in near for ok in falling_ok):
                found.append(tok)
    return list(dict.fromkeys(found))

# ── Olaya özel dilim kapıları (4 Eki, Bahadır onayı): terimlerden biri dilimde geçmeli. Çekimler otomatik
# (find_terms). "people": True olan kuralın terimi koddan gelir: spec'teki N'in sayı kelimesi (kod N'i olayın kişi
# aralığından seçer, GPT cümleye döker). "away_from": kaçılan şey (mesaj satırı ve geri bildirim). ───────────────
NUMBER_WORDS = {3: "three", 4: "four", 5: "five", 6: "six"}
_FLEE = ("run", "ran", "running", "flee", "fled", "fleeing", "sprint", "scatter", "dash", "bolt", "race",
         # 4 Eki, Bahadır: kuru provada "scramble", "darting" reddedildi. "rush" YOK (su da "rushes")
         "scramble", "dart", "hurry")


def _people_rules(away_from: str) -> list[dict]:
    return [
        {"rule": "slice_flee", "field": "slice_1_rest", "terms": _FLEE,
         "missing": "0-4s: insanların kaçışı",
         "feedback": f"'slice_1_rest' must show people running away from {away_from}."},
        {"rule": "slice_count", "field": "slice_1_rest", "people": True, "away_from": away_from,
         "missing": "0-4s: kaçan kişi sayısı ({word})",
         "feedback": "'slice_1_rest' must say that {word} people run away from " + away_from + "."},
    ]


SLICE_RULES = {
    TIDAL: _people_rules("the wave"),
    # TASLAK (4 Eki, heyelan)
    MUDSLIDE: _people_rules("the mud"),
    SLOPE: _people_rules("the mud"),
    VILLAGE: _people_rules("the mud"),
    # TASLAK (4 Eki, hortum)
    LANDFALL: _people_rules("the tornado"),
    MARINA_TORNADO: _people_rules("the tornado"),
    AVENUE: _people_rules("the tornado"),
    # TASLAK (8 Eki, yangın): mevcut kaçış listesi (_FLEE, "rush" yok)
    WILDFIRE: _people_rules("the flames"),
    FACADE_FIRE: _people_rules("the flames"),
    FIRE_TORNADO: _people_rules("the fire tornado"),
    HELICOPTER: _people_rules("the flames"),   # 10 Eki: orman gibi
    # 10 Eki: süper hücre fırtınası, insanlar fırtınadan kaçar (mevcut _FLEE)
    HAIL: _people_rules("the storm"),
    DOWNBURST: _people_rules("the storm"),
    LIGHTNING: _people_rules("the storm"),
    STORM_HIGHWAY: _people_rules("the storm"),
}


def has_people_rule(event: str) -> bool:
    return any(r.get("people") for r in SLICE_RULES.get(event, ()))


def choose_people(event: str, ship: str | None, rng: random.Random | None = None) -> int | None:
    """Kaçan kişi sayısı N (olayın kişi aralığından); kişi kuralı olmayan olayda None."""
    if not has_people_rule(event):
        return None
    lo, hi = count_range(event, ship)
    return (rng or random).randint(lo, hi)


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

    def ok2(v):   # 10 Eki: kamera noktası dışlaması 4-9s maddesinde de olabilir (helikopter F2/F5)
        return spot not in b["excluded_spots"].get(v, set())
    return [(v, d) for v in b["slice_2"] for d in b["slice_3"]
            if (v, d) not in b["excluded_pairs"] and ok2(v) and ok3(d)]


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


# Görünümü olmayan olaylar (TASLAK, 4 Eki, heyelan): araç olayın kendi listesinden (EVENT_VEHICLES).
def event_vehicles(event: str, view: str | None) -> list[tuple[str, tuple[str, ...]]]:
    """Olayın araç listesi: görünüm varsa görünümün (REGION_VEHICLES), yoksa olayın (EVENT_VEHICLES)."""
    if view is not None:
        if view not in REGION_VEHICLES:
            raise StructureError(f"Görünümün araç listesi yok: {view}")
        return REGION_VEHICLES[view]
    if event not in EVENT_VEHICLES:
        raise StructureError(f"Olayın araç listesi yok: {event}")
    return EVENT_VEHICLES[event]


def choose_event_vehicle(event: str, rng: random.Random | None = None) -> str:
    return (rng or random).choice([v for v, _ in event_vehicles(event, None)])


def spec_vehicle_terms(spec: dict) -> tuple[str, ...]:
    for v, terms in event_vehicles(spec["event"], spec["view"]):
        if v == spec["vehicle"]:
            return terms
    raise StructureError(f"Araç listede yok: {spec['vehicle']} / {spec['event']} / {spec['view']}")


def structure_views(event: str) -> list[str | None]:
    """Olayın görünümleri: bölge görünümlü olaylarda 6 görünüm, diğerlerinde [None]."""
    return list(REGION_VIEWS) if event in REGION_VIEW_EVENTS else [None]


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
def build_spec(event: str, ship: str | None, spot: str, view: str | None, b2: str, b3: str, vehicle: str,
               people: int | None = None) -> dict:
    """Kie'ye gidecek prompt'u kuran ve denetleyen her şey (slices hariç). people: kaçan kişi sayısı N (sadece
    kişi kuralı olan olaylarda, zorunlu)."""
    if not is_structured(event):
        raise StructureError(f"Yapılandırılmış olay değil: {event}")
    if has_people_rule(event) != (people is not None):
        raise StructureError(f"Kaçan kişi sayısı uyuşmuyor: {event} / {people}")
    spec = {"event": event, "ship": ship, "spot": spot, "view": view, "beat_2": b2, "beat_3": b3,
            "vehicle": vehicle, "key_visual": EVENT_KEY_VISUAL[event],
            "suffix": style_suffix(event, ship, spot, view)}
    if people is not None:
        spec["people"] = people
    return spec


def people_word(spec: dict) -> str:
    return NUMBER_WORDS.get(spec.get("people"), "")


def people_line(spec: dict) -> str:
    """GPT'ye giden kaçan kişi satırı (kişi kuralı olan olaylarda), yoksa boş."""
    rule = next((r for r in SLICE_RULES.get(spec["event"], ()) if r.get("people")), None)
    if not rule:
        return ""
    w = people_word(spec)
    return (f"PEOPLE RUNNING AWAY: {w} (slice_1_rest must say that {w} people run away from "
            f"{rule['away_from']})\n")


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
    tw = TOTAL_WORDS_BY_EVENT.get(event, TOTAL_WORDS)
    if not tw[0] <= total <= tw[1]:
        out.append(_issue("total_words", f"toplam {tw[0]}-{tw[1]} kelime ({total})",
                          f"The three fields plus the fixed opening must total {tw[0]} to {tw[1]} "
                          f"words; now {total}."))
    for r in SLICE_RULES.get(event, ()):
        word = people_word(spec)
        terms = (word,) if r.get("people") else r["terms"]
        if not (all(terms) and find_terms(terms, slices.get(r["field"], ""))):
            out.append(_issue(r["rule"], r["missing"].format(word=word), r["feedback"].format(word=word)))
    beats = EVENT_BEATS[event]
    s2, s3 = slices.get("slice_2", ""), slices.get("slice_3", "")
    vterms = spec_vehicle_terms(spec)
    # 10 Eki: araç sadece seçilen 4-9s maddesinin metninde {vehicle} varsa zorunlu (mevcut tüm olaylarda hepsinde var;
    # helikopterin F1/F2/F4/F5 maddeleri araçsız)
    if "{vehicle}" in beats["slice_2"][spec["beat_2"]]["text"] and not find_terms(vterms, s2):
        out.append(_issue("beat_vehicle", f"4-9s: araç ({spec['vehicle']})",
                          f"'slice_2' must name the {spec['vehicle']}."))
    for slot, bid, text in (("slice_2", spec["beat_2"], s2), ("slice_3", spec["beat_3"], s3)):
        miss = missing_term_groups(beats[slot][bid]["terms"], text)
        if miss:
            label = "4-9s" if slot == "slice_2" else "9-15s"
            event_text = beat_text(event, slot, bid, spec["vehicle"])
            out.append(_issue("beat_terms", f"{label}: seçilen olay ({bid}) görünmüyor",
                              f"'{slot}' must clearly show this event: {event_text}."))
    # Yangın (8 Eki): yağmur/ıslaklık yasağı (kilit cümle dahil tüm hikâye) ve 4-9s'de araç havalanmaz
    if event in NO_RAIN_EVENTS:
        wet = rain_words(plain_story(spec, slices), event in WATER_DROP_EVENTS)
        if wet:
            out.append(_issue("fire_no_rain", f"yağmur/ıslaklık yasak ({', '.join(wet)})",
                              f"Remove {', '.join(repr(w) for w in wet)}: the air is hot and dry; no rain, wet or "
                              f"soaked surfaces anywhere."))
    for slot in NO_LIFT_SLICE.get(event, ()):
        lifted = find_terms(_FIRE_NO_LIFT, slices.get(slot, ""))
        if lifted:
            label = "4-9s" if slot == "slice_2" else "9-15s"
            out.append(_issue("fire_no_lift", f"{label}: araç havalanmaz ({', '.join(lifted)})",
                              f"In '{slot}' the {spec['vehicle']} stays on the ground: remove "
                              f"{', '.join(repr(w) for w in lifted)}."))
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
    if has_people_rule(spec["event"]):
        lo, hi = count_range(spec["event"], spec["ship"])
        if not (isinstance(spec.get("people"), int) and lo <= spec["people"] <= hi and people_word(spec)):
            out.append(_issue("people", f"kaçan kişi sayısı {lo}-{hi} değil ({spec.get('people')})"))
    elif "people" in spec:
        out.append(_issue("people", "kişi kuralı olmayan olayda kaçan kişi sayısı var"))
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
    suffix_wet = rain_words(expected_suffix, spec["event"] in WATER_DROP_EVENTS)
    if spec["event"] in NO_RAIN_EVENTS and suffix_wet:   # 8 Eki: yangında stil eki de yağmursuz
        out.append(_issue("fire_no_rain_suffix", f"stil ekinde yağmur/ıslaklık ({', '.join(suffix_wet)})"))
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
    if set(EVENT_VEHICLES) - set(EVENT_KEY_VISUAL):
        raise StructureError(f"Araç listesi yapılandırılmamış olayda: {set(EVENT_VEHICLES) - set(EVENT_KEY_VISUAL)}")
    if set(SLICE_RULES) - set(EVENT_KEY_VISUAL):
        raise StructureError(f"Dilim kapısı yapılandırılmamış olayda: {set(SLICE_RULES) - set(EVENT_KEY_VISUAL)}")
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
        for d in b["excluded_views"]:
            if d not in b["slice_3"]:
                raise StructureError(f"Bölge kısıtı bilinmeyen id: {d}")
        for d in b["excluded_spots"]:   # 10 Eki: kamera noktası dışlaması 4-9s ya da 9-15s maddesinde
            if d not in b["slice_3"] and d not in b["slice_2"]:
                raise StructureError(f"Bölge kısıtı bilinmeyen id: {d}")
        for r in SLICE_RULES.get(event, ()):
            if r["field"] not in SLICE_FIELDS or not (r.get("people") or r.get("terms")):
                raise StructureError(f"Dilim kapısı hatalı: {event}/{r.get('rule')}")
        if has_people_rule(event):
            lo, hi = count_range(event, None)
            if any(n not in NUMBER_WORDS for n in range(lo, hi + 1)):
                raise StructureError(f"Kişi aralığının sayı kelimesi yok: {event} {lo}-{hi}")
        if event in REGION_VIEW_EVENTS:
            if event in EVENT_VEHICLES or b["excluded_views"] and set().union(*b["excluded_views"].values()) - set(REGION_VIEWS):
                raise StructureError(f"Görünümlü olayda olay araç listesi ya da bilinmeyen görünüm: {event}")
        elif not EVENT_VEHICLES.get(event) or any(not t for _, t in EVENT_VEHICLES[event]) or b["excluded_views"]:
            raise StructureError(f"Görünümsüz olayın araç listesi yok ya da görünüm kısıtı var: {event}")
        for d, spots in b["excluded_spots"].items():
            if spots - set(EVENT_SKELETONS[event]["spots"]):
                raise StructureError(f"Bilinmeyen spot: {event}/{d}: {spots - set(EVENT_SKELETONS[event]['spots'])}")
        for view in structure_views(event):
            for spot in view_spots(event, view):
                if not allowed_pairs(event, view, spot):
                    raise StructureError(f"İzinli olay çifti yok: {event} / {view} / {spot}")


_validate_data()
