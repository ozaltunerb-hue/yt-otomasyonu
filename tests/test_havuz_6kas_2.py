#!/usr/bin/env python3
"""6 Kasım 2026 (2), Bahadır: kalan havuz temizliği. Ağ yok, Kie/GPT çağrısı yok.

Pasif öğeler havuzda durur ve seçilmez; yeni öğeler birebir ve DENEME; "concrete" ve "always in frame" kilitsiz 8 olaydan
çıktı, ortak metinler kilitli olaylarda bayt bayt aynı (kopya / olay bazlı değişim). Kilit: tests/test_kilit_6kas.py.
"""
import logging
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.frame_axis as fx   # noqa: E402
import core.opening_axis as ox   # noqa: E402
import core.pool_word_gate as gate   # noqa: E402
import core.proven_axes as pa   # noqa: E402
import core.scene_env as sv   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402

PY, ME, TI, MU, SL = es.PYROCLASTIC, es.METEOR, es.TIDAL, es.MUDSLIDE, es.SLOPE
MA, AV, FA = es.MARINA_TORNADO, es.AVENUE, es.FACADE_FIRE
NEW = {PY: {"Q7": "the cloud front tears the roof off the house right below before swallowing it",
            "Q8": "the cloud front knocks down the front wall of the two-storey house across the street, then swallows "
                  "it"},
       ME: {"W5": "the shockwave blasts the palm trees along the promenade flat",
            "W6": "the blast tears the roofs off the beach bars along the promenade"}}
PASSIVE = {PY: {"P6", "Q6"}, ME: {"W2"}, TI: {"T1"}, MU: {"H3"}, SL: {"R3", "R6"}, MA: {"Z7"}}
NEVER_PANS = "the camera never pans, turns or follows"
CHANGED = (PY, ME, TI, MU, SL, MA, AV, FA)


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)
        ps.reset_memory()


def _spots(event):
    return [(v, s) for v in (es.structure_views(event) or [None]) for s in sk.view_spots(event, v)]


class TestPools(_Quiet):
    def test_new_items_verbatim_and_trial(self):
        for event, items in NEW.items():
            pool = {**es.EVENT_BEATS[event]["slice_2"], **es.EVENT_BEATS[event]["slice_3"]}
            for bid, text in items.items():
                self.assertEqual(pool[bid]["text"], text)
                self.assertIn(bid, es.TRIAL_BEATS[event])
                self.assertNotIn(bid, es.disabled_beats(event))
                self.assertEqual(gate.term_hits(text), [], bid)

    def test_new_items_in_right_slice(self):
        self.assertLessEqual({"Q7", "Q8"}, set(es.EVENT_BEATS[PY]["slice_3"]))
        self.assertLessEqual({"W5", "W6"}, set(es.EVENT_BEATS[ME]["slice_2"]))

    def test_passive_stays_in_pool_not_selectable(self):
        for event, ids in PASSIVE.items():
            pool = {**es.EVENT_BEATS[event]["slice_2"], **es.EVENT_BEATS[event]["slice_3"]}
            for bid in ids:
                self.assertTrue(pool[bid]["text"], bid)
                self.assertIn(bid, es.disabled_beats(event))
            for view, spot in _spots(event):
                self.assertFalse([p for p in es.allowed_pairs(event, view, spot) if set(p) & ids])

    def test_kept_active_with_reason(self):
        """Cadde P4 (4 öğe), P6 (684K hiti), sokak H4 (H6 seçilemiyor: gerçek havuz 4'ün altına düşerdi)."""
        for event, bid in ((AV, "P4"), (AV, "P6"), (MU, "H4")):
            self.assertNotIn(bid, es.disabled_beats(event), (event, bid))

    def test_min_four_really_selectable(self):
        """Her dilimde en az 4 öğe GERÇEKTEN seçilebilir: yasak çiftlerle hiç eşi kalmayan öğe sayılmaz (sokak H6)."""
        for event in CHANGED:
            pairs = {p for view, spot in _spots(event) for p in es.allowed_pairs(event, view, spot)}
            for i in (0, 1):
                self.assertGreaterEqual(len({p[i] for p in pairs}), 4, (event, i))

    def test_meteor_active_slice2(self):
        active = [b for b in es.EVENT_BEATS[ME]["slice_2"] if b not in es.disabled_beats(ME)]
        self.assertEqual(active, ["W1", "W3", "W5", "W6"])

    def test_same_object_rule_for_new_items(self):
        """Aynı yapı iki dilimde yok (13 Eki, 29 Eki kuralı) yeni öğelerde de."""
        self.assertLessEqual({("P3", "Q7"), ("P1", "Q8"), ("P5", "Q8")}, es.EVENT_BEATS[PY]["excluded_pairs"])
        self.assertIn(("W6", "X4"), es.EVENT_BEATS[ME]["excluded_pairs"])
        rooftop = "Rooftop terrace facing the erupting volcano"
        self.assertIn(rooftop, es.EVENT_BEATS[PY]["excluded_spots"]["Q7"])

    def test_meteor_damage_gate_noun_not_counted(self):
        self.assertTrue(es.find_terms(es.METEOR_DAMAGE, NEW[ME]["W5"]))
        self.assertFalse(es.find_terms(es.METEOR_DAMAGE, "the blast reaches the shore"))


class TestOpenings(_Quiet):
    def test_passive_openings(self):
        self.assertEqual(ox.options(TI), ["A", "C", "D"])
        self.assertEqual(ox.options(AV), ["A", "C", "D"])
        for event in (TI, AV):
            self.assertTrue(ox.OPENINGS[event]["B"])   # silinmedi

    def test_rotation(self):
        """Dev dalgada B koruma harfiydi: rotasyonda sadece A kalır. Caddede koruma D, değişmedi."""
        self.assertEqual(pa.openings(TI, ox.options(TI)), ["A"])
        self.assertEqual(pa.openings(AV, ox.options(AV)), ["A", "D"])


class TestEnvs(_Quiet):
    def test_new_texts(self):
        # 11 Kas (A5): kül bulutu ortamları "right at the foot of the volcano" ile biter
        self.assertEqual(sk.volc_env_text(PY, "pastel_town"),
                         "a street of colorful painted stucco houses with balconies right at the foot of the volcano")
        self.assertEqual(sv.SCENE_ENVS[MU]["B"], "a steep town of pastel stucco houses with tin roofs and banana trees")
        self.assertEqual(sv.SCENE_ENVS[FA]["E"], "a 1970s brick housing estate with long balcony corridors and a playground")

    def test_bombs_keep_their_own_text(self):
        bombs = es.VOLCANIC_BOMBS
        self.assertEqual(sk.volc_env_text(bombs, "pastel_town"), "a street of colorful concrete houses with parked trucks")
        self.assertEqual(sk.VOLC_ENVS["pastel_town"]["text"], "a street of colorful concrete houses with parked trucks")
        self.assertIn("colorful concrete", es.volc_place(bombs, "pastel_town"))
        self.assertIn("painted stucco", es.volc_place(PY, "pastel_town"))

    def test_other_envs_shared(self):
        for name in ("hillside_town", "suburb", "mountain_village"):   # 11 Kas (A5): kül bulutu kopyası + "foot"
            self.assertEqual(sk.volc_env_text(PY, name), f'{sk.VOLC_ENVS[name]["text"]} {sk.PYRO_FOOT}')
            self.assertEqual(sk.volc_env_text(es.VOLCANIC_BOMBS, name), sk.VOLC_ENVS[name]["text"])

    def test_pyroclastic_window_frame_uses_copy(self):
        self.assertIn("painted stucco", fx.family_window(PY, "pastel_town"))
        self.assertIn("colorful concrete", fx.family_window(es.VOLCANIC_BOMBS, "pastel_town"))


class TestCamera(_Quiet):
    def test_five_events_use_never_pans(self):
        self.assertEqual(set(sk.NEVER_PANS_EVENTS), {FA, MU, SL, MA, AV})
        for event in sk.NEVER_PANS_EVENTS:
            for seed in range(1, 21):
                snap = ps.snapshot_event(event, seed)
                self.assertIn(NEVER_PANS, snap["style_suffix"], (event, seed))
                self.assertNotIn("always in frame", snap["prompt"], (event, seed))

    def test_locked_events_share_template_untouched(self):
        for event in (es.LANDFALL, es.VILLAGE, es.WILDFIRE):
            self.assertNotIn(event, sk.NEVER_PANS_EVENTS)
            hits = [ps.snapshot_event(event, s)["style_suffix"] for s in range(1, 21)]
            self.assertFalse([h for h in hits if NEVER_PANS in h], event)
            self.assertTrue([h for h in hits if "always in frame" in h], event)

    def test_replacement_keeps_rest_of_sentence(self):
        cam = "the camera stays fixed, tilting only slightly, never descending, the mud flow always in frame, an empty foreground"
        self.assertEqual(sk._THREAT_IN_FRAME.sub(NEVER_PANS, cam),
                         f"the camera stays fixed, tilting only slightly, never descending, {NEVER_PANS}, an empty foreground")


class TestWordGate(_Quiet):
    def test_list_has_no_stale_record(self):
        """Temizlenen kayıtlar listeden çıktı; kalan her kayıt hâlâ gerçek bir takılma."""
        found = gate.scan(gate.unlocked_events(), camera_seeds=range(1, 41))
        self.assertEqual(set(found), set(gate.KNOWN_HITS))

    def test_only_decided_hits_left_outside_quake_and_avalanche(self):
        family = set(es.AVALANCHE_EVENTS) | set(es.EARTHQUAKE_EVENTS)
        left = {k for k in gate.KNOWN_HITS if k[0] not in family}
        self.assertEqual(left, {(MU, "beat", "H4", "crushed"), (AV, "beat", "P4", "crushed"), (AV, "beat", "P6", "spin"),
                                (AV, "beat", "P6", "swept up"),
                                (PY, "beat", "Q5", "blast")})   # 11 Kas (A6): hit, karar Bahadır'da


if __name__ == "__main__":
    unittest.main()
