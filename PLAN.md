# Maestro plan

The one place that says where Maestro stands. Read it at the start of every Maestro session; tick tasks off in the
same commit that finishes them. Work goes one task at a time (DadCraft, Oct 23: "bucket by bucket, or task by task
as much as possible to keep token cost low").

**Next:** Bucket 2, task 2.6 (the theory exam).

## The goal (DadCraft, Oct 23)

Maestro is the musical brain behind Ouralia's generative music. It knows theory, composition, rhythm and many styles
(EDM, future bass, synthwave, chillwave, ambient, afrobeat, salsa, power rock, hip hop, rap, crunk, trap, ...).
The user builds a band: one genre for the full experience, or a blend of several, "kind of like how we can choose the
band members in Ouralia, except that everyone stays one beat, makes musical, melodic, rhythmic sense and still
embodies what each part is supposed to be even if they're from different styles."

**The core decision Maestro makes:** given the shared beat, the chords and where we are in the song, what does this
band member play, the way its style plays it?

## Decisions (each confirmed by DadCraft, Oct 23)

1. **Grow it from `dcs_composer`** (Ouralia's C composer: chords, sections, motifs, rule-made grooves). It already is
   the shared conductor; Maestro adds style. No second conductor.
2. **Decisions, not audio.** Maestro decides notes; Ouralia's Pd makes the sound.
3. **Each member has a style (how it plays) and a sound (what it plays on).** Picking a style sets its usual sound;
   the sound can be swapped on its own ("salsa horns but as a NES chiptune lead").
4. **Styles blend.** A member can be one style or a mix; "full one genre" is 100% of one.
5. **Knowledge first, app last.** Maestro learns theory and styles on the PC before any Ouralia work. Each knowledge
   step is still checked by DadCraft's ears on short PC clips (only DadCraft judges sound).
6. **Rules stay as guardrails.** The model suggests, the theory rules check, on the PC and on the phone.
7. **Data must be openly licensed** (public domain, CC0, CC BY, ...), every set tagged with its license and credited
   in `CREDITS.md`. **The model that ships in Ouralia is trained only on data that allows commercial use** (NC
   conflicts with Ouralia's GPL), released as CC BY-SA 4.0. NC data (Ouralia won't be sold, so it's allowed) is for
   PC-side work only: experiments, research, the style judge; models trained with it stay on the PC, under
   CC BY-NC-SA 4.0. Never train on Lakh-style fan MIDI of copyrighted songs, or use weights trained on it (ideas only).
   Music made by other AI models is ideas only too (DadCraft, Oct 23: "lets stay legally safe").
10. **Licenses:** code GPL-3.0-or-later (like Ouralia); docs and the style book CC BY-SA 4.0 (README "License").
8. **The phone version is small** (target: tens of MB, around MIDI-GPT's ~20M parameters), shrunk from the PC model.
9. **Free to drift, always making sense.** Maestro is never locked to fixed patterns: styles are written as
   tendencies and ranges, the model makes fresh choices each bar, and the rules only rule out what doesn't fit,
   never say what to play. Compositions evolve over a long play (key, energy, density, how strongly each style
   shows, motifs that develop). **No style trait is ever a lock** (DadCraft, Oct 23): the drafts are starting
   points, and an unexpected mix can work (something bright and happy over trap has, for him). **No two plays are
   alike:** turn Ouralia off and on with the same settings and the evolution is a new one. The same key and scale
   share notes, but the music is never identical run to run (a fresh random seed each play; no replaying a stored
   path). Measured before DadCraft listens: staleness within a play (how often bars and phrases repeat over ~20
   minutes) and sameness between plays (two runs, same settings).
11. **The band grows past today's four members** (drums, bass, pad, melody, plus the arp). The first styles need
    more roles, planned from the style book on: **rhythm guitar** (power rock), **keys** (salsa's montuno piano),
    **horns** (salsa) and **percussion** (congas, timbales, cowbell, clave; its own member, apart from the kit).
    Ouralia gets a sound for each in bucket 6.
12. **Ouralia goes its own way until Maestro is ready** (DadCraft, Oct 23). Ouralia keeps developing on its own;
    Maestro never changes it in buckets 2–5. Integration happens on a separate Ouralia + Maestro dev path that
    DadCraft tests privately or with beta testers, and it goes into Ouralia proper only when he deems it ready.
    So Maestro follows a moving `dcs_composer`: the sync check and the parity test (bucket 2) catch every change.
13. **Every note lands on point on the grid** (DadCraft, Oct 23). The band members are machines, not human
    players: nothing early, late or out of sync, no member ahead or behind the beat, no random looseness. Swing is a
    choice of grid point (the off-beat on a later step), never an offset between steps. Human-played data is
    rounded to the grid. **In reserve** (DadCraft, Oct 23), if the band sounds too robotic: the shared pocket from
    commit `56888cc` (`rhythm.py`): one small timing draw per step that every member shares, so the band moves
    together and stays in sync, held under a ms limit. Only DadCraft brings it back, after hearing clips.

## How each bucket runs

Plan (presented to DadCraft and approved) → tasks → checkpoint (DadCraft reviews the output). Task lists for later
buckets are drafts: refine them in that bucket's plan step. Key decisions get checked with DadCraft explicitly, and
added to the list above.

## Buckets

### 1. Groundwork — DONE
Plan approved Oct 23.
- [x] 1.1 Read how `dcs_composer` (Ouralia `dcs/src/dcs_composer.c`) represents key, scale, chords, sections,
      parts and timing, and where its randomness comes from (how it seeds, whether two plays can repeat). Write what
      exists into `docs/format.md` ("Today in Ouralia").
- [x] 1.2 Data audit into `docs/data.md`: every candidate set with license, NC/commercial-safe tag, size, format and
      the styles and members it covers; mark the gaps. Start from `docs/research.md` and `docs/music-info.md`.
      Start `CREDITS.md` with the attribution each chosen set requires.
- [x] 1.3 Check MidiTok (license, tokens, fit with 1.1) and write Maestro's format into `docs/format.md`: one shared
      timeline (tempo, meter, key, chord, section, energy), one part per member, controls per member (style vector,
      density, register...), sound kept separate.
- [x] 1.4 With DadCraft: pick the first 3–4 far-apart styles, from what the data covers. Picked: trap,
      synthwave, salsa, power rock.
- [x] Checkpoint 1: DadCraft reads the summary of `data.md` and `format.md`.

### 2. Theory core
A tested PC library: keys, chords, voice leading, rhythm, form. Grown from `dcs_composer` (decision 1).
- [x] 2.0 Plan approved Oct 23. **Language:** Python 3.12 (buckets 4–5 are Python; Ouralia's tests already drive
      the C composer from Python via `tools/pdtest`); the guardrail rules get a C port in 6.2, checked against the
      same test cases. Deps: pytest, mido (MIT); no music21. **Layout:** `pyproject.toml`; `maestro/`
      (`data/composer.json`: the composer's tables with the Ouralia commit they came from; `rng.py`: seeded
      randomness incl. the composer's LCG; `port.py`: today's composer; `theory/` `pitch` `chords` `voicing`
      `rhythm` `form`; `explain.py`); `tests/` (unit, `exam/`, `parity/`); `tools/` (`sync_check.py`, `drift.py`).
      Each rule module has a **check** (rules out what doesn't fit, with the reason) and a **choose** (picks among
      what's left, seeded): rules never say what to play (decision 9). **In step with C:** `sync_check.py` diffs
      `composer.json` against `dcs_composer.c` at Ouralia's current commit (start of each bucket, and whenever
      Ouralia's composer changes: decision 12); the **parity test** runs `port.py` and the real C composer (through
      Ouralia's test engine, read-only, its built lib) on the same seeds and needs the same chords and sections.
      Maestro's additions sit on top and can be switched off, so today's composer stays a mode to compare against.
      Changes Maestro would want in C are listed in `docs/format.md` for bucket 6.
- [x] 2.1 Skeleton and port: the package and tests, `composer.json` and the sync check, today's composer in Python
      (chords, cadences, phrase variation, sections and their memory, voicing, bass) passing the parity test.
- [x] 2.2 Keys, scales, chords and their functions: more scales (Phrygian, harmonic minor...), diminished,
      sevenths, borrowed and secondary chords, names and roman numerals, function (home, away, tension); what the
      four styles need (trap's dark minor, synthwave's borrowed chords, salsa's ii–V and montuno, rock's power
      chords and bVII).
- [x] 2.3 Voice leading: smooth moves, a range per member (new roles too, decision 11), the melody on top
      (`docs/taste.md`); parallels and the like as tendencies a style sets, not bans.
- [x] 2.4 Rhythm and meter: the beat grid (24 steps, was 12), meters past 4/4, half-time, clave, swing and feel per member.
- [x] 2.5 Form, sections and energy; how a long play evolves over ~20 minutes (energy arc, key changes, motifs that
      develop: decision 9).
- [ ] 2.6 A theory exam (our own, after MusicTheoryBench, no copied questions) with a score, and choices explained
      in plain words.
- [ ] 2.7 The two drift measures (decision 9): staleness within a play, sameness between plays, with targets.
- [ ] Checkpoint 2: DadCraft spot-checks the explained choices.

### 3. Style book (draft)
For each chosen style, how each member plays it, written from sources.
- [ ] 3.0 Plan approved (incl. what a style entry holds: tempo, swing, grid, chord vocabulary, register, default
      sound, all as tendencies and ranges with many variants, never a few fixed patterns: decision 9). Styles with no
      open data for a member (`docs/data.md` "Coverage and gaps") get that member's theory written out in full,
      since practice MIDI made from it is their main training data (DadCraft, Oct 23; the method and
      examples: `docs/data.md` "Filling the gaps with theory"). Each style's entry covers every role it uses,
      the new ones too (decision 11). DadCraft's taste notes (`docs/taste.md`, from his production logs) are a
      source for synthwave and the blends, and for checks before he listens. Check open textbooks as
      sources (e.g. Open Music Theory, license to check).
- [ ] 3.1 A PC clip player, so DadCraft can hear MIDI clips.
- [ ] 3.2 The drummer, starting from the Groove MIDI Dataset (CC BY 4.0).
- [ ] 3.3 One task per style: 3.3a trap, 3.3b synthwave, 3.3c salsa, 3.3d power rock.
- [ ] 3.4 The style judge (CLaMP 3, license checked) scores the clips first.
- [ ] 3.5 Layering (arrangement): which members play when. Members join one after another along a build and drop
      out as it eases (after Ouralia's Calm builds: pad, room notes, chimes, then harmony and reverb, each joining
      further along the rise; `docs/format.md`), and sections thin or fill the band. Each style's entry says who
      comes in first and who sits out (trap might drop its drums for a breakdown), as tendencies, never a fixed
      order (decision 9). Driven by `form.py`'s energy, with the check and choose like the other theory modules.
      In bucket 6 it becomes the way Calm builds and Maestro's arc stop stacking (DadCraft, Oct 23).
- [ ] Checkpoint 3: each member in each style, by ear; plus a long clip and two plays of the same settings, with the
      drift measures passed first. Ask DadCraft whether the on-grid band sounds too robotic; if so, the reserve
      pocket (decision 13) can be played to him next to the on-grid version. Also for his ear, from 2.5: the
      semitone key lift, how sections growing heavier comes across, and the layering (3.5).

### 4. Training data (draft)
- [ ] 4.0 Plan approved.
- [ ] 4.1 Download the clean sets, each tagged with its license.
- [ ] 4.2 Practice MIDI made from the style book, labeled.
- [ ] 4.3 Open audio to MIDI: stems, Basic Pitch, Beat This! on CC0 modern tracks.
- [ ] 4.4 Label (style, member, attributes), tokenize; commercial-safe and NC kept apart.
- [ ] Checkpoint 4: counts, and random samples by ear.

### 5. The model (draft)
Trained on this PC (RTX 2070, 8 GB).
- [ ] 5.0 Plan approved.
- [ ] 5.1 A small per-member model with controls (MIDI-GPT style); each member written seeing the others.
- [ ] 5.2 Compare a GETMusic-style model; keep the better one.
- [ ] 5.3 Style dropout for the "how much style" knob; style blends.
- [ ] 5.4 Learn broadly, then specialize per style; improve against the judge (NotaGen's CLaMP-DPO idea).
- [ ] 5.5 The drift measures on the model: within a play and between plays; check it doesn't copy its training data.
- [ ] Checkpoint 5: its parts next to the rule ones, by ear (can DadCraft tell which is which?); long plays.

### 6. Into Ouralia (draft)
- [ ] 6.0 Plan approved (follows Ouralia's CLAUDE.md). The separate dev path (decision 12): e.g. a long-lived
      Ouralia branch kept up to date with main, and a beta build that installs beside the release; to settle here.
      The C side gets its tables from a header generated from `composer.json` (one source).
- [ ] 6.1 Shrink the model for the phone; measure CPU and battery.
- [ ] 6.2 `dcs_composer` gains a style and a sound per member, swappable; rules as guardrails; the new roles
      (decision 11) get members and kits in Ouralia.
- [ ] 6.3 The drift measures on the phone (fresh seed each play; the patch's Pd `[random]`s and `expr random` are
      unseeded today, so they repeat after each app start: `docs/format.md`).
- [ ] Checkpoint 6: trap drums with a synthwave bassist, on the phone (beta build); off and on again gives a new
      evolution.
- [ ] 6.4 DadCraft (and beta testers) play the beta; it goes into Ouralia proper only when DadCraft deems it ready.

## Verdicts and notes
- Oct 23: research rounds 1 and 2 done (`docs/research.md`).
- Oct 23: decision 9 added (DadCraft: compositions evolve as they go on, and never the same evolution from play to
  play; same key and scale share notes, but never identical run to run).
- Oct 23: decision 7 refined and 10 added (DadCraft agreed): the phone model uses commercial-safe data only; code
  GPLv3+, docs CC BY-SA 4.0.
- Oct 23: 1.1 done (`docs/format.md` "Today in Ouralia"). The composer seeds from the clock (a new piece each
  start); the rest of the patch's randomness is unseeded and repeats per app start, to fix in bucket 6.
- Oct 23: 1.2 done (`docs/data.md`, `CREDITS.md`). Drums are covered across many styles (GMD, E-GMD); bass, pad and
  melody have no open data in any modern style, so the style book and transcribed open audio fill them. Two
  questions for DadCraft in `data.md` (synthetic AI music as data; programmatic drum loops).
- Oct 23: DadCraft's data answers: AI-made music is ideas only (added to decision 7); the WaivOps drum loops are in;
  the gap styles get their own theory per member in the style book, which drives their practice MIDI (3.0, 4.2).
- Oct 23: 1.3 done (`docs/format.md` "Maestro's format"). MidiTok is MIT; its MMM layout is the token base. A song
  is a MIDI file plus a JSON beside it (timeline, member controls, sound, license, seed); pitches shifted to the key
  for tokens; a 12-step beat grid (16ths and triplets); sound never in the tokens. For DadCraft at checkpoint 1.
- Oct 23: 1.4 done. DadCraft picked the first four styles: **trap** (half-time, triplet hat rolls, 808 bass; HH-TRP
  loops, FMA hip hop), **synthwave** (straight 8ths, arps, pads; RTRO-DRM, FMA electronic), **salsa** (clave,
  tumbao, montuno; GMD latin drums, leans most on the style book) and **power rock** (human feel; GMD rock, FMA rock).
  They differ in grid (triplet, straight, clave), feel (programmed vs human) and harmony. Ambient was the other
  candidate for the fourth slot; DadCraft chose power rock.
- Oct 23: checkpoint 1 passed; bucket 1 done. DadCraft's verdicts: (1) bass, pad and melody learn from the style
  book's practice MIDI plus transcribed open audio, as planned (recording our own parts was offered as a third
  source and declined for now; revisit if checkpoint 3 clips sound stiff); (2) plan the new roles now (decision 11);
  (3) the format stands as written.
- Oct 23: DadCraft shared four production logs (synthwave covers of game music, made with Suno) and his Suno
  Knowledge Base. Their musical lessons are in `docs/taste.md`, as ideas only (AI audio, copyrighted compositions):
  one style leads and others season it; far-apart styles stay in separate members; some styles fight some moods;
  the melody must stay on top. The logs themselves stay private, out of the repo.
- Oct 23: 2.0 done, bucket 2 plan approved. DadCraft: Python for the PC core with the guardrails ported to C in
  bucket 6 (yes); Maestro grows from `dcs_composer` through an exact port with a parity test (yes); rhythm and form
  split into 2.4 and 2.5 (yes). New decision 12: Ouralia keeps its own development; Maestro integrates on a separate
  dev path tested privately or with beta testers, released into Ouralia proper only when he's good with it.
- Oct 23: 2.1 done. `maestro/port.py` is today's `dcs_composer` choice for choice (chords, sections, melody,
  drums, walking notes, cells), its tables in `data/composer.json` from Ouralia `933148d`; the parity test (16
  scenarios, every scale, ~7,400 outputs) passes against the real C, and fails if any of three compiler-chosen
  draw orders is flipped (noted for bucket 6 in `docs/format.md`). `tools/sync_check.py` reports when the C moves.
- Oct 23: 2.2 done. `maestro/theory/pitch.py` (14 scales: the composer's 8 plus phrygian, locrian, harmonic and
  melodic minor, phrygian dominant, blues; keys spelled properly) and `theory/chords.py` (root, quality, colour and
  bass as in `docs/format.md`; diatonic, secondary, borrowed or chromatic; names, roman numerals that count from the
  tonic's major scale so bVII reads the same in every key; function home, away or tension with the reason; a
  vocabulary check that gives its reason and a seeded choose; `two_five` for salsa). Tests cover what the four styles
  need (phrygian bII and harmonic minor V, synthwave's bVI bVII iv, salsa's ii-V and secondary ii-Vs, rock's power
  chords and bVII).
- Oct 23: DadCraft approved both 2.2 choices: roman numerals count from the tonic's major scale (A minor reads i ii°
  bIII iv v bVI bVII; bVII the same in every key), and the functions (tension: V, vii°, secondaries, phrygian's bII;
  softer homes: vi, iii, the relative major; away: bVII and minor v).
- Oct 23: 2.3 done. `maestro/theory/voicing.py`: a range per pitched member in MIDI notes (bass C1-G3, guitar
  E2-E5, keys G2-E6, pad C3-C6, horns E3-C6, arp G3-G6, melody C4-C7), narrowed by the register control. The check
  rules out notes out of range or outside the chord, a needed tone missing (the perfect fifth goes first when there's
  no room; a rootless style leaves the root to the bass), notes not under the melody, and low intervals that turn to
  mud (the arranger's low-interval table). Smooth moves, leaps, parallel fifths and octaves, spread and a pull to the
  range's middle (so a long play can't drift off) are costs a style sets, negative when it likes them; the choose
  picks seeded among the smoothest few. First drafts: plain avoids parallels, synthwave glides as a block, power rock
  likes parallel fifths, salsa likes octaves (montuno) and plays rootless, trap barely minds. `check_band` checks the
  melody on top and mud across members; `explain` says each move in plain words. For DadCraft: the ranges and the
  style drafts.
- Oct 23: DadCraft approved both 2.3 choices: the member ranges, and the first style drafts (power rock's parallel
  fifths, synthwave's block glide, salsa's octaves and rootless keys, trap's wide pads, plain avoiding parallels).
- Oct 23: DadCraft moved the beat grid from 12 to 24 steps a beat, so trap's 32nd hat rolls land on it as well as
  triplets (`docs/format.md` updated).
- Oct 23: 2.4 done. `maestro/theory/rhythm.py`: the 24-step grid (20 ticks a step; today's `tick16` is every 6th),
  meters with their grouping (4/4, 3/4, 2/4, 5/4, 6/8, 12/8, 7/8 as 2+2+3, any other n/d), metric weight per step,
  the backbeat and the pulse (half-time puts trap's snare on 3; double-time), counting in players' words ("2 and",
  "1 trip"). The claves: son and rumba in 3-2 and 2-3, and the 6/8 bell; the check rules out a part that lines up
  with the other direction (crossed), while a part the same each bar (a tumbao) passes. The choose draws onsets
  seeded by a style's weights (which subdivisions it uses, how much it leans on the beat); trap rolls at 16ths,
  32nds and both triplets. Feel per member: swing, accents, pulse (first drafts had human timing too; see below).
  For DadCraft: the style drafts, and son 2-3 as salsa's default clave.
- Oct 23: DadCraft approved both 2.4 choices (the style drafts, son 2-3), then asked whether it would make a
  coherent song. Not yet: the drafts gave members human timing (rock's bass behind the beat, random looseness), each
  drawn on its own, so kick and bass could flam; and nothing checked the band as a whole. A first fix kept human
  timing inside ms limits; DadCraft set it straight: "nothing should ever be late ... none of our band members is
  human. all parts should land on point on the grid" (decision 13). Now in 2.4: no push, no looseness; swing is a
  number of grid steps; `check_band_rhythm` rules out any note between grid steps, members playing the same step
  apart (a swung part over a straight one), and any member crossing the timeline's clave, whatever its style.
  Every style draft passes. Rhythms that groove (repetition, variation) come in 2.5 and bucket 3.
- Oct 23: 2.5 done. `maestro/theory/form.py`: a play planned a section at a time (the room leans each one), over an
  energy arc of waves (3-7 minutes of build and release each, peaks 0.6-1.0, drawn fresh each play); a section's
  energy is the room plus the arc plus its kind's shift (the composer's), growing a little through it
  (`docs/taste.md`). Key changes at section starts: relative, parallel, a fifth, or a lift up a semitone or tone
  (on a Lift only), at least a few minutes apart, at most a few hops from home, home pulling harder the further away.
  Motifs in scale steps with grid lengths develop each statement (again, nudged, inverted, backwards, shorter,
  longer, twice as slow or fast; young ones stay close) and are reborn from their own opening after a while. Checks
  with reasons for sections, key changes and motifs; plain-word `explain_section`. A 20-minute plan per style passes
  every check; 30,000 motif statements break none. For DadCraft: the style drafts (trap stays in one dark key, full
  energy from the start; synthwave long swells and key lifts; salsa full from the start, relative and fifth moves;
  power rock shorter waves, key lifts), and a key lift up a semitone (the "truck driver" change) allowed at all.
- Oct 23: DadCraft on the 2.5 choices: (1) the style drafts are fine to test, but never hard locked: he has put
  something bright and happy over trap and it worked. So a style's modes are now what its key changes lean to
  (three times as often), never a ban; added to decision 9. (2) The semitone key lift: he judges it by ear, at the
  first clips. And "music gets heavier as zone progresses" was one S3&K zone, not a rule: how much a section grows
  is now a style setting (`docs/taste.md` corrected); he'll hear how it comes across.
- Oct 23: DadCraft pointed at Ouralia's **Calm builds** as maybe what "heavier as zone progresses" meant. Compared
  (`docs/format.md`): it is closer to Maestro's energy waves than to a section growing. Both swell over minutes; Calm
  builds is set off by the listener standing still in a calm room, with fixed timings (30 s wait, 180 rise, 60 hold,
  120 fall, 180 rest) and ends within 5 s when they move, and it builds by **layers joining** (pad, room notes, chimes,
  harmony and reverb) and levels lifted, not by changing notes. Maestro's waves run always, drawn fresh (3-7 minutes,
  peaks 0.6-1.0), and lean what every member plays; it has no layering yet (which members play when). The two would
  stack in bucket 6 (noted there).
- Oct 23: DadCraft: handle the borrowed chords now, so it isn't lost. The 2.2 chord vocabulary was a ban (a chord
  outside a style's list was ruled out); now it's a lean (decision 9): `choose_in_style` picks from the style's usual
  chords, and `outside`% of the time (5 by default) from beyond them, near chords (borrowed, secondary, other
  qualities and colours) four times as often as remote chromatic ones; `outside()` says why a chord is unusual.
- Oct 23: DadCraft: layering goes in the style book, so it gets done there: task 3.5 added. Checkpoint 3 also
  carries the 2.5 items he wants to hear (the semitone key lift, sections growing heavier).
