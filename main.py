import os
from dotenv import load_dotenv
from src.openai_client import OpenAIClient
from src.config import load_config
from src.dialogue import parse_dialogue, save_dialogue
from src.audio import generate_segments, combine_segments

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Load configuration and data
cfg = load_config(BASE_DIR)

# 2. Generate dialogue via OpenAI
client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
dialogue_text = client.generate_dialogue(cfg["model"], cfg["system_prompt"], cfg["episode_prompt"])
print(dialogue_text)

# 3. Parse and save dialogue
lines = parse_dialogue(dialogue_text, cfg["voices"])
save_dialogue(lines, os.path.join(BASE_DIR, cfg["output"]["dialogue_file"]))

# 4. Generate audio segments and combine into final podcast
segments_dir = os.path.join(BASE_DIR, cfg["output"]["segments_dir"])
segment_files = generate_segments(lines, cfg["voices"], client, segments_dir)
combine_segments(segment_files, os.path.join(BASE_DIR, cfg["output"]["podcast_file"]))
