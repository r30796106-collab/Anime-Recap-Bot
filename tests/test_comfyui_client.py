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


def test_wait_for_completion_returns_successful_outputs(monkeypatch):
    client = ComfyUIClient("http://localhost:8188")
    record = {"outputs": {"1": {"images": [{"filename": "scene.png"}]}},
              "status": {"status_str": "success", "completed": True}}
    monkeypatch.setattr(client, "get_history", lambda _prompt_id: {"abc": record})
    assert client.wait_for_completion("abc") == record


def test_wait_for_completion_fails_immediately_on_execution_error(monkeypatch):
    client = ComfyUIClient("http://localhost:8188")
    record = {
        "outputs": {},
        "status": {
            "status_str": "error",
            "completed": False,
            "messages": [
                ["execution_error", {
                    "exception_type": "MissingModelError",
                    "exception_message": "Checkpoint not found",
                }]
            ],
        },
    }
    monkeypatch.setattr(client, "get_history", lambda _prompt_id: {"abc": record})
    monkeypatch.setattr(
        "anime_recap.images.comfyui.time.sleep",
        lambda _seconds: pytest.fail("failed workflows must not keep polling"),
    )
    with pytest.raises(ComfyUIError, match="workflow abc failed.*Checkpoint not found"):
        client.wait_for_completion("abc")


def test_wait_for_completion_rejects_completed_workflow_without_outputs(monkeypatch):
    client = ComfyUIClient("http://localhost:8188")
    record = {"outputs": {}, "status": {"status_str": "success", "completed": True}}
    monkeypatch.setattr(client, "get_history", lambda _prompt_id: {"abc": record})
    with pytest.raises(ComfyUIError, match="completed without outputs"):
        client.wait_for_completion("abc")
