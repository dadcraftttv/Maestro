# SPDX-License-Identifier: GPL-3.0-or-later
from exam import EXAM, LEVELS, TOPICS, run


def test_every_question_is_well_formed():
    assert {q.topic for q in EXAM} == set(TOPICS) and {q.level for q in EXAM} == set(LEVELS)
    assert len({q.question for q in EXAM}) == len(EXAM)
    assert all(q.why for q in EXAM)


def test_maestro_passes_the_exam():
    """Every question right, except the marked gaps; a gap answered right must lose its mark."""
    wrong = [f"{q.question} wanted {q.answer!r}, got {got!r}" for q, got, ok in run() if not ok and not q.gap]
    healed = [q.question for q, _, ok in run() if ok and q.gap]
    assert not wrong, "\n".join(wrong)
    assert not healed, f"answered right now, take the gap mark off: {healed}"
