# SPDX-License-Identifier: GPL-3.0-or-later
import json
import shutil

import pytest

from maestro.stylebook import BOOK, HERE, ROLES, STYLES, StyleError, load, make
from maestro.theory.chords import Vocabulary
from maestro.theory.form import FORM, Form
from maestro.theory.rhythm import Feel, Rhythm
from maestro.theory.voicing import RANGES, UNPITCHED


def test_the_book_loads_every_style_in_order():
    assert STYLES == ("plain", "trap", "synthwave", "salsa", "power_rock") == tuple(FORM)
    assert all(BOOK[s]["license"] == "CC BY-SA 4.0" and BOOK[s]["sources"] for s in STYLES)


def test_roles_are_the_bands_members():
    assert set(ROLES) == set(RANGES) | set(UNPITCHED)


def test_json_turns_into_the_theorys_values():
    f = make(Form, {"why": "words", "phrases": {"1": 1}, "wave": [4, 7], "depth": 1, "modes": ["minor"]}, "t")
    assert f.phrases == {1: 1} and f.wave == (4, 7) and f.depth == 1.0 and isinstance(f.depth, float)
    v = make(Vocabulary, {"colours": [None, "7"], "borrow": None}, "t")
    assert v.colours == frozenset((None, "7")) and v.borrow is None


@pytest.mark.parametrize("cls, data, says", [
    (Rhythm, {"tripplet": 2}, "unknown part 'tripplet'"),
    (Rhythm, {"lift": "3"}, "t.lift: expected int"),
    (Rhythm, {"lift": True}, "t.lift: expected int"),
    (Rhythm, {"lift": None}, "t.lift: can't be left empty"),
    (Rhythm, {"clave": "son_3-3"}, "unknown clave"),
    (Vocabulary, {"qualities": ["maj", "minor"]}, "unknown quality 'minor'"),
    (Vocabulary, {"borrow": ["dorain"]}, "unknown scale 'dorain'"),
    (Form, {"moves": {"leap": 1}}, "unknown key move 'leap'"),
    (Form, {"phrases": {"two": 1}}, "t.phrases: expected dict"),
    (Feel, {"pulse": "quarter"}, "unknown pulse"),
    (Feel, {"swing": 9}, "swing goes from 0 to 6"),
])
def test_a_bad_field_says_where(cls, data, says):
    with pytest.raises(StyleError, match=says.replace("(", r"\(")):
        make(cls, data, "t")


def _book(tmp_path, style="trap", change=None):
    """A copy of the book with one style's entry changed."""
    folder = tmp_path / "styles"
    shutil.copytree(HERE, folder)
    if change:
        p = folder / f"{style}.json"
        entry = json.loads(p.read_text())
        change(entry)
        p.write_text(json.dumps(entry))
    return folder


@pytest.mark.parametrize("change, says", [
    (lambda e: e.update(style="drill"), "not its file name"),
    (lambda e: e.update(license="CC BY-NC 4.0"), "style data is CC BY-SA 4.0"),
    (lambda e: e.update(sources=[]), "must cite at least one source"),
    (lambda e: e.update(mood="dark"), "unknown part 'mood'"),
    (lambda e: e["time"].update(tempo=1000), "time.tempo must be a whole BPM"),
    (lambda e: e["time"]["feel"].update(drum={}), "time.feel: unknown part 'drum'"),
    (lambda e: e["members"].update({"808": {"sound": 38}}), "members: unknown part '808'"),
    (lambda e: e["members"]["pad"].update(sound=128), "members.pad.sound must be a whole number from 0 to 127"),
    (lambda e: e["harmony"].update(chords={}), "harmony: unknown part 'chords'"),
])
def test_a_bad_file_says_where(tmp_path, change, says):
    with pytest.raises(StyleError, match=f"trap: .*{says}"):
        load(_book(tmp_path, change=change))


def test_the_book_and_its_folder_agree(tmp_path):
    folder = _book(tmp_path)
    (folder / "drill.json").write_text("{}")
    with pytest.raises(StyleError, match="book.json lists"):
        load(folder)
    (folder / "drill.json").unlink()
    (folder / "trap.json").write_text("{not json")
    with pytest.raises(StyleError, match="trap: not valid JSON"):
        load(folder)
