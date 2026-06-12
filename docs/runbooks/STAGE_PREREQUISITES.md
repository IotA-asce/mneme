# Stage Prerequisites — What You Need to Provide (Stage 3 → 8)

Date: 2026-06-13 (revision 4 — Stage 6 Local Living Lab foundation)
Status: Living checklist for the human side of the master roadmap

Stages 0–5 are complete in the repo-owned virtual-head architecture, and Stage 6 is now the **Local Living Lab**: microphone, speaker, camera, local models, memory, attention, virtual presence, and evaluation on the computer you already own. All motor/hardware work is deferred to the Stage 8 physical-embodiment track. Mneme targets **Windows, macOS, and Linux** equally; your primary dev machine is a **Mac Mini M4**, which is sufficient for the current brain-first path.

Almost everything from the previous revision's shopping list is now deferred or unnecessary. Here is what actually remains.

## TL;DR Checklist

| # | Item | Needed for | Blocking? | Cost |
|---|---|---|---|---|
| 1 | Python 3.11+ on the Mac | Stage 3–6 | Yes | $0 |
| 2 | Camera + microphone | Stage 4/6 live perception | Yes for live local tests | $0–80 |
| 3 | Camera/mic OS permissions granted | Stage 4/6 | Yes for live adapters | $0 |
| 4 | Optional local extras install | Stage 6 | Yes for native ASR/TTS/vision | $0 |
| 5 | Local model files under `.local/models/` | Stage 6 | Yes for faster-whisper/Kokoro/MediaPipe runs | model-dependent |
| 6 | TTS command/voice fallback | Stage 5/6 | No (simulated output works) | $0 |
| 7 | Repeat local use and redacted logs | Stage 7 | Eventually | time |
| — | ~~ROS 2, mic array, servos, PSU, e-stop, head mechanics~~ | Stage 8 (deferred) | Not until you opt in | — |

Privacy decisions are already made and recorded in `docs/safety/MEMORY_PRIVACY.md` (raw frames stored, transcripts persist, everyone remembered) — nothing more needed from you there unless you want to revisit.

---

## Stage 3 — Cross-Platform Runtime and Virtual Head

**Nothing to buy.** This stage is pure software: the runtime loop, peripheral discovery, the terminal virtual head, and the 3-OS CI matrix.

What you do on the Mac Mini:

1. Install Python 3.11+ if not present — `brew install python@3.12` (install Homebrew first from https://brew.sh if needed), or use https://python.org installers. Apple Silicon native builds, no Rosetta needed.
2. Clone and set up:
   ```bash
   git clone https://github.com/IotA-asce/mneme.git && cd mneme
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e '.[dev]'
   python scripts/dev_check.py
   ```
3. Set the git identity on that machine: `git config user.name "Mu In Nasif" && git config user.email muinnasif@gmail.com`.

The peripheral discovery service (M3.2) will report whatever the Mac has (built-in devices on a Mac Mini are: none — see Stage 4).

## Stage 4 — Real Perception (Camera + Microphone)

**Hardware** — note the Mac Mini has **no built-in camera or microphone**, so you need:

- **Camera:** any UVC USB webcam works on macOS (and Windows/Linux). If you have an iPhone, **Continuity Camera** also works ($0) but is macOS-only — fine for your bench, the discovery service will just find it as a camera. Otherwise a Logitech C920-class webcam (~$60) is the cross-platform reference device.
- **Microphone:** most webcams include one (sufficient). A small USB conference mic (~$20–40) improves ASR if needed. No mic array required — sound direction is deferred with the physical head.
- **Speakers:** for Stage 5 voice output — anything, including the Mac Mini's built-in speaker.

**Actions:**

1. Grant camera/microphone permissions when macOS prompts (System Settings → Privacy & Security → Camera/Microphone → your terminal/Python). Without this, capture silently fails — it's the #1 macOS perception gotcha.
2. Stage 4 command adapters remain supported. Stage 6 adds optional native adapters behind the same contracts.

Disk note: with raw-frame storage decided, expect the archive to grow — M4.4 adds retention caps you can tune; the Mac Mini's internal storage is fine to start.

## Stage 5 — Conversational Presence

Stage 5 is implemented with simulated speech by default and optional local TTS command adapters.

- **TTS command:** optional. On macOS, `mneme run --tts-command "say {text}" --input "hello Mneme"` uses the built-in `say` command.
- **Voice label:** optional. `--voice <name>` persists the selected label as procedural memory and reuses it on later runs.
- Nothing else is required: avatar state and skills are virtual, and no purchases are needed.

## Stage 6 — Local Living Lab

Stage 6 is implemented as an opt-in local foundation. The base install stays lightweight; native model/media dependencies are extras.

Install the full local lab extras when you are ready to test real local media:

```bash
pip install -e '.[local-lab]'
```

Check configured local models:

```bash
mneme models list --json
mneme models verify --json
```

Run the local speech profile after placing compatible ASR/TTS model files:

```bash
mneme run --profile local-speech --json
```

Run the local vision profile after granting camera permission:

```bash
mneme run --profile local-vision --face-backend mediapipe --json
```

Open the local browser dashboard:

```bash
mneme ui
```

Record evaluation metrics:

```bash
mneme run --json --input "hello Mneme" --evaluation-log .local/evaluation/daily_driver.jsonl
mneme eval summarize --path .local/evaluation/daily_driver.jsonl --json
```

The important manual checks are:

1. macOS grants microphone/camera permission to the terminal or Python process.
2. `mneme models verify --json` shows expected files present.
3. Microphone capture produces transcripts within a usable delay.
4. TTS either plays locally or fails as a clear skill failure.
5. Barge-in preempts active speech and no user turn produces duplicate spoken replies.
6. Camera frames produce anonymous `person_seen` observations; no unrestricted identity recognition is enabled.
7. Evaluation logs grow locally and contain no secrets you do not intend to store.

## Stage 7 — Evolving Brain Evaluation

- **People + time:** repeated local use and 2–3 repeat visitors over weeks will expose continuity and memory behavior.
- **Private logs:** daily-driver logs should be redacted before becoming replay fixtures.
- **Local-only default:** model-generated memories remain `model_inferred` unless confirmed by the user.
- **Cloud/LLM access:** optional future decision only; cloud is not a hard requirement.

## Stage 8 — Physical Embodiment (deferred)

**Buy nothing now.** The previous revision's full hardware guidance (ROS 2 environment, Dynamixel servos ~$250–300, U2D2 controller, 12V PSU, physical e-stop, head mechanics, mic array, touch sensors — ~$350–700 total) is preserved in git history (`git log -- docs/runbooks/STAGE_PREREQUISITES.md`, revision 1) and will be refreshed into this document when you green-light the physical track. The only thing to know today: when that day comes, a Linux box near the bench will be back on the list — keep it in mind if you ever retire other hardware.

---

## Open Decisions Summary

1. **Local model choices:** place/verify model files under `.local/models/`; downloads stay explicit and license-documented.
2. **Stage 7:** decide which evaluation metrics matter most for the evolving-brain experiments.
3. **Whenever you choose:** green-light the Stage 8 physical-embodiment track.

Stages 3–6 can run locally with the setup commands above. Physical embodiment remains explicit opt-in work.
