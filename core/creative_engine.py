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
    "arctic_ice_navigation": {
        "title": "Kutup & Buzul Seyri (Ice Navigation & Cold Weather)",
        "guidance": "Polar pack ice navigation, hull ice grinding, frozen spray accumulation, bow de-icing, sub-zero blizzard deck operations, icebreaker escort friction.",
        "example_elements": ["polar research vessel", "heavy icebreaker", "arctic LNG carrier", "ice floe impact", "freezing deck spray", "pneumatic de-icing boots"],
        "camera_styles": ["fixed bridge wing cold-weather camera", "stationary forecastle ice-watch camera", "low-angle hull observation CCTV"],
    },
    "heavy_lift_and_project_cargo": {
        "title": "Ağır Yük & Proje Yükü Elleçleme (Heavy Lift & Deck Cargo)",
        "guidance": "Oversized industrial cargo shifting in swells, deck gantry cranes, timber deck cargo stanchion stress, turbine blade transport, modular hull transport barge.",
        "example_elements": ["heavy-lift crane ship", "ocean cargo deck barge", "coastal lumber freighter", "lashing turnbuckle strain", "heavy equipment deck cradle"],
        "camera_styles": ["fixed catwalk cargo CCTV", "stationary crane boom monitoring camera", "upper bridge deck surveillance camera"],
    },
    "salvage_and_heavy_towing": {
        "title": "Derin Deniz Kurtarma & Ağır Çekme (Salvage & Ocean Towing)",
        "guidance": "Emergency ocean towing bridles, salvage tug winch tension, pusher tug linked barge dynamics in river rapids, disabled vessel escort in gale seas.",
        "example_elements": ["salvage tugboat", "river pusher tug", "emergency towing bridle", "hydraulic towing pin", "tension winch drum friction"],
        "camera_styles": ["fixed aft work-deck CCTV", "stationary towing winch surveillance camera", "rugged quarterdeck action camera"],
    },
    "offshore_supply_and_dp": {
        "title": "Açık Deniz İkmal & Dinamik Konumlandırma (Offshore Supply & Rig Ops)",
        "guidance": "Platform supply vessels (PSV) holding station in heavy seas, cargo crane transfer swing, high-pressure hose connection surge, anchor handling tug deck ops.",
        "example_elements": ["platform supply vessel (PSV)", "anchor handling tug (AHTS)", "deck cargo rail", "dry bulk loading hose", "heavy shark-jaw line stopper"],
        "camera_styles": ["fixed aft deck floodlight camera", "stationary superstructure surveillance CCTV", "bridge aft control console camera"],
    },
    "ro_ro_and_ferry_operations": {
        "title": "Ro-Ro, Feribot & Yolcu Gemisi Dinamikleri (Ferry, Ro-Ro & Passenger Vessel Logistics)",
        "guidance": "Vehicle deck kinetic weight shifts in cross swells, loading ramp hydraulic hinge pressure, bow visor spray seals, high-speed catamaran roll recovery, lashed vehicle rows straining and grinding on car carriers (PCTC), unsecured cars breaking loose and sliding on ferry vehicle decks, ramp-entrance vehicle jolts, wash flooding the open vehicle deck.",
        "example_elements": ["island vehicle ferry", "high-speed passenger catamaran", "open-deck freight ferry", "PCTC car carrier", "lashed vehicle rows", "vehicle lashing chain", "hydraulic ramp hinge", "deck drainage scuppers"],
        "camera_styles": ["fixed car deck security CCTV", "stationary ramp coaming surveillance camera", "overhead mezzanine deck camera"],
    },
    "bulk_and_tanker_logistics": {
        "title": "Dökme Yük & Tanker Dinamikleri (Bulk, Liquid & Gas Transport)",
        "guidance": "Ore carrier liquefaction shifts, crude oil tanker surge at single point mooring buoy, deck manifold emergency shutdown, ballast tank venting wash.",
        "example_elements": ["capesize bulk ore carrier", "crude oil supertanker", "chemical parcel tanker", "deck manifold piping", "ballast vent head surge"],
        "camera_styles": ["fixed catwalk pipe-rack CCTV", "stationary forward mooring deck camera", "bridge wing look-down surveillance"],
    },
    "container_and_gantry_operations": {
        "title": "Konteyner Taşımacılığı & Terminal Elleçleme (Container Stacks & Port Gantry)",
        "guidance": "Parametric rolling in beam seas, upper container tier twistlock shear, harbor gantry crane loading in sudden wind shear, cell guide alignment friction.",
        "example_elements": ["ultra-large container vessel (ULCV)", "feeder container ship", "quayside container gantry", "twistlock corner casting", "lashing bridge frame"],
        "camera_styles": ["fixed lashing bridge security camera", "stationary quay gantry CCTV", "forward bay observation camera"],
    },
    "commercial_storm_fishing": {
        "title": "Açık Deniz Ticari Balıkçılık (Rough Sea Commercial Fishing)",
        "guidance": "Stern trawler hauling cod nets in heavy following seas, crab boat pot launch line snag on icy decks, factory ship fish processing conveyor surge.",
        "example_elements": ["North Sea stern trawler", "Bering Sea crab vessel", "pelagic longliner", "trawl winch warp wire", "aft ramp floodgate"],
        "camera_styles": ["fixed trawl deck CCTV", "stationary gallows surveillance camera", "protective wheelhouse window camera"],
    },
    "harbor_pilotage_and_berthing": {
        "title": "Liman Kılavuzluğu & Dar Kanal Manevraları (Pilotage & Harbor Tug Ops)",
        "guidance": "Pilot boat coming alongside rolling ship in swell, harbor tug bow fender compression against quay, bow thruster turbulence near shallow canal banks.",
        "example_elements": ["harbor pilot boat", "maneuver escort tugboat", "narrow canal freighter", "Yokohama pneumatic dock fender", "quayside concrete bollard"],
        "camera_styles": ["fixed quay security camera", "stationary pilot boarding station CCTV", "tugboat wheelhouse mast camera"],
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
}


def get_creative_catalyst(recent_history: list[str] | None = None) -> dict:
    """
    Geniş denizcilik ilham alanlarından birini seçer, 56 senaryoluk DeepMyster
    fikir kütüphanesini ve son 30 günün canlı geçmişini birleştirerek
    GPT-4o için zengin yaratıcı katalizör bağlamı üretir.
    """
    if recent_history is None:
        recent_history = []

    domain_keys = list(MARITIME_INSPIRATION_DOMAINS.keys())
    random.shuffle(domain_keys)

    chosen_key = domain_keys[0]
    for key in domain_keys:
        if not any(key in h.lower() for h in recent_history):
            chosen_key = key
            break

    domain = MARITIME_INSPIRATION_DOMAINS[chosen_key]

    # Mevcut fikir kütüphanesinden örnekleri derle (GPT'ye ton/örnek olarak iletmek için)
    library_samples = []
    for cat_key, cat_data in DEEPMYSTER_EXISTING_IDEAS_LIBRARY.items():
        sample = random.choice(cat_data["reference_scenarios"])
        library_samples.append(f"[{cat_data['title']}]: {sample}")

    catalyst = {
        "domain_id": chosen_key,
        "domain_title": domain["title"],
        "guidance": domain["guidance"],
        "example_elements": domain["example_elements"],
        "camera_styles": domain["camera_styles"],
        "existing_library_reference": library_samples,
        "recent_history": recent_history[-20:],  # Son 20 konuyu canlı negatif liste olarak ver
    }

    log.info(f"🎲 Yaratıcı Denizcilik Katalizörü Seçildi: [{chosen_key}] {domain['title']}")
    return catalyst


# ─────────────────────────────────────────────────────────────────────────────
# 🤖 KATMAN 2: GPT SENARYO YÖNETMENİ — System Prompt
# ─────────────────────────────────────────────────────────────────────────────

SCENARIO_WRITER_SYSTEM_TEMPLATE = """You are the master director and physical maritime incident specialist for "DeepMyster" — capturing authentic, high-tension, real-world nautical incidents as if filmed by real observers: a fixed security/CCTV camera, a bystander's handheld phone, or a chase-POV camera from a nearby vessel.

## CORE DIRECTIVE:
You have FULL CREATIVE AUTONOMY to invent a unique, realistic <<DURATION>>-second physical maritime incident.
The footage MUST be 100% understandable on a SILENT SCREEN within the first 2-3 seconds.

## CAMERA PERSPECTIVE (ASSIGNED PER SCENE):
The user prompt assigns ONE of three realistic camera perspectives for this scene: a fixed-mount security/CCTV camera, bystander/passenger handheld phone footage, or a chase/pursuit POV from a nearby vessel. Write the "observer_camera" field and the scene itself to match the assigned perspective exactly. NEVER use fisheye/GoPro-style distortion or drone/aerial-only framing unless the assigned perspective is specifically an elevated dockside or marina tower camera.
For onboard deck, pool, or vehicle-deck scenes, the fixed camera may be mounted ON the ship looking at its own deck/interior spaces — visible deck architecture, railings, or vehicle-deck structure establishes the ship without needing an exterior hull/bow shot.

## VESSEL VARIETY (ROTATE ACROSS TYPES):
Draw the vessel from the FULL range of realistic sea vessels — cruise/passenger ships, ferries, Ro-Ro vehicle carriers, general cargo ships, container ships, tankers, tugboats/rescue boats, yachts/powerboats in marina settings, and other realistic commercial or recreational vessels. Rotate across these types across generations — do NOT let any single vessel type dominate repeatedly.

## INCIDENT VARIETY (NON-EXHAUSTIVE — INVENT FREELY WITHIN THIS RANGE):
Incidents may include, but are not limited to: a yacht or powerboat losing control near a marina, a passenger ship or ferry closing dangerously on people waiting at a dock, mechanical failures, cargo shifts, collisions, mooring line failures, storm damage, and other genuine maritime physical crises. Always maritime/vessel-based — never an unrelated non-maritime setting.

## EXISTING IDEAS LIBRARY & BRAND UNIVERSE (INSPIRATION & ANTI-REPETITION):
You are provided with samples from DeepMyster's 71-topic reference library.
- THESE SAMPLES DEFINE OUR BRAND'S HIGH-TENSION REALISTIC MARITIME REALITY.
- DO NOT copy or mechanically rehash these exact scenarios by merely swapping ship names or minor nouns.
- INSTEAD: Use them as an inspiration springboard to understand our universe, identify unchartered maritime operations (ice operations, drydock mechanics, heavy cargo crane dynamics, high-sea pilotage, etc.), and EXTRAPOLATE completely novel, authentic physical incidents that expand the channel's horizons.

## RECENT PRODUCTION HISTORY (STRICT DO NOT REPEAT):
Review the recent topics list provided in the user prompt. DO NOT repeat the exact same vessel type, incident mechanism, or setting from recent productions.

## STORY & PHYSICAL REALITY STANDARDS:
1. PURE PHYSICAL DRAMA: Grounded in real maritime physics, hydrodynamics, friction, weight shifts, weather, or mechanical loads.
2. NO INVISIBLE/INTERNAL ISSUES: No underwater rudders, no internal computer glitch, no unseen engine failures. The crisis MUST be visible in front of the camera.
3. CONTEXTUAL HUMAN ROLES: Include natural maritime personnel appropriate for the scene (e.g. helmsman at bridge console, deckhand securing rigging, winch operator, dockworkers taking cover, or crane operator). Do NOT shoehorn cartoonish actions; keep movements authentic.
4. SINGLE CONTINUOUS <<DURATION>>-SECOND TAKE: No drone acrobatics, no multi-angle movie cuts. One unbroken realistic industrial or eyewitness camera view. The scenario must describe ONE single peak moment — the worst instant of the incident — not a sequence of events spread across time. visible_start is what the camera sees at second 0; visible_consequence is what naturally follows in that same continuous shot, never a later scene or separate outcome that would need a time jump or cut to show.
5. CONCRETE PHYSICAL OUTCOME: The <<DURATION>>th second must show a visible change of state (e.g. line locks under stopper, water drains through scuppers, mass settles against barrier, fender halts vessel momentum).
6. CONSTANT HIGH ACTION (NON-NEGOTIABLE): Every scenario must depict something ACTIVELY breaking, colliding, flooding, swinging, or in danger, unfolding in real time. NEVER a calm, static, or purely observational moment — motion must read as fluid, fast, and genuinely dangerous, matching real bystander-filmed maritime incident footage, not a staged or slow-moving shot.
7. AUTHENTIC CLOTHING & RAW WEATHER (NON-NEGOTIABLE): Crew, staff, and marina personnel must wear authentic maritime PPE — high-visibility orange, red, or yellow foul-weather gear, wetsuits, or work coveralls. NEVER stark white hazmat or astronaut-style suits, including in arctic/polar scenes (use realistic red or orange polar immersion suits instead). Passengers, boat owners, guests, and vehicle drivers/occupants are NOT crew — dress them in ordinary civilian clothing appropriate to the setting: swimwear, casual/resort wear, or sun hats for pool/deck scenes; regular casual clothing for car-deck scenes; yacht-casual or resort wear for marina scenes. NEVER put civilians in hi-vis PPE. Weather and lighting must read as raw and natural — real overcast, fog, or rain grain, never glossy, overly clean, or cinematically polished; avoid mirror-smooth CGI-looking water or movie-trailer lighting.

## OUTPUT FORMAT (STRICT JSON):
{
  "vessel_class": "Specific real-world vessel class (e.g. Arctic Stern Trawler, 140m Ro-Pax Ferry, Heavy Tugboat, Ocean Cruise Liner, Luxury Motor Yacht)",
  "incident_type": "Short 3-5 word label of the physical crisis",
  "scenario_summary": "One clear, punchy sentence explaining the crisis, physical dynamics, and resolution",
  "visible_start": "Exactly what the camera sees at second 0 — the incident already at its peak moment, not a calm lead-in (vessel motion, sea condition, initial tension)",
  "physical_movement": "The core kinetic/mechanical movement and human response (<<EARLY>>-<<LATE>>s)",
  "visible_consequence": "What naturally follows in that SAME continuous shot by <<DURATION>>s — the direct physical result of visible_start/physical_movement, NOT a later scene, new camera angle, or separate outcome that would require a time jump or cut to show",
  "observer_camera": "Specific realistic camera perspective matching the assigned archetype for this scene (e.g. fixed forecastle CCTV, bystander's handheld phone from the railing, chase POV from a coast guard boat)",
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
# ✂️ KATMAN 3: PROMPT SİMPLİFİYER (SEEDANCE 2 MINI: 25–45 KELİME)
# ─────────────────────────────────────────────────────────────────────────────

PROMPT_SIMPLIFIER_SYSTEM_TEMPLATE = """You are a Seedance 2 Mini prompt engineer for DeepMyster documentary maritime videos.
Your ONE job: Convert the maritime scenario into a HIGH-SIGNAL, PHOTOREALISTIC prompt of EXACTLY 25 TO 45 WORDS following the <<DURATION>>-second single-take standard.

## DOĞUKAN METODOLOJİSİ ("Less is More"):
- Seedance 2 Mini needs clear, high-signal, descriptive visual language without cinematic fluff or robotic checklists.
- Single continuous <<DURATION>>-second take from the assigned realistic camera perspective (fixed CCTV, bystander handheld, or chase POV).
- Raw, authentic lighting (overcast daylight, storm lighting, industrial port lights).

## DIVERSE STRUCTURAL STYLES (Use varied sentence structures — DO NOT copy the same grammar):

✅ Style 1 (Event & Kinetic Action):
"A towering green swell crashes over the bow of an arctic stern trawler, swamping the foredeck as a deckhand braces against the winch housing. Seawater violently rushes through freeing ports into the foam." (33 words)

✅ Style 2 (Perspective & Heavy Mass Shift):
"High-angle bridge wing CCTV captures a bulk carrier rolling sharply in cross-seas, causing the heavy hatch cover crane to roll along its deck rails until slamming firmly against emergency rubber end-stops." (31 words)

✅ Style 3 (Mechanical Tension & Friction):
"During high-wind docking maneuvers, an industrial towing winch drum slips under sudden surge load, sending sparks and white smoke from the brake band before locking tight against the stopper." (29 words)

✅ Style 4 (Atmospheric & Cargo Shift):
"An island freight catamaran lists in heavy harbor chop, shifting a palletized cargo crate across the slick vehicle deck until wedged securely against the steel ramp coaming." (27 words)

## STRICT RULES:
1. LENGTH: EXACTLY 25 TO 45 WORDS.
2. NO TIMESTAMPS / NO HEADERS: No 'Shot 1', '(0-<<DURATION>>s)', 'Scene 1'.
3. NO CAMERA/LIGHTING TAGS: Do NOT end the prompt with a camera or lighting description (e.g. no 'Fixed CCTV camera, raw overcast footage.'). Camera and lighting are appended automatically afterward — focus entirely on the physical scene, action, and outcome.
4. PRESERVE REALISM DETAILS: Keep authentic PPE colors for crew (orange/red/yellow gear, wetsuits, coveralls — never white hazmat suits) and ordinary civilian clothing for passengers/guests/drivers (never hi-vis PPE on civilians), and raw natural weather exactly as described in the scenario. Do not sanitize, glamorize, or make water/ice/lighting look glossy or CGI-clean.

## OUTPUT FORMAT (STRICT JSON):
{
  "prompt": "The exact 25-45 word prompt",
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
    "Crew/staff wear high-visibility orange, red, or yellow foul-weather gear or "
    "work coveralls, never white hazmat suits (even in polar scenes, use "
    "red/orange immersion suits). Passengers, boat owners, guests, and vehicle "
    "occupants wear ordinary civilian clothing appropriate to the setting "
    "(swimwear, resort or casual wear, sun hats for pool/deck scenes; regular "
    "casual clothing for car-deck scenes) — never hi-vis PPE on civilians. Raw "
    "natural overcast/fog/rain lighting, not glossy or CGI-clean water or ice."
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
