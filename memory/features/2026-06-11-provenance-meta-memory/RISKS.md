# Risks and Follow-Up

- Speakability is a retrieval policy hook, not encryption or full authorization.
- `restricted` remains visible to ordinary retrieval; callers need future policy handling before speaking or displaying sensitive records.
- Summary storage now has meta-memory support, but summary retrieval is still future work.
- Provenance rejects secret-like keys, but it does not inspect every value for accidental secret content.
- Retrieval counter updates occur after ranking, so ranking explanations show the meta-memory state before the current retrieval update.
