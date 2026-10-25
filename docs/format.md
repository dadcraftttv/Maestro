# Maestro's format

Two parts: what Ouralia has today (task 1.1), then Maestro's own format (task 1.3).

## Today in Ouralia

Read on Oct 23 from Ouralia's `dcs/src/dcs_composer.c` (a Pd external in C, 932 lines; its header comment is the
full reference), the patch builder `tools/patchgen/music.py` (`add_composer`) and `rhythm.py` (the tempo clock), and
libpd's `pure-data/src/x_misc.c` (`pdscenes`). The composer runs when Song Shape is "Evolving" (`music_var` 1);
"Steady" is the old pad (a chord near the room's brightness every 7 s, no memory).

### Key and scale
- **Key:** not in the composer. Everything it sends is in semitones from the key note; the patch adds the key
  (`mu_key_root`: key + 48, the octave from C3) and turns it into Hz (`mtof`). A key change sends `again` (the same
  chord resent, so it moves with the key).
- **Scale:** `scale <0-7>`: Major, Minor, Major pentatonic, Minor pentatonic, Dorian, Mixolydian, Lydian, Whole tone
  (`SCALE_IV`, the same list as the patch's). A new scale starts a new piece. Pentatonic scales take their chords
  from the full scale they come from (major pent. from Ionian, minor pent. from Aeolian); the melody stays
  pentatonic. Six chord "modes" (`t_mode`): degrees, semitones, the chords used (no diminished), and a 7×7 table of
  weights for moving from each chord to each other one, leaning on each mode's colour chord (Dorian IV,
  Mixolydian bVII, Lydian II).

### Chords
- A chord is a **scale degree** (0–6); triads stacked in thirds of the scale. Phrases of 4 chords (`PLEN`), each
  made by weighted moves and ending on a cadence; a phrase can be varied (a chord or two changed).
- **Colours** (`color 1`): now and then a seventh (in place of the doubled root), an added ninth, or sus4/sus2 that
  resolves to the plain chord on the next bar; how often depends on the section (`KIND_COLOR`).
- **Voicing:** pad of 4 notes (3 chord notes, root doubled an octave up), each chord voiced closest to the last;
  Calm spreads it open. The bass is the chord's root or the home note (`KIND_BASS`, percent per section).
- **Out (one list per chord):** anchor (the scale step that fits it best), bass (semitones 0–11), 4 pad notes
  (semitones from the key note, about −5..+28).

### Sections (form)
- Four kinds: **Home, Lift, Calm, Turn** (0–3). Home comes back between the others (70% after an away section);
  which away section leans on the room: energy and brightness → Lift, quiet → Calm, never the same journey twice in a
  row if it can help it. A section is 2 phrases (3 now and then, away from Home).
- **Memory:** each kind keeps its phrase, motif and patterns; when it comes back they return slightly changed. A new
  scale or `seed` forgets them all (a new piece, Home first).
- Per section: chord length (`KIND_SECS` 6.5 / 4.5 / 9 / 5.5 s, rounded to 1–4 bars; a cadence held a bar longer
  35% of the time), melody register (`KIND_REG`, scale steps), drum drive (`KIND_DRIVE`, Calm −0.25, Lift +0.15).
- **Out:** kind and melody register when a section starts (Java's `AudioService` shows it).
- No energy curve of its own beyond this: the room's `intensity` (energy) and brightness lean the choices; "The Band
  Plays" (`rhythm.py`, `BAND_*`) adds an 8-bar build-and-drop on the drum drive.
- **Calm builds** (outside the composer, in Java: `CalmBuild.java`, a Music switch, off by default): once the
  listener has stood still in a calm room for 30 s, a build rises over 180 s, holds 60, eases back over 120, then rests
  180 before the next; walking or a lively room ends it within 5 s. It builds by layers joining in turn (pad from the
  start, room notes from a quarter of the way, standing-still chimes from halfway, harmony and reverb from three
  quarters), each lifted up to +40% at the top. It changes the mix and the chime chance, not the composer's notes, so
  the port never sees it.

### Parts (members)
The band today is **melody** (chimes), **bass**, **pad** and **drums**, each with a kit (its sound) picked on its
own (`rhythm.py`: mel, bass, pad, drums). The composer gives each of them rules-made material:
- **Pad and bass:** the chord list above.
- **Melody** (`note <middle> <chord> <n>`, answered with a scale step): a motif of 3–6 notes per section, played in
  statements like a theme and variations (motif, again, answered, moved, upside down, backwards, cut short, carried
  on). A pause of 2.2 s ends a statement. With Melody rhythm on, a one-bar rhythm cell (`cell <drive> <style>`:
  straight, dotted, mixed), 16 note lengths in 16ths, one note changed per bar.
- **Drums** (`drums <drive> <break>`): 3 lanes (kick, snare, hat) × 16 velocities per bar, Euclidean spreads sized by
  the drive, snare on the backbeat with ghosts, open hats coded as velocity + 2.
- **Walking notes** (`arp <pace> <n>`): 8 scale steps above the chord root (rising, falling, broken, around the
  root...).
- Patterns keep most of the bar and change one thing each bar; every 4th bar is the section's own pattern again.
- There is **no style** anywhere: every part plays one way. That's what Maestro adds (decision 1).

### Timing
- **Meter:** 4/4 only, 16 sixteenths a bar (`tick16`, 0–15). Swing is applied in the drum engine (off-beat 16ths
  late), not in the composer.
- **Tempo:** from the patch's tempo clock, which follows the user's walking like a band follows its drummer (or a
  set BPM, `tempo_mode` 1); `tempo <bpm>` on every beat.
- **Bar:** the composer moves on `bar` (tick 0). If no bar comes (no clock) it keeps its own bar time from the
  tempo (a watchdog at 1.6 bars, then every bar).
- Chord changes and patterns are per bar; the melody is per note, asked for by the patch when a note is due.

### Randomness: can two plays repeat?
- **The composer:** its own generator (an LCG, `rnd`), seeded at creation from the clock:
  `time(0) * 2654435761 + n` (n counts composers made in this process). So each app start gives a new piece. `seed
  <n>` sets it exactly (only the tests send it, through `comp_seed`; the app never does). Two plays repeat only if
  started in the same second, or with the same `seed`.
- **The rest of the patch is not seeded:** its 60 Pd `[random]` objects take their seeds from a fixed sequence in
  Pd (`makeseed`, a constant start), and `expr`'s `random()` uses C `rand()` with no `srand`. So after a fresh app
  start these give the **same** sequence every time. Different input (the room, the walking, the timing) changes
  when they're asked, so the sound still varies. But with the same input the patch's own choices would repeat.
- **Java:** `Modulation`, `ParamStore`, `CallResponse` and `MotifMemory` use `new Random()`, different every run.
- **For decision 9** (no two plays alike): the composer already does it. The patch's `[random]`s and `expr random`
  would need a per-play seed (one `seed` message per object, from the start time) when Maestro reaches Ouralia
  (bucket 6). Noted for 6.3.

### What Maestro can build on (for 1.3)
- A shared timeline that already exists: tempo, bar/16th grid, key (outside), scale, chord (degree + voicing +
  colour), section kind, energy and brightness.
- Parts as scale steps or semitones from the key, a bar at a time (drums, walking notes, cell) or per note (melody).
- Missing: meter other than 4/4, triplet/swing grids in the composer, a style per part, a part's register and
  density as controls (today they come from the section and the drive).

## Maestro's format

Written Oct 23 (task 1.3). One shared timeline for the whole band, one part per member, controls per member, and the
sound kept out of it. It grows from the composer's own picture (above), so `dcs_composer` can speak it in bucket 6.

### MidiTok (checked Oct 23)
- **What:** Python library that turns MIDI into tokens for models and back (github.com/Natooz/MidiTok). v3.1.0,
  Sep 30 2026, actively kept up. Python ≥3.10; needs numpy, symusic (MIT), Hugging Face `tokenizers` and
  `huggingface_hub`.
- **License:** MIT (symusic too). Works with our GPL-3.0-or-later code; keep its notice when we ship it.
- **Tokenizers:** REMI, TSD, MIDI-Like, Structured, CPWord, Octuple, MuMIDI, PerTok, BEAT, and **MMM**: the
  Multitrack Music Machine layout that MIDI-GPT uses (research.md). In MMM each track is its own run of tokens and
  the runs are joined; `Bar_Fill` marks bars to rewrite, so one member (or a few bars of it) can be redone with the
  others kept.
- **Built-in controls** ("attribute controls", per track or per bar): note density, polyphony, note length, pitch
  classes, repetition. More can be added (`add_attribute_control`), and new tokens too (`add_to_vocab`).
- **Also:** tempo and time-signature tokens, a beat grid set per range (`beat_res`, so 16ths and triplets), drums
  as their own track, BPE to shorten sequences.
- **Where it doesn't fit 1.1, and what we do:**
  - Its chord tokens are *guessed* from the notes. Ours are *given* by the composer (degree, colour), so chords are
    our own timeline tokens.
  - MMM only reads tempo and key back from the first track. The timeline is its own run, written once, not per
    track (research.md said the same).
  - No style, section, energy or register: our own tokens on top.
  - Pitches are absolute MIDI notes; the composer thinks from the key note. We shift every piece to the key before
    tokenizing (below).
- **Verdict:** use MidiTok's MMM as the base for tokens (task 4.4), with our timeline and controls added. Our own
  file format (below) stays the source of truth, so we aren't tied to MidiTok.

### The song file
One clip or song = a standard **MIDI file** (the notes, tempo, meter; one track per member, the track named after
its member) plus a **JSON file** beside it with everything MIDI can't hold: the timeline, the members' controls,
where it came from and its license. MIDI keeps the clips playable in any player (task 2.7); the JSON keeps the
labels readable. Ticks: 480 a beat. A member that slides (trap's 808, task 3.4a) carries pitch bends: its track
opens by setting the bend range to an octave (RPN 0), each slide bends over its last 8th to the next note's pitch,
and the bend is back at rest when the next note starts (a glide in Ouralia, bucket 6). A member's sound in the JSON
may name one of Maestro's own (`"808"`, `"808 kit"`): the player renders that track itself (`synth.py`).

```json
{
  "source": {"set": "groove-midi", "license": "CC BY 4.0", "commercial_safe": true, "seed": 81723},
  "timeline": [
    {"bar": 0, "tempo": 92, "meter": "4/4", "key": 9, "scale": "minor",
     "chord": {"root": 0, "quality": "min", "color": null, "bass": 0},
     "section": {"kind": "home", "bar": 0, "phrase_bar": 0, "cadence": false},
     "energy": 0.4, "brightness": 0.5}
  ],
  "members": {
    "drums": {"role": "drums", "style": {"trap": 1.0}, "strength": 0.9, "density": 0.6, "swing": 0.1},
    "bass":  {"role": "bass", "style": {"synthwave": 0.7, "trap": 0.3}, "strength": 0.7,
              "density": 0.4, "register": [28, 48]}
  },
  "sound": {"drums": "808", "bass": "analog-saw"}
}
```

### The timeline (shared by the whole band)
A list of changes, each from a bar (or a beat in that bar); anything not given carries on from before.
- **Tempo:** BPM. In data, from the file; in Ouralia, from the walking clock as today.
- **Meter:** `4/4` first; `3/4`, `6/8`, `12/8` allowed (salsa and afrobeat lean on 12/8 feels). Today's composer is
  4/4 only.
- **Grid:** 24 steps a beat (a quarter note; 20 MIDI ticks a step), so 16ths (every 6th step), 32nds (every 3rd),
  8th and 16th triplets (every 8th and 4th) and 32nd triplets (every 2nd) all land on it; today's `tick16` is steps
  0, 6, 12 ... of the bar. It was 12 until task 2.4, when DadCraft chose 24 so trap's 32nd hat rolls aren't rounded
  into triplets (Oct 23). Notes in the MIDI keep their exact ticks; the grid is what tokens round to.
- **Rhythm** (task 2.4, `maestro/theory/rhythm.py`): meters with their beat grouping (7/8 as 2+2+3), metric weight
  per step, the backbeat, half-time and double-time as a pulse, and the claves (son and rumba in 3-2 and 2-3, the 6/8
  bell); a clave on the timeline (`"clave": "son_2-3"`) binds every member, whatever its style, and a part
  crossing it is ruled out.
- **Key:** root 0–11 (C = 0) and **scale**: the composer's 8 (major, minor, major and minor pentatonic, dorian,
  mixolydian, lydian, whole tone), plus phrygian, locrian, harmonic and melodic minor, phrygian dominant and blues
  (task 2.2, `maestro/theory/pitch.py`).
- **Chord:** **root** in semitones from the key note, **quality** (maj, min, dim, aug, sus2, sus4, power), **colour**
  (7, maj7, add9, 9 ... or none) and **bass** note (semitones from the key; an inversion or pedal when it isn't the
  root). The scale degree follows from the root when the chord is in the scale; a root outside it is a borrowed
  chord, which real music has and the composer doesn't make yet.
- **Section:** **kind** (home, lift, calm, turn: the composer's four; data gets the closest one: verse ≈ home,
  chorus or drop ≈ lift, breakdown ≈ calm, bridge ≈ turn), the bar within the section and within the 4-bar phrase,
  and whether this bar is a cadence.
- **Energy** 0–1 (the room's intensity today), and **brightness** 0–1 (the room). Both lean every member.
- **Form** (task 2.5, `maestro/theory/form.py`): a play is planned a section at a time as it goes, so the room keeps
  leaning it. Under the room's energy runs an arc of waves (each a few minutes of build and release, drawn fresh each
  play); a section's energy is the room plus the arc (scaled by the style's depth) plus its kind's shift (the
  composer's `KIND_DRIVE`), and grows a little through the section. The key may move at a section start (relative,
  parallel, a fifth, or a lift up a semitone or tone, which only a Lift takes), never sooner than the style's gap,
  never more hops from home than it allows, home pulling harder the further away it is. Motifs are scale steps with
  grid lengths, so they carry across key changes; each statement develops the last (again, a note moved, inverted,
  backwards, shorter, longer, twice as slow or fast), young motifs staying closer, and after the style's `life` a
  motif is reborn from its own opening. The checks rule out a play not opening at Home, an away section twice
  running, a Lift that doesn't lift, a Calm above 0.65, a rise over 0.35 into anything but a Lift, motifs off the
  grid, wider than an octave, leaping past a fifth, stale (3 the same running) or no longer related to what they grew
  from. The composer resets its memory on a scale change; Maestro keeps its motifs through key changes.

### The members (one part each)
- **Role:** what the member is for: drums, bass, pad (chords), melody (lead), arp (walking notes, today's `arp`),
  and, for the first styles (PLAN.md decision 11): **guitar** (rhythm: power chords, riffs), **keys** (comping,
  salsa's montuno), **horns** (a section: lines and stabs in two or three voices) and **percussion** (hand
  percussion as its own member: congas, bongos, timbales, cowbell, clave, shaker; General MIDI percussion notes,
  apart from the drum kit). A role is the job, not the sound.
- **Notes:** start (ticks), length, pitch, velocity.
  - Pitch: MIDI note numbers in the file; for tokens, shifted so the key note is C (pitch − key root), the way the
    composer sends semitones from the key note and the patch adds the key back. A part learned in one key fits all
    twelve.
  - Drums: one track with General MIDI drum notes, grouped in lanes: kick, snare, clap, closed hat, open hat, toms,
    crash/ride, percussion. Today's three lanes are kick, snare and hat (open hat as velocity + 2).
- **Controls** (per member, per section or per bar; each optional, so a member can be left free):
  - **style:** weights over styles, adding to 1 (`{"trap": 1.0}` is full trap; a blend is decision 4).
  - **strength:** how strongly the style shows, 0–1 (0 = plain, the theory rules alone; the dropout knob, 5.3).
  - **density:** notes a bar, 0–1 (MidiTok's density control, binned).
  - **register:** lowest and highest note it should use.
  - **polyphony** (pad, keys: notes at once), **note length**, **feel**: swing as a grid choice (the steps
    the off-beat moves to a later step: for 8ths 4 is triplet swing, 6 hard 75:25; for 16ths 2 is triplet swing),
    accents, and pulse (full, half, double). Each style has a feel per member (`rhythm.py` `FEEL`), so trap's
    half-time drums and a straight synthwave bass can share one beat. **Every generated note lands on point on a
    grid step** (PLAN.md decision 13): no member plays ahead or behind, nothing is loosened at random, and members
    playing the same step land on it together (a swung part over a straight one is ruled out). Human-played data
    (the Groove MIDI drums) gets its notes rounded to the grid when it's tokenized, so the model never learns to
    drift. A shared band pocket (one small timing draw per step for the whole band) is kept in reserve in commit
    `56888cc`, in case checkpoint 3 sounds too robotic.
  - **repetition:** how much it repeats the bars before versus moves on (MidiTok's repetition control); with the
    seed it is how decision 9 gets measured and steered.
- **Sound is not here.** Each member's sound is a name in `sound` (an Ouralia kit), never in the notes or tokens,
  so the model never learns it and it can be swapped freely (decision 3). A style's usual sound lives in its style
  book entry (bucket 3). From data, a MIDI program only tells us the role (GM 32–39 → bass and so on).

### Tokens (for the model, bucket 4)
MidiTok MMM, laid out as: the timeline run (per bar: tempo, meter, key, scale, chord, section, energy), then one
run per member, each opened with its role and controls (`Style_trap_10`, `Strength_9`, `Density_6`, `Register_..`,
weights and levels binned), then its bars of notes on the 24-step grid. Drums last. `Bar_Fill` asks the model to
write one member's bars seeing the timeline and the other members, which is how each member is "written seeing the
others" (5.1). Commercial-safe and NC data are tokenized into separate sets (decision 7).

### Seeds and drift (decision 9)
Every generated play stores its **seed** (in `source`). Tests and the drift measures replay a seed; the app never
does: each play draws a fresh one, as the composer already does. The measures and their targets: `maestro/drift.py`.

### From today's composer to this format
| `dcs_composer` today | Maestro's format |
|---|---|
| key outside it (`mu_key_root`) | timeline key |
| `scale <0-7>` | timeline scale (same 8, more later) |
| chord degree + colour + voicing | chord root/quality/colour/bass; the voicing is the pad member's notes |
| bass list (root or home note) | bass member's notes |
| section kind + `KIND_*` tables | section kind; the tables become style and control defaults |
| drive, `intensity` | energy, and each member's density |
| `KIND_REG` (melody register) | melody member's register control |
| melody motif statements, `cell` | melody member's notes (motif logic stays in the theory core, bucket 2) |
| `drums` 3 lanes × 16 | drums member, more lanes, 24-step grid |
| `tick16`, 4/4 | 24-step grid; 4/4 plus other meters |
| swing in the drum engine | swing/feel control per member |
| `rnd` seeded from the clock | seed stored per play |
| no style | style, strength per member |

## The style book (task 3.1, Oct 24)
One JSON file a style in `maestro/data/styles/` (`trap.json`, ...), CC BY-SA 4.0 with its sources cited, and
`book.json` listing the styles in order (plain first: the theory core's defaults, the baseline). `maestro/stylebook.py`
reads and checks every file when Maestro starts; the theory modules build their tables from it (`VOCAB`, `LEADING`,
`RHYTHM`, `FEEL`, `FORM`, the sketch's tempo, sounds and drum guide). A file names only what differs from the theory
core's defaults: a field left out keeps its default (the defaults are the dataclasses in the theory modules). Any
part may carry a `"why"` in plain words.

| Part | Holds | Built into |
|---|---|---|
| `style`, `license`, `sources`, `why` | the file's name, CC BY-SA 4.0, where it comes from, what it is | (checked) |
| `time.tempo` | the felt tempo, BPM (required) | the sketch's tempo |
| `time.rhythm` | grid weights, the clave | `rhythm.Rhythm` |
| `time.feel` | `"*"` for every member, then a role's own | `rhythm.Feel` |
| `harmony.vocabulary` | kinds, qualities, colours, borrowed scales, how often it steps out | `chords.Vocabulary` |
| `harmony.leading` | voice-leading costs and rules | `voicing.Leading` |
| `form` | phrases, waves, key changes, motif life | `form.Form` |
| `harmony.progressions` | `families` (each a loop in roman numerals with its bar lines, `"i iv \| V7 iv"`, and a weight), `variants` (weights: again, swap, colour, approach, turnaround), `stay`, `cadence` (% of phrases made to land home, 100 by default; trap 25), `still` (a loop of one chord allowed) | `flow.Flow` (3.2, 3.4a) |
| `members.<role>` | `sound` (GM program, or one of Maestro's own: `"808"`, `"808 kit"`, played by `synth.py`), `level` (velocity), for drums `kicks` and `hats` | the sketch |
| `members.drums.patterns` | a programmed drummer (trap) instead of GMD's: `kicks` (each `bars`: two lists of a bar's 16ths), `hats` (each `bars`: two strings of eight 8ths, `-` `x` `xx` `o` and the rolls `3` `4` `6`), each with `weight` and `when` (low, high, any); `stay`, `vary` (% of rounds the kick changes a note), `drop` (% of section ends where the kick, clap and 808 drop out), `intro` (bars of hats alone at the start); the fills: `roll` (% of section ends with a snare roll), `cascade` (% of 8-bar runs, or of section ends without a roll, ending in the falling staccato cascade), `cymbals` (% of sections entered with a reversed cymbal and a crash), `riser` (% of section ends with a riser over two bars) | `drums.Programmed` (3.4a) |
| `members.melody.shape` | `"phrase"` (the default: shaped over the phrase) or `"loop"` with `loop`: `bars` (weights for 1 or 2), `cells` (weights for a beat's rhythm: `q`, `8 8`, `8 r`, `r 8`, `16 16 8`, `8 16 16`, `t t t`, `r`), `stay`, `vary` | `flow.LoopFlow` (3.4a) |
| `members.bass` (an 808) | `with`: `"pattern"` (the default) or `"kick"`: no pattern, a note on each of the drummer's kicks and each chord change, held to the next; `tones` (weights: root, third, fifth, octave; a chord's first note is its root), `slides` (% of the notes sliding into the next over their last 8th, a pitch bend in the clip) | `flow.bass_808` (3.4a) |
| `members.melody.develop` | weights added to the motif's development (again, nudge, invert, back, shorter, longer, augment, diminish, triplet: two notes filling a beat played as three 8th triplets) | `form.Theme` (3.4a) |
| `members.bass.patterns` | pattern families: notes as `[at, length, tone, which]` in 16ths (length `null`: held to the next note; tone root, third, fifth or octave; which `now` or `ahead`, the chord at the next half bar), `bars`, `weight`; `variants` (again, drop, approach, octave) | `flow.Pattern` (3.2) |
| `members.drums` | `grooves` (the GMD styles it draws on, with weights), `time` (weights for its timekeeping, `"hat 8th"`, `"ride quarter"`, `"crash 8th"`, leaning GMD's own), `busy` (% of GMD's small-hit odds played), `fills` (% of phrases ending in a fill), `rolls` (% ending in a hat roll instead), `backbeat` (`"fixed"`: only grooves with the plain backbeat, no extra snares; trap's snare on 3), `turns` (% of beats the hats change rate, at energy 0.5) with `turn rates` (weights: 8th_triplet, 16th, 16th_triplet, 32nd, 32nd_triplet); no `grooves`: no kit | `drums.Drummer` (3.3, 3.4a) |
| `members.percussion.parts` | each part's pattern families: hits as `[16th, voice, velocity]` over `bars` 1 or 2 (two-bar ones in the clave's cycle), `weight`, `when` (low, high or any energy); `variants` (again, drop); `abanico` (% of section ends) | `percussion.Part` (3.3) |

Roles are the band's members (decision 11). The loader says where a file goes wrong (`trap: form.moves: unknown key
move 'leap'`): unknown parts and fields, the wrong kind of value, a missing source or the wrong license, and any name
the theory doesn't know (a quality, a scale, a clave, a key move). Lists become tuples or sets, and phrase counts
become whole numbers, as the theory expects. Bucket 3's later tasks add parts (fit and form in 3.4), each with its
check. A style that names no progressions or bass patterns plays `theory/flow.py`'s defaults (common loops and
schemas; roots, root and fifth, root eighths); the families that don't fit a key or the style's vocabulary are
ruled out, with the reason.

**The drummer's numbers** (task 3.3) are in `maestro/data/grooves.json`, made by `tools/groove_stats.py` from the
Groove MIDI Dataset (CC BY 4.0, downloaded into `private/gmd`): our own counts, never the performances. For each GMD
style (rock, hip hop, pop, dance; straight takes only, each lined up on its backbeat, rounded to 16ths, up to 32 bars
a take): its common backbones (kick and accented snare on the 8ths) with their shares, how often a bar keeps the one
before, the odds of every other hit on each 16th, its timekeeping, the mean velocity on each 16th, and its fills
(length, pace, drums, how often the toms go down). Run the tool again after changing it; the style files only point
at it.

## The port and the C (task 2.1, Oct 23)
`maestro/port.py` is today's `dcs_composer` in Python, choice for choice: the same seed and messages give the same
outputs (chords, sections, melody statements, drums, walking notes, cells), checked by the parity test
(`tests/parity`), which drives the real C composer through Ouralia's test engine. Its tables live in
`maestro/data/composer.json` with the Ouralia commit they came from (`933148d`); `tools/sync_check.py` says when the
C file has moved on. To match bit for bit, the port rounds float maths to 32 bits at each step and keeps Pd's clock
(the bar watch fires on DSP ticks, in Pd's own time units).

### Changes Maestro would want in C (for bucket 6)
- **Calm builds and Maestro's arc would stack.** Both swell over minutes; run together, a calm room would get two
  builds at once. Bucket 6 picks one: the listener's stillness feeding Maestro's arc (a longer, deeper wave while
  they stand still) is the natural fit, with the layers becoming members joining (Maestro's arrangement).
- **Three draws in an unspecified order.** Three expressions call `rnd()` twice where C leaves the order to the
  compiler: `nudge_motif` (`m->iv[1 + rnd()] += rnd() ? 1 : -1`), `vary_drums` (`(rnd() ? 1 : -1) * (1 + rnd())`)
  and `new_statement` (the same shape). GCC draws the sign first in the last two and the right side first in the
  first; the port does the same, and the parity test fails if either order is flipped. Clang (the Android NDK's
  compiler) may choose otherwise, so the phone and the desktop could already differ. Split each into two statements.
