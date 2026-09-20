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
            "Car ferry rolling violently in heavy swells as deck crew in yellow foul weather gear battle to lash shifting trucks on open vehicle deck.",
            "Heavy Ro-Ro vehicle carrier surging at loading ramp while dock staff frantically guide disembarking cars through storm chop.",
            "Deckhands scrambling across wet flooded vehicle deck to hook emergency heavy chains on sliding freight trailers in severe gale.",
            "Ferry captain and navigation officers urgently correcting thrusters as open bow visor takes pounding oceanic waves.",
            "Passengers gripping safety handrails as a rolling high-speed catamaran heels sharply and deck crew scramble to secure storm gates before the next wave hits.",
            "Commercial Ro-Ro freight crew working together on pitching stern ramp to secure loose vehicle lashings in severe swell.",
            "Island car ferry crew directing vehicles while surge waves wash across lower loading ramp during emergency departure.",
            "On a large PCTC car carrier, a sudden roll sends rows of lashed vehicles straining against their chains, grinding hard against each other.",
            "On a ferry's vehicle deck, a poorly secured car breaks loose in rough seas and slides into a neighboring vehicle, drivers scrambling out in a panic.",
            "A car waiting at the ramp entrance is jolted hard as the vessel suddenly rolls, the driver braking hard in a panic to avoid rolling off the ramp.",
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
            "Dockmaster and marina personnel securing straining cleat lines as violent storm surge lifts floating pontoons with tilting boats.",
            "Marina safety boat crew maneuvering in close quarters to intercept drifting powerboat before it hits concrete breakwater.",
            "A sailing yacht caught broadside in a passing vessel's wake near the marina entrance heels hard, nearly capsizing as the crew scramble to the high side.",
            "A yard travel lift malfunctions with a hoisted yacht swinging dangerously in its slings as yard staff scatter clear of the suspended hull.",
            "A dockside electrical fire flares and spreads rapidly toward neighboring boats as marina staff race to contain it with extinguishers and hoses.",
            "A mooring line snaps during a dockside gathering, the boat lurching hard toward the pier as people aboard lose their footing and grab for the rail.",
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
            "Terminal dock staff rushing to secure double-cleated lines from pitching passenger vessel in breaking waves.",
            "Cruise ship's towering hull surges against the terminal fendering as mooring winches strain and dock crew scramble clear of snapping lines in gusting crosswind.",
            "A cruise ship's pool-deck glass wind-break screen cracks and shatters under a sudden storm gust, deck staff evacuating sunbathing passengers from the area.",
        ],
    },
    "harbor_collisions": {
        "title": "Liman İçi Gemi Manevraları & Yakın Geçişler",
        "reference_scenarios": [
            "Bridge officers and harbor pilot tensely coordinating emergency reverse thrust on container ship near quayside crane.",
            "Commercial tugboat crew managing straining hawser towline as drifting bulk carrier bow slides dangerously close in heavy gale.",
            "Cruise liner listing hard against the terminal fendering as harbor pilots scramble to correct a sudden list during final approach, the towering hull scraping the pier.",
            "Harbor pilot boat crew skillfully pacing alongside massive cargo vessel as harbor pilot boards via pilot ladder in rough water.",
            "Container ship deck crew on forecastle preparing emergency anchor drop as ship drifts toward concrete berth sea wall.",
            "Tugboat deckhands securing heavy towing bridle while flanking giant maneuvering freighter in turbulent propeller wash.",
            "Quayside dockworkers and crane operators reacting from berth as approaching cargo freighter suffers rudder stall.",
            "An open-air deck bar's tables and umbrellas are blown into chaos as sudden heavy weather hits, passengers in casual wear fleeing indoors past toppling furniture.",
        ],
    },
    "rough_seas_storms": {
        "title": "Açık Deniz Fırtınaları & Dev Dalgalar",
        "reference_scenarios": [
            "Bridge officers inside ship wheelhouse bracing as massive 45-foot wave crashes over cargo forecastle deck.",
            "Deckhands in high-visibility foul weather gear holding safety lifelines across waterlogged deck of rolling bulk carrier.",
            "Ship captain and helmsman gripping steering consoles as green seawater floods forward bridge windows in towering swell.",
            "Deep sea fishing trawler crew in heavy oilskins battling freezing spray to haul deck gear in violent cross-seas.",
            "Offshore supply vessel crew fighting the helm as dynamic positioning alarms blare through 40-foot hurricane swells and the vessel yaws hard off station.",
            "Cargo ship deck crew inspecting lashing turnbuckles on shifted container stacks between relentless ocean waves.",
            "Freighter bridge team watching in tension as bow plunges deep underwater before surging through dense sea foam.",
            "A rogue wave sweeps across a cruise ship's open pool deck as sunbathing passengers in swimwear scramble for cover, pool water surging violently across the tiles.",
        ],
    },
    "navigation_hazards": {
        "title": "Kanal, Boğaz & Sığ Su Seyir Tehlikeleri",
        "reference_scenarios": [
            "Container vessel helmsman fighting sudden bank suction effect as ship stern swings dangerously close to canal embankment.",
            "River cargo barge crew bracing as crosscurrent forces pushing barge against concrete bridge support pillar.",
            "Harbor pilot and captain tensely reversing engines as dense fog suddenly reveals unlit breakwater buoy ahead.",
            "Bulk carrier navigating narrow rocky fjord inlet while watch officer signals emergency helm order against strong eddy current.",
            "Commercial tugboat flanking disabled freighter as crosswinds push vessel toward shallow sandbank.",
            "Ferry captain executing emergency bow thruster maneuver as outgoing tidal rip threatens to turn vessel broadside.",
            "Cargo vessel lookout crew on forecastle calling warnings as ship brushes shallow sandbank in turbulent crosscurrents.",
            "A passenger walking an upper deck stumbles hard into the railing as the cruise ship suddenly rolls, crew rushing over to help them back to their feet.",
        ],
    },
    "emergency_rescue": {
        "title": "Acil Müdahale & Kurtarma Operasyonları",
        "reference_scenarios": [
            "Deck crew in bright orange foul weather gear rushing across flooded deck to deploy portable emergency bilge pumps.",
            "Coast guard rescue boat crew launching rigid inflatable craft into violent breaking surf to reach vessel in distress.",
            "Ship officers on open bridge wing scanning dark storm waves with high-power searchlights to guide rescue swimmers.",
            "Deckhands working together against howling gale to retrieve damaged heavy towing gear and secure deck safety lines.",
            "Rescue swimmer descending from helicopter hoist cable onto pitching vessel deck as deck crew signals guidance.",
            "Cruise liner passengers scrambling down a swaying gangway into a pitching tender boat as crew battle to hold it steady against the hull in rough swell.",
            "Salvage tugboat deck crew throwing emergency rescue lines and life rings to seamen on waterlogged deck.",
            "Wind and swell send deck loungers and tables sliding and tumbling across a cruise ship's open sun deck as passengers in resort wear grab for the railings.",
        ],
    },
    "machinery_failures": {
        "title": "Makine, Dümen & Sistem Arızaları",
        "reference_scenarios": [
            "Ship captain and helmsman fighting manual emergency steering wheel in wheelhouse as vessel drifts toward rocky breakwater.",
            "Marine engineers in boiler suits rushing through vibrating engine room to isolate blown hydraulic steering pipe.",
            "Electrical engineer resetting main switchboard breakers under emergency red backup lighting during violent storm blackout.",
            "Bridge officers and lookouts on a cruise liner reacting to sudden bow thruster failure as crosswinds push the towering hull toward the terminal pier during docking.",
            "Deckhands and boatswain dropping emergency anchor on forecastle deck as cargo ship suffers complete propulsion loss.",
            "Chief engineer and mechanics working frantically on jammed steering gear actuator as storm waves batter the hull.",
            "Bridge crew scrambling as the backup radar flickers out and the emergency generator strains to take load while the ship rolls hard in heavy seas.",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 🌊 10 GENİŞ DENİZCİLİK İLHAM ALANI (Genişletilmiş Operasyonel Ufuk)
# ─────────────────────────────────────────────────────────────────────────────

MARITIME_INSPIRATION_DOMAINS = {
    "salvage_and_heavy_towing": {
        "title": "Derin Deniz Kurtarma & Ağır Çekme (Salvage & Ocean Towing)",
        "guidance": "Emergency ocean towing bridles, salvage tug winch tension, pusher tug linked barge dynamics in river rapids, disabled vessel escort in gale seas.",
        "example_elements": ["salvage tugboat", "river pusher tug", "emergency towing bridle", "hydraulic towing pin", "tension winch drum friction"],
        "camera_styles": ["fixed aft work-deck CCTV", "stationary towing winch surveillance camera", "rugged quarterdeck action camera"],
    },
    "ferry_operations": {
        "title": "Feribot & Yolcu Dinamikleri (Ferry & Passenger Vessel Logistics)",
        "guidance": "Vehicle deck kinetic weight shifts in cross swells, loading ramp hydraulic hinge pressure, bow visor spray seals, high-speed catamaran roll recovery, unsecured cars breaking loose and sliding on ferry vehicle decks, ramp-entrance vehicle jolts, wash flooding the open vehicle deck.",
        "example_elements": ["island vehicle ferry", "high-speed passenger catamaran", "open-deck freight ferry", "hydraulic ramp hinge", "deck drainage scuppers"],
        "camera_styles": ["fixed car deck security CCTV", "stationary ramp coaming surveillance camera", "overhead mezzanine deck camera"],
    },

    "commercial_storm_fishing": {
        "title": "Açık Deniz Ticari Balıkçılık (Rough Sea Commercial Fishing)",
        "guidance": "Stern trawler hauling cod nets in heavy following seas, crab boat pot launch line snag on icy decks, factory ship fish processing conveyor surge.",
        "example_elements": ["North Sea stern trawler", "Bering Sea crab vessel", "pelagic longliner", "trawl winch warp wire", "aft ramp floodgate"],
        "camera_styles": ["fixed trawl deck CCTV", "stationary gallows surveillance camera", "protective wheelhouse window camera"],
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
        "guidance": "A powerful tornado forms offshore and makes landfall. The PRIMARY FOCUS is the tornado, extreme weather, and civilian evacuation on the coast (marinas, coastal towns, or New York-style major cities). Small civilian boats, yachts, or marina vessels may be visible reacting to the weather in the background. ABSOLUTELY NO heavy commercial ships, no container ships, no tankers, and no tugboats.",
        "example_elements": ["offshore waterspout", "waterfront debris", "dark storm clouds", "evacuating civilians", "battered coastal architecture"],
        "camera_styles": ["fixed coastal/marina CCTV", "bystander phone from coastal road", "chase POV from safe inland structure"],
    },
}


_last_used_domain: str | None = None  # Süreç-içi hafıza — art arda aynı domain seçilmesini engeller

# ─────────────────────────────────────────────────────────────────────────────
# 🎲 ZORUNLU KOMBİNASYON HAVUZLARI (Varyasyon Garantisi & Görsel Dünya)
# ─────────────────────────────────────────────────────────────────────────────

DOMAIN_ATTRIBUTES = {
    "salvage_and_heavy_towing": {
        "ships": ["Offshore Recovery Vessel", "Heavy Rescue Ship"],
        "environments": ["Gale force open sea", "River rapids", "Shallow coastal water"],
        "events": ["Emergency towing bridle snap", "Tension winch drum friction", "Pushed barge collision"]
    },
    "ferry_operations": {
        "ships": ["Passenger Car Ferry", "High-speed Catamaran"],
        "environments": ["Ferry terminal ramp", "Open vehicle deck", "Island crossing route"],
        "events": ["Secured vehicles breaking loose", "Loading ramp hydraulic hinge failure", "Water flooding open vehicle deck"]
    },

    "commercial_storm_fishing": {
        "ships": ["North Sea Stern Trawler"],
        "environments": ["Heavy following seas", "Freezing storm waves", "Rough fishing grounds"],
        "events": ["Hauling net snag", "Crab pot launch line snag", "Factory deck equipment washed overboard"]
    },
    "shipyard_and_drydock_engineering": {
        "ships": ["Vessel on Slipway"],
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
            "Coastal Town",
            "Marina",
            "Beach Road",
            "Harbor Area",
            "Coastal Boats",
            "Major Coastal City",
            "Dense Urban Waterfront",
            "New York-style Waterfront City"
        ],
        "events": [
            "Tornado forming offshore",
            "Tornado approaching coastline",
            "Tornado making landfall",
            "Coastal evacuation",
            "Waterfront disruption",
            "Strong wind and rain",
            "Coastal debris movement",
            "Boats and marina equipment reacting to severe weather"
        ]
    }
}


def get_creative_catalyst(recent_history: list[str] | None = None) -> dict:
    """
    Geniş denizcilik ilham alanlarından birini seçer ve GPT-4o için bağlam üretir.
    Geçmişteki son 7 seçime bakarak Visual World ve Gemi Tipi tekrarlarını engeller,
    olası kilitlenmeleri Fallback mekanizmasıyla çözer.
    """
    if recent_history is None:
        recent_history = []
        
    recent_domains = []
    recent_ships = []
    
    # recent_history içinde combo_key'ler bulunabilir: "domain|ship|event|env|camera"
    for item in recent_history[-7:]:
        parts = item.split('|')
        if len(parts) >= 2:
            recent_domains.append(parts[0].lower().strip())
            recent_ships.append(parts[1].lower().strip())
            
    all_domains = list(MARITIME_INSPIRATION_DOMAINS.keys())
    available_domains = [d for d in all_domains if d.lower() not in recent_domains]
    
    if available_domains:
        chosen_domain_key = random.choice(available_domains)
    else:
        # Fallback: En yakın geçmişteki 2 tanesini çıkarıp kalandan seç (kilitlenmeyi önler)
        fallback_domains = [d for d in all_domains if d.lower() not in recent_domains[-2:]]
        chosen_domain_key = random.choice(fallback_domains) if fallback_domains else random.choice(all_domains)

    domain_data = MARITIME_INSPIRATION_DOMAINS[chosen_domain_key]
    attrs = DOMAIN_ATTRIBUTES.get(chosen_domain_key)
    
    # Gemi seçimi ve tekrar kontrolü
    all_ships = attrs["ships"]
    available_ships = [s for s in all_ships if s.lower() not in recent_ships]
    
    if available_ships:
        chosen_ship = random.choice(available_ships)
    else:
        # Fallback: Gemi havuzu çok darsa kilitlenmemesi için son 2 videodakileri hariç tut
        fallback_ships = [s for s in all_ships if s.lower() not in recent_ships[-2:]]
        chosen_ship = random.choice(fallback_ships) if fallback_ships else random.choice(all_ships)
        
    chosen_event = random.choice(attrs["events"])
    chosen_env = random.choice(attrs["environments"])

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
        "forced_ship": chosen_ship,
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
2. Cruise ships with civilian passengers aboard
3. Harbor/port scenes with civilians present (dockside crowds, terminal visitors)
4. Marinas with yachts and pleasure craft
5. Rescue operations (coast guard, tow/salvage response)
6. Ferries carrying vehicles and passengers
Never repeat the setting used in the RECENT PRODUCTION HISTORY list below, and never let two consecutive scenarios feel like the same world even if surface details (ship name, incident mechanism) differ — two different cargo-ship deck scenes back to back still count as a repeat.

## EXISTING IDEAS LIBRARY & BRAND UNIVERSE (INSPIRATION & ANTI-REPETITION):
You are provided with samples from DeepMyster's 71-topic reference library.
- THESE SAMPLES DEFINE OUR BRAND'S HIGH-TENSION REALISTIC MARITIME REALITY.
- DO NOT copy or mechanically rehash these exact scenarios by merely swapping ship names or minor nouns.
- INSTEAD: Use them as an inspiration springboard to understand our universe and EXTRAPOLATE completely novel, authentic physical incidents that expand the channel's horizons.

## RECENT PRODUCTION HISTORY (STRICT DO NOT REPEAT):
Review the recent topics list provided in the user prompt. DO NOT repeat the exact same vessel type, incident mechanism, setting, or world from recent productions.

## STORY & PHYSICAL REALITY STANDARDS:
1. PURE PHYSICAL DRAMA: Grounded in real maritime physics, hydrodynamics, friction, weight shifts, weather, or mechanical loads. No invisible/internal issues — no underwater rudders, no internal computer glitches, no unseen engine failures. The crisis MUST be visible in front of the camera.
2. CAST — CREW OR CIVILIANS, MAXIMUM 2, EXACT COUNT (NON-NEGOTIABLE): Every scene has AT MOST 2 named people on screen. Use crew (e.g. a deckhand, a helmsman) OR civilians instead of crew (passengers, dock workers, boat owners, bystanders) — civilians-only scenes are just as valid as crew scenes. State the exact count ONCE as a specific number in visible_start (e.g. "one deckhand," "two passengers" — NEVER "crew members," "some passengers," or any headcount without a number), and keep that exact same number of people identical across visible_start, physical_movement, and visible_consequence. Never introduce a new person who wasn't present at second 0, and never have someone present at the start vanish without an in-shot reason — Seedance renders the prompt literally, and an inconsistent headcount produces ghost people appearing or disappearing mid-shot. Clothing is role-specific and context-aware: yacht/marina staff wear smart nautical casual; cruise/ferry staff wear standard uniforms; fishing crew wear heavy waterproof gear; tug/salvage/heavy-work deckhands wear high-visibility PPE; arctic crew wear thermal immersion suits. Civilians wear ordinary normal clothing appropriate to the setting (casual wear, resort wear, swimwear for pool/deck scenes) and are NEVER dressed in hi-vis PPE. NEVER use white hazmat suits. Do NOT shoehorn cartoonish actions; keep movements authentic.
3. THREE-BEAT STRUCTURE, ALL WITHIN <<DURATION>> SECONDS, ONE CONTINUOUS SHOT (NON-NEGOTIABLE): Every scenario is exactly three beats, no time skips between them, no drone acrobatics, no multi-angle movie cuts, no scene cuts, no camera repositioning mid-shot:
   - BEAT 1 — INSTANT ESTABLISHING FLASH (well under 1 second): A near-instantaneous visual anchor — just enough to place the viewer in the setting and show who is present. This is a flash-frame, NOT a scene, NOT a pause, NOT time for anything routine to be noticed happening — it must not read as a calm moment.
   - BEAT 2 — SUDDEN WRONG TURN: Something goes suddenly, physically wrong with no warning signs and no slow escalation — the break/failure/collision itself happens fast, and MUST be visible and understandable within the first 2 seconds of the shot overall.
   - BEAT 3 — DANGEROUS CONSEQUENCE (through <<DURATION>>s): The immediate, visible physical danger that beat 2 causes, still actively unfolding on screen at <<DURATION>>s — not a resolved or safe outcome.
4. MOMENTUM: Beat 1 is a flash, not a pause — the viewer must understand the danger is already happening within the first 2 seconds of the shot. From that point onward the scene must be ACTIVELY breaking, colliding, flooding, swinging, or in danger, unfolding in real time — fluid, fast, and genuinely dangerous, matching real bystander-filmed maritime incident footage, never a staged or slow-moving escalation.
5. CONCRETE PHYSICAL OUTCOME: The <<DURATION>>th second must show the beat 3 danger still visibly in progress — not a resolved, safe, or calm ending.
6. RAW WEATHER & LIGHTING (NON-NEGOTIABLE): Weather and lighting must read as raw and natural — real overcast, fog, or rain grain, never glossy, overly clean, or cinematically polished; avoid mirror-smooth CGI-looking water or movie-trailer lighting.

## OUTPUT FORMAT (STRICT JSON):
{
  "vessel_class": "Specific real-world vessel class (e.g. Arctic Stern Trawler, 140m Ro-Pax Ferry, Heavy Tugboat, Ocean Cruise Liner, Luxury Motor Yacht)",
  "incident_type": "Short 3-5 word label of the physical crisis",
  "scenario_summary": "One clear, punchy sentence covering all three beats: the normal moment, what goes wrong, and the visible consequence",
  "visible_start": "BEAT 1: a near-instantaneous establishing flash (well under 1 second) showing the setting and people, immediately giving way to beat 2 — the danger must be understood within the first 2 seconds of the shot overall, not a calm moment. State the exact crew/civilian count here once as a specific number (e.g. 'two deckhands', 'one passenger') — never a vague term like 'crew members' with no number. Maximum 2 people.",
  "physical_movement": "BEAT 2 (<<EARLY>>-<<LATE>>s): the sudden physical wrong turn — the break/failure/collision itself, happening fast, no warning. Same people, same exact count as visible_start.",
  "visible_consequence": "BEAT 3 (<<LATE>>-<<DURATION>>s): the immediate dangerous consequence, still visibly unfolding at <<DURATION>>s, not resolved or safe. Same people, same exact count as visible_start.",
  "observer_camera": "The exact assigned camera position, stated concretely (e.g. 'fixed camera bolted to the cruise ship's port-side superstructure', 'bystander's handheld phone from the pier', 'POV from the bow of a coast guard boat')",
  "silent_screen_understandable": true
}"""


def compute_duration_breakpoints(duration: int) -> tuple[int, int]:
    """Sahneyi 3 aşamaya böler: başlangıç / eskalasyon / sonuç.
    12s için 0-3 / 3-9 / 12 üretir — orijinal sabit değerlerle birebir eşleşir."""
    early = max(2, round(duration * 0.25))
    late = max(early + 1, min(duration - 1, round(duration * 0.75)))
    return early, late


def build_scenario_writer_system(duration: int) -> str:
    """SCENARIO_WRITER_SYSTEM'i config.DEFAULT_DURATION'a göre üretir."""
    early, late = compute_duration_breakpoints(duration)
    return (
        SCENARIO_WRITER_SYSTEM_TEMPLATE
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

## OUTPUT FORMAT (STRICT JSON):
{
  "prompt": "The exact generated prompt",
  "word_count": 33
}"""


def build_prompt_simplifier_system(duration: int) -> str:
    """PROMPT_SIMPLIFIER_SYSTEM'i config.DEFAULT_DURATION'a göre üretir."""
    return PROMPT_SIMPLIFIER_SYSTEM_TEMPLATE.replace("<<DURATION>>", str(duration))


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

_REALISM_GUARDRAILS = (
    "Crew and staff clothing must perfectly match the vessel and environment: "
    "yacht/marina crew wear smart nautical casual; cruise/ferry staff wear proper uniforms; "
    "fishing crew wear heavy waterproof gear; tug/salvage/heavy-work deckhands wear high-visibility PPE; "
    "arctic crew wear thermal immersion suits. "
    "Passengers, guests, and bystanders wear ordinary civilian clothing appropriate to the setting "
    "(swimwear, resort or casual wear, sun hats for pool/deck scenes; regular casual clothing for car-deck scenes) — "
    "never hi-vis PPE on civilians. NEVER use white hazmat suits. Raw "
    "natural overcast/fog/rain lighting, not glossy or artificially perfect water or ice."
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
            "camera movement. When filming the vessel from outside/alongside, "
            "frame must keep the hull, bow, or superstructure visible to establish "
            "ship type — no tight shot confined only to deck machinery. For "
            "onboard deck, pool, or vehicle-deck scenes filmed from a camera "
            "mounted ON the ship (looking at its own interior spaces, not the ship "
            "from outside), visible deck architecture, railings, superstructure, "
            "or vehicle-deck structure satisfies this instead — e.g. a pool-deck "
            "camera showing loungers, railings, and open sky is sufficient; do not "
            f"force an exterior hull/bow shot into an onboard scene. {_SINGLE_MOMENT_GUARDRAIL} {_REALISM_GUARDRAILS}"
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
            "beyond it. Filmed from a ship's railing, nearby vessel, or dock, "
            "occasionally showing a hint of a railing, hand, or phone edge at "
            "the frame border. The vessel in crisis must be fully and clearly "
            f"visible in frame at all times, not just a cropped detail. {_SINGLE_MOMENT_GUARDRAIL} {_REALISM_GUARDRAILS}"
        ),
    },
    "chase_pov": {
        "title": "Takip/Kovalama POV (Yakındaki Tekneden)",
        "weight": 1,
        "gpt_guidance": (
            "Chase or pursuit point-of-view filmed from the deck or bow of a "
            "nearby observer vessel — e.g. a coast guard boat, escort boat, or "
            "following ship. TWO distinct vessels are mandatory: the observer "
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
            f"actively in crisis, fully visible, not just a cropped detail. {_SINGLE_MOMENT_GUARDRAIL} {_REALISM_GUARDRAILS}"
        ),
    },
}

# Geriye dönük uyumluluk — bazı test scriptleri tek bir STYLE_LOCK_SUFFIX bekliyor.
# Varsayılan (en sık seçilen) arketipin son ekini temsil eder.
STYLE_LOCK_SUFFIX = CAMERA_ARCHETYPES["fixed_cctv"]["style_lock"]


def choose_camera_archetype() -> str:
    """3 kamera arketipinden birini ağırlıklı rastgele seçer (CCTV varsayılan/en sık)."""
    keys = list(CAMERA_ARCHETYPES.keys())
    weights = [CAMERA_ARCHETYPES[k]["weight"] for k in keys]
    return random.choices(keys, weights=weights, k=1)[0]


def apply_style_lock(prompt_text: str, camera_archetype: str = "fixed_cctv") -> str:
    """GPT'nin ürettiği prompt'a — içeriğinden bağımsız — seçilen kamera arketipinin
    sabit stil bloğunu ekler."""
    prompt_text = (prompt_text or "").strip().rstrip(".")
    archetype = CAMERA_ARCHETYPES.get(camera_archetype, CAMERA_ARCHETYPES["fixed_cctv"])
    return f"{prompt_text}. {archetype['style_lock']}"


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
✅ "⚠️ Heavy Sea Swell Slams Open Ro-Ro Ramp #Shorts"
✅ "🌊 120mm Towing Bridle Strains in High Gale #Shorts"
✅ "🚢 Arctic Trawler Takes Massive Green Wave Over Bow #Shorts"
✅ "⚓ Tugboat Bow Fender Crushed in Tight Canal Berth #Shorts"
✅ "🌊 Gantry Crane Swaying Violently on Container Deck #Shorts"

OUTPUT FORMAT (STRICT JSON):
{
  "youtube_title": "Crisis title without spoilers (max 55 chars, NO channel prefix)",
  "youtube_description": "2 authentic sentences describing the visible physical event + hashtags",
  "tags": ["DeepMyster", "Shorts", "Maritime", "CCTV", "Ocean", "RoughSeas"]
}"""
