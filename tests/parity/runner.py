# SPDX-License-Identifier: GPL-3.0-or-later
"""The parity check: the same messages to Ouralia's real dcs_composer (through Ouralia's test engine, read-only:
its desktop libpd and built dcs lib) and to maestro.port, and every output compared, message by message.

    python tests/parity/runner.py <scenario> <result.json>    (one scenario in a fresh process: Pd's clock at 0)

test_parity.py runs each scenario this way (libpd prints to stdout, and is one global instance per process).
"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from maestro.port import Composer, f32   # noqa: E402

OURALIA = os.environ.get("MAESTRO_OURALIA", os.path.join(os.path.dirname(ROOT), "Ouralia"))
LIB = os.path.join(OURALIA, "tools", ".libpd", "libpd.so")
DCS_LIB = os.path.join(OURALIA, "dcs", "build", "dcs.pd_linux")
DCS_SRC = os.path.join(OURALIA, "dcs", "src", "dcs_composer.c")
OUTLETS = ("chord", "sect", "mel", "form", "drum", "arp", "cell", "bline")
SR, BLOCK = 48000, 64


def blocks(seconds):
    return int(seconds * SR) // BLOCK


def scenarios():
    """name -> steps; a step is ("msg", selector, *args) or ("run", blocks)."""
    sc = {}
    tempos = [100, 72, 140, 100, 160, 90, 120, 100]
    for s in range(8):   # chords, cadences, phrases, sections and their memory, voicing, bass, colours: every scale
        steps = [("msg", "tempo", tempos[s]), ("msg", "color", s % 2), ("msg", "bright", 0.1 * s),
                 ("msg", "energy", 0.9 - 0.1 * s), ("msg", "seed", 7 * s + 3), ("msg", "scale", s), ("msg", "start")]
        for b in range(400):
            steps.append(("msg", "bar"))
            if b == 150:
                steps += [("msg", "energy", 1.0), ("msg", "bright", 1.0), ("msg", "again"), ("msg", "bang")]
            if b == 250:
                steps += [("msg", "energy", 0.0), ("msg", "color", 1 - s % 2), ("msg", "tempo", 200)]
        sc[f"chords_scale{s}"] = steps
    for name, scale, color, n, brk in (("patterns_minpent", 3, 0, 5, 0.6), ("patterns_major", 0, 1, 7, 0.0),
                                       ("patterns_whole", 7, 1, 6, 0.4)):
        steps = [("msg", "color", color), ("msg", "seed", 11 + scale), ("msg", "scale", scale), ("msg", "start")]
        for b in range(240):
            drive = 0.5 + 0.5 * math.sin(b / 17.0)
            steps += [("msg", "bar"), ("msg", "drums", drive, brk), ("msg", "arp", 1 - drive, n),
                      ("msg", "cell", drive, 1 + (b // 30) % 3)]
        sc[name] = steps
    for name, scale, n, sections in (("melody_free", 3, 5, False), ("melody_sections", 0, 7, True),
                                     ("melody_dorian", 4, 7, True)):
        steps = [("msg", "seed", 3 + scale), ("msg", "scale", scale)] + ([("msg", "start")] if sections else [])
        for burst in range(60):
            for i in range(3 + burst % 6):
                steps.append(("msg", "note", 7 - burst % 5, (burst * 3) % n, n))
                steps.append(("run", blocks(0.4)))
                if sections:
                    steps += [("msg", "bar")] * 3
            steps.append(("run", blocks(3.0) if burst % 4 else blocks(1.0)))
        sc[name] = steps
    # no bars at all: the composer keeps its own time; then the clock comes back, a new scale and seed mid-piece
    sc["no_clock"] = ([("msg", "tempo", 120), ("msg", "seed", 21), ("msg", "scale", 0), ("msg", "start"),
                       ("msg", "bar")] + [("run", blocks(1.0))] * 60 + [("msg", "bar")] * 40
                      + [("msg", "scale", 5)] + [("run", blocks(0.5))] * 40 + [("msg", "seed", 22)]
                      + [("msg", "bar"), ("msg", "drums", 0.7, 0.5), ("run", blocks(0.3))] * 60)
    # new pieces (renew): handovers with the open ending, the drop, the old groove and motif carried, then new ones;
    # renew off mid-piece and back on
    for name, scale, seed in (("renew_minor", 1, 31), ("renew_dorian", 4, 32)):
        steps = [("msg", "renew", 1), ("msg", "seed", seed), ("msg", "scale", scale), ("msg", "start")]
        for b in range(420):
            drive = 0.5 + 0.5 * math.sin(b / 23.0)
            steps += [("msg", "bar"), ("msg", "drums", drive, 0.3), ("msg", "arp", 1 - drive, 7),
                      ("msg", "cell", drive, 1 + (b // 40) % 3), ("msg", "note", 7 - b % 5, (b * 3) % 7, 7)]
            if b == 300:
                steps.append(("msg", "renew", 0))
            if b == 330:
                steps.append(("msg", "renew", 1))
        sc[name] = steps
    for name, scale in (("bline_minor", 1), ("bline_pent", 3), ("bline_major", 0), ("bline_whole", 7)):
        steps = [("msg", "seed", 47), ("msg", "scale", scale), ("msg", "renew", 1), ("msg", "start")]
        for b in range(420):
            steps += [("msg", "bar"), ("msg", "bline", (b % 21) / 20), ("msg", "drums", 0.5, 0.3)]
            if b == 250:
                steps.append(("msg", "scale", 7))
        sc[name] = steps
    # before start: bars and patterns while nothing plays yet
    sc["before_start"] = ([("msg", "seed", 9), ("msg", "bar"), ("msg", "drums", 0.3, 0), ("msg", "arp", 0.5, 7),
                           ("msg", "cell", 0.4, 3), ("msg", "note", 7, 0, 7), ("msg", "again")] * 5
                          + [("msg", "start")] + [("msg", "bar"), ("msg", "cell", 0.8, 3)] * 100)
    return sc


def run_c(steps):
    sys.path.insert(0, os.path.join(OURALIA, "tools"))
    import tempfile
    from pdtest import Engine
    lines = ["#N canvas 0 0 600 400 12;", "#X declare -lib dcs;"]
    objs = ["r cin", "dcs_composer", "s m_chord", "s m_sect", "s m_mel", "s m_form", "route drum arp cell bline",
            "s m_drum", "s m_arp", "s m_cell", "s m_bline"]
    conns = [(0, 0, 1, 0)] + [(1, i, 2 + i, 0) for i in range(4)] + [(1, 4, 6, 0)] + [(6, i, 7 + i, 0) for i in range(4)]
    lines += [f"#X obj 10 {40 + 25 * i} {t};" for i, t in enumerate(objs)]
    lines += [f"#X connect {a} {o} {b} {i};" for a, o, b, i in conns]
    path = os.path.join(tempfile.mkdtemp(prefix="maestro_parity_"), "parity.pd")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    e = Engine(LIB, path)
    names = ["m_" + o for o in OUTLETS]
    e.listen(*names)
    seen, out = {n: 0 for n in names}, []
    for step in steps:
        if step[0] == "run":
            e.run(e.silence(step[1] * BLOCK / SR))
        else:
            e.send_msg("cin", step[1], *step[2:])
        got = {}
        for o, n in zip(OUTLETS, names):
            store = e.heard[n] if o == "mel" else e.lists.get(n, [])
            if len(store) > seen[n]:
                got[o] = [v if o == "mel" else list(v) for v in store[seen[n]:]]
                seen[n] = len(store)
        out.append(got)
    e.close()
    return out


def run_port(steps):
    c, out = Composer(), []   # (seeded from the clock like the C; each scenario's seed message sets the real one)
    for step in steps:
        if step[0] == "run":
            c.tick(step[1])
        else:
            c.send(step[1], *step[2:])
        got = {}
        for o, v in c.out:
            got.setdefault(o, []).append(f32(v) if o == "mel" else [f32(x) for x in v])
        c.out.clear()
        out.append(got)
    return out


def compare(name):
    steps = scenarios()[name]
    a, b = run_c(steps), run_port(steps)
    outputs = sum(len(v) for g in a for v in g.values())
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return {"ok": False, "outputs": outputs, "step": i, "message": list(steps[i]),
                    "c": {k: v[:3] for k, v in x.items()}, "port": {k: v[:3] for k, v in y.items()}}
    return {"ok": True, "outputs": outputs, "steps": len(steps)}


if __name__ == "__main__":
    result = compare(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        json.dump(result, f)
