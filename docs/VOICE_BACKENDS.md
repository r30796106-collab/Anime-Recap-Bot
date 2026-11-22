# Voice backend

## Kokoro Hindi adapter

The optional Kokoro adapter uses the upstream language code h (Hindi) and writes WAV audio at 24 kHz by default.

Install only when testing this backend:

    python -m pip install -e ".[voice,dev]"

Then instantiate KokoroHindiTTS with an explicit Hindi voice name. Voice availability and quality can vary by model release; test Hindi names, pronunciation, punctuation and mixed Hindi/English phrases with a sample before selecting a production voice.

The core package does not download model weights or import Kokoro at startup. The optional backend may require PyTorch, espeak-ng and model downloads. This is not recommended as a default Termux/Android installation. Prefer a supported Linux/remote GPU environment for the first real TTS benchmark.

Upstream: https://github.com/hexgrad/kokoro (Apache-2.0 code and weights per upstream README; verify all transitive dependencies and deployment terms).
