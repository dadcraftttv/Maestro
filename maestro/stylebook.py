# SPDX-License-Identifier: GPL-3.0-or-later
"""The style book: one JSON file a style in `data/styles` (CC BY-SA 4.0, its sources cited; PLAN.md 3.0), read and
written with no extra library so the desk can write it too. A file holds tendencies, never fixed patterns (decision
9), and names only what differs from the theory core's defaults: a field left out keeps its default. Any part may
carry a "why" in plain words. `book.json` lists the styles, in order.

The loader checks each file as it reads it: the parts and fields it knows, the kind of each value. The theory
modules check what only they know (a chord quality, a clave) when they build their tables from it."""
import dataclasses as dc
import json
import os
import types

from .synth import SYNTHS

HERE = os.path.join(os.path.dirname(__file__), "data", "styles")
LICENSE = "CC BY-SA 4.0"
ROLES = ("drums", "percussion", "bass", "keys", "guitar", "horns", "pad", "arp", "melody")   # decision 11
PARTS = {"time": ("tempo", "rhythm", "feel"), "harmony": ("vocabulary", "leading", "progressions"), "form": None,
         "members": None}
# a member's fields, beside the theory's; patterns and their variants are checked by `theory/flow.py`, the drummer's
# grooves and timekeeping by `theory/drums.py`, the percussion's parts by `theory/percussion.py`
MEMBER = {"sound": (0, 127), "level": (1, 127), "kicks": (1, 24), "hats": str, "patterns": dict, "variants": dict,
          "grooves": dict, "time": dict, "busy": (0, 200), "fills": (0, 100), "rolls": (0, 100), "parts": dict,
          "with": str, "tones": dict, "slides": (0, 100), "develop": dict, "backbeat": str, "turns": (0, 100),
          "turn rates": dict, "loud time": dict, "shape": str, "loop": dict,
          "voices": (2, 4), "shapes": dict, "rate": dict, "calm": str, "loops": dict, "pump": (0, 100), "echo": (0, 100),
          "gain": (-40, 20),   # gain: dB in the clip player's mix, set from the mix check (task 3.8)
          "plays": bool, "walk": (0, 100), "coro": dict, "riff": dict,   # task 3.4c: a member sitting out, the
#                                                                          bass's walk-ups, the horns' loops
          "tracks": dict, "scratch": dict, "scale": str, "bends": (0, 100), "vibrato": bool,
          "double": dict, "licks": dict, "fast": (0, 100), "pan": (-64, 63),
          "lowest": str}   # 3.5c: the bass's lowest note, its instrument's (a bass guitar's E1)   # the second round: double bass,
#                                                                          the duel's licks, a lead to one side   # task 3.4d: the doubled guitars, the
#                                                                          lead's pentatonic, bends and vibrato
TEMPO = (20, 400)
# The style judge's cards (task 3.5a): what each member's playing should measure, written from the style's sources,
# never from the generator's own numbers. Each trait is [low, high, its source]; `maestro/judge.py` measures a clip
# against them (3.5b). Shares are % of the member's notes (rolls: of its bars), counted on the bars it plays.
TRAITS = {
    "notes": (0, 64),          # onsets a bar (a chord's notes struck together count once)
    "syncopation": (0, 100),   # % of onsets off the beat with no onset of the member's on the next beat
    "triplets": (0, 100),      # % of onsets off the 16th grid (triplets, 32nds)
    "rolls": (0, 100),         # % of bars holding a run of three or more onsets closer than a 16th
    "register": "names",       # [lowest, highest] note names: its 10th and 90th percentile pitches lie inside
    "chord tones": (0, 100),   # % of onsets on a beat that are tones of the chord there, the one they're held into
                               # or, on a bar's last beat, the coming one (the anticipation)
    "velocity": (0, 127),      # the spread (standard deviation) of its velocities
    "repeats": (0, 100),       # % of bars whose onsets repeat one of the two bars it played before
    "length": (0, 64),         # its median note length, in beats
    "voices": (1, 12),         # the median count of pitch classes struck together
    "slides": (0, 100),        # % of notes sliding (a pitch bend) into place
    "top": (0, 100),           # % of its onsets over every other pitched member sounding then
}
BAND = {"tempo": TEMPO, "chords": (0, 16)}   # BPM; chords a bar
# "steps": [[16ths of the bar, 0-15], low, high, source]: each step listed is hit in low-high % of the bars played
DRUM_LANES = ("kick", "snare", "hats", "cymbals", "toms")   # snare holds the clap, hats the open and pedal ones
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


class StyleError(ValueError):
    pass


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _keys(d, known, where):
    if not isinstance(d, dict):
        raise StyleError(f"{where}: expected an object, got {d!r}")
    for k in d:
        if k == "why":
            if not isinstance(d[k], str):
                raise StyleError(f"{where}.why: expected words, got {d[k]!r}")
        elif k not in known:
            raise StyleError(f"{where}: unknown part {k!r} (known: {', '.join(known)})")


def check(entry, name):
    """Raise a StyleError saying where, when a style file isn't one the book can read."""
    _keys(entry, ("style", "license", "sources", "time", "harmony", "form", "members", "mix", "arrange", "layers", "judge"),
          name)
    if "mix" in entry:
        check_mix(entry["mix"], f"{name}: mix")
    if "judge" in entry:
        check_judge(entry["judge"], entry.get("members", {}), f"{name}: judge")
    if entry.get("style") != name:
        raise StyleError(f"{name}: its \"style\" is {entry.get('style')!r}, not its file name")
    if entry.get("license") != LICENSE:
        raise StyleError(f"{name}: style data is {LICENSE} (README \"License\"), not {entry.get('license')!r}")
    src = entry.get("sources")
    if not src or not isinstance(src, list) or not all(isinstance(s, str) and s for s in src):
        raise StyleError(f"{name}: \"sources\" must cite at least one source")
    for part, subs in PARTS.items():
        if part in entry and subs:
            _keys(entry[part], subs, f"{name}: {part}")
    tempo = entry.get("time", {}).get("tempo")
    if not isinstance(tempo, int) or isinstance(tempo, bool) or not TEMPO[0] <= tempo <= TEMPO[1]:
        raise StyleError(f"{name}: time.tempo must be a whole BPM from {TEMPO[0]} to {TEMPO[1]}, got {tempo!r}")
    if "feel" in entry["time"]:
        _keys(entry["time"]["feel"], ("*",) + ROLES, f"{name}: time.feel")
    members = entry.get("members", {})
    _keys(members, ROLES, f"{name}: members")
    for role, m in members.items():
        if role == "why":
            continue
        _keys(m, tuple(MEMBER), f"{name}: members.{role}")
        for k, v in m.items():
            rule = MEMBER.get(k)
            if k == "sound" and isinstance(v, str):     # one of Maestro's own sounds (synth.py), else GM
                if v not in SYNTHS:
                    raise StyleError(f"{name}: members.{role}.sound: no sound {v!r} (Maestro's own: "
                                     f"{', '.join(SYNTHS)}; else a GM program)")
                continue
            if rule in (str, dict, bool) and not isinstance(v, rule) or isinstance(rule, tuple) and not (
                    isinstance(v, int) and not isinstance(v, bool) and rule[0] <= v <= rule[1]):
                want = {str: "words", dict: "an object", bool: "true or false"}.get(rule) or f"a whole number from {rule[0]} to {rule[1]}"
                raise StyleError(f"{name}: members.{role}.{k} must be {want}, got {v!r}")


def check_mix(mix, where):
    """The mix targets: {role or "top": [low, high] dB}. A member's loudness against the melody's; "top": how far
    the melody sits over the loudest other member."""
    _keys(mix, ROLES + ("top",), where)
    for k, v in mix.items():
        if k != "why" and not (isinstance(v, list) and len(v) == 2 and all(map(_number, v)) and v[0] <= v[1]):
            raise StyleError(f"{where}.{k} must be [low, high] in dB, got {v!r}")


def midi(name):
    """A note name ("E1", "C#4", "Bb3") as its MIDI number, C4 = 60; None when it isn't one."""
    if not isinstance(name, str) or not name or name[0] not in NOTE:
        return None
    pc, rest = NOTE[name[0]], name[1:]
    if rest[:1] in ("#", "b"):
        pc, rest = pc + (1 if rest[0] == "#" else -1), rest[1:]
    try:
        return pc + 12 * (int(rest) + 1)
    except ValueError:
        return None


def _trait(v, rule, where):
    if not (isinstance(v, list) and len(v) == 3 and isinstance(v[2], str) and v[2]):
        raise StyleError(f"{where} must be [low, high, its source], got {v!r}")
    lo, hi = (midi(v[0]), midi(v[1])) if rule == "names" else v[:2]
    if rule == "names":
        if lo is None or hi is None:
            raise StyleError(f"{where}: expected note names like \"E1\", got {v[:2]!r}")
    elif not (_number(lo) and _number(hi) and rule[0] <= lo and hi <= rule[1]):
        raise StyleError(f"{where}: expected numbers from {rule[0]} to {rule[1]}, got {v[:2]!r}")
    if lo > hi:
        raise StyleError(f"{where}: low over high, {v[:2]!r}")


def _card(card, where):
    _keys(card, tuple(TRAITS) + ("steps",), where)
    for k, v in card.items():
        if k == "steps":
            if not isinstance(v, list) or not v:
                raise StyleError(f"{where}.steps must list [[16ths], low, high, its source]")
            for s in v:
                if not (isinstance(s, list) and len(s) == 4 and isinstance(s[0], list) and s[0] and all(
                        isinstance(i, int) and not isinstance(i, bool) and 0 <= i <= 15 for i in s[0])):
                    raise StyleError(f"{where}.steps: expected [[16ths 0-15], low, high, its source], got {s!r}")
                _trait(s[1:], (0, 100), f"{where}.steps {s[0]}")
        elif k != "why":
            _trait(v, TRAITS[k], f"{where}.{k}")


def check_judge(judge, members, where):
    """The style's cards: "band" (tempo, chords a bar), then a role's traits; drums and percussion by lane (the
    drum lanes, the percussion's own parts)."""
    _keys(judge, ("band",) + ROLES, where)
    for role, card in judge.items():
        if role == "why":
            continue
        if role == "band":
            _keys(card, tuple(BAND), f"{where}.band")
            for k, v in card.items():
                if k != "why":
                    _trait(v, BAND[k], f"{where}.band.{k}")
        elif role in ("drums", "percussion"):
            lanes = DRUM_LANES if role == "drums" else tuple(members.get("percussion", {}).get("parts", {}))
            _keys(card, lanes, f"{where}.{role}")
            for lane, c in card.items():
                if lane != "why":
                    _card(c, f"{where}.{role}.{lane}")
        else:
            _card(card, f"{where}.{role}")


def load(folder=HERE):
    """{style: its checked entry}, in the book's order."""
    global MIX
    with open(os.path.join(folder, "book.json")) as f:
        head = json.load(f)
    names, MIX = head["styles"], head.get("mix", {})
    check_mix(MIX, "book.json: mix")
    files = {n[:-5] for n in os.listdir(folder) if n.endswith(".json")} - {"book"}
    if set(names) != files:
        raise StyleError(f"book.json lists {sorted(names)} but the folder holds {sorted(files)}")
    book = {}
    for name in names:
        with open(os.path.join(folder, f"{name}.json")) as f:
            try:
                entry = json.load(f)
            except json.JSONDecodeError as e:
                raise StyleError(f"{name}: not valid JSON ({e})") from None
        check(entry, name)
        book[name] = entry
    return book


MIX = {}
BOOK = load()


def mix_targets(style):
    """A style's mix targets: the book's, with the style's own over them."""
    return {k: v for k, v in {**MIX, **BOOK[style].get("mix", {})}.items() if k != "why"}
STYLES = tuple(BOOK)


def part(style, *path):
    """One part of a style's entry ({} when the file leaves it out)."""
    d = BOOK[style]
    for p in path:
        d = d.get(p, {})
    return d


def _value(v, f, where):
    hint = f.type
    optional = isinstance(hint, types.UnionType) and type(None) in hint.__args__
    if optional:
        hint = next(a for a in hint.__args__ if a is not type(None))
    if v is None:
        if optional:
            return None
        raise StyleError(f"{where}: can't be left empty (null)")
    default = f.default if f.default is not dc.MISSING else f.default_factory()
    if hint is bool:
        ok = isinstance(v, bool)
    elif hint is int:
        ok = isinstance(v, int) and not isinstance(v, bool)
    elif hint is float:
        ok, v = _number(v), float(v) if _number(v) else v
    elif hint is str:
        ok = isinstance(v, str)
    elif hint in (tuple, frozenset):
        ok = isinstance(v, list) and all(x is None or isinstance(x, str) or _number(x) for x in v)
        v = hint(v) if ok else v
    elif hint is dict:
        ok = isinstance(v, dict) and all(_number(x) for x in v.values())
        if ok and default and all(isinstance(k, int) for k in default):
            try:
                v = {int(k): x for k, x in v.items()}
            except ValueError:
                ok = False
        if ok and default and any(isinstance(x, float) for x in default.values()):
            v = {k: float(x) for k, x in v.items()}
    else:
        raise TypeError(f"{where}: the book can't read a {hint} field")
    if not ok:
        raise StyleError(f"{where}: expected {hint.__name__}{' or null' if optional else ''}, got {v!r}")
    return v


def make(cls, data, where):
    """A theory dataclass from one part of a file: its fields checked and turned from JSON, the rest defaults."""
    _keys(data, tuple(f.name for f in dc.fields(cls)), where)
    fields = {f.name: f for f in dc.fields(cls)}
    kw = {k: _value(v, fields[k], f"{where}.{k}") for k, v in data.items() if k != "why"}
    try:
        return cls(**kw)
    except ValueError as e:
        raise StyleError(f"{where}: {e}") from None


def table(cls, *path):
    """{style: cls} for every style, from the same part of each file."""
    return per_style(lambda s: make(cls, part(s, *path), f"{s}: {'.'.join(path)}"))


# A style made from another at run time (a nudge, `theory/nudge.py`, task 3.9) joins the book under its own name;
# each table built with `per_style` gets its row then, so the theory reads it like any style. It never joins STYLES,
# which stays the book's own.
_TABLES = []


def per_style(build, keep=lambda s: True):
    """{style: build(style)} for each style in the book `keep` lets in, kept up to date as styles are derived."""
    d = {s: build(s) for s in BOOK if keep(s)}
    _TABLES.append((d, build, keep))
    return d


def derive(name, entry):
    """Add a style made at run time: checked like a file, then each table's row built."""
    check(entry, name)
    BOOK[name] = entry
    for d, build, keep in _TABLES:
        if keep(name):
            d[name] = build(name)
    return name


def forget(name):
    """Take a derived style out of the book and its tables again (the book's own styles stay)."""
    if name in STYLES:
        raise StyleError(f"{name} is one of the book's own styles")
    BOOK.pop(name, None)
    for d, _, _ in _TABLES:
        d.pop(name, None)
