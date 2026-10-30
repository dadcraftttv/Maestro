"""Optional pad: syncopation, harmony, stepwise upper voice and RNG isolation."""
from maestro.port import Composer, CALM


def test_chords_motion_and_rhythm():
    intervals, offbeats, patterns, harmonies = [], 0, set(), set()
    for scale in range(8):
        c = Composer(seed=47)
        c.send("scale", scale)
        c.chords_on(1)
        c.start()
        previous = None
        for bar in range(80):
            c.bar()
            assert c.bars_left <= 2
            c.chords()
            row = c.out[-1][1]
            assert len(row) == 96
            patterns.add(tuple(row[::6]))
            harmonies.add(tuple(row[1:4]))
            assert -1 in row[::6] and -2 in row[::6]
            for i in range(16):
                if row[6*i] != 1:
                    continue
                offbeats += i % 4 != 0
                top = row[6*i+4]
                assert row[6*i+5] == top + 12
                assert all((top - n) % 12 != 1 for n in row[6*i+1:6*i+4])   # no b9 over the chord
                if previous is not None:
                    intervals.append(abs(top - previous))
                previous = top
    assert offbeats > 100
    assert len(patterns) >= 3 and len(harmonies) > 4
    assert sum(intervals) / len(intervals) <= 2
    assert max(intervals) <= 3 and sum(i <= 2 for i in intervals) / len(intervals) > .9


def test_chords_do_not_change_other_parts():
    a, b = Composer(seed=47), Composer(seed=47)
    for bar in range(200):
        for c in (a, b):
            c.bar()
        b.chords()
        b.out.pop()
        assert a.out == b.out
        for c in (a, b):
            c.drums(.5, .3)
            c.bline(.5)
        assert a.out == b.out


def test_chords_calm_is_sparser_and_seed_restarts():
    c = Composer(seed=47)
    c.chords()
    first = c.out[-1]
    c.chords()
    c.seed(47)
    c.chords()
    assert c.out[-1] == first
    c.kind = CALM
    c.chords()
    assert c.out[-1][1][::6].count(1) == 2
