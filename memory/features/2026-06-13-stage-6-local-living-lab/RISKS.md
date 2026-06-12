# Risks

- Real microphone/camera permissions and device behavior are not CI-testable.
- Optional packages may have platform-specific install issues.
- Local ASR/TTS/vision latency and quality depend on selected model files and host hardware.
- Kokoro API compatibility may vary by package version; the adapter is intentionally small and injectable.
- Default registry entries do not auto-download models; future downloads need source/license/checksum review.
- The browser UI is a dashboard, not a lifelike graphical avatar.
- Local brain-loop progress must not be treated as physical hardware safety.
