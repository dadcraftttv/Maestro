# SPDX-License-Identifier: GPL-3.0-or-later
"""Today's composer in Python: Ouralia's `dcs_composer` (dcs/src/dcs_composer.c), choice for choice.

Maestro grows from it (decision 1). Given the same seed and the same messages it sends exactly what the C sends:
the parity test (tests/parity) runs both and compares every output. Its tables come from `data/composer.json`
(kept in step by tools/sync_check.py); its logic follows the C line by line, so the C comments explain it. Float
maths is rounded to 32 bits at each step, as the C does it.

Messages are methods (scale, tempo, bright, energy, bar, start, again, seed, color, renew, note, drums, arp, cell);
`tick()` lets Pd's time pass (the composer's own bar clock fires when no bar comes). Everything the composer sends
lands in `out` as (outlet, values): "chord" [anchor, bass, 4 pad notes], "sect" [kind, register], "mel" note,
"form" [form, first note], "drum" [lane, 16 velocities], "arp" [8 steps], "cell" [16 lengths, count, last onset].

Ported from dcs_composer.c: Copyright (c) 2026 dadcraft (DadCraft Studios), BSD-3-Clause.
"""
import json, os, struct, time

from .rng import ComposerRng

with open(os.path.join(os.path.dirname(__file__), "data", "composer.json")) as _f:
    _C = json.load(_f)


def f32(v):
    """A C float: v rounded to 32 bits."""
    return struct.unpack("<f", struct.pack("<f", v))[0]


def _f32s(v):
    return [_f32s(x) for x in v] if isinstance(v, list) else f32(v)


_D, _E, _T = _C["defines"], _C["enums"], _C["tables"]
NSCALES, PLEN, MOTIF_MAX, GAP_MS, ROAM, ARP_LEN = (_D[k] for k in ("NSCALES", "PLEN", "MOTIF_MAX", "GAP_MS", "ROAM", "ARP_LEN"))
PIECE_BARS = _D["PIECE_BARS"]
HOME, LIFT, CALM, TURN, NKINDS = (_E[k] for k in ("HOME", "LIFT", "CALM", "TURN", "NKINDS"))
WHOLE = _E["WHOLE"]
F_MOTIF, F_AGAIN, F_ANSWER, F_MOVED, F_INVERT, F_BACK, F_SHORT, F_LONGER = range(8)
SCALE_N, SCALE_IV, PARENT, MODES = _T["SCALE_N"], _T["SCALE_IV"], _T["PARENT"], _T["MODES"]
KIND_BLINE_HOLD = _T["KIND_BLINE_HOLD"]
KIND_SECS, KIND_DRIVE = _f32s(_T["KIND_SECS"]), _f32s(_T["KIND_DRIVE"])
KIND_REG, KIND_BASS, KIND_OPEN, KIND_COLOR = _T["KIND_REG"], _T["KIND_BASS"], _T["KIND_OPEN"], _T["KIND_COLOR"]
GHOST, CELL_K_STRAIGHT, CELL_K_DOTTED = _T["ghost"], _T["K_5"], _T["K_3"]

# Pd's clock (m_sched.c): time in units of 1/14112 ms; a DSP tick is one block
TIMEUNITPERMSEC = 32.0 * 441.0
TIMEUNITPERSECOND = TIMEUNITPERMSEC * 1000.0

# C floats used in comparisons and outputs
_V = {k: f32(v) for k, v in dict(k1=1.0, k8=0.85, kk=0.65, kl=0.8, km=0.6, sn=0.9, sq=0.6, gh=0.3, h4=0.6, h2=0.45,
                                 h1=0.28, ho=2.45, c15=0.15, c3=0.3, c2=0.2, c5=0.5, c4=0.4, c7=0.7).items()}


def _cdiv(a, b):
    """C's integer division (toward zero)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def euclid(i, k, rot, steps):
    """Is step i one of k hits spread evenly over the steps."""
    return int(k > 0 and (((i + rot) % steps) * k) % steps < k)


def tone_step(t, n):
    """The t-th chord tone up (0 root, 1 third, 2 fifth, 3 the root an octave up..)."""
    return (t % 3) * 2 + (t // 3) * n


def chord_tone(target, chord, n, root_only):
    """The chord tone (chord, +2, +4 steps, any octave) nearest a step."""
    best, bd = target, 1 << 20
    for o in range(-4, 7):
        for k in range(1 if root_only else 3):
            d = chord + 2 * k + o * n
            if abs(d - target) < bd:
                bd, best = abs(d - target), d
    return best


def pc(m, d):
    """Semitones of a degree, over octaves."""
    return m["iv"][d % m["n"]] + 12 * (d // m["n"])


class Composer:
    """One dcs_composer object. `seed=None` seeds from the clock like the C (a different piece every time)."""

    _made = 0

    def __init__(self, seed=None, sr=48000, blocksize=64):
        Composer._made += 1
        self.out = []
        self.systime = 0.0
        self.tick_units = (blocksize / sr) * TIMEUNITPERSECOND
        self.watch_at = None                     # the bar clock's set time (None: unset)
        self.r = ComposerRng((int(time.time()) * 2654435761 + Composer._made) if seed is None else 0)
        self.scale, self.started = 0, 0
        self.bpm, self.bright, self.energy = f32(100), f32(0.5), f32(0.5)
        self.have, self.kept = [0] * NKINDS, [[0] * PLEN for _ in range(NKINDS)]
        self.kind, self.last_away, self.phrases_left = HOME, CALM, 0
        self.prog, self.pos, self.bars_left = [0] * PLEN, 0, 0
        self.deg, self.voice, self.voiced, self.bass = 0, [0] * 4, 0, 0
        self.motif = [[] for _ in range(NKINDS)]  # each a list of steps from the first note
        self.stmt = []
        self.have_motif = [0] * NKINDS
        self.mel_kind, self.stmt_k, self.stmt_pos, self.stmt_base, self.stmt_on, self.drift = -1, 0, 0, 0, 0, 0
        self.last_note = 0.0
        self.drum_base = [[[0.0] * 16 for _ in range(3)] for _ in range(NKINDS)]
        self.drum_cur = [[0.0] * 16 for _ in range(3)]
        self.drum_d, self.drum_have, self.drum_kind, self.drum_bars = [0.0] * NKINDS, [0] * NKINDS, -1, 0
        self.arp_base, self.arp_cur = [[0] * ARP_LEN for _ in range(NKINDS)], [0] * ARP_LEN
        self.arp_have, self.arp_kind, self.arp_bars, self.arp_n, self.arp_pace = [0] * NKINDS, -1, 0, 0, [0.0] * NKINDS
        self.cell_base, self.cell_cur = [[0] * 16 for _ in range(NKINDS)], [0] * 16
        self.cell_have, self.cell_style, self.cell_kind, self.cell_bars = [0] * NKINDS, [0] * NKINDS, -1, 0
        self.cell_d = [0.0] * NKINDS
        self.bline_base = [[[0] * 3 for _ in range(16)] for _ in range(NKINDS)]
        self.bline_cur = [[0] * 3 for _ in range(16)]
        self.bline_have, self.bline_kind, self.bline_bars = [0] * NKINDS, -1, 0
        self.color, self.sus_voice, self.sus_third = 0, -1, 0
        # new pieces: bars until the next, the open ending under way, and the handover's phrases (0: none)
        self.renew, self.piece_bars, self.leadin, self.handover = 0, PIECE_BARS, 0, 0
        self._make_phrase(HOME, self.prog)       # (quietly: nothing is sent while the patch loads)
        self.have[HOME] = 1
        self.kept[HOME] = self.prog[:]
        self.phrases_left, self.deg, self.bars_left = 2, 0, 1
        if seed is not None:   # as if `seed <n>` came straight after loading (its section start not sent)
            self.seed(seed)
            self.out.clear()

    def rnd(self, n):
        return self.r.rnd(n)

    def mode(self):
        return MODES[PARENT[self.scale]]

    # ---- time ----

    def _clock_delay(self, ms):
        self.watch_at = self.systime + TIMEUNITPERMSEC * ms

    def tick(self, blocks=1):
        """Let `blocks` DSP ticks pass, like Pd's sched_tick: the bar clock fires when it falls due."""
        for _ in range(blocks):
            nxt = self.systime + self.tick_units
            while self.watch_at is not None and self.watch_at < nxt:
                self.systime, self.watch_at = self.watch_at, None
                self._watch()
            self.systime = nxt

    def _watch(self):   # no bar came: keep time from the tempo
        self.bar()
        self._clock_delay(self._bar_ms())

    def _bar_ms(self):
        return int(f32(f32(240000.0) / (self.bpm if self.bpm > 30 else f32(100))))

    # ---- the chords and the form ----

    def _pick_of(self, lst, avoid):
        c = []
        for v in lst[:3]:   # (-1 ends the list)
            if v < 0:
                break
            if v != avoid:
                c.append(v)
        return c[self.rnd(len(c))] if c else lst[0]

    def _step(self, frm, to, avoid):
        m = self.mode()
        w = [0] * 7
        total = 0
        for d in range(m["n"]):
            w[d] = m["w"][frm][d] * (m["w"][d][to] + 1 if to >= 0 else 1) if (m["ok"][d] and d != frm and d != avoid) else 0
            if to >= 0 and d == to:
                w[d] = 0
            total += w[d]
        if total == 0:   # nothing leads there: any other chord
            for d in range(m["n"]):
                w[d] = 1 if (m["ok"][d] and d != frm and d != to) else 0
                total += w[d]
            if total == 0:
                return frm
        r = self.rnd(total)
        for d in range(m["n"]):
            r -= w[d]
            if r < 0:
                return d
        return frm

    def _other_chord(self, avoid):
        m = self.mode()
        c = [d for d in range(m["n"]) if m["ok"][d] and d != avoid]
        return c[self.rnd(len(c))] if c else 0

    def _make_phrase(self, kind, p):
        m = self.mode()
        if kind == LIFT:
            first = self._pick_of(m["lift"], -1)
            last = self._pick_of(m["open"], first)
        elif kind == CALM:
            first = self._pick_of(m["calm"], -1)
            last = 0 if self.rnd(10) < 6 else first
        elif kind == TURN:
            first = self._other_chord(0)
            last = 0 if self.rnd(2) else self._pick_of(m["calm"], first)
        else:
            first = last = 0
        p[0] = first
        p[1] = self._step(first, -1, -1)
        p[2] = self._step(p[1], last, -1)
        p[3] = last

    def _vary_phrase(self, kind, p):
        i = 1 + self.rnd(PLEN - 2)
        p[i] = self._step(p[i - 1], p[i + 1], -1)
        if kind == LIFT and self.rnd(4) == 0:
            p[PLEN - 1] = self._pick_of(self.mode()["open"], p[PLEN - 2])

    def _begin_section(self, kind):
        self.kind = kind
        self.phrases_left = 2 + int(kind != HOME and self.rnd(3) == 0)
        if self.have[kind]:   # it comes back, a little changed
            self.prog = self.kept[kind][:]
            self._vary_phrase(kind, self.prog)
        else:
            self._make_phrase(kind, self.prog)
            self.have[kind] = 1
        self.kept[kind] = self.prog[:]
        self.pos = 0
        self.out.append(("sect", [kind, KIND_REG[kind]]))

    def _next_kind(self):
        if self.kind != HOME and self.rnd(10) < (5 if self.renew else 7):
            return HOME
        w = [0.0, f32(f32(1.0 + self.energy) + f32(0.5 * self.bright)), f32(1.0 + f32(1 - self.energy)), _V["c7"]]
        w[self.kind] = 0.0
        if self.last_away != self.kind:
            w[self.last_away] = f32(w[self.last_away] * _V["c4"])
        total = f32(f32(w[1] + w[2]) + w[3])
        r = f32(f32(total * self.rnd(1000)) / 1000.0)
        for k in range(1, NKINDS):
            r = f32(r - w[k])
            if r < 0:
                return k
        return TURN

    def _chord_bars(self):
        b = int(f32(f32(f32(KIND_SECS[self.kind] * 1000) / self._bar_ms()) + 0.5))
        b = max(1, min(4, b))
        if self.pos == PLEN - 1 and self.rnd(100) < 35:
            b += 1   # a cadence held a little longer
        return b

    def _voice_chord(self):
        m = self.mode()
        t = [pc(m, self.deg) % 12, pc(m, self.deg + 2) % 12, pc(m, self.deg + 4) % 12]
        best, bestcost = [0, 0, 0], 1 << 30
        for inv in range(3):
            for base in range(-5, 9):
                if (base + 120) % 12 != t[inv]:
                    continue
                v = [base, 0, 0]
                v[1] = base + (t[(inv + 1) % 3] - t[inv] + 12) % 12
                v[2] = v[1] + (t[(inv + 2) % 3] - t[(inv + 1) % 3] + 12) % 12
                if KIND_OPEN[self.kind]:   # drop the middle note an octave higher
                    v[1], v[2] = v[2], v[1] + 12
                cost = (-2 - base if base < -2 else base - 5 if base > 5 else 0) * 3 + (v[2] - 19 if v[2] > 19 else 0) * 3
                if self.voiced:
                    cost += sum(abs(v[i] - self.voice[i]) for i in range(3))
                else:
                    cost += inv * 4
                if cost < bestcost:
                    bestcost, best = cost, v[:]
        self.voice[:3] = best
        root = next((b for b in best if (b + 120) % 12 == t[0]), best[0])
        self.voice[3] = root + 12
        self.voiced = 1
        self.bass = t[0] if self.rnd(100) < KIND_BASS[self.kind] else 0
        self.sus_voice = -1
        if self.color and PARENT[self.scale] != WHOLE:
            c = KIND_COLOR[self.kind]
            r = self.rnd(100)
            if r < c[0]:                                   # its seventh, a little below the doubled root
                self.voice[3] = root + (pc(m, self.deg + 6) - pc(m, self.deg) + 24) % 12
            elif r < c[0] + c[1]:                          # an added ninth
                self.voice[3] = root + 12 + (pc(m, self.deg + 1) - pc(m, self.deg) + 24) % 12
            elif r < c[0] + c[1] + c[2]:                   # sus4 or sus2, resolving at the next bar
                four = (pc(m, self.deg + 3) - pc(m, self.deg) + 24) % 12
                two = (pc(m, self.deg + 1) - pc(m, self.deg) + 24) % 12
                up = 1 if four == 5 and (two != 2 or self.rnd(3)) else -1 if two == 2 else 0
                for i in range(3 if up else 0):
                    if (self.voice[i] + 120) % 12 == t[1]:
                        self.sus_voice, self.sus_third = i, self.voice[i]
                        third = (t[1] - t[0] + 12) % 12
                        self.voice[i] += four - third if up > 0 else two - third
                        break

    def _anchor(self):
        m = self.mode()
        n = SCALE_N[self.scale]
        if n == m["n"] and SCALE_IV[self.scale][:n] == m["iv"][:n]:   # the chords' own scale: the degree itself
            return self.deg
        t = [pc(m, self.deg) % 12, pc(m, self.deg + 2) % 12, pc(m, self.deg + 4) % 12]
        best, bestscore = 0, -1
        for s in range(n):
            score = sum(SCALE_IV[self.scale][(s + 2 * k) % n] == t[j] for k in range(3) for j in range(3))
            score += (SCALE_IV[self.scale][s] == t[0]) * 3
            if score > bestscore:
                bestscore, best = score, s
        return best

    def _emit(self):
        self.out.append(("chord", [self._anchor(), self.bass] + self.voice[:]))

    def _play_pos(self, fresh):
        same = self.voiced and self.prog[self.pos] == self.deg
        self.deg = self.prog[self.pos]
        self.bars_left = self._chord_bars()
        if same and not fresh:
            return   # the same chord again: it is simply held
        self._voice_chord()
        self._emit()

    def _lead_in(self):   # the last phrase of a piece: its ending open, so the new piece answers it
        self.leadin = 1
        self.prog[PLEN - 1] = self._pick_of(self.mode()["open"], self.prog[PLEN - 2])

    def _advance(self):
        self.pos += 1
        if self.pos >= PLEN:
            if self.handover:
                self.handover += 1
            if self.handover == 2:     # a phrase into the new piece: a new groove
                for k in range(NKINDS):
                    self.drum_have[k] = self.arp_have[k] = self.cell_have[k] = self.bline_have[k] = 0
                self.drum_kind = self.arp_kind = self.cell_kind = self.bline_kind = -1
            elif self.handover == 3:   # and a phrase later, new motifs
                for k in range(NKINDS):
                    self.have_motif[k] = 0
                self.mel_kind = -1
                self.handover = 0
            if self.leadin:
                self._handover()
            else:
                self.phrases_left -= 1
                if self.phrases_left > 0:   # the phrase again: often the same, sometimes changed
                    self.pos = 0
                    if self.rnd(2):
                        self._vary_phrase(self.kind, self.prog)
                else:
                    k = self._next_kind()
                    if self.kind != HOME:
                        self.last_away = self.kind
                    self._begin_section(k)
            if self.renew and not self.leadin and not self.handover and self.piece_bars <= 0 and self.phrases_left == 1:
                self._lead_in()
        self._play_pos(0)

    # ---- the melody ----

    def _make_motif(self):
        m = [0] * (3 + self.rnd(4))
        d, run = (1 if self.rnd(2) else -1), 0
        for i in range(1, len(m)):
            r = self.rnd(11)
            size = 1 if r < 6 else 2 if r < 9 else 0 if r < 10 else 3   # steps, some skips, a repeat, a leap
            if self.rnd(100) < 35 or run >= 2:
                d, run = -d, 0
            v = m[i - 1] + d * size
            if v > 4 or v < -4:   # keep it within a narrow range
                d = -d
                v = m[i - 1] + d * size
            run += size != 0
            m[i] = v
        return m

    def _nudge_motif(self, m):
        if self.rnd(10) < 6:
            # C: m->iv[1 + rnd(n - 1)] += rnd(2) ? 1 : -1; GCC draws the right side first (the parity test pins it)
            s = 1 if self.rnd(2) else -1
            m[1 + self.rnd(len(m) - 1)] += s

    def _new_statement(self, middle, chord, n):
        carry = self.handover and self.mel_kind >= 0 and self.have_motif[self.mel_kind]   # a handover: the old motif
        if not carry and (self.mel_kind != self.kind or not self.have_motif[self.kind]):   # the section's own motif
            self.mel_kind = self.kind
            if self.have_motif[self.kind]:
                self._nudge_motif(self.motif[self.kind])
            else:
                self.motif[self.kind] = self._make_motif()
            self.have_motif[self.kind] = 1
            self.stmt_k = self.drift = 0
        m = self.motif[self.mel_kind]
        k, first = self.stmt_k % 4, self.stmt_k < 4
        develop = k == 2 if first else k in (1, 2)
        if k == 0 or (first and k == 3):
            form = F_MOTIF
        elif not develop:
            form = F_AGAIN if first and self.rnd(2) else F_ANSWER
        else:
            r = self.rnd(10)
            form = F_MOVED if r < 3 else F_INVERT if r < 5 else F_BACK if r < 6 else F_SHORT if r < 8 else F_LONGER
        st = m[:]
        if form == F_INVERT:
            st = [-v for v in m]
        elif form == F_BACK:
            st = [m[len(m) - 1 - i] - m[-1] for i in range(len(m))]
        elif form == F_SHORT:
            st = st[:len(m) - 1 - self.rnd(len(m) - 3)] if len(m) > 3 else st
        elif form == F_LONGER and len(st) < MOTIF_MAX:
            last, prev = m[-1], (m[-2] if len(m) > 1 else 0)
            st.append(last + (1 if last >= prev else -1))   # one more step the way it was going
        if form == F_MOVED or (form == F_INVERT and self.rnd(2)):
            # C: (rnd(2) ? 1 : -1) * (1 + rnd(2)), operands in GCC's order (the parity test pins it)
            sign = 1 if self.rnd(2) else -1
            s = sign * (1 + self.rnd(2))
            self.drift = self.drift - s if (self.drift + s > ROAM or self.drift + s < -ROAM) else self.drift + s
            base = self.stmt_base + s if self.stmt_on else chord_tone(middle + self.drift, chord, n, 0)
        else:
            if k == 0 and first:
                self.drift = 0
            elif k == 0:
                self.drift = _cdiv(self.drift, 2)   # the theme comes back, partway toward the middle
            base = chord_tone(middle + self.drift, chord, n, 0)
        if base > middle + ROAM + 1 or base < middle - ROAM - 1:
            base = chord_tone(middle + self.drift, chord, n, 0)
        if form == F_ANSWER:   # the motif again, landing on the chord's root
            st[-1] = chord_tone(base + st[-1], chord, n, 1) - base
        self.stmt = st
        self.stmt_base, self.stmt_pos, self.stmt_on = base, 0, 1
        self.stmt_k += 1
        self.out.append(("form", [form, base]))

    def note(self, fmid, fchord, fn):
        fmid, fchord, fn = f32(fmid), f32(fchord), f32(fn)
        middle, chord, n = int(fmid), int(fchord), int(fn) if fn >= 1 else 7
        if (not self.stmt_on or (self.systime - self.last_note) / TIMEUNITPERMSEC > GAP_MS
                or self.stmt_pos >= len(self.stmt)):
            self._new_statement(middle, chord, n)
        deg = self.stmt_base + self.stmt[self.stmt_pos]
        self.stmt_pos += 1
        while deg > middle + ROAM + 4:   # (whole octaves back toward the middle)
            deg -= n
        while deg < middle - ROAM - 4:
            deg += n
        self.last_note = self.systime
        self.out.append(("mel", deg))

    # ---- patterns made by rules ----

    def _make_drums(self, d, brk, p):
        V = _V
        for lane in p:
            lane[:] = [0.0] * 16
        kicks = 2 + int(f32(f32(3 * d) + 0.5))
        for i in range(16):
            if euclid(i, kicks, 0, 16):
                p[0][i] = V["k1"] if i == 0 else V["k8"] if i == 8 else V["kk"]
        if brk > V["c3"] and p[0][8] > 0 and self.rnd(2):   # a breakbeat leans the middle kick late
            p[0][8], p[0][10] = 0.0, V["kl"]
        if d < V["c2"]:
            p[1][12] = V["sq"]
        else:
            p[1][4] = p[1][12] = V["sn"]
        g = int(f32(f32(f32(f32(3 * d) * self.rnd(100)) / 100.0) + 0.5))
        for _ in range(g):
            p[1][GHOST[self.rnd(5)]] = V["gh"]
        hats = 4 + int(f32(f32(8 * d) + 0.5))
        rot = 2 if hats == 4 and self.rnd(3) == 0 else 0   # (4 hats: sometimes off the beat)
        for i in range(16):
            if euclid(i, hats, rot, 16):
                p[2][i] = V["h4"] if i % 4 == 0 else V["h2"] if i % 2 == 0 else V["h1"]
        if d > V["c5"] and self.rnd(2):
            p[2][14] = V["ho"]   # an open hat before the bar comes round

    def _vary_drums(self, p):
        V = _V
        what = self.rnd(3)
        if what == 0:
            hits = [i for i in range(1, 16) if 0 < p[0][i] < V["kl"]]   # (the downbeat and the strong middle kick stay put)
            if hits:
                frm = hits[self.rnd(len(hits))]
                # C: from + (rnd(2) ? 1 : -1) * (1 + rnd(2)), operands in GCC's order (the parity test pins it)
                sign = 1 if self.rnd(2) else -1
                to = frm + sign * (1 + self.rnd(2))
                if 0 < to < 16 and p[0][to] == 0:
                    p[0][to], p[0][frm] = V["km"], 0.0
            else:
                p[0][6 + 4 * self.rnd(2)] = V["km"]
        elif what == 1:
            i = GHOST[self.rnd(5)]
            if p[1][i] < V["c5"]:
                p[1][i] = 0.0 if p[1][i] > 0 else V["gh"]
        else:
            i = 1 + 2 * self.rnd(8)   # an off-beat 16th
            if i in (15, 13):
                p[2][14] = V["h2"] if p[2][14] >= 2 else V["ho"] if p[2][14] > 0 else V["h2"]
            else:
                p[2][i] = 0.0 if p[2][i] > 0 else V["h1"]

    def _pat_kind(self, cur):   # the section whose patterns play: the old piece's for the first phrase of a handover
        return cur if self.handover == 1 and cur >= 0 else self.kind

    def drums(self, fdrive, fbrk):
        k = self._pat_kind(self.drum_kind)
        d = f32(f32(fdrive) + KIND_DRIVE[k])
        d = 0.0 if d < 0 else 1.0 if d > 1 else d
        if not self.drum_have[k] or abs(f32(d - self.drum_d[k])) > _V["c15"]:   # this section's own bar
            self._make_drums(d, f32(fbrk), self.drum_base[k])
            self.drum_have[k], self.drum_d[k], self.drum_kind = 1, d, -1
        if self.drum_kind != k or self._bump("drum_bars") % 4 == 0:
            if self.drum_kind != k:
                self.drum_bars = 0
            self.drum_kind = k
            self.drum_cur = [lane[:] for lane in self.drum_base[k]]
        elif self.rnd(10) < 7:
            self._vary_drums(self.drum_cur)
        for lane in range(3):
            drop = lane < 2 and self.leadin and self.pos == PLEN - 1   # the drop
            self.out.append(("drum", [lane] + ([0.0] * 16 if drop else self.drum_cur[lane][:])))

    def _bline_step(self, d, hold):
        n, r = SCALE_N[self.scale], self.rnd(100)
        p = [0 if r < 55 else n if r < 75 else (4 if n == 7 else 3) if r < 90 else 1, 0, 0]
        if self.rnd(100) < 35 - int(f32(20 * d)):
            p[0] = -1
        if p[0] >= 0 and hold and self.rnd(100) < hold:
            p[0] = -2
        p[2] = int(p[0] >= 0 and self.rnd(4) == 0)
        return p

    @staticmethod
    def _bline_prev(p, i):
        for j in range(i - 2, -1, -2):
            if p[j][0] != -2:
                return p[j][0]
        return -1

    def bline(self, fdrive):
        k = self._pat_kind(self.bline_kind)
        d = f32(f32(fdrive) + KIND_DRIVE[k])
        d = 0.0 if d < 0 else 1.0 if d > 1 else d
        if not self.bline_have[k]:
            for i in range(16):
                self.bline_base[k][i] = [-2, 0, 0]
                if not i % 2:
                    hold = KIND_BLINE_HOLD[k] if self._bline_prev(self.bline_base[k], i) >= 0 else 0
                    self.bline_base[k][i] = self._bline_step(d, hold)
                    if not i:
                        self.bline_base[k][i][0] = 0
            self.bline_base[k][0][0] = 0
            for i in range(2, 16, 2):
                self.bline_base[k][i][1] = int(self.bline_base[k][i][0] >= 0 and
                    self._bline_prev(self.bline_base[k], i) >= 0 and self.rnd(6) == 0)
            self.bline_have[k] = 1
        if self.bline_kind != k or self._bump("bline_bars") % 4 == 0:
            if self.bline_kind != k:
                self.bline_bars = 0
            self.bline_kind = k
            self.bline_cur = [p[:] for p in self.bline_base[k]]
        elif self.rnd(10) < 7:
            edits = 1 + self.rnd(2)
            for _ in range(edits):
                i = 2 * self.rnd(8)
                hold = KIND_BLINE_HOLD[k] if self._bline_prev(self.bline_cur, i) >= 0 else 0
                self.bline_cur[i] = self._bline_step(d, hold)
                if not i or (self.bline_cur[i][0] == -1 and i < 14 and self.bline_cur[i + 2][0] == -2):
                    self.bline_cur[i][0] = 0
                self.bline_cur[i][1] = int(self.bline_cur[i][0] >= 0 and
                    self._bline_prev(self.bline_cur, i) >= 0 and self.rnd(6) == 0)
        for i in range(16):
            if self.bline_cur[i][0] < 0 or self._bline_prev(self.bline_cur, i) < 0:
                self.bline_cur[i][1] = 0
        self.out.append(("bline", [v for p in self.bline_cur for v in p]))

    def _bump(self, name):
        """C's ++x->name, used inside a condition."""
        setattr(self, name, getattr(self, name) + 1)
        return getattr(self, name)

    def _make_arp(self, pace, n, p):
        top = 3 + int(f32(f32(2 * pace) + 0.5))
        shape = self.rnd(5)
        t = [0] * ARP_LEN
        for i in range(ARP_LEN):
            up, tri = i % (top + 1), (i if i <= top else 2 * top - i)
            if shape == 0:
                t[i] = max(tri, 0)                   # rise and fall
            elif shape == 1:
                t[i] = up                            # rising
            elif shape == 2:
                t[i] = top - up                      # falling
            elif shape == 3:
                t[i] = i // 2 + (i % 2) * 2          # broken: 0 2 1 3 2 4 ..
            else:
                t[i] = 1 + (i // 2) % top if i % 2 else 0   # around the root
            t[i] = min(t[i], top + 1)
        for i in range(ARP_LEN):
            p[i] = tone_step(t[i], n)
            if i % 2 and self.rnd(4) == 0:
                p[i] += 1                            # a passing note on a weak step

    def arp(self, fpace, fn):
        fpace, fn = f32(fpace), f32(fn)
        k, n = self._pat_kind(self.arp_kind), int(fn) if fn >= 1 else 7
        pace = 0.0 if fpace < 0 else 1.0 if fpace > 1 else fpace
        if not self.arp_have[k] or n != self.arp_n or abs(f32(pace - self.arp_pace[k])) > _V["c3"]:
            self._make_arp(pace, n, self.arp_base[k])
            self.arp_have[k], self.arp_pace[k], self.arp_n, self.arp_kind = 1, pace, n, -1
        if self.arp_kind != k or self._bump("arp_bars") % 4 == 0:
            if self.arp_kind != k:
                self.arp_bars = 0
            self.arp_kind = k
            self.arp_cur = self.arp_base[k][:]
        elif self.arp_bars % 8 == 6:                 # the figure backwards
            self.arp_cur = self.arp_base[k][::-1]
        elif self.rnd(10) < 6:                       # a note moves to a neighbouring chord tone
            i, t = 1 + self.rnd(ARP_LEN - 1), 0      # (the bar's first note stays)
            while tone_step(t + 1, n) <= self.arp_cur[i] and t < 7:
                t += 1
            t += 1 if (t == 0 or self.rnd(2)) else -1
            self.arp_cur[i] = tone_step(t, n)
        self.out.append(("arp", self.arp_cur[:]))

    def _make_cell(self, d, dotted, on):
        on[:] = [0] * 16
        if not dotted:
            k = CELL_K_STRAIGHT[int(f32(f32(d * 4) + 0.5))]   # even counts on the 8ths stay straight
            for i in range(8):
                on[2 * i] = euclid(i, k, 0, 8)
        else:
            k = CELL_K_DOTTED[int(f32(f32(d * 2) + 0.5))]     # odd counts on the 16ths: 3+3+2-like, dotted
            late = 2 if self.rnd(4) == 0 else 0
            for i in range(16):
                if euclid(i, k, 0, 16) and i + late < 16:
                    on[i + late] = 1
        if not on[0] and not on[2]:
            on[0] = 1

    def _vary_cell(self, dotted, on):
        at = [i for i in range(16) if on[i]]
        n, grid = len(at), (1 if dotted else 2)
        what = self.rnd(3)
        if what == 0 and n > 1:                      # a note (not the first) moves
            i = at[1 + self.rnd(n - 1)]
            to = i + (grid if self.rnd(2) else -grid)
            if 0 < to < 16 and not on[to]:
                on[to], on[i] = 1, 0
        elif what == 1:                              # a long note splits
            for j in range(n):
                end = at[j + 1] if j + 1 < n else 16
                if end - at[j] >= 4:
                    on[at[j] + (end - at[j]) // 2 // grid * grid] = 1
                    break
        elif n > 2:                                  # two notes merge
            on[at[1 + self.rnd(n - 2)]] = 0

    def cell(self, fdrive, fstyle):
        k, style = self._pat_kind(self.cell_kind), int(f32(fstyle))
        d = f32(f32(fdrive) + KIND_DRIVE[k])
        d = 0.0 if d < 0 else 1.0 if d > 1 else d
        if style == 2:
            dotted = 1
        elif style == 3:
            dotted = int(self.cell_style[k] == 2) if self.cell_have[k] else self.rnd(2)
        else:
            dotted = 0
        if (not self.cell_have[k] or abs(f32(d - self.cell_d[k])) > _V["c2"]
                or (style != 3 and (self.cell_style[k] == 2) != bool(dotted))):
            self._make_cell(d, dotted, self.cell_base[k])
            self.cell_have[k], self.cell_d[k], self.cell_style[k], self.cell_kind = 1, d, (2 if dotted else 1), -1
        dotted = self.cell_style[k] == 2
        if self.cell_kind != k or self._bump("cell_bars") % 4 == 0:
            if self.cell_kind != k:
                self.cell_bars = 0
            self.cell_kind = k
            self.cell_cur = self.cell_base[k][:]
        elif self.rnd(10) < 6:
            self._vary_cell(dotted, self.cell_cur)
        lens, count, last = [0] * 16, 0, 0
        for i in range(16):
            if self.cell_cur[i]:
                j = i + 1
                while j < 16 and not self.cell_cur[j]:
                    j += 1
                lens[i], count, last = j - i, count + 1, i
        self.out.append(("cell", lens + [count, last]))

    # ---- messages ----

    def bar(self):
        self._clock_delay(self._bar_ms() * 1.6)
        if not self.started:
            return
        self.piece_bars -= 1
        self.bars_left -= 1
        if self.bars_left <= 0:
            self._advance()
        elif self.sus_voice >= 0:   # a sus chord resolves
            self.voice[self.sus_voice] = self.sus_third
            self.sus_voice = -1
            self._emit()

    def _piece(self):   # a new piece: forget the sections, Home first
        for k in range(NKINDS):
            self.have[k] = self.have_motif[k] = self.drum_have[k] = self.arp_have[k] = self.cell_have[k] = self.bline_have[k] = 0
        self.drum_kind = self.arp_kind = self.cell_kind = self.bline_kind = -1
        self.voiced = 0
        self.mel_kind = -1
        self.stmt_on = 0
        self.last_away = CALM
        self.leadin = self.handover = 0
        self.piece_bars = PIECE_BARS   # (the first piece draws no random number: a seed gives the same piece)
        self._begin_section(HOME)

    def _handover(self):   # the new piece takes over: its own chords and sections, under the old groove and motif
        for k in range(NKINDS):
            self.have[k] = 0
        self.last_away = CALM
        self.leadin = 0
        self.handover = 1
        self.piece_bars = PIECE_BARS + self.rnd(PIECE_BARS // 2 + 1)
        self._begin_section(HOME)

    def renew_(self, f):
        self.renew = int(f32(f) >= 0.5)
        if not self.renew:
            self.leadin = 0   # (a handover under way finishes)

    def scale_(self, f):
        s = int(f32(f))
        self.scale = 0 if s < 0 else NSCALES - 1 if s >= NSCALES else s
        self._piece()
        if self.started:
            self._play_pos(1)

    def start(self):
        self.started = 1
        self._play_pos(1)
        self._clock_delay(self._bar_ms() * 1.6)

    def again(self):
        if self.started:
            self._emit()

    def tempo(self, f):
        self.bpm = f32(f)

    def color_(self, f):
        self.color = int(f32(f) >= 0.5)

    def bright_(self, f):
        f = f32(f)
        self.bright = 0.0 if f < 0 else 1.0 if f > 1 else f

    def energy_(self, f):
        f = f32(f)
        self.energy = 0.0 if f < 0 else 1.0 if f > 1 else f

    def seed(self, f):
        self.r.seed(f32(f))
        self._piece()

    def send(self, selector, *args):
        """A message by its Pd name, e.g. send("scale", 3)."""
        getattr(self, {"scale": "scale_", "color": "color_", "renew": "renew_", "bright": "bright_", "energy": "energy_",
                       "bang": "again"}.get(selector, selector))(*args)
