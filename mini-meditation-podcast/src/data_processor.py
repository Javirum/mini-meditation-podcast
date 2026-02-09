import os
import json
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
import edge_tts
from pydub import AudioSegment

load_dotenv()

# ── 1. Load data from multiple file sources ──────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Source 1: JSON configuration (voices, prompts, model settings, output paths)
config_path = os.path.join(BASE_DIR, "data", "config.json")
with open(config_path, "r") as f:
    config = json.load(f)

# Source 2: Plain-text transcript file
transcript_path = os.path.join(BASE_DIR, "data", "transcript.txt")
with open(transcript_path, "r") as f:
    transcript = f.read()

# ── 2. Build structured data from config ─────────────────────────────

voices = config["voices"]                         # dict  – speaker → TTS voice ID
output_paths = config["output"]                    # dict  – logical name → file path
system_prompt = config["podcast"]["system_prompt"]  # str
episode_prompt = config["podcast"]["episode_prompt"].format(transcript=transcript)
model = config["openai"]["model"]                  # str

# ── 3. Generate dialogue via OpenAI API ──────────────────────────────

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

openai_response = client.responses.create(
    model=model,
    instructions=system_prompt,
    input=episode_prompt,
)

dialogue_text = openai_response.output_text
print(dialogue_text)

# ── 4. Parse dialogue into a list of dicts ───────────────────────────

lines = []
for raw_line in dialogue_text.strip().splitlines():
    raw_line = raw_line.strip()
    for speaker in voices:
        if raw_line.upper().startswith(f"{speaker}:"):
            lines.append({
                "speaker": speaker,
                "text": raw_line.split(":", 1)[1].strip(),
            })
            break

# ── 5. Write dialogue to a text file (intermediate output) ──────────

dialogue_out = os.path.join(BASE_DIR, output_paths["dialogue_file"])
os.makedirs(os.path.dirname(dialogue_out), exist_ok=True)

with open(dialogue_out, "w") as f:
    for line in lines:
        f.write(f"{line['speaker']}: {line['text']}\n")
print(f"Dialogue saved to {dialogue_out}")

# ── 6. Generate & combine audio ─────────────────────────────────────

async def main():
    segments_dir = os.path.join(BASE_DIR, output_paths["segments_dir"])
    os.makedirs(segments_dir, exist_ok=True)

    # Generate one MP3 per dialogue line
    segment_files = []
    for i, line in enumerate(lines, start=1):
        out_file = os.path.join(segments_dir, f"{i:03d}_{line['speaker']}.mp3")
        tts = edge_tts.Communicate(text=line["text"], voice=voices[line["speaker"]])
        await tts.save(out_file)
        segment_files.append(out_file)
    print("Audio segments generated successfully.")

    # Concatenate all segments into a single podcast file
    combined = AudioSegment.empty()
    for seg in segment_files:
        combined += AudioSegment.from_mp3(seg)

    podcast_out = os.path.join(BASE_DIR, output_paths["podcast_file"])
    combined.export(podcast_out, format="mp3")
    print(f"Combined podcast saved to {podcast_out}")

asyncio.run(main())
