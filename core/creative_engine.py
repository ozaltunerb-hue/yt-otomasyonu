from __future__ import annotations

"""
Creative Engine — "DeepMyster" Doğukan Metodolojisi & Yaratıcı Serbestlik Standardı.

Temel İlkeler:
  1. YARATICI KONTROLÜN TERSİNE ÇEVRİLMESİ (Inversion of Control):
     Python kodu sabit cümle parçalarını dikte etmez. GPT-4o geniş denizcilik evreni içinde
     özgürce olay, gemi mimarisi, fiziksel kriz ve kamera açısını belirler.
  2. DEEPMYSTER INSPIRATION & EXISTING IDEAS LIBRARY (71 Temel Senaryo):
     Mevcut 71 fikir deterministik bir seçim listesi DEĞİLDİR; GPT-4o'nun DeepMyster evrenini
     anlaması, bilinen konuları tekrar etmemesi ve yeni denizcilik ufukları keşfetmesi için
     sağlanan semantik referans kütüphanesidir.
  3. DOĞUKAN METODOLOJİSİ (Less is More):
     Seedance 2 Mini için 25–45 kelimelik yüksek görsel sinyal yoğunluklu, süssüz,
     tek kesintisiz, yapılandırılabilir süreli (config.DEFAULT_DURATION) fotogerçekçi
     CCTV/belgesel promptları.
  4. SÖZDİZİMSEL ÇEŞİTLİLİK (Anti-Few-Shot Klonlama):
     Farklı cümle yapıları, farklı bakış açıları ve organik insan rolleri.
"""
import random
import logging
from typing import List, Dict, Any

log = logging.getLogger("CreativeEngine")

# ─────────────────────────────────────────────────────────────────────────────
# 📚 DEEPMYSTER EXISTING IDEAS & BRAND UNIVERSE (71 Referans Senaryo Kütüphanesi)
# ─────────────────────────────────────────────────────────────────────────────
# Bu kütüphane GPT-4o'ya "neler yaptığımızı ve marka tonumuzu" öğretir.
# GPT bu fikirleri birebir kopyalamaz; buradan yola çıkarak yeni olaylar türetir.

DEEPMYSTER_EXISTING_IDEAS_LIBRARY = {
    "ro_ro_emergencies": {
        "title": "Ro-Ro & Araç Feribot Acil Durumları",
        "reference_scenarios": [
            "Car ferry rolling violently in heavy swells as deck crew in yellow foul weather gear battle to lash shifting cars on open vehicle deck.",
            "A passenger car ferry surges at the loading ramp in storm chop as dock staff frantically wave disembarking cars off the heaving ramp.",
            "Deckhands scrambling across wet flooded vehicle deck to hook emergency heavy chains on sliding cars in severe gale.",
            "Ferry captain and navigation officers urgently correcting thrusters as open bow visor takes pounding oceanic waves.",
            "Passengers gripping safety handrails as a rolling high-speed catamaran heels sharply and deck crew scramble to secure storm gates before the next wave hits.",
            "Ferry deckhands on a pitching stern ramp fight to re-secure vehicle lashings as a swell lifts the ramp off the quay.",
            "Island car ferry crew directing vehicles while surge waves wash across lower loading ramp during emergency departure.",
            "On a passenger car ferry's lower vehicle deck, a sudden roll sends rows of lashed cars straining against their chains, grinding hard against each other.",
            "On a ferry's vehicle deck, a poorly secured car breaks loose in rough seas and slides into a neighboring vehicle, drivers scrambling out in a panic.",
            "A car waiting at the ramp entrance is jolted hard as the passenger car ferry suddenly rolls, the driver braking hard in a panic to avoid rolling off the ramp.",
            "On an open-deck island car ferry, sudden wash floods across the vehicle deck submerging tires as owners in casual clothing dash back to their cars.",
            "A lashing chain snaps on the vehicle deck, freeing a car to slide across the wet deck as crew scramble clear of its path.",
        ],
    },
    "marina_incidents": {
        "title": "Yat Marinaları & Marina Acil Durumları",
        "reference_scenarios": [
            "Marina dock staff frantically sprinting along floating pontoon to deploy heavy inflatable fenders as runaway yacht approaches luxury slips.",
            "Yacht captain and deckhand on bow desperately throwing mooring lines to marina crew during sudden storm surge.",
            "Marina staff using long boat hooks to fend off drifting luxury yacht slamming toward wooden pontoons in sudden harbor squall.",
            "Private yacht with a jammed throttle careens out of control across the marina fairway as the skipper fights the wheel and dockworkers scatter clear.",
            "Marina emergency response crew in safety gear rushing along pontoon with fire hoses toward smoking yacht aft deck.",
            "Dockmaster and marina personnel securing straining cleat lines as violent storm surge lifts floating pontoons with tilting motor yachts.",
            "Marina staff on a floating pontoon race to fend off a drifting runaway powerboat before it slams into the concrete breakwater.",
            "A sailing yacht caught broadside in a passing vessel's wake near the marina entrance heels hard, nearly capsizing as the crew scramble to the high side.",
            "A yard travel lift malfunctions with a hoisted yacht swinging dangerously in its slings as yard staff scatter clear of the suspended hull.",
            "A dockside electrical fire flares and spreads rapidly toward neighboring sailing yachts as marina staff race to contain it with extinguishers and hoses.",
            "A mooring line snaps during a dockside gathering, the luxury motor yacht lurching hard toward the pier as people aboard lose their footing and grab for the rail.",
            "A jet ski launches airborne after hitting another vessel's wake at the marina entrance, the rider bracing hard for a rough landing.",
        ],
    },
    "passenger_terminals": {
        "title": "Yolcu İskeleleri & Feribot Terminalleri",
        "reference_scenarios": [
            "Ferry captain working thruster levers as commuter ferry slams hard against pier wooden fender dolphins in strong harbor surge.",
            "A cruise liner's gangway buckles and tears loose under sudden vessel surge as deck crew scramble to pull passengers back before the walkway collapses into the water.",
            "Terminal dockworkers jumping back as heavy mooring line snaps violently under high tension in gale winds.",
            "Passenger ferry drifts out of control toward a crowded terminal pier as dockside crowds scramble clear and crew fire emergency horn blasts, the hull grazing the fender pilings at the last second.",
            "A cruise liner narrowly misses a pier structure as the captain executes a last-second emergency turn, passengers on the open upper deck bracing against the railings.",
            "Terminal dock staff rushing to secure double-cleated lines from a pitching passenger car ferry in breaking waves.",
            "Cruise ship's towering hull surges against the terminal fendering as mooring winches strain and dock crew scramble clear of snapping lines in gusting crosswind.",
            "A cruise ship's pool-deck glass wind-break screen cracks and shatters under a sudden storm gust, deck staff evacuating sunbathing passengers from the area.",
        ],
    },
    "harbor_collisions": {
        "title": "Liman İçi Gemi Manevraları & Yakın Geçişler",
        "reference_scenarios": [
            "A high-speed catamaran misjudges its berthing turn and slams its bow into the terminal fendering as dockworkers scramble clear of a snapping mooring line.",
            "A passenger car ferry's stern swings wide in a gusting crosswind and grinds along the concrete quay, sparks flying as dock staff wave waiting cars back.",
            "Cruise liner listing hard against the terminal fendering as harbor pilots scramble to correct a sudden list during final approach, the towering hull scraping the pier.",
            "A cruise tender boat surges against the liner's side platform in heavy swell, crew bracing as the boarding gangway lurches and jams.",
            "A luxury motor yacht reversing into its berth loses throttle control and rams the neighboring sailing yacht, fenders bursting and rigging swinging.",
            "A high-speed catamaran caught in a departing car ferry's wash in the narrow harbor entrance heels hard as passengers grab the rails.",
            "Terminal dockworkers dive clear as a mega cruise ship's mooring line parts under load and whips across the quay.",
            "An open-air deck bar's tables and umbrellas are blown into chaos as sudden heavy weather hits, passengers in casual wear fleeing indoors past toppling furniture.",
        ],
    },
    "rough_seas_storms": {
        "title": "Açık Deniz Fırtınaları & Dev Dalgalar",
        "reference_scenarios": [
            "A massive green wave crashes over the bow of a passenger car ferry, spray bursting across the bridge windows as officers brace at the consoles.",
            "Deckhands in orange foul weather gear cling to lifelines on a rolling car ferry's open vehicle deck as seawater sweeps between lashed cars.",
            "A high-speed catamaran's captain and helmsman grip steering consoles as green seawater floods the forward bridge windows in towering swell.",
            "A sailing yacht heels violently in freezing cross-seas as its crew in heavy foul weather gear fight to reef the thrashing mainsail.",
            "A high-speed catamaran yaws hard off course in towering storm swells as the bridge crew fight the helm and passengers brace in their seats.",
            "A high-speed catamaran slams down hard off a storm swell, loose luggage tumbling across the passenger cabin floor.",
            "An offshore waterspout sweeps into a coastal marina, tearing a sailing yacht from its mooring and spinning it into the pontoon.",
            "A rogue wave sweeps across a cruise ship's open pool deck as sunbathing passengers in swimwear scramble for cover, pool water surging violently across the tiles.",
        ],
    },
    "navigation_hazards": {
        "title": "Kanal, Boğaz & Sığ Su Seyir Tehlikeleri",
        "reference_scenarios": [
            "A cruise liner's stern swings dangerously close to a narrow canal embankment under sudden bank suction as officers fight the helm.",
            "A sailing yacht's keel strikes a hidden sandbar at speed, the mast whipping forward as the crew are thrown against the cockpit.",
            "Harbor pilot and captain tensely reversing engines as dense fog suddenly reveals unlit breakwater buoy ahead.",
            "A passenger car ferry in a narrow rocky inlet is swept sideways by a strong eddy current, its hull scraping along the rocks.",
            "A runaway powerboat skims across shallow water and grounds hard on a sandbank, the hull slewing sideways in a burst of spray.",
            "Ferry captain executing emergency bow thruster maneuver as outgoing tidal rip threatens to turn vessel broadside.",
            "A jet ski cuts across a ferry's bow in a busy channel, the ferry veering hard as passengers lurch against the rails.",
            "A passenger walking an upper deck stumbles hard into the railing as the cruise ship suddenly rolls, crew rushing over to help them back to their feet.",
        ],
    },
    "emergency_rescue": {
        "title": "Acil Müdahale & Kurtarma Operasyonları",
        "reference_scenarios": [
            "Deck crew in bright orange foul weather gear rushing across flooded deck to deploy portable emergency bilge pumps.",
            "Cruise tender boat crew launch into violent breaking surf to reach a swamped jet ski rider, the tender pitching hard in the swell.",
            "Cruise liner officers on the open bridge wing scanning dark storm waves with high-power searchlights to guide rescue swimmers.",
            "Ferry deckhands battle a howling gale to re-rig torn safety lines across the open car deck as spray sweeps over the rail.",
            "A lifeboat swinging from a mega cruise ship's davits slams against the towering hull in heavy swell as crew fight the falls.",
            "Cruise liner passengers scrambling down a swaying gangway into a pitching tender boat as crew battle to hold it steady against the hull in rough swell.",
            "Marina staff hurl life rings and rescue lines to a luxury motor yacht's crew as the yacht floods and lists at its berth.",
            "Wind and swell send deck loungers and tables sliding and tumbling across a cruise ship's open sun deck as passengers in resort wear grab for the railings.",
        ],
    },
    "machinery_failures": {
        "title": "Makine, Dümen & Sistem Arızaları",
        "reference_scenarios": [
            "Ferry captain and helmsman fighting the manual emergency steering wheel as the passenger car ferry drifts toward a rocky breakwater.",
            "Marine engineers in boiler suits rushing through vibrating engine room to isolate blown hydraulic steering pipe.",
            "Electrical engineer resetting main switchboard breakers under emergency red backup lighting during violent storm blackout.",
            "Bridge officers and lookouts on a cruise liner reacting to sudden bow thruster failure as crosswinds push the towering hull toward the terminal pier during docking.",
            "A restraining cable snaps early on a shipyard slipway, the sailing yacht lurching down the ways as yard workers in hi-vis scatter clear.",
            "Chief engineer and mechanics working frantically on jammed steering gear actuator as storm waves batter the hull.",
            "Bridge crew scrambling as the backup radar flickers out and the emergency generator strains to take load while the cruise liner rolls hard in heavy seas.",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 🌊 10 GENİŞ DENİZCİLİK İLHAM ALANI (Genişletilmiş Operasyonel Ufuk)
# ─────────────────────────────────────────────────────────────────────────────

MARITIME_INSPIRATION_DOMAINS = {
    "ferry_operations": {
        "title": "Feribot & Yolcu Dinamikleri (Ferry & Passenger Vessel Logistics)",
        "guidance": "Vehicle deck kinetic weight shifts in cross swells, loading ramp hydraulic hinge pressure, bow visor spray seals, high-speed catamaran roll recovery, unsecured cars breaking loose and sliding on ferry vehicle decks, ramp-entrance vehicle jolts, wash flooding the open vehicle deck.",
        "example_elements": ["island vehicle ferry", "high-speed passenger catamaran", "open-deck vehicle ferry", "hydraulic ramp hinge", "deck drainage scuppers"],
        "camera_styles": ["fixed car deck security CCTV", "stationary ramp coaming surveillance camera", "overhead mezzanine deck camera"],
    },

    "shipyard_and_drydock_engineering": {
        "title": "Tersane, Kuru Havuz & Kızak Dinamikleri (Drydock & Launch Mechanics)",
        "guidance": "Floating drydock flooding/un-docking stability, slipway gravitational launch friction, hull keel block settling, giant propeller shaft rig placement.",
        "example_elements": ["floating drydock", "shipyard slipway", "caisson dock gate", "timber keel block", "high-tonnage gantry crane sling"],
        "camera_styles": ["fixed drydock wing-wall CCTV", "stationary dock basin security camera", "crane gantry overview camera"],
    },
    "marina_and_yacht_operations": {
        "title": "Marina & Yat Operasyonları (Marina & Yacht Incidents)",
        "guidance": "Yacht or powerboat losing control near marina pontoons, runaway vessel drifting toward moored boats or dock structures, marina staff emergency response, storm surge lifting floating docks, fuel dock emergencies, travel lift hoisting failures, dockside fires, boat wake collisions, jet ski/small boat wake incidents near the marina entrance.",
        "example_elements": ["luxury motor yacht", "sailing yacht", "runaway powerboat", "floating pontoon dock", "marina fuel dock", "mooring cleat under strain", "boat travel lift", "jet ski", "marina fire hose station"],
        "camera_styles": ["fixed marina pontoon CCTV", "stationary fuel dock security camera", "dockside harbor camera"],
    },
    "cruise_ship_operations": {
        "title": "Yolcu Gemisi & Kruvaziyer Operasyonları (Cruise & Large Passenger Ship Ops)",
        "guidance": "Cruise liner terminal berthing and bow thruster docking dynamics, gangway connection stress under swell, tender boat launch/recovery in rough water, hull list correction, near-miss pier approaches. Also covers onboard pool-deck and sun-deck incidents: rogue waves sweeping the pool deck, wind-blown deck furniture, sudden rolls throwing passengers off balance, deck bar chaos in sudden weather.",
        "example_elements": ["ocean cruise liner", "mega cruise ship", "cruise ship tender boat", "passenger gangway", "bow thruster docking system", "terminal mooring bollard", "open-air pool deck", "sun deck loungers", "glass wind-break screen"],
        "camera_styles": ["fixed terminal berth CCTV", "stationary gangway connection camera", "quayside cruise terminal security camera", "onboard pool-deck security camera", "sun-deck overhead security camera"],
    },
    "coastal_tornado_landfall": {
        "title": "Coastal Tornado / Denizden Karaya Hortum",
        "guidance": "A powerful tornado forms offshore and makes landfall. The PRIMARY FOCUS is the tornado, extreme weather, and civilian evacuation on the coast or in cities. Small civilian boats, yachts, or marina vessels may be visible if a marina environment is explicitly chosen. In city or beach environments, marinas/harbors should NOT be forced. ABSOLUTELY NO vessels other than the assigned small civilian craft.",
        "example_elements": ["offshore waterspout", "waterfront debris", "dark storm clouds", "evacuating civilians", "battered coastal architecture"],
        "camera_styles": ["fixed coastal/marina CCTV", "bystander phone from coastal road", "chase POV from safe inland structure"],
    },
    "urban_city_disasters": {
        "title": "Şehir Merkezi Doğal Afetleri (Urban City Disasters)",
        "guidance": "Severe natural disasters striking deep inside urban city centers, downtown districts, or commercial streets. The setting MUST be an explicit city center (skyscrapers, asphalt roads, city squares, high-rise buildings, urban traffic). DO NOT force a harbor, marina, port, or dock into the scene unless it's a coastal edge. NO ships or vessels are required; focus on the urban destruction, weather anomaly, or flooding.",
        "example_elements": ["flooded city street", "swaying skyscraper", "flying urban debris", "evacuating pedestrians", "submerged cars"],
        "camera_styles": ["fixed traffic intersection CCTV", "bystander phone from an apartment window", "building security camera"],
    },
    "open_beach_coastal_events": {
        "title": "Plaj ve Açık Sahil Olayları (Open Beach & Coastal Events)",
        "guidance": "Extreme weather, tornadoes, or massive waves hitting an open sandy beach, beachfront promenade, or coastal resort. The setting MUST be a natural beach or public coastal shoreline. DO NOT force a marina, harbor, ferry terminal, or port into the scene. NO ships are required; focus on the crashing waves, sweeping winds, and beachfront chaos.",
        "example_elements": ["sweeping storm surge", "beachfront promenade", "abandoned beach chairs", "crashing waves", "coastal road"],
        "camera_styles": ["fixed beach resort CCTV", "bystander phone from beachfront balcony", "boardwalk security camera"],
    }
}


_last_used_domain: str | None = None  # Süreç-içi hafıza — art arda aynı domain seçilmesini engeller

# ─────────────────────────────────────────────────────────────────────────────
# 🎲 ZORUNLU KOMBİNASYON HAVUZLARI (Varyasyon Garantisi & Görsel Dünya)
# ─────────────────────────────────────────────────────────────────────────────

DOMAIN_ATTRIBUTES = {
    "ferry_operations": {
        "ships": ["Passenger Car Ferry", "High-speed Catamaran"],
        "environments": ["Ferry terminal ramp", "Open vehicle deck", "Island crossing route"],
        "events": ["Secured vehicles breaking loose", "Loading ramp hydraulic hinge failure", "Water flooding open vehicle deck"]
    },

    "shipyard_and_drydock_engineering": {
        "ships": ["Luxury Motor Yacht", "Sailing Yacht", "High-speed Catamaran", "Passenger Car Ferry"],
        "environments": ["Shipyard basin", "Drydock interior", "Construction slipway"],
        "events": ["Drydock flooding instability", "Slipway gravitational launch friction", "Keel block settling failure"]
    },
    "marina_and_yacht_operations": {
        "ships": ["Luxury Motor Yacht", "Sailing Yacht", "Runaway Powerboat", "Jet Ski"],
        "environments": ["Floating pontoon dock", "Marina fairway", "Marina fuel dock", "Yacht club entrance"],
        "events": ["Mooring cleat under strain snapping", "Jammed throttle runaway", "Storm surge lifting floating docks", "Wake collision"]
    },
    "cruise_ship_operations": {
        "ships": ["Ocean Cruise Liner", "Mega Cruise Ship", "Cruise Tender Boat"],
        "environments": ["Cruise terminal berth", "Open-air pool deck", "Sun deck"],
        "events": ["Gangway connection stress", "Rogue wave sweeping pool deck", "Bow thruster docking failure", "Wind-blown deck furniture"]
    },
    "coastal_tornado_landfall": {
        "ships": [
            "Luxury Motor Yacht",
            "Sailing Yacht",
            "Runaway Powerboat",
            "Jet Ski"
        ],
        "environments": [
            "Downtown city center",
            "Dense urban downtown",
            "High-rise coastal city",
            "Residential coastal district",
            "Commercial city streets",
            "Open sandy beach",
            "Wide public beach",
            "Beachfront promenade",
            "Coastal resort beach",
            "Empty sandy shoreline",
            "Marina",
            "Harbor Area"
        ],
        "events": [
            "Tornado forming offshore",
            "Tornado approaching coastline",
            "Tornado making landfall",
            "Coastal evacuation",
            "Waterfront disruption",
            "Strong wind and rain",
            "Coastal debris movement",
            "Marina equipment reacting to severe weather"
        ]
    },
    "urban_city_disasters": {
        "ships": [],
        "environments": [
            "Downtown city center",
            "Dense urban downtown",
            "High-rise city district",
            "Commercial city streets",
            "Residential city district",
            "Suburban coastal city"
        ],
        "events": [
            "Severe storm hitting downtown",
            "Flash flooding in city streets",
            "Extreme wind disrupting downtown streets",
            "Falling outdoor objects caused by severe weather",
            "Sudden coastal storm reaching the urban district",
            "Major weather event disrupting city traffic",
            "Heavy rain overwhelming city streets"
        ]
    },
    "open_beach_coastal_events": {
        "ships": [],
        "environments": [
            "Open sandy beach",
            "Wide public beach",
            "Beachfront promenade",
            "Coastal resort beach",
            "Empty sandy shoreline",
            "Beach parking area",
            "Open coastal road beside beach"
        ],
        "events": [
            "Tornado approaching an open beach",
            "Sudden extreme storm hitting the beach",
            "Powerful coastal wind sweeping across the shoreline",
            "Large waves reaching the beach",
            "Severe storm disrupting a beachfront area",
            "Beach evacuation during extreme weather",
            "Coastal flooding reaching the beachfront"
        ]
    }
}

# Gemiyle fiziksel olarak uyuşmayan ortam/olaylar (TUR 10): tender botta havuz/güneş güvertesi
# ve şezlong yok (dry-run 2 #3: "cruise tender boat's pool deck" + 15 yolcu).
SHIP_INCOMPATIBLE = {
    "Cruise Tender Boat": {
        "environments": {"Open-air pool deck", "Sun deck"},
        "events": {"Rogue wave sweeping pool deck", "Wind-blown deck furniture"},
        "scenario_terms": r"\bpool\s*deck|\bsun\s*deck|\bswimming\s+pool|\bloungers?\b|\bsun\s*beds?\b",
    },
}

# Gemisi opsiyonel domainler (TUR 11): gemi sadece bu ortamlarda atanır, diğer ortamlarda
# (şehir/plaj) gemi None olur ve gemi gerektiren olaylar havuzdan çıkar. Önce ortam seçilir.
VESSEL_ENVIRONMENTS = {
    "coastal_tornado_landfall": {
        "environments": {"Marina", "Harbor Area"},
        "vessel_only_events": {"Marina equipment reacting to severe weather"},
    },
}

# Import anında kontrol: yazım hatası filtreyi sessizce boşa düşürmesin.
for _d, _v in VESSEL_ENVIRONMENTS.items():
    _bad = (_v["environments"] - set(DOMAIN_ATTRIBUTES[_d]["environments"])) | (
        _v["vessel_only_events"] - set(DOMAIN_ATTRIBUTES[_d]["events"]))
    if _bad or not DOMAIN_ATTRIBUTES[_d]["ships"]:
        raise RuntimeError(f"VESSEL_ENVIRONMENTS[{_d}] havuzla uyuşmuyor: {sorted(_bad)}")

# GPT'ye gösterilen gemi evreni: domain havuzlarından otomatik türer, elle liste tutulmaz.
VESSEL_UNIVERSE = sorted({s for a in DOMAIN_ATTRIBUTES.values() for s in a["ships"]})

# Kie'ye giden prompt'ta atanan geminin adı geçmeli (2026-09-24, TUR 8): "the vessel"
# yazılınca Seedance belirsizi kargo gemisi olarak çiziyordu. Gemi → kabul edilen ad kalıbı.
SHIP_NAME_PATTERNS = {
    "Passenger Car Ferry": r"\bferr(?:y|ies)\b",
    "High-speed Catamaran": r"\bcatamarans?\b",
    "Luxury Motor Yacht": r"\byachts?\b",
    "Sailing Yacht": r"\b(?:yachts?|sailboats?)\b",
    "Runaway Powerboat": r"\b(?:power|speed)boats?\b",
    "Jet Ski": r"\bjet[- ]?skis?\b",
    "Ocean Cruise Liner": r"\bcruise (?:ship|liner)s?\b|\bliners?\b",
    "Mega Cruise Ship": r"\bcruise (?:ship|liner)s?\b|\bliners?\b",
    "Cruise Tender Boat": r"\btenders?\b",
}

# Import anında kontrol: evrene eklenen gemi ad kalıbı olmadan sessizce kapıdan kaçmasın.
_missing_names = set(VESSEL_UNIVERSE) - set(SHIP_NAME_PATTERNS)
if _missing_names:
    raise RuntimeError(f"SHIP_NAME_PATTERNS eksik: {sorted(_missing_names)}")


def get_creative_catalyst(recent_history: list[str] | None = None) -> dict:
    """
    Geniş denizcilik ilham alanlarından birini seçer ve GPT-4o için bağlam üretir.
    Geçmişteki seçimlere bakarak Visual World (Domain), Gemi Tipi, Event ve Environment tekrarlarını
    strict rotasyonla engeller (LRU).
    """
    if recent_history is None:
        recent_history = []
        
    recent_domains = []
    recent_ships = []
    recent_events = []
    recent_envs = []
    
    # recent_history içinde combo_key'ler bulunabilir: "domain|ship|event|env|camera".
    # Sadece bugünkü evrene ait 5 parçalı combo'lar sayılır; '|' içeren Konu metinleri
    # (örn. elle yazılmış TEST kaydı) rotasyon slotu işgal etmesin (2026-09-24).
    for item in recent_history:
        parts = item.split('|')
        if is_current_universe_combo(item):
            recent_domains.append(parts[0].lower().strip())
            recent_ships.append(parts[1].lower().strip())
            recent_events.append(parts[2].lower().strip())
            recent_envs.append(parts[3].lower().strip())
            
    all_domains = list(MARITIME_INSPIRATION_DOMAINS.keys())
    
    # Visual World (Domain) için Katı Rotasyon (İlk 7'de 7 farklı):
    # En fazla N-1 önceki kullanımları hariç tutarız. 
    # Örneğin 7 domain varsa, son 6 domain'i dışlarsak geriye tam olarak kullanılmamış 1 tane kalır.
    exclude_count = max(1, len(all_domains) - 1)
    recently_used_domains = recent_domains[-exclude_count:] if recent_domains else []
    available_domains = [d for d in all_domains if d.lower() not in recently_used_domains]
    
    if available_domains:
        chosen_domain_key = random.choice(available_domains)
    else:
        # Fallback (asla buraya düşmemeli ama güvenlik için):
        # Eğer bir şekilde havuz daralırsa en eski kullanılanı seçmeye çalış.
        fallback_domains = [d for d in all_domains if d.lower() not in recent_domains[-1:]]
        chosen_domain_key = random.choice(fallback_domains) if fallback_domains else random.choice(all_domains)

    domain_data = MARITIME_INSPIRATION_DOMAINS[chosen_domain_key]
    attrs = DOMAIN_ATTRIBUTES.get(chosen_domain_key)
    
    # Yardımcı LRU Seçici Fonksiyon
    def _choose_lru(options: list[str], history: list[str]) -> str | None:
        if not options:
            return None
            
        # Önce hiç kullanılmamış olanları bul
        unused = [o for o in options if o.lower() not in history]
        if unused:
            return random.choice(unused)
        
        # Hepsi kullanıldıysa, en az yakın zamanda kullanılanı (en eski) bul
        history_lower = [h.lower() for h in history]
        options_lower = [o.lower() for o in options]
        
        last_seen = {}
        for opt in options_lower:
            try:
                rev_idx = history_lower[::-1].index(opt)
                last_seen[opt] = len(history_lower) - 1 - rev_idx
            except ValueError:
                last_seen[opt] = -1
                
        oldest_opt = min(last_seen, key=last_seen.get)
        
        for o in options:
            if o.lower() == oldest_opt:
                return o
        return random.choice(options)

    # Gemi, Olay ve Ortam Seçimi (Kendi içlerinde tekrarı minimize eder)
    vessel_envs = VESSEL_ENVIRONMENTS.get(chosen_domain_key)
    if vessel_envs:
        # Gemisi opsiyonel domain (TUR 11): önce ortam; şehir/plaj ortamında gemi yok
        chosen_env = _choose_lru(attrs.get("environments", []), recent_envs)
        if chosen_env in vessel_envs["environments"]:
            chosen_ship = _choose_lru(attrs.get("ships", []), recent_ships)
            events = attrs.get("events", [])
        else:
            chosen_ship = None
            events = [e for e in attrs.get("events", []) if e not in vessel_envs["vessel_only_events"]]
        chosen_event = _choose_lru(events, recent_events)
    else:
        chosen_ship = _choose_lru(attrs.get("ships", []), recent_ships)
        banned = SHIP_INCOMPATIBLE.get(chosen_ship or "", {})
        events = [e for e in attrs.get("events", []) if e not in banned.get("events", set())]
        envs = [e for e in attrs.get("environments", []) if e not in banned.get("environments", set())]
        if attrs.get("events") and not events or attrs.get("environments") and not envs:
            raise RuntimeError(f"SHIP_INCOMPATIBLE '{chosen_ship}' için {chosen_domain_key} havuzunda seçenek bırakmadı")
        chosen_event = _choose_lru(events, recent_events)
        chosen_env = _choose_lru(envs, recent_envs)

    # Mevcut fikir kütüphanesinden örnekleri derle
    library_samples = []
    for cat_key, cat_data in DEEPMYSTER_EXISTING_IDEAS_LIBRARY.items():
        sample = random.choice(cat_data["reference_scenarios"])
        library_samples.append(f"[{cat_data['title']}]: {sample}")

    catalyst = {
        "domain_id": chosen_domain_key,
        "domain_title": domain_data["title"],
        "guidance": domain_data["guidance"],
        "example_elements": domain_data["example_elements"],
        "camera_styles": domain_data["camera_styles"],
        "existing_library_reference": library_samples,
        "recent_history": recent_history[-20:],
        "forced_ship": chosen_ship or "None",
        "forced_event": chosen_event,
        "forced_environment": chosen_env,
    }

    log.info(f"🎲 Görsel Dünya Seçildi: [{chosen_domain_key}] {domain_data['title']}")
    return catalyst


# ─────────────────────────────────────────────────────────────────────────────
# 🤖 KATMAN 2: GPT SENARYO YÖNETMENİ — System Prompt
# ─────────────────────────────────────────────────────────────────────────────

SCENARIO_WRITER_SYSTEM_TEMPLATE = """You are the master director and physical maritime incident specialist for "DeepMyster" — capturing authentic, high-tension, real-world nautical incidents as if filmed by real observers: a fixed security camera, a bystander's handheld phone, or a POV camera from a nearby vessel.

## CORE DIRECTIVE:
You have FULL CREATIVE AUTONOMY to invent a unique, realistic <<DURATION>>-second physical maritime incident.
The footage MUST be 100% understandable on a SILENT SCREEN.

## CAMERA — EXACT POSITION REQUIRED (NON-NEGOTIABLE):
The user prompt assigns ONE of three exact camera positions for this scene. Write the "observer_camera" field and the scene itself to match EXACTLY:
- Eye-level handheld phone footage filmed by a bystander standing on a dock or pier at the water's edge.
- A fixed security camera mounted on the vessel's own wall/superstructure — completely static, no observer present in the scene. For onboard deck, pool, or vehicle-deck scenes, this camera may be mounted ON the ship looking at its own interior spaces — visible deck architecture, railings, or vehicle-deck structure establishes the ship without needing an exterior hull/bow shot.
- POV footage from the deck or bow of another nearby vessel, close to the action, with that observer vessel's own rail/bow visible in the foreground.
NEVER describe a generic "wide shot," an unspecified establishing shot, or an ambiguous vantage point — commit to exactly one of the three positions above, stated concretely (e.g. "fixed camera bolted to the cruise ship's port-side superstructure," not "a camera shows the ship"). NEVER use fisheye/GoPro-style distortion or drone/aerial framing.

## VARIETY — ROTATE WORLDS (NON-NEGOTIABLE):
Every scenario must come from a genuinely different world than recent productions. Rotate through these varied settings:
1. Cruise ships with civilian passengers aboard
2. Ferries and high-speed catamarans carrying vehicles and passengers
3. Marinas with yachts, powerboats, and jet skis
4. Shipyard slipway launches
5. Coastal tornadoes, open beaches, and urban storm disasters
Never repeat the setting used in the RECENT PRODUCTION HISTORY list below, and never let two consecutive scenarios feel like the same world even if surface details (ship name, incident mechanism) differ — two different ferry vehicle-deck scenes back to back still count as a repeat.

## EXISTING IDEAS LIBRARY & BRAND UNIVERSE (INSPIRATION & ANTI-REPETITION):
You are provided with samples from DeepMyster's 71-topic reference library.
- THESE SAMPLES DEFINE OUR BRAND'S HIGH-TENSION REALISTIC MARITIME REALITY.
- DO NOT copy or mechanically rehash these exact scenarios by merely swapping ship names or minor nouns.
- INSTEAD: Use them as an inspiration springboard to understand our universe and EXTRAPOLATE completely novel, authentic physical incidents that expand the channel's horizons.

## RECENT PRODUCTION HISTORY (STRICT DO NOT REPEAT):
Review the recent topics list provided in the user prompt. DO NOT repeat the exact same vessel type, incident mechanism, setting, or world from recent productions.

## STORY & PHYSICAL REALITY STANDARDS:
1. PURE PHYSICAL DRAMA: Grounded in real physics, gravity, friction, weather, or mechanical loads. The crisis MUST be visible in front of the camera.
2. <<CAST_RULE>>
3. THREE-BEAT STRUCTURE, ALL WITHIN <<DURATION>> SECONDS, ONE CONTINUOUS SHOT:
   - BEAT 1 — DANGER ALREADY MOVING (well under 1 second): A near-instantaneous visual anchor where the trigger is already happening.
   - BEAT 2 — ACTION (<<EARLY>>-<<LATE>>s): The sudden physical wrong turn. MUST USE EXPLICIT KINETIC VERBS (e.g., crashes, snaps, rolls, flips, slams, sweeps, falls). DO NOT use static verbs like "is leaning", "nearing".
   - BEAT 3 — CONSEQUENCE (<<LATE>>-<<DURATION>>s): The immediate, visible physical danger, still actively unfolding at <<DURATION>>s.
4. KINETIC MOMENTUM: The viewer must see a visible physical event unfolding dynamically.
5. CONCRETE PHYSICAL OUTCOME: The <<DURATION>>th second must show the beat 3 danger still visibly in progress.
6. NO FORCED MARITIME ASSETS: If `vessel_class` is "None" (in ANY domain, including Coastal Tornado in a city or beach setting), DO NOT create ships, boats, or docks. Keep it strictly urban or strictly beach. If `vessel_class` is provided, stick to that exact ship. NEVER spawn any additional vessel beyond the given vessel_class (no rescue boats, no escort boats). Always call the vessel by its assigned type (e.g. 'the sailing yacht', 'the passenger car ferry') in visible_start and every later beat; never refer to it only as 'the vessel', 'the ship' or 'the boat'.
7. BEAT 1 MUST SHOW DANGER ALREADY IN MOTION (NON-NEGOTIABLE): visible_start must contain a physical action verb happening right now (e.g. crashes, slams, snaps, surges, swings, tilts). FORBIDDEN patterns in visible_start: 'is visible', 'visible from', the phrase 'as [X] approaches' (e.g. 'as the ferry approaches the pier'), 'scene opens', 'observing as', 'bustling', 'looming', 'signals for'. The grammatical subject of visible_start's first sentence must be the physical thing in danger or the people in the scene (e.g. 'A mooring line snaps…', 'Waves crash…'); camera position and framing belong only in observer_camera, never in visible_start. Instead, describe the crisis as it happens or immediately after it starts. Beat 1 is the TRIGGER starting (wave hits, line snaps, blocks give way); beat 3 is the RESULT. Starting with the trigger is required; starting with the result is still forbidden. visible_start pairs the trigger action with a visible physical effect on another object (spray, snapping lines, sliding objects, splintering blocks); human emotional reactions (startled, alarmed, shocked, panicked) belong in physical_movement, never in visible_start. Give the moving object ONE direction relative to the camera (across the frame, away from the camera, or toward the camera) and keep that same direction in every beat.

## OUTPUT FORMAT (STRICT JSON):
All field values are plain descriptive prose. Never start a value with a label or timestamp such as "BEAT 1:" or "(0-4s)".
{
  "vessel_class": "Specific real-world vessel class (or 'None' if the prompt specifies it's a gemisiz sahne/şehir/plaj)",
  "incident_type": "Short 3-5 word label of the physical crisis",
  "scenario_summary": "One clear, punchy sentence covering only what the three beats show: the opening action, what goes wrong, and the visible consequence. It must not introduce any person, vessel, or object that is not in visible_start, physical_movement, or visible_consequence",
  "visible_start": "<<VISIBLE_START_DESC>>",
  "beat1_action_verb": "The single main physical action verb of visible_start's first sentence, copied exactly as written there (e.g. 'gushes', 'spins', 'lifts'). It must be what the hazard does, not what people or the camera do.",
  "physical_movement": "<<PHYSICAL_MOVEMENT_DESC>>",
  "visible_consequence": "<<VISIBLE_CONSEQUENCE_DESC>>",
  "observer_camera": "The exact assigned camera position, stated concretely (e.g. 'fixed camera bolted to the cruise ship's port-side superstructure', 'bystander's handheld phone from the pier', 'POV from the bow of the second vessel already established in this scene')",
  "silent_screen_understandable": true
}"""


def compute_duration_breakpoints(duration: int) -> tuple[int, int]:
    """Sahneyi 3 aşamaya böler: başlangıç / eskalasyon / sonuç.
    12s için 0-3 / 3-9 / 12 üretir — orijinal sabit değerlerle birebir eşleşir."""
    early = max(2, round(duration * 0.25))
    late = max(early + 1, min(duration - 1, round(duration * 0.75)))
    return early, late


def build_scenario_writer_system(duration: int, domain_id: str = "") -> str:
    """SCENARIO_WRITER_SYSTEM'i config.DEFAULT_DURATION'a göre üretir."""
    early, late = compute_duration_breakpoints(duration)
    
    if domain_id in ENV_CENTRIC_DOMAINS:
        cast_rule = "ENVIRONMENT-CENTRIC (CAST OPTIONAL): Focus the entire scene and camera strictly on the MASSIVE NATURAL EVENT (e.g. tornado, waterspout, giant wave, flood). Do NOT focus on specific fleeing humans. Humans/cars should only be background scale references. The natural event must be the primary visual anchor and must remain fully in frame. Do not let the event get pushed out of the camera's view."
        vis_start = "A near-instantaneous establishing flash (well under 1 second) showing the massive natural event already in violent motion (e.g. a tornado tearing across the shoreline, a rogue wave crashing onto the beach). DO NOT start by describing people (e.g. 'Two pedestrians'). The natural event must be the primary visual anchor. Do NOT start with the consequence already happening."
        phys_mov = "The sudden physical wrong turn — STRONG VISIBLE PHYSICAL ACTION of the natural event (e.g., sweeps, crashes, rips, floods, slams). The physical movement of the disaster must be explicit and extreme."
        vis_cons = "The immediate dangerous consequence of the natural disaster, still visibly unfolding at <<DURATION>>s, not resolved or safe. Never end with the danger settling, stopping, calming, or being resolved, and never end on people just watching; end mid-action (e.g. 'still surging', 'continues to slide')."
    elif domain_id in DOMAIN_CAST_RANGES:
        lo, hi = DOMAIN_CAST_RANGES[domain_id]
        cast_rule = (
            f"CAST SIZE: Show approximately {lo}-{hi} people in the "
            f"scene, matching realistic crew/passenger count for this "
            f"environment. Do not exceed {hi}. All people count "
            f"consistently across visible_start, physical_movement, "
            f"and visible_consequence — same exact count in all "
            f"three beats."
        )
        vis_start = "A near-instantaneous establishing flash (well under 1 second) showing the people with the danger already in motion, immediately giving way to beat 2 — the danger must be understood within the first 2 seconds of the shot overall, not a calm moment. State the head count once here as a specific number or a close estimate (e.g. 'three deckhands', 'about twenty passengers') — never a vague term like 'crew members' with no number — and keep that same count in all three beats. Do NOT start with the consequence already happening."
        phys_mov = "The sudden physical wrong turn — STRONG VISIBLE PHYSICAL ACTION (e.g., swings, veers, slides, surges, rolls, pitches, slams). Do NOT use passive words like 'approaches' or 'is in danger'. The physical movement must be explicit and extreme. Same people, same exact count as visible_start."
        vis_cons = "The immediate dangerous consequence, still visibly unfolding at <<DURATION>>s, not resolved or safe. Same people, same exact count as visible_start. Never end with the danger settling, stopping, calming, or being resolved, and never end on people just watching; end mid-action (e.g. 'still surging', 'continues to slide')."
    else:
        raise RuntimeError(
            f"Unknown domain_id '{domain_id}' — DOMAIN_CAST_RANGES "
            f"missing entry. Config bug, do not silently pass."
        )

    # Önce alan açıklamaları eklenir, sonra süreler: açıklamaların içindeki
    # <<DURATION>> gibi placeholder'lar da çözülsün (aksi halde GPT'ye ham gidiyordu).
    return (
        SCENARIO_WRITER_SYSTEM_TEMPLATE
        .replace("<<CAST_RULE>>", cast_rule)
        .replace("<<VISIBLE_START_DESC>>", vis_start)
        .replace("<<PHYSICAL_MOVEMENT_DESC>>", phys_mov)
        .replace("<<VISIBLE_CONSEQUENCE_DESC>>", vis_cons)
        .replace("<<DURATION>>", str(duration))
        .replace("<<EARLY>>", str(early))
        .replace("<<LATE>>", str(late))
    )


# ─────────────────────────────────────────────────────────────────────────────
# ✂️ KATMAN 3: PROMPT SİMPLİFİYER (SEEDANCE 2 MINI)
# ─────────────────────────────────────────────────────────────────────────────

PROMPT_SIMPLIFIER_SYSTEM_TEMPLATE = """You are a Seedance 2 Mini prompt engineer for DeepMyster documentary maritime videos.
Your ONE job: Convert the maritime scenario into a HIGH-SIGNAL, PHOTOREALISTIC prompt following the <<DURATION>>-second single-take standard.

## DOĞUKAN METODOLOJİSİ ("Less is More"):
- Seedance 2 Mini needs clear, high-signal, descriptive visual language without cinematic fluff or robotic checklists.
- Single continuous <<DURATION>>-second take from the assigned realistic camera perspective (fixed CCTV, bystander handheld, or chase POV).
- Raw, authentic lighting (overcast daylight, storm lighting, industrial port lights).

## STRICT RULES:
1. NO TIMESTAMPS / NO HEADERS: No 'Shot 1', '(0-<<DURATION>>s)', 'Scene 1'.
2. NO CAMERA/LIGHTING TAGS: Do NOT end the prompt with a camera or lighting description (e.g. no 'Fixed CCTV camera, raw overcast footage.'). Camera and lighting are appended automatically afterward — focus entirely on the physical scene, action, and outcome.
3. PRESERVE REALISM DETAILS: Keep authentic PPE colors for crew (orange/red/yellow gear, wetsuits, coveralls — never white hazmat suits) and ordinary civilian clothing for passengers/guests/drivers (never hi-vis PPE on civilians), and raw natural weather exactly as described in the scenario. Do not sanitize, glamorize, or make water/ice/lighting look glossy or CGI-clean.
4. STRICT CHRONOLOGICAL FLOW: You MUST maintain the exact timeline: 1) Initial state, 2) STRONG VISIBLE PHYSICAL MOVEMENT (e.g. swings, veers, slams, pitches), 3) Final consequence. NEVER start the prompt with the vessel already damaged or the consequence already happening. Action must be active and visible, not passive (like 'is in danger').
5. NO HALLUCINATION / STRICT INVENTORY: Do NOT add any new vessels, characters, objects, or dramatic elements (e.g. 'escort boat', 'officer', 'dust', 'debris') that are not explicitly present in the provided scenario. Preserve the exact Vessel Class and Environment, and name the vessel by its type (e.g. 'the sailing yacht', 'the cruise liner') — never only 'the vessel', 'the ship' or 'the boat'; a prompt that does not name the vessel type is rejected. Focus ONLY on a single main action chain.
6. PRESERVE PHENOMENA NAMES: DO NOT sanitize or dilute the specific names of massive environmental phenomena. If the scenario mentions a 'tornado', 'waterspout', 'tsunami', or 'rogue wave', YOU MUST USE THAT EXACT WORD in the prompt. Do not replace it with generic terms like 'fierce winds' or 'storm'. The natural disaster must remain the primary visual subject.
7. NUMBER FIDELITY: If the scenario specifies a count ('Two deckhands', 'One bystander', 'Three crew'), preserve that EXACT count. If the scenario is vague (just 'crew' or 'passengers'), keep it vague — do NOT invent specific numbers. NEVER downgrade a specific count to a vague plural.
8. BEAT 3 CONTINUATION FIDELITY: If the scenario's visible_consequence includes ongoing-danger markers ('still', 'continues', 'keeps', 'continuing'), the simplified prompt MUST preserve at least one of these markers or end with an ongoing action verb (e.g. 'surging', 'sweeps', 'keeps sliding'). NEVER simplify the final sentence to a static state.
   GOOD: 'Floodwaters continue to push inland, debris swirling in the current'
   GOOD: 'Water is still surging across the deck, sweeping cars sideways'
   BAD: 'Floodwaters cover the street' (static, action stopped)
   BAD: 'Cars are damaged' (past tense, action resolved)
9. BEAT 1 SUBJECT FIDELITY: The FIRST sentence of the prompt MUST keep the same grammatical subject as the scenario's visible_start. If the scenario says 'water gushes' or 'a tornado spins', the prompt starts with that subject-action pair — NOT with spectators watching it. The action verb of visible_start MUST be the active predicate of the first sentence, not a subordinate clause introduced by 'watch', 'see', 'observe', 'react'.
   GOOD: 'Water gushes from beneath the vessel's hull as workers scramble clear'
   GOOD: 'A tornado spins ferociously offshore, tearing debris skyward'
   BAD: 'Three workers watch in shock as water gushes'
   BAD: 'Passengers react as a tornado spins offshore'
   BAD: 'The scene shows water gushing while workers stand by'
   The first sentence pairs the opening action with what it physically does to another object (spray bursting, blocks splintering, cars sweeping sideways). Never put human emotional reactions (startled, alarmed, shocked, panicked) in the first sentence; people's reactions come later. Keep ONE movement direction for the moving object throughout the prompt.
   GOOD: 'The sailing yacht lurches down the slipway, keel blocks splintering beneath the hull'
   BAD: 'The sailing yacht lurches forward, startling three workers'

## OUTPUT FORMAT (STRICT JSON):
{
  "prompt": "The exact generated prompt",
  "word_count": 33
}"""


def build_prompt_simplifier_system(duration: int, domain_id: str = "") -> str:
    """PROMPT_SIMPLIFIER_SYSTEM'i config.DEFAULT_DURATION'a göre üretir."""
    sys_prompt = PROMPT_SIMPLIFIER_SYSTEM_TEMPLATE.replace("<<DURATION>>", str(duration))
    if domain_id in ENV_CENTRIC_DOMAINS:
        sys_prompt += "\n\n10. STRICT ENVIRONMENT-CENTRIC FOCUS: DO NOT START THE PROMPT WITH HUMANS (e.g. 'Two pedestrians...'). Begin immediately with the massive natural disaster (e.g. 'A massive coastal tornado...', 'A giant rogue wave...'). If humans are present, they are secondary background elements. DO NOT DILUTE THE PHENOMENON (keep exact words like 'tornado', 'waterspout', 'tsunami', 'storm surge')."
    return sys_prompt


# ─────────────────────────────────────────────────────────────────────────────
# 🎥 KAMERA ARKETİPLERİ — Impact Seacam referans analizi (Fixed CCTV + Handheld + Chase POV)
# ─────────────────────────────────────────────────────────────────────────────
# Python HER üretimde bu 3 arketipten birini seçer (ağırlıklı rastgele — CCTV en
# sık/varsayılan). Seçim hem GPT'ye (senaryo aşaması) hem de deterministik stil
# kilidine aktarılır — ikisi arasında çelişki olmaması için TEK kaynak.

_LENS_GUARDRAILS = (
    "normal-to-moderate-wide lens, no fisheye/action-cam distortion, "
    "no drone/aerial framing"
)

_STATIC_POSITION_GUARDRAIL = (
    "the camera's position and distance from the subject must stay exactly "
    "constant for the entire shot — no zooming in, no drifting closer, no "
    "changing vantage point"
)

_SINGLE_MOMENT_GUARDRAIL = (
    "Single unbroken moment only: the camera captures ONE continuous instant "
    "of the incident unfolding, no time skips, no scene cuts, no camera "
    "repositioning mid-shot. The action must flow as one seamless real-time "
    "sequence from first to last frame."
)

def get_realism_guardrails(domain_id: str, vessel_class: str) -> str:
    """Seçilen Visual World ve Ship Class'a göre spesifik gerçekçilik kuralları üretir."""
    domain_id = (domain_id or "").lower()
    vessel_class = (vessel_class or "").lower()
    
    # Kıyafet domain'e göre değil ROLE göre (2026-09-24): eski "cruise/ferry staff
    # wear proper uniforms" kuralı senaryodaki turuncu tulumlu deckhand'lerle çelişiyordu.
    role_rules = (
        "Clothing follows each person's role: deckhands, dockworkers, and technicians wear "
        "high-visibility orange or yellow PPE coveralls; officers and captains wear proper "
        "uniforms (ferry officer uniform, white cruise officer uniform); passengers, guests, "
        "and bystanders wear ordinary civilian clothing appropriate to the setting (swimwear, "
        "resort or casual wear, sun hats for pool/deck scenes; regular casual clothing for "
        "car-deck scenes) — never hi-vis PPE on civilians."
    )

    common_rules = (
        "NEVER use white hazmat suits. Raw natural overcast/fog/rain lighting, "
        "not glossy or artificially perfect water or ice."
    )

    return " ".join([role_rules, common_rules])


# Bu domainlerde forced_ship=None olabilir (doğal afet/olay odaklı, gemi zorunlu değil).
# chase_pov iki ayrı gemi zorunlu kıldığı için buralarda seçilmemeli — aksi halde GPT
# ikinci gemiyi karşılamak için yoktan bir tekne icat ediyordu (2026-09-23 tespit edildi).
ENV_CENTRIC_DOMAINS = ["coastal_tornado_landfall", "urban_city_disasters", "open_beach_coastal_events"]

# Gemi domainlerinde ekrandaki gerçekçi kişi aralığı (2026-09-24). "Max 2" sadece
# kargo gemileri içindi; kargo domain'i artık yok. Env-centric domainler tabloya
# girmez, kendi ENVIRONMENT-CENTRIC cast kuralını alır.
DOMAIN_CAST_RANGES = {
    "ferry_operations": (2, 5),
    "shipyard_and_drydock_engineering": (2, 5),
    "marina_and_yacht_operations": (3, 6),
    "cruise_ship_operations": (8, 25),
}

# Import anında kontrol: eksik domain üretim ortasında değil, başlangıçta patlasın.
_missing_cast = set(MARITIME_INSPIRATION_DOMAINS) - set(DOMAIN_CAST_RANGES) - set(ENV_CENTRIC_DOMAINS)
if _missing_cast:
    raise RuntimeError(f"DOMAIN_CAST_RANGES eksik: {sorted(_missing_cast)}")


def is_current_universe_combo(combo_key: str) -> bool:
    """Combo Key bugünkü evrene mi ait: 5 parça, domain 7'de, gemi VESSEL_UNIVERSE'te veya 'none'.
    Eski evren kayıtları (kargo, tug, trawler, LNG...) Notion tarihçesinden yazıcıya sızmasın diye (2026-09-24)."""
    parts = [p.strip().lower() for p in (combo_key or "").split("|")]
    if len(parts) != 5:
        return False
    domain, ship = parts[0], parts[1]
    return domain in MARITIME_INSPIRATION_DOMAINS and (
        ship == "none" or ship in {v.lower() for v in VESSEL_UNIVERSE}
    )


CAMERA_ARCHETYPES = {
    "fixed_cctv": {
        "title": "Sabit Güvenlik/CCTV Kamerası",
        "weight": 2,
        "gpt_guidance": (
            "Fixed-mount security/CCTV camera — dockside, marina, pool deck, ship "
            "superstructure, or ONBOARD deck/interior mounted (looking at the "
            "ship's own pool deck, sun deck, or vehicle deck rather than the ship "
            "from outside). Completely static, unmoving frame, no observer present "
            "in the scene."
        ),
        "style_lock": (
            f"Static fixed-mount security CCTV camera, {_LENS_GUARDRAILS}. Slight "
            "natural motion blur, no cinematic framing, no artistic close-ups, no "
            f"camera movement. {_SINGLE_MOMENT_GUARDRAIL}"
        ),
        # Gemiye özgü kadraj kuralı — ENV_CENTRIC domainlerde eklenmez (apply_style_lock)
        "vessel_framing": (
            "When filming the vessel from outside/alongside, "
            "frame must keep the hull, bow, or superstructure visible to establish "
            "ship type — no tight shot confined only to deck machinery. For "
            "onboard deck, pool, or vehicle-deck scenes filmed from a camera "
            "mounted ON the ship (looking at its own interior spaces, not the ship "
            "from outside), visible deck architecture, railings, superstructure, "
            "or vehicle-deck structure satisfies this instead — e.g. a pool-deck "
            "camera showing loungers, railings, and open sky is sufficient; do not "
            "force an exterior hull/bow shot into an onboard scene."
        ),
    },
    "bystander_handheld": {
        "title": "Yolcu/İzleyici Elde Telefon Görüntüsü",
        "weight": 1,
        "gpt_guidance": (
            "Bystander or passenger handheld phone footage — filmed by a real "
            "onlooker from a ship's railing, an adjacent vessel, or a dock, watching "
            "the incident unfold nearby. If a railing, window, or other foreground "
            "boundary element is visible at the start, it must remain visible and "
            "in the same position for the entire shot — the person filming does "
            "not move, lean past it, or climb over it."
        ),
        # Env-centric domainlerde (şehir/plaj/hortum) gemi küpeştesi yok (TUR 10)
        "gpt_guidance_env": (
            "Bystander handheld phone footage — filmed by a real onlooker on land "
            "(balcony, window, rooftop, roadside, or waterfront), watching the "
            "incident unfold nearby. If a railing, window, or other foreground "
            "boundary element is visible at the start, it must remain visible and "
            "in the same position for the entire shot — the person filming does "
            "not move, lean past it, or climb over it."
        ),
        "style_lock": (
            f"Bystander handheld phone footage, {_LENS_GUARDRAILS}. Natural minor "
            "handheld shake means only small in-place tremor and wobble of the "
            f"hands — {_STATIC_POSITION_GUARDRAIL}. The framing established in "
            "the very first moment of the shot — same subject distance, same "
            "field of view — must be held completely unchanged for the full "
            "duration: NO progressive zoom, NO push-in, NO gradual creep closer, "
            "even a slow one. If the shot is filmed through, over, or behind a "
            "railing, window, porthole, or other foreground boundary element, "
            "that element MUST stay visible in frame for the entire shot — the "
            "camera must never appear to pass through it, climb over it, or move "
            f"beyond it. {_SINGLE_MOMENT_GUARDRAIL}"
        ),
        # Çekim yeri domain'e göre (apply_style_lock): env-centric'te gemi küpeştesi yok (TUR 10)
        "vantage": (
            "Filmed from a ship's railing, nearby vessel, or dock, occasionally "
            "showing a hint of a railing, hand, or phone edge at the frame border."
        ),
        "vantage_env": (
            "Filmed by an onlooker on land (balcony, window, rooftop, roadside, or "
            "waterfront), occasionally showing a hint of a window frame, hand, or "
            "phone edge at the frame border."
        ),
        # Gemiye özgü kadraj kuralı — ENV_CENTRIC domainlerde eklenmez (apply_style_lock)
        "vessel_framing": (
            "The vessel in crisis must be fully and clearly "
            "visible in frame at all times, not just a cropped detail."
        ),
    },
    "chase_pov": {
        "title": "Takip/Kovalama POV (Yakındaki Tekneden)",
        "weight": 1,
        "gpt_guidance": (
            "Chase or pursuit point-of-view filmed from the deck or bow of a "
            "nearby observer vessel — e.g. an escort boat, a nearby yacht, or a "
            "following ferry. TWO distinct vessels are mandatory: the observer "
            "vessel the camera is mounted on (its bow/rail may appear in the "
            "foreground), and a second, clearly separate vessel actively in "
            "crisis that stays visible throughout the shot. This is NOT a "
            "single-vessel storm scene — if a two-vessel setup does not fit "
            "naturally, choose a different incident within the same domain "
            "instead of defaulting to one vessel alone."
        ),
        "style_lock": (
            "Chase POV filmed from the deck or bow of a nearby pursuing vessel, "
            f"close to the action, {_LENS_GUARDRAILS}. Natural handheld boat "
            f"motion means only small in-place tremor and wobble from sea swell — "
            f"{_STATIC_POSITION_GUARDRAIL}. No cinematic framing, no artistic "
            "close-ups. Two distinct vessels must be visible throughout: the "
            "observer's own vessel and a clearly separate second vessel "
            f"actively in crisis, fully visible, not just a cropped detail. {_SINGLE_MOMENT_GUARDRAIL}"
        ),
    },
}

# Geriye dönük uyumluluk — bazı test scriptleri tek bir STYLE_LOCK_SUFFIX bekliyor.
# Varsayılan (en sık seçilen) arketipin son ekini temsil eder (gemili sahne hali).
STYLE_LOCK_SUFFIX = (
    f'{CAMERA_ARCHETYPES["fixed_cctv"]["style_lock"]} {CAMERA_ARCHETYPES["fixed_cctv"]["vessel_framing"]}'
)


def choose_camera_archetype(domain_id: str = "") -> str:
    """3 kamera arketipinden birini ağırlıklı rastgele seçer (CCTV varsayılan/en sık).

    Environment-centric domainlerde (gemi yok, forced_ship=None) chase_pov elenir:
    o arketip iki ayrı gemi zorunlu kılar, gemisiz domainde GPT bunu karşılamak
    için yoktan bir tekne icat ediyordu (2026-09-23 tespit edildi).
    """
    keys = list(CAMERA_ARCHETYPES.keys())
    if domain_id in ENV_CENTRIC_DOMAINS:
        keys = [k for k in keys if k != "chase_pov"]
    weights = [CAMERA_ARCHETYPES[k]["weight"] for k in keys]
    return random.choices(keys, weights=weights, k=1)[0]


# Seedance iki test videosunda da ilk 3-4 sn yavaş/durgun açıldı (2026-09-24 TUR 9); tüm arketiplere eklenir.
_MOTION_START_GUARDRAIL = (
    "Motion is already under way in the very first frame: the danger is visibly moving "
    "from frame one, no calm or static opening."
)


def join_story_and_style(story: str, style_suffix: str) -> str:
    """Hikaye + sabit stil eki → Kie'ye giden nihai prompt."""
    return f"{(story or '').strip().rstrip('.')}. {style_suffix}"


def style_lock_suffix(camera_archetype: str = "fixed_cctv", catalyst: dict = None) -> str:
    """Hikayeden bağımsız sabit stil eki (kamera + gerçekçilik). Kie retry'larında GPT sadece
    hikayeyi yeniden yazar, bu ek değişmeden geri eklenir (2026-09-24 TUR 12)."""
    return apply_style_lock("", camera_archetype, catalyst)[2:]


def apply_style_lock(prompt_text: str, camera_archetype: str = "fixed_cctv", catalyst: dict = None) -> str:
    """GPT'nin ürettiği prompt'a — içeriğinden bağımsız — seçilen kamera arketipinin
    sabit stil bloğunu ekler. Catalyst verilirse dinamik gerçekçilik kuralları eklenir."""
    prompt_text = (prompt_text or "").strip().rstrip(".")
    archetype = CAMERA_ARCHETYPES.get(camera_archetype, CAMERA_ARCHETYPES["fixed_cctv"])
    style_lock = archetype["style_lock"]
    # Gemi kadraj kuralı ENV_CENTRIC domainlerde eklenmez: hortum/dalga ana odak
    # kalmalı (tekne olsa bile). catalyst yoksa eski davranış: kural eklenir.
    domain_id = (catalyst or {}).get("domain_id", "")
    if domain_id not in ENV_CENTRIC_DOMAINS and archetype.get("vessel_framing"):
        style_lock = f"{style_lock} {archetype['vessel_framing']}"
    vantage = archetype.get("vantage_env" if domain_id in ENV_CENTRIC_DOMAINS else "vantage")
    if vantage:
        style_lock = f"{style_lock} {vantage}"
    style_lock = f"{style_lock} {_MOTION_START_GUARDRAIL}"

    if catalyst:
        domain_id = catalyst.get("domain_id", "")
        vessel = catalyst.get("forced_ship", "")
        realism = get_realism_guardrails(domain_id, vessel)
        return f"{prompt_text}. {style_lock} {realism}"
    else:
        # Geriye dönük uyumluluk
        return f"{prompt_text}. {style_lock} {get_realism_guardrails('', '')}"



# ─────────────────────────────────────────────────────────────────────────────
# 📺 YOUTUBE METADATA — Merak & No-Spoiler
# ─────────────────────────────────────────────────────────────────────────────

YOUTUBE_METADATA_SYSTEM = """You generate YouTube Shorts metadata for "DeepMyster" — an authentic documentary channel featuring real maritime physical incidents.

CRITICAL TITLE RULES:
- Highlight the CRISIS and DANGER, NEVER reveal the outcome (NO SPOILERS).
- NEVER use channel prefixes like "DeepMyster:", "[DeepMyster]", or "DeepMyster -".
- MAX 55 characters. Punchy, authentic, with 1-2 relevant emojis (🌊, 🚢, ⚠️, ⚓, 🛳️, 🛟).
- English only.

DESCRIPTION RULES:
- 2 realistic sentences describing the physical tension and visible emergency + #DeepMyster #Shorts #Maritime #CCTV #RoughSeas.
- Tags: 8-12 relevant tags.

GOOD TITLE EXAMPLES:
✅ "⚠️ Heavy Sea Swell Slams Open Ferry Car Ramp #Shorts"
✅ "🌊 Mooring Line Snaps as Cruise Ship Surges #Shorts"
✅ "🚢 Car Ferry Takes Massive Green Wave Over Bow #Shorts"
✅ "⚓ Runaway Yacht Crushes Marina Pontoon #Shorts"
✅ "🌊 Cruise Tender Slams Against Liner in Swell #Shorts"

OUTPUT FORMAT (STRICT JSON):
{
  "youtube_title": "Crisis title without spoilers (max 55 chars, NO channel prefix)",
  "youtube_description": "2 authentic sentences describing the visible physical event + hashtags",
  "tags": ["DeepMyster", "Shorts", "Maritime", "CCTV", "Ocean", "RoughSeas"]
}"""
