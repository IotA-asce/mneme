# Stage Prerequisites — What You Need to Provide (Stage 3 → 7)

Date: 2026-06-12
Status: Living checklist for the human side of the master roadmap

Stages 0–2 were pure software and are complete. Every remaining stage needs something only you can provide: an environment, a purchase, a physical build step, or a decision. This document lists exactly what, why, where to get it, and what to do with it. Items are ordered by when they block progress.

> Costs are rough 2026 estimates in USD; check current prices. Nothing here commits you to a vendor — alternatives are listed where they exist.

---

## TL;DR Checklist

| # | Item | Needed for | Blocking? | Rough cost |
|---|---|---|---|---|
| 1 | Decision: ROS 2 environment (WSL2 / Docker / Linux box) | Stage 3 | Yes — blocks everything after M3.1 | $0 (WSL2) |
| 2 | ROS 2 Jazzy installed + working `colcon` build | Stage 3 | Yes | $0 |
| 3 | USB webcam | Stage 4 (vision) | Yes for M4.1 | $30–80 |
| 4 | USB mic array with DOA (ReSpeaker v2) | Stage 4 (speech + sound direction) | Yes for M4.2/M4.3 | $70–100 |
| 5 | Touch sensor breakout + microcontroller | Stage 4 (touch) | Only for M4.4 | $15–30 |
| 6 | Decision: bench compute (this PC + WSL vs. SBC) | Stage 4–6 | Yes by Stage 4 | $0–250 |
| 7 | Decision: head design + expressive channels (DOF list) | Stage 5 | Yes before skills are finalized | $0 |
| 8 | TTS voice choice (Piper) | Stage 5 (speech skill) | No (defaults fine) | $0 |
| 9 | Smart servos + controller + PSU + e-stop | Stage 6 | Yes — entire stage | $250–600 |
| 10 | Head mechanics (3D-printed kit or pan-tilt) | Stage 6 | Yes | $50–300 |
| 11 | Decision: LLM provider + API key (optional) | Stage 7 | No (deterministic fallbacks exist) | usage-based |
| 12 | Privacy/consent decisions for person memory | Stage 4 & 7 | Yes before storing real faces/voices | $0 |

---

## Stage 3 — ROS 2 Runtime Bridge

### 3.1 A ROS 2 development environment (the big one)

**Why:** Stage 3 wraps the Python memory core in ROS 2 nodes, generates the `android_brain_interfaces` package from our aligned drafts, and proves replay parity over ROS transport. None of that runs without a ROS 2 distribution, and ROS 2 is a first-class citizen on Ubuntu Linux only.

**Your decision — pick one (my recommendation: A now, C before Stage 6):**

**Option A — WSL2 + Ubuntu 24.04 (recommended to start, $0):**
You are on Windows 11, which supports WSL2 with GUI apps (WSLg) and USB passthrough (`usbipd-win`). This is the fastest path and fully sufficient for Stages 3–5 (everything up to real hardware is simulated/dry-run).

1. In an **admin** PowerShell: `wsl --install -d Ubuntu-24.04`, reboot, create your Linux user.
2. Inside Ubuntu, install ROS 2 **Jazzy Jalisco** (LTS, supported to 2029) following the official guide: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html — it is ~6 commands (add the apt repository, `sudo apt install ros-jazzy-desktop`).
3. Install the build tools: `sudo apt install python3-colcon-common-extensions python3-rosdep python3-vcstool build-essential` then `sudo rosdep init && rosdep update`.
4. Add `source /opt/ros/jazzy/setup.bash` to `~/.bashrc`.
5. Clone this repo inside WSL (don't build against the Windows-mounted copy — file I/O is slow and line endings bite): `git clone https://github.com/IotA-asce/mneme.git`.
6. Sanity check: `ros2 run demo_nodes_cpp talker` in one terminal, `ros2 run demo_nodes_py listener` in another.

**Option B — Docker (`$0`, good for CI):** `docker pull osrf/ros:jazzy-desktop` and develop in a container (VS Code Dev Containers works well). Cleanest isolation; slightly more friction for interactive work. We will want this anyway for the GitHub Actions CI job.

**Option C — A dedicated Linux machine or dual-boot (best long-term):** Stages 4–6 want direct, low-latency USB access to camera/mic/servo controllers and the ability to sit on the bench next to the head. Any x86 mini-PC (used ThinkCentre/NUC, ~$150–250) or your own dual-boot with Ubuntu 24.04 works. You can defer this until Stage 4/6 — WSL2 with `usbipd` passthrough covers a lot, but native Linux removes a whole class of device headaches.

**Not recommended:** native Windows ROS 2. Binary support is second-tier, many packages don't build, and every tutorial assumes Linux.

**What I'll do once you have it:** generate the interface package from `interfaces/`, build the `mneme_memory_node` bridge, set up `colcon test` + replay parity tests, and add a ROS CI workflow.

### 3.2 GitHub Actions minutes (almost certainly already fine)

The repo is on GitHub; public repos get free CI. The Stage 3 CI job runs in the `osrf/ros:jazzy` container. Nothing to buy — just be aware CI runtime will grow. If the repo is private, check your Actions minutes quota (Settings → Billing).

---

## Stage 4 — Real Perception

All processing stays **local** (project rule: no cloud as a hard dependency). Models below run on CPU; a GPU/NPU makes them faster but is optional at bench scale.

### 4.1 Camera (vision worker)

- **Buy:** any good USB UVC webcam. Recommended: **Logitech C920/C922** (~$60–80) — ubiquitous, well-supported by V4L2/OpenCV, decent low-light. Budget alternative: any 1080p UVC cam (~$25).
- **Stretch (optional, not required):** a depth camera (Luxonis **OAK-D Lite**, ~$150) adds on-board person detection and depth later; skip for now.
- **Do:** plug into the Linux environment. Under WSL2 you'll need `usbipd-win` (`winget install usbipd`) to attach the camera to WSL: `usbipd bind --busid <id>` + `usbipd attach --wsl --busid <id>`. Verify with `ls /dev/video*`.
- **Software I'll set up (no action needed):** OpenCV for capture/detection and a local face-embedding model for re-identification. License note: some face-recognition model weights are research-only — I'll flag the license of whatever we pick for your approval before it lands in the repo.

### 4.2 Microphone array (speech + sound direction workers)

A normal mic gives speech but not direction-of-arrival. One device covers both M4.2 and M4.3:

- **Buy:** **Seeed ReSpeaker USB Mic Array (v2.0)** (~$70–100, seeedstudio.com or Mouser/DigiKey). 4-mic XMOS array, USB, built-in DOA/beamforming/VAD, plays nicely with Linux ALSA.
  - Alternative if you choose a Raspberry Pi for compute: **ReSpeaker 4-Mic Array HAT** (~$25), sits on the Pi GPIO.
- **Do:** plug in (same `usbipd` dance under WSL2), verify with `arecord -l`.
- **Software I'll set up:** silero-VAD + faster-whisper (small/int8 model, fully local) for transcripts; the array's DOA angle feeds the `sound_direction` worker.

### 4.3 Touch sensing

- **Buy:** **MPR121 12-channel capacitive touch breakout** (~$8, Adafruit #1982 or clones) + copper foil tape for touch zones + a microcontroller to bridge I2C→USB serial: **Raspberry Pi Pico** (~$5) or any Arduino-compatible board you have.
- **Do:** nothing yet beyond acquiring; wiring happens with the head build (Stage 6). If you want early touch testing, tape three foil zones to a cardboard stand-in.
- **Software I'll set up:** a tiny serial protocol → `touch` perception events.

### 4.4 Compute decision

Decide where perception runs:

- **This PC (WSL2 or dual-boot):** $0, plenty of CPU for whisper-small + face detection. Fine through Stage 5.
- **Raspberry Pi 5 (8 GB, ~$80 + PSU/SD ~$30):** makes the head self-contained later; whisper-tiny/int8 and lightweight vision fit, but it's the constraint you'll feel.
- **NVIDIA Jetson Orin Nano (~$250):** if you want headroom for better vision models on-device.

My recommendation: stay on the PC through Stage 5; decide on embedded compute only when the head exists.

### 4.5 Privacy decisions (required before real faces/voices are stored)

Per the roadmap's privacy track, I need three explicit decisions from you, recorded in `docs/safety/`:

1. May face **embeddings** (not images — raw frames are never persisted into memory by design) be stored in SQLite for re-identification? Retention period?
2. May speech **transcripts** be stored (they already flow into episodes in simulation)? Retention period?
3. Who may be remembered — everyone seen, or only enrolled/consenting people?

---

## Stage 5 — Expressive Skills and Dry-Run Actuation

Mostly software against a fake actuator backend — cheap, but two things are yours:

### 5.1 Decision: what the head physically is (drives the skill list)

Before skill controllers are finalized I need the expressive channel list. Concretely, confirm or edit this default plan:

| Channel | DOF | Default assumption |
|---|---|---|
| Neck | 2 (pan + tilt) | yes |
| Eyes | 2 (shared pan + tilt) | yes |
| Eyelids | 1 (blink) | yes |
| Ears | 2 (one per ear) | yes |
| Jaw/mouth | 0 in v1 (speech is audio-only) | confirm |

This is a design decision, not a purchase — but Stage 6 shopping depends on it (servo count ≈ DOF count + spares).

### 5.2 TTS voice

- **Default (recommended):** **Piper TTS** — local, fast, MIT-licensed, runs on CPU (github.com/rhasspy/piper). Voices are free downloads; listen to samples at https://rhasspy.github.io/piper-samples/ and tell me which voice is "Mneme's voice". $0.
- Anything cloud-based would violate the no-hard-cloud-dependency rule, so I'll wire Piper either way; a different local engine is swappable later.

---

## Stage 6 — Hardware Bring-Up (gated, human-supervised)

Do not buy any of this until Stage 5's safety gate is passed — but here is the full list so you can budget.

### 6.1 Actuators — the most important purchase decision

**Strong recommendation: smart serial-bus servos with position/load/temperature feedback**, not hobby PWM servos. Our safety architecture (limits enforced in the bridge, `internal_health` events, degraded mode on overheat) *requires* feedback; PWM servos are blind.

- **Recommended: Dynamixel XL430-W250-T** (~$50 each, robotis.us) for neck, **XC330-M288-T** (~$24 each) for eyes/lids/ears. For the default 7-DOF head: ≈ $250–300.
  - Controller: **Dynamixel U2D2 + power hub** (~$50) — USB serial to the servo bus.
- **Budget alternative:** Waveshare/Feetech **ST3215 serial bus servos** (~$14 each) + their USB driver board (~$10). Feedback exists but the ecosystem is rougher. Total ≈ $120.
- **Avoid:** MG996R-class PWM hobby servos. Cheap (~$5) but no feedback, no soft limits, fail unsafe.

### 6.2 Head mechanics

Pick one:

- **3D-printed open design:** the **InMoov head** (inmoov.fr, free STLs) is the classic; print yourself or via a service (PCBWay/Craftcloud, ~$80–150 in PLA). Most work, most expressive.
- **Commercial pan-tilt skeleton + custom shell:** a 2-DOF pan-tilt bracket kit (~$20–60) holding camera + mic as a "face", with ears/eyes added incrementally. Least work; my recommendation for a first bench head.
- You'll need basic tools either way: screwdrivers, M2/M3 hardware assortment (~$15), and ideally access to a 3D printer for brackets.

### 6.3 Power and safety (non-negotiable)

- **PSU:** 12 V (Dynamixel) bench supply sized ≥ 2× total stall current — a 12 V/10 A switching supply (~$25). Separate USB power for logic.
- **Physical e-stop:** latching mushroom switch (~$10) wired to cut the **servo power rail only** (logic stays up so we keep telemetry). This is required by AGENTS.md §11 before any live actuation.
- Inline fuse on the servo rail, and a fire-safe bench area with the head clamped down.

### 6.4 What you'll physically do

Stage 6 is explicitly human-supervised: you'll be the hands for assembly, wiring per the docs I'll write into `docs/hardware/`, and the supervising operator for every staged live test (one actuator at a time, limited range first, hand on the e-stop). Budget a few sessions of bench time.

---

## Stage 7 — Lifelike Presence

### 7.1 LLM access (optional, guarded)

LLM-assisted summarization/dialogue realization is optional with deterministic fallbacks, per the architecture. If you want it:

- **Decision:** provider + budget. Recommended: an **Anthropic API key** (console.anthropic.com → API keys; usage-based billing — set a monthly spend limit) used for summarization and dialogue realization only, always `model_inferred`, never actuator-facing.
- **Offline alternative:** a local model via **Ollama** (ollama.com, $0) — quality is lower but keeps the robot fully offline.
- The key will live in an environment variable on the bench machine — **never in this repo** (repo rule: no secrets, enforced by provenance checks).

### 7.2 People and policy

- **Consent:** Stage 7's person-scoped continuity means real people's preferences persist across sessions. Decide the enrollment policy (explicit "Mneme, remember me" opt-in is my recommendation) and who the test visitors are.
- **Evaluation time:** the presence-quality suite needs repeat visits from at least 2–3 people over weeks. That's calendar time only you can provide.

---

## Decisions I Need From You (summary)

1. **Stage 3, now:** which ROS environment — WSL2 (fast start), Docker, or dedicated Linux box? → I start M3.1 the day it exists.
2. **Stage 4:** approve the perception shopping list (camera + ReSpeaker + touch parts) and answer the three privacy questions (§4.5).
3. **Stage 5:** confirm the expressive channel table (§5.1) and pick a Piper voice (§5.2).
4. **Stage 6:** servo ecosystem choice — Dynamixel (recommended) vs. budget Feetech (§6.1) — and head mechanics path (§6.2).
5. **Stage 7:** LLM provider + budget, or local-only (§7.1); person-memory enrollment policy (§7.2).

## What Needs Nothing From You

Pieces I can still build in pure software while you procure: the ROS-independent slice of Stage 3 (node adapter classes, package skeletons, launch plans, parity test harness), richer replay scenarios, the window→episode bridge, topic-specific episode retrieval, and the Stage 4 worker scaffolds against simulated backends. Say the word and I'll keep moving on those in parallel.
