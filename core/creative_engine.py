from __future__ import annotations

"""
Creative Engine — "DeepMyster" Yaratıcı Senaryo Motoru.

3 Katmanlı Sistem:
  Katman 1: 8 Genişletilmiş Denizcilik Kategorisi + Bağlamsal Gemi/Vessel + Lokasyon + Kamera + Mürettebat/İnsan seed havuzu
  Katman 2: GPT-4o ile gerçekçi, fizik kurallarına uygun deniz olayı senaryosu üretimi
  Katman 3: Seedance-optimize basit ve fotogerçekçi prompt'a dönüştürme (PROMPT_SIMPLIFIER_SYSTEM)

Kalıcı Kurallar:
- ZORUNLU İNSAN / MÜRETTEBAT KURALI: Her videoda mutlaka en az bir insan/mürettebat görünmelidir.
  İnsansız video kesinlikle üretilmez. İnsanlar yalnızca arka planda duran figüranlar değil,
  senaryoya uygun şekilde krizin, manevranın, tehlikenin veya kurtarmanın aktif parçasıdır.
- ROL & KAMERA ÇEŞİTLİLİĞİ: İnsanın olay içindeki rolü (kaptan, zabit, güverte personeli,
  yolcular, marina personeli, liman çalışanları, kurtarma ekipleri, gemi mühendisleri) her videoda
  farklılaştırılır; tekrar eden insan/kamera şablonlarından kaçınılır.
- 8 Kritik Kategori: Ro-Ro kazaları, Yat marinaları, Yolcu iskeleleri, Liman çarpışmaları,
  Açık deniz fırtınaları, Kanal/giriş tehlikeleri, Acil müdahale/kurtarma, Makine/dümen arızaları.
- Ham Belgesel Estetiği: Fotogerçekçi, sinematik, gerçek kamera/bodycam/CCTV hissi.
- Başlık: Otomatik 'DeepMyster:' öneki ASLA kullanılmaz, doğrudan olayı anlatan doğal başlıklar üretilir.
"""
import random
import logging

log = logging.getLogger("CreativeEngine")

# ────────────────────────────────────────
# 🌊 KATMAN 1: DEEPMYSTER SEED HAVUZLARI (8 KATEGORİ)
# ────────────────────────────────────────

MARITIME_CATEGORIES = {
    "roro_accidents": {
        "label": "Ro-Ro ve Arabalı Gemi Kazaları & Olayları",
        "vessels": [
            "large car and passenger ferry",
            "heavy Ro-Ro vehicle carrier",
            "coastal vehicle freight ferry",
            "high-speed passenger-car catamaran",
            "island commuter car ferry",
        ],
        "incidents": [
            "car ferry rolling violently in heavy swells as deck crew in yellow foul weather gear battle to lash shifting trucks on open vehicle deck",
            "heavy Ro-Ro vehicle carrier surging at loading ramp while dock staff frantically guide disembarking cars through storm chop",
            "deckhands scrambling across wet flooded vehicle deck to hook emergency heavy chains on sliding freight trailers in severe gale",
            "ferry captain and navigation officers urgently correcting thrusters as open bow visor takes pounding oceanic waves",
            "passengers gripping safety handrails on rolling high-speed catamaran while deck crew members secure storm gates in rough seas",
            "commercial Ro-Ro freight crew working together on pitching stern ramp to secure loose vehicle lashings in severe swell",
            "island car ferry crew directing vehicles while surge waves wash across lower loading ramp during emergency departure",
        ],
        "settings": [
            "on the rolling vehicle cargo deck of a ferry in heavy open seas with deckhands in high-visibility suits",
            "at an exposed ferry terminal slip with dockworkers and crew managing storm surge",
            "in a turbulent strait crossing with passengers and crew bracing against steep breaking chop",
            "approaching a concrete Ro-Ro loading ramp amidst surging ocean swells with ramp marshals active",
        ],
    },
    "marina_incidents": {
        "label": "Yat Marinaları ve Marina Acil Durumları",
        "vessels": [
            "luxury motor yacht",
            "large private superyacht",
            "high-performance powerboat",
            "twin-engine luxury cabin cruiser",
            "marina safety response boat",
        ],
        "incidents": [
            "marina dock staff frantically sprinting along floating pontoon to deploy heavy inflatable fenders as runaway yacht approaches luxury slips",
            "yacht captain and deckhand on bow desperately throwing mooring lines to marina crew during sudden storm surge",
            "marina staff using long boat hooks to fend off drifting luxury yacht slamming toward wooden pontoons in sudden harbor squall",
            "private yacht skipper fighting jammed throttle near fuel dock while marina dockworkers wave emergency warnings",
            "marina emergency response crew in safety gear rushing along pontoon with fire hoses toward smoking yacht aft deck",
            "dockmaster and marina personnel securing straining cleat lines as violent storm surge lifts floating pontoons with tilting boats",
            "marina safety boat crew maneuvering in close quarters to intercept drifting powerboat before it hits concrete breakwater",
        ],
        "settings": [
            "at a crowded luxury yacht marina during sudden violent storm surge with dock staff active on pontoons",
            "beside floating marina dock pontoons with marina crew managing rolling boats amidst steep harbor chop",
            "near a marina fuel dock with emergency personnel bracing as turbulent surge pushes vessels",
            "at a private marina basin exposed to incoming gale squalls with boat owners and staff securing lines",
        ],
    },
    "passenger_terminals": {
        "label": "Yolcu İskeleleri ve Feribot Terminalleri",
        "vessels": [
            "commuter passenger ferry",
            "large passenger catamaran",
            "double-ended passenger ferry",
            "coastal excursion vessel",
            "harbor passenger water taxi",
        ],
        "incidents": [
            "ferry captain working thruster levers as commuter ferry slams hard against pier wooden fender dolphins in strong harbor surge",
            "deck crew securing swaying boarding gangway as passengers grip safety handrails over churning water",
            "terminal dockworkers jumping back as heavy mooring line snaps violently under high tension in gale winds",
            "ferry deckhands throwing heavy heaving lines to terminal dockworkers amidst turbulent wave surge",
            "passengers on open upper deck bracing against railings as ferry captain executes emergency turn away from pier wall",
            "terminal dock staff rushing to secure double-cleated lines from pitching passenger vessel in breaking waves",
            "deck officers guiding passengers away from spray-swept boarding gate as heavy swell pushes catamaran against terminal pilings",
        ],
        "settings": [
            "at an active passenger ferry terminal with dockworkers and deck crew managing turbulent wave chop",
            "alongside a concrete passenger pier with passengers holding handrails and deckhands securing lines",
            "at a crowded waterfront ferry landing with terminal staff managing pitching commuter vessels during severe gusts",
            "at an island passenger dock with local crew assisting disembarkation amidst sudden breaking waves",
        ],
    },
    "harbor_collisions": {
        "label": "Liman İçi Gemi Çarpışmaları ve Manevralar",
        "vessels": [
            "massive container ship",
            "heavy ocean bulk carrier",
            "large crude oil tanker",
            "commercial harbor tugboat",
            "industrial cargo freighter",
        ],
        "incidents": [
            "bridge officers and harbor pilot tensely coordinating emergency reverse thrust on container ship near quayside crane",
            "commercial tugboat crew managing straining hawser towline as drifting bulk carrier bow slides dangerously close in heavy gale",
            "cargo ship captain and watch officer on bridge wing shouting emergency orders as vessel drifts toward anchored tanker",
            "harbor pilot boat crew skillfully pacing alongside massive cargo vessel as harbor pilot boards via pilot ladder in rough water",
            "container ship deck crew on forecastle preparing emergency anchor drop as ship drifts toward concrete berth sea wall",
            "tugboat deckhands securing heavy towing bridle while flanking giant maneuvering freighter in turbulent propeller wash",
            "quayside dockworkers and crane operators reacting from berth as approaching cargo freighter suffers rudder stall",
        ],
        "settings": [
            "inside a busy industrial seaport basin with harbor pilots and bridge teams actively maneuvering",
            "alongside an active container terminal quay with dockworkers and deckhands managing gale surges",
            "in a congested harbor turning basin with tugboat crews coordinating emergency vessel position",
            "between industrial shipping berths with deck watchmen signaling maneuvering giant vessels",
        ],
    },
    "rough_seas_storms": {
        "label": "Açık Deniz Fırtınaları ve Dev Dalgalar",
        "vessels": [
            "massive container ship",
            "ocean bulk carrier",
            "deep sea fishing trawler",
            "heavy crude oil tanker",
            "rugged offshore supply vessel",
        ],
        "incidents": [
            "bridge officers inside ship wheelhouse bracing as massive 45-foot wave crashes over cargo forecastle deck",
            "deckhands in high-visibility foul weather gear holding safety lifelines across waterlogged deck of rolling bulk carrier",
            "ship captain and helmsman gripping steering consoles as green seawater floods forward bridge windows in towering swell",
            "deep sea fishing trawler crew in heavy oilskins battling freezing spray to haul deck gear in violent cross-seas",
            "offshore supply vessel crew monitoring dynamic positioning thruster consoles during 40-foot hurricane swells",
            "cargo ship deck crew inspecting lashing turnbuckles on shifted container stacks between relentless ocean waves",
            "freighter bridge team watching in tension as bow plunges deep underwater before surging through dense sea foam",
        ],
        "settings": [
            "in the storm-tossed open North Atlantic Ocean with bridge crew on high alert under dark skies",
            "in deep oceanic waters with deckhands navigating flooded companionways amidst 40-foot gray-green swells",
            "along a treacherous offshore shipping lane with watch officers monitoring radar and violent wave impacts",
            "in the frigid sub-arctic ocean with trawler crew working on ice-sprayed deck amidst massive waves",
        ],
    },
    "channel_navigation": {
        "label": "Kanal ve Liman Giriş-Çıkış Tehlikeleri",
        "vessels": [
            "massive container ship",
            "ocean cargo vessel",
            "heavy oil tanker",
            "commercial salvage tugboat",
            "harbor pilot boat",
        ],
        "incidents": [
            "ship captain and harbor pilot urgently spinning rudder controls to counter severe shallow water bank suction in narrow shipping canal",
            "bridge watch officers on open bridge wing scanning narrow rocky breakwater inlet through dense sea fog and breaking swells",
            "tanker deck watchmen on bow signaling distance to rocky shallow banks during turbulent tidal surge",
            "commercial salvage tugboat crew executing full-power lateral pull to keep drifting freighter in center of narrow channel",
            "harbor pilot climbing ship rope ladder while deckhands assist and steady him amidst violent channel chop",
            "freighter bridge team coordinating bow thrusters and engine orders to squeeze past narrow rocky harbor choke point",
            "cargo vessel lookout crew on forecastle calling warnings as ship brushes shallow sandbank in turbulent crosscurrents",
        ],
        "settings": [
            "in a narrow industrial shipping canal with bridge officers and pilot tensely steering past concrete sea walls",
            "at a treacherous rocky harbor inlet with deck watchmen monitoring violent breaking cross-swells",
            "navigating a narrow dredged harbor channel with tugboat crews and helmsmen maintaining course",
            "entering an exposed seaport breakwater channel with bridge crew navigating gale warnings",
        ],
    },
    "emergency_rescue": {
        "label": "Mürettebat Acil Müdahale ve Kurtarma Operasyonları",
        "vessels": [
            "rugged coast guard rescue cutter",
            "deck crew on pitching cargo ship",
            "commercial salvage tugboat",
            "offshore supply vessel with rescue craft",
            "deep sea trawler crew in survival gear",
        ],
        "incidents": [
            "deck crew in bright orange foul weather gear rushing across flooded deck to deploy portable emergency bilge pumps",
            "coast guard rescue boat crew launching rigid inflatable craft into violent breaking surf to reach vessel in distress",
            "ship officers on open bridge wing scanning dark storm waves with high-power searchlights to guide rescue swimmers",
            "deckhands working together against howling gale to retrieve damaged heavy towing gear and secure deck safety lines",
            "rescue swimmer descending from helicopter hoist cable onto pitching vessel deck as deck crew signals guidance",
            "crew members in immersion survival suits launching emergency life raft from listing vessel side into turbulent ocean",
            "salvage tugboat deck crew throwing emergency rescue lines and life rings to seamen on waterlogged deck",
        ],
        "settings": [
            "on the spray-drenched forecastle deck with crew battling towering oceanic waves in survival gear",
            "near an exposed coastal reef with coast guard rescue crew operating in turbulent breaking surf",
            "on the pitching aft deck of a rescue vessel with team members executing operations in dark storm conditions",
            "along the flooded main deck of a listing cargo vessel with seamen coordinating emergency evacuation",
        ],
    },
    "machinery_failures": {
        "label": "Makine, Dümen ve Sistem Arızaları",
        "vessels": [
            "ship captain and bridge officers in wheelhouse",
            "marine engineers in ship engine room",
            "heavy bulk carrier crew with jammed rudder",
            "ocean cargo freighter deck officers in blackout",
            "tugboat and vessel emergency response team",
        ],
        "incidents": [
            "ship captain and helmsman fighting manual emergency steering wheel in wheelhouse as vessel drifts toward rocky breakwater",
            "marine engineers in boiler suits rushing through vibrating engine room to isolate blown hydraulic steering pipe",
            "electrical engineer resetting main switchboard breakers under emergency red backup lighting during violent storm blackout",
            "bridge officers and lookouts reacting to sudden bow thruster failure as crosswinds push vessel toward concrete pier",
            "deckhands and boatswain dropping emergency anchor on forecastle deck as cargo ship suffers complete propulsion loss",
            "chief engineer and mechanics working frantically on jammed steering gear actuator as storm waves batter the hull",
            "bridge crew tensely monitoring flickering backup radar consoles as emergency generator takes load in heavy seas",
        ],
        "settings": [
            "inside the ship bridge wheelhouse with captain and officers managing alarms and stormy seas outside",
            "inside the ship engine control station with engineers responding to flashing red warning indicators",
            "on the forward anchor deck with deckhands securing emergency anchor windlass near rocky coast",
            "in a congested harbor fairway with bridge team sounding emergency whistle as propulsion stalls",
        ],
    },
}

CAMERA_PERSPECTIVES = [
    "raw handheld documentary camera footage capturing crew action and vessel motion",
    "ship bridge wheelhouse camera looking past captain and controls out to violent forward deck",
    "rugged bodycam worn by deck crew member battling waves and securing deck gear",
    "quayside CCTV surveillance camera recording dockworkers and incoming vessel drama",
    "forecastle deck action camera drenched in flying sea spray showing deckhands in hi-vis gear",
    "harbor watchtower telephoto lens documentary footage capturing crew maneuvering vessel",
    "pilot boat tracking camera moving alongside vessel showing crew on deck",
    "marina pontoon camera recording marina staff sprinting with fenders as yacht approaches",
    "engine room surveillance camera capturing marine engineers rushing to emergency consoles",
    "dramatic low-angle quayside camera capturing dockworkers managing heavy lines near giant hull",
]

CREW_CONTEXTS = [
    "Deckhands in bright high-visibility foul weather gear actively battle sea spray to secure equipment and chains",
    "Ship captain and bridge officers in the wheelhouse tensely maneuver throttles and emergency steering controls",
    "Marina dock staff on pontoons frantically sprint to deploy heavy inflatable fenders for runaway yacht",
    "Port dockworkers and line handlers on the quay manage high-tension mooring ropes during dangerous maneuver",
    "Passengers and crew grip safety rails on rolling deck, reacting with urgency to severe pitch and roll",
    "Emergency rescue crew or coast guard swimmers in survival suits actively execute critical crisis response",
    "Marine engineers in boiler suits frantically repair machinery under flashing emergency warning lights",
    "Harbor pilot and tugboat crew execute critical coordinated maneuvers in turbulent churning water",
    "Lookout watch officers on bridge wing scan stormy swells with searchlights and binoculars",
]

DYNAMICS_TEMPLATES = [
    "deck crew braces hard against safety handrails as a massive wave crashes over the forecastle bow",
    "captain works emergency controls as the vessel rolls sharply into a deep wave trough",
    "marina staff deploy fenders just in time as foamy surge water pushes the vessel sideways",
    "deckhands scramble across spray-washed steel plates to secure loose cargo before the next swell hits",
    "dockworkers on the pier jump back as high-tension mooring line snaps with flying sea spray",
    "passengers grip railings tightly while crew guides them during sudden violent vessel yaw",
    "engineers fight heavy vibrations as backup emergency power kicks in amidst severe hull roll",
    "rescue crew pulls equipment aboard rigid inflatable boat amidst towering whitecaps",
    "bridge officers brace against console as green water floods over the forward windows",
]


def generate_creative_seed(used_combos: list[str] | None = None) -> dict:
    """
    Benzersiz bir DeepMyster deniz olayı + gemi + çevre + kamera + mürettebat kombinasyonu üretir.
    8 kategori arasında dengeli rotasyon yapar ve tekrarları önler.
    Her seed mutlaka aktif bir insan / mürettebat bağlamı içerir.
    Geriye dönük uyumluluk için animal/talent anahtarlarını da taşır.
    """
    if used_combos is None:
        used_combos = []

    # Kategorileri karıştırarak her kategoriden zengin kombinasyonlar oluştur
    categories_keys = list(MARITIME_CATEGORIES.keys())
    random.shuffle(categories_keys)

    all_combos = []
    for cat_key in categories_keys:
        cat_data = MARITIME_CATEGORIES[cat_key]
        for incident in cat_data["incidents"]:
            for vessel in cat_data["vessels"]:
                combo_key = f"{cat_key}|{vessel}|{incident}"
                if combo_key not in used_combos:
                    all_combos.append({
                        "vessel": vessel,
                        "incident": incident,
                        "animal": vessel,          # Geriye dönük prompt_generator uyumluluğu
                        "talent": incident,        # Geriye dönük prompt_generator uyumluluğu
                        "category": cat_key,
                        "category_label": cat_data["label"],
                        "combo_key": combo_key,
                        "settings_pool": cat_data.get("settings", []),
                    })

    if not all_combos:
        log.warning("⚠️ Tüm DeepMyster kombinasyonları kullanılmış — geçmiş sıfırlanıyor")
        for cat_key in categories_keys:
            cat_data = MARITIME_CATEGORIES[cat_key]
            for incident in cat_data["incidents"]:
                for vessel in cat_data["vessels"]:
                    all_combos.append({
                        "vessel": vessel,
                        "incident": incident,
                        "animal": vessel,
                        "talent": incident,
                        "category": cat_key,
                        "category_label": cat_data["label"],
                        "combo_key": f"{cat_key}|{vessel}|{incident}",
                        "settings_pool": cat_data.get("settings", []),
                    })

    chosen = random.choice(all_combos)
    
    # Kategoriye özel veya genel havuzdan uyumlu lokasyon seç
    if chosen.get("settings_pool"):
        chosen["setting"] = random.choice(chosen["settings_pool"])
    else:
        chosen["setting"] = "in rough open sea passage with deck crew battling relentless waves lashing across the hull"
    
    chosen["twist"] = random.choice(DYNAMICS_TEMPLATES)
    chosen["camera_perspective"] = random.choice(CAMERA_PERSPECTIVES)
    chosen["crew_context"] = random.choice(CREW_CONTEXTS)

    log.info(
        f"🎲 DeepMyster Seed: [{chosen['category_label']}] "
        f"{chosen['vessel']} × {chosen['incident'][:40]}... "
        f"| Cam: {chosen['camera_perspective'][:30]}... "
        f"| Crew: {chosen['crew_context'][:30]}..."
    )

    return chosen


# ────────────────────────────────────────
# 🤖 KATMAN 2: GPT SENARYO ÜRETİCİ — System Prompt
# ────────────────────────────────────────

SCENARIO_WRITER_SYSTEM = """You are the lead maritime scenario writer and director for "DeepMyster" — a realistic documentary YouTube Shorts channel dedicated to authentic maritime incidents, ship accidents, storms, rough seas, critical maneuvering emergencies, and crew survival/operations.

YOUR GOAL: Create a completely UNIQUE, REALISTIC, single-scene maritime scenario based on the provided seed. Avoid repetitive clichés. Every video must feel like a brand-new real-world maritime event captured on camera.

## CRITICAL SCENARIO RULES:
1. 100% REALISTIC & PHYSICALLY PLAUSIBLE: Real hydrodynamics, authentic ship behaviors, natural ocean wave physics, and realistic environmental effects.
2. MANDATORY HUMAN / CREW PRESENCE (STRICT - ZERO TOLERANCE FOR UNMANNED VIDEOS):
   - Every single video MUST prominently feature at least one human or crew member (e.g., captain, deckhand, bridge officer, dockworker, marina staff, passenger, rescue swimmer, or marine engineer).
   - CREWLESS / UNINHABITED VIDEOS ARE STRICTLY FORBIDDEN.
   - Humans must NOT be passive background props; they must be natural, active participants in the incident (managing controls, securing gear, handling lines, bracing against waves, responding to alarms, guiding passengers, or executing rescue operations).
3. ROLE & CAMERA DIVERSITY (NO REPETITIVE TEMPLATES):
   - The human role and camera perspective MUST vary across videos: alternate between wheelhouse captains/officers, deckhands battling storm spray on lifelines, marina staff deploying fenders on pontoons, quay dockworkers dodging snapping lines, passengers gripping safety rails, engine room engineers fixing failures, and rescue teams launching boats.
   - Avoid repetitive human or camera templates. Each video must have a unique perspective and dynamic human engagement.
4. EXPANDED INCIDENT DOMAINS:
   - Ro-Ro & Car Ferry emergencies (cargo shift, ramp swells, heavy rolls, vehicle deck crew).
   - Luxury yacht marina emergencies (surges, loose moorings, pontoon collisions, marina staff).
   - Passenger docks & ferry terminals (hard fender impacts, gangway sway, mooring snaps, dockworkers & passengers).
   - Harbor ship collisions & tight maneuvering near-misses (bridge pilots, tug crews, line handlers).
   - Heavy oceanic storms, 40ft swells, and green water flooding decks (deckhands on lifelines, bridge officers).
   - Port/canal/inlet navigation hazards (bank suction, crosscurrents, breakwater surges, lookout watch).
   - Crew emergency interventions (lashing loose cargo, emergency bilge pumping, rescue boat launch).
   - Mechanical/steering/engine blackout failures (engineers in engine room, captain on manual wheel).
5. NO DIALOGUE, NO TEXT OVERLAYS, NO NARRATION: Tension is 100% visual, kinetic, and atmospheric.
6. AUDIO: Ambient ocean roar, wind howling, wave impacts, metal creaking, engine rumble, warning alarms (if applicable).
7. ONE CONTINUOUS 15-SECOND SHOT: Single seamless, dramatic shot.

## OUTPUT FORMAT (STRICT JSON):
{
  "scenario_summary": "One clear sentence describing the unique realistic maritime incident with the active human role",
  "scenes": [
    {
      "scene_number": 1,
      "description": "Realistic visual description of the vessel, active human/crew actions, and environmental dynamics (2-3 sentences)",
      "duration": 15
    }
  ],
  "total_duration": 15,
  "clip_count": 1,
  "why_this_clip_count": "Single continuous 15-second dramatic documentary shot featuring active human presence"
}"""


# ────────────────────────────────────────
# ✂️ KATMAN 3: PROMPT SİMPLİFİYER — System Prompt
# ────────────────────────────────────────

PROMPT_SIMPLIFIER_SYSTEM = """You are a Seedance 2.0 video prompt specialist for "DeepMyster". Your ONE job: convert a detailed maritime scene description into a SHORT, SIMPLE video generation prompt.

## CRITICAL RULES:
1. OUTPUT MUST BE 15-30 WORDS MAXIMUM. Strict limit.
2. MANDATORY HUMAN / CREW PRESENCE: Every prompt MUST explicitly include at least one human/crew member (e.g. deckhand, captain, dockworker, passenger, marina staff, rescue crew, engineer) actively involved in the kinetic action. Unmanned / crewless prompts are strictly forbidden.
3. Focus on the primary human/crew action interacting with the vessel and maritime elements.
4. Use SIMPLE, DIRECT language. No flowery poetic descriptions.
5. Include ONE key visual detail (wave spray, shifting cargo, gangway, snapping line, or flashing bridge consoles).
6. End with a strict realism style hint (e.g., 'photorealistic, raw documentary camera footage, natural lighting', 'rugged bodycam footage, natural motion', 'quayside CCTV camera footage'). NEVER mention the video duration in the prompt.
7. NEVER include dialogue or spoken words.
8. NEVER use these forbidden words: steal, theft, crime, arrest, gun, weapon, violence, blood, attack, kill, fight, drugs, police, cop, glowing, magical, mystical, artifact, runes, sci-fi, fantasy, obsidian, anime, cgi, 3d render, cartoon, illustration.
9. The output MUST look like REAL, amateur or professional documentary camera footage.

## GOOD EXAMPLES:
✅ "A large car ferry rolls heavily in 30-foot swells as deck crew in yellow gear lash shifting vehicles. Photorealistic, raw documentary footage, natural lighting."
✅ "Marina staff sprint along floating pontoon deploying heavy fenders as runaway luxury yacht drifts in storm surge. Realistic CCTV camera footage."
✅ "Commercial tugboat deckhands manage straining hawser line while pulling a giant container ship in rough harbor swells. Photorealistic action camera footage."
✅ "Ship captain and officers in wheelhouse urgently fight manual steering wheel during sudden storm blackout. Alarms flashing. Raw documentary bridge camera footage."
✅ "Deck crew in orange survival suits secure snapped mooring chains on pitching cargo ship forecastle as waves crash over deck. Rugged bodycam footage."
✅ "Ferry passengers grip safety handrails while deck officer secures swinging gangway amidst violent harbor wave chop. Raw handheld documentary footage."

## OUTPUT FORMAT (STRICT JSON):
{
  "prompt": "The simplified 15-30 word prompt",
  "word_count": 22
}"""


# ────────────────────────────────────────
# 📺 YOUTUBE METADATA — System Prompt
# ────────────────────────────────────────

YOUTUBE_METADATA_SYSTEM = """You create YouTube Shorts metadata for "DeepMyster" — a realistic maritime documentary channel dedicated to extreme rough seas, ship incidents, and oceanic storms.

Given the video scenario, create an engaging, authentic title, description, and tags.

CRITICAL TITLE RULES:
- The title MUST directly describe the dramatic maritime event naturally, engagingly, and realistically.
- NEVER start the title with "DeepMyster:", "DeepMyster -", "DeepMyster |", "[DeepMyster]", or any channel name prefix.
- The title must focus directly on what happens in the scene (e.g. "Massive Waves Catch Cargo Ship at Harbor Entrance #Shorts", "Runaway Yacht Hits Marina Dock in Storm Surge #Shorts", "Deck Crew Battles Flooded Bow in 40ft Seas #Shorts").
- Title: MAX 60 characters. Compelling, natural, and realistic with relevant emoji (🌊, 🚢, 🛥️, ⚓, ⛈️, 🛟, ⚠️).
- Everything in ENGLISH (for global audience).

DESCRIPTION & TAGS RULES:
- Description: 2-3 realistic sentences about the maritime event + #DeepMyster #Shorts #Maritime. English only.
- Tags: 8-12 relevant tags (e.g., DeepMyster, Shorts, Maritime, RoughSeas, CargoShip, Storm, Ocean, Waves, Marina, Ferry, Crew).
- Include "DeepMyster" in tags.
- Include "Shorts" in tags.

TITLE STYLE EXAMPLES (NATURAL, NO CHANNEL PREFIX):
✅ "🌊 Cargo Ship Battles Massive 40ft Storm Waves #Shorts"
✅ "🛥️ Runaway Yacht Slams Marina Dock in Storm Surge #Shorts"
✅ "🚢 Ro-Ro Ferry Vehicle Deck Floods in Rough Seas #Shorts"
✅ "⚓ Passenger Ferry Hits Pier Dolphins in Harbor Gale #Shorts"
✅ "🛟 Deck Crew Secures Snapped Line in Violent Storm #Shorts"
✅ "⚠️ Container Ship Near-Miss at Harbor Channel #Shorts"

OUTPUT FORMAT (STRICT JSON):
{
  "youtube_title": "Natural compelling title with emoji (max 60 chars, NEVER starting with 'DeepMyster')",
  "youtube_description": "Authentic 2-3 sentence description",
  "tags": ["DeepMyster", "Shorts", "Maritime", "RoughSeas", "CargoShip", "Storm", "Ocean", "Crew"]
}"""
