# SPDX-License-Identifier: GPL-3.0-or-later
"""Real music to notes (decision 19's proof; later task 4.3): splits a recording into stems with Demucs (MIT) and
writes each pitched stem's notes with Basic Pitch (Apache-2.0), all on this PC. The notes become a Maestro clip
(MIDI and its JSON) that the clip player renders through Maestro's own sounds: the bass stem as the bass, the top
voice of the "other" stem as the melody, the rest of it as the pad. The drum stem is kept as audio; Basic Pitch
writes no drums.

Runs in its own environment, `private/transcribe` (torch, demucs, basic-pitch; gitignored):

    private/transcribe/bin/python tools/transcribe.py inbox/song.mp3 --out private/refs/song

then `.venv/bin/python -m maestro.play private/refs/song/notes.mid --wav-only`. A copyrighted recording stays in
`inbox/` or `private/` (decision 7: ideas only, never committed or sent out)."""
import argparse, json, os, subprocess, sys

import mido

BEAT = 960                         # ticks a beat; the clip is written at 120 BPM, so a second is 2 beats
SOUNDS = {"melody": "saw lead", "pad": "supersaw", "bass": "saw bass"}


def stems(audio, out):
    """{stem: its WAV} from Demucs's htdemucs (drums, bass, other, vocals), split on the GPU when there is one."""
    import torch
    name = os.path.splitext(os.path.basename(audio))[0]
    subprocess.run([sys.executable, "-m", "demucs", "-n", "htdemucs", "-o", out, "-d",
                    "cuda" if torch.cuda.is_available() else "cpu", audio], check=True, stdout=subprocess.DEVNULL)
    folder = os.path.join(out, "htdemucs", name)
    return {s: os.path.join(folder, s + ".wav") for s in ("drums", "bass", "other", "vocals")}


def notes(wav, low=None, high=None):
    """[(start s, end s, pitch, velocity)] Basic Pitch hears in a stem."""
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    _, _, events = predict(wav, ICASSP_2022_MODEL_PATH, onset_threshold=0.55, frame_threshold=0.3,
                           minimum_note_length=70, minimum_frequency=low, maximum_frequency=high,
                           multiple_pitch_bends=False, melodia_trick=True)
    return sorted((s, e, int(p), max(1, min(127, int(a * 127)))) for s, e, p, a, *_ in events)


def skyline(notes):
    """(melody, the rest): a note is the melody's when nothing higher sounds as it starts."""
    top, rest = [], []
    for n in notes:
        s, e, p, _ = n
        (rest if any(o[2] > p and o[0] <= s + 0.03 and o[1] > s + 0.03 for o in notes) else top).append(n)
    return top, rest


def write(parts, out):
    midi = mido.MidiFile(type=1, ticks_per_beat=BEAT)
    conductor = mido.MidiTrack([mido.MetaMessage("set_tempo", tempo=500000, time=0)])
    midi.tracks.append(conductor)
    for name, ns in parts.items():
        tr = mido.MidiTrack([mido.MetaMessage("track_name", name=name, time=0)])
        events = sorted([(round(s * 2 * BEAT), 1, p, v) for s, e, p, v in ns] +
                        [(round(e * 2 * BEAT), 0, p, 0) for s, e, p, v in ns])
        now = 0
        for t, on, p, v in events:
            tr.append(mido.Message("note_on" if on else "note_off", note=p, velocity=v, time=t - now))
            now = t
        midi.tracks.append(tr)
    path = os.path.join(out, "notes.mid")
    midi.save(path)
    members = {n: {"role": n, "sound": SOUNDS[n]} for n in parts}
    json.dump({"source": {"style": "synthwave", "from": "tools/transcribe.py"}, "members": members},
              open(path[:-4] + ".json", "w"), indent=1)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("audio")
    ap.add_argument("--out", required=True, help="a folder under private/")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    wavs = stems(a.audio, a.out)
    bass = notes(wavs["bass"], 30, 400)
    melody, pad = skyline(notes(wavs["other"], 80, 4200))
    path = write({"melody": melody, "pad": pad, "bass": bass}, a.out)
    print(f"{path}: melody {len(melody)}, pad {len(pad)}, bass {len(bass)} notes; drums {wavs['drums']}")


if __name__ == "__main__":
    main()
