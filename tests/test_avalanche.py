#!/usr/bin/env python3
"""
❄️ Çığ kategorisi (13 Eki 2026, Bahadır; TASLAK): 3 olay yapılandırılmış hatta, volkan yapısı (sabit yüksek kamera,
kod havuzu, araçsız, 175 kelime kapısı, olaya özel yasak kelimeler). KİLİT: havuz/kilit cümle/kamera Bahadır'ın
onayıyla değişir. Ağ yok, Kie/GPT çağrısı yok.
"""
import asyncio
import os
import random
import re
import sys
import unittest
from itertools import combinations
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
import core.skeleton_pipeline as sk

KOY, KAYAK, ORMAN = es.AVALANCHE_VILLAGE, es.AVALANCHE_SKI, es.AVALANCHE_FOREST
AVA = (KOY, KAYAK, ORMAN)
HT, BAL, LIFT = "Hillside terrace", "Balcony of a mountain chalet", "Terrace of the lift station"
CAMS = {HT: "on a hillside terrace above the valley", BAL: "on the balcony of a mountain chalet",
        LIFT: "on the terrace of the ski-lift station"}
PERCH = {HT: "terrace", BAL: "balcony", LIFT: "terrace"}
CAMERA = ("Handheld footage shot by a person standing {cam}, high vantage looking across the valley toward the "
          "avalanche on the mountain slope; slight hand shake, the camera stays fixed on the {perch}, tilting down no "
          "more than slightly and never descending, the avalanche always visible in the upper part of the frame, a "
          "corner of the railing in the foreground; one continuous shot, no zoom, no cuts.")
GUARD = "Bystanders wear winter civilian clothes; raw natural overcast daylight, no hazmat suits."
ROOF = {"A3", "A6", "B3", "D3", "E6"}        # (*) sadece yamaç terasında
LIFTB = {"C1", "C5", "D6"}                  # (†) istasyon terasında seçilmez


def cap(s):
    return s[0].upper() + s[1:]


KEY = {
    KOY: "A powder avalanche thunders down the mountainside and slams into a mountain village, a wall of snow engulfing "
         "the first chalets.",
    KAYAK: "An avalanche crashes down the ski slope and hits a mountain lodge, a cloud of snow bursting over its "
           "terrace.",
    ORMAN: "A huge avalanche rips through a pine forest above a valley and hits the houses below, a white cloud rolling "
           "over them.",
}
POOLS = {
    KOY: ({"A1": "the snow wall flattens a row of pine trees and hurls the trunks ahead of it",
           "A2": "the snow blast tears a wooden chalet off its foundation and sweeps it down the slope",
           "A3": "the snow blast rips the roof off a barn and scatters the planks",
           "A4": "the snow wall shoves a stone wall over and rolls on through the village street",
           "A5": "the snow blast snaps a row of wooden fence posts and power poles",
           "A6": "the snow cloud smashes the balcony off a chalet facade"},
          {"B1": "a second wave hits a chalet and its front wall bursts inward",
           "B2": "the snow wall buries a whole row of houses up to their roofs",
           "B3": "the snow blast topples a wooden church bell tower across the street",
           "B4": "the snow wall crashes into a hillside retaining wall and the stones tumble out",
           "B5": "the snow cloud blows the windows out of a long wooden building",
           "B6": "the snow wall carries a wooden shed off its base and breaks it apart"}),
    KAYAK: ({"C1": "the avalanche front mows down a row of ski-lift towers, one after another",
             "C2": "the snow wall shatters a glass-fronted lodge entrance",
             "C3": "the avalanche rips the wooden terrace railing off the lodge and sweeps it away",
             "C4": "the snow blast flattens a line of wooden snow barriers and orange safety fences",
             "C5": "the avalanche hits a stone chairlift station and its upper wall breaks apart",
             "C6": "the avalanche rolls through a grove of pines and snaps them like matchsticks"},
            {"D1": "a second surge buries the lodge's ground floor, snow bursting through the windows",
             "D2": "the snow wall tears a wooden annex off the lodge and carries it downhill",
             "D3": "the avalanche lifts the lodge's roof deck and tosses it aside",
             "D4": "the snow blast knocks over a floodlight tower and its steel frame crashes down",
             "D5": "the avalanche sweeps a small wooden hut off its base and breaks it up",
             "D6": "the snow cloud engulfs the chairlift cables and a cable pylon topples"}),
    ORMAN: ({"E1": "the avalanche front hurls snapped pine trunks into a row of wooden cabins",
             "E2": "the snow cloud swallows a stand of tall pines whole, their tops whipping flat",
             "E3": "the avalanche sweeps a wooden footbridge off its piers",
             "E4": "the snow wall tears a woodshed apart and scatters the logs",
             "E5": "the avalanche hits a stone farmhouse wall and the wall cracks open",
             "E6": "the snow blast peels the roof off a cabin"},
            {"F1": "a second surge slams into the cabins and their walls burst outward",
             "F2": "the snow wall buries a wooden cabin to the roofline",
             "F3": "the avalanche carries a pile of broken trunks across the valley floor into a stone house",
             "F4": "the snow blast knocks over a wooden water tower",
             "F5": "the snow cloud blows the front off a barn and the hay bursts out",
             "F6": "the avalanche sweeps a row of fences and a footbridge railing away"}),
}
# Aynı yapı sınıfı (Bahadır): çatı/kule, duvar, köprü/korkuluk, ağaç, ahşap yapı, cephe, teleferik. Yorumlar: B3 çan
# kulesi A3 ile çatı/kule sınıfı; B1 (ön duvar) ve B5 (pencereler) cephe; E6 kabin çatısı çatı sınıfı.
STRUCT = {
    KOY: {"A1": {"tree"}, "A2": {"wood"}, "A3": {"roof"}, "A4": {"wall"}, "A5": {"rail"}, "A6": {"facade"},
          "B1": {"facade"}, "B2": {"houses"}, "B3": {"roof"}, "B4": {"wall"}, "B5": {"facade"}, "B6": {"wood"}},
    KAYAK: {"C1": {"lift"}, "C2": {"facade"}, "C3": {"rail"}, "C4": {"rail"}, "C5": {"lift", "wall"}, "C6": {"tree"},
            "D1": {"facade"}, "D2": {"wood"}, "D3": {"roof"}, "D4": {"tower"}, "D5": {"wood"}, "D6": {"lift"}},
    ORMAN: {"E1": {"tree", "wood"}, "E2": {"tree"}, "E3": {"bridge"}, "E4": {"wood"}, "E5": {"wall", "stonehouse"},
            "E6": {"roof"},
            "F1": {"wood"}, "F2": {"wood"}, "F3": {"tree", "stonehouse"}, "F4": {"tower"}, "F5": {"wood", "facade"},
            "F6": {"bridge", "rail"}},
}
VALID = {
    "A1": ["The wall of snow knocks down a line of pines and flings the trunks forward.",
           "The avalanche snaps a row of fir trees and throws the broken trunks ahead.",
           "A row of pine trees is flattened as the snow wall hurls their trunks downhill.",
           "The snow blast uproots the pines and sends the trunks tumbling ahead of it.",
           "The snow wall flattens a row of pine trees and hurls the trunks ahead of it."],
    "A2": ["The snow blast rips a wooden chalet from its foundation and carries it down the slope.",
           "The avalanche tears a chalet off its base and drags it downhill.",
           "A wooden house is lifted off its foundation and swept away by the snow.",
           "The wall of snow shoves a chalet off its footings and rolls it down the mountainside.",
           "The snow blast tears a wooden chalet off its foundation and sweeps it down the slope."],
    "A3": ["The blast tears the roof off a barn and flings the planks across the snow.",
           "The barn's roof is ripped away and its planks scatter in the snow cloud.",
           "The snow blast lifts the roof off a wooden barn and hurls the boards away.",
           "The avalanche strips the roof from a barn, scattering planks everywhere.",
           "The snow blast rips the roof off a barn and scatters the planks."],
    "A4": ["The snow wall pushes over a stone wall and keeps rolling down the village street.",
           "A low stone wall topples under the snow and the avalanche rolls on through the street.",
           "The avalanche knocks down a garden wall and surges through the village.",
           "The snow shoves a dry-stone wall over and pours down the street.",
           "The snow wall shoves a stone wall over and rolls on through the village street."],
    "A5": ["The snow blast breaks a row of wooden fence posts and power poles.",
           "Fence posts and power poles snap one after another in the blast.",
           "The avalanche flattens a wooden fence and knocks down the power poles.",
           "A line of utility poles and fencing cracks and topples in the snow blast.",
           "The snow blast snaps a row of wooden fence posts and power poles."],
    "A6": ["The snow cloud tears the balcony off a chalet's facade.",
           "A chalet balcony is ripped from the facade by the snow cloud.",
           "The blast smashes a wooden balcony and it breaks away from the chalet.",
           "The snow cloud rips the balcony off the front of a chalet.",
           "The snow cloud smashes the balcony off a chalet facade."],
    "B1": ["A second wave slams into a chalet and its front wall caves in.",
           "Another surge hits a wooden house and its front wall bursts inward.",
           "The second wave of snow smashes a chalet's front wall inward.",
           "A chalet's front wall collapses as a second surge strikes it.",
           "A second wave hits a chalet and its front wall bursts inward."],
    "B2": ["The avalanche buries a row of chalets up to the eaves.",
           "A whole row of houses is engulfed in snow up to their roofs.",
           "The snow wall swallows a line of cottages up to their rooftops.",
           "Snow piles up over a row of houses until only their roofs show.",
           "The snow wall buries a whole row of houses up to their roofs."],
    "B3": ["The snow blast knocks a wooden church bell tower across the street.",
           "A wooden bell tower topples over and crashes across the street.",
           "The church tower collapses in the snow blast and falls into the street.",
           "The blast brings down the wooden belfry across the road.",
           "The snow blast topples a wooden church bell tower across the street."],
    "B4": ["The snow wall slams into a retaining wall on the hillside and its stones tumble out.",
           "A hillside retaining wall gives way under the snow, stones spilling out.",
           "The avalanche smashes a retaining wall and the stones fall into the street.",
           "The retaining wall cracks open and its stones tumble down the slope.",
           "The snow wall crashes into a hillside retaining wall and the stones tumble out."],
    "B5": ["The snow cloud blows out the windows of a long wooden building.",
           "Every window of a long wooden building shatters in the snow cloud.",
           "The blast bursts the windows of a long timber hall.",
           "The windows of a wooden building explode as the snow cloud hits.",
           "The snow cloud blows the windows out of a long wooden building."],
    "B6": ["The avalanche lifts a wooden shed off its base and smashes it to pieces.",
           "A wooden shed is swept off its foundation and breaks apart in the snow.",
           "The snow wall drags a shed off its base and crushes it.",
           "The snow tears a small shed from its base and it falls apart.",
           "The snow wall carries a wooden shed off its base and breaks it apart."],
    "C1": ["The avalanche front knocks down a row of ski-lift towers one after another.",
           "Ski-lift towers snap and topple one by one as the avalanche hits.",
           "The avalanche mows down the chairlift towers in a row.",
           "The snow wall brings down a line of lift pylons, one after another.",
           "The avalanche front mows down a row of ski-lift towers, one after another."],
    "C2": ["The snow wall smashes the glass front of the lodge entrance.",
           "The lodge's glass entrance shatters as the snow wall hits.",
           "The avalanche bursts through a glass-fronted lodge entrance.",
           "The snow blasts out the glass doors of the lodge entrance.",
           "The snow wall shatters a glass-fronted lodge entrance."],
    "C3": ["The avalanche tears the wooden terrace railing off the lodge and carries it away.",
           "The lodge's terrace railing is ripped off and swept away by the snow.",
           "The snow wall rips the wooden balustrade from the lodge terrace.",
           "The avalanche wrenches the terrace railing loose and drags it down the slope.",
           "The avalanche rips the wooden terrace railing off the lodge and sweeps it away."],
    "C4": ["The snow blast knocks down a line of wooden snow barriers and orange safety fences.",
           "The avalanche flattens the orange safety fences and wooden barriers.",
           "A row of snow fences and safety netting is torn down by the blast.",
           "The snow wall snaps the wooden barriers and sweeps the orange fences away.",
           "The snow blast flattens a line of wooden snow barriers and orange safety fences."],
    "C5": ["The avalanche slams into the stone chairlift station and its upper wall crumbles.",
           "The upper wall of the chairlift station cracks and caves in as the snow hits.",
           "The snow wall smashes into the lift station and its top wall collapses.",
           "The chairlift station's stone wall bursts apart under the avalanche.",
           "The avalanche hits a stone chairlift station and its upper wall breaks apart."],
    "C6": ["The avalanche rolls through a stand of pines and snaps them like twigs.",
           "The snow wall breaks a grove of pine trees like matchsticks.",
           "Pine trees crack and topple as the avalanche tears through the grove.",
           "The avalanche flattens a grove of firs, snapping every trunk.",
           "The avalanche rolls through a grove of pines and snaps them like matchsticks."],
    "D1": ["A second surge buries the lodge's ground floor and snow bursts through the windows.",
           "Another wave of snow swamps the lodge's ground floor, smashing the windows.",
           "The lodge's ground floor is buried as snow blows in through the windows.",
           "A second surge fills the lodge's lower floor and the windows burst.",
           "A second surge buries the lodge's ground floor, snow bursting through the windows."],
    "D2": ["The snow wall rips a wooden annex off the lodge and carries it downhill.",
           "The avalanche tears the lodge's wooden extension away and sweeps it down the slope.",
           "A wooden annex is torn from the lodge and dragged downhill by the snow.",
           "The snow wall shoves the lodge's wooden wing off and carries it away.",
           "The snow wall tears a wooden annex off the lodge and carries it downhill."],
    "D3": ["The avalanche lifts the roof deck of the lodge and tosses it aside.",
           "The lodge's roof deck is ripped up and flung aside by the snow.",
           "The snow blast tears off the lodge roof and throws it away.",
           "The avalanche peels the lodge's roof deck up and hurls it to the side.",
           "The avalanche lifts the lodge's roof deck and tosses it aside."],
    "D4": ["The snow blast knocks down a floodlight tower and its steel frame crashes to the ground.",
           "A floodlight tower topples over and its steel frame crashes down.",
           "The avalanche brings down a tall light mast, its frame crashing into the snow.",
           "The floodlight tower buckles and falls as the snow blast hits.",
           "The snow blast knocks over a floodlight tower and its steel frame crashes down."],
    "D5": ["The avalanche pushes a small hut off its base and smashes it.",
           "A wooden hut is swept away by the avalanche and breaks apart.",
           "The snow carries a little wooden shack off its footings and crushes it.",
           "The avalanche rips a hut from its base and tumbles it down the slope.",
           "The avalanche sweeps a small wooden hut off its base and breaks it up."],
    "D6": ["The snow cloud swallows the chairlift cables and a cable pylon topples over.",
           "The avalanche engulfs the chairlift and one of its pylons crashes down.",
           "A chairlift pylon falls as the snow cloud buries the cables.",
           "The snow cloud covers the lift cables and a pylon collapses.",
           "The snow cloud engulfs the chairlift cables and a cable pylon topples."],
    "E1": ["The avalanche hurls snapped pine trunks into a row of wooden cabins.",
           "Broken pine trunks are flung into the wooden cabins by the avalanche front.",
           "The avalanche drives snapped trees into a row of cabins.",
           "The snow front throws broken trunks into the wooden huts.",
           "The avalanche front hurls snapped pine trunks into a row of wooden cabins."],
    "E2": ["The snow cloud swallows a stand of tall pines, their tops whipping flat.",
           "A stand of tall pines is engulfed by the snow cloud as their tops bend flat.",
           "The avalanche engulfs a grove of tall firs and flattens their tops.",
           "Tall pine trees are buried in the snow cloud, their crowns whipping down.",
           "The snow cloud swallows a stand of tall pines whole, their tops whipping flat."],
    "E3": ["The avalanche rips a wooden footbridge off its piers.",
           "A wooden footbridge is swept off its supports by the snow.",
           "The snow wall tears the footbridge from its piers and carries it away.",
           "The avalanche smashes a footbridge and the span collapses into the stream.",
           "The avalanche sweeps a wooden footbridge off its piers."],
    "E4": ["The snow wall rips a woodshed open and scatters the logs.",
           "A woodshed bursts open in the snow and its logs fly everywhere.",
           "The avalanche smashes a woodshed and flings the firewood across the snow.",
           "The snow wall breaks a woodshed apart and scatters the logs.",
           "The snow wall tears a woodshed apart and scatters the logs."],
    "E5": ["The avalanche hits a stone farmhouse and its wall cracks open.",
           "The wall of a stone farmhouse splits as the avalanche strikes it.",
           "The snow slams into a farmhouse and its stone wall caves in.",
           "A stone farmhouse wall bursts open under the avalanche.",
           "The avalanche hits a stone farmhouse wall and the wall cracks open."],
    "E6": ["The snow blast tears the roof off a cabin.",
           "A cabin's roof is ripped away by the snow blast.",
           "The avalanche lifts the roof off a wooden cabin and flings it away.",
           "The snow blast strips the roof from a small cabin.",
           "The snow blast peels the roof off a cabin."],
    "F1": ["Another surge hits the cabins and their walls burst outward.",
           "The second wave smashes into the wooden cabins and their walls cave in.",
           "A second surge strikes the cabins, blowing their walls out.",
           "The cabins' walls shatter as a second wave of snow hits them.",
           "A second surge slams into the cabins and their walls burst outward."],
    "F2": ["The snow wall buries a wooden cabin up to its roofline.",
           "A wooden cabin is buried to the roofline under the snow.",
           "The avalanche engulfs a cabin until only its roofline shows.",
           "The snow swallows a small wooden hut up to the roof.",
           "The snow wall buries a wooden cabin to the roofline."],
    "F3": ["The avalanche carries broken trunks across the valley floor and into a stone house.",
           "Broken trunks are swept across the valley floor and slam into a stone house.",
           "The avalanche drives a pile of snapped trees into a stone house on the valley floor.",
           "The snow pushes a mass of broken trunks into the side of a stone house.",
           "The avalanche carries a pile of broken trunks across the valley floor into a stone house."],
    "F4": ["The snow blast knocks down a wooden water tower.",
           "A wooden water tower topples over in the snow blast.",
           "The avalanche brings down a water tower, which crashes into the snow.",
           "The blast knocks over a tall wooden water tank.",
           "The snow blast knocks over a wooden water tower."],
    "F5": ["The snow cloud rips the front off a barn and hay bursts out.",
           "A barn's front wall is torn away and the hay inside bursts out.",
           "The snow blast blows the barn's front open and straw explodes outward.",
           "The front of a barn bursts open and bales of hay spill into the snow.",
           "The snow cloud blows the front off a barn and the hay bursts out."],
    "F6": ["The avalanche sweeps away a row of fences and a footbridge railing.",
           "A row of fences and the railing of a footbridge are swept away by the snow.",
           "The avalanche tears a line of fences and a bridge railing away.",
           "The snow carries off a row of fences and the footbridge railing.",
           "The avalanche sweeps a row of fences and a footbridge railing away."],
}
# Sadece atmosfer (kar tozu, gökyüzü, uzaktan çığ): hiçbir maddeden geçmemeli
ATMOSPHERE = ["Snow dust drifts over the valley below the mountain.",
              "The avalanche roars down the slope under a grey sky.",
              "A white cloud rises high above the mountainside.",
              "Snow keeps falling over the quiet village.",
              "The mountain disappears behind a wall of white powder.",
              "A cloud of snow spreads across the sky above the valley."]


def ava_gpt(messages=None):
    """Ağsız sahte GPT: seçilen maddeleri birebir dilim yapar (kod seçimi; ücretli çağrı yok)."""
    async def gpt(system, user, **kw):
        if messages is not None:
            messages.append(user)
        line = dict(l.split(": ", 1) for l in user.splitlines()
                    if l.startswith(("4-9s EVENT", "9-15s EVENT", "PEOPLE RUNNING AWAY")))
        word = line["PEOPLE RUNNING AWAY"].split()[0]
        away = line["PEOPLE RUNNING AWAY"].split("run away from ")[1].rstrip(")")
        s2, s3 = cap(line["4-9s EVENT"]), cap(line["9-15s EVENT"])
        s2 += " as the snow roars" if len(s2.split()) < 10 else ""
        s3 += " as the snow roars" if len(s3.split()) < 10 else ""
        return {"slice_1_rest": f"{cap(word)} people run from {away}.", "slice_2": s2 + ".", "slice_3": s3 + "."}
    return gpt


def build(e, b2, b3, spot=HT, people=5):
    spec = es.build_spec(e, None, spot, None, b2, b3, None, people)
    s2, s3 = cap(es.beat_text(e, "slice_2", b2)), cap(es.beat_text(e, "slice_3", b3))
    s2 += " as the snow roars" if len(s2.split()) < 10 else ""
    s3 += " as the snow roars" if len(s3.split()) < 10 else ""
    sl = {"slice_1_rest": es.clean_slice(f"{cap(es.NUMBER_WORDS[people])} people run from the avalanche."),
          "slice_2": es.clean_slice(s2), "slice_3": es.clean_slice(s3)}
    return spec, sl


def codes(spec, sl):
    return {i["rule"] for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl))}


def beats():
    for e in AVA:
        for slot in ("slice_2", "slice_3"):
            for bid, beat in es.EVENT_BEATS[e][slot].items():
                yield e, slot, bid, beat


class TestAvalanche(unittest.TestCase):
    def setUp(self):
        es._BEAT_MEMORY.clear()

    def test_category_menu_and_registrations(self):
        import bot
        import core.creative_pipeline as cp
        from core.creative_engine import DOMAIN_ATTRIBUTES, ENV_CENTRIC_DOMAINS, MARITIME_INSPIRATION_DOMAINS
        self.assertEqual(bot.DOMAIN_LABELS["avalanche_disasters"], "❄️ Çığ")
        self.assertIn('avalanche_disasters: "❄️ Çığ",', open(os.path.join(ROOT, "dashboard.html"), encoding="utf-8").read())
        self.assertEqual({e: bot.EVENT_LABELS[e] for e in AVA},
                         {KOY: "🏔️ Çığ köyü yutuyor", KAYAK: "⛷️ Çığ kayak merkezine iniyor",
                          ORMAN: "🌲 Çığ ormandan vadiye iniyor"})
        self.assertEqual(es.AVALANCHE_EVENTS, AVA)
        self.assertEqual(sk.skeleton_events("avalanche_disasters"), list(AVA))
        self.assertEqual(DOMAIN_ATTRIBUTES["avalanche_disasters"]["environments"], [HT, BAL, LIFT])
        self.assertEqual(DOMAIN_ATTRIBUTES["avalanche_disasters"]["ships"], [])
        self.assertIn("avalanche_disasters", MARITIME_INSPIRATION_DOMAINS)
        self.assertIn("avalanche_disasters", ENV_CENTRIC_DOMAINS)
        self.assertIn("avalanche_disasters", sk.NO_SIGNS_DOMAINS)
        self.assertEqual(sk.PHENOMENA["Çığ"], list(AVA))
        for e in AVA:
            with self.subTest(event=e):
                self.assertTrue(es.is_structured(e))
                self.assertLessEqual(len(bot.EVENT_LABELS[e]), 40)
                self.assertEqual(cp.EVENT_REQUIRED[e], [])
                self.assertIn(e, cp.EVENT_OUTCOMES)
                self.assertEqual(sk.count_range(e, None), (3, 6))
                self.assertEqual(es.TOTAL_WORDS_BY_EVENT[e], (40, 75))
                self.assertFalse(es.uses_vehicle(e))
                self.assertNotIn(e, es.EVENT_VEHICLES)
                self.assertEqual(es.structure_views(e), [None])
                self.assertIn(e, es.WORD_CAP_EVENTS)
                self.assertNotIn(e, es.NO_RAIN_EVENTS)
        # Telegram: çığ düğmesi görünür, 3 olay seçilebilir
        texts = [b.text for row in bot.domain_keyboard().inline_keyboard for b in row]
        self.assertIn("❄️ Çığ", texts)
        ev = [b.text for row in bot.event_keyboard(bot.DOMAIN_KEYS.index("avalanche_disasters")).inline_keyboard
              for b in row]
        for label in ("🏔️ Çığ köyü yutuyor", "⛷️ Çığ kayak merkezine iniyor", "🌲 Çığ ormandan vadiye iniyor"):
            self.assertIn(label, ev)

    def test_key_visuals_and_pools_locked(self):
        import core.creative_pipeline as cp
        for e in AVA:
            with self.subTest(event=e):
                self.assertEqual(es.EVENT_KEY_VISUAL[e], KEY[e])
                found = {i["rule"] for i in cp.story_rule_issues(e, None, KEY[e])}
                self.assertFalse(found & {"a_trigger_first", "e_event_and_ship_named", "required"})
                b = es.EVENT_BEATS[e]
                self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, POOLS[e][0])
                self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, POOLS[e][1])
                self.assertEqual(b["excluded_views"], {})

    def test_cameras_and_style_suffix(self):
        from core.trace_format import count_constraints
        self.assertEqual(sk.AVALANCHE_WEATHER, ["overcast winter daylight over snowy mountains"])
        spots = {KOY: [HT, BAL], KAYAK: [HT, BAL, LIFT], ORMAN: [HT, BAL]}
        for e in AVA:
            s = sk.EVENT_SKELETONS[e]
            self.assertIs(s["weather"], sk.AVALANCHE_WEATHER)
            self.assertEqual(list(s["spots"]), spots[e])
            for spot in spots[e]:
                suffix = sk.style_suffix(e, None, spot)
                with self.subTest(event=e, spot=spot):
                    self.assertEqual(sk.CAMERA_SPOTS[spot], CAMS[spot])
                    self.assertEqual(suffix, f"{CAMERA.format(cam=CAMS[spot], perch=PERCH[spot])} {GUARD} No readable "
                                             f"signs, text or flags.")
                    self.assertNotIn("pans to follow", suffix)
                    self.assertNotIn("follow", suffix)
                    self.assertLessEqual(count_constraints(suffix)[0], 8)
        # volkan ve diğer kategorilerin kamera satırı değişmedi
        self.assertTrue(sk.style_suffix(es.ERUPTION, None, "Hillside terrace facing the erupting volcano")
                        .startswith("Handheld footage shot by a person standing on a hillside terrace above the village, "
                                    "high vantage looking down over the village street toward the erupting volcano;"))
        self.assertIn("the camera pans to follow the", sk.style_suffix(es.MUDSLIDE, None, list(
            sk.EVENT_SKELETONS[es.MUDSLIDE]["spots"])[0]))

    def test_term_lists_avalanche_only(self):
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(es))
        node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(getattr(t, "id", None) == "EVENT_BEATS" for t in n.targets))
        seen = 0
        for k, v in zip(node.keys, node.values):
            if getattr(k, "id", None) in ("AVALANCHE_VILLAGE", "AVALANCHE_SKI", "AVALANCHE_FOREST"):
                seen += 1
                names = {n.id for n in ast.walk(v) if isinstance(n, ast.Name)}
                self.assertTrue(names and all(n.startswith("_AVA_") for n in names), names)
        self.assertEqual(seen, 3)

    def test_every_beat_alone_and_five_natural_sentences(self):
        self.assertEqual(set(VALID), {bid for _, _, bid, _ in beats()})
        z6 = {"annihilate", "splinter", "obliterate", "demolish", "wreck", "wreak", "rupture", "pulverize",
              "tear apart", "tears apart", "tore apart", "torn apart", "blow apart", "blows apart", "blew apart",
              "blown apart"}
        for e, slot, bid, beat in beats():
            text = es.clean_slice(cap(es.beat_text(e, slot, bid)))
            with self.subTest(beat=bid):
                self.assertEqual(es.missing_term_groups(beat["terms"], text), [])
                self.assertGreaterEqual(len(VALID[bid]), 5)
                for s in VALID[bid]:
                    self.assertEqual(es.missing_term_groups(beat["terms"], s), [], s)
                    for code, terms, *_ in es.EVENT_BANNED_WORDS[e]:
                        self.assertEqual(es.find_terms(terms, s), [], s)
                for a in ATMOSPHERE:
                    self.assertTrue(es.missing_term_groups(beat["terms"], a), a)
                others = [o for o, ob in es.EVENT_BEATS[e][slot].items()
                          if o != bid and es.missing_term_groups(ob["terms"], text)]
                self.assertTrue(others, bid)
                self.assertNotIn("{vehicle}", beat["text"])
                self.assertFalse({w for g in beat["terms"] for w in g} & z6)

    def test_banned_and_slow_words_gate(self):
        spec, sl = build(KOY, "A1", "B2")
        self.assertFalse(codes(spec, sl) & {"avalanche_banned", "avalanche_no_slow"})
        for w in ("rescue", "helicopter", "skier", "snowmobile", "vehicle", "truck", "car", "cargo", "tugboat",
                  "ship", "boat", "siren", "text", "sign", "logo"):
            with self.subTest(word=w):
                bad = es.clean_slice(f"The snow wall buries a whole row of houses and a {w} up to their roofs")
                self.assertIn("avalanche_banned", codes(spec, {**sl, "slice_3": bad}))
        for w in ("slowly", "gently", "calmly", "gradually", "softly"):
            with self.subTest(word=w):
                bad = es.clean_slice(f"The snow wall {w} buries a whole row of houses up to their roofs")
                self.assertIn("avalanche_no_slow", codes(spec, {**sl, "slice_3": bad}))
        self.assertIn("avalanche_no_slow", codes(spec, {**sl, "slice_1_rest": "Five calm people run from the avalanche."}))
        # "carries", "signal"/"cartwheel" gibi kelimeler yasak sayılmaz; volkanda bu kapı yok
        self.assertEqual(es.find_terms(es._AVA_BANNED, "The avalanche carries the cabin, a cartwheel spins."), [])
        self.assertNotIn(es.ERUPTION, es.EVENT_BANNED_WORDS)
        self.assertEqual(set(es.EVENT_BANNED_WORDS), set(AVA))

    def test_forbidden_pairs_follow_same_structure_rule(self):
        for e, tags in STRUCT.items():
            b = es.EVENT_BEATS[e]
            self.assertEqual(set(tags), set(b["slice_2"]) | set(b["slice_3"]))
            with self.subTest(event=e):
                self.assertEqual(b["excluded_pairs"], {(v, d) for v in b["slice_2"] for d in b["slice_3"]
                                                      if tags[v] & tags[d]})
        self.assertEqual(es.EVENT_BEATS[KOY]["excluded_pairs"],
                         {("A2", "B6"), ("A3", "B3"), ("A4", "B4"), ("A6", "B1"), ("A6", "B5")})
        self.assertEqual(es.EVENT_BEATS[KAYAK]["excluded_pairs"], {("C1", "D6"), ("C5", "D6"), ("C2", "D1")})
        self.assertEqual(es.EVENT_BEATS[ORMAN]["excluded_pairs"],
                         {("E1", "F1"), ("E1", "F2"), ("E1", "F3"), ("E1", "F5"), ("E2", "F3"), ("E3", "F6"),
                          ("E4", "F1"), ("E4", "F2"), ("E4", "F5"), ("E5", "F3")})

    def test_camera_exclusions(self):
        # çatı/baca (*) sadece yamaç terasında; teleferik (†) istasyon terasında yok
        for e in AVA:
            b = es.EVENT_BEATS[e]
            for bid in list(b["slice_2"]) + list(b["slice_3"]):
                spots = set(sk.view_spots(e, None)) - b["excluded_spots"].get(bid, set())
                with self.subTest(beat=bid):
                    if bid in ROOF:
                        self.assertEqual(spots, {HT})
                    elif bid in LIFTB:
                        self.assertNotIn(LIFT, spots)
                        self.assertEqual(spots, {HT, BAL})
                    else:
                        self.assertEqual(spots, set(sk.view_spots(e, None)))
        counts = {e: [len(es.allowed_pairs(e, None, s)) for s in sk.view_spots(e, None)] for e in AVA}
        self.assertEqual(counts, {KOY: [31, 18], KAYAK: [33, 27, 15], ORMAN: [26, 20]})

    def test_block_depth_never_runs_out(self):
        # standart 3; aday kalmayan noktası olan olaylarda 2 (kayak: istasyon terası, orman: balkon)
        self.assertNotIn(KOY, es.RECENT_BEAT_BLOCK_BY_EVENT)
        self.assertEqual(es.RECENT_BEAT_BLOCK, 3)
        self.assertEqual((es.RECENT_BEAT_BLOCK_BY_EVENT[KAYAK], es.RECENT_BEAT_BLOCK_BY_EVENT[ORMAN]), (2, 2))

        def worst(e, spot, k):
            b, ps = es.EVENT_BEATS[e], es.allowed_pairs(e, None, spot)
            return min(sum(1 for v, d in ps if v not in x2 and d not in x3)
                       for x2 in map(set, combinations(b["slice_2"], k))
                       for x3 in map(set, combinations(b["slice_3"], k)))
        for e in AVA:
            k = es.RECENT_BEAT_BLOCK_BY_EVENT.get(e, es.RECENT_BEAT_BLOCK)
            for spot in sk.view_spots(e, None):
                with self.subTest(event=e, spot=spot):
                    self.assertGreater(worst(e, spot, k), 0)
        self.assertEqual(worst(KAYAK, LIFT, 3), 0)    # 2'ye düşürmenin sebebi
        self.assertEqual(worst(ORMAN, BAL, 3), 0)

    def test_all_combinations_pass_final_check(self):
        n = 0
        for e in AVA:
            for spot in sk.view_spots(e, None):
                for b2, b3 in es.allowed_pairs(e, None, spot):
                    spec, sl = build(e, b2, b3, spot, people=3 + n % 4)
                    issues = es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl), es.assemble_story(spec, sl))
                    if issues:
                        self.fail(f"{e}/{spot}/{b2}+{b3}: {issues}")
                    n += 1
        self.assertEqual(n, 31 + 18 + 33 + 27 + 15 + 26 + 20)

    def test_100_productions_each_event(self):
        import core.creative_pipeline as cp
        for e in AVA:
            es._BEAT_MEMORY.clear()
            b = es.EVENT_BEATS[e]
            depth = es.RECENT_BEAT_BLOCK_BY_EVENT.get(e, es.RECENT_BEAT_BLOCK)
            msgs, tags, spots, most = [], [], set(), 0
            with self.subTest(event=e):
                for _ in range(100):
                    scene = asyncio.run(cp.build_creative_scene("avalanche_disasters", e, [], [], ava_gpt(msgs)))
                    t, spec, sl = scene["trace"], scene["structure"]["spec"], scene["structure"]["slices"]
                    pair = (spec["beat_2"], spec["beat_3"])
                    self.assertEqual(es.final_prompt_issues(spec, sl, scene["prompt"], scene["story"]), [])
                    self.assertNotIn(pair, b["excluded_pairs"])
                    for x in pair:
                        if x in ROOF:
                            self.assertEqual(t["spot"], HT)
                        if x in LIFTB:
                            self.assertNotEqual(t["spot"], LIFT)
                    for prev in tags[-depth:]:
                        self.assertNotEqual(pair[0], prev[0])
                        self.assertNotEqual(pair[1], prev[1])
                    n = len(scene["prompt"].split())
                    most = max(most, n)
                    self.assertLessEqual(n, 175)
                    self.assertNotIn("pans to follow", scene["prompt"])
                    self.assertIsNone(t["vehicle"])
                    self.assertNotIn("VEHICLE:", msgs[-1])
                    self.assertTrue(scene["combo_key"].startswith("avalanche_disasters|none|"))
                    tags.append(pair)
                    spots.add(t["spot"])
                self.assertEqual(spots, set(sk.view_spots(e, None)))
                self.assertGreaterEqual(len(set(tags)), 15)
                self.assertLessEqual(most, 175)

    def test_skeleton_texts(self):
        import core.prompt_generator as pg
        for e in AVA:
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
