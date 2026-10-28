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
- **imslp-midi-cc0-1.0**, compiled by TiMauzi from IMSLP, CC0 1.0 (no attribution required; credited with thanks).
  https://huggingface.co/datasets/TiMauzi/imslp-midi-cc0-1.0
- **WaivOps HH-TRP, EDM-TR8 and RTRO-DRM**, by Patchbanks / WaivOps, CC BY 4.0.
  https://zenodo.org/records/15734094 · https://zenodo.org/records/13257814 (RTRO-DRM: Zenodo record to add on
  download)

## Tools (not data; never trained on)

- **FluidR3 GM** soundfont, by Frank Wen (Toby Smithe and contributors), MIT license: the clip player's sounds
  (`tools/get_sounds.sh`, from Ubuntu's `fluid-soundfont-gm`). **FluidSynth** (LGPL-2.1), used as the system library.
- **GeneralUser GS** v2.0.3 soundfont, by S. Christian Collins, its own license ("You may use GeneralUser GS without
  restriction for your own music creation, private or commercial"; its author can't vouch for every sample's
  origin): B of the sounds A/B on trap (Oct 28), on this PC only (`tools/get_sounds.sh`, from
  github.com/mrbumpy409/GeneralUser-GS). Not shipped, not trained on.

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
