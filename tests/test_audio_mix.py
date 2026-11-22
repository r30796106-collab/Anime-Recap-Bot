import pytest

from anime_recap.audio import build_audio_mix_filter, validate_audio_tracks


def test_audio_mix_keeps_narration_and_ducks_music():
    result = build_audio_mix_filter(1, 2, 0.15)
    assert "[1:a]" in result and "[2:a]" in result
    assert "volume=0.150" in result and "amix=inputs=2" in result


def test_empty_audio_track_is_rejected(tmp_path):
    empty = tmp_path / "empty.wav"
    empty.touch()
    with pytest.raises(ValueError, match="empty"):
        validate_audio_tracks(empty)
