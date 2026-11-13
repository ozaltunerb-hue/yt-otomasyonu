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
# havuzu K*/L*). Araç bu modun kendi havuzundan (son 2), kişi 3/4. Yasak çiftler M2+N3 (iki kez ağaç), M4+N1 (iki kez
# ev çatısı). "U-turn" bu modda yok (M1 hit sahnesi, U dönüşü olmadan).
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
ORMAN_MID_BLOCK = 2
ORMAN_FINAL_BLOCK = 2
ORMAN_BANNED_PAIRS = (("M2", "N3"), ("M4", "N1"))
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
    "opening": "A towering wall of flames sweeps down the {forest} slope at the far end of the street and slams into "
               "the edge of {place}, igniting roofs and trees as it races toward the camera.",
    "people": {3: "Three people run up the street below, away from the flames.",
               4: "Four people run up the street below, away from the flames."},
    "action": "Burning embers and thick smoke blow across the street from the very first frame.",
    "vehicles": ("white van", "pickup truck", "SUV"),
    "mids": {
        "M1": "Halfway down the street, the {vehicle} speeds away as the wall of flames closes the road right behind it.",
        "M2": "Halfway down the street, a huge burning pine crashes down onto the {vehicle}, crushing its roof.",
        "M3": "Halfway down the street, the wall of flames swallows a parked {vehicle}, its windows bursting as it "
              "disappears into the fire.",
        "M4": "Halfway down the street, two houses on either side of the road catch fire at once, flames pouring out of "
              "their windows and roofs.",
    },
    "finals": {
        "N1": "Right below the balcony, the flames reach the nearest house and its roof caves in, a fountain of sparks "
              "bursting up toward the camera.",
        "N2": "Right below the balcony, the wall of flames engulfs the garden and wooden deck of the nearest house, "
              "burning planks collapsing in a shower of sparks.",
        "N3": "Right below the balcony, a burning tree topples onto the nearest house, smashing through its roof as "
              "flames pour inside.",
        "N4": "Right below the balcony, the fire jumps the street and the wooden fence and carport below burst into "
              "flames, heat and sparks rushing up toward the camera.",
    },
    "vehicle_mids": ("M1", "M2", "M3"),
    "camera": {True: "the camera pans to follow the wall of flames as it approaches", False: "the camera stays fixed"},
    "tail": ("Handheld footage shot from the balcony of a hillside house overlooking the street and the burning slope, "
             "high vantage, normal lens, a corner of the balcony railing in the foreground; slight hand shake, "
             "{camera}; one continuous shot, no zoom, no cuts, no face close to the camera. Civilians in everyday "
             "clothes, never CGI. Realistic wildfire: towering, roaring flames and thick smoke, never thin lines or "
             "strips of fire. Raw natural light under an orange smoky sky. Real time, never slow motion, people run at "
             "full speed. No readable signs, text or flags."),
}
_OR = YAKLASMA_ORMAN
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
        raise es.StructureError(f"{ORMAN_MODE_LABEL}: {mid} bu modda yok (orta M1-M4)")
    if mid in _OR["vehicle_mids"] and vehicle not in _OR["vehicles"]:
        raise es.StructureError(f"{ORMAN_MODE_LABEL}: {mid} için araç yok ({vehicle})")
    return _OR["mids"][mid].format(vehicle=vehicle or "")


def orman_story(geo: str, people: int, mid: str, vehicle: str | None, final: str) -> str:
    if (mid, final) in ORMAN_BANNED_PAIRS:
        raise es.StructureError(f"{ORMAN_MODE_LABEL}: {mid}+{final} yasak çift")
    a, b, c = es.SLICE_LABELS
    return (f"{a}: {orman_opening(geo)} {orman_people(people)} {_OR['action']} {b}: {orman_mid(mid, vehicle)} "
            f"{c}: {_OR['finals'][final]}")


def orman_prompt(geo: str, people: int, mid: str, vehicle: str | None, final: str, follow: bool | None = None) -> str:
    from core.creative_engine import join_story_and_style
    return join_story_and_style(orman_story(geo, people, mid, vehicle, final), orman_tail(follow))


def orman_tags(history: list[str]) -> list[str]:
    return [t for t in es.beat_history(es.WILDFIRE, history or []) if re.fullmatch(r"M\d+\+N\d+", t)]


def orman_choose_mid(history: list[str], rng=None) -> str:
    return _block_pick(list(_OR["mids"]), [t.split("+")[0] for t in orman_tags(history)], ORMAN_MID_BLOCK, rng)


def orman_choose_final(history: list[str], mid: str, rng=None) -> str:
    """Final: son 2 elenir; seçilen ortanın yasak eşi (M2→N3, M4→N1) hiç aday değil."""
    banned = {f for m, f in ORMAN_BANNED_PAIRS if m == mid}
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
    R1-R6 (son 3 elenir, R1 tohum), araç (son 2), orta M1-M4 (son 2), final N1-N4 (son 2; M2+N3, M4+N1 yasak), kişi 3/4.
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
    plain = " ".join([orman_opening(geo), orman_people(people), _OR["action"], mid_text, _OR["finals"][final]])
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
               f"{ORMAN_MID_BLOCK} · final son {ORMAN_FINAL_BLOCK} (M2+N3, M4+N1 yasak)")
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
        return [f"orta M1-M4 değil ({ob.get('mid')})"]
    if ob.get("final") not in _OR["finals"]:
        return [f"final N1-N4 değil ({ob.get('final')})"]
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
    for bad in ("Full action", "Until the last frame", "U-turn"):
        if bad in text:
            out.append(f"bu modda olmayan ifade var: {bad}")
    for lab in es.SLICE_LABELS:
        if f"{lab}: " not in text:
            out.append(f"zaman etiketi eksik: {lab}")
    if len(text.split()) > ORMAN_MAX_WORDS:
        out.append(f"prompt {len(text.split())} kelime (en fazla {ORMAN_MAX_WORDS})")
    if len(text) > ORMAN_MAX_CHARS:
        out.append(f"prompt {len(text)} karakter (en fazla {ORMAN_MAX_CHARS})")
    return out
