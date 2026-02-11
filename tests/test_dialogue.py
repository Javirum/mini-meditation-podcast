import os

from src.dialogue import parse_dialogue, save_dialogue

VOICES = {"COACH": "nova", "STUDENT": "echo"}


# --- parse_dialogue ---

def test_parse_basic():
    raw = "COACH: Welcome.\nSTUDENT: Thank you."
    result = parse_dialogue(raw, VOICES)
    assert result == [
        {"speaker": "COACH", "text": "Welcome."},
        {"speaker": "STUDENT", "text": "Thank you."},
    ]


def test_parse_case_insensitive():
    raw = "coach: Hello there."
    result = parse_dialogue(raw, VOICES)
    assert result == [{"speaker": "COACH", "text": "Hello there."}]


def test_parse_skips_unrecognized():
    raw = "NARRATOR: Once upon a time.\nCOACH: Begin."
    result = parse_dialogue(raw, VOICES)
    assert len(result) == 1
    assert result[0]["speaker"] == "COACH"


def test_parse_skips_blank_lines():
    raw = "COACH: One.\n\n   \nSTUDENT: Two."
    result = parse_dialogue(raw, VOICES)
    assert len(result) == 2


def test_parse_preserves_colons_in_text():
    raw = "COACH: Time is 3:00 pm."
    result = parse_dialogue(raw, VOICES)
    assert result[0]["text"] == "Time is 3:00 pm."


def test_parse_empty_input():
    assert parse_dialogue("", VOICES) == []


def test_parse_strips_whitespace():
    raw = "  COACH:   Hello.  \n  STUDENT:   Hi.  "
    result = parse_dialogue(raw, VOICES)
    assert result[0]["text"] == "Hello."
    assert result[1]["text"] == "Hi."


# --- save_dialogue ---

def test_save_writes_file(tmp_path):
    out = tmp_path / "dialogue.txt"
    lines = [
        {"speaker": "COACH", "text": "Welcome."},
        {"speaker": "STUDENT", "text": "Thanks."},
    ]
    save_dialogue(lines, str(out))
    content = out.read_text()
    assert content == "COACH: Welcome.\nSTUDENT: Thanks.\n"


def test_save_creates_nested_dirs(tmp_path):
    out = tmp_path / "a" / "b" / "c" / "dialogue.txt"
    save_dialogue([{"speaker": "COACH", "text": "Hi."}], str(out))
    assert out.exists()


def test_save_empty_lines(tmp_path):
    out = tmp_path / "empty.txt"
    save_dialogue([], str(out))
    assert out.read_text() == ""
