import json

import pytest

from src.config import load_config


def _setup_config(tmp_path, config_dict, transcript_text="Hello world"):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config_file = data_dir / "config.json"
    config_file.write_text(json.dumps(config_dict))
    transcript_file = data_dir / "transcript.txt"
    transcript_file.write_text(transcript_text)
    return config_file, transcript_file


def _base_config():
    return {
        "voices": {"COACH": "nova", "STUDENT": "echo"},
        "output": {"segments_dir": "output/segments", "podcast_path": "output/podcast.mp3"},
        "podcast": {
            "system_prompt": "You are a meditation coach.",
            "episode_prompt": "Transcript: {transcript}",
        },
        "openai": {"model": "gpt-4o-mini"},
    }


def test_load_config_basic(tmp_path):
    _setup_config(tmp_path, _base_config(), "My transcript")
    cfg = load_config(str(tmp_path))
    assert cfg["voices"] == {"COACH": "nova", "STUDENT": "echo"}
    assert cfg["model"] == "gpt-4o-mini"
    assert cfg["system_prompt"] == "You are a meditation coach."
    assert "My transcript" in cfg["episode_prompt"]


def test_tts_model_defaults(tmp_path):
    _setup_config(tmp_path, _base_config())
    cfg = load_config(str(tmp_path))
    assert cfg["tts_model"] == "tts-1"


def test_custom_paths(tmp_path):
    cfg_dict = _base_config()
    cfg_file = tmp_path / "custom.json"
    cfg_file.write_text(json.dumps(cfg_dict))
    tx_file = tmp_path / "custom.txt"
    tx_file.write_text("custom transcript")

    cfg = load_config(str(tmp_path), config_path=str(cfg_file), transcript_path=str(tx_file))
    assert "custom transcript" in cfg["episode_prompt"]


def test_missing_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path))


def test_missing_transcript_raises(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "config.json").write_text(json.dumps(_base_config()))
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path))


def test_invalid_json_raises(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "config.json").write_text("{bad json!!")
    (data_dir / "transcript.txt").write_text("hi")
    with pytest.raises(json.JSONDecodeError):
        load_config(str(tmp_path))


def test_missing_key_raises(tmp_path):
    incomplete = {"openai": {"model": "gpt-4o-mini"}}
    _setup_config(tmp_path, incomplete)
    with pytest.raises(KeyError):
        load_config(str(tmp_path))
