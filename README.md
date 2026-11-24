# Anime Recap Bot

An independent, modular pipeline for producing Hindi anime recap videos from user-provided story material.

## V1 scope

- Convert supplied story text into a structured recap script and scene plan.
- Maintain character references and scene-level visual prompts.
- Generate or import scene artwork through pluggable image backends.
- Produce Hindi narration, subtitles, music and sound-effect tracks.
- Assemble vertical videos (9:16, target 1080x1920) with FFmpeg.
- Provide repeatable tests, provenance records and configurable resource limits.

**V1 is an anime recap workflow, not a full traditional frame-by-frame anime production system.** Advanced image-to-video and motion features are optional integrations after the reliable still-image recap pipeline works.

## Development principles

1. Keep integrations modular and replaceable; do not hard-code a single AI provider.
2. Prefer free/open-source components, but verify each dependency's license, hardware needs and maintenance status before adoption.
3. Never download copyrighted anime episodes, extract protected footage, or bypass platform protections. Use user-provided, authorized source material and assets.
4. Keep API keys and credentials out of source control.
5. Test each integration in isolation before enabling it in the end-to-end workflow.
6. Develop on feature branches and merge through reviewed pull requests.

## Quick start

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

FFmpeg and any optional image/TTS backends must be installed separately when those stages are enabled.

## Project status

The repository now includes a provider-neutral story/scene plan, SRT generation, a ComfyUI HTTP adapter (workflow submission, history polling and output image download), character-aware prompt construction, a Kokoro adapter, per-scene narration orchestration, still-image motion filters, audio mixing helpers, FFmpeg export command construction and deterministic asset preflight checks. These components have unit/CI coverage, but external ComfyUI generation, real Kokoro Hindi audio quality and a complete end-to-end MP4 have not yet been verified.

### Current verification boundaries

- GitHub Actions CI validates Python tests, lint and compilation; it does not prove external model inference works.
- ComfyUI requires a user-managed reachable server, a compatible workflow JSON and model weights installed on that server.
- Kokoro requires its optional dependencies and model assets; no model is downloaded by default.
- Motion filters currently animate still images; they do not generate new character animation frames.
- Character consistency is supported through reusable character descriptions in prompts. Visual identity consistency still needs reference-image/IP-Adapter style backend support and human review.

## License

No project license has been selected yet. Until a license is added, all rights are reserved by the repository owner. Third-party components retain their own licenses.

## Blue Ant read-only audit

This repository includes an on-demand **Blue Ant Read-only Project Audit** workflow.

1. Open the repository's **Actions** tab.
2. Select **Blue Ant Read-only Project Audit**.
3. Choose **Run workflow** and select the branch/ref to inspect.
4. Download the generated JSON report from the workflow run's artifacts.

Blue Ant's fixed specialists inspect repository structure, tests/CI, documentation and selected safety patterns. They are read-only: they do not execute this project's tests or modify files. GitHub Actions CI is the source of truth for test execution.


## One-command recap assembly

The `render` command now connects the scene plan, image preflight, optional narration,
subtitles, background music and FFmpeg export. It expects one image per scene in
`outputs/images/`, named `001_scene_001.png` (or `scene_001.png`); PNG, JPG,
JPEG and WebP are supported.

```bash
anime-recap plan examples/sample_story_hi.txt --title "दीये की आखिरी रोशनी"
anime-recap srt examples/sample_recap_plan.json --output outputs/recap.srt
# Generate scene images with your configured ComfyUI workflow and place them in outputs/images/.
anime-recap voice examples/sample_recap_plan.json --voice YOUR_KOKORO_HINDI_VOICE
anime-recap render examples/sample_recap_plan.json \
  --images-dir outputs/images \
  --voice-dir outputs/voice \
  --subtitles outputs/recap.srt \
  --music assets/background_music.wav \
  --output outputs/recap.mp4
```

Alternatively, pass one already-concatenated narration track with `--audio narration.wav`
instead of `--voice-dir`. The render step checks that every scene has a non-empty image before invoking FFmpeg. After
encoding, it uses FFprobe to verify that the MP4 is readable and has the expected 9:16 dimensions,
60 fps, scene-plan duration and (when narration or music was supplied) an audio stream. Install
FFmpeg and FFprobe and pass `--ffprobe` if the executable is not named `ffprobe`. External ComfyUI
and Kokoro services still need to be configured separately; this command does not claim to generate
those assets by itself. A passing mocked CI test validates the probe logic, not an actual sample MP4.


### Generate scene images with ComfyUI

Export a workflow from ComfyUI using **Save (API Format)**. The workflow must be the API-format
JSON object (node IDs mapped to node definitions), not the regular UI workflow export. Identify
the positive and optional negative `CLIPTextEncode` node IDs, plus the optional sampler seed
node ID. The command injects a character-aware scene prompt into the positive text node, applies
the negative prompt when configured, submits one workflow per scene, waits for completion and
downloads the first image output for each scene.

```bash
# This checked-in sample plan contains six 5-second scenes and fixed Aarav/Dadi profiles.
export COMFYUI_URL="http://127.0.0.1:8188"
anime-recap images examples/sample_recap_plan.json \
  --workflow workflows/anime_portrait_api.json \
  --prompt-node 6 \
  --negative-prompt-node 7 \
  --seed-node 3 \
  --seed 4100 \
  --output-dir outputs/images

# Generate Hindi narration, subtitles and assemble the MP4
anime-recap voice examples/sample_recap_plan.json --voice YOUR_INSTALLED_HINDI_VOICE
anime-recap srt examples/sample_recap_plan.json --output outputs/recap.srt
anime-recap render examples/sample_recap_plan.json \
  --images-dir outputs/images \
  --voice-dir outputs/voice \
  --subtitles outputs/recap.srt \
  --output outputs/recap.mp4
```

Node IDs above are examples only: read them from your own API-format workflow. The workflow must
contain a positive text input named `text`; if supplied, the negative prompt node must also expose
`inputs.text`, and the seed node must expose `inputs.seed`. Use a workflow compatible with the
models and custom nodes installed on your ComfyUI server. The bot does not install model weights
or custom nodes automatically. For remote servers, use an authenticated/private network path;
do not expose an unauthenticated ComfyUI instance to the public internet.

## Pollinations image generation and anime upscaling

Pollinations is an optional cloud image-generation alternative to self-hosted ComfyUI. Its current unified gateway requires an API key; service availability, model access and costs/credits may change. Get a key from `enter.pollinations.ai`, store it in `POLLINATIONS_API_KEY` (never commit it), and review generated scene relevance.

```bash
export POLLINATIONS_API_KEY='YOUR_KEY_HERE'\nanime-recap images-pollinations examples/sample_recap_plan.json --output-dir outputs/images --model tongyi-mai/z-image-turbo
```

This creates one prompt-conditioned image per scene using the character-aware prompts, retries failed requests, validates image bytes, and varies the seed per scene. Authentication is required; use models with free credits/allowance only if available in your account. The endpoint is not a guaranteed free service or production SLA.

Optional anime image enhancement uses the Real-ESRGAN NCNN/Vulkan command-line executable, which must be installed separately:

```bash
anime-recap enhance-images outputs/images --output-dir outputs/enhanced --model realesr-animevideov3 --scale 2
```

The enhancer validates each input/output and does not run if the executable is missing. Enhancement is opt-in; use the enhanced directory as your render images directory only after checking quality.

