from unittest.mock import patch, MagicMock

import pytest

from src.openai_client import OpenAIClient


def _mock_response(status_code=400):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {}
    return resp


# --- Constructor ---

@patch("src.openai_client.OpenAI")
def test_init_empty_key_raises(mock_cls):
    with pytest.raises(ValueError, match="API key"):
        OpenAIClient("")


@patch("src.openai_client.OpenAI")
def test_init_none_key_raises(mock_cls):
    with pytest.raises(ValueError, match="API key"):
        OpenAIClient(None)


@patch("src.openai_client.OpenAI")
def test_init_valid_key(mock_cls):
    client = OpenAIClient("sk-test")
    mock_cls.assert_called_once_with(api_key="sk-test")


# --- generate_dialogue ---

@patch("src.openai_client.OpenAI")
def test_dialogue_returns_text(mock_cls):
    mock_instance = mock_cls.return_value
    mock_instance.responses.create.return_value.output_text = "COACH: Hello."
    client = OpenAIClient("sk-test")
    result = client.generate_dialogue("gpt-4o-mini", "system", "episode")
    assert result == "COACH: Hello."
    mock_instance.responses.create.assert_called_once_with(
        model="gpt-4o-mini", instructions="system", input="episode",
    )


@patch("src.openai_client.OpenAI")
def test_dialogue_empty_response_raises(mock_cls):
    mock_instance = mock_cls.return_value
    mock_instance.responses.create.return_value.output_text = ""
    client = OpenAIClient("sk-test")
    with pytest.raises(ValueError, match="empty"):
        client.generate_dialogue("model", "sys", "ep")


@patch("src.openai_client.OpenAI")
def test_dialogue_connection_error(mock_cls):
    from openai import APIConnectionError
    mock_instance = mock_cls.return_value
    mock_instance.responses.create.side_effect = APIConnectionError(request=MagicMock())
    client = OpenAIClient("sk-test")
    with pytest.raises(ConnectionError):
        client.generate_dialogue("model", "sys", "ep")


@patch("src.openai_client.OpenAI")
def test_dialogue_rate_limit(mock_cls):
    from openai import RateLimitError
    mock_instance = mock_cls.return_value
    mock_instance.responses.create.side_effect = RateLimitError(
        response=_mock_response(429), body=None, message="rate limited",
    )
    client = OpenAIClient("sk-test")
    with pytest.raises(RuntimeError, match="rate limit"):
        client.generate_dialogue("model", "sys", "ep")


@patch("src.openai_client.OpenAI")
def test_dialogue_status_error(mock_cls):
    from openai import APIStatusError
    mock_instance = mock_cls.return_value
    mock_instance.responses.create.side_effect = APIStatusError(
        message="server error", response=_mock_response(500), body=None,
    )
    client = OpenAIClient("sk-test")
    with pytest.raises(RuntimeError, match="500"):
        client.generate_dialogue("model", "sys", "ep")


# --- generate_speech ---

@patch("src.openai_client.OpenAI")
def test_speech_streams_to_file(mock_cls):
    mock_instance = mock_cls.return_value
    mock_ctx = MagicMock()
    mock_instance.audio.speech.with_streaming_response.create.return_value.__enter__ = MagicMock(return_value=mock_ctx)
    mock_instance.audio.speech.with_streaming_response.create.return_value.__exit__ = MagicMock(return_value=False)
    client = OpenAIClient("sk-test")
    client.generate_speech("Hello", "nova", "tts-1", "/tmp/out.mp3")
    mock_ctx.stream_to_file.assert_called_once_with("/tmp/out.mp3")


@patch("src.openai_client.OpenAI")
def test_speech_connection_error(mock_cls):
    from openai import APIConnectionError
    mock_instance = mock_cls.return_value
    mock_instance.audio.speech.with_streaming_response.create.side_effect = APIConnectionError(
        request=MagicMock(),
    )
    client = OpenAIClient("sk-test")
    with pytest.raises(ConnectionError):
        client.generate_speech("Hi", "nova", "tts-1", "/tmp/out.mp3")


@patch("src.openai_client.OpenAI")
def test_speech_rate_limit(mock_cls):
    from openai import RateLimitError
    mock_instance = mock_cls.return_value
    mock_instance.audio.speech.with_streaming_response.create.side_effect = RateLimitError(
        response=_mock_response(429), body=None, message="rate limited",
    )
    client = OpenAIClient("sk-test")
    with pytest.raises(RuntimeError, match="rate limit"):
        client.generate_speech("Hi", "nova", "tts-1", "/tmp/out.mp3")


@patch("src.openai_client.OpenAI")
def test_speech_status_error(mock_cls):
    from openai import APIStatusError
    mock_instance = mock_cls.return_value
    mock_instance.audio.speech.with_streaming_response.create.side_effect = APIStatusError(
        message="bad request", response=_mock_response(400), body=None,
    )
    client = OpenAIClient("sk-test")
    with pytest.raises(RuntimeError, match="400"):
        client.generate_speech("Hi", "nova", "tts-1", "/tmp/out.mp3")


# --- transcribe_audio ---

@patch("builtins.open", new_callable=MagicMock)
@patch("src.openai_client.OpenAI")
def test_transcribe_returns_text(mock_cls, mock_open):
    mock_instance = mock_cls.return_value
    mock_instance.audio.transcriptions.create.return_value.text = "Hello from Whisper"
    client = OpenAIClient("sk-test")
    result = client.transcribe_audio("/tmp/audio.mp3")
    assert result == "Hello from Whisper"
    mock_instance.audio.transcriptions.create.assert_called_once()


@patch("builtins.open", new_callable=MagicMock)
@patch("src.openai_client.OpenAI")
def test_transcribe_empty_raises(mock_cls, mock_open):
    mock_instance = mock_cls.return_value
    mock_instance.audio.transcriptions.create.return_value.text = ""
    client = OpenAIClient("sk-test")
    with pytest.raises(ValueError, match="empty transcription"):
        client.transcribe_audio("/tmp/audio.mp3")


@patch("builtins.open", new_callable=MagicMock)
@patch("src.openai_client.OpenAI")
def test_transcribe_connection_error(mock_cls, mock_open):
    from openai import APIConnectionError
    mock_instance = mock_cls.return_value
    mock_instance.audio.transcriptions.create.side_effect = APIConnectionError(request=MagicMock())
    client = OpenAIClient("sk-test")
    with pytest.raises(ConnectionError):
        client.transcribe_audio("/tmp/audio.mp3")


@patch("builtins.open", new_callable=MagicMock)
@patch("src.openai_client.OpenAI")
def test_transcribe_rate_limit(mock_cls, mock_open):
    from openai import RateLimitError
    mock_instance = mock_cls.return_value
    mock_instance.audio.transcriptions.create.side_effect = RateLimitError(
        response=_mock_response(429), body=None, message="rate limited",
    )
    client = OpenAIClient("sk-test")
    with pytest.raises(RuntimeError, match="rate limit"):
        client.transcribe_audio("/tmp/audio.mp3")
