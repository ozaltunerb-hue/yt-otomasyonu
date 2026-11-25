# ⭐ Hit kalıbı (12 Kas 2026, Bahadır). Hesap düşüşte; sadece hit seviyesinde (9/10) video isteniyor. Hit videoyu üreten
# gerçek Kie prompt'unun ÇERÇEVESİ (kamera/kadraj cümlesi, stil ve kural cümleleri, cümle sırası, bağlaçlar) birebir;
# olaylar her basışta değişir (video kopya görünmesin).
#
# Kaynak: Notion "DeepMyster Youtube Otomasyonu" kayıtları (dashboard_data/notion_runs.json ile birebir aynı). Tarihler
# Türkiye saati (Notion UTC: -3 saat).
#
# Normal üretim yolu DEĞİŞMEZ: mod sadece Telegram "⭐ Hit kalıbı" butonundan açılır (config["hit_env"]). Seçim normal
# hattın kendisi (ortam zorlanır, T4+U11 dışlanır: es.HIT_OVERRIDE), metin burada hit kalıbına yerleştirilir. GPT yok.
import re

import core.event_structure as es

FIRE_TORNADO = es.FIRE_TORNADO

# ── Hit prompt'ları (Kie'ye giden TAM metin, birebir) ────────────────────────────────────────────────────────────────
HIT_PROMPTS = {
    # 5 Kas 2026 00:13 üretimi (T4+U11, forest_edge, çatı terası); 9/10 kilit videosu. Notion 40ed048d625e81dba114c29e14ecd258
    FIRE_TORNADO: {
        "source": "5 Kas 2026 00:13",
        "notion": "40ed048d-625e-81db-a114-c29e14ecd258",
        "combo_key": "fire_disasters|none|fire tornado tears across a burning roadside|rooftop terrace above a wooded "
                     "residential area##T4+U11|bystander_handheld",
        "prompt": (
            "0-4s: A colossal spinning fire tornado, a twisting funnel several times taller than the houses and trees, "
            "tears out of a burning forest into a residential area, its wide base engulfing the houses. Two people run "
            "away in the street below. 4-9s: The pickup truck is shoved sideways as the huge base of the fire tornado "
            "sweeps past right behind it. 9-15s: A wooden garage beside a house across the street bursts apart, "
            "burning boards spiraling up. Handheld footage filmed on a rooftop terrace above a wooded residential area, "
            "high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; "
            "slight hand shake, the camera stays fixed, an empty foreground; one continuous shot, no zoom, no cuts, no "
            "person or face close to the camera. Civilians in everyday clothes, no hazmat suits, never CGI. A rotating "
            "funnel of flame with orbiting debris, never a straight plume or explosion. Everything moves in real time, "
            "never in slow motion, people run at full speed. No readable signs, text or flags."),
        # hit'in kendi parçaları (fark satırı ve testler için)
        "parts": {"env": "forest_edge", "people": "Two people run away in the street below.", "beat_2": "T4",
                  "beat_3": "U11", "vehicle": "pickup truck"},
    },
    # 13 Eki 2026 11:23 üretimi (13 Eki 2,13M hit). KAYIT: buton şimdilik görünmez
    es.PYROCLASTIC: {
        "source": "13 Eki 2026 11:23",
        "notion": "3f8d048d-625e-8183-aee5-ea111581308e",
        "combo_key": "volcano_disasters|none|pyroclastic cloud races down into a village street|hillside terrace facing "
                     "the erupting volcano##P2+Q1|bystander_handheld",
        "prompt": (
            "0-4s: A pyroclastic cloud races down the volcano’s flank and slams into a village street. Four villagers, "
            "caught in the chaos, immediately dart away, their figures barely visible against the ashen background. "
            "4-9s: The deadly cloud crashes through, snapping street trees like twigs and toppling power poles, "
            "striking the ground with force. 9-15s: The cloud's fury intensifies, slamming into a house, its walls "
            "crumbling under pressure, debris swirling amid the advancing ash. Handheld footage shot by a person "
            "standing on a hillside terrace above the village, high vantage looking down over the village street "
            "toward the erupting volcano; slight hand shake, the camera stays fixed on the terrace, tilting down no "
            "more than slightly and never descending, the erupting volcano always visible in the upper third of the "
            "frame, a corner of the terrace railing in the foreground; one continuous shot, no zoom, no cuts. "
            "Bystanders wear civilian clothes, no hi-vis PPE; responders wear service uniforms. Raw natural light "
            "matching the weather, never glossy or CGI; no hazmat suits. No readable signs, text or flags."),
    },
    # 9 Eki 2026 21:52 üretimi (19 Eki 3,02M hit). KAYIT: buton şimdilik görünmez
    es.WILDFIRE: {
        "source": "9 Eki 2026 21:52",
        "notion": "3f4d048d-625e-81f9-a10f-eaf888802f52",
        "combo_key": "fire_disasters|none|wall of flames sweeps into a hillside neighborhood|balcony of a hillside "
                     "house##K5+L4|bystander_handheld",
        "prompt": (
            "0-4s: A towering wall of flames sweeps down the forested slope and slams into the edge of the "
            "neighborhood, igniting roofs and trees. Five people run desperately, scattering in various directions to "
            "escape the rapidly encroaching inferno. 4-9s: The white van accelerates, executing a sharp U-turn and "
            "leaves the scene, just as the flames close in behind. 9-15s: The advancing fire consumes an entire line "
            "of trees, their tops exploding into fiery embers, rising into the swirling sky. Handheld footage shot by "
            "a person standing on a balcony of a hillside house overlooking the street and the burning slope, eye "
            "level, normal lens; slight hand shake, the camera pans to follow the wall of flames; no zoom, no cuts. "
            "Bystanders wear civilian clothes, never hi-vis PPE on civilians; emergency responders wear service "
            "uniforms. Raw natural light matching the weather, never glossy or CGI; no white hazmat suits. No "
            "readable signs, text or flags."),
    },
}

# Telegram'da butonu görünen olaylar (kül bulutu ve orman metinleri kayıtlı, butonları şimdilik yok)
HIT_ACTIVE_EVENTS = (FIRE_TORNADO,)
HIT_ENVS = {FIRE_TORNADO: ("forest_edge", "tree_street", "village_woods")}
# Hit videonun kendi kurgusu: bu modda hiç seçilmez
HIT_BANNED_PAIRS = {FIRE_TORNADO: {("T4", "U11")}}
MODE_LABEL = "⭐ Hit kalıbı"

_FT = HIT_PROMPTS[FIRE_TORNADO]
# Kalıbın sabit kuyruğu: 9-15s cümlesinden sonraki her şey (kamera/kadraj cümlesi + stil ve kural cümleleri), birebir
HIT_TAIL = {FIRE_TORNADO: _FT["prompt"][_FT["prompt"].index("Handheld footage filmed on a rooftop terrace"):]}
# Hit prompt'ta olmayan, sonradan eklenen iki cümle: bu modda YOK
ADDED_LINES = {FIRE_TORNADO: ("Full action from the very first frame to the last.",
                              es.CONTINUATION_LINES[FIRE_TORNADO])}


def is_active(event: str | None) -> bool:
    return event in HIT_ACTIVE_EVENTS


def envs(event: str) -> tuple[str, ...]:
    return HIT_ENVS.get(event, ())


def override(event: str, env: str) -> dict:
    """es.HIT_OVERRIDE değeri: seçimde ortam zorlanır, hit çifti dışlanır."""
    if not is_active(event) or env not in envs(event):
        raise ValueError(f"Hit kalıbı bu olay/ortamda yok: {event} / {env}")
    return {"event": event, "fire_env": env, "banned_pairs": {event: set(HIT_BANNED_PAIRS.get(event, set()))}}


async def no_gpt(*args, **kwargs):
    raise RuntimeError("Hit kalıbında GPT çağrılmaz")


def hit_slices(event: str, slices: dict) -> dict:
    """Normal hattın birebir dilimleri; 9-15s'teki devam cümlesi (hit'te yoktu) çıkarılır."""
    cont = es.CONTINUATION_LINES.get(event)
    s3 = slices["slice_3"]
    if cont:
        if not s3.endswith(" " + cont):
            raise es.StructureError("Hit kalıbı: 9-15s devam cümlesiyle bitmiyor (beklenmeyen dilim)")
        s3 = s3[:-len(cont) - 1]
    return {**slices, "slice_3": s3}


def build_story(spec: dict, slices: dict) -> str:
    return es.assemble_story(spec, slices)


def build_prompt(event: str, story: str) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(story, HIT_TAIL[event])


def _q(text: str) -> str:
    return f"«{text}»"


def diff_lines(event: str, spec: dict, slices: dict) -> str:
    """Onay mesajı: mod satırı + hit prompt'a göre değişen parçalar (her biri ayrı satır)."""
    hit = HIT_PROMPTS[event]
    p = hit["parts"]
    env = spec.get("fire_env")
    kv_hit = es.FIRE_TOR_ENVS[p["env"]]["key"]
    s2_hit = es.beat_text(event, "slice_2", p["beat_2"], p["vehicle"])
    s3_hit = es.beat_text(event, "slice_3", p["beat_3"], p["vehicle"])
    s2_hit = s2_hit[0].upper() + s2_hit[1:] + "."
    s3_hit = s3_hit[0].upper() + s3_hit[1:] + "."
    def line(name, before, after, tag=""):
        return f"• {name}{tag}: aynı" if before == after else f"• {name}{tag}: {_q(before)} → {_q(after)}"
    return "\n".join([
        f"Mod: {MODE_LABEL} (kaynak: {hit['source']})",
        "Hit prompt'a göre değişen parçalar (kamera, kadraj, stil ve kural cümleleri birebir hit):",
        line("Açılış", kv_hit, spec["key_visual"], f" ({p['env']} → {env})"),
        line("İnsan", p["people"], slices["slice_1_rest"]),
        line("4-9s", s2_hit, slices["slice_2"], f" ({p['beat_2']} → {spec['beat_2']})"),
        line("9-15s", s3_hit, slices["slice_3"], f" ({p['beat_3']} → {spec['beat_3']})"),
        line("Araç", p["vehicle"], spec["vehicle"]),
        "• Hit'te olmayan iki cümle yok: " + " / ".join(_q(x) for x in ADDED_LINES[event]),
    ])


def apply(scene: dict, env: str) -> dict:
    """Normal hattın kurduğu sahneyi hit kalıbına çevirir (aynı seçimler, hit çerçevesi). structure["hit"] Kie öncesi
    son denetimin (submit_issues) ve yeniden yazımın kaynağıdır."""
    event = scene["event"]
    st = scene.get("structure") or {}
    spec, slices = st.get("spec"), st.get("slices")
    if not is_active(event) or not spec or spec.get("fire_env") != env:
        raise es.StructureError(f"Hit kalıbı kurulamadı: {event} / {env}")
    hs = hit_slices(event, slices)
    story = build_story(spec, hs)
    prompt = build_prompt(event, story)
    hit = {"event": event, "env": env, "source": HIT_PROMPTS[event]["source"], "slices": hs, "story": story,
           "suffix": HIT_TAIL[event], "prompt": prompt, "lines": diff_lines(event, spec, hs)}
    problems = issues({**st, "hit": hit}, {"prompt": prompt, "story": story, "style_suffix": HIT_TAIL[event]})
    if problems:
        raise es.StructureError("Hit kalıbı son denetimden geçmedi: " + "; ".join(problems))
    label = es.FIRE_TOR_ENVS[env]["label"]
    structure = {**st, "hit": hit,
                 "environment": f"Ortam: {label} ({env}) · kamera = hit kalıbı (rooftop terrace above a wooded "
                                "residential area)",
                 "story_source": f"Hikâye: kod (birebir) · {MODE_LABEL}"}
    trace = {**(scene.get("trace") or {}), "mode": "hit", "hit_source": hit["source"]}
    # 12 Kas (5): Onay görüntüsü gerçek hit parçalarını gösterir (prompt aynı)
    shown, structure["axes_line"] = _hit_display(scene, structure, hit)
    trace = {**shown, "mode": "hit", "hit_source": hit["source"]}
    return {**scene, "story": story, "style_suffix": HIT_TAIL[event], "prompt": prompt, "structure": structure,
            "trace": trace}


def issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin hit kalıbıyla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    hit, spec = structure["hit"], structure["spec"]
    event = hit["event"]
    out = []
    if spec.get("key_visual") != es.expected_key_visual(event, spec["spot"], spec.get("opening")):
        out.append("kilit görsel spec'te değişmiş")
    if spec.get("fire_env") != hit["env"]:
        out.append("ortam seçilenle aynı değil")
    if (spec["beat_2"], spec["beat_3"]) in HIT_BANNED_PAIRS.get(event, set()):
        out.append(f"hit çifti seçildi ({spec['beat_2']}+{spec['beat_3']})")
    story = build_story(spec, hit["slices"])
    prompt = build_prompt(event, story)
    if info.get("style_suffix") != HIT_TAIL[event]:
        out.append("stil eki hit kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye hit kalıbıyla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt hit kalıbıyla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    for added in ADDED_LINES[event]:
        if added in text:
            out.append(f"hit'te olmayan cümle var: {added}")
    if len(text.split()) > es.max_prompt_words(event):
        out.append(f"prompt {len(text.split())} kelime (en fazla {es.max_prompt_words(event)})")
    if len(text) > es.max_prompt_chars(event):
        out.append(f"prompt {len(text)} karakter (en fazla {es.max_prompt_chars(event)})")
    return out


# ── ⭐ Hit kalıbı · Yaklaşma ─────────────────────────────────────────────────────────────────────────────────────────
# v1 (12 Kas 2026 (3), Bahadır; 2bb750f): ortama göre açılış, "run up the street ... away from the fire tornado", 4-9s
# ateş hortumu T* havuzu ("Halfway down the street, " öneki), Y1-Y4, "A rotating funnel of flame" stil eki. PASİF KAYIT:
# v2 (aşağıda) bütün metinleri yeniden tanımladı. Silinmedi; hiçbir yol bu sözlüğü kullanmaz.
YAKLASMA_ATES_HORTUMU_V1 = {
    "openings": {
        "forest_edge": "A colossal spinning fire tornado, a twisting funnel several times taller than the houses and "
                       "trees, tears out of a burning forest at the far end of the street and advances down the street "
                       "toward the camera, its wide base engulfing the houses on both sides.",
        "tree_street": "A colossal spinning fire tornado, a twisting funnel several times taller than the houses and "
                       "trees, tears out of a burning forest at the far end of a tree-lined street and advances down "
                       "the street toward the camera, its wide base engulfing the trees and houses on both sides.",
        "village_woods": "A colossal spinning fire tornado, a twisting funnel several times taller than the houses and "
                         "trees, tears out of the burning woods at the far end of the village road and advances down "
                         "the road toward the camera, its wide base engulfing the houses on both sides.",
    },
    # village_woods'ta sonraki cümlelerde "street" yerine "road"
    "street": {"forest_edge": "street", "tree_street": "street", "village_woods": "road"},
    "long_street": {"forest_edge": "a long street", "tree_street": "a long street",
                    "village_woods": "a long village road"},
    "people": {2: "Two people run up the {street} below, away from the fire tornado.",
               3: "Three people run up the {street} below, away from the fire tornado."},
    "mid_prefix": "Halfway down the {street}, ",
    "finals": {
        "Y1": "Right below the terrace, the fire tornado reaches the nearest house and tears its roof off, burning "
              "boards spiraling up into the funnel.",
        "Y2": "Right below the terrace, the fire tornado swallows the nearest house, its whole front wall ripped away "
              "and sucked into the funnel.",
        "Y3": "Right below the terrace, the porch and upper floor of the nearest house are torn apart by the base of "
              "the fire tornado, burning planks whirling past the camera.",
        "Y4": "Right below the terrace, the fire tornado rips the backyard shed and fence of the nearest house apart, "
              "burning boards spiraling up past the camera.",
    },
    "camera": {True: "the camera turns slowly to keep the tornado in frame as it approaches",
               False: "the camera stays fixed"},
    "tail": ("Handheld footage filmed on a rooftop terrace looking straight down {long_street} into the distance, high "
             "vantage, the tornado growing larger in the frame as it approaches, top never cut off, two or three "
             "people fleeing below; slight hand shake, {camera}, an empty foreground; one continuous shot, no zoom, no "
             "cuts, no person or face close to the camera. Civilians in everyday clothes, no hazmat suits, never CGI. "
             "A rotating funnel of flame with orbiting debris, never a straight plume or explosion. Everything moves "
             "in real time, never in slow motion, people run at full speed. No readable signs, text or flags."),
    # Araç savrulması / dönmesi / takla içeren ortalar bu modda hiç seçilmez (üçü normal yolda da zaten pasif):
    # T1 araç havaya kalkar ve fırlatılır, T5 ters döner (takla), T6 araç döner. T4 ("shoved sideways") kullanılabilir.
    "excluded_mids": {"T1": "araç havaya kalkar, fırlatılır", "T5": "araç ters döner (takla)",
                      "T6": "araç döner"},
}
YAKLASMA_EVENTS = (FIRE_TORNADO,)

# ── v2 (12 Kas 2026 (4), Bahadır): coğrafya ekseni + sürekli aksiyon + yan görünüm huni + O1-O5 ortaları ───────────────
# Yaklaşma modunun TÜM metinleri yeniden tanımlandı (v1 yukarıda pasif kayıt). T* havuzu bu modda KULLANILMAZ (havuzda
# aynen duruyor, normal yol ve ⭐ Hit kalıbı değişmez). O5 (araç tek parça fırlatılır) araç savurma yasağının SADECE bu
# modda kaldırıldığı orta; başka hiçbir mod/olay/havuz bu metni görmez.
APPROACH_MODE_LABEL = "⭐ Hit kalıbı · Yaklaşma"
# Kamera: True = yaklaşan hortumu yavaşça takip eder, False = sabit (Bahadır, varsayılan True)
YAKLASMA_KAMERA_TAKIP = True
YAKLASMA_MAX_WORDS = 230
YAKLASMA_MAX_CHARS = 1400
# v1'in Y3 sığma koruması (12 Kas (3)): v2 metinleriyle bütün kombinasyonlar sınıra sığıyor, gereksiz. Pasif (False);
# açılırsa yine sınırı aşan finali aday dışı bırakır
YAKLASMA_SIGMA_KORUMASI = False
YAKLASMA_TARIF = "yan görünüm (v2)"
# Coğrafya: son YAKLASMA_GEO_BLOCK üretimin coğrafyası elenir. 5 Kas hit'i G1 sayılır: geçmişin en başına G1 işlenir
YAKLASMA_GEO_BLOCK = 3
YAKLASMA_GEO_SEED = ("G1",)
YAKLASMA_ATES_HORTUMU = {
    "geos": {
        "G1": {"name": "Kaliforniya", "forest": "a burning pine forest", "houses": "wooden suburban houses"},
        "G2": {"name": "Avustralya", "forest": "burning eucalyptus bushland",
               "houses": "tin-roofed weatherboard houses"},
        "G3": {"name": "Yunanistan", "forest": "a burning pine forest",
               "houses": "whitewashed terracotta-roofed houses"},
        "G4": {"name": "Kanada", "forest": "a burning spruce forest", "houses": "dark-roofed timber houses"},
        "G5": {"name": "Portekiz", "forest": "a burning eucalyptus forest", "houses": "tile-roofed stone houses"},
    },
    "openings": {
        "forest_edge": "A colossal fire tornado, a twisting funnel several times taller than the houses, tears out of "
                       "{forest} at the far end of the street and advances toward the camera, engulfing the {houses} "
                       "on both sides, flinging burning branches and roof shingles into the street.",
        "tree_street": "A colossal fire tornado, a twisting funnel several times taller than the houses, tears out of "
                       "{forest} at the far end of a tree-lined street and advances toward the camera, engulfing the "
                       "{houses} on both sides, flinging burning branches and roof shingles into the street.",
        "village_woods": "A colossal fire tornado, a twisting funnel several times taller than the houses, tears out "
                         "of {forest} at the far end of the village road and advances toward the camera, engulfing the "
                         "{houses} on both sides, flinging burning branches and roof shingles into the road.",
    },
    # village_woods'ta insan, orta ve stil cümlelerinde "street" yerine "road"
    "street": {"forest_edge": "street", "tree_street": "street", "village_woods": "road"},
    "long_street": {"forest_edge": "a long street", "tree_street": "a long street",
                    "village_woods": "a long village road"},
    "people": {2: "Two people run up the {street} below.", 3: "Three people run up the {street} below."},
    "action": "Burning debris rains down from the very first frame.",
    "mids": {
        "O1": "Halfway down the street, the fire tornado rips the roof off a house and a power pole crashes across "
              "the road just in front of the {vehicle}.",
        "O2": "Halfway down the street, the base of the fire tornado sweeps over the {vehicle}, shattering its windows "
              "and setting it ablaze.",
        "O3": "Halfway down the street, the fire tornado uproots a tall burning tree and slams it across the road onto "
              "the {vehicle}, crushing its hood.",
        # 12 Kas (4), Bahadır (3. seçenek): "on either side of the road" çıktı (village_woods + O4 + Y4 + takip 231 kelimeydi)
        "O4": "Halfway down the street, two houses burst into flames as the fire tornado passes between them, their "
              "roofs peeling off into the funnel.",
        "O5": "Halfway down the street, the fire tornado lifts the {vehicle} off the road and hurls it, in one piece, "
              "into the burning front yard of a house.",
    },
    "finals": {
        "Y1": "Right below the terrace, the fire tornado reaches the nearest house and tears its roof off, burning "
              "boards spiraling up into the funnel.",
        "Y2": "Right below the terrace, the fire tornado swallows the nearest house, its whole front wall ripped away "
              "and sucked into the funnel.",
        "Y3": "Right below the terrace, the porch and upper floor of the nearest house are torn apart, burning planks "
              "whirling past the camera.",
        "Y4": "Right below the terrace, the fire tornado rips the backyard shed and fence of the nearest house apart, "
              "burning boards spiraling up past the camera.",
    },
    # iki çatı/ev yıkımı art arda olmasın (Bahadır)
    "banned_pairs": {("O1", "Y1"), ("O4", "Y1")},
    "vehicle_throw_mid": "O5",
    "camera": {True: "the camera turns slowly to keep the tornado in frame", False: "the camera stays fixed"},
    "tail": ("Handheld footage filmed on a rooftop terrace looking down {long_street}, high vantage, the tornado "
             "growing larger in the frame as it approaches, top never cut off; slight hand shake, {camera}; one "
             "continuous shot, no zoom, no cuts, no face close to the camera. Civilians in everyday clothes, never "
             "CGI. Seen from the side, a tall funnel of flame narrowing toward the ground, spiral bands of fire "
             "climbing its sides, debris orbiting it; never a plume, explosion, ring or hollow eye. Real time, never "
             "slow motion, people run at full speed. No readable signs, text or flags."),
}
_YK = YAKLASMA_ATES_HORTUMU
O5_WARNING = "⚠️ Araç savurma ortası (O5): videoda aracın tek parça kalıp kalmadığını kontrol et."
_GEO_MEMORY: list[str] = []


def yaklasma_is_active(event: str | None) -> bool:
    return event in YAKLASMA_EVENTS


def yaklasma_envs(event: str) -> tuple[str, ...]:
    return tuple(_YK["openings"]) if yaklasma_is_active(event) else ()


def yaklasma_override(event: str, env: str) -> dict:
    """es.HIT_OVERRIDE değeri: ortam zorlanır (normal hattın 4-9s/9-15s seçimi bu modda atılır; ek dışlama yok)."""
    if not yaklasma_is_active(event) or env not in yaklasma_envs(event):
        raise ValueError(f"{APPROACH_MODE_LABEL} bu olay/ortamda yok: {event} / {env}")
    return {"event": event, "fire_env": env, "banned_pairs": {event: set()}}


def _st(env: str, text: str) -> str:
    return text.replace("street", "road") if _YK["street"][env] == "road" else text


def yaklasma_camera_text(follow: bool | None = None) -> str:
    return _YK["camera"][bool(YAKLASMA_KAMERA_TAKIP if follow is None else follow)]


def yaklasma_tail(env: str, follow: bool | None = None) -> str:
    return _YK["tail"].format(long_street=_YK["long_street"][env], camera=yaklasma_camera_text(follow))


def yaklasma_opening(env: str, geo: str) -> str:
    g = _YK["geos"][geo]
    return _YK["openings"][env].format(forest=g["forest"], houses=g["houses"])


def yaklasma_people(env: str, n: int) -> str:
    if n not in _YK["people"]:
        raise es.StructureError(f"{APPROACH_MODE_LABEL}: kişi sayısı 2 ya da 3 olmalı ({n})")
    return _YK["people"][n].format(street=_YK["street"][env])


def yaklasma_mid(env: str, mid: str, vehicle: str | None) -> str:
    if mid not in _YK["mids"]:
        raise es.StructureError(f"{APPROACH_MODE_LABEL}: {mid} bu modda yok (orta O1-O5)")
    return _st(env, _YK["mids"][mid]).format(vehicle=vehicle or "")


def _lru(ids: list[str], seen: list[str], rng=None) -> str:
    import random
    last = {f: max((i for i, x in enumerate(seen) if x == f), default=-1) for f in ids}
    lo = min(last.values())
    return (rng or random).choice([f for f in ids if last[f] == lo])


def yaklasma_tags(event: str, history: list[str]) -> list[str]:
    """Olay çifti geçmişi (eskiden yeniye), sadece bu modun O*+Y* kayıtları."""
    return [t for t in es.beat_history(event, history or []) if re.fullmatch(r"O\d+\+Y\d+", t)]


def yaklasma_choose_mid(event: str, history: list[str], rng=None) -> str:
    """O1-O5 arasında LRU: hiç kullanılmamış ya da en eski kullanılan orta; eşitlikte rastgele."""
    return _lru(list(_YK["mids"]), [t.split("+")[0] for t in yaklasma_tags(event, history)], rng)


def yaklasma_choose_final(event: str, history: list[str], rng=None, fits=None, mid: str | None = None) -> str:
    """Y1-Y4 arasında LRU; yasak çiftler (O1+Y1, O4+Y1) aday olmaz. fits: sığma koruması (YAKLASMA_SIGMA_KORUMASI)."""
    ids = [f for f in _YK["finals"] if (mid, f) not in _YK["banned_pairs"] and (fits is None or fits(f))]
    if not ids:
        raise es.StructureError(f"{APPROACH_MODE_LABEL}: final adayı kalmadı (orta {mid})")
    return _lru(ids, [t.split("+")[1] for t in yaklasma_tags(event, history)], rng)


def yaklasma_geo_history(records: list | None) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun coğrafyaları; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == FIRE_TORNADO and axes.get("mod") == "yaklasma"
                and axes.get("cografya") in _YK["geos"]):
            out.append(axes["cografya"])
    return out


def yaklasma_choose_geo(used: list[str] | None = None, rng=None) -> str:
    """Coğrafya: G1 (5 Kas hit'i) geçmişin başına işlenir, son YAKLASMA_GEO_BLOCK coğrafya elenir, kalanlardan rastgele.
    used: Notion geçmişi (eskiden yeniye); None ise süreç hafızası."""
    import random
    seen = list(YAKLASMA_GEO_SEED) + list(_GEO_MEMORY if used is None else used)
    blocked = set(seen[-YAKLASMA_GEO_BLOCK:])
    cands = [g for g in _YK["geos"] if g not in blocked] or list(_YK["geos"])
    return (rng or random).choice(cands)


def yaklasma_story(env: str, geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    a, b, c = es.SLICE_LABELS
    return (f"{a}: {yaklasma_opening(env, geo)} {yaklasma_people(env, people)} {_YK['action']} "
            f"{b}: {yaklasma_mid(env, mid, vehicle)} {c}: {_YK['finals'][final]}")


def yaklasma_prompt(env: str, geo: str, people: int, mid: str, vehicle: str | None, final: str,
                    follow: bool | None = None) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(yaklasma_story(env, geo, people, mid, vehicle, final), yaklasma_tail(env, follow))


def yaklasma_lines(ap: dict) -> str:
    """Onay mesajı satırları."""
    label = es.FIRE_TOR_ENVS[ap["env"]]["label"]
    text = ap["prompt"]
    lines = [
        f"Mod: {APPROACH_MODE_LABEL}",
        f"Coğrafya: {ap['geo']} {_YK['geos'][ap['geo']]['name']}",
        f"Ortam: {label} ({ap['env']})",
        f"Orta (4-9s): {ap['mid']} «{yaklasma_mid(ap['env'], ap['mid'], ap['vehicle'])}»",
        f"Final (9-15s): {ap['final']} «{_YK['finals'][ap['final']]}»",
        "Kamera: " + ("takip (yaklaşan hortumu yavaşça takip eder)" if ap["follow"] else "sabit"),
        f"Kelime: {len(text.split())} (en fazla {YAKLASMA_MAX_WORDS}) · karakter: {len(text)} "
        f"(en fazla {YAKLASMA_MAX_CHARS})",
        f"Hortum tarifi: {YAKLASMA_TARIF}",
    ]
    if ap["mid"] == _YK["vehicle_throw_mid"]:
        lines.append(O5_WARNING)
    return "\n".join(lines)


def _yaklasma_axes(js, tag: str, geo: str):
    import json
    try:
        data = json.loads(js)
    except (TypeError, ValueError):
        return js
    if isinstance(data.get("axes"), dict):
        data["axes"]["beats"] = tag
        data["axes"]["mod"] = "yaklasma"
        data["axes"]["cografya"] = geo
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def yaklasma_apply(scene: dict, env: str, history: list[str] | None = None, rng=None,
                   follow: bool | None = None, geo_used: list[str] | None = None) -> dict:
    """Normal hattın kurduğu sahneden (aynı ortam, araç, kişi sayısı) Yaklaşma prompt'u kurar. Coğrafya G1-G5 (son 3
    elenir), orta O1-O5 LRU, final Y1-Y4 LRU (yasak çiftler hariç). Normal hattın T*/U* seçimi atılır.
    structure["approach"] Kie öncesi son denetimin (submit_issues) ve yeniden yazımın kaynağıdır."""
    event = scene["event"]
    st = scene.get("structure") or {}
    spec = st.get("spec")
    if not yaklasma_is_active(event) or not spec or spec.get("fire_env") != env:
        raise es.StructureError(f"{APPROACH_MODE_LABEL} kurulamadı: {event} / {env}")
    follow = bool(YAKLASMA_KAMERA_TAKIP if follow is None else follow)
    vehicle, people = spec.get("vehicle"), spec.get("people")
    geo = yaklasma_choose_geo(geo_used, rng)
    mid = yaklasma_choose_mid(event, history or [], rng)

    def fits(f):
        p = yaklasma_prompt(env, geo, people, mid, vehicle, f, follow)
        return len(p.split()) <= YAKLASMA_MAX_WORDS and len(p) <= YAKLASMA_MAX_CHARS
    final = yaklasma_choose_final(event, history or [], rng, fits if YAKLASMA_SIGMA_KORUMASI else None, mid)
    old_tag, new_tag = es.beat_tag(spec["beat_2"], spec["beat_3"]), es.beat_tag(mid, final)
    with es._BEAT_LOCK:   # seçim anı hafızası: atılan T*+U* yerine bu üretimin gerçek çifti
        mem = es._BEAT_MEMORY.get(event, [])
        if mem and mem[-1] == old_tag:
            mem[-1] = new_tag
    _GEO_MEMORY.append(geo)
    del _GEO_MEMORY[:-12]
    story = yaklasma_story(env, geo, people, mid, vehicle, final)
    tail = yaklasma_tail(env, follow)
    prompt = yaklasma_prompt(env, geo, people, mid, vehicle, final, follow)
    ap = {"event": event, "env": env, "geo": geo, "mid": mid, "final": final, "vehicle": vehicle, "people": people,
          "follow": follow, "story": story, "suffix": tail, "prompt": prompt, "version": 2}
    ap["lines"] = yaklasma_lines(ap)
    problems = yaklasma_issues({**st, "approach": ap}, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{APPROACH_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = scene.get("combo_key", "")
    if f"#{old_tag}|" in combo:
        combo = combo.replace(f"#{old_tag}|", f"#{new_tag}|")
    label = es.FIRE_TOR_ENVS[env]["label"]
    cap_info = {**(st.get("caption_info") or {}), "opening": yaklasma_opening(env, geo),
                "beat_2": yaklasma_mid(env, mid, vehicle)[:-1], "beat_3": _YK["finals"][final][:-1]}
    structure = {**st, "approach": ap, "caption_info": cap_info,
                 "environment": f"Ortam: {label} ({env}) · coğrafya {geo} {_YK['geos'][geo]['name']} · kamera = "
                                f"{APPROACH_MODE_LABEL} (rooftop terrace, {'takip' if follow else 'sabit'})",
                 "story_source": f"Hikâye: kod (birebir) · {APPROACH_MODE_LABEL}"}
    if st.get("axes_json"):
        structure["axes_json"] = _yaklasma_axes(st["axes_json"], new_tag, geo)
    # 12 Kas (5): Onay görüntüsü gerçek Yaklaşma parçalarını ve gerçek kamerayı gösterir (prompt aynı)
    shown, structure["axes_line"] = _yaklasma_display(scene, structure, ap)
    trace = {**shown, "mode": "yaklasma", "beats": new_tag, "cografya": geo}
    out = {**scene, "story": story, "plain_story": story, "style_suffix": tail, "prompt": prompt,
           "combo_key": combo, "structure": structure, "trace": trace}
    if scene.get("axes_json"):
        out["axes_json"] = _yaklasma_axes(scene["axes_json"], new_tag, geo)
    return out


def yaklasma_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin Yaklaşma kalıbıyla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    ap = structure["approach"]
    env, out = ap["env"], []
    if ap.get("geo") not in _YK["geos"]:
        return [f"coğrafya G1-G5 değil ({ap.get('geo')})"]
    if ap["final"] not in _YK["finals"]:
        return [f"final Y1-Y4 değil ({ap['final']})"]
    if ap["mid"] not in _YK["mids"]:
        return [f"orta O1-O5 değil ({ap['mid']})"]
    if (ap["mid"], ap["final"]) in _YK["banned_pairs"]:
        return [f"yasak çift ({ap['mid']}+{ap['final']})"]
    try:
        story = yaklasma_story(env, ap["geo"], ap["people"], ap["mid"], ap["vehicle"], ap["final"])
        prompt = yaklasma_prompt(env, ap["geo"], ap["people"], ap["mid"], ap["vehicle"], ap["final"], ap["follow"])
    except es.StructureError as e:
        return [str(e)]
    if info.get("style_suffix") != yaklasma_tail(env, ap["follow"]):
        out.append("stil eki Yaklaşma kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye Yaklaşma kalıbıyla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt Yaklaşma kalıbıyla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    for added in ADDED_LINES[FIRE_TORNADO]:
        if added in text:
            out.append(f"bu modda olmayan cümle var: {added}")
    for slot in ("slice_2", "slice_3"):
        for bid in es.EVENT_BEATS[ap["event"]][slot]:
            if es.beat_text(ap["event"], slot, bid, ap["vehicle"]) in text:
                out.append(f"havuz maddesi ({bid}) var")
    if len(text.split()) > YAKLASMA_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {YAKLASMA_MAX_WORDS})")
    if len(text) > YAKLASMA_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {YAKLASMA_MAX_CHARS})")
    return out


# ── Onay görüntüsü (12 Kas 2026 (5), Bahadır): Hit kalıbı modlarında "1. Seçim", "3. Hikâye" ve "Eksenler" satırı Kie'ye
# giden GERÇEK prompt'un parçalarını ve gerçek kamerasını gösterir (normal yolun açılışı / kamera modu gösterilmez).
# Sadece görüntü: trace ve axes_line Kie prompt'una girmez (prompt metni aynı, snapshot diff 0).
def mode_display(scene: dict, structure: dict, *, mode: str, camera: str, opening: str, mid: tuple[str, str],
                 final: tuple[str, str], plain: str, axes: dict, repeat: str, vehicle: str | None = None,
                 labels: tuple[str, str, str] | None = None, spot: str | None = None,
                 weather: str = "-") -> tuple[dict, str]:
    """(trace, axes_line): mid/final = (kod, metin)."""
    trace = {**(scene.get("trace") or {}), "mode_label": mode, "mode_camera": camera, "key_visual": opening,
             "beats": f"{mid[0]}+{final[0]}", "beat_2_text": mid[1], "beat_3_text": final[1], "vehicle": vehicle,
             "story": plain, "story_words": len(plain.split()), "story_source_kind": "code",
             "story_source": f"Hikâye: kod (birebir) · {mode}", "weather": weather, "repeat_note": repeat,
             "attempts": []}
    if labels:
        trace["display_labels"] = labels
    if spot:
        trace["spot"] = spot
    line = (f"Eksenler ({mode}): " + " · ".join(f"{k}={v if v not in (None, '') else '-'}" for k, v in axes.items())
            + f"\nTekrar önleme: {repeat}")
    return trace, line


def _hit_display(scene: dict, structure: dict, hit: dict) -> tuple[dict, str]:
    spec, s = structure["spec"], hit["slices"]
    plain = " ".join([spec["key_visual"], s["slice_1_rest"], s["slice_2"], s["slice_3"]])
    camera = "sabit (hit kalıbı: the camera stays fixed; rooftop terrace above a wooded residential area)"
    axes = {"ortam": hit["env"], "araç": spec.get("vehicle"), "kişi": spec.get("people"), "orta": spec["beat_2"],
            "final": spec["beat_3"], "kamera modu": "sabit (hit kalıbı)"}
    return mode_display(scene, structure, mode=MODE_LABEL, camera=camera, opening=spec["key_visual"],
                        mid=(spec["beat_2"], s["slice_2"]), final=(spec["beat_3"], s["slice_3"]), plain=plain,
                        axes=axes, vehicle=spec.get("vehicle"),
                        spot="Rooftop terrace above a wooded residential area (hit kalıbı)",
                        repeat=f"olay çifti normal LRU (hit çifti {'+'.join(sorted(HIT_BANNED_PAIRS[FIRE_TORNADO])[0])} "
                               "hiç gelmez)")


def _yaklasma_display(scene: dict, structure: dict, ap: dict) -> tuple[dict, str]:
    env, geo = ap["env"], ap["geo"]
    mid_text = yaklasma_mid(env, ap["mid"], ap["vehicle"])
    opening = yaklasma_opening(env, geo)
    plain = " ".join([opening, yaklasma_people(env, ap["people"]), _YK["action"], mid_text, _YK["finals"][ap["final"]]])
    cam = "takip" if ap["follow"] else "sabit"
    axes = {"coğrafya": f"{geo} {_YK['geos'][geo]['name']}", "ortam": env, "araç": ap["vehicle"],
            "kişi": ap["people"], "orta": ap["mid"], "final": ap["final"], "kamera modu": cam}
    return mode_display(scene, structure, mode=APPROACH_MODE_LABEL,
                        camera=f"{cam} ({yaklasma_camera_text(ap['follow'])}); rooftop terrace, {_YK['long_street'][env]}",
                        opening=opening, mid=(ap["mid"], mid_text), final=(ap["final"], _YK["finals"][ap["final"]]),
                        plain=plain, axes=axes, vehicle=ap["vehicle"],
                        spot=f"Rooftop terrace looking down {_YK['long_street'][env]} (Yaklaşma kalıbı)",
                        repeat=f"coğrafya son {YAKLASMA_GEO_BLOCK} elendi (G1 tohum) · orta O1-O5 LRU · final Y1-Y4 "
                               "LRU (O1+Y1, O4+Y1 yasak)")


# ── ⭐ Hit kalıbı · 24 Eylül (12 Kas 2026 (5), Bahadır): dev dalga ───────────────────────────────────────────────────
# 24 Eyl hit'i (1,4M): sahil binasının yüksek balkonu, korkuluk görünür, gri kapalı gün; dalga karşıdaki dükkânların
# arkasından yükselip caddeye çöker, arabalar oyuncak gibi sürüklenir, sel kameraya doğru gelir. Hikâye tamamen koddan,
# GPT yok. Zaman etiketi (0-4s / 4-9s / 9-15s) YOK (hit prompt'ta da yoktu): bu mod kendi son denetimini kullanır,
# yapılandırılmış hattın etiket denetimi bu moda uygulanmaz. Araç sürükleme yasağı SADECE bu modda kalkar (çekirdek
# aksiyon ve F1/F2/F3); dev dalganın normal yolu ve diğer olaylar aynen. Seçim: normal hattın sahnesi (görünüm, combo
# kaydı) kurulur, metni burada değiştirilir; kayıt A*+F* olarak yazılır.
DALGA24_MODE_LABEL = "⭐ Hit kalıbı · 24 Eylül"
DALGA24_EVENTS = (es.TIDAL,)
# Kamera: True = yerinde durur, suyu izlemek için hafifçe döner; False = sabit (varsayılan True)
DALGA24_KAMERA_TAKIP = True
DALGA24_MAX_WORDS = 230
DALGA24_MAX_CHARS = 1400
DALGA24_GEO_BLOCK = 3
DALGA24_GEO_SEED = ("D1",)        # 24 Eyl hit'i D1 sayılır: ilk üretimde D1 gelmez
DALGA24_OPENING_BLOCK = 2
DALGA24_OPENING_SEED = ("A2",)    # ilk üretimde A1 gelsin
DALGA24_FINAL_BLOCK = 2
DALGA_24EYLUL = {
    "geos": {
        "D1": {"name": "İngiltere", "place": "a grey British seaside town",
               "shops": "the row of seafront shops and cafés with awnings"},
        "D2": {"name": "Portekiz", "place": "a Portuguese seaside town", "shops": "the row of tiled shopfronts and cafés"},
        "D3": {"name": "Japonya", "place": "a Japanese coastal town",
               "shops": "the row of small shops with low tiled roofs"},
        "D4": {"name": "Şili", "place": "a Chilean port town", "shops": "the row of colorful painted shopfronts"},
        "D5": {"name": "İtalya", "place": "an Italian seaside town", "shops": "the row of pastel shopfronts with balconies"},
        "D6": {"name": "Endonezya", "place": "an Indonesian coastal town",
               "shops": "the row of small shophouses with tin roofs"},
    },
    "openings": {
        "A1": {"desc": "binaların arkasından",
               "text": "A colossal tidal wave rises behind {shops} across the street in {place} and crashes over their "
                       "roofs into the street."},
        "A2": {"desc": "caddenin başından",
               "text": "A colossal tidal wave surges in from the sea at the far end of the street in {place} and rushes "
                       "down it toward the camera, between {shops} on both sides."},
    },
    "people": "People watch from the rooftops across the street while others run along the street below.",
    "core": "The wave sweeps parked cars into the storefronts; vehicles smash like toys against the windows as the "
            "surging muddy water pushes half-submerged debris down the whole street toward the camera.",
    "finals": {
        "F1": "Right below the balcony, the flood slams the cars against the building and tears away its ground-floor "
              "shopfronts.",
        "F2": "Right below the balcony, a city bus is swept off the road and carried along by the flood, crashing into "
              "the cars piled against the building.",
        "F3": "Right below the balcony, the surge rips a café terrace and its awning off the building and drags them "
              "down the street with the cars.",
        "F4": "As the whole street turns into a raging river below the balcony, a second, even bigger wave rises on the "
              "horizon.",
    },
    "camera": {True: "the camera stays in place and turns slightly to follow the water", False: "the camera stays fixed"},
    "tail": ("Handheld phone footage filmed from a high balcony of a seafront building looking along the street, the "
             "balcony railing visible in the foreground; slight hand shake, {camera}; one continuous shot, no zoom, no "
             "cuts, no face close to the camera. Civilians in everyday clothes, never CGI. Raw natural overcast light "
             "under a grey sky, never glossy or cinematic; muddy brown water with real foam and debris. Real time, "
             "never slow motion, people run at full speed. No readable signs, text or flags."),
}
_DZ = DALGA_24EYLUL
_DZ_GEO_MEMORY: list[str] = []


def dalga24_is_active(event: str | None) -> bool:
    return event in DALGA24_EVENTS


def dalga24_camera_text(follow: bool | None = None) -> str:
    return _DZ["camera"][bool(DALGA24_KAMERA_TAKIP if follow is None else follow)]


def dalga24_tail(follow: bool | None = None) -> str:
    return _DZ["tail"].format(camera=dalga24_camera_text(follow))


def dalga24_opening(geo: str, opening: str) -> str:
    g = _DZ["geos"][geo]
    return _DZ["openings"][opening]["text"].format(place=g["place"], shops=g["shops"])


def dalga24_story(geo: str, opening: str, final: str) -> str:
    """Etiketsiz hikâye (zaman etiketi yok): açılış + insan + çekirdek aksiyon + final."""
    return " ".join([dalga24_opening(geo, opening), _DZ["people"], _DZ["core"], _DZ["finals"][final]])


def dalga24_prompt(geo: str, opening: str, final: str, follow: bool | None = None) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(dalga24_story(geo, opening, final), dalga24_tail(follow))


def _block_pick(ids: list[str], seen: list[str], block: int, rng=None) -> str:
    """Son `block` üretimin değeri elenir (aday kalmazsa derinlik 1, sonra 0), kalanlardan rastgele."""
    import random
    for depth in (block, 1, 0):
        blocked = set(seen[-depth:]) if depth else set()
        left = [x for x in ids if x not in blocked]
        if left:
            return (rng or random).choice(left)
    return (rng or random).choice(ids)


def dalga24_tags(history: list[str]) -> list[str]:
    return [t for t in es.beat_history(es.TIDAL, history or []) if re.fullmatch(r"A\d+\+F\d+", t)]


def dalga24_choose_opening(history: list[str], rng=None) -> str:
    seen = list(DALGA24_OPENING_SEED) + [t.split("+")[0] for t in dalga24_tags(history)]
    return _block_pick(list(_DZ["openings"]), seen, DALGA24_OPENING_BLOCK, rng)


def dalga24_choose_final(history: list[str], rng=None) -> str:
    return _block_pick(list(_DZ["finals"]), [t.split("+")[1] for t in dalga24_tags(history)], DALGA24_FINAL_BLOCK, rng)


def dalga24_geo_history(records: list | None) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun coğrafyaları; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == es.TIDAL and axes.get("mod") == "dalga24"
                and axes.get("cografya") in _DZ["geos"]):
            out.append(axes["cografya"])
    return out


def dalga24_choose_geo(used: list[str] | None = None, rng=None) -> str:
    seen = list(DALGA24_GEO_SEED) + list(_DZ_GEO_MEMORY if used is None else used)
    return _block_pick(list(_DZ["geos"]), seen, DALGA24_GEO_BLOCK, rng)


def dalga24_lines(dz: dict) -> str:
    text = dz["prompt"]
    return "\n".join([
        f"Mod: {DALGA24_MODE_LABEL}",
        f"Coğrafya: {dz['geo']} {_DZ['geos'][dz['geo']]['name']}",
        f"Açılış: {dz['opening']} ({_DZ['openings'][dz['opening']]['desc']})",
        f"Final: {dz['final']} «{_DZ['finals'][dz['final']]}»",
        "Kamera: " + ("takip (yerinde durur, suyu izlemek için hafifçe döner)" if dz["follow"] else "sabit"),
        f"Kelime: {len(text.split())} (en fazla {DALGA24_MAX_WORDS}) · karakter: {len(text)} "
        f"(en fazla {DALGA24_MAX_CHARS})",
        "Zaman etiketi: yok (24 Eyl hit prompt'unda da yoktu)",
    ])


def _dalga24_axes(js, tag: str, geo: str):
    import json
    try:
        data = json.loads(js)
    except (TypeError, ValueError):
        return js
    if isinstance(data.get("axes"), dict):
        data["axes"]["beats"] = tag
        data["axes"]["mod"] = "dalga24"
        data["axes"]["cografya"] = geo
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def dalga24_apply(scene: dict, history: list[str] | None = None, rng=None, follow: bool | None = None,
                  geo_used: list[str] | None = None) -> dict:
    """Normal hattın kurduğu dev dalga sahnesinden (görünüm ve kayıt aynı) 24 Eylül kalıbı prompt'unu kurar. Coğrafya
    D1-D6 (son 3 elenir, D1 tohum), açılış A1/A2 (son 2 elenir, A2 tohum: ilk üretim A1), final F1-F4 (son 2 elenir).
    structure["dalga24"] Kie öncesi son denetimin (submit_issues) ve yeniden yazımın kaynağıdır."""
    event = scene["event"]
    st = scene.get("structure") or {}
    spec = st.get("spec")
    if not dalga24_is_active(event) or not spec:
        raise es.StructureError(f"{DALGA24_MODE_LABEL} kurulamadı: {event}")
    follow = bool(DALGA24_KAMERA_TAKIP if follow is None else follow)
    geo = dalga24_choose_geo(geo_used, rng)
    opening = dalga24_choose_opening(history or [], rng)
    final = dalga24_choose_final(history or [], rng)
    old_tag, new_tag = es.beat_tag(spec["beat_2"], spec["beat_3"]), es.beat_tag(opening, final)
    with es._BEAT_LOCK:   # seçim anı hafızası: atılan T*+W* yerine bu üretimin gerçek çifti
        mem = es._BEAT_MEMORY.get(event, [])
        if mem and mem[-1] == old_tag:
            mem[-1] = new_tag
    _DZ_GEO_MEMORY.append(geo)
    del _DZ_GEO_MEMORY[:-12]
    story = dalga24_story(geo, opening, final)
    tail = dalga24_tail(follow)
    prompt = dalga24_prompt(geo, opening, final, follow)
    dz = {"event": event, "geo": geo, "opening": opening, "final": final, "follow": follow, "story": story,
          "suffix": tail, "prompt": prompt}
    dz["lines"] = dalga24_lines(dz)
    problems = dalga24_issues({**st, "dalga24": dz}, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{DALGA24_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = scene.get("combo_key", "")
    if f"#{old_tag}|" in combo:
        combo = combo.replace(f"#{old_tag}|", f"#{new_tag}|")
    name = _DZ["geos"][geo]["name"]
    cap_info = {**(st.get("caption_info") or {}), "opening": dalga24_opening(geo, opening),
                "beat_2": _DZ["core"][:-1], "beat_3": _DZ["finals"][final][:-1]}
    cam = "takip" if follow else "sabit"
    structure = {**st, "dalga24": dz, "caption_info": cap_info,
                 "environment": f"Coğrafya: {geo} {name} · kamera = {DALGA24_MODE_LABEL} (high balcony, {cam})",
                 "story_source": f"Hikâye: kod (birebir) · {DALGA24_MODE_LABEL}"}
    if st.get("axes_json"):
        structure["axes_json"] = _dalga24_axes(st["axes_json"], new_tag, geo)
    trace, axes_line = mode_display(
        scene, structure, mode=DALGA24_MODE_LABEL,
        camera=f"{cam} ({dalga24_camera_text(follow)}); high balcony, railing in foreground",
        opening=dalga24_opening(geo, opening), mid=("çekirdek", _DZ["core"]), final=(final, _DZ["finals"][final]),
        plain=story, labels=("Açılış", "Çekirdek aksiyon", "Final"),
        spot="High balcony of a seafront building (24 Eylül kalıbı)", weather="overcast, grey sky (stil eki)",
        axes={"coğrafya": f"{geo} {name}", "açılış": f"{opening} ({_DZ['openings'][opening]['desc']})",
              "final": final, "kamera modu": cam},
        repeat=f"coğrafya son {DALGA24_GEO_BLOCK} elendi (D1 tohum) · açılış son {DALGA24_OPENING_BLOCK} (A2 tohum) · "
               f"final son {DALGA24_FINAL_BLOCK}")
    # görünüm (normal hattın bölgesi) ve kişi aralığı prompt'ta yok: gösterilmez; kayıt etiketi beats_tag'de
    trace = {**trace, "mode": "dalga24", "beats_tag": new_tag, "cografya": geo, "view": None, "view_source": None,
             "count_range": ["-", "-"], "vehicle": "adı yok (parked cars, city bus)"}
    structure["axes_line"] = axes_line
    out = {**scene, "story": story, "plain_story": story, "style_suffix": tail, "prompt": prompt,
           "combo_key": combo, "structure": structure, "trace": trace}
    if scene.get("axes_json"):
        out["axes_json"] = _dalga24_axes(scene["axes_json"], new_tag, geo)
    return out


def dalga24_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin 24 Eylül kalıbıyla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    dz = structure["dalga24"]
    if dz.get("geo") not in _DZ["geos"]:
        return [f"coğrafya D1-D6 değil ({dz.get('geo')})"]
    if dz.get("opening") not in _DZ["openings"]:
        return [f"açılış A1/A2 değil ({dz.get('opening')})"]
    if dz.get("final") not in _DZ["finals"]:
        return [f"final F1-F4 değil ({dz.get('final')})"]
    out = []
    story = dalga24_story(dz["geo"], dz["opening"], dz["final"])
    prompt = dalga24_prompt(dz["geo"], dz["opening"], dz["final"], dz["follow"])
    if info.get("style_suffix") != dalga24_tail(dz["follow"]):
        out.append("stil eki 24 Eylül kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye 24 Eylül kalıbıyla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt 24 Eylül kalıbıyla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    for bad in ("0-4s", "4-9s", "9-15s", "Full action", "Until the last frame"):
        if bad in text:
            out.append(f"bu modda olmayan ifade var: {bad}")
    if len(text.split()) > DALGA24_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {DALGA24_MAX_WORDS})")
    if len(text) > DALGA24_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {DALGA24_MAX_CHARS})")
    return out


# ── ⭐ Hit kalıbı · Yaklaşma (kül bulutu) (12 Kas 2026 (6), Bahadır) ───────────────────────────────────────────────────
# Kül bulutu hit'i (13 Eki 11:23, P2+Q1): yamaç terası, köy caddesi, volkan kadrajda, bulut yamaçtan caddeye inip
# kameraya doğru gelir. Ateş hortumu Yaklaşma ve dev dalga 24 Eylül yapısıyla birleşik. GPT yok, hikâye tamamen koddan.
# Zaman etiketleri VAR (hit'te de vardı). Kül bulutunun normal yolu ve yukarıdaki kayıtlı hit prompt'u değişmez.
# Araç savurma yasağı SADECE bu modda K2 için kalkar. Kül bulutunun normal hattında araç yok: araç bu modun kendi
# havuzundan (son 2 elenir); kişi sayısı da bu modda 3 ya da 4 (normal hattın 3-6 aralığı kullanılmaz). Kayıt K*+L*.
KUL_MODE_LABEL = "⭐ Hit kalıbı · Yaklaşma (kül bulutu)"
KUL_BUTTON_LABEL = "⭐ Hit kalıbı · Yaklaşma"
KUL_EVENTS = (es.PYROCLASTIC,)
# Kamera: True = terasta kalır, bulutu izlemek için yavaşça aşağı eğilir; False = terasta sabit (varsayılan True)
KUL_YAKLASMA_KAMERA_TAKIP = True
KUL_MAX_WORDS = 230
KUL_MAX_CHARS = 1400
KUL_GEO_BLOCK = 3
KUL_GEO_SEED = ("V1",)          # ilk üretimde V1 gelmez
KUL_VEHICLE_BLOCK = 2
KUL_MID_BLOCK = 1      # 13 Kas (2): 3 aktif seçenek, son 1 elenir
KUL_FINAL_BLOCK = 1
YAKLASMA_KUL_BULUTU = {
    "geos": {
        "V1": {"name": "İtalya", "volcano": "A broad grey volcano",
               "place": "a village of stone houses with terracotta roofs"},
        "V2": {"name": "Endonezya", "volcano": "A steep green volcano",
               "place": "a village of tin-roofed houses among palm trees"},
        "V3": {"name": "Japonya", "volcano": "A snow-capped cone volcano", "place": "a town of tiled-roof Japanese houses"},
        "V4": {"name": "Şili", "volcano": "A snow-capped Andean volcano", "place": "a town of colorful wooden houses"},
        "V5": {"name": "Guatemala", "volcano": "A tall cone volcano", "place": "a town of pastel colonial houses"},
        "V6": {"name": "Filipinler", "volcano": "A perfectly cone-shaped volcano",
               "place": "a town of concrete houses with tin roofs"},
    },
    # 13 Kas 2026: güçlü patlama açılışı (eski metin KUL_OPENING_V1, pasif)
    "opening": "{volcano} rises above the far end of the street in {place} and erupts violently, a massive explosion "
               "column bursting from its summit as a pyroclastic cloud races down its flank into the street, rolling "
               "toward the camera.",
    "people": {3: "Three people run up the street below, away from the cloud.",
               4: "Four people run up the street below, away from the cloud."},
    "action": "Ash rains down from the very first frame.",
    "vehicles": ("parked car", "pickup truck", "small bus"),
    "mids": {
        "K1": "Halfway down the street, the cloud snaps a row of street trees and power poles and they crash across the "
              "road.",
        "K2": "Halfway down the street, the cloud swallows a {vehicle} and hurls it, in one piece, against a house wall.",
        "K5": "Halfway down the street, the blast of the cloud slams a {vehicle} sideways into a shopfront, glass "
              "exploding around it.",
    },
    "finals": {
        "L1": "Right below the terrace, the cloud engulfs the nearest house and its front wall collapses, debris "
              "swirling in the ash.",
        "L2": "Right below the terrace, the cloud tears the roof off the nearest house and sweeps it away in pieces.",
        "L4": "Right below the terrace, the grey cloud surges over the nearest houses and swallows the street, darkness "
              "racing up toward the camera.",
    },
    "vehicle_mids": ("K2", "K5"),
    "vehicle_throw_mid": "K2",
    "camera": {True: "the camera stays on the terrace and tilts down slowly to follow the cloud, never descending",
               False: "the camera stays fixed on the terrace, never descending"},
    "tail": ("Handheld footage shot from a terrace above the town, high vantage looking down the street, the whole "
             "erupting volcano visible in the upper part of the frame, a corner of the terrace "
             "railing in the foreground; slight hand shake, {camera}; one continuous shot, no zoom, no cuts, no face "
             "close to the camera. Civilians in everyday clothes, never CGI. A dense, boiling grey pyroclastic cloud "
             "growing larger as it approaches, never a thin smoke plume. Raw natural light under an "
             "ash-grey sky lit orange by the eruption. Real time, never slow motion, people run at full speed. No "
             "readable signs, text or flags."),
}
_KB = YAKLASMA_KUL_BULUTU
# 13 Kas 2026 öncesi metinler (82a8942), pasif; kullanılmaz.
KUL_OPENING_V1 = ("{volcano} rises above the far end of the street in {place} and erupts, sending a towering pyroclastic "
                  "cloud racing down its flank into the street and rolling toward the camera.")
KUL_TAIL_V1 = ("Handheld footage shot from a terrace above the town, high vantage looking down the street toward the "
               "erupting volcano, the whole volcano visible in the upper part of the frame, a corner of the terrace "
               "railing in the foreground; slight hand shake, {camera}; one continuous shot, no zoom, no cuts, no face "
               "close to the camera. Civilians in everyday clothes, never CGI. A dense, boiling grey pyroclastic cloud "
               "growing larger in the frame as it approaches, never a thin smoke plume. Raw natural light under an "
               "ash-grey sky lit orange by the eruption. Real time, never slow motion, people run at full speed. No "
               "readable signs, text or flags.")
# 13 Kas 2026 (2): zayıf seçenekler pasif (bu modda seçilmez, kullanılmaz)
KUL_PASIF = {
    "mids": {
        "K3": "Halfway down the street, the blast of the cloud shatters every window and tears the shutters off the "
              "houses.",
        "K4": "Halfway down the street, the cloud rolls over a {vehicle} trying to reverse away and buries it in grey "
              "ash.",
    },
    "finals": {
        "L3": "Right below the terrace, the cloud rips apart the garden wall and fence, hurling debris up toward the "
              "camera.",
    },
}
KUL_V5_VOLCANO_V1 = "A towering cone volcano"
KUL_K3_V1 = ("Halfway down the street, the blast of the cloud shatters every window along the street and tears the "
             "shutters off the houses.")
K2_WARNING = "⚠️ Araç savurma ortası (K2): videoda aracın tek parça kalıp kalmadığını kontrol et."
_KUL_GEO_MEMORY: list[str] = []
_KUL_VEHICLE_MEMORY: list[str] = []


def kul_is_active(event: str | None) -> bool:
    return event in KUL_EVENTS


def kul_camera_text(follow: bool | None = None) -> str:
    return _KB["camera"][bool(KUL_YAKLASMA_KAMERA_TAKIP if follow is None else follow)]


def kul_tail(follow: bool | None = None) -> str:
    return _KB["tail"].format(camera=kul_camera_text(follow))


def kul_opening(geo: str) -> str:
    g = _KB["geos"][geo]
    return _KB["opening"].format(volcano=g["volcano"], place=g["place"])


def kul_people(n: int) -> str:
    if n not in _KB["people"]:
        raise es.StructureError(f"{KUL_MODE_LABEL}: kişi sayısı 3 ya da 4 olmalı ({n})")
    return _KB["people"][n]


def kul_mid(mid: str, vehicle: str | None) -> str:
    if mid not in _KB["mids"]:
        raise es.StructureError(f"{KUL_MODE_LABEL}: {mid} bu modda yok (orta K1, K2, K5)")
    if mid in _KB["vehicle_mids"] and vehicle not in _KB["vehicles"]:
        raise es.StructureError(f"{KUL_MODE_LABEL}: {mid} için araç yok ({vehicle})")
    return _KB["mids"][mid].format(vehicle=vehicle or "")


def kul_story(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    a, b, c = es.SLICE_LABELS
    return (f"{a}: {kul_opening(geo)} {kul_people(people)} {_KB['action']} {b}: {kul_mid(mid, vehicle)} "
            f"{c}: {_KB['finals'][final]}")


def kul_prompt(geo: str, people: int, mid: str, vehicle: str | None, final: str, follow: bool | None = None) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(kul_story(geo, people, mid, vehicle, final), kul_tail(follow))


def kul_tags(history: list[str]) -> list[str]:
    return [t for t in es.beat_history(es.PYROCLASTIC, history or []) if re.fullmatch(r"K\d+\+L\d+", t)]


def kul_choose_mid(history: list[str], rng=None) -> str:
    return _block_pick(list(_KB["mids"]), [t.split("+")[0] for t in kul_tags(history)], KUL_MID_BLOCK, rng)


def kul_choose_final(history: list[str], rng=None) -> str:
    return _block_pick(list(_KB["finals"]), [t.split("+")[1] for t in kul_tags(history)], KUL_FINAL_BLOCK, rng)


def kul_axes_history(records: list | None, key: str) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == es.PYROCLASTIC and axes.get("mod") == "kul_yaklasma"
                and axes.get(key)):
            out.append(axes[key])
    return out


def kul_choose_geo(used: list[str] | None = None, rng=None) -> str:
    seen = list(KUL_GEO_SEED) + list(_KUL_GEO_MEMORY if used is None else used)
    return _block_pick(list(_KB["geos"]), seen, KUL_GEO_BLOCK, rng)


def kul_choose_vehicle(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(list(_KB["vehicles"]), list(_KUL_VEHICLE_MEMORY if used is None else used),
                       KUL_VEHICLE_BLOCK, rng)


def kul_lines(kb: dict) -> str:
    text = kb["prompt"]
    lines = [
        f"Mod: {KUL_MODE_LABEL}",
        f"Coğrafya: {kb['geo']} {_KB['geos'][kb['geo']]['name']}",
        f"Araç: {kb['vehicle']}" + ("" if kb["mid"] in _KB["vehicle_mids"] else " (bu ortada araç yok)"),
        f"Orta (4-9s): {kb['mid']} «{kul_mid(kb['mid'], kb['vehicle'])}»",
        f"Final (9-15s): {kb['final']} «{_KB['finals'][kb['final']]}»",
        "Kamera: " + ("takip (terasta kalır, bulutu izlemek için yavaşça aşağı eğilir)" if kb["follow"]
                      else "sabit (terasta)"),
        f"Kelime: {len(text.split())} (en fazla {KUL_MAX_WORDS}) · karakter: {len(text)} (en fazla {KUL_MAX_CHARS})",
    ]
    if kb["mid"] == _KB["vehicle_throw_mid"]:
        lines.append(K2_WARNING)
    return "\n".join(lines)


def _kul_axes(js, tag: str, geo: str, vehicle: str, people: int):
    import json
    try:
        data = json.loads(js)
    except (TypeError, ValueError):
        return js
    if isinstance(data.get("axes"), dict):
        data["axes"].update({"beats": tag, "mod": "kul_yaklasma", "cografya": geo, "arac": vehicle,
                             "vehicle": vehicle, "people": people})
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def kul_apply(scene: dict, history: list[str] | None = None, rng=None, follow: bool | None = None,
              geo_used: list[str] | None = None, vehicle_used: list[str] | None = None) -> dict:
    """Normal hattın kurduğu kül bulutu sahnesinden (kayıt aynı) Yaklaşma (kül bulutu) prompt'unu kurar. Coğrafya V1-V6
    (son 3 elenir, V1 tohum), araç (son 2), orta K1/K2/K5 (son 1), final L1/L2/L4 (son 1), kişi 3/4.
    K3, K4, L3 pasif (KUL_PASIF).
    structure["kul_yaklasma"] Kie öncesi son denetimin (submit_issues) ve yeniden yazımın kaynağıdır."""
    import random
    event = scene["event"]
    st = scene.get("structure") or {}
    spec = st.get("spec")
    if not kul_is_active(event) or not spec:
        raise es.StructureError(f"{KUL_MODE_LABEL} kurulamadı: {event}")
    follow = bool(KUL_YAKLASMA_KAMERA_TAKIP if follow is None else follow)
    r = rng or random
    geo = kul_choose_geo(geo_used, r)
    vehicle = kul_choose_vehicle(vehicle_used, r)
    people = r.choice((3, 4))
    mid = kul_choose_mid(history or [], r)
    final = kul_choose_final(history or [], r)
    old_tag, new_tag = es.beat_tag(spec["beat_2"], spec["beat_3"]), es.beat_tag(mid, final)
    with es._BEAT_LOCK:   # seçim anı hafızası: atılan P*+Q* yerine bu üretimin gerçek çifti
        mem = es._BEAT_MEMORY.get(event, [])
        if mem and mem[-1] == old_tag:
            mem[-1] = new_tag
    for m, v in ((_KUL_GEO_MEMORY, geo), (_KUL_VEHICLE_MEMORY, vehicle)):
        m.append(v)
        del m[:-12]
    story = kul_story(geo, people, mid, vehicle, final)
    tail = kul_tail(follow)
    prompt = kul_prompt(geo, people, mid, vehicle, final, follow)
    kb = {"event": event, "geo": geo, "people": people, "vehicle": vehicle, "mid": mid, "final": final,
          "follow": follow, "story": story, "suffix": tail, "prompt": prompt}
    kb["lines"] = kul_lines(kb)
    problems = kul_issues({**st, "kul_yaklasma": kb}, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{KUL_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = scene.get("combo_key", "")
    if f"#{old_tag}|" in combo:
        combo = combo.replace(f"#{old_tag}|", f"#{new_tag}|")
    name = _KB["geos"][geo]["name"]
    mid_text = kul_mid(mid, vehicle)
    cap_info = {**(st.get("caption_info") or {}), "opening": kul_opening(geo), "people": people,
                "beat_2": mid_text[:-1], "beat_3": _KB["finals"][final][:-1]}
    cam = "takip" if follow else "sabit"
    structure = {**st, "kul_yaklasma": kb, "caption_info": cap_info,
                 "environment": f"Coğrafya: {geo} {name} · kamera = {KUL_MODE_LABEL} (terrace above the town, {cam})",
                 "story_source": f"Hikâye: kod (birebir) · {KUL_MODE_LABEL}"}
    if st.get("axes_json"):
        structure["axes_json"] = _kul_axes(st["axes_json"], new_tag, geo, vehicle, people)
    plain = " ".join([kul_opening(geo), kul_people(people), _KB["action"], mid_text, _KB["finals"][final]])
    trace, axes_line = mode_display(
        scene, structure, mode=KUL_MODE_LABEL, camera=f"{cam} ({kul_camera_text(follow)}); terrace above the town, "
        "volcano in the upper part of the frame, railing corner in foreground",
        opening=kul_opening(geo), mid=(mid, mid_text), final=(final, _KB["finals"][final]), plain=plain,
        vehicle=vehicle if mid in _KB["vehicle_mids"] else f"{vehicle} (bu ortada araç yok)",
        spot="Terrace above the town, looking down the street toward the volcano (Yaklaşma kalıbı)",
        weather="ash-grey sky lit orange (stil eki)",
        axes={"coğrafya": f"{geo} {name}", "araç": vehicle, "kişi": people, "orta": mid, "final": final,
              "kamera modu": cam},
        repeat=f"coğrafya son {KUL_GEO_BLOCK} elendi (V1 tohum) · araç son {KUL_VEHICLE_BLOCK} · orta son "
               f"{KUL_MID_BLOCK} · final son {KUL_FINAL_BLOCK}")
    # normal hattın ortam etiketi ve görünümü prompt'ta yok: gösterilmez
    trace = {**trace, "mode": "kul_yaklasma", "cografya": geo, "count_range": [3, 4], "view": None,
             "view_source": None, "fire_env_label_short": None}
    structure["axes_line"] = axes_line
    out = {**scene, "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt,
           "combo_key": combo, "structure": structure, "trace": trace}
    if scene.get("axes_json"):
        out["axes_json"] = _kul_axes(scene["axes_json"], new_tag, geo, vehicle, people)
    return out


def kul_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin bu kalıpla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    kb = structure["kul_yaklasma"]
    if kb.get("geo") not in _KB["geos"]:
        return [f"coğrafya V1-V6 değil ({kb.get('geo')})"]
    if kb.get("mid") not in _KB["mids"]:
        return [f"orta K1/K2/K5 değil ({kb.get('mid')})"]
    if kb.get("final") not in _KB["finals"]:
        return [f"final L1/L2/L4 değil ({kb.get('final')})"]
    try:
        story = kul_story(kb["geo"], kb["people"], kb["mid"], kb["vehicle"], kb["final"])
        prompt = kul_prompt(kb["geo"], kb["people"], kb["mid"], kb["vehicle"], kb["final"], kb["follow"])
    except es.StructureError as e:
        return [str(e)]
    out = []
    if info.get("style_suffix") != kul_tail(kb["follow"]):
        out.append("stil eki Yaklaşma (kül bulutu) kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye kalıpla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt kalıpla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    for bad in ("Full action", "Until the last frame"):
        if bad in text:
            out.append(f"bu modda olmayan ifade var: {bad}")
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > KUL_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {KUL_MAX_WORDS})")
    if len(text) > KUL_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {KUL_MAX_CHARS})")
    return out


# ── ⭐ Hit kalıbı · Yaklaşma (orman yangını) (13 Kas 2026, Bahadır) ────────────────────────────────────────────────────
# Orman yangını hit'i (9 Eki 21:52, K5+L4): yamaçtaki bir evin balkonundan caddeye ve yanan yamaca bakış, alev duvarı
# ormanlık yamaçtan inip mahalleye çarpar, kamera alevleri takip eder. Kül bulutu Yaklaşma yapısıyla birleşik. GPT yok,
# hikâye tamamen koddan, zaman etiketleri VAR. Orman yangınının normal yolu ve yukarıdaki kayıtlı orman hit prompt'u
# değişmez (eski orman hit butonu gizli kalır, HIT_ACTIVE_EVENTS değişmedi). Kayıt M*+N* (olay bazlı; normal orman
# havuzu K*/L*). Araç bu modun kendi havuzundan (son 2), kişi 3/4. Yasak çift M2+N3 (iki kez ağaç). 13 Kas (2): M4 ve
# N4 pasif (ORMAN_PASIF), orta/final LRU son 1, açılışta yangın ilk karede köyün içinde. "U-turn" bu modda yok (M1 hit
# sahnesi, U dönüşü olmadan). 13 Kas (3): yangın ilk karede caddenin ortasında, ortalar "Just ahead of the flames,",
# yasak çiftler M2+N2, M2+N3, M3+N2 (eski metinler ORMAN_OPENING_V2 / ORMAN_MIDS_V2, pasif).
# 20 Kas 2026 (v4, "ilk 3 saniye olay kuralı", Bahadır): ilk karede karşıdaki ev yerden çatıya alev alır + alev duvarı
# yamaçtan iner; "action" cümlesi hikâyeye girmez; ortalar M2/M3, finaller N1/N3 ("big in frame"); M1 ve N2 pasif
# (ORMAN_PASIF); yasak çift yalnız M2+N3; stil ekine "never a calm moment". Eski metinler ORMAN_*_V3 / ORMAN_*_V1, pasif.
# 20 Kas 2026 (v5, Bahadır): v4 videosunda karşıdaki ev yamaçtaki uzak köye kondu ve alevler asfaltta sıvı gibi aktı.
# Açılışta ev "right across from the balcony, close and big in frame", alev duvarı evin arkasındaki yamaçtan iner;
# stil ekine "never flowing along the road like liquid". Eski metinler ORMAN_OPENING_V4 / ORMAN_TAIL_V2, pasif.
# 20 Kas 2026 (v6, Bahadır): v5 videosunda alev yine asfaltta aktı, pikap alev topundan sonra dağıldı (ortalar ateşi
# caddenin ortasına koyuyordu). Ortalar "Beside the street", araç garaj yolunda; stil eki "never along the asphalt",
# "burning vehicles stay whole". Eski metinler ORMAN_MIDS_V5 / ORMAN_TAIL_V3 / ORMAN_REQUIRED_V5, pasif.
# 20 Kas 2026 (v7, Bahadır): v6 videosunda açılıştaki ev mantar biçimli ateş topuyla patladı, alevler yer yer saydamdı,
# N3 finali zayıf kaldı. Açılışta ev "is engulfed in flames" (patlama yok), stil eki "no explosions", "solid flames ...
# never see-through"; final yalnız N1 (N3 pasif, ORMAN_PASIF), final LRU'su atlanır, ortalar yalnız orta geçmişine göre.
# Eski metinler ORMAN_OPENING_V5 / ORMAN_TAIL_V4 / ORMAN_FINALS_V6 / ORMAN_REQUIRED_V6 / ORMAN_BANNED_V6 (v6 yasak ifade listesi), pasif.
ORMAN_MODE_LABEL = "⭐ Hit kalıbı · Yaklaşma (orman yangını)"
ORMAN_BUTTON_LABEL = "⭐ Hit kalıbı · Yaklaşma"
ORMAN_EVENTS = (es.WILDFIRE,)
# Kamera: True = alev duvarını takip eder (pan); False = sabit (varsayılan True)
ORMAN_YAKLASMA_KAMERA_TAKIP = True
ORMAN_MAX_WORDS = 230
ORMAN_MAX_CHARS = 1400
ORMAN_GEO_BLOCK = 3
ORMAN_GEO_SEED = ("R1",)          # ilk üretimde R1 gelmez
ORMAN_VEHICLE_BLOCK = 2
ORMAN_MID_BLOCK = 1      # 13 Kas (2): 3 aktif seçenek, son 1 elenir
ORMAN_FINAL_BLOCK = 1
ORMAN_BANNED_PAIRS = (("M2", "N3"),)   # 20 Kas v4: iki kez ağaç olmasın (N2 pasif)
ORMAN_BANNED_PAIRS_V3 = (("M2", "N3"), ("M2", "N2"), ("M3", "N2"))   # 13 Kas (3), pasif
ORMAN_VERSION_LABEL = "Sürüm: v7 (patlama yok, katı alev, final N1)"
ORMAN_VERSION_LABEL_V6 = "Sürüm: v6 (ateş yolda yok, araç garaj yolunda)"   # pasif
ORMAN_VERSION_LABEL_V5 = "Sürüm: v5 (yakın ev, akan ateş yok)"   # pasif
ORMAN_VERSION_LABEL_V4 = "Sürüm: v4 (ilk 3 saniye olay)"   # pasif
# Kie öncesi denetim: zorunlu ifadeler (yoksa gönderme) ve bu modda olmayan ifadeler (varsa gönderme)
ORMAN_REQUIRED = ("From the very first frame", "big in frame", "right across from the balcony", "engulfed in flames",
                  "Beside the street", "never along the asphalt", "no explosions", "never see-through",
                  "Never a calm moment")   # 20 Kas v7
ORMAN_REQUIRED_V6 = ("From the very first frame", "big in frame", "right across from the balcony", "Beside the street",
                     "never along the asphalt", "Never a calm moment")   # pasif
ORMAN_REQUIRED_V5 = ("From the very first frame", "big in frame", "never a calm moment",
                     "right across from the balcony", "never flowing along the road like liquid")   # pasif
ORMAN_REQUIRED_V4 = ("From the very first frame", "big in frame", "never a calm moment")   # pasif
ORMAN_FORBIDDEN = ("Full action", "Until the last frame", "U-turn", "speeds away", "wooden deck",
                   "halfway down the street", "Burning embers", "In the middle of the street",
                   "disappears into the fire", "windows blowing out", "bursts into flames",
                   "topples onto the nearest house")   # 20 Kas v7: +3
ORMAN_BANNED_V6 = ("Full action", "Until the last frame", "U-turn", "speeds away", "wooden deck",
                   "halfway down the street", "Burning embers", "In the middle of the street",
                   "disappears into the fire")   # pasif (v6 yasak ifade listesi)
YAKLASMA_ORMAN = {
    "geos": {
        "R1": {"name": "Kaliforniya", "forest": "pine-covered",
               "place": "a hillside neighborhood of wooden suburban houses"},
        "R2": {"name": "Avustralya", "forest": "eucalyptus-covered",
               "place": "a hillside neighborhood of tin-roofed weatherboard houses"},
        "R3": {"name": "Yunanistan", "forest": "pine-covered",
               "place": "a hillside village of whitewashed terracotta-roofed houses"},
        "R4": {"name": "Kanada", "forest": "spruce-covered", "place": "a hillside town of dark-roofed timber houses"},
        "R5": {"name": "Portekiz", "forest": "eucalyptus-covered",
               "place": "a hillside village of tile-roofed stone houses"},
        "R6": {"name": "Şili", "forest": "pine-covered", "place": "a hillside town of colorful wooden houses"},
    },
    # 20 Kas 2026 (v7): ev patlamaz, yerden çatıya alevler içinde (eski metinler ORMAN_OPENING_V1-V5, pasif)
    "opening": "From the very first frame {place} is burning: the house right across from the balcony, close and big in "
               "frame, is engulfed in flames from ground to roof as a towering wall of flames races down the {forest} "
               "slope behind it.",
    "people": {3: "Three people run up the street below, away from the flames.",
               4: "Four people run up the street below, away from the flames."},
    # 20 Kas v4: hikâyeye girmez (ORMAN_ACTION_V1 olarak da saklı)
    "action": "Burning embers and thick smoke blow across the street from the very first frame.",
    "vehicles": ("white van", "pickup truck", "SUV"),
    # 20 Kas 2026 (v6): ateş caddede değil, araç garaj yolunda (eski ortalar ORMAN_MIDS_V5, pasif)
    "mids": {
        "M2": "Beside the street, big in frame, a burning tree crashes down onto a {vehicle} parked in a driveway, "
              "crushing its roof in a burst of sparks.",
        "M3": "Beside the street, big in frame, flames from a burning house pour over the {vehicle} in its driveway, "
              "its windows bursting as it catches fire.",
    },
    # 20 Kas 2026 (v7): final yalnız N1 (v6 finalleri ORMAN_FINALS_V6, N3 pasif)
    "finals": {
        "N1": "Right below the balcony, big in frame, the flames reach the nearest house and its roof caves in, a "
              "fountain of sparks bursting up toward the camera.",
    },
    "vehicle_mids": ("M2", "M3"),
    "camera": {True: "the camera pans to follow the wall of flames as it approaches", False: "the camera stays fixed"},
    # 20 Kas 2026 (v7): patlama yok, katı alev (eski stil ekleri ORMAN_TAIL_V1-V4, pasif)
    "tail": ("Handheld footage shot from the balcony of a hillside house overlooking the street and the burning slope, "
             "high vantage, normal lens, a corner of the balcony railing in the foreground; slight hand shake, "
             "{camera}; no zoom, no cuts. Fire spreads only through trees, yards and houses, never along the asphalt; "
             "burning vehicles stay whole; no explosions. Never a calm moment. Civilians in everyday clothes, never "
             "CGI. Realistic wildfire: towering, roaring, solid flames and thick smoke, never see-through, never thin "
             "lines or strips of fire. Raw natural light under an orange smoky sky. Real time, never slow motion, "
             "people run at full speed."),
}
_OR = YAKLASMA_ORMAN
# 20 Kas 2026 (v7) öncesi açılış, stil eki ve finaller (1f044c9, v6), pasif; kullanılmaz.
ORMAN_OPENING_V5 = ("From the very first frame {place} is burning: the house right across from the balcony, close and "
                    "big in frame, bursts into flames from ground to roof, windows blowing out, as a towering wall of "
                    "flames races down the {forest} slope behind it.")
ORMAN_TAIL_V4 = ("Handheld footage shot from the balcony of a hillside house overlooking the street and the burning slope, "
                 "high vantage, normal lens, a corner of the balcony railing in the foreground; slight hand shake, "
                 "{camera}; one continuous shot, no zoom, no cuts. The fire spreads only through trees, yards and houses, "
                 "never along the asphalt; burning vehicles stay whole. Never a calm moment. Civilians in everyday "
                 "clothes, never CGI. Realistic wildfire: towering, roaring flames and thick smoke, never thin lines or "
                 "strips of fire. Raw natural light under an orange smoky sky. Real time, never slow motion, people run at "
                 "full speed.")
ORMAN_FINALS_V6 = {
    "N1": "Right below the balcony, big in frame, the flames reach the nearest house and its roof caves in, a "
          "fountain of sparks bursting up toward the camera.",
    "N3": "Right below the balcony, big in frame, a burning tree topples onto the nearest house, smashing through "
          "its roof as flames pour inside.",
}
# 20 Kas 2026 (v6) öncesi ortalar ve stil eki (bbce59c, v5), pasif; kullanılmaz.
ORMAN_MIDS_V5 = {
    "M2": "In the middle of the street, big in frame, a huge burning tree crashes down onto the {vehicle}, "
          "crushing its roof in a burst of sparks.",
    "M3": "In the middle of the street, big in frame, the wall of flames swallows a parked {vehicle}, its windows "
          "bursting as it disappears into the fire.",
}
ORMAN_TAIL_V3 = ("Handheld footage shot from the balcony of a hillside house overlooking the street and the burning slope, "
                 "high vantage, normal lens, a corner of the balcony railing in the foreground; slight hand shake, "
                 "{camera}; one continuous shot, no zoom, no cuts. The fire keeps spreading through trees and houses the "
                 "whole time, never flowing along the road like liquid, never a calm moment. Civilians in everyday "
                 "clothes, never CGI. Realistic wildfire: towering, roaring flames and thick smoke, never thin lines or "
                 "strips of fire. Raw natural light under an orange smoky sky. Real time, never slow motion, people run at "
                 "full speed.")
# 20 Kas 2026 (v5) öncesi açılış ve stil eki (903c6ab, v4), pasif; kullanılmaz.
ORMAN_OPENING_V4 = ("From the very first frame {place} is burning: the house across the street, big in frame, bursts into "
                    "flames from ground to roof, windows blowing out, as a towering wall of flames races down the {forest} "
                    "slope toward the camera.")
ORMAN_TAIL_V2 = ("Handheld footage shot from the balcony of a hillside house overlooking the street and the burning slope, "
                 "high vantage, normal lens, a corner of the balcony railing in the foreground; slight hand shake, "
                 "{camera}; one continuous shot, no zoom, no cuts, no face close to the camera. The fire keeps spreading "
                 "the whole time, never a calm moment. Civilians in everyday clothes, never CGI. Realistic wildfire: towering, roaring flames and thick smoke, never thin lines or "
                 "strips of fire. Raw natural light under an orange smoky sky. Real time, never slow motion, people run at "
                 "full speed. No readable signs, text or flags.")
# 20 Kas 2026 (v4) öncesi metinler (5556588), pasif; kullanılmaz.
ORMAN_OPENING_V3 = ("A towering wall of flames has already swept down the {forest} slope and is racing halfway down the "
                    "street through {place} toward the camera, igniting roofs and trees as it comes.")
ORMAN_ACTION_V1 = "Burning embers and thick smoke blow across the street from the very first frame."
ORMAN_MIDS_V3 = {
    "M1": "Just ahead of the flames, the {vehicle} speeds away as the wall of flames closes the road right behind it.",
    "M2": "Just ahead of the flames, a huge burning pine crashes down onto the {vehicle}, crushing its roof.",
    "M3": "Just ahead of the flames, the wall of flames swallows a parked {vehicle}, its windows bursting as it "
          "disappears into the fire.",
}
ORMAN_FINALS_V3 = {
    "N1": "Right below the balcony, the flames reach the nearest house and its roof caves in, a fountain of sparks "
          "bursting up toward the camera.",
    "N2": "Right below the balcony, the wall of flames engulfs the garden and wooden deck of the nearest house, "
          "burning planks collapsing in a shower of sparks.",
    "N3": "Right below the balcony, a burning tree topples onto the nearest house, smashing through its roof as "
          "flames pour inside.",
}
ORMAN_TAIL_V1 = ("Handheld footage shot from the balcony of a hillside house overlooking the street and the burning slope, "
                 "high vantage, normal lens, a corner of the balcony railing in the foreground; slight hand shake, "
                 "{camera}; one continuous shot, no zoom, no cuts, no face close to the camera. Civilians in everyday "
                 "clothes, never CGI. Realistic wildfire: towering, roaring flames and thick smoke, never thin lines or "
                 "strips of fire. Raw natural light under an orange smoky sky. Real time, never slow motion, people run "
                 "at full speed. No readable signs, text or flags.")
# 13 Kas 2026 (2) öncesi açılış (2b35000), pasif; kullanılmaz.
ORMAN_OPENING_V1 = ("A towering wall of flames sweeps down the {forest} slope at the far end of the street and slams "
                    "into the edge of {place}, igniting roofs and trees as it races toward the camera.")
# 13 Kas 2026 (3) öncesi açılış ve ortalar (8de752a), pasif; kullanılmaz.
ORMAN_OPENING_V2 = ("A towering wall of flames has already swept down the {forest} slope at the far end of the street "
                    "and is racing through the edge of {place} toward the camera, igniting roofs and trees as it comes.")
ORMAN_MIDS_V2 = {
    "M1": "Halfway down the street, the {vehicle} speeds away as the wall of flames closes the road right behind it.",
    "M2": "Halfway down the street, a huge burning pine crashes down onto the {vehicle}, crushing its roof.",
    "M3": "Halfway down the street, the wall of flames swallows a parked {vehicle}, its windows bursting as it "
          "disappears into the fire.",
}
# 13 Kas 2026 (2): M4 (araçsız orta) ve N4 pasif; 20 Kas v4: M1 ve N2 (v3 metni) pasif (bu modda seçilmez, kullanılmaz)
ORMAN_PASIF = {
    "mids": {
        "M4": "Halfway down the street, two houses on either side of the road catch fire at once, flames pouring out of "
              "their windows and roofs.",
        "M1": ORMAN_MIDS_V3["M1"],
    },
    "finals": {
        "N2": ORMAN_FINALS_V3["N2"],
        "N3": ORMAN_FINALS_V6["N3"],   # 20 Kas v7: pasif
        "N4": "Right below the balcony, the fire jumps the street and the wooden fence and carport below burst into "
              "flames, heat and sparks rushing up toward the camera.",
    },
}
_ORMAN_GEO_MEMORY: list[str] = []
_ORMAN_VEHICLE_MEMORY: list[str] = []


def orman_is_active(event: str | None) -> bool:
    return event in ORMAN_EVENTS


def orman_camera_text(follow: bool | None = None) -> str:
    return _OR["camera"][bool(ORMAN_YAKLASMA_KAMERA_TAKIP if follow is None else follow)]


def orman_tail(follow: bool | None = None) -> str:
    return _OR["tail"].format(camera=orman_camera_text(follow))


def orman_opening(geo: str) -> str:
    g = _OR["geos"][geo]
    return _OR["opening"].format(forest=g["forest"], place=g["place"])


def orman_people(n: int) -> str:
    if n not in _OR["people"]:
        raise es.StructureError(f"{ORMAN_MODE_LABEL}: kişi sayısı 3 ya da 4 olmalı ({n})")
    return _OR["people"][n]


def orman_mid(mid: str, vehicle: str | None) -> str:
    if mid not in _OR["mids"]:
        raise es.StructureError(f"{ORMAN_MODE_LABEL}: {mid} bu modda yok (orta M2, M3)")
    if mid in _OR["vehicle_mids"] and vehicle not in _OR["vehicles"]:
        raise es.StructureError(f"{ORMAN_MODE_LABEL}: {mid} için araç yok ({vehicle})")
    return _OR["mids"][mid].format(vehicle=vehicle or "")


def orman_story(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    if (mid, final) in ORMAN_BANNED_PAIRS:
        raise es.StructureError(f"{ORMAN_MODE_LABEL}: {mid}+{final} yasak çift")
    a, b, c = es.SLICE_LABELS
    if final not in _OR["finals"]:
        raise es.StructureError(f"{ORMAN_MODE_LABEL}: {final} bu modda yok (final N1)")
    # 20 Kas v4: "action" cümlesi hikâyeye girmez
    return f"{a}: {orman_opening(geo)} {orman_people(people)} {b}: {orman_mid(mid, vehicle)} {c}: {_OR['finals'][final]}"


def orman_prompt(geo: str, people: int, mid: str, vehicle: str | None, final: str, follow: bool | None = None) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(orman_story(geo, people, mid, vehicle, final), orman_tail(follow))


def orman_tags(history: list[str]) -> list[str]:
    return [t for t in es.beat_history(es.WILDFIRE, history or []) if re.fullmatch(r"M\d+\+N\d+", t)]


def orman_choose_mid(history: list[str], rng=None) -> str:
    """Orta: son 1 elenir. 13 Kas (3): yasak çiftler yüzünden son finalden sonra final adayı kalmayan orta (ör. son
    final N1 iken yalnız N1'e gidebilen M2) aday değil; böyle orta yoksa tüm ortalar. 20 Kas v7: tek final (N1) varken
    bu eleme yapılmaz, ortalar yalnız orta geçmişine göre seçilir (M2/M3 dönüşümlü)."""
    tags = orman_tags(history)
    if len(_OR["finals"]) == 1:
        return _block_pick(list(_OR["mids"]), [t.split("+")[0] for t in tags], ORMAN_MID_BLOCK, rng)
    recent = set([t.split("+")[1] for t in tags][-ORMAN_FINAL_BLOCK:]) if ORMAN_FINAL_BLOCK else set()
    viable = [m for m in _OR["mids"]
              if any((m, f) not in ORMAN_BANNED_PAIRS and f not in recent for f in _OR["finals"])]
    return _block_pick(viable or list(_OR["mids"]), [t.split("+")[0] for t in tags], ORMAN_MID_BLOCK, rng)


def orman_choose_final(history: list[str], mid: str, rng=None) -> str:
    """Final: son 1 elenir; seçilen ortanın yasak eşi (v4: M2→N3) hiç aday değil. 20 Kas v7: tek aday (N1) varsa LRU
    atlanır (rastgelelik tüketilmez), yer yarılmasındaki tek seçenek düzeni."""
    banned = {f for m, f in ORMAN_BANNED_PAIRS if m == mid}
    left = [f for f in _OR["finals"] if f not in banned]
    if len(left) == 1:
        return left[0]
    return _block_pick([f for f in _OR["finals"] if f not in banned], [t.split("+")[1] for t in orman_tags(history)],
                       ORMAN_FINAL_BLOCK, rng)


def orman_axes_history(records: list | None, key: str) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == es.WILDFIRE and axes.get("mod") == "orman_yaklasma"
                and axes.get(key)):
            out.append(axes[key])
    return out


def orman_choose_geo(used: list[str] | None = None, rng=None) -> str:
    seen = list(ORMAN_GEO_SEED) + list(_ORMAN_GEO_MEMORY if used is None else used)
    return _block_pick(list(_OR["geos"]), seen, ORMAN_GEO_BLOCK, rng)


def orman_choose_vehicle(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(list(_OR["vehicles"]), list(_ORMAN_VEHICLE_MEMORY if used is None else used),
                       ORMAN_VEHICLE_BLOCK, rng)


def orman_camera_label(follow: bool) -> str:
    return "takip (alev duvarını izlemek için döner)" if follow else "sabit"


def orman_lines(ob: dict) -> str:
    text = ob["prompt"]
    return "\n".join([
        f"Mod: {ORMAN_MODE_LABEL}",
        ORMAN_VERSION_LABEL,
        f"Coğrafya: {ob['geo']} {_OR['geos'][ob['geo']]['name']}",
        f"Araç: {ob['vehicle']}" + ("" if ob["mid"] in _OR["vehicle_mids"] else " (bu ortada araç yok)"),
        f"Orta (4-9s): {ob['mid']} «{orman_mid(ob['mid'], ob['vehicle'])}»",
        f"Final (9-15s): {ob['final']} «{_OR['finals'][ob['final']]}»",
        "Kamera: " + orman_camera_label(ob["follow"]),
        f"Kelime: {len(text.split())} (en fazla {ORMAN_MAX_WORDS}) · karakter: {len(text)} (en fazla {ORMAN_MAX_CHARS})",
    ])


def _orman_axes(js, tag: str, geo: str, vehicle: str, people: int):
    import json
    try:
        data = json.loads(js)
    except (TypeError, ValueError):
        return js
    if isinstance(data.get("axes"), dict):
        data["axes"].update({"beats": tag, "mod": "orman_yaklasma", "cografya": geo, "arac": vehicle,
                             "vehicle": vehicle, "people": people})
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def orman_apply(scene: dict, history: list[str] | None = None, rng=None, follow: bool | None = None,
                geo_used: list[str] | None = None, vehicle_used: list[str] | None = None) -> dict:
    """Normal hattın kurduğu orman yangını sahnesinden (kayıt aynı) Yaklaşma (orman yangını) prompt'unu kurar. Coğrafya
    R1-R6 (son 3 elenir, R1 tohum), araç (son 2), orta M2/M3 (son 1), final yalnız N1 (20 Kas v7; LRU atlanır),
    kişi 3/4. M1, M4, N2, N3, N4 pasif (ORMAN_PASIF).
    structure["orman_yaklasma"] Kie öncesi son denetimin (submit_issues) ve yeniden yazımın kaynağıdır."""
    import random
    event = scene["event"]
    st = scene.get("structure") or {}
    spec = st.get("spec")
    if not orman_is_active(event) or not spec:
        raise es.StructureError(f"{ORMAN_MODE_LABEL} kurulamadı: {event}")
    follow = bool(ORMAN_YAKLASMA_KAMERA_TAKIP if follow is None else follow)
    r = rng or random
    geo = orman_choose_geo(geo_used, r)
    vehicle = orman_choose_vehicle(vehicle_used, r)
    people = r.choice((3, 4))
    mid = orman_choose_mid(history or [], r)
    final = orman_choose_final(history or [], mid, r)
    old_tag, new_tag = es.beat_tag(spec["beat_2"], spec["beat_3"]), es.beat_tag(mid, final)
    with es._BEAT_LOCK:   # seçim anı hafızası: atılan K*+L* yerine bu üretimin gerçek çifti
        mem = es._BEAT_MEMORY.get(event, [])
        if mem and mem[-1] == old_tag:
            mem[-1] = new_tag
    for m, v in ((_ORMAN_GEO_MEMORY, geo), (_ORMAN_VEHICLE_MEMORY, vehicle)):
        m.append(v)
        del m[:-12]
    story = orman_story(geo, people, mid, vehicle, final)
    tail = orman_tail(follow)
    prompt = orman_prompt(geo, people, mid, vehicle, final, follow)
    ob = {"event": event, "geo": geo, "people": people, "vehicle": vehicle, "mid": mid, "final": final,
          "follow": follow, "story": story, "suffix": tail, "prompt": prompt}
    ob["lines"] = orman_lines(ob)
    problems = orman_issues({**st, "orman_yaklasma": ob}, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{ORMAN_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = scene.get("combo_key", "")
    if f"#{old_tag}|" in combo:
        combo = combo.replace(f"#{old_tag}|", f"#{new_tag}|")
    name = _OR["geos"][geo]["name"]
    mid_text = orman_mid(mid, vehicle)
    cap_info = {**(st.get("caption_info") or {}), "opening": orman_opening(geo), "people": people,
                "beat_2": mid_text[:-1], "beat_3": _OR["finals"][final][:-1]}
    cam = "takip" if follow else "sabit"
    structure = {**st, "orman_yaklasma": ob, "caption_info": cap_info,
                 "environment": f"Coğrafya: {geo} {name} · kamera = {ORMAN_MODE_LABEL} (balcony of a hillside house, "
                                f"{cam})",
                 "story_source": f"Hikâye: kod (birebir) · {ORMAN_MODE_LABEL}"}
    if st.get("axes_json"):
        structure["axes_json"] = _orman_axes(st["axes_json"], new_tag, geo, vehicle, people)
    plain = " ".join([orman_opening(geo), orman_people(people), mid_text, _OR["finals"][final]])
    trace, axes_line = mode_display(
        scene, structure, mode=ORMAN_MODE_LABEL, camera=f"{cam} ({orman_camera_text(follow)}); balcony of a hillside "
        "house overlooking the street and the burning slope, railing corner in foreground",
        opening=orman_opening(geo), mid=(mid, mid_text), final=(final, _OR["finals"][final]), plain=plain,
        vehicle=vehicle if mid in _OR["vehicle_mids"] else f"{vehicle} (bu ortada araç yok)",
        spot="Balcony of a hillside house overlooking the street and the burning slope (Yaklaşma kalıbı)",
        weather="orange smoky sky (stil eki)",
        axes={"coğrafya": f"{geo} {name}", "araç": vehicle, "kişi": people, "orta": mid, "final": final,
              "kamera modu": cam},
        repeat=f"coğrafya son {ORMAN_GEO_BLOCK} elendi (R1 tohum) · araç son {ORMAN_VEHICLE_BLOCK} · orta son "
               f"{ORMAN_MID_BLOCK} · final tek seçenek N1")
    # normal hattın ortam etiketi ve görünümü prompt'ta yok: gösterilmez
    trace = {**trace, "mode": "orman_yaklasma", "cografya": geo, "count_range": [3, 4], "view": None,
             "view_source": None, "fire_env_label_short": None}
    structure["axes_line"] = axes_line
    out = {**scene, "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt,
           "combo_key": combo, "structure": structure, "trace": trace}
    if scene.get("axes_json"):
        out["axes_json"] = _orman_axes(scene["axes_json"], new_tag, geo, vehicle, people)
    return out


def orman_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin bu kalıpla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    ob = structure["orman_yaklasma"]
    if ob.get("geo") not in _OR["geos"]:
        return [f"coğrafya R1-R6 değil ({ob.get('geo')})"]
    if ob.get("mid") not in _OR["mids"]:
        return [f"orta M2, M3 değil ({ob.get('mid')})"]
    if ob.get("final") not in _OR["finals"]:
        return [f"final N1 değil ({ob.get('final')})"]
    try:
        story = orman_story(ob["geo"], ob["people"], ob["mid"], ob["vehicle"], ob["final"])
        prompt = orman_prompt(ob["geo"], ob["people"], ob["mid"], ob["vehicle"], ob["final"], ob["follow"])
    except es.StructureError as e:
        return [str(e)]
    out = []
    if info.get("style_suffix") != orman_tail(ob["follow"]):
        out.append("stil eki Yaklaşma (orman yangını) kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye kalıpla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt kalıpla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    for bad in ORMAN_FORBIDDEN:
        if bad in text:
            out.append(f"bu modda olmayan ifade var: {bad}")
    for need in ORMAN_REQUIRED:
        if need not in text:
            out.append(f"zorunlu ifade eksik: {need}")
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > ORMAN_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {ORMAN_MAX_WORDS})")
    if len(text) > ORMAN_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {ORMAN_MAX_CHARS})")
    return out


# ── ⭐ Hit kalıbı · Yaklaşma (helikopter) (13 Kas 2026, Bahadır) ──────────────────────────────────────────────────────
# Göl kenarındaki bir kasabada yangın evlerin içinde; gövde tanklı ağır yangın helikopteri gölün üstünde alçakta durup
# sarkan hortumla tankına su emer ve suyu gövdesinin altındaki tanktan yangına boşaltır (14 Kas (2): kova kaldırıldı). Diğer Yaklaşma modlarının yapısı: GPT yok, hikâye tamamen koddan, zaman etiketleri VAR. Helikopterin normal
# yolu değişmez. Kayıt H*+J* (olay bazlı; normal helikopter havuzu F*/G*). Suyun kaynağı her zaman "belly tank"; "helicopter's",
# "bucket" ve "cable" bu modda hiç yok. Araç bu modun kendi
# havuzundan (son 2), kişi 3/4, coğrafya L1-L6 (son 3, Türkiye yok, tohum yok), orta/final LRU son 1, yasak çift yok.
HELI_MODE_LABEL = "⭐ Hit kalıbı · Yaklaşma (helikopter)"
HELI_BUTTON_LABEL = "⭐ Hit kalıbı · Yaklaşma"
HELI_EVENTS = (es.HELICOPTER,)
# Kamera: 14 Kas 2026'dan beri bu modda her zaman sabit (varsayılan False). True verilse bile takip cümlesi çıkmaz.
HELI_YAKLASMA_KAMERA_TAKIP = False
HELI_MAX_WORDS = 230
HELI_MAX_CHARS = 1400
HELI_GEO_BLOCK = 3
HELI_VEHICLE_BLOCK = 2
HELI_MID_BLOCK = 1
HELI_FINAL_BLOCK = 1
YAKLASMA_HELIKOPTER = {
    "geos": {
        "L1": {"name": "Kanada", "place": "a Canadian lakeside town of log houses below snowy peaks"},
        "L2": {"name": "Kaliforniya", "place": "a lakeside mountain town of wooden cabins among tall pines"},
        "L3": {"name": "İtalya", "place": "an Italian lakeside town of terracotta villas and cypress trees"},
        "L4": {"name": "İsviçre", "place": "a Swiss lakeside village of wooden chalets below the Alps"},
        "L5": {"name": "Yunanistan", "place": "a Greek lakeside village of whitewashed houses and olive trees"},
        "L6": {"name": "Avustralya", "place": "an Australian lakeside town of weatherboard houses among eucalyptus"},
    },
    # 14 Kas 2026 (5) v6 (Bahadır): göl sahnesi gölden kalkan, hortumundan su damlayan Skycrane (motor emmeyi
    # çizemiyor); ortalar aşağıdaki caddede ve sert; finalde çatı suyun altında çöküyor. H2'deki araç artikeli kodda
    # ({art}: heli_article, SUV için "an"). Kamera yüksekliği, kompozisyon ve stil eki v5'teki gibi.
    "opening": "Wildfire is burning through {place}, the houses right below engulfed in flames, embers raining onto "
               "the street, while on the distant lake an orange S-64 Skycrane rises off the water, water dripping "
               "from the long hose hanging from its belly.",
    "people": {3: "Three people run below.",
               4: "Four people run below."},
    "vehicles": ("pickup truck", "SUV", "white van"),
    "mids": {
        "H1": "Down in the street, a wall of flames engulfs a fleeing {vehicle}, as the Skycrane flies in from the lake.",
        "H2": "Down in the street, a huge burning pine crashes onto {art} {vehicle} trying to escape, as the Skycrane "
              "flies in from the lake.",
        "H3": "Down in the street, the flames reach a parked {vehicle} and it explodes into a fireball, as the "
              "Skycrane flies in from the lake.",
    },
    "finals": {
        "J1": "The Skycrane stops right above the burning houses below, in front of the camera, and dumps its belly "
              "tank onto a burning roof, the roof caving in with a blast of steam and sparks.",
        "J2": "The Skycrane sweeps low over the burning roofs below, in front of the camera, releasing its belly tank "
              "onto the flames, a roof collapsing in a blast of steam and sparks.",
    },
    "vehicle_mids": ("H1", "H2", "H3"),
    # 14 Kas 2026: kamera bu modda her zaman sabit; takip cümlesi hiç çıkmaz (eski HELI_CAMERA_V1, pasif)
    "camera": "the camera stays fixed",
    "tail": ("Handheld footage from the top-floor balcony of a tall building, high vantage looking steeply down on "
             "the burning houses and the street, the lake far in the distance beyond them, the Skycrane large in "
             "frame, never flying over the camera, a corner of the balcony railing in the foreground; slight hand "
             "shake, the camera stays fixed; one continuous shot, no zoom, no cuts. Water comes only out of the belly "
             "tank and lands right on the burning roofs, never on the camera. Realistic wildfire: towering, roaring "
             "flames and thick smoke, never thin lines of fire. Real time, never slow motion. No readable signs, text "
             "or flags."),
}
# 14 Kas 2026 (5) (Bahadır), v6: v5 üretiminde kamera, kompozisyon ve su hedefi tuttu; hortum yine göle su püskürttü
# (6 üretimdir motor emmeyi çizemiyor), aksiyon zayıftı. 5a78f75 metinleri pasif (coğrafya, insan, stil eki aynen aktif):
HELI_OPENING_V5 = 'Wildfire is burning through {place}, the houses right below engulfed in towering flames, while far out on the distant lake an orange S-64 Skycrane hovers low, a long hose hanging from its belly, its end sunk deep in the water, filling its belly tank.'
HELI_MIDS_V5 = {'H1': 'Down in the street, the flames swallow a parked {vehicle} as the Skycrane flies in from the distant lake.', 'H2': 'Down in the street, a huge burning pine crashes onto a parked {vehicle}, crushing it, as the Skycrane flies in from the distant lake.', 'H3': 'Across the street, a burning roof collapses in a burst of sparks as a {vehicle} speeds away and the Skycrane flies in from the distant lake.'}
HELI_FINALS_V5 = {'J1': 'The Skycrane stops right above the burning houses below, in front of the camera, and dumps its belly tank onto their roofs, a massive curtain of water exploding into white steam.', 'J2': 'The Skycrane sweeps low over the burning roofs below, in front of the camera, releasing its belly tank onto the flames, the fire hissing into white steam.'}
HELI_FORBIDDEN_V5 = ("helicopter's", "bucket", "cable", "terrace", "streaming", "sucking", "spray", "pouring", "toward the camera")
HELI_REQUIRED_V5 = ("S-64 Skycrane", "belly tank", "high vantage", "its end sunk deep in the water")
# 14 Kas 2026 (4) (Bahadır), v5: v4 üretiminde stil ekinde "high vantage" olmadığı için kamera yer seviyesine indi, göl
# kameranın önüne geldi ve yanan evler karşı kıyıda kaldı, hortum göle su püskürttü, orta olaylar uzakta kaldı. Kamera
# yangın tarafında yüksekte, göl uzakta, hortumun ucu suya batık, su kameranın önündeki yanan çatılara. b925c79 metinleri
# pasif (coğrafya L1-L6 aynen aktif):
HELI_OPENING_V4 = 'The burning forest has reached {place} on the shore of a wide lake, and the houses across the street from the terrace are on fire, as a huge orange S-64 Skycrane helicopter with a big belly tank hovers low over the lake, its snorkel hose dipped into the water, rotor wash rippling the surface.'
HELI_PEOPLE_V4 = {3: 'Three people run along the street below.', 4: 'Four people run along the street below.'}
HELI_MIDS_V4 = {'H1': 'Across the street, the flames swallow a parked {vehicle} as the Skycrane lifts off the lake and heads for the burning houses.', 'H2': 'Across the street, a huge burning pine crashes onto a parked {vehicle}, crushing it in a shower of sparks, as the Skycrane lifts off the lake.', 'H3': 'Across the street, a burning roof collapses in a burst of sparks as a {vehicle} speeds away and the Skycrane lifts off the lake.'}
HELI_FINALS_V4 = {'J1': 'The Skycrane hovers right above the burning houses across the street and dumps its whole belly tank, a massive curtain of water slamming onto the flames and exploding into a huge cloud of white steam.', 'J2': 'The Skycrane sweeps low over the burning houses across the street, releasing a long sheet of water from its belly tank straight onto the flames, the fire hissing into white steam.'}
HELI_TAIL_V4 = 'Handheld footage shot from a high terrace overlooking the lake and the burning houses across the street, the Skycrane large in frame, flying from the lake to the burning houses, never over the camera, a corner of the terrace railing in the foreground; slight hand shake, the camera stays fixed; one continuous shot, no zoom, no cuts. Water comes only out of the belly tank and lands right on the flames. Realistic wildfire: towering, roaring flames and thick smoke, never thin lines of fire. Real time, never slow motion. No readable signs, text or flags.'
# 14 Kas 2026 (3) (Bahadır), v4: 4 üretimde "heavy firefighting helicopter" standart helikopter çizildi, "sucking water /
# water streaming from its hose" göle su dökme gibi çizildi, final hedefi belirsizdi, orta olaylar uzaktaydı, göl ve
# ülke belirsizdi. S-64 Skycrane, hedef terasın karşısındaki yanan evler. 97d3b76 metinleri pasif:
HELI_GEOS_V3 = {'L1': 'a Canadian lakeside town of timber houses', 'L2': 'a lakeside mountain town of wooden cabins', 'L3': 'an Italian lakeside town of terracotta-roofed stone houses', 'L4': 'a Swiss lakeside village of wooden chalets', 'L5': 'a Greek lakeside village of whitewashed houses', 'L6': 'an Australian lakeside town of weatherboard houses'}
HELI_OPENING_V3 = 'The burning forest has already reached {place}, a towering wall of flames racing through the houses along the lakeshore, as a heavy firefighting helicopter hovers low over the lake below the terrace, sucking water into its belly tank through a thick hanging hose.'
HELI_PEOPLE_V3 = {3: 'Three people run along the lakeshore below.', 4: 'Four people run along the lakeshore below.'}
HELI_MIDS_V3 = {'H1': 'The helicopter lifts off the lake, water streaming from its hanging hose, and flies low over the rooftops toward the burning houses.', 'H2': 'Just ahead of the flames, a burning pine crashes onto a fleeing {vehicle}, crushing its hood, as the heavy helicopter passes low overhead.', 'H3': 'Just ahead of the flames, the wall of fire swallows a parked {vehicle} as the heavy helicopter passes low overhead.'}
HELI_FINALS_V3 = {'J1': 'The helicopter hovers over the burning houses and opens its belly tank, a massive curtain of water crashing onto the flames and bursting into white steam.', 'J2': 'The helicopter stops over a burning roof and releases its belly tank straight onto it, the roof hissing into steam as it caves in.', 'J3': 'The helicopter sweeps low along the wall of flames at the lakeshore, a long sheet of water pouring from its belly tank onto the fire and bursting into steam.'}
HELI_VEHICLE_MIDS_V3 = ('H2', 'H3')
HELI_TAIL_V3 = 'Handheld footage shot from a high terrace of a lakeside house overlooking the lake and the street, the heavy helicopter in the middle distance, crossing the frame sideways, never flying toward or over the camera, a corner of the terrace railing in the foreground; slight hand shake, the camera stays fixed; one continuous shot, no zoom, no cuts. The water lands only on the burning houses and flames. Never CGI. Realistic wildfire: towering, roaring flames and thick smoke, never thin lines of fire. Real time, never slow motion. No readable signs, text or flags.'
# 14 Kas 2026 (2) (Bahadır): üç üretimde de su kovadan değil gövdeden döküldü, son üretimde yanmayan evlere düştü.
# Kova kaldırıldı, gövde tanklı ağır yangın helikopteri geldi. 96b3d25 kovalı metinler pasif:
HELI_OPENING_V2 = 'The burning forest has already reached {place}, a towering wall of flames racing down the street toward the camera, as a firefighting helicopter skims the lake below the terrace, filling the big orange bucket hanging on a long steel cable far below it.'
HELI_MIDS_V2 = {
    'H1': 'The helicopter lifts off the lake, the full bucket swinging far below on its cable, and flies low over the rooftops toward the flames.',
    'H2': 'Just ahead of the flames, a burning pine crashes onto a fleeing {vehicle}, crushing its hood, as the helicopter passes overhead with the full bucket swinging far below it.',
    'H3': 'Just ahead of the flames, the wall of fire swallows a parked {vehicle} as the helicopter passes overhead with the full bucket swinging far below it.',
}
HELI_FINALS_V2 = {
    'J1': 'The helicopter hovers over the burning houses down the street and the hanging bucket opens, a massive curtain of water falling from it onto the flames and bursting into white steam.',
    'J2': 'The helicopter stops over the burning roof of a house down the street and the bucket far below it dumps its water straight onto the flames, the roof hissing into steam as it caves in.',
    'J3': 'The helicopter sweeps along the wall of flames at the lakeshore and the bucket empties onto it, a long sheet of water crashing onto the fire and bursting into steam.',
}
HELI_TAIL_V2 = 'Handheld footage shot from a high terrace of a lakeside house overlooking the lake and the street, the helicopter clearly visible in the middle distance, crossing the frame sideways, never flying toward or over the camera, a corner of the terrace railing in the foreground; slight hand shake, the camera stays fixed; one continuous shot, no zoom, no cuts. Water falls only out of the bottom of the hanging bucket, never from the body of the helicopter. Never CGI. Realistic wildfire: towering, roaring flames and thick smoke, never thin lines of fire. Real time, never slow motion. No readable signs, text or flags.'
# 14 Kas 2026 (Bahadır): ilk üretimde helikopter kameraya geldi, su terasın altına (yangının olmadığı yere) ve
# gövdeden döküldü ("Right below the terrace ... toward the camera" finalleri + takip kamerası). Eski metinler pasif:
HELI_OPENING_V1 = ("The burning forest has already reached {place}, a towering wall of flames racing down the street "
                   "toward the camera, as a firefighting helicopter skims the lake below the terrace, filling the big "
                   "bucket on its steel cable.")
HELI_MIDS_V1 = {
    "H1": 'The helicopter lifts off the lake with the full bucket swinging on its cable and flies low over the rooftops toward the flames, water dripping from the bucket.',
    "H2": 'Just ahead of the flames, a burning pine crashes onto a fleeing {vehicle}, crushing its hood, as the helicopter flies low overhead with the full bucket.',
    "H3": 'Just ahead of the flames, the wall of fire swallows a parked {vehicle} as the helicopter roars low overhead with the full bucket.',
}
HELI_FINALS_V1 = {
    "J1": 'Right below the terrace, the bucket opens over the burning house and a massive curtain of water hits the flames, bursting into white steam that rushes up toward the camera.',
    "J2": 'Right below the terrace, the bucket dumps its water onto the burning roof of the nearest house just as it caves in, steam and sparks bursting up toward the camera.',
    "J3": 'Right below the terrace, the bucket releases its water onto the wall of flames at the lakeshore, steam and spray blasting across the street toward the camera.',
}
HELI_CAMERA_V1 = {True: 'the camera turns slightly to follow the helicopter', False: 'the camera stays fixed'}
HELI_TAIL_V1 = 'Handheld footage shot from a high terrace of a lakeside house overlooking the lake and the street, the helicopter large and close in frame, a corner of the terrace railing in the foreground; slight hand shake, {camera}; one continuous shot, no zoom, no cuts, no face close to the camera. Water pours only from the bucket on the steel cable, never from the helicopter itself. Civilians in everyday clothes, never CGI. Realistic wildfire: towering, roaring flames and thick smoke, never thin lines or strips of fire. Orange smoky sky. Real time, never slow motion, people run at full speed. No readable signs, text or flags.'
_HL = YAKLASMA_HELIKOPTER
_HELI_GEO_MEMORY: list[str] = []
_HELI_VEHICLE_MEMORY: list[str] = []


def heli_is_active(event: str | None) -> bool:
    return event in HELI_EVENTS


def heli_camera_text(follow: bool | None = None) -> str:
    return _HL["camera"]   # 14 Kas: her zaman sabit


def heli_tail(follow: bool | None = None) -> str:
    return _HL["tail"]   # 14 Kas: kamera stil ekinde birebir sabit


def heli_opening(geo: str) -> str:
    return _HL["opening"].format(place=_HL["geos"][geo]["place"])


def heli_people(n: int) -> str:
    if n not in _HL["people"]:
        raise es.StructureError(f"{HELI_MODE_LABEL}: kişi sayısı 3 ya da 4 olmalı ({n})")
    return _HL["people"][n]


def heli_mid(mid: str, vehicle: str | None) -> str:
    if mid not in _HL["mids"]:
        raise es.StructureError(f"{HELI_MODE_LABEL}: {mid} bu modda yok (orta H1, H2, H3)")
    if mid in _HL["vehicle_mids"] and vehicle not in _HL["vehicles"]:
        raise es.StructureError(f"{HELI_MODE_LABEL}: {mid} için araç yok ({vehicle})")
    return _HL["mids"][mid].format(vehicle=vehicle or "", art=heli_article(vehicle or ""))


def heli_article(word: str) -> str:
    """Araç adının önündeki belirsiz artikel: sesli harf sesiyle başlayan ("SUV" = "es-yu-vi") için "an"."""
    return "an" if word[:1].upper() in "AEIOU" or word.startswith("SUV") else "a"


def heli_final(final: str) -> str:
    if final not in _HL["finals"]:
        raise es.StructureError(f"{HELI_MODE_LABEL}: {final} bu modda yok (final J1, J2)")
    return _HL["finals"][final]


def heli_story(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    """Sıra: açılış + insan + orta + final (aksiyon / "Until the last frame" cümlesi yok)."""
    a, b, c = es.SLICE_LABELS
    return f"{a}: {heli_opening(geo)} {heli_people(people)} {b}: {heli_mid(mid, vehicle)} {c}: {heli_final(final)}"


def heli_prompt(geo: str, people: int, mid: str, vehicle: str | None, final: str, follow: bool | None = None) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(heli_story(geo, people, mid, vehicle, final), heli_tail(follow))


def heli_tags(history: list[str]) -> list[str]:
    return [t for t in es.beat_history(es.HELICOPTER, history or []) if re.fullmatch(r"H\d+\+J\d+", t)]


def heli_choose_mid(history: list[str], rng=None) -> str:
    return _block_pick(list(_HL["mids"]), [t.split("+")[0] for t in heli_tags(history)], HELI_MID_BLOCK, rng)


def heli_choose_final(history: list[str], rng=None) -> str:
    return _block_pick(list(_HL["finals"]), [t.split("+")[1] for t in heli_tags(history)], HELI_FINAL_BLOCK, rng)


def heli_axes_history(records: list | None, key: str) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == es.HELICOPTER and axes.get("mod") == "heli_yaklasma"
                and axes.get(key)):
            out.append(axes[key])
    return out


def heli_choose_geo(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(list(_HL["geos"]), list(_HELI_GEO_MEMORY if used is None else used), HELI_GEO_BLOCK, rng)


def heli_choose_vehicle(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(list(_HL["vehicles"]), list(_HELI_VEHICLE_MEMORY if used is None else used),
                       HELI_VEHICLE_BLOCK, rng)


def heli_camera_label(follow: bool) -> str:
    return "sabit"   # 14 Kas: bu modda takip yok


def heli_lines(hb: dict) -> str:
    text = hb["prompt"]
    return "\n".join([
        f"Mod: {HELI_MODE_LABEL}",
        f"Coğrafya: {hb['geo']} {_HL['geos'][hb['geo']]['name']}",
        f"Araç: {hb['vehicle']}" + ("" if hb["mid"] in _HL["vehicle_mids"] else " (bu ortada araç yok)"),
        f"Orta (4-9s): {hb['mid']} «{heli_mid(hb['mid'], hb['vehicle'])}»",
        f"Final (9-15s): {hb['final']} «{heli_final(hb['final'])}»",
        "Kamera: " + heli_camera_label(hb["follow"]),
        f"Kelime: {len(text.split())} (en fazla {HELI_MAX_WORDS}) · karakter: {len(text)} (en fazla {HELI_MAX_CHARS})",
    ])


def _heli_axes(js, tag: str, geo: str, vehicle: str, people: int):
    import json
    try:
        data = json.loads(js)
    except (TypeError, ValueError):
        return js
    if isinstance(data.get("axes"), dict):
        data["axes"].update({"beats": tag, "mod": "heli_yaklasma", "cografya": geo, "arac": vehicle,
                             "vehicle": vehicle, "people": people})
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def heli_apply(scene: dict, history: list[str] | None = None, rng=None, follow: bool | None = None,
               geo_used: list[str] | None = None, vehicle_used: list[str] | None = None) -> dict:
    """Normal hattın kurduğu helikopter sahnesinden (kayıt aynı) Yaklaşma (helikopter) prompt'unu kurar. Coğrafya L1-L6
    (son 3 elenir), araç (son 2), orta H1-H3 (son 1), final J1-J2 (son 1), kişi 3/4.
    structure["heli_yaklasma"] Kie öncesi son denetimin (submit_issues) ve yeniden yazımın kaynağıdır."""
    import random
    event = scene["event"]
    st = scene.get("structure") or {}
    spec = st.get("spec")
    if not heli_is_active(event) or not spec:
        raise es.StructureError(f"{HELI_MODE_LABEL} kurulamadı: {event}")
    follow = False   # 14 Kas: bu modda kamera her zaman sabit (bayrak ya da parametre takibi açmaz)
    r = rng or random
    geo = heli_choose_geo(geo_used, r)
    vehicle = heli_choose_vehicle(vehicle_used, r)
    people = r.choice((3, 4))
    mid = heli_choose_mid(history or [], r)
    final = heli_choose_final(history or [], r)
    old_tag, new_tag = es.beat_tag(spec["beat_2"], spec["beat_3"]), es.beat_tag(mid, final)
    with es._BEAT_LOCK:   # seçim anı hafızası: atılan F*+G* yerine bu üretimin gerçek çifti
        mem = es._BEAT_MEMORY.get(event, [])
        if mem and mem[-1] == old_tag:
            mem[-1] = new_tag
    for m, v in ((_HELI_GEO_MEMORY, geo), (_HELI_VEHICLE_MEMORY, vehicle)):
        m.append(v)
        del m[:-12]
    story = heli_story(geo, people, mid, vehicle, final)
    tail = heli_tail(follow)
    prompt = heli_prompt(geo, people, mid, vehicle, final, follow)
    hb = {"event": event, "geo": geo, "people": people, "vehicle": vehicle, "mid": mid, "final": final,
          "follow": follow, "story": story, "suffix": tail, "prompt": prompt}
    hb["lines"] = heli_lines(hb)
    problems = heli_issues({**st, "heli_yaklasma": hb}, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{HELI_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = scene.get("combo_key", "")
    if f"#{old_tag}|" in combo:
        combo = combo.replace(f"#{old_tag}|", f"#{new_tag}|")
    name = _HL["geos"][geo]["name"]
    mid_text, final_text = heli_mid(mid, vehicle), heli_final(final)
    cap_info = {**(st.get("caption_info") or {}), "opening": heli_opening(geo), "people": people,
                "beat_2": mid_text[:-1], "beat_3": final_text[:-1]}
    cam = "takip" if follow else "sabit"
    structure = {**st, "heli_yaklasma": hb, "caption_info": cap_info,
                 "environment": f"Coğrafya: {geo} {name} · kamera = {HELI_MODE_LABEL} (top-floor balcony of a tall "
                                f"building, high vantage, {cam})",
                 "story_source": f"Hikâye: kod (birebir) · {HELI_MODE_LABEL}"}
    if st.get("axes_json"):
        structure["axes_json"] = _heli_axes(st["axes_json"], new_tag, geo, vehicle, people)
    plain = " ".join([heli_opening(geo), heli_people(people), mid_text, final_text])
    trace, axes_line = mode_display(
        scene, structure, mode=HELI_MODE_LABEL, camera=f"{cam} ({heli_camera_text(follow)}); top-floor balcony of a "
        "tall building, high vantage over the burning houses, lake far beyond, balcony railing corner in foreground",
        opening=heli_opening(geo), mid=(mid, mid_text), final=(final, final_text), plain=plain,
        vehicle=vehicle if mid in _HL["vehicle_mids"] else f"{vehicle} (bu ortada araç yok)",
        spot="Top-floor balcony of a tall building above the burning houses, lake far beyond (Yaklaşma kalıbı)",
        weather="yok (stil ekinde gökyüzü yok)",
        axes={"coğrafya": f"{geo} {name}", "araç": vehicle if mid in _HL["vehicle_mids"] else "yok",
              "kişi": people, "orta": mid, "final": final, "kamera modu": cam},
        repeat=f"coğrafya son {HELI_GEO_BLOCK} elendi · araç son {HELI_VEHICLE_BLOCK} · orta son {HELI_MID_BLOCK} · "
               f"final son {HELI_FINAL_BLOCK} (yasak çift yok)")
    # normal hattın ortam etiketi ve görünümü prompt'ta yok: gösterilmez
    trace = {**trace, "mode": "heli_yaklasma", "cografya": geo, "count_range": [3, 4], "view": None,
             "view_source": None, "fire_env_label_short": None}
    structure["axes_line"] = axes_line
    out = {**scene, "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt,
           "combo_key": combo, "structure": structure, "trace": trace}
    if scene.get("axes_json"):
        out["axes_json"] = _heli_axes(scene["axes_json"], new_tag, geo, vehicle, people)
    return out


HELI_NO_FLY_PHRASE = "never flying over the camera"
HELI_NO_WATER_ON_CAMERA = "never on the camera"
HELI_FORBIDDEN = ("helicopter's", "bucket", "cable", "terrace", "streaming", "sucking", "spray", "pouring", "sunk",
                  "toward the camera", "a SUV")
HELI_REQUIRED = ("S-64 Skycrane", "belly tank", "high vantage", "water dripping from the long hose")


def heli_camera_issues(text: str, geo: str) -> list[str]:
    """14 Kas (4) v5, (5) v6 ("sunk" ve "a SUV" yasak, "water dripping from the long hose" zorunlu): yasak ifadeler hiçbir yerde yok; "over the camera" sadece "never flying over the camera",
    "on the camera" sadece "never on the camera" içinde; zorunlu ifadeler her prompt'ta var. İhlal = gönderilmez."""
    out = []
    low = text.lower()
    for bad in HELI_FORBIDDEN:
        if bad.lower() in low:
            out.append(f'"{bad}" bu modda yok')
    if "over the camera" in text.replace(HELI_NO_FLY_PHRASE, "", 1):
        out.append(f'"over the camera" "{HELI_NO_FLY_PHRASE}" dışında geçiyor')
    if "on the camera" in text.replace(HELI_NO_WATER_ON_CAMERA, "", 1):
        out.append(f'"on the camera" "{HELI_NO_WATER_ON_CAMERA}" dışında geçiyor')
    for need in HELI_REQUIRED:
        if need not in text:
            out.append(f'"{need}" eksik')
    return out


def heli_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin bu kalıpla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    hb = structure["heli_yaklasma"]
    if hb.get("geo") not in _HL["geos"]:
        return [f"coğrafya L1-L6 değil ({hb.get('geo')})"]
    if hb.get("mid") not in _HL["mids"]:
        return [f"orta H1, H2, H3 değil ({hb.get('mid')})"]
    if hb.get("final") not in _HL["finals"]:
        return [f"final J1, J2 değil ({hb.get('final')})"]
    try:
        story = heli_story(hb["geo"], hb["people"], hb["mid"], hb["vehicle"], hb["final"])
        prompt = heli_prompt(hb["geo"], hb["people"], hb["mid"], hb["vehicle"], hb["final"], hb["follow"])
    except es.StructureError as e:
        return [str(e)]
    out = []
    if info.get("style_suffix") != heli_tail(hb["follow"]):
        out.append("stil eki Yaklaşma (helikopter) kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye kalıpla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt kalıpla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    for bad in ("Full action", "Until the last frame", "helicopter's", "turns slightly to follow"):
        if bad in text:
            out.append(f"bu modda olmayan ifade var: {bad}")
    out += heli_camera_issues(text, hb["geo"])
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > HELI_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {HELI_MAX_WORDS})")
    if len(text) > HELI_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {HELI_MAX_CHARS})")
    return out


# ── ⭐ Hit kalıbı · Yaklaşma (hortum) (14 Kas 2026, Bahadır) ──────────────────────────────────────────────────────────
# Kaynak: kanal rekoru "It came off the sea and straight into the harbor town" (1 Kas paylaşımı, 10M+). Üretim 31 Eki
# 09:52, coastal_tornado_landfall, C1+E1, pencere kadrajı, pickup truck. Hit prompt'unun kamera/kadraj/stil cümleleri
# neredeyse birebir; açılış, O1 ve F1 hit'in kendi sahneleri. Diğer Yaklaşma modlarının yapısı: GPT yok, hikâye tamamen
# koddan, zaman etiketleri VAR. "Hortum karaya vurur" normal yolu (KİLİTLİ) değişmez. Kayıt O*+F* (olay bazlı; normal
# karaya vurur havuzu C*/E*). Coğrafya G1-G6 (son 3, Türkiye yok, G3 tohum: ilk üretimde G3 gelmez), araç bu modun
# kendi havuzundan (son 2), kişi 3/5, orta/final LRU son 1, yasak çift yok. Araç savurma (O1/O2) bu modda serbest.
HORTUM_MODE_LABEL = "⭐ Hit kalıbı · Yaklaşma (hortum)"
HORTUM_BUTTON_LABEL = "⭐ Hit kalıbı · Yaklaşma"
HORTUM_EVENTS = (es.LANDFALL,)
HORTUM_MAX_WORDS = 230
HORTUM_MAX_CHARS = 1400
HORTUM_GEO_BLOCK = 3
HORTUM_GEO_SEED = ("G3",)          # ilk üretimde G3 gelmez (rekor videoya en çok benzeyen)
HORTUM_VEHICLE_BLOCK = 2
HORTUM_MID_BLOCK = 1
HORTUM_FINAL_BLOCK = 1
YAKLASMA_HORTUM = {
    # 15 Kas 2026, Bahadır: her coğrafyanın kendi yer metni (place) ve SAHNE cümlesi (scene; stil ekinde kamera
    # cümlesinin hemen arkasında). Eski yer metinleri HORTUM_PASIF G1_V1-G6_V1.
    "geos": {
        "G1": {"name": "Norveç",
               "place": "a Norwegian fishing harbor of red wooden boathouses and white wooden houses",
               "scene": "Setting: red wooden boathouses on stilts along a fjord quay, white wooden houses and steep "
                        "green mountains behind."},
        "G2": {"name": "İtalya", "place": "an Italian harbor town of pastel houses climbing the hillside",
               "scene": "Setting: tall pastel houses with green shutters stacked up a steep hillside above a small "
                        "stone harbor."},
        "G3": {"name": "İrlanda", "place": "an Irish harbor town of painted terraced houses",
               "scene": "Setting: painted two-storey terraced houses with slate roofs along a stone harbor wall, a "
                        "grey Atlantic sea."},
        "G4": {"name": "Danimarka", "place": "a Danish harbor town of brick canal houses",
               "scene": "Setting: narrow brick houses with steep tiled roofs along a canal quay with old wooden "
                        "boats."},
        "G5": {"name": "Brezilya", "place": "a Brazilian harbor town of colonial houses",
               "scene": "Setting: low whitewashed colonial houses with blue and yellow trim, a cobblestone seafront "
                        "street, palm trees and fishing boats."},
        "G6": {"name": "Hindistan", "place": "an Indian harbor town of Portuguese-style houses",
               "scene": "Setting: weathered Portuguese-style houses with balconies and flat roofs, a seafront road, "
                        "wooden fishing boats pulled up on the shore."},
    },
    "opening": "The tornado makes landfall from the sea at {place}, crosses the seafront road and flips a parked car "
               "onto its side, then heads up the street toward the camera.",
    "people": {3: "Three people run away from the tornado.",
               5: "Five people run away from the tornado."},
    "vehicles": ("pickup truck", "delivery van", "SUV"),
    # 15 Kas: aktif ortalar O1 (yeni: araç havaya) + O2; ikisinde de araç var. Eski O1 ve O3 HORTUM_PASIF (O1_V1, O3_V1)
    "mids": {
        "O1": "The tornado lifts the {vehicle} off the street, spins it through the air and smashes it down onto the "
              "quay.",
        "O2": "The tornado lifts the {vehicle} off the quay and hurls it, in one piece, into the harbor water.",
    },
    # 15 Kas: F1/F2'den "colorful" çıktı (eskiler HORTUM_PASIF F1_V1, F2_V1)
    "finals": {
        "F1": "Right across from the window, the tornado tears the roof off a house, the pieces flying past the camera.",
        "F2": "Right across from the window, the tornado rips the whole front wall off a house, furniture swirling up "
              "into the funnel.",
        "F3": "Right below the window, the tornado hits the row of houses, roofs and balconies peeling off one after "
              "another.",
    },
    "vehicle_mids": ("O1", "O2"),
    "camera": "the camera stays fixed, tilting only slightly",
    # 15 Kas: sabit "Setting: ..." cümlesi çıktı (HORTUM_PASIF STIL_V1); {scene} = seçilen coğrafyanın sahne cümlesi
    "tail": ("Handheld footage filmed through an open upper-floor window across from the harbor street, high vantage; "
             "slight hand shake, the camera stays fixed, tilting only slightly, never descending, the tornado always "
             "in frame, the open window frame at one side; one continuous shot, no zoom, no cuts, no person or face "
             "close to the camera. {scene} All people are ordinary civilians in everyday clothes, no hazmat suits, "
             "natural light, never CGI. Everything moves in real time, never in slow motion, people run at full "
             "speed."),
}
# Pasif kayıt (15 Kas 2026, Bahadır): 15 Kas üretimlerinde sabit sahne cümlesi her ülkede aynı renkli liman evlerini
# çizdirdi, O3 kadrajı tekne havuzuna kilitledi (İtalya 4/10), O1 (kaldırıma itme) iki üretimde de çizilmedi.
# Bu metinler hiçbir üretimde seçilmez.
HORTUM_PASIF = {
    "G1_V1": "a Norwegian harbor town of colorful wooden fishing houses",
    "G2_V1": "an Italian harbor town of pastel houses climbing the hillside",
    "G3_V1": "an Irish harbor town of colorful terraced houses",
    "G4_V1": "a Danish harbor town of colorful canal houses",
    "G5_V1": "a Brazilian harbor town of colorful colonial houses",
    "G6_V1": "an Indian harbor town of colorful Portuguese-style houses",
    "STIL_V1": "Setting: colorful houses along a stone quay with small sailboats.",
    "O1_V1": "The tornado shoves the {vehicle} sideways across the street and slams it into the far curb.",
    "O3_V1": "The tornado rips the moored sailboats out of the water and flings them onto the quay.",
    "F1_V1": "Right across from the window, the tornado tears the roof off a colorful house, the pieces flying past "
             "the camera.",
    "F2_V1": "Right across from the window, the tornado rips the whole front wall off a colorful house, furniture "
             "swirling up into the funnel.",
}
HORTUM_O2_WARNING = "⚠️ Araç savurma ortası (O2): videoda aracın tek parça kalıp kalmadığını kontrol et."  # pasif (15 Kas (2) öncesi)
# 15 Kas (2): yeni O1 de aracı havaya kaldırıyor; uyarı O1 ve O2'de (prompt metni değişmedi)
HORTUM_VEHICLE_WARNING = "⚠️ Araç ortası: videoda aracın tek parça kalıp kalmadığını kontrol et."
HORTUM_WARNING_MIDS = ("O1", "O2")
HORTUM_REQUIRED = ("high vantage", "open upper-floor window")
HORTUM_FORBIDDEN = ("colorful houses along a stone quay", "Full action", "Until the last frame")
_HT = YAKLASMA_HORTUM
_HORTUM_GEO_MEMORY: list[str] = []
_HORTUM_VEHICLE_MEMORY: list[str] = []


def hortum_is_active(event: str | None) -> bool:
    return event in HORTUM_EVENTS


def hortum_camera_text(follow: bool | None = None) -> str:
    return _HT["camera"]


def hortum_scene(geo: str) -> str:
    return _HT["geos"][geo]["scene"]


def hortum_tail(geo: str, follow: bool | None = None) -> str:
    """15 Kas: stil eki coğrafyaya bağlı (kamera cümlesinin hemen arkasında seçilen coğrafyanın sahne cümlesi)."""
    return _HT["tail"].format(scene=hortum_scene(geo))


def hortum_opening(geo: str) -> str:
    return _HT["opening"].format(place=_HT["geos"][geo]["place"])


def hortum_people(n: int) -> str:
    if n not in _HT["people"]:
        raise es.StructureError(f"{HORTUM_MODE_LABEL}: kişi sayısı 3 ya da 5 olmalı ({n})")
    return _HT["people"][n]


def hortum_mid(mid: str, vehicle: str | None) -> str:
    if mid not in _HT["mids"]:
        raise es.StructureError(f"{HORTUM_MODE_LABEL}: {mid} bu modda yok (orta O1, O2)")
    if mid in _HT["vehicle_mids"] and vehicle not in _HT["vehicles"]:
        raise es.StructureError(f"{HORTUM_MODE_LABEL}: {mid} için araç yok ({vehicle})")
    return _HT["mids"][mid].format(vehicle=vehicle or "")


def hortum_final(final: str) -> str:
    if final not in _HT["finals"]:
        raise es.StructureError(f"{HORTUM_MODE_LABEL}: {final} bu modda yok (final F1, F2, F3)")
    return _HT["finals"][final]


def hortum_story(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    """Sıra: açılış + insan + orta + final (aksiyon / "Until the last frame" cümlesi yok)."""
    a, b, c = es.SLICE_LABELS
    return (f"{a}: {hortum_opening(geo)} {hortum_people(people)} {b}: {hortum_mid(mid, vehicle)} "
            f"{c}: {hortum_final(final)}")


def hortum_prompt(geo: str, people: int, mid: str, vehicle: str | None, final: str, follow: bool | None = None) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(hortum_story(geo, people, mid, vehicle, final), hortum_tail(geo, follow))


def hortum_tags(history: list[str]) -> list[str]:
    return [t for t in es.beat_history(es.LANDFALL, history or []) if re.fullmatch(r"O\d+\+F\d+", t)]


def hortum_choose_mid(history: list[str], rng=None) -> str:
    return _block_pick(list(_HT["mids"]), [t.split("+")[0] for t in hortum_tags(history)], HORTUM_MID_BLOCK, rng)


def hortum_choose_final(history: list[str], rng=None) -> str:
    return _block_pick(list(_HT["finals"]), [t.split("+")[1] for t in hortum_tags(history)], HORTUM_FINAL_BLOCK, rng)


def hortum_axes_history(records: list | None, key: str) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == es.LANDFALL and axes.get("mod") == "hortum_yaklasma"
                and axes.get(key)):
            out.append(axes[key])
    return out


def hortum_choose_geo(used: list[str] | None = None, rng=None) -> str:
    seen = list(HORTUM_GEO_SEED) + list(_HORTUM_GEO_MEMORY if used is None else used)
    return _block_pick(list(_HT["geos"]), seen, HORTUM_GEO_BLOCK, rng)


def hortum_choose_vehicle(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(list(_HT["vehicles"]), list(_HORTUM_VEHICLE_MEMORY if used is None else used),
                       HORTUM_VEHICLE_BLOCK, rng)


def hortum_lines(tb: dict) -> str:
    text = tb["prompt"]
    lines = [
        f"Mod: {HORTUM_MODE_LABEL}",
        f"Coğrafya: {tb['geo']} {_HT['geos'][tb['geo']]['name']}",
        f"Sahne: «{hortum_scene(tb['geo'])}»",   # 15 Kas: seçilen coğrafyanın sahne cümlesi
        f"Araç: {tb['vehicle']}" + ("" if tb["mid"] in _HT["vehicle_mids"] else " (bu ortada araç yok)"),
        f"Orta (4-9s): {tb['mid']} «{hortum_mid(tb['mid'], tb['vehicle'])}»",
        f"Final (9-15s): {tb['final']} «{hortum_final(tb['final'])}»",
        "Kamera: sabit (hafifçe eğilir, açık üst kat penceresi)",
        f"Kelime: {len(text.split())} (en fazla {HORTUM_MAX_WORDS}) · karakter: {len(text)} (en fazla {HORTUM_MAX_CHARS})",
    ]
    if tb["mid"] in HORTUM_WARNING_MIDS:
        lines.append(HORTUM_VEHICLE_WARNING)
    return "\n".join(lines)


def _hortum_axes(js, tag: str, geo: str, vehicle: str | None, people: int):
    import json
    try:
        data = json.loads(js)
    except (TypeError, ValueError):
        return js
    if isinstance(data.get("axes"), dict):
        data["axes"].update({"beats": tag, "mod": "hortum_yaklasma", "cografya": geo, "arac": vehicle,
                             "vehicle": vehicle, "people": people})
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hortum_apply(scene: dict, history: list[str] | None = None, rng=None, follow: bool | None = None,
                 geo_used: list[str] | None = None, vehicle_used: list[str] | None = None) -> dict:
    """Normal hattın kurduğu "hortum karaya vurur" sahnesinden (kayıt aynı) Yaklaşma (hortum) prompt'unu kurar.
    Coğrafya G1-G6 (son 3 elenir, G3 tohum), araç (son 2), orta O1-O2 (son 1), final F1-F3 (son 1), kişi 3/5.
    15 Kas: iki ortada da araç var, araç geçmişi her üretimde ilerler.
    structure["hortum_yaklasma"] Kie öncesi son denetimin (submit_issues) ve yeniden yazımın kaynağıdır."""
    import random
    event = scene["event"]
    st = scene.get("structure") or {}
    spec = st.get("spec")
    if not hortum_is_active(event) or not spec:
        raise es.StructureError(f"{HORTUM_MODE_LABEL} kurulamadı: {event}")
    follow = False   # kamera sabit, sadece hafifçe eğilir (stil eki birebir)
    r = rng or random
    geo = hortum_choose_geo(geo_used, r)
    vehicle = hortum_choose_vehicle(vehicle_used, r)
    people = r.choice((3, 5))
    mid = hortum_choose_mid(history or [], r)
    final = hortum_choose_final(history or [], r)
    old_tag, new_tag = es.beat_tag(spec["beat_2"], spec["beat_3"]), es.beat_tag(mid, final)
    with es._BEAT_LOCK:   # seçim anı hafızası: atılan C*+E* yerine bu üretimin gerçek çifti
        mem = es._BEAT_MEMORY.get(event, [])
        if mem and mem[-1] == old_tag:
            mem[-1] = new_tag
    has_vehicle = mid in _HT["vehicle_mids"]
    # araç hafızası sadece aracın gerçekten prompt'a girdiği ortada (O1/O2) ilerler (Notion "arac" ile aynı)
    for m, v in ((_HORTUM_GEO_MEMORY, geo), (_HORTUM_VEHICLE_MEMORY, vehicle if has_vehicle else None)):
        if v is not None:
            m.append(v)
            del m[:-12]
    story = hortum_story(geo, people, mid, vehicle, final)
    tail = hortum_tail(geo, follow)
    prompt = hortum_prompt(geo, people, mid, vehicle, final, follow)
    tb = {"event": event, "geo": geo, "people": people, "vehicle": vehicle, "mid": mid, "final": final,
          "follow": follow, "story": story, "suffix": tail, "prompt": prompt}
    tb["lines"] = hortum_lines(tb)
    problems = hortum_issues({**st, "hortum_yaklasma": tb}, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{HORTUM_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = scene.get("combo_key", "")
    if f"#{old_tag}|" in combo:
        combo = combo.replace(f"#{old_tag}|", f"#{new_tag}|")
    name = _HT["geos"][geo]["name"]
    mid_text, final_text = hortum_mid(mid, vehicle), hortum_final(final)
    cap_info = {**(st.get("caption_info") or {}), "opening": hortum_opening(geo), "people": people,
                "beat_2": mid_text[:-1], "beat_3": final_text[:-1]}
    structure = {**st, "hortum_yaklasma": tb, "caption_info": cap_info,
                 "environment": f"Coğrafya: {geo} {name} · kamera = {HORTUM_MODE_LABEL} (open upper-floor window "
                                "across from the harbor street, high vantage, sabit)",
                 "story_source": f"Hikâye: kod (birebir) · {HORTUM_MODE_LABEL}"}
    if st.get("axes_json"):
        structure["axes_json"] = _hortum_axes(st["axes_json"], new_tag, geo, vehicle if has_vehicle else None, people)
    plain = " ".join([hortum_opening(geo), hortum_people(people), mid_text, final_text])
    trace, axes_line = mode_display(
        scene, structure, mode=HORTUM_MODE_LABEL, camera=f"sabit ({hortum_camera_text(follow)}); open upper-floor "
        "window across from the harbor street, high vantage, open window frame at one side",
        opening=hortum_opening(geo), mid=(mid, mid_text), final=(final, final_text), plain=plain,
        vehicle=vehicle if has_vehicle else f"{vehicle} (bu ortada araç yok)",
        spot="Open upper-floor window across from the harbor street (Yaklaşma kalıbı)",
        weather="yok (stil ekinde natural light)",
        axes={"coğrafya": f"{geo} {name}", "araç": vehicle if has_vehicle else "yok",
              "kişi": people, "orta": mid, "final": final, "kamera modu": "sabit"},
        repeat=f"coğrafya son {HORTUM_GEO_BLOCK} elendi (G3 tohum) · araç son {HORTUM_VEHICLE_BLOCK} · orta son "
               f"{HORTUM_MID_BLOCK} · final son {HORTUM_FINAL_BLOCK} (yasak çift yok)")
    # normal hattın ortam etiketi ve görünümü prompt'ta yok: gösterilmez
    trace = {**trace, "mode": "hortum_yaklasma", "cografya": geo, "count_range": [3, 5], "view": None,
             "view_source": None, "fire_env_label_short": None}
    structure["axes_line"] = axes_line
    out = {**scene, "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt,
           "combo_key": combo, "structure": structure, "trace": trace}
    if scene.get("axes_json"):
        out["axes_json"] = _hortum_axes(scene["axes_json"], new_tag, geo, vehicle if has_vehicle else None, people)
    return out


def hortum_camera_issues(text: str, geo: str | None = None) -> list[str]:
    """Kie öncesi son kontrol: "high vantage", "open upper-floor window", G1-G6'dan birinin place metni ve aynı
    coğrafyanın sahne cümlesi var; eski sabit sahne ("colorful houses along a stone quay"), "Full action" ve
    "Until the last frame" yok. İhlal = gönderilmez."""
    out = []
    for need in HORTUM_REQUIRED:
        if need not in text:
            out.append(f'"{need}" eksik')
    places = [g for g, v in _HT["geos"].items() if v["place"] in text]
    if not places:
        out.append("G1-G6 yer metni yok")
    elif geo is not None and places != [geo]:
        out.append(f"yer metni seçilen coğrafya değil ({geo}: {places})")
    scenes = [g for g, v in _HT["geos"].items() if v["scene"] in text]   # 15 Kas: coğrafyanın sahne cümlesi
    if not scenes:
        out.append("G1-G6 sahne cümlesi yok")
    elif geo is not None and scenes != [geo]:
        out.append(f"sahne cümlesi seçilen coğrafya değil ({geo}: {scenes})")
    for bad in HORTUM_FORBIDDEN:
        if bad in text:
            out.append(f"bu modda olmayan ifade var: {bad}")
    return out


def hortum_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin bu kalıpla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    tb = structure["hortum_yaklasma"]
    if tb.get("geo") not in _HT["geos"]:
        return [f"coğrafya G1-G6 değil ({tb.get('geo')})"]
    if tb.get("mid") not in _HT["mids"]:
        return [f"orta O1, O2 değil ({tb.get('mid')})"]
    if tb.get("final") not in _HT["finals"]:
        return [f"final F1, F2, F3 değil ({tb.get('final')})"]
    try:
        story = hortum_story(tb["geo"], tb["people"], tb["mid"], tb["vehicle"], tb["final"])
        prompt = hortum_prompt(tb["geo"], tb["people"], tb["mid"], tb["vehicle"], tb["final"], tb["follow"])
    except es.StructureError as e:
        return [str(e)]
    out = []
    if info.get("style_suffix") != hortum_tail(tb["geo"], tb["follow"]):
        out.append("stil eki Yaklaşma (hortum) kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye kalıpla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt kalıpla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out += hortum_camera_issues(text, tb["geo"])
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > HORTUM_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {HORTUM_MAX_WORDS})")
    if len(text) > HORTUM_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {HORTUM_MAX_CHARS})")
    return out


# ── ⭐ Hit kalıbı · Yaklaşma (cadde) (15 Kas 2026, Bahadır) ───────────────────────────────────────────────────────────
# Kaynak: 17 Eki hit'i (1,2M; "Hortum sahil caddesini süpürür", Onay P6+Q3, beyaz minibüs, yüksek cam korkuluklu
# balkon). YAKLASMA_HORTUM ile aynı düzen: GPT yok, hikâye tamamen koddan, zaman etiketleri VAR. "Hortum sahil caddesini
# süpürür" normal yolu değişmez. Kayıt O*+F* (olay bazlı; normal cadde havuzu P*/Q*). Coğrafya G1-G6 (son 3, G1 tohum:
# ilk 3 üretimde G1 gelmez), araç bu modun kendi havuzundan (son 2), kişi 3/5, orta/final LRU son 1, yasak çift yok.
# İki ortada da araç var (araç savurma bu modda serbest).
# 15 Kas (3), Bahadır: mod hit'ten çok uzaklaştı (200 kelime, geniş açı, uzun kamera kuralları, "the sea at its end");
# 15 Kas Meksika üretiminde hortum ilk 6 sn caddenin ucunda kaldı, video 2/10. Hit'in kendi Kie prompt'una dönüldü,
# metin birebir, 4 değişiklik: coğrafya kelimesi, park halindeki araç + hurda, kameraya yakın final, "pans to follow"
# yerine hafif takip. "eye level, normal lens" hit'in ifadesi (normal lens hortumu büyük ve yakın gösterir), bu modda
# serbest. Kişi 5/6 (hit'in cümlesi). Önceki metinlerin hepsi CADDE_PASIF (_V2).
CADDE_MODE_LABEL = "⭐ Hit kalıbı · Yaklaşma (cadde)"
CADDE_BUTTON_LABEL = "⭐ Hit kalıbı · Yaklaşma"
CADDE_EVENTS = (es.AVENUE,)
CADDE_MAX_WORDS = 230
CADDE_MAX_CHARS = 1400
CADDE_GEO_BLOCK = 3
CADDE_GEO_SEED = ("G1",)           # G1 başlangıçta "kullanıldı": ilk 3 üretimde G1 gelmez
CADDE_VEHICLE_BLOCK = 2
CADDE_MID_BLOCK = 1
CADDE_FINAL_BLOCK = 1
YAKLASMA_CADDE = {
    "geos": {
        "G1": {"name": "ABD", "place": "a Californian beach town"},
        "G2": {"name": "Brezilya", "place": "a Brazilian beach city with wavy mosaic sidewalks"},
        # 15 Kas (2): alçak ölçek (eski G3/G5/G6 yer metinleri CADDE_PASIF G3_V1, G5_V1, G6_V1)
        "G3": {"name": "Avustralya", "place": "an Australian beach town of low-rise surf shops and cafes"},
        "G4": {"name": "Meksika", "place": "a Mexican beach town of colorful low buildings"},
        "G5": {"name": "İspanya", "place": "a Spanish seaside town of low whitewashed houses"},
        "G6": {"name": "Hindistan", "place": "an Indian seaside town of low pastel buildings"},
    },
    # 15 Kas (3): hit'in metni (eski açılış, insan, orta, final, stil eki CADDE_PASIF *_V2)
    "opening": "A violent tornado sweeps down a palm-lined coastal avenue of {place}, hurling signs, branches and "
               "debris along the road.",
    "people": {5: "Five people scramble in a panic, sprinting down the sidewalk to escape its furious path.",
               6: "Six people scramble in a panic, sprinting down the sidewalk to escape its furious path."},
    "vehicles": ("white van", "pickup truck", "SUV"),
    "mids": {
        "O1": "The tornado lifts a parked {vehicle} skyward, spinning it wildly before it crashes, wrecked, onto the "
              "avenue.",
        "O2": "The tornado flips a parked {vehicle} and sends it rolling over and over down the avenue until it stops, "
              "crushed, on its roof.",
    },
    "finals": {
        "F1": "Right across the street, the tornado tears the roof off a building, the pieces flying past the camera.",
        "F2": "Right across the street, the tornado rips the balconies and front wall off a building, debris flying "
              "past the camera.",
        "F3": "Right below the balcony, the tornado rips the palm trees out by the roots and hurls them past the "
              "camera.",
    },
    "vehicle_mids": ("O1", "O2"),
    "camera": "the camera follows the tornado only slightly, keeping the avenue in frame",
    # 15 Kas (3): hit'in eki birebir, sadece "pans to follow" yerine hafif takip
    "tail": ("Handheld footage shot by a person standing on a high balcony across the street, overlooking the avenue, "
             "eye level, normal lens; slight hand shake, the camera follows the tornado only slightly, keeping the "
             "avenue in frame; no zoom, no cuts. Bystanders wear civilian clothes, never hi-vis PPE on civilians; "
             "emergency responders wear service uniforms. Raw natural light matching the weather, never glossy or "
             "CGI; no white hazmat suits."),
}
# 15 Kas (2), Bahadır: ilk cadde üretimi (İspanya, O1+F2) 6/10. "white apartment blocks", "high-rise hotels", "high
# balcony", "wide avenue" kamerayı 10. kata çıkardı; savrulan minibüs yere inip yoluna devam etti. Eski metinler pasif.
CADDE_PASIF = {
    "G3_V1": "an Australian beach city lined with high-rise hotels",
    "G5_V1": "a Spanish seaside town of white apartment blocks",
    "G6_V1": "an Indian seaside city of pastel apartment blocks",
    "O1_V1": "The tornado sweeps the {vehicle} up into the air, spins it, and crashes it down across the avenue.",
    "O2_V1": "The tornado flips the {vehicle} and sends it rolling over and over down the avenue toward the camera.",
    "F1_V1": "Right across from the balcony, the tornado tears the roof off an apartment building, the pieces flying "
             "past the camera.",
    "F2_V1": "Right across from the balcony, the tornado rips the balconies and front wall off an apartment building, "
             "debris flying past the camera.",
    "STIL_V1": ("Handheld footage shot from a high balcony with a glass railing across the avenue, high vantage; "
                "slight hand shake, the camera stays fixed, tilting only slightly, never descending, the tornado "
                "always in frame, the glass railing in the foreground; one continuous shot, no zoom, no cuts, no "
                "person or face close to the camera. Setting: a wide palm-lined avenue with parked cars and the sea "
                "at its end. All people are ordinary civilians in everyday clothes, no hazmat suits, natural light "
                "under grey storm clouds, never CGI. Everything moves in real time, never in slow motion, people run "
                "at full speed."),
    "KAMERA_SATIRI_V1": "Kamera: sabit (hafifçe eğilir, cam korkuluklu yüksek balkon)",
    # 15 Kas (3): hit prompt'una dönüş; 15 Kas (2) metinlerinin hepsi (açılış, insan 3/5 ve F3 ilk sürümden beri aynıydı)
    "ACILIS_V2": "A violent tornado sweeps down a palm-lined coastal avenue of {place}, hurling signs, branches and "
                 "debris along the road, and heads straight toward the camera.",
    "INSAN_3_V2": "Three people sprint along the sidewalk toward the camera, fleeing the tornado.",
    "INSAN_5_V2": "Five people sprint along the sidewalk toward the camera, fleeing the tornado.",
    "O1_V2": "The tornado sweeps a parked {vehicle} up into the air, spins it, and slams it down on its roof across "
             "the avenue, where it stays wrecked.",
    "O2_V2": "The tornado flips a parked {vehicle} and sends it rolling over and over down the avenue toward the "
             "camera until it stops, crushed, on its side.",
    "F1_V2": "Right across from the balcony, the tornado tears the roof off the building across the street, the "
             "pieces flying past the camera.",
    "F2_V2": "Right across from the balcony, the tornado rips the balconies and front wall off the building across "
             "the street, debris flying past the camera.",
    "F3_V2": "Right below the balcony, the tornado rips the palm trees out by the roots and hurls them past the "
             "camera.",
    "KAMERA_V2": "the camera stays fixed, tilting only slightly",
    "STIL_V2": ("Handheld footage shot from a third-floor balcony with a glass railing across the avenue, high "
                "vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the "
                "tornado always in frame, the glass railing in the foreground; one continuous shot, no zoom, no cuts, "
                "no person or face close to the camera. Setting: a two-lane palm-lined avenue with cars parked on both "
                "sides, low-rise buildings, the sea at its end. All people are ordinary civilians in everyday clothes, "
                "no hazmat suits, natural light under grey storm clouds, never CGI. Everything moves in real time, "
                "never in slow motion, people run at full speed."),
    "KAMERA_SATIRI_V2": "Kamera: sabit (hafifçe eğilir, cam korkuluklu 3. kat balkon)",
    "ZORUNLU_V2": ("high vantage", "glass railing", "third-floor balcony", "a parked"),
    "YASAK_V2": ("pans to follow", "eye level", "Full action", "Until the last frame", "high-rise", "apartment block",
                 "wide palm-lined avenue"),
}
CADDE_CAMERA_LINE = "Kamera: hit kamerası (yüksek balkon, normal lens, hafif takip)"
CADDE_VEHICLE_WARNING = "⚠️ Araç ortası: videoda aracın tek parça kalıp kalmadığını kontrol et."
# 15 Kas (3): "eye level" bu modda serbest (hit'in ifadesi); diğer modların yasakları aynı
CADDE_REQUIRED = ("high balcony across the street", "normal lens", "a parked")
CADDE_FORBIDDEN = ("pans to follow", "third-floor", "glass railing", "the sea at its end", "Full action",
                   "Until the last frame")
_CD = YAKLASMA_CADDE
_CADDE_GEO_MEMORY: list[str] = []
_CADDE_VEHICLE_MEMORY: list[str] = []


def cadde_is_active(event: str | None) -> bool:
    return event in CADDE_EVENTS


def cadde_camera_text(follow: bool | None = None) -> str:
    return _CD["camera"]


def cadde_tail(follow: bool | None = None) -> str:
    return _CD["tail"]


def cadde_opening(geo: str) -> str:
    return _CD["opening"].format(place=_CD["geos"][geo]["place"])


def cadde_people(n: int) -> str:
    if n not in _CD["people"]:
        raise es.StructureError(f"{CADDE_MODE_LABEL}: kişi sayısı 5 ya da 6 olmalı ({n})")
    return _CD["people"][n]


def cadde_mid(mid: str, vehicle: str | None) -> str:
    if mid not in _CD["mids"]:
        raise es.StructureError(f"{CADDE_MODE_LABEL}: {mid} bu modda yok (orta O1, O2)")
    if mid in _CD["vehicle_mids"] and vehicle not in _CD["vehicles"]:
        raise es.StructureError(f"{CADDE_MODE_LABEL}: {mid} için araç yok ({vehicle})")
    return _CD["mids"][mid].format(vehicle=vehicle or "")


def cadde_final(final: str) -> str:
    if final not in _CD["finals"]:
        raise es.StructureError(f"{CADDE_MODE_LABEL}: {final} bu modda yok (final F1, F2, F3)")
    return _CD["finals"][final]


def cadde_story(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    """Sıra: açılış + insan + orta + final (aksiyon / "Until the last frame" cümlesi yok)."""
    a, b, c = es.SLICE_LABELS
    return (f"{a}: {cadde_opening(geo)} {cadde_people(people)} {b}: {cadde_mid(mid, vehicle)} "
            f"{c}: {cadde_final(final)}")


def cadde_prompt(geo: str, people: int, mid: str, vehicle: str | None, final: str, follow: bool | None = None) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(cadde_story(geo, people, mid, vehicle, final), cadde_tail(follow))


def cadde_tags(history: list[str]) -> list[str]:
    return [t for t in es.beat_history(es.AVENUE, history or []) if re.fullmatch(r"O\d+\+F\d+", t)]


def cadde_choose_mid(history: list[str], rng=None) -> str:
    return _block_pick(list(_CD["mids"]), [t.split("+")[0] for t in cadde_tags(history)], CADDE_MID_BLOCK, rng)


def cadde_choose_final(history: list[str], rng=None) -> str:
    return _block_pick(list(_CD["finals"]), [t.split("+")[1] for t in cadde_tags(history)], CADDE_FINAL_BLOCK, rng)


def cadde_axes_history(records: list | None, key: str) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == es.AVENUE and axes.get("mod") == "cadde_yaklasma"
                and axes.get(key)):
            out.append(axes[key])
    return out


def cadde_choose_geo(used: list[str] | None = None, rng=None) -> str:
    seen = list(CADDE_GEO_SEED) + list(_CADDE_GEO_MEMORY if used is None else used)
    return _block_pick(list(_CD["geos"]), seen, CADDE_GEO_BLOCK, rng)


def cadde_choose_vehicle(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(list(_CD["vehicles"]), list(_CADDE_VEHICLE_MEMORY if used is None else used),
                       CADDE_VEHICLE_BLOCK, rng)


def cadde_lines(tb: dict) -> str:
    text = tb["prompt"]
    lines = [
        f"Mod: {CADDE_MODE_LABEL}",
        f"Coğrafya: {tb['geo']} {_CD['geos'][tb['geo']]['name']}",
        f"Araç: {tb['vehicle']}" + ("" if tb["mid"] in _CD["vehicle_mids"] else " (bu ortada araç yok)"),
        f"Orta (4-9s): {tb['mid']} «{cadde_mid(tb['mid'], tb['vehicle'])}»",
        f"Final (9-15s): {tb['final']} «{cadde_final(tb['final'])}»",
        f"Kişi: {tb['people']}",
        CADDE_CAMERA_LINE,
        f"Kelime: {len(text.split())} (en fazla {CADDE_MAX_WORDS}) · karakter: {len(text)} (en fazla {CADDE_MAX_CHARS})",
    ]
    if tb["mid"] in _CD["vehicle_mids"]:
        lines.append(CADDE_VEHICLE_WARNING)
    return "\n".join(lines)


def _cadde_axes(js, tag: str, geo: str, vehicle: str | None, people: int):
    import json
    try:
        data = json.loads(js)
    except (TypeError, ValueError):
        return js
    if isinstance(data.get("axes"), dict):
        data["axes"].update({"beats": tag, "mod": "cadde_yaklasma", "cografya": geo, "arac": vehicle,
                             "vehicle": vehicle, "people": people})
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def cadde_apply(scene: dict, history: list[str] | None = None, rng=None, follow: bool | None = None,
                geo_used: list[str] | None = None, vehicle_used: list[str] | None = None) -> dict:
    """Normal hattın kurduğu "hortum sahil caddesini süpürür" sahnesinden (kayıt aynı) Yaklaşma (cadde) prompt'unu
    kurar. Coğrafya G1-G6 (son 3 elenir, G1 tohum), araç (son 2), orta O1-O2 (son 1), final F1-F3 (son 1), kişi 5/6.
    structure["cadde_yaklasma"] Kie öncesi son denetimin (submit_issues) ve yeniden yazımın kaynağıdır."""
    import random
    event = scene["event"]
    st = scene.get("structure") or {}
    spec = st.get("spec")
    if not cadde_is_active(event) or not spec:
        raise es.StructureError(f"{CADDE_MODE_LABEL} kurulamadı: {event}")
    follow = False   # 15 Kas (3): hafif takip stil ekinin içinde (birebir); ayrı takip seçeneği yok
    r = rng or random
    geo = cadde_choose_geo(geo_used, r)
    vehicle = cadde_choose_vehicle(vehicle_used, r)
    people = r.choice((5, 6))
    mid = cadde_choose_mid(history or [], r)
    final = cadde_choose_final(history or [], r)
    old_tag, new_tag = es.beat_tag(spec["beat_2"], spec["beat_3"]), es.beat_tag(mid, final)
    with es._BEAT_LOCK:   # seçim anı hafızası: atılan P*+Q* yerine bu üretimin gerçek çifti
        mem = es._BEAT_MEMORY.get(event, [])
        if mem and mem[-1] == old_tag:
            mem[-1] = new_tag
    has_vehicle = mid in _CD["vehicle_mids"]
    for m, v in ((_CADDE_GEO_MEMORY, geo), (_CADDE_VEHICLE_MEMORY, vehicle if has_vehicle else None)):
        if v is not None:
            m.append(v)
            del m[:-12]
    story = cadde_story(geo, people, mid, vehicle, final)
    tail = cadde_tail(follow)
    prompt = cadde_prompt(geo, people, mid, vehicle, final, follow)
    tb = {"event": event, "geo": geo, "people": people, "vehicle": vehicle, "mid": mid, "final": final,
          "follow": follow, "story": story, "suffix": tail, "prompt": prompt}
    tb["lines"] = cadde_lines(tb)
    problems = cadde_issues({**st, "cadde_yaklasma": tb}, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{CADDE_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = scene.get("combo_key", "")
    if f"#{old_tag}|" in combo:
        combo = combo.replace(f"#{old_tag}|", f"#{new_tag}|")
    name = _CD["geos"][geo]["name"]
    mid_text, final_text = cadde_mid(mid, vehicle), cadde_final(final)
    cap_info = {**(st.get("caption_info") or {}), "opening": cadde_opening(geo), "people": people,
                "beat_2": mid_text[:-1], "beat_3": final_text[:-1]}
    structure = {**st, "cadde_yaklasma": tb, "caption_info": cap_info,
                 "environment": f"Coğrafya: {geo} {name} · kamera = {CADDE_MODE_LABEL} (high balcony across the "
                                "street, eye level, normal lens, hafif takip)",
                 "story_source": f"Hikâye: kod (birebir) · {CADDE_MODE_LABEL}"}
    if st.get("axes_json"):
        structure["axes_json"] = _cadde_axes(st["axes_json"], new_tag, geo, vehicle if has_vehicle else None, people)
    plain = " ".join([cadde_opening(geo), cadde_people(people), mid_text, final_text])
    trace, axes_line = mode_display(
        scene, structure, mode=CADDE_MODE_LABEL, camera=f"hit kamerası ({cadde_camera_text(follow)}); high balcony "
        "across the street, overlooking the avenue, eye level, normal lens",
        opening=cadde_opening(geo), mid=(mid, mid_text), final=(final, final_text), plain=plain,
        vehicle=vehicle if has_vehicle else f"{vehicle} (bu ortada araç yok)",
        spot="High balcony across the street, overlooking the avenue (Yaklaşma kalıbı, hit kamerası)",
        weather="yok (stil ekinde raw natural light matching the weather)",
        axes={"coğrafya": f"{geo} {name}", "araç": vehicle if has_vehicle else "yok",
              "kişi": people, "orta": mid, "final": final, "kamera modu": "hafif takip"},
        repeat=f"coğrafya son {CADDE_GEO_BLOCK} elendi (G1 tohum) · araç son {CADDE_VEHICLE_BLOCK} · orta son "
               f"{CADDE_MID_BLOCK} · final son {CADDE_FINAL_BLOCK} (yasak çift yok)")
    # normal hattın ortam etiketi ve görünümü prompt'ta yok: gösterilmez
    trace = {**trace, "mode": "cadde_yaklasma", "cografya": geo, "count_range": [5, 6], "view": None,
             "view_source": None, "fire_env_label_short": None}
    structure["axes_line"] = axes_line
    out = {**scene, "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt,
           "combo_key": combo, "structure": structure, "trace": trace}
    if scene.get("axes_json"):
        out["axes_json"] = _cadde_axes(scene["axes_json"], new_tag, geo, vehicle if has_vehicle else None, people)
    return out


def cadde_camera_issues(text: str, geo: str | None = None) -> list[str]:
    """Kie öncesi son kontrol (15 Kas (3)): CADDE_REQUIRED ("high balcony across the street", "normal lens",
    "a parked") ve seçilen G'nin place metni var; CADDE_FORBIDDEN'dan hiçbiri yok. İhlal = gönderilmez."""
    out = []
    for need in CADDE_REQUIRED:
        if need not in text:
            out.append(f'"{need}" eksik')
    places = [g for g, v in _CD["geos"].items() if v["place"] in text]
    if not places:
        out.append("G1-G6 yer metni yok")
    elif geo is not None and places != [geo]:
        out.append(f"yer metni seçilen coğrafya değil ({geo}: {places})")
    for bad in CADDE_FORBIDDEN:
        if bad in text:
            out.append(f"bu modda olmayan ifade var: {bad}")
    return out


def cadde_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin bu kalıpla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    tb = structure["cadde_yaklasma"]
    if tb.get("geo") not in _CD["geos"]:
        return [f"coğrafya G1-G6 değil ({tb.get('geo')})"]
    if tb.get("mid") not in _CD["mids"]:
        return [f"orta O1, O2 değil ({tb.get('mid')})"]
    if tb.get("final") not in _CD["finals"]:
        return [f"final F1, F2, F3 değil ({tb.get('final')})"]
    try:
        story = cadde_story(tb["geo"], tb["people"], tb["mid"], tb["vehicle"], tb["final"])
        prompt = cadde_prompt(tb["geo"], tb["people"], tb["mid"], tb["vehicle"], tb["final"], tb["follow"])
    except es.StructureError as e:
        return [str(e)]
    out = []
    if info.get("style_suffix") != cadde_tail(tb["follow"]):
        out.append("stil eki Yaklaşma (cadde) kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye kalıpla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt kalıpla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out += cadde_camera_issues(text, tb["geo"])
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > CADDE_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {CADDE_MAX_WORDS})")
    if len(text) > CADDE_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {CADDE_MAX_CHARS})")
    return out


# ── ❄️ Donduran fırtına (15 Kas 2026, Bahadır) ─────────────────────────────────────────────────────────────────────────
# Yeni kategori, tek olay: "❄️ Fırtınanın gözü şehri dondurur". İlham: The Day After Tomorrow (şehir merkezi, fırtınanın
# gözü gökyüzünde görünür, geçtiği her şeyi anında dondurur). Karar (15 Kas, Bahadır): insanlar kaçarken donar, sokakta
# köpek de donar, kan yok; Kie reddederse öğrenmiş oluruz. YAKLASMA_CADDE ile aynı düzen (GPT yok, hikâye koddan
# birebir, zaman etiketleri var), ama normal hattın sahnesi YOK: olay yapılandırılmış havuzda değil, sahne tamamen
# burada kurulur (donma_build_scene). Diğer olaylar, kategoriler ve modlar değişmez. Kayıt O*+F* (combo + Eksenler).
# Coğrafya G1-G6 (son 3), araç son 2, orta/final son 1, kişi 5/6, yasak çift yok.
DONMA_MODE_LABEL = "❄️ Donduran fırtına"
DONMA_DOMAIN = "frozen_storm_disasters"          # Combo Key'in ilk parçası (Notion eksen sorgusu bununla)
DONMA_EVENT = "Storm's eye freezes the city"     # Notion "Olay"; normal havuzda (DOMAIN_ATTRIBUTES) yok
DONMA_CATEGORY_LABEL = "❄️ Donduran fırtına"     # Telegram kategori düğmesi
# 15 Kas (3): görünen ad değişti (sadece etiket; iç anahtar DONMA_EVENT, LRU ve Notion aynı). Eski: DONMA_PASIF.
DONMA_EVENT_LABEL = "❄️ Buz fırtınası şehri dondurur"   # Telegram olay düğmesi
DONMA_NOTION_CATEGORY = "Donduran fırtına"       # Notion: Eksenler "kategori" (metin) + Paylaşımlar "Kategori"
DONMA_MAX_WORDS = 230
DONMA_MAX_CHARS = 1400
DONMA_GEO_BLOCK = 3
DONMA_VEHICLE_BLOCK = 2
DONMA_MID_BLOCK = 1
DONMA_FINAL_BLOCK = 1
DONMA_SPOT = "high balcony across the street"
DONMA_FIRTINA = {
    "geos": {
        "G1": {"name": "ABD", "place": "a New York avenue of brownstone buildings"},
        "G2": {"name": "Fransa", "place": "a Paris boulevard of cream stone buildings"},
        "G3": {"name": "İngiltere", "place": "a London street of red-brick terraces"},
        "G4": {"name": "Almanya", "place": "a Berlin boulevard lined with linden trees"},
        # 15 Kas (2): G5 kısaldı (eski metin DONMA_PASIF G5_V1)
        "G5": {"name": "Brezilya", "place": "a Rio avenue of palm trees and pastel buildings"},
        "G6": {"name": "Hindistan", "place": "a Mumbai street of old colonial buildings"},
    },
    # 15 Kas (3): 2. sürüm (New York) çok yapay çıktı: "circular hole" bilim kurgu bir göz ve ışık sütunu çizdirdi,
    # buz dalga gibi aktı, insanlar ve köpek donmadan heykel gibi kayarak geldi. Gözden vazgeçildi: tehdit caddeden
    # gelen kar ve buz fırtınası cephesi. Metinler 1. sürüme (Londra) döndü; açılış fırtına cephesi (fıskiye yok),
    # F3 "blizzard". 2. sürüm metinleri DONMA_PASIF *_V2, 1. sürüm *_V1 (pasif). Altın kural: video asla yapay görünmez.
    "opening": "A freezing blizzard front of dense, swirling snow and ice rolls down {place} toward the camera, and "
               "everything it swallows turns white with frost in an instant, trees and parked cars freezing solid.",
    "people": {5: "Five people and a dog sprint toward the camera ahead of it.",
               6: "Six people and a dog sprint toward the camera ahead of it."},
    "vehicles": ("city bus", "taxi", "delivery van"),
    "mids": {
        "O1": "The frost catches the people and the dog mid-stride, freezing them solid into white ice statues, and a "
              "moving {vehicle} freezes white and slides sideways into a lamppost.",
        "O2": "The frost catches the people and the dog mid-stride, freezing them solid into white ice statues, and a "
              "{vehicle} freezes mid-turn and tips over onto its side.",
    },
    "finals": {
        "F1": "Right across the street, the frost climbs the building, its windows bursting white with ice, then ice "
              "races over the balcony railing in front of the camera.",
        "F2": "Right below the balcony, a tree and a row of parked cars freeze solid, the tree splitting with a crack, "
              "and white frost creeps up the railing in front of the camera.",
        "F3": "The blizzard hits the camera's building, ice racing up the facade and over the balcony railing as frost "
              "spreads across the edges of the frame.",
    },
    "vehicle_mids": ("O1", "O2"),
    "camera": "the camera stays fixed, tilting only slightly, the blizzard always in frame",
    "tail": ("Handheld footage shot by a person standing on a high balcony across the street, high vantage, normal "
             "lens; slight hand shake, the camera stays fixed, tilting only slightly, the blizzard always in frame; one "
             "continuous shot, no zoom, no cuts. Everything the frost touches freezes instantly and stays frozen white; "
             "frozen people stand still like statues, no blood, no injuries, no faces close to the camera. Raw natural "
             "light under a dark storm sky, never glossy or CGI. No readable signs or text. Everything moves in real "
             "time, never in slow motion, people run at full speed."),
}
# 15 Kas (2): değişen eski metinler (pasif, hiçbir aktif prompt'ta çıkmaz)
DONMA_PASIF = {
    "G5_V1": "a Rio de Janeiro avenue of palm trees and pastel buildings",
    "OPENING_V1": ("The storm's eye opens in the black sky above {place}, and a wall of white frost races down the "
                   "street toward the camera, freezing a fountain's spray in mid-air."),
    "PEOPLE_V1": {5: "Five people and a dog sprint toward the camera ahead of it.",
                  6: "Six people and a dog sprint toward the camera ahead of it."},
    "O1_V1": ("The frost catches the people and the dog mid-stride, freezing them solid into white ice statues, and a "
              "moving {vehicle} freezes white and slides sideways into a lamppost."),
    "O2_V1": ("The frost catches the people and the dog mid-stride, freezing them solid into white ice statues, and a "
              "{vehicle} freezes mid-turn and tips over onto its side."),
    "F2_V1": ("Right below the balcony, a tree and a row of parked cars freeze solid, the tree splitting with a crack, "
              "and white frost creeps up the railing in front of the camera."),
    "TAIL_V1": ("Handheld footage shot by a person standing on a high balcony across the street, normal lens; slight "
                "hand shake, the camera stays fixed, tilting only slightly, the storm's eye always visible in the sky; "
                "one continuous shot, no zoom, no cuts. Everything the frost touches freezes instantly and stays frozen "
                "white; frozen people stand still like statues, no blood, no injuries, no faces close to the camera. "
                "Raw natural light under a dark storm sky, never glossy or CGI. No readable signs or text. Everything "
                "moves in real time, never in slow motion, people run at full speed."),
    "TAIL_SHORTEN_V1": "No readable signs or text.",
    "WARNING_V1": "⚠️ Donma: insanlar ve köpek kanlı/yaralı değil, buz heykel gibi donmuş mu kontrol et.",
    "REQUIRED_V1": ("storm's eye", "freez", "normal lens", "no blood"),
    "FORBIDDEN_V1": ("pans to follow", "Full action", "Until the last frame", "blood-", "corpse", "dead"),
    # 15 Kas (3): 2. sürüm (New York, göz halka) metinleri, pasif; hiçbir aktif prompt'ta çıkmaz
    "OPENING_V2": ("Above {place}, the storm's eye opens, a vast circular hole in the black clouds with a calm pale sky "
                   "inside the ring, and a wall of white frost races down the street toward the camera, freezing "
                   "everything it passes."),
    "PEOPLE_V2": {5: "Five people and a dog sprint down the middle of the street ahead of it.",
                  6: "Six people and a dog sprint down the middle of the street ahead of it."},
    "O1_V2": ("The frost catches the people and the dog mid-stride, far below the camera, freezing them solid into ice "
              "statues, and a moving {vehicle} freezes white and slides sideways into a lamppost."),
    "O2_V2": ("The frost catches the people and the dog mid-stride, far below the camera, freezing them solid into ice "
              "statues, and a {vehicle} freezes mid-turn and tips over onto its side."),
    "F2_V2": ("Right below the balcony, a tree and parked cars freeze solid, the tree splitting with a crack, and frost "
              "creeps up the railing in front of the camera."),
    "F3_V2": ("The frost wall hits the camera's building, ice racing up the facade and over the balcony railing as "
              "frost spreads across the edges of the frame."),
    "CAMERA_V2": "the camera stays fixed, tilting only slightly, the storm's eye always visible in the sky",
    "TAIL_V2": ("Handheld footage shot by a person standing on a high balcony across the street, high vantage looking "
                "down over the street, normal lens; slight hand shake, the camera stays fixed, tilting only slightly, "
                "the storm's eye always visible in the sky; one continuous shot, no zoom, no cuts. No funnel, no "
                "tornado. Everything the frost touches freezes instantly and stays frozen white; frozen people stand "
                "still like statues, no blood, no injuries, no faces close to the camera. Natural light under a dark "
                "sky, never CGI. Everything moves in real time, never in slow motion, people run at full speed."),
    "EVENT_LABEL_V2": "❄️ Fırtınanın gözü şehri dondurur",
    "WARNING_V2": ("⚠️ Donma: insanlar ve köpek kanlı/yaralı değil, buz heykel gibi donmuş mu kontrol et. "
                   "Kamera yüksekte mi, gökte huni değil halka şeklinde göz mü?"),
    "REQUIRED_V2": ("storm's eye", "circular hole", "freez", "high vantage", "normal lens", "No funnel", "no blood",
                    "far below the camera"),
    "FORBIDDEN_V2": ("fountain", "pans to follow", "Full action", "Until the last frame", "blood-", "corpse", "dead"),
    "WEATHER_V2": "yok (stil ekinde natural light under a dark sky)",
    "CONFIRM_DESC_V2": ("Fırtınanın gözü şehrin üstünde açılır, beyaz don caddeden kameraya doğru gelir; kaçan insanlar "
                        "ve köpek buz heykel gibi donar (kan yok), araç donup kayar ya da devrilir; final kameranın "
                        "balkonunda."),
}
# Önceden onaylı yedek kısaltma (bir kombinasyon 230 kelimeyi aşarsa stil ekinde bu cümle kısalır). 15 Kas (2): gerekmedi.
DONMA_TAIL_SHORTEN = "Everything moves in real time, never in slow motion, people run at full speed."
DONMA_TAIL_SHORTEN_TO = "People run at full speed."
DONMA_SHORTENED = False
DONMA_CAMERA_LINE = "Kamera: hit kamerası (yüksek balkon, normal lens, sabit)"
DONMA_WARNING = ("⚠️ Gerçekçilik: insanlar ve köpek donmadan önce gerçekten koşuyor mu (kaymıyor mu), kan/yara yok mu, "
                 "kamera yüksekte mi, video yapay görünüyor mu?")
DONMA_WEATHER = "kar ve buz fırtınası cephesi (stil ekinde raw natural light under a dark storm sky)"
DONMA_CONFIRM_DESC = ("Kar ve buz fırtınası cephesi caddeden kameraya doğru gelir; dokunduğu her şey anında beyaz donar. "
                      "Kaçan insanlar ve köpek buz heykel gibi donar (kan yok), araç donup kayar ya da devrilir; final "
                      "kameranın balkonunda.")
# 15 Kas (3): Kie öncesi son kontrol (büyük/küçük harf fark etmez). Eskiler DONMA_PASIF *_V1 / *_V2.
DONMA_REQUIRED = ("blizzard", "freez", "high vantage", "normal lens", "no blood", "never glossy or CGI")
DONMA_FORBIDDEN = ("storm's eye", "circular hole", "fountain", "far below the camera", "pans to follow", "Full action",
                   "Until the last frame", "blood-", "corpse", "dead")
_DF = DONMA_FIRTINA
_DONMA_GEO_MEMORY: list[str] = []
_DONMA_VEHICLE_MEMORY: list[str] = []


def donma_is_active(event: str | None) -> bool:
    return event == DONMA_EVENT


def donma_camera_text() -> str:
    return _DF["camera"]


def donma_tail() -> str:
    tail = _DF["tail"]
    if DONMA_SHORTENED:
        tail = tail.replace(DONMA_TAIL_SHORTEN, DONMA_TAIL_SHORTEN_TO)
    return tail


def donma_opening(geo: str) -> str:
    if geo not in _DF["geos"]:
        raise es.StructureError(f"{DONMA_MODE_LABEL}: {geo} bu kategoride yok (coğrafya G1-G6)")
    return _DF["opening"].format(place=_DF["geos"][geo]["place"])


def donma_people(n: int) -> str:
    if n not in _DF["people"]:
        raise es.StructureError(f"{DONMA_MODE_LABEL}: kişi sayısı 5 ya da 6 olmalı ({n})")
    return _DF["people"][n]


def donma_mid(mid: str, vehicle: str | None) -> str:
    if mid not in _DF["mids"]:
        raise es.StructureError(f"{DONMA_MODE_LABEL}: {mid} bu kategoride yok (orta O1, O2)")
    if mid in _DF["vehicle_mids"] and vehicle not in _DF["vehicles"]:
        raise es.StructureError(f"{DONMA_MODE_LABEL}: {mid} için araç yok ({vehicle})")
    return _DF["mids"][mid].format(vehicle=vehicle or "")


def donma_final(final: str) -> str:
    if final not in _DF["finals"]:
        raise es.StructureError(f"{DONMA_MODE_LABEL}: {final} bu kategoride yok (final F1, F2, F3)")
    return _DF["finals"][final]


def donma_story(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    """Sıra: açılış + insan + orta + final (zaman etiketleriyle)."""
    a, b, c = es.SLICE_LABELS
    return (f"{a}: {donma_opening(geo)} {donma_people(people)} {b}: {donma_mid(mid, vehicle)} "
            f"{c}: {donma_final(final)}")


def donma_prompt(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    """Prompt = açılış + insan + orta + final + stil eki."""
    from core.creative_engine import join_story_and_style
    return join_story_and_style(donma_story(geo, people, mid, vehicle, final), donma_tail())


def donma_tags(history: list[str]) -> list[str]:
    """Combo Key'lerden + süreç hafızasından O*+F* çiftleri (eskiden yeniye)."""
    return [t for t in es.beat_history(DONMA_EVENT, history or []) if re.fullmatch(r"O\d+\+F\d+", t)]


def donma_choose_mid(tags: list[str], rng=None) -> str:
    return _block_pick(list(_DF["mids"]), [t.split("+")[0] for t in tags], DONMA_MID_BLOCK, rng)


def donma_choose_final(tags: list[str], rng=None) -> str:
    return _block_pick(list(_DF["finals"]), [t.split("+")[1] for t in tags], DONMA_FINAL_BLOCK, rng)


def donma_axes_history(records: list | None, key: str) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu kategorinin `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == DONMA_EVENT and axes.get("mod") == "donma_firtina"
                and axes.get(key)):
            out.append(axes[key])
    return out


def donma_choose_geo(used: list[str] | None = None, rng=None) -> str:
    seen = list(_DONMA_GEO_MEMORY if used is None else used)
    return _block_pick(list(_DF["geos"]), seen, DONMA_GEO_BLOCK, rng)


def donma_choose_vehicle(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(list(_DF["vehicles"]), list(_DONMA_VEHICLE_MEMORY if used is None else used),
                       DONMA_VEHICLE_BLOCK, rng)


def donma_lines(tb: dict) -> str:
    """✋ Onay satırları: mod, coğrafya, araç, orta, final, kişi, kamera, kelime/karakter, eksenler, tekrar önleme,
    donma uyarısı."""
    text = tb["prompt"]
    lines = [
        f"Mod: {DONMA_MODE_LABEL}",
        f"Coğrafya: {tb['geo']} {_DF['geos'][tb['geo']]['name']}",
        f"Araç: {tb['vehicle']}",
        f"Orta (4-9s): {tb['mid']} «{donma_mid(tb['mid'], tb['vehicle'])}»",
        f"Final (9-15s): {tb['final']} «{donma_final(tb['final'])}»",
        f"Kişi: {tb['people']}",
        DONMA_CAMERA_LINE,
        f"Kelime: {len(text.split())} (en fazla {DONMA_MAX_WORDS}) · karakter: {len(text)} (en fazla {DONMA_MAX_CHARS})",
    ]
    if tb.get("axes_line"):
        lines.append(tb["axes_line"])
    lines.append(DONMA_WARNING)
    return "\n".join(lines)


def donma_caption_beat(text: str) -> str:
    """Caption açıklama şablonu için beat cümlesi: ilk harf küçük, son nokta yok (normal hattın beat_text biçimi)."""
    t = text.rstrip(".")
    return t[:1].lower() + t[1:]


def donma_axes_json(tag: str, geo: str, vehicle: str, people: int, excluded: dict | None = None) -> str:
    import core.axes_history as ah
    axes = {"spot": DONMA_SPOT, "view": None, "light": None, "vehicle": vehicle, "people": people, "beats": tag,
            "mod": "donma_firtina", "kategori": DONMA_NOTION_CATEGORY, "cografya": geo, "arac": vehicle}
    return ah.axes_json(DONMA_EVENT, axes, excluded)


def donma_build_scene(domain: str | None, event: str | None, history: list[str] | None = None,
                      records: list | None = None, rng=None, history_source: str = "bellek") -> dict:
    """❄️ Donduran fırtına sahnesi: GPT yok, normal hat yok. records = Notion "Eksenler" ham kayıtları (None =
    okunamadı / yükleyici yok: süreç hafızası). Coğrafya son 3, araç son 2, orta/final son 1, kişi 5/6.
    structure["donma_firtina"] Kie öncesi son denetimin (submit_issues) kaynağıdır."""
    import random
    from core.skeleton_pipeline import SKELETON_CAMERA
    if domain not in (None, DONMA_DOMAIN) or not donma_is_active(event):
        raise es.StructureError(f"{DONMA_MODE_LABEL} kurulamadı: {domain} / {event}")
    r = rng or random
    geo_used = donma_axes_history(records, "cografya")
    vehicle_used = donma_axes_history(records, "arac")
    tags = donma_axes_history(records, "beats") if records is not None else donma_tags(history or [])
    geo = donma_choose_geo(geo_used, r)
    vehicle = donma_choose_vehicle(vehicle_used, r)
    people = r.choice((5, 6))
    mid = donma_choose_mid(tags, r)
    final = donma_choose_final(tags, r)
    tag = es.beat_tag(mid, final)
    es.remember_beats(DONMA_EVENT, tag)   # seçim anı hafızası (TEST/iptal da sayılır)
    for m, v in ((_DONMA_GEO_MEMORY, geo), (_DONMA_VEHICLE_MEMORY, vehicle)):
        m.append(v)
        del m[:-12]
    story = donma_story(geo, people, mid, vehicle, final)
    tail = donma_tail()
    prompt = donma_prompt(geo, people, mid, vehicle, final)
    name = _DF["geos"][geo]["name"]
    mid_text, final_text = donma_mid(mid, vehicle), donma_final(final)
    opening = donma_opening(geo)
    plain = " ".join([opening, donma_people(people), mid_text, final_text])
    repeat = (f"coğrafya son {DONMA_GEO_BLOCK} elendi · araç son {DONMA_VEHICLE_BLOCK} · orta son {DONMA_MID_BLOCK} · "
              f"final son {DONMA_FINAL_BLOCK} (yasak çift yok)")
    base_trace = {"pipeline": "creative", "structured": True, "domain": DONMA_DOMAIN, "event": DONMA_EVENT,
                  "ship": "None", "camera": SKELETON_CAMERA, "view": None, "view_source": None,
                  "place": _DF["geos"][geo]["place"], "count_range": [5, 6], "people_running": people,
                  "outcome": "-", "recent_count": 0}
    trace, axes_line = mode_display(
        {"trace": base_trace}, {}, mode=DONMA_MODE_LABEL,
        camera=f"hit kamerası ({donma_camera_text()}); high balcony across the street, normal lens",
        opening=opening, mid=(mid, mid_text), final=(final, final_text), plain=plain, vehicle=vehicle,
        spot="High balcony across the street (hit kamerası, yüksek balkon, normal lens, sabit)",
        weather=DONMA_WEATHER,
        axes={"coğrafya": f"{geo} {name}", "araç": vehicle, "kişi": people, "orta": mid, "final": final,
              "kamera modu": "sabit"},
        repeat=repeat)
    trace = {**trace, "mode": "donma_firtina", "cografya": geo, "axes_source": history_source}
    tb = {"event": DONMA_EVENT, "geo": geo, "people": people, "vehicle": vehicle, "mid": mid, "final": final,
          "story": story, "suffix": tail, "prompt": prompt, "axes_line": axes_line}
    tb["lines"] = donma_lines(tb)
    excluded = {"cografya": [g for g in _DF["geos"] if g in (geo_used if geo_used is not None
                                                             else _DONMA_GEO_MEMORY[:-1])[-DONMA_GEO_BLOCK:]]}
    axes_json = donma_axes_json(tag, geo, vehicle, people, excluded)
    structure = {"donma_firtina": tb, "axes_json": axes_json, "axes_line": None, "environment": None,
                 "story_source": f"Hikâye: kod (birebir) · {DONMA_MODE_LABEL}", "story_source_kind": "code",
                 "caption_info": {"opening": opening, "people": people, "kadraj": "balkon",
                                  # caption şablonları normal beat'ler gibi küçük harfle başlayan cümle bekler
                                  "beat_2": donma_caption_beat(mid_text), "beat_3": donma_caption_beat(final_text)},
                 "caption_candidates": None}
    problems = donma_issues(structure, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{DONMA_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = f"{DONMA_DOMAIN}|none|{DONMA_EVENT.lower()}|{DONMA_SPOT}##{tag}|{SKELETON_CAMERA}"
    return {"domain": DONMA_DOMAIN, "event": DONMA_EVENT, "ship": None, "spot": DONMA_SPOT, "story": story,
            "plain_story": plain, "style_suffix": tail, "prompt": prompt, "combo_key": combo, "trace": trace,
            "structure": structure, "axes_json": axes_json}


def donma_camera_issues(text: str, geo: str | None = None) -> list[str]:
    """Kie öncesi son kontrol: DONMA_REQUIRED ("blizzard", "freez", "high vantage", "normal lens", "no blood",
    "never glossy or CGI") ve seçilen G'nin place metni var; DONMA_FORBIDDEN'dan ("storm's eye", "circular hole",
    "fountain", "far below the camera" dahil) hiçbiri yok (büyük/küçük harf fark etmez). İhlal = gönderilmez. Eski
    listeler DONMA_PASIF."""
    out = []
    low = (text or "").lower()
    for need in DONMA_REQUIRED:
        if need.lower() not in low:
            out.append(f'"{need}" eksik')
    places = [g for g, v in _DF["geos"].items() if v["place"] in (text or "")]
    if not places:
        out.append("G1-G6 yer metni yok")
    elif geo is not None and places != [geo]:
        out.append(f"yer metni seçilen coğrafya değil ({geo}: {places})")
    for bad in DONMA_FORBIDDEN:
        if bad.lower() in low:
            out.append(f"bu kategoride olmayan ifade var: {bad}")
    return out


def donma_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin bu kalıpla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    tb = structure["donma_firtina"]
    if tb.get("geo") not in _DF["geos"]:
        return [f"coğrafya G1-G6 değil ({tb.get('geo')})"]
    if tb.get("mid") not in _DF["mids"]:
        return [f"orta O1, O2 değil ({tb.get('mid')})"]
    if tb.get("final") not in _DF["finals"]:
        return [f"final F1, F2, F3 değil ({tb.get('final')})"]
    try:
        story = donma_story(tb["geo"], tb["people"], tb["mid"], tb["vehicle"], tb["final"])
        prompt = donma_prompt(tb["geo"], tb["people"], tb["mid"], tb["vehicle"], tb["final"])
    except es.StructureError as e:
        return [str(e)]
    out = []
    if info.get("style_suffix") != donma_tail():
        out.append("stil eki Donduran fırtına kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye kalıpla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt kalıpla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out += donma_camera_issues(text, tb["geo"])
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > DONMA_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {DONMA_MAX_WORDS})")
    if len(text) > DONMA_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {DONMA_MAX_CHARS})")
    return out


# ── 🌀 Kasırga (15 Kas 2026 (4), Bahadır) ─────────────────────────────────────────────────────────────────────────────
# Yeni kategori, tek olay: "🌀 Kasırga kıyı kasabasını döver". Odak rüzgâr: hortum (huni) yok, dev dalga/sel dalgası
# yok. Altın kural: video asla yapay görünmez; kısa, sade, gerçek görüntülere benzer prompt. DONMA_FIRTINA ile aynı
# düzen (GPT yok, hikâye koddan birebir, zaman etiketleri var, normal hattın sahnesi YOK: olay yapılandırılmış havuzda
# değil, rastgele domain rotasyonu ve snapshot'lar değişmesin diye sahne burada kurulur: kasirga_build_scene).
# Coğrafya G1-G6 (son 3), araç son 2, orta/final son 1, kişi 4/5. Kayıt O*+F* (combo + Eksenler).
# 15 Kas (5): kategori 5 şiddet + sağanak + kaos; O3 (kökünden sökülen ağaç), yeni F2 (dükkân cephesi), kamera sabit
# (rüzgârla sarsılır, "heavy hand shake" yasak). Eski metinler KASIRGA_PASIF (_V1).
KASIRGA_MODE_LABEL = "🌀 Kasırga"
KASIRGA_DOMAIN = "hurricane_disasters"                 # Combo Key'in ilk parçası (Notion eksen sorgusu bununla)
KASIRGA_EVENT = "Hurricane winds batter a coastal town"   # Notion "Olay"; normal havuzda (DOMAIN_ATTRIBUTES) yok
KASIRGA_CATEGORY_LABEL = "🌀 Kasırga"                   # Telegram kategori düğmesi
KASIRGA_EVENT_LABEL = "🌀 Kasırga kıyı kasabasını döver"   # Telegram olay düğmesi
KASIRGA_NOTION_CATEGORY = "Kasırga"                     # Notion: Eksenler "kategori" (metin) + Paylaşımlar "Kategori"
KASIRGA_MAX_WORDS = 230
KASIRGA_MAX_CHARS = 1400
KASIRGA_GEO_BLOCK = 3
KASIRGA_VEHICLE_BLOCK = 2
KASIRGA_MID_BLOCK = 1
KASIRGA_FINAL_BLOCK = 1
KASIRGA_SPOT = "high balcony across the street"
KASIRGA = {
    "geos": {
        "G1": {"name": "ABD", "place": "a Florida beach town of low pastel houses"},
        "G2": {"name": "Filipinler", "place": "a Philippine coastal town of tin-roofed houses"},
        "G3": {"name": "Meksika", "place": "a Mexican Caribbean town of colorful concrete houses"},
        "G4": {"name": "Hindistan", "place": "an Indian coastal town of old concrete buildings"},
        "G5": {"name": "Küba", "place": "a Cuban seaside town of faded colonial houses"},
        "G6": {"name": "Japonya", "place": "a Japanese coastal town of low tiled houses"},
    },
    "opening": ("Category 5 hurricane winds and torrential sideways rain hammer a street in {place}, palm trees bent "
                "almost flat, one palm torn out by its roots and hurled across the road, branches, roof sheets and "
                "debris flying everywhere in total chaos."),   # 21 Kas (2) v2; eski OPENING_V2 pasif
    "people": {4: "Four people struggle along the sidewalk toward the camera, bent double against the wind, clinging "
                  "to railings, one knocked off his feet by a gust.",
               5: "Five people struggle along the sidewalk toward the camera, bent double against the wind, clinging "
                  "to railings, one knocked off his feet by a gust."},
    "vehicles": ("pickup truck", "SUV", "small car"),
    "mids": {
        "O1": "A violent gust flips a parked {vehicle} onto its roof and sends it skidding across the wet road.",
        "O2": "A shop awning rips loose and slams down onto a parked {vehicle}, smashing its windshield.",   # 21 Kas (3) v3; eski O2_V3 pasif
        "O3": "A big tree is ripped out by its roots and crashes across the road onto a parked {vehicle}, crushing its "
              "roof.",
    },
    "finals": {
        "F1": "Right across the street, the wind peels the whole roof off a house, metal sheets and tiles flying past "
              "the camera.",
        "F2": ("Right across the street, a wooden power pole snaps at its base and crashes down across the road, live "
               "wires whipping and sparking."),   # 21 Kas (2) v2; eski F2_V2 pasif
        "F3": "Across the street, a large blank billboard rips loose and cartwheels down the road toward the camera.",
    },
    "vehicle_mids": ("O1", "O2", "O3"),
    "camera": ("the camera stays fixed on the street and never pans, shaking in the wind, rain streaking across the "
               "lens; a balcony railing stays fixed at the bottom of the frame the whole time; no zoom, no cuts"),
    "tail": ("Handheld footage shot by a person standing on a high balcony across the street, eye level, normal lens; "
             "the camera stays fixed on the street and never pans, shaking in the wind, rain streaking across the lens; "
             "a balcony railing stays fixed at the bottom of the frame the whole time; no zoom, no cuts. No tornado "
             "funnel, no flood waves. Bystanders wear everyday clothes. Raw natural light under a dark grey sky in "
             "pouring rain, never glossy or CGI. No readable signs or text. Everything moves in real time, never in "
             "slow motion."),   # 21 Kas (3) v3; eski TAIL_V3 pasif
}
KASIRGA_CAMERA_LINE = ("Kamera: hit kamerası (yüksek balkon, normal lens, sabit, dönmez, korkuluk altta sabit, "
                       "rüzgârla sarsılır, lenste yağmur)")   # 21 Kas (3) v3; eski CAMERA_LINE_V3 pasif
KASIRGA_WARNING = ("⚠️ Gerçekçilik: gökte huni yok mu, sel dalgası yok mu, insanlar rüzgârla gerçekten boğuşuyor mu, "
                   "video yapay görünüyor mu? Sağanak yağmur, karanlık gökyüzü ve kaos var mı?")
KASIRGA_WEATHER = "kategori 5 kasırga rüzgârı ve sağanak yatay yağmur (stil ekinde dark grey sky in pouring rain)"
KASIRGA_CONFIRM_DESC = ("Kategori 5 kasırga rüzgârı ve sağanak yatay yağmur kıyı kasabasının caddesini döver: "
                        "palmiyeler yatar, dallar, çatı sacları ve enkaz her yere uçar. İnsanlar rüzgâra karşı "
                        "boğuşarak kameraya doğru ilerler, biri rüzgârla yere düşer; park halindeki araç devrilir, "
                        "üstüne tente ve sac düşer ya da kökünden sökülen ağaç üstüne çöker; final caddenin "
                        "karşısında. Huni yok, sel dalgası yok.")
# Kie öncesi son kontrol (büyük/küçük harf fark etmez). Yasak ifadeler, stil ekindeki "No tornado funnel, no flood
# waves." cümlesi metinden çıkarıldıktan sonra aranır.
KASIRGA_REQUIRED = ("Category 5", "torrential sideways rain", "normal lens", "stays fixed on the street", "pouring rain",
                    "No tornado funnel")
KASIRGA_FORBIDDEN = ("tornado", "funnel", "twister", "waterspout", "surge", "tsunami", "tidal", "flood wave",
                     "pans to follow", "Full action", "Until the last frame", "heavy hand shake")
KASIRGA_NEGATION = "No tornado funnel, no flood waves."
# 15 Kas (5): değişen eski metinler (pasif, hiçbir aktif prompt'ta çıkmaz)
KASIRGA_PASIF = {
    "G5_V1": "a Cuban seaside street of faded colonial houses",
    "OPENING_V1": ("Hurricane winds and sideways rain hammer a street in {place}, palm trees bending almost flat as "
                   "metal roof sheets tear loose and fly across the road."),
    "PEOPLE_V1": {4: "Four people struggle along the sidewalk toward the camera, bent double against the wind, "
                     "clinging to railings.",
                  5: "Five people struggle along the sidewalk toward the camera, bent double against the wind, "
                     "clinging to railings."},
    "F2_V1": ("Right below the balcony, a tall palm tree snaps in half and crashes onto the parked cars, debris "
              "slamming into the balcony railing."),
    "VEHICLE_MIDS_V1": ("O1", "O2"),
    "CAMERA_V1": "heavy hand shake from the wind, rain streaking across the lens; no zoom, no cuts",
    "TAIL_V1": ("Handheld footage shot by a person standing on a high balcony across the street, eye level, normal "
                "lens; heavy hand shake from the wind, rain streaking across the lens; no zoom, no cuts. No tornado "
                "funnel, no flood waves. Bystanders wear everyday clothes. Raw natural light under a dark storm sky, "
                "never glossy or CGI. No readable signs or text. Everything moves in real time, never in slow motion."),
    "CAMERA_LINE_V1": "Kamera: hit kamerası (yüksek balkon, normal lens, rüzgârla sarsılan el, lenste yağmur)",
    "WARNING_V1": ("⚠️ Gerçekçilik: gökte huni yok mu, sel dalgası yok mu, insanlar rüzgârla gerçekten boğuşuyor mu, "
                   "video yapay görünüyor mu?"),
    "WEATHER_V1": "kasırga rüzgârı ve yatay yağmur (stil ekinde raw natural light under a dark storm sky)",
    "CONFIRM_DESC_V1": ("Kasırga rüzgârı ve yatay yağmur kıyı kasabasının caddesini döver: palmiyeler yatar, çatı "
                        "sacları uçar. İnsanlar rüzgâra karşı boğuşarak kameraya doğru ilerler; park halindeki araç "
                        "devrilir ya da üstüne tente ve sac düşer; final caddenin karşısında ya da balkonun altında. "
                        "Huni yok, sel dalgası yok."),
    "REQUIRED_V1": ("Hurricane", "sideways rain", "normal lens", "No tornado funnel"),
    "SPOT_DISPLAY_V1": "High balcony across the street (hit kamerası, yüksek balkon, normal lens, rüzgârla sarsılan el)",
    "CAMERA_MODE_V1": "elde, rüzgârla sarsılan",
    # 21 Kas (2), kasırga v2: açılışa kökünden sökülen palmiye, F2 dükkân cephesi yerine elektrik direği
    "OPENING_V2": ("Category 5 hurricane winds and torrential sideways rain hammer a street in {place}, palm trees "
                   "bent almost flat, branches, roof sheets and debris flying everywhere in total chaos."),
    "F2_V2": ("Right across the street, the wind rips the entire front wall off a shop, glass and debris blasting past "
              "the camera."),
    # 21 Kas (3), kasırga v3: stil ekine "never pans" + sabit korkuluk, O2'den metal sac çıktı (yalnız tente)
    "TAIL_V3": ("Handheld footage shot by a person standing on a high balcony across the street, eye level, normal "
                "lens; the camera stays fixed on the street, shaking in the wind, rain streaking across the lens; no "
                "zoom, no cuts. No tornado funnel, no flood waves. Bystanders wear everyday clothes. Raw natural light "
                "under a dark grey sky in pouring rain, never glossy or CGI. No readable signs or text. Everything "
                "moves in real time, never in slow motion."),
    "CAMERA_V3": ("the camera stays fixed on the street, shaking in the wind, rain streaking across the lens; no zoom, "
                  "no cuts"),
    "CAMERA_LINE_V3": "Kamera: hit kamerası (yüksek balkon, normal lens, sabit, rüzgârla sarsılır, lenste yağmur)",
    "O2_V3": ("A shop awning and a sheet of metal roofing rip loose and slam down onto a parked {vehicle}, smashing its "
              "windows."),
    "VERSION_LINE_V3": "Sürüm: kasırga v2 (palmiye kökünden, F2 direk)",
}
KASIRGA_VERSION_LINE = "Sürüm: kasırga v3 (sabit korkuluk, O2 tente)"   # 21 Kas (3): ✋ Onay + bot onay metni
# 21 Kas: Telegram coğrafya menüsü düğmeleri (okunur ad). Havuz metinleri değişmez; Onay satırı geos[..]["name"].
KASIRGA_GEO_BUTTONS = {"G1": "🇺🇸 ABD Florida", "G2": "🇵🇭 Filipinler", "G3": "🌴 Meksika Karayipleri",
                       "G4": "🇮🇳 Hindistan", "G5": "🇨🇺 Küba", "G6": "🇯🇵 Japonya"}
_KS = KASIRGA
_KASIRGA_GEO_MEMORY: list[str] = []
_KASIRGA_VEHICLE_MEMORY: list[str] = []


def kasirga_is_active(event: str | None) -> bool:
    return event == KASIRGA_EVENT


def kasirga_camera_text() -> str:
    return _KS["camera"]


def kasirga_tail() -> str:
    return _KS["tail"]


def kasirga_opening(geo: str) -> str:
    if geo not in _KS["geos"]:
        raise es.StructureError(f"{KASIRGA_MODE_LABEL}: {geo} bu kategoride yok (coğrafya G1-G6)")
    return _KS["opening"].format(place=_KS["geos"][geo]["place"])


def kasirga_people(n: int) -> str:
    if n not in _KS["people"]:
        raise es.StructureError(f"{KASIRGA_MODE_LABEL}: kişi sayısı 4 ya da 5 olmalı ({n})")
    return _KS["people"][n]


def kasirga_mid(mid: str, vehicle: str | None) -> str:
    if mid not in _KS["mids"]:
        raise es.StructureError(f"{KASIRGA_MODE_LABEL}: {mid} bu kategoride yok (orta O1-O3)")
    if mid in _KS["vehicle_mids"] and vehicle not in _KS["vehicles"]:
        raise es.StructureError(f"{KASIRGA_MODE_LABEL}: {mid} için araç yok ({vehicle})")
    return _KS["mids"][mid].format(vehicle=vehicle or "")


def kasirga_final(final: str) -> str:
    if final not in _KS["finals"]:
        raise es.StructureError(f"{KASIRGA_MODE_LABEL}: {final} bu kategoride yok (final F1, F2, F3)")
    return _KS["finals"][final]


def kasirga_story(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    """Sıra: açılış + insan + orta + final (zaman etiketleriyle)."""
    a, b, c = es.SLICE_LABELS
    return (f"{a}: {kasirga_opening(geo)} {kasirga_people(people)} {b}: {kasirga_mid(mid, vehicle)} "
            f"{c}: {kasirga_final(final)}")


def kasirga_prompt(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    """Prompt = açılış + insan + orta + final + stil eki."""
    from core.creative_engine import join_story_and_style
    return join_story_and_style(kasirga_story(geo, people, mid, vehicle, final), kasirga_tail())


def kasirga_tags(history: list[str]) -> list[str]:
    """Combo Key'lerden + süreç hafızasından O*+F* çiftleri (eskiden yeniye)."""
    return [t for t in es.beat_history(KASIRGA_EVENT, history or []) if re.fullmatch(r"O\d+\+F\d+", t)]


def kasirga_choose_mid(tags: list[str], rng=None) -> str:
    return _block_pick(list(_KS["mids"]), [t.split("+")[0] for t in tags], KASIRGA_MID_BLOCK, rng)


def kasirga_choose_final(tags: list[str], rng=None) -> str:
    return _block_pick(list(_KS["finals"]), [t.split("+")[1] for t in tags], KASIRGA_FINAL_BLOCK, rng)


def kasirga_axes_history(records: list | None, key: str) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu kategorinin `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == KASIRGA_EVENT and axes.get("mod") == "kasirga"
                and axes.get(key)):
            out.append(axes[key])
    return out


def kasirga_choose_geo(used: list[str] | None = None, rng=None) -> str:
    seen = list(_KASIRGA_GEO_MEMORY if used is None else used)
    return _block_pick(list(_KS["geos"]), seen, KASIRGA_GEO_BLOCK, rng)


def kasirga_choose_vehicle(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(list(_KS["vehicles"]), list(_KASIRGA_VEHICLE_MEMORY if used is None else used),
                       KASIRGA_VEHICLE_BLOCK, rng)


def kasirga_lines(tb: dict) -> str:
    """✋ Onay satırları: mod, coğrafya, araç, orta, final, kişi, kamera, kelime/karakter, eksenler, tekrar önleme,
    gerçekçilik uyarısı."""
    text = tb["prompt"]
    lines = [
        f"Mod: {KASIRGA_MODE_LABEL}",
        KASIRGA_VERSION_LINE,
        f"Coğrafya: {tb['geo']} {_KS['geos'][tb['geo']]['name']} "
        f"({'menü' if tb.get('geo_source') == 'menu' else 'rastgele'})",
        f"Araç: {tb['vehicle']}",
        f"Orta (4-9s): {tb['mid']} «{kasirga_mid(tb['mid'], tb['vehicle'])}»",
        f"Final (9-15s): {tb['final']} «{kasirga_final(tb['final'])}»",
        f"Kişi: {tb['people']}",
        KASIRGA_CAMERA_LINE,
        f"Kelime: {len(text.split())} (en fazla {KASIRGA_MAX_WORDS}) · karakter: {len(text)} "
        f"(en fazla {KASIRGA_MAX_CHARS})",
    ]
    if tb.get("axes_line"):
        lines.append(tb["axes_line"])
    lines.append(KASIRGA_WARNING)
    return "\n".join(lines)


def kasirga_axes_json(tag: str, geo: str, vehicle: str, people: int, excluded: dict | None = None,
                      geo_menu: bool = False) -> str:
    import core.axes_history as ah
    axes = {"spot": KASIRGA_SPOT, "view": None, "light": None, "vehicle": vehicle, "people": people, "beats": tag,
            "mod": "kasirga", "kategori": KASIRGA_NOTION_CATEGORY, "cografya": geo, "arac": vehicle}
    if geo_menu:   # 21 Kas: coğrafya Telegram menüsünden (🎲 Rastgele yolunda anahtar yok: kayıt eskisiyle aynı)
        axes["cografya_secim"] = "menu"
    return ah.axes_json(KASIRGA_EVENT, axes, excluded)


def kasirga_build_scene(domain: str | None, event: str | None, history: list[str] | None = None,
                        records: list | None = None, rng=None, history_source: str = "bellek",
                        geo: str | None = None) -> dict:
    """🌀 Kasırga sahnesi: GPT yok, normal hat yok. records = Notion "Eksenler" ham kayıtları (None = okunamadı /
    yükleyici yok: süreç hafızası). Coğrafya son 3, araç son 2, orta/final son 1, kişi 4/5. structure["kasirga"] Kie
    öncesi son denetimin (submit_issues) kaynağıdır.
    geo: 21 Kas, Telegram coğrafya menüsünden seçilen G (o üretim için sabit, LRU seçimi atlanır; diğer eksenler
    LRU). None = 🎲 Rastgele (bugünkü seçim, birebir)."""
    import random
    from core.skeleton_pipeline import SKELETON_CAMERA
    if domain not in (None, KASIRGA_DOMAIN) or not kasirga_is_active(event):
        raise es.StructureError(f"{KASIRGA_MODE_LABEL} kurulamadı: {domain} / {event}")
    if geo is not None and geo not in _KS["geos"]:
        raise es.StructureError(f"{KASIRGA_MODE_LABEL}: {geo} bu kategoride yok (coğrafya G1-G6)")
    geo_menu = geo is not None
    r = rng or random
    geo_used = kasirga_axes_history(records, "cografya")
    vehicle_used = kasirga_axes_history(records, "arac")
    tags = kasirga_axes_history(records, "beats") if records is not None else kasirga_tags(history or [])
    if not geo_menu:
        geo = kasirga_choose_geo(geo_used, r)
    vehicle = kasirga_choose_vehicle(vehicle_used, r)
    people = r.choice((4, 5))
    mid = kasirga_choose_mid(tags, r)
    final = kasirga_choose_final(tags, r)
    tag = es.beat_tag(mid, final)
    es.remember_beats(KASIRGA_EVENT, tag)   # seçim anı hafızası (TEST/iptal da sayılır)
    for m, v in ((_KASIRGA_GEO_MEMORY, geo), (_KASIRGA_VEHICLE_MEMORY, vehicle)):
        m.append(v)
        del m[:-12]
    story = kasirga_story(geo, people, mid, vehicle, final)
    tail = kasirga_tail()
    prompt = kasirga_prompt(geo, people, mid, vehicle, final)
    name = _KS["geos"][geo]["name"]
    mid_text, final_text = kasirga_mid(mid, vehicle), kasirga_final(final)
    opening = kasirga_opening(geo)
    plain = " ".join([opening, kasirga_people(people), mid_text, final_text])
    repeat = (f"coğrafya son {KASIRGA_GEO_BLOCK} elendi · araç son {KASIRGA_VEHICLE_BLOCK} · orta son "
              f"{KASIRGA_MID_BLOCK} · final son {KASIRGA_FINAL_BLOCK} (yasak çift yok)")
    if geo_menu:
        repeat = repeat.replace(f"coğrafya son {KASIRGA_GEO_BLOCK} elendi", f"coğrafya menüden ({geo})")
    base_trace = {"pipeline": "creative", "structured": True, "domain": KASIRGA_DOMAIN, "event": KASIRGA_EVENT,
                  "ship": "None", "camera": SKELETON_CAMERA, "view": None, "view_source": None,
                  "place": _KS["geos"][geo]["place"], "count_range": [4, 5], "people_running": people,
                  "outcome": "-", "recent_count": 0}
    trace, axes_line = mode_display(
        {"trace": base_trace}, {}, mode=KASIRGA_MODE_LABEL,
        camera=f"hit kamerası ({kasirga_camera_text()}); high balcony across the street, eye level, normal lens",
        opening=opening, mid=(mid, mid_text), final=(final, final_text), plain=plain, vehicle=vehicle,
        spot="High balcony across the street (hit kamerası, yüksek balkon, normal lens, sabit, rüzgârla sarsılır)",
        weather=KASIRGA_WEATHER,
        axes={"coğrafya": f"{geo} {name}", "araç": vehicle, "kişi": people, "orta": mid, "final": final,
              "kamera modu": "elde, sabit, rüzgârla sarsılır"},
        repeat=repeat)
    trace = {**trace, "mode": "kasirga", "cografya": geo, "axes_source": history_source,
             **({"cografya_secim": "menu"} if geo_menu else {})}
    tb = {"event": KASIRGA_EVENT, "geo": geo, "people": people, "vehicle": vehicle, "mid": mid, "final": final,
          "story": story, "suffix": tail, "prompt": prompt, "axes_line": axes_line,
          "geo_source": "menu" if geo_menu else "rastgele"}
    tb["lines"] = kasirga_lines(tb)
    excluded = {"cografya": [] if geo_menu else
                [g for g in _KS["geos"] if g in (geo_used if geo_used is not None
                                                 else _KASIRGA_GEO_MEMORY[:-1])[-KASIRGA_GEO_BLOCK:]]}
    axes_json = kasirga_axes_json(tag, geo, vehicle, people, excluded, geo_menu)
    structure = {"kasirga": tb, "axes_json": axes_json, "axes_line": None, "environment": None,
                 "story_source": f"Hikâye: kod (birebir) · {KASIRGA_MODE_LABEL}", "story_source_kind": "code",
                 "caption_info": {"opening": opening, "people": people, "kadraj": "balkon",
                                  # caption şablonları normal beat'ler gibi küçük harfle başlayan cümle bekler
                                  "beat_2": donma_caption_beat(mid_text), "beat_3": donma_caption_beat(final_text)},
                 "caption_candidates": None}
    problems = kasirga_issues(structure, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{KASIRGA_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = f"{KASIRGA_DOMAIN}|none|{KASIRGA_EVENT.lower()}|{KASIRGA_SPOT}##{tag}|{SKELETON_CAMERA}"
    return {"domain": KASIRGA_DOMAIN, "event": KASIRGA_EVENT, "ship": None, "spot": KASIRGA_SPOT, "story": story,
            "plain_story": plain, "style_suffix": tail, "prompt": prompt, "combo_key": combo, "trace": trace,
            "structure": structure, "axes_json": axes_json}


def kasirga_camera_issues(text: str, geo: str | None = None) -> list[str]:
    """Kie öncesi son kontrol: KASIRGA_REQUIRED ("Category 5", "torrential sideways rain", "normal lens", "stays fixed
    on the street", "pouring rain", "No tornado funnel") ve seçilen G'nin place metni var; stil ekindeki "No tornado
    funnel, no flood waves." cümlesi çıkarıldıktan sonra KASIRGA_FORBIDDEN'dan (tornado, funnel, twister, waterspout,
    surge, tsunami, tidal, flood wave, pans to follow, Full action, Until the last frame, heavy hand shake) hiçbiri yok
    (büyük/küçük harf fark etmez). İhlal = gönderilmez."""
    out = []
    text = text or ""
    low = text.lower()
    for need in KASIRGA_REQUIRED:
        if need.lower() not in low:
            out.append(f'"{need}" eksik')
    places = [g for g, v in _KS["geos"].items() if v["place"] in text]
    if not places:
        out.append("G1-G6 yer metni yok")
    elif geo is not None and places != [geo]:
        out.append(f"yer metni seçilen coğrafya değil ({geo}: {places})")
    rest = text.replace(KASIRGA_NEGATION, " ").lower()
    for bad in KASIRGA_FORBIDDEN:
        if bad.lower() in rest:
            out.append(f"bu kategoride olmayan ifade var: {bad}")
    return out


def kasirga_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin bu kalıpla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    tb = structure["kasirga"]
    if tb.get("geo") not in _KS["geos"]:
        return [f"coğrafya G1-G6 değil ({tb.get('geo')})"]
    if tb.get("mid") not in _KS["mids"]:
        return [f"orta O1-O3 değil ({tb.get('mid')})"]
    if tb.get("final") not in _KS["finals"]:
        return [f"final F1, F2, F3 değil ({tb.get('final')})"]
    try:
        story = kasirga_story(tb["geo"], tb["people"], tb["mid"], tb["vehicle"], tb["final"])
        prompt = kasirga_prompt(tb["geo"], tb["people"], tb["mid"], tb["vehicle"], tb["final"])
    except es.StructureError as e:
        return [str(e)]
    out = []
    if info.get("style_suffix") != kasirga_tail():
        out.append("stil eki Kasırga kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye kalıpla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt kalıpla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out += kasirga_camera_issues(text, tb["geo"])
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > KASIRGA_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {KASIRGA_MAX_WORDS})")
    if len(text) > KASIRGA_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {KASIRGA_MAX_CHARS})")
    return out


# ── ⭐ Hit kopyası (ateş hortumu) (16 Kas 2026, Bahadır) ─────────────────────────────────────────────────────────────
# Sebep: ateş hortumu Yaklaşma modundan çıkan video (Portekiz, 16 Kas paylaşımı) zayıf kaldı, hortum uzaktan başladığı
# için ilk saniyeler boştu. En iyi ateş hortumu (6 Kas paylaşımı, 5 Kas 00:13 üretimi, "Filmed as the truck is swept
# away", T4+U11, forest_edge, çatı terası; HIT_PROMPTS[FIRE_TORNADO]) tamamen farklıydı: hortum ilk saniyeden
# kadrajın yarısını dolduran bir dev. Karar: "Hit kopyası" yöntemi. Hit'in Kie prompt'u kelimesi kelimesine kullanılır,
# sadece coğrafya ({place}) ve araç ({vehicle}) değişir. GPT çağrılmaz. Yaklaşma modu pasif (menüde yok, kodu duruyor).
# Gelecekteki hit kopyaları Notion üretim veritabanının "Prompt" alanından alınır.
# KASIRGA / DONMA_FIRTINA ile aynı kod-hikâye yolu: normal hattın sahnesi kurulmaz (hit_kopya_build_scene). Olay
# normal havuzdaki ateş hortumu (FIRE_TORNADO); kayıt combo "##HK:G*" (olay çifti değil: normal hattın T*/U* LRU'su
# etkilenmez) + Eksenler mod=hit_kopya_ates, cografya, arac.
HIT_KOPYA_MODE_LABEL = "⭐ Hit kopyası (ateş hortumu)"
HIT_KOPYA_BUTTON = "⭐ Hit kopyası"                 # Telegram: ateş hortumu onay ekranı, ⭐ Hit kalıbı'nın yanında
HIT_KOPYA_EVENTS = (FIRE_TORNADO,)
HIT_KOPYA_DOMAIN = "fire_disasters"
HIT_KOPYA_MOD = "hit_kopya_ates"                    # config bayrağı, structure anahtarı, Notion axes.mod
HIT_KOPYA_SOURCE = "Kaynak: 5 Kas 00:13 üretimi (6 Kas paylaşımı), birebir"
HIT_KOPYA_MAX_WORDS = 230
HIT_KOPYA_MAX_CHARS = 1400
HIT_KOPYA_GEO_BLOCK = 3
HIT_KOPYA_GEO_SEED = ("G3",)     # 16 Kas Portekiz paylaşımıyla benzemesin: geçmişin en başına G3 "kullanıldı" işlenir
HIT_KOPYA_VEHICLE_BLOCK = 2
HIT_KOPYA_SPOT = "rooftop terrace above a wooded residential area"
HIT_KOPYA_ATES = {
    "geos": {
        "G1": {"name": "Kanada", "place": "a Canadian lakeside town"},
        "G2": {"name": "Avustralya", "place": "an Australian bush town"},
        "G3": {"name": "Portekiz", "place": "a Portuguese hillside village"},
        "G4": {"name": "ABD", "place": "a Californian suburb"},
        "G5": {"name": "Yunanistan", "place": "a Greek coastal town"},
        "G6": {"name": "Şili", "place": "a Chilean hillside town"},
    },
    "vehicles": ("pickup truck", "SUV", "delivery van"),
    # Kelimesi kelimesine hit prompt'u (HIT_PROMPTS[FIRE_TORNADO]); sadece "of {place}" eklendi, "pickup truck" →
    # {vehicle}. 17 Kas: ilk iki üretimde (Yunanistan, Kanada) hortum neredeyse yerinde durdu; SADECE hareket
    # düzeltildi: açılışa "racing fast across the neighborhood," + stil ekine "The fire tornado keeps moving fast the
    # whole time, never standing still." (eski şablon HIT_KOPYA_PASIF["HIT_KOPYA_ATES_V1"], pasif)
    "template": (
        "0-4s: A colossal spinning fire tornado, a twisting funnel several times taller than the houses and trees, "
        "tears out of a burning forest into a residential area of {place}, racing fast across the neighborhood, its "
        "wide base engulfing the houses. Two "
        "people run away in the street below. 4-9s: The {vehicle} is shoved sideways as the huge base of the fire "
        "tornado sweeps past right behind it. 9-15s: A wooden garage beside a house across the street bursts apart, "
        "burning boards spiraling up. Handheld footage filmed on a rooftop terrace above a wooded residential area, "
        "high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; "
        "slight hand shake, the camera stays fixed, an empty foreground; one continuous shot, no zoom, no cuts, no "
        "person or face close to the camera. Civilians in everyday clothes, no hazmat suits, never CGI. A rotating "
        "funnel of flame with orbiting debris, never a straight plume or explosion. The fire tornado keeps moving "
        "fast the whole time, never standing still. Everything moves in real time, "
        "never in slow motion, people run at full speed. No readable signs, text or flags."),
    "tail_start": "Handheld footage filmed on a rooftop terrace",
}
# 17 Kas: pasif kayıt (kullanılmaz, silinmez). 16 Kas bbc301b şablonu, hareket eklemeleri öncesi.
HIT_KOPYA_ATES_V1 = {
    "template": (
        "0-4s: A colossal spinning fire tornado, a twisting funnel several times taller than the houses and trees, "
        "tears out of a burning forest into a residential area of {place}, its wide base engulfing the houses. Two "
        "people run away in the street below. 4-9s: The {vehicle} is shoved sideways as the huge base of the fire "
        "tornado sweeps past right behind it. 9-15s: A wooden garage beside a house across the street bursts apart, "
        "burning boards spiraling up. Handheld footage filmed on a rooftop terrace above a wooded residential area, "
        "high vantage, the tornado filling half the frame, top never cut off, two or three people fleeing below; "
        "slight hand shake, the camera stays fixed, an empty foreground; one continuous shot, no zoom, no cuts, no "
        "person or face close to the camera. Civilians in everyday clothes, no hazmat suits, never CGI. A rotating "
        "funnel of flame with orbiting debris, never a straight plume or explosion. Everything moves in real time, "
        "never in slow motion, people run at full speed. No readable signs, text or flags."),
    "tail_start": "Handheld footage filmed on a rooftop terrace",
}
HIT_KOPYA_PASIF = {"HIT_KOPYA_ATES_V1": HIT_KOPYA_ATES_V1}
# 17 Kas: "racing fast across the neighborhood" + "never standing still" eklendi (hareket)
HIT_KOPYA_REQUIRED = ("several times taller than the houses", "the tornado filling half the frame", "rooftop terrace",
                      "never CGI", "racing fast across the neighborhood", "never standing still")
HIT_KOPYA_FORBIDDEN = ("pans to follow", "Full action", "Until the last frame", "approaches from", "in the distance")
HIT_KOPYA_WARNING = ("⚠️ Hit karşılaştırması: hortum ilk saniyeden kadrajın yarısını dolduruyor mu, video 6 Kas "
                     "hit'iyle boy ölçüşür mü?")
HIT_KOPYA_CONFIRM_DESC = ("5 Kas 00:13 üretiminin (6 Kas paylaşımı) Kie prompt'u kelimesi kelimesine; sadece coğrafya "
                          "(G1-G6) ve araç değişir. Dev ateş hortumu ilk saniyeden kadrajın yarısını doldurur, ormandan "
                          "yerleşime çıkar, araç yana savrulur, karşıdaki ahşap garaj parçalanır. Çatı terası, sabit "
                          "kamera. Coğrafya, araç, kelime sayısı ✋ Onay mesajında. Hikâye için GPT çağrılmaz.")
_HKA = HIT_KOPYA_ATES
_HIT_KOPYA_GEO_MEMORY: list[str] = []
_HIT_KOPYA_VEHICLE_MEMORY: list[str] = []


def hit_kopya_is_active(event: str | None) -> bool:
    return event in HIT_KOPYA_EVENTS


def _hit_kopya_split() -> tuple[str, str]:
    t = _HKA["template"]
    i = t.index(" " + _HKA["tail_start"])
    return t[:i], t[i + 1:]


def hit_kopya_tail() -> str:
    return _hit_kopya_split()[1]


def _hit_kopya_check(geo: str, vehicle: str) -> None:
    if geo not in _HKA["geos"]:
        raise es.StructureError(f"{HIT_KOPYA_MODE_LABEL}: {geo} bu modda yok (coğrafya G1-G6)")
    if vehicle not in _HKA["vehicles"]:
        raise es.StructureError(f"{HIT_KOPYA_MODE_LABEL}: araç bu modda yok ({vehicle})")


def hit_kopya_story(geo: str, vehicle: str) -> str:
    """Zaman etiketli hikâye (hit prompt'unun stil ekinden önceki kısmı), sadece {place} ve {vehicle} dolar."""
    _hit_kopya_check(geo, vehicle)
    return _hit_kopya_split()[0].format(place=_HKA["geos"][geo]["place"], vehicle=vehicle)


def hit_kopya_prompt(geo: str, vehicle: str) -> str:
    """Prompt = şablon (kelimesi kelimesine), sadece {place} ve {vehicle} dolar. join_story_and_style ile aynı metin."""
    from core.creative_engine import join_story_and_style
    return join_story_and_style(hit_kopya_story(geo, vehicle), hit_kopya_tail())


def hit_kopya_axes_history(records: list | None, key: str) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") in HIT_KOPYA_EVENTS and axes.get("mod") == HIT_KOPYA_MOD
                and axes.get(key)):
            out.append(axes[key])
    return out


def hit_kopya_choose_geo(used: list[str] | None = None, rng=None) -> str:
    """Son 3 coğrafya elenir; geçmişin en başında G3 tohumu (16 Kas Portekiz paylaşımı)."""
    seen = list(HIT_KOPYA_GEO_SEED) + list(_HIT_KOPYA_GEO_MEMORY if used is None else used)
    return _block_pick(list(_HKA["geos"]), seen, HIT_KOPYA_GEO_BLOCK, rng)


def hit_kopya_choose_vehicle(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(list(_HKA["vehicles"]), list(_HIT_KOPYA_VEHICLE_MEMORY if used is None else used),
                       HIT_KOPYA_VEHICLE_BLOCK, rng)


def hit_kopya_lines(tb: dict) -> str:
    """✋ Onay satırları: mod, coğrafya, araç, kaynak, kelime/karakter, eksenler + tekrar önleme, hit karşılaştırması."""
    text = tb["prompt"]
    g = _HKA["geos"][tb["geo"]]
    lines = [
        f"Mod: {HIT_KOPYA_MODE_LABEL}",
        f"Coğrafya: {tb['geo']} {g['name']} «{g['place']}»",
        f"Araç: {tb['vehicle']}",
        HIT_KOPYA_SOURCE,
        f"Kelime: {len(text.split())} (en fazla {HIT_KOPYA_MAX_WORDS}) · karakter: {len(text)} "
        f"(en fazla {HIT_KOPYA_MAX_CHARS})",
    ]
    if tb.get("axes_line"):
        lines.append(tb["axes_line"])
    lines.append(HIT_KOPYA_WARNING)
    return "\n".join(lines)


def hit_kopya_axes_json(geo: str, vehicle: str, excluded: dict | None = None) -> str:
    import core.axes_history as ah
    axes = {"spot": HIT_KOPYA_SPOT, "view": None, "light": None, "vehicle": vehicle, "people": 2,
            "beats": f"HK:{geo}", "mod": HIT_KOPYA_MOD, "cografya": geo, "arac": vehicle}
    return ah.axes_json(FIRE_TORNADO, axes, excluded)


def hit_kopya_build_scene(domain: str | None, event: str | None, history: list[str] | None = None,
                          records: list | None = None, rng=None, history_source: str = "bellek") -> dict:
    """⭐ Hit kopyası (ateş hortumu) sahnesi: GPT yok, normal hat yok. records = Notion "Eksenler" ham kayıtları (None =
    okunamadı / yükleyici yok: süreç hafızası). Coğrafya son 3 (G3 tohum), araç son 2. structure["hit_kopya_ates"] Kie
    öncesi son denetimin (submit_issues) kaynağıdır."""
    import random
    from core.skeleton_pipeline import SKELETON_CAMERA
    if domain not in (None, HIT_KOPYA_DOMAIN) or not hit_kopya_is_active(event):
        raise es.StructureError(f"{HIT_KOPYA_MODE_LABEL} kurulamadı: {domain} / {event}")
    r = rng or random
    geo_used = hit_kopya_axes_history(records, "cografya")
    vehicle_used = hit_kopya_axes_history(records, "arac")
    geo = hit_kopya_choose_geo(geo_used, r)
    vehicle = hit_kopya_choose_vehicle(vehicle_used, r)
    for m, v in ((_HIT_KOPYA_GEO_MEMORY, geo), (_HIT_KOPYA_VEHICLE_MEMORY, vehicle)):
        m.append(v)
        del m[:-12]
    story = hit_kopya_story(geo, vehicle)
    tail = hit_kopya_tail()
    prompt = hit_kopya_prompt(geo, vehicle)
    g = _HKA["geos"][geo]
    a, b, c = es.SLICE_LABELS
    opening = story.split(f"{b}: ")[0][len(f"{a}: "):].strip()
    mid_text = story.split(f"{b}: ")[1].split(f" {c}: ")[0]
    final_text = story.split(f"{c}: ")[1]
    plain = " ".join([opening, mid_text, final_text])
    seen_geo = list(HIT_KOPYA_GEO_SEED) + list(geo_used if geo_used is not None else _HIT_KOPYA_GEO_MEMORY[:-1])
    seen_veh = list(vehicle_used if vehicle_used is not None else _HIT_KOPYA_VEHICLE_MEMORY[:-1])
    repeat = (f"coğrafya son {HIT_KOPYA_GEO_BLOCK} elendi (G3 tohum) · araç son {HIT_KOPYA_VEHICLE_BLOCK} · olaylar "
              "sabit (hit'in kendisi)")
    base_trace = {"pipeline": "creative", "structured": True, "domain": HIT_KOPYA_DOMAIN, "event": FIRE_TORNADO,
                  "ship": "None", "camera": SKELETON_CAMERA, "view": None, "view_source": None,
                  "place": g["place"], "count_range": [2, 3], "people_running": 2, "outcome": "-",
                  "recent_count": 0}
    trace, axes_line = mode_display(
        {"trace": base_trace}, {}, mode=HIT_KOPYA_MODE_LABEL,
        camera="hit kamerası (the camera stays fixed); rooftop terrace above a wooded residential area, high vantage",
        opening=opening, mid=("T4", mid_text), final=("U11", final_text), plain=plain, vehicle=vehicle,
        spot="Rooftop terrace above a wooded residential area (hit kopyası, birebir)",
        axes={"coğrafya": f"{geo} {g['name']}", "araç": vehicle, "olaylar": "T4+U11 (hit, sabit)",
              "kamera modu": "elde, sabit (hit)"},
        repeat=repeat)
    trace = {**trace, "mode": HIT_KOPYA_MOD, "cografya": geo, "axes_source": history_source}
    tb = {"event": FIRE_TORNADO, "geo": geo, "vehicle": vehicle, "story": story, "suffix": tail, "prompt": prompt,
          "axes_line": axes_line}
    tb["lines"] = hit_kopya_lines(tb)
    excluded = {"cografya": [x for x in _HKA["geos"] if x in seen_geo[-HIT_KOPYA_GEO_BLOCK:]],
                "arac": [x for x in _HKA["vehicles"] if x in seen_veh[-HIT_KOPYA_VEHICLE_BLOCK:]]}
    axes_json = hit_kopya_axes_json(geo, vehicle, excluded)
    structure = {HIT_KOPYA_MOD: tb, "axes_json": axes_json, "axes_line": None, "environment": None,
                 "story_source": f"Hikâye: kod (birebir) · {HIT_KOPYA_MODE_LABEL}", "story_source_kind": "code",
                 "caption_info": {"opening": opening, "people": 2, "kadraj": "çatı",
                                  "beat_2": donma_caption_beat(mid_text), "beat_3": donma_caption_beat(final_text)},
                 "caption_candidates": None}
    problems = hit_kopya_issues(structure, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{HIT_KOPYA_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = f"{HIT_KOPYA_DOMAIN}|none|{FIRE_TORNADO.lower()}|{HIT_KOPYA_SPOT}##HK:{geo}|{SKELETON_CAMERA}"
    return {"domain": HIT_KOPYA_DOMAIN, "event": FIRE_TORNADO, "ship": None, "spot": HIT_KOPYA_SPOT, "story": story,
            "plain_story": plain, "style_suffix": tail, "prompt": prompt, "combo_key": combo, "trace": trace,
            "structure": structure, "axes_json": axes_json}


def hit_kopya_camera_issues(text: str, geo: str | None = None) -> list[str]:
    """Kie öncesi son kontrol: HIT_KOPYA_REQUIRED ("several times taller than the houses", "the tornado filling half
    the frame", "rooftop terrace", "never CGI", 17 Kas: "racing fast across the neighborhood", "never standing still")
    ve seçilen G'nin place metni var; HIT_KOPYA_FORBIDDEN'dan ("pans to
    follow", "Full action", "Until the last frame", "approaches from", "in the distance") hiçbiri yok (büyük/küçük harf
    fark etmez). İhlal = gönderilmez."""
    out = []
    text = text or ""
    low = text.lower()
    for need in HIT_KOPYA_REQUIRED:
        if need.lower() not in low:
            out.append(f'"{need}" eksik')
    places = [g for g, v in _HKA["geos"].items() if v["place"] in text]
    if not places:
        out.append("G1-G6 yer metni yok")
    elif geo is not None and places != [geo]:
        out.append(f"yer metni seçilen coğrafya değil ({geo}: {places})")
    for bad in HIT_KOPYA_FORBIDDEN:
        if bad.lower() in low:
            out.append(f"bu modda olmayan ifade var: {bad}")
    return out


def hit_kopya_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin şablondan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    tb = structure[HIT_KOPYA_MOD]
    if tb.get("geo") not in _HKA["geos"]:
        return [f"coğrafya G1-G6 değil ({tb.get('geo')})"]
    if tb.get("vehicle") not in _HKA["vehicles"]:
        return [f"araç bu modda yok ({tb.get('vehicle')})"]
    story = hit_kopya_story(tb["geo"], tb["vehicle"])
    prompt = hit_kopya_prompt(tb["geo"], tb["vehicle"])
    out = []
    if info.get("style_suffix") != hit_kopya_tail():
        out.append("stil eki hit kopyası değil")
    if info.get("story") != story:
        out.append("hikâye şablonla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt şablonla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out += hit_kopya_camera_issues(text, tb["geo"])
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > HIT_KOPYA_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {HIT_KOPYA_MAX_WORDS})")
    if len(text) > HIT_KOPYA_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {HIT_KOPYA_MAX_CHARS})")
    return out


# ── ⭐ Hit kopyası (orman yangını) (20 Kas 2026, Bahadır) ───────────────────────────────────────────────────────────
# Sebep: orman Yaklaşma v4-v7 testlerinin hiçbiri paylaşılabilir çıkmadı. Kaynak: 9 Eki 2026 21:52 üretimi (19 Eki
# paylaşımı), Kie prompt'u HIT_PROMPTS[es.WILDFIRE]["prompt"] (Notion 3f4d048d-625e-81f9-a10f-eaf888802f52, kayıt
# değişmez). Ateş hortumu Hit kopyasıyla (HIT_KOPYA_ATES) aynı düzen, ayrı sabitler ve fonksiyonlar. GPT çağrılmaz.
# Orman Yaklaşma v7 kodda ve menüde aynen kalır. Kayıt combo "##HKO:G*" (olay çifti değil: normal orman K*/L* ve
# Yaklaşma M*/N* LRU'su etkilenmez) + Eksenler mod=hit_kopya_orman, cografya, arac (v2: + engel, kisi, surum).
# 20 Kas (v2): v1 testi (G6 Şili, SUV) hit'le alakasız ve zayıf çıktı (3 kişi koşuyor, araç durgun, boş arazide
# patlama). Hit'in iskeleti ve dili kalır (alev duvarı yamaçtan inip mahalleye çarpar, balkon, eye level, pans to
# follow); zayıf betler (U dönüşü, ağaç tepeleri) çıktı; 6-8 kişi; ortada düşen adam + önüne devrilen yanan ağaç /
# direk (O1/O2 dönüşümlü, 13 Eki kül bulutu hit'indeki devrilen direklerden esinli); final balkonun dibindeki evin
# çatısı çöker. Yer artık stil ekinde ("a hillside house in {place}"). v1 şablon/listeler/metinler _V1 pasif kopya.
# 21 Kas (v3, Bahadır): v2 testinde (G5 Portekiz, O2 direk, 7 kişi) direk sahnesi ve gerçekçilik iyiydi ama kamera
# sürekli döndüğü için olaylar takip edilemedi ve balkon korkuluğu ilk 3 sn yoktu, sonra şekil değiştirdi. Tek
# değişiklik stil ekinde: "the camera pans to follow the wall of flames" → kamera sokağa sabit + koyu metal korkuluk
# baştan sona kadrajın altında sabit. Hikâye, coğrafya, araç, engel, kişi, LRU aynen. v2 _V2 pasif kopya; engel
# LRU'su v2 + v3 kayıtlarını sayar (engel ekseni aynı, dönüşüm v2'nin son engelinden devam eder).
HIT_KOPYA_ORMAN_MODE_LABEL = "⭐ Hit kopyası (orman yangını)"
HIT_KOPYA_ORMAN_EVENTS = (es.WILDFIRE,)
HIT_KOPYA_ORMAN_DOMAIN = "fire_disasters"
HIT_KOPYA_ORMAN_MOD = "hit_kopya_orman"             # config bayrağı, structure anahtarı, Notion axes.mod
HIT_KOPYA_ORMAN_SURUM = "v3"                         # Notion axes.surum
HIT_KOPYA_ORMAN_SURUM_V2 = "v2"                      # pasif (v2)
HIT_KOPYA_ORMAN_OBSTACLE_SURUMS = ("v2", "v3")       # engel LRU'su bu sürümlerin kayıtlarından (v1'de engel yok)
HIT_KOPYA_ORMAN_VERSION_LINE = "Sürüm: v3 (sabit kamera, sabit korkuluk)"
HIT_KOPYA_ORMAN_VERSION_LINE_V2 = "Sürüm: v2 (6-8 kişi, düşen adam + ağaç/direk, çatı çöker)"   # pasif (v2)
HIT_KOPYA_ORMAN_CAMERA = "sabit kamera (sokağa sabit), korkuluk kadrajın altında"   # ✋ Onay "Kamera:" satırı
HIT_KOPYA_ORMAN_CAMERA_V2 = ("hit kamerası (the camera pans to follow the wall of flames); balcony of a hillside "
                             "house, eye level, normal lens")   # pasif (v2)
HIT_KOPYA_ORMAN_CAMERA_AXIS = "sabit (sokağa sabit), korkuluk altta"   # Eksenler "kamera modu"
HIT_KOPYA_ORMAN_CAMERA_AXIS_V2 = "elde, alevleri takip (hit)"         # pasif (v2)
HIT_KOPYA_ORMAN_SPOT_LABEL = "Balcony of a hillside house (hit kopyası v3)"
HIT_KOPYA_ORMAN_SPOT_LABEL_V2 = "Balcony of a hillside house (hit kopyası v2)"   # pasif (v2)
HIT_KOPYA_ORMAN_SOURCE = "Kaynak: 9 Eki 21:52 üretimi (19 Eki paylaşımı, 5,4M), iskelet ve dil"
HIT_KOPYA_ORMAN_SOURCE_V1 = "Kaynak: 9 Eki 21:52 üretimi (19 Eki paylaşımı, 3M), birebir"   # pasif (v1)
HIT_KOPYA_ORMAN_MAX_WORDS = 230
HIT_KOPYA_ORMAN_MAX_CHARS = 1400
HIT_KOPYA_ORMAN_GEO_BLOCK = 3
HIT_KOPYA_ORMAN_GEO_SEED = ("G4",)   # 20 Kas Kanada paylaşımıyla benzemesin: geçmişin en başına G4 "kullanıldı"
HIT_KOPYA_ORMAN_VEHICLE_BLOCK = 2
HIT_KOPYA_ORMAN_OBSTACLE_BLOCK = 1   # iki engel: son 1 elenir = dönüşümlü
HIT_KOPYA_ORMAN_SPOT = "balcony of a hillside house"   # hit kaydının (K5+L4) yeri
HIT_KOPYA_ORMAN_PEOPLE_COUNT = {"Six": 6, "Seven": 7, "Eight": 8}
HIT_KOPYA_ORMAN_OBSTACLE_NAMES = {"O1": "yanan ağaç", "O2": "yanan direk"}
HIT_KOPYA_ORMAN = {
    "geos": {
        "G1": {"name": "Kaliforniya", "place": "a Californian suburb"},
        "G2": {"name": "Avustralya", "place": "an Australian bush town"},
        "G3": {"name": "Yunanistan", "place": "a Greek village"},
        "G4": {"name": "Kanada", "place": "a Canadian mountain town"},
        "G5": {"name": "Portekiz", "place": "a Portuguese village"},
        "G6": {"name": "Şili", "place": "a Chilean town"},
    },
    "vehicles": ("a white van", "a pickup truck", "an SUV"),   # artikeliyle; Onay ve Eksenler'de artikelsiz ad
    "obstacles": {"O1": "burning tree", "O2": "burning power pole"},
    "people": ("Six", "Seven", "Eight"),   # rastgele (LRU yok); Eksenler'de 6/7/8
    # Bahadır'ın v2 metni, birebir; v3 (21 Kas): yalnız kamera parçası değişti (sabit kamera + sabit korkuluk)
    "template": (
        "0-4s: A towering wall of flames sweeps down the forested slope and slams into the edge of the neighborhood, "
        "igniting roofs and trees. {people} people run desperately up the street toward the camera, scattering to "
        "escape the rapidly encroaching inferno, as {vehicle} speeds past them. 4-9s: One man trips and falls on the "
        "road; right in front of him a {obstacle} crashes down in a burst of sparks, and he scrambles up and keeps "
        "running. 9-15s: The flames reach the house right below the balcony and its roof caves in, a fountain of "
        "sparks bursting up toward the camera. Handheld footage shot by a person standing on a balcony of a hillside "
        "house in {place} overlooking the street and the burning slope, eye level, normal lens; slight hand shake, "
        "the camera stays fixed on the street; a dark metal balcony railing stays fixed at the bottom of the frame "
        "the whole time; no zoom, no cuts. Bystanders wear civilian clothes, never "
        "hi-vis PPE on civilians; emergency responders wear service uniforms. Raw natural light matching the "
        "weather, never glossy or CGI; no white hazmat suits. No readable signs, text or flags."),
    "tail_start": "Handheld footage shot by a person standing on a balcony",
}
HIT_KOPYA_ORMAN_CAMERA_OLD_V2 = "slight hand shake, the camera pans to follow the wall of flames; no zoom, no cuts."
HIT_KOPYA_ORMAN_CAMERA_NEW = ("slight hand shake, the camera stays fixed on the street; a dark metal balcony railing "
                              "stays fixed at the bottom of the frame the whole time; no zoom, no cuts.")
HIT_KOPYA_ORMAN_REQUIRED = ("sweeps down the forested slope and slams into the edge of the neighborhood",
                            "run desperately up the street toward the camera", "trips and falls",
                            "right in front of him", "scrambles up and keeps running", "its roof caves in",
                            "the camera stays fixed on the street", "railing stays fixed at the bottom of the frame",
                            "never glossy or CGI")
HIT_KOPYA_ORMAN_FORBIDDEN = ("U-turn", "their tops exploding", "Full action", "Until the last frame", "big in frame",
                             "From the very first frame", "the edge of a", "the edge of an", "onto him",
                             "on top of him", "pans to follow")
HIT_KOPYA_ORMAN_WARNING = ("⚠️ Hit karşılaştırması: alev duvarı ilk saniyelerde mahalleye çarpıyor mu, düşen adam ve "
                           "önüne devrilen ağaç/direk yakın ve net mi, çatı çöküyor mu, korkuluk baştan sona aynı yerde "
                           "ve aynı şekilde mi?")
# ── pasif (v2, 21 Kas 892fdf9): Bahadır'ın v2 metni, kamera alev duvarını takip eder ──
HIT_KOPYA_ORMAN_V2 = {
    "geos": {
        "G1": {"name": "Kaliforniya", "place": "a Californian suburb"},
        "G2": {"name": "Avustralya", "place": "an Australian bush town"},
        "G3": {"name": "Yunanistan", "place": "a Greek village"},
        "G4": {"name": "Kanada", "place": "a Canadian mountain town"},
        "G5": {"name": "Portekiz", "place": "a Portuguese village"},
        "G6": {"name": "Şili", "place": "a Chilean town"},
    },
    "vehicles": ("a white van", "a pickup truck", "an SUV"),
    "obstacles": {"O1": "burning tree", "O2": "burning power pole"},
    "people": ("Six", "Seven", "Eight"),
    "template": (
        "0-4s: A towering wall of flames sweeps down the forested slope and slams into the edge of the neighborhood, "
        "igniting roofs and trees. {people} people run desperately up the street toward the camera, scattering to "
        "escape the rapidly encroaching inferno, as {vehicle} speeds past them. 4-9s: One man trips and falls on the "
        "road; right in front of him a {obstacle} crashes down in a burst of sparks, and he scrambles up and keeps "
        "running. 9-15s: The flames reach the house right below the balcony and its roof caves in, a fountain of "
        "sparks bursting up toward the camera. Handheld footage shot by a person standing on a balcony of a hillside "
        "house in {place} overlooking the street and the burning slope, eye level, normal lens; slight hand shake, "
        "the camera pans to follow the wall of flames; no zoom, no cuts. Bystanders wear civilian clothes, never "
        "hi-vis PPE on civilians; emergency responders wear service uniforms. Raw natural light matching the "
        "weather, never glossy or CGI; no white hazmat suits. No readable signs, text or flags."),
    "tail_start": "Handheld footage shot by a person standing on a balcony",
}
HIT_KOPYA_ORMAN_REQUIRED_V2 = ("sweeps down the forested slope and slams into the edge of the neighborhood",
                               "run desperately up the street toward the camera", "trips and falls",
                               "right in front of him", "scrambles up and keeps running", "its roof caves in",
                               "the camera pans to follow the wall of flames", "never glossy or CGI")
HIT_KOPYA_ORMAN_FORBIDDEN_V2 = ("U-turn", "their tops exploding", "Full action", "Until the last frame",
                                "big in frame", "From the very first frame", "the edge of a", "the edge of an",
                                "onto him", "on top of him")
HIT_KOPYA_ORMAN_WARNING_V2 = ("⚠️ Hit karşılaştırması: alev duvarı ilk saniyelerde mahalleye çarpıyor mu, düşen adam "
                              "ve önüne devrilen ağaç/direk yakın ve net mi, çatı çöküyor mu?")
HIT_KOPYA_ORMAN_CONFIRM_DESC = ("9 Eki orman hit'inin (19 Eki paylaşımı, 5,4M) iskeleti ve dili; zayıf betler "
                                "çıkarıldı. Alev duvarı yamaçtan inip mahalleye çarpar, 6-8 kişi kameraya doğru kaçar, "
                                "yanlarından bir araç hızla geçer; kaçan bir adam düşer, hemen önüne yanan ağaç ya da "
                                "yanan elektrik direği (dönüşümlü) devrilir, adam kalkıp kaçmaya devam eder; final: "
                                "balkonun dibindeki evin çatısı çöker. Coğrafya (G1-G6) ve araç değişir. Hikâye için "
                                "GPT çağrılmaz.")
# ── pasif (v1, 20 Kas 7df29b5): hit prompt'u kelimesi kelimesine, yalnız "the edge of {place}" + "The {vehicle}" ──
HIT_KOPYA_ORMAN_V1 = {
    "geos": {
        "G1": {"name": "Kaliforniya", "place": "a Californian hillside suburb"},
        "G2": {"name": "Avustralya", "place": "an Australian bush town"},
        "G3": {"name": "Yunanistan", "place": "a Greek hillside village"},
        "G4": {"name": "Kanada", "place": "a Canadian mountain town"},
        "G5": {"name": "Portekiz", "place": "a Portuguese hillside village"},
        "G6": {"name": "Şili", "place": "a Chilean hillside town"},
    },
    "vehicles": ("white van", "pickup truck", "SUV"),
    "template": (
        "0-4s: A towering wall of flames sweeps down the forested slope and slams into the edge of {place}, "
        "igniting roofs and trees. Five people run desperately, scattering in various directions to "
        "escape the rapidly encroaching inferno. 4-9s: The {vehicle} accelerates, executing a sharp U-turn and "
        "leaves the scene, just as the flames close in behind. 9-15s: The advancing fire consumes an entire line "
        "of trees, their tops exploding into fiery embers, rising into the swirling sky. Handheld footage shot by "
        "a person standing on a balcony of a hillside house overlooking the street and the burning slope, eye "
        "level, normal lens; slight hand shake, the camera pans to follow the wall of flames; no zoom, no cuts. "
        "Bystanders wear civilian clothes, never hi-vis PPE on civilians; emergency responders wear service "
        "uniforms. Raw natural light matching the weather, never glossy or CGI; no white hazmat suits. No "
        "readable signs, text or flags."),
    "tail_start": "Handheld footage shot by a person standing on a balcony",
}
HIT_KOPYA_ORMAN_REQUIRED_V1 = ("sweeps down the forested slope and slams into the edge of",
                               "rapidly encroaching inferno", "sharp U-turn",
                               "the camera pans to follow the wall of flames", "never glossy or CGI")
HIT_KOPYA_ORMAN_FORBIDDEN_V1 = ("Full action", "Until the last frame", "big in frame", "From the very first frame",
                                "never along the asphalt")
HIT_KOPYA_ORMAN_WARNING_V1 = ("⚠️ Hit karşılaştırması: alev duvarı ilk saniyelerde yamaçtan inip mahalleye çarpıyor "
                              "mu, video 19 Eki hit'iyle boy ölçüşür mü?")
HIT_KOPYA_ORMAN_CONFIRM_DESC_V1 = ("9 Eki 21:52 üretiminin (19 Eki paylaşımı, 3M) Kie prompt'u kelimesi kelimesine; "
                                   "sadece coğrafya (G1-G6) ve araç değişir. Alev duvarı ormanlık yamaçtan inip "
                                   "mahalleye çarpar, insanlar kaçar, araç U dönüşü yapıp kaçar, ağaç sırası tepeden "
                                   "kıvılcım saçarak yanar. Yamaç evinin balkonu, kamera alevleri takip eder. Hikâye "
                                   "için GPT çağrılmaz.")
_HKO = HIT_KOPYA_ORMAN
_HIT_KOPYA_ORMAN_GEO_MEMORY: list[str] = []
_HIT_KOPYA_ORMAN_VEHICLE_MEMORY: list[str] = []
_HIT_KOPYA_ORMAN_OBSTACLE_MEMORY: list[str] = []


def hit_kopya_orman_is_active(event: str | None) -> bool:
    return event in HIT_KOPYA_ORMAN_EVENTS


def hit_kopya_orman_vehicle_names() -> list[str]:
    """Artikelsiz araç adları (Onay, Eksenler, LRU): white van, pickup truck, SUV."""
    return [v.split(" ", 1)[1] for v in _HKO["vehicles"]]


def _hit_kopya_orman_vehicle_phrase(name: str) -> str:
    return _HKO["vehicles"][hit_kopya_orman_vehicle_names().index(name)]


def _hit_kopya_orman_people_word(n: int) -> str:
    return next(w for w, k in HIT_KOPYA_ORMAN_PEOPLE_COUNT.items() if k == n)


def _hit_kopya_orman_split() -> tuple[str, str]:
    t = _HKO["template"]
    i = t.index(" " + _HKO["tail_start"])
    return t[:i], t[i + 1:]


def _hit_kopya_orman_check(geo: str, vehicle: str, obstacle: str = "O1", people: int = 6) -> None:
    if geo not in _HKO["geos"]:
        raise es.StructureError(f"{HIT_KOPYA_ORMAN_MODE_LABEL}: {geo} bu modda yok (coğrafya G1-G6)")
    if vehicle not in hit_kopya_orman_vehicle_names():
        raise es.StructureError(f"{HIT_KOPYA_ORMAN_MODE_LABEL}: araç bu modda yok ({vehicle})")
    if obstacle not in _HKO["obstacles"]:
        raise es.StructureError(f"{HIT_KOPYA_ORMAN_MODE_LABEL}: engel bu modda yok ({obstacle})")
    if people not in HIT_KOPYA_ORMAN_PEOPLE_COUNT.values():
        raise es.StructureError(f"{HIT_KOPYA_ORMAN_MODE_LABEL}: kişi sayısı 6-8 değil ({people})")


def hit_kopya_orman_tail(geo: str) -> str:
    """Stil eki (balkon kamerası); v2'de yer ({place}) burada."""
    _hit_kopya_orman_check(geo, hit_kopya_orman_vehicle_names()[0])
    return _hit_kopya_orman_split()[1].format(place=_HKO["geos"][geo]["place"])


def hit_kopya_orman_story(geo: str, vehicle: str, obstacle: str, people: int) -> str:
    """Zaman etiketli hikâye (stil ekinden önceki kısım): {people}, {vehicle} (artikelli), {obstacle} dolar."""
    _hit_kopya_orman_check(geo, vehicle, obstacle, people)
    return _hit_kopya_orman_split()[0].format(people=_hit_kopya_orman_people_word(people),
                                              vehicle=_hit_kopya_orman_vehicle_phrase(vehicle),
                                              obstacle=_HKO["obstacles"][obstacle])


def hit_kopya_orman_prompt(geo: str, vehicle: str, obstacle: str, people: int) -> str:
    """Prompt = şablon (birebir), yalnız yer tutucular dolar. join_story_and_style ile aynı metin."""
    from core.creative_engine import join_story_and_style
    return join_story_and_style(hit_kopya_orman_story(geo, vehicle, obstacle, people), hit_kopya_orman_tail(geo))


def hit_kopya_orman_axes_history(records: list | None, key: str,
                                 surum: str | tuple[str, ...] | None = None) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun `key` değerleri; okunamadıysa None. surum
    verilirse yalnız o sürüm(ler)in kayıtları (engel: v2 + v3, HIT_KOPYA_ORMAN_OBSTACLE_SURUMS)."""
    surums = (surum,) if isinstance(surum, str) else surum
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") in HIT_KOPYA_ORMAN_EVENTS
                and axes.get("mod") == HIT_KOPYA_ORMAN_MOD and axes.get(key)
                and (surums is None or axes.get("surum") in surums)):
            out.append(axes[key])
    return out


def hit_kopya_orman_choose_geo(used: list[str] | None = None, rng=None) -> str:
    """Son 3 coğrafya elenir; geçmişin en başında G4 tohumu (20 Kas Kanada paylaşımı)."""
    seen = list(HIT_KOPYA_ORMAN_GEO_SEED) + list(_HIT_KOPYA_ORMAN_GEO_MEMORY if used is None else used)
    return _block_pick(list(_HKO["geos"]), seen, HIT_KOPYA_ORMAN_GEO_BLOCK, rng)


def hit_kopya_orman_choose_vehicle(used: list[str] | None = None, rng=None) -> str:
    return _block_pick(hit_kopya_orman_vehicle_names(),
                       list(_HIT_KOPYA_ORMAN_VEHICLE_MEMORY if used is None else used),
                       HIT_KOPYA_ORMAN_VEHICLE_BLOCK, rng)


def hit_kopya_orman_choose_obstacle(used: list[str] | None = None, rng=None) -> str:
    """Son 1 engel elenir: O1 / O2 dönüşümlü."""
    return _block_pick(list(_HKO["obstacles"]), list(_HIT_KOPYA_ORMAN_OBSTACLE_MEMORY if used is None else used),
                       HIT_KOPYA_ORMAN_OBSTACLE_BLOCK, rng)


def hit_kopya_orman_lines(tb: dict) -> str:
    """✋ Onay satırları: mod, sürüm, kaynak, coğrafya, araç, kişi, engel, kamera, kelime/karakter, eksenler + tekrar
    önleme, hit karşılaştırması."""
    text = tb["prompt"]
    g = _HKO["geos"][tb["geo"]]
    lines = [
        f"Mod: {HIT_KOPYA_ORMAN_MODE_LABEL}",
        HIT_KOPYA_ORMAN_VERSION_LINE,
        HIT_KOPYA_ORMAN_SOURCE,
        f"Coğrafya: {tb['geo']} {g['name']} «{g['place']}»",
        f"Araç: {tb['vehicle']}",
        f"Kişi: {tb['people']}",
        f"Engel: {tb['obstacle']} {HIT_KOPYA_ORMAN_OBSTACLE_NAMES[tb['obstacle']]}",
        f"Kamera: {HIT_KOPYA_ORMAN_CAMERA}",   # v3 (21 Kas): sabit kamera + sabit korkuluk
        f"Kelime: {len(text.split())} (en fazla {HIT_KOPYA_ORMAN_MAX_WORDS}) · karakter: {len(text)} "
        f"(en fazla {HIT_KOPYA_ORMAN_MAX_CHARS})",
    ]
    if tb.get("axes_line"):
        lines.append(tb["axes_line"])
    lines.append(HIT_KOPYA_ORMAN_WARNING)
    return "\n".join(lines)


def hit_kopya_orman_axes_json(geo: str, vehicle: str, obstacle: str, people: int, excluded: dict | None = None) -> str:
    import core.axes_history as ah
    axes = {"spot": HIT_KOPYA_ORMAN_SPOT, "view": None, "light": None, "vehicle": vehicle, "people": people,
            "beats": f"HKO:{geo}", "mod": HIT_KOPYA_ORMAN_MOD, "cografya": geo, "arac": vehicle, "engel": obstacle,
            "kisi": people, "surum": HIT_KOPYA_ORMAN_SURUM}
    return ah.axes_json(es.WILDFIRE, axes, excluded)


def hit_kopya_orman_build_scene(domain: str | None, event: str | None, history: list[str] | None = None,
                                records: list | None = None, rng=None, history_source: str = "bellek") -> dict:
    """⭐ Hit kopyası (orman yangını) v3 sahnesi: GPT yok, normal hat yok. records = Notion "Eksenler" ham kayıtları
    (None = okunamadı / yükleyici yok: süreç hafızası). Coğrafya son 3 (G4 tohum), araç son 2 (v1 kayıtları da
    sayılır), engel son 1 (v2 + v3 kayıtları), kişi rastgele 6-8. structure["hit_kopya_orman"] Kie öncesi son
    denetimin (submit_issues) kaynağıdır."""
    import random
    from core.skeleton_pipeline import SKELETON_CAMERA
    if domain not in (None, HIT_KOPYA_ORMAN_DOMAIN) or not hit_kopya_orman_is_active(event):
        raise es.StructureError(f"{HIT_KOPYA_ORMAN_MODE_LABEL} kurulamadı: {domain} / {event}")
    r = rng or random
    geo_used = hit_kopya_orman_axes_history(records, "cografya")
    vehicle_used = hit_kopya_orman_axes_history(records, "arac")
    obstacle_used = hit_kopya_orman_axes_history(records, "engel", HIT_KOPYA_ORMAN_OBSTACLE_SURUMS)
    geo = hit_kopya_orman_choose_geo(geo_used, r)
    vehicle = hit_kopya_orman_choose_vehicle(vehicle_used, r)
    obstacle = hit_kopya_orman_choose_obstacle(obstacle_used, r)
    people = HIT_KOPYA_ORMAN_PEOPLE_COUNT[r.choice(_HKO["people"])]
    for m, v in ((_HIT_KOPYA_ORMAN_GEO_MEMORY, geo), (_HIT_KOPYA_ORMAN_VEHICLE_MEMORY, vehicle),
                 (_HIT_KOPYA_ORMAN_OBSTACLE_MEMORY, obstacle)):
        m.append(v)
        del m[:-12]
    story = hit_kopya_orman_story(geo, vehicle, obstacle, people)
    tail = hit_kopya_orman_tail(geo)
    prompt = hit_kopya_orman_prompt(geo, vehicle, obstacle, people)
    g = _HKO["geos"][geo]
    a, b, c = es.SLICE_LABELS
    opening = story.split(f"{b}: ")[0][len(f"{a}: "):].strip()
    mid_text = story.split(f"{b}: ")[1].split(f" {c}: ")[0]
    final_text = story.split(f"{c}: ")[1]
    plain = " ".join([opening, mid_text, final_text])
    seen_geo = list(HIT_KOPYA_ORMAN_GEO_SEED) + list(geo_used if geo_used is not None
                                                     else _HIT_KOPYA_ORMAN_GEO_MEMORY[:-1])
    seen_veh = list(vehicle_used if vehicle_used is not None else _HIT_KOPYA_ORMAN_VEHICLE_MEMORY[:-1])
    seen_obs = list(obstacle_used if obstacle_used is not None else _HIT_KOPYA_ORMAN_OBSTACLE_MEMORY[:-1])
    repeat = (f"coğrafya son {HIT_KOPYA_ORMAN_GEO_BLOCK}, G4 tohum · araç son {HIT_KOPYA_ORMAN_VEHICLE_BLOCK} · "
              f"engel son {HIT_KOPYA_ORMAN_OBSTACLE_BLOCK} · kişi rastgele 6-8")
    base_trace = {"pipeline": "creative", "structured": True, "domain": HIT_KOPYA_ORMAN_DOMAIN, "event": es.WILDFIRE,
                  "ship": "None", "camera": SKELETON_CAMERA, "view": None, "view_source": None,
                  "place": g["place"], "count_range": [6, 8], "people_running": people, "outcome": "-",
                  "recent_count": 0}
    obs_label = f"{obstacle} {HIT_KOPYA_ORMAN_OBSTACLE_NAMES[obstacle]}"
    trace, axes_line = mode_display(
        {"trace": base_trace}, {}, mode=HIT_KOPYA_ORMAN_MODE_LABEL,
        camera=HIT_KOPYA_ORMAN_CAMERA,
        opening=opening, mid=(obstacle, mid_text), final=("F", final_text), plain=plain, vehicle=vehicle,
        spot=HIT_KOPYA_ORMAN_SPOT_LABEL,
        axes={"sürüm": HIT_KOPYA_ORMAN_SURUM, "coğrafya": f"{geo} {g['name']}", "araç": vehicle, "kişi": people,
              "engel": obs_label, "final": "çatı çöker", "kamera modu": HIT_KOPYA_ORMAN_CAMERA_AXIS},
        repeat=repeat)
    trace = {**trace, "mode": HIT_KOPYA_ORMAN_MOD, "cografya": geo, "engel": obstacle,
             "surum": HIT_KOPYA_ORMAN_SURUM, "axes_source": history_source}
    tb = {"event": es.WILDFIRE, "geo": geo, "vehicle": vehicle, "obstacle": obstacle, "people": people,
          "story": story, "suffix": tail, "prompt": prompt, "axes_line": axes_line}
    tb["lines"] = hit_kopya_orman_lines(tb)
    excluded = {"cografya": [x for x in _HKO["geos"] if x in seen_geo[-HIT_KOPYA_ORMAN_GEO_BLOCK:]],
                "arac": [x for x in hit_kopya_orman_vehicle_names() if x in seen_veh[-HIT_KOPYA_ORMAN_VEHICLE_BLOCK:]],
                "engel": [x for x in _HKO["obstacles"] if x in seen_obs[-HIT_KOPYA_ORMAN_OBSTACLE_BLOCK:]]}
    axes_json = hit_kopya_orman_axes_json(geo, vehicle, obstacle, people, excluded)
    structure = {HIT_KOPYA_ORMAN_MOD: tb, "axes_json": axes_json, "axes_line": None, "environment": None,
                 "story_source": f"Hikâye: kod (birebir) · {HIT_KOPYA_ORMAN_MODE_LABEL}", "story_source_kind": "code",
                 "caption_info": {"opening": opening, "people": people, "kadraj": "balkon",
                                  "beat_2": donma_caption_beat(mid_text), "beat_3": donma_caption_beat(final_text)},
                 "caption_candidates": None}
    problems = hit_kopya_orman_issues(structure, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{HIT_KOPYA_ORMAN_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = (f"{HIT_KOPYA_ORMAN_DOMAIN}|none|{es.WILDFIRE.lower()}|{HIT_KOPYA_ORMAN_SPOT}##HKO:{geo}|"
             f"{SKELETON_CAMERA}")
    return {"domain": HIT_KOPYA_ORMAN_DOMAIN, "event": es.WILDFIRE, "ship": None, "spot": HIT_KOPYA_ORMAN_SPOT,
            "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt, "combo_key": combo,
            "trace": trace, "structure": structure, "axes_json": axes_json}


def hit_kopya_orman_camera_issues(text: str, geo: str | None = None) -> list[str]:
    """Kie öncesi son kontrol: HIT_KOPYA_ORMAN_REQUIRED ifadelerinin hepsi ve seçilen G'nin place metni var;
    HIT_KOPYA_ORMAN_FORBIDDEN'dan ("U-turn", "their tops exploding", "Full action", "Until the last frame", "big in
    frame", "From the very first frame", "the edge of a", "the edge of an", "onto him", "on top of him", "pans to
    follow") hiçbiri yok
    (büyük/küçük harf fark etmez). İhlal = gönderilmez."""
    out = []
    text = text or ""
    low = text.lower()
    for need in HIT_KOPYA_ORMAN_REQUIRED:
        if need.lower() not in low:
            out.append(f'"{need}" eksik')
    places = [g for g, v in _HKO["geos"].items() if v["place"] in text]
    if not places:
        out.append("G1-G6 yer metni yok")
    elif geo is not None and places != [geo]:
        out.append(f"yer metni seçilen coğrafya değil ({geo}: {places})")
    for bad in HIT_KOPYA_ORMAN_FORBIDDEN:
        if bad.lower() in low:
            out.append(f"bu modda olmayan ifade var: {bad}")
    return out


def hit_kopya_orman_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin şablondan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    tb = structure[HIT_KOPYA_ORMAN_MOD]
    if tb.get("geo") not in _HKO["geos"]:
        return [f"coğrafya G1-G6 değil ({tb.get('geo')})"]
    if tb.get("vehicle") not in hit_kopya_orman_vehicle_names():
        return [f"araç bu modda yok ({tb.get('vehicle')})"]
    if tb.get("obstacle") not in _HKO["obstacles"]:
        return [f"engel O1/O2 değil ({tb.get('obstacle')})"]
    if tb.get("people") not in HIT_KOPYA_ORMAN_PEOPLE_COUNT.values():
        return [f"kişi sayısı 6-8 değil ({tb.get('people')})"]
    args = (tb["geo"], tb["vehicle"], tb["obstacle"], tb["people"])
    story = hit_kopya_orman_story(*args)
    prompt = hit_kopya_orman_prompt(*args)
    out = []
    if info.get("style_suffix") != hit_kopya_orman_tail(tb["geo"]):
        out.append("stil eki hit kopyası değil")
    if info.get("story") != story:
        out.append("hikâye şablonla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt şablonla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out += hit_kopya_orman_camera_issues(text, tb["geo"])
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > HIT_KOPYA_ORMAN_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {HIT_KOPYA_ORMAN_MAX_WORDS})")
    if len(text) > HIT_KOPYA_ORMAN_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {HIT_KOPYA_ORMAN_MAX_CHARS})")
    return out


# ── ⭐ Hit kopyası (ani sel) (21 Kas 2026, Bahadır) ──────────────────────────────────────────────────────────────────
# Kaynak: 4 Kas 2026 01:57 üretimi (5 Kas paylaşımı, 355K izlenme), V12+D17, north_european_seaside. Orman Hit
# kopyasıyla (HIT_KOPYA_ORMAN) aynı düzen, ayrı sabitler ve fonksiyonlar. GPT çağrılmaz, metni tamamen kod üretir.
# Şablon Bahadır'ın metni, süslü parantez dışı birebir: {People} (Five/Six/Seven), {M} (4-9s, {vehicle} ile M1-M3),
# {F} (9-15s, F1-F3; otobüs ve bina/cephe yıkımı yok), {SETTING} (sel olayının 6 görünüm metni, view_district ile
# aynen), {LIGHT} (sel olayının ışık havuzu, aynen). Menü: Şehir Afeti → ⭐ Hit kopyası (ani sel) → 6 görünüm + 🎲
# Rastgele. LRU: görünüm (rastgele) son 2, M son 1, F son 2, araç son 1, ışık son 1, kişi son 1. Kadraj ve ön plan
# sabit (çatı, boş ön plan); LRU onlara dokunmaz. Kayıt combo "##HKS:<görünüm>" (olay çifti / görünüm değil: normal
# sel LRU'su etkilenmez) + Eksenler mod=hit_kopya_sel; normal eksen anahtarları (spot/view/light/vehicle/people/
# beats) boş yazılır ki normal sel hattının LRU'su bu kayıtları saymasın.
HIT_KOPYA_SEL_MODE_LABEL = "⭐ Hit kopyası (ani sel)"
HIT_KOPYA_SEL_EVENTS = (es.FLOOD,)
HIT_KOPYA_SEL_DOMAIN = "urban_city_disasters"
HIT_KOPYA_SEL_MOD = "hit_kopya_sel"                  # config bayrağı, structure anahtarı, Notion axes.mod
HIT_KOPYA_SEL_SURUM = "v1"                           # Notion axes.surum
HIT_KOPYA_SEL_VERSION_LINE = "Sürüm: hit_sel v1"
HIT_KOPYA_SEL_CAMERA = "sabit çatı, boş ön plan (hit ile aynı)"   # ✋ Onay "Kamera:" satırı
HIT_KOPYA_SEL_CAMERA_AXIS = "sabit çatı, boş ön plan"             # Eksenler "kamera modu"
HIT_KOPYA_SEL_SPOT = "flat rooftop above a dense downtown street"   # hit kaydının kamera yeri (combo)
HIT_KOPYA_SEL_SPOT_LABEL = "Flat rooftop above a dense downtown street (hit kopyası)"
HIT_KOPYA_SEL_SOURCE = ("Kaynak: 4 Kas 01:57 üretimi (5 Kas paylaşımı, 355K), V12+D17, north_european_seaside, "
                        "iskelet ve dil")
HIT_KOPYA_SEL_MAX_WORDS = 230
HIT_KOPYA_SEL_MAX_CHARS = 1400
HIT_KOPYA_SEL_VIEW_BLOCK = 2      # yalnız 🎲 Rastgele'de; menüden seçilen görünüm aynen
HIT_KOPYA_SEL_MID_BLOCK = 1
HIT_KOPYA_SEL_FINAL_BLOCK = 2
HIT_KOPYA_SEL_VEHICLE_BLOCK = 1
HIT_KOPYA_SEL_LIGHT_BLOCK = 1
HIT_KOPYA_SEL_PEOPLE_BLOCK = 1
HIT_KOPYA_SEL_PEOPLE_COUNT = {"Five": 5, "Six": 6, "Seven": 7}
HIT_KOPYA_SEL = {
    "people": ("Five", "Six", "Seven"),
    "vehicles": ("orange delivery truck", "green delivery van", "white SUV"),
    "mids": {
        "M1": "The {vehicle} floats free and is carried fast down the middle of the street.",
        "M2": "The {vehicle} is caught by the current, turns sideways and is dragged down the street.",
        "M3": "The {vehicle} is lifted, spins around and slams into the parked cars along the street.",
    },
    "finals": {
        "F1": "The surge lifts the parked cars and carries them down the street, crashing into each other.",
        "F2": "The surge flips a parked car onto its roof and carries it down the street.",
        "F3": "The surge tips a large box truck onto its side and pushes it along the street.",
    },
    # Bahadır'ın metni, süslü parantez dışı birebir
    "template": (
        "0-4s: A waist-high wall of brown muddy floodwater surges into the street. {People} people immediately flee "
        "from the overpowering surge. 4-9s: Water rises past the car windows. {M} 9-15s: A second surge, first-floor "
        "high, slams in. {F} Handheld footage filmed on a flat rooftop above a dense downtown street, high vantage; "
        "slight hand shake, the camera stays fixed, tilting only slightly, never descending, the floodwater always in "
        "frame, an empty foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. All "
        "people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI. Everything moves "
        "in real time, never in slow motion, people run at full speed. Setting: {SETTING}, in {LIGHT}, no readable "
        "signs, text or flags."),
    "tail_start": "Handheld footage filmed on a flat rooftop",
}
HIT_KOPYA_SEL_WATER = ("A waist-high wall of brown muddy floodwater surges into the street.",
                       "Water rises past the car windows.", "A second surge, first-floor high, slams in.")
HIT_KOPYA_SEL_REQUIRED = HIT_KOPYA_SEL_WATER + ("the camera stays fixed", "an empty foreground", "never CGI")
HIT_KOPYA_SEL_FORBIDDEN = ("bus", "GPT")                         # tüm çıktıda, alt dize
HIT_KOPYA_SEL_BEAT_FORBIDDEN = ("building", "facade", "collapse")  # yalnız M ve F cümlelerinde (görünüm metni aynen)
HIT_KOPYA_SEL_NAMES = {"M1": "araç akıntıda sürüklenir", "M2": "araç yan döner, sürüklenir",
                       "M3": "araç döner, park hâlindeki arabalara çarpar",
                       "F1": "park hâlindeki arabalar birbirine çarparak sürüklenir", "F2": "araba ters döner",
                       "F3": "kamyon yan yatar"}
HIT_KOPYA_SEL_WARNING = ("⚠️ Hit karşılaştırması: su duvarı ilk saniyelerde caddeye giriyor mu, insanlar kaçıyor mu, araç "
                         "akıntıyla gidiyor mu, ikinci dalga birinci kat yüksekliğinde mi, kamera çatıda sabit mi?")
HIT_KOPYA_SEL_CONFIRM_DESC = ("5 Kas ani sel hit'inin (355K) iskeleti ve dili. Bel hizasında kahverengi çamurlu su "
                              "duvarı caddeye girer, 5-7 kişi kaçar; su araba camlarını geçer, araç akıntıya kapılır "
                              "(M1-M3); ikinci dalga birinci kat yüksekliğinde çarpar (F1-F3, otobüs ve bina yıkımı "
                              "yok). Çatıdan sabit kamera, boş ön plan. Araç, orta, final, kişi, ışık ✋ Onay "
                              "mesajında. Hikâye için GPT çağrılmaz.")
_HKS = HIT_KOPYA_SEL
_HIT_KOPYA_SEL_MEMORY_KEYS = ("gorunum", "m", "f", "arac", "isik", "kisi")
_HIT_KOPYA_SEL_VIEW_MEMORY: list[str] = []
_HIT_KOPYA_SEL_MID_MEMORY: list[str] = []
_HIT_KOPYA_SEL_FINAL_MEMORY: list[str] = []
_HIT_KOPYA_SEL_VEHICLE_MEMORY: list[str] = []
_HIT_KOPYA_SEL_LIGHT_MEMORY: list[str] = []
_HIT_KOPYA_SEL_PEOPLE_MEMORY: list[str] = []


def hit_kopya_sel_is_active(event: str | None) -> bool:
    return event in HIT_KOPYA_SEL_EVENTS


def hit_kopya_sel_views() -> list[str]:
    """Sel olayının 6 görünümü (skeleton_pipeline.REGION_VIEWS sırası)."""
    from core.skeleton_pipeline import REGION_VIEWS
    return list(REGION_VIEWS)


def hit_kopya_sel_setting(view: str) -> str:
    """{SETTING}: normal sel hattının görünüm cümlesi, aynen (view_district)."""
    from core.skeleton_pipeline import view_district
    return view_district(es.FLOOD, view)


def hit_kopya_sel_lights() -> list[str]:
    """{LIGHT}: sel olayının ışık havuzu, aynen (EVENT_SKELETONS[FLOOD]["weather"])."""
    from core.skeleton_pipeline import EVENT_SKELETONS
    return list(EVENT_SKELETONS[es.FLOOD]["weather"])


def _hit_kopya_sel_check(view: str, vehicle: str, mid: str, final: str, people: int, light: str) -> None:
    if view not in hit_kopya_sel_views():
        raise es.StructureError(f"{HIT_KOPYA_SEL_MODE_LABEL}: görünüm bu modda yok ({view})")
    if vehicle not in _HKS["vehicles"]:
        raise es.StructureError(f"{HIT_KOPYA_SEL_MODE_LABEL}: araç bu modda yok ({vehicle})")
    if mid not in _HKS["mids"]:
        raise es.StructureError(f"{HIT_KOPYA_SEL_MODE_LABEL}: orta M1-M3 değil ({mid})")
    if final not in _HKS["finals"]:
        raise es.StructureError(f"{HIT_KOPYA_SEL_MODE_LABEL}: final F1-F3 değil ({final})")
    if people not in HIT_KOPYA_SEL_PEOPLE_COUNT.values():
        raise es.StructureError(f"{HIT_KOPYA_SEL_MODE_LABEL}: kişi sayısı 5-7 değil ({people})")
    if light not in hit_kopya_sel_lights():
        raise es.StructureError(f"{HIT_KOPYA_SEL_MODE_LABEL}: ışık bu modda yok ({light})")


def hit_kopya_sel_mid(mid: str, vehicle: str) -> str:
    return _HKS["mids"][mid].format(vehicle=vehicle)


def hit_kopya_sel_prompt(view: str, vehicle: str, mid: str, final: str, people: int, light: str) -> str:
    """Prompt = şablon (birebir), yalnız yer tutucular dolar."""
    _hit_kopya_sel_check(view, vehicle, mid, final, people, light)
    word = next(w for w, k in HIT_KOPYA_SEL_PEOPLE_COUNT.items() if k == people)
    return _HKS["template"].format(People=word, M=hit_kopya_sel_mid(mid, vehicle), F=_HKS["finals"][final],
                                   SETTING=hit_kopya_sel_setting(view), LIGHT=light)


def hit_kopya_sel_story(*args) -> str:
    """Zaman etiketli hikâye (stil ekinden önceki kısım)."""
    p = hit_kopya_sel_prompt(*args)
    return p[:p.index(" " + _HKS["tail_start"])]


def hit_kopya_sel_tail(*args) -> str:
    """Stil eki (çatı kamerası + Setting satırı)."""
    p = hit_kopya_sel_prompt(*args)
    return p[p.index(" " + _HKS["tail_start"]) + 1:]


def hit_kopya_sel_axes_history(records: list | None, key: str) -> list | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu modun `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") in HIT_KOPYA_SEL_EVENTS
                and axes.get("mod") == HIT_KOPYA_SEL_MOD and axes.get(key) not in (None, "")):
            out.append(axes[key])
    return out


def hit_kopya_sel_lines(tb: dict) -> str:
    """✋ Onay satırları: mod, sürüm, kaynak, görünüm, araç, M, F, kişi, ışık, kamera, kelime/karakter, eksenler +
    tekrar önleme, hit karşılaştırması."""
    text = tb["prompt"]
    lines = [
        f"Mod: {HIT_KOPYA_SEL_MODE_LABEL}",
        HIT_KOPYA_SEL_VERSION_LINE,
        HIT_KOPYA_SEL_SOURCE,
        f"Görünüm: {tb['view']} «{hit_kopya_sel_setting(tb['view'])}» ({tb['view_source']})",
        f"Araç: {tb['vehicle']}",
        f"M (4-9s): {tb['mid']} {HIT_KOPYA_SEL_NAMES[tb['mid']]}",
        f"F (9-15s): {tb['final']} {HIT_KOPYA_SEL_NAMES[tb['final']]}",
        f"Kişi: {tb['people']}",
        f"Işık: {tb['light']}",
        f"Kamera: {HIT_KOPYA_SEL_CAMERA}",
        f"Kelime: {len(text.split())} (en fazla {HIT_KOPYA_SEL_MAX_WORDS}) · karakter: {len(text)} "
        f"(en fazla {HIT_KOPYA_SEL_MAX_CHARS})",
    ]
    if tb.get("axes_line"):
        lines.append(tb["axes_line"])
    lines.append(HIT_KOPYA_SEL_WARNING)
    return "\n".join(lines)


def hit_kopya_sel_axes_json(tb: dict, excluded: dict | None = None) -> str:
    import core.axes_history as ah
    axes = {"spot": None, "view": None, "light": None, "vehicle": None, "people": None, "beats": None,
            "mod": HIT_KOPYA_SEL_MOD, "gorunum": tb["view"], "gorunum_kaynak": tb["view_source"],
            "arac": tb["vehicle"], "m": tb["mid"], "f": tb["final"], "isik": tb["light"], "kisi": tb["people"],
            "surum": HIT_KOPYA_SEL_SURUM}
    return ah.axes_json(es.FLOOD, axes, excluded)


def hit_kopya_sel_build_scene(domain: str | None, event: str | None, history: list[str] | None = None,
                              records: list | None = None, rng=None, history_source: str = "bellek",
                              view: str | None = None) -> dict:
    """⭐ Hit kopyası (ani sel) sahnesi: GPT yok, normal hat yok. view = menüden seçilen görünüm (None = 🎲 Rastgele,
    son 2 elenir). records = Notion "Eksenler" ham kayıtları (None = süreç hafızası). structure["hit_kopya_sel"] Kie
    öncesi son denetimin (submit_issues) kaynağıdır."""
    import random
    from core.skeleton_pipeline import SKELETON_CAMERA
    if domain not in (None, HIT_KOPYA_SEL_DOMAIN) or not hit_kopya_sel_is_active(event):
        raise es.StructureError(f"{HIT_KOPYA_SEL_MODE_LABEL} kurulamadı: {domain} / {event}")
    if view is not None and view not in hit_kopya_sel_views():
        raise es.StructureError(f"{HIT_KOPYA_SEL_MODE_LABEL}: görünüm bu modda yok ({view})")
    r = rng or random
    memories = {"gorunum": _HIT_KOPYA_SEL_VIEW_MEMORY, "m": _HIT_KOPYA_SEL_MID_MEMORY,
                "f": _HIT_KOPYA_SEL_FINAL_MEMORY, "arac": _HIT_KOPYA_SEL_VEHICLE_MEMORY,
                "isik": _HIT_KOPYA_SEL_LIGHT_MEMORY, "kisi": _HIT_KOPYA_SEL_PEOPLE_MEMORY}
    seen = {}
    for key, mem in memories.items():
        h = hit_kopya_sel_axes_history(records, key)
        seen[key] = list(mem if h is None else h)
    seen["kisi"] = [next((w for w, k in HIT_KOPYA_SEL_PEOPLE_COUNT.items() if k == n), n) for n in seen["kisi"]]
    axes_spec = (("gorunum", hit_kopya_sel_views(), HIT_KOPYA_SEL_VIEW_BLOCK),
                 ("arac", list(_HKS["vehicles"]), HIT_KOPYA_SEL_VEHICLE_BLOCK),
                 ("m", list(_HKS["mids"]), HIT_KOPYA_SEL_MID_BLOCK),
                 ("f", list(_HKS["finals"]), HIT_KOPYA_SEL_FINAL_BLOCK),
                 ("isik", hit_kopya_sel_lights(), HIT_KOPYA_SEL_LIGHT_BLOCK),
                 ("kisi", list(_HKS["people"]), HIT_KOPYA_SEL_PEOPLE_BLOCK))
    picked, excluded = {}, {}
    for key, ids, block in axes_spec:
        if key == "gorunum" and view is not None:
            picked[key], excluded[key] = view, []
            continue
        picked[key] = _block_pick(ids, seen[key], block, r)
        excluded[key] = [x for x in ids if x in seen[key][-block:]]
    people = HIT_KOPYA_SEL_PEOPLE_COUNT[picked["kisi"]]
    excluded["kisi"] = [HIT_KOPYA_SEL_PEOPLE_COUNT[w] for w in excluded["kisi"]]
    for key, mem in memories.items():
        mem.append(people if key == "kisi" else picked[key])
        del mem[:-12]
    args = (picked["gorunum"], picked["arac"], picked["m"], picked["f"], people, picked["isik"])
    prompt = hit_kopya_sel_prompt(*args)
    story = hit_kopya_sel_story(*args)
    tail = hit_kopya_sel_tail(*args)
    a, b, c = es.SLICE_LABELS
    opening = story.split(f" {b}: ")[0][len(f"{a}: "):].strip()
    mid_text = story.split(f"{b}: ")[1].split(f" {c}: ")[0]
    final_text = story.split(f"{c}: ")[1]
    plain = " ".join([opening, mid_text, final_text])
    view_source = "menü" if view is not None else "rastgele"
    repeat = (f"görünüm son {HIT_KOPYA_SEL_VIEW_BLOCK} (yalnız rastgele) · araç son {HIT_KOPYA_SEL_VEHICLE_BLOCK} · "
              f"M son {HIT_KOPYA_SEL_MID_BLOCK} · F son {HIT_KOPYA_SEL_FINAL_BLOCK} · ışık son "
              f"{HIT_KOPYA_SEL_LIGHT_BLOCK} · kişi son {HIT_KOPYA_SEL_PEOPLE_BLOCK} · kadraj ve ön plan sabit")
    base_trace = {"pipeline": "creative", "structured": True, "domain": HIT_KOPYA_SEL_DOMAIN, "event": es.FLOOD,
                  "ship": "None", "camera": SKELETON_CAMERA, "view": picked["gorunum"], "view_source": view_source,
                  "place": hit_kopya_sel_setting(picked["gorunum"]), "count_range": [5, 7], "people_running": people,
                  "outcome": "-", "recent_count": 0}
    trace, axes_line = mode_display(
        {"trace": base_trace}, {}, mode=HIT_KOPYA_SEL_MODE_LABEL, camera=HIT_KOPYA_SEL_CAMERA,
        opening=opening, mid=(picked["m"], mid_text), final=(picked["f"], final_text), plain=plain,
        vehicle=picked["arac"], spot=HIT_KOPYA_SEL_SPOT_LABEL, weather=picked["isik"],
        axes={"sürüm": HIT_KOPYA_SEL_SURUM, "görünüm": f"{picked['gorunum']} ({view_source})", "araç": picked["arac"],
              "M": picked["m"], "F": picked["f"], "kişi": people, "ışık": picked["isik"],
              "kamera modu": HIT_KOPYA_SEL_CAMERA_AXIS},
        repeat=repeat)
    trace = {**trace, "mode": HIT_KOPYA_SEL_MOD, "surum": HIT_KOPYA_SEL_SURUM, "axes_source": history_source}
    tb = {"event": es.FLOOD, "view": picked["gorunum"], "view_source": view_source, "vehicle": picked["arac"],
          "mid": picked["m"], "final": picked["f"], "people": people, "light": picked["isik"], "story": story,
          "suffix": tail, "prompt": prompt, "axes_line": axes_line}
    tb["lines"] = hit_kopya_sel_lines(tb)
    axes_json = hit_kopya_sel_axes_json(tb, excluded)
    structure = {HIT_KOPYA_SEL_MOD: tb, "axes_json": axes_json, "axes_line": None, "environment": None,
                 "story_source": f"Hikâye: kod (birebir) · {HIT_KOPYA_SEL_MODE_LABEL}", "story_source_kind": "code",
                 "caption_info": {"opening": opening, "people": people, "kadraj": "çatı",
                                  "beat_2": donma_caption_beat(mid_text), "beat_3": donma_caption_beat(final_text)},
                 "caption_candidates": None}
    problems = hit_kopya_sel_issues(structure, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{HIT_KOPYA_SEL_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = (f"{HIT_KOPYA_SEL_DOMAIN}|none|{es.FLOOD.lower()}|{HIT_KOPYA_SEL_SPOT}##HKS:{picked['gorunum']}|"
             f"{SKELETON_CAMERA}")
    return {"domain": HIT_KOPYA_SEL_DOMAIN, "event": es.FLOOD, "ship": None, "spot": HIT_KOPYA_SEL_SPOT,
            "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt, "combo_key": combo,
            "trace": trace, "structure": structure, "axes_json": axes_json}


def hit_kopya_sel_text_issues(text: str, mid_text: str | None = None, final_text: str | None = None) -> list[str]:
    """Kie öncesi son kontrol: üç su cümlesi ve kamera ifadeleri birebir var; "bus" ve "GPT" tüm metinde yok; M ve F
    cümlelerinde "building", "facade", "collapse" yok (büyük/küçük harf fark etmez). İhlal = gönderilmez."""
    out = []
    text = text or ""
    for need in HIT_KOPYA_SEL_REQUIRED:
        if need not in text:
            out.append(f'"{need}" eksik')
    for bad in HIT_KOPYA_SEL_FORBIDDEN:
        if bad.lower() in text.lower():
            out.append(f"bu modda olmayan ifade var: {bad}")
    for label, beat in (("M", mid_text), ("F", final_text)):
        for bad in HIT_KOPYA_SEL_BEAT_FORBIDDEN:
            if beat is not None and bad in beat.lower():
                out.append(f"{label} cümlesinde yasak kelime: {bad}")
    return out


def hit_kopya_sel_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin şablondan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    tb = structure[HIT_KOPYA_SEL_MOD]
    args = (tb.get("view"), tb.get("vehicle"), tb.get("mid"), tb.get("final"), tb.get("people"), tb.get("light"))
    try:
        _hit_kopya_sel_check(*args)
    except es.StructureError as e:
        return [str(e)]
    prompt, story, tail = hit_kopya_sel_prompt(*args), hit_kopya_sel_story(*args), hit_kopya_sel_tail(*args)
    out = []
    if info.get("style_suffix") != tail:
        out.append("stil eki hit kopyası değil")
    if info.get("story") != story:
        out.append("hikâye şablonla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt şablonla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out += hit_kopya_sel_text_issues(text, hit_kopya_sel_mid(tb["mid"], tb["vehicle"]), _HKS["finals"][tb["final"]])
    if f"Setting: {hit_kopya_sel_setting(tb['view'])}, in {tb['light']}," not in text:
        out.append("Setting satırı seçilen görünüm + ışık değil")
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > HIT_KOPYA_SEL_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {HIT_KOPYA_SEL_MAX_WORDS})")
    if len(text) > HIT_KOPYA_SEL_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {HIT_KOPYA_SEL_MAX_CHARS})")
    return out


# ── ⭐ Hit kopyası (kül bulutu) (24 Kas 2026, Bahadır) ───────────────────────────────────────────────────────────────
# Kaynak: 13 Eki 2026 11:23 üretimi "Pyroclastic Cloud Engulfs Village Street" (13 Eki paylaşımı, 2,1M izlenme).
# Sel ve orman Hit kopyasıyla (HIT_KOPYA_SEL, HIT_KOPYA_ORMAN) aynı düzen, ayrı sabitler ve fonksiyonlar. GPT
# çağrılmaz, metni tamamen kod üretir. Şablon Bahadır'ın metni, süslü parantez dışı birebir (24 Kas kararı: "above
# {place}"; F2'de "blasts" yerine "hurls", çünkü "blast" yasak). {place} = kül bulutu Yaklaşma modunun V1-V6 yer
# metni, aynen (YAKLASMA_KUL_BULUTU["geos"][V]["place"]); {People} Six/Seven/Eight; {M} M1-M2; {F} F1-F2.
# Menü: Volkan → ⭐ Hit kopyası (kül bulutu) → V1-V6 + 🎲 Rastgele + 🔙 Geri. LRU: coğrafya (yalnız rastgele) son 2,
# M son 1, F son 1, kişi son 1; kamera ve ışık sabit. Kayıt combo "##HKK:<V>" (olay çifti yok: normal kül bulutu
# hatlarının LRU'su etkilenmez) + Eksenler mod=hit_kopya_kul; normal eksen anahtarları (spot/view/light/vehicle/
# people) boş yazılır. Mevcut kül bulutu modları (Yaklaşma, yapılandırılmış hat) değişmez.
# 24 Kas (v2, Bahadır; ilk test 3/10: kamera alçak, bulut geç ve birden, patlama bomba gibi, final simsiyah, insanlar
# yakın): yeni şablon (bulut ilk karede, lav arka planda, kamera yamaçta köyün çok üstünde), bu moda özel V1-V6 yer
# metinleri (HIT_KOPYA_KUL_PLACES; Yaklaşma metinleri değişmez), yeni M1-M2 ve F1-F2 (karanlık yok, kalın kahverengi
# kül). v1 şablonu, M, F, yer metinleri ve ilgili satırlar _V1 olarak pasif. Kişi, LRU, menü, callback'ler aynen.
# 24 Kas (v3, Bahadır; Japonya testi: volkan çok yakın ve devasa, "upper third" + "tilting down no more than slightly"
# kamerayı yukarı baktırıp çatı hizasına indirdi, bulut dar sütun gibi aktı, ağaç devrilmesi görünmedi; direk
# Endonezya'da çalıştı): yeni şablon (volkan uzakta ufukta, kamera köye dik aşağı bakar, geniş bulut duvarı), M1-M2
# ikisi de direk (ağaç yok). F1-F2, yer metinleri, kişi, LRU, menü, callback'ler aynen. v2 şablonu, M1-M2 ve ilgili
# satırlar _V2 olarak pasif.
# 24 Kas (v4, Bahadır; v1-v3'te hit prompt'u fazla değiştirildi, sonuçlar kötüleşti): 13 Eki 11:23 hit prompt'u
# KELİMESİ KELİMESİNE (HIT_KOPYA_KUL_HIT_PROMPT); tek fark ilk cümlede "slams into a village street" yerine "slams into
# the street of {place}". {place} = v2 yer metinleri (HIT_KOPYA_KUL_PLACES) aynen. M, F ve kişi ekseni yok (hitteki
# gibi sabit: dört köylü, ağaçlar + direkler, eve çarpma). Menü, coğrafya LRU (yalnız rastgele, son 2), callback'ler
# ve ayrı geçmiş alanları aynen. v3 şablonu, M, F, kişi ekseni, zorunlu/yasak listeleri ve satırlar _V3 olarak pasif.
# 24 Kas (v5, Bahadır; v4 İtalya testinde de kamera alçak kaldı, direk koşanların arkasına devrildi, insanlar durup
# geriye baktı, kamera döndü): hitin işe yarayan cümleleri korunur; kamera yüksekliği (yamaçtaki uzun evin üst kat
# balkonu, geniş açı, dik aşağı), direğin konumu (koşanların önünde, kamera ile aralarında), koşuş yönü (durmadan
# kameraya) ve final (bulut evlere çarpıp kameraya ilerler) açıkça yazılır. {houses} = YALNIZ ev tipi (bu moda özel,
# "hillside" yok; HIT_KOPYA_KUL_HOUSES). M, F, kişi ekseni yok. Menü, coğrafya LRU (yalnız rastgele, son 2),
# callback'ler, ayrı geçmiş alanları aynen. v4 şablonu, v4 yer metinleri (HIT_KOPYA_KUL_PLACES_V4) ve v4 hit
# karşılaştırması _V4 olarak pasif. Kie öncesi denetim: v5 şablonundan bayt bayt + zorunlu/yasak ifadeler.
# 24 Kas (v6, Bahadır; v5'te volkan kenarda kaldı, bulut iki katman oldu, direk uzakta devrildi, kimse düşmedi, ışık
# güneşli çıktı): hit videosunun asıl geometrisi. Kamera köyün hemen üstündeki yamaçta bir evin terasında; köy caddesi
# kameradan dümdüz aşağı, volkana doğru uzanır; volkan karenin tam ortasında, caddenin bittiği yerin hemen arkasında.
# Tek geniş bulut duvarı; bir adam düşer, direk tam önüne kıvılcımla devrilir; bulut caddeden kameraya tırmanıp terası
# kahverengi küle gömer; kül grisi gökyüzü. {houses} = v5 ev metinleri aynen. M, F, kişi ekseni yok. Menü, coğrafya
# LRU, callback'ler, ayrı geçmiş alanları aynen. v5 şablonu, zorunlu/yasak listeleri, denetim ve satırlar _V5 olarak
# pasif. Kie öncesi denetim: v6 şablonundan bayt bayt + v6 zorunlu/yasak ifadeler.
# 24 Kas (v7, Bahadır; hit videosu ile v6 videosu yan yana: hitin görünümünü yaratan, hit prompt'unda coğrafya
# olmadığı için modelin çizdiği seyrek evli, geniş ana yollu kasaba; Avrupa/Japonya ev tarifleri sık, dar sokaklı köy
# çizdirip kamerayı çatıların dibine indiriyor): 13 Eki hit prompt'u (v4) BİREBİR; tek fark "slams into a village
# street" yerine köy yapısını tarif eden ifade (HIT_KOPYA_KUL_TOWN_PHRASE_V7). Coğrafya yalnız V2, V4, V5, V6 (seyrek
# kasabaya uyan dört ülke, {houses} = v5 ev metinleri aynen); V1 İtalya ve V3 Japonya bu modda pasif (menüde yok,
# rastgele yolunda seçilmez, kodda duruyor). Rastgele LRU dört coğrafya içinde son 2. M, F, kişi ekseni yok. Menü
# düzeni, callback'ler, ayrı geçmiş alanları aynen. v6 şablonu, zorunlu/yasak listeleri, denetim ve satırlar _V6
# olarak pasif. Kie öncesi denetim: hit prompt'unun tek ifade değişmiş hâliyle bayt bayt (kelime yasağı yok).
# 25 Kas (v8, Bahadır; v7 Guatemala testinde kamera tuttu ama insanlar volkana koştu, koni kül sütunu arkasında
# kayboldu, direkler insanlar geçtikten sonra devrildi, sahne boştu): kamera/stil cümlesi ve kasaba tarifi v7'deki gibi
# BİREBİR; yalnız aksiyon cümleleri değişti (lav koniden akar, çatılarda izleyenler, dört köylü kameraya koşar, düşen
# adamın tam önüne direk, bulut araçları sürükler ve eve çarpar) ve kasaba cümlesine "{vehicles} parked along the
# roadside, " eklendi (HIT_KOPYA_KUL_VEHICLES, coğrafyaya göre). Coğrafya, menü, LRU, callback, geçmiş alanları aynen.
# v7 şablonu, hit karşılaştırması ve satırlar _V7 olarak pasif. Kie öncesi denetim: v8 şablonundan bayt bayt +
# zorunlu/yasak ifadeler + stil eki = hit stil eki.
HIT_KOPYA_KUL_MODE_LABEL = "⭐ Hit kopyası (kül bulutu)"
HIT_KOPYA_KUL_EVENTS = (es.PYROCLASTIC,)
HIT_KOPYA_KUL_DOMAIN = "volcano_disasters"
HIT_KOPYA_KUL_MOD = "hit_kopya_kul"                  # config bayrağı, structure anahtarı, Notion axes.mod
HIT_KOPYA_KUL_GEO_KEY = "hit_kopya_kul_geo"          # config anahtarı: menüden seçilen V (yoksa 🎲 Rastgele)
HIT_KOPYA_KUL_SURUM = "v8"                           # Notion axes.surum (25 Kas v8)
HIT_KOPYA_KUL_VERSION_LINE = ("Sürüm: hit_kul v8 (v7 kamerası/kasabası birebir + yönlü aksiyon + park halinde araçlar + "
                              "çatılarda izleyenler)")
HIT_KOPYA_KUL_CAMERA = "hit kamerası (tepe terası, volkan üst üçte birde), birebir"   # ✋ Onay
HIT_KOPYA_KUL_CAMERA_AXIS = HIT_KOPYA_KUL_CAMERA   # Eksenler
HIT_KOPYA_KUL_EVENTS_LINE = ("Olaylar: bulut ana yolun ucuna çarpar, lav volkanın konisinden akar · çatılarda insanlar "
                             "izler, dört köylü kameraya koşar · biri düşer, tam önüne direk kıvılcımla devrilir · "
                             "bulut park halindeki araçları sürükler, eve çarpar")   # ✋ Onay
HIT_KOPYA_KUL_PEOPLE = 4                             # "four villagers" (sabit)
HIT_KOPYA_KUL_SURUM_V7 = "v7"                                                                  # pasif (v7)
HIT_KOPYA_KUL_VERSION_LINE_V7 = "Sürüm: hit_kul v7 (hit prompt'u birebir + seyrek kasaba, geniş ana yol)"   # pasif (v7)
HIT_KOPYA_KUL_CAMERA_V7 = "hit kamerası (tepe terası, volkan üst üçte birde), birebir"         # pasif (v7; v8 ile aynı)
HIT_KOPYA_KUL_CAMERA_AXIS_V7 = HIT_KOPYA_KUL_CAMERA_V7                                         # pasif (v7)
HIT_KOPYA_KUL_EVENTS_LINE_V7 = "Olaylar: hit ile birebir (ağaçlar ve direkler devrilir, bulut eve çarpar)"   # pasif (v7)
HIT_KOPYA_KUL_SURUM_V6 = "v6"                                                                  # pasif (v6)
HIT_KOPYA_KUL_VERSION_LINE_V6 = ("Sürüm: hit_kul v6 (hit geometrisi: yamaçtaki ev terası, cadde dümdüz volkana "
                                 "uzanır, volkan ortada)")                                     # pasif (v6)
HIT_KOPYA_KUL_CAMERA_V6 = ("yamaçtaki evin terası, cadde kameradan volkana dümdüz uzanır, volkan karenin ortasında, "
                           "dönmez")                                                           # pasif (v6)
HIT_KOPYA_KUL_CAMERA_AXIS_V6 = HIT_KOPYA_KUL_CAMERA_V6                                         # pasif (v6)
HIT_KOPYA_KUL_EVENTS_LINE_V6 = ("Olaylar: tek geniş bulut duvarı caddenin ucuna çarpar · adam düşer, önüne direk "
                                "kıvılcımla devrilir · bulut caddeden kameraya tırmanıp terası kahverengi küle "
                                "gömer")                                                       # pasif (v6)
HIT_KOPYA_KUL_SURUM_V5 = "v5"                                                                  # pasif (v5)
HIT_KOPYA_KUL_VERSION_LINE_V5 = ("Sürüm: hit_kul v5 (yüksek balkon + geniş açı, direk koşanların önünde, köy vadide "
                                 "düzde)")                                                     # pasif (v5)
HIT_KOPYA_KUL_CAMERA_V5 = "yamaçtaki uzun evin üst kat balkonu, geniş açı, köye dik aşağı bakar, dönmez"   # pasif (v5)
HIT_KOPYA_KUL_CAMERA_AXIS_V5 = HIT_KOPYA_KUL_CAMERA_V5                                         # pasif (v5)
HIT_KOPYA_KUL_EVENTS_LINE_V5 = ("Olaylar: bulut köye çarpar · direk koşanların önüne kıvılcımla devrilir, üstünden "
                                "atlarlar · bulut evlere çarpıp kameraya ilerler")             # pasif (v5)
HIT_KOPYA_KUL_SURUM_V4 = "v4"                                                                  # pasif (v4)
HIT_KOPYA_KUL_VERSION_LINE_V4 = "Sürüm: hit_kul v4 (hit prompt'u birebir, yalnız coğrafya değişir)"   # pasif (v4)
HIT_KOPYA_KUL_CAMERA_V4 = "hit kamerası (tepe terası, volkan üst üçte birde), birebir"         # pasif (v4)
HIT_KOPYA_KUL_CAMERA_AXIS_V4 = "hit kamerası (tepe terası, volkan üst üçte birde), birebir"    # pasif (v4)
HIT_KOPYA_KUL_EVENTS_LINE_V4 = ("Olaylar: hit ile birebir (ağaçlar ve direkler devrilir, bulut eve "
                                "çarpar)")                                                     # pasif (v4)
HIT_KOPYA_KUL_SURUM_V3 = "v3"                                                                  # pasif (v3)
HIT_KOPYA_KUL_VERSION_LINE_V3 = ("Sürüm: hit_kul v3 (volkan ufukta, kamera dik aşağı bakar, geniş bulut duvarı, hep "
                                 "direk)")                                                     # pasif (v3)
HIT_KOPYA_KUL_CAMERA_V3 = "sabit yüksek yamaç terası, köye dik aşağı bakar, volkan uzakta ufukta"   # pasif (v3)
HIT_KOPYA_KUL_CAMERA_AXIS_V3 = "sabit yüksek yamaç terası, köye dik aşağı bakar, volkan uzakta ufukta"   # pasif (v3)
HIT_KOPYA_KUL_SURUM_V2 = "v2"                                                                  # pasif (v2)
HIT_KOPYA_KUL_VERSION_LINE_V2 = "Sürüm: hit_kul v2 (yüksek yamaç kamerası, bulut ilk karede, lav arka planda)"   # pasif
HIT_KOPYA_KUL_CAMERA_V2 = "sabit yüksek yamaç terası, köy aşağıda serili, volkan üst üçte birde"   # pasif (v2)
HIT_KOPYA_KUL_CAMERA_AXIS_V2 = "sabit yüksek yamaç terası, köy aşağıda serili, volkan üst üçte birde"   # pasif (v2)
HIT_KOPYA_KUL_SURUM_V1 = "v1"                                                                  # pasif (v1)
HIT_KOPYA_KUL_VERSION_LINE_V1 = "Sürüm: hit_kul v1"                                            # pasif (v1)
HIT_KOPYA_KUL_CAMERA_V1 = "sabit tepe terası, volkan üst üçte birde (hit ile aynı)"            # pasif (v1)
HIT_KOPYA_KUL_CAMERA_AXIS_V1 = "sabit tepe terası, volkan üst üçte birde"                      # pasif (v1)
HIT_KOPYA_KUL_SPOT = "hillside terrace above the village"                          # combo kamera yeri
HIT_KOPYA_KUL_SPOT_LABEL = "Hillside terrace above the village street (hit kopyası v8, hit kamerası)"
HIT_KOPYA_KUL_SPOT_LABEL_V7 = "Hillside terrace above the village street (hit kopyası v7, hit kamerası)"   # pasif
HIT_KOPYA_KUL_SPOT_LABEL_V6 = "Terrace of a hillside house just above the village street (hit kopyası v6)"   # pasif
HIT_KOPYA_KUL_SPOT_LABEL_V5 = "Top-floor balcony of a tall hillside house above the village (hit kopyası v5)"   # pasif
HIT_KOPYA_KUL_SPOT_LABEL_V4 = "Hillside terrace above the village street (hit kopyası)"   # pasif (v4)
HIT_KOPYA_KUL_SOURCE = "Kaynak: 13 Eki hit kamerası/stili birebir + v7 kasaba tarifi + v8 aksiyon"
HIT_KOPYA_KUL_SOURCE_V7 = "Kaynak: 13 Eki hit prompt'u birebir; yalnız köy yapısı ifadesi eklendi (v7)"   # pasif (v7)
HIT_KOPYA_KUL_SOURCE_V6 = "Kaynak: 13 Eki hit'inin geometrisi + cümleleri (v6)"   # pasif (v6)
HIT_KOPYA_KUL_SOURCE_V5 = "Kaynak: 13 Eki hit'inin cümleleri + v5 kamera/konum düzeltmeleri"   # pasif (v5)
HIT_KOPYA_KUL_SOURCE_V4 = ('Kaynak: 13 Eki 11:23 üretimi "Pyroclastic Cloud Engulfs Village Street" (13 Eki paylaşımı, '
                           '2,1M), iskelet ve dil')   # pasif (v4)
HIT_KOPYA_KUL_MAX_WORDS = 230
HIT_KOPYA_KUL_MAX_CHARS = 1400
HIT_KOPYA_KUL_GEO_BLOCK = 2      # yalnız 🎲 Rastgele'de; menüden seçilen coğrafya aynen
HIT_KOPYA_KUL_MID_BLOCK_V3 = 1      # pasif (v3; v4'te M ekseni yok)
HIT_KOPYA_KUL_FINAL_BLOCK_V3 = 1    # pasif (v3; v4'te F ekseni yok)
HIT_KOPYA_KUL_PEOPLE_BLOCK_V3 = 1   # pasif (v3; v4'te kişi ekseni yok)
HIT_KOPYA_KUL_PEOPLE_COUNT_V3 = {"Six": 6, "Seven": 7, "Eight": 8}   # pasif (v3 kişi ekseni)
HIT_KOPYA_KUL_GEO_BUTTONS = {"V1": "🇮🇹 İtalya", "V2": "🇮🇩 Endonezya", "V3": "🇯🇵 Japonya", "V4": "🇨🇱 Şili",
                             "V5": "🇬🇹 Guatemala", "V6": "🇵🇭 Filipinler"}
# v7 (24 Kas): bu modda aktif coğrafyalar (seyrek kasaba yapısına uyan dört ülke); V1 İtalya ve V3 Japonya pasif
# (menüde yok, rastgele yolunda seçilmez; metinleri HIT_KOPYA_KUL_HOUSES'ta duruyor, pasif sürümler kullanır)
HIT_KOPYA_KUL_ACTIVE_GEOS = ("V2", "V4", "V5", "V6")
HIT_KOPYA_KUL_PASSIVE_GEOS = ("V1", "V3")
# v5 (24 Kas): {houses}, YALNIZ ev tipi (bu moda özel, "hillside" yok; Bahadır'ın talimatından birebir)
HIT_KOPYA_KUL_HOUSES = {
    "V1": "low stone houses with terracotta roofs",
    "V2": "low tin-roofed houses among palm trees",
    "V3": "low tiled-roof wooden houses",
    "V4": "low colorful wooden houses",
    "V5": "low pastel houses with tin roofs",
    "V6": "low concrete houses with tin roofs",
}
# v8 (25 Kas): {vehicles}, yol kenarındaki park halindeki araçlar (yalnız aktif dört; Bahadır'ın talimatından birebir)
HIT_KOPYA_KUL_VEHICLES = {
    "V2": "motorbikes and small pickups",
    "V4": "old pickups and small hatchbacks",
    "V5": "old pickups and a painted school bus",
    "V6": "jeepneys and motorcycle tricycles",
}
# v2-v4 (24 Kas): bu moda özel yer metinleri, pasif (v5'te {houses}); Yaklaşma V1-V6 metinleri değişmez
HIT_KOPYA_KUL_PLACES_V4 = {
    "V1": "a hillside village of low stone houses with terracotta roofs",
    "V2": "a hillside village of low tin-roofed houses among palm trees",
    "V3": "a hillside village of low tiled-roof wooden houses",
    "V4": "a hillside village of low colorful wooden houses",
    "V5": "a hillside village of low pastel houses with tin roofs",
    "V6": "a hillside village of low concrete houses with tin roofs",
}
# v1 yer metinleri (kül bulutu Yaklaşma V1-V6 "place" metninin 24 Kas kopyası), pasif
HIT_KOPYA_KUL_PLACES_V1 = {
    "V1": "a village of stone houses with terracotta roofs",
    "V2": "a village of tin-roofed houses among palm trees",
    "V3": "a town of tiled-roof Japanese houses",
    "V4": "a town of colorful wooden houses",
    "V5": "a town of pastel colonial houses",
    "V6": "a town of concrete houses with tin roofs",
}
# 13 Eki 11:23 hit prompt'u, kelimesi kelimesine (Bahadır'ın talimatından; "volcano’s" içindeki kesme işareti ’)
HIT_KOPYA_KUL_HIT_PROMPT = (
    "0-4s: A pyroclastic cloud races down the volcano’s flank and slams into a village street. Four villagers, caught "
    "in the chaos, immediately dart away, their figures barely visible against the ashen background. 4-9s: The deadly "
    "cloud crashes through, snapping street trees like twigs and toppling power poles, striking the ground with "
    "force. 9-15s: The cloud's fury intensifies, slamming into a house, its walls crumbling under pressure, debris "
    "swirling amid the advancing ash. Handheld footage shot by a person standing on a hillside terrace above the "
    "village, high vantage looking down over the village street toward the erupting volcano; slight hand shake, the "
    "camera stays fixed on the terrace, tilting down no more than slightly and never descending, the erupting volcano "
    "always visible in the upper third of the frame, a corner of the terrace railing in the foreground; one "
    "continuous shot, no zoom, no cuts. Bystanders wear civilian clothes, no hi-vis PPE; responders wear service "
    "uniforms. Raw natural light matching the weather, never glossy or CGI; no hazmat suits. No readable signs, text "
    "or flags.")
HIT_KOPYA_KUL_HIT_PHRASE = "slams into a village street"          # hit'te değişen tek ifade
HIT_KOPYA_KUL_PLACE_PHRASE = "slams into the street of {place}"   # v4'teki karşılığı (pasif)
# v7'deki karşılığı (Bahadır'ın v7 metninden birebir; köy yapısı ifadesi), pasif (v8 şablonunda aynen + araçlar)
HIT_KOPYA_KUL_TOWN_PHRASE_V7 = ("slams into the far end of the wide main road of a small town of {houses}, spread out "
                                "with yards and trees between them, with an open stretch of road between the camera "
                                "and the first houses")
# v8 (25 Kas): Bahadır'ın v8 metni, süslü parantez dışı birebir ("volcano’s flank" içinde ’, "volcano's visible cone"
# içinde düz kesme işareti). Stil eki = hit stil eki (v7 ile bayt bayt aynı)
HIT_KOPYA_KUL = {
    "template": (
        "0-4s: A pyroclastic cloud races down the volcano’s flank and slams into the far end of the wide main road of "
        "a small town of {houses}, spread out with yards and trees between them, {vehicles} parked along the "
        "roadside, with an open stretch of road between the camera and the first houses. Glowing lava streaks down "
        "the volcano's visible cone. People watch from the rooftops while four villagers sprint up the road toward "
        "the camera. 4-9s: One falls; right in front of him a power pole crashes across the road in sparks, and he "
        "scrambles up and runs on. 9-15s: The cloud sweeps the parked vehicles along and slams into a house. Handheld "
        "footage shot by a person standing on a hillside terrace above the village, high vantage looking down over "
        "the village street toward the erupting volcano; slight hand shake, the camera stays fixed on the terrace, "
        "tilting down no more than slightly and never descending, the erupting volcano always visible in the upper "
        "third of the frame, a corner of the terrace railing in the foreground; one continuous shot, no zoom, no "
        "cuts. Bystanders wear civilian clothes, no hi-vis PPE; responders wear service uniforms. Raw natural light "
        "matching the weather, never glossy or CGI; no hazmat suits. No readable signs, text or flags."),
    "tail_start": "Handheld footage shot by a person standing on a hillside terrace",
}
# v8 Kie öncesi denetim: her çıktıda birebir geçmesi gerekenler / hiçbir çıktıda geçmemesi gerekenler (küçük harf)
HIT_KOPYA_KUL_REQUIRED = ("People watch from the rooftops", "toward the camera", "right in front of him a power pole",
                          "parked along the roadside", "visible cone", "sweeps the parked vehicles")
HIT_KOPYA_KUL_FORBIDDEN = ("dart away", "toppling power poles", "debris swirling in the ash")
# v7 (24 Kas): 13 Eki hit prompt'u, tek değişiklik HIT_KOPYA_KUL_HIT_PHRASE → HIT_KOPYA_KUL_TOWN_PHRASE_V7; pasif (v8)
HIT_KOPYA_KUL_V7 = {
    "template": HIT_KOPYA_KUL_HIT_PROMPT.replace(HIT_KOPYA_KUL_HIT_PHRASE, HIT_KOPYA_KUL_TOWN_PHRASE_V7),
    "tail_start": "Handheld footage shot by a person standing on a hillside terrace",
}
# v6 (24 Kas): Bahadır'ın v6 metni, süslü parantez dışı birebir ({houses} = v5 ev metinleri aynen); pasif (v7)
HIT_KOPYA_KUL_V6 = {
    "template": (
        "0-4s: A single huge wall of pyroclastic cloud, as wide as the whole valley, races down the flank of the "
        "volcano and slams into the far end of the village street, a village of {houses}. Four villagers sprint up "
        "the street toward the camera at full speed. 4-9s: One man trips and falls on the road; right in front of him "
        "a power pole snaps and crashes across the street in a burst of sparks, and he scrambles up and keeps "
        "running. 9-15s: The cloud rolls up the street toward the camera, swallowing the houses one by one, debris "
        "swirling amid the advancing ash, until it engulfs the terrace in thick brown ash. Handheld footage filmed "
        "from the terrace of a house on the hillside just above the village; the village street runs straight "
        "downhill away from the camera toward the erupting volcano, which stands in the center of the frame directly "
        "behind the far end of the street; high vantage looking down over the rooftops; slight hand shake, the "
        "camera stays fixed and never pans, turns or descends; a corner of the terrace railing in the foreground; "
        "one continuous shot, no zoom, no cuts. Bystanders wear civilian clothes, no hi-vis PPE. Raw natural light "
        "under an ash-grey sky, never glossy or CGI; no hazmat suits. No readable signs, text or flags."),
    "tail_start": "Handheld footage filmed from the terrace",
}
# v6 Kie öncesi denetim: her çıktıda birebir geçmesi gerekenler / hiçbir çıktıda geçmemesi gerekenler (küçük harf);
# pasif (v7: hit prompt'u birebir, kelime listesi yok)
HIT_KOPYA_KUL_REQUIRED_V6 = ("runs straight downhill away from the camera toward the erupting volcano",
                          "stands in the center of the frame directly behind the far end of the street",
                          "single huge wall of pyroclastic cloud", "One man trips and falls",
                          "right in front of him a power pole", "never pans, turns or descends", "ash-grey sky")
HIT_KOPYA_KUL_FORBIDDEN_V6 = ("matching the weather", "top-floor balcony", "jump over it", "flat ground in the valley",
                           "hillside village", "dart away")
# v5 (24 Kas): Bahadır'ın v5 metni, süslü parantez dışı birebir; pasif (v6)
HIT_KOPYA_KUL_V5 = {
    "template": (
        "0-4s: A huge pyroclastic cloud races down the flank of the volcano behind the village and slams into the far "
        "end of the village street, a village of {houses} spread out on flat ground in the valley far below the "
        "camera. Four villagers sprint up the street toward the camera at full speed, never stopping or looking back. "
        "4-9s: The deadly cloud crashes through, snapping street trees like twigs; a power pole right in front of the "
        "running villagers, between them and the camera, snaps and falls across the road in a burst of sparks, and "
        "they jump over it and keep running. 9-15s: The cloud's fury intensifies, slamming into the houses below and "
        "rolling on toward the camera, debris swirling amid the advancing ash. Handheld footage shot from the "
        "top-floor balcony of a tall house high up on a steep hillside, far above the village; wide-angle view "
        "looking steeply down over the whole village and its street toward the erupting volcano; the rooftops look "
        "small far below; slight hand shake, the camera stays fixed, never pans, turns or descends; a corner of the "
        "balcony railing in the foreground; one continuous shot, no zoom, no cuts. Bystanders wear civilian clothes, "
        "no hi-vis PPE. Raw natural light matching the weather, never glossy or CGI; no hazmat suits. No readable "
        "signs, text or flags."),
    "tail_start": "Handheld footage shot from the top-floor balcony",
}
# v4 (24 Kas): hit prompt'u, tek değişiklik HIT_KOPYA_KUL_HIT_PHRASE → HIT_KOPYA_KUL_PLACE_PHRASE; pasif (v5)
HIT_KOPYA_KUL_V4 = {
    "template": HIT_KOPYA_KUL_HIT_PROMPT.replace(HIT_KOPYA_KUL_HIT_PHRASE, HIT_KOPYA_KUL_PLACE_PHRASE),
    "tail_start": "Handheld footage shot by a person standing on a hillside terrace",
}
# v5 Kie öncesi denetim listeleri, pasif (v6)
HIT_KOPYA_KUL_REQUIRED_V5 = ("top-floor balcony of a tall house high up on a steep hillside",
                             "wide-angle view looking steeply down", "the rooftops look small far below",
                             "between them and the camera", "never stopping or looking back",
                             "never pans, turns or descends", "spread out on flat ground in the valley")
HIT_KOPYA_KUL_FORBIDDEN_V5 = ("hillside village", "dart away", "upper third", "tilting down no more than slightly",
                              "village street toward the erupting volcano; slight")   # sonuncusu v4 kamera cümlesi
# v3 (24 Kas) şablon, M1-M2, F1-F2, kişi: pasif (v4 ile hit prompt'una dönüldü)
HIT_KOPYA_KUL_V3 = {
    "people": ("Six", "Seven", "Eight"),
    "mids": {
        "M1": "One man trips and falls; right in front of him the cloud snaps a power pole and it crashes across the "
              "road in a burst of sparks, and he scrambles up and runs on.",
        "M2": "Far down the street a whole row of power poles snaps one after another in bursts of sparks and crashes "
              "across the road just in front of the running people; one man falls, scrambles up and runs on.",
    },
    "finals": {
        "F1": "The cloud rolls up the village toward the terrace, swallows the houses just below and engulfs the "
              "terrace in thick brown ash.",
        "F2": "The cloud tears the roof tiles off the houses just below the terrace and hurls them toward the camera, "
              "then engulfs the terrace in thick brown ash.",
    },
    # Bahadır'ın v3 metni, süslü parantez dışı birebir (24 Kas)
    "template": (
        "0-4s: From the very first frame a wide wall of pyroclastic cloud, as wide as the whole mountainside, rolls "
        "down a distant volcano on the horizon, glowing lava streaking down its slopes behind it, and slams into the "
        "far end of {place} far below. {People} people, small in the distance, run up the village street toward the "
        "camera. 4-9s: {M} 9-15s: {F} Handheld footage shot from a terrace high on a steep hillside, far above the "
        "rooftops, looking steeply down at the whole village spread out small far below, with the distant erupting "
        "volcano on the horizon; slight hand shake, the camera stays fixed on the terrace and never descends, a "
        "corner of the terrace railing in the foreground; one continuous shot, no zoom, no cuts. Bystanders wear "
        "civilian clothes, no hazmat suits. Raw natural light under an ash-grey sky, never glossy or CGI. No readable "
        "signs, text or flags."),
    "tail_start": "Handheld footage shot from a terrace high on a steep hillside",
}
# v8 stil eki (= v7 = 13 Eki hit stil eki, birebir); Kie öncesi denetim
HIT_KOPYA_KUL_TAIL = HIT_KOPYA_KUL["template"][HIT_KOPYA_KUL["template"].index(HIT_KOPYA_KUL["tail_start"]):]
# v7 stil eki, pasif (v8 ile aynı)
HIT_KOPYA_KUL_TAIL_V7 = HIT_KOPYA_KUL_V7["template"][HIT_KOPYA_KUL_V7["template"].index(
    HIT_KOPYA_KUL_V7["tail_start"]):]
# v6 stil eki, pasif
HIT_KOPYA_KUL_TAIL_V6 = HIT_KOPYA_KUL_V6["template"][HIT_KOPYA_KUL_V6["template"].index(
    HIT_KOPYA_KUL_V6["tail_start"]):]
# v5 stil eki, pasif
HIT_KOPYA_KUL_TAIL_V5 = HIT_KOPYA_KUL_V5["template"][HIT_KOPYA_KUL_V5["template"].index(
    HIT_KOPYA_KUL_V5["tail_start"]):]
# v4 stil eki (= 13 Eki hit stil eki, birebir), pasif
HIT_KOPYA_KUL_TAIL_V4 = HIT_KOPYA_KUL_V4["template"][HIT_KOPYA_KUL_V4["template"].index(
    HIT_KOPYA_KUL_V4["tail_start"]):]
HIT_KOPYA_KUL_TAIL_V3 = HIT_KOPYA_KUL_V3["template"][HIT_KOPYA_KUL_V3["template"].index(
    HIT_KOPYA_KUL_V3["tail_start"]):]   # pasif (v3)
# v2 (24 Kas) şablon ve M1-M2: pasif (v3 ile değişti; F1-F2 v3'te aynen)
HIT_KOPYA_KUL_V2 = {
    "people": ("Six", "Seven", "Eight"),
    "mids": {
        "M1": "One man trips and falls; right in front of him the cloud snaps a power pole and it crashes across the "
              "road in a burst of sparks, and he scrambles up and runs on.",
        "M2": "One man trips and falls; right in front of him the cloud snaps a large tree and it crashes across the "
              "road, and he scrambles up and runs on.",
    },
    "finals": {
        "F1": "The cloud rolls up the village toward the terrace, swallows the houses just below and engulfs the "
              "terrace in thick brown ash.",
        "F2": "The cloud tears the roof tiles off the houses just below the terrace and hurls them toward the camera, "
              "then engulfs the terrace in thick brown ash.",
    },
    # Bahadır'ın v2 metni (pasif), süslü parantez dışı birebir (24 Kas)
    "template": (
        "0-4s: From the very first frame a single huge pyroclastic cloud races down the flank of the volcano, glowing "
        "lava pouring down the slope behind it, and slams into the far end of {place} far below. {People} people, "
        "small in the distance, run up the village street toward the camera. 4-9s: {M} 9-15s: {F} Handheld footage "
        "shot from a terrace high on a steep hillside, far above the rooftops, the whole village spread out below, "
        "looking down over the village street toward the erupting volcano; slight hand shake, the camera stays fixed "
        "on the terrace, tilting down no more than slightly and never descending, the erupting volcano always visible "
        "in the upper third of the frame, a corner of the terrace railing in the foreground; one continuous shot, no "
        "zoom, no cuts. Bystanders wear civilian clothes, no hazmat suits. Raw natural light under an ash-grey sky, "
        "never glossy or CGI. No readable signs, text or flags."),
    "tail_start": "Handheld footage shot from a terrace high on a steep hillside",
}
HIT_KOPYA_KUL_TAIL_V2 = HIT_KOPYA_KUL_V2["template"][HIT_KOPYA_KUL_V2["template"].index(
    HIT_KOPYA_KUL_V2["tail_start"]):]   # pasif (v2)
# v1 (24 Kas) şablon, M, F: pasif (v2 ile değişti)
HIT_KOPYA_KUL_V1 = {
    "people": ("Six", "Seven", "Eight"),
    "mids": {
        "M1": "One man trips and falls on the road; right in front of him the cloud snaps a power pole and it crashes "
              "across the street in a burst of sparks, and he scrambles up and keeps running.",
        "M2": "One man trips and falls on the road; right in front of him the cloud snaps a large tree and it crashes "
              "across the street, and he scrambles up and keeps running.",
    },
    "finals": {
        "F1": "The cloud rolls up the street, swallows the houses below the terrace and engulfs the camera in darkness.",
        "F2": "Right below the terrace the cloud tears the roof tiles off the nearest house and hurls them toward the "
              "camera, then engulfs the camera in darkness.",
    },
    # Bahadır'ın metni, süslü parantez dışı birebir (24 Kas: "the volcano above {place} erupts")
    "template": (
        "0-4s: From the very first frame the volcano above {place} erupts, fountains of glowing lava spurting from its "
        "crater, and a single huge pyroclastic cloud races down its flank and slams into the far end of the village "
        "street. {People} people run desperately up the street toward the camera. 4-9s: {M} 9-15s: {F} Handheld "
        "footage shot by a person standing on a hillside terrace above the village, high vantage looking down over the "
        "village street toward the erupting volcano; slight hand shake, the camera stays fixed on the terrace, tilting "
        "down no more than slightly and never descending, the erupting volcano always visible in the upper third of "
        "the frame, a corner of the terrace railing in the foreground; one continuous shot, no zoom, no cuts. "
        "Bystanders wear civilian clothes, no hi-vis PPE; responders wear service uniforms. Raw natural light under an "
        "ash-grey sky, never glossy or CGI; no hazmat suits. No readable signs, text or flags."),
    "tail_start": "Handheld footage shot by a person standing on a hillside terrace",
}
# 13 Eki hit'inin stil eki, birebir (karşılaştırma için; tek fark ışık cümlesi)
HIT_KOPYA_KUL_HIT_TAIL = (
    "Handheld footage shot by a person standing on a hillside terrace above the village, high vantage looking down "
    "over the village street toward the erupting volcano; slight hand shake, the camera stays fixed on the terrace, "
    "tilting down no more than slightly and never descending, the erupting volcano always visible in the upper third "
    "of the frame, a corner of the terrace railing in the foreground; one continuous shot, no zoom, no cuts. "
    "Bystanders wear civilian clothes, no hi-vis PPE; responders wear service uniforms. Raw natural light matching "
    "the weather, never glossy or CGI; no hazmat suits. No readable signs, text or flags.")
HIT_KOPYA_KUL_HIT_LIGHT = "Raw natural light matching the weather,"
HIT_KOPYA_KUL_LIGHT = "Raw natural light under an ash-grey sky,"
HIT_KOPYA_KUL_REQUIRED_V3 = ("wide wall of pyroclastic cloud", "distant volcano on the horizon", "looking steeply down",
                             "power pole", "high on a steep hillside, far above the rooftops",
                             "the camera stays fixed on the terrace")   # pasif (v3)
HIT_KOPYA_KUL_FORBIDDEN_V3 = ("bus", "explosion", "blast", "collapse", "sunset", "GPT", "colonial", "darkness",
                              "erupts", "upper third", "tilting down no more than slightly", "tree",
                              "single huge")   # pasif (v3; v4'te kelime yasağı yok, hit karşılaştırması var)
# v3 yasak denetiminden önce çıkarılan sabit ifadeler (24 Kas v3 kararı: V2 "among palm trees"), pasif
HIT_KOPYA_KUL_FORBIDDEN_EXCEPTIONS_V3 = ("palm trees",)
HIT_KOPYA_KUL_REQUIRED_V2 = ("single huge pyroclastic cloud", "glowing lava pouring down the slope",
                             "high on a steep hillside, far above the rooftops",
                             "the camera stays fixed on the terrace",
                             "the erupting volcano always visible in the upper third of the frame")   # pasif (v2)
HIT_KOPYA_KUL_FORBIDDEN_V2 = ("bus", "explosion", "blast", "collapse", "sunset", "GPT", "colonial", "darkness",
                              "erupts")   # pasif (v2)
HIT_KOPYA_KUL_REQUIRED_V1 = ("fountains of glowing lava", "single huge pyroclastic cloud",
                             "the camera stays fixed on the terrace",
                             "the erupting volcano always visible in the upper third of the frame")   # pasif (v1)
HIT_KOPYA_KUL_FORBIDDEN_V1 = ("bus", "explosion", "blast", "collapse", "sunset", "GPT")   # pasif (v1)
HIT_KOPYA_KUL_NAMES_V3 = {"M1": "adam düşer, önüne elektrik direği kıvılcımlarla yola devrilir",
                          "M2": "caddede bir sıra direk peş peşe kıvılcımlarla yola devrilir, bir adam düşer",
                          "F1": "bulut köyü terasa doğru tırmanır, terası kalın kahverengi küle gömer",
                          "F2": "terasın altındaki evlerin kiremitleri kameraya savrulur, teras kalın kahverengi "
                                "külde"}   # pasif (v3)
HIT_KOPYA_KUL_NAMES_V2 = {"M1": "adam düşer, elektrik direği kıvılcımlarla yola devrilir",
                          "M2": "adam düşer, büyük ağaç yola devrilir",
                          "F1": "bulut köyü terasa doğru tırmanır, terası kalın kahverengi küle gömer",
                          "F2": "terasın altındaki evlerin kiremitleri kameraya savrulur, teras kalın kahverengi külde"}
HIT_KOPYA_KUL_NAMES_V1 = {"M1": "adam düşer, elektrik direği kıvılcımlarla devrilir",
                       "M2": "adam düşer, büyük ağaç devrilir",
                       "F1": "bulut caddeyi ve evleri yutar, kamera karanlıkta",
                       "F2": "en yakın evin kiremitleri kameraya savrulur, kamera karanlıkta"}
HIT_KOPYA_KUL_WARNING = ("⚠️ Hit karşılaştırması (v8): volkanın konisi ve lavı görünüyor mu, çatılarda izleyen insanlar "
                         "var mı, köylüler kameraya mı koşuyor (volkana değil), düşen adamın tam önüne direk devriliyor "
                         "mu, yol kenarında araçlar var mı ve bulut onları sürüklüyor mu, kamera açısı v7'deki gibi mi?")
HIT_KOPYA_KUL_WARNING_V7 = ("⚠️ Hit karşılaştırması (v7): volkan büyük ve üst üçte birde mi, yol geniş ve evler seyrek "
                            "mi, kamera ile evler arasında açık alan var mı, bulut tek duvar mı, kamera dönmüyor "
                            "mu?")   # pasif (v7)
HIT_KOPYA_KUL_WARNING_V6 = ("⚠️ Hit karşılaştırması (v6): volkan karenin ortasında mı, cadde kameradan volkana dümdüz "
                         "uzanıyor mu, bulut tek geniş duvar mı (iki katman değil), adam düşüyor ve direk tam önüne mi "
                         "devriliyor, kamera dönmüyor mu, gökyüzü kül grisi mi (güneşli değil)?")   # pasif (v6)
HIT_KOPYA_KUL_WARNING_V5 = ("⚠️ Hit karşılaştırması (v5): kamera yüksekte ve geniş açı mı, çatılar aşağıda küçük mü, "
                         "direk koşanların önünde mi (kamera ile aralarında), insanlar durmadan ve geriye bakmadan "
                         "kameraya mı koşuyor, kamera dönmüyor ve aşağı inmiyor mu?")   # pasif (v5)
HIT_KOPYA_KUL_WARNING_V4 = ("⚠️ Hit karşılaştırması: prompt 13 Eki hit'iyle birebir (yalnız coğrafya farklı). Video "
                            "hit'e benziyor mu: bulut yamaçtan inip köy caddesine çarpıyor mu, dört köylü kaçıyor mu, "
                            "ağaçlar ve direkler devriliyor mu, bulut bir eve çarpıyor mu, kamera tepe terasında sabit "
                            "ve volkan üst üçte birde mi?")   # pasif (v4)
HIT_KOPYA_KUL_WARNING_V3 = ("⚠️ Hit karşılaştırması: volkan uzakta ufukta mı (yakın ve devasa değil), kamera köye dik "
                            "aşağı bakıyor ve yamaç terasında sabit mi (çatı hizasına inmiyor), bulut tüm yamaç "
                            "genişliğinde duvar gibi mi (dar sütun değil), direk kıvılcımlarla yola devriliyor mu, "
                            "insanlar uzakta küçük mü, final kahverengi kül mü (simsiyah değil)?")   # pasif (v3)
HIT_KOPYA_KUL_WARNING_V2 = ("⚠️ Hit karşılaştırması: bulut ilk karede yamaçtan iniyor mu, lav arkasında akıyor mu, kamera "
                            "köyün çok üstünde yüksek yamaç terasında sabit mi, insanlar uzakta küçük mü, volkan üst "
                            "üçte birde mi, final kahverengi kül mü (simsiyah değil)?")   # pasif (v2)
HIT_KOPYA_KUL_WARNING_V1 = ("⚠️ Hit karşılaştırması: ilk karede volkan patlıyor ve lav fışkırıyor mu, tek büyük bulut "
                         "köy caddesinin ucuna çarpıyor mu, insanlar kameraya doğru koşuyor mu, kamera terasta sabit "
                         "ve volkan üst üçte birde mi?")
HIT_KOPYA_KUL_CONFIRM_DESC = ("13 Eki kül bulutu hit'inin (2,1M) kamerası ve stili birebir, v8: kasaba v7'deki gibi "
                              "(seyrek evli küçük kasaba, geniş ana yol, kamera ile ilk evler arasında açık yol), yol "
                              "kenarında coğrafyaya uygun park halinde araçlar. Kül bulutu volkanın yamacından iner ve "
                              "yolun uzak ucuna çarpar, volkanın konisinden parlayan lav akar; çatılarda insanlar "
                              "izler, dört köylü yoldan kameraya koşar. Biri düşer, tam önüne bir elektrik direği "
                              "kıvılcımla devrilir, kalkıp koşmaya devam eder. Bulut park halindeki araçları sürükler "
                              "ve bir eve çarpar. Kamera: tepe terası, volkan üst üçte birde, korkuluk köşesi ön "
                              "planda. Coğrafya (Endonezya, Şili, Guatemala, Filipinler) ve araçlar ✋ Onay "
                              "mesajında. Hikâye için GPT çağrılmaz.")
HIT_KOPYA_KUL_CONFIRM_DESC_V7 = ("13 Eki kül bulutu hit'inin (2,1M) prompt'u, v7: kelimesi kelimesine aynı, tek fark "
                                 "ilk cümlede köy caddesi yerine seyrek evli küçük bir kasabanın geniş ana yolu (evler "
                                 "arasında bahçe ve ağaçlar, kamera ile ilk evler arasında açık yol). Kül bulutu "
                                 "volkanın yamacından iner ve yolun uzak ucuna çarpar, dört köylü kaçar; ağaçlar ve "
                                 "elektrik direkleri devrilir; bulut bir eve çarpar, duvarları çöker. Hit kamerası "
                                 "birebir: tepe terası, volkan üst üçte birde, korkuluk köşesi ön planda. Coğrafya "
                                 "(Endonezya, Şili, Guatemala, Filipinler) ✋ Onay mesajında. Hikâye için GPT çağrılmaz.")   # pasif (v7)
HIT_KOPYA_KUL_CONFIRM_DESC_V6 = ("13 Eki kül bulutu hit'inin (2,1M) geometrisi ve cümleleri, v6. Vadi genişliğinde tek "
                              "büyük kül bulutu duvarı volkanın yamacından iner ve köy caddesinin uzak ucuna çarpar; "
                              "dört köylü caddeden kameraya koşar. Bir adam düşer, tam önüne bir elektrik direği "
                              "kıvılcımla devrilir, kalkıp koşmaya devam eder. Bulut caddeden kameraya tırmanır, evleri "
                              "tek tek yutar ve terası kalın kahverengi küle gömer. Kamera: köyün hemen üstündeki "
                              "yamaçta bir evin terası, cadde kameradan volkana dümdüz uzanır, volkan karenin "
                              "ortasında caddenin bittiği yerin arkasında, dönmez ve inmez, teras korkuluğu köşesi ön "
                              "planda. Kül grisi gökyüzü. Coğrafya ✋ Onay mesajında. Hikâye için GPT "
                              "çağrılmaz.")   # pasif (v6)
HIT_KOPYA_KUL_CONFIRM_DESC_V5 = ("13 Eki kül bulutu hit'inin (2,1M) cümleleri, v5: kamera ve konumlar açıkça yazıldı. "
                              "Büyük kül bulutu köyün arkasındaki volkanın yamacından iner ve vadide düzlükteki köyün "
                              "caddesinin uzak ucuna çarpar; dört köylü durmadan, geriye bakmadan kameraya koşar. Bulut "
                              "ağaçları kırar; koşanların önünde (kamera ile aralarında) bir elektrik direği "
                              "kıvılcımla yola devrilir, üstünden atlayıp koşmaya devam ederler. Bulut evlere çarpar "
                              "ve kameraya ilerler. Kamera: yamaçtaki uzun evin üst kat balkonu, geniş açı, köye dik "
                              "aşağı bakar, çatılar küçük, dönmez ve inmez, balkon korkuluğu köşesi ön planda. "
                              "Coğrafya ✋ Onay mesajında. Hikâye için GPT çağrılmaz.")   # pasif (v5)
HIT_KOPYA_KUL_CONFIRM_DESC_V4 = ("13 Eki kül bulutu hit'inin (2,1M) prompt'u, v4: kelimesi kelimesine aynı, tek fark "
                                 "ilk cümlede köy caddesi yerine seçilen coğrafyanın caddesi. Kül bulutu volkanın "
                                 "yamacından iner ve caddeye çarpar, dört köylü kaçar; ağaçlar ve elektrik direkleri "
                                 "devrilir; bulut bir eve çarpar, duvarları çöker. Hit kamerası birebir: tepe terası, "
                                 "volkan üst üçte birde, korkuluk köşesi ön planda. Coğrafya ✋ Onay mesajında. Hikâye "
                                 "için GPT çağrılmaz.")   # pasif (v4)
HIT_KOPYA_KUL_CONFIRM_DESC_V3 = ("13 Eki kül bulutu hit'inin (2,1M) iskeleti, v3. İlk karede uzakta ufuktaki volkandan tüm "
                              "yamaç genişliğinde bir kül bulutu duvarı iner, arkasında lav akar, aşağıdaki köyün "
                              "ucuna çarpar; 6-8 kişi uzakta, küçük, köy caddesinde kameraya doğru koşar; önlerine "
                              "elektrik direği ya da bir sıra direk kıvılcımlarla devrilir, bir adam düşüp kalkar "
                              "(M1-M2); bulut terasa tırmanır ve terası kalın kahverengi küle gömer (F1-F2). Köyün çok "
                              "üstündeki yüksek yamaç terasından sabit kamera, köye dik aşağı bakar, korkuluk köşesi ön "
                              "planda. Coğrafya, M, F, kişi ✋ Onay mesajında. Hikâye için GPT çağrılmaz.")
HIT_KOPYA_KUL_CONFIRM_DESC_V2 = ("13 Eki kül bulutu hit'inin (2,1M) iskeleti, v2. İlk karede tek büyük kül bulutu volkanın "
                              "yamacından iner, arkasında lav akar, aşağıdaki köyün ucuna çarpar; 6-8 kişi uzakta, "
                              "küçük, köy caddesinde kameraya doğru koşar; bir adam düşer, önüne direk ya da ağaç "
                              "devrilir (M1-M2); bulut terasa tırmanır ve terası kalın kahverengi küle gömer (F1-F2). "
                              "Köyün çok üstündeki yüksek yamaç terasından sabit kamera, köy aşağıda serili, volkan "
                              "üst üçte birde, korkuluk köşesi ön planda. Coğrafya, M, F, kişi ✋ Onay mesajında. "
                              "Hikâye için GPT çağrılmaz.")   # pasif (v2)
HIT_KOPYA_KUL_CONFIRM_DESC_V1 = ("13 Eki kül bulutu hit'inin (2,1M) iskeleti ve dili. İlk karede volkan patlar, kraterden "
                              "lav fışkırır, tek büyük kül bulutu yamaçtan inip köy caddesinin ucuna çarpar, 6-8 kişi "
                              "kameraya doğru koşar; bir adam düşer, önüne direk ya da ağaç devrilir (M1-M2); bulut "
                              "terasın altına gelir ve kamerayı karanlığa gömer (F1-F2). Tepe terasından sabit "
                              "kamera, volkan üst üçte birde, korkuluk köşesi ön planda. Coğrafya, M, F, kişi ✋ Onay "
                              "mesajında. Hikâye için GPT çağrılmaz.")
_HKK = HIT_KOPYA_KUL
_HKK_V7 = HIT_KOPYA_KUL_V7
_HKK_V6 = HIT_KOPYA_KUL_V6
_HKK_V5 = HIT_KOPYA_KUL_V5
_HKK_V4 = HIT_KOPYA_KUL_V4
_HKK_V3 = HIT_KOPYA_KUL_V3
_HIT_KOPYA_KUL_GEO_MEMORY: list[str] = []
# v3 eksen hafızaları (M, F, kişi): pasif, v4'te kullanılmaz
_HIT_KOPYA_KUL_MID_MEMORY: list[str] = []
_HIT_KOPYA_KUL_FINAL_MEMORY: list[str] = []
_HIT_KOPYA_KUL_PEOPLE_MEMORY: list[str] = []


def hit_kopya_kul_is_active(event: str | None) -> bool:
    return event in HIT_KOPYA_KUL_EVENTS


def hit_kopya_kul_geos() -> list[str]:
    """v7-v8 aktif coğrafyalar (V2, V4, V5, V6): menü, 🎲 Rastgele ve Kie öncesi denetim yalnız bunları kullanır."""
    return list(HIT_KOPYA_KUL_ACTIVE_GEOS)


def hit_kopya_kul_all_geos() -> list[str]:
    """V1-V6 (kül bulutu Yaklaşma moduyla aynı sıra ve kimlikler); pasif sürümler (v1-v6) ve fixture kilitleri için."""
    return list(HIT_KOPYA_KUL_HOUSES)


def hit_kopya_kul_place(geo: str) -> str:
    """v5-v8 {houses}: bu moda özel ev tipi metni (HIT_KOPYA_KUL_HOUSES), aynen."""
    return HIT_KOPYA_KUL_HOUSES[geo]


def hit_kopya_kul_vehicles(geo: str) -> str:
    """v8 {vehicles}: yol kenarındaki park halindeki araçlar (HIT_KOPYA_KUL_VEHICLES), aynen."""
    return HIT_KOPYA_KUL_VEHICLES[geo]


def hit_kopya_kul_place_v4(geo: str) -> str:
    """Pasif (v2-v4): {place} yer metni (HIT_KOPYA_KUL_PLACES_V4), aynen."""
    return HIT_KOPYA_KUL_PLACES_V4[geo]


def hit_kopya_kul_geo_text(geo: str) -> str:
    return f"{geo} {HIT_KOPYA_KUL_GEO_BUTTONS[geo]}"


def _hit_kopya_kul_check(geo: str) -> None:
    """v7-v8: yalnız aktif coğrafyalar (V1 İtalya ve V3 Japonya bu modda pasif)."""
    if geo not in hit_kopya_kul_geos():
        raise es.StructureError(f"{HIT_KOPYA_KUL_MODE_LABEL}: coğrafya bu modda yok ({geo})")


def _hit_kopya_kul_check_all(geo: str) -> None:
    """Pasif sürümler (v1-v6): V1-V6."""
    if geo not in hit_kopya_kul_all_geos():
        raise es.StructureError(f"{HIT_KOPYA_KUL_MODE_LABEL}: coğrafya bu modda yok ({geo})")


def hit_kopya_kul_prompt(geo: str) -> str:
    """v8 prompt = v8 şablonu birebir, yalnız {houses} ve {vehicles} dolar."""
    _hit_kopya_kul_check(geo)
    return _HKK["template"].format(houses=hit_kopya_kul_place(geo), vehicles=hit_kopya_kul_vehicles(geo))


def hit_kopya_kul_prompt_v7(geo: str) -> str:
    """Pasif (v7): 13 Eki hit prompt'u birebir, yalnız köy yapısı ifadesi ({houses} dolar; yalnız aktif dört coğrafya)."""
    _hit_kopya_kul_check(geo)
    return _HKK_V7["template"].format(houses=hit_kopya_kul_place(geo))


def hit_kopya_kul_hit_expected_v7(geo: str) -> str:
    """Pasif (v7): hit prompt'unun kendisinden bağımsız kurulum: tek değişiklik "slams into a village street" → köy
    yapısı ifadesi (HIT_KOPYA_KUL_TOWN_PHRASE_V7, {houses} dolu)."""
    _hit_kopya_kul_check(geo)
    return HIT_KOPYA_KUL_HIT_PROMPT.replace(HIT_KOPYA_KUL_HIT_PHRASE,
                                            HIT_KOPYA_KUL_TOWN_PHRASE_V7.format(houses=hit_kopya_kul_place(geo)))


def hit_kopya_kul_prompt_v6(geo: str) -> str:
    """Pasif (v6): v6 şablonu birebir, yalnız {houses} dolar."""
    _hit_kopya_kul_check_all(geo)
    return _HKK_V6["template"].format(houses=hit_kopya_kul_place(geo))


def hit_kopya_kul_prompt_v5(geo: str) -> str:
    """Pasif (v5): v5 şablonu birebir, yalnız {houses} dolar."""
    _hit_kopya_kul_check_all(geo)
    return _HKK_V5["template"].format(houses=hit_kopya_kul_place(geo))


def hit_kopya_kul_prompt_v4(geo: str) -> str:
    """Pasif (v4): 13 Eki hit prompt'u birebir, yalnız {place} (v4 yer metni) dolar."""
    _hit_kopya_kul_check_all(geo)
    return _HKK_V4["template"].format(place=hit_kopya_kul_place_v4(geo))


def hit_kopya_kul_hit_expected_v4(geo: str) -> str:
    """Pasif (v4): hit prompt'unun kendisinden bağımsız kurulum: tek değişiklik "slams into a village street" →
    "slams into the street of <yer>"."""
    _hit_kopya_kul_check_all(geo)
    return HIT_KOPYA_KUL_HIT_PROMPT.replace(HIT_KOPYA_KUL_HIT_PHRASE,
                                            HIT_KOPYA_KUL_PLACE_PHRASE.format(place=hit_kopya_kul_place_v4(geo)))


def hit_kopya_kul_story(geo: str) -> str:
    """Zaman etiketli hikâye (stil ekinden önceki kısım)."""
    p = hit_kopya_kul_prompt(geo)
    return p[:p.index(" " + _HKK["tail_start"])]


def hit_kopya_kul_tail(geo: str) -> str:
    """Stil eki (v7-v8: 13 Eki hit stil eki birebir; coğrafyadan bağımsız)."""
    p = hit_kopya_kul_prompt(geo)
    return p[p.index(" " + _HKK["tail_start"]) + 1:]


def _hit_kopya_kul_check_v3(geo: str, mid: str, final: str, people: int) -> None:
    """Pasif (v3): coğrafya + M + F + kişi denetimi."""
    if geo not in hit_kopya_kul_all_geos():
        raise es.StructureError(f"{HIT_KOPYA_KUL_MODE_LABEL}: coğrafya bu modda yok ({geo})")
    if mid not in _HKK_V3["mids"]:
        raise es.StructureError(f"{HIT_KOPYA_KUL_MODE_LABEL}: orta M1-M2 değil ({mid})")
    if final not in _HKK_V3["finals"]:
        raise es.StructureError(f"{HIT_KOPYA_KUL_MODE_LABEL}: final F1-F2 değil ({final})")
    if people not in HIT_KOPYA_KUL_PEOPLE_COUNT_V3.values():
        raise es.StructureError(f"{HIT_KOPYA_KUL_MODE_LABEL}: kişi sayısı 6-8 değil ({people})")


def hit_kopya_kul_prompt_v3(geo: str, mid: str, final: str, people: int) -> str:
    """Pasif (v3): v3 şablonu, yer tutucular dolar."""
    _hit_kopya_kul_check_v3(geo, mid, final, people)
    word = next(w for w, k in HIT_KOPYA_KUL_PEOPLE_COUNT_V3.items() if k == people)
    return _HKK_V3["template"].format(place=hit_kopya_kul_place_v4(geo), People=word, M=_HKK_V3["mids"][mid],
                                      F=_HKK_V3["finals"][final])


def hit_kopya_kul_axes_history(records: list | None, key: str) -> list | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye, iptaller dahil) bu modun `key` değerleri; okunamadıysa
    None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") in HIT_KOPYA_KUL_EVENTS
                and axes.get("mod") == HIT_KOPYA_KUL_MOD and axes.get(key) not in (None, "")):
            out.append(axes[key])
    return out


def hit_kopya_kul_lines(tb: dict) -> str:
    """✋ Onay satırları: mod, sürüm, kaynak, coğrafya, olaylar, araçlar, kamera, kelime/karakter, eksenler + tekrar
    önleme, hit karşılaştırması."""
    text = tb["prompt"]
    lines = [
        f"Mod: {HIT_KOPYA_KUL_MODE_LABEL}",
        HIT_KOPYA_KUL_VERSION_LINE,
        HIT_KOPYA_KUL_SOURCE,
        f"Coğrafya: {hit_kopya_kul_geo_text(tb['geo'])} «{hit_kopya_kul_place(tb['geo'])}» ({tb['geo_source']})",
        HIT_KOPYA_KUL_EVENTS_LINE,
        f"Araçlar: {hit_kopya_kul_vehicles(tb['geo'])}",
        f"Kamera: {HIT_KOPYA_KUL_CAMERA}",
        f"Kelime: {len(text.split())} (en fazla {HIT_KOPYA_KUL_MAX_WORDS}) · karakter: {len(text)} "
        f"(en fazla {HIT_KOPYA_KUL_MAX_CHARS})",
    ]
    if tb.get("axes_line"):
        lines.append(tb["axes_line"])
    lines.append(HIT_KOPYA_KUL_WARNING)
    return "\n".join(lines)


def hit_kopya_kul_axes_json(tb: dict, excluded: dict | None = None) -> str:
    """v4-v8: M, F, kişi ekseni yok (None yazılır; v3 kayıtlarındaki değerler geçmişte kalır)."""
    import core.axes_history as ah
    axes = {"spot": None, "view": None, "light": None, "vehicle": None, "people": None, "beats": None,
            "mod": HIT_KOPYA_KUL_MOD, "cografya": tb["geo"], "cografya_kaynak": tb["geo_source"], "m": None,
            "f": None, "kisi": None, "surum": HIT_KOPYA_KUL_SURUM}
    return ah.axes_json(es.PYROCLASTIC, axes, excluded)


def hit_kopya_kul_build_scene(domain: str | None, event: str | None, history: list[str] | None = None,
                              records: list | None = None, rng=None, history_source: str = "bellek",
                              geo: str | None = None) -> dict:
    """⭐ Hit kopyası (kül bulutu) v8 sahnesi: GPT yok, normal hat yok. geo = menüden seçilen V (yalnız V2, V4, V5,
    V6; None = 🎲 Rastgele, dört coğrafya içinde son 2 elenir). records = Notion "Eksenler" ham kayıtları (None = süreç hafızası). structure["hit_kopya_kul"] Kie
    öncesi son denetimin (submit_issues) kaynağıdır."""
    import random
    from core.skeleton_pipeline import SKELETON_CAMERA
    if domain not in (None, HIT_KOPYA_KUL_DOMAIN) or not hit_kopya_kul_is_active(event):
        raise es.StructureError(f"{HIT_KOPYA_KUL_MODE_LABEL} kurulamadı: {domain} / {event}")
    if geo is not None and geo not in hit_kopya_kul_geos():
        raise es.StructureError(f"{HIT_KOPYA_KUL_MODE_LABEL}: coğrafya bu modda yok ({geo})")
    r = rng or random
    h = hit_kopya_kul_axes_history(records, "cografya")
    ids = hit_kopya_kul_geos()
    # v7-v8: geçmişteki pasif coğrafyalar (V1, V3) sayılmaz; son 2 dört aktif coğrafya içinde
    seen = [x for x in (_HIT_KOPYA_KUL_GEO_MEMORY if h is None else h) if x in ids]
    if geo is not None:
        g, excluded = geo, {"cografya": []}
    else:
        g = _block_pick(ids, seen, HIT_KOPYA_KUL_GEO_BLOCK, r)
        excluded = {"cografya": [x for x in ids if x in seen[-HIT_KOPYA_KUL_GEO_BLOCK:]]}
    _HIT_KOPYA_KUL_GEO_MEMORY.append(g)
    del _HIT_KOPYA_KUL_GEO_MEMORY[:-12]
    people = HIT_KOPYA_KUL_PEOPLE
    prompt = hit_kopya_kul_prompt(g)
    story = hit_kopya_kul_story(g)
    tail = hit_kopya_kul_tail(g)
    a, b, c = es.SLICE_LABELS
    opening = story.split(f" {b}: ")[0][len(f"{a}: "):].strip()
    mid_text = story.split(f"{b}: ")[1].split(f" {c}: ")[0]
    final_text = story.split(f"{c}: ")[1]
    plain = " ".join([opening, mid_text, final_text])
    geo_source = "menü" if geo is not None else "rastgele"
    repeat = (f"coğrafya son {HIT_KOPYA_KUL_GEO_BLOCK} (yalnız rastgele) · olaylar, kişi, kamera ve ışık sabit "
              "(v8: hit kamerası/stili birebir)")
    base_trace = {"pipeline": "creative", "structured": True, "domain": HIT_KOPYA_KUL_DOMAIN,
                  "event": es.PYROCLASTIC, "ship": "None", "camera": SKELETON_CAMERA, "view": None,
                  "view_source": None, "place": hit_kopya_kul_place(g), "count_range": [people, people],
                  "people_running": people, "outcome": "-", "recent_count": 0}
    trace, axes_line = mode_display(
        {"trace": base_trace}, {}, mode=HIT_KOPYA_KUL_MODE_LABEL, camera=HIT_KOPYA_KUL_CAMERA,
        opening=opening, mid=("hit", mid_text), final=("hit", final_text), plain=plain,
        spot=HIT_KOPYA_KUL_SPOT_LABEL, weather="matching the weather (hit stil eki, sabit)",
        axes={"sürüm": HIT_KOPYA_KUL_SURUM, "coğrafya": f"{hit_kopya_kul_geo_text(g)} ({geo_source})",
              "olaylar": "v8 aksiyon", "kamera modu": HIT_KOPYA_KUL_CAMERA_AXIS},
        repeat=repeat)
    trace = {**trace, "mode": HIT_KOPYA_KUL_MOD, "surum": HIT_KOPYA_KUL_SURUM, "cografya": g,
             "axes_source": history_source}
    tb = {"event": es.PYROCLASTIC, "geo": g, "geo_source": geo_source, "people": people, "story": story,
          "suffix": tail, "prompt": prompt, "axes_line": axes_line}
    tb["lines"] = hit_kopya_kul_lines(tb)
    axes_json = hit_kopya_kul_axes_json(tb, excluded)
    structure = {HIT_KOPYA_KUL_MOD: tb, "axes_json": axes_json, "axes_line": None,
                 "environment": f"Coğrafya: {hit_kopya_kul_geo_text(g)} · kamera = {HIT_KOPYA_KUL_MODE_LABEL} "
                                "(hit kamerası: hillside terrace above the village, sabit)",
                 "story_source": f"Hikâye: kod (birebir) · {HIT_KOPYA_KUL_MODE_LABEL}", "story_source_kind": "code",
                 "caption_info": {"opening": opening, "people": people, "kadraj": "teras",
                                  "beat_2": donma_caption_beat(mid_text), "beat_3": donma_caption_beat(final_text)},
                 "caption_candidates": None}
    problems = hit_kopya_kul_issues(structure, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{HIT_KOPYA_KUL_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = (f"{HIT_KOPYA_KUL_DOMAIN}|none|{es.PYROCLASTIC.lower()}|{HIT_KOPYA_KUL_SPOT}##HKK:{g}|"
             f"{SKELETON_CAMERA}")
    return {"domain": HIT_KOPYA_KUL_DOMAIN, "event": es.PYROCLASTIC, "ship": None, "spot": HIT_KOPYA_KUL_SPOT,
            "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt, "combo_key": combo,
            "trace": trace, "structure": structure, "axes_json": axes_json}


def hit_kopya_kul_text_issues(text: str) -> list[str]:
    """Kie öncesi son kontrol (v8): metin aktif coğrafyalardan (V2, V4, V5, V6) birinin v8 şablonuyla bayt bayt aynı,
    zorunlu ifadeler var, yasaklı ifadeler yok. İhlal = gönderilmez."""
    text = text or ""
    out = []
    if not any(text == hit_kopya_kul_prompt(g) for g in hit_kopya_kul_geos()):
        out.append("prompt v8 şablonuyla birebir değil (yalnız ev tipi ve araçlar farklı olabilir)")
    for need in HIT_KOPYA_KUL_REQUIRED:
        if need not in text:
            out.append(f'"{need}" eksik')
    low = text.lower()
    for bad in HIT_KOPYA_KUL_FORBIDDEN:
        if bad.lower() in low:
            out.append(f"bu modda olmayan ifade var: {bad}")
    return out


def hit_kopya_kul_text_issues_v7(text: str) -> list[str]:
    """Pasif (v7): Kie öncesi son kontrol (v7): metin, 13 Eki hit prompt'unun aktif coğrafyalardan (V2, V4, V5, V6) birinin ev
    metniyle kurulan hâliyle bayt bayt aynı olmalı ("slams into a village street" → köy yapısı ifadesi dışında fark
    yok). Kelime yasağı yok. İhlal = gönderilmez."""
    text = text or ""
    if any(text == hit_kopya_kul_hit_expected_v7(g) for g in hit_kopya_kul_geos()):
        return []
    return ["prompt 13 Eki hit prompt'uyla birebir değil (yalnız köy yapısı ifadesi farklı olabilir)"]


def hit_kopya_kul_text_issues_v6(text: str) -> list[str]:
    """Pasif (v6): metin v6 şablonuyla bayt bayt aynı, v6 zorunlu ifadeler var, v6 yasaklı ifadeler yok."""
    text = text or ""
    out = []
    if not any(text == hit_kopya_kul_prompt_v6(g) for g in hit_kopya_kul_all_geos()):
        out.append("prompt v6 şablonuyla birebir değil (yalnız ev tipi farklı olabilir)")
    for need in HIT_KOPYA_KUL_REQUIRED_V6:
        if need not in text:
            out.append(f'"{need}" eksik')
    low = text.lower()
    for bad in HIT_KOPYA_KUL_FORBIDDEN_V6:
        if bad.lower() in low:
            out.append(f"bu modda olmayan ifade var: {bad}")
    return out


def hit_kopya_kul_text_issues_v5(text: str) -> list[str]:
    """Pasif (v5): metin v5 şablonuyla bayt bayt aynı, v5 zorunlu ifadeler var, v5 yasaklı ifadeler yok."""
    text = text or ""
    out = []
    if not any(text == hit_kopya_kul_prompt_v5(g) for g in hit_kopya_kul_all_geos()):
        out.append("prompt v5 şablonuyla birebir değil (yalnız ev tipi farklı olabilir)")
    for need in HIT_KOPYA_KUL_REQUIRED_V5:
        if need not in text:
            out.append(f'"{need}" eksik')
    low = text.lower()
    for bad in HIT_KOPYA_KUL_FORBIDDEN_V5:
        if bad.lower() in low:
            out.append(f"bu modda olmayan ifade var: {bad}")
    return out


def hit_kopya_kul_text_issues_v4(text: str) -> list[str]:
    """Pasif (v4): Kie öncesi son kontrol (v4): metin, 13 Eki hit prompt'unun V1-V6'dan birinin yer metniyle kurulan hâliyle
    bayt bayt aynı olmalı ("slams into a village street" → "slams into the street of <yer>" dışında fark yok). Kelime
    yasağı yok. İhlal = gönderilmez."""
    text = text or ""
    if any(text == hit_kopya_kul_hit_expected_v4(g) for g in hit_kopya_kul_all_geos()):
        return []
    return ["prompt 13 Eki hit prompt'uyla birebir değil (yalnız coğrafya ifadesi farklı olabilir)"]


def hit_kopya_kul_text_issues_v3(text: str) -> list[str]:
    """Pasif (v3): zorunlu ifadeler birebir var; yasaklı ifadeler (HIT_KOPYA_KUL_FORBIDDEN_V3) tüm metinde yok
    (büyük/küçük harf fark etmez, kelime başından; HIT_KOPYA_KUL_FORBIDDEN_EXCEPTIONS_V3 önce çıkarılır)."""
    out = []
    text = text or ""
    for need in HIT_KOPYA_KUL_REQUIRED_V3:
        if need not in text:
            out.append(f'"{need}" eksik')
    low = text.lower()
    for ok in HIT_KOPYA_KUL_FORBIDDEN_EXCEPTIONS_V3:
        low = low.replace(ok.lower(), " ")
    import re
    for bad in HIT_KOPYA_KUL_FORBIDDEN_V3:
        # v3: kelime başından eşleşir ("tree"/"trees" yakalanır, şablondaki "street" yakalanmaz)
        if re.search(r"\b" + re.escape(bad.lower()), low):
            out.append(f"bu modda olmayan ifade var: {bad}")
    return out


def hit_kopya_kul_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce (v8): gönderilecek metin, seçilen coğrafyanın v8 şablonundan yeniden kurulanla bayt bayt aynı
    mı, zorunlu/yasak ifadeler tamam mı, stil eki hit stil eki mi, sınırlar içinde mi. Boş = gönder."""
    tb = structure[HIT_KOPYA_KUL_MOD]
    geo = tb.get("geo")
    try:
        _hit_kopya_kul_check(geo)
    except es.StructureError as e:
        return [str(e)]
    prompt, story, tail = hit_kopya_kul_prompt(geo), hit_kopya_kul_story(geo), hit_kopya_kul_tail(geo)
    out = []
    if tb.get("people") != HIT_KOPYA_KUL_PEOPLE:
        out.append(f"kişi sayısı hitteki gibi {HIT_KOPYA_KUL_PEOPLE} değil ({tb.get('people')})")
    if info.get("style_suffix") != tail:
        out.append("stil eki hit kamera eki değil")
    if info.get("story") != story:
        out.append("hikâye şablonla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt şablonla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out.extend(hit_kopya_kul_text_issues(text))
    if tail != HIT_KOPYA_KUL_TAIL or tail != HIT_KOPYA_KUL_HIT_TAIL:
        out.append("stil eki 13 Eki hit stil ekinden farklı")
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > HIT_KOPYA_KUL_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {HIT_KOPYA_KUL_MAX_WORDS})")
    if len(text) > HIT_KOPYA_KUL_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {HIT_KOPYA_KUL_MAX_CHARS})")
    return out


# ── 🌍 Yer yarılması (17 Kas 2026, Bahadır) ──────────────────────────────────────────────────────────────────────────
# Yeni kategori (2012 filmi esinli), tek olay: "🌍 Cadde yarılır". Deprem yarığı caddenin ortasından açılır, asfalt
# yarılıp derin bir uçuruma çöker, yarık kameraya doğru koşar. KASIRGA ile aynı kod-hikâye yolu (GPT yok, hikâye
# koddan birebir, zaman etiketleri metnin içinde; normal hattın sahnesi YOK: olay yapılandırılmış havuzda değil,
# rastgele domain rotasyonu ve snapshot'lar değişmesin diye sahne burada kurulur: yer_yarilmasi_build_scene).
# Prompt = AÇILIŞ + " " + ORTA + " " + FİNAL + " " + STİL (metinler Bahadır'ın talimatından birebir). Coğrafya G1-G6
# (son 3). 18 Kas (v3): orta tek seçenek O2 (otobüs), final tek seçenek F1 (bina); O1 ve F2 pasif (_PASIF), tek
# seçenekte orta/final LRU atlanır. Araç ve kişi sayısı ekseni yok (metinde sabit). Kayıt O*+F* (combo + Eksenler).
# 18 Kas (v4): yarık caddeyi yatay (soldan sağa) kameranın önünden keser, kamera çaprazdaki köşe binanın çatı
# terasında, ilk kareden aksiyon, tek orta O3 (otobüs, boşluk yok), tek final F3 (köşe binası kadrajda büyük).
# v3 açılış/orta/final/stil/listeler/etiket _V3 pasif kopya. Coğrafya G1-G6 ve LRU (son 3) aynen.
YER_YARILMASI_MODE_LABEL = "Yer yarılması · kod hikâye (v4: yatay yarık + köşe terası)"   # ✋ Onay (18 Kas v4)
YER_YARILMASI_MODE_LABEL_V3 = "Yer yarılması · kod hikâye (v3: ilk saniyede yarılma + otobüs + bina)"   # pasif (v3)
YER_YARILMASI_MODE_LABEL_V2 = "Yer yarılması · kod hikâye (v2: açık yarık + balkon kilidi)"   # pasif (18 Kas v2)
YER_YARILMASI_MODE_LABEL_V1 = "Yer yarılması · kod hikâye"   # pasif (17 Kas)
YER_YARILMASI_DOMAIN = "fissure_disasters"                    # Combo Key'in ilk parçası (Notion eksen sorgusu bununla)
YER_YARILMASI_EVENT = "Earthquake fissure splits a city avenue"   # Notion "Olay"; normal havuzda (DOMAIN_ATTRIBUTES) yok
YER_YARILMASI_CATEGORY_LABEL = "🌍 Yer yarılması"             # Telegram kategori düğmesi
YER_YARILMASI_EVENT_LABEL = "🌍 Cadde yarılır"                 # Telegram olay düğmesi
YER_YARILMASI_NOTION_CATEGORY = "Yer yarılması"               # Notion: Eksenler "kategori" (metin) + Paylaşımlar
YER_YARILMASI_MOD = "yer_yarilmasi"                           # config bayrağı, structure anahtarı, Notion axes.mod
YER_YARILMASI_MAX_WORDS = 230
YER_YARILMASI_MAX_CHARS = 1400
YER_YARILMASI_GEO_BLOCK = 3
YER_YARILMASI_MID_BLOCK = 1
YER_YARILMASI_FINAL_BLOCK = 1
YER_YARILMASI_SPOT = "rooftop terrace of a corner building"   # 18 Kas v4 (combo + Eksenler spot)
YER_YARILMASI_SPOT_V3 = "high balcony across the avenue"       # pasif (v1-v3)
YER_YARILMASI = {
    "geos": {
        "G1": {"name": "ABD (Kaliforniya)", "place": "a wide palm-lined boulevard in a Southern Californian city"},
        "G2": {"name": "ABD", "place": "a busy downtown avenue of brick buildings and glass towers in an American "
                                       "city"},
        "G3": {"name": "Meksika", "place": "a busy avenue of colonial-style buildings and jacaranda trees in Mexico "
                                           "City"},
        "G4": {"name": "Brezilya", "place": "a crowded avenue of tall apartment blocks in São Paulo"},
        "G5": {"name": "Şili", "place": "a busy avenue of Santiago with the Andes rising behind it"},
        "G6": {"name": "Japonya", "place": "a busy shopping street lined with narrow buildings in a Japanese city"},
    },
    # 18 Kas v4: açılış (ilk kareden yatay yarık, soldan sağa, kameranın önünden); v3 metni YER_YARILMASI_OPENING_V3
    "opening": ("From the very first frame {place} is breaking apart: a wide, jagged earthquake fissure cuts across "
                "the street from left to right in front of the camera, asphalt slabs dropping into it as it keeps "
                "widening. People sprint away from its edges."),
    # 18 Kas v4: tek orta O3 (otobüs fren yapar, boşluk yok); v3 ortası YER_YARILMASI_MIDS_V3, O1 pasif (_PASIF)
    "mids": {
        "O3": "A city bus brakes at the edge, tilts sideways and topples into the fissure in a burst of dust as more "
              "road breaks off.",
    },
    # 18 Kas v4: tek final F3 (köşe binası kadrajda büyük); v3 finali YER_YARILMASI_FINALS_V3, F2 pasif (_PASIF)
    "finals": {
        "F3": "The corner building on the far edge, big in frame, tilts and collapses into the fissure in a roar of "
              "dust.",
    },
    # 18 Kas v4: stil (köşe binası çatı terası, çapraz açı, teras korkuluğu kilidi); v3 metni YER_YARILMASI_TAIL_V3
    "tail": ("Handheld footage shot by a person standing on the rooftop terrace of a corner building diagonally "
             "across the street, normal lens; slight hand shake, the camera stays fixed on the fissure, shaking with "
             "the quake; no zoom, no cuts. The terrace railing stays at the bottom of the frame the whole time; the "
             "camera never moves forward or tilts down into the fissure. The ground keeps shaking and the fissure "
             "keeps widening the whole time, never a calm moment. Real earthquake footage: irregular broken asphalt, "
             "soil and rock, never thin drawn cracks, never glossy or CGI; no lava, no fire, no glowing light, no "
             "explosions. No readable signs or text. Everything moves in real time, never in slow motion, people run "
             "at full speed."),
}
# 18 Kas v4: v3 metinleri PASİF kopya (silinmedi, hiçbir yol kullanmaz; geri dönüş için)
YER_YARILMASI_OPENING_V3 = ("In the very first second {place} violently splits open down the middle, slabs of asphalt "
                            "heaving up as a long, jagged earthquake fissure tears toward the camera. Five or six "
                            "people sprint away along the sidewalks.")
YER_YARILMASI_MIDS_V3 = {
    "O2": "A city bus on the edge tilts sideways and topples into the fissure in a burst of dust.",
}
YER_YARILMASI_FINALS_V3 = {
    "F1": "The front of a building on the far side leans out and collapses into the fissure in a roar of dust and "
          "debris.",
}
YER_YARILMASI_TAIL_V3 = ("Handheld footage shot by a person standing on a high balcony across the avenue, normal lens; "
                         "slight hand shake, the camera stays fixed on the avenue, shaking with the quake; no zoom, no "
                         "cuts. The balcony railing stays at the bottom of the frame the whole time; the camera never "
                         "moves forward or tilts down into the fissure. The ground keeps shaking and the fissure keeps "
                         "tearing wider the whole time, never a calm moment. Real earthquake footage: irregular broken "
                         "asphalt, soil and rock, never a clean straight trench, never glossy or CGI; no lava, no "
                         "fire, no glowing light, no explosions, no flood water. No readable signs or text. Everything "
                         "moves in real time, never in slow motion, people run at full speed.")
# 18 Kas v3: v2 metinleri PASİF kopya (silinmedi, hiçbir yol kullanmaz; geri dönüş için)
YER_YARILMASI_OPENING_V2 = ("A massive earthquake fissure has already torn open down the middle of {place}, a long, "
                            "straight chasm running down the length of the avenue, its edges still collapsing as it "
                            "keeps ripping wider toward the camera. Five or six people sprint away along the sidewalks "
                            "as the ground drops behind them.")
YER_YARILMASI_MIDS_V2 = {
    "O1": "Parked cars along the edge tip over and slide nose-first into the chasm, one after another.",
    "O2": "A city bus at the edge tilts sideways and topples into the chasm in a burst of dust.",
}
YER_YARILMASI_FINALS_V2 = {
    "F1": "The front of a building on the far side of the chasm leans out and collapses into it in a roar of dust "
          "and debris.",
    "F2": "A whole section of the avenue, cars still on it, drops straight down into the chasm.",
}
YER_YARILMASI_TAIL_V2 = ("Handheld footage shot by a person standing on a high balcony across the avenue, eye level, "
                         "normal lens; slight hand shake, the camera stays fixed on the avenue, shaking with the quake; "
                         "no zoom, no cuts. The balcony railing stays at the bottom of the frame the whole time; the "
                         "camera never moves forward or tilts down into the chasm. Bystanders wear everyday clothes. "
                         "Raw natural daylight, dust in the air, never glossy or CGI. A real earthquake fissure of torn "
                         "asphalt, soil and rock, no lava, no fire, no glowing light, no explosions, no flood water. No "
                         "readable signs or text. Everything moves in real time, never in slow motion, people run at "
                         "full speed.")
# 18 Kas v3: pasif beat'ler (seçilmez): O1 park halindeki arabalar, F2 yol parçası (v2 metinleri)
YER_YARILMASI_MIDS_PASIF = {"O1": YER_YARILMASI_MIDS_V2["O1"]}
YER_YARILMASI_FINALS_PASIF = {"F2": YER_YARILMASI_FINALS_V2["F2"]}
# 18 Kas: v1 metinleri PASİF kopya (silinmedi, hiçbir yol kullanmaz; geri dönüş için)
YER_YARILMASI_OPENING_V1 = ("A massive earthquake fissure rips open down the middle of {place}, the asphalt splitting "
                            "apart and collapsing into a deep, wide chasm that races along the avenue toward the camera. "
                            "Five or six people sprint away along the sidewalks as the ground drops behind them.")
YER_YARILMASI_TAIL_V1 = ("Handheld footage shot by a person standing on a high balcony across the avenue, eye level, "
                         "normal lens; slight hand shake, the camera stays fixed on the avenue, shaking with the quake; "
                         "no zoom, no cuts. Bystanders wear everyday clothes, never hi-vis PPE on civilians. Raw natural "
                         "daylight, dust in the air, never glossy or CGI. A real earthquake fissure of torn asphalt, "
                         "soil and rock, no lava, no fire, no glowing light, no explosions, no flood water. No readable "
                         "signs or text. Everything moves in real time, never in slow motion, people run at full speed.")
YER_YARILMASI_CAMERA_LINE = ("Kamera: köşe binanın çatı terası, çapraz açı, normal lens, sabit, korkuluk kadrajın "
                             "altında")   # 18 Kas v4
YER_YARILMASI_CAMERA_LINE_V3 = ("Kamera: hit kamerası (caddenin karşısında yüksek balkon, normal lens, sabit, depremle "
                                "sarsılır, korkuluk kadrajın altında)")   # pasif (v3)
YER_YARILMASI_CAMERA_LINE_V2 = ("Kamera: hit kamerası (caddenin karşısında yüksek balkon, göz hizası, normal lens, "
                                "sabit, depremle sarsılır)")   # pasif
YER_YARILMASI_WARNING = ("⚠️ Gerçekçilik: yarık gerçek asfalt, toprak ve kaya mı (lav, ateş, parlama yok mu), insanlar "
                         "tam hızla koşuyor mu, video yapay görünüyor mu?")
YER_YARILMASI_WEATHER = "gündüz, doğal ışık (stil ekinde ışık satırı yok)"   # 18 Kas v3
YER_YARILMASI_WEATHER_V2 = "gündüz, doğal ışık, havada toz (stil ekinde raw natural daylight, dust in the air)"   # pasif
YER_YARILMASI_CONFIRM_DESC = ("İlk kareden cadde parçalanıyor: geniş, düzensiz bir deprem yarığı kameranın önünden "
                              "caddeyi soldan sağa keser, asfalt parçaları içine düşer, yarık genişlemeye devam eder. "
                              "İnsanlar kenarlardan kaçar. Ortada bir şehir otobüsü kenarda fren yapar, yan yatar ve "
                              "yarığa devrilir, yol kopmaya devam eder. Finalde karşı kenardaki köşe binası, kadrajda "
                              "büyük, yan yatıp yarığa çöker. Zemin hiç durmadan sarsılır. Lav yok, ateş yok, patlama "
                              "yok.")   # 18 Kas v4
YER_YARILMASI_CONFIRM_DESC_V3 = ("İlk saniyede cadde ortadan yarılır: asfalt kalkar, düzensiz uzun bir deprem yarığı "
                                 "kameraya doğru yırtılır. Beş altı kişi kaldırımlardan kaçar. Ortada bir şehir "
                                 "otobüsü yarığa devrilir; finalde karşıdaki binanın cephesi yarığa çöker. Zemin hiç "
                                 "durmadan sarsılır. Lav yok, ateş yok, sel suyu yok.")   # pasif (v3)
YER_YARILMASI_CONFIRM_DESC_V2 = ("Büyük bir deprem yarığı caddenin ortasından açılır: asfalt yarılır, derin ve geniş bir "
                              "uçuruma çöker, yarık caddeden kameraya doğru ilerler. Beş altı kişi kaldırımlardan "
                              "kaçar. Ortada park halindeki arabalar ya da bir şehir otobüsü uçuruma devrilir; finalde "
                              "karşıdaki binanın cephesi ya da caddenin bir bölümü uçuruma çöker. Lav yok, ateş yok, "
                              "sel suyu yok.")
# Kie öncesi son kontrol (büyük/küçük harf fark etmez)
# 18 Kas v4: ilk kareden yatay yarık (soldan sağa), köşe binası çatı terası (çapraz), teras korkuluğu kilidi, hiç
# sakin an yok, final kadrajda büyük, ince çizilmiş çatlak yok; v3'ün "very first second", "splits open" ve balkon
# ifadeleri, hendek ve v1/v2 ifadeleri artık yasak. v3 listeleri _V3, v2 listeleri _V2 (pasif)
YER_YARILMASI_REQUIRED = ("very first frame", "jagged earthquake fissure", "from left to right",
                          "rooftop terrace of a corner building", "diagonally across the street", "normal lens",
                          "terrace railing stays", "never moves forward", "never a calm moment", "big in frame",
                          "never thin drawn cracks")
YER_YARILMASI_FORBIDDEN = ("tornado", "funnel", "tsunami", "drone", "aerial", "slow-motion", "sinkhole", "crater",
                           "trench", "has already torn open", "straight chasm", "very first second", "splits open",
                           "balcony", "parked cars", "section of the avenue")
YER_YARILMASI_REQUIRED_V3 = ("very first second", "jagged earthquake fissure", "high balcony", "normal lens",
                             "balcony railing stays", "never moves forward", "never a calm moment")
YER_YARILMASI_FORBIDDEN_V3 = ("tornado", "funnel", "tsunami", "drone", "aerial", "slow-motion", "sinkhole", "crater",
                              "has already torn open", "straight chasm", "parked cars", "section of the avenue")
YER_YARILMASI_REQUIRED_V2 = ("earthquake fissure", "chasm", "high balcony", "normal lens", "has already torn open",
                             "long, straight chasm", "balcony railing stays", "never moves forward")
YER_YARILMASI_FORBIDDEN_V2 = ("tornado", "funnel", "tsunami", "drone", "aerial", "slow-motion", "sinkhole", "crater",
                              "rips open")
_YY = YER_YARILMASI
_YER_YARILMASI_GEO_MEMORY: list[str] = []


def yer_yarilmasi_is_active(event: str | None) -> bool:
    return event == YER_YARILMASI_EVENT


def yer_yarilmasi_tail() -> str:
    return _YY["tail"]


def yer_yarilmasi_opening(geo: str) -> str:
    if geo not in _YY["geos"]:
        raise es.StructureError(f"{YER_YARILMASI_MODE_LABEL}: {geo} bu kategoride yok (coğrafya G1-G6)")
    return _YY["opening"].format(place=_YY["geos"][geo]["place"])


def yer_yarilmasi_mid(mid: str) -> str:
    if mid not in _YY["mids"]:
        raise es.StructureError(f"{YER_YARILMASI_MODE_LABEL}: {mid} bu kategoride yok (orta {'/'.join(_YY['mids'])})")
    return _YY["mids"][mid]


def yer_yarilmasi_final(final: str) -> str:
    if final not in _YY["finals"]:
        raise es.StructureError(f"{YER_YARILMASI_MODE_LABEL}: {final} bu kategoride yok (final "
                                f"{'/'.join(_YY['finals'])})")
    return _YY["finals"][final]


def yer_yarilmasi_story(geo: str, mid: str, final: str) -> str:
    """Sıra: açılış + orta + final (zaman etiketleriyle)."""
    a, b, c = es.SLICE_LABELS
    return f"{a}: {yer_yarilmasi_opening(geo)} {b}: {yer_yarilmasi_mid(mid)} {c}: {yer_yarilmasi_final(final)}"


def yer_yarilmasi_prompt(geo: str, mid: str, final: str) -> str:
    """Prompt = AÇILIŞ + " " + ORTA + " " + FİNAL + " " + STİL."""
    from core.creative_engine import join_story_and_style
    return join_story_and_style(yer_yarilmasi_story(geo, mid, final), yer_yarilmasi_tail())


def yer_yarilmasi_tags(history: list[str]) -> list[str]:
    """Combo Key'lerden + süreç hafızasından O*+F* çiftleri (eskiden yeniye)."""
    return [t for t in es.beat_history(YER_YARILMASI_EVENT, history or []) if re.fullmatch(r"O\d+\+F\d+", t)]


def _yy_pick(ids: list[str], seen: list[str], block: int, rng=None) -> str:
    """Tek seçenek varsa LRU atlanır (rastgelelik tüketilmez); birden çoksa son `block` elenir."""
    if len(ids) == 1:
        return ids[0]
    return _block_pick(ids, seen, block, rng)


def yer_yarilmasi_choose_mid(tags: list[str], rng=None) -> str:
    return _yy_pick(list(_YY["mids"]), [t.split("+")[0] for t in tags], YER_YARILMASI_MID_BLOCK, rng)


def yer_yarilmasi_choose_final(tags: list[str], rng=None) -> str:
    return _yy_pick(list(_YY["finals"]), [t.split("+")[1] for t in tags], YER_YARILMASI_FINAL_BLOCK, rng)


def yer_yarilmasi_axes_history(records: list | None, key: str) -> list[str] | None:
    """Notion "Eksenler" ham kayıtlarından (eskiden yeniye) bu kategorinin `key` değerleri; okunamadıysa None."""
    import json
    if records is None:
        return None
    out = []
    for rec in records:
        try:
            data = json.loads((rec or {}).get("eksenler") or "")
        except (TypeError, ValueError, AttributeError):
            continue
        axes = data.get("axes") if isinstance(data, dict) else None
        if (isinstance(axes, dict) and data.get("event") == YER_YARILMASI_EVENT
                and axes.get("mod") == YER_YARILMASI_MOD and axes.get(key)):
            out.append(axes[key])
    return out


def yer_yarilmasi_choose_geo(used: list[str] | None = None, rng=None) -> str:
    seen = list(_YER_YARILMASI_GEO_MEMORY if used is None else used)
    return _block_pick(list(_YY["geos"]), seen, YER_YARILMASI_GEO_BLOCK, rng)


def yer_yarilmasi_lines(tb: dict) -> str:
    """✋ Onay satırları: mod, coğrafya, orta, final, kamera, kelime/karakter, eksenler + tekrar önleme, uyarı."""
    text = tb["prompt"]
    g = _YY["geos"][tb["geo"]]
    lines = [
        f"Mod: {YER_YARILMASI_MODE_LABEL}",
        f"Coğrafya: {tb['geo']} {g['name']} «{g['place']}»",
        f"Orta (4-9s): {tb['mid']} «{yer_yarilmasi_mid(tb['mid'])}»",
        f"Final (9-15s): {tb['final']} «{yer_yarilmasi_final(tb['final'])}»",
        YER_YARILMASI_CAMERA_LINE,
        f"Kelime: {len(text.split())} (en fazla {YER_YARILMASI_MAX_WORDS}) · karakter: {len(text)} "
        f"(en fazla {YER_YARILMASI_MAX_CHARS})",
    ]
    if tb.get("axes_line"):
        lines.append(tb["axes_line"])
    lines.append(YER_YARILMASI_WARNING)
    return "\n".join(lines)


def yer_yarilmasi_axes_json(tag: str, geo: str, excluded: dict | None = None) -> str:
    import core.axes_history as ah
    axes = {"spot": YER_YARILMASI_SPOT, "view": None, "light": None, "vehicle": None, "people": 5, "beats": tag,
            "mod": YER_YARILMASI_MOD, "kategori": YER_YARILMASI_NOTION_CATEGORY, "cografya": geo}
    return ah.axes_json(YER_YARILMASI_EVENT, axes, excluded)


def yer_yarilmasi_build_scene(domain: str | None, event: str | None, history: list[str] | None = None,
                              records: list | None = None, rng=None, history_source: str = "bellek") -> dict:
    """🌍 Yer yarılması sahnesi: GPT yok, normal hat yok. records = Notion "Eksenler" ham kayıtları (None = okunamadı /
    yükleyici yok: süreç hafızası). Coğrafya son 3, orta/final son 1. structure["yer_yarilmasi"] Kie öncesi son
    denetimin (submit_issues) kaynağıdır."""
    import random
    from core.skeleton_pipeline import SKELETON_CAMERA
    if domain not in (None, YER_YARILMASI_DOMAIN) or not yer_yarilmasi_is_active(event):
        raise es.StructureError(f"{YER_YARILMASI_MODE_LABEL} kurulamadı: {domain} / {event}")
    r = rng or random
    geo_used = yer_yarilmasi_axes_history(records, "cografya")
    tags = yer_yarilmasi_axes_history(records, "beats") if records is not None else yer_yarilmasi_tags(history or [])
    geo = yer_yarilmasi_choose_geo(geo_used, r)
    mid = yer_yarilmasi_choose_mid(tags, r)
    final = yer_yarilmasi_choose_final(tags, r)
    tag = es.beat_tag(mid, final)
    es.remember_beats(YER_YARILMASI_EVENT, tag)   # seçim anı hafızası (TEST/iptal da sayılır)
    _YER_YARILMASI_GEO_MEMORY.append(geo)
    del _YER_YARILMASI_GEO_MEMORY[:-12]
    story = yer_yarilmasi_story(geo, mid, final)
    tail = yer_yarilmasi_tail()
    prompt = yer_yarilmasi_prompt(geo, mid, final)
    g = _YY["geos"][geo]
    opening, mid_text, final_text = yer_yarilmasi_opening(geo), yer_yarilmasi_mid(mid), yer_yarilmasi_final(final)
    plain = " ".join([opening, mid_text, final_text])
    repeat = (f"coğrafya son {YER_YARILMASI_GEO_BLOCK} elendi · orta son {YER_YARILMASI_MID_BLOCK} · final son "
              f"{YER_YARILMASI_FINAL_BLOCK}")
    base_trace = {"pipeline": "creative", "structured": True, "domain": YER_YARILMASI_DOMAIN,
                  "event": YER_YARILMASI_EVENT, "ship": "None", "camera": SKELETON_CAMERA, "view": None,
                  "view_source": None, "place": g["place"], "count_range": [5, 6], "people_running": 5,
                  "outcome": "-", "recent_count": 0}
    trace, axes_line = mode_display(
        {"trace": base_trace}, {}, mode=YER_YARILMASI_MODE_LABEL,
        camera="hit kamerası (the camera stays fixed on the fissure, shaking with the quake); rooftop terrace of a "
               "corner building diagonally across the street, normal lens",
        opening=opening, mid=(mid, mid_text), final=(final, final_text), plain=plain, vehicle=None,
        spot="Rooftop terrace of a corner building (köşe binanın çatı terası, çapraz açı, normal lens, sabit, "
             "korkuluk kadrajın altında)",
        weather=YER_YARILMASI_WEATHER,
        axes={"coğrafya": f"{geo} {g['name']}", "orta": mid, "final": final,
              "kamera modu": "elde, sabit, depremle sarsılır"},
        repeat=repeat)
    trace = {**trace, "mode": YER_YARILMASI_MOD, "cografya": geo, "axes_source": history_source}
    tb = {"event": YER_YARILMASI_EVENT, "geo": geo, "mid": mid, "final": final, "story": story, "suffix": tail,
          "prompt": prompt, "axes_line": axes_line}
    tb["lines"] = yer_yarilmasi_lines(tb)
    seen_geo = list(geo_used if geo_used is not None else _YER_YARILMASI_GEO_MEMORY[:-1])
    excluded = {"cografya": [x for x in _YY["geos"] if x in seen_geo[-YER_YARILMASI_GEO_BLOCK:]]}
    axes_json = yer_yarilmasi_axes_json(tag, geo, excluded)
    structure = {YER_YARILMASI_MOD: tb, "axes_json": axes_json, "axes_line": None, "environment": None,
                 "story_source": f"Hikâye: kod (birebir) · {YER_YARILMASI_MODE_LABEL}", "story_source_kind": "code",
                 "caption_info": {"opening": opening, "people": 5, "kadraj": "teras",
                                  "beat_2": donma_caption_beat(mid_text), "beat_3": donma_caption_beat(final_text)},
                 "caption_candidates": None}
    problems = yer_yarilmasi_issues(structure, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{YER_YARILMASI_MODE_LABEL} son denetimden geçmedi: " + "; ".join(problems))
    combo = (f"{YER_YARILMASI_DOMAIN}|none|{YER_YARILMASI_EVENT.lower()}|{YER_YARILMASI_SPOT}##{tag}|"
             f"{SKELETON_CAMERA}")
    return {"domain": YER_YARILMASI_DOMAIN, "event": YER_YARILMASI_EVENT, "ship": None, "spot": YER_YARILMASI_SPOT,
            "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt, "combo_key": combo,
            "trace": trace, "structure": structure, "axes_json": axes_json}


def yer_yarilmasi_camera_issues(text: str, geo: str | None = None) -> list[str]:
    """Kie öncesi son kontrol: YER_YARILMASI_REQUIRED (v4: very first frame, jagged earthquake fissure, from left to
    right, rooftop terrace of a corner building, diagonally across the street, normal lens, terrace railing stays,
    never moves forward, never a calm moment, big in frame, never thin drawn cracks) ve seçilen G'nin place metni var;
    YER_YARILMASI_FORBIDDEN'dan (tornado, funnel, tsunami, drone, aerial, slow-motion, sinkhole, crater, trench, has
    already torn open, straight chasm, very first second, splits open, balcony, parked cars, section of the avenue)
    hiçbiri yok (büyük/küçük harf fark etmez). İhlal = gönderilmez."""
    out = []
    text = text or ""
    low = text.lower()
    for need in YER_YARILMASI_REQUIRED:
        if need.lower() not in low:
            out.append(f'"{need}" eksik')
    places = [k for k, v in _YY["geos"].items() if v["place"] in text]
    if not places:
        out.append("G1-G6 yer metni yok")
    elif geo is not None and places != [geo]:
        out.append(f"yer metni seçilen coğrafya değil ({geo}: {places})")
    for bad in YER_YARILMASI_FORBIDDEN:
        if bad.lower() in low:
            out.append(f"bu kategoride olmayan ifade var: {bad}")
    return out


def yer_yarilmasi_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin bu kalıpla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    tb = structure[YER_YARILMASI_MOD]
    if tb.get("surum") == YER_YARILMASI_V5_SURUM:   # 25 Kas: v5 kaydı kendi kalıbıyla denetlenir
        return yer_yarilmasi_v5_issues(structure, info)
    if tb.get("geo") not in _YY["geos"]:
        return [f"coğrafya G1-G6 değil ({tb.get('geo')})"]
    if tb.get("mid") not in _YY["mids"]:
        return [f"orta aktif seçenek değil ({tb.get('mid')})"]
    if tb.get("final") not in _YY["finals"]:
        return [f"final aktif seçenek değil ({tb.get('final')})"]
    story = yer_yarilmasi_story(tb["geo"], tb["mid"], tb["final"])
    prompt = yer_yarilmasi_prompt(tb["geo"], tb["mid"], tb["final"])
    out = []
    if info.get("style_suffix") != yer_yarilmasi_tail():
        out.append("stil eki Yer yarılması kalıbı değil")
    if info.get("story") != story:
        out.append("hikâye kalıpla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != prompt:
        out.append("prompt kalıpla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out += yer_yarilmasi_camera_issues(text, tb["geo"])
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > YER_YARILMASI_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {YER_YARILMASI_MAX_WORDS})")
    if len(text) > YER_YARILMASI_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {YER_YARILMASI_MAX_CHARS})")
    return out


# ── 🌍 Yer yarılması v5 (25 Kas 2026, Bahadır): AKTİF sürüm ──────────────────────────────────────────────────────────
# Kamera, açılış, stil eki ve G1-G6 metinleri v4 ile bayt bayt aynı (aynı nesneler okunur, kopya yok). Yeni: orta
# havuzu M1 (park halindeki arabalar) / M2 (teslimat kamyonu) / M3 (tramvay, yalnız coğrafya metninde tramvay geçen
# G'lerde; şu an hiçbirinde geçmiyor, M3 pasif), final havuzu F1 (v4 F3 cümlesi aynen) / F2 (yaya üst geçidi),
# coğrafya menüsü (menüden seçilen G tekrar önlemeye takılmaz). Kayıt M*+F*; v1-v4'ün O*+F* kayıtları orta/final LRU'ya
# girmez (F1/F2 adları eski sürümlerde başka cümleydi). v4 silinmedi ve çalışır: config "yer_yarilmasi_surum": "v4"
# (yukarıdaki fonksiyonlar aynen). v4 orta O3 ve v4 final F3 kimliği v5'te seçilemez.
YER_YARILMASI_V5_SURUM = "v5"
YER_YARILMASI_SURUM_KEY = "yer_yarilmasi_surum"               # config: "v4" = v4 kalıbı, yoksa v5
YER_YARILMASI_GEO_KEY = "yer_yarilmasi_geo"                   # config: menüden seçilen G1-G6 (None = 🎲 Rastgele)
YER_YARILMASI_V5_MODE_LABEL = "Yer yarılması · kod hikâye (v5: yeni orta havuzu + coğrafya menüsü)"   # ✋ Onay
YER_YARILMASI_V5_VERSION_LINE = ("Sürüm: yer_yar v5 (v4 kamera/açılış birebir + yeni orta havuzu + bina/üst geçit "
                                 "finali + coğrafya menüsü)")
YER_YARILMASI_GEO_BUTTONS = {"G1": "🇺🇸 ABD Kaliforniya", "G2": "🇺🇸 ABD şehir merkezi", "G3": "🇲🇽 Meksika",
                             "G4": "🇧🇷 Brezilya", "G5": "🇨🇱 Şili", "G6": "🇯🇵 Japonya"}
YER_YARILMASI_V5_MIDS = {
    "M1": "Cars parked along the curb slide sideways into the widening fissure one after another.",
    "M2": "A delivery truck brakes too late and plunges nose-first into the fissure, its rear wheels lifting into the "
          "air.",
}
YER_YARILMASI_V5_TRAM_MIDS = {   # yalnız yer metninde tramvay geçen coğrafyalarda (yer_yarilmasi_v5_tram_geos)
    "M3": "A tram derails at the edge of the fissure, tips over and slides in.",
}
YER_YARILMASI_V5_FINALS = {
    "F1": YER_YARILMASI["finals"]["F3"],   # v4 köşe binası finali, aynen
    "F2": "A pedestrian overpass spanning the street cracks at both ends and collapses into the fissure.",
}
YER_YARILMASI_V5_CONFIRM_DESC = ("İlk kareden cadde parçalanıyor: geniş, düzensiz bir deprem yarığı kameranın önünden "
                                 "caddeyi soldan sağa keser, asfalt parçaları içine düşer, yarık genişlemeye devam "
                                 "eder. İnsanlar kenarlardan kaçar. Ortada park halindeki arabalar art arda yarığa "
                                 "kayar ya da geç fren yapan bir teslimat kamyonu burun üstü yarığa düşer. Finalde "
                                 "kadrajda büyük köşe binası yan yatıp yarığa çöker ya da yaya üst geçidi iki ucundan "
                                 "çatlayıp yarığa çöker. Zemin hiç durmadan sarsılır. Lav yok, ateş yok, patlama yok.")
# Kie öncesi: v4 listeleri; "big in frame" yalnız F1 cümlesinde olduğu için finale bağlı. Otobüs v5'te yasak.
YER_YARILMASI_V5_REQUIRED = tuple(x for x in YER_YARILMASI_REQUIRED if x != "big in frame")
YER_YARILMASI_V5_FINAL_REQUIRED = {"F1": "big in frame", "F2": "pedestrian overpass"}
YER_YARILMASI_V5_FORBIDDEN = YER_YARILMASI_FORBIDDEN + ("city bus",)


def yer_yarilmasi_v5_tram_geos() -> list[str]:
    """Yer metninde tramvay geçen coğrafyalar (metinden okunur, elle liste yok)."""
    return [g for g, v in _YY["geos"].items() if re.search(r"\b(?:tram(?:s|way|ways|lines?)?|streetcars?)\b", v["place"], re.I)]


def yer_yarilmasi_v5_mids(geo: str) -> dict[str, str]:
    """Bu coğrafyada seçilebilen ortalar (M3 yalnız tramvaylı coğrafyada)."""
    return {**YER_YARILMASI_V5_MIDS, **(YER_YARILMASI_V5_TRAM_MIDS if geo in yer_yarilmasi_v5_tram_geos() else {})}


def yer_yarilmasi_v5_mid(geo: str, mid: str) -> str:
    mids = yer_yarilmasi_v5_mids(geo)
    if mid not in mids:
        raise es.StructureError(f"{YER_YARILMASI_V5_MODE_LABEL}: {mid} {geo} için yok (orta {'/'.join(mids)})")
    return mids[mid]


def yer_yarilmasi_v5_final(final: str) -> str:
    if final not in YER_YARILMASI_V5_FINALS:
        raise es.StructureError(f"{YER_YARILMASI_V5_MODE_LABEL}: {final} yok (final "
                                f"{'/'.join(YER_YARILMASI_V5_FINALS)})")
    return YER_YARILMASI_V5_FINALS[final]


def yer_yarilmasi_v5_story(geo: str, mid: str, final: str) -> str:
    """Sıra: açılış (v4) + orta + final (zaman etiketleriyle)."""
    a, b, c = es.SLICE_LABELS
    return (f"{a}: {yer_yarilmasi_opening(geo)} {b}: {yer_yarilmasi_v5_mid(geo, mid)} "
            f"{c}: {yer_yarilmasi_v5_final(final)}")


def yer_yarilmasi_v5_prompt(geo: str, mid: str, final: str) -> str:
    """Prompt = AÇILIŞ (v4) + " " + ORTA + " " + FİNAL + " " + STİL (v4)."""
    from core.creative_engine import join_story_and_style
    return join_story_and_style(yer_yarilmasi_v5_story(geo, mid, final), yer_yarilmasi_tail())


def yer_yarilmasi_v5_tags(tags: list[str]) -> list[str]:
    """Yalnız v5 çiftleri (M*+F*)."""
    return [t for t in tags or [] if re.fullmatch(r"M\d+\+F\d+", t)]


def yer_yarilmasi_v5_lines(tb: dict) -> str:
    """✋ Onay satırları: mod, sürüm, coğrafya (menü / rastgele), orta, final, kamera, kelime/karakter, eksenler +
    tekrar önleme, uyarı. Boş alan satırı yok (araç ekseni yok)."""
    text = tb["prompt"]
    g = _YY["geos"][tb["geo"]]
    lines = [
        f"Mod: {YER_YARILMASI_V5_MODE_LABEL}",
        YER_YARILMASI_V5_VERSION_LINE,
        f"Coğrafya: {tb['geo']} {g['name']} «{g['place']}» ({tb['geo_source']})",
        f"Orta (4-9s): {tb['mid']} «{yer_yarilmasi_v5_mid(tb['geo'], tb['mid'])}»",
        f"Final (9-15s): {tb['final']} «{yer_yarilmasi_v5_final(tb['final'])}»",
        YER_YARILMASI_CAMERA_LINE,
        f"Kelime: {len(text.split())} (en fazla {YER_YARILMASI_MAX_WORDS}) · karakter: {len(text)} "
        f"(en fazla {YER_YARILMASI_MAX_CHARS})",
    ]
    if tb.get("axes_line"):
        lines.append(tb["axes_line"])
    lines.append(YER_YARILMASI_WARNING)
    return "\n".join(lines)


def yer_yarilmasi_v5_axes_json(tb: dict, tag: str, excluded: dict | None = None) -> str:
    import core.axes_history as ah
    axes = {"spot": YER_YARILMASI_SPOT, "view": None, "light": None, "vehicle": None, "people": 5, "beats": tag,
            "mod": YER_YARILMASI_MOD, "kategori": YER_YARILMASI_NOTION_CATEGORY, "cografya": tb["geo"],
            "cografya_kaynak": tb["geo_source"], "surum": YER_YARILMASI_V5_SURUM}
    return ah.axes_json(YER_YARILMASI_EVENT, axes, excluded)


def yer_yarilmasi_v5_build_scene(domain: str | None, event: str | None, history: list[str] | None = None,
                                 records: list | None = None, rng=None, history_source: str = "bellek",
                                 geo: str | None = None) -> dict:
    """🌍 Yer yarılması v5 sahnesi: GPT yok, normal hat yok. geo = menüden seçilen G (tekrar önlemeye takılmaz; None =
    🎲 Rastgele, son 3 elenir). Orta/final son 1. records = Notion "Eksenler" ham kayıtları (None = süreç hafızası).
    structure["yer_yarilmasi"] Kie öncesi son denetimin (submit_issues) kaynağıdır."""
    import random
    from core.skeleton_pipeline import SKELETON_CAMERA
    label = YER_YARILMASI_V5_MODE_LABEL
    if domain not in (None, YER_YARILMASI_DOMAIN) or not yer_yarilmasi_is_active(event):
        raise es.StructureError(f"{label} kurulamadı: {domain} / {event}")
    if geo is not None and geo not in _YY["geos"]:
        raise es.StructureError(f"{label}: {geo} bu kategoride yok (coğrafya G1-G6)")
    r = rng or random
    geo_used = yer_yarilmasi_axes_history(records, "cografya")
    tags = yer_yarilmasi_v5_tags(yer_yarilmasi_axes_history(records, "beats") if records is not None
                                 else es.beat_history(YER_YARILMASI_EVENT, history or []))
    seen_geo = list(_YER_YARILMASI_GEO_MEMORY if geo_used is None else geo_used)
    geo_source = "menü" if geo is not None else "rastgele"
    if geo is None:
        geo = yer_yarilmasi_choose_geo(seen_geo, r)
        excluded = {"cografya": [x for x in _YY["geos"] if x in seen_geo[-YER_YARILMASI_GEO_BLOCK:]]}
    else:
        excluded = {"cografya": []}
    mid = _yy_pick(list(yer_yarilmasi_v5_mids(geo)), [t.split("+")[0] for t in tags], YER_YARILMASI_MID_BLOCK, r)
    final = _yy_pick(list(YER_YARILMASI_V5_FINALS), [t.split("+")[1] for t in tags], YER_YARILMASI_FINAL_BLOCK, r)
    tag = es.beat_tag(mid, final)
    es.remember_beats(YER_YARILMASI_EVENT, tag)   # seçim anı hafızası (TEST/iptal da sayılır)
    _YER_YARILMASI_GEO_MEMORY.append(geo)         # menü seçimi de sonraki 🎲 Rastgele için sayılır
    del _YER_YARILMASI_GEO_MEMORY[:-12]
    story = yer_yarilmasi_v5_story(geo, mid, final)
    tail = yer_yarilmasi_tail()
    prompt = yer_yarilmasi_v5_prompt(geo, mid, final)
    g = _YY["geos"][geo]
    opening = yer_yarilmasi_opening(geo)
    mid_text, final_text = yer_yarilmasi_v5_mid(geo, mid), yer_yarilmasi_v5_final(final)
    plain = " ".join([opening, mid_text, final_text])
    geo_repeat = (f"coğrafya menüden ({geo})" if geo_source == "menü"
                  else f"coğrafya son {YER_YARILMASI_GEO_BLOCK} elendi")
    repeat = f"{geo_repeat} · orta son {YER_YARILMASI_MID_BLOCK} · final son {YER_YARILMASI_FINAL_BLOCK}"
    base_trace = {"pipeline": "creative", "structured": True, "domain": YER_YARILMASI_DOMAIN,
                  "event": YER_YARILMASI_EVENT, "ship": "None", "camera": SKELETON_CAMERA, "view": None,
                  "view_source": None, "place": g["place"], "count_range": [5, 6], "people_running": 5,
                  "outcome": "-", "recent_count": 0}
    trace, axes_line = mode_display(
        {"trace": base_trace}, {}, mode=label,
        camera="hit kamerası (the camera stays fixed on the fissure, shaking with the quake); rooftop terrace of a "
               "corner building diagonally across the street, normal lens",
        opening=opening, mid=(mid, mid_text), final=(final, final_text), plain=plain, vehicle=None,
        spot="Rooftop terrace of a corner building (köşe binanın çatı terası, çapraz açı, normal lens, sabit, "
             "korkuluk kadrajın altında)",
        weather=YER_YARILMASI_WEATHER,
        axes={"sürüm": YER_YARILMASI_V5_SURUM, "coğrafya": f"{geo} {g['name']} ({geo_source})", "orta": mid,
              "final": final, "kamera modu": "elde, sabit, depremle sarsılır"},
        repeat=repeat)
    trace = {**trace, "mode": YER_YARILMASI_MOD, "surum": YER_YARILMASI_V5_SURUM, "cografya": geo,
             "axes_source": history_source, "no_vehicle_axis": True}   # 🔍 Ayrıntı'da "Araç: None" basılmaz
    tb = {"event": YER_YARILMASI_EVENT, "surum": YER_YARILMASI_V5_SURUM, "geo": geo, "geo_source": geo_source,
          "mid": mid, "final": final, "story": story, "suffix": tail, "prompt": prompt, "axes_line": axes_line}
    tb["lines"] = yer_yarilmasi_v5_lines(tb)
    axes_json = yer_yarilmasi_v5_axes_json(tb, tag, excluded)
    structure = {YER_YARILMASI_MOD: tb, "axes_json": axes_json, "axes_line": None, "environment": None,
                 "story_source": f"Hikâye: kod (birebir) · {label}", "story_source_kind": "code",
                 "caption_info": {"opening": opening, "people": 5, "kadraj": "teras",
                                  "beat_2": donma_caption_beat(mid_text), "beat_3": donma_caption_beat(final_text)},
                 "caption_candidates": None}
    problems = yer_yarilmasi_issues(structure, {"prompt": prompt, "story": story, "style_suffix": tail})
    if problems:
        raise es.StructureError(f"{label} son denetimden geçmedi: " + "; ".join(problems))
    combo = (f"{YER_YARILMASI_DOMAIN}|none|{YER_YARILMASI_EVENT.lower()}|{YER_YARILMASI_SPOT}##{tag}|"
             f"{SKELETON_CAMERA}")
    return {"domain": YER_YARILMASI_DOMAIN, "event": YER_YARILMASI_EVENT, "ship": None, "spot": YER_YARILMASI_SPOT,
            "story": story, "plain_story": plain, "style_suffix": tail, "prompt": prompt, "combo_key": combo,
            "trace": trace, "structure": structure, "axes_json": axes_json}


def yer_yarilmasi_v5_text_issues(text: str, geo: str, final: str) -> list[str]:
    """Kie öncesi son kontrol (v5): zorunlu ifadeler + finale bağlı zorunlu ifade + yalnız seçilen G'nin yer metni var,
    yasakların hiçbiri yok (büyük/küçük harf fark etmez). İhlal = gönderilmez."""
    out = []
    text = text or ""
    low = text.lower()
    for need in YER_YARILMASI_V5_REQUIRED + (YER_YARILMASI_V5_FINAL_REQUIRED[final],):
        if need.lower() not in low:
            out.append(f'"{need}" eksik')
    places = [k for k, v in _YY["geos"].items() if v["place"] in text]
    if places != [geo]:
        out.append(f"yer metni seçilen coğrafya değil ({geo}: {places})")
    for bad in YER_YARILMASI_V5_FORBIDDEN:
        if bad.lower() in low:
            out.append(f"bu kategoride olmayan ifade var: {bad}")
    return out


def yer_yarilmasi_v5_issues(structure: dict, info: dict) -> list[str]:
    """Kie'den hemen önce: gönderilecek metin v5 kalıbıyla koddan yeniden kurulanla birebir aynı mı. Boş = gönder."""
    tb = structure[YER_YARILMASI_MOD]
    if tb.get("geo") not in _YY["geos"]:
        return [f"coğrafya G1-G6 değil ({tb.get('geo')})"]
    if tb.get("mid") not in yer_yarilmasi_v5_mids(tb["geo"]):
        return [f"orta aktif seçenek değil ({tb.get('mid')})"]
    if tb.get("final") not in YER_YARILMASI_V5_FINALS:
        return [f"final aktif seçenek değil ({tb.get('final')})"]
    key = (tb["geo"], tb["mid"], tb["final"])
    out = []
    if info.get("style_suffix") != yer_yarilmasi_tail():
        out.append("stil eki Yer yarılması kalıbı değil")
    if info.get("story") != yer_yarilmasi_v5_story(*key):
        out.append("hikâye kalıpla yeniden kurulanla birebir aynı değil")
    if info.get("prompt") != yer_yarilmasi_v5_prompt(*key):
        out.append("prompt kalıpla yeniden kurulanla birebir aynı değil")
    text = info.get("prompt", "")
    out += yer_yarilmasi_v5_text_issues(text, tb["geo"], tb["final"])
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > YER_YARILMASI_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {YER_YARILMASI_MAX_WORDS})")
    if len(text) > YER_YARILMASI_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {YER_YARILMASI_MAX_CHARS})")
    return out
