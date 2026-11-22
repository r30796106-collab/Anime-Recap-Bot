import json
import sys

from anime_recap import cli


def test_images_free_cli_passes_options_and_reports(tmp_path, monkeypatch, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({
        "title": "Test",
        "scenes": [{"scene_id": "scene_001", "narration": "हिंदी", "visual_prompt": "rainy station"}],
    }), encoding="utf-8")
    out_dir = tmp_path / "images"
    captured = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_options"] = kwargs

    def fake_generate(project, client, output_dir, **kwargs):
        captured.update({"scene_count": len(project.scenes), "output_dir": output_dir, "options": kwargs})
        return [tmp_path / "one.jpg"]

    monkeypatch.setattr("anime_recap.images.pollinations.PollinationsClient", FakeClient)
    monkeypatch.setattr("anime_recap.images.pollinations.generate_scene_images_free", fake_generate)
    monkeypatch.setattr(sys, "argv", [
        "anime-recap", "images-free", str(plan), "--output-dir", str(out_dir),
        "--seed", "42", "--width", "512", "--height", "768",
        "--model", "test/model", "--timeout", "25",
    ])

    cli.main()

    assert captured["client_options"] == {"model": "test/model", "timeout": 25.0}
    assert captured["scene_count"] == 1
    assert captured["output_dir"] == out_dir
    assert captured["options"]["seed"] == 42
    assert captured["options"]["width"] == 512
    assert captured["options"]["height"] == 768
    assert "Generated 1 images" in capsys.readouterr().out
