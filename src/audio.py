import os
import hashlib
import logging

from pydub import AudioSegment
from tqdm import tqdm

logger = logging.getLogger(__name__)


def _segment_hash(text, voice, tts_model):
    """Compute a short hash identifying a unique TTS request."""
    key = f"{text}|{voice}|{tts_model}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def generate_segments(lines, voices, client, segments_dir, tts_model="tts-1", no_cache=False, progress_callback=None):
    """Call TTS for each dialogue line, return list of segment file paths."""
    os.makedirs(segments_dir, exist_ok=True)
    segment_files = []

    for i, line in enumerate(tqdm(lines, desc="Generating segments", unit="seg"), start=1):
        voice = voices[line["speaker"]]
        out_file = os.path.join(segments_dir, f"{i:03d}_{line['speaker']}.mp3")
        hash_file = out_file + ".hash"
        current_hash = _segment_hash(line["text"], voice, tts_model)

        # Check cache
        if not no_cache and os.path.exists(out_file) and os.path.exists(hash_file):
            with open(hash_file, "r") as f:
                if f.read().strip() == current_hash:
                    logger.info("Cached segment %d/%d (%s)", i, len(lines), line["speaker"])
                    segment_files.append(out_file)
                    continue

        logger.info("Generating segment %d/%d (%s)", i, len(lines), line["speaker"])
        client.generate_speech(
            text=line["text"],
            voice=voice,
            model=tts_model,
            output_path=out_file,
        )

        with open(hash_file, "w") as f:
            f.write(current_hash)

        segment_files.append(out_file)

        if progress_callback is not None:
            progress_callback(i, len(lines))

    logger.info("Audio segments generated successfully.")
    return segment_files


def combine_segments(segment_files, output_path, pause_ms=700):
    """Concatenate MP3 segments into a single podcast file with pauses."""
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=pause_ms)

    for i, seg in enumerate(segment_files):
        if i > 0:
            combined += pause
        combined += AudioSegment.from_mp3(seg)

    combined.export(output_path, format="mp3")
    logger.info("Combined podcast saved to %s", output_path)
