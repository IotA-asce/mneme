# Memory Privacy Decisions

Date: 2026-06-12
Status: Owner-decided policy for perception-derived memory (Stage 4+)
Decided by: project owner

These decisions were made explicitly by the project owner and supersede the earlier draft assumption that raw frames would never be persisted. They apply to the virtual-head deployment on machines the owner controls.

## Decisions

1. **Raw frames: stored.** Captured camera frames may be persisted and associated with episodes. Implementation bounds (not policy): frames are archived at salience boundaries (keyframes), not as continuous video, with size/age retention caps (`Stage 4 / M4.4`) so storage stays bounded.
2. **Transcripts: persist.** Speech transcripts flow into episodes and facts exactly as simulated transcripts already do, with full provenance.
3. **Everyone is remembered.** No enrollment gate: any person seen or heard may receive a person entity, embeddings for re-identification, episodes, and facts.

## Standing safeguards (unchanged by these decisions)

- Provenance, confidence, and source typing on every stored item; secret-bearing provenance keys rejected at write time.
- Speakability policy still governs what Mneme may *say* (`never_say`/`internal_only` never reach retrieval or utterance plans; `restricted` is never spoken).
- Suppression and explicit purge tombstones (`docs/memory/DECAY.md`) remain available to remove or hide any person's data on request — purge is reasoned and audited.
- Nothing leaves the device: all perception processing and storage is local (no cloud hard dependency).

## Revisit triggers

Revisit this policy before: deploying on machines other than the owner's, demoing in public spaces, multi-user households with guests who haven't been told, or any jurisdiction-specific compliance need. The enrollment-gated alternative ("remember only people who opt in") remains a documented option.
