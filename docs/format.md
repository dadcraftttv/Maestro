# Maestro's format

Two parts: what Ouralia has today (task 1.1), then Maestro's own format (task 1.3, to come).

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
