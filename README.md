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
anime-recap srt workspace/scene_plan.json --output outputs/recap.srt
# Generate scene images with your configured ComfyUI workflow and place them in outputs/images/.
anime-recap voice workspace/scene_plan.json --voice YOUR_KOKORO_HINDI_VOICE
anime-recap render workspace/scene_plan.json \
  --images-dir outputs/images \
  --voice-dir outputs/voice \
  --subtitles outputs/recap.srt \
  --music assets/background_music.wav \
  --output outputs/recap.mp4
```

Alternatively, pass one already-concatenated narration track with `--audio narration.wav`
instead of `--voice-dir`. The render step checks that every scene has a non-empty image
before invoking FFmpeg. External ComfyUI and Kokoro services still need to be configured
separately; this command does not claim to generate those assets by itself.
