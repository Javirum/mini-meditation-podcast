import os
import logging

logger = logging.getLogger(__name__)


def parse_dialogue(raw_text, voices):
    """Split raw dialogue text into a list of {speaker, text} dicts."""
    lines = []
    for raw_line in raw_text.strip().splitlines():
        raw_line = raw_line.strip()
        for speaker in voices:
            if raw_line.upper().startswith(f"{speaker}:"):
                lines.append({
                    "speaker": speaker,
                    "text": raw_line.split(":", 1)[1].strip(),
                })
                break
    return lines


def save_dialogue(lines, output_path):
    """Write parsed dialogue lines to a text file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        for line in lines:
            f.write(f"{line['speaker']}: {line['text']}\n")
    logger.info("Dialogue saved to %s", output_path)
