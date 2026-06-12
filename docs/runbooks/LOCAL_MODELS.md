# Local Models Runbook

Status: Stage 6 foundation
Date: 2026-06-13

Mneme is local-first, but model files are not repository assets. Keep downloaded or converted models under `.local/models/`, which is ignored by git.

## Registry

The model registry lives at `config/models.yaml`.

Each record describes:

- model ID,
- backend,
- local path,
- license/source notes,
- optional checksum,
- profiles that use the model,
- optional download URL.

Downloads are intentionally disabled unless `download_url` is present. Add a URL only after the source, license, redistribution terms, and expected checksum are understood.

## Commands

List everything:

```bash
mneme models list --json
```

List models for a profile:

```bash
mneme models list --profile local-speech --json
mneme models list --profile local-vision --json
```

Verify local files:

```bash
mneme models verify --json
mneme models verify faster_whisper_base --json
```

Download only when a registry entry explicitly supports it:

```bash
mneme models download <model_id>
```

If a download is not configured, the command fails deliberately.

## Defaults

The default registry currently describes:

- `faster_whisper_base` for local ASR,
- `kokoro_default` for local TTS,
- `mediapipe_face_detector` for local vision/person presence.

These records are hygiene metadata, not bundled models. Tests use fake model backends and temporary files.

## Rules

- Do not commit `.local/models/`.
- Prefer permissive-license models and document license/source before enabling a default.
- Add checksums when practical.
- Keep cloud models optional.
- Treat all model-generated memories as `model_inferred` unless confirmed by the user.
- Do not add face embedding identity recognition until the exact model/license has been approved.
