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
     Seedance 2 Mini için 45–60 kelimelik (TUR 24; önce 25–45) yüksek görsel sinyal yoğunluklu, süssüz,
     tek kesintisiz, yapılandırılabilir süreli (config.DEFAULT_DURATION) fotogerçekçi
     belgesel hikayesi. Kamera (fixed_cctv / bystander_handheld / chase_pov), ışık ve
     kıyafet kuralları stil kilidiyle (style_lock_suffix) arkadan eklenir.
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
# 🌊 7 İLHAM ALANI: 4 gemi domaini + 3 çevre odaklı (ENV_CENTRIC_DOMAINS), kargo yok (2026-09-24)
# ─────────────────────────────────────────────────────────────────────────────

MARITIME_INSPIRATION_DOMAINS = {
    "ferry_operations": {
        "title": "Feribot & Yolcu Dinamikleri (Ferry & Passenger Vessel Logistics)",
        "guidance": "Waves breaking over the rail onto the vehicle deck, lashing chains snapping, parked driverless cars (engines and headlights off) skidding sideways on a rolling deck, a loading ramp hinge snapping and the ramp dropping. A high-speed catamaran is a twin-hull vessel with two parallel hulls.",
        "example_elements": ["island vehicle ferry", "high-speed passenger catamaran", "open-deck vehicle ferry", "hydraulic ramp hinge", "deck drainage scuppers"],
        "camera_styles": ["fixed car deck security CCTV", "stationary ramp coaming surveillance camera", "overhead mezzanine deck camera"],
    },

    "shipyard_and_drydock_engineering": {
        "title": "Tersane, Kuru Havuz & Kızak Dinamikleri (Drydock & Launch Mechanics)",
        "guidance": "Slipway launches on inclined slipway rails with a launch cradle and timber blocks, the hull sliding toward open water; restraining cables snapping; keel blocks and timber shores collapsing under the hull; a drydock flood gate bursting; crane slings snapping. Every cause is a visible physical object failing on camera.",
        "example_elements": ["inclined slipway rails", "launch cradle", "timber keel blocks", "drydock flood gate", "high-tonnage gantry crane sling"],
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
        "guidance": "Cruise liner terminal berthing and bow thruster docking dynamics, gangway connection stress under swell, tender boat launch/recovery in rough water, hull list correction, near-miss pier approaches. Also covers onboard pool-deck and sun-deck incidents: rogue waves breaking over the rail onto the pool deck, a heavy roll tilting the deck and sending loungers sliding, sudden rolls throwing passengers off balance.",
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
    },
    # 2 Eki, Bahadır: Seedance hızlı akan su gücünü iyi çiziyor, yavaş kayan toprağı 15 sn'de göstermiyor; heyelan,
    # aşırı yağıştan yamaçtan hızla inen çamur ve su akıntısı olarak tanımlanır (kayma/yükselme/yavaş çökme yok).
    "landslide_disasters": {
        "title": "Heyelan (Landslide & Mud Torrent)",
        "guidance": "After extreme rainfall, a fast torrent of brown mud, water, rocks and logs pours down a steep hillside into a street, a road or a village. Always fast, violent flowing mud and water, never slow sliding earth. NO ships or vessels.",
        "example_elements": ["steep hillside street", "brown mud torrent", "rocks and logs in the flow", "parked cars shoved sideways", "road guardrail"],
        "camera_styles": ["bystander phone from a balcony across the street", "bystander phone from a road bridge"],
    },
    # 8 Eki, Bahadır (TASLAK): 🔥 Yangın. Kuru, dumanlı hava; yağmur ve ıslak zemin hiçbir yerde yok.
    "fire_disasters": {
        "title": "Yangın (Wildfire & Fire)",
        "guidance": "A violent, fast-spreading fire in hot, dry, smoky air: a wall of flames sweeping into a hillside neighborhood, flames racing up a tower facade, or a fire tornado tearing across a burning roadside. The flames visibly touch and ignite roofs, trees, vehicles and buildings. NO ships or vessels.",
        "example_elements": ["wall of flames", "burning roofs and trees", "falling burning debris", "glowing embers", "thick smoke"],
        "camera_styles": ["bystander phone from a balcony across the street", "bystander phone from a roadside embankment"],
    },
    # 10 Eki, Bahadır (TASLAK): 🌋 Volkan. Görünür sebep (patlama, lav, kül bulutu, düşen taşlar) ve ağır kütle.
    "volcano_disasters": {
        "title": "Volkan (Volcanic Eruption)",
        "guidance": "A violent volcanic eruption above a village under an ash-grey sky lit orange by the eruption plume: a shockwave blowing out windows, a lava river swallowing parked cars, a pyroclastic cloud tearing through a street, or glowing volcanic bombs punching through roofs. The volcano is always visible above the rooftops. NO ships or vessels.",
        "example_elements": ["erupting volcano above the rooftops", "glowing lava river in a village street", "pyroclastic cloud racing down the flank", "glowing rocks punching through roofs", "shattered shop windows"],
        "camera_styles": ["bystander phone from a hillside terrace facing the volcano", "bystander phone from a rooftop terrace facing the volcano"],
    }
}


_last_used_domain: str | None = None  # Süreç-içi hafıza — art arda aynı domain seçilmesini engeller

# ─────────────────────────────────────────────────────────────────────────────
# 🎲 ZORUNLU KOMBİNASYON HAVUZLARI (Varyasyon Garantisi & Görsel Dünya)
# ─────────────────────────────────────────────────────────────────────────────

# Olay adları kamerada görünen somut tetiktir (TUR 24): "launch friction", "flooding instability",
# "gangway stress", "wind-blown" gibi soyut/görünmez sebepler GPT'ye sebepsiz kriz yazdırıyordu.
DOMAIN_ATTRIBUTES = {
    "ferry_operations": {
        "ships": ["Passenger Car Ferry", "High-speed Catamaran"],
        "environments": ["Ferry terminal ramp", "Open vehicle deck", "Island crossing route"],
        "events": ["Lashing chain snaps and a parked car breaks loose", "Loading ramp hinge snaps and the ramp drops",
                   "Green wave breaks over the rail onto the vehicle deck"]
    },

    # Catamaran tersanede yok (TUR 24): Seedance tek gövdeli yat çiziyordu.
    # TUR 27: ana olay yandan suya indirme (side launch); EVENT_WEIGHTS ile çoğunlukla seçilir.
    "shipyard_and_drydock_engineering": {
        "ships": ["Luxury Motor Yacht", "Sailing Yacht", "Passenger Car Ferry"],
        "environments": ["Side-launch berth at the quay edge", "Shipyard basin", "Drydock interior", "Construction slipway"],
        "events": ["Side launch: the hull tips sideways off the side-launch berth at the quay edge, drops broadside into the water, heels 30-40 degrees and throws a huge wave onto the quay",
                   "Restraining cable snaps during slipway launch", "Keel blocks collapse under the launching hull",
                   "Drydock flood gate bursts open", "Timber shores snap and the hull tips on its keel blocks",
                   "Crane sling snaps while lowering the hull into the water"]
    },
    "marina_and_yacht_operations": {
        "ships": ["Luxury Motor Yacht", "Sailing Yacht", "Runaway Powerboat", "Jet Ski"],
        "environments": ["Floating pontoon dock", "Marina fairway", "Marina fuel dock", "Yacht club entrance",
                         # Kontrolsüz yat çekim yerleri (1 Eki, Bahadır); sadece o olayla uyumlu
                         "Breakwater at the marina entrance", "Marina berthing pier",
                         "Narrow channel between moored boats"],
        "events": [# 1 Eki: havuzda kalır, iskelet hattından çıktı (REMOVED_EVENTS); halat kopması görünmedi
                   "Mooring line snaps in a storm gust", "Jammed throttle sends the boat careening",
                   "Storm surge wave lifts and buckles the floating pontoon", "Passing boat's wake slams the boat sideways",
                   # 1 Eki: eklendi ve aynı gün iskelet hattından çıktı (REMOVED_EVENTS); bağlı teknelere çarpmadı
                   "Yacht loses control and rams moored boats in the marina"]
    },
    "cruise_ship_operations": {
        "ships": ["Ocean Cruise Liner", "Mega Cruise Ship", "Cruise Tender Boat"],
        "environments": ["Cruise terminal berth", "Open-air pool deck", "Sun deck"],
        "events": ["Mooring line snaps and whips across the quay", "Gangway tears loose as the hull surges",
                   "Rogue wave breaks over the rail onto the pool deck", "Heavy roll tilts the deck and sends loungers sliding"]
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
            "Harbor Area",
            # 4 Eki, Bahadır (TASLAK): "Tornado crosses a marina quay" spotu, marina kategorisinin rıhtımı
            "Marina berthing pier",
            # 4 Eki, Bahadır: marina olayının yeni tek spotu
            "High marina balcony",
            # 10 Eki, Bahadır: "Tornado sweeps down a coastal avenue" yüksek balkon noktaları
            "High balcony over a downtown avenue", "Upper-floor balcony over a residential avenue",
            "High balcony over a high-rise avenue"
        ],
        "events": [
            "Tornado forming offshore",
            "Tornado approaching coastline",
            "Tornado making landfall",
            "Coastal evacuation",
            "Waterfront disruption",
            "Tornado rain bands and flying debris lash the waterfront",
            "Coastal debris movement",
            "Marina equipment reacting to severe weather",
            # 4 Eki, Bahadır (TASLAK): yapılandırılmış hat hortum olayları
            "Tornado crosses a marina quay",
            "Tornado sweeps down a coastal avenue"
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
            "Suburban coastal city",
            # Dev dalga baskını çekim yerleri (30 Eyl, Bahadır onayı); iskelet dışındaki olaylar da seçebilir
            "Coastal road below a seafront promenade",
            "Coastal street of low shopfronts",
            "Coastal avenue behind a seawall",
        ],
        "events": [
            "Severe storm hitting downtown",
            "Flash flooding in city streets",
            # 30 Eyl: havuzda kalır, iskelet hattından çıktı (REMOVED_EVENTS); aksiyonsuz video veriyordu
            "Storm gust tears signs and scaffolding loose downtown",
            # 30 Eyl: Bahadır'ın beğendiği 24 Eyl videosu (dosya 1790240764259-vf8owrlvyva)
            "Tidal wave surges over a coastal city street",
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
            "Storm gust rips umbrellas and beach chairs into the air",
            "Large waves reaching the beach",
            "Severe storm disrupting a beachfront area",
            "Beach evacuation during extreme weather",
            "Coastal flooding reaching the beachfront"
        ]
    },
    # 2 Eki, Bahadır: Seedance hızlı akan su gücünü iyi çiziyor, yavaş kayan toprağı 15 sn'de göstermiyor; heyelan,
    # aşırı yağıştan yamaçtan hızla inen çamur ve su akıntısı olarak tanımlanır (kayma/yükselme/yavaş çökme yok).
    "landslide_disasters": {
        "ships": [],
        "environments": [
            "Balcony across a steep hillside street", "Rooftop terrace below a hillside street",
            "Side stairway off a narrow hillside lane",
            "Behind the guardrail of a hillside road", "Bridge on a side road below the slope",
            "Far edge of the road across from the slope",
            "Terrace on the opposite hillside", "High steps on the village square",
            "Upper-floor balcony of a village house",
        ],
        "events": [
            "Mudslide pours down a hillside street",
            "Rain-soaked slope collapses onto a roadside",
            "Mud and debris torrent tears through a hillside village",
        ]
    },
    # 8 Eki, Bahadır (TASLAK): 🔥 Yangın. Ortamlar kamera noktalarıdır (heyelan deseni); Bahadır'ın ortam
    # tarifleri (Hillside village neighborhood, Downtown city center, High-rise coastal city, Burning valley road)
    # iskeletin yer metnine (PLACE) gider.
    "fire_disasters": {
        "ships": [],
        "environments": [
            "Balcony of a hillside house", "Embankment above the village road",
            # 8 Eki (2), Bahadır: cephe yangınında kameralar yüksek; kaldırım noktaları çıktı, çatı terasları girdi
            "Balcony across from a downtown tower", "Rooftop terrace across from a downtown tower",
            "Balcony across from a coastal high-rise", "Rooftop terrace across from a coastal high-rise",
            "Overlook above the burning valley road", "Balcony of a roadside house",
        ],
        "events": [
            "Wall of flames sweeps into a hillside neighborhood",
            "Flames race up a tower facade",
            "Fire tornado tears across a burning roadside",
            # 10 Eki, Bahadır: 4. olay
            "Firefighting helicopter drops water on the flames racing toward a hillside neighborhood",
        ]
    },
    # 10 Eki, Bahadır (TASLAK): 🌋 Volkan. Ortamlar kamera noktaları (hepsi yüksek, dağa bakıyor; heyelan deseni)
    "volcano_disasters": {
        "ships": [],
        "environments": [
            "Hillside terrace facing the erupting volcano", "Rooftop terrace facing the erupting volcano",
            "Balcony of a village house facing the erupting volcano",
        ],
        "events": [
            "Volcano erupts and a shockwave blows out windows",
            "Lava river pours down into a village street",
            "Pyroclastic cloud races down into a village street",
            "Volcanic bombs slam into a village street",
        ]
    }
}

# Gemiyle fiziksel olarak uyuşmayan ortam/olaylar (TUR 10): tender botta havuz/güneş güvertesi
# ve şezlong yok (dry-run 2 #3: "cruise tender boat's pool deck" + 15 yolcu).
SHIP_INCOMPATIBLE = {
    "Cruise Tender Boat": {
        "environments": {"Open-air pool deck", "Sun deck"},
        "events": {"Rogue wave breaks over the rail onto the pool deck", "Heavy roll tilts the deck and sends loungers sliding"},
        "scenario_terms": r"\bpool\s*deck|\bsun\s*deck|\bswimming\s+pool|\bloungers?\b|\bsun\s*beds?\b",
    },
}

# Olay ↔ ortam uyumu (TUR 24): "slipway launch" + "Drydock interior" suyu olmayan düz beton,
# "floating docks" + "Marina fairway" iskelesiz kanal üretiyordu. Tabloda olmayan domain serbest.
EVENT_ENV_COMPAT = {
    "ferry_operations": {
        "Lashing chain snaps and a parked car breaks loose": {"Open vehicle deck", "Island crossing route"},
        "Loading ramp hinge snaps and the ramp drops": {"Ferry terminal ramp"},
        "Green wave breaks over the rail onto the vehicle deck": {"Open vehicle deck", "Island crossing route"},
    },
    "shipyard_and_drydock_engineering": {
        "Side launch: the hull tips sideways off the side-launch berth at the quay edge, drops broadside into the water, heels 30-40 degrees and throws a huge wave onto the quay": {"Side-launch berth at the quay edge"},
        "Restraining cable snaps during slipway launch": {"Construction slipway"},
        "Keel blocks collapse under the launching hull": {"Construction slipway"},
        "Drydock flood gate bursts open": {"Drydock interior"},
        "Timber shores snap and the hull tips on its keel blocks": {"Drydock interior"},
        "Crane sling snaps while lowering the hull into the water": {"Shipyard basin"},
    },
    "marina_and_yacht_operations": {
        "Mooring line snaps in a storm gust": {"Floating pontoon dock", "Marina fuel dock"},
        "Jammed throttle sends the boat careening": {"Floating pontoon dock", "Marina fairway", "Marina fuel dock",
                                                     "Yacht club entrance"},
        "Storm surge wave lifts and buckles the floating pontoon": {"Floating pontoon dock", "Marina fuel dock"},
        "Passing boat's wake slams the boat sideways": {"Marina fairway", "Yacht club entrance", "Floating pontoon dock"},
        "Yacht loses control and rams moored boats in the marina": {"Breakwater at the marina entrance",
                                                                    "Marina berthing pier",
                                                                    "Narrow channel between moored boats"},
    },
    "cruise_ship_operations": {
        "Mooring line snaps and whips across the quay": {"Cruise terminal berth"},
        "Gangway tears loose as the hull surges": {"Cruise terminal berth"},
        "Rogue wave breaks over the rail onto the pool deck": {"Open-air pool deck"},
        "Heavy roll tilts the deck and sends loungers sliding": {"Sun deck", "Open-air pool deck"},
    },
}

# Import anında kontrol: her olay tabloda, her ortamın en az bir olayı var, yazım hatası yok.
for _d, _m in EVENT_ENV_COMPAT.items():
    _ev, _en = set(DOMAIN_ATTRIBUTES[_d]["events"]), set(DOMAIN_ATTRIBUTES[_d]["environments"])
    _bad = (set(_m) ^ _ev) | {e for envs in _m.values() for e in envs - _en} | (_en - set().union(*_m.values()))
    if _bad:
        raise RuntimeError(f"EVENT_ENV_COMPAT[{_d}] havuzla uyuşmuyor: {sorted(_bad)}")

# ── Side launch (TUR 27) ──
SIDE_LAUNCH_EVENT = "Side launch: the hull tips sideways off the side-launch berth at the quay edge, drops broadside into the water, heels 30-40 degrees and throws a huge wave onto the quay"
SIDE_LAUNCH_ENV = "Side-launch berth at the quay edge"

# Olay → izinli gemiler: side launch sadece feribotla (yat değil)
EVENT_SHIP_ONLY = {
    SIDE_LAUNCH_EVENT: {"Passenger Car Ferry"},
}

# Domain içi olay ağırlığı (listede olmayan olay = 1). Side launch ~%71 (10 / 14).
EVENT_WEIGHTS = {
    "shipyard_and_drydock_engineering": {SIDE_LAUNCH_EVENT: 10},
}

# Tekrarı serbest olaylar: 60 günlük combo dedup'ı ve olay×ortam cezası uygulanmaz. Side launch'ta
# tek gemi × tek ortam × 2 kamera = 2 combo var; dedup onu 2 videodan sonra 60 gün kilitlerdi.
REPEATABLE_EVENTS = {SIDE_LAUNCH_EVENT}

# Olaya özel beat planı: yazıcıya zorunlu olarak gider. TUR 28: "slipway" yok, gemi yan düşer (burun/kıç
# kameraya dönük değil), kamera aynı rıhtımda.
EVENT_BEAT_PLANS = {
    SIDE_LAUNCH_EVENT: (
        "BEAT 1 (visible_start's FIRST sentence must show exactly this): The passenger car ferry, its entire long "
        "side facing the camera, tips sideways off the quay edge and drops broadside into the water. "
        "BEAT 2: as the hull hits the water it heels 30-40 degrees and throws up a wall of water. "
        "BEAT 3: the ferry keeps rolling hard from side to side, the huge wave slams onto the quay, and the people "
        "on the quay turn and run back from it. "
        "Never write 'slipway' (say 'side-launch berth at the quay edge'), and never show the ferry bow-first or "
        "stern-first: its long side faces the camera the whole time."
    ),
}

# Olaya özel yazıcı rehberi (TUR 28): domain rehberindeki "slipway" kelimeleri side launch'a sızmasın
EVENT_GUIDANCE = {
    SIDE_LAUNCH_EVENT: (
        "Side launch of a passenger car ferry: the hull stands broadside on a side-launch berth at the quay edge, "
        "tips sideways off it and drops broadside into the water, heeling 30-40 degrees and throwing a huge wave "
        "onto the quay while people there run back.",
        ["side-launch berth at the quay edge", "timber blocks", "holding ropes", "quay edge", "wall of water"],
    ),
}

for _e, _ships in EVENT_SHIP_ONLY.items():
    _d = next(d for d, a in DOMAIN_ATTRIBUTES.items() if _e in a["events"])
    if not _ships <= set(DOMAIN_ATTRIBUTES[_d]["ships"]):
        raise RuntimeError(f"EVENT_SHIP_ONLY[{_e}] domain gemilerinde yok")
for _d, _w in EVENT_WEIGHTS.items():
    if set(_w) - set(DOMAIN_ATTRIBUTES[_d]["events"]):
        raise RuntimeError(f"EVENT_WEIGHTS[{_d}] bilinmeyen olay")

# Gemi üstü ortamlar (TUR 24): stil eki burada "geminin kendi güvertesi, ufukta ikinci gemi yok"
# der; dışarıdan "geminin tamamı görünsün" kuralı ikinci gemi çizdiriyordu.
ONBOARD_ENVIRONMENTS = {"Open vehicle deck", "Island crossing route", "Open-air pool deck", "Sun deck"}
VEHICLE_DECK_ENVIRONMENTS = {"Open vehicle deck", "Island crossing route"}

# Seedance'ın bilmediği gövde tipleri için görünür tarif (TUR 24): prompt "catamaran" deyince tek gövde çiziyordu.
# Gemi üstü çekimde gövdeler kadrajda olamaz; orada sadece gövde tipi söylenir (K1 dry-run: güverte
# CCTV'si + "two parallel hulls visible" çelişiyordu).
SHIP_VISUALS = {
    "High-speed Catamaran": "twin-hull catamaran, two parallel hulls visible",
}
SHIP_VISUALS_ONBOARD = {
    "High-speed Catamaran": "aboard a twin-hull catamaran",
}

# Olay×ortam LRU cezası (TUR 24): aynı domain'in son N üretiminde görülen olay+ortam ikilisi
# (gemi/kamera farklı olsa bile) tekrar seçilmez; bugün "flooding + open vehicle deck" iki kez geldi.
RECENT_PAIR_WINDOW = 5

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


def get_creative_catalyst(recent_history: list[str] | None = None, domain: str | None = None,
                          event: str | None = None) -> dict:
    """
    Geniş denizcilik ilham alanlarından birini seçer ve GPT-4o için bağlam üretir.
    Geçmişteki seçimlere bakarak Visual World (Domain), Gemi Tipi, Event ve Environment tekrarlarını
    strict rotasyonla engeller (LRU).
    domain verilirse (Telegram /uret) domain rotasyonu atlanır, gemi/olay/ortam LRU'su aynen çalışır.
    event verilirse (Telegram /uret olay menüsü) olay zorunludur; ortam EVENT_ENV_COMPAT'a göre,
    gemi olaya izinli gemilerden LRU ile seçilir. domain verilmezse olayın domain'i kullanılır.
    """
    if domain is not None and domain not in MARITIME_INSPIRATION_DOMAINS:
        raise ValueError(f"Bilinmeyen domain: {domain}")
    if event is not None:
        owner = next((d for d, a in DOMAIN_ATTRIBUTES.items() if event in a["events"]), None)
        if owner is None or (domain is not None and domain != owner):
            raise ValueError(f"Olay bu domain'de yok: {domain} / {event}")
        domain = owner
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
    
    if domain is not None:
        chosen_domain_key = domain
    elif available_domains:
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

    def _last_seen(value: str, history: list[str]) -> int:
        """history'de en son görüldüğü indeks; hiç görülmediyse -1 (LRU sırası)."""
        low = value.lower()
        return max((i for i, h in enumerate(history) if h == low), default=-1)

    # Aynı domain'in son RECENT_PAIR_WINDOW üretimindeki olay+ortam ikilileri (TUR 24)
    recent_pairs = {(e, v) for d, e, v in [t for t in zip(recent_domains, recent_events, recent_envs)
                                           if t[0] == chosen_domain_key][-RECENT_PAIR_WINDOW:]}

    recent_pairs = {(e, v) for e, v in recent_pairs if e not in {x.lower() for x in REPEATABLE_EVENTS}}

    def _choose_pair(events: list[str], envs: list[str]) -> tuple[str | None, str | None]:
        """Uyumlu (olay, ortam) ikilisi: son ikililer hariç, önce en eski olay sonra en eski ortam."""
        compat = EVENT_ENV_COMPAT.get(chosen_domain_key, {})
        pairs = [(e, v) for e in events for v in envs if e not in compat or v in compat[e]]
        if not pairs:
            raise RuntimeError(f"{chosen_domain_key}: olay×ortam uyumu seçenek bırakmadı ({events} × {envs})")
        fresh = [p for p in pairs if (p[0].lower(), p[1].lower()) not in recent_pairs] or pairs
        keyed = [((_last_seen(e, recent_events), _last_seen(v, recent_envs)), (e, v)) for e, v in fresh]
        best = min(k for k, _ in keyed)
        return random.choice([p for k, p in keyed if k == best])

    # Gemi, Olay ve Ortam Seçimi (Kendi içlerinde tekrarı minimize eder)
    vessel_envs = VESSEL_ENVIRONMENTS.get(chosen_domain_key)
    if event is not None:
        # Zorunlu olay (Telegram olay menüsü): uyumlu ortam + olaya izinli gemi, ikisi de LRU
        compat = EVENT_ENV_COMPAT.get(chosen_domain_key, {})
        envs = [v for v in attrs["environments"] if event not in compat or v in compat[event]]
        chosen_event = event
        if vessel_envs:
            if event in vessel_envs["vessel_only_events"]:
                envs = [v for v in envs if v in vessel_envs["environments"]]
            _, chosen_env = _choose_pair([event], envs)
            chosen_ship = (_choose_lru(attrs["ships"], recent_ships)
                           if chosen_env in vessel_envs["environments"] else None)
        else:
            ships = [s for s in attrs["ships"] if s in EVENT_SHIP_ONLY.get(event, attrs["ships"])
                     and event not in SHIP_INCOMPATIBLE.get(s, {}).get("events", set())]
            chosen_ship = _choose_lru(ships, recent_ships)
            banned = SHIP_INCOMPATIBLE.get(chosen_ship or "", {}).get("environments", set())
            _, chosen_env = _choose_pair([event], [v for v in envs if v not in banned])
    elif vessel_envs:
        # Gemisi opsiyonel domain (TUR 11): önce ortam; şehir/plaj ortamında gemi yok
        chosen_env = _choose_lru(attrs.get("environments", []), recent_envs)
        if chosen_env in vessel_envs["environments"]:
            chosen_ship = _choose_lru(attrs.get("ships", []), recent_ships)
            events = attrs.get("events", [])
        else:
            chosen_ship = None
            events = [e for e in attrs.get("events", []) if e not in vessel_envs["vessel_only_events"]]
        chosen_event, chosen_env = _choose_pair(events, [chosen_env])
    elif chosen_domain_key in EVENT_WEIGHTS:
        # Ağırlıklı domain (TUR 27): önce olay (ağırlıkla), sonra ona izinli gemi ve ortam
        compat = EVENT_ENV_COMPAT.get(chosen_domain_key, {})
        weights = EVENT_WEIGHTS[chosen_domain_key]
        events = [e for e in attrs["events"] if e in REPEATABLE_EVENTS
                  or any((e.lower(), v.lower()) not in recent_pairs for v in compat.get(e, attrs["environments"]))]
        events = events or attrs["events"]
        chosen_event = random.choices(events, weights=[weights.get(e, 1) for e in events], k=1)[0]
        ships = [s for s in attrs["ships"] if s in EVENT_SHIP_ONLY.get(chosen_event, attrs["ships"])
                 and chosen_event not in SHIP_INCOMPATIBLE.get(s, {}).get("events", set())]
        chosen_ship = _choose_lru(ships, recent_ships)
        banned = SHIP_INCOMPATIBLE.get(chosen_ship or "", {}).get("environments", set())
        envs = [v for v in attrs["environments"]
                if v not in banned and (chosen_event not in compat or v in compat[chosen_event])]
        _, chosen_env = _choose_pair([chosen_event], envs)
    else:
        # Taze olay+ortam ikilisi kalmayan gemi seçilmez (TUR 24: Cruise Tender'ın 2 olayı da yakın
        # geçmişteyse ceza boşa düşüyordu); hiçbirinde kalmadıysa tüm gemiler aday.
        def _has_fresh(ship: str) -> bool:
            b = SHIP_INCOMPATIBLE.get(ship, {})
            compat = EVENT_ENV_COMPAT.get(chosen_domain_key, {})
            return any((e.lower(), v.lower()) not in recent_pairs
                       for e in attrs["events"] if e not in b.get("events", set())
                       for v in attrs["environments"] if v not in b.get("environments", set())
                       and (e not in compat or v in compat[e]))
        ships = attrs.get("ships", [])
        chosen_ship = _choose_lru([s for s in ships if _has_fresh(s)] or ships, recent_ships)
        banned = SHIP_INCOMPATIBLE.get(chosen_ship or "", {})
        events = [e for e in attrs.get("events", []) if e not in banned.get("events", set())
                  and chosen_ship in EVENT_SHIP_ONLY.get(e, {chosen_ship})]
        envs = [e for e in attrs.get("environments", []) if e not in banned.get("environments", set())]
        if attrs.get("events") and not events or attrs.get("environments") and not envs:
            raise RuntimeError(f"SHIP_INCOMPATIBLE '{chosen_ship}' için {chosen_domain_key} havuzunda seçenek bırakmadı")
        chosen_event, chosen_env = _choose_pair(events, envs)

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
7. BEAT 1 MUST SHOW DANGER ALREADY IN MOTION (NON-NEGOTIABLE): visible_start must contain a physical action verb happening right now (e.g. crashes, slams, snaps, surges, swings, tilts). FORBIDDEN patterns in visible_start: 'is visible', 'visible from', the phrase 'as [X] approaches' (e.g. 'as the ferry approaches the pier'), 'scene opens', 'observing as', 'bustling', 'looming', 'signals for'. The grammatical subject of visible_start's first sentence must be the physical thing in danger or the people in the scene (e.g. 'A mooring line snaps…', 'Waves crash…'); camera position and framing belong only in observer_camera, never in visible_start. Instead, describe the crisis as it happens or immediately after it starts. Beat 1 is the TRIGGER starting (wave hits, line snaps, blocks give way); beat 3 is the RESULT. Starting with the trigger is required; starting with the result is still forbidden. visible_start pairs the trigger action with a visible physical effect on another object (spray, snapping lines, sliding objects, splintering blocks); human emotional reactions (startled, alarmed, shocked, panicked) belong in physical_movement, never in visible_start. Any people in visible_start must already be moving (bracing, scrambling, lunging, grabbing) — never standing, watching, looking, or waiting. Give the moving object ONE direction relative to the camera (across the frame, away from the camera, or toward the camera) and keep that same direction in every beat.
8. VISIBLE TRIGGER (NON-NEGOTIABLE): The crisis has ONE concrete physical cause that the camera sees (e.g. a wave crashes over the rail, a mooring line or cable snaps, keel blocks collapse, a hinge snaps, the ship heels hard, a wake slams into the hull). Name it in visible_trigger and show it in visible_start or physical_movement. Never an invisible or abstract cause (friction, pressure, stress, instability, 'an unexpected force', 'for no reason'), and never people panicking or running without that visible cause.
9. REAL PHYSICS: People can never push, pull, hold back or stop a vessel, floating dock or pontoon by hand. Slipway launches happen on inclined slipway rails with a launch cradle and timber blocks, sliding toward open water, never across flat dry concrete. Cars on a ferry vehicle deck are parked and driverless with engines and headlights off; they skid or slide, never drive.
10. BEAT 3 KEEPS MOVING: The last 5 seconds show the danger still physically moving (still sliding, still flooding, still swinging). Never write stabilize, steady, regain control, settle or calm in visible_consequence, and never end on people trying to stabilize things.

## OUTPUT FORMAT (STRICT JSON):
All field values are plain descriptive prose. Never start a value with a label or timestamp such as "BEAT 1:" or "(0-4s)".
{
  "vessel_class": "Specific real-world vessel class (or 'None' if the prompt specifies it's a gemisiz sahne/şehir/plaj)",
  "incident_type": "Short 3-5 word label of the physical crisis",
  "scenario_summary": "One clear, punchy sentence covering only what the three beats show: the opening action, what goes wrong, and the visible consequence. It must not introduce any person, vessel, or object that is not in visible_start, physical_movement, or visible_consequence",
  "visible_start": "<<VISIBLE_START_DESC>>",
  "beat1_action_verb": "The single main physical action verb of visible_start's first sentence, copied exactly as written there (e.g. 'gushes', 'spins', 'lifts'). It must be what the hazard does, not what people or the camera do.",
  "visible_trigger": "The single concrete physical trigger the camera sees (e.g. 'the mooring line snaps', 'a green wave crashes over the rail', 'keel blocks collapse'), using words that also appear in visible_start or physical_movement. Never friction, pressure, stress, instability or an unseen cause.",
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


def cast_range(domain_id: str, event: str = "", ship: str = "") -> tuple[int, int] | None:
    """Kişi aralığı: önce olaya özel (EVENT_CAST_RANGES), sonra gemiye özel (SHIP_CAST_RANGES), yoksa
    domain'in. Env-centric için None."""
    if domain_id not in DOMAIN_CAST_RANGES:
        return None
    return EVENT_CAST_RANGES.get(event) or SHIP_CAST_RANGES.get(ship or "") or DOMAIN_CAST_RANGES.get(domain_id)


def build_scenario_writer_system(duration: int, domain_id: str = "", event: str = "", ship: str = "") -> str:
    """SCENARIO_WRITER_SYSTEM'i config.DEFAULT_DURATION'a göre üretir."""
    early, late = compute_duration_breakpoints(duration)
    
    if domain_id in ENV_CENTRIC_DOMAINS:
        cast_rule = "ENVIRONMENT-CENTRIC (HUMANS AS BACKGROUND, AT LEAST ONE): Focus the entire scene and camera strictly on the MASSIVE NATURAL EVENT (e.g. tornado, waterspout, giant wave, flood). Do NOT focus on specific fleeing humans. Humans/cars are background scale references, but at least one human must be visible and explicitly named in the beats (e.g. rooftop watchers, sidewalk bystanders, distant figures on the promenade). Never a zero-human scene. The cliché of a hi-vis hero charging toward the danger is forbidden. The natural event must be the primary visual anchor and must remain fully in frame. Do not let the event get pushed out of the camera's view."
        vis_start = "A near-instantaneous establishing flash (well under 1 second) showing the massive natural event already in violent motion (e.g. a tornado tearing across the shoreline, a rogue wave crashing onto the beach). DO NOT start by describing people (e.g. 'Two pedestrians'). The natural event must be the primary visual anchor. Do NOT start with the consequence already happening."
        phys_mov = "The sudden physical wrong turn — STRONG VISIBLE PHYSICAL ACTION of the natural event (e.g., sweeps, crashes, rips, floods, slams). The physical movement of the disaster must be explicit and extreme."
        vis_cons = "The immediate dangerous consequence of the natural disaster, still visibly unfolding at <<DURATION>>s, not resolved or safe. Never end with the danger settling, stopping, calming, or being resolved, and never end on people just watching; end mid-action (e.g. 'still surging', 'continues to slide')."
    elif domain_id in DOMAIN_CAST_RANGES:
        lo, hi = cast_range(domain_id, event, ship)
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
   The first sentence pairs the opening action with what it physically does to another object (spray bursting, blocks splintering, cars sweeping sideways). Never put human emotional reactions (startled, alarmed, shocked, panicked) or static people (standing, watching, looking, waiting) in the first sentence; people's reactions come later. Never change what happens to people: keep the scenario's own verbs for them (do not turn 'sets the crew into action' into 'sweeps the crew'). Keep ONE movement direction for the moving object throughout the prompt.
   GOOD: 'The sailing yacht lurches down the slipway, keel blocks splintering beneath the hull'
   BAD: 'The sailing yacht lurches forward, startling three workers'
10. VISIBLE TRIGGER: Keep the scenario's visible trigger (the wave, the snapping line, the collapsing blocks) as something the camera sees. Never write an invisible or abstract cause such as 'friction', 'pressure', 'instability', 'an unexpected force' or 'for no reason'.
11. REAL PHYSICS: People never push, pull or hold a vessel, dock or pontoon by hand. Cars on a ferry deck are parked and driverless; they skid or slide, never drive, and their headlights are off.
12. LENGTH AND ENDING: 45 to 60 words. Give the final outcome its own full sentence of at least 12 words in which the danger is still physically moving. Never end with stabilize, steady, regain control, settle or calm.

## OUTPUT FORMAT (STRICT JSON):
{
  "prompt": "The exact generated prompt",
  "word_count": 52
}"""


def build_prompt_simplifier_system(duration: int, domain_id: str = "") -> str:
    """PROMPT_SIMPLIFIER_SYSTEM'i config.DEFAULT_DURATION'a göre üretir."""
    sys_prompt = PROMPT_SIMPLIFIER_SYSTEM_TEMPLATE.replace("<<DURATION>>", str(duration))
    if domain_id in ENV_CENTRIC_DOMAINS:
        sys_prompt += "\n\n13. STRICT ENVIRONMENT-CENTRIC FOCUS: DO NOT START THE PROMPT WITH HUMANS (e.g. 'Two pedestrians...'). Begin immediately with the massive natural disaster (e.g. 'A massive coastal tornado...', 'A giant rogue wave...'). Humans are secondary background elements, but keep every person from the scenario (e.g. rooftop watchers, bystanders) in the prompt; never drop all humans. DO NOT DILUTE THE PHENOMENON (keep exact words like 'tornado', 'waterspout', 'tsunami', 'storm surge')."
    return sys_prompt


# ─────────────────────────────────────────────────────────────────────────────
# 🎥 KAMERA ARKETİPLERİ — Impact Seacam referans analizi (Fixed CCTV + Handheld + Chase POV)
# ─────────────────────────────────────────────────────────────────────────────
# Python HER üretimde bu 3 arketipten birini seçer (ağırlıklı rastgele — CCTV en
# sık/varsayılan). Seçim hem GPT'ye (senaryo aşaması) hem de deterministik stil
# kilidine aktarılır — ikisi arasında çelişki olmaması için TEK kaynak.

# Stil eki sahneye göre kısa modüllerden kurulur (TUR 24): eski ek 270-341 kelimeydi, hikaye
# (36 kelime) prompt'un %10'u kalıyordu; handheld'de "hand/phone edge", gemi üstü sahnede
# "vessel fully visible" ve tersaneye havuz/yolcu kıyafeti sızıyordu. Hedef ~80-100 kelime.

# Kıyafet: sadece o domain/ortamın rolleri
_CLOTHING = {
    "ferry_operations": "Crew wear orange hi-vis PPE; drivers and passengers wear casual clothes.",
    "shipyard_and_drydock_engineering": "Shipyard workers wear orange hi-vis PPE and hard hats.",
    "marina_and_yacht_operations": "Marina staff wear orange hi-vis PPE; boat owners wear casual clothes.",
}
_CLOTHING_CRUISE_ONBOARD = "Passengers wear swimwear or resort wear; crew wear white cruise uniforms."
_CLOTHING_CRUISE_BERTH = "Dock crew wear orange hi-vis PPE; passengers wear casual clothes."
_CLOTHING_ENV = "Bystanders wear civilian clothes, never hi-vis PPE on civilians; emergency responders wear service uniforms."
_CLOTHING_ENV_DOCK = " Dock workers wear orange hi-vis PPE."
_CLOTHING_LEGACY = "Crew wear orange hi-vis PPE; passengers and bystanders wear casual clothes, never hi-vis PPE on civilians."

_LIGHTING = "Raw natural light matching the weather, never glossy or CGI; no white hazmat suits."

# El kamerası çekim yeri (gemi dışı sahne), domain'e göre
_HANDHELD_SPOT = {
    "ferry_operations": "the quay",
    "shipyard_and_drydock_engineering": "the shipyard floor",
    "marina_and_yacht_operations": "the pontoon",
    "cruise_ship_operations": "the quay",
}


def _has_ship(vessel_class: str | None) -> bool:
    return bool(vessel_class) and vessel_class.strip().lower() != "none"


def scene_physics_rules(domain_id: str, vessel_class: str, environment: str) -> list[str]:
    """Sahneye özgü fizik kuralları (TUR 24); stil ekine ve yazıcı mesajına aynen gider.

    İşçiler yatı elle itiyordu, kızak suyu olmayan düz betondu, feribotta arabalar farları
    yanık sürülüyordu, catamaran tek gövde çiziliyordu.
    """
    rules = []
    ship = (vessel_class or "").strip()
    if _has_ship(ship):
        visual = (SHIP_VISUALS_ONBOARD if environment in ONBOARD_ENVIRONMENTS else SHIP_VISUALS).get(ship)
        if visual:
            rules.append(f"{visual[0].upper()}{visual[1:]}.")
        # Gemi üstünde (havuz/güneş/araç güvertesi) itilecek gemi/iskele yok; kural gürültü olur
        # Side launch'ta gövdenin yanında kimse yok (TUR 27); ek 124 kelimeye çıkıyordu
        if environment not in ONBOARD_ENVIRONMENTS and environment != SIDE_LAUNCH_ENV:
            rules.append("Nobody pushes, pulls or holds a vessel or dock by hand.")
    if domain_id == "shipyard_and_drydock_engineering":
        rules.append({
            "Construction slipway": "The hull rides a launch cradle on inclined slipway rails sloping down into open water.",
            "Drydock interior": "The hull stands on timber keel blocks braced by side shores inside the drydock.",
            "Shipyard basin": "A gantry crane holds the hull in slings above the open water of the basin.",
            SIDE_LAUNCH_ENV: "Its entire long side faces the camera; never bow-first or stern-first.",
        }.get(environment, "The hull sits on timber blocks and supports, never on bare flat concrete."))
    if environment == SIDE_LAUNCH_ENV:
        rules.append("People on the quay run back as the wave hits.")
    if domain_id == "ferry_operations" and environment in VEHICLE_DECK_ENVIRONMENTS:
        rules.append("Parked driverless cars, engines and headlights off, skid or slide; they never drive.")
    return rules


def get_realism_guardrails(domain_id: str, vessel_class: str, environment: str = "") -> str:
    """Kıyafet (sadece ilgili roller) + ışık. domain_id boşsa geriye uyumlu genel metin."""
    domain_id = (domain_id or "").lower()
    if domain_id in ENV_CENTRIC_DOMAINS:
        clothing = _CLOTHING_ENV + (_CLOTHING_ENV_DOCK if _has_ship(vessel_class) else "")
    elif domain_id == "cruise_ship_operations":
        clothing = _CLOTHING_CRUISE_ONBOARD if environment in ONBOARD_ENVIRONMENTS else _CLOTHING_CRUISE_BERTH
    elif environment == SIDE_LAUNCH_ENV:
        clothing = "Workers wear orange hi-vis PPE; spectators wear casual clothes."
    else:
        clothing = _CLOTHING.get(domain_id, _CLOTHING_LEGACY)
    return f"{clothing} {_LIGHTING}"


# Bu domainlerde forced_ship=None olabilir (doğal afet/olay odaklı, gemi zorunlu değil).
# chase_pov iki ayrı gemi zorunlu kıldığı için buralarda seçilmemeli — aksi halde GPT
# ikinci gemiyi karşılamak için yoktan bir tekne icat ediyordu (2026-09-23 tespit edildi).
ENV_CENTRIC_DOMAINS = ["coastal_tornado_landfall", "urban_city_disasters", "open_beach_coastal_events",
                       "landslide_disasters",   # 2 Eki: heyelan (gemisiz, sivil giyim kuralı)
                       "fire_disasters",        # 8 Eki: yangın (gemisiz, sivil giyim kuralı)
                       "volcano_disasters"]     # 10 Eki: volkan (gemisiz, sivil giyim kuralı)

# Gemi domainlerinde ekrandaki gerçekçi kişi aralığı (2026-09-24). "Max 2" sadece
# kargo gemileri içindi; kargo domain'i artık yok. Env-centric domainler tabloya
# girmez, kendi ENVIRONMENT-CENTRIC cast kuralını alır.
# Env-centric domainlerde sayı zorunlu değil ama en az 1 insan (arka plan ölçeği) şart (TUR 16).
ENV_CENTRIC_MIN_PEOPLE = 1

DOMAIN_CAST_RANGES = {
    "ferry_operations": (2, 5),
    "shipyard_and_drydock_engineering": (2, 5),
    "marina_and_yacht_operations": (3, 6),
    "cruise_ship_operations": (8, 25),
}

# Olaya özel kişi aralığı (TUR 27): suya indirme kalabalık çeker; K1 dry-run'da 5 adayın 3'ü
# "about ten/a dozen/twenty spectators" ile tersane aralığını (2-5) aşıp elendi.
EVENT_CAST_RANGES = {
    SIDE_LAUNCH_EVENT: (5, 20),
}

# Gemiye özel kişi aralığı (TUR 29): jet ski'de 1-2 sürücü var; marina aralığı (3-6) "two riders" ve
# "one rider"ı 7 günde 3 kez haksız reddetti.
SHIP_CAST_RANGES = {
    "Jet Ski": (1, 6),
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
            "Static fixed-mount security CCTV camera, normal lens, no fisheye or drone view; "
            "the frame never moves, zooms or cuts."
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
            "Bystander handheld phone footage, normal lens, no fisheye or drone view; slight tremor "
            "only, fixed position and framing, no zoom or cuts; no phone, hands or fingers in frame."
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
            "Chase POV from a nearby boat's deck, normal lens, no fisheye or drone view; slight swell "
            "motion, same distance, no zoom or cuts; its rail and the separate vessel in crisis stay visible."
        ),
    },
}

def choose_camera_archetype(domain_id: str = "", environment: str = "") -> str:
    """3 kamera arketipinden birini ağırlıklı rastgele seçer (CCTV varsayılan/en sık).

    Environment-centric domainlerde (gemi yok, forced_ship=None) chase_pov elenir:
    o arketip iki ayrı gemi zorunlu kılar, gemisiz domainde GPT bunu karşılamak
    için yoktan bir tekne icat ediyordu (2026-09-23 tespit edildi).
    Gemi üstü ortamlarda (havuz/güneş/araç güvertesi) da elenir (TUR 24): başka tekneden
    çekimde güvertedeki olay görünmüyor, K1 dry-run'da havuz güvertesine chase_pov atanmıştı.
    """
    keys = list(CAMERA_ARCHETYPES.keys())
    # Side launch (TUR 27/28): kamera aynı rıhtımda, sabit CCTV veya el kamerası
    if domain_id in ENV_CENTRIC_DOMAINS or environment in ONBOARD_ENVIRONMENTS or environment == SIDE_LAUNCH_ENV:
        keys = [k for k in keys if k != "chase_pov"]
    weights = [CAMERA_ARCHETYPES[k]["weight"] for k in keys]
    return random.choices(keys, weights=weights, k=1)[0]


# Seedance ilk 3-4 sn yavaş açıyordu (TUR 9); son 5-7 sn de donuk kalıyordu (TUR 24). Tüm arketiplere eklenir.
_MOTION_START_GUARDRAIL = (
    "Already moving in the first frame, still moving in the last; no calm opening or ending."
)


# Side launch akıcılığı (TUR 27): yavaş başlangıç yok, tek hızlı hareket
_SIDE_LAUNCH_MOTION = ("One continuous fast motion, no slow start; already tipping in the first frame, "
                       "still rolling in the last.")


def join_story_and_style(story: str, style_suffix: str) -> str:
    """Hikaye + sabit stil eki → Kie'ye giden nihai prompt."""
    return f"{(story or '').strip().rstrip('.')}. {style_suffix}"


def style_lock_suffix(camera_archetype: str = "fixed_cctv", catalyst: dict = None) -> str:
    """Hikayeden bağımsız sabit stil eki (kamera + gerçekçilik). Kie retry'larında GPT sadece
    hikayeyi yeniden yazar, bu ek değişmeden geri eklenir (2026-09-24 TUR 12)."""
    return apply_style_lock("", camera_archetype, catalyst)[2:]


def _location_line(camera_archetype: str, domain_id: str, ship: str, environment: str) -> str:
    """Çekim yeri + kadraj (TUR 24): gemi üstü sahnede ikinci gemi yok, dışarıdan geminin tamamı."""
    if domain_id in ENV_CENTRIC_DOMAINS:
        if camera_archetype == "bystander_handheld":
            return "Filmed by an onlooker on land (balcony, window, rooftop or roadside)."
        return ""
    name = f"the {ship.lower()}" if _has_ship(ship) else "the vessel"
    if environment == SIDE_LAUNCH_ENV:
        # TUR 28: aynı rıhtımda ~50 m yanda, geminin tüm boyu kadrajı doldurur, büyüklük/konum değişmez
        return ("Filmed from the same quay about 50 m away; the ferry's whole length fills the frame, "
                "same size and position throughout, no jump closer.")
    if environment in ONBOARD_ENVIRONMENTS and camera_archetype != "chase_pov":
        return f"Filmed aboard {name}; no second ship on the horizon."
    if camera_archetype == "bystander_handheld":
        return f"Filmed at eye level from {_HANDHELD_SPOT.get(domain_id, 'the dock')}; {name} stays fully in frame."
    if camera_archetype == "fixed_cctv":
        return f"{name[0].upper()}{name[1:]} stays fully in frame."
    return ""


def apply_style_lock(prompt_text: str, camera_archetype: str = "fixed_cctv", catalyst: dict = None) -> str:
    """GPT'nin ürettiği hikayeye seçilen kamera arketipinin ve sahnenin kısa stil ekini ekler.

    Sıra: kamera, çekim yeri/kadraj, sahne fiziği, hareket, kıyafet + ışık. Catalyst yoksa
    geriye uyumlu genel ek (gemili sahne varsayımı).
    """
    prompt_text = (prompt_text or "").strip().rstrip(".")
    archetype = CAMERA_ARCHETYPES.get(camera_archetype, CAMERA_ARCHETYPES["fixed_cctv"])
    cat = catalyst or {}
    domain_id = cat.get("domain_id", "")
    ship = cat.get("forced_ship", "") or ""
    env = cat.get("forced_environment", "") or ""
    motion = _SIDE_LAUNCH_MOTION if env == SIDE_LAUNCH_ENV else _MOTION_START_GUARDRAIL
    parts = [archetype["style_lock"], _location_line(camera_archetype, domain_id, ship, env),
             *scene_physics_rules(domain_id, ship, env), motion,
             get_realism_guardrails(domain_id, ship, env)]
    return f"{prompt_text}. " + " ".join(p for p in parts if p)


# Geriye dönük uyumluluk: bazı betikler tek bir STYLE_LOCK_SUFFIX bekliyor (varsayılan arketip, genel sahne).
STYLE_LOCK_SUFFIX = style_lock_suffix("fixed_cctv")


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
