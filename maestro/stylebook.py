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
          "turn rates": dict, "shape": str, "loop": dict,
          "voices": (2, 4), "shapes": dict, "rate": dict, "calm": str, "pump": (0, 100), "echo": (0, 100),
          "gain": (-40, 20)}   # gain: dB in the clip player's mix, set from the mix check (task 3.8)
TEMPO = (20, 400)


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
    _keys(entry, ("style", "license", "sources", "time", "harmony", "form", "members", "mix"), name)
    if "mix" in entry:
        check_mix(entry["mix"], f"{name}: mix")
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
            if rule in (str, dict) and not isinstance(v, rule) or isinstance(rule, tuple) and not (
                    isinstance(v, int) and not isinstance(v, bool) and rule[0] <= v <= rule[1]):
                want = {str: "words", dict: "an object"}.get(rule) or f"a whole number from {rule[0]} to {rule[1]}"
                raise StyleError(f"{name}: members.{role}.{k} must be {want}, got {v!r}")


def check_mix(mix, where):
    """The mix targets: {role or "top": [low, high] dB}. A member's loudness against the melody's; "top": how far
    the melody sits over the loudest other member."""
    _keys(mix, ROLES + ("top",), where)
    for k, v in mix.items():
        if k != "why" and not (isinstance(v, list) and len(v) == 2 and all(map(_number, v)) and v[0] <= v[1]):
            raise StyleError(f"{where}.{k} must be [low, high] in dB, got {v!r}")


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
    return {s: make(cls, part(s, *path), f"{s}: {'.'.join(path)}") for s in STYLES}
