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
    image.write_bytes(b"\\x89PNG\\r\\n\\x1a\\nplaceholder")
    project = RecapProject("demo", scenes=[Scene("s1", "hello", "anime scene")])
    assert validate_recap_assets(project, [image])["ok"] is True



def test_quality_preflight_rejects_unrecognized_image_bytes(tmp_path):
    image = tmp_path / "scene.png"
    image.write_bytes(b"not-an-image")
    project = RecapProject("demo", scenes=[Scene("s1", "hello", "anime scene")])
    report = validate_recap_assets(project, [image])
    assert report["ok"] is False
    assert "invalid_image_format:0" in report["issues"]


def test_quality_preflight_recognizes_supported_image_signatures(tmp_path):
    signatures = [
        b"\\xff\\xd8\\xffjpeg",
        b"\\x89PNG\\r\\n\\x1a\\n",
        b"RIFF\\x00\\x00\\x00\\x00WEBP",
    ]
    project = RecapProject("demo", scenes=[Scene("s1", "hello", "anime scene")])
    for index, signature in enumerate(signatures):
        image = tmp_path / f"scene_{index}.img"
        image.write_bytes(signature)
        assert validate_recap_assets(project, [image])["ok"] is True
