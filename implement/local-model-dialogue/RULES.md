# Rules

- The deterministic planner chooses dialogue act; the model only realizes wording.
- The model may use only memory refs included in the cognitive context packet.
- `never_say` and `internal_only` memory content must not enter prompts.
- `restricted` memory content must be redacted unless trusted internal mode is used.
- Model output cannot write durable memory.
- Model output cannot directly command skills, actuators, or hardware.
- Any model/runtime/schema/safety failure must fall back to deterministic text.
