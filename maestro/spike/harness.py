# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded next-bar sampling with grammar masks and unchanged Maestro judge."""
from collections import Counter
from dataclasses import replace
import math
import random
import time

from maestro import judge
from maestro.song import Note
from .tokens import TONIC, decode


def legal(event, pos, control):
    """One-bar grammar: boundary ties are explicit; interior ties forbidden.

    Prior sustain, when present, fixes the continuation pitch/velocity. A tie-out
    can only occur at the bar boundary. Decoder alone does not enforce these.
    """
    if not isinstance(event, (tuple, list)) or len(event) not in (3, 7):
        return False
    if any(type(v) is not int for v in event[1:]):
        return False
    kind, x, *rest = event
    if x != pos or not 0 <= pos < 96:
        return False
    previous = [t for t in control['previous'] if t[0] in ('NOTE', 'REST')]
    prior = previous[-1] if previous else None
    pending = prior is not None and prior[0] == 'NOTE' and prior[6] == 1
    if kind == 'REST' and len(event) == 3:
        return not (pos == 0 and pending) and 1 <= rest[0] <= 96-pos
    if kind != 'NOTE' or len(event) != 7:
        return False
    pitch, duration, velocity, tie_in, tie_out = rest
    low, high = control['register']
    tonic = TONIC.get(control['key'], 0)
    if not (low <= pitch+tonic <= high and 1 <= duration <= 96-pos
            and 0 <= velocity <= 7 and tie_in in (0, 1) and tie_out in (0, 1)):
        return False
    if tie_out and pos + duration != 96:
        return False
    if tie_in != int(pos == 0 and pending):
        return False
    return not tie_in or (pitch, velocity) == (prior[2], prior[4])


def draw(weights, rng):
    items = [(tuple(e), float(w)) for e, w in weights.items() if w > 0]
    if any(not math.isfinite(w) for _, w in items):
        raise ValueError('nonfinite generator weight')
    if not items:
        raise ValueError('empty support')
    return rng.choices([e for e, _ in items], weights=[w for _, w in items], k=1)[0]


def propose(generator, control, bar, rng, masked=True, telemetry=None):
    """Generator protocol: distribution(control, prefix, position) -> weights.

    Returns decoded notes and mask counters. At most 96 event calls. Raw mode
    stops at the first invalid choice, with no correction or musical acceptance.
    """
    prefix, pos, choices, masked_mass = [], 0, 0, 0.0
    while pos < 96:
        weights = generator.distribution(control, prefix, pos)
        valid = {e: w for e, w in weights.items() if legal(e, pos, control)}
        total = sum(weights.values())
        if total <= 0 or any(not math.isfinite(w) or w < 0 for w in weights.values()):
            raise ValueError('invalid generator weights')
        removed = 1 - sum(valid.values()) / total
        masked_mass += removed
        if telemetry is not None:
            telemetry["choices"] += 1
            telemetry["masked_mass_sum"] += removed
        raw = draw(weights, rng)
        if not legal(raw, pos, control):
            choices += 1
            if telemetry is not None:
                telemetry["masked_choices"] += 1
            if not masked:
                raise ValueError('raw grammar')
            raw = draw(valid, rng)
        prefix.append(raw)
        pos += raw[3] if raw[0] == 'NOTE' else raw[2]
    stream = [['BAR', bar], *[list(e) for e in prefix], ['END']]
    return decode(stream, TONIC.get(control['key'], 0)), {
        'masked_choices': choices, 'masked_mass_sum': masked_mass, 'choices': len(prefix)}


def judge_bar(clip, member, bar, notes):
    """Replace target melody in caller's context and run full-context plus target-bar card checks.

    clip is a judge.Clip; notes use absolute 24-tick/beat coordinates. The caller
    supplies accompaniment, style, timeline and prior bars. No thresholds change.
    """
    if clip.bar_steps != 96 or not 0 <= bar < clip.bars:
        raise ValueError('4/4 clip and in-range target bar required')
    player = clip.players[member]
    if player.role != 'melody':
        raise ValueError('target must be melody')
    lo, hi = bar*96, (bar+1)*96
    kept = []
    for n in player.notes:
        if n.step < lo:
            kept.append(replace(n, steps=min(n.steps, lo-n.step)))
        elif n.step >= hi:
            kept.append(n)
    # Coarse bin 0 represents MIDI 1..15; midpoint avoids illegal zero velocity.
    candidate = kept + [Note(a, b-a, p, min(127, v*16+8)) for a,b,p,v in notes]
    updated = replace(clip, players={**clip.players, member: replace(player, notes=sorted(candidate, key=lambda n:n.step))})
    rows = judge.score(updated)
    reasons = [] if judge.passes(rows) else [r.says() for r in rows if not r.ok]
    # Preserve absolute time and the complete accompaniment/chord context. Only
    # the target member's card measurements use this bar's sounding notes.
    local = [n for n in updated.players[member].notes
             if n.step < hi and n.step + n.steps > lo]
    local = [replace(n, step=max(n.step, lo),
                     steps=min(n.step+n.steps, hi)-max(n.step, lo)) for n in local]
    # A bar of rest is allowed (DadCraft, Oct 29): only the full judge sees it.
    if not local:
        return reasons
    card = judge.BOOK[clip.style_of(member)]['judge'][player.role]
    local_rows = judge._card_rows(card, local, updated, member, '', 0)
    if not local_rows or not judge.passes(local_rows):
        reasons += ['target bar: ' + r.says() for r in local_rows if not r.ok]
        if not local_rows:
            reasons.append('target bar: no measurable card traits')
    return reasons


def next_bar(generator, control, bar, rng, check, fallback, attempts=3, synchronize=None):
    """Build ahead of playback. check(notes)->reasons is required for every bar.

    fallback()->notes must return the rules' melody for this exact context.
    Invalid fallback raises rather than emitting a bar that failed Maestro checks.
    A GPU generator supplies its synchronization hook for honest wall times.
    """
    if type(attempts) is not int or not 1 <= attempts <= 16:
        raise ValueError('attempts must be 1..16')
    sync = synchronize or (lambda: None)
    sync()
    start = time.perf_counter()
    log = {'attempts': 0, 'retries': 0, 'accepted': False, 'fallback': False,
           'masked_choices': 0, 'masked_mass_sum': 0.0, 'choices': 0,
           'raw_valid': False, 'raw_reason': [], 'rejections': []}
    # Separate raw rollout on a cloned RNG, so auditing does not alter sampling.
    audit_rng = random.Random()
    audit_rng.setstate(rng.getstate())
    try:
        raw, _ = propose(generator, control, bar, audit_rng, masked=False)
        log['raw_reason'] = list(check(raw))
        log['raw_valid'] = not log['raw_reason']
    except (ValueError, AssertionError) as exc:
        log['raw_reason'] = [str(exc)]
    for i in range(attempts):
        log['attempts'] += 1
        log['retries'] = i
        try:
            notes, _ = propose(generator, control, bar, rng, telemetry=log)
            reasons = list(check(notes))
        except (ValueError, AssertionError) as exc:
            reasons = [str(exc)]
        if not reasons:
            log['accepted'] = True
            break
        log['rejections'].append(reasons)
    else:
        notes = fallback()
        reasons = list(check(notes))
        if reasons:
            raise ValueError(f'rule fallback failed checks: {reasons}')
        log['fallback'] = True
    sync()
    log['milliseconds'] = (time.perf_counter()-start)*1000
    return notes, log


def summarize(logs):
    if not logs:
        raise ValueError('no bars')
    times = sorted(x['milliseconds'] for x in logs)
    reasons = Counter(r for x in logs for rs in x['rejections'] for r in rs)
    return {'bars': len(logs), 'raw_valid': sum(x['raw_valid'] for x in logs),
            'first_try': sum(x['accepted'] and x['attempts']==1 for x in logs),
            'accepted': sum(x['accepted'] for x in logs),
            'fallbacks': sum(x['fallback'] for x in logs),
            'retries': sum(x['retries'] for x in logs),
            'masked_choices': sum(x['masked_choices'] for x in logs),
            'choices': sum(x['choices'] for x in logs),
            'rejection_reasons': dict(reasons),
            'p50_ms': times[math.ceil(len(times)*.5)-1],
            'p99_ms': times[math.ceil(len(times)*.99)-1]}
