import json
import sys
import types

from anime_recap import cli


def test_voice_command_generates_per_scene_audio_and_manifest(tmp_path, monkeypatch, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "title": "Demo",
                "scenes": [
                    {"scene_id": "opening", "narration": "नमस्ते"},
                    {"scene_id": "ending", "narration": "धन्यवाद"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class FakeVoice:
        def __init__(self, voice):
            assert voice == "hi-test"

        def synthesize(self, text, output_path):
            output_path.write_bytes(text.encode("utf-8"))
            return output_path

    fake_kokoro = types.ModuleType("anime_recap.voice.kokoro")
    fake_kokoro.KokoroHindiTTS = FakeVoice
    monkeypatch.setitem(sys.modules, "anime_recap.voice.kokoro", fake_kokoro)
    monkeypatch.setattr(
        sys,
        "argv",
        ["anime-recap", "voice", str(plan), "--voice", "hi-test",
         "--output-dir", str(tmp_path / "voice")],
    )

    cli.main()

    output_dir = tmp_path / "voice"
    assert (output_dir / "001_opening.wav").read_bytes() == "नमस्ते".encode("utf-8")
    assert (output_dir / "002_ending.wav").read_bytes() == "धन्यवाद".encode("utf-8")
    manifest = json.loads((output_dir / "narration_manifest.json").read_text(encoding="utf-8"))
    assert [item["scene_id"] for item in manifest] == ["opening", "ending"]
    assert "Generated 2 narration files" in capsys.readouterr().out


def test_load_project_preserves_character_references(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "title": "Demo",
                "characters": [
                    {
                        "character_id": "hero",
                        "name": "Hero",
                        "visual_description": "Blue jacket and black hair",
                    }
                ],
                "scenes": [
                    {"scene_id": "intro", "narration": "Hello", "character_ids": ["hero"]}
                ],
            }
        ),
        encoding="utf-8",
    )

    project = cli._load_project(plan)
    assert project.characters[0].character_id == "hero"
    assert project.scenes[0].character_ids == ["hero"]
    project.validate()
