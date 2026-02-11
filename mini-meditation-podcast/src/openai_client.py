from openai import OpenAI


class OpenAIClient:
    def __init__(self, api_key):
        self._client = OpenAI(api_key=api_key)

    def generate_dialogue(self, model, system_prompt, episode_prompt):
        response = self._client.responses.create(
            model=model,
            instructions=system_prompt,
            input=episode_prompt,
        )
        return response.output_text

    def generate_speech(self, text, voice, model, output_path):
        with self._client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=text,
        ) as response:
            response.stream_to_file(output_path)
