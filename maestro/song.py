# SPDX-License-Identifier: GPL-3.0-or-later
"""A song file (`docs/format.md`, "The song file"): a standard MIDI file, one track per member named after it, and a
JSON file beside it with what MIDI can't hold (the timeline, each member's role and sound, where the clip came from
and what to listen for). Ticks: 480 a beat. Notes are kept in grid steps (24 a beat, `theory/rhythm.py`), so every
note starts and ends on point on the grid (decision 13); a note that isn't on a step can't be written."""
import json
from dataclasses import dataclass, field

import mido

from .theory.rhythm import STEPS, TICK, TICKS

DRUMS_CHANNEL = 9   # General MIDI's kit channel (10, counted from 1)


@dataclass(frozen=True)
class Note:
    step: int        # start, in grid steps from the clip's start
    steps: int       # length in steps
    pitch: int       # MIDI note number (General MIDI drum note on a kit)
    velocity: int = 96

    def __post_init__(self):
        for name in ("step", "steps", "pitch", "velocity"):
            if not isinstance(getattr(self, name), int):
                raise ValueError(f"{name} must be a whole number (on the grid): {getattr(self, name)!r}")
        if self.step < 0 or self.steps < 1 or not 0 <= self.pitch <= 127 or not 1 <= self.velocity <= 127:
            raise ValueError(f"note out of range: {self}")


@dataclass
class Member:
    name: str                 # the track's name
    role: str                 # what it is for: drums, bass, pad, melody, arp, guitar, keys, horns, percussion
    program: int = 0          # its sound: a General MIDI program (decision 3: the sound is kept apart from the style)
    kit: bool = False         # a drum kit (plays on the kit channel)
    notes: list = field(default_factory=list)

    def add(self, step, steps, pitch, velocity=96):
        self.notes.append(Note(step, steps, pitch, velocity))


@dataclass
class Song:
    tempo: float = 100.0
    meter: tuple = (4, 4)
    members: list = field(default_factory=list)
    timeline: list = field(default_factory=list)   # one entry per bar or change (format.md, "The timeline")
    source: dict = field(default_factory=dict)     # where it came from: set, license, seed...
    listen: str = ""                               # what DadCraft listens for (said before the clip plays)

    def member(self, name, role, program=0, kit=False):
        m = Member(name, role, program, kit)
        self.members.append(m)
        return m

    def bar_steps(self):
        num, den = self.meter
        return num * STEPS * 4 // den

    def write(self, stem):
        """Writes `<stem>.mid` and `<stem>.json`; returns the MIDI path."""
        mid = mido.MidiFile(type=1, ticks_per_beat=TICKS)
        head = mido.MidiTrack()
        head.append(mido.MetaMessage("track_name", name="timeline", time=0))
        head.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.tempo), time=0))
        head.append(mido.MetaMessage("time_signature", numerator=self.meter[0], denominator=self.meter[1], time=0))
        mid.tracks.append(head)
        chan = iter(c for c in range(16) if c != DRUMS_CHANNEL)
        for m in self.members:
            ch = DRUMS_CHANNEL if m.kit else next(chan)
            tr = mido.MidiTrack()
            tr.append(mido.MetaMessage("track_name", name=m.name, time=0))
            if not m.kit:
                tr.append(mido.Message("program_change", channel=ch, program=m.program, time=0))
            ev = []   # (tick, 0 = off before 1 = on at the same tick, message)
            for n in m.notes:
                ev.append((n.step * TICK, 1, mido.Message("note_on", channel=ch, note=n.pitch, velocity=n.velocity)))
                ev.append(((n.step + n.steps) * TICK, 0, mido.Message("note_off", channel=ch, note=n.pitch)))
            now = 0
            for t, _, msg in sorted(ev, key=lambda e: (e[0], e[1])):
                tr.append(msg.copy(time=t - now))
                now = t
            mid.tracks.append(tr)
        mid.save(f"{stem}.mid")
        info = {"tempo": self.tempo, "meter": f"{self.meter[0]}/{self.meter[1]}", "source": self.source,
                "listen": self.listen,
                "members": {m.name: {"role": m.role, "sound": "kit" if m.kit else m.program} for m in self.members},
                "timeline": self.timeline}
        with open(f"{stem}.json", "w") as f:
            json.dump(info, f, indent=1)
        return f"{stem}.mid"


def read_notes(path):
    """A MIDI file's notes per track name: {name: [Note]}. Refuses a note off the grid (decision 13)."""
    mid = mido.MidiFile(path)
    scale = TICKS / mid.ticks_per_beat
    out = {}
    for tr in mid.tracks:
        name, now, held, notes = tr.name, 0, {}, []
        for msg in tr:
            now += msg.time
            if msg.type not in ("note_on", "note_off"):
                continue
            t = now * scale
            if t % TICK:
                raise ValueError(f"{path}: {name} has a note off the grid at tick {now}")
            key = (msg.channel, msg.note)
            if msg.type == "note_on" and msg.velocity:
                held[key] = (int(t) // TICK, msg.velocity)
            elif key in held:
                s, v = held.pop(key)
                notes.append(Note(s, int(t) // TICK - s, msg.note, v))
        if notes:
            out[name] = sorted(notes, key=lambda n: (n.step, n.pitch))
    return out
