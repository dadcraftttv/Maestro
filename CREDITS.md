# Credits

Every data set Maestro uses, with the attribution its license asks for. A set is listed here before it is used
(`docs/data.md` has the full audit). Models trained on these sets carry these credits.

## Commercial-safe (may train the phone model)

- **Groove MIDI Dataset**, by Google LLC (Magenta), CC BY 4.0. Jon Gillick, Adam Roberts, Jesse Engel, Douglas Eck,
  David Bamman, "Learning to Groove with Inverse Sequence Transformations", ICML 2019.
  https://magenta.tensorflow.org/datasets/groove
- **Expanded Groove MIDI Dataset (E-GMD)**, by Google LLC (Magenta), CC BY 4.0. Lee Callender, Curtis Hawthorne,
  Jesse Engel, "Improving Perceptual Quality of Drum Transcription with the Expanded Groove MIDI Dataset", 2020.
  https://magenta.tensorflow.org/datasets/e-gmd
- **PDMX** (`no_license_conflict` subset), CC BY 4.0; the scores are public domain, from MuseScore. Phillip Long,
  Zachary Novack, Taylor Berg-Kirkpatrick, Julian McAuley, "PDMX: A Large-Scale Public Domain MusicXML Dataset for
  Symbolic Music Processing", ICASSP 2025. https://zenodo.org/records/15571083
  S.0a v6 adds the uploader's public-domain string-quartet setting of **Nearer My God to Thee**, score 1975051,
  uploader `wade.allen.965`; original tune Bethany by Lowell Mason, words by Sarah Flower Adams. Local
  per-score evidence includes the encoding declaration, first-person authorship statement and publication citation;
  cleared in Claude Code's review (Oct 29). https://musescore.com/user/123153/scores/1975051
- **WaivOps HH-TRP, EDM-TR8 and RTRO-DRM**, by Patchbanks / WaivOps, CC BY 4.0.
  https://zenodo.org/records/15734094 · https://zenodo.org/records/13257814 (RTRO-DRM: Zenodo record to add on
  download)

## Local inventory candidates (not cleared for training)

- **OpenScore Lieder**, OpenScore contributors, CC0-1.0. Credit and repository link requested:
  https://github.com/OpenScore/Lieder · https://musescore.com/openscore-lieder-corpus
- **OpenScore String Quartets**, OpenScore contributors, CC0-1.0. Credit and repository link requested:
  https://github.com/OpenScore/StringQuartets · https://musescore.com/openscore-string-quartets
  Per-piece provenance stays in the local inventory; underlying works/editions still require review.

- **Mutopia Project**, individual public-domain dedications or Creative Commons Attribution licenses only
  (S.0a v5 screening, DadCraft-approved Oct 28). Composer, work, typesetter/maintainer, precise license,
  source URL and file hashes are recorded per piece in `private/s0a_v5/`. SA/NC and unclear rights are excluded.
  CC BY 3.0 typesettings used: Handel, Messiah (Mutopia 1732), typeset by Nicolas Sceaux; O. Rieding, Concerto
  in B minor, Op. 35 (Mutopia 1781), typeset by Michael Fischer v. Mollard.
  https://www.mutopiaproject.org/ ; https://www.mutopiaproject.org/legal.html
- **S.0a v7 local song candidates** (rights reviewed by Claude Code, Oct 29): PDMX no-conflict PD/CC0 encodings of
  Joseph M. Daly's Chicken Reel, adapted by uploader Bernard Delahaye (5919666);
  Euday L. Bowman's Twelfth Street Rag (5860188); Hill tune Happy Birthday, uploader Upsideken's own
  4/4 setting (5915185); traditional/Weatherly Danny Boy, G. Breen's Wyncote Brass arrangement (61265);
  Stephen Foster's Camptown Races, uploader Piotr Barcz's score (6320642).
  MuseScore per-score URLs, metadata hashes, cited dates and arrangement evidence are in
  `private/s0a_v7/rights_manifest.json`. Secondary dates are flagged; no training approval.
  Mutopia **1034**, Lowell Mason's Nearer My God to Thee, typeset by **Ross Uber**, Public Domain:
  https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1034
- **TiMauzi IMSLP MIDI CC0 catalog**, revision `703e983510885d9833dd1c534900e0eb258b69af`
  (S.0a v5 screening). Collection CC0 is not a per-composition clearance. Individual provenance and
  unresolved rights are recorded under `private/s0a_v5/` before any admission.
  https://huggingface.co/datasets/TiMauzi/imslp-midi-cc0-1.0

## Tools (not data; never trained on)

- **MuseScore** 3.6.2, MuseScore contributors, GPL-2.0,
  https://github.com/musescore/MuseScore/tree/v3.6.2 · approved local CLI conversion fallback.

- **music21** v9.9.2, Michael Scott Asato Cuthbert and contributors, BSD-3-Clause,
  https://github.com/cuthbertLab/music21 · local MusicXML conversion only (`data` extra).
  Its bundled corpus is never accessed or used.

- **FluidR3 GM** soundfont, by Frank Wen (Toby Smithe and contributors), MIT license: the clip player's sounds
  (`tools/get_sounds.sh`, from Ubuntu's `fluid-soundfont-gm`). **FluidSynth** (LGPL-2.1), used as the system library.
- **GeneralUser GS** v2.0.3 soundfont, by S. Christian Collins, its own license ("You may use GeneralUser GS without
  restriction for your own music creation, private or commercial"; its author can't vouch for every sample's
  origin): B of the sounds A/B on trap (Oct 28), on this PC only (`tools/get_sounds.sh`, from
  github.com/mrbumpy409/GeneralUser-GS). Not shipped, not trained on.
- **Demucs** (htdemucs, by Meta AI, MIT) splits recordings into stems and **Basic Pitch** (Spotify, Apache-2.0)
  turns stems into notes: `tools/transcribe.py`, in its own environment under `private/` (decision 19's proof;
  later task 4.3).

## Written theory (ideas in our own words, cited in the style files' `sources`)

- **Open Music Theory**, by its authors and contributors, CC BY-SA 4.0: loops and schemas (the progression
  families, task 3.2). https://viva.pressbooks.pub/openmusictheory
- **jazznet**, by its authors, MIT: the ii-V progressions (task 3.2). https://github.com/tosiron/jazznet
- **Wikipedia**, "Tumbao", CC BY-SA 4.0: salsa's anticipated bass (task 3.2). https://en.wikipedia.org/wiki/Tumbao
- **Wikipedia**, "Guajeo", "Montuno", "Son montuno", "Salsa music", "Mambo (music)", CC BY-SA 4.0: salsa's piano
  montuno, horns and song parts, ideas in our own words (task 3.4c).
- **Wikipedia**, "Trap music", "Drill music", "Roland TR-808", CC BY-SA 4.0: trap's entry (task 3.4a).
  https://en.wikipedia.org/wiki/Trap_music
- **Ben Duinker**, "Good Things Come in Threes: Triplet Flow in Recent Hip-Hop Music", Popular Music 38/3 (2019),
  (c) Cambridge University Press: the idea of triplet figures over a duple beat (the motif's `triplet`, task 3.4a),
  ideas only.

- **The Rock Corpus**, by Trevor de Clercq and David Temperley, CC BY 4.0: our counts of the RS 200's harmonic
  analyses (`tools/rock_stats.py`, `maestro/data/rock.json`), power rock's progressions (task 3.4d); the songs
  themselves are copyrighted and nothing of them is kept. T. de Clercq, D. Temperley, "A Corpus Analysis of Rock
  Harmony", Popular Music 30/1 (2011). http://rockcorpus.midside.com
- **Wikipedia**, "Power chord", "Palm mute", "Pentatonic scale", "String bending", "Verse-chorus form", "Arena
  rock", CC BY-SA 4.0: power rock's guitars, lead and parts (task 3.4d).
- **SynTheory**, MIT. Megan Wei, Michael Freeman, Chris Donahue, Chen Sun, "Do Music Generation Models Encode Music
  Theory?", ISMIR 2024. https://github.com/brown-palm/syntheory: its chord progressions and their recipe (two triads
  a bar at 120 BPM, every key), rebuilt in our own code to check the style judge (task 3.5c).
- **Wikipedia**, "Double tracking", "Nashville tuning (high strung)", CC BY-SA 4.0: power rock's guitar card, the
  octave-up double (task 3.5c).

## Non-commercial (PC only, never in the phone model)

- **Aria-MIDI**, CC BY-NC-SA 4.0. Louis Bradshaw, Simon Colton, "Aria-MIDI: A Dataset of Piano MIDI Files for
  Symbolic Music Modeling", ICLR 2025. https://huggingface.co/datasets/loubb/aria-midi

## S.0a v8 local song additions (Oct 29; review pending)

Nine local PDMX encodings, individually recorded in the private v8 rights manifest. Traditional tune dates
and dated third-party settings are separate from encoding licenses. Danny Boy 61265 is removed for insufficient
usable material. No new source files downloaded.

- [Down by the riverside 3 voices](https://musescore.com/user/7220866/scores/6341482), score 6341482; encoding by Paweł Kupis, cc-zero. Date: traditional.
- [All through the night](https://musescore.com/user/3099636/scores/5930552), score 5930552; encoding by sangerforum, cc-zero. Date: traditional.
- [April Showers](https://musescore.com/user/1461451/scores/818331), score 818331; encoding by clothesliner, publicdomain. Date: secondary.
- [Love's_Old_Sweet_Song](https://musescore.com/user/3099636/scores/5968906), score 5968906; encoding by sangerforum, cc-zero. Date: secondary.
- [The Whiffenpoof Song - Tod B. Galloway](https://musescore.com/user/33131263/scores/5767326), score 5767326; encoding by John__Smith, publicdomain. Date: secondary.
- [Aba Daba Honeymoon - Arthur Fields](https://musescore.com/user/15377981/scores/6146547), score 6146547; encoding by MikeStokesberry, cc-zero. Date: secondary.
- [St Louis Blues](https://musescore.com/user/28851728/scores/5962248), score 5962248; encoding by peter_scott71, cc-zero. Date: secondary.
- [There's Music in the Air - SATB](https://musescore.com/user/3099636/scores/2067021), score 2067021; encoding by sangerforum, cc-zero. Date: secondary.
- [Poor Wayfaring Stranger - Trombone](https://musescore.com/user/27301546/scores/5984045), score 5984045; encoding by ttranman77, cc-zero. Date: traditional.

## S.0a v9 local song additions (Oct 29)

Three more local PDMX encodings from the whole-bar chord fallback; no new source files downloaded.

- [De Camptown Races - TTBB](https://musescore.com/user/3099636/scores/1907501), score 1907501; encoding by sangerforum, cc-zero. Date: secondary.
- [The Twelve Days of Christmas](https://musescore.com/user/6624501/scores/5851745), score 5851745; encoding by Joshua667746, cc-zero. Date: traditional.
- [Danny Boy](https://musescore.com/user/4873976/scores/5947839), score 5947839; encoding by Nickbarbosa, cc-zero. Date: secondary.

## S.0a v10 MusicXML-symbol addition (Oct 29; dropped by DadCraft in v11, not in the corpus)

- [After You've Gone](https://musescore.com/user/157900/scores/156119), score 156119; music Turner Layton,
  words Henry Creamer (1918); encoding by uglybeauty, publicdomain declaration. Chord symbols read from the
  approved PDMX MusicXML archive. Marion Harris appears as artist, with no stated recording source or arranger;
  Claude Code kept it under the rules; see `private/s0a_v10/new_additions_review.json`.
