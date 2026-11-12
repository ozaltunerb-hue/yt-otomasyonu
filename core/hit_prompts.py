# ⭐ Hit kalıbı (12 Kas 2026, Bahadır). Hesap düşüşte; sadece hit seviyesinde (9/10) video isteniyor. Hit videoyu üreten
# gerçek Kie prompt'unun ÇERÇEVESİ (kamera/kadraj cümlesi, stil ve kural cümleleri, cümle sırası, bağlaçlar) birebir;
# olaylar her basışta değişir (video kopya görünmesin).
#
# Kaynak: Notion "DeepMyster Youtube Otomasyonu" kayıtları (dashboard_data/notion_runs.json ile birebir aynı). Tarihler
# Türkiye saati (Notion UTC: -3 saat).
#
# Normal üretim yolu DEĞİŞMEZ: mod sadece Telegram "⭐ Hit kalıbı" butonundan açılır (config["hit_env"]). Seçim normal
# hattın kendisi (ortam zorlanır, T4+U11 dışlanır: es.HIT_OVERRIDE), metin burada hit kalıbına yerleştirilir. GPT yok.
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
