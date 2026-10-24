# Maestro — notes for Claude Code

Maestro is the music brain for Ouralia (see `README.md`). Owner: **DadCraft**: always call him that, in files,
commits and replies; never a real name. Public on GitHub: dadcraftttv/Maestro (since Oct 23).

## Start of every session
1. Read `PLAN.md`: the goal, DadCraft's decisions, the buckets and the **Next** line. It is the only status file.
2. Do one task (DadCraft wants it task by task to keep token cost low). Don't read `docs/research.md` or other docs
   whole: grep the part the task needs.
3. In the same commit that finishes a task: tick it in `PLAN.md`, move **Next**, note any verdict of DadCraft's in
   `docs/verdicts.md`, and update Maestro's entry in Conductor's `docs/items.md`.

## How DadCraft wants it run (his brief, `docs/dadcraft-brief.md`)
- Small agile buckets, one at a time: present a plan for each, then a checkpoint where he reviews the output.
- Verify key decisions with him explicitly, so we don't drift from the original intent. New decisions go into
  PLAN.md's list once he confirms them.
- Only DadCraft judges sound. Before he listens, check what can be measured (the style judge, tests), and tell him
  exactly what to listen for.

## Rules
- Data: only openly licensed sets, each tagged with its license; NC sets kept apart and never in the phone model
  (PLAN.md decision 7). Record every set in `docs/data.md` and its credit in `CREDITS.md` before using it.
- Licenses: code GPL-3.0-or-later, docs and style data CC BY-SA 4.0 (README "License").
- Learn from other projects' ideas; don't copy their code wholesale, and check a license before using any code or
  weights.
- Ouralia work (bucket 6) follows Ouralia's own CLAUDE.md.
- Conductor's rules apply too: scoped searches, capped output, big public inputs to `scripts/ask.py`, subagents for
  small checkable tasks only.
