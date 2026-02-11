import os


def extract_from_text(file_path):
    """Read plain text file."""
    with open(file_path, "r") as f:
        return f.read()


def extract_from_pdf(file_path):
    """Extract text from all pages of a PDF."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_from_audio(file_path, client):
    """Transcribe audio file via OpenAI Whisper."""
    return client.transcribe_audio(file_path)


EXTENSION_MAP = {
    ".txt": "text",
    ".pdf": "pdf",
    ".mp3": "audio",
    ".wav": "audio",
    ".m4a": "audio",
    ".webm": "audio",
    ".mp4": "audio",
    ".ogg": "audio",
}


def process_upload(file_path, client=None):
    """Dispatch to the right extractor based on file extension. Returns text."""
    ext = os.path.splitext(file_path)[1].lower()
    file_type = EXTENSION_MAP.get(ext)
    if file_type == "text":
        return extract_from_text(file_path)
    elif file_type == "pdf":
        return extract_from_pdf(file_path)
    elif file_type == "audio":
        if client is None:
            raise ValueError("OpenAI client required for audio transcription")
        return extract_from_audio(file_path, client)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
