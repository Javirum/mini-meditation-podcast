import logging

from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self._client = OpenAI(api_key=api_key)

    def generate_dialogue(self, model, system_prompt, episode_prompt):
        try:
            response = self._client.responses.create(
                model=model,
                instructions=system_prompt,
                input=episode_prompt,
            )
        except APIConnectionError:
            raise ConnectionError("Failed to connect to OpenAI API")
        except RateLimitError:
            raise RuntimeError("OpenAI API rate limit exceeded — try again later")
        except APIStatusError as e:
            raise RuntimeError(f"OpenAI API error ({e.status_code}): {e.message}")

        if not response.output_text:
            raise ValueError("OpenAI returned an empty dialogue response")
        return response.output_text

    def generate_speech(self, text, voice, model, output_path):
        try:
            with self._client.audio.speech.with_streaming_response.create(
                model=model,
                voice=voice,
                input=text,
            ) as response:
                response.stream_to_file(output_path)
        except APIConnectionError:
            raise ConnectionError("Failed to connect to OpenAI TTS API")
        except RateLimitError:
            raise RuntimeError("OpenAI TTS rate limit exceeded — try again later")
        except APIStatusError as e:
            raise RuntimeError(f"OpenAI TTS error ({e.status_code}): {e.message}")

    def transcribe_audio(self, audio_path):
        try:
            with open(audio_path, "rb") as f:
                transcription = self._client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                )
            if not transcription.text:
                raise ValueError("OpenAI returned an empty transcription")
            return transcription.text
        except APIConnectionError:
            raise ConnectionError("Failed to connect to OpenAI Whisper API")
        except RateLimitError:
            raise RuntimeError("OpenAI Whisper rate limit exceeded — try again later")
        except APIStatusError as e:
            raise RuntimeError(f"OpenAI Whisper error ({e.status_code}): {e.message}")
