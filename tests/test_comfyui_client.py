import json
from unittest.mock import patch

import pytest

from anime_recap.images.comfyui import ComfyUIClient, ComfyUIError


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.payload


def test_submit_workflow_posts_json_and_returns_id():
    client = ComfyUIClient("http://localhost:8188")
    with patch("anime_recap.images.comfyui.urlopen", return_value=FakeResponse({"prompt_id": "abc"})) as call:
        assert client.submit_workflow({"1": {"class_type": "SaveImage"}}) == "abc"
    assert call.call_args.args[0].full_url == "http://localhost:8188/prompt"


def test_invalid_server_url_is_rejected():
    with pytest.raises(ValueError, match="http"):
        ComfyUIClient("localhost:8188")


def test_missing_prompt_id_is_reported():
    client = ComfyUIClient("http://localhost:8188")
    with (
        patch("anime_recap.images.comfyui.urlopen", return_value=FakeResponse({})),
        pytest.raises(ComfyUIError, match="prompt_id"),
    ):
        client.submit_workflow({"1": {}})


def test_download_image_saves_comfyui_output(tmp_path):
    client = ComfyUIClient("http://localhost:8188")
    with patch("anime_recap.images.comfyui.urlopen", return_value=FakeResponse({"ok": True})) as call:
        destination = client.download_image(
            {"filename": "scene.png", "subfolder": "output", "type": "output"},
            tmp_path / "scene.png",
        )
    assert destination.read_bytes() == b'{"ok": true}'
    assert "filename=scene.png" in call.call_args.args[0].full_url
