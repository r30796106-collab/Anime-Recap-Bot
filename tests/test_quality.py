import pytest
from PIL import Image

from anime_recap.models import RecapProject, Scene
from anime_recap.quality import validate_recap_assets


def _project():
    return RecapProject("demo", scenes=[Scene("s1", "hello", "anime scene")])


def _write_image(path, image_format="PNG", size=(512, 512)):
    Image.new("RGB", size, color=(30, 60, 90)).save(path, format=image_format)
    return path


def test_quality_preflight_reports_missing_images_and_prompts(tmp_path):
    project = RecapProject("demo", scenes=[Scene("s1", "hello")])
    report = validate_recap_assets(project, [])
    assert report["ok"] is False
    assert "image_count_mismatch" in report["issues"]
    assert any(item.startswith("missing_visual_prompts") for item in report["issues"])


@pytest.mark.parametrize("image_format", ["PNG", "JPEG", "WEBP"])
def test_quality_preflight_decodes_supported_formats(tmp_path, image_format):
    suffix = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[image_format]
    image = _write_image(tmp_path / f"scene{suffix}", image_format=image_format)

    report = validate_recap_assets(_project(), [image])

    assert report["ok"] is True
    assert report["image_details"] == [
        {"index": 0, "format": image_format, "width": 512, "height": 512}
    ]


def test_quality_preflight_rejects_unrecognized_image_bytes(tmp_path):
    image = tmp_path / "scene.png"
    image.write_bytes(b"not-an-image")

    report = validate_recap_assets(_project(), [image])

    assert report["ok"] is False
    assert "image_decode_failed:0" in report["issues"]


def test_quality_preflight_rejects_truncated_image_data(tmp_path):
    image = _write_image(tmp_path / "scene.png")
    image.write_bytes(image.read_bytes()[:40])

    report = validate_recap_assets(_project(), [image])

    assert report["ok"] is False
    assert "image_decode_failed:0" in report["issues"]


def test_quality_preflight_rejects_low_resolution_images(tmp_path):
    image = _write_image(tmp_path / "thumbnail.png", size=(256, 384))

    report = validate_recap_assets(_project(), [image])

    assert report["ok"] is False
    assert "image_dimensions_too_small:0:256x384" in report["issues"]


def test_quality_preflight_rejects_images_over_pixel_limit(tmp_path):
    image = _write_image(tmp_path / "large.png", size=(64, 64))

    report = validate_recap_assets(_project(), [image], min_dimension=1, max_pixels=1000)

    assert report["ok"] is False
    assert "image_dimensions_too_large:0:64x64" in report["issues"]


def test_quality_preflight_rejects_unsupported_image_format(tmp_path):
    image = _write_image(tmp_path / "scene.gif", image_format="GIF")

    report = validate_recap_assets(_project(), [image])

    assert report["ok"] is False
    assert "unsupported_image_format:0" in report["issues"]
