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

Bootstrap stage. The repository currently defines the project boundaries, quality gates and modular architecture; generation backends will be integrated incrementally.

## License

No project license has been selected yet. Until a license is added, all rights are reserved by the repository owner. Third-party components retain their own licenses.
