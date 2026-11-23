import pytest

from anime_recap.images.enhance import enhance_image, enhance_images


def test_upscaler_missing_executable_fails_cleanly(tmp_path):
    source = tmp_path / "src.png"
    source.write_bytes(b"img")
    with pytest.raises(FileNotFoundError, match="not found"):
        enhance_image(source, tmp_path / "out.png", executable="missing-upscaler-xyz")


def test_enhancer_rejects_missing_image(tmp_path):
    with pytest.raises(ValueError, match="missing or empty"):
        enhance_image(tmp_path / "missing.png", tmp_path / "out.png")


def test_batch_returns_empty_when_no_inputs(tmp_path):
    assert enhance_images([], tmp_path / "enhanced") == []
