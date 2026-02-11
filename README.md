# Mini Meditation Podcast

Generates a meditation-style podcast conversation using OpenAI's API and converts it to audio with Edge TTS.

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

1. Clone the repository and navigate to the project folder:

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
pip install openai edge-tts pydub python-dotenv
```

4. Create a `.env` file in the project root with your API key:

```
OPENAI_API_KEY=your-api-key-here
```

## Usage

Run the script:

```bash
python src/data_processor.py
```

This will:

1. Generate a podcast dialogue via the OpenAI API
2. Convert each dialogue line to speech using Edge TTS
3. Concatenate all segments into a single file at `output/meditation_podcast.mp3`
