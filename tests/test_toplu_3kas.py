#!/usr/bin/env python3
"""3 Kasım 2026 toplu düzeltme (Bahadır): kilit kuralı + 8 aşama. Ağ yok, Kie/GPT çağrısı yok (sahte GPT).

- Kilit: 5 kanıtlanmış olayın (orman yangını, helikopter, hortum karaya vurur, volkan bombaları, heyelan köy)
  prompt_snapshot'ı baseline ile birebir aynı (diff = 0).
- Aşama 1: VERBATIM_SLICES (kilitsiz olaylarda AÇIK): GPT farklı dilim metni döndürse bile son prompt seçilen havuz
  metnini birebir taşır. Kilitli 5 olayda KAPALI: GPT dilimi HEAD'deki gibi korunur.
- Devam (3 Kas): kruvaziyer ve plaj & sahil pasif; meteor kilit cümlesi muafiyeti; GPT insan satırı sadece meteorda
  değişti (HEAD fixture'ı: tests/fixtures/people_line_head.json); cephe M12 araç öğesi (deneme).
- Aşama 2: zayıf öğeler pasif (seçilmez), yeni güçlü öğeler deneme (en fazla %20, art arda gelmez).
- Aşama 3: sel ve dev dalgada insan ekseni (run/sprint, somut hedef, yokuş yukarı yok, I1-I2 kanıtlı).
- Aşama 4: yeni RED kuralları (her biri 1 red + 1 geçen); kilitli olayların kod yedeği reddedilmez; seawall kadrajı pasif.
- Aşama 5: çamur seli açılışı ıslak/akan/yağmurlu, hareket ilk karede.
- Aşama 6: meteor K4 kadraj, O5 ortam, yeni ışık deneme; insanlar kıyı yolunda/teraslarda; CGI ve kamera hareketi kapısı.
- Aşama 7: deprem modern ortamlar; eski sokak ve eski taş ortamları pasif.
- Aşama 8: menü callback -> olay eşlemesi.
"""
import asyncio
import collections
import logging
import os
import random
import re
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.frame_axis as fx   # noqa: E402
import core.proven_axes as pa   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402

LOCKED = (es.WILDFIRE, es.HELICOPTER, es.LANDFALL, es.VOLCANIC_BOMBS, es.VILLAGE)
UNLOCKED = tuple(e for e in ps.active_events() if e not in LOCKED)
BAD_2 = "The car keeps rolling away and obliterates the street in a fiery hail of debris."
BAD_3 = "Everything is lifted effortlessly as the roar of devastation spreads further."


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)


def _human(msg: str) -> str:
    m = re.search(r"PEOPLE RUNNING AWAY: (\w+)", msg)
    w = m.group(1).capitalize() if m else "Four"
    if "terraces right below" in msg:   # meteor yakınlık satırı
        return f"{w} people run across the terraces right below."
    return f"{w} people run away in the street right below."


async def _bad_slices_gpt(system, msg, **kw):
    return {"slice_1_rest": _human(msg), "slice_2": BAD_2, "slice_3": BAD_3}


def _sequence(event: str, n: int, seed: int) -> list[dict]:
    """n ardışık üretim (kod yedeği yolu), sahte Notion eksen geçmişiyle (üretimdeki LRU yolu)."""
    ps.reset_memory()
    random.seed(seed)
    hist, recs, rows = [], [], []
    for _ in range(n):
        sc = ps.build(event, history=list(hist), axes_loader=lambda d: list(recs))
        recs.append({"eksenler": sc["axes_json"], "combo_key": sc["combo_key"], "prompt": sc["prompt"]})
        hist.append(sc["combo_key"])
        rows.append(sc)
    return rows


# ── KİLİT ─────────────────────────────────────────────────────────────────────────────────────────────────────────
class TestLockedSnapshot(_Quiet):
    def test_locked_events_unchanged(self):
        """Kilitli 5 olayın prompt_snapshot'ı baseline ile birebir aynı (20 tohum)."""
        base = ps.load_baseline()
        now = ps.snapshot_all(list(LOCKED))
        self.assertEqual(ps.diff({e: base[e] for e in LOCKED}, now), {})

    def test_locked_list(self):
        # 6 Kas: + sel, anıt, ateş hortumu (tests/test_kilit_6kas.py). Bu dosyadaki LOCKED = ilk 5 (VERBATIM kapalı olanlar)
        self.assertEqual(set(es.VERBATIM_OFF_EVENTS), set(LOCKED))
        self.assertTrue(set(LOCKED) <= set(es.LOCKED_EVENTS))

    def test_locked_pools_untouched(self):
        """Kilitli olaylarda pasif/deneme öğe ya da insan ekseni yok. Tek istisna (3 Kas, Bahadır onaylı): helikopter G7,
        bombalar T5 pasif (TestLockPassiveException)."""
        for e in LOCKED:
            self.assertEqual(es.DISABLED_BEATS.get(e, set()), es.LOCKED_PASSIVE_EXCEPTION.get(e, set()))
            self.assertNotIn(e, es.TRIAL_BEATS)
            self.assertNotIn(e, es.PEOPLE_AXIS_EVENTS)
            for axis in pa.EXTRA_TRIALS.values():
                self.assertNotIn(e, axis)


# ── AŞAMA 1 ───────────────────────────────────────────────────────────────────────────────────────────────────────
class TestVerbatimSlices(_Quiet):
    def test_flag_on_unlocked_off_locked(self):
        for e in UNLOCKED:
            self.assertTrue(es.verbatim_on(e), e)
        for e in LOCKED:
            self.assertFalse(es.verbatim_on(e), e)

    def test_locked_gpt_slices_kept(self):
        """Kilitli 5 olayda GPT'nin dilimleri atılmaz (HEAD davranışı); kilitsizde atılır."""
        async def gpt(system, msg, **kw):
            return {"slice_1_rest": _human(msg), "slice_2": BAD_2, "slice_3": BAD_3}
        for e in ps.active_events():
            spec = _spec(e)
            try:
                _, attempts = asyncio.run(cp.write_slices(spec, "P", "W", [], gpt, max_attempts=1))
            except cp.CreativeStoryError as err:
                attempts = err.attempts
            sl = attempts[0]["slices"]
            with self.subTest(event=e):
                if e in LOCKED:
                    self.assertEqual((sl["slice_2"], sl["slice_3"]), (BAD_2, BAD_3))
                    self.assertNotIn("gpt_slices", attempts[0])
                else:
                    self.assertIn(sl["slice_2"], es.verbatim_forms(spec, "slice_2"))
                    self.assertEqual(attempts[0]["gpt_slices"]["slice_2"], BAD_2)

    def test_gpt_slices_replaced_by_pool_text(self):
        """Her aktif olayda GPT farklı dilim metni döndürse bile son prompt havuz metnini içerir."""
        real = cp.record_story_source
        cp.record_story_source = lambda entry: None
        try:
            for e in UNLOCKED:
                for seed in (1, 2, 3):
                    with self.subTest(event=e, seed=seed):
                        ps.reset_memory()
                        random.seed(seed)
                        sc = asyncio.run(cp.build_creative_scene(None, e, [], [], _bad_slices_gpt))
                        spec, sl = sc["structure"]["spec"], sc["structure"]["slices"]
                        for slot in ("slice_2", "slice_3"):
                            self.assertIn(sl[slot], es.verbatim_forms(spec, slot))
                            self.assertIn(sl[slot], sc["prompt"])
                        self.assertNotIn(BAD_2, sc["prompt"])
                        self.assertNotIn(BAD_3, sc["prompt"])
        finally:
            cp.record_story_source = real

    def test_gpt_path_used_with_pool_text(self):
        """GPT'nin insan cümlesi geçerliyse hikâye kaynağı GPT, dilimler yine havuzdan."""
        real = cp.record_story_source
        cp.record_story_source = lambda entry: None
        try:
            ps.reset_memory()
            random.seed(4)
            sc = asyncio.run(cp.build_creative_scene(None, es.TIDAL, [], [], _bad_slices_gpt))
        finally:
            cp.record_story_source = real
        self.assertEqual(sc["structure"]["story_source_kind"], "gpt")
        self.assertIn("gpt_slices", sc["trace"]["attempts"][-1])
        self.assertEqual(sc["trace"]["attempts"][-1]["gpt_slices"]["slice_2"], BAD_2)

    def test_verbatim_gate_rejects_rewrite(self):
        ps.reset_memory()
        random.seed(2)
        sc = ps.build(es.FLOOD)
        spec, sl = sc["structure"]["spec"], dict(sc["structure"]["slices"])
        self.assertEqual(es.verbatim_issues(spec, sl), [])
        sl["slice_3"] = sl["slice_3"].replace(".", " in seconds.")
        codes = {i["rule"] for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl),
                                                            es.assemble_story(spec, sl))}
        self.assertIn("verbatim_slice", codes)

    def test_flag_off_keeps_gpt_text(self):
        spec = ps.build(es.FLOOD)["structure"]["spec"]
        old = es.VERBATIM_SLICES[es.FLOOD]
        es.VERBATIM_SLICES[es.FLOOD] = False
        try:
            sl = {"slice_1_rest": "a.", "slice_2": BAD_2, "slice_3": BAD_3}
            self.assertEqual(es.apply_verbatim(spec, sl), sl)
            self.assertEqual(es.verbatim_issues(spec, sl), [])
        finally:
            es.VERBATIM_SLICES[es.FLOOD] = old

    def test_fallback_is_verbatim(self):
        """Kod yedeği (snapshot yolu) dilimleri zaten birebir havuz metni: kilitli olaylarda bayrak snapshot'ı değiştirmez."""
        for e in ps.active_events():
            for seed in range(1, 6):
                ps.reset_memory()
                random.seed(seed)
                sc = ps.build(e)
                spec, sl = sc["structure"]["spec"], sc["structure"]["slices"]
                self.assertEqual(es.verbatim_issues(spec, sl), [], (e, seed))


# ── AŞAMA 2 ───────────────────────────────────────────────────────────────────────────────────────────────────────
class TestWeakPassive(_Quiet):
    def test_disabled_and_trial_sets(self):
        # 3 Kas (sel su kontrolü): sel pasif ve deneme listeleri test_sel_su_3kas'ta
        self.assertEqual(es.DISABLED_BEATS, {es.FLOOD: {"D2", "D4", "V4", "V3", "V5", "V6", "V7", "V8", "D3", "D8",
                                                        "D9"}, es.TIDAL: {"W2", "W6", "W8", "T6", "T4", "W9", "T1"},
                                             es.FACADE_FIRE: {"N4", "M6"},
                                             es.HELICOPTER: {"G7"}, es.VOLCANIC_BOMBS: {"T5"},   # kilit istisnası
                                             es.LIBERTY: {"B4", "B6"},   # 4 Kas (4): 4-9s'te araç yok
                                             # 6 Kas: havuz temizliği (tests/test_kilit_6kas.py)
                                             es.FIRE_TORNADO: {"T5", "T6", "U6", "U10"},
                                             es.AVENUE: {"P5", "P7"},
                                             # 6 Kas (2): kalan havuz temizliği (tests/test_havuz_6kas_2.py)
                                             es.PYROCLASTIC: {"Q2", "P6", "Q6"}, es.MARINA_TORNADO: {"Y5", "Z7"},
                                             es.METEOR: {"W2"}, es.MUDSLIDE: {"H3"}, es.SLOPE: {"R3", "R6"}})
        self.assertEqual(es.TRIAL_BEATS, {es.FLOOD: {"D10", "V9", "V10", "V11", "V12", "D12", "D13", "D14", "D15",
                                                     "D16", "D17", "D18"},
                                          es.TIDAL: {"W9"}, es.FACADE_FIRE: {"N7", "M12"},
                                          es.PYROCLASTIC: {"Q7", "Q8"}, es.METEOR: {"W5", "W6"},   # 6 Kas (2)
                                          # 4 Kas (B2): Özgürlük Anıtı tüm öğeler DENEME
                                          es.LIBERTY: {"B1", "B2", "B3", "B4", "B5", "B6", "C1", "C2", "C3", "C4", "C6"}})
        for e, off in es.DISABLED_BEATS.items():   # silinmedi: havuzda duruyor
            pool = set(es.EVENT_BEATS[e]["slice_2"]) | set(es.EVENT_BEATS[e]["slice_3"])
            self.assertTrue(off <= pool)

    def test_disabled_never_selected(self):
        for e in es.DISABLED_BEATS:
            for v, d in es.allowed_pairs(e, "riviera" if e in sk.REGION_VIEW_EVENTS else None, "x"):
                self.assertNotIn(v, es.DISABLED_BEATS[e])
                self.assertNotIn(d, es.DISABLED_BEATS[e])

    def test_new_finals_strong(self):
        weak = ("dumpster", "lamppost", "awning", "shop window", "bicycle", "retreat", "steam", "brake", "destruct",
                "devastat", "low wall")
        for e, ids in es.TRIAL_BEATS.items():
            for bid in ids:
                slot = "slice_3" if bid in es.EVENT_BEATS[e]["slice_3"] else "slice_2"
                text = es.EVENT_BEATS[e][slot][bid]["text"]
                self.assertFalse(es.pool_lint_hits(text), text)
                self.assertFalse([w for w in weak if w in text], text)

    def test_trial_share_and_no_repeat(self):
        for e in es.TRIAL_BEATS:
            if es.dogrulama_on(e):   # 3 Kas: SEL_DOGRULAMA açıkken selde deneme mekanizması yok (test_sel_su_3kas)
                continue   # 4 Kas: OZGURLUK_DOGRULAMA da (test_sel_ozgurluk_4kas)
            rows = _sequence(e, 60, 11)
            flags = [any(x in es.TRIAL_BEATS[e] for x in r["trace"]["beats"].split("+")) for r in rows]
            # beklenen ~%17 (en fazla %20 olasılık); 3 Kas SEL_DOGRULAMA: selde en fazla %50 (art arda yok: ~%33)
            self.assertLessEqual(sum(flags) / len(flags), 0.55 if e == es.FLOOD else 0.25, e)
            self.assertFalse(any(a and b for a, b in zip(flags, flags[1:])), e)
            for r in rows:
                self.assertFalse(set(r["trace"]["beats"].split("+")) & es.DISABLED_BEATS[e])

    def test_facade_vehicle_trial(self):
        """M6 pasif; yerine M12 (park hâlindeki araç alevler içinde, araç hareket etmez) deneme ve kapılardan geçer."""
        self.assertTrue(es.uses_vehicle(es.FACADE_FIRE))
        text = es.EVENT_BEATS[es.FACADE_FIRE]["slice_2"]["M12"]["text"]
        for bad in ("spin", "spun", "lift", "roll", "tumbl", "flip"):
            self.assertNotIn(bad, text)
        rows = _sequence(es.FACADE_FIRE, 60, 2)
        m12 = [r for r in rows if r["trace"]["beats"].startswith("M12+")]
        self.assertTrue(m12)
        for r in m12:
            spec, sl = r["structure"]["spec"], r["structure"]["slices"]
            self.assertIn(spec["vehicle"], sl["slice_2"])
            self.assertEqual(es.final_prompt_issues(spec, sl, r["prompt"], r["story"]), [])
        spec = m12[0]["structure"]["spec"]
        for v in es.EVENT_BEATS[es.FACADE_FIRE]["slice_3"]:   # her izinli çiftte kod yedeği sığar ve geçer
            if ("M12", v) in es.EVENT_BEATS[es.FACADE_FIRE]["excluded_pairs"] or v in es.DISABLED_BEATS[es.FACADE_FIRE]:
                continue
            s2 = {**spec, "beat_3": v}
            cands = es.fallback_candidates(s2)
            self.assertTrue(cands, v)
            self.assertEqual(es.final_prompt_issues(s2, cands[0], es.assemble_prompt(s2, cands[0]),
                                                    es.assemble_story(s2, cands[0])), [])


# ── AŞAMA 3 ───────────────────────────────────────────────────────────────────────────────────────────────────────
class TestPeopleAxis(_Quiet):
    def test_people_rule_and_lines(self):
        for e in (es.FLOOD, es.TIDAL):   # 6 Kas (kilit): 4 Kas hikâye ekseni pasif, selde kişi kuralı geri
            self.assertTrue(es.has_people_rule(e))
            self.assertEqual(sk.count_range(e, None), (3, 6))
            lines = es.FALLBACK_PEOPLE[e]
            self.assertGreaterEqual(len(lines), 6)
            for t in lines:
                low = t.lower()
                self.assertTrue(t.startswith("{N} "), t)
                self.assertTrue(re.search(r"\b(run|sprint)\b", low), t)
                for bad in ("scatter", "scramble", "dash", "uphill", "higher", "up the street", "flee", "safety"):
                    self.assertNotIn(bad, low, t)
        self.assertEqual(es.FALLBACK_PEOPLE[es.TIDAL][:2], (es.FALLBACK_PEOPLE_RETIRED[es.TIDAL][0],
                                                            es.FALLBACK_PEOPLE_RETIRED[es.TIDAL][4]))

    def test_rotation(self):
        for e in (es.FLOOD, es.TIDAL):   # 6 Kas (kilit): selde I1-I6 geri
            rows = _sequence(e, 60, 3)
            ids = [r["trace"]["axes"]["insan"] for r in rows]
            self.assertTrue(all(ids))
            trial = [i not in es.PEOPLE_AXIS_PROVEN for i in ids]
            self.assertFalse(any(a and b for a, b in zip(trial, trial[1:])), (e, ids))
            self.assertLessEqual(sum(trial) / len(trial), 0.3)
            proven = [i for i in ids if i in es.PEOPLE_AXIS_PROVEN]
            self.assertEqual(set(proven), {"I1", "I2"})
            for r in rows:   # kod yedeği seçilen cümleyi kullanır
                i = int(r["trace"]["axes"]["insan"][1:]) - 1
                word = es.people_word(r["structure"]["spec"]).capitalize()
                self.assertEqual(r["structure"]["slices"]["slice_1_rest"],
                                 es.clean_slice(es.FALLBACK_PEOPLE[e][i].format(N=word)))

    def test_axes_line_shows_person(self):
        rows = _sequence(es.FLOOD, 2, 1)   # 6 Kas (kilit): selde I1-I6 geri
        self.assertRegex(rows[-1]["structure"]["axes_line"], r"kişi=\d")
        self.assertIn("insan=I", rows[-1]["structure"]["axes_line"])


# ── AŞAMA 4 ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _spec(event=None, seed=1):
    ps.reset_memory()
    random.seed(seed)
    return ps.build(event or es.FLOOD)["structure"]["spec"]


class TestNewGates(_Quiet):
    CASES = [   # (kural, reddedilen, geçen)
        ("invented_motion", "The van keeps rolling away down the road.", "The van is pushed down the road."),
        ("invented_motion", "The car spins before rolling into the wall.", "The car spins into the wall."),
        ("invented_motion", "The truck shakes as it rolls into the shop.", "The truck slides into the shop."),
        ("invented_motion", "The bus is lifted effortlessly by the water.", "The bus is shoved by the water."),
        ("hype_word", "The bombardment hits every roof.", "Rocks hit every roof."),
        ("hype_word", "The mud obliterates the house.", "The mud crushes the house."),
        ("hype_word", "A fiery hail falls on the street.", "Burning debris falls on the street."),
        ("hype_word", "A fiery downfall covers the cars.", "Burning debris covers the cars."),
        ("people_dash", "Four people dash into a doorway.", "Four people run into a doorway."),
        ("vague_target", "Four people run to safety.", "Four people run into a hotel lobby."),
        ("vague_target", "Four people run away from danger.", "Four people run away from the water."),
        ("vague_target", "Four people flee the threat.", "Four people flee the wave."),
        ("sound_word", "The water roars down the street.", "The water surges down the street."),
        ("sound_word", "The wall falls with a thunderous impact.", "The wall falls onto the road."),
        ("sound_word", "Thunder shakes the street.", "A thunderstorm darkens the street."),
        ("sound_word", "A crash sound fills the street.", "A crash fills the street with debris."),
        ("sound_word", "People scream as the wave hits.", "People run as the wave hits."),
        ("sound_word", "The impact echoes down the street.", "The impact shakes the street."),
        ("sound_word", "Steam hisses from the cars.", "Steam rises from the cars."),
        ("sound_word", "The rumble grows.", "The flood grows."),
        ("sound_word", "A deafening crash.", "A heavy crash."),
        ("sound_word", "A boom shakes the houses.", "A blast shakes the houses."),
    ]

    def test_each_rule_rejects_and_passes(self):
        spec = _spec()
        for rule, bad, good in self.CASES:
            with self.subTest(rule=rule, bad=bad):
                sl = {"slice_1_rest": bad, "slice_2": "", "slice_3": ""}
                self.assertIn(rule, {i["rule"] for i in es.gpt_added_issues(spec, sl)})
                sl = {"slice_1_rest": good, "slice_2": "", "slice_3": ""}
                self.assertNotIn(rule, {i["rule"] for i in es.gpt_added_issues(spec, sl)})

    def test_pool_text_exempt(self):
        """Kilit cümlede/havuzda geçen kök muaf (çığ "roaring", helikopter G5 "roar back")."""
        spec = _spec(es.AVALANCHE_VILLAGE)
        sl = {"slice_1_rest": "Five villagers run away right below as it keeps roaring.", "slice_2": "", "slice_3": ""}
        self.assertNotIn("sound_word", {i["rule"] for i in es.gpt_added_issues(spec, sl)})

    def test_locked_fallbacks_never_rejected(self):
        """Kilitli olayların her kod yedeği (tüm beat çiftleri × insan cümleleri) yeni kurallardan geçer."""
        new = {"people_dash", "invented_motion", "hype_word", "vague_target", "sound_word"}
        for e in LOCKED:
            spec0 = _spec(e)
            for v, d in es.allowed_pairs(e, spec0["view"], spec0["spot"]):
                spec = {**spec0, "beat_2": v, "beat_3": d}
                for i, t in enumerate(es.fallback_people_pool(spec)):
                    sl = {"slice_1_rest": es.clean_slice(t.format(N=es.people_word(spec).capitalize())),
                          "slice_2": es.fallback_beat_slice(spec, "slice_2"),
                          "slice_3": es.fallback_beat_slice(spec, "slice_3")}
                    found = {x["rule"] for x in es.gpt_added_issues(spec, sl)} & new
                    self.assertEqual(found, set(), (e, v, d, i))

    def test_seawall_frame_passive(self):
        spot = "Coastal avenue behind a seawall"
        self.assertIn(spot, fx.SPOT_FRAME[es.TIDAL])   # silinmedi
        for s in sk.EVENT_SKELETONS[es.TIDAL]["spots"]:
            for f in fx.all_frames(es.TIDAL, s, list(sk.EVENT_SKELETONS[es.TIDAL]["spots"])):
                self.assertNotEqual(f.get("pos_spot"), spot)
        for seed in range(1, 41):
            self.assertNotIn("on top of the seawall", ps.snapshot_event(es.TIDAL, seed)["prompt"])


# ── AŞAMA 5 ───────────────────────────────────────────────────────────────────────────────────────────────────────
class TestMudslideOpening(_Quiet):
    def test_key_sentence(self):
        key = es.EVENT_KEY_VISUAL[es.MUDSLIDE].lower()
        for w in ("torrent", "thick brown mud", "drenched", "pouring rain", "already"):
            self.assertIn(w, key)
        self.assertNotIn("tears loose", key)
        self.assertEqual(es.EVENT_KEY_VISUAL[es.VILLAGE], "A massive torrent of thick brown mud full of rocks, branches "
                                                          "and debris bursts through the drenched hillside village.")

    def test_all_seeds_build(self):
        for seed in range(1, 41):
            snap = ps.snapshot_event(es.MUDSLIDE, seed)
            self.assertNotIn("error", snap, seed)


# ── AŞAMA 6 ───────────────────────────────────────────────────────────────────────────────────────────────────────
K4 = "Rooftop terrace of a modern seafront building"


class TestMeteor(_Quiet):
    def test_new_options_are_trial(self):
        self.assertEqual(pa.PROVEN_SPOTS[es.METEOR], {"High terrace of a seafront villa"})
        self.assertEqual(pa.PROVEN_METEOR_ENVS, {"O2"})
        self.assertIn(K4, pa.guards(es.METEOR, "spot"))
        self.assertIn("O5", pa.guards(es.METEOR, "meteor_env"))
        self.assertIn("clear early-morning light", pa.guards(es.METEOR, "light"))
        cam = sk.meteor_camera(K4).lower()
        for w in ("high", "wide", "fixed"):
            self.assertIn(w, cam)
        for w in ("eye level", "normal lens", "pans", "follow"):
            self.assertNotIn(w, cam)

    def test_share_and_no_repeat(self):
        rows = _sequence(es.METEOR, 80, 5)
        for axis, key in (("spot", lambda r: r["spot"]), ("meteor_env", lambda r: r["trace"]["meteor_env"]),
                          ("light", lambda r: r["trace"]["weather"])):
            g = pa.guards(es.METEOR, axis)
            flags = [key(r) in g for r in rows]
            self.assertLessEqual(sum(flags) / len(flags), 0.3, axis)
            self.assertFalse(any(a and b for a, b in zip(flags, flags[1:])), axis)

    def test_all_combos_fit(self):
        E = es.METEOR
        for spot in sk.EVENT_SKELETONS[E]["spots"]:
            for b2, b3 in es.allowed_pairs(E, None, spot):
                for env in es.METEOR_ENVS:
                    for li in sk.METEOR_WEATHER:
                        for n in range(3, 7):
                            frame = {"type": fx.native(E, spot)[0], "pos_spot": spot, "fg": None, "mode": None}
                            spec = es.build_spec(E, None, spot, None, b2, b3, None, n, es.meteor_setting(env, li),
                                                 None, frame)
                            cands = es.fallback_candidates(spec)
                            self.assertTrue(cands, (spot, b2, b3, env, li, n))
                            self.assertEqual(es.final_prompt_issues(spec, cands[0], es.assemble_prompt(spec, cands[0]),
                                                                    es.assemble_story(spec, cands[0])), [])

    def test_people_near_coast(self):
        for t in es.FALLBACK_PEOPLE[es.METEOR]:
            self.assertTrue(es.find_terms(es._MET_NEAR, t), t)
            self.assertTrue(re.search(r"\b(run|sprint)\b", t))
        spec = _spec(es.METEOR)
        bad = {"slice_1_rest": f"{es.people_word(spec).capitalize()} people run in the street right below.",
               "slice_2": es.fallback_beat_slice(spec, "slice_2"), "slice_3": es.fallback_beat_slice(spec, "slice_3")}
        self.assertIn("slice_near_camera", {i["rule"] for i in es.slice_issues(spec, bad)})
        self.assertIn("coastal road and terraces right below", es.people_line(spec))

    def test_key_sentence_exempt(self):
        """3a: "column of water" kilit cümlede; kod yedeği / birebir metin reddedilmez, GPT tekrarlarsa reddedilir."""
        self.assertIn("column of water", es.EVENT_KEY_VISUAL[es.METEOR])
        for seed in range(1, 21):
            ps.reset_memory()
            random.seed(seed)
            sc = ps.build(es.METEOR)
            spec, sl = sc["structure"]["spec"], sc["structure"]["slices"]
            self.assertTrue(sc["prompt"].startswith("0-4s: " + spec["key_visual"]))
            self.assertEqual(es.meteor_cgi_issues(spec, sl), [], seed)
            self.assertEqual(es.final_prompt_issues(spec, sl, sc["prompt"], sc["story"]), [], seed)
            gpt = {**sl, "slice_1_rest": f"{es.people_word(spec).capitalize()} people run across the terraces right "
                                         f"below as a column of water rises."}
            self.assertIn("meteor_cgi", {i["rule"] for i in es.slice_issues(spec, gpt)}, seed)

    def test_people_line_only_meteor_changed(self):
        """3b: GPT'ye giden "PEOPLE RUNNING AWAY" satırı HEAD ile aynı; değişen sadece meteor (yer ifadesi) ve sel
        (Aşama 3: selde kişi kuralı yeni, HEAD'de satır yoktu)."""
        import json
        head = json.load(open(os.path.join(ROOT, "tests", "fixtures", "people_line_head.json"), encoding="utf-8"))
        changed = set()
        for key, line in head.items():
            e, n = key.rsplit("|", 1)
            if es.people_line({"event": e, "people": int(n)}) != line:
                changed.add(e)
        # 6 Kas (kilit): sel 3249de8 hâline döndü (3 Kas'taki gibi kişi satırı var)
        self.assertEqual(changed, {es.METEOR, es.FLOOD})
        self.assertNotIn("street right below", es.people_line({"event": es.METEOR, "people": 4}))

    def test_cgi_and_camera_gate(self):
        spec = _spec(es.METEOR)
        s2, s3 = es.fallback_beat_slice(spec, "slice_2"), es.fallback_beat_slice(spec, "slice_3")
        for rule, bad, good in (("meteor_cgi", "A spiky plume rises.", "A white plume rises."),
                                ("meteor_cgi", "A column of water rises.", "Spray rises over the bay."),
                                ("meteor_cgi", "A frozen trail hangs.", "Smoke hangs over the bay."),
                                ("meteor_cgi", "A wall of white hits.", "White spray hits."),
                                ("meteor_camera_move", "The view pans to the shore.", "Panic spreads on the shore."),
                                ("meteor_camera_move", "The view tilts down.", "The palms bend down."),
                                ("meteor_camera_move", "Smoke drifts over.", "Smoke pours over."),
                                ("meteor_camera_move", "The view follows the wave.", "The wave hits the shore.")):
            with self.subTest(rule=rule, bad=bad):
                sl = {"slice_1_rest": bad, "slice_2": s2, "slice_3": s3}
                self.assertIn(rule, {i["rule"] for i in es.meteor_cgi_issues(spec, sl)})
                sl = {"slice_1_rest": good, "slice_2": s2, "slice_3": s3}
                self.assertNotIn(rule, {i["rule"] for i in es.meteor_cgi_issues(spec, sl)})


# ── AŞAMA 7 ───────────────────────────────────────────────────────────────────────────────────────────────────────
class TestEarthquakeModern(_Quiet):
    def test_old_street_passive(self):
        self.assertIn(es.EARTHQUAKE_OLD_STREET, sk.DISABLED_EVENTS)
        self.assertIn(es.EARTHQUAKE_OLD_STREET, es.EVENT_BEATS)   # silinmedi
        self.assertEqual(sk.skeleton_events("earthquake_disasters"), [es.EARTHQUAKE_APARTMENT])

    def test_modern_envs_and_trial(self):
        rows = _sequence(es.EARTHQUAKE_APARTMENT, 80, 9)
        envs = [r["trace"]["environment"] for r in rows]
        for env in envs:
            self.assertNotIn(env["city"], es.EQ_PASSIVE_CITIES)
        flags = [bool({e["city"], e["street"]} & es.EQ_TRIAL_VALUES) for e in envs]
        self.assertGreater(sum(flags), 0)
        self.assertLessEqual(sum(flags) / len(flags), 0.3)
        self.assertFalse(any(a and b for a, b in zip(flags, flags[1:])))
        for r in rows:
            self.assertNotIn("stone", r["prompt"])


# ── AŞAMA 8 ───────────────────────────────────────────────────────────────────────────────────────────────────────
class TestMenuMapping(_Quiet):
    def test_cruise_and_beach_passive(self):
        import bot
        shown = {b.callback_data for r in bot.domain_keyboard().inline_keyboard for b in r}
        for d in ("cruise_ship_operations", "open_beach_coastal_events"):
            self.assertFalse(sk.domain_active(d))
            self.assertEqual(sk.skeleton_events(d), [])
            self.assertIn(d, bot.DOMAIN_KEYS)   # silinmedi, sıra numarası aynı
            self.assertIsNone(bot.parse_selection(str(bot.DOMAIN_KEYS.index(d))))
            self.assertNotIn(f"{bot.CALLBACK_PREFIX}d:{bot.DOMAIN_KEYS.index(d)}", shown)
        for e in ("Mooring line snaps and whips across the quay", "Tornado approaching an open beach"):
            self.assertIn(e, sk.EVENT_SKELETONS)

    def test_urban_buttons(self):
        import bot
        di = bot.DOMAIN_KEYS.index("urban_city_disasters")
        rows = bot.event_keyboard(di).inline_keyboard
        got = {}
        for r in rows:
            for b in r:
                parts = b.callback_data[len(bot.CALLBACK_PREFIX):].split(":")
                if parts[0] == "e" and parts[2] != bot.RANDOM_ID:
                    got[b.text] = bot.parse_selection(parts[1], parts[2])[1]
                    vk = bot.view_keyboard(parts[1], parts[2]).inline_keyboard
                    for vr in vk:
                        for vb in vr:
                            vp = vb.callback_data[len(bot.CALLBACK_PREFIX):].split(":")
                            if vp[0] == "v":
                                ok = bot.confirm_keyboard(*vp[1:]).inline_keyboard[0][0].callback_data
                                self.assertEqual(bot.parse_selection(*ok[len(bot.CALLBACK_PREFIX):].split(":")[1:3])[1],
                                                 got[b.text])
        self.assertEqual(got["🌊 Caddelerde ani sel"], es.FLOOD)
        self.assertEqual(got["🌊 Kıyı şehrinde dev dalga baskını"], es.TIDAL)



# ── KİLİT İSTİSNASI (3 Kas, Bahadır onaylı, tek seferlik) ───────────────────────────────────────────────────────────
G7_TEXT = "the falling sheet of water hits a burning garage across the street and its walls collapse in steam"
T5_HEAD = "a volcanic bomb lands in the middle of the street and the road blasts apart in a crater of sparks"


class TestLockPassiveException(_Quiet):
    """Helikopter G7 (buhar finali) ve bombalar T5 ("crater of sparks") PASİF, silinmedi. Biri yanlışlıkla
    aktifleştirirse ya da kilitli olaylara başka pasif öğe eklerse bu test kırılır. Orman L4 aktif kalır."""

    def test_exception_exact(self):
        self.assertEqual(es.LOCKED_PASSIVE_EXCEPTION, {es.HELICOPTER: {"G7"}, es.VOLCANIC_BOMBS: {"T5"}})
        self.assertEqual(es.DISABLED_BEATS[es.HELICOPTER], {"G7"})
        self.assertEqual(es.DISABLED_BEATS[es.VOLCANIC_BOMBS], {"T5"})
        for e in (es.WILDFIRE, es.LANDFALL, es.VILLAGE):
            self.assertNotIn(e, es.DISABLED_BEATS)

    def test_kept_in_pool(self):
        """Silinmedi: metin havuzda aynen duruyor."""
        self.assertEqual(es.EVENT_BEATS[es.HELICOPTER]["slice_3"]["G7"]["text"], G7_TEXT)
        self.assertTrue(es.EVENT_BEATS[es.VOLCANIC_BOMBS]["slice_3"]["T5"]["text"].startswith(T5_HEAD))
        self.assertIn("L4", es.EVENT_BEATS[es.WILDFIRE]["slice_3"])

    def test_never_selectable(self):
        for e, bid in ((es.HELICOPTER, "G7"), (es.VOLCANIC_BOMBS, "T5")):
            for view in es.structure_views(e):
                for spot in sk.view_spots(e, view):
                    pairs = es.allowed_pairs(e, view, spot)
                    self.assertTrue(pairs, (e, spot))
                    self.assertFalse([p for p in pairs if bid in p], (e, spot))
        # orman L4 hâlâ seçilebilir
        spots = sk.view_spots(es.WILDFIRE, None)
        self.assertTrue(any(p[1] == "L4" for s in spots for p in es.allowed_pairs(es.WILDFIRE, None, s)))

    def test_not_in_prompts(self):
        """20 tohumda (baseline tohumları) ve 100 ardışık üretimde G7/T5 ne izde ne promptta."""
        snap = ps.snapshot_all([es.HELICOPTER, es.VOLCANIC_BOMBS])
        for e, bid, text in ((es.HELICOPTER, "G7", G7_TEXT), (es.VOLCANIC_BOMBS, "T5", T5_HEAD)):
            for seed, r in snap[e].items():
                self.assertNotIn("error", r, (e, seed))
                self.assertNotIn(bid, r["axes"]["beats"].split("+"))
                self.assertNotIn(text.lower(), r["prompt"].lower())
                self.assertNotIn("crater of sparks", r["prompt"].lower())
        for r in _sequence(es.HELICOPTER, 100, 1):
            self.assertNotIn("G7", r["trace"]["beats"].split("+"))
            self.assertNotIn(G7_TEXT.lower(), r["prompt"].lower())

    def test_helicopter_trial_finals_unchanged(self):
        """G1/G2/G5 deneme statüsü ve %10 payı aynı; 100 üretimde pay %20'yi aşmaz."""
        self.assertEqual(es.TRIAL_FINALS, {es.HELICOPTER: {"G1", "G2", "G5"}})
        self.assertEqual(es.TRIAL_FINAL_SHARE, 0.10)
        rows = _sequence(es.HELICOPTER, 100, 1)
        share = sum(r["trace"]["beats"].split("+")[1] in es.TRIAL_FINALS[es.HELICOPTER] for r in rows) / len(rows)
        self.assertLessEqual(share, 0.20)


if __name__ == "__main__":
    unittest.main()
