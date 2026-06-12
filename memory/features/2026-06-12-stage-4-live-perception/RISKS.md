# Risks

- Real capture depends on host permissions and the configured local command.
- The base package does not ship a native camera library, face detector, VAD, or ASR model.
- Transcript raw traces are retained in SQLite; destructive transcript deletion remains an explicit purge policy.
- Stage 5 still needs spoken output and conversational presence work.
