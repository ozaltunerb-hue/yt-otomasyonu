#!/usr/bin/env python3
"""
🔥 Ateş hortumu kapısı (15 Eki 2026, Bahadır): Telegram 10:44 üretimi 3 denemede kapıdan geçmedi. GPT'nin doğru T6/U4
cümleleri "seçilen olay görünmüyor" diye reddedildi, sonraki denemeler 40-70 toplamını aştı (81, 73). Madde terimleri
anlam bazlı nesne + eylem gruplarına çevrildi (_FIRE_TOR_*, sadece bu olay), toplam 40-75. Ağ yok, Kie/GPT çağrısı yok.
REJECTED_REAL: gerçek GPT retleri. FREE: madde metninden farklı kurulmuş serbest cümleler. HELD_OUT: ilk grup tasarımından
SONRA yazılan kontrol cümleleri (ilk ölçümde 3/36 ret; "upward", "from the road" eklendi).
"""
import asyncio
import os
import random
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.skeleton_pipeline as sk

E = es.FIRE_TORNADO
SPOTS = ("Overlook above the burning valley road", "Balcony of a roadside house")
VEHICLES = ("pickup truck", "small car", "white van", "SUV")

REJECTED_REAL = {
    "T6": [
        'Flaming debris collides with the SUV, causing it to skid violently until it halts blocking the road.',
        "A shower of fiery debris smashes into the SUV's side, causing it to spin wildly before coming to rest across the road.",
        "Flaming debris crashes into the SUV's flank, causing it to spin wildly before grinding to a halt in the road.",
    ],
    "U4": [
        'The tornado engulfs a heap of burning brush, ejecting it in a blazing arc of sparks onto the roadway.',
        'A fierce surge of the tornado draws in a burning brush pile, hurling it across the road in a dazzling spray of embers.',
        'The tornado draws up burning brush, hurling it across the road in a spectacular shower of fiery sparks, still spinning.',
    ],
}
FREE = {
    "T1": [
        'The swirling flames heave the pickup truck off the asphalt and hurl it against a blazing tree.',
        'Caught in the fiery vortex, the van rises off the road and is thrown into a burning pine.',
        'The fire whirl yanks the SUV into the air and smashes it into a tree engulfed in flames.',
        'The small car is pulled off the ground by the spinning fire and slammed into a flaming trunk.',
        'Whirling flames pluck the van from the road, tossing it into a tree that is already ablaze.',
    ],
    "T2": [
        "A flaming limb flung by the fire whirl crashes through the van's windshield.",
        'The tornado hurls a blazing branch straight into the SUV, shattering its front glass.',
        'A burning bough whips out of the vortex and caves in the windscreen of the small car.',
        "Torn loose by the spinning fire, a glowing branch punches through the pickup truck's windshield.",
        'A fiery branch launched by the tornado slams into the van, cracking its windshield to pieces.',
    ],
    "T3": [
        'The SUV rises into the fiery column, twirls around, and slams back onto the asphalt amid a burst of sparks.',
        'The van is carried aloft, rotating wildly, then smashes onto the road as sparks explode around it.',
        'Lifted high by the vortex, the small car whirls end over end before plunging onto the road in a spray of embers.',
        'The fire whirl hoists the pickup truck skyward, spins it, and drops it hard onto the road, scattering sparks.',
        'The tornado sucks the SUV off the ground, sends it spiraling, and hurls it down onto the road in a cascade of sparks.',
    ],
    "T4": [
        'The van slides sideways while the fire whirl sweeps over the road behind it, pelting its roof with glowing embers.',
        'As the flaming vortex passes behind the SUV, it fishtails across the lane under a rain of sparks on its roof.',
        'The pickup truck skids broadside as the burning tornado crosses at its back, showering cinders over the roof.',
        'Behind the small car the fire tornado cuts across the road, and the car slews sideways as embers pelt its roof.',
        'The SUV drifts sideways across the asphalt while the swirling fire passes behind, scattering embers onto its roof.',
    ],
    "T5": [
        'The spinning flames pin the van against the guardrail until its bonnet bursts into flames.',
        'Whirling fire drives the SUV into the crash barrier, and flames take hold of its hood.',
        'The pickup truck is pushed hard into the roadside barrier by the vortex as its hood ignites.',
        "Forced against the guardrail by the fiery whirl, the small car's front end erupts in flames.",
        'The swirling inferno rams the SUV into the metal railing, setting the hood ablaze.',
    ],
    "T6": [
        'Burning wreckage strikes the van broadside, sending it into a spin until it stalls across the lane.',
        "A blazing chunk of debris hits the pickup truck's flank and it whips around, ending sideways across the road.",
        'Fiery debris pounds the side of the small car, which slews around and comes to rest blocking the road.',
        "A mass of burning debris rams the SUV's door, knocking it into a skid that leaves it stranded across the asphalt.",
        "Flaming fragments batter the van's side panel, spinning it until it halts crosswise on the road.",
    ],
    "U1": [
        'The fiery vortex peels the blazing roof from a house and flings burning chunks all over the street.',
        'A burning house loses its roof to the fire whirl, its flaming fragments strewn across the road.',
        'The tornado wrenches the flaming roof off a home, sending fiery shards raining across the street.',
        "The spinning fire tears away a house's burning roof and hurls its glowing pieces over the street.",
        "With a violent twist, the fire tornado lifts a house's roof, already ablaze, and showers the street with burning debris.",
    ],
    "U2": [
        'The flaming vortex rips a blazing tree out by its roots and hurls it along the road.',
        'A burning pine is torn from the ground by the fire whirl and thrown down the roadway.',
        'The tornado yanks a flaming tree from the earth, sending it tumbling down the road.',
        'Roots and all, a burning oak is pulled up by the spinning fire and tossed down the highway.',
        'The fire tornado wrenches a blazing tree loose and launches it far down the road.',
    ],
    "U3": [
        'The spinning fire rips a billboard off its posts and flings it to the side.',
        'A roadside billboard is torn from its frame by the swirling flames and thrown away.',
        'The fire whirl wrenches a large advertising board loose and tosses it across the shoulder.',
        'Swirling flames snap a billboard from its legs and hurl it off the road.',
        'The tornado of fire peels a burning billboard off its stand and sends it flying aside.',
    ],
    "U4": [
        'The fire whirl inhales a heap of blazing scrub and flings it over the road in a burst of sparks.',
        'A mound of burning brush is pulled into the vortex and sprayed across the road as a shower of embers.',
        'The tornado lifts a pile of flaming undergrowth and blasts it across the asphalt in a jet of sparks.',
        'Burning shrubs are sucked into the spinning column and hurled over the road in a cascade of glowing cinders.',
        'The vortex scoops up a stack of smoldering brushwood and spews it across the road in a fountain of sparks.',
    ],
    "U5": [
        'The fire whirl rips a length of blazing fence loose and sweeps it over the field.',
        'A section of burning fencing is torn free by the vortex and carried across the meadow.',
        'The spinning flames wrench a flaming stretch of wooden fence away and drag it across the field.',
        'The tornado yanks a burning fence panel from the ground and hurls it across the open field.',
        'A stretch of fence, already alight, is pulled up by the fire tornado and carried over the grassland.',
    ],
    "U6": [
        'The fire whirl rolls over a parked caravan and flips it aside amid billowing flames and smoke.',
        'A parked trailer is overturned by the passing vortex, vanishing in a cloud of fire and smoke.',
        'The spinning flames engulf a parked camper and throw it to the side in a burst of smoke and fire.',
        'The tornado crosses a parked trailer and knocks it over in a swirl of flames and black smoke.',
        'The burning vortex slams into a parked caravan and tips it onto its side inside a cloud of fire and smoke.',
    ],
}
HELD_OUT = {
    "T1": [
        'The roaring fire vortex tears the white van from the road and hurls it into a blazing pine.',
        'The pickup truck is ripped from the asphalt by the flames and thrown against a burning tree, wedged in its branches.',
        'The fiery whirlwind snatches the small car upward, smashing it into the trunk of a flaming tree.',
    ],
    "T2": [
        'A flaming branch torn off by the tornado crashes into the SUV, splintering its windshield.',
        "The vortex flings a burning limb that bursts through the white van's windscreen.",
        "A blazing tree branch whirls out of the fire and shatters the pickup truck's front window.",
    ],
    "T3": [
        'The fire tornado lifts the SUV high, spinning it violently before slamming it back down on the road in a burst of sparks.',
        'Swept into the air, the white van twists and tumbles, then crashes onto the road showering sparks.',
        'The small car is hurled upward by the inferno, spirals around, and smashes down onto the road amid sparks.',
    ],
    "T4": [
        'The SUV skids across the road as the fire tornado passes behind it, embers raining onto its roof.',
        'With the fiery column crossing behind, the white van slides sideways while sparks pelt its roof.',
        'The pickup truck fishtails across the lane as burning embers scatter over its roof from the tornado behind it.',
    ],
    "T5": [
        'The whirling flames force the SUV into the guardrail, and its hood bursts into flames.',
        'The white van is slammed against the guardrail by the tornado as fire spreads across its hood.',
        "Pinned against the barrier by the swirling inferno, the small car's hood starts to burn.",
    ],
    "T6": [
        "A burst of flaming debris rams into the SUV's side, sending it spinning to a stop across the lane.",
        'Burning wreckage smashes the white van broadside and it spins out, stopping across the road.',
        'Fiery debris hammers into the side of the pickup truck, which whips around and halts sideways on the road.',
    ],
    "U1": [
        'The fire tornado tears the flaming roof from a house, scattering burning shingles across the street.',
        "A house's blazing roof is ripped away by the vortex and its fiery pieces rain over the street.",
        'The swirling flames strip the roof off a burning home and fling its fragments into the street.',
    ],
    "U2": [
        'The fire tornado rips a flaming tree from the ground and throws it along the road.',
        'A burning tree is uprooted by the vortex and hurled down the roadway.',
        'The fiery whirl tears a blazing pine out of the earth and sends it crashing down the road.',
    ],
    "U3": [
        'The swirling flames rip a billboard off its supports and fling it aside.',
        'A burning billboard is torn loose by the fire tornado and hurled across the roadside.',
        'The vortex wrenches a flaming billboard from its frame and tosses it away.',
    ],
    "U4": [
        'The fire tornado sucks in a pile of burning brush and sprays it across the road in a fountain of sparks.',
        'A heap of flaming scrub is drawn into the vortex and spat out across the road in a burst of embers.',
        'The tornado swallows a burning brush pile and hurls it over the road in a glowing shower of sparks.',
    ],
    "U5": [
        'The fire tornado rips a burning stretch of fence away and carries it over the field.',
        'A section of flaming fence is torn loose by the vortex and swept across the field.',
        'The swirling flames tear a blazing fence apart and hurl the pieces across the field.',
    ],
    "U6": [
        'The fire tornado rolls over a parked trailer and flips it aside in a cloud of fire and smoke.',
        'A parked caravan is tossed aside by the vortex, disappearing in flames and smoke.',
        'The swirling flames sweep across a parked trailer, overturning it in a burst of fire and smoke.',
    ],
}


def slot(bid):
    return "slice_2" if bid[0] == "T" else "slice_3"


def terms(bid):
    return es.EVENT_BEATS[E][slot(bid)][bid]["terms"]


def with_vehicle(text, vehicle):
    for v in ("pickup truck", "small car", "white van", "SUV", "van"):
        if v in text:
            return text.replace("white van" if v == "van" and "white van" in text else v, vehicle, 1)
    return text


def build(b2, b3, vehicle="SUV", spot=SPOTS[0], s2=None, s3=None, s1=None, people=5):
    spec = es.build_spec(E, None, spot, None, b2, b3, vehicle, people)
    word = es.NUMBER_WORDS[people].capitalize()
    sl = {"slice_1_rest": s1 or f"{word} people run from the fire tornado along the roadside.",
          "slice_2": s2 or with_vehicle(FREE[b2][0], vehicle), "slice_3": s3 or FREE[b3][0]}
    return spec, sl


class TestFireTornadoGate(unittest.TestCase):
    def test_rejected_real_gpt_sentences_pass(self):
        # 15 Eki 10:44: 3 denemede reddedilen gerçek GPT cümleleri artık kendi maddesinde geçer
        for bid, sents in REJECTED_REAL.items():
            for t in sents:
                with self.subTest(beat=bid, text=t):
                    self.assertEqual(es.missing_term_groups(terms(bid), t), [])
        for t in REJECTED_REAL["T6"]:
            spec, sl = build("T6", "U4", "SUV", s2=t, s3=REJECTED_REAL["U4"][1])
            with self.subTest(text=t):
                codes = {i["rule"] for i in es.slice_issues(spec, sl)}
                self.assertFalse(codes & {"beat_terms", "beat_vehicle"}, codes)

    def test_free_paraphrases_pass_every_beat(self):
        ids = [b for sl in ("slice_2", "slice_3") for b in es.EVENT_BEATS[E][sl]]
        self.assertEqual(sorted(FREE), sorted(ids))
        self.assertEqual(sorted(HELD_OUT), sorted(ids))
        for bid in ids:
            beat = es.beat_text(E, slot(bid), bid, "SUV").lower()
            self.assertGreaterEqual(len(FREE[bid]), 5)
            for t in FREE[bid] + HELD_OUT[bid]:
                with self.subTest(beat=bid, text=t):
                    self.assertEqual(es.missing_term_groups(terms(bid), t), [])
                    self.assertNotEqual(t.lower().rstrip("."), beat)
                    self.assertNotEqual(t.lower().split()[:4], beat.split()[:4])   # farklı kurulmuş
                    self.assertTrue(10 <= len(t.split()) <= 24)
                    if slot(bid) == "slice_2":
                        for v in VEHICLES:   # araç kapısı da geçer
                            vt = dict(es.event_vehicles(E, None))[v]
                            self.assertTrue(es.find_terms(vt, with_vehicle(t, v)), (v, t))

    def test_no_false_positive_between_beats(self):
        # Bir maddenin cümlesi başka maddenin kapısından geçmez. İstisna: yasak çiftler (T1/U2, T2/U2, T4/U4) aynı
        # videoda hiç birlikte seçilmez.
        b = es.EVENT_BEATS[E]
        ex = b["excluded_pairs"] | {(d, v) for v, d in b["excluded_pairs"]}
        ids = list(b["slice_2"]) + list(b["slice_3"])
        for x in ids:
            for o in ids:
                if o == x or (x, o) in ex:
                    continue
                for t in FREE[o] + HELD_OUT[o] + REJECTED_REAL.get(o, []):
                    with self.subTest(beat=x, other=o, text=t):
                        self.assertTrue(es.missing_term_groups(terms(x), t))
        # "spinning/whirling" hortumun sıfatı: T1 cümlesi T3 (iniş yok), U1 cümlesi T6 (araç yok) sayılmaz
        self.assertTrue(es.missing_term_groups(terms("T3"), FREE["T1"][3]))
        self.assertTrue(es.missing_term_groups(terms("T6"), FREE["U1"][4]))

    def test_event_missing_still_rejected(self):
        bad = {"T1": "The van is pushed into a burning tree by the swirling flames.",
               "T3": "The SUV spins on the road as the flames swirl around it.",
               "T5": "The SUV is shoved against the guardrail by the whirling wind.",
               "T6": "The SUV spins and stops across the road as the flames swirl.",
               "U3": "The wind tears a billboard from its supports and hurls it aside.",
               "U4": "A pile of burning brush glows beside the road.",
               "U6": "A parked trailer stands near the burning road."}
        for bid, t in bad.items():
            with self.subTest(beat=bid, text=t):
                self.assertTrue(es.missing_term_groups(terms(bid), t))

    def test_term_lists_only_fire_tornado(self):
        # _FIRE_TOR_* listeleri sadece ateş hortumunda; diğer yangın olayları ortak _FIRE_* listelerini kullanır
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(es))
        node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(getattr(t, "id", None) == "EVENT_BEATS" for t in n.targets))
        for k, v in zip(node.keys, node.values):
            names = {n.id for n in ast.walk(v) if isinstance(n, ast.Name)}
            tor = {n for n in names if n.startswith("_FIRE_TOR_")}
            with self.subTest(event=getattr(k, "id", None)):
                if getattr(k, "id", None) == "FIRE_TORNADO":
                    self.assertTrue(tor)
                else:
                    self.assertFalse(tor)

    def test_total_words_75_only_fire_tornado(self):
        self.assertEqual(es.TOTAL_WORDS, (40, 70))
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[E], (40, 75))
        self.assertNotIn(es.FACADE_FIRE, es.TOTAL_WORDS_BY_EVENT)
        key = len(es.EVENT_KEY_VISUAL[E].split())

        def story(total):
            s1 = "Five people run from the fire tornado along the roadside now."
            s2 = "Burning debris slams into the SUV, which spins to a halt."
            base = "The tornado lifts burning brush and hurls it over the road in sparks".split()
            need = total - key - len(s1.split()) - len(s2.split())
            return {"slice_1_rest": s1, "slice_2": s2, "slice_3": " ".join((base + ["again"] * 40)[:need])}
        spec = es.build_spec(E, None, SPOTS[0], None, "T6", "U4", "SUV", 5)
        for total, ok in ((73, True), (75, True), (76, False), (81, False)):
            sl = story(total)
            self.assertEqual(len(es.plain_story(spec, sl).split()), total)
            with self.subTest(total=total):
                self.assertEqual("total_words" not in {i["rule"] for i in es.slice_issues(spec, sl)}, ok)

    def test_prompt_never_exceeds_175_words(self):
        # 175 kelime sınırı değişmedi; ateş hortumunda en uzun stil eki + 75 + 3 etiket altında kalır
        longest = max(len(es.style_suffix(E, None, s, None, None).split()) for s in SPOTS)
        self.assertEqual(sorted(sk.EVENT_SKELETONS[E]["spots"]), sorted(SPOTS))
        self.assertLessEqual(longest + 75 + 3, es.VOLC_MAX_PROMPT_WORDS)
        self.assertEqual(es.VOLC_MAX_PROMPT_WORDS, 175)

    def test_no_word_budget_line(self):
        # GPT'ye kural eklenmedi: dilim bütçesi satırı sadece çığ/deprem; 75 GPT'ye sadece ret geri bildiriminde gider
        self.assertNotIn(E, es.BUDGET_EVENTS)
        self.assertEqual(es.word_budget_line({"event": E, "key_visual": es.EVENT_KEY_VISUAL[E]}), "")

    def test_people_gate_unchanged(self):
        spec, sl = build("T6", "U4")
        codes = {i["rule"] for i in es.slice_issues(spec, {**sl, "slice_1_rest": "The smoke hangs over the road."})}
        self.assertTrue(codes & {"slice_flee", "slice_people"}, codes)
        self.assertFalse({i["rule"] for i in es.slice_issues(spec, sl)} - {"total_words"})

    def test_200_productions_free_paraphrase(self):
        # Sahte GPT madde metnini değil serbest/gerçek cümlelerden birini yazar; ilk denemede en az %90
        import core.creative_pipeline as cp
        rng = random.Random(15)
        pool = {b: FREE[b] + HELD_OUT[b] + REJECTED_REAL.get(b, []) for b in FREE}
        people = ["{w} people run from the fire tornado along the roadside.",
                  "{w} people flee from the fire tornado down the road.",
                  "{w} drivers abandon their cars and run from the fire tornado.",
                  "{w} people sprint away from the fire tornado across the field."]

        async def gpt(system, user, **kw):
            line = dict(l.split(": ", 1) for l in user.splitlines() if ": " in l)
            w = line["PEOPLE RUNNING AWAY"].split()[0].capitalize()
            v = line["VEHICLE"].strip()
            b2 = next(b for b in es.EVENT_BEATS[E]["slice_2"]
                      if es.beat_text(E, "slice_2", b, v) == line["4-9s EVENT"])
            b3 = next(b for b in es.EVENT_BEATS[E]["slice_3"] if es.beat_text(E, "slice_3", b) == line["9-15s EVENT"])
            return {"slice_1_rest": rng.choice(people).format(w=w),
                    "slice_2": with_vehicle(rng.choice(pool[b2]), v), "slice_3": rng.choice(pool[b3])}
        es._BEAT_MEMORY.clear()
        first, longest = 0, 0
        for _ in range(200):
            scene = asyncio.run(cp.build_creative_scene("fire_disasters", E, [], [], gpt))
            spec, sl = scene["structure"]["spec"], scene["structure"]["slices"]
            self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
            longest = max(longest, len(scene["prompt"].split()))
            first += len(scene["trace"]["attempts"]) == 1
        self.assertGreaterEqual(first, 180)
        self.assertLessEqual(longest, 175)
        es._BEAT_MEMORY.clear()


if __name__ == "__main__":
    unittest.main()
