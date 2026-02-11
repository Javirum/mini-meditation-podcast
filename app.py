import os
import json

from dotenv import load_dotenv

# Monkey-patch gradio_client bug: boolean additionalProperties passed as schema
import gradio_client.utils as _gc_utils

_orig_json_schema_fn = _gc_utils._json_schema_to_python_type


def _patched_json_schema_fn(schema, defs=None):
    if isinstance(schema, bool):
        return "Any"
    return _orig_json_schema_fn(schema, defs)


_gc_utils._json_schema_to_python_type = _patched_json_schema_fn

import gradio as gr

from src.openai_client import OpenAIClient
from src.dialogue import parse_dialogue, save_dialogue
from src.audio import generate_segments, combine_segments
from src.transcript import process_upload

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Load defaults from config.json and transcript.txt
# ---------------------------------------------------------------------------
with open(os.path.join(BASE_DIR, "data", "config.json"), "r") as f:
    _config = json.load(f)

with open(os.path.join(BASE_DIR, "data", "transcript.txt"), "r") as f:
    _default_transcript = f.read()

_default_system_prompt = _config["podcast"]["system_prompt"]
_episode_prompt_template = _config["podcast"]["episode_prompt"]

OPENAI_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


# ---------------------------------------------------------------------------
# Pipeline generator — yields intermediate UI updates
# ---------------------------------------------------------------------------
def generate_podcast(
    transcript,
    system_prompt,
    gpt_model,
    tts_model,
    coach_voice,
    student_voice,
    pause_ms,
    skip_cache,
    progress=gr.Progress(track_tqdm=True),
):
    status = ""
    dialogue_text = ""
    audio_path = None
    dialogue_file = None
    podcast_file = None

    try:
        # --- 1. Generate dialogue ----------------------------------------
        progress(0.0, desc="Generating dialogue...")
        status = "Generating dialogue..."
        yield status, dialogue_text, audio_path, dialogue_file, podcast_file

        episode_prompt = _episode_prompt_template.format(transcript=transcript)
        client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
        dialogue_text = client.generate_dialogue(gpt_model, system_prompt, episode_prompt)

        progress(0.2, desc="Parsing dialogue...")
        status = "Dialogue generated. Parsing..."
        yield status, dialogue_text, audio_path, dialogue_file, podcast_file

        # --- 2. Parse & save dialogue ------------------------------------
        voices = {"COACH": coach_voice, "STUDENT": student_voice}
        lines = parse_dialogue(dialogue_text, voices)

        dialogue_out = os.path.join(BASE_DIR, _config["output"]["dialogue_file"])
        save_dialogue(lines, dialogue_out)
        dialogue_file = dialogue_out

        progress(0.25, desc="Generating audio segments...")
        status = "Generating audio segments..."
        yield status, dialogue_text, audio_path, dialogue_file, podcast_file

        # --- 3. Generate TTS segments ------------------------------------
        segments_dir = os.path.join(BASE_DIR, _config["output"]["segments_dir"])

        def _segment_progress(current, total):
            frac = 0.25 + 0.65 * (current / total)
            progress(frac, desc=f"Generating segment {current}/{total}...")

        segment_files = generate_segments(
            lines,
            voices,
            client,
            segments_dir,
            tts_model=tts_model,
            no_cache=skip_cache,
            progress_callback=_segment_progress,
        )

        progress(0.9, desc="Combining segments...")
        status = "Combining segments..."
        yield status, dialogue_text, audio_path, dialogue_file, podcast_file

        # --- 4. Combine into final podcast -------------------------------
        podcast_out = os.path.join(BASE_DIR, _config["output"]["podcast_file"])
        combine_segments(segment_files, podcast_out, pause_ms=int(pause_ms))

        audio_path = podcast_out
        podcast_file = podcast_out
        progress(1.0, desc="Done!")
        status = "Done!"
        yield status, dialogue_text, audio_path, dialogue_file, podcast_file

    except Exception as exc:
        status = f"Error: {exc}"
        yield status, dialogue_text, audio_path, dialogue_file, podcast_file


# ---------------------------------------------------------------------------
# File upload handler
# ---------------------------------------------------------------------------
def handle_upload(file):
    if file is None:
        return _default_transcript
    try:
        client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
        return process_upload(file.name, client=client)
    except Exception as e:
        raise gr.Error(f"Failed to process file: {e}")


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
with gr.Blocks(title="Mini Meditation Podcast") as demo:
    gr.Markdown("# Mini Meditation Podcast Generator")

    with gr.Row():
        # ---- Left column: inputs ----------------------------------------
        with gr.Column():
            file_upload = gr.File(
                label="Upload Transcript (txt, pdf, or audio)",
                file_types=[".txt", ".pdf", ".mp3", ".wav", ".m4a", ".webm", ".mp4", ".ogg"],
            )
            transcript_box = gr.Textbox(
                label="Transcript",
                value=_default_transcript,
                lines=10,
                max_lines=20,
            )
            system_prompt_box = gr.Textbox(
                label="System Prompt",
                value=_default_system_prompt,
                lines=5,
                max_lines=10,
            )
            gpt_model = gr.Dropdown(
                label="GPT Model",
                choices=["gpt-4", "gpt-4o", "gpt-4o-mini"],
                value=_config["openai"]["model"],
            )
            tts_model = gr.Dropdown(
                label="TTS Model",
                choices=["tts-1", "tts-1-hd"],
                value=_config["openai"].get("tts_model", "tts-1"),
            )
            coach_voice = gr.Dropdown(
                label="Coach Voice",
                choices=OPENAI_VOICES,
                value=_config["voices"]["COACH"],
            )
            student_voice = gr.Dropdown(
                label="Student Voice",
                choices=OPENAI_VOICES,
                value=_config["voices"]["STUDENT"],
            )
            pause_slider = gr.Slider(
                label="Pause Duration (ms)",
                minimum=0,
                maximum=2000,
                step=100,
                value=_config["output"].get("pause_ms", 700),
            )
            skip_cache = gr.Checkbox(label="Skip Cache", value=False)
            generate_btn = gr.Button("Generate Podcast", variant="primary")

        # ---- Right column: outputs --------------------------------------
        with gr.Column():
            status_box = gr.Textbox(label="Status / Log", interactive=False)
            dialogue_box = gr.Textbox(
                label="Generated Dialogue",
                interactive=False,
                lines=15,
                max_lines=30,
            )
            audio_player = gr.Audio(label="Podcast Audio", type="filepath")
            dialogue_download = gr.File(label="Download Dialogue")
            podcast_download = gr.File(label="Download Podcast")

    file_upload.change(fn=handle_upload, inputs=[file_upload], outputs=[transcript_box])

    generate_btn.click(
        fn=generate_podcast,
        inputs=[
            transcript_box,
            system_prompt_box,
            gpt_model,
            tts_model,
            coach_voice,
            student_voice,
            pause_slider,
            skip_cache,
        ],
        outputs=[
            status_box,
            dialogue_box,
            audio_player,
            dialogue_download,
            podcast_download,
        ],
    )

if __name__ == "__main__":
    demo.launch()
