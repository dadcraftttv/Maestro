"""Frozen S.0 event codec, v1: 4/4 at 24 ticks per beat.

Encode/decode behavior preserved from the private corpus audit.
See docs/s1-tokens.md for field vocabulary and decoder limitations.
"""

TONIC = {'Cb':11,'Gb':6,'Db':1,'Ab':8,'Eb':3,'Bb':10,'F':5,'C':0,'G':7,'D':2,'A':9,'E':4,'B':11,'F#':6,'C#':1,
         'Abm':8,'Ebm':3,'Bbm':10,'Fm':5,'Cm':0,'Gm':7,'Dm':2,'Am':9,'Em':4,'Bm':11,'F#m':6,'C#m':1,'G#m':8,'D#m':3,'A#m':10}


def encode(notes, lo, hi, tonic, chord_labels=None):
    tokens = []
    for bar in range(lo, hi):
        tokens.append(['BAR', bar])
        if chord_labels is not None:
            tokens.append(['CHORDS', *[(c['root'],c['quality']) for c in chord_labels[bar*4:bar*4+4]]])
        pos = 0
        start = bar * 96
        for a,b,p,v in notes:
            if b <= start or a >= start+96:
                continue
            x,y = max(a,start)-start, min(b,start+96)-start
            if x > pos:
                tokens.append(['REST',pos,x-pos])
            assert x >= pos and y > x
            tokens.append(['NOTE',x,p-tonic,y-x,v,int(a<start),int(b>start+96)])
            pos = y
        if pos < 96:
            tokens.append(['REST',pos,96-pos])
    tokens.append(['END'])
    return tokens


def decode(tokens, tonic):
    out = []
    bar = None
    pos = 96
    first = None
    pending = False
    ended = False
    for token in tokens:
        kind,*v = token
        if kind == 'BAR':
            assert pos == 96
            assert bar is None or v[0] == bar+1
            bar = v[0]
            if first is None:
                first = bar
            pos = 0
        elif kind == 'CHORDS':
            assert pos == 0 and len(v) == 4
        elif kind == 'REST':
            assert not pending and v[0] == pos and v[1] > 0
            pos += v[1]
        elif kind == 'NOTE':
            x,relative,duration,velocity,tie_in,tie_out = v
            assert x == pos and duration > 0 and 0 <= velocity <= 7
            a,b,pitch = bar*96+x,bar*96+x+duration,relative+tonic
            if pending:
                assert tie_in and out[-1][1:] == [a,pitch,velocity]
                out[-1][1] = b
            else:
                assert not tie_in or (bar == first and pos == 0)
                out.append([a,b,pitch,velocity])
            pending = bool(tie_out)
            pos += duration
        elif kind == 'END':
            assert pos == 96
            ended = True
        else:
            raise ValueError(kind)
        assert pos <= 96
    assert ended
    return out


def clipped(notes, lo, hi):
    # Independent target from source notes; no token fields or decoder reuse.
    return [[max(a,lo*96),min(b,hi*96),p,v] for a,b,p,v in notes if a<hi*96 and b>lo*96]


CHORD_QUALITIES = ('aug', 'dim', 'dom7', 'half_dim7', 'maj7', 'major',
                   'min7', 'minor', 'sus2', 'sus4')


def condition(notes, chords, key, bar, run_start, register, density):
    """Build next-bar controls without reading the target melody.

    ``register`` is an inclusive MIDI range, ``density`` a desired onset count
    (0..96). Callers supply these controls, never infer them from the target.
    History stops at the eligible run boundary and contains at most eight bars.
    Phrase position is a mechanical eight-bar cycle from that boundary.
    """
    if key is not None and key not in TONIC:
        raise ValueError('unknown key')
    if not (isinstance(bar, int) and isinstance(run_start, int)
            and 0 <= run_start <= bar):
        raise ValueError('invalid bar/run boundary')
    low, high = register
    if not (isinstance(low, int) and isinstance(high, int) and 0 <= low <= high <= 127):
        raise ValueError('invalid register')
    if not isinstance(density, int) or not 0 <= density <= 96:
        raise ValueError('invalid density')
    upcoming = chords[bar * 4:bar * 4 + 4]
    if len(upcoming) != 4 or any(c is None for c in upcoming):
        raise ValueError('four known upcoming beat chords required')
    if any(not isinstance(c['root'], int) or not 0 <= c['root'] <= 11
           or c['quality'] not in CHORD_QUALITIES for c in upcoming):
        raise ValueError('unsupported chord')
    lo = max(run_start, bar - 8)
    return {
        'upcoming_chords': [(c['root'], c['quality']) for c in upcoming],
        'key': key,
        'register': (low, high),
        'density': density,
        'bar_in_phrase': (bar - run_start) % 8,
        'history_bars': bar - lo,
        'previous': encode(notes, lo, bar, TONIC.get(key, 0)),
    }
