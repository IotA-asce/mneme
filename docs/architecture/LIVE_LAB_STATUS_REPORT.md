# Mneme Live Lab Status Report

Date: 2026-06-14  
Status: Current capability and behavior report after first successful local camera/mic/speaker run  
Scope: Brain-first local living lab, not physical embodiment

## Executive Summary

Mneme has crossed from a simulated/typed prototype into a working local brain loop on the current Mac:

- the camera can produce frames,
- MediaPipe can detect anonymous people,
- attention can lock onto the visible user,
- the microphone can record bounded audio windows,
- Faster-Whisper can produce speech transcripts,
- deterministic dialogue can answer each recognized speech turn,
- macOS `say` can speak the response,
- live console output shows the loop as it runs.

This is not yet a sentient-feeling robot brain. It is a working sensory-cognitive loop with important behavior gaps. The current system is too reactive, too memory-management focused, and too eager to respond to partial utterances. It behaves like a memory-aware assistant attached to live perception, not like a continuous social mind.

The most important next behavioral work is not more hardware. It is conversational timing, social presence, and intent understanding.

## Latest Live Session Evidence

Observed command:

```bash
mneme run --profile local-lab --live \
  --asr-model .local/models/faster-whisper-base \
  --face-backend mediapipe \
  --tts-command "say {text}"
```

Model/device setup status from the session:

- `faster_whisper_base`: present under `.local/models/faster-whisper-base`.
- `mediapipe_face_detector`: present under `.local/models/mediapipe/face_detector.task`.
- `kokoro_default`: still missing, but not required for this run because macOS `say` was used.
- Camera: `Brio 100`.
- Microphone: `Brio 100`.
- Speakers: at least three discovered output options.

Observed positive behavior:

- Mneme detected one or two person candidates in camera frames.
- `person_seen` events were published with high confidence, around `0.94` to `0.98`.
- Attention moved from curiosity scanning to `person:user` / `person:session_person_1`.
- Presence state showed `listening` and `tracking person_1` or `tracking user`.
- Speech transcripts were produced from live microphone audio.
- ASR latency was roughly `3.8s` to `4.6s` per captured segment.
- Mneme generated and spoke responses through the configured TTS command.

Observed weak behavior:

- Mneme repeatedly used responses like: `I can use it as current context; ask me to remember it if it should persist.`
- It interpreted too much of the conversation through the lens of memory storage.
- It responded to short or partial transcripts such as `Okay`, `You`, or garbled fragments.
- It sometimes surfaced conflict/memory clarification when the user was not asking a memory question.
- It did not wait for the user to finish a thought before generating the next response.
- It treated interruption mechanically rather than socially. Interruption exists, but the timing is not natural.
- ASR produced imperfect fragments such as `eu sei` and incomplete sentence text; the current dialogue layer trusted these too quickly.

## Current Capability

Mneme currently supports a local, inspectable brain loop:

```text
camera/microphone/device inventory
  -> perception observations
  -> sensory echo and working memory
  -> world model
  -> attention manager
  -> memory promotion/retrieval/review
  -> executive intent
  -> deterministic dialogue plan
  -> optional local model wording
  -> virtual speech skill
  -> simulated or command-backed speech output
```

Implemented capabilities:

- Local runtime with deterministic event bus.
- Real device inventory for camera, microphone, and speaker discovery.
- Optional live camera capture through OpenCV.
- Optional MediaPipe face/person detection through a local model file.
- Optional live microphone capture through `sounddevice`.
- Optional local ASR through Faster-Whisper.
- Optional speech output through command adapters, including macOS `say`.
- Bounded sensory echo and working memory.
- World model with persons, active speaker, touch/sound/internal/safety seams.
- Attention manager with target ranking, dwell/lock, curiosity scanning, and person focus.
- Executive intent generation.
- Deterministic dialogue planner.
- Local Ollama wording layer when explicitly enabled.
- Durable SQLite memory for raw traces, episodes, facts, summaries, meta-memory, review records, and snapshots.
- Fact conflict detection and supervised memory review commands.
- Cognitive and speech benchmark harnesses.
- Local browser UI for state, device selection, typed input, cognition status, and review actions.
- Live console status for perception, speech, attention, and presence.

Current capability evidence should be described conservatively:

- Mneme has passed the architecture threshold for a local perception-to-response loop.
- Mneme has not proven animal-level, human-level, or sentient cognition.
- Mneme currently has L1/L2-style components: stimulus response, attention, working memory, durable memory, and basic social tracking.
- It does not yet have stable long-horizon conversation, robust social timing, self-directed goals, or adaptive personality.

## Current Behavior It Supports

### Person Presence

When the camera and MediaPipe model are working, Mneme can detect anonymous session people and track attention toward them.

Current behavior:

- sees person candidates,
- publishes `person_seen`,
- updates world model persons,
- shifts attention to the visible person,
- updates avatar/presence state to `listening` or tracking.

Current limits:

- no identity recognition,
- no persistent person continuity beyond anonymous/session-level labels,
- no expression or emotion truth,
- no social decision like greeting someone just because they entered view.

### Live Speech

Mneme records bounded microphone segments and runs ASR on each segment.

Current behavior:

- captures audio chunks,
- transcribes them with Faster-Whisper,
- publishes `speech_transcript`,
- uses transcripts as dialogue turns,
- can speak back through a command TTS adapter.

Current limits:

- the default path is fixed-window recording, not natural endpointing,
- ASR latency is several seconds per segment,
- partial and garbled transcripts are treated too confidently,
- no mature push-to-talk, wake-word, silence-tail, or barge-in policy yet,
- no robust echo cancellation against Mneme's own spoken output.

### Attention And Presence

Mneme can focus on people, curiosity targets, and user speech.

Current behavior:

- curiosity scan when idle,
- person focus when a person is visible,
- user focus when speech is attributed to the user,
- avatar state reflects listening/thinking/speaking/idle.

Current limits:

- presence is mostly stateful reporting, not rich social behavior,
- attention does not yet drive nuanced response timing,
- no gaze motor hardware exists,
- virtual avatar UI is still a dashboard, not an expressive face.

### Dialogue

Mneme can produce deterministic responses grounded in turn type, memory, and runtime status.

Current behavior:

- greetings,
- unknown/ordinary utterance acknowledgements,
- memory-backed answers,
- contradiction clarification,
- status/capability/self responses,
- review proposal acknowledgement,
- optional local model wording behind deterministic safety checks.

Current limits:

- ordinary conversation falls back to memory-oriented templates,
- the system overuses "ask me to remember it",
- local model wording is not enabled by default in the live command shown,
- the local model does not own planning, intent, or memory policy,
- no natural small talk policy or internal motivation model exists yet.

### Memory

Mneme has a serious memory substrate compared with the rest of the system.

Current behavior:

- stores raw traces, episodes, facts, summaries, and meta-memory,
- tracks provenance and source type,
- distinguishes inferred and user-confirmed facts,
- retrieves and reranks memories,
- detects semantic fact conflicts,
- supports supervised correction/forget/confirm/reject flows,
- can explain memory-backed answers.

Current limits:

- memory is too prominent in dialogue behavior,
- there is no mature decision layer for "this is just conversational context" versus "this needs memory review",
- no long-term autobiographical policy has been tuned through daily-driver logs,
- no privacy/redaction workflow for real logs yet.

## Brief Architecture

Mneme keeps cognition in layers. The central rule is still:

```text
Workers publish observations.
State builders publish state.
The executive publishes intent.
Skills publish goals/status.
Output backends perform final simulated/local output.
Safety may override any stage.
```

### Runtime Transport

The local runtime uses an in-process event bus. Components subscribe to typed event kinds:

- `perception_observation`,
- `world_state_update`,
- `attention_update`,
- `memory_candidate`,
- `executive_intent`,
- `skill_goal`,
- `skill_status`,
- `safety_event`.

This keeps the repo ROS-like without requiring ROS yet.

### Perception Layer

Main modules:

- `live_perception.py`
- `local_audio.py`
- `local_vision.py`
- `peripherals.py`

Responsibilities:

- discover host camera/microphone/speaker options,
- capture camera frames,
- detect faces/persons when a model is configured,
- record bounded microphone windows,
- transcribe audio through Faster-Whisper,
- publish observations and raw traces.

### State Layer

Main modules:

- `working_memory.py`
- `world_model.py`
- `context_windows.py`

Responsibilities:

- keep recent sensory fragments,
- maintain current speaker/topic/attention/goal/safety state,
- fuse persons and speech into world state,
- persist bounded working-context snapshots.

### Attention Layer

Main module:

- `attention.py`

Responsibilities:

- rank targets,
- maintain dwell/lock,
- avoid rapid flicker,
- support curiosity scanning,
- publish attention state.

### Memory Layer

Main modules:

- `models.py`
- `storage.py`
- `salience.py`
- `promotion.py`
- `retrieval.py`
- `memory_review.py`
- `consolidation_daemon.py`

Responsibilities:

- score salience,
- promote observations into traces/episodes/facts,
- retrieve relevant memory,
- preserve provenance,
- detect fact conflicts,
- support supervised memory review,
- consolidate repeated episodes.

### Executive And Dialogue Layer

Main modules:

- `executive.py`
- `dialogue.py`
- `turn_understanding.py`
- `cognitive_context.py`
- `model_dialogue.py`

Responsibilities:

- classify user turns,
- decide high-level intent,
- retrieve memory for the turn,
- plan deterministic dialogue acts,
- optionally let a local model improve wording,
- keep memory and safety policy deterministic.

### Presence And Output Layer

Main modules:

- `presence.py`
- `virtual_head.py`
- `local_ui.py`

Responsibilities:

- convert dialogue plans into virtual speech goals,
- publish skill goal/status events,
- track avatar mode and gaze target,
- speak through simulated or command-backed output,
- expose CLI/UI state.

## User Feedback Captured From This Session

### 1. Mneme Feels Too Much Like A Reminder App

Current behavior:

- For ordinary utterances, Mneme often says it can use the content as current context and asks the user to explicitly remember it.
- This is caused by the deterministic unknown-response template and by the system's memory-first heritage.

Why this is wrong for the product goal:

- A sentient-feeling robot brain should treat most conversation as lived context, not as a memory filing prompt.
- Memory should be happening quietly in the background, with explicit memory review only when needed.

Future direction:

- Add a social conversation mode that acknowledges, listens, asks relevant follow-up questions, or stays silent when appropriate.
- Make explicit memory prompts rare.
- Separate "contextual listening" from "memory storage instruction" in dialogue policy.
- Use salience to decide memory candidate creation silently, then expose review only when useful.

### 2. Turn Timing Is Not Natural

Current behavior:

- Mneme records fixed audio windows.
- After each ASR result, it treats the transcript as a complete turn.
- It may respond to fragments before the speaker finishes the thought.

Why this is wrong for the product goal:

- Human conversation includes backchannels, pauses, hesitation, and interruptions.
- A robot brain should wait through natural pauses, avoid answering incomplete fragments, and interrupt only when there is a reason.

Future direction:

- Add true endpointing using VAD plus silence-tail timing.
- Add partial-turn accumulation across ASR windows.
- Add confidence/fragment gating before dialogue response.
- Add a response-delay policy that considers whether the user likely finished.
- Add "continue listening" and nonverbal backchannel states before speaking.

### 3. Interruption Exists, But It Is Not Socially Correct

Current behavior:

- Barge-in/preemption exists mechanically.
- New speech can interrupt active speech output.
- The robot can speak over ongoing user thought because it treats each transcript window independently.

Why this is wrong for the product goal:

- Interruption should be deliberate: safety, correction, clear overlap, or conversational backchannel.
- It should not arise from poor endpointing.

Future direction:

- Distinguish user barge-in from robot interruption.
- Add interruption reasons and thresholds.
- Suppress robot speech while the user appears to be continuing.
- Add short backchannels like "mm" or visual listening state without full verbal response.

### 4. ASR Quality Needs Guardrails

Current behavior:

- ASR can produce short or garbled transcript fragments.
- Dialogue treats these fragments as real turns.

Examples from the session:

- `You`
- `eu sei`
- incomplete phrases such as `This actually like a...`

Future direction:

- Add transcript confidence and length thresholds.
- Mark uncertain transcripts as "heard uncertainly" rather than normal turns.
- Accumulate likely fragments into one turn.
- Add "I may have misheard" behavior only when useful, not every time.

### 5. Memory Conflict Surfacing Needs Better Context

Current behavior:

- Mneme surfaced `I have conflicting memories about user likes. Could you clarify?`
- This can be correct in a memory review context, but jarring during ordinary conversation.

Future direction:

- Surface conflicts only when the user asks a relevant recall question, makes a correction, or explicitly discusses the conflicting fact.
- Keep conflict state available internally without making it the default social response.

## Current Risks

- Live ASR and camera behavior are now real enough that poor timing feels worse than missing perception.
- The deterministic dialogue layer is too blunt for live conversation.
- Fixed-window ASR can create false conversational turns.
- Response latency and interruption timing are not yet tuned.
- Memory-heavy responses can make Mneme feel like a database assistant instead of an embodied brain.
- The local model layer is still only a wording layer unless explicitly enabled.
- No cloud dependency exists by default, which is correct for this phase, but local model quality and latency now matter.

## Recommended Next Implementation Set

The next work should target behavior quality, not more hardware.

### M9.2 Turn Endpointing And Conversation Timing

Add:

- live speech turn accumulator,
- VAD/silence-tail endpointing,
- partial transcript handling,
- response delay based on turn-completion confidence,
- tests for long utterances split across capture windows,
- tests for no response to fragments like `Okay` unless context requires it.

Exit criteria:

- Mneme waits for the user to finish most utterances.
- Mneme does not respond to every partial ASR fragment.
- Barge-in still works when the user interrupts Mneme.

### M9.3 Social Presence Policy

Add:

- listening/backchannel states,
- silence as a valid response,
- greeting policy for stable person presence,
- follow-up question policy,
- non-memory acknowledgement templates,
- configurable verbosity.

Exit criteria:

- Ordinary conversation no longer defaults to "ask me to remember it".
- Mneme can simply listen, acknowledge, or ask a relevant question.

### M9.4 Memory Policy Tuning For Live Conversation

Add:

- distinction between contextual turn, memorable event, explicit memory instruction, correction, and recall query,
- lower visibility of memory-management prompts,
- conflict surfacing only when relevant,
- review proposals for corrections without derailing ordinary speech.

Exit criteria:

- Memory remains central internally but not obnoxious conversationally.
- Mneme feels like it remembers because it uses context well, not because it keeps talking about remembering.

### M9.5 Live Session Evaluation

Add:

- redacted live-session log format,
- metrics for interruption quality,
- fragment response rate,
- memory-prompt overuse,
- ASR uncertainty rate,
- response latency,
- user correction frequency.

Exit criteria:

- Daily live sessions can produce actionable behavior scores.
- Capability ladder evidence starts reflecting live multimodal behavior, not only scripted fixtures.

## Bottom Line

Mneme now has the core local loop alive:

```text
see person -> attend -> hear speech -> transcribe -> think -> respond -> speak
```

The next gap is quality of mind:

```text
listen patiently -> infer turn intent -> choose whether to speak -> respond socially -> remember quietly
```

That is the right next direction if the goal is a sentient-feeling robot brain rather than a reminder app with camera and microphone access.
