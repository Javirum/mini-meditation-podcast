import os
from pydub import AudioSegment


def generate_segments(lines, voices, client, segments_dir):
    """Call TTS for each dialogue line, return list of segment file paths."""
    os.makedirs(segments_dir, exist_ok=True)
    segment_files = []
    for i, line in enumerate(lines, start=1):
        out_file = os.path.join(segments_dir, f"{i:03d}_{line['speaker']}.mp3")
        client.generate_speech(
            text=line["text"],
            voice=voices[line["speaker"]],
            model="tts-1",
            output_path=out_file,
        )
        segment_files.append(out_file)
    print("Audio segments generated successfully.")
    return segment_files


def combine_segments(segment_files, output_path):
    """Concatenate MP3 segments into a single podcast file."""
    combined = AudioSegment.empty()
    for seg in segment_files:
        combined += AudioSegment.from_mp3(seg)
    combined.export(output_path, format="mp3")
    print(f"Combined podcast saved to {output_path}")
