# Maestro plan

The one place that says where Maestro stands. Read it at the start of every Maestro session; tick tasks off in the
same commit that finishes them. Work goes one task at a time (DadCraft, Oct 23: "bucket by bucket, or task by task
as much as possible to keep token cost low").

**Next:** Bucket 2, task 2.0 (the plan).

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
   tendencies and ranges, the model makes fresh choices each bar, and the rules only rule out what doesn't fit, never
   say what to play. Compositions evolve over a long play (key, energy, density, how strongly each style shows,
   motifs that develop). **No two plays are alike:** turn Ouralia off and on with the same settings and the
   evolution is a new one. The same key and scale share notes, but the music is never identical run to run (a fresh
   random seed each play; no replaying a stored path). Measured before DadCraft listens: staleness within a play
   (how often bars and phrases repeat over ~20 minutes) and sameness between plays (two runs, same settings).
11. **The band grows past today's four members** (drums, bass, pad, melody, plus the arp). The first styles need
    more roles, planned from the style book on: **rhythm guitar** (power rock), **keys** (salsa's montuno piano),
    **horns** (salsa) and **percussion** (congas, timbales, cowbell, clave; its own member, apart from the kit).
    Ouralia gets a sound for each in bucket 6.

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

### 2. Theory core (draft)
A tested PC library: keys, chords, voice leading, rhythm, form.
- [ ] 2.0 Plan approved (incl. language and layout, and how it stays in step with the C composer).
- [ ] 2.1 Keys, scales, chords and their functions.
- [ ] 2.2 Voice leading.
- [ ] 2.3 Rhythm and meter; form, sections and energy; how a long play evolves (decision 9).
- [ ] 2.4 A theory exam (our own, after MusicTheoryBench) and choices explained in plain words.
- [ ] 2.5 The two drift measures (decision 9): staleness within a play, sameness between plays, with targets.
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
- [ ] Checkpoint 3: each member in each style, by ear; plus a long clip and two plays of the same settings, with the
      drift measures passed first.

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
- [ ] 6.0 Plan approved (follows Ouralia's CLAUDE.md).
- [ ] 6.1 Shrink the model for the phone; measure CPU and battery.
- [ ] 6.2 `dcs_composer` gains a style and a sound per member, swappable; rules as guardrails; the new roles
      (decision 11) get members and kits in Ouralia.
- [ ] 6.3 The drift measures on the phone (fresh seed each play; the patch's Pd `[random]`s and `expr random` are
      unseeded today, so they repeat after each app start: `docs/format.md`).
- [ ] Checkpoint 6: trap drums with a synthwave bassist, on the phone; off and on again gives a new evolution.

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
