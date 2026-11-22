"""Lazy adapter for Kokoro TTS; keeps heavyweight dependencies optional."""
from pathlib import Path


class KokoroHindiTTS:
    def __init__(self, voice: str, sample_rate: int = 24000) -> None:
        if not voice.strip():
            raise ValueError("A Kokoro Hindi voice name must be provided")
        if sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        self.voice = voice
        self.sample_rate = sample_rate

    def synthesize(self, text: str, output_path: str | Path) -> Path:
        if not text.strip():
            raise ValueError("Narration text is empty")
        try:
            from kokoro import KPipeline
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError(
                "Kokoro TTS is optional. Install the voice extra: pip install 'anime-recap-bot[voice]'"
            ) from exc

        pipeline = KPipeline(lang_code="h")
        samples: list[float] = []
        for _graphemes, _phonemes, audio in pipeline(text, voice=self.voice):
            if hasattr(audio, "detach"):
                audio = audio.detach().cpu().numpy()
            if hasattr(audio, "tolist"):
                audio = audio.tolist()
            if audio and isinstance(audio[0], list):
                for chunk in audio:
                    samples.extend(float(value) for value in chunk)
            else:
                samples.extend(float(value) for value in audio)

        if not samples:
            raise RuntimeError("Kokoro returned no audio samples")
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(destination), samples, self.sample_rate)
        return destination
