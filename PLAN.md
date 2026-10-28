# Maestro plan

The one place that says where Maestro stands. Read it at the start of every Maestro session; tick tasks off in the
same commit that finishes them. Work goes one task at a time (DadCraft, Oct 23: "bucket by bucket, or task by task
as much as possible to keep token cost low").

**Next:** the third proof under decision 19 (started Oct 28, Codex has it): PDMX's human-written open scores rendered three ways (faithful, mapped on piano, mapped on Maestro's sounds), no transcription; its four steps under decision 19 in "Decisions" (grep "third proof").

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
8. **The phone version is small** (target: tens of MB, around MIDI-GPT's ~20M parameters), shrunk from the PC model.
9. **Free to drift, always making sense.** Maestro is never locked to fixed patterns: styles are written as
   tendencies and ranges, the model makes fresh choices each bar, and the rules only rule out what doesn't fit,
   never say what to play. Compositions evolve over a long play (key, energy, density, how strongly each style
   shows, motifs that develop). **No style trait is ever a lock** (DadCraft, Oct 23): the drafts are starting
   points, and an unexpected mix can work (something bright and happy over trap has, for him). **No two plays are
   alike:** turn Ouralia off and on with the same settings and the evolution is a new one. The same key and scale
   share notes, but the music is never identical run to run (a fresh random seed each play; no replaying a stored
   path). Measured before DadCraft listens: staleness within a play (how often bars and phrases repeat over ~20
   minutes) and sameness between plays (two runs, same settings). Grooving members (drums, percussion, bass, pad)
   and a melody that loops (trap's riff) repeat freely; the band's own targets still hold (DadCraft, Oct 24: "let
   the riff repeat freely").
10. **Licenses:** code GPL-3.0-or-later (like Ouralia); docs and the style book CC BY-SA 4.0 (README "License").
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
15. **The beat never waits** (DadCraft, Oct 26, from the outside reviews: `docs/research.md` round 4). Maestro
    makes each member's next bar ahead of time and keeps it queued; the model never runs note by note. If a bar
    isn't ready in time (the phone busy, the model slow), the rule-made bar plays instead, so a slow model never
    drops a beat or stalls the sound. The time to make a bar is measured on the PC from the model spike (S.1) on,
    and on the phone in 6.1.
16. **Checkpoint 3 asks for a sound baseline, not a finished style** (DadCraft, Oct 26). A listening round is worth
    running while it still changes the style book's format or the checks; once a style's rounds only fine-tune its
    sound (salsa's fuller horn section, synthwave's lead register and the like), that tuning waits for the desk (D),
    where DadCraft does it himself, offline, and it tests the desk too. Each style passes Checkpoint 3 when it is good
    enough to be a sound baseline: for the practice MIDI, the guardrails and the fallback bar (decision 15).
17. **Every member can be hot-swapped** (DadCraft, Oct 26: "in the end we should be able to keep trap elements and
    swap one of them for salsa. same with every style. everything can run how it should be it should be able to get
    hot-swapped and still make sense"). Any member of any style can be swapped for another style's while the band
    plays, and the band still makes sense. So each member's rules travel with its own style, not the song's (a salsa
    bass in a trap band keeps its E1 floor and its tumbao), the judge scores each member against its own style's
    card (a song file's `members.<name>.style`), and the guardrails check a swapped member against the band it
    joins (the chords, the clave). Building it: 5.3 (style blends) and 6.2 (a style per member in `dcs_composer`).
18. **Checks sized to the change** (DadCraft, Oct 27: "the workflow needs to be optimized", after a one-style task
    took 30-45 minutes of checks). A task that changes one style fuzzes and drifts that style only
    (`tools/fuzz.py <style>`, `python -m maestro.drift --flow <style>`); the other styles are covered by their clips
    staying byte-identical, as their output hasn't moved. Every style is fuzzed and drifted when shared code changes
    (theory, flow, sketch, song, the player) and before each Checkpoint; GitHub runs the tests on every push. The
    checks use every core: pytest runs parallel by default (`-n 0` for one process), fuzz and drift spread their work.
19. **The notes come from real music; the rules are the guardrails** (DadCraft, Oct 28: "i'm fine with it. we need
    to get Maestro to a point where it's producing convincing music on the fly so it can integrate with Ouralia the
    way it's supposed to"). After "nothing about it sounds convincing": the rule-written parts sound like a
    description of the style, not the style. Checkpoint 3's style-by-style rounds stop; the rules keep key, chords,
    range, the beat on time and the hot-swap (decision 6, 17); the spike (S) comes forward onto a melodic member;
    bucket 4's sources are rethought (real music to MIDI and the desk; practice MIDI from the style book would only
    teach the rules back). First, the proof: his three references (`inbox/`: Suno covers of Nintendo songs, his
    prompts beside them; copyrighted, so ideas only, on this PC, never committed or sent out) turned into notes and
    played through Maestro's own sounds, next to ours.
    The proof built Oct 28 (`tools/transcribe.py`: Demucs stems, Basic Pitch notes, about 15 s a song on the GPU):
    the three in `private/refs/proof`, each notes only (Maestro's synthwave sounds: saw lead, supersaw, saw bass)
    and with its own drum stem, next to synthwave seed 12 (the same sounds) without and with its drums; all at
    synthwave's mix targets. The transcription is rough (a few stray notes; the melody is the top voice of
    Demucs's "other" stem). His listen (Oct 28): "those notes for those songs through our system sound awful."
    The same sounds made our clip generic, not awful, so the rough transcription is the likely cause: not yet an
    answer, and a warning for bucket 4.3 (audio to MIDI is the data plan).
    His second word (Oct 28): "the timing of these notes is all over the place and just wrong"; the plan
    (snap to the beat, single lines, measure first, then a piano listen) "yes, i'm fine with your plan"; his UVR5
    install offered. Second round: `tools/transcribe.py` splits with htdemucs_ft from UVR's model folder, fits one
    tempo to the drum stem (measured: ALttP 100, P-Switch 158 not the prompt's 160, Underground 88 not 117) and
    the 16ths' phase to the pitched stems' strikes; lead and bass by pYIN as single lines, the pad as half-bar
    chords, every note on a 16th. Measured against the stems: notes start a median 11 ms from the real ones
    (Underground, 80% within 40 ms); pitch match 0.66 / 0.80 / 0.70 (first round, ALttP: 0.65, off the grid). In
    `private/refs/proof`: each song's real bass and other stems (a), the notes on a GM piano (b), through
    Maestro's sounds (c), and with its own drum stem (d). His listen (Oct 28): "it's better, but not by much. it's
    like the aliens got a slightly better understanding of what the box was supposed to be." Transcribing audio
    is not the main source; next proposed: human-written open scores (PDMX) through the same player.
    **The third proof, approved and on hold** (DadCraft, Oct 28: "yes, but hold off on that. log that as the next
    step"; Claude Code or Codex may pick it up). The steps:
    1. Check PDMX's license notice and its own license-conflict flags at the source; record what's found in
       `docs/data.md` (it's listed SAFE there) before using it. Fetch only the files needed if the set allows it
       (the full set is 14.4 GB), into `private/` (gitignored).
    2. Pick 4-6 well-rated pieces tagged pop, electronic, game or film style, people's own originals only: no
       arrangement of a copyrighted song, whatever its license (decision 7). Say why each was picked.
    3. Render each piece three ways, into `private/pdmx_proof/` (Codex's review, Oct 28: one change per step, so a
       bad result points at its cause). (a) Faithful: the score as written, all its parts on their own GM
       instruments. DadCraft listens to (a) first and keeps only the pieces he finds convincing; the rest are
       dropped. (b) Mapped: the kept pieces' parts mapped to Maestro's members (melody, pad, bass; drums left out),
       on a plain GM piano (program 0). (c) The same mapped events as (b), the same timing, durations and
       velocities, on Maestro's synthwave sounds (saw lead, supersaw, saw bass), balanced with `python -m
       maestro.mix` to synthwave's targets.
    4. Measure first: what the mapping lost (notes dropped, parts merged, register moved), the mix check, note
       counts and ranges. Then tell DadCraft what to listen for. (a) → (b) is the mapping, (b) → (c) the sounds. If
       (c) convinces where ours and the transcribed ones didn't, the notes are the gap: S trains on PDMX's
       melodies and chords (whether PDMX is enough data is bucket 4's question). If it breaks at (b), the
       mapping comes first; at (c), our sounds and rendering are fixed before any model work.
    DadCraft, Oct 28: "i'd like to start the third proof", with the three-way render; Codex takes it.

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
- [x] 3.4 One task per style, each entry covering every role it uses: 3.4a trap, 3.4b synthwave, 3.4c salsa,
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
- [x] Listen after 3.4a: `clips/trap/trap_2222573989` (32 bars, i-bVI throughout), with its summary and "listen
      for" line. Heard Oct 24: "not what i would call trap. not even close": the 808 not felt as bass and kick at
      once, the slides buried under the pad and bells, the hats stiff and not rolling, the whole a little stuck
      (`docs/verdicts.md`).
- [x] 3.4a, second round. Plan (Oct 24): the sound and the mix, written hat and kick patterns, a loop melody, the
      drop-outs pulled forward from 3.6. DadCraft: trap is 2 Chainz, Future, Travis Scott ("a cleaner trap sound
      and not the fuzzy distortion"), Atlanta and others; the sounds "what would get us closest"; "try everything".
      Done Oct 24: `maestro/synth.py`, Maestro's own sounds made the TR-808's way (a clean sine 808 with a long
      decay and real glides, a punchy kick, a clap, square-wave hats), mixed in by the clip player with FluidSynth's
      GM members (numpy now a dependency); a member's sound may be `"808"` or `"808 kit"`. Trap's mix: the 808 and
      kick loudest, the strings thin (48), the bell over them (110). A programmed drummer (`drums.Programmed`):
      six written kick patterns and six hat patterns with their rolls (louder as they run), the clap on 3,
      machine-steady; the kick varies a note 25% of rounds; the kick, clap and 808 drop out for a section's last
      bar half the time, and the play opens on 4 bars of hats alone (the 808 rests with them; checked). The melody
      a loop (`flow.loop_melody`): a 1- or 2-bar riff of rhythm cells (triplets among them) going round the section,
      its beat notes fitted to each chord, a phrase's last round landing home. No chord swaps. 189 tests, exam
      106/106. Drift: every band target met; the melody's own (copies of its last 16 bars <= 30%) not: 77%, as a
      riff repeats; asked of DadCraft, the target unchanged until he says.
- [x] Listen after 3.4a's second round: `clips/trap2/trap_74` (32 bars; hats alone, the drop at bar 16, three
      kinds of section). Heard Oct 24: the bass "definately feels more like trap", the pads and bells still too
      loud to hear the hats; "a good step in the right direction". Remixed (the hats up 10 dB, the bell and the
      strings down 5-9 dB, the same music).
- [x] Listen to the remix of `clips/trap2/trap_74`. Heard Oct 24: "better"; the bells and pads still loud and too
      busy; kit parts he hears in his head missing. Auditions (`clips/audition/`) chosen: the snare rolls, a snare
      under the clap, the cymbal swells and riser, and a falling snare cascade, staccato (audition 11).
      Built Oct 24: the clap on 3 layered over a snare; at a section's end a snare roll (16ths, then 32nds, louder,
      40%) or the cascade (50% of the rest, and of 8-bar runs inside a section): 16ths over the last two beats,
      each hit cut short, stepping down, the kick and hats stopping for it; a reversed cymbal into 60% of
      sections with a crash on the one, a riser over the last two bars of 35%; drop-outs 40%. The bell quieter
      (72) and sparser (rests and quarters favoured), the strings quieter (28). 190 tests, exam 106/106; drift's
      band targets met, the riff's own still 77% (asked).
- [x] Listen to `clips/trap3/trap_1025`. Heard Oct 24: the bells and strings "could stand to still be even less
      busier"; the cascade "not hitting right"; "in general, i'm not crazy about what i'm hearing for trap so far
      beyond the bass". The riff repeats freely (decision 9). Done: the riff plays every other round (78 notes
      where there were 168), the strings two voices (66 notes where there were 99), the cascade off (its code
      kept). Clip: `clips/trap4/trap_1025`, the same music.
- [ ] Trap, when DadCraft brings a reference (Oct 24: "i'll listen to some trap at some point and come back with a
      sample", likely copyrighted): heard and described on this PC only, ideas in our own words, the file kept in
      `inbox/` (gitignored), never committed, never sent to a free API, never training data (decision 7). Then the
      cascade, and whatever else he finds missing.
- [x] 3.4b Synthwave. Plan (Oct 24), approved; DadCraft chose: outrun as the core and dreamy calm sections
      ("what would you recommend?": outrun, the sound most mean by synthwave and what his own notes describe), light
      pumping, RTRO-DRM later (writing its patterns from theory now), all seven proposals.
      Done Oct 24: Maestro's own synthwave sounds in `synth.py`, stereo: a supersaw pad (seven saws, ±28 cents,
      spread), a saw bass (its filter snapping shut, a sine sub), a plucked arp with a ping-pong echo on the dotted
      8th, a saw lead with vibrato on held notes, a LinnDrum-style kit (gated-reverb snare and toms); a reverb a
      member, the pad (35%) and bass (20%) ducking under the kick (`pump`, a member's field in the song's JSON).
      The bass by mood (`when` on a pattern): octave or root 8ths and 16ths when the energy is up, a held sub when
      it's low. A new **arp** member (`flow.arp_part`): a shape a section (up, up and down, broken, climb, pedal)
      round each chord's tones from C4, 16ths, or 8ths when the energy is low; checked (one note at a time, chord
      tones, its range); it stays under the lead. The programmed drummer generalised: the snare's beats a style (2
      and 4) or a kick pattern (half time on 3 for calm sections), tom fills high to floor into a section; the check
      takes each bar's allowed snare beats. Harmony: six four-bar families (the aeolian loop i-bVI-bIII-bVII first;
      two major ones for a lifted key), rounds mostly as written, half the phrases landing home. Tempo 112, full
      from the first beat. The tempo stays one a play: the calm sections slow by the drums going half time, not by
      a tempo change. 198 tests (`tests/unit/test_synthwave.py`), exam and parity pass; drift: every target met
      (melody copies 3%; trap's unchanged). Trap's clips are byte-identical.
- [x] Listen after 3.4b: `clips/synthwave/synthwave_14` (32 bars: 16 outrun bars, a tom fill, 16 dreamy bars).
      Heard Oct 24: "yes" to all the listen-for questions (outrun, then dreamy; the lead on top; the light pump; the
      tom fill); the pads and leads still too loud. Done: the pad and lead each about 3 dB down (levels 56 and 80);
      no new render yet (DadCraft: not now). His synthwave finds checked (`docs/data.md`): nothing new to train on;
      SynTheory (MIT) kept for the style judge; one preset suggests the lead sits too high (an idea for later).
- [ ] Synthwave, next round (logged Oct 24, DadCraft: "log that to pick up next time"): ask him first whether a
      phrase should land home through bVI-bVII-i (F-G-Am) instead of the flow's borrowed V7 (E7-Am), as YC Music
      Theory's minor-key pop page suggests (`docs/data.md`); the lead's register (ours E5-A6, the Reimaginer's
      preset centred on G#4). The quieter pad and lead were heard in the A/B after 3.8 (B, his pick).
- [x] 3.4c Salsa. Plan (Oct 26), approved; DadCraft chose: all six proposals, classic Fania era, the tempo kept at
      180. Done Oct 26: the **keys** member (`theory/keys.py`): the piano montuno, a two-bar guajeo in 8ths a
      section (four patterns, two only when loud, one only when low), its top line in octaves, a chord tone filling
      in on the clave's strokes and the anticipations, each change pushed in an 8th early; every pattern checked
      against the clave when the book loads. The **horns** member (`theory/horns.py`): two trombones (GM 57) in
      harmony (the chord tone a third to a sixth under the top line, a third down the scale on a passing note):
      punches on the clave's strokes closing the lead's phrases, the coro (a two-bar refrain, kept all section,
      answering the lead in bars 3-4 and 7-8), the mambo's riff; a loop that crosses the clave with what the horns
      played before is drawn again, then they punch. **The parts** (`theory/arrange.py`, the style book's new
      `arrange`, a first piece of 3.6): a part a phrase, the play's first section the cuerpo (the lead sings, the
      horns punch), loud phrases the montuno (the lead calls, the coro answers) or, after a montuno, a mambo (the
      horns' riff, the lead out); 60% of section ends break (bass, piano and horns on the clave's 3-side strokes, the
      percussion down to the clave, the strokes and an abanico, the lead silent). The bass: two more tumbaos (the
      third, the octave) and a walk up into 50% of the other section ends (on 1, the and of 2 and of 3, landing on
      the tumbao's 4). The pad sits out (`plays: false`), still voiced so the lead keeps its room. Where leaving
      the lead out would cross the clave (the whole play or cut at the clip's end), it sings on. Mix: new defaults
      keys -8 to -3 dB and horns -6 to 0 dB under the melody; salsa's gains from the mix check (percussion -7,
      horns -7, bass -3, keys -6), every member in its target. 212 tests (`tests/unit/test_salsa.py`), exam
      106/106, fuzz 2000 seeds a style clean, drift every target met (melody copies 2%); the other styles' clips
      byte-identical (80 seeds).
- [x] Listen after 3.4c, as A/B: `clips/ab/salsa` (seed 75, 32 bars; A: 3.3's round, cac0f0a; B: today's: 16 bars
      of cuerpo, a break, 8 of montuno, 8 of mambo). Oct 26: B ("the piano timing sounds right", the trombones
      sound right, "the break hits together, and the progression feels right. It still feels like salsa").
- [ ] Salsa, next round (DadCraft, Oct 26, "maybe down the line"): a fuller horn section for styles that have one,
      more horns playing together, a little quieter, "so that we get that full horn section sound". Today's two
      trombones already play in harmony but on one GM track; look at each voice on its own (its own channel and
      pan) and adding the trumpets (and sax where a style has them), set in the mix check.
- [x] 3.4d Power rock. Plan (Oct 26), approved; DadCraft chose: all seven proposals, 80s arena rock, the tempo
      kept at 130, the guitar solo later (3.6). Done Oct 26: the **guitar** member (`theory/guitar.py`): power chords
      (root, fifth, octave) doubled on two tracks, left and right (pan ±48), each in its own octave (from E2, from
      E3), sliding as one shape; patterns in three groups (palm-muted chugs, a gallop; driving 8ths; the anthem's
      3-3-2 push, ringing chords), two of them locking the bass to their rhythm; checked (roots and fifths of the
      chord sounding or pushed, each track in its octave). **Harmony** from the Rock Corpus (CC BY 4.0;
      `tools/rock_stats.py` counts one analyst's RS 200 chord lists into `maestro/data/rock.json`, the files kept in
      `private/`): I, IV, V hold most of the time; 1975-1991, bVII in 51% of songs (36% overall), bVI in 35%. Eight
      families (anthem, double plagal, the I-IV vamp, fifties, the bVI-bVII climb; three minor), every phrase landing
      home; the home key drawn mostly major (`form.home`: major 3, minor 1). **The bass**: root 8ths, the octave pump,
      the push, sparser verse roots. **The lead**: on the pentatonic off its chord tones, 16% of held notes bending up
      a step into place (held to the note's end), vibrato (CC 1) on long notes. **The parts** (`arrange`: verse,
      chorus, drive, pre-chorus): the play opens on a palm-muted verse, 70% of quiet sections leading into a loud one
      build through a pre-chorus (the snare in 8ths then 16ths, rising), 40% of section ends stop (the band on the
      one, ringing, the drums filling in); the drummer keeps time on the hat in a verse, the ride or crash in a chorus
      (`"loud time"`, by the part). The pad sits out. The song file gained pan (CC 10), vibrato and held bends. Mix:
      guitar target 3-8 dB under the lead each, gain -9 from the mix check on 8 clips. A fix found by the fuzzer (any
      style): a phrase's half landing on a borrowed chord with no other tone in the key stepped up instead of landing
      home. 223 tests (`tests/unit/test_power_rock.py`), exam, fuzz 2000 seeds a style clean, drift every target met
      (melody copies 4%); the other styles' clips byte-identical (80 seeds).
- [x] Listen after 3.4d, as A/B: `clips/ab/power_rock` (seed 65, 32 bars; A: 3.3's round, ee7fe99; B: today's: an
      8-bar verse, an 8-bar pre-chorus ending in a stop with the snare build, 8 bars of chorus on the double plagal,
      8 driven). Listen for: 80s arena rock; the two guitars wide, tight palm mutes in the verse, big in the chorus;
      the build and the stop; the bass driving with the kick; the lead's bends in tune; the flat seventh.
      Oct 26: B ("B wins again, but i wouldn't say it sounds like 80's arena rock at all. the guitars sound fine.
      Everything else sounds fine.").
- [x] Power rock, second round (DadCraft, Oct 26: B fine, but not 80s arena rock). Asked what's missing: "when i
      think power rock, i think double bass pedals and dueling guitars, akin to Bill and Ted, among others." Plan
      approved: "all of it, 150, both, pull the solo forward"; the target is now 80s hair metal and shred. Done Oct 26:
      **double bass** (`drums.double_kick`, written from theory: GMD has none): in the chorus, drive and duel both
      feet run 16ths, the gallop or 8ths into 16ths (a run a phrase, mostly kept), 30% of the other phrases end on a
      beat of 16ths; never in a stop or a build. **Two leads**, one each side (pan ∓32): the first alone in a verse;
      in a chorus (`lead: "twin"`) the second a third under it in the key; **the duel** (`lead: "duel"`, a part after
      a chorus, the solo pulled forward from 3.6): the two trade shred licks over the phrase, two bars each, then one,
      then half a bar, and land home together a sixth apart; a lick is a pentatonic run (16ths, 40% in 16th
      triplets), a pedal lick or a sweep, ending on a held chord tone (`guitar.duel`, `check_leads`: in range, never
      both at once unless a third or sixth apart, a lick's held notes on their chord). The twin bends with the first.
      A gallop in the drive group too, locking the bass. Tempo 150. Mix: rhythm guitars gain -11 (6-7 dB under the
      lead), drums -1; every member in its target on 8 clips. A verse's timekeeping now never on the ride or crash.
      226 tests, fuzz 2000 seeds a style clean, drift every target met, the other styles' clips byte-identical.
- [x] Listen after power rock's second round, as A/B: `clips/ab/power_rock` (seed 63, 48 bars; A: the first round,
      6543892; B: today's: verse, pre-chorus with the snare build, a chorus in twin harmony, a duel, a chorus, a
      duel; double plagal then the anthem loop). Listen for: hair metal and shred; the double bass in the loud parts;
      the duel trading left and right, the turns shorter and hotter, landing home together; the twin harmony.
      Oct 26: B. "it doesn't sound like 80's hair metal or thrash, but it's better than it was. i almost didn't hear
      the double bass pedal kicks." The duel and the twin harmony: "yes and yes".
- [x] Power rock, third round (logged Oct 26): the double bass barely heard (the GM kick soft and masked by the
      bass's 8ths: louder, clickier kicks in the runs, the bass out of their way); still not hair metal or thrash,
      most likely the sound (GM stand-ins: Maestro's own high-gain guitar, a tight metal kit, a scooped mix), maybe
      thrash's faster tempo and riffs. Ask DadCraft which first.
      The kick first (DadCraft, Oct 26: "yes, fix the kick"). Done Oct 26: every double-bass kick at velocity 120,
      both feet even; GM's Power kit (sound 16; the song file now writes a kit's program when it isn't 0); the bass an
      octave up (under G2) in the double-bass phrases, out of the kick's low end; drums gain -9 (the Power kit is
      louder throughout). The kick alone measured 7 dB up against the band; the drums in their target on 4 of 5
      clips (a verse-heavy one 1.2 dB under). 226 tests, fuzz 2000 clean, the other styles byte-identical. A/B:
      `clips/ab/power_rock` (seed 63, 48 bars; A: the second round, df745ed; B: the new kick). Heard Oct 26: "B wins."
      Closed Oct 26 (DadCraft: "lets save the metal sounds for later. no thrash."): no thrash, in power rock or as
      a style.
- [ ] Later (DadCraft, Oct 26): Maestro's own metal sounds for power rock (a high-gain guitar, a tight metal kit, a
      scooped mix) in place of the GM stand-ins. Ask DadCraft when to pick it up.
- [x] 3.5 The style judge scores the clips before DadCraft listens. **Our own judge** (DadCraft, Oct 26: "Own
      judge"): no outside weights, offline, safe to ship. The license check ruled the planned ones out: CLaMP 3's
      code and weights are MIT, but its symbolic model (C2) learned from M4-RAG (CC BY-NC-ND, research only; music
      found by searching song titles and artists, its 0.75M symbolic pairs unpublished), so fan MIDI of copyrighted
      songs can't be ruled out (decision 7: no weights trained on it). TinyMU (arXiv 2604.15849) has no code, weights
      or license we could find; look again if it gets a release. A small classifier trained only on our practice MIDI
      and openly licensed sets can join the judge in buckets 4-5, and 5.4 improves against this judge.
  - [x] 3.5a Style cards: a "judge" part in each style file, a few measurable traits a member (notes a bar, which
        steps it hits, syncopation, register, chord tones, velocity spread, repetition) as ranges, each with its
        source. Written from the sources (`docs/research.md`, `docs/taste.md`, the style's references), not copied
        from the generator's own numbers, so the judge doesn't just grade the rules against themselves.
        Done Oct 26: cards in trap, synthwave, salsa and power rock (plain is the core's defaults, no card), 2-5
        traits a member, the drums by lane and salsa's percussion by part; the trait list and its definitions in
        `stylebook.TRAITS` (syncopation: an onset off the beat with no onset on the next beat; chord tones counted
        on the beat, against the chord there or the one a note is held into, so the tumbao's anticipations count);
        the loader checks every card. Expected in 3.5c: synthwave's lead register (the Reimaginer's C4-C6) will flag
        today's lead (E5-A6), the open point already waiting for synthwave's next round.
  - [x] 3.5b `maestro/judge.py`: measures a clip's MIDI (its `.json` gives the roles), scores each member against
        its style's card and names the trait that's off ("trap hats: too few rolls"); a cross check scores each
        clip against every style's card, and a clip should fit its own style best.
        Done Oct 26: `python -m maestro.judge clip.mid` (or a Song in memory). A trait inside its range scores 1,
        falling to 0 a range's width outside. The fit is the mean over members (the band's tempo and chords count
        as one), so a busy drum card doesn't outweigh the melody, and a member a style has no card for scores 0
        (otherwise synthwave, with no guitar card, out-fit power rock on its own clips). "Repeats" compares where
        the onsets fall, not their pitches, so a montuno or arp following the chords still goes round. A blend
        can give each member its own style. `song.read_notes` now keeps overlapping notes of one pitch (trap's
        32nd hat rolls lost 8 of 306 hits), and a roll ringing past the end adds no bar. 246 tests.
        First run (seeds 7-9, 16 bars): every clip fits its own style best (trap 99% against synthwave's 87%,
        the closest; the others by 25 points or more). Flagged, for 3.5c: synthwave's lead A5-E6 against C4-C6
        (expected) and its bass down to C1 on two seeds; salsa seed 7 drew "tumbao on the one" for the whole clip
        (beat 1 every bar against the card's 0-40%, 50% chord tones since its beat-4 anticipation stops at the
        bar line instead of being held into the next chord, down to D1 under E1), and the keys' syncopation at 23%
        against 25%; power rock's timeline says "A" for all 16 bars while the riff moves A5-D5-E5 (guitars 77%
        chord tones, bass 62-66%), guitar R doubles an octave up (A3-A4 against E2-E4), and seed 8's bass plays 12
        notes a bar against 2-8. One-offs: trap's melody at 9 notes a bar (seed 7) and no triplets (seed 9).
  - [x] 3.5c Check the judge: today's clips pass their own cards; wrong clips (a member from another style, the
        velocities flattened, the notes shuffled off the style's steps) score low; SynTheory (MIT) tests the chord
        and tempo measures where it fits. Tests and fuzz clean. Then every listen gets the judge's table first.
        The plan (Oct 26, from DadCraft's calls on 3.5b's flags), first the fixes, then the checks above:
        1. Salsa's "tumbao on the one" plays only for a few bars, not a whole clip (DadCraft: "only for a few
           bars"). The bass entry limits it; the card's beat 1 range (0-40% of bars) stays.
        2. Chord tones count anticipations: a note on the last beat before a chord change that fits the coming
           chord counts, held over the bar line or not (Open Music Theory, "Embellishing tones": the anticipation).
           Claude's suggestion, asked for by DadCraft ("what would you suggest?"): confirm with him first. The
           narrower choice was to keep "held into" only.
        3. Power rock, both (DadCraft: "why not both?"): the timeline names the riff's chords as it moves (A5, D5,
           E5, not "A" all clip; the bass and lead read it too), and the guitar card allows the riff's passing
           tones, its floor set from a rock riff source, not from the generator's numbers.
        4. Guitar R keeps its octave-up double (DadCraft: "yes"); the guitar card's register widens to cover it,
           from a source on doubled guitars.
        Fixes done Oct 26 (DadCraft confirmed the anticipation rule: "Count anticipations"):
        1. A bass pattern may say "most" (bars in a row, then another of the style's patterns takes over and is the
           one a next section keeps); "tumbao on the one" has 2.
        2. The judge counts a note on the beat before a chord change against the coming chord too.
        3. The timeline now writes a chord changing inside a bar as its own entry, `{"bar", "beat", "chord"}`
           (format.md already allowed "a beat in that bar"), and the judge reads the changes by step. Power rock's
           "A" all clip was the timeline missing the second chord of "I IV" (and salsa's "i iv"): the guitars now
           measure 100% chord tones. Today's riff plays only roots and fifths (`check_guitar`), so it has no
           passing tones to allow; the card's 90% floor stays until the riff gets them, with a riff source then
           (Wikipedia's "Riff" says nothing on its notes).
        4. The guitar card's register is E2-E5: Wikipedia "Double tracking" (the part taken twice, left and right,
           each its own sound), "Power chord" (octave doubling), "Nashville tuning (high strung)".
        Rerun (seeds 7-9, 16 bars): every clip fits its own style best, 98-100%. Still flagged: synthwave's lead
        (expected), the bass under E1 (power rock D1, synthwave C1: the bass range is C1-G3 for every style, an
        808's floor), salsa's chords at 2.12 a bar against 0.5-2 (the vamp's variants add chords), a few one-offs.
        The checks' first measure (Oct 26) shows the judge too lenient, three points for DadCraft:
        - one wrong member hardly moves a clip's fit, the mean over members (trap 99% to 97% with salsa's bass);
          the swapped bass's own score falls (57-86%);
        - only power rock's drums have a velocity trait, so flattened velocities go unseen elsewhere;
        - every note shifted a 16th: the drums and percussion fall (22-86%), trap's melody barely (96%).
        DadCraft, Oct 26: "yes to all four" (the weakest member, velocity traits, the bass floor, salsa's chord rate
        left as it is), and decision 17 (any member hot-swapped). Done Oct 26:
        - A clip passes when every member scores 80% or more (`judge.weakest`, `judge.passes`); the table names the
          weakest. Each member is scored against its own style: `Member.style` writes `members.<name>.style` in the
          song file and the judge reads it.
        - The bass's floor is its style's (`"lowest"` in the bass's entry, `flow.bass_range`): E1 for power rock,
          salsa and synthwave (their cards' bass guitar, double bass and E1 floor); trap's 808 keeps C1.
        - Velocity: trap's hats get a trait (8-45, from GMD's hip hop hats: 88-107 on the
          beat, 40-56 on the 16ths). Synthwave's drum machine plays flat hats on some seeds (the LinnDrum had no
          per-hit velocity), so no trait there; salsa's percussion and the melodic members have no source with
          numbers yet: open.
        - `tests/unit/test_judge_check.py` (25 tests): today's clips (seeds 1-3) pass and fit their own style
          best; a bass or drummer from another style fails, named as the weakest (8 pairs); a drummer swapped in
          with its own style scores by it, and its style reads back from the file; flattened velocities are named
          (trap, power rock); every note a 16th late leaves the steps and fails (trap's hats roll on every 16th, so
          only its clap's step is named); SynTheory's 19 progressions in 12 keys read back with 100% chord tones and
          the right chord rate, and a timeline a chord late is caught. SynTheory credited (MIT).
        Open, for later tasks: the melody cards hardly tell styles apart (another style's melody scores 75-100%);
        a bass moved into another band can fail its own card, since its notes follow its first band's chords (a
        true hot-swap draws the member over the band's chords: 5.3, 6.2); the riff's passing tones (when it gets
        them, with a source). Every listen from now on gets the judge's table first.
- [x] 3.6 Layering (arrangement): which members play when. Members join one after another along a build and drop
      out as it eases (after Ouralia's Calm builds: pad, room notes, chimes, then harmony and reverb, each joining
      further along the rise; `docs/format.md`), and sections thin or fill the band. Each style's entry says who
      comes in first and who sits out (trap might drop its drums for a breakdown), as tendencies, never a fixed
      order (decision 9). Driven by `form.py`'s energy, with the check and choose like the other theory modules.
      Also a style per section (after HeartMuLa, research round 3, DadCraft, Oct 24): the blend can shift as the
      song moves (the band turns salsa for a breakdown), as tendencies too.
      In bucket 6 it becomes the way Calm builds and Maestro's arc stop stacking (DadCraft, Oct 23).
      From Tangerine (DadCraft, Oct 26: `docs/research.md` round 6), for long plays: **rotation**, every few bars
      (a style's tendency, a little random) one playing member rests and one resting member comes back, so the
      band's size holds while its colour turns; the longer a member has played the likelier it rests, and swaps
      fall on chord changes, never on a cadence. And **slow change**: every so many passes of a loop, one detail of
      one member changes (a hit on or off, a note a step up or down, an octave, an accent), never two members at
      once; how often is a style's tendency.
      Plan (Oct 26), approved; DadCraft chose: proposals 1-5 now (a layer map a style, builds and eases on phrase
      starts, breakdowns taking over the kick drop-outs, rotation, slow change), never fewer than two members,
      synthwave's long clip first (A/B against today); a style per section later.
      Synthwave built Oct 26: `theory/layers.py` (the style book's new `layers`: each member's join energy, the
      spread, least 2, breakdowns, rotate, changes), drawn after every member with its own seed, so the same seed
      plays the same notes with or without it; each phrase's band in the clip's words, a "Band" line in its summary.
      Synthwave: the pad, then the bass at 0.3, the arp at 0.45, the drums at 0.55; breakdowns (35%) to the arp and
      pad; a swap every 16-32 bars, never on a section's first phrase; a slow change every 2-3 phrases. The drums'
      last-bar kick drop stays as it was (a one-bar fill, not a layering choice). Checks: `tests/unit/test_layers.py`,
      fuzz 2000/2000 clean, drift all met, judge 99% (every member 80%+), mix in its targets. Listen:
      `clips/ab/synthwave` (A: 0f50ba5, no layering; B: layered; seed 14, 84 bars, 3 minutes). Heard Oct 26: B
      better; the thinning and filling, the breakdown, the rotations and the slow changes all good; the kick drop
      stays (`docs/verdicts.md`). The other maps approved Oct 26 (`docs/verdicts.md`), one style at a time with an
      A/B each: trap, then salsa, then power rock. Trap's breakdown keeps the melody (the riff), so a breakdown may
      list the melody.
      Trap built Oct 27: the strings from the start, the drums at 0.25, the 808 at 0.4; breakdowns (35%) to the
      strings and riff, the beat cut; rotation every 16-32 bars, a slow change every 2-3 phrases. A breakdown may
      list the melody (a phrase marks itself `down`). Two rules for every style, after trap's drift measure (its
      longest exact copy went from 3-7 bars to 8-12: the strings and riff alone for two phrases, both looping every
      4 bars): the thinnest band holds one phrase, then a member joins; and no breakdown when the phrase before
      already played its band. After them, 3-8 bars; synthwave's seed 14 plays the same band as its approved B.
      Checks: 283 tests (the layering tests run trap too; the 808's kick test uses the plain take, since a resting
      beat leaves the 808 alone), fuzz 2000/2000 clean (trap, synthwave), drift met except trap's "same bar, same
      place" at 2% (it was before too), judge 100% in A and B (the riff's triplets 0% in both). Mix: the 808 and
      drums about 0.5 dB over the riff in A and B alike (levels unchanged; DadCraft, Oct 27: "the 808s are fine").
      Listen: `clips/ab/trap` (A: 4e59e36, no layering; B: layered; seed 74, 84 bars, 2.5 minutes). Heard Oct 27:
      "B is better, keep it" (`docs/verdicts.md`).
      Salsa built Oct 27: its parts lead, so the keys, bass, percussion and horns play throughout (the cuerpo, montuno
      and mambo already say what the lead and horns play); breakdowns (35%) to the piano's montuno over the
      percussion, the melody, bass and horns resting; a slow change every 2-3 phrases, no rotation. Slow change now
      reaches the keys (a hit dropped) and the percussion (a hit dropped or accented), never the clave (nor the
      drums' snare, as before). Salsa's montunos are mostly loud already, so few sections rise into a louder one: a
      breakdown in 9 of 40 seeds. Checks: 287 tests (the layering tests run salsa too; the clave stays as drawn),
      fuzz 2000/2000 clean, drift all met, judge 100% in A and B (A's horns 14% syncopation, B's every trait in),
      mix in its targets, levels unchanged. Listen: `clips/ab/salsa` (A: 4753c5e, no layering; B: layered; seed 12,
      84 bars, about 2 minutes; 3.4c's pair moved to `clips/ab/salsa/3.4c`). Heard Oct 27: "everything sound good"
      (`docs/verdicts.md`).
      Power rock built Oct 27: songs open loud (energy 0.6-0.7 in all 40 seeds measured), so "the guitars first"
      takes a new setting, `opens`: the first phrase plays its own band whatever the energy, the rest crashing in
      after it (skipped when the play is one phrase). DadCraft chose (Oct 27): "guitars alone, then crash" (the
      rhythm guitars and the lead, two members), and the band thinning "only in real calm dips" (the bass joins at
      0.2, the drums at 0.3; drawn at 0.3 and 0.45 the drums sat out a quarter of the bars, now 7%). Breakdowns (35%)
      to the bass and drums, both leads resting (the second lead now rests with the melody), the guitars slamming
      back; a stop inside a breakdown is the bass and drums'. Slow change every 2-3 phrases on the bass and drums, no
      rotation. A breakdown in 15 of 40 seeds. Checks: 292 tests, fuzz 2000/2000 clean, drift all met, judge 94% in
      A and B alike (the second lead's slides and height under target in both, as before), mix: guitar L 0.6 dB
      under its target in B (0.1 in A), the drums now inside theirs. Listen: `clips/ab/power_rock` (A: f415824, no
      layering; B: layered; seed 12, 84 bars, about 2:35; 3.4d's pair moved to `clips/ab/power_rock/3.4d`).
      Heard Oct 27: "B is better, keep it" (`docs/verdicts.md`). Done Oct 27, all four styles layered; a style per
      section stays for later (DadCraft, Oct 26).
- [x] 3.7 Clip summaries: a short summary in plain words for each checkpoint clip (shape agreed Oct 24: style,
      bars, key, tempo; the chords as a loop and how it varies; the bass; the pad; the melody's phrase; a "listen
      for" line). The detailed per-bar explanation stays, for debugging.
      Done Oct 27 (plan approved; DadCraft chose: the mock-up's shape, about a dozen lines, and 2-3 lines for each
      solo clip): `explain.summary` grouped by member across the clip, not by section: a form line (the parts or
      sections, breaks, builds, breakdowns), each chord family once with where it plays and how many rounds vary
      beyond landing home, then each member once ("throughout", "in the choruses", or its bars), moments counted
      ("a fill (5 times)"), the melody, the band, the style's listen-for (unchanged). 8-10 lines in every style at 84
      bars (was 22-36). `explain.member_summary`: a solo clip's three lines (header, the member, a listen-for), for
      Checkpoint 3's solo clips. Test: 12 lines at most at 16 and 84 bars, every member who plays named, solo
      summaries 3 lines; 293 tests pass. Samples: `clips/summaries/<style>_12.txt` (seed 12, 84 bars, with the solo
      summaries).
- [x] 3.8 Checks before every listen (outside reviews, DadCraft, Oct 26: `docs/research.md` round 4):
      - **seed fuzzing:** thousands of seeds a style through the theory modules and the sketch: nothing empty,
        every note on the grid and in its member's range, no choose left with nothing to pick;
      - **a mix check:** each member's loudness in the rendered clip against a target per style, the melody on
        top; levels are set from it before a render, not after a listen;
      - **A/B listens:** when a style has an earlier round, both clips go to DadCraft side by side (same seed and
        bars where they can be), and he says which is better and why;
      - **tests on every push:** a GitHub Actions run of pytest (the parity test skips there: no Ouralia build).
      Which styles each check runs on: decision 18. Done Oct 26. CI: `.github/workflows/tests.yml`. Fuzzing: `tools/fuzz.py` (2000 seeds a style, every style
      clean; 40 a style in the tests). It found the phrase melody over C7, salsa's melody crossing the clave, a
      phrase's first half ending home, and the checks only saying what they ruled out. Fixed, as DadCraft picked:
      the pad gives way under a phrase that runs over C7; a phrase the check rules out (range, ending, clave) is
      drawn again, up to 4 times, then the plain phrase plays (a chord tone a bar, on the clave's hits). The mix
      check: `maestro/mix.py` (BS.1770 loudness of each member alone, against the melody); the targets in the
      style book's "mix" (one default, a style may override); each member's "gain" (dB) in the player's mix. Set:
      synthwave's drums and bass -2, pad and arp -1; trap's 808 -22, kit -17, strings -3. A/B: `tools/ab.py`.
- [x] Listen after 3.8, as A/B. `clips/ab/synthwave` (A: what DadCraft heard, 1bad590; B: the pad and lead 3 dB
      down and today's gains), `clips/ab/trap` (the same notes; B: the riff about 22 dB up against the 808). Oct 26:
      B in both ("cleaner, maybe? less hiss or fuzziness?"). The default mix target holds; no style overrides it.
- [x] 3.9 DNA nudges (DadCraft, Oct 26, from Fase Groove Piano's "Musical DNA": `docs/research.md` round 5). A few
      named directions (more energetic, more minimal, funkier, more soulful, more sophisticated), each one step a
      click. A step shifts the style's tendencies, not its notes: density, syncopation, accents and velocity, chord
      colour, register. It always stays inside the style's ranges (decision 9), so the rules never have to fight it
      (decision 6). It works on one member or the whole band and stacks with a blend (decision 4). Check before a
      listen: each step moves its own measures the way it says, the drift measures still pass, fuzz clean. Plan to
      DadCraft before starting; in bucket 6 it may become a control in Ouralia.
      Plan approved (Oct 27): the directions as planned (energetic: denser, harder accents; minimal: the opposite;
      funky: off-beat hits, accent contrast; soulful: a wider loudness spread, more coloured chords; sophisticated:
      richer colours and more varied rounds, only colours the style lists), five clicks each, opposites cancel;
      synthwave first. Built: `theory/nudge.py` (a nudged style joins the book under its own name,
      `stylebook.derive`, every table built for it), `--nudge energetic=2,bass:funky=1` in sketch, fuzz and drift.
      Register isn't moved yet (the ranges are the theory's, not the style's). Checked: each direction at +3 moves
      its own measures over 12 seeds (`tests/unit/test_nudge.py`), the judge's fit holds, fuzz clean at +5.
- [x] Listen after 3.9 (Oct 27): "energetic sounds fine. minimal doesn't sound very minimal. funky didn't stand out.
      soulful and sophisticated don't sound very different from each other." His calls for the second round:
      minimal thins the band (the energy leans down: members join later, more breakdowns, the calm patterns),
      energetic the opposite; funky may add small pushes in a straight style (the bass's and kick's last hit on a
      beat a 16th early, ghost 16th hats; not in a clave style); soulful is the feel (dynamics, longer notes, the
      lead's bends and vibrato, in any style now), sophisticated the harmony (each loop beside a coloured copy in
      the style's own colours, more colour passes, key changes more often). Even +5 passes the style's judge:
      the floor (pad, bass) joins as before so a short calm play has it, the others later, and rotation swaps less
      (at +5 it brought the drums into calm bars, half time only). Fuzz found an old trap bug on the way: a riff
      round landing home over V sang the tonic against it; it now lands on the chord's nearest tone there.
- [x] Listen after 3.9, round 2 (Oct 27): `clips/nudges` (synthwave, seed 12, 48 bars, plain then each at +4).
      DadCraft: "the nudges are fine." 3.9 done; register nudges stay for later.
- [x] 3.10 The scratch lane (DadCraft, Oct 26, from Fase Groove Guitar: `docs/research.md` round 5). The rhythm
      guitar gets a lane of muted, unpitched scratch strokes that fills the empty 16ths between its chord hits by
      itself: palm-mute chugs in power rock, funk scratch where a style asks for it (afrobeat, later). It's a
      tendency in the style entry (how often, on which 16ths, how loud), never on top of a chord hit, and it eases
      off in stops and builds. Check: never under another hit, in its mix target, fuzz clean; then an A/B against
      the guitar without it. Plan to DadCraft before starting; it may join power rock's next round.
      Plan approved (Oct 27): "power rock only, heavier sections". Built: a `scratch` entry in power rock's guitar
      (`theory/guitar.py`, wired in `explain.py`, with its own seed so every other note stays put): in a phrase
      from energy 0.45 up (not the opening phrase), short palm-muted root strokes fill free 16ths, likeliest
      either side of the backbeat, 18 under the hits (velocity 52 against 78); none in a stop, the bar before one,
      or a build. The chorus and drive patterns ring through every 16th, so in practice it lands in the heavier
      verses. Checked: `check_scratch` (never under a ringing note), 4 new tests, fuzz 2000/2000 clean (and
      energetic+5), mix and judge unchanged (99% fit).
- [x] Listen after 3.10 (Oct 27): `clips/ab/scratch` (power rock, seed 16, 84 bars; A without the lane, B with it,
      in bars 9-24). DadCraft: "B sounds better, keep the scratch lane." 3.10 done. Open, his call when: strokes in
      the chorus would need its patterns' chords shortened.
- [x] 3.11 Chord moves by shared notes (DadCraft, Oct 26, from Tangerine: `docs/research.md` round 6). Where
      the style's families leave a choice (the next family at a section, a variant, a key change), the closer move
      is likelier: chords counted by the notes they share, keys by the scale notes that differ (0 for the relative
      key, up to 7). A **distance** tendency in the style entry sets how far the harmony likes to travel (calm
      sections near, a lift further), always inside the style's families (decisions 6, 9). Check: the shared notes
      at each change measured against the style's distance, drift measures pass, fuzz clean; then an A/B against
      today's draws. Plan to DadCraft before starting.
      Plan approved (Oct 27): "synthwave first, gentle". Built: a `distance` entry in synthwave's
      `harmony.progressions` (calm 2, home 1, turn 0, lift -1: near above 0, far below) leans three choices
      (`theory/form.py` `lean`, `notes_apart`; `theory/flow.py` `shared`): the key move at a section (scale notes
      apart), the family after a seam (notes its first chord shares with the chord heard last), a swapped chord
      (notes shared with its neighbours). Closeness is read against the choices on offer, so the nearest weighs at
      most twice the farthest. Odds from A minor: a calm move to the relative key 67% -> 80%; a Lift's semitone
      lift 33% -> 41%. The seam lean does little in synthwave (nearly every loop opens on i). Other styles name no
      distance and play bit for bit as before (300-bar plays compared). 9 new tests (`test_distance.py`), 316
      pass; fuzz 2000/2000 clean, drift met, exam 106/106. Key changes sit 3 minutes apart, so the A/B is long:
      `clips/ab/distance` (seed 10, 240 bars; A 0fe729e, B distance): bar 121, a Calm, A goes down a fifth to D minor, B to the relative C major; bar 217, a Lift, A goes home to A minor, B a tone up to D major. The play is drawn before its parts, so after a different key draw the rest of B is a different roll too (drums, arp). Judge 99% and mix the same on both (drums -3, as before).
      Heard Oct 27: "the distance sounds good to me." 3.11 done. Other styles' distance waits for their rounds.
- [x] 3.12 Loops of different lengths (DadCraft, Oct 26, from Tangerine: `docs/research.md` round 6). A member's
      loop can run a length other than the bar (an arp of 5 or 7 steps against the bass's 16), so the parts meet in
      new places each time round, with accents carrying the pulse. A style's tendency (which members, which
      lengths); the loops line up again at each section or cadence so the form stays clear. Synthwave's arp and
      calm sections first. Check: every loop back in line at its section, notes on the grid and in range, drift
      measures pass, fuzz clean; then an A/B. Plan to DadCraft before starting.
      Plan approved (Oct 27): calm sections only, back in line each phrase, beats louder. Built: a `loops` entry
      in synthwave's arp (lengths 3 or 5, weights 1 and 2; accent 30). In a calm section the shape is cut or carried
      round to that many notes (`theory/flow.py` `arp_part`), counted from the phrase's start instead of each chord,
      so it meets the bar somewhere new and is back in line each phrase, always on its chord's tones. Off-beats
      softer in those sections (`sketch.py`): 76 on the bar, 70 and 64 on the beats, 58 between (were 70-76). The
      length is drawn from its own seed, so the rest of the play is note for note the same; other styles too
      (300-bar plays, all five, compared with the hash seed fixed). 7 new tests (`test_arp_loops.py`), 323 pass;
      fuzz 2000/2000 clean, drift met, exam 106/106. A/B: `clips/ab/loops` (seed 10, 48 bars; A 7ba3f7a, B loops):
      only the calm section, bars 17-32, differs (a loop of 3, up and down cut to 0 1 2). Judge 99% and mix the
      same on both. Found: power rock seed 3's bass and drums differ between runs (set order under Python's hash
      seed), before 3.12. Fixed Oct 27 (DadCraft: "commit the power rock seed 3 fix"): the layer plan drops members
      in sorted order, so each draws its jitter the same whatever the hash seed (a test runs three hash seeds).
      Heard Oct 27: "B sounds better, keep the loops." 3.12 done. Other members and styles wait for their rounds.
- [ ] Checkpoint 3 (decision 16: a sound baseline per style, not a finished one; fine-tuning waits for the desk):
      each member in each style, by ear; plus a long clip and two plays of the same settings, with the
      drift measures passed first. Ask DadCraft whether the on-grid band sounds too robotic; if so, the reserve
      pocket (decision 13) can be played to him next to the on-grid version. Ask too whether the chord rounds change
      too much or too little, on the long clip (open from the listen after 3.2). Also for his ear, from 2.5: the
      semitone key lift, how sections growing heavier comes across, and the layering (3.6).
      Plan approved (Oct 27): one style a session (synthwave, trap, salsa, power rock), plain only as a reference,
      the pocket A/B built now. Built: `maestro/checkpoint.py` writes a style's set to `clips/checkpoint3/<style>`
      (the full 84-bar play with its summary and the judge's table; each member alone, the 16 bars of that play
      where it plays most, with its 2-3 lines; the pocket clip; a second play; a 240-bar play; plain). The reserve
      pocket is `Song.pocket` / `sketch --pocket MS`: one draw per step from its own seed, shared by the band, only
      in the written MIDI, so the notes and the judge are unchanged. 2 new tests, 326 pass. Synthwave (seed 12):
      judge 99% on all three plays, only the melody's register high (E5-E6, an open point for the desk); drift
      met; the mix's drums about 4 dB loud, as before.
      Synthwave heard Oct 27: "i'm good with how all of them sound": every member, the second and long plays, plain
      for reference. Synthwave passes as a baseline. He didn't ask for the pocket, so the band stays on the grid
      (decision 13) and the pocket stays in reserve.
      Trap's set built Oct 27 (seed 12): judge 100% on all three plays (the long play's riff triplets 4%, under
      5%), mix in target, drift met over 20 minutes. On the 84-bar files two misses, both the measure's: the riff is
      counted as a melody (file mode doesn't apply `--flow`'s riff rule; a 3-line fix), and 3 of 85 bars match
      between the two plays (1% over 20 minutes).
      **Generic, Oct 27.** DadCraft on trap's set: "all of this sounds painfully generic, across all the genres. the
      trap bass and drums are dialed in, but everything else... ehhhh." Then: maybe "the sounds and mastering",
      maybe "the notes occasionally sound like they're rushing ... tripping over themselves". Checkpoint 3 paused.
      What was found (measured, nothing changed yet):
      - The tripping: the motif's "diminish" move (`theory/form.py`, "twice as fast") can apply to a motif already
        sped up, so 8ths become 16ths, then 32nds, for long stretches; `check_motif` only refuses notes under a
        32nd. Melody 32nds: synthwave 119 of 395 (`clips/checkpoint3/synthwave/1_full_12`, about 0:24-0:51 and
        1:09-1:24), power rock 86 of 381 (`clips/ab/power_rock/2_B_now_12`, 0:26-0:37, 1:26-1:45), salsa 35 of 177
        (`clips/ab/salsa/2_B_now_12`, 0:31-0:45). Trap's riff has none; its triplets over straight hats (one
        beat every few bars) are the only candidate there. Clean: no member's notes overlap, nothing off the grid,
        bass and pad never faster than 16ths; the near-hits against the drums are trap's hat rolls.
      - The sounds: trap's riff and strings are FluidR3 GM (`play.py`); only the 808 and the kit are Maestro's own
        synths, the parts he called dialed in.
      - Why generic (Opus): the parts drawn from real music (GMD grooves, the 808) are the ones that land; the
        rule-written melody, pad and harmony are correct but middle-of-the-road. Bucket 4's practice MIDI from the
        style book would teach a model the same thing.
      Proposed, waiting for his call: (1) "diminish" only down to 16ths, A/B on synthwave, the rest of the play
      unchanged; (2) the same notes through better, openly licensed sounds next to today's, trap first, to tell
      notes from sounds; (3) his moments ("file, time, what's off") and a reference track or two per style, kept
      in `inbox/`, ideas only; (4) then likely: stop Checkpoint 3's style-by-style listens, move the spike (S) to a
      melodic member, and rethink bucket 4's sources (real music to MIDI, the desk) with the style book as the
      guardrails. Not decided.
      **(1) done, Oct 28** (DadCraft: "yes to 1"). `check_motif` refuses a note faster than a 16th (`FASTEST`), so
      "twice as fast" stops at 16ths. Synthwave seed 12's melody: 104 notes a 32nd apart, now none; tests, exam
      106/106, fuzz 2000/2000 on four styles and drift all pass. With one shared seed any melody change also redraws
      the arp and drums, so the A/B `clips/ab/sixteenths` is his clip with only the melody track swapped (judge 99%
      both). Found on the way: a slow change (task 3.5) could drop the tumbao's "and of 2" and cross the clave, in 15
      of 80 salsa seeds before, seed 12 among them (so `clips/ab/salsa` likely has it); `slow_changes` now skips a
      dropped hit that crosses. His listen (Oct 28): "the melody still moves. doesn't sound like it's tripping over
      itself": (1) passes.
      **(2) built, Oct 28** (DadCraft: "all three"). Trap's checkpoint clip (seed 12, 84 bars), the same MIDI three
      ways in `clips/ab/sounds_trap`; only the bell riff and the strings change, the 808 and kit stay Maestro's own.
      A: today's FluidR3 GM. B: GeneralUser GS v2.0.3 (MuseScore General, first pick, is FluidR3 reworked, so too
      close to A). C: Maestro's own `fm bell` and `dark strings` (`synth.py`). Gains set so all three meet the mix
      targets alike (the melody level with the drums, the pad 6-8 dB under). His listen (Oct 28): "they still sound painfully generic and meandering. the sounds might be part of
      the problem, but they aren't the main culprit." (2) answered: mostly the notes.
      Asked for his moments (Oct 28): "it's the whole thing. nothing about it sounds convincing", like an alien
      rebuilding a box from a description, "you can tell how it's supposed to be representative ... but it's just
      all wrong." No moments to give; (4) is on the table, his call.

### S. A first model spike (draft; before D; DadCraft, Oct 26; brought forward onto a melodic member, decision 19)
Buckets 1-3 are rules; the risk is bucket 5 (little open data for our styles, 8 GB to train on). A short test of a
learned model finds out what buckets 4 and 5 need before the desk and the training data are built (outside reviews,
`docs/research.md` round 4).
- [ ] S.0 Plan approved: one member (the drums from Groove MIDI, CC BY 4.0, or a member from the style book's practice
      MIDI), the smallest MIDI-GPT-style model that can learn it, a few days' work at most.
- [ ] S.1 Train it on this PC and play it inside the rules (decision 6); measure 5.0's success measures and the time
      to make a bar (decision 15).
- [ ] Checkpoint S: DadCraft hears it blind, A/B against the rule-made part. What it shows (data, size, tokens) goes
      into the plans of buckets 4 and 5.

### D. Maestro's own desk (draft; after S, before bucket 4, decision 14)
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
      what it took away. Then the style fine-tuning that decision 16 left for the desk (salsa's fuller horn section,
      synthwave's lead register, Maestro's own metal sounds, ...) is his to do there.

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
- [ ] 5.0 Plan approved, with the success measures set first (outside reviews, Oct 26), so the model earns its
      place over the rules' seeded choose: how often the checks reject its suggestions (too often and it's a
      bottleneck), how often it picks what choose rarely would (too rarely and it's a thin coat over the rules),
      DadCraft's blind A/B, and the time to make a bar (decision 15). The spike (S) tries them first.
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
      The plan also settles the live inputs (outside reviews, Oct 26): how Ouralia's room, movement and the user's
      own changes steer Maestro; smoothed, landing on phrase or section boundaries, holding a while before going
      back, and which one wins when the user and the room disagree.
- [ ] 6.1 Shrink the model for the phone; measure CPU, battery and the time to make a bar, with the rules'
      fallback (decision 15): a bar ready well before it's due at the fastest tempo (salsa's 180), nearly always.
- [ ] 6.2 `dcs_composer` gains a style and a sound per member, swappable; rules as guardrails; the new roles
      (decision 11) get members and kits in Ouralia.
- [ ] 6.3 The drift measures on the phone (fresh seed each play; the patch's Pd `[random]`s and `expr random` are
      unseeded today, so they repeat after each app start: `docs/format.md`).
- [ ] Checkpoint 6: trap drums with a synthwave bassist, on the phone (beta build); off and on again gives a new
      evolution.
- [ ] 6.4 DadCraft (and beta testers) play the beta; it goes into Ouralia proper only when DadCraft deems it ready.

## Verdicts and notes
DadCraft's verdicts and the notes on each finished task are in `docs/verdicts.md` (grep it; don't read it whole).
