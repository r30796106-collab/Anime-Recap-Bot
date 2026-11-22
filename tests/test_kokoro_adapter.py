import sys
import types

from anime_recap.voice.kokoro import KokoroHindiTTS


def test_kokoro_adapter_lazy_loads_and_writes_audio(tmp_path, monkeypatch) -> None:
    class FakePipeline:
        def __init__(self, lang_code):
            assert lang_code == "h"

        def __call__(self, text, voice):
            assert text == "नमस्ते दुनिया"
            assert voice == "hi-test"
            yield text, "phonemes", [0.1, 0.2, 0.3]

    fake_kokoro = types.SimpleNamespace(KPipeline=FakePipeline)
    fake_soundfile = types.SimpleNamespace(
        write=lambda path, samples, rate: open(path, "w", encoding="utf-8").write(
            f"{rate}:{len(samples)}"
        )
    )
    monkeypatch.setitem(sys.modules, "kokoro", fake_kokoro)
    monkeypatch.setitem(sys.modules, "soundfile", fake_soundfile)

    output = tmp_path / "voice" / "narration.wav"
    result = KokoroHindiTTS(voice="hi-test").synthesize("नमस्ते दुनिया", output)
    assert result == output
    assert output.read_text(encoding="utf-8") == "24000:3"


def test_kokoro_adapter_rejects_empty_text() -> None:
    try:
        KokoroHindiTTS(voice="hi-test").synthesize(" ", "unused.wav")
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("Expected empty narration to be rejected")
