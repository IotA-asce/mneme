# Live Local Lab Diagnostics Rules

- Optional detector failures must not stop valid camera frame capture.
- Missing local model files must be reported as configuration gaps, not hidden as "no person detected".
- Do not store or commit model assets under `.local/models/`.
- Do not infer identity, emotion, or user confirmation from face detection.
- Keep CI fake-backed; real camera/model validation remains manual.

