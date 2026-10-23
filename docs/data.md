# Data audit

Every candidate set for Maestro: license, tag, size, format, and the styles and members it covers (task 1.2,
Oct 23). Licenses were checked on each set's own page on Oct 23. Check them again when downloading (task 4.1).

Members are Ouralia's band today (`format.md`): **melody**, **bass**, **pad** (chords) and **drums**.

**Tags** (PLAN.md decision 7):
- **SAFE:** allows commercial use. Fine for the phone model.
- **NC:** non-commercial. PC only (experiments, research, the style judge), kept apart, never in the phone model.
- **OUT:** not for training. Ideas only.
- **CHECK:** license or source not clear yet. Not used until it is.

## Symbolic (MIDI, scores)

| Set | License | Tag | Size | Format | Styles | Members | Status |
|---|---|---|---|---|---|---|---|
| Groove MIDI (GMD) | CC BY 4.0 | SAFE | 1,150 files, 13.6 h; MIDI-only 3 MB (with audio 4.8 GB) | MIDI + synthesized WAV, CSV | 18 drum styles: afrobeat, afrocuban, funk, hip hop, jazz, latin, rock, reggae, pop, soul... | drums (human, with feel) | **chosen** (3.2) |
| Expanded GMD (E-GMD) | CC BY 4.0 | SAFE | 45,537 sequences (1,059 unique), 444 h, 43 kits; MIDI-only 103 MB (with audio 90 GB) | MIDI + WAV, CSV | as GMD | drums | **chosen**, MIDI only |
| PDMX | CC BY 4.0 (scores public domain) | SAFE | 250K+ scores, 14.4 GB | MusicXML (MXL), MIDI, MusicRender JSON, PDF; CSV with genres and ratings | mostly classical, folk, hymns, film/game arrangements; genre column | melody, bass, pad (harmony, voice leading); few drums | **chosen**: only the `no_license_conflict` subset (222,856); 12% have license conflicts, dropped |
| imslp-midi-cc0-1.0 (TiMauzi, HF) | CC0 1.0 | SAFE | 1,113 files, 50 MB download | parquet holding MIDI, with era, style, key | classical, romantic, some "modern" | melody, bass, pad | **chosen** (theory, bucket 2) |
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
| WaivOps HH-TRP | CC BY 4.0 | SAFE | 15,000 loops, 55 h, 22.3 GB | WAV + JSON labels | trap: drill, trapsoul, cloud rap, emo rap | candidate for trap drums (made by a program, not humans; MIDI not published) |
| WaivOps EDM-TR8 | CC BY 4.0 | SAFE | 3,790 loops, 9 h, 4.4 GB | WAV, BPM labels | EDM, TR-808 | candidate for EDM drums (made by a program) |
| WaivOps RTRO-DRM | CC BY 4.0 | SAFE | 2,138 clips | WAV | 1980s electronic (synthwave drums) | candidate (made by a program) |
| Freesound | per file: CC0, CC BY, CC BY-NC | per file | huge | WAV etc., API filter by license | modern loops and stems, all kinds | candidate: CC0 and CC BY loops via the API |
| ccMixter | per track, many NC | per track | | MP3, stems | modern, beat-driven | candidate, per track |
| Musopen | per recording, many public domain | per track | | MP3/FLAC | classical | low priority (PDMX already has classical scores) |
| Citizen DJ (Library of Congress) | public domain (US recordings published before 1926) | SAFE | thousands of clips | audio | early jazz, blues, opera, classical | low priority; old, noisy recordings |
| Great 78 (Internet Archive) | mixed; the labels sued the Archive over it (2023) | OUT | 400K+ records | audio | early 20th-century popular | keep out |
| MusicCaps | captions CC BY-SA 4.0; audio is YouTube clips (copyrighted) | OUT | 5,521 clips | captions only | all kinds | not "public domain" as `music-info.md` says; no audio to train on |

Other tools: **MusicBrainz** (CC0 metadata, no music) can check dates and credits. **Synthetic music from an AI model**
(e.g. ACE-Step output) is an open question, see below.

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
across many styles. The gaps are filled by:
1. **The style book** (bucket 3) and its practice MIDI (4.2): written from sources, labeled, ours (SAFE).
2. **Open audio turned into MIDI** (4.3): the FMA CC0 and CC BY tracks (electronic, hip hop, rock), CC0 and CC BY
   Freesound and ccMixter loops, transcribed with Demucs → Basic Pitch → Beat This!.
3. **Theory and harmony** from PDMX and IMSLP, which carry over to every style (bucket 2).

Salsa and afrobeat have the least modern open audio. Expect them to lean most on the style book.

## Questions for DadCraft

1. **Synthetic music from other AI models** (e.g. ACE-Step output) as training data: their own training data is
   unknown, so the spirit of decision 7 says no. Proposed: OUT, ideas only.
2. **Programmatic drum loops** (WaivOps): CC BY, but made by a program, and where its patterns came from isn't
   stated. Proposed: SAFE by license, but only as a supplement to GMD's human drumming, credited.

## Sources (checked Oct 23)
- GMD: https://magenta.tensorflow.org/datasets/groove · E-GMD: https://magenta.tensorflow.org/datasets/e-gmd
- PDMX: https://zenodo.org/records/15571083
- imslp-midi-cc0-1.0: https://huggingface.co/datasets/TiMauzi/imslp-midi-cc0-1.0
- Aria-MIDI: https://huggingface.co/datasets/loubb/aria-midi
- FMA: https://github.com/mdeff/fma · MTG-Jamendo: https://github.com/MTG/mtg-jamendo-dataset
- SoundSafari: https://huggingface.co/datasets/SoundSafari/Public-Domain-Music
- WaivOps HH-TRP: https://zenodo.org/records/15734094 · EDM-TR8: https://zenodo.org/records/13257814
- GiantSteps: https://github.com/GiantSteps/drum-pattern-datasets
- GigaMIDI: https://www.metacreation.net/projects/gigamidi-dataset
