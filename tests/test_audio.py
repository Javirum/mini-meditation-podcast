import hashlib
import os
from unittest.mock import patch, MagicMock, call

import pytest

from src.audio import _segment_hash, generate_segments, combine_segments

VOICES = {"COACH": "nova", "STUDENT": "echo"}


# --- _segment_hash ---

def test_hash_length_and_hex():
    h = _segment_hash("text", "nova", "tts-1")
    assert len(h) == 16
    assert all(c in "0123456789abcdef" for c in h)


def test_hash_deterministic():
    assert _segment_hash("a", "b", "c") == _segment_hash("a", "b", "c")


def test_hash_differs_for_different_inputs():
    h1 = _segment_hash("hello", "nova", "tts-1")
    h2 = _segment_hash("world", "echo", "tts-1-hd")
    assert h1 != h2


def test_hash_matches_manual():
    expected = hashlib.sha256("text|voice|model".encode()).hexdigest()[:16]
    assert _segment_hash("text", "voice", "model") == expected


# --- generate_segments ---

@patch("src.audio.tqdm", side_effect=lambda x, **kw: x)
def test_calls_client_per_line(mock_tqdm, tmp_path):
    lines = [
        {"speaker": "COACH", "text": "Welcome."},
        {"speaker": "STUDENT", "text": "Thanks."},
    ]
    client = MagicMock()
    result = generate_segments(lines, VOICES, client, str(tmp_path), tts_model="tts-1")
    assert client.generate_speech.call_count == 2
    assert len(result) == 2
    # Verify correct args for first call
    first_call = client.generate_speech.call_args_list[0]
    assert first_call == call(text="Welcome.", voice="nova", model="tts-1", output_path=result[0])


@patch("src.audio.tqdm", side_effect=lambda x, **kw: x)
def test_cache_hit_skips_client(mock_tqdm, tmp_path):
    lines = [{"speaker": "COACH", "text": "Hello."}]
    client = MagicMock()
    # Pre-create the mp3 and hash files
    mp3_path = tmp_path / "001_COACH.mp3"
    mp3_path.write_bytes(b"fake audio")
    hash_path = tmp_path / "001_COACH.mp3.hash"
    hash_path.write_text(_segment_hash("Hello.", "nova", "tts-1"))

    generate_segments(lines, VOICES, client, str(tmp_path), tts_model="tts-1")
    client.generate_speech.assert_not_called()


@patch("src.audio.tqdm", side_effect=lambda x, **kw: x)
def test_no_cache_forces_regen(mock_tqdm, tmp_path):
    lines = [{"speaker": "COACH", "text": "Hello."}]
    client = MagicMock()
    # Pre-create cached files
    mp3_path = tmp_path / "001_COACH.mp3"
    mp3_path.write_bytes(b"fake audio")
    hash_path = tmp_path / "001_COACH.mp3.hash"
    hash_path.write_text(_segment_hash("Hello.", "nova", "tts-1"))

    generate_segments(lines, VOICES, client, str(tmp_path), tts_model="tts-1", no_cache=True)
    client.generate_speech.assert_called_once()


@patch("src.audio.tqdm", side_effect=lambda x, **kw: x)
def test_stale_cache_regenerates(mock_tqdm, tmp_path):
    lines = [{"speaker": "COACH", "text": "Hello."}]
    client = MagicMock()
    # Pre-create with wrong hash
    mp3_path = tmp_path / "001_COACH.mp3"
    mp3_path.write_bytes(b"fake audio")
    hash_path = tmp_path / "001_COACH.mp3.hash"
    hash_path.write_text("wrong_hash_value!")

    generate_segments(lines, VOICES, client, str(tmp_path), tts_model="tts-1")
    client.generate_speech.assert_called_once()


@patch("src.audio.tqdm", side_effect=lambda x, **kw: x)
def test_writes_hash_file(mock_tqdm, tmp_path):
    lines = [{"speaker": "COACH", "text": "Hello."}]
    client = MagicMock()
    generate_segments(lines, VOICES, client, str(tmp_path), tts_model="tts-1")
    hash_path = tmp_path / "001_COACH.mp3.hash"
    assert hash_path.exists()
    assert hash_path.read_text() == _segment_hash("Hello.", "nova", "tts-1")


@patch("src.audio.tqdm", side_effect=lambda x, **kw: x)
def test_custom_tts_model(mock_tqdm, tmp_path):
    lines = [{"speaker": "COACH", "text": "Hi."}]
    client = MagicMock()
    generate_segments(lines, VOICES, client, str(tmp_path), tts_model="tts-1-hd")
    client.generate_speech.assert_called_once_with(
        text="Hi.", voice="nova", model="tts-1-hd",
        output_path=os.path.join(str(tmp_path), "001_COACH.mp3"),
    )


# --- combine_segments ---

@patch("src.audio.AudioSegment")
def test_concatenates_with_pauses(mock_audio_cls):
    mock_combined = MagicMock()
    mock_combined.__iadd__ = MagicMock(return_value=mock_combined)
    mock_audio_cls.empty.return_value = mock_combined
    mock_audio_cls.silent.return_value = MagicMock()
    mock_audio_cls.from_mp3.side_effect = [MagicMock(), MagicMock()]

    combine_segments(["a.mp3", "b.mp3"], "out.mp3")

    mock_audio_cls.from_mp3.assert_any_call("a.mp3")
    mock_audio_cls.from_mp3.assert_any_call("b.mp3")
    mock_audio_cls.silent.assert_called_once_with(duration=700)
    mock_combined.export.assert_called_once_with("out.mp3", format="mp3")


@patch("src.audio.AudioSegment")
def test_custom_pause_duration(mock_audio_cls):
    mock_audio_cls.empty.return_value = MagicMock()
    mock_audio_cls.from_mp3.return_value = MagicMock()

    combine_segments(["a.mp3", "b.mp3"], "out.mp3", pause_ms=1000)
    mock_audio_cls.silent.assert_called_once_with(duration=1000)


@patch("src.audio.AudioSegment")
def test_single_file_no_pause(mock_audio_cls):
    mock_empty = MagicMock()
    mock_audio_cls.empty.return_value = mock_empty
    mock_audio_cls.from_mp3.return_value = MagicMock()

    combine_segments(["only.mp3"], "out.mp3")
    mock_audio_cls.silent.assert_called_once()  # pause object is created
    # But __iadd__ should only be called with the segment, not the pause
    # The pause is created but never added because i==0 for the only element
    calls = mock_empty.__iadd__.call_args_list
    # First call should be with the segment (not the pause)
    assert len(calls) == 1
