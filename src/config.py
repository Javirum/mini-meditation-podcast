import os
import json
import logging

logger = logging.getLogger(__name__)


def load_config(base_dir, config_path=None, transcript_path=None):
    """Read config.json and transcript.txt, return a unified config dict."""
    config_path = config_path or os.path.join(base_dir, "data", "config.json")
    transcript_path = transcript_path or os.path.join(base_dir, "data", "transcript.txt")

    logger.info("Loading config from %s", config_path)
    with open(config_path, "r") as f:
        config = json.load(f)

    logger.info("Loading transcript from %s", transcript_path)
    with open(transcript_path, "r") as f:
        transcript = f.read()

    return {
        "voices": config["voices"],
        "output": config["output"],
        "system_prompt": config["podcast"]["system_prompt"],
        "episode_prompt": config["podcast"]["episode_prompt"].format(transcript=transcript),
        "model": config["openai"]["model"],
        "tts_model": config["openai"].get("tts_model", "tts-1"),
    }
