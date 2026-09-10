from __future__ import annotations

"""
Creative Engine — "DeepMyster" Yaratıcı Senaryo & Komplikasyonlu Olay Örgüsü Motoru.

5 Aşamalı Mikro-Hikâye Sistemi (Komplikasyonlu):
  1. HOOK (1–3 sn): Olay doğrudan başlar. Olağandışı başlangıç ("Ne oluyor?").
  2. OLAY (3–7 sn): Tehlike/sorun netleşir, mürettebat fiziksel müdahale başlatır.
  3. TIRMANIŞ / KOMPLİKASYON (7–12 sn): İlk müdahale yetersiz kalır veya yeni bir risk doğar ("Şimdi ne olacak?").
  4. KRİTİK AN (12–15 sn): Sonucu belirleyen son saniye hamlesi veya kritik fiziksel manevra.
  5. SONUÇ / PAYOFF (Son 3–5 sn): Görsel ve fiziksel somut netice (hasar, kurtarma, rota değişimi).

Temel Kural:
  "BU VİDEODA TAM OLARAK NE OLDU VE VİDEONUN SONUNDA NE DEĞİŞTİ?"
  (Fiziksel durumdaki değişim net olarak gösterilmek zorundadır.)
"""
import random
import logging

log = logging.getLogger("CreativeEngine")

# ────────────────────────────────────────
# 🌊 KATMAN 1: DEEPMYSTER KOMPLİKASYONLU OLAY SEED HAVUZLARI (8 KATEGORİ)
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
            "Violent swell snaps primary trailer lashing; deckhands attempt to hook emergency chain but the hook slips as the truck lurches toward companionway, forcing the crew to dive and jam heavy steel chocks under tires just before hull breach.",
            "Storm surge lifts Ro-Ro ramp as a vehicle skids sideways; the primary tow cable snaps, but the dock marshal rapidly catches the secondary safety arresting strap and anchors it to deck bollard inches from the water.",
            "Bow visor hydraulic lock blows during 35ft wave impact; primary emergency valve jams with water rushing in, forcing the chief officer to manually sledgehammer the secondary mechanical locking pin into place.",
            "Shifting freight container pins cargo forklift; rolling swell tilts forklift toward open deck railing, but deck crew cuts the forklift safety cage with hydraulic shears and pulls driver clear before next wave hits.",
            "Passenger vehicle slides across slick ramp in gale; marshal's throw line misses axle, forcing second crewman to drop a heavy rubber ramp wedge directly under moving front wheel.",
            "Straining stern ramp cable snaps on vehicle ferry; secondary winch motor stalls under load, forcing deckhands to trigger manual gravitational emergency brake stops.",
            "Cargo trailer lurch snaps safety chain and blocks scupper drain; water accumulates rapidly on vehicle deck until boatswain hacks drain grate clear with prybar, releasing trapped floodwater.",
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
            "Sudden squall snaps yacht bow line; marina staff drops a standard fender but it pops under extreme hull pressure, forcing safety boat to ram in with an oversized heavy-duty pneumatic buffer right as fiberglass grazes concrete piling.",
            "Stuck throttle propels yacht toward marina fuel dock; skipper cuts main ignition but boat coasts on inertia toward pumps, forcing dockmaster to trip emergency master fuel shutoff and kick a floating tire buffer between dock and bow.",
            "Marina pontoon cleat tears loose in storm surge; crew throws mooring line to adjacent slip but rope snags on cleat horn, forcing second dockhand to leap onto tilting pontoon and tie off directly to steel pile guide.",
            "Aft deck fire ignites near shore power cable; first powder extinguisher runs empty with flames spreading toward canvas cover, forcing response crew to drag seawater hose and blast foam directly onto battery box.",
            "Drifting superyacht sideswipes marina berths in gale; safety boat's towline parts under tension, forcing skipper to execute full-throttle lateral shove against yacht flank, deflecting bow clear of docked boats.",
            "Yacht anchor drags toward shallow breakwater rocks; bow thruster stalls from weed ingestion, forcing deckhand on bow to drop emergency secondary kedge anchor just before keel strikes reef.",
            "Tidal surge wedges yacht swim platform under dock finger; pneumatic jack slips off wet timber, forcing dockhands to use heavy prybars and shift boat ballast to dislodge stern.",
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
            "Commuter ferry loses port thruster approaching pier; captain drops starboard anchor but chain jumps windlass gear, forcing emergency full reverse throttle on remaining engine to arrest momentum meters from quay wall.",
            "Wave surge dislodges passenger gangway; dockhand grabs railing but handrail weld cracks under weight, forcing second crewman to lasso gangway bridge frame and heave it onto solid concrete dock.",
            "Heavy mooring hawser snaps violently under surge; snapping tail whips toward dock crew who dive behind concrete bollard as recoiling cable smashes dock light stanchion.",
            "Surge wave sweeps passenger catamaran toward terminal pilings; primary bumper fender tears off, forcing deck crew to drop backup inflatable foam cushions and tighten stern spring line.",
            "Excursion boat engine stalls in strong crosscurrent; tow line thrown from pilot boat falls short into churning water, forcing pilot boat to pace alongside and make direct hull-to-hull push into slip.",
            "Boarding gate latch fails as ferry lists; safety barrier swings open toward water, forcing deck officer to tackle passenger back to deck and latch backup heavy steel chain.",
            "Ferry bow strikes wooden dolphin in gale; wooden fender shatters on impact, forcing terminal crew to trigger emergency pneumatic dock brakes to absorb secondary hull rebound.",
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
            "Container ship suffers rudder lock in narrow harbor; lead tugboat attempts straight reverse pull but towline snaps with flying spray, forcing assist tug to ram ship port quarter and shove bow away from gantry crane.",
            "Bulk carrier drifts toward anchored tanker in squall; port anchor drops but fails to hold on muddy bottom, forcing pilot to drop starboard anchor with full chain brake tension to halt drift thirty meters away.",
            "Cargo freighter bow brushes pier wall in crosscurrents; bow thruster stalls under overload, forcing watch officer on bridge wing to drop anchor brake and swing vessel stern clear of container stacks.",
            "Tugboat towline snags on giant bulbous bow; emergency quick-release hook jams under tension, forcing tug deckhand to sever synthetic line with rescue axe right before tug gets swamped.",
            "Industrial freighter propulsion fails near bridge piers; harbor tug applies full lateral push but loses traction, forcing second tug to hook stern bridle and execute synchronized pivot.",
            "Forward mooring wire parts on container ship; loose cable whips into forecastle winch, forcing boatswain to engage emergency manual dog clutch and brake drum before ship drifts into fairway.",
            "Harbor pilot boat swamped by giant wake during boarding; pilot ladder bottom rung tears away, forcing deckhand to catch pilot safety harness and haul him onto pilot boat foredeck.",
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
            "Massive 45-foot rogue wave smashes forward hatch cover; boatswain crawls on lifeline to latch dogs but secondary wave knocks tool loose, forcing him to secure dogs with backup steel ratchet strap.",
            "Rolling bulk carrier suffers shifted container stack; primary turnbuckle snaps under strain, forcing deckhands in gale to loop heavy wire lashing around adjacent container frame to halt cascade.",
            "Green water shatters forward wheelhouse safety window; electronic throttle console shorts out from saltwater, forcing captain to switch to auxiliary mechanical telegraph in aft bridge wing.",
            "Trawler net snags propeller in cross-seas; crew cuts winch cable but trailing rope wraps shaft, forcing mechanic to lock shaft brake and drift on sea anchor to prevent engine stall.",
            "Offshore supply vessel dynamic positioning fails in 40ft seas; manual twin-screw throttle lags, forcing bridge crew to deploy bow thruster surge and steer bow directly into crest.",
            "Forecastle deck railing bends under wave impact trapping companionway door; deckhand uses emergency fire axe to wedge door open, allowing flooded deck water to drain through scuppers.",
            "Freezing spray locks trawler wheelhouse wipers and freeing ports; deckhand with de-icing mallet slips on ice but catches safety rail, then knocks free freeing port ice to drain deck.",
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
            "Bank suction pulls container ship stern toward rocky bank; hard-over rudder counter-action fails to break suction, forcing pilot to order full emergency burst on bow thruster to pop stern into channel.",
            "Dense fog blinds freighter approaching breakwater; lookout spots rocky groin at 50 meters and calls warning, but helm response is sluggish, forcing captain to dump full port rudder and drop port anchor to pivot away.",
            "Cargo ship brushes submerged sandbank; ballast pump valve sticks during deballasting, forcing engineers to manually hand-crank emergency sea chest valve to lighten ship draft.",
            "Salvage tug fights tidal eddy at harbor entrance; tow bridle bridle shackle bends under lateral load, forcing crew to quickly hook backup towing strap before barge swings toward rocks.",
            "Oil tanker experiences steering lag at channel bend; primary steering pump alarms sound, forcing helmsman to activate emergency auxiliary steering gear to complete channel turn.",
            "Cross-tide sweeps freighter toward navigation buoy; thruster burst stalls initially from aeration, forcing captain to gun main engine ahead and blow propeller wash past buoy.",
            "Harbor inlet breakers threaten to broach inbound ship; stern takes heavy quartering wave lifting rudder, forcing captain to apply sudden reverse throttle to restore water bite.",
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
            "Deckhand swept against safety netting by breaking wave; rescue swimmer reaches him but swimmer's tether snags on deck cleat, forcing boatswain to cut snag with knife so swimmer can haul seaman to superstructure.",
            "Listing fishing boat takes on water; transfer hose from rescue cutter kinks and stops pump suction, forcing cutter crew to throw secondary submersible electric pump to stabilize vessel list.",
            "Helicopter hoist cable snags on pitching mast during evacuation; winch cable tensions dangerously, forcing deck officer to cut guide line with rigging shears, freeing cable for safe hoist lift.",
            "Seaman trapped in flooded companionway; hydraulic spreader slips on greased door frame, forcing damage control team to wedge timber baulks and pry hatch open on second attempt.",
            "Distressed sailboat drifts toward breaking reef; first thrown line misses deck in howling wind, forcing salvage tug to maneuver into wave trough and launch rocket-propelled line to secure tow.",
            "Emergency life raft painter line tangles on sinking trawler rigging; boatswain cuts snagged painter with knife just as raft begins getting dragged underwater, allowing raft to surface.",
            "Injured crewman stretcher slides on waterlogged deck; forward tie-down snaps, forcing two teammates to throw their bodies across stretcher to pin it until bridge turns ship into wind.",
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
            "Engine room main cooling pipe bursts spraying steam; isolation valve handwheel shears off, forcing chief engineer to grab heavy pipe wrench and manually twist valve stem shut before boiler overheat.",
            "Ship suffers blackout near rocky shoreline; emergency generator auto-start fails due to air lock, forcing electrician to manually bleed diesel injector and crank generator in darkness.",
            "Hydraulic steering cylinder blows under heavy rudder load; bridge manual helm spins freely with vessel drifting toward shoals, forcing crew to rush aft steering flat and engage emergency hand pump.",
            "Bow thruster stalls while docking in high crosswinds; boatswain drops port anchor but brake band slips, forcing crew to apply auxiliary friction clamp to arrest chain run.",
            "Engine room turbocharger catches fire; primary CO2 pull cable snaps, forcing engineer to race to local release cabinet and manually pull secondary gas cylinder pins.",
            "Fuel leak sprays hot exhaust manifold; automatic deluge valve fails to trip, forcing mechanic to trigger manual foam canister directly onto fire source.",
            "Steering gear jams 25 degrees starboard in shipping lane; emergency tiller linkage binds, forcing bridge to use differential twin-screw propeller thrust to steer vessel straight.",
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
    """Benzersiz bir DeepMyster 5 aşamalı ve komplikasyonlu deniz olayı seed'i üretir."""
    if used_combos is None:
        used_combos = []

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
                        "animal": vessel,          # Geriye dönük uyumluluk
                        "talent": incident,        # Geriye dönük uyumluluk
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
# 🤖 KATMAN 2: GPT SENARYO ÜRETİCİ — 13 KRİTERLİ & KOMPLİKASYONLU 5-SHOT MİKRO-HİKÂYE
# ────────────────────────────────────────

SCENARIO_WRITER_SYSTEM = """You are the lead maritime scenario writer and director for "DeepMyster" — a realistic documentary YouTube Shorts channel dedicated to authentic maritime incidents, ship emergencies, oceanic storms, critical maneuvering, and active crew survival/operations.

YOUR MISSION: Create a captivating, physically realistic 15-second MINI-NARRATIVE (Micro-Story) structured into EXACTLY 5 CONTINUOUS SHOTS × 3 SECONDS (Total 15s) with a rigorous cause-and-effect progression, active human participation, and AT LEAST ONE REAL COMPLICATION.

The viewer MUST experience this progression:
"What is happening?" (0-3s Hook) → "What will happen next?" (3-9s Incident & Escalation with Complication) → "What physically changed in the end?" (9-15s Critical Move & Concrete Visual Payoff).

## 1. MANDATORY 5-SHOT × 3-SECOND FLOW (EXACTLY 15 SECONDS):
- SHOT 1 / 0–3s — HOOK: Incident is ALREADY in progress from frame 1 in media res. No calm sea, no establishing landscape shot, no passive atmosphere. An unusual concrete physical event MUST be immediately visible.
- SHOT 2 / 3–6s — INCIDENT & CREW ACTION: The danger/mechanism becomes clear. Crew/personnel ACTIVELY & PHYSICALLY intervene (diving, hauling, jamming, steering, latching). Incident continues.
- SHOT 3 / 6–9s — ESCALATION & UNEXPECTED COMPLICATION: STRICT RULE: REJECT SIMPLE 1-STEP FIXES! The initial intervention fails, a tool slips, a line snaps, danger changes direction, or a secondary risk emerges, forcing an urgent tactical shift.
- SHOT 4 / 9–12s — CRITICAL MOMENT: Decisive physical move, high-stakes maneuver, or emergency decision that determines the outcome. Peak of danger. Camera clearly frames the critical physical action.
- SHOT 5 / 12–15s — RESOLUTION / PAYOFF: Concrete physical outcome MUST happen VISUALLY on screen (e.g. vessel trajectory deflected, runaway equipment locked, impact absorbed by buffer, flood drained). Hypothetical/invisible "they were saved" is STRICTLY FORBIDDEN.

## 2. STORY CAUSALITY (NEDEN-SONUÇ ZİNCİRİ):
Every shot MUST be the physical consequence of the previous shot:
CAUSE → ACTION → CONSEQUENCE → COMPLICATION → CRITICAL ACTION → RESULT.
Internal Check: "What happened in the previous shot, and why is this shot its direct physical consequence?" If unclear, FAIL.

## 3. OBJECT / CHARACTER / ENVIRONMENT CONTINUITY:
Strict continuity throughout the 15s:
- Same vessel, same crew members, same clothes/gear, same equipment, same location, same weather/sea conditions, same timeline.
- No teleportation, no duplicated objects, no suddenly appearing gear, no disappearing people.

## 4. STORY-DRIVEN CAMERA SYSTEM (STORY → ACTION → CAMERA):
- NEVER select cameras just to look "cinematic". The camera is chosen solely to show the critical physical action in the clearest way.
- Internal Question: "What is the single most important physical information the viewer needs to see in this shot?"
- Match physical recording sources (phone camera, witness camera, ship-mounted bridge cam, quayside CCTV, deckhand bodycam, harbor security cam, pilot boat tracking cam). A CCTV camera cannot fly like a drone; a phone camera cannot be in impossible mid-air.
- STRICTLY FORBIDDEN: Random aerials, random orbits, random close-ups, random camera switches that hide physical action or add no story information.

## 5. ACTIVE HUMAN / CREW PARTICIPATION RULE:
- Crew / personnel MUST be active physical participants of the crisis (hauling lines, fighting helm, deploying buffers, using tools). Passive background standing is FORBIDDEN.

## 6. WHAT HAPPENED & WHAT CHANGED RULE:
- Answer explicitly: "What exactly happened in this video and what physically changed by the end?" (e.g. "Cargo trailer lashing snapped on rolling ferry deck; initial hook slipped, but deckhands dove to jam steel chocks under tires, locking the truck 2 feet before hull collision.")

## 7. NO-SPOILER TITLE RULE:
- Title MUST focus solely on the CRISIS and DANGER (max 50 chars). NEVER reveal the resolution (e.g. use "⚠️ Runaway Freight Truck Slides on Ferry Deck" instead of "Crew Stops Truck").

## OUTPUT FORMAT (STRICT JSON):
{
  "scenario_title": "Crisis-focused title without spoiling resolution (max 50 chars)",
  "what_happened_and_what_changed": "Concrete physical explanation of what happened, the complication, and what physically changed on screen",
  "story_arc": {
    "hook_seconds_0_3": "Shot 1 (0-3s): In media res shocking start of the crisis with visible physical event",
    "incident_seconds_3_6": "Shot 2 (3-6s): Clear mechanism of danger and active physical crew intervention",
    "escalation_and_complication_seconds_6_9": "Shot 3 (6-9s): Complication, failed first attempt, or secondary risk escalating tension",
    "critical_moment_seconds_9_12": "Shot 4 (9-12s): Decisive high-stakes physical maneuver/action at peak of danger",
    "resolution_seconds_12_15": "Shot 5 (12-15s): Visible physical change/outcome on screen"
  },
  "camera_plan": {
    "shot_1_camera": "Recording source (e.g. CCTV / Bodycam / Bridge cam) + framing rationale for 0-3s",
    "shot_2_camera": "Recording source + framing rationale showing crew action for 3-6s",
    "shot_3_camera": "Recording source + framing rationale showing complication for 6-9s",
    "shot_4_camera": "Recording source + framing rationale showing critical move for 9-12s",
    "shot_5_camera": "Recording source + framing rationale showing visible payoff for 12-15s"
  },
  "scenes": [
    {
      "scene_number": 1,
      "description": "Continuous 15-second physical action covering all 5 shots (Hook -> Incident -> Complication -> Critical Action -> Physical Payoff) with strict continuity",
      "duration": 15
    }
  ],
  "quality_self_check_13": {
    "1_strong_hook_0_3s": {"pass": true, "reason": "Specific reason why hook starts in media res without establishing shot"},
    "2_clear_problem_3_6s": {"pass": true, "reason": "Specific reason why the danger mechanism is clear"},
    "3_active_crew_physical_action": {"pass": true, "reason": "Specific reason showing active physical crew intervention (not passive)"},
    "4_genuine_escalation": {"pass": true, "reason": "Specific reason how tension escalates"},
    "5_unexpected_complication_6_9s": {"pass": true, "reason": "Specific complication or failed first attempt described"},
    "6_critical_moment_9_12s": {"pass": true, "reason": "Specific decisive physical maneuver described"},
    "7_visible_physical_resolution_12_15s": {"pass": true, "reason": "Specific visual physical outcome described"},
    "8_clear_what_changed_physically": {"pass": true, "reason": "Specific physical state change before vs after"},
    "9_strict_shot_continuity_and_causality": {"pass": true, "reason": "Specific explanation of cause-and-effect continuity"},
    "10_unpredictable_curiosity_maintained": {"pass": true, "reason": "Specific reason why viewer remains in suspense until payoff"},
    "11_no_spoiler_in_title": {"pass": true, "reason": "Specific confirmation that title has no resolution spoiler"},
    "12_complete_micro_narrative": {"pass": true, "reason": "Specific confirmation of complete micro-story structure"},
    "13_story_driven_camera": {"pass": true, "reason": "Specific explanation of how camera choice serves physical story information"}
  },
  "scenario_summary": "One punchy sentence summarizing crisis, complication, and payoff",
  "total_duration": 15,
  "clip_count": 1
}"""


# ────────────────────────────────────────
# ✂️ KATMAN 3: SEEDANCE 2 MINI PROMPT SPECIALIST (5 SHOT × 3S STANDARD)
# ────────────────────────────────────────

PROMPT_SIMPLIFIER_SYSTEM = """You are a Seedance 2 Mini (bytedance/seedance-2-fast) prompt engineer for "DeepMyster".
Your ONE job: convert a 5-stage maritime micro-story into a HIGHLY DYNAMIC, KINETIC, 5-SHOT CONTINUOUS ACTION prompt for Seedance 2 Mini.

## CRITICAL SEEDANCE 2 MINI 5-SHOT FORMAT:
1. STRUCTURE (5 SHOTS × 3 SECONDS = 15 SECONDS):
   Each shot MUST clearly express: CAMERA + SUBJECT + ACTION + CAUSE/CONTINUITY + IMMEDIATE CONSEQUENCE + DIEGETIC AUDIO.
2. DURATION: Exactly 15 seconds continuous progression.
3. WORD COUNT: 35-55 WORDS in a single tight, cohesive prompt narrative covering the 5 shots chronologically.
4. FORBIDDEN WORDS: steal, theft, crime, arrest, gun, weapon, violence, blood, kill, drugs, glowing, magical, mystical, sci-fi, fantasy, anime, cgi, 3d render.
5. PHOTOREALISM: End with 'Photorealistic raw documentary footage, natural lighting, diegetic environmental audio' or 'Rugged bodycam footage, natural physics, ambient sounds'.

## PROMPT STRUCTURE FORMULA:
"SHOT 1 (0-3s): [Camera source + in-media-res incident + audio]. SHOT 2 (3-6s): [Crew physical action + audio]. SHOT 3 (6-9s): [Complication / failed attempt + audio]. SHOT 4 (9-12s): [Decisive critical maneuver + audio]. SHOT 5 (12-15s): [Visible physical payoff / locked outcome + audio]. Photorealistic raw documentary footage, natural lighting."
OR a tightly integrated chronological single-flow prompt incorporating all 5 shot stages seamlessly.

## EXAMPLES:
✅ "SHOT 1 (0-3s): Handheld bridge camera frames cargo trailer snapping lashings on rolling ferry deck with loud metallic snap. SHOT 2 (3-6s): Deckhands scramble across flooded steel plates with emergency chain. SHOT 3 (6-9s): Hook slips under load as trailer pivots toward companionway. SHOT 4 (9-12s): Deckhands dive and jam heavy steel chocks under front tires. SHOT 5 (12-15s): Chocks bite firmly into deck, locking trailer two feet before hull impact. Photorealistic raw documentary footage, natural lighting, ambient storm audio."
✅ "SHOT 1 (0-3s): Quayside CCTV captures sudden squall snapping yacht bow line in churning harbor. SHOT 2 (3-6s): Marina staff sprint and deploy inflatable fender against piling. SHOT 3 (6-9s): Fender pops under massive hull surge as boat drifts toward fuel dock. SHOT 4 (9-12s): Safety boat accelerates full-throttle and makes lateral push against yacht flank. SHOT 5 (12-15s): Thrust deflects yacht bow five meters clear into open slip. Photorealistic documentary camera footage, natural lighting."

## OUTPUT FORMAT (STRICT JSON):
{
  "prompt": "The complete chronological 5-shot prompt (35-55 words) detailing Shot 1 through Shot 5 with camera, action, complication, and visual payoff",
  "word_count": 48,
  "complication_included": "Brief description of the complication in Shot 3",
  "physical_outcome_included": "Brief description of the visual physical outcome in Shot 5"
}"""


# ────────────────────────────────────────
# 📺 YOUTUBE METADATA — Merak & No-Spoiler
# ────────────────────────────────────────

YOUTUBE_METADATA_SYSTEM = """You create YouTube Shorts metadata for "DeepMyster" — realistic documentary channel focusing on intense nautical incidents and ship emergencies.

CRITICAL TITLE RULES:
- The title MUST focus on the CRISIS and DANGER, NOT the resolution/outcome (NO SPOILERS!).
- NEVER write "Saved by...", "Fixed by...", or give away the ending in the title.
- NEVER start the title with "DeepMyster:", "DeepMyster -", "[DeepMyster]", or any channel prefix.
- Title: MAX 55 characters. Compelling, authentic, with 1-2 relevant emoji (🌊, 🚢, 🛥️, ⚓, ⛈️, 🛟, ⚠️).
- Everything in ENGLISH.

DESCRIPTION RULES:
- 2-3 realistic sentences describing the dramatic crisis, the escalating danger, and the intense crew struggle + #DeepMyster #Shorts #Maritime #RoughSeas. English only.
- Tags: 8-12 relevant tags.

GOOD TITLE EXAMPLES (TENSION / NO SPOILER):
✅ "⚠️ Runaway Superyacht Drifts Out of Control in Storm #Shorts"
✅ "🌊 40ft Rogue Wave Hits Ferry Deck Shifting Heavy Cargo #Shorts"
✅ "🚢 Container Ship Suffers Steering Lock Near Harbor Crane #Shorts"
✅ "🛟 Deckhand Caught on Flooded Foredeck as Towline Parts #Shorts"
✅ "⚓ Commuter Ferry Loses Engine Control Approaching Pier #Shorts"

OUTPUT FORMAT (STRICT JSON):
{
  "youtube_title": "Tense crisis-focused title without spoilers (max 55 chars, NO channel name prefix)",
  "youtube_description": "2-3 authentic sentences detailing the crisis and intense struggle",
  "tags": ["DeepMyster", "Shorts", "Maritime", "RoughSeas", "CargoShip", "Storm", "Ocean", "Crew", "Rescue"]
}"""

