# Mini Meditation Podcast

Generates meditation-style podcast conversations using **OpenAI GPT** for dialogue generation and **OpenAI TTS** for text-to-speech audio. Feed it a transcript (or upload a file), and it produces a two-speaker podcast episode as an MP3.

## Features

- AI-powered dialogue generation (GPT-4 / GPT-4o)
- Text-to-speech with OpenAI TTS (multiple voice options)
- Segment caching — skips re-generating unchanged audio segments
- File upload support — `.txt`, `.pdf`, and audio files (`.mp3`, `.wav`, `.m4a`, etc.)
- Gradio web UI with progress tracking
- CLI with configurable flags

## Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- FFmpeg (required by pydub for MP3 handling)

### Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

## Setup

1. Clone the repository:

```bash
git clone https://github.com/Javirum/mini-meditation-podcast.git
cd mini-meditation-podcast
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your API key:

```
OPENAI_API_KEY=your-api-key-here
```

## Usage

### CLI

```bash
python main.py
```

| Flag | Description |
|------|-------------|
| `--config PATH` | Path to config JSON (default: `data/config.json`) |
| `--transcript PATH` | Path to transcript file (default: `data/transcript.txt`) |
| `--no-cache` | Force regeneration of all audio segments |

### Web UI

```bash
python app.py
```

Opens a Gradio interface where you can edit the transcript and system prompt, choose GPT/TTS models and voices, upload files, and generate the podcast with live progress updates.

## Configuration

Edit `data/config.json` to customise defaults:

```jsonc
{
  "openai": {
    "model": "gpt-4",          // GPT model for dialogue generation
    "tts_model": "tts-1"       // TTS model ("tts-1" or "tts-1-hd")
  },
  "voices": {
    "COACH": "nova",            // OpenAI voice for the Coach speaker
    "STUDENT": "alloy"          // OpenAI voice for the Student speaker
  },
  "podcast": {
    "system_prompt": "...",     // System prompt sent to GPT
    "episode_prompt": "..."     // Episode prompt template ({transcript} placeholder)
  },
  "output": {
    "segments_dir": "output/segments",
    "dialogue_file": "output/dialogue.txt",
    "podcast_file": "output/meditation_podcast.mp3",
    "pause_ms": 700             // Silence between segments (ms)
  }
}
```

## Project Structure

```
.
├── main.py              # CLI entry point
├── app.py               # Gradio web UI
├── data/
│   ├── config.json      # Default configuration
│   └── transcript.txt   # Default transcript
├── src/
│   ├── audio.py         # TTS segment generation & combining
│   ├── config.py        # Config loading & validation
│   ├── dialogue.py      # Dialogue parsing & saving
│   ├── openai_client.py # OpenAI API wrapper
│   └── transcript.py    # File upload processing (txt/pdf/audio)
├── tests/               # pytest unit tests
├── output/              # Generated audio & dialogue (gitignored segments)
└── requirements.txt
```

## Testing

```bash
pytest tests/
```
