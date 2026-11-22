from anime_recap.models import RecapProject, Scene
from anime_recap.quality import validate_recap_assets


def test_quality_preflight_reports_missing_images_and_prompts(tmp_path):
    project = RecapProject("demo", scenes=[Scene("s1", "hello")])
    report = validate_recap_assets(project, [])
    assert report["ok"] is False
    assert "image_count_mismatch" in report["issues"]
    assert any(item.startswith("missing_visual_prompts") for item in report["issues"])


def test_quality_preflight_accepts_present_image_and_prompt(tmp_path):
    image = tmp_path / "scene.png"
    image.write_bytes(b"image-bytes")
    project = RecapProject("demo", scenes=[Scene("s1", "hello", "anime scene")])
    assert validate_recap_assets(project, [image])["ok"] is True
