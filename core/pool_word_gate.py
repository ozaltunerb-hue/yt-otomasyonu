"""Havuz metni kelime kapısı (6 Kas 2026, Bahadır, Aşama 3).

Sebep: dönen, takla atan, havaya kalkan araçları Seedance şekil değiştirerek çiziyor; "always in frame" ve "follow"
kamerayı tehdidi takibe itiyor. KİLİTSİZ olayların AKTİF havuz metinlerinde (kilit cümle, açılışlar, beat'ler, ortam,
kamera eki) aşağıdaki kökler yasak. Kilitli olaylar muaf (sadece rapor). Pasif öğeler seçilemediği için sayılmaz.

Bugün takılan öğeler KNOWN_HITS'te: pasifleştirilmedi, karar Bahadır'da. Listede olmayan yeni takılma testi kırar
(tests/test_pool_word_gate.py). Kapı üretim yolunda çalışmaz, prompt değiştirmez.
"""
from __future__ import annotations

import re

BANNED_TERMS = {
    "swept up": r"swept\s+up",
    "lift": r"lift(?:s|ed|ing)?",
    "fly": r"fl(?:y|ies|ying)",
    "flung into the air": r"flung\s+into\s+the\s+air",
    "spin": r"spin(?:s|ning)?|spun",
    "flip": r"flip(?:s|ped|ping)?",
    "roll over": r"roll(?:s|ed)?\s+(?:[\w{}'-]+\s+){0,3}?over",
    "onto its roof": r"onto\s+its\s+roof",
    "toss": r"toss(?:es|ed|ing)?",
    "crushed": r"crush(?:es|ed|ing)?",
    "concrete": r"concrete",
    "follow": r"follow(?:s|ed|ing)?",
    "always in frame": r"always\s+in\s+frame",
}
_BANNED_RE = {k: re.compile(rf"\b(?:{v})\b", re.IGNORECASE) for k, v in BANNED_TERMS.items()}
# 11 Kas 2026, Bahadır (A6): SADECE kül bulutunda ek yasak kökler (patlama / mantar bulutu çağrışımı). Genel liste aynen.
PYROCLASTIC = "Pyroclastic cloud races down into a village street"
EVENT_BANNED_TERMS = {PYROCLASTIC: {"fireball": r"fireballs?", "blast": r"blast(?:s|ed|ing)?",
                                    "explosion": r"explosions?", "explode": r"explod(?:e|es|ed|ing)",
                                    "nuclear": r"nuclear", "mushroom": r"mushrooms?"}}
_EVENT_BANNED_RE = {e: {k: re.compile(rf"\b(?:{v})\b", re.IGNORECASE) for k, v in terms.items()}
                    for e, terms in EVENT_BANNED_TERMS.items()}
# Bahadır'ın 6 Kas'ta dev dalga için yazdırdığı kamera cümlesi "follows" içerir ama takibi YASAKLAR: kapı bu tam ifadeyi
# yok sayar. Başka "follow" geçen metin takılır.
ALLOWED_PHRASES = ("the camera never pans, turns or follows",)


def term_hits(text: str, event: str | None = None) -> list[str]:
    """Metinde geçen yasak kökler (etiketleriyle). event: olaya özel ek kökler (EVENT_BANNED_TERMS, 11 Kas)."""
    low = text or ""
    for phrase in ALLOWED_PHRASES:
        low = low.replace(phrase, " ")
    rxs = {**_BANNED_RE, **_EVENT_BANNED_RE.get(event, {})}
    return [k for k, rx in rxs.items() if rx.search(low)]


def _items(event: str, camera_seeds) -> list[tuple[str, str, str]]:
    """Olayın aktif havuz metinleri: (tür, kimlik, metin)."""
    import core.event_structure as es
    import core.opening_axis as ox
    import core.scene_env as sv
    import core.skeleton_pipeline as sk
    out = [("kilit", "-", es.EVENT_KEY_VISUAL[event])]
    off = ox.DISABLED_OPENINGS.get(event, set())
    out += [("acilis", k, v) for k, v in ox.OPENINGS.get(event, {}).items() if k not in off]
    beats_off = es.disabled_beats(event)
    for slot in ("slice_2", "slice_3"):
        out += [("beat", b, v["text"]) for b, v in es.EVENT_BEATS[event][slot].items() if b not in beats_off]
    out += [("ortam", k, v) for k, v in sv.SCENE_ENVS.get(event, {}).items()]
    if event in es.METEOR_EVENTS:
        out += [("ortam", k, v) for k, v in es.METEOR_ENVS.items()]
    if event in es.VOLC_ENV_EVENTS:
        out += [("ortam", k, sk.volc_env_text(event, k)) for k in sk.VOLC_ENVS]
    if event in es.AVALANCHE_EVENTS:
        out += [("ortam", axis, v) for axis, vals in es.ENV_AXES.items() for v in vals]
    if event in es.EARTHQUAKE_EVENTS:
        passive = set(getattr(es, "EQ_PASSIVE_CITIES", ()))
        out += [("ortam", axis, v) for axis, vals in es.EQ_ENV_AXES.items() for v in vals if v not in passive]
    # Kamera eki: gerçek üretim yolunun stil eki (kamera cümlesi + Setting satırı); kapalı listeler yerine ölçüm
    if camera_seeds:
        import prompt_snapshot as ps
        for seed in camera_seeds:
            snap = ps.snapshot_event(event, seed)
            out.append(("kamera", "-", snap.get("style_suffix", "")))
    return out


def scan(events, camera_seeds=range(1, 9)) -> dict[tuple[str, str, str, str], str]:
    """{(olay, tür, kimlik, kök): metin}: verilen olaylardaki takılmalar."""
    found: dict[tuple[str, str, str, str], str] = {}
    for event in events:
        for kind, key, text in _items(event, camera_seeds):
            for term in term_hits(text, event):
                found.setdefault((event, kind, key, term), text)
    return found


def unlocked_events() -> list[str]:
    import core.event_structure as es
    import prompt_snapshot as ps
    return [e for e in ps.active_events() if e not in es.LOCKED_EVENTS]


# Bu turda takılan, DOKUNULMAYAN öğeler (Bahadır kararı bekliyor). Listeden öğe çıkarmak serbest; yeni öğe eklemek karar ister.
KNOWN_HITS: frozenset[tuple[str, str, str, str]] = frozenset({
    ('Avalanche crashes down onto a ski lodge', 'beat', 'C3', 'fly'),
    ('Avalanche crashes down onto a ski lodge', 'beat', 'D1', 'fly'),
    ('Avalanche crashes down onto a ski lodge', 'beat', 'D3', 'lift'),
    ('Avalanche crashes down onto a ski lodge', 'beat', 'D3', 'toss'),
    ('Avalanche crashes down onto a ski lodge', 'kamera', '-', 'lift'),
    ('Avalanche rips through a pine forest into a valley', 'beat', 'F2', 'fly'),
    ('Avalanche slams into a mountain village', 'beat', 'A5', 'fly'),
    ('Avalanche slams into a mountain village', 'beat', 'B5', 'fly'),
    ('Earthquake collapses an apartment block', 'beat', 'P4', 'concrete'),
    ('Earthquake collapses an apartment block', 'beat', 'Q3', 'concrete'),
    ('Earthquake collapses an apartment block', 'kamera', '-', 'concrete'),
    ('Earthquake collapses an apartment block', 'ortam', 'city', 'concrete'),
    ('Mudslide pours down a hillside street', 'beat', 'H4', 'crushed'),
    # 11 Kas (A6): kül bulutu Q5 "blasts" yeni kül bulutu kapısına takıldı; Q5 25 Eki 102K paylaşımında (17 Eki 14:13
    # üretimi P2+Q5) kullanıldı: hit kuralı gereği pasife alınmadı, karar Bahadır'da
    ('Pyroclastic cloud races down into a village street', 'beat', 'Q5', 'blast'),
    ('Tornado sweeps down a coastal avenue', 'beat', 'P4', 'crushed'),
    ('Tornado sweeps down a coastal avenue', 'beat', 'P6', 'spin'),
    ('Tornado sweeps down a coastal avenue', 'beat', 'P6', 'swept up'),
})
