import pytest

from anime_recap.images.pollinations import (
    PollinationsClient,
    PollinationsError,
    generate_scene_images_free,
)
from anime_recap.models import RecapProject, Scene

class FakeResponse:
    def __init__(self):
        self.headers = {"Content-Type": "image/jpeg"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b"\xff\xd8\xfffake-jpeg-bytes"


def _project():
    return RecapProject(
        title="Test recap",
        scenes=[
            Scene("scene_001", "A boy at a station", "A boy at a railway station in monsoon rain"),
            Scene("scene_002", "Lamp shines", "A glowing diya in the boy's hands"),
        ],
    )


def test_authenticated_provider_downloads_scene_images(tmp_path, monkeypatch):
    urls = []
    headers = []

    def fake_urlopen(request, timeout):
        urls.append(request.full_url)
        headers.append(request.headers)
        return FakeResponse()

    monkeypatch.setattr("anime_recap.images.pollinations.urlopen", fake_urlopen)
    outputs = generate_scene_images_free(
        _project(), PollinationsClient(api_key="test-token", retries=0), tmp_path, seed=50
    )

    assert [p.name for p in outputs] == ["001_scene_001.jpg", "002_scene_002.jpg"]
    assert all(p.read_bytes().startswith(b"\xff\xd8\xff") for p in outputs)
    assert len(urls) == 2
    assert "boy%20at%20a%20railway%20station" in urls[0]
    assert "seed=50" in urls[0] and "seed=51" in urls[1]
    assert all(h.get("Authorization") == "Bearer test-token" for h in headers)


def test_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("POLLINATIONS_API_KEY", raising=False)
    with pytest.raises(PollinationsError, match="requires a Pollinations API key"):
        PollinationsClient(retries=0).generate("prompt", tmp_path / "image.jpg")


def test_retries_failed_request(monkeypatch, tmp_path):
    calls = {"n": 0}

    def fake_urlopen(request, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("temporary outage")
        return FakeResponse()

    monkeypatch.setattr("anime_recap.images.pollinations.urlopen", fake_urlopen)
    client = PollinationsClient(api_key="test-token", retries=1)
    client.generate("a scene", tmp_path / "retry.jpg")
    assert calls["n"] == 2


@pytest.mark.parametrize("content_type", ["text/html", "image/png"])
def test_rejects_non_image_or_mismatched_response(monkeypatch, tmp_path, content_type):
    response = FakeResponse()
    response.headers = {"Content-Type": content_type}

    monkeypatch.setattr("anime_recap.images.pollinations.urlopen", lambda *a, **kw: response)
    with pytest.raises(PollinationsError, match="not a recognized image"):
        PollinationsClient(api_key="test-token", retries=0).generate("prompt", tmp_path / "bad.png")


def test_rejects_non_https_and_invalid_dimensions():
    with pytest.raises(ValueError, match="HTTPS"):
        PollinationsClient(base_url="http://example.invalid")
    with pytest.raises(ValueError, match="dimensions"):
        PollinationsClient(api_key="test-token", retries=0).generate("prompt", Path("x.jpg"), width=20)
