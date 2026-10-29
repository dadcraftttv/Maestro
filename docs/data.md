# Data audit

Every candidate set for Maestro: license, tag, size, format, and the styles and members it covers (task 1.2,
Oct 23). Licenses were checked on each set's own page on Oct 23. Check them again when downloading (task 4.1).

Members are Ouralia's band today (`format.md`): **melody**, **bass**, **pad** (chords) and **drums**. The first
styles add **guitar**, **keys**, **horns** and **percussion** (PLAN.md decision 11), with no open data in these
styles either, so the style book fills them the same way.

**Tags** (PLAN.md decision 7):
- **SAFE:** allows commercial use. Fine for the phone model.
- **NC:** non-commercial. PC only (experiments, research, the style judge), kept apart, never in the phone model.
- **OUT:** not for training. Ideas only.
- **CHECK:** license or source not clear yet. Not used until it is.

### OpenScore source check (Oct 28, S.0a v3)

DadCraft approved both MusicXML downloads (about 59 MB): [OpenScore Lieder](https://github.com/OpenScore/Lieder)
and [OpenScore String Quartets](https://github.com/OpenScore/StringQuartets). Both repositories' README and
LICENSE.txt state CC0-1.0; both request credit and a link for public-facing use. CC0 allows commercial reuse
within the affirmer's rights; underlying compositions, revisions and arrangements still require screening.
These are local inventory/listening candidates, not blanket training clearance. Voice/piano and quartet parts
can supply independent lead/accompaniment; use accompaniment-derived chords, never invented melody harmony.
Pinned URLs, per-file checksums/provenance and detailed licence findings stay in `private/s0a_v3/` and
`private/sources/`. Nottingham's reuse permission and music21 encoding rights remain unresolved; The Session's
current custom licence prohibits LLM processing, so it is excluded. Mutopia needs per-piece PD/CC0/CC BY evidence;
SA/NC remain excluded. No other source corpus was approved or ingested.

### OpenScore reader/recount (Oct 28, S.0a v4; Claude reviewed and accepted Oct 28)

DadCraft approved music21 as a local library-only converter (`data` extra pinned to 9.9.2), and then selected
"Install MuseScore CLI for the 12 files" for its import failures. The portable 3.6.2 fallback and virtual
display stay local; no system packages changed. Neither tool's bundled music is used. All 1,658 approved
score hashes pass. Conversion grows from 341 to 1,432 (1,259 Lieder / 173 quartets), including two checked
MuseScore exports; every v3-readable score remains readable. The adapter counts notes, merges ties, preserves
grace groups under a fixed timing rule, aligns pickups and converts transposing instruments to sounding pitch.
All 37 differing note lists among the 341 shared files have timing causes recorded per file; 304 match exactly.

Unchanged musical gates yield 49 OpenScore candidates (45 Lieder / 4 quartets), versus four in v3. After the
23 v3 rights cuts, two-copy work cap and frozen-split/uploader isolation, the complete corpus has 550 pieces,
483 families and 10,529 usable bars (33,551 notes; 396,789 scalar tokens). Eight copies are removed; one new
score is quarantined for an uploader/split conflict. Existing surviving placements are preserved. Count-only
3/4 and 6/8 screens yield 31 and 18 additional candidates before duplicate/isolation checks; none are included.

Claude Code inspected all 41 new pieces (Oct 28): CC0 OpenScore transcriptions, composers died by 1924, no
third-party arrangers; none cut. DadCraft passed the ten new-v4 listen pairs (Oct 28: "snapping didn't hurt anything"). The 226 conversion rejections (mostly unresolved tie continuity) describe current reader limits,
not a corpus ceiling or proof the sources are invalid. Full funnels, per-file credits/checksums, comparison
causes, fixtures, cap/quarantine lists and checked listen pairs remain in `private/s0a_v4/`. No additional
source-music download, musical-gate relaxation, PyTorch or training was approved.

### Pickup bars in MusicXML (Oct 29, S.0a v11; Claude Code)

An unflagged short first or last XML bar now counts as a pickup/final bar when the MIDI has the same short
bar. 20 melody-only scores align instead of 4, but the new passes are duplicates or capped extra copies of
songs already in the corpus; the one new song, Greensleeves (score 4810739 and two copies), is a Frank Nordberg
musicaviva.com transcription whose chords are his setting, so it is cut. DadCraft then dropped After You've Gone
(156119): the corpus is **592 pieces / 517 families**, 494/50/48, identical to v9. `private/s0a_v11/REPORT.md`.

### Written MusicXML chords (Oct 29, S.0a v10; reviewed by Claude Code)

DadCraft approved downloading PDMX's `mxl.tar.gz`; 1,894,335,797 bytes, published MD5
`49ffd75ecf5489c0be6d41182eb11ff7` verified. Streamed only the 387 previously rights-cleared scores.
Melody-only scores can now use explicit harmony roots/kinds/basses at their written offsets, held to the
next symbol and sampled at each half-bar start. Extensions are dropped into the existing vocabulary;
unsupported/altered-core chords remain unlabelled. Labels carry `window: symbol`, null confidence/margin.
Accompanied scores retain v9 labels. XML/MIDI measure boundaries, meters and note onsets must agree;
no guessed pickup padding, repeat expansion or grace timing.

Of 111 melody-only chord failures, 43 have harmony symbols (1,196 of 1,197 mapped), four align; 68 have
none and 39 are cut for uncertain alignment. Two Twinkle copies are duplicates/capped; an intro explicitly
credits Pee-Wee Ellis and is cut. Added **After You've Gone**, score 156119, Creamer/Layton 1918, encoding
by uglybeauty, declaration publicdomain: 20 bars / 87 notes. Metadata names Marion Harris as artist but
names no recording source or arranger; XML credits Creamer/Layton only. Claude Code kept it: no stated source or arranger, so the rules
retain it. Thirteen previously cleared candidate settings cut for third-party editions,
recording sources or modern contributors; none was frozen in v9.

**593 pieces / 518 families**, split 495/50/48; 11,254 bars / 35,990 notes / 424,222 scalar tokens.
All 592 v9 records/splits exact; checksum, cap, family/uploader, codec and listen checks pass; 327 tests pass.
Only one new train listen pair is available: `private/s0a_v10/LISTEN_S0A.md`; its pad plays symbol labels.
Full inventory, rights calls, alignment cuts and replay steps: `private/s0a_v10/REPORT.md`. No training.

### Whole-bar chord fallback (Oct 29, S.0a v9; Claude Code)

A half bar whose accompaniment gives no confident chord now takes its whole bar's label under the same v3 test;
a silent half holds the other half's label. Each label records its window (`half`, `bar`, `hold`) so training
can drop or down-weight the fallbacks. No chord is taken from the melody. Same candidates and rules as v8;
three additions (Camptown Races 1850, Twelve Days of Christmas from Austin's 1909 printing, Danny Boy 1913):
**592 pieces / 517 families**, split 494/50/48; 11,234 bars / 35,903 notes. The 589 v8 records are unchanged.
111 of the 113 remaining chord failures are single-line melodies with no accompaniment in the MIDI; chord
symbols, where they exist, are only in PDMX's MusicXML (downloaded and tested in v10 above). `private/s0a_v9/REPORT.md`.

### Compatible bar runs and traditional songs (Oct 29, S.0a v8; reviewed by Claude Code)

DadCraft's four approved loosenings retain source-declared 4/4/2/2/paired-2/4 runs of at least four bars,
accept exact normalized titles with metadata extras and missing composer fields, admit uploader settings,
and tag traditional tunes separately when a printing ≤1925 is cited. Every new piece also needs ≥4 usable
bars and ≥8 lead notes. Third-party undated settings, soundtracks and recording transcriptions stay cut.

Final: **589 pieces / 516 families**, split 491/50/48; 11,206 bars / 35,740 notes / 421,895 scalar tokens.
Nine additions (164 bars / 596 notes), sparse Danny Boy 61265 removed (two bars / one note). Surviving 580
baseline records and placements unchanged. PDMX rights screen 387 → meter 191 → lead 152 → final musical 22;
six already frozen, six cap cuts, one held-out-family quarantine, nine kept. No new Mutopia/IMSLP additions.

Nine traditional tune dates are separately tagged `date: traditional`; secondary dates remain independently
removable. Fourteen priority traditional titles researched; five remain unresolved under the printing/tune
identity requirement. All final encodings are inherited consistent PD/CC0, with no source downloads or scans.
Rights review must check inferred own settings 5984045 (Tristan Tran/ttranman77), 6341482 (background recording
link not described as transcription), 5962248 (unqualified uploader arrangement). Lutkin 5930552 setting is
[dated 1914 by Rochester](https://urresearch.rochester.edu/institutionalPublicationPublicView.action?institutionalItemVersionId=21578).

Seven new train original/snapped pairs, including two traditional and five meter-run pieces; requested eight
unavailable under split rules. Source/codec/cap/family/uploader and exact-baseline audits, eight boundary
checks, 327 tests and independent audio checks pass. No DadCraft sound verdict or training approval.
Full manifests, cuts, reproducible funnel and guide: `private/s0a_v8/REPORT.md` and `LISTEN_S0A.md`.

### Looser local song screen (Oct 29, S.0a v7; reviewed by Claude Code)

DadCraft authorized 2/2, paired 2/4, explicit pickup trimming, constrained skyline leads, two-bar chord
runs and cited secondary publication dates ≤1925 with named creators. Encoding licenses and decision 7 stay.
Seven verified + 333 secondary-dated songs; secondary entries are tagged `date: secondary` and removable
as a group. No recording years used. All local v6 candidates accounted for; 1,549 consistent PDMX encodings
and five licensed local Mutopia MIDI members rerun. No new source files obtained.

Six additions: Chicken Reel (5919666), Twelfth Street Rag (5860188), Happy Birthday remake (5915185),
Danny Boy (61265), Camptown Races (6320642), Mutopia 1034 Nearer My God to Thee. Added 55 usable bars /
212 notes / 2,550 scalar tokens. Final 581 pieces / 507 families, split 485/49/47; 11,044 bars /
35,145 notes / 415,091 scalar tokens. All 575 complete baseline records and placements exactly preserved.
Four new train audio pairs; requested eight unavailable, and the second rebarred 2/4 piece is validation.
Two skyline and three secondary-dated train pieces covered. Danny Boy's two usable bars contain one lead
note; usefulness awaits DadCraft's judgment. No sound verdict or training approval.

327 tests, ten gate fixtures, all source/codec/cap/family/uploader checks and four audio-pair checks pass.
Skyline: ≤10% polyphonic onsets (held notes included), C3–C6, ≤24-semitone span, at least eight onsets.
Secondary dates and own-arrangement readings need Claude Code review; Happy Birthday tune/lyric date
scope especially. Third-party Cartwright, Anke Held, soundtrack and fake-book settings remain excluded.
Details, every per-piece bar loss, date citations, rights/cap cuts and replay scripts:
`private/s0a_v7/REPORT.md`; listening guide `private/s0a_v7/LISTEN_S0A.md`.

### Song-title screen (Oct 29, S.0a v6; reviewed by Claude Code)

Claude Code's review (Oct 29): 1975051 clears (1859 tune, uploader's own arrangement); 575 pieces stand.
DadCraft (Oct 29) judged the screen too strict; S.0a v7 loosens meter, lead, chord and dating rules (PLAN.md).

Applied v5's Hallelujah cut first: 574 retained pieces. Correct literal-quote TSV parsing preserves all
1,401 leads; 455 library rows dropped, 91 classical rows counted, 11 non-song/medley rows excluded.
844 song rows merge to 628 identities. Seven pre-1931 publications independently checked; 356 secondary
catalog date leads remain insufficient by themselves for admission, 237 dates unknown, 24 creators unknown,
one homonym/date conflict, three verified later publications. Recording years never substitute for publication.
Most first-publication research remains unresolved; these exclusions are not proof the songs are unavailable.

Local PDMX title/song/composer/artist search finds 1,838 loose candidates; Mutopia 12 and IMSLP four.
Title hits include homonyms and artist-name false positives. Diagnostic preflight of 1,549 consistent PD/CC0
PDMX encodings yields 26 musical passes, all individually reviewed. The verified-rights PDMX funnel is
10 scores → 10 parsed → seven 4/4 → four fixed lead → two chord-run/snapping passes. One verified-rights
Mutopia score fails chord runs; IMSLP admits none. Two old Twinkle settings credited to Mozart are correctly
aliased to the anonymous French tune, keeping their validation placements; they cap out the new setting.

One new hymn arrangement, PDMX 1975051, adds four usable bars / ten notes. Lowell Mason's Bethany setting
has an independently cataloged 1859 publication; the uploader describes writing their string-quartet arrangement
in first person. Claude Code accepts that authorship reading. Final: 575 pieces / 503 families,
split 481/47/47, 10,989 bars / 34,933 notes / 412,541 scalar tokens. All 574 old musical records, evidence
and splits preserved; cap 2 without exception, family/uploader isolation, source hashes, codec round trips,
327 tests and one original/snapped train listen pair pass. New styles: hymn one; ragtime/popular/blues/folk zero.

Three independently dated songs have no local metadata hit: Oh Lady Be Good, My Melancholy Baby, Someone to
Watch Over Me. Another 218 secondary date leads lack hits; their dates still need verification. These are
metadata-search results, not proof of source-wide absence or a confirmed 221-song scan backlog.
Per-song dates/citations, rights and identity exclusions, diagnostics and checks: `private/s0a_v6/REPORT.md`.
Listen: `private/s0a_v6/LISTEN_S0A.md`. No source-music downloads, YouTube access, scans or training.

### Permissive catalog screen (Oct 28, S.0a v5; reviewed by Claude Code)

Claude Code's review (Oct 28): all 25 Mutopia additions clear; IMSLP's zero accepted. One baseline Hallelujah
copy (5783003) is cut so the two-copy cap holds with no exception: 574 pieces. V6 applied
`private/s0a_v5/claude_review_cuts.json` before its screen. The 575 figures below are Codex's v5, before that cut.

DadCraft approved the TiMauzi IMSLP MIDI CC0 download and Mutopia metadata plus per-piece PD/CC0/CC BY
music. IMSLP is pinned to Hugging Face revision `703e983510885d9833dd1c534900e0eb258b69af`;
Mutopia's repository index to `2144afd6f52d56c5b6995b8b589ef1268b3139f0`. Website snapshots, hashes,
per-piece provenance, exclusions and scripts stay in `private/s0a_v5/`; no source music is committed.
Mutopia website content is separately checksummed; the repository revision does not pin generated website files.
The collection label alone does not clear an IMSLP file: 817 license fields are missing and 296 say CC0.
Source-page evidence must resolve composition and arrangement rights. Mutopia SA/NC/unclear entries are excluded;
permitted encodings still require composition/arrangement checks. Existing v4 musical gates and frozen 550
placements remain in force. No PyTorch or training.

Mutopia's live catalog has 2,123 entries (previously quoted: 2,124). Rights-screen passes: 1,058;
two MIDI URLs return 404. The other 1,056 entries supply 3,396 MIDI members, including movements and parts.
After byte deduplication: 3,361; parsed: 3,358; all-4/4: 914; fixed lead: 182; chord/snap passes: 33;
resolved song identities: 29; kept after cap: 25. Four Giulio Cesare candidates have unresolved movement
mapping. Rights cuts: 765 SA, 204 unresolved composer dates, 36 needing composition grants, 58 unresolved
arranger grants/dates, 2 unresolved transcriber credits. Missing evidence is not proof of legal unsuitability.
IMSLP contributes zero: original-file provenance verification encounters a human challenge; its 817 null
licenses and 296 CC0 rows remain excluded pending composition/arrangement evidence.

Added 461 usable bars / 1,388 notes. Final provisional corpus: 575 pieces / 502 families, split 481/47/47;
10,990 usable bars / 34,939 notes / 412,609 scalar tokens. All 550 old musical records and splits survive.
Work keys distinguish OpenScore songs within collections and Hensel from Mendelssohn. Improved aliases reveal
three baseline Hallelujah encodings, all in train; the preserve-550 instruction takes precedence, so this
explicit cap exception needs Claude's correction. All three new Hallelujah proposals and Invention 13 are cut.
Other works meet the two-copy cap; work/family/uploader split checks pass. Mutopia's Dvorak B.150 opus typo
is corrected in derived identity with a composer-catalog reference; raw source metadata remains intact.

Count-only native-meter diagnostics before cap: 45 in 3/4, 6 in 6/8; none admitted. In 4/4, 149 fail only the
chord-run gate; 732 without a lead have unassessable chord/snapping gates. Counts describe MIDI members,
not independent works. Kept catalog style labels: 9 Romantic, 10 Baroque, 5 Classical, 1 Technique; mostly
voice/orchestra, violin with piano/orchestra, plus quartet/organ/contrapuntal ensemble/piano exercise. This
adds little contemporary target-style coverage and does not establish sufficient training diversity.

All codec round trips, independent baseline/family/split checks, ten new train original/snapped audio pairs
and the 327-test suite pass. DadCraft's v5 sound verdict remains open. The pinned IMSLP shards total
50,519,503 bytes and match upstream LFS SHA256s; Mutopia website files have separate snapshot hashes.
PyArrow 23.0.1 was added only to the local venv to read Parquet. Per-piece manifests, exclusions, rights
uncertainties, checksums, listening guide and replay details: `private/s0a_v5/REPORT.md`.

### Corpus-size follow-up (Oct 28, DadCraft; for Claude Code review)

DadCraft asked about other datasets and the gigabytes of music available, concerned that 537 pieces seems small.
**537 was v3's pipeline candidate yield, not the available-data ceiling or proof of sufficient training
data.** The combined 10,224 usable bars permit a feasibility experiment; adequate musical variety/generalization
has not been demonstrated. Overlapping training windows and transpositions do not add independent compositions.

The limited custom MusicXML reader rejected 1,317 of 1,658 approved OpenScore files before musical screening.
Grace timing, pickups and ties are major implementation limits; subsequent transcriber-as-arranger exclusions
also need interpretation review. These counts do not establish musical or legal unsuitability. Codex's
recommendation: use a mature notation converter (OpenScore documents batch conversion), resolve transcription
versus arrangement metadata, and review extraction policy before treating this yield as a corpus-size estimate.
Keep rights checks; do not silently remove grace notes, thin polyphony or weaken chord checks to increase counts.

Further sources/opportunities from that discussion (the v5 download approval above supersedes the earlier
restriction for IMSLP/Mutopia only; no training approved):
- Revisit [PDMX](https://arxiv.org/abs/2409.10831), over 250,000 scores: separate fixed lead, 4/4 and accompaniment
  chord coverage are deliberate narrow gates. Better conversion/extraction may recover more; any policy changes
  require explicit review, and per-piece rights still matter.
- [TiMauzi IMSLP MIDI CC0 collection](https://huggingface.co/datasets/TiMauzi/imslp-midi-cc0-1.0): 1,113 entries,
  about 50.5 MB download in its dataset card; advertised PD/CC0 with source/provenance URLs. Investigate original
  piece/encoding rights and duplicates before use; a dataset label alone is not clearance.
- [Mutopia](https://www.mutopiaproject.org/): 2,124 pieces listed, with MIDI and editable LilyPond notation.
  Build a per-piece PD/CC0/CC BY manifest; exclude SA/NC under the existing brief.
- Commissioned or contributed original MIDI with explicit permission could fill target-style gaps. This is an
  option, not authorization to contact contributors, spend money, or generate a synthetic substitute corpus.

Large collections do exist, but audio bytes are not equivalent to usable symbolic notes/harmony; audio would
need a separate transcription/representation plan. [GigaMIDI](https://huggingface.co/datasets/Metacreation/GigaMIDI)
is CC BY-NC 4.0 and [Google MAESTRO](https://magenta.tensorflow.org/datasets/maestro) is CC BY-NC-SA 4.0;
neither fits the current commercial phone-model rules. No change to those rules was requested. DadCraft asked
that this discussion be logged for Claude; no new extraction policy, dependency install, downloads or training
was approved by this follow-up.

### PDMX download recheck (Oct 28, third proof)

Checked the [v9 source record](https://zenodo.org/records/15571083) and its API metadata before score use:
dataset license CC BY 4.0. The maintainers report 31,221 internal/public license disagreements and recommend
`subset:no_license_conflict` (222,856 entries). Require that flag, `license_conflict=False`, `is_original=True`,
valid MIDI, and inspect selected titles/composer metadata for copyrighted arrangements; the flags alone do not
establish authorship. This is a local listening experiment, not training or a blanket clearance of the corpus.
Only the catalog and MIDI archive are requested initially; selected files and provenance stay in `private/pdmx_proof/`.
No source music is modified for stage (a); GM synthesis changes its presentation. Scores will not be quantized or
reduced before DadCraft's first listening checkpoint. CREDITS.md already records the dataset attribution.

#### Third-proof stage (a) selection

Catalog, MIDI and metadata archives match the v9 record's MD5 values. Four candidates use CC0 score metadata,
`is_original=True`, `license_conflict=False`, and `subset:no_license_conflict=True`. Ratings are screening
signals, not musical verdicts. Archived author descriptions support originality; no independent authorship
verification is claimed. The catalog's flags alone are insufficient: flagged “original” entries included
Nintendo covers and commercial-song arrangements, which were excluded from this proof.

| Piece / composer | Rating (count) | Why selected / archived author statement | Original source |
|---|---|---|---|
| Film music / Isaac O'Shea | 4.56 (4) | Film-music tag; describes first coursework composition; piano baseline | https://musescore.com/user/9465681/scores/5826459 |
| Creepy Title Theme Concept / Daniel Neufeld | 4.91 (9) | Original game-title concept explicitly described by author; contrasting piano mood | https://musescore.com/user/137765/scores/5912795 |
| The Little Boat / Joshua Sommer | 4.85 (4) | Author describes composing for a short film; full orchestral contrast | https://musescore.com/user/6624501/scores/5851806 |
| 6 Cinematic Scenes (Storyteller) / Brayden Meng | 4.66 (3) | Cinematic tags, six-scene original narrative described by author; second orchestral example | https://musescore.com/user/29636574/scores/5597356 |

Only supplied MIDI is rendered, unchanged, using the existing FluidR3 GM player. This does not independently
verify score-export fidelity or reproduce live performance. Local source metadata, exact filenames, MIDI hashes,
measurements, listening guide and WAVs are in `private/pdmx_proof/`; no training and no source music committed.
DadCraft must accept stage (a) before any mapping. Dataset attribution remains in CREDITS.md.

#### Third-proof stages (b)/(c), Oct 28

DadCraft accepted all four faithful renders. The local reduction uses fixed lead/bass staves and merges the
remaining pitched notes into a pad capped at five simultaneous voices; percussion, zero-duration notes, duplicate
overlapping pad pitches and excess voices are omitted. Notes are octave-folded into the three members' registers.
Controllers,
bends and original program changes are removed, including piano sustain. Timings, durations, velocities and
tempo changes of retained notes are identical between (b) piano and (c) synthwave. The fixed lead does not track
orchestral melody handoffs. Exact per-piece loss accounting and merged source-track lists are local in
`private/pdmx_proof/stage_bc_report.json`, with mapped note provenance and MIDI files. No quantization or training.
The existing synth functions and effects are called through a local adapter respecting the full tempo map;
the production synth player assumes one tempo. Both mapped stages and a copy of (a) are loudness matched,
with separate matching for previews. Guide: `private/pdmx_proof/LISTEN_BC.md`. DadCraft's listen (Oct 28): phrases,
harmony and development still convince after reduction; synthwave sounds preserve the music, but the instruments
still sound generic. The third proof passes; model/data suitability still needs the planned spike.

## Symbolic (MIDI, scores)

| Set | License | Tag | Size | Format | Styles | Members | Status |
|---|---|---|---|---|---|---|---|
| Groove MIDI (GMD) | CC BY 4.0 | SAFE | 1,150 files, 13.6 h; MIDI-only 3 MB (with audio 4.8 GB) | MIDI + synthesized WAV, CSV | 18 drum styles: afrobeat, afrocuban, funk, hip hop, jazz, latin, rock, reggae, pop, soul... | drums (human, with feel) | **chosen**; **in use** (3.3, Oct 24: license re-checked, MIDI-only zip in `private/gmd`, counts in `maestro/data/grooves.json`) |
| Expanded GMD (E-GMD) | CC BY 4.0 | SAFE | 45,537 sequences (1,059 unique), 444 h, 43 kits; MIDI-only 103 MB (with audio 90 GB) | MIDI + WAV, CSV | as GMD | drums | **chosen**, MIDI only |
| PDMX | CC BY 4.0 (scores public domain) | SAFE | 250K+ scores, 14.4 GB | MusicXML (MXL), MIDI, MusicRender JSON, PDF; CSV with genres and ratings | mostly classical, folk, hymns, film/game arrangements; genre column | melody, bass, pad (harmony, voice leading); few drums | **chosen**: only the `no_license_conflict` subset (222,856); 12% have license conflicts, dropped |
| imslp-midi-cc0-1.0 (TiMauzi, HF) | CC0 catalog; per-file evidence unresolved | CHECK | 1,113 files, 50 MB download | parquet holding MIDI, with era, style, key | classical, romantic, some "modern" | melody, bass, pad | **screened v5: none admitted** (817 missing licenses; 296 provenance unresolved) |
| Aria-MIDI | CC BY-NC-SA 4.0 | NC | 1,186,253 files, 16.6 GB | MIDI + metadata.json (genre, composer; "may vary") | piano, all kinds (transcribed from audio) | melody, pad, bass (piano) | **chosen for PC only**; its find-transcribe-filter idea goes into 4.3 |
| MAESTRO | CC BY-NC-SA 4.0 | NC | ~200 h piano | MIDI + audio | classical piano | melody, pad | candidate, PC only; Aria-MIDI covers it |
| Lakh MIDI, and sets built from it (Slakh2100, MidiCaps) | fan MIDI of copyrighted songs | OUT | 174K+ files | MIDI | pop, rock, all kinds | all | never (decision 7) |
| GigaMIDI, MetaMIDI | scraped, "research under fair dealing" | OUT | 1M+ files | MIDI | all kinds | all | never, same reason as Lakh |
| POP909, DadaGP | arrangements/tabs of copyrighted songs | OUT | | MIDI / Guitar Pro | pop, rock, metal | all | never, same reason |
| Weimar Jazz Database | "open access", no clear license | OUT | ~456 solos | own format, MIDI | jazz | melody (solos) | transcriptions of copyrighted recordings: ideas only |
| Chord sets of copyrighted songs (Chordonomicon, Hooktheory) | scraped / site terms | OUT | | chord text | pop, rock, all kinds | pad, bass | ideas only (chord habits per genre, as written sources for the style book) |
| GiantSteps drum patterns | not stated | CHECK | | | EDM, house, techno, breakbeat | drums | ask or skip |

## Audio (to transcribe into MIDI in task 4.3)

A recording has two rights: the composition and the recording. Both must be open.

| Set | License | Tag | Size | Format | Styles | Status |
|---|---|---|---|---|---|---|
| FMA (Free Music Archive) | metadata CC BY 4.0; audio per track (the artist's choice) | per track: CC0 and CC BY are SAFE, BY-NC is NC, ND is OUT | small 7.2 GiB, medium 22, large 93, full 879 GiB; 106,574 tracks, 161 genres | MP3, CSV | modern: electronic, hip hop, rock, pop, experimental... | **best modern candidate**; filter by each track's license (confirm the column in 4.1) |
| SoundSafari Public-Domain-Music (HF) | tagged CC0, no dataset card | CHECK | ~5,180 MP3s | MP3 | mixed, said to come from FMA | check each track against FMA's own license before use |
| MTG-Jamendo | metadata CC BY-NC-SA 4.0; audio per track; "solely for non-commercial research" | NC | 55K+ tracks, 195 tags; 156–508 GB | MP3, TSV | modern, many genres, instrument tags | PC only (the style judge, research) |
| WaivOps HH-TRP | CC BY 4.0 | SAFE | 15,000 loops, 55 h, 22.3 GB | WAV + JSON labels | trap: drill, trapsoul, cloud rap, emo rap | **chosen** (DadCraft), trap drums (made by a program, not humans; MIDI not published) |
| WaivOps EDM-TR8 | CC BY 4.0 | SAFE | 3,790 loops, 9 h, 4.4 GB | WAV, BPM labels | EDM, TR-808 | **chosen**, EDM drums (made by a program) |
| WaivOps RTRO-DRM | CC BY 4.0 | SAFE | 2,138 clips | WAV | 1980s electronic (synthwave drums) | **chosen**, synthwave drums (made by a program) |
| Freesound | per file: CC0, CC BY, CC BY-NC | per file | huge | WAV etc., API filter by license | modern loops and stems, all kinds | candidate: CC0 and CC BY loops via the API |
| ccMixter | per track, many NC | per track | | MP3, stems | modern, beat-driven | candidate, per track |
| Musopen | per recording, many public domain | per track | | MP3/FLAC | classical | low priority (PDMX already has classical scores) |
| Citizen DJ (Library of Congress) | public domain (US recordings published before 1926) | SAFE | thousands of clips | audio | early jazz, blues, opera, classical | low priority; old, noisy recordings |
| Great 78 (Internet Archive) | mixed; the labels sued the Archive over it (2023) | OUT | 400K+ records | audio | early 20th-century popular | keep out |
| MusicCaps | captions CC BY-SA 4.0; audio is YouTube clips (copyrighted) | OUT | 5,521 clips | captions only | all kinds | not "public domain" as `music-info.md` says; no audio to train on |

Other tools: **MusicBrainz** (CC0 metadata, no music) can check dates and credits. **Synthetic music from an AI model**
(e.g. ACE-Step output) is OUT, ideas only (DadCraft, below).

## Coverage and gaps

| Style | drums | bass | pad | melody |
|---|---|---|---|---|
| classical, folk, hymns | (few) | PDMX, IMSLP | PDMX, IMSLP | PDMX, IMSLP; Aria (NC) |
| jazz, blues, soul, funk, gospel | GMD, E-GMD | **gap** | **gap** | **gap** |
| rock / power rock, punk, pop | GMD, E-GMD | gap | gap | gap |
| hip hop, rap | GMD | gap | gap | gap |
| trap, crunk | HH-TRP (audio loops) | gap | gap | gap |
| EDM, future bass | EDM-TR8 (audio loops) | gap | gap | gap |
| synthwave, chillwave | RTRO-DRM (audio clips) | gap | gap | gap |
| ambient | none needed much | gap | gap | gap |
| afrobeat, highlife | GMD | gap | gap | gap |
| salsa, latin, afro-cuban | GMD ("latin", "afrocuban") | gap | gap | gap |

**The big gap:** no open symbolic data exists for bass, pad or melody in any modern or popular style. Every large
MIDI set of pop music is fan MIDI or transcriptions of copyrighted songs (OUT). Drums are the only member covered
across many styles. **Since decision 19 (Oct 28)** the notes come from real music and the rules are the guardrails:
practice MIDI from the style book would only teach the rules back, so it's no longer a gap-filler for training. The
gaps are filled by:
1. **Human-written open scores** (PDMX): melodies and chords first, starting with the melodic spike (PLAN.md S.0).
   They carry phrasing, harmony and development, not modern styles.
2. **Open audio turned into MIDI** (4.3): the FMA CC0 and CC BY tracks (electronic, hip hop, rock), CC0 and CC BY
   Freesound and ccMixter loops, transcribed with Demucs → Basic Pitch → Beat This!. The second proof showed
   transcription alone isn't enough as the main source (PLAN.md decision 19).
3. **The style book** (bucket 3): each style's own theory per member, which drives the rules and guardrails.
4. **Music DadCraft gives the desk** (4.5), tagged and licensed.

Salsa and afrobeat have the least modern open audio. Expect them to lean most on the style book's rules and on music given to the desk.

## DadCraft's answers (Oct 23)

1. **Synthetic music from other AI models** (e.g. ACE-Step output): **OUT, ideas only** ("lets stay legally safe").
2. **Programmatic drum loops** (WaivOps HH-TRP, EDM-TR8, RTRO-DRM): **yes**, SAFE, as a supplement to GMD's human
   drumming, credited in `CREDITS.md`.
3. **Theory fills the gaps** (his idea): see "Filling the gaps with theory" below.

## Filling the gaps with theory (DadCraft, Oct 23)

DadCraft asked whether theory about the lacking genres can fill their gaps. Yes, and it is legally clean: describing
how a style works (a trap hi-hat roll, a salsa bass that lands ahead of the beat) is an idea anyone can use. Only
specific songs are protected. How it works:

1. **The style book (bucket 3) writes down each style's own theory, member by member**, from written sources
   (open textbooks, articles, our own listening notes). Examples of what an entry holds:
   - **Trap drums:** hi-hat rolls in triplets, 32nds and faster, a half-time snare on beat 3, 808 kicks that also
     carry the bass. **Trap bass:** long 808 notes that slide, mostly on the root and the fifth.
   - **Salsa:** the clave pattern sets everything. The bass is a *tumbao*: it skips beat 1 and plays just ahead of
     beats 3 and 4. The piano plays a repeating *montuno* figure in octaves.
   - **Future bass:** wide 7th and 9th chords, often stacked over one held bass note, rhythmic chord stabs, and big
     tension-and-release moments.
   - **Synthwave:** steady eighth-note bass, simple minor chord loops, long held pads under singable leads.
   - **Afrobeat:** guitar and keys play short interlocking parts, the bass repeats long riffs, the drummer keeps busy
     on the hi-hat.
2. **Each entry is tendencies and ranges, not fixed patterns**, so decision 9 holds: the music never plays the same
   way twice.
3. **The style book generates practice MIDI (task 4.2).** For the gap members (bass, pad and melody in every modern
   style) this is their main training data. It is ours, so it is SAFE for the phone model.
4. **DadCraft checks it by ear:** short clips per style and member in checkpoint 3.

## DadCraft's source lists, sorted (task 3.0a, Oct 24)

His lists of theory sites, named references and AI systems, sorted with the rules table (`maestro/data/licenses.json`,
decision 14; tags as above). Each notice was read on the source's own page, repo or record on Oct 24; portals were
opened and their sets checked one by one. **Use:** *book* = a source for the style book now (3.x); *reader* = for
Maestro's own reader later (bucket D); *data* = training data (bucket 4); *ideas* = read for ideas only; *drop* = not
used. *Off-target* = none of the planned styles (classical, early, folk or regional traditions); kept as reader
material only if DadCraft wants those styles later.

### Strongest for the style book now
| Source | Notice | Tag | Holds | Use |
|---|---|---|---|---|
| Rock Corpus (deClercq, Temperley): rockcorpus.midside.com | "can be used under the terms of the CC BY 4.0 License" | SAFE license, songs copyrighted | chord progressions and melodies of 200 rock songs, analysed | book: progression statistics in our own words (the "no flow" carry); not training data (decision 7, like the chord sets above) |
| music-theory-data: github.com/seancolsen/music-theory-data | CC-BY-SA-4.0 | SAFE | scales, chords, intervals as data | book: checks our scale and chord tables |
| jazznet: github.com/tosiron/jazznet | MIT | SAFE | generated piano chords, arpeggios, progressions | book, data: progressions; salsa's ii-V and sevenths |
| Radif Corpus: zenodo 10.5281/zenodo.15742125 | CC BY 4.0 | SAFE | 228 Iranian radif pieces, MIDI, MusicXML | off-target; reader |
| Drum Groove Corpora (Empirical Musicology Review, 2021) | "CC 4.0" (which one not said) | CHECK | onset timings of pop and rock drumming | for the drummer (3.3) once the license is named |
| CoCoPops (Billboard, Rolling Stone): github.com/Computational-Cognitive-Musicology-Lab/CoCoPops | CC BY-NC 4.0 | NC | melody and harmony of 949 pop and rock songs | book (ideas, PC side): pop and rock progressions; never the phone model |
| MIT OCW 21M.383 Computational Music Theory | CC BY-NC-SA (OCW) | NC | course on music21-style analysis | reader |

### Theory sites and papers
| Source | Notice | Tag | Use |
|---|---|---|---|
| musictheory.net lessons | "© 2000-2025 musictheory.net, LLC" | OUT | ideas (basic theory, nothing new to us) |
| teoria.com | CC BY-NC-ND 4.0 | OUT (ND) | ideas |
| MusicTheoryBench (HF m-a-p) | "license: cc" (no version) | CHECK | already the model for our exam (2.6), no questions copied |
| JSD jazz structure dataset (TISMIR 131, listed twice) | article CC BY 4.0; data: audio of copyrighted recordings | CHECK | the annotations' own license to be checked |
| "A corpus and a modular infrastructure for ... (an)notated music" (Sci Data 2025, PMC12052250) | article CC BY-NC-ND | OUT | ideas; the corpus is checked on its own if wanted |
| S3 symphony dataset (ISMIR 2024 LBD 37) | none in the paper | CHECK | off-target |
| Dilemmadata (zenodo 19661224): AugmentedNet + Distant Listening Corpus as pitch arrays | CC BY-NC-SA 4.0 | NC | off-target (classical analysis) |
| music21 (BSD), mido (MIT; docs CC BY 4.0), maialib (GPL-3.0) | code licenses | SAFE | tools: mido in use; music21 library-only converter approved Oct 28 for S.0a v4; maialib ideas |
| TransFolk (MIT), folk_ngram_analysis (CC BY 4.0) | code licenses | SAFE | ideas (folk n-grams); off-target |
| Tegridy MIDI Dataset | Apache-2.0 on the repo; holds Lakh and fan MIDI | OUT | never (decision 7) |
| MCFlow, Regional Hip-Hop (CCML) | none | CHECK | rap flow and rhyme: the only hip hop sources; ask the lab for a license |
| SymbTr (makam) | CC BY-NC-SA 4.0 | NC | off-target |
| Hooktheory API | "Hooktheory © 2026", site terms | OUT | ideas (chord trends per genre), as already in this audit |
| Cantus Database | CC BY-NC (site) | NC | off-target (chant) |
| fasola.org (Sacred Harp) | "Copyright © 1995-2025" | OUT | off-target |
| Josquin Research Project, wandelweiser.de, newmusicnotation.com, itma.ie | none found | CHECK | off-target |
| The Mod Archive | site ©; each module's license is its author's | CHECK | tracker music (chiptune, early EDM): only modules with their own open license, checked one by one |
| GitHub topic "computational-musicology", UVA music guide | lists, not sources | - | each linked source on its own |

### Portals, set by set (the ones near our styles)
| Set | Notice | Tag | Holds |
|---|---|---|---|
| OpenMIC-2018 | cc-by-4.0 (Zenodo) | SAFE | instrument labels for audio clips (for a judge, not for parts) |
| Harmonix Set | MIT file, but "users must agree to the License" before the data | CHECK | beats and structure of 912 pop songs |
| GiantSteps MTG Key | none | CHECK | keys of 604 EDM excerpts |
| McGill Billboard, iRb jazz, EWLD, Isophonics, RWC, MedleyDB | none, restricted or research-only | CHECK / OUT | pop, rock, jazz chords and structure |
| JAAH (jazz harmony) | cc-by-nc-sa-4.0 | NC | 113 jazz tracks, chords aligned to audio |
| Lakh, BitMidi, MIDI Man, Band-in-a-Box files | fan MIDI of copyrighted songs | OUT | never (decision 7) |
| CCMUSIC (Chinese pop and instruments) | the repo says CC BY-NC-ND 4.0, Zenodo says CC BY 4.0: contradicts | CHECK | Mandopop set is under a company agreement: OUT |
| CompMusic (26 sets) | site CC BY-NC-ND 3.0; sets one by one | - | all off-target (Indian art music, makam, jingju) |
| musoRepo's 27 classical, early and folk sets | not checked | - | off-target |

### Named references (no URL given)
| Name | Found | Tag |
|---|---|---|
| TheSession.org data (github.com/adactio/TheSession-data) | its license allows commercial use but **forbids any use with large language models**, including reading it with LLM tools | OUT: neither Claude nor Maestro's reader may process it |
| Nottingham Folk Tunes (github.com/jukedeck/nottingham-dataset) | GPL-3.0 | SAFE, off-target (folk) |
| Persian Radif | the Radif Corpus above | SAFE, off-target |
| Indian Art Music, Turkish Makam, Beijing Opera | CompMusic's sets above | off-target |
| VGMusic collection, VGM chiptune (NES-MDB), SNES SPC database | transcriptions and rips of copyrighted game music | OUT (decision 7), whatever the code license |
| DadaGP | tabs of copyrighted songs | OUT, as already in this audit |
| MuseScore registries | user scores, mixed rights | PDMX is their open part (SAFE, above) |
| Essen Folk Song Database, CCARH (KernScores), Lost Voices, neume pipelines | research sites, no clear license | CHECK, off-target |
| MusicXML repository (W3C) | the format's samples, no license on the repo | a format reference, not data |
| TIV African Drumming Dataset, Choro Music Symbolic Dataset, Balinese Gamelan Notation Archive | **not found**: no dataset by these names (a choro corpus exists in one 2025 paper, unreleased; El Bongosero is a hand-percussion set to check instead) | - |

### For the four styles now (searched Oct 24, DadCraft: "how much can you find for those things we need now?")
| Need | Found | Tag | Use |
|---|---|---|---|
| Progressions, loops, pop schemas (all four styles) | Open Music Theory (viva.pressbooks.pub/openmusictheory): popular music part with loops and four-chord schemas | SAFE: "licensed under a Creative Commons Attribution-ShareAlike 4.0 International License, except where otherwise noted" (DadCraft read it on the site, Oct 24; Gotham, Gullings, Hamm, Hughes, Jarvis, Lavengood, Peterson, 2023). Each chapter used is checked for its own note first (the rules table's "except where noted") | book: progressions, loops, schemas, form; credited in CREDITS.md when used |
| Progressions in folk and pop | Chord Progression Handbook (Matney, Niemuth, KU ScholarWorks 2019) | NC (CC BY-NC 4.0) | reader; ideas for the book |
| Tumbao, guajeo (montuno), clave, salsa's sections | Wikipedia's articles on them | SAFE (CC BY-SA 4.0, text) | book: theory in our own words, credited |
| Rock progressions | the Rock Corpus (above) | statistics only | book: used in 3.4d (Oct 26), `tools/rock_stats.py` counts the RS 200's timed chord lists (one analyst's, dt) into `maestro/data/rock.json`; the files stay in `private/rockcorpus` |
| Sevenths, ii-V, progressions | jazznet (above) | SAFE | book, data |
| Drums: rock, hip hop, latin, afrocuban, funk | Groove MIDI and E-GMD (chosen, above) | SAFE | data (3.3) |
| Afro-Cuban drums | ClaveNet (2024): GMD grooves with Afro-Cuban seed patterns swapped in; no data release found | - | ideas: the same trick on our own grooves |
| Hand percussion (congas, bongos) | El Bongosero (ISMIR 2024): paper CC BY 4.0, data license not stated | CHECK | percussion, once its license is found |
| Pop and rock drum timing | Drum Groove Corpora: the article says "CC 4.0", its footer CC BY-NC 4.0 | CHECK (likely NC) | - |
| Trap (808 lines, hat rolls) | only commercial MIDI packs (royalty-free for songs, no dataset rights) | OUT | none: written from theory |
| Synthwave (progressions, arps, bass) | blog guides only (eMastered, Unison), all rights reserved | OUT | ideas only; DadCraft's own logs (`taste.md`) stay the best source |
| EDM multitrack | Extended GigaMIDI (CC BY-NC 4.0) holds scraped MIDI | OUT (decision 7) | none |

**So:** open *data* for the four styles is close to none beyond drums (GMD) and jazznet's generated chords. Open
*written theory* covers the basics (progressions, schemas, tumbao, clave, montuno) well enough for the style book.
Trap and synthwave rest on theory written from what's known about them and on DadCraft's own production notes,
then the practice MIDI made from the book (task 4.2), as planned in "Filling the gaps with theory".

### What it adds up to
- For the four styles, one openly licensed source of real rock progressions (statistics for the book, not training
  data), one with sevenths and ii-V habits (jazznet, generated, SAFE),
  and NC pop and rock harmony (CoCoPops) for ideas on the PC side. Trap, synthwave and salsa still have no open
  harmony data: their entries are written from theory (as planned, "Filling the gaps with theory").
- Hip hop's only sources (MCFlow, Regional Hip-Hop) have no license; asking the lab would open them.
- Most of the list is off-target (classical, early, folk, regional traditions): kept for Maestro's reader
  (DadCraft, Oct 24), each still under its own tag.

## Trap, a closer look (Oct 24, before 3.4a)
DadCraft: "a deep dive on anything we can use for training and/or theory on trap, if only to help inform how 3.4a
goes." Searched GitHub, Hugging Face, Kaggle, Zenodo, Freesound, FMA, ccMixter, Music Theory Online, Open Music
Theory and Wikipedia; licenses from each source's own page, contents from samples.

**Training data.** No open trap MIDI exists: every trap MIDI set found is a commercial pack (royalty-free for
songs, no dataset rights: OUT), fan MIDI (Lakh and its offspring, MidiCaps, Los Angeles MIDI: OUT, decision 7) or
NC. What there is:

| Source | License | Tag | What | Use |
|---|---|---|---|---|
| GMD hip hop | CC BY 4.0 | SAFE | human hip hop grooves | in use: trap's drummer at half time (3.3) |
| WaivOps HH-TRP | CC BY 4.0 | SAFE | 15,000 trap drum loops, audio, made by a program | chosen: trap drums (bucket 4) |
| Freesound, "trap 808" | per sound (CC0, CC BY, some NC) | SAFE when CC0 or CC BY | 183 CC0 sounds alone: 808 and snare one-shots, some 808 bass loops and whole beats | 808 lines via audio to MIDI (4.3); the CC0 one-shots as Ouralia's 808 and kit sounds (bucket 6) |
| FMA hip hop (CC0 and CC BY tracks) | per track | SAFE when CC0 or CC BY | whole tracks | stems and Basic Pitch (4.3) |
| ccMixter | per upload (BY or BY-NC) | per upload | stems and remixes; no CC BY trap stems turned up in the search | check upload by upload (4.1) |
| Kukedlc/suno-ai-music-dataset (HF) | CC BY 4.0 (says) | ideas only | AI-made (Suno) tracks, some trap | not training data (decision 7: AI-made music is ideas only) |
| Lo-Fi Hip Hop MIDIs (Kaggle) | CC0 (says) | - | 41 KB, source not stated, lo-fi not trap | not usable (unknown source) |
| WaivOps Lo-Fi Chords | CC BY 4.0 | SAFE | 8,000 piano chord loops, audio, soul and retro | off-target for trap |
| Selektaudio "free 808 MIDI" | the vendor says its patterns come from CC0, PD and CC BY recordings | CHECK | 808 MIDI patterns, behind an account | not usable unless the claim can be checked |

So trap's training data will be mostly **practice MIDI from its style book entry** (4.2) and **open audio turned
into MIDI** (4.3), with GMD and HH-TRP for drums: the entry written in 3.4a is what the model learns trap from.

**Theory.** No open textbook covers trap (Open Music Theory's "Drumbeats" chapter may touch it; the page refused
the fetch, to check in 3.4a; it refused again in 3.4a, HTTP 403, so it is left out). What we have, all as ideas in our own words:
- **Wikipedia** (CC BY-SA 4.0): "Trap music", "Drill music", "Roland TR-808". Felt around 70 BPM, counted 140
  (range about 100-176) in half time; hats in double and triple time; the snare (or clap) rigidly on beat 3;
  808 kicks tuned with a long decay so they are the bass; dark drones, thin or thick, and cinematic synth strings,
  brass, woodwinds and keys. Drill (Chicago, UK, Brooklyn): skippy, syncopated hats (UK: a sped-up tresillo),
  808 slides, more syncopated drums, synth brass and bells.
- **Ben Duinker, "Good Things Come in Threes: Triplet Flow in Recent Hip-Hop Music"** (Popular Music 38/3, 2019;
  (c) Cambridge University Press, an accepted manuscript on McGill's repository): triplet flow (the beat divided in
  three over a beat divided in two or four), in three kinds: mixed, phrasal, total; tied to trap's sparse, slow
  beats. For Maestro (no vocals) the idea is for the melody: triplet figures over the straight 16ths.
- **Kyle Adams, "On the Metrical Techniques of Flow in Rap Music"** (Music Theory Online 15/5, 2009; (c) the
  author): where the accented and rhyming notes fall in the beat, and phrases running across the bar line
  (enjambment). Ideas for the melody's phrasing.
- **Mitchell Ohriner, "Flow: The Rhythmic Voice in Rap Music"** (Oxford, 2019): not read; mostly older rap.
- **Producers' guides** (copyrighted, ideas only, weakest): harmony mostly static (one or two chords, often
  harmonic minor or phrygian colours); the 808 often the only clear harmony, so mostly roots, with slides between
  notes and octave jumps; a verse of 16 bars, a hook of 8-16; the 808 and kick drop out before a hook, and beat
  switches, for drama.

**What it suggests for 3.4a** (proposals for DadCraft):
1. The 808 is trap's bass member: long notes placed with the kick, mostly roots (and fifths, octave jumps), some
   sliding into the next note (a pitch bend in the PC clips; a glide in Ouralia, bucket 6).
2. Harmony nearly static: loops of one or two chords (i, i-VI, i-bII), a chord every one or two bars.
3. The melody: a short dark motif repeated and varied (bell, pluck, flute, piano), with triplet figures over the
   straight grid (from triplet flow); a counter-melody optional.
4. The hats change rate inside the bar (16ths, triplets, 32nds), not only in rolls at a phrase's end; open hats
   as accents; the snare or clap fixed on 3.
5. For 3.6 (layering): the 808 and kick dropping out before a hook, hat-only openings, a beat switch.
6. Subgenres (drill, rage, trapsoul) later, as their own entries or as seasoning.

### DadCraft's trap finds (Oct 24, from a Google search; `inbox/trap.md`, `inbox/trap_training_specs.md`)

| Source | License | Tag | What | Use |
|---|---|---|---|---|
| GigaMIDI | scraped | OUT | already audited above | none (decision 7) |
| XMIDI (xmusic-project) | none stated; source of its 108k MIDI not stated | OUT | MIDI with emotion and genre labels | none unless a license and the files' origin turn up |
| RapBank (zqning) | CC BY-NC-SA 4.0, and only YouTube IDs | OUT | links to 94k rap videos; the audio is copyrighted | none |
| RapVerse | none stated for the data (the paper is CC BY 4.0) | OUT | rap vocals, lyrics, motion | none (no instrumental, no license) |
| GCX trap dataset | a vendor's licensed product | OUT | audio with key and tempo labels | none (not open) |
| genres_v2.csv (Spotify audio features, a GitHub project) | none stated; Spotify's API terms | ideas only | 42k tracks' features (tempo, energy, valence, mode), 15 playlist genres | numbers checked, nothing kept |

What genres_v2 says (medians, our own counts): its "trap" label sits with techno, trance and dnb (150 BPM, energy
0.94): EDM trap, not the Atlanta rap trap DadCraft means. Its "Dark Trap" (4,578 tracks) is: 142 BPM (our 140 fits),
low valence 0.22 (dark), energy 0.65, and only 46% detected as minor (Spotify's mode is rough, but minor is no lock,
as decision 9 says). No change to the entry.

The specs file is an AI-written overview (Google's), ideas only and to be checked: it agrees with the entry (140
counted in half time, the snare on 3 of each bar, 32nd hat rolls, triplets, an 808 gliding over 50-250 ms: ours
slides over an 8th, 214 ms at 140, and a bend linear in semitones is the exponential glide it gives). New: 64th
"stutter" rolls (our grid of 24 a beat stops at 32nd triplets), and a check for rolled hats (the spread of the gaps
between hat hits). Its advice to penalise major keys hard goes against decision 9, so it isn't taken.

### DadCraft's synthwave finds (Oct 24, from a Google search; `inbox/synthwave.md`)

Licenses from each repo's own page (GitHub's license field, the Hugging Face card).

| Source | License | Tag | What | Use |
|---|---|---|---|---|
| Tegridy MIDI Dataset | Apache-2.0 on the repo; holds Lakh and fan MIDI | OUT | already audited above | none (decision 7) |
| Synthwave MIDI Reimaginer (zeittresor) | none stated | ideas only | a GUI that restyles MIDI by 171 hand-set presets | its synthwave preset read (below), nothing kept |
| SynTheory (brown-palm; HF meganwei/syntheory) | MIT (code and data) | SAFE | made-up clips of notes, intervals, scales, chords, progressions, tempos, meters, to probe whether a music model knows theory | for 3.5 and bucket 4: checking that the style judge and our model hear theory; not a synthwave source |
| synth1-dataset (OdysseasKr) | none stated | OUT | sounds rendered from Synth1 presets | none |
| WaivOps Lo-Fi Chords | CC BY 4.0 (Zenodo; the GitHub repo states none) | SAFE | already audited above | off-target for synthwave (piano, soul) |
| Open Music Theory | already in use (3.2) | - | - | - |
| YC Music Theory (CUNY Academic Commons; source github.com/georgelam155/cunyopenmusic, from DadCraft) | CC BY-SA 4.0 (the site's footer and its "about" page: use, change, even sell, with credit and the same license) | SAFE | a 2019 remix of Open Music Theory 1.0 for a York College course; its pop/rock harmony pages | ideas, in our own words (below) |
| music21 | BSD-3-Clause | SAFE | already audited above; library-only S.0a v4 converter, never bundled corpus | - |
| mingus | GPL-3.0 | SAFE | a Python theory library (chords, scales, progressions) | not needed: our theory core covers it |

The Reimaginer's synthwave preset agrees with the entry: 96-128 BPM (ours 112), four on the floor, a gated snare,
tom fills, a Juno-style pad, a synth bass and an arp; reverb and delay fairly high. Its lead sits much lower than
ours (centred on G#4, the bass on A2), where our lead's phrases run from about E5 to A6: a reason, beside the level,
the lead may sound too loud (a saw that high cuts through). Noted for the next synthwave round, not yet changed.

YC Music Theory's pop/rock harmony pages (read from the repo DadCraft found, Oct 24; the site itself asks for a
captcha) back the synthwave entry: in minor, pop's usual way home is bVI-bVII-i rather than iv-V-i (the bass
stepping up, closer to the relative major), and the "singer/songwriter" loop (VI-IV-I-V in major, i-VI-III-VII in
minor) is the entry's sunset and aeolian loop. So a synthwave phrase landing home on E7-Am (the flow's cadence
borrowing V7) is less its own than F-G-Am: a change proposed to DadCraft for the next synthwave round. Its "Everett
systems" page on rock's major triads over the pentatonic (I, bIII, IV, V, bVII; rotated loops of power chords) is
for power rock (3.4d).

## The outside lists (Oct 26)

Six AI systems' lists of open music-AI resources (`inbox/`, private; `docs/research.md` round 4). Nothing in them is
trap, synthwave, salsa or power rock, so the gaps above stand. Each notice was read on the source's own page on
Oct 26 and mapped with the rules table (`maestro/data/licenses.json`, decision 14).

| Candidate | What it is | Notice found (where) | Tag | Use |
|---|---|---|---|---|
| MusicNet | 330 classical recordings, 1M+ note labels | "Creative Commons Attribution 4.0 International" (Zenodo record 5120004, Rights); recordings from CC and public-domain sources, each file's source in its metadata | SAFE | off-target; voice leading and the exam, if wanted |
| Fundamentals of Music Processing (Müller) | MIR textbook as notebooks | text and figures "CC BY-NC-SA 4.0", `libfmp` code "MIT license", audio "the respective original licenses apply" (FMP C0 page, About) | NC (text), SAFE (code) | reader, PC side; ideas in our own words |
| ComMU | 11,144 short MIDI pieces "written and created by professional composers" | "CC BY-NC-SA 4.0 ... prohibited to be used for commercial purposes" (POZAlabs/ComMU-code README, License) | NC | PC only: experiments, the style judge |
| GiantMIDI-Piano | 10,855 classical piano pieces transcribed from YouTube recordings | "CC BY 4.0" (bytedance/GiantMIDI-Piano README, License), not saying if it covers the MIDI or the code; the download disclaimer adds no terms and says nothing on the recordings | CHECK | third-party content (the recordings); off-target, low priority |
| JSB Chorales | Bach's chorales (the Boulanger-Lewandowski split) | none (czhuang/JSB-Chorales-dataset: no LICENSE, no notice; its source page is gone). music21's copy (Greentree's MusicXML) is distributed "with the permission of the encoders", and the corpus "may not be used for commercial uses" in parts | CHECK | Bach is public domain, the encodings aren't clearly licensed; off-target |
| EMOPIA | 1,087 pop piano clips from 387 songs, emotion labels; MIDI transcribed from YouTube covers | "Creative Commons Attribution 4.0 International" (Zenodo record 5090631, Rights) | OUT | a CC license on transcriptions of copyrighted pop songs (the doubt rule; decision 7); the four emotion quadrants as an idea only |
| Popular Hooks | 38,694 hooks of pop songs: MIDI, lyrics, YouTube links | none (NEXTLab-ZJU/popular-hook card: no license field); each song links its TheoryTab entry, lyrics from music APIs | OUT | copyrighted songs, no notice; TheoryTab is Hooktheory's (OUT above) |
| Niko Chord Progression Dataset | 5k+ progressions labelled by style | AccoMontage2 repo "MIT license" (the code); the data "re-organized from the original Niko Dataset", which is "Nikos Ultimate MIDI Pack" (pianoforproducers.com, a paid MIDI pack) | OUT | a code license on a commercial pack (the doubt rule) |
| Discover MIDI | 6.74M de-duplicated MIDI files | "cc-by-nc-sa-4.0" (projectlosangeles/Discover-MIDI-Dataset card); sources not given, files matched to artist and title | OUT | Lakh-style fan MIDI of copyrighted songs (decision 7) |
| Galaxy MIDI | "19.9M MIDI" (one list only) | not found on Hugging Face, GitHub or in papers | drop | likely a list's mistake |

So nothing new for the phone model: MusicNet is safe but classical; ComMU and the FMP text are PC only.

The lists got several licenses wrong, against what we checked at the source: Lakh MIDI and Slakh2100 called CC BY
(fan MIDI of copyrighted songs: OUT); MAESTRO and MTG-Jamendo counted as plain CC (both NC); Hooktheory, teoria.com and
musictheory.net called usable for training (all OUT); Essen called public domain (no clear license: CHECK). The
refuse-when-in-doubt rule (decision 14) is there for exactly this.

## Sources (checked Oct 23)
- GMD: https://magenta.tensorflow.org/datasets/groove · E-GMD: https://magenta.tensorflow.org/datasets/e-gmd
- PDMX: https://zenodo.org/records/15571083
- imslp-midi-cc0-1.0: https://huggingface.co/datasets/TiMauzi/imslp-midi-cc0-1.0
- Aria-MIDI: https://huggingface.co/datasets/loubb/aria-midi
- FMA: https://github.com/mdeff/fma · MTG-Jamendo: https://github.com/MTG/mtg-jamendo-dataset
- SoundSafari: https://huggingface.co/datasets/SoundSafari/Public-Domain-Music
- WaivOps HH-TRP: https://zenodo.org/records/15734094 · EDM-TR8: https://zenodo.org/records/13257814 · Lo-Fi Chords:
  https://zenodo.org/records/17819350
- Trap, a closer look: https://en.wikipedia.org/wiki/Trap_music · https://en.wikipedia.org/wiki/Drill_music ·
  https://en.wikipedia.org/wiki/Roland_TR-808 · Duinker: https://mcgill.scholaris.ca/items/808db999-6a28-48f9-9422-392946339f35 ·
  Adams: https://mtosmt.org/issues/mto.09.15.5/mto.09.15.5.adams.php · Freesound: https://freesound.org ·
  https://huggingface.co/datasets/Kukedlc/suno-ai-music-dataset · https://www.kaggle.com/datasets/zakarii/lofi-hip-hop-midi
- GiantSteps: https://github.com/GiantSteps/drum-pattern-datasets
- GigaMIDI: https://www.metacreation.net/projects/gigamidi-dataset
