#!/usr/bin/env python3
"""
🏚️ Deprem kategorisi (14 Eki 2026, Bahadır; TASLAK): 2 olay yapılandırılmış hatta, çığ yapısı (sabit yüksek kamera,
kod havuzu, araçsız, 175 kelime kapısı, olaya özel yasak kelimeler, ortam havuzu, yakınlık kapısı). Çöken bina her
zaman konut. KİLİT: havuz/kilit cümle/kamera Bahadır'ın onayıyla değişir. Ağ yok, Kie/GPT çağrısı yok.
"""
import asyncio
import os
import random
import sys
import unittest
from itertools import combinations

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import core.event_structure as es
import core.skeleton_pipeline as sk

APT, OLD = es.EARTHQUAKE_APARTMENT, es.EARTHQUAKE_OLD_STREET
EQ = (APT, OLD)
ROOF, BAL = "Rooftop terrace of a building across the street", "High-floor balcony across the street"
CAMS = {ROOF: "a rooftop terrace", BAL: "a high-floor balcony"}
CAMERA = ("Handheld footage from {cam}, high vantage looking across the street at the buildings collapsing opposite; "
          "the collapsing buildings and the dust fill the upper two thirds of the frame, the street and a corner of "
          "the railing fill the lower part; strong hand shake from the ground tremor, the camera stays fixed and never "
          "descends; one continuous shot, no zoom, no cuts.")
GUARD = "Bystanders wear everyday clothes; raw natural light, no hazmat suits."
HIGH = {"P2", "Q4", "R1"}   # (*) sadece çatı terasında
KEY = {
    APT: "The ground is already shaking violently and a six-storey apartment block across the street collapses floor "
         "by floor, a huge dust cloud bursting out of it.",
    OLD: "The ground is already shaking violently and a row of old stone houses along the street collapses one after "
         "another, dust and rubble bursting into the street.",
}
POOLS = {
    APT: ({"P1": "the upper floors pancake down onto the lower ones and a wall of dust surges across the street",
           "P2": "the whole front wall of the block peels off and crashes onto the street",
           "P3": "the neighboring apartment block leans and its side wall collapses",
           "P4": "a huge concrete slab from the collapsing block slams into the road and breaks it apart"},
          {"Q1": "the building next door crumbles floor by floor into the same dust cloud",
           "Q2": "the dust wave rolls down the street and the upper floors of the apartment blocks opposite cave in",
           "Q3": "a row of low houses beside the block is flattened under falling concrete",
           "Q4": "a second apartment block across the street tilts and falls into the dust"}),
    OLD: ({"R1": "the facade of the nearest old stone house slides off in one piece and crashes down",
           "R2": "the stone walls of two houses fold inward and their roofs fall in",
           "R3": "a thick dust cloud pours down the narrow street as the stone houses keep falling",
           "R4": "a corner stone house crumbles and its rubble spreads across the junction"},
          {"T1": "the next house in the row caves in and the dust cloud grows",
           "T2": "the collapse runs down the street, house after house, toward us",
           "T3": "the rubble heap of a fallen house slides out into the street",
           "T4": "the roof of a stone house falls in and its walls collapse into the street"}),
}
# Aynı yapı/görüntü sınıfı: komşu blok (P3: Q1, Q4), toz dalgası (P1, Q2), çatı içe göçer (R2, T4), toz bulutu (R3, T1),
# sokağa yayılan moloz (R4, T3)
STRUCT = {
    APT: {"P1": {"dust"}, "P2": set(), "P3": {"neighbor"}, "P4": set(),
          "Q1": {"neighbor"}, "Q2": {"dust"}, "Q3": set(), "Q4": {"neighbor"}},
    OLD: {"R1": set(), "R2": {"roof"}, "R3": {"dust"}, "R4": {"rubble"},
          "T1": {"dust"}, "T2": set(), "T3": {"rubble"}, "T4": {"roof"}},
}
VALID = {
    "P1": ["The upper floors pancake onto the ones below as a wall of dust surges across the street.",
           "Floor after floor collapses onto the lower storeys, dust surging over the street.",
           "The top floors crash down onto the lower floors and dust rolls across the road.",
           "The upper storeys drop onto the floors beneath them, throwing dust across the street.",
           "The upper floors pancake down onto the lower ones and a wall of dust surges across the street."],
    "P2": ["The entire front wall of the block tears away and crashes into the street.",
           "The block's facade peels off in one sheet and slams onto the street.",
           "The whole front of the apartment block comes away and falls onto the road.",
           "The front wall shears off the block and crashes down onto the street below.",
           "The whole front wall of the block peels off and crashes onto the street."],
    "P3": ["The neighbouring apartment block tilts and its side wall caves in.",
           "Next door, another apartment block leans over and its side wall collapses.",
           "The adjacent block sways and its side wall crumbles into the street.",
           "The apartment building next door leans hard and its side wall gives way.",
           "The neighboring apartment block leans and its side wall collapses."],
    "P4": ["A huge concrete slab from the block crashes onto the road and cracks it apart.",
           "A massive slab of concrete slams into the street, splitting the asphalt.",
           "A giant chunk of concrete falls from the block and smashes the road open.",
           "A concrete slab drops onto the roadway and breaks it into pieces.",
           "A huge concrete slab from the collapsing block slams into the road and breaks it apart."],
    "Q1": ["The building next door collapses floor by floor into the same dust cloud.",
           "The neighbouring building crumbles storey by storey into the dust.",
           "Next door, another apartment block caves in floor by floor.",
           "The adjacent building comes down one floor at a time into the dust cloud.",
           "The building next door crumbles floor by floor into the same dust cloud."],
    "Q2": ["The dust wave sweeps down the street as the top floors of the blocks opposite cave in.",
           "A wave of dust rolls along the street and the upper floors of the apartment blocks across collapse.",
           "Dust surges down the street while the upper storeys of the buildings opposite give way.",
           "The dust wave races down the street and the apartment blocks opposite crumble from the top floors.",
           "The dust wave rolls down the street and the upper floors of the apartment blocks opposite cave in."],
    "Q3": ["A row of low houses beside the block is crushed under falling concrete.",
           "Falling concrete flattens the low houses next to the block.",
           "The low houses beside the block cave in under the falling concrete.",
           "Concrete crashes down and smashes a row of small houses beside the block.",
           "A row of low houses beside the block is flattened under falling concrete."],
    "Q4": ["A second apartment block across the street leans and falls into the dust.",
           "Another apartment block opposite tilts and collapses into the dust cloud.",
           "Across the street, a second block topples over into the dust.",
           "A second apartment building opposite sways and crashes down into the dust.",
           "A second apartment block across the street tilts and falls into the dust."],
    "R1": ["The front wall of the nearest old stone house slides off in one piece and crashes down.",
           "The nearest stone house's facade breaks away whole and falls into the street.",
           "The facade of the closest old stone house tears off and crashes to the ground.",
           "The whole front of the nearest stone house comes away and collapses.",
           "The facade of the nearest old stone house slides off in one piece and crashes down."],
    "R2": ["The stone walls of two houses buckle inward and their roofs fall in.",
           "Two houses fold in on themselves as their roofs cave in.",
           "The walls of two old houses crumble inward and the roofs collapse.",
           "Two stone houses give way, their walls folding inward and their roofs dropping.",
           "The stone walls of two houses fold inward and their roofs fall in."],
    "R3": ["A thick cloud of dust pours down the narrow street as the stone houses keep collapsing.",
           "Dust floods the narrow street while the old stone houses keep falling.",
           "A dense dust cloud rolls down the street as more stone houses crumble.",
           "The narrow street fills with thick dust as the houses keep coming down.",
           "A thick dust cloud pours down the narrow street as the stone houses keep falling."],
    "R4": ["A corner stone house collapses and its rubble spills across the junction.",
           "The stone house on the corner crumbles, rubble spreading over the intersection.",
           "A corner house caves in and its stones scatter across the junction.",
           "The old corner house falls apart and its rubble pours into the crossroads.",
           "A corner stone house crumbles and its rubble spreads across the junction."],
    "T1": ["The next house in the row collapses and the dust cloud grows.",
           "Another house in the row caves in as the dust thickens.",
           "The neighbouring house crumbles and the dust cloud swells.",
           "The next stone house in the row gives way and more dust rises.",
           "The next house in the row caves in and the dust cloud grows."],
    "T2": ["The collapse sweeps down the street, house after house, toward us.",
           "House after house falls in turn along the street, closer and closer.",
           "One after another the houses collapse down the street, heading toward us.",
           "The houses fall one by one along the street, the collapse coming our way.",
           "The collapse runs down the street, house after house, toward us."],
    "T3": ["The rubble heap of a collapsed house slides into the street.",
           "A heap of rubble from a collapsed house spills across the street.",
           "The debris of a fallen house pours out onto the road.",
           "Piles of stones from a fallen house tumble out into the street.",
           "The rubble heap of a fallen house slides out into the street."],
    "T4": ["The roof of a stone house caves in and its walls collapse into the street.",
           "A stone house's roof falls in and its walls crumble onto the street.",
           "The roof of an old house drops in and the walls tumble into the street.",
           "A house's roof collapses and its stone walls fall into the street.",
           "The roof of a stone house falls in and its walls collapse into the street."],
}
# Sadece atmosfer: hiçbir maddeden geçmemeli
ATMOSPHERE = ["The ground shakes under a hazy sky.",
              "Dust drifts across the quiet street.",
              "A grey sky hangs over the rooftops.",
              "The street trembles as people look up.",
              "A haze of dust hangs in the morning light."]
SETTING = "Setting: a dense hillside neighbourhood of dark apartment blocks, quiet residential street, hazy dusty morning."
LEAK = ("turkey", "türkiye", "syria", "japan", "italy", "greece", "iran", "nepal", "mexico", "chile", "istanbul",
        "ankara", "antakya", "flag", "logo", "banner")


def cap(s):
    return s[0].upper() + s[1:]


def eq_gpt(messages=None):
    """Ağsız sahte GPT: seçilen maddeleri birebir dilim yapar (ücretli çağrı yok)."""
    async def gpt(system, user, **kw):
        if messages is not None:
            messages.append(user)
        line = dict(l.split(": ", 1) for l in user.splitlines()
                    if l.startswith(("4-9s EVENT", "9-15s EVENT", "PEOPLE RUNNING AWAY")))
        word = line["PEOPLE RUNNING AWAY"].split()[0]
        away = line["PEOPLE RUNNING AWAY"].split("run away from ")[1].split(",")[0]
        s2, s3 = cap(line["4-9s EVENT"]), cap(line["9-15s EVENT"])
        s2 += " as the ground shakes" if len(s2.split()) < 10 else ""
        s3 += " as the ground shakes" if len(s3.split()) < 10 else ""
        return {"slice_1_rest": f"{cap(word)} people run from {away} near the railing.",
                "slice_2": s2 + ".", "slice_3": s3 + "."}
    return gpt


def build(e, b2, b3, spot=ROOF, people=5, setting=SETTING):
    spec = es.build_spec(e, None, spot, None, b2, b3, None, people, setting)
    s2, s3 = cap(es.beat_text(e, "slice_2", b2)), cap(es.beat_text(e, "slice_3", b3))
    s2 += " as the ground shakes" if len(s2.split()) < 10 else ""
    s3 += " as the ground shakes" if len(s3.split()) < 10 else ""
    sl = {"slice_1_rest": es.clean_slice(f"{cap(es.NUMBER_WORDS[people])} people run from the collapsing buildings "
                                         f"near the railing."),
          "slice_2": es.clean_slice(s2), "slice_3": es.clean_slice(s3)}
    return spec, sl


def codes(spec, sl):
    return {i["rule"] for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl))}


def beats():
    for e in EQ:
        for slot in ("slice_2", "slice_3"):
            for bid, beat in es.EVENT_BEATS[e][slot].items():
                yield e, slot, bid, beat


def all_envs(e):
    out = []
    for c in es.EQ_EVENT_CITIES[e]:
        for st in es.EQ_EVENT_STREETS[e]:
            for li in es.EQ_ENV_AXES["light"]:
                env = {"city": c, "street": st, "light": li}
                if c == es.EQ_AVENUE_CITY and st not in es.EQ_AVENUE_STREETS:
                    continue
                if len(es.setting_line(env).split()) <= 15:
                    out.append(env)
    return out


class TestEarthquake(unittest.TestCase):
    def setUp(self):
        es._BEAT_MEMORY.clear()
        es._EQ_ENV_MEMORY.clear()

    def test_category_menu_and_registrations(self):
        import bot
        import core.creative_pipeline as cp
        from core.creative_engine import (DOMAIN_ATTRIBUTES, ENV_CENTRIC_DOMAINS, MARITIME_INSPIRATION_DOMAINS,
                                          is_current_universe_combo)
        self.assertEqual(bot.DOMAIN_LABELS["earthquake_disasters"], "🏚️ Deprem")
        self.assertIn('earthquake_disasters: "🏚️ Deprem",', open(os.path.join(ROOT, "dashboard.html"),
                                                                encoding="utf-8").read())
        self.assertEqual({e: bot.EVENT_LABELS[e] for e in EQ},
                         {APT: "🏢 Apartman bloğu çöküyor", OLD: "🧱 Eski sokak çöküyor"})
        self.assertEqual(sk.skeleton_events("earthquake_disasters"), list(EQ))
        self.assertEqual(DOMAIN_ATTRIBUTES["earthquake_disasters"]["environments"], [ROOF, BAL])
        self.assertEqual(DOMAIN_ATTRIBUTES["earthquake_disasters"]["ships"], [])
        self.assertIn("earthquake_disasters", MARITIME_INSPIRATION_DOMAINS)
        self.assertIn("earthquake_disasters", ENV_CENTRIC_DOMAINS)
        self.assertIn("earthquake_disasters", sk.NO_SIGNS_DOMAINS)
        self.assertEqual(sk.PHENOMENA["Deprem"], list(EQ))
        # Notion kombinasyon geçmişi deprem kayıtlarını sayar (Combo Key metin alanı; select seçeneği gerekmez)
        self.assertTrue(is_current_universe_combo(
            f"earthquake_disasters|none|{APT.lower()}|{ROOF.lower()}##P1+Q1|bystander_handheld"))
        for e in EQ:
            with self.subTest(event=e):
                self.assertTrue(es.is_structured(e))
                self.assertEqual(cp.EVENT_REQUIRED[e], [])
                self.assertIn(e, cp.EVENT_OUTCOMES)
                self.assertEqual(sk.count_range(e, None), (3, 6))
                self.assertEqual(es.TOTAL_WORDS_BY_EVENT[e], (40, 70))
                self.assertFalse(es.uses_vehicle(e))
                self.assertNotIn(e, es.EVENT_VEHICLES)
                self.assertEqual(es.structure_views(e), [None])
                self.assertIn(e, es.WORD_CAP_EVENTS)
                self.assertIn(e, es.ENV_EVENTS)
                self.assertIn(e, es.BUDGET_EVENTS)
                self.assertNotIn(e, es.NO_RAIN_EVENTS)
        # Telegram: deprem düğmesi, 2 olay + 🎲 Rastgele / 🔙 Geri, callback 64 bayt altında
        texts = [b.text for row in bot.domain_keyboard().inline_keyboard for b in row]
        self.assertIn("🏚️ Deprem", texts)
        markup = bot.event_keyboard(bot.DOMAIN_KEYS.index("earthquake_disasters"))
        labels = [b.text for row in markup.inline_keyboard for b in row]
        for label in ("🏢 Apartman bloğu çöküyor", "🧱 Eski sokak çöküyor", "🎲 Rastgele"):
            self.assertIn(label, labels)
        self.assertTrue(any("Geri" in t for t in labels))
        for row in markup.inline_keyboard:
            for b in row:
                self.assertLessEqual(len(b.callback_data.encode()), 64)

    def test_key_sentences_and_pools_locked(self):
        import core.creative_pipeline as cp
        for e in EQ:
            with self.subTest(event=e):
                self.assertEqual(es.EVENT_KEY_VISUAL[e], KEY[e])
                self.assertIn("is already shaking violently", KEY[e])
                self.assertIn("apartment block" if e == APT else "old stone houses", KEY[e])
                found = {i["rule"] for i in cp.story_rule_issues(e, None, KEY[e])}
                self.assertFalse(found & {"a_trigger_first", "b_no_camera_words", "e_event_and_ship_named", "required"})
                b = es.EVENT_BEATS[e]
                self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, POOLS[e][0])
                self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, POOLS[e][1])
                self.assertEqual(b["excluded_views"], {})
                for code, terms, *_ in es.EVENT_BANNED_WORDS[e]:
                    self.assertEqual(es.find_terms(terms, KEY[e]), [])
        # hiçbir maddede kamera kelimesi, balkon düşmesi, cam/pencere, dükkan/ofis, gömülme yok
        for e, slot, bid, beat in beats():
            with self.subTest(beat=bid):
                for w in ("camera", "video", "footage", "phone", "balcony", "glass", "window", "shop", "office",
                          "arch", "gate", "door", "bury", "buried", "burial"):
                    # "next door" bir kapı maddesi değil (Q1: yan bina)
                    self.assertEqual(es.find_terms((w,), beat["text"].replace("next door", "")), [], w)

    def test_camera_and_style_suffix(self):
        from core.trace_format import count_constraints
        for e in EQ:
            self.assertEqual(list(sk.EVENT_SKELETONS[e]["spots"]), [ROOF, BAL])
            for spot in (ROOF, BAL):
                suffix = sk.style_suffix(e, None, spot, None, SETTING)
                with self.subTest(event=e, spot=spot):
                    self.assertEqual(sk.CAMERA_SPOTS[spot], CAMS[spot])
                    self.assertEqual(suffix, f"{CAMERA.format(cam=CAMS[spot])} {SETTING} {GUARD} No readable signs, "
                                             f"text or flags.")
                    self.assertNotIn("follow", suffix)
                    self.assertLessEqual(count_constraints(suffix)[0], 8)
                    self.assertLessEqual(len(suffix.split()), 95)
                    self.assertLessEqual(70 + 3 + len(suffix.split()), 175)
        # çığ ve volkan kamerası değişmedi
        self.assertTrue(sk.style_suffix(es.AVALANCHE_SKI, None, "Terrace of the lift station")
                        .startswith("Handheld footage from the lift station terrace, high vantage looking up a steep"))
        self.assertTrue(sk.style_suffix(es.ERUPTION, None, "Hillside terrace facing the erupting volcano")
                        .startswith("Handheld footage shot by a person standing on a hillside terrace above the village"))

    def test_term_lists_earthquake_only(self):
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(es))
        node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(getattr(t, "id", None) == "EVENT_BEATS" for t in n.targets))
        seen = 0
        for k, v in zip(node.keys, node.values):
            if getattr(k, "id", None) in ("EARTHQUAKE_APARTMENT", "EARTHQUAKE_OLD_STREET"):
                seen += 1
                names = {n.id for n in ast.walk(v) if isinstance(n, ast.Name)}
                self.assertTrue(names and all(n.startswith("_EQ_") for n in names), names)
        self.assertEqual(seen, 2)

    def test_every_beat_alone_and_five_natural_sentences(self):
        self.assertEqual(set(VALID), {bid for _, _, bid, _ in beats()})
        for e, slot, bid, beat in beats():
            text = es.clean_slice(cap(es.beat_text(e, slot, bid)))
            with self.subTest(beat=bid):
                self.assertEqual(es.missing_term_groups(beat["terms"], text), [])
                self.assertGreaterEqual(len(VALID[bid]), 5)
                for s in VALID[bid]:
                    self.assertEqual(es.missing_term_groups(beat["terms"], s), [], s)
                    for code, terms, *_ in es.EVENT_BANNED_WORDS[e]:
                        self.assertEqual(es.find_terms(terms, s), [], s)
                    self.assertEqual(es.find_terms(("camera", "video", "footage", "phone"), s), [], s)
                for a in ATMOSPHERE:
                    self.assertTrue(es.missing_term_groups(beat["terms"], a), a)
                others = [o for o, ob in es.EVENT_BEATS[e][slot].items()
                          if o != bid and es.missing_term_groups(ob["terms"], text)]
                self.assertTrue(others, bid)

    def test_banned_and_slow_words_gate(self):
        spec, sl = build(APT, "P1", "Q1")
        self.assertFalse(codes(spec, sl) & {"earthquake_banned", "earthquake_no_slow"})
        for w in ("dead", "bodies", "body", "victims", "injured", "blood", "trapped", "buried", "rescue", "casualties",
                  "car", "truck", "cargo", "tugboat", "Turkey", "Istanbul", "Japan"):
            with self.subTest(word=w):
                bad = es.clean_slice(f"The building next door crumbles floor by floor near the {w}")
                self.assertIn("earthquake_banned", codes(spec, {**sl, "slice_3": bad}))
        for w in ("slowly", "gently", "gradually"):
            with self.subTest(word=w):
                bad = es.clean_slice(f"The building next door {w} crumbles floor by floor into the dust")
                self.assertIn("earthquake_no_slow", codes(spec, {**sl, "slice_3": bad}))
        # kamera kelimesi yine yasak (b kuralı)
        bad = es.clean_slice("The collapse runs down the street, house after house, toward the camera")
        spec2, sl2 = build(OLD, "R2", "T2")
        self.assertIn("b_no_camera_words", {i["rule"] for i in es.final_prompt_issues(
            spec2, {**sl2, "slice_3": bad}, es.assemble_prompt(spec2, {**sl2, "slice_3": bad}),
            es.assemble_story(spec2, {**sl2, "slice_3": bad}))})
        # çığ yasakları değişmedi, depremde ayrı liste
        self.assertEqual(es.EVENT_BANNED_WORDS[es.AVALANCHE_SKI][0][0], "avalanche_banned")

    def test_people_close_to_camera(self):
        spec, sl = build(APT, "P1", "Q1")
        self.assertIn("close by: near the railing or in the street right below", es.people_line(spec))
        self.assertIn("run away from the collapsing buildings", es.people_line(spec))
        for t in ("Five residents run from the collapsing buildings near the railing.",
                  "Five people run from the collapsing buildings in the street right below."):
            self.assertFalse(codes(spec, {**sl, "slice_1_rest": t}) & {"slice_near_camera", "slice_flee"})
        far = "Five people run from the collapsing buildings down the avenue."
        self.assertIn("slice_near_camera", {i["rule"] for i in es.slice_issues(spec, {**sl, "slice_1_rest": far})})
        self.assertEqual(sk.count_range(APT, None), (3, 6))

    def test_forbidden_pairs_and_spot_exclusions(self):
        for e, tags in STRUCT.items():
            b = es.EVENT_BEATS[e]
            with self.subTest(event=e):
                self.assertEqual(b["excluded_pairs"], {(v, d) for v in b["slice_2"] for d in b["slice_3"]
                                                      if tags[v] & tags[d]})
                for bid in list(b["slice_2"]) + list(b["slice_3"]):
                    spots = {ROOF, BAL} - b["excluded_spots"].get(bid, set())
                    self.assertEqual(spots, {ROOF} if bid in HIGH else {ROOF, BAL}, bid)
        counts = {e: [len(es.allowed_pairs(e, None, s)) for s in (ROOF, BAL)] for e in EQ}
        self.assertEqual(counts, {APT: [13, 7], OLD: [13, 9]})

    def test_block_depth_two_with_fallback_never_runs_out(self):
        self.assertEqual({e: es.RECENT_BEAT_BLOCK_BY_EVENT[e] for e in EQ}, {APT: 2, OLD: 2})
        self.assertEqual(es.BEAT_BLOCK_FALLBACK_EVENTS, EQ)

        def worst(e, spot, k):
            b, ps = es.EVENT_BEATS[e], es.allowed_pairs(e, None, spot)
            return min(sum(1 for v, d in ps if v not in x2 and d not in x3)
                       for x2 in map(set, combinations(b["slice_2"], k))
                       for x3 in map(set, combinations(b["slice_3"], k)))
        for e in EQ:
            for spot in (ROOF, BAL):
                with self.subTest(event=e, spot=spot):
                    self.assertGreater(worst(e, spot, 1), 0)   # yedek derinlik her zaman aday bırakır
        self.assertEqual(worst(APT, BAL, 2), 0)   # yedeğin sebebi: balkonda 3 × 3, kalan tek çift yasak olabilir
        for spot in (ROOF,):
            self.assertGreater(worst(APT, spot, 2), 0)
        for spot in (ROOF, BAL):
            self.assertGreater(worst(OLD, spot, 2), 0)
        # gerçek akış: 300 seçim boyunca hiç aday tükenmez, son 2 (yedekte son 1) tekrar etmez
        rng = random.Random(3)
        for e in EQ:
            es._BEAT_MEMORY.clear()
            tags = []
            for _ in range(300):
                spot = rng.choice([ROOF, BAL])
                b2, b3 = es.choose_beats(e, None, spot, [], rng)
                if tags:
                    self.assertNotEqual(b2, tags[-1][0])
                    self.assertNotEqual(b3, tags[-1][1])
                es.remember_beats(e, es.beat_tag(b2, b3))
                tags.append((b2, b3))
        # diğer olaylarda yedek yok (davranış aynı)
        self.assertNotIn(es.AVALANCHE_FOREST, es.BEAT_BLOCK_FALLBACK_EVENTS)

    def test_all_combinations_pass_final_check(self):
        n = 0
        for e in EQ:
            for spot in (ROOF, BAL):
                for b2, b3 in es.allowed_pairs(e, None, spot):
                    for env in all_envs(e):
                        spec, sl = build(e, b2, b3, spot, people=3 + n % 4, setting=es.setting_line(env))
                        prompt = es.assemble_prompt(spec, sl)
                        issues = es.final_prompt_issues(spec, sl, prompt, es.assemble_story(spec, sl))
                        if issues:
                            self.fail(f"{e}/{spot}/{b2}+{b3}/{env}: {issues}")
                        self.assertLessEqual(len(prompt.split()), 175)
                        n += 1
        self.assertEqual(n, (13 + 7) * len(all_envs(APT)) + (13 + 9) * len(all_envs(OLD)))

    def test_environment_compatibility(self):
        self.assertEqual(es.EQ_ENV_AXES["light"], ("hazy dusty morning", "heavy grey overcast sky",
                                                   "late-afternoon low sun", "blue dawn light"))
        self.assertEqual(set(es.EQ_ENV_AXES["street"]), {"wide avenue", "narrow residential street",
                                                        "tree-lined square edge", "quiet residential street"})
        self.assertNotIn("narrow residential street", es.EQ_EVENT_STREETS[APT])
        self.assertNotIn("wide avenue", es.EQ_EVENT_STREETS[OLD])
        self.assertTrue(all("apartment" in c for c in es.EQ_EVENT_CITIES[APT]))
        self.assertTrue(all("stone" in c for c in es.EQ_EVENT_CITIES[OLD]))
        for e in EQ:
            envs = all_envs(e)
            self.assertTrue(envs)
            for env in envs:
                line = es.setting_line(env)
                with self.subTest(event=e, line=line):
                    self.assertLessEqual(len(line.split()), 15)
                    self.assertEqual(es.find_terms(LEAK, line), [])
                    for code, terms, *_ in es.EVENT_BANNED_WORDS[e]:
                        self.assertEqual(es.find_terms(terms, line), [])
                    if env["light"] == "hazy dusty morning":   # beyaz üstüne beyaz: koyu tonlu şehir
                        self.assertIn("dark", line)
                    else:
                        self.assertNotIn("dark", line)
                    if env["city"] == es.EQ_AVENUE_CITY:
                        self.assertEqual(env["street"], "tree-lined square edge")   # tekrar/çelişki yok
        self.assertEqual(es.environment_label({"city": "old brick-and-stone residential buildings",
                                               "street": "narrow residential street", "light": "blue dawn light",
                                               "spot": BAL}),
                         f"Ortam: şehir = old brick-and-stone residential buildings · sokak = narrow residential "
                         f"street · ışık = blue dawn light · kamera = {BAL}")

    def test_environment_lru_and_separate_from_avalanche(self):
        rng = random.Random(5)
        for e in EQ:
            es._EQ_ENV_MEMORY.clear()
            prev = []
            for _ in range(200):
                spot = es.choose_env_spot(e, [ROOF, BAL], rng)
                env = es.choose_environment(e, spot, "P1" if e == APT else "R2", "Q1" if e == APT else "T2", rng)
                if prev:
                    for axis in ("city", "street", "light", "spot"):
                        self.assertNotEqual(env[axis], prev[-1][axis], axis)
                es.remember_environment(env)
                prev.append(env)
            self.assertEqual({x["light"] for x in prev}, set(es.EQ_ENV_AXES["light"]))
        # çığ hafızası deprem seçimini etkilemez (ve tersi)
        es._ENV_MEMORY[:] = [{"mountain": "x", "village": "y", "light": "z", "spot": ROOF}]
        es._EQ_ENV_MEMORY.clear()
        self.assertIn(es.choose_env_spot(APT, [ROOF, BAL], random.Random(1)), (ROOF, BAL))
        es.remember_environment({"city": es.EQ_EVENT_CITIES[APT][0], "street": "wide avenue",
                                 "light": "blue dawn light", "spot": ROOF})
        self.assertEqual(len(es._ENV_MEMORY), 1)
        self.assertEqual(len(es._EQ_ENV_MEMORY), 1)
        es._ENV_MEMORY.clear()
        es._EQ_ENV_MEMORY.clear()

    def test_100_productions_each_event(self):
        import core.creative_pipeline as cp
        for e in EQ:
            es._BEAT_MEMORY.clear()
            es._EQ_ENV_MEMORY.clear()
            b = es.EVENT_BEATS[e]
            msgs, tags, envs, most, first_pass = [], [], [], 0, 0
            with self.subTest(event=e):
                for _ in range(100):
                    scene = asyncio.run(cp.build_creative_scene("earthquake_disasters", e, [], [], eq_gpt(msgs)))
                    t, spec, sl = scene["trace"], scene["structure"]["spec"], scene["structure"]["slices"]
                    pair = (spec["beat_2"], spec["beat_3"])
                    self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
                    self.assertNotIn(pair, b["excluded_pairs"])
                    for x in pair:
                        if x in HIGH:
                            self.assertEqual(t["spot"], ROOF)
                    if tags:
                        self.assertNotEqual(pair[0], tags[-1][0])
                        self.assertNotEqual(pair[1], tags[-1][1])
                    env = t["environment"]
                    if envs:
                        for axis in ("city", "street", "light", "spot"):
                            self.assertNotEqual(env[axis], envs[-1][axis], axis)
                    self.assertIn(es.setting_line(env), scene["prompt"])
                    self.assertIn(f"WEATHER: {es.env_weather(env)}", msgs[-1])
                    self.assertEqual(scene["structure"]["environment"], es.environment_label(env))
                    no_neg = scene["prompt"].lower().replace("no readable signs, text or flags", "")
                    self.assertEqual(es.find_terms(LEAK, no_neg), [])
                    n = len(scene["prompt"].split())
                    most = max(most, n)
                    self.assertLessEqual(n, 175)
                    self.assertIsNone(t["vehicle"])
                    self.assertNotIn("VEHICLE:", msgs[-1])
                    self.assertIn("WORD BUDGET:", msgs[-1])
                    self.assertIn("close by: near the railing", msgs[-1])
                    first_pass += len(t["attempts"]) == 1
                    tags.append(pair)
                    envs.append(env)
                self.assertEqual({x["spot"] for x in envs}, {ROOF, BAL})
                self.assertGreaterEqual(len(set(tags)), 12)
                self.assertEqual(first_pass, 100)

    def test_skeleton_texts(self):
        import core.prompt_generator as pg
        for e in EQ:
            s = sk.EVENT_SKELETONS[e]
            for spot in s["spots"]:
                story = sk.fill_skeleton(e, None, {"spot": spot, "weather": s["weather"][0], "count": 4,
                                                   "people": s["people"][0]})
                with self.subTest(event=e, spot=spot):
                    self.assertTrue(35 <= len(story.split()) <= 70, len(story.split()))
                    self.assertEqual(pg.event_fidelity_issues(e, story), [])
                    for code, terms, *_ in es.EVENT_BANNED_WORDS[e]:
                        self.assertEqual(es.find_terms(terms, story), [], story)


if __name__ == "__main__":
    unittest.main()
