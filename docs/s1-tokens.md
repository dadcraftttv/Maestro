# S.1 token codec v1

`maestro.spike.tokens` freezes the S.0 corpus codec. No training library is imported.
Encode/decode are behavior-identical to `private/s0a/token_check.py`; v12 stays frozen.
The representation is ordered structured event records (lists), with typed fields below.
The historical 423,836 scalar count counts each tag and field, with eight chord fields
per CHORDS record; it is not the number of event records or a vocabulary size.

| Record | Fields, in order | Domain / meaning |
| --- | --- | --- |
| BAR | bar | Absolute nonnegative source bar index; consecutive within a sequence |
| CHORDS | four (root, quality) pairs | Beat order; root 0–11, quality below |
| NOTE | position, relative pitch, duration, velocity, tie-in, tie-out | Position 0–95; pitch -11–127; duration 1–96; velocity 0–7; ties 0/1 |
| REST | position, duration | Position 0–95; duration 1–96, fills gaps |
| END | none | Sequence terminator, also the empty history |

One beat is 24 ticks; a 4/4 bar is 96. Input notes are `[start, end, MIDI pitch,
coarse velocity]`, sorted and monophonic; end is exclusive. Coarse velocity is
floor(source MIDI velocity / 16). Pitch is MIDI pitch minus the key tonic pitch
class, retaining octave; it is not scale degree or pitch class. Supported spelled
keys and their tonic classes are the frozen `TONIC` mapping in the module. Unknown
corpus key (`None`) uses tonic 0 for pitches, while conditioning retains `None`.
Do not silently label an unknown key C major.

Chord quality vocabulary, in fixed order: `aug`, `dim`, `dom7`, `half_dim7`, `maj7`,
`major`, `min7`, `minor`, `sus2`, `sus4`. Chord roots retain absolute pitch classes,
matching the old codec. CHORDS is optional; when present it follows BAR and holds
exactly four beat labels. Confidence/PCS metadata are not tokens. BAR's absolute
index is an integer field, not a separate learned symbol for each corpus bar.
This freezes the event/field vocabulary; tensor IDs and batching are not introduced here.

A window `[lo, hi)` clips notes at its boundaries. Across bars, ties preserve one
continuous note, pitch and velocity. A first note may tie in from before the window;
a final note may tie out. Rests cover all remaining ticks, including empty bars.
Encode returns absolute BAR indices and one END. Decode merges ties and returns
clipped absolute-time notes. The historical assertion checks are preserved: this
is a trusted corpus codec, not a complete validator for arbitrary generated streams.
For example END placement, MIDI bounds and all tie flag combinations are not fully
validated. Step 4 must mask grammar violations and run Maestro's existing checks;
never treat successful decoding alone as musical acceptance. Assertions must be enabled.

`condition(notes, chords, key, bar, run_start, register, density)` returns controls
for the target bar:

- `upcoming_chords`: the target bar's four known beat chords, available before generation.
- `key`: a supported spelled key, or explicit unknown (`None`).
- `register`: requested inclusive MIDI range `(low, high)`, 0–127.
- `density`: requested number of note onsets in the next bar, 0–96; a continuation
  tie is not an onset. It is a control, not a claim about the eventual output.
- `previous`: encoded preceding **eight** bars, shortened only at the eligible run
  start. `history_bars` records the actual count; zero history is `[END]`, with no
  fabricated silent padding. No history crosses a run boundary or a piece.
- `bar_in_phrase`: proposed reproducible proxy `(bar - run_start) % 8`, zero-based.
  The corpus has no phrase annotations. This is a mechanical eight-bar cycle,
  reset at each eligible run, not a recovered human phrase boundary. Use the same
  run anchor at inference; do not reset it for each sliding history window.

Register and density are explicit caller controls: never infer them from the target
melody during validation or generation. The private check uses fixed `(0,127)` / 4
only to exercise the API, not to define training controls. Piece key is supplied
metadata, not inferred by this function. Prior tied sustains can cross the target
boundary; target onsets and their velocities are never read for conditioning.
Training windows must remain within their piece's frozen split. No genre tags.

Checks: public fixtures test exact events, transposition, ties, clipping, rests,
empty/nonzero windows, existing decoder rejections, conditioning controls and causal
history. Private `private/s1_prep_step2/check.py` compares public events against the
original codec on all complete v12 melodies and eligible runs, round-trips every
window, and checks history/control causality for every eligible bar. It reads v12
without rewriting it; the report includes the corpus SHA-256. Run from repo root:
`PYTHONPATH=. .venv/bin/python private/s1_prep_step2/check.py`.
