# Context

Stage 4 already had real host device inventory. The remaining work was to let Mneme turn discovered cameras and microphones into perception events while preserving the architecture boundary: workers publish observations, memory handles storage, world model fuses state, and executive decides intent.

The base package intentionally remains dependency-light. Built-in OpenCV, face models, VAD, and ASR engines are deferred to explicit adapter decisions.
