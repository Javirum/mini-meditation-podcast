import os
import argparse
import logging

from dotenv import load_dotenv
from src.openai_client import OpenAIClient
from src.config import load_config
from src.dialogue import parse_dialogue, save_dialogue
from src.audio import generate_segments, combine_segments

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser(description="Generate a meditation podcast episode")
    parser.add_argument("--config", default=None, help="Path to config JSON (default: data/config.json)")
    parser.add_argument("--transcript", default=None, help="Path to transcript file (default: data/transcript.txt)")
    parser.add_argument("--no-cache", action="store_true", help="Force regeneration of all audio segments")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 1. Load configuration and data
    cfg = load_config(BASE_DIR, config_path=args.config, transcript_path=args.transcript)

    # 2. Generate dialogue via OpenAI
    client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
    dialogue_text = client.generate_dialogue(cfg["model"], cfg["system_prompt"], cfg["episode_prompt"])
    logger.info("Dialogue generated:\n%s", dialogue_text)

    # 3. Parse and save dialogue
    lines = parse_dialogue(dialogue_text, cfg["voices"])
    save_dialogue(lines, os.path.join(BASE_DIR, cfg["output"]["dialogue_file"]))

    # 4. Generate audio segments and combine into final podcast
    segments_dir = os.path.join(BASE_DIR, cfg["output"]["segments_dir"])
    segment_files = generate_segments(
        lines,
        cfg["voices"],
        client,
        segments_dir,
        tts_model=cfg["tts_model"],
        no_cache=args.no_cache,
    )
    combine_segments(
        segment_files,
        os.path.join(BASE_DIR, cfg["output"]["podcast_file"]),
        pause_ms=cfg["output"].get("pause_ms", 700),
    )


if __name__ == "__main__":
    main()
