# Stage Prerequisites — What You Need to Provide (Stage 3 → 7)

Date: 2026-06-13 (revision 3 — Stage 5 virtual presence complete)
Status: Living checklist for the human side of the master roadmap

Stages 0–5 are complete in the repo-owned virtual-head architecture. The near-term target remains a **virtual head** — perception and speech on the machines you already own — with all motor/hardware work deferred to the Stage 6 physical-embodiment track. Mneme targets **Windows, macOS, and Linux** equally; your primary dev machine is a **Mac Mini M4**, which is fully sufficient through Stage 5 and 7.

Almost everything from the previous revision's shopping list is now deferred or unnecessary. Here is what actually remains.

## TL;DR Checklist

| # | Item | Needed for | Blocking? | Cost |
|---|---|---|---|---|
| 1 | Python 3.11+ on the Mac | Stage 3–5 | Yes | $0 |
| 2 | Camera + microphone (likely already owned) | Stage 4 | Yes for live perception | $0–80 |
| 3 | Camera/mic OS permissions granted | Stage 4–5 | Yes for live adapters | $0 |
| 4 | TTS command/voice choice | Stage 5 | No (simulated output works) | $0 |
| 5 | Approval for optional native perception/TTS dependencies | Future adapter work | Only if adding deps | $0 |
| 6 | LLM provider + budget, or local-only | Stage 7 | No (fallbacks exist) | optional |
| 7 | Repeat visitors for presence evaluation | Stage 7 | Eventually | time |
| — | ~~ROS 2, mic array, servos, PSU, e-stop, head mechanics~~ | Stage 6 (deferred) | Not until you opt in | — |

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
2. Stage 4 currently uses command adapters, not bundled OpenCV/audio/ASR dependencies. Optional native adapters can be added later only after dependency approval.

Disk note: with raw-frame storage decided, expect the archive to grow — M4.4 adds retention caps you can tune; the Mac Mini's internal storage is fine to start.

## Stage 5 — Conversational Presence

Stage 5 is implemented with simulated speech by default and optional local TTS command adapters.

- **TTS command:** optional. On macOS, `mneme run --tts-command "say {text}" --input "hello Mneme"` uses the built-in `say` command.
- **Voice label:** optional. `--voice <name>` persists the selected label as procedural memory and reuses it on later runs.
- Nothing else is required: avatar state and skills are virtual, and no purchases are needed.

## Stage 6 — Physical Embodiment (deferred)

**Buy nothing now.** The previous revision's full hardware guidance (ROS 2 environment, Dynamixel servos ~$250–300, U2D2 controller, 12V PSU, physical e-stop, head mechanics, mic array, touch sensors — ~$350–700 total) is preserved in git history (`git log -- docs/runbooks/STAGE_PREREQUISITES.md`, revision 1) and will be refreshed into this document when you green-light the physical track. The only thing to know today: when that day comes, a Linux box near the bench will be back on the list — keep it in mind if you ever retire other hardware.

## Stage 7 — Lifelike Presence

- **LLM access (optional, decision):** Anthropic API key (console.anthropic.com, set a spend cap) for guarded summarization/dialogue realization, or local-only via Ollama (ollama.com, $0, runs well on M4). Deterministic fallbacks exist either way; any key lives in an environment variable on your machine, never in the repo.
- **People + time:** the presence-quality evaluation needs 2–3 repeat visitors over weeks; that calendar time is yours to provide.

---

## Open Decisions Summary

1. **Optional native adapters:** approve any future native perception/TTS dependencies before they are added.
2. **Stage 7:** LLM provider + budget, or local-only.
3. **Whenever you choose:** green-light the Stage 6 physical-embodiment track.

Stages 3–5 can run locally with the setup commands above. Future native adapters and physical embodiment remain explicit opt-in work.
