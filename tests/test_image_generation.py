import json

import pytest

from anime_recap.images.comfyui import ComfyUIError
from anime_recap.images.generation import generate_scene_images
from anime_recap.models import RecapProject, Scene


class FakeComfyUI:
    def __init__(self):
        self.workflows = []
        self.downloads = []

    def submit_workflow(self, workflow):
        self.workflows.append(workflow)
        return f"prompt-{len(self.workflows)}"

    def wait_for_completion(self, prompt_id, timeout=600.0):
        return {
            "outputs": {
                "9": {
                    "images": [
                        {"filename": f"{prompt_id}.png", "subfolder": "", "type": "output"}
                    ]
                }
            }
        }

    def download_image(self, descriptor, output_path):
        from pathlib import Path

        path = Path(output_path)
        path.write_bytes(b"generated-image")
        self.downloads.append((descriptor, path))
        return path


def _project():
    return RecapProject(
        title="Sample",
        scenes=[
            Scene("scene_001", "आरव स्टेशन पहुँचा", "A boy reaches an old railway station"),
            Scene("scene_002", "दीया चमक उठा", "A golden oil lamp glows on the platform"),
        ],
    )


def _workflow():
    return {
        "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "old positive"}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "old negative"}},
        "3": {"class_type": "KSampler", "inputs": {"seed": 99}},
    }


def test_generates_and_downloads_one_image_per_scene(tmp_path):
    project = _project()
    workflow = _workflow()
    original = json.loads(json.dumps(workflow))
    client = FakeComfyUI()

    outputs = generate_scene_images(
        project,
        workflow,
        client,
        tmp_path,
        prompt_node_id="1",
        negative_prompt_node_id="2",
        seed_node_id="3",
        seed=500,
    )

    assert [path.name for path in outputs] == [
        "001_scene_001.png",
        "002_scene_002.png",
    ]
    assert all(path.read_bytes() == b"generated-image" for path in outputs)
    assert client.workflows[0]["1"]["inputs"]["text"].startswith("high-quality 2D Japanese anime")
    assert "old positive" not in client.workflows[0]["1"]["inputs"]["text"]
    assert [item["3"]["inputs"]["seed"] for item in client.workflows] == [500, 501]
    assert workflow == original


def test_rejects_missing_prompt_node(tmp_path):
    with pytest.raises(TypeError, match="Positive prompt node"):
        generate_scene_images(
            _project(), _workflow(), FakeComfyUI(), tmp_path, prompt_node_id="missing"
        )


def test_rejects_workflow_without_image_outputs(tmp_path):
    class NoImageClient(FakeComfyUI):
        def wait_for_completion(self, prompt_id, timeout=600.0):
            return {"outputs": {"9": {"gifs": []}}}

    with pytest.raises(ComfyUIError, match="without image outputs"):
        generate_scene_images(
            _project(), _workflow(), NoImageClient(), tmp_path, prompt_node_id="1"
        )


def test_rejects_unsafe_scene_id(tmp_path):
    project = RecapProject(
        title="Unsafe", scenes=[Scene("../outside", "text", "visual")]
    )
    with pytest.raises(ValueError, match="Unsafe scene ID"):
        generate_scene_images(
            project, _workflow(), FakeComfyUI(), tmp_path, prompt_node_id="1"
        )
