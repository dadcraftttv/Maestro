# SPDX-License-Identifier: GPL-3.0-or-later
"""A/B listens (task 3.8): a style's earlier round next to today's, the same seed and bars, for DadCraft to say which
is better and why. A is made and rendered by the earlier commit's own code (a git worktree, removed after), B by
today's, so each sounds as it did in its round.

    .venv/bin/python tools/ab.py synthwave 1a2b3c4 --seed 14 --bars 32
    .venv/bin/python -m maestro.play clips/ab/synthwave          # A, then B

writes `clips/ab/<style>/1_A_<commit>_<seed>` and `2_B_now_<seed>` (.mid, .json, .txt, .wav) and `ab.txt`, the
question for the listen."""
import argparse, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from maestro import play


def make(root, style, seed, bars, out, sf2):
    """The clip `root`'s code makes for style, seed and bars, rendered by its own player; the stem it wrote."""
    os.makedirs(out, exist_ok=True)
    run = dict(cwd=root, check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, "-m", "maestro.sketch", style, "--seed", str(seed), "--seeds", "1",
                    "--bars", str(bars), "--out", out], **run)
    stem = os.path.join(out, f"{style}_{seed}")
    subprocess.run([sys.executable, "-m", "maestro.play", f"{stem}.mid", "--wav-only", "--sf2", sf2], **run)
    return stem


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("style")
    ap.add_argument("commit", help="the earlier round's commit")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--bars", type=int, default=16)
    ap.add_argument("--out", help="clips/ab/<style>")
    a = ap.parse_args(argv)
    out = os.path.abspath(a.out or os.path.join(HERE, "clips", "ab", a.style))
    short = subprocess.run(["git", "rev-parse", "--short", a.commit], cwd=HERE, check=True, capture_output=True,
                           text=True).stdout.strip()
    sf2 = play.soundfont()
    os.makedirs(out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        old = os.path.join(tmp, "old")
        subprocess.run(["git", "worktree", "add", "--detach", old, short], cwd=HERE, check=True, capture_output=True)
        try:
            stems = {f"1_A_{short}": make(old, a.style, a.seed, a.bars, os.path.join(tmp, "a"), sf2),
                     "2_B_now": make(HERE, a.style, a.seed, a.bars, os.path.join(tmp, "b"), sf2)}
            for name, stem in stems.items():
                for ext in (".mid", ".json", ".txt", ".wav"):
                    if os.path.exists(stem + ext):
                        shutil.copy(stem + ext, os.path.join(out, f"{name}_{a.seed}{ext}"))
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", old], cwd=HERE, capture_output=True)
    with open(os.path.join(out, "ab.txt"), "w") as f:
        f.write(f"{a.style}, seed {a.seed}, {a.bars} bars. A: commit {short}'s round. B: today's.\n"
                "Which is better, and why? Each clip's .txt says what changed in its round.\n")
    print(out)


if __name__ == "__main__":
    main()
