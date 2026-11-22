# Upstream integration research (initial pass)

Research date: 2026-11-22. Code licenses do not automatically cover model weights, datasets, checkpoints or generated assets; those terms must be checked separately.

| Upstream | Observed code license / status | Decision |
|---|---|---|
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI) | GPL-3.0; modular local/server image and video workflow engine; supports API workflows and model offloading. | Candidate optional external backend. Integrate over its API; do not copy its code into this project. Check model and workflow terms separately. |
| [AnimateDiff Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved) | Apache-2.0. Requires ComfyUI, motion modules and compatible model files. | Optional later motion backend; not part of baseline. Check model-file licenses and hardware costs. |
| [IPAdapter Plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus) | GPL-3.0; upstream README says maintenance-only (2025-04-14). | Defer pending maintenance and GPL review. |
| [Practical-RIFE](https://github.com/hzwer/Practical-RIFE) | MIT. Neural frame interpolation; model weights and runtime dependencies need separate checks. | Optional post-processing experiment; not needed for still-image recap export. |
| [VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) | GPL-family license. ComfyUI custom nodes for video/image sequence workflows. | Defer: baseline exporter uses FFmpeg directly. |
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | Primarily LGPL, with optional GPL components depending on build configuration. | Use as an external executable, not vendored source. Check the installed build and enabled codecs. |
| [Kokoro](https://github.com/hexgrad/kokoro) | Apache-2.0 library; upstream documents Hindi language code h. | Best TTS candidate for a separate adapter spike. Verify Hindi voice quality, pronunciation, performance and dependencies before requiring it. |
| [MoviePy](https://github.com/Zulko/moviepy) | MIT. Upstream notes it can be slower than direct FFmpeg for many operations. | Not selected for baseline; direct FFmpeg CLI is leaner for this use case. |

## Hardware and cost gate

Do not install ComfyUI, download checkpoints or motion models on a phone by default. The full diffusion/video stack can consume substantial storage, RAM and compute. Keep story, scene-plan, subtitle and FFmpeg orchestration usable without GPU/model downloads. Validate the lightweight pipeline first, then select a remote GPU or local backend from a real sample run.
