# Architecture

## Pipeline

1. **Input/library** — user-provided synopsis, episode notes or authorized text.
2. **Story engine** — normalize source text and draft a concise Hindi recap script.
3. **Scene engine** — split narration into scenes with timing and visual intent.
4. **Character engine** — store stable character descriptions and reference assets.
5. **Image engine** — provider adapter for generated or user-supplied artwork.
6. **Quality gate** — verify image presence, dimensions, relevance metadata and retry budget.
7. **Voice engine** — Hindi TTS or imported narration audio.
8. **Subtitle engine** — timestamped SRT/ASS captions.
9. **Video engine** — transitions, pan/zoom, audio mix and FFmpeg export.
10. **Validation** — inspect output metadata, duration, resolution, audio and subtitle tracks.

## Design constraints

- Core models and orchestration must not depend on a specific AI vendor.
- Each provider lives behind an adapter in an integration module.
- Expensive generation is opt-in and bounded by per-job budgets.
- Cache generated assets and record prompts/provider/model metadata.
- Fail clearly when an optional backend is unavailable; never silently substitute copyrighted footage.
- Keep source text, generated assets and final exports in user-controlled workspace paths.

## Initial output target

YouTube Shorts: 9:16, 1080x1920, Hindi narration and subtitles. Frame rate and codec are configurable at export time; 60 FPS is a target to validate, not a promise that every source asset contains native 60 FPS motion.
