# Maestro verdicts and notes

DadCraft's verdicts and the notes on each finished task, oldest first. Moved out of `PLAN.md` on Oct 24 so it
isn't reloaded every session; grep for the part a task needs.

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
- Oct 23: 2.6 done. `tests/exam/exam.py`: our own theory exam, 106 questions over pitch, chords, voicing, rhythm and
  form, as knowledge or reasoning (MusicTheoryBench's split, none of its questions), each answer worked out by hand
  and given with why in plain words; `python tests/exam/exam.py` prints the score card (`--all` every question). It
  found one slip, now fixed: the blues scale's blue note was spelled D# in A, now Eb (the flat five). Score 106/106;
  the test fails on any wrong answer (a question the library can't answer yet is marked as a gap). `maestro/explain.py`:
  a few bars drawn one choice at a time (section and energy, chord and its function, pad and bass moves, the bass
  rhythm against the clave, the motif's development), each in plain words, for checkpoint 2's spot check
  (`python -m maestro.explain salsa --seed 7`). It needed a chord vocabulary per style, which 2.2 hadn't drafted:
  `chords.VOCAB` (trap: dark minor, borrowing harmonic minor's V and phrygian's bII; synthwave: borrowed bVI bVII
  iv, sus and add9, maj7; salsa: diatonic plus secondary dominants, sevenths and sixths; power rock: power chords,
  borrowing from mixolydian and minor). In the passage a section leans to open on its tonic and a tension chord to
  land where it points (12 times as often), never a must. For DadCraft: the style vocabularies, and the passages.
- Oct 23: DadCraft approved the 2.6 style vocabularies ("vocabularies look good").
- Oct 24: look back on Maestro with DadCraft. Nothing had been heard yet, so the clip player moves up to 2.7 (drift
  measures 2.8). Decision 14: Maestro is his own local model, taught away from Claude Code through a local web page
  (bucket D, after the style book becomes data files in 3.1), no Claude budget to use or train it; sources
  license-checked first, which he can hand to Claude. He confirmed the PC model is the big one and the phone model
  its distilled form, the evolution of `dcs_composer`.
- Oct 24: DadCraft: training with Claude stays possible, but away and offline is critical; Claude and he keep
  shaping Maestro as it's used. The reader should be as good as it can be: the best local models, a team of them,
  free APIs as an optional online boost (decision 14, D.0, D.2). The verdict log moved here from PLAN.md;
  Conductor's `items.md` keeps being updated per task as before.
- Oct 24: task 2.7, the clip player. DadCraft chose FluidR3 GM (MIT) for the sounds over the thin TimGM6mb and
  Ouralia's own Pd sounds (the player judges the notes; Ouralia's sounds come in bucket 6), and the baseline first:
  today's composer as clips now, the style clips with checkpoint 2. On the phone the melody and walking notes come
  from the listener (chimes standing, walking notes walking), so a baseline clip stands for its first half and walks
  for its second. Measured before he listens: every note on the grid, melody and walking notes in the key, bass in
  the patch's 65-131 Hz, the WAV the clip's length and about 5 dB under clipping.
- Oct 24: DadCraft heard the baseline clips: "they all sound like a theme that evolves and comes back changed to
  some degree. the chords feel like they do move and eventually come back home. the timing overall feels ok", but
  the chime/lead seems to come in "just a hair after the drums", and at points each part seemed to slow down, which
  made the small desync more noticeable. Measured: in the WAV every part starts within ~7 ms of its grid time (the
  drums 2-7 ms), one tempo, no drift from the start of a clip to its end; so not a timing error in the file. Likely
  causes: the vibraphone's soft attack is heard later than a drum hit, and the clip's own melody pacing (a silent
  breath bar every 4th bar, then long dotted notes) feels like slowing. Three sync test clips (`clips/sync`: drums
  and the lead in unison on vibraphone, xylophone, square lead) to tell them apart.
- Oct 24: DadCraft on the sync test clips: "they all sound like they're in sync with the drums" (vibraphone too), so
  the lead's sound alone isn't it. In the baseline clips the lead always starts a bar on the downbeat and nearly
  every note lands on a kick or snare. Next: four versions of clip 1's first 16 bars (`clips/ab`: as heard, no
  pad, xylophone lead, no breath bar) to find what in the mix makes it feel late. `baseline.clip` gained `breath`.
- Oct 24: DadCraft on the A/B clips: "they both now sound in sync. i'm not sure what i heard before, if nothing
  changed." Nothing had: the baseline WAVs he first heard are the same renders. Closed with no change; if a lag
  shows up again, he notes the clip and the second, and that spot gets measured. 2.7's listen done.
- Oct 24: task 2.8's drift targets, confirmed by DadCraft ("targets look good, keep drums and bass uncapped"):
  within a play, band 4-bar phrases copied <= 10%, longest exact copy <= 8 bars, melody bars copying one of the
  last 16 <= 30%, new band bars >= 25% in every 2-minute window; between two plays, same bar in the same place
  <= 1%, 4-bar phrases shared <= 5%, longest shared run <= 4 bars. Drums, bass (and pad) are shown, never capped.
- Oct 24: checkpoint 2 started. DadCraft chose a sketch player for the style clips (the theory core's choices
  played, with a bare drum guide, over reading only or no drums) and style tempos in one key (trap 140, synthwave
  100, salsa 180, power rock 130, all A minor). Measured on 1,200 sketches before he listens: every note on the
  grid, the melody above the pad, no part crossing the clave unless the words say so, the WAVs 3-7 dB under
  clipping. Fixed on the way: the pad had no ceiling and climbed into the melody (now under F5, and the melody
  keeps one register a clip); the pad was voiced without the bass and could be muddy (now the bass comes first and
  the pad is drawn again, up to 10 times); a 9th chord left the 3-note pad silent (now 4 notes then); the motif
  ignored the clave (now a statement moves a bar later to sit with it, said in the words). Still in: about 1 bar
  in 300 stays muddy after 10 draws ("ruled out" in the words), and salsa's draft piles up secondary dominants.
- Oct 24: DadCraft heard the checkpoint 2 clips: "that sounded rough, but i guess that's supposed to be the case";
  the chords don't move the way the styles do ("i can hear how each one is *supposed* to be indicative of it's
  respective style, but it's a long way off"); the melody "very short and it's hard to judge from just those short
  runs". On the explanations: "i'm having trouble digesting that ... none of them really sounded like what they
  should be for their respective styles ... very rough and there didn't seem to be any flow". Checkpoint 2 closed
  (his choice). Carried into 3.0: (1) no flow: the core draws each chord one bar at a time from the vocabulary,
  with no idea of a progression; a style needs its progressions and loops (as families of tendencies with many
  variants, decision 9), a bass line built on its pattern (tumbao, 808 slides, root eighths) rather than random
  onsets, and a melody shaped over a phrase; (2) the melody is judged on long clips at checkpoint 3; (3) the
  per-bar explanation is too dense to listen against: a checkpoint needs a short summary per clip in plain words
  (the detailed one kept for debugging), to be agreed with DadCraft in 3.0.
- Oct 24: DadCraft has lists of theory sites (some known only by name) and music AI systems to sort. Confirmed:
  a source sort before the style book plan (3.0a, lists in a gitignored `inbox/`), and Maestro checks licenses
  itself (decision 14): its reader finds and quotes the notice, a fixed rules table decides the tier, anything
  unclear is not usable until he looks; Claude applies the same table until the desk exists.
- Oct 24: task 3.0a, DadCraft's lists sorted (36 sites, 19 named references, 20 AI systems; portals opened set by
  set). The rules table uses data.md's tags (SAFE, NC, OUT, CHECK), narrowest license first. Found: few open sources
  near the four styles (the Rock Corpus, CC BY but copyrighted songs, so statistics for the book only; jazznet,
  MIT; CoCoPops, NC); TheSession's license forbids any use with LLMs (OUT for Claude and the reader); three named
  sets don't exist under those names (TIV drumming, choro, Balinese gamelan); most of the list is off-target.
  Open for DadCraft: the off-target sources (keep for the reader or drop), asking the CCML lab to license MCFlow
  (rap flow), and the research proposals.
- Oct 24: DadCraft: keep the off-target sources for Maestro's reader ("i want as much training data for it
  later"). Then, before 3.0: find the theory and open data the four styles need now.
- Oct 24: task 3.0, bucket 3's plan approved as presented (PLAN.md 3.0): a style entry is one JSON file a style
  (time, harmony with progression families and harmonic rhythm, each member's ranges and pattern families, fit and
  form, checks); a new task 3.2 Flow for Checkpoint 2's "no flow", then the drummer and percussion (3.3), the four
  styles (3.4), the judge (3.5), layering (3.6), clip summaries (3.7). DadCraft also chose: a listen after 3.2
  (one style, 16 bars) before the four entries are written; the clip summary shape as shown (style, bars, key,
  tempo; the chord loop and how it varies; bass; pad; the melody's phrase; a "listen for" line); and two round-3
  proposals into bucket 3: a style per section (HeartMuLa, in 3.6) and TinyMU as a second judge (3.5, license
  first). The other round-3 proposals come up in buckets 4-6's plans.
- Oct 24: task 3.2's plan approved as presented (progressions as families with variants and a cadence a phrase,
  the bass on its style's pattern family, the melody shaped over the phrase; `theory/flow.py`, switchable). DadCraft
  chose salsa for the listen after 3.2, and an 8-bar phrase (statement, answer left open, the opening again,
  answer landing home).
- Oct 24: the listen after 3.2 (`clips/flow/salsa_23`, 16 bars). DadCraft: "it feels more like salsa! the clave
  and bass are a nice feel, and it sounds like the lead does go round and come home. yes, it feels like it's going
  through a question and answer or call and response." On too much or too little change from round to round: "i
  can't tell" (asked again at checkpoint 3, on a long clip). "this was big step in the right direction for salsa,
  but there's still a long way to go."
- Oct 24: 3.3's plan approved, with DadCraft's choices: salsa gets the percussion member and no kit (as a salsa band
  plays); percussion for salsa now, the other styles' in 3.4; GMD feeds the drummer as groove families plus per-step
  odds, varied each bar; a listen to salsa and power rock at the end.
- Oct 24: 3.3 done. Notes: GMD's punk takes left out (5 straight takes, the lining-up misreads its skank beat), so
  power rock draws on rock only; 63 swung rock takes left out (our four styles are straight); a long jam capped at
  32 bars a take. The cáscara's bars set against the clave by where they meet its strokes (sources disagreed). The
  kick and bass are measured (the share of bass notes the kick lands with), not ruled. Seen in the drift sweep, from
  3.2 and not this task: salsa's melody now and then lines up with the other clave over a 32-bar clip (seeds 30, 40);
  for 3.4c.
