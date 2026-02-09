import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import asyncio, json, os
import edge_tts
from pydub import AudioSegment

load_dotenv()

BASE_DIR = Path(__file__).parent

# Configuration
prompt ="Use the provided transcript of a coaching session to create a soothing meditation script. The meditation should help listeners embrace the challenges of learning to code, transforming feelings of frustration and imposter syndrome into acceptance and growth. The script should be calming, encouraging, and empowering, guiding listeners to find peace in the process of learning and overcoming obstacles."

#OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VOICES = {
    "COACH": "en-US-GuyNeural",
    "STUDENT": "en-US-JennyNeural"
}

async def speak_line(text: str, voice: str, out_path: str):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(out_path)

async def main():
    with open(BASE_DIR / "script.json", "r", encoding="utf-8") as f:
        lines = json.load(f)

    os.makedirs("output/segments", exist_ok=True)

    for i, line in enumerate(lines, start=1):
        speaker = line["speaker"]
        text = line["text"]

        voice = VOICES.get(speaker, "en-US-GuyNeural")  # fallback
        out_file = f"output/segments/{i:03d}_{speaker}.mp3"

        await speak_line(text, voice, out_file)

asyncio.run(main())
print("Audio segments generated successfully.")

# Concatenate all segments into a single file
segments_dir = "output/segments"
segment_files = sorted(f for f in os.listdir(segments_dir) if f.endswith(".mp3"))

combined = AudioSegment.empty()
for filename in segment_files:
    segment = AudioSegment.from_mp3(os.path.join(segments_dir, filename))
    combined += segment

combined.export("output/meditation_podcast.mp3", format="mp3")
print("Combined podcast saved to output/meditation_podcast.mp3")
