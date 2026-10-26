# SPDX-License-Identifier: GPL-3.0-or-later
"""A song file (`docs/format.md`, "The song file"): a standard MIDI file, one track per member named after it, and a
JSON file beside it with what MIDI can't hold (the timeline, each member's role and sound, where the clip came from
and what to listen for). Ticks: 480 a beat. Notes are kept in grid steps (24 a beat, `theory/rhythm.py`), so every
note starts and ends on point on the grid (decision 13); a note that isn't on a step can't be written. A member's
slides (trap's 808, power rock's lead) are pitch bends, the bend range set to an octave; the bend is back at rest by
the next note. A member may sit to one side (its pan) and shake a held note (the mod wheel: vibrato)."""
import json
from dataclasses import dataclass, field

import mido

from .synth import SYNTHS
from .theory.rhythm import STEPS, TICK, TICKS

DRUMS_CHANNEL = 9   # General MIDI's kit channel (10, counted from 1)
BEND_RANGE = 12     # semitones a full pitch bend reaches, set on a member that slides
BEND_EVERY = 2      # steps between the points of a slide's bend
VIBRATO = 48        # the mod wheel's depth for a held note's vibrato


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
    program: int | str = 0    # its sound: a General MIDI program, or one of Maestro's own (`synth.SYNTHS`: "808")
    #                           (decision 3: the sound is kept apart from the style)
    kit: bool = False         # a drum kit (plays on the kit channel)
    pump: int = 0             # % it ducks under the kick in the clip player's mix (synthwave's pad and bass)
    gain: int = 0             # dB in the clip player's mix (the mix check's, task 3.8)
    pan: int = 0              # -64 (left) to 63 (right): power rock's doubled guitars (task 3.4d)
    notes: list = field(default_factory=list)
    slides: list = field(default_factory=list)   # (step, steps, semitones, hold): a bend from step, reached at its
    #                                              end and held `hold` steps more (a lead's bend up into its note)
    vibrato: list = field(default_factory=list)  # (step, steps): the mod wheel up, a lead's vibrato on a held note

    def add(self, step, steps, pitch, velocity=96):
        self.notes.append(Note(step, steps, pitch, velocity))

    def slide(self, step, steps, semitones, hold=0):
        if not all(isinstance(x, int) for x in (step, steps, semitones, hold)) or step < 0 or steps < 1 \
                or hold < 0 or not 0 < abs(semitones) <= BEND_RANGE:
            raise ValueError(f"slide out of range: {step, steps, semitones, hold}")
        self.slides.append((step, steps, semitones, hold))

    def shake(self, step, steps):
        if not all(isinstance(x, int) for x in (step, steps)) or step < 0 or steps < 1:
            raise ValueError(f"vibrato out of range: {step, steps}")
        self.vibrato.append((step, steps))


@dataclass
class Song:
    tempo: float = 100.0
    meter: tuple = (4, 4)
    members: list = field(default_factory=list)
    timeline: list = field(default_factory=list)   # one entry per bar or change (format.md, "The timeline")
    source: dict = field(default_factory=dict)     # where it came from: set, license, seed...
    listen: str = ""                               # what DadCraft listens for (said before the clip plays)

    def member(self, name, role, program=0, kit=False):
        if isinstance(program, str) and program not in SYNTHS:
            raise ValueError(f"{name}: no sound {program!r} (Maestro's own: {', '.join(SYNTHS)})")
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
            if isinstance(m.program, int) and (not m.kit or m.program):   # a kit's program picks GM's kit (16: Power)
                tr.append(mido.Message("program_change", channel=ch, program=m.program, time=0))
            if m.pan:
                tr.append(mido.Message("control_change", channel=ch, control=10, value=64 + m.pan, time=0))
            if m.slides:   # RPN 0, the bend range, then the RPN closed
                for c, v in ((101, 0), (100, 0), (6, BEND_RANGE), (38, 0), (101, 127), (100, 127)):
                    tr.append(mido.Message("control_change", channel=ch, control=c, value=v, time=0))
            ev = []   # (tick, 0 = off before 1 = a bend before 2 = on at the same tick, message)
            for n in m.notes:
                ev.append((n.step * TICK, 2, mido.Message("note_on", channel=ch, note=n.pitch, velocity=n.velocity)))
                ev.append(((n.step + n.steps) * TICK, 0, mido.Message("note_off", channel=ch, note=n.pitch)))
            for at, steps, semis, hold in m.slides:
                full = round(8191 * semis / BEND_RANGE)
                for k in range(BEND_EVERY, steps + 1, BEND_EVERY):
                    ev.append(((at + k) * TICK - (k == steps and not hold), 1,
                               mido.Message("pitchwheel", channel=ch, pitch=round(full * k / steps))))
                ev.append(((at + steps + hold) * TICK, 0 if hold else 1,
                           mido.Message("pitchwheel", channel=ch, pitch=0)))
            for at, steps in m.vibrato:
                ev.append((at * TICK, 1, mido.Message("control_change", channel=ch, control=1, value=VIBRATO)))
                ev.append(((at + steps) * TICK, 0, mido.Message("control_change", channel=ch, control=1, value=0)))
            now = 0
            for t, _, msg in sorted(ev, key=lambda e: (e[0], e[1])):
                tr.append(msg.copy(time=t - now))
                now = t
            mid.tracks.append(tr)
        mid.save(f"{stem}.mid")
        info = {"tempo": self.tempo, "meter": f"{self.meter[0]}/{self.meter[1]}", "source": self.source,
                "listen": self.listen,
                "members": {m.name: {"role": m.role, "sound": m.program if isinstance(m.program, str) else
                                     "kit" if m.kit else m.program, **({"pump": m.pump} if m.pump else {}),
                                     **({"gain": m.gain} if m.gain else {}), **({"pan": m.pan} if m.pan else {})}
                            for m in self.members},
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
