import os
import json


def load_config(base_dir):
    """Read config.json and transcript.txt, return a unified config dict."""
    config_path = os.path.join(base_dir, "data", "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    transcript_path = os.path.join(base_dir, "data", "transcript.txt")
    with open(transcript_path, "r") as f:
        transcript = f.read()

    return {
        "voices": config["voices"],
        "output": config["output"],
        "system_prompt": config["podcast"]["system_prompt"],
        "episode_prompt": config["podcast"]["episode_prompt"].format(transcript=transcript),
        "model": config["openai"]["model"],
    }
