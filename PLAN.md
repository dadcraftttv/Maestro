# Maestro plan

The one place that says where Maestro stands. Read it at the start of every Maestro session; tick tasks off in the
same commit that finishes them. Work goes one task at a time (DadCraft, Oct 23: "bucket by bucket, or task by task
as much as possible to keep token cost low").

**Next:** Bucket 3, the listen after 3.4a (`clips/trap/trap_2222573989`), then 3.4b (synthwave's entry).

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
14. **Maestro is DadCraft's own local model** (DadCraft, Oct 24). He can teach it with Claude, but teaching it
    away from Claude Code and offline is critical: everything works on this PC alone, and neither using nor training
    it spends his Claude budget. Claude and DadCraft keep shaping it as it's used and pain points show up. He gives it documents in any format; a local reader (a small
    openly licensed language model on this PC) reads each one in full, proposes what to add to the style book in
    its own words, with the passage it came from and what it skipped and why, and he accepts or rejects that on a
    local web page. Music he gives it becomes training data, and the PC model trains on this PC. Documents don't
    train the network directly: they become style book knowledge, which drives the rules and the practice MIDI the
    model learns from. Claude builds these tools once; it doesn't do the reading or the training. The PC model is
    the big one; the phone model is distilled from it (decision 8), carries the same rules, theory and styles, and
    becomes the evolution of `dcs_composer`. **The reader is as good as it can be** (DadCraft, Oct 24): the best
    local models this PC can run, several working as a team (skim, extract, cross-check), and free API calls as an
    optional boost when online, for public sources only (Conductor's rule). Offline it does the whole job alone. **Every source is license-checked before it's fed** (decision 7 still
    holds). Free to read isn't always free to reuse; the check decides commercial-safe, NC (PC only) or not
    usable. **Maestro does the check itself** (DadCraft, Oct 24): its reader only finds the notice (footer,
    license or terms page, CC badge, SPDX tag, LICENSE file) and quotes it with where it was found; a fixed rules
    table, not a model, maps the license to the tier (CC0, public domain, CC BY, CC BY-SA, MIT, GPL and the like:
    commercial-safe; any NC: PC only; ND, all rights reserved, no notice, or anything not in the table: not
    usable). When in doubt it refuses: a missing, vague or contradicting notice ("except where noted", third-party
    content) leaves the source not usable until DadCraft looks, or hands it to Claude (the notice and the source
    page, not the whole text). Each verdict shows on the desk page with the notice and the reason, and DadCraft can
    overrule it. Until the desk exists, Claude applies the same table (3.0a).

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
      `rhythm` `form`; `explain.py`); `tests/` (unit, `exam/`, `parity/`); `tools/` (`sync_check.py`;
      the drift measures became `maestro/drift.py` in 2.8).
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
- [x] 2.6 A theory exam (our own, after MusicTheoryBench, no copied questions) with a score, and choices explained
      in plain words.
- [x] 2.7 A PC clip player (moved up from 3.1, DadCraft, Oct 24), so DadCraft can hear MIDI clips: the
      checkpoints from here on are listened to, not read. Song files (`maestro/song.py`: MIDI + JSON, notes kept
      on the grid), the player (`python -m maestro.play <clip or folder>`: FluidSynth through ctypes, FluidR3 GM from
      `tools/get_sounds.sh`, offline) and the baseline: today's composer as four clips (`python -m maestro.baseline`).
- [x] 2.8 The two drift measures (decision 9): staleness within a play, sameness between plays, with targets
      (DadCraft confirmed them Oct 24; drums, bass and pad shown but never capped). `python -m maestro.drift`
      (today's composer, two 20-minute plays per preset) or `python -m maestro.drift a.mid [b.mid]`. Bars compared by
      their notes (loudness left out), held notes included. Today's composer meets every target: no band phrase
      copied, worst 2-minute window 83-93% new bars, melody 4-14% copies, nothing shared between two plays.
- [x] Checkpoint 2: DadCraft spot-checks the explained choices, and hears a few bars per style.
      Clips (Oct 24): `maestro/sketch.py` plays `explain.py`'s choices (same draws: what's heard is what the
      words say), 8 bars, two seeds per style, at trap 140, synthwave 100, salsa 180, power rock 130, all
      in A minor; a bare drum guide (salsa: clave and cowbell), not explained.
      Heard Oct 24: rough approximations, no style and no flow; carried into 3.0 (`docs/verdicts.md`).

### 3. Style book (draft)
For each chosen style, how each member plays it, written from sources.
- [x] 3.0a Source sort (DadCraft, Oct 24): his lists go in `inbox/` (gitignored, nothing public until checked):
      `theory-sites.txt` (one URL a line), `named-refs.txt` (sites known only by name; Claude finds the URLs),
      `ai-systems.txt` (checked against `docs/research.md`). Claude writes the rules table (decision 14) as a data
      file Maestro's desk reuses, then sorts every source by license, the styles and members it covers and the gap
      it fills (`docs/data.md` "Coverage and gaps"), into: style book now (the few key sources for 3.x),
      Maestro's reader later (most of them, bucket D), training data (bucket 4), or not usable. Licenses and
      contents from small samples, not whole sites; sweeps to `librarian`, reviewed by Opus. New ideas from the AI
      systems go to `docs/research.md` and come to DadCraft as proposals. Results in `docs/data.md`.
      Done Oct 24: the rules table `maestro/data/licenses.json` (data.md's tags), the sort in `docs/data.md`
      ("DadCraft's source lists, sorted"), seven proposals in `docs/research.md` round 3.
- [x] 3.0 Plan approved Oct 24. **A style entry** (one JSON file a style, CC BY-SA 4.0, its sources cited; JSON
      like `composer.json` and `licenses.json`: read and written with no extra library, so the desk can write it
      too) holds tendencies and ranges with weights, never fixed patterns (decision 9):
      - **time:** tempo range around the felt tempo (trap ~140, synthwave ~100, salsa ~180, power rock ~130),
        half-time, meter, the grid subdivisions it uses, swing as a grid point (decision 13);
      - **harmony:** mode weights, the chord vocabulary (today's `VOCAB`), **progression families** (loops and
        schemas with their variants), **harmonic rhythm** (chords a bar), cadence habits;
      - **each member it uses** (drums, percussion, bass, keys, rhythm guitar, horns, pad, arp, melody: decision 11):
        register and density ranges, rhythm leanings on the grid, **pattern families** (tumbao, 808 slides, root
        eighths, montuno, power-chord chugs), voice-leading habits, a default sound (a GM program for the PC clips, a
        named sound for Ouralia);
      - **fit and form:** the energies and moods it suits, the one trait it lends when it seasons a blend, who comes
        in first and who sits out (`docs/taste.md`);
      - **checks before DadCraft listens:** `docs/taste.md`'s failure list.
      Every member but drums is an open-data gap in all four styles, so each one's theory is written out in full
      (`docs/data.md` "Filling the gaps with theory"); sources from 3.0a's sort (`docs/data.md`, "For the four
      styles now"). Carries from Checkpoint 2 (`docs/verdicts.md`): flow (3.2), the melody heard on long clips
      (checkpoint 3), a short summary per clip (3.7).
- [x] 3.1 The style book format: the tables in `chords.py`, `voicing.py`, `rhythm.py`, `form.py` and `sketch.py`
      move into one JSON file a style, with a loader that checks each file. Same behaviour: the tests and the exam
      pass unchanged.
      Done Oct 24: `maestro/data/styles/` (a file a style, `book.json` for the order), `maestro/stylebook.py` (the
      loader and its checks, `tests/unit/test_stylebook.py`), the format in `docs/format.md` ("The style book").
      Same behaviour, checked: the tables identical value for value, 136 tests and the exam (106/106) unchanged,
      explain's text and the sketch clips byte for byte.
- [x] 3.2 Flow (Checkpoint 2's "no flow"): progressions drawn as families with variants over 4 or 8 bars, not one
      chord a bar; the bass built on its style's pattern family; the melody shaped over a phrase (a statement and
      an answer landing on the cadence). Check and choose like the other theory modules. Sources: Open Music Theory
      (loops, schemas; each chapter's own note checked), the Rock Corpus (statistics in our words), jazznet (ii-V).
      The drift measures run first (loops repeat, bars must still stay under the staleness targets).
      Done Oct 24 (plan approved; DadCraft chose salsa for the listen and an 8-bar phrase): `maestro/theory/flow.py`
      (families with variants and a cadence each phrase; bass patterns with notes ahead of the chord; the phrase:
      statements on an arc, the half left open, the end home, chord tones on the beat), each with its check,
      `tests/unit/test_flow.py`. Salsa's entry has 7 families (montuno vamp, ii-V, andalusian, the minor circle and
      three major ones) and 3 tumbaos, and now borrows harmonic minor's V7 (which also changes the old path's salsa
      draws). Other styles play the defaults until 3.4. Flow is the default in `explain` and `sketch`
      (`--no-flow`: Checkpoint 2's draws). Drift (`python -m maestro.drift --flow ...`, 20 minutes, two plays a style):
      every target met in all five styles (melody 2-11% copies; bass ~45% and pad 62-78% repeat, as loops do).
      No chapter text used, only the ideas, so no chapter's note needed checking; the Rock Corpus waits for 3.4d.
- [x] Listen after 3.2 (DadCraft, Oct 24): one style, a 16-bar clip with its progression, bass pattern and a phrased
      melody, with its summary (3.7's shape), before the four entries are written.
      Heard Oct 24 (`clips/flow/salsa_23`): more like salsa, the clave and bass a nice feel, the lead goes round and
      comes home, question and answer heard; "a big step in the right direction ... still a long way to go". How
      much the rounds change he couldn't tell: asked again at checkpoint 3 (`docs/verdicts.md`).
- [x] 3.3 The drummer, starting from the Groove MIDI Dataset (CC BY 4.0), and the **percussion** member (congas,
      timbales, cowbell, clave), written from theory (El Bongosero's data license is still unclear).
      Done Oct 24 (plan approved; DadCraft chose: salsa has percussion and no kit, percussion for salsa now and the
      rest in 3.4, GMD as groove families plus odds, a listen to salsa and power rock): `tools/groove_stats.py`
      counts GMD (straight takes, lined up on the backbeat, rounded to 16ths) into `maestro/data/grooves.json`;
      `maestro/theory/drums.py` (a groove a section, kept or changed bar by bar at GMD's rate, the small hits by its
      odds and the energy, fills at phrase ends with toms mostly going down, a crash on each section, trap's half
      time and hat rolls; the check: grid, two hands, the backbeat); `maestro/theory/percussion.py` (salsa's clave,
      conga tumbao, bongo martillo or bell, cáscara on shell or bell, güiro, an abanico into a section; the check:
      no part crosses the clave), `tests/unit/test_drums.py`. Drummers: power rock from rock, trap from hip hop,
      synthwave from dance and pop, plain from rock and pop. Drift (20 minutes, two plays a style): every target met;
      the drums copy one of their last 16 bars only 1-12% of the time, the percussion 59%. 181 tests, exam 106/106.
- [x] Listen after 3.3: `clips/drums/salsa_23` and `power_rock_26` (32 bars each: a 16-bar clip is always one
      section, and the change between sections is what to hear).
      Heard Oct 24: "good first pass on the drums and percussion. both feel like they should. still a long way to
      go, but absolutely a good first run." The drummer "sounds steady, not restless" (Oct 24).
- [ ] 3.4 One task per style, each entry covering every role it uses: 3.4a trap, 3.4b synthwave, 3.4c salsa,
      3.4d power rock.
      Before 3.4a (DadCraft, Oct 24): a closer look at trap's data and theory, in `docs/data.md` ("Trap, a closer
      look"): no open trap MIDI anywhere, so trap's training data is the entry's practice MIDI and open audio turned
      into MIDI; six proposals for the entry, for DadCraft to choose from in 3.4a's plan.
      3.4a done Oct 24 (plan approved; DadCraft chose: proposals 1-4 now, the drop-outs and beat switches in 3.6,
      the subgenres later; the 808 slides now and then, about 1 note in 6; a bell lead; dark strings under it).
      The 808 (`flow.bass_808`): no pattern, a note on each of the drummer's kicks and each chord change, held to the
      next, mostly roots, some fifths and octave jumps, 16% of its notes sliding into the next (a pitch bend over the
      last 8th, the bend range an octave; `song.py`); its check: every note on a kick or a change, every slide
      landing on the next note, a chord tone. So trap's drums are drawn before its bass. Harmony: six loops of one
      or two chords (one chord, i-bVI, i-bII, i-iv, i-V and a bright I-vi for a major key), a chord every one or two
      bars, a phrase made to land home only 25% of the time (`cadence`), one-chord loops allowed (`still`). The
      melody: a motif move `triplet` (two notes filling a beat played as three 8th triplets, after Duinker's
      triplet flow), weighted per style (`members.melody.develop`). The drums: the snare fixed on 3 (`backbeat`,
      only GMD's plain-backbeat grooves, no extra snares; checked), the hats turning for a beat to 16th triplets,
      32nds or 8th triplets (`turns`, 12% of beats at energy 0.5). Sounds: glockenspiel lead, slow strings, a synth
      bass for the 808. `tests/unit/test_trap.py`; 189 tests, exam 106/106. Drift (20 minutes, two plays): every
      target met in all five styles (trap's melody copies 4%, pad 93% as its harmony stays put). Open Music Theory's
      "Drumbeats" refused the fetch again (HTTP 403): left out.
- [ ] Listen after 3.4a: `clips/trap/trap_2222573989` (32 bars, i-bVI throughout), with its summary and "listen
      for" line.
- [ ] 3.5 The style judge (CLaMP 3, license checked) scores the clips first. TinyMU as a second, small local judge
      that says what it hears, if its license allows (research round 3, DadCraft, Oct 24).
- [ ] 3.6 Layering (arrangement): which members play when. Members join one after another along a build and drop
      out as it eases (after Ouralia's Calm builds: pad, room notes, chimes, then harmony and reverb, each joining
      further along the rise; `docs/format.md`), and sections thin or fill the band. Each style's entry says who
      comes in first and who sits out (trap might drop its drums for a breakdown), as tendencies, never a fixed
      order (decision 9). Driven by `form.py`'s energy, with the check and choose like the other theory modules.
      Also a style per section (after HeartMuLa, research round 3, DadCraft, Oct 24): the blend can shift as the
      song moves (the band turns salsa for a breakdown), as tendencies too.
      In bucket 6 it becomes the way Calm builds and Maestro's arc stop stacking (DadCraft, Oct 23).
- [ ] 3.7 Clip summaries: a short summary in plain words for each checkpoint clip (shape agreed Oct 24: style,
      bars, key, tempo; the chords as a loop and how it varies; the bass; the pad; the melody's phrase; a "listen
      for" line). The detailed per-bar explanation stays, for debugging.
- [ ] Checkpoint 3: each member in each style, by ear; plus a long clip and two plays of the same settings, with the
      drift measures passed first. Ask DadCraft whether the on-grid band sounds too robotic; if so, the reserve
      pocket (decision 13) can be played to him next to the on-grid version. Ask too whether the chord rounds change
      too much or too little, on the long clip (open from the listen after 3.2). Also for his ear, from 2.5: the
      semitone key lift, how sections growing heavier comes across, and the layering (3.6).

### D. Maestro's own desk (draft; between buckets 3 and 4, decision 14)
A local web page on this PC where DadCraft teaches Maestro without Claude Code.
- [ ] D.0 Plan approved: the reader models, picked on a test of our own (the same chapters run through each
      candidate, scored on what it got right and what it missed), from what's best when we get there: the license,
      what fits the RTX 2070's 8 GB plus 62 GB of RAM (mixture-of-experts models with part of the weights in RAM
      run well beyond the 8 GB), the speed. The converters, the page, and the free APIs for the online boost.
- [ ] D.1 Converters: any document to text, locally (PDF, DOCX, EPUB, web pages, Markdown, text; OCR for scans).
      Each source recorded with its license and tier (decision 14) before it's read: the notice finder (quotes
      the notice and where it was found) and the rules table from 3.0a; not usable unless the table says otherwise.
- [ ] D.2 The reader, as a team of local models: a fast one sorts each part of a document (useful for music or
      not, which style and member), a stronger one writes the proposals, a second one cross-checks them against the
      passage; online, free APIs can add a vote. It reads every part, proposes style book changes in the data format of 3.1 with
      the passage each came from, and lists what it skipped and why. The theory checks and the exam run on each
      proposal before DadCraft sees it.
- [ ] D.3 The page: drop files in, see what was taken away, accept, edit or reject; accepted changes go into the
      style book, with the source credited.
- [ ] Checkpoint D: DadCraft feeds an open textbook chapter through the page, away from Claude Code, and judges
      what it took away.

### 4. Training data (draft)
- [ ] 4.0 Plan approved.
- [ ] 4.1 Download the clean sets, each tagged with its license.
- [ ] 4.2 Practice MIDI made from the style book, labeled.
- [ ] 4.3 Open audio to MIDI: stems, Basic Pitch, Beat This! on CC0 modern tracks.
- [ ] 4.4 Label (style, member, attributes), tokenize; commercial-safe and NC kept apart.
- [ ] 4.5 The desk takes music: drop MIDI or audio on the page (audio through 4.3's tools), tagged and licensed.
- [ ] Checkpoint 4: counts, and random samples by ear.

### 5. The model (draft)
Trained on this PC (RTX 2070, 8 GB).
- [ ] 5.0 Plan approved.
- [ ] 5.1 A small per-member model with controls (MIDI-GPT style); each member written seeing the others.
- [ ] 5.2 Compare a GETMusic-style model; keep the better one.
- [ ] 5.3 Style dropout for the "how much style" knob; style blends.
- [ ] 5.4 Learn broadly, then specialize per style; improve against the judge (NotaGen's CLaMP-DPO idea).
- [ ] 5.5 The drift measures on the model: within a play and between plays; check it doesn't copy its training data.
- [ ] 5.6 Train from the desk: one button rebuilds the practice MIDI and retrains the PC model on this PC.
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
DadCraft's verdicts and the notes on each finished task are in `docs/verdicts.md` (grep it; don't read it whole).
