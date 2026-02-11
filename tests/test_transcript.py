from unittest.mock import patch, MagicMock

import pytest

from src.transcript import (
    extract_from_text,
    extract_from_pdf,
    extract_from_audio,
    process_upload,
)


# --- extract_from_text ---

def test_extract_from_text(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("Hello, world!")
    assert extract_from_text(str(f)) == "Hello, world!"


# --- extract_from_pdf ---

@patch("pypdf.PdfReader")
def test_extract_from_pdf(mock_reader_cls):
    page1 = MagicMock()
    page1.extract_text.return_value = "Page 1 text"
    page2 = MagicMock()
    page2.extract_text.return_value = "Page 2 text"
    mock_reader_cls.return_value.pages = [page1, page2]

    result = extract_from_pdf("dummy.pdf")

    assert result == "Page 1 text\nPage 2 text"
    mock_reader_cls.assert_called_once_with("dummy.pdf")


# --- extract_from_audio ---

def test_extract_from_audio():
    mock_client = MagicMock()
    mock_client.transcribe_audio.return_value = "transcribed text"
    result = extract_from_audio("audio.mp3", mock_client)
    assert result == "transcribed text"
    mock_client.transcribe_audio.assert_called_once_with("audio.mp3")


# --- process_upload ---

def test_process_upload_txt(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("Some transcript content")
    assert process_upload(str(f)) == "Some transcript content"


@patch("src.transcript.extract_from_pdf", return_value="pdf content")
def test_process_upload_pdf(mock_extract):
    result = process_upload("report.pdf")
    assert result == "pdf content"
    mock_extract.assert_called_once_with("report.pdf")


def test_process_upload_audio():
    mock_client = MagicMock()
    mock_client.transcribe_audio.return_value = "audio transcript"
    result = process_upload("lecture.mp3", client=mock_client)
    assert result == "audio transcript"
    mock_client.transcribe_audio.assert_called_once_with("lecture.mp3")


def test_process_upload_audio_no_client_raises():
    with pytest.raises(ValueError, match="OpenAI client required"):
        process_upload("lecture.mp3")


def test_process_upload_unsupported_raises():
    with pytest.raises(ValueError, match="Unsupported file type"):
        process_upload("document.docx")
