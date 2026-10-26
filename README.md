# Maestro

The composer of the Orchestra: the music brain that will drive Ouralia's generative music.

Status: bucket 3 of 6 (the style book) under way: the theory core is done, and the trap and synthwave entries are written.

## The idea

Maestro learns what makes music music: theory (scales, harmony, voice leading, rhythm, form) and what sets genres
apart (EDM, future bass, synthwave, chillwave, ambient, afrobeat, salsa, rock, hip hop, trap, ...). It can be big on
the computer, and a small version distilled from it runs on the phone.

## Where it stands

`PLAN.md` holds the goal, DadCraft's decisions and the buckets (checked off as they're done).
`docs/research.md`: what other music AI projects teach us. `docs/dadcraft-brief.md`: how DadCraft wants it run.

## Running it

    python3 -m venv .venv && .venv/bin/pip install -e '.[test]'
    .venv/bin/python -m pytest -q          # unit tests; parity with Ouralia's composer when ../Ouralia is built
    python3 tools/sync_check.py            # is the port in step with Ouralia's dcs_composer.c?
    .venv/bin/python tests/exam/exam.py    # the theory exam's score card (--all: every question and why)
    .venv/bin/python -m maestro.explain salsa --seed 7   # a few bars of choices, in plain words

The parity test needs Ouralia beside this repo (or `MAESTRO_OURALIA`), with its test build: `tools/build_libpd.sh`
and `make -C dcs` there. It only reads Ouralia, never changes it.

## License

- **Code:** GPL-3.0-or-later (`LICENSE`), the same as Ouralia.
- **Docs and the style book** (`*.md`, `docs/`, style data): CC BY-SA 4.0 (`LICENSE-docs`).
- **Trained models:** the model that ships in Ouralia is trained only on data that allows commercial use and is
  released under CC BY-SA 4.0, with credits for its data. Models trained with NC data stay on the PC, under
  CC BY-NC-SA 4.0. Data sets are not shared here; each keeps its own license. Credits: `CREDITS.md`.
