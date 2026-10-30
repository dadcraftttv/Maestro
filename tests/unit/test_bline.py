"""Optional bass line: musical limits, memory and isolated random demand."""
from maestro.port import Composer, SCALE_N, NKINDS


def row(c, drive=0.5):
    c.bline(drive)
    return c.out.pop()[1]


def test_bline_limits_and_density():
    rests = [0, 0]
    notes = accents = slides = eligible = 0
    for drive in (0, 1):
        for seed in range(100):
            c = Composer(seed=seed)
            c.kind = 1  # Lift: no extra section holds, isolate drive's rest probability
            c.send("scale", seed % 8)
            n = SCALE_N[c.scale]
            p = row(c, drive)
            assert len(p) == 48 and p[0] == 0
            prev = -1
            for i in range(16):
                degree, slide, accent = p[3*i:3*i+3]
                assert degree in (-2, -1, 0, 1, 4 if n == 7 else 3, n)
                assert slide in (0, 1) and accent in (0, 1)
                if i % 2:
                    assert (degree, slide, accent) == (-2, 0, 0)
                    continue
                if degree < 0:
                    rests[drive] += degree == -1
                    assert not slide and not accent
                    if degree == -2:
                        assert prev >= 0
                else:
                    notes += 1
                    accents += accent
                    slides += slide
                    eligible += prev >= 0
                    if slide:
                        assert prev >= 0
                if degree != -2:
                    prev = degree
    assert 0.08 < rests[1]/800 < rests[0]/800 < 0.4
    assert 0.15 < accents/notes < 0.35
    assert 0.10 < slides/eligible < 0.23


def test_eighths_and_section_density_over_many_bars():
    means = []
    for kind in range(NKINDS):
        starts = 0
        for seed in range(20):
            c = Composer(seed=seed)
            c.kind = kind
            previous = None
            for bar in range(200):
                p = row(c)
                if previous is not None and bar % 4:
                    assert sum(a != b for a, b in zip(previous[::3], p[::3])) <= 2
                previous = p
                assert p[0] == 0
                prev = -1
                for i in range(16):
                    degree, slide, accent = p[3*i:3*i+3]
                    if i % 2:
                        assert (degree, slide, accent) == (-2, 0, 0)
                        continue
                    if degree == -2:
                        assert prev >= 0 and not slide and not accent
                    else:
                        if slide:
                            assert degree >= 0 and prev >= 0
                        prev = degree
                    starts += degree >= 0
        means.append(starts / 4000)
    assert 5 < means[0] < 6.5 and 6 < means[1] < 7
    assert 3 < means[2] < 4 and 5 < means[3] < 6.5
    assert means[2] + 2 < means[1]


def test_bline_base_return_sections_and_reset():
    c = Composer(seed=47)
    first = row(c)
    for _ in range(3):
        row(c)
    assert row(c) == first
    bases = []
    for k in range(NKINDS):
        c.kind = k
        row(c)
        bases.append(c.bline_base[k])
    assert len({str(p) for p in bases}) == NKINDS
    c.send("scale", 3)
    assert not any(c.bline_have) and c.bline_kind == -1


def test_bline_handover_carries_then_renews():
    c = Composer(seed=47)
    c.kind = 1
    row(c)
    old = [p[:] for p in c.bline_base[1]]
    c._handover()
    row(c)
    assert c.bline_kind == 1 and c.bline_base[1] == old
    c.pos = 3
    c._advance()
    assert c.handover == 2 and not any(c.bline_have)
    row(c)
    assert c.bline_base[c.kind] != old


def test_no_bline_draws_until_requested():
    c = Composer(seed=47)
    c.send("start")
    for _ in range(200):
        c.send("bar")
        c.drums(0.5, 0.3)
    assert not any(c.bline_have)
    assert all(selector != "bline" for selector, _ in c.out)
