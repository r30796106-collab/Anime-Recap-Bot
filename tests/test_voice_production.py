import json

from anime_recap.models import RecapProject, Scene
from anime_recap.voice.production import create_scene_narration


class FakeVoice:
    def synthesize(self, text, output_path):
        output_path.write_bytes(text.encode("utf-8"))
        return output_path


def test_scene_voice_files_and_manifest_are_created(tmp_path):
    project = RecapProject("demo", scenes=[
        Scene("intro", "नमस्ते"), Scene("ending", "धन्यवाद")
    ])
    outputs = create_scene_narration(project, FakeVoice(), tmp_path)
    assert len(outputs) == 2
    assert all(path.is_file() for path in outputs)
    manifest = json.loads((tmp_path / "narration_manifest.json").read_text(encoding="utf-8"))
    assert [item["scene_id"] for item in manifest] == ["intro", "ending"]
