# SPDX-License-Identifier: GPL-3.0-or-later
"""Maestro's choices in plain words: a few bars drawn from the theory core, one choice at a time, each said the
way a player would say it (the section and its energy, the chord and why, how the pad and bass move, the bass
rhythm against the clave, how the motif develops). For spot checks (checkpoint 2); `sketch.py` plays the same
choices as a rough clip. The choices are the drafts' tendencies one by one, and making them into music is the style
book's work (bucket 3).

Task 3.2's flow (`theory/flow.py`) is the default: progressions as families, the bass on its pattern, the melody
shaped over the phrase. `--no-flow` gives Checkpoint 2's bar-by-bar draws, to compare.

    python -m maestro.explain salsa --seed 7 --bars 16 [--no-flow]"""
import argparse, re
from itertools import groupby

from .rng import ComposerRng, fresh_seed
from .stylebook import part
from .theory.chords import VOCAB, _resolves_to, choose_in_style, function, name, outside, roman
from .theory.flow import ARPS, BASS, bass_range, FLOW, arp_part, bass_808, check_arp, bass_part, chart, check_808, check_bass, check_phrase, chord_at, \
    check_loop, held, loop_melody, LOOPS, phrase_melody, plain_phrase, progression, _nearest, _tone
from .theory.drums import DOUBLE, DRUMMER, KIT, _fill, _vel, check_drums, double_kick, drum_part, quiet_spans
from .theory.guitar import GUITAR, VOICINGS, _root as guitar_root, bends as lead_bends, check_guitar, check_leads, \
    check_scratch, scratch as scratch_lane, \
    duel, guitar_part, lock_bass, pentatonic, power, twin, vibrato
from .theory.arrange import ARRANGE, check_parts, cut as silence, phrase_parts
from .theory.horns import HORNS, check_horns, harmonize, hits, horn_part, strokes
from .theory.keys import KEYS, ahead, check_keys, montuno_part, voice
from .theory.layers import LAYERS, check_layers, plan_layers, silence as rest, slow_changes
from .theory.form import DEVELOPS, FORM, WORDS, Play, Theme, _draw, explain_section
from .theory.percussion import PERCUSSION, check_percussion, percussion_part
from .theory.pitch import Key
from .theory.rhythm import CLAVES, METERS, RHYTHM, check_clave, check_onsets, choose_onsets, explain_feel, explain_onsets, \
    feel_for
from .theory.voicing import LEADING, check_band, choose_voicing, explain, member_range, note_name, voicings

TRIES = 10   # draws of a bass rhythm before giving up on sitting with the clave
REDRAWS = 4  # draws of a phrase the check rules out before the plain one plays
LEAN = 12   # how much more often a section opens on its tonic, and a tension chord goes where it leans
SAY = 2     # bars between statements of the motif (a statement and its answer)
UNDER = 77  # the pad stays under F5, leaving the melody its own register on top
UP_FROM = 43  # G2: under it, power rock's bass goes an octave up over the double bass


def _notes(key, v):
    return " ".join(note_name(key, m) for m in v)


def _melody_on(m, at, end):
    """The statement's onsets from step `at`, the ones before `end` (the clip's end)."""
    on, t = [], at
    for length in m.lengths:
        if t < end:
            on.append(t)
        t += length
    return on


def _crosses(m, at, clave, end, before):
    """Whether the melody crosses the clave once this statement joins the notes `before` it."""
    return check_clave([t % clave.length for t in before + _melody_on(m, at, end)], clave) is not None


def passage(style="plain", seed=1, bars=8, home=Key(9, "minor"), bpm=100, room=0.5, flow=True):
    """The choices for `bars` bars, as lines of plain words."""
    return (flow_choices if flow else choices)(style, seed, bars, home, bpm, room)[0]


def choices(style="plain", seed=1, bars=8, home=Key(9, "minor"), bpm=100, room=0.5):
    """The choices for `bars` bars: (lines of plain words, one record a bar). A record holds the bar's section,
    key, energy, chord, pad and bass notes, and on the bars they start, the bass onsets (steps from bar 1) and the
    motif; `sketch.py` plays them, so what is heard is what the words say."""
    rng = ComposerRng()
    rng.seed(seed)
    form, leading, rhythm = FORM[style], LEADING[style], RHYTHM[style]
    met = METERS["4/4"]
    clave = CLAVES[rhythm.clave] if rhythm.clave else None
    play = Play(rng, home, form, bpm, met, FLOW[style].distance)
    while play.bar < bars:
        play.next_section(room)
    theme = Theme(rng, life=form.life)
    out = [f"{style}, seed {seed}, home {home}, {bpm} bpm"]
    pad = bass = leans = None
    recs, sung = [], []   # sung: the melody's onsets so far
    for b in range(bars):
        s = play.section_at(b)
        key = s.key
        if s.start == b:
            i = play.sections.index(s)
            out.append("")
            out.append(explain_section(s, play.sections[i - 1] if i else None))
        # the chord: a section leans to open on its tonic; after a tension chord, where it leans weighs most
        def lands(c):
            return c.root == leans and c.quality in ("maj", "min")
        ch = choose_in_style(rng, key, VOCAB[style],
                             lambda c: LEAN if lands(c) or (s.start == b and c.root == 0) else 1)
        fn, why = function(ch, key)
        line = f"bar {b + 1}: {name(ch, key)} ({roman(ch, key)}), {fn}: {why}"
        if lands(ch):
            line += "; the tension resolves"
        rare = outside(ch, key, VOCAB[style])
        if rare:
            line += f". Unusual: {rare}"
        out.append(line)
        rec = {"bar": b, "section": s, "key": key, "energy": s.energy_at(b), "chord": ch}
        recs.append(rec)
        leans = _resolves_to(ch) if fn == "tension" else None
        # the bass, then the pad over it (drawn again while the two are muddy together)
        new_bass = choose_voicing(rng, ch, key, 1, member_range("bass"), bass, leading, on_bass=True)
        try:
            n = 3 if voicings(ch, key, 3, member_range("pad"), leading, ceiling=UNDER) else 4   # four for a 9th
            for tries in range(TRIES + 1):
                new = choose_voicing(rng, ch, key, n, member_range("pad"), pad, leading, ceiling=UNDER)
                muddy = check_band({"pad": new, "bass": new_bass}, key)
                if not muddy:
                    break
            line = _notes(key, new) if pad is None else explain(pad, new, key)
            if tries:
                line += f" (drawn again {'once' if tries == 1 else f'{tries} times'}: muddy with the bass)"
            out.append("  pad: " + line)
            pad = new
        except ValueError as e:
            out.append(f"  pad: rests ({e})")
            pad = None
        out.append("  bass: " + (_notes(key, new_bass) if bass is None else explain(bass, new_bass, key)))
        bass = new_bass
        rec["pad"], rec["bass"] = pad, bass
        for why in check_band({"pad": pad or [], "bass": bass}, key):
            out.append(f"  ruled out: {why}")
        # the bass rhythm, two bars at a time (a clave's length), busier with more energy
        if b % 2 == 0:
            feel = feel_for(style, "bass")
            n = 3 + round(4 * s.energy_at(b))
            tries = 0
            while True:
                on = choose_onsets(rng, met, n, rhythm, feel.pulse, bars=2, keep=(0,))
                crossed = check_onsets(on, met, 2, clave)
                if crossed is None or tries == TRIES:
                    break
                tries += 1
            line = f"  bass rhythm, bars {b + 1}-{b + 2} ({explain_feel(feel)}): {explain_onsets([o + b * met.bar for o in on], met)}"
            if clave is not None:
                c = clave.name.replace("_", " ")
                again = "once" if tries == 1 else f"{tries} times"
                line += (f"; sits with the {c} clave" + (f" (drawn again {again}: crossed)" if tries else "")
                         if crossed is None else f"; still {crossed} after {TRIES} draws")
            out.append(line)
            rec["bass_on"] = [o + b * met.bar for o in on]
        # the melody's motif, every SAY bars
        if b % SAY == 0:
            m, how = theme.next()
            at, where = b * met.bar, ""
            if clave is not None and _crosses(m, at, clave, bars * met.bar, sung):   # a statement sits with the clave, a bar later if need be
                if b + 1 < bars and not _crosses(m, at + met.bar, clave, bars * met.bar, sung):
                    at, where = at + met.bar, " (a bar later, to sit with the clave)"
                else:
                    where = " (crosses the clave either way)"
            rec["motif"], rec["motif_at"] = m, at
            sung += _melody_on(m, at, bars * met.bar)
            out.append(f"  melody{where}: {WORDS[how]}: " + " ".join(key.name(key.degree(d) % 12) for d in m.steps))
    return out, recs



def give_way(rng, notes, pad, bass, spans, key_at, lo, hi, leading):
    """When a phrase runs over the melody's top, the pad gives way: the phrase an octave down, the pad's chords
    under it voiced below it, still not muddy with the bass. (the notes, the new pad or None, lines)."""
    top = member_range("melody").high
    if max(m for _, _, m in notes) <= top:
        return notes, None, []
    down = [(st, length, m - 12) for st, length, m in notes]
    ceiling = min(m for _, _, m in down)
    if max(m for _, _, m in down) > top or ceiling <= member_range("pad").low:
        return notes, None, []
    out, prev = [n for n in pad if not lo <= n[0] < hi], None
    for sp in spans:
        if not lo <= sp.at < hi:
            continue
        was = sorted(m for st, _, m in pad if st == sp.at)
        if not was:
            continue
        if prev is None:                    # the voicing before the phrase, to move from smoothly
            prev = sorted(m for st, length, m in pad if st < sp.at <= st + length) or None
        under = [m for st, length, m in bass if st <= sp.at < st + length] or [bass[0][2]]
        try:
            for _ in range(TRIES + 1):
                v = choose_voicing(rng, sp.chord, key_at(sp.at), len(was), member_range("pad"), prev, leading,
                                   ceiling=ceiling)
                if not check_band({"pad": v, "bass": under}, key_at(sp.at)):
                    break
            else:
                return notes, None, []
        except ValueError:
            return notes, None, []
        out += [(sp.at, sp.length, m) for m in v]
        prev = v
    return down, sorted(out), [f"    the pad gives way: voiced under {note_name(key_at(lo), ceiling)}, the melody an "
                               "octave down to stay under C7"]


def band(rng, style, plan, play, spans, key_at, bass, melody, percussion, clave, kit_why, end):
    """Salsa's band over the whole play (task 3.4c): a part each phrase (`arrange.py`), the lead calling or
    leaving room for it, the montuno a section, the horns a phrase, the bass walking up into some sections and the
    band breaking on the clave's strokes at others. (keys, horns, parts, breaks, bass, melody, percussion). `end`:
    the clip's last step, where the lead is cut too."""

    def crosses(notes):                  # the lead with bars left out, over the whole play and up to the clip's end
        return clave and clave.two_sided and any(check_clave(sorted({n[0] % clave.length for n in ns}), clave)
                                                 for ns in (notes, [n for n in notes if n[0] < end]))
    met, ar, phrase = METERS["4/4"], ARRANGE[style], FORM[style].phrase
    parts, breaks, said = phrase_parts(rng, ar, play.sections, phrase, play.bar)
    for ln in said:
        bar = _bar_of(ln) - 1
        next(p for p in plan if p["section"].start <= bar < p["section"].end)["lines"].append(ln)
    for p in plan:
        p["parts"] = [(at, x.name) for at, s, x in parts if s is p["section"]]
    kit_why.append(("arrangement", check_parts(parts, ar)))
    # the montuno, a pattern a section
    keys, pat = [], None
    if KEYS[style]:
        for p in plan:
            s = p["section"]
            notes, pat, lines = montuno_part(rng, KEYS[style], spans, key_at, s.start, s.bars, met, s.energy, pat,
                                             clave)
            p["lines"] += lines
            p["keys"] = pat
            keys += notes
    # the horns a phrase, and the lead around them
    horns, loops, hf = [], {}, HORNS[style]
    for at, s, x in parts:
        lo, hi = at * met.bar, (at + phrase) * met.bar
        played = "out"
        if hf:
            notes, played, lines = horn_part(rng, hf, x.horns, spans, key_at, at, phrase, met, s.energy_at(at), loops,
                                             clave, phrase, [n[0] for n in horns])
            horns += notes
            p = next(p for p in plan if p["section"] is s)
            p["lines"] += [f"  bar {at + 1}, {ln.strip()}" for ln in lines]
            p.setdefault("horns", []).append((at, played))
        was = melody
        if x.lead == "out":
            melody = silence(melody, lo, hi)
        elif x.lead == "call" and played == "coro":
            for k in range(phrase // 2):
                if (k + 1) % hf.coro.every == 0:
                    melody = silence(melody, lo + 2 * k * met.bar, lo + (2 * k + 2) * met.bar)
        if melody is not was and crosses(melody):
            melody = was                     # what's left of the lead would cross the clave: it sings on
            next(p for p in plan if p["section"] is s)["lines"].append(
                f"  melody, bar {at + 1}: sings on through the horns' bars, to stay with the clave")
    # the bass's walk-ups, and the breaks
    walk, r = part(style, "members", "bass").get("walk", 0), bass_range(BASS[style])
    for s in play.sections[:-1]:
        b = s.end - 1
        lo, side = b * met.bar, strokes(clave, b, met)
        if len(side) != 3:              # only on the clave's 3 side
            continue
        if b in breaks:
            hit = [lo + t for t in side]
            nxt = [ahead(st, met) if st == hit[-1] else st for st in hit]
            was, melody = melody, silence(melody, lo, lo + met.bar)
            if crosses(melody):
                melody = was                 # what's left of the lead would cross the clave: it sings on
            near = next((m for st, _, m in reversed(bass) if st < lo), round(r.mid))
            bass = [n for n in bass if not lo <= n[0] < lo + met.bar]
            for st, at in zip(hit, nxt):
                near = _nearest(key_at(at).tonic + _tone(chord_at(spans, at).chord, "root"), near, r)
                bass.append((st, 9 if st != hit[-1] else None, near))
            bass = held(sorted(bass, key=lambda n: n[0]), play.bar * met.bar)
            keys = silence(keys, lo, lo + met.bar) + [(st, 9, m) for st, at in zip(hit, nxt)
                                                      for m in voice(chord_at(spans, at).chord, key_at(at), 1, True)]
            if hf:
                horns = silence(horns, lo, lo + met.bar) + harmonize(
                    hits(spans, key_at, hit, lambda st: nxt[hit.index(st)]), spans, key_at, hf.voices)
            percussion = [h for h in percussion if not lo <= h[0] < lo + met.bar or h[4] == "clave"
                          or h[0] - lo in side or h[4] == "timbales" and h[1] == 3]
        elif walk and rng.rnd(100) < walk:
            t = next((m for st, _, m in bass if st == lo + 72), None)
            key = key_at((b + 1) * met.bar)
            under = [m for m in range(t - 12, t) if (m - key.tonic) % 12 in {key.degree(d) % 12 for d in range(7)}][-3:] \
                if t else []
            if len(under) == 3 and under[0] >= r.low:
                bass = [n for n in bass if not lo <= n[0] < lo + 72] + list(zip((lo, lo + 36, lo + 60), (36, 24, 12),
                                                                                under))
                bass = held(sorted(bass, key=lambda n: n[0]), play.bar * met.bar)
                next(p for p in plan if p["section"] is s)["lines"].append(
                    f"  bass, bar {b + 1}: walks up into the next section")
    keys.sort(key=lambda n: n[0])
    horns.sort(key=lambda n: n[0])
    if KEYS[style]:
        kit_why.append(("keys", check_keys(keys, spans, key_at, met, clave)))
    if hf:
        kit_why.append(("horns", check_horns(horns, hf.voices, clave)))
    return keys, horns, parts, breaks, bass, melody, percussion


def rock_band(rng, style, plan, play, spans, key_at, bass, melody, drums, kit_why, ruled):
    """Power rock's band over the whole play (task 3.4d): a part each phrase (`arrange.py`: verse, pre-chorus,
    chorus), the rhythm guitar a phrase in its part's group, the bass locking to the guitar where its pattern says,
    the snare building at a pre-chorus's end, the band stopping on the one at some section ends, double bass in the
    loud parts; then the second lead (twin harmony in a chorus, trading licks in a duel) and the leads' bends and
    vibrato. `ruled`: the parts, drawn before the drums (`phrase_parts`). (guitar {track: notes}, muted steps,
    parts, breaks, builds, bass, drums, bends, vibrato, the first lead, the second, its bends, its vibrato)."""
    met, ar, phrase, gf = METERS["4/4"], ARRANGE[style], FORM[style].phrase, GUITAR[style]
    whole = play.bar * met.bar
    parts, breaks, said = ruled
    for ln in said:
        bar = _bar_of(ln) - 1
        next(p for p in plan if p["section"].start <= bar < p["section"].end)["lines"].append(ln)
    for p in plan:
        p["parts"] = [(at, x.name) for at, s, x in parts if s is p["section"]]
    kit_why.append(("arrangement", check_parts(parts, ar)))
    # the rhythm guitar a phrase, the bass locked to it where its pattern says
    guitar, muted, pats, near, bnear = {t.name: [] for t in gf.tracks}, [], {}, None, None
    for at, s, x in parts:
        notes, mu, pat, near, lines = guitar_part(rng, gf, x.guitar, spans, key_at, at, phrase, met,
                                                  pats.get(x.guitar), near)
        pats[x.guitar] = pat
        for k, ns in notes.items():
            guitar[k] += ns
        muted += mu
        p = next(p for p in plan if p["section"] is s)
        p["lines"] += lines
        p.setdefault("guitar", []).append((at, x.name, pat))
        if pat.bass:
            lo, hi = at * met.bar, (at + phrase) * met.bar
            bnear = next((m for st, _, m in reversed(bass) if st < lo), bnear)
            locked, bnear = lock_bass(notes[gf.tracks[0].name], spans, key_at, met, bnear,
                                           bass_range(BASS[style]))
            bass = sorted(silence(bass, lo, hi) + locked, key=lambda n: n[0])
            p["lines"].append(f"  bass, bars {at + 1}-{at + phrase}: locks to the guitar's {pat.name}")
    # the pre-chorus's last bar: the snare building into the chorus
    builds = [at + phrase - 1 for at, _, x in parts if x.name == ar.build]
    dr = DRUMMER[style]
    for b in builds:
        lo = b * met.bar
        drums = [h for h in drums if not lo <= h[0] < lo + met.bar]
        drums += [(lo, 6, KIT["kick"], _vel(dr, "kick", 0, 1.0), "kick"),
                  (lo, 6, KIT["crash"], _vel(dr, "crash", 0, 1.0), "crash")]
        steps = list(range(lo + 12, lo + met.bar // 2, 12)) + list(range(lo + met.bar // 2, lo + met.bar, 6))
        for k, st in enumerate(steps):
            drums.append((st, 6, KIT["snare"], 60 + 55 * k // len(steps), "snare"))
        p = next(p for p in plan if p["section"].start <= b < p["section"].end)
        p["drums"] = [ln for ln in p["drums"] if not ln.startswith(f"  drums, bar {b + 1}:")] + [
            f"  drums, bar {b + 1}: the snare builds, 8ths then 16ths, into the chorus"]
    # the stops: the band hits the one and lets it ring, the drums fill in (or build, at a pre-chorus's end)
    r = bass_range(BASS[style])
    for b in breaks:
        lo, hi = b * met.bar, (b + 1) * met.bar
        key, ch = key_at(lo), chord_at(spans, lo).chord
        for t in gf.tracks:
            was = [n for n in guitar[t.name] if n[0] < lo]
            last = min((m for st, _, m in was if st == was[-1][0]), default=None) if was else None
            root = guitar_root(key.tonic + ch.root, last, VOICINGS[t.voicing])
            guitar[t.name] = silence(guitar[t.name], lo, hi) + [(lo, met.bar, m) for m in power(ch, root).values()]
        muted = [m for m in muted if not lo <= m < hi]
        near = next((m for st, _, m in reversed(bass) if st < lo), round(r.mid))
        bass = sorted(silence(bass, lo, hi) + [(lo, met.bar, _nearest(key.tonic + ch.root, near, r))],
                      key=lambda n: n[0])
        if b not in builds:
            e = play.section_at(b).energy_at(b)
            drums = [h for h in drums if not lo <= h[0] < hi]
            drums += [(lo, 6, KIT["kick"], _vel(dr, "kick", 0, e), "kick"),
                      (lo, 6, KIT["crash"], _vel(dr, "crash", 0, e), "crash")]
            fill, words = _fill(rng, dr, hi - met.bar // 2, hi, e, False)
            drums += [(st, 6, KIT[v], _vel(dr, v, (st % met.bar) // 6, e), v) for st, v in fill]
            p = next(p for p in plan if p["section"].start <= b < p["section"].end)
            p["drums"] = [ln for ln in p["drums"] if not ln.startswith(f"  drums, bar {b + 1}:")] + [
                f"  drums, bar {b + 1}: the stop, kick and crash on the one, then {words}"]
    if DOUBLE[style]:                    # both feet: double bass in the loud parts, bursts into some phrases
        drums, said = double_kick(rng, DOUBLE[style], dr, drums,
                                  [(at * met.bar, (at + phrase) * met.bar, x.name, s.energy_at(at)) for at, s, x in parts],
                                  met, set(breaks) | set(builds))
        for lo, ln in said:
            next(p for p in plan if p["section"].start <= lo // met.bar < p["section"].end)["drums"].append(ln)
        up = [(at * met.bar, (at + phrase) * met.bar) for at, _, x in parts if x.name in DOUBLE[style].parts]
        bass = [(st, n, m + 12 if any(lo <= st < hi for lo, hi in up) and m + 12 <= r.high and m < UP_FROM else m)
                for st, n, m in bass]                # the bass an octave up, out of the double bass's low end
    drums.sort(key=lambda h: (h[0], h[2]))
    for k in guitar:
        guitar[k].sort(key=lambda n: (n[0], n[2]))
    kit_why.append(("guitar", check_guitar(guitar, gf, spans, key_at, met)))
    kit_why.append(("drums after the stops and builds", check_drums(drums, met, whole)))
    # the two leads: in twin harmony in a chorus, trading licks in a duel
    lead, second, licks, near = part(style, "members", "melody"), [], [], None
    floor = member_range("melody").low - 1
    for at, s, x in parts:
        lo, hi = at * met.bar, (at + phrase) * met.bar
        if x.lead == "twin":
            second += twin([n for n in melody if lo <= n[0] < hi], key_at, floor)
        elif x.lead == "duel":
            near = next((m for st, _, m in reversed(melody) if st < lo), 76)
            one, two, lines = duel(rng, lead.get("licks", {"run": 1}), lead.get("fast", 0), spans, key_at, at,
                                   phrase, met, near)
            melody = sorted(silence(melody, lo, hi) + one, key=lambda n: n[0])
            second += two
            licks.append((lo, hi))
            next(p for p in plan if p["section"] is s)["lines"] += lines
    second.sort(key=lambda n: n[0])
    if second:
        kit_why.append(("leads", check_leads(melody, second, key_at, spans, licks)))
    # the leads' bends and vibrato: the twin bends with the first lead
    bent = lead_bends(rng, melody, key_at, lead["bends"]) if lead.get("bends") else []
    at = {st: (steps, semis) for st, steps, semis in bent}
    bent2 = [(st, at[st][0], k) for st, length, m in second if st in at
             for k in [2 if (m - 2 - key_at(st).tonic) % 12 in {key_at(st).degree(d) % 12 for d in range(7)} else 1]
             if m - k > floor]
    shakes = vibrato(melody) if lead.get("vibrato") else []
    return guitar, sorted(muted), parts, breaks, builds, bass, drums, bent, shakes, melody, second, bent2, \
        vibrato(second) if lead.get("vibrato") else []


def flow_choices(style="plain", seed=1, bars=8, home=Key(9, "minor"), bpm=100, room=0.5, layers=True):
    """Task 3.2's choices for `bars` bars: (lines of plain words, the take). The take holds the notes ("pad",
    "bass", "melody": (step, length, MIDI note)), a record a bar like `choices`' (bar, section, key, energy, its
    first chord) and a record a section ("plan": its family, its passes in words, its bass pattern, its phrases)
    for the summary. Whole sections are drawn, then cut at the clip's end. `layers`: who plays when (task 3.6),
    for the styles that list it; off, every member plays throughout (the A/B's earlier side)."""
    rng = ComposerRng()
    rng.seed(seed)
    form, leading, rhythm, vocab = FORM[style], LEADING[style], RHYTHM[style], VOCAB[style]
    met = METERS["4/4"]
    end = bars * met.bar
    clave = CLAVES[rhythm.clave] if rhythm.clave else None
    if form.home:                                # the style draws its home's mode (power rock: mostly major)
        home = Key(home.tonic, _draw(rng, form.home) or home.scale)
    play = Play(rng, home, form, bpm, met, FLOW[style].distance)
    while play.bar < bars:
        play.next_section(room)
    theme = Theme(rng, life=form.life, develop=DEVELOPS[style])

    def key_at(step):
        return play.section_at(min(step, play.bar * met.bar - 1) // met.bar).key

    # the chords, section by section
    spans, plan, fam = [], [], None
    for s in play.sections:
        seam = (spans[-1].chord, play.section_at(s.start - 1).key) if spans else None
        sp, fam, lines = progression(rng, FLOW[style], s.key, vocab, s.start, s.bars, met, form.phrase, fam,
                                     s.kind, seam)
        spans += sp
        plan.append({"section": s, "family": fam, "lines": lines,
                     "passes": [ln.split(": ", 2)[-1] for ln in lines if ln.startswith("  bars ")]})
    every = [{"bar": b, "section": play.section_at(b), "energy": play.section_at(b).energy_at(b)}
             for b in range(play.bar)]
    ruled = None
    if GUITAR[style]:                            # power rock's parts first, so the drummer keeps time by them
        ruled = phrase_parts(rng, ARRANGE[style], play.sections, form.phrase, play.bar)
        for r in every:
            first = next(x for at, s, x in ruled[0] if s is r["section"])
            r["loud"] = first.when == "high"
    whole, half = play.bar * met.bar, feel_for(style, "drums").pulse == "half"
    kit_why = []
    for p in plan:
        p["drums"], p["percussion"] = [], []

    def draw_drums():
        if not DRUMMER[style]:
            return []
        hits, said = drum_part(rng, DRUMMER[style], every, met, form.phrase, whole, half)
        for s, line in said:
            next(p for p in plan if p["section"] is s)["drums"].append(line)
        kit_why.append(("drums", check_drums(hits, met, whole, half, DRUMMER[style].fixed)))
        return hits
    # the bass on its pattern, carrying on from section to section; an 808 (trap) on the drummer's kicks, so the
    # drums come first
    bass, slides, pat, near, bf = [], [], None, None, BASS[style]
    drums = draw_drums() if bf.kick else []
    kicks = sorted({h[0] for h in drums if h[4] == "kick"})
    quiet = quiet_spans(drums, met, whole) if bf.kick else []
    for p in plan:
        s = p["section"]
        if bf.kick:
            notes, sl, lines = bass_808(rng, bf, spans, key_at, kicks, s.start, s.bars, met, s.energy, near,
                                           quiet)
            slides += sl
            pat = None
        else:
            notes, pat, lines = bass_part(rng, bf, spans, key_at, s.start, s.bars, met, s.energy, pat, clave,
                                          [n[0] for n in bass], near)
        bass += notes
        near = notes[-1][2] if notes else near
        p["pattern"], p["bass"], p["lines"] = pat, lines[0].split(": ", 1)[1], p["lines"] + lines
    bass = held(bass, play.bar * met.bar)
    why = check_bass(bass, met, clave, bf) or (check_808(bass, slides, kicks, spans, key_at, quiet) if bf.kick
                                          else None)
    # the pad: each chord voiced under the melody's room, moving smoothly, not muddy with the bass under it
    pad, prev, again, rests = [], None, 0, 0
    for sp in spans:
        key, ch = key_at(sp.at), sp.chord
        under = [m for st, length, m in bass if st <= sp.at < st + length] or [bass[0][2]]
        try:
            want = part(style, "members", "pad").get("voices", 3)                             # trap: 2
            n = want if voicings(ch, key, want, member_range("pad"), leading, ceiling=UNDER) else \
                3 if voicings(ch, key, 3, member_range("pad"), leading, ceiling=UNDER) else 4   # four for a 9th
            for tries in range(TRIES + 1):
                v = choose_voicing(rng, ch, key, n, member_range("pad"), prev, leading, ceiling=UNDER)
                if not check_band({"pad": v, "bass": under}, key):
                    break
            again += tries
            pad += [(sp.at, sp.length, m) for m in v]
            prev = v
        except ValueError:
            rests, prev = rests + 1, None
    # the melody, a phrase at a time, over the pad
    melody, loop = [], None
    for p in plan:
        s, p["phrases"] = p["section"], []
        if LOOPS[style]:                         # a riff going round (trap), not shaped over the phrase
            lo, hi = s.start * met.bar, s.end * met.bar
            floor = max((m for st, length, m in pad if st < hi and st + length > lo), default=UNDER)
            notes, loop, lines = loop_melody(rng, LOOPS[style], spans, s.key, s.start, s.bars, met, floor, loop,
                                             form.phrase)
            bad = check_loop(notes, spans, s.key, floor)
            p["lines"] += lines + ([f"    ruled out: {bad}"] if bad else [])
            p["loop"] = lines[0].split(": ", 1)[1]
            melody += notes
            continue
        for at in range(s.start, s.end, form.phrase):
            lo, hi = at * met.bar, (at + form.phrase) * met.bar
            floor = max((m for st, length, m in pad if st < hi and st + length > lo), default=UNDER)
            sung, two = [n[0] for n in melody], clave if clave and clave.two_sided else None
            for tries in range(REDRAWS + 2):         # drawn again when the check rules it out, then the plain one
                notes, lines = plain_phrase(spans, s.key, at, form.phrase, met, floor, two) if tries > REDRAWS else \
                    phrase_melody(rng, theme, spans, s.key, at, form.phrase, met, floor, clave, sung)
                if part(style, "members", "melody").get("scale") == "pentatonic":    # power rock's lead
                    notes, moved = pentatonic(notes, spans, s.key)
                    lines = lines + ([f"    on the pentatonic: {moved} note{'s' * (moved != 1)} moved onto it"]
                                     if moved else [])
                notes, under, said = give_way(rng, notes, pad, bass, spans, key_at, lo, hi, leading)
                bad = check_phrase(notes, spans, s.key, met, form.phrase, at, two, sung)
                if not bad:
                    break
                p["lines"].append(f"    drawn again: {bad}")
            if under is not None:
                pad[:] = under
            p["lines"] += lines + said + ([f"    ruled out: {bad}"] if bad else [])
            p["phrases"].append(lines)
            melody += notes
    # the drums and the percussion over the whole play (task 3.3), their words with each section
    if not bf.kick:
        drums = draw_drums()
    # the arp (synthwave): a shape a section, round and round over each chord's tones
    arp, shape, looped = [], None, []
    if ARPS[style]:
        arng = ComposerRng()                      # the loops' own seed (task 3.12): the play is the same without them
        arng.seed(seed ^ 0x100B5)
        for p in plan:
            s = p["section"]
            notes, shape, lines, n = arp_part(rng, ARPS[style], spans, key_at, s.start, s.bars, met, s.energy, shape,
                                              form.phrase, arng)
            p["lines"] += lines
            p["arp"] = lines[0].split(": ", 1)[1]
            arp += notes
            if n:
                looped.append((s.start * met.bar, (s.start + s.bars) * met.bar))
        kit_why.append(("arp", check_arp(arp, spans, key_at)))
    percussion = []
    if PERCUSSION[style]:
        percussion, said = percussion_part(rng, PERCUSSION[style], every, met, whole, clave)
        for s, line in said:
            next(p for p in plan if p["section"] is s)["percussion"].append(line)
        kit_why.append(("percussion", check_percussion(percussion, met, whole, clave)))
    # salsa's band (task 3.4c): the part each phrase plays, the breaks, the bass's walk-ups, the montuno, the horns
    keys, horns, parts, breaks = [], [], [], []
    if ARRANGE[style] and not GUITAR[style]:
        keys, horns, parts, breaks, bass, melody, percussion = band(rng, style, plan, play, spans, key_at, bass, melody,
                                                                    percussion, clave, kit_why, end)
        why = check_bass(bass, met, clave, BASS[style])
    # power rock's band (task 3.4d): the parts, the doubled rhythm guitar, the builds and stops, the lead's bends
    guitar, muted, builds, bent, shakes, second, bent2, shakes2 = {}, [], [], [], [], [], [], []
    scratched = []
    if GUITAR[style]:
        guitar, muted, parts, breaks, builds, bass, drums, bent, shakes, melody, second, bent2, shakes2 = rock_band(
            rng, style, plan, play, spans, key_at, bass, melody, drums, kit_why, ruled)
        why = check_bass(bass, met, clave, BASS[style])
        sc = GUITAR[style].scratch
        if sc:                               # the scratch lane (task 3.10), with its own seed so the rest stays
            srng = ComposerRng()
            srng.seed(seed ^ 0x5C2A7)
            quiet = set(breaks) | {b - 1 for b in breaks} | set(builds)
            for at, s, x in parts:
                if at == 0 or s.energy_at(at) < sc.energy or sc.parts and x.name not in sc.parts:
                    continue
                n = 0
                for b in range(at, at + form.phrase):
                    if b in quiet:
                        continue
                    lo, hi = b * met.bar, (b + 1) * met.bar
                    lead = GUITAR[style].tracks[0].name
                    got = scratch_lane(srng, sc, [y for y in guitar[lead] if y[0] < hi], lo, hi, met)
                    for st in got:
                        key, ch = key_at(st), chord_at(spans, st).chord
                        for t in GUITAR[style].tracks:
                            was = [y for y in guitar[t.name] if y[0] < st]
                            near = min(m for a, _, m in was if a == max(a for a, _, _ in was)) if was else None
                            guitar[t.name].append((st, sc.length, guitar_root(key.tonic + ch.root, near,
                                                                              VOICINGS[t.voicing])))
                    scratched += got
                    n += len(got)
                if n:
                    next(p for p in plan if p["section"] is s)["lines"].append(
                        f"  guitar, bars {at + 1}-{at + form.phrase}: {n} scratch strokes between the hits")
            for k in guitar:
                guitar[k].sort(key=lambda y: (y[0], y[2]))
            kit_why.append(("scratch lane", check_scratch(guitar, scratched, sc, met)
                            or check_guitar(guitar, GUITAR[style], spans, key_at, met)))
    elif part(style, "members", "melody").get("bends") or part(style, "members", "melody").get("vibrato"):
        lead = part(style, "members", "melody")    # a soulful nudge's (task 3.9): any lead bends and shakes
        bent = lead_bends(rng, melody, key_at, lead["bends"]) if lead.get("bends") else []
        sung = {st: m for st, _, m in melody}        # a bend starts under its note: never down in the pad
        bent = [b for b in bent if not any(at <= b[0] < at + n and m >= sung[b[0]] - b[2] for at, n, m in pad)]
        shakes = vibrato(melody) if lead.get("vibrato") else []
    # who plays when (task 3.6): the band a phrase by the energy, with its own seed so the notes stay the same
    layered, ly = [], LAYERS[style] if layers else None
    if ly:
        lrng = ComposerRng()
        lrng.seed(seed ^ 0x1A7E5)
        layered = plan_layers(lrng, ly, play.sections, form.phrase, bars)
        kit_why.append(("layers", check_layers(layered, ly)))
        notes = {"pad": pad, "bass": bass, "arp": arp, "melody": melody, "keys": keys, "horns": horns,
                 "drums": drums, "percussion": percussion}
        changed = slow_changes(lrng, ly, layered, notes, spans, key_at, met)
        for x in layered:
            lo, hi = x.at * met.bar, (x.at + x.bars) * met.bar
            for r in [r for r in ly.join if r not in x.playing] + ["melody"] * (not x.melody):
                if r == "guitar":
                    guitar = {k: rest(ns, lo, hi) for k, ns in guitar.items()}
                    continue
                notes[r][:] = rest(notes[r], lo, hi)
                if r == "bass":
                    slides = [sl for sl in slides if not lo <= sl[0] < hi]
                if r == "melody":
                    bent = [b for b in bent if not lo <= b[0] < hi]
                    shakes = [v for v in shakes if not lo <= v[0] < hi]
                    second = rest(second, lo, hi)                  # power rock's second lead rests with it
                    bent2 = [b for b in bent2 if not lo <= b[0] < hi]
                    shakes2 = [v for v in shakes2 if not lo <= v[0] < hi]
            band_ = ", ".join(sorted(x.playing)) + (" and the melody" if x.melody else "")
            words = [f"  band, bars {x.at + 1}-{x.at + x.bars}: {band_}" + "".join(f"; {w}" for w in x.said)]
            words += [f"  bars {x.at + 1}-{x.at + x.bars}: {w}" for y, w in changed if y is x]
            next(p for p in plan if p["section"] is x.section)["lines"] += words
    for p in plan:
        p["lines"] += p["drums"] + p["percussion"]
    # cut at the clip's end, in words and notes
    out = [f"{style}, seed {seed}, home {home}, {bpm} bpm (flow)"]
    for i, p in enumerate(plan):
        s = p["section"]
        if s.start >= bars:
            break
        out += ["", explain_section(s, plan[i - 1]["section"] if i else None)] + p["lines"]
    if why:
        out.append(f"  bass check: {why}")
    out += [f"  {role} check: {why}" for role, why in kit_why if why]
    out.append(f"  pad: each chord voiced under the melody, moving the shortest way"
               + (f"; drawn again {again} times (muddy with the bass)" if again else "")
               + (f"; rests under {rests} chords" if rests else ""))

    def cut(notes):
        return [(st, min(length, end - st), m) for st, length, m in notes if st < end]
    recs = []
    for b in range(bars):
        s = play.section_at(b)
        recs.append({"bar": b, "section": s, "key": s.key, "energy": s.energy_at(b),
                     "chord": chord_at(spans, b * met.bar).chord})
    # a chord changing inside a bar (power rock's "I IV", salsa's "i iv"): its own entry, from the beat it sounds
    changes = [{"bar": sp.at // met.bar, "at": sp.at % met.bar, "key": play.section_at(sp.at // met.bar).key,
                "chord": sp.chord} for sp in spans if sp.at % met.bar and sp.at < end]
    take = {"pad": cut(pad), "bass": cut(bass), "melody": cut(melody), "arp": cut(arp), "bars": recs, "changes": changes,
            "keys": cut(keys), "horns": cut(horns), "parts": [x for x in parts if x[0] < bars],
            "breaks": [b for b in breaks if b < bars], "builds": [b for b in builds if b < bars],
            "guitar": {k: cut(ns) for k, ns in guitar.items()}, "muted": [m for m in muted if m < end],
            "scratch": [m for m in scratched if m < end], "looped": [(a, min(b, end)) for a, b in looped if a < end],
            "bends": [x for x in bent if x[0] < end], "vibrato": [(st, min(n, end - st)) for st, n in shakes if st < end],
            "lead2": cut(second), "bends2": [x for x in bent2 if x[0] < end],
            "vibrato2": [(st, min(n, end - st)) for st, n in shakes2 if st < end],
            "slides": [sl for sl in slides if sl[0] + sl[1] < end],
            "drums": [h for h in drums if h[0] < end], "percussion": [h for h in percussion if h[0] < end],
            "plan": [p for p in plan if p["section"].start < bars], "spans": [s for s in spans if s.at < end],
            "layers": [x for x in layered if x.at < bars]}
    return out, take


def _bar_of(line):
    """The bar a line of words is about ("  drums, bar 8: ...", or the first of "  drums, bars 17-24: ...")."""
    m = re.search(r"bars? (\d+)(?:-\d+)?:", line)
    return int(m[1]) if m else 0


def _bars_said(lines, last):
    out = []
    for ln in lines:
        m = re.search(r"(bars? \d+(?:-\d+)?):", ln)
        if _bar_of(ln) <= last:
            out.append(f"{m[1] if m else 'bar 0'}, {ln.split(': ', 1)[1]}")
    return out


def _merge(items, name_at, bars):
    """Labels said section by section ((first bar, end bar, label), bars from 0) as one clause: "X throughout", or
    each label once with where it plays ("in the verses", or its bars when its places share a name with another's)."""
    items = [(a, min(b, bars), x) for a, b, x in items if a < bars and x]
    order = list(dict.fromkeys(x for _, _, x in items))
    if len(order) == 1:
        span = sum(b - a for a, b, _ in items)
        return order[0] + (" throughout" if span == bars else f" ({_bars(items)})")
    names = {x: {name_at(b) for a, e, y in items if y == x for b in range(a, e)} for x in order}
    out = []
    for x in order:
        mine = [(a, b, y) for a, b, y in items if y == x]
        shared = any(names[x] & names[y] for y in order if y != x)
        out.append(f"{x} ({_bars(mine) if shared or not names[x] else _places(names[x], name_at, bars)})")
    return "; ".join(out)


def _bars(items):
    runs = []
    for a, b, _ in sorted(items):
        if runs and runs[-1][1] == a:
            runs[-1][1] = b
        else:
            runs.append([a, b])
    return "bar" + "s" * (len(runs) > 1 or runs[0][1] - runs[0][0] > 1) + " " + ", ".join(
        f"{a + 1}-{b}" if b - a > 1 else f"{a + 1}" for a, b in runs)


def _places(names, name_at, bars):
    """ "the verses and the chorus": each name, plural when it comes round more than once."""
    said = []
    for n in sorted(names, key=lambda n: min(b for b in range(bars) if name_at(b) == n)):
        times = sum(1 for b in range(bars) if name_at(b) == n and (b == 0 or name_at(b - 1) != n))
        said.append("the " + (n + ("es" if n.endswith("s") else "s") if times > 1 else n))
    return "in " + " and ".join(", ".join(said[:-1]) and [", ".join(said[:-1]), said[-1]] or said)


def _short(why, most=50):
    """A pattern's why, cut to its first clause when it runs long."""
    return why if len(why) <= most else why.split(", ")[0]


def _events(lines, bars):
    """A member's moments ("a fill of 2 beats in 16ths (snare, kick)" at bar 8, ...) counted by kind: "a fill (9
    times), the snare builds"."""
    kinds = []
    for ln in lines:
        if _bar_of(ln) > bars:
            continue
        w = re.sub(r" \([^)]*\)", "", ln.split(": ", 1)[1])
        kinds.append(re.split(r" of \d|, |: | for the ", w)[0])
    count = {k: kinds.count(k) for k in dict.fromkeys(kinds)}
    return ", ".join(k + (f" ({n} times)" if n > 1 else "") for k, n in count.items())


def _said(style, seed, bars, bpm, take, met=METERS["4/4"]):
    """The summary's lines by member (task 3.7: the shape agreed Oct 24, grouped by member across the clip and kept
    to about a dozen lines however long the clip; DadCraft, Oct 27)."""
    plan, n = take["plan"], FORM[style].phrase
    home = plan[0]["section"].key
    out = {"head": f"{style.replace('_', ' ')}, {bars} bars (about {bars * 4 * 60 // bpm // 60}:"
                   f"{bars * 4 * 60 // bpm % 60:02d}), {home}, {bpm} BPM, seed {seed}"}
    spans = [(p["section"].start, p["section"].end) for p in plan]
    parts = {at + i: x.name for at, _, x in take.get("parts", []) for i in range(n)}
    if parts:
        def name_at(b):
            return parts.get(b, "")
    else:
        def name_at(b):
            return next(p["section"].kind for p in plan if p["section"].start <= b < p["section"].end) + " section"
    # the form: the parts (salsa's, power rock's) or the sections, then what breaks it
    if parts:
        runs = [(k, [b for b, _ in g]) for k, g in groupby(((b, parts.get(b, "")) for b in range(bars)),
                                                          key=lambda y: y[1]) if k]
    else:
        runs = [(p["section"].kind, list(range(p["section"].start, min(p["section"].end, bars)))) for p in plan]
    words = {"cuerpo": "cuerpo", "montuno": "montuno (the coro)", "mambo": "mambo (the horns' riff)"}
    stop = ARRANGE[style].stop if ARRANGE.get(style) else False
    downs = [str(x.at + 1) for x in take.get("layers", []) if x.down]
    extra = ([f"a stop at bar {b + 1}" if stop else f"a break at bar {b + 1}" for b in take["breaks"]]
             + [f"the snare builds at bar {b + 1}" for b in take.get("builds", [])]
             + [f"a breakdown at bar{'s' * (len(downs) > 1)} {', '.join(downs)}" for _ in downs[:1]])
    out["form"] = ("Form: " + " · ".join(f"{words.get(k, k)} {bs[0] + 1}-{bs[-1] + 1}" for k, bs in runs)
                   + (f"; {', '.join(extra)}" if extra else "") + ".")
    # the chords: each family once, where it plays, then how its rounds vary
    items, varied, rounds = [], [], 0
    for p in plan:
        s, f = p["section"], p["family"]
        per = {len(x) for x in f.bars}
        runs_ = [len(list(g)) for _, g in groupby(" ".join(x) for x in f.bars)]
        pace = ("one chord throughout" if len(runs_) == 1 and per == {1} else
                "a chord a bar" if per == {1} and set(runs_) == {1} else
                f"a chord every {runs_[0]} bars" if per == {1} and len(set(runs_)) == 1 else
                "a chord every bar or two" if per == {1} else "two chords a bar" if per == {2} else
                "chords every bar or half bar")
        items.append((s.start, s.end, f"{f.name}{f' in {s.key}' if s.key != home else ''}, "
                                      f"{chart(f.spans(s.key, 0, met), s.key, met)} ({f.chords}), {pace}"))
        passes = p["passes"][:max(1, (min(s.end, bars) - s.start) // f.loop)]
        rounds += len(passes)
        varied += [[x for x in w.split("; ") if not x.startswith("lands home")] for w in passes if w != "as written"]
    varied = [w for w in varied if w]
    kinds = list(dict.fromkeys(w[0] for w in varied))
    out["chords"] = (f"Chords: {_merge(items, name_at, bars)}. {len(varied)} of {rounds} rounds vary beyond landing "
                     "home"
                     + (f", for example {'; '.join(kinds[:3])}" if kinds else "") + ".")
    # the bass, the kick under it
    items = [(p["section"].start, p["section"].end,
              p["bass"].split("; ")[0] if p["pattern"] is None else p["pattern"].name
              + (f": {_short(p['pattern'].why)}" if p["pattern"].why else "")) for p in plan]
    kicks = {h[0] for h in take["drums"] if h[4] == "kick"}
    locked = sum(1 for x in take["bass"] if x[0] in kicks)
    out["bass"] = (f"Bass: {_merge(items, name_at, bars)}"
                   + (f"; {len(take['slides'])} slides" if take.get("slides") else "")
                   + (f"; the kick lands with {round(100 * locked / max(1, len(take['bass'])))}% of its notes"
                      if kicks else "") + ".")
    if take.get("guitar"):                     # power rock's rhythm guitars, a phrase at a time (task 3.4d)
        items = [(at, at + n, pat.name + (f": {_short(pat.why)}" if pat.why else ""))
                 for p in plan for at, _, pat in p.get("guitar", [])]
        out["guitar"] = ("Guitars (two, left and right, power chords in their own octaves; no pad): "
                         + _merge(items, name_at, bars) + ".")
    if any(p.get("keys") for p in plan):        # salsa's montuno piano (task 3.4c)
        items = [(p["section"].start, p["section"].end, p["keys"].name) for p in plan if p.get("keys")]
        out["keys"] = "Keys (the montuno piano plays the chords; no pad): " + _merge(items, name_at, bars) + "."
    if take.get("horns"):                       # the trombones, part by part (task 3.4c)
        said = []
        for p in plan:
            for ln in p["lines"]:
                m = re.match(r"\s*bar (\d+), horns: (.*)", ln)
                if m:
                    said.append((int(m[1]) - 1, m[2].replace(" (kept)", "")))
        items = [(a, said[i + 1][0] if i + 1 < len(said) else bars, w) for i, (a, w) in enumerate(said)]
        out["horns"] = "Horns, two trombones in harmony: " + _merge(items, name_at, bars) + "."
    if take.get("drums"):
        items = [(p["section"].start, p["section"].end,
                  re.sub(r"^programmed; ", "", p["drums"][0].split("drums: ", 1)[1]).split("; ")[0])
                 for p in plan if p.get("drums")]
        grooves = _merge(items, name_at, bars)
        moments = _events([ln for p in plan for ln in p.get("drums", [])[1:]], bars)
        out["drums"] = f"Drums: {grooves}" + (f"; then {moments}" if moments else "") + "."
    if take.get("percussion"):
        kit = {}                                # each drum on its own, its patterns merged
        for p in plan:
            for w in re.sub(r" \([^)]*\)", "", p["percussion"][0].split("percussion: ", 1)[1]).split("; ") \
                    if p.get("percussion") else []:
                who, what = w.split(": ", 1)
                kit.setdefault(who, []).append((p["section"].start, p["section"].end, what))
        moments = _events([ln for p in plan for ln in p.get("percussion", [])[1:]], bars)
        out["percussion"] = ("Percussion: " + "; ".join(f"{who}, {_merge(its, name_at, bars).replace('; ', ', ')}"
                                                        for who, its in kit.items())
                             + (f"; then {moments}" if moments else "") + ".")
    if part(style, "members", "pad").get("plays", True):
        out["pad"] = "Pad: holds each chord, its voices moving the shortest way, under the melody."
    if take.get("arp"):
        items = [(p["section"].start, p["section"].end, p["arp"].replace(" (kept)", "")) for p in plan]
        out["arp"] = "Arp: " + _merge(items, name_at, bars) + "."
    # the melody, its lead's touches and the second lead
    if LOOPS[style]:
        items = [(p["section"].start, p["section"].end, p["loop"].replace(" (kept)", "").split(", ")[0]) for p in plan]
        mel = (f"Melody: {_merge(items, name_at, bars)}; each round fitted to its chord, a phrase's last round "
               "landing home")
    else:
        count = len([ph for p in plan for ph in p["phrases"]][:max(1, bars // n)])
        mel = (f"Melody: {count} phrase{'s' * (count > 1)} of {n} bars, each a question and its answer: the motif, a "
               "peak about two-thirds in, the half left open, home on the cadence")
    if take.get("bends") or take.get("vibrato"):
        mel += f"; on the pentatonic, {len(take['bends'])} notes bending up, {len(take['vibrato'])} with vibrato"
    if take.get("lead2"):                       # power rock's second lead
        items = [(at, at + n, {"twin": "twin harmony a third under", "duel": "the duel, trading licks"}[x.lead])
                 for at, _, x in take.get("parts", []) if x.lead in ("twin", "duel")]
        mel += f"; a second lead on the other side: {_merge(items, name_at, bars)}"
    out["melody"] = mel + "."
    if take.get("layers"):                      # who plays when (task 3.6)
        ls = take["layers"]
        full = sum(1 for x in ls if len(x.playing) == len(LAYERS[style].join) and x.melody)
        swaps = sum(1 for x in ls for w in x.said if w.startswith("rotation"))
        moves = sum(1 for x in ls for w in x.said if w.startswith("the "))
        opens = next((w.split(": ", 1)[1] for w in ls[0].said if w.startswith("opens")), None)
        downs = [w.split(": ", 1)[1] for x in ls for w in x.said if w.startswith("breakdown")]
        out["band"] = (f"Band: the whole band in {full} of {len(ls)} phrases"
                       + (f"; opens with {opens}" if opens else "")
                       + (f"; {moves} phrase{'s' * (moves != 1)} where members join or rest" if moves else "")
                       + (f", {swaps} rotation{'s' * (swaps != 1)}" if swaps else "")
                       + (f"; the breakdown: {downs[0]}" if downs else "") + ".")
    out["listen"] = _listen(style, bars, take)
    return out


def summary(style, seed, bars, bpm, take, met=METERS["4/4"]):
    """The clip in a few plain lines (task 3.7): style, bars, key, tempo; the form; the chords as loops and how they
    vary; each member once, where it changes; the melody's phrase; the band; what to listen for."""
    return list(_said(style, seed, bars, bpm, take, met).values())


MEMBER = {"bass": "does it lock with the kick and lead into each chord",
          "drums": "does the groove feel like the style, its fills leading into the next phrase",
          "percussion": "does each drum sit with the clave and with the others",
          "pad": "do the chords move smoothly, never in the melody's way",
          "melody": "does each phrase ask and answer, and come home",
          "guitar": "are the chords tight and in time, the palm mutes clear",
          "keys": "does the montuno lock with the clave and push each chord in early",
          "horns": "do the two trombones sound together, in tune and on the clave",
          "arp": "does it sparkle over each chord without crowding the lead"}


def member_summary(style, seed, bars, bpm, take, member, met=METERS["4/4"]):
    """A member's clip on its own (Checkpoint 3's solo clips; DadCraft, Oct 27: 2-3 lines): what it plays in the
    style, and what to listen for."""
    said = _said(style, seed, bars, bpm, take, met)
    return [said["head"] + f", {member} alone", said[member],
            f"Listen for: {MEMBER[member]}; does it sound like {style.replace('_', ' ')}'s {member}."]


def _listen(style, bars, take):
    plan = take["plan"]
    if BASS[style].kick:                        # trap's own questions (DadCraft's, after the first round)
        return ("Listen for: does the 808 feel like the bass and the kick at once, and do its slides come through; "
                   "do the hats roll rather than tick, the clap staying put on 3; does the bell's riff go round like "
                   "trap's, its triplets over the grid; do the hats-alone opening and the drop before a section "
                   "keep it from feeling stuck"
                   + ("; do the strings and riff hold the quiet starts, the drums then the 808 coming in as it rises; "
                      "does the breakdown (the beat cut, the riff and strings playing on) make the drop hit; do the "
                      "rotations and slow changes keep the loop fresh" if take.get("layers") else "") + ".")
    if ARPS[style]:                             # synthwave's own questions (task 3.4b)
        return ("Listen for: does it feel like outrun when the energy is up (the bass driving in 8ths, the snare "
                   "big on 2 and 4, the arp sparkling in 16ths) and turn dreamy when it's low (a held bass, the drums "
                   "at half time, the arp in 8ths); does the lead stay on top and sing; do the pad and bass breathe "
                   "with the kick without pumping like EDM; do the tom fills lead into the next section"
                   + ("; does the band thin and fill with the energy, the parts coming and going without jolts; does "
                      "the breakdown (arp and pad alone) set up what follows; do the slow changes keep the loops "
                      "fresh without sounding like mistakes" if take.get("layers") else "") + ".")
    if GUITAR[style]:                           # power rock's own questions (task 3.4d)
        names = {x.name for _, _, x in take["parts"]}
        double = any("double bass" in ln for p in plan for ln in p.get("drums", []))
        leads = {x.lead for _, _, x in take["parts"]}
        return ("Listen for: does it sound like 80s hair metal and shred"
                   + ("; does the double bass drive the loud parts" if double else "")
                   + ("; do the two leads duel, trading licks left and right, the turns getting shorter and hotter, "
                      "and land home together" if "duel" in leads else "")
                   + ("; do they sing the chorus's hook in twin harmony" if "twin" in leads else "")
                   + "; are the rhythm guitars still wide and tight, palm-muted in the verse"
                   + ("; does the pre-chorus build into it, the snare doubling up" if take.get("builds") else "")
                   + ("; does the stop hit together and ring" if take["breaks"] else "")
                   + "; do the bends land in tune.")
    if take.get("parts"):                       # salsa's own questions (task 3.4c)
        names = {x.name for _, _, x in take["parts"]}
        walks = [_bar_of(ln) for p in plan for ln in p["lines"] if "walks up" in ln and _bar_of(ln) < bars]
        return ("Listen for: does the piano's montuno lock with the clave and push each chord in early; do the "
                   "trombones sound like a Fania horn section ("
                   + ", ".join(w for k, w in (("cuerpo", "punching the ends of the lead's phrases"),
                                              ("montuno", "the coro answering the lead"),
                                              ("mambo", "the mambo's riff")) if k in names) + ")"
                   + ("; does the song move from its body into the montuno" if {"cuerpo", "montuno"} <= names else "")
                   + ("; does the break hit together" if take["breaks"] else "")
                   + ("; does the bass walk up into the next section" if walks else "")
                   + "; does it all still feel like salsa.")
    return ("Listen for: does it flow, chords going round and coming home rather than wandering; does the bass "
               "feel like the style; does each phrase sound like a question and its answer"
               + ("; does the drummer feel like the style, its fills leading into the next phrase"
                  if take.get("drums") else "")
               + ("; does the percussion sit with the clave and lift in the loud sections"
                  if take.get("percussion") else "")
               + ("; does the 808 feel like the bass and the kick at once, and do its slides land as a gesture, not a "
                  "habit; does the snare stay put on 3 while the hats turn to triplets and 32nds; do the lead's "
                  "triplets sit over the grid; does the harmony staying put feel like trap rather than stuck"
                  if BASS[style].kick else "") + ".")

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("style", nargs="?", default="plain", choices=sorted(FORM))
    p.add_argument("--seed", type=int, default=None, help="a fresh one when left out")
    p.add_argument("--bars", type=int, default=8)
    p.add_argument("--no-flow", dest="flow", action="store_false", help="Checkpoint 2's bar-by-bar draws")
    a = p.parse_args(argv)
    print("\n".join(passage(a.style, fresh_seed() if a.seed is None else a.seed, a.bars, flow=a.flow)))


if __name__ == "__main__":
    main()
